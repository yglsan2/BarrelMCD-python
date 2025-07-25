from typing import Dict, List, Optional
from enum import Enum

class DataTypeCategory(Enum):
    TEXT = "Texte"
    NUMERIC = "Numérique"
    DATE_TIME = "Date et Heure"
    BOOLEAN = "Booléen"
    BINARY = "Binaire"
    JSON = "JSON"
    UUID = "UUID"
    ENUM = "Énumération"
    CUSTOM = "Personnalisé"

class DataType:
    def __init__(self, name: str, category: DataTypeCategory, 
                 description: str, constraints: Optional[List[str]] = None):
        self.name = name
        self.category = category
        self.description = description
        self.constraints = constraints or []
        
    def __str__(self) -> str:
        return self.name

class DataTypeManager:
    def __init__(self):
        self.types: Dict[str, DataType] = {}
        self._initialize_types()
        
    def _initialize_types(self):
        # Types de texte
        self.add_type(DataType("VARCHAR", DataTypeCategory.TEXT,
                             "Chaîne de caractères de longueur variable",
                             ["length"]))
        self.add_type(DataType("CHAR", DataTypeCategory.TEXT,
                             "Chaîne de caractères de longueur fixe",
                             ["length"]))
        self.add_type(DataType("TEXT", DataTypeCategory.TEXT,
                             "Texte de longueur illimitée"))
        self.add_type(DataType("LONGTEXT", DataTypeCategory.TEXT,
                             "Texte très long"))
        
        # Types numériques
        self.add_type(DataType("INTEGER", DataTypeCategory.NUMERIC,
                             "Nombre entier"))
        self.add_type(DataType("BIGINT", DataTypeCategory.NUMERIC,
                             "Grand nombre entier"))
        self.add_type(DataType("SMALLINT", DataTypeCategory.NUMERIC,
                             "Petit nombre entier"))
        self.add_type(DataType("DECIMAL", DataTypeCategory.NUMERIC,
                             "Nombre décimal",
                             ["precision", "scale"]))
        self.add_type(DataType("FLOAT", DataTypeCategory.NUMERIC,
                             "Nombre flottant"))
        self.add_type(DataType("DOUBLE", DataTypeCategory.NUMERIC,
                             "Nombre flottant double précision"))
        
        # Types date et heure
        self.add_type(DataType("DATE", DataTypeCategory.DATE_TIME,
                             "Date"))
        self.add_type(DataType("TIME", DataTypeCategory.DATE_TIME,
                             "Heure"))
        self.add_type(DataType("DATETIME", DataTypeCategory.DATE_TIME,
                             "Date et heure"))
        self.add_type(DataType("TIMESTAMP", DataTypeCategory.DATE_TIME,
                             "Horodatage"))
        
        # Types booléens
        self.add_type(DataType("BOOLEAN", DataTypeCategory.BOOLEAN,
                             "Valeur booléenne"))
        
        # Types binaires
        self.add_type(DataType("BLOB", DataTypeCategory.BINARY,
                             "Données binaires"))
        self.add_type(DataType("MEDIUMBLOB", DataTypeCategory.BINARY,
                             "Données binaires de taille moyenne"))
        self.add_type(DataType("LONGBLOB", DataTypeCategory.BINARY,
                             "Grandes données binaires"))
        
        # Types JSON
        self.add_type(DataType("JSON", DataTypeCategory.JSON,
                             "Données JSON"))
        
        # Types UUID
        self.add_type(DataType("UUID", DataTypeCategory.UUID,
                             "Identifiant unique universel"))
        
        # Types énumération
        self.add_type(DataType("ENUM", DataTypeCategory.ENUM,
                             "Type énuméré",
                             ["values"]))
        
    def add_type(self, data_type: DataType):
        self.types[data_type.name] = data_type
        
    def get_type(self, name: str) -> Optional[DataType]:
        return self.types.get(name)
        
    def get_types_by_category(self, category: DataTypeCategory) -> List[DataType]:
        return [t for t in self.types.values() if t.category == category]
        
    def get_all_types(self) -> List[DataType]:
        return list(self.types.values())
        
    def get_all_categories(self) -> List[DataTypeCategory]:
        return list(DataTypeCategory)
        
    def validate_type(self, type_name: str, **kwargs) -> bool:
        """Valide un type de données et ses paramètres"""
        data_type = self.get_type(type_name)
        if not data_type:
            return False
            
        # Vérification des contraintes requises
        for constraint in data_type.constraints:
            if constraint not in kwargs:
                return False
                
        return True
        
    def format_type(self, type_name: str, **kwargs) -> str:
        """Formate un type de données avec ses paramètres"""
        data_type = self.get_type(type_name)
        if not data_type:
            return "TEXT"  # Type par défaut
            
        if not data_type.constraints:
            return type_name
            
        # Construction de la chaîne avec les paramètres
        params = []
        for constraint in data_type.constraints:
            if constraint in kwargs:
                params.append(str(kwargs[constraint]))
                
        if params:
            return f"{type_name}({','.join(params)})"
            
        return type_name
        
    @staticmethod
    def get_supported_sql_dialects() -> List[str]:
        """Retourne la liste des dialectes SQL supportés"""
        return ["PostgreSQL", "MySQL", "SQLite", "Oracle", "SQL Server"]
        
    def get_type_description(self, type_name: str) -> str:
        """Retourne la description d'un type de données"""
        data_type = self.get_type(type_name)
        return data_type.description if data_type else "Type inconnu"
        
    def get_type_constraints(self, type_name: str) -> List[str]:
        """Retourne les contraintes d'un type de données"""
        data_type = self.get_type(type_name)
        return data_type.constraints if data_type else []
        
    def get_type_category(self, type_name: str) -> Optional[DataTypeCategory]:
        """Retourne la catégorie d'un type de données"""
        data_type = self.get_type(type_name)
        return data_type.category if data_type else None
