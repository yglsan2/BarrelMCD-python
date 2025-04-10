from PyQt5.QtWidgets import QDialog, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QPainter, QColor, QPen, QFont

from .responsive_styles import ResponsiveStyles

class MobileDialog(QDialog):
    """Boîte de dialogue optimisée pour mobile"""
    
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        
        # Configuration de base
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Widget conteneur
        self.container = QWidget()
        self.setCentralWidget(self.container)
        
        # Layout principal
        self.layout = QVBoxLayout(self.container)
        self.layout.setContentsMargins(16, 16, 16, 16)
        self.layout.setSpacing(16)
        
        # En-tête
        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        # Titre
        self.title = QLabel(title)
        self.title.setStyleSheet("color: #333; font-weight: bold;")
        header_layout.addWidget(self.title)
        
        # Bouton fermer
        self.close_button = QPushButton("✕")
        self.close_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                padding: 8px;
                color: #666;
            }
            QPushButton:hover {
                color: #333;
            }
        """)
        self.close_button.clicked.connect(self.reject)
        header_layout.addWidget(self.close_button)
        
        self.layout.addWidget(header)
        
        # Contenu
        self.content = QWidget()
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.layout.addWidget(self.content)
        
        # Boutons
        self.buttons = QWidget()
        self.buttons_layout = QHBoxLayout(self.buttons)
        self.buttons_layout.setContentsMargins(0, 0, 0, 0)
        self.buttons_layout.setSpacing(8)
        self.layout.addWidget(self.buttons)
        
        # Style
        self.setStyleSheet(ResponsiveStyles.get_dialog_style(1.0))
        
    def add_widget(self, widget: QWidget):
        """Ajoute un widget au contenu"""
        self.content_layout.addWidget(widget)
        
    def add_button(self, text: str, callback=None, role: str = "accept"):
        """Ajoute un bouton"""
        button = QPushButton(text)
        button.setStyleSheet("""
            QPushButton {
                background-color: #007AFF;
                color: white;
                border: none;
                padding: 12px;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        if callback:
            button.clicked.connect(callback)
        if role == "accept":
            button.clicked.connect(self.accept)
        elif role == "reject":
            button.clicked.connect(self.reject)
        self.buttons_layout.addWidget(button)
        
    def paintEvent(self, event):
        """Dessine la boîte de dialogue"""
        super().paintEvent(event)
        
        # Ajouter une ombre et un fond
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Fond blanc avec coins arrondis
        painter.setBrush(QColor(255, 255, 255))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(self.rect(), 12, 12)
        
        # Ombre portée
        painter.setPen(QPen(QColor(0, 0, 0, 30), 1))
        painter.drawRoundedRect(self.rect().adjusted(0, 0, -1, -1), 12, 12)
        
    def resizeEvent(self, event):
        """Gère le redimensionnement"""
        super().resizeEvent(event)
        
        # Ajuster la taille des polices
        font_size = ResponsiveStyles.get_font_size(1.0)
        for widget in [self.title, self.close_button]:
            font = widget.font()
            font.setPointSize(font_size)
            widget.setFont(font)
            
    def showEvent(self, event):
        """Gère l'affichage de la boîte de dialogue"""
        super().showEvent(event)
        
        # Ajuster la taille en fonction du contenu
        self.adjustSize()
        
        # Centrer la boîte de dialogue par rapport au parent
        if self.parent():
            parent_rect = self.parent().rect()
            x = parent_rect.center().x() - self.width() // 2
            y = parent_rect.center().y() - self.height() // 2
            self.move(x, y) 