#!/usr/bin/env bash
# Crée une Release GitHub v1.0.0 et y attache les 4 installables.
# Prérequis : les 4 fichiers dans barrelmcd_flutter/packaging/out/ OU packaging/out/
# (Windows/macOS = souvent packaging/out/, .deb et .pkg = souvent barrelmcd_flutter/packaging/out/)
# Token : GITHUB_TOKEN ou ~/Documents/github_token.txt

set -e
OWNER="yglsan2"
REPO="BarrelMCD-python"
TAG="v1.0.0"
OUT_FLUTTER="barrelmcd_flutter/packaging/out"
OUT_ROOT="packaging/out"

if [[ -z "$GITHUB_TOKEN" ]] && [[ -r "$HOME/Documents/github_token.txt" ]]; then
  GITHUB_TOKEN=$(cat "$HOME/Documents/github_token.txt" | tr -d '\n\r')
fi
if [[ -z "$GITHUB_TOKEN" ]]; then
  echo "GITHUB_TOKEN non défini. Utilise ~/Documents/github_token.txt ou export GITHUB_TOKEN=..."
  exit 1
fi

AUTH="Authorization: token $GITHUB_TOKEN"
API="https://api.github.com/repos/${OWNER}/${REPO}"

# Cherche chaque fichier dans les deux dossiers possibles
find_asset() {
  local name="$1"
  [[ -f "$OUT_FLUTTER/$name" ]] && echo "$OUT_FLUTTER/$name" && return
  [[ -f "$OUT_ROOT/$name" ]] && echo "$OUT_ROOT/$name" && return
  echo ""
}
WIN_ZIP=$(find_asset "BarrelMCD-Flutter-Windows-x64.zip")
MAC_ZIP=$(find_asset "BarrelMCD-Flutter-macOS.zip")
DEB=$(find_asset "barrelmcd-flutter_1.0.0_amd64.deb")
ARCH_PKG=$(find_asset "barrelmcd-flutter-1.0.0-1-x86_64.pkg.tar.zst")

for label in "Windows zip:WIN_ZIP" "macOS zip:MAC_ZIP" ".deb:DEB" "Arch pkg:ARCH_PKG"; do
  desc="${label%%:*}"
  var="${label##*:}"
  path="${!var}"
  if [[ -z "$path" || ! -f "$path" ]]; then
    echo "Fichier manquant ($desc): cherché dans $OUT_FLUTTER et $OUT_ROOT"
    exit 1
  fi
done

echo "==> Création de la release $TAG..."
BODY=$(cat << 'BODY'
**BarrelMCD Flutter 1.0.0** — Installables pour toutes les plateformes.

| Fichier | Plateforme |
|---------|------------|
| BarrelMCD-Flutter-Windows-x64.zip | Windows (décompresser puis lancer barrelmcd_flutter.exe) |
| BarrelMCD-Flutter-macOS.zip | macOS (décompresser pour obtenir le .dmg) |
| barrelmcd-flutter_1.0.0_amd64.deb | Debian / Ubuntu |
| barrelmcd-flutter-1.0.0-1-x86_64.pkg.tar.zst | Arch Linux |

Licence : GPL v3. Auteur : DesertYGL.
BODY
)
RESP=$(curl -s -X POST -H "$AUTH" -H "Content-Type: application/json" \
  "$API/releases" \
  -d "{\"tag_name\":\"$TAG\",\"name\":\"BarrelMCD Flutter 1.0.0\",\"body\":$(echo "$BODY" | jq -Rs .)}")

UPLOAD_URL=$(echo "$RESP" | jq -r '.upload_url')
if [[ -z "$UPLOAD_URL" || "$UPLOAD_URL" == "null" ]]; then
  MSG=$(echo "$RESP" | jq -r '.message // .')
  echo "Erreur création release: $MSG"
  exit 1
fi
# upload_url est du type https://uploads.github.com/.../assets{?name,label}
UPLOAD_BASE="${UPLOAD_URL%\{*}"
echo "   Release créée."

upload_asset() {
  local path="$1"
  local name=$(basename "$path")
  local mime="$2"
  echo "==> Upload $name..."
  curl -s -X POST -H "$AUTH" -H "Content-Type: $mime" \
    "$UPLOAD_BASE?name=$name" \
    --data-binary @"$path" > /dev/null
}

upload_asset "$WIN_ZIP" "application/zip"
upload_asset "$MAC_ZIP" "application/zip"
upload_asset "$DEB" "application/vnd.debian.binary-package"
upload_asset "$ARCH_PKG" "application/zstd"

echo "==> Terminé. Release: https://github.com/${OWNER}/${REPO}/releases/tag/${TAG}"
echo ""
echo "Pour pousser le tag et la release (si le tag n'existait pas encore) :"
echo "  git tag $TAG"
echo "  git push origin $TAG"
