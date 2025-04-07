from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QMessageBox
import traceback
import logging
from typing import Optional, Callable, Any

class ErrorHandler(QObject):
    """Gestionnaire d'erreurs et de robustesse"""
    
    # Signaux
    error_occurred = pyqtSignal(str, str)  # titre, message
    warning_occurred = pyqtSignal(str, str)  # titre, message
    info_occurred = pyqtSignal(str, str)  # titre, message
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_logging()
        
    def setup_logging(self):
        """Configure le système de logging"""
        logging.basicConfig(
            filename='barrel_mcd.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        
    def handle_error(self, error: Exception, context: str = "", show_dialog: bool = True):
        """Gère une erreur"""
        error_msg = str(error)
        error_type = type(error).__name__
        
        # Log de l'erreur
        logging.error(f"{context}: {error_type} - {error_msg}")
        logging.error(traceback.format_exc())
        
        # Affichage du message d'erreur
        if show_dialog:
            self.error_occurred.emit(
                "Erreur",
                f"Une erreur est survenue : {error_msg}\n\nContexte : {context}"
            )
            
    def handle_warning(self, message: str, context: str = "", show_dialog: bool = True):
        """Gère un avertissement"""
        # Log de l'avertissement
        logging.warning(f"{context}: {message}")
        
        # Affichage du message d'avertissement
        if show_dialog:
            self.warning_occurred.emit(
                "Avertissement",
                f"{message}\n\nContexte : {context}"
            )
            
    def handle_info(self, message: str, context: str = "", show_dialog: bool = True):
        """Gère une information"""
        # Log de l'information
        logging.info(f"{context}: {message}")
        
        # Affichage du message d'information
        if show_dialog:
            self.info_occurred.emit(
                "Information",
                f"{message}\n\nContexte : {context}"
            )
            
    def safe_execute(self, func: Callable, *args, **kwargs) -> Optional[Any]:
        """Exécute une fonction de manière sécurisée"""
        try:
            return func(*args, **kwargs)
        except Exception as e:
            self.handle_error(e, f"Erreur lors de l'exécution de {func.__name__}")
            return None
            
    def validate_input(self, value: Any, validation_func: Callable, error_message: str) -> bool:
        """Valide une entrée"""
        try:
            return validation_func(value)
        except Exception as e:
            self.handle_error(e, f"Erreur de validation : {error_message}")
            return False
            
    def check_file_access(self, file_path: str, mode: str = 'r') -> bool:
        """Vérifie l'accès à un fichier"""
        try:
            with open(file_path, mode) as f:
                pass
            return True
        except Exception as e:
            self.handle_error(e, f"Erreur d'accès au fichier : {file_path}")
            return False
            
    def check_directory_access(self, dir_path: str) -> bool:
        """Vérifie l'accès à un répertoire"""
        try:
            import os
            os.access(dir_path, os.R_OK | os.W_OK)
            return True
        except Exception as e:
            self.handle_error(e, f"Erreur d'accès au répertoire : {dir_path}")
            return False
            
    def validate_file_size(self, file_path: str, max_size_mb: int = 10) -> bool:
        """Vérifie la taille d'un fichier"""
        try:
            import os
            size_mb = os.path.getsize(file_path) / (1024 * 1024)
            if size_mb > max_size_mb:
                self.handle_warning(
                    f"Le fichier est trop volumineux ({size_mb:.1f} MB). "
                    f"Taille maximale : {max_size_mb} MB"
                )
                return False
            return True
        except Exception as e:
            self.handle_error(e, f"Erreur lors de la vérification de la taille du fichier : {file_path}")
            return False
            
    def check_memory_usage(self, threshold_mb: int = 500) -> bool:
        """Vérifie l'utilisation de la mémoire"""
        try:
            import psutil
            process = psutil.Process()
            memory_mb = process.memory_info().rss / (1024 * 1024)
            if memory_mb > threshold_mb:
                self.handle_warning(
                    f"Utilisation mémoire élevée ({memory_mb:.1f} MB). "
                    f"Seuil : {threshold_mb} MB"
                )
                return False
            return True
        except Exception as e:
            self.handle_error(e, "Erreur lors de la vérification de la mémoire")
            return False
            
    def validate_network_connection(self) -> bool:
        """Vérifie la connexion réseau"""
        try:
            import socket
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            return True
        except Exception as e:
            self.handle_error(e, "Erreur de connexion réseau")
            return False
            
    def check_disk_space(self, path: str, required_mb: int = 100) -> bool:
        """Vérifie l'espace disque disponible"""
        try:
            import shutil
            free_mb = shutil.disk_usage(path).free / (1024 * 1024)
            if free_mb < required_mb:
                self.handle_warning(
                    f"Espace disque insuffisant ({free_mb:.1f} MB). "
                    f"Espace requis : {required_mb} MB"
                )
                return False
            return True
        except Exception as e:
            self.handle_error(e, f"Erreur lors de la vérification de l'espace disque : {path}")
            return False
            
    def validate_file_format(self, file_path: str, allowed_extensions: list) -> bool:
        """Vérifie le format d'un fichier"""
        try:
            import os
            ext = os.path.splitext(file_path)[1].lower()
            if ext not in allowed_extensions:
                self.handle_warning(
                    f"Format de fichier non supporté : {ext}. "
                    f"Formats autorisés : {', '.join(allowed_extensions)}"
                )
                return False
            return True
        except Exception as e:
            self.handle_error(e, f"Erreur lors de la validation du format du fichier : {file_path}")
            return False
            
    def check_system_resources(self) -> bool:
        """Vérifie les ressources système"""
        try:
            # Vérification de la mémoire
            if not self.check_memory_usage():
                return False
                
            # Vérification de l'espace disque
            if not self.check_disk_space(".", 100):
                return False
                
            # Vérification de la connexion réseau
            if not self.validate_network_connection():
                return False
                
            return True
        except Exception as e:
            self.handle_error(e, "Erreur lors de la vérification des ressources système")
            return False 