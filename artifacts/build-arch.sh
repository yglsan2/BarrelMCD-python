#!/usr/bin/env bash
# À lancer en tant qu'utilisateur normal (pas root) pour produire le .pkg.tar.zst
set -e
cd "$(dirname "$0")/arch-build"
makepkg -s --noconfirm
echo "Paquet produit : $(ls -1 barrelmcd-flutter-*.pkg.tar.zst 2>/dev/null)"
for f in barrelmcd-flutter-*.pkg.tar.zst; do [[ "$f" == *-debug-* ]] || cp "$f" ..; done 2>/dev/null || true
