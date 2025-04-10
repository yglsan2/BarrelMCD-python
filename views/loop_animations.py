from PyQt5.QtCore import QObject, QPropertyAnimation, QEasingCurve, QPointF, QRectF, QTimer
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush
from PyQt5.QtWidgets import QGraphicsItem

class LoopAnimationManager(QObject):
    """Gestionnaire d'animations en boucle pour les éléments graphiques"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.loop_animations = {}
        self.animation_timers = {}
        
    def start_pulse_loop(self, item: QGraphicsItem, scale_factor: float = 1.1, 
                        duration: int = 1000, repeat_count: int = -1):
        """Démarre une animation de pulsation en boucle
        
        Args:
            item: L'élément à animer
            scale_factor: Facteur d'échelle pour la pulsation
            duration: Durée d'une pulsation en ms
            repeat_count: Nombre de répétitions (-1 pour infini)
        """
        if item in self.loop_animations:
            self.stop_loop(item)
            
        # Animation d'échelle
        animation = QPropertyAnimation(item, b"scale")
        animation.setDuration(duration)
        animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        animation.setStartValue(1.0)
        animation.setEndValue(scale_factor)
        animation.setLoopCount(repeat_count)
        
        # Timer pour l'animation inverse
        timer = QTimer()
        timer.timeout.connect(lambda: self._reverse_pulse(item, scale_factor, duration))
        timer.start(duration)
        
        self.loop_animations[item] = animation
        self.animation_timers[item] = timer
        animation.start()
        
    def start_rotation_loop(self, item: QGraphicsItem, angle: float = 360,
                           duration: int = 2000, repeat_count: int = -1):
        """Démarre une animation de rotation en boucle
        
        Args:
            item: L'élément à animer
            angle: Angle de rotation en degrés
            duration: Durée d'une rotation en ms
            repeat_count: Nombre de répétitions (-1 pour infini)
        """
        if item in self.loop_animations:
            self.stop_loop(item)
            
        animation = QPropertyAnimation(item, b"rotation")
        animation.setDuration(duration)
        animation.setEasingCurve(QEasingCurve.Type.Linear)
        animation.setStartValue(item.rotation())
        animation.setEndValue(angle)
        animation.setLoopCount(repeat_count)
        
        self.loop_animations[item] = animation
        animation.start()
        
    def start_bounce_loop(self, item: QGraphicsItem, distance: float = 10,
                         duration: int = 1000, repeat_count: int = -1):
        """Démarre une animation de rebond en boucle
        
        Args:
            item: L'élément à animer
            distance: Distance de rebond en pixels
            duration: Durée d'un rebond en ms
            repeat_count: Nombre de répétitions (-1 pour infini)
        """
        if item in self.loop_animations:
            self.stop_loop(item)
            
        original_pos = item.pos()
        
        # Animation de rebond
        animation = QPropertyAnimation(item, b"pos")
        animation.setDuration(duration)
        animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        animation.setStartValue(original_pos)
        animation.setEndValue(QPointF(original_pos.x(), original_pos.y() - distance))
        animation.setLoopCount(repeat_count)
        
        self.loop_animations[item] = animation
        animation.start()
        
    def start_color_loop(self, item: QGraphicsItem, start_color: QColor,
                        end_color: QColor, duration: int = 1000,
                        repeat_count: int = -1):
        """Démarre une animation de changement de couleur en boucle
        
        Args:
            item: L'élément à animer
            start_color: Couleur de départ
            end_color: Couleur d'arrivée
            duration: Durée d'une transition en ms
            repeat_count: Nombre de répétitions (-1 pour infini)
        """
        if item in self.loop_animations:
            self.stop_loop(item)
            
        # Sauvegarde des styles originaux
        original_pen = item.pen()
        original_brush = item.brush()
        
        # Animation de couleur
        animation = QPropertyAnimation(item, b"brush")
        animation.setDuration(duration)
        animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        animation.setStartValue(QBrush(start_color))
        animation.setEndValue(QBrush(end_color))
        animation.setLoopCount(repeat_count)
        
        # Restauration des styles à la fin
        def restore_style():
            item.setPen(original_pen)
            item.setBrush(original_brush)
            
        animation.finished.connect(restore_style)
        self.loop_animations[item] = animation
        animation.start()
        
    def stop_loop(self, item: QGraphicsItem):
        """Arrête l'animation en boucle d'un élément
        
        Args:
            item: L'élément dont l'animation doit être arrêtée
        """
        if item in self.loop_animations:
            self.loop_animations[item].stop()
            del self.loop_animations[item]
            
        if item in self.animation_timers:
            self.animation_timers[item].stop()
            del self.animation_timers[item]
            
    def stop_all_loops(self):
        """Arrête toutes les animations en boucle"""
        for item in self.loop_animations.keys():
            self.stop_loop(item)
            
    def _reverse_pulse(self, item: QGraphicsItem, scale_factor: float, duration: int):
        """Inverse l'animation de pulsation
        
        Args:
            item: L'élément à animer
            scale_factor: Facteur d'échelle
            duration: Durée de l'animation
        """
        if item not in self.loop_animations:
            return
            
        animation = self.loop_animations[item]
        animation.setStartValue(scale_factor)
        animation.setEndValue(1.0)
        animation.start() 