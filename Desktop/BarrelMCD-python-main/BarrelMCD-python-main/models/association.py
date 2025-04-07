from PyQt6.QtWidgets import QGraphicsItem, QGraphicsRectItem, QGraphicsTextItem
from PyQt6.QtCore import Qt, QRectF, QPointF, QLineF
from PyQt6.QtGui import QPainter, QPainterPath, QColor, QPen, QBrush, QFont
import uuid

class Association(QGraphicsItem):
    """Représente une association dans le diagramme MCD"""
    
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
            "background": QColor(200, 200, 200),
            "border": QColor(0, 0, 0),
            "text": QColor(0, 0, 0),
            "font": QFont("Arial", 10)
        }
        
        # Création des éléments graphiques
        self.rect = QGraphicsRectItem(self)
        self.title = QGraphicsTextItem(self)
        self.title.setPlainText(name)
        self.title.setDefaultTextColor(self.style['text'])
        self.title.setFont(self.style['font'])
        
        # Mise à jour de la taille
        self.update_size()
        
    def boundingRect(self) -> QRectF:
        """Retourne la zone englobante de l'association"""
        return QRectF(-50, -30, 100, 60)
        
    def paint(self, painter: QPainter, option, widget) -> None:
        """Dessine l'association"""
        # Dessiner le losange
        painter.setPen(QPen(self.style["border"]))
        painter.setBrush(QBrush(self.style["background"]))
        
        rect = self.boundingRect()
        center = rect.center()
        width = rect.width()
        height = rect.height()
        
        path = QPainterPath()
        path.moveTo(center.x(), center.y() - height/2)
        path.lineTo(center.x() + width/2, center.y())
        path.lineTo(center.x(), center.y() + height/2)
        path.lineTo(center.x() - width/2, center.y())
        path.closeSubpath()
        
        painter.drawPath(path)
        
        # Dessiner le nom
        painter.setPen(self.style["text"])
        painter.setFont(self.style["font"])
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, self.name)
        
    def setName(self, name: str) -> None:
        """Définit le nom de l'association"""
        self.name = name
        self.update()
        
    def setStyle(self, style: dict) -> None:
        """Définit le style de l'association"""
        self.style = style
        self.update()
        
    def addAttribute(self, name: str, type: str) -> None:
        """Ajoute un attribut à l'association"""
        self.attributes.append({
            "name": name,
            "type": type
        })
        self.update()
        
    def removeAttribute(self, name: str) -> None:
        """Supprime un attribut de l'association"""
        self.attributes = [attr for attr in self.attributes if attr["name"] != name]
        self.update()
        
    def to_dict(self) -> dict:
        """Convertit l'association en dictionnaire pour la sauvegarde"""
        return {
            "id": self.id,
            "name": self.name,
            "pos": {
                "x": self.pos().x(),
                "y": self.pos().y()
            },
            "attributes": self.attributes,
            "style": {
                "background": self.style["background"].name(),
                "border": self.style["border"].name(),
                "text": self.style["text"].name(),
                "font": {
                    "family": self.style["font"].family(),
                    "size": self.style["font"].pointSize()
                }
            }
        }
        
    @classmethod
    def from_dict(cls, data: dict) -> 'Association':
        """Crée une association à partir d'un dictionnaire"""
        association = cls(data["pos"]["x"], data["pos"]["y"], data["name"])
        association.id = data["id"]
        association.attributes = data["attributes"]
        
        # Restaurer le style
        association.style = {
            "background": QColor(data["style"]["background"]),
            "border": QColor(data["style"]["border"]),
            "text": QColor(data["style"]["text"]),
            "font": QFont(
                data["style"]["font"]["family"],
                data["style"]["font"]["size"]
            )
        }
        
        return association
        
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
            text_item.setDefaultTextColor(self.style['text'])
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
        
    def paint(self, painter, option, widget):
        # Configuration du peintre
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Création du chemin avec coins arrondis
        path = QPainterPath()
        rect = self.rect.rect()
        radius = 3
        
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
        painter.setBrush(QBrush(self.style['background']))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawPath(path)
        
        # Dessin de la bordure
        pen = QPen(self.style['border'])
        pen.setWidth(1)
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

