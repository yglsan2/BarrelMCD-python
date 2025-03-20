from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QPainter, QColor, QPen

from .mobile_toolbar import MobileToolBar
from .mobile_status_bar import MobileStatusBar
from .mobile_canvas import MobileCanvas
from .mobile_menu import MobileMenu
from .mobile_dialog import MobileDialog
from .responsive_styles import ResponsiveStyles

class MobileWindow(QMainWindow):
    """Fenêtre principale optimisée pour mobile"""
    
    def __init__(self):
        super().__init__()
        
        # Configuration de base
        self.setWindowTitle("Barrel MCD")
        self.setMinimumSize(ResponsiveStyles.get_window_size(1.0))
        
        # Widget central
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # Layout principal
        self.layout = QVBoxLayout(self.central_widget)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        # Barre d'outils
        self.toolbar = MobileToolBar(self)
        self.addToolBar(self.toolbar)
        
        # Canvas
        self.canvas = MobileCanvas(self)
        self.layout.addWidget(self.canvas)
        
        # Barre d'état
        self.statusbar = MobileStatusBar(self)
        self.setStatusBar(self.statusbar)
        
        # Menu
        self.menu = MobileMenu(self)
        
        # Connexions
        self.setup_connections()
        
        # Style
        self.setStyleSheet(ResponsiveStyles.get_window_style(1.0))
        
    def setup_connections(self):
        """Configure les connexions"""
        # Menu
        self.toolbar.get_button("menu").clicked.connect(self.show_menu)
        
        # Nouveau
        self.toolbar.get_button("new").clicked.connect(self.new_diagram)
        
        # Ouvrir
        self.toolbar.get_button("open").clicked.connect(self.open_diagram)
        
        # Enregistrer
        self.toolbar.get_button("save").clicked.connect(self.save_diagram)
        
        # Zoom
        self.toolbar.get_button("zoom").clicked.connect(self.toggle_zoom)
        
        # Grille
        self.toolbar.get_button("grid").clicked.connect(self.toggle_grid)
        
        # Aide
        self.toolbar.get_button("help").clicked.connect(self.show_help)
        
    def show_menu(self):
        """Affiche le menu"""
        self.menu.clear()
        self.menu.add_action("Nouveau diagramme", "📄", self.new_diagram)
        self.menu.add_action("Ouvrir...", "📂", self.open_diagram)
        self.menu.add_action("Enregistrer", "💾", self.save_diagram)
        self.menu.add_action("Enregistrer sous...", "💾", self.save_diagram_as)
        self.menu.add_separator()
        self.menu.add_action("Paramètres", "⚙️", self.show_settings)
        self.menu.add_action("À propos", "ℹ️", self.show_about)
        self.menu.exec(self.toolbar.get_button("menu").mapToGlobal(QPointF(0, 0)))
        
    def new_diagram(self):
        """Crée un nouveau diagramme"""
        dialog = MobileDialog("Nouveau diagramme", self)
        dialog.add_widget(QLabel("Voulez-vous créer un nouveau diagramme ?"))
        dialog.add_button("Annuler", role="reject")
        dialog.add_button("Créer", role="accept")
        if dialog.exec():
            self.canvas.clear()
            self.statusbar.set_mode("Édition")
            
    def open_diagram(self):
        """Ouvre un diagramme"""
        dialog = MobileDialog("Ouvrir un diagramme", self)
        dialog.add_widget(QLabel("Sélectionnez un fichier à ouvrir"))
        dialog.add_button("Annuler", role="reject")
        dialog.add_button("Ouvrir", role="accept")
        if dialog.exec():
            # TODO: Implémenter l'ouverture de fichier
            pass
            
    def save_diagram(self):
        """Enregistre le diagramme"""
        self.statusbar.set_save_status("saving")
        # TODO: Implémenter la sauvegarde
        self.statusbar.set_save_status("saved")
        
    def save_diagram_as(self):
        """Enregistre le diagramme sous un nouveau nom"""
        dialog = MobileDialog("Enregistrer sous...", self)
        dialog.add_widget(QLabel("Choisissez un nom pour le fichier"))
        dialog.add_button("Annuler", role="reject")
        dialog.add_button("Enregistrer", role="accept")
        if dialog.exec():
            # TODO: Implémenter la sauvegarde sous
            pass
            
    def toggle_zoom(self):
        """Bascule le zoom"""
        if self.canvas.zoom_factor == 1.0:
            self.canvas.zoom(2.0)
            self.toolbar.get_button("zoom").setText("🔍-")
        else:
            self.canvas.zoom(0.5)
            self.toolbar.get_button("zoom").setText("🔍+")
            
    def toggle_grid(self):
        """Bascule l'affichage de la grille"""
        self.canvas.set_grid_visible(not self.canvas.show_grid)
        self.toolbar.get_button("grid").setText("📏" if self.canvas.show_grid else "📏-")
        
    def show_help(self):
        """Affiche l'aide"""
        dialog = MobileDialog("Aide", self)
        dialog.add_widget(QLabel("Comment utiliser Barrel MCD"))
        dialog.add_button("Fermer", role="accept")
        dialog.exec()
        
    def show_settings(self):
        """Affiche les paramètres"""
        dialog = MobileDialog("Paramètres", self)
        dialog.add_widget(QLabel("Configuration de l'application"))
        dialog.add_button("Annuler", role="reject")
        dialog.add_button("Enregistrer", role="accept")
        dialog.exec()
        
    def show_about(self):
        """Affiche la boîte À propos"""
        dialog = MobileDialog("À propos", self)
        dialog.add_widget(QLabel("Barrel MCD v1.0"))
        dialog.add_button("Fermer", role="accept")
        dialog.exec()
        
    def paintEvent(self, event):
        """Dessine la fenêtre"""
        super().paintEvent(event)
        
        # Ajouter une ombre portée
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(QPen(QColor(0, 0, 0, 30), 1))
        painter.drawRect(self.rect().adjusted(0, 0, -1, -1))
        
    def resizeEvent(self, event):
        """Gère le redimensionnement"""
        super().resizeEvent(event)
        
        # Ajuster la taille des widgets
        self.toolbar.setFixedHeight(ResponsiveStyles.get_toolbar_height(1.0))
        self.statusbar.setFixedHeight(ResponsiveStyles.get_status_bar_height(1.0)) 