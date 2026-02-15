# Comportement Looping – Analyse Radare2 et critères BarrelMCD

Ce document restitue l’**analyse radare2** du binaire **Looping.exe** (dans `~/Téléchargements`) ciblée sur le **comportement** (souris, drag, pan, sélection, hit-test), puis fixe les **critères** pour que BarrelMCD se comporte au moins aussi bien que Looping.

---

## 1. Commandes Radare2 pour l’analyse comportement

À exécuter depuis une machine où r2 et Looping.exe sont disponibles (ex. `~/Téléchargements/Looping.exe` ou `Looping_32bits.exe`) :

```bash
# Toutes les chaînes, puis filtre comportement
r2 -q -e bin.relocs.apply=true -e bin.cache=true -c "izz" "/chemin/vers/Looping.exe" 2>/dev/null | grep -iE "souris|mouse|clic|click|drag|glisser|deplacer|move|pan|scroll|selection|select|hit|WM_|LBUTTON|RBUTTON|OnMouse|MouseDown|MouseMove|MouseUp|Capture|Deplacer|Déplacer|entité|association|arc|lien|HitTest|accHitTest|accSelection|DragMinDist|DragDelay|DoubleClick|RetourOutilSelection|EpaississementSelection|Clic droit" > looping_behavior_strings.txt
```

Script projet (recherche SQL) à étendre pour le comportement :  
`scripts/radare2_looping_sql_search.sh` → ajouter une cible "comportement" ou créer `scripts/radare2_looping_behavior.sh`.

---

## 2. Chaînes pertinentes extraites (Looping.exe)

Résultats typiques d’une analyse r2 `izz` + grep sur le comportement :

| Chaîne / symbole | Rôle probable | Équivalent BarrelMCD |
|------------------|---------------|------------------------|
| **accHitTest** | Hit-test accessibilité / UI | `_hitTestTopmostAtScene`, `_entityIndexAtScene`, `_associationIndexAtScene` |
| **accSelection** | Sélection (objet sous le curseur) | `selectedEntityIndices`, `selectedAssociationIndices`, `selectedLinkIndices` |
| **CMouseManager** / **Mouse** | Gestion souris (MFC) | Listener `onPointerDown` / `onPointerMove` / `onPointerUp` |
| **CScrollView** | Vue défilable (pan/scroll) | `InteractiveViewer` + `panEnabled` |
| **AFX_WM_GETDRAGBOUNDS** / **AFX_WM_ON_DRAGCOMPLETE** | Début/fin de drag | `_pendingDragEntityIndex` → commit quand `dist > _dragCommitSlop` |
| **AFX_WM_ON_TABGROUPMOUSEMOVE** | Déplacement souris pendant action | `onPointerMove` (commit drag ou déplacer élément) |
| **DragMinDist** / **DragDelay** | Seuil et délai avant de considérer un drag | `_dragCommitSlop` (pixels), pas de délai temporel obligatoire |
| **DragScrollDelay** / **DragScrollInset** / **DragScrollInterval** | Pan/scroll pendant drag vers le bord | Optionnel : auto-scroll si on drag vers les bords |
| **DoubleClick** | Double-clic | Tap avec `duration` / double-tap si on veut menus Looping |
| **Selection** | Sélection d’objets | Mode Sélection + sélection entité/association/lien |
| **RetourOutilSelection** | Retour à l’outil sélection après action | Mode `CanvasMode.select` par défaut après création lien |
| **EpaississementSelection** | Mise en évidence sélection | Contour / épaisseur des éléments sélectionnés |
| **Clic droit** (UTF-16) | Menu contextuel | Clic droit → menu entité/association/lien |
| **Association** / **Lien** / **CDrawArc** | Objets dessin | `state.associations`, `state.associationLinks`, `_LinksPainter` |

En Looping, le **hit-test** et la **sélection** sont centralisés (accHitTest, accSelection) ; le **drag** est soumis à un seuil (DragMinDist) et le **pan/scroll** est distinct du drag d’objet (CScrollView + messages AFX_WM_*).

---

## 3. Règles de comportement « comme Looping »

Pour que BarrelMCD se comporte au moins aussi bien que Looping, le canvas doit respecter les points suivants (déduits du binaire et de l’usage observé de Looping).

### 3.1 Hit-test unifié (un seul élément « au-dessus »)

- **Looping** : un clic désigne **un seul** objet (entité, association ou lien), pas deux à la fois. L’ordre de priorité (qui est « au-dessus ») est cohérent avec l’affichage.
- **BarrelMCD** :  
  - Utiliser **un seul** hit-test qui retourne l’élément le plus « haut » (ex. `_hitTestTopmostAtScene`).  
  - Ordre recommandé : **associations** puis **entités** (comme draw.io / Looping), pour que les petits losanges ne soient pas « mangés » par les grands rectangles.  
  - Ne jamais traiter un même clic comme entité ET association.

