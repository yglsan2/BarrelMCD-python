from PyQt6.QtWidgets import QGraphicsItem
from PyQt6.QtCore import Qt, QRectF, QPointF, QLineF
from PyQt6.QtGui import QPainter, QPen, QColor, QPainterPath

class FlexibleArrow(QGraphicsItem):
    """Représente une flèche flexible entre deux éléments"""
    
    def __init__(self, source: QGraphicsItem, target: QGraphicsItem):
        super().__init__()
        self.source = source
        self.target = target
        self.setZValue(-1)  # Placer la flèche sous les autres éléments
        
        # Style par défaut
        self.style = {
            "color": QColor(0, 0, 0),
            "width": 2,
            "arrow_size": 10
        }
        
    def boundingRect(self) -> QRectF:
        """Retourne la zone englobante de la flèche"""
        if not self.source or not self.target:
            return QRectF()
            
        source_pos = self.source.scenePos()
        target_pos = self.target.scenePos()
        
        # Calculer les points de contrôle
        control_points = self._calculate_control_points(source_pos, target_pos)
        
        # Créer un chemin pour la flèche
        path = QPainterPath()
        path.moveTo(control_points[0])
        
        # Courbe de Bézier
        path.cubicTo(
            control_points[1],
            control_points[2],
            control_points[3]
        )
        
        # Ajouter la pointe de la flèche
        arrow_points = self._calculate_arrow_points(control_points[3], control_points[2])
        path.lineTo(arrow_points[0])
        path.moveTo(control_points[3])
        path.lineTo(arrow_points[1])
        
        return path.boundingRect().adjusted(-5, -5, 5, 5)
        
    def paint(self, painter: QPainter, option, widget) -> None:
        """Dessine la flèche"""
        if not self.source or not self.target:
            return
            
        source_pos = self.source.scenePos()
        target_pos = self.target.scenePos()
        
        # Calculer les points de contrôle
        control_points = self._calculate_control_points(source_pos, target_pos)
        
        # Configurer le peintre
        painter.setPen(QPen(self.style["color"], self.style["width"]))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        
        # Dessiner la courbe
        path = QPainterPath()
        path.moveTo(control_points[0])
        path.cubicTo(
            control_points[1],
            control_points[2],
            control_points[3]
        )
        painter.drawPath(path)
        
        # Dessiner la pointe de la flèche
        arrow_points = self._calculate_arrow_points(control_points[3], control_points[2])
        painter.drawLine(control_points[3], arrow_points[0])
        painter.drawLine(control_points[3], arrow_points[1])
        
    def _calculate_control_points(self, source_pos: QPointF, target_pos: QPointF) -> list:
        """Calcule les points de contrôle pour la courbe de Bézier"""
        # Point de départ
        start = QPointF(source_pos.x(), source_pos.y())
        
        # Point d'arrivée
        end = QPointF(target_pos.x(), target_pos.y())
        
        # Points de contrôle
        dx = end.x() - start.x()
        dy = end.y() - start.y()
        
        control1 = QPointF(start.x() + dx * 0.25, start.y() + dy * 0.25)
        control2 = QPointF(start.x() + dx * 0.75, start.y() + dy * 0.75)
        
        return [start, control1, control2, end]
        
    def _calculate_arrow_points(self, end: QPointF, control: QPointF) -> list:
        """Calcule les points pour la pointe de la flèche"""
        # Vecteur de direction
        direction = QPointF(end.x() - control.x(), end.y() - control.y())
        length = (direction.x() ** 2 + direction.y() ** 2) ** 0.5
        
        if length == 0:
            return [end, end]
            
        # Normaliser le vecteur
        direction = QPointF(direction.x() / length, direction.y() / length)
        
        # Vecteur perpendiculaire
        perpendicular = QPointF(-direction.y(), direction.x())
        
        # Points de la flèche
        arrow_size = self.style["arrow_size"]
        point1 = QPointF(
            end.x() - direction.x() * arrow_size + perpendicular.x() * arrow_size/2,
            end.y() - direction.y() * arrow_size + perpendicular.y() * arrow_size/2
        )
        point2 = QPointF(
            end.x() - direction.x() * arrow_size - perpendicular.x() * arrow_size/2,
            end.y() - direction.y() * arrow_size - perpendicular.y() * arrow_size/2
        )
        
        return [point1, point2]
        
    def setStyle(self, style: dict) -> None:
        """Définit le style de la flèche"""
        self.style = style
        self.update()
        
    def to_dict(self) -> dict:
        """Convertit la flèche en dictionnaire pour la sauvegarde"""
        return {
            "source_id": self.source.id if hasattr(self.source, "id") else None,
            "target_id": self.target.id if hasattr(self.target, "id") else None,
            "style": {
                "color": self.style["color"].name(),
                "width": self.style["width"],
                "arrow_size": self.style["arrow_size"]
            }
        }
        
    @classmethod
    def from_dict(cls, data: dict, source: QGraphicsItem, target: QGraphicsItem) -> 'FlexibleArrow':
        """Crée une flèche à partir d'un dictionnaire"""
        arrow = cls(source, target)
        
        # Restaurer le style
        arrow.style = {
            "color": QColor(data["style"]["color"]),
            "width": data["style"]["width"],
            "arrow_size": data["style"]["arrow_size"]
        }
        
        return arrow 