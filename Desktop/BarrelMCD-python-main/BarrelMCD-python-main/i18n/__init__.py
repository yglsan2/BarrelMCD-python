from .language_manager import LanguageManager

# Instance globale du gestionnaire de langues
language_manager = LanguageManager()

# Fonction utilitaire pour obtenir un texte traduit
def get_text(key: str, lang: str = None) -> str:
    """Récupère un texte traduit"""
    return language_manager.get_text(key, lang)

# Fonction utilitaire pour changer la langue
def set_language(lang_code: str) -> bool:
    """Change la langue courante"""
    return language_manager.set_language(lang_code)

# Fonction utilitaire pour obtenir les langues disponibles
def get_available_languages():
    """Retourne les langues disponibles"""
    return language_manager.get_available_languages()

# Fonction utilitaire pour obtenir la langue courante
def get_current_language() -> str:
    """Retourne la langue courante"""
    return language_manager.get_current_language() 