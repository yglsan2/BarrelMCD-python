from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QComboBox, QTextEdit, QTableWidget, QTableWidgetItem, QSpinBox, QCheckBox, QGroupBox, QLineEdit, QGridLayout, QToolBar, QTabWidget, QMessageBox, QInputDialog
from enum import Enum
from typing import List, Dict, Optional
import json
import pandas as pd
from .data_analyzer import DataAnalyzer
from .model_converter import ModelConverter, ConversionType
from .sql_inspector import SQLInspector
from .mcd_drawer import MCDDrawer

class ModelType(Enum):
    """Types de modèles supportés"""
    MCD = "MCD"  # Modèle Conceptuel de Données
    UML = "UML"  # Unified Modeling Language
    MLD = "MLD"  # Modèle Logique de Données

class RelationType(Enum):
    """Types de relations supportés"""
    ONE_TO_ONE = "1,1"
    ONE_TO_MANY = "1,n"
    MANY_TO_ONE = "n,1"
    MANY_TO_MANY = "n,n"
    COMPOSITION = "composition"
    AGGREGATION = "aggregation"
    INHERITANCE = "inheritance"

class AttributeType(Enum):
    """Types d'attributs supportés"""
    STRING = "VARCHAR"
    INTEGER = "INT"
    FLOAT = "FLOAT"
    BOOLEAN = "BOOLEAN"
    DATE = "DATE"
    DATETIME = "DATETIME"
    TEXT = "TEXT"
    JSON = "JSON"
    BLOB = "BLOB"
    ENUM = "ENUM"
    SET = "SET"
    UUID = "UUID"
    TIMESTAMP = "TIMESTAMP"
    DECIMAL = "DECIMAL"
    BINARY = "BINARY"
    XML = "XML"
    POINT = "POINT"
    GEOMETRY = "GEOMETRY"
    ARRAY = "ARRAY"
    CUSTOM = "CUSTOM"  # Pour les types personnalisés

class AttributeConstraint(Enum):
    """Contraintes d'attributs supportées"""
    NOT_NULL = "NOT NULL"
    UNIQUE = "UNIQUE"
    PRIMARY_KEY = "PRIMARY KEY"
    FOREIGN_KEY = "FOREIGN KEY"
    CHECK = "CHECK"
    DEFAULT = "DEFAULT"

class Entity:
    """Classe représentant une entité dans un modèle"""
    def __init__(self, name: str, attributes: List[Dict] = None, primary_key: List[str] = None):
        self.name = name
        self.attributes = attributes or []
        self.primary_key = primary_key or []
        self.relations = []
        self.unique_constraints = []
        
    def add_attribute(self, name: str, type: AttributeType, constraints: List[AttributeConstraint] = None, 
                     is_nullable: bool = True, is_unique: bool = False, default: str = None, 
                     custom_type: str = None, custom_type_warning: bool = False):
        """Ajoute un attribut à l'entité avec des contraintes.
        
        Args:
            name: Nom de l'attribut
            type: Type de l'attribut
            constraints: Liste des contraintes
            is_nullable: Si l'attribut peut être null
            is_unique: Si l'attribut doit être unique
            default: Valeur par défaut
            custom_type: Type personnalisé si type est CUSTOM
            custom_type_warning: Si un avertissement a été accepté pour le type personnalisé
        """
        # Vérifier l'unicité du nom de l'attribut
        if any(attr["name"] == name for attr in self.attributes):
            raise ValueError(f"Un attribut avec le nom '{name}' existe déjà dans l'entité '{self.name}'")
            
        # Gérer le type personnalisé
        if type == AttributeType.CUSTOM and not custom_type:
            raise ValueError("Le type personnalisé doit être spécifié")
            
        # Construire les contraintes
        final_constraints = constraints or []
        if not is_nullable:
            final_constraints.append(AttributeConstraint.NOT_NULL)
        if is_unique:
            final_constraints.append(AttributeConstraint.UNIQUE)
            
        attribute = {
            "name": name,
            "type": type,
            "constraints": final_constraints,
            "nullable": is_nullable,
            "unique": is_unique,
            "default": default
        }
        
        if type == AttributeType.CUSTOM:
            attribute.update({
                "custom_type": custom_type,
                "custom_type_warning": custom_type_warning
            })
            
        self.attributes.append(attribute)
        
    def add_relation(self, target: str, type: RelationType, attributes: List[Dict] = None):
        """Ajoute une relation à l'entité"""
        self.relations.append({
            "target": target,
            "type": type,
            "attributes": attributes or []
        })

    def add_unique_constraint(self, attribute_names: List[str], name: str = None):
        """Ajoute une contrainte d'unicité sur plusieurs attributs.
        
        Args:
            attribute_names: Liste des noms d'attributs
            name: Nom de la contrainte (optionnel)
        """
        # Vérifier que tous les attributs existent
        for attr_name in attribute_names:
            if not any(attr["name"] == attr_name for attr in self.attributes):
                raise ValueError(f"L'attribut '{attr_name}' n'existe pas dans l'entité '{self.name}'")
                
        constraint = {
            "name": name or f"unique_{self.name}_{'_'.join(attribute_names)}",
            "attributes": attribute_names
        }
        
        self.unique_constraints.append(constraint)

