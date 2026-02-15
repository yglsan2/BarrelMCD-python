#!/usr/bin/env bash
# Construit le paquet source Debian/PPA dans un conteneur Docker (Ubuntu 22.04).
# À lancer depuis la racine du dépôt BarrelMCD-python.
# Prérequis: Docker installé.

set -e
REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$REPO_ROOT"

IMAGE_NAME="${IMAGE_NAME:-barrelmcd-deb}"
SCRIPT_DIR="barrelmcd_flutter/packaging"

echo "==> Construction de l'image Docker (une fois) : $IMAGE_NAME"
docker build -t "$IMAGE_NAME" -f "$SCRIPT_DIR/Dockerfile.deb" .

echo "==> Lancement du build du paquet source dans le conteneur..."
docker run --rm \
  -v "$REPO_ROOT:/workspace" \
  -w /workspace \
  "$IMAGE_NAME" \
  ./barrelmcd_flutter/packaging/build_source_package.sh

echo "==> Fichiers générés dans $REPO_ROOT :"
ls -la "$REPO_ROOT"/barrelmcd-flutter_1.0.0*.dsc "$REPO_ROOT"/barrelmcd-flutter_1.0.0*-1_source.changes 2>/dev/null || true
echo ""
echo "Pour envoyer au PPA (sur une machine avec dput configuré) :"
echo "  cd $REPO_ROOT"
echo "  debsign -k VOTRE_CLE barrelmcd-flutter_1.0.0-1_source.changes"
echo "  dput ppa:VOTRE_ID/ppa barrelmcd-flutter_1.0.0-1_source.changes"
