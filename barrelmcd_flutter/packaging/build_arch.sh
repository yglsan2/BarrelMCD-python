#!/usr/bin/env bash
# Build Arch Linux package from current clone (no tarball).
# Run from barrelmcd_flutter or from BarrelMCD-python root.
set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
if [[ -d "$SCRIPT_DIR/../barrelmcd_flutter" ]]; then
  ROOT="$SCRIPT_DIR/.."
  FLUTTER_DIR="$ROOT/barrelmcd_flutter"
else
  ROOT="$SCRIPT_DIR/../.."
  FLUTTER_DIR="$SCRIPT_DIR/.."
fi
cd "$FLUTTER_DIR"
VERSION="1.0.0"
OUT_DIR="$SCRIPT_DIR/out"
PKG_DIR="${OUT_DIR}/pkg"
mkdir -p "$OUT_DIR" "$PKG_DIR/opt/barrelmcd-flutter" "$PKG_DIR/usr/bin" "$PKG_DIR/usr/share/applications" "$PKG_DIR/usr/share/licenses/barrelmcd-flutter"

echo "==> flutter pub get"
flutter pub get
echo "==> flutter build linux --release"
flutter build linux --release

BUNDLE="$FLUTTER_DIR/build/linux/x64/release/bundle"
if [[ ! -d "$BUNDLE" ]]; then
  echo "Erreur: $BUNDLE introuvable."
  exit 1
fi

echo "==> Copie du bundle"
cp -r "$BUNDLE"/* "$PKG_DIR/opt/barrelmcd-flutter/"
echo '#!/bin/sh
exec /opt/barrelmcd-flutter/barrelmcd_flutter "$@"' > "$PKG_DIR/usr/bin/barrelmcd-flutter"
chmod 755 "$PKG_DIR/usr/bin/barrelmcd-flutter"
cp LICENSE "$PKG_DIR/usr/share/licenses/barrelmcd-flutter/"
cat > "$PKG_DIR/usr/share/applications/barrelmcd-flutter.desktop" << 'DESKTOP'
[Desktop Entry]
Name=BarrelMCD Flutter
Comment=Modélisation conceptuelle de données (MCD)
Exec=/opt/barrelmcd-flutter/barrelmcd_flutter
Icon=/opt/barrelmcd-flutter/data/flutter_assets/assets/images/logo.png
Terminal=false
Type=Application
Categories=Development;Office;
DESKTOP

echo "==> Création du paquet .pkg.tar.zst"
cd "$PKG_DIR"
tar --sort=name --mtime="@0" -cf - . | zstd -o "${OUT_DIR}/barrelmcd-flutter-${VERSION}-1-x86_64.pkg.tar.zst"
cd - >/dev/null
rm -rf "$PKG_DIR"
echo "==> Créé: ${OUT_DIR}/barrelmcd-flutter-${VERSION}-1-x86_64.pkg.tar.zst"
echo "Installation: sudo pacman -U ${OUT_DIR}/barrelmcd-flutter-${VERSION}-1-x86_64.pkg.tar.zst"