class SemanticAnalyzer:
    """Analyseur sémantique pour les relations et cardinalités"""
    
    def __init__(self):
        self.nlp_patterns = {
            "fr": {
                "possessifs": ["son", "sa", "ses", "leur", "leurs"],
                "quantificateurs": ["plusieurs", "tous", "chaque", "certain", "quelques", "nombreux"],
                "articles": ["le", "la", "les", "un", "une", "des"],
                "verbes_possession": ["avoir", "posséder", "contenir", "inclure", "comprendre"],
                "verbes_appartenance": ["appartenir", "faire partie", "dépendre", "être lié"],
                "verbes_composition": ["composer", "constituer", "former", "regrouper"]
            },
            "en": {
                "possessifs": ["its", "their", "his", "her"],
                "quantificateurs": ["many", "several", "each", "some", "numerous", "all"],
                "articles": ["the", "a", "an"],
                "verbes_possession": ["have", "own", "contain", "include", "comprise"],
                "verbes_appartenance": ["belong", "be part", "depend", "be linked"],
                "verbes_composition": ["compose", "constitute", "form", "group"]
            }
        }
        
        self.domain_patterns = {
            "commerce": {
                "one_to_many": [
                    ("commande", "produit"),
                    ("client", "commande"),
                    ("catégorie", "produit")
                ],
                "many_to_many": [
                    ("client", "produit"),
                    ("commande", "promotion")
                ]
            },
            "education": {
                "one_to_many": [
                    ("cours", "étudiant"),
                    ("professeur", "cours"),
                    ("département", "professeur")
                ],
                "many_to_many": [
                    ("étudiant", "cours"),
                    ("professeur", "projet")
                ]
            },
            "rh": {
                "one_to_many": [
                    ("département", "employé"),
                    ("manager", "équipe"),
                    ("projet", "tâche")
                ],
                "many_to_many": [
                    ("employé", "projet"),
                    ("compétence", "poste")
                ]
            }
        }
        
        self.learned_patterns = {}
        
    def analyze_text(self, text: str, lang: str = "fr") -> Dict:
        """Analyse un texte pour en extraire les informations sémantiques.
        
        Args:
            text: Texte à analyser
            lang: Langue du texte
            
        Returns:
            Dict: Informations sémantiques extraites
        """
        words = text.lower().split()
        info = {
            "quantification": None,
            "possession": False,
            "composition": False,
            "direction": None
        }
        
        patterns = self.nlp_patterns[lang]
        
        # Analyser les quantificateurs
        for word in words:
            if word in patterns["quantificateurs"]:
                info["quantification"] = "multiple"
                break
                
        # Analyser les verbes
        for word in words:
            if word in patterns["verbes_possession"]:
                info["possession"] = True
            if word in patterns["verbes_composition"]:
                info["composition"] = True
                
        # Déterminer la direction de la relation
        for i, word in enumerate(words):
            if word in patterns["verbes_possession"] and i > 0:
                info["direction"] = "forward"
            elif word in patterns["verbes_appartenance"] and i > 0:
                info["direction"] = "backward"
                
        return info
        
    def analyze_domain(self, source: str, target: str) -> Optional[RelationType]:
        """Analyse les entités selon le domaine métier.
        
        Args:
            source: Nom de l'entité source
            target: Nom de l'entité cible
            
        Returns:
            RelationType: Type de relation suggéré ou None
        """
        source = source.lower()
        target = target.lower()
        
        # Vérifier dans tous les domaines
        for domain, patterns in self.domain_patterns.items():
            # Vérifier les patterns one-to-many
            for src, tgt in patterns["one_to_many"]:
                if src in source and tgt in target:
                    return RelationType.ONE_TO_MANY
                elif src in target and tgt in source:
                    return RelationType.MANY_TO_ONE
                    
            # Vérifier les patterns many-to-many
            for ent1, ent2 in patterns["many_to_many"]:
                if (ent1 in source and ent2 in target) or \
                   (ent1 in target and ent2 in source):
                    return RelationType.MANY_TO_MANY
                    
        return None
        
    def learn_pattern(self, source: str, target: str, relation_type: RelationType, validated: bool = True):
        """Apprend un nouveau pattern de relation.
        
        Args:
            source: Nom de l'entité source
            target: Nom de l'entité cible
            relation_type: Type de relation
            validated: Si le pattern a été validé par l'utilisateur
        """
        if validated:
            key = (source.lower(), target.lower())
            self.learned_patterns[key] = {
                "type": relation_type,
                "count": self.learned_patterns.get(key, {}).get("count", 0) + 1
            }
            
    def get_learned_suggestion(self, source: str, target: str) -> Optional[RelationType]:
        """Obtient une suggestion basée sur les patterns appris.
        
        Args:
            source: Nom de l'entité source
            target: Nom de l'entité cible
            
        Returns:
            RelationType: Type de relation suggéré ou None
        """
        key = (source.lower(), target.lower())
        if key in self.learned_patterns:
            return self.learned_patterns[key]["type"]
        return None

