# Analyse Radare2 (référence externe) et équivalents code (Dart/Flutter, Python)

Ce document restitue l’analyse du binaire **Looping.exe** (dans Téléchargements) avec **radare2** en ligne de commande, puis donne des **équivalents en Dart/Flutter** (et indications Python) pour la logique métier des **liens/arcs** entre entités et associations, afin d’aligner Barrel MCD sur le comportement Looping et de corriger les bugs de flèches.

---

## 1. Commandes Radare2 utilisées

```bash
# Depuis le dossier des téléchargements
cd ~/Téléchargements

# Chaînes (section data)
r2 -q -c "e bin.relocs.apply=true; iz" Looping.exe | grep -iE "CDraw|Arc|Trait|Fleche|Ellipse|Lien|cardinal"

# Adresses des classes de dessin
r2 -q -c "e bin.relocs.apply=true; iz~CDrawArc; iz~CDrawTrait; iz~CDrawFleche"
```

---

## 2. Logique métier Looping (extraite du binaire)

### 2.1 Classes de dessin (RTTI / .rdata)

| Classe Looping    | Rôle                    | Équivalent Barrel MCD (Dart)     |
|-------------------|-------------------------|----------------------------------|
| **CDrawArc**      | Arc = lien entité–association | Un élément de `association_links` |
| **CDrawTrait**    | Segment / ligne de l’arc | `canvas.drawLine()` / `Path` + `drawPath()` |
| **CDrawFleche**   | Flèche (pointe) à l’extrémité | `LinkArrow._drawChevronAt()` |
| **CDrawEllipse**  | Forme association (ovale) | `AssociationOval` (cercle/ellipse) |
| **CDrawRelation** | Association MCD         | Objet dans `state.associations`  |
| **CDrawEntite**   | Entité MCD              | Objet dans `state.entities`      |

En Looping : **un arc (lien)** est composé d’un **trait** (CDrawTrait) et éventuellement d’une **flèche** (CDrawFleche) à l’arrivée. La flèche est positionnée **exactement au point d’arrivée du tracé** (point de relâchement utilisateur), pas décalée.

### 2.2 Options d’affichage (strings)

| String Looping       | Signification              | Équivalent Dart/Flutter                    |
|----------------------|----------------------------|--------------------------------------------|
| `AfficherTrait`      | Afficher le trait de l’arc | Toujours : `canvas.drawLine(start, to, paint)` |
| `AfficherFlecheSiDF` | Afficher flèche selon critère | Mode précision : chevron à l’arrivée (`_drawChevronAt(canvas, to, ...)`) |
| `TexteArcQuelCote`   | Côté du texte (cardinalités) | `cardinalityAlongOffset` + `cardinalityPerpOffset` (de part et d’autre du segment) |
| `HauteurEllipse` / `LargeurEllipse` | Dimensions association | `AssociationOval.minDiameter`, `width` / `height` de l’association |
| `Epaisseur trait`    | Épaisseur du trait         | `strokeWidth` (ex. 2.5) dans `link_arrow.dart` |
| `Couleur trait`      | Couleur du trait           | `AppTheme.primary` |

### 2.3 Règles de dessin (déduites)

1. **Un lien = un arc** : une seule entrée par paire (association, entité) avec deux cardinalités.
2. **Trait** : segment droit (ou polyline si points de contrôle) du point d’accroche association vers le point d’accroche entité (ou l’inverse selon le sens de création).
3. **Flèche** : dessinée **à l’extrémité** du segment (point `to`), pas en dessous ni décalée ; direction = vecteur (from → to).
4. **Cardinalités** : texte de part et d’autre du segment (marge le long + offset perpendiculaire), comme `TexteArcQuelCote`.

---

## 3. Équivalents code Dart/Flutter

### 3.1 Segment d’un lien (from, to) – comme Looping “arc”

**Looping** : l’arc a un point de départ et un point d’arrivée (accroche sur relation, accroche sur entité ; ou point de relâchement si l’utilisateur a déplacé la pointe).

**Barrel MCD (équivalent)** – une seule source de vérité pour le segment (dessin + hit-test) :

```dart
// Équivalent logique Looping : (from, to) = segment de l’arc.
// from = côté association (ou entité si arrowAtAssociation), to = pointe de flèche ou accroche.

({Offset from, Offset to}) getLinkSegment(
  Map<String, dynamic> assoc,
  Map<String, dynamic> entity,
  Map<String, dynamic> link,
) {
  final from = associationArmPosition(assoc, link);  // pointe du bras
  final to = entityLinkEndpoint(entity, from, link: link);
  return (from: from, to: to);
}
```

Avec **pointe de flèche personnalisée** (point de relâchement) :

