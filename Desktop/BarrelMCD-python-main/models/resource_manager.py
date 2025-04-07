import os
import sys
import platform
from pathlib import Path
from typing import Optional, Union
import logging
import shutil

class ResourceManager:
    """Gestionnaire de ressources multiplateforme"""
    
    def __init__(self, app_name: str = "barrel_mcd"):
        """
        Initialise le gestionnaire de ressources
        
        Args:
            app_name: Nom de l'application
        """
        self.app_name = app_name
        self.resource_dir = self._get_resource_dir()
        self.setup_resources()
        
    def _get_resource_dir(self) -> Path:
        """
        Obtient le répertoire de ressources selon la plateforme
        
        Returns:
            Path: Chemin du répertoire de ressources
        """
        if getattr(sys, 'frozen', False):
            # Application packagée (exe, app, etc.)
            base_dir = Path(sys._MEIPASS)
        else:
            # Application en développement
            base_dir = Path(__file__).parent.parent
            
        return base_dir / "resources"
        
    def setup_resources(self):
        """Configure les répertoires de ressources"""
        # Créer les répertoires de ressources s'ils n'existent pas
        self.resource_dir.mkdir(parents=True, exist_ok=True)
        
        # Sous-répertoires
        (self.resource_dir / "icons").mkdir(exist_ok=True)
        (self.resource_dir / "styles").mkdir(exist_ok=True)
        (self.resource_dir / "templates").mkdir(exist_ok=True)
        (self.resource_dir / "locales").mkdir(exist_ok=True)
        
    def get_resource_path(self, resource_name: str, resource_type: str = "") -> Path:
        """
        Obtient le chemin d'une ressource
        
        Args:
            resource_name: Nom de la ressource
            resource_type: Type de ressource (icons, styles, templates, locales)
            
        Returns:
            Path: Chemin de la ressource
        """
        if resource_type:
            return self.resource_dir / resource_type / resource_name
        return self.resource_dir / resource_name
        
    def get_icon_path(self, icon_name: str) -> Path:
        """
        Obtient le chemin d'une icône
        
        Args:
            icon_name: Nom de l'icône
            
        Returns:
            Path: Chemin de l'icône
        """
        return self.get_resource_path(icon_name, "icons")
        
    def get_style_path(self, style_name: str) -> Path:
        """
        Obtient le chemin d'un style
        
        Args:
            style_name: Nom du style
            
        Returns:
            Path: Chemin du style
        """
        return self.get_resource_path(style_name, "styles")
        
    def get_template_path(self, template_name: str) -> Path:
        """
        Obtient le chemin d'un template
        
        Args:
            template_name: Nom du template
            
        Returns:
            Path: Chemin du template
        """
        return self.get_resource_path(template_name, "templates")
        
    def get_locale_path(self, locale: str) -> Path:
        """
        Obtient le chemin d'un fichier de traduction
        
        Args:
            locale: Code de la langue
            
        Returns:
            Path: Chemin du fichier de traduction
        """
        return self.get_resource_path(f"{locale}.json", "locales")
        
    def copy_resource(self, source: Union[str, Path], destination: Union[str, Path]) -> bool:
        """
        Copie une ressource
        
        Args:
            source: Chemin source
            destination: Chemin de destination
            
        Returns:
            bool: True si la copie a réussi
        """
        try:
            shutil.copy2(source, destination)
            return True
        except Exception as e:
            logging.error(f"Erreur lors de la copie de la ressource : {e}")
            return False
            
    def ensure_resource_exists(self, resource_path: Union[str, Path]) -> bool:
        """
        Vérifie si une ressource existe
        
        Args:
            resource_path: Chemin de la ressource
            
        Returns:
            bool: True si la ressource existe
        """
        return Path(resource_path).exists()
        
    def get_platform_specific_resource(self, base_name: str, resource_type: str = "") -> Path:
        """
        Obtient une ressource spécifique à la plateforme
        
        Args:
            base_name: Nom de base de la ressource
            resource_type: Type de ressource
            
        Returns:
            Path: Chemin de la ressource
        """
        system = platform.system().lower()
        platform_specific_name = f"{base_name}_{system}"
        
        # Essayer d'abord la version spécifique à la plateforme
        platform_path = self.get_resource_path(platform_specific_name, resource_type)
        if platform_path.exists():
            return platform_path
            
        # Sinon, utiliser la version générique
        return self.get_resource_path(base_name, resource_type)
        
    def list_resources(self, resource_type: str = "", pattern: str = "*") -> list:
        """
        Liste les ressources d'un type donné
        
        Args:
            resource_type: Type de ressource
            pattern: Pattern de recherche
            
        Returns:
            list: Liste des ressources trouvées
        """
        if resource_type:
            resource_dir = self.resource_dir / resource_type
        else:
            resource_dir = self.resource_dir
            
        return list(resource_dir.glob(pattern))
        
    def create_resource_backup(self, resource_path: Union[str, Path]) -> Optional[Path]:
        """
        Crée une sauvegarde d'une ressource
        
        Args:
            resource_path: Chemin de la ressource
            
        Returns:
            Optional[Path]: Chemin de la sauvegarde ou None en cas d'erreur
        """
        try:
            resource_path = Path(resource_path)
            if not resource_path.exists():
                return None
                
            backup_path = resource_path.with_suffix(f"{resource_path.suffix}.bak")
            shutil.copy2(resource_path, backup_path)
            return backup_path
        except Exception as e:
            logging.error(f"Erreur lors de la création de la sauvegarde : {e}")
            return None
            
    def restore_resource_backup(self, resource_path: Union[str, Path]) -> bool:
        """
        Restaure une sauvegarde de ressource
        
        Args:
            resource_path: Chemin de la ressource
            
        Returns:
            bool: True si la restauration a réussi
        """
        try:
            resource_path = Path(resource_path)
            backup_path = resource_path.with_suffix(f"{resource_path.suffix}.bak")
            
            if not backup_path.exists():
                return False
                
            shutil.copy2(backup_path, resource_path)
            return True
        except Exception as e:
            logging.error(f"Erreur lors de la restauration de la sauvegarde : {e}")
            return False 