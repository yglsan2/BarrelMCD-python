from typing import Dict, List
from enum import Enum

class ConversionType(Enum):
    MCD_TO_UML = "mcd_to_uml"
    MCD_TO_MLD = "mcd_to_mld"
    UML_TO_MLD = "uml_to_mld"
    MLD_TO_SQL = "mld_to_sql"

class ModelConverter:
    """Convertisseur intelligent de modèles de données"""
    
    def __init__(self):
        self.conversion_rules = {
            # Règles de conversion MCD → UML
            "mcd_to_uml": {
                "entity_to_class": self._convert_entity_to_class,
                "relation_to_association": self._convert_relation_to_association,
                "inheritance_to_generalization": self._convert_inheritance_to_generalization
            },
            # Règles de conversion MCD → MLD
            "mcd_to_mld": {
                "one_to_one": self._convert_one_to_one,
                "one_to_many": self._convert_one_to_many,
                "many_to_many": self._convert_many_to_many,
                "inheritance": self._convert_inheritance_mld
            }
        }
        
    def convert_model(self, source_model: Dict, conversion_type: ConversionType) -> Dict:
        """Convertit un modèle vers un autre format."""
        if conversion_type == ConversionType.MCD_TO_UML:
            return self._convert_to_uml(source_model)
        elif conversion_type == ConversionType.MCD_TO_MLD:
            return self._convert_to_mld(source_model)
        elif conversion_type == ConversionType.UML_TO_MLD:
            return self._convert_uml_to_mld(source_model)
        elif conversion_type == ConversionType.MLD_TO_SQL:
            return self._convert_to_sql(source_model)
            
    def _convert_to_uml(self, mcd: Dict) -> Dict:
        """Convertit un MCD en diagramme de classes UML."""
        uml_model = {
            "classes": {},
            "associations": [],
            "generalizations": []
        }
        
        # 1. Convertir les entités en classes
        for entity_name, entity in mcd["entities"].items():
            uml_class = self._convert_entity_to_class(entity)
            uml_model["classes"][entity_name] = uml_class
            
        # 2. Convertir les relations en associations
        for relation in mcd["relations"]:
            if relation["type"] != "INHERITANCE":
                association = self._convert_relation_to_association(relation)
                uml_model["associations"].append(association)
            else:
                generalization = self._convert_inheritance_to_generalization(relation)
                uml_model["generalizations"].append(generalization)
                
        return uml_model
        
    def _convert_to_mld(self, mcd: Dict) -> Dict:
        """Convertit un MCD en Modèle Logique de Données."""
        mld_model = {
            "tables": {},
            "foreign_keys": [],
            "constraints": []
        }
        
        # 1. Créer les tables pour les entités
        for entity_name, entity in mcd["entities"].items():
            table = self._create_table_from_entity(entity)
            mld_model["tables"][entity_name] = table
            
        # 2. Traiter les relations
        for relation in mcd["relations"]:
            if relation["type"] == "ONE_TO_ONE":
                self._convert_one_to_one(relation, mld_model)
            elif relation["type"] == "ONE_TO_MANY":
                self._convert_one_to_many(relation, mld_model)
            elif relation["type"] == "MANY_TO_MANY":
                self._convert_many_to_many(relation, mld_model)
            elif relation["type"] == "INHERITANCE":
                self._convert_inheritance_mld(relation, mld_model)
                
        # 3. Optimiser le modèle
        self._optimize_mld(mld_model)
        
        return mld_model
        
    def _convert_to_sql(self, mld: Dict) -> str:
        """Génère le script SQL à partir du MLD."""
        sql_script = []
        
        # 1. Créer les tables
        for table_name, table in mld["tables"].items():
            sql_script.append(self._generate_create_table(table_name, table))
            
        # 2. Ajouter les clés étrangères
        for fk in mld["foreign_keys"]:
            sql_script.append(self._generate_foreign_key(fk))
            
        # 3. Ajouter les contraintes
        for constraint in mld["constraints"]:
            sql_script.append(self._generate_constraint(constraint))
            
        return "\n\n".join(sql_script)
        
    def _convert_entity_to_class(self, entity: Dict) -> Dict:
        """Convertit une entité MCD en classe UML."""
        uml_class = {
            "name": entity["name"],
            "attributes": [],
            "operations": [],
            "stereotypes": []
        }
        
        # Convertir les attributs
        for attr in entity["attributes"]:
            uml_attr = {
                "name": attr["name"],
                "type": self._convert_type_to_uml(attr["type"]),
                "visibility": "-" if not attr.get("primary_key") else "+"
            }
            uml_class["attributes"].append(uml_attr)
            
        # Ajouter les opérations CRUD par défaut
        crud_operations = [
            {"name": f"create{entity['name']}", "parameters": [], "return_type": entity["name"]},
            {"name": f"read{entity['name']}", "parameters": ["id: int"], "return_type": entity["name"]},
            {"name": f"update{entity['name']}", "parameters": [f"entity: {entity['name']}"], "return_type": "void"},
            {"name": f"delete{entity['name']}", "parameters": ["id: int"], "return_type": "void"}
        ]
        uml_class["operations"].extend(crud_operations)
        
        # Ajouter les stéréotypes
        if entity.get("is_weak"):
            uml_class["stereotypes"].append("weak")
            
        return uml_class
        
    def _convert_relation_to_association(self, relation: Dict) -> Dict:
        """Convertit une relation MCD en association UML."""
        return {
            "name": relation.get("name", ""),
            "source": {
                "class": relation["source"],
                "multiplicity": self._convert_cardinality_to_multiplicity(relation["source_cardinality"]),
                "role": relation.get("source_role", "")
            },
            "target": {
                "class": relation["target"],
                "multiplicity": self._convert_cardinality_to_multiplicity(relation["target_cardinality"]),
                "role": relation.get("target_role", "")
            },
            "attributes": relation.get("attributes", [])
        }
        
    def _convert_inheritance_to_generalization(self, inheritance: Dict) -> Dict:
        """Convertit une relation d'héritage en généralisation UML."""
        return {
            "parent": inheritance["parent"],
            "child": inheritance["child"],
            "type": inheritance.get("type", "complete")  # complete/incomplete, exclusive/overlapping
        }
        
    def _create_table_from_entity(self, entity: Dict) -> Dict:
        """Crée une table MLD à partir d'une entité MCD."""
        table = {
            "name": entity["name"],
            "columns": [],
            "primary_key": [],
            "unique_constraints": [],
            "check_constraints": []
        }
        
        # Convertir les attributs en colonnes
        for attr in entity["attributes"]:
            column = {
                "name": attr["name"],
                "type": self._convert_type_to_sql(attr["type"]),
                "nullable": not attr.get("mandatory", False),
                "unique": attr.get("unique", False)
            }
            table["columns"].append(column)
            
            if attr.get("primary_key"):
                table["primary_key"].append(attr["name"])
                
            if attr.get("unique"):
                table["unique_constraints"].append([attr["name"]])
                
        return table
        
    def _convert_one_to_one(self, relation: Dict, mld: Dict):
        """Convertit une relation 1:1 en MLD."""
        # Déterminer la table qui portera la clé étrangère
        if relation.get("optional_side") == "target":
            source_table = relation["source"]
            target_table = relation["target"]
        else:
            source_table = relation["target"]
            target_table = relation["source"]
            
        # Ajouter la clé étrangère
        fk_name = f"fk_{source_table.lower()}_{target_table.lower()}"
        column_name = f"{target_table.lower()}_id"
        
        mld["tables"][source_table]["columns"].append({
            "name": column_name,
            "type": "INTEGER",
            "nullable": False,
            "unique": True
        })
        
        mld["foreign_keys"].append({
            "name": fk_name,
            "table": source_table,
            "columns": [column_name],
            "referenced_table": target_table,
            "referenced_columns": ["id"],
            "on_delete": "CASCADE",
            "on_update": "CASCADE"
        })
        
    def _convert_one_to_many(self, relation: Dict, mld: Dict):
        """Convertit une relation 1:N en MLD."""
        # La clé étrangère va dans la table côté N
        many_side = relation["source"] if relation["source_cardinality"].endswith("*") else relation["target"]
        one_side = relation["target"] if many_side == relation["source"] else relation["source"]
        
        # Ajouter la clé étrangère
        fk_name = f"fk_{many_side.lower()}_{one_side.lower()}"
        column_name = f"{one_side.lower()}_id"
        
        mld["tables"][many_side]["columns"].append({
            "name": column_name,
            "type": "INTEGER",
            "nullable": not relation.get("mandatory", False)
        })
        
        mld["foreign_keys"].append({
            "name": fk_name,
            "table": many_side,
            "columns": [column_name],
            "referenced_table": one_side,
            "referenced_columns": ["id"],
            "on_delete": "CASCADE",
            "on_update": "CASCADE"
        })
        
    def _convert_many_to_many(self, relation: Dict, mld: Dict):
        """Convertit une relation N:M en MLD."""
        # Créer la table de liaison
        junction_table_name = f"{relation['source'].lower()}_{relation['target'].lower()}"
        
        junction_table = {
            "name": junction_table_name,
            "columns": [
                {
                    "name": f"{relation['source'].lower()}_id",
                    "type": "INTEGER",
                    "nullable": False
                },
                {
                    "name": f"{relation['target'].lower()}_id",
                    "type": "INTEGER",
                    "nullable": False
                }
            ],
            "primary_key": [
                f"{relation['source'].lower()}_id",
                f"{relation['target'].lower()}_id"
            ]
        }
        
        # Ajouter les attributs de la relation s'il y en a
        if relation.get("attributes"):
            for attr in relation["attributes"]:
                junction_table["columns"].append({
                    "name": attr["name"],
                    "type": self._convert_type_to_sql(attr["type"]),
                    "nullable": not attr.get("mandatory", False)
                })
                
        mld["tables"][junction_table_name] = junction_table
        
        # Ajouter les clés étrangères
        mld["foreign_keys"].extend([
            {
                "name": f"fk_{junction_table_name}_{relation['source'].lower()}",
                "table": junction_table_name,
                "columns": [f"{relation['source'].lower()}_id"],
                "referenced_table": relation["source"],
                "referenced_columns": ["id"],
                "on_delete": "CASCADE",
                "on_update": "CASCADE"
            },
            {
                "name": f"fk_{junction_table_name}_{relation['target'].lower()}",
                "table": junction_table_name,
                "columns": [f"{relation['target'].lower()}_id"],
                "referenced_table": relation["target"],
                "referenced_columns": ["id"],
                "on_delete": "CASCADE",
                "on_update": "CASCADE"
            }
        ])
        
    def _convert_inheritance_mld(self, inheritance: Dict, mld: Dict):
        """Convertit une relation d'héritage en MLD."""
        parent = inheritance["parent"]
        child = inheritance["child"]
        strategy = inheritance.get("strategy", "joined")  # joined, single_table, table_per_class
        
        if strategy == "joined":
            # La table enfant contient une clé étrangère vers la table parent
            mld["tables"][child]["columns"].append({
                "name": f"{parent.lower()}_id",
                "type": "INTEGER",
                "nullable": False
            })
            
            mld["foreign_keys"].append({
                "name": f"fk_{child.lower()}_{parent.lower()}",
                "table": child,
                "columns": [f"{parent.lower()}_id"],
                "referenced_table": parent,
                "referenced_columns": ["id"],
                "on_delete": "CASCADE",
                "on_update": "CASCADE"
            })
            
        elif strategy == "single_table":
            # Tous les attributs de l'enfant sont ajoutés à la table parent
            # avec nullable=True
            parent_table = mld["tables"][parent]
            discriminator_column = {
                "name": "type",
                "type": "VARCHAR(50)",
                "nullable": False
            }
            parent_table["columns"].append(discriminator_column)
            
            for column in mld["tables"][child]["columns"]:
                if column["name"] != "id":
                    column["nullable"] = True
                    parent_table["columns"].append(column)
                    
            # Supprimer la table enfant
            del mld["tables"][child]
            
        elif strategy == "table_per_class":
            # La table enfant contient tous les attributs du parent
            child_table = mld["tables"][child]
            parent_table = mld["tables"][parent]
            
            for column in parent_table["columns"]:
                if column["name"] != "id":
                    child_table["columns"].append(column.copy())
                    
    def _optimize_mld(self, mld: Dict):
        """Optimise le modèle logique de données."""
        # 1. Détecter et fusionner les tables similaires
        self._merge_similar_tables(mld)
        
        # 2. Optimiser les clés étrangères
        self._optimize_foreign_keys(mld)
        
        # 3. Ajouter les index appropriés
        self._add_optimal_indexes(mld)
        
    def _merge_similar_tables(self, mld: Dict):
        """Fusionne les tables ayant une structure similaire."""
        tables_to_merge = []
        
        for table1_name, table1 in mld["tables"].items():
            for table2_name, table2 in mld["tables"].items():
                if table1_name >= table2_name:
                    continue
                    
                if self._are_tables_similar(table1, table2):
                    tables_to_merge.append((table1_name, table2_name))
                    
        for table1_name, table2_name in tables_to_merge:
            self._merge_tables(mld, table1_name, table2_name)
            
    def _optimize_foreign_keys(self, mld: Dict):
        """Optimise les clés étrangères du modèle."""
        # 1. Détecter les chaînes de références
        reference_chains = self._find_reference_chains(mld)
        
        # 2. Ajouter des raccourcis pour les chaînes longues
        for chain in reference_chains:
            if len(chain) > 2:
                self._add_shortcut_reference(mld, chain)
                
    def _add_optimal_indexes(self, mld: Dict):
        """Ajoute des index optimaux au modèle."""
        for table_name, table in mld["tables"].items():
            # 1. Index sur les clés étrangères
            for fk in mld["foreign_keys"]:
                if fk["table"] == table_name:
                    table.setdefault("indexes", []).append({
                        "name": f"idx_{fk['name']}",
                        "columns": fk["columns"],
                        "type": "BTREE"
                    })
                    
            # 2. Index sur les colonnes fréquemment recherchées
            for column in table["columns"]:
                if any(pattern in column["name"].lower() 
                      for pattern in ["name", "code", "date", "status"]):
                    table.setdefault("indexes", []).append({
                        "name": f"idx_{table_name}_{column['name']}",
                        "columns": [column["name"]],
                        "type": "BTREE"
                    })
                    
    def _convert_type_to_uml(self, db_type: str) -> str:
        """Convertit un type de base de données en type UML."""
        type_mapping = {
            "integer": "Integer",
            "bigint": "Long",
            "decimal": "Double",
            "varchar": "String",
            "text": "String",
            "date": "Date",
            "datetime": "DateTime",
            "boolean": "Boolean",
            "char": "Character"
        }
        return type_mapping.get(db_type.lower(), "String")
        
    def _convert_type_to_sql(self, db_type: str) -> str:
        """Convertit un type générique en type SQL."""
        type_mapping = {
            "integer": "INTEGER",
            "bigint": "BIGINT",
            "decimal": "DECIMAL(10,2)",
            "varchar": "VARCHAR(255)",
            "text": "TEXT",
            "date": "DATE",
            "datetime": "TIMESTAMP",
            "boolean": "BOOLEAN",
            "char": "CHAR(1)"
        }
        return type_mapping.get(db_type.lower(), "VARCHAR(255)")
        
    def _convert_cardinality_to_multiplicity(self, cardinality: str) -> str:
        """Convertit une cardinalité MCD en multiplicité UML."""
        mapping = {
            "0..1": "0..1",
            "1": "1",
            "0..*": "*",
            "1..*": "1..*",
            "*": "*"
        }
        return mapping.get(cardinality, "*")
        
    def _generate_create_table(self, table_name: str, table: Dict) -> str:
        """Génère la commande CREATE TABLE."""
        columns = []
        for column in table["columns"]:
            col_def = f"{column['name']} {column['type']}"
            if not column.get("nullable", True):
                col_def += " NOT NULL"
            if column.get("unique"):
                col_def += " UNIQUE"
            columns.append(col_def)
            
        if table["primary_key"]:
            columns.append(f"PRIMARY KEY ({', '.join(table['primary_key'])})")
            
        return f"CREATE TABLE {table_name} (\n  " + ",\n  ".join(columns) + "\n);"
        
    def _generate_foreign_key(self, fk: Dict) -> str:
        """Génère une contrainte de clé étrangère."""
        return f"""ALTER TABLE {fk['table']}
ADD CONSTRAINT {fk['name']}
FOREIGN KEY ({', '.join(fk['columns'])})
REFERENCES {fk['referenced_table']} ({', '.join(fk['referenced_columns'])})
ON DELETE {fk.get('on_delete', 'NO ACTION')}
ON UPDATE {fk.get('on_update', 'NO ACTION')};"""
        
    def _generate_constraint(self, constraint: Dict) -> str:
        """Génère une contrainte SQL."""
        if constraint["type"] == "CHECK":
            return f"""ALTER TABLE {constraint['table']}
ADD CONSTRAINT {constraint['name']}
CHECK ({constraint['condition']});"""
        elif constraint["type"] == "UNIQUE":
            return f"""ALTER TABLE {constraint['table']}
ADD CONSTRAINT {constraint['name']}
UNIQUE ({', '.join(constraint['columns'])});"""
        return "" 