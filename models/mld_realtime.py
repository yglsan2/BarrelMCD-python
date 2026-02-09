#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Générateur MLD en temps réel
"""

from typing import List, Dict, Any
from PyQt5.QtCore import QObject, pyqtSignal
from .model_converter import ModelConverter

class MLDRealtimeGenerator(QObject):
    """Générateur MLD en temps réel"""
    
    # Signaux
    mld_updated = pyqtSignal(str)  # MLD textuel mis à jour
    
    def __init__(self):
        super().__init__()
        self.converter = ModelConverter()
        self.current_mld = ""
        
    def update_mld(self, entities: List[Dict], associations: List[Dict]):
        """Met à jour le MLD en temps réel"""
        try:
            # Filtrer les entités fictives
            real_entities = [e for e in entities if not e.get("is_fictitious", False)]
            
            # Générer le MLD
            mcd_data = {
                "entities": real_entities,
                "associations": associations
            }
            
            mld_data = self.converter.mcd_to_mld(mcd_data)
            self.current_mld = self._format_mld_text(mld_data)
            self.mld_updated.emit(self.current_mld)
            
        except Exception as e:
            self.current_mld = f"Erreur lors de la génération MLD: {e}"
            self.mld_updated.emit(self.current_mld)
    
    def _format_mld_text(self, mld_data: Dict) -> str:
        """Formate le MLD en texte lisible"""
        lines = []
        lines.append("=" * 60)
        lines.append("MODÈLE LOGIQUE DE DONNÉES (MLD)")
        lines.append("=" * 60)
        lines.append("")
        
        # Tables
        if "tables" in mld_data:
            lines.append("TABLES:")
            lines.append("-" * 60)
            for table in mld_data["tables"]:
                lines.append(f"\nTable: {table.get('name', 'N/A')}")
                lines.append("  Attributs:")
                for attr in table.get("attributes", []):
                    pk_marker = " [PK]" if attr.get("is_primary_key", False) else ""
                    fk_marker = f" [FK -> {attr.get('references', '')}]" if attr.get("is_foreign_key", False) else ""
                    nullable = "" if attr.get("nullable", True) else " NOT NULL"
                    lines.append(f"    - {attr.get('name', 'N/A')}: {attr.get('type', 'N/A')}{pk_marker}{fk_marker}{nullable}")
        
        # Clés étrangères
        if "foreign_keys" in mld_data:
            lines.append("\n" + "-" * 60)
            lines.append("CLÉS ÉTRANGÈRES:")
            for fk in mld_data["foreign_keys"]:
                lines.append(f"  {fk.get('from_table', 'N/A')}.{fk.get('from_column', 'N/A')} -> {fk.get('to_table', 'N/A')}.{fk.get('to_column', 'N/A')}")
        
        return "\n".join(lines)
    
    def get_current_mld(self) -> str:
        """Retourne le MLD actuel"""
        return self.current_mld

