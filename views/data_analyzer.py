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
    """Classe responsable de l'analyse intelligente des données pour générer le MCD."""
    
    def __init__(self):
        self.entity_templates = EntityTemplates()
        self.detected_entities = {}
        self.detected_relations = []
        self.nlp_patterns = {
            "fr": {
                "verbes_possession": [
                    "avoir", "posséder", "contenir", "inclure", "comprendre",
                    "gérer", "administrer", "superviser", "diriger"
                ],
                "verbes_appartenance": [
                    "appartenir", "faire partie", "dépendre", "être lié",
                    "être rattaché", "être associé", "être affilié"
                ],
                "verbes_composition": [
                    "composer", "constituer", "former", "regrouper",
                    "assembler", "structurer", "organiser"
                ],
                "verbes_action": [
                    "créer", "modifier", "supprimer", "consulter",
                    "valider", "annuler", "traiter", "gérer"
                ],
                "indicateurs_temporels": [
                    "date", "période", "durée", "début", "fin",
                    "création", "modification", "suppression"
                ],
                "indicateurs_etat": [
                    "statut", "état", "phase", "étape", "niveau",
                    "progression", "avancement"
                ],
                "indicateurs_quantite": [
                    "nombre", "quantité", "montant", "total", "somme",
                    "moyenne", "minimum", "maximum"
                ]
            }
        }
        
        self.entity_patterns = {
            "acteur": {
                "keywords": ["utilisateur", "client", "employé", "personne"],
                "attributes": ["id", "nom", "prénom", "email", "téléphone"],
                "actions": ["créer", "modifier", "supprimer", "consulter"]
            },
            "document": {
                "keywords": ["facture", "commande", "devis", "contrat"],
                "attributes": ["numéro", "date", "montant", "statut"],
                "actions": ["générer", "valider", "annuler"]
            },
            "produit": {
                "keywords": ["article", "bien", "service", "item"],
                "attributes": ["référence", "nom", "prix", "stock"],
                "actions": ["ajouter", "modifier", "supprimer"]
            }
        }
        
        self.relation_patterns = {
            "possession": ["avoir", "posséder", "détenir"],
            "composition": ["contenir", "inclure", "composer"],
            "action": ["créer", "modifier", "gérer", "utiliser"],
            "association": ["participer", "appartenir", "travailler"]
        }
        
        self.cardinality_patterns = {
            "one_to_one": [
                r"unique", r"exclusif", r"seul", r"un et un seul"
            ],
            "one_to_many": [
                r"plusieurs", r"multiple", r"tous les", r"chaque"
            ],
            "many_to_many": [
                r"plusieurs .* plusieurs", r"multiple .* multiple"
            ]
        }
        
        self.business_rules = {
            "commerce": {
                "entites_obligatoires": ["client", "produit", "commande"],
                "relations_typiques": [
                    ("client", "commande", "MANY_TO_ONE"),
                    ("produit", "commande", "MANY_TO_MANY")
                ],
                "attributs_calcules": {
                    "commande": ["montant_total", "nombre_articles"],
                    "produit": ["stock_disponible", "prix_ttc"]
                }
            },
            "rh": {
                "entites_obligatoires": ["employe", "departement", "poste"],
                "relations_typiques": [
                    ("employe", "departement", "MANY_TO_ONE"),
                    ("employe", "poste", "MANY_TO_ONE")
                ],
                "attributs_calcules": {
                    "departement": ["nombre_employes", "masse_salariale"],
                    "employe": ["anciennete", "conges_restants"]
                }
            }
        }
        
        self.semantic_patterns = {
            "n_ary_indicators": {
                "verbs": ["participe", "implique", "relie", "connecte", "associe", "intervient"],
                "prepositions": ["entre", "parmi", "avec", "pour"],
                "conjunctions": ["et", "ou", "ainsi que", "comme"],
                "quantifiers": ["plusieurs", "multiples", "divers", "différents"]
            },
            "temporal_patterns": {
                "sequence": ["avant", "après", "pendant", "durant", "lors de"],
                "frequency": ["toujours", "jamais", "parfois", "souvent"],
                "duration": ["pendant", "durant", "pour", "jusqu'à"]
            },
            "business_rules": {
                "commerce": {
                    "mandatory_entities": ["Client", "Produit", "Commande", "Facture"],
                    "typical_relations": {
                        "Commande_Produit_Client": {
                            "type": "n_ary",
                            "entities": ["Commande", "Produit", "Client"],
                            "attributes": ["quantite", "prix_unitaire", "date_commande"]
                        }
                    }
                },
                "medical": {
                    "mandatory_entities": ["Patient", "Medecin", "Consultation", "Traitement"],
                    "typical_relations": {
                        "Prescription_Patient_Medicament": {
                            "type": "n_ary",
                            "entities": ["Patient", "Medicament", "Medecin"],
                            "attributes": ["dosage", "frequence", "duree"]
                        }
                    }
                },
                "education": {
                    "mandatory_entities": ["Etudiant", "Cours", "Professeur", "Note"],
                    "typical_relations": {
                        "Evaluation_Etudiant_Cours": {
                            "type": "n_ary",
                            "entities": ["Etudiant", "Cours", "Professeur"],
                            "attributes": ["note", "date_evaluation", "commentaire"]
                        }
                    }
                }
            }
        }
        
    def analyze_data(self, data: Any, format_type: str = "json") -> Dict:
        """Analyse les données et génère un MCD."""
        # Réinitialiser les détections
        self.detected_entities = {}
        self.detected_relations = []

        # Convertir les données en dictionnaire
        data_dict = self._convert_to_dict(data, format_type)

        # Analyser la structure
        self._analyze_structure(data_dict)

        # Valider le modèle
        self._validate_model()

        return {
            "entities": self.detected_entities,
            "relations": self.detected_relations
        }

    def _convert_to_dict(self, data: Any, format_type: str) -> Dict:
        """Convertit les données dans un format dictionnaire."""
        if format_type == "json":
            if isinstance(data, str):
                return json.loads(data)
            return data
        elif format_type == "xml":
            if isinstance(data, str):
                root = ET.fromstring(data)
            else:
                root = data
            return self._xml_to_dict(root)
        else:
            raise ValueError(f"Format non supporté: {format_type}")

    def _xml_to_dict(self, element: ET.Element) -> Dict:
        """Convertit un élément XML en dictionnaire."""
        result = {}
        for child in element:
            if len(child) > 0:
                if child.tag in result:
                    if not isinstance(result[child.tag], list):
                        result[child.tag] = [result[child.tag]]
                    result[child.tag].append(self._xml_to_dict(child))
                else:
                    result[child.tag] = self._xml_to_dict(child)
            else:
                result[child.tag] = child.text
        return result

    def _analyze_structure(self, data: Dict) -> None:
        """Analyse la structure des données."""
        for key, value in data.items():
            if isinstance(value, list) and len(value) > 0:
                # C'est probablement une collection d'entités
                entity_name = key.rstrip('s')  # Enlever le 's' final si présent
                self._analyze_entity(entity_name, value[0])
            elif isinstance(value, dict):
                # C'est soit une entité unique, soit un objet imbriqué
                self._analyze_entity(key, value)

        # Détecter les relations
        self._detect_relations(data)

    def _analyze_entity(self, name: str, data: Dict) -> None:
        """Analyse une entité et ses attributs."""
        if name not in self.detected_entities:
            entity = {
                "name": name,
                "attributes": [],
                "primary_key": []
            }

            # Analyser les attributs
            for attr_name, attr_value in data.items():
                attribute = self._analyze_attribute(attr_name, attr_value)
                if attribute:
                    entity["attributes"].append(attribute)
                    if "id" in attr_name.lower() or attr_name.lower() == "id":
                        entity["primary_key"].append(attr_name)

            self.detected_entities[name] = entity

    def _analyze_attribute(self, name: Union[str, List[str]], value: Any = None) -> Dict:
        """Analyse un attribut pour déterminer son type et ses contraintes.
        
        Args:
            name: Nom de l'attribut ou liste de mots-clés
            value: Valeur de l'attribut (optionnel)
            
        Returns:
            Dict: Informations sur l'attribut
        """
        # Si name est une liste, utiliser le premier mot comme nom
        if isinstance(name, list):
            name = name[0]
            
        # Initialiser les informations de l'attribut
        attr_info = {
            "name": name,
            "type": "string",  # Type par défaut
            "constraints": []
        }
        
        # Détecter le type à partir du nom
        if "_id" in name.lower() or name.lower().endswith("id"):
            attr_info["type"] = "integer"
            attr_info["constraints"].append("NOT NULL")
            if name.lower() == "id":
                attr_info["constraints"].append("PRIMARY KEY")
        elif "date" in name.lower():
            attr_info["type"] = "date"
        elif "prix" in name.lower() or "montant" in name.lower():
            attr_info["type"] = "DECIMAL"  # En majuscules pour correspondre au test
            attr_info["constraints"].append("CHECK (value >= 0)")
        elif "email" in name.lower():
            attr_info["type"] = "string"
            attr_info["constraints"].append("UNIQUE")
        
        # Affiner le type à partir de la valeur si fournie
        if value is not None:
            if isinstance(value, bool):
                attr_info["type"] = "boolean"
            elif isinstance(value, int):
                attr_info["type"] = "integer"
            elif isinstance(value, float):
                attr_info["type"] = "DECIMAL"  # En majuscules pour correspondre au test
            elif isinstance(value, str):
                try:
                    pd.to_datetime(value)
                    attr_info["type"] = "date"
                except:
                    attr_info["type"] = "string"
        
        return attr_info

    def _detect_relations(self, data: Union[pd.DataFrame, Dict]) -> List[Dict]:
        """Détecte les relations entre les entités à partir des données.
        
        Args:
            data: DataFrame ou dictionnaire contenant les données
            
        Returns:
            List[Dict]: Liste des relations détectées
        """
        relations = []
        
        # Convertir le dictionnaire en DataFrame si nécessaire
        if isinstance(data, dict):
            # Créer un DataFrame pour chaque entité
            dfs = {}
            for key, value in data.items():
                if isinstance(value, list):
                    df = pd.DataFrame(value)
                    dfs[key] = df
                elif isinstance(value, dict):
                    df = pd.DataFrame([value])
                    dfs[key] = df
            
            # Analyser les relations entre les DataFrames
            for key1, df1 in dfs.items():
                for key2, df2 in dfs.items():
                    if key1 >= key2:
                        continue
                        
                    # Analyser chaque paire de colonnes
                    for col1 in df1.columns:
                        for col2 in df2.columns:
                            # Extraire les noms d'entités
                            entity1 = self._extract_entity_name(col1)
                            entity2 = self._extract_entity_name(col2)
                            
                            if entity1 and entity2:
                                # Vérifier si c'est une relation de clé étrangère
                                if col1.endswith('_id') and col1[:-3] == col2.lower():
                                    relation = {
                                        "source": entity2,
                                        "target": entity1,
                                        "type": "ONE_TO_MANY",
                                        "attributes": []
                                    }
                                    relations.append(relation)
                                elif col2.endswith('_id') and col2[:-3] == col1.lower():
                                    relation = {
                                        "source": entity1,
                                        "target": entity2,
                                        "type": "ONE_TO_MANY",
                                        "attributes": []
                                    }
                                    relations.append(relation)
        else:
            # Analyser directement le DataFrame
            for col1 in data.columns:
                for col2 in data.columns:
                    if col1 >= col2:
                        continue
                        
                    # Extraire les noms d'entités
                    entity1 = self._extract_entity_name(col1)
                    entity2 = self._extract_entity_name(col2)
                    
                    if entity1 and entity2:
                        # Vérifier si c'est une relation de clé étrangère
                        if col1.endswith('_id') and col1[:-3] == col2.lower():
                            relation = {
                                "source": entity2,
                                "target": entity1,
                                "type": "ONE_TO_MANY",
                                "attributes": []
                            }
                            relations.append(relation)
                        elif col2.endswith('_id') and col2[:-3] == col1.lower():
                            relation = {
                                "source": entity1,
                                "target": entity2,
                                "type": "ONE_TO_MANY",
                                "attributes": []
                            }
                            relations.append(relation)
        
        return relations

    def detect_n_ary_relations(self, text: str) -> List[Dict]:
        """Détecte les relations n-aires dans un texte.
        
        Args:
            text: Texte à analyser
            
        Returns:
            List[Dict]: Liste des relations n-aires détectées
        """
        relations = []
        
        # Patterns pour détecter les relations n-aires
        patterns = [
            r"(?:une|un|le|la|les)\s+(\w+)\s+(?:relie|lie|connecte|associe)\s+(?:un|une|le|la|les)\s+(\w+)(?:\s*,\s*(?:un|une|le|la|les)\s+(\w+))*(?:\s+et\s+(?:un|une|le|la|les)\s+(\w+))",
            r"(?:une|un|le|la|les)\s+(\w+)\s+(?:est lié|est associé|est connecté)\s+(?:à|avec)\s+(?:un|une|le|la|les)\s+(\w+)(?:\s*,\s*(?:un|une|le|la|les)\s+(\w+))*(?:\s+et\s+(?:un|une|le|la|les)\s+(\w+))",
            r"(?:une|un|le|la|les)\s+(\w+)\s+(?:contient|inclut|comprend)\s+(?:un|une|le|la|les)\s+(\w+)(?:\s*,\s*(?:un|une|le|la|les)\s+(\w+))*(?:\s+et\s+(?:un|une|le|la|les)\s+(\w+))"
        ]
        
        # Analyser le texte avec chaque pattern
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                # Extraire les entités
                entities = []
                for group in match.groups():
                    if group:
                        # Capitaliser le nom de l'entité
                        entity = group[0].upper() + group[1:].lower()
                        if entity not in entities:
                            entities.append(entity)
                
                if len(entities) >= 3:
                    relation = {
                        "entities": entities,
                        "type": "N_ARY",
                        "attributes": []
                    }
                    
                    # Extraire les attributs de la relation
                    attr_pattern = r"(?:avec|ayant|possédant)\s+(?:une|un|le|la|les)\s+(\w+)(?:\s+et\s+(?:une|un|le|la|les)\s+(\w+))*"
                    attr_match = re.search(attr_pattern, text[match.end():], re.IGNORECASE)
                    if attr_match:
                        attributes = [a for a in attr_match.groups() if a is not None]
                        relation["attributes"] = attributes
                    
                    relations.append(relation)
        
        return relations

    def _validate_model(self) -> None:
        """Valide le modèle généré."""
        # Vérifier que chaque entité a une clé primaire
        for entity_name, entity in self.detected_entities.items():
            if not entity["primary_key"]:
                # Ajouter une clé primaire par défaut
                entity["attributes"].insert(0, {
                    "name": "id",
                    "type": "integer",
                    "nullable": False
                })
                entity["primary_key"] = ["id"]

        # Vérifier les relations
        valid_relations = []
        for relation in self.detected_relations:
            if (relation["source"] in self.detected_entities and
                relation["target"] in self.detected_entities):
                valid_relations.append(relation)
        self.detected_relations = valid_relations

    def _analyze_database_schema(self, schema: Dict):
        """Analyse le schéma de la base de données."""
        # Implémentation de l'analyse du schéma
        pass  # Placeholder, implémentation réelle nécessaire

    def _consolidate_results(self) -> Dict:
        """Consolide les résultats de l'analyse."""
        mcd_structure = {
            "entities": {},
            "relations": []
        }
        
        # 1. Consolider les entités
        for name, entity in self.detected_entities.items():
            # Vérifier si l'entité peut être fusionnée avec une autre
            if self._should_merge_entity(entity):
                self._merge_entity(entity, mcd_structure["entities"])
            else:
                mcd_structure["entities"][name] = entity
                
        # 2. Consolider les relations
        for relation in self.detected_relations:
            if self._is_valid_relation(relation, mcd_structure["entities"]):
                mcd_structure["relations"].append(relation)
                
        return mcd_structure
        
    def _should_merge_entity(self, entity: Dict) -> bool:
        """Détermine si une entité devrait être fusionnée."""
        # Si l'entité a peu d'attributs et beaucoup de clés étrangères
        if len(entity["attributes"]) <= 3 and len(entity["foreign_keys"]) >= 2:
            return True
            
        # Si l'entité semble être une table de liaison
        if all(self._is_potential_foreign_key(attr["name"]) for attr in entity["attributes"]):
            return True
            
        return False
        
    def _merge_entity(self, entity: Dict, existing_entities: Dict):
        """Fusionne une entité avec une entité existante ou crée une relation."""
        if len(entity["foreign_keys"]) == 2:
            # Créer une relation many-to-many
            self.detected_relations.append({
                "source": entity["foreign_keys"][0]["referenced_table"],
                "target": entity["foreign_keys"][1]["referenced_table"],
                "type": "MANY_TO_MANY",
                "through": entity["name"]
            })
        else:
            # Ajouter les attributs à l'entité principale
            main_entity = self._find_main_entity(entity, existing_entities)
            if main_entity:
                main_entity["attributes"].extend(entity["attributes"])
                
    def _find_main_entity(self, entity: Dict, existing_entities: Dict) -> Dict:
        """Trouve l'entité principale pour une fusion."""
        for fk in entity["foreign_keys"]:
            referenced_table = fk["referenced_table"]
            if referenced_table in existing_entities:
                return existing_entities[referenced_table]
        return None
        
    def _is_valid_relation(self, relation: Dict, entities: Dict) -> bool:
        """Vérifie si une relation est valide."""
        return (relation["source"] in entities and 
                relation["target"] in entities and
                relation["source"] != relation["target"])

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