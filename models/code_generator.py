#!/usr/bin/env python3

from enum import Enum
# -*- coding: utf-8 -*-

"""
Générateur de code pour BarrelMCD
Support SQL, MLD, ORM, etc.
"""

from PyQt5.QtCore import QObject, pyqtSignal
from enum import Enum
from typing import Dict, List, Any, Optional
import re

class CodeLanguage(Enum):
    """Langages de code supportés"""
    SQL = "sql"
    PYTHON = "python"
    JAVA = "java"
    C_SHARP = "csharp"
    PHP = "php"
    JAVASCRIPT = "javascript"

class ORMFramework(Enum):
    """Frameworks ORM supportés"""
    SQLALCHEMY = "sqlalchemy"
    DJANGO_ORM = "django_orm"
    HIBERNATE = "hibernate"
    ENTITY_FRAMEWORK = "entity_framework"
    ELOQUENT = "eloquent"
    SEQUELIZE = "sequelize"

class SQLDialect(Enum):
    """Dialectes SQL supportés"""
    MYSQL = "mysql"
    POSTGRESQL = "postgresql"
    SQLITE = "sqlite"
    ORACLE = "oracle"
    SQLSERVER = "sqlserver"

class CodeGenerator(QObject):
    """Générateur de code pour les modèles MCD"""
    
    # Signaux
    code_generated = pyqtSignal(str, str)  # language, code
    generation_error = pyqtSignal(str)  # error_message
    
    def __init__(self):
        super().__init__()
        
    def generate_sql(self, entities: List[Dict], associations: List[Dict], 
                    dialect: SQLDialect = SQLDialect.MYSQL) -> str:
        """Génère le code SQL pour le modèle MCD"""
        try:
            sql_code = []
            sql_code.append(f"-- Généré par BarrelMCD")
            sql_code.append(f"-- Dialecte: {dialect.value}")
            sql_code.append("")
            
            # Générer les tables pour les entités
            for entity in entities:
                table_sql = self._generate_entity_table(entity, dialect)
                sql_code.extend(table_sql)
                sql_code.append("")
            
            # Générer les tables pour les associations
            for association in associations:
                if association.get("entities"):
                    table_sql = self._generate_association_table(association, dialect)
                    sql_code.extend(table_sql)
                    sql_code.append("")
            
            return "\n".join(sql_code)
        except Exception as e:
            self.generation_error.emit(f"Erreur lors de la génération SQL: {e}")
            return ""
    
    def generate_orm(self, entities: List[Dict], associations: List[Dict],
                    language: CodeLanguage, framework: ORMFramework) -> str:
        """Génère le code ORM pour le modèle MCD"""
        try:
            if language == CodeLanguage.PYTHON and framework == ORMFramework.SQLALCHEMY:
                return self._generate_sqlalchemy_models(entities, associations)
            elif language == CodeLanguage.PYTHON and framework == ORMFramework.DJANGO_ORM:
                return self._generate_django_models(entities, associations)
            elif language == CodeLanguage.JAVA and framework == ORMFramework.HIBERNATE:
                return self._generate_hibernate_entities(entities, associations)
            else:
                self.generation_error.emit(f"Combinaison non supportée: {language.value} + {framework.value}")
                return ""
        except Exception as e:
            self.generation_error.emit(f"Erreur lors de la génération ORM: {e}")
            return ""
    
    def generate_mld(self, entities: List[Dict], associations: List[Dict]) -> str:
        """Génère le Modèle Logique de Données (MLD)"""
        try:
            mld_code = []
            mld_code.append("-- Modèle Logique de Données (MLD)")
            mld_code.append("-- Généré par BarrelMCD")
            mld_code.append("")
            
            # Traitement des entités
            for entity in entities:
                mld_entity = self._generate_mld_entity(entity)
                mld_code.extend(mld_entity)
                mld_code.append("")
            
            # Traitement des associations
            for association in associations:
                if association.get("entities"):
                    mld_association = self._generate_mld_association(association)
                    mld_code.extend(mld_association)
                    mld_code.append("")
            
            return "\n".join(mld_code)
        except Exception as e:
            self.generation_error.emit(f"Erreur lors de la génération MLD: {e}")
            return ""
    
    def _generate_entity_table(self, entity: Dict, dialect: SQLDialect) -> List[str]:
        """Génère le code SQL pour une entité"""
        table_name = self._sanitize_name(entity.get("name", "table"))
        sql_lines = []
        
        # Début de la table
        sql_lines.append(f"CREATE TABLE {table_name} (")
        
        # Colonnes
        columns = []
        
        # Clé primaire
        pk_name = f"{table_name}_id"
        if dialect == SQLDialect.MYSQL:
            columns.append(f"    {pk_name} INT AUTO_INCREMENT PRIMARY KEY")
        elif dialect == SQLDialect.POSTGRESQL:
            columns.append(f"    {pk_name} SERIAL PRIMARY KEY")
        elif dialect == SQLDialect.SQLITE:
            columns.append(f"    {pk_name} INTEGER PRIMARY KEY AUTOINCREMENT")
        else:
            columns.append(f"    {pk_name} INT PRIMARY KEY")
        
        # Attributs
        for attr in entity.get("attributes", []):
            attr_name = self._sanitize_name(attr.get("name", "attr"))
            attr_type = self._map_sql_type(attr.get("type", "VARCHAR"), dialect)
            nullable = "" if attr.get("null", True) else " NOT NULL"
            columns.append(f"    {attr_name} {attr_type}{nullable}")
        
        sql_lines.append(",\n".join(columns))
        sql_lines.append(");")
        
        return sql_lines
    
    def _generate_association_table(self, association: Dict, dialect: SQLDialect) -> List[str]:
        """Génère le code SQL pour une association"""
        if not association.get("entities"):
            return []
        
        table_name = self._sanitize_name(association.get("name", "association"))
        sql_lines = []
        
        sql_lines.append(f"CREATE TABLE {table_name} (")
        
        # Clés étrangères
        columns = []
        for entity in association["entities"]:
            entity_name = self._sanitize_name(entity.get("name", "entity"))
            fk_name = f"{entity_name}_id"
            columns.append(f"    {fk_name} INT NOT NULL")
        
        # Attributs de l'association
        for attr in association.get("attributes", []):
            attr_name = self._sanitize_name(attr.get("name", "attr"))
            attr_type = self._map_sql_type(attr.get("type", "VARCHAR"), dialect)
            nullable = "" if attr.get("null", True) else " NOT NULL"
            columns.append(f"    {attr_name} {attr_type}{nullable}")
        
        sql_lines.append(",\n".join(columns))
        sql_lines.append(");")
        
        return sql_lines
    
    def _generate_sqlalchemy_models(self, entities: List[Dict], associations: List[Dict]) -> str:
        """Génère les modèles SQLAlchemy"""
        code_lines = []
        code_lines.append("from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey")
        code_lines.append("from sqlalchemy.ext.declarative import declarative_base")
        code_lines.append("from sqlalchemy.orm import relationship")
        code_lines.append("")
        code_lines.append("Base = declarative_base()")
        code_lines.append("")
        
        # Modèles pour les entités
        for entity in entities:
            model_code = self._generate_sqlalchemy_entity(entity)
            code_lines.extend(model_code)
            code_lines.append("")
        
        # Modèles pour les associations
        for association in associations:
            if association.get("entities"):
                model_code = self._generate_sqlalchemy_association(association)
                code_lines.extend(model_code)
                code_lines.append("")
        
        return "\n".join(code_lines)
    
    def _generate_sqlalchemy_entity(self, entity: Dict) -> List[str]:
        """Génère un modèle SQLAlchemy pour une entité"""
        class_name = self._to_pascal_case(entity.get("name", "Entity"))
        table_name = self._sanitize_name(entity.get("name", "entity"))
        
        code_lines = []
        code_lines.append(f"class {class_name}(Base):")
        code_lines.append(f'    __tablename__ = "{table_name}"')
        code_lines.append("")
        
        # Clé primaire
        pk_name = f"{table_name}_id"
        code_lines.append(f"    {pk_name} = Column(Integer, primary_key=True)")
        
        # Attributs
        for attr in entity.get("attributes", []):
            attr_name = self._sanitize_name(attr.get("name", "attr"))
            attr_type = self._map_sqlalchemy_type(attr.get("type", "String"))
            code_lines.append(f"    {attr_name} = Column({attr_type})")
        
        return code_lines
    
    def _generate_mld_entity(self, entity: Dict) -> List[str]:
        """Génère le MLD pour une entité"""
        entity_name = entity.get("name", "Entity")
        mld_lines = []
        
        mld_lines.append(f"Entité: {entity_name}")
        mld_lines.append("Attributs:")
        
        for attr in entity.get("attributes", []):
            attr_name = attr.get("name", "attr")
            attr_type = attr.get("type", "VARCHAR")
            mld_lines.append(f"  - {attr_name} ({attr_type})")
        
        return mld_lines
    
    def _generate_mld_association(self, association: Dict) -> List[str]:
        """Génère le MLD pour une association"""
        association_name = association.get("name", "Association")
        mld_lines = []
        
        mld_lines.append(f"Association: {association_name}")
        mld_lines.append("Entités liées:")
        
        for entity in association.get("entities", []):
            entity_name = entity.get("name", "Entity")
            cardinality = association.get("cardinalities", {}).get(entity_name, "1")
            mld_lines.append(f"  - {entity_name} ({cardinality})")
        
        if association.get("attributes"):
            mld_lines.append("Attributs:")
            for attr in association["attributes"]:
                attr_name = attr.get("name", "attr")
                attr_type = attr.get("type", "VARCHAR")
                mld_lines.append(f"  - {attr_name} ({attr_type})")
        
        return mld_lines
    
    def _sanitize_name(self, name: str) -> str:
        """Nettoie un nom pour l'utiliser en SQL"""
        return re.sub(r'[^a-zA-Z0-9_]', '_', name.lower())
    
    def _to_pascal_case(self, name: str) -> str:
        """Convertit en PascalCase"""
        return ''.join(word.capitalize() for word in re.split(r'[_\s-]', name))
    
    def _map_sql_type(self, mcd_type: str, dialect: SQLDialect) -> str:
        """Mappe un type MCD vers un type SQL"""
        type_mapping = {
            "VARCHAR": "VARCHAR(255)",
            "TEXT": "TEXT",
            "INT": "INT",
            "FLOAT": "FLOAT",
            "DATE": "DATE",
            "DATETIME": "DATETIME",
            "BOOLEAN": "BOOLEAN"
        }
        return type_mapping.get(mcd_type.upper(), "VARCHAR(255)")
    
    def _map_sqlalchemy_type(self, mcd_type: str) -> str:
        """Mappe un type MCD vers un type SQLAlchemy"""
        type_mapping = {
            "VARCHAR": "String",
            "TEXT": "Text",
            "INT": "Integer",
            "FLOAT": "Float",
            "DATE": "Date",
            "DATETIME": "DateTime",
            "BOOLEAN": "Boolean"
        }
        return type_mapping.get(mcd_type.upper(), "String")
