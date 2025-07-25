#!/usr/bin/env python3

from enum import Enum
# -*- coding: utf-8 -*-

"""
Gestionnaire de raccourcis clavier pour BarrelMCD
"""

from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QShortcut, QApplication
from PyQt5.QtGui import QKeySequence
from typing import Dict, Callable, Any

class ShortcutManager(QObject):
    """Gestionnaire de raccourcis clavier"""
    
    # Signaux
    shortcut_triggered = pyqtSignal(str)  # Émis quand un raccourci est déclenché
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.shortcuts: Dict[str, QShortcut] = {}
        self.actions: Dict[str, Callable] = {}
        
    def register_shortcut(self, key: str, action: Callable, description: str = "") -> bool:
        """Enregistre un raccourci clavier"""
        try:
            shortcut = QShortcut(QKeySequence(key), self.parent())
            shortcut.activated.connect(action)
            self.shortcuts[key] = shortcut
            self.actions[key] = action
            return True
        except Exception as e:
            print(f"Erreur lors de l'enregistrement du raccourci {key}: {e}")
            return False
    
    def unregister_shortcut(self, key: str) -> bool:
        """Désenregistre un raccourci clavier"""
        if key in self.shortcuts:
            shortcut = self.shortcuts.pop(key)
            shortcut.deleteLater()
            self.actions.pop(key, None)
            return True
        return False
    
    def get_shortcut_list(self) -> Dict[str, str]:
        """Retourne la liste des raccourcis enregistrés"""
        return {key: action.__name__ for key, action in self.actions.items()}
    
    def clear_all(self) -> None:
        """Efface tous les raccourcis"""
        for shortcut in self.shortcuts.values():
            shortcut.deleteLater()
        self.shortcuts.clear()
        self.actions.clear()

# Raccourcis prédéfinis
class Shortcuts:
    """Raccourcis clavier standard"""
    
    # Fichier
    SAVE = "Ctrl+S"
    OPEN = "Ctrl+O"
    NEW = "Ctrl+N"
    SAVE_AS = "Ctrl+Shift+S"
    
    # Édition
    UNDO = "Ctrl+Z"
    REDO = "Ctrl+Y"
    COPY = "Ctrl+C"
    PASTE = "Ctrl+V"
    CUT = "Ctrl+X"
    DELETE = "Delete"
    SELECT_ALL = "Ctrl+A"
    
    # Vue
    ZOOM_IN = "Ctrl++"
    ZOOM_OUT = "Ctrl+-"
    ZOOM_RESET = "Ctrl+0"
    FIT_TO_VIEW = "Ctrl+F"
    
    # Outils
    TOOL_ENTITY = "E"
    TOOL_ASSOCIATION = "A"
    TOOL_INHERITANCE = "I"
    TOOL_SELECT = "S"
    
    # Génération
    GENERATE_SQL = "Ctrl+G"
    GENERATE_MLD = "Ctrl+M"
    EXPORT_SVG = "Ctrl+Shift+E"
    
    # Validation
    VALIDATE_MODEL = "Ctrl+V"
    
    # Aide
    HELP = "F1"
    ABOUT = "Ctrl+Shift+A"
