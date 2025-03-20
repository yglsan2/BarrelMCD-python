from PyQt5.QtWidgets import QGraphicsScene, QGraphicsItem, QGraphicsTextItem
from PyQt5.QtCore import Qt, QRectF, QPointF
from PyQt5.QtGui import QPen, QBrush, QColor, QFont, QPainter, QPainterPath
import numpy as np

class MCDDrawer:
    """Classe pour dessiner le MCD avec un rendu professionnel"""
    
    COLORS = {
        "entity": QColor("#2196F3"),  # Bleu material design
        "weak_entity": QColor("#90CAF9"),  # Bleu clair
        "relation": QColor("#4CAF50"),  # Vert material design
        "inheritance": QColor("#FF9800"),  # Orange
        "text": QColor("#212121"),  # Gris foncé
        "border": QColor("#757575"),  # Gris
        "background": QColor("#FFFFFF"),  # Blanc
        "grid": QColor("#EEEEEE")  # Gris très clair
    }
    
    FONTS = {
        "entity_name": QFont("Arial", 12, QFont.Bold),
        "attribute": QFont("Arial", 10),
        "relation": QFont("Arial", 11, QFont.Bold),
        "cardinality": QFont("Arial", 10, QFont.Bold)
    }
    
    def __init__(self, scene: QGraphicsScene):
        self.scene = scene
        self.entity_boxes = {}
        self.relation_boxes = {}
        self.layout = self._initialize_layout()
        
    def _initialize_layout(self) -> dict:
        """Initialise la disposition du MCD."""
        return {
            "margin": 50,
            "entity_width": 200,
            "entity_min_height": 100,
            "relation_size": 100,
            "spacing": 150,
            "grid_size": 20
        }
        
    def draw_mcd(self, mcd_structure: dict):
        """Dessine le MCD complet."""
        self.scene.clear()
        self.entity_boxes.clear()
        self.relation_boxes.clear()
        
        # 1. Dessiner la grille de fond
        self._draw_grid()
        
        # 2. Calculer les positions optimales
        positions = self._calculate_optimal_positions(mcd_structure)
        
        # 3. Dessiner les entités
        for entity_name, entity in mcd_structure["entities"].items():
            pos = positions[entity_name]
            self._draw_entity(entity, pos)
            
        # 4. Dessiner les relations et associations
        for relation in mcd_structure["relations"]:
            self._draw_relation(relation, positions)
            
        # 5. Dessiner les héritages
        for entity_name, entity in mcd_structure["entities"].items():
            if "herite_de" in entity:
                self._draw_inheritance(entity_name, entity["herite_de"], positions)
                
    def _draw_grid(self):
        """Dessine une grille de fond."""
        size = 5000  # Taille arbitraire de la grille
        pen = QPen(self.COLORS["grid"])
        pen.setStyle(Qt.DotLine)
        
        for x in range(0, size, self.layout["grid_size"]):
            self.scene.addLine(x, 0, x, size, pen)
        for y in range(0, size, self.layout["grid_size"]):
            self.scene.addLine(0, y, size, y, pen)
            
    def _calculate_optimal_positions(self, mcd_structure: dict) -> dict:
        """Calcule les positions optimales des entités."""
        # Algorithme de force dirigée simplifié
        positions = {}
        current_x = self.layout["margin"]
        current_y = self.layout["margin"]
        max_height = 0
        
        # Grouper les entités liées
        groups = self._group_related_entities(mcd_structure)
        
        for group in groups:
            group_width = 0
            for entity_name in group:
                # Calculer la position
                positions[entity_name] = QPointF(current_x + group_width, current_y)
                
                # Mettre à jour les dimensions
                entity_height = self._calculate_entity_height(mcd_structure["entities"][entity_name])
                max_height = max(max_height, entity_height)
                group_width += self.layout["entity_width"] + self.layout["spacing"]
                
            current_y += max_height + self.layout["spacing"]
            max_height = 0
            
        return positions
        
    def _group_related_entities(self, mcd_structure: dict) -> list:
        """Groupe les entités liées ensemble."""
        groups = []
        used_entities = set()
        
        for relation in mcd_structure["relations"]:
            current_group = set()
            current_group.add(relation["source"])
            current_group.add(relation["target"])
            
            # Fusionner avec les groupes existants qui partagent des entités
            for group in groups[:]:
                if current_group & group:
                    current_group |= group
                    groups.remove(group)
                    
            groups.append(current_group)
            used_entities |= current_group
            
        # Ajouter les entités isolées
        for entity_name in mcd_structure["entities"]:
            if entity_name not in used_entities:
                groups.append({entity_name})
                
        return groups
        
    def _draw_entity(self, entity: dict, position: QPointF):
        """Dessine une entité avec ses attributs."""
        # Calculer la hauteur en fonction des attributs
        height = self._calculate_entity_height(entity)
        
        # Créer le rectangle de l'entité
        rect = QRectF(position.x(), position.y(), 
                     self.layout["entity_width"], height)
        
        # Dessiner le rectangle
        box = self.scene.addRect(rect, 
            QPen(self.COLORS["border"]),
            QBrush(self.COLORS["entity"] if not entity.get("is_weak") 
                  else self.COLORS["weak_entity"]))
        
        # Ajouter le nom de l'entité
        name_text = self.scene.addText(entity["name"], self.FONTS["entity_name"])
        name_text.setDefaultTextColor(self.COLORS["text"])
        name_text.setPos(
            position.x() + (self.layout["entity_width"] - name_text.boundingRect().width()) / 2,
            position.y() + 5
        )
        
        # Dessiner la ligne de séparation
        self.scene.addLine(
            position.x(), position.y() + 30,
            position.x() + self.layout["entity_width"], position.y() + 30,
            QPen(self.COLORS["border"])
        )
        
        # Dessiner les attributs
        y_offset = 40
        for attr in entity["attributes"]:
            self._draw_attribute(attr, position, y_offset)
            y_offset += 20
            
        # Stocker la référence du rectangle
        self.entity_boxes[entity["name"]] = box
        
    def _draw_attribute(self, attribute: dict, entity_pos: QPointF, y_offset: float):
        """Dessine un attribut d'entité."""
        # Préparer le texte de l'attribut
        text = f"{attribute['name']}: {attribute['type']}"
        if attribute.get("primary_key"):
            text = "🔑 " + text
        elif attribute.get("foreign_key"):
            text = "🔗 " + text
        
        # Créer le texte
        attr_text = self.scene.addText(text, self.FONTS["attribute"])
        attr_text.setDefaultTextColor(self.COLORS["text"])
        attr_text.setPos(
            entity_pos.x() + 10,
            entity_pos.y() + y_offset
        )
        
    def _draw_relation(self, relation: dict, positions: dict):
        """Dessine une relation entre deux entités."""
        source_box = self.entity_boxes[relation["source"]]
        target_box = self.entity_boxes[relation["target"]]
        
        # Calculer les points de connexion
        source_point = self._calculate_connection_point(source_box, target_box)
        target_point = self._calculate_connection_point(target_box, source_box)
        
        # Dessiner le losange de relation si nécessaire
        if relation["type"] == "MANY_TO_MANY":
            center = QPointF(
                (source_point.x() + target_point.x()) / 2,
                (source_point.y() + target_point.y()) / 2
            )
            self._draw_relation_diamond(relation, center)
            
        # Dessiner les lignes
        pen = QPen(self.COLORS["border"])
        pen.setWidth(2)
        self.scene.addLine(source_point.x(), source_point.y(),
                          target_point.x(), target_point.y(), pen)
        
        # Dessiner les cardinalités
        self._draw_cardinality(relation["source_cardinality"], source_point, center)
        self._draw_cardinality(relation["target_cardinality"], target_point, center)
        
    def _draw_relation_diamond(self, relation: dict, center: QPointF):
        """Dessine un losange de relation."""
        size = self.layout["relation_size"] / 2
        
        path = QPainterPath()
        path.moveTo(center.x(), center.y() - size/2)  # Haut
        path.lineTo(center.x() + size/2, center.y())  # Droite
        path.lineTo(center.x(), center.y() + size/2)  # Bas
        path.lineTo(center.x() - size/2, center.y())  # Gauche
        path.closeSubpath()
        
        # Dessiner le losange
        self.scene.addPath(path, 
            QPen(self.COLORS["border"]),
            QBrush(self.COLORS["relation"]))
            
        # Ajouter le nom de la relation
        text = self.scene.addText(relation.get("name", ""), self.FONTS["relation"])
        text.setDefaultTextColor(self.COLORS["text"])
        text.setPos(
            center.x() - text.boundingRect().width()/2,
            center.y() - text.boundingRect().height()/2
        )
        
    def _draw_cardinality(self, cardinality: str, point: QPointF, center: QPointF):
        """Dessine une cardinalité."""
        # Calculer la position du texte
        angle = self._calculate_angle(point, center)
        offset = 20
        text_pos = QPointF(
            point.x() + offset * np.cos(angle + np.pi/2),
            point.y() + offset * np.sin(angle + np.pi/2)
        )
        
        # Créer le texte
        text = self.scene.addText(cardinality, self.FONTS["cardinality"])
        text.setDefaultTextColor(self.COLORS["text"])
        text.setPos(text_pos)
        
    def _draw_inheritance(self, child: str, parent: str, positions: dict):
        """Dessine une relation d'héritage."""
        child_box = self.entity_boxes[child]
        parent_box = self.entity_boxes[parent]
        
        # Calculer les points de connexion
        child_point = self._calculate_connection_point(child_box, parent_box)
        parent_point = self._calculate_connection_point(parent_box, child_box)
        
        # Dessiner le triangle d'héritage
        triangle_size = 20
        angle = self._calculate_angle(parent_point, child_point)
        
        triangle = QPainterPath()
        triangle.moveTo(parent_point.x(), parent_point.y())
        triangle.lineTo(parent_point.x() + triangle_size * np.cos(angle + np.pi/6),
                       parent_point.y() + triangle_size * np.sin(angle + np.pi/6))
        triangle.lineTo(parent_point.x() + triangle_size * np.cos(angle - np.pi/6),
                       parent_point.y() + triangle_size * np.sin(angle - np.pi/6))
        triangle.closeSubpath()
        
        self.scene.addPath(triangle,
            QPen(self.COLORS["border"]),
            QBrush(self.COLORS["inheritance"]))
            
        # Dessiner la ligne
        pen = QPen(self.COLORS["border"])
        pen.setWidth(2)
        self.scene.addLine(child_point.x(), child_point.y(),
                          parent_point.x(), parent_point.y(), pen)
        
    def _calculate_entity_height(self, entity: dict) -> float:
        """Calcule la hauteur nécessaire pour une entité."""
        return max(
            self.layout["entity_min_height"],
            40 + 20 * len(entity["attributes"])  # 40 pour le header, 20 par attribut
        )
        
    def _calculate_connection_point(self, source: QGraphicsItem, target: QGraphicsItem) -> QPointF:
        """Calcule le point de connexion optimal entre deux éléments."""
        source_rect = source.boundingRect()
        target_rect = target.boundingRect()
        
        source_center = source.pos() + QPointF(source_rect.width()/2, source_rect.height()/2)
        target_center = target.pos() + QPointF(target_rect.width()/2, target_rect.height()/2)
        
        angle = self._calculate_angle(source_center, target_center)
        
        # Calculer l'intersection avec le rectangle
        if abs(np.cos(angle)) > abs(np.sin(angle)):
            # Intersection horizontale
            x = source_center.x() + np.sign(np.cos(angle)) * source_rect.width()/2
            y = source_center.y() + np.tan(angle) * source_rect.width()/2
        else:
            # Intersection verticale
            x = source_center.x() + np.cos(angle)/np.sin(angle) * source_rect.height()/2
            y = source_center.y() + np.sign(np.sin(angle)) * source_rect.height()/2
            
        return QPointF(x, y)
        
    def _calculate_angle(self, p1: QPointF, p2: QPointF) -> float:
        """Calcule l'angle entre deux points."""
        return np.arctan2(p2.y() - p1.y(), p2.x() - p1.x()) 