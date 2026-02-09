#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Classe Entity pour représenter les entités MCD
"""

from PyQt5.QtWidgets import (
    QGraphicsRectItem, QGraphicsTextItem, QGraphicsItemGroup,
    QGraphicsDropShadowEffect, QInputDialog, QMenu, QAction
)
from PyQt5.QtCore import Qt, QRectF, QPointF, pyqtSignal
from PyQt5.QtGui import QPen, QBrush, QColor, QFont, QPainter, QPainterPath
from PyQt5.QtWidgets import QGraphicsItem

from views.dark_theme import DarkTheme

from PyQt5.QtCore import QObject

class EntitySignals(QObject):
    """Signaux pour l'entité"""
    entity_renamed = pyqtSignal(str, str)  # old_name, new_name
    attribute_added = pyqtSignal(str, str)  # name, type
    attribute_removed = pyqtSignal(str)
    attribute_modified = pyqtSignal(str, str, str)  # name, old_type, new_type
    inheritance_added = pyqtSignal(str, str) # parent_name, child_name
    inheritance_removed = pyqtSignal(str) # child_name

class Entity(QGraphicsItem):
    """Classe représentant une entité MCD"""
    
    def __init__(self, name="Nouvelle entité", pos=QPointF(0, 0)):
        super().__init__()
        
        # Créer l'objet de signaux
        self.signals = EntitySignals()
        
        # Propriétés de base
        self.name = name
        self.attributes = []
        self.is_weak = False
        self.is_selected = False
        self.is_fictitious = False  # Entité fictive (non générée dans MLD)
        self.business_rules = []  # Règles de gestion
        
        # Héritage
        self.parent_entity = None  # Entité parente (généralisation)
        self.child_entities = []   # Entités enfants (spécialisations)
        self.inheritance_links = []  # Liens d'héritage visuels
        self.inheritance_type = None  # "specialization" ou "generalization"
        
        # Configuration visuelle
        self.width = 200
        self.height = 100
        self.min_height = 80
        self.attribute_height = 25
        self.padding = 10
        
        # Styles
        self.setup_styles()
        
        # Création des éléments visuels
        self.create_visual_elements()
        
        # Position
        self.setPos(pos)
        
        # Configuration interactive
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        self.setFlag(QGraphicsItem.ItemIsFocusable, True)
        self.setAcceptHoverEvents(True)
        
        # Effet d'ombre
        self.setup_shadow()
        
    def setup_styles(self):
        """Configure les styles visuels"""
        self.colors = DarkTheme.COLORS
        self.style = DarkTheme.get_entity_style("default")
        
        # Couleurs
        self.bg_color = QColor(self.style["background"])
        self.border_color = QColor(self.style["border"])
        self.text_color = QColor(self.style["text"])
        self.selected_color = QColor(self.style["selected"])
        
        # Polices
        self.title_font = QFont("Segoe UI", 12, QFont.Bold)
        self.attribute_font = QFont("Segoe UI", 10)
        
    def create_visual_elements(self):
        """Crée les éléments visuels de l'entité"""
        # Les éléments seront créés dans paint()
        pass
        
    def setup_shadow(self):
        """Configure l'effet d'ombre"""
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)
        shadow.setColor(QColor(self.colors["shadow"]))
        shadow.setOffset(2, 2)
        self.setGraphicsEffect(shadow)
        
    def add_default_attributes(self):
        """Ajoute des attributs par défaut"""
        self.add_attribute("id", "INTEGER", is_primary_key=True)
        self.add_attribute("nom", "VARCHAR(100)")
        
    def add_attribute(self, name, type_name, is_primary_key=False, nullable=True, default_value=None):
        """Ajoute un attribut à l'entité"""
        attribute = {
            "name": name,
            "type": type_name,
            "is_primary_key": is_primary_key,
            "nullable": nullable,
            "default_value": default_value
        }
        self.attributes.append(attribute)
        self.update_layout()
        self.signals.attribute_added.emit(name, type_name)
        self.update()  # Redessiner l'entité
        
    def get_available_types(self):
        """Retourne la liste des types d'attributs disponibles"""
        return [
            "VARCHAR(255)", "VARCHAR(100)", "VARCHAR(50)", "VARCHAR(25)",
            "TEXT", "LONGTEXT",
            "INTEGER", "INT", "BIGINT", "SMALLINT",
            "DECIMAL(10,2)", "DECIMAL(8,2)", "DECIMAL(5,2)",
            "FLOAT", "DOUBLE",
            "DATE", "DATETIME", "TIMESTAMP",
            "TIME", "YEAR",
            "BOOLEAN", "BOOL",
            "BLOB", "LONGBLOB",
            "ENUM", "SET"
        ]
        

        
    def update_layout(self):
        """Met à jour la disposition des éléments"""
        # Calculer la nouvelle hauteur
        total_height = 50  # Titre + séparateur
        total_height += len(self.attributes) * self.attribute_height
        total_height += self.padding
        
        # Ajuster la hauteur minimale
        if total_height < self.min_height:
            total_height = self.min_height
            
        # Mettre à jour la hauteur
        self.height = total_height
        self.update()  # Redessiner l'entité
            
    def remove_attribute(self, name):
        """Supprime un attribut"""
        for i, attribute in enumerate(self.attributes):
            if attribute["name"] == name:
                # Supprimer de la liste
                self.attributes.pop(i)
                
                # Mettre à jour la disposition
                self.update_layout()
                self.signals.attribute_removed.emit(name)
                break
                
    def rename(self, new_name):
        """Renomme l'entité"""
        old_name = self.name
        self.name = new_name
        self.update()  # Redessiner l'entité
        self.signals.entity_renamed.emit(old_name, new_name)
        
    def rename_entity(self):
        """Ouvre le dialogue de renommage"""
        new_name, ok = QInputDialog.getText(None, "Renommer l'entité", 
                                           "Nouveau nom:", text=self.name)
        if ok and new_name.strip():
            self.rename(new_name.strip())
        
    def set_selected(self, selected):
        """Définit l'état de sélection"""
        self.is_selected = selected
        if selected:
            self.setZValue(10)  # Mettre au premier plan
        else:
            self.setZValue(0)  # Remettre au plan normal
        self.update()  # Redessiner l'entité
            
    def mousePressEvent(self, event):
        """Gère l'événement de clic"""
        if event.button() == Qt.LeftButton:
            self.setSelected(True)
            self.setFocus()
            # Laisser le canvas gérer le déplacement
            event.accept()
        else:
            super().mousePressEvent(event)
        
    def mouseMoveEvent(self, event):
        """Gère l'événement de mouvement"""
        # Le déplacement est géré par le canvas
        super().mouseMoveEvent(event)
        
    def mouseReleaseEvent(self, event):
        """Gère l'événement de relâchement"""
        if event.button() == Qt.LeftButton:
            self.setSelected(False)
        super().mouseReleaseEvent(event)
        
    def hoverEnterEvent(self, event):
        """Gère l'entrée de la souris"""
        self.setCursor(Qt.SizeAllCursor)
        super().hoverEnterEvent(event)
        
    def hoverLeaveEvent(self, event):
        """Gère la sortie de la souris"""
        self.setCursor(Qt.ArrowCursor)
        super().hoverLeaveEvent(event)
            
    def mouseDoubleClickEvent(self, event):
        """Gère le double-clic pour éditer"""
        if event.button() == Qt.LeftButton:
            from views.attribute_editor_dialog import AttributeEditorDialog
            dlg = AttributeEditorDialog(self)
            dlg.exec_()
            
    def edit_entity(self):
        """Ouvre l'éditeur d'entité"""
        new_name, ok = QInputDialog.getText(
            None, "Modifier l'entité", 
            "Nom de l'entité:", 
            text=self.name
        )
        if ok and new_name and new_name != self.name:
            self.rename(new_name)
            
    def add_inheritance_link(self, parent_entity):
        """Ajoute un lien d'héritage vers une entité parente"""
        if parent_entity != self and parent_entity not in self.child_entities:
            self.parent_entity = parent_entity
            parent_entity.child_entities.append(self)
            self.signals.inheritance_added.emit(parent_entity.name, self.name)
            
    def remove_inheritance_link(self):
        """Supprime le lien d'héritage"""
        if self.parent_entity:
            if self in self.parent_entity.child_entities:
                self.parent_entity.child_entities.remove(self)
            self.parent_entity = None
            self.signals.inheritance_removed.emit(self.name)
            
    def get_all_attributes(self):
        """Retourne tous les attributs (hérités + propres)"""
        all_attrs = []
        
        # Ajouter les attributs hérités
        if self.parent_entity:
            all_attrs.extend(self.parent_entity.get_all_attributes())
            
        # Ajouter les attributs propres
        all_attrs.extend(self.attributes)
        
        return all_attrs
        
    def contextMenuEvent(self, event):
        """Affiche le menu contextuel avec options d'héritage et d'édition d'attributs"""
        menu = QMenu()
        # Actions principales
        rename_action = menu.addAction("✏️ Renommer l'entité")
        attr_editor_action = menu.addAction("🧩 Éditer les attributs avancés")
        add_attr_action = menu.addAction("➕ Ajouter un attribut")
        edit_attrs_action = menu.addAction("📝 Éditer les attributs (simple)")
        menu.addSeparator()
        # Actions d'héritage
        inheritance_menu = menu.addMenu("🔄 Héritage")
        if self.parent_entity:
            remove_inheritance_action = inheritance_menu.addAction(f"Supprimer héritage de {self.parent_entity.name}")
            remove_inheritance_action.triggered.connect(self.remove_inheritance_link)
        else:
            add_inheritance_action = inheritance_menu.addAction("Ajouter héritage...")
            add_inheritance_action.triggered.connect(self.add_inheritance_dialog)
        # Actions de style
        style_menu = menu.addMenu("🎨 Style")
        weak_action = style_menu.addAction("🔗 Entité faible")
        weak_action.setCheckable(True)
        weak_action.setChecked(self.is_weak)
        center_action = style_menu.addAction("🎯 Centrer")
        align_grid_action = style_menu.addAction("📐 Aligner sur grille")
        # Connexions
        rename_action.triggered.connect(self.rename_entity)
        attr_editor_action.triggered.connect(lambda: self._open_attribute_editor_dialog())
        add_attr_action.triggered.connect(self.add_attribute_dialog)
        edit_attrs_action.triggered.connect(self.edit_attributes_dialog)
        weak_action.triggered.connect(self.toggle_weak_entity)
        center_action.triggered.connect(self.center_entity)
        align_grid_action.triggered.connect(self.align_to_grid)
        menu.exec_(event.screenPos())

    def _open_attribute_editor_dialog(self):
        from views.attribute_editor_dialog import AttributeEditorDialog
        dlg = AttributeEditorDialog(self)
        dlg.exec_()

    def add_inheritance_dialog(self):
        """Dialogue pour ajouter un héritage"""
        # TODO: Implémenter un dialogue pour sélectionner l'entité parente
        # Pour l'instant, on utilise une entrée simple
        parent_name, ok = QInputDialog.getText(None, "Ajouter héritage", 
                                             "Nom de l'entité parente:")
        if ok and parent_name.strip():
            # Chercher l'entité parente dans la scène
            if hasattr(self, 'scene') and self.scene():
                for item in self.scene().items():
                    if isinstance(item, Entity) and item.name == parent_name.strip():
                        self.add_inheritance_link(item)
                        break
                    
    def add_attribute_dialog(self):
        """Dialogue pour ajouter un attribut avec types prédéfinis"""
        from PyQt5.QtWidgets import QInputDialog, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox, QCheckBox, QPushButton
        
        dialog = QDialog()
        dialog.setWindowTitle("Ajouter un attribut")
        dialog.setModal(True)
        
        layout = QVBoxLayout()
        
        # Nom de l'attribut
        name_layout = QHBoxLayout()
        name_label = QLabel("Nom:")
        name_edit = QLineEdit()
        name_layout.addWidget(name_label)
        name_layout.addWidget(name_edit)
        layout.addLayout(name_layout)
        
        # Type d'attribut
        type_layout = QHBoxLayout()
        type_label = QLabel("Type:")
        type_combo = QComboBox()
        type_combo.addItems(self.get_available_types())
        type_layout.addWidget(type_label)
        type_layout.addWidget(type_combo)
        layout.addLayout(type_layout)
        
        # Options
        primary_check = QCheckBox("Clé primaire")
        nullable_check = QCheckBox("Nullable")
        nullable_check.setChecked(True)
        
        layout.addWidget(primary_check)
        layout.addWidget(nullable_check)
        
        # Boutons
        button_layout = QHBoxLayout()
        ok_button = QPushButton("OK")
        cancel_button = QPushButton("Annuler")
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)
        
        dialog.setLayout(layout)
        
        # Connexions
        ok_button.clicked.connect(dialog.accept)
        cancel_button.clicked.connect(dialog.reject)
        
        if dialog.exec_() == QDialog.Accepted:
            name = name_edit.text().strip()
            type_name = type_combo.currentText()
            is_primary = primary_check.isChecked()
            nullable = nullable_check.isChecked()
            
            if name:
                self.add_attribute(name, type_name, is_primary, nullable)
                
    def edit_attributes_dialog(self):
        """Ouvre le dialogue d'édition des attributs"""
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox, QCheckBox, QPushButton, QListWidget, QListWidgetItem
        
        dialog = QDialog()
        dialog.setWindowTitle("Éditer les attributs")
        dialog.setModal(True)
        dialog.resize(400, 300)
        
        layout = QVBoxLayout()
        
        # Liste des attributs
        list_label = QLabel("Attributs:")
        layout.addWidget(list_label)
        
        attr_list = QListWidget()
        for attr in self.attributes:
            item = QListWidgetItem(f"{attr['name']}: {attr['type']}")
            item.setData(Qt.UserRole, attr)
            attr_list.addItem(item)
        layout.addWidget(attr_list)
        
        # Boutons d'action
        button_layout = QHBoxLayout()
        add_button = QPushButton("Ajouter")
        edit_button = QPushButton("Modifier")
        delete_button = QPushButton("Supprimer")
        button_layout.addWidget(add_button)
        button_layout.addWidget(edit_button)
        button_layout.addWidget(delete_button)
        layout.addLayout(button_layout)
        
        # Boutons de fermeture
        close_layout = QHBoxLayout()
        ok_button = QPushButton("OK")
        close_layout.addWidget(ok_button)
        layout.addLayout(close_layout)
        
        dialog.setLayout(layout)
        
        # Connexions
        add_button.clicked.connect(lambda: self.add_attribute_dialog())
        edit_button.clicked.connect(lambda: self.edit_attribute_dialog(attr_list.currentItem()))
        delete_button.clicked.connect(lambda: self.delete_attribute(attr_list.currentItem()))
        ok_button.clicked.connect(dialog.accept)
        
        dialog.exec_()
        
    def edit_attribute_dialog(self, list_item):
        """Dialogue pour modifier un attribut"""
        if not list_item:
            return
            
        attr = list_item.data(Qt.UserRole)
        if not attr:
            return
            
        from PyQt5.QtWidgets import QInputDialog, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox, QCheckBox, QPushButton
        
        dialog = QDialog()
        dialog.setWindowTitle("Modifier l'attribut")
        dialog.setModal(True)
        
        layout = QVBoxLayout()
        
        # Nom de l'attribut
        name_layout = QHBoxLayout()
        name_label = QLabel("Nom:")
        name_edit = QLineEdit(attr['name'])
        name_layout.addWidget(name_label)
        name_layout.addWidget(name_edit)
        layout.addLayout(name_layout)
        
        # Type d'attribut
        type_layout = QHBoxLayout()
        type_label = QLabel("Type:")
        type_combo = QComboBox()
        type_combo.addItems(self.get_available_types())
        type_combo.setCurrentText(attr['type'])
        type_layout.addWidget(type_label)
        type_layout.addWidget(type_combo)
        layout.addLayout(type_layout)
        
        # Options
        primary_check = QCheckBox("Clé primaire")
        primary_check.setChecked(attr.get('is_primary_key', False))
        nullable_check = QCheckBox("Nullable")
        nullable_check.setChecked(attr.get('nullable', True))
        
        layout.addWidget(primary_check)
        layout.addWidget(nullable_check)
        
        # Boutons
        button_layout = QHBoxLayout()
        ok_button = QPushButton("OK")
        cancel_button = QPushButton("Annuler")
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)
        
        dialog.setLayout(layout)
        
        # Connexions
        ok_button.clicked.connect(dialog.accept)
        cancel_button.clicked.connect(dialog.reject)
        
        if dialog.exec_() == QDialog.Accepted:
            old_name = attr['name']
            new_name = name_edit.text().strip()
            new_type = type_combo.currentText()
            is_primary = primary_check.isChecked()
            nullable = nullable_check.isChecked()
            
            if new_name and new_name != old_name:
                # Supprimer l'ancien attribut
                self.remove_attribute(old_name)
                # Ajouter le nouveau
                self.add_attribute(new_name, new_type, is_primary, nullable)
                
    def delete_attribute(self, list_item):
        """Supprime un attribut"""
        if not list_item:
            return
            
        attr = list_item.data(Qt.UserRole)
        if attr:
            self.remove_attribute(attr['name'])
            # Rafraîchir la liste
            list_item.parent().takeItem(list_item.parent().row(list_item))
        
    def toggle_weak_entity(self):
        """Bascule entre entité normale et entité faible"""
        self.is_weak = not self.is_weak
        if self.is_weak:
            self.style = DarkTheme.get_entity_style("weak")
        else:
            self.style = DarkTheme.get_entity_style("default")
            
        # Mettre à jour les couleurs
        self.bg_color = QColor(self.style["background"])
        self.border_color = QColor(self.style["border"])
        self.rect_item.setBrush(QBrush(self.bg_color))
        self.rect_item.setPen(QPen(self.border_color, 2))
        
    def center_entity(self):
        """Centre l'entité dans la vue"""
        scene_rect = self.scene().sceneRect()
        center = scene_rect.center()
        self.setPos(center.x() - self.width / 2, center.y() - self.height / 2)
        
    def align_to_grid(self):
        """Aligne l'entité sur la grille"""
        pos = self.pos()
        grid_size = 20
        new_x = round(pos.x() / grid_size) * grid_size
        new_y = round(pos.y() / grid_size) * grid_size
        self.setPos(new_x, new_y)
        
    def get_data(self):
        """Retourne les données de l'entité pour export"""
        return {
            "name": self.name,
            "position": {"x": self.pos().x(), "y": self.pos().y()},
            "attributes": self.attributes.copy(),
            "is_weak": self.is_weak
        }
        
    def boundingRect(self):
        """Retourne le rectangle englobant de l'entité"""
        return QRectF(0, 0, self.width, self.height)
        
    def shape(self):
        """Retourne la forme de l'entité pour la détection de clic"""
        path = QPainterPath()
        path.addRect(self.boundingRect())
        return path
        
    def paint(self, painter, option, widget):
        """Dessine l'entité avec style moderne"""
        # Configuration de l'antialiasing pour un rendu lisse
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
        
        # Rectangle principal avec coins arrondis
        rect = self.boundingRect()
        corner_radius = 8
        
        # Créer un dégradé pour le fond
        from PyQt5.QtGui import QLinearGradient
        gradient = QLinearGradient(rect.topLeft(), rect.bottomLeft())
        if self.is_selected:
            gradient.setColorAt(0, QColor(self.selected_color).lighter(120))
            gradient.setColorAt(1, QColor(self.selected_color))
        else:
            gradient.setColorAt(0, QColor(self.bg_color).lighter(110))
            gradient.setColorAt(1, self.bg_color)
        
        painter.setBrush(QBrush(gradient))
        
        # Bordure selon l'état de sélection avec effet de lueur
        if self.is_selected:
            # Effet de lueur pour la sélection
            glow_pen = QPen(QColor(self.selected_color).lighter(150), 4)
            glow_pen.setCapStyle(Qt.RoundCap)
            glow_pen.setJoinStyle(Qt.RoundJoin)
            painter.setPen(glow_pen)
            painter.drawRoundedRect(rect.adjusted(-1, -1, 1, 1), corner_radius, corner_radius)
            
            pen = QPen(self.selected_color, 3)
        else:
            pen = QPen(self.border_color, 2)
            
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)
        painter.setPen(pen)
        painter.drawRoundedRect(rect, corner_radius, corner_radius)
        
        # Titre
        painter.setPen(QPen(self.text_color))
        painter.setFont(self.title_font)
        title_rect = QRectF(self.padding, self.padding, 
                           self.width - 2 * self.padding, 30)
        painter.drawText(title_rect, Qt.AlignCenter, self.name)
        
        # Ligne de séparation
        painter.setPen(QPen(self.border_color, 2))
        painter.drawLine(self.padding, 40, 
                        self.width - self.padding, 40)
        
        # Attributs avec meilleure visibilité
        painter.setFont(self.attribute_font)
        y_offset = 50
        for attribute in self.attributes:
            # Préfixe pour clé primaire
            prefix = "🔑 " if attribute['is_primary_key'] else ""
            # Icônes pour les propriétés
            icons = []
            if attribute.get('unique', False):
                icons.append("🔒")
            if attribute.get('indexed', False):
                icons.append("📊")
            if not attribute.get('nullable', True):
                icons.append("⚠️")
            
            # Texte principal
            text = f"{prefix}{attribute['name']}: {attribute['type']}"
            if icons:
                text += f" {' '.join(icons)}"
            
            # Couleur selon le type d'attribut
            if attribute['is_primary_key']:
                painter.setPen(QPen(QColor(255, 200, 100)))  # Orange pour PK
            elif attribute.get('unique', False):
                painter.setPen(QPen(QColor(100, 200, 255)))  # Bleu pour unique
            else:
                painter.setPen(QPen(QColor(200, 200, 200)))  # Blanc par défaut
            
            painter.drawText(self.padding, y_offset, text)
            y_offset += self.attribute_height
        
    def set_data(self, data):
        """Charge les données dans l'entité"""
        self.name = data.get("name", "Nouvelle entité")
        self.title_item.setPlainText(self.name)
        
        pos_data = data.get("position", {"x": 0, "y": 0})
        self.setPos(pos_data["x"], pos_data["y"])
        
        # Charger les attributs
        self.attributes = []
        for attr_data in data.get("attributes", []):
            self.add_attribute(
                attr_data["name"],
                attr_data["type"],
                attr_data.get("is_primary_key", False)
            )
            
        self.is_weak = data.get("is_weak", False)
        if self.is_weak:
            self.toggle_weak_entity()
