# Analyse : « Ça se lance mais ça ne fait rien »

## Résumé

| Cause possible | Verdict | Détail |
|----------------|---------|--------|
| **1. Code Python** | ❌ Probablement pas | L’API est utilisée seulement pour import/export/validation. La création d’entité au clic ne passe pas par l’API. |
| **2. Code Flutter** | ✅ **Oui** | Erreur de compilation (doublon `_buildEntity`) et/ou gestes (tap) pas reçus ou pas traités. |
| **3. Jonction Flutter ↔ API** | ⚠️ Partiel | Port et URLs sont cohérents ; si l’API n’est pas sur 8001, seul import/validation/export sont impactés, pas le clic sur le canvas. |

---

## 1. Code Python (API)

- **Rôle** : parse Markdown, validation MCD, MCD → MLD, MCD → SQL, analyse de données.
- **Pas utilisé pour** : création d’une entité au clic, création d’une association au clic, déplacement, liens. Tout ça est **local** dans Flutter (`McdState.addEntity`, `addAssociation`, etc.).
- **Conclusion** : si « rien ne se passe » au sens « je clique sur le canvas et aucune entité ne s’ajoute », le problème ne vient **pas** du code Python. En revanche, si « rien ne se passe » = « l’import Markdown / la validation / l’export ne marchent pas », alors l’API (ou la jonction) peut être en cause.

---

## 2. Code Flutter

### 2.1 Erreur de compilation (prioritaire)

Le fichier `lib/widgets/mcd_canvas.dart` contient encore :

- Une méthode factice `_onEntityLongPress_BUILDENTITY_SECOND_PLACEHOLDER_TO_DELETE` (bloc invalide avec `if (false) const Text(...)`).
- Une **deuxième** définition de `_buildEntity` (doublon).

Résultat : **`_buildEntity' is already declared in this scope`** et erreurs de syntaxe. Tant que ce bloc n’est pas supprimé, le projet ne compile pas (ou vous lancez une ancienne build). Dans ce cas, « ça ne fait rien » peut simplement venir du fait que la dernière version avec les clics ne tourne pas.

**Correction appliquée** : le fichier `mcd_canvas.dart` a été **restauré depuis Git** (`git restore barrelmcd_flutter/lib/widgets/mcd_canvas.dart`). La version dans le dépôt compile et contient déjà la logique de clic (onTapUp → _onCanvasTap → _showNewEntityDialog). Si vous aviez des modifications locales (dont le bloc dupliqué), elles ont été annulées. Pour retrouver la logique de clic sans le doublon, gardez cette version restaurée.

### 2.2 Comportement au clic (une fois que ça compile)

Le flux prévu est :

1. **Clic sur le canvas** → `GestureDetector.onTapUp` → `_onCanvasTap(localPosition, sceneWidth, sceneHeight)`.
2. Si le canvas est vide **ou** si le mode est « Entité » → `_showNewEntityDialog(x, y)`.
3. Le dialogue demande le nom → à la validation, `state.addEntity(trimmed, x, y)` puis `notifyListeners()`.

Si « ça compile mais le clic ne fait rien » :

- Vérifier en console les logs `[McdCanvas] onTapUp` et `[McdCanvas] _onCanvasTap` (avec `_kCanvasDebug = true`).
- Si ces logs n’apparaissent pas : le tap est peut‑être absorbé par un autre widget (ex. `InteractiveViewer` pour le pan/zoom) ou la zone cliquable ne couvre pas la zone visible.
- Si les logs apparaissent mais pas le dialogue : problème dans `_showNewEntityDialog` ou dans le `context` (navigator, overlay).
- Si le dialogue s’ouvre mais l’entité n’apparaît pas : problème dans `addEntity` ou dans la mise à jour d’état / rebuild du canvas.

Donc le blocage « rien ne se passe » côté interface est **côté Flutter** (état, gestes, build).

---

## 3. Jonction Flutter ↔ API

- **Flutter** : `ApiClient(baseUrl: 'http://127.0.0.1:8001')` (`lib/main.dart`).
- **Python** : lancer l’API sur le **même port** :  
  `cd BarrelMCD-python && .venv/bin/python -m uvicorn api.main:app --reload --port 8001`
- **Routes** : `/api/parse-markdown`, `/api/validate`, `/api/to-mld`, `/api/to-sql`, etc. ; le préfixe `/api` est cohérent avec le routeur Python.

Si l’API est sur **8000** (ou pas démarrée), les appels Flutter (import Markdown, validation, export) échoueront, mais **pas** la création d’entité au clic, qui est purement locale.

En résumé : la jonction est importante pour tout ce qui passe par l’API ; pour « clic → nouvelle entité », elle n’est pas en cause.

---

## Synthèse et ordre d’action

1. **Corriger le Flutter**  
   Supprimer le bloc dupliqué / factice dans `mcd_canvas.dart` (lignes 560–618) pour que le projet compile. Puis vérifier les logs de tap et le flux `_onCanvasTap` → `_showNewEntityDialog` → `addEntity`.

2. **Vérifier la jonction uniquement pour import/export/validation**  
   Démarrer l’API sur le port **8001** et tester depuis l’app (import Markdown, bouton Valider, export MLD/SQL).

3. **Ne pas chercher la cause « rien ne se passe » côté Python** pour le simple clic de création d’entité : ce chemin n’utilise pas l’API.

En bref : **le problème « ça ne fait rien » est principalement Flutter** (build + gestion des clics) ; la jonction et l’API concernent le reste des fonctionnalités (import, validation, export).