```dart
// Si arrow_tip stocké : to = arrowTip (exactement où l’utilisateur a relâché).
final tipX = (link['arrow_tip_x'] as num?)?.toDouble();
final tipY = (link['arrow_tip_y'] as num?)?.toDouble();
if (tipX != null && tipY != null) {
  final arrowTip = Offset(tipX, tipY);
  if (arrowAtAssociation)
    return (from: entityPt, to: arrowTip);   // entité → pointe (côté assoc)
  else
    return (from: _associationSimpleAttachment(assoc, arrowTip), to: arrowTip);
}
```

### 3.2 Dessin du trait + flèche (style Looping)

**Looping** : dessiner le trait (CDrawTrait) puis la flèche (CDrawFleche) à l’arrivée.

**Barrel MCD** – `link_arrow.dart` :

```dart
// 1) Trait : du start (marge depuis from) jusqu’à to (point d’arrivée)
canvas.drawLine(start, to, paint);

// 2) Flèche exactement sur le point d’accroche (to) — comme Looping
_drawChevronAt(canvas, to, ux, uy, paint.color, selected ? 10.0 : 8.0);

// 3) Pastille au départ (association)
canvas.drawCircle(start, dotRadius, dotPaint);
```

Vecteur direction pour le chevron : `(ux, uy) = (dx/dist, dy/dist)` avec `(dx, dy) = to - from`.

### 3.3 Cardinalités de part et d’autre (TexteArcQuelCote)

**Looping** : texte de chaque côté de l’arc avec marge et décalage perpendiculaire.

**Barrel MCD** :

```dart
final normX = uy;
final normY = -ux;
final assocBoxCenter = Offset(
  from.dx + cardinalityAlongOffset * ux + cardinalityPerpOffset * normX,
  from.dy + cardinalityAlongOffset * uy + cardinalityPerpOffset * normY,
);
final entityBoxCenter = Offset(
  to.dx - cardinalityAlongOffset * ux - cardinalityPerpOffset * normX,
  to.dy - cardinalityAlongOffset * uy - cardinalityPerpOffset * normY,
);
_drawCardinalityBox(canvas, assocBoxCenter, cardinalityAssoc, selected);
_drawCardinalityBox(canvas, entityBoxCenter, cardinalityEntity, selected);
```

---

## 4. Équivalent Python (côté API / logique métier)

Pour le **modèle** (entités, associations, liens) et les **règles Merise** inspirées de Looping, le code Python Barrel MCD est déjà aligné (voir `api/services/merise_rules.py`, `models/association.py`, `models/entity.py`). Pour le **dessin**, c’est le Flutter qui fait le rendu ; l’API expose seulement les structures JSON (entités, associations, `association_links` avec `card_entity`, `card_assoc`, optionnellement `arrow_tip_x`, `arrow_tip_y`, `entity_side`, `arm_index`).

Exemple de structure d’un lien (équivalent Looping “arc”) :

```python
# Python (modèle / export)
{
    "association": "NomAssociation",
    "entity": "NomEntite",
    "card_entity": "1,n",
    "card_assoc": "0,1",
    "arrow_at_association": True,
    "arrow_tip_x": 450.0,
    "arrow_tip_y": 320.0,
    "entity_side": "right",
    "arm_index": 0,
}
```

---

## 5. Correctifs recommandés (bugs flèches Barrel MCD)

Pour éviter qu’**une ou plusieurs flèches “bouffent” le dessin** (décalage, débordement) :

1. **Clip de la couche des liens**  
   Dessiner uniquement dans le rectangle scène : dans `_LinksPainter.paint()`, envelopper le dessin dans  
   `canvas.save(); canvas.clipRect(Rect.fromLTWH(0, 0, size.width, size.height)); ... canvas.restore();`  
   Ainsi, aucun segment ne peut déborder de la scène.

2. **Cohérence des coordonnées**  
   S’assurer que `arrow_tip_x` / `arrow_tip_y` sont **toujours en coordonnées scène** (conversion viewport → scène au relâchement du drag, comme avec `_viewportToScene` sur le Listener extérieur).

3. **Même géométrie partout**  
   Utiliser la même largeur/hauteur d’association (ex. `(a['width'] as num?)?.toDouble() ?? 96.0`) et la même formule de centre/accroche dans le canvas (hit-test, `_getLinkSegment`) et dans `_LinksPainter`, pour éviter décalage entre clic et dessin.

4. **Segment dégénéré**  
   Si `dist < 1` (from ≈ to), ne pas dessiner le lien (déjà géré dans `paintWithStyle`).

---

## 6. Références

- **Binaire** : `~/Téléchargements/Looping.exe` (PE32+ x86-64).
- **Analyse r2** : `docs/ANALYSE_RADARE2_LOOPING.md`, `barrelmcd_flutter/doc/INSPIRATION_LOOPING_LIENS.md`.
- **Code Flutter** : `barrelmcd_flutter/lib/widgets/link_arrow.dart`, `mcd_canvas.dart` (`_LinksPainter`, `_getLinkSegment`), `lib/utils/link_geometry.dart`.

*Document généré à partir de l’analyse radare2 de Looping.exe et du code Barrel MCD (février 2026).*
