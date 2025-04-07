from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QMessageBox
import traceback
import logging
import os
import platform
from pathlib import Path
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
        # Utiliser le répertoire de logs configuré
        log_dir = Path(os.environ.get('BARREL_MCD_LOGS', 'logs'))
        log_file = log_dir / 'barrel_mcd.log'
        
        # Créer le répertoire de logs si nécessaire
        log_dir.mkdir(exist_ok=True)
        
        # Configurer le logging avec le chemin multiplateforme
        logging.basicConfig(
            filename=str(log_file),
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            encoding='utf-8'
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
            
    def validate_file_size(self, file_path: str, max_size_mb: int = 10) -> bool:
        """Vérifie la taille d'un fichier"""
        try:
            size_mb = Path(file_path).stat().st_size / (1024 * 1024)
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
            # Utiliser un timeout plus court sur les systèmes mobiles
            timeout = 1 if platform.system() in ['Android', 'iOS'] else 3
            socket.create_connection(("8.8.8.8", 53), timeout=timeout)
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
            ext = Path(file_path).suffix.lower()
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