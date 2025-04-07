from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QFileDialog, QMessageBox, QLabel,
    QMenuBar, QMenu
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon

from .data_analyzer import DataAnalyzer
from .model_converter import ModelConverter
from .mcd_drawer import MCDDrawer
from .sql_inspector import SQLInspector
from .language_menu import LanguageMenu
from i18n import get_text

class MainWindow(QMainWindow):
    """Fenêtre principale de l'application BarrelMCD."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("BarrelMCD")
        self.setMinimumSize(1200, 800)
        
        # Initialiser les composants
        self.data_analyzer = DataAnalyzer()
        self.model_converter = ModelConverter()
        self.mcd_drawer = MCDDrawer()
        self.sql_inspector = SQLInspector()
        
        # Configurer l'interface
        self._setup_ui()
        self._setup_menu()
        
    def _setup_menu(self):
        """Configure la barre de menu"""
        menubar = self.menuBar()
        
        # Menu Fichier
        file_menu = menubar.addMenu(get_text("file"))
        file_menu.setObjectName("file_menu")
        
        # Menu Édition
        edit_menu = menubar.addMenu(get_text("edit"))
        edit_menu.setObjectName("edit_menu")
        
        # Menu Affichage
        view_menu = menubar.addMenu(get_text("view"))
        view_menu.setObjectName("view_menu")
        
        # Menu Langue
        self.language_menu = LanguageMenu(self)
        self.language_menu.language_changed.connect(self._on_language_changed)
        menubar.addMenu(self.language_menu)
        
        # Menu Aide
        help_menu = menubar.addMenu(get_text("help"))
        help_menu.setObjectName("help_menu")
        
    def _on_language_changed(self, lang_code: str):
        """Gère le changement de langue"""
        # Mettre à jour l'interface avec la nouvelle langue
        self._update_ui_texts()
        
    def _update_ui_texts(self):
        """Met à jour tous les textes de l'interface"""
        # Mettre à jour les titres des menus
        self.menuBar().findChild(QMenu, "file_menu").setTitle(get_text("file"))
        self.menuBar().findChild(QMenu, "edit_menu").setTitle(get_text("edit"))
        self.menuBar().findChild(QMenu, "view_menu").setTitle(get_text("view"))
        self.menuBar().findChild(QMenu, "help_menu").setTitle(get_text("help"))
        
        # Mettre à jour les textes des boutons
        for button in self.findChildren(QPushButton):
            if button.objectName() in translations:
                button.setText(get_text(button.objectName()))
                
        # Mettre à jour les labels
        for label in self.findChildren(QLabel):
            if label.objectName() in translations:
                label.setText(get_text(label.objectName()))
                
    def _setup_ui(self):
        """Configure l'interface utilisateur."""
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        main_layout = QVBoxLayout(central_widget)
        
        # Barre d'outils
        toolbar_layout = QHBoxLayout()
        
        # Boutons d'action
        import_btn = QPushButton(get_text("import"))
        import_btn.setObjectName("import")
        import_btn.clicked.connect(self._import_data)
        
        analyze_btn = QPushButton(get_text("analyze"))
        analyze_btn.setObjectName("analyze")
        analyze_btn.clicked.connect(self._analyze_data)
        
        convert_btn = QPushButton(get_text("convert"))
        convert_btn.setObjectName("convert")
        convert_btn.clicked.connect(self._convert_model)
        
        export_btn = QPushButton(get_text("export_sql"))
        export_btn.setObjectName("export_sql")
        export_btn.clicked.connect(self._export_sql)
        
        # Ajouter les boutons à la barre d'outils
        toolbar_layout.addWidget(import_btn)
        toolbar_layout.addWidget(analyze_btn)
        toolbar_layout.addWidget(convert_btn)
        toolbar_layout.addWidget(export_btn)
        toolbar_layout.addStretch()
        
        # Zone de dessin du MCD
        self.drawing_area = QWidget()
        self.drawing_area.setMinimumSize(800, 600)
        
        # Assembler le layout
        main_layout.addLayout(toolbar_layout)
        main_layout.addWidget(self.drawing_area)
        
    def _import_data(self):
        """Importe les données depuis un fichier."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Sélectionner un fichier",
            "",
            "Tous les fichiers (*);;JSON (*.json);;CSV (*.csv);;Excel (*.xlsx)"
        )
        if file_path:
            try:
                # TODO: Implémenter l'import des données
                QMessageBox.information(self, "Succès", "Données importées avec succès!")
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Erreur lors de l'import: {str(e)}")
    
    def _analyze_data(self):
        """Analyse les données pour générer le MCD."""
        try:
            # TODO: Implémenter l'analyse des données
            QMessageBox.information(self, "Succès", "Analyse terminée!")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de l'analyse: {str(e)}")
    
    def _convert_model(self):
        """Convertit le modèle vers UML ou MLD."""
        try:
            # TODO: Implémenter la conversion du modèle
            QMessageBox.information(self, "Succès", "Conversion effectuée!")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la conversion: {str(e)}")
    
    def _export_sql(self):
        """Exporte le modèle en SQL."""
        try:
            # TODO: Implémenter l'export SQL
            QMessageBox.information(self, "Succès", "Export SQL terminé!")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de l'export: {str(e)}") 