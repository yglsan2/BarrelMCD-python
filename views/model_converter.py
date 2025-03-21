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
            class_name = entity_name.capitalize()
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
                parent = relation["parent"].capitalize()
                child = relation["child"].capitalize()
                
                if parent in uml["classes"] and child in uml["classes"]:
                    uml["generalizations"].append({
                        "parent": parent,
                        "child": child
                    })
            else:
                source = relation["source"].capitalize()
                target = relation["target"].capitalize()
                
                if source in uml["classes"] and target in uml["classes"]:
                    uml["associations"].append({
                        "source": source,
                        "target": target,
                        "source_cardinality": relation.get("source_cardinality", "1"),
                        "target_cardinality": relation.get("target_cardinality", "1")
                    })
        
        return uml
        
    def _convert_to_mld(self, mcd: Dict) -> Dict:
        """Convertit un MCD en MLD."""
        mld = {
            "tables": {},
            "foreign_keys": [],
            "constraints": []
        }
        
        # Convertir les entités en tables
        for entity_name, entity in mcd["entities"].items():
            table = {
                "name": entity["name"],
                "columns": [],
                "primary_key": []
            }
            
            # Convertir les attributs en colonnes
            for attr in entity["attributes"]:
                column = {
                    "name": attr["name"],
                    "type": attr["type"],
                    "nullable": True
                }
                if "primary_key" in attr and attr["primary_key"]:
                    column["nullable"] = False
                    table["primary_key"].append(attr["name"])
                table["columns"].append(column)
            
            mld["tables"][entity["name"]] = table
        
        # Traiter les relations
        for relation in mcd["relations"]:
            if relation["type"] == "MANY_TO_MANY":
                self._convert_many_to_many(relation, mld)
            elif relation["type"] == "ONE_TO_MANY":
                self._convert_one_to_many(relation, mld)
            elif relation["type"] == "ONE_TO_ONE":
                self._convert_one_to_one(relation, mld)
            elif relation["type"] == "INHERITANCE":
                self._convert_inheritance(relation, mld)
        
        return mld
        
    def _convert_to_sql(self, mld: Dict) -> str:
        """Convertit un MLD en script SQL."""
        sql_script = []
        
        # Créer les tables
        for table_name, table in mld["tables"].items():
            sql = f"CREATE TABLE {table_name} (\n"
            
            # Colonnes
            columns = []
            for column in table["columns"]:
                col_def = f"    {column['name']} {column['type']}"
                if not column.get("nullable", True):
                    col_def += " NOT NULL"
                columns.append(col_def)
            
            # Clé primaire
            if table["primary_key"]:
                columns.append(f"    PRIMARY KEY ({', '.join(table['primary_key'])})")
            
            sql += ",\n".join(columns)
            sql += "\n);"
            sql_script.append(sql)
        
        # Ajouter les clés étrangères
        for fk in mld["foreign_keys"]:
            sql = f"ALTER TABLE {fk['table']} ADD FOREIGN KEY ({fk['column']}) "
            sql += f"REFERENCES {fk['referenced_table']}({fk['referenced_column']});"
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