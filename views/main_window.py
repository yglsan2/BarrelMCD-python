import os
import time
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QFileDialog, QMessageBox, QLabel, QGraphicsView, QGraphicsScene, QInputDialog, QTextEdit, QDialog,
    QToolBar, QAction, QDockWidget, QListWidget, QSplitter, QFrame, QSizePolicy, QScrollArea, QMenu
)
from PyQt5.QtCore import Qt, QSize, QTimer
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QKeySequence
from PyQt5.QtSvg import QSvgRenderer
from PyQt5.QtPrintSupport import QPrinter
from PyQt5.QtSvg import QSvgWidget

from views.data_analyzer import DataAnalyzer
from views.model_converter import ModelConverter
from views.mcd_drawer import MCDDrawer
from views.sql_inspector import SQLInspector
from views.interactive_canvas import InteractiveCanvas
from views.markdown_import_dialog import MarkdownImportDialog

# Cache global pour les icônes SVG
_icon_cache = {}

def svg_to_icon(svg_path, size=24):
    """Convertit un fichier SVG en icône QIcon avec cache"""
    if svg_path in _icon_cache:
        return _icon_cache[svg_path]
    
    if os.path.exists(svg_path):
        try:
            renderer = QSvgRenderer(svg_path)
            if renderer.isValid():
                pixmap = QPixmap(size, size)
                pixmap.fill(Qt.transparent)
                painter = QPainter(pixmap)
                renderer.render(painter)
                painter.end()
                icon = QIcon(pixmap)
                _icon_cache[svg_path] = icon
                return icon
            else:
                print(f"SVG invalide: {svg_path}")
        except Exception as e:
            print(f"Erreur lors du chargement de l'icône SVG {svg_path}: {e}")
    else:
        print(f"Fichier SVG non trouvé: {svg_path}")
    return None

