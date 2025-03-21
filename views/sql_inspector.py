from typing import Dict, List, Any, Optional
import sqlparse
from sqlparse.sql import Token, TokenList, Identifier, Function
from sqlparse.tokens import Keyword, Name, Punctuation, String, Number
import re

class SQLInspector:
    """Inspecteur intelligent de schémas SQL"""
    
    def __init__(self):
        self.schema = {
            "tables": {},
            "foreign_keys": [],
            "constraints": []
        }
        
    def analyze_sql(self, sql_script: str) -> Dict:
        """Analyse un script SQL et construit le schéma."""
        # Réinitialiser le schéma
        self.schema = {
            "tables": {},
            "foreign_keys": [],
            "constraints": []
        }
        
        # Parser le script SQL
        statements = sqlparse.parse(sql_script)
        
        # Analyser chaque instruction
        for statement in statements:
            if statement.get_type() == "CREATE":
                self._analyze_create_statement(statement)
            elif statement.get_type() == "ALTER":
                self._analyze_alter_statement(statement)
        
        # Analyser les relations entre tables
        self._analyze_relationships()
        
        return self.schema
        
    def validate_schema(self) -> List[Dict]:
        """Valide le schéma et retourne une liste de problèmes."""
        issues = []
        
        # Vérifier les conventions de nommage
        issues.extend(self._validate_naming_conventions())
        
        # Vérifier les types de données
        issues.extend(self._validate_data_types())
        
        # Vérifier les clés primaires
        issues.extend(self._validate_primary_keys())
        
        # Vérifier les contraintes NULL
        issues.extend(self._validate_null_constraints())
        
        # Vérifier la couverture des index
        issues.extend(self._validate_index_coverage())
        
        return issues
        
    def suggest_optimizations(self) -> List[Dict]:
        """Suggère des optimisations pour le schéma."""
        suggestions = []
        
        # Vérifier les types de données
        for table_name, table in self.schema["tables"].items():
            for column in table["columns"]:
                # Optimiser les VARCHAR
                if isinstance(column["type"], str) and column["type"].startswith("VARCHAR"):
                    size_str = column["type"].replace("VARCHAR(", "").replace(")", "")
                    if size_str and int(size_str) > 255:
                        suggestions.append({
                            "type": "data_type_optimization",
                            "table": table_name,
                            "column": column["name"],
                            "current_type": column["type"],
                            "suggested_type": "TEXT",
                            "reason": "VARCHAR trop grand, TEXT recommandé"
                        })
                
                # Optimiser les nombres
                elif column["type"] == "INTEGER":
                    if any(word in column["name"].lower() for word in ["prix", "montant", "cout", "price", "amount", "cost"]):
                        suggestions.append({
                            "type": "data_type_optimization",
                            "table": table_name,
                            "column": column["name"],
                            "current_type": "INTEGER",
                            "suggested_type": "DECIMAL(10,2)",
                            "reason": "Utiliser DECIMAL pour les montants monétaires"
                        })
        
        # Suggérer des index
        for fk in self.schema["foreign_keys"]:
            if not self._has_index(fk["table"], fk["column"]):
                suggestions.append({
                    "type": "missing_index",
                    "table": fk["table"],
                    "column": fk["column"],
                    "reason": "Clé étrangère sans index"
                })
        
        return suggestions
        
    def _analyze_create_statement(self, statement: TokenList) -> None:
        """Analyse une instruction CREATE TABLE."""
        # Extraire le nom de la table
        table_name = None
        for token in statement.tokens:
            if isinstance(token, Identifier):
                table_name = token.value.strip('"').strip('`')
                break
        
        if not table_name:
            return
        
        table = {
            "name": table_name,
            "columns": [],
            "primary_key": [],
            "indexes": []
        }
        
        # Trouver la définition des colonnes
        columns_def = None
        for token in statement.tokens:
            if token.ttype == Punctuation and token.value == "(":
                columns_def = token.parent
                break
        
        if not columns_def:
            return
        
        # Parser les colonnes et contraintes
        current_column = None
        for token in columns_def.tokens:
            if isinstance(token, Identifier):
                current_column = self._parse_column_definition(token)
                if current_column:
                    table["columns"].append(current_column)
            elif token.ttype == Keyword and token.value.upper() == "PRIMARY KEY":
                pk_cols = self._extract_column_list(columns_def, token)
                table["primary_key"].extend(pk_cols)
            elif token.ttype == Keyword and token.value.upper() == "FOREIGN KEY":
                fk = self._parse_foreign_key(columns_def, token, table_name)
                if fk:
                    self.schema["foreign_keys"].append(fk)
        
        self.schema["tables"][table_name] = table
        
    def _analyze_alter_statement(self, statement: TokenList) -> None:
        """Analyse une instruction ALTER TABLE."""
        # Extraire le nom de la table
        table_name = None
        for token in statement.tokens:
            if token.ttype == Name:
                table_name = token.value.strip('"').strip('`')
                break
        
        if not table_name:
            return
        
        # Analyser les modifications
        for token in statement.tokens:
            if token.ttype == Keyword and token.value.upper() == "ADD":
                if "FOREIGN KEY" in token.parent.value.upper():
                    fk = self._parse_foreign_key(token.parent, token, table_name)
                    if fk:
                        self.schema["foreign_keys"].append(fk)
                elif "CONSTRAINT" in token.parent.value.upper():
                    constraint = self._parse_constraint(token.parent, table_name)
                    if constraint:
                        self.schema["constraints"].append(constraint)
    
    def _analyze_relationships(self) -> None:
        """Analyse les relations entre les tables."""
        for fk in self.schema["foreign_keys"]:
            # Vérifier si la table référencée existe
            if fk["referenced_table"] not in self.schema["tables"]:
                continue
            
            # Détecter le type de relation
            is_one_to_one = self._is_one_to_one(fk)
            if is_one_to_one:
                fk["relationship_type"] = "ONE_TO_ONE"
            else:
                fk["relationship_type"] = "ONE_TO_MANY"
    
    def _parse_column_definition(self, token: Identifier) -> Optional[Dict]:
        """Parse la définition d'une colonne."""
        column = {
            "name": token.get_name(),
            "type": token.get_typecast() or "VARCHAR",
            "nullable": True
        }
        
        # Analyser les contraintes de la colonne
        for constraint in token.tokens:
            if constraint.ttype == Keyword:
                if constraint.value.upper() == "NOT NULL":
                    column["nullable"] = False
                elif constraint.value.upper() == "PRIMARY KEY":
                    column["primary_key"] = True
                elif constraint.value.upper() == "UNIQUE":
                    column["unique"] = True
        
        return column
    
    def _parse_foreign_key(self, token_list: TokenList, start_token: Token, table_name: str) -> Optional[Dict]:
        """Parse une contrainte de clé étrangère."""
        fk = {
            "table": table_name,
            "column": None,
            "referenced_table": None,
            "referenced_column": None
        }
        
        # Trouver les colonnes source et cible
        columns = self._extract_column_list(token_list, start_token)
        if len(columns) >= 2:
            fk["column"] = columns[0]
            fk["referenced_column"] = columns[1]
        
        # Trouver la table référencée
        for token in token_list.tokens:
            if token.ttype == Name and not fk["referenced_table"]:
                fk["referenced_table"] = token.value.strip('"').strip('`')
        
        return fk if all(fk.values()) else None
    
    def _parse_constraint(self, token_list: TokenList, table_name: str) -> Optional[Dict]:
        """Parse une contrainte."""
        constraint = {
            "table": table_name,
            "type": None,
            "columns": []
        }
        
        for token in token_list.tokens:
            if token.ttype == Keyword:
                if token.value.upper() in ["UNIQUE", "CHECK"]:
                    constraint["type"] = token.value.upper()
            elif isinstance(token, Identifier):
                constraint["columns"].append(token.value.strip('"').strip('`'))
        
        return constraint if constraint["type"] and constraint["columns"] else None
    
    def _extract_column_list(self, token_list: TokenList, start_token: Token) -> List[str]:
        """Extrait une liste de colonnes d'une parenthèse."""
        columns = []
        in_parenthesis = False
        
        for token in token_list.tokens:
            if token.ttype == Punctuation:
                if token.value == "(":
                    in_parenthesis = True
                elif token.value == ")":
                    in_parenthesis = False
            elif in_parenthesis and isinstance(token, Identifier):
                columns.append(token.value.strip('"').strip('`'))
        
        return columns
    
    def _is_one_to_one(self, fk: Dict) -> bool:
        """Détermine si une clé étrangère représente une relation one-to-one."""
        # Vérifier si la colonne est UNIQUE
        table = self.schema["tables"].get(fk["table"])
        if not table:
            return False
        
        for constraint in self.schema["constraints"]:
            if (constraint["table"] == fk["table"] and
                constraint["type"] == "UNIQUE" and
                fk["column"] in constraint["columns"]):
                return True
        
        return False
    
    def _has_index(self, table_name: str, column_name: str) -> bool:
        """Vérifie si une colonne a un index."""
        table = self.schema["tables"].get(table_name)
        if not table:
            return False
        
        return any(column_name in index["columns"] for index in table.get("indexes", []))
    
    def _validate_naming_conventions(self) -> List[Dict]:
        """Valide les conventions de nommage."""
        issues = []
        
        # Règles de nommage
        table_pattern = r'^[a-z][a-z0-9_]*$'
        column_pattern = r'^[a-z][a-z0-9_]*$'
        
        for table_name, table in self.schema["tables"].items():
            # Vérifier le nom de la table
            if not re.match(table_pattern, table_name):
                issues.append({
                    "type": "naming_convention",
                    "object_type": "table",
                    "name": table_name,
                    "message": "Le nom de la table doit être en minuscules avec underscores"
                })
            
            # Vérifier les noms des colonnes
            for column in table["columns"]:
                if not re.match(column_pattern, column["name"]):
                    issues.append({
                        "type": "naming_convention",
                        "object_type": "column",
                        "table": table_name,
                        "name": column["name"],
                        "message": "Le nom de la colonne doit être en minuscules avec underscores"
                    })
        
        return issues
    
    def _validate_data_types(self) -> List[Dict]:
        """Valide les types de données."""
        issues = []
        
        for table_name, table in self.schema["tables"].items():
            for column in table["columns"]:
                # Vérifier les VARCHAR sans taille spécifiée
                if column["type"].upper() == "VARCHAR":
                    issues.append({
                        "type": "data_type",
                        "table": table_name,
                        "column": column["name"],
                        "message": "VARCHAR doit avoir une taille spécifiée"
                    })
                
                # Vérifier les types numériques pour les montants
                if (any(word in column["name"].lower() for word in ["prix", "montant", "cout"]) and
                    column["type"].upper() == "INTEGER"):
                    issues.append({
                        "type": "data_type",
                        "table": table_name,
                        "column": column["name"],
                        "message": "Utiliser DECIMAL pour les montants monétaires"
                    })
        
        return issues
    
    def _validate_primary_keys(self) -> List[Dict]:
        """Valide les clés primaires."""
        issues = []
        
        for table_name, table in self.schema["tables"].items():
            if not table["primary_key"]:
                issues.append({
                    "type": "primary_key",
                    "table": table_name,
                    "message": "La table doit avoir une clé primaire"
                })
        
        return issues
    
    def _validate_null_constraints(self) -> List[Dict]:
        """Valide les contraintes NULL."""
        issues = []
        
        for table_name, table in self.schema["tables"].items():
            for column in table["columns"]:
                # Les clés primaires doivent être NOT NULL
                if column["name"] in table["primary_key"] and column.get("nullable", True):
                    issues.append({
                        "type": "null_constraint",
                        "table": table_name,
                        "column": column["name"],
                        "message": "Les colonnes de clé primaire doivent être NOT NULL"
                    })
                
                # Les clés étrangères devraient être NOT NULL
                if any(fk["column"] == column["name"] and fk["table"] == table_name 
                      for fk in self.schema["foreign_keys"]) and column.get("nullable", True):
                    issues.append({
                        "type": "null_constraint",
                        "table": table_name,
                        "column": column["name"],
                        "message": "Les clés étrangères devraient être NOT NULL"
                    })
        
        return issues
    
    def _validate_index_coverage(self) -> List[Dict]:
        """Valide la couverture des index."""
        issues = []
        
        for table_name, table in self.schema["tables"].items():
            # Vérifier les clés étrangères
            for fk in self.schema["foreign_keys"]:
                if fk["table"] == table_name and not self._has_index(table_name, fk["column"]):
                    issues.append({
                        "type": "missing_index",
                        "table": table_name,
                        "column": fk["column"],
                        "message": "Les clés étrangères devraient avoir un index"
                    })
            
            # Vérifier les colonnes fréquemment utilisées dans les filtres
            filter_columns = self._identify_filter_columns(table)
            for column in filter_columns:
                if not self._has_index(table_name, column):
                    issues.append({
                        "type": "missing_index",
                        "table": table_name,
                        "column": column,
                        "message": "Les colonnes fréquemment filtrées devraient avoir un index"
                    })
        
        return issues
    
    def _identify_filter_columns(self, table: Dict) -> List[str]:
        """Identifie les colonnes susceptibles d'être utilisées dans des filtres."""
        filter_columns = []
        
        for column in table["columns"]:
            # Colonnes de statut
            if any(word in column["name"].lower() for word in ["status", "etat", "type", "categorie"]):
                filter_columns.append(column["name"])
            
            # Colonnes de date
            if column["type"].upper() in ["DATE", "TIMESTAMP"]:
                filter_columns.append(column["name"])
            
            # Colonnes booléennes
            if column["type"].upper() == "BOOLEAN":
                filter_columns.append(column["name"])
        
        return filter_columns