import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from views import MobileWindow

def main():
    """Point d'entrée de l'application"""
    app = QApplication(sys.argv)
    
    # Configuration de l'application
    app.setApplicationName("Barrel MCD")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("Barrel")
    app.setOrganizationDomain("barrel-mcd.com")
    
    # Création de la fenêtre principale
    window = MobileWindow()
    window.show()
    
    # Lancement de l'application
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
