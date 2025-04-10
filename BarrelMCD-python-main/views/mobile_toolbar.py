from PyQt5.QtWidgets import QToolBar, QWidget, QHBoxLayout, QSizePolicy
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon, QPainter, QColor, QPen

from .touch_button import TouchButton
from .responsive_styles import ResponsiveStyles

class MobileToolBar(QToolBar):
    """Barre d'outils optimisée pour mobile"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Configuration de base
        self.setMovable(False)
        self.setFloatable(False)
        self.setIconSize(QSize(24, 24))
        
        # Widget conteneur
        self.container = QWidget()
        self.setCentralWidget(self.container)
        
        # Layout horizontal
        self.layout = QHBoxLayout(self.container)
        self.layout.setContentsMargins(8, 8, 8, 8)
        self.layout.setSpacing(8)
        
        # Boutons principaux
        self.buttons = {}
        self.setup_buttons()
        
        # Style
        self.setStyleSheet(ResponsiveStyles.get_toolbar_style(1.0))
        
    def setup_buttons(self):
        """Configure les boutons de la barre d'outils"""
        # Bouton Menu
        self.buttons["menu"] = TouchButton("☰")
        self.buttons["menu"].setToolTip("Menu")
        self.layout.addWidget(self.buttons["menu"])
        
        # Bouton Nouveau
        self.buttons["new"] = TouchButton("+")
        self.buttons["new"].setToolTip("Nouveau")
        self.layout.addWidget(self.buttons["new"])
        
        # Bouton Ouvrir
        self.buttons["open"] = TouchButton("📂")
        self.buttons["open"].setToolTip("Ouvrir")
        self.layout.addWidget(self.buttons["open"])
        
        # Bouton Enregistrer
        self.buttons["save"] = TouchButton("💾")
        self.buttons["save"].setToolTip("Enregistrer")
        self.layout.addWidget(self.buttons["save"])
        
        # Espaceur flexible
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.layout.addWidget(spacer)
        
        # Bouton Zoom
        self.buttons["zoom"] = TouchButton("🔍")
        self.buttons["zoom"].setToolTip("Zoom")
        self.layout.addWidget(self.buttons["zoom"])
        
        # Bouton Grille
        self.buttons["grid"] = TouchButton("📏")
        self.buttons["grid"].setToolTip("Grille")
        self.layout.addWidget(self.buttons["grid"])
        
        # Bouton Aide
        self.buttons["help"] = TouchButton("❓")
        self.buttons["help"].setToolTip("Aide")
        self.layout.addWidget(self.buttons["help"])
        
    def add_action(self, text: str, icon: str, callback=None) -> TouchButton:
        """Ajoute une action à la barre d'outils"""
        button = TouchButton(icon)
        button.setToolTip(text)
        if callback:
            button.clicked.connect(callback)
        self.layout.insertWidget(self.layout.count() - 4, button)  # Insère avant l'espaceur
        return button
        
    def remove_action(self, button: TouchButton):
        """Supprime une action de la barre d'outils"""
        self.layout.removeWidget(button)
        button.deleteLater()
        
    def paintEvent(self, event):
        """Dessine la barre d'outils"""
        super().paintEvent(event)
        
        # Ajouter une ombre portée
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Dessiner une ligne de séparation
        painter.setPen(QPen(QColor(200, 200, 200), 1))
        painter.drawLine(0, self.height() - 1, self.width(), self.height() - 1)
        
    def resizeEvent(self, event):
        """Gère le redimensionnement"""
        super().resizeEvent(event)
        
        # Ajuster la taille des boutons
        button_size = ResponsiveStyles.get_button_size(1.0)
        for button in self.buttons.values():
            button.setFixedSize(button_size)
            
    def get_button(self, name: str) -> TouchButton:
        """Retourne un bouton par son nom"""
        return self.buttons.get(name) 