class CardinalityAnalyzer:
    """Classe pour analyser et deviner les cardinalités des relations"""
    
    def __init__(self):
        self.semantic_analyzer = SemanticAnalyzer()
        # Patterns pour détecter les relations 1,n
        self.one_to_many_patterns = {
            "possède": {"source": "1", "target": "n"},
            "contient": {"source": "1", "target": "n"},
            "gère": {"source": "1", "target": "n"},
            "compose": {"source": "1", "target": "n"},
            "regroupe": {"source": "1", "target": "n"}
        }
        
        # Patterns pour détecter les relations n,n
        self.many_to_many_patterns = {
            "participe": True,
            "utilise": True,
            "appartient": True,
            "associé": True,
            "lié": True
        }
        
        # Mots indiquant une relation parent-enfant (1,n)
        self.parent_child_indicators = {
            "parent": True,
            "enfant": True,
            "catégorie": True,
            "sous": True,
            "super": True
        }
        
    def analyze_relation(self, source_entity: Entity, target_entity: Entity, relation_name: str = None, description: str = None) -> RelationType:
        """Analyse et devine la cardinalité d'une relation.
        
        Args:
            source_entity: Entité source
            target_entity: Entité cible
            relation_name: Nom de la relation (optionnel)
            description: Description textuelle de la relation (optionnel)
            
        Returns:
            RelationType: Type de relation deviné
        """
        # 1. Vérifier les patterns appris
        learned_type = self.semantic_analyzer.get_learned_suggestion(
            source_entity.name, target_entity.name
        )
        if learned_type:
            return learned_type
            
        # 2. Analyser le domaine métier
        domain_type = self.semantic_analyzer.analyze_domain(
            source_entity.name, target_entity.name
        )
        if domain_type:
            return domain_type
            
        # 3. Analyser la description sémantique
        if description:
            semantic_info = self.semantic_analyzer.analyze_text(description)
            if semantic_info["quantification"] == "multiple":
                if semantic_info["direction"] == "forward":
                    return RelationType.ONE_TO_MANY
                elif semantic_info["direction"] == "backward":
                    return RelationType.MANY_TO_ONE
            if semantic_info["composition"]:
                return RelationType.COMPOSITION
                
        # 4. Utiliser l'analyse existante
        return super().analyze_relation(source_entity, target_entity, relation_name)
        
    def validate_cardinality(self, source_entity: Entity, target_entity: Entity, 
                           relation_type: RelationType, description: str = None) -> List[str]:
        """Valide une cardinalité et retourne les erreurs potentielles.
        
        Args:
            source_entity: Entité source
            target_entity: Entité cible
            relation_type: Type de relation
            description: Description textuelle de la relation
            
        Returns:
            List[str]: Liste des erreurs détectées
        """
        errors = []
        
        # Vérifier la cohérence avec le domaine métier
        domain_type = self.semantic_analyzer.analyze_domain(
            source_entity.name, target_entity.name
        )
        if domain_type and domain_type != relation_type:
            errors.append(
                f"La cardinalité {relation_type.value} ne correspond pas aux pratiques "
                f"habituelles du domaine qui suggèrent {domain_type.value}"
            )
            
        # Vérifier la cohérence avec la description
        if description:
            semantic_info = self.semantic_analyzer.analyze_text(description)
            if semantic_info["quantification"] == "multiple" and relation_type == RelationType.ONE_TO_ONE:
                errors.append(
                    "La description suggère une relation multiple mais la cardinalité est 1,1"
                )
                
        # Vérifier la cohérence structurelle
        if self._has_foreign_key(source_entity, target_entity) and \
           relation_type in [RelationType.ONE_TO_MANY, RelationType.MANY_TO_MANY]:
            errors.append(
                f"L'entité {source_entity.name} contient une clé étrangère vers "
                f"{target_entity.name} mais la cardinalité suggère l'inverse"
            )
            
        return errors
        
    def _has_foreign_key(self, entity: Entity, target: Entity) -> bool:
        """Vérifie si une entité a une clé étrangère vers une autre."""
        target_name = target.name.lower()
        for attr in entity.attributes:
            attr_name = attr["name"].lower()
            if (f"{target_name}_id" in attr_name or 
                f"id_{target_name}" in attr_name or 
                f"fk_{target_name}" in attr_name):
                return True
        return False
        
    def _has_collection_indicators(self, entity: Entity) -> bool:
        """Vérifie si une entité a des indicateurs de collection."""
        name = entity.name.lower()
        collection_indicators = ["liste", "collection", "groupe", "ensemble", "s"]
        return any(indicator in name for indicator in collection_indicators)
        
    def suggest_cardinality_correction(self, relation_type: RelationType, source_entity: Entity, target_entity: Entity) -> str:
        """Suggère une correction pour une cardinalité potentiellement incorrecte.
        
        Args:
            relation_type: Type de relation actuel
            source_entity: Entité source
            target_entity: Entité cible
            
        Returns:
            str: Message de suggestion ou None si pas de correction nécessaire
        """
        suggested_type = self.analyze_relation(source_entity, target_entity)
        
        if suggested_type != relation_type:
            message = f"La cardinalité actuelle ({relation_type.value}) pourrait être incorrecte. "
            message += f"Suggestion : utiliser {suggested_type.value} car :\n"
            
            if self._has_foreign_key(source_entity, target_entity):
                message += f"- {source_entity.name} contient une référence vers {target_entity.name}\n"
            if self._has_foreign_key(target_entity, source_entity):
                message += f"- {target_entity.name} contient une référence vers {source_entity.name}\n"
            if self._has_collection_indicators(source_entity):
                message += f"- {source_entity.name} semble être une collection\n"
            if self._has_collection_indicators(target_entity):
                message += f"- {target_entity.name} semble être une collection\n"
                
            message += "\nRègles de cardinalité :\n"
            message += "- 1,1 : Un élément est associé à exactement un autre\n"
            message += "- 1,n : Un élément peut être associé à plusieurs autres\n"
            message += "- n,1 : Plusieurs éléments peuvent être associés à un seul\n"
            message += "- n,n : Plusieurs éléments peuvent être associés à plusieurs autres"
            
            return message
            
        return None

