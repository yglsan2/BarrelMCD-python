from PyQt5.QtWidgets import QMenu, QAction
from PyQt5.QtCore import Qt, pyqtSignal
from i18n import get_available_languages, set_language, get_current_language, get_text

class LanguageMenu(QMenu):
    """Menu de sélection de langue"""
    
    language_changed = pyqtSignal(str)  # Signal émis quand la langue change
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle(get_text("language"))
        self._setup_menu()
    
    def _setup_menu(self):
        """Configure le menu des langues"""
        current_lang = get_current_language()
        available_languages = get_available_languages()
        
        # Crée une action pour chaque langue disponible
        for lang_code, lang_name in available_languages.items():
            action = QAction(lang_name, self)
            action.setCheckable(True)
            action.setChecked(lang_code == current_lang)
            action.triggered.connect(lambda checked, code=lang_code: self._change_language(code))
            self.addAction(action)
    
    def _change_language(self, lang_code: str):
        """Change la langue de l'application"""
        if set_language(lang_code):
            # Met à jour l'interface
            self._update_menu_items()
            # Émet un signal pour informer les autres widgets
            self.language_changed.emit(lang_code)
    
    def _update_menu_items(self):
        """Met à jour l'état des actions du menu"""
        current_lang = get_current_language()
        for action in self.actions():
            lang_code = action.text()
            action.setChecked(lang_code == current_lang) 