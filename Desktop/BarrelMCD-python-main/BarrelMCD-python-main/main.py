#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from PyQt5.QtWidgets import QApplication
from views.main_window import MainWindow

def main():
    """Point d'entrée principal de l'application."""
    app = QApplication(sys.argv)
    
    # Appliquer le style moderne
    app.setStyle("Fusion")
    
    # Créer et afficher la fenêtre principale
    window = MainWindow()
    window.show()
    
    # Lancer la boucle d'événements
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
