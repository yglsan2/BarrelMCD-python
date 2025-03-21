from typing import Dict, List, Any, Optional
from enum import Enum

class ConversionType(Enum):
    MCD_TO_UML = "mcd_to_uml"
    MCD_TO_MLD = "mcd_to_mld"
    MLD_TO_SQL = "mld_to_sql"

class ModelConverter:
    """Convertisseur intelligent de modèles de données"""
    
    def __init__(self):
        """Initialise le convertisseur de modèles."""
        pass

    def convert_model(self, model: Dict, conversion_type: ConversionType) -> Dict:
        """Convertit un modèle d'un format à un autre.
        
        Args:
            model: Modèle à convertir
            conversion_type: Type de conversion
            
        Returns:
            Dict: Modèle converti
        """
        if conversion_type == ConversionType.MCD_TO_UML:
            return self.convert_to_uml(model)
        elif conversion_type == ConversionType.MCD_TO_MLD:
            return self._convert_to_mld(model)
        elif conversion_type == ConversionType.MCD_TO_SQL:
            return self._convert_to_sql(model)
        else:
            raise ValueError(f"Type de conversion non supporté: {conversion_type}")
        
    def convert_to_uml(self, model: Dict) -> Dict:
        """Convertit un modèle MCD en UML.
        
        Args:
            model: Modèle MCD à convertir
            
        Returns:
            Dict: Modèle UML avec classes, associations et généralisations
        """
        uml = {
            "classes": {},
            "associations": [],
            "generalizations": []
        }
        
        # Convertir les entités en classes
        for entity_name, entity in model["entities"].items():
            uml["classes"][entity_name] = {
                "name": entity_name,
                "attributes": [],
                "methods": []
            }
            
            # Convertir les attributs
            for attr in entity["attributes"]:
                visibility = "+" if attr.get("primary_key", False) else "-"
                uml["classes"][entity_name]["attributes"].append({
                    "name": attr["name"],
                    "type": self._convert_type_to_uml(attr["type"]),
                    "visibility": visibility
                })
        
        # Convertir les relations en associations
        for relation in model.get("relations", []):
            source = relation["source"]
            target = relation["target"]
            
            # Vérifier que les classes existent
            if source in uml["classes"] and target in uml["classes"]:
                # Créer l'association
                association = {
                    "source": source,
                    "target": target,
                    "source_multiplicity": relation.get("source_cardinality", "1"),
                    "target_multiplicity": relation.get("target_cardinality", "1")
                }
                
                # Ajouter le nom de la relation si présent
                if "name" in relation:
                    association["name"] = relation["name"]
                
                uml["associations"].append(association)
        
        # Convertir les hiérarchies en généralisations
        for hierarchy in model.get("hierarchies", []):
            parent = hierarchy["parent"]
            child = hierarchy["child"]
            
            # Vérifier que les classes existent
            if parent in uml["classes"] and child in uml["classes"]:
                uml["generalizations"].append({
                    "parent": parent,
                    "child": child
                })
        
        return uml
        
    def _convert_to_mld(self, model: Dict) -> Dict:
        """Convertit un modèle MCD en MLD.
        
        Args:
            model: Modèle MCD à convertir
            
        Returns:
            Dict: Modèle MLD
        """
        mld = {
            "tables": {}
        }
        
        # Convertir les entités en tables
        for entity_name, entity in model["entities"].items():
            mld["tables"][entity_name] = {
                "name": entity_name,
                "columns": [],
                "primary_key": entity.get("primary_key", []),
                "foreign_keys": []
            }
            
            # Convertir les attributs en colonnes
            for attr in entity["attributes"]:
                column = {
                    "name": attr["name"],
                    "type": attr["type"],
                    "nullable": not attr.get("primary_key", False)
                }
                mld["tables"][entity_name]["columns"].append(column)
        
        # Traiter les relations
        for relation in model.get("relations", []):
            source = relation["source"]
            target = relation["target"]
            
            if relation["type"] == "ONE_TO_MANY":
                # Ajouter la clé étrangère dans la table "many"
                fk_name = f"{source}_id"
                mld["tables"][target]["columns"].append({
                    "name": fk_name,
                    "type": "INTEGER",
                    "nullable": False
                })
                mld["tables"][target]["foreign_keys"].append({
                    "column": fk_name,
                    "references": {
                        "table": source,
                        "column": "id"
                    }
                })
            elif relation["type"] == "MANY_TO_MANY":
                # Créer une table de liaison
                table_name = f"{source}_{target}"
                mld["tables"][table_name] = {
                    "name": table_name,
                    "columns": [
                        {
                            "name": f"{source}_id",
                            "type": "INTEGER",
                            "nullable": False
                        },
                        {
                            "name": f"{target}_id",
                            "type": "INTEGER",
                            "nullable": False
                        }
                    ],
                    "primary_key": [f"{source}_id", f"{target}_id"],
                    "foreign_keys": [
                        {
                            "column": f"{source}_id",
                            "references": {
                                "table": source,
                                "column": "id"
                            }
                        },
                        {
                            "column": f"{target}_id",
                            "references": {
                                "table": target,
                                "column": "id"
                            }
                        }
                    ]
                }
        
        return mld
        
    def _convert_to_sql(self, model: Dict) -> Dict:
        """Convertit un modèle MCD en SQL.
        
        Args:
            model: Modèle MCD à convertir
            
        Returns:
            Dict: Schéma SQL
        """
        sql = {
            "tables": {},
            "foreign_keys": [],
            "constraints": [],
            "relationships": [],
            "hierarchies": []
        }
        
        # Convertir les entités en tables
        for entity_name, entity in model["entities"].items():
            sql["tables"][entity_name] = {
                "name": entity_name,
                "columns": [],
                "primary_key": entity.get("primary_key", [])
            }
            
            # Convertir les attributs en colonnes
            for attr in entity["attributes"]:
                column = {
                    "name": attr["name"],
                    "type": self._convert_type_to_sql(attr["type"]),
                    "constraints": []
                }
                
                # Ajouter les contraintes
                if attr.get("primary_key", False):
                    column["constraints"].append("PRIMARY KEY")
                if not attr.get("nullable", True):
                    column["constraints"].append("NOT NULL")
                if attr.get("unique", False):
                    column["constraints"].append("UNIQUE")
                
                sql["tables"][entity_name]["columns"].append(column)
        
        # Traiter les relations
        for relation in model.get("relations", []):
            source = relation["source"]
            target = relation["target"]
            
            if relation["type"] == "ONE_TO_MANY":
                # Ajouter la clé étrangère
                sql["foreign_keys"].append({
                    "table": target,
                    "column": f"{source}_id",
                    "references": {
                        "table": source,
                        "column": "id"
                    }
                })
                
                # Ajouter la relation
                sql["relationships"].append({
                    "type": "one_to_many",
                    "source": source,
                    "target": target,
                    "source_multiplicity": "1",
                    "target_multiplicity": "*"
                })
            elif relation["type"] == "MANY_TO_MANY":
                # Créer une table de liaison
                table_name = f"{source}_{target}"
                sql["tables"][table_name] = {
                    "name": table_name,
                    "columns": [
                        {
                            "name": f"{source}_id",
                            "type": "INTEGER",
                            "constraints": ["NOT NULL"]
                        },
                        {
                            "name": f"{target}_id",
                            "type": "INTEGER",
                            "constraints": ["NOT NULL"]
                        }
                    ],
                    "primary_key": [f"{source}_id", f"{target}_id"]
                }
                
                # Ajouter les clés étrangères
                sql["foreign_keys"].extend([
                    {
                        "table": table_name,
                        "column": f"{source}_id",
                        "references": {
                            "table": source,
                            "column": "id"
                        }
                    },
                    {
                        "table": table_name,
                        "column": f"{target}_id",
                        "references": {
                            "table": target,
                            "column": "id"
                        }
                    }
                ])
                
                # Ajouter la relation
                sql["relationships"].append({
                    "type": "many_to_many",
                    "junction_table": table_name,
                    "tables": [source, target]
                })
            elif relation["type"] == "INHERITANCE":
                # Ajouter la hiérarchie
                sql["hierarchies"].append({
                    "type": "inheritance",
                    "parent": source,
                    "child": target
                })
        
        return sql

    def _convert_type_to_sql(self, type_str: str) -> str:
        """Convertit un type de données en type SQL avec tailles par défaut et valeurs personnalisées.
        
        Args:
            type_str: Type de données à convertir
            
        Returns:
            str: Type SQL avec tailles et valeurs personnalisées
        """
        type_str = type_str.upper()
        
        # Types numériques
        if type_str in ["INTEGER", "INT"]:
            return "INTEGER"
        elif type_str in ["DECIMAL", "NUMERIC"]:
            return "DECIMAL(10,2)"
        elif type_str == "FLOAT":
            return "REAL"
        
        # Types textuels avec tailles par défaut
        elif type_str == "STRING":
            return "VARCHAR(255)"
        elif type_str == "TEXT":
            return "TEXT"
        
        # Types temporels
        elif type_str == "DATE":
            return "DATE"
        elif type_str == "DATETIME":
            return "TIMESTAMP"
        
        # Types booléens avec valeurs personnalisées
        elif type_str == "BOOLEAN":
            return "BOOLEAN DEFAULT 'OUI' CHECK (value IN ('OUI', 'NON'))"
        
        # Types énumérés personnalisés
        elif type_str.startswith("ENUM"):
            # Format attendu: ENUM('val1', 'val2', ...)
            return type_str
        
        # Types avec taille spécifique
        elif type_str.startswith("VARCHAR") and "(" in type_str:
            return type_str
        elif type_str.startswith("CHAR") and "(" in type_str:
            return type_str
        
        # Par défaut
        return type_str

    def _convert_type_to_uml(self, sql_type: str) -> str:
        """Convertit un type SQL en type UML.
        
        Args:
            sql_type: Type SQL à convertir
            
        Returns:
            str: Type UML correspondant
        """
        sql_type = sql_type.upper()
        
        # Types numériques
        if sql_type in ["INTEGER", "BIGINT", "SMALLINT", "TINYINT"]:
            return "Integer"
        elif sql_type in ["DECIMAL", "NUMERIC", "FLOAT", "REAL"]:
            return "Double"
            
        # Types textuels
        elif sql_type in ["VARCHAR", "CHAR", "TEXT"]:
            return "String"
            
        # Types booléens
        elif sql_type in ["BOOLEAN", "BIT"]:
            return "Boolean"
            
        # Types date/heure
        elif sql_type in ["DATE", "DATETIME", "TIMESTAMP"]:
            return "DateTime"
            
        # Types binaires
        elif sql_type in ["BLOB", "BINARY", "VARBINARY"]:
            return "Byte[]"
            
        # Par défaut
        return "Object" 