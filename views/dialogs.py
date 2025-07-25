from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QComboBox, QCheckBox, QPushButton,
                             QFormLayout, QSpinBox)
from PyQt6.QtCore import Qt
from ..models.attribute import Attribute
from .error_handler import ErrorHandler

class AttributeDialog(QDialog):
    """Dialogue pour ajouter/modifier un attribut"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.error_handler = ErrorHandler(self)
        self.setup_ui()
        
    def setup_ui(self):
        """Configure l'interface utilisateur"""
        try:
            self.setWindowTitle("Attribut")
            self.setModal(True)
            
            layout = QFormLayout()
            
            # Nom de l'attribut
            self.name_edit = QLineEdit()
            layout.addRow("Nom:", self.name_edit)
            
            # Type de données
            self.type_combo = QComboBox()
            self.type_combo.addItems([
                "VARCHAR",
                "CHAR",
                "TEXT",
                "INTEGER",
                "FLOAT",
                "DECIMAL",
                "DATE",
                "DATETIME",
                "BOOLEAN"
            ])
            layout.addRow("Type:", self.type_combo)
            
            # Taille (pour VARCHAR et CHAR)
            self.size_spin = QSpinBox()
            self.size_spin.setRange(1, 255)
            self.size_spin.setValue(50)
            layout.addRow("Taille:", self.size_spin)
            
            # Options
            self.primary_key_check = QCheckBox("Clé primaire")
            self.unique_check = QCheckBox("Unique")
            self.not_null_check = QCheckBox("Non nul")
            layout.addRow("", self.primary_key_check)
            layout.addRow("", self.unique_check)
            layout.addRow("", self.not_null_check)
            
            # Boutons
            button_layout = QHBoxLayout()
            ok_button = QPushButton("OK")
            cancel_button = QPushButton("Annuler")
            button_layout.addWidget(ok_button)
            button_layout.addWidget(cancel_button)
            layout.addRow("", button_layout)
            
            # Connexions
            ok_button.clicked.connect(self.accept)
            cancel_button.clicked.connect(self.reject)
            self.type_combo.currentTextChanged.connect(self._on_type_changed)
            
            self.setLayout(layout)
            
        except Exception as e:
            self.error_handler.handle_error(e, "Erreur lors de la configuration de l'interface")
            
    def _on_type_changed(self, type_name: str):
        """Gère le changement de type"""
        try:
            self.size_spin.setEnabled(type_name in ["VARCHAR", "CHAR"])
            
        except Exception as e:
            self.error_handler.handle_error(e, "Erreur lors du changement de type")
            
    def get_attribute(self) -> Attribute:
        """Récupère l'attribut configuré"""
        try:
            name = self.name_edit.text()
            data_type = self.type_combo.currentText()
            
            if data_type in ["VARCHAR", "CHAR"]:
                data_type = f"{data_type}({self.size_spin.value()})"
                
            return Attribute(
                name=name,
                data_type=data_type,
                is_primary_key=self.primary_key_check.isChecked(),
                is_unique=self.unique_check.isChecked(),
                is_not_null=self.not_null_check.isChecked()
            )
            
        except Exception as e:
            self.error_handler.handle_error(e, "Erreur lors de la récupération de l'attribut")
            return None
            
class CardinalityDialog(QDialog):
    """Dialogue pour modifier la cardinalité d'une association"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.error_handler = ErrorHandler(self)
        self.setup_ui()
        
    def setup_ui(self):
        """Configure l'interface utilisateur"""
        try:
            self.setWindowTitle("Cardinalité")
            self.setModal(True)
            
            layout = QFormLayout()
            
            # Cardinalité source
            source_layout = QHBoxLayout()
            self.source_min = QSpinBox()
            self.source_min.setRange(0, 1)
            self.source_min.setValue(1)
            self.source_max = QComboBox()
            self.source_max.addItems(["1", "n"])
            source_layout.addWidget(self.source_min)
            source_layout.addWidget(QLabel(","))
            source_layout.addWidget(self.source_max)
            layout.addRow("Source:", source_layout)
            
            # Cardinalité cible
            target_layout = QHBoxLayout()
            self.target_min = QSpinBox()
            self.target_min.setRange(0, 1)
            self.target_min.setValue(1)
            self.target_max = QComboBox()
            self.target_max.addItems(["1", "n"])
            target_layout.addWidget(self.target_min)
            target_layout.addWidget(QLabel(","))
            target_layout.addWidget(self.target_max)
            layout.addRow("Cible:", target_layout)
            
            # Boutons
            button_layout = QHBoxLayout()
            ok_button = QPushButton("OK")
            cancel_button = QPushButton("Annuler")
            button_layout.addWidget(ok_button)
            button_layout.addWidget(cancel_button)
            layout.addRow("", button_layout)
            
            # Connexions
            ok_button.clicked.connect(self.accept)
            cancel_button.clicked.connect(self.reject)
            
            self.setLayout(layout)
            
        except Exception as e:
            self.error_handler.handle_error(e, "Erreur lors de la configuration de l'interface")
            
    def get_cardinality(self) -> str:
        """Récupère la cardinalité configurée"""
        try:
            source = f"{self.source_min.value()},{self.source_max.currentText()}"
            target = f"{self.target_min.value()},{self.target_max.currentText()}"
            return f"{source}:{target}"
            
        except Exception as e:
            self.error_handler.handle_error(e, "Erreur lors de la récupération de la cardinalité")
            return "1:1" 