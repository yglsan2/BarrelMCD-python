import os
import shutil
from pathlib import Path
from typing import Optional, List, Union
import platform
import tempfile
import json
import logging
import time

class FileManager:
    """Gestionnaire de fichiers multiplateforme"""
    
    def __init__(self, base_dir: Optional[str] = None):
        """
        Initialise le gestionnaire de fichiers
        
        Args:
            base_dir: Répertoire de base pour les opérations sur les fichiers
        """
        self.base_dir = Path(base_dir) if base_dir else Path(os.environ.get('BARREL_MCD_DATA', 'data'))
        self.temp_dir = Path(tempfile.gettempdir()) / 'barrel_mcd'
        self.setup_directories()
        
    def setup_directories(self):
        """Crée les répertoires nécessaires"""
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
    def get_platform_path(self, path: Union[str, Path]) -> Path:
        """
        Convertit un chemin en chemin compatible avec la plateforme
        
        Args:
            path: Chemin à convertir
            
        Returns:
            Path: Chemin compatible avec la plateforme
        """
        return Path(path).resolve()
        
    def normalize_path(self, path: Union[str, Path]) -> str:
        """
        Normalise un chemin pour l'affichage
        
        Args:
            path: Chemin à normaliser
            
        Returns:
            str: Chemin normalisé
        """
        return str(Path(path).resolve())
        
    def get_relative_path(self, path: Union[str, Path], base: Optional[Union[str, Path]] = None) -> str:
        """
        Obtient un chemin relatif
        
        Args:
            path: Chemin absolu
            base: Chemin de base (optionnel)
            
        Returns:
            str: Chemin relatif
        """
        base_path = Path(base) if base else self.base_dir
        return str(Path(path).relative_to(base_path))
        
    def ensure_directory(self, path: Union[str, Path]) -> Path:
        """
        Crée un répertoire s'il n'existe pas
        
        Args:
            path: Chemin du répertoire
            
        Returns:
            Path: Chemin du répertoire créé
        """
        dir_path = Path(path)
        dir_path.mkdir(parents=True, exist_ok=True)
        return dir_path
        
    def list_files(self, directory: Union[str, Path], pattern: str = "*") -> List[Path]:
        """
        Liste les fichiers d'un répertoire
        
        Args:
            directory: Répertoire à lister
            pattern: Pattern de recherche
            
        Returns:
            List[Path]: Liste des fichiers trouvés
        """
        dir_path = Path(directory)
        return list(dir_path.glob(pattern))
        
    def copy_file(self, source: Union[str, Path], destination: Union[str, Path]) -> bool:
        """
        Copie un fichier
        
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
            logging.error(f"Erreur lors de la copie du fichier : {e}")
            return False
            
    def move_file(self, source: Union[str, Path], destination: Union[str, Path]) -> bool:
        """
        Déplace un fichier
        
        Args:
            source: Chemin source
            destination: Chemin de destination
            
        Returns:
            bool: True si le déplacement a réussi
        """
        try:
            shutil.move(source, destination)
            return True
        except Exception as e:
            logging.error(f"Erreur lors du déplacement du fichier : {e}")
            return False
            
    def delete_file(self, path: Union[str, Path]) -> bool:
        """
        Supprime un fichier
        
        Args:
            path: Chemin du fichier
            
        Returns:
            bool: True si la suppression a réussi
        """
        try:
            Path(path).unlink()
            return True
        except Exception as e:
            logging.error(f"Erreur lors de la suppression du fichier : {e}")
            return False
            
    def create_temp_file(self, suffix: Optional[str] = None) -> Path:
        """
        Crée un fichier temporaire
        
        Args:
            suffix: Suffixe du fichier
            
        Returns:
            Path: Chemin du fichier temporaire
        """
        return Path(tempfile.mktemp(suffix=suffix, dir=str(self.temp_dir)))
        
    def save_json(self, data: dict, path: Union[str, Path]) -> bool:
        """
        Sauvegarde des données au format JSON
        
        Args:
            data: Données à sauvegarder
            path: Chemin du fichier
            
        Returns:
            bool: True si la sauvegarde a réussi
        """
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logging.error(f"Erreur lors de la sauvegarde du fichier JSON : {e}")
            return False
            
    def load_json(self, path: Union[str, Path]) -> Optional[dict]:
        """
        Charge des données au format JSON
        
        Args:
            path: Chemin du fichier
            
        Returns:
            Optional[dict]: Données chargées ou None en cas d'erreur
        """
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"Erreur lors du chargement du fichier JSON : {e}")
            return None
            
    def get_file_info(self, path: Union[str, Path]) -> dict:
        """
        Obtient les informations sur un fichier
        
        Args:
            path: Chemin du fichier
            
        Returns:
            dict: Informations sur le fichier
        """
        file_path = Path(path)
        stats = file_path.stat()
        return {
            'name': file_path.name,
            'size': stats.st_size,
            'created': stats.st_ctime,
            'modified': stats.st_mtime,
            'is_file': file_path.is_file(),
            'is_dir': file_path.is_dir(),
            'extension': file_path.suffix
        }
        
    def cleanup_temp_files(self, max_age_hours: int = 24):
        """
        Nettoie les fichiers temporaires
        
        Args:
            max_age_hours: Âge maximum des fichiers en heures
        """
        try:
            current_time = time.time()
            for file_path in self.temp_dir.glob("*"):
                if file_path.is_file():
                    file_age = current_time - file_path.stat().st_mtime
                    if file_age > (max_age_hours * 3600):
                        file_path.unlink()
        except Exception as e:
            logging.error(f"Erreur lors du nettoyage des fichiers temporaires : {e}") 