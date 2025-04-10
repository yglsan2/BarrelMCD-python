from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QMessageBox
import traceback
import logging
import os
import platform
from pathlib import Path
from typing import Optional, Callable, Any, Dict, List, Union
import sys
import time
from datetime import datetime

class ErrorHandler(QObject):
    """
    Gestionnaire d'erreurs et de robustesse pour l'application.
    
    Cette classe fournit un système complet de gestion des erreurs avec :
    - Logging détaillé des erreurs
    - Gestion des exceptions avec contexte
    - Système de notification utilisateur
    - Mécanismes de récupération automatique
    - Statistiques d'erreurs
    
    Attributes:
        error_occurred (pyqtSignal): Signal émis lors d'une erreur
        warning_occurred (pyqtSignal): Signal émis lors d'un avertissement
        info_occurred (pyqtSignal): Signal émis pour une information
        error_stats (Dict): Statistiques des erreurs
        recovery_attempts (Dict): Tentatives de récupération
    """
    
    # Signaux
    error_occurred = pyqtSignal(str, str)  # titre, message
    warning_occurred = pyqtSignal(str, str)  # titre, message
    info_occurred = pyqtSignal(str, str)  # titre, message
    
    def __init__(self, parent=None):
        """
        Initialise le gestionnaire d'erreurs.
        
        Args:
            parent: Objet parent Qt (optionnel)
        """
        super().__init__(parent)
        self.setup_logging()
        self.error_stats = {}
        self.recovery_attempts = {}
        self.max_recovery_attempts = 3
        self.recovery_cooldown = 60  # secondes
        
    def setup_logging(self):
        """
        Configure le système de logging avec rotation des fichiers.
        
        Le système de logging est configuré pour :
        - Créer des fichiers de log datés
        - Limiter la taille des fichiers
        - Conserver un historique des logs
        """
        try:
            # Utiliser le répertoire de logs configuré
            log_dir = Path(os.environ.get('BARREL_MCD_LOGS', 'logs'))
            log_file = log_dir / f'barrel_mcd_{datetime.now().strftime("%Y%m%d")}.log'
            
            # Créer le répertoire de logs si nécessaire
            log_dir.mkdir(exist_ok=True)
            
            # Configurer le logging avec le chemin multiplateforme
            logging.basicConfig(
                filename=str(log_file),
                level=logging.INFO,
                format='%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
                encoding='utf-8'
            )
            
            # Ajouter un handler pour la console en développement
            if not getattr(sys, 'frozen', False):
                console_handler = logging.StreamHandler()
                console_handler.setLevel(logging.DEBUG)
                formatter = logging.Formatter('%(levelname)s - %(message)s')
                console_handler.setFormatter(formatter)
                logging.getLogger().addHandler(console_handler)
                
        except Exception as e:
            # En cas d'erreur lors de la configuration du logging
            print(f"Erreur critique lors de la configuration du logging: {e}")
            
    def handle_error(self, error: Exception, context: str = "", show_dialog: bool = True, 
                    recovery_callback: Optional[Callable] = None) -> bool:
        """
        Gère une erreur avec possibilité de récupération.
        
        Args:
            error: L'exception à gérer
            context: Contexte de l'erreur
            show_dialog: Afficher une boîte de dialogue
            recovery_callback: Fonction de récupération à exécuter
            
        Returns:
            bool: True si l'erreur a été gérée avec succès
        """
        try:
            error_msg = str(error)
            error_type = type(error).__name__
            
            # Mettre à jour les statistiques
            self._update_error_stats(error_type, context)
            
            # Log de l'erreur
            logging.error(f"{context}: {error_type} - {error_msg}")
            logging.error(traceback.format_exc())
            
            # Vérifier si une récupération est possible
            if recovery_callback and self._can_attempt_recovery(error_type, context):
                try:
                    if recovery_callback():
                        logging.info(f"Récupération réussie pour {error_type} dans {context}")
                        return True
                except Exception as recovery_error:
                    logging.error(f"Échec de la récupération: {recovery_error}")
            
            # Affichage du message d'erreur
            if show_dialog:
                self.error_occurred.emit(
                    "Erreur",
                    f"Une erreur est survenue : {error_msg}\n\nContexte : {context}"
                )
            
            return False
            
        except Exception as e:
            # En cas d'erreur dans le gestionnaire d'erreurs lui-même
            logging.critical(f"Erreur critique dans le gestionnaire d'erreurs: {e}")
            return False
            
    def handle_warning(self, message: str, context: str = "", show_dialog: bool = True) -> None:
        """
        Gère un avertissement.
        
        Args:
            message: Message d'avertissement
            context: Contexte de l'avertissement
            show_dialog: Afficher une boîte de dialogue
        """
        try:
            # Log de l'avertissement
            logging.warning(f"{context}: {message}")
            
            # Affichage du message d'avertissement
            if show_dialog:
                self.warning_occurred.emit(
                    "Avertissement",
                    f"{message}\n\nContexte : {context}"
                )
                
        except Exception as e:
            logging.error(f"Erreur lors de la gestion de l'avertissement: {e}")
            
    def _update_error_stats(self, error_type: str, context: str) -> None:
        """
        Met à jour les statistiques d'erreurs.
        
        Args:
            error_type: Type d'erreur
            context: Contexte de l'erreur
        """
        key = f"{error_type}:{context}"
        if key not in self.error_stats:
            self.error_stats[key] = {
                'count': 0,
                'first_seen': time.time(),
                'last_seen': time.time()
            }
        
        stats = self.error_stats[key]
        stats['count'] += 1
        stats['last_seen'] = time.time()
        
    def _can_attempt_recovery(self, error_type: str, context: str) -> bool:
        """
        Vérifie si une tentative de récupération est possible.
        
        Args:
            error_type: Type d'erreur
            context: Contexte de l'erreur
            
        Returns:
            bool: True si une récupération peut être tentée
        """
        key = f"{error_type}:{context}"
        if key not in self.recovery_attempts:
            self.recovery_attempts[key] = {
                'count': 0,
                'last_attempt': 0
            }
            
        attempts = self.recovery_attempts[key]
        current_time = time.time()
        
        # Vérifier le nombre de tentatives et le délai
        if (attempts['count'] < self.max_recovery_attempts and 
            current_time - attempts['last_attempt'] > self.recovery_cooldown):
            attempts['count'] += 1
            attempts['last_attempt'] = current_time
            return True
            
        return False
        
    def get_error_stats(self) -> Dict[str, Dict]:
        """
        Récupère les statistiques d'erreurs.
        
        Returns:
            Dict[str, Dict]: Statistiques des erreurs
        """
        return self.error_stats
        
    def clear_error_stats(self) -> None:
        """Réinitialise les statistiques d'erreurs."""
        self.error_stats.clear()
        self.recovery_attempts.clear()
        
    def validate_file_size(self, file_path: Union[str, Path], max_size_mb: int = 10) -> bool:
        """
        Vérifie la taille d'un fichier.
        
        Args:
            file_path: Chemin du fichier
            max_size_mb: Taille maximale en MB
            
        Returns:
            bool: True si la taille est acceptable
        """
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
        """
        Vérifie l'utilisation de la mémoire.
        
        Args:
            threshold_mb: Seuil d'utilisation en MB
            
        Returns:
            bool: True si l'utilisation est acceptable
        """
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
        """
        Vérifie la connexion réseau.
        
        Returns:
            bool: True si la connexion est active
        """
        try:
            import socket
            # Utiliser un timeout plus court sur les systèmes mobiles
            timeout = 1 if platform.system() in ['Android', 'iOS'] else 3
            socket.create_connection(("8.8.8.8", 53), timeout=timeout)
            return True
        except Exception as e:
            self.handle_error(e, "Erreur de connexion réseau")
            return False
            
    def check_disk_space(self, path: Union[str, Path], required_mb: int = 100) -> bool:
        """
        Vérifie l'espace disque disponible.
        
        Args:
            path: Chemin à vérifier
            required_mb: Espace requis en MB
            
        Returns:
            bool: True si l'espace est suffisant
        """
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
            
    def validate_file_format(self, file_path: Union[str, Path], allowed_extensions: List[str]) -> bool:
        """
        Vérifie le format d'un fichier.
        
        Args:
            file_path: Chemin du fichier
            allowed_extensions: Extensions autorisées
            
        Returns:
            bool: True si le format est valide
        """
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
        """
        Vérifie les ressources système.
        
        Returns:
            bool: True si les ressources sont suffisantes
        """
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