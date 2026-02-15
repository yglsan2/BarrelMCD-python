# Vérification : Flutter consomme les endpoints Python sans masquer le code backend

## 1. Correspondance endpoints Python ↔ Flutter

| Endpoint Python | Méthode ApiClient (Flutter) | Utilisation dans l'app |
|----------------|-----------------------------|------------------------|
| `GET /health` | `health()` | Appel au démarrage (HomeScreen) pour afficher un avertissement si l'API est injoignable. |
| `POST /api/parse-markdown` | `parseMarkdown(content)` | McdState.parseMarkdown → écran Import Markdown (onglet Markdown). |
| `POST /api/parse-mots-codes` | `parseMotsCodes(content)` | McdState.parseMotsCodes → écran Import Markdown (onglet Mots codés). |
| `POST /api/validate` | `validateMcd(mcd)` | McdState.validateMcd → barre d'outils (Valider), écran Import (onglet Validation). |
| `POST /api/to-mld` | `mcdToMld(mcd)` | McdState.generateMld → panneau MLD/SQL, barre d'outils. |
| `POST /api/to-sql` | `mcdToSql(mcd, dbms)` | McdState.generateSql → panneau MLD/SQL, bouton SQL (Ctrl+E). |
| `POST /api/analyze-data` | `analyzeData(data, formatType)` | Non utilisé dans l'UI actuelle (méthode prête pour une future fonctionnalité). |

Tous les endpoints métier (parse, validate, to-mld, to-sql) sont bien consommés par Flutter. Aucun endpoint Python n’est « masqué » par du code Flutter qui remplacerait l’appel.

---

## 2. Formats requêtes / réponses (alignement)

- **parse-markdown** : corps `{ "content": string }` → réponse `{ "parsed", "canvas", "precision_score" }`. Flutter envoie `content`, lit `canvas` et `precision_score`.
- **parse-mots-codes** : corps `{ "content": string }` → réponse `{ "canvas" }`. Flutter envoie `content`, lit `canvas`.
- **validate** : corps `{ "mcd": { entities, associations, association_links, inheritance_links } }` → réponse `{ "valid", "errors" }`. Flutter envoie `mcdData` (même structure), lit `errors`.
- **to-mld** : corps `{ "mcd" }` → réponse = MLD (objet). Flutter envoie `mcdData`, utilise la réponse telle quelle.
- **to-sql** : corps `{ "mcd", "dbms" }` → réponse `{ "sql" }`. Flutter envoie `mcdData` et `dbms`, lit `sql`.

Les clés utilisées côté Flutter correspondent à celles exposées par l’API Python.

---

## 3. Pas de logique métier dupliquée (Flutter ne masque pas le code Python)

- **Validation MCD** : effectuée uniquement par l’API (`api/services/merise_rules.validate_mcd`). Flutter n’a qu’une normalisation d’affichage pour les cardinalités lors de la saisie d’un lien (`_normalizeCardinality` dans mcd_state : 1,n / n,1 → 1,n) ; la règle métier reste côté Python.
- **Parsing** : Markdown et mots codés sont parsés côté Python (mcd_service, mocodo_style_parser, markdown_mcd_parser). Flutter envoie le texte et affiche le résultat ; aucun parser métier en Dart.
- **MCD → MLD → SQL** : toute la chaîne est dans `api/services/mcd_service` + `views/model_converter`. Flutter envoie le MCD (format canvas) et affiche MLD/SQL ; aucune conversion en Dart.
- **Normalisation de chargement** : `MainToolbar.normalizeEntities` / `normalizeAssociations` / `normalizeAssociationLinks` servent uniquement à charger des fichiers .bar/.json (format Looping/Barrel) ; ce n’est pas une redéfinition des règles Merise, seulement un adaptateur de format pour l’UI.

En résumé : la logique métier (validation, parsing, conversion) reste dans le backend Python ; Flutter ne la masque pas et ne la duplique pas.

---

## 4. Port et baseUrl

- Flutter : `ApiClient(baseUrl: 'http://127.0.0.1:8000')` (défini dans `main.dart`).
- API Python : par défaut `api/main.py` lance uvicorn sur le port 8000. Pour que Flutter atteigne l’API, lancer le serveur sur le port 8000, par exemple :  
  `uvicorn api.main:app --host 0.0.0.0 --port 8000`

Si le port diffère, adapter `baseUrl` dans `main.dart` pour qu’il pointe vers l’URL du serveur Python.
