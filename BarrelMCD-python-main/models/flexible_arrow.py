from PyQt5.QtWidgets import QGraphicsItem
from PyQt5.QtCore import Qt, QRectF, QPointF, QLineF
from PyQt5.QtGui import QPainter, QPen, QColor, QPainterPath, QPainterPathStroker, QFont
import os

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
            "arrow_size": 10,
            "curve_tension": 0.5,  # Tension de la courbe (0-1)
            "hover_effect": True,  # Effet au survol
            "smoothness": 0.3,     # Lissage de la courbe (0-1)
            "shadow": True,        # Ombre portée
            "shadow_color": QColor(0, 0, 0, 30),
            "shadow_width": 4,
            "cardinality": {
                "source": "1,1",
                "target": "1,1",
                "show": True,
                "font": QFont("Arial", 8),
                "color": QColor(0, 0, 0),
                "offset": 15  # Distance du texte par rapport à la ligne
            }
        }
        
        # État
        self.is_hovered = False
        self.is_reversed = False  # Indique si la flèche est inversée
        
        # Liste des cardinalités disponibles (4 cardinalités principales)
        self.available_cardinalities = ["0,1", "1,1", "0,n", "1,n"]
        
        # Règles de conversion MCD vers MLD
        self.mld_rules = {
            "0,1": {
                "table_type": "principale",
                "primary_key": True,
                "foreign_key": {
                    "required": False,
                    "unique": False
                }
            },
            "1,1": {
                "table_type": "principale",
                "primary_key": True,
                "foreign_key": {
                    "required": True,
                    "unique": True
                }
            },
            "0,n": {
                "table_type": "intermediaire",
                "primary_key": "composite",
                "foreign_keys": {
                    "source": {"required": True},
                    "target": {"required": True}
                }
            },
            "1,n": {
                "table_type": "intermediaire",
                "primary_key": "composite",
                "foreign_keys": {
                    "source": {"required": True},
                    "target": {"required": True}
                }
            }
        }
        
    def generate_cardinality_visual(self, output_path: str = None) -> str:
        """Génère un visuel SVG des cardinalités MCD et leur conversion en MLD"""
        if output_path is None:
            output_path = os.path.join(os.path.dirname(__file__), "cardinality_visual.svg")
            
        # Créer le contenu SVG
        svg_content = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 600">
  <style>
    .title {{ font-family: Arial; font-size: 24px; font-weight: bold; }}
    .subtitle {{ font-family: Arial; font-size: 18px; }}
    .text {{ font-family: Arial; font-size: 14px; }}
    .mcd {{ fill: #2e3367; }}
    .mld {{ fill: #66b32e; }}
    .arrow {{ stroke: #000; stroke-width: 2; fill: none; }}
    .table {{ fill: #f0f0f0; stroke: #000; stroke-width: 1; }}
    .primary-key {{ fill: #f6a316; }}
    .foreign-key {{ fill: #2b73b9; }}
    .cardinality {{ font-family: Arial; font-size: 12px; }}
  </style>
  
  <!-- Titre -->
  <text x="400" y="40" text-anchor="middle" class="title">Cardinalités MCD et leur conversion en MLD</text>
  
  <!-- Légende -->
  <rect x="50" y="60" width="20" height="20" class="mcd" />
  <text x="80" y="75" class="text">Modèle Conceptuel de Données (MCD)</text>
  
  <rect x="50" y="90" width="20" height="20" class="mld" />
  <text x="80" y="105" class="text">Modèle Logique de Données (MLD)</text>
  
  <!-- Cardinalité 0,1 -->
  <g transform="translate(0, 150)">
    <text x="400" y="0" text-anchor="middle" class="subtitle">Cardinalité 0,1</text>
    
    <!-- MCD -->
    <rect x="100" y="30" width="120" height="80" rx="5" class="mcd" />
    <text x="160" y="60" text-anchor="middle" class="text" fill="white">Entité A</text>
    
    <rect x="580" y="30" width="120" height="80" rx="5" class="mcd" />
    <text x="640" y="60" text-anchor="middle" class="text" fill="white">Entité B</text>
    
    <path d="M 220 70 L 580 70" class="arrow" />
    <polygon points="570 65, 580 70, 570 75" fill="black" />
    
    <text x="400" y="50" text-anchor="middle" class="cardinality">0,1</text>
    
    <!-- MLD -->
    <rect x="100" y="150" width="120" height="80" rx="5" class="mld" />
    <text x="160" y="180" text-anchor="middle" class="text">Table A</text>
    <rect x="110" y="190" width="100" height="20" class="primary-key" />
    <text x="160" y="205" text-anchor="middle" class="text">id (PK)</text>
    
    <rect x="580" y="150" width="120" height="80" rx="5" class="mld" />
    <text x="640" y="180" text-anchor="middle" class="text">Table B</text>
    <rect x="590" y="190" width="100" height="20" class="primary-key" />
    <text x="640" y="205" text-anchor="middle" class="text">id (PK)</text>
    
    <rect x="110" y="220" width="100" height="20" class="foreign-key" />
    <text x="160" y="235" text-anchor="middle" class="text">b_id (FK)</text>
    
    <path d="M 160 260 L 640 260" class="arrow" stroke-dasharray="5,5" />
    <text x="400" y="280" text-anchor="middle" class="text">Clé étrangère nullable dans la table A</text>
  </g>
  
  <!-- Cardinalité 1,1 -->
  <g transform="translate(0, 300)">
    <text x="400" y="0" text-anchor="middle" class="subtitle">Cardinalité 1,1</text>
    
    <!-- MCD -->
    <rect x="100" y="30" width="120" height="80" rx="5" class="mcd" />
    <text x="160" y="60" text-anchor="middle" class="text" fill="white">Entité A</text>
    
    <rect x="580" y="30" width="120" height="80" rx="5" class="mcd" />
    <text x="640" y="60" text-anchor="middle" class="text" fill="white">Entité B</text>
    
    <path d="M 220 70 L 580 70" class="arrow" />
    <polygon points="570 65, 580 70, 570 75" fill="black" />
    
    <text x="400" y="50" text-anchor="middle" class="cardinality">1,1</text>
    
    <!-- MLD -->
    <rect x="100" y="150" width="120" height="80" rx="5" class="mld" />
    <text x="160" y="180" text-anchor="middle" class="text">Table A</text>
    <rect x="110" y="190" width="100" height="20" class="primary-key" />
    <text x="160" y="205" text-anchor="middle" class="text">id (PK)</text>
    
    <rect x="580" y="150" width="120" height="80" rx="5" class="mld" />
    <text x="640" y="180" text-anchor="middle" class="text">Table B</text>
    <rect x="590" y="190" width="100" height="20" class="primary-key" />
    <text x="640" y="205" text-anchor="middle" class="text">id (PK)</text>
    
    <rect x="110" y="220" width="100" height="20" class="foreign-key" />
    <text x="160" y="235" text-anchor="middle" class="text">b_id (FK)</text>
    
    <path d="M 160 260 L 640 260" class="arrow" stroke-dasharray="5,5" />
    <text x="400" y="280" text-anchor="middle" class="text">Clé étrangère non-nullable et unique dans la table A</text>
  </g>
  
  <!-- Cardinalité 0,n -->
  <g transform="translate(0, 450)">
    <text x="400" y="0" text-anchor="middle" class="subtitle">Cardinalité 0,n</text>
    
    <!-- MCD -->
    <rect x="100" y="30" width="120" height="80" rx="5" class="mcd" />
    <text x="160" y="60" text-anchor="middle" class="text" fill="white">Entité A</text>
    
    <rect x="580" y="30" width="120" height="80" rx="5" class="mcd" />
    <text x="640" y="60" text-anchor="middle" class="text" fill="white">Entité B</text>
    
    <path d="M 220 70 L 580 70" class="arrow" />
    <polygon points="570 65, 580 70, 570 75" fill="black" />
    
    <text x="400" y="50" text-anchor="middle" class="cardinality">0,n</text>
    
    <!-- MLD -->
    <rect x="100" y="150" width="120" height="80" rx="5" class="mld" />
    <text x="160" y="180" text-anchor="middle" class="text">Table A</text>
    <rect x="110" y="190" width="100" height="20" class="primary-key" />
    <text x="160" y="205" text-anchor="middle" class="text">id (PK)</text>
    
    <rect x="580" y="150" width="120" height="80" rx="5" class="mld" />
    <text x="640" y="180" text-anchor="middle" class="text">Table B</text>
    <rect x="590" y="190" width="100" height="20" class="primary-key" />
    <text x="640" y="205" text-anchor="middle" class="text">id (PK)</text>
    
    <rect x="300" y="150" width="200" height="80" rx="5" class="mld" />
    <text x="400" y="180" text-anchor="middle" class="text">Table A_B</text>
    <rect x="310" y="190" width="80" height="20" class="foreign-key" />
    <text x="350" y="205" text-anchor="middle" class="text">a_id (FK)</text>
    <rect x="410" y="190" width="80" height="20" class="foreign-key" />
    <text x="450" y="205" text-anchor="middle" class="text">b_id (FK)</text>
    
    <path d="M 160 260 L 300 260" class="arrow" stroke-dasharray="5,5" />
    <path d="M 500 260 L 640 260" class="arrow" stroke-dasharray="5,5" />
    <text x="400" y="280" text-anchor="middle" class="text">Table de liaison avec clés étrangères vers A et B</text>
  </g>
  
  <!-- Cardinalité 1,n -->
  <g transform="translate(0, 600)">
    <text x="400" y="0" text-anchor="middle" class="subtitle">Cardinalité 1,n</text>
    
    <!-- MCD -->
    <rect x="100" y="30" width="120" height="80" rx="5" class="mcd" />
    <text x="160" y="60" text-anchor="middle" class="text" fill="white">Entité A</text>
    
    <rect x="580" y="30" width="120" height="80" rx="5" class="mcd" />
    <text x="640" y="60" text-anchor="middle" class="text" fill="white">Entité B</text>
    
    <path d="M 220 70 L 580 70" class="arrow" />
    <polygon points="570 65, 580 70, 570 75" fill="black" />
    
    <text x="400" y="50" text-anchor="middle" class="cardinality">1,n</text>
    
    <!-- MLD -->
    <rect x="100" y="150" width="120" height="80" rx="5" class="mld" />
    <text x="160" y="180" text-anchor="middle" class="text">Table A</text>
    <rect x="110" y="190" width="100" height="20" class="primary-key" />
    <text x="160" y="205" text-anchor="middle" class="text">id (PK)</text>
    
    <rect x="580" y="150" width="120" height="80" rx="5" class="mld" />
    <text x="640" y="180" text-anchor="middle" class="text">Table B</text>
    <rect x="590" y="190" width="100" height="20" class="primary-key" />
    <text x="640" y="205" text-anchor="middle" class="text">id (PK)</text>
    
    <rect x="300" y="150" width="200" height="80" rx="5" class="mld" />
    <text x="400" y="180" text-anchor="middle" class="text">Table A_B</text>
    <rect x="310" y="190" width="80" height="20" class="foreign-key" />
    <text x="350" y="205" text-anchor="middle" class="text">a_id (FK)</text>
    <rect x="410" y="190" width="80" height="20" class="foreign-key" />
    <text x="450" y="205" text-anchor="middle" class="text">b_id (FK)</text>
    
    <path d="M 160 260 L 300 260" class="arrow" stroke-dasharray="5,5" />
    <path d="M 500 260 L 640 260" class="arrow" stroke-dasharray="5,5" />
    <text x="400" y="280" text-anchor="middle" class="text">Table de liaison avec clés étrangères vers A et B</text>
  </g>
</svg>"""
        
        # Écrire le fichier SVG
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(svg_content)
            
        return output_path
        
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
        
        # Courbe de Bézier avec lissage
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
        
        # Ajouter une marge pour l'effet de survol, l'ombre et les cardinalités
        margin = 20 if self.is_hovered or self.style["shadow"] or self.style["cardinality"]["show"] else 5
        return path.boundingRect().adjusted(-margin, -margin, margin, margin)
        
    def paint(self, painter: QPainter, option, widget) -> None:
        """Dessine la flèche avec effets visuels"""
        if not self.source or not self.target:
            return
            
        source_pos = self.source.scenePos()
        target_pos = self.target.scenePos()
        
        # Calculer les points de contrôle
        control_points = self._calculate_control_points(source_pos, target_pos)
        
        # Configurer le peintre
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Effet d'ombre
        if self.style["shadow"]:
            shadow = QPainterPathStroker()
            shadow.setWidth(self.style["shadow_width"])
            shadow.setColor(self.style["shadow_color"])
            path = self._get_arrow_path(control_points)
            painter.drawPath(shadow.createStroke(path))
        
        # Effet de survol
        if self.is_hovered and self.style["hover_effect"]:
            painter.setPen(QPen(self.style["color"], self.style["width"] + 2))
        else:
            painter.setPen(QPen(self.style["color"], self.style["width"]))
            
        painter.setBrush(Qt.BrushStyle.NoBrush)
        
        # Dessiner la courbe
        path = self._get_arrow_path(control_points)
        painter.drawPath(path)
        
        # Dessiner la pointe de la flèche
        arrow_points = self._calculate_arrow_points(control_points[3], control_points[2])
        painter.drawLine(control_points[3], arrow_points[0])
        painter.drawLine(control_points[3], arrow_points[1])
        
        # Dessiner les cardinalités
        if self.style["cardinality"]["show"]:
            self._draw_cardinalities(painter, control_points)
        
    def _draw_cardinalities(self, painter: QPainter, control_points: list) -> None:
        """Dessine les cardinalités sur la flèche"""
        # Configurer le texte
        painter.setFont(self.style["cardinality"]["font"])
        painter.setPen(self.style["cardinality"]["color"])
        
        # Calculer le point milieu de la courbe
        mid_point = self._get_mid_point(control_points)
        
        # Calculer la normale à la courbe au point milieu
        normal = self._get_normal_at_point(control_points, mid_point)
        
        # Positionner les cardinalités
        offset = self.style["cardinality"]["offset"]
        
        # Source cardinality
        source_pos = QPointF(
            mid_point.x() - normal.x() * offset,
            mid_point.y() - normal.y() * offset
        )
        
        # Target cardinality
        target_pos = QPointF(
            mid_point.x() + normal.x() * offset,
            mid_point.y() + normal.y() * offset
        )
        
        # Dessiner les cardinalités
        source_text = self.style["cardinality"]["source"]
        target_text = self.style["cardinality"]["target"]
        
        # Ajuster la position du texte pour qu'il soit centré
        source_rect = painter.fontMetrics().boundingRect(source_text)
        target_rect = painter.fontMetrics().boundingRect(target_text)
        
        painter.drawText(
            source_pos.x() - source_rect.width() / 2,
            source_pos.y() + source_rect.height() / 2,
            source_text
        )
        
        painter.drawText(
            target_pos.x() - target_rect.width() / 2,
            target_pos.y() + target_rect.height() / 2,
            target_text
        )
        
    def _get_mid_point(self, control_points: list) -> QPointF:
        """Calcule le point milieu de la courbe de Bézier"""
        # Approximation du point milieu
        t = 0.5
        p0, p1, p2, p3 = control_points
        
        # Formule de Bézier pour t=0.5
        x = (1-t)**3 * p0.x() + 3*(1-t)**2 * t * p1.x() + 3*(1-t) * t**2 * p2.x() + t**3 * p3.x()
        y = (1-t)**3 * p0.y() + 3*(1-t)**2 * t * p1.y() + 3*(1-t) * t**2 * p2.y() + t**3 * p3.y()
        
        return QPointF(x, y)
        
    def _get_normal_at_point(self, control_points: list, point: QPointF) -> QPointF:
        """Calcule la normale à la courbe au point donné"""
        # Approximation de la tangente
        t = 0.5  # Même valeur que pour le point milieu
        p0, p1, p2, p3 = control_points
        
        # Dérivée de la courbe de Bézier
        dx = 3*(1-t)**2 * (p1.x() - p0.x()) + 6*(1-t)*t * (p2.x() - p1.x()) + 3*t**2 * (p3.x() - p2.x())
        dy = 3*(1-t)**2 * (p1.y() - p0.y()) + 6*(1-t)*t * (p2.y() - p1.y()) + 3*t**2 * (p3.y() - p2.y())
        
        # Normaliser
        length = (dx**2 + dy**2)**0.5
        if length == 0:
            return QPointF(0, 1)  # Vecteur vertical par défaut
            
        # Retourner la normale (perpendiculaire)
        return QPointF(-dy/length, dx/length)
        
    def _get_arrow_path(self, control_points: list) -> QPainterPath:
        """Crée le chemin de la flèche avec lissage"""
        path = QPainterPath()
        path.moveTo(control_points[0])
        
        # Courbe de Bézier avec lissage
        tension = self.style["curve_tension"]
        smoothness = self.style["smoothness"]
        
        # Points de contrôle ajustés pour le lissage
        c1 = QPointF(
            control_points[1].x() + (control_points[2].x() - control_points[1].x()) * smoothness,
            control_points[1].y() + (control_points[2].y() - control_points[1].y()) * smoothness
        )
        c2 = QPointF(
            control_points[2].x() - (control_points[2].x() - control_points[1].x()) * smoothness,
            control_points[2].y() - (control_points[2].y() - control_points[1].y()) * smoothness
        )
        
        path.cubicTo(c1, c2, control_points[3])
        return path
        
    def _calculate_control_points(self, source_pos: QPointF, target_pos: QPointF) -> list:
        """Calcule les points de contrôle pour la courbe de Bézier"""
        # Inverser les points si la flèche est inversée
        if self.is_reversed:
            source_pos, target_pos = target_pos, source_pos
            
        # Point de départ
        start = QPointF(source_pos.x(), source_pos.y())
        
        # Point d'arrivée
        end = QPointF(target_pos.x(), target_pos.y())
        
        # Points de contrôle
        dx = end.x() - start.x()
        dy = end.y() - start.y()
        
        # Ajuster la tension de la courbe
        tension = self.style["curve_tension"]
        
        control1 = QPointF(
            start.x() + dx * 0.25 * tension,
            start.y() + dy * 0.25 * tension
        )
        control2 = QPointF(
            start.x() + dx * 0.75 * tension,
            start.y() + dy * 0.75 * tension
        )
        
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
        self.style.update(style)
        self.update()
        
    def reverse(self) -> None:
        """Inverse le sens de la flèche"""
        self.is_reversed = not self.is_reversed
        self.update()
        
    def setCardinality(self, source: str = None, target: str = None) -> None:
        """Définit les cardinalités de la flèche"""
        if source is not None:
            self.style["cardinality"]["source"] = source
        if target is not None:
            self.style["cardinality"]["target"] = target
        self.update()
        
    def cycleSourceCardinality(self) -> None:
        """Change cycliquement la cardinalité source"""
        current = self.style["cardinality"]["source"]
        try:
            index = self.available_cardinalities.index(current)
            next_index = (index + 1) % len(self.available_cardinalities)
            self.style["cardinality"]["source"] = self.available_cardinalities[next_index]
            self.update()
        except ValueError:
            # Si la cardinalité n'est pas dans la liste, utiliser la première
            self.style["cardinality"]["source"] = self.available_cardinalities[0]
            self.update()
            
    def cycleTargetCardinality(self) -> None:
        """Change cycliquement la cardinalité cible"""
        current = self.style["cardinality"]["target"]
        try:
            index = self.available_cardinalities.index(current)
            next_index = (index + 1) % len(self.available_cardinalities)
            self.style["cardinality"]["target"] = self.available_cardinalities[next_index]
            self.update()
        except ValueError:
            # Si la cardinalité n'est pas dans la liste, utiliser la première
            self.style["cardinality"]["target"] = self.available_cardinalities[0]
            self.update()
            
    def setAvailableCardinalities(self, cardinalities: list) -> None:
        """Définit les cardinalités disponibles"""
        self.available_cardinalities = cardinalities
        
    def hoverEnterEvent(self, event) -> None:
        """Gère l'entrée du curseur"""
        self.is_hovered = True
        self.update()
        
    def hoverLeaveEvent(self, event) -> None:
        """Gère la sortie du curseur"""
        self.is_hovered = False
        self.update()
        
    def mouseDoubleClickEvent(self, event) -> None:
        """Gère le double-clic sur la flèche"""
        # Inverser la flèche au double-clic
        self.reverse()
        
    def to_dict(self) -> dict:
        """Convertit la flèche en dictionnaire pour la sauvegarde"""
        return {
            "source_id": self.source.id if hasattr(self.source, "id") else None,
            "target_id": self.target.id if hasattr(self.target, "id") else None,
            "is_reversed": self.is_reversed,
            "style": {
                "color": self.style["color"].name(),
                "width": self.style["width"],
                "arrow_size": self.style["arrow_size"],
                "curve_tension": self.style["curve_tension"],
                "hover_effect": self.style["hover_effect"],
                "smoothness": self.style["smoothness"],
                "shadow": self.style["shadow"],
                "shadow_color": self.style["shadow_color"].name(),
                "shadow_width": self.style["shadow_width"],
                "cardinality": {
                    "source": self.style["cardinality"]["source"],
                    "target": self.style["cardinality"]["target"],
                    "show": self.style["cardinality"]["show"]
                }
            }
        }
        
    @classmethod
    def from_dict(cls, data: dict, source: QGraphicsItem, target: QGraphicsItem) -> 'FlexibleArrow':
        """Crée une flèche à partir d'un dictionnaire"""
        arrow = cls(source, target)
        
        # Restaurer l'état
        arrow.is_reversed = data.get("is_reversed", False)
        
        # Restaurer le style
        arrow.style = {
            "color": QColor(data["style"]["color"]),
            "width": data["style"]["width"],
            "arrow_size": data["style"]["arrow_size"],
            "curve_tension": data["style"].get("curve_tension", 0.5),
            "hover_effect": data["style"].get("hover_effect", True),
            "smoothness": data["style"].get("smoothness", 0.3),
            "shadow": data["style"].get("shadow", True),
            "shadow_color": QColor(data["style"].get("shadow_color", "#0000001E")),
            "shadow_width": data["style"].get("shadow_width", 4),
            "cardinality": {
                "source": data["style"].get("cardinality", {}).get("source", "1,1"),
                "target": data["style"].get("cardinality", {}).get("target", "1,1"),
                "show": data["style"].get("cardinality", {}).get("show", True),
                "font": QFont("Arial", 8),
                "color": QColor(0, 0, 0),
                "offset": 15
            }
        }
        
        return arrow
        
    def get_mld_rules(self) -> dict:
        """Retourne les règles MLD pour la relation"""
        source_card = self.style["cardinality"]["source"]
        target_card = self.style["cardinality"]["target"]
        
        # Si la flèche est inversée, inverser les cardinalités
        if self.is_reversed:
            source_card, target_card = target_card, source_card
            
        return {
            "source": self.mld_rules[source_card],
            "target": self.mld_rules[target_card]
        }
        
    def generate_mld_sql(self) -> str:
        """Génère le SQL pour la création des tables selon les règles MLD"""
        source_card = self.style["cardinality"]["source"]
        target_card = self.style["cardinality"]["target"]
        
        # Si la flèche est inversée, inverser les cardinalités
        if self.is_reversed:
            source_card, target_card = target_card, source_card
            
        source_rules = self.mld_rules[source_card]
        target_rules = self.mld_rules[target_card]
        
        sql = []
        
        # Récupérer les noms des entités
        source_name = self.source.name if hasattr(self.source, "name") else "source"
        target_name = self.target.name if hasattr(self.target, "name") else "target"
        
        # Cas 1: Relation avec table principale (0,1 ou 1,1)
        if source_rules["table_type"] == "principale" and target_rules["table_type"] == "principale":
            # Choisir la table qui portera la clé étrangère (celle avec 0,1)
            if source_card == "0,1":
                sql.append(f"ALTER TABLE {source_name} ADD COLUMN {target_name}_id INTEGER")
                if source_rules["foreign_key"]["required"]:
                    sql.append(f"ALTER TABLE {source_name} ALTER COLUMN {target_name}_id SET NOT NULL")
                if source_rules["foreign_key"]["unique"]:
                    sql.append(f"ALTER TABLE {source_name} ADD UNIQUE ({target_name}_id)")
                sql.append(f"ALTER TABLE {source_name} ADD FOREIGN KEY ({target_name}_id) REFERENCES {target_name}(id)")
            else:
                sql.append(f"ALTER TABLE {target_name} ADD COLUMN {source_name}_id INTEGER")
                if target_rules["foreign_key"]["required"]:
                    sql.append(f"ALTER TABLE {target_name} ALTER COLUMN {source_name}_id SET NOT NULL")
                if target_rules["foreign_key"]["unique"]:
                    sql.append(f"ALTER TABLE {target_name} ADD UNIQUE ({source_name}_id)")
                sql.append(f"ALTER TABLE {target_name} ADD FOREIGN KEY ({source_name}_id) REFERENCES {source_name}(id)")
                
        # Cas 2: Relation avec table intermédiaire (0,n ou 1,n)
        else:
            table_name = f"{source_name}_{target_name}"
            sql.append(f"CREATE TABLE {table_name} (")
            sql.append(f"    {source_name}_id INTEGER NOT NULL,")
            sql.append(f"    {target_name}_id INTEGER NOT NULL,")
            sql.append(f"    PRIMARY KEY ({source_name}_id, {target_name}_id),")
            sql.append(f"    FOREIGN KEY ({source_name}_id) REFERENCES {source_name}(id),")
            sql.append(f"    FOREIGN KEY ({target_name}_id) REFERENCES {target_name}(id)")
            sql.append(");")
            
        return "\n".join(sql)
        
    def to_mld(self) -> dict:
        """Convertit la relation en format MLD"""
        source_card = self.style["cardinality"]["source"]
        target_card = self.style["cardinality"]["target"]
        
        # Si la flèche est inversée, inverser les cardinalités
        if self.is_reversed:
            source_card, target_card = target_card, source_card
            
        source_rules = self.mld_rules[source_card]
        target_rules = self.mld_rules[target_card]
        
        # Récupérer les noms des entités
        source_name = self.source.name if hasattr(self.source, "name") else "source"
        target_name = self.target.name if hasattr(self.target, "name") else "target"
        
        return {
            "source": {
                "name": source_name,
                "rules": source_rules,
                "cardinality": source_card
            },
            "target": {
                "name": target_name,
                "rules": target_rules,
                "cardinality": target_card
            },
            "sql": self.generate_mld_sql()
        } 