### 3.2 Pan désactivé dès qu’un drag d’élément est en attente

- **Looping** : si on appuie sur une entité ou une association, le premier mouvement déplace l’objet ; le fond ne défile pas tant qu’on n’a pas relâché ou annulé.
- **BarrelMCD** :  
  - `panEnabled` doit être **false** dès qu’il existe un **pending** drag (entité ou association), pas seulement quand le drag est « commit ».  
  - Condition actuelle recommandée :  
    `panEnabled = mode != createLink && !draggingElement && !pendingElementDrag && !draggingLinkHandle && !draggingLinkSegment && !rotatingArm`  
    avec `pendingElementDrag = (_pendingDragEntityIndex != null || _pendingDragAssocIndex != null)`.

### 3.3 Commit du drag au premier mouvement au-dessus du seuil

- **Looping** : un petit déplacement après le clic valide le déplacement de l’objet (pas un tap). Pas de pan tant que l’objet peut être déplacé.
- **BarrelMCD** :  
  - Conserver un **seuil en pixels** (`_dragCommitSlop`) : tant que `distance(move, down) <= _dragCommitSlop`, on reste en « pending » ; au premier `distance > _dragCommitSlop`, on **commit** le drag (entité ou association) et on déplace l’élément.  
  - Ne pas committer le pan à la place du drag : donc pan désactivé si `pendingElementDrag` (voir 3.2).

### 3.4 Liens (arcs) : segment et flèche comme Looping

- **Looping** : un arc = **CDrawArc** (trait + flèche). Point d’arrivée = point de relâchement utilisateur (ou accroche entité/association). Flèche **à l’extrémité** du segment.
- **BarrelMCD** :  
  - Une seule source de vérité pour le segment (from, to) : `_getLinkSegment` / géométrie dans `link_geometry.dart`.  
  - Si le segment calculé est trop court ou « à l’envers », utiliser un **fallback** (segment par défaut assoc ↔ entité).  
  - Éviter `dist < 1` pour le dessin (LinkArrow ne dessine rien) : garantir une longueur minimale (ex. `kMinLinkSegmentLength`) ou segment par défaut.  
  - Clip du rectangle scène pour que les liens ne débordent pas.

### 3.5 Clic droit et menus contextuels

- **Looping** : « Clic droit » (chaîne dans le binaire) ouvre des menus contextuels selon l’objet sous le curseur.
- **BarrelMCD** : conserver les menus au clic droit sur entité, association, lien (et héritage / CIF si applicable).

### 3.6 Sélection et retour à l’outil sélection

- **Looping** : « RetourOutilSelection » / outil sélection par défaut après une action (ex. création de lien).
- **BarrelMCD** : après création d’un lien (dialogue cardinalités validé), repasser en mode Sélection et désélectionner ou sélectionner le lien créé selon le choix UX.

---

## 4. Synthèse : checklist BarrelMCD vs Looping

| Critère | Looping (observé / binaire) | BarrelMCD (à vérifier) |
|--------|-----------------------------|-------------------------|
| Hit-test un seul élément | accHitTest, ordre cohérent | `_hitTestTopmostAtScene`, associations avant entités |
| Pan désactivé si pending drag | Pas de scroll tant qu’objet capturé | `panEnabled` inclut `!pendingElementDrag` |
| Commit drag au seuil pixels | DragMinDist | `_dragCommitSlop` au premier move |
| Segment lien dégénéré | Trait + flèche à l’arrivée | Fallback segment défaut + longueur min |
| Clic droit → menu | Chaîne « Clic droit » | Menus entité / association / lien |
| Logs / diagnostic | N/A (binaire) | `_kDiagnosticLog`, try/catch, logs DIAG down/up/move et LINK |

---

## 5. Références

- **Binaire** : `~/Téléchargements/Looping.exe` ou `Looping_32bits.exe`.
- **Docs existantes** : `ANALYSE_RADARE2_LOOPING.md`, `LOOPING_RADARE2_EQUIVALENTS_CODE.md`, `ANALYSE_LOGIQUE_METIER_LOOPING.md`.
- **Code Flutter** : `barrelmcd_flutter/lib/widgets/mcd_canvas.dart` (Listener, `_hitTestTopmostAtScene`, `panEnabled`, `_dragCommitSlop`, `_LinksPainter`), `link_geometry.dart`, `link_arrow.dart`.
- **Script r2** : `scripts/radare2_looping_sql_search.sh` (SQL) ; à dupliquer ou étendre en `scripts/radare2_looping_behavior.sh` pour sortir `looping_behavior_strings.txt`.

*Document rédigé pour aligner le comportement BarrelMCD sur Looping à partir de l’analyse radare2 (février 2026).*
