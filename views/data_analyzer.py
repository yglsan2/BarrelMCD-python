from typing import Dict, List, Set, Tuple, Any, Optional, Union
import pandas as pd
import numpy as np
from collections import defaultdict
import re
from enum import Enum
import json
import xml.etree.ElementTree as ET

class EntityTemplate:
    """Modèles d'entités courantes avec leurs attributs typiques"""
    
    TEMPLATES = {
        "personne": {
            "attributs_obligatoires": {
                "id": "integer",
                "nom": "varchar",
                "prenom": "varchar"
            },
            "attributs_optionnels": {
                "date_naissance": "date",
                "adresse": "varchar",
                "email": "varchar",
                "telephone": "varchar",
                "sexe": "char"
            },
            "mots_cles": ["personne", "individu", "utilisateur", "user", "person"],
            "relations_courantes": ["adresse", "contact", "document"]
        },
        "client": {
            "attributs_obligatoires": {
                "id": "integer",
                "numero_client": "varchar"
            },
            "attributs_optionnels": {
                "societe": "varchar",
                "siret": "varchar",
                "tva": "varchar",
                "type_client": "varchar"
            },
            "herite_de": "personne",
            "mots_cles": ["client", "acheteur", "customer", "buyer"],
            "relations_courantes": ["commande", "facture", "panier"]
        },
        "employe": {
            "attributs_obligatoires": {
                "id": "integer",
                "matricule": "varchar",
                "date_embauche": "date"
            },
            "attributs_optionnels": {
                "poste": "varchar",
                "salaire": "decimal",
                "departement": "varchar"
            },
            "herite_de": "personne",
            "mots_cles": ["employe", "employee", "staff", "personnel", "salarie"],
            "relations_courantes": ["departement", "projet", "manager"]
        },
        "produit": {
            "attributs_obligatoires": {
                "id": "integer",
                "reference": "varchar",
                "nom": "varchar",
                "prix": "decimal"
            },
            "attributs_optionnels": {
                "description": "text",
                "stock": "integer",
                "categorie": "varchar",
                "marque": "varchar",
                "poids": "decimal"
            },
            "mots_cles": ["produit", "article", "item", "product", "marchandise"],
            "relations_courantes": ["categorie", "fournisseur", "commande"]
        },
        "commande": {
            "attributs_obligatoires": {
                "id": "integer",
                "numero": "varchar",
                "date": "datetime",
                "montant_total": "decimal"
            },
            "attributs_optionnels": {
                "statut": "varchar",
                "mode_paiement": "varchar",
                "remise": "decimal",
                "commentaire": "text"
            },
            "mots_cles": ["commande", "order", "achat", "purchase"],
            "relations_courantes": ["client", "produit", "facture"]
        }
    }
    
    @classmethod
    def get_template(cls, name: str) -> Dict:
        """Retourne un template d'entité."""
        return cls.TEMPLATES.get(name.lower())
        
    @classmethod
    def find_matching_template(cls, columns: List[str], data_sample: pd.DataFrame = None) -> Tuple[str, float]:
        """Trouve le template le plus proche pour un ensemble de colonnes."""
        best_match = None
        best_score = 0
        
        for template_name, template in cls.TEMPLATES.items():
            score = 0
            total_attributes = len(template["attributs_obligatoires"]) + len(template["attributs_optionnels"])
            
            # Vérifier les attributs obligatoires
            for attr in template["attributs_obligatoires"]:
                if any(col.lower().replace("_", "").replace("-", "") == attr.lower() for col in columns):
                    score += 2
                    
            # Vérifier les attributs optionnels
            for attr in template["attributs_optionnels"]:
                if any(col.lower().replace("_", "").replace("-", "") == attr.lower() for col in columns):
                    score += 1
                    
            # Vérifier les mots-clés dans les noms de colonnes
            for keyword in template["mots_cles"]:
                if any(keyword.lower() in col.lower() for col in columns):
                    score += 3
                    
            # Analyse des données si disponibles
            if data_sample is not None:
                score += cls._analyze_data_patterns(data_sample, template)
                
            # Calculer le score final
            score = score / (total_attributes * 2 + len(template["mots_cles"]) * 3)
            
            if score > best_score:
                best_score = score
                best_match = template_name
                
        return best_match, best_score
        
    @classmethod
    def _analyze_data_patterns(cls, data: pd.DataFrame, template: Dict) -> float:
        """Analyse les patterns dans les données pour matcher avec le template."""
        score = 0
        
        # Vérifier les formats de données typiques
        for col in data.columns:
            col_lower = col.lower()
            
            # Vérifier les patterns d'email
            if "email" in template["attributs_optionnels"] and \
               data[col].dtype == "object" and \
               data[col].str.contains("@").any():
                score += 2
                
            # Vérifier les patterns de dates
            if any(date_field in template["attributs_obligatoires"] or \
                  date_field in template["attributs_optionnels"] 
                  for date_field in ["date", "date_naissance", "date_embauche"]):
                try:
                    pd.to_datetime(data[col])
                    score += 2
                except:
                    pass
                    
            # Vérifier les patterns numériques
            if "montant" in col_lower or "prix" in col_lower or "salaire" in col_lower:
                if data[col].dtype in ["float64", "int64"]:
                    score += 2
                    
        return score

