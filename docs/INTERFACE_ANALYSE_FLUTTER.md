# Analyse de l'interface BarrelMCD (Python) pour le port Flutter

## 1. Vue d'ensemble

L'application Python est composée de :
- **Fenêtre principale** (`MainWindow`) : titre "BarrelMCD - Modélisation Conceptuelle de Données", thème sombre, barre d'outils, zone canvas scrollable, docks (Propriétés, Explorateur) masqués par défaut.
- **Canvas interactif** (`InteractiveCanvas`) : zone de dessin MCD avec entités (rectangles), associations (losanges), liens avec cardinalités, grille, zoom, modes (sélection, entité, association, lien).
- **Dialogs** : Import Markdown (onglets Fichier, Éditeur, Prévisualisation, Validation, Héritage, Analyse), Aide, Console, À propos, Export/Import MCD.

## 2. Structure de l'écran principal

```
┌─────────────────────────────────────────────────────────────────────────┐
│ [Logo] Barrel MCD                                                        │
├─────────────────────────────────────────────────────────────────────────┤
│ [Logo] [Fichier▼] | [Entité] [Association] [Lien] [Auto-Liens] |       │
│ [Zoom+] [Zoom-] [Ajuster] [Grille] | [Suppr] [Annuler] [Répéter] |      │
│ [Importer] [Markdown] [SQL] [Image] [PDF] | [Aide] [Console] |            │
│ [Exporter MCD] [Importer MCD] | [Auto-connexion] [Optimiser]              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                     CANVAS (zone scrollable)                      │   │
│  │   Fond #1e1e1e, grille 20px, entités rectangulaires,            │   │
│  │   associations losanges, flèches avec cardinalités               │   │
│  │   Logo "BarrelMCD" en coin                                       │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

## 3. Palette de couleurs (DarkTheme)

| Usage | Couleur hex |
|-------|-------------|
| Background | #0A0A0A |
| Surface / Toolbar | #1A1A1A, #2d2d30 |
| Texte primaire | #FFFFFF |
| Texte secondaire | #B8B8B8 |
| Accent / Primary | #00D4FF (cyan) |
| Secondary | #FF6B35 (orange) |
| Entité fond | #1E2A3A, bordure #2E3A4A |
| Association fond | #4A1E3A, bordure #5A2E4A |
| Succès | #00E676, Erreur | #FF1744 |
| Boutons | #3e3e42, hover #4e4e52 |

## 4. Barre d'outils – actions et raccourcis

| Bouton | Raccourci | Action |
|--------|-----------|--------|
| Fichier | - | Menu : Nouveau (Ctrl+N), Ouvrir (Ctrl+O), Enregistrer (Ctrl+S), Enregistrer sous, Exporter (.bar, .loo, .xml, .json, .sql), Quitter (Ctrl+Q) |
| Entité | E | Mode création d'entité (clic sur le canvas) |
| Association | A | Mode création d'association |
| Lien | L | Mode création de lien entre deux éléments |
| Auto-Liens | Ctrl+L | Détection automatique des connexions |
| Zoom + | Z | Zoom avant |
| Zoom - | X | Zoom arrière |
| Ajuster | F | Ajuster à la vue |
| Grille | G | Afficher/masquer grille |
| Supprimer | Delete | Supprimer la sélection |
| Annuler | Ctrl+Z | Undo |
| Répéter | Ctrl+Y | Redo |
| Importer | Ctrl+I | Import JSON/CSV/Excel |
| Markdown | Ctrl+M | Dialogue d'import Markdown |
| SQL | Ctrl+E | Export SQL |
| Image | Ctrl+P | Export PNG |
| PDF | Ctrl+D | Export PDF |
| Aide | F1 | Dialogue d'aide |
| Console | F12 | Dialogue log/console |
| Exporter MCD | Ctrl+Shift+E | Export MCD JSON |
| Importer MCD | Ctrl+Shift+I | Import MCD JSON |
| Auto-connexion | - | Toggle (checkable) |
| Optimiser | - | Optimiser les connexions |

## 5. Menus (en plus de la barre d'outils)

- **Fichier** : idem toolbar + Exporter (sous-menu).
- **Édition** : Annuler, Répéter, Nouvelle Entité.
- **Affichage** : Grand écran (F11), Écran moyen (F10), Petit écran (F9), Plein écran (F12), Panneau Propriétés (Ctrl+P), Panneau Explorateur (Ctrl+E), Zoom Avant/Arrière, Ajuster à la vue, Grille.
- **Aide** : Aide (F1), À propos.

## 6. Canvas – comportement

- **Modes** : `select` | `add_entity` | `add_association` | `create_link`
- **Sélection** : clic = sélection, Ctrl+clic = multi-sélection, glisser = déplacer.
- **Création entité** : mode E → clic → dialogue "Nom de l'entité" → entité créée avec position libre.
- **Création association** : mode A → clic → dialogue "Nom de l'association" → puis cliquer sur les entités pour lier (avec cardinalité).
- **Liens** : flèches (PerformanceArrow) entre association et entité, cardinalités éditables (double-clic ou menu).
- **Grille** : 20px, snap optionnel.
- **Zoom** : molette + Ctrl, facteur 1.15, min 0.1, max 5.0.
- **Raccourcis canvas** : S (sélection), E, A, L, Z, X, F, G, Delete, Ctrl+Z, Ctrl+Y, Échap (annuler mode).

## 7. Données MCD (format API / JSON)

Structure renvoyée par `get_mcd_data()` / export :

```json
{
  "entities": [
    {
      "name": "string",
      "position": { "x": 0, "y": 0 },
      "attributes": [
        { "name": "id", "type": "INTEGER", "is_primary_key": true, "nullable": true, "default_value": null }
      ],
      "is_weak": false,
      "parent_entity": "NomParent ou null"
    }
  ],
  "associations": [
    {
      "name": "string",
      "position": { "x": 0, "y": 0 },
      "attributes": [],
      "entities": ["Entité1", "Entité2"],
      "cardinalities": { "Entité1": "1,1", "Entité2": "0,n" }
    }
  ],
  "inheritance_links": [ { "parent": "Parent", "child": "Child" } ],
  "association_links": [
    { "association": "NomAssoc", "entity": "NomEntité", "cardinality": "1,N" }
  ]
}
```

## 8. Dialogue Import Markdown

- **Onglets** : Fichier (sélection + prévisualisation), Éditeur (syntaxe Markdown MCD), Prévisualisation (tableaux Entités / Associations), Validation (erreurs + stats), Héritage, Analyse (qualité).
- **Boutons** : Générer Template, Importer le MCD, Annuler.
- **Score de précision** affiché en en-tête.
- **Syntaxe** : `## Entité`, `- attribut (type) PK : desc`, `### Entité1 <-> Entité2 : Association`, cardinalités `Entité1 : 1,1` etc.

## 9. Endpoints API Python à exposer (pour Flutter)

| Méthode | Route | Description |
|---------|--------|-------------|
| POST | /mcd/parse-markdown | Body: `{ "content": "..." }` → structure MCD parsée |
| POST | /mcd/validate | Body: structure MCD → erreurs de validation |
| GET/POST | /mcd/to-mld | Body: MCD → MLD (logique) |
| GET/POST | /mcd/to-sql | Body: MCD ou MLD → script SQL |
| POST | /mcd/analyze-data | Body: données JSON/CSV (format décrit) → MCD analysé |
| GET | /health | Santé du serveur |

L'UI Flutter enverra le modèle (entités/associations/liens) au format ci-dessus ; le backend renverra MCD/MLD/SQL et les erreurs de validation.

## 10. Fichiers à créer

- **Backend** : `api/main.py` (FastAPI), `api/routers/mcd.py`, services réutilisant `views.markdown_mcd_parser`, `models/` (entity, association, model_converter, sql_generator, etc.).
- **Flutter** : `barrelmcd_flutter/` avec écran principal (toolbar + canvas), widgets (EntityBox, AssociationDiamond, LinkArrow), dialogue Import Markdown, appels HTTP vers l’API Python.
