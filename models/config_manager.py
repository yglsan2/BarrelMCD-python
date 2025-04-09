import os
import json
import platform
from pathlib import Path
from typing import Any, Dict, Optional
import logging
import shutil

class ConfigManager:
    """Gestionnaire de configuration multiplateforme"""
    
    def __init__(self, app_name: str = "barrel_mcd"):
        """
        Initialise le gestionnaire de configuration
        
        Args:
            app_name: Nom de l'application
        """
        self.app_name = app_name
        self.config_dir = self._get_config_dir()
        self.config_file = self.config_dir / "config.json"
        self.default_config = self._get_default_config()
        self.current_config = self._load_config()
        
    def _get_config_dir(self) -> Path:
        """
        Obtient le répertoire de configuration selon la plateforme
        
        Returns:
            Path: Chemin du répertoire de configuration
        """
        system = platform.system()
        
        if system == "Windows":
            config_dir = Path(os.environ.get("APPDATA", "")) / self.app_name
        elif system == "Darwin":  # macOS
            config_dir = Path.home() / "Library" / "Application Support" / self.app_name
        else:  # Linux et autres
            config_dir = Path.home() / f".{self.app_name}"
            
        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir
        
    def _get_default_config(self) -> Dict[str, Any]:
        """
        Retourne la configuration par défaut
        
        Returns:
            Dict[str, Any]: Configuration par défaut
        """
        return {
            "theme": "light",
            "language": "fr",
            "auto_save": True,
            "auto_save_interval": 300,  # 5 minutes
            "recent_files": [],
            "max_recent_files": 10,
            "window": {
                "width": 1024,
                "height": 768,
                "maximized": False
            },
            "editor": {
                "font_size": 12,
                "font_family": "Consolas" if platform.system() == "Windows" else "Monaco",
                "tab_size": 4,
                "show_line_numbers": True
            },
            "paths": {
                "data_dir": str(Path.home() / "Documents" / self.app_name),
                "temp_dir": str(Path(tempfile.gettempdir()) / self.app_name),
                "export_dir": str(Path.home() / "Documents" / self.app_name / "exports")
            }
        }
        
    def _load_config(self) -> Dict[str, Any]:
        """
        Charge la configuration depuis le fichier
        
        Returns:
            Dict[str, Any]: Configuration chargée
        """
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                # Fusion avec la configuration par défaut pour les nouvelles options
                return self._merge_configs(self.default_config, config)
            return self.default_config.copy()
        except Exception as e:
            logging.error(f"Erreur lors du chargement de la configuration : {e}")
            return self.default_config.copy()
            
    def _merge_configs(self, default: Dict[str, Any], user: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fusionne la configuration utilisateur avec la configuration par défaut
        
        Args:
            default: Configuration par défaut
            user: Configuration utilisateur
            
        Returns:
            Dict[str, Any]: Configuration fusionnée
        """
        result = default.copy()
        
        for key, value in user.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
                
        return result
        
    def save_config(self) -> bool:
        """
        Sauvegarde la configuration actuelle
        
        Returns:
            bool: True si la sauvegarde a réussi
        """
        try:
            # Créer une sauvegarde de l'ancienne configuration
            if self.config_file.exists():
                backup_file = self.config_file.with_suffix('.json.bak')
                shutil.copy2(self.config_file, backup_file)
                
            # Sauvegarder la nouvelle configuration
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.current_config, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logging.error(f"Erreur lors de la sauvegarde de la configuration : {e}")
            return False
            
    def get(self, key: str, default: Any = None) -> Any:
        """
        Récupère une valeur de configuration
        
        Args:
            key: Clé de configuration (notation pointée supportée)
            default: Valeur par défaut
            
        Returns:
            Any: Valeur de configuration
        """
        try:
            value = self.current_config
            for k in key.split('.'):
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
            
    def set(self, key: str, value: Any) -> bool:
        """
        Définit une valeur de configuration
        
        Args:
            key: Clé de configuration (notation pointée supportée)
            value: Valeur à définir
            
        Returns:
            bool: True si la définition a réussi
        """
        try:
            keys = key.split('.')
            config = self.current_config
            
            # Naviguer jusqu'au dernier niveau
            for k in keys[:-1]:
                if k not in config:
                    config[k] = {}
                config = config[k]
                
            # Définir la valeur
            config[keys[-1]] = value
            return True
        except Exception as e:
            logging.error(f"Erreur lors de la définition de la configuration : {e}")
            return False
            
    def reset(self) -> bool:
        """
        Réinitialise la configuration aux valeurs par défaut
        
        Returns:
            bool: True si la réinitialisation a réussi
        """
        try:
            self.current_config = self.default_config.copy()
            return self.save_config()
        except Exception as e:
            logging.error(f"Erreur lors de la réinitialisation de la configuration : {e}")
            return False
            
    def add_recent_file(self, file_path: str) -> bool:
        """
        Ajoute un fichier à la liste des fichiers récents
        
        Args:
            file_path: Chemin du fichier
            
        Returns:
            bool: True si l'ajout a réussi
        """
        try:
            recent_files = self.get('recent_files', [])
            if file_path in recent_files:
                recent_files.remove(file_path)
            recent_files.insert(0, file_path)
            
            # Limiter le nombre de fichiers récents
            max_files = self.get('max_recent_files', 10)
            recent_files = recent_files[:max_files]
            
            return self.set('recent_files', recent_files)
        except Exception as e:
            logging.error(f"Erreur lors de l'ajout d'un fichier récent : {e}")
            return False
            
    def clear_recent_files(self) -> bool:
        """
        Efface la liste des fichiers récents
        
        Returns:
            bool: True si l'effacement a réussi
        """
        return self.set('recent_files', []) 