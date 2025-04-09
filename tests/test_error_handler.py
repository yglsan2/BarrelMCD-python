import unittest
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QObject
from models.error_handler import ErrorHandler
import sys
import os
import logging
from unittest.mock import patch, MagicMock

class TestErrorHandler(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Initialisation de l'application Qt pour les tests"""
        cls.app = QApplication(sys.argv)
        
    def setUp(self):
        """Initialisation avant chaque test"""
        self.error_handler = ErrorHandler()
        
    def test_error_handling(self):
        """Test de la gestion des erreurs"""
        # Test avec une exception simple
        with self.assertLogs(level='ERROR') as log:
            self.error_handler.handle_error(Exception("Test error"), "Test context")
            self.assertTrue(any("Test error" in msg for msg in log.output))
            self.assertTrue(any("Test context" in msg for msg in log.output))
            
    def test_warning_handling(self):
        """Test de la gestion des avertissements"""
        # Test avec un avertissement
        with self.assertLogs(level='WARNING') as log:
            self.error_handler.handle_warning("Test warning", "Test context")
            self.assertTrue(any("Test warning" in msg for msg in log.output))
            self.assertTrue(any("Test context" in msg for msg in log.output))
            
    def test_info_handling(self):
        """Test de la gestion des informations"""
        # Test avec une information
        with self.assertLogs(level='INFO') as log:
            self.error_handler.handle_info("Test info", "Test context")
            self.assertTrue(any("Test info" in msg for msg in log.output))
            self.assertTrue(any("Test context" in msg for msg in log.output))
            
    def test_safe_execute(self):
        """Test de l'exécution sécurisée"""
        # Test avec une fonction qui réussit
        def success_func():
            return "Success"
            
        result = self.error_handler.safe_execute(success_func)
        self.assertEqual(result, "Success")
        
        # Test avec une fonction qui échoue
        def fail_func():
            raise Exception("Test error")
            
        result = self.error_handler.safe_execute(fail_func)
        self.assertIsNone(result)
        
    def test_validate_input(self):
        """Test de la validation des entrées"""
        # Test avec une validation qui réussit
        def success_validation(value):
            return value == "valid"
            
        result = self.error_handler.validate_input("valid", success_validation, "Test validation")
        self.assertTrue(result)
        
        # Test avec une validation qui échoue
        def fail_validation(value):
            raise ValueError("Invalid value")
            
        result = self.error_handler.validate_input("invalid", fail_validation, "Test validation")
        self.assertFalse(result)
        
    def test_check_file_access(self):
        """Test de la vérification de l'accès aux fichiers"""
        # Test avec un fichier existant
        with open("test_file.txt", "w") as f:
            f.write("Test content")
            
        try:
            result = self.error_handler.check_file_access("test_file.txt")
            self.assertTrue(result)
        finally:
            if os.path.exists("test_file.txt"):
                os.remove("test_file.txt")
                
        # Test avec un fichier inexistant
        result = self.error_handler.check_file_access("nonexistent_file.txt")
        self.assertFalse(result)
        
    def test_check_directory_access(self):
        """Test de la vérification de l'accès aux répertoires"""
        # Test avec un répertoire existant
        result = self.error_handler.check_directory_access(".")
        self.assertTrue(result)
        
        # Test avec un répertoire inexistant
        result = self.error_handler.check_directory_access("nonexistent_directory")
        self.assertFalse(result)
        
    def test_validate_file_size(self):
        """Test de la validation de la taille des fichiers"""
        # Créer un fichier temporaire
        with open("test_file.txt", "w") as f:
            f.write("Test content")
            
        try:
            # Test avec une taille acceptable
            result = self.error_handler.validate_file_size("test_file.txt", max_size_mb=1)
            self.assertTrue(result)
            
            # Test avec une taille trop grande
            result = self.error_handler.validate_file_size("test_file.txt", max_size_mb=0.0001)
            self.assertFalse(result)
        finally:
            if os.path.exists("test_file.txt"):
                os.remove("test_file.txt")
                
    def test_check_memory_usage(self):
        """Test de la vérification de l'utilisation de la mémoire"""
        # Simuler une utilisation de mémoire acceptable
        with patch('psutil.Process') as mock_process:
            mock_process.return_value.memory_info.return_value.rss = 100 * 1024 * 1024  # 100 MB
            result = self.error_handler.check_memory_usage(threshold_mb=200)
            self.assertTrue(result)
            
        # Simuler une utilisation de mémoire excessive
        with patch('psutil.Process') as mock_process:
            mock_process.return_value.memory_info.return_value.rss = 300 * 1024 * 1024  # 300 MB
            result = self.error_handler.check_memory_usage(threshold_mb=200)
            self.assertFalse(result)
            
    def test_validate_network_connection(self):
        """Test de la vérification de la connexion réseau"""
        # Simuler une connexion réussie
        with patch('socket.create_connection') as mock_socket:
            mock_socket.return_value = MagicMock()
            result = self.error_handler.validate_network_connection()
            self.assertTrue(result)
            
        # Simuler une connexion échouée
        with patch('socket.create_connection') as mock_socket:
            mock_socket.side_effect = Exception("Connection failed")
            result = self.error_handler.validate_network_connection()
            self.assertFalse(result)
            
    def test_check_disk_space(self):
        """Test de la vérification de l'espace disque"""
        # Simuler un espace disque suffisant
        with patch('shutil.disk_usage') as mock_disk:
            mock_disk.return_value.free = 200 * 1024 * 1024  # 200 MB
            result = self.error_handler.check_disk_space(".", required_mb=100)
            self.assertTrue(result)
            
        # Simuler un espace disque insuffisant
        with patch('shutil.disk_usage') as mock_disk:
            mock_disk.return_value.free = 50 * 1024 * 1024  # 50 MB
            result = self.error_handler.check_disk_space(".", required_mb=100)
            self.assertFalse(result)
            
    def test_validate_file_format(self):
        """Test de la validation du format de fichier"""
        # Test avec un format valide
        result = self.error_handler.validate_file_format("test.txt", [".txt", ".csv"])
        self.assertTrue(result)
        
        # Test avec un format invalide
        result = self.error_handler.validate_file_format("test.doc", [".txt", ".csv"])
        self.assertFalse(result)
        
    def test_check_system_resources(self):
        """Test de la vérification des ressources système"""
        # Simuler des ressources suffisantes
        with patch.object(self.error_handler, 'check_memory_usage', return_value=True), \
             patch.object(self.error_handler, 'check_disk_space', return_value=True), \
             patch.object(self.error_handler, 'validate_network_connection', return_value=True):
            result = self.error_handler.check_system_resources()
            self.assertTrue(result)
            
        # Simuler des ressources insuffisantes
        with patch.object(self.error_handler, 'check_memory_usage', return_value=False), \
             patch.object(self.error_handler, 'check_disk_space', return_value=True), \
             patch.object(self.error_handler, 'validate_network_connection', return_value=True):
            result = self.error_handler.check_system_resources()
            self.assertFalse(result)
            
if __name__ == '__main__':
    unittest.main() 