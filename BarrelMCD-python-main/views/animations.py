from PyQt5.QtCore import QObject, QPropertyAnimation, QEasingCurve, QPointF, QRectF
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush
from PyQt5.QtWidgets import QGraphicsItem

class AnimationManager(QObject):
    """Gestionnaire d'animations et de transitions visuelles"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.animations = []
        
    def animate_item_movement(self, item: QGraphicsItem, target_pos: QPointF, duration: int = 300):
        """Anime le déplacement d'un élément"""
        animation = QPropertyAnimation(item, b"pos")
        animation.setDuration(duration)
        animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        animation.setStartValue(item.pos())
        animation.setEndValue(target_pos)
        animation.start()
        self.animations.append(animation)
        
    def animate_item_resize(self, item: QGraphicsItem, target_rect: QRectF, duration: int = 300):
        """Anime le redimensionnement d'un élément"""
        animation = QPropertyAnimation(item, b"geometry")
        animation.setDuration(duration)
        animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        animation.setStartValue(item.geometry())
        animation.setEndValue(target_rect)
        animation.start()
        self.animations.append(animation)
        
    def animate_item_opacity(self, item: QGraphicsItem, target_opacity: float, duration: int = 300):
        """Anime l'opacité d'un élément"""
        animation = QPropertyAnimation(item, b"opacity")
        animation.setDuration(duration)
        animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        animation.setStartValue(item.opacity())
        animation.setEndValue(target_opacity)
        animation.start()
        self.animations.append(animation)
        
    def animate_item_highlight(self, item: QGraphicsItem, duration: int = 500):
        """Anime la mise en surbrillance d'un élément"""
        # Sauvegarde des styles originaux
        original_pen = item.pen()
        original_brush = item.brush()
        
        # Animation de la couleur
        highlight_color = QColor(255, 255, 0, 100)
        animation = QPropertyAnimation(item, b"brush")
        animation.setDuration(duration)
        animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        animation.setStartValue(original_brush)
        animation.setEndValue(QBrush(highlight_color))
        animation.start()
        
        # Animation de retour
        def restore_style():
            item.setPen(original_pen)
            item.setBrush(original_brush)
            
        animation.finished.connect(restore_style)
        self.animations.append(animation)
        
    def animate_item_pulse(self, item: QGraphicsItem, scale_factor: float = 1.1, duration: int = 300):
        """Anime l'effet de pulsation d'un élément"""
        # Sauvegarde de la transformation
        original_transform = item.transform()
        
        # Animation d'échelle
        animation = QPropertyAnimation(item, b"scale")
        animation.setDuration(duration)
        animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        animation.setStartValue(1.0)
        animation.setEndValue(scale_factor)
        animation.start()
        
        # Animation de retour
        def restore_scale():
            item.setTransform(original_transform)
            
        animation.finished.connect(restore_scale)
        self.animations.append(animation)
        
    def animate_item_rotation(self, item: QGraphicsItem, angle: float, duration: int = 300):
        """Anime la rotation d'un élément"""
        animation = QPropertyAnimation(item, b"rotation")
        animation.setDuration(duration)
        animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        animation.setStartValue(item.rotation())
        animation.setEndValue(angle)
        animation.start()
        self.animations.append(animation)
        
    def animate_item_shake(self, item: QGraphicsItem, intensity: float = 5.0, duration: int = 500):
        """Anime l'effet de secousse d'un élément"""
        original_pos = item.pos()
        
        # Création des positions pour l'animation
        positions = []
        steps = 10
        for i in range(steps):
            offset = intensity * (1 - i/steps) * (1 if i % 2 == 0 else -1)
            positions.append(QPointF(original_pos.x() + offset, original_pos.y()))
            
        # Animation séquentielle
        for i, pos in enumerate(positions):
            animation = QPropertyAnimation(item, b"pos")
            animation.setDuration(duration // steps)
            animation.setEasingCurve(QEasingCurve.Type.Linear)
            animation.setStartValue(item.pos())
            animation.setEndValue(pos)
            animation.start()
            self.animations.append(animation)
            
        # Retour à la position initiale
        final_animation = QPropertyAnimation(item, b"pos")
        final_animation.setDuration(duration // steps)
        final_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        final_animation.setStartValue(item.pos())
        final_animation.setEndValue(original_pos)
        final_animation.start()
        self.animations.append(final_animation)
        
    def stop_all_animations(self):
        """Arrête toutes les animations en cours"""
        for animation in self.animations:
            animation.stop()
        self.animations.clear() 