#!/usr/bin/env bash
# Build .deb for Debian/Ubuntu (BarrelMCD Flutter)
set -e
cd "$(dirname "$0")/.."
APP_NAME="barrelmcd-flutter"
VERSION="1.0.0"
ARCH="amd64"
BUNDLE_DIR="build/linux/x64/release/bundle"
OUT_DIR="packaging/out"
PKG_DIR="${OUT_DIR}/${APP_NAME}_${VERSION}_${ARCH}"

echo "==> flutter pub get"
flutter pub get
echo "==> flutter build linux --release"
flutter build linux --release

if [[ ! -d "$BUNDLE_DIR" ]]; then
  echo "Erreur: $BUNDLE_DIR introuvable."
  exit 1
fi

mkdir -p "${PKG_DIR}/DEBIAN"
mkdir -p "${PKG_DIR}/opt/barrelmcd-flutter"
mkdir -p "${PKG_DIR}/usr/share/applications"
mkdir -p "${PKG_DIR}/usr/bin"

echo "==> Copie du bundle vers package"
cp -r "$BUNDLE_DIR"/* "${PKG_DIR}/opt/barrelmcd-flutter/"

# Script de lancement
cat > "${PKG_DIR}/usr/bin/barrelmcd-flutter" << 'LAUNCHER'
#!/bin/sh
exec /opt/barrelmcd-flutter/barrelmcd_flutter "$@"
LAUNCHER
chmod 755 "${PKG_DIR}/usr/bin/barrelmcd-flutter"

# Desktop entry
cat > "${PKG_DIR}/usr/share/applications/barrelmcd-flutter.desktop" << 'DESKTOP'
[Desktop Entry]
Name=BarrelMCD Flutter
Comment=Modélisation conceptuelle de données (MCD)
Exec=/opt/barrelmcd-flutter/barrelmcd_flutter
Icon=/opt/barrelmcd-flutter/data/flutter_assets/assets/images/logo.png
Terminal=false
Type=Application
Categories=Development;Office;
DESKTOP

# DEBIAN/control
cat > "${PKG_DIR}/DEBIAN/control" << ENDCONTROL
Package: $APP_NAME
Version: $VERSION
Section: devel
Priority: optional
Architecture: $ARCH
Maintainer: DesertYGL
Description: Interface Flutter pour BarrelMCD - Modélisation conceptuelle de données (MCD)
 Dessin d'entités, associations, liens avec cardinalités.
 Export MLD, MPD, SQL. Licence GPL-3.0.
Homepage: https://github.com/yglsan2/BarrelMCD-python
ENDCONTROL

dpkg-deb --build --root-owner-group "${PKG_DIR}" "${OUT_DIR}/${APP_NAME}_${VERSION}_${ARCH}.deb"
rm -rf "${PKG_DIR}"
echo "==> Créé: ${OUT_DIR}/${APP_NAME}_${VERSION}_${ARCH}.deb"
