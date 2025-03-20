from PyQt6.QtWidgets import (QMainWindow, QDockWidget, QMenuBar, QStatusBar,
                             QMessageBox, QFileDialog, QToolBar, QDialog,
                             QVBoxLayout, QComboBox, QPushButton, QLabel)
from PyQt6.QtCore import Qt
from .canvas import DiagramCanvas
from .help_toolbar import HelpToolBar
from .documentation import DocumentationGenerator
from .error_handler import ErrorHandler
from .sql_generator import SQLGenerator, SQLDialect
import os

class SQLDialectDialog(QDialog):
    """Boîte de dialogue pour sélectionner le dialecte SQL"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Sélectionner le dialecte SQL")
        self.setup_ui()
        
    def setup_ui(self):
        """Configure l'interface de la boîte de dialogue"""
        layout = QVBoxLayout(self)
        
        # Label explicatif
        layout.addWidget(QLabel("Choisissez le dialecte SQL pour la génération :"))
        
        # Liste déroulante des dialectes
        self.dialect_combo = QComboBox()
        for dialect in SQLDialect:
            self.dialect_combo.addItem(dialect.value, dialect)
        layout.addWidget(self.dialect_combo)
        
        # Boutons
        button_layout = QHBoxLayout()
        ok_button = QPushButton("OK")
        cancel_button = QPushButton("Annuler")
        
        ok_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)
        
    def get_selected_dialect(self) -> SQLDialect:
        """Retourne le dialecte SQL sélectionné"""
        return self.dialect_combo.currentData()

