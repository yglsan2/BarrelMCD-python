# Transcription MCD → MLD → MPD → SQL : alignement Barrel

Ce document décrit comment **Barrel MCD** transpose un modèle conceptuel (MCD) vers le MLD, le MPD et le SQL, et en quoi cette logique est **alignée sur Barrel** (et les règles Merise).

**Références** : `docs/ANALYSE_LOGIQUE_METIER_LOOPING.md`, binaire Barrel.exe (chaînes UTF-16), `views/model_converter.py`, `api/services/mcd_service.py`.

---

## 1. Chaîne de transcription

| Étape | Barrel | Barrel MCD |
|-------|--------|------------|
| MCD (canvas) | Entités, associations, liens, cardinalités 0,1 \| 1,1 \| 0,n \| 1,n | Idem : `mcdData` (entities, associations, association_links, inheritance_links) |
| MCD → MLD | Entité → table ; 1,n/0,n → FK côté « n » ; n-n → table de correspondance ; héritage → FK enfant→parent | `mcd_service.mcd_to_mld` → `ModelConverter._convert_to_mld` |
| MLD → MPD | Types physiques par SGBD (INT AUTO_INCREMENT, SERIAL, IDENTITY, etc.) | `ModelConverter.generate_mpd(mld, dbms)` |
| MPD → SQL | CREATE TABLE, PRIMARY KEY, FOREIGN KEY, index, contraintes | `ModelConverter.generate_sql_from_mpd` |

---

## 2. Règles Merise / Barrel appliquées

### 2.1 Clé étrangère côté « n »

- **Règle** : la clé étrangère est portée par la table correspondant à l’entité en **cardinalité max = n** (0,n ou 1,n).
- **Barrel** : dans `_convert_association_to_foreign_keys`, si entity1 est 1,1 ou 0,1 et entity2 est 0,n ou 1,n, la FK est ajoutée à la table entity2 (`_add_foreign_key(mld, entity2, entity1, ...)`). Même logique dans l’autre sens pour 1,n–0,1.

### 2.2 FK nullable si 0,n (Merise / Barrel)

- **Règle** : si la cardinalité côté porteur de la FK est **0,n**, la colonne FK peut être NULL (participation optionnelle).
- **Barrel** : `_add_foreign_key(..., cardinality_source=...)` ; si `cardinality_source == "0,n"` alors `nullable=True`, sinon `nullable=False`. Aligné Barrel.

### 2.3 Table de correspondance (n-n)

- **Barrel** : « créer une table de correspondance dans le MLD », nommée comme l’association.
- **Barrel** : `_create_junction_table` crée une table de liaison :
  - **Nom** : nom de l’association (sanitized : minuscules, espaces → `_`) si fourni et non conflictuel, sinon `entity1_entity2`.
  - Colonnes : `entity1_id`, `entity2_id`, plus les **attributs de l’association** (rubriques) si présents.
  - Clé primaire composite : `(entity1_id, entity2_id)`.
  - Deux clés étrangères vers les tables entity1 et entity2.

### 2.4 Héritage

- **Règle** : l’enfant a une FK vers le parent (1,1 côté enfant).
- **Barrel** : `_convert_inheritance_to_foreign_keys` ajoute une FK de la table enfant vers la table parent, et une contrainte d’unicité sur cette FK (simulation héritage). FK NOT NULL (cardinalité 1,1).

### 2.5 Entités fictives

- **Barrel** : classes fictives non générées dans le MLD.
- **Barrel** : `_canvas_mcd_to_converter_format(exclude_fictive=True)` exclut les entités avec `is_fictive=True` du MCD envoyé au convertisseur. Elles n’apparaissent pas dans le MLD/SQL.

### 2.6 Association porteuse de rubriques et 1,1

- **Barrel** : « La cardinalité 1,1 est interdite lorsque l'association est porteuse de rubriques ».
- **Barrel** : `merise_rules.validate_cardinality_1_1_no_attributes` et validation côté API / Flutter avant mise à jour et à l’édition des cardinalités.

---

## 3. Types SQL (MPD)

- **Barrel** : VARCHAR, VARCHAR2, NVARCHAR, INT, INTEGER, BIGINT, TINYINT, SMALLINT, DATE, DATETIME, DATETIME2, INT IDENTITY, AUTO_INCREMENT, SERIAL, etc.
- **Barrel** : `_convert_type_to_sql` reconnaît les types courants (INTEGER, VARCHAR, VARCHAR2, NVARCHAR, DATE, DATETIME, DECIMAL, BOOLEAN, etc.). Les types déjà avec taille/précision (ex. `VARCHAR(100)`) sont conservés. `generate_mpd` adapte par SGBD :
  - **MySQL** : INT AUTO_INCREMENT, VARCHAR avec index BTREE si pertinent.
  - **PostgreSQL** : SERIAL, VARCHAR.
  - **SQLite** : INTEGER PRIMARY KEY AUTOINCREMENT.
  - **SQL Server** : INT IDENTITY(1,1).

---

## 4. SGBD supportés

| SGBD | Barrel | Barrel MCD |
|------|--------|------------|
| MySQL | Oui | Oui (`dbms=mysql`) |
| PostgreSQL | Oui | Oui |
| SQLite | Oui | Oui |
| SQL Server | Oui (chaînes observées) | Oui (`dbms=sqlserver`) |

---

## 5. Synthèse qualité de transcription

- **MCD → MLD** : même logique que Barrel (entité → table, FK côté n, nullable si 0,n, table de correspondance nommée par l’association, rubriques en n-n, héritage, fictives exclues).
- **MLD → MPD** : types et options par SGBD (AUTO_INCREMENT, SERIAL, IDENTITY, index sur FK).
- **MPD → SQL** : CREATE TABLE, PRIMARY KEY, ALTER TABLE ADD CONSTRAINT (FK et UNIQUE), CREATE INDEX.

Écarts mineurs volontaires ou à compléter selon besoins : pas d’ALTER TABLE pour évolution de schéma, pas de « SGBD personnalisé », pas d’export VB-Access. La **qualité de transcription** d’un modèle à l’autre est alignée sur Barrel pour l’usage courant (MCD → MLD → MPD → SQL, règles Merise, plusieurs SGBD).
