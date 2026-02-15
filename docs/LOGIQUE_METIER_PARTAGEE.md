# Logique métier partagée (Flutter + API Python)

Pour gagner du temps, la logique métier « lourde » est centralisée côté **API Python** et réutilisée par Flutter via HTTP.

## Où se trouve quoi

| Rôle | Côté Python (API) | Côté Flutter |
|------|--------------------|--------------|
| **Création entité / association** | Référence : `views/interactive_canvas.py` (`create_entity`, `create_association`) | `mcd_state.dart` (`addEntity`, `addAssociation`), `mcd_canvas.dart` (dialogs) |
| **Validation MCD** (règles Merise / Barrel) | `api/services/merise_rules.py` + `mcd_service.validate_mcd()` | Appel HTTP `POST /validate` |
| **Cardinalités** (0,1 | 1,1 | 0,n | 1,n) | `merise_rules.normalize_cardinality()` | Utilisé côté API ; Flutter envoie le MCD, l’API normalise |
| **MCD → MLD** | `mcd_service.mcd_to_mld()` | `POST /to-mld` |
| **Génération SQL** | `mcd_service.mcd_to_sql()` | `POST /to-sql` |
| **Import Markdown** | `mcd_service.parse_markdown()` + `markdown_to_canvas_format()` | `POST /parse-markdown` |

## Réutiliser la logique existante

- **Ajouter une règle Merise / Barrel** : l’écrire dans `api/services/merise_rules.py`, puis l’appeler dans `validate_mcd()`. Règles actuelles : cardinalités 0,1|1,1|0,n|1,n ; 1,1 interdite si association porteuse de rubriques ; rubriques uniquement en association n-n (table de correspondance) ; pas de doublons dans les rubriques ; type obligatoire pour chaque rubrique ; chaque entité doit être reliée à au moins une association ; pas de cycle d’héritage. Flutter n’a rien à changer : il appelle `POST /validate` et affiche les erreurs.
- **S’inspirer du flux Python** : `views/interactive_canvas.py` (modes `add_entity`, `add_association`, création de liens) et `views/main_window.py` (menus, raccourcis) décrivent le flux complet ; le canvas Flutter reproduit le même enchaînement (mode → clic → dialog → mise à jour état).
- **Format commun** : le MCD est échangé en JSON (entités, associations, association_links, inheritance_links) entre Flutter et l’API ; `mcd_service._canvas_mcd_to_converter_format()` adapte ce format pour le reste du backend.

## Démarrage

- API : `cd BarrelMCD-python && .venv/bin/python -m uvicorn api.main:app --reload --port 8000`
- Flutter : `cd barrelmcd_flutter && flutter run`

Flutter doit pointer vers `http://127.0.0.1:8000` (voir `lib/main.dart`).
