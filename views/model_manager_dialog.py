from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QLineEdit, QComboBox, QMessageBox
)
from PyQt5.QtCore import Qt

class ModelManagerDialog(QDialog):
    """Boîte de dialogue pour gérer les modèles MCD."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Gestionnaire de modèles")
        self.setMinimumWidth(400)
        self.setup_ui()
        
    def setup_ui(self):
        """Configure l'interface utilisateur."""
        layout = QVBoxLayout(self)
        
        # Nom du modèle
        name_layout = QHBoxLayout()
        name_label = QLabel("Nom du modèle :")
        self.name_input = QLineEdit()
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.name_input)
        layout.addLayout(name_layout)
        
        # Type de modèle
        type_layout = QHBoxLayout()
        type_label = QLabel("Type de modèle :")
        self.type_combo = QComboBox()
        self.type_combo.addItems(["Relationnel", "Entité-Association"])
        type_layout.addWidget(type_label)
        type_layout.addWidget(self.type_combo)
        layout.addLayout(type_layout)
        
        # Boutons
        buttons_layout = QHBoxLayout()
        create_btn = QPushButton("Créer")
        create_btn.clicked.connect(self._create_model)
        cancel_btn = QPushButton("Annuler")
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(create_btn)
        buttons_layout.addWidget(cancel_btn)
        layout.addLayout(buttons_layout)
        
    def _create_model(self):
        """Crée un nouveau modèle."""
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Erreur", "Le nom du modèle est obligatoire.")
            return
            
        model_type = self.type_combo.currentText()
        # TODO: Implémenter la création du modèle
        
        QMessageBox.information(
            self,
            "Succès",
            f"Modèle '{name}' de type {model_type} créé avec succès !"
        )
        self.accept() 