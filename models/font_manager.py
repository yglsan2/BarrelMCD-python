import platform
from typing import Dict, List, Optional
from pathlib import Path
import logging

class FontManager:
    """Gestionnaire de polices multiplateforme"""
    
    # Polices système par défaut selon la plateforme
    SYSTEM_FONTS = {
        "Windows": {
            "monospace": "Cascadia Code",  # Police moderne pour le code
            "sans": "Segoe UI",  # Police système moderne
            "serif": "Georgia",
            "fallback": "Arial"
        },
        "Darwin": {  # macOS
            "monospace": "SF Mono",
            "sans": "SF Pro",
            "serif": "New York",
            "fallback": "Helvetica"
        },
        "Linux": {
            "monospace": "Fira Code",  # Police moderne pour le code
            "sans": "Inter",
            "serif": "Liberation Serif",
            "fallback": "DejaVu Sans"
        }
    }
    
    # Polices alternatives libres (à télécharger si nécessaire)
    FREE_FONTS = {
        "monospace": [
            "Fira Code",  # Excellente pour le code avec ligatures
            "JetBrains Mono",  # Très lisible
            "Source Code Pro",  # Alternative classique
            "IBM Plex Mono"  # Style professionnel
        ],
        "sans": [
            "Inter",  # Moderne et très lisible
            "Roboto",  # Style Material Design
            "Open Sans",  # Classique et fiable
            "Noto Sans"  # Excellente couverture Unicode
        ],
        "serif": [
            "Merriweather",  # Élégante et lisible
            "Source Serif Pro",  # Classique
            "IBM Plex Serif",  # Style professionnel
            "Lora"  # Moderne et élégante
        ]
    }
    
    def __init__(self):
        """Initialise le gestionnaire de polices"""
        self.system = platform.system()
        self.available_fonts = self._get_available_fonts()
        
    def _get_available_fonts(self) -> Dict[str, List[str]]:
        """
        Récupère les polices disponibles sur le système
        
        Returns:
            Dict[str, List[str]]: Polices disponibles par catégorie
        """
        available = {
            "monospace": [],
            "sans": [],
            "serif": []
        }
        
        # Ajouter les polices système par défaut
        system_fonts = self.SYSTEM_FONTS.get(self.system, self.SYSTEM_FONTS["Linux"])
        for category, font in system_fonts.items():
            if category != "fallback":
                available[category].append(font)
                
        # Ajouter les polices libres si elles sont installées
        for category, fonts in self.FREE_FONTS.items():
            available[category].extend(fonts)
            
        return available
        
    def get_font(self, category: str, size: int = 12, weight: str = "normal") -> str:
        """
        Obtient une police pour une catégorie donnée
        
        Args:
            category: Catégorie de police (monospace, sans, serif)
            size: Taille de la police
            weight: Graisse de la police (normal, bold, etc.)
            
        Returns:
            str: Spécification de police CSS
        """
        if category not in self.available_fonts:
            category = "sans"  # Fallback sur sans-serif
            
        fonts = self.available_fonts[category]
        if not fonts:
            # Fallback sur les polices système par défaut
            system_fonts = self.SYSTEM_FONTS.get(self.system, self.SYSTEM_FONTS["Linux"])
            fonts = [system_fonts[category], system_fonts["fallback"]]
            
        # Construire la liste des polices avec fallbacks
        font_list = ", ".join(f'"{font}"' for font in fonts)
        
        # Ajouter les polices système génériques en dernier recours
        generic_fonts = {
            "monospace": "monospace",
            "sans": "sans-serif",
            "serif": "serif"
        }
        font_list += f", {generic_fonts[category]}"
        
        return f"{font_list} {size}px {weight}"
        
    def get_code_font(self, size: int = 12) -> str:
        """
        Obtient une police optimisée pour le code
        
        Args:
            size: Taille de la police
            
        Returns:
            str: Spécification de police CSS
        """
        return self.get_font("monospace", size)
        
    def get_ui_font(self, size: int = 12) -> str:
        """
        Obtient une police optimisée pour l'interface utilisateur
        
        Args:
            size: Taille de la police
            
        Returns:
            str: Spécification de police CSS
        """
        return self.get_font("sans", size)
        
    def get_title_font(self, size: int = 16) -> str:
        """
        Obtient une police optimisée pour les titres
        
        Args:
            size: Taille de la police
            
        Returns:
            str: Spécification de police CSS
        """
        return self.get_font("serif", size, "bold")
        
    def get_font_styles(self) -> Dict[str, str]:
        """
        Obtient les styles de police pour l'application
        
        Returns:
            Dict[str, str]: Styles CSS pour les différentes catégories de texte
        """
        return {
            "code": self.get_code_font(),
            "ui": self.get_ui_font(),
            "title": self.get_title_font(),
            "heading1": self.get_title_font(24),
            "heading2": self.get_title_font(20),
            "heading3": self.get_title_font(16),
            "normal": self.get_ui_font(),
            "small": self.get_ui_font(10),
            "large": self.get_ui_font(14)
        }
        
    def get_font_css(self) -> str:
        """
        Génère le CSS pour les polices de l'application
        
        Returns:
            str: CSS pour les polices
        """
        styles = self.get_font_styles()
        css = []
        
        for class_name, font_spec in styles.items():
            css.append(f".font-{class_name} {{")
            css.append(f"    font-family: {font_spec};")
            css.append("}")
            
        return "\n".join(css) 