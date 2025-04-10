from PyQt5.QtCore import QObject, pyqtSignal
from typing import List, Dict, Any
from ..models.entity import Entity
from ..models.association import Association
from ..models.attribute import Attribute
from .error_handler import ErrorHandler

class ModelValidator(QObject):
    """Validateur de modèles et générateur de MLD"""
    
    # Signaux
    validation_completed = pyqtSignal(bool, str)  # succès, message
    mld_generated = pyqtSignal(str)  # script SQL
    documentation_generated = pyqtSignal(str)  # documentation
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.error_handler = ErrorHandler(self)
        
    def validate_model(self, entities: List[Entity], associations: List[Association]) -> bool:
        """Valide le modèle complet"""
        try:
            # Vérification des entités
            if not self._validate_entities(entities):
                return False
                
            # Vérification des relations
            if not self._validate_relations(entities, associations):
                return False
                
            # Vérification des cycles
            if not self._check_cycles(entities, associations):
                return False
                
            # Vérification des clés
            if not self._validate_keys(entities):
                return False
                
            self.validation_completed.emit(True, "Modèle valide")
            return True
            
        except Exception as e:
            self.error_handler.handle_error(e, "Erreur lors de la validation du modèle")
            self.validation_completed.emit(False, str(e))
            return False
            
    def _validate_entities(self, entities: List[Entity]) -> bool:
        """Valide les entités"""
        try:
            # Vérification des noms uniques
            names = set()
            for entity in entities:
                if entity.name in names:
                    self.error_handler.handle_warning(
                        f"Nom d'entité en double : {entity.name}"
                    )
                    return False
                names.add(entity.name)
                
            # Vérification des attributs
            for entity in entities:
                if not self._validate_attributes(entity.attributes):
                    return False
                    
            return True
            
        except Exception as e:
            self.error_handler.handle_error(e, "Erreur lors de la validation des entités")
            return False
            
    def _validate_attributes(self, attributes: List[Attribute]) -> bool:
        """Valide les attributs d'une entité"""
        try:
            # Vérification des noms uniques
            names = set()
            for attr in attributes:
                if attr.name in names:
                    self.error_handler.handle_warning(
                        f"Nom d'attribut en double : {attr.name}"
                    )
                    return False
                names.add(attr.name)
                
            # Vérification des types de données
            for attr in attributes:
                if not self._validate_data_type(attr.data_type):
                    return False
                    
            return True
            
        except Exception as e:
            self.error_handler.handle_error(e, "Erreur lors de la validation des attributs")
            return False
            
    def _validate_data_type(self, data_type: str) -> bool:
        """Valide un type de données"""
        valid_types = {
            "INTEGER", "VARCHAR", "TEXT", "DECIMAL", "DATE", "TIMESTAMP",
            "BOOLEAN", "FLOAT", "DOUBLE", "CHAR", "BLOB", "CLOB"
        }
        return data_type.upper() in valid_types
        
    def _validate_relations(self, entities: List[Entity], associations: List[Association]) -> bool:
        """Valide les relations"""
        try:
            for assoc in associations:
                # Vérification des entités liées
                if not (assoc.source in entities and assoc.target in entities):
                    self.error_handler.handle_warning(
                        "Relation invalide : entité source ou cible manquante"
                    )
                    return False
                    
                # Vérification des cardinalités
                if not self._validate_cardinality(assoc.cardinality):
                    return False
                    
            return True
            
        except Exception as e:
            self.error_handler.handle_error(e, "Erreur lors de la validation des relations")
            return False
            
    def _validate_cardinality(self, cardinality: str) -> bool:
        """Valide une cardinalité"""
        valid_cardinalities = {"1,1", "1,n", "n,1", "n,n"}
        return cardinality in valid_cardinalities
        
    def _check_cycles(self, entities: List[Entity], associations: List[Association]) -> bool:
        """Vérifie l'absence de cycles dans les relations"""
        try:
            # Construction du graphe
            graph = {entity: [] for entity in entities}
            for assoc in associations:
                graph[assoc.source].append(assoc.target)
                graph[assoc.target].append(assoc.source)
                
            # Détection des cycles
            visited = set()
            path = set()
            
            def has_cycle(node: Entity) -> bool:
                visited.add(node)
                path.add(node)
                for neighbor in graph[node]:
                    if neighbor not in visited:
                        if has_cycle(neighbor):
                            return True
                    elif neighbor in path:
                        return True
                path.remove(node)
                return False
                
            # Vérification pour chaque composante connexe
            for entity in entities:
                if entity not in visited:
                    if has_cycle(entity):
                        self.error_handler.handle_warning(
                            "Cycle détecté dans les relations"
                        )
                        return False
                        
            return True
            
        except Exception as e:
            self.error_handler.handle_error(e, "Erreur lors de la vérification des cycles")
            return False
            
    def _validate_keys(self, entities: List[Entity]) -> bool:
        """Valide les clés primaires et étrangères"""
        try:
            for entity in entities:
                # Vérification de la clé primaire
                has_primary_key = False
                for attr in entity.attributes:
                    if attr.is_primary_key:
                        has_primary_key = True
                        break
                        
                if not has_primary_key:
                    self.error_handler.handle_warning(
                        f"Entité {entity.name} sans clé primaire"
                    )
                    return False
                    
            return True
            
        except Exception as e:
            self.error_handler.handle_error(e, "Erreur lors de la validation des clés")
            return False
            
    def generate_mld(self, entities: List[Entity], associations: List[Association]) -> str:
        """Génère le script SQL pour le MLD"""
        try:
            sql_script = []
            
            # Génération des tables
            for entity in entities:
                table_sql = self._generate_table_sql(entity)
                sql_script.append(table_sql)
                
            # Génération des clés étrangères
            for assoc in associations:
                fk_sql = self._generate_foreign_key_sql(assoc)
                if fk_sql:
                    sql_script.append(fk_sql)
                    
            script = "\n\n".join(sql_script)
            self.mld_generated.emit(script)
            return script
            
        except Exception as e:
            self.error_handler.handle_error(e, "Erreur lors de la génération du MLD")
            return ""
            
    def _generate_table_sql(self, entity: Entity) -> str:
        """Génère le SQL pour une table"""
        columns = []
        for attr in entity.attributes:
            col_def = f"{attr.name} {attr.data_type}"
            if attr.is_primary_key:
                col_def += " PRIMARY KEY"
            if attr.is_unique:
                col_def += " UNIQUE"
            if attr.is_not_null:
                col_def += " NOT NULL"
            columns.append(col_def)
            
        return f"CREATE TABLE {entity.name} (\n    " + ",\n    ".join(columns) + "\n);"
        
    def _generate_foreign_key_sql(self, association: Association) -> str:
        """Génère le SQL pour une clé étrangère"""
        if not association.foreign_key:
            return ""
            
        return f"""
ALTER TABLE {association.target.name}
ADD CONSTRAINT fk_{association.source.name}_{association.target.name}
FOREIGN KEY ({association.foreign_key})
REFERENCES {association.source.name}({association.primary_key});
"""
        
    def generate_documentation(self, entities: List[Entity], associations: List[Association]) -> str:
        """Génère la documentation du modèle"""
        try:
            doc = []
            
            # Documentation des entités
            doc.append("# Documentation du Modèle Conceptuel de Données\n")
            
            doc.append("## Entités\n")
            for entity in entities:
                doc.append(f"### {entity.name}\n")
                doc.append("#### Attributs :")
                for attr in entity.attributes:
                    doc.append(f"- {attr.name} ({attr.data_type})")
                    if attr.is_primary_key:
                        doc.append("  - Clé primaire")
                    if attr.is_unique:
                        doc.append("  - Unique")
                    if attr.is_not_null:
                        doc.append("  - Non nul")
                        
            # Documentation des relations
            doc.append("\n## Relations\n")
            for assoc in associations:
                doc.append(f"### {assoc.source.name} - {assoc.target.name}")
                doc.append(f"- Cardinalité : {assoc.cardinality}")
                if assoc.foreign_key:
                    doc.append(f"- Clé étrangère : {assoc.foreign_key}")
                    
            documentation = "\n".join(doc)
            self.documentation_generated.emit(documentation)
            return documentation
            
        except Exception as e:
            self.error_handler.handle_error(e, "Erreur lors de la génération de la documentation")
            return "" 