#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import platform
from pathlib import Path
from PyQt5.QtWidgets import QApplication
from views.main_window import MainWindow

def setup_environment():
    """Configure l'environnement selon le système d'exploitation"""
    # Définir le répertoire de l'application
    if getattr(sys, 'frozen', False):
        # Si l'application est packagée (exe, app, etc.)
        app_dir = Path(sys._MEIPASS)
    else:
        # Si l'application est en développement
        app_dir = Path(__file__).parent

    # Créer les répertoires nécessaires
    data_dir = app_dir / 'data'
    logs_dir = app_dir / 'logs'
    temp_dir = app_dir / 'temp'

    for directory in [data_dir, logs_dir, temp_dir]:
        directory.mkdir(exist_ok=True)

    # Configurer les variables d'environnement
    os.environ['BARREL_MCD_HOME'] = str(app_dir)
    os.environ['BARREL_MCD_DATA'] = str(data_dir)
    os.environ['BARREL_MCD_LOGS'] = str(logs_dir)
    os.environ['BARREL_MCD_TEMP'] = str(temp_dir)

    # Configurer le séparateur de chemin selon l'OS
    os.environ['BARREL_MCD_PATH_SEP'] = os.path.sep

    return {
        'os': platform.system(),
        'os_version': platform.version(),
        'python_version': platform.python_version(),
        'app_dir': app_dir,
        'data_dir': data_dir,
        'logs_dir': logs_dir,
        'temp_dir': temp_dir
    }

def main():
    """Point d'entrée principal de l'application."""
    # Configuration de l'environnement
    env = setup_environment()
    
    # Création de l'application
    app = QApplication(sys.argv)
    
    # Appliquer le style moderne
    app.setStyle("Fusion")
    
    # Créer et afficher la fenêtre principale
    window = MainWindow()
    window.show()
    
    # Lancer la boucle d'événements
    sys.exit(app.exec_())

if __name__ == '__main__':
    main() 