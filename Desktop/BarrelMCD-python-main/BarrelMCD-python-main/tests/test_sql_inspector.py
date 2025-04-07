import pytest
from views.sql_inspector import SQLInspector

def test_analyze_sql():
    """Test l'analyse d'un script SQL."""
    inspector = SQLInspector()
    sql_script = """
    CREATE TABLE client (
        id INTEGER PRIMARY KEY,
        nom VARCHAR(100) NOT NULL,
        email VARCHAR(255) UNIQUE
    );
    
    CREATE TABLE commande (
        id INTEGER PRIMARY KEY,
        client_id INTEGER NOT NULL,
        date DATE NOT NULL,
        FOREIGN KEY (client_id) REFERENCES client(id)
    );
    """
    
    schema = inspector.analyze_sql(sql_script)
    
    assert "tables" in schema
    assert "foreign_keys" in schema
    assert "constraints" in schema
    assert "client" in schema["tables"]
    assert "commande" in schema["tables"]
    assert len(schema["foreign_keys"]) == 1

def test_validate_schema():
    """Test la validation du schéma."""
    inspector = SQLInspector()
    inspector.schema = {
        "tables": {
            "client": {
                "name": "client",
                "columns": [
                    {"name": "id", "type": "INTEGER", "nullable": False},
                    {"name": "email", "type": "VARCHAR", "nullable": True}
                ],
                "primary_key": ["id"]
            },
            "commande": {
                "name": "commande",
                "columns": [
                    {"name": "id", "type": "INTEGER", "nullable": False},
                    {"name": "client_id", "type": "INTEGER", "nullable": False}
                ],
                "primary_key": ["id"]
            }
        },
        "foreign_keys": [
            {
                "name": "fk_commande_client",
                "table": "commande",
                "columns": ["client_id"],
                "referenced_table": "client",
                "referenced_columns": ["id"]
            }
        ],
        "constraints": []
    }
    
    issues = inspector.validate_schema()
    
    # Le schéma est valide, donc pas d'erreurs critiques
    assert not any(issue["severity"] == "error" for issue in issues)

def test_suggest_optimizations():
    """Test les suggestions d'optimisation."""
    inspector = SQLInspector()
    inspector.schema = {
        "tables": {
            "produit": {
                "name": "produit",
                "columns": [
                    {"name": "id", "type": "INTEGER", "nullable": False},
                    {"name": "nom", "type": "VARCHAR(1000)", "nullable": True},
                    {"name": "prix", "type": "INTEGER", "nullable": True}
                ],
                "primary_key": ["id"]
            }
        },
        "foreign_keys": [],
        "constraints": []
    }
    
    suggestions = inspector.suggest_optimizations()
    
    assert len(suggestions) > 0
    # Devrait suggérer TEXT pour le nom (VARCHAR trop grand)
    assert any(s["type"] == "data_type_optimization" and s["column"] == "nom" for s in suggestions)
    # Devrait suggérer DECIMAL pour le prix
    assert any(s["type"] == "data_type_optimization" and s["column"] == "prix" for s in suggestions)

def test_analyze_relationships():
    """Test l'analyse des relations."""
    inspector = SQLInspector()
    inspector.schema = {
        "tables": {
            "categorie": {
                "name": "categorie",
                "columns": [
                    {"name": "id", "type": "INTEGER", "nullable": False},
                    {"name": "parent_id", "type": "INTEGER", "nullable": True}
                ],
                "primary_key": ["id"]
            }
        },
        "foreign_keys": [
            {
                "name": "fk_categorie_parent",
                "table": "categorie",
                "columns": ["parent_id"],
                "referenced_table": "categorie",
                "referenced_columns": ["id"]
            }
        ],
        "constraints": []
    }
    
    inspector._analyze_relationships()
    
    # Vérifier la détection de la hiérarchie récursive
    assert "hierarchies" in inspector.schema
    assert any(h["type"] == "recursive" and h["table"] == "categorie" 
              for h in inspector.schema["hierarchies"])

def test_validate_naming_conventions():
    """Test la validation des conventions de nommage."""
    inspector = SQLInspector()
    inspector.schema = {
        "tables": {
            "CamelCase": {
                "name": "CamelCase",
                "columns": [
                    {"name": "ID", "type": "INTEGER", "nullable": False},
                    {"name": "Bad_Name", "type": "VARCHAR", "nullable": True}
                ],
                "primary_key": ["ID"]
            }
        },
        "foreign_keys": [],
        "constraints": []
    }
    
    issues = inspector._validate_naming_conventions(inspector.schema)
    
    assert len(issues) > 0
    assert any(issue["type"] == "naming_convention" and issue["table"] == "CamelCase" 
              for issue in issues)

def test_validate_data_types():
    """Test la validation des types de données."""
    inspector = SQLInspector()
    inspector.schema = {
        "tables": {
            "utilisateur": {
                "name": "utilisateur",
                "columns": [
                    {"name": "id", "type": "VARCHAR", "nullable": False},
                    {"name": "email", "type": "TEXT", "nullable": True},
                    {"name": "date_creation", "type": "VARCHAR", "nullable": True}
                ],
                "primary_key": ["id"]
            }
        },
        "foreign_keys": [],
        "constraints": []
    }
    
    issues = inspector._validate_data_types(inspector.schema)
    
    assert len(issues) > 0
    # L'ID devrait être un INTEGER
    assert any(issue["column"] == "id" for issue in issues)
    # L'email devrait être un VARCHAR
    assert any(issue["column"] == "email" for issue in issues)
    # La date devrait être un DATE ou TIMESTAMP
    assert any(issue["column"] == "date_creation" for issue in issues) 