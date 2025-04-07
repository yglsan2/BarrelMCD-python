from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QPushButton, QLabel, QComboBox, QHBoxLayout, QCheckBox
from views.error_handler import ErrorHandler
import re
from enum import Enum
from typing import List, Dict, Optional
from difflib import SequenceMatcher
import unicodedata

class QueryType(Enum):
    """Types de requêtes SQL supportés"""
    SELECT = "SELECT"
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    CREATE = "CREATE"
    ALTER = "ALTER"
    DROP = "DROP"
    PROCEDURE = "PROCEDURE"
    FUNCTION = "FUNCTION"
    TRIGGER = "TRIGGER"
    VIEW = "VIEW"
    CTE = "CTE"  # Common Table Expression
    RECURSIVE = "RECURSIVE"  # Requête récursive
    ANALYTIC = "ANALYTIC"  # Fonctions analytiques
    STATISTIC = "STATISTIC"  # Analyses statistiques
    MATERIALIZED = "MATERIALIZED"  # Vues matérialisées
    TRANSACTION = "TRANSACTION"  # Transactions
    CURSOR = "CURSOR"  # Curseurs
    EXCEPTION = "EXCEPTION"  # Gestion des exceptions
    PERFORMANCE = "PERFORMANCE"  # Validation des performances
    COMPLEX_TRIGGER = "COMPLEX_TRIGGER"  # Triggers complexes
    NESTED_TRIGGER = "NESTED_TRIGGER"  # Triggers imbriqués
    TRIGGER_CURSOR = "TRIGGER_CURSOR"  # Curseurs dans les triggers
    TRIGGER_CONSTRAINT = "TRIGGER_CONSTRAINT"  # Contraintes dans les triggers

class QueryError(Exception):
    """Classe de base pour les erreurs de requête"""
    def __init__(self, message: str, query_type: QueryType, context: dict = None):
        super().__init__(message)
        self.query_type = query_type
        self.context = context or {}

class SyntaxError(QueryError):
    """Erreur de syntaxe dans la description"""
    pass

class SemanticError(QueryError):
    """Erreur sémantique dans la description"""
    pass

class ValidationError(QueryError):
    """Erreur de validation des paramètres"""
    pass

