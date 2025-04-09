import pytest
from views.model_converter import ModelConverter, ConversionType

def test_convert_to_uml():
    """Test la conversion MCD vers UML."""
    converter = ModelConverter()
    mcd = {
        "entities": {
            "client": {
                "name": "client",
                "attributes": [
                    {"name": "id", "type": "integer", "primary_key": True},
                    {"name": "nom", "type": "varchar"}
                ]
            }
        },
        "relations": [
            {
                "name": "passe",
                "source": "client",
                "target": "commande",
                "type": "ONE_TO_MANY",
                "source_cardinality": "1",
                "target_cardinality": "*"
            }
        ]
    }
    
    uml = converter.convert_model(mcd, ConversionType.MCD_TO_UML)
    
    assert "classes" in uml
    assert "associations" in uml
    assert "generalizations" in uml
    assert "client" in uml["classes"]
    assert len(uml["associations"]) == 1

def test_convert_to_mld():
    """Test la conversion MCD vers MLD."""
    converter = ModelConverter()
    mcd = {
        "entities": {
            "client": {
                "name": "client",
                "attributes": [
                    {"name": "id", "type": "integer", "primary_key": True},
                    {"name": "nom", "type": "varchar"}
                ]
            },
            "commande": {
                "name": "commande",
                "attributes": [
                    {"name": "id", "type": "integer", "primary_key": True},
                    {"name": "date", "type": "date"}
                ]
            }
        },
        "relations": [
            {
                "name": "passe",
                "source": "client",
                "target": "commande",
                "type": "ONE_TO_MANY"
            }
        ]
    }
    
    mld = converter.convert_model(mcd, ConversionType.MCD_TO_MLD)
    
    assert "tables" in mld
    assert "foreign_keys" in mld
    assert "constraints" in mld
    assert "client" in mld["tables"]
    assert "commande" in mld["tables"]
    assert len(mld["foreign_keys"]) >= 1

def test_convert_to_sql():
    """Test la conversion MLD vers SQL."""
    converter = ModelConverter()
    mld = {
        "tables": {
            "client": {
                "name": "client",
                "columns": [
                    {"name": "id", "type": "INTEGER", "nullable": False},
                    {"name": "nom", "type": "VARCHAR", "nullable": True}
                ],
                "primary_key": ["id"]
            }
        },
        "foreign_keys": [],
        "constraints": []
    }
    
    sql = converter.convert_model(mld, ConversionType.MLD_TO_SQL)
    
    assert isinstance(sql, str)
    assert "CREATE TABLE client" in sql
    assert "id INTEGER NOT NULL" in sql
    assert "PRIMARY KEY" in sql

def test_convert_inheritance():
    """Test la conversion des relations d'héritage."""
    converter = ModelConverter()
    mcd = {
        "entities": {
            "personne": {
                "name": "personne",
                "attributes": [
                    {"name": "id", "type": "integer", "primary_key": True},
                    {"name": "nom", "type": "varchar"}
                ]
            },
            "client": {
                "name": "client",
                "attributes": [
                    {"name": "numero_client", "type": "varchar"}
                ]
            }
        },
        "relations": [
            {
                "type": "INHERITANCE",
                "parent": "personne",
                "child": "client"
            }
        ]
    }
    
    uml = converter.convert_model(mcd, ConversionType.MCD_TO_UML)
    
    assert len(uml["generalizations"]) == 1
    assert uml["generalizations"][0]["parent"] == "personne"
    assert uml["generalizations"][0]["child"] == "client"

def test_convert_many_to_many():
    """Test la conversion des relations many-to-many."""
    converter = ModelConverter()
    mcd = {
        "entities": {
            "etudiant": {
                "name": "etudiant",
                "attributes": [
                    {"name": "id", "type": "integer", "primary_key": True}
                ]
            },
            "cours": {
                "name": "cours",
                "attributes": [
                    {"name": "id", "type": "integer", "primary_key": True}
                ]
            }
        },
        "relations": [
            {
                "name": "inscription",
                "source": "etudiant",
                "target": "cours",
                "type": "MANY_TO_MANY",
                "attributes": [
                    {"name": "date_inscription", "type": "date"}
                ]
            }
        ]
    }
    
    mld = converter.convert_model(mcd, ConversionType.MCD_TO_MLD)
    
    # Vérifier la création de la table de liaison
    assert "etudiant_cours" in mld["tables"]
    junction_table = mld["tables"]["etudiant_cours"]
    assert "etudiant_id" in [col["name"] for col in junction_table["columns"]]
    assert "cours_id" in [col["name"] for col in junction_table["columns"]]
    assert "date_inscription" in [col["name"] for col in junction_table["columns"]]

