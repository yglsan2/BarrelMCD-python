# Analyse JMerise (logiciel libre MCD) – Liens, associations, relations

Ce document décrit l’analyse de **JMerise** (JMerise062.zip, application Java) pour en tirer des enseignements sur la gestion des **liens**, **associations** (relations) et **cardinalités**, afin d’aligner Barrel MCD sur les bonnes pratiques.

---

## 1. Méthode d’analyse

- **Extraction** : JMerise062.zip décompressé (JAR + libs + exemple .mcd).
- **Outils** : `jar tf`, `javap -p` sur les `.class` pour la structure et les méthodes ; `strings` sur le fichier .mcd pour le format de sauvegarde.
- **Classes ciblées** : `Merise` (modèle), `IhmMCD` (affichage MCD), `formes` / `formes2` (formes graphiques).

---

## 2. Modèle métier JMerise

### 2.1 Lien (Merise.Lien)

```text
- entite: Merise.Entite
- relation: Merise.Relation
- cardinalite: String (défaut "0,n")
```

Un **lien** relie une **entité** et une **relation** (association) et porte une **cardinalité**. Pas de notion de « bras » multiple par paire dans le modèle : une seule cardinalité par couple (entité, relation).

### 2.2 Relation (Merise.Relation)

- Hérite de **Merise.EntiteRelation** (nom, commentaire, liste d’attributs, clés SQL, etc.).
- Relation = association MCD (losange/ovale dans l’IHM).

### 2.3 EntiteRelation (base commune)

- **p0** : Point (x, y) – coin supérieur gauche.
- **width**, **height** : dimensions.
- **centre** : point central (calculé).
- Méthodes : getX(), getY(), getCentreX(), getCentreY(), setX(), setY(), redimentionner(), isSelected(int, int), paint() (abstrait).

Les **formes** (entité, relation) ont donc une position (x, y) et une taille (width, height), comme dans Barrel MCD.

---

## 3. Interface MCD – Liens (IhmMCD.IhmLien)

### 3.1 Champs principaux

| Champ            | Type           | Rôle |
|------------------|----------------|------|
| entite           | IhmEntite      | Entité graphique |
| relation         | IhmRelation    | Relation graphique |
| cardinalite      | String         | Texte cardinalité (ex. "1,n") |
| cardCentre       | boolean        | Cardinalité au centre du segment ? |
| xCardinal, yCardinal | double     | Position du label de cardinalité |
| xCassure, yCassure | double      | **Point de cassure** (ligne brisée / elbow) |
| cassure          | boolean        | Utiliser une cassure (ligne en angle) |
| nom              | String         | Nom du lien (optionnel) |
| selected         | boolean        | Lien sélectionné |

### 3.2 Dessin et géométrie

- **paint(Graphics)** : trace le lien (trait + cardinalité).
- **rectangleCardinalite(Graphics)** : dessine le cadre du texte de cardinalité.
- **calculeA(), calculeB()** : coefficients de la droite (équation de la ligne entité–relation).
- **calculeACassureRelation**, **calculeBCassureEntite**, etc. : variantes avec **cassure** (point intermédiaire) pour tracer un segment brisé.
- **calculerXYCardinalCentre()**, **carculerXYCardinal()** : position du label de cardinalité le long du segment.

En résumé : JMerise gère un **point de cassure** (xCassure, yCassure) pour dessiner des **lignes en angle** (équivalent des styles « elbow » dans Barrel MCD).

### 3.3 Hit-test

- **isSelected(int, int)** : test de sélection du lien.
- **isDansCadreCardinalite**, **isDansCadreNomLien**, **isSelectedDroite**, **isDansLeCarre**, **isDansLeCarreEntite**, **isDansLeCarreRelation** : tests de proximité sur le segment, la cardinalité et les formes.

---

## 4. Format de sauvegarde (.mcd)

Le fichier `exemple_MCD_GestionCommandeClient.mcd` est binaire. Les chaînes extraites montrent notamment :

