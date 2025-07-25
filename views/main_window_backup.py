from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QFileDialog, QMessageBox, QLabel, QGraphicsView, QGraphicsScene, QInputDialog,
    QTextEdit, QDialog, QToolBar, QAction, QDockWidget, QListWidget, QSplitter, QFrame, QMenu, QMenuBar, QStatusBar
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon, QImage, QPainter, QKeySequence, QFont
from PyQt5.QtPrintSupport import QPrinter

from views.data_analyzer import DataAnalyzer
from views.model_converter import ModelConverter
from views.mcd_drawer import MCDDrawer
from views.sql_inspector import SQLInspector
from views.interactive_canvas import InteractiveCanvas
from views.dark_theme import DarkTheme

# Import des nouveaux gestionnaires
from models.history_manager import HistoryManager, HistoryActions
from models.shortcut_manager import ShortcutManager, Shortcuts
from models.clipboard_manager import ClipboardManager
from models.code_generator import CodeGenerator, CodeLanguage, ORMFramework, SQLDialect
from models.model_validator import ModelValidator
from models.export_manager import ExportManager, ExportFormat
from views.logo_manager import LogoManager
from PyQt5.QtPrintSupport import QPrinter

from views.data_analyzer import DataAnalyzer
from views.model_converter import ModelConverter
from views.mcd_drawer import MCDDrawer
from views.sql_inspector import SQLInspector
from views.interactive_canvas import InteractiveCanvas
from views.dark_theme import DarkTheme

class MainWindow(QMainWindow):

# Import des nouveaux gestionnaires
from models.history_manager import HistoryManager, HistoryActions
from models.shortcut_manager import ShortcutManager, Shortcuts
from models.clipboard_manager import ClipboardManager

