import pytest
from PyQt5.QtWidgets import QApplication, QGraphicsScene
from PyQt5.QtCore import QPointF, QRectF
from views.mcd_drawer import MCDDrawer

# Créer une instance de QApplication pour les tests
app = QApplication([])

def test_init():
    """Test l'initialisation du MCDDrawer."""
    drawer = MCDDrawer()
    
    assert drawer.colors is not None
    assert drawer.fonts is not None
    assert drawer.margin > 0
    assert drawer.entity_width > 0
    assert drawer.entity_min_height > 0
    assert drawer.grid_size > 0

def test_draw_entity():
    """Test le dessin d'une entité."""
    drawer = MCDDrawer()
    scene = QGraphicsScene()
    
    entity = {
        "name": "client",
        "attributes": [
            {"name": "id", "type": "integer", "is_pk": True},
            {"name": "nom", "type": "varchar", "is_pk": False}
        ]
    }
    
    pos = QPointF(100, 100)
    box = drawer._draw_entity(scene, entity, pos)
    
    assert isinstance(box, QRectF)
    assert box.x() == pos.x()
    assert box.y() == pos.y()
    assert box.width() == drawer.entity_width
    assert box.height() >= drawer.entity_min_height
    assert len(scene.items()) > 0

def test_draw_relation():
    """Test le dessin d'une relation."""
    drawer = MCDDrawer()
    scene = QGraphicsScene()
    
    relation = {
        "name": "passe",
        "cardinality": "1:*"
    }
    
    entity1_box = QRectF(100, 100, drawer.entity_width, drawer.entity_min_height)
    entity2_box = QRectF(400, 100, drawer.entity_width, drawer.entity_min_height)
    
    drawer._draw_relation(scene, relation, entity1_box, entity2_box)
    
    # Vérifier que les éléments ont été ajoutés à la scène
    assert len(scene.items()) > 0

def test_calculate_positions():
    """Test le calcul des positions des entités."""
    drawer = MCDDrawer()
    
    mcd = {
        "entities": [
            {
                "name": "client",
                "attributes": [
                    {"name": "id", "type": "integer", "is_pk": True},
                    {"name": "nom", "type": "varchar", "is_pk": False}
                ]
            },
            {
                "name": "commande",
                "attributes": [
                    {"name": "id", "type": "integer", "is_pk": True},
                    {"name": "date", "type": "date", "is_pk": False}
                ]
            }
        ]
    }
    
    positions = drawer._calculate_positions(mcd)
    
    assert len(positions) == 2
    assert "client" in positions
    assert "commande" in positions
    assert isinstance(positions["client"], QPointF)
    assert isinstance(positions["commande"], QPointF)
    
    # Vérifier que les positions sont différentes
    assert positions["client"] != positions["commande"]

def test_calculate_connection_point():
    """Test le calcul des points de connexion."""
    drawer = MCDDrawer()
    
    box = QRectF(100, 100, drawer.entity_width, drawer.entity_min_height)
    target = QPointF(400, 100)
    
    point = drawer._calculate_connection_point(box, target)
    
    assert isinstance(point, QPointF)
    assert point.x() >= box.left()
    assert point.x() <= box.right()
    assert point.y() >= box.top()
    assert point.y() <= box.bottom()

def test_draw_mcd():
    """Test le dessin complet du MCD."""
    drawer = MCDDrawer()
    scene = QGraphicsScene()
    
    mcd = {
        "entities": [
            {
                "name": "client",
                "attributes": [
                    {"name": "id", "type": "integer", "is_pk": True},
                    {"name": "nom", "type": "varchar", "is_pk": False}
                ]
            },
            {
                "name": "commande",
                "attributes": [
                    {"name": "id", "type": "integer", "is_pk": True},
                    {"name": "date", "type": "date", "is_pk": False}
                ]
            }
        ],
        "relations": [
            {
                "name": "passe",
                "entity1": "client",
                "entity2": "commande",
                "cardinality": "1:*"
            }
        ]
    }
    
    drawer.draw_mcd(scene, mcd)
    
    # Vérifier que la scène contient des éléments
    assert len(scene.items()) > 0
    
    # Vérifier que la grille a été dessinée
    grid_items = [item for item in scene.items() if item.type() == 6]  # 6 = QGraphicsLineItem
    assert len(grid_items) > 0 