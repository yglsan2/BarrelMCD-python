#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Système de flèches flexibles performant pour BarrelMCD
Optimisé pour des performances fluides même avec de nombreux éléments
Style moderne inspiré de Barrel, Draw.io et Lucidchart
"""

import math
from enum import Enum
from PyQt5.QtWidgets import QGraphicsPathItem, QGraphicsItem, QMenu, QInputDialog
from PyQt5.QtCore import Qt, QRectF, QPointF, QLineF, pyqtSignal, QObject
from PyQt5.QtGui import (
    QPainter, QPen, QColor, QPainterPath, QBrush, QLinearGradient,
    QFont, QFontMetrics
)

class ArrowStyle(Enum):
    """Styles de flèches disponibles"""
    STRAIGHT = "straight"      # Ligne droite simple
    CURVED = "curved"          # Courbe de Bézier élégante
    STEPPED = "stepped"        # Ligne en escalier
    ORTHOGONAL = "orthogonal"  # Ligne orthogonale
    SMART = "smart"            # Détection automatique

class PerformanceArrowSignals(QObject):
    """Signaux pour les flèches"""
    arrow_modified = pyqtSignal()
    cardinality_changed = pyqtSignal(str, str)  # end, cardinality

class PerformanceArrow(QGraphicsPathItem):
    """Flèche flexible performante avec rendu optimisé"""
    
    def __init__(self, source: QGraphicsItem, target: QGraphicsItem, 
                 cardinality_start="1", cardinality_end="N"):
        super().__init__()
        
        # Créer l'objet de signaux
        self.signals = PerformanceArrowSignals()
        
        # Éléments source et cible
        self.source = source
        self.target = target
        self.cardinality_start = cardinality_start
        self.cardinality_end = cardinality_end
        
        # Style et configuration
        self.style = ArrowStyle.SMART
        self.auto_style = True
        
        # Configuration visuelle moderne
        self.colors = {
            "line": QColor(100, 150, 255),      # Bleu moderne
            "line_hover": QColor(150, 200, 255), # Bleu clair au survol
            "arrow": QColor(100, 150, 255),     # Même couleur que la ligne
            "cardinality_bg": QColor(30, 30, 30, 220),  # Fond semi-transparent
            "cardinality_text": QColor(255, 255, 255),  # Texte blanc
        }
        
        self.dimensions = {
            "line_width": 2.5,
            "line_width_hover": 3.5,
            "arrow_size": 12,
            "arrow_width": 8,
            "cardinality_offset": 20,
            "cardinality_padding": 4
        }
        
        # Points de contrôle pour les courbes
        self.control_points = []
        self.path_cache = None
        self.last_source_pos = None
        self.last_target_pos = None
        
        # État
        self.is_hovered = False
        self.is_selected = False
        
        # Configuration de base
        self.setZValue(-1)  # Sous les autres éléments
        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        
        # Cache pour les performances
        self._bounding_rect_cache = None
        self._shape_cache = None
        
        # Calcul initial du chemin
        self.update_path()
        
    def boundingRect(self) -> QRectF:
        """Calcule la zone englobante avec cache"""
        if self._bounding_rect_cache and self.path_cache:
            return self._bounding_rect_cache
            
        if not self.path_cache:
            return QRectF()
            
        rect = self.path_cache.boundingRect()
        # Ajouter de l'espace pour la cardinalité et la flèche
        margin = max(self.dimensions["arrow_size"], self.dimensions["cardinality_offset"])
        rect.adjust(-margin, -margin, margin, margin)
        
        self._bounding_rect_cache = rect
        return rect
        
    def shape(self) -> QPainterPath:
        """Retourne la forme pour la détection de collision avec cache"""
        if self._shape_cache and self.path_cache:
            return self._shape_cache
            
        if not self.path_cache:
            return QPainterPath()
            
        # Créer un chemin élargi pour faciliter la sélection
        stroker = QPainterPath()
        stroker.addPath(self.path_cache)
        # Élargir de quelques pixels pour faciliter le clic
        stroker = self._widen_path(self.path_cache, 5)
        
        self._shape_cache = stroker
        return stroker
        
    def _widen_path(self, path: QPainterPath, width: float) -> QPainterPath:
        """Élargit un chemin pour faciliter la sélection"""
        from PyQt5.QtGui import QPainterPathStroker
        stroker = QPainterPathStroker()
        stroker.setWidth(width)
        stroker.setCapStyle(Qt.RoundCap)
        stroker.setJoinStyle(Qt.RoundJoin)
        return stroker.createStroke(path)
        
    def paint(self, painter: QPainter, option, widget):
        """Dessine la flèche avec rendu optimisé"""
        if not self.source or not self.target:
            return
            
        # Mettre à jour le chemin si nécessaire
        if self._needs_update():
            self.update_path()
            
        if not self.path_cache:
            return
            
        # Configuration du peintre
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
        
        # Couleur et épaisseur selon l'état
        if self.is_hovered or self.is_selected:
            line_color = self.colors["line_hover"]
            line_width = self.dimensions["line_width_hover"]
        else:
            line_color = self.colors["line"]
            line_width = self.dimensions["line_width"]
            
        # Créer un dégradé pour la ligne
        rect = self.path_cache.boundingRect()
        gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())
        gradient.setColorAt(0, line_color)
        gradient.setColorAt(1, line_color.lighter(110))
        
        # Dessiner la ligne principale
        pen = QPen(gradient, line_width)
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(self.path_cache)
        
        # Dessiner la pointe de la flèche
        self._draw_arrow_head(painter, line_color, line_width)
        
        # Dessiner les cardinalités
        self._draw_cardinalities(painter)
        
    def _needs_update(self) -> bool:
        """Vérifie si le chemin doit être mis à jour"""
        if not self.source or not self.target:
            return False
            
        source_pos = self._get_element_center(self.source)
        target_pos = self._get_element_center(self.target)
        
        if (self.last_source_pos != source_pos or 
            self.last_target_pos != target_pos):
            return True
            
        return False
        
    def update_path(self):
        """Met à jour le chemin de la flèche"""
        if not self.source or not self.target:
            return
            
        # Détecter le style optimal si nécessaire
        if self.auto_style:
            self.style = self._detect_optimal_style()
            
        # Calculer les points selon le style
        points = self._calculate_points()
        if not points or len(points) < 2:
            return
            
        # Créer le chemin
        self.path_cache = self._create_path_from_points(points)
        self.setPath(self.path_cache)
        
        # Mettre à jour les positions en cache
        self.last_source_pos = self._get_element_center(self.source)
        self.last_target_pos = self._get_element_center(self.target)
        
        # Invalider les caches
        self._bounding_rect_cache = None
        self._shape_cache = None
        self.prepareGeometryChange()
        
    def _detect_optimal_style(self) -> ArrowStyle:
        """Détecte le style optimal selon la disposition"""
        if not self.source or not self.target:
            return ArrowStyle.STRAIGHT
            
        source_pos = self._get_element_center(self.source)
        target_pos = self._get_element_center(self.target)
        
        dx = target_pos.x() - source_pos.x()
        dy = target_pos.y() - source_pos.y()
        distance = math.sqrt(dx*dx + dy*dy)
        angle = math.atan2(dy, dx)
        
        # Règles de détection intelligente
        if distance < 150:
            return ArrowStyle.STRAIGHT
        elif abs(angle) < math.pi/6 or abs(angle) > 5*math.pi/6:
            return ArrowStyle.ORTHOGONAL
        elif abs(angle - math.pi/2) < math.pi/6 or abs(angle + math.pi/2) < math.pi/6:
            return ArrowStyle.ORTHOGONAL
        elif distance > 300:
            return ArrowStyle.CURVED
        else:
            return ArrowStyle.STEPPED
            
    def _calculate_points(self) -> list:
        """Calcule les points selon le style choisi"""
        if not self.source or not self.target:
            return []
            
        source_center = self._get_element_center(self.source)
        target_center = self._get_element_center(self.target)
        
        # Obtenir les points sur les bords
        start_point = self._get_border_point(self.source, source_center, target_center)
        end_point = self._get_border_point(self.target, target_center, source_center)
        
        if self.style == ArrowStyle.STRAIGHT:
            return [start_point, end_point]
        elif self.style == ArrowStyle.CURVED:
            return self._calculate_curved_points(start_point, end_point)
        elif self.style == ArrowStyle.STEPPED:
            return self._calculate_stepped_points(start_point, end_point)
        elif self.style == ArrowStyle.ORTHOGONAL:
            return self._calculate_orthogonal_points(start_point, end_point)
        else:
            return [start_point, end_point]
            
    def _calculate_curved_points(self, start: QPointF, end: QPointF) -> list:
        """Calcule les points pour une courbe de Bézier"""
        mid_point = QPointF((start.x() + end.x()) / 2,
                           (start.y() + end.y()) / 2)
        
        dx = end.x() - start.x()
        dy = end.y() - start.y()
        distance = math.sqrt(dx*dx + dy*dy)
        
        if distance > 0:
            offset = min(distance * 0.3, 60)
            perpendicular = QPointF(-dy/distance * offset, dx/distance * offset)
            control_point = mid_point + perpendicular
        else:
            control_point = mid_point
            
        return [start, control_point, end]
        
    def _calculate_stepped_points(self, start: QPointF, end: QPointF) -> list:
        """Calcule les points pour une ligne en escalier"""
        mid_x = (start.x() + end.x()) / 2
        return [start, QPointF(mid_x, start.y()), 
                QPointF(mid_x, end.y()), end]
                
    def _calculate_orthogonal_points(self, start: QPointF, end: QPointF) -> list:
        """Calcule les points pour une ligne orthogonale"""
        dx = abs(end.x() - start.x())
        dy = abs(end.y() - start.y())
        
        if dx > dy:
            mid_point = QPointF(end.x(), start.y())
        else:
            mid_point = QPointF(start.x(), end.y())
            
        return [start, mid_point, end]
        
    def _get_element_center(self, element: QGraphicsItem) -> QPointF:
        """Obtient le centre d'un élément"""
        pos = element.scenePos()
        rect = element.boundingRect()
        return QPointF(pos.x() + rect.width()/2, pos.y() + rect.height()/2)
        
    def _get_border_point(self, element: QGraphicsItem, 
                         element_center: QPointF, 
                         direction_center: QPointF) -> QPointF:
        """Calcule le point sur le bord de l'élément"""
        dx = direction_center.x() - element_center.x()
        dy = direction_center.y() - element_center.y()
        distance = math.sqrt(dx*dx + dy*dy)
        
        if distance < 1:
            return element_center
            
        direction = QPointF(dx/distance, dy/distance)
        rect = element.boundingRect()
        
        # Calculer l'intersection avec le rectangle
        center = element.scenePos() + QPointF(rect.width()/2, rect.height()/2)
        half_width = rect.width() / 2
        half_height = rect.height() / 2
        
        # Trouver le point d'intersection
        if abs(dx) * half_height > abs(dy) * half_width:
            # Intersection avec les côtés verticaux
            x = center.x() + (half_width if dx > 0 else -half_width)
            y = center.y() + dy * (x - center.x()) / dx if dx != 0 else center.y()
        else:
            # Intersection avec les côtés horizontaux
            y = center.y() + (half_height if dy > 0 else -half_height)
            x = center.x() + dx * (y - center.y()) / dy if dy != 0 else center.x()
            
        return QPointF(x, y)
        
    def _create_path_from_points(self, points: list) -> QPainterPath:
        """Crée un chemin à partir des points calculés"""
        if not points or len(points) < 2:
            return QPainterPath()
            
        path = QPainterPath()
        path.moveTo(points[0])
        
        if len(points) == 2:
            path.lineTo(points[1])
        elif len(points) == 3 and self.style == ArrowStyle.CURVED:
            path.quadTo(points[1], points[2])
        else:
            for i in range(1, len(points)):
                path.lineTo(points[i])
                
        return path
        
    def _draw_arrow_head(self, painter: QPainter, color: QColor, width: float):
        """Dessine la pointe de la flèche"""
        if not self.path_cache:
            return
            
        # Obtenir le dernier segment
        path_elements = self.path_cache.toSubpathPolygons()
        if not path_elements:
            return
            
        polygon = path_elements[-1]
        if len(polygon) < 2:
            return
            
        end_point = polygon[-1]
        control_point = polygon[-2] if len(polygon) > 1 else polygon[0]
        
        # Calculer la direction
        direction = QPointF(end_point.x() - control_point.x(),
                           end_point.y() - control_point.y())
        length = math.sqrt(direction.x() * direction.x() + direction.y() * direction.y())
        
        if length < 1:
            return
            
        direction = QPointF(direction.x() / length, direction.y() / length)
        perpendicular = QPointF(-direction.y(), direction.x())
        
        # Points de la flèche
        arrow_size = self.dimensions["arrow_size"]
        arrow_width = self.dimensions["arrow_width"]
        
        base = QPointF(end_point.x() - direction.x() * arrow_size,
                      end_point.y() - direction.y() * arrow_size)
        
        point1 = QPointF(base.x() + perpendicular.x() * arrow_width/2,
                        base.y() + perpendicular.y() * arrow_width/2)
        point2 = QPointF(base.x() - perpendicular.x() * arrow_width/2,
                        base.y() - perpendicular.y() * arrow_width/2)
        
        # Dessiner la pointe
        arrow_path = QPainterPath()
        arrow_path.moveTo(end_point)
        arrow_path.lineTo(point1)
        arrow_path.moveTo(end_point)
        arrow_path.lineTo(point2)
        
        pen = QPen(color, width)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)
        painter.drawPath(arrow_path)
        
    def _draw_cardinalities(self, painter: QPainter):
        """Dessine les cardinalités avec style moderne"""
        if not self.path_cache:
            return
            
        font = QFont("Arial", 9, QFont.Bold)
        painter.setFont(font)
        fm = QFontMetrics(font)
        
        # Position au milieu de la ligne
        rect = self.path_cache.boundingRect()
        mid_point = rect.center()
        
        # Dessiner la cardinalité de départ
        if self.cardinality_start:
            self._draw_cardinality_label(painter, self.cardinality_start, 
                                       mid_point, -self.dimensions["cardinality_offset"])
        
        # Dessiner la cardinalité d'arrivée
        if self.cardinality_end:
            self._draw_cardinality_label(painter, self.cardinality_end, 
                                       mid_point, self.dimensions["cardinality_offset"])
        
    def _draw_cardinality_label(self, painter: QPainter, text: str, 
                               position: QPointF, offset: float):
        """Dessine un label de cardinalité avec fond"""
        font = painter.font()
        fm = QFontMetrics(font)
        text_rect = fm.boundingRect(text)
        
        # Position du texte
        text_pos = QPointF(position.x() - text_rect.width()/2,
                          position.y() + offset - text_rect.height()/2)
        
        # Rectangle de fond
        padding = self.dimensions["cardinality_padding"]
        bg_rect = QRectF(text_pos.x() - padding,
                        text_pos.y() - padding,
                        text_rect.width() + padding * 2,
                        text_rect.height() + padding * 2)
        
        # Dessiner le fond arrondi
        painter.setBrush(QBrush(self.colors["cardinality_bg"]))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(bg_rect, 4, 4)
        
        # Dessiner le texte
        painter.setPen(QPen(self.colors["cardinality_text"]))
        painter.drawText(text_pos, text)
        
    def hoverEnterEvent(self, event):
        """Gère l'entrée de la souris"""
        self.is_hovered = True
        self.setCursor(Qt.PointingHandCursor)
        self.update()
        super().hoverEnterEvent(event)
        
    def hoverLeaveEvent(self, event):
        """Gère la sortie de la souris"""
        self.is_hovered = False
        self.setCursor(Qt.ArrowCursor)
        self.update()
        super().hoverLeaveEvent(event)
        
    def mouseDoubleClickEvent(self, event):
        """Gère le double-clic pour éditer la cardinalité"""
        # Détecter quelle cardinalité a été cliquée
        if not self.path_cache:
            return
            
        rect = self.path_cache.boundingRect()
        mid_point = rect.center()
        click_pos = event.pos()
        
        # Vérifier si on clique sur une cardinalité
        offset = self.dimensions["cardinality_offset"]
        if abs(click_pos.y() - (mid_point.y() - offset)) < 15:
            self._edit_cardinality("start")
        elif abs(click_pos.y() - (mid_point.y() + offset)) < 15:
            self._edit_cardinality("end")
        else:
            # Éditer les deux
            self._edit_cardinality("both")
            
    def _edit_cardinality(self, end: str):
        """Édite la cardinalité"""
        cardinalities = ["0,1", "1,1", "0,N", "1,N", "N,N"]
        
        if end == "start":
            current = self.cardinality_start
            title = "Cardinalité de départ"
        elif end == "end":
            current = self.cardinality_end
            title = "Cardinalité d'arrivée"
        else:
            # Éditer les deux
            self._edit_cardinality("start")
            self._edit_cardinality("end")
            return
            
        try:
            index = cardinalities.index(current) if current in cardinalities else 1
        except ValueError:
            index = 1
            
        cardinality, ok = QInputDialog.getItem(
            None, title, "Cardinalité:", cardinalities, index, False
        )
        
        if ok:
            if end == "start":
                self.cardinality_start = cardinality
            else:
                self.cardinality_end = cardinality
            self.signals.cardinality_changed.emit(end, cardinality)
            self.update()
            
    def contextMenuEvent(self, event):
        """Menu contextuel pour la flèche"""
        menu = QMenu()
        
        # Styles
        style_menu = menu.addMenu("Style de ligne")
        for style in ArrowStyle:
            action = style_menu.addAction(style.value.capitalize())
            action.setCheckable(True)
            action.setChecked(self.style == style)
            action.triggered.connect(lambda checked, s=style: self.set_style(s))
        
        # Cardinalités
        menu.addAction(f"Cardinalité départ ({self.cardinality_start})",
                      lambda: self._edit_cardinality("start"))
        menu.addAction(f"Cardinalité arrivée ({self.cardinality_end})",
                      lambda: self._edit_cardinality("end"))
        
        menu.addSeparator()
        
        # Détection automatique
        auto_action = menu.addAction("Détection automatique")
        auto_action.setCheckable(True)
        auto_action.setChecked(self.auto_style)
        auto_action.triggered.connect(lambda checked: setattr(self, 'auto_style', checked))
        
        menu.exec_(event.screenPos())
        
    def set_style(self, style: ArrowStyle):
        """Change le style de la flèche"""
        self.style = style
        self.auto_style = False
        self.update_path()
        self.update()
        
    def itemChange(self, change, value):
        """Gère les changements de l'élément"""
        if change == QGraphicsItem.ItemSelectedChange:
            self.is_selected = value
            self.update()
        return super().itemChange(change, value)

