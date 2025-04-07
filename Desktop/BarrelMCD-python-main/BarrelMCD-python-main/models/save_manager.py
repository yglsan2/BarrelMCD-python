import json
import os
from datetime import datetime
from typing import Dict, Any, Optional
from PyQt6.QtCore import QTimer, QObject, pyqtSignal

from .bar_format import BarFormat

class SaveManager(QObject):
    """Gestionnaire de sauvegarde pour Barrel MCD"""
    
    # Signaux
    auto_save_started = pyqtSignal()
    auto_save_finished = pyqtSignal(bool, str)
    save_started = pyqtSignal()
    save_finished = pyqtSignal(bool, str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_file: Optional[str] = None
        self.auto_save_interval = 5 * 60 * 1000  # 5 minutes
        self.auto_save_timer = QTimer(self)
        self.auto_save_timer.timeout.connect(self.auto_save)
        self.auto_save_timer.start()
        self.last_save_time = datetime.now()
        self.is_saving = False
        self.bar_format = BarFormat(self)
        
    def set_current_file(self, file_path: str) -> None:
        """Définit le fichier courant"""
        self.current_file = file_path
        self.last_save_time = datetime.now()
        
    def save(self, data: Dict[str, Any], file_path: Optional[str] = None) -> bool:
        """Sauvegarde les données dans un fichier"""
        if self.is_saving:
            return False
            
        self.is_saving = True
        self.save_started.emit()
        
        try:
            # Utiliser le fichier courant si aucun n'est spécifié
            if file_path is None:
                file_path = self.current_file
                
            if not file_path:
                raise ValueError("Aucun fichier spécifié")
                
            # Sauvegarder au format .bar
            success = self.bar_format.save(data, file_path)
            
            if success:
                self.current_file = file_path
                self.last_save_time = datetime.now()
                self.save_finished.emit(True, "")
            else:
                self.save_finished.emit(False, "Erreur lors de la sauvegarde")
                
            return success
            
        except Exception as e:
            self.save_finished.emit(False, str(e))
            return False
            
        finally:
            self.is_saving = False
            
    def auto_save(self) -> None:
        """Sauvegarde automatique si des modifications ont été faites"""
        if not self.current_file or self.is_saving:
            return
            
        # Vérifier si des modifications ont été faites depuis la dernière sauvegarde
        if (datetime.now() - self.last_save_time).total_seconds() > self.auto_save_interval / 1000:
            self.auto_save_started.emit()
            # La sauvegarde sera gérée par le signal save_finished
            self.save({})  # Les données réelles seront fournies par l'application
            
    def load(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Charge les données depuis un fichier"""
        try:
            return self.bar_format.load(file_path)
        except Exception as e:
            return None
            
    def set_auto_save_interval(self, minutes: int) -> None:
        """Définit l'intervalle de sauvegarde automatique en minutes"""
        self.auto_save_interval = minutes * 60 * 1000
        self.auto_save_timer.setInterval(self.auto_save_interval)
        
    def enable_auto_save(self, enabled: bool) -> None:
        """Active ou désactive la sauvegarde automatique"""
        if enabled:
            self.auto_save_timer.start()
        else:
            self.auto_save_timer.stop() 