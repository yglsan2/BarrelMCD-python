#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Gestionnaire d'historique pour BarrelMCD
Système Undo/Redo complet
"""

from PyQt5.QtCore import QObject, pyqtSignal
from enum import Enum
import copy
import json
from typing import Dict, List, Any, Optional

class ActionType(Enum):
    """Types d'actions supportées"""
    CREATE_ENTITY = "create_entity"
    DELETE_ENTITY = "delete_entity"
    MODIFY_ENTITY = "modify_entity"
    CREATE_ASSOCIATION = "create_association"
    DELETE_ASSOCIATION = "delete_association"
    MODIFY_ASSOCIATION = "modify_association"
    CREATE_INHERITANCE = "create_inheritance"
    DELETE_INHERITANCE = "delete_inheritance"
    ADD_ATTRIBUTE = "add_attribute"
    REMOVE_ATTRIBUTE = "remove_attribute"
    MODIFY_ATTRIBUTE = "modify_attribute"
    MOVE_ELEMENT = "move_element"
    MODIFY_CARDINALITY = "modify_cardinality"

class HistoryAction:
    """Représente une action dans l'historique"""
    
    def __init__(self, action_type: ActionType, data: Dict[str, Any], description: str = ""):
        self.action_type = action_type
        self.data = data
        self.description = description
        self.timestamp = None  # Sera défini lors de l'ajout
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit l'action en dictionnaire pour sauvegarde"""
        return {
            "action_type": self.action_type.value,
            "data": self.data,
            "description": self.description,
            "timestamp": self.timestamp
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'HistoryAction':
        """Crée une action depuis un dictionnaire"""
        action = cls(
            ActionType(data["action_type"]),
            data["data"],
            data.get("description", "")
        )
        action.timestamp = data.get("timestamp")
        return action

class HistoryManager(QObject):
    """Gestionnaire d'historique avec Undo/Redo"""
    
    # Signaux
    history_changed = pyqtSignal()  # Émis quand l'historique change
    can_undo_changed = pyqtSignal(bool)  # Émis quand l'état Undo change
    can_redo_changed = pyqtSignal(bool)  # Émis quand l'état Redo change
    
    def __init__(self, max_actions: int = 100):
        super().__init__()
        self.max_actions = max_actions
        self.undo_stack: List[HistoryAction] = []
        self.redo_stack: List[HistoryAction] = []
        self.is_undoing = False
        self.is_redoing = False
        
    def add_action(self, action: HistoryAction) -> None:
        """Ajoute une action à l'historique"""
        if self.is_undoing or self.is_redoing:
            return
            
        # Vider la pile Redo quand une nouvelle action est ajoutée
        self.redo_stack.clear()
        
        # Ajouter l'action à la pile Undo
        self.undo_stack.append(action)
        
        # Limiter la taille de la pile
        if len(self.undo_stack) > self.max_actions:
            self.undo_stack.pop(0)
        
        self._emit_changes()
    
    def undo(self) -> Optional[HistoryAction]:
        """Annule la dernière action"""
        if not self.can_undo():
            return None
            
        self.is_undoing = True
        action = self.undo_stack.pop()
        self.redo_stack.append(action)
        self.is_undoing = False
        
        self._emit_changes()
        return action
    
    def redo(self) -> Optional[HistoryAction]:
        """Refait la dernière action annulée"""
        if not self.can_redo():
            return None
            
        self.is_redoing = True
        action = self.redo_stack.pop()
        self.undo_stack.append(action)
        self.is_redoing = False
        
        self._emit_changes()
        return action
    
    def can_undo(self) -> bool:
        """Vérifie si on peut annuler"""
        return len(self.undo_stack) > 0
    
    def can_redo(self) -> bool:
        """Vérifie si on peut refaire"""
        return len(self.redo_stack) > 0
    
    def clear(self) -> None:
        """Vide l'historique"""
        self.undo_stack.clear()
        self.redo_stack.clear()
        self._emit_changes()
    
    def get_undo_description(self) -> str:
        """Retourne la description de la prochaine action à annuler"""
        if self.can_undo():
            return self.undo_stack[-1].description
        return ""
    
    def get_redo_description(self) -> str:
        """Retourne la description de la prochaine action à refaire"""
        if self.can_redo():
            return self.redo_stack[-1].description
        return ""
    
    def _emit_changes(self) -> None:
        """Émet les signaux de changement"""
        self.history_changed.emit()
        self.can_undo_changed.emit(self.can_undo())
        self.can_redo_changed.emit(self.can_redo())
    
    def save_to_file(self, filename: str) -> bool:
        """Sauvegarde l'historique dans un fichier"""
        try:
            data = {
                "undo_stack": [action.to_dict() for action in self.undo_stack],
                "redo_stack": [action.to_dict() for action in self.redo_stack]
            }
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Erreur lors de la sauvegarde de l'historique: {e}")
            return False
    
    def load_from_file(self, filename: str) -> bool:
        """Charge l'historique depuis un fichier"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.undo_stack = [HistoryAction.from_dict(action_data) 
                             for action_data in data.get("undo_stack", [])]
            self.redo_stack = [HistoryAction.from_dict(action_data) 
                             for action_data in data.get("redo_stack", [])]
            
            self._emit_changes()
            return True
        except Exception as e:
            print(f"Erreur lors du chargement de l'historique: {e}")
            return False

# Actions spécifiques pour faciliter la création
class HistoryActions:
    """Actions prédéfinies pour l'historique"""
    
    @staticmethod
    def create_entity(entity_data: Dict[str, Any]) -> HistoryAction:
        """Action de création d'entité"""
        return HistoryAction(
            ActionType.CREATE_ENTITY,
            entity_data,
            f"Création de l'entité '{entity_data.get('name', 'Nouvelle entité')}'"
        )
    
    @staticmethod
    def delete_entity(entity_data: Dict[str, Any]) -> HistoryAction:
        """Action de suppression d'entité"""
        return HistoryAction(
            ActionType.DELETE_ENTITY,
            entity_data,
            f"Suppression de l'entité '{entity_data.get('name', 'Entité')}'"
        )
    
    @staticmethod
    def modify_entity(old_data: Dict[str, Any], new_data: Dict[str, Any]) -> HistoryAction:
        """Action de modification d'entité"""
        return HistoryAction(
            ActionType.MODIFY_ENTITY,
            {"old": old_data, "new": new_data},
            f"Modification de l'entité '{new_data.get('name', 'Entité')}'"
        )
    
    @staticmethod
    def create_association(association_data: Dict[str, Any]) -> HistoryAction:
        """Action de création d'association"""
        return HistoryAction(
            ActionType.CREATE_ASSOCIATION,
            association_data,
            f"Création de l'association '{association_data.get('name', 'Nouvelle association')}'"
        )
    
    @staticmethod
    def delete_association(association_data: Dict[str, Any]) -> HistoryAction:
        """Action de suppression d'association"""
        return HistoryAction(
            ActionType.DELETE_ASSOCIATION,
            association_data,
            f"Suppression de l'association '{association_data.get('name', 'Association')}'"
        )
    
    @staticmethod
    def move_element(element_data: Dict[str, Any], old_pos: Dict[str, float], new_pos: Dict[str, float]) -> HistoryAction:
        """Action de déplacement d'élément"""
        return HistoryAction(
            ActionType.MOVE_ELEMENT,
            {
                "element": element_data,
                "old_position": old_pos,
                "new_position": new_pos
            },
            f"Déplacement de '{element_data.get('name', 'Élément')}'"
        )