class EntityTemplates:
    def __init__(self):
        self.templates = {
            "personne": {
                "attributes": ["id", "nom", "prenom", "email", "date_naissance", "adresse", "telephone"],
                "weight": 1.0
            },
            "produit": {
                "attributes": ["id", "nom", "description", "prix", "stock", "categorie", "reference"],
                "weight": 1.0
            },
            "commande": {
                "attributes": ["id", "date", "montant", "statut", "client_id", "numero"],
                "weight": 1.0
            },
            "facture": {
                "attributes": ["id", "numero", "date", "montant", "client_id", "commande_id"],
                "weight": 1.0
            }
        }

    def find_matching_template(self, words: List[str]) -> Tuple[str, float]:
        """Trouve le meilleur template correspondant aux mots donnés."""
        best_score = 0.0
        best_template = None

        normalized_words = [word.lower() for word in words]

        for template_name, template in self.templates.items():
            score = self._calculate_similarity(normalized_words, template["attributes"])
            if score > best_score:
                best_score = score
                best_template = template_name

        return best_template or "generic", best_score

    def _calculate_similarity(self, words: List[str], template_attrs: List[str]) -> float:
        """Calcule la similarité entre les mots et les attributs du template."""
        matches = sum(1 for word in words if any(attr in word or word in attr for attr in template_attrs))
        total = max(len(words), len(template_attrs))
        return matches / total if total > 0 else 0.0

