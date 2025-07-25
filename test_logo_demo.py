#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Démonstration des différentes approches d'affichage du logo
"""

import sys
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QLabel, QComboBox
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from views.interactive_canvas import InteractiveCanvas

class LogoDemoWindow(QMainWindow):
    """Fenêtre de démonstration pour tester les logos"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("BarrelMCD - Démonstration Logo")
        self.setGeometry(100, 100, 1200, 800)
        
        # Configuration du logo dans la barre de titre
        logo_path = os.path.join(os.path.dirname(__file__), "docs", "logos", "barrel_icon.png")
        if os.path.exists(logo_path):
            self.setWindowIcon(QIcon(logo_path))
            print(f"Logo chargé: {logo_path}")
        else:
            print(f"Logo non trouvé: {logo_path}")
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        layout = QVBoxLayout(central_widget)
        
        # Canvas
        self.canvas = InteractiveCanvas()
        layout.addWidget(self.canvas)
        
        # Panneau de contrôle
        control_panel = self.create_control_panel()
        layout.addWidget(control_panel)
        
        # Créer quelques éléments de test
        self.create_test_elements()
        
    def create_control_panel(self):
        """Crée le panneau de contrôle pour le logo"""
        panel = QWidget()
        panel.setMaximumHeight(100)
        layout = QHBoxLayout(panel)
        
        # Bouton pour basculer le logo
        toggle_btn = QPushButton("👁️ Afficher/Masquer Logo")
        toggle_btn.clicked.connect(self.canvas.toggle_logo)
        layout.addWidget(toggle_btn)
        
        # Sélecteur de position
        layout.addWidget(QLabel("Position:"))
        position_combo = QComboBox()
        positions = [
            ("top_left", "↖️ Coin supérieur gauche"),
            ("top_right", "↗️ Coin supérieur droit"),
            ("bottom_left", "↙️ Coin inférieur gauche"),
            ("bottom_right", "↘️ Coin inférieur droit"),
            ("center", "🎯 Centre")
        ]
        for pos_key, pos_name in positions:
            position_combo.addItem(pos_name, pos_key)
        position_combo.currentTextChanged.connect(self.on_position_changed)
        layout.addWidget(position_combo)
        
        # Sélecteur de taille
        layout.addWidget(QLabel("Taille:"))
        size_combo = QComboBox()
        sizes = [("40", "Petit"), ("80", "Moyen"), ("120", "Grand"), ("160", "Très grand")]
        for size_key, size_name in sizes:
            size_combo.addItem(size_name, size_key)
        size_combo.currentTextChanged.connect(self.on_size_changed)
        layout.addWidget(size_combo)
        
        # Bouton pour changer le style du logo
        style_btn = QPushButton("🎨 Changer Style")
        style_btn.clicked.connect(self.change_logo_style)
        layout.addWidget(style_btn)
        
        layout.addStretch()
        return panel
        
    def on_position_changed(self, text):
        """Change la position du logo"""
        position_map = {
            "↖️ Coin supérieur gauche": "top_left",
            "↗️ Coin supérieur droit": "top_right",
            "↙️ Coin inférieur gauche": "bottom_left",
            "↘️ Coin inférieur droit": "bottom_right",
            "🎯 Centre": "center"
        }
        if text in position_map:
            self.canvas.set_logo_position(position_map[text])
            
    def on_size_changed(self, text):
        """Change la taille du logo"""
        size_map = {
            "Petit": 40,
            "Moyen": 80,
            "Grand": 120,
            "Très grand": 160
        }
        if text in size_map:
            self.canvas.set_logo_size(size_map[text])
            
    def change_logo_style(self):
        """Change le style du logo (décommente différentes approches)"""
        # Cette méthode permet de basculer entre les différentes approches
        # en modifiant le code dans create_logo_item()
        print("Pour changer le style, modifiez la méthode create_logo_item() dans interactive_canvas.py")
        print("Décommentez l'une des lignes suivantes:")
        print("- self.logo_item = self.create_svg_logo()")
        print("- self.logo_item = self.create_geometric_logo()")
        
    def create_test_elements(self):
        """Crée quelques éléments de test sur le canvas"""
        # Créer quelques entités de test
        from models.entity import Entity
        from PyQt5.QtCore import QPointF
        
        entity1 = Entity("Client", QPointF(-100, -50))
        entity2 = Entity("Commande", QPointF(100, -50))
        entity3 = Entity("Produit", QPointF(0, 100))
        
        self.canvas.scene.addItem(entity1)
        self.canvas.scene.addItem(entity2)
        self.canvas.scene.addItem(entity3)

def main():
    """Fonction principale"""
    app = QApplication(sys.argv)
    
    # Appliquer un style sombre
    app.setStyle("Fusion")
    
    # Créer et afficher la fenêtre
    window = LogoDemoWindow()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main() 