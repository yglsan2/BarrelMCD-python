#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Gestion des règles de gestion
"""

from typing import List, Dict, Any, Optional
from PyQt5.QtCore import QObject, pyqtSignal
from enum import Enum

class RuleType(Enum):
    """Types de règles de gestion"""
    ENTITY = "entity"
    ASSOCIATION = "association"
    ATTRIBUTE = "attribute"
    GLOBAL = "global"

class BusinessRule:
    """Représente une règle de gestion"""
    
    def __init__(self, name: str, rule_type: RuleType, description: str,
                 target: str = "", condition: str = "", action: str = ""):
        self.name = name
        self.type = rule_type
        self.description = description
        self.target = target  # Entité, association ou attribut concerné
        self.condition = condition  # Condition de la règle
        self.action = action  # Action à effectuer
        self.is_enabled = True
        self.priority = 0  # Priorité (0 = normal, >0 = haute priorité)
        
    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire"""
        return {
            "name": self.name,
            "type": self.type.value,
            "description": self.description,
            "target": self.target,
            "condition": self.condition,
            "action": self.action,
            "is_enabled": self.is_enabled,
            "priority": self.priority
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BusinessRule':
        """Crée depuis un dictionnaire"""
        rule = cls(
            data["name"],
            RuleType(data["type"]),
            data.get("description", ""),
            data.get("target", ""),
            data.get("condition", ""),
            data.get("action", "")
        )
        rule.is_enabled = data.get("is_enabled", True)
        rule.priority = data.get("priority", 0)
        return rule

class BusinessRulesManager(QObject):
    """Gestionnaire des règles de gestion"""
    
    # Signaux
    rule_added = pyqtSignal(object)
    rule_removed = pyqtSignal(str)
    rule_modified = pyqtSignal(object)
    
    def __init__(self):
        super().__init__()
        self.rules: List[BusinessRule] = []
        
    def add_rule(self, rule: BusinessRule) -> bool:
        """Ajoute une règle"""
        if any(r.name == rule.name for r in self.rules):
            return False
        
        self.rules.append(rule)
        self.rule_added.emit(rule)
        return True
    
    def remove_rule(self, name: str) -> bool:
        """Supprime une règle"""
        for i, rule in enumerate(self.rules):
            if rule.name == name:
                self.rules.pop(i)
                self.rule_removed.emit(name)
                return True
        return False
    
    def get_rules_for_entity(self, entity_name: str) -> List[BusinessRule]:
        """Retourne les règles pour une entité"""
        return [r for r in self.rules if r.type == RuleType.ENTITY and r.target == entity_name]
    
    def get_rules_for_association(self, association_name: str) -> List[BusinessRule]:
        """Retourne les règles pour une association"""
        return [r for r in self.rules if r.type == RuleType.ASSOCIATION and r.target == association_name]
    
    def export_rules(self) -> List[Dict[str, Any]]:
        """Exporte les règles"""
        return [r.to_dict() for r in self.rules]
    
    def import_rules(self, rules_data: List[Dict[str, Any]]):
        """Importe les règles"""
        self.rules = [BusinessRule.from_dict(r) for r in rules_data]
    
    def generate_documentation(self) -> str:
        """Génère la documentation des règles"""
        doc = "# Règles de Gestion\n\n"
        
        for rule_type in RuleType:
            rules_of_type = [r for r in self.rules if r.type == rule_type]
            if rules_of_type:
                doc += f"## {rule_type.value.capitalize()}\n\n"
                for rule in rules_of_type:
                    doc += f"### {rule.name}\n"
                    doc += f"**Description:** {rule.description}\n\n"
                    if rule.condition:
                        doc += f"**Condition:** {rule.condition}\n\n"
                    if rule.action:
                        doc += f"**Action:** {rule.action}\n\n"
                    doc += "---\n\n"
        
        return doc

