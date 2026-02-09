#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Parseur Markdown vers MCD (Modèle Conceptuel de Données)
Version 2.0 - Correction fondamentale : Pas de clés en MCD
"""

import re
import json
from typing import Dict, List, Optional, Tuple
from enum import Enum

class CardinalityType(Enum):
    """Types de cardinalités possibles - Version étendue"""
    ONE_TO_ONE = "1,1"
    ONE_TO_MANY = "1,n"
    MANY_TO_ONE = "n,1"
    MANY_TO_MANY = "n,n"
    ZERO_TO_ONE = "0,1"
    ZERO_TO_MANY = "0,n"
    ONE_TO_ZERO_OR_ONE = "1,0..1"
    ZERO_OR_ONE_TO_MANY = "0..1,n"
    ONE_TO_OPTIONAL = "1,0..1"
    OPTIONAL_TO_MANY = "0..1,n"
    EXACTLY_ONE = "1,1"
    ZERO_OR_ONE = "0,1"

class MarkdownMCDParser:
    """Parseur Markdown vers MCD avec support étendu"""
    
    def __init__(self, verbose: bool = False):
        self.entities = {}
        self.associations = []
        self.current_entity = None
        self.current_association = None
        self.inheritance_hierarchy = {}
        self.foreign_key_mappings = {}
        self.verbose = verbose
        
    def log(self, message: str):
        """Log avec mode verbose"""
        if self.verbose:
            print(f"🔍 DEBUG: {message}")
    
    def parse_markdown(self, markdown_content: str) -> Dict:
        """Parse le contenu markdown vers une structure MCD"""
        self.log("=== DÉBUT DU PARSING MARKDOWN ===")
        self.log(f"Contenu à parser: {len(markdown_content)} caractères")
        
        lines = markdown_content.split('\n')
        self.log(f"Nombre de lignes: {len(lines)}")
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
                
            self.log(f"Ligne {i+1}: '{line}'")
            
            # Détecter les associations (titre de niveau 2 avec <->)
            if line.startswith('## ') and '<->' in line:
                self.log(f"🔍 Détection association (niveau 2): {line}")
                self._parse_association_header(line.replace('## ', '### '))
            # Détecter les entités (titre de niveau 2)
            elif line.startswith('## '):
                self.log(f"🔍 Détection entité: {line}")
                self._parse_entity_header(line)
            # Détecter les associations (titre de niveau 3)
            elif line.startswith('### '):
                self.log(f"🔍 Détection association (niveau 3): {line}")
                self._parse_association_header(line)
            # Détecter les attributs (liste avec -)
            elif line.startswith('- '):
                self.log(f"🔍 Détection attribut: {line}")
                self._parse_attribute(line)
            # Détecter les cardinalités (ligne avec cardinalité)
            elif ':' in line and self._contains_cardinality(line):
                self.log(f"🔍 Détection cardinalité: {line}")
                self._parse_cardinality(line)
            # Détecter les descriptions d'associations
            elif line.startswith('**') and line.endswith('**'):
                self.log(f"🔍 Détection description: {line}")
                self._parse_association_description(line)
            # Détecter les héritages
            elif 'hérite' in line.lower() or 'extends' in line.lower():
                self.log(f"🔍 Détection héritage: {line}")
                self._parse_inheritance(line)
        
        self.log("=== FIN DU PARSING LIGNE PAR LIGNE ===")
        
        # Traitement post-parsing
        self.log("=== TRAITEMENT POST-PARSING ===")
        self._process_inheritance()
        
        # Construction de la structure finale
        self.log("=== CONSTRUCTION STRUCTURE FINALE ===")
        mcd_structure = self._build_mcd_structure()
        
        self.log(f"Structure finale:")
        self.log(f"  - Entités: {len(self.entities)}")
        self.log(f"  - Associations: {len(self.associations)}")
        self.log(f"  - Héritage: {len(self.inheritance_hierarchy)}")
        
        return mcd_structure

    def _parse_entity_header(self, line: str):
        """Parse un en-tête d'entité pour MCD (pas de clés primaires)"""
        entity_text = line[3:].strip()  # Enlever '## '
        self.log(f"Parsing entité: '{entity_text}'")
        
        # Vérifier s'il y a de l'héritage dans l'en-tête
        inheritance_patterns = [
            r'(\w+)\s+hérite\s+de\s+(\w+)',
            r'(\w+)\s+extends\s+(\w+)',
        ]
        
        for pattern in inheritance_patterns:
            match = re.search(pattern, entity_text, re.IGNORECASE)
            if match:
                child = self._clean_entity_name(match.group(1))
                parent = self._clean_entity_name(match.group(2))
                self.log(f"Héritage détecté: {child} hérite de {parent}")
                
                # Créer l'entité parent si elle n'existe pas
                if parent not in self.entities:
                    self.log(f"Création entité parent: {parent}")
                    self.entities[parent] = {
                        'name': parent,
                        'attributes': [],
                        'description': '',
                        'parent': None,
                        'children': []
                    }
                
                # Créer l'entité enfant
                self.log(f"Création entité enfant: {child}")
                self.current_entity = child
                self.entities[child] = {
                    'name': child,
                    'attributes': [],
                    'description': '',
                    'parent': parent,
                    'children': []
                }
                
                # Établir la relation d'héritage
                self.entities[parent]['children'].append(child)
                self.inheritance_hierarchy[child] = parent
                self.log(f"Héritage établi: {child} -> {parent}")
                return
        
        # Pas d'héritage, entité normale
        entity_name = self._clean_entity_name(entity_text)
        self.log(f"Entité normale: {entity_name}")
        self.current_entity = entity_name
        self.entities[entity_name] = {
            'name': entity_name,
            'attributes': [],
            'description': '',
            'parent': None,
            'children': []
        }
        
    def _parse_association_header(self, line: str):
        """Parse un en-tête d'association avec support étendu"""
        association_text = line[4:].strip()  # Enlever '### '
        self.log(f"Parsing association: '{association_text}'")
        
        # Extraire les entités et le nom de l'association
        entities_and_name = self._extract_entities_from_association(association_text)
        
        if entities_and_name:
            entity1, entity2, association_name = entities_and_name
            self.log(f"Association extraite: {entity1} <-> {entity2} : {association_name}")
            
            self.current_association = {
                'name': association_name,
                'entity1': entity1,
                'entity2': entity2,
                'cardinality1': '1,1',
                'cardinality2': '1,1',
                'description': '',
                'type': 'binary',  # binary, ternary, inheritance
                'attributes': []  # Pour les associations avec attributs
            }
            
            self.associations.append(self.current_association)
            self.log(f"Association ajoutée: {association_name}")
        else:
            self.log(f"❌ Impossible d'extraire l'association: {association_text}")
    
    def _parse_attribute(self, line: str):
        """Parse un attribut pour MCD (pas de clés)"""
        attribute_text = line[2:].strip()  # Enlever '- '
        self.log(f"Parsing attribut: '{attribute_text}'")
        
        if self.current_entity:
            # Parser l'attribut pour l'entité courante
            attribute_info = self._parse_attribute_info_improved(attribute_text)
            self.entities[self.current_entity]['attributes'].append(attribute_info)
            self.log(f"Attribut ajouté à {self.current_entity}: {attribute_info['name']}")
                
        elif self.current_association:
            # Parser l'attribut pour l'association courante
            attribute_info = self._parse_attribute_info_improved(attribute_text)
            if 'attributes' not in self.current_association:
                self.current_association['attributes'] = []
            self.current_association['attributes'].append(attribute_info)
            self.log(f"Attribut ajouté à l'association: {attribute_info['name']}")
        else:
            self.log(f"❌ Aucune entité/association courante pour l'attribut: {attribute_text}")
    
    def _parse_cardinality(self, line: str):
        """Parse une ligne de cardinalité avec support étendu"""
        if not self.current_association:
            self.log(f"❌ Pas d'association courante pour la cardinalité: {line}")
            return
            
        self.log(f"Parsing cardinalité: '{line}'")
        
        # CORRECTION FONDAMENTALE : Patterns simplifiés et robustes
        cardinality_patterns = [
            r'(\w+)\s*:\s*([0-9n]+,?[0-9n]*)',
            r'([0-9n]+,?[0-9n]*)\s*:\s*(\w+)',
            r'(\w+)\s*([0-9n]+,?[0-9n]*)',
            r'([0-9n]+,?[0-9n]*)\s*(\w+)',
        ]
        
        for pattern in cardinality_patterns:
            matches = re.findall(pattern, line)
            if matches:
                self.log(f"Matches trouvés: {matches}")
                for match in matches:
                    if len(match) == 2:
                        entity_or_card, card_or_entity = match
                        self.log(f"Match: {entity_or_card} / {card_or_entity}")
                        
                        # Déterminer si c'est une entité ou une cardinalité
                        if self._is_cardinality_improved(entity_or_card):
                            cardinality = entity_or_card
                            entity_name = card_or_entity
                            self.log(f"Cardinalité trouvée: {cardinality} pour {entity_name}")
                        elif self._is_cardinality_improved(card_or_entity):
                            cardinality = card_or_entity
                            entity_name = entity_or_card
                            self.log(f"Cardinalité trouvée: {cardinality} pour {entity_name}")
                        else:
                            self.log(f"❌ Cardinalité invalide: {entity_or_card} / {card_or_entity}")
                            continue
                            
                        # Assigner la cardinalité à l'entité appropriée
                        if entity_name == self.current_association['entity1']:
                            self.current_association['cardinality1'] = cardinality
                            self.log(f"Cardinalité 1 assignée: {cardinality}")
                        elif entity_name == self.current_association['entity2']:
                            self.current_association['cardinality2'] = cardinality
                            self.log(f"Cardinalité 2 assignée: {cardinality}")
                        else:
                            self.log(f"❌ Entité non reconnue: {entity_name}")
    
    def _parse_association_description(self, line: str):
        """Parse une description d'association"""
        if self.current_association:
            description = line.strip('*').strip()
            self.current_association['description'] = description
            self.log(f"Description d'association: {description}")
        else:
            self.log(f"❌ Pas d'association courante pour la description: {line}")
    
    def _parse_inheritance(self, line: str):
        """Parse une ligne d'héritage"""
        self.log(f"Parsing héritage: '{line}'")
        
        # Patterns pour détecter l'héritage
        inheritance_patterns = [
            r'(\w+)\s+hérite\s+de\s+(\w+)',
            r'(\w+)\s+extends\s+(\w+)',
            r'(\w+)\s+est\s+un\s+(\w+)',
            r'(\w+)\s+spécialise\s+(\w+)',
        ]
        
        for pattern in inheritance_patterns:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                child = self._clean_entity_name(match.group(1))
                parent = self._clean_entity_name(match.group(2))
                self.log(f"Héritage détecté: {child} -> {parent}")
                
                # Créer l'entité parent si elle n'existe pas
                if parent not in self.entities:
                    self.log(f"Création entité parent: {parent}")
                    self.entities[parent] = {
                        'name': parent,
                        'attributes': [],
                        'description': '',
                        'parent': None,
                        'children': []
                    }
                
                # Créer l'entité enfant si elle n'existe pas
                if child not in self.entities:
                    self.log(f"Création entité enfant: {child}")
                    self.entities[child] = {
                        'name': child,
                        'attributes': [],
                        'description': '',
                        'parent': parent,
                        'children': []
                    }
                
                # Établir la relation d'héritage
                self.entities[child]['parent'] = parent
                self.entities[parent]['children'].append(child)
                self.inheritance_hierarchy[child] = parent
                self.log(f"Héritage établi: {child} -> {parent}")
                break
    
    def _clean_entity_name(self, name: str) -> str:
        """Nettoie le nom d'une entité"""
        # Supprimer les caractères spéciaux et normaliser
        name = re.sub(r'[^\w\s]', '', name)
        name = name.strip().lower()
        # Capitaliser la première lettre
        result = name.capitalize()
        self.log(f"Nom nettoyé: '{name}' -> '{result}'")
        return result
    
    def _extract_entities_from_association(self, text: str) -> Optional[Tuple[str, str, str]]:
        """Extrait les entités et le nom de l'association avec support étendu"""
        self.log(f"Extraction d'association: '{text}'")
        
        # Patterns pour détecter les associations
        patterns = [
            r'(\w+)\s*<->\s*(\w+)\s*:\s*(\w+)',  # Entity1 <-> Entity2 : Association
            r'(\w+)\s*-\s*(\w+)\s*:\s*(\w+)',     # Entity1 - Entity2 : Association
            r'(\w+)\s*et\s*(\w+)\s*:\s*(\w+)',    # Entity1 et Entity2 : Association
            r'(\w+)\s*(\w+)\s*:\s*(\w+)',         # Entity1 Entity2 : Association
            r'(\w+)\s*<->\s*(\w+)\s*<->\s*(\w+)\s*:\s*(\w+)',  # Association ternaire
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                self.log(f"Pattern match: {pattern}")
                if len(match.groups()) == 3:
                    entity1 = self._clean_entity_name(match.group(1))
                    entity2 = self._clean_entity_name(match.group(2))
                    association_name = match.group(3).strip()
                    self.log(f"Association extraite: {entity1} <-> {entity2} : {association_name}")
                    return (entity1, entity2, association_name)
                elif len(match.groups()) == 4:
                    # Association ternaire
                    entity1 = self._clean_entity_name(match.group(1))
                    entity2 = self._clean_entity_name(match.group(2))
                    entity3 = self._clean_entity_name(match.group(3))
                    association_name = match.group(4).strip()
                    # Pour l'instant, on traite comme binaire
                    self.log(f"Association ternaire traitée comme binaire: {entity1} <-> {entity2} : {association_name}")
                    return (entity1, entity2, association_name)
        
        self.log(f"❌ Aucun pattern ne correspond: {text}")
        return None
    
    def _parse_attribute_info_improved(self, text: str) -> Dict:
        """Parse les informations d'un attribut pour MCD (pas de clés)"""
        self.log(f"Parsing attribut amélioré: '{text}'")
        
        attribute_info = {
            'name': '',
            'type': 'varchar',
            'is_nullable': True,
            'description': text,
            'size': None,
            'precision': None,
            'scale': None,
            'default_value': None,
            'constraints': []
        }
        
        # CORRECTION FONDAMENTALE : En MCD, il n'y a PAS de clés primaires/étrangères
        # Les clés apparaissent dans le MLD/MPD, pas dans le MCD
        # On ignore donc les marqueurs PK/FK pour le MCD
        
        # Extraire le nom de l'attribut
        name_match = re.search(r'(\w+)(?:\s*\([^)]+\))?', text)
        if name_match:
            attribute_info['name'] = name_match.group(1).lower()
            self.log(f"Nom d'attribut extrait: {attribute_info['name']}")
        
        # Détecter le type avec précision
        # Pattern pour type avec taille: varchar(50)
        size_pattern = r'\((\w+)\((\d+)\)\)'
        size_match = re.search(size_pattern, text)
        if size_match:
            attribute_info['type'] = size_match.group(1).lower()
            attribute_info['size'] = int(size_match.group(2))
            self.log(f"Type avec taille: {attribute_info['type']}({attribute_info['size']})")
        else:
            # Pattern pour type avec précision: decimal(10,2)
            precision_pattern = r'\((\w+)\((\d+),(\d+)\)\)'
            precision_match = re.search(precision_pattern, text)
            if precision_match:
                attribute_info['type'] = precision_match.group(1).lower()
                attribute_info['precision'] = int(precision_match.group(2))
                attribute_info['scale'] = int(precision_match.group(3))
                self.log(f"Type avec précision: {attribute_info['type']}({attribute_info['precision']},{attribute_info['scale']})")
            else:
                # Pattern pour type simple: varchar, integer, etc.
                simple_pattern = r'\((\w+)\)'
                simple_match = re.search(simple_pattern, text)
                if simple_match:
                    attribute_info['type'] = simple_match.group(1).lower()
                    self.log(f"Type simple: {attribute_info['type']}")
                else:
                    # Type par défaut
                    attribute_info['type'] = 'varchar'
                    self.log(f"Type par défaut: {attribute_info['type']}")
        
        # Détecter les contraintes
        if 'NOT NULL' in text.upper():
            attribute_info['is_nullable'] = False
            self.log("Contrainte NOT NULL détectée")
        
        if 'UNIQUE' in text.upper():
            attribute_info['constraints'].append('UNIQUE')
            self.log("Contrainte UNIQUE détectée")
        
        # Détecter les valeurs par défaut
        default_match = re.search(r"DEFAULT\s+['\"]?([^'\"]+)['\"]?", text, re.IGNORECASE)
        if default_match:
            attribute_info['default_value'] = f"'{default_match.group(1)}'"
            self.log(f"Valeur par défaut: {attribute_info['default_value']}")
        
        self.log(f"Attribut parsé: {attribute_info}")
        return attribute_info
    
    # Les 4 cardinalités du MCD Merise : (min, max) avec min ∈ {0,1}, max ∈ {1,n}.
    MCD_CARDINALITIES = ('0,1', '1,1', '0,n', '1,n')

    def _is_cardinality_improved(self, text: str) -> bool:
        """Vérifie si un texte représente une des 4 cardinalités MCD Merise."""
        self.log(f"Vérification cardinalité: '{text}'")
        t = text.strip().lower()
        if t in self.MCD_CARDINALITIES:
            self.log(f"✅ Cardinalité MCD valide: {text}")
            return True
        self.log(f"❌ Cardinalité invalide (MCD: 0,1 | 1,1 | 0,n | 1,n): {text}")
        return False

    def _contains_cardinality(self, text: str) -> bool:
        """Vérifie si une ligne contient une des 4 cardinalités MCD."""
        result = any(card in text for card in self.MCD_CARDINALITIES)
        self.log(f"Contient cardinalité '{text}': {result}")
        return result
    
    def _process_inheritance(self):
        """Traite l'héritage en copiant les attributs de la classe parent"""
        self.log("=== TRAITEMENT DE L'HÉRITAGE ===")
        
        for child, parent in self.inheritance_hierarchy.items():
            self.log(f"Traitement héritage: {child} -> {parent}")
            
            if parent in self.entities and child in self.entities:
                # Copier les attributs de la classe parent
                for attr in self.entities[parent]['attributes']:
                    # Vérifier si l'attribut n'existe pas déjà
                    if not any(existing_attr['name'] == attr['name'] for existing_attr in self.entities[child]['attributes']):
                        # Copier l'attribut en ajustant si nécessaire
                        inherited_attr = attr.copy()
                        inherited_attr['inherited_from'] = parent
                        self.entities[child]['attributes'].append(inherited_attr)
                        self.log(f"Attribut hérité: {attr['name']} de {parent} vers {child}")
                    else:
                        self.log(f"Attribut déjà présent: {attr['name']} dans {child}")
            else:
                self.log(f"❌ Entité manquante: parent={parent in self.entities}, child={child in self.entities}")
    
    def _process_foreign_keys(self):
        """Traite les clés étrangères - SUPPRIMÉ car pas de clés en MCD"""
        # CORRECTION FONDAMENTALE : En MCD, il n'y a pas de clés étrangères
        # Cette fonction est supprimée car les clés apparaissent dans le MLD/MPD
        self.log("Fonction _process_foreign_keys supprimée (pas de clés en MCD)")
        pass
    
    def _build_mcd_structure(self) -> Dict:
        """Construit la structure finale du MCD améliorée"""
        self.log("=== CONSTRUCTION STRUCTURE MCD ===")
        
        structure = {
            'entities': self.entities,
            'associations': self.associations,
            'inheritance': self.inheritance_hierarchy,
            'metadata': {
                'total_entities': len(self.entities),
                'total_associations': len(self.associations),
                'total_inheritance_relations': len(self.inheritance_hierarchy),
                'parser_version': '2.0',
                'precision_score': self._calculate_precision_score()
            }
        }
        
        self.log(f"Structure construite:")
        self.log(f"  - Entités: {len(self.entities)}")
        self.log(f"  - Associations: {len(self.associations)}")
        self.log(f"  - Héritage: {len(self.inheritance_hierarchy)}")
        self.log(f"  - Score: {structure['metadata']['precision_score']:.1f}%")
        
        return structure
    
    def _calculate_precision_score(self) -> float:
        """Calcule un score de précision basé sur les éléments MCD essentiels"""
        self.log("=== CALCUL SCORE DE PRÉCISION ===")
        
        score = 0.0
        total_checks = 0
        
        # CORRECTION FONDAMENTALE : Se concentrer sur les vrais éléments MCD
        # 1. Vérifier que chaque entité a au moins un attribut
        for entity_name, entity in self.entities.items():
            total_checks += 1
            has_attributes = len(entity['attributes']) > 0
            self.log(f"Entité '{entity_name}' a {len(entity['attributes'])} attributs: {has_attributes}")
            if has_attributes:
                score += 1
        
        # 2. BONUS : Vérifier qu'il y a plusieurs entités (MCD plus riche)
        if len(self.entities) > 1:
            total_checks += 1
            multiple_entities = len(self.entities) >= 2
            self.log(f"Plusieurs entités: {multiple_entities} ({len(self.entities)} entités)")
            if multiple_entities:
                score += 1
        
        # 2. Vérifier que les associations ont des cardinalités valides
        for association in self.associations:
            total_checks += 1
            card1_valid = self._is_cardinality_improved(association['cardinality1'])
            card2_valid = self._is_cardinality_improved(association['cardinality2'])
            self.log(f"Association '{association['name']}' cardinalités: {association['cardinality1']} ({card1_valid}), {association['cardinality2']} ({card2_valid})")
            if card1_valid and card2_valid:
                score += 1
        
        # 3. Vérifier que les entités référencées dans les associations existent
        for association in self.associations:
            total_checks += 1
            entity1_exists = association['entity1'] in self.entities
            entity2_exists = association['entity2'] in self.entities
            self.log(f"Association '{association['name']}' entités: {association['entity1']} ({entity1_exists}), {association['entity2']} ({entity2_exists})")
            if entity1_exists and entity2_exists:
                score += 1
        
        # 4. Vérifier que les associations sont binaires (règle MCD)
        for association in self.associations:
            total_checks += 1
            is_binary = association['entity1'] != association['entity2']
            self.log(f"Association '{association['name']}' binaire: {is_binary}")
            if is_binary:
                score += 1
        
        # 5. BONUS : Vérifier l'héritage (si présent)
        if self.inheritance_hierarchy:
            total_checks += 1
            inheritance_valid = len(self.inheritance_hierarchy) > 0
            self.log(f"Héritage valide: {inheritance_valid} ({len(self.inheritance_hierarchy)} relations)")
            if inheritance_valid:
                score += 1
        
        # 6. BONUS : Vérifier les associations (critère important)
        # Toujours vérifier les associations, même si aucune n'existe
        total_checks += 1
        associations_valid = len(self.associations) > 0
        self.log(f"Associations présentes: {associations_valid} ({len(self.associations)} associations)")
        if associations_valid:
            score += 1
        
        # Normaliser le score entre 0 et 100
        if total_checks > 0:
            normalized_score = (score / total_checks) * 100
            # Limiter à 100% maximum
            final_score = min(normalized_score, 100.0)
            self.log(f"Score final: {score}/{total_checks} = {final_score:.1f}%")
            return final_score
        
        self.log("Aucun check effectué, score: 0.0%")
        return 0.0
    
    def validate_mcd(self, mcd_structure: Dict) -> List[str]:
        """Valide la structure MCD et retourne les erreurs"""
        errors = []
        
        # Vérifications de base
        if not mcd_structure.get('entities'):
            errors.append("Aucune entité trouvée")
        
        if not mcd_structure.get('associations'):
            errors.append("Aucune association trouvée")
        
        # Vérifier que les associations sont binaires
        for association in mcd_structure.get('associations', []):
            if association['entity1'] == association['entity2']:
                errors.append(f"Association '{association['name']}' relie une entité à elle-même")
        
        return errors
    
    def export_to_json(self, mcd_structure: Dict, file_path: str) -> bool:
        """Exporte la structure MCD vers un fichier JSON"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(mcd_structure, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Erreur lors de l'export: {e}")
            return False
    
    def generate_markdown_template(self) -> str:
        """Génère un template markdown pour MCD"""
        template = """# Modèle Conceptuel de Données

## Entite1
- attribut1 (type) : description
- attribut2 (type) : description

## Entite2
- attribut1 (type) : description
- attribut2 (type) : description

## Entite1 <-> Entite2 : Association
**Description de l'association**
Entite1 : cardinalite1
Entite2 : cardinalite2
"""
        return template 