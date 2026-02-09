#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Convertisseur de modèles MCD vers MLD/MPD/UML
"""

from typing import Dict, List, Any, Optional

class ModelConverter:
    """Convertisseur de modèles"""
    
    def __init__(self):
        pass
    
    def mcd_to_mld(self, mcd: Dict) -> Dict:
        """Convertit un MCD en MLD"""
        mld = {
            "tables": [],
            "foreign_keys": []
        }
        
        # Convertir les entités en tables
        for entity in mcd.get("entities", []):
            if entity.get("is_fictitious", False):
                continue  # Ignorer les entités fictives
                
            table = {
                "name": entity["name"],
                "attributes": []
            }
            
            # Convertir les attributs
            for attr in entity.get("attributes", []):
                table["attributes"].append({
                    "name": attr["name"],
                    "type": attr["type"],
                    "is_primary_key": attr.get("is_primary_key", False),
                    "nullable": attr.get("nullable", True),
                    "is_foreign_key": attr.get("is_foreign_key", False),
                    "references": attr.get("references")
                })
            
            mld["tables"].append(table)
        
        # Convertir les associations en tables de liaison
        for association in mcd.get("associations", []):
            if len(association.get("entities", [])) >= 2:
                # Créer une table de liaison
                link_table = {
                    "name": association["name"],
                    "attributes": []
                }
                
                # Ajouter les clés étrangères vers les entités
                for entity_name in association["entities"]:
                    link_table["attributes"].append({
                        "name": f"{entity_name.lower()}_id",
                        "type": "INTEGER",
                        "is_primary_key": True,
                        "is_foreign_key": True,
                        "references": entity_name,
                        "nullable": False
                    })
                
                # Ajouter les attributs de l'association
                for attr in association.get("attributes", []):
                    link_table["attributes"].append({
                        "name": attr["name"],
                        "type": attr["type"],
                        "is_primary_key": False,
                        "nullable": attr.get("nullable", True)
                    })
                
                mld["tables"].append(link_table)
        
        return mld
    
    def mcd_to_uml(self, mcd: Dict) -> Dict:
        """Convertit un MCD en UML"""
        uml = {
            "classes": [],
            "relationships": []
        }
        
        # Convertir les entités en classes
        for entity in mcd.get("entities", []):
            uml_class = {
                "name": entity["name"],
                "attributes": entity.get("attributes", []),
                "methods": []
            }
            uml["classes"].append(uml_class)
        
        # Convertir les associations en relations
        for association in mcd.get("associations", []):
            relationship = {
                "name": association["name"],
                "type": "association",
                "entities": association.get("entities", []),
                "cardinalities": association.get("cardinalities", {})
            }
            uml["relationships"].append(relationship)
        
        return uml

