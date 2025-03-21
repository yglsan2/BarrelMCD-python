import sys
import math
from PyQt6.QtWidgets import (QGraphicsScene, QGraphicsView, QGraphicsItem,
                             QMenu, QInputDialog, QColorDialog, QFontDialog, QMessageBox)
from PyQt6.QtCore import Qt, QPointF, QRectF, QSizeF, QLineF, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QPainterPath
from .gestures import GestureManager
from .animations import AnimationManager
from .feedback import FeedbackManager
from .responsive_styles import ResponsiveStyles
from .touch_optimizer import TouchOptimizer
from .help_system import HelpSystem
from .styles import AppStyles
from .error_handler import ErrorHandler
from .advanced_associations import AdvancedAssociations
from .dialogs import AttributeDialog, CardinalityDialog

from ..models.entity import Entity
from ..models.association import Association
from ..models.magnetic_arrow import MagneticArrow
from ..models.attribute import Attribute

class DiagramCanvas(QGraphicsView):
    # Signaux
    item_selected = pyqtSignal(object)
    item_deselected = pyqtSignal(object)
    diagram_modified = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        
        # Configuration de base
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        
        # État
        self.current_mode = "select"  # select, add_entity, add_association, add_relation
        self.relation_source = None
        self.relation_line = None
        self.current_style = None
        
        # Zoom
        self.zoom_factor = 1.15
        self.min_zoom = 0.1
        self.max_zoom = 5.0
        
        # Grille
        self.grid_size = ResponsiveStyles.get_grid_size()
        self.show_grid = True
        
        # Templates prédéfinis
        self.templates = {
            "user": {
                "name": "Utilisateur",
                "attributes": [
                    ("id", "INTEGER", True, True),
                    ("username", "VARCHAR(50)", True, True),
                    ("email", "VARCHAR(100)", True, True),
                    ("password_hash", "VARCHAR(255)", True, False),
                    ("created_at", "TIMESTAMP", True, False)
                ]
            },
            "product": {
                "name": "Produit",
                "attributes": [
                    ("id", "INTEGER", True, True),
                    ("name", "VARCHAR(100)", True, False),
                    ("description", "TEXT", False, False),
                    ("price", "DECIMAL(10,2)", True, False),
                    ("stock", "INTEGER", True, False)
                ]
            },
            "order": {
                "name": "Commande",
                "attributes": [
                    ("id", "INTEGER", True, True),
                    ("user_id", "INTEGER", True, False),
                    ("total_amount", "DECIMAL(10,2)", True, False),
                    ("status", "VARCHAR(20)", True, False),
                    ("created_at", "TIMESTAMP", True, False)
                ]
            }
        }
        
        # Raccourcis clavier
        self.setup_shortcuts()
        
        # Styles par défaut
        self.default_styles = {
            "entity": AppStyles.get_entity_style("default"),
            "association": AppStyles.get_association_style("default"),
            "arrow": AppStyles.get_relation_style("default")
        }
        
        # Initialisation des gestionnaires
        self.gesture_manager = GestureManager(self)
        self.animation_manager = AnimationManager(self)
        self.feedback_manager = FeedbackManager(self)
        self.touch_optimizer = TouchOptimizer(self)
        
        # Initialisation du système d'aide
        self.help_system = HelpSystem(self)
        
        # Initialisation du gestionnaire d'erreurs
        self.error_handler = ErrorHandler(self)
        self.error_handler.error_occurred.connect(self._show_error_dialog)
        self.error_handler.warning_occurred.connect(self._show_warning_dialog)
        self.error_handler.info_occurred.connect(self._show_info_dialog)
        
        # Connexion des signaux
        self.gesture_manager.pinch_zoom.connect(self.handle_pinch_zoom)
        self.gesture_manager.pan_started.connect(self.handle_pan_start)
        self.gesture_manager.pan_moved.connect(self.handle_pan_move)
        self.gesture_manager.pan_ended.connect(self.handle_pan_end)
        self.gesture_manager.double_tap.connect(self.handle_double_tap)
        self.gesture_manager.long_press.connect(self.handle_long_press)
        
        # Connexion des signaux d'aide
        self.help_system.tutorial_step_completed.connect(self._on_tutorial_step_completed)
        
        # Vérification des ressources système
        if not self.error_handler.check_system_resources():
            self.error_handler.handle_warning(
                "Certaines ressources système sont limitées. "
                "L'application pourrait fonctionner de manière suboptimale."
            )
            
        self.setup_ui()
        
        # Systèmes de support
        self.advanced_associations = AdvancedAssociations(self)
        
        # Connexion des signaux
        self.advanced_associations.association_created.connect(self._on_association_created)
        self.advanced_associations.association_modified.connect(self._on_association_modified)
        self.advanced_associations.association_deleted.connect(self._on_association_deleted)
        
    def setup_shortcuts(self):
        # Raccourcis pour les modes
        self.shortcuts = {
            Qt.Key.Key_S: self.set_mode_select,
            Qt.Key.Key_E: self.set_mode_entity,
            Qt.Key.Key_A: self.set_mode_association,
            Qt.Key.Key_R: self.set_mode_relation,
            Qt.Key.Key_Z: self.zoom_in,
            Qt.Key.Key_X: self.zoom_out,
            Qt.Key.Key_F: self.fit_view,
            Qt.Key.Key_G: self.toggle_grid,
            Qt.Key.Key_Delete: self.delete_selected,
            Qt.Key.Key_Control: self.start_relation,
            Qt.Key.Key_Shift: self.start_relation
        }
        
    def keyPressEvent(self, event):
        if event.key() in self.shortcuts:
            self.shortcuts[event.key()]()
        else:
            super().keyPressEvent(event)
            
    def set_mode_select(self):
        self.set_mode("select")
        
    def set_mode_entity(self):
        self.set_mode("add_entity")
        
    def set_mode_association(self):
        self.set_mode("add_association")
        
    def set_mode_relation(self):
        self.set_mode("add_relation")
        
    def start_relation(self):
        if self.current_mode == "select":
            self.set_mode("add_relation")
            
    def delete_selected(self):
        for item in self.scene.selectedItems():
            self.scene.removeItem(item)
            self.diagram_modified.emit()
            
    def toggle_grid(self):
        self.show_grid = not self.show_grid
        self.viewport().update()
        
    def setup_ui(self):
        # Configuration de la scène
        self.scene.setSceneRect(QRectF(-1000, -1000, 2000, 2000))
        
        # Ajout d'un fond blanc
        self.setBackgroundBrush(QBrush(QColor("#FFFFFF")))
        
    def drawBackground(self, painter, rect):
        super().drawBackground(painter, rect)
        
        if self.show_grid:
            grid_style = AppStyles.get_grid_style()
            
            # Dessiner la grille mineure
            painter.setPen(QPen(grid_style["color"], grid_style["line_width"]))
            
            left = int(rect.left()) - (int(rect.left()) % self.grid_size)
            top = int(rect.top()) - (int(rect.top()) % self.grid_size)
            
            lines = []
            x = left
            while x < rect.right():
                lines.append(QLineF(x, rect.top(), x, rect.bottom()))
                x += self.grid_size
                
            y = top
            while y < rect.bottom():
                lines.append(QLineF(rect.left(), y, rect.right(), y))
                y += self.grid_size
                
            painter.drawLines(lines)
            
            # Dessiner la grille majeure
            painter.setPen(QPen(grid_style["major_line_color"], grid_style["major_line_width"]))
            
            major_lines = []
            x = left
            while x < rect.right():
                if x % (self.grid_size * grid_style["major_line_spacing"]) == 0:
                    major_lines.append(QLineF(x, rect.top(), x, rect.bottom()))
                x += self.grid_size
                
            y = top
            while y < rect.bottom():
                if y % (self.grid_size * grid_style["major_line_spacing"]) == 0:
                    major_lines.append(QLineF(rect.left(), y, rect.right(), y))
                y += self.grid_size
                
            painter.drawLines(major_lines)
        
    def mousePressEvent(self, event):
        """Gère les événements de clic"""
        try:
        if event.button() == Qt.MouseButton.LeftButton:
                scene_pos = self.mapToScene(event.position().toPoint())
                
                # Aide contextuelle pour les éléments
                item = self.scene.itemAt(scene_pos, self.transform())
                if item:
                    self._show_item_help(item)
                    
                # Optimisation tactile
                if event.source() == Qt.MouseEvent.Source.TouchScreen:
                    self.touch_optimizer.process_touch_start(scene_pos)
                    return
                    
                # Mode sélection
                if self.current_mode == "select":
                    item = self.scene.itemAt(scene_pos, self.transform())
                    if item:
                        if isinstance(item, (Entity, Association)):
                            self.animation_manager.animate_item_highlight(item)
                            self.feedback_manager.show_tooltip(
                                f"Type: {item.__class__.__name__}",
                                scene_pos
                            )
                    else:
                        self.scene.clearSelection()
                        
                # Mode relation
            elif self.current_mode == "add_relation":
                    item = self.scene.itemAt(scene_pos, self.transform())
                    if item and isinstance(item, Entity):
                        if not self.relation_source:
                            self.relation_source = item
                            self.relation_line = self.scene.addLine(
                            scene_pos.x(), scene_pos.y(),
                            scene_pos.x(), scene_pos.y(),
                                QPen(QColor(52, 152, 219), 2, Qt.PenStyle.DashLine)
                            )
                            self.feedback_manager.show_tooltip(
                                "Sélectionnez la cible",
                                scene_pos
                            )
                        elif item != self.relation_source:
                            self.add_relation(self.relation_source, item)
                            self.relation_source = None
                            if self.relation_line:
                                self.scene.removeItem(self.relation_line)
                                self.relation_line = None
                
        except Exception as e:
            self.error_handler.handle_error(
                e,
                "Erreur lors du traitement du clic"
            )
                
    def mouseMoveEvent(self, event):
        """Gère les événements de mouvement"""
        try:
            scene_pos = self.mapToScene(event.position().toPoint())
            
            # Optimisation tactile
            if event.source() == Qt.MouseEvent.Source.TouchScreen:
                self.touch_optimizer.process_touch_move(scene_pos)
                return
            
            # Mise à jour de la ligne de relation
            if self.relation_line:
                source_pos = self.relation_source.scenePos()
                target_pos = scene_pos
                
                # Calcul des points d'ancrage magnétiques
                source_anchor = self._find_anchor_point(source_pos, target_pos, self.relation_source)
                target_anchor = self._find_anchor_point(target_pos, source_pos, None)
                
                # Mise à jour de la ligne
                self.relation_line.setLine(
                    source_anchor.x(), source_anchor.y(),
                    target_anchor.x(), target_anchor.y()
                )
            
            # Mise à jour de la grille
            if self.show_grid:
                self.feedback_manager.show_grid_snap(scene_pos)
            
        except Exception as e:
            self.error_handler.handle_error(
                e,
                "Erreur lors du traitement du mouvement"
            )
            
    def mouseReleaseEvent(self, event):
        """Gère les événements de relâchement"""
        if event.source() == Qt.MouseEvent.Source.TouchScreen:
            self.touch_optimizer.process_touch_end(self.mapToScene(event.position().toPoint()))
            return
            
        if event.button() == Qt.MouseButton.LeftButton:
            self.pan_active = False
            self.last_mouse_pos = None
            
    def wheelEvent(self, event):
        """Gère les événements de molette"""
        try:
            factor = 1.15
            if event.angleDelta().y() < 0:
                factor = 1.0 / factor
                
            self.zoom_at(event.position(), factor)
            
        except Exception as e:
            self.error_handler.handle_error(
                e,
                "Erreur lors du zoom"
            )
            
    def zoom_at(self, pos, factor):
        """Zoom à une position donnée"""
        try:
            # Vérification de la mémoire avant le zoom
            if not self.error_handler.check_memory_usage(threshold_mb=100):
                self.error_handler.handle_warning(
                    "Mémoire insuffisante",
                    "Le zoom pourrait être instable"
                )
                
            old_pos = self.mapToScene(pos.toPoint())
            self.scale(factor, factor)
            new_pos = self.mapToScene(pos.toPoint())
            delta = new_pos - old_pos
            self.translate(delta.x(), delta.y())
            self.zoom_level *= factor
            
        except Exception as e:
            self.error_handler.handle_error(
                e,
                "Erreur lors du zoom"
            )
            
    def zoom_in_at(self, pos):
        """Zoom avant à une position donnée"""
        self.zoom_at(pos, 1.15)
        
    def zoom_out_at(self, pos):
        """Zoom arrière à une position donnée"""
        self.zoom_at(pos, 1.0 / 1.15)
        
    def handle_pinch_zoom(self, factor):
        """Gère le zoom par pincement"""
        self.zoom_at(self.mapFromScene(self.touch_optimizer.touch_points[-1]), factor)
        
    def handle_pan_start(self):
        """Gère le début du panning"""
        self.pan_active = True
        self.last_mouse_pos = self.mapFromScene(self.touch_optimizer.touch_points[-1])
        
    def handle_pan_move(self, delta):
        """Gère le panning"""
        if self.pan_active and self.last_mouse_pos:
            self.translate(delta.x(), delta.y())
            self.last_mouse_pos = self.mapFromScene(self.touch_optimizer.touch_points[-1])
            
    def handle_pan_end(self):
        """Gère la fin du panning"""
        self.pan_active = False
        self.last_mouse_pos = None
        
    def handle_double_tap(self, pos):
        """Gère le double tap"""
        self.zoom_in_at(self.mapFromScene(pos))
        
    def handle_long_press(self, pos):
        """Gère l'appui long"""
        self.show_context_menu(self.mapFromScene(pos))
        
    def show_context_menu(self, pos):
        """Affiche le menu contextuel"""
        try:
            item = self.scene.itemAt(pos, self.transform())
            if not item:
                return
                
            menu = QMenu(self)
            
            if isinstance(item, Entity):
                menu.addAction("Renommer", lambda: self.rename_entity(item))
                menu.addAction("Supprimer", lambda: self.delete_item(item))
            elif isinstance(item, Association):
                menu.addAction("Modifier", lambda: self.edit_association(item))
                menu.addAction("Supprimer", lambda: self.delete_item(item))
                
            menu.exec(self.mapToGlobal(self.mapFromScene(pos)))
            
        except Exception as e:
            self.error_handler.handle_error(
                e,
                "Erreur lors de l'affichage du menu contextuel"
            )
        
    def rename_entity(self, entity):
        """Renomme une entité"""
        try:
            new_name, ok = QInputDialog.getText(
                self,
                "Renommer",
                "Nouveau nom:",
                text=entity.name
            )
            if ok and new_name:
                # Validation du nom
                if not self.error_handler.validate_input(
                    new_name,
                    lambda x: len(x.strip()) > 0,
                    "Le nom ne peut pas être vide"
                ):
                    return
                    
                entity.name = new_name
                entity.update()
                self.diagram_modified.emit()
                
        except Exception as e:
            self.error_handler.handle_error(
                e,
                "Erreur lors du renommage de l'entité"
            )
            
    def edit_association(self, association):
        """Modifie une association"""
        # TODO: Implémenter l'édition des associations
        pass
            
    def delete_item(self, item):
        """Supprime un élément"""
        try:
            # Vérification de la mémoire avant la suppression
            if not self.error_handler.check_memory_usage(threshold_mb=100):
                self.error_handler.handle_warning(
                    "Mémoire insuffisante",
                    "La suppression pourrait être instable"
                )
                
        self.scene.removeItem(item)
            self.diagram_modified.emit()
            
        except Exception as e:
            self.error_handler.handle_error(
                e,
                "Erreur lors de la suppression de l'élément"
            )
        
    def add_relation(self, source: Entity, target: Entity):
        """Ajoute une relation entre deux entités"""
        try:
            if source == target:
                self.error_handler.handle_warning(
                    "Impossible de créer une relation",
                    "Une entité ne peut pas être liée à elle-même"
                )
                return
                
            # Vérification de la mémoire avant d'ajouter la relation
            if not self.error_handler.check_memory_usage(threshold_mb=100):
                self.error_handler.handle_warning(
                    "Mémoire insuffisante",
                    "L'ajout de la relation pourrait être instable"
                )
                
            # Création de la flèche magnétique
            arrow = MagneticArrow(source, target)
            self.scene.addItem(arrow)
            
            # Connexion des signaux
            source.position_changed.connect(arrow.update_position)
            target.position_changed.connect(arrow.update_position)
            
            # Animation et feedback
            self.animation_manager.animate_item_highlight(arrow)
            self.feedback_manager.show_notification(
                "Relation créée",
                "success"
            )
            
            self.diagram_modified.emit()
            
        except Exception as e:
            self.error_handler.handle_error(
                e,
                "Erreur lors de la création de la relation"
            )
        
    def _find_anchor_point(self, source_pos: QPointF, target_pos: QPointF, item: Entity) -> QPointF:
        """Trouve le point d'ancrage optimal"""
        if not item:
            return target_pos
            
        # Calcul de l'angle entre les points
        dx = target_pos.x() - source_pos.x()
        dy = target_pos.y() - source_pos.y()
        angle = math.atan2(dy, dx)
        
        # Calcul des points d'intersection avec la boîte
        rect = item.boundingRect()
        center = item.scenePos() + QPointF(rect.center())
        
        # Ajustement en fonction de l'angle
        if abs(math.cos(angle)) > abs(math.sin(angle)):
            # Intersection horizontale
            x = center.x() + (rect.width() / 2) * (1 if dx > 0 else -1)
            y = center.y() + (rect.height() / 2) * math.tan(angle)
        else:
            # Intersection verticale
            x = center.x() + (rect.width() / 2) * math.atan(angle)
            y = center.y() + (rect.height() / 2) * (1 if dy > 0 else -1)
            
        return QPointF(x, y)

    def _show_item_help(self, item):
        """Affiche l'aide contextuelle pour un élément"""
        tooltip_style = AppStyles.get_ui_style("tooltip")
        
        if isinstance(item, Entity):
            self.help_system.show_tooltip(
                "Entité : Faites un appui long pour modifier",
                item.scenePos(),
                item,
                tooltip_style
            )
        elif isinstance(item, Association):
            self.help_system.show_tooltip(
                "Association : Faites un appui long pour modifier",
                item.scenePos(),
                item,
                tooltip_style
            )
        elif isinstance(item, MagneticArrow):
            self.help_system.show_tooltip(
                "Relation : Faites un appui long pour modifier",
                item.scenePos(),
                item,
                tooltip_style
            )
            
    def set_mode(self, mode):
        """Change le mode de l'application"""
        self.current_mode = mode
        self._show_mode_help(mode)
        
    def _show_mode_help(self, mode):
        """Affiche l'aide pour le mode actuel"""
        tooltip_style = AppStyles.get_ui_style("tooltip")
        
        help_texts = {
            "select": "Mode sélection : Cliquez sur un élément pour le sélectionner",
            "add_entity": "Mode entité : Cliquez sur le canvas pour créer une entité",
            "add_association": "Mode association : Cliquez sur le canvas pour créer une association",
            "add_relation": "Mode relation : Sélectionnez l'entité source puis l'entité cible"
        }
        
        if mode in help_texts:
            self.help_system.show_tooltip(
                help_texts[mode],
                QPointF(0, 0),
                duration=3000,
                style=tooltip_style
            )
            
    def start_tutorial(self, tutorial_name):
        """Démarre un tutoriel"""
        self.help_system.start_tutorial(tutorial_name)
        
    def show_quick_help(self):
        """Affiche l'aide rapide"""
        self.help_system.show_quick_help()
        
    def toggle_help(self):
        """Active/désactive l'aide"""
        self.help_system.toggle_help()
        
    def _on_tutorial_step_completed(self):
        """Gère la fin d'une étape de tutoriel"""
        if self.help_system.current_tutorial:
            self.help_system._show_next_step()

    def _show_error_dialog(self, title: str, message: str):
        """Affiche une boîte de dialogue d'erreur"""
        QMessageBox.critical(self, title, message)
        
    def _show_warning_dialog(self, title: str, message: str):
        """Affiche une boîte de dialogue d'avertissement"""
        QMessageBox.warning(self, title, message)
        
    def _show_info_dialog(self, title: str, message: str):
        """Affiche une boîte de dialogue d'information"""
        QMessageBox.information(self, title, message)

    def _on_association_created(self, association: Association):
        """Gère la création d'une association"""
        try:
            self.scene.addItem(association)
            self.diagram_modified.emit()
            
        except Exception as e:
            self.error_handler.handle_error(e, "Erreur lors de la création d'une association")
            
    def _on_association_modified(self, association: Association):
        """Gère la modification d'une association"""
        try:
            self.scene.update()
            self.diagram_modified.emit()
            
        except Exception as e:
            self.error_handler.handle_error(e, "Erreur lors de la modification d'une association")
            
    def _on_association_deleted(self, association: Association):
        """Gère la suppression d'une association"""
        try:
            self.scene.removeItem(association)
            self.diagram_modified.emit()
            
        except Exception as e:
            self.error_handler.handle_error(e, "Erreur lors de la suppression d'une association")
