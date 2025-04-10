#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import platform
import traceback
from pathlib import Path
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from views.main_window import MainWindow


def setup_environment():
    """Configure l'environnement selon le système d'exploitation"""
    try:
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

        # Configurer le style de l'application
        if platform.system() == 'Windows':
            os.environ['QT_QPA_PLATFORM'] = 'windows'
        elif platform.system() == 'Darwin':  # macOS
            os.environ['QT_QPA_PLATFORM'] = 'cocoa'
        else:  # Linux et autres
            os.environ['QT_QPA_PLATFORM'] = 'xcb'

        return True
    except Exception as e:
        print(f"Erreur lors de la configuration de l'environnement: {str(e)}")
        traceback.print_exc()
        return False


def main():
    """Point d'entrée principal de l'application"""
    try:
        # Configuration de l'environnement
        if not setup_environment():
            sys.exit(1)

        # Création de l'application Qt
        app = QApplication(sys.argv)

        # Configuration des attributs de l'application
        app.setAttribute(Qt.AA_UseHighDpiPixmaps)
        app.setAttribute(Qt.AA_EnableHighDpiScaling)

        # Création et affichage de la fenêtre principale
        window = MainWindow()
        window.show()

        # Exécution de la boucle d'événements
        return app.exec_()

    except Exception as e:
        print(f"Erreur critique: {str(e)}")
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
