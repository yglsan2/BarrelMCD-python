#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Gestionnaire de presse-papiers pour BarrelMCD
"""

from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QApplication
import json
from typing import Dict, List, Any, Optional

class ClipboardManager(QObject):
    """Gestionnaire de presse-papiers pour les éléments MCD"""
    
    # Signaux
    clipboard_changed = pyqtSignal()  # Émis quand le presse-papiers change
    
    def __init__(self):
        super().__init__()
        self.clipboard_data: Dict[str, Any] = {}
        self.clipboard_type: str = ""
        
    def copy_elements(self, elements: List[Dict[str, Any]], element_type: str) -> bool:
        """Copie des éléments dans le presse-papiers"""
        try:
            self.clipboard_data = {
                "type": element_type,
                "elements": elements,
                "count": len(elements)
            }
            self.clipboard_type = element_type
            
            # Copier aussi dans le presse-papiers système (format JSON)
            clipboard_text = json.dumps(self.clipboard_data, ensure_ascii=False, indent=2)
            QApplication.clipboard().setText(clipboard_text)
            
            self.clipboard_changed.emit()
            return True
        except Exception as e:
            print(f"Erreur lors de la copie: {e}")
            return False
    
    def paste_elements(self) -> Optional[Dict[str, Any]]:
        """Colle les éléments du presse-papiers"""
        if not self.clipboard_data:
            return None
        
        try:
            # Créer une copie des données pour éviter les références
            pasted_data = {
                "type": self.clipboard_type,
                "elements": self.clipboard_data.get("elements", []).copy(),
                "count": self.clipboard_data.get("count", 0)
            }
            
            # Modifier les noms pour éviter les conflits
            for element in pasted_data["elements"]:
                if "name" in element:
                    element["name"] = f"{element['name']}_copie"
                if "id" in element:
                    element["id"] = None  # Nouvel ID sera généré
            
            return pasted_data
        except Exception as e:
            print(f"Erreur lors du collage: {e}")
            return None
    
    def cut_elements(self, elements: List[Dict[str, Any]], element_type: str) -> bool:
        """Coupe des éléments (copie + suppression)"""
        if self.copy_elements(elements, element_type):
            # Les éléments seront supprimés par l'appelant
            return True
        return False
    
    def has_data(self) -> bool:
        """Vérifie si le presse-papiers contient des données"""
        return bool(self.clipboard_data)
    
    def get_clipboard_type(self) -> str:
        """Retourne le type d'éléments dans le presse-papiers"""
        return self.clipboard_type
    
    def get_element_count(self) -> int:
        """Retourne le nombre d'éléments dans le presse-papiers"""
        return self.clipboard_data.get("count", 0)
    
    def clear(self) -> None:
        """Vide le presse-papiers"""
        self.clipboard_data = {}
        self.clipboard_type = ""
        self.clipboard_changed.emit()
    
    def get_clipboard_info(self) -> Dict[str, Any]:
        """Retourne les informations sur le contenu du presse-papiers"""
        return {
            "has_data": self.has_data(),
            "type": self.clipboard_type,
            "count": self.get_element_count(),
            "elements": self.clipboard_data.get("elements", [])
        }
