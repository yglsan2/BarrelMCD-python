from typing import Dict, List, Optional, Union, Any, Callable
from enum import Enum
from dataclasses import dataclass
from decimal import Decimal
import re

class QuantityUnit(Enum):
    """Unités de mesure supportées"""
    NONE = "sans unité"
    LENGTH = "longueur"
    MASS = "masse"
    VOLUME = "volume"
    TIME = "temps"
    SPEED = "vitesse"
    AREA = "surface"
    TEMPERATURE = "température"
    CURRENCY = "devise"
    PERCENTAGE = "pourcentage"
    CUSTOM = "personnalisé"

@dataclass
class UnitDefinition:
    """Définition d'une unité de mesure"""
    name: str
    symbol: str
    category: QuantityUnit
    conversion_factor: Decimal
    base_unit: Optional[str] = None
    description: Optional[str] = None
    format: Optional[str] = None
    min_value: Optional[Decimal] = None
    max_value: Optional[Decimal] = None
    precision: Optional[int] = None
    validators: List[Callable] = None

class QuantityManager:
    """Gestionnaire de quantités avec support pour les unités et conversions"""
    
    def __init__(self):
        self.units: Dict[str, UnitDefinition] = {}
        self._initialize_units()
        
    def _initialize_units(self):
        # Unités de longueur
        self.add_unit(UnitDefinition(
            name="mètre",
            symbol="m",
            category=QuantityUnit.LENGTH,
            conversion_factor=Decimal("1"),
            base_unit="m",
            description="Unité de base de longueur",
            format="0.00",
            precision=2
        ))
        self.add_unit(UnitDefinition(
            name="kilomètre",
            symbol="km",
            category=QuantityUnit.LENGTH,
            conversion_factor=Decimal("1000"),
            base_unit="m",
            description="1000 mètres"
        ))
        self.add_unit(UnitDefinition(
            name="centimètre",
            symbol="cm",
            category=QuantityUnit.LENGTH,
            conversion_factor=Decimal("0.01"),
            base_unit="m",
            description="0.01 mètre"
        ))
        
        # Unités de masse
        self.add_unit(UnitDefinition(
            name="kilogramme",
            symbol="kg",
            category=QuantityUnit.MASS,
            conversion_factor=Decimal("1"),
            base_unit="kg",
            description="Unité de base de masse",
            format="0.000",
            precision=3
        ))
        self.add_unit(UnitDefinition(
            name="gramme",
            symbol="g",
            category=QuantityUnit.MASS,
            conversion_factor=Decimal("0.001"),
            base_unit="kg",
            description="0.001 kilogramme"
        ))
        
        # Unités de volume
        self.add_unit(UnitDefinition(
            name="litre",
            symbol="L",
            category=QuantityUnit.VOLUME,
            conversion_factor=Decimal("1"),
            base_unit="L",
            description="Unité de base de volume",
            format="0.00",
            precision=2
        ))
        self.add_unit(UnitDefinition(
            name="millilitre",
            symbol="mL",
            category=QuantityUnit.VOLUME,
            conversion_factor=Decimal("0.001"),
            base_unit="L",
            description="0.001 litre"
        ))
        
        # Unités de temps
        self.add_unit(UnitDefinition(
            name="seconde",
            symbol="s",
            category=QuantityUnit.TIME,
            conversion_factor=Decimal("1"),
            base_unit="s",
            description="Unité de base de temps"
        ))
        self.add_unit(UnitDefinition(
            name="minute",
            symbol="min",
            category=QuantityUnit.TIME,
            conversion_factor=Decimal("60"),
            base_unit="s",
            description="60 secondes"
        ))
        self.add_unit(UnitDefinition(
            name="heure",
            symbol="h",
            category=QuantityUnit.TIME,
            conversion_factor=Decimal("3600"),
            base_unit="s",
            description="3600 secondes"
        ))
        
        # Unités monétaires
        self.add_unit(UnitDefinition(
            name="euro",
            symbol="€",
            category=QuantityUnit.CURRENCY,
            conversion_factor=Decimal("1"),
            base_unit="EUR",
            description="Unité monétaire européenne",
            format="0.00",
            precision=2
        ))
        self.add_unit(UnitDefinition(
            name="dollar",
            symbol="$",
            category=QuantityUnit.CURRENCY,
            conversion_factor=Decimal("0.85"),  # Taux de conversion exemple
            base_unit="EUR",
            description="Dollar américain"
        ))
        
        # Unités de température
        self.add_unit(UnitDefinition(
            name="celsius",
            symbol="°C",
            category=QuantityUnit.TEMPERATURE,
            conversion_factor=Decimal("1"),
            base_unit="°C",
            description="Degré Celsius",
            format="0.0",
            precision=1
        ))
        self.add_unit(UnitDefinition(
            name="fahrenheit",
            symbol="°F",
            category=QuantityUnit.TEMPERATURE,
            conversion_factor=Decimal("1.8"),
            base_unit="°C",
            description="Degré Fahrenheit"
        ))
        
    def add_unit(self, unit: UnitDefinition):
        """Ajoute une nouvelle unité de mesure"""
        self.units[unit.symbol] = unit
        
    def get_unit(self, symbol: str) -> Optional[UnitDefinition]:
        """Récupère une unité par son symbole"""
        return self.units.get(symbol)
        
    def get_units_by_category(self, category: QuantityUnit) -> List[UnitDefinition]:
        """Récupère toutes les unités d'une catégorie"""
        return [u for u in self.units.values() if u.category == category]
        
    def convert(self, value: Decimal, from_unit: str, to_unit: str) -> Decimal:
        """Convertit une valeur d'une unité à une autre"""
        from_def = self.get_unit(from_unit)
        to_def = self.get_unit(to_unit)
        
        if not from_def or not to_def:
            raise ValueError("Unité non supportée")
            
        if from_def.category != to_def.category:
            raise ValueError("Conversion impossible entre ces catégories d'unités")
            
        # Conversion spéciale pour la température
        if from_def.category == QuantityUnit.TEMPERATURE:
            if from_unit == "°C" and to_unit == "°F":
                return value * Decimal("9/5") + Decimal("32")
            elif from_unit == "°F" and to_unit == "°C":
                return (value - Decimal("32")) * Decimal("5/9")
                
        # Conversion standard
        base_value = value * from_def.conversion_factor
        return base_value / to_def.conversion_factor
        
    def format_quantity(self, value: Decimal, unit: str, format_str: Optional[str] = None) -> str:
        """Formate une quantité avec son unité"""
        unit_def = self.get_unit(unit)
        if not unit_def:
            raise ValueError("Unité non supportée")
            
        if format_str is None:
            format_str = unit_def.format or "0.00"
            
        return f"{value:{format_str}} {unit}"
        
    def parse_quantity(self, text: str) -> tuple[Decimal, str]:
        """Parse une chaîne contenant une quantité et son unité"""
        pattern = r"([-+]?\d*\.?\d+)\s*([^\d\s]+)"
        match = re.match(pattern, text)
        if not match:
            raise ValueError("Format de quantité invalide")
            
        value = Decimal(match.group(1))
        unit = match.group(2)
        
        if unit not in self.units:
            raise ValueError("Unité non supportée")
            
        return value, unit
        
    def validate_quantity(self, value: Decimal, unit: str) -> bool:
        """Valide une quantité selon les contraintes de l'unité"""
        unit_def = self.get_unit(unit)
        if not unit_def:
            return False
            
        if unit_def.min_value is not None and value < unit_def.min_value:
            return False
            
        if unit_def.max_value is not None and value > unit_def.max_value:
            return False
            
        if unit_def.validators:
            return all(validator(value) for validator in unit_def.validators)
            
        return True
        
    def get_base_unit(self, category: QuantityUnit) -> Optional[str]:
        """Récupère l'unité de base d'une catégorie"""
        units = self.get_units_by_category(category)
        for unit in units:
            if unit.base_unit == unit.symbol:
                return unit.symbol
        return None 