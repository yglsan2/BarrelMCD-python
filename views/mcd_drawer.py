from PyQt5.QtWidgets import (
    QGraphicsScene, QGraphicsItem, QGraphicsTextItem,
    QGraphicsRectItem, QGraphicsLineItem, QGraphicsEllipseItem
)
from PyQt5.QtCore import Qt, QRectF, QPointF
from PyQt5.QtGui import QPen, QBrush, QColor, QFont
from typing import Dict, List, Tuple

class MCDDrawer:
    """Classe responsable du dessin du MCD."""
    
    def __init__(self):
        # Couleurs
        self.colors = {
            "entity": QColor("#E3F2FD"),
            "weak_entity": QColor("#FFECB3"),
            "relation": QColor("#F3E5F5"),
            "inheritance": QColor("#E8F5E9"),
            "text": QColor("#000000"),
            "border": QColor("#1976D2"),
            "background": QColor("#FFFFFF"),
            "grid": QColor("#EEEEEE")
        }
        
        # Styles de police
        self.fonts = {
            "entity_name": QFont("Arial", 12, QFont.Bold),
            "attribute": QFont("Arial", 10),
            "relation": QFont("Arial", 11),
            "cardinality": QFont("Arial", 9)
        }
        
        # Paramètres de mise en page
        self.margin = 50
        self.entity_width = 200
        self.entity_min_height = 100
        self.relation_size = 100
        self.spacing = 150
        self.grid_size = 20
    
    def draw_mcd(self, scene: QGraphicsScene, mcd: Dict) -> None:
        """
        Dessine le MCD dans la scène.
        
        Args:
            scene: La scène où dessiner
            mcd: Le MCD à dessiner
        """
        # Effacer la scène
        scene.clear()
        
        # Dessiner la grille
        self._draw_grid(scene)
        
        # Calculer les positions optimales
        positions = self._calculate_positions(mcd)
        
        # Dessiner les entités
        entity_boxes = {}
        for entity in mcd["entities"]:
            pos = positions[entity["name"]]
            box = self._draw_entity(scene, entity, pos)
            entity_boxes[entity["name"]] = box
        
        # Dessiner les relations
        for relation in mcd["relations"]:
            self._draw_relation(
                scene,
                relation,
                entity_boxes[relation["entity1"]],
                entity_boxes[relation["entity2"]]
            )
    
    def _draw_grid(self, scene: QGraphicsScene) -> None:
        """Dessine une grille de fond."""
        pen = QPen(self.colors["grid"])
        pen.setStyle(Qt.DotLine)
        
        # Obtenir les dimensions de la scène
        rect = scene.sceneRect()
        
        # Lignes verticales
        x = rect.left()
        while x <= rect.right():
            line = QGraphicsLineItem(x, rect.top(), x, rect.bottom())
            line.setPen(pen)
            scene.addItem(line)
            x += self.grid_size
        
        # Lignes horizontales
        y = rect.top()
        while y <= rect.bottom():
            line = QGraphicsLineItem(rect.left(), y, rect.right(), y)
            line.setPen(pen)
            scene.addItem(line)
            y += self.grid_size
    
    def _calculate_positions(self, mcd: Dict) -> Dict[str, QPointF]:
        """Calcule les positions optimales des entités."""
        positions = {}
        x = self.margin
        y = self.margin
        
        # Pour l'instant, placement simple en grille
        max_height = 0
        for entity in mcd["entities"]:
            positions[entity["name"]] = QPointF(x, y)
            
            # Calculer la hauteur de l'entité
            height = self.entity_min_height
            height += len(entity["attributes"]) * 20
            max_height = max(max_height, height)
            
            x += self.entity_width + self.spacing
            if x > 800:  # Largeur maximale
                x = self.margin
                y += max_height + self.spacing
                max_height = 0
        
        return positions
    
    def _draw_entity(self, scene: QGraphicsScene, entity: Dict, pos: QPointF) -> QRectF:
        """
        Dessine une entité.
        
        Returns:
            QRectF: La boîte englobante de l'entité
        """
        # Calculer la hauteur
        height = self.entity_min_height
        height += len(entity["attributes"]) * 20
        
        # Dessiner le rectangle
        rect = QRectF(pos.x(), pos.y(), self.entity_width, height)
        box = QGraphicsRectItem(rect)
        box.setBrush(QBrush(self.colors["entity"]))
        box.setPen(QPen(self.colors["border"]))
        scene.addItem(box)
        
        # Nom de l'entité
        name = QGraphicsTextItem(entity["name"])
        name.setFont(self.fonts["entity_name"])
        name.setDefaultTextColor(self.colors["text"])
        name.setPos(
            pos.x() + (self.entity_width - name.boundingRect().width()) / 2,
            pos.y() + 10
        )
        scene.addItem(name)
        
        # Ligne de séparation
        separator = QGraphicsLineItem(
            pos.x(), pos.y() + 40,
            pos.x() + self.entity_width, pos.y() + 40
        )
        separator.setPen(QPen(self.colors["border"]))
        scene.addItem(separator)
        
        # Attributs
        y = pos.y() + 50
        for attr in entity["attributes"]:
            text = f"{'# ' if attr['is_pk'] else ''}{attr['name']}: {attr['type']}"
            attr_item = QGraphicsTextItem(text)
            attr_item.setFont(self.fonts["attribute"])
            attr_item.setDefaultTextColor(self.colors["text"])
            attr_item.setPos(pos.x() + 10, y)
            scene.addItem(attr_item)
            y += 20
        
        return rect
    
    def _draw_relation(
        self,
        scene: QGraphicsScene,
        relation: Dict,
        entity1_box: QRectF,
        entity2_box: QRectF
    ) -> None:
        """Dessine une relation entre deux entités."""
        # Calculer les points de connexion
        start = self._calculate_connection_point(entity1_box, entity2_box.center())
        end = self._calculate_connection_point(entity2_box, entity1_box.center())
        
        # Dessiner la ligne
        line = QGraphicsLineItem(
            start.x(), start.y(),
            end.x(), end.y()
        )
        line.setPen(QPen(self.colors["border"]))
        scene.addItem(line)
        
        # Point central pour le losange de relation
        center = QPointF(
            (start.x() + end.x()) / 2,
            (start.y() + end.y()) / 2
        )
        
        # Dessiner le losange
        diamond = self._create_diamond(center, self.relation_size / 2)
        diamond.setBrush(QBrush(self.colors["relation"]))
        diamond.setPen(QPen(self.colors["border"]))
        scene.addItem(diamond)
        
        # Nom de la relation
        name = QGraphicsTextItem(relation["name"])
        name.setFont(self.fonts["relation"])
        name.setDefaultTextColor(self.colors["text"])
        name.setPos(
            center.x() - name.boundingRect().width() / 2,
            center.y() - name.boundingRect().height() / 2
        )
        scene.addItem(name)
        
        # Cardinalités
        card1, card2 = relation["cardinality"].split(":")
        self._draw_cardinality(scene, start, center, card1)
        self._draw_cardinality(scene, end, center, card2)
    
    def _calculate_connection_point(self, box: QRectF, target: QPointF) -> QPointF:
        """Calcule le point de connexion sur le bord d'une entité."""
        center = box.center()
        
        # Vecteur de direction
        dx = target.x() - center.x()
        dy = target.y() - center.y()
        
        # Intersection avec le rectangle
        if abs(dx) * box.height() > abs(dy) * box.width():
            # Intersection avec les côtés verticaux
            x = box.x() if dx < 0 else box.x() + box.width()
            y = center.y() + dy * (x - center.x()) / dx
        else:
            # Intersection avec les côtés horizontaux
            y = box.y() if dy < 0 else box.y() + box.height()
            x = center.x() + dx * (y - center.y()) / dy
        
        return QPointF(x, y)
    
    def _create_diamond(self, center: QPointF, size: float) -> QGraphicsItem:
        """Crée un losange pour représenter une relation."""
        diamond = QGraphicsEllipseItem(
            center.x() - size,
            center.y() - size,
            size * 2,
            size * 2
        )
        return diamond
    
    def _draw_cardinality(
        self,
        scene: QGraphicsScene,
        point: QPointF,
        center: QPointF,
        cardinality: str
    ) -> None:
        """Dessine une cardinalité."""
        # Calculer la position du texte
        dx = center.x() - point.x()
        dy = center.y() - point.y()
        distance = (dx * dx + dy * dy) ** 0.5
        
        if distance > 0:
            # Position à 20% de la distance du point de connexion
            x = point.x() + dx * 0.2 / distance
            y = point.y() + dy * 0.2 / distance
            
            # Créer le texte
            text = QGraphicsTextItem(cardinality)
            text.setFont(self.fonts["cardinality"])
            text.setDefaultTextColor(self.colors["text"])
            text.setPos(
                x - text.boundingRect().width() / 2,
                y - text.boundingRect().height() / 2
            )
            scene.addItem(text) 