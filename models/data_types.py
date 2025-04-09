from enum import Enum
from typing import Optional, List, Callable, Any, Union, Dict

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
    GEOMETRY = "Géométrie"
    NETWORK = "Réseau"
    MONEY = "Monétaire"
    MEDIA = "Média"
    ARRAY = "Tableau"
    COMPOSITE = "Composite"

class DataType:
    def __init__(self, name: str, category: DataTypeCategory, 
                 description: str, constraints: Optional[List[str]] = None,
                 validators: Optional[List[Callable]] = None,
                 default_value: Any = None,
                 min_value: Optional[Union[int, float]] = None,
                 max_value: Optional[Union[int, float]] = None,
                 precision: Optional[int] = None,
                 scale: Optional[int] = None,
                 length: Optional[int] = None,
                 format: Optional[str] = None,
                 unit: Optional[str] = None,
                 size_bytes: Optional[int] = None):
        self.name = name
        self.category = category
        self.description = description
        self.constraints = constraints or []
        self.validators = validators or []
        self.default_value = default_value
        self.min_value = min_value
        self.max_value = max_value
        self.precision = precision
        self.scale = scale
        self.length = length
        self.format = format
        self.unit = unit
        self.size_bytes = size_bytes
        
    def __str__(self) -> str:
        return self.name

