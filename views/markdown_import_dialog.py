#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Dialogue d'import Markdown pour BarrelMCD - Version Améliorée
Permet d'importer un fichier markdown et de générer un MCD avec précision accrue
"""

import os
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit,
    QLabel, QFileDialog, QMessageBox, QProgressBar, QTabWidget,
    QWidget, QSplitter, QListWidget, QListWidgetItem, QGroupBox,
    QFormLayout, QLineEdit, QComboBox, QCheckBox, QSpinBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QTextBrowser
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QTextCursor, QColor, QPalette

from views.markdown_mcd_parser import MarkdownMCDParser

class MarkdownImportDialog(QDialog):
    """Dialogue amélioré pour importer un fichier markdown et générer un MCD"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parser = MarkdownMCDParser()
        self.markdown_content = ""
        self.mcd_structure = None
        self.precision_score = 0.0
        self.setup_ui()
        
    def setup_ui(self):
        """Configure l'interface utilisateur améliorée"""
        self.setWindowTitle("Import Markdown - BarrelMCD (Version Améliorée)")
        self.setMinimumSize(1000, 700)
        
        # Layout principal
        layout = QVBoxLayout()
        
        # En-tête avec score de précision
        header_layout = QHBoxLayout()
        self.precision_label = QLabel("Score de précision: --")
        self.precision_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        header_layout.addWidget(self.precision_label)
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        
        # Créer les onglets
        self.tab_widget = QTabWidget()
        self.setup_file_tab()
        self.setup_editor_tab()
        self.setup_preview_tab()
        self.setup_validation_tab()
        self.setup_inheritance_tab()
        self.setup_analysis_tab()
        
        layout.addWidget(self.tab_widget)
        
        # Boutons d'action
        button_layout = QHBoxLayout()
        
        self.import_button = QPushButton("Importer le MCD")
        self.import_button.setEnabled(False)
        self.import_button.clicked.connect(self.import_mcd)
        self.import_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        
        self.cancel_button = QPushButton("Annuler")
        self.cancel_button.clicked.connect(self.reject)
        
        self.generate_template_button = QPushButton("Générer Template")
        self.generate_template_button.clicked.connect(self.generate_template)
        
        button_layout.addWidget(self.generate_template_button)
        button_layout.addStretch()
        layout.addWidget(QLabel(""))  # Espaceur
        button_layout.addWidget(self.import_button)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
    def setup_file_tab(self):
        """Configure l'onglet d'import de fichier amélioré"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Section de sélection de fichier
        file_group = QGroupBox("Sélection du fichier Markdown")
        file_layout = QVBoxLayout()
        
        # Bouton pour sélectionner le fichier
        self.select_file_button = QPushButton("Sélectionner un fichier Markdown")
        self.select_file_button.clicked.connect(self.select_file)
        file_layout.addWidget(self.select_file_button)
        
        # Label pour afficher le chemin du fichier
        self.file_path_label = QLabel("Aucun fichier sélectionné")
        self.file_path_label.setStyleSheet("color: gray; font-style: italic;")
        file_layout.addWidget(self.file_path_label)
        
        # Indicateur de qualité
        self.quality_indicator = QLabel("")
        self.quality_indicator.setStyleSheet("font-weight: bold; padding: 5px;")
        file_layout.addWidget(self.quality_indicator)
        
        file_group.setLayout(file_layout)
        layout.addWidget(file_group)
        
        # Section de prévisualisation
        preview_group = QGroupBox("Prévisualisation du contenu")
        preview_layout = QVBoxLayout()
        
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setMaximumHeight(300)
        preview_layout.addWidget(self.preview_text)
        
        preview_group.setLayout(preview_layout)
        layout.addWidget(preview_group)
        
        widget.setLayout(layout)
        self.tab_widget.addTab(widget, "📁 Fichier")
        
    def setup_editor_tab(self):
        """Configure l'onglet d'édition directe amélioré"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Instructions améliorées
        instructions = QLabel(
            "✏️ Éditeur Markdown - Syntaxe supportée:\n"
            "• ## Entité : Définit une entité\n"
            "• - attribut (type) PK/FK : description : Définit un attribut\n"
            "• ### Entité1 <-> Entité2 : Association : Définit une association\n"
            "• Entité1 : 1,1 / Entité2 : 0,n : Définit les cardinalités\n"
            "• ## Entité2 hérite de Entité1 : Définit l'héritage"
        )
        instructions.setStyleSheet("color: #666; padding: 10px; background-color: #f5f5f5; border-radius: 5px;")
        layout.addWidget(instructions)
        
        # Éditeur de texte avec coloration syntaxique
        self.editor_text = QTextEdit()
        self.editor_text.setFont(QFont("Courier", 10))
        self.editor_text.textChanged.connect(self.on_editor_text_changed)
        
        # Appliquer une coloration syntaxique basique
        self.apply_syntax_highlighting()
        
        layout.addWidget(self.editor_text)
        
        widget.setLayout(layout)
        self.tab_widget.addTab(widget, "✏️ Éditeur")
        
    def setup_preview_tab(self):
        """Configure l'onglet de prévisualisation amélioré"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Section des entités avec tableau détaillé
        entities_group = QGroupBox("🏗️ Entités détectées")
        entities_layout = QVBoxLayout()
        
        self.entities_table = QTableWidget()
        self.entities_table.setColumnCount(4)
        self.entities_table.setHorizontalHeaderLabels(["Entité", "Attributs", "Clé Primaire", "Héritage"])
        self.entities_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        entities_layout.addWidget(self.entities_table)
        
        entities_group.setLayout(entities_layout)
        layout.addWidget(entities_group)
        
        # Section des associations avec tableau détaillé
        associations_group = QGroupBox("🔗 Associations détectées")
        associations_layout = QVBoxLayout()
        
        self.associations_table = QTableWidget()
        self.associations_table.setColumnCount(5)
        self.associations_table.setHorizontalHeaderLabels(["Association", "Entité1", "Cardinalité1", "Entité2", "Cardinalité2"])
        self.associations_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        associations_layout.addWidget(self.associations_table)
        
        associations_group.setLayout(associations_layout)
        layout.addWidget(associations_group)
        
        widget.setLayout(layout)
        self.tab_widget.addTab(widget, "👁️ Prévisualisation")
        
    def setup_validation_tab(self):
        """Configure l'onglet de validation amélioré"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Section de validation avec détails
        validation_group = QGroupBox("✅ Validation du MCD")
        validation_layout = QVBoxLayout()
        
        self.validation_text = QTextBrowser()
        validation_layout.addWidget(self.validation_text)
        
        validation_group.setLayout(validation_layout)
        layout.addWidget(validation_group)
        
        # Section de statistiques détaillées
        stats_group = QGroupBox("📊 Statistiques détaillées")
        stats_layout = QFormLayout()
        
        self.entities_count_label = QLabel("0")
        self.associations_count_label = QLabel("0")
        self.attributes_count_label = QLabel("0")
        self.inheritance_count_label = QLabel("0")
        self.foreign_keys_count_label = QLabel("0")
        
        stats_layout.addRow("Nombre d'entités:", self.entities_count_label)
        stats_layout.addRow("Nombre d'associations:", self.associations_count_label)
        stats_layout.addRow("Nombre d'attributs:", self.attributes_count_label)
        stats_layout.addRow("Relations d'héritage:", self.inheritance_count_label)
        stats_layout.addRow("Clés étrangères:", self.foreign_keys_count_label)
        
        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)
        
        widget.setLayout(layout)
        self.tab_widget.addTab(widget, "✅ Validation")
        
    def setup_inheritance_tab(self):
        """Configure l'onglet d'héritage"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Section d'héritage
        inheritance_group = QGroupBox("🔄 Hiérarchie d'héritage")
        inheritance_layout = QVBoxLayout()
        
        self.inheritance_text = QTextBrowser()
        inheritance_layout.addWidget(self.inheritance_text)
        
        inheritance_group.setLayout(inheritance_layout)
        layout.addWidget(inheritance_group)
        
        widget.setLayout(layout)
        self.tab_widget.addTab(widget, "🔄 Héritage")
        
    def setup_analysis_tab(self):
        """Configure l'onglet d'analyse"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Section d'analyse
        analysis_group = QGroupBox("🔍 Analyse de qualité")
        analysis_layout = QVBoxLayout()
        
        self.analysis_text = QTextBrowser()
        analysis_layout.addWidget(self.analysis_text)
        
        analysis_group.setLayout(analysis_layout)
        layout.addWidget(analysis_group)
        
        widget.setLayout(layout)
        self.tab_widget.addTab(widget, "🔍 Analyse")
        
    def apply_syntax_highlighting(self):
        """Applique une coloration syntaxique basique"""
        # Cette fonction pourrait être étendue pour une vraie coloration syntaxique
        pass
        
    def select_file(self):
        """Sélectionne un fichier markdown"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Sélectionner un fichier Markdown",
            "",
            "Fichiers Markdown (*.md *.markdown);;Tous les fichiers (*)"
        )
        
        if file_path:
            self.load_file(file_path)
            
    def load_file(self, file_path):
        """Charge un fichier markdown"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            self.markdown_content = content
            self.file_path_label.setText(f"Fichier: {os.path.basename(file_path)}")
            self.preview_text.setPlainText(content)
            self.editor_text.setPlainText(content)
            
            self.parse_markdown()
            
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Impossible de charger le fichier: {str(e)}")
            
    def on_editor_text_changed(self):
        """Appelé quand le texte de l'éditeur change"""
        content = self.editor_text.toPlainText()
        if content != self.markdown_content:
            self.markdown_content = content
            self.parse_markdown()
            
    def parse_markdown(self):
        """Parse le contenu markdown et met à jour l'interface"""
        if not self.markdown_content.strip():
            self.clear_preview()
            return
            
        try:
            # Parser le markdown
            self.mcd_structure = self.parser.parse_markdown(self.markdown_content)
            
            # Récupérer le score de précision
            self.precision_score = self.mcd_structure.get('metadata', {}).get('precision_score', 0.0)
            
            # Mettre à jour la prévisualisation
            self.update_preview()
            
            # Valider le MCD
            self.validate_mcd()
            
            # Mettre à jour l'indicateur de qualité
            self.update_quality_indicator()
            
            # Activer le bouton d'import
            self.import_button.setEnabled(True)
            
        except Exception as e:
            QMessageBox.warning(self, "Erreur de parsing", f"Erreur lors du parsing: {str(e)}")
            self.clear_preview()
            
    def update_preview(self):
        """Met à jour la prévisualisation du MCD améliorée"""
        if not self.mcd_structure:
            return
            
        # Mettre à jour le tableau des entités
        self.update_entities_table()
        
        # Mettre à jour le tableau des associations
        self.update_associations_table()
        
        # Mettre à jour les statistiques
        self.update_statistics()
        
        # Mettre à jour l'héritage
        self.update_inheritance_display()
        
        # Mettre à jour l'analyse
        self.update_analysis()
        
    def update_entities_table(self):
        """Met à jour le tableau des entités"""
        self.entities_table.setRowCount(0)
        
        for entity_name, entity in self.mcd_structure['entities'].items():
            row = self.entities_table.rowCount()
            self.entities_table.insertRow(row)
            
            # Nom de l'entité
            self.entities_table.setItem(row, 0, QTableWidgetItem(entity_name))
            
            # Nombre d'attributs
            attr_count = len(entity['attributes'])
            self.entities_table.setItem(row, 1, QTableWidgetItem(str(attr_count)))
            
            # Clé primaire
            pk = entity.get('primary_key', 'Aucune')
            self.entities_table.setItem(row, 2, QTableWidgetItem(pk))
            
            # Héritage
            parent = entity.get('parent', '')
            self.entities_table.setItem(row, 3, QTableWidgetItem(parent))
            
    def update_associations_table(self):
        """Met à jour le tableau des associations"""
        self.associations_table.setRowCount(0)
        
        for association in self.mcd_structure['associations']:
            row = self.associations_table.rowCount()
            self.associations_table.insertRow(row)
            
            # Nom de l'association
            self.associations_table.setItem(row, 0, QTableWidgetItem(association['name']))
            
            # Entité1
            self.associations_table.setItem(row, 1, QTableWidgetItem(association['entity1']))
            
            # Cardinalité1
            self.associations_table.setItem(row, 2, QTableWidgetItem(association['cardinality1']))
            
            # Entité2
            self.associations_table.setItem(row, 3, QTableWidgetItem(association['entity2']))
            
            # Cardinalité2
            self.associations_table.setItem(row, 4, QTableWidgetItem(association['cardinality2']))
            
    def update_statistics(self):
        """Met à jour les statistiques détaillées"""
        if not self.mcd_structure:
            return
            
        # Compter les éléments
        total_attributes = sum(len(entity['attributes']) for entity in self.mcd_structure['entities'].values())
        inheritance_count = len(self.mcd_structure.get('inheritance', {}))
        foreign_keys_count = sum(
            1 for entity in self.mcd_structure['entities'].values()
            for attr in entity['attributes']
            if attr.get('is_foreign_key', False)
        )
        
        self.entities_count_label.setText(str(len(self.mcd_structure['entities'])))
        self.associations_count_label.setText(str(len(self.mcd_structure['associations'])))
        self.attributes_count_label.setText(str(total_attributes))
        self.inheritance_count_label.setText(str(inheritance_count))
        self.foreign_keys_count_label.setText(str(foreign_keys_count))
        
    def update_inheritance_display(self):
        """Met à jour l'affichage de l'héritage"""
        if not self.mcd_structure:
            return
            
        inheritance_text = ""
        inheritance = self.mcd_structure.get('inheritance', {})
        
        if inheritance:
            inheritance_text = "🔄 Hiérarchie d'héritage:\n\n"
            for child, parent in inheritance.items():
                inheritance_text += f"• {child} hérite de {parent}\n"
        else:
            inheritance_text = "Aucune relation d'héritage détectée."
            
        self.inheritance_text.setPlainText(inheritance_text)
        
    def update_analysis(self):
        """Met à jour l'analyse de qualité"""
        if not self.mcd_structure:
            return
            
        analysis_text = f"🔍 Analyse de qualité\n\n"
        analysis_text += f"Score de précision: {self.precision_score:.1f}%\n\n"
        
        # Analyse des entités
        entities_with_pk = sum(1 for entity in self.mcd_structure['entities'].values() if entity.get('primary_key'))
        analysis_text += f"Entités avec clé primaire: {entities_with_pk}/{len(self.mcd_structure['entities'])}\n"
        
        # Analyse des associations
        valid_cardinalities = sum(
            1 for assoc in self.mcd_structure['associations']
            if self.parser._is_cardinality_improved(assoc['cardinality1']) and 
               self.parser._is_cardinality_improved(assoc['cardinality2'])
        )
        analysis_text += f"Associations avec cardinalités valides: {valid_cardinalities}/{len(self.mcd_structure['associations'])}\n"
        
        # Analyse des attributs
        total_attrs = sum(len(entity['attributes']) for entity in self.mcd_structure['entities'].values())
        fk_attrs = sum(
            1 for entity in self.mcd_structure['entities'].values()
            for attr in entity['attributes']
            if attr.get('is_foreign_key', False)
        )
        analysis_text += f"Attributs clés étrangères: {fk_attrs}/{total_attrs}\n"
        
        self.analysis_text.setPlainText(analysis_text)
        
    def update_quality_indicator(self):
        """Met à jour l'indicateur de qualité"""
        if self.precision_score >= 90:
            self.quality_indicator.setText("🟢 Excellente qualité")
            self.quality_indicator.setStyleSheet("color: green; font-weight: bold; padding: 5px;")
        elif self.precision_score >= 75:
            self.quality_indicator.setText("🟡 Bonne qualité")
            self.quality_indicator.setStyleSheet("color: orange; font-weight: bold; padding: 5px;")
        elif self.precision_score >= 60:
            self.quality_indicator.setText("🟠 Qualité moyenne")
            self.quality_indicator.setStyleSheet("color: #FF8C00; font-weight: bold; padding: 5px;")
        else:
            self.quality_indicator.setText("🔴 Qualité insuffisante")
            self.quality_indicator.setStyleSheet("color: red; font-weight: bold; padding: 5px;")
            
        # Mettre à jour le label principal
        self.precision_label.setText(f"Score de précision: {self.precision_score:.1f}%")
        
    def clear_preview(self):
        """Efface la prévisualisation"""
        self.entities_table.setRowCount(0)
        self.associations_table.setRowCount(0)
        self.entities_count_label.setText("0")
        self.associations_count_label.setText("0")
        self.attributes_count_label.setText("0")
        self.inheritance_count_label.setText("0")
        self.foreign_keys_count_label.setText("0")
        self.validation_text.clear()
        self.inheritance_text.clear()
        self.analysis_text.clear()
        self.import_button.setEnabled(False)
        self.quality_indicator.setText("")
        self.precision_label.setText("Score de précision: --")
        
    def validate_mcd(self):
        """Valide le MCD et affiche les erreurs améliorées"""
        if not self.mcd_structure:
            return
            
        errors = self.parser.validate_mcd(self.mcd_structure)
        
        validation_text = f"✅ Validation du MCD\n\n"
        validation_text += f"Score de précision: {self.precision_score:.1f}%\n\n"
        
        if errors:
            validation_text += "❌ Erreurs de validation:\n\n"
            for error in errors:
                validation_text += f"• {error}\n"
            self.validation_text.setStyleSheet("color: red;")
        else:
            validation_text += "✅ MCD valide !\n\n"
            validation_text += "Toutes les règles CIF/CIFF sont respectées.\n"
            validation_text += "Les cardinalités sont valides.\n"
            validation_text += "Aucun cycle d'héritage détecté."
            self.validation_text.setStyleSheet("color: green;")
            
        self.validation_text.setPlainText(validation_text)
            
    def generate_template(self):
        """Génère un template markdown amélioré"""
        template = self.parser.generate_markdown_template()
        self.editor_text.setPlainText(template)
        self.tab_widget.setCurrentIndex(1)  # Aller à l'onglet éditeur
        
    def import_mcd(self):
        """Importe le MCD dans l'application principale"""
        if not self.mcd_structure:
            QMessageBox.warning(self, "Erreur", "Aucun MCD à importer")
            return
            
        # Valider une dernière fois
        errors = self.parser.validate_mcd(self.mcd_structure)
        if errors:
            reply = QMessageBox.question(
                self,
                "Validation échouée",
                f"Le MCD contient {len(errors)} erreur(s). Voulez-vous continuer quand même ?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.No:
                return
                
        # Accepter le dialogue
        self.accept()
        
    def get_mcd_structure(self):
        """Retourne la structure MCD parsée"""
        return self.mcd_structure 