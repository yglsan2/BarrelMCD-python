#!/usr/bin/env bash
# Construit le paquet source pour Debian/PPA (barrelmcd-flutter).
# À lancer depuis barrelmcd_flutter/ ou depuis BarrelMCD-python.
# Prérequis: devscripts, build-essential, debhelper

set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT"

VERSION="1.0.0"
PKG_NAME="barrelmcd-flutter"
ORIG_TARBALL="${PKG_NAME}_${VERSION}.orig.tar.gz"
BUILD_DIR="$(dirname "$ROOT")/${PKG_NAME}-${VERSION}"

echo "==> Build Flutter Linux (release)..."
OFFLINE=""
for arg in "$@"; do [[ "$arg" == "--offline" ]] && OFFLINE=1; done
if [[ -n "$OFFLINE" || -n "${FLUTTER_PUB_OFFLINE:-}" ]]; then
  echo "==> flutter pub get --offline"
  flutter pub get --offline
else
  flutter pub get
fi
echo "==> flutter build linux --release"
flutter build linux --release

BUNDLE="$ROOT/build/linux/x64/release/bundle"
if [[ ! -d "$BUNDLE" ]]; then
  echo "Erreur: bundle introuvable ($BUNDLE)"
  exit 1
fi

echo "==> Préparation du répertoire source..."
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"
cp -r "$BUNDLE"/* "$BUILD_DIR/"

echo "==> Création de l'archive orig..."
(cd "$(dirname "$BUILD_DIR")" && tar czvf "$ORIG_TARBALL" "$(basename "$BUILD_DIR")")

echo "==> Copie de debian/..."
cp -r "$ROOT/debian" "$BUILD_DIR/"

echo "==> Construction du paquet source (debuild -S -sa)..."
cd "$BUILD_DIR"
debuild -S -sa -d

DEST="$(dirname "$BUILD_DIR")"
echo "==> Terminé. Fichiers dans $DEST:"
ls -la "$DEST"/${PKG_NAME}_${VERSION}*.dsc "$DEST"/${PKG_NAME}_${VERSION}*-1_source.changes 2>/dev/null || true
echo ""
echo "Pour envoyer au PPA (remplacer VOTRE_ID par ton identifiant Launchpad):"
echo "  cd $DEST && dput ppa:VOTRE_ID/ppa ${PKG_NAME}_${VERSION}-1_source.changes"
echo ""
echo "Si besoin de signer avec une clé GPG :"
echo "  debsign -k VOTRE_CLE $DEST/${PKG_NAME}_${VERSION}-1_source.changes"