class ModelManager(QObject):
    """Classe pour gérer les modèles de données"""
    
    # Signaux
    model_updated = pyqtSignal(str)  # Émet le modèle mis à jour
    error_occurred = pyqtSignal(str)  # Émet les messages d'erreur
    custom_type_warning = pyqtSignal(str, str)  # Émet un avertissement pour un type personnalisé
    duplicate_relation_warning = pyqtSignal(str)  # Émet un avertissement pour une relation en double
    validation_errors = pyqtSignal(str)  # Émet les erreurs de validation
    
    def __init__(self):
        super().__init__()
        self.models = {}
        self.current_model = None
        self.current_model_type = None
        self.custom_types = set()  # Pour suivre les types personnalisés
        self.cardinality_analyzer = CardinalityAnalyzer()
        self.data_analyzer = DataAnalyzer()
        self.model_converter = ModelConverter()
        self.sql_inspector = SQLInspector()
        
    def analyze_data(self, data: Dict, data_type: str = "json") -> Dict:
        """Analyse les données et génère un modèle conceptuel."""
        # Analyser les données avec DataAnalyzer
        mcd = self.data_analyzer.analyze_data(data)
        
        # Stocker le modèle courant
        self.current_model = mcd
        self.current_model_type = "MCD"
        
        return mcd
        
    def convert_model(self, target_type: str) -> Dict:
        """Convertit le modèle courant vers un autre format."""
        if not self.current_model:
            raise ValueError("Aucun modèle n'est chargé")
            
        # Déterminer le type de conversion
        conversion_type = self._get_conversion_type(self.current_model_type, target_type)
        
        # Convertir le modèle
        converted_model = self.model_converter.convert_model(
            self.current_model,
            conversion_type
        )
        
        # Mettre à jour le modèle courant
        self.current_model = converted_model
        self.current_model_type = target_type
        
        return converted_model
        
    def generate_sql(self) -> str:
        """Génère le script SQL à partir du modèle courant."""
        if self.current_model_type != "MLD":
            # Convertir d'abord en MLD si nécessaire
            self.convert_model("MLD")
            
        return self.model_converter.convert_model(
            self.current_model,
            ConversionType.MLD_TO_SQL
        )
        
    def validate_model(self) -> List[Dict]:
        """Valide le modèle courant."""
        if not self.current_model:
            raise ValueError("Aucun modèle n'est chargé")
            
        issues = []
        
        if self.current_model_type == "MCD":
            # Valider la cohérence du MCD
            issues.extend(self._validate_mcd())
        elif self.current_model_type == "MLD":
            # Valider la cohérence du MLD
            issues.extend(self._validate_mld())
        elif self.current_model_type == "SQL":
            # Valider le schéma SQL
            issues.extend(self.sql_inspector.validate_schema())
            
        return issues
        
    def suggest_optimizations(self) -> List[Dict]:
        """Suggère des optimisations pour le modèle courant."""
        if not self.current_model:
            raise ValueError("Aucun modèle n'est chargé")
            
        suggestions = []
        
        if self.current_model_type == "MCD":
            # Suggestions pour le MCD
            suggestions.extend(self._suggest_mcd_optimizations())
        elif self.current_model_type == "MLD":
            # Suggestions pour le MLD
            suggestions.extend(self._suggest_mld_optimizations())
        elif self.current_model_type == "SQL":
            # Suggestions pour le schéma SQL
            suggestions.extend(self.sql_inspector.suggest_optimizations())
            
        return suggestions
        
    def draw_mcd(self, scene) -> None:
        """Dessine le MCD dans la scène graphique."""
        if self.current_model_type != "MCD":
            raise ValueError("Le modèle courant n'est pas un MCD")
            
        drawer = MCDDrawer(scene)
        drawer.draw_mcd(self.current_model)
        
    def _get_conversion_type(self, source_type: str, target_type: str) -> ConversionType:
        """Détermine le type de conversion approprié."""
        conversions = {
            ("MCD", "UML"): ConversionType.MCD_TO_UML,
            ("MCD", "MLD"): ConversionType.MCD_TO_MLD,
            ("UML", "MLD"): ConversionType.UML_TO_MLD,
            ("MLD", "SQL"): ConversionType.MLD_TO_SQL
        }
        
        key = (source_type, target_type)
        if key not in conversions:
            raise ValueError(f"Conversion de {source_type} vers {target_type} non supportée")
            
        return conversions[key]
        
    def _validate_mcd(self) -> List[Dict]:
        """Valide la cohérence du MCD."""
        issues = []
        
        # 1. Vérifier les entités
        for entity_name, entity in self.current_model["entities"].items():
            # Vérifier la présence d'attributs
            if not entity["attributes"]:
                issues.append({
                    "type": "empty_entity",
                    "severity": "error",
                    "entity": entity_name,
                    "message": "L'entité n'a pas d'attributs"
                })
                
            # Vérifier la présence d'une clé primaire
            if not any(attr.get("primary_key") for attr in entity["attributes"]):
                issues.append({
                    "type": "missing_primary_key",
                    "severity": "error",
                    "entity": entity_name,
                    "message": "L'entité n'a pas de clé primaire"
                })
                
        # 2. Vérifier les relations
        for relation in self.current_model["relations"]:
            # Vérifier l'existence des entités
            if relation["source"] not in self.current_model["entities"]:
                issues.append({
                    "type": "invalid_relation",
                    "severity": "error",
                    "relation": relation.get("name", ""),
                    "message": f"L'entité source {relation['source']} n'existe pas"
                })
                
            if relation["target"] not in self.current_model["entities"]:
                issues.append({
                    "type": "invalid_relation",
                    "severity": "error",
                    "relation": relation.get("name", ""),
                    "message": f"L'entité cible {relation['target']} n'existe pas"
                })
                
            # Vérifier les cardinalités
            if not self._is_valid_cardinality(relation["source_cardinality"]):
                issues.append({
                    "type": "invalid_cardinality",
                    "severity": "error",
                    "relation": relation.get("name", ""),
                    "message": f"Cardinalité source invalide: {relation['source_cardinality']}"
                })
                
            if not self._is_valid_cardinality(relation["target_cardinality"]):
                issues.append({
                    "type": "invalid_cardinality",
                    "severity": "error",
                    "relation": relation.get("name", ""),
                    "message": f"Cardinalité cible invalide: {relation['target_cardinality']}"
                })
                
        return issues
        
    def _validate_mld(self) -> List[Dict]:
        """Valide la cohérence du MLD."""
        issues = []
        
        # 1. Vérifier les tables
        for table_name, table in self.current_model["tables"].items():
            # Vérifier la présence de colonnes
            if not table["columns"]:
                issues.append({
                    "type": "empty_table",
                    "severity": "error",
                    "table": table_name,
                    "message": "La table n'a pas de colonnes"
                })
                
            # Vérifier la clé primaire
            if not table["primary_key"]:
                issues.append({
                    "type": "missing_primary_key",
                    "severity": "error",
                    "table": table_name,
                    "message": "La table n'a pas de clé primaire"
                })
                
        # 2. Vérifier les clés étrangères
        for fk in self.current_model["foreign_keys"]:
            # Vérifier l'existence des tables
            if fk["table"] not in self.current_model["tables"]:
                issues.append({
                    "type": "invalid_foreign_key",
                    "severity": "error",
                    "foreign_key": fk["name"],
                    "message": f"La table source {fk['table']} n'existe pas"
                })
                
            if fk["referenced_table"] not in self.current_model["tables"]:
                issues.append({
                    "type": "invalid_foreign_key",
                    "severity": "error",
                    "foreign_key": fk["name"],
                    "message": f"La table référencée {fk['referenced_table']} n'existe pas"
                })
                
        return issues
        
    def _suggest_mcd_optimizations(self) -> List[Dict]:
        """Suggère des optimisations pour le MCD."""
        suggestions = []
        
        # 1. Détecter les entités faibles potentielles
        weak_entities = self._detect_weak_entities()
        for entity in weak_entities:
            suggestions.append({
                "type": "weak_entity",
                "entity": entity,
                "message": "Cette entité pourrait être une entité faible"
            })
            
        # 2. Détecter les relations redondantes
        redundant_relations = self._detect_redundant_relations()
        for relation in redundant_relations:
            suggestions.append({
                "type": "redundant_relation",
                "relation": relation,
                "message": "Cette relation pourrait être redondante"
            })
            
        # 3. Suggérer des héritages
        inheritance_candidates = self._detect_inheritance_candidates()
        for candidate in inheritance_candidates:
            suggestions.append({
                "type": "inheritance_candidate",
                "entities": candidate["entities"],
                "message": "Ces entités pourraient partager un héritage"
            })
            
        return suggestions
        
    def _suggest_mld_optimizations(self) -> List[Dict]:
        """Suggère des optimisations pour le MLD."""
        suggestions = []
        
        # 1. Optimisation des types de données
        type_optimizations = self._suggest_data_type_optimizations()
        suggestions.extend(type_optimizations)
        
        # 2. Suggestions d'index
        index_suggestions = self._suggest_indexes()
        suggestions.extend(index_suggestions)
        
        # 3. Suggestions de normalisation
        normalization_suggestions = self._suggest_normalization()
        suggestions.extend(normalization_suggestions)
        
        return suggestions
        
    def _is_valid_cardinality(self, cardinality: str) -> bool:
        """Vérifie si une cardinalité est valide."""
        valid_patterns = [
            "0..1", "1", "0..*", "1..*", "*"
        ]
        return cardinality in valid_patterns
        
    def _detect_weak_entities(self) -> List[str]:
        """Détecte les entités qui pourraient être des entités faibles."""
        weak_candidates = []
        
        for entity_name, entity in self.current_model["entities"].items():
            # Une entité est potentiellement faible si :
            # 1. Elle a peu d'attributs propres
            # 2. Elle a une relation forte avec une autre entité
            # 3. Sa clé primaire dépend d'une autre entité
            
            own_attributes = [attr for attr in entity["attributes"]
                            if not attr.get("foreign_key")]
                            
            if len(own_attributes) <= 2:
                # Vérifier les relations
                for relation in self.current_model["relations"]:
                    if relation["source"] == entity_name and \
                       relation["source_cardinality"] == "1" and \
                       relation["target_cardinality"] in ["1", "1..*"]:
                        weak_candidates.append(entity_name)
                        break
                        
        return weak_candidates
        
    def _detect_redundant_relations(self) -> List[Dict]:
        """Détecte les relations potentiellement redondantes."""
        redundant = []
        
        # Construire un graphe des relations
        relations_graph = {}
        for relation in self.current_model["relations"]:
            source = relation["source"]
            target = relation["target"]
            
            if source not in relations_graph:
                relations_graph[source] = {}
            if target not in relations_graph:
                relations_graph[target] = {}
                
            relations_graph[source][target] = relation
            relations_graph[target][source] = relation
            
        # Détecter les chemins alternatifs
        for source in relations_graph:
            for target in relations_graph[source]:
                if source < target:  # Éviter les doublons
                    paths = self._find_alternative_paths(relations_graph, source, target)
                    if len(paths) > 1:
                        redundant.append({
                            "source": source,
                            "target": target,
                            "paths": paths
                        })
                        
        return redundant
        
    def _detect_inheritance_candidates(self) -> List[Dict]:
        """Détecte les entités qui pourraient partager un héritage."""
        candidates = []
        
        entities = list(self.current_model["entities"].items())
        for i, (entity1_name, entity1) in enumerate(entities):
            for entity2_name, entity2 in entities[i+1:]:
                # Calculer la similarité des attributs
                similarity = self._calculate_entity_similarity(entity1, entity2)
                
                if similarity > 0.7:  # Seuil de similarité
                    candidates.append({
                        "entities": [entity1_name, entity2_name],
                        "similarity": similarity,
                        "common_attributes": self._get_common_attributes(entity1, entity2)
                    })
                    
        return candidates
        
    def _suggest_data_type_optimizations(self) -> List[Dict]:
        """Suggère des optimisations de types de données."""
        suggestions = []
        
        for table_name, table in self.current_model["tables"].items():
            for column in table["columns"]:
                # Optimiser les VARCHAR
                if column["type"].startswith("VARCHAR"):
                    if int(column["type"].split("(")[1].split(")")[0]) > 255:
                        suggestions.append({
                            "type": "data_type",
                            "table": table_name,
                            "column": column["name"],
                            "current": column["type"],
                            "suggested": "TEXT",
                            "reason": "Utiliser TEXT pour les longues chaînes"
                        })
                        
                # Optimiser les numériques
                elif column["type"] == "INTEGER":
                    if "id" in column["name"].lower():
                        suggestions.append({
                            "type": "data_type",
                            "table": table_name,
                            "column": column["name"],
                            "current": "INTEGER",
                            "suggested": "BIGINT",
                            "reason": "Utiliser BIGINT pour les identifiants"
                        })
                        
        return suggestions
        
    def _suggest_indexes(self) -> List[Dict]:
        """Suggère des index pour améliorer les performances."""
        suggestions = []
        
        for table_name, table in self.current_model["tables"].items():
            # Index sur les clés étrangères
            for fk in self.current_model["foreign_keys"]:
                if fk["table"] == table_name:
                    suggestions.append({
                        "type": "index",
                        "table": table_name,
                        "columns": fk["columns"],
                        "reason": "Index sur clé étrangère"
                    })
                    
            # Index sur les colonnes fréquemment utilisées
            for column in table["columns"]:
                if any(pattern in column["name"].lower()
                      for pattern in ["name", "code", "date", "status"]):
                    suggestions.append({
                        "type": "index",
                        "table": table_name,
                        "columns": [column["name"]],
                        "reason": "Colonne fréquemment utilisée"
                    })
                    
        return suggestions
        
    def _suggest_normalization(self) -> List[Dict]:
        """Suggère des améliorations de normalisation."""
        suggestions = []
        
        for table_name, table in self.current_model["tables"].items():
            # Détecter les violations de la 1NF
            multivalued = self._detect_multivalued_attributes(table)
            if multivalued:
                suggestions.append({
                    "type": "normalization",
                    "level": "1NF",
                    "table": table_name,
                    "columns": multivalued,
                    "suggestion": "Créer une table séparée pour ces valeurs"
                })
                
            # Détecter les violations de la 2NF
            partial_deps = self._detect_partial_dependencies(table)
            if partial_deps:
                suggestions.append({
                    "type": "normalization",
                    "level": "2NF",
                    "table": table_name,
                    "dependencies": partial_deps,
                    "suggestion": "Déplacer ces attributs dans une nouvelle table"
                })
                
            # Détecter les violations de la 3NF
            transitive_deps = self._detect_transitive_dependencies(table)
            if transitive_deps:
                suggestions.append({
                    "type": "normalization",
                    "level": "3NF",
                    "table": table_name,
                    "dependencies": transitive_deps,
                    "suggestion": "Créer une nouvelle table pour ces dépendances"
                })
                
        return suggestions
        
    def _calculate_entity_similarity(self, entity1: Dict, entity2: Dict) -> float:
        """Calcule la similarité entre deux entités."""
        attrs1 = {attr["name"]: attr["type"] for attr in entity1["attributes"]}
        attrs2 = {attr["name"]: attr["type"] for attr in entity2["attributes"]}
        
        common_attrs = set(attrs1.keys()) & set(attrs2.keys())
        type_matches = sum(1 for attr in common_attrs if attrs1[attr] == attrs2[attr])
        
        total_attrs = len(set(attrs1.keys()) | set(attrs2.keys()))
        
        return (len(common_attrs) + type_matches) / (2 * total_attrs)
        
    def _get_common_attributes(self, entity1: Dict, entity2: Dict) -> List[str]:
        """Retourne les attributs communs entre deux entités."""
        attrs1 = {attr["name"]: attr["type"] for attr in entity1["attributes"]}
        attrs2 = {attr["name"]: attr["type"] for attr in entity2["attributes"]}
        
        return [attr for attr in attrs1 if attr in attrs2 and attrs1[attr] == attrs2[attr]]
        
    def _find_alternative_paths(self, graph: Dict, start: str, end: str,
                              path: List[str] = None) -> List[List[str]]:
        """Trouve tous les chemins alternatifs entre deux entités."""
        if path is None:
            path = []
            
        path = path + [start]
        if start == end:
            return [path]
            
        paths = []
        for next_node in graph[start]:
            if next_node not in path:
                new_paths = self._find_alternative_paths(graph, next_node, end, path)
                paths.extend(new_paths)
                
        return paths
        
    def _detect_multivalued_attributes(self, table: Dict) -> List[str]:
        """Détecte les attributs potentiellement multivalués."""
        multivalued = []
        
        for column in table["columns"]:
            # Détecter les patterns courants de valeurs multiples
            if any(pattern in column["name"].lower()
                  for pattern in ["list", "array", "tags", "categories"]):
                multivalued.append(column["name"])
                
        return multivalued
        
    def _detect_partial_dependencies(self, table: Dict) -> List[Dict]:
        """Détecte les dépendances partielles."""
        dependencies = []
        
        if len(table["primary_key"]) > 1:  # Clé primaire composite
            non_key_attrs = [col["name"] for col in table["columns"]
                           if col["name"] not in table["primary_key"]]
            
            for attr in non_key_attrs:
                # Vérifier si l'attribut dépend d'une partie de la clé
                for key_part in table["primary_key"]:
                    if self._are_attributes_related(key_part, attr):
                        dependencies.append({
                            "attribute": attr,
                            "depends_on": key_part
                        })
                        
        return dependencies
        
    def _detect_transitive_dependencies(self, table: Dict) -> List[Dict]:
        """Détecte les dépendances transitives."""
        dependencies = []
        
        non_key_attrs = [col["name"] for col in table["columns"]
                        if col["name"] not in table["primary_key"]]
        
        for attr1 in non_key_attrs:
            for attr2 in non_key_attrs:
                if attr1 != attr2 and self._are_attributes_related(attr1, attr2):
                    dependencies.append({
                        "from": attr1,
                        "through": attr2
                    })
                    
        return dependencies
        
    def _are_attributes_related(self, attr1: str, attr2: str) -> bool:
        """Détermine si deux attributs sont probablement liés."""
        # Vérifier les préfixes/suffixes communs
        prefixes = ["id_", "code_", "num_"]
        if any(attr1.startswith(prefix) and attr2.startswith(prefix)
               for prefix in prefixes):
            return True
            
        # Vérifier les patterns courants
        patterns = {
            "date": ["date", "created", "modified", "updated"],
            "status": ["status", "state", "phase"],
            "amount": ["amount", "total", "price", "cost"]
        }
        
        for category, words in patterns.items():
            if any(word in attr1.lower() for word in words) and \
               any(word in attr2.lower() for word in words):
                return True
                
        return False

