# Charte Graphique BarrelMCD

## Codes des couleurs

### Mode sombre (par défaut)
```css
:root {
    /* Couleurs principales */
    --bg-primary: #121212;           /* Fond principal (noir) */
    --bg-secondary: #1a1a2e;         /* Panneau de travail (bleu très foncé) */
    --bg-tertiary: #2d2d44;          /* Barre d'outils (bleu foncé) */
    
    /* Entités */
    --entity-bg: #2a2a3a;            /* Fond des entités */
    --entity-border: #3d3d4d;        /* Bordure des entités */
    
    /* Associations */
    --association-bg: #1a2a3a;       /* Fond des associations */
    --association-border: #2d3d4d;   /* Bordure des associations */
    
    /* Texte */
    --text-primary: #ffffff;          /* Texte principal (blanc) */
    --text-secondary: #b3b3b3;        /* Texte secondaire (gris clair) */
    
    /* Grille */
    --grid-color: rgba(255, 255, 255, 0.1); /* Grille (blanc semi-transparent) */
    
    /* Boutons */
    --button-bg: #2d2d44;            /* Fond des boutons */
    --button-hover: #3d3d4d;         /* Survol des boutons */
    
    /* Accent */
    --accent-color: #1a5276;         /* Couleur d'accent (bleu sombre) */
}
```

### Mode clair
```css
.light-theme {
    --bg-primary: #ffffff;           /* Fond principal (blanc) */
    --bg-secondary: #f0f0f0;         /* Panneau de travail (gris très clair) */
    --bg-tertiary: #1a5276;          /* Barre d'outils (bleu sombre) */
    
    /* Entités */
    --entity-bg: #ffffff;            /* Fond des entités */
    --entity-border: #e0e0e0;        /* Bordure des entités */
    
    /* Associations */
    --association-bg: #f5f5f5;       /* Fond des associations */
    --association-border: #e0e0e0;   /* Bordure des associations */
    
    /* Texte */
    --text-primary: #333333;         /* Texte principal (noir) */
    --text-secondary: #666666;       /* Texte secondaire (gris) */
    
    /* Grille */
    --grid-color: rgba(0, 0, 0, 0.15); /* Grille (noir semi-transparent) */
    
    /* Boutons */
    --button-bg: #1a5276;            /* Fond des boutons */
    --button-hover: #154360;         /* Survol des boutons */
    
    /* Accent */
    --accent-color: #f6a316;         /* Couleur d'accent (orange) */
}
```

## Couleurs des modèles
```css
.model-mcd {
    --model-color: #4caf50;           /* Vert */
}

.model-uml {
    --model-color: #2196f3;           /* Bleu */
}

.model-mld {
    --model-color: #ff9800;           /* Orange */
}

.model-mpd {
    --model-color: #9c27b0;           /* Violet */
}

.model-sql {
    --model-color: #f44336;           /* Rouge */
}
```

## Couleurs des attributs
```css
.attribute-primary {
    color: #4caf50;                   /* Vert */
}

.attribute-foreign {
    color: #2196f3;                   /* Bleu */
}

.attribute-index {
    color: #ff9800;                   /* Orange */
}

.attribute-required {
    color: #f44336;                   /* Rouge */
}
```

## Couleurs des cardinalités
```css
.cardinality {
    color: #9c27b0;                   /* Violet */
}
```

## Couleurs des contraintes
```css
.constraint {
    color: #ff9800;                   /* Orange */
}
```

## Structure de l'interface

### En-tête
- Hauteur : 60px
- Fond : var(--bg-tertiary)
- Bordure inférieure : 1px solid var(--entity-border)

### Menu
- Éléments alignés à gauche
- Espacement : 20px entre les éléments
- Couleur du texte : var(--text-primary)
- Effet de survol : var(--button-hover)

### Boutons de modèle
- Alignés à droite
- Espacement : 10px entre les boutons
- Fond : var(--button-bg)
- Effet de survol : var(--button-hover)
- Bouton actif : var(--accent-color)

### Barre latérale
- Largeur : 280px
- Fond : var(--bg-secondary)
- Bordure droite : 1px solid var(--entity-border)
- Défilement vertical activé

### Espace de travail
- Fond : var(--bg-primary)
- Défilement activé
- Position relative pour le positionnement absolu des entités

### Entités
- Fond : var(--entity-bg)
- Bordure : 1px solid var(--entity-border)
- Ombre : 0 2px 4px rgba(0, 0, 0, 0.2)
- Coins arrondis : 6px
- Padding : 15px
- Marge inférieure : 15px

### Barre de statut
- Hauteur : 30px
- Fond : var(--bg-secondary)
- Bordure supérieure : 1px solid var(--entity-border)
- Couleur du texte : var(--text-secondary)
- Padding horizontal : 20px 