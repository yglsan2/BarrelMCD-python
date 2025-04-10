from PyQt5.QtWidgets import (QGraphicsScene, QGraphicsView, QGraphicsItem,
                             QMenu, QInputDialog, QColorDialog, QFontDialog, QMessageBox)
from PyQt5.QtCore import Qt, QPointF, QRectF, QSizeF, QLineF, pyqtSignal
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush, QFont, QPainterPath
from .gestures import GestureManager
from .animations import AnimationManager
from .loop_animations import LoopAnimationManager
from .feedback import FeedbackManager

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
        
        # Initialisation des gestionnaires
        self.gesture_manager = GestureManager(self)
        self.animation_manager = AnimationManager(self)
        self.loop_animation_manager = LoopAnimationManager(self)
        self.feedback_manager = FeedbackManager(self)
        self.touch_optimizer = TouchOptimizer(self)

        # ... existing code ... 

    def start_item_pulse(self, item: QGraphicsItem, scale_factor: float = 1.1, 
                        duration: int = 1000, repeat_count: int = -1):
        """Démarre une animation de pulsation en boucle pour un élément
        
        Args:
            item: L'élément à animer
            scale_factor: Facteur d'échelle pour la pulsation
            duration: Durée d'une pulsation en ms
            repeat_count: Nombre de répétitions (-1 pour infini)
        """
        self.loop_animation_manager.start_pulse_loop(item, scale_factor, duration, repeat_count)
        
    def start_item_rotation(self, item: QGraphicsItem, angle: float = 360,
                           duration: int = 2000, repeat_count: int = -1):
        """Démarre une animation de rotation en boucle pour un élément
        
        Args:
            item: L'élément à animer
            angle: Angle de rotation en degrés
            duration: Durée d'une rotation en ms
            repeat_count: Nombre de répétitions (-1 pour infini)
        """
        self.loop_animation_manager.start_rotation_loop(item, angle, duration, repeat_count)
        
    def start_item_bounce(self, item: QGraphicsItem, distance: float = 10,
                         duration: int = 1000, repeat_count: int = -1):
        """Démarre une animation de rebond en boucle pour un élément
        
        Args:
            item: L'élément à animer
            distance: Distance de rebond en pixels
            duration: Durée d'un rebond en ms
            repeat_count: Nombre de répétitions (-1 pour infini)
        """
        self.loop_animation_manager.start_bounce_loop(item, distance, duration, repeat_count)
        
    def start_item_color_loop(self, item: QGraphicsItem, start_color: QColor,
                            end_color: QColor, duration: int = 1000,
                            repeat_count: int = -1):
        """Démarre une animation de changement de couleur en boucle pour un élément
        
        Args:
            item: L'élément à animer
            start_color: Couleur de départ
            end_color: Couleur d'arrivée
            duration: Durée d'une transition en ms
            repeat_count: Nombre de répétitions (-1 pour infini)
        """
        self.loop_animation_manager.start_color_loop(item, start_color, end_color, 
                                                   duration, repeat_count)
        
    def stop_item_animation(self, item: QGraphicsItem):
        """Arrête l'animation en boucle d'un élément
        
        Args:
            item: L'élément dont l'animation doit être arrêtée
        """
        self.loop_animation_manager.stop_loop(item)
        
    def stop_all_animations(self):
        """Arrête toutes les animations en boucle"""
        self.loop_animation_manager.stop_all_loops()
        self.animation_manager.stop_all_animations()

    # ... existing code ... 