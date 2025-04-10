from PyQt5.QtCore import QObject, Qt, QTimer, QPointF
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush, QFont
from PyQt5.QtWidgets import QGraphicsItem, QGraphicsTextItem

class FeedbackManager(QObject):
    """Gestionnaire des retours visuels et notifications"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.tooltips = []
        self.notifications = []
        self.highlights = []
        
    def show_tooltip(self, text: str, pos: QPointF, duration: int = 2000):
        """Affiche une infobulle"""
        tooltip = QGraphicsTextItem(text)
        tooltip.setDefaultTextColor(QColor(255, 255, 255))
        tooltip.setFont(QFont("Arial", 10))
        tooltip.setPos(pos)
        tooltip.setZValue(1000)
        
        # Style de l'infobulle
        tooltip.setBackgroundBrush(QBrush(QColor(0, 0, 0, 180)))
        tooltip.setPadding(5)
        
        # Animation d'apparition
        tooltip.setOpacity(0)
        self.parent().scene().addItem(tooltip)
        
        # Animation d'opacité
        animation = QPropertyAnimation(tooltip, b"opacity")
        animation.setDuration(200)
        animation.setStartValue(0)
        animation.setEndValue(1)
        animation.start()
        
        # Suppression après la durée
        QTimer.singleShot(duration, lambda: self._fade_out_tooltip(tooltip))
        
        self.tooltips.append(tooltip)
        
    def show_notification(self, text: str, type: str = "info", duration: int = 3000):
        """Affiche une notification"""
        notification = QGraphicsTextItem(text)
        notification.setDefaultTextColor(QColor(255, 255, 255))
        notification.setFont(QFont("Arial", 12))
        
        # Position en haut à droite
        scene = self.parent().scene()
        pos = QPointF(scene.width() - notification.boundingRect().width() - 20, 20)
        notification.setPos(pos)
        notification.setZValue(1000)
        
        # Style selon le type
        if type == "success":
            color = QColor(46, 204, 113, 180)
        elif type == "error":
            color = QColor(231, 76, 60, 180)
        elif type == "warning":
            color = QColor(241, 196, 15, 180)
        else:  # info
            color = QColor(52, 152, 219, 180)
            
        notification.setBackgroundBrush(QBrush(color))
        notification.setPadding(10)
        
        # Animation d'apparition
        notification.setOpacity(0)
        scene.addItem(notification)
        
        # Animation d'opacité
        animation = QPropertyAnimation(notification, b"opacity")
        animation.setDuration(200)
        animation.setStartValue(0)
        animation.setEndValue(1)
        animation.start()
        
        # Suppression après la durée
        QTimer.singleShot(duration, lambda: self._fade_out_notification(notification))
        
        self.notifications.append(notification)
        
    def highlight_item(self, item: QGraphicsItem, color: QColor = QColor(255, 255, 0, 100), duration: int = 1000):
        """Met en surbrillance un élément"""
        # Sauvegarde des styles originaux
        original_pen = item.pen()
        original_brush = item.brush()
        
        # Application de la surbrillance
        item.setPen(QPen(color, 2))
        item.setBrush(QBrush(color.lighter(120)))
        
        # Animation de retour
        def restore_style():
            item.setPen(original_pen)
            item.setBrush(original_brush)
            
        QTimer.singleShot(duration, restore_style)
        
        self.highlights.append(item)
        
    def show_connection_preview(self, start_pos: QPointF, current_pos: QPointF):
        """Affiche un aperçu de la connexion"""
        if not hasattr(self, '_preview_line'):
            self._preview_line = QGraphicsLineItem()
            self._preview_line.setPen(QPen(QColor(52, 152, 219), 2, Qt.PenStyle.DashLine))
            self._preview_line.setZValue(100)
            self.parent().scene().addItem(self._preview_line)
            
        self._preview_line.setLine(start_pos.x(), start_pos.y(), current_pos.x(), current_pos.y())
        
    def hide_connection_preview(self):
        """Cache l'aperçu de la connexion"""
        if hasattr(self, '_preview_line'):
            self._preview_line.setVisible(False)
            
    def show_grid_snap(self, pos: QPointF):
        """Affiche un indicateur de snap sur la grille"""
        if not hasattr(self, '_snap_indicator'):
            self._snap_indicator = QGraphicsEllipseItem()
            self._snap_indicator.setPen(QPen(QColor(52, 152, 219), 2))
            self._snap_indicator.setBrush(QBrush(QColor(52, 152, 219, 50)))
            self._snap_indicator.setRect(-5, -5, 10, 10)
            self._snap_indicator.setZValue(100)
            self.parent().scene().addItem(self._snap_indicator)
            
        self._snap_indicator.setPos(pos)
        self._snap_indicator.setVisible(True)
        
    def hide_grid_snap(self):
        """Cache l'indicateur de snap"""
        if hasattr(self, '_snap_indicator'):
            self._snap_indicator.setVisible(False)
            
    def _fade_out_tooltip(self, tooltip: QGraphicsTextItem):
        """Fait disparaître une infobulle"""
        animation = QPropertyAnimation(tooltip, b"opacity")
        animation.setDuration(200)
        animation.setStartValue(1)
        animation.setEndValue(0)
        animation.finished.connect(lambda: self._remove_tooltip(tooltip))
        animation.start()
        
    def _fade_out_notification(self, notification: QGraphicsTextItem):
        """Fait disparaître une notification"""
        animation = QPropertyAnimation(notification, b"opacity")
        animation.setDuration(200)
        animation.setStartValue(1)
        animation.setEndValue(0)
        animation.finished.connect(lambda: self._remove_notification(notification))
        animation.start()
        
    def _remove_tooltip(self, tooltip: QGraphicsTextItem):
        """Supprime une infobulle"""
        if tooltip in self.tooltips:
            self.tooltips.remove(tooltip)
            self.parent().scene().removeItem(tooltip)
            
    def _remove_notification(self, notification: QGraphicsTextItem):
        """Supprime une notification"""
        if notification in self.notifications:
            self.notifications.remove(notification)
            self.parent().scene().removeItem(notification) 