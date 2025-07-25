import json
import os
from datetime import datetime
from typing import Dict, Any, Optional
from PyQt6.QtCore import QObject, pyqtSignal

class BarFormat(QObject):
    """Gestionnaire du format de sauvegarde Barrel MCD (.bar)"""
    
    # Signaux
    save_started = pyqtSignal()
    save_finished = pyqtSignal(bool, str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.version = "1.0"
        self.magic_number = "BARREL_MCD"
        
    def save(self, data: Dict[str, Any], file_path: str) -> bool:
        """Sauvegarde les données au format .bar"""
        self.save_started.emit()
        
        try:
            # Créer le dossier parent si nécessaire
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Préparer les données de sauvegarde
            save_data = {
                "magic_number": self.magic_number,
                "version": self.version,
                "created_at": datetime.now().isoformat(),
                "last_modified": datetime.now().isoformat(),
                "data": data
            }
            
            # Sauvegarder dans un fichier temporaire d'abord
            temp_file = f"{file_path}.tmp"
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, ensure_ascii=False, indent=2)
                
            # Remplacer le fichier original
            if os.path.exists(file_path):
                os.replace(temp_file, file_path)
            else:
                os.rename(temp_file, file_path)
                
            self.save_finished.emit(True, "")
            return True
            
        except Exception as e:
            self.save_finished.emit(False, str(e))
            return False
            
    def load(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Charge les données depuis un fichier .bar"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                save_data = json.load(f)
                
            # Vérifier le magic number
            if save_data.get("magic_number") != self.magic_number:
                raise ValueError("Format de fichier invalide")
                
            # Vérifier la version
            if save_data.get("version") != self.version:
                raise ValueError(f"Version de fichier non supportée: {save_data.get('version')}")
                
            return save_data["data"]
            
        except Exception as e:
            return None
            
    def get_diagram_data(self, canvas) -> Dict[str, Any]:
        """Récupère les données du diagramme pour la sauvegarde"""
        data = {
            "entities": [],
            "associations": [],
            "relations": [],
            "view_settings": {
                "zoom": canvas.transform().m11(),
                "center": {
                    "x": canvas.horizontalScrollBar().value(),
                    "y": canvas.verticalScrollBar().value()
                },
                "show_grid": canvas.show_grid,
                "grid_size": canvas.grid_size
            }
        }
        
        # Collecter les entités
        for item in canvas.scene.items():
            if isinstance(item, Entity):
                data["entities"].append(item.to_dict())
            elif isinstance(item, Association):
                data["associations"].append(item.to_dict())
            elif isinstance(item, FlexibleArrow):
                data["relations"].append(item.to_dict())
                
        return data
        
    def load_diagram_data(self, canvas, data: Dict[str, Any]) -> bool:
        """Charge les données du diagramme depuis un fichier"""
        try:
            # Nettoyer la scène
            canvas.scene.clear()
            
            # Restaurer les paramètres de vue
            view_settings = data.get("view_settings", {})
            if view_settings:
                canvas.setTransform(QTransform().scale(
                    view_settings.get("zoom", 1.0),
                    view_settings.get("zoom", 1.0)
                ))
                canvas.horizontalScrollBar().setValue(view_settings.get("center", {}).get("x", 0))
                canvas.verticalScrollBar().setValue(view_settings.get("center", {}).get("y", 0))
                canvas.show_grid = view_settings.get("show_grid", True)
                canvas.grid_size = view_settings.get("grid_size", 20)
            
            # Créer un dictionnaire pour stocker les items par ID
            items_by_id = {}
            
            # Charger les entités
            for entity_data in data.get("entities", []):
                entity = Entity.from_dict(entity_data)
                canvas.scene.addItem(entity)
                items_by_id[entity.id] = entity
                
            # Charger les associations
            for assoc_data in data.get("associations", []):
                association = Association.from_dict(assoc_data)
                canvas.scene.addItem(association)
                items_by_id[association.id] = association
                
            # Charger les relations
            for relation_data in data.get("relations", []):
                source_id = relation_data.get("source_id")
                target_id = relation_data.get("target_id")
                
                if source_id in items_by_id and target_id in items_by_id:
                    arrow = FlexibleArrow.from_dict(
                        relation_data,
                        items_by_id[source_id],
                        items_by_id[target_id]
                    )
                    canvas.scene.addItem(arrow)
                    
            return True
            
        except Exception as e:
            return False 