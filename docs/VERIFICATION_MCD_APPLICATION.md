# Vérification de l'application MCD BarrelMCD

Rapport d'analyse et corrections effectuées pour rendre le logiciel MCD utilisable.

---

## 1. Corrections effectuées

### 1.1 Fichier `barrelmcd_flutter/lib/widgets/mcd_canvas.dart`

- **Doublon supprimé** : la méthode factice `_onEntityLongPress_BUILDENTITY_SECOND_PLACEHOLDER_TO_DELETE` et la deuxième déclaration de `_buildEntity` ont été retirées. Il ne reste qu’une seule méthode `_buildEntity` et la vraie méthode `_onEntityLongPress`.
- **Mode debug désactivé** : `_kCanvasDebug = false` pour limiter les logs en console et masquer l’overlay de debug en production.

### 1.2 Fichier `barrelmcd_flutter/lib/widgets/main_toolbar.dart`

- **Export image** : utilisation directe de `exportImageKey` au lieu de `context.findAncestorWidgetOfExactType<MainToolbar>()?.exportImageKey`, qui ne permettait pas de récupérer le bon `RepaintBoundary` pour l’export PNG.

### 1.3 Fichier `barrelmcd_flutter/lib/core/canvas_mode.dart`

- **Mode debug désactivé** : `_kCanvasModeDebug = false`.

---

## 2. Vérifications effectuées

### 2.1 Flux canvas (Flutter)

- **Clic sur canvas vide** : ouverture du dialogue « Nouvelle entité », puis `addEntity` → entité affichée.
- **Mode Entité (E)** : clic sur le canvas → dialogue « Nouvelle entité ».
- **Mode Association (A)** : clic → dialogue « Nouvelle association ».
- **Mode Lien (L)** : clic entité puis association (ou l’inverse) → dialogue cardinalité (0,1 | 1,1 | 0,n | 1,n) → `addAssociationLink`.
- **Mode Sélection** : clic sur le vide → `selectNone` ; pan du canvas (InteractiveViewer) ; glisser une entité/association pour la déplacer.
- **Long press** sur entité/association : menu contextuel (renommer, attributs, faible/fictive, héritage, supprimer).

### 2.2 État MCD (`mcd_state.dart`)

- Entités, associations, `association_links`, `inheritance_links` ; undo/redo ; `mcdData` au format attendu par l’API (associations avec `entities` et `cardinalities` dérivés des liens).
- `loadFromCanvasFormat` pour ouvrir un fichier .bar/.json ou après import Markdown.

### 2.3 API Python

- **Routes** : `/api/parse-markdown`, `/api/validate`, `/api/to-mld`, `/api/to-sql`, `/api/analyze-data` ; `/health` à la racine.
- **CORS** : activé pour tous les origines en dev.
- **Format** : `mcd_service` adapte le format canvas (entités, associations, association_links, inheritance_links) vers le format interne (ModelConverter) ; `validate_mcd` utilise `merise_rules` + validateur Markdown.

### 2.4 Jonction Flutter ↔ API

- **Base URL** : `http://127.0.0.1:8001` dans `main.dart`.
- **Lancement API** : `cd BarrelMCD-python && .venv/bin/python -m uvicorn api.main:app --reload --port 8001`
- Les appels Flutter (`parseMarkdown`, `validateMcd`, `mcdToSql`, `mcdToMld`) utilisent le préfixe `/api` ; côté Python le routeur est monté avec `prefix="/api"`.

### 2.5 Barre d’outils

- Fichier : Nouveau, Ouvrir (.bar/.json/.loo), Enregistrer, Enregistrer sous.
- Modes : Sélection, Entité, Association, Lien ; bouton Auto-Liens (message d’info).
- Zoom +/-, Ajuster, Grille ; Supprimer ; Annuler / Répéter.
- Importer, Markdown, MLD/SQL, Valider, SQL, Image, PDF (PDF : message « à intégrer »), Copier MCD, Éléments, Aide, Console.

---

## 3. Analyse statique

- `dart analyze lib/` : **0 erreur** ; 2 infos (prefer_const dans `_buildEmptyHint`).
- Le projet Flutter compile.

---

## 4. Si l’erreur « _buildEntity already declared » réapparaît

Si le bloc dupliqué réapparaît dans `mcd_canvas.dart` (par exemple après un merge), exécuter depuis la racine du dépôt :

```bash
cd barrelmcd_flutter && python3 -c "
path = 'lib/widgets/mcd_canvas.dart'
with open(path, 'r', encoding='utf-8') as f:
    c = f.read()
start = c.find('  void _onEntityLongPress_BUILDENTITY_SECOND_PLACEHOLDER_TO_DELETE(')
end = c.find('\n  void _onEntityLongPress(BuildContext context, McdState state, int index, Map<String, dynamic> entity) {')
if start != -1 and end != -1:
    with open(path, 'w', encoding='utf-8') as f:
        f.write(c[:start] + c[end:])
    print('Bloc dupliqué supprimé.')
else:
    print('Marqueurs non trouvés (déjà corrigé ou fichier différent).')
"
```

---

## 5. Commandes pour lancer l’application

**Terminal 1 – API :**
```bash
cd /home/benjisan/BarrelMCD-python && .venv/bin/python -m uvicorn api.main:app --reload --port 8001
```

**Terminal 2 – Flutter :**
```bash
cd /home/benjisan/BarrelMCD-python/barrelmcd_flutter && flutter run
```

Sans l’API, la création d’entités/associations et les liens fonctionnent en local ; l’import Markdown, la validation MCD et l’export MLD/SQL nécessitent l’API sur le port 8001.
