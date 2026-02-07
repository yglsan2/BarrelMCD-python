# BarrelMCD Flutter

Interface Flutter pour BarrelMCD. Reprend le design de l'interface Python (thème sombre, barre d'outils, canvas MCD) et délègue la logique au backend Python via l'API.

## Prérequis

- Flutter SDK
- Backend API BarrelMCD en cours d'exécution (voir `api/README.md`)

## Configuration

L'URL de l'API est définie dans `lib/main.dart` :

```dart
ApiClient(baseUrl: 'http://127.0.0.1:8000')
```

Pour Android émulateur, utilisez `http://10.0.2.2:8000`.

## Installation et lancement

```bash
cd barrelmcd_flutter
flutter pub get
flutter run -d linux   # ou chrome, android, etc.
```

## Structure

- `lib/main.dart` : point d'entrée, Provider (ApiClient, McdState)
- `lib/app.dart` : MaterialApp, thème
- `lib/theme/app_theme.dart` : couleurs et thème (alignés sur le Python)
- `lib/core/api_client.dart` : appels HTTP vers l'API
- `lib/core/mcd_state.dart` : état MCD (entités, associations, log)
- `lib/screens/` : HomeScreen, MarkdownImportScreen, dialogs (Aide, SQL)
- `lib/widgets/` : MainToolbar, McdCanvas, EntityBox, AssociationDiamond

## Fonctionnalités

- **Canvas interactif** : modes Sélection, Entité, Association, Lien. Création au clic (entité/association), liaison association↔entité avec choix de cardinalité (1,1 / 1,n / 0,n etc.). Déplacement par glisser-déposer. Flèches avec cardinalités dessinées entre associations et entités.
- **Fichier** : Nouveau, Ouvrir (.bar / .json), Enregistrer / Enregistrer sous. Format .bar compatible avec le projet Python.
- **Undo / Redo** : historique (50 niveaux). Suppression de l’élément sélectionné (Suppr ou bouton). Sélection via l’Explorateur (liste entités / associations / liens) ou en cliquant sur le canvas en mode Sélection.
- **Import Markdown** : onglets Fichier, Éditeur, Prévisualisation, Validation. Template, import vers le modèle. Les liens association–entité sont créés automatiquement.
- **MLD / SQL** : panneau « MLD/SQL » (génération via l’API). Export SQL (copier / dialogue). La logique MCD→MLD→SQL et la prise en charge de `primary_key` sur les attributs sont côté API Python.
- **Explorateur** : liste des entités, associations et liens ; clic pour sélectionner puis Suppr pour supprimer.
- **Raccourcis** : Suppr (supprimer), Ctrl+Z (annuler), Ctrl+Y (répéter). Grille (bouton), zoom (InteractiveViewer à la molette).

La logique métier (parsing, validation, MCD→MLD→SQL) est exécutée côté Python ; l’UI Flutter envoie le modèle au format documenté dans `docs/INTERFACE_ANALYSE_FLUTTER.md`.
