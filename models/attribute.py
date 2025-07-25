#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Classe Attribute pour représenter les attributs des entités MCD
"""

from PyQt5.QtCore import Qt, QPointF
from PyQt5.QtGui import QPen, QBrush, QColor, QFont

class Attribute:
    """Classe représentant un attribut d'entité MCD"""
    
    def __init__(self, name="", type_name="VARCHAR(255)", is_primary_key=False):
        self.name = name
        self.type = type_name
        self.is_primary_key = is_primary_key
        self.is_required = False
        self.default_value = None
        self.constraints = []
        
    def to_dict(self):
        """Convertit l'attribut en dictionnaire"""
        return {
            "name": self.name,
            "type": self.type,
            "is_primary_key": self.is_primary_key,
            "is_required": self.is_required,
            "default_value": self.default_value,
            "constraints": self.constraints.copy()
        }
        
    @classmethod
    def from_dict(cls, data):
        """Crée un attribut à partir d'un dictionnaire"""
        attr = cls(
            name=data.get("name", ""),
            type_name=data.get("type", "VARCHAR(255)"),
            is_primary_key=data.get("is_primary_key", False)
        )
        attr.is_required = data.get("is_required", False)
        attr.default_value = data.get("default_value")
        attr.constraints = data.get("constraints", [])
        return attr
        
    def __str__(self):
        """Représentation textuelle de l'attribut"""
        prefix = "# " if self.is_primary_key else ""
        return f"{prefix}{self.name}: {self.type}"
        
    def __repr__(self):
        return f"Attribute('{self.name}', '{self.type}', pk={self.is_primary_key})" 