from PyQt5.QtCore import QObject, QPointF, QTimer, Qt
from PyQt5.QtGui import QPainterPath
import math

class TouchOptimizer(QObject):
    """Optimiseur des interactions tactiles"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.touch_points = []
        self.last_pos = None
        self.velocity = QPointF(0, 0)
        self.smoothing_factor = 0.3  # Facteur de lissage (0-1)
        self.velocity_threshold = 0.5  # Seuil de vitesse pour le swipe
        self.min_swipe_distance = 50  # Distance minimale pour un swipe
        self.last_touch_time = 0
        self.double_tap_timeout = 300  # ms
        self.long_press_timeout = 500  # ms
        self.pan_active = False
        self.zoom_active = False
        
    def process_touch_start(self, pos: QPointF):
        """Traite le début d'un contact tactile"""
        current_time = QTimer.currentTime()
        
        # Gestion du double tap
        if current_time - self.last_touch_time < self.double_tap_timeout:
            self.handle_double_tap(pos)
            return
            
        # Démarrer le timer pour l'appui long
        self.long_press_timer = QTimer()
        self.long_press_timer.setSingleShot(True)
        self.long_press_timer.timeout.connect(lambda: self.handle_long_press(pos))
        self.long_press_timer.start(self.long_press_timeout)
        
        self.touch_points = [pos]
        self.last_pos = pos
        self.velocity = QPointF(0, 0)
        self.last_touch_time = current_time
        
    def process_touch_move(self, pos: QPointF):
        """Traite le mouvement d'un contact tactile"""
        if not self.last_pos:
            return
            
        # Calcul de la vélocité
        delta = pos - self.last_pos
        self.velocity = self.smooth_velocity(delta)
        
        # Détection du type de geste
        if not self.pan_active and not self.zoom_active:
            if len(self.touch_points) == 2:
                self.detect_pinch_gesture()
            else:
                self.detect_pan_gesture()
                
        # Mise à jour des points de contact
        self.touch_points.append(pos)
        if len(self.touch_points) > 10:  # Limiter le nombre de points stockés
            self.touch_points.pop(0)
            
        self.last_pos = pos
        
    def process_touch_end(self, pos: QPointF):
        """Traite la fin d'un contact tactile"""
        if self.long_press_timer.isActive():
            self.long_press_timer.stop()
            
        if len(self.touch_points) > 1:
            # Détection du swipe
            if self.velocity.length() > self.velocity_threshold:
                self.handle_swipe()
                
        self.touch_points = []
        self.last_pos = None
        self.velocity = QPointF(0, 0)
        self.pan_active = False
        self.zoom_active = False
        
    def smooth_velocity(self, delta: QPointF) -> QPointF:
        """Lisse la vélocité du mouvement"""
        return self.velocity * (1 - self.smoothing_factor) + delta * self.smoothing_factor
        
    def detect_pan_gesture(self):
        """Détecte un geste de panning"""
        if len(self.touch_points) < 2:
            return
            
        # Calcul de la distance totale parcourue
        path = QPainterPath()
        path.moveTo(self.touch_points[0])
        for point in self.touch_points[1:]:
            path.lineTo(point)
            
        # Si la distance est suffisante, activer le panning
        if path.length() > self.min_swipe_distance:
            self.pan_active = True
            self.zoom_active = False
            
    def detect_pinch_gesture(self):
        """Détecte un geste de pincement"""
        if len(self.touch_points) < 2:
            return
            
        # Calcul de la distance entre les points
        current_distance = (self.touch_points[-1] - self.touch_points[-2]).length()
        initial_distance = (self.touch_points[0] - self.touch_points[1]).length()
        
        # Si la variation de distance est significative, activer le zoom
        if abs(current_distance - initial_distance) > 10:
            self.zoom_active = True
            self.pan_active = False
            
    def handle_swipe(self):
        """Gère un geste de swipe"""
        if len(self.touch_points) < 2:
            return
            
        # Calcul de la direction du swipe
        start = self.touch_points[0]
        end = self.touch_points[-1]
        direction = end - start
        
        # Déterminer la direction principale
        if abs(direction.x()) > abs(direction.y()):
            if direction.x() > 0:
                self.parent().pan_right()
            else:
                self.parent().pan_left()
        else:
            if direction.y() > 0:
                self.parent().pan_down()
            else:
                self.parent().pan_up()
                
    def handle_double_tap(self, pos: QPointF):
        """Gère un double tap"""
        self.parent().zoom_in_at(pos)
        
    def handle_long_press(self, pos: QPointF):
        """Gère un appui long"""
        self.parent().show_context_menu(pos)
        
    def get_smoothed_position(self, pos: QPointF) -> QPointF:
        """Retourne une position lissée"""
        if not self.last_pos:
            return pos
            
        # Lissage exponentiel
        return self.last_pos * (1 - self.smoothing_factor) + pos * self.smoothing_factor
        
    def get_gesture_scale(self) -> float:
        """Calcule le facteur d'échelle pour le zoom"""
        if len(self.touch_points) < 2:
            return 1.0
            
        current_distance = (self.touch_points[-1] - self.touch_points[-2]).length()
        initial_distance = (self.touch_points[0] - self.touch_points[1]).length()
        
        if initial_distance == 0:
            return 1.0
            
        return current_distance / initial_distance 