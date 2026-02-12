# Analyse Radare2 – Fonctionnalité « Recherche SQL » de Looping

Ce document décrit **comment analyser avec radare2** la structure de la fonctionnalité de recherche SQL (ou équivalent) dans le binaire **Looping.exe**, afin de s’en inspirer pour implémenter le bouton **SQL Search** dans BarrelMCD.

**Prérequis** : avoir téléchargé Looping (version 4.1) depuis [looping-mcd.fr](https://www.looping-mcd.fr/) et extrait `Looping.exe` (32 ou 64 bits). Exemple : `~/Téléchargements/Looping.exe` ou `~/Téléchargements/Looping/Looping64.exe`.

---

## 1. Objectif de l’analyse

Identifier dans le binaire Looping :

- Les **chaînes** liées à la recherche (Recherche, Search, Requête, SQL, procédure, trigger, vue, contrainte, dépendance, etc.).
- Les **références** (xrefs) de ces chaînes vers le code (fonctions qui les utilisent).
- La **structure logique** : menus, dialogues, types d’objets recherchés (requêtes, procédures stockées, vues, triggers, contraintes, dépendances).

Cela permettra de documenter le flux UI et les concepts pour reproduire une fonctionnalité équivalente (ou supérieure) dans BarrelMCD.

---

## 2. Commandes Radare2 de base

### 2.1 Ouvrir le binaire (sans analyse lourde)

```bash
r2 -q -e bin.relocs.apply=true -e bin.cache=true "/chemin/vers/Looping.exe"
```

En mode batch (une seule commande) :

```bash
r2 -q -e bin.relocs.apply=true -c "e bin.cache=true; iI" "/chemin/vers/Looping.exe"
```

- `iI` : infos binaire (format PE, architecture).
- Pour un PE Windows x86/x64, les chaînes sont souvent en `.rdata` / `.data`, en ASCII ou UTF-16.

### 2.2 Extraire toutes les chaînes

- **`iz`** : chaînes en section data (courtes).
- **`izz`** : toutes les chaînes (y compris dans le code).

En batch, pour grepper ensuite :

```bash
r2 -q -e bin.relocs.apply=true -c "izz" "/chemin/vers/Looping.exe" > looping_strings.txt
```

Puis :

```bash
grep -iE "recherche|search|requête|query|sql|procédure|trigger|vue|view|contrainte|dépendance|dependency|stored|procedure" looping_strings.txt
```

### 2.3 Chaînes UTF-16 (Windows)

Looping étant un logiciel Windows (MFC / C++), beaucoup de libellés sont en UTF-16. Avec r2, les chaînes wide sont parfois listées par `izz` (selon le support du binaire). Sinon, recherche manuelle :

```bash
r2 -q -e bin.relocs.apply=true -c "/w Recherche" "/chemin/vers/Looping.exe"
```

- **`/w chaine`** : recherche de la chaîne wide (UTF-16) dans le binaire.

Pour lister les hits et leurs adresses :

```bash
r2 -q -e bin.relocs.apply=true -c "/w Recherche; px 32" "/chemin/vers/Looping.exe"
```

### 2.4 Références (xrefs) vers une chaîne

Une fois une adresse intéressante trouvée (ex. chaîne "Recherche" en .rdata) :

1. Ouvrir une session interactive : `r2 -e bin.relocs.apply=true "/chemin/vers/Looping.exe"`.
2. Aller à l’adresse : `s 0xADRESSE`.
3. Lister les références **vers** cette adresse : **`axt`** (xref to).
4. Les adresses affichées sont des endroits dans le code qui utilisent cette chaîne (souvent des call ou des lea vers la chaîne).

Cela permet de remonter aux fonctions qui gèrent le menu « Recherche » ou la boîte de dialogue.

### 2.5 Analyse des fonctions (afl)

Après une analyse complète :

```bash
r2 -q -e bin.relocs.apply=true -c "aaa; afl" "/chemin/vers/Looping.exe" > looping_functions.txt
```

Les fonctions sont en général sans symbole (ex. `fcn.1401258a8`). Pour associer une fonction à la « recherche SQL », il faut :

- Partir d’une chaîne (ex. « Recherche dans le projet » ou « Procédures stockées »).
- Faire `axt` sur cette chaîne pour obtenir l’adresse d’une fonction.
- Dans une session r2 : `s ADRESSE_FONCTION; pdf` pour désassembler la fonction et voir la logique (appels à d’autres sous-fonctions, comparaisons, etc.).

---

## 3. Mots-clés à cibler (grep sur izz / iz)

À extraire et analyser en priorité :

| Catégorie        | Mots-clés (FR/EN) |
|-----------------|-------------------|
| Recherche       | Recherche, Search, Chercher, Find |
| Requêtes       | Requête, Query, SQL |
| Objets BDD     | Procédure, Stored procedure, Trigger, Vue, View, Contrainte, Constraint |
| Dépendances    | Dépendance, Dependency, Référence, Reference, Appel, Call |
| UI             | Recherche dans, Rechercher, Critères, Filtre, Résultat |

Exemple de commande unique (sortie r2 en UTF-8 selon l’env) :

```bash
r2 -q -e bin.relocs.apply=true -c "izz" "/chemin/vers/Looping.exe" 2>/dev/null | grep -iE "recherche|search|requête|query|sql|procédure|trigger|vue|view|contrainte|dépendance|dependency|stored|procedure|chercher|find|filtre|résultat"
```

---

## 4. Structure attendue (à confirmer par l’analyse)

D’après la description utilisateur et les logiciels du domaine (DBeaver, SSMS, Redgate SQL Search) :

1. **Point d’entrée** : un menu ou un bouton (ex. « Outils » → « Recherche SQL » ou icône loupe).
2. **Fenêtre de recherche** :
   - Zone de saisie (texte ou « problématique »).
   - Filtres par type : Requêtes SQL, Procédures stockées, Triggers, Vues, Contraintes, Dépendances.
   - Option « Recherche complexe » ou « Requêtes complexes ».
3. **Moteur** :
   - Parcours des métadonnées (catalogues SGBD) et/ou parsing du code SQL (scripts, DDL).
   - Construction éventuelle d’un graphe de dépendances (qui appelle quoi).
4. **Résultats** :
   - Liste d’objets avec nom, type, emplacement (fichier / base / schéma).
   - Clic → ouverture de l’objet (éditeur, position dans le script).

L’analyse r2 doit permettre de **valider ou préciser** cette structure (noms de menus, libellés, présence ou non de « recherche par problématique »).

---

## 5. Script d’extraction fourni

Un script shell est fourni dans le dépôt :

- **`scripts/radare2_looping_sql_search.sh`**

Il prend en argument le chemin vers `Looping.exe`, exécute les commandes r2 utiles et produit des fichiers de sortie dans `docs/analysis_output/` (ou un répertoire indiqué) pour exploitation ultérieure.

Voir le script pour les commandes exactes et le format de sortie.

---

## 6. Suite : spécification BarrelMCD « SQL Search »

Une fois l’analyse effectuée (et les chaînes / xrefs documentés), la spec BarrelMCD pour le bouton **SQL Search** sera mise à jour dans :

- **`docs/SQL_SEARCH_SPEC.md`** (à créer ou à compléter)

avec :

- Les choix d’UI inspirés de Looping (menus, filtres, résultats).
- Les fonctionnalités visées : recherche texte, requêtes complexes, procédures/triggers/vues/contraintes, dépendances, graphe visuel, recherche par problématique.
- Références DBeaver / SSMS pour aller au-delà de Looping si besoin.

---

*Document rédigé pour le projet BarrelMCD – analyse Looping avec radare2 (février 2026).*
