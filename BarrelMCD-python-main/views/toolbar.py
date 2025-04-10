from PyQt5.QtWidgets import QToolBar, QAction, QMenu, QMessageBox
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt
from .styles import AppStyles

class HelpToolBar(QToolBar):
    """Barre d'outils pour l'aide"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMovable(False)
        self.setFloatable(False)
        self.setIconSize(QSize(24, 24))
        
        # Style de la barre d'outils
        toolbar_style = AppStyles.get_ui_style("toolbar")
        self.setStyleSheet(f"""
            QToolBar {{
                background-color: {toolbar_style["background_color"].name()};
                color: {toolbar_style["text_color"].name()};
                font-family: {toolbar_style["font"].family()};
                font-size: {toolbar_style["font"].pointSize()}px;
                padding: {toolbar_style["padding"]}px;
                border-radius: {toolbar_style["border_radius"]}px;
            }}
            QToolButton {{
                background-color: transparent;
                border: none;
                padding: 5px;
                border-radius: 4px;
            }}
            QToolButton:hover {{
                background-color: {AppStyles.ACCENT_COLOR.name()};
            }}
            QToolButton:pressed {{
                background-color: {AppStyles.SECONDARY_COLOR.name()};
            }}
            QMenu {{
                background-color: {AppStyles.get_ui_style("menu")["background_color"].name()};
                color: {AppStyles.get_ui_style("menu")["text_color"].name()};
                font-family: {AppStyles.get_ui_style("menu")["font"].family()};
                font-size: {AppStyles.get_ui_style("menu")["font"].pointSize()}px;
                padding: {AppStyles.get_ui_style("menu")["padding"]}px;
                border-radius: {AppStyles.get_ui_style("menu")["border_radius"]}px;
            }}
            QMenu::item {{
                padding: 5px 10px;
                border-radius: 4px;
            }}
            QMenu::item:selected {{
                background-color: {AppStyles.get_ui_style("menu")["hover_color"].name()};
            }}
        """)
        
        # Bouton d'aide rapide
        self.quick_help_action = QAction(
            QIcon("resources/icons/help.png"),
            "Aide rapide",
            self
        )
        self.quick_help_action.setStatusTip("Affiche l'aide rapide")
        self.quick_help_action.triggered.connect(self.parent().show_quick_help)
        self.addAction(self.quick_help_action)
        
        # Menu des tutoriels
        self.tutorials_menu = QMenu("Tutoriels", self)
        
        # Tutoriel de création d'entité
        create_entity_action = QAction(
            QIcon("resources/icons/entity.png"),
            "Créer une entité",
            self
        )
        create_entity_action.triggered.connect(
            lambda: self.parent().start_tutorial("create_entity")
        )
        self.tutorials_menu.addAction(create_entity_action)
        
        # Tutoriel de création de relation
        create_relation_action = QAction(
            QIcon("resources/icons/relation.png"),
            "Créer une relation",
            self
        )
        create_relation_action.triggered.connect(
            lambda: self.parent().start_tutorial("create_relation")
        )
        self.tutorials_menu.addAction(create_relation_action)
        
        # Tutoriel d'édition
        edit_action = QAction(
            QIcon("resources/icons/edit.png"),
            "Modifier un élément",
            self
        )
        edit_action.triggered.connect(
            lambda: self.parent().start_tutorial("edit_entity")
        )
        self.tutorials_menu.addAction(edit_action)
        
        # Bouton des tutoriels
        self.tutorials_action = QAction(
            QIcon("resources/icons/tutorial.png"),
            "Tutoriels",
            self
        )
        self.tutorials_action.setMenu(self.tutorials_menu)
        self.addAction(self.tutorials_action)
        
        # Bouton pour activer/désactiver l'aide
        self.toggle_help_action = QAction(
            QIcon("resources/icons/help_off.png"),
            "Activer/Désactiver l'aide",
            self
        )
        self.toggle_help_action.setCheckable(True)
        self.toggle_help_action.setChecked(True)
        self.toggle_help_action.triggered.connect(self.parent().toggle_help)
        self.addAction(self.toggle_help_action)
        
        # Ajout d'un séparateur
        self.addSeparator()
        
        # Bouton pour afficher les raccourcis clavier
        self.shortcuts_action = QAction(
            QIcon("resources/icons/keyboard.png"),
            "Raccourcis clavier",
            self
        )
        self.shortcuts_action.triggered.connect(self._show_shortcuts)
        self.addAction(self.shortcuts_action)
        
    def _show_shortcuts(self):
        """Affiche les raccourcis clavier"""
        button_style = AppStyles.get_ui_style("button")
        
        shortcuts_text = """
        Raccourcis clavier :
        
        Modes :
        - S : Mode sélection
        - E : Mode entité
        - A : Mode association
        - R : Mode relation
        
        Navigation :
        - Z : Zoom avant
        - X : Zoom arrière
        - F : Ajuster la vue
        - G : Afficher/masquer la grille
        
        Édition :
        - Suppr : Supprimer l'élément sélectionné
        - Ctrl+R : Démarrer une relation
        - Shift+R : Démarrer une relation
        
        Aide :
        - F1 : Aide rapide
        - H : Activer/désactiver l'aide
        """
        
        msg = QMessageBox(self)
        msg.setWindowTitle("Raccourcis clavier")
        msg.setText(shortcuts_text)
        msg.setStyleSheet(f"""
            QMessageBox {{
                background-color: {AppStyles.BACKGROUND_COLOR.name()};
            }}
            QMessageBox QLabel {{
                color: {AppStyles.TEXT_COLOR.name()};
                font-family: {button_style["font"].family()};
                font-size: {button_style["font"].pointSize()}px;
            }}
            QPushButton {{
                background-color: {button_style["background_color"].name()};
                color: {button_style["text_color"].name()};
                font-family: {button_style["font"].family()};
                font-size: {button_style["font"].pointSize()}px;
                padding: {button_style["padding"]}px;
                border-radius: {button_style["border_radius"]}px;
            }}
            QPushButton:hover {{
                background-color: {button_style["hover_color"].name()};
            }}
        """)
        msg.exec() 