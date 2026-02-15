#!/usr/bin/env bash
# Analyse radare2 ciblée sur le COMPORTEMENT de Looping (souris, drag, pan, sélection, hit-test).
# Usage: ./radare2_looping_behavior.sh [chemin/Looping.exe] [répertoire_sortie]
# Exemple: ./radare2_looping_behavior.sh ~/Téléchargements/Looping.exe docs/analysis_output

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
if [[ -n "$1" ]]; then
  LOOPING_EXE="$1"
else
  if [[ -f "$REPO_ROOT/Looping.exe" ]]; then
    LOOPING_EXE="$REPO_ROOT/Looping.exe"
  elif [[ -f "$HOME/Téléchargements/Looping.exe" ]]; then
    LOOPING_EXE="$HOME/Téléchargements/Looping.exe"
  elif [[ -f "$HOME/Téléchargements/Looping_32bits.exe" ]]; then
    LOOPING_EXE="$HOME/Téléchargements/Looping_32bits.exe"
  else
    LOOPING_EXE="$REPO_ROOT/Looping.exe"
  fi
fi
OUTPUT_DIR="${2:-$REPO_ROOT/docs/analysis_output}"

if [[ ! -f "$LOOPING_EXE" ]]; then
  echo "Fichier non trouvé: $LOOPING_EXE" >&2
  echo "Téléchargez Looping depuis https://www.looping-mcd.fr/ et indiquez le chemin vers Looping.exe" >&2
  echo "Usage: $0 [chemin/Looping.exe] [répertoire_sortie]" >&2
  exit 1
fi

mkdir -p "$OUTPUT_DIR"
echo "Binaire: $LOOPING_EXE"
echo "Sortie:  $OUTPUT_DIR"
echo ""

if ! command -v r2 &>/dev/null; then
  echo "radare2 (r2) n'est pas installé ou pas dans le PATH." >&2
  echo "Installation: https://rada.re/n/radare2.html" >&2
  exit 1
fi

R2_OPTS="-q -e bin.relocs.apply=true -e bin.cache=true"

# 1) Toutes les chaînes
echo "[1/3] Extraction des chaînes (izz)..."
r2 $R2_OPTS -c "izz" "$LOOPING_EXE" 2>/dev/null > "$OUTPUT_DIR/looping_izz.txt" || true
wc -l < "$OUTPUT_DIR/looping_izz.txt" | xargs echo "  Lignes:"

# 2) Filtre comportement : souris, drag, pan, sélection, hit, clic, déplacement
echo "[2/3] Filtrage chaînes comportement (souris, drag, pan, hit-test, sélection)..."
GREP_BEHAVIOR="souris|mouse|clic|click|drag|glisser|deplacer|move|pan|scroll|selection|select|hit|WM_|LBUTTON|RBUTTON|OnMouse|MouseDown|MouseMove|MouseUp|Capture|Deplacer|Déplacer|HitTest|accHitTest|accSelection|DragMinDist|DragDelay|DoubleClick|RetourOutilSelection|EpaississementSelection|Clic droit|CScrollView|GETDRAGBOUNDS|DRAGCOMPLETE|TABGROUPMOUSEMOVE|DragScroll|CDrawArc|CDrawRelation|CDrawEntite"
grep -iE "$GREP_BEHAVIOR" "$OUTPUT_DIR/looping_izz.txt" > "$OUTPUT_DIR/looping_behavior_strings.txt" 2>/dev/null || true
wc -l < "$OUTPUT_DIR/looping_behavior_strings.txt" 2>/dev/null | xargs echo "  Chaînes retenues:" || echo "  0"
if [[ -s "$OUTPUT_DIR/looping_behavior_strings.txt" ]]; then
  echo "  Fichier: $OUTPUT_DIR/looping_behavior_strings.txt"
fi

# 3) Infos binaire
echo "[3/3] Infos binaire (iI; iS)..."
r2 $R2_OPTS -c "iI; iS" "$LOOPING_EXE" 2>/dev/null > "$OUTPUT_DIR/looping_bininfo_behavior.txt" || true

echo ""
echo "Terminé. Voir docs/COMPORTEMENT_LOOPING_ANALYSE_RADARE2.md pour les critères BarrelMCD."
echo "Pour xrefs sur une chaîne: r2 -e bin.relocs.apply=true \"$LOOPING_EXE\" puis izz~VotreChaîne, s ADRESSE, axt"
echo ""
