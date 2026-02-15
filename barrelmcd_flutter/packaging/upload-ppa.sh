#!/usr/bin/env bash
# Signe et envoie le paquet source au PPA Launchpad.
# À lancer sur Ubuntu (ou dans un conteneur Ubuntu avec ta clé GPG).
# Usage: ./upload-ppa.sh [répertoire des .changes] [ppa:TON_ID/ppa] [optionnel: KEYID]
set -e
DEST="${1:-.}"
PPA="${2:?Usage: $0 <répertoire> <ppa:launchpad_id/ppa> [keyid]}"
KEYID="${3:-}"

cd "$DEST"
CHANGES=$(ls -1 barrelmcd-flutter_*-1_source.changes 2>/dev/null | head -1)
[[ -n "$CHANGES" ]] || { echo "Aucun fichier .changes dans $DEST"; exit 1; }

if [[ -n "$KEYID" ]]; then
  debsign -k "$KEYID" "$CHANGES"
else
  debsign "$CHANGES"
fi
dput "$PPA" "$CHANGES"