class ModelManagerDialog(QDialog):
    """Dialogue pour la gestion des modèles"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.model_manager = ModelManager()
        self.setup_ui()
        self.setup_connections()
        self.current_domain = None
        self.setup_themes()
        
    def setup_ui(self):
        """Configure l'interface utilisateur améliorée"""
        self.setWindowTitle("BarrelMCD - Modélisation de Données")
        self.setMinimumWidth(1400)
        self.setMinimumHeight(900)
        
        # Layout principal avec splitter
        main_layout = QHBoxLayout(self)
        splitter = QSplitter(Qt.Horizontal)
        
        # Panneau de gauche
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # Groupe de configuration
        config_group = QGroupBox("Configuration")
        config_layout = QVBoxLayout()
        
        # Sélection du domaine métier
        domain_layout = QHBoxLayout()
        domain_label = QLabel("Domaine métier :")
        self.domain_combo = QComboBox()
        self.domain_combo.addItems(["Commerce", "Medical", "Education", "Autre"])
        domain_layout.addWidget(domain_label)
        domain_layout.addWidget(self.domain_combo)
        config_layout.addLayout(domain_layout)
        
        # Type de modèle et type d'entrée
        model_input_layout = QGridLayout()
        model_input_layout.addWidget(QLabel("Type de modèle :"), 0, 0)
        self.model_type_combo = QComboBox()
        self.model_type_combo.addItems(["MCD", "UML", "MLD"])
        model_input_layout.addWidget(self.model_type_combo, 0, 1)
        
        model_input_layout.addWidget(QLabel("Type d'entrée :"), 1, 0)
        self.input_type_combo = QComboBox()
        self.input_type_combo.addItems(["JSON", "CSV", "Excel", "Texte"])
        model_input_layout.addWidget(self.input_type_combo, 1, 1)
        config_layout.addLayout(model_input_layout)
        
        config_group.setLayout(config_layout)
        left_layout.addWidget(config_group)
        
        # Zone de saisie avec aide contextuelle
        input_group = QGroupBox("Données d'entrée")
        input_layout = QVBoxLayout()
        
        # Barre d'outils pour la zone de texte
        toolbar = QToolBar()
        toolbar.addAction(QIcon("icons/import.png"), "Importer", self._import_file)
        toolbar.addAction(QIcon("icons/validate.png"), "Valider", self._validate_input)
        toolbar.addAction(QIcon("icons/help.png"), "Aide", self._show_help)
        input_layout.addWidget(toolbar)
        
        self.data_edit = QTextEdit()
        self.data_edit.setPlaceholderText("Entrez vos données ici...")
        input_layout.addWidget(self.data_edit)
        
        # Aide contextuelle
        self.help_label = QLabel()
        self.help_label.setWordWrap(True)
        self.help_label.setStyleSheet("color: #666; font-style: italic;")
        input_layout.addWidget(self.help_label)
        
        input_group.setLayout(input_layout)
        left_layout.addWidget(input_group)
        
        # Options avancées
        advanced_group = QGroupBox("Options avancées")
        advanced_layout = QVBoxLayout()
        
        # Options d'importation
        import_options = QWidget()
        import_layout = QFormLayout(import_options)
        self.csv_separator = QLineEdit(",")
        self.excel_sheet = QLineEdit("Sheet1")
        self.encoding = QComboBox()
        self.encoding.addItems(["utf-8", "latin-1", "cp1252", "ascii"])
        import_layout.addRow("Séparateur CSV :", self.csv_separator)
        import_layout.addRow("Feuille Excel :", self.excel_sheet)
        import_layout.addRow("Encodage :", self.encoding)
        advanced_layout.addWidget(import_options)
        
        # Options de génération
        generation_options = QWidget()
        generation_layout = QFormLayout(generation_options)
        self.auto_detect = QCheckBox("Détection automatique des relations")
        self.optimize_model = QCheckBox("Optimisation automatique")
        self.validate_constraints = QCheckBox("Validation des contraintes")
        generation_layout.addRow(self.auto_detect)
        generation_layout.addRow(self.optimize_model)
        generation_layout.addRow(self.validate_constraints)
        advanced_layout.addWidget(generation_options)
        
        advanced_group.setLayout(advanced_layout)
        left_layout.addWidget(advanced_group)
        
        # Boutons d'action
        actions_layout = QHBoxLayout()
        self.generate_btn = QPushButton("Générer MCD")
        self.export_btn = QPushButton("Exporter")
        self.clear_btn = QPushButton("Effacer")
        actions_layout.addWidget(self.generate_btn)
        actions_layout.addWidget(self.export_btn)
        actions_layout.addWidget(self.clear_btn)
        left_layout.addLayout(actions_layout)
        
        # Panneau de droite avec onglets
        right_panel = QTabWidget()
        
        # Onglet Visualisation
        self.mcd_view = MCDView()
        right_panel.addTab(self.mcd_view, "Visualisation")
        
        # Onglet SQL
        self.sql_tab = QWidget()
        sql_layout = QVBoxLayout(self.sql_tab)
        self.sql_edit = QTextEdit()
        self.sql_edit.setReadOnly(True)
        sql_toolbar = QToolBar()
        sql_toolbar.addAction("Copier", self._copy_sql)
        sql_toolbar.addAction("Enregistrer", self._save_sql)
        sql_layout.addWidget(sql_toolbar)
        sql_layout.addWidget(self.sql_edit)
        right_panel.addTab(self.sql_tab, "SQL")
        
        # Onglet Messages
        self.messages_tab = QWidget()
        messages_layout = QVBoxLayout(self.messages_tab)
        self.messages_edit = QTextEdit()
        self.messages_edit.setReadOnly(True)
        messages_layout.addWidget(self.messages_edit)
        right_panel.addTab(self.messages_tab, "Messages")
        
        # Ajout des panneaux au splitter
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        
        main_layout.addWidget(splitter)
        
    def setup_connections(self):
        """Configure les connexions des signaux"""
        self.domain_combo.currentTextChanged.connect(self._update_domain)
        self.input_type_combo.currentTextChanged.connect(self._update_input_help)
        self.generate_btn.clicked.connect(self._generate_model)
        self.export_btn.clicked.connect(self._export_model)
        self.clear_btn.clicked.connect(self._clear_all)
        
    def setup_themes(self):
        """Configure les thèmes et styles"""
        self.setStyleSheet("""
            QDialog {
                background-color: #f5f5f5;
            }
            QGroupBox {
                border: 1px solid #ddd;
                border-radius: 5px;
                margin-top: 1ex;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px;
            }
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 5px 15px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #0D47A1;
            }
            QTextEdit {
                border: 1px solid #ddd;
                border-radius: 3px;
            }
            QComboBox {
                border: 1px solid #ddd;
                border-radius: 3px;
                padding: 3px;
            }
            QLabel {
                color: #333;
            }
        """)
        
    def _update_domain(self, domain: str):
        """Met à jour le domaine métier et les suggestions"""
        self.current_domain = domain.lower()
        self._update_input_help()
        
    def _update_input_help(self):
        """Met à jour l'aide contextuelle selon le type d'entrée et le domaine"""
        input_type = self.input_type_combo.currentText()
        domain = self.current_domain
        
        help_text = "Exemple de format attendu :\n\n"
        
        if domain == "commerce":
            if input_type == "JSON":
                help_text += """
{
    "entities": {
        "Client": {
            "attributes": [
                {"name": "id", "type": "INTEGER", "primary_key": true},
                {"name": "nom", "type": "VARCHAR"},
                {"name": "email", "type": "VARCHAR"}
            ]
        },
        "Commande": {
            "attributes": [
                {"name": "id", "type": "INTEGER", "primary_key": true},
                {"name": "date", "type": "DATE"},
                {"name": "montant", "type": "DECIMAL"}
            ]
        }
    }
}"""
            elif input_type == "Texte":
                help_text += """
Un Client peut passer plusieurs Commandes.
Chaque Commande contient plusieurs Produits avec une quantité.
Une Facture est générée pour chaque Commande.
"""
        elif domain == "medical":
            if input_type == "Texte":
                help_text += """
Un Patient consulte plusieurs Médecins.
Chaque Consultation donne lieu à une ou plusieurs Prescriptions.
Un Médicament peut être prescrit à plusieurs Patients.
"""
        
        self.help_label.setText(help_text)
        
    def _generate_model(self):
        """Génère le modèle à partir des données"""
        try:
            # Récupérer les données
            data = self.data_edit.toPlainText()
            input_type = self.input_type_combo.currentText()
            
            # Générer le modèle
            if input_type == "JSON":
                model = self.model_manager.analyze_data(json.loads(data))
            elif input_type in ["CSV", "Excel"]:
                df = pd.read_csv(StringIO(data)) if input_type == "CSV" else \
                     pd.read_excel(StringIO(data))
                model = self.model_manager.analyze_data({"data": df})
            else:
                model = self.model_manager.analyze_data({"text": data})
                
            # Mettre à jour la visualisation
            self.mcd_view.display_model(model)
            
            # Générer le SQL
            sql = self.model_manager.generate_sql()
            self.sql_edit.setText(sql)
            
            # Message de succès
            self.messages_edit.append("Modèle généré avec succès !")
            
        except Exception as e:
            self.messages_edit.append(f"Erreur : {str(e)}")
            
    def _export_model(self):
        """Exporte le modèle dans différents formats"""
        from PyQt5.QtWidgets import QFileDialog
        
        # Demander le type d'export
        export_type, ok = QInputDialog.getItem(
            self,
            "Export",
            "Choisir le format d'export :",
            ["SQL", "PNG", "PDF", "JSON"],
            0,
            False
        )
        
        if ok and export_type:
            # Demander le chemin de sauvegarde
            file_filter = {
                "SQL": "Fichiers SQL (*.sql)",
                "PNG": "Images PNG (*.png)",
                "PDF": "Documents PDF (*.pdf)",
                "JSON": "Fichiers JSON (*.json)"
            }[export_type]
            
            filepath, _ = QFileDialog.getSaveFileName(
                self,
                "Enregistrer sous",
                "",
                file_filter
            )
            
            if filepath:
                try:
                    if export_type == "SQL":
                        with open(filepath, 'w') as f:
                            f.write(self.sql_edit.toPlainText())
                    elif export_type == "PNG":
                        self.mcd_view.save_as_image(filepath)
                    elif export_type == "PDF":
                        self.mcd_view.save_as_pdf(filepath)
                    elif export_type == "JSON":
                        with open(filepath, 'w') as f:
                            json.dump(self.model_manager.current_model, f, indent=2)
                            
                    self.messages_edit.append(f"Export réussi vers {filepath}")
                    
                except Exception as e:
                    self.messages_edit.append(f"Erreur lors de l'export : {str(e)}")
                    
    def _clear_all(self):
        """Efface toutes les données"""
        reply = QMessageBox.question(
            self,
            "Confirmation",
            "Voulez-vous vraiment effacer toutes les données ?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.data_edit.clear()
            self.sql_edit.clear()
            self.messages_edit.clear()
            self.mcd_view.clear()
            self.model_manager.current_model = None
            
    def _validate_input(self):
        """Valide les données d'entrée"""
        try:
            data = self.data_edit.toPlainText()
            input_type = self.input_type_combo.currentText()
            
            if input_type == "JSON":
                json.loads(data)  # Teste si le JSON est valide
                self.messages_edit.append("Format JSON valide")
            elif input_type == "CSV":
                pd.read_csv(StringIO(data))
                self.messages_edit.append("Format CSV valide")
            elif input_type == "Excel":
                pd.read_excel(StringIO(data))
                self.messages_edit.append("Format Excel valide")
            else:
                # Validation basique du texte
                if len(data.split()) < 3:
                    raise ValueError("Le texte est trop court")
                self.messages_edit.append("Format texte valide")
                
        except Exception as e:
            self.messages_edit.append(f"Erreur de validation : {str(e)}")
            
    def _show_help(self):
        """Affiche l'aide contextuelle"""
        QMessageBox.information(
            self,
            "Aide",
            """
            <h3>Utilisation de BarrelMCD</h3>
            <p>1. Sélectionnez votre domaine métier</p>
            <p>2. Choisissez le type d'entrée (JSON, CSV, Excel, Texte)</p>
            <p>3. Entrez ou importez vos données</p>
            <p>4. Cliquez sur "Générer MCD" pour créer le modèle</p>
            <p>5. Utilisez les onglets pour voir le MCD, le SQL ou les messages</p>
            <p>6. Exportez votre modèle dans différents formats</p>
            
            <h4>Formats supportés</h4>
            <ul>
                <li>JSON : Structure de données complète</li>
                <li>CSV : Données tabulaires</li>
                <li>Excel : Feuilles de calcul</li>
                <li>Texte : Description en langage naturel</li>
            </ul>
            """,
            QMessageBox.Ok
        )
        
    def _copy_sql(self):
        """Copie le SQL dans le presse-papier"""
        QApplication.clipboard().setText(self.sql_edit.toPlainText())
        self.messages_edit.append("SQL copié dans le presse-papier")
        
    def _save_sql(self):
        """Enregistre le SQL dans un fichier"""
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Enregistrer le SQL",
            "",
            "Fichiers SQL (*.sql)"
        )
        
        if filepath:
            try:
                with open(filepath, 'w') as f:
                    f.write(self.sql_edit.toPlainText())
                self.messages_edit.append(f"SQL enregistré dans {filepath}")
            except Exception as e:
                self.messages_edit.append(f"Erreur lors de l'enregistrement : {str(e)}") 