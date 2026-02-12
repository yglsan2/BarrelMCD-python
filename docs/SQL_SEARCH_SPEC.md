# Spécification – Bouton « SQL Search » (BarrelMCD)

Ce document décrit la fonctionnalité **SQL Search** à implémenter dans BarrelMCD : un bouton dans la deuxième barre d’outils ouvrant une fenêtre dédiée pour rechercher dans le code SQL (requêtes, procédures stockées, triggers, vues, contraintes, dépendances, appels croisés), avec l’ambition de dépasser SSMS et de s’inspirer de **Looping** et **DBeaver**.

---

## 1. Références et inspiration

| Source | Apport attendu |
|-------|----------------|
| **Looping** | Structure de la fonctionnalité « recherche SQL » (à documenter via analyse radare2 : voir [ANALYSE_RADARE2_LOOPING_SQL_SEARCH.md](ANALYSE_RADARE2_LOOPING_SQL_SEARCH.md) et script `scripts/radare2_looping_sql_search.sh`). |
| **DBeaver** (open source) | Recherche full-text dans les métadonnées, navigation par type d’objet, dépendances. |
| **Redgate SQL Search** | Recherche de fragments SQL dans tables, vues, procédures, fonctions, jobs ; wildcards et booléens. |
| **SSMS** | Objectif : faire mieux (recherche par problématique, graphe de dépendances, moteur visuel). |

---

## 2. Position dans l’interface

- **Emplacement** : bouton **« SQL Search »** (ou icône loupe + libellé) dans la **deuxième barre d’outils** (celle du panneau MLD/SQL ou barre d’outils secondaire selon le layout actuel).
- **Action** : ouverture d’une **fenêtre** (panneau latéral, drawer ou dialogue) dédiée à la recherche SQL, sans fermer le MCD ni le panneau MLD.

---

## 3. Services offerts dans la fenêtre SQL Search

La fenêtre doit permettre au moins :

1. **Recherche par mots-clés**  
   - Dans : requêtes SQL, procédures stockées, triggers, vues, contraintes, définitions d’objets.  
   - Filtres par type d’objet (cases à cocher ou onglets).  
   - Option « requêtes complexes » (requêtes contenant sous-requêtes, JOINs multiples, etc.).

2. **Recherche par problématique**  
   - Saisie d’une question ou d’une phrase (ex. « qui met à jour la table X ? », « où est utilisée la vue Y ? »).  
   - Interprétation (règles heuristiques et/ou indexation) pour retrouver les objets concernés (tables, vues, procédures, triggers).

3. **Objets et métadonnées**  
   - Liste des **procédures stockées**, **triggers**, **vues**, **contraintes**.  
   - Pour chaque objet : nom, type, schéma/base, extrait de définition.

4. **Dépendances et appels croisés**  
   - **Graphe de dépendances** : qui dépend de quoi (vue → tables, procédure → vues/tables, trigger → table).  
   - **Appels croisés** : procédure A appelle procédure B, etc.  
   - Navigation depuis un résultat vers le graphe (nœud sélectionné).

5. **Moteur visuel spécialisé**  
   - Vue graphe interactive (nœuds = objets, arêtes = dépendances / appels).  
   - Zoom, pan, clic sur un nœud pour ouvrir la définition ou la position dans le code.

---

## 4. Flux technique envisagé

1. **Connexion**  
   - Utiliser une connexion BDD déjà configurée dans l’app (celle utilisée pour le MLD/MPD ou une connexion dédiée « analyse »).  
   - À terme : possibilité de plusieurs connexions (multi-serveurs).

2. **Métadonnées**  
   - Interrogation des catalogues (ex. `INFORMATION_SCHEMA`, vues système selon SGBD) pour lister les objets (procédures, triggers, vues, contraintes).  
   - Récupération des définitions (DDL) pour chaque objet.

3. **Parsing SQL**  
   - Parser les définitions (et éventuellement les requêtes sauvegardées) pour extraire :  
     - tables/colonnes référencées ;  
     - appels à d’autres objets (procédures, vues).  
   - Construire un **graphe de dépendances** (graphe orienté : objet A → objet B si A référence B).

4. **Indexation / recherche**  
   - Index full-text (ou recherche simple) sur les noms et le texte des définitions.  
   - Pour « recherche par problématique » : mapping question → requêtes de recherche (mots-clés, types d’objets) ou usage d’un modèle local/API (optionnel, phase ultérieure).

5. **UI**  
   - Zone de saisie (recherche + option « problématique »).  
   - Filtres par type (Requêtes, Procédures, Triggers, Vues, Contraintes, Dépendances).  
   - Liste de résultats (nom, type, extrait) avec action « Ouvrir » / « Aller au graphe ».  
   - Onglet ou panneau « Graphe de dépendances » avec rendu visuel interactif.

---

## 5. Phases d’implémentation proposées

| Phase | Contenu |
|-------|--------|
| **0** | Bouton « SQL Search » dans la 2ᵉ barre ; ouverture d’une fenêtre vide avec zone de recherche et zone de résultats (placeholder). |
| **1** | Connexion au SGBD ; recherche par mots-clés dans les métadonnées (noms + définitions) ; filtres par type d’objet. |
| **2** | Parsing SQL des définitions ; construction du graphe de dépendances ; affichage liste + liens « dépend de » / « utilisé par ». |
| **3** | Moteur visuel : graphe interactif (nœuds, arêtes), zoom/pan, clic pour ouvrir l’objet. |
| **4** | Recherche par problématique (heuristiques + indexation) ; requêtes complexes détectées ; amélioration UX (suggestions, historique). |

---

## 6. Analyse Looping (radare2)

Pour aligner la structure et le vocabulaire sur Looping :

1. **Télécharger** Looping (ex. [looping-mcd.fr](https://www.looping-mcd.fr/)) et extraire `Looping.exe`.  
2. **Lancer** le script d’analyse :  
   `./scripts/radare2_looping_sql_search.sh /chemin/vers/Looping.exe`  
3. **Exploiter** les sorties dans `docs/analysis_output/` (chaînes, puis xrefs en session r2) et mettre à jour ce spec ou [ANALYSE_RADARE2_LOOPING_SQL_SEARCH.md](ANALYSE_RADARE2_LOOPING_SQL_SEARCH.md) avec les menus, libellés et flux identifiés.  
4. **Itérer** sur l’UI BarrelMCD (bouton, fenêtre, filtres) pour coller au comportement Looping tout en visant DBeaver/SSMS+.

---

## 7. Fichiers liés

- `docs/ANALYSE_RADARE2_LOOPING_SQL_SEARCH.md` – Méthodologie radare2 pour analyser la fonctionnalité dans Looping.  
- `scripts/radare2_looping_sql_search.sh` – Script d’extraction des chaînes et infos binaire.  
- `docs/analysis_output/` – Sorties du script (ignoré par git).  

---

*Spec v1 – février 2026. À compléter après analyse radare2 de Looping et premiers maquettes UI.*
