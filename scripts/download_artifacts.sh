#!/usr/bin/env bash
# Télécharge les artifacts Windows et macOS du workflow "Build Windows et macOS".
# Usage: GITHUB_TOKEN=ton_token ./scripts/download_artifacts.sh
# Token : https://github.com/settings/tokens (cocher scope "repo" ou "actions: read")

set -e
OWNER="yglsan2"
REPO="BarrelMCD-python"
OUT_DIR="packaging/out"
mkdir -p "$OUT_DIR"

# Token : variable GITHUB_TOKEN ou fichier ~/Documents/github_token.txt
if [[ -z "$GITHUB_TOKEN" ]]; then
  if [[ -r "$HOME/Documents/github_token.txt" ]]; then
    GITHUB_TOKEN=$(cat "$HOME/Documents/github_token.txt" | tr -d '\n\r')
    echo "==> Token lu depuis $HOME/Documents/github_token.txt"
  fi
fi
if [[ -z "$GITHUB_TOKEN" ]]; then
  echo "Usage: GITHUB_TOKEN=ton_token $0"
  echo "Ou place ton token dans ~/Documents/github_token.txt (une ligne)"
  exit 1
fi

AUTH="Authorization: token $GITHUB_TOKEN"
API="https://api.github.com/repos/${OWNER}/${REPO}"

echo "==> Récupération du dernier run réussi..."
RUNS=$(curl -s -w "\n%{http_code}" -H "$AUTH" "${API}/actions/runs?per_page=20&status=completed")
HTTP_CODE=$(echo "$RUNS" | tail -1)
RUNS_JSON=$(echo "$RUNS" | sed '$d')
if [[ "$HTTP_CODE" == "401" ]]; then
  echo "Erreur 401 : token invalide ou expiré."
  echo "Vérifie ton token sur https://github.com/settings/tokens (scope 'repo' ou 'actions: read')."
  exit 1
fi
if [[ "$HTTP_CODE" != "200" ]]; then
  echo "Erreur HTTP $HTTP_CODE : $(echo "$RUNS_JSON" | jq -r '.message // .' 2>/dev/null)"
  exit 1
fi
RUN_ID=$(echo "$RUNS_JSON" | jq -r '.workflow_runs[] | select(.name == "Build Windows et macOS" and .conclusion == "success") | .id' | head -1)

if [[ -z "$RUN_ID" || "$RUN_ID" == "null" ]]; then
  echo "Aucun run réussi trouvé pour le workflow 'Build Windows et macOS'."
  echo "Réponse (extrait): $(echo "$RUNS_JSON" | jq -c '.workflow_runs[0:2] | .[].name' 2>/dev/null || echo "$RUNS_JSON" | head -c 200)"
  exit 1
fi

echo "   Run ID: $RUN_ID"
echo "==> Liste des artifacts de ce run..."
ARTIFACTS=$(curl -s -H "$AUTH" "${API}/actions/runs/${RUN_ID}/artifacts")

WIN_URL=$(echo "$ARTIFACTS" | jq -r '.artifacts[] | select(.name=="BarrelMCD-Flutter-Windows-x64") | .archive_download_url' | head -1)
MAC_URL=$(echo "$ARTIFACTS" | jq -r '.artifacts[] | select(.name=="BarrelMCD-Flutter-macOS") | .archive_download_url' | head -1)

if [[ -z "$WIN_URL" || "$WIN_URL" == "null" ]]; then
  echo "Artifact Windows introuvable dans ce run."
  echo "Artifacts disponibles: $(echo "$ARTIFACTS" | jq -r '.artifacts[].name' 2>/dev/null)"
  exit 1
fi
if [[ -z "$MAC_URL" || "$MAC_URL" == "null" ]]; then
  echo "Artifact macOS introuvable dans ce run."
  exit 1
fi

echo "==> Téléchargement Windows..."
curl -sL -H "$AUTH" -H "Accept: application/vnd.github+json" \
  "$WIN_URL" -o "$OUT_DIR/BarrelMCD-Flutter-Windows-x64.zip"
echo "   -> $OUT_DIR/BarrelMCD-Flutter-Windows-x64.zip"

echo "==> Téléchargement macOS..."
curl -sL -H "$AUTH" -H "Accept: application/vnd.github+json" \
  "$MAC_URL" -o "$OUT_DIR/BarrelMCD-Flutter-macOS.zip"
echo "   -> $OUT_DIR/BarrelMCD-Flutter-macOS.zip"

echo "==> Terminé. Décompresse les .zip pour obtenir le contenu (exe / dmg)."
