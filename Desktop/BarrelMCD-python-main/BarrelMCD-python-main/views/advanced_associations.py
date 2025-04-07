from PyQt6.QtCore import QObject, pyqtSignal, QPointF
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QPainterPath
from typing import List, Dict, Any
from ..models.entity import Entity
from ..models.association import Association
from .error_handler import ErrorHandler

class AdvancedAssociations(QObject):
    """Gestionnaire des associations avancées"""
    
    # Signaux
    association_created = pyqtSignal(Association)
    association_modified = pyqtSignal(Association)
    association_deleted = pyqtSignal(Association)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.error_handler = ErrorHandler(self)
        
        # Styles pour les différents types d'associations
        self.styles = {
            "generalization": {
                "color": QColor(52, 152, 219),
                "line_width": 2,
                "line_style": "solid",
                "arrow_style": "hollow"
            },
            "specialization": {
                "color": QColor(46, 204, 113),
                "line_width": 2,
                "line_style": "solid",
                "arrow_style": "hollow"
            },
            "aggregation": {
                "color": QColor(155, 89, 182),
                "line_width": 2,
                "line_style": "solid",
                "arrow_style": "diamond"
            },
            "composition": {
                "color": QColor(231, 76, 60),
                "line_width": 2,
                "line_style": "solid",
                "arrow_style": "filled_diamond"
            }
        }
        
    def create_generalization(self, parent: Entity, child: Entity) -> Association:
        """Crée une relation de généralisation"""
        try:
            # Vérification des entités
            if not self._validate_entities(parent, child):
                return None
                
            # Création de l'association
            assoc = Association(
                source=parent,
                target=child,
                type="generalization",
                cardinality="1,1"
            )
            
            # Configuration des attributs hérités
            self._setup_inherited_attributes(parent, child)
            
            self.association_created.emit(assoc)
            return assoc
            
        except Exception as e:
            self.error_handler.handle_error(e, "Erreur lors de la création de la généralisation")
            return None
            
    def create_specialization(self, parent: Entity, child: Entity) -> Association:
        """Crée une relation de spécialisation"""
        try:
            # Vérification des entités
            if not self._validate_entities(parent, child):
                return None
                
            # Création de l'association
            assoc = Association(
                source=child,
                target=parent,
                type="specialization",
                cardinality="1,1"
            )
            
            # Configuration des attributs spécifiques
            self._setup_specific_attributes(child)
            
            self.association_created.emit(assoc)
            return assoc
            
        except Exception as e:
            self.error_handler.handle_error(e, "Erreur lors de la création de la spécialisation")
            return None
            
    def create_aggregation(self, whole: Entity, part: Entity) -> Association:
        """Crée une relation d'agrégation"""
        try:
            # Vérification des entités
            if not self._validate_entities(whole, part):
                return None
                
            # Création de l'association
            assoc = Association(
                source=whole,
                target=part,
                type="aggregation",
                cardinality="1,n"
            )
            
            self.association_created.emit(assoc)
            return assoc
            
        except Exception as e:
            self.error_handler.handle_error(e, "Erreur lors de la création de l'agrégation")
            return None
            
    def create_composition(self, whole: Entity, part: Entity) -> Association:
        """Crée une relation de composition"""
        try:
            # Vérification des entités
            if not self._validate_entities(whole, part):
                return None
                
            # Création de l'association
            assoc = Association(
                source=whole,
                target=part,
                type="composition",
                cardinality="1,n"
            )
            
            self.association_created.emit(assoc)
            return assoc
            
        except Exception as e:
            self.error_handler.handle_error(e, "Erreur lors de la création de la composition")
            return None
            
    def _validate_entities(self, entity1: Entity, entity2: Entity) -> bool:
        """Valide les entités pour une association"""
        try:
            if entity1 == entity2:
                self.error_handler.handle_warning(
                    "Impossible de créer une association",
                    "Une entité ne peut pas être associée à elle-même"
                )
                return False
                
            return True
            
        except Exception as e:
            self.error_handler.handle_error(e, "Erreur lors de la validation des entités")
            return False
            
    def _setup_inherited_attributes(self, parent: Entity, child: Entity):
        """Configure les attributs hérités"""
        try:
            for attr in parent.attributes:
                # Copie des attributs non-clés
                if not attr.is_primary_key:
                    child.attributes.append(attr.copy())
                    
        except Exception as e:
            self.error_handler.handle_error(e, "Erreur lors de la configuration des attributs hérités")
            
    def _setup_specific_attributes(self, entity: Entity):
        """Configure les attributs spécifiques"""
        try:
            # Ajout d'un attribut discriminant
            entity.attributes.append(Attribute(
                name="type",
                data_type="VARCHAR(50)",
                is_primary_key=False,
                is_unique=False,
                is_not_null=True
            ))
            
        except Exception as e:
            self.error_handler.handle_error(e, "Erreur lors de la configuration des attributs spécifiques")
            
    def draw_association(self, painter: QPainter, assoc: Association, source_pos: QPointF, target_pos: QPointF):
        """Dessine une association avancée"""
        try:
            style = self.styles.get(assoc.type)
            if not style:
                return
                
            # Configuration du style
            painter.setPen(QPen(style["color"], style["line_width"]))
            
            # Dessin de la ligne
            path = QPainterPath()
            path.moveTo(source_pos)
            path.lineTo(target_pos)
            painter.drawPath(path)
            
            # Dessin de la flèche selon le type
            if style["arrow_style"] == "hollow":
                self._draw_hollow_arrow(painter, source_pos, target_pos)
            elif style["arrow_style"] == "diamond":
                self._draw_diamond_arrow(painter, source_pos, target_pos, False)
            elif style["arrow_style"] == "filled_diamond":
                self._draw_diamond_arrow(painter, source_pos, target_pos, True)
                
        except Exception as e:
            self.error_handler.handle_error(e, "Erreur lors du dessin de l'association")
            
    def _draw_hollow_arrow(self, painter: QPainter, source_pos: QPointF, target_pos: QPointF):
        """Dessine une flèche creuse"""
        try:
            # Calcul des points de la flèche
            angle = math.atan2(target_pos.y() - source_pos.y(),
                             target_pos.x() - source_pos.x())
            arrow_size = 20
            
            p1 = QPointF(
                target_pos.x() - arrow_size * math.cos(angle - math.pi/6),
                target_pos.y() - arrow_size * math.sin(angle - math.pi/6)
            )
            p2 = QPointF(
                target_pos.x() - arrow_size * math.cos(angle + math.pi/6),
                target_pos.y() - arrow_size * math.sin(angle + math.pi/6)
            )
            
            # Dessin de la flèche
            path = QPainterPath()
            path.moveTo(p1)
            path.lineTo(target_pos)
            path.lineTo(p2)
            painter.drawPath(path)
            
        except Exception as e:
            self.error_handler.handle_error(e, "Erreur lors du dessin de la flèche creuse")
            
    def _draw_diamond_arrow(self, painter: QPainter, source_pos: QPointF, target_pos: QPointF, filled: bool):
        """Dessine une flèche en diamant"""
        try:
            # Calcul des points du diamant
            angle = math.atan2(target_pos.y() - source_pos.y(),
                             target_pos.x() - source_pos.x())
            arrow_size = 20
            
            p1 = QPointF(
                target_pos.x() - arrow_size * math.cos(angle - math.pi/4),
                target_pos.y() - arrow_size * math.sin(angle - math.pi/4)
            )
            p2 = QPointF(
                target_pos.x() - arrow_size * math.cos(angle + math.pi/4),
                target_pos.y() - arrow_size * math.sin(angle + math.pi/4)
            )
            
            # Dessin du diamant
            path = QPainterPath()
            path.moveTo(p1)
            path.lineTo(target_pos)
            path.lineTo(p2)
            path.lineTo(source_pos)
            path.closeSubpath()
            
            if filled:
                painter.fillPath(path, painter.pen().color())
            else:
                painter.drawPath(path)
                
        except Exception as e:
            self.error_handler.handle_error(e, "Erreur lors du dessin de la flèche en diamant") 