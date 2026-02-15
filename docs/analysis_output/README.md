# Sortie analyse Radare2 (Looping)

Ce répertoire est destiné aux fichiers générés par les scripts d’analyse de **Looping.exe** avec radare2.

## Génération

Depuis la racine du dépôt, avec Looping.exe dans `~/Téléchargements` :

```bash
# Comportement (souris, drag, pan, hit-test)
./scripts/radare2_looping_behavior.sh ~/Téléchargements/Looping.exe docs/analysis_output
```

Ou manuellement :

```bash
# Toutes les chaînes (sans head pour avoir aussi .rdata avec CDrawArc, accHitTest, etc.)
r2 -q -e bin.relocs.apply=true -e bin.cache=true -c "izz" ~/Téléchargements/Looping.exe 2>/dev/null > docs/analysis_output/looping_izz.txt

# Puis filtrer les chaînes "comportement"
grep -iE "souris|mouse|clic|click|drag|HitTest|accHitTest|accSelection|DragMinDist|CScrollView|CDrawArc|CDrawRelation|CDrawEntite|Selection|Lien|Association|Clic droit" docs/analysis_output/looping_izz.txt > docs/analysis_output/looping_behavior_strings.txt
```

**Note** : Si vous avez utilisé `head -8000` sur `izz`, les chaînes en `.rdata` (CDrawArc, etc.) peuvent être au-delà des 8000 premières lignes. Pour une analyse complète, ne pas limiter le nombre de lignes.

## Référence

Voir `docs/COMPORTEMENT_LOOPING_ANALYSE_RADARE2.md` pour l’exploitation des résultats et les critères BarrelMCD.
