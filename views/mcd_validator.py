import logging
import re
from PyQt5.QtCore import QObject, pyqtSignal
from typing import Dict, List

class MCDValidator(QObject):
    """Validateur spécifique pour le Modèle Conceptuel de Données"""
    
    # Signaux
    validation_completed = pyqtSignal(bool)
    validation_error = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.error_handler = None  # À initialiser avec votre gestionnaire d'erreurs
        
    def validate_mcd(self, mcd_data):
        """Valide un modèle MCD selon les règles de modélisation conceptuelle"""
        try:
            # Vérification de la structure de base
            if not isinstance(mcd_data, dict):
                raise ValueError("Le modèle MCD doit être un dictionnaire")

            if "entities" not in mcd_data or "relations" not in mcd_data:
                raise ValueError("Le modèle MCD doit contenir des entités et des relations")

            # Validation des entités
            self._validate_entities(mcd_data["entities"])

            # Validation des relations
            self._validate_relations(mcd_data["relations"], mcd_data["entities"])

            self.validation_completed.emit(True)
            return True

        except Exception as e:
            error_msg = f"Erreur de validation MCD : {str(e)}"
            self.logger.error(error_msg)
            self.validation_error.emit(error_msg)
            return False
            
    def _validate_entities(self, entities):
        """Valide les entités du MCD"""
        if not entities:
            raise ValueError("Le modèle doit contenir au moins une entité")

        entity_names = set()
        for entity_name, entity_data in entities.items():
            # Vérification des doublons
            if entity_name in entity_names:
                raise ValueError(f"Entité en double : {entity_name}")
            entity_names.add(entity_name)

            # Vérification de la structure de l'entité
            if not isinstance(entity_data, dict):
                raise ValueError(f"Structure invalide pour l'entité {entity_name}")

            if "attributes" not in entity_data or "primary_key" not in entity_data:
                raise ValueError(f"L'entité {entity_name} doit avoir des attributs et une clé primaire")

            # Vérification des attributs
            if not entity_data["attributes"]:
                raise ValueError(f"L'entité {entity_name} doit avoir au moins un attribut")

            if entity_data["primary_key"] not in entity_data["attributes"]:
                raise ValueError(f"La clé primaire {entity_data['primary_key']} doit être un attribut de l'entité {entity_name}")
            
    def _validate_relations(self, relations, entities):
        """Valide les relations du MCD"""
        if not isinstance(relations, list):
            raise ValueError("Les relations doivent être une liste")

        relation_names = set()
        for relation in relations:
            # Vérification de la structure de la relation
            required_fields = ["name", "source", "target", "cardinality"]
            for field in required_fields:
                if field not in relation:
                    raise ValueError(f"La relation doit contenir le champ {field}")

            # Vérification des doublons
            if relation["name"] in relation_names:
                raise ValueError(f"Relation en double : {relation['name']}")
            relation_names.add(relation["name"])

            # Vérification des entités référencées
            if relation["source"] not in entities:
                raise ValueError(f"L'entité source {relation['source']} n'existe pas")
            if relation["target"] not in entities:
                raise ValueError(f"L'entité cible {relation['target']} n'existe pas")

            # Vérification de la cardinalité
            valid_cardinalities = ["1,1", "1,n", "n,1", "n,n"]
            if relation["cardinality"] not in valid_cardinalities:
                raise ValueError(f"Cardinalité invalide : {relation['cardinality']}")
            
    def _validate_cardinalities(self, relations: List[Dict]) -> bool:
        """Valide les cardinalités des relations"""
        try:
            valid_cardinalities = {
                "0,1", "1,1", "0,n", "1,n", "n,1", "n,n"
            }
            
            for relation in relations:
                if relation["source_cardinality"] not in valid_cardinalities:
                    self.validation_error.emit(
                        "invalid_cardinality",
                        f"Cardinalité source invalide dans la relation {relation.get('name', '')}: {relation['source_cardinality']}"
                    )
                    return False
                    
                if relation["target_cardinality"] not in valid_cardinalities:
                    self.validation_error.emit(
                        "invalid_cardinality",
                        f"Cardinalité cible invalide dans la relation {relation.get('name', '')}: {relation['target_cardinality']}"
                    )
                    return False
                    
            return True
            
        except Exception as e:
            self.error_handler.handle_error(e, "Erreur lors de la validation des cardinalités")
            return False
            
    def _validate_no_technical_keys(self, entities: Dict) -> bool:
        """Vérifie l'absence de clés techniques dans le MCD"""
        try:
            for entity_name, entity in entities.items():
                for attr in entity["attributes"]:
                    # Vérification des noms techniques
                    if self._is_technical_key(attr["name"]):
                        self.validation_error.emit(
                            "technical_key",
                            f"L'attribut {attr['name']} dans l'entité {entity_name} semble être une clé technique"
                        )
                        return False
                        
                    # Vérification des contraintes techniques
                    if attr.get("primary_key") or attr.get("foreign_key"):
                        self.validation_error.emit(
                            "technical_constraint",
                            f"L'attribut {attr['name']} dans l'entité {entity_name} a une contrainte technique"
                        )
                        return False
                        
            return True
            
        except Exception as e:
            self.error_handler.handle_error(e, "Erreur lors de la validation des clés")
            return False
            
    def _is_technical_key(self, name: str) -> bool:
        """Vérifie si un nom d'attribut semble être une clé technique"""
        technical_patterns = [
            r"^id$",
            r"^id_.*$",
            r".*_id$",
            r"^pk_.*$",
            r"^fk_.*$",
            r"^key_.*$",
            r".*_key$"
        ]
        
        return any(re.match(pattern, name.lower()) for pattern in technical_patterns) 