class DataTypeManager:
    def __init__(self):
        self.types: Dict[str, DataType] = {}
        self._initialize_types()
        
    def _initialize_types(self):
        # Types numériques entiers
        self.add_type(DataType("INT", DataTypeCategory.NUMERIC,
                             "Entier standard",
                             size_bytes=4,
                             min_value=-2147483648,
                             max_value=2147483647))
        self.add_type(DataType("SMALLINT", DataTypeCategory.NUMERIC,
                             "Petit entier",
                             size_bytes=2,
                             min_value=-32768,
                             max_value=32767))
        self.add_type(DataType("TINYINT", DataTypeCategory.NUMERIC,
                             "Très petit entier",
                             size_bytes=1,
                             min_value=-128,
                             max_value=127))
        self.add_type(DataType("BIGINT", DataTypeCategory.NUMERIC,
                             "Grand entier",
                             size_bytes=8,
                             min_value=-9223372036854775808,
                             max_value=9223372036854775807))
        
        # Types numériques décimaux
        self.add_type(DataType("DECIMAL", DataTypeCategory.NUMERIC,
                             "Nombre décimal précis",
                             ["precision", "scale"],
                             precision=18,
                             scale=0))
        self.add_type(DataType("NUMERIC", DataTypeCategory.NUMERIC,
                             "Nombre décimal précis (synonyme de DECIMAL)",
                             ["precision", "scale"],
                             precision=18,
                             scale=0))
        self.add_type(DataType("FLOAT", DataTypeCategory.NUMERIC,
                             "Nombre à virgule flottante",
                             ["precision"],
                             precision=53))
        self.add_type(DataType("REAL", DataTypeCategory.NUMERIC,
                             "Virgule flottante 4 octets",
                             size_bytes=4))
        
        # Types texte
        self.add_type(DataType("CHAR", DataTypeCategory.TEXT,
                             "Chaîne de caractères de longueur fixe",
                             ["length"],
                             length=1))
        self.add_type(DataType("VARCHAR", DataTypeCategory.TEXT,
                             "Chaîne de caractères de longueur variable",
                             ["length"],
                             length=1))
        self.add_type(DataType("TEXT", DataTypeCategory.TEXT,
                             "Texte long (déprécié)",
                             description="Jusqu'à 2^31-1 caractères"))
        self.add_type(DataType("NCHAR", DataTypeCategory.TEXT,
                             "Chaîne unicode de longueur fixe",
                             ["length"],
                             length=1))
        self.add_type(DataType("NVARCHAR", DataTypeCategory.TEXT,
                             "Chaîne unicode de longueur variable",
                             ["length"],
                             length=1))
        self.add_type(DataType("NTEXT", DataTypeCategory.TEXT,
                             "Texte unicode long (déprécié)",
                             description="Jusqu'à 2^30-1 caractères"))
        
        # Types date et heure
        self.add_type(DataType("DATE", DataTypeCategory.DATE_TIME,
                             "Date (AAAA-MM-JJ)",
                             size_bytes=3,
                             format="YYYY-MM-DD"))
        self.add_type(DataType("DATETIME", DataTypeCategory.DATE_TIME,
                             "Date et heure (précision 1/300 sec)",
                             size_bytes=8,
                             format="YYYY-MM-DD HH:MM:SS.fff"))
        self.add_type(DataType("DATETIME2", DataTypeCategory.DATE_TIME,
                             "Date et heure avec précision choisie",
                             ["precision"],
                             precision=7,
                             format="YYYY-MM-DD HH:MM:SS.fffffff"))
        self.add_type(DataType("SMALLDATETIME", DataTypeCategory.DATE_TIME,
                             "Date et heure moins précis",
                             size_bytes=4,
                             format="YYYY-MM-DD HH:MM"))
        self.add_type(DataType("TIME", DataTypeCategory.DATE_TIME,
                             "Heure uniquement",
                             ["precision"],
                             precision=7,
                             format="HH:MM:SS.fffffff"))
        self.add_type(DataType("TIMESTAMP", DataTypeCategory.DATE_TIME,
                             "Auto-incrément de version",
                             size_bytes=8))
        
        # Types binaires
        self.add_type(DataType("BINARY", DataTypeCategory.BINARY,
                             "Données binaires fixes",
                             ["length"],
                             length=1))
        self.add_type(DataType("VARBINARY", DataTypeCategory.BINARY,
                             "Données binaires variables",
                             ["length"],
                             length=1))
        self.add_type(DataType("IMAGE", DataTypeCategory.BINARY,
                             "Données binaires longues (déprécié)",
                             description="Jusqu'à 2^31-1 octets"))
        
        # Types booléens
        self.add_type(DataType("BIT", DataTypeCategory.BOOLEAN,
                             "Booléen (0/1)",
                             size_bytes=1,
                             min_value=0,
                             max_value=1))
        
        # Types UUID
        self.add_type(DataType("UNIQUEIDENTIFIER", DataTypeCategory.UUID,
                             "Identifiant GUID",
                             size_bytes=16))
        
        # Types de texte
        self.add_type(DataType("LONGTEXT", DataTypeCategory.TEXT,
                             "Texte très long"))
        self.add_type(DataType("MEDIUMTEXT", DataTypeCategory.TEXT,
                             "Texte de longueur moyenne"))
        self.add_type(DataType("TINYTEXT", DataTypeCategory.TEXT,
                             "Texte court"))
        self.add_type(DataType("HTML", DataTypeCategory.TEXT,
                             "Contenu HTML"))
        self.add_type(DataType("XML", DataTypeCategory.TEXT,
                             "Contenu XML"))
        self.add_type(DataType("JSON", DataTypeCategory.JSON,
                             "Données JSON"))
        self.add_type(DataType("YAML", DataTypeCategory.TEXT,
                             "Contenu YAML"))
        
        # Types numériques
        self.add_type(DataType("DECIMAL", DataTypeCategory.NUMERIC,
                             "Nombre décimal",
                             ["precision", "scale"],
                             precision=10,
                             scale=2))
        self.add_type(DataType("FLOAT", DataTypeCategory.NUMERIC,
                             "Nombre flottant simple précision"))
        self.add_type(DataType("DOUBLE", DataTypeCategory.NUMERIC,
                             "Nombre flottant double précision"))
        self.add_type(DataType("REAL", DataTypeCategory.NUMERIC,
                             "Nombre réel"))
        
        # Types monétaires
        self.add_type(DataType("MONEY", DataTypeCategory.MONEY,
                             "Montant monétaire",
                             precision=19,
                             scale=4,
                             unit="EUR"))
        self.add_type(DataType("CURRENCY", DataTypeCategory.MONEY,
                             "Devise",
                             length=3))
        
        # Types date et heure
        self.add_type(DataType("DATE", DataTypeCategory.DATE_TIME,
                             "Date",
                             format="YYYY-MM-DD"))
        self.add_type(DataType("TIME", DataTypeCategory.DATE_TIME,
                             "Heure",
                             format="HH:MM:SS"))
        self.add_type(DataType("DATETIME", DataTypeCategory.DATE_TIME,
                             "Date et heure",
                             format="YYYY-MM-DD HH:MM:SS"))
        self.add_type(DataType("TIMESTAMP", DataTypeCategory.DATE_TIME,
                             "Horodatage",
                             format="YYYY-MM-DD HH:MM:SS"))
        self.add_type(DataType("YEAR", DataTypeCategory.DATE_TIME,
                             "Année",
                             format="YYYY"))
        
        # Types booléens
        self.add_type(DataType("BOOLEAN", DataTypeCategory.BOOLEAN,
                             "Valeur booléenne",
                             default_value=False))
        
        # Types binaires
        self.add_type(DataType("BLOB", DataTypeCategory.BINARY,
                             "Données binaires"))
        self.add_type(DataType("MEDIUMBLOB", DataTypeCategory.BINARY,
                             "Données binaires de taille moyenne"))
        self.add_type(DataType("LONGBLOB", DataTypeCategory.BINARY,
                             "Grandes données binaires"))
        self.add_type(DataType("TINYBLOB", DataTypeCategory.BINARY,
                             "Petites données binaires"))
        
        # Types UUID
        self.add_type(DataType("UUID", DataTypeCategory.UUID,
                             "Identifiant unique universel"))
        
        # Types énumération
        self.add_type(DataType("ENUM", DataTypeCategory.ENUM,
                             "Type énuméré",
                             ["values"]))
        self.add_type(DataType("SET", DataTypeCategory.ENUM,
                             "Ensemble de valeurs",
                             ["values"]))
        
        # Types géométriques
        self.add_type(DataType("POINT", DataTypeCategory.GEOMETRY,
                             "Point géométrique"))
        self.add_type(DataType("LINESTRING", DataTypeCategory.GEOMETRY,
                             "Ligne géométrique"))
        self.add_type(DataType("POLYGON", DataTypeCategory.GEOMETRY,
                             "Polygone"))
        self.add_type(DataType("MULTIPOINT", DataTypeCategory.GEOMETRY,
                             "Ensemble de points"))
        self.add_type(DataType("MULTILINESTRING", DataTypeCategory.GEOMETRY,
                             "Ensemble de lignes"))
        self.add_type(DataType("MULTIPOLYGON", DataTypeCategory.GEOMETRY,
                             "Ensemble de polygones"))
        self.add_type(DataType("GEOMETRYCOLLECTION", DataTypeCategory.GEOMETRY,
                             "Collection de géométries"))
        
        # Types réseau
        self.add_type(DataType("INET", DataTypeCategory.NETWORK,
                             "Adresse IPv4 ou IPv6"))
        self.add_type(DataType("CIDR", DataTypeCategory.NETWORK,
                             "Bloc d'adresses IP"))
        self.add_type(DataType("MACADDR", DataTypeCategory.NETWORK,
                             "Adresse MAC"))
        
        # Types média
        self.add_type(DataType("IMAGE", DataTypeCategory.MEDIA,
                             "Image",
                             format="base64"))
        self.add_type(DataType("AUDIO", DataTypeCategory.MEDIA,
                             "Audio",
                             format="base64"))
        self.add_type(DataType("VIDEO", DataTypeCategory.MEDIA,
                             "Vidéo",
                             format="base64"))
        
        # Types tableau
        self.add_type(DataType("ARRAY", DataTypeCategory.ARRAY,
                             "Tableau de valeurs",
                             ["element_type"]))
        
        # Types composite
        self.add_type(DataType("COMPOSITE", DataTypeCategory.COMPOSITE,
                             "Type composite",
                             ["fields"])) 