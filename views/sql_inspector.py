from typing import Dict, List, Set, Tuple
import sqlparse
from sqlparse.sql import Token, TokenList
from sqlparse.tokens import Keyword, Name, Punctuation, String, Number

class SQLInspector:
    """Inspecteur intelligent de schémas SQL"""
    
    def __init__(self):
        self.schema = {
            "tables": {},
            "foreign_keys": [],
            "constraints": [],
            "indexes": []
        }
        self.validation_rules = self._initialize_validation_rules()
        
    def analyze_sql(self, sql_script: str) -> Dict:
        """Analyse un script SQL et retourne sa structure."""
        # Parser le script SQL
        statements = sqlparse.parse(sql_script)
        
        for statement in statements:
            if statement.get_type() == "CREATE":
                self._analyze_create_statement(statement)
            elif statement.get_type() == "ALTER":
                self._analyze_alter_statement(statement)
                
        # Analyser les relations et dépendances
        self._analyze_relationships()
        
        return self.schema
        
    def validate_schema(self) -> List[Dict]:
        """Valide le schéma SQL et retourne les problèmes détectés."""
        issues = []
        
        # Appliquer toutes les règles de validation
        for rule in self.validation_rules:
            rule_issues = rule(self.schema)
            if rule_issues:
                issues.extend(rule_issues)
                
        return issues
        
    def suggest_optimizations(self) -> List[Dict]:
        """Suggère des optimisations pour le schéma."""
        suggestions = []
        
        # 1. Vérifier les index manquants
        suggestions.extend(self._suggest_missing_indexes())
        
        # 2. Vérifier les contraintes manquantes
        suggestions.extend(self._suggest_missing_constraints())
        
        # 3. Vérifier la normalisation
        suggestions.extend(self._suggest_normalization())
        
        # 4. Vérifier les types de données
        suggestions.extend(self._suggest_data_types())
        
        return suggestions
        
    def _initialize_validation_rules(self) -> List:
        """Initialise les règles de validation du schéma."""
        return [
            self._validate_primary_keys,
            self._validate_foreign_keys,
            self._validate_naming_conventions,
            self._validate_data_types,
            self._validate_null_constraints,
            self._validate_index_coverage,
            self._validate_circular_references,
            self._validate_table_relationships
        ]
        
    def _analyze_create_statement(self, statement: TokenList):
        """Analyse une instruction CREATE TABLE."""
        # Extraire le nom de la table
        table_name = self._extract_table_name(statement)
        
        # Initialiser la structure de la table
        table = {
            "name": table_name,
            "columns": [],
            "primary_key": None,
            "unique_constraints": [],
            "check_constraints": [],
            "indexes": []
        }
        
        # Analyser les colonnes et contraintes
        self._analyze_table_definition(statement, table)
        
        # Ajouter la table au schéma
        self.schema["tables"][table_name] = table
        
    def _analyze_alter_statement(self, statement: TokenList):
        """Analyse une instruction ALTER TABLE."""
        # Extraire le nom de la table et le type de modification
        table_name = self._extract_table_name(statement)
        alter_type = self._extract_alter_type(statement)
        
        if alter_type == "ADD CONSTRAINT":
            self._analyze_constraint(statement, table_name)
        elif alter_type == "ADD FOREIGN KEY":
            self._analyze_foreign_key(statement, table_name)
        elif alter_type == "ADD INDEX":
            self._analyze_index(statement, table_name)
            
    def _analyze_relationships(self):
        """Analyse les relations entre les tables."""
        # 1. Détecter les relations implicites
        self._detect_implicit_relationships()
        
        # 2. Analyser les cardinalités
        self._analyze_cardinalities()
        
        # 3. Détecter les hiérarchies
        self._detect_hierarchies()
        
    def _detect_implicit_relationships(self):
        """Détecte les relations implicites entre les tables."""
        for table_name, table in self.schema["tables"].items():
            for column in table["columns"]:
                if self._is_potential_foreign_key(column["name"]):
                    referenced_table = self._extract_referenced_table(column["name"])
                    if referenced_table in self.schema["tables"]:
                        self._add_implicit_foreign_key(table_name, column["name"], referenced_table)
                        
    def _analyze_cardinalities(self):
        """Analyse les cardinalités des relations."""
        for fk in self.schema["foreign_keys"]:
            # Déterminer la cardinalité côté source
            source_nullable = self._is_column_nullable(fk["table"], fk["columns"][0])
            source_cardinality = "0..1" if source_nullable else "1"
            
            # Déterminer la cardinalité côté cible
            target_unique = self._is_column_unique(fk["referenced_table"], fk["referenced_columns"][0])
            target_cardinality = "1" if target_unique else "*"
            
            # Mettre à jour la relation
            fk["cardinality"] = f"{source_cardinality}..{target_cardinality}"
            
    def _detect_hierarchies(self):
        """Détecte les hiérarchies dans le schéma."""
        hierarchies = []
        
        for table_name, table in self.schema["tables"].items():
            # Vérifier si la table a une clé étrangère vers elle-même
            self_references = self._find_self_references(table_name)
            if self_references:
                hierarchies.append({
                    "type": "recursive",
                    "table": table_name,
                    "column": self_references[0]
                })
                
            # Vérifier les relations d'héritage
            inheritance = self._find_inheritance_pattern(table_name)
            if inheritance:
                hierarchies.append(inheritance)
                
        self.schema["hierarchies"] = hierarchies
        
    def _validate_primary_keys(self, schema: Dict) -> List[Dict]:
        """Valide les clés primaires."""
        issues = []
        
        for table_name, table in schema["tables"].items():
            if not table["primary_key"]:
                issues.append({
                    "type": "missing_primary_key",
                    "severity": "error",
                    "table": table_name,
                    "message": f"La table {table_name} n'a pas de clé primaire"
                })
                
        return issues
        
    def _validate_foreign_keys(self, schema: Dict) -> List[Dict]:
        """Valide les clés étrangères."""
        issues = []
        
        for fk in schema["foreign_keys"]:
            # Vérifier que la table référencée existe
            if fk["referenced_table"] not in schema["tables"]:
                issues.append({
                    "type": "invalid_foreign_key",
                    "severity": "error",
                    "table": fk["table"],
                    "message": f"La clé étrangère {fk['name']} référence une table inexistante"
                })
                continue
                
            # Vérifier que les colonnes référencées existent
            referenced_table = schema["tables"][fk["referenced_table"]]
            for col in fk["referenced_columns"]:
                if not any(c["name"] == col for c in referenced_table["columns"]):
                    issues.append({
                        "type": "invalid_foreign_key",
                        "severity": "error",
                        "table": fk["table"],
                        "message": f"La colonne {col} référencée n'existe pas dans {fk['referenced_table']}"
                    })
                    
        return issues
        
    def _validate_naming_conventions(self, schema: Dict) -> List[Dict]:
        """Valide les conventions de nommage."""
        issues = []
        
        # Règles de nommage
        naming_rules = {
            "table": r"^[a-z][a-z0-9_]*$",
            "column": r"^[a-z][a-z0-9_]*$",
            "primary_key": r"^id$|^[a-z]+_id$",
            "foreign_key": r"^[a-z]+_id$",
            "index": r"^idx_[a-z0-9_]+$"
        }
        
        for table_name, table in schema["tables"].items():
            # Vérifier le nom de la table
            if not re.match(naming_rules["table"], table_name):
                issues.append({
                    "type": "naming_convention",
                    "severity": "warning",
                    "table": table_name,
                    "message": "Le nom de la table ne respecte pas la convention"
                })
                
            # Vérifier les noms de colonnes
            for column in table["columns"]:
                if not re.match(naming_rules["column"], column["name"]):
                    issues.append({
                        "type": "naming_convention",
                        "severity": "warning",
                        "table": table_name,
                        "column": column["name"],
                        "message": "Le nom de la colonne ne respecte pas la convention"
                    })
                    
        return issues
        
    def _validate_data_types(self, schema: Dict) -> List[Dict]:
        """Valide les types de données."""
        issues = []
        
        # Règles de validation des types
        type_rules = {
            "id": ["integer", "bigint"],
            "date": ["date", "timestamp"],
            "price": ["decimal", "numeric"],
            "quantity": ["integer", "decimal"],
            "status": ["varchar", "char"],
            "email": ["varchar"],
            "phone": ["varchar"],
            "url": ["varchar", "text"]
        }
        
        for table_name, table in schema["tables"].items():
            for column in table["columns"]:
                # Vérifier les types selon le nom de la colonne
                for pattern, valid_types in type_rules.items():
                    if pattern in column["name"].lower():
                        if column["type"].lower() not in valid_types:
                            issues.append({
                                "type": "invalid_data_type",
                                "severity": "warning",
                                "table": table_name,
                                "column": column["name"],
                                "message": f"Le type {column['type']} peut ne pas être optimal pour {column['name']}"
                            })
                            
        return issues
        
    def _validate_null_constraints(self, schema: Dict) -> List[Dict]:
        """Valide les contraintes NULL/NOT NULL."""
        issues = []
        
        for table_name, table in schema["tables"].items():
            for column in table["columns"]:
                # Les clés primaires doivent être NOT NULL
                if column["name"] in table["primary_key"] and column.get("nullable"):
                    issues.append({
                        "type": "invalid_null_constraint",
                        "severity": "error",
                        "table": table_name,
                        "column": column["name"],
                        "message": "Une clé primaire ne peut pas être NULL"
                    })
                    
                # Les clés étrangères devraient généralement être NOT NULL
                if self._is_foreign_key(table_name, column["name"]) and column.get("nullable"):
                    issues.append({
                        "type": "nullable_foreign_key",
                        "severity": "warning",
                        "table": table_name,
                        "column": column["name"],
                        "message": "Considérer NOT NULL pour la clé étrangère"
                    })
                    
        return issues
        
    def _validate_index_coverage(self, schema: Dict) -> List[Dict]:
        """Valide la couverture des index."""
        issues = []
        
        for table_name, table in schema["tables"].items():
            # Vérifier les index sur les clés étrangères
            for fk in schema["foreign_keys"]:
                if fk["table"] == table_name:
                    if not self._has_index_for_columns(table, fk["columns"]):
                        issues.append({
                            "type": "missing_index",
                            "severity": "warning",
                            "table": table_name,
                            "columns": fk["columns"],
                            "message": "Index manquant sur la clé étrangère"
                        })
                        
            # Vérifier les index sur les colonnes fréquemment utilisées
            for column in table["columns"]:
                if self._is_frequently_queried_column(column["name"]) and \
                   not self._has_index_for_columns(table, [column["name"]]):
                    issues.append({
                        "type": "missing_index",
                        "severity": "suggestion",
                        "table": table_name,
                        "columns": [column["name"]],
                        "message": "Considérer un index pour cette colonne fréquemment utilisée"
                    })
                    
        return issues
        
    def _validate_circular_references(self, schema: Dict) -> List[Dict]:
        """Valide les références circulaires."""
        issues = []
        
        # Construire un graphe de dépendances
        dependencies = defaultdict(list)
        for fk in schema["foreign_keys"]:
            dependencies[fk["table"]].append(fk["referenced_table"])
            
        # Détecter les cycles
        visited = set()
        path = []
        
        def detect_cycle(table):
            if table in path:
                cycle = path[path.index(table):] + [table]
                issues.append({
                    "type": "circular_reference",
                    "severity": "warning",
                    "tables": cycle,
                    "message": f"Référence circulaire détectée: {' -> '.join(cycle)}"
                })
                return
                
            if table in visited:
                return
                
            visited.add(table)
            path.append(table)
            
            for dep in dependencies[table]:
                detect_cycle(dep)
                
            path.pop()
            
        for table in schema["tables"]:
            if table not in visited:
                detect_cycle(table)
                
        return issues
        
    def _validate_table_relationships(self, schema: Dict) -> List[Dict]:
        """Valide les relations entre les tables."""
        issues = []
        
        # Détecter les tables isolées
        for table_name in schema["tables"]:
            if not self._has_relationships(table_name):
                issues.append({
                    "type": "isolated_table",
                    "severity": "warning",
                    "table": table_name,
                    "message": f"La table {table_name} n'a aucune relation avec d'autres tables"
                })
                
        # Vérifier les relations many-to-many
        for relation in self._find_many_to_many_relations():
            if not self._has_junction_table(relation):
                issues.append({
                    "type": "missing_junction_table",
                    "severity": "suggestion",
                    "tables": [relation["table1"], relation["table2"]],
                    "message": "Une table de liaison pourrait être nécessaire"
                })
                
        return issues
        
    def _suggest_missing_indexes(self) -> List[Dict]:
        """Suggère des index manquants."""
        suggestions = []
        
        for table_name, table in self.schema["tables"].items():
            # 1. Colonnes fréquemment filtrées
            filter_columns = self._identify_filter_columns(table)
            for column in filter_columns:
                if not self._has_index_for_columns(table, [column]):
                    suggestions.append({
                        "type": "missing_index",
                        "table": table_name,
                        "columns": [column],
                        "reason": "Colonne fréquemment utilisée dans les filtres"
                    })
                    
            # 2. Colonnes de tri
            sort_columns = self._identify_sort_columns(table)
            for column in sort_columns:
                if not self._has_index_for_columns(table, [column]):
                    suggestions.append({
                        "type": "missing_index",
                        "table": table_name,
                        "columns": [column],
                        "reason": "Colonne fréquemment utilisée pour le tri"
                    })
                    
            # 3. Index composites pour les requêtes courantes
            composite_candidates = self._identify_composite_index_candidates(table)
            for columns in composite_candidates:
                if not self._has_index_for_columns(table, columns):
                    suggestions.append({
                        "type": "missing_composite_index",
                        "table": table_name,
                        "columns": columns,
                        "reason": "Index composite recommandé pour les requêtes courantes"
                    })
                    
        return suggestions
        
    def _suggest_missing_constraints(self) -> List[Dict]:
        """Suggère des contraintes manquantes."""
        suggestions = []
        
        for table_name, table in self.schema["tables"].items():
            # 1. Contraintes d'unicité
            unique_candidates = self._identify_unique_candidates(table)
            for column in unique_candidates:
                suggestions.append({
                    "type": "missing_unique_constraint",
                    "table": table_name,
                    "column": column,
                    "reason": "La colonne pourrait nécessiter une contrainte UNIQUE"
                })
                
            # 2. Contraintes CHECK
            check_candidates = self._identify_check_candidates(table)
            for check in check_candidates:
                suggestions.append({
                    "type": "missing_check_constraint",
                    "table": table_name,
                    "column": check["column"],
                    "condition": check["condition"],
                    "reason": "Une contrainte CHECK pourrait être utile"
                })
                
            # 3. Contraintes NOT NULL
            nullable_candidates = self._identify_not_null_candidates(table)
            for column in nullable_candidates:
                suggestions.append({
                    "type": "missing_not_null",
                    "table": table_name,
                    "column": column,
                    "reason": "La colonne devrait probablement être NOT NULL"
                })
                
        return suggestions
        
    def _suggest_normalization(self) -> List[Dict]:
        """Suggère des améliorations de normalisation."""
        suggestions = []
        
        # 1. Détecter les violations de la 1NF
        first_normal_form = self._check_first_normal_form()
        suggestions.extend(first_normal_form)
        
        # 2. Détecter les violations de la 2NF
        second_normal_form = self._check_second_normal_form()
        suggestions.extend(second_normal_form)
        
        # 3. Détecter les violations de la 3NF
        third_normal_form = self._check_third_normal_form()
        suggestions.extend(third_normal_form)
        
        return suggestions
        
    def _suggest_data_types(self) -> List[Dict]:
        """Suggère des optimisations de types de données."""
        suggestions = []
        
        for table_name, table in self.schema["tables"].items():
            for column in table["columns"]:
                # 1. Optimisation des VARCHAR
                if column["type"].startswith("VARCHAR"):
                    suggestions.extend(self._optimize_varchar(table_name, column))
                    
                # 2. Optimisation des numériques
                elif column["type"] in ["INTEGER", "DECIMAL", "NUMERIC"]:
                    suggestions.extend(self._optimize_numeric(table_name, column))
                    
                # 3. Optimisation des dates
                elif column["type"] in ["TIMESTAMP", "DATETIME"]:
                    suggestions.extend(self._optimize_datetime(table_name, column))
                    
        return suggestions
        
    def _check_first_normal_form(self) -> List[Dict]:
        """Vérifie la première forme normale."""
        violations = []
        
        for table_name, table in self.schema["tables"].items():
            # Détecter les colonnes potentiellement multivaluées
            for column in table["columns"]:
                if self._is_potentially_multivalued(column):
                    violations.append({
                        "type": "1nf_violation",
                        "table": table_name,
                        "column": column["name"],
                        "suggestion": "Créer une table séparée pour les valeurs multiples"
                    })
                    
        return violations
        
    def _check_second_normal_form(self) -> List[Dict]:
        """Vérifie la deuxième forme normale."""
        violations = []
        
        for table_name, table in self.schema["tables"].items():
            # Vérifier les dépendances partielles
            if len(table["primary_key"]) > 1:  # Clé primaire composite
                non_key_attrs = [col["name"] for col in table["columns"]
                               if col["name"] not in table["primary_key"]]
                
                for attr in non_key_attrs:
                    if self._has_partial_dependency(table, attr):
                        violations.append({
                            "type": "2nf_violation",
                            "table": table_name,
                            "column": attr,
                            "suggestion": "Déplacer l'attribut dans une nouvelle table"
                        })
                        
        return violations
        
    def _check_third_normal_form(self) -> List[Dict]:
        """Vérifie la troisième forme normale."""
        violations = []
        
        for table_name, table in self.schema["tables"].items():
            # Vérifier les dépendances transitives
            transitive_deps = self._find_transitive_dependencies(table)
            
            for dep in transitive_deps:
                violations.append({
                    "type": "3nf_violation",
                    "table": table_name,
                    "columns": dep["columns"],
                    "suggestion": "Créer une nouvelle table pour ces attributs"
                })
                
        return violations
        
    def _optimize_varchar(self, table_name: str, column: Dict) -> List[Dict]:
        """Suggère des optimisations pour les colonnes VARCHAR."""
        suggestions = []
        
        # Vérifier si un type plus approprié existe
        if any(pattern in column["name"].lower() for pattern in ["email", "url"]):
            suggestions.append({
                "type": "data_type_optimization",
                "table": table_name,
                "column": column["name"],
                "current_type": column["type"],
                "suggested_type": "VARCHAR(320)" if "email" in column["name"].lower() else "TEXT",
                "reason": "Taille optimisée pour le type de données"
            })
            
        # Vérifier si la taille peut être optimisée
        if "(" in column["type"]:
            size = int(column["type"].split("(")[1].split(")")[0])
            if size > 255:
                suggestions.append({
                    "type": "data_type_optimization",
                    "table": table_name,
                    "column": column["name"],
                    "current_type": column["type"],
                    "suggested_type": "TEXT",
                    "reason": "Utiliser TEXT pour les chaînes longues"
                })
                
        return suggestions
        
    def _optimize_numeric(self, table_name: str, column: Dict) -> List[Dict]:
        """Suggère des optimisations pour les colonnes numériques."""
        suggestions = []
        
        # Optimiser les entiers
        if column["type"] == "INTEGER":
            if "id" in column["name"].lower():
                suggestions.append({
                    "type": "data_type_optimization",
                    "table": table_name,
                    "column": column["name"],
                    "current_type": "INTEGER",
                    "suggested_type": "BIGINT",
                    "reason": "Utiliser BIGINT pour les identifiants"
                })
                
        # Optimiser les décimaux
        elif column["type"].startswith("DECIMAL"):
            if "price" in column["name"].lower():
                suggestions.append({
                    "type": "data_type_optimization",
                    "table": table_name,
                    "column": column["name"],
                    "current_type": column["type"],
                    "suggested_type": "DECIMAL(10,2)",
                    "reason": "Précision optimale pour les prix"
                })
                
        return suggestions
        
    def _optimize_datetime(self, table_name: str, column: Dict) -> List[Dict]:
        """Suggère des optimisations pour les colonnes de date/heure."""
        suggestions = []
        
        # Vérifier si TIMESTAMP est nécessaire
        if column["type"] == "TIMESTAMP" and \
           not any(pattern in column["name"].lower() 
                  for pattern in ["created", "updated", "modified"]):
            suggestions.append({
                "type": "data_type_optimization",
                "table": table_name,
                "column": column["name"],
                "current_type": "TIMESTAMP",
                "suggested_type": "DATE",
                "reason": "DATE pourrait suffire si l'heure n'est pas nécessaire"
            })
            
        return suggestions 