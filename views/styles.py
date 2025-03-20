from PyQt6.QtGui import QColor, QPalette, QFont, QIcon
from PyQt6.QtCore import Qt

class AppStyles:
    """Gestionnaire de styles de l'application"""
    
    # Couleurs principales
    PRIMARY_COLOR = QColor("#1a237e")  # Bleu foncé
    SECONDARY_COLOR = QColor("#0d47a1")  # Bleu royal
    ACCENT_COLOR = QColor("#2196f3")  # Bleu clair
    BACKGROUND_COLOR = QColor("#f5f5f5")  # Gris très clair
    TEXT_COLOR = QColor("#212121")  # Gris foncé
    
    # Couleurs des entités
    ENTITY_COLORS = {
        "default": QColor("#ffffff"),  # Blanc
        "primary": QColor("#e3f2fd"),  # Bleu très clair
        "secondary": QColor("#f3e5f5"),  # Violet clair
        "success": QColor("#e8f5e9"),  # Vert clair
        "warning": QColor("#fff3e0"),  # Orange clair
        "error": QColor("#ffebee")  # Rouge clair
    }
    
    # Couleurs des associations
    ASSOCIATION_COLORS = {
        "default": QColor("#f5f5f5"),  # Gris clair
        "primary": QColor("#bbdefb"),  # Bleu clair
        "secondary": QColor("#e1bee7"),  # Violet clair
        "success": QColor("#c8e6c9"),  # Vert clair
        "warning": QColor("#ffe0b2"),  # Orange clair
        "error": QColor("#ffcdd2")  # Rouge clair
    }
    
    # Couleurs des relations
    RELATION_COLORS = {
        "default": QColor("#90a4ae"),  # Gris bleuté
        "primary": QColor("#64b5f6"),  # Bleu
        "secondary": QColor("#ba68c8"),  # Violet
        "success": QColor("#81c784"),  # Vert
        "warning": QColor("#ffb74d"),  # Orange
        "error": QColor("#e57373")  # Rouge
    }
    
    # Styles des entités
    ENTITY_STYLES = {
        "default": {
            "background_color": ENTITY_COLORS["default"],
            "border_color": PRIMARY_COLOR,
            "text_color": TEXT_COLOR,
            "font": QFont("Segoe UI", 10),
            "border_width": 2,
            "corner_radius": 8,
            "padding": 10,
            "shadow": True
        },
        "primary": {
            "background_color": ENTITY_COLORS["primary"],
            "border_color": SECONDARY_COLOR,
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
            "border_color": PRIMARY_COLOR,
            "text_color": TEXT_COLOR,
            "font": QFont("Segoe UI", 10),
            "border_width": 2,
            "corner_radius": 8,
            "padding": 10,
            "shadow": True
        },
        "primary": {
            "background_color": ASSOCIATION_COLORS["primary"],
            "border_color": SECONDARY_COLOR,
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
            "text_color": QColor("#ffffff"),
            "font": QFont("Segoe UI", 10),
            "padding": 5,
            "border_radius": 4
        },
        "menu": {
            "background_color": QColor("#ffffff"),
            "text_color": TEXT_COLOR,
            "font": QFont("Segoe UI", 10),
            "padding": 5,
            "border_radius": 4,
            "hover_color": QColor("#e3f2fd")
        },
        "status_bar": {
            "background_color": QColor("#f5f5f5"),
            "text_color": TEXT_COLOR,
            "font": QFont("Segoe UI", 9),
            "padding": 3
        },
        "tooltip": {
            "background_color": QColor(0, 0, 0, 180),
            "text_color": QColor("#ffffff"),
            "font": QFont("Segoe UI", 9),
            "padding": 5,
            "border_radius": 4
        },
        "button": {
            "background_color": ACCENT_COLOR,
            "text_color": QColor("#ffffff"),
            "font": QFont("Segoe UI", 10),
            "padding": 8,
            "border_radius": 4,
            "hover_color": SECONDARY_COLOR
        }
    }
    
    # Styles de la grille
    GRID_STYLES = {
        "color": QColor("#e0e0e0"),
        "line_width": 1,
        "major_line_color": QColor("#bdbdbd"),
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