from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QFont, QColor, QIcon
from PyQt5.QtWidgets import QSizePolicy

class ResponsiveStyles:
    """Gestion des styles responsifs"""
    
    # Dimensions de référence (iPhone SE)
    REFERENCE_WIDTH = 375
    REFERENCE_HEIGHT = 667
    
    @staticmethod
    def get_scale_factor(width: int, height: int) -> float:
        """Calcule le facteur d'échelle par rapport aux dimensions de référence"""
        width_scale = width / ResponsiveStyles.REFERENCE_WIDTH
        height_scale = height / ResponsiveStyles.REFERENCE_HEIGHT
        return min(width_scale, height_scale)
        
    @staticmethod
    def get_font_size(scale: float) -> int:
        """Calcule la taille de police"""
        return int(14 * scale)
        
    @staticmethod
    def get_button_size(scale: float) -> tuple:
        """Calcule la taille des boutons"""
        return (int(44 * scale), int(44 * scale))
        
    @staticmethod
    def get_toolbar_height(scale: float) -> int:
        """Calcule la hauteur de la barre d'outils"""
        return int(56 * scale)
        
    @staticmethod
    def get_status_bar_height(scale: float) -> int:
        """Calcule la hauteur de la barre d'état"""
        return int(24 * scale)
        
    @staticmethod
    def get_grid_size(scale: float) -> int:
        """Calcule la taille de la grille"""
        return int(20 * scale)
        
    @staticmethod
    def get_margin(scale: float) -> int:
        """Calcule la marge"""
        return int(8 * scale)
        
    @staticmethod
    def get_padding(scale: float) -> int:
        """Calcule le padding"""
        return int(16 * scale)
        
    @staticmethod
    def get_corner_radius(scale: float) -> int:
        """Calcule le rayon des coins arrondis"""
        return int(8 * scale)
        
    @staticmethod
    def get_window_size(scale: float) -> tuple:
        """Calcule la taille de la fenêtre"""
        return (int(375 * scale), int(667 * scale))
        
    @staticmethod
    def get_entity_size(scale: float) -> tuple:
        """Calcule la taille des entités"""
        return (int(120 * scale), int(80 * scale))
        
    @staticmethod
    def get_association_size(scale: float) -> tuple:
        """Calcule la taille des associations"""
        return (int(100 * scale), int(60 * scale))
        
    @staticmethod
    def get_colors() -> dict:
        """Retourne les couleurs"""
        return {
            "primary": "#007AFF",
            "secondary": "#5856D6",
            "success": "#34C759",
            "warning": "#FF9500",
            "error": "#FF3B30",
            "background": "#FFFFFF",
            "surface": "#F2F2F7",
            "text": "#000000",
            "text_secondary": "#666666",
            "border": "#C6C6C8"
        }
        
    @staticmethod
    def get_button_style(scale: float) -> str:
        """Retourne le style des boutons"""
        colors = ResponsiveStyles.get_colors()
        return f"""
            QPushButton {{
                background-color: {colors["primary"]};
                color: white;
                border: none;
                border-radius: {ResponsiveStyles.get_corner_radius(scale)}px;
                padding: {ResponsiveStyles.get_padding(scale)}px;
                font-size: {ResponsiveStyles.get_font_size(scale)}px;
            }}
            QPushButton:hover {{
                background-color: {colors["secondary"]};
            }}
            QPushButton:pressed {{
                background-color: {colors["primary"]};
                opacity: 0.8;
            }}
        """
        
    @staticmethod
    def get_toolbar_style(scale: float) -> str:
        """Retourne le style de la barre d'outils"""
        colors = ResponsiveStyles.get_colors()
        return f"""
            QToolBar {{
                background-color: {colors["background"]};
                border: none;
                border-bottom: 1px solid {colors["border"]};
                spacing: {ResponsiveStyles.get_margin(scale)}px;
                padding: {ResponsiveStyles.get_margin(scale)}px;
            }}
        """
        
    @staticmethod
    def get_status_bar_style(scale: float) -> str:
        """Retourne le style de la barre d'état"""
        colors = ResponsiveStyles.get_colors()
        return f"""
            QStatusBar {{
                background-color: {colors["surface"]};
                border: none;
                border-top: 1px solid {colors["border"]};
                color: {colors["text_secondary"]};
                font-size: {ResponsiveStyles.get_font_size(scale)}px;
            }}
        """
        
    @staticmethod
    def get_menu_style(scale: float) -> str:
        """Retourne le style du menu"""
        colors = ResponsiveStyles.get_colors()
        return f"""
            QMenu {{
                background-color: {colors["background"]};
                border: 1px solid {colors["border"]};
                border-radius: {ResponsiveStyles.get_corner_radius(scale)}px;
                padding: {ResponsiveStyles.get_margin(scale)}px;
            }}
        """
        
    @staticmethod
    def get_dialog_style(scale: float) -> str:
        """Retourne le style des boîtes de dialogue"""
        colors = ResponsiveStyles.get_colors()
        return f"""
            QDialog {{
                background-color: {colors["background"]};
                border: 1px solid {colors["border"]};
                border-radius: {ResponsiveStyles.get_corner_radius(scale)}px;
                padding: {ResponsiveStyles.get_padding(scale)}px;
            }}
        """
        
    @staticmethod
    def get_canvas_style(scale: float) -> str:
        """Retourne le style du canvas"""
        colors = ResponsiveStyles.get_colors()
        return f"""
            QGraphicsView {{
                background-color: {colors["background"]};
                border: none;
            }}
        """
        
    @staticmethod
    def get_window_style(scale: float) -> str:
        """Retourne le style de la fenêtre"""
        colors = ResponsiveStyles.get_colors()
        return f"""
            QMainWindow {{
                background-color: {colors["background"]};
            }}
        """ 