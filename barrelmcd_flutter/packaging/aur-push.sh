#!/usr/bin/env bash
# À lancer depuis BarrelMCD-python (pas depuis aur-barrelmcd).
# Usage: ./barrelmcd_flutter/packaging/aur-push.sh

set -e
REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
AUR_DIR="$REPO_ROOT/aur-barrelmcd"

if [[ ! -d "$AUR_DIR" ]]; then
  echo "Clone AUR d'abord :"
  echo "  cd $REPO_ROOT"
  echo "  git -c init.defaultBranch=master clone ssh://aur@aur.archlinux.org/barrelmcd-flutter.git aur-barrelmcd"
  exit 1
fi

echo "==> Copie PKGBUILD et LICENSE dans le clone AUR..."
cp "$REPO_ROOT/barrelmcd_flutter/packaging/PKGBUILD.aur" "$AUR_DIR/PKGBUILD"
cp "$REPO_ROOT/barrelmcd_flutter/packaging/LICENSE.aur" "$AUR_DIR/LICENSE"

echo "==> Génération de .SRCINFO (nécessite makepkg)..."
(cd "$AUR_DIR" && makepkg --printsrcinfo > .SRCINFO)

echo "==> Fichiers prêts dans $AUR_DIR"
echo "Édite la ligne # Maintainer: dans $AUR_DIR/PKGBUILD puis :"
echo "  cd $AUR_DIR"
echo "  git add PKGBUILD .SRCINFO LICENSE"
echo "  git commit -m 'Initial commit: barrelmcd-flutter 1.0.0'"
echo "  git push origin master"
