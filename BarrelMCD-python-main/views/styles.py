from PyQt5.QtGui import QColor, QPalette, QFont, QIcon
from PyQt5.QtCore import Qt

class AppStyles:
    """Gestionnaire de styles de l'application"""
    
    # Couleurs principales
    PRIMARY_COLOR = QColor("#6B4E71")  # Violet doux
    SECONDARY_COLOR = QColor("#8B7B8E")  # Violet gris
    ACCENT_COLOR = QColor("#E6B0AA")  # Rose pâle
    BACKGROUND_COLOR = QColor("#F8F7F8")  # Blanc cassé
    TEXT_COLOR = QColor("#2C2C2C")  # Gris foncé doux
    
    # Couleurs des entités
    ENTITY_COLORS = {
        "default": QColor("#FFFFFF"),  # Blanc
        "primary": QColor("#F0EEF2"),  # Violet très pâle
        "secondary": QColor("#E8E6EB"),  # Violet gris pâle
        "success": QColor("#A3D9A5"),  # Vert pastel
        "warning": QColor("#F4D03F"),  # Jaune doux
        "error": QColor("#F1948A")  # Rouge pastel
    }
    
    # Couleurs des associations
    ASSOCIATION_COLORS = {
        "default": QColor("#F8F7F8"),  # Blanc cassé
        "primary": QColor("#E8E6EB"),  # Violet gris pâle
        "secondary": QColor("#E0DEE5"),  # Violet gris très pâle
        "success": QColor("#A3D9A5"),  # Vert pastel
        "warning": QColor("#F4D03F"),  # Jaune doux
        "error": QColor("#F1948A")  # Rouge pastel
    }
    
    # Couleurs des relations
    RELATION_COLORS = {
        "default": QColor("#D5D3D8"),  # Gris violet pâle
        "primary": QColor("#8B7B8E"),  # Violet gris
        "secondary": QColor("#6B4E71"),  # Violet doux
        "success": QColor("#A3D9A5"),  # Vert pastel
        "warning": QColor("#F4D03F"),  # Jaune doux
        "error": QColor("#F1948A")  # Rouge pastel
    }
    
    # Styles des entités
    ENTITY_STYLES = {
        "default": {
            "background_color": ENTITY_COLORS["default"],
            "border_color": QColor("#D5D3D8"),  # Gris violet pâle
            "text_color": TEXT_COLOR,
            "font": QFont("Segoe UI", 10),
            "border_width": 2,
            "corner_radius": 8,
            "padding": 10,
            "shadow": True
        },
        "primary": {
            "background_color": ENTITY_COLORS["primary"],
            "border_color": PRIMARY_COLOR,
            "text_color": TEXT_COLOR,
            "font": QFont("Segoe UI", 10),
            "border_width": 2,
            "corner_radius": 8,
            "padding": 10,
            "shadow": True
        }
    }
    
    # Styles des associations
    ASSOCIATION_STYLES = {
        "default": {
            "background_color": ASSOCIATION_COLORS["default"],
            "border_color": QColor("#D5D3D8"),  # Gris violet pâle
            "text_color": TEXT_COLOR,
            "font": QFont("Segoe UI", 10),
            "border_width": 2,
            "corner_radius": 8,
            "padding": 10,
            "shadow": True
        },
        "primary": {
            "background_color": ASSOCIATION_COLORS["primary"],
            "border_color": PRIMARY_COLOR,
            "text_color": TEXT_COLOR,
            "font": QFont("Segoe UI", 10),
            "border_width": 2,
            "corner_radius": 8,
            "padding": 10,
            "shadow": True
        }
    }
    
    # Styles des relations
    RELATION_STYLES = {
        "default": {
            "color": RELATION_COLORS["default"],
            "width": 2,
            "arrow_size": 10,
            "magnet_strength": 0.3,
            "curve_tension": 0.5,
            "hover_effect": True,
            "show_control_points": False,
            "line_style": "bezier",
            "cardinality": {
                "source": "1",
                "target": "N",
                "show": True
            }
        },
        "primary": {
            "color": RELATION_COLORS["primary"],
            "width": 2,
            "arrow_size": 10,
            "magnet_strength": 0.3,
            "curve_tension": 0.5,
            "hover_effect": True,
            "show_control_points": False,
            "line_style": "bezier",
            "cardinality": {
                "source": "1",
                "target": "N",
                "show": True
            }
        }
    }
    
    # Styles de l'interface
    UI_STYLES = {
        "toolbar": {
            "background_color": PRIMARY_COLOR,
            "text_color": QColor("#FFFFFF"),
            "font": QFont("Segoe UI", 10),
            "padding": 5,
            "border_radius": 4
        },
        "menu": {
            "background_color": QColor("#FFFFFF"),
            "text_color": TEXT_COLOR,
            "font": QFont("Segoe UI", 10),
            "padding": 5,
            "border_radius": 4,
            "hover_color": QColor("#F0EEF2")  # Violet très pâle
        },
        "status_bar": {
            "background_color": QColor("#F8F7F8"),
            "text_color": TEXT_COLOR,
            "font": QFont("Segoe UI", 9),
            "padding": 3
        },
        "tooltip": {
            "background_color": QColor(0, 0, 0, 180),
            "text_color": QColor("#FFFFFF"),
            "font": QFont("Segoe UI", 9),
            "padding": 5,
            "border_radius": 4
        },
        "button": {
            "background_color": ACCENT_COLOR,
            "text_color": QColor("#2C2C2C"),
            "font": QFont("Segoe UI", 10),
            "padding": 8,
            "border_radius": 4,
            "hover_color": SECONDARY_COLOR
        }
    }
    
    # Styles de la grille
    GRID_STYLES = {
        "color": QColor("#E8E6EB"),  # Violet gris pâle
        "line_width": 1,
        "major_line_color": QColor("#8B7B8E"),  # Violet gris
        "major_line_width": 2,
        "major_line_spacing": 100
    }
    
    @classmethod
    def get_entity_style(cls, style_name="default"):
        """Retourne le style d'une entité"""
        return cls.ENTITY_STYLES.get(style_name, cls.ENTITY_STYLES["default"])
        
    @classmethod
    def get_association_style(cls, style_name="default"):
        """Retourne le style d'une association"""
        return cls.ASSOCIATION_STYLES.get(style_name, cls.ASSOCIATION_STYLES["default"])
        
    @classmethod
    def get_relation_style(cls, style_name="default"):
        """Retourne le style d'une relation"""
        return cls.RELATION_STYLES.get(style_name, cls.RELATION_STYLES["default"])
        
    @classmethod
    def get_ui_style(cls, component):
        """Retourne le style d'un composant de l'interface"""
        return cls.UI_STYLES.get(component, {})
        
    @classmethod
    def get_grid_style(cls):
        """Retourne le style de la grille"""
        return cls.GRID_STYLES
        
    @classmethod
    def apply_theme(cls, app):
        """Applique le thème à l'application"""
        palette = QPalette()
        
        # Couleurs principales
        palette.setColor(QPalette.ColorRole.Window, cls.BACKGROUND_COLOR)
        palette.setColor(QPalette.ColorRole.WindowText, cls.TEXT_COLOR)
        palette.setColor(QPalette.ColorRole.Base, QColor("#ffffff"))
        palette.setColor(QPalette.ColorRole.AlternateBase, cls.BACKGROUND_COLOR)
        palette.setColor(QPalette.ColorRole.ToolTipBase, cls.UI_STYLES["tooltip"]["background_color"])
        palette.setColor(QPalette.ColorRole.ToolTipText, cls.UI_STYLES["tooltip"]["text_color"])
        palette.setColor(QPalette.ColorRole.Text, cls.TEXT_COLOR)
        palette.setColor(QPalette.ColorRole.Button, cls.PRIMARY_COLOR)
        palette.setColor(QPalette.ColorRole.ButtonText, QColor("#ffffff"))
        palette.setColor(QPalette.ColorRole.BrightText, QColor("#ffffff"))
        palette.setColor(QPalette.ColorRole.Link, cls.ACCENT_COLOR)
        palette.setColor(QPalette.ColorRole.Highlight, cls.ACCENT_COLOR)
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
        
        app.setPalette(palette)
        
        # Style global
        app.setStyle("Fusion")
        
        # Police par défaut
        app.setFont(cls.UI_STYLES["menu"]["font"]) 