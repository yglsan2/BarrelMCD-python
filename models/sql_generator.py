from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
import re
from .data_types import DataType, DataTypeManager

class SQLDialect(Enum):
    MYSQL = "MySQL"
    POSTGRESQL = "PostgreSQL"
    SQLSERVER = "SQL Server"
    ORACLE = "Oracle"
    SQLITE = "SQLite"
    MARIADB = "MariaDB"
    DB2 = "DB2"
    FIREBIRD = "Firebird"
    H2 = "H2"
    HSQLDB = "HSQLDB"
    INFORMIX = "Informix"
    SYBASE = "Sybase"

class SQLStatementType(Enum):
    CREATE_TABLE = "CREATE TABLE"
    ALTER_TABLE = "ALTER TABLE"
    CREATE_INDEX = "CREATE INDEX"
    DROP_INDEX = "DROP INDEX"
    UNKNOWN = "UNKNOWN"

class SQLGenerator:
    def __init__(self):
        self.data_type_manager = DataTypeManager()
        self._load_type_mappings()
        self._load_syntax_mappings()
        
    def _load_type_mappings(self):
        """Charge les mappings de types pour chaque dialecte SQL"""
        self.type_mappings = {
            SQLDialect.MYSQL: {
                "INT": "INT",
                "SMALLINT": "SMALLINT",
                "TINYINT": "TINYINT",
                "BIGINT": "BIGINT",
                "DECIMAL": "DECIMAL",
                "NUMERIC": "DECIMAL",
                "FLOAT": "FLOAT",
                "REAL": "FLOAT",
                "CHAR": "CHAR",
                "VARCHAR": "VARCHAR",
                "TEXT": "TEXT",
                "NCHAR": "CHAR",
                "NVARCHAR": "VARCHAR",
                "NTEXT": "TEXT",
                "DATE": "DATE",
                "DATETIME": "DATETIME",
                "DATETIME2": "DATETIME",
                "SMALLDATETIME": "DATETIME",
                "TIME": "TIME",
                "TIMESTAMP": "TIMESTAMP",
                "BINARY": "BINARY",
                "VARBINARY": "VARBINARY",
                "IMAGE": "LONGBLOB",
                "BIT": "TINYINT(1)",
                "UNIQUEIDENTIFIER": "CHAR(36)"
            },
            SQLDialect.POSTGRESQL: {
                "INT": "INTEGER",
                "SMALLINT": "SMALLINT",
                "TINYINT": "SMALLINT",
                "BIGINT": "BIGINT",
                "DECIMAL": "NUMERIC",
                "NUMERIC": "NUMERIC",
                "FLOAT": "REAL",
                "REAL": "REAL",
                "CHAR": "CHAR",
                "VARCHAR": "VARCHAR",
                "TEXT": "TEXT",
                "NCHAR": "CHAR",
                "NVARCHAR": "VARCHAR",
                "NTEXT": "TEXT",
                "DATE": "DATE",
                "DATETIME": "TIMESTAMP",
                "DATETIME2": "TIMESTAMP",
                "SMALLDATETIME": "TIMESTAMP",
                "TIME": "TIME",
                "TIMESTAMP": "TIMESTAMP",
                "BINARY": "BYTEA",
                "VARBINARY": "BYTEA",
                "IMAGE": "BYTEA",
                "BIT": "BOOLEAN",
                "UNIQUEIDENTIFIER": "UUID"
            },
            SQLDialect.SQLSERVER: {
                "INT": "INT",
                "SMALLINT": "SMALLINT",
                "TINYINT": "TINYINT",
                "BIGINT": "BIGINT",
                "DECIMAL": "DECIMAL",
                "NUMERIC": "NUMERIC",
                "FLOAT": "FLOAT",
                "REAL": "REAL",
                "CHAR": "CHAR",
                "VARCHAR": "VARCHAR",
                "TEXT": "TEXT",
                "NCHAR": "NCHAR",
                "NVARCHAR": "NVARCHAR",
                "NTEXT": "NTEXT",
                "DATE": "DATE",
                "DATETIME": "DATETIME",
                "DATETIME2": "DATETIME2",
                "SMALLDATETIME": "SMALLDATETIME",
                "TIME": "TIME",
                "TIMESTAMP": "ROWVERSION",
                "BINARY": "BINARY",
                "VARBINARY": "VARBINARY",
                "IMAGE": "IMAGE",
                "BIT": "BIT",
                "UNIQUEIDENTIFIER": "UNIQUEIDENTIFIER"
            },
            SQLDialect.ORACLE: {
                "INT": "NUMBER",
                "SMALLINT": "NUMBER",
                "TINYINT": "NUMBER",
                "BIGINT": "NUMBER",
                "DECIMAL": "NUMBER",
                "NUMERIC": "NUMBER",
                "FLOAT": "BINARY_FLOAT",
                "REAL": "BINARY_DOUBLE",
                "CHAR": "CHAR",
                "VARCHAR": "VARCHAR2",
                "TEXT": "CLOB",
                "NCHAR": "NCHAR",
                "NVARCHAR": "NVARCHAR2",
                "NTEXT": "NCLOB",
                "DATE": "DATE",
                "DATETIME": "TIMESTAMP",
                "DATETIME2": "TIMESTAMP",
                "SMALLDATETIME": "TIMESTAMP",
                "TIME": "TIMESTAMP",
                "TIMESTAMP": "TIMESTAMP",
                "BINARY": "RAW",
                "VARBINARY": "RAW",
                "IMAGE": "BLOB",
                "BIT": "NUMBER(1)",
                "UNIQUEIDENTIFIER": "RAW(16)"
            },
            SQLDialect.SQLITE: {
                "INT": "INTEGER",
                "SMALLINT": "INTEGER",
                "TINYINT": "INTEGER",
                "BIGINT": "INTEGER",
                "DECIMAL": "REAL",
                "NUMERIC": "REAL",
                "FLOAT": "REAL",
                "REAL": "REAL",
                "CHAR": "TEXT",
                "VARCHAR": "TEXT",
                "TEXT": "TEXT",
                "NCHAR": "TEXT",
                "NVARCHAR": "TEXT",
                "NTEXT": "TEXT",
                "DATE": "TEXT",
                "DATETIME": "TEXT",
                "DATETIME2": "TEXT",
                "SMALLDATETIME": "TEXT",
                "TIME": "TEXT",
                "TIMESTAMP": "TEXT",
                "BINARY": "BLOB",
                "VARBINARY": "BLOB",
                "IMAGE": "BLOB",
                "BIT": "INTEGER",
                "UNIQUEIDENTIFIER": "TEXT"
            }
        }
        
    def _load_syntax_mappings(self):
        """Charge les mappings de syntaxe pour chaque dialecte SQL"""
        self.syntax_mappings = {
            SQLDialect.MYSQL: {
                "auto_increment": "AUTO_INCREMENT",
                "primary_key": "PRIMARY KEY",
                "foreign_key": "FOREIGN KEY",
                "references": "REFERENCES",
                "on_delete": "ON DELETE",
                "on_update": "ON UPDATE",
                "cascade": "CASCADE",
                "restrict": "RESTRICT",
                "set_null": "SET NULL",
                "no_action": "NO ACTION",
                "default": "DEFAULT",
                "not_null": "NOT NULL",
                "unique": "UNIQUE",
                "index": "INDEX",
                "create_index": "CREATE INDEX {index_name} ON {table_name} ({columns})",
                "drop_index": "DROP INDEX {index_name} ON {table_name}",
                "add_column": "ADD COLUMN {column_def}",
                "modify_column": "MODIFY {column_def}",
                "drop_column": "DROP COLUMN {column_name}",
                "rename_column": "CHANGE {old_name} {new_name} {data_type}",
                "add_constraint": "ADD CONSTRAINT {constraint_name} {constraint_def}",
                "drop_constraint": "DROP CONSTRAINT {constraint_name}"
            },
            SQLDialect.POSTGRESQL: {
                "auto_increment": "SERIAL",
                "primary_key": "PRIMARY KEY",
                "foreign_key": "FOREIGN KEY",
                "references": "REFERENCES",
                "on_delete": "ON DELETE",
                "on_update": "ON UPDATE",
                "cascade": "CASCADE",
                "restrict": "RESTRICT",
                "set_null": "SET NULL",
                "no_action": "NO ACTION",
                "default": "DEFAULT",
                "not_null": "NOT NULL",
                "unique": "UNIQUE",
                "index": "INDEX",
                "create_index": "CREATE INDEX {index_name} ON {table_name} ({columns})",
                "drop_index": "DROP INDEX {index_name}",
                "add_column": "ADD COLUMN {column_def}",
                "modify_column": "ALTER COLUMN {column_name} TYPE {data_type}",
                "drop_column": "DROP COLUMN {column_name}",
                "rename_column": "RENAME COLUMN {old_name} TO {new_name}",
                "add_constraint": "ADD CONSTRAINT {constraint_name} {constraint_def}",
                "drop_constraint": "DROP CONSTRAINT {constraint_name}"
            },
            SQLDialect.SQLSERVER: {
                "auto_increment": "IDENTITY(1,1)",
                "primary_key": "PRIMARY KEY",
                "foreign_key": "FOREIGN KEY",
                "references": "REFERENCES",
                "on_delete": "ON DELETE",
                "on_update": "ON UPDATE",
                "cascade": "CASCADE",
                "restrict": "NO ACTION",
                "set_null": "SET NULL",
                "no_action": "NO ACTION",
                "default": "DEFAULT",
                "not_null": "NOT NULL",
                "unique": "UNIQUE",
                "index": "INDEX",
                "create_index": "CREATE INDEX {index_name} ON {table_name} ({columns})",
                "drop_index": "DROP INDEX {index_name} ON {table_name}",
                "add_column": "ADD {column_def}",
                "modify_column": "ALTER COLUMN {column_def}",
                "drop_column": "DROP COLUMN {column_name}",
                "rename_column": "EXEC sp_rename '{table_name}.{old_name}', '{new_name}', 'COLUMN'",
                "add_constraint": "ADD CONSTRAINT {constraint_name} {constraint_def}",
                "drop_constraint": "DROP CONSTRAINT {constraint_name}"
            },
            SQLDialect.ORACLE: {
                "auto_increment": "GENERATED ALWAYS AS IDENTITY",
                "primary_key": "PRIMARY KEY",
                "foreign_key": "FOREIGN KEY",
                "references": "REFERENCES",
                "on_delete": "ON DELETE",
                "on_update": "ON UPDATE",
                "cascade": "CASCADE",
                "restrict": "NO ACTION",
                "set_null": "SET NULL",
                "no_action": "NO ACTION",
                "default": "DEFAULT",
                "not_null": "NOT NULL",
                "unique": "UNIQUE",
                "index": "INDEX",
                "create_index": "CREATE INDEX {index_name} ON {table_name} ({columns})",
                "drop_index": "DROP INDEX {index_name}",
                "add_column": "ADD {column_def}",
                "modify_column": "MODIFY {column_def}",
                "drop_column": "DROP COLUMN {column_name}",
                "rename_column": "ALTER TABLE {table_name} RENAME COLUMN {old_name} TO {new_name}",
                "add_constraint": "ADD CONSTRAINT {constraint_name} {constraint_def}",
                "drop_constraint": "DROP CONSTRAINT {constraint_name}"
            },
            SQLDialect.SQLITE: {
                "auto_increment": "AUTOINCREMENT",
                "primary_key": "PRIMARY KEY",
                "foreign_key": "FOREIGN KEY",
                "references": "REFERENCES",
                "on_delete": "ON DELETE",
                "on_update": "ON UPDATE",
                "cascade": "CASCADE",
                "restrict": "RESTRICT",
                "set_null": "SET NULL",
                "no_action": "NO ACTION",
                "default": "DEFAULT",
                "not_null": "NOT NULL",
                "unique": "UNIQUE",
                "index": "INDEX",
                "create_index": "CREATE INDEX {index_name} ON {table_name} ({columns})",
                "drop_index": "DROP INDEX {index_name}",
                "add_column": "ADD COLUMN {column_def}",
                "modify_column": "ALTER TABLE {table_name} ALTER COLUMN {column_name} {data_type}",
                "drop_column": "DROP COLUMN {column_name}",
                "rename_column": "ALTER TABLE {table_name} RENAME COLUMN {old_name} TO {new_name}",
                "add_constraint": "ADD CONSTRAINT {constraint_name} {constraint_def}",
                "drop_constraint": "DROP CONSTRAINT {constraint_name}"
            }
        }
        
    def analyze_sql(self, sql: str) -> Tuple[SQLStatementType, Dict[str, Any]]:
        """Analyse le SQL pour déterminer son type et extraire les informations"""
        sql = sql.strip().upper()
        
        # Détermine le type de requête
        if sql.startswith("CREATE TABLE"):
            return SQLStatementType.CREATE_TABLE, self._analyze_create_table(sql)
        elif sql.startswith("ALTER TABLE"):
            return SQLStatementType.ALTER_TABLE, self._analyze_alter_table(sql)
        elif sql.startswith("CREATE INDEX"):
            return SQLStatementType.CREATE_INDEX, self._analyze_create_index(sql)
        elif sql.startswith("DROP INDEX"):
            return SQLStatementType.DROP_INDEX, self._analyze_drop_index(sql)
        else:
            return SQLStatementType.UNKNOWN, {}
            
    def _analyze_create_table(self, sql: str) -> Dict[str, Any]:
        """Analyse une requête CREATE TABLE"""
        result = {
            "table_name": "",
            "columns": []
        }
        
        # Extrait le nom de la table
        match = re.match(r"CREATE TABLE\s+(\w+)", sql)
        if match:
            result["table_name"] = match.group(1)
            
        # Extrait les définitions de colonnes
        columns_match = re.search(r"\((.*)\)", sql, re.DOTALL)
        if columns_match:
            columns_str = columns_match.group(1)
            columns = self._parse_column_definitions(columns_str)
            result["columns"] = columns
            
        return result
        
    def _analyze_alter_table(self, sql: str) -> Dict[str, Any]:
        """Analyse une requête ALTER TABLE"""
        result = {
            "table_name": "",
            "operations": []
        }
        
        # Extrait le nom de la table
        match = re.match(r"ALTER TABLE\s+(\w+)", sql)
        if match:
            result["table_name"] = match.group(1)
            
        # Extrait les opérations
        operations = []
        if "ADD COLUMN" in sql:
            add_match = re.search(r"ADD COLUMN\s+(.*?)(?:,|$)", sql, re.DOTALL)
            if add_match:
                operations.append({
                    "operation": "ADD",
                    "column_def": add_match.group(1).strip()
                })
                
        if "MODIFY" in sql or "ALTER COLUMN" in sql:
            modify_match = re.search(r"(?:MODIFY|ALTER COLUMN)\s+(.*?)(?:,|$)", sql, re.DOTALL)
            if modify_match:
                operations.append({
                    "operation": "MODIFY",
                    "column_def": modify_match.group(1).strip()
                })
                
        if "DROP COLUMN" in sql:
            drop_match = re.search(r"DROP COLUMN\s+(\w+)", sql)
            if drop_match:
                operations.append({
                    "operation": "DROP",
                    "column_name": drop_match.group(1).strip()
                })
                
        result["operations"] = operations
        return result
        
    def _analyze_create_index(self, sql: str) -> Dict[str, Any]:
        """Analyse une requête CREATE INDEX"""
        result = {
            "index_name": "",
            "table_name": "",
            "columns": [],
            "is_unique": False
        }
        
        # Extrait les informations de l'index
        match = re.match(r"CREATE\s+(UNIQUE\s+)?INDEX\s+(\w+)\s+ON\s+(\w+)\s*\((.*)\)", sql)
        if match:
            result["is_unique"] = match.group(1) is not None
            result["index_name"] = match.group(2)
            result["table_name"] = match.group(3)
            result["columns"] = [col.strip() for col in match.group(4).split(",")]
            
        return result
        
    def _analyze_drop_index(self, sql: str) -> Dict[str, Any]:
        """Analyse une requête DROP INDEX"""
        result = {
            "index_name": "",
            "table_name": ""
        }
        
        # Extrait les informations de l'index
        match = re.match(r"DROP INDEX\s+(\w+)(?:\s+ON\s+(\w+))?", sql)
        if match:
            result["index_name"] = match.group(1)
            if match.group(2):
                result["table_name"] = match.group(2)
                
        return result
        
    def _parse_column_definitions(self, columns_str: str) -> List[Dict[str, Any]]:
        """Analyse les définitions de colonnes"""
        columns = []
        
        # Divise les définitions de colonnes
        column_defs = [col.strip() for col in columns_str.split(",")]
        
        for col_def in column_defs:
            if col_def.startswith("PRIMARY KEY") or col_def.startswith("FOREIGN KEY") or col_def.startswith("CONSTRAINT"):
                continue  # Ignore les contraintes de table
                
            # Extrait le nom et le type
            parts = col_def.split()
            if len(parts) >= 2:
                column = {
                    "name": parts[0],
                    "data_type": parts[1],
                    "is_primary_key": False,
                    "is_unique": False,
                    "is_not_null": False,
                    "default_value": None
                }
                
                # Analyse les contraintes
                for i in range(2, len(parts)):
                    if parts[i] == "PRIMARY" and i+1 < len(parts) and parts[i+1] == "KEY":
                        column["is_primary_key"] = True
                    elif parts[i] == "UNIQUE":
                        column["is_unique"] = True
                    elif parts[i] == "NOT" and i+1 < len(parts) and parts[i+1] == "NULL":
                        column["is_not_null"] = True
                    elif parts[i] == "DEFAULT" and i+1 < len(parts):
                        column["default_value"] = parts[i+1]
                        
                columns.append(column)
                
        return columns
        
    def convert_sql(self, sql: str, source_dialect: SQLDialect, target_dialect: SQLDialect) -> str:
        """Convertit le SQL d'un dialecte à un autre"""
        statement_type, info = self.analyze_sql(sql)
        
        if statement_type == SQLStatementType.CREATE_TABLE:
            return self.generate_create_table(
                info["table_name"],
                info["columns"],
                target_dialect
            )
        elif statement_type == SQLStatementType.ALTER_TABLE:
            return self.generate_alter_table(
                info["table_name"],
                info["operations"],
                target_dialect
            )
        elif statement_type == SQLStatementType.CREATE_INDEX:
            return self.generate_create_index(
                info["table_name"],
                info["index_name"],
                info["columns"],
                info["is_unique"],
                target_dialect
            )
        elif statement_type == SQLStatementType.DROP_INDEX:
            return self.generate_drop_index(
                info["table_name"],
                info["index_name"],
                target_dialect
            )
        else:
            # Pour les requêtes non reconnues, tente une conversion simple
            return self._convert_sql_simple(sql, source_dialect, target_dialect)
            
    def _convert_sql_simple(self, sql: str, source_dialect: SQLDialect, target_dialect: SQLDialect) -> str:
        """Convertit le SQL d'un dialecte à un autre de manière simple"""
        converted_sql = sql
        
        # Convertit les types de données
        source_mappings = self.type_mappings.get(source_dialect, {})
        target_mappings = self.type_mappings.get(target_dialect, {})
        
        for source_type, target_type in target_mappings.items():
            if source_type in source_mappings:
                source_type_pattern = source_mappings[source_type]
                if '(' in source_type_pattern:
                    source_type_pattern = source_type_pattern.split('(')[0]
                converted_sql = converted_sql.replace(source_type_pattern, target_type)
                
        # Convertit la syntaxe
        source_syntax = self.syntax_mappings.get(source_dialect, {})
        target_syntax = self.syntax_mappings.get(target_dialect, {})
        
        for key, source_value in source_syntax.items():
            if key in target_syntax:
                target_value = target_syntax[key]
                converted_sql = converted_sql.replace(source_value, target_value)
                
        return converted_sql
        
    def convert_type(self, data_type: str, dialect: SQLDialect) -> str:
        """Convertit un type de données vers le dialecte SQL spécifié"""
        base_type = data_type.split('(')[0].upper()
        params = data_type[data_type.find('(')+1:data_type.find(')')] if '(' in data_type else None
        
        # Récupère le type mappé
        mapped_type = self.type_mappings.get(dialect, {}).get(base_type, base_type)
        
        # Gestion des paramètres spécifiques
        if params and dialect in [SQLDialect.MYSQL, SQLDialect.POSTGRESQL, SQLDialect.SQLSERVER]:
            if base_type in ["DECIMAL", "NUMERIC"]:
                precision, scale = params.split(',')
                return f"{mapped_type}({precision},{scale})"
            elif base_type in ["CHAR", "VARCHAR", "NCHAR", "NVARCHAR", "BINARY", "VARBINARY"]:
                return f"{mapped_type}({params})"
            elif base_type in ["FLOAT", "DATETIME2", "TIME"]:
                return f"{mapped_type}({params})"
                
        return mapped_type
        
    def generate_create_table(self, table_name: str, columns: List[Dict[str, Any]], dialect: SQLDialect) -> str:
        """Génère une requête CREATE TABLE pour le dialecte spécifié"""
        column_defs = []
        
        for column in columns:
            name = column['name']
            data_type = self.convert_type(column['data_type'], dialect)
            constraints = []
            
            if column.get('is_primary_key'):
                if dialect == SQLDialect.MYSQL:
                    constraints.append("PRIMARY KEY")
                else:
                    constraints.append("PRIMARY KEY")
                    
            if column.get('is_unique'):
                constraints.append("UNIQUE")
                
            if column.get('is_not_null'):
                constraints.append("NOT NULL")
                
            if column.get('default_value') is not None:
                default_value = column['default_value']
                if isinstance(default_value, str):
                    default_value = f"'{default_value}'"
                constraints.append(f"DEFAULT {default_value}")
                
            column_def = f"{name} {data_type}"
            if constraints:
                column_def += " " + " ".join(constraints)
                
            column_defs.append(column_def)
            
        # Gestion des clés primaires selon le dialecte
        if dialect == SQLDialect.MYSQL:
            create_sql = f"CREATE TABLE {table_name} (\n  " + ",\n  ".join(column_defs) + "\n);"
        else:
            create_sql = f"CREATE TABLE {table_name} (\n  " + ",\n  ".join(column_defs) + "\n);"
            
        return create_sql
        
    def generate_alter_table(self, table_name: str, alterations: List[Dict[str, Any]], dialect: SQLDialect) -> str:
        """Génère une requête ALTER TABLE pour le dialecte spécifié"""
        alter_statements = []
        
        for alteration in alterations:
            operation = alteration['operation']
            column_name = alteration['column_name']
            
            if operation == 'ADD':
                data_type = self.convert_type(alteration['data_type'], dialect)
                constraints = []
                
                if alteration.get('is_primary_key'):
                    constraints.append("PRIMARY KEY")
                if alteration.get('is_unique'):
                    constraints.append("UNIQUE")
                if alteration.get('is_not_null'):
                    constraints.append("NOT NULL")
                    
                column_def = f"{column_name} {data_type}"
                if constraints:
                    column_def += " " + " ".join(constraints)
                    
                alter_statements.append(f"ADD COLUMN {column_def}")
                
            elif operation == 'MODIFY':
                data_type = self.convert_type(alteration['data_type'], dialect)
                constraints = []
                
                if alteration.get('is_primary_key'):
                    constraints.append("PRIMARY KEY")
                if alteration.get('is_unique'):
                    constraints.append("UNIQUE")
                if alteration.get('is_not_null'):
                    constraints.append("NOT NULL")
                    
                column_def = f"{column_name} {data_type}"
                if constraints:
                    column_def += " " + " ".join(constraints)
                    
                if dialect == SQLDialect.MYSQL:
                    alter_statements.append(f"MODIFY {column_def}")
                elif dialect == SQLDialect.POSTGRESQL:
                    alter_statements.append(f"ALTER COLUMN {column_name} TYPE {data_type}")
                else:
                    alter_statements.append(f"ALTER COLUMN {column_def}")
                    
            elif operation == 'DROP':
                alter_statements.append(f"DROP COLUMN {column_name}")
                
        return f"ALTER TABLE {table_name}\n  " + ",\n  ".join(alter_statements) + ";"
        
    def generate_create_index(self, table_name: str, index_name: str, columns: List[str], 
                            is_unique: bool = False, dialect: SQLDialect = SQLDialect.MYSQL) -> str:
        """Génère une requête CREATE INDEX pour le dialecte spécifié"""
        unique = "UNIQUE " if is_unique else ""
        columns_str = ", ".join(columns)
        
        if dialect == SQLDialect.MYSQL:
            return f"CREATE {unique}INDEX {index_name} ON {table_name} ({columns_str});"
        else:
            return f"CREATE {unique}INDEX {index_name} ON {table_name} ({columns_str});"
            
    def generate_drop_index(self, table_name: str, index_name: str, dialect: SQLDialect = SQLDialect.MYSQL) -> str:
        """Génère une requête DROP INDEX pour le dialecte spécifié"""
        if dialect == SQLDialect.MYSQL:
            return f"DROP INDEX {index_name} ON {table_name};"
        else:
            return f"DROP INDEX {index_name};" 