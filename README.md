# BarrelMCD

BarrelMCD est une application web moderne et intuitive pour la modélisation de données. Elle permet de créer, visualiser et exporter différents types de modèles de données (MCD, UML, MLD, MPD, SQL) avec une interface utilisateur élégante et fonctionnelle.

## Fonctionnalités

- **Modèles multiples** : Créez et gérez différents types de modèles : MCD, UML, MLD, MPD et SQL.
- **Interface intuitive** : Une interface utilisateur moderne qui facilite la création et la modification de vos modèles de données.
- **Thèmes personnalisables** : Basculez entre le mode sombre et le mode clair selon vos préférences.
- **Exportation de code** : Générez automatiquement du code SQL à partir de vos modèles.

## Installation

1. Clonez ce dépôt :
   ```
   git clone https://github.com/votre-utilisateur/barrel-mcd.git
   ```

2. Ouvrez le fichier `index.html` dans votre navigateur web.

## Utilisation

### Interface principale

L'interface principale de BarrelMCD est divisée en plusieurs sections :

- **En-tête** : Contient le logo, le menu principal et les boutons de sélection de modèle.
- **Barre latérale** : Affiche la liste des entités et leurs attributs.
- **Espace de travail** : Zone principale où vous pouvez visualiser et modifier votre modèle.
- **Barre de statut** : Affiche des informations sur l'état actuel de l'application.

### Création d'un modèle

1. Sélectionnez le type de modèle que vous souhaitez créer (MCD, UML, MLD, MPD, SQL) en cliquant sur le bouton correspondant dans l'en-tête.
2. Utilisez la barre latérale pour ajouter des entités à votre modèle.
3. Faites glisser les entités dans l'espace de travail pour les positionner.
4. Créez des relations entre les entités en les connectant.

### Basculement entre les thèmes

Pour basculer entre le mode sombre et le mode clair, utilisez la fonction `toggleTheme()` dans la console du navigateur ou ajoutez un bouton dans l'interface.

## Structure du projet

```
barrel-mcd/
├── index.html              # Page principale de l'application
├── app_preview.html        # Aperçu de l'application
├── static/
│   ├── css/
│   │   ├── barrel_theme.css  # Styles principaux
│   │   └── logo.css           # Styles pour le logo
│   └── img/
│       ├── BARREL v4 avec-dark.svg  # Logo avec texte (mode sombre)
│       └── BARREL v4 sans-dark.svg  # Logo sans texte (mode sombre)
└── README.md               # Documentation
```

## Charte graphique

### Mode sombre

- **Fond principal** : #121212 (noir)
- **Panneau de travail** : #1a1a2e (bleu très foncé)
- **Barre d'outils** : #2d2d44 (bleu foncé)
- **Accent** : #1a5276 (bleu sombre)

### Mode clair

- **Fond principal** : #ffffff (blanc)
- **Panneau de travail** : #f0f0f0 (gris très clair)
- **Barre d'outils** : #1a5276 (bleu sombre)
- **Accent** : #f6a316 (orange)

## Contribution

Les contributions sont les bienvenues ! N'hésitez pas à ouvrir une issue ou à soumettre une pull request.

## Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails. 