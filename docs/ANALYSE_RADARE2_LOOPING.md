# Analyse Looping.exe avec Radare2

Ce document restitue les résultats d’une **analyse réelle** du binaire `Looping.exe` avec radare2 (commandes `iz`, `izz`, `ie`, `iS`). Source : exécution de r2 sur la machine, pas une simple reprise des anciennes doc.

## 1. Commandes utilisées

```bash
r2 -q -c "iz" "/chemin/vers/Looping.exe"    # chaînes (data)
r2 -q -c "izz" "/chemin/vers/Looping.exe"   # toutes les chaînes
r2 -q -c "ie; iS" "/chemin/vers/Looping.exe" # entrées / sections
r2 -q -c "aaa; afl" "/chemin/vers/Looping.exe" # analyse complète + liste des fonctions
# + grep sur izz pour Arc, Relation, Lien, CDraw, trait, flèche, etc.
```

### Liste des fonctions (aaa; afl)

Après `aaa; afl`, r2 liste de nombreuses fonctions (ex. `fcn.1401258a8`, `fcn.1400f92b0`) **sans noms symboliques** : le PE est en release, pas de table des symboles exportée. Les noms sont des adresses. Pour cibler le code de dessin (Arc, Flèche, Relation, Ellipse), on peut :

- **Références aux chaînes** : en session r2, aller sur l’adresse d’une chaîne (ex. `CDrawArc` en .rdata) puis `axt` (xref to) pour voir quelles fonctions l’utilisent.
- **Filtrer les méthodes** : `afl~method` si des noms de méthodes C++ ont été détectés.
- **Relocations** : relancer avec `-e bin.relocs.apply=true` ou `-e bin.cache=true` pour une analyse plus stable si besoin.

## 2. Classes de dessin (noms C++ / MFC)

Identifiants de type / RTTI dans `.rdata` et `.data` :

| Classe | Rôle probable |
|--------|----------------|
| **CDrawObj** | Classe de base des objets dessinés |
| **CDrawRelation** | Association (relation) MCD |
| **CDrawEntite** | Entité MCD |
| **CDrawEntiteUML** | Variante UML entité |
| **CDrawArc** | Arc / lien entre entité et relation |
| **CDrawArcCif** | Arc CIF |
| **CDrawArcContrainte** | Arc de contrainte |
| **CDrawArcHeritage** | Arc d’héritage |
| **CDrawArcHeritageUML** | Arc héritage UML |
| **CDrawArcObjetLibre** | Arc objet libre |
| **CDrawArcRegle** | Arc règle de gestion |
| **CDrawTrait** | Trait (ligne) |
| **CDrawFleche** | Flèche (objet distinct du trait) |
| **CDrawEllipse** | Ellipse (forme ovale) |
| **CDrawRectangle** | Rectangle |
| **CDrawCif** | CIF |
| **CDrawContrainte** | Contrainte |
| **CDrawCrayon** | Crayon / outil |
| **CDrawHeritage** | Héritage |
| **CDrawImage** | Image |
| **CDrawProf** | Profil ? |
| **CDrawRegle** | Règle |
| **CDrawTexte** | Texte |
| **CDrawTitre** | Titre |

En résumé : **lien** = `CDrawArc`, **association** = `CDrawRelation`, **flèche** = `CDrawFleche`, **forme ovale** = `CDrawEllipse`. Le dessin des arcs peut s’appuyer à la fois sur un trait (`CDrawTrait`) et une flèche (`CDrawFleche`).

## 3. Options / propriétés d’affichage (chaînes)

- **AfficherTrait** : afficher ou non le trait.
- **AfficherFlecheSiDF** : afficher la flèche selon un critère (DF).
- **AfficherRubrique**, **AfficherType**, **AfficherTitre**, **AfficherFond** : rubriques, types, titre, fond.
- **AfficherTypeDansMLD**, **AfficherFluxEntreRegle**, **AfficherCascade**.
- **TexteArcQuelCote** : de quel côté de l’arc placer le texte (cardinalités).
- **ArcFormatIdRelatif**, **ArcFormatLienMLD** : format d’identifiant / lien MLD.
- **Epaisseur trait** (UTF-16) : épaisseur du trait.
- **Couleur trait** (UTF-16) : couleur du trait.
- **HauteurTouteRubriqueEntite**, **HauteurAutoMaximumEntite** : hauteur entité.
- **Largeur de l’angle de l’association** (UTF-16) : largeur d’angle (forme association).
- **Hauteur de l’angle de l’association** (UTF-16) : hauteur d’angle (forme association).
- **Hauteur du titre de l’association** (UTF-16) : hauteur du titre sur l’association.
- **défaut de l’association**, **défaut des rubriques de l’association**, **défaut des types de rubriques de l’association**.

Donc en Looping : **trait** et **flèche** sont pilotés par des options (AfficherTrait, AfficherFlecheSiDF), et l’**association** a des dimensions d’“angle” (largeur / hauteur) qui correspondent sans doute à une forme elliptique ou en losange.

## 4. Règles métier (messages d’erreur)

- « La cardinalité 1,1 est interdite lorsque l'association est porteuse de rubriques »
- « Une association ne peut pas avoir des cardinalités … »
- « Une association gérant une table de correspondance ne peut pas avoir de cardinalités … »
- « Les cardinalités des liens de la CIF. »
- « association porteuse de rubriques, confirmez-vous la validation de l… »
- « Seules les associations gérant une table de correspondance peuvent être porteuses de rubriques »
- « Il existe des doublons dans les rubriques. »
- « Type de la rubrique manquant »
- « Point manquant entre la table et la rubrique »
- « L'entité … nécessite une association cible », « nécessite au moins une association »
- « Une CIF n'a d'intérêt qu'avec des associations n-aires (n>2) »
- « une association reliant plus de 2 entités, et toutes les cardinalités … »
- « Une contrainte inter-associations concerne au moins deux associations »

Cohérent avec la doc existante (ANALYSE_LOGIQUE_METIER_LOOPING.md) et avec les règles déjà implémentées (1,1 + rubriques, etc.).

## 5. Conséquences pour Barrel MCD (Flutter / Python)

1. **Forme association** : Looping a une classe **CDrawEllipse** et des champs “Largeur/Hauteur de l’angle de l’association”. Pour coller au comportement : dessiner l’association en **ellipse** (ovale), avec largeur et hauteur d’angle configurables (ou dérivées d’un ratio).
2. **Liens** : Un lien = **CDrawArc** (entité–relation). Le dessin peut utiliser **CDrawTrait** (segment) et **CDrawFleche** (pointe). Donc : tracer le segment puis dessiner la flèche **à l’extrémité** (point de relâchement du tracé), pas “en dessous” ni décalée.
3. **Sens de la flèche** : Puisque la flèche est un objet (CDrawFleche) associé à l’arc, elle doit être positionnée **à l’arrivée du tracé** (point où l’utilisateur a relâché). Pas de sens inversé par défaut.
4. **Options** : S’inspirer de AfficherTrait, Epaisseur trait, Couleur trait, TexteArcQuelCote pour les options d’affichage des liens (trait, flèche, position des cardinalités).

---

*Dernière analyse r2 : février 2026. Binaire : Looping.exe (PE32+ x86-64).*
