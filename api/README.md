# API BarrelMCD

Backend FastAPI pour l'interface Flutter. Expose la logique MCD/MLD/SQL et le parsing Markdown **sans dépendance Qt**.

## Installation

Le script `run_api.sh` crée un **environnement virtuel** (`.venv`) dans le projet et y installe les dépendances. Aucune installation système (pip, etc.) n’est nécessaire.

Les modules `views` et `models` du projet Python sont utilisés (parser Markdown, ModelConverter, DataAnalyzer). PyQt n'est pas requis pour l'API.

## Lancement

À la racine du projet :
```bash
./run_api.sh
```

La première exécution crée `.venv` et installe les dépendances ; les suivantes lancent directement l’API.

**Sans le script (venv manuel) :**
```bash
cd /chemin/vers/BarrelMCD-python
python3 -m venv .venv
.venv/bin/pip install -r api/requirements.txt
.venv/bin/python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

## Endpoints

| Méthode | Route | Description |
|---------|--------|-------------|
| GET | `/health` | Santé du serveur |
| POST | `/api/parse-markdown` | Body: `{ "content": "..." }` → structure MCD + format canvas |
| POST | `/api/validate` | Body: `{ "mcd": { ... } }` → `{ "valid", "errors" }` |
| POST | `/api/to-mld` | Body: `{ "mcd": { ... } }` → MLD |
| POST | `/api/to-sql` | Body: `{ "mcd": { ... } }` → `{ "sql": "..." }` |
| POST | `/api/analyze-data` | Body: `{ "data": [...], "format_type": "json" }` → MCD analysé |

Le format MCD (canvas) attendu est décrit dans `docs/INTERFACE_ANALYSE_FLUTTER.md`.
