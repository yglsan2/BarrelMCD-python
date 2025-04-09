from PyQt5.QtWidgets import QLabel, QWidget, QVBoxLayout
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QPixmap
import os

class LogoWidget(QWidget):
    """Widget pour afficher le logo BARREL de manière responsive"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Création du label pour le logo
        self.logo_label = QLabel(self)
        self.logo_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.logo_label)
        
        # Chargement du logo approprié
        self.update_logo()
        
    def update_logo(self):
        """Met à jour le logo en fonction de la taille de la fenêtre"""
        width = self.width()
        
        # Sélection du logo en fonction de la largeur
        if width >= 1024:
            logo_path = "static/img/desktop/BARREL v4 avec-dark.svg"
            size = QSize(200, 200)
        elif width >= 768:
            logo_path = "static/img/tablet/BARREL v4 sans-dark.svg"
            size = QSize(120, 120)
        else:
            logo_path = "static/img/mobile/BARREL v4 sans-dark.svg"
            size = QSize(80, 80)
            
        # Vérification de l'existence du fichier
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path)
            scaled_pixmap = pixmap.scaled(size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.logo_label.setPixmap(scaled_pixmap)
            
    def resizeEvent(self, event):
        """Gère le redimensionnement du widget"""
        super().resizeEvent(event)
        self.update_logo() 