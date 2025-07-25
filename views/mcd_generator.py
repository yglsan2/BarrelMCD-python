from typing import Dict, List, Tuple
from PyQt5.QtWidgets import QGraphicsScene, QGraphicsView, QGraphicsItem
from PyQt5.QtCore import Qt, QRectF, QPointF
from PyQt5.QtGui import QPen, QBrush, QColor, QPainter, QFont
import pandas as pd

class MCDGenerator:
    """Générateur de MCD à partir d'un dictionnaire de données"""
    
    def __init__(self, model_manager):
        self.model_manager = model_manager
        self.semantic_analyzer = self.model_manager.cardinality_analyzer.semantic_analyzer
        self.data_analyzer = DataAnalyzer()
        self.scene = QGraphicsScene()
        self.entities = {}
        self.relations = []
        
    def generate_from_dict(self, data_dict: Dict) -> bool:
        """Génère un MCD à partir d'un dictionnaire de données."""
        try:
            # Analyser les données avec le nouvel analyseur
            mcd_structure = self.data_analyzer.analyze_data(
                database_schema=data_dict
            )
            
            # Créer les entités
            for name, entity in mcd_structure["entities"].items():
                self.entities[name] = entity
                self.model_manager.add_entity(
                    name,
                    entity["attributes"],
                    entity["primary_key"]
                )
                
            # Créer les relations
            self.relations = mcd_structure["relations"]
            for relation in self.relations:
                self.model_manager.add_relation(
                    relation["source"],
                    relation["target"],
                    RelationType[relation["type"]]
                )
                
            # Dessiner le MCD
            self._draw_mcd()
            
            return True
            
        except Exception as e:
            self.model_manager.error_occurred.emit(str(e))
            return False
            
    def generate_from_dataframes(self, data: Dict[str, pd.DataFrame]) -> bool:
        """Génère un MCD à partir de DataFrames pandas."""
        try:
            # Analyser les données avec le nouvel analyseur
            mcd_structure = self.data_analyzer.analyze_data(
                data=data
            )
            
            # Créer les entités
            for name, entity in mcd_structure["entities"].items():
                self.entities[name] = entity
                self.model_manager.add_entity(
                    name,
                    entity["attributes"],
                    entity["primary_key"]
                )
                
            # Créer les relations
            self.relations = mcd_structure["relations"]
            for relation in self.relations:
                self.model_manager.add_relation(
                    relation["source"],
                    relation["target"],
                    RelationType[relation["type"]]
                )
                
            # Dessiner le MCD
            self._draw_mcd()
            
            return True
            
        except Exception as e:
            self.model_manager.error_occurred.emit(str(e))
            return False
            
    def generate_from_text(self, text: str) -> bool:
        """Génère un MCD à partir d'une description textuelle."""
        try:
            # Analyser le texte avec le nouvel analyseur
            mcd_structure = self.data_analyzer.analyze_data(
                text=text
            )
            
            # Créer les entités
            for name, entity in mcd_structure["entities"].items():
                self.entities[name] = entity
                self.model_manager.add_entity(
                    name,
                    entity["attributes"],
                    entity["primary_key"]
                )
                
            # Créer les relations
            self.relations = mcd_structure["relations"]
            for relation in self.relations:
                self.model_manager.add_relation(
                    relation["source"],
                    relation["target"],
                    RelationType[relation["type"]]
                )
                
            # Dessiner le MCD
            self._draw_mcd()
            
            return True
            
        except Exception as e:
            self.model_manager.error_occurred.emit(str(e))
            return False
        
    def _draw_mcd(self):
        """Dessine le MCD dans la scène."""
        # Réinitialiser la scène
        self.scene.clear()
        
        # Configuration du dessin
        entity_width = 200
        entity_height = 100
        spacing = 150
        current_x = 0
        current_y = 0
        
        # Dessiner les entités
        entity_positions = {}
        for name, info in self.entities.items():
            # Créer le rectangle de l'entité
            rect = self.scene.addRect(
                current_x, current_y, 
                entity_width, entity_height,
                QPen(Qt.black),
                QBrush(Qt.white)
            )
            
            # Ajouter le nom de l'entité
            text = self.scene.addText(name)
            text.setPos(
                current_x + (entity_width - text.boundingRect().width()) / 2,
                current_y + 10
            )
            
            # Stocker la position
            entity_positions[name] = {
                "rect": rect,
                "center": QPointF(
                    current_x + entity_width/2,
                    current_y + entity_height/2
                )
            }
            
            # Mettre à jour la position pour la prochaine entité
            current_x += entity_width + spacing
            if current_x > 800:  # Nouvelle ligne après 4 entités
                current_x = 0
                current_y += entity_height + spacing
                
        # Dessiner les relations
        for relation in self.relations:
            source_pos = entity_positions[relation["source"]]["center"]
            target_pos = entity_positions[relation["target"]]["center"]
            
            # Dessiner la ligne
            line = self.scene.addLine(
                source_pos.x(), source_pos.y(),
                target_pos.x(), target_pos.y(),
                QPen(Qt.black)
            )
            
            # Ajouter les cardinalités
            mid_point = QPointF(
                (source_pos.x() + target_pos.x()) / 2,
                (source_pos.y() + target_pos.y()) / 2
            )
            
            # Cardinalité source
            source_card = self.scene.addText(
                self._get_cardinality_text(relation["type"], "source")
            )
            source_card.setPos(
                source_pos.x() + 10,
                source_pos.y() - 20
            )
            
            # Cardinalité cible
            target_card = self.scene.addText(
                self._get_cardinality_text(relation["type"], "target")
            )
            target_card.setPos(
                target_pos.x() - 30,
                target_pos.y() - 20
            )
            
    def _get_cardinality_text(self, relation_type: RelationType, side: str) -> str:
        """Retourne le texte de cardinalité pour une relation."""
        if relation_type == RelationType.ONE_TO_ONE:
            return "1,1"
        elif relation_type == RelationType.ONE_TO_MANY:
            return "1,1" if side == "source" else "0,n"
        elif relation_type == RelationType.MANY_TO_ONE:
            return "0,n" if side == "source" else "1,1"
        elif relation_type == RelationType.MANY_TO_MANY:
            return "0,n"
        return ""

class MCDView(QGraphicsView):
    """Vue pour afficher le MCD"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setRenderHint(QPainter.Antialiasing)
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        
    def wheelEvent(self, event):
        """Gère le zoom avec la molette de la souris."""
        if event.modifiers() & Qt.ControlModifier:
            factor = 1.1
            if event.angleDelta().y() < 0:
                factor = 0.9
            self.scale(factor, factor)
        else:
            super().wheelEvent(event) 