class QueryInspector(QObject):
    """Classe pour analyser et générer des requêtes SQL à partir d'une description textuelle."""
    
    # Signaux
    query_generated = pyqtSignal(str)  # Émet la requête SQL générée
    error_occurred = pyqtSignal(str)  # Émet les messages d'erreur
    suggestion_made = pyqtSignal(str)  # Émet des suggestions de correction
    
    def __init__(self):
        super().__init__()
        self.error_handler = ErrorHandler()
        self._load_query_patterns()
        self._load_procedure_patterns()
        self._load_correction_rules()
        self._load_error_patterns()
        self._load_performance_rules()
        self._load_constraint_patterns()
        self._load_trigger_patterns()
        self._load_nested_trigger_patterns()
        self._load_trigger_cursor_patterns()
        self._load_trigger_constraint_patterns()
        
    def _load_query_patterns(self):
        """Charge les patterns de reconnaissance pour différents types de requêtes"""
        self.query_patterns = {
            QueryType.SELECT: {
                "basic": r"afficher|montrer|sélectionner|sélectionne|sélectionnez|sélectionnons|sélectionnent|sélectionné|sélectionnée|sélectionnés|sélectionnées",
                "join": r"joindre|joindre avec|relier|relier avec|associer|associer avec|combiner|combiner avec",
                "where": r"où|dans lequel|dans laquelle|dans lesquels|dans lesquelles|si|quand",
                "group_by": r"grouper par|regrouper par|grouper selon|regrouper selon",
                "having": r"ayant|avec|dont",
                "order_by": r"trier par|ordonner par|classer par|trier selon|ordonner selon|classer selon",
                "limit": r"limiter à|limiter par|limiter de|limiter en",
                "distinct": r"unique|distinct|différent|différente|différents|différentes"
            },
            QueryType.INSERT: {
                "basic": r"insérer|ajouter|créer|créer un|créer une|créer des",
                "values": r"avec les valeurs|avec les données|avec|contenant|contenant les"
            },
            QueryType.UPDATE: {
                "basic": r"modifier|mettre à jour|changer|changer la|changer le|changer les",
                "set": r"en|par|à|avec",
                "where": r"où|dans lequel|dans laquelle|dans lesquels|dans lesquelles|si|quand"
            },
            QueryType.DELETE: {
                "basic": r"supprimer|effacer|enlever|retirer|ôter",
                "where": r"où|dans lequel|dans laquelle|dans lesquels|dans lesquelles|si|quand",
                "cascade": r"cascade|en cascade|et tout ce qui est lié|et tout ce qui est associé|et tout ce qui est relié"
            },
            QueryType.CTE: {
                "basic": r"avec|en utilisant|en définissant|en créant",
                "recursive": r"récursif|récursive|récursivement|récurrence",
                "hierarchie": r"hiérarchie|arbre|structure|niveau|parent|enfant|manager|subordonné",
                "statistiques": r"statistiques|moyenne|écart-type|variance|médiane|quartile|percentile"
            },
            QueryType.ANALYTIC: {
                "window": r"fenêtre|window|partition|rang|rank|row_number|dense_rank",
                "lag_lead": r"précédent|suivant|lag|lead|décalage",
                "aggregation": r"somme|total|moyenne|moyen|compte|nombre|min|max"
            }
        }
        
    def _load_procedure_patterns(self):
        """Charge les patterns de reconnaissance pour les procédures stockées"""
        self.procedure_patterns = {
            "basic": r"procédure|procédure stockée|fonction|routine|programme|script",
            "parameters": r"paramètre|paramètres|argument|arguments|entrée|entrées|sortie|sorties",
            "return": r"retourner|retourne|retourné|retournée|retournés|retournées",
            "transaction": r"transaction|transactions|commit|rollback|sauvegarder|annuler",
            "error": r"erreur|exception|gérer|gestion|traitement|traiter",
            "loop": r"boucle|répéter|itérer|parcourir|parcours|tant que|pour chaque",
            "condition": r"si|alors|sinon|fin si|cas|selon|fin cas"
        }
        
    def _load_correction_rules(self):
        """Charge les règles de correction pour la gestion des erreurs de frappe"""
        self.correction_rules = {
            "accents": {
                "a": ["à", "â", "ä"],
                "e": ["é", "è", "ê", "ë"],
                "i": ["î", "ï"],
                "o": ["ô", "ö"],
                "u": ["ù", "û", "ü"],
                "c": ["ç"]
            },
            "common_typos": {
                "table": ["tabel", "tabl", "tble"],
                "select": ["slect", "selet", "selct"],
                "where": ["whre", "wher", "were"],
                "join": ["joi", "jion", "joinn"],
                "group": ["grup", "grou", "grop"],
                "order": ["ordr", "oder", "ord"],
                "having": ["havng", "havin", "hav"],
                "procedure": ["proc", "procedur", "procedre"],
                "function": ["funct", "functon", "functin"],
                "trigger": ["triger", "trigr", "trig"]
            }
        }
        
    def _load_error_patterns(self):
        """Charge les patterns pour la détection des erreurs"""
        self.error_patterns = {
            "syntax": {
                "missing_table": r"table manquante|table non spécifiée|table non définie",
                "missing_column": r"colonne manquante|colonne non spécifiée|colonne non définie",
                "invalid_join": r"jointure invalide|jointure incorrecte|jointure non valide",
                "invalid_condition": r"condition invalide|condition incorrecte|condition non valide"
            },
            "semantic": {
                "ambiguous_column": r"colonne ambiguë|colonne non unique|colonne dupliquée",
                "invalid_type": r"type invalide|type incorrect|type non valide",
                "missing_parameter": r"paramètre manquant|paramètre non spécifié|paramètre non défini"
            },
            "validation": {
                "invalid_value": r"valeur invalide|valeur incorrecte|valeur non valide",
                "out_of_range": r"hors limites|hors plage|valeur hors limites",
                "constraint_violation": r"contrainte violée|contrainte non respectée|contrainte invalide"
            }
        }
        
    def _load_performance_rules(self):
        """Charge les règles de validation des performances"""
        self.performance_rules = {
            "select": {
                "basic": r"SELECT\s+\*\s+FROM",
                "join": r"JOIN\s+\*\s+ON",
                "where": r"WHERE\s+\*\s+FROM",
                "group_by": r"GROUP BY\s+\*\s+FROM",
                "having": r"HAVING\s+\*\s+FROM",
                "order_by": r"ORDER BY\s+\*\s+FROM",
                "limit": r"LIMIT\s+\*\s+FROM"
            },
            "insert": {
                "basic": r"INSERT INTO\s+\*\s+VALUES",
                "values": r"VALUES\s+\*\s+",
                "select": r"INSERT INTO\s+\*\s+SELECT"
            },
            "update": {
                "basic": r"UPDATE\s+\*\s+SET",
                "set": r"SET\s+\*\s+=",
                "where": r"WHERE\s+\*\s+="
            },
            "delete": {
                "basic": r"DELETE FROM\s+\*",
                "where": r"WHERE\s+\*"
            },
            "cte": {
                "basic": r"WITH\s+\*\s+AS",
                "recursive": r"RECURSIVE\s+\*\s+AS",
                "hierarchie": r"WITH RECURSIVE\s+\*\s+AS",
                "statistiques": r"WITH statistiques AS"
            },
            "analytic": {
                "basic": r"SELECT\s+\*\s+FROM",
                "window": r"SELECT\s+\*\s+FROM",
                "lag_lead": r"SELECT\s+\*\s+FROM",
                "aggregation": r"SELECT\s+\*\s+FROM"
            }
        }
        
    def _load_constraint_patterns(self):
        """Charge les patterns pour la gestion des contraintes"""
        self.constraint_patterns = {
            "foreign_key": {
                "basic": r"clé étrangère|référence|lié à|associé à|relatif à",
                "cascade": r"en cascade|cascade|propagation|propager",
                "set_null": r"mettre à null|mettre à vide|effacer",
                "restrict": r"restreindre|empêcher|bloquer"
            },
            "transaction": {
                "begin": r"début|commencer|démarrer|initier",
                "commit": r"valider|confirmer|sauvegarder|appliquer",
                "rollback": r"annuler|annulation|annuler les changements|revenir en arrière",
                "savepoint": r"point de sauvegarde|sauvegarder à|marquer|point de retour"
            }
        }
        
    def _load_trigger_patterns(self):
        """Charge les patterns pour la gestion des triggers"""
        self.trigger_patterns = {
            "basic": r"trigger|déclencheur|déclenche|déclencher|déclenché|déclenchée|déclenchés|déclenchées",
            "timing": {
                "before": r"avant|préalablement|préalable|préalablement à",
                "after": r"après|postérieur|postérieurement|postérieur à",
                "instead": r"au lieu de|remplacer|substituer|à la place de"
            },
            "event": {
                "insert": r"insertion|insérer|ajouter|créer",
                "update": r"mise à jour|modifier|changer|mettre à jour",
                "delete": r"suppression|supprimer|effacer|enlever",
                "truncate": r"tronquer|vider|effacer tout|supprimer tout"
            },
            "condition": {
                "when": r"quand|si|lorsque|lors de",
                "for_each": r"pour chaque|pour chaque ligne|pour chaque enregistrement|pour chaque élément"
            },
            "action": {
                "execute": r"exécuter|effectuer|réaliser|faire",
                "raise": r"lever|générer|provoquer|déclencher",
                "log": r"journaliser|enregistrer|sauvegarder|noter",
                "audit": r"auditer|traquer|suivre|monitorer"
            }
        }
        
    def _load_nested_trigger_patterns(self):
        """Charge les patterns pour la gestion des triggers imbriqués"""
        self.nested_trigger_patterns = {
            "basic": r"trigger imbriqué|déclencheur imbriqué|trigger dans un trigger|déclencheur dans un déclencheur",
            "level": r"niveau|profondeur|imbrication",
            "cascade": r"en cascade|cascade|propagation|propager",
            "recursive": r"récursif|récursive|récursivement|récurrence",
            "condition": r"condition|si|quand|lorsque|lors de"
        }
        
    def _load_trigger_cursor_patterns(self):
        """Charge les patterns pour la gestion des curseurs dans les triggers"""
        self.trigger_cursor_patterns = {
            "basic": r"curseur dans le trigger|curseur dans le déclencheur|cursor dans le trigger|cursor dans le déclencheur",
            "loop": r"boucle|répéter|itérer|parcourir|parcours",
            "fetch": r"récupérer|obtenir|prendre|extraire",
            "condition": r"condition|si|quand|lorsque|lors de",
            "action": r"action|effectuer|exécuter|faire|réaliser"
        }
        
    def _load_trigger_constraint_patterns(self):
        """Charge les patterns pour la gestion des contraintes dans les triggers"""
        self.trigger_constraint_patterns = {
            "basic": r"contrainte dans le trigger|contrainte dans le déclencheur|règle dans le trigger|règle dans le déclencheur",
            "validation": r"valider|vérifier|contrôler|s'assurer",
            "check": r"vérifier que|s'assurer que|contrôler que|valider que",
            "error": r"erreur|exception|lever|générer|provoquer",
            "message": r"message|texte|description|détail"
        }
        
    def _normalize_text(self, text: str) -> str:
        """Normalise le texte pour la comparaison.
        
        Args:
            text: Texte à normaliser
            
        Returns:
            str: Texte normalisé
        """
        # Supprimer les accents
        text = unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('ASCII')
        # Convertir en minuscules
        text = text.lower()
        # Supprimer la ponctuation
        text = re.sub(r'[^\w\s]', ' ', text)
        return text
        
    def _similarity_ratio(self, s1: str, s2: str) -> float:
        """Calcule le ratio de similarité entre deux chaînes.
        
        Args:
            s1: Première chaîne
            s2: Deuxième chaîne
            
        Returns:
            float: Ratio de similarité
        """
        return SequenceMatcher(None, self._normalize_text(s1), self._normalize_text(s2)).ratio()
        
    def _correct_word(self, word: str) -> str:
        """Corrige un mot en utilisant les règles de correction.
        
        Args:
            word: Mot à corriger
            
        Returns:
            str: Mot corrigé
        """
        word = word.lower()
        
        # Vérifier les erreurs de frappe courantes
        for correct, typos in self.correction_rules["common_typos"].items():
            if word in typos:
                return correct
                
        # Vérifier les accents
        for base, variants in self.correction_rules["accents"].items():
            if word in variants:
                return base
                
        return word
        
    def _analyze_procedure(self, description: str) -> str:
        """Analyse une description de procédure stockée.
        
        Args:
            description: Description textuelle de la procédure
            
        Returns:
            str: Code SQL de la procédure
        """
        # Extraire le nom de la procédure
        name_match = re.search(r"(?:créer|définir|écrire) (?:une )?(?:procédure|fonction) ([a-zA-Z_][a-zA-Z0-9_]*)", description.lower())
        if not name_match:
            return ""
            
        proc_name = name_match.group(1)
        
        # Extraire les paramètres
        params = []
        param_matches = re.finditer(r"(?:paramètre|argument) ([a-zA-Z_][a-zA-Z0-9_]*) (?:de type|du type|type) ([a-zA-Z_][a-zA-Z0-9_]*)", description.lower())
        for match in param_matches:
            param_name = match.group(1)
            param_type = match.group(2)
            params.append(f"{param_name} {param_type}")
            
        # Extraire le type de retour pour les fonctions
        return_type = None
        if "fonction" in description.lower():
            return_match = re.search(r"(?:retourne|retourner) (?:un|une) ([a-zA-Z_][a-zA-Z0-9_]*)", description.lower())
            if return_match:
                return_type = return_match.group(1)
                
        # Construire la procédure
        query = f"CREATE {'FUNCTION' if return_type else 'PROCEDURE'} {proc_name}\n"
        
        # Ajouter les paramètres
        if params:
            query += f"({', '.join(params)})\n"
            
        # Ajouter le type de retour pour les fonctions
        if return_type:
            query += f"RETURNS {return_type}\n"
            
        # Ajouter le corps de la procédure
        query += "BEGIN\n"
        
        # Extraire et ajouter la logique
        logic = self._extract_procedure_logic(description)
        query += logic
        
        query += "END;"
        
        return query
        
    def _extract_procedure_logic(self, description: str) -> str:
        """Extrait la logique d'une procédure stockée.
        
        Args:
            description: Description textuelle de la procédure
            
        Returns:
            str: Logique SQL
        """
        logic = []
        
        # Extraire les variables
        var_matches = re.finditer(r"(?:variable|var) ([a-zA-Z_][a-zA-Z0-9_]*) (?:de type|du type|type) ([a-zA-Z_][a-zA-Z0-9_]*)", description.lower())
        for match in var_matches:
            var_name = match.group(1)
            var_type = match.group(2)
            logic.append(f"    DECLARE {var_name} {var_type};")
            
        # Extraire les boucles
        loop_matches = re.finditer(r"(?:boucle|répéter|itérer|parcourir) (?:sur|pour) ([^.,]+)", description.lower())
        for match in loop_matches:
            loop_var = match.group(1)
            logic.append(f"    FOR {loop_var} IN (SELECT * FROM {loop_var}) LOOP")
            logic.append("        -- Logique de la boucle")
            logic.append("    END LOOP;")
            
        # Extraire les conditions
        if_matches = re.finditer(r"si ([^.,]+) alors", description.lower())
        for match in if_matches:
            condition = match.group(1)
            logic.append(f"    IF {self._convert_condition_to_sql(condition)} THEN")
            logic.append("        -- Logique du if")
            logic.append("    END IF;")
            
        # Extraire les transactions
        if "transaction" in description.lower():
            logic.append("    START TRANSACTION;")
            logic.append("    -- Logique de la transaction")
            logic.append("    COMMIT;")
            
        # Extraire la gestion des erreurs
        if "erreur" in description.lower() or "exception" in description.lower():
            logic.append("    DECLARE")
            logic.append("        custom_exception EXCEPTION;")
            logic.append("    BEGIN")
            logic.append("        -- Logique avec gestion d'erreur")
            logic.append("    EXCEPTION")
            logic.append("        WHEN custom_exception THEN")
            logic.append("            ROLLBACK;")
            logic.append("            RAISE_APPLICATION_ERROR(-20001, 'Message d''erreur');")
            logic.append("    END;")
            
        return "\n".join(logic)
        
    def _analyze_complex_query(self, description: str) -> str:
        """Analyse une requête complexe avec CTE et fonctions analytiques.
        
        Args:
            description: Description textuelle de la requête
            
        Returns:
            str: Requête SQL générée
        """
        # Détecter si c'est une requête avec CTE
        if re.search(self.query_patterns[QueryType.CTE]["basic"], description.lower()):
            return self._generate_cte_query(description)
            
        # Détecter si c'est une requête récursive
        if re.search(self.query_patterns[QueryType.CTE]["recursive"], description.lower()):
            return self._generate_recursive_query(description)
            
        # Détecter si c'est une analyse statistique
        if re.search(self.query_patterns[QueryType.STATISTIC]["basic"], description.lower()):
            return self._generate_statistic_query(description)
            
        return ""
        
    def _generate_cte_query(self, description: str) -> str:
        """Génère une requête avec CTE.
        
        Args:
            description: Description textuelle de la requête
            
        Returns:
            str: Requête SQL générée
        """
        ctes = []
        
        # Extraire les CTE
        cte_matches = re.finditer(r"(?:avec|en utilisant|en définissant) ([a-zA-Z_][a-zA-Z0-9_]*) comme \((.*?)\)", description.lower(), re.DOTALL)
        for match in cte_matches:
            cte_name = match.group(1)
            cte_query = match.group(2)
            ctes.append(f"{cte_name} AS (\n{cte_query}\n)")
            
        # Extraire la requête principale
        main_query = re.search(r"(?:sélectionner|afficher) (.*?)(?:ordre|tri|limiter|fin)?", description.lower(), re.DOTALL)
        if not main_query:
            return ""
            
        # Construire la requête finale
        query = "WITH " + ",\n".join(ctes) + "\n"
        query += main_query.group(1)
        
        return query
        
    def _generate_recursive_query(self, description: str) -> str:
        """Génère une requête récursive.
        
        Args:
            description: Description textuelle de la requête
            
        Returns:
            str: Requête SQL générée
        """
        # Détecter le type de récursion
        if re.search(self.query_patterns[QueryType.CTE]["hierarchie"], description.lower()):
            return self._generate_hierarchical_query(description)
            
        return ""
        
    def _generate_hierarchical_query(self, description: str) -> str:
        """Génère une requête hiérarchique.
        
        Args:
            description: Description textuelle de la requête
            
        Returns:
            str: Requête SQL générée
        """
        # Extraire la table et les colonnes
        table_match = re.search(r"(?:table|tableau) ([a-zA-Z_][a-zA-Z0-9_]*)", description.lower())
        if not table_match:
            return ""
            
        table = table_match.group(1)
        
        # Extraire les colonnes de la hiérarchie
        id_match = re.search(r"(?:identifiant|id) ([a-zA-Z_][a-zA-Z0-9_]*)", description.lower())
        parent_match = re.search(r"(?:parent|manager|supérieur) ([a-zA-Z_][a-zA-Z0-9_]*)", description.lower())
        
        if not id_match or not parent_match:
            return ""
            
        id_col = id_match.group(1)
        parent_col = parent_match.group(1)
        
        # Construire la requête récursive
        query = f"WITH RECURSIVE hierarchie AS (\n"
        query += f"    -- Base case: trouver les racines\n"
        query += f"    SELECT \n"
        query += f"        {id_col},\n"
        query += f"        nom,\n"
        query += f"        {parent_col},\n"
        query += f"        1 AS niveau\n"
        query += f"    FROM {table}\n"
        query += f"    WHERE {parent_col} IS NULL\n\n"
        query += f"    UNION ALL\n\n"
        query += f"    -- Recursive case: trouver les enfants\n"
        query += f"    SELECT \n"
        query += f"        e.{id_col},\n"
        query += f"        e.nom,\n"
        query += f"        e.{parent_col},\n"
        query += f"        h.niveau + 1\n"
        query += f"    FROM {table} e\n"
        query += f"    JOIN hierarchie h ON e.{parent_col} = h.{id_col}\n"
        query += f")\n"
        query += f"SELECT * FROM hierarchie\n"
        query += f"ORDER BY niveau, nom;"
        
        return query
        
    def _generate_statistic_query(self, description: str) -> str:
        """Génère une requête d'analyse statistique.
        
        Args:
            description: Description textuelle de la requête
            
        Returns:
            str: Requête SQL générée
        """
        # Détecter le type d'analyse statistique
        if "écart-type" in description.lower() or "variance" in description.lower():
            return self._generate_standard_deviation_query(description)
        elif "médiane" in description.lower() or "quartile" in description.lower():
            return self._generate_median_query(description)
        elif "corrélation" in description.lower():
            return self._generate_correlation_query(description)
            
        return ""
        
    def _generate_standard_deviation_query(self, description: str) -> str:
        """Génère une requête pour calculer l'écart-type.
        
        Args:
            description: Description textuelle de la requête
            
        Returns:
            str: Requête SQL générée
        """
        # Extraire la table et la colonne
        table_match = re.search(r"(?:table|tableau) ([a-zA-Z_][a-zA-Z0-9_]*)", description.lower())
        column_match = re.search(r"(?:colonne|valeur) ([a-zA-Z_][a-zA-Z0-9_]*)", description.lower())
        
        if not table_match or not column_match:
            return ""
            
        table = table_match.group(1)
        column = column_match.group(1)
        
        # Construire la requête
        query = f"WITH statistiques AS (\n"
        query += f"    SELECT \n"
        query += f"        AVG({column}) AS moyenne,\n"
        query += f"        STDDEV({column}) AS ecart_type,\n"
        query += f"        VARIANCE({column}) AS variance\n"
        query += f"    FROM {table}\n"
        query += f")\n"
        query += f"SELECT \n"
        query += f"    moyenne,\n"
        query += f"    ecart_type,\n"
        query += f"    variance,\n"
        query += f"    moyenne - 2 * ecart_type AS limite_inf,\n"
        query += f"    moyenne + 2 * ecart_type AS limite_sup\n"
        query += f"FROM statistiques;"
        
        return query
        
    def _validate_query(self, query: str, query_type: QueryType) -> bool:
        """Valide une requête SQL générée.
        
        Args:
            query: Requête SQL à valider
            query_type: Type de requête
            
        Returns:
            bool: True si la requête est valide, False sinon
        """
        try:
            # Vérifier la syntaxe de base
            if not query.strip():
                raise SyntaxError("Requête vide", query_type)
                
            # Vérifier les tables et colonnes
            self._validate_tables_and_columns(query)
            
            # Vérifier les jointures
            self._validate_joins(query)
            
            # Vérifier les conditions
            self._validate_conditions(query)
            
            # Vérifier les agrégations
            self._validate_aggregations(query)
            
            # Vérifier les CTE
            if query_type == QueryType.CTE:
                self._validate_cte(query)
                
            # Vérifier les transactions
            if query_type == QueryType.TRANSACTION:
                self._validate_transaction(query)
                
            return True
            
        except QueryError as e:
            self.error_handler.handle_error(e, "Erreur de validation de la requête")
            self.error_occurred.emit(str(e))
            return False
            
    def _validate_tables_and_columns(self, query: str):
        """Valide les tables et colonnes d'une requête.
        
        Args:
            query: Requête SQL à valider
            
        Raises:
            SyntaxError: Si une table ou une colonne est invalide
        """
        # Vérifier les tables
        tables = re.findall(r"FROM\s+([a-zA-Z_][a-zA-Z0-9_]*)", query)
        if not tables:
            raise SyntaxError("Aucune table spécifiée", QueryType.SELECT)
            
        # Vérifier les colonnes
        columns = re.findall(r"SELECT\s+(.*?)\s+FROM", query)
        if not columns or columns[0] == "*":
            return
            
        # Vérifier les alias de colonnes
        aliases = re.findall(r"AS\s+([a-zA-Z_][a-zA-Z0-9_]*)", query)
        if len(set(aliases)) != len(aliases):
            raise SemanticError("Alias de colonnes dupliqués", QueryType.SELECT)
            
    def _validate_joins(self, query: str):
        """Valide les jointures d'une requête.
        
        Args:
            query: Requête SQL à valider
            
        Raises:
            SyntaxError: Si une jointure est invalide
        """
        joins = re.findall(r"JOIN\s+([a-zA-Z_][a-zA-Z0-9_]*)", query)
        conditions = re.findall(r"ON\s+(.*?)(?:WHERE|GROUP BY|ORDER BY|LIMIT|$)", query)
        
        if len(joins) != len(conditions):
            raise SyntaxError("Nombre de jointures et de conditions ON ne correspond pas", QueryType.SELECT)
            
    def _validate_conditions(self, query: str):
        """Valide les conditions d'une requête.
        
        Args:
            query: Requête SQL à valider
            
        Raises:
            SyntaxError: Si une condition est invalide
        """
        # Vérifier les conditions WHERE
        where_conditions = re.findall(r"WHERE\s+(.*?)(?:GROUP BY|ORDER BY|LIMIT|$)", query)
        if where_conditions:
            self._validate_condition_syntax(where_conditions[0])
            
        # Vérifier les conditions HAVING
        having_conditions = re.findall(r"HAVING\s+(.*?)(?:ORDER BY|LIMIT|$)", query)
        if having_conditions:
            self._validate_condition_syntax(having_conditions[0])
            
    def _validate_condition_syntax(self, condition: str):
        """Valide la syntaxe d'une condition.
        
        Args:
            condition: Condition à valider
            
        Raises:
            SyntaxError: Si la condition est invalide
        """
        # Vérifier les opérateurs
        operators = ["=", "!=", ">", "<", ">=", "<=", "LIKE", "IN", "BETWEEN", "IS NULL", "IS NOT NULL"]
        if not any(op in condition for op in operators):
            raise SyntaxError("Condition sans opérateur valide", QueryType.SELECT)
            
        # Vérifier les parenthèses
        if condition.count("(") != condition.count(")"):
            raise SyntaxError("Parenthèses non équilibrées dans la condition", QueryType.SELECT)
            
    def _validate_aggregations(self, query: str):
        """Valide les agrégations d'une requête.
        
        Args:
            query: Requête SQL à valider
            
        Raises:
            SyntaxError: Si une agrégation est invalide
        """
        # Vérifier les fonctions d'agrégation
        aggregations = re.findall(r"(COUNT|SUM|AVG|MIN|MAX)\s*\((.*?)\)", query)
        for func, col in aggregations:
            if not col.strip():
                raise SyntaxError(f"Colonne manquante dans la fonction {func}", QueryType.SELECT)
                
    def _validate_cte(self, query: str):
        """Valide une requête avec CTE.
        
        Args:
            query: Requête SQL à valider
            
        Raises:
            SyntaxError: Si la CTE est invalide
        """
        # Vérifier la syntaxe WITH
        if not query.startswith("WITH"):
            raise SyntaxError("Requête CTE doit commencer par WITH", QueryType.CTE)
            
        # Vérifier les CTE récursifs
        if "RECURSIVE" in query:
            self._validate_recursive_cte(query)
            
    def _validate_recursive_cte(self, query: str):
        """Valide une CTE récursive.
        
        Args:
            query: Requête SQL à valider
            
        Raises:
            SyntaxError: Si la CTE récursive est invalide
        """
        # Vérifier la présence de UNION ALL
        if "UNION ALL" not in query:
            raise SyntaxError("CTE récursive doit contenir UNION ALL", QueryType.RECURSIVE)
            
        # Vérifier la condition d'arrêt
        if "WHERE" not in query:
            raise SyntaxError("CTE récursive doit avoir une condition d'arrêt", QueryType.RECURSIVE)
            
    def _validate_transaction(self, query: str):
        """Valide une transaction.
        
        Args:
            query: Requête SQL à valider
            
        Raises:
            SyntaxError: Si la transaction est invalide
        """
        # Vérifier le début de la transaction
        if not query.startswith("BEGIN"):
            raise SyntaxError("Transaction doit commencer par BEGIN", QueryType.TRANSACTION)
            
        # Vérifier la fin de la transaction
        if not query.endswith("COMMIT") and not query.endswith("ROLLBACK"):
            raise SyntaxError("Transaction doit se terminer par COMMIT ou ROLLBACK", QueryType.TRANSACTION)
            
    def analyze_query(self, description: str) -> str:
        """Analyse une description textuelle et génère la requête SQL correspondante.
        
        Args:
            description: Description textuelle de la requête
            
        Returns:
            str: Requête SQL générée
        """
        try:
            # Corriger les erreurs de frappe
            corrected_description = self._correct_text(description)
            
            # Vérifier la syntaxe de base
            if not corrected_description.strip():
                raise SyntaxError("Description vide", QueryType.SELECT)
                
            # Vérifier si c'est un trigger imbriqué
            if re.search(self.nested_trigger_patterns["basic"], corrected_description.lower()):
                query = self._generate_nested_trigger(corrected_description)
            # Vérifier si c'est un trigger avec curseur
            elif re.search(self.trigger_cursor_patterns["basic"], corrected_description.lower()):
                query = self._generate_trigger_with_cursor(corrected_description)
            # Vérifier si c'est un trigger avec contraintes
            elif re.search(self.trigger_constraint_patterns["basic"], corrected_description.lower()):
                query = self._generate_trigger_with_constraints(corrected_description)
            # Vérifier si c'est un trigger complexe
            elif re.search(self.trigger_patterns["basic"], corrected_description.lower()):
                if re.search(self.trigger_patterns["action"]["audit"], corrected_description.lower()):
                    query = self._generate_audit_trigger(corrected_description)
                else:
                    query = self._generate_complex_trigger(corrected_description)
            # Vérifier si c'est une transaction
            elif re.search(self.constraint_patterns["transaction"]["begin"], corrected_description.lower()):
                query = self._generate_transaction(corrected_description)
            # Vérifier si c'est une clé étrangère
            elif re.search(self.constraint_patterns["foreign_key"]["basic"], corrected_description.lower()):
                query = self._generate_foreign_key(corrected_description)
            # Vérifier si c'est une vue matérialisée
            elif re.search(r"vue matérialisée", corrected_description.lower()):
                query = self._generate_materialized_view(corrected_description)
            # Vérifier si c'est un curseur
            elif re.search(r"curseur|cursor", corrected_description.lower()):
                query = self._generate_cursor(corrected_description)
            # Vérifier si c'est une requête complexe
            elif re.search(self.query_patterns[QueryType.CTE]["basic"], corrected_description.lower()) or \
                 re.search(self.query_patterns[QueryType.ANALYTIC]["basic"], corrected_description.lower()):
                query = self._analyze_complex_query(corrected_description)
            # Vérifier si c'est une procédure stockée
            elif re.search(self.procedure_patterns["basic"], corrected_description.lower()):
                query = self._analyze_procedure(corrected_description)
            else:
                # Déterminer le type de requête
                query_type = self._determine_query_type(corrected_description)
                
                # Générer la requête selon le type
                if query_type == QueryType.SELECT:
                    query = self._generate_select_query(corrected_description)
                elif query_type == QueryType.INSERT:
                    query = self._generate_insert_query(corrected_description)
                elif query_type == QueryType.UPDATE:
                    query = self._generate_update_query(corrected_description)
                elif query_type == QueryType.DELETE:
                    query = self._generate_delete_query(corrected_description)
                else:
                    raise ValueError("Type de requête non supporté")
                    
            # Valider la requête générée
            if not self._validate_query(query, query_type):
                return ""
                
            # Valider les performances
            performance_suggestions = self._validate_performance(query)
            if performance_suggestions:
                self.suggestion_made.emit("Suggestions d'optimisation :\n" + "\n".join(performance_suggestions))
                
            return query
                
        except QueryError as e:
            self.error_handler.handle_error(e, "Erreur lors de l'analyse de la requête")
            self.error_occurred.emit(str(e))
            return ""
        except Exception as e:
            self.error_handler.handle_error(e, "Erreur inattendue")
            self.error_occurred.emit(str(e))
            return ""
            
    def _correct_text(self, text: str) -> str:
        """Corrige le texte en gérant les erreurs de frappe.
        
        Args:
            text: Texte à corriger
            
        Returns:
            str: Texte corrigé
        """
        words = text.split()
        corrected_words = []
        
        for word in words:
            # Corriger le mot
            corrected_word = self._correct_word(word)
            corrected_words.append(corrected_word)
            
            # Si le mot a été corrigé, émettre une suggestion
            if corrected_word != word:
                self.suggestion_made.emit(f"Suggestions pour '{word}': {corrected_word}")
                
        return " ".join(corrected_words)
        
    def _determine_query_type(self, description: str) -> QueryType:
        """Détermine le type de requête à partir de la description.
        
        Args:
            description: Description textuelle de la requête
            
        Returns:
            QueryType: Type de requête déterminé
        """
        description = description.lower()
        
        # Vérifier les patterns pour chaque type de requête
        for query_type, patterns in self.query_patterns.items():
            if any(re.search(pattern, description) for pattern in patterns["basic"]):
                return query_type
                
        # Par défaut, considérer comme une requête SELECT
        return QueryType.SELECT
        
    def _generate_select_query(self, description: str) -> str:
        """Génère une requête SELECT à partir de la description.
        
        Args:
            description: Description textuelle de la requête
            
        Returns:
            str: Requête SELECT générée
        """
        # Extraire les tables
        tables = self._extract_tables(description)
        
        # Extraire les conditions de jointure
        joins = self._extract_joins(description, tables)
        
        # Extraire les conditions WHERE
        where_conditions = self._extract_where_conditions(description)
        
        # Extraire les conditions GROUP BY
        group_by = self._extract_group_by(description)
        
        # Extraire les conditions HAVING
        having = self._extract_having(description)
        
        # Extraire les conditions ORDER BY
        order_by = self._extract_order_by(description)
        
        # Extraire la limite
        limit = self._extract_limit(description)
        
        # Construire la requête
        query = "SELECT "
        
        # Ajouter DISTINCT si nécessaire
        if re.search(self.query_patterns[QueryType.SELECT]["distinct"], description.lower()):
            query += "DISTINCT "
            
        # Ajouter les colonnes (à implémenter selon le contexte)
        query += "* "
        
        # Ajouter les tables et jointures
        query += f"FROM {tables[0]} "
        for join in joins:
            query += f"{join} "
            
        # Ajouter les conditions WHERE
        if where_conditions:
            query += f"WHERE {where_conditions} "
            
        # Ajouter GROUP BY
        if group_by:
            query += f"GROUP BY {group_by} "
            
        # Ajouter HAVING
        if having:
            query += f"HAVING {having} "
            
        # Ajouter ORDER BY
        if order_by:
            query += f"ORDER BY {order_by} "
            
        # Ajouter LIMIT
        if limit:
            query += f"LIMIT {limit} "
            
        return query.strip()
        
    def _extract_tables(self, description: str) -> list[str]:
        """Extrait les noms des tables mentionnées dans la description.
        
        Args:
            description: Description textuelle de la requête
            
        Returns:
            list[str]: Liste des noms de tables
        """
        # Pattern pour détecter les noms de tables
        table_pattern = r"(?:table|tableau|liste|ensemble) (?:des |de |du |de la |de l'|des )?([a-zA-Z_][a-zA-Z0-9_]*)"
        matches = re.finditer(table_pattern, description.lower())
        return [match.group(1) for match in matches]
        
    def _extract_joins(self, description: str, tables: list[str]) -> list[str]:
        """Extrait les conditions de jointure à partir de la description.
        
        Args:
            description: Description textuelle de la requête
            tables: Liste des tables mentionnées
            
        Returns:
            list[str]: Liste des conditions de jointure
        """
        joins = []
        description = description.lower()
        
        # Détecter les jointures explicites
        join_pattern = r"(?:joindre|relier|associer|combiner) (?:avec|à) ([a-zA-Z_][a-zA-Z0-9_]*)"
        matches = re.finditer(join_pattern, description)
        
        for match in matches:
            table = match.group(1)
            if table in tables:
                # Chercher la condition de jointure
                condition_pattern = r"(?:sur|par|via) ([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*([a-zA-Z_][a-zA-Z0-9_]*)"
                condition_match = re.search(condition_pattern, description)
                if condition_match:
                    joins.append(f"INNER JOIN {table} ON {condition_match.group(1)} = {condition_match.group(2)}")
                    
        return joins
        
    def _extract_where_conditions(self, description: str) -> str:
        """Extrait les conditions WHERE à partir de la description.
        
        Args:
            description: Description textuelle de la requête
            
        Returns:
            str: Conditions WHERE extraites
        """
        # Pattern pour détecter les conditions
        where_pattern = r"(?:où|dans lequel|dans laquelle|dans lesquels|dans lesquelles|si|quand) ([^.,]+)"
        match = re.search(where_pattern, description.lower())
        if match:
            return self._convert_condition_to_sql(match.group(1))
        return ""
        
    def _extract_group_by(self, description: str) -> str:
        """Extrait les conditions GROUP BY à partir de la description.
        
        Args:
            description: Description textuelle de la requête
            
        Returns:
            str: Conditions GROUP BY extraites
        """
        # Pattern pour détecter les groupements
        group_pattern = r"(?:grouper par|regrouper par|grouper selon|regrouper selon) ([^.,]+)"
        match = re.search(group_pattern, description.lower())
        if match:
            return match.group(1)
        return ""
        
    def _extract_having(self, description: str) -> str:
        """Extrait les conditions HAVING à partir de la description.
        
        Args:
            description: Description textuelle de la requête
            
        Returns:
            str: Conditions HAVING extraites
        """
        # Pattern pour détecter les conditions HAVING
        having_pattern = r"(?:ayant|avec|dont) ([^.,]+)"
        match = re.search(having_pattern, description.lower())
        if match:
            return self._convert_condition_to_sql(match.group(1))
        return ""
        
    def _extract_order_by(self, description: str) -> str:
        """Extrait les conditions ORDER BY à partir de la description.
        
        Args:
            description: Description textuelle de la requête
            
        Returns:
            str: Conditions ORDER BY extraites
        """
        # Pattern pour détecter les tri
        order_pattern = r"(?:trier par|ordonner par|classer par|trier selon|ordonner selon|classer selon) ([^.,]+)"
        match = re.search(order_pattern, description.lower())
        if match:
            return match.group(1)
        return ""
        
    def _extract_limit(self, description: str) -> str:
        """Extrait la limite à partir de la description.
        
        Args:
            description: Description textuelle de la requête
            
        Returns:
            str: Limite extraite
        """
        # Pattern pour détecter la limite
        limit_pattern = r"(?:limiter à|limiter par|limiter de|limiter en) (\d+)"
        match = re.search(limit_pattern, description.lower())
        if match:
            return match.group(1)
        return ""
        
    def _convert_condition_to_sql(self, condition: str) -> str:
        """Convertit une condition en langage naturel en condition SQL.
        
        Args:
            condition: Condition en langage naturel
            
        Returns:
            str: Condition SQL
        """
        # Remplacer les opérateurs en langage naturel par leurs équivalents SQL
        condition = condition.lower()
        condition = re.sub(r"est égal à|égale|égales|égaux|égale à|égales à|égaux à", "=", condition)
        condition = re.sub(r"est différent de|différent de|différente de|différents de|différentes de", "!=", condition)
        condition = re.sub(r"est supérieur à|supérieur à|supérieure à|supérieurs à|supérieures à", ">", condition)
        condition = re.sub(r"est inférieur à|inférieur à|inférieure à|inférieurs à|inférieures à", "<", condition)
        condition = re.sub(r"est supérieur ou égal à|supérieur ou égal à|supérieure ou égale à|supérieurs ou égaux à|supérieures ou égales à", ">=", condition)
        condition = re.sub(r"est inférieur ou égal à|inférieur ou égal à|inférieure ou égale à|inférieurs ou égaux à|inférieures ou égales à", "<=", condition)
        condition = re.sub(r"contient|contient la|contient le|contient les", "LIKE", condition)
        condition = re.sub(r"commence par|commence avec", "LIKE", condition)
        condition = re.sub(r"finit par|finit avec", "LIKE", condition)
        condition = re.sub(r"est dans|est présent dans|est inclut dans|est inclus dans", "IN", condition)
        condition = re.sub(r"est entre|est compris entre", "BETWEEN", condition)
        condition = re.sub(r"est nul|est vide|n'a pas de valeur", "IS NULL", condition)
        condition = re.sub(r"n'est pas nul|n'est pas vide|a une valeur", "IS NOT NULL", condition)
        
        return condition.strip()

    def _generate_transaction(self, description: str) -> str:
        """Génère une transaction.
        
        Args:
            description: Description textuelle de la transaction
            
        Returns:
            str: Code SQL de la transaction
        """
        # Extraire les opérations de la transaction
        operations = []
        operation_matches = re.finditer(r"(?:effectuer|exécuter|faire|réaliser) (.*?)(?:et|puis|ensuite|après|avant)", description.lower(), re.DOTALL)
        for match in operation_matches:
            operations.append(match.group(1))
            
        # Extraire les points de sauvegarde
        savepoints = []
        savepoint_matches = re.finditer(r"(?:point de sauvegarde|sauvegarder à|marquer) ([a-zA-Z_][a-zA-Z0-9_]*)", description.lower())
        for match in savepoint_matches:
            savepoints.append(match.group(1))
            
        # Construire la transaction
        query = "BEGIN;\n\n"
        
        # Ajouter les points de sauvegarde
        for savepoint in savepoints:
            query += f"SAVEPOINT {savepoint};\n"
            
        # Ajouter les opérations
        for operation in operations:
            query += f"{operation};\n"
            
        # Ajouter la validation ou l'annulation
        if re.search(self.constraint_patterns["transaction"]["commit"], description.lower()):
            query += "\nCOMMIT;"
        elif re.search(self.constraint_patterns["transaction"]["rollback"], description.lower()):
            query += "\nROLLBACK;"
        else:
            query += "\nCOMMIT;"
            
        return query
        
    def _generate_foreign_key(self, description: str) -> str:
        """Génère une contrainte de clé étrangère.
        
        Args:
            description: Description textuelle de la contrainte
            
        Returns:
            str: Code SQL de la contrainte
        """
        # Extraire les tables et colonnes
        table_match = re.search(r"(?:table|tableau) ([a-zA-Z_][a-zA-Z0-9_]*)", description.lower())
        column_match = re.search(r"(?:colonne|champ) ([a-zA-Z_][a-zA-Z0-9_]*)", description.lower())
        ref_table_match = re.search(r"(?:référence|lié à|associé à|relatif à) (?:la table|le tableau) ([a-zA-Z_][a-zA-Z0-9_]*)", description.lower())
        ref_column_match = re.search(r"(?:colonne|champ) ([a-zA-Z_][a-zA-Z0-9_]*) (?:de|dans) (?:la table|le tableau)", description.lower())
        
        if not all([table_match, column_match, ref_table_match, ref_column_match]):
            return ""
            
        table = table_match.group(1)
        column = column_match.group(1)
        ref_table = ref_table_match.group(1)
        ref_column = ref_column_match.group(1)
        
        # Déterminer le comportement en cas de suppression/modification
        on_delete = "RESTRICT"
        on_update = "RESTRICT"
        
        if re.search(self.constraint_patterns["foreign_key"]["cascade"], description.lower()):
            on_delete = "CASCADE"
            on_update = "CASCADE"
        elif re.search(self.constraint_patterns["foreign_key"]["set_null"], description.lower()):
            on_delete = "SET NULL"
            on_update = "SET NULL"
            
        # Construire la contrainte
        query = f"ALTER TABLE {table}\n"
        query += f"ADD CONSTRAINT fk_{table}_{column}\n"
        query += f"FOREIGN KEY ({column})\n"
        query += f"REFERENCES {ref_table}({ref_column})\n"
        query += f"ON DELETE {on_delete}\n"
        query += f"ON UPDATE {on_update};"
        
        return query
        
    def _generate_materialized_view(self, description: str) -> str:
        """Génère une vue matérialisée.
        
        Args:
            description: Description textuelle de la vue
            
        Returns:
            str: Code SQL de la vue
        """
        # Extraire le nom de la vue
        name_match = re.search(r"(?:vue|view) ([a-zA-Z_][a-zA-Z0-9_]*)", description.lower())
        if not name_match:
            return ""
            
        view_name = name_match.group(1)
        
        # Extraire les colonnes
        columns = []
        column_matches = re.finditer(r"(?:colonne|champ) ([a-zA-Z_][a-zA-Z0-9_]*)", description.lower())
        for match in column_matches:
            columns.append(match.group(1))
            
        # Extraire la requête sous-jacente
        subquery_match = re.search(r"(?:requête|query) ([^.,]+)", description.lower())
        if not subquery_match:
            return ""
            
        subquery = subquery_match.group(1)
        
        # Construire la vue
        query = f"CREATE MATERIALIZED VIEW {view_name} AS\n"
        query += f"SELECT {', '.join(columns)}\n"
        query += f"FROM ({subquery})\n"
        query += "WITH NO DATA;"
        
        return query
        
    def _generate_cursor(self, description: str) -> str:
        """Génère un curseur.
        
        Args:
            description: Description textuelle du curseur
            
        Returns:
            str: Code SQL du curseur
        """
        # Extraire le nom du curseur
        name_match = re.search(r"(?:curseur|cursor) ([a-zA-Z_][a-zA-Z0-9_]*)", description.lower())
        if not name_match:
            return ""
            
        cursor_name = name_match.group(1)
        
        # Extraire la requête sous-jacente
        subquery_match = re.search(r"(?:requête|query) ([^.,]+)", description.lower())
        if not subquery_match:
            return ""
            
        subquery = subquery_match.group(1)
        
        # Construire le curseur
        query = f"DECLARE {cursor_name} CURSOR FOR\n"
        query += f"SELECT * FROM ({subquery});"
        
        return query

    def _generate_complex_trigger(self, description: str) -> str:
        """Génère un trigger complexe.
        
        Args:
            description: Description textuelle du trigger
            
        Returns:
            str: Code SQL du trigger
        """
        # Extraire le nom du trigger
        name_match = re.search(r"(?:trigger|déclencheur) ([a-zA-Z_][a-zA-Z0-9_]*)", description.lower())
        if not name_match:
            return ""
            
        trigger_name = name_match.group(1)
        
        # Extraire la table cible
        table_match = re.search(r"(?:sur|pour) (?:la table|le tableau) ([a-zA-Z_][a-zA-Z0-9_]*)", description.lower())
        if not table_match:
            return ""
            
        table_name = table_match.group(1)
        
        # Déterminer le timing
        timing = "AFTER"
        if re.search(self.trigger_patterns["timing"]["before"], description.lower()):
            timing = "BEFORE"
        elif re.search(self.trigger_patterns["timing"]["instead"], description.lower()):
            timing = "INSTEAD OF"
            
        # Déterminer les événements
        events = []
        if re.search(self.trigger_patterns["event"]["insert"], description.lower()):
            events.append("INSERT")
        if re.search(self.trigger_patterns["event"]["update"], description.lower()):
            events.append("UPDATE")
        if re.search(self.trigger_patterns["event"]["delete"], description.lower()):
            events.append("DELETE")
        if re.search(self.trigger_patterns["event"]["truncate"], description.lower()):
            events.append("TRUNCATE")
            
        # Extraire la condition WHEN
        when_condition = None
        when_match = re.search(r"(?:quand|si|lorsque|lors de) ([^.,]+)", description.lower())
        if when_match:
            when_condition = self._convert_condition_to_sql(when_match.group(1))
            
        # Extraire les actions
        actions = []
        action_matches = re.finditer(r"(?:exécuter|effectuer|réaliser|faire) ([^.,]+)", description.lower())
        for match in action_matches:
            actions.append(match.group(1))
            
        # Construire le trigger
        query = f"CREATE OR REPLACE TRIGGER {trigger_name}\n"
        query += f"{timing} {' OR '.join(events)}\n"
        query += f"ON {table_name}\n"
        
        if when_condition:
            query += f"WHEN ({when_condition})\n"
            
        query += "FOR EACH ROW\n"
        query += "BEGIN\n"
        
        # Ajouter les actions
        for action in actions:
            query += f"    {action};\n"
            
        # Ajouter la gestion des erreurs
        query += "EXCEPTION\n"
        query += "    WHEN OTHERS THEN\n"
        query += "        RAISE_APPLICATION_ERROR(-20001, 'Erreur dans le trigger : ' || SQLERRM);\n"
        query += "END;"
        
        return query
        
    def _generate_audit_trigger(self, description: str) -> str:
        """Génère un trigger d'audit.
        
        Args:
            description: Description textuelle du trigger
            
        Returns:
            str: Code SQL du trigger
        """
        # Extraire le nom du trigger
        name_match = re.search(r"(?:trigger|déclencheur) ([a-zA-Z_][a-zA-Z0-9_]*)", description.lower())
        if not name_match:
            return ""
            
        trigger_name = name_match.group(1)
        
        # Extraire la table cible
        table_match = re.search(r"(?:sur|pour) (?:la table|le tableau) ([a-zA-Z_][a-zA-Z0-9_]*)", description.lower())
        if not table_match:
            return ""
            
        table_name = table_match.group(1)
        
        # Extraire les colonnes à auditer
        columns = []
        column_matches = re.finditer(r"(?:colonne|champ) ([a-zA-Z_][a-zA-Z0-9_]*)", description.lower())
        for match in column_matches:
            columns.append(match.group(1))
            
        # Construire le trigger
        query = f"CREATE OR REPLACE TRIGGER {trigger_name}_audit\n"
        query += "AFTER INSERT OR UPDATE OR DELETE\n"
        query += f"ON {table_name}\n"
        query += "FOR EACH ROW\n"
        query += "BEGIN\n"
        
        # Ajouter l'insertion dans la table d'audit
        query += "    INSERT INTO audit_log (\n"
        query += "        table_name,\n"
        query += "        operation,\n"
        query += "        old_values,\n"
        query += "        new_values,\n"
        query += "        changed_by,\n"
        query += "        changed_at\n"
        query += "    ) VALUES (\n"
        query += f"        '{table_name}',\n"
        query += "        CASE\n"
        query += "            WHEN INSERTING THEN 'INSERT'\n"
        query += "            WHEN UPDATING THEN 'UPDATE'\n"
        query += "            WHEN DELETING THEN 'DELETE'\n"
        query += "        END,\n"
        query += "        CASE\n"
        query += "            WHEN UPDATING OR DELETING THEN\n"
        query += "                json_build_object(\n"
        for col in columns:
            query += f"                    '{col}', OLD.{col},\n"
        query += "                )::text\n"
        query += "            ELSE NULL\n"
        query += "        END,\n"
        query += "        CASE\n"
        query += "            WHEN INSERTING OR UPDATING THEN\n"
        query += "                json_build_object(\n"
        for col in columns:
            query += f"                    '{col}', NEW.{col},\n"
        query += "                )::text\n"
        query += "            ELSE NULL\n"
        query += "        END,\n"
        query += "        current_user,\n"
        query += "        current_timestamp\n"
        query += "    );\n"
        
        query += "END;"
        
        return query

    def _generate_nested_trigger(self, description: str) -> str:
        """Génère un trigger imbriqué.
        
        Args:
            description: Description textuelle du trigger
            
        Returns:
            str: Code SQL du trigger
        """
        # Extraire le nom du trigger parent
        parent_match = re.search(r"(?:trigger|déclencheur) parent ([a-zA-Z_][a-zA-Z0-9_]*)", description.lower())
        if not parent_match:
            return ""
            
        parent_name = parent_match.group(1)
        
        # Extraire le nom du trigger enfant
        child_match = re.search(r"(?:trigger|déclencheur) enfant ([a-zA-Z_][a-zA-Z0-9_]*)", description.lower())
        if not child_match:
            return ""
            
        child_name = child_match.group(1)
        
        # Extraire la table cible
        table_match = re.search(r"(?:sur|pour) (?:la table|le tableau) ([a-zA-Z_][a-zA-Z0-9_]*)", description.lower())
        if not table_match:
            return ""
            
        table_name = table_match.group(1)
        
        # Déterminer le niveau d'imbrication
        level = 1
        level_match = re.search(r"(?:niveau|profondeur|imbrication) (\d+)", description.lower())
        if level_match:
            level = int(level_match.group(1))
            
        # Déterminer si c'est une cascade
        is_cascade = bool(re.search(self.nested_trigger_patterns["cascade"], description.lower()))
        
        # Construire le trigger parent
        parent_query = f"CREATE OR REPLACE TRIGGER {parent_name}\n"
        parent_query += "AFTER INSERT OR UPDATE OR DELETE\n"
        parent_query += f"ON {table_name}\n"
        parent_query += "FOR EACH ROW\n"
        parent_query += "BEGIN\n"
        
        # Ajouter la logique du trigger parent
        parent_query += "    -- Logique du trigger parent\n"
        parent_query += "    IF :NEW.status = 'ACTIVE' THEN\n"
        parent_query += f"        -- Déclencher le trigger enfant\n"
        parent_query += "    END IF;\n"
        parent_query += "END;"
        
        # Construire le trigger enfant
        child_query = f"CREATE OR REPLACE TRIGGER {child_name}\n"
        child_query += "AFTER INSERT OR UPDATE OR DELETE\n"
        child_query += f"ON {table_name}\n"
        child_query += "FOR EACH ROW\n"
        child_query += "BEGIN\n"
        
        # Ajouter la logique du trigger enfant
        child_query += "    -- Logique du trigger enfant\n"
        child_query += "    IF :NEW.status = 'ACTIVE' THEN\n"
        child_query += "        -- Actions spécifiques\n"
        child_query += "    END IF;\n"
        child_query += "END;"
        
        return f"{parent_query}\n\n{child_query}"
        
    def _generate_trigger_with_cursor(self, description: str) -> str:
        """Génère un trigger avec curseur.
        
        Args:
            description: Description textuelle du trigger
            
        Returns:
            str: Code SQL du trigger
        """
        # Extraire le nom du trigger
        name_match = re.search(r"(?:trigger|déclencheur) ([a-zA-Z_][a-zA-Z0-9_]*)", description.lower())
        if not name_match:
            return ""
            
        trigger_name = name_match.group(1)
        
        # Extraire la table cible
        table_match = re.search(r"(?:sur|pour) (?:la table|le tableau) ([a-zA-Z_][a-zA-Z0-9_]*)", description.lower())
        if not table_match:
            return ""
            
        table_name = table_match.group(1)
        
        # Extraire le nom du curseur
        cursor_match = re.search(r"(?:curseur|cursor) ([a-zA-Z_][a-zA-Z0-9_]*)", description.lower())
        if not cursor_match:
            return ""
            
        cursor_name = cursor_match.group(1)
        
        # Construire le trigger
        query = f"CREATE OR REPLACE TRIGGER {trigger_name}\n"
        query += "AFTER INSERT OR UPDATE OR DELETE\n"
        query += f"ON {table_name}\n"
        query += "FOR EACH ROW\n"
        query += "DECLARE\n"
        query += f"    {cursor_name} CURSOR FOR\n"
        query += "        SELECT * FROM related_table\n"
        query += "        WHERE status = :NEW.status;\n"
        query += "    v_record related_table%ROWTYPE;\n"
        query += "BEGIN\n"
        
        # Ajouter la logique avec le curseur
        query += f"    OPEN {cursor_name};\n"
        query += "    LOOP\n"
        query += f"        FETCH {cursor_name} INTO v_record;\n"
        query += "        EXIT WHEN NOT FOUND;\n"
        query += "        -- Actions avec v_record\n"
        query += "    END LOOP;\n"
        query += f"    CLOSE {cursor_name};\n"
        query += "END;"
        
        return query
        
    def _generate_trigger_with_constraints(self, description: str) -> str:
        """Génère un trigger avec contraintes.
        
        Args:
            description: Description textuelle du trigger
            
        Returns:
            str: Code SQL du trigger
        """
        # Extraire le nom du trigger
        name_match = re.search(r"(?:trigger|déclencheur) ([a-zA-Z_][a-zA-Z0-9_]*)", description.lower())
        if not name_match:
            return ""
            
        trigger_name = name_match.group(1)
        
        # Extraire la table cible
        table_match = re.search(r"(?:sur|pour) (?:la table|le tableau) ([a-zA-Z_][a-zA-Z0-9_]*)", description.lower())
        if not table_match:
            return ""
            
        table_name = table_match.group(1)
        
        # Extraire les contraintes
        constraints = []
        constraint_matches = re.finditer(r"(?:vérifier que|s'assurer que|contrôler que|valider que) ([^.,]+)", description.lower())
        for match in constraint_matches:
            constraints.append(match.group(1))
            
        # Extraire le message d'erreur
        error_message = "Contrainte violée"
        message_match = re.search(r"(?:message|texte|description|détail) ([^.,]+)", description.lower())
        if message_match:
            error_message = message_match.group(1)
            
        # Construire le trigger
        query = f"CREATE OR REPLACE TRIGGER {trigger_name}\n"
        query += "BEFORE INSERT OR UPDATE OR DELETE\n"
        query += f"ON {table_name}\n"
        query += "FOR EACH ROW\n"
        query += "BEGIN\n"
        
        # Ajouter les contraintes
        for constraint in constraints:
            query += f"    IF NOT ({self._convert_condition_to_sql(constraint)}) THEN\n"
            query += f"        RAISE_APPLICATION_ERROR(-20001, '{error_message}');\n"
            query += "    END IF;\n"
            
        query += "END;"
        
        return query

