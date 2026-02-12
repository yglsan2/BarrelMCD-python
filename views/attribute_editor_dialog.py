from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem,
    QAbstractItemView, QHeaderView, QMessageBox, QComboBox, QCheckBox, QWidget, QStyle, QLabel,
    QLineEdit, QTextEdit, QGroupBox, QFormLayout, QSpinBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QColor, QFont

class AttributeEditorDialog(QDialog):
    """Panneau moderne d'édition des attributs d'une entité style Barrel, mais plus moderne."""
    def __init__(self, entity, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Attributs de l'entité : {entity.name}")
        self.setMinimumSize(800, 500)
        self.entity = entity
        self.setModal(False)
        self.setStyleSheet(self._modern_style())
        self._setup_ui()
        self._load_attributes()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Tableau principal avec plus de colonnes
        self.table = QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels([
            "Nom", "Type", "PK", "Nullable", "Unique", "Index", "Défaut", "Commentaire"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.DoubleClicked | QAbstractItemView.SelectedClicked)
        self.table.setDragDropMode(QAbstractItemView.InternalMove)
        self.table.setDragEnabled(True)
        self.table.setAcceptDrops(True)
        self.table.setDropIndicatorShown(True)
        self.table.setFont(QFont("Segoe UI", 10))
        layout.addWidget(self.table)

        # Panneau d'édition détaillée
        detail_group = QGroupBox("Édition détaillée")
        detail_layout = QFormLayout(detail_group)
        
        self.name_edit = QLineEdit()
        self.type_combo = QComboBox()
        self.type_combo.addItems(self.entity.get_available_types())
        self.pk_check = QCheckBox()
        self.nullable_check = QCheckBox()
        self.unique_check = QCheckBox()
        self.index_check = QCheckBox()
        self.default_edit = QLineEdit()
        self.comment_edit = QTextEdit()
        self.comment_edit.setMaximumHeight(60)
        
        detail_layout.addRow("Nom:", self.name_edit)
        detail_layout.addRow("Type:", self.type_combo)
        detail_layout.addRow("Clé primaire:", self.pk_check)
        detail_layout.addRow("Nullable:", self.nullable_check)
        detail_layout.addRow("Unique:", self.unique_check)
        detail_layout.addRow("Indexé:", self.index_check)
        detail_layout.addRow("Valeur par défaut:", self.default_edit)
        detail_layout.addRow("Commentaire:", self.comment_edit)
        
        layout.addWidget(detail_group)

        # Boutons d'action
        btn_layout = QHBoxLayout()
        add_btn = QPushButton("➕ Ajouter")
        del_btn = QPushButton("🗑️ Supprimer")
        up_btn = QPushButton("⬆️ Monter")
        down_btn = QPushButton("⬇️ Descendre")
        apply_btn = QPushButton("Appliquer")
        ok_btn = QPushButton("Valider")
        cancel_btn = QPushButton("Annuler")
        
        for btn in (add_btn, del_btn, up_btn, down_btn, apply_btn, ok_btn, cancel_btn):
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet("padding: 6px 12px; border-radius: 6px;")
        
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(del_btn)
        btn_layout.addWidget(up_btn)
        btn_layout.addWidget(down_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(apply_btn)
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        # Connexions
        add_btn.clicked.connect(self._add_row)
        del_btn.clicked.connect(self._delete_row)
        up_btn.clicked.connect(self._move_up)
        down_btn.clicked.connect(self._move_down)
        apply_btn.clicked.connect(self._apply_to_entity)
        ok_btn.clicked.connect(self._apply)
        cancel_btn.clicked.connect(self.reject)
        
        # Connexion de la sélection du tableau
        self.table.itemSelectionChanged.connect(self._on_selection_changed)

    def _load_attributes(self):
        self.table.setRowCount(0)
        for attr in self.entity.attributes:
            self._add_row(attr)

    def _add_row(self, attr=None):
        row = self.table.rowCount()
        self.table.insertRow(row)
        
        # Nom
        name_item = QTableWidgetItem(attr["name"] if attr else "")
        self.table.setItem(row, 0, name_item)
        
        # Type
        type_combo = QComboBox()
        type_combo.addItems(self.entity.get_available_types())
        if attr:
            type_combo.setCurrentText(attr["type"])
        self.table.setCellWidget(row, 1, type_combo)
        
        # PK
        pk_check = QCheckBox()
        pk_check.setChecked(attr["is_primary_key"] if attr else False)
        pk_check.setStyleSheet("margin-left:12px;")
        self.table.setCellWidget(row, 2, pk_check)
        
        # Nullable
        nullable_check = QCheckBox()
        nullable_check.setChecked(attr["nullable"] if attr else True)
        nullable_check.setStyleSheet("margin-left:12px;")
        self.table.setCellWidget(row, 3, nullable_check)
        
        # Unique
        unique_check = QCheckBox()
        unique_check.setChecked(attr.get("unique", False) if isinstance(attr, dict) else False)
        unique_check.setStyleSheet("margin-left:12px;")
        self.table.setCellWidget(row, 4, unique_check)
        
        # Index
        index_check = QCheckBox()
        index_check.setChecked(attr.get("indexed", False) if isinstance(attr, dict) else False)
        index_check.setStyleSheet("margin-left:12px;")
        self.table.setCellWidget(row, 5, index_check)
        
        # Valeur par défaut
        default_item = QTableWidgetItem(attr["default_value"] if attr and attr["default_value"] else "")
        self.table.setItem(row, 6, default_item)
        
        # Commentaire
        comment_item = QTableWidgetItem(attr.get("comment", "") if isinstance(attr, dict) else "")
        self.table.setItem(row, 7, comment_item)

    def _on_selection_changed(self):
        """Met à jour le panneau d'édition détaillée selon la sélection"""
        current_row = self.table.currentRow()
        if current_row >= 0:
            try:
                # Récupérer les données de la ligne sélectionnée
                name_item = self.table.item(current_row, 0)
                name = name_item.text() if name_item else ""
                
                type_widget = self.table.cellWidget(current_row, 1)
                type_ = type_widget.currentText() if type_widget else ""
                
                pk_widget = self.table.cellWidget(current_row, 2)
                pk = pk_widget.isChecked() if pk_widget else False
                
                nullable_widget = self.table.cellWidget(current_row, 3)
                nullable = nullable_widget.isChecked() if nullable_widget else True
                
                unique_widget = self.table.cellWidget(current_row, 4)
                unique = unique_widget.isChecked() if unique_widget else False
                
                indexed_widget = self.table.cellWidget(current_row, 5)
                indexed = indexed_widget.isChecked() if indexed_widget else False
                
                default_item = self.table.item(current_row, 6)
                default = default_item.text() if default_item else ""
                
                comment_item = self.table.item(current_row, 7)
                comment = comment_item.text() if comment_item else ""
                
                # Mettre à jour le panneau d'édition
                self.name_edit.setText(name)
                self.type_combo.setCurrentText(type_)
                self.pk_check.setChecked(pk)
                self.nullable_check.setChecked(nullable)
                self.unique_check.setChecked(unique)
                self.index_check.setChecked(indexed)
                self.default_edit.setText(default)
                self.comment_edit.setPlainText(comment)
            except Exception as e:
                print(f"Erreur lors de la mise à jour du panneau d'édition: {e}")
                # En cas d'erreur, vider les champs
                self.name_edit.setText("")
                self.type_combo.setCurrentText("")
                self.pk_check.setChecked(False)
                self.nullable_check.setChecked(True)
                self.unique_check.setChecked(False)
                self.index_check.setChecked(False)
                self.default_edit.setText("")
                self.comment_edit.setPlainText("")

    def _apply_to_entity(self):
        """Applique les modifications du panneau d'édition à la ligne sélectionnée"""
        current_row = self.table.currentRow()
        if current_row >= 0:
            # Mettre à jour la ligne avec les données du panneau
            self.table.item(current_row, 0).setText(self.name_edit.text())
            self.table.cellWidget(current_row, 1).setCurrentText(self.type_combo.currentText())
            self.table.cellWidget(current_row, 2).setChecked(self.pk_check.isChecked())
            self.table.cellWidget(current_row, 3).setChecked(self.nullable_check.isChecked())
            self.table.cellWidget(current_row, 4).setChecked(self.unique_check.isChecked())
            self.table.cellWidget(current_row, 5).setChecked(self.index_check.isChecked())
            self.table.item(current_row, 6).setText(self.default_edit.text())
            self.table.item(current_row, 7).setText(self.comment_edit.toPlainText())

    def _delete_row(self):
        for idx in sorted(set([i.row() for i in self.table.selectedItems()]), reverse=True):
            self.table.removeRow(idx)

    def _move_up(self):
        row = self.table.currentRow()
        if row > 0:
            self.table.insertRow(row-1)
            for col in range(self.table.columnCount()):
                item = self.table.takeItem(row+1, col)
                widget = self.table.cellWidget(row+1, col)
                if item:
                    self.table.setItem(row-1, col, item)
                if widget:
                    self.table.setCellWidget(row-1, col, widget)
            self.table.removeRow(row+1)
            self.table.selectRow(row-1)

    def _move_down(self):
        row = self.table.currentRow()
        if row < self.table.rowCount()-1:
            self.table.insertRow(row+2)
            for col in range(self.table.columnCount()):
                item = self.table.takeItem(row, col)
                widget = self.table.cellWidget(row, col)
                if item:
                    self.table.setItem(row+2, col, item)
                if widget:
                    self.table.setCellWidget(row+2, col, widget)
            self.table.removeRow(row)
            self.table.selectRow(row+1)

    def _apply(self):
        # Valider et synchroniser avec l'entité
        new_attrs = []
        for row in range(self.table.rowCount()):
            name = self.table.item(row, 0).text().strip() if self.table.item(row, 0) else ""
            type_ = self.table.cellWidget(row, 1).currentText() if self.table.cellWidget(row, 1) else "VARCHAR(255)"
            pk = self.table.cellWidget(row, 2).isChecked() if self.table.cellWidget(row, 2) else False
            nullable = self.table.cellWidget(row, 3).isChecked() if self.table.cellWidget(row, 3) else True
            unique = self.table.cellWidget(row, 4).isChecked() if self.table.cellWidget(row, 4) else False
            indexed = self.table.cellWidget(row, 5).isChecked() if self.table.cellWidget(row, 5) else False
            default = self.table.item(row, 6).text().strip() if self.table.item(row, 6) else None
            comment = self.table.item(row, 7).text().strip() if self.table.item(row, 7) else None
            
            if name:
                new_attrs.append({
                    "name": name,
                    "type": type_,
                    "is_primary_key": pk,
                    "nullable": nullable,
                    "unique": unique,
                    "indexed": indexed,
                    "default_value": default,
                    "comment": comment
                })
        
        self.entity.attributes = new_attrs
        self.entity.update_layout()
        self.entity.update()
        self.accept()

    def _modern_style(self):
        return """
        QDialog {
            background: #23272e;
            border-radius: 12px;
        }
        QTableWidget, QHeaderView::section {
            background: #23272e;
            color: #e0e0e0;
            border: none;
            font-size: 13px;
        }
        QTableWidget::item:selected {
            background: #2d3640;
        }
        QPushButton {
            background: #2d3640;
            color: #e0e0e0;
            border: none;
            border-radius: 6px;
            padding: 6px 12px;
        }
        QPushButton:hover {
            background: #3a4250;
        }
        QComboBox, QCheckBox, QLineEdit, QTextEdit {
            background: #23272e;
            color: #e0e0e0;
            border-radius: 4px;
        }
        QHeaderView::section {
            background: #2d3640;
            color: #e0e0e0;
            border: none;
        }
        QGroupBox {
            color: #e0e0e0;
            font-weight: bold;
            border: 1px solid #444444;
            border-radius: 6px;
            margin-top: 6px;
            padding-top: 6px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 7px;
            padding: 0px 5px 0px 5px;
        }
        """ 