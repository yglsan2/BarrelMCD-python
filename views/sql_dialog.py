from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QComboBox, QTextEdit, QPushButton, QTabWidget,
                             QSplitter, QWidget)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QApplication
from models.sql_generator import SQLGenerator, SQLDialect

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