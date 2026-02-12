#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Canvas interactif pour la création manuelle de MCD
Inspiré de Barrel et Power Designer
"""

import time
from PyQt5.QtWidgets import (
    QGraphicsView, QGraphicsScene, QGraphicsItem, QGraphicsRectItem,
    QGraphicsTextItem, QGraphicsEllipseItem, QGraphicsPolygonItem,
    QMenu, QInputDialog, QColorDialog, QFontDialog, QMessageBox,
    QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QLabel, QComboBox,
    QLineEdit, QSpinBox, QCheckBox, QGroupBox, QDialog, QTextEdit,
    QGraphicsDropShadowEffect, QGraphicsOpacityEffect
)
from PyQt5.QtCore import Qt, QPointF, QRectF, QSizeF, QLineF, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import (
    QPainter, QColor, QPen, QBrush, QFont, QPainterPath, QPolygonF,
    QLinearGradient, QRadialGradient, QTransform, QKeySequence
)
from PyQt5.QtPrintSupport import QPrinter
from PyQt5.QtCore import QPoint

from views.dark_theme import DarkTheme
from models.entity import Entity
from models.association import Association
# Relation supprimée - on utilise uniquement les associations
from models.attribute import Attribute
import json
from models.hybrid_arrow import HybridArrow
from models.smart_connector import SmartConnector, SmartConnection
from models.flexible_arrow import FlexibleArrow
from models.performance_arrow import PerformanceArrow
import math

class InteractiveCanvas(QGraphicsView):
    """Canvas interactif pour la création de MCD"""
    
    # Signaux
    entity_created = pyqtSignal(object)
    entity_modified = pyqtSignal(object)
    entity_deleted = pyqtSignal(object)
    association_created = pyqtSignal(object)
    association_modified = pyqtSignal(object)
    association_deleted = pyqtSignal(object)
    diagram_modified = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        
        # Configuration de base
        self.setRenderHint(QPainter.Antialiasing)
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        
        # État du canvas
        self.current_mode = "select"  # select, add_entity, add_association, create_link
        self.current_tool = "select"
        self.selected_items = []
        self.dragging = False
        self.last_mouse_pos = None
        
        # Mode création de liens style Db-Main
        self.link_creation_mode = False
        self.link_start_item = None
        self.link_preview_line = None
        
        # Mode création multiple (pour créer plusieurs éléments d'affilée)
        self.multiple_creation_mode = False
        
        # Zoom et navigation
        self.zoom_factor = 1.15
        self.min_zoom = 0.1
        self.max_zoom = 5.0
        self.current_zoom = 1.0
        
        # Grille
        self.grid_size = 20
        self.show_grid = True
        self.snap_to_grid = True
        
        # Historique
        self.undo_stack = []
        self.redo_stack = []
        self.max_history = 50
        
        # Sélection
        self.selected_items = []
        
        # Configuration des styles
        self.setup_styles()
        
        # Configuration des raccourcis
        self.setup_shortcuts()
        
        # Configuration de la scène
        self.setup_scene()
        
        # Connexion des événements
        self.setup_events()
        
        self.association_in_creation = None  # Association en cours de placement
        self.association_links = []  # [(association, entity, lineItem)]
        self.selecting_entities_for_association = False
        self.inheritance_links = []  # [(parent_entity, child_entity, lineItem)]
        
        # Logo
        self.logo_item = None
        self.show_logo = True
        self.logo_position = "top_left"  # top_left, top_right, bottom_left, bottom_right, center
        self.logo_size = 80
        self.setup_logo()
        
        # Système intelligent de connexion style Db-Main
        self.smart_connector = SmartConnector()
        self.auto_connect_enabled = True
        self.smart_connections = []  # Liste des connexions intelligentes
        
    def setup_styles(self):
        """Configure les styles visuels"""
        self.colors = DarkTheme.COLORS
        self.entity_style = DarkTheme.get_entity_style("default")
        self.association_style = DarkTheme.get_entity_style("association")
        
    def setup_shortcuts(self):
        """Configure les raccourcis clavier"""
        self.shortcuts = {
            Qt.Key_S: self.set_mode_select,
            Qt.Key_E: self.set_mode_entity,
            Qt.Key_A: self.set_mode_association,
            Qt.Key_L: self.set_mode_create_link,  # L pour mode création de liens
            Qt.Key_M: self.toggle_multiple_creation,  # M pour basculer le mode création multiple
            Qt.Key_Z: self.zoom_in,
            Qt.Key_X: self.zoom_out,
            Qt.Key_F: self.fit_view,
            Qt.Key_G: self.toggle_grid,
            Qt.Key_Delete: self.delete_selected,
            Qt.Key_C: self.copy_selected,
            Qt.Key_V: self.paste_items,
            Qt.Key_D: self.duplicate_selected,
            Qt.Key_1: lambda: self.set_cardinality("1"),
            Qt.Key_N: lambda: self.set_cardinality("N"),
            Qt.Key_P: lambda: self.set_cardinality("P"),
            Qt.Key_A: self.select_all,  # Ctrl+A pour tout sélectionner
            Qt.Key_T: self.toggle_logo,  # T pour basculer le logo
        }
        
    def setup_scene(self):
        """Configure la scène graphique"""
        self.scene.setSceneRect(QRectF(-2000, -2000, 4000, 4000))
        self.setBackgroundBrush(QBrush(QColor(self.colors["background"])))
        
    def setup_events(self):
        """Configure les événements de souris et clavier"""
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)
        # Forcer la capture des événements
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        self.viewport().setAttribute(Qt.WA_TransparentForMouseEvents, False)
        
    def setup_logo(self):
        """Configure l'affichage du logo"""
        self.create_logo_item()
        self.update_logo_position()
        
    def create_logo_item(self):
        """Crée l'élément logo avec différentes approches"""
        # Supprimer l'ancien logo s'il existe
        if self.logo_item:
            self.scene.removeItem(self.logo_item)
            self.logo_item = None
            
        # Créer le nouveau logo
        self.logo_item = self.create_text_logo()
        
        # Ajouter le logo à la scène seulement s'il n'y est pas déjà
        if self.logo_item and self.logo_item not in self.scene.items():
            self.logo_item.setZValue(1000)  # Toujours au-dessus
            self.scene.addItem(self.logo_item)
            
    def create_text_logo(self):
        """Crée un logo textuel stylisé"""
        logo_text = QGraphicsTextItem("BarrelMCD")
        logo_text.setDefaultTextColor(QColor(255, 255, 255))
        
        # Style moderne avec gradient
        font = QFont("Arial", 16, QFont.Bold)
        logo_text.setFont(font)
        
        # Effet d'ombre
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)
        shadow.setColor(QColor(0, 0, 0, 100))
        shadow.setOffset(2, 2)
        logo_text.setGraphicsEffect(shadow)
        
        # Fond semi-transparent
        background = QGraphicsRectItem(logo_text.boundingRect())
        background.setBrush(QBrush(QColor(0, 0, 0, 50)))
        background.setPen(QPen(QColor(255, 255, 255, 100), 1))
        background.setZValue(-1)
        
        # Grouper le texte et le fond
        group = self.scene.createItemGroup([background, logo_text])
        return group
        
    def create_svg_logo(self):
        """Crée un logo SVG (nécessite un fichier SVG)"""
        try:
            from PyQt5.QtSvg import QGraphicsSvgItem
            # Chemin vers le fichier SVG du logo
            svg_path = "assets/logo.svg"  # À adapter selon votre structure
            svg_item = QGraphicsSvgItem(svg_path)
            svg_item.setScale(self.logo_size / 100.0)  # Ajuster la taille
            return svg_item
        except ImportError:
            print("Module SVG non disponible, utilisation du logo textuel")
            return self.create_text_logo()
        except FileNotFoundError:
            print("Fichier SVG non trouvé, utilisation du logo textuel")
            return self.create_text_logo()
            
    def create_geometric_logo(self):
        """Crée un logo avec des formes géométriques"""
        # Créer un groupe d'éléments
        items = []
        
        # Cercle principal
        circle = QGraphicsEllipseItem(0, 0, self.logo_size, self.logo_size)
        circle.setBrush(QBrush(QColor(100, 150, 255)))
        circle.setPen(QPen(QColor(255, 255, 255), 2))
        items.append(circle)
        
        # Texte au centre
        text = QGraphicsTextItem("BM")
        text.setDefaultTextColor(QColor(255, 255, 255))
        font = QFont("Arial", 12, QFont.Bold)
        text.setFont(font)
        
        # Centrer le texte
        text_rect = text.boundingRect()
        text.setPos((self.logo_size - text_rect.width()) / 2,
                   (self.logo_size - text_rect.height()) / 2)
        items.append(text)
        
        # Grouper les éléments
        group = self.scene.createItemGroup(items)
        return group
        
    def update_logo_position(self):
        """Met à jour la position du logo"""
        if not self.logo_item or not self.show_logo:
            return
            
        # Obtenir les dimensions de la vue
        view_rect = self.viewport().rect()
        scene_rect = self.scene.sceneRect()
        
        # Calculer la position selon le paramètre
        if self.logo_position == "top_left":
            pos = QPointF(scene_rect.left() + 20, scene_rect.top() + 20)
        elif self.logo_position == "top_right":
            pos = QPointF(scene_rect.right() - self.logo_size - 20, scene_rect.top() + 20)
        elif self.logo_position == "bottom_left":
            pos = QPointF(scene_rect.left() + 20, scene_rect.bottom() - self.logo_size - 20)
        elif self.logo_position == "bottom_right":
            pos = QPointF(scene_rect.right() - self.logo_size - 20, scene_rect.bottom() - self.logo_size - 20)
        elif self.logo_position == "center":
            pos = QPointF((scene_rect.left() + scene_rect.right()) / 2 - self.logo_size / 2,
                         (scene_rect.top() + scene_rect.bottom()) / 2 - self.logo_size / 2)
        else:
            pos = QPointF(scene_rect.left() + 20, scene_rect.top() + 20)
            
        self.logo_item.setPos(pos)
        
    def toggle_logo(self):
        """Bascule l'affichage du logo"""
        self.show_logo = not self.show_logo
        if self.logo_item:
            self.logo_item.setVisible(self.show_logo)
            
    def set_logo_position(self, position):
        """Change la position du logo"""
        valid_positions = ["top_left", "top_right", "bottom_left", "bottom_right", "center"]
        if position in valid_positions:
            self.logo_position = position
            self.update_logo_position()
            
    def set_logo_size(self, size):
        """Change la taille du logo"""
        self.logo_size = max(20, min(200, size))  # Limiter entre 20 et 200
        self.create_logo_item()
        self.update_logo_position()
        
    def keyPressEvent(self, event):
        """Gère les événements clavier"""
        if event.key() == Qt.Key_Escape:
            # Annuler le mode de liaison d'association
            if self.selecting_entities_for_association:
                self.selecting_entities_for_association = False
                self.association_in_creation = None
                self.setCursor(Qt.ArrowCursor)
                print("Mode de liaison annulé.")
                return
            # Annuler le mode création de liens
            elif self.link_creation_mode:
                self.cancel_link_creation()
                print("Mode création de liens annulé.")
                return
            # Sortir des modes de création d'entités et d'associations
            elif self.current_mode in ["add_entity", "add_association"]:
                self.set_mode_select()
                print("Retour au mode sélection.")
                return
        elif event.key() in self.shortcuts:
            self.shortcuts[event.key()]()
        else:
            super().keyPressEvent(event)
            
    def mousePressEvent(self, event):
        """Gère l'événement de clic avec support du mode création de liens"""
        scene_pos = self.mapToScene(event.pos())
        item = self.scene.itemAt(scene_pos, self.transform())
        
        print(f"[DEBUG] mousePressEvent: current_mode='{self.current_mode}', button={event.button()}, scene_pos={scene_pos}")
        print(f"[DEBUG] Item sous le curseur: {item}")
        
        if event.button() == Qt.LeftButton:
            if hasattr(self, 'link_creation_mode') and self.link_creation_mode:
                # Mode création de liens
                print("[DEBUG] Mode link_creation_mode détecté")
                if item and hasattr(item, 'name'):
                    self.handle_link_creation_click(item)
                event.accept()
                return
            elif self.current_mode == "create_link":
                # Mode création de liens via bouton
                print("[DEBUG] Mode create_link détecté")
                if item and hasattr(item, 'name'):
                    if not hasattr(self, 'link_start_item') or self.link_start_item is None:
                        self.link_start_item = item
                        item.setSelected(True)
                        print(f"Premier élément sélectionné: {item.name}")
                    else:
                        # Terminer la création du lien
                        self.handle_link_creation_click(item)
                event.accept()
                return
            elif self.current_mode == "add_association":
                # Mode création d'association
                print(f"[DEBUG] Mode add_association détecté, création d'association à {scene_pos}")
                self.create_association(scene_pos)
                event.accept()
                return
            elif self.current_mode == "add_entity":
                # Mode création d'entité
                print(f"[DEBUG] Mode add_entity détecté, création d'entité à {scene_pos}")
                self.create_entity(scene_pos)
                event.accept()
                return
            else:
                # Mode normal - gérer la sélection et le déplacement
                print(f"[DEBUG] Mode normal détecté: {self.current_mode}")
                self.handle_select_mode(event, scene_pos)
                event.accept()
                return
        else:
            # Clic droit pour menu contextuel
            if event.button() == Qt.RightButton:
                self.show_context_menu(event, scene_pos)
                event.accept()
                return
            else:
                super().mousePressEvent(event)
            
        # Forcer l'acceptation de l'événement
        event.accept()
            
    def mouseMoveEvent(self, event):
        """Gère l'événement de mouvement avec prévisualisation des liens"""
        if self.link_creation_mode:
            scene_pos = self.mapToScene(event.pos())
            self.update_link_preview(scene_pos)
            event.accept()
            return
        else:
            super().mouseMoveEvent(event)
            
    def mouseReleaseEvent(self, event):
        """Gère les événements de relâchement de souris"""
        if event.button() == Qt.LeftButton:
            if self.dragging:
                # Finaliser le déplacement
                self.dragging = False
                self.setCursor(Qt.ArrowCursor)
                
                # Sauvegarder la position finale des éléments déplacés
                for item in self.selected_items:
                    if isinstance(item, (Entity, Association)):
                        item.setData(0, item.pos())
                
                # Mettre à jour les liens après déplacement
                self.update_association_links()
                
                # Émettre le signal de modification
                self.diagram_modified.emit()
                
            # Vérifier si on a glissé d'un élément vers un autre pour créer un lien automatique
            if hasattr(self, 'drag_start_item') and self.drag_start_item:
                scene_pos = self.mapToScene(event.pos())
                end_item = self.scene.itemAt(scene_pos, self.transform())
                
                if (end_item and end_item != self.drag_start_item and 
                    isinstance(end_item, (Entity, Association)) and
                    isinstance(self.drag_start_item, (Entity, Association))):
                    
                    # Créer un lien automatique
                    self.create_automatic_link(self.drag_start_item, end_item)
                
                self.drag_start_item = None
            
    def wheelEvent(self, event):
        """Gère le zoom avec la molette"""
        if event.modifiers() == Qt.ControlModifier:
            factor = self.zoom_factor if event.angleDelta().y() > 0 else 1.0 / self.zoom_factor
            self.zoom_at(self.mapToScene(event.pos()), factor)
        else:
            super().wheelEvent(event)
            
    def handle_select_mode(self, event, scene_pos):
        """Gère le mode sélection avec déplacement fluide"""
        item = self.scene.itemAt(scene_pos, self.transform())
        if item:
            if isinstance(item, (Entity, Association)):
                # Si on est en mode création d'association, créer un lien
                if self.selecting_entities_for_association and isinstance(item, Entity):
                    if self.association_in_creation:
                        # Vérifier si cette entité n'est pas déjà liée à cette association
                        already_linked = False
                        for link_data in self.association_links:
                            if len(link_data) >= 3:
                                assoc, entity, arrow = link_data[:3]
                            if assoc == self.association_in_creation and entity == item:
                                already_linked = True
                                break
                        
                        if not already_linked:
                            # Créer le lien entre l'association et l'entité
                            self.create_association_link(self.association_in_creation, item)
                            # Ajouter l'entité à l'association
                            self.association_in_creation.add_entity(item.name)
                            print(f"Lien créé entre {self.association_in_creation.name} et {item.name}")
                            self.diagram_modified.emit()
                        else:
                            print(f"Lien déjà existant entre {self.association_in_creation.name} et {item.name}")
                        return
                
                # Gestion de la sélection - CORRECTION ICI
                if event.modifiers() == Qt.ControlModifier:
                    # Sélection multiple
                    if item in self.selected_items:
                        self.selected_items.remove(item)
                        item.setSelected(False)
                    else:
                        self.selected_items.append(item)
                        item.setSelected(True)
                else:
                    # Sélection simple - NE PAS EFFACER LES AUTRES ÉLÉMENTS
                    # Juste sélectionner l'élément cliqué
                    item.setSelected(True)
                    if item not in self.selected_items:
                        self.selected_items.append(item)
                
                # Démarrer le déplacement (toujours possible)
                self.dragging = True
                self.last_mouse_pos = scene_pos
                self.drag_start_pos = scene_pos
                self.drag_start_item = item  # Capturer l'élément de départ pour les liens automatiques
                self.initial_item_positions = {}
                for selected_item in self.selected_items:
                    self.initial_item_positions[selected_item] = selected_item.pos()
                
                # Changer le curseur pour indiquer le déplacement
                self.setCursor(Qt.ClosedHandCursor)
                print(f"[Canvas] Déplacement démarré pour {item}")
        else:
            # Clic dans le vide : désélectionner seulement si pas de Ctrl
            if not event.modifiers() == Qt.ControlModifier:
                self.clear_selection()
            self.dragging = False
            self.setCursor(Qt.ArrowCursor)
            
    # Suppression des méthodes handle_relation_mode, create_relation, update_relation_line, set_mode_relation, start_relation
            
    def handle_drag(self, event, scene_pos):
        """Gère le glisser-déposer avec déplacement fluide"""
        if self.selected_items and self.dragging and hasattr(self, 'initial_item_positions'):
            # Calculer le déplacement depuis la position de départ
            delta = scene_pos - self.drag_start_pos
            
            for item in self.selected_items:
                if isinstance(item, (Entity, Association)):
                    # Utiliser la position initiale sauvegardée
                    initial_pos = self.initial_item_positions.get(item, item.pos())
                    new_pos = initial_pos + delta
                    
                    # Snap à la grille si activé
                    if self.snap_to_grid:
                        new_pos = self.snap_to_grid_pos(new_pos)
                    
                    # Appliquer la nouvelle position
                    item.setPos(new_pos)
            
            # Mettre à jour les liens d'association et d'héritage après déplacement
            self.update_association_links()
            self.update_inheritance_links()
            self.diagram_modified.emit()
            
    def create_entity(self, pos):
        """Crée une nouvelle entité à une position libre - Version améliorée style Db-Main"""
        print(f"[DEBUG] create_entity() appelée avec pos={pos}")
        try:
            # Demander le nom de l'entité
            print("[DEBUG] Affichage du dialogue de nom d'entité...")
            name, ok = QInputDialog.getText(self, "Nouvelle entité", "Nom de l'entité:")
            print(f"[DEBUG] Dialogue fermé: name='{name}', ok={ok}")
            
            if ok and name and name.strip():
                name = name.strip()
                
                # Vérifier si une entité avec ce nom existe déjà
                existing_entities = [item for item in self.scene.items() 
                                   if isinstance(item, Entity) and item.name == name]
                if existing_entities:
                    QMessageBox.warning(self, "Entité existante", 
                                      f"Une entité nommée '{name}' existe déjà.")
                    return
                
                # Trouver une position libre
                free_pos = self.find_free_position(pos, "entity")
                
                # Créer l'entité
                entity = Entity(name, free_pos)
                
                # Ajouter des données pour identifier l'élément
                entity.setData(0, "entity")
                entity.setData(1, name)
                
                # Vérifier que l'entité n'est pas déjà dans la scène
                if entity not in self.scene.items():
                    self.scene.addItem(entity)
                    
                    # Ajouter à l'historique
                    self.add_to_history("create_entity", entity)
                    
                    # Émettre les signaux
                    self.entity_created.emit(entity)
                    self.diagram_modified.emit()
                    
                    # Connexion automatique si activée (désactivée temporairement)
                    # if self.auto_connect_enabled:
                    #     try:
                    #         connection = self.smart_connector.auto_connect_new_item(entity)
                    #         if connection:
                    #             self.smart_connections.append(connection)
                    #             self.scene.addItem(connection)
                    #     except AttributeError:
                    #         print("Fonctionnalité de connexion automatique non disponible")
                    #     self.update_smart_connections()
                    
                    # Sélectionner la nouvelle entité
                    self.clear_selection()
                    entity.setSelected(True)
                    self.selected_items = [entity]
                    
                    # Détection automatique des liens après création d'entité
                    self.auto_detect_connections()
                    
                    # Gérer le mode création multiple
                    if self.multiple_creation_mode:
                        # Mode création multiple : rester en mode création
                        print(f"Entité '{name}' créée ! Mode création multiple actif. Cliquez pour créer une autre entité.")
                    else:
                        # Mode création unique : demander si continuer
                        from PyQt5.QtWidgets import QMessageBox
                        reply = QMessageBox.question(self, "Continuer ?", 
                            f"Entité '{name}' créée avec succès !\n\n"
                            "Voulez-vous créer une autre entité ?\n"
                            "(Appuyez sur M pour activer le mode création multiple)",
                            QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
                        
                        if reply == QMessageBox.No:
                            # Retourner au mode sélection
                            self.set_mode_select()
                            print("Retour au mode sélection.")
                        else:
                            # Rester en mode création
                            print(f"Mode création d'entités reste actif. Cliquez pour créer une autre entité.")
                else:
                    print(f"Erreur: L'entité est déjà dans la scène")
                    
            else:
                print("Création d'entité annulée par l'utilisateur")
                
        except Exception as e:
            print(f"Erreur lors de la création de l'entité: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la création de l'entité : {e}")

    def create_association(self, pos):
        """Crée une nouvelle association robuste, inspirée de Db-Main"""
        print(f"[DEBUG] create_association() appelée avec pos={pos}")
        try:
            # Demander le nom de l'association
            print("[DEBUG] Affichage du dialogue de nom...")
            name, ok = QInputDialog.getText(self, "Nouvelle association", "Nom de l'association:")
            print(f"[DEBUG] Dialogue fermé: name='{name}', ok={ok}")
            
            if not (ok and name and name.strip()):
                print("Création d'association annulée par l'utilisateur")
                return
                
            name = name.strip()
            print(f"[DEBUG] Nom validé: '{name}'")
            
            # Vérifier l'unicité du nom
            existing = [item for item in self.scene.items() if isinstance(item, Association) and item.name == name]
            if existing:
                print(f"[DEBUG] Association '{name}' existe déjà")
                QMessageBox.warning(self, "Association existante", f"Une association nommée '{name}' existe déjà.")
                return
                
            # Trouver une position libre
            print(f"[DEBUG] Recherche position libre...")
            free_pos = self.find_free_position(pos, "association")
            print(f"[DEBUG] Position libre trouvée: {free_pos}")
            
            # Créer l'association
            print(f"[DEBUG] Création de l'objet Association...")
            association = Association(name, free_pos)
            print(f"[DEBUG] Association créée: {association}")
            
            association.setData(0, "association")
            association.setData(1, name)
            
            print(f"[DEBUG] Ajout à la scène...")
            self.scene.addItem(association)
            print(f"[DEBUG] Ajouté à la scène avec succès")
            
            self.add_to_history("create_association", association)
            self.association_created.emit(association)
            self.diagram_modified.emit()
            
            # Sélectionner l'association
            print(f"[DEBUG] Sélection de l'association...")
            self.clear_selection()
            association.setSelected(True)
            self.selected_items = [association]
            # Détection automatique des liens après création d'association
            self.auto_detect_connections()
            
            # Gérer le mode création multiple
            if self.multiple_creation_mode:
                # Mode création multiple : rester en mode création
                print(f"Association '{name}' créée ! Mode création multiple actif. Cliquez pour créer une autre association.")
            else:
                # Mode création unique : demander si continuer
                from PyQt5.QtWidgets import QMessageBox
                reply = QMessageBox.question(self, "Continuer ?", 
                    f"Association '{name}' créée avec succès !\n\n"
                    "Voulez-vous créer une autre association ?\n"
                    "(Appuyez sur M pour activer le mode création multiple)",
                    QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
                
                if reply == QMessageBox.No:
                    # Retourner au mode sélection
                    self.set_mode_select()
                    print("Retour au mode sélection.")
                else:
                    # Rester en mode création
                    print(f"Mode création d'associations reste actif. Cliquez pour créer une autre association.")
                
        except Exception as e:
            print(f"Erreur lors de la création de l'association: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la création de l'association : {e}")
            
    def find_free_position(self, pos, item_type="entity"):
        """Trouve une position libre pour éviter les chevauchements"""
        # Taille approximative des éléments
        if item_type == "entity":
            width, height = 120, 80
        else:  # association
            width, height = 100, 60
            
        # Position initiale
        test_pos = pos
        offset = 50  # Distance entre les éléments
        max_attempts = 20
        
        for attempt in range(max_attempts):
            # Vérifier si la position est libre
            is_free = True
            test_rect = QRectF(test_pos.x() - width/2, test_pos.y() - height/2, width, height)
            
            for item in self.scene.items():
                if isinstance(item, (Entity, Association)):
                    item_rect = QRectF(item.pos().x() - width/2, item.pos().y() - height/2, width, height)
                    if test_rect.intersects(item_rect):
                        is_free = False
                        break
            
            if is_free:
                return test_pos
                
            # Essayer une nouvelle position
            if attempt % 4 == 0:
                test_pos = QPointF(pos.x() + offset * (attempt // 4 + 1), pos.y())
            elif attempt % 4 == 1:
                test_pos = QPointF(pos.x() - offset * (attempt // 4 + 1), pos.y())
            elif attempt % 4 == 2:
                test_pos = QPointF(pos.x(), pos.y() + offset * (attempt // 4 + 1))
            else:
                test_pos = QPointF(pos.x(), pos.y() - offset * (attempt // 4 + 1))
        
        # Si aucune position libre n'est trouvée, retourner la position originale
        return pos
            
    def snap_to_grid_pos(self, pos):
        """Snappe une position à la grille"""
        x = round(pos.x() / self.grid_size) * self.grid_size
        y = round(pos.y() / self.grid_size) * self.grid_size
        return QPointF(x, y)
        
    def set_mode(self, mode):
        """Change le mode actuel"""
        print(f"[DEBUG] set_mode() appelée avec mode='{mode}'")
        self.current_mode = mode
        self.current_tool = mode
        self.setCursor(self.get_cursor_for_mode(mode))
        print(f"[DEBUG] Mode changé vers: {self.current_mode}")
        
    def get_cursor_for_mode(self, mode):
        """Retourne le curseur approprié pour le mode"""
        if mode == "select":
            return Qt.ArrowCursor
        elif mode == "add_entity":
            return Qt.CrossCursor
        elif mode == "add_association":
            return Qt.CrossCursor
        elif mode == "add_relation":
            return Qt.CrossCursor
        return Qt.ArrowCursor
        
    def set_mode_select(self):
        self.set_mode("select")
        
    def set_mode_entity(self):
        print(f"[DEBUG] set_mode_entity() appelée, ancien mode: {self.current_mode}")
        self.set_mode("add_entity")
        print(f"[DEBUG] Nouveau mode: {self.current_mode}")
        
    def set_mode_association(self):
        print(f"[DEBUG] set_mode_association() appelée, ancien mode: {self.current_mode}")
        self.set_mode("add_association")
        print(f"[DEBUG] Nouveau mode: {self.current_mode}")
        
    # Suppression des méthodes handle_relation_mode, create_relation, update_relation_line, set_mode_relation, start_relation
            
    def zoom_at(self, pos, factor):
        """Zoom à une position spécifique"""
        new_zoom = self.current_zoom * factor
        if self.min_zoom <= new_zoom <= self.max_zoom:
            self.current_zoom = new_zoom
            self.setTransform(QTransform().scale(new_zoom, new_zoom))
            
    def zoom_in(self):
        self.zoom_at(self.mapToScene(self.viewport().rect().center()), self.zoom_factor)
        
    def zoom_out(self):
        self.zoom_at(self.mapToScene(self.viewport().rect().center()), 1.0 / self.zoom_factor)
        
    def fit_view(self):
        """Ajuste la vue pour voir tout le diagramme"""
        self.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)
        self.current_zoom = 1.0
        
    def toggle_grid(self):
        """Bascule l'affichage de la grille"""
        self.show_grid = not self.show_grid
        self.viewport().update()
        
    def delete_selected(self):
        """Supprime les éléments sélectionnés"""
        if self.selected_items:
            for item in self.selected_items:
                # Supprimer les liens d'association et d'héritage liés à cet élément
                self.remove_association_links_for_item(item)
                self.remove_inheritance_links_for_item(item)
                self.add_to_history("delete_item", item)
                self.scene.removeItem(item)
            self.selected_items.clear()
            self.diagram_modified.emit()
            print(f"[Canvas] Éléments supprimés, liens nettoyés")
            
    def copy_selected(self):
        """Copie les éléments sélectionnés"""
        # TODO: Implémenter la copie
        pass
        
    def paste_items(self):
        """Colle les éléments copiés"""
        # TODO: Implémenter le collage
        pass
        
    def duplicate_selected(self):
        """Duplique les éléments sélectionnés"""
        # TODO: Implémenter la duplication
        pass
        
    def set_cardinality(self, cardinality):
        """Définit la cardinalité pour les relations"""
        # TODO: Implémenter la cardinalité
        pass
        
    def clear_selection(self):
        """Efface la sélection"""
        for item in self.selected_items:
            if hasattr(item, 'setSelected'):
                item.setSelected(False)
        self.selected_items.clear()
        
    def select_all(self):
        """Sélectionne tous les éléments"""
        self.clear_selection()
        for item in self.scene.items():
            if isinstance(item, (Entity, Association)):
                self.selected_items.append(item)
                item.setSelected(True)
        self.diagram_modified.emit()
        

        
    def show_context_menu(self, event, pos):
        """Menu contextuel amélioré avec options intuitives"""
        menu = QMenu()
        
        # Actions principales
        create_entity_action = menu.addAction("➕ Créer une entité")
        create_association_action = menu.addAction("🔗 Créer une association")
        
        menu.addSeparator()
        
        # Actions de navigation
        zoom_in_action = menu.addAction("🔍 Zoom avant")
        zoom_out_action = menu.addAction("🔍 Zoom arrière")
        fit_action = menu.addAction("📐 Ajuster à la vue")
        grid_action = menu.addAction("📏 Afficher/Masquer grille")
        
        menu.addSeparator()
        
        # Actions d'édition
        if self.selected_items:
            delete_action = menu.addAction("🗑️ Supprimer la sélection")
            copy_action = menu.addAction("📋 Copier")
            duplicate_action = menu.addAction("📄 Dupliquer")
            
            menu.addSeparator()
            
            # Actions spécifiques aux associations
            if any(isinstance(item, Association) for item in self.selected_items):
                link_action = menu.addAction("🔗 Lier à des entités")
                unlink_action = menu.addAction("🔗 Supprimer les liens")
        
        # Actions du logo
        menu.addSeparator()
        logo_submenu = menu.addMenu("🎨 Logo")
        toggle_logo_action = logo_submenu.addAction("👁️ Afficher/Masquer logo")
        
        # Sous-menu pour la position du logo
        position_submenu = logo_submenu.addMenu("📍 Position du logo")
        positions = [
            ("top_left", "↖️ Coin supérieur gauche"),
            ("top_right", "↗️ Coin supérieur droit"),
            ("bottom_left", "↙️ Coin inférieur gauche"),
            ("bottom_right", "↘️ Coin inférieur droit"),
            ("center", "🎯 Centre")
        ]
        
        for pos_key, pos_name in positions:
            action = position_submenu.addAction(pos_name)
            action.triggered.connect(lambda checked, p=pos_key: self.set_logo_position(p))
        
        # Actions d'import/export
        menu.addSeparator()
        export_action = menu.addAction("💾 Exporter MCD")
        import_action = menu.addAction("📂 Importer MCD")
        
        # Connexion des actions
        create_entity_action.triggered.connect(lambda: self.create_entity(pos))
        create_association_action.triggered.connect(lambda: self.create_association(pos))
        zoom_in_action.triggered.connect(self.zoom_in)
        zoom_out_action.triggered.connect(self.zoom_out)
        fit_action.triggered.connect(self.fit_view)
        grid_action.triggered.connect(self.toggle_grid)
        toggle_logo_action.triggered.connect(self.toggle_logo)
        
        if self.selected_items:
            delete_action.triggered.connect(self.delete_selected)
            copy_action.triggered.connect(self.copy_selected)
            duplicate_action.triggered.connect(self.duplicate_selected)
            
            if any(isinstance(item, Association) for item in self.selected_items):
                link_action.triggered.connect(lambda: self.start_link_mode())
                unlink_action.triggered.connect(lambda: self.remove_all_links())
        
        export_action.triggered.connect(lambda: self.export_mcd_to_json())
        import_action.triggered.connect(lambda: self.show_import_dialog())
        
        # Convertir QPointF en QPoint pour exec_()
        screen_pos = event.screenPos()
        menu.exec_(QPoint(int(screen_pos.x()), int(screen_pos.y())))

    def start_link_mode(self):
        """Démarre le mode de liaison pour une association sélectionnée"""
        associations = [item for item in self.selected_items if isinstance(item, Association)]
        if associations:
            self.association_in_creation = associations[0]
            self.selecting_entities_for_association = True
            self.setCursor(Qt.CrossCursor)
            QMessageBox.information(self, "Mode liaison", 
                f"Cliquez sur les entités à relier à l'association '{self.association_in_creation.name}'.\n"
                "Double-cliquez sur l'association pour terminer.")

    def remove_all_links(self):
        """Supprime tous les liens d'une association sélectionnée"""
        associations = [item for item in self.selected_items if isinstance(item, Association)]
        if associations:
            association = associations[0]
            self.remove_association_links_for_item(association)
            QMessageBox.information(self, "Liens supprimés", 
                f"Tous les liens de l'association '{association.name}' ont été supprimés.")

    def show_import_dialog(self):
        """Affiche le dialogue d'import MCD"""
        from PyQt5.QtWidgets import QFileDialog
        filename, _ = QFileDialog.getOpenFileName(
            self, "Importer MCD", "", "JSON Files (*.json);;All Files (*)"
        )
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    json_data = f.read()
                if self.import_mcd_from_json(json_data):
                    QMessageBox.information(self, "Succès", "MCD importé avec succès !")
                else:
                    QMessageBox.critical(self, "Erreur", "Erreur lors de l'import du MCD")
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Erreur lors de l'import : {e}")
        
    def add_to_history(self, action, item):
        """Ajoute une action à l'historique"""
        self.undo_stack.append({"action": action, "item": item})
        if len(self.undo_stack) > self.max_history:
            self.undo_stack.pop(0)
        self.redo_stack.clear()
        
    def undo(self):
        """Annule la dernière action"""
        if self.undo_stack:
            action_data = self.undo_stack.pop()
            self.redo_stack.append(action_data)
            # TODO: Implémenter l'annulation
            self.diagram_modified.emit()
            
    def redo(self):
        """Répète la dernière action annulée"""
        if self.redo_stack:
            action_data = self.redo_stack.pop()
            self.undo_stack.append(action_data)
            # TODO: Implémenter la répétition
            self.diagram_modified.emit()
            
    def drawBackground(self, painter, rect):
        """Dessine l'arrière-plan avec la grille"""
        super().drawBackground(painter, rect)
        
        if self.show_grid:
            self.draw_grid(painter, rect)
            
    def draw_grid(self, painter, rect):
        """Dessine la grille"""
        grid_style = DarkTheme.get_grid_style()
        
        painter.setPen(QPen(QColor(grid_style["minor_lines"]), 1, Qt.DotLine))
        
        # Lignes verticales
        x = rect.left()
        while x <= rect.right():
            painter.drawLine(int(x), int(rect.top()), int(x), int(rect.bottom()))
            x += self.grid_size
            
        # Lignes horizontales
        y = rect.top()
        while y <= rect.bottom():
            painter.drawLine(int(rect.left()), int(y), int(rect.right()), int(y))
            y += self.grid_size
            
        # Lignes principales tous les 5 carreaux
        painter.setPen(QPen(QColor(grid_style["major_lines"]), 1, Qt.SolidLine))
        
        x = rect.left()
        while x <= rect.right():
            if int(x) % (self.grid_size * 5) == 0:
                painter.drawLine(int(x), int(rect.top()), int(x), int(rect.bottom()))
            x += self.grid_size
            
        y = rect.top()
        while y <= rect.bottom():
            if int(y) % (self.grid_size * 5) == 0:
                painter.drawLine(int(rect.left()), int(y), int(rect.right()), int(y))
            y += self.grid_size
            
    def export_mcd_to_json(self):
        """Exporte le MCD en format JSON"""
        mcd_data = self.get_mcd_data()
        return json.dumps(mcd_data, indent=2, ensure_ascii=False)
        
    def import_mcd_from_json(self, json_data):
        """Importe un MCD depuis un JSON"""
        try:
            mcd_data = json.loads(json_data)
            self.load_mcd_data(mcd_data)
            return True
        except Exception as e:
            print(f"Erreur lors de l'import: {e}")
            return False
            
    def get_mcd_data(self):
        """Récupère toutes les données du MCD"""
        mcd_data = {
            "entities": [],
            "associations": [],
            "inheritance_links": [],
            "association_links": []
        }
        
        # Récupérer les entités
        for item in self.scene.items():
            if isinstance(item, Entity):
                entity_data = {
                    "name": item.name,
                    "position": {"x": item.pos().x(), "y": item.pos().y()},
                    "attributes": item.attributes,
                    "is_weak": item.is_weak,
                    "parent_entity": item.parent_entity.name if item.parent_entity else None
                }
                mcd_data["entities"].append(entity_data)
                
        # Récupérer les associations
        for item in self.scene.items():
            if isinstance(item, Association):
                association_data = {
                    "name": item.name,
                    "position": {"x": item.pos().x(), "y": item.pos().y()},
                    "attributes": item.attributes,
                    "entities": item.entities,
                    "cardinalities": item.cardinalities
                }
                mcd_data["associations"].append(association_data)
                
        # Récupérer les liens d'héritage
        for parent, child, line in self.inheritance_links:
            inheritance_data = {
                "parent": parent.name,
                "child": child.name
            }
            mcd_data["inheritance_links"].append(inheritance_data)
            
        # Récupérer les liens d'association
        for assoc, entity, arrow in self.association_links:
            link_data = {
                "association": assoc.name,
                "entity": entity.name,
                "cardinality": "1,N"  # Valeur par défaut
            }
            mcd_data["association_links"].append(link_data)
            
        return mcd_data
        
    def load_mcd_data(self, mcd_data):
        """Charge les données MCD dans le canvas"""
        # Vider le canvas
        self.scene.clear()
        self.association_links = []
        self.inheritance_links = []
        
        # Créer les entités
        entities_dict = {}
        for entity_data in mcd_data.get("entities", []):
            entity = Entity(entity_data["name"], 
                          QPointF(entity_data["position"]["x"], entity_data["position"]["y"]))
            entity.attributes = entity_data.get("attributes", [])
            entity.is_weak = entity_data.get("is_weak", False)
            self.scene.addItem(entity)
            entities_dict[entity_data["name"]] = entity
            
        # Créer les associations
        associations_dict = {}
        for assoc_data in mcd_data.get("associations", []):
            association = Association(assoc_data["name"],
                                   QPointF(assoc_data["position"]["x"], assoc_data["position"]["y"]))
            association.attributes = assoc_data.get("attributes", [])
            association.entities = assoc_data.get("entities", [])
            association.cardinalities = assoc_data.get("cardinalities", {})
            self.scene.addItem(association)
            associations_dict[assoc_data["name"]] = association
            
        # Créer les liens d'héritage
        for inheritance_data in mcd_data.get("inheritance_links", []):
            parent = entities_dict.get(inheritance_data["parent"])
            child = entities_dict.get(inheritance_data["child"])
            if parent and child:
                self.create_inheritance_link(parent, child)
                child.add_inheritance_link(parent)
                
        # Créer les liens d'association
        for link_data in mcd_data.get("association_links", []):
            association = associations_dict.get(link_data["association"])
            entity = entities_dict.get(link_data["entity"])
            if association and entity:
                cardinality = link_data.get("cardinality", "1,N")
                self.create_association_link(association, entity, cardinality)
                
    def finish_association_links(self):
        """Termine la sélection des entités pour l'association en cours avec feedback"""
        if self.association_in_creation:
            # Compter les liens créés pour cette association
            link_count = 0
            for assoc, entity, arrow in self.association_links:
                if assoc == self.association_in_creation:
                    link_count += 1
            
            print(f"[Canvas] Association '{self.association_in_creation.name}' terminée avec {link_count} lien(s)")
            
            # Feedback utilisateur
            if link_count > 0:
                QMessageBox.information(self, "Liaison terminée", 
                    f"Association '{self.association_in_creation.name}' liée à {link_count} entité(s).\n"
                    "Vous pouvez maintenant créer d'autres associations ou modifier les liens existants.")
            else:
                QMessageBox.warning(self, "Aucune liaison", 
                    f"Association '{self.association_in_creation.name}' créée mais non liée.\n"
                    "Vous pouvez la lier plus tard en cliquant dessus puis sur les entités.")
            
        self.selecting_entities_for_association = False
        self.association_in_creation = None
        self.setCursor(Qt.ArrowCursor) 

    def update_association_links(self):
        """Met à jour les positions des liens d'association"""
        for assoc, entity, arrow in self.association_links:
            if assoc and entity and arrow and arrow in self.scene.items():
                # Mettre à jour la flèche (elle se met à jour automatiquement)
                if hasattr(arrow, 'update_path'):
                    arrow.update_path()
                print(f"[Canvas] Lien mis à jour entre {assoc.name} et {entity.name}")
                
    def update_inheritance_links(self):
        """Met à jour les positions des liens d'héritage"""
        for parent, child, line in self.inheritance_links:
            if parent and child and line:
                # Recalculer les positions
                parent_pos = parent.pos()
                child_pos = child.pos()
                
                # Mettre à jour la ligne d'héritage
                line.setLine(parent_pos.x(), parent_pos.y(), child_pos.x(), child_pos.y())
                
    def create_inheritance_link(self, parent_entity, child_entity):
        """Crée un lien d'héritage visuel"""
        # Créer la ligne d'héritage avec une flèche spéciale
        line = self.scene.addLine(
            parent_entity.pos().x(), parent_entity.pos().y(),
            child_entity.pos().x(), child_entity.pos().y(),
            QPen(QColor(100, 200, 100), 2, Qt.SolidLine)
        )
        
        # Ajouter une flèche pour indiquer l'héritage
        # TODO: Implémenter une flèche plus sophistiquée
        
        self.inheritance_links.append((parent_entity, child_entity, line))
        
    def remove_inheritance_links_for_item(self, item):
        """Supprime tous les liens d'héritage liés à un élément"""
        links_to_remove = []
        for parent, child, line in self.inheritance_links:
            if parent == item or child == item:
                if line in self.scene.items():
                    self.scene.removeItem(line)
                links_to_remove.append((parent, child, line))
        
        # Retirer les liens de la liste
        for link in links_to_remove:
            if link in self.inheritance_links:
                self.inheritance_links.remove(link)
                
    def remove_association_links_for_item(self, item):
        """Supprime tous les liens d'association liés à un élément"""
        links_to_remove = []
        for assoc, entity, line in self.association_links:
            if assoc == item or entity == item:
                # Supprimer la ligne
                if line in self.scene.items():
                    self.scene.removeItem(line)
                links_to_remove.append((assoc, entity, line))
        
        # Retirer les liens de la liste
        for link in links_to_remove:
            if link in self.association_links:
                self.association_links.remove(link)
                
        print(f"[Canvas] Liens supprimés pour l'élément {item.name if hasattr(item, 'name') else 'inconnu'}")

    def create_association_link(self, association, entity, cardinality="1,N"):
        """Crée un lien performant entre une association et une entité avec flèche flexible"""
        print(f"[Canvas] Création de lien entre {association.name} et {entity.name}")
        try:
            # Parser la cardinalité (format "1,N" ou "start,end")
            if "," in cardinality:
                parts = cardinality.split(",")
                cardinality_start = parts[0] if len(parts) > 0 else "1"
                cardinality_end = parts[1] if len(parts) > 1 else "N"
            else:
                cardinality_start = "1"
                cardinality_end = cardinality if cardinality else "N"
            
            # Créer une flèche performante
            arrow = PerformanceArrow(association, entity, cardinality_start, cardinality_end)
            
            # Connecter les signaux pour mettre à jour la flèche quand les éléments bougent
            if hasattr(association, 'position_changed'):
                association.position_changed.connect(arrow.update_path)
            if hasattr(entity, 'position_changed'):
                entity.position_changed.connect(arrow.update_path)
            
            # Ajouter à la scène
            self.scene.addItem(arrow)
            
            # Stocker le lien
            self.association_links.append((association, entity, arrow))
            
            # Mettre à jour la cardinalité dans l'association
            if hasattr(association, 'set_cardinality'):
                association.set_cardinality(entity.name, cardinality)
            
            # Ajouter l'entité à l'association
            if hasattr(association, 'add_entity'):
                association.add_entity(entity.name, cardinality)
            
            # Connecter le signal de modification de la flèche
            arrow.signals.arrow_modified.connect(self.diagram_modified.emit)
            arrow.signals.cardinality_changed.connect(
                lambda end, card: association.set_cardinality(entity.name, card) if end == "end" else None
            )
            
            print(f"[Canvas] Lien créé avec succès avec flèche performante")
            self.diagram_modified.emit()
            
        except Exception as e:
            print(f"[Canvas] Erreur lors de la création du lien: {e}")
            import traceback
            traceback.print_exc()
            return

    def edit_cardinality_dialog(self, association, entity, arrow):
        """Ouvre le dialogue d'édition de cardinalité pour un lien flexible"""
        from PyQt5.QtWidgets import QInputDialog
        cardinalities = ["0,1", "1,1", "0,N", "1,N", "N,N"]
        current = association.cardinalities.get(entity.name, "1,N")
        cardinality, ok = QInputDialog.getItem(self, f"Cardinalité pour {entity.name}", "Cardinalité:", cardinalities, cardinalities.index(current) if current in cardinalities else 3, False)
        if ok:
            association.set_cardinality(entity.name, cardinality)
            # Mettre à jour la cardinalité dans la flèche flexible
            if hasattr(arrow, 'set_cardinality'):
                arrow.set_cardinality(entity.name, cardinality)
            self.diagram_modified.emit()

    def show_link_context_menu(self, event, association, entity, arrow):
        """Menu contextuel spécifique à un lien association-entité hybride"""
        menu = QMenu()
        edit_action = menu.addAction("✏️ Éditer la cardinalité")
        delete_action = menu.addAction("🗑️ Supprimer le lien")
        style_action = menu.addAction("🎨 Changer le style")
        # Actions futures : inverser, etc.
        edit_action.triggered.connect(lambda: self.edit_cardinality_dialog(association, entity, arrow))
        delete_action.triggered.connect(lambda: self.delete_association_link(association, entity, arrow))
        style_action.triggered.connect(lambda: self.change_arrow_style(arrow))
        menu.exec_(event.screenPos())

    def delete_association_link(self, association, entity, arrow):
        """Supprime un lien association-entité hybride"""
        if arrow in self.scene.items():
            self.scene.removeItem(arrow)
        self.association_links = [l for l in self.association_links if l[2] != arrow]
        if entity.name in association.entities:
            association.remove_entity(entity.name)
        self.diagram_modified.emit()
        
    def change_arrow_style(self, arrow):
        """Change le style d'une flèche hybride"""
        from PyQt5.QtWidgets import QInputDialog
        styles = ["smart", "straight", "curved", "stepped", "orthogonal"]
        current_style = arrow.style.value
        style, ok = QInputDialog.getItem(self, "Changer le style", "Style:", styles, styles.index(current_style) if current_style in styles else 0, False)
        if ok:
            from models.hybrid_arrow import ArrowStyle
            arrow.set_style(ArrowStyle(style))
            self.diagram_modified.emit() 

    def resizeEvent(self, event):
        """Gère le redimensionnement de la vue"""
        super().resizeEvent(event)
        self.update_logo_position()
        
    def showEvent(self, event):
        """Gère l'affichage de la vue"""
        super().showEvent(event)
        self.update_logo_position()
    
    def update_smart_connections(self):
        """Met à jour les connexions intelligentes quand les éléments bougent"""
        # Mettre à jour les obstacles
        for item in self.scene.items():
            if hasattr(item, 'name'):  # Entités et associations
                self.smart_connector.update_obstacle(item)
        
        # Mettre à jour toutes les connexions
        for connection in self.smart_connections:
            if connection.start_item and connection.end_item:
                connection.update_path()
                
    def toggle_auto_connect(self):
        """Active/désactive la connexion automatique"""
        self.auto_connect_enabled = not self.auto_connect_enabled
        if self.auto_connect_enabled:
            self.update_smart_connections()
    
    def optimize_all_connections(self):
        """Optimise toutes les connexions existantes"""
        self.smart_connector.optimize_connections()
    
    def get_connection_stats(self):
        """Retourne les statistiques de connexion"""
        return self.smart_connector.get_connection_statistics() 

    def auto_detect_connections(self):
        """Détecte automatiquement les connexions entre associations et entités proches - Style DB-MAIN"""
        print("[Canvas] Détection automatique des connexions...")
        
        # Récupérer toutes les entités et associations
        entities = [item for item in self.scene.items() if isinstance(item, Entity)]
        associations = [item for item in self.scene.items() if isinstance(item, Association)]
        
        print(f"[Canvas] Trouvé {len(entities)} entités et {len(associations)} associations")
        
        connections_created = 0
        
        for association in associations:
            print(f"[Canvas] Vérification de l'association: {association.name}")
            # Trouver les entités proches de cette association
            nearby_entities = self.find_nearby_entities(association, entities, max_distance=200)
            print(f"[Canvas] Entités proches de {association.name}: {[e.name for e in nearby_entities]}")
            
            for entity in nearby_entities:
                # Vérifier si la connexion n'existe pas déjà
                if not self.connection_exists(association, entity):
                    print(f"[Canvas] Création de lien entre {association.name} et {entity.name}")
                    # Créer la connexion automatiquement avec cardinalité par défaut
                    self.create_association_link(association, entity, "1,N")
                    connections_created += 1
                    print(f"[Canvas] Connexion automatique créée: {association.name} ↔ {entity.name}")
                else:
                    print(f"[Canvas] Lien déjà existant entre {association.name} et {entity.name}")
        
        if connections_created > 0:
            print(f"[Canvas] {connections_created} connexion(s) créée(s) automatiquement !")
            QMessageBox.information(self, "Connexions automatiques", 
                f"{connections_created} connexion(s) créée(s) automatiquement !\n\n"
                "Les entités proches des associations ont été liées.")
        else:
            print("[Canvas] Aucune nouvelle connexion détectée.")
            QMessageBox.information(self, "Connexions automatiques", 
                "Aucune nouvelle connexion détectée.\n\n"
                "Toutes les entités proches des associations sont déjà connectées.")
                    
    def find_nearby_entities(self, association, entities, max_distance=200):
        """Trouve les entités proches d'une association - Style DB-MAIN intelligent"""
        nearby = []
        assoc_pos = association.pos()
        
        print(f"[Canvas] Recherche d'entités proches de {association.name} à la position {assoc_pos}")
        
        for entity in entities:
            # Ignorer les entités déjà connectées
            if self.connection_exists(association, entity):
                print(f"[Canvas] {entity.name} déjà connectée à {association.name}")
                continue
                
            entity_pos = entity.pos()
            distance = math.sqrt(
                (assoc_pos.x() - entity_pos.x())**2 + 
                (assoc_pos.y() - entity_pos.y())**2
            )
            
            print(f"[Canvas] Distance entre {association.name} et {entity.name}: {distance:.1f}")
            
            if distance <= max_distance:
                nearby.append((entity, distance))
                print(f"[Canvas] {entity.name} ajoutée à la liste des entités proches")
        
        # Trier par distance et retourner les plus proches
        nearby.sort(key=lambda x: x[1])
        
        # Limiter à 3 connexions par association pour plus de flexibilité
        result = [entity for entity, _ in nearby[:3]]
        print(f"[Canvas] Entités proches trouvées: {[e.name for e in result]}")
        return result
        
    def connection_exists(self, association, entity):
        """Vérifie si une connexion existe déjà entre une association et une entité"""
        for assoc, ent, connection in self.association_links:
            if assoc == association and ent == entity:
                return True
        return False 

    def set_mode_create_link(self):
        """Active le mode création de liens style Db-Main"""
        self.current_mode = "create_link"
        self.setCursor(Qt.CrossCursor)
        print("Mode création de liens activé ! Cliquez sur deux éléments pour les relier.")
            
    def start_link_creation(self, start_item):
        """Commence la création d'un lien depuis un élément"""
        self.link_creation_mode = True
        self.link_start_item = start_item
        
        # Créer une ligne de prévisualisation
        if self.link_preview_line:
            self.scene.removeItem(self.link_preview_line)
        self.link_preview_line = self.scene.addLine(0, 0, 0, 0, QPen(QColor(255, 255, 0), 2, Qt.DashLine))
        
        self.setCursor(Qt.CrossCursor)
        
    def update_link_preview(self, mouse_pos):
        """Met à jour la prévisualisation du lien"""
        if self.link_preview_line and self.link_start_item:
            start_pos = self.link_start_item.pos()
            self.link_preview_line.setLine(start_pos.x(), start_pos.y(), mouse_pos.x(), mouse_pos.y())
            
    def finish_link_creation(self, end_item):
        """Termine la création d'un lien"""
        if not self.link_start_item or not end_item:
            return
            
        # Déterminer le type de lien
        if hasattr(self.link_start_item, 'attributes'):  # Entité
            if hasattr(end_item, 'attributes'):  # Vers une autre entité
                # Créer une association entre les deux entités
                self.create_association_between_entities(self.link_start_item, end_item)
            else:  # Vers une association
                self.create_association_link(end_item, self.link_start_item, "1,N")
        else:  # Association
            if hasattr(end_item, 'attributes'):  # Vers une entité
                self.create_association_link(self.link_start_item, end_item, "1,N")
            else:  # Vers une autre association (non supporté)
                QMessageBox.warning(self, "Lien non supporté", 
                    "Les liens entre associations ne sont pas supportés.")
                    
        # Nettoyer
        self.cleanup_link_creation() 

    def cleanup_link_creation(self):
        """Nettoie le mode création de liens"""
        self.link_creation_mode = False
        self.link_start_item = None
        if self.link_preview_line:
            self.scene.removeItem(self.link_preview_line)
            self.link_preview_line = None
        self.setCursor(Qt.ArrowCursor) 

    def create_link_between_items(self, item1, item2, cardinality1="1", cardinality2="N"):
        """Crée un lien entre deux éléments (entité-association) style Db-Main"""
        try:
            # Déterminer quel élément est l'entité et lequel est l'association
            entity = None
            association = None
            
            if isinstance(item1, Entity) and isinstance(item2, Association):
                entity = item1
                association = item2
            elif isinstance(item1, Association) and isinstance(item2, Entity):
                entity = item2
                association = item1
            else:
                QMessageBox.warning(self, "Type d'élément invalide", 
                                  "Un lien ne peut être créé qu'entre une entité et une association.")
                return False
            
            # Vérifier si le lien existe déjà
            if self.connection_exists(association, entity):
                QMessageBox.information(self, "Lien existant", 
                                      f"Un lien existe déjà entre '{entity.name}' et '{association.name}'.")
                return False
            
            # Créer le lien
            cardinality = f"{cardinality1},{cardinality2}"
            self.create_association_link(association, entity, cardinality)
            
            # Ajouter l'entité à l'association
            association.add_entity(entity.name)
            
            # Mettre à jour les connexions intelligentes
            if self.auto_connect_enabled:
                self.update_smart_connections()
            
            print(f"Lien créé entre '{entity.name}' et '{association.name}' avec cardinalité {cardinality}")
            return True
            
        except Exception as e:
            print(f"Erreur lors de la création du lien: {e}")
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la création du lien : {e}")
            return False
    
    def start_link_creation_mode(self):
        """Active le mode création de liens style Db-Main"""
        self.link_creation_mode = True
        self.setCursor(Qt.CrossCursor)
        print("Mode création de liens activé ! Cliquez sur deux éléments pour les relier.")
    
    def handle_link_creation_click(self, item):
        """Gère les clics en mode création de liens"""
        if not self.link_creation_mode:
            return
        
        if not hasattr(self, 'link_start_item'):
            self.link_start_item = None
        
        if self.link_start_item is None:
            # Premier clic - sélectionner le premier élément
            if isinstance(item, (Entity, Association)):
                self.link_start_item = item
                item.setSelected(True)
                print(f"Premier élément sélectionné: {item.name}")
        else:
            # Deuxième clic - créer le lien
            if isinstance(item, (Entity, Association)) and item != self.link_start_item:
                # Déterminer quel élément est l'entité et lequel est l'association
                entity = None
                association = None
                
                if isinstance(self.link_start_item, Entity) and isinstance(item, Association):
                    entity = self.link_start_item
                    association = item
                elif isinstance(self.link_start_item, Association) and isinstance(item, Entity):
                    entity = item
                    association = self.link_start_item
                else:
                    QMessageBox.warning(self, "Type d'élément invalide", 
                                      "Un lien ne peut être créé qu'entre une entité et une association.")
                    return
                
                # Vérifier si le lien existe déjà
                if self.connection_exists(association, entity):
                    QMessageBox.information(self, "Lien existant", 
                                          f"Un lien existe déjà entre '{entity.name}' et '{association.name}'.")
                    return
                
                # Créer le lien avec cardinalité par défaut
                self.create_association_link(association, entity, "1,N")
                
                print(f"Lien créé avec succès entre '{entity.name}' et '{association.name}'")
                
                # Réinitialiser le mode
                self.link_start_item = None
                self.link_creation_mode = False
                self.setCursor(Qt.ArrowCursor)
                self.clear_selection()
            else:
                QMessageBox.warning(self, "Élément invalide", 
                                  "Veuillez sélectionner un élément différent.")
    
    def cancel_link_creation(self):
        """Annule le mode création de liens"""
        self.link_creation_mode = False
        self.link_start_item = None
        self.setCursor(Qt.ArrowCursor)
        self.clear_selection()
        
    def create_automatic_link(self, item1, item2):
        """Crée automatiquement un lien entre deux éléments lors du glisser-déposer"""
        try:
            # Déterminer quel élément est l'entité et lequel est l'association
            entity = None
            association = None
            
            if isinstance(item1, Entity) and isinstance(item2, Association):
                entity = item1
                association = item2
            elif isinstance(item1, Association) and isinstance(item2, Entity):
                entity = item2
                association = item1
            else:
                # Si ce sont deux entités, créer une association entre elles
                if isinstance(item1, Entity) and isinstance(item2, Entity):
                    # Créer une association au milieu
                    mid_pos = QPointF(
                        (item1.pos().x() + item2.pos().x()) / 2,
                        (item1.pos().y() + item2.pos().y()) / 2
                    )
                    association = Association(f"Lien_{item1.name}_{item2.name}", mid_pos)
                    self.scene.addItem(association)
                    
                    # Créer les liens
                    self.create_association_link(association, item1, "1,N")
                    self.create_association_link(association, item2, "1,N")
                    
                    print(f"Association créée entre '{item1.name}' et '{item2.name}'")
                    return
                else:
                    print(f"[Canvas] Types d'éléments non supportés pour le lien automatique")
                    return
            
            # Vérifier si le lien existe déjà
            if self.connection_exists(association, entity):
                print(f"[Canvas] Lien déjà existant entre {association.name} et {entity.name}")
                return
            
            # Créer le lien
            self.create_association_link(association, entity, "1,N")
            
            print(f"Lien créé entre '{entity.name}' et '{association.name}'")
                
        except Exception as e:
            print(f"[Canvas] Erreur lors de la création du lien automatique: {e}")
            import traceback
            traceback.print_exc()
            
    def toggle_multiple_creation(self):
        """Bascule le mode création multiple"""
        self.multiple_creation_mode = not self.multiple_creation_mode
        if self.multiple_creation_mode:
            print("[Canvas] Mode création multiple activé - Vous pouvez créer plusieurs éléments d'affilée")
            QMessageBox.information(self, "Mode création multiple", 
                "Mode création multiple activé !\n\n"
                "Vous pouvez maintenant créer plusieurs entités/associations d'affilée\n"
                "sans avoir à confirmer à chaque fois.\n\n"
                "Appuyez sur M pour désactiver ce mode.")
        else:
            print("[Canvas] Mode création multiple désactivé")
            QMessageBox.information(self, "Mode création multiple", 
                "Mode création multiple désactivé.\n\n"
                "Vous devrez confirmer après chaque création d'élément.") 