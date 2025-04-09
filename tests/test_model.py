import unittest
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt, QPointF
from BarrelMCD-python-main.models.entity import Entity
from BarrelMCD-python-main.models.data_types import DataTypeManager
import sys

class TestEntity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Initialisation de l'application Qt pour les tests"""
        cls.app = QApplication(sys.argv)
        
    def setUp(self):
        """Initialisation avant chaque test"""
        self.entity = Entity(0, 0, "TestEntity")
        self.data_type_manager = DataTypeManager()
        
    def test_entity_creation(self):
        """Test de la création d'une entité"""
        self.assertEqual(self.entity.name, "TestEntity")
        self.assertEqual(len(self.entity.attributes), 0)
        
    def test_add_attribute(self):
        """Test de l'ajout d'attributs"""
        # Ajout d'un attribut
        self.entity.add_attribute("TestAttribute", "VARCHAR(100)")
        
        # Vérifications
        self.assertEqual(len(self.entity.attributes), 1)
        self.assertEqual(self.entity.attributes[0]["name"], "TestAttribute")
        
    def test_remove_attribute(self):
        """Test de la suppression d'attributs"""
        # Ajout d'un attribut
        self.entity.add_attribute("TestAttribute", "VARCHAR(100)")
        
        # Suppression de l'attribut
        self.entity.remove_attribute("TestAttribute")
        
        # Vérification
        self.assertEqual(len(self.entity.attributes), 0)
        
    def test_entity_serialization(self):
        """Test de la sérialisation de l'entité"""
        # Ajout d'attributs
        self.entity.add_attribute("Attr1", "INT")
        self.entity.add_attribute("Attr2", "VARCHAR(100)")
        
        # Sérialisation
        entity_dict = self.entity.to_dict()
        
        # Vérifications
        self.assertEqual(entity_dict["name"], "TestEntity")
        self.assertEqual(len(entity_dict["attributes"]), 2)
        
    def test_entity_deserialization(self):
        """Test de la désérialisation de l'entité"""
        # Création d'un dictionnaire de test
        entity_dict = {
            "name": "TestEntity",
            "attributes": [
                {
                    "name": "Attr1",
                    "type": "INT"
                },
                {
                    "name": "Attr2",
                    "type": "VARCHAR(100)"
                }
            ]
        }
        
        # Désérialisation
        new_entity = Entity.from_dict(entity_dict)
        
        # Vérifications
        self.assertEqual(new_entity.name, "TestEntity")
        self.assertEqual(len(new_entity.attributes), 2)
        
    def test_attribute_validation(self):
        """Test de la validation des attributs"""
        # Test avec un nom invalide
        with self.assertRaises(ValueError):
            self.entity.add_attribute("", "VARCHAR(100)")
            
        # Test avec un type invalide
        with self.assertRaises(ValueError):
            self.entity.add_attribute("Test", "")
            
    def test_entity_validation(self):
        """Test de la validation de l'entité"""
        # Test avec un nom invalide
        with self.assertRaises(ValueError):
            Entity(0, 0, "")
            
        # Test avec des attributs en double
        self.entity.add_attribute("Test", "VARCHAR(100)")
        with self.assertRaises(ValueError):
            self.entity.add_attribute("Test", "INT")
            
if __name__ == '__main__':
    unittest.main() 