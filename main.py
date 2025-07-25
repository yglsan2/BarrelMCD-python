#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Application principale BarrelMCD
"""

import os
import sys

# Configuration pour éviter les warnings Wayland
os.environ['QT_QPA_PLATFORM'] = 'xcb'

# Ajouter le répertoire parent au path pour les imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon

from views.main_window import MainWindow
from views.dark_theme import DarkTheme

def main():
    """Point d'entrée principal de l'application"""
    # Créer l'application Qt
    app = QApplication(sys.argv)
    
    # Configuration de l'application
    app.setApplicationName("BarrelMCD")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("BarrelMCD")
    
    # Appliquer le thème sombre
    DarkTheme.apply_dark_theme(app)
    
    # Créer et afficher la fenêtre principale
    window = MainWindow()
    window.show()
    
    # Lancer l'application
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
