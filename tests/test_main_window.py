import unittest
from PyQt5.QtWidgets import QApplication, QDialog, QFileDialog, QDockWidget, QPushButton
from PyQt5.QtCore import Qt
from views.main_window import MainWindow
from views.sql_dialog import SQLConversionDialog
import sys
import os

class TestMainWindow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Initialisation de l'application Qt pour les tests"""
        cls.app = QApplication(sys.argv)
        
    def setUp(self):
        """Initialisation avant chaque test"""
        self.window = MainWindow()
        
    def tearDown(self):
        """Nettoyage après chaque test"""
        self.window.close()
        
    def test_window_initialization(self):
        """Test de l'initialisation de la fenêtre"""
        self.assertEqual(self.window.windowTitle(), "BarrelMCD")
        self.assertGreaterEqual(self.window.width(), 800)
        self.assertGreaterEqual(self.window.height(), 600)
        
    def test_security_manager(self):
        """Test du gestionnaire de sécurité"""
        # Vérifier que le gestionnaire de sécurité est initialisé
        self.assertIsNotNone(self.window.security_manager)
        
        # Test de la validation des entrées
        self.assertTrue(self.window.security_manager.validate_input("valid_input"))
        self.assertFalse(self.window.security_manager.validate_input("SELECT * FROM users"))
        self.assertFalse(self.window.security_manager.validate_input("<script>alert('xss')</script>"))
        
    def test_touch_button(self):
        """Test des boutons tactiles"""
        # Vérifier que les boutons sont créés avec les bonnes dimensions
        for button in self.window.findChildren(QPushButton):
            if hasattr(button, 'is_touch_button') and button.is_touch_button:
                self.assertGreaterEqual(button.minimumWidth(), 80)
                self.assertGreaterEqual(button.minimumHeight(), 40)
                self.assertIn("background-color", button.styleSheet())
                self.assertIn("border-radius", button.styleSheet())
        
    def test_model_operations(self):
        """Test des opérations sur les modèles"""
        # Test de création d'une nouvelle entité
        initial_count = len(self.window.scene.items())
        self.window.add_entity()
        self.assertGreater(len(self.window.scene.items()), initial_count)
        
        # Test d'ajout d'attribut
        entity = self.window.scene.items()[0]  # Première entité
        initial_attr_count = len(entity.attributes)
        self.window.add_attribute(entity)
        self.assertGreater(len(entity.attributes), initial_attr_count)
        
    def test_sql_conversion(self):
        """Test de la conversion SQL"""
        # Test de l'ouverture du dialogue de conversion
        self.window.show_sql_conversion()
        # Vérifier que le dialogue est visible
        self.assertTrue(any(isinstance(w, SQLConversionDialog) for w in self.window.findChildren(QDialog)))
        
    def test_file_operations(self):
        """Test des opérations sur les fichiers"""
        # Créer un fichier temporaire pour les tests
        test_file = "test_model.bcd"
        
        try:
            # Test de sauvegarde
            self.window.save_model()
            # Vérifier que le dialogue de sauvegarde s'affiche
            self.assertTrue(any(isinstance(w, QFileDialog) for w in self.window.findChildren(QFileDialog)))
            
            # Test d'ouverture
            self.window.open_model()
            # Vérifier que le dialogue d'ouverture s'affiche
            self.assertTrue(any(isinstance(w, QFileDialog) for w in self.window.findChildren(QFileDialog)))
            
        finally:
            # Nettoyage
            if os.path.exists(test_file):
                os.remove(test_file)
                
    def test_responsive_layout(self):
        """Test de la mise en page responsive"""
        # Test du redimensionnement
        self.window.resize(400, 300)
        self.window.updateAllLayouts()
        
        # Vérifier que les boutons sont en mode vertical sur petit écran
        button_container = self.window.findChild(QWidget, "button_container")
        if button_container and button_container.layout():
            self.assertEqual(button_container.layout().direction(), Qt.Vertical)
        
        # Test du redimensionnement en grand écran
        self.window.resize(1200, 800)
        self.window.updateAllLayouts()
        
        # Vérifier que les boutons sont en mode horizontal sur grand écran
        if button_container and button_container.layout():
            self.assertEqual(button_container.layout().direction(), Qt.Horizontal)
        
    def test_security_features(self):
        """Test des fonctionnalités de sécurité"""
        # Test du verrouillage après trop de tentatives
        security = self.window.security_manager
        for _ in range(4):  # Plus que le maximum autorisé
            security.verify_password("wrong_password")
            
        self.assertIsNotNone(security.lockout_time)
        self.assertGreater(security.login_attempts, security.max_login_attempts)
        
    def test_error_handling(self):
        """Test de la gestion des erreurs"""
        # Test avec des données invalides
        with self.assertLogs(level='ERROR') as log:
            self.window.security_manager.encrypt_data(None)
            self.assertTrue(any("Erreur de chiffrement" in msg for msg in log.output))
            
        # Test avec un fichier inexistant
        with self.assertRaises(Exception):
            self.window.open_model("nonexistent_file.bcd")
            
    def test_ui_components(self):
        """Test des composants de l'interface"""
        # Vérifier la présence des éléments essentiels
        self.assertIsNotNone(self.window.menuBar())
        self.assertIsNotNone(self.window.statusBar())
        self.assertIsNotNone(self.window.centralWidget())
        
        # Vérifier les panneaux latéraux
        self.assertTrue(any(isinstance(d, QDockWidget) for d in self.window.findChildren(QDockWidget)))
        
if __name__ == '__main__':
    unittest.main() 