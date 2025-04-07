from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QTextEdit, QFileDialog, QMessageBox
)
from PyQt5.QtCore import Qt

class SQLInspectorDialog(QDialog):
    """Boîte de dialogue pour inspecter les schémas SQL."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Inspecteur SQL")
        self.setMinimumSize(600, 400)
        self.setup_ui()
        
    def setup_ui(self):
        """Configure l'interface utilisateur."""
        layout = QVBoxLayout(self)
        
        # Zone de texte SQL
        self.sql_text = QTextEdit()
        self.sql_text.setPlaceholderText("Collez votre schéma SQL ici...")
        layout.addWidget(self.sql_text)
        
        # Boutons
        buttons_layout = QHBoxLayout()
        
        load_btn = QPushButton("Charger un fichier")
        load_btn.clicked.connect(self._load_file)
        
        analyze_btn = QPushButton("Analyser")
        analyze_btn.clicked.connect(self._analyze_sql)
        
        close_btn = QPushButton("Fermer")
        close_btn.clicked.connect(self.reject)
        
        buttons_layout.addWidget(load_btn)
        buttons_layout.addWidget(analyze_btn)
        buttons_layout.addWidget(close_btn)
        layout.addLayout(buttons_layout)
        
    def _load_file(self):
        """Charge un fichier SQL."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Charger un fichier SQL",
            "",
            "Fichiers SQL (*.sql);;Tous les fichiers (*.*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    self.sql_text.setText(f.read())
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Erreur",
                    f"Impossible de lire le fichier : {str(e)}"
                )
    
    def _analyze_sql(self):
        """Analyse le schéma SQL."""
        sql = self.sql_text.toPlainText().strip()
        if not sql:
            QMessageBox.warning(
                self,
                "Erreur",
                "Veuillez d'abord entrer ou charger un schéma SQL."
            )
            return
            
        # TODO: Implémenter l'analyse du schéma SQL
        QMessageBox.information(
            self,
            "Analyse",
            "L'analyse du schéma SQL sera implémentée prochainement."
        ) 