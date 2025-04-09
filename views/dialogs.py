from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QTextEdit, QPushButton, QComboBox,
                             QCheckBox, QGroupBox, QFormLayout, QSpinBox,
                             QDoubleSpinBox, QMessageBox, QTabWidget, QWidget,
                             QSplitter)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QApplication
from models.attribute import Attribute
from models.data_types import DataType, DataTypeManager
from models.quantity_manager import QuantityManager, QuantityUnit
from models.sql_generator import SQLGenerator, SQLDialect

class ModelDialog(QDialog):
    """Dialogue pour créer ou modifier un modèle"""
    
    def __init__(self, parent=None, model=None):
        super().__init__(parent)
        self.model = model
        self.setup_ui()
        
    def setup_ui(self):
        """Configure l'interface utilisateur"""
        self.setWindowTitle("Nouveau modèle" if not self.model else "Modifier le modèle")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout(self)
        
        # Formulaire
        form_layout = QFormLayout()
        
        self.name_edit = QLineEdit()
        if self.model:
            self.name_edit.setText(self.model.name)
        form_layout.addRow("Nom:", self.name_edit)
        
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(100)
        if self.model:
            self.description_edit.setText(self.model.description)
        form_layout.addRow("Description:", self.description_edit)
        
        layout.addLayout(form_layout)
        
        # Boutons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_button = QPushButton("Annuler")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.accept)
        button_layout.addWidget(ok_button)
        
        layout.addLayout(button_layout)
        
    def get_model_name(self):
        """Récupère le nom du modèle"""
        return self.name_edit.text().strip()
        
    def get_model_description(self):
        """Récupère la description du modèle"""
        return self.description_edit.toPlainText().strip()

