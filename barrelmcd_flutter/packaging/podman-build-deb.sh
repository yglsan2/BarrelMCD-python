#!/usr/bin/env bash
# Construit le paquet source Debian/PPA dans un conteneur (Ubuntu 22.04).
# Utilise Podman. À lancer depuis la racine du dépôt BarrelMCD-python.
# Prérequis: Podman (pacman -S podman).
#
# Si en rootless le réseau échoue (pasta/tun), lancer avec sudo pour avoir
# le réseau dans le conteneur : sudo ./barrelmcd_flutter/packaging/podman-build-deb.sh

set -e
REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$REPO_ROOT"

IMAGE_NAME="${IMAGE_NAME:-barrelmcd-deb}"
SCRIPT_DIR="barrelmcd_flutter/packaging"

echo "==> Construction de l'image (une fois) : $IMAGE_NAME"
podman build -t "$IMAGE_NAME" -f "$SCRIPT_DIR/Dockerfile.deb" .

# En root (sudo), le conteneur a le réseau ; en rootless, pas de /dev/net/tun donc on monte le cache Pub.
if [[ -n "$(id -u 2>/dev/null)" && "$(id -u)" -eq 0 ]]; then
  echo "==> Lancement du build (réseau disponible en root)..."
  podman run --rm \
    -v "$REPO_ROOT:/workspace:z" \
    -w /workspace \
    "$IMAGE_NAME" \
    ./barrelmcd_flutter/packaging/build_source_package.sh
else
  echo "==> Remplissage du cache Pub sur l'hôte..."
  (cd "$REPO_ROOT/barrelmcd_flutter" && flutter pub get) || true
  PUB_CACHE="${PUB_CACHE:-$HOME/.pub-cache}"
  echo "==> Lancement du build (sans réseau, cache Pub monté)..."
  podman run --rm --network=none \
    -e PUB_CACHE=/root/.pub-cache \
    -v "$REPO_ROOT:/workspace:z" \
    -v "${PUB_CACHE}:/root/.pub-cache:z" \
    -w /workspace \
    "$IMAGE_NAME" \
    ./barrelmcd_flutter/packaging/build_source_package.sh --offline
fi

echo "==> Fichiers générés dans $REPO_ROOT :"
ls -la "$REPO_ROOT"/barrelmcd-flutter_1.0.0*.dsc "$REPO_ROOT"/barrelmcd-flutter_1.0.0*-1_source.changes 2>/dev/null || true
echo ""
echo "Pour envoyer au PPA (sur une machine avec dput configuré) :"
echo "  cd $REPO_ROOT"
echo "  debsign -k VOTRE_CLE barrelmcd-flutter_1.0.0-1_source.changes"
echo "  dput ppa:VOTRE_ID/ppa barrelmcd-flutter_1.0.0-1_source.changes"