from views.logo_manager import LogoManager
from models.code_generator import CodeGenerator, CodeLanguage, ORMFramework, SQLDialect
from models.model_validator import ModelValidator
from models.export_manager import ExportManager, ExportFormat
    """Fenêtre principale de l'application BarrelMCD."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("BarrelMCD - Modélisation Conceptuelle de Données")
        self.setMinimumSize(1400, 900)
        
        # Initialiser les composants
        self.data_analyzer = DataAnalyzer()
        self.model_converter = ModelConverter()

        # Gestionnaire de logos
        self.logo_manager = LogoManager()
        self.mcd_drawer = MCDDrawer()
        self.sql_inspector = SQLInspector()
        self.current_data = None
        self.current_format = None
        self.current_mcd = None

        # Nouveaux gestionnaires
        self.history_manager = HistoryManager()
        self.shortcut_manager = ShortcutManager(self)
        self.clipboard_manager = ClipboardManager()
        self.code_generator = CodeGenerator()
        self.model_validator = ModelValidator()
        self.export_manager = ExportManager()
        self.log_messages = []
        
        # Canvas interactif
        self.canvas = InteractiveCanvas()
        
        # Configurer l'interface
        self._setup_ui()
        self._setup_toolbar()
        self._setup_docks()
        
        # Connexion des signaux
        self._connect_signals()
        
    def _setup_ui(self):
        """Configure l'interface utilisateur."""
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Zone de dessin principale
        self.canvas.setMinimumSize(1000, 700)
        main_layout.addWidget(self.canvas)
        
    def _setup_toolbar(self):
        """Configure la barre d'outils principale"""
        toolbar = QToolBar("Outils principaux")
        toolbar.setIconSize(QSize(24, 24))
        toolbar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.addToolBar(toolbar)
        
        # Groupe d'outils de sélection
        select_action = QAction("Sélection", self)
        select_action.setShortcut(QKeySequence("S"))
        select_action.setToolTip("Mode sélection (S)")
        select_action.triggered.connect(lambda: self.canvas.set_mode("select"))
        toolbar.addAction(select_action)
        
        toolbar.addSeparator()
        
        # Groupe d'outils de création
        entity_action = QAction("Entité", self)
        entity_action.setShortcut(QKeySequence("E"))
        entity_action.setToolTip("Créer une entité (E)")
        entity_action.triggered.connect(lambda: self.canvas.set_mode("add_entity"))
        toolbar.addAction(entity_action)
        
        association_action = QAction("Association", self)
        association_action.setShortcut(QKeySequence("A"))
        association_action.setToolTip("Créer une association (A)")
        association_action.triggered.connect(lambda: self.canvas.set_mode("add_association"))
        toolbar.addAction(association_action)
        
        relation_action = QAction("Relation", self)
        relation_action.setShortcut(QKeySequence("R"))
        relation_action.setToolTip("Créer une relation (R)")
        relation_action.triggered.connect(lambda: self.canvas.set_mode("add_relation"))
        toolbar.addAction(relation_action)
        
        toolbar.addSeparator()
        
        # Groupe d'outils de navigation
        zoom_in_action = QAction("Zoom +", self)
        zoom_in_action.setShortcut(QKeySequence("Z"))
        zoom_in_action.setToolTip("Zoom avant (Z)")
        zoom_in_action.triggered.connect(self.canvas.zoom_in)
        toolbar.addAction(zoom_in_action)
        
        zoom_out_action = QAction("Zoom -", self)
        zoom_out_action.setShortcut(QKeySequence("X"))
        zoom_out_action.setToolTip("Zoom arrière (X)")
        zoom_out_action.triggered.connect(self.canvas.zoom_out)
        toolbar.addAction(zoom_out_action)
        
        fit_action = QAction("Ajuster", self)
        fit_action.setShortcut(QKeySequence("F"))
        fit_action.setToolTip("Ajuster à la vue (F)")
        fit_action.triggered.connect(self.canvas.fit_view)
        toolbar.addAction(fit_action)
        
        grid_action = QAction("Grille", self)
        grid_action.setShortcut(QKeySequence("G"))
        grid_action.setToolTip("Afficher/Masquer grille (G)")
        grid_action.triggered.connect(self.canvas.toggle_grid)
        toolbar.addAction(grid_action)
        
        toolbar.addSeparator()
        
        # Groupe d'outils d'édition
        delete_action = QAction("Supprimer", self)
        delete_action.setShortcut(QKeySequence("Delete"))
        delete_action.setToolTip("Supprimer la sélection (Delete)")
        delete_action.triggered.connect(self.canvas.delete_selected)
        toolbar.addAction(delete_action)
        
        undo_action = QAction("Annuler", self)
        undo_action.setShortcut(QKeySequence("Ctrl+Z"))
        undo_action.setToolTip("Annuler (Ctrl+Z)")
        undo_action.triggered.connect(self.canvas.undo)
        toolbar.addAction(undo_action)
        
        redo_action = QAction("Répéter", self)
        redo_action.setShortcut(QKeySequence("Ctrl+Y"))
        redo_action.setToolTip("Répéter (Ctrl+Y)")
        redo_action.triggered.connect(self.canvas.redo)
        toolbar.addAction(redo_action)
        
        toolbar.addSeparator()
        
        # Groupe d'outils d'import/export
        import_action = QAction("Importer", self)
        import_action.setShortcut(QKeySequence("Ctrl+O"))
        import_action.setToolTip("Importer des données (Ctrl+O)")
        import_action.triggered.connect(self._import_data)
        toolbar.addAction(import_action)
        
        export_sql_action = QAction("Exporter SQL", self)
        export_sql_action.setShortcut(QKeySequence("Ctrl+S"))
        export_sql_action.setToolTip("Exporter en SQL (Ctrl+S)")
        export_sql_action.triggered.connect(self._export_sql)
        toolbar.addAction(export_sql_action)
        
        export_png_action = QAction("Exporter PNG", self)
        export_png_action.setShortcut(QKeySequence("Ctrl+P"))
        export_png_action.setToolTip("Exporter en PNG (Ctrl+P)")
        export_png_action.triggered.connect(self._export_diagram)
        toolbar.addAction(export_png_action)
        
        export_pdf_action = QAction("Exporter PDF", self)
        export_pdf_action.setShortcut(QKeySequence("Ctrl+D"))
        export_pdf_action.setToolTip("Exporter en PDF (Ctrl+D)")
        export_pdf_action.triggered.connect(self._export_pdf)
        toolbar.addAction(export_pdf_action)
        
        toolbar.addSeparator()
        
        # Groupe d'outils d'aide
        help_action = QAction("Aide", self)
        help_action.setShortcut(QKeySequence("F1"))
        help_action.setToolTip("Aide (F1)")
        help_action.triggered.connect(self._show_help)
        toolbar.addAction(help_action)
        
        console_action = QAction("Console", self)
        console_action.setShortcut(QKeySequence("F2"))
        console_action.setToolTip("Console (F2)")
        console_action.triggered.connect(self._show_console)
        toolbar.addAction(console_action)
        
        # Actions d'export/import
        export_action = QAction("Exporter MCD", self)
        export_action.setToolTip("Exporter le MCD en JSON")
        export_action.triggered.connect(self.export_mcd)
        toolbar.addAction(export_action)
        
        import_action = QAction("Importer MCD", self)
        import_action.setToolTip("Importer un MCD depuis JSON")
        import_action.triggered.connect(self.import_mcd)
        toolbar.addAction(import_action)
        
        toolbar.addSeparator()
        
    def _setup_docks(self):
        """Configure les panneaux latéraux"""
        # Panneau des propriétés
        properties_dock = QDockWidget("Propriétés", self)
        properties_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
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
        explorer_widget = QWidget()
        explorer_layout = QVBoxLayout(explorer_widget)
        
        # Liste des éléments
        self.elements_list = QListWidget()
        explorer_layout.addWidget(QLabel("Éléments du diagramme:"))
        explorer_layout.addWidget(self.elements_list)
        
        explorer_dock.setWidget(explorer_widget)
        self.addDockWidget(Qt.LeftDockWidgetArea, explorer_dock)
        
    def _connect_signals(self):

        # Connexion des nouveaux signaux
        self._connect_history_signals()
        self._connect_shortcut_signals()
        self._setup_shortcuts()
        self._setup_menu()
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
            mcd = self.data_analyzer.analyze_data(self.current_data, format_type='json')
        elif self.current_format in ['csv', 'excel']:
            # Pour CSV/Excel, convertir en dictionnaire
            mcd = self.data_analyzer.analyze_data(self.current_data.to_dict(orient='records'), format_type='json')
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
            uml = self.model_converter.convert_model(self.current_mcd, self.model_converter.ConversionType.MCD_TO_UML)
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