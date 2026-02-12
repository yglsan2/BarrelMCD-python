#!/usr/bin/env bash
# Analyse radare2 ciblée sur la fonctionnalité "Recherche SQL" de Looping.exe
# Usage: ./radare2_looping_sql_search.sh [chemin/Looping.exe] [répertoire_sortie]
# Exemple: ./radare2_looping_sql_search.sh ~/Téléchargements/Looping.exe docs/analysis_output

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

# Vérifier que r2 est disponible
if ! command -v r2 &>/dev/null; then
  echo "radare2 (r2) n'est pas installé ou pas dans le PATH." >&2
  echo "Installation: https://rada.re/n/radare2.html" >&2
  exit 1
fi

R2_OPTS="-q -e bin.relocs.apply=true -e bin.cache=true"

# 1) Toutes les chaînes (izz)
echo "[1/4] Extraction de toutes les chaînes (izz)..."
r2 $R2_OPTS -c "izz" "$LOOPING_EXE" 2>/dev/null > "$OUTPUT_DIR/looping_izz.txt" || true
wc -l < "$OUTPUT_DIR/looping_izz.txt" | xargs echo "  Lignes:"

# 2) Filtre "SQL Search" / recherche / requêtes / procédures / triggers / vues / dépendances
echo "[2/4] Filtrage des chaînes liées à la recherche SQL..."
GREP_PATTERN="recherche|search|requête|query|sql|procédure|trigger|vue|view|contrainte|dépendance|dependency|stored|procedure|chercher|find|filtre|résultat|résultats|objet|reference|référence"
grep -iE "$GREP_PATTERN" "$OUTPUT_DIR/looping_izz.txt" > "$OUTPUT_DIR/looping_sql_search_strings.txt" || true
wc -l < "$OUTPUT_DIR/looping_sql_search_strings.txt" | xargs echo "  Chaînes retenues:"
if [[ -s "$OUTPUT_DIR/looping_sql_search_strings.txt" ]]; then
  echo "  Fichier: $OUTPUT_DIR/looping_sql_search_strings.txt"
fi

# 3) Infos binaire (sections, entrées)
echo "[3/4] Informations binaire (sections, format)..."
r2 $R2_OPTS -c "iI; iS" "$LOOPING_EXE" 2>/dev/null > "$OUTPUT_DIR/looping_bininfo.txt" || true
echo "  Fichier: $OUTPUT_DIR/looping_bininfo.txt"

# 4) Liste des fonctions (après analyse aaa) — optionnel, peut être long
echo "[4/4] Analyse des fonctions (aaa; afl) — peut prendre du temps..."
r2 $R2_OPTS -c "aaa; afl" "$LOOPING_EXE" 2>/dev/null > "$OUTPUT_DIR/looping_functions.txt" || true
wc -l < "$OUTPUT_DIR/looping_functions.txt" | xargs echo "  Fonctions:"
echo "  Fichier: $OUTPUT_DIR/looping_functions.txt"

echo ""
echo "Terminé. Pour analyser les xrefs vers une chaîne, ouvrez une session r2:"
echo "  r2 -e bin.relocs.apply=true \"$LOOPING_EXE\""
echo "  Puis: izz~VotreChaîne  pour trouver l'adresse, puis  s ADRESSE  et  axt  pour les références."
echo ""
echo "Voir aussi: docs/ANALYSE_RADARE2_LOOPING_SQL_SEARCH.md"