class QueryInspectorDialog(QDialog):
    """Dialogue pour l'inspecteur de requêtes."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.query_inspector = QueryInspector()
        self.setup_ui()
        
    def setup_ui(self):
        """Configure l'interface utilisateur."""
        self.setWindowTitle("Inspecteur de Requêtes SQL")
        self.setMinimumWidth(800)
        self.setMinimumHeight(600)
        
        layout = QVBoxLayout()
        
        # Zone de description
        description_label = QLabel("Décrivez la requête SQL souhaitée :")
        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText("Exemple : Créer une procédure qui calcule le total des ventes par client, avec gestion des erreurs")
        layout.addWidget(description_label)
        layout.addWidget(self.description_edit)
        
        # Options de correction
        options_layout = QHBoxLayout()
        self.correct_typos_check = QCheckBox("Corriger les erreurs de frappe")
        self.correct_typos_check.setChecked(True)
        self.show_suggestions_check = QCheckBox("Afficher les suggestions")
        self.show_suggestions_check.setChecked(True)
        options_layout.addWidget(self.correct_typos_check)
        options_layout.addWidget(self.show_suggestions_check)
        layout.addLayout(options_layout)
        
        # Bouton d'analyse
        analyze_button = QPushButton("Analyser")
        analyze_button.clicked.connect(self._analyze_query)
        layout.addWidget(analyze_button)
        
        # Zone de suggestions
        suggestions_label = QLabel("Suggestions de correction :")
        self.suggestions_edit = QTextEdit()
        self.suggestions_edit.setReadOnly(True)
        self.suggestions_edit.setMaximumHeight(100)
        layout.addWidget(suggestions_label)
        layout.addWidget(self.suggestions_edit)
        
        # Zone de résultat
        result_label = QLabel("Requête SQL générée :")
        self.result_edit = QTextEdit()
        self.result_edit.setReadOnly(True)
        layout.addWidget(result_label)
        layout.addWidget(self.result_edit)
        
        self.setLayout(layout)
        
        # Connecter le signal de suggestion
        self.query_inspector.suggestion_made.connect(self._on_suggestion_made)
        
    def _analyze_query(self):
        """Analyse la description et génère la requête SQL."""
        description = self.description_edit.toPlainText()
        if not description:
            return
            
        # Vider les suggestions
        self.suggestions_edit.clear()
        
        query = self.query_inspector.analyze_query(description)
        if query:
            self.result_edit.setText(query)
            
    def _on_suggestion_made(self, suggestion: str):
        """Gère les suggestions de correction.
        
        Args:
            suggestion: Suggestion de correction
        """
        if self.show_suggestions_check.isChecked():
            self.suggestions_edit.append(suggestion) 