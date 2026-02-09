#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Gestion des contraintes d'intégrité fonctionnelle (CIF/CIFF)
"""

from enum import Enum
from typing import List, Dict, Any, Optional
from PyQt5.QtCore import QObject, pyqtSignal

class CIFType(Enum):
    """Types de contraintes CIF"""
    FUNCTIONAL = "functional"  # Contrainte fonctionnelle
    INTER_ASSOCIATION = "inter_association"  # Contrainte inter-associations
    UNIQUE = "unique"  # Contrainte d'unicité
    EXCLUSION = "exclusion"  # Contrainte d'exclusion

class CIFConstraint:
    """Représente une contrainte d'intégrité fonctionnelle"""
    
    def __init__(self, name: str, constraint_type: CIFType, 
                 description: str = "", entities: List[str] = None,
                 associations: List[str] = None, attributes: List[str] = None):
        self.name = name
        self.type = constraint_type
        self.description = description
        self.entities = entities or []
        self.associations = associations or []
        self.attributes = attributes or []
        self.is_enabled = True
        
    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire"""
        return {
            "name": self.name,
            "type": self.type.value,
            "description": self.description,
            "entities": self.entities,
            "associations": self.associations,
            "attributes": self.attributes,
            "is_enabled": self.is_enabled
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CIFConstraint':
        """Crée depuis un dictionnaire"""
        constraint = cls(
            data["name"],
            CIFType(data["type"]),
            data.get("description", ""),
            data.get("entities", []),
            data.get("associations", []),
            data.get("attributes", [])
        )
        constraint.is_enabled = data.get("is_enabled", True)
        return constraint

class CIFManager(QObject):
    """Gestionnaire des contraintes CIF/CIFF"""
    
    # Signaux
    constraint_added = pyqtSignal(object)
    constraint_removed = pyqtSignal(str)
    constraint_modified = pyqtSignal(object)
    
    def __init__(self):
        super().__init__()
        self.constraints: List[CIFConstraint] = []
        
    def add_constraint(self, constraint: CIFConstraint) -> bool:
        """Ajoute une contrainte"""
        # Vérifier qu'il n'y a pas de doublon
        if any(c.name == constraint.name for c in self.constraints):
            return False
        
        self.constraints.append(constraint)
        self.constraint_added.emit(constraint)
        return True
    
    def remove_constraint(self, name: str) -> bool:
        """Supprime une contrainte"""
        for i, constraint in enumerate(self.constraints):
            if constraint.name == name:
                self.constraints.pop(i)
                self.constraint_removed.emit(name)
                return True
        return False
    
    def get_constraints_for_entity(self, entity_name: str) -> List[CIFConstraint]:
        """Retourne les contraintes pour une entité"""
        return [c for c in self.constraints if entity_name in c.entities]
    
    def get_constraints_for_association(self, association_name: str) -> List[CIFConstraint]:
        """Retourne les contraintes pour une association"""
        return [c for c in self.constraints if association_name in c.associations]
    
    def validate_constraints(self, entities: List[Dict], associations: List[Dict]) -> List[Dict]:
        """Valide toutes les contraintes"""
        errors = []
        
        for constraint in self.constraints:
            if not constraint.is_enabled:
                continue
                
            # Valider selon le type
            if constraint.type == CIFType.FUNCTIONAL:
                errors.extend(self._validate_functional_constraint(constraint, entities, associations))
            elif constraint.type == CIFType.INTER_ASSOCIATION:
                errors.extend(self._validate_inter_association_constraint(constraint, associations))
            elif constraint.type == CIFType.UNIQUE:
                errors.extend(self._validate_unique_constraint(constraint, entities))
            elif constraint.type == CIFType.EXCLUSION:
                errors.extend(self._validate_exclusion_constraint(constraint, entities, associations))
        
        return errors
    
    def _validate_functional_constraint(self, constraint: CIFConstraint, 
                                       entities: List[Dict], associations: List[Dict]) -> List[Dict]:
        """Valide une contrainte fonctionnelle"""
        errors = []
        # TODO: Implémenter la validation
        return errors
    
    def _validate_inter_association_constraint(self, constraint: CIFConstraint, 
                                              associations: List[Dict]) -> List[Dict]:
        """Valide une contrainte inter-associations"""
        errors = []
        # TODO: Implémenter la validation
        return errors
    
    def _validate_unique_constraint(self, constraint: CIFConstraint, 
                                   entities: List[Dict]) -> List[Dict]:
        """Valide une contrainte d'unicité"""
        errors = []
        # TODO: Implémenter la validation
        return errors
    
    def _validate_exclusion_constraint(self, constraint: CIFConstraint, 
                                      entities: List[Dict], associations: List[Dict]) -> List[Dict]:
        """Valide une contrainte d'exclusion"""
        errors = []
        # TODO: Implémenter la validation
        return errors
    
    def export_constraints(self) -> List[Dict[str, Any]]:
        """Exporte les contraintes"""
        return [c.to_dict() for c in self.constraints]
    
    def import_constraints(self, constraints_data: List[Dict[str, Any]]):
        """Importe les contraintes"""
        self.constraints = [CIFConstraint.from_dict(c) for c in constraints_data]

