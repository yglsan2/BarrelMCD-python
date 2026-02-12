# Fonctionnalités MCD – État par rapport à la liste type Barrel

| # | Fonctionnalité | État BarrelMCD (Flutter + API) |
|---|----------------|-------------------------------|
| 1 | **Modélisation Entité/Association et Diagramme de Classes UML** | **Partiel** – MCD Entité/Association complet. Diagramme de classes UML : conversion MCD→UML existe côté Python (`model_converter.convert_to_uml`) mais pas de vue UML dans l’app Flutter. |
| 2 | **Classes d'entités fictives non générées dans le MLD** | **Oui** – Entité fictive (`is_fictive`) : menu contextuel « Entité fictive (non générée MLD) », exclue du MLD/SQL côté API. |
| 3 | **Transformation association en entité avec identifiants relatifs** | **Non** – Non implémenté dans l’interface ni dans l’API. |
| 4 | **Définition des propriétés et des types de données** | **Oui** – Attributs (nom, type, clé primaire) sur entités et associations. Types en texte libre (VARCHAR, INTEGER, etc.). |
| 5 | **Héritage avec spécialisations et généralisations** | **Partiel** – Liens d’héritage parent/enfant, affichage et édition. Pas de distinction explicite spécialisation/généralisation ni de copie automatique des attributs hérités dans l’UI. |
| 6 | **Contraintes d'intégrité fonctionnelle (CIF) et inter-associations** | **Non** – Côté Python : `cif_constraints.py`, `CIFManager`. Non exposé dans l’API ni dans Flutter. |
| 7 | **Règles de gestion avec possibilité de spécifier du code SQL** | **Non** – Côté Python : `business_rules.py`. Non exposé dans l’API ni dans Flutter. |
| 8 | **Insertion de textes, graphiques et images connectables par flux** | **Non** – Canvas limité aux entités, associations et liens. |
| 9 | **MLD affiché en temps réel** | **Oui** – Panneau MLD/SQL ; cache invalidé à chaque modification MCD ; rafraîchissement en arrière-plan (transposition instantanée) ; bouton Rafraîchir. |
| 10 | **Requêtes SQL DDL en temps réel** | **Oui** – Même panneau ; MLD/MPD/SQL régénérés à l’ouverture si besoin, précalcul en arrière-plan après édition MCD. |
| 11 | **Exportation de scripts SQL pour les principaux SGBD** | **Oui** – Panneau MLD/SQL : choix SGBD (MySQL, PostgreSQL, SQLite). API `to-sql` avec paramètre `dbms`. |
| 12 | **Possibilité de paramétrer un SGBD personnalisé** | **Non** – Pas de moteur SGBD personnalisé (seulement les 3 prédéfinis). |
| 13 | **Exportation des MCD aux formats images et presse-papier** | **Oui** – Export image PNG ; bouton « Copier MCD » (JSON) et « Copier SQL » / « Copier MLD » dans le panneau MLD/SQL. |
| 14 | **Affichage multi-vues et multi-zooms** | **Partiel** – Une seule vue, zoom (InteractiveViewer). Pas de plusieurs vues simultanées. |
| 15 | **Présentation entièrement personnalisable** | **Non** – Thème sombre fixe. Pas de personnalisation couleurs/polices/formes. |

## Synthèse

- **Déjà en place** : 1 (propriétés et types).
- **Partiel** : 7 (MCD+UML, héritage, MLD/SQL temps réel, export SQL, export image, multi-zoom, presse-papier).
- **Absent dans l’app** : 7 (entités fictives, transformation assoc→entité, CIF, règles de gestion, textes/images, SGBD personnalisé, personnalisation présentation).

Ce document peut être mis à jour au fur et à mesure des évolutions.

---

**Voir aussi** : [ANALYSE_LOGIQUE_METIER_LOOPING.md](ANALYSE_LOGIQUE_METIER_LOOPING.md) — analyse détaillée de la logique métier Barrel (entités, attributs, cardinalités MCD/MLD, CIF, règles de gestion, MPD, SQL) et roadmap pour atteindre le même niveau dans Barrel MCD.
