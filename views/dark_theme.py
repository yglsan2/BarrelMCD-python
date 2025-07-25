#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Système de thème dark mode moderne et élégant pour BarrelMCD
"""

from PyQt5.QtGui import QPalette, QColor, QFont, QLinearGradient, QBrush
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtWidgets import QApplication

class DarkTheme:
    """Gestionnaire de thème dark mode moderne pour BarrelMCD"""
    
    # Palette de couleurs moderne et élégante
    COLORS = {
        # Couleurs de base - Tons sombres sophistiqués
        "background": "#0A0A0A",           # Noir profond
        "surface": "#1A1A1A",              # Gris très sombre
        "surface_light": "#2A2A2A",        # Gris sombre
        "surface_dark": "#151515",         # Gris très sombre
        "surface_elevated": "#252525",     # Gris pour éléments surélevés
        
        # Couleurs de texte - Hiérarchie claire
        "text_primary": "#FFFFFF",         # Blanc pur
        "text_secondary": "#B8B8B8",       # Gris clair
        "text_tertiary": "#888888",        # Gris moyen
        "text_disabled": "#555555",        # Gris désactivé
        
        # Couleurs d'accent - Palette moderne
        "primary": "#00D4FF",              # Cyan électrique
        "primary_light": "#33DDFF",        # Cyan clair
        "primary_dark": "#0099CC",         # Cyan sombre
        "primary_gradient_start": "#00D4FF",
        "primary_gradient_end": "#0099CC",
        
        # Couleurs secondaires
        "secondary": "#FF6B35",            # Orange vif
        "secondary_light": "#FF8A65",
        "secondary_dark": "#E55A2B",
        
        # Couleurs de statut
        "success": "#00E676",              # Vert néon
        "success_light": "#66FFA6",
        "success_dark": "#00C853",
        
        "warning": "#FFD600",              # Jaune vif
        "warning_light": "#FFE666",
        "warning_dark": "#FFB300",
        
        "error": "#FF1744",                # Rouge vif
        "error_light": "#FF5C8D",
        "error_dark": "#D50000",
        
        # Couleurs pour les entités MCD - Design moderne
        "entity_bg": "#1E2A3A",           # Bleu sombre
        "entity_border": "#2E3A4A",        # Bleu plus clair
        "entity_selected": "#00D4FF",      # Cyan pour sélection
        "entity_hover": "#2A3A4A",         # Bleu au survol
        
        # Couleurs pour les relations
        "relation_bg": "#4A1E3A",          # Violet sombre
        "relation_border": "#5A2E4A",      # Violet plus clair
        "relation_selected": "#FF6B35",    # Orange pour sélection
        "relation_hover": "#5A2E4A",       # Violet au survol
        
        # Couleurs pour les attributs
        "attribute_bg": "#1A1A1A",         # Gris sombre
        "attribute_border": "#2A2A2A",     # Gris plus clair
        "pk_color": "#FF6B35",             # Orange pour clé primaire
        "pk_bg": "#4A1E1A",                # Rouge sombre pour PK
        
        # Couleurs pour la grille
        "grid_major": "#333333",           # Gris pour lignes principales
        "grid_minor": "#222222",           # Gris pour lignes secondaires
        "grid_guide": "#1A1A1A",           # Gris pour guides
        
        # Couleurs pour les outils
        "toolbar_bg": "#1A1A1A",           # Gris sombre
        "toolbar_border": "#2A2A2A",       # Gris plus clair
        "button_bg": "#2A2A2A",            # Gris
        "button_hover": "#3A3A3A",         # Gris clair au survol
        "button_pressed": "#1A1A1A",       # Gris sombre pressé
        "button_border": "#3A3A3A",        # Bordure grise
        
        # Couleurs pour les dialogues
        "dialog_bg": "#1A1A1A",            # Gris sombre
        "dialog_border": "#2A2A2A",        # Gris plus clair
        "dialog_shadow": "#000000",        # Ombre noire
        
        # Couleurs pour les menus
        "menu_bg": "#1A1A1A",              # Gris sombre
        "menu_border": "#2A2A2A",          # Gris plus clair
        "menu_selected": "#00D4FF",        # Cyan pour sélection
        "menu_hover": "#2A2A2A",           # Gris au survol
        
        # Couleurs pour les scrollbars
        "scrollbar_bg": "#1A1A1A",         # Gris sombre
        "scrollbar_handle": "#3A3A3A",     # Gris
        "scrollbar_handle_hover": "#00D4FF", # Cyan au survol
        
        # Couleurs pour les effets
        "glow": "#00D4FF",                 # Lueur cyan
        "shadow": "#000000",               # Ombre noire
        "highlight": "#00D4FF",            # Surbrillance cyan
    }
    
    @classmethod
    def apply_dark_theme(cls, app: QApplication):
        """Applique le thème dark mode moderne à l'application"""
        palette = QPalette()
        
        # Configuration de la palette avec les nouvelles couleurs
        palette.setColor(QPalette.Window, QColor(cls.COLORS["background"]))
        palette.setColor(QPalette.WindowText, QColor(cls.COLORS["text_primary"]))
        palette.setColor(QPalette.Base, QColor(cls.COLORS["surface"]))
        palette.setColor(QPalette.AlternateBase, QColor(cls.COLORS["surface_light"]))
        palette.setColor(QPalette.ToolTipBase, QColor(cls.COLORS["surface_elevated"]))
        palette.setColor(QPalette.ToolTipText, QColor(cls.COLORS["text_primary"]))
        palette.setColor(QPalette.Text, QColor(cls.COLORS["text_primary"]))
        palette.setColor(QPalette.Button, QColor(cls.COLORS["button_bg"]))
        palette.setColor(QPalette.ButtonText, QColor(cls.COLORS["text_primary"]))
        palette.setColor(QPalette.BrightText, QColor(cls.COLORS["error"]))
        palette.setColor(QPalette.Link, QColor(cls.COLORS["primary"]))
        palette.setColor(QPalette.Highlight, QColor(cls.COLORS["primary"]))
        palette.setColor(QPalette.HighlightedText, QColor(cls.COLORS["text_primary"]))
        
        # Couleurs pour les états désactivés
        palette.setColor(QPalette.Disabled, QPalette.WindowText, QColor(cls.COLORS["text_disabled"]))
        palette.setColor(QPalette.Disabled, QPalette.Text, QColor(cls.COLORS["text_disabled"]))
        palette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(cls.COLORS["text_disabled"]))
        
        app.setPalette(palette)
        
        # Configuration du style
        app.setStyle("Fusion")
        
        # Stylesheet personnalisé moderne
        stylesheet = cls._get_modern_dark_stylesheet()
        app.setStyleSheet(stylesheet)
    
    @classmethod
    def _get_modern_dark_stylesheet(cls) -> str:
        """Retourne le stylesheet CSS moderne pour le dark mode"""
        return f"""
        /* Styles généraux - Design moderne */
        QWidget {{
            background-color: {cls.COLORS["background"]};
            color: {cls.COLORS["text_primary"]};
            font-family: 'Segoe UI', 'SF Pro Display', 'Arial', sans-serif;
            font-size: 13px;
            font-weight: 400;
        }}
        
        /* Fenêtre principale */
        QMainWindow {{
            background-color: {cls.COLORS["background"]};
            border: none;
        }}
        
        /* Barre d'outils moderne */
        QToolBar {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {cls.COLORS["surface_elevated"]}, stop:1 {cls.COLORS["toolbar_bg"]});
            border: none;
            border-bottom: 1px solid {cls.COLORS["toolbar_border"]};
            spacing: 8px;
            padding: 8px;
        }}
        
        QToolBar QToolButton {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {cls.COLORS["button_bg"]}, stop:1 {cls.COLORS["surface_dark"]});
            border: 1px solid {cls.COLORS["button_border"]};
            border-radius: 6px;
            padding: 10px 16px;
            margin: 2px;
            min-width: 90px;
            min-height: 36px;
            font-weight: 500;
            color: {cls.COLORS["text_primary"]};
        }}
        
        QToolBar QToolButton:hover {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {cls.COLORS["button_hover"]}, stop:1 {cls.COLORS["surface_light"]});
            border-color: {cls.COLORS["primary"]};
        }}
        
        QToolBar QToolButton:pressed {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {cls.COLORS["button_pressed"]}, stop:1 {cls.COLORS["surface_dark"]});
            border-color: {cls.COLORS["primary_dark"]};
        }}
        
        /* Boutons modernes */
        QPushButton {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {cls.COLORS["button_bg"]}, stop:1 {cls.COLORS["surface_dark"]});
            border: 1px solid {cls.COLORS["button_border"]};
            border-radius: 6px;
            padding: 10px 20px;
            font-weight: 500;
            min-width: 90px;
            min-height: 36px;
            color: {cls.COLORS["text_primary"]};
        }}
        
        QPushButton:hover {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {cls.COLORS["button_hover"]}, stop:1 {cls.COLORS["surface_light"]});
            border-color: {cls.COLORS["primary"]};
        }}
        
        QPushButton:pressed {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {cls.COLORS["button_pressed"]}, stop:1 {cls.COLORS["surface_dark"]});
            border-color: {cls.COLORS["primary_dark"]};
        }}
        
        QPushButton:disabled {{
            background-color: {cls.COLORS["surface_dark"]};
            color: {cls.COLORS["text_disabled"]};
            border-color: {cls.COLORS["text_disabled"]};
        }}
        
        /* Boutons d'action avec couleurs */
        QPushButton[class="primary"] {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {cls.COLORS["primary"]}, stop:1 {cls.COLORS["primary_dark"]});
            border-color: {cls.COLORS["primary_dark"]};
            color: white;
            font-weight: 600;
        }}
        
        QPushButton[class="primary"]:hover {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {cls.COLORS["primary_light"]}, stop:1 {cls.COLORS["primary"]});
        }}
        
        QPushButton[class="success"] {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {cls.COLORS["success"]}, stop:1 {cls.COLORS["success_dark"]});
            border-color: {cls.COLORS["success_dark"]};
            color: white;
            font-weight: 600;
        }}
        
        QPushButton[class="warning"] {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {cls.COLORS["warning"]}, stop:1 {cls.COLORS["warning_dark"]});
            border-color: {cls.COLORS["warning_dark"]};
            color: black;
            font-weight: 600;
        }}
        
        QPushButton[class="error"] {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {cls.COLORS["error"]}, stop:1 {cls.COLORS["error_dark"]});
            border-color: {cls.COLORS["error_dark"]};
            color: white;
            font-weight: 600;
        }}
        
        /* Zones de texte modernes */
        QTextEdit, QPlainTextEdit {{
            background-color: {cls.COLORS["surface"]};
            border: 1px solid {cls.COLORS["surface_light"]};
            border-radius: 6px;
            padding: 12px;
            selection-background-color: {cls.COLORS["primary"]};
            font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
            font-size: 12px;
        }}
        
        QTextEdit:focus, QPlainTextEdit:focus {{
            border-color: {cls.COLORS["primary"]};
        }}
        
        /* Champs de saisie modernes */
        QLineEdit {{
            background-color: {cls.COLORS["surface"]};
            border: 1px solid {cls.COLORS["surface_light"]};
            border-radius: 6px;
            padding: 10px 12px;
            selection-background-color: {cls.COLORS["primary"]};
            font-size: 13px;
        }}
        
        QLineEdit:focus {{
            border-color: {cls.COLORS["primary"]};
        }}
        
        /* Combobox moderne */
        QComboBox {{
            background-color: {cls.COLORS["surface"]};
            border: 1px solid {cls.COLORS["surface_light"]};
            border-radius: 6px;
            padding: 10px 12px;
            min-width: 120px;
            font-size: 13px;
        }}
        
        QComboBox:hover {{
            border-color: {cls.COLORS["primary"]};
        }}
        
        QComboBox:focus {{
            border-color: {cls.COLORS["primary"]};
        }}
        
        QComboBox::drop-down {{
            border: none;
            width: 24px;
        }}
        
        QComboBox::down-arrow {{
            image: none;
            border-left: 6px solid transparent;
            border-right: 6px solid transparent;
            border-top: 6px solid {cls.COLORS["text_primary"]};
        }}
        
        QComboBox QAbstractItemView {{
            background-color: {cls.COLORS["surface"]};
            border: 1px solid {cls.COLORS["surface_light"]};
            border-radius: 6px;
            selection-background-color: {cls.COLORS["primary"]};
        }}
        
        /* Menus modernes */
        QMenuBar {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {cls.COLORS["surface_elevated"]}, stop:1 {cls.COLORS["toolbar_bg"]});
            border-bottom: 1px solid {cls.COLORS["toolbar_border"]};
            padding: 4px;
        }}
        
        QMenuBar::item {{
            background-color: transparent;
            padding: 8px 16px;
            border-radius: 4px;
            margin: 2px;
        }}
        
        QMenuBar::item:selected {{
            background-color: {cls.COLORS["menu_hover"]};
        }}
        
        QMenu {{
            background-color: {cls.COLORS["menu_bg"]};
            border: 1px solid {cls.COLORS["menu_border"]};
            border-radius: 6px;
            padding: 6px;
        }}
        
        QMenu::item {{
            padding: 10px 20px;
            border-radius: 4px;
            margin: 2px;
        }}
        
        QMenu::item:selected {{
            background-color: {cls.COLORS["menu_selected"]};
        }}
        
        /* Dialogues modernes */
        QDialog {{
            background-color: {cls.COLORS["dialog_bg"]};
            border: 1px solid {cls.COLORS["dialog_border"]};
            border-radius: 8px;
        }}
        
        /* Scrollbars modernes */
        QScrollBar:vertical {{
            background-color: {cls.COLORS["scrollbar_bg"]};
            width: 14px;
            border-radius: 7px;
            margin: 0px;
        }}
        
        QScrollBar::handle:vertical {{
            background-color: {cls.COLORS["scrollbar_handle"]};
            border-radius: 7px;
            min-height: 30px;
            margin: 2px;
        }}
        
        QScrollBar::handle:vertical:hover {{
            background-color: {cls.COLORS["scrollbar_handle_hover"]};
        }}
        
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}
        
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
            background: none;
        }}
        
        /* Status bar moderne */
        QStatusBar {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {cls.COLORS["toolbar_bg"]}, stop:1 {cls.COLORS["surface_dark"]});
            border-top: 1px solid {cls.COLORS["toolbar_border"]};
            padding: 4px;
        }}
        
        /* GroupBox moderne */
        QGroupBox {{
            font-weight: 600;
            border: 1px solid {cls.COLORS["surface_light"]};
            border-radius: 6px;
            margin-top: 12px;
            padding-top: 12px;
            background-color: {cls.COLORS["surface"]};
        }}
        
        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 12px;
            padding: 0 8px 0 8px;
            color: {cls.COLORS["primary"]};
        }}
        
        /* Checkbox moderne */
        QCheckBox {{
            spacing: 10px;
            font-size: 13px;
        }}
        
        QCheckBox::indicator {{
            width: 18px;
            height: 18px;
            border: 2px solid {cls.COLORS["surface_light"]};
            border-radius: 3px;
            background-color: {cls.COLORS["surface"]};
        }}
        
        QCheckBox::indicator:checked {{
            background-color: {cls.COLORS["primary"]};
            border-color: {cls.COLORS["primary"]};
            image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iOSIgdmlld0JveD0iMCAwIDEyIDkiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxwYXRoIGQ9Ik0xIDQuNUw0LjUgOEwxMSAxIiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCIvPgo8L3N2Zz4K);
        }}
        
        QCheckBox::indicator:hover {{
            border-color: {cls.COLORS["primary"]};
        }}
        
        /* Radio button moderne */
        QRadioButton {{
            spacing: 10px;
            font-size: 13px;
        }}
        
        QRadioButton::indicator {{
            width: 18px;
            height: 18px;
            border: 2px solid {cls.COLORS["surface_light"]};
            border-radius: 9px;
            background-color: {cls.COLORS["surface"]};
        }}
        
        QRadioButton::indicator:checked {{
            background-color: {cls.COLORS["primary"]};
            border-color: {cls.COLORS["primary"]};
        }}
        
        QRadioButton::indicator:hover {{
            border-color: {cls.COLORS["primary"]};
        }}
        
        /* Slider moderne */
        QSlider::groove:horizontal {{
            border: 1px solid {cls.COLORS["surface_light"]};
            height: 8px;
            background-color: {cls.COLORS["surface_dark"]};
            border-radius: 4px;
        }}
        
        QSlider::handle:horizontal {{
            background-color: {cls.COLORS["primary"]};
            border: 2px solid {cls.COLORS["primary_dark"]};
            width: 20px;
            margin: -6px 0;
            border-radius: 10px;
        }}
        
        QSlider::handle:horizontal:hover {{
            background-color: {cls.COLORS["primary_light"]};
        }}
        
        /* Effets de focus globaux */
        *:focus {{
            outline: none;
        }}
        """
    
    @classmethod
    def get_entity_style(cls, entity_type: str = "default") -> dict:
        """Retourne le style moderne pour une entité MCD"""
        styles = {
            "default": {
                "background": cls.COLORS["entity_bg"],
                "border": cls.COLORS["entity_border"],
                "text": cls.COLORS["text_primary"],
                "selected": cls.COLORS["entity_selected"],
                "hover": cls.COLORS["entity_hover"],
                "shadow": "0 4px 12px rgba(0, 0, 0, 0.3)"
            },
            "weak": {
                "background": cls.COLORS["surface_dark"],
                "border": cls.COLORS["text_disabled"],
                "text": cls.COLORS["text_secondary"],
                "selected": cls.COLORS["primary"],
                "hover": cls.COLORS["surface_light"],
                "shadow": "0 2px 8px rgba(0, 0, 0, 0.2)"
            },
            "association": {
                "background": cls.COLORS["relation_bg"],
                "border": cls.COLORS["relation_border"],
                "text": cls.COLORS["text_primary"],
                "selected": cls.COLORS["relation_selected"],
                "hover": cls.COLORS["relation_hover"],
                "shadow": "0 4px 12px rgba(255, 107, 53, 0.3)"
            }
        }
        return styles.get(entity_type, styles["default"])
    
    @classmethod
    def get_attribute_style(cls, is_primary_key: bool = False) -> dict:
        """Retourne le style moderne pour un attribut"""
        if is_primary_key:
            return {
                "background": cls.COLORS["pk_bg"],
                "text": cls.COLORS["text_primary"],
                "font_weight": "bold",
                "border": cls.COLORS["pk_color"],
                "glow": f"0 0 8px {cls.COLORS['pk_color']}"
            }
        else:
            return {
                "background": cls.COLORS["attribute_bg"],
                "text": cls.COLORS["text_primary"],
                "font_weight": "normal",
                "border": cls.COLORS["attribute_border"],
                "glow": "none"
            }
    
    @classmethod
    def get_grid_style(cls) -> dict:
        """Retourne le style moderne pour la grille"""
        return {
            "major_lines": cls.COLORS["grid_major"],
            "minor_lines": cls.COLORS["grid_minor"],
            "guide_lines": cls.COLORS["grid_guide"],
            "major_spacing": 100,
            "minor_spacing": 20,
            "opacity": 0.6
        }
    
    @classmethod
    def get_glow_effect(cls, color: str = None) -> str:
        """Retourne un effet de lueur CSS"""
        if color is None:
            color = cls.COLORS["glow"]
        return f"0 0 12px {color}, 0 0 24px {color}" 