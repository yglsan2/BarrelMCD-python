#!/bin/bash
# Push vers GitHub : commits sans cosignature (cursoragent) et sans mention Katyusha.
set -e
cd "$(dirname "$0")"
echo "Dernier commit local :"
git log -1 --oneline HEAD
echo ""
echo "Envoi vers origin/main..."
git push origin main --force-with-lease
echo ""
echo "OK. Sur GitHub : plus de cursoragent ni de Katyusha dans les pushes."
