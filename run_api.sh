#!/bin/bash
# Lance l'API BarrelMCD (backend pour l'interface Flutter)
# Utilise un venv pour éviter "externally-managed-environment" (Arch / PEP 668).

set -e
cd "$(dirname "$0")"
VENV_DIR=".venv"

# Créer le venv s'il n'existe pas
if [ ! -d "$VENV_DIR" ]; then
  echo "Création de l'environnement virtuel dans $VENV_DIR..."
  python3 -m venv "$VENV_DIR"
fi

# Installer / mettre à jour les dépendances
echo "Installation des dépendances API..."
"$VENV_DIR/bin/pip" install -q -r api/requirements.txt

echo "Démarrage de l'API sur http://127.0.0.0:8000"
exec "$VENV_DIR/bin/python" -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
