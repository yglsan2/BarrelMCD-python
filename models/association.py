#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Classe Association pour représenter les associations MCD selon la méthode Merise
"""

from PyQt5.QtWidgets import (
    QGraphicsItemGroup, QGraphicsPolygonItem, QGraphicsTextItem,
    QGraphicsDropShadowEffect, QInputDialog, QMenu, QAction,
    QGraphicsItem
)
from PyQt5.QtCore import Qt, QRectF, QPointF, pyqtSignal, QObject
from PyQt5.QtGui import QPen, QBrush, QColor, QFont, QPainter, QPolygonF, QPainterPath, QCursor

from views.dark_theme import DarkTheme

class AssociationSignals(QObject):
    """Signaux pour l'association"""
    association_renamed = pyqtSignal(str, str)  # old_name, new_name
    cardinality_changed = pyqtSignal(str, str)  # entity, cardinality
    attribute_added = pyqtSignal(str, str)  # name, type
    attribute_removed = pyqtSignal(str)

class Association(QGraphicsItem):
    """Classe représentant une association MCD selon Merise"""
    
    def __init__(self, name="Nouvelle association", pos=QPointF(0, 0)):
        super().__init__()
        
        # Créer l'objet de signaux
        self.signals = AssociationSignals()
        
        # Propriétés de base
        self.name = name
        self.attributes = []
        self.entities = []  # Liste des entités connectées
        self.cardinalities = {}  # {entity_name: cardinality}
        self.roles = {}  # {entity_name: role} pour associations réflexives
        self.is_selected = False
        self.is_reflexive = False  # Association réflexive
        self.business_rules = []  # Règles de gestion
        self.cif_constraints = []  # Contraintes d'intégrité fonctionnelle
        self.can_be_entity = False  # Peut être transformée en entité
        
        # Configuration visuelle
        self.size = 60
        self.min_size = 40
        self.padding = 8
        
        # Redimensionnement
        self.resize_handles = []
        self.is_resizing = False
        self.resize_handle_size = 8
        self.hovered_handle = None
        
        # Styles
        self.setup_styles()
        
        # Création des éléments visuels
        self.create_visual_elements()
        
        # Position
        self.setPos(pos)
        
        # Configuration interactive
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        self.setFlag(QGraphicsItem.ItemIsFocusable, True)
        self.setAcceptHoverEvents(True)
        
        # Effet d'ombre
        self.setup_shadow()
        
    def setup_styles(self):
        """Configure les styles visuels"""
        self.colors = DarkTheme.COLORS
        self.style = DarkTheme.get_entity_style("association")
        
        # Couleurs
        self.bg_color = QColor(self.style["background"])
        self.border_color = QColor(self.style["border"])
        self.text_color = QColor(self.style["text"])
        self.selected_color = QColor(self.style["selected"])
        
        # Polices
        self.title_font = QFont("Segoe UI", 10, QFont.Bold)
        self.attribute_font = QFont("Segoe UI", 8)
        
    def create_visual_elements(self):
        """Crée les éléments visuels de l'association (losange)"""
        # Les éléments seront dessinés dans paint()
        pass
        
    def create_diamond(self):
        """Crée la forme de losange"""
        diamond = QGraphicsPolygonItem()
        
        # Points du losange
        center_x = self.size / 2
        center_y = self.size / 2
        half_size = self.size / 2
        
        points = [
            QPointF(center_x, center_y - half_size),  # Haut
            QPointF(center_x + half_size, center_y),  # Droite
            QPointF(center_x, center_y + half_size),  # Bas
            QPointF(center_x - half_size, center_y)   # Gauche
        ]
        
        polygon = QPolygonF(points)
        diamond.setPolygon(polygon)
        diamond.setBrush(QBrush(self.bg_color))
        diamond.setPen(QPen(self.border_color, 2))
        
        return diamond
        
    def setup_shadow(self):
        """Configure l'effet d'ombre"""
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(8)
        shadow.setColor(QColor(self.colors["shadow"]))
        shadow.setOffset(1, 1)
        self.setGraphicsEffect(shadow)
        
    def add_entity(self, entity_name, cardinality="1"):
        """Ajoute une entité à l'association"""
        if entity_name not in self.entities:
            self.entities.append(entity_name)
            self.cardinalities[entity_name] = cardinality
            
    def remove_entity(self, entity_name):
        """Retire une entité de l'association"""
        if entity_name in self.entities:
            self.entities.remove(entity_name)
            if entity_name in self.cardinalities:
                del self.cardinalities[entity_name]
                
    def set_cardinality(self, entity_name, cardinality):
        """Définit la cardinalité pour une entité"""
        if entity_name in self.entities:
            self.cardinalities[entity_name] = cardinality
            self.signals.cardinality_changed.emit(entity_name, cardinality)
            
    def add_attribute(self, name, type_name):
        """Ajoute un attribut à l'association"""
        attribute = {
            "name": name,
            "type": type_name,
            "is_primary_key": False,
            "nullable": True
        }
        self.attributes.append(attribute)
        self.update_display()  # Redessiner l'association
        self.signals.attribute_added.emit(name, type_name)
        
    def remove_attribute(self, name):
        """Supprime un attribut"""
        for i, attribute in enumerate(self.attributes):
            if attribute["name"] == name:
                self.attributes.pop(i)
                self.update_display()  # Redessiner l'association
                self.signals.attribute_removed.emit(name)
                break
                
    def update_display(self):
        """Met à jour l'affichage de l'association avec les attributs"""
        # Recalculer la taille selon les attributs
        min_height = 60 + len(self.attributes) * 20
        self.size = max(self.size, min_height)
        
        # Redessiner l'association
        self.update()
        
    def rename(self, new_name):
        """Renomme l'association"""
        old_name = self.name
        self.name = new_name
        self.update()  # Redessiner l'association
        self.signals.association_renamed.emit(old_name, new_name)
        
    def rename_association(self):
        """Renomme l'association"""
        new_name, ok = QInputDialog.getText(None, "Renommer l'association", 
                                           "Nouveau nom:", text=self.name)
        if ok and new_name.strip():
            old_name = self.name
            self.name = new_name.strip()
            self.update_display()
            self.signals.association_renamed.emit(old_name, self.name)
            
    def set_selected(self, selected):
        """Définit l'état de sélection"""
        self.is_selected = selected
        if selected:
            self.setZValue(10)  # Mettre au premier plan
        else:
            self.setZValue(0)  # Remettre au plan normal
        self.update()  # Redessiner l'association
            
    def create_resize_handles(self):
        """Crée les handles de redimensionnement"""
        self.resize_handles = []
        width = self.size * 1.5
        height = self.size
        
        # 8 handles autour de l'ovoïde
        handles = [
            (-width/2, -height/2),  # Coin supérieur gauche
            (0, -height/2),         # Milieu haut
            (width/2, -height/2),   # Coin supérieur droit
            (width/2, 0),           # Milieu droite
            (width/2, height/2),    # Coin inférieur droit
            (0, height/2),          # Milieu bas
            (-width/2, height/2),   # Coin inférieur gauche
            (-width/2, 0)           # Milieu gauche
        ]
        
        for i, (x, y) in enumerate(handles):
            self.resize_handles.append({
                'pos': QPointF(x, y),
                'cursor': self.get_resize_cursor(i),
                'index': i
            })
    
    def get_resize_cursor(self, handle_index):
        """Retourne le curseur approprié pour chaque handle"""
        cursors = [
            Qt.SizeFDiagCursor,  # Coin supérieur gauche
            Qt.SizeVerCursor,     # Milieu haut
            Qt.SizeBDiagCursor,   # Coin supérieur droit
            Qt.SizeHorCursor,     # Milieu droite
            Qt.SizeFDiagCursor,   # Coin inférieur droit
            Qt.SizeVerCursor,     # Milieu bas
            Qt.SizeBDiagCursor,   # Coin inférieur gauche
            Qt.SizeHorCursor      # Milieu gauche
        ]
        return cursors[handle_index]
    
    def get_handle_at_pos(self, pos):
        """Retourne le handle à la position donnée"""
        for handle in self.resize_handles:
            handle_rect = QRectF(
                handle['pos'].x() - self.resize_handle_size/2,
                handle['pos'].y() - self.resize_handle_size/2,
                self.resize_handle_size,
                self.resize_handle_size
            )
            if handle_rect.contains(pos):
                return handle
        return None
    
    def mousePressEvent(self, event):
        """Gère l'événement de clic"""
        if event.button() == Qt.LeftButton:
            # Vérifier si on clique sur un handle de redimensionnement
            handle = self.get_handle_at_pos(event.pos())
            if handle:
                self.is_resizing = True
                self.hovered_handle = handle
                self.setCursor(handle['cursor'])
                event.accept()
                return
            
            self.setSelected(True)
            self.setFocus()
            # Laisser le canvas gérer le déplacement
            event.accept()
        else:
            super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """Gère l'événement de mouvement"""
        if self.is_resizing and self.hovered_handle:
            # Redimensionner selon le handle
            self.resize_from_handle(event.pos(), self.hovered_handle)
            event.accept()
            return
        
        # Vérifier le survol des handles
        handle = self.get_handle_at_pos(event.pos())
        if handle:
            self.setCursor(handle['cursor'])
        else:
            self.setCursor(Qt.SizeAllCursor)
        
        super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        """Gère l'événement de relâchement"""
        if event.button() == Qt.LeftButton:
            if self.is_resizing:
                self.is_resizing = False
                self.hovered_handle = None
                self.setCursor(Qt.ArrowCursor)
                event.accept()
                return
            
            self.setSelected(False)
        super().mouseReleaseEvent(event)
    
    def resize_from_handle(self, pos, handle):
        """Redimensionne l'association selon le handle"""
        # Calculer la nouvelle taille selon la position du handle
        width = self.size * 1.5
        height = self.size
        
        # Ajuster selon le handle
        if handle['index'] in [0, 2, 4, 6]:  # Coins
            # Redimensionner proportionnellement
            new_width = max(self.min_size * 1.5, abs(pos.x()) * 2)
            new_height = max(self.min_size, abs(pos.y()) * 2)
            self.size = min(new_width / 1.5, new_height)
        elif handle['index'] in [1, 5]:  # Haut/Bas
            new_height = max(self.min_size, abs(pos.y()) * 2)
            self.size = new_height
        elif handle['index'] in [3, 7]:  # Gauche/Droite
            new_width = max(self.min_size * 1.5, abs(pos.x()) * 2)
            self.size = new_width / 1.5
        
        # Mettre à jour les handles
        self.create_resize_handles()
        self.update()
        
    def hoverEnterEvent(self, event):
        """Gère l'entrée de la souris"""
        self.setCursor(Qt.SizeAllCursor)
        super().hoverEnterEvent(event)
        
    def hoverLeaveEvent(self, event):
        """Gère la sortie de la souris"""
        self.setCursor(Qt.ArrowCursor)
        super().hoverLeaveEvent(event)
            
    def mouseDoubleClickEvent(self, event):
        """Gère le double-clic pour éditer l'association"""
        if event.button() == Qt.LeftButton:
            self.edit_association()
            
    def edit_association(self):
        """Ouvre l'éditeur d'association"""
        # Menu pour choisir ce qu'éditer
        menu = QMenu()
        rename_action = menu.addAction("Renommer l'association")
        
        # Connexions
        rename_action.triggered.connect(self.rename_association)
        
        menu.exec_(QCursor.pos())
        
    def add_attribute_dialog(self):
        """Dialogue pour ajouter un attribut"""
        name, ok = QInputDialog.getText(None, "Ajouter un attribut", "Nom de l'attribut:")
        if ok and name.strip():
            attr_type, ok2 = QInputDialog.getItem(None, "Type d'attribut", 
                                                "Type:", ["VARCHAR", "INTEGER", "DECIMAL", "DATE", "BOOLEAN"], 0, False)
            if ok2:
                self.add_attribute(name.strip(), attr_type)
                
    def edit_attributes_dialog(self):
        """Dialogue pour éditer les attributs"""
        # TODO: Implémenter un dialogue plus avancé pour éditer les attributs
        pass
            
    def edit_cardinality(self, entity_name):
        """Ouvre le dialogue d'édition de cardinalité"""
        cardinalities = ["0,1", "1,1", "0,N", "1,N", "N,N"]
        current = self.cardinalities.get(entity_name, "1,1")
        
        cardinality, ok = QInputDialog.getItem(
            None, f"Cardinalité pour {entity_name}", 
            "Cardinalité:", cardinalities, 
            cardinalities.index(current) if current in cardinalities else 1, 
            False
        )
        if ok:
            self.set_cardinality(entity_name, cardinality)
            
    def center_association(self):
        """Centre l'association dans la vue"""
        scene_rect = self.scene().sceneRect()
        center = scene_rect.center()
        self.setPos(center.x() - self.size / 2, center.y() - self.size / 2)
        
    def align_to_grid(self):
        """Aligne l'association sur la grille"""
        pos = self.pos()
        grid_size = 20
        new_x = round(pos.x() / grid_size) * grid_size
        new_y = round(pos.y() / grid_size) * grid_size
        self.setPos(new_x, new_y)
        
    def get_data(self):
        """Retourne les données de l'association pour export"""
        return {
            "name": self.name,
            "position": {"x": self.pos().x(), "y": self.pos().y()},
            "entities": self.entities.copy(),
            "cardinalities": self.cardinalities.copy(),
            "attributes": self.attributes.copy()
        }
        
    def set_data(self, data):
        """Charge les données dans l'association"""
        self.name = data.get("name", "Nouvelle association")
        
        pos_data = data.get("position", {"x": 0, "y": 0})
        self.setPos(pos_data["x"], pos_data["y"])
        
        # Charger les entités et cardinalités
        self.entities = data.get("entities", [])
        self.cardinalities = data.get("cardinalities", {})
        
        # Charger les attributs
        self.attributes = data.get("attributes", [])
        
        self.update()  # Redessiner l'association
        
    def boundingRect(self):
        """Retourne le rectangle englobant de l'association"""
        # Calculer la taille selon les attributs
        width = max(120, len(self.name) * 8 + 40)
        height = 60 + len(self.attributes) * 20
        return QRectF(-width/2, -height/2, width, height)
        
    def shape(self):
        """Retourne la forme de l'association pour la détection de clic"""
        path = QPainterPath()
        path.addRect(self.boundingRect())
        return path
        
    def paint(self, painter, option, widget):
        """Dessine l'association (forme ovoïdale)"""
        # Configuration de l'antialiasing
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Dimensions de l'ovoïde
        center_x = 0
        center_y = 0
        width = self.size * 1.5  # Plus large que haut pour l'effet ovoïdal
        height = self.size
        
        # Créer le chemin de l'ovoïde
        path = QPainterPath()
        
        # Dessiner une ellipse allongée (ovoïde)
        rect = QRectF(-width/2, -height/2, width, height)
        path.addEllipse(rect)
        
        # Couleur de remplissage
        painter.setBrush(QBrush(self.bg_color))
        
        # Bordure selon l'état de sélection
        if self.is_selected:
            painter.setPen(QPen(self.selected_color, 3))
        else:
            painter.setPen(QPen(self.border_color, 2))
            
        painter.drawPath(path)
        
        # Dessiner le titre
        painter.setPen(QPen(self.text_color))
        painter.setFont(self.title_font)
        
        # Centrer le texte dans l'ovoïde
        text_rect = QRectF(-width/2, -height/2, width, height)
        painter.drawText(text_rect, Qt.AlignCenter, self.name)
        
        # Dessiner les handles de redimensionnement si sélectionné
        if self.is_selected:
            self.create_resize_handles()
            painter.setPen(QPen(QColor(255, 255, 255), 1))
            painter.setBrush(QBrush(QColor(100, 150, 255)))
            
            for handle in self.resize_handles:
                handle_rect = QRectF(
                    handle['pos'].x() - self.resize_handle_size/2,
                    handle['pos'].y() - self.resize_handle_size/2,
                    self.resize_handle_size,
                    self.resize_handle_size
                )
                painter.drawRect(handle_rect)
