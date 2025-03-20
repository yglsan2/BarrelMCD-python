from typing import Dict, List, Set, Tuple
import pandas as pd
import numpy as np
from collections import defaultdict
import re
from enum import Enum

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

class DataAnalyzer:
    """Analyseur intelligent de données pour la génération de MCD"""
    
    def __init__(self):
        self.entity_templates = EntityTemplate
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
        
        # Patterns pour la détection intelligente des entités
        self.entity_patterns = {
            "acteur": {
                "mots_cles": ["utilisateur", "client", "employé", "personne", "membre"],
                "attributs_communs": ["nom", "prénom", "email", "téléphone"],
                "actions_typiques": ["connexion", "inscription", "modification"]
            },
            "document": {
                "mots_cles": ["facture", "commande", "contrat", "devis", "rapport"],
                "attributs_communs": ["numéro", "date", "montant", "statut"],
                "actions_typiques": ["création", "validation", "envoi"]
            },
            "transaction": {
                "mots_cles": ["paiement", "virement", "achat", "vente"],
                "attributs_communs": ["montant", "date", "statut", "référence"],
                "actions_typiques": ["effectuer", "valider", "annuler"]
            },
            "catalogue": {
                "mots_cles": ["produit", "service", "article", "catégorie"],
                "attributs_communs": ["nom", "description", "prix", "référence"],
                "actions_typiques": ["ajout", "modification", "recherche"]
            }
        }
        
        # Règles métier pour l'analyse intelligente
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
        
    def analyze_data(self, data: Dict[str, pd.DataFrame] = None, text: str = None, 
                    database_schema: Dict = None) -> Dict:
        """Analyse les données avec une intelligence améliorée."""
        self.detected_entities = {}
        self.detected_relations = []
        
        # 1. Analyser le contexte métier
        business_context = self._detect_business_context(data, text, database_schema)
        
        # 2. Appliquer les règles métier spécifiques
        if business_context:
            self._apply_business_rules(business_context)
        
        # 3. Analyser les données selon leur type
        if data:
            self._analyze_dataframes(data)
        if text:
            self._analyze_text(text)
        if database_schema:
            self._analyze_database_schema(database_schema)
            
        # 4. Détecter les patterns récurrents
        self._detect_patterns()
        
        # 5. Optimiser le modèle
        self._optimize_model()
        
        # 6. Valider la cohérence
        self._validate_model()
        
        return self._consolidate_results()
        
    def _detect_business_context(self, data, text, schema) -> str:
        """Détecte le contexte métier à partir des données."""
        contexts = defaultdict(int)
        
        # Analyser les noms de tables/colonnes
        if data:
            for df_name, df in data.items():
                self._analyze_names_for_context(df_name, df.columns, contexts)
                
        # Analyser le schéma
        if schema:
            for table_name, table_info in schema.items():
                self._analyze_names_for_context(table_name, 
                    [col["name"] for col in table_info["columns"]], contexts)
                
        # Analyser le texte
        if text:
            self._analyze_text_for_context(text, contexts)
            
        # Retourner le contexte le plus probable
        if contexts:
            return max(contexts.items(), key=lambda x: x[1])[0]
        return None
        
    def _analyze_names_for_context(self, table_name: str, column_names: List[str], contexts: Dict):
        """Analyse les noms pour détecter le contexte métier."""
        for context, rules in self.business_rules.items():
            # Vérifier les entités obligatoires
            for entity in rules["entites_obligatoires"]:
                if entity in table_name.lower():
                    contexts[context] += 2
                if any(entity in col.lower() for col in column_names):
                    contexts[context] += 1
                    
            # Vérifier les attributs calculés
            for entity, attrs in rules["attributs_calcules"].items():
                if any(attr in col.lower() for col in column_names for attr in attrs):
                    contexts[context] += 1
                    
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
                    
    def _apply_business_rules(self, context: str):
        """Applique les règles métier du contexte détecté."""
        if context not in self.business_rules:
            return
            
        rules = self.business_rules[context]
        
        # Ajouter les entités obligatoires manquantes
        for entity in rules["entites_obligatoires"]:
            if entity not in self.detected_entities:
                template = self.entity_templates.get_template(entity)
                if template:
                    self.detected_entities[entity] = self._create_entity_from_template(entity, template)
                    
        # Ajouter les relations typiques
        for source, target, rel_type in rules["relations_typiques"]:
            if source in self.detected_entities and target in self.detected_entities:
                self._add_relation(source, target, rel_type)
                
        # Ajouter les attributs calculés
        for entity, attrs in rules["attributs_calcules"].items():
            if entity in self.detected_entities:
                for attr in attrs:
                    self._add_calculated_attribute(entity, attr)
                    
    def _detect_patterns(self):
        """Détecte les patterns récurrents dans les données."""
        # 1. Détecter les groupes d'attributs similaires
        attribute_groups = self._find_similar_attributes()
        
        # 2. Détecter les hiérarchies
        hierarchies = self._detect_hierarchies()
        
        # 3. Détecter les entités faibles
        weak_entities = self._detect_weak_entities()
        
        # 4. Optimiser le modèle en fonction des patterns détectés
        self._apply_detected_patterns(attribute_groups, hierarchies, weak_entities)
        
    def _find_similar_attributes(self) -> Dict:
        """Trouve les groupes d'attributs similaires."""
        groups = defaultdict(list)
        
        for entity_name, entity in self.detected_entities.items():
            for attr in entity["attributes"]:
                # Normaliser le nom de l'attribut
                normalized_name = self._normalize_attribute_name(attr["name"])
                
                # Grouper par type et pattern de nom
                key = (attr["type"], normalized_name)
                groups[key].append((entity_name, attr["name"]))
                
        return groups
        
    def _detect_hierarchies(self) -> List[Dict]:
        """Détecte les relations hiérarchiques."""
        hierarchies = []
        
        for entity_name, entity in self.detected_entities.items():
            # Détecter les auto-références
            for fk in entity["foreign_keys"]:
                if fk["referenced_table"] == entity_name:
                    hierarchies.append({
                        "type": "self_reference",
                        "entity": entity_name,
                        "key": fk["column"]
                    })
                    
            # Détecter les chaînes de références
            chain = self._find_reference_chain(entity_name)
            if chain:
                hierarchies.append({
                    "type": "reference_chain",
                    "chain": chain
                })
                
        return hierarchies
        
    def _detect_weak_entities(self) -> List[str]:
        """Détecte les entités faibles."""
        weak_entities = []
        
        for entity_name, entity in self.detected_entities.items():
            # Une entité est considérée faible si :
            # 1. Elle a une clé étrangère obligatoire
            # 2. Sa clé primaire inclut une clé étrangère
            # 3. Elle a peu d'attributs propres
            
            if (len(entity["foreign_keys"]) > 0 and
                any(fk["column"] in entity["primary_key"] for fk in entity["foreign_keys"]) and
                len([attr for attr in entity["attributes"] 
                     if not self._is_foreign_key(attr["name"])]) <= 3):
                weak_entities.append(entity_name)
                
        return weak_entities
        
    def _apply_detected_patterns(self, attribute_groups, hierarchies, weak_entities):
        """Applique les patterns détectés pour optimiser le modèle."""
        # 1. Factoriser les attributs similaires
        self._factorize_similar_attributes(attribute_groups)
        
        # 2. Optimiser les hiérarchies
        self._optimize_hierarchies(hierarchies)
        
        # 3. Gérer les entités faibles
        self._handle_weak_entities(weak_entities)
        
    def _factorize_similar_attributes(self, attribute_groups):
        """Factorise les attributs similaires en créant des entités de référence."""
        for (attr_type, pattern), occurrences in attribute_groups.items():
            if len(occurrences) >= 3:  # Seuil pour la factorisation
                # Créer une nouvelle entité de référence
                ref_entity_name = f"Ref_{pattern.title()}"
                
                if ref_entity_name not in self.detected_entities:
                    self.detected_entities[ref_entity_name] = {
                        "name": ref_entity_name,
                        "attributes": [
                            {"name": "id", "type": "integer", "primary_key": True},
                            {"name": "value", "type": attr_type}
                        ],
                        "primary_key": ["id"]
                    }
                    
                # Mettre à jour les références dans les entités d'origine
                for entity_name, attr_name in occurrences:
                    self._add_reference(entity_name, ref_entity_name, attr_name)
                    
    def _optimize_hierarchies(self, hierarchies):
        """Optimise les structures hiérarchiques détectées."""
        for hierarchy in hierarchies:
            if hierarchy["type"] == "self_reference":
                # Ajouter des attributs de niveau
                entity = self.detected_entities[hierarchy["entity"]]
                entity["attributes"].append({
                    "name": "level",
                    "type": "integer",
                    "nullable": True
                })
                entity["attributes"].append({
                    "name": "path",
                    "type": "varchar",
                    "nullable": True
                })
                
            elif hierarchy["type"] == "reference_chain":
                # Ajouter des raccourcis pour les requêtes fréquentes
                chain = hierarchy["chain"]
                if len(chain) > 2:
                    start_entity = self.detected_entities[chain[0]]
                    end_entity = self.detected_entities[chain[-1]]
                    self._add_reference(chain[0], chain[-1], f"direct_{chain[-1].lower()}_id")
                    
    def _handle_weak_entities(self, weak_entities):
        """Gère les entités faibles détectées."""
        for entity_name in weak_entities:
            entity = self.detected_entities[entity_name]
            
            # Ajouter un attribut composite pour l'identification
            composite_key = []
            for fk in entity["foreign_keys"]:
                if fk["column"] in entity["primary_key"]:
                    composite_key.append(fk["column"])
                    
            if composite_key:
                entity["composite_key"] = composite_key
                
            # Marquer l'entité comme faible
            entity["is_weak"] = True
            
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
        
    def _find_reference_chain(self, start_entity: str, visited: Set = None) -> List[str]:
        """Trouve une chaîne de références à partir d'une entité."""
        if visited is None:
            visited = set()
            
        if start_entity in visited:
            return None
            
        visited.add(start_entity)
        entity = self.detected_entities[start_entity]
        
        # Parcourir les clés étrangères
        for fk in entity["foreign_keys"]:
            target = fk["referenced_table"]
            if target not in visited:
                chain = self._find_reference_chain(target, visited)
                if chain:
                    return [start_entity] + chain
                    
        return [start_entity]
        
    def _add_reference(self, source_entity: str, target_entity: str, attr_name: str):
        """Ajoute une référence entre deux entités."""
        entity = self.detected_entities[source_entity]
        
        # Supprimer l'ancien attribut s'il existe
        entity["attributes"] = [
            attr for attr in entity["attributes"]
            if attr["name"] != attr_name
        ]
        
        # Ajouter la nouvelle référence
        entity["foreign_keys"].append({
            "column": attr_name,
            "referenced_table": target_entity
        })
        
        entity["attributes"].append({
            "name": attr_name,
            "type": "integer",
            "nullable": True,
            "foreign_key": {
                "table": target_entity,
                "column": "id"
            }
        })
        
    def _add_calculated_attribute(self, entity_name: str, attr_name: str):
        """Ajoute un attribut calculé à une entité."""
        entity = self.detected_entities[entity_name]
        
        # Déterminer le type approprié
        attr_type = "decimal"
        if any(word in attr_name for word in ["nombre", "quantite", "count"]):
            attr_type = "integer"
            
        # Ajouter l'attribut calculé
        entity["attributes"].append({
            "name": attr_name,
            "type": attr_type,
            "nullable": True,
            "is_calculated": True
        })
        
    def _validate_model(self):
        """Valide la cohérence globale du modèle."""
        # 1. Vérifier les références circulaires
        self._check_circular_references()
        
        # 2. Vérifier la normalisation
        self._check_normalization()
        
        # 3. Vérifier la cohérence des cardinalités
        self._check_cardinality_consistency()
        
    def _check_circular_references(self):
        """Vérifie et corrige les références circulaires."""
        def find_cycle(entity, visited, path):
            if entity in path:
                return path[path.index(entity):]
            if entity in visited:
                return None
                
            visited.add(entity)
            path.append(entity)
            
            for fk in self.detected_entities[entity]["foreign_keys"]:
                target = fk["referenced_table"]
                cycle = find_cycle(target, visited, path)
                if cycle:
                    return cycle
                    
            path.pop()
            return None
            
        # Détecter et corriger les cycles
        for entity_name in self.detected_entities:
            cycle = find_cycle(entity_name, set(), [])
            if cycle:
                # Transformer la référence circulaire en relation many-to-many
                self._break_reference_cycle(cycle)
                
    def _check_normalization(self):
        """Vérifie et améliore la normalisation du modèle."""
        for entity_name, entity in self.detected_entities.items():
            # Détecter les dépendances fonctionnelles
            dependencies = self._find_functional_dependencies(entity)
            
            # Appliquer la normalisation si nécessaire
            if dependencies:
                self._normalize_entity(entity_name, dependencies)
                
    def _check_cardinality_consistency(self):
        """Vérifie la cohérence des cardinalités."""
        for relation in self.detected_relations:
            source = self.detected_entities[relation["source"]]
            target = self.detected_entities[relation["target"]]
            
            # Vérifier la cohérence des clés étrangères
            if relation["type"] == "ONE_TO_ONE":
                if not any(attr.get("unique") for attr in source["attributes"]):
                    # Ajouter la contrainte d'unicité manquante
                    for attr in source["attributes"]:
                        if attr["name"] == f"{target['name'].lower()}_id":
                            attr["unique"] = True
                            
            # Vérifier les relations many-to-many
            elif relation["type"] == "MANY_TO_MANY":
                if not any(rel["through"] for rel in self.detected_relations
                         if rel["source"] == relation["source"]
                         and rel["target"] == relation["target"]):
                    # Créer la table de liaison manquante
                    self._create_junction_table(relation["source"], relation["target"])
                    
    def _break_reference_cycle(self, cycle: List[str]):
        """Brise un cycle de références en créant une table de liaison."""
        # Choisir deux entités du cycle pour créer la relation many-to-many
        entity1, entity2 = cycle[:2]
        
        # Supprimer la référence directe
        self._remove_foreign_key(entity1, entity2)
        
        # Créer une table de liaison
        self._create_junction_table(entity1, entity2)
        
    def _find_functional_dependencies(self, entity: Dict) -> List[Dict]:
        """Trouve les dépendances fonctionnelles dans une entité."""
        dependencies = []
        
        # Analyser les attributs pour trouver des dépendances
        non_key_attrs = [attr for attr in entity["attributes"]
                        if attr["name"] not in entity["primary_key"]]
        
        for attr1 in non_key_attrs:
            related_attrs = []
            for attr2 in non_key_attrs:
                if attr1 != attr2 and self._are_attributes_related(attr1, attr2):
                    related_attrs.append(attr2["name"])
                    
            if related_attrs:
                dependencies.append({
                    "determinant": attr1["name"],
                    "dependent": related_attrs
                })
                
        return dependencies
        
    def _normalize_entity(self, entity_name: str, dependencies: List[Dict]):
        """Normalise une entité en fonction des dépendances fonctionnelles."""
        entity = self.detected_entities[entity_name]
        
        for dep in dependencies:
            # Créer une nouvelle entité pour la dépendance
            new_entity_name = f"{entity_name}_{dep['determinant']}"
            
            if new_entity_name not in self.detected_entities:
                # Créer la nouvelle entité
                new_entity = {
                    "name": new_entity_name,
                    "attributes": [
                        {"name": "id", "type": "integer", "primary_key": True}
                    ],
                    "primary_key": ["id"],
                    "foreign_keys": []
                }
                
                # Déplacer les attributs dépendants
                attrs_to_move = [dep["determinant"]] + dep["dependent"]
                for attr_name in attrs_to_move:
                    attr = next(a for a in entity["attributes"] if a["name"] == attr_name)
                    new_entity["attributes"].append(attr)
                    entity["attributes"].remove(attr)
                    
                # Ajouter la référence
                self._add_reference(entity_name, new_entity_name, f"{new_entity_name.lower()}_id")
                
                # Ajouter la nouvelle entité
                self.detected_entities[new_entity_name] = new_entity
                
    def _create_junction_table(self, entity1: str, entity2: str):
        """Crée une table de liaison entre deux entités."""
        table_name = f"{entity1}_{entity2}"
        
        if table_name not in self.detected_entities:
            # Créer la table de liaison
            junction_table = {
                "name": table_name,
                "attributes": [
                    {"name": f"{entity1.lower()}_id", "type": "integer"},
                    {"name": f"{entity2.lower()}_id", "type": "integer"}
                ],
                "primary_key": [f"{entity1.lower()}_id", f"{entity2.lower()}_id"],
                "foreign_keys": [
                    {
                        "column": f"{entity1.lower()}_id",
                        "referenced_table": entity1
                    },
                    {
                        "column": f"{entity2.lower()}_id",
                        "referenced_table": entity2
                    }
                ]
            }
            
            self.detected_entities[table_name] = junction_table
            
            # Mettre à jour les relations
            self.detected_relations.append({
                "source": entity1,
                "target": entity2,
                "type": "MANY_TO_MANY",
                "through": table_name
            })

    def _analyze_dataframes(self, data: Dict[str, pd.DataFrame]):
        """Analyse les DataFrames pour détecter la structure."""
        for table_name, df in data.items():
            # 1. Détecter le template correspondant
            template_name, score = self.entity_templates.find_matching_template(
                df.columns, df
            )
            
            if score > 0.6:  # Seuil de confiance
                template = self.entity_templates.get_template(template_name)
                entity = self._create_entity_from_template(template_name, template, df)
            else:
                entity = self._analyze_dataframe_structure(table_name, df)
                
            self.detected_entities[table_name] = entity
            
            # 2. Détecter les relations
            self._detect_relations_from_dataframe(table_name, df)
            
    def _analyze_dataframe_structure(self, table_name: str, df: pd.DataFrame) -> Dict:
        """Analyse la structure d'un DataFrame."""
        entity = {
            "name": table_name,
            "attributes": [],
            "primary_key": [],
            "foreign_keys": []
        }
        
        # Analyser chaque colonne
        for col in df.columns:
            attr = self._analyze_column(col, df[col])
            entity["attributes"].append(attr)
            
            # Détecter les clés primaires potentielles
            if self._is_potential_primary_key(df[col]):
                entity["primary_key"].append(col)
                
            # Détecter les clés étrangères potentielles
            if self._is_potential_foreign_key(col):
                entity["foreign_keys"].append({
                    "column": col,
                    "referenced_table": self._extract_referenced_table(col)
                })
                
        return entity
        
    def _analyze_column(self, name: str, series: pd.Series) -> Dict:
        """Analyse une colonne pour déterminer ses caractéristiques."""
        attr = {
            "name": name,
            "type": self._determine_column_type(series),
            "nullable": series.isnull().any(),
            "unique": series.nunique() == len(series),
            "stats": {
                "distinct_values": series.nunique(),
                "null_ratio": series.isnull().mean(),
                "numeric_ratio": pd.to_numeric(series, errors='coerce').notnull().mean()
            }
        }
        
        # Détecter si c'est un identifiant
        if self._is_potential_identifier(name, series):
            attr["is_identifier"] = True
            
        return attr
        
    def _determine_column_type(self, series: pd.Series) -> str:
        """Détermine le type de données d'une colonne."""
        if pd.api.types.is_integer_dtype(series):
            return "integer"
        elif pd.api.types.is_float_dtype(series):
            return "decimal"
        elif pd.api.types.is_datetime64_any_dtype(series):
            return "datetime"
        elif pd.api.types.is_bool_dtype(series):
            return "boolean"
        elif series.dtype == "object":
            # Analyser plus en détail les chaînes
            sample = series.dropna().head(100)
            if all(self._is_date_string(str(x)) for x in sample):
                return "date"
            elif all(len(str(x)) == 1 for x in sample):
                return "char"
            elif all("@" in str(x) for x in sample):
                return "email"
            elif len(sample.str.len().unique()) == 1:
                return f"char({sample.str.len().iloc[0]})"
            else:
                return "varchar"
        return "text"
        
    def _is_date_string(self, text: str) -> bool:
        """Vérifie si une chaîne est une date."""
        date_patterns = [
            r"\d{4}-\d{2}-\d{2}",
            r"\d{2}/\d{2}/\d{4}",
            r"\d{2}\.\d{2}\.\d{4}"
        ]
        return any(re.match(pattern, text) for pattern in date_patterns)
        
    def _is_potential_primary_key(self, series: pd.Series) -> bool:
        """Détermine si une colonne peut être une clé primaire."""
        return (series.nunique() == len(series) and 
                not series.isnull().any() and
                (series.dtype in ["int64", "object"]))
                
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
        
    def _detect_relations_from_dataframe(self, table_name: str, df: pd.DataFrame):
        """Détecte les relations à partir d'un DataFrame."""
        for col in df.columns:
            if self._is_potential_foreign_key(col):
                referenced_table = self._extract_referenced_table(col)
                if referenced_table:
                    relation = {
                        "source": table_name,
                        "target": referenced_table,
                        "type": self._determine_relation_type(df[col]),
                        "column": col
                    }
                    self.detected_relations.append(relation)
                    
    def _determine_relation_type(self, series: pd.Series) -> str:
        """Détermine le type de relation basé sur les données."""
        if series.nunique() == len(series) and not series.isnull().any():
            return "ONE_TO_ONE"
        elif series.nunique() < len(series):
            return "MANY_TO_ONE"
        return "ONE_TO_MANY"
        
    def _analyze_text(self, text: str):
        """Analyse un texte descriptif pour détecter la structure."""
        sentences = self._split_into_sentences(text.lower())
        
        for sentence in sentences:
            # 1. Détecter les entités
            entities = self._detect_entities_in_text(sentence)
            
            # 2. Détecter les relations et cardinalités
            if len(entities) >= 2:
                self._analyze_relationship(sentence, entities)
                
    def _split_into_sentences(self, text: str) -> List[str]:
        """Découpe le texte en phrases."""
        # Patterns de fin de phrase
        end_patterns = r'[.!?]+'
        
        # Découper en gardant les séparateurs
        parts = re.split(f'({end_patterns})', text)
        
        # Reconstituer les phrases
        sentences = []
        current = ""
        
        for part in parts:
            current += part
            if re.search(end_patterns, part):
                sentences.append(current.strip())
                current = ""
                
        if current:
            sentences.append(current.strip())
            
        return sentences
        
    def _detect_entities_in_text(self, sentence: str) -> List[str]:
        """Détecte les entités dans une phrase."""
        entities = []
        
        # 1. Chercher les entités connues
        for template_name, template in self.entity_templates.TEMPLATES.items():
            for keyword in template["mots_cles"]:
                if keyword in sentence:
                    entities.append(template_name)
                    break
                    
        # 2. Chercher les mots avec majuscules (potentielles entités)
        words = re.findall(r'\b[A-Z][a-z]+\b', sentence)
        entities.extend(word.lower() for word in words)
        
        # 3. Chercher les patterns d'entités
        for entity_type, patterns in self.entity_patterns.items():
            for keyword in patterns["mots_cles"]:
                if keyword in sentence:
                    entities.append(entity_type)
                    
        return list(set(entities))
        
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

    def _are_attributes_related(self, attr1: Dict, attr2: Dict) -> bool:
        """Détermine si deux attributs sont liés fonctionnellement."""
        # 1. Vérifier les noms similaires
        name1 = self._normalize_attribute_name(attr1["name"])
        name2 = self._normalize_attribute_name(attr2["name"])
        
        if name1 == name2:
            return False  # Même attribut
            
        # 2. Vérifier les préfixes/suffixes communs
        common_prefixes = ["date", "code", "numero", "ref", "id"]
        if any(prefix in name1 and prefix in name2 for prefix in common_prefixes):
            return True
            
        # 3. Vérifier les types compatibles
        if attr1["type"] == attr2["type"]:
            # Pour les types numériques
            if attr1["type"] in ["integer", "decimal"]:
                # Vérifier si l'un est un total/somme de l'autre
                if ("total" in name1 and not "total" in name2) or \
                   ("total" in name2 and not "total" in name1):
                    return True
                    
            # Pour les dates
            elif attr1["type"] in ["date", "datetime"]:
                # Vérifier si les dates sont liées (début/fin)
                date_pairs = [("debut", "fin"), ("creation", "modification")]
                for start, end in date_pairs:
                    if (start in name1 and end in name2) or \
                       (start in name2 and end in name1):
                        return True
                        
        return False

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

    def detect_n_ary_relations(self, text: str) -> List[Dict]:
        """Détecte les relations n-aires dans le texte."""
        n_ary_relations = []
        sentences = self._split_into_sentences(text)
        
        for sentence in sentences:
            # Recherche des indicateurs de relation n-aire
            if self._has_n_ary_indicators(sentence):
                entities = self._extract_entities(sentence)
                if len(entities) >= 3:  # Une relation n-aire implique au moins 3 entités
                    attributes = self._extract_attributes(sentence)
                    n_ary_relations.append({
                        "entities": entities,
                        "attributes": attributes,
                        "description": sentence
                    })
                    
        return n_ary_relations

    def _has_n_ary_indicators(self, sentence: str) -> bool:
        """Vérifie si la phrase contient des indicateurs de relation n-aire."""
        patterns = self.semantic_patterns["n_ary_indicators"]
        words = sentence.lower().split()
        
        # Vérifier la présence d'indicateurs
        has_verb = any(verb in sentence.lower() for verb in patterns["verbs"])
        has_multiple_entities = len(re.findall(r'[A-Z][a-z]+', sentence)) >= 3
        has_conjunction = any(conj in sentence.lower() for conj in patterns["conjunctions"])
        
        return has_verb and has_multiple_entities and has_conjunction

    def _extract_entities(self, sentence: str) -> List[str]:
        """Extrait les entités d'une phrase."""
        entities = []
        # Recherche des mots commençant par une majuscule
        potential_entities = re.findall(r'[A-Z][a-z]+', sentence)
        
        for entity in potential_entities:
            # Vérifier si c'est une entité valide selon le contexte
            if self._validate_entity(entity):
                entities.append(entity)
                
        return entities

    def _extract_attributes(self, sentence: str) -> List[Dict]:
        """Extrait les attributs d'une relation."""
        attributes = []
        # Recherche des attributs potentiels
        words = sentence.lower().split()
        
        for i, word in enumerate(words):
            if word in ["avec", "contenant", "incluant"]:
                # Analyser les mots suivants pour trouver des attributs
                potential_attr = words[i+1:i+4]
                attr_info = self._analyze_attribute(potential_attr)
                if attr_info:
                    attributes.append(attr_info)
                    
        return attributes

    def _analyze_attribute(self, words: List[str]) -> Optional[Dict]:
        """Analyse un attribut potentiel pour déterminer son type et ses contraintes."""
        if not words:
            return None
            
        attr_name = words[0]
        attr_type = self._guess_attribute_type(words)
        constraints = self._detect_constraints(words)
        
        return {
            "name": attr_name,
            "type": attr_type,
            "constraints": constraints
        }

    def _guess_attribute_type(self, words: List[str]) -> str:
        """Devine le type d'un attribut basé sur son contexte."""
        type_indicators = {
            "nombre": "INTEGER",
            "montant": "DECIMAL",
            "date": "DATE",
            "heure": "TIME",
            "texte": "VARCHAR",
            "description": "TEXT",
            "statut": "ENUM",
            "email": "VARCHAR(255)",
            "telephone": "VARCHAR(20)"
        }
        
        for word in words:
            for indicator, type_ in type_indicators.items():
                if indicator in word.lower():
                    return type_
                    
        return "VARCHAR(255)"  # Type par défaut

    def _detect_constraints(self, words: List[str]) -> List[str]:
        """Détecte les contraintes sur un attribut."""
        constraints = []
        constraint_indicators = {
            "obligatoire": "NOT NULL",
            "unique": "UNIQUE",
            "positif": "CHECK (value > 0)",
            "supérieur": "CHECK",
            "inférieur": "CHECK"
        }
        
        for word in words:
            for indicator, constraint in constraint_indicators.items():
                if indicator in word.lower():
                    constraints.append(constraint)
                    
        return constraints

    def _validate_entity(self, entity: str) -> bool:
        """Vérifie si une entité est valide selon le contexte."""
        # Implémentation de la validation de l'entité
        return True  # Placeholder, implémentation réelle nécessaire

    def _remove_foreign_key(self, source_entity: str, target_entity: str):
        """Supprime une référence entre deux entités."""
        entity = self.detected_entities[source_entity]
        
        # Supprimer la référence
        entity["foreign_keys"] = [
            fk for fk in entity["foreign_keys"]
            if fk["referenced_table"] != target_entity
        ]
        
        # Mettre à jour les références dans les entités cibles
        for fk in self.detected_entities[target_entity]["foreign_keys"]:
            if fk["referenced_table"] == source_entity:
                fk["referenced_table"] = None
                
    def _analyze_database_schema(self, schema: Dict):
        """Analyse le schéma de la base de données."""
        # Implémentation de l'analyse du schéma
        pass  # Placeholder, implémentation réelle nécessaire

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