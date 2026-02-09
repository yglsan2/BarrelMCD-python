#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Gestion des entités fictives (non générées dans le MLD)
"""

from models.entity import Entity
from typing import Dict

class FictitiousEntity(Entity):
    """Entité fictive qui n'est pas générée dans le MLD"""
    
    def __init__(self, name="Nouvelle entité fictive", pos=None):
        super().__init__(name, pos)
        self.is_fictitious = True
        self.purpose = ""  # Raison de l'entité fictive
        self.exclude_from_mld = True
        self.exclude_from_sql = True
        
    def set_purpose(self, purpose: str):
        """Définit la raison de l'entité fictive"""
        self.purpose = purpose
    
    def to_dict(self) -> Dict:
        """Exporte l'entité fictive"""
        data = super().get_data()
        data["is_fictitious"] = True
        data["purpose"] = self.purpose
        data["exclude_from_mld"] = self.exclude_from_mld
        data["exclude_from_sql"] = self.exclude_from_sql
        return data
    
    @classmethod
    def from_dict(cls, data: Dict):
        """Crée depuis un dictionnaire"""
        entity = cls(data.get("name", "Entité fictive"), None)
        entity.purpose = data.get("purpose", "")
        entity.exclude_from_mld = data.get("exclude_from_mld", True)
        entity.exclude_from_sql = data.get("exclude_from_sql", True)
        return entity

