#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Gestionnaire de logos pour BarrelMCD
"""

from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtWidgets import QLabel, QVBoxLayout, QWidget
import os

class LogoManager(QObject):
    """Gestionnaire de logos pour l'application"""
    
    def __init__(self):
        super().__init__()
        self.logos_path = "docs/logos"
        self.logos = {}
        self._load_logos()
    
    def _load_logos(self):
        """Charge les logos depuis le répertoire"""
        try:
            if os.path.exists(self.logos_path):
                for filename in os.listdir(self.logos_path):
                    if filename.endswith(('.svg', '.png', '.jpg', '.jpeg')):
                        logo_path = os.path.join(self.logos_path, filename)
                        logo_name = os.path.splitext(filename)[0]
                        self.logos[logo_name] = logo_path
        except Exception as e:
            print(f"Erreur lors du chargement des logos: {e}")
    
    def get_logo(self, logo_name: str) -> QIcon:
        """Retourne un logo sous forme d'icône"""
        if logo_name in self.logos:
            return QIcon(self.logos[logo_name])
        return QIcon()
    
    def get_logo_pixmap(self, logo_name: str, size: tuple = (64, 64)) -> QPixmap:
        """Retourne un logo sous forme de pixmap"""
        if logo_name in self.logos:
            pixmap = QPixmap(self.logos[logo_name])
            return pixmap.scaled(size[0], size[1], Qt.KeepAspectRatio, Qt.SmoothTransformation)
        return QPixmap()
    
    def create_logo_widget(self, logo_name: str = "BARREL v4 sans", 
                          app_name: str = "Barrel MCD", size: tuple = (128, 128)) -> QWidget:
        """Crée un widget avec logo et nom de l'application"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Logo
        logo_label = QLabel()
        logo_pixmap = self.get_logo_pixmap(logo_name, size)
        logo_label.setPixmap(logo_pixmap)
        logo_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(logo_label)
        
        # Nom de l'application
        if app_name:
            name_label = QLabel(app_name)
            name_label.setAlignment(Qt.AlignCenter)
            name_label.setStyleSheet("""
                QLabel {
                    font-size: 18px;
                    font-weight: bold;
                    color: #ffffff;
                    margin-top: 10px;
                }
            """)
            layout.addWidget(name_label)
        
        widget.setLayout(layout)
        return widget
    
    def get_available_logos(self) -> list:
        """Retourne la liste des logos disponibles"""
        return list(self.logos.keys())
    
    def set_application_icon(self, app, logo_name: str = "BARREL v4 sans"):
        """Définit l'icône de l'application"""
        icon = self.get_logo(logo_name)
        if not icon.isNull():
            app.setWindowIcon(icon)
    
    def create_splash_screen(self, logo_name: str = "BARREL v4 sans", 
                           app_name: str = "Barrel MCD") -> QWidget:
        """Crée un écran de démarrage"""
        splash_widget = QWidget()
        splash_widget.setStyleSheet("""
            QWidget {
                background-color: #2b2b2b;
                border: 2px solid #3c3c3c;
                border-radius: 10px;
            }
        """)
        
        layout = QVBoxLayout()
        
        # Logo plus grand pour le splash
        logo_label = QLabel()
        logo_pixmap = self.get_logo_pixmap(logo_name, (200, 200))
        logo_label.setPixmap(logo_pixmap)
        logo_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(logo_label)
        
        # Nom de l'application
        name_label = QLabel(app_name)
        name_label.setAlignment(Qt.AlignCenter)
        name_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #ffffff;
                margin-top: 20px;
            }
        """)
        layout.addWidget(name_label)
        
        # Version
        version_label = QLabel("Version 1.0")
        version_label.setAlignment(Qt.AlignCenter)
        version_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: #cccccc;
                margin-top: 10px;
            }
        """)
        layout.addWidget(version_label)
        
        splash_widget.setLayout(layout)
        return splash_widget
