#!/usr/bin/env python3

from enum import Enum
# -*- coding: utf-8 -*-

"""
Validateur de modèle MCD pour BarrelMCD
"""

from PyQt5.QtCore import QObject, pyqtSignal
from enum import Enum
from typing import Dict, List, Any, Optional

class ValidationLevel(Enum):
    """Niveaux de validation"""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"

class ValidationRule(Enum):
    """Règles de validation"""
    ENTITY_NAME_UNIQUE = "entity_name_unique"
    ASSOCIATION_NAME_UNIQUE = "association_name_unique"
    ENTITY_HAS_ATTRIBUTES = "entity_has_attributes"
    ASSOCIATION_HAS_ENTITIES = "association_has_entities"
    CARDINALITY_VALID = "cardinality_valid"
    INHERITANCE_CYCLE = "inheritance_cycle"
    NAMING_CONVENTION = "naming_convention"

class ValidationResult:
    """Résultat d'une validation"""
    
    def __init__(self, rule: ValidationRule, level: ValidationLevel, 
                 message: str, element_id: Optional[str] = None):
        self.rule = rule
        self.level = level
        self.message = message
        self.element_id = element_id
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire"""
        return {
            "rule": self.rule.value,
            "level": self.level.value,
            "message": self.message,
            "element_id": self.element_id
        }

class ModelValidator(QObject):
    """Validateur de modèle MCD"""
    
    # Signaux
    validation_completed = pyqtSignal(list)  # Liste des résultats
    validation_error = pyqtSignal(str)  # Message d'erreur
    
    def __init__(self):
        super().__init__()
        self.validation_rules = [
            ValidationRule.ENTITY_NAME_UNIQUE,
            ValidationRule.ASSOCIATION_NAME_UNIQUE,
            ValidationRule.ENTITY_HAS_ATTRIBUTES,
            ValidationRule.ASSOCIATION_HAS_ENTITIES,
            ValidationRule.CARDINALITY_VALID,
            ValidationRule.INHERITANCE_CYCLE,
            ValidationRule.NAMING_CONVENTION
        ]
    
    def validate_model(self, entities: List[Dict], associations: List[Dict], 
                      inheritances: List[Dict]) -> List[ValidationResult]:
        """Valide le modèle MCD complet"""
        results = []
        
        try:
            # Validation des entités
            results.extend(self._validate_entities(entities))
            
            # Validation des associations
            results.extend(self._validate_associations(associations, entities))
            
            # Validation des héritages
            results.extend(self._validate_inheritances(inheritances, entities))
            
            # Validation globale
            results.extend(self._validate_global_rules(entities, associations, inheritances))
            
            self.validation_completed.emit([r.to_dict() for r in results])
            return results
            
        except Exception as e:
            self.validation_error.emit(f"Erreur lors de la validation: {e}")
            return []
    
    def _validate_entities(self, entities: List[Dict]) -> List[ValidationResult]:
        """Valide les entités"""
        results = []
        
        # Vérifier les noms uniques
        entity_names = []
        for entity in entities:
            name = entity.get("name", "")
            if name in entity_names:
                results.append(ValidationResult(
                    ValidationRule.ENTITY_NAME_UNIQUE,
                    ValidationLevel.ERROR,
                    f"Nom d'entité dupliqué: {name}",
                    entity.get("id")
                ))
            else:
                entity_names.append(name)
            
            # Vérifier qu'une entité a des attributs
            if not entity.get("attributes"):
                results.append(ValidationResult(
                    ValidationRule.ENTITY_HAS_ATTRIBUTES,
                    ValidationLevel.WARNING,
                    f"L'entité '{name}' n'a pas d'attributs",
                    entity.get("id")
                ))
            
            # Vérifier la convention de nommage
            if not self._check_naming_convention(name):
                results.append(ValidationResult(
                    ValidationRule.NAMING_CONVENTION,
                    ValidationLevel.WARNING,
                    f"Le nom '{name}' ne suit pas la convention de nommage",
                    entity.get("id")
                ))
        
        return results
    
    def _validate_associations(self, associations: List[Dict], entities: List[Dict]) -> List[ValidationResult]:
        """Valide les associations"""
        results = []
        
        # Vérifier les noms uniques
        association_names = []
        for association in associations:
            name = association.get("name", "")
            if name in association_names:
                results.append(ValidationResult(
                    ValidationRule.ASSOCIATION_NAME_UNIQUE,
                    ValidationLevel.ERROR,
                    f"Nom d'association dupliqué: {name}",
                    association.get("id")
                ))
            else:
                association_names.append(name)
            
            # Vérifier qu'une association a des entités liées
            if not association.get("entities"):
                results.append(ValidationResult(
                    ValidationRule.ASSOCIATION_HAS_ENTITIES,
                    ValidationLevel.ERROR,
                    f"L'association '{name}' n'a pas d'entités liées",
                    association.get("id")
                ))
            
            # Vérifier les cardinalités
            cardinalities = association.get("cardinalities", {})
            for entity_name, cardinality in cardinalities.items():
                if not self._is_valid_cardinality(cardinality):
                    results.append(ValidationResult(
                        ValidationRule.CARDINALITY_VALID,
                        ValidationLevel.ERROR,
                        f"Cardinalité invalide '{cardinality}' pour l'entité '{entity_name}'",
                        association.get("id")
                    ))
        
        return results
    
    def _validate_inheritances(self, inheritances: List[Dict], entities: List[Dict]) -> List[ValidationResult]:
        """Valide les héritages"""
        results = []
        
        # Vérifier les cycles d'héritage
        entity_names = [e.get("name") for e in entities]
        for inheritance in inheritances:
            parent = inheritance.get("parent")
            child = inheritance.get("child")
            
            if parent and child:
                if self._has_inheritance_cycle(parent, child, inheritances):
                    results.append(ValidationResult(
                        ValidationRule.INHERITANCE_CYCLE,
                        ValidationLevel.ERROR,
                        f"Cycle d'héritage détecté entre '{parent}' et '{child}'",
                        inheritance.get("id")
                    ))
        
        return results
    
    def _validate_global_rules(self, entities: List[Dict], associations: List[Dict], 
                              inheritances: List[Dict]) -> List[ValidationResult]:
        """Valide les règles globales"""
        results = []
        
        # Vérifier qu'il y a au moins une entité
        if not entities:
            results.append(ValidationResult(
                ValidationRule.ENTITY_HAS_ATTRIBUTES,
                ValidationLevel.ERROR,
                "Le modèle doit contenir au moins une entité"
            ))
        
        # Vérifier la cohérence des références
        entity_names = [e.get("name") for e in entities]
        for association in associations:
            for entity_name in association.get("entities", []):
                if entity_name not in entity_names:
                    results.append(ValidationResult(
                        ValidationRule.ASSOCIATION_HAS_ENTITIES,
                        ValidationLevel.ERROR,
                        f"L'entité '{entity_name}' référencée dans l'association '{association.get('name')}' n'existe pas"
                    ))
        
        return results
    
    def _check_naming_convention(self, name: str) -> bool:
        """Vérifie la convention de nommage"""
        if not name:
            return False
        
        # Règles de base
        if not name[0].isalpha():
            return False
        
        # Pas de caractères spéciaux
        if not name.replace("_", "").replace("-", "").isalnum():
            return False
        
        return True
    
    def _is_valid_cardinality(self, cardinality: str) -> bool:
        """Vérifie si une cardinalité est valide"""
        valid_cardinalities = ["0,1", "1,1", "0,N", "1,N", "N,1", "N,N"]
        return cardinality in valid_cardinalities
    
    def _has_inheritance_cycle(self, parent: str, child: str, inheritances: List[Dict]) -> bool:
        """Détecte les cycles d'héritage"""
        # Implémentation simplifiée - à améliorer
        visited = set()
        
        def dfs(current: str, target: str) -> bool:
            if current == target:
                return True
            if current in visited:
                return False
            
            visited.add(current)
            
            for inheritance in inheritances:
                if inheritance.get("parent") == current:
                    if dfs(inheritance.get("child"), target):
                        return True
            
            return False
        
        return dfs(child, parent)
    
    def get_validation_summary(self, results: List[ValidationResult]) -> Dict[str, int]:
        """Retourne un résumé de la validation"""
        summary = {
            "total": len(results),
            "errors": len([r for r in results if r.level == ValidationLevel.ERROR]),
            "warnings": len([r for r in results if r.level == ValidationLevel.WARNING]),
            "info": len([r for r in results if r.level == ValidationLevel.INFO])
        }
        return summary
    
    def is_model_valid(self, results: List[ValidationResult]) -> bool:
        """Vérifie si le modèle est valide (pas d'erreurs)"""
        return not any(r.level == ValidationLevel.ERROR for r in results)
