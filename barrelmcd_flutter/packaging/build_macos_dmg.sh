#!/usr/bin/env bash
# Build macOS .dmg (run on macOS only).
set -e
cd "$(dirname "$0")/.."
VERSION="1.0.0"
OUT_DIR="packaging/out"
DMG_NAME="BarrelMCD_Flutter-${VERSION}"
APP_BUNDLE="build/macos/Build/Products/Release/barrelmcd_flutter.app"

echo "==> flutter pub get"
flutter pub get
echo "==> flutter build macos --release"
flutter build macos --release

if [[ ! -d "$APP_BUNDLE" ]]; then
  echo "Erreur: $APP_BUNDLE introuvable."
  exit 1
fi

mkdir -p "$OUT_DIR"
DMG_TMP="$OUT_DIR/dmg_tmp"
rm -rf "$DMG_TMP"
mkdir -p "$DMG_TMP"
cp -R "$APP_BUNDLE" "$DMG_TMP/"
ln -s /Applications "$DMG_TMP/Applications"

echo "==> Création du DMG"
hdiutil create -volname "$DMG_NAME" -srcfolder "$DMG_TMP" -ov -format UDZO "$OUT_DIR/${DMG_NAME}.dmg"
rm -rf "$DMG_TMP"
echo "==> Créé: $OUT_DIR/${DMG_NAME}.dmg"
