#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Gestion des associations réflexives avec rôles
"""

from PyQt5.QtCore import QObject, pyqtSignal
from typing import Dict, List, Optional
from .association import Association

class ReflexiveAssociation(Association):
    """Association réflexive avec gestion des rôles"""
    
    def __init__(self, name="Nouvelle association réflexive", pos=None):
        super().__init__(name, pos)
        self.is_reflexive = True
        self.entity = None  # L'entité concernée
        self.roles = {}  # {connection_id: role_name}
        self.connections = []  # Liste des connexions (même entité, rôles différents)
        
    def set_entity(self, entity_name: str):
        """Définit l'entité pour l'association réflexive"""
        self.entity = entity_name
        if entity_name not in self.entities:
            self.entities.append(entity_name)
    
    def add_role(self, connection_id: str, role_name: str, cardinality: str = "1,1"):
        """Ajoute un rôle pour une connexion"""
        self.roles[connection_id] = role_name
        if connection_id not in self.cardinalities:
            self.cardinalities[connection_id] = cardinality
    
    def get_role(self, connection_id: str) -> Optional[str]:
        """Retourne le rôle pour une connexion"""
        return self.roles.get(connection_id)
    
    def get_connections_with_roles(self) -> List[Dict]:
        """Retourne les connexions avec leurs rôles"""
        return [
            {
                "id": conn_id,
                "role": self.roles.get(conn_id, ""),
                "cardinality": self.cardinalities.get(conn_id, "1,1")
            }
            for conn_id in self.connections
        ]
    
    def to_dict(self) -> Dict:
        """Exporte l'association réflexive"""
        data = super().to_dict()
        data["is_reflexive"] = True
        data["entity"] = self.entity
        data["roles"] = self.roles.copy()
        data["connections"] = self.connections.copy()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict):
        """Crée depuis un dictionnaire"""
        assoc = cls(data.get("name", "Association réflexive"), None)
        assoc.set_entity(data.get("entity", ""))
        assoc.roles = data.get("roles", {})
        assoc.connections = data.get("connections", [])
        assoc.cardinalities = data.get("cardinalities", {})
        return assoc

