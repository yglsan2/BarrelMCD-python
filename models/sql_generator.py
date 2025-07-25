from typing import List, Dict, Any, Optional
from enum import Enum
import re
from .data_types import DataTypeManager

class SQLDialect(Enum):
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    SQLITE = "sqlite"
    ORACLE = "oracle"
    SQLSERVER = "sqlserver"
    DB2 = "db2"
    FIREBIRD = "firebird"
    H2 = "h2"
    HSQLDB = "hsqldb"
    INFORMIX = "informix"
    SYBASE = "sybase"
    TERADATA = "teradata"
    VERTICA = "vertica"

class SQLGenerator:
    def __init__(self, dialect: SQLDialect = SQLDialect.POSTGRESQL):
        self.dialect = dialect
        self.data_type_manager = DataTypeManager()
        self.supported_dialects = {
            SQLDialect.POSTGRESQL: self._generate_postgresql,
            SQLDialect.MYSQL: self._generate_mysql,
            SQLDialect.SQLITE: self._generate_sqlite,
            SQLDialect.ORACLE: self._generate_oracle,
            SQLDialect.SQLSERVER: self._generate_sqlserver,
            SQLDialect.DB2: self._generate_db2,
            SQLDialect.FIREBIRD: self._generate_firebird,
            SQLDialect.H2: self._generate_h2,
            SQLDialect.HSQLDB: self._generate_hsqldb,
            SQLDialect.INFORMIX: self._generate_informix,
            SQLDialect.SYBASE: self._generate_sybase,
            SQLDialect.TERADATA: self._generate_teradata,
            SQLDialect.VERTICA: self._generate_vertica
        }
        
    @staticmethod
    def get_supported_sql_dialects() -> List[str]:
        return [dialect.value for dialect in SQLDialect]
        
    def generate_sql(self, entities: List[Dict[str, Any]], associations: List[Dict[str, Any]]) -> str:
        if self.dialect not in self.supported_dialects:
            raise ValueError(f"Dialecte SQL non supporté : {self.dialect}")
            
        return self.supported_dialects[self.dialect](entities, associations)
        
    def _generate_postgresql(self, entities: List[Dict[str, Any]], associations: List[Dict[str, Any]]) -> str:
        sql = []
        
        # Génération des tables d'entités
        for entity in entities:
            sql.append(self._generate_table_postgresql(entity))
            
        # Génération des tables d'association
        for association in associations:
            sql.append(self._generate_association_table_postgresql(association))
            
        # Génération des contraintes de clés étrangères
        for association in associations:
            sql.extend(self._generate_foreign_keys_postgresql(association))
            
        return "\n\n".join(sql)
        
    def _generate_table_postgresql(self, entity: Dict[str, Any]) -> str:
        table_name = self._sanitize_name(entity["name"])
        columns = []
        
        for attr in entity["attributes"]:
            columns.append(self._generate_column_postgresql(attr))
            
        # Ajout des contraintes de clé primaire
        pk_columns = [attr["name"] for attr in entity["attributes"] if attr.get("is_primary", False)]
        if pk_columns:
            columns.append(f"PRIMARY KEY ({', '.join(pk_columns)})")
            
        # Ajout des contraintes UNIQUE
        unique_columns = [attr["name"] for attr in entity["attributes"] if attr.get("is_unique", False)]
        for col in unique_columns:
            columns.append(f"UNIQUE ({col})")
            
        return f"""CREATE TABLE {table_name} (
    {',\n    '.join(columns)}
);"""
        
    def _generate_column_postgresql(self, attribute: Dict[str, Any]) -> str:
        name = self._sanitize_name(attribute["name"])
        type_ = self._map_data_type(attribute["type"], SQLDialect.POSTGRESQL)
        constraints = []
        
        if attribute.get("is_primary", False):
            constraints.append("PRIMARY KEY")
        if attribute.get("is_unique", False):
            constraints.append("UNIQUE")
        if attribute.get("is_not_null", True):
            constraints.append("NOT NULL")
            
        if "default" in attribute:
            constraints.append(f"DEFAULT {attribute['default']}")
            
        return f"{name} {type_} {' '.join(constraints)}"
        
    def _generate_association_table_postgresql(self, association: Dict[str, Any]) -> str:
        table_name = self._sanitize_name(association["name"])
        columns = []
        
        # Ajout des clés étrangères
        for entity in association["entities"]:
            entity_name = self._sanitize_name(entity["name"])
            columns.append(f"{entity_name}_id INTEGER NOT NULL")
            
        # Ajout des attributs de l'association
        for attr in association["attributes"]:
            columns.append(self._generate_column_postgresql(attr))
            
        # Clé primaire composite
        pk_columns = [f"{entity['name']}_id" for entity in association["entities"]]
        columns.append(f"PRIMARY KEY ({', '.join(pk_columns)})")
        
        return f"""CREATE TABLE {table_name} (
    {',\n    '.join(columns)}
);"""
        
    def _generate_foreign_keys_postgresql(self, association: Dict[str, Any]) -> List[str]:
        table_name = self._sanitize_name(association["name"])
        fk_statements = []
        
        for entity in association["entities"]:
            entity_name = self._sanitize_name(entity["name"])
            fk_statements.append(f"""ALTER TABLE {table_name}
    ADD CONSTRAINT fk_{table_name}_{entity_name}
    FOREIGN KEY ({entity_name}_id)
    REFERENCES {entity_name}(id)
    ON DELETE {entity.get('on_delete', 'CASCADE')}
    ON UPDATE {entity.get('on_update', 'CASCADE')};""")
            
        return fk_statements
        
    def _map_data_type(self, type_: str, dialect: SQLDialect) -> str:
        type_mapping = {
            SQLDialect.POSTGRESQL: {
                "INTEGER": "INTEGER",
                "VARCHAR": "VARCHAR",
                "TEXT": "TEXT",
                "BOOLEAN": "BOOLEAN",
                "DATE": "DATE",
                "TIME": "TIME",
                "TIMESTAMP": "TIMESTAMP",
                "DECIMAL": "DECIMAL",
                "FLOAT": "REAL",
                "DOUBLE": "DOUBLE PRECISION",
                "BLOB": "BYTEA",
                "JSON": "JSONB",
                "UUID": "UUID",
                "ENUM": "ENUM"
            },
            SQLDialect.MYSQL: {
                "INTEGER": "INT",
                "VARCHAR": "VARCHAR",
                "TEXT": "TEXT",
                "BOOLEAN": "BOOLEAN",
                "DATE": "DATE",
                "TIME": "TIME",
                "TIMESTAMP": "TIMESTAMP",
                "DECIMAL": "DECIMAL",
                "FLOAT": "FLOAT",
                "DOUBLE": "DOUBLE",
                "BLOB": "BLOB",
                "JSON": "JSON",
                "UUID": "CHAR(36)",
                "ENUM": "ENUM"
            },
            # Ajouter les mappings pour les autres dialectes...
        }
        
        base_type = type_.split("(")[0].upper()
        if dialect in type_mapping and base_type in type_mapping[dialect]:
            return type_mapping[dialect][base_type]
        return type_
        
    def _sanitize_name(self, name: str) -> str:
        # Nettoyer le nom pour le SQL
        name = name.lower()
        name = name.replace(" ", "_")
        name = "".join(c for c in name if c.isalnum() or c == "_")
        return name
        
    # Implémenter les méthodes de génération pour les autres dialectes...
    def _generate_mysql(self, entities: List[Dict[str, Any]], associations: List[Dict[str, Any]]) -> str:
        # TODO: Implémenter la génération MySQL
        pass
        
    def _generate_sqlite(self, entities: List[Dict[str, Any]], associations: List[Dict[str, Any]]) -> str:
        # TODO: Implémenter la génération SQLite
        pass
        
    def _generate_oracle(self, entities: List[Dict[str, Any]], associations: List[Dict[str, Any]]) -> str:
        # TODO: Implémenter la génération Oracle
        pass
        
    def _generate_sqlserver(self, entities: List[Dict[str, Any]], associations: List[Dict[str, Any]]) -> str:
        # TODO: Implémenter la génération SQL Server
        pass
        
    def _generate_db2(self, entities: List[Dict[str, Any]], associations: List[Dict[str, Any]]) -> str:
        # TODO: Implémenter la génération DB2
        pass
        
    def _generate_firebird(self, entities: List[Dict[str, Any]], associations: List[Dict[str, Any]]) -> str:
        # TODO: Implémenter la génération Firebird
        pass
        
    def _generate_h2(self, entities: List[Dict[str, Any]], associations: List[Dict[str, Any]]) -> str:
        # TODO: Implémenter la génération H2
        pass
        
    def _generate_hsqldb(self, entities: List[Dict[str, Any]], associations: List[Dict[str, Any]]) -> str:
        # TODO: Implémenter la génération HSQLDB
        pass
        
    def _generate_informix(self, entities: List[Dict[str, Any]], associations: List[Dict[str, Any]]) -> str:
        # TODO: Implémenter la génération Informix
        pass
        
    def _generate_sybase(self, entities: List[Dict[str, Any]], associations: List[Dict[str, Any]]) -> str:
        # TODO: Implémenter la génération Sybase
        pass
        
    def _generate_teradata(self, entities: List[Dict[str, Any]], associations: List[Dict[str, Any]]) -> str:
        # TODO: Implémenter la génération Teradata
        pass
        
    def _generate_vertica(self, entities: List[Dict[str, Any]], associations: List[Dict[str, Any]]) -> str:
        # TODO: Implémenter la génération Vertica
        pass
