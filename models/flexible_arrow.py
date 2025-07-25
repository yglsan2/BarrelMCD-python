#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Classe FlexibleArrow pour les flèches style Draw.io
"""

from PyQt5.QtWidgets import (
    QGraphicsItem, QGraphicsPathItem, QGraphicsEllipseItem,
    QGraphicsRectItem, QGraphicsItemGroup, QMenu, QAction, QInputDialog
)
from PyQt5.QtCore import Qt, QPointF, QRectF, pyqtSignal, QObject
from PyQt5.QtGui import (
    QPen, QBrush, QColor, QPainter, QPainterPath, QCursor, QFont
)

class FlexibleArrowSignals(QObject):
    """Signaux pour les flèches flexibles"""
    arrow_modified = pyqtSignal()
    cardinality_changed = pyqtSignal(str, str)  # entity, cardinality

class FlexibleArrow(QGraphicsItemGroup):
    """Flèche flexible style Draw.io avec points de contrôle"""
    
    def __init__(self, start_entity=None, end_entity=None, cardinality_start="1", cardinality_end="N"):
        super().__init__()
        
        # Créer l'objet de signaux
        self.signals = FlexibleArrowSignals()
        
        # Entités connectées
        self.start_entity = start_entity
        self.end_entity = end_entity
        self.cardinality_start = cardinality_start
        self.cardinality_end = cardinality_end
        
        # Points de contrôle (style Draw.io)
        self.control_points = []
        self.selected_point = None
        self.is_dragging = False
        
        # Configuration visuelle
        self.arrow_color = QColor(100, 150, 255)
        self.arrow_width = 2
        self.handle_size = 6
        self.anchor_size = 8
        
        # Éléments visuels
        self.path_item = None
        self.anchor_points = []
        self.control_handles = []
        
        # Configuration interactive
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemIsFocusable, True)
        self.setAcceptHoverEvents(True)
        
        # Créer les éléments visuels
        self.create_visual_elements()
        
    def create_visual_elements(self):
        """Crée les éléments visuels de la flèche"""
        # Créer le chemin de base
        self.path_item = QGraphicsPathItem()
        self.path_item.setPen(QPen(self.arrow_color, self.arrow_width))
        self.path_item.setBrush(QBrush(Qt.transparent))
        self.addToGroup(self.path_item)
        
        # Créer les points d'ancrage
        self.create_anchor_points()
        
        # Créer les handles de contrôle
        self.create_control_handles()
        
        # Initialiser le chemin
        self.update_path()
        
    def create_anchor_points(self):
        """Crée les points d'ancrage aux extrémités"""
        # Point d'ancrage de départ
        start_anchor = QGraphicsEllipseItem(-self.anchor_size/2, -self.anchor_size/2, 
                                           self.anchor_size, self.anchor_size)
        start_anchor.setPen(QPen(self.arrow_color, 2))
        start_anchor.setBrush(QBrush(self.arrow_color))
        start_anchor.setZValue(10)
        self.anchor_points.append(start_anchor)
        self.addToGroup(start_anchor)
        
        # Point d'ancrage d'arrivée
        end_anchor = QGraphicsEllipseItem(-self.anchor_size/2, -self.anchor_size/2, 
                                         self.anchor_size, self.anchor_size)
        end_anchor.setPen(QPen(self.arrow_color, 2))
        end_anchor.setBrush(QBrush(self.arrow_color))
        end_anchor.setZValue(10)
        self.anchor_points.append(end_anchor)
        self.addToGroup(end_anchor)
        
    def create_control_handles(self):
        """Crée les handles de contrôle pour ajuster la courbure"""
        # Handle de contrôle central (pour créer des bras coudés)
        control_handle = QGraphicsRectItem(-self.handle_size/2, -self.handle_size/2, 
                                         self.handle_size, self.handle_size)
        control_handle.setPen(QPen(QColor(255, 255, 0), 1))
        control_handle.setBrush(QBrush(QColor(255, 255, 0, 150)))
        control_handle.setZValue(15)
        self.control_handles.append(control_handle)
        self.addToGroup(control_handle)
        
    def update_path(self):
        """Met à jour le chemin de la flèche"""
        if not self.start_entity or not self.end_entity:
            return
            
        # Obtenir les positions des entités
        start_pos = self.start_entity.pos()
        end_pos = self.end_entity.pos()
        
        # Créer le chemin
        path = QPainterPath()
        
        # Point de départ
        path.moveTo(start_pos)
        
        # Points de contrôle (style Draw.io)
        if self.control_points:
            for point in self.control_points:
                path.lineTo(point)
        else:
            # Créer un point de contrôle central pour éviter les obstacles
            mid_point = QPointF((start_pos.x() + end_pos.x()) / 2, 
                               (start_pos.y() + end_pos.y()) / 2)
            path.lineTo(mid_point)
        
        # Point d'arrivée
        path.lineTo(end_pos)
        
        # Ajouter la pointe de flèche
        self.add_arrow_head(path, end_pos, start_pos)
        
        # Mettre à jour le chemin
        self.path_item.setPath(path)
        
        # Mettre à jour les positions des points d'ancrage
        self.anchor_points[0].setPos(start_pos)
        self.anchor_points[1].setPos(end_pos)
        
        # Mettre à jour les handles de contrôle
        if self.control_handles:
            if self.control_points:
                self.control_handles[0].setPos(self.control_points[0])
            else:
                mid_point = QPointF((start_pos.x() + end_pos.x()) / 2, 
                                   (start_pos.y() + end_pos.y()) / 2)
                self.control_handles[0].setPos(mid_point)
                
        # Dessiner les cardinalités
        painter = QPainter()
        self.paint_cardinalities(painter)
                
    def add_arrow_head(self, path, end_pos, start_pos):
        """Ajoute la pointe de flèche"""
        # Calculer la direction
        direction = end_pos - start_pos
        if direction.isNull():
            return
            
        # Normaliser
        length = (direction.x()**2 + direction.y()**2)**0.5
        if length == 0:
                return
            
        direction = direction / length
        
        # Créer la pointe de flèche
        arrow_length = 15
        arrow_width = 8
        
        # Point de base de la flèche
        base = end_pos - direction * arrow_length
        
        # Points latéraux
        perp = QPointF(-direction.y(), direction.x())
        left = base + perp * arrow_width
        right = base - perp * arrow_width
        
        # Dessiner la pointe
        path.moveTo(end_pos)
        path.lineTo(left)
        path.moveTo(end_pos)
        path.lineTo(right)
        
    def paint_cardinalities(self, painter):
        """Dessine les cardinalités sur la flèche"""
        if not self.start_entity or not self.end_entity:
            return
            
        # Position des cardinalités
        start_pos = self.start_entity.pos()
        end_pos = self.end_entity.pos()
        
        # Cardinalité de départ
        if self.cardinality_start:
            painter.setPen(QPen(self.arrow_color, 1))
            painter.setFont(QFont("Arial", 8, QFont.Bold))
            start_text_pos = start_pos + QPointF(10, -10)
            painter.drawText(start_text_pos, self.cardinality_start)
            
        # Cardinalité d'arrivée
        if self.cardinality_end:
            painter.setPen(QPen(self.arrow_color, 1))
            painter.setFont(QFont("Arial", 8, QFont.Bold))
            end_text_pos = end_pos + QPointF(-10, -10)
            painter.drawText(end_text_pos, self.cardinality_end)
    
    def get_cardinality_at_pos(self, pos):
        """Retourne la cardinalité à la position donnée"""
        if not self.start_entity or not self.end_entity:
            return None
            
        start_pos = self.start_entity.pos()
        end_pos = self.end_entity.pos()
        
        # Vérifier la cardinalité de départ
        start_text_rect = QRectF(start_pos.x() + 5, start_pos.y() - 15, 20, 15)
        if start_text_rect.contains(pos):
            return "start"
            
        # Vérifier la cardinalité d'arrivée
        end_text_rect = QRectF(end_pos.x() - 25, end_pos.y() - 15, 20, 15)
        if end_text_rect.contains(pos):
            return "end"
            
        return None
    
    def mousePressEvent(self, event):
        """Gère l'événement de clic"""
        if event.button() == Qt.LeftButton:
            # Vérifier si on clique sur une cardinalité
            cardinality_pos = self.get_cardinality_at_pos(event.pos())
            if cardinality_pos:
                self.edit_cardinality(cardinality_pos)
                event.accept()
                return
            
            # Vérifier si on clique sur un handle
            pos = event.pos()
            
            # Vérifier les points d'ancrage
            for i, anchor in enumerate(self.anchor_points):
                if anchor.contains(anchor.mapFromParent(pos)):
                    self.selected_point = f"anchor_{i}"
                    self.is_dragging = True
                    event.accept()
                    return
                    
            # Vérifier les handles de contrôle
            for i, handle in enumerate(self.control_handles):
                if handle.contains(handle.mapFromParent(pos)):
                    self.selected_point = f"control_{i}"
                    self.is_dragging = True
                    event.accept()
                    return
                    
            # Double-clic pour éditer
            if event.type() == event.MouseButtonDblClick:
                self.edit_cardinality()
                
        super().mousePressEvent(event)
        
    def mouseMoveEvent(self, event):
        """Gère l'événement de mouvement"""
        if self.is_dragging and self.selected_point:
            new_pos = event.pos()
            
            if self.selected_point.startswith("anchor_"):
                # Déplacer le point d'ancrage
                anchor_index = int(self.selected_point.split("_")[1])
                if anchor_index == 0:
                    # Déplacer l'entité de départ
                    if self.start_entity:
                        self.start_entity.setPos(new_pos)
                else:
                    # Déplacer l'entité d'arrivée
                    if self.end_entity:
                        self.end_entity.setPos(new_pos)
                        
            elif self.selected_point.startswith("control_"):
                # Déplacer le point de contrôle
                control_index = int(self.selected_point.split("_")[1])
                if control_index < len(self.control_points):
                    self.control_points[control_index] = new_pos
                else:
                    self.control_points.append(new_pos)
                    
            self.update_path()
            self.signals.arrow_modified.emit()
            event.accept()
            return
            
        super().mouseMoveEvent(event)
        
    def mouseReleaseEvent(self, event):
        """Gère l'événement de relâchement"""
        if event.button() == Qt.LeftButton:
            self.is_dragging = False
            self.selected_point = None
            
        super().mouseReleaseEvent(event)
        
    def contextMenuEvent(self, event):
        """Menu contextuel pour la flèche"""
        menu = QMenu()
        
        # Actions pour les cardinalités
        edit_start_action = menu.addAction(f"Modifier cardinalité départ ({self.cardinality_start})")
        edit_end_action = menu.addAction(f"Modifier cardinalité arrivée ({self.cardinality_end})")
        
        # Actions pour la forme
        straight_action = menu.addAction("Ligne droite")
        curved_action = menu.addAction("Ligne courbe")
        stepped_action = menu.addAction("Ligne en escalier")
        
        # Connexions
        edit_start_action.triggered.connect(lambda: self.edit_cardinality("start"))
        edit_end_action.triggered.connect(lambda: self.edit_cardinality("end"))
        straight_action.triggered.connect(self.make_straight)
        curved_action.triggered.connect(self.make_curved)
        stepped_action.triggered.connect(self.make_stepped)
        
        menu.exec_(QCursor.pos())
        
    def edit_cardinality(self, end="end"):
        """Édite la cardinalité de la flèche"""
        
        cardinalities = ["0,1", "1,1", "0,N", "1,N", "N,N"]
        
        if end == "start":
            current = self.cardinality_start
            title = "Cardinalité de départ"
        else:
            current = self.cardinality_end
            title = "Cardinalité d'arrivée"
            
        cardinality, ok = QInputDialog.getItem(
            None, title, "Cardinalité:", cardinalities,
            cardinalities.index(current) if current in cardinalities else 1, False
        )
        
        if ok:
            if end == "start":
                self.cardinality_start = cardinality
            else:
                self.cardinality_end = cardinality
            self.signals.cardinality_changed.emit(end, cardinality)
            
    def make_straight(self):
        """Rend la flèche droite"""
        self.control_points.clear()
        self.update_path()
        
    def make_curved(self):
        """Rend la flèche courbe"""
        if self.start_entity and self.end_entity:
            start_pos = self.start_entity.pos()
            end_pos = self.end_entity.pos()
            mid_point = QPointF((start_pos.x() + end_pos.x()) / 2, 
                               (start_pos.y() + end_pos.y()) / 2)
            self.control_points = [mid_point]
            self.update_path()
            
    def make_stepped(self):
        """Rend la flèche en escalier"""
        if self.start_entity and self.end_entity:
            start_pos = self.start_entity.pos()
            end_pos = self.end_entity.pos()
            
            # Créer des points pour un escalier
            step1 = QPointF(end_pos.x(), start_pos.y())
            self.control_points = [step1]
            self.update_path()
            
    def set_selected(self, selected):
        """Définit l'état de sélection"""
        if selected:
            self.setZValue(10)
            # Afficher les handles
            for handle in self.control_handles:
                handle.setVisible(True)
        else:
            self.setZValue(0)
            # Masquer les handles
            for handle in self.control_handles:
                handle.setVisible(False)
                
    def update_from_entities(self):
        """Met à jour la flèche selon les positions des entités"""
        self.update_path() 