# Transcription des logiques métier (références open source)

Réinterprétation des logiques métier de **Mocodo**, **OpenSphere / Open ModelSphere** et **PG Modeler** dans les langages de BarrelMCD : **Python** (API) et **Dart** (Flutter). Aucun copier-coller de code : idées et règles uniquement.

---

## 1. Références et langages sources → cibles

| Logiciel | Langage(s) source | Licence | Logique forte | Où c’est transcrit |
|----------|-------------------|---------|----------------|---------------------|
| **Mocodo** | Python | MIT | Mots codés → MCD (grammaire, cardinalités 11/1N/01/0N) | Python : `api/services/mocodo_style_parser.py` |
| **OpenSphere / Open ModelSphere** | JavaScript / Java | GPL | Règles Merise, validation MCD, canvas relationnel | Python : `api/services/merise_rules.py` ; Flutter : `mcd_state.dart`, `mcd_canvas.dart` |
| **PG Modeler** | C++/Qt | GPLv3 | Modèle physique, DDL, tables BDD | Python : `mcd_service.mcd_to_mld` + `views.model_converter` (référence pour règles MLD/SQL) |

---

## 2. Détail par référence

### 2.1 Mocodo (mots codés → schéma)

- **Idée** : texte minimaliste (une ligne = entité avec attributs, ou association avec cardinalités) → MCD.
- **Transcription** :
  - **Python** : `api/services/mocodo_style_parser.py` — parser des lignes type `Entité: attr1, attr2` et `Assoc, 11 Entité1, 1N Entité2`, sortie en format canvas (entities, associations, association_links).
  - **API** : `POST /api/parse-mots-codes` → même format JSON que le canvas Flutter.
  - **Flutter** : appel à cette route puis `loadFromCanvasFormat` (existant) ; pas de logique métier Mocodo en Dart.

### 2.2 OpenSphere / Open ModelSphere (Merise, validation, canvas)

- **Idée** : cardinalités 0,1 | 1,1 | 0,n | 1,n ; noms uniques ; associations qui relient des entités ; pas de cycle d’héritage.
- **Transcription** :
  - **Python** : `api/services/merise_rules.py` — `normalize_cardinality`, `validate_mcd`, `validate_entity_names_unique`, `validate_association_entities`, `validate_cardinalities_on_links`, `validate_inheritance_no_cycle`. Utilisé par `mcd_service.validate_mcd` et par la conversion MCD → MLD.
  - **Flutter** : pas de duplication des règles ; le client envoie le MCD à l’API pour validation et pour MLD/SQL. Création d’entités/associations/liens et undo/redo restent en Dart (`mcd_state.dart`, `mcd_canvas.dart`).

### 2.3 PG Modeler (partie BDD)

- **Idée** : modèle physique (tables, colonnes, types, clés), génération DDL propre au SGBD.
- **Transcription** : on s’appuie sur la chaîne existante **MCD → MLD → MPD → SQL** dans `views/model_converter.py` ; les règles Merise (qui côté “n” porte la clé étrangère, table de liaison pour n-n) sont centralisées dans `merise_rules.py` et utilisées par `mcd_service._canvas_mcd_to_converter_format` et le converter. Aucune copie de code C++ : seule la logique (entité → table, association n-n → table de liaison, 1,n → FK) est reprise.

---

## 3. Où se trouve la logique métier (après transcription)

| Rôle | Fichier(s) Python | Fichier(s) Dart |
|------|--------------------|------------------|
| Cardinalités Merise (0,1 | 1,1 | 0,n | 1,n) | `merise_rules.py` | — (API) |
| Validation MCD (noms uniques, liens, cycles) | `merise_rules.py` | — (API) |
| Mots codés → MCD (style Mocodo) | `mocodo_style_parser.py` | — (API) |
| MCD (canvas) → format interne MLD/SQL | `mcd_service._canvas_mcd_to_converter_format` | — |
| MCD → MLD, MLD → SQL | `mcd_service` + `views.model_converter` | — |
| Création / déplacement entités, associations, liens | — | `mcd_state.dart`, `mcd_canvas.dart` |
| Undo / redo, chargement canvas | — | `mcd_state.dart` |

---

## 4. Ancienne logique supprimée ou évitée

- **Validation** : l’API ne s’appuie plus que sur `merise_rules.validate_mcd` pour la validation MCD. L’appel à `MarkdownMCDParser.validate_mcd` a été retiré de `mcd_service.validate_mcd` (vérifié : aucun autre appel à ce validateur dans le flux API/Flutter).
- **Import texte** : en plus du Markdown, l’entrée « mots codés » passe par `mocodo_style_parser` uniquement dans `api/services`, sans dupliquer de règles ailleurs.
- Les modules sous `views/` (parser Markdown, model_converter, etc.) restent utilisés par l’API pour le **parsing Markdown** et la conversion **MCD→MLD→SQL**, mais la logique métier Merise (validation, cardinalités, format canvas) est centralisée dans `api/services/` pour le flux Flutter.

### Vérification (aucune ancienne logique dans le flux API)

- `api/services/mcd_service.validate_mcd` n’appelle que `merise_validate_mcd` (aucun `parser.validate_mcd`).
- L’import « mots codés » ne passe que par `api/services/mocodo_style_parser.parse_mots_codes`.
- Les usages de `MarkdownMCDParser` dans `views/`, `test_*.py`, `cli_*`, `demo_*` concernent l’appli Qt et les tests ; ils ne font pas partie du flux API/Flutter.
