from typing import Dict, List, Optional, Union
from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtGui import QColor

class CustomType(QObject):
    """Représente un type personnalisé avec ses propriétés et quantités"""
    
    # Signaux
    type_modified = pyqtSignal(str)  # Nom du type modifié
    quantity_changed = pyqtSignal(str, int)  # Nom du type, nouvelle quantité
    
    def __init__(self, name: str, base_type: str = "string", 
                 description: str = "", color: Optional[QColor] = None):
        super().__init__()
        self.name: str = name
        self.base_type: str = base_type
        self.description: str = description
        self.color: Optional[QColor] = color
        self.quantity: int = 1
        self.constraints: Dict[str, Union[str, int, float, bool]] = {}
        self.validators: List[callable] = []
        self.default_value: Optional[Union[str, int, float, bool]] = None
        
    def set_quantity(self, quantity: int) -> None:
        """Définit la quantité pour ce type
        
        Args:
            quantity: Nombre d'éléments de ce type
        """
        if quantity < 0:
            raise ValueError("La quantité ne peut pas être négative")
        self.quantity = quantity
        self.quantity_changed.emit(self.name, quantity)
        
    def add_constraint(self, name: str, value: Union[str, int, float, bool]) -> None:
        """Ajoute une contrainte au type
        
        Args:
            name: Nom de la contrainte
            value: Valeur de la contrainte
        """
        self.constraints[name] = value
        self.type_modified.emit(self.name)
        
    def add_validator(self, validator: callable) -> None:
        """Ajoute une fonction de validation
        
        Args:
            validator: Fonction qui prend une valeur et retourne un booléen
        """
        self.validators.append(validator)
        self.type_modified.emit(self.name)
        
    def validate(self, value: Union[str, int, float, bool]) -> bool:
        """Valide une valeur selon les contraintes et validateurs
        
        Args:
            value: Valeur à valider
            
        Returns:
            bool: True si la valeur est valide
        """
        # Vérification du type de base
        try:
            if self.base_type == "string":
                if not isinstance(value, str):
                    return False
            elif self.base_type == "integer":
                if not isinstance(value, int):
                    return False
            elif self.base_type == "float":
                if not isinstance(value, (int, float)):
                    return False
            elif self.base_type == "boolean":
                if not isinstance(value, bool):
                    return False
        except:
            return False
            
        # Vérification des contraintes
        for constraint_name, constraint_value in self.constraints.items():
            if constraint_name == "min_length" and len(str(value)) < constraint_value:
                return False
            elif constraint_name == "max_length" and len(str(value)) > constraint_value:
                return False
            elif constraint_name == "min_value" and value < constraint_value:
                return False
            elif constraint_name == "max_value" and value > constraint_value:
                return False
            elif constraint_name == "pattern" and not re.match(constraint_value, str(value)):
                return False
                
        # Vérification des validateurs personnalisés
        for validator in self.validators:
            if not validator(value):
                return False
                
        return True
        
    def set_default_value(self, value: Union[str, int, float, bool]) -> None:
        """Définit une valeur par défaut
        
        Args:
            value: Valeur par défaut
        """
        if self.validate(value):
            self.default_value = value
            self.type_modified.emit(self.name)
        else:
            raise ValueError("La valeur par défaut ne respecte pas les contraintes")
            
    def to_dict(self) -> Dict:
        """Convertit le type en dictionnaire pour la sérialisation
        
        Returns:
            Dict: Représentation du type
        """
        return {
            "name": self.name,
            "base_type": self.base_type,
            "description": self.description,
            "color": self.color.name() if self.color else None,
            "quantity": self.quantity,
            "constraints": self.constraints,
            "default_value": self.default_value
        }
        
    @classmethod
    def from_dict(cls, data: Dict) -> 'CustomType':
        """Crée un type à partir d'un dictionnaire
        
        Args:
            data: Données du type
            
        Returns:
            CustomType: Nouveau type
        """
        type_obj = cls(
            name=data["name"],
            base_type=data["base_type"],
            description=data["description"],
            color=QColor(data["color"]) if data["color"] else None
        )
        type_obj.quantity = data["quantity"]
        type_obj.constraints = data["constraints"]
        type_obj.default_value = data["default_value"]
        return type_obj 