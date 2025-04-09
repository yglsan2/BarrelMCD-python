import os
import importlib
from typing import Dict, Optional

class LanguageManager:
    """Gestionnaire de langues pour l'application"""
    
    def __init__(self):
        self.current_language = "fr"  # Langue par défaut
        self.translations: Dict[str, Dict] = {}
        self.available_languages = {
            "fr": "Français",
            "en": "English",
            "es": "Español",
            "de": "Deutsch",
            "it": "Italiano",
            "pt": "Português",
            "ru": "Русский",
            "ar": "العربية",
            "zh": "中文",
            "ja": "日本語",
            "ko": "한국어",
            "lv": "Latviešu"
        }
        self._load_translations()
    
    def _load_translations(self):
        """Charge toutes les traductions disponibles"""
        i18n_dir = os.path.dirname(os.path.abspath(__file__))
        for lang_code in self.available_languages.keys():
            try:
                module = importlib.import_module(f".{lang_code}", package="i18n")
                self.translations[lang_code] = module.translations
            except ImportError:
                print(f"Impossible de charger la traduction pour {lang_code}")
    
    def get_text(self, key: str, lang: Optional[str] = None) -> str:
        """Récupère le texte traduit pour une clé donnée"""
        lang = lang or self.current_language
        try:
            # Gestion des clés imbriquées (ex: "data_types.INTEGER")
            value = self.translations[lang]
            for k in key.split('.'):
                value = value[k]
            return value
        except (KeyError, TypeError):
            # Si la traduction n'est pas trouvée, on essaie en anglais
            if lang != "en":
                return self.get_text(key, "en")
            # Si même l'anglais n'est pas trouvé, on retourne la clé
            return key
    
    def set_language(self, lang_code: str) -> bool:
        """Change la langue courante"""
        if lang_code in self.available_languages:
            self.current_language = lang_code
            return True
        return False
    
    def get_available_languages(self) -> Dict[str, str]:
        """Retourne les langues disponibles avec leurs noms natifs"""
        return self.available_languages
    
    def get_current_language(self) -> str:
        """Retourne le code de la langue courante"""
        return self.current_language
    
    def get_language_name(self, lang_code: str) -> Optional[str]:
        """Retourne le nom natif d'une langue"""
        return self.available_languages.get(lang_code) 