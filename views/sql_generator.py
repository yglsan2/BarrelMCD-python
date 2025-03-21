from PyQt5.QtCore import QObject, pyqtSignal
from models.entities import Entity, Attribute
from models.associations import Association
from views.error_handler import ErrorHandler
import os
from enum import Enum
import re

class SQLDialect(Enum):
    """Dialectes SQL supportés"""
    MYSQL = "MySQL"
    POSTGRESQL = "PostgreSQL"
    SQLITE = "SQLite"
    ORACLE = "Oracle"
    SQLSERVER = "SQL Server"

class SQLGenerator(QObject):
    """Classe pour générer les scripts SQL à partir du modèle de données."""
    
    # Signaux
    sql_generated = pyqtSignal(str)  # Émet le chemin du fichier SQL généré
    error_occurred = pyqtSignal(str)  # Émet les messages d'erreur
    
    def __init__(self):
        super().__init__()
        self.error_handler = ErrorHandler()
        self.dialect = SQLDialect.MYSQL  # Dialecte par défaut
        self._load_sql_templates()
        self._load_type_mappings()
        self._load_naming_rules()
        
    def _load_naming_rules(self):
        """Charge les règles de nommage pour chaque dialecte"""
        self.naming_rules = {
            SQLDialect.MYSQL: {
                "max_identifier_length": 64,
                "case_sensitive": False,
                "allowed_chars": r'^[a-zA-Z0-9_$]+$',
                "reserved_words": {
                    "group": "`group`",
                    "order": "`order`",
                    "key": "`key`"
                }
            },
            SQLDialect.POSTGRESQL: {
                "max_identifier_length": 63,
                "case_sensitive": True,
                "allowed_chars": r'^[a-zA-Z0-9_]+$',
                "reserved_words": {
                    "user": '"user"',
                    "group": '"group"',
                    "order": '"order"'
                }
            },
            SQLDialect.SQLITE: {
                "max_identifier_length": None,
                "case_sensitive": False,
                "allowed_chars": r'^[a-zA-Z0-9_]+$',
                "reserved_words": {
                    "group": "[group]",
                    "order": "[order]",
                    "key": "[key]"
                }
            },
            SQLDialect.ORACLE: {
                "max_identifier_length": 30,
                "case_sensitive": False,
                "allowed_chars": r'^[a-zA-Z0-9_$#]+$',
                "reserved_words": {
                    "user": '"USER"',
                    "group": '"GROUP"',
                    "order": '"ORDER"'
                }
            },
            SQLDialect.SQLSERVER: {
                "max_identifier_length": 128,
                "case_sensitive": False,
                "allowed_chars": r'^[a-zA-Z0-9_$#@]+$',
                "reserved_words": {
                    "user": "[user]",
                    "group": "[group]",
                    "order": "[order]"
                }
            }
        }
        
    def _sanitize_identifier(self, name: str) -> str:
        """Nettoie un identifiant selon les règles du dialecte.
        
        Args:
            name: Nom à nettoyer
            
        Returns:
            str: Nom nettoyé
        """
        rules = self.naming_rules[self.dialect]
        
        # Vérifier la longueur maximale
        if rules["max_identifier_length"] and len(name) > rules["max_identifier_length"]:
            name = name[:rules["max_identifier_length"]]
        
        # Vérifier les caractères autorisés
        if not re.match(rules["allowed_chars"], name):
            name = re.sub(r'[^' + rules["allowed_chars"][2:-2] + ']', '_', name)
        
        # Gérer les mots réservés
        if name.lower() in rules["reserved_words"]:
            return rules["reserved_words"][name.lower()]
            
        # Gérer la casse
        if not rules["case_sensitive"]:
            name = name.lower()
            
        return name
        
    def _load_type_mappings(self):
        """Charge les correspondances de types pour chaque dialecte"""
        self.type_mappings = {
            SQLDialect.MYSQL: {
                "VARCHAR": lambda size: f"VARCHAR({size})",
                "CHAR": lambda size: f"CHAR({size})",
                "INTEGER": lambda _: "INT",
                "FLOAT": lambda _: "FLOAT",
                "DECIMAL": lambda size: f"DECIMAL({size})",
                "DATE": lambda _: "DATE",
                "DATETIME": lambda _: "DATETIME",
                "BOOLEAN": lambda _: "BOOLEAN",
                "TEXT": lambda _: "TEXT",
                "BLOB": lambda _: "BLOB",
                "JSON": lambda _: "JSON",
                "UUID": lambda _: "CHAR(36)",
                "ENUM": lambda values: f"ENUM({', '.join(f\"'{v}'\" for v in values)})",
                "SET": lambda values: f"SET({', '.join(f\"'{v}'\" for v in values)})"
            },
            SQLDialect.POSTGRESQL: {
                "VARCHAR": lambda size: f"VARCHAR({size})",
                "CHAR": lambda size: f"CHAR({size})",
                "INTEGER": lambda _: "INTEGER",
                "FLOAT": lambda _: "REAL",
                "DECIMAL": lambda size: f"NUMERIC({size})",
                "DATE": lambda _: "DATE",
                "DATETIME": lambda _: "TIMESTAMP",
                "BOOLEAN": lambda _: "BOOLEAN",
                "TEXT": lambda _: "TEXT",
                "BLOB": lambda _: "BYTEA",
                "JSON": lambda _: "JSONB",
                "UUID": lambda _: "UUID",
                "ENUM": lambda values: f"CREATE TYPE {values[0]}_enum AS ENUM ({', '.join(f\"'{v}'\" for v in values)})",
                "SET": lambda values: "TEXT[]"
            },
            SQLDialect.SQLITE: {
                "VARCHAR": lambda size: "TEXT",
                "CHAR": lambda size: "TEXT",
                "INTEGER": lambda _: "INTEGER",
                "FLOAT": lambda _: "REAL",
                "DECIMAL": lambda size: "NUMERIC",
                "DATE": lambda _: "TEXT",
                "DATETIME": lambda _: "TEXT",
                "BOOLEAN": lambda _: "INTEGER",
                "TEXT": lambda _: "TEXT",
                "BLOB": lambda _: "BLOB",
                "JSON": lambda _: "TEXT",
                "UUID": lambda _: "TEXT",
                "ENUM": lambda values: "TEXT",
                "SET": lambda values: "TEXT"
            },
            SQLDialect.ORACLE: {
                "VARCHAR": lambda size: f"VARCHAR2({size})",
                "CHAR": lambda size: f"CHAR({size})",
                "INTEGER": lambda _: "NUMBER",
                "FLOAT": lambda _: "NUMBER",
                "DECIMAL": lambda size: f"NUMBER({size})",
                "DATE": lambda _: "DATE",
                "DATETIME": lambda _: "TIMESTAMP",
                "BOOLEAN": lambda _: "NUMBER(1)",
                "TEXT": lambda _: "CLOB",
                "BLOB": lambda _: "BLOB",
                "JSON": lambda _: "CLOB",
                "UUID": lambda _: "RAW(16)",
                "ENUM": lambda values: f"ENUM({', '.join(f\"'{v}'\" for v in values)})",
                "SET": lambda values: f"SET({', '.join(f\"'{v}'\" for v in values)})"
            },
            SQLDialect.SQLSERVER: {
                "VARCHAR": lambda size: f"NVARCHAR({size})",
                "CHAR": lambda size: f"NCHAR({size})",
                "INTEGER": lambda _: "INT",
                "FLOAT": lambda _: "FLOAT",
                "DECIMAL": lambda size: f"DECIMAL({size})",
                "DATE": lambda _: "DATE",
                "DATETIME": lambda _: "DATETIME2",
                "BOOLEAN": lambda _: "BIT",
                "TEXT": lambda _: "NVARCHAR(MAX)",
                "BLOB": lambda _: "VARBINARY(MAX)",
                "JSON": lambda _: "NVARCHAR(MAX)",
                "UUID": lambda _: "UNIQUEIDENTIFIER",
                "ENUM": lambda values: f"ENUM({', '.join(f\"'{v}'\" for v in values)})",
                "SET": lambda values: f"SET({', '.join(f\"'{v}'\" for v in values)})"
            }
        }
        
    def _load_sql_templates(self):
        """Charge les templates SQL pour chaque dialecte"""
        self.sql_templates = {
            SQLDialect.MYSQL: {
                "header": "-- Script MySQL généré automatiquement\n-- Ne pas modifier manuellement\n\n",
                "create_table": "CREATE TABLE {name} (\n{columns}\n) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;",
                "column": "    {name} {type} {constraints}",
                "primary_key": "    PRIMARY KEY ({columns})",
                "foreign_key": "ALTER TABLE {table} ADD CONSTRAINT {name} FOREIGN KEY ({columns}) REFERENCES {ref_table} ({ref_columns});",
                "index": "CREATE INDEX {name} ON {table} ({columns});",
                "comment": "COMMENT ON COLUMN {table}.{column} IS '{comment}';"
            },
            SQLDialect.POSTGRESQL: {
                "header": "-- Script PostgreSQL généré automatiquement\n-- Ne pas modifier manuellement\n\n",
                "create_table": "CREATE TABLE {name} (\n{columns}\n);",
                "column": "    {name} {type} {constraints}",
                "primary_key": "    PRIMARY KEY ({columns})",
                "foreign_key": "ALTER TABLE {table} ADD CONSTRAINT {name} FOREIGN KEY ({columns}) REFERENCES {ref_table} ({ref_columns});",
                "index": "CREATE INDEX {name} ON {table} ({columns});",
                "comment": "COMMENT ON COLUMN {table}.{column} IS '{comment}';"
            },
            SQLDialect.SQLITE: {
                "header": "-- Script SQLite généré automatiquement\n-- Ne pas modifier manuellement\n\n",
                "create_table": "CREATE TABLE {name} (\n{columns}\n);",
                "column": "    {name} {type} {constraints}",
                "primary_key": "    PRIMARY KEY ({columns})",
                "foreign_key": "CREATE INDEX {name} ON {table} ({columns});",
                "index": "CREATE INDEX {name} ON {table} ({columns});",
                "comment": "-- {comment}"
            },
            SQLDialect.ORACLE: {
                "header": "-- Script Oracle généré automatiquement\n-- Ne pas modifier manuellement\n\n",
                "create_table": "CREATE TABLE {name} (\n{columns}\n);",
                "column": "    {name} {type} {constraints}",
                "primary_key": "    CONSTRAINT {name}_pk PRIMARY KEY ({columns})",
                "foreign_key": "ALTER TABLE {table} ADD CONSTRAINT {name} FOREIGN KEY ({columns}) REFERENCES {ref_table} ({ref_columns});",
                "index": "CREATE INDEX {name} ON {table} ({columns});",
                "comment": "COMMENT ON COLUMN {table}.{column} IS '{comment}';"
            },
            SQLDialect.SQLSERVER: {
                "header": "-- Script SQL Server généré automatiquement\n-- Ne pas modifier manuellement\n\n",
                "create_table": "CREATE TABLE {name} (\n{columns}\n);",
                "column": "    {name} {type} {constraints}",
                "primary_key": "    CONSTRAINT {name}_pk PRIMARY KEY ({columns})",
                "foreign_key": "ALTER TABLE {table} ADD CONSTRAINT {name} FOREIGN KEY ({columns}) REFERENCES {ref_table} ({ref_columns});",
                "index": "CREATE INDEX {name} ON {table} ({columns});",
                "comment": "EXEC sp_addextendedproperty @name=N'MS_Description', @value=N'{comment}', @level0type=N'SCHEMA', @level0name=N'dbo', @level1type=N'TABLE', @level1name=N'{table}', @level2type=N'COLUMN', @level2name=N'{column}';"
            }
        }
        
    def set_dialect(self, dialect: SQLDialect):
        """Définit le dialecte SQL à utiliser.
        
        Args:
            dialect: Le dialecte SQL à utiliser
        """
        self.dialect = dialect
        
    def generate_sql(self, entities: list[Entity], associations: list[Association], output_dir: str) -> None:
        """Génère le script SQL à partir du modèle de données.
        
        Args:
            entities: Liste des entités du modèle
            associations: Liste des associations du modèle
            output_dir: Répertoire de sortie pour le script SQL
        """
        try:
            # Créer le répertoire de sortie s'il n'existe pas
            os.makedirs(output_dir, exist_ok=True)
            
            # Générer le script SQL
            sql_file = os.path.join(output_dir, f"schema_{self.dialect.value.lower()}.sql")
            self._generate_sql_file(entities, associations, sql_file)
            
            self.sql_generated.emit(sql_file)
            
        except Exception as e:
            self.error_handler.handle_error(e, "Erreur lors de la génération du script SQL")
            self.error_occurred.emit(str(e))
    
    def _generate_sql_file(self, entities: list[Entity], associations: list[Association], output_file: str) -> None:
        """Génère le fichier SQL avec les instructions CREATE TABLE et les contraintes.
        
        Args:
            entities: Liste des entités
            associations: Liste des associations
            output_file: Chemin du fichier de sortie
        """
        with open(output_file, 'w', encoding='utf-8') as f:
            # En-tête du fichier
            f.write(self.sql_templates[self.dialect]["header"])
            
            # Générer les tables pour chaque entité
            for entity in entities:
                self._write_entity_table(f, entity)
            
            # Générer les contraintes de clés étrangères
            f.write("\n-- Contraintes de clés étrangères\n")
            for association in associations:
                self._write_foreign_key_constraints(f, association)
    
    def _write_entity_table(self, file, entity: Entity) -> None:
        """Écrit la définition d'une table pour une entité.
        
        Args:
            file: Fichier ouvert en écriture
            entity: Entité à convertir en table
        """
        # Nettoyer le nom de la table
        table_name = self._sanitize_identifier(entity.name)
        
        # Colonnes de la table
        columns = []
        
        # Ajouter l'ID auto-incrémenté si pas de clé primaire définie
        if not any(attr.is_primary_key for attr in entity.attributes):
            id_type = {
                SQLDialect.MYSQL: "INT AUTO_INCREMENT",
                SQLDialect.POSTGRESQL: "SERIAL",
                SQLDialect.SQLITE: "INTEGER PRIMARY KEY AUTOINCREMENT",
                SQLDialect.ORACLE: "NUMBER GENERATED ALWAYS AS IDENTITY",
                SQLDialect.SQLSERVER: "INT IDENTITY(1,1)"
            }
            columns.append(f"    id {id_type[self.dialect]} PRIMARY KEY")
        
        # Ajouter les autres colonnes
        for attr in entity.attributes:
            # Nettoyer le nom de la colonne
            attr.name = self._sanitize_identifier(attr.name)
            column_def = self._get_column_definition(attr)
            columns.append(column_def)
        
        # Ajouter les contraintes de clé primaire si des attributs sont marqués comme PK
        pk_attrs = [attr for attr in entity.attributes if attr.is_primary_key]
        if pk_attrs:
            pk_names = [attr.name for attr in pk_attrs]
            pk_constraint = self.sql_templates[self.dialect]["primary_key"].format(
                name=table_name,
                columns=", ".join(pk_names)
            )
            columns.append(pk_constraint)
        
        # Écrire la définition de la table
        table_def = self.sql_templates[self.dialect]["create_table"].format(
            name=table_name,
            columns=",\n".join(columns)
        )
        file.write(f"\n-- Table {table_name}\n")
        file.write(table_def + "\n")
        
        # Ajouter les commentaires sur les colonnes
        for attr in entity.attributes:
            if attr.comment:
                comment = self.sql_templates[self.dialect]["comment"].format(
                    table=table_name,
                    column=attr.name,
                    comment=attr.comment.replace("'", "''")  # Échapper les apostrophes
                )
                file.write(comment + "\n")
                
        # Ajouter les index pour les colonnes uniques
        for attr in entity.attributes:
            if attr.is_unique and not attr.is_primary_key:
                idx = self.sql_templates[self.dialect]["index"].format(
                    name=f"idx_{table_name}_{attr.name}",
                    table=table_name,
                    columns=attr.name
                )
                file.write(idx + "\n")
    
    def _get_column_definition(self, attr: Attribute) -> str:
        """Génère la définition d'une colonne SQL à partir d'un attribut.
        
        Args:
            attr: Attribut à convertir en colonne
            
        Returns:
            str: Définition de la colonne SQL
        """
        # Type de données SQL
        sql_type = self._get_sql_type(attr)
        
        # Contraintes de la colonne
        constraints = []
        if attr.is_primary_key and self.dialect != SQLDialect.ORACLE and self.dialect != SQLDialect.SQLSERVER:
            constraints.append("PRIMARY KEY")
        if attr.is_unique:
            constraints.append("UNIQUE")
        if attr.is_not_null:
            constraints.append("NOT NULL")
        
        # Définition complète de la colonne
        return self.sql_templates[self.dialect]["column"].format(
            name=attr.name,
            type=sql_type,
            constraints=" ".join(constraints)
        )
    
    def _get_sql_type(self, attr: Attribute) -> str:
        """Convertit le type de données en type SQL selon le dialecte.
        
        Args:
            attr: Attribut dont le type doit être converti
            
        Returns:
            str: Type SQL correspondant
        """
        # Règles spécifiques par dialecte
        type_rules = {
            SQLDialect.MYSQL: {
                "INTEGER": "INT",
                "FLOAT": "FLOAT",
                "DECIMAL": "DECIMAL",
                "DATETIME": "DATETIME",
                "BOOLEAN": "BOOLEAN",
                "TEXT": "TEXT",
                "BLOB": "BLOB",
                "JSON": "JSON",
                "UUID": "CHAR(36)",
                "ENUM": lambda values: f"ENUM({', '.join(f\"'{v}'\" for v in values)})",
                "SET": lambda values: f"SET({', '.join(f\"'{v}'\" for v in values)})"
            },
            SQLDialect.POSTGRESQL: {
                "INTEGER": "INTEGER",
                "FLOAT": "REAL",
                "DECIMAL": "NUMERIC",
                "DATETIME": "TIMESTAMP",
                "BOOLEAN": "BOOLEAN",
                "TEXT": "TEXT",
                "BLOB": "BYTEA",
                "JSON": "JSONB",
                "UUID": "UUID",
                "ENUM": lambda values: f"CREATE TYPE {values[0]}_enum AS ENUM ({', '.join(f\"'{v}'\" for v in values)})",
                "SET": lambda values: "TEXT[]"
            },
            SQLDialect.SQLITE: {
                "INTEGER": "INTEGER",
                "FLOAT": "REAL",
                "DECIMAL": "NUMERIC",
                "DATETIME": "TEXT",
                "BOOLEAN": "INTEGER",
                "TEXT": "TEXT",
                "BLOB": "BLOB",
                "JSON": "TEXT",
                "UUID": "TEXT",
                "ENUM": lambda values: "TEXT",
                "SET": lambda values: "TEXT"
            },
            SQLDialect.ORACLE: {
                "INTEGER": "NUMBER",
                "FLOAT": "NUMBER",
                "DECIMAL": "NUMBER",
                "DATETIME": "TIMESTAMP",
                "BOOLEAN": "NUMBER(1)",
                "TEXT": "CLOB",
                "BLOB": "BLOB",
                "JSON": "CLOB",
                "UUID": "RAW(16)",
                "ENUM": lambda values: f"ENUM({', '.join(f\"'{v}'\" for v in values)})",
                "SET": lambda values: f"SET({', '.join(f\"'{v}'\" for v in values)})"
            },
            SQLDialect.SQLSERVER: {
                "INTEGER": "INT",
                "FLOAT": "FLOAT",
                "DECIMAL": "DECIMAL",
                "DATETIME": "DATETIME2",
                "BOOLEAN": "BIT",
                "TEXT": "NVARCHAR(MAX)",
                "BLOB": "VARBINARY(MAX)",
                "JSON": "NVARCHAR(MAX)",
                "UUID": "UNIQUEIDENTIFIER",
                "ENUM": lambda values: f"ENUM({', '.join(f\"'{v}'\" for v in values)})",
                "SET": lambda values: f"SET({', '.join(f\"'{v}'\" for v in values)})"
            }
        }
        
        # Règles de conversion spécifiques
        conversion_rules = {
            SQLDialect.MYSQL: {
                "INT": "INT",
                "INTEGER": "INT",
                "SMALLINT": "SMALLINT",
                "BIGINT": "BIGINT",
                "TINYINT": "TINYINT",
                "MEDIUMINT": "MEDIUMINT",
                "FLOAT": "FLOAT",
                "DOUBLE": "DOUBLE",
                "DECIMAL": "DECIMAL",
                "NUMERIC": "DECIMAL",
                "CHAR": "CHAR",
                "VARCHAR": "VARCHAR",
                "TEXT": "TEXT",
                "TINYTEXT": "TINYTEXT",
                "MEDIUMTEXT": "MEDIUMTEXT",
                "LONGTEXT": "LONGTEXT",
                "BLOB": "BLOB",
                "TINYBLOB": "TINYBLOB",
                "MEDIUMBLOB": "MEDIUMBLOB",
                "LONGBLOB": "LONGBLOB",
                "DATE": "DATE",
                "TIME": "TIME",
                "DATETIME": "DATETIME",
                "TIMESTAMP": "TIMESTAMP",
                "YEAR": "YEAR",
                "BOOLEAN": "BOOLEAN",
                "BOOL": "BOOLEAN",
                "JSON": "JSON",
                "UUID": "CHAR(36)",
                "ENUM": lambda values: f"ENUM({', '.join(f\"'{v}'\" for v in values)})",
                "SET": lambda values: f"SET({', '.join(f\"'{v}'\" for v in values)})"
            },
            SQLDialect.POSTGRESQL: {
                "INT": "INTEGER",
                "INTEGER": "INTEGER",
                "SMALLINT": "SMALLINT",
                "BIGINT": "BIGINT",
                "FLOAT": "REAL",
                "DOUBLE": "DOUBLE PRECISION",
                "DECIMAL": "NUMERIC",
                "NUMERIC": "NUMERIC",
                "CHAR": "CHAR",
                "VARCHAR": "VARCHAR",
                "TEXT": "TEXT",
                "BLOB": "BYTEA",
                "DATE": "DATE",
                "TIME": "TIME",
                "DATETIME": "TIMESTAMP",
                "TIMESTAMP": "TIMESTAMP",
                "BOOLEAN": "BOOLEAN",
                "BOOL": "BOOLEAN",
                "JSON": "JSONB",
                "UUID": "UUID",
                "ENUM": lambda values: f"CREATE TYPE {values[0]}_enum AS ENUM ({', '.join(f\"'{v}'\" for v in values)})",
                "SET": lambda values: "TEXT[]"
            },
            SQLDialect.SQLITE: {
                "INT": "INTEGER",
                "INTEGER": "INTEGER",
                "SMALLINT": "INTEGER",
                "BIGINT": "INTEGER",
                "FLOAT": "REAL",
                "DOUBLE": "REAL",
                "DECIMAL": "NUMERIC",
                "NUMERIC": "NUMERIC",
                "CHAR": "TEXT",
                "VARCHAR": "TEXT",
                "TEXT": "TEXT",
                "BLOB": "BLOB",
                "DATE": "TEXT",
                "TIME": "TEXT",
                "DATETIME": "TEXT",
                "TIMESTAMP": "TEXT",
                "BOOLEAN": "INTEGER",
                "BOOL": "INTEGER",
                "JSON": "TEXT",
                "UUID": "TEXT",
                "ENUM": lambda values: "TEXT",
                "SET": lambda values: "TEXT"
            },
            SQLDialect.ORACLE: {
                "INT": "NUMBER",
                "INTEGER": "NUMBER",
                "SMALLINT": "NUMBER",
                "BIGINT": "NUMBER",
                "FLOAT": "NUMBER",
                "DOUBLE": "NUMBER",
                "DECIMAL": "NUMBER",
                "NUMERIC": "NUMBER",
                "CHAR": "CHAR",
                "VARCHAR": "VARCHAR2",
                "TEXT": "CLOB",
                "BLOB": "BLOB",
                "DATE": "DATE",
                "TIME": "DATE",
                "DATETIME": "TIMESTAMP",
                "TIMESTAMP": "TIMESTAMP",
                "BOOLEAN": "NUMBER(1)",
                "BOOL": "NUMBER(1)",
                "JSON": "CLOB",
                "UUID": "RAW(16)",
                "ENUM": lambda values: f"ENUM({', '.join(f\"'{v}'\" for v in values)})",
                "SET": lambda values: f"SET({', '.join(f\"'{v}'\" for v in values)})"
            },
            SQLDialect.SQLSERVER: {
                "INT": "INT",
                "INTEGER": "INT",
                "SMALLINT": "SMALLINT",
                "BIGINT": "BIGINT",
                "FLOAT": "FLOAT",
                "DOUBLE": "FLOAT",
                "DECIMAL": "DECIMAL",
                "NUMERIC": "NUMERIC",
                "CHAR": "NCHAR",
                "VARCHAR": "NVARCHAR",
                "TEXT": "NVARCHAR(MAX)",
                "BLOB": "VARBINARY(MAX)",
                "DATE": "DATE",
                "TIME": "TIME",
                "DATETIME": "DATETIME2",
                "TIMESTAMP": "DATETIME2",
                "BOOLEAN": "BIT",
                "BOOL": "BIT",
                "JSON": "NVARCHAR(MAX)",
                "UUID": "UNIQUEIDENTIFIER",
                "ENUM": lambda values: f"ENUM({', '.join(f\"'{v}'\" for v in values)})",
                "SET": lambda values: f"SET({', '.join(f\"'{v}'\" for v in values)})"
            }
        }
        
        # Convertir le type selon les règles du dialecte
        if attr.type in conversion_rules[self.dialect]:
            rule = conversion_rules[self.dialect][attr.type]
            if callable(rule):
                return rule(attr.size)
            return rule
            
        # Type par défaut
        return conversion_rules[self.dialect]["VARCHAR"](255)
    
    def _write_foreign_key_constraints(self, file, association: Association) -> None:
        """Écrit les contraintes de clés étrangères pour une association.
        
        Args:
            file: Fichier ouvert en écriture
            association: Association à convertir en contraintes
        """
        # Nettoyer les noms des tables
        source_table = self._sanitize_identifier(association.source.name)
        target_table = self._sanitize_identifier(association.target.name)
        
        # Gérer les relations many-to-many
        if association.is_many_to_many():
            # Créer une table de jonction
            junction_table = self._sanitize_identifier(f"{source_table}_{target_table}")
            
            # Colonnes de la table de jonction
            columns = [
                f"{source_table}_id {self._get_sql_type({'type': 'INTEGER'})} NOT NULL",
                f"{target_table}_id {self._get_sql_type({'type': 'INTEGER'})} NOT NULL",
                f"PRIMARY KEY ({source_table}_id, {target_table}_id)"
            ]
            
            # Ajouter les attributs de l'association
            for attr in association.attributes:
                columns.append(self._get_column_definition(attr))
            
            # Créer la table de jonction
            table_def = self.sql_templates[self.dialect]["create_table"].format(
                name=junction_table,
                columns=",\n".join(columns)
            )
            file.write(f"\n-- Table de jonction {junction_table}\n")
            file.write(table_def + "\n")
            
            # Ajouter les contraintes de clés étrangères
            fk1 = self.sql_templates[self.dialect]["foreign_key"].format(
                table=junction_table,
                name=f"fk_{junction_table}_{source_table}",
                columns=f"{source_table}_id",
                ref_table=source_table,
                ref_columns="id"
            )
            file.write(fk1 + "\n")
            
            fk2 = self.sql_templates[self.dialect]["foreign_key"].format(
                table=junction_table,
                name=f"fk_{junction_table}_{target_table}",
                columns=f"{target_table}_id",
                ref_table=target_table,
                ref_columns="id"
            )
            file.write(fk2 + "\n")
            
        else:
            # Relation one-to-many ou one-to-one
            if association.foreign_key:
                fk = self.sql_templates[self.dialect]["foreign_key"].format(
                    table=target_table,
                    name=f"fk_{target_table}_{source_table}",
                    columns=association.foreign_key,
                    ref_table=source_table,
                    ref_columns=association.primary_key
                )
                file.write(fk + "\n")
                
                # Ajouter un index sur la clé étrangère
                idx = self.sql_templates[self.dialect]["index"].format(
                    name=f"idx_{target_table}_{association.foreign_key}",
                    table=target_table,
                    columns=association.foreign_key
                )
                file.write(idx + "\n")
                
                # Ajouter une contrainte UNIQUE pour les relations one-to-one
                if association.is_one_to_one():
                    unique = f"ALTER TABLE {target_table} ADD CONSTRAINT uk_{target_table}_{association.foreign_key} UNIQUE ({association.foreign_key});"
                    file.write(unique + "\n")