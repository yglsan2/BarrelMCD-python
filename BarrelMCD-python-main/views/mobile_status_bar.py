from PyQt6.QtWidgets import QStatusBar, QWidget, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QColor, QPen

from .responsive_styles import ResponsiveStyles

class MobileStatusBar(QStatusBar):
    """Barre d'état optimisée pour mobile"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Configuration de base
        self.setFixedHeight(ResponsiveStyles.get_status_bar_height(1.0))
        
        # Widget conteneur
        self.container = QWidget()
        self.setCentralWidget(self.container)
        
        # Layout horizontal
        self.layout = QHBoxLayout(self.container)
        self.layout.setContentsMargins(8, 4, 8, 4)
        self.layout.setSpacing(8)
        
        # Labels d'état
        self.labels = {}
        self.setup_labels()
        
        # Style
        self.setStyleSheet(ResponsiveStyles.get_status_bar_style(1.0))
        
    def setup_labels(self):
        """Configure les labels de la barre d'état"""
        # Label de mode
        self.labels["mode"] = QLabel("Mode: Édition")
        self.labels["mode"].setStyleSheet("color: #666;")
        self.layout.addWidget(self.labels["mode"])
        
        # Label de zoom
        self.labels["zoom"] = QLabel("Zoom: 100%")
        self.labels["zoom"].setStyleSheet("color: #666;")
        self.layout.addWidget(self.labels["zoom"])
        
        # Label de grille
        self.labels["grid"] = QLabel("Grille: Activée")
        self.labels["grid"].setStyleSheet("color: #666;")
        self.layout.addWidget(self.labels["grid"])
        
        # Label de sauvegarde
        self.labels["save"] = QLabel("💾")
        self.labels["save"].setStyleSheet("color: #666;")
        self.layout.addWidget(self.labels["save"])
        
    def set_mode(self, mode: str):
        """Met à jour le mode affiché"""
        self.labels["mode"].setText(f"Mode: {mode}")
        
    def set_zoom(self, zoom: int):
        """Met à jour le niveau de zoom affiché"""
        self.labels["zoom"].setText(f"Zoom: {zoom}%")
        
    def set_grid(self, enabled: bool):
        """Met à jour l'état de la grille"""
        self.labels["grid"].setText(f"Grille: {'Activée' if enabled else 'Désactivée'}")
        
    def set_save_status(self, status: str):
        """Met à jour le statut de sauvegarde"""
        if status == "saving":
            self.labels["save"].setText("💾")
        elif status == "saved":
            self.labels["save"].setText("✓")
        elif status == "error":
            self.labels["save"].setText("❌")
            
    def paintEvent(self, event):
        """Dessine la barre d'état"""
        super().paintEvent(event)
        
        # Ajouter une ligne de séparation
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(QPen(QColor(200, 200, 200), 1))
        painter.drawLine(0, 0, self.width(), 0)
        
    def resizeEvent(self, event):
        """Gère le redimensionnement"""
        super().resizeEvent(event)
        
        # Ajuster la taille des polices
        font_size = ResponsiveStyles.get_font_size(1.0)
        for label in self.labels.values():
            font = label.font()
            font.setPointSize(font_size)
            label.setFont(font) 