class AttributeDialog(QDialog):
    """Dialogue pour ajouter ou modifier un attribut"""
    
    def __init__(self, parent=None, attribute=None):
        super().__init__(parent)
        self.attribute = attribute
        self.data_type_manager = DataTypeManager()
        self.quantity_manager = QuantityManager()
        self.setup_ui()
        
    def setup_ui(self):
        """Configure l'interface utilisateur"""
        self.setWindowTitle("Nouvel attribut" if not self.attribute else "Modifier l'attribut")
        self.setMinimumWidth(500)
        
        layout = QVBoxLayout(self)
        
        # Formulaire
        form_layout = QFormLayout()
        
        self.name_edit = QLineEdit()
        if self.attribute:
            self.name_edit.setText(self.attribute.name)
        form_layout.addRow("Nom:", self.name_edit)
        
        self.data_type_combo = QComboBox()
        for data_type in self.data_type_manager.get_all_types():
            self.data_type_combo.addItem(data_type.name, data_type)
        if self.attribute:
            index = self.data_type_combo.findData(self.attribute.data_type)
            if index >= 0:
                self.data_type_combo.setCurrentIndex(index)
        self.data_type_combo.currentIndexChanged.connect(self._on_data_type_changed)
        form_layout.addWidget(QLabel("Type de données:"))
        form_layout.addWidget(self.data_type_combo)
        
        # Paramètres spécifiques au type
        self.type_params_group = QGroupBox("Paramètres du type")
        self.type_params_layout = QFormLayout(self.type_params_group)
        
        self.length_spin = QSpinBox()
        self.length_spin.setRange(1, 65535)
        self.length_spin.setValue(255)
        self.type_params_layout.addRow("Longueur:", self.length_spin)
        
        self.precision_spin = QSpinBox()
        self.precision_spin.setRange(1, 65)
        self.precision_spin.setValue(10)
        self.type_params_layout.addRow("Précision:", self.precision_spin)
        
        self.scale_spin = QSpinBox()
        self.scale_spin.setRange(0, 30)
        self.scale_spin.setValue(2)
        self.type_params_layout.addRow("Échelle:", self.scale_spin)
        
        layout.addLayout(form_layout)
        layout.addWidget(self.type_params_group)
        
        # Unité de mesure
        self.quantity_group = QGroupBox("Unité de mesure")
        self.quantity_layout = QFormLayout(self.quantity_group)
        
        self.unit_category_combo = QComboBox()
        for unit in QuantityUnit:
            self.unit_category_combo.addItem(unit.value, unit)
        self.unit_category_combo.currentIndexChanged.connect(self._on_unit_category_changed)
        self.quantity_layout.addRow("Catégorie:", self.unit_category_combo)
        
        self.unit_symbol_combo = QComboBox()
        self.quantity_layout.addRow("Unité:", self.unit_symbol_combo)
        
        # Contraintes de quantité
        self.quantity_constraints_group = QGroupBox("Contraintes de quantité")
        self.quantity_constraints_layout = QFormLayout(self.quantity_constraints_group)
        
        self.min_value_spin = QDoubleSpinBox()
        self.min_value_spin.setRange(-999999999, 999999999)
        self.quantity_constraints_layout.addRow("Valeur minimale:", self.min_value_spin)
        
        self.max_value_spin = QDoubleSpinBox()
        self.max_value_spin.setRange(-999999999, 999999999)
        self.max_value_spin.setValue(999999999)
        self.quantity_constraints_layout.addRow("Valeur maximale:", self.max_value_spin)
        
        self.precision_spin_quantity = QSpinBox()
        self.precision_spin_quantity.setRange(0, 10)
        self.precision_spin_quantity.setValue(2)
        self.quantity_constraints_layout.addRow("Précision:", self.precision_spin_quantity)
        
        layout.addWidget(self.quantity_group)
        layout.addWidget(self.quantity_constraints_group)
        
        # Contraintes
        self.constraints_group = QGroupBox("Contraintes")
        self.constraints_layout = QVBoxLayout(self.constraints_group)
        
        self.primary_key_check = QCheckBox("Clé primaire")
        self.constraints_layout.addWidget(self.primary_key_check)
        
        self.unique_check = QCheckBox("Unique")
        self.constraints_layout.addWidget(self.unique_check)
        
        self.not_null_check = QCheckBox("Non nul")
        self.constraints_layout.addWidget(self.not_null_check)
        
        self.default_edit = QLineEdit()
        self.constraints_layout.addWidget(QLabel("Valeur par défaut:"))
        self.constraints_layout.addWidget(self.default_edit)
        
        layout.addWidget(self.constraints_group)
        
        # Boutons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_button = QPushButton("Annuler")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.accept)
        button_layout.addWidget(ok_button)
        
        layout.addLayout(button_layout)
        
        # Initialisation
        self._on_data_type_changed()
        self._on_unit_category_changed()
        
        if self.attribute:
            self._load_attribute()
            
    def _on_data_type_changed(self):
        """Appelé lorsque le type de données change"""
        data_type = self.data_type_combo.currentData()
        
        # Affiche/masque les paramètres spécifiques au type
        has_length = data_type.name in ["VARCHAR", "CHAR", "TEXT", "BINARY", "VARBINARY"]
        has_precision = data_type.name in ["DECIMAL", "NUMERIC", "FLOAT", "DOUBLE"]
        
        self.length_spin.setVisible(has_length)
        self.type_params_layout.labelForField(self.length_spin).setVisible(has_length)
        
        self.precision_spin.setVisible(has_precision)
        self.type_params_layout.labelForField(self.precision_spin).setVisible(has_precision)
        
        self.scale_spin.setVisible(has_precision)
        self.type_params_layout.labelForField(self.scale_spin).setVisible(has_precision)
        
        # Active/désactive les groupes de quantité
        is_numeric = data_type.category in ["NUMERIC", "INTEGER"]
        self.quantity_group.setEnabled(is_numeric)
        self.quantity_constraints_group.setEnabled(is_numeric)
        
    def _on_unit_category_changed(self):
        """Appelé lorsque la catégorie d'unité change"""
        category = self.unit_category_combo.currentData()
        
        # Met à jour les unités disponibles
        self.unit_symbol_combo.clear()
        for unit in self.quantity_manager.get_units_by_category(category):
            self.unit_symbol_combo.addItem(f"{unit.name} ({unit.symbol})", unit)
            
    def _load_attribute(self):
        """Charge les données de l'attribut existant"""
        if not self.attribute:
            return
            
        # Type de données
        data_type = self.attribute.data_type
        index = self.data_type_combo.findData(data_type)
        if index >= 0:
            self.data_type_combo.setCurrentIndex(index)
            
        # Paramètres du type
        if hasattr(data_type, "length"):
            self.length_spin.setValue(data_type.length)
            
        if hasattr(data_type, "precision"):
            self.precision_spin.setValue(data_type.precision)
            
        if hasattr(data_type, "scale"):
            self.scale_spin.setValue(data_type.scale)
            
        # Unité de mesure
        if self.attribute.quantity_unit:
            category = self.attribute.quantity_unit.category
            index = self.unit_category_combo.findData(category)
            if index >= 0:
                self.unit_category_combo.setCurrentIndex(index)
                
            unit = self.attribute.quantity_unit
            index = self.unit_symbol_combo.findData(unit)
            if index >= 0:
                self.unit_symbol_combo.setCurrentIndex(index)
                
        # Contraintes de quantité
        if self.attribute.quantity_constraints:
            constraints = self.attribute.quantity_constraints
            if "min" in constraints:
                self.min_value_spin.setValue(constraints["min"])
            if "max" in constraints:
                self.max_value_spin.setValue(constraints["max"])
            if "precision" in constraints:
                self.precision_spin_quantity.setValue(constraints["precision"])
                
        # Contraintes
        self.primary_key_check.setChecked(self.attribute.is_primary_key)
        self.unique_check.setChecked(self.attribute.is_unique)
        self.not_null_check.setChecked(self.attribute.is_not_null)
        if self.attribute.default_value is not None:
            self.default_edit.setText(str(self.attribute.default_value))
            
    def get_attribute(self):
        """Récupère l'attribut configuré"""
        try:
            name = self.name_edit.text().strip()
            if not name:
                QMessageBox.warning(self, "Attention", "Le nom de l'attribut est requis.")
                return None
                
            data_type = self.data_type_combo.currentData()
            
            # Crée l'attribut
            attribute = Attribute(
                name=name,
                data_type=data_type
            )
            
            # Configure les paramètres du type
            if data_type.name in ["VARCHAR", "CHAR", "TEXT", "BINARY", "VARBINARY"]:
                attribute.set_length(self.length_spin.value())
                
            if data_type.name in ["DECIMAL", "NUMERIC", "FLOAT", "DOUBLE"]:
                attribute.set_precision(self.precision_spin.value())
                attribute.set_scale(self.scale_spin.value())
                
            # Configure l'unité de mesure
            if data_type.category in ["NUMERIC", "INTEGER"]:
                unit = self.unit_symbol_combo.currentData()
                if unit:
                    attribute.set_quantity_unit(unit)
                    
                    # Configure les contraintes de quantité
                    constraints = {}
                    if self.min_value_spin.value() > -999999999:
                        constraints["min"] = self.min_value_spin.value()
                    if self.max_value_spin.value() < 999999999:
                        constraints["max"] = self.max_value_spin.value()
                    if self.precision_spin_quantity.value() != 2:
                        constraints["precision"] = self.precision_spin_quantity.value()
                        
                    if constraints:
                        attribute.set_quantity_constraints(constraints)
                        
            # Configure les contraintes
            attribute.is_primary_key = self.primary_key_check.isChecked()
            attribute.is_unique = self.unique_check.isChecked()
            attribute.is_not_null = self.not_null_check.isChecked()
            
            default_value = self.default_edit.text().strip()
            if default_value:
                attribute.set_default_value(default_value)
                
            return attribute
            
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la création de l'attribut: {str(e)}")
            return None

