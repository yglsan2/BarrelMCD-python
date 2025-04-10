from PyQt5.QtWidgets import QGraphicsItem, QGraphicsTextItem
from PyQt5.QtCore import Qt, QRectF, QPointF, QLineF, QPropertyAnimation, QEasingCurve, QSizeF
from PyQt5.QtGui import QPainter, QPen, QColor, QPainterPath, QPainterPathStroker, QFont, QPainterPathElement

class MagneticArrow(QGraphicsItem):
    """Représente une flèche magnétique qui s'adapte aux entités et associations"""
    
    def __init__(self, source: QGraphicsItem, target: QGraphicsItem):
        super().__init__()
        self.source = source
        self.target = target
        self.setZValue(-1)  # Placer la flèche sous les autres éléments
        
        # Points d'ancrage magnétiques
        self.source_anchor = QPointF()
        self.target_anchor = QPointF()
        
        # Points de contrôle pour la courbe de Bézier
        self.control1 = QPointF()
        self.control2 = QPointF()
        
        # Points de contrôle supplémentaires pour des courbes complexes
        self.control_points = []
        self.selected_control = None
        
        # Style par défaut
        self.style = {
            "color": QColor(0, 0, 0),
            "width": 2,
            "arrow_size": 10,
            "magnet_strength": 0.3,  # Force d'attraction des points d'ancrage
            "curve_tension": 0.5,    # Tension de la courbe (0-1)
            "hover_effect": True,    # Effet au survol
            "show_control_points": False,  # Afficher les points de contrôle
            "line_style": "bezier",  # bezier, orthogonal, straight
            "cardinality": {
                "source": "1",
                "target": "N",
                "show": True
            }
        }
        
        # État
        self.is_hovered = False
        self.is_dragging = False
        self.drag_point = None
        self.is_editing = False
        
        # Animation
        self.animation = QPropertyAnimation(self, b"curve_tension")
        self.animation.setDuration(200)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        # Labels de cardinalité
        self.source_label = QGraphicsTextItem(self)
        self.target_label = QGraphicsTextItem(self)
        self._update_labels()
        
    def start_pulse_animation(self, scale_factor: float = 1.1, duration: int = 1000):
        """Démarre une animation de pulsation
        
        Args:
            scale_factor: Facteur d'échelle pour la pulsation
            duration: Durée d'une pulsation en ms
        """
        if hasattr(self, 'scene') and self.scene():
            canvas = self.scene().views()[0]
            canvas.start_item_pulse(self, scale_factor, duration)
            
    def start_rotation_animation(self, angle: float = 360, duration: int = 2000):
        """Démarre une animation de rotation
        
        Args:
            angle: Angle de rotation en degrés
            duration: Durée d'une rotation en ms
        """
        if hasattr(self, 'scene') and self.scene():
            canvas = self.scene().views()[0]
            canvas.start_item_rotation(self, angle, duration)
            
    def start_bounce_animation(self, distance: float = 10, duration: int = 1000):
        """Démarre une animation de rebond
        
        Args:
            distance: Distance de rebond en pixels
            duration: Durée d'un rebond en ms
        """
        if hasattr(self, 'scene') and self.scene():
            canvas = self.scene().views()[0]
            canvas.start_item_bounce(self, distance, duration)
            
    def start_color_animation(self, start_color: QColor, end_color: QColor, 
                            duration: int = 1000):
        """Démarre une animation de changement de couleur
        
        Args:
            start_color: Couleur de départ
            end_color: Couleur d'arrivée
            duration: Durée d'une transition en ms
        """
        if hasattr(self, 'scene') and self.scene():
            canvas = self.scene().views()[0]
            canvas.start_item_color_loop(self, start_color, end_color, duration)
            
    def stop_animation(self):
        """Arrête toutes les animations de la flèche"""
        if hasattr(self, 'scene') and self.scene():
            canvas = self.scene().views()[0]
            canvas.stop_item_animation(self) 