class MainWindow(QMainWindow):
    """Fenêtre principale de l'application BarrelMCD."""
    
    def __init__(self):
        super().__init__()
        
        # Configuration de base
        self.setWindowTitle("BarrelMCD - Modélisation Conceptuelle de Données")
        
        # Obtenir la taille de l'écran
        screen = self.screen().geometry()
        screen_width = screen.width()
        screen_height = screen.height()
        
        # Calculer une taille par défaut adaptée à l'écran
        default_width = min(1200, int(screen_width * 0.8))
        default_height = min(800, int(screen_height * 0.8))
        
        self.setMinimumSize(800, 600)
        self.resize(default_width, default_height)
        
        # Centrer la fenêtre
        x = (screen_width - default_width) // 2
        y = (screen_height - default_height) // 2
        self.move(x, y)
        
        # Définir l'icône de la fenêtre principale
        icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'docs/logos/barrel_icon.ico')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        # Initialiser les variables
        self.current_data = None
        self.current_format = None
        self.current_mcd = None
        self.log_messages = []
        
        # Variables pour la gestion de la fenêtre
        self.previous_geometry = None
        self.is_fullscreen = False
        self.drag_start_pos = None
        self.is_dragging = False
        
        # Timer pour détecter le glissement vers le haut
        self.drag_timer = QTimer()
        self.drag_timer.setSingleShot(True)
        self.drag_timer.timeout.connect(self.check_fullscreen_trigger)
        
        # Composants lourds - initialisation différée
        self.data_analyzer = None
        self.model_converter = None
        self.mcd_drawer = None
        self.sql_inspector = None
        
        # Canvas interactif
        self.canvas = InteractiveCanvas()
        
        # Configurer l'interface
        self._setup_ui()
        self._setup_toolbar()
        self._setup_docks()
        
        # Connexion des signaux
        self._connect_signals()
        
        # Configuration du menu principal
        self._setup_menu()
        
    def _setup_ui(self):
        """Configure l'interface utilisateur responsive."""
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal avec flex
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)
        
        # Logo principal en haut à gauche
        logo_widget = QWidget()
        logo_layout = QHBoxLayout(logo_widget)
        logo_layout.setContentsMargins(10, 5, 10, 5)
        logo_layout.setSpacing(5)  # Réduire l'espacement entre logo et texte
        
        # Logo BarrelMCD (plus petit et sans coins blancs)
        logo_label = QLabel()
        logo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'docs/logos/barrel_icon_512.png')
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path)
            # Créer un pixmap transparent plus petit (20x20)
            transparent_pixmap = QPixmap(20, 20)
            transparent_pixmap.fill(Qt.transparent)
            painter = QPainter(transparent_pixmap)
            scaled_pixmap = pixmap.scaled(18, 18, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            # Centrer le logo dans le pixmap transparent
            x = (20 - scaled_pixmap.width()) // 2
            y = (20 - scaled_pixmap.height()) // 2
            painter.drawPixmap(x, y, scaled_pixmap)
            painter.end()
            logo_label.setPixmap(transparent_pixmap)
        logo_label.setStyleSheet("QLabel { background-color: transparent; border: none; }")
        logo_label.setAttribute(Qt.WA_TranslucentBackground, True)
        logo_layout.addWidget(logo_label)
        
        # Créer un layout horizontal pour séparer "Barrel" et "MCD"
        title_layout = QHBoxLayout()
        title_layout.setSpacing(0)
        
        # "Barrel" en couleur plus claire
        barrel_label = QLabel("Barrel")
        barrel_label.setStyleSheet("""
            QLabel {
                color: #4e4e5f;
                font-size: 16px;
                font-weight: bold;
                background-color: transparent;
                border: none;
            }
        """)
        title_layout.addWidget(barrel_label)
        
        # "MCD" en bleu foncé
        mcd_label = QLabel("MCD")
        mcd_label.setStyleSheet("""
            QLabel {
                color: #2c2c44;
                font-size: 16px;
                font-weight: bold;
                background-color: transparent;
                border: none;
            }
        """)
        title_layout.addWidget(mcd_label)
        
        title_layout.addStretch()
        logo_layout.addLayout(title_layout)
        
        logo_layout.addStretch()
        main_layout.addWidget(logo_widget)
        
        # Zone de dessin principale avec flex
        canvas_container = QWidget()
        canvas_layout = QVBoxLayout(canvas_container)
        canvas_layout.setContentsMargins(5, 5, 5, 5)
        
        # Canvas avec taille flexible et responsive
        self.canvas.setMinimumSize(600, 400)
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        canvas_layout.addWidget(self.canvas)
        
        # Ajout du canvas dans une zone scrollable avec barres automatiques
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(canvas_container)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #1e1e1e;
            }
            QScrollBar:vertical {
                background-color: #2d2d30;
                width: 16px;
                border-radius: 8px;
                margin: 2px;
            }
            QScrollBar::handle:vertical {
                background-color: #4e4e52;
                border-radius: 8px;
                min-height: 30px;
                margin: 2px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #5e5e62;
            }
            QScrollBar::handle:vertical:pressed {
                background-color: #6e6e72;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
                background-color: transparent;
            }
            QScrollBar:horizontal {
                background-color: #2d2d30;
                height: 16px;
                border-radius: 8px;
                margin: 2px;
            }
            QScrollBar::handle:horizontal {
                background-color: #4e4e52;
                border-radius: 8px;
                min-width: 30px;
                margin: 2px;
            }
            QScrollBar::handle:horizontal:hover {
                background-color: #5e5e62;
            }
            QScrollBar::handle:horizontal:pressed {
                background-color: #6e6e72;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0px;
                background-color: transparent;
            }
        """)
        
        main_layout.addWidget(scroll_area)
        
    def _setup_toolbar(self):
        """Configure la barre d'outils principale - Interface responsive et moderne"""
        # Chemin de base pour les ressources
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        toolbar = QToolBar("Outils principaux")
        toolbar.setIconSize(QSize(20, 20))
        toolbar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        toolbar.setStyleSheet("""
            QToolBar {
                spacing: 4px;
                padding: 2px;
                background-color: #2d2d30;
                border-bottom: 1px solid #3e3e42;
            }
            QToolButton {
                background-color: #3e3e42;
                border: 1px solid #555555;
                border-radius: 3px;
                padding: 4px 8px;
                color: #ffffff;
                font-weight: bold;
                font-size: 10px;
                min-width: 60px;
                max-width: 120px;
            }
            QToolButton:hover {
                background-color: #4e4e52;
                border-color: #666666;
            }
            QToolButton:pressed {
                background-color: #2d2d30;
            }
        """)
        self.addToolBar(toolbar)
        
        # Logo BarrelMCD dans la barre d'outils
        logo_action = QAction(self)
        logo_path = os.path.join(base_path, "docs", "logos", "barrel_icon_large.png")
        if os.path.exists(logo_path):
            logo_action.setIcon(QIcon(logo_path))
        logo_action.setToolTip("BarrelMCD - Modélisation Conceptuelle de Données")
        logo_action.setEnabled(False)
        toolbar.addAction(logo_action)
        
        # Bouton Fichier dans la barre d'outils
        file_menu_action = QAction("📁 Fichier", self)
        file_menu_action.setToolTip("Menu Fichier - Nouveau, Ouvrir, Enregistrer, Exporter")
        
        # Créer le menu déroulant pour le bouton Fichier
        file_menu = QMenu(self)
        
        # Actions du menu Fichier
        new_action = QAction("🆕 Nouveau", self)
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self.new_project)
        file_menu.addAction(new_action)
        
        open_action = QAction("📂 Ouvrir...", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.open_project)
        file_menu.addAction(open_action)
        
        file_menu.addSeparator()
        
        save_action = QAction("💾 Enregistrer", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save_project)
        file_menu.addAction(save_action)
        
        save_as_action = QAction("💾 Enregistrer sous...", self)
        save_as_action.setShortcut("Ctrl+Shift+S")
        save_as_action.triggered.connect(self.save_project_as)
        file_menu.addAction(save_as_action)
        
        file_menu.addSeparator()
        
        # Sous-menu Exporter
        export_menu = file_menu.addMenu("📤 Exporter")
        
        export_bar_action = QAction("BarrelMCD (.bar)", self)
        export_bar_action.triggered.connect(lambda: self.export_project('bar'))
        export_menu.addAction(export_bar_action)
        
        export_loo_action = QAction("Barrel (.loo)", self)
        export_loo_action.triggered.connect(lambda: self.export_project('loo'))
        export_menu.addAction(export_loo_action)
        
        export_xml_action = QAction("XML (.xml)", self)
        export_xml_action.triggered.connect(lambda: self.export_project('xml'))
        export_menu.addAction(export_xml_action)
        
        export_json_action = QAction("JSON (.json)", self)
        export_json_action.triggered.connect(lambda: self.export_project('json'))
        export_menu.addAction(export_json_action)
        
        export_sql_action = QAction("SQL (.sql)", self)
        export_sql_action.triggered.connect(lambda: self.export_project('sql'))
        export_menu.addAction(export_sql_action)
        
        file_menu.addSeparator()
        
        quit_action = QAction("❌ Quitter", self)
        quit_action.setShortcut("Ctrl+Q")
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)
        
        # Connecter le menu au bouton
        file_menu_action.setMenu(file_menu)
        
        # Style du menu déroulant
        file_menu.setStyleSheet("""
            QMenu {
                background-color: #2d2d30;
                border: 1px solid #3e3e42;
                color: #ffffff;
                font-size: 11px;
                padding: 4px;
            }
            QMenu::item {
                background-color: transparent;
                padding: 6px 12px;
                border-radius: 3px;
            }
            QMenu::item:selected {
                background-color: #4e4e52;
            }
            QMenu::separator {
                height: 1px;
                background-color: #3e3e42;
                margin: 2px 4px;
            }
        """)
        
        toolbar.addAction(file_menu_action)
        
        toolbar.addSeparator()
        
        # Outils de création rapide avec icônes SVG
        entity_action = QAction(self)
        entity_icon = svg_to_icon(os.path.join(base_path, "docs", "logos", "icon_entity.svg"))
        if entity_icon:
            entity_action.setIcon(entity_icon)
        entity_action.setText("Entité")
        entity_action.setShortcut(QKeySequence("E"))
        entity_action.setToolTip("Créer une entité (E)")
        entity_action.triggered.connect(self.create_entity_quick)
        toolbar.addAction(entity_action)
        
        association_action = QAction(self)
        association_icon = svg_to_icon(os.path.join(base_path, "docs", "logos", "icon_association.svg"))
        if association_icon:
            association_action.setIcon(association_icon)
        association_action.setText("Association")
        association_action.setShortcut(QKeySequence("A"))
        association_action.setToolTip("Créer une association (A)")
        association_action.triggered.connect(self.create_association_quick)
        toolbar.addAction(association_action)
        
        # Bouton création de liens style Db-Main
        link_action = QAction(self)
        link_icon = svg_to_icon(os.path.join(base_path, "docs", "logos", "icon_association.svg"))
        if link_icon:
            link_action.setIcon(link_icon)
        link_action.setText("Lien")
        link_action.setShortcut(QKeySequence("L"))
        link_action.setToolTip("Créer un lien entre éléments (L)")
        link_action.triggered.connect(self.create_link_quick)
        toolbar.addAction(link_action)
        
        # Bouton connexions automatiques style DB-MAIN
        auto_connect_action = QAction(self)
        auto_connect_icon = svg_to_icon(os.path.join(base_path, "docs", "logos", "icon_zoom_in.svg"))
        if auto_connect_icon:
            auto_connect_action.setIcon(auto_connect_icon)
        auto_connect_action.setText("Auto-Liens")
        auto_connect_action.setShortcut(QKeySequence("Ctrl+L"))
        auto_connect_action.setToolTip("Créer automatiquement les liens entre entités et associations proches (Ctrl+L)")
        auto_connect_action.triggered.connect(self.auto_connect_entities)
        toolbar.addAction(auto_connect_action)
        
        toolbar.addSeparator()
        
        # Groupe d'outils de navigation avec icônes SVG
        zoom_in_action = QAction(self)
        zoom_in_icon = svg_to_icon(os.path.join(base_path, "docs", "logos", "icon_zoom_in.svg"))
        if zoom_in_icon:
            zoom_in_action.setIcon(zoom_in_icon)
        zoom_in_action.setText("Zoom +")
        zoom_in_action.setShortcut(QKeySequence("Z"))
        zoom_in_action.setToolTip("Zoom avant (Z)")
        zoom_in_action.triggered.connect(self.canvas.zoom_in)
        toolbar.addAction(zoom_in_action)
        
        zoom_out_action = QAction(self)
        zoom_out_icon = svg_to_icon(os.path.join(base_path, "docs", "logos", "icon_zoom_out.svg"))
        if zoom_out_icon:
            zoom_out_action.setIcon(zoom_out_icon)
        zoom_out_action.setText("Zoom -")
        zoom_out_action.setShortcut(QKeySequence("X"))
        zoom_out_action.setToolTip("Zoom arrière (X)")
        zoom_out_action.triggered.connect(self.canvas.zoom_out)
        toolbar.addAction(zoom_out_action)
        
        fit_action = QAction(self)
        fit_icon = svg_to_icon(os.path.join(base_path, "docs", "logos", "icon_fit_view.svg"))
        if fit_icon:
            fit_action.setIcon(fit_icon)
        fit_action.setText("Ajuster")
        fit_action.setShortcut(QKeySequence("F"))
        fit_action.setToolTip("Ajuster à la vue (F)")
        fit_action.triggered.connect(self.canvas.fit_view)
        toolbar.addAction(fit_action)
        
        grid_action = QAction(self)
        grid_icon = svg_to_icon(os.path.join(base_path, "docs", "logos", "icon_grid.svg"))
        if grid_icon:
            grid_action.setIcon(grid_icon)
        grid_action.setText("Grille")
        grid_action.setShortcut(QKeySequence("G"))
        grid_action.setToolTip("Afficher/Masquer grille (G)")
        grid_action.triggered.connect(self.canvas.toggle_grid)
        toolbar.addAction(grid_action)
        
        toolbar.addSeparator()
        
        # Groupe d'outils d'édition avec icônes SVG
        delete_action = QAction(self)
        delete_icon = svg_to_icon(os.path.join(base_path, "docs", "logos", "icon_delete.svg"))
        if delete_icon:
            delete_action.setIcon(delete_icon)
        delete_action.setText("Supprimer")
        delete_action.setShortcut(QKeySequence("Delete"))
        delete_action.setToolTip("Supprimer l'élément sélectionné (Delete)")
        delete_action.triggered.connect(self.canvas.delete_selected)
        toolbar.addAction(delete_action)
        
        undo_action = QAction(self)
        undo_icon = svg_to_icon(os.path.join(base_path, "docs", "logos", "icon_undo.svg"))
        if undo_icon:
            undo_action.setIcon(undo_icon)
        undo_action.setText("Annuler")
        undo_action.setShortcut(QKeySequence("Ctrl+Z"))
        undo_action.setToolTip("Annuler la dernière action (Ctrl+Z)")
        undo_action.triggered.connect(self.canvas.undo)
        toolbar.addAction(undo_action)
        
        redo_action = QAction(self)
        redo_icon = svg_to_icon(os.path.join(base_path, "docs", "logos", "icon_redo.svg"))
        if redo_icon:
            redo_action.setIcon(redo_icon)
        redo_action.setText("Répéter")
        redo_action.setShortcut(QKeySequence("Ctrl+Y"))
        redo_action.setToolTip("Répéter la dernière action annulée (Ctrl+Y)")
        redo_action.triggered.connect(self.canvas.redo)
        toolbar.addAction(redo_action)
        
        toolbar.addSeparator()
        
        # Groupe d'outils d'import/export avec icônes SVG
        import_action = QAction(self)
        import_icon = svg_to_icon(os.path.join(base_path, "docs", "logos", "icon_import.svg"))
        if import_icon:
            import_action.setIcon(import_icon)
        import_action.setText("Importer")
        import_action.setShortcut(QKeySequence("Ctrl+I"))
        import_action.setToolTip("Importer des données (Ctrl+I)")
        import_action.triggered.connect(self._import_data)
        toolbar.addAction(import_action)
        
        # Bouton d'import Markdown
        markdown_import_action = QAction(self)
        markdown_icon = svg_to_icon(os.path.join(base_path, "docs", "logos", "icon_markdown.svg"))
        if markdown_icon:
            markdown_import_action.setIcon(markdown_icon)
        markdown_import_action.setText("Markdown")
        markdown_import_action.setShortcut(QKeySequence("Ctrl+M"))
        markdown_import_action.setToolTip("Importer depuis Markdown (Ctrl+M)")
        markdown_import_action.triggered.connect(self._import_from_markdown)
        toolbar.addAction(markdown_import_action)
        
        sql_action = QAction(self)
        sql_icon = svg_to_icon(os.path.join(base_path, "docs", "logos", "icon_export_sql.svg"))
        if sql_icon:
            sql_action.setIcon(sql_icon)
        sql_action.setText("SQL")
        sql_action.setShortcut(QKeySequence("Ctrl+E"))
        sql_action.setToolTip("Exporter en SQL (Ctrl+E)")
        sql_action.triggered.connect(self._export_sql)
        toolbar.addAction(sql_action)
        
        # Groupe d'outils d'export avec icônes SVG
        image_action = QAction(self)
        image_icon = svg_to_icon(os.path.join(base_path, "docs", "logos", "icon_image.svg"))
        if image_icon:
            image_action.setIcon(image_icon)
        image_action.setText("Image")
        image_action.setShortcut(QKeySequence("Ctrl+P"))
        image_action.setToolTip("Exporter en image (Ctrl+P)")
        image_action.triggered.connect(self._export_diagram)
        toolbar.addAction(image_action)
        
        pdf_action = QAction(self)
        pdf_icon = svg_to_icon(os.path.join(base_path, "docs", "logos", "icon_pdf.svg"))
        if pdf_icon:
            pdf_action.setIcon(pdf_icon)
        pdf_action.setText("PDF")
        pdf_action.setShortcut(QKeySequence("Ctrl+D"))
        pdf_action.setToolTip("Exporter en PDF (Ctrl+D)")
        pdf_action.triggered.connect(self._export_pdf)
        toolbar.addAction(pdf_action)
        
        toolbar.addSeparator()
        
        # Groupe d'outils d'aide avec icônes SVG
        help_action = QAction(self)
        help_icon = svg_to_icon(os.path.join(base_path, "docs", "logos", "icon_help.svg"))
        if help_icon:
            help_action.setIcon(help_icon)
        help_action.setText("Aide")
        help_action.setShortcut(QKeySequence("F1"))
        help_action.setToolTip("Afficher l'aide (F1)")
        help_action.triggered.connect(self._show_help)
        toolbar.addAction(help_action)
        
        console_action = QAction(self)
        console_icon = svg_to_icon(os.path.join(base_path, "docs", "logos", "icon_console.svg"))
        if console_icon:
            console_action.setIcon(console_icon)
        console_action.setText("Console")
        console_action.setShortcut(QKeySequence("F12"))
        console_action.setToolTip("Afficher la console (F12)")
        console_action.triggered.connect(self._show_console)
        toolbar.addAction(console_action)
        
        # Groupe d'outils d'export MCD avec icônes SVG
        export_action = QAction(self)
        export_icon = svg_to_icon(os.path.join(base_path, "docs", "logos", "icon_export.svg"))
        if export_icon:
            export_action.setIcon(export_icon)
        export_action.setText("Exporter MCD")
        export_action.setShortcut(QKeySequence("Ctrl+Shift+E"))
        export_action.setToolTip("Exporter le MCD (Ctrl+Shift+E)")
        export_action.triggered.connect(self.export_mcd)
        toolbar.addAction(export_action)
        
        import_mcd_action = QAction(self)
        import_mcd_icon = svg_to_icon(os.path.join(base_path, "docs", "logos", "icon_import_mcd.svg"))
        if import_mcd_icon:
            import_mcd_action.setIcon(import_mcd_icon)
        import_mcd_action.setText("Importer MCD")
        import_mcd_action.setShortcut(QKeySequence("Ctrl+Shift+I"))
        import_mcd_action.setToolTip("Importer un MCD (Ctrl+Shift+I)")
        import_mcd_action.triggered.connect(self.import_mcd)
        toolbar.addAction(import_mcd_action)
        
        toolbar.addSeparator()
        
        # Groupe d'outils de connexion intelligente
        auto_connect_action = QAction("🔗 Auto-connexion", self)
        auto_connect_action.setCheckable(True)
        auto_connect_action.setChecked(True)
        auto_connect_action.setToolTip("Activer/désactiver la connexion automatique")
        auto_connect_action.triggered.connect(self.toggle_auto_connect)
        toolbar.addAction(auto_connect_action)
        
        optimize_action = QAction("⚡ Optimiser", self)
        optimize_action.setToolTip("Optimiser toutes les connexions")
        optimize_action.triggered.connect(self.optimize_connections)
        toolbar.addAction(optimize_action)
        
    def _setup_docks(self):
        """Configure les panneaux latéraux"""
        # Panneau des propriétés
        properties_dock = QDockWidget("Propriétés", self)
        properties_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        properties_dock.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable)
        properties_widget = QWidget()
        properties_layout = QVBoxLayout(properties_widget)
        
        # Propriétés de l'élément sélectionné
        self.properties_label = QLabel("Aucun élément sélectionné")
        self.properties_label.setWordWrap(True)
        properties_layout.addWidget(self.properties_label)
        
        properties_dock.setWidget(properties_widget)
        self.addDockWidget(Qt.RightDockWidgetArea, properties_dock)
        
        # Panneau de l'explorateur
        explorer_dock = QDockWidget("Explorateur", self)
        explorer_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        explorer_dock.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable)
        explorer_widget = QWidget()
        explorer_layout = QVBoxLayout(explorer_widget)
        
        # Liste des éléments
        self.elements_list = QListWidget()
        explorer_layout.addWidget(QLabel("Éléments du diagramme:"))
        explorer_layout.addWidget(self.elements_list)
        
        explorer_dock.setWidget(explorer_widget)
        self.addDockWidget(Qt.LeftDockWidgetArea, explorer_dock)
        
        # Stocker les références pour pouvoir les masquer/afficher
        self.properties_dock = properties_dock
        self.explorer_dock = explorer_dock
        
        # Masquer les docks par défaut pour avoir plus d'espace
        properties_dock.hide()
        explorer_dock.hide()
        
    def _connect_signals(self):
        """Connecte les signaux du canvas"""
        self.canvas.entity_created.connect(self._on_entity_created)
        self.canvas.entity_modified.connect(self._on_entity_modified)
        self.canvas.entity_deleted.connect(self._on_entity_deleted)
        self.canvas.association_created.connect(self._on_association_created)
        self.canvas.association_modified.connect(self._on_association_modified)
        self.canvas.association_deleted.connect(self._on_association_deleted)
        self.canvas.diagram_modified.connect(self._on_diagram_modified)
        
    def _on_entity_created(self, entity):
        """Appelé quand une entité est créée"""
        self._log(f"Entité créée: {entity.name}")
        self._update_elements_list()
        
    def _on_entity_modified(self, entity):
        """Appelé quand une entité est modifiée"""
        self._log(f"Entité modifiée: {entity.name}")
        self._update_elements_list()
        
    def _on_entity_deleted(self, entity):
        """Appelé quand une entité est supprimée"""
        self._log(f"Entité supprimée: {entity.name}")
        self._update_elements_list()
        
    def _on_association_created(self, association):
        """Appelé quand une association est créée"""
        self._log(f"Association créée: {association.name}")
        self._update_elements_list()
        
    def _on_association_modified(self, association):
        """Appelé quand une association est modifiée"""
        self._log(f"Association modifiée: {association.name}")
        self._update_elements_list()
        
    def _on_association_deleted(self, association):
        """Appelé quand une association est supprimée"""
        self._log(f"Association supprimée: {association.name}")
        self._update_elements_list()
        
    def _on_diagram_modified(self):
        """Appelé quand le diagramme est modifié"""
        self._log("Diagramme modifié")
        self._update_elements_list()
        
    def _update_elements_list(self):
        """Met à jour la liste des éléments"""
        self.elements_list.clear()
        
        # Ajouter les entités
        for item in self.canvas.scene.items():
            if hasattr(item, 'name'):
                if hasattr(item, 'attributes'):  # C'est une entité
                    self.elements_list.addItem(f"📦 {item.name} ({len(item.attributes)} attributs)")
                else:  # C'est une association
                    self.elements_list.addItem(f"🔗 {item.name}")
        
    def _import_data(self):
        """Importe les données depuis un fichier et lance l'analyse + affichage MCD."""
        file_path, file_type = QFileDialog.getOpenFileName(
            self,
            "Sélectionner un fichier",
            "",
            "JSON (*.json);;CSV (*.csv);;Excel (*.xlsx);;Tous les fichiers (*)"
        )
        if file_path:
            try:
                if file_path.endswith('.json'):
                    import json
                    with open(file_path, 'r', encoding='utf-8') as f:
                        self.current_data = json.load(f)
                    self.current_format = 'json'
                elif file_path.endswith('.csv'):
                    import pandas as pd
                    self.current_data = pd.read_csv(file_path)
                    self.current_format = 'csv'
                elif file_path.endswith('.xlsx'):
                    import pandas as pd
                    self.current_data = pd.read_excel(file_path)
                    self.current_format = 'excel'
                else:
                    raise ValueError("Format de fichier non supporté")
                self._analyze_and_draw()
                self._log(f"Import réussi : {file_path}")
                QMessageBox.information(self, "Succès", "Données importées et analysées avec succès!")
            except Exception as e:
                self._log(f"Erreur import : {str(e)}")
                QMessageBox.critical(self, "Erreur", f"Erreur lors de l'import: {str(e)}")
    
    def _analyze_data(self):
        """Analyse les données courantes et affiche le MCD."""
        try:
            if self.current_data is None or self.current_format is None:
                QMessageBox.warning(self, "Avertissement", "Aucune donnée à analyser. Veuillez importer un fichier d'abord.")
                return
            self._analyze_and_draw()
            self._log("Analyse terminée et MCD affiché!")
            QMessageBox.information(self, "Succès", "Analyse terminée et MCD affiché!")
        except Exception as e:
            self._log(f"Erreur analyse : {str(e)}")
            QMessageBox.critical(self, "Erreur", f"Erreur lors de l'analyse: {str(e)}")
    
    def _analyze_and_draw(self):
        """Analyse les données et dessine le MCD dans la scène graphique."""
        # Analyse des données
        if self.current_format in ['json']:
            mcd = self._get_data_analyzer().analyze_data(self.current_data, format_type='json')
        elif self.current_format in ['csv', 'excel']:
            # Pour CSV/Excel, convertir en dictionnaire
            mcd = self._get_data_analyzer().analyze_data(self.current_data.to_dict(orient='records'), format_type='json')
        else:
            raise ValueError("Format de données non supporté pour l'analyse")
        self.current_mcd = mcd
        # Adapter le format attendu par MCDDrawer
        mcd_for_draw = self._format_mcd_for_draw(mcd)
        # Redimensionner la scène
        self.canvas.scene.setSceneRect(0, 0, 1200, 800)
        self.canvas.scene.clear()
        self.mcd_drawer.draw_mcd(self.canvas.scene, mcd_for_draw)
    
    def _format_mcd_for_draw(self, mcd):
        """Adapte le MCD pour le dessin (liste d'entités et de relations)."""
        # Les entités doivent être une liste avec 'name' et 'attributes'
        entities = []
        for name, ent in mcd['entities'].items():
            attrs = []
            for attr in ent.get('attributes', []):
                attrs.append({
                    'name': attr.get('name', ''),
                    'type': attr.get('type', ''),
                    'is_pk': attr.get('primary_key', False)
                })
            entities.append({'name': name, 'attributes': attrs})
        # Les relations doivent être une liste avec 'name', 'entity1', 'entity2', 'cardinality'
        relations = []
        for rel in mcd['relations']:
            relations.append({
                'name': rel.get('name', ''),
                'entity1': rel.get('entity1', ''),
                'entity2': rel.get('entity2', ''),
                'cardinality': rel.get('cardinality', '1:1')
            })
        return {'entities': entities, 'relations': relations}
    
    def _convert_model(self):
        """Convertit le modèle vers UML ou MLD et affiche le résultat."""
        if self.current_mcd is None:
            self._log("Aucun MCD à convertir.")
            QMessageBox.warning(self, "Avertissement", "Aucun MCD à convertir. Veuillez importer et analyser des données d'abord.")
            return

        # Choix du type de conversion
        conversion_types = ["UML (diagramme de classes)", "MLD (modèle logique de données)"]
        choice, ok = QInputDialog.getItem(self, "Type de conversion", "Choisir le format :", conversion_types, 0, False)
        if not ok:
            return

        if choice.startswith("UML"):
            uml = self._get_model_converter().convert_model(self.current_mcd, self._get_model_converter().ConversionType.MCD_TO_UML)
            text = str(uml)
        else:
            mld = self.model_converter.convert_model(self.current_mcd, self.model_converter.ConversionType.MCD_TO_MLD)
            text = str(mld)

        # Afficher le résultat dans une boîte de dialogue
        dlg = QDialog(self)
        dlg.setWindowTitle("Résultat de la conversion")
        layout = QVBoxLayout(dlg)
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setText(text)
        layout.addWidget(text_edit)
        close_btn = QPushButton("Fermer")
        close_btn.clicked.connect(dlg.accept)
        layout.addWidget(close_btn)
        dlg.exec_()
        self._log(f"Conversion effectuée : {choice}")
    
    def _export_sql(self):
        """Exporte le modèle en SQL."""
        try:
            if self.current_mcd is None:
                self._log("Aucun MCD à exporter.")
                QMessageBox.warning(self, "Avertissement", "Aucun MCD à exporter. Veuillez importer et analyser des données d'abord.")
                return
            # Conversion MCD -> MLD
            mld = self.model_converter.convert_model(self.current_mcd, self.model_converter.ConversionType.MCD_TO_MLD)
            # Conversion MLD -> SQL (utilisation directe du convertisseur pour obtenir le script)
            sql_script = self.model_converter._convert_to_sql(mld)
            # Sauvegarde dans un fichier
            file_path, _ = QFileDialog.getSaveFileName(self, "Enregistrer le script SQL", "modele.sql", "Fichiers SQL (*.sql)")
            if file_path:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(sql_script)
                self._log(f"Export SQL : {file_path}")
                QMessageBox.information(self, "Succès", f"Script SQL exporté avec succès dans : {file_path}")
        except Exception as e:
            self._log(f"Erreur export SQL : {str(e)}")
            QMessageBox.critical(self, "Erreur", f"Erreur lors de l'export: {str(e)}")
    
    def _export_diagram(self):
        """Exporte le diagramme MCD affiché en PNG."""
        file_path, _ = QFileDialog.getSaveFileName(self, "Enregistrer le diagramme", "diagramme.png", "Images PNG (*.png)")
        if file_path:
            rect = self.canvas.scene.sceneRect()
            image = QImage(int(rect.width()), int(rect.height()), QImage.Format_ARGB32)
            image.fill(0xFFFFFFFF)
            painter = QPainter(image)
            self.canvas.scene.render(painter)
            painter.end()
            image.save(file_path)
            self._log(f"Export diagramme PNG : {file_path}")
            QMessageBox.information(self, "Succès", f"Diagramme exporté avec succès dans : {file_path}")
    
    def _export_pdf(self):
        """Exporte le diagramme MCD affiché en PDF."""
        file_path, _ = QFileDialog.getSaveFileName(self, "Enregistrer le diagramme PDF", "diagramme.pdf", "Fichiers PDF (*.pdf)")
        if file_path:
            printer = QPrinter(QPrinter.HighResolution)
            printer.setOutputFormat(QPrinter.PdfFormat)
            printer.setOutputFileName(file_path)
            rect = self.canvas.scene.sceneRect()
            printer.setPaperSize(rect.size(), QPrinter.Point)
            painter = QPainter(printer)
            self.canvas.scene.render(painter)
            painter.end()
            self._log(f"Export diagramme PDF : {file_path}")
            QMessageBox.information(self, "Succès", f"Diagramme exporté en PDF dans : {file_path}")
    
    def _show_help(self):
        """Affiche la documentation utilisateur dans une fenêtre de dialogue."""
        doc = (
            "<h2>BarrelMCD - Aide utilisateur</h2>"
            "<h3>Outils de création :</h3>"
            "<ul>"
            "<li><b>Sélection (S)</b> : Sélectionner et déplacer les éléments</li>"
            "<li><b>Entité (E)</b> : Créer une nouvelle entité</li>"
            "<li><b>Association (A)</b> : Créer une nouvelle association</li>"
            "<li><b>Relation (R)</b> : Créer une relation entre entités</li>"
            "</ul>"
            "<h3>Navigation :</h3>"
            "<ul>"
            "<li><b>Zoom + (Z)</b> : Zoom avant</li>"
            "<li><b>Zoom - (X)</b> : Zoom arrière</li>"
            "<li><b>Ajuster (F)</b> : Ajuster la vue</li>"
            "<li><b>Grille (G)</b> : Afficher/Masquer la grille</li>"
            "</ul>"
            "<h3>Édition :</h3>"
            "<ul>"
            "<li><b>Delete</b> : Supprimer la sélection</li>"
            "<li><b>Ctrl+Z</b> : Annuler</li>"
            "<li><b>Ctrl+Y</b> : Répéter</li>"
            "</ul>"
            "<h3>Import/Export :</h3>"
            "<ul>"
            "<li><b>Ctrl+O</b> : Importer des données</li>"
            "<li><b>Ctrl+S</b> : Exporter en SQL</li>"
            "<li><b>Ctrl+P</b> : Exporter en PNG</li>"
            "<li><b>Ctrl+D</b> : Exporter en PDF</li>"
            "</ul>"
            "<p>Double-cliquez sur un élément pour le modifier.</p>"
            "<p>Clic droit pour le menu contextuel.</p>"
        )
        dlg = QDialog(self)
        dlg.setWindowTitle("Aide BarrelMCD")
        layout = QVBoxLayout(dlg)
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setHtml(doc)
        layout.addWidget(text_edit)
        close_btn = QPushButton("Fermer")
        close_btn.clicked.connect(dlg.accept)
        layout.addWidget(close_btn)
        dlg.exec_()
        self._log("Affichage de l'aide utilisateur.")
    
    def _log(self, message):
        self.log_messages.append(message)
        if len(self.log_messages) > 500:
            self.log_messages = self.log_messages[-500:]
    
    def _show_console(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("Console / Log d'erreurs")
        layout = QVBoxLayout(dlg)
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setPlainText("\n".join(self.log_messages))
        layout.addWidget(text_edit)
        close_btn = QPushButton("Fermer")
        close_btn.clicked.connect(dlg.accept)
        layout.addWidget(close_btn)
        dlg.exec_() 

    def export_mcd(self):
        """Exporte le MCD en JSON"""
        from PyQt5.QtWidgets import QFileDialog
        filename, _ = QFileDialog.getSaveFileName(
            self, "Exporter MCD", "", "JSON Files (*.json);;All Files (*)"
        )
        if filename:
            try:
                json_data = self.canvas.export_mcd_to_json()
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(json_data)
                QMessageBox.information(self, "Succès", "MCD exporté avec succès !")
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Erreur lors de l'export : {e}")
                
    def import_mcd(self):
        """Importe un MCD depuis JSON"""
        from PyQt5.QtWidgets import QFileDialog
        filename, _ = QFileDialog.getOpenFileName(
            self, "Importer MCD", "", "JSON Files (*.json);;All Files (*)"
        )
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    json_data = f.read()
                if self.canvas.import_mcd_from_json(json_data):
                    QMessageBox.information(self, "Succès", "MCD importé avec succès !")
                else:
                    QMessageBox.critical(self, "Erreur", "Erreur lors de l'import du MCD")
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Erreur lors de l'import : {e}")
    
    def _import_from_markdown(self):
        """Importe un MCD depuis un fichier markdown"""
        try:
            # Ouvrir le dialogue d'import markdown
            dialog = MarkdownImportDialog(self)
            result = dialog.exec_()
            
            if result == QDialog.Accepted:
                # Récupérer la structure MCD parsée
                mcd_structure = dialog.get_mcd_structure()
                
                if mcd_structure:
                    # Créer les entités dans le canvas
                    self._create_entities_from_markdown(mcd_structure)
                    
                    # Créer les associations dans le canvas
                    self._create_associations_from_markdown(mcd_structure)
                    
                    QMessageBox.information(
                        self, 
                        "Import réussi", 
                        f"MCD importé avec succès !\n"
                        f"Entités: {len(mcd_structure['entities'])}\n"
                        f"Associations: {len(mcd_structure['associations'])}"
                    )
                else:
                    QMessageBox.warning(self, "Erreur", "Aucune structure MCD valide trouvée")
                    
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de l'import markdown: {str(e)}")
    
    def _create_entities_from_markdown(self, mcd_structure):
        """Crée les entités à partir de la structure MCD markdown"""
        if not hasattr(self, 'canvas') or not self.canvas:
            return
            
        # Position initiale pour les entités
        x, y = 100, 100
        spacing = 250
        
        for entity_name, entity_data in mcd_structure['entities'].items():
            # Créer l'entité dans le canvas
            entity = self.canvas.create_entity(entity_name, x, y)
            
            # Ajouter les attributs
            for attr in entity_data.get('attributes', []):
                if hasattr(entity, 'add_attribute'):
                    entity.add_attribute(
                        attr['name'],
                        attr.get('type', 'varchar'),
                        attr.get('description', '')
                    )
            
            # Définir la clé primaire si elle existe
            if entity_data.get('primary_key'):
                if hasattr(entity, 'set_primary_key'):
                    entity.set_primary_key(entity_data['primary_key'])
            
            # Déplacer la position pour la prochaine entité
            x += spacing
            if x > 800:  # Nouvelle ligne après 3 entités
                x = 100
                y += 200
    
    def _create_associations_from_markdown(self, mcd_structure):
        """Crée les associations à partir de la structure MCD markdown"""
        if not hasattr(self, 'canvas') or not self.canvas:
            return
            
        for association in mcd_structure.get('associations', []):
            # Trouver les entités dans le canvas
            entity1 = self.canvas.find_entity_by_name(association['entity1'])
            entity2 = self.canvas.find_entity_by_name(association['entity2'])
            
            if entity1 and entity2:
                # Créer l'association
                self.canvas.create_association(
                    entity1,
                    entity2,
                    association['name'],
                    association.get('cardinality1', '1,1'),
                    association.get('cardinality2', '1,1')
                ) 

    def _connect_history_signals(self):
        """Connecte les signaux de l'historique"""
        if hasattr(self, "history_manager"):
            self.history_manager.can_undo_changed.connect(self._update_undo_action)
            self.history_manager.can_redo_changed.connect(self._update_redo_action)

    def _connect_shortcut_signals(self):
        """Connecte les signaux des raccourcis"""
        if hasattr(self, "shortcut_manager"):
            self.shortcut_manager.shortcut_triggered.connect(self._handle_shortcut)

    def _setup_shortcuts(self):
        """Configure les raccourcis clavier (méthode vide pour éviter l'erreur)"""
        pass

    def _setup_menu(self):
        super().menuBar().clear()
        # Menu Fichier
        file_menu = self.menuBar().addMenu('&Fichier')
        
        # Action Nouveau
        new_action = QAction('&Nouveau', self)
        new_action.setShortcut('Ctrl+N')
        new_action.setStatusTip('Créer un nouveau projet')
        new_action.triggered.connect(self.new_project)
        file_menu.addAction(new_action)
        
        # Action Ouvrir
        open_action = QAction('&Ouvrir...', self)
        open_action.setShortcut('Ctrl+O')
        open_action.setStatusTip('Ouvrir un projet existant')
        open_action.triggered.connect(self.open_project)
        file_menu.addAction(open_action)
        
        file_menu.addSeparator()
        
        # Action Enregistrer
        save_action = QAction('&Enregistrer', self)
        save_action.setShortcut('Ctrl+S')
        save_action.setStatusTip('Enregistrer le projet')
        save_action.triggered.connect(self.save_project)
        file_menu.addAction(save_action)
        
        # Action Enregistrer sous
        save_as_action = QAction('Enregistrer &sous...', self)
        save_as_action.setShortcut('Ctrl+Shift+S')
        save_as_action.setStatusTip('Enregistrer le projet sous un nouveau nom')
        save_as_action.triggered.connect(self.save_project_as)
        file_menu.addAction(save_as_action)
        
        file_menu.addSeparator()
        
        # Sous-menu Exporter
        export_menu = file_menu.addMenu('&Exporter')
        
        # Export en format .bar (BarrelMCD)
        export_bar_action = QAction('Format &BarrelMCD (.bar)', self)
        export_bar_action.setStatusTip('Exporter en format BarrelMCD natif')
        export_bar_action.triggered.connect(lambda: self.export_project('bar'))
        export_menu.addAction(export_bar_action)
        
        # Export en format .loo
        export_loo_action = QAction('Format &Barrel (.loo)', self)
        export_loo_action.setStatusTip('Exporter en format .loo')
        export_loo_action.triggered.connect(lambda: self.export_project('loo'))
        export_menu.addAction(export_loo_action)
        
        # Export en format .xml
        export_xml_action = QAction('Format &XML (.xml)', self)
        export_xml_action.setStatusTip('Exporter en format XML simplifié')
        export_xml_action.triggered.connect(lambda: self.export_project('xml'))
        export_menu.addAction(export_xml_action)
        
        # Export en format .json
        export_json_action = QAction('Format &JSON (.json)', self)
        export_json_action.setStatusTip('Exporter en format JSON')
        export_json_action.triggered.connect(lambda: self.export_project('json'))
        export_menu.addAction(export_json_action)
        
        # Export en format .sql
        export_sql_action = QAction('Format &SQL (.sql)', self)
        export_sql_action.setStatusTip('Exporter en format SQL')
        export_sql_action.triggered.connect(lambda: self.export_project('sql'))
        export_menu.addAction(export_sql_action)
        
        file_menu.addSeparator()
        
        # Action Quitter
        quit_action = QAction('&Quitter', self)
        quit_action.setShortcut('Ctrl+Q')
        quit_action.setStatusTip('Quitter l\'application')
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)
        
        # Menu Édition
        edit_menu = self.menuBar().addMenu('&Édition')
        
        # Actions d'édition
        undo_action = QAction('&Annuler', self)
        undo_action.setShortcut('Ctrl+Z')
        undo_action.setStatusTip('Annuler la dernière action')
        undo_action.triggered.connect(self.canvas.undo)
        edit_menu.addAction(undo_action)
        
        redo_action = QAction('&Répéter', self)
        redo_action.setShortcut('Ctrl+Y')
        redo_action.setStatusTip('Répéter la dernière action annulée')
        redo_action.triggered.connect(self.canvas.redo)
        edit_menu.addAction(redo_action)
        
        edit_menu.addSeparator()
        
        # Actions de création
        create_entity_action = QAction('Nouvelle &Entité', self)
        create_entity_action.setShortcut('E')
        
        # Menu Affichage
        view_menu = self.menuBar().addMenu('&Affichage')
        
        # Action Grand écran
        large_action = QAction('&Grand écran', self)
        large_action.setShortcut('F11')
        large_action.setStatusTip('Mode grand écran (F11)')
        large_action.triggered.connect(self.show_large_screen)
        view_menu.addAction(large_action)
        
        # Action Écran moyen
        medium_action = QAction('&Écran moyen', self)
        medium_action.setShortcut('F10')
        medium_action.setStatusTip('Mode écran moyen (F10)')
        medium_action.triggered.connect(self.show_medium_screen)
        view_menu.addAction(medium_action)
        
        # Action Petit écran
        small_action = QAction('&Petit écran', self)
        small_action.setShortcut('F9')
        small_action.setStatusTip('Mode petit écran (F9)')
        small_action.triggered.connect(self.show_small_screen)
        view_menu.addAction(small_action)
        
        view_menu.addSeparator()
        
        # Action Plein écran (mode spécial)
        fullscreen_action = QAction('&Plein écran', self)
        fullscreen_action.setShortcut('F12')
        fullscreen_action.setStatusTip('Basculer en mode plein écran (F12)')
        fullscreen_action.triggered.connect(self.toggle_fullscreen)
        view_menu.addAction(fullscreen_action)
        
        view_menu.addSeparator()
        
        # Actions pour les docks
        toggle_properties_action = QAction('&Panneau Propriétés', self)
        toggle_properties_action.setShortcut('Ctrl+P')
        toggle_properties_action.setStatusTip('Afficher/Masquer le panneau des propriétés')
        toggle_properties_action.triggered.connect(self.toggle_properties_dock)
        view_menu.addAction(toggle_properties_action)
        
        toggle_explorer_action = QAction('&Panneau Explorateur', self)
        toggle_explorer_action.setShortcut('Ctrl+E')
        toggle_explorer_action.setStatusTip('Afficher/Masquer le panneau explorateur')
        toggle_explorer_action.triggered.connect(self.toggle_explorer_dock)
        view_menu.addAction(toggle_explorer_action)
        
        view_menu.addSeparator()
        
        # Actions de zoom et navigation
        zoom_in_action = QAction('Zoom &Avant', self)
        zoom_in_action.setShortcut('Z')
        zoom_in_action.setStatusTip('Zoom avant')
        zoom_in_action.triggered.connect(self.canvas.zoom_in)
        view_menu.addAction(zoom_in_action)
        
        zoom_out_action = QAction('Zoom &Arrière', self)
        zoom_out_action.setShortcut('X')
        zoom_out_action.setStatusTip('Zoom arrière')
        zoom_out_action.triggered.connect(self.canvas.zoom_out)
        view_menu.addAction(zoom_out_action)
        
        fit_view_action = QAction('&Ajuster à la vue', self)
        fit_view_action.setShortcut('F')
        fit_view_action.setStatusTip('Ajuster le diagramme à la vue')
        fit_view_action.triggered.connect(self.canvas.fit_view)
        view_menu.addAction(fit_view_action)
        
        view_menu.addSeparator()
        
        toggle_grid_action = QAction('Afficher/Masquer la &Grille', self)
        toggle_grid_action.setShortcut('G')
        toggle_grid_action.setStatusTip('Afficher ou masquer la grille')
        toggle_grid_action.triggered.connect(self.canvas.toggle_grid)
        view_menu.addAction(toggle_grid_action)
        
        # Menu Aide
        help_menu = self.menuBar().addMenu('&Aide')
        
        help_action = QAction('&Aide', self)
        help_action.setShortcut('F1')
        help_action.setStatusTip('Afficher l\'aide')
        help_action.triggered.connect(self._show_help)
        help_menu.addAction(help_action)
        
        about_action = QAction('À &propos', self)
        about_action.setStatusTip('À propos de BarrelMCD')
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def _update_undo_action(self, can_undo: bool):
        pass

    def _update_redo_action(self, can_redo: bool):
        pass

    def _handle_shortcut(self, shortcut_name: str):
        pass 

    def create_entity_quick(self):
        """Active le mode création d'entité - Version fluide style Db-Main"""
        print("[DEBUG] create_entity_quick() appelée")
        try:
            # Activer directement le mode création d'entité
            self.canvas.set_mode_entity()
            print("[DEBUG] Mode création d'entité activé")
            
            # Afficher un message informatif non-bloquant
            self.statusBar().showMessage("Mode création d'entités activé - Cliquez sur la palette pour créer une entité (Échap pour sortir)", 3000)
        except Exception as e:
            print(f"[DEBUG] Erreur dans create_entity_quick: {e}")
            import traceback
            traceback.print_exc()
        
    def create_association_quick(self):
        """Active le mode création d'association - Version fluide style Db-Main"""
        print("[DEBUG] create_association_quick() appelée")
        try:
            # Activer directement le mode création d'association
            self.canvas.set_mode_association()
            print("[DEBUG] Mode création d'association activé")
            
            # Afficher un message informatif non-bloquant
            self.statusBar().showMessage("Mode création d'associations activé - Cliquez sur la palette pour créer une association (Échap pour sortir)", 3000)
        except Exception as e:
            print(f"[DEBUG] Erreur dans create_association_quick: {e}")
            import traceback
            traceback.print_exc() 
    
    def create_link_quick(self):
        """Active le mode création de liens style Db-Main"""
        print("[DEBUG] create_link_quick() appelée")
        try:
            self.canvas.set_mode_create_link()
            print("[DEBUG] Mode création de liens activé")
            
            # Afficher un message informatif non-bloquant
            self.statusBar().showMessage("Mode création de liens activé - Cliquez sur deux éléments pour les relier (Échap pour sortir)", 3000)
        except Exception as e:
            print(f"[DEBUG] Erreur dans create_link_quick: {e}")
            import traceback
            traceback.print_exc()
            
    def auto_connect_entities(self):
        """Active les connexions automatiques style DB-MAIN"""
        print("[DEBUG] auto_connect_entities() appelée")
        try:
            # Appeler la méthode de détection automatique du canvas
            self.canvas.auto_detect_connections()
            print("[DEBUG] Connexions automatiques activées")
        except Exception as e:
            print(f"[DEBUG] Erreur dans auto_connect_entities: {e}")
            import traceback
            traceback.print_exc()
    
    def new_project(self):
        """Crée un nouveau projet"""
        reply = QMessageBox.question(self, 'Nouveau projet', 
                                   'Voulez-vous créer un nouveau projet ? Les modifications non sauvegardées seront perdues.',
                                   QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.canvas.clear()
            self.current_file_path = None
            self.setWindowTitle('BarrelMCD - Nouveau projet')
            self._log("Nouveau projet créé")
    
    def open_project(self):
        """Ouvre un projet existant"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Ouvrir un projet", "", 
            "Tous les formats (*.bar *.loo *.xml *.json);;Format BarrelMCD (*.bar);;Format .loo (*.loo);;Format XML (*.xml);;Format JSON (*.json);;Tous les fichiers (*)"
        )
        if file_path:
            try:
                self.load_project(file_path)
                self.current_file_path = file_path
                self.setWindowTitle(f'BarrelMCD - {os.path.basename(file_path)}')
                self._log(f"Projet ouvert : {file_path}")
                QMessageBox.information(self, "Succès", "Projet ouvert avec succès !")
            except Exception as e:
                self._log(f"Erreur lors de l'ouverture : {str(e)}")
                QMessageBox.critical(self, "Erreur", f"Erreur lors de l'ouverture : {str(e)}")
    
    def save_project(self):
        """Enregistre le projet"""
        if hasattr(self, 'current_file_path') and self.current_file_path:
            self.save_project_to_file(self.current_file_path)
        else:
            self.save_project_as()
    
    def save_project_as(self):
        """Enregistre le projet sous un nouveau nom"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Enregistrer le projet sous", "", 
            "Format BarrelMCD (*.bar);;Format .loo (*.loo);;Format XML (*.xml);;Format JSON (*.json);;Tous les fichiers (*)"
        )
        if file_path:
            try:
                self.save_project_to_file(file_path)
                self.current_file_path = file_path
                self.setWindowTitle(f'BarrelMCD - {os.path.basename(file_path)}')
                self._log(f"Projet enregistré : {file_path}")
                QMessageBox.information(self, "Succès", "Projet enregistré avec succès !")
            except Exception as e:
                self._log(f"Erreur lors de l'enregistrement : {str(e)}")
                QMessageBox.critical(self, "Erreur", f"Erreur lors de l'enregistrement : {str(e)}")
    
    def save_project_to_file(self, file_path):
        """Enregistre le projet dans un fichier"""
        extension = os.path.splitext(file_path)[1].lower()
        
        if extension == '.bar':
            self.save_as_barrel_format(file_path)
        elif extension == '.loo':
            self.save_as_looping_format(file_path)
        elif extension == '.xml':
            self.save_as_xml_format(file_path)
        elif extension == '.json':
            self.save_as_json_format(file_path)
        else:
            # Par défaut, sauvegarde en format BarrelMCD
            self.save_as_barrel_format(file_path)
    
    def load_project(self, file_path):
        """Charge un projet depuis un fichier"""
        extension = os.path.splitext(file_path)[1].lower()
        
        if extension == '.bar':
            self.load_from_barrel_format(file_path)
        elif extension == '.loo':
            self.load_from_looping_format(file_path)
        elif extension == '.xml':
            self.load_from_xml_format(file_path)
        elif extension == '.json':
            self.load_from_json_format(file_path)
        else:
            raise ValueError(f"Format de fichier non supporté : {extension}")
    
    def export_project(self, format_type):
        """Exporte le projet dans un format spécifique"""
        format_extensions = {
            'bar': ('.bar', 'Format BarrelMCD (*.bar)'),
            'loo': ('.loo', 'Format .loo (*.loo)'),
            'xml': ('.xml', 'Format XML (*.xml)'),
            'json': ('.json', 'Format JSON (*.json)'),
            'sql': ('.sql', 'Format SQL (*.sql)')
        }
        
        if format_type not in format_extensions:
            QMessageBox.warning(self, "Format non supporté", f"Le format {format_type} n'est pas supporté.")
            return
        
        ext, filter_name = format_extensions[format_type]
        file_path, _ = QFileDialog.getSaveFileName(
            self, f"Exporter en {format_type.upper()}", f"projet{ext}", filter_name
        )
        
        if file_path:
            try:
                if format_type == 'bar':
                    self.save_as_barrel_format(file_path)
                elif format_type == 'loo':
                    self.save_as_looping_format(file_path)
                elif format_type == 'xml':
                    self.save_as_xml_format(file_path)
                elif format_type == 'json':
                    self.save_as_json_format(file_path)
                elif format_type == 'sql':
                    self.save_as_sql_format(file_path)
                
                self._log(f"Export {format_type.upper()} : {file_path}")
                QMessageBox.information(self, "Succès", f"Projet exporté en {format_type.upper()} avec succès !")
            except Exception as e:
                self._log(f"Erreur export {format_type.upper()} : {str(e)}")
                QMessageBox.critical(self, "Erreur", f"Erreur lors de l'export : {str(e)}")
    
    def save_as_barrel_format(self, file_path):
        """Sauvegarde en format BarrelMCD (.bar)"""
        import json
        data = {
            'version': '1.0',
            'format': 'barrelmcd',
            'created': time.strftime('%Y-%m-%d %H:%M:%S'),
            'entities': self.canvas.get_entities_data(),
            'associations': self.canvas.get_associations_data(),
            'canvas_info': {
                'zoom': self.canvas.transform().m11(),
                'center': [self.canvas.mapToScene(self.canvas.viewport().rect().center()).x(),
                          self.canvas.mapToScene(self.canvas.viewport().rect().center()).y()]
            }
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def save_as_looping_format(self, file_path):
        """Sauvegarde en format .loo"""
        import json
        data = {
            'version': '1.0',
            'format': 'looping',
            'created': time.strftime('%Y-%m-%d %H:%M:%S'),
            'project_name': 'BarrelMCD Project',
            'entities': self.canvas.get_entities_data(),
            'associations': self.canvas.get_associations_data(),
            'metadata': {
                'author': 'BarrelMCD',
                'description': 'Modèle Conceptuel de Données',
                'last_modified': time.strftime('%Y-%m-%d %H:%M:%S')
            }
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def save_as_xml_format(self, file_path):
        """Sauvegarde en format XML simplifié"""
        import xml.etree.ElementTree as ET
        
        root = ET.Element('mcd')
        root.set('version', '1.0')
        root.set('created', time.strftime('%Y-%m-%d %H:%M:%S'))
        
        # Entités
        entities_elem = ET.SubElement(root, 'entities')
        for entity_data in self.canvas.get_entities_data():
            entity_elem = ET.SubElement(entities_elem, 'entity')
            entity_elem.set('id', str(entity_data.get('id', '')))
            entity_elem.set('name', entity_data.get('name', ''))
            entity_elem.set('x', str(entity_data.get('x', 0)))
            entity_elem.set('y', str(entity_data.get('y', 0)))
            
            # Attributs
            attributes_elem = ET.SubElement(entity_elem, 'attributes')
            for attr in entity_data.get('attributes', []):
                attr_elem = ET.SubElement(attributes_elem, 'attribute')
                attr_elem.set('name', attr.get('name', ''))
                attr_elem.set('type', attr.get('type', ''))
                attr_elem.set('primary', str(attr.get('primary', False)).lower())
        
        # Associations
        associations_elem = ET.SubElement(root, 'associations')
        for assoc_data in self.canvas.get_associations_data():
            assoc_elem = ET.SubElement(associations_elem, 'association')
            assoc_elem.set('id', str(assoc_data.get('id', '')))
            assoc_elem.set('name', assoc_data.get('name', ''))
            assoc_elem.set('x', str(assoc_data.get('x', 0)))
            assoc_elem.set('y', str(assoc_data.get('y', 0)))
            
            # Relations
            relations_elem = ET.SubElement(assoc_elem, 'relations')
            for rel in assoc_data.get('relations', []):
                rel_elem = ET.SubElement(relations_elem, 'relation')
                rel_elem.set('entity_id', str(rel.get('entity_id', '')))
                rel_elem.set('cardinality', rel.get('cardinality', ''))
                rel_elem.set('role', rel.get('role', ''))
        
        # Écrire le fichier XML
        tree = ET.ElementTree(root)
        ET.indent(tree, space="  ")
        tree.write(file_path, encoding='utf-8', xml_declaration=True)
    
    def save_as_json_format(self, file_path):
        """Sauvegarde en format JSON standard"""
        import json
        data = {
            'version': '1.0',
            'format': 'json',
            'created': time.strftime('%Y-%m-%d %H:%M:%S'),
            'entities': self.canvas.get_entities_data(),
            'associations': self.canvas.get_associations_data()
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def save_as_sql_format(self, file_path):
        """Sauvegarde en format SQL"""
        try:
            if not hasattr(self, 'current_mcd') or not self.current_mcd:
                QMessageBox.warning(self, "Avertissement", "Aucun MCD à exporter. Veuillez importer et analyser des données d'abord.")
                return
            
            # Conversion MCD -> MLD
            mld = self.model_converter.convert_model(self.current_mcd, self.model_converter.ConversionType.MCD_TO_MLD)
            # Conversion MLD -> SQL
            sql_script = self.model_converter._convert_to_sql(mld)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(sql_script)
        except Exception as e:
            raise Exception(f"Erreur lors de la conversion SQL : {str(e)}")
    
    def load_from_barrel_format(self, file_path):
        """Charge depuis le format BarrelMCD (.bar)"""
        import json
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.canvas.clear()
        self.canvas.load_from_data(data)
    
    def load_from_looping_format(self, file_path):
        """Charge depuis le format .loo"""
        import json
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.canvas.clear()
        self.canvas.load_from_data(data)
    
    def load_from_xml_format(self, file_path):
        """Charge depuis le format XML"""
        import xml.etree.ElementTree as ET
        
        tree = ET.parse(file_path)
        root = tree.getroot()
        
        self.canvas.clear()
        
        # Charger les entités
        entities_elem = root.find('entities')
        if entities_elem is not None:
            for entity_elem in entities_elem.findall('entity'):
                entity_data = {
                    'id': entity_elem.get('id', ''),
                    'name': entity_elem.get('name', ''),
                    'x': float(entity_elem.get('x', 0)),
                    'y': float(entity_elem.get('y', 0)),
                    'attributes': []
                }
                
                # Charger les attributs
                attributes_elem = entity_elem.find('attributes')
                if attributes_elem is not None:
                    for attr_elem in attributes_elem.findall('attribute'):
                        attr_data = {
                            'name': attr_elem.get('name', ''),
                            'type': attr_elem.get('type', ''),
                            'primary': attr_elem.get('primary', 'false').lower() == 'true'
                        }
                        entity_data['attributes'].append(attr_data)
                
                self.canvas.create_entity_from_data(entity_data)
        
        # Charger les associations
        associations_elem = root.find('associations')
        if associations_elem is not None:
            for assoc_elem in associations_elem.findall('association'):
                assoc_data = {
                    'id': assoc_elem.get('id', ''),
                    'name': assoc_elem.get('name', ''),
                    'x': float(assoc_elem.get('x', 0)),
                    'y': float(assoc_elem.get('y', 0)),
                    'relations': []
                }
                
                # Charger les relations
                relations_elem = assoc_elem.find('relations')
                if relations_elem is not None:
                    for rel_elem in relations_elem.findall('relation'):
                        rel_data = {
                            'entity_id': rel_elem.get('entity_id', ''),
                            'cardinality': rel_elem.get('cardinality', ''),
                            'role': rel_elem.get('role', '')
                        }
                        assoc_data['relations'].append(rel_data)
                
                self.canvas.create_association_from_data(assoc_data)
    
    def load_from_json_format(self, file_path):
        """Charge depuis le format JSON"""
        import json
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.canvas.clear()
        self.canvas.load_from_data(data)
    
    def show_about(self):
        """Affiche la boîte de dialogue À propos"""
        # Créer une boîte de dialogue personnalisée
        about_dialog = QDialog(self)
        about_dialog.setWindowTitle("À propos de BarrelMCD")
        about_dialog.setFixedSize(400, 280)
        about_dialog.setStyleSheet("""
            QDialog {
                background-color: #2d2d30;
                color: #e0e0e0;
            }
            QLabel {
                color: #e0e0e0;
                font-size: 11px;
                background-color: transparent;
                border: none;
            }
            QPushButton {
                background-color: #3e3e42;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 8px 16px;
                color: #e0e0e0;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #4e4e52;
            }
        """)
        
        layout = QVBoxLayout(about_dialog)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Logo BarrelMCD (plus petit)
        logo_label = QLabel()
        logo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'docs/logos/barrel_icon_512.png')
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path)
            # Redimensionner le logo pour qu'il soit plus petit
            pixmap = pixmap.scaled(48, 48, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_label.setPixmap(pixmap)
            logo_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(logo_label)
        
        # Titre
        title_label = QLabel("BarrelMCD")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #e0e0e0; margin: 5px;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # Sous-titre
        subtitle_label = QLabel("Modélisation Conceptuelle de Données")
        subtitle_label.setStyleSheet("font-size: 12px; color: #b0b0b0; margin: 5px;")
        subtitle_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle_label)
        
        # Séparateur
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet("background-color: #555555; border: none;")
        separator.setFixedHeight(1)
        layout.addWidget(separator)
        
        # Informations
        info_text = QLabel(
            "Version 1.0\n"
            "Créateur : Yglsan\n\n"
            "Un outil moderne pour la création et la gestion de modèles conceptuels de données.\n\n"
            "Fonctionnalités :\n"
            "• Création d'entités et d'associations\n"
            "• Export en multiples formats (.bar, .loo, .xml, .json, .sql)\n"
            "• Interface intuitive et responsive\n"
            "• Support multi-plateforme"
        )
        info_text.setWordWrap(True)
        info_text.setStyleSheet("margin: 10px; line-height: 1.4; color: #d0d0d0;")
        layout.addWidget(info_text)
        
        # Bouton Fermer
        close_button = QPushButton("Fermer")
        close_button.clicked.connect(about_dialog.accept)
        close_button.setFixedWidth(100)
        layout.addWidget(close_button, alignment=Qt.AlignCenter)
        
        about_dialog.exec_()

    def toggle_fullscreen(self):
        """Bascule entre le mode plein écran et la taille normale"""
        if self.isFullScreen():
            # Sortir du plein écran
            self.previous_geometry = self.geometry()
            super().showNormal()
            if self.previous_geometry:
                self.setGeometry(self.previous_geometry)
            self.is_fullscreen = False
        else:
            # Entrer en plein écran
            self.previous_geometry = self.geometry()
            super().showFullScreen()
            self.is_fullscreen = True

    def keyPressEvent(self, event):
        """Gère les événements de touches"""
        if event.key() == Qt.Key_F11:
            self.show_large_screen()
        elif event.key() == Qt.Key_F10:
            self.show_medium_screen()
        elif event.key() == Qt.Key_F9:
            self.show_small_screen()
        elif event.key() == Qt.Key_F12:
            self.toggle_fullscreen()
        elif event.key() == Qt.Key_Escape and self.isFullScreen():
            self.toggle_fullscreen()
        else:
            super().keyPressEvent(event)

    def mousePressEvent(self, event):
        """Transmet tous les événements au canvas"""
        self.canvas.mousePressEvent(event)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """Transmet tous les événements au canvas"""
        self.canvas.mouseMoveEvent(event)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """Transmet tous les événements au canvas"""
        self.canvas.mouseReleaseEvent(event)
        super().mouseReleaseEvent(event)

    def check_fullscreen_trigger(self):
        """Vérifie si on doit passer en plein écran"""
        if self.is_dragging and not self.isFullScreen():
            # Vérifier si la fenêtre touche le haut de l'écran
            screen_geometry = self.screen().geometry()
            window_geometry = self.geometry()
            
            # Conditions plus souples pour activer le plein écran
            if (window_geometry.y() <= 10 and 
                window_geometry.height() >= screen_geometry.height() * 0.7):
                self.toggle_fullscreen()

    def showMaximized(self):
        """Maximise la fenêtre (différent du plein écran)"""
        if self.isFullScreen():
            # Sortir du plein écran sans récursion
            self.previous_geometry = self.geometry()
            super().showNormal()
            if self.previous_geometry:
                self.setGeometry(self.previous_geometry)
            self.is_fullscreen = False
        super().showMaximized()

    def showNormal(self):
        """Restaure la taille normale (différent du plein écran)"""
        if self.isFullScreen():
            # Sortir du plein écran sans récursion
            self.previous_geometry = self.geometry()
            super().showNormal()
            self.is_fullscreen = False
        # Redimensionner à une taille vraiment plus petite que maximisé
        self.resize(600, 450)
        self.move(300, 150)  # Positionner la fenêtre
    
    def toggle_auto_connect(self):
        """Active/désactive la connexion automatique"""
        self.canvas.toggle_auto_connect()
    
    def optimize_connections(self):
        """Optimise toutes les connexions"""
        self.canvas.optimize_all_connections()
        stats = self.canvas.get_connection_stats()
        QMessageBox.information(self, "Optimisation terminée", 
            f"Connexions optimisées !\n\n"
            f"Statistiques :\n"
            f"- Entités : {stats['entities_count']}\n"
            f"- Associations : {stats['associations_count']}\n"
            f"- Connexions : {stats['total_connections']}\n"
            f"- Auto-détection : {'Activée' if stats['auto_detection_enabled'] else 'Désactivée'}")
    
    def show_large_screen(self):
        """Affiche en mode grand écran (80% de l'écran)"""
        if self.isFullScreen():
            self.toggle_fullscreen()
        
        screen = self.screen().geometry()
        width = int(screen.width() * 0.8)
        height = int(screen.height() * 0.8)
        x = (screen.width() - width) // 2
        y = (screen.height() - height) // 2
        
        self.setGeometry(x, y, width, height)
        self.showNormal()
    
    def show_medium_screen(self):
        """Affiche en mode écran moyen (60% de l'écran)"""
        if self.isFullScreen():
            self.toggle_fullscreen()
        
        screen = self.screen().geometry()
        width = int(screen.width() * 0.6)
        height = int(screen.height() * 0.6)
        x = (screen.width() - width) // 2
        y = (screen.height() - height) // 2
        
        self.setGeometry(x, y, width, height)
        self.showNormal()
    
    def show_small_screen(self):
        """Affiche en mode petit écran (40% de l'écran)"""
        if self.isFullScreen():
            self.toggle_fullscreen()
        
        screen = self.screen().geometry()
        width = int(screen.width() * 0.4)
        height = int(screen.height() * 0.4)
        x = (screen.width() - width) // 2
        y = (screen.height() - height) // 2
        
        self.setGeometry(x, y, width, height)
        self.showNormal()
    
    def toggle_properties_dock(self):
        """Affiche ou masque le panneau des propriétés"""
        if hasattr(self, 'properties_dock'):
            if self.properties_dock.isVisible():
                self.properties_dock.hide()
            else:
                self.properties_dock.show()
    
    def toggle_explorer_dock(self):
        """Affiche ou masque le panneau explorateur"""
        if hasattr(self, 'explorer_dock'):
            if self.explorer_dock.isVisible():
                self.explorer_dock.hide()
            else:
                self.explorer_dock.show()