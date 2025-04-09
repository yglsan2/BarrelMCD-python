import unittest
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt, QPointF
from models.entity import Entity
from models.association import Association, FlexibleArrow
import sys

class TestAssociation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Initialisation de l'application Qt pour les tests"""
        cls.app = QApplication(sys.argv)
        
    def setUp(self):
        """Initialisation avant chaque test"""
        # Création de deux entités pour les tests
        self.entity1 = Entity(0, 0, "Entity1")
        self.entity2 = Entity(200, 0, "Entity2")
        
        # Création d'une association
        self.association = Association(self.entity1, self.entity2, "TestAssociation")
        
    def test_association_creation(self):
        """Test de la création d'une association"""
        self.assertEqual(self.association.name, "TestAssociation")
        self.assertEqual(self.association.entity1, self.entity1)
        self.assertEqual(self.association.entity2, self.entity2)
        
    def test_association_properties(self):
        """Test des propriétés de l'association"""
        # Test de la cardinalité
        self.association.set_cardinality1("1")
        self.association.set_cardinality2("n")
        
        self.assertEqual(self.association.cardinality1, "1")
        self.assertEqual(self.association.cardinality2, "n")
        
        # Test du type d'association
        self.association.set_type("Composition")
        self.assertEqual(self.association.type, "Composition")
        
    def test_flexible_arrow(self):
        """Test de la flèche flexible"""
        # Création d'une flèche flexible
        arrow = FlexibleArrow(self.entity1, self.entity2)
        
        # Test des points de contrôle
        self.assertEqual(len(arrow.control_points), 2)
        self.assertEqual(arrow.control_points[0], QPointF(0, 0))
        self.assertEqual(arrow.control_points[1], QPointF(200, 0))
        
        # Test de l'ajout de points de contrôle
        arrow.add_control_point(QPointF(100, 50))
        self.assertEqual(len(arrow.control_points), 3)
        self.assertEqual(arrow.control_points[1], QPointF(100, 50))
        
        # Test de la suppression de points de contrôle
        arrow.remove_control_point(1)
        self.assertEqual(len(arrow.control_points), 2)
        
    def test_association_serialization(self):
        """Test de la sérialisation de l'association"""
        # Configuration de l'association
        self.association.set_cardinality1("1")
        self.association.set_cardinality2("n")
        self.association.set_type("Composition")
        
        # Sérialisation
        association_dict = self.association.to_dict()
        
        # Vérifications
        self.assertEqual(association_dict["name"], "TestAssociation")
        self.assertEqual(association_dict["entity1_id"], self.entity1.id)
        self.assertEqual(association_dict["entity2_id"], self.entity2.id)
        self.assertEqual(association_dict["cardinality1"], "1")
        self.assertEqual(association_dict["cardinality2"], "n")
        self.assertEqual(association_dict["type"], "Composition")
        
    def test_association_deserialization(self):
        """Test de la désérialisation de l'association"""
        # Création d'un dictionnaire de test
        association_dict = {
            "name": "TestAssociation",
            "entity1_id": self.entity1.id,
            "entity2_id": self.entity2.id,
            "cardinality1": "1",
            "cardinality2": "n",
            "type": "Composition"
        }
        
        # Désérialisation
        new_association = Association.from_dict(association_dict, [self.entity1, self.entity2])
        
        # Vérifications
        self.assertEqual(new_association.name, "TestAssociation")
        self.assertEqual(new_association.entity1, self.entity1)
        self.assertEqual(new_association.entity2, self.entity2)
        self.assertEqual(new_association.cardinality1, "1")
        self.assertEqual(new_association.cardinality2, "n")
        self.assertEqual(new_association.type, "Composition")
        
    def test_association_validation(self):
        """Test de la validation de l'association"""
        # Test avec un nom invalide
        with self.assertRaises(ValueError):
            Association(self.entity1, self.entity2, "")
            
        # Test avec des entités identiques
        with self.assertRaises(ValueError):
            Association(self.entity1, self.entity1, "TestAssociation")
            
    def test_arrow_styles(self):
        """Test des styles de flèche"""
        # Création d'une flèche flexible
        arrow = FlexibleArrow(self.entity1, self.entity2)
        
        # Test du style par défaut
        self.assertIsNotNone(arrow.pen())
        self.assertIsNotNone(arrow.brush())
        
        # Test du changement de style
        arrow.set_style({
            "color": Qt.GlobalColor.red,
            "width": 3,
            "dash_pattern": [10, 5]
        })
        
        self.assertEqual(arrow.pen().color(), Qt.GlobalColor.red)
        self.assertEqual(arrow.pen().width(), 3)
        self.assertEqual(arrow.pen().style(), Qt.PenStyle.DashLine)
        
if __name__ == '__main__':
    unittest.main() 