def test_convert_to_uml_with_inheritance():
    """Test la conversion MCD vers UML avec héritage."""
    converter = ModelConverter()
    mcd = {
        "entities": {
            "personne": {
                "name": "personne",
                "attributes": [
                    {"name": "id", "type": "integer", "primary_key": True},
                    {"name": "nom", "type": "varchar"}
                ]
            },
            "client": {
                "name": "client",
                "attributes": [
                    {"name": "numero_client", "type": "varchar"}
                ],
                "inherits_from": "personne"
            }
        },
        "relations": []
    }
    
    uml = converter.convert_model(mcd, ConversionType.MCD_TO_UML)
    
    assert "generalizations" in uml
    assert len(uml["generalizations"]) == 1
    assert uml["generalizations"][0]["parent"] == "personne"
    assert uml["generalizations"][0]["child"] == "client"

def test_convert_to_mld_with_constraints():
    """Test la conversion MCD vers MLD avec contraintes."""
    converter = ModelConverter()
    mcd = {
        "entities": {
            "produit": {
                "name": "produit",
                "attributes": [
                    {"name": "id", "type": "integer", "primary_key": True},
                    {"name": "nom", "type": "varchar", "unique": True},
                    {"name": "prix", "type": "decimal", "check": "prix > 0"}
                ]
            }
        },
        "relations": []
    }
    
    mld = converter.convert_model(mcd, ConversionType.MCD_TO_MLD)
    
    assert "constraints" in mld
    assert len(mld["constraints"]) >= 2  # Au moins UNIQUE et CHECK
    assert any("UNIQUE" in str(c) for c in mld["constraints"])
    assert any("CHECK" in str(c) for c in mld["constraints"])

def test_convert_to_sql_with_indexes():
    """Test la conversion MLD vers SQL avec index."""
    converter = ModelConverter()
    mld = {
        "tables": {
            "client": {
                "name": "client",
                "columns": [
                    {"name": "id", "type": "INTEGER", "nullable": False},
                    {"name": "nom", "type": "VARCHAR", "nullable": True}
                ],
                "primary_key": ["id"],
                "indexes": [
                    {"name": "idx_client_nom", "columns": ["nom"]}
                ]
            }
        },
        "foreign_keys": [],
        "constraints": []
    }
    
    sql = converter.convert_model(mld, ConversionType.MLD_TO_SQL)
    
    assert "CREATE INDEX idx_client_nom" in sql
    assert "ON client (nom)" in sql

def test_invalid_conversion_type():
    """Test la gestion des types de conversion invalides."""
    converter = ModelConverter()
    mcd = {"entities": {}, "relations": []}
    
    with pytest.raises(ValueError):
        converter.convert_model(mcd, "INVALID_TYPE")

def test_empty_model_conversion():
    """Test la conversion d'un modèle vide."""
    converter = ModelConverter()
    empty_model = {"entities": {}, "relations": []}
    
    # Test conversion vers UML
    uml = converter.convert_model(empty_model, ConversionType.MCD_TO_UML)
    assert "classes" in uml
    assert len(uml["classes"]) == 0
    
    # Test conversion vers MLD
    mld = converter.convert_model(empty_model, ConversionType.MCD_TO_MLD)
    assert "tables" in mld
    assert len(mld["tables"]) == 0
    
    # Test conversion vers SQL
    sql = converter.convert_model({"tables": {}, "foreign_keys": [], "constraints": []}, 
                                ConversionType.MLD_TO_SQL)
    assert isinstance(sql, str)
    assert len(sql.strip()) == 0 