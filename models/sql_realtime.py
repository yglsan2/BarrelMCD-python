#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Générateur SQL en temps réel
"""

from typing import List, Dict, Any
from PyQt5.QtCore import QObject, pyqtSignal
from .sql_generator import SQLGenerator, SQLDialect

class SQLRealtimeGenerator(QObject):
    """Générateur SQL en temps réel"""
    
    # Signaux
    sql_updated = pyqtSignal(str, str)  # SQL mis à jour (dialect, sql)
    
    def __init__(self):
        super().__init__()
        self.generators = {}
        self.current_sql = {}
        
        # Initialiser les générateurs pour tous les dialectes
        for dialect in SQLDialect:
            self.generators[dialect] = SQLGenerator(dialect)
    
    def update_sql(self, entities: List[Dict], associations: List[Dict], 
                   dialect: SQLDialect = SQLDialect.POSTGRESQL):
        """Met à jour le SQL en temps réel"""
        try:
            # Filtrer les entités fictives
            real_entities = [e for e in entities if not e.get("is_fictitious", False)]
            
            # Générer le SQL
            generator = self.generators.get(dialect, self.generators[SQLDialect.POSTGRESQL])
            sql = generator.generate_sql(real_entities, associations)
            
            self.current_sql[dialect.value] = sql
            self.sql_updated.emit(dialect.value, sql)
            
        except Exception as e:
            error_sql = f"-- Erreur lors de la génération SQL: {e}"
            self.current_sql[dialect.value] = error_sql
            self.sql_updated.emit(dialect.value, error_sql)
    
    def update_all_dialects(self, entities: List[Dict], associations: List[Dict]):
        """Met à jour le SQL pour tous les dialectes"""
        for dialect in SQLDialect:
            self.update_sql(entities, associations, dialect)
    
    def get_current_sql(self, dialect: SQLDialect = SQLDialect.POSTGRESQL) -> str:
        """Retourne le SQL actuel pour un dialecte"""
        return self.current_sql.get(dialect.value, "")

