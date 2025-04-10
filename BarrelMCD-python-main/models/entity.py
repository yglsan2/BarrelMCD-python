from PyQt5.QtWidgets import QGraphicsItem, QGraphicsRectItem, QGraphicsTextItem
from PyQt5.QtCore import Qt, QRectF, QPointF
from PyQt5.QtGui import QPainter, QPainterPath, QColor, QPen, QBrush, QFont
import uuid

class Entity(QGraphicsItem):
    """Représente une entité dans le diagramme MCD"""
    
    def __init__(self, x: float, y: float, name: str = ""):
        super().__init__()
        self.id = str(uuid.uuid4())
        self.name = name
        self.attributes = []
        self.setPos(x, y)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)
        
        # Style par défaut
        self.style = {
            "background": QColor(240, 240, 240),
            "border": QColor(0, 0, 0),
            "text": QColor(0, 0, 0),
            'background_color': QColor("#FFFFFF"),
            'border_color': QColor("#2C3E50"),
            'text_color': QColor("#2C3E50"),
            'font': QFont("Arial", 10),
            'border_width': 2,
            'corner_radius': 5
        }
        
        # Création des éléments graphiques
        self.rect = QGraphicsRectItem(self)
        self.title = QGraphicsTextItem(self)
        self.title.setPlainText(name)
        self.title.setDefaultTextColor(self.style['text_color'])
        self.title.setFont(self.style['font'])
        
        # Mise à jour de la taille
        self.update_size()
        
    def set_style(self, style):
        self.style.update(style)
        self.title.setDefaultTextColor(self.style['text_color'])
        self.title.setFont(self.style['font'])
        self.update()
        
    def update_size(self):
        # Calcul de la taille en fonction du contenu
        title_width = self.title.boundingRect().width()
        title_height = self.title.boundingRect().height()
        
        # Espace pour les attributs
        attr_height = len(self.attributes) * 20 if self.attributes else 0
        
        # Taille totale
        width = max(title_width + 40, 150)  # Largeur minimale de 150
        height = title_height + attr_height + 20
        
        # Mise à jour du rectangle
        self.rect.setRect(0, 0, width, height)
        
        # Position du titre
        self.title.setPos(10, 5)
        
        # Mise à jour des attributs
        self.update_attributes()
        
    def update_attributes(self):
        # Suppression des anciens attributs
        for attr in self.attributes:
            if hasattr(attr, 'text_item'):
                self.scene().removeItem(attr['text_item'])
        
        # Création des nouveaux attributs
        y = self.title.boundingRect().height() + 10
        for attr in self.attributes:
            text_item = QGraphicsTextItem(self)
            text_item.setPlainText(f"{attr['name']}: {attr['type']}")
            text_item.setDefaultTextColor(self.style['text_color'])
            text_item.setFont(self.style['font'])
            text_item.setPos(10, y)
            attr['text_item'] = text_item
            y += 20
            
    def add_attribute(self, name, type="VARCHAR(255)"):
        self.attributes.append({
            'name': name,
            'type': type,
            'constraints': []
        })
        self.update_size()
        
    def boundingRect(self):
        return self.rect.rect()
        
    def paint(self, painter, option, widget):
        # Configuration du peintre
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Création du chemin avec coins arrondis
        path = QPainterPath()
        rect = self.rect.rect()
        radius = self.style['corner_radius']
        
        path.moveTo(rect.left() + radius, rect.top())
        path.lineTo(rect.right() - radius, rect.top())
        path.quadTo(rect.right(), rect.top(),
                   rect.right(), rect.top() + radius)
        path.lineTo(rect.right(), rect.bottom() - radius)
        path.quadTo(rect.right(), rect.bottom(),
                   rect.right() - radius, rect.bottom())
        path.lineTo(rect.left() + radius, rect.bottom())
        path.quadTo(rect.left(), rect.bottom(),
                   rect.left(), rect.bottom() - radius)
        path.lineTo(rect.left(), rect.top() + radius)
        path.quadTo(rect.left(), rect.top(),
                   rect.left() + radius, rect.top())
        
        # Dessin du fond
        painter.setBrush(QBrush(self.style['background_color']))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawPath(path)
        
        # Dessin de la bordure
        pen = QPen(self.style['border_color'])
        pen.setWidth(self.style['border_width'])
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(path)
        
        # Dessin de la ligne de séparation
        if self.attributes:
            y = self.title.boundingRect().height() + 5
            painter.drawLine(rect.left() + 5, y, rect.right() - 5, y)
            
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.setSelected(True)
        super().mousePressEvent(event)
        
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.setSelected(False)
        super().mouseReleaseEvent(event)
