#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Système de flèches hybride parfait
Combine le meilleur de Mocodo, Lucidchart, Draw.io et outils de référence MCD
"""

import math
import traceback
from enum import Enum
from PyQt5.QtWidgets import QGraphicsItem, QGraphicsPathItem
from PyQt5.QtCore import Qt, QRectF, QPointF, QLineF, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QPainter, QPen, QColor, QPainterPath, QBrush, QLinearGradient

class ArrowStyle(Enum):
    """Styles de flèches disponibles"""
    STRAIGHT = "straight"      # Mocodo - Ligne droite simple
    CURVED = "curved"          # Lucidchart - Courbe de Bézier élégante
    STEPPED = "stepped"        # Draw.io - Ligne en escalier
    ORTHOGONAL = "orthogonal"  # Ligne orthogonale
    SMART = "smart"            # Hybride - Détection automatique

class HybridArrow(QGraphicsPathItem):
    """Flèche hybride intelligente avec détection automatique du meilleur style"""
    
    def __init__(self, source: QGraphicsItem, target: QGraphicsItem, cardinality="1,N"):
        super().__init__()
        
        # Éléments source et cible
        self.source = source
        self.target = target
        self.cardinality = cardinality
        
        # Style et configuration
        self.style = ArrowStyle.SMART  # Détection automatique par défaut
        self.auto_style = True  # Détection automatique du style optimal
        
        # Configuration visuelle
        self.colors = {
            "line": QColor(100, 150, 255),      # Bleu moderne
            "arrow": QColor(255, 200, 100),     # Orange pour la pointe
            "cardinality": QColor(200, 200, 200) # Gris pour le texte
        }
        
        self.dimensions = {
            "line_width": 2.5,
            "arrow_size": 10,
            "cardinality_offset": 15
        }
        
        # Points de contrôle pour les courbes
        self.control_points = []
        self.path_cache = None
        self.last_update = 0
        
        # Animation
        self.animation = None
        self.setup_animation()
        
        # Configuration de base
        self.setZValue(-1)  # Sous les autres éléments
        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        
        # Calcul initial du chemin
        self.update_path()
        
    def setup_animation(self):
        """Configure l'animation de la flèche"""
        # Désactiver l'animation pour l'instant pour éviter l'erreur
        self.animation = None
        # self.animation = QPropertyAnimation(self, b"opacity")
        # self.animation.setDuration(300)
        # self.animation.setEasingCurve(QEasingCurve.OutCubic)
        
    def boundingRect(self) -> QRectF:
        """Calcule la zone englobante de la flèche"""
        if self.path_cache:
            rect = self.path_cache.boundingRect()
            # Ajouter de l'espace pour la cardinalité
            rect.adjust(-20, -20, 20, 20)
            return rect
        return QRectF()
        
    def shape(self) -> QPainterPath:
        """Retourne la forme de la flèche pour la détection de collision"""
        if self.path_cache:
            return self.path_cache
        return QPainterPath()
        
    def paint(self, painter: QPainter, option, widget):
        """Dessine la flèche avec le style approprié"""
        if not self.source or not self.target:
            return
            
        # Mettre à jour le chemin si nécessaire
        self.update_path()
        
        if not self.path_cache:
            return
            
        # Configuration du peintre
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Dessiner la ligne principale
        self.draw_main_line(painter)
        
        # Dessiner la pointe de la flèche
        self.draw_arrow_head(painter)
        
        # Dessiner la cardinalité
        self.draw_cardinality(painter)
        
    def update_path(self):
        """Met à jour le chemin de la flèche"""
        if not self.source or not self.target:
            return
            
        # Détecter le style optimal si nécessaire
        if self.auto_style:
            self.style = self.detect_optimal_style()
            
        # Calculer les points selon le style
        points = self.calculate_points()
        if not points or len(points) < 2:
            return
            
        # Créer le chemin
        self.path_cache = self.create_path_from_points(points)
        self.setPath(self.path_cache)
        
    def detect_optimal_style(self) -> ArrowStyle:
        """Détecte le style optimal selon la disposition des éléments"""
        if not self.source or not self.target:
            return ArrowStyle.STRAIGHT
            
        source_pos = self.source.scenePos()
        target_pos = self.target.scenePos()
        
        # Calculer la distance et l'angle
        dx = target_pos.x() - source_pos.x()
        dy = target_pos.y() - source_pos.y()
        distance = math.sqrt(dx*dx + dy*dy)
        angle = math.atan2(dy, dx)
        
        # Règles de détection
        if distance < 100:
            return ArrowStyle.STRAIGHT  # Court = ligne droite
        elif abs(angle) < math.pi/6 or abs(angle) > 5*math.pi/6:
            return ArrowStyle.ORTHOGONAL  # Horizontal = orthogonal
        elif abs(angle - math.pi/2) < math.pi/6 or abs(angle + math.pi/2) < math.pi/6:
            return ArrowStyle.ORTHOGONAL  # Vertical = orthogonal
        elif distance > 200:
            return ArrowStyle.CURVED  # Long = courbe
        else:
            return ArrowStyle.STEPPED  # Moyen = escalier
            
    def calculate_points(self) -> list:
        """Calcule les points selon le style choisi"""
        if not self.source or not self.target:
            return []
            
        source_center = self.get_element_center(self.source)
        target_center = self.get_element_center(self.target)
        
        if self.style == ArrowStyle.STRAIGHT:
            return self.calculate_straight_points(source_center, target_center)
        elif self.style == ArrowStyle.CURVED:
            return self.calculate_curved_points(source_center, target_center)
        elif self.style == ArrowStyle.STEPPED:
            return self.calculate_stepped_points(source_center, target_center)
        elif self.style == ArrowStyle.ORTHOGONAL:
            return self.calculate_orthogonal_points(source_center, target_center)
        else:
            return self.calculate_straight_points(source_center, target_center)
            
    def get_element_center(self, element: QGraphicsItem) -> QPointF:
        """Obtient le centre d'un élément"""
        pos = element.scenePos()
        rect = element.boundingRect()
        return QPointF(pos.x() + rect.width()/2, pos.y() + rect.height()/2)
        
    def calculate_straight_points(self, start: QPointF, end: QPointF) -> list:
        """Calcule les points pour une ligne droite (style Mocodo)"""
        # Points de départ et d'arrivée sur les bords
        start_point = self.get_border_point(start, end)
        end_point = self.get_border_point(end, start)
        
        return [start_point, end_point]
        
    def calculate_curved_points(self, start: QPointF, end: QPointF) -> list:
        """Calcule les points pour une courbe de Bézier (style Lucidchart)"""
        start_point = self.get_border_point(start, end)
        end_point = self.get_border_point(end, start)
        
        # Point de contrôle au milieu avec décalage
        mid_point = QPointF((start_point.x() + end_point.x()) / 2,
                           (start_point.y() + end_point.y()) / 2)
        
        # Décalage perpendiculaire pour la courbe
        dx = end_point.x() - start_point.x()
        dy = end_point.y() - start_point.y()
        distance = math.sqrt(dx*dx + dy*dy)
        
        if distance > 0:
            # Décalage proportionnel à la distance
            offset = min(distance * 0.3, 50)
            perpendicular = QPointF(-dy/distance * offset, dx/distance * offset)
            control_point = mid_point + perpendicular
        else:
            control_point = mid_point
            
        return [start_point, control_point, end_point]
        
    def calculate_stepped_points(self, start: QPointF, end: QPointF) -> list:
        """Calcule les points pour une ligne en escalier (style Draw.io)"""
        start_point = self.get_border_point(start, end)
        end_point = self.get_border_point(end, start)
        
        # Point intermédiaire au milieu
        mid_x = (start_point.x() + end_point.x()) / 2
        mid_y = (start_point.y() + end_point.y()) / 2
        
        return [start_point, QPointF(mid_x, start_point.y()), 
                QPointF(mid_x, end_point.y()), end_point]
                
    def calculate_orthogonal_points(self, start: QPointF, end: QPointF) -> list:
        """Calcule les points pour une ligne orthogonale"""
        start_point = self.get_border_point(start, end)
        end_point = self.get_border_point(end, start)
        
        # Déterminer si on va horizontalement ou verticalement en premier
        dx = abs(end_point.x() - start_point.x())
        dy = abs(end_point.y() - start_point.y())
        
        if dx > dy:
            # Horizontal en premier
            mid_point = QPointF(end_point.x(), start_point.y())
        else:
            # Vertical en premier
            mid_point = QPointF(start_point.x(), end_point.y())
            
        return [start_point, mid_point, end_point]
        
    def get_border_point(self, element_center: QPointF, direction_center: QPointF) -> QPointF:
        """Calcule le point sur le bord de l'élément dans la direction donnée"""
        # Calculer la direction
        dx = direction_center.x() - element_center.x()
        dy = direction_center.y() - element_center.y()
        distance = math.sqrt(dx*dx + dy*dy)
        
        if distance < 1:
            return element_center
            
        # Normaliser la direction
        direction = QPointF(dx/distance, dy/distance)
        
        # Trouver l'élément source ou target
        element = self.source if element_center == self.get_element_center(self.source) else self.target
        rect = element.boundingRect()
        
        # Rayon de l'élément
        radius = max(rect.width(), rect.height()) / 2
        
        # Point sur le bord
        border_point = QPointF(
            element_center.x() + direction.x() * radius,
            element_center.y() + direction.y() * radius
        )
        
        return border_point
        
    def create_path_from_points(self, points: list) -> QPainterPath:
        """Crée un chemin à partir des points calculés"""
        if not points or len(points) < 2:
            return QPainterPath()
            
        path = QPainterPath()
        path.moveTo(points[0])
        
        if len(points) == 2:
            # Ligne droite
            path.lineTo(points[1])
        elif len(points) == 3 and self.style == ArrowStyle.CURVED:
            # Courbe de Bézier
            path.quadTo(points[1], points[2])
        else:
            # Ligne brisée
            for i in range(1, len(points)):
                path.lineTo(points[i])
                
        return path
        
    def draw_main_line(self, painter: QPainter):
        """Dessine la ligne principale de la flèche"""
        if not self.path_cache:
            return
            
        # Créer un dégradé pour la ligne
        gradient = QLinearGradient(self.path_cache.boundingRect().topLeft(),
                                 self.path_cache.boundingRect().bottomRight())
        gradient.setColorAt(0, self.colors["line"])
        gradient.setColorAt(1, self.colors["line"].lighter(120))
        
        # Dessiner la ligne
        pen = QPen(gradient, self.dimensions["line_width"])
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(self.path_cache)
        
    def draw_arrow_head(self, painter: QPainter):
        """Dessine la pointe de la flèche"""
        if not self.path_cache:
            return
            
        # Obtenir le dernier segment de la ligne
        path_elements = self.path_cache.toSubpathPolygons()
        if not path_elements:
            return
            
        # Prendre le dernier polygone
        polygon = path_elements[-1]
        if len(polygon) < 2:
            return
            
        # Points pour la pointe de la flèche
        end_point = polygon[-1]
        control_point = polygon[-2] if len(polygon) > 1 else polygon[0]
        
        # Calculer la direction
        direction = QPointF(end_point.x() - control_point.x(),
                           end_point.y() - control_point.y())
        length = math.sqrt(direction.x() * direction.x() + direction.y() * direction.y())
        
        if length < 1:
            return
            
        # Normaliser
        direction = QPointF(direction.x() / length, direction.y() / length)
        
        # Vecteur perpendiculaire
        perpendicular = QPointF(-direction.y(), direction.x())
        
        # Points de la flèche
        arrow_size = self.dimensions["arrow_size"]
        point1 = QPointF(
            end_point.x() - direction.x() * arrow_size + perpendicular.x() * arrow_size/2,
            end_point.y() - direction.y() * arrow_size + perpendicular.y() * arrow_size/2
        )
        point2 = QPointF(
            end_point.x() - direction.x() * arrow_size - perpendicular.x() * arrow_size/2,
            end_point.y() - direction.y() * arrow_size - perpendicular.y() * arrow_size/2
        )
        
        # Dessiner la pointe
        arrow_path = QPainterPath()
        arrow_path.moveTo(end_point)
        arrow_path.lineTo(point1)
        arrow_path.moveTo(end_point)
        arrow_path.lineTo(point2)
        
        pen = QPen(self.colors["arrow"], self.dimensions["line_width"] + 1)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)
        painter.drawPath(arrow_path)
        
    def draw_cardinality(self, painter: QPainter):
        """Dessine la cardinalité"""
        if not self.cardinality or not self.path_cache:
            return
            
        # Position du texte au milieu de la ligne
        rect = self.path_cache.boundingRect()
        text_pos = QPointF(rect.center().x(), rect.center().y() - self.dimensions["cardinality_offset"])
        
        # Configuration du texte
        font = painter.font()
        font.setPointSize(8)
        font.setBold(True)
        painter.setFont(font)
        
        # Fond pour la lisibilité
        text_rect = painter.fontMetrics().boundingRect(self.cardinality)
        background_rect = QRectF(text_pos.x() - text_rect.width()/2 - 3,
                                text_pos.y() - text_rect.height()/2 - 2,
                                text_rect.width() + 6,
                                text_rect.height() + 4)
        
        painter.setBrush(QBrush(QColor(0, 0, 0, 180)))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(background_rect, 3, 3)
        
        # Texte
        painter.setPen(QPen(self.colors["cardinality"]))
        painter.drawText(text_pos, self.cardinality)
        
    def set_style(self, style: ArrowStyle):
        """Change le style de la flèche"""
        self.style = style
        self.auto_style = False
        self.update_path()
        
    def set_cardinality(self, cardinality: str):
        """Change la cardinalité"""
        self.cardinality = cardinality
        self.update()
        
    def set_colors(self, colors: dict):
        """Change les couleurs de la flèche"""
        self.colors.update(colors)
        self.update()
        
    def animate_appearance(self):
        """Anime l'apparition de la flèche"""
        # Désactiver l'animation pour l'instant
        pass
        # if self.animation:
        #     self.setOpacity(0)
        #     self.animation.setStartValue(0)
        #     self.animation.setEndValue(1)
        #     self.animation.start()
        
    def to_dict(self) -> dict:
        """Convertit la flèche en dictionnaire pour la sauvegarde"""
        return {
            "style": self.style.value,
            "cardinality": self.cardinality,
            "colors": {k: v.name() if hasattr(v, 'name') else str(v) for k, v in self.colors.items()},
            "dimensions": self.dimensions.copy()
        }
        
    @classmethod
    def from_dict(cls, data: dict, source: QGraphicsItem, target: QGraphicsItem) -> 'HybridArrow':
        """Crée une flèche à partir d'un dictionnaire"""
        arrow = cls(source, target, data.get("cardinality", "1,N"))
        arrow.style = ArrowStyle(data.get("style", "smart"))
        arrow.colors.update(data.get("colors", {}))
        arrow.dimensions.update(data.get("dimensions", {}))
        return arrow
        
    def mouseDoubleClickEvent(self, event):
        """Gère le double-clic sur la flèche"""
        # Émettre un signal ou appeler une méthode du parent
        if hasattr(self, 'on_double_click'):
            self.on_double_click(event)
        event.accept()
        
    def contextMenuEvent(self, event):
        """Gère le clic droit sur la flèche"""
        # Émettre un signal ou appeler une méthode du parent
        if hasattr(self, 'on_context_menu'):
            self.on_context_menu(event)
        event.accept()
        
    def hoverEnterEvent(self, event):
        """Gère l'entrée de la souris sur la flèche"""
        self.setCursor(Qt.PointingHandCursor)
        # Optionnel : changer l'apparence
        super().hoverEnterEvent(event)
        
    def hoverLeaveEvent(self, event):
        """Gère la sortie de la souris de la flèche"""
        self.setCursor(Qt.ArrowCursor)
        # Optionnel : restaurer l'apparence
        super().hoverLeaveEvent(event) 