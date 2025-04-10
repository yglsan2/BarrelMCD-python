import unittest
from unittest.mock import MagicMock
from views.mcd_validator import MCDValidator

class TestMCDValidator(unittest.TestCase):
    def setUp(self):
        self.validator = MCDValidator()
        self.validator.validation_completed = MagicMock()
        self.validator.validation_error = MagicMock()

    def test_validate_valid_mcd(self):
        valid_mcd = {
            "entities": {
                "Client": {
                    "attributes": ["id", "nom", "prenom", "email"],
                    "primary_key": "id"
                },
                "Commande": {
                    "attributes": ["numero", "date", "montant"],
                    "primary_key": "numero"
                }
            },
            "relations": [
                {
                    "name": "Commande_Client",
                    "source": "Client",
                    "target": "Commande",
                    "cardinality": "1,n"
                }
            ]
        }
        
        result = self.validator.validate_mcd(valid_mcd)
        self.assertTrue(result)
        self.validator.validation_completed.emit.assert_called_once()

    def test_validate_invalid_mcd_duplicate_entity(self):
        invalid_mcd = {
            "entities": {
                "Client": {
                    "attributes": ["id", "nom"],
                    "primary_key": "id"
                },
                "Client": {  # Doublon
                    "attributes": ["id", "nom"],
                    "primary_key": "id"
                }
            },
            "relations": []
        }
        
        result = self.validator.validate_mcd(invalid_mcd)
        self.assertFalse(result)
        self.validator.validation_error.emit.assert_called()

    def test_validate_invalid_mcd_empty_attributes(self):
        invalid_mcd = {
            "entities": {
                "Client": {
                    "attributes": [],
                    "primary_key": "id"
                }
            },
            "relations": []
        }
        
        result = self.validator.validate_mcd(invalid_mcd)
        self.assertFalse(result)
        self.validator.validation_error.emit.assert_called()

    def test_validate_invalid_mcd_invalid_cardinality(self):
        invalid_mcd = {
            "entities": {
                "Client": {
                    "attributes": ["id", "nom"],
                    "primary_key": "id"
                },
                "Commande": {
                    "attributes": ["numero", "date"],
                    "primary_key": "numero"
                }
            },
            "relations": [
                {
                    "name": "Commande_Client",
                    "source": "Client",
                    "target": "Commande",
                    "cardinality": "invalid"  # Cardinalité invalide
                }
            ]
        }
        
        result = self.validator.validate_mcd(invalid_mcd)
        self.assertFalse(result)
        self.validator.validation_error.emit.assert_called()

if __name__ == '__main__':
    unittest.main() 