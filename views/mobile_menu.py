from PyQt6.QtWidgets import QMenu, QWidget, QVBoxLayout, QPushButton, QLabel
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QPainter, QColor, QPen, QFont

from .responsive_styles import ResponsiveStyles

class MobileMenu(QMenu):
    """Menu optimisé pour mobile"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Configuration de base
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Popup)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Widget conteneur
        self.container = QWidget()
        self.setCentralWidget(self.container)
        
        # Layout vertical
        self.layout = QVBoxLayout(self.container)
        self.layout.setContentsMargins(16, 16, 16, 16)
        self.layout.setSpacing(8)
        
        # Titre
        self.title = QLabel("Menu")
        self.title.setStyleSheet("color: #333; font-weight: bold;")
        self.layout.addWidget(self.title)
        
        # Séparateur
        self.layout.addWidget(QLabel(""))
        
        # Style
        self.setStyleSheet(ResponsiveStyles.get_menu_style(1.0))
        
    def add_action(self, text: str, icon: str = None, callback=None):
        """Ajoute une action au menu"""
        button = QPushButton(text)
        if icon:
            button.setText(f"{icon} {text}")
        button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                padding: 12px;
                text-align: left;
                color: #333;
            }
            QPushButton:hover {
                background-color: #f0f0f0;
            }
        """)
        if callback:
            button.clicked.connect(callback)
        self.layout.addWidget(button)
        
    def add_separator(self):
        """Ajoute un séparateur"""
        self.layout.addWidget(QLabel(""))
        
    def paintEvent(self, event):
        """Dessine le menu"""
        super().paintEvent(event)
        
        # Ajouter une ombre et un fond
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Fond blanc avec coins arrondis
        painter.setBrush(QColor(255, 255, 255))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(self.rect(), 8, 8)
        
        # Ombre portée
        painter.setPen(QPen(QColor(0, 0, 0, 30), 1))
        painter.drawRoundedRect(self.rect().adjusted(0, 0, -1, -1), 8, 8)
        
    def resizeEvent(self, event):
        """Gère le redimensionnement"""
        super().resizeEvent(event)
        
        # Ajuster la taille des polices
        font_size = ResponsiveStyles.get_font_size(1.0)
        for i in range(self.layout.count()):
            widget = self.layout.itemAt(i).widget()
            if isinstance(widget, (QLabel, QPushButton)):
                font = widget.font()
                font.setPointSize(font_size)
                widget.setFont(font)
                
    def showEvent(self, event):
        """Gère l'affichage du menu"""
        super().showEvent(event)
        
        # Ajuster la taille en fonction du contenu
        self.adjustSize()
        
        # Centrer le menu par rapport au parent
        if self.parent():
            parent_rect = self.parent().rect()
            x = parent_rect.center().x() - self.width() // 2
            y = parent_rect.center().y() - self.height() // 2
            self.move(x, y) 