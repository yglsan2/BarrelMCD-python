from PyQt6.QtWidgets import QPushButton, QSizePolicy
from PyQt6.QtCore import Qt, QSize, QPoint
from PyQt6.QtGui import QPainter, QColor, QPainterPath, QFont

class TouchButton(QPushButton):
    """Bouton tactile optimisé pour mobile"""
    
    def __init__(self, text: str = "", parent=None):
        super().__init__(text, parent)
        
        # Configuration de base
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.setMinimumSize(44, 44)  # Taille minimale recommandée pour le tactile
        
        # Style
        self.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                padding: 8px;
            }
        """)
        
        # État
        self.is_pressed = False
        self.ripple_center = QPoint()
        self.ripple_radius = 0
        self.ripple_opacity = 0
        
        # Animation
        self.ripple_animation = None
        
    def paintEvent(self, event):
        """Dessine le bouton avec effet de ripple"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Dessiner le fond
        if self.is_pressed:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(0, 0, 0, 30))
            painter.drawRoundedRect(self.rect(), 8, 8)
            
        # Dessiner l'effet de ripple
        if self.ripple_radius > 0:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(0, 0, 0, int(30 * self.ripple_opacity)))
            painter.drawEllipse(self.ripple_center, self.ripple_radius, self.ripple_radius)
            
        # Dessiner le texte
        painter.setPen(self.palette().text().color())
        painter.setFont(self.font())
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self.text())
        
    def mousePressEvent(self, event):
        """Gère l'appui sur le bouton"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_pressed = True
            self.ripple_center = event.position().toPoint()
            self.ripple_radius = 0
            self.ripple_opacity = 1
            self.update()
            
    def mouseReleaseEvent(self, event):
        """Gère le relâchement du bouton"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_pressed = False
            self.update()
            
    def mouseMoveEvent(self, event):
        """Gère le déplacement sur le bouton"""
        if self.is_pressed:
            # Calculer la distance depuis le point d'appui
            distance = (event.position().toPoint() - self.ripple_center).manhattanLength()
            if distance > 20:  # Seuil de tolérance
                self.is_pressed = False
                self.update()
                
    def enterEvent(self, event):
        """Gère l'entrée de la souris"""
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
    def leaveEvent(self, event):
        """Gère la sortie de la souris"""
        self.setCursor(Qt.CursorShape.ArrowCursor)
        
    def resizeEvent(self, event):
        """Gère le redimensionnement"""
        super().resizeEvent(event)
        # Ajuster la taille du texte si nécessaire
        if self.text():
            font = self.font()
            metrics = self.fontMetrics()
            text_width = metrics.horizontalAdvance(self.text())
            if text_width > self.width() - 16:  # 8px de padding de chaque côté
                # Réduire la taille de la police
                while text_width > self.width() - 16 and font.pointSize() > 8:
                    font.setPointSize(font.pointSize() - 1)
                    metrics = QFontMetrics(font)
                    text_width = metrics.horizontalAdvance(self.text())
                self.setFont(font) 