# BarrelMCD

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/downloads/)
[![Flutter](https://img.shields.io/badge/Flutter-Dart-02569B?logo=flutter)](https://flutter.dev/)

*Outil simple et intuitif pour la modélisation de données (MCD / MLD / SQL)*

**Auteur :** DesertYGL

[Installation](#-installation) • [Utilisation](#-utilisation) • [Structure](#-structure-du-projet) • [Licence](#-licence)

</div>

---

## À propos

BarrelMCD permet de concevoir des **modèles conceptuels de données** (MCD), de les convertir en **modèle logique** (MLD) et d’en générer le **SQL**. Le projet repose sur un **backend Python** (API FastAPI) et une **interface Flutter** (desktop : Linux, Windows, macOS).

## Fonctionnalités

### Canvas MCD

- **Entités** : création, placement, édition du nom et des attributs.
- **Associations** : création avec 1 à 8 bras (points de connexion), attributs éditables.
- **Liens** : liaison entité ↔ association avec **cardinalités** (1, n, 0,1, etc.), sens gauche↔droite, flèches et libellés.
- **Sélection** : mode Sélection pour déplacer entités/associations ; cycle de sélection quand plusieurs éléments se superposent.
- **Navigation** : zoom (molette), pan (glisser le fond du canvas).
- **Fichier** : ouvrir / enregistrer en `.bar` ou `.json`.

### Import Markdown

- Parsing de fichiers `.md` pour en déduire entités et associations.
- Prévisualisation et validation du MCD avant intégration.
- Nécessite l’API backend.

### MLD et SQL

- Panneaux **MLD** et **SQL** générés à partir du MCD courant via l’API.
- Sans API : l’app reste utilisable pour éditer et sauvegarder le MCD.

### Autres

- **Annuler / rétablir** (undo / redo).
- **Explorateur d’éléments** : liste des entités et associations, accès rapide à l’édition.
- **Thème sombre** par défaut.

## Installation

### Prérequis

- **Python 3.8+** (pour l’API)
- **Flutter SDK** (pour l’interface)
- Un environnement virtuel Python (venv) est recommandé pour le backend

### Cloner le dépôt

```bash
git clone https://github.com/yglsan2/BarrelMCD-python.git
cd BarrelMCD-python
```

### Lancer l’API (backend)

```bash
./run_api.sh
```

À la première exécution, un venv `.venv` est créé et les dépendances installées. L’API est ensuite disponible sur http://127.0.0.1:8000.

### Lancer l’interface Flutter

```bash
cd barrelmcd_flutter
flutter pub get
flutter run -d linux   # ou windows, macos, chrome, etc.
```

## Utilisation

1. Démarrer l’API : `./run_api.sh` (à la racine).
2. Lancer l’app : `cd barrelmcd_flutter && flutter run -d linux`.
3. Utiliser les modes **Entité**, **Association**, **Lien** pour construire le MCD ; **Markdown** pour importer ; **MLD / SQL** pour afficher les sorties.

Sans API, l’application reste utilisable pour créer, modifier et sauvegarder des modèles (`.bar` / `.json`) ; l’import Markdown et la génération MLD/SQL nécessitent l’API.

## Structure du projet

| Élément            | Rôle |
|--------------------|------|
| `api/`             | API FastAPI (parsing Markdown, validation MCD, MCD→MLD→SQL) |
| `barrelmcd_flutter/` | Application Flutter (interface graphique) |
| `views/`, `models/` | Logique Python (parsers, convertisseurs) |
| `main.py`          | Ancienne interface PyQt (optionnelle) |
| `run_api.sh`       | Script de lancement de l’API avec venv |

## Licence

Ce projet est sous **licence MIT**. Voir le fichier [LICENSE](LICENSE) pour les détails.

---

<div align="center">

*BarrelMCD — DesertYGL*

</div>
