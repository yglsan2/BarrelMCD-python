from typing import Dict, List, Any, Optional
from enum import Enum

class ConversionType(Enum):
    MCD_TO_UML = "mcd_to_uml"
    MCD_TO_MLD = "mcd_to_mld"
    MLD_TO_SQL = "mld_to_sql"

class ModelConverter:
    """Convertisseur intelligent de modèles de données"""
    
    def __init__(self):
        self.default_cardinalities = {
            "ONE_TO_MANY": ("1", "*"),
            "MANY_TO_ONE": ("*", "1"),
            "ONE_TO_ONE": ("1", "1"),
            "MANY_TO_MANY": ("*", "*")
        }
        
    def convert_model(self, source_model: Dict, conversion_type: ConversionType) -> Dict:
        """Convertit un modèle d'un format à un autre."""
        if conversion_type == ConversionType.MCD_TO_UML:
            return self.convert_to_uml(source_model, conversion_type)
        elif conversion_type == ConversionType.MCD_TO_MLD:
            return self._convert_to_mld(source_model)
        elif conversion_type == ConversionType.MLD_TO_SQL:
            return self._convert_to_sql(source_model)
        else:
            raise ValueError(f"Type de conversion non supporté: {conversion_type}")
        
    def convert_to_uml(self, model: Dict, conversion_type: ConversionType) -> Dict:
        """Convertit un modèle vers UML.
        
        Args:
            model: Modèle à convertir
            conversion_type: Type de conversion
            
        Returns:
            Dict: Modèle UML
        """
        uml = {
            "classes": {},
            "associations": [],
            "generalizations": []
        }
        
        # Convertir les entités en classes
        for entity_name, entity in model["entities"].items():
            class_name = entity_name.lower()  # Garder le nom en minuscules
            uml["classes"][class_name] = {
                "name": class_name,
                "attributes": [],
                "methods": []
            }
            
            # Convertir les attributs
            for attr in entity["attributes"]:
                visibility = "+" if attr.get("primary_key", False) else "-"
                uml_type = self._convert_type_to_uml(attr["type"])
                uml["classes"][class_name]["attributes"].append({
                    "name": attr["name"],
                    "type": uml_type,
                    "visibility": visibility
                })
        
        # Convertir les relations en associations et généralisations
        for relation in model.get("relations", []):
            if relation["type"] == "INHERITANCE":
                parent = relation["parent"].lower()  # Garder le nom en minuscules
                child = relation["child"].lower()  # Garder le nom en minuscules
                
                if parent in uml["classes"] and child in uml["classes"]:
                    uml["generalizations"].append({
                        "parent": parent,
                        "child": child
                    })
            else:
                source = relation["source"].lower()  # Garder le nom en minuscules
                target = relation["target"].lower()  # Garder le nom en minuscules
                
                if source in uml["classes"] and target in uml["classes"]:
                    uml["associations"].append({
                        "source": source,
                        "target": target,
                        "source_cardinality": relation.get("source_cardinality", "1"),
                        "target_cardinality": relation.get("target_cardinality", "1")
                    })
        
        return uml
        
    def _convert_to_mld(self, mcd: Dict) -> Dict:
        """Convertit un MCD en MLD avec gestion correcte des clés."""
        mld = {
            "tables": {},
            "foreign_keys": [],
            "constraints": []
        }
        
        # CORRECTION FONDAMENTALE : En MCD, il n'y a pas de clés primaires
        # On doit les générer automatiquement pour le MLD
        
        # Étape 1 : Créer les tables de base
        for entity_name, entity in mcd["entities"].items():
            table = {
                "name": entity["name"].lower(),  # Nom de table en minuscules
                "columns": [],
                "primary_key": []
            }
            
            # Ajouter automatiquement une clé primaire si elle n'existe pas
            has_primary_key = False
            for attr in entity["attributes"]:
                column = {
                    "name": attr["name"],
                    "type": self._convert_type_to_sql(attr["type"]),
                    "nullable": attr.get("is_nullable", True),
                    "size": attr.get("size"),
                    "precision": attr.get("precision"),
                    "scale": attr.get("scale"),
                    "default": attr.get("default_value")
                }
                
                # Détecter les clés primaires potentielles
                if (attr["name"].lower() in ["id", "code", "numero"] or 
                    "identifiant" in attr.get("description", "").lower()):
                    column["nullable"] = False
                    table["primary_key"].append(attr["name"])
                    has_primary_key = True
                
                table["columns"].append(column)
            
            # Si aucune clé primaire n'a été trouvée, en créer une automatiquement
            if not has_primary_key:
                # Ajouter une colonne ID automatique
                id_column = {
                    "name": "id",
                    "type": "INTEGER",
                    "nullable": False,
                    "auto_increment": True
                }
                table["columns"].insert(0, id_column)
                table["primary_key"].append("id")
            
            mld["tables"][entity["name"].lower()] = table
        
        # Étape 2 : Traiter les associations pour créer les clés étrangères
        for association in mcd.get("associations", []):
            self._convert_association_to_foreign_keys(association, mld)
        
        # Étape 3 : Traiter l'héritage
        inheritance = mcd.get("inheritance", {})
        for child, parent in inheritance.items():
            self._convert_inheritance_to_foreign_keys(child, parent, mld)
        
        return mld
    
    def _convert_association_to_foreign_keys(self, association: Dict, mld: Dict) -> None:
        """Convertit une association MCD en clés étrangères MLD."""
        entity1 = association["entity1"].lower()
        entity2 = association["entity2"].lower()
        cardinality1 = association["cardinality1"]
        cardinality2 = association["cardinality2"]
        
        # Règles de conversion des cardinalités vers clés étrangères
        if cardinality1 == "1,1" and cardinality2 == "0,n":
            # Relation 1,n : clé étrangère dans la table "many"
            self._add_foreign_key(mld, entity2, entity1, association["name"])
            
        elif cardinality1 == "0,n" and cardinality2 == "1,1":
            # Relation n,1 : clé étrangère dans la table "many"
            self._add_foreign_key(mld, entity1, entity2, association["name"])
            
        elif cardinality1 == "0,n" and cardinality2 == "0,n":
            # Relation n,n : table de liaison
            self._create_junction_table(mld, entity1, entity2, association)
            
        elif cardinality1 == "1,1" and cardinality2 == "1,1":
            # Relation 1,1 : clé étrangère dans l'une des tables
            self._add_foreign_key(mld, entity1, entity2, association["name"])
    
    def _add_foreign_key(self, mld: Dict, source_table: str, target_table: str, association_name: str) -> None:
        """Ajoute une clé étrangère au MLD."""
        if source_table not in mld["tables"] or target_table not in mld["tables"]:
            return
        
        # Nom de la colonne clé étrangère
        fk_column_name = f"{target_table}_id"
        
        # Ajouter la colonne clé étrangère à la table source
        fk_column = {
            "name": fk_column_name,
            "type": "INTEGER",
            "nullable": False
        }
        
        mld["tables"][source_table]["columns"].append(fk_column)
        
        # Ajouter la contrainte de clé étrangère
        foreign_key = {
            "table": source_table,
            "column": fk_column_name,
            "referenced_table": target_table,
            "referenced_column": "id",
            "constraint_name": f"fk_{source_table}_{target_table}"
        }
        
        mld["foreign_keys"].append(foreign_key)
    
    def _create_junction_table(self, mld: Dict, entity1: str, entity2: str, association: Dict) -> None:
        """Crée une table de liaison pour une relation n,n."""
        junction_table_name = f"{entity1}_{entity2}"
        
        junction_table = {
            "name": junction_table_name,
            "columns": [
                {
                    "name": f"{entity1}_id",
                    "type": "INTEGER",
                    "nullable": False
                },
                {
                    "name": f"{entity2}_id",
                    "type": "INTEGER",
                    "nullable": False
                }
            ],
            "primary_key": [f"{entity1}_id", f"{entity2}_id"]
        }
        
        # Ajouter les attributs de l'association s'ils existent
        if "attributes" in association:
            for attr in association["attributes"]:
                junction_table["columns"].append({
                    "name": attr["name"],
                    "type": self._convert_type_to_sql(attr["type"]),
                    "nullable": attr.get("is_nullable", True)
                })
        
        mld["tables"][junction_table_name] = junction_table
        
        # Ajouter les clés étrangères de la table de liaison
        mld["foreign_keys"].extend([
            {
                "table": junction_table_name,
                "column": f"{entity1}_id",
                "referenced_table": entity1,
                "referenced_column": "id",
                "constraint_name": f"fk_{junction_table_name}_{entity1}"
            },
            {
                "table": junction_table_name,
                "column": f"{entity2}_id",
                "referenced_table": entity2,
                "referenced_column": "id",
                "constraint_name": f"fk_{junction_table_name}_{entity2}"
            }
        ])
    
    def _convert_inheritance_to_foreign_keys(self, child: str, parent: str, mld: Dict) -> None:
        """Convertit l'héritage en clés étrangères."""
        child_table = child.lower()
        parent_table = parent.lower()
        
        if child_table not in mld["tables"] or parent_table not in mld["tables"]:
            return
        
        # Ajouter une clé étrangère de l'enfant vers le parent
        self._add_foreign_key(mld, child_table, parent_table, "inheritance")
        
        # Ajouter une contrainte d'unicité pour simuler l'héritage
        unique_constraint = {
            "table": child_table,
            "columns": [f"{parent_table}_id"],
            "constraint_name": f"uk_{child_table}_parent"
        }
        mld["constraints"].append(unique_constraint)
    
    def _convert_type_to_sql(self, mcd_type: str) -> str:
        """Convertit un type MCD en type SQL."""
        type_mapping = {
            "integer": "INTEGER",
            "varchar": "VARCHAR(255)",
            "text": "TEXT",
            "date": "DATE",
            "datetime": "DATETIME",
            "decimal": "DECIMAL(10,2)",
            "boolean": "BOOLEAN",
            "char": "CHAR(1)",
            "blob": "BLOB"
        }
        return type_mapping.get(mcd_type.lower(), "VARCHAR(255)")
        
    def _convert_to_sql(self, mld: Dict) -> str:
        """Convertit un MLD en script SQL robuste."""
        sql_script = []
        
        # Créer les tables
        for table_name, table in mld["tables"].items():
            sql = f"CREATE TABLE {table_name} (\n"
            
            # Colonnes
            columns = []
            for column in table["columns"]:
                col_def = f"    {column['name']} {column['type']}"
                
                # Gestion des contraintes
                if not column.get("nullable", True):
                    col_def += " NOT NULL"
                if column.get("auto_increment"):
                    col_def += " AUTO_INCREMENT"
                if column.get("default") is not None:
                    default_val = column['default']
                    if isinstance(default_val, str) and not default_val.isdigit():
                        default_val = f"'{default_val}'"
                    col_def += f" DEFAULT {default_val}"
                
                # Gestion des tailles et précisions
                if column.get("size") is not None:
                    col_def = col_def.replace("VARCHAR(255)", f"VARCHAR({column['size']})")
                    col_def = col_def.replace("CHAR(1)", f"CHAR({column['size']})")
                if column.get("precision") is not None and column.get("scale") is not None:
                    col_def = col_def.replace("DECIMAL(10,2)", f"DECIMAL({column['precision']}, {column['scale']})")
                
                columns.append(col_def)
            
            # Clé primaire
            if table["primary_key"]:
                pk_columns = ", ".join(table["primary_key"])
                columns.append(f"    PRIMARY KEY ({pk_columns})")
            
            sql += ",\n".join(columns)
            sql += "\n);"
            sql_script.append(sql)
        
        # Ajouter les clés étrangères
        for fk in mld["foreign_keys"]:
            sql = f"ALTER TABLE {fk['table']} ADD CONSTRAINT {fk['constraint_name']} "
            sql += f"FOREIGN KEY ({fk['column']}) REFERENCES {fk['referenced_table']}({fk['referenced_column']});"
            sql_script.append(sql)
        
        # Ajouter les contraintes d'unicité
        for constraint in mld["constraints"]:
            if constraint.get("constraint_name"):
                sql = f"ALTER TABLE {constraint['table']} ADD CONSTRAINT {constraint['constraint_name']} "
                sql += f"UNIQUE ({', '.join(constraint['columns'])});"
                sql_script.append(sql)
        
        return "\n\n".join(sql_script)
    
    def generate_mpd(self, mld: Dict, dbms: str = "mysql") -> Dict:
        """Génère un MPD (Modèle Physique de Données) à partir du MLD."""
        if not mld:
            return {"tables": {}, "indexes": [], "triggers": [], "procedures": [], "dbms": dbms}
            
        mpd = {
            "tables": {},
            "indexes": [],
            "triggers": [],
            "procedures": [],
            "dbms": dbms
        }
        
        # Convertir les tables MLD en tables MPD
        for table_name, table in mld["tables"].items():
            mpd_table = {
                "name": table_name,
                "columns": [],
                "primary_key": table["primary_key"],
                "indexes": [],
                "triggers": []
            }
            
            # Convertir les colonnes avec optimisations spécifiques au SGBD
            for column in table["columns"]:
                mpd_column = column.copy()
                
                # Optimisations spécifiques au SGBD
                if dbms == "mysql":
                    if mpd_column.get("auto_increment"):
                        mpd_column["type"] = "INT AUTO_INCREMENT"
                    if mpd_column["type"].startswith("VARCHAR") and (mpd_column.get("size") or 255) <= 255:
                        mpd_column["index"] = "BTREE"
                
                elif dbms == "postgresql":
                    if mpd_column.get("auto_increment"):
                        mpd_column["type"] = "SERIAL"
                    if mpd_column["type"].startswith("VARCHAR"):
                        mpd_column["index"] = "BTREE"
                
                elif dbms == "sqlite":
                    if mpd_column.get("auto_increment"):
                        mpd_column["type"] = "INTEGER PRIMARY KEY AUTOINCREMENT"
                
                mpd_table["columns"].append(mpd_column)
            
            # Ajouter des index automatiques
            self._add_automatic_indexes(mpd_table, dbms)
            
            mpd["tables"][table_name] = mpd_table
        
        # Ajouter les clés étrangères du MLD
        mpd["foreign_keys"] = mld["foreign_keys"]
        mpd["constraints"] = mld["constraints"]
        
        return mpd
    
    def _add_automatic_indexes(self, table: Dict, dbms: str) -> None:
        """Ajoute des index automatiques pour optimiser les performances."""
        table_name = table["name"]
        
        # Index sur les clés étrangères
        for column in table["columns"]:
            if column["name"].endswith("_id") and column["name"] != "id":
                index_name = f"idx_{table_name}_{column['name']}"
                table["indexes"].append({
                    "name": index_name,
                    "columns": [column["name"]],
                    "type": "BTREE"
                })
        
        # Index sur les colonnes fréquemment utilisées
        common_search_columns = ["nom", "name", "code", "email", "date_creation", "created_at"]
        for column in table["columns"]:
            if column["name"].lower() in common_search_columns:
                index_name = f"idx_{table_name}_{column['name']}"
                table["indexes"].append({
                    "name": index_name,
                    "columns": [column["name"]],
                    "type": "BTREE"
                })
    
    def generate_sql_from_mpd(self, mpd: Dict) -> str:
        """Génère du SQL optimisé à partir du MPD."""
        if not mpd:
            return ""
            
        sql_script = []
        dbms = mpd.get("dbms", "mysql")
        
        # Créer les tables avec optimisations
        for table_name, table in mpd["tables"].items():
            sql = f"CREATE TABLE {table_name} (\n"
            
            columns = []
            for column in table["columns"]:
                col_def = f"    {column['name']} {column['type']}"
                
                if not column.get("nullable", True):
                    col_def += " NOT NULL"
                if column.get("default") is not None:
                    default_val = column['default']
                    if isinstance(default_val, str) and not default_val.isdigit():
                        default_val = f"'{default_val}'"
                    col_def += f" DEFAULT {default_val}"
                
                columns.append(col_def)
            
            # Clé primaire
            if table["primary_key"]:
                pk_columns = ", ".join(table["primary_key"])
                columns.append(f"    PRIMARY KEY ({pk_columns})")
            
            sql += ",\n".join(columns)
            sql += "\n)"
            
            # Options spécifiques au SGBD
            if dbms == "mysql":
                sql += " ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci"
            elif dbms == "postgresql":
                sql += ""
            elif dbms == "sqlite":
                sql += ""
            
            sql += ";"
            sql_script.append(sql)
        
        # Ajouter les clés étrangères
        for fk in mpd["foreign_keys"]:
            sql = f"ALTER TABLE {fk['table']} ADD CONSTRAINT {fk['constraint_name']} "
            sql += f"FOREIGN KEY ({fk['column']}) REFERENCES {fk['referenced_table']}({fk['referenced_column']});"
            sql_script.append(sql)
        
        # Ajouter les index
        for table_name, table in mpd["tables"].items():
            for index in table["indexes"]:
                sql = f"CREATE INDEX {index['name']} ON {table_name} "
                sql += f"({', '.join(index['columns'])});"
                sql_script.append(sql)
        
        # Ajouter les contraintes d'unicité
        for constraint in mpd["constraints"]:
            if constraint.get("constraint_name"):
                sql = f"ALTER TABLE {constraint['table']} ADD CONSTRAINT {constraint['constraint_name']} "
                sql += f"UNIQUE ({', '.join(constraint['columns'])});"
                sql_script.append(sql)
        
        return "\n\n".join(sql_script)
        
    def _convert_many_to_many(self, relation: Dict, mld: Dict) -> None:
        """Convertit une relation many-to-many."""
        table_name = f"{relation['source']}_{relation['target']}"
        junction_table = {
            "name": table_name,
            "columns": [
                {
                    "name": f"{relation['source']}_id",
                    "type": "INTEGER",
                    "nullable": False
                },
                {
                    "name": f"{relation['target']}_id",
                    "type": "INTEGER",
                    "nullable": False
                }
            ],
            "primary_key": [f"{relation['source']}_id", f"{relation['target']}_id"]
        }
        
        # Ajouter les attributs de la relation
        if "attributes" in relation:
            for attr in relation["attributes"]:
                junction_table["columns"].append({
                    "name": attr["name"],
                    "type": attr["type"],
                    "nullable": True
                })
        
        mld["tables"][table_name] = junction_table
        
        # Ajouter les clés étrangères
        mld["foreign_keys"].extend([
            {
                "table": table_name,
                "column": f"{relation['source']}_id",
                "referenced_table": relation["source"],
                "referenced_column": "id"
            },
            {
                "table": table_name,
                "column": f"{relation['target']}_id",
                "referenced_table": relation["target"],
                "referenced_column": "id"
            }
        ])
        
    def _convert_one_to_many(self, relation: Dict, mld: Dict) -> None:
        """Convertit une relation one-to-many."""
        # Ajouter la clé étrangère à la table "many"
        target_table = mld["tables"][relation["target"]]
        target_table["columns"].append({
            "name": f"{relation['source']}_id",
            "type": "INTEGER",
            "nullable": False
        })
        
        mld["foreign_keys"].append({
            "table": relation["target"],
            "column": f"{relation['source']}_id",
            "referenced_table": relation["source"],
            "referenced_column": "id"
        })
        
    def _convert_one_to_one(self, relation: Dict, mld: Dict) -> None:
        """Convertit une relation one-to-one."""
        # Ajouter la clé étrangère à la table cible avec une contrainte UNIQUE
        target_table = mld["tables"][relation["target"]]
        target_table["columns"].append({
            "name": f"{relation['source']}_id",
            "type": "INTEGER",
            "nullable": False
        })
        
        mld["foreign_keys"].append({
            "table": relation["target"],
            "column": f"{relation['source']}_id",
            "referenced_table": relation["source"],
            "referenced_column": "id"
        })
        
        mld["constraints"].append({
            "table": relation["target"],
            "type": "UNIQUE",
            "columns": [f"{relation['source']}_id"]
        })
        
    def _convert_inheritance(self, relation: Dict, mld: Dict) -> None:
        """Convertit une relation d'héritage."""
        # Copier les colonnes de la classe parente dans la classe enfant
        parent_table = mld["tables"][relation["parent"]]
        child_table = mld["tables"][relation["child"]]
        
        # Ajouter les colonnes de la classe parente
        for column in parent_table["columns"]:
            if column["name"] not in [col["name"] for col in child_table["columns"]]:
                child_table["columns"].append(column.copy())
        
        # Ajouter la clé primaire si elle n'existe pas
        if not child_table["primary_key"]:
            child_table["primary_key"] = parent_table["primary_key"].copy()
        
    def _convert_type_to_uml(self, sql_type: str) -> str:
        """Convertit un type SQL en type UML."""
        type_mapping = {
            "INTEGER": "int",
            "DECIMAL": "float",
            "VARCHAR": "String",
            "TEXT": "String",
            "DATE": "Date",
            "BOOLEAN": "boolean"
        }
        
        base_type = sql_type.split("(")[0].upper()
        return type_mapping.get(base_type, "Object") 