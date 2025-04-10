from .mcd_validator import MCDValidator

class ModelManager(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.mcd_validator = MCDValidator(self)
        self.mcd_validator.validation_completed.connect(self._on_validation_completed)
        self.mcd_validator.validation_error.connect(self._on_validation_error)

    def validate_model(self, model: Dict, model_type: str) -> bool:
        """Valide un modèle selon son type"""
        try:
            if model_type.upper() == "MCD":
                return self.mcd_validator.validate_mcd(model)
            # Autres types de modèles à implémenter ici
            return True
        except Exception as e:
            self.error_handler.handle_error(e, "Erreur lors de la validation du modèle")
            return False

    def _on_validation_completed(self, success: bool, message: str):
        """Gère la fin de la validation"""
        if success:
            self.logger.info(message)
        else:
            self.logger.error(message)

    def _on_validation_error(self, error_type: str, message: str):
        """Gère les erreurs de validation"""
        self.logger.error(f"Erreur de validation ({error_type}): {message}") 