class FlexibleArrow(QGraphicsItem):
    def __init__(self, start_item, end_item):
        super().__init__()
        self.start_item = start_item
        self.end_item = end_item
        self.style = {
            'color': QColor("#2C3E50"),
            'width': 2,
            'arrow_size': 10
        }
        
        # Cardinalités
        self.start_cardinality = "1"
        self.end_cardinality = "1"
        
        # Style de la flèche
        self.is_inheritance = False
        
        # Mise à jour de la position
        self.update_position()
        
    def set_style(self, style):
        self.style.update(style)
        self.update()
        
    def set_inheritance_style(self):
        self.is_inheritance = True
        self.style['arrow_size'] = 15
        self.update()
        
    def update_position(self):
        # Calcul des points de connexion
        start_rect = self.start_item.sceneBoundingRect()
        end_rect = self.end_item.sceneBoundingRect()
        
        # Point de départ
        start_center = start_rect.center()
        end_center = end_rect.center()
        
        # Calcul de l'intersection avec les rectangles
        line = QLineF(start_center, end_center)
        start_point = self.intersect_rect(start_rect, line)
        end_point = self.intersect_rect(end_rect, line)
        
        # Mise à jour de la position
        self.setPos(0, 0)
        self.prepareGeometryChange()
        self.start_point = start_point
        self.end_point = end_point
        
    def intersect_rect(self, rect, line):
        # Calcul de l'intersection entre une ligne et un rectangle
        # Retourne le point d'intersection le plus proche
        points = []
        
        # Intersection avec les côtés du rectangle
        for i in range(4):
            p1 = rect.topLeft() if i == 0 else rect.topRight() if i == 1 else rect.bottomRight() if i == 2 else rect.bottomLeft()
            p2 = rect.topRight() if i == 0 else rect.bottomRight() if i == 1 else rect.bottomLeft() if i == 2 else rect.topLeft()
            
            side = QLineF(p1, p2)
            intersection = QPointF()
            if line.intersect(side, intersection) == QLineF.IntersectType.BoundedIntersection:
                points.append(intersection)
        
        # Retourner le point le plus proche du centre de la ligne
        if points:
            line_center = line.center()
            return min(points, key=lambda p: (p - line_center).manhattanLength())
        return line.p1()
        
    def boundingRect(self):
        if not hasattr(self, 'start_point') or not hasattr(self, 'end_point'):
            return QRectF()
            
        # Rectangle englobant avec marge pour la flèche
        rect = QRectF(self.start_point, self.end_point).normalized()
        margin = self.style['arrow_size']
        rect.adjust(-margin, -margin, margin, margin)
        return rect
        
    def paint(self, painter, option, widget):
        if not hasattr(self, 'start_point') or not hasattr(self, 'end_point'):
            return
            
        # Configuration du peintre
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Style de la ligne
        pen = QPen(self.style['color'])
        pen.setWidth(self.style['width'])
        if self.is_inheritance:
            pen.setStyle(Qt.PenStyle.DashLine)
        painter.setPen(pen)
        
        # Dessin de la ligne
        painter.drawLine(self.start_point, self.end_point)
        
        # Dessin de la flèche
        self.draw_arrow(painter, self.end_point, self.start_point)
        
        # Dessin des cardinalités
        self.draw_cardinalities(painter)
        
    def draw_arrow(self, painter, end_point, start_point):
        # Calcul des points de la flèche
        angle = QLineF(end_point, start_point).angle()
        arrow_size = self.style['arrow_size']
        
        # Points de la flèche
        p1 = end_point + QPointF(
            arrow_size * 0.5 * (angle + 30),
            arrow_size * 0.5 * (angle - 30)
        )
        p2 = end_point + QPointF(
            arrow_size * 0.5 * (angle - 30),
            arrow_size * 0.5 * (angle + 30)
        )
        
        # Dessin de la flèche
        path = QPainterPath()
        path.moveTo(end_point)
        path.lineTo(p1)
        path.lineTo(p2)
        path.closeSubpath()
        
        painter.setBrush(QBrush(self.style['color']))
        painter.drawPath(path)
        
    def draw_cardinalities(self, painter):
        # Configuration du texte
        font = QFont("Arial", 8)
        painter.setFont(font)
        painter.setPen(self.style['color'])
        
        # Position des cardinalités
        start_text = self.start_cardinality
        end_text = self.end_cardinality
        
        # Calcul des positions
        line_center = QLineF(self.start_point, self.end_point).center()
        normal = QLineF(self.start_point, self.end_point).normalVector().unitVector()
        offset = 15
        
        # Dessin des cardinalités
        start_pos = line_center + normal * offset
        end_pos = line_center - normal * offset
        
        painter.drawText(start_pos, start_text)
        painter.drawText(end_pos, end_text)
        
    def cycle_start_cardinality(self):
        cardinalities = ["0", "1", "n", "0,1", "1,n", "0,n"]
        current_index = cardinalities.index(self.start_cardinality)
        self.start_cardinality = cardinalities[(current_index + 1) % len(cardinalities)]
        self.update()
        
    def cycle_end_cardinality(self):
        cardinalities = ["0", "1", "n", "0,1", "1,n", "0,n"]
        current_index = cardinalities.index(self.end_cardinality)
        self.end_cardinality = cardinalities[(current_index + 1) % len(cardinalities)]
        self.update()
        
    def update_cardinality_display(self):
        self.update()