class MainWindow(QMainWindow):
    """Fenêtre principale de l'application"""
    
    def __init__(self):
        super().__init__()
        self.error_handler = ErrorHandler(self)
        self.sql_generator = SQLGenerator()
        self.setup_ui()
        
    def setup_ui(self):
        """Configure l'interface utilisateur"""
        try:
            # Configuration de la fenêtre
            self.setWindowTitle("Barrel MCD")
            self.setMinimumSize(800, 600)
            
            # Zone de dessin
            self.canvas = DiagramCanvas(self)
            self.setCentralWidget(self.canvas)
            
            # Barre d'outils d'aide
            self.help_toolbar = HelpToolBar(self)
            self.addToolBar(self.help_toolbar)
            
            # Barre de menu
            self.setup_menu_bar()
            
            # Barre de statut
            self.status_bar = QStatusBar()
            self.setStatusBar(self.status_bar)
            self.status_bar.showMessage("Prêt")
            
            # Connexion des signaux
            self.canvas.diagram_modified.connect(self._on_diagram_modified)
            
        except Exception as e:
            self.error_handler.handle_error(e, "Erreur lors de la configuration de l'interface")
            
    def setup_menu_bar(self):
        """Configure la barre de menu"""
        try:
            menubar = self.menuBar()
            
            # Menu Fichier
            file_menu = menubar.addMenu("Fichier")
            file_menu.addAction("Nouveau", self._new_diagram, "Ctrl+N")
            file_menu.addAction("Ouvrir", self._open_diagram, "Ctrl+O")
            file_menu.addAction("Enregistrer", self._save_diagram, "Ctrl+S")
            file_menu.addSeparator()
            file_menu.addAction("Quitter", self.close, "Ctrl+Q")
            
            # Menu Édition
            edit_menu = menubar.addMenu("Édition")
            edit_menu.addAction("Annuler", self.canvas.undo, "Ctrl+Z")
            edit_menu.addAction("Rétablir", self.canvas.redo, "Ctrl+Y")
            edit_menu.addSeparator()
            edit_menu.addAction("Supprimer", self.canvas.delete_selected, "Suppr")
            
            # Menu Affichage
            view_menu = menubar.addMenu("Affichage")
            view_menu.addAction("Zoom avant", self.canvas.zoom_in, "Ctrl++")
            view_menu.addAction("Zoom arrière", self.canvas.zoom_out, "Ctrl+-")
            view_menu.addAction("Ajuster", self.canvas.fit_view, "Ctrl+0")
            view_menu.addSeparator()
            view_menu.addAction("Grille", self.canvas.toggle_grid, "Ctrl+G")
            
            # Menu Aide
            help_menu = menubar.addMenu("Aide")
            help_menu.addAction("Aide rapide", self.canvas.show_quick_help, "F1")
            help_menu.addSeparator()
            help_menu.addAction("À propos", self._show_about)
            
            # Menu Documentation
            doc_menu = menubar.addMenu("Documentation")
            doc_menu.addAction("Générer la documentation", self._generate_documentation)
            
            # Menu SQL
            sql_menu = menubar.addMenu("SQL")
            sql_menu.addAction("Générer le script SQL", self._generate_sql)
            
        except Exception as e:
            self.error_handler.handle_error(e, "Erreur lors de la configuration de la barre de menu")
            
    def _new_diagram(self):
        """Crée un nouveau diagramme"""
        try:
            if self.canvas.is_modified():
                reply = QMessageBox.question(
                    self,
                    "Nouveau diagramme",
                    "Le diagramme actuel a été modifié. Voulez-vous le sauvegarder ?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel
                )
                
                if reply == QMessageBox.StandardButton.Cancel:
                    return
                elif reply == QMessageBox.StandardButton.Yes:
                    if not self._save_diagram():
                        return
                        
            self.canvas.clear()
            self.status_bar.showMessage("Nouveau diagramme créé")
            
        except Exception as e:
            self.error_handler.handle_error(e, "Erreur lors de la création d'un nouveau diagramme")
            
    def _open_diagram(self):
        """Ouvre un diagramme existant"""
        try:
            if self.canvas.is_modified():
                reply = QMessageBox.question(
                    self,
                    "Ouvrir un diagramme",
                    "Le diagramme actuel a été modifié. Voulez-vous le sauvegarder ?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel
                )
                
                if reply == QMessageBox.StandardButton.Cancel:
                    return
                elif reply == QMessageBox.StandardButton.Yes:
                    if not self._save_diagram():
                        return
                        
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Ouvrir un diagramme",
                "",
                "Diagrammes (*.json);;Tous les fichiers (*.*)"
            )
            
            if file_path:
                self.canvas.load_diagram(file_path)
                self.status_bar.showMessage(f"Diagramme chargé : {file_path}")
                
        except Exception as e:
            self.error_handler.handle_error(e, "Erreur lors de l'ouverture du diagramme")
            
    def _save_diagram(self) -> bool:
        """Sauvegarde le diagramme actuel"""
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Enregistrer le diagramme",
                "",
                "Diagrammes (*.json);;Tous les fichiers (*.*)"
            )
            
            if file_path:
                self.canvas.save_diagram(file_path)
                self.status_bar.showMessage(f"Diagramme sauvegardé : {file_path}")
                return True
                
            return False
            
        except Exception as e:
            self.error_handler.handle_error(e, "Erreur lors de la sauvegarde du diagramme")
            return False
            
    def _show_about(self):
        """Affiche la boîte de dialogue À propos"""
        try:
            QMessageBox.about(
                self,
                "À propos de Barrel MCD",
                "Barrel MCD est un outil de conception de modèles de données conceptuels.\n\n"
                "Version 1.0.0\n"
                "© 2024 Barrel MCD"
            )
            
        except Exception as e:
            self.error_handler.handle_error(e, "Erreur lors de l'affichage de la boîte de dialogue À propos")
            
    def _generate_documentation(self):
        """Génère la documentation du diagramme"""
        try:
            output_dir = QFileDialog.getExistingDirectory(
                self,
                "Sélectionner le répertoire de sortie",
                ""
            )
            
            if output_dir:
                generator = DocumentationGenerator(self)
                generator.documentation_generated.connect(self._on_documentation_generated)
                generator.error_occurred.connect(self._on_documentation_error)
                generator.generate_documentation(
                    self.canvas.get_entities(),
                    self.canvas.get_associations(),
                    output_dir
                )
                
        except Exception as e:
            self.error_handler.handle_error(e, "Erreur lors de la génération de la documentation")
            
    def _on_documentation_generated(self, output_dir: str):
        """Gère la génération réussie de la documentation"""
        try:
            QMessageBox.information(
                self,
                "Documentation générée",
                f"La documentation a été générée dans le répertoire :\n{output_dir}"
            )
            
        except Exception as e:
            self.error_handler.handle_error(e, "Erreur lors de la notification de génération de documentation")
            
    def _on_documentation_error(self, error: str):
        """Gère l'erreur de génération de documentation"""
        try:
            QMessageBox.critical(
                self,
                "Erreur de génération",
                f"Une erreur est survenue lors de la génération de la documentation :\n{error}"
            )
            
        except Exception as e:
            self.error_handler.handle_error(e, "Erreur lors de la notification d'erreur de documentation")
            
    def _on_diagram_modified(self):
        """Gère la modification du diagramme"""
        try:
            self.status_bar.showMessage("Diagramme modifié")
            
        except Exception as e:
            self.error_handler.handle_error(e, "Erreur lors de la notification de modification")
            
    def _generate_sql(self):
        """Génère le script SQL à partir du modèle de données."""
        try:
            # Vérifier si le diagramme est modifié
            if self.canvas.is_modified():
                reply = QMessageBox.question(
                    self,
                    "Diagramme modifié",
                    "Le diagramme a été modifié. Voulez-vous l'enregistrer avant de générer le SQL ?",
                    QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel
                )
                
                if reply == QMessageBox.Save:
                    if not self._save_diagram():
                        return
                elif reply == QMessageBox.Cancel:
                    return
            
            # Sélectionner le dialecte SQL
            dialect_dialog = SQLDialectDialog(self)
            if dialect_dialog.exec() != QDialog.DialogCode.Accepted:
                return
                
            selected_dialect = dialect_dialog.get_selected_dialect()
            self.sql_generator.set_dialect(selected_dialect)
            
            # Sélectionner le répertoire de sortie
            output_dir = QFileDialog.getExistingDirectory(
                self,
                "Sélectionner le répertoire de sortie",
                os.path.expanduser("~")
            )
            
            if output_dir:
                # Récupérer les entités et associations du canvas
                entities = self.canvas.get_entities()
                associations = self.canvas.get_associations()
                
                # Générer le script SQL
                self.sql_generator.generate_sql(entities, associations, output_dir)
                self.status_bar.showMessage("Génération du script SQL en cours...")
                
        except Exception as e:
            self.error_handler.handle_error(e, "Erreur lors de la génération du script SQL")
    
    def _on_sql_generated(self, sql_file: str):
        """Gère la fin de la génération du script SQL.
        
        Args:
            sql_file: Chemin du fichier SQL généré
        """
        self.status_bar.showMessage(f"Script SQL généré : {sql_file}")
        QMessageBox.information(
            self,
            "Succès",
            f"Le script SQL a été généré avec succès dans :\n{sql_file}"
        )
    
    def _on_sql_error(self, error_msg: str):
        """Gère les erreurs lors de la génération du script SQL.
        
        Args:
            error_msg: Message d'erreur
        """
        self.status_bar.showMessage("Erreur lors de la génération du script SQL")
        QMessageBox.critical(
            self,
            "Erreur",
            f"Une erreur est survenue lors de la génération du script SQL :\n{error_msg}"
        ) 