class DataAnalyzer:
    def __init__(self):
        """Initialise l'analyseur de données."""
        self.detected_entities = {}
        self.detected_relations = []
        self.templates = EntityTemplate()

    def analyze_data(self, data: Union[pd.DataFrame, Dict], format_type: str = "csv") -> Dict:
        """Analyse des données pour générer un modèle conceptuel.
        
        Args:
            data: Données à analyser (DataFrame ou dictionnaire)
            format_type: Type de format des données ("csv" ou "json")
            
        Returns:
            Dict: Modèle conceptuel détecté
        """
        # Réinitialiser l'état
        self.detected_entities = {}
        self.detected_relations = []
        
        # Convertir en DataFrame si nécessaire
        if format_type == "json":
            data_dict = data
            for entity_name, value in data_dict.items():
                # Normaliser le nom de l'entité (singulier)
                entity_name = self._normalize_entity_name(entity_name)
                if isinstance(value, list) and len(value) > 0:
                    self._analyze_entity(entity_name, value[0])
        else:
            if isinstance(data, pd.DataFrame):
                self._analyze_dataframe(data)
            else:
                raise ValueError("Format de données non supporté")
        
        # Détecter les relations
        self._detect_relations(data)
        
        # Construire le modèle final
        return {
            "entities": self.detected_entities,
            "relations": self.detected_relations,
            "hierarchies": [rel for rel in self.detected_relations if rel["type"] == "INHERITANCE"]
        }

    def _analyze_entity(self, name: str, data: Dict) -> None:
        """Analyse une entité et ses attributs.
        
        Args:
            name: Nom de l'entité
            data: Données de l'entité
        """
        if name not in self.detected_entities:
            # Créer l'entité
            entity = {
                "name": name,
                "attributes": [],
                "primary_key": []
            }
            
            # Détecter le template correspondant
            template = self.templates.find_matching_template(name, list(data.keys()))
            if template:
                entity.update(template)
            
            # Analyser les attributs
            for attr_name, attr_value in data.items():
                attribute = self._analyze_attribute(attr_name, attr_value)
                entity["attributes"].append(attribute)
                if "PRIMARY KEY" in attribute["constraints"]:
                    entity["primary_key"].append(attribute["name"])
            
            self.detected_entities[name] = entity

    def _analyze_attribute(self, name_or_words: Union[str, List[str]], value: Any = None) -> Dict:
        """Analyse un attribut pour déterminer son type et ses contraintes.
        
        Args:
            name_or_words: Nom de l'attribut ou liste de mots-clés
            value: Valeur de l'attribut (optionnel)
            
        Returns:
            Dict: Informations sur l'attribut avec:
                - name: Nom normalisé de l'attribut
                - type: Type de données (DECIMAL, INTEGER, VARCHAR, etc.)
                - constraints: Liste des contraintes (PRIMARY KEY, NOT NULL, etc.)
                - size: Taille spécifique pour les types VARCHAR/CHAR
                - enum_values: Valeurs possibles pour les types énumérés
        """
        # Normaliser l'entrée
        if isinstance(name_or_words, list):
            name = name_or_words[0]
            words = name_or_words
        else:
            name = name_or_words
            words = [name]
            
        # Normaliser le nom
        name = self._normalize_attribute_name(name)
        
        # Initialiser les informations
        attr_info = {
            "name": name,
            "type": "VARCHAR(255)",  # Type par défaut avec taille
            "constraints": [],
            "size": None,
            "enum_values": None
        }
        
        # Détecter le type à partir des mots-clés
        if any(word in name for word in ["prix", "montant", "total", "cout", "price", "amount"]):
            attr_info["type"] = "DECIMAL(10,2)"
            attr_info["constraints"].append("CHECK (value >= 0)")
        elif any(word in name for word in ["id", "code", "reference"]):
            attr_info["type"] = "INTEGER"
            attr_info["constraints"].append("NOT NULL")
            if name == "id":
                attr_info["constraints"].append("PRIMARY KEY")
        elif any(word in name for word in ["date", "created", "updated", "deleted"]):
            attr_info["type"] = "DATETIME"
        elif any(word in name for word in ["email", "mail"]):
            attr_info["type"] = "VARCHAR(100)"
            attr_info["constraints"].append("UNIQUE")
        elif any(word in name for word in ["description", "commentaire", "contenu", "content"]):
            attr_info["type"] = "TEXT"
        elif any(word in name for word in ["actif", "valide", "active", "valid", "enabled"]):
            attr_info["type"] = "BOOLEAN"
            attr_info["constraints"].extend([
                "NOT NULL",
                "DEFAULT 'OUI'",
                "CHECK (value IN ('OUI', 'NON'))"
            ])
        elif any(word in name for word in ["status", "etat", "state"]):
            attr_info["type"] = "ENUM('ACTIF', 'INACTIF', 'EN_ATTENTE')"
            attr_info["enum_values"] = ["ACTIF", "INACTIF", "EN_ATTENTE"]
        
        # Affiner le type à partir de la valeur si fournie
        if value is not None:
            if isinstance(value, bool):
                attr_info["type"] = "BOOLEAN"
                attr_info["constraints"].extend([
                    "NOT NULL",
                    "DEFAULT 'OUI'",
                    "CHECK (value IN ('OUI', 'NON'))"
                ])
            elif isinstance(value, int):
                if attr_info["type"] != "DECIMAL(10,2)":  # Ne pas écraser DECIMAL
                    attr_info["type"] = "INTEGER"
            elif isinstance(value, float):
                attr_info["type"] = "DECIMAL(10,2)"
            elif isinstance(value, str):
                try:
                    pd.to_datetime(value)
                    attr_info["type"] = "DATETIME"
                except:
                    # Ajuster la taille du VARCHAR en fonction de la longueur maximale
                    max_length = len(value)
                    if max_length > 255:
                        attr_info["type"] = "TEXT"
                    else:
                        attr_info["type"] = f"VARCHAR({max(255, max_length)})"
                        attr_info["size"] = max(255, max_length)
        
        # Ajouter des contraintes supplémentaires
        if name.endswith("_id"):
            referenced_table = self._extract_referenced_table(name)
            if referenced_table:
                attr_info["constraints"].append(f"FOREIGN KEY REFERENCES {referenced_table}(id)")
        
        return attr_info

    def _normalize_entity_name(self, name: str) -> str:
        """Normalise le nom d'une entité.
        
        Args:
            name: Nom à normaliser
            
        Returns:
            str: Nom normalisé
        """
        # Mettre au singulier
        if name.endswith('s'):
            name = name[:-1]
        
        # Convertir en minuscules
        name = name.lower()
        
        # Supprimer les caractères spéciaux
        name = re.sub(r'[^a-z0-9_]', '', name)
        
        return name

    def _detect_relations(self, data: Union[pd.DataFrame, Dict]) -> None:
        """Détecte les relations entre les entités.
        
        Args:
            data: Données à analyser
        """
        if isinstance(data, dict):
            # Analyser les relations dans les données JSON
            for entity_name, values in data.items():
                entity_name = self._normalize_entity_name(entity_name)
                if isinstance(values, list) and len(values) > 0:
                    for value in values:
                        # Détecter les clés étrangères
                        for attr_name in value.keys():
                            if attr_name.endswith('_id'):
                                target_entity = attr_name[:-3]
                                if target_entity in self.detected_entities:
                                    self.detected_relations.append({
                                        "name": f"has_{target_entity}",
                                        "source": entity_name,
                                        "target": target_entity,
                                        "type": "ONE_TO_MANY",
                                        "source_cardinality": "1",
                                        "target_cardinality": "*"
                                    })
        else:
            # Analyser les relations dans le DataFrame
            for col in data.columns:
                if col.endswith('_id'):
                    target_entity = col[:-3]
                    source_entity = self._detect_source_entity(data, col)
                    if source_entity and target_entity in self.detected_entities:
                        self.detected_relations.append({
                            "name": f"has_{target_entity}",
                            "source": source_entity,
                            "target": target_entity,
                            "type": "ONE_TO_MANY",
                            "source_cardinality": "1",
                            "target_cardinality": "*"
                        })

    def _normalize_attribute_name(self, name: str) -> str:
        """Normalise le nom d'un attribut pour la détection de patterns."""
        # Supprimer les préfixes/suffixes courants
        prefixes = ["id_", "code_", "ref_"]
        suffixes = ["_id", "_code", "_ref"]
        
        normalized = name.lower()
        for prefix in prefixes:
            if normalized.startswith(prefix):
                normalized = normalized[len(prefix):]
        for suffix in suffixes:
            if normalized.endswith(suffix):
                normalized = normalized[:-len(suffix)]
                
        return normalized
        
    def _is_potential_foreign_key(self, column_name: str) -> bool:
        """Détermine si une colonne peut être une clé étrangère."""
        patterns = [
            r".*_id$",
            r"id_.*",
            r".*_code$",
            r"code_.*",
            r".*_ref$",
            r"ref_.*"
        ]
        return any(re.match(pattern, column_name.lower()) for pattern in patterns)

    def _extract_referenced_table(self, column_name: str) -> str:
        """Extrait le nom de la table référencée depuis le nom de la colonne."""
        patterns = [
            (r"(.*)_id$", 1),
            (r"id_(.*)", 1),
            (r"(.*)_code$", 1),
            (r"code_(.*)", 1),
            (r"(.*)_ref$", 1),
            (r"ref_(.*)", 1)
        ]
        
        for pattern, group in patterns:
            match = re.match(pattern, column_name.lower())
            if match:
                return match.group(group)
        return None
        
    def _analyze_text_for_context(self, text: str, contexts: Dict):
        """Analyse le texte pour détecter le contexte métier."""
        text_lower = text.lower()
        
        # Analyser les mots-clés spécifiques à chaque domaine
        for context, rules in self.business_rules.items():
            # Compter les occurrences des entités obligatoires
            for entity in rules["entites_obligatoires"]:
                contexts[context] += text_lower.count(entity)
                
            # Vérifier les relations typiques
            for source, target, _ in rules["relations_typiques"]:
                if source in text_lower and target in text_lower:
                    contexts[context] += 2
                    
    def _analyze_relationship(self, sentence: str, entities: List[str]):
        """Analyse une relation entre entités dans une phrase."""
        # Patterns de cardinalités
        cardinality_patterns = {
            "ONE_TO_ONE": [
                r"un seul", r"unique", r"exactement un",
                r"correspond à un", r"associé à un"
            ],
            "ONE_TO_MANY": [
                r"plusieurs", r"multiple", r"nombreux",
                r"contient des", r"possède des"
            ],
            "MANY_TO_ONE": [
                r"appartient à", r"fait partie de",
                r"est associé à", r"dépend de"
            ],
            "MANY_TO_MANY": [
                r"peuvent avoir plusieurs",
                r"sont associés à plusieurs",
                r"participent à"
            ]
        }
        
        # Détecter le type de relation
        relation_type = self._detect_relation_type(sentence, cardinality_patterns)
        
        # Détecter les cardinalités spécifiques
        source_cardinality = self._detect_specific_cardinality(sentence, entities[0])
        target_cardinality = self._detect_specific_cardinality(sentence, entities[1])
        
        # Créer la relation
        relation = {
            "source": entities[0],
            "target": entities[1],
            "type": relation_type,
            "source_cardinality": source_cardinality,
            "target_cardinality": target_cardinality,
            "name": self._extract_relation_name(sentence)
        }
        
        self.detected_relations.append(relation)
        
    def _detect_relation_type(self, sentence: str, patterns: Dict) -> str:
        """Détecte le type de relation basé sur les patterns."""
        # Scores pour chaque type
        scores = {rel_type: 0 for rel_type in patterns}
        
        # Vérifier les patterns explicites
        for rel_type, rel_patterns in patterns.items():
            for pattern in rel_patterns:
                if re.search(pattern, sentence):
                    scores[rel_type] += 2
                    
        # Vérifier les verbes de possession
        for verb in self.nlp_patterns["fr"]["verbes_possession"]:
            if verb in sentence:
                scores["ONE_TO_MANY"] += 1
                
        # Vérifier les verbes d'appartenance
        for verb in self.nlp_patterns["fr"]["verbes_appartenance"]:
            if verb in sentence:
                scores["MANY_TO_ONE"] += 1
                
        # Détecter les pluriels
        if re.search(r"(s|x)(\W|$)", sentence):
            scores["ONE_TO_MANY"] += 0.5
            scores["MANY_TO_MANY"] += 0.5
            
        # Retourner le type avec le score le plus élevé
        return max(scores.items(), key=lambda x: x[1])[0]
        
    def _detect_specific_cardinality(self, sentence: str, entity: str) -> str:
        """Détecte une cardinalité spécifique pour une entité."""
        # Patterns de cardinalités spécifiques
        specific_patterns = {
            r"(?:exactement|précisément|uniquement)\s+(\d+)": lambda x: x,
            r"au moins\s+(\d+)": lambda x: f"{x}..*",
            r"au plus\s+(\d+)": lambda x: f"0..{x}",
            r"entre\s+(\d+)\s+et\s+(\d+)": lambda x, y: f"{x}..{y}",
            r"optionnel": lambda: "0..1",
            r"obligatoire": lambda: "1",
            r"plusieurs": lambda: "1..*",
            r"multiple": lambda: "*..*"
        }
        
        # Chercher l'entité dans la phrase
        entity_pos = sentence.find(entity)
        if entity_pos == -1:
            return "1"  # Cardinalité par défaut
            
        # Analyser le contexte autour de l'entité
        context = sentence[max(0, entity_pos - 50):min(len(sentence), entity_pos + 50)]
        
        # Chercher des patterns spécifiques
        for pattern, formatter in specific_patterns.items():
            match = re.search(pattern, context)
            if match:
                return formatter(*match.groups()) if match.groups() else formatter()
                
        # Cardinalité par défaut basée sur le pluriel
        return "*..*" if re.search(r"(s|x)(\W|$)", entity) else "1"
        
    def _extract_relation_name(self, sentence: str) -> str:
        """Extrait un nom significatif pour la relation."""
        # Verbes d'action courants
        action_verbs = self.nlp_patterns["fr"]["verbes_action"]
        
        # Chercher un verbe d'action
        for verb in action_verbs:
            match = re.search(f"\\b{verb}\\b", sentence)
            if match:
                # Extraire le contexte autour du verbe
                start = max(0, match.start() - 20)
                end = min(len(sentence), match.end() + 20)
                context = sentence[start:end]
                
                # Nettoyer et formater
                name = verb.capitalize()
                
                # Ajouter des compléments si présents
                complements = re.findall(r'\b\w+\b', context[match.end() - start:])
                if complements:
                    name += "_" + "_".join(complements[:2])
                    
                return name
                
        return "relation"  # Nom par défaut

    def _extract_entity_name(self, column_name: str) -> str:
        """Extrait le nom de l'entité à partir du nom de la colonne.
        
        Args:
            column_name: Nom de la colonne
            
        Returns:
            str: Nom de l'entité
        """
        # Supprimer les suffixes courants
        suffixes = ["_id", "_ref", "_fk", "_key", "_code", "_no", "_num"]
        for suffix in suffixes:
            if column_name.endswith(suffix):
                return column_name[:-len(suffix)]
        
        # Supprimer les préfixes courants
        prefixes = ["id_", "ref_", "fk_", "key_", "code_", "no_", "num_"]
        for prefix in prefixes:
            if column_name.startswith(prefix):
                return column_name[len(prefix):]
        
        return column_name

    def _analyze_attribute(self, words: List[str]) -> Dict:
        """Analyse les mots pour déterminer les caractéristiques d'un attribut.
        
        Args:
            words: Liste des mots à analyser
            
        Returns:
            Dict: Informations sur l'attribut
        """
        # Normaliser les mots
        words = [w.lower() for w in words]
        
        # Déterminer le type
        type_mapping = {
            "integer": "INTEGER",
            "int": "INTEGER",
            "decimal": "DECIMAL",
            "float": "DECIMAL",
            "double": "DECIMAL",
            "boolean": "BOOLEAN",
            "bool": "BOOLEAN",
            "string": "VARCHAR",
            "str": "VARCHAR",
            "text": "TEXT",
            "date": "DATE",
            "datetime": "DATETIME",
            "timestamp": "DATETIME"
        }
        
        attr_type = "VARCHAR"  # Type par défaut
        for word in words:
            if word in type_mapping:
                attr_type = type_mapping[word]
                break
        
        # Déterminer les contraintes
        constraints = {
            "primary_key": False,
            "unique": False,
            "not_null": False
        }
        
        # Vérifier les contraintes
        if any(word in ["id", "identifiant", "code", "reference"] for word in words):
            constraints["primary_key"] = True
            constraints["not_null"] = True
            constraints["unique"] = True
        elif any(word in ["unique", "distinct"] for word in words):
            constraints["unique"] = True
        elif any(word in ["not_null", "required", "obligatoire"] for word in words):
            constraints["not_null"] = True
        
        return {
            "name": words[0],
            "type": attr_type,
            "constraints": constraints
        } 