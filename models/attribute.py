from typing import Optional, List, Dict, Any, Union
from decimal import Decimal
from .quantity_manager import QuantityManager, QuantityUnit, UnitDefinition

class Attribute:
    def __init__(self, name: str, data_type: str, 
                 is_primary_key: bool = False,
                 is_unique: bool = False,
                 is_not_null: bool = True,
                 default_value: Any = None,
                 quantity_unit: Optional[str] = None,
                 quantity_constraints: Optional[Dict[str, Any]] = None):
        self.name = name
        self.data_type = data_type
        self.is_primary_key = is_primary_key
        self.is_unique = is_unique
        self.is_not_null = is_not_null
        self.default_value = default_value
        self.quantity_unit = quantity_unit
        self.quantity_constraints = quantity_constraints or {}
        self.quantity_manager = QuantityManager()
        
    def set_quantity_unit(self, unit: str):
        """Définit l'unité de mesure pour cet attribut"""
        if unit and not self.quantity_manager.get_unit(unit):
            raise ValueError(f"Unité non supportée: {unit}")
        self.quantity_unit = unit
        
    def set_quantity_constraints(self, constraints: Dict[str, Any]):
        """Définit les contraintes de quantité"""
        self.quantity_constraints = constraints
        
    def validate_quantity(self, value: Union[Decimal, str, float, int]) -> bool:
        """Valide une valeur de quantité"""
        if not self.quantity_unit:
            return True
            
        try:
            if isinstance(value, str):
                value, _ = self.quantity_manager.parse_quantity(value)
            else:
                value = Decimal(str(value))
                
            return self.quantity_manager.validate_quantity(value, self.quantity_unit)
        except (ValueError, TypeError):
            return False
            
    def convert_quantity(self, value: Union[Decimal, str, float, int], 
                        target_unit: str) -> Decimal:
        """Convertit une quantité vers une autre unité"""
        if not self.quantity_unit:
            raise ValueError("Cet attribut n'a pas d'unité de mesure")
            
        try:
            if isinstance(value, str):
                value, _ = self.quantity_manager.parse_quantity(value)
            else:
                value = Decimal(str(value))
                
            return self.quantity_manager.convert(value, self.quantity_unit, target_unit)
        except (ValueError, TypeError) as e:
            raise ValueError(f"Erreur de conversion: {str(e)}")
            
    def format_quantity(self, value: Union[Decimal, str, float, int], 
                       format_str: Optional[str] = None) -> str:
        """Formate une quantité avec son unité"""
        if not self.quantity_unit:
            return str(value)
            
        try:
            if isinstance(value, str):
                value, _ = self.quantity_manager.parse_quantity(value)
            else:
                value = Decimal(str(value))
                
            return self.quantity_manager.format_quantity(value, self.quantity_unit, format_str)
        except (ValueError, TypeError) as e:
            raise ValueError(f"Erreur de formatage: {str(e)}")
            
    def get_quantity_info(self) -> Dict[str, Any]:
        """Récupère les informations sur l'unité de mesure"""
        if not self.quantity_unit:
            return {}
            
        unit_def = self.quantity_manager.get_unit(self.quantity_unit)
        if not unit_def:
            return {}
            
        return {
            "unit": self.quantity_unit,
            "category": unit_def.category.value,
            "description": unit_def.description,
            "format": unit_def.format,
            "precision": unit_def.precision,
            "min_value": unit_def.min_value,
            "max_value": unit_def.max_value,
            "constraints": self.quantity_constraints
        }
        
    def to_dict(self) -> Dict[str, Any]:
        """Convertit l'attribut en dictionnaire"""
        data = {
            "name": self.name,
            "data_type": self.data_type,
            "is_primary_key": self.is_primary_key,
            "is_unique": self.is_unique,
            "is_not_null": self.is_not_null,
            "default_value": self.default_value
        }
        
        if self.quantity_unit:
            data["quantity_unit"] = self.quantity_unit
            data["quantity_constraints"] = self.quantity_constraints
            
        return data
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Attribute':
        """Crée un attribut à partir d'un dictionnaire"""
        return cls(
            name=data["name"],
            data_type=data["data_type"],
            is_primary_key=data.get("is_primary_key", False),
            is_unique=data.get("is_unique", False),
            is_not_null=data.get("is_not_null", True),
            default_value=data.get("default_value"),
            quantity_unit=data.get("quantity_unit"),
            quantity_constraints=data.get("quantity_constraints")
        ) 