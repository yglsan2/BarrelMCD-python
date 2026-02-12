# Comparaison logiciels / Barrel – dessin automatique MLD et MPD

Ce document restitue l’analyse du binaire **référence externe** avec **radare2** en ligne de commande (chaînes liées au MLD/MPD graphique), puis la comparaison avec le code Barrel (Flutter) pour le dessin automatique MLD/MPD.

---

## 1. Commandes Radare2 utilisées

```bash
cd ~/Téléchargements   # ou /home/benjisan/Téléchargements
r2 -q -c "e bin.relocs.apply=true; iz" référence externe | grep -iE "MLD|MPD|schema|layout|table|foreign|graphique|position"
r2 -q -c "e bin.relocs.apply=true; iz" référence externe | grep -E "ArcFormatLienMLD|DiezeDansMLD|Largeur zone|Hauteur zone|Couleur table MLD"
```

**Recherche « photo / calque / position table »** :  
`grep -iE "photo|calque|calquer|position.*table|table.*position"` ne remonte que des **faux positifs** (chaînes « OiCCPPhotoshop ICC profile » dans `.rsrc`, à cause de « position » dans « composition »). Il n’y a **pas de chaîne explicite** « photo du MCD » ou « calquer » dans référence externe ; l’idée de réutiliser les positions du MCD pour le MLD est déduite de la doc / du comportement. En filtrant les Photoshop : chaînes utiles en `.rdata` = « Position contrainte cl… », « POSITION », « table de correspondance », « La table », etc. ; en `.rsrc` = « Position : », « Ajuster à la fenêtre », **ID_MLD**, **ID_MLD_STANDARD**, **ID_MLD_CROWSFOOT**, **ID_MCD_ZOOM**.

*(Éviter `aaa` sur ce binaire : analyse trop longue.)*

---

## 2. Chaînes de référence (MLD / MPD graphique) (MLD / MPD graphique)

| Chaîne (r2) | Rôle probable | Équivalent Barrel |
|-------------|--------------|-------------------|
| **Largeur zone graphique** | Largeur de la zone de dessin MLD | `layout.width` → `SizedBox(width: w)` dans `SchemaDiagramView` |
| **Hauteur zone graphique** | Hauteur de la zone de dessin MLD | `layout.height` → `SizedBox(height: h)` |
| **Couleur table MLD** | Couleur de fond des cartes tables | `AppTheme.entityBg` dans `_TableCard` |
| **ArcFormatLienMLD** | Format des liens (arcs FK) dans le MLD | `_SchemaLinesPainter` : path cubic + flèche |
| **AfficherTypeDansMLD** | Afficher les types dans le MLD | `SchemaDiagramView.showTypes` → colonnes avec `colType` |
| **DiezeDansMLDGraphique** | Symbole # pour les clés primaires en MLD graphique | Barrel : icône clé (`Icons.key`) à la place du # |
| **Format du lien MLD** / **Format lien MLD** | Options d’affichage des liens | Lignes FK dessinées entre `fromRect` et `toRect` |
| **table de correspondance** (dans le MLD) | Table de liaison (n:n) | `layoutSchema` / `_parseSchemaData` : tables = Map ou List, même structure |
| **FOREIGN KEY** / **CREATE TABLE** | Génération SQL / structure | Côté API Python ; Flutter affiche les tables + FK du MLD/MPD |
| **COutputEditMLD** / **COutputWndMLD** (RTTI) | Fenêtre / édition MLD | Panneau MLD/SQL Flutter (`MldSqlPanel`, onglet MLD/MPD) |

---

## 3. Dessin automatique « photo du MCD »

- **Référence** : le MLD graphique réutilise les **positions** des entités/associations du MCD (même disposition à l’écran).
- **Barrel** :
  - `layoutSchemaFromMcd(data, mcdEntities, mcdAssociations)` : si `mcdEntities` / `mcdAssociations` sont fournis, on place chaque table du MLD au **centre** correspondant à l’entité ou l’association du MCD.
  - `_mcdPositionForTable(tableName, entities, associations)` :
    - table = entité : recherche par nom (insensible à la casse).
    - table = association : nom normalisé (sans caractères spéciaux, espaces → `_`).
    - table = table de liaison (ex. `entite1_entite2`) : association liant les deux entités → position de l’association.
  - Les dimensions de la « zone graphique » sont déduites des rectangles des tables (`extentW`, `extentH`), avec clamp pour éviter des valeurs invalides.

**Alignement** : même logique pour le placement pour le placement des tables à partir du MCD.

---

## 4. Différences et correctifs Barrel

### 4.1 Données d’entrée (MLD/MPD)

- **Référence** : attend sans doute une structure fixe (tables = map, colonnes = liste de champs).
- **Barrel** : l’API peut renvoyer `tables` en **Map** ou **List**.  
  **Correctif** : `_parseSchemaData()` normalise les deux formats et `_normalizeColumn()` accepte colonne = Map ou string, pour éviter les exceptions de cast.

### 4.2 Dimensions et Rect

- **Référence** : « Largeur / Hauteur zone graphique » → dimensions explicites.
- **Barrel** : `Rect.fromCenter` et `layout.width`/`height` peuvent recevoir 0 ou négatif si les données sont incohérentes.  
  **Correctif** : `.clamp(40.0, 2000.0)` sur les hauteurs de cartes, `.clamp(400.0, 10000.0)` sur `extentW`/`extentH`, et fallback pour `maxW`/`maxH` dans `LayoutBuilder` (800×600 si contraintes invalides).

### 4.3 MPD en mode dessin auto

- **Référence** : le MPD graphique peut aussi reprendre la disposition du MCD.
- **Barrel** : auparavant, l’onglet MPD n’utilisait pas les positions MCD.  
  **Correctif** : `_MpdView` reçoit `mcdEntities` et `mcdAssociations` et les passe à `SchemaDiagramView`, comme pour le MLD. Le MPD utilise donc le même « dessin automatique » que le MLD.

### 4.4 Robustesse

- **Barrel** : `SchemaDiagramView.build` est entouré d’un **try/catch** : en cas d’exception (données inattendues, Rect invalide, etc.), un message d’erreur s’affiche à la place du schéma au lieu de faire planter l’app.

---

## 5. Fichiers Barrel concernés

| Fichier | Rôle |
|---------|------|
| `lib/widgets/schema_diagram.dart` | `layoutSchema`, `layoutSchemaFromMcd`, `_parseSchemaData`, `_mcdPositionForTable`, `SchemaDiagramView`, `_TableCard`, `_SchemaLinesPainter` |
| `lib/screens/mld_sql_panel.dart` | `_MldView` (MLD + positions MCD), `_MpdView` (MPD + positions MCD depuis la même correction) |

---

## 6. Références

- **Binaire** : `~/Téléchargements/référence externe` (PE32+ x86-64).
- **Radare2** : `r2 -q -c "e bin.relocs.apply=true; iz" référence externe` pour les chaînes sans analyse complète.
- **Barrel** : `docs/LOOPING_RADARE2_EQUIVALENTS_CODE.md` (liens MCD), `docs/FONCTIONNALITES_MCD_LOOPING.md`.

*Document généré à partir de l’analyse radare2 de référence externe et du code Barrel (février 2026).*
