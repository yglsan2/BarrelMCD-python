#!/usr/bin/env bash
# Génère le .deb dans un conteneur Ubuntu. À lancer depuis la racine du dépôt.
# Usage: ./artifacts/build-deb-podman.sh
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

# S'assurer que le bundle est à jour dans barrelmcd-flutter-1.0.0
if [[ -d barrelmcd_flutter/build/linux/x64/release/bundle ]]; then
  echo "==> Sync bundle vers barrelmcd-flutter-1.0.0..."
  cp -r barrelmcd_flutter/build/linux/x64/release/bundle/* barrelmcd-flutter-1.0.0/ 2>/dev/null || true
fi

echo "==> Build .deb dans Ubuntu 22.04 (podman)..."
podman run --rm -v "$ROOT:/work:rw" -w /work ubuntu:22.04 bash -c '
  apt-get update -qq && apt-get install -y -qq devscripts debhelper build-essential > /dev/null
  cd barrelmcd-flutter-1.0.0 && debuild -b -us -uc
'

echo "==> Copie du .deb vers artifacts/"
cp -v barrelmcd-flutter_1.0.0-1_amd64.deb artifacts/ 2>/dev/null || cp -v barrelmcd-flutter_1.0.0-1_amd64.deb "$ROOT/artifacts/"
echo "Terminé. Fichiers dans artifacts/:"
ls -la artifacts/*.deb artifacts/*.tar.gz 2>/dev/null || true