- **Configuration MCD** : `IhmMCD2.ConfigurationMCD2`, options d’affichage (zoom, types, cardinalités en majuscule, etc.).
- **Classes de lien** : `clLien2`, `clLienActiver2`, `clLienNom2`, `clLienNomCardinalite2`, `clLienFondCardinalite2`, `clLienText2`, etc. (couleurs et styles).
- **Entité / relation** : `clEntiteCadre2`, `clRelation2`, `traitEntiteRelation2`, `lienEntiteRelation2`, etc.
- **Propriétés** : `xPropriete`, `yPropriete`, `cardinalite2points2`, `lienContraintes2`, etc.

Cohérent avec un modèle où chaque lien stocke des propriétés visuelles (dont position de cardinalité et éventuellement cassure).

---

## 5. Comparaison avec Barrel MCD et Looping

| Aspect              | JMerise                    | Looping (doc existante)     | Barrel MCD actuel |
|---------------------|----------------------------|-----------------------------|-------------------|
| Lien                | Entité + Relation + cardinalité | Arc (CDrawArc) = trait + flèche | association_links : assoc, entity, card_entity, card_assoc, arm_index |
| Position cardinalité| xCardinal, yCardinal       | Texte de part et d’autre (marge + perp) | cardinalityAlongOffset, cardinalityPerpOffset |
| Ligne brisée        | cassure (xCassure, yCassure) | Polyline si points de contrôle | line_style: elbow_h, elbow_v (point intermédiaire) |
| Accroche entité     | Centre / bord (via IhmEntiteRelation) | Point d’accroche sur le bord | entityLinkEndpoint (entity_side, bras, ou bord face à l’assoc) |
| Accroche relation   | (implicite dans IhmRelation) | Pointe du bras (arm)        | associationArmPosition(assoc, link) avec arm_index |
| Flèche              | (non détaillée dans les classes vues) | À l’extrémité du segment    | snapTipToEntityBoundary / snapTipToAssociationBoundary |

---

## 6. Recommandations pour Barrel MCD

1. **Segment (from, to)**  
   Conserver une **seule source de vérité** pour le segment (comme dans `link_geometry.getLinkSegment` et la spec Looping) :  
   - from = accroche association (pointe du bras, `arm_index`),  
   - to = accroche entité (bord ou bras),  
   - avec prise en charge de la pointe personnalisée (arrow_tip) et du **snap** pour que la flèche ne rentre pas dans les formes.

2. **Plusieurs liens par paire (association, entité)**  
   JMerise modélise un seul lien par (entité, relation) ; Barrel MCD et Looping autorisent **plusieurs bras** (plusieurs liens) entre la même association et la même entité. Conserver **arm_index** et **associationArmPosition(assoc, link)** pour que chaque lien parte du bon bras.

3. **Cassure / ligne en angle**  
   JMerise utilise un point de cassure (xCassure, yCassure). Barrel MCD a déjà **elbow_h** / **elbow_v** avec un point intermédiaire dérivé de (effFrom, effTo). On peut envisager plus tard un **point de cassure stocké** (comme arrow_tip) pour un angle libre, en s’inspirant de JMerise.

4. **Cardinalités**  
   Positionner les labels de part et d’autre du segment avec une marge le long du segment et un décalage perpendiculaire (déjà en place dans LinkArrow), éventuellement avec option « cardinalité au centre » (équivalent de **cardCentre** dans JMerise) si besoin.

5. **Rétroconception / export**  
   JMerise inclut BDDRetro, SQLGenerateur, etc. Pour Barrel MCD, s’appuyer sur l’API et les docs existantes (MLD, MPD, SQL) ; l’analyse JMerise ne change pas la logique de rétroconception déjà en place.

---

## 7. Références

- **JMerise** : JMerise062.zip (Téléchargements), JMerise.jar, packages Merise, IhmMCD, formes, formes2.
- **Barrel MCD** : `barrelmcd_flutter/lib/utils/link_geometry.dart`, `lib/widgets/link_arrow.dart`, `lib/widgets/mcd_canvas.dart` (_LinksPainter).
- **Looping** : `docs/LOOPING_RADARE2_EQUIVALENTS_CODE.md`, `docs/COMPORTEMENT_LOOPING_ANALYSE_RADARE2.md`.

*Document généré à partir de l’analyse javap des classes JMerise (février 2026).*
