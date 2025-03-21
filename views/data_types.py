from typing import Dict, List, Optional, Union
from enum import Enum

class DataTypeCategory(Enum):
    """Catégories de types de données"""
    NUMERIC = "numeric"
    TEXT = "text"
    TEMPORAL = "temporal"
    BOOLEAN = "boolean"
    ENUM = "enum"
    BINARY = "binary"
    JSON = "json"
    CUSTOM = "custom"

class DataType:
    """Classe représentant un type de données personnalisé"""
    
    def __init__(self, name: str, category: DataTypeCategory, 
                 description: str, constraints: Optional[List[str]] = None,
                 size: Optional[Union[int, Dict[str, int]]] = None,
                 values: Optional[List[str]] = None):
        self.name = name
        self.category = category
        self.description = description
        self.constraints = constraints or []
        self.size = size
        self.values = values
        
    def __str__(self) -> str:
        if self.category == DataTypeCategory.ENUM and self.values:
            return f"{self.name}({', '.join(self.values)})"
        elif self.size:
            if isinstance(self.size, dict):
                return f"{self.name}({self.size.get('precision', '')}, {self.size.get('scale', '')})"
            return f"{self.name}({self.size})"
        return self.name

class DataTypeManager:
    """Gestionnaire des types de données personnalisés"""
    
    def __init__(self):
        self.types: Dict[str, DataType] = {}
        self._initialize_default_types()
        
    def _initialize_default_types(self):
        """Initialise les types de données par défaut"""
        # Types numériques
        self.types["INTEGER"] = DataType(
            "INTEGER", DataTypeCategory.NUMERIC,
            "Nombre entier", ["NOT NULL"]
        )
        self.types["DECIMAL"] = DataType(
            "DECIMAL", DataTypeCategory.NUMERIC,
            "Nombre décimal", ["NOT NULL"],
            {"precision": 10, "scale": 2}
        )
        
        # Types textuels
        self.types["VARCHAR"] = DataType(
            "VARCHAR", DataTypeCategory.TEXT,
            "Chaîne de caractères de longueur variable",
            ["NOT NULL"], 255
        )
        self.types["TEXT"] = DataType(
            "TEXT", DataTypeCategory.TEXT,
            "Texte long", ["NOT NULL"]
        )
        
        # Types temporels
        self.types["DATE"] = DataType(
            "DATE", DataTypeCategory.TEMPORAL,
            "Date", ["NOT NULL"]
        )
        self.types["DATETIME"] = DataType(
            "DATETIME", DataTypeCategory.TEMPORAL,
            "Date et heure", ["NOT NULL"]
        )
        
        # Types booléens
        self.types["BOOLEAN"] = DataType(
            "BOOLEAN", DataTypeCategory.BOOLEAN,
            "Valeur booléenne", ["NOT NULL"],
            values=["OUI", "NON"]
        )
        
        # Types énumérés courants
        self.types["STATUT"] = DataType(
            "STATUT", DataTypeCategory.ENUM,
            "Statut d'un élément", ["NOT NULL"],
            values=["ACTIF", "INACTIF", "EN_ATTENTE"]
        )
        self.types["PRIORITE"] = DataType(
            "PRIORITE", DataTypeCategory.ENUM,
            "Niveau de priorité", ["NOT NULL"],
            values=["BASSE", "MOYENNE", "HAUTE", "URGENTE"]
        )
        
    def add_type(self, name: str, category: DataTypeCategory,
                description: str, constraints: Optional[List[str]] = None,
                size: Optional[Union[int, Dict[str, int]]] = None,
                values: Optional[List[str]] = None) -> DataType:
        """Ajoute un nouveau type de données personnalisé."""
        data_type = DataType(name, category, description, constraints, size, values)
        self.types[name] = data_type
        return data_type
        
    def get_type(self, name: str) -> Optional[DataType]:
        """Récupère un type de données par son nom."""
        return self.types.get(name)
        
    def update_type(self, name: str, **kwargs) -> Optional[DataType]:
        """Met à jour un type de données existant."""
        if name in self.types:
            data_type = self.types[name]
            for key, value in kwargs.items():
                if hasattr(data_type, key):
                    setattr(data_type, key, value)
            return data_type
        return None
        
    def delete_type(self, name: str) -> bool:
        """Supprime un type de données."""
        if name in self.types:
            del self.types[name]
            return True
        return False
        
    def get_all_types(self) -> List[DataType]:
        """Récupère tous les types de données."""
        return list(self.types.values())
        
    def get_types_by_category(self, category: DataTypeCategory) -> List[DataType]:
        """Récupère tous les types d'une catégorie donnée."""
        return [t for t in self.types.values() if t.category == category] 