class SQLTextEdit(QTextEdit):
    """Zone de texte personnalisée qui émet un signal lors des modifications"""
    textChanged = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.textChanged.connect(self._on_text_changed)
        
    def _on_text_changed(self):
        self.textChanged.emit()

class SQLConversionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.sql_generator = SQLGenerator()
        self.setup_ui()
        
    def setup_ui(self):
        """Configure l'interface utilisateur"""
        self.setWindowTitle("Conversion SQL")
        self.setMinimumSize(800, 600)
        
        # Layout principal
        layout = QVBoxLayout(self)
        
        # Sélection du dialecte source
        source_layout = QHBoxLayout()
        source_label = QLabel("Dialecte source:")
        self.source_dialect = QComboBox()
        for dialect in SQLDialect:
            self.source_dialect.addItem(dialect.value, dialect)
        self.source_dialect.setCurrentText(SQLDialect.MYSQL.value)
        source_layout.addWidget(source_label)
        source_layout.addWidget(self.source_dialect)
        layout.addLayout(source_layout)
        
        # Splitter pour le SQL source et les conversions
        splitter = QSplitter(Qt.Vertical)
        
        # Zone de SQL source
        source_widget = QWidget()
        source_layout = QVBoxLayout(source_widget)
        source_layout.setContentsMargins(0, 0, 0, 0)
        
        source_sql_label = QLabel("SQL source:")
        self.source_sql = SQLTextEdit()
        self.source_sql.textChanged.connect(self._on_source_sql_changed)
        
        source_layout.addWidget(source_sql_label)
        source_layout.addWidget(self.source_sql)
        splitter.addWidget(source_widget)
        
        # Onglets pour les dialectes cibles
        self.target_tabs = QTabWidget()
        self.target_sqls = {}
        
        for dialect in SQLDialect:
            if dialect != SQLDialect.MYSQL:  # Évite de convertir vers le même dialecte
                tab = QWidget()
                tab_layout = QVBoxLayout(tab)
                tab_layout.setContentsMargins(0, 0, 0, 0)
                
                sql_edit = QTextEdit()
                sql_edit.setReadOnly(True)
                
                button_layout = QHBoxLayout()
                copy_button = QPushButton("Copier")
                copy_button.clicked.connect(lambda checked, d=dialect: self._copy_to_clipboard(d))
                refresh_button = QPushButton("Actualiser")
                refresh_button.clicked.connect(lambda checked, d=dialect: self._refresh_sql(d))
                
                button_layout.addWidget(copy_button)
                button_layout.addWidget(refresh_button)
                button_layout.addStretch()
                
                tab_layout.addWidget(sql_edit)
                tab_layout.addLayout(button_layout)
                
                self.target_tabs.addTab(tab, dialect.value)
                self.target_sqls[dialect] = sql_edit
                
        splitter.addWidget(self.target_tabs)
        layout.addWidget(splitter)
        
        # Boutons de dialogue
        button_layout = QHBoxLayout()
        close_button = QPushButton("Fermer")
        close_button.clicked.connect(self.accept)
        button_layout.addStretch()
        button_layout.addWidget(close_button)
        layout.addLayout(button_layout)
        
        # Connexions
        self.source_dialect.currentIndexChanged.connect(self._on_source_dialect_changed)
        
    def _on_source_dialect_changed(self):
        """Appelé lorsque le dialecte source change"""
        self._refresh_all_sql()
        
    def _on_source_sql_changed(self):
        """Appelé lorsque le SQL source change"""
        self._refresh_all_sql()
        
    def _refresh_all_sql(self):
        """Actualise le SQL pour tous les dialectes cibles"""
        for dialect in self.target_sqls:
            self._refresh_sql(dialect)
            
    def _refresh_sql(self, target_dialect: SQLDialect):
        """Actualise le SQL pour un dialecte cible spécifique"""
        try:
            source_dialect = self.source_dialect.currentData()
            source_sql = self.source_sql.toPlainText()
            
            if source_sql.strip():
                converted_sql = self.sql_generator.convert_sql(
                    source_sql,
                    source_dialect,
                    target_dialect
                )
                self.target_sqls[target_dialect].setPlainText(converted_sql)
            else:
                self.target_sqls[target_dialect].clear()
                
        except Exception as e:
            self.target_sqls[target_dialect].setPlainText(f"Erreur de conversion: {str(e)}")
            
    def _copy_to_clipboard(self, dialect: SQLDialect):
        """Copie le SQL converti dans le presse-papiers"""
        sql = self.target_sqls[dialect].toPlainText()
        if sql:
            QApplication.clipboard().setText(sql)
            
    def get_sql_for_dialect(self, dialect: SQLDialect) -> str:
        """Récupère le SQL converti pour un dialecte spécifique"""
        return self.target_sqls[dialect].toPlainText() 