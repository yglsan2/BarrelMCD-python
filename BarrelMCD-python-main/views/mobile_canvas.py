from PyQt5.QtWidgets import QGraphicsView, QGraphicsScene
from PyQt5.QtCore import Qt, QRectF, QPointF
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush

from .responsive_styles import ResponsiveStyles

class MobileCanvas(QGraphicsView):
    """Canvas optimisé pour mobile"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Configuration de base
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        
        # Scène
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        
        # État
        self.zoom_factor = 1.0
        self.panning = False
        self.last_pos = None
        self.grid_size = ResponsiveStyles.get_grid_size(1.0)
        self.show_grid = True
        
        # Style
        self.setStyleSheet(ResponsiveStyles.get_canvas_style(1.0))
        
    def wheelEvent(self, event):
        """Gère le zoom avec le pinch-to-zoom"""
        if event.angleDelta().y() > 0:
            self.zoom(1.2)
        else:
            self.zoom(0.8)
            
    def mousePressEvent(self, event):
        """Gère le début du panning"""
        if event.button() == Qt.MouseButton.MiddleButton:
            self.panning = True
            self.last_pos = event.pos()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
        super().mousePressEvent(event)
        
    def mouseReleaseEvent(self, event):
        """Gère la fin du panning"""
        if event.button() == Qt.MouseButton.MiddleButton:
            self.panning = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
        super().mouseReleaseEvent(event)
        
    def mouseMoveEvent(self, event):
        """Gère le panning"""
        if self.panning and self.last_pos:
            delta = event.pos() - self.last_pos
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())
            self.last_pos = event.pos()
        super().mouseMoveEvent(event)
        
    def drawBackground(self, painter: QPainter, rect: QRectF):
        """Dessine le fond et la grille"""
        # Fond blanc
        painter.fillRect(rect, QColor(255, 255, 255))
        
        if self.show_grid:
            # Grille
            painter.setPen(QPen(QColor(200, 200, 200), 1))
            
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
            
    def zoom(self, factor: float):
        """Applique un zoom"""
        self.zoom_factor *= factor
        self.scale(factor, factor)
        
    def fit_to_view(self):
        """Ajuste la vue pour afficher tout le contenu"""
        if self.scene.items():
            self.setSceneRect(self.scene.itemsBoundingRect())
            self.fitInView(self.scene.itemsBoundingRect(), Qt.AspectRatioMode.KeepAspectRatio)
            
    def resizeEvent(self, event):
        """Gère le redimensionnement"""
        super().resizeEvent(event)
        self.fit_to_view()
        
    def add_item(self, item):
        """Ajoute un élément à la scène"""
        self.scene.addItem(item)
        
    def remove_item(self, item):
        """Supprime un élément de la scène"""
        self.scene.removeItem(item)
        
    def clear(self):
        """Vide la scène"""
        self.scene.clear()
        
    def get_items(self):
        """Retourne tous les éléments de la scène"""
        return self.scene.items()
        
    def get_selected_items(self):
        """Retourne les éléments sélectionnés"""
        return [item for item in self.scene.selectedItems()]
        
    def set_grid_visible(self, visible: bool):
        """Affiche ou cache la grille"""
        self.show_grid = visible
        self.viewport().update()
        
    def set_grid_size(self, size: float):
        """Définit la taille de la grille"""
        self.grid_size = size
        self.viewport().update() 