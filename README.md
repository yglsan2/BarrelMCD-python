# Barrel MCD

Barrel MCD est une application de création de diagrammes de conception de données (MCD) optimisée pour les appareils mobiles et tablettes, créée par Yglsan.

## Fonctionnalités

- Interface utilisateur responsive adaptée aux appareils mobiles
- Création et édition de diagrammes MCD
- Support du zoom et du panning
- Grille magnétique
- Sauvegarde automatique
- Export en différents formats

## Installation

1. Clonez le dépôt :
```bash
git clone https://github.com/yglsan/barrel-mcd.git
cd barrel-mcd
```

2. Créez un environnement virtuel :
```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows
```

3. Installez les dépendances :
```bash
pip install -r requirements.txt
```

## Utilisation

1. Lancez l'application :
```bash
python main.py
```

2. Créez un nouveau diagramme en cliquant sur le bouton "+" dans la barre d'outils.

3. Ajoutez des entités en les faisant glisser depuis la palette.

4. Créez des associations en cliquant sur les points de connexion.

5. Sauvegardez votre travail en cliquant sur le bouton "💾".

## Interface utilisateur

### Barre d'outils
- Menu (☰) : Accès aux options principales
- Nouveau (📄) : Crée un nouveau diagramme
- Ouvrir (📂) : Ouvre un diagramme existant
- Enregistrer (💾) : Sauvegarde le diagramme
- Zoom (🔍) : Ajuste le niveau de zoom
- Grille (📏) : Active/désactive la grille
- Aide (❓) : Affiche l'aide

### Barre d'état
- Mode actuel
- Niveau de zoom
- État de la grille
- Statut de sauvegarde

### Canvas
- Zoom avec le pinch-to-zoom
- Panning avec le doigt
- Grille magnétique
- Points de connexion intelligents

## Contribution

Les contributions sont les bienvenues ! N'hésitez pas à :

1. Fork le projet
2. Créer une branche pour votre fonctionnalité
3. Commiter vos changements
4. Pousser vers la branche
5. Ouvrir une Pull Request

## Licence

Ce projet est sous licence OpenGL 3.0. Voir le fichier `LICENSE` pour plus de détails.

## Auteur

- Yglsan (contact@yglsan.com)
