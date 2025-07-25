from PyQt6.QtWidgets import QGraphicsItem, QGraphicsTextItem
from PyQt6.QtCore import Qt, QRectF, QPointF, QLineF, QPropertyAnimation, QEasingCurve, QSizeF
from PyQt6.QtGui import QPainter, QPen, QColor, QPainterPath, QPainterPathStroker, QFont, QPainterPathElement

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
        
    def boundingRect(self) -> QRectF:
        """Retourne la zone englobante de la flèche"""
        if not self.source or not self.target:
            return QRectF()
            
        # Calculer les points de contrôle
        self._update_control_points()
        
        # Créer un chemin pour la flèche
        path = self._get_arrow_path()
        
        # Ajouter une marge pour l'effet de survol et les points de contrôle
        margin = 15 if self.is_hovered or self.style["show_control_points"] else 5
        rect = path.boundingRect().adjusted(-margin, -margin, margin, margin)
        
        # Inclure les labels de cardinalité
        if self.style["cardinality"]["show"]:
            rect = rect.united(self.source_label.boundingRect())
            rect = rect.united(self.target_label.boundingRect())
            
        return rect
        
    def paint(self, painter: QPainter, option, widget) -> None:
        """Dessine la flèche avec effets visuels"""
        if not self.source or not self.target:
            return
            
        # Mettre à jour les points de contrôle
        self._update_control_points()
        
        # Configurer le peintre
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Effet de survol
        if self.is_hovered:
            # Ombre portée
            shadow = QPainterPathStroker()
            shadow.setWidth(4)
            shadow.setColor(QColor(0, 0, 0, 30))
            painter.drawPath(shadow.createStroke(self._get_arrow_path()))
            
            # Ligne plus épaisse
            painter.setPen(QPen(self.style["color"], self.style["width"] + 2))
        else:
            painter.setPen(QPen(self.style["color"], self.style["width"]))
            
        painter.setBrush(Qt.BrushStyle.NoBrush)
        
        # Dessiner la flèche selon le style
        if self.style["line_style"] == "orthogonal":
            self._draw_orthogonal_arrow(painter)
        elif self.style["line_style"] == "straight":
            self._draw_straight_arrow(painter)
        else:
            self._draw_bezier_arrow(painter)
            
        # Dessiner les points de contrôle
        if self.style["show_control_points"]:
            self._draw_control_points(painter)
            
    def _draw_bezier_arrow(self, painter: QPainter) -> None:
        """Dessine une flèche avec courbe de Bézier"""
        path = self._get_arrow_path()
        painter.drawPath(path)
        
    def _draw_orthogonal_arrow(self, painter: QPainter) -> None:
        """Dessine une flèche orthogonale"""
        path = QPainterPath()
        path.moveTo(self.source_anchor)
        
        # Calculer les points intermédiaires
        mid_x = (self.source_anchor.x() + self.target_anchor.x()) / 2
        path.lineTo(mid_x, self.source_anchor.y())
        path.lineTo(mid_x, self.target_anchor.y())
        path.lineTo(self.target_anchor)
        
        # Dessiner le chemin
        painter.drawPath(path)
        
        # Dessiner la pointe de la flèche
        arrow_points = self._calculate_arrow_points(self.target_anchor, QPointF(mid_x, self.target_anchor.y()))
        painter.drawLine(self.target_anchor, arrow_points[0])
        painter.drawLine(self.target_anchor, arrow_points[1])
        
    def _draw_straight_arrow(self, painter: QPainter) -> None:
        """Dessine une flèche droite"""
        painter.drawLine(self.source_anchor, self.target_anchor)
        
        # Dessiner la pointe de la flèche
        arrow_points = self._calculate_arrow_points(self.target_anchor, self.source_anchor)
        painter.drawLine(self.target_anchor, arrow_points[0])
        painter.drawLine(self.target_anchor, arrow_points[1])
        
    def _draw_control_points(self, painter: QPainter) -> None:
        """Dessine les points de contrôle"""
        painter.setPen(QPen(Qt.GlobalColor.blue, 1))
        painter.setBrush(QBrush(Qt.GlobalColor.white))
        
        # Points de contrôle principaux
        for point in [self.control1, self.control2]:
            painter.drawEllipse(point, 4, 4)
            
        # Points de contrôle supplémentaires
        for point in self.control_points:
            painter.setPen(QPen(Qt.GlobalColor.green, 1))
            painter.drawEllipse(point, 3, 3)
            
    def _update_control_points(self) -> None:
        """Met à jour les points de contrôle et d'ancrage"""
        if not self.source or not self.target:
            return
            
        # Obtenir les positions des éléments
        source_pos = self.source.scenePos()
        target_pos = self.target.scenePos()
        
        # Calculer les points d'ancrage magnétiques
        self.source_anchor = self._find_anchor_point(source_pos, target_pos, self.source)
        self.target_anchor = self._find_anchor_point(target_pos, source_pos, self.target)
        
        # Calculer les points de contrôle
        dx = self.target_anchor.x() - self.source_anchor.x()
        dy = self.target_anchor.y() - self.source_anchor.y()
        
        # Ajuster la tension de la courbe
        tension = self.style["curve_tension"]
        
        self.control1 = QPointF(
            self.source_anchor.x() + dx * 0.25 * tension,
            self.source_anchor.y() + dy * 0.25 * tension
        )
        self.control2 = QPointF(
            self.source_anchor.x() + dx * 0.75 * tension,
            self.source_anchor.y() + dy * 0.75 * tension
        )
        
        # Mettre à jour les labels de cardinalité
        self._update_labels()
        
    def _update_labels(self) -> None:
        """Met à jour les labels de cardinalité"""
        if not self.style["cardinality"]["show"]:
            self.source_label.setVisible(False)
            self.target_label.setVisible(False)
            return
            
        # Configurer les labels
        font = QFont("Arial", 8)
        self.source_label.setFont(font)
        self.target_label.setFont(font)
        self.source_label.setPlainText(self.style["cardinality"]["source"])
        self.target_label.setPlainText(self.style["cardinality"]["target"])
        
        # Positionner les labels
        mid_point = QPointF(
            (self.source_anchor.x() + self.target_anchor.x()) / 2,
            (self.source_anchor.y() + self.target_anchor.y()) / 2
        )
        
        # Source label
        source_pos = QPointF(
            self.source_anchor.x() + (mid_point.x() - self.source_anchor.x()) * 0.25,
            self.source_anchor.y() + (mid_point.y() - self.source_anchor.y()) * 0.25
        )
        self.source_label.setPos(source_pos)
        
        # Target label
        target_pos = QPointF(
            self.target_anchor.x() + (mid_point.x() - self.target_anchor.x()) * 0.25,
            self.target_anchor.y() + (mid_point.y() - self.target_anchor.y()) * 0.25
        )
        self.target_label.setPos(target_pos)
        
        self.source_label.setVisible(True)
        self.target_label.setVisible(True)
        
    def mousePressEvent(self, event) -> None:
        """Gère le clic sur la flèche"""
        if event.button() == Qt.MouseButton.LeftButton:
            if self.style["show_control_points"]:
                # Vérifier si un point de contrôle est cliqué
                pos = event.pos()
                for i, point in enumerate([self.control1, self.control2] + self.control_points):
                    if (pos - point).manhattanLength() < 5:
                        self.selected_control = i
                        self.drag_point = pos
                        self.setCursor(Qt.CursorShape.ClosedHandCursor)
                        return
                        
            self.is_dragging = True
            self.drag_point = event.pos()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            
    def mouseReleaseEvent(self, event) -> None:
        """Gère le relâchement du clic"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_dragging = False
            self.selected_control = None
            self.drag_point = None
            self.setCursor(Qt.CursorShape.ArrowCursor)
            
    def mouseMoveEvent(self, event) -> None:
        """Gère le déplacement de la souris"""
        if self.is_dragging and self.drag_point:
            if self.selected_control is not None:
                # Déplacer le point de contrôle
                delta = event.pos() - self.drag_point
                if self.selected_control == 0:
                    self.control1 += delta
                elif self.selected_control == 1:
                    self.control2 += delta
                else:
                    self.control_points[self.selected_control - 2] += delta
            else:
                # Ajuster la tension de la courbe
                delta = event.pos() - self.drag_point
                self.style["curve_tension"] = max(0.1, min(0.9,
                    self.style["curve_tension"] + delta.x() * 0.001
                ))
                
            self.drag_point = event.pos()
            self.update()
            
    def contextMenuEvent(self, event) -> None:
        """Gère le menu contextuel"""
        menu = QMenu()
        
        # Style de ligne
        line_style_menu = menu.addMenu("Style de ligne")
        for style in ["bezier", "orthogonal", "straight"]:
            action = line_style_menu.addAction(style.capitalize())
            action.setCheckable(True)
            action.setChecked(self.style["line_style"] == style)
            action.triggered.connect(lambda checked, s=style: self.set_line_style(s))
            
        # Cardinalité
        cardinality_menu = menu.addMenu("Cardinalité")
        for end in ["source", "target"]:
            submenu = cardinality_menu.addMenu(f"{end.capitalize()} ({self.style['cardinality'][end]})")
            for value in ["0", "1", "N", "0,1", "1,N", "0,N"]:
                action = submenu.addAction(value)
                action.triggered.connect(lambda checked, e=end, v=value: self.set_cardinality(e, v))
                
        # Points de contrôle
        control_action = menu.addAction("Afficher les points de contrôle")
        control_action.setCheckable(True)
        control_action.setChecked(self.style["show_control_points"])
        control_action.triggered.connect(lambda checked: self.set_show_control_points(checked))
        
        menu.exec(event.screenPos())
        
    def set_line_style(self, style: str) -> None:
        """Définit le style de ligne"""
        self.style["line_style"] = style
        self.update()
        
    def set_cardinality(self, end: str, value: str) -> None:
        """Définit la cardinalité d'une extrémité"""
        self.style["cardinality"][end] = value
        self._update_labels()
        self.update()
        
    def set_show_control_points(self, show: bool) -> None:
        """Affiche ou cache les points de contrôle"""
        self.style["show_control_points"] = show
        self.update()
        
    def to_dict(self) -> dict:
        """Convertit la flèche en dictionnaire pour la sauvegarde"""
        return {
            "source_id": self.source.id if hasattr(self.source, "id") else None,
            "target_id": self.target.id if hasattr(self.target, "id") else None,
            "style": {
                "color": self.style["color"].name(),
                "width": self.style["width"],
                "arrow_size": self.style["arrow_size"],
                "magnet_strength": self.style["magnet_strength"],
                "curve_tension": self.style["curve_tension"],
                "hover_effect": self.style["hover_effect"],
                "show_control_points": self.style["show_control_points"],
                "line_style": self.style["line_style"],
                "cardinality": self.style["cardinality"]
            },
            "control_points": [
                {"x": p.x(), "y": p.y()} for p in self.control_points
            ]
        }
        
    @classmethod
    def from_dict(cls, data: dict, source: QGraphicsItem, target: QGraphicsItem) -> 'MagneticArrow':
        """Crée une flèche à partir d'un dictionnaire"""
        arrow = cls(source, target)
        
        # Restaurer le style
        arrow.style = {
            "color": QColor(data["style"]["color"]),
            "width": data["style"]["width"],
            "arrow_size": data["style"]["arrow_size"],
            "magnet_strength": data["style"]["magnet_strength"],
            "curve_tension": data["style"]["curve_tension"],
            "hover_effect": data["style"]["hover_effect"],
            "show_control_points": data["style"]["show_control_points"],
            "line_style": data["style"]["line_style"],
            "cardinality": data["style"]["cardinality"]
        }
        
        # Restaurer les points de contrôle
        arrow.control_points = [
            QPointF(p["x"], p["y"]) for p in data.get("control_points", [])
        ]
        
        return arrow 