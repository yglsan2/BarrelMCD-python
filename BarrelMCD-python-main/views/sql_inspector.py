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
        """Analyse un script SQL pour construire un schéma.
        
        Args:
            sql_script: Script SQL à analyser
            
        Returns:
            Dict: Schéma de la base de données
        """
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
            # Nettoyer et normaliser l'instruction
            statement_str = str(statement).strip()
            
            # Analyser CREATE TABLE
            if "CREATE TABLE" in statement_str.upper():
                # Extraire le nom de la table
                match = re.search(r'CREATE\s+TABLE\s+(\w+)', statement_str, re.IGNORECASE)
                if match:
                    table_name = match.group(1).lower()
                    self._analyze_create_table(statement_str, table_name)
            
            # Analyser ALTER TABLE
            elif "ALTER TABLE" in statement_str.upper():
                # Extraire le nom de la table
                match = re.search(r'ALTER\s+TABLE\s+(\w+)', statement_str, re.IGNORECASE)
                if match:
                    table_name = match.group(1).lower()
                    self._analyze_alter_table(statement_str, table_name)
        
        # Analyser les relations
        self._analyze_relationships()
        
        return self.schema
        
    def _is_create_table(self, statement: TokenList) -> bool:
        """Vérifie si l'instruction est un CREATE TABLE."""
        return (len(statement.tokens) >= 2 and
                statement.tokens[0].ttype == Keyword and
                statement.tokens[0].value.upper() == 'CREATE' and
                any(token.value.upper() == 'TABLE' for token in statement.tokens))

    def _is_alter_table(self, statement: TokenList) -> bool:
        """Vérifie si l'instruction est un ALTER TABLE."""
        return (len(statement.tokens) >= 2 and
                statement.tokens[0].ttype == Keyword and
                statement.tokens[0].value.upper() == 'ALTER' and
                any(token.value.upper() == 'TABLE' for token in statement.tokens))

    def _analyze_create_table(self, statement: str, table_name: str) -> None:
        """Analyse une instruction CREATE TABLE.
        
        Args:
            statement: Instruction SQL
            table_name: Nom de la table
        """
        # Extraire le contenu entre parenthèses
        match = re.search(r'CREATE\s+TABLE\s+(\w+)\s*\((.*)\)', statement, re.IGNORECASE | re.DOTALL)
        if not match:
            return
        
        table_name = match.group(1).lower()
        columns_str = match.group(2)
        
        # Initialiser la table
        table = {
            "name": table_name,
            "columns": [],
            "primary_key": []
        }
        
        # Analyser les colonnes et contraintes
        for column_def in self._split_column_definitions(columns_str):
            column_def = column_def.strip()
            
            # Ignorer les lignes vides
            if not column_def:
                continue
            
            # Analyser les contraintes de table
            if column_def.upper().startswith(("PRIMARY KEY", "FOREIGN KEY", "UNIQUE", "CHECK")):
                self._analyze_constraint(table_name, column_def)
                continue
            
            # Analyser la définition de colonne
            column = self._analyze_column_definition(column_def)
            if column:
                table["columns"].append(column)
        
        self.schema["tables"][table_name] = table

    def _analyze_column_definition(self, column_def: str) -> Optional[Dict]:
        """Analyse la définition d'une colonne.
        
        Args:
            column_def: Définition de la colonne
            
        Returns:
            Optional[Dict]: Informations sur la colonne ou None si invalide
        """
        # Pattern pour extraire le nom, type et contraintes
        pattern = r'(\w+)\s+([A-Za-z]+(?:\([^)]+\))?)\s*(.*)'
        match = re.match(pattern, column_def)
        if not match:
            return None
        
        name = match.group(1).lower()
        data_type = match.group(2).upper()
        constraints = match.group(3).upper()
        
        column = {
            "name": name,
            "type": data_type,
            "nullable": "NOT NULL" not in constraints
        }
        
        # Vérifier si c'est une clé primaire
        if "PRIMARY KEY" in constraints:
            column["primary_key"] = True
            
        # Vérifier si c'est unique
        if "UNIQUE" in constraints:
            column["unique"] = True
        
        return column

    def _analyze_foreign_key(self, token_list: TokenList, start_token: Token, table_name: str) -> Optional[Dict]:
        """Analyse une contrainte de clé étrangère."""
        fk = {
            "table": table_name,
            "columns": [],
            "referenced_table": None,
            "referenced_columns": []
        }

        # Trouver les colonnes source et cible
        columns = self._extract_column_list(token_list, start_token)
        if len(columns) >= 2:
            fk["columns"].append(columns[0])
            fk["referenced_columns"].append(columns[1])

        # Trouver la table référencée
        for token in token_list.tokens:
            if token.ttype == Name and not fk["referenced_table"]:
                fk["referenced_table"] = token.value.strip('"').strip('`').lower()

        return fk if all(fk.values()) else None

    def _extract_column_list(self, token_list: TokenList, start_token: Token) -> List[str]:
        """Extrait une liste de colonnes d'une parenthèse."""
        columns = []
        in_parenthesis = False
        
        for token in token_list.tokens:
            if token.ttype == Punctuation:
                if token.value == '(':
                    in_parenthesis = True
                elif token.value == ')':
                    in_parenthesis = False
            elif in_parenthesis and isinstance(token, Identifier):
                columns.append(token.value.strip('"').strip('`').lower())

        return columns

    def _analyze_alter_table(self, statement: str, table_name: str) -> None:
        """Analyse une instruction ALTER TABLE.
        
        Args:
            statement: Instruction SQL
            table_name: Nom de la table
        """
        # Analyser les modifications
        for token in statement.split():
            if token.upper() == 'ADD':
                if 'FOREIGN KEY' in token:
                    fk = self._analyze_foreign_key(token, token, table_name)
                    if fk:
                        self.schema["foreign_keys"].append(fk)
                elif 'CONSTRAINT' in token:
                    constraint = self._analyze_constraint(statement, table_name)
                    if constraint:
                        self.schema["constraints"].append(constraint)

    def _analyze_constraint(self, table_name: str, column_def: str) -> Optional[Dict]:
        """Analyse une contrainte."""
        constraint = {
            "table": table_name,
            "type": None,
            "columns": []
        }

        # Vérifier si la table existe
        if table_name not in self.schema["tables"]:
            self.schema["tables"][table_name] = {
                "name": table_name,
                "columns": [],
                "primary_key": []
            }

        # Analyser les contraintes
        if "FOREIGN KEY" in column_def.upper():
            constraint["type"] = "FOREIGN KEY"
            # Extraire les colonnes de la clé étrangère
            match = re.search(r'FOREIGN\s+KEY\s*\((.*?)\)', column_def)
            if match:
                constraint["columns"] = [col.strip() for col in match.group(1).split(",")]
        elif "PRIMARY KEY" in column_def.upper():
            constraint["type"] = "PRIMARY KEY"
            # Extraire les colonnes de la clé primaire
            match = re.search(r'PRIMARY\s+KEY\s*\((.*?)\)', column_def)
            if match:
                constraint["columns"] = [col.strip() for col in match.group(1).split(",")]
        elif "UNIQUE" in column_def.upper():
            constraint["type"] = "UNIQUE"
            # Extraire les colonnes uniques
            match = re.search(r'UNIQUE\s*\((.*?)\)', column_def)
            if match:
                constraint["columns"] = [col.strip() for col in match.group(1).split(",")]

        return constraint if constraint["type"] and constraint["columns"] else None

    def validate_schema(self) -> List[Dict]:
        """Valide le schéma de la base de données.
        
        Returns:
            List[Dict]: Liste des problèmes trouvés
        """
        issues = []
        
        # Valider les conventions de nommage
        issues.extend(self._validate_naming_conventions())
        
        # Valider les types de données
        issues.extend(self._validate_data_types())
        
        # Valider les contraintes NULL
        issues.extend(self._validate_null_constraints())
        
        # Valider les clés étrangères
        issues.extend(self._validate_foreign_keys())
        
        return issues
    
    def _validate_naming_conventions(self) -> List[Dict]:
        """Valide les conventions de nommage.
        
        Returns:
            List[Dict]: Liste des problèmes trouvés
        """
        issues = []
        
        # Vérifier les noms de tables
        for table_name, table in self.schema["tables"].items():
            if not re.match(r'^[a-z][a-z0-9_]*$', table_name):
                issues.append({
                    "type": "naming_convention",
                    "severity": "warning",
                    "message": f"Le nom de la table '{table_name}' ne suit pas la convention de nommage (lettres minuscules, chiffres et underscores)",
                    "table": table_name
                })
            
            # Vérifier les noms de colonnes
            for column in table["columns"]:
                if not re.match(r'^[a-z][a-z0-9_]*$', column["name"]):
                    issues.append({
                        "type": "naming_convention",
                        "severity": "warning",
                        "message": f"Le nom de la colonne '{column['name']}' ne suit pas la convention de nommage",
                        "table": table_name,
                        "column": column["name"]
                    })
        
        return issues
    
    def _validate_data_types(self) -> List[Dict]:
        """Valide les types de données.
        
        Returns:
            List[Dict]: Liste des problèmes trouvés
        """
        issues = []
        
        for table_name, table in self.schema["tables"].items():
            for column in table["columns"]:
                # Vérifier les VARCHAR sans taille
                if column["type"].upper().startswith("VARCHAR") and "(" not in column["type"]:
                    issues.append({
                        "type": "data_type",
                        "severity": "warning",
                        "message": "VARCHAR sans taille spécifiée",
                        "table": table_name,
                        "column": column["name"]
                    })
                
                # Vérifier les montants en INTEGER
                if column["type"].upper() == "INTEGER" and any(word in column["name"].lower() for word in ["prix", "montant", "cout", "cost", "amount"]):
                    issues.append({
                        "type": "data_type",
                        "severity": "warning",
                        "message": "Utilisation de INTEGER pour un montant, préférer DECIMAL",
                        "table": table_name,
                        "column": column["name"]
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
                if any(fk["columns"][0] == column["name"] and fk["table"] == table_name 
                      for fk in self.schema["foreign_keys"]) and column.get("nullable", True):
                    issues.append({
                        "type": "null_constraint",
                        "table": table_name,
                        "column": column["name"],
                        "message": "Les clés étrangères devraient être NOT NULL"
                    })
        
        return issues

    def _validate_foreign_keys(self) -> List[Dict]:
        """Valide les clés étrangères."""
        issues = []
        
        for fk in self.schema["foreign_keys"]:
            if fk["table"] == fk["referenced_table"]:
                issues.append({
                    "type": "recursive_foreign_key",
                    "severity": "warning",
                    "message": f"La clé étrangère {fk['columns'][0]} vers {fk['referenced_table']} est récursive",
                    "table": fk["table"],
                    "column": fk["columns"][0]
                })
        
        return issues

    def suggest_optimizations(self) -> List[Dict]:
        """Suggère des optimisations pour le schéma.
        
        Returns:
            List[Dict]: Liste des suggestions d'optimisation
        """
        suggestions = []
        
        # Vérifier les index manquants sur les clés étrangères
        for fk in self.schema["foreign_keys"]:
            table_name = fk["table"]
            column_name = fk["columns"][0]
            
            # Vérifier si un index existe déjà
            has_index = False
            for constraint in self.schema["constraints"]:
                if (constraint["type"] == "index" and 
                    constraint["table"] == table_name and 
                    column_name in constraint["columns"]):
                    has_index = True
                    break
            
            if not has_index:
                suggestions.append({
                    "type": "missing_index",
                    "severity": "warning",
                    "message": f"Index manquant sur la clé étrangère {column_name}",
                    "table": table_name,
                    "column": column_name,
                    "sql": f"CREATE INDEX idx_{table_name}_{column_name} ON {table_name}({column_name});"
                })
        
        # Vérifier les colonnes fréquemment utilisées pour le filtrage
        filter_columns = ["status", "type", "category", "date", "active", "enabled"]
        for table_name, table in self.schema["tables"].items():
            for column in table["columns"]:
                if column["name"].lower() in filter_columns:
                    # Vérifier si un index existe déjà
                    has_index = False
                    for constraint in self.schema["constraints"]:
                        if (constraint["type"] == "index" and 
                            constraint["table"] == table_name and 
                            column["name"] in constraint["columns"]):
                            has_index = True
                            break
                    
                    if not has_index:
                        suggestions.append({
                            "type": "missing_index",
                            "severity": "info",
                            "message": f"Index suggéré sur la colonne de filtrage {column['name']}",
                            "table": table_name,
                            "column": column["name"],
                            "sql": f"CREATE INDEX idx_{table_name}_{column['name']} ON {table_name}({column['name']});"
                        })
        
        # Vérifier les types de données inefficaces
        for table_name, table in self.schema["tables"].items():
            for column in table["columns"]:
                # Vérifier les VARCHAR trop grands
                if column["type"].upper().startswith("VARCHAR"):
                    size_match = re.search(r'VARCHAR\((\d+)\)', column["type"].upper())
                    if size_match:
                        size = int(size_match.group(1))
                        if size > 1000:
                            suggestions.append({
                                "type": "data_type_optimization",
                                "severity": "warning",
                                "message": f"VARCHAR({size}) trop grand, considérer TEXT",
                                "table": table_name,
                                "column": column["name"],
                                "sql": f"ALTER TABLE {table_name} ALTER COLUMN {column['name']} TYPE TEXT;"
                            })
                
                # Vérifier les INTEGER pour les petits nombres
                if column["type"].upper() == "INTEGER":
                    if any(word in column["name"].lower() for word in ["status", "type", "code", "flag"]):
                        suggestions.append({
                            "type": "data_type_optimization",
                            "severity": "info",
                            "message": "INTEGER trop grand pour un code/status, considérer SMALLINT ou TINYINT",
                            "table": table_name,
                            "column": column["name"],
                            "sql": f"ALTER TABLE {table_name} ALTER COLUMN {column['name']} TYPE SMALLINT;"
                        })
        
        return suggestions

    def _analyze_relationships(self) -> None:
        """Analyse les relations entre les tables."""
        # Initialiser les hiérarchies
        self.schema["hierarchies"] = []
        
        # Détecter les relations récursives (hiérarchies)
        for fk in self.schema["foreign_keys"]:
            if fk["table"] == fk["referenced_table"]:
                hierarchy = {
                    "type": "recursive",
                    "table": fk["table"],
                    "parent_column": fk["referenced_columns"][0],
                    "child_column": fk["columns"][0]
                }
                self.schema["hierarchies"].append(hierarchy)
        
        # Détecter les relations d'héritage
        for table_name, table in self.schema["tables"].items():
            # Chercher les colonnes qui pourraient indiquer un type
            type_columns = [col for col in table["columns"] 
                          if col["name"] in ["type", "discriminator", "entity_type"]]
            
            if type_columns:
                hierarchy = {
                    "type": "inheritance",
                    "table": table_name,
                    "discriminator": type_columns[0]["name"]
                }
                self.schema["hierarchies"].append(hierarchy)
        
        # Détecter les relations many-to-many
        for table_name, table in self.schema["tables"].items():
            # Vérifier si c'est une table de jointure
            if len(table["columns"]) <= 4:  # ID + 2 FKs + éventuellement une date
                fk_count = sum(1 for fk in self.schema["foreign_keys"] 
                             if fk["table"] == table_name)
                if fk_count == 2:
                    # C'est probablement une table de jointure
                    related_tables = []
                    for fk in self.schema["foreign_keys"]:
                        if fk["table"] == table_name:
                            related_tables.append(fk["referenced_table"])
                    
                    if len(related_tables) == 2:
                        relationship = {
                            "type": "many_to_many",
                            "junction_table": table_name,
                            "tables": related_tables
                        }
                        if "relationships" not in self.schema:
                            self.schema["relationships"] = []
                        self.schema["relationships"].append(relationship)

    def _split_column_definitions(self, columns_str: str) -> List[str]:
        """Divise la chaîne de définitions de colonnes en une liste.
        
        Args:
            columns_str: Chaîne contenant les définitions de colonnes
            
        Returns:
            List[str]: Liste des définitions de colonnes
        """
        # Supprimer les espaces superflus
        columns_str = re.sub(r'\s+', ' ', columns_str.strip())
        
        # Diviser sur les virgules, en respectant les parenthèses
        columns = []
        current = ""
        paren_count = 0
        
        for char in columns_str:
            if char == ',' and paren_count == 0:
                columns.append(current.strip())
                current = ""
            else:
                if char == '(':
                    paren_count += 1
                elif char == ')':
                    paren_count -= 1
                current += char
        
        if current.strip():
            columns.append(current.strip())
        
        return columns