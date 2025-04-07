import pytest
from views.data_analyzer import DataAnalyzer

def test_analyze_data_with_json():
    """Test l'analyse des données au format JSON."""
    analyzer = DataAnalyzer()
    test_data = {
        "clients": [
            {
                "id": 1,
                "nom": "Dupont",
                "prenom": "Jean",
                "email": "jean.dupont@email.com"
            }
        ],
        "commandes": [
            {
                "id": 1,
                "client_id": 1,
                "date": "2024-03-20",
                "montant": 150.50
            }
        ]
    }
    
    result = analyzer.analyze_data(test_data, "json")
    
    # Vérifier la structure du résultat
    assert "entities" in result
    assert "relations" in result
    
    # Vérifier la détection des entités
    assert len(result["entities"]) >= 2
    assert any(e["name"].lower() == "client" for e in result["entities"].values())
    assert any(e["name"].lower() == "commande" for e in result["entities"].values())
    
    # Vérifier la détection des relations
    assert len(result["relations"]) >= 1
    relation = result["relations"][0]
    assert relation["source"] == "commande"
    assert relation["target"] == "client"
    assert relation["type"] == "MANY_TO_ONE"

def test_detect_entity_template():
    """Test la détection des templates d'entités."""
    analyzer = DataAnalyzer()
    test_data = {
        "id": 1,
        "nom": "Dupont",
        "prenom": "Jean",
        "email": "jean@email.com",
        "date_naissance": "1990-01-01"
    }
    
    template_name, score = analyzer.entity_templates.find_matching_template(
        list(test_data.keys())
    )
    
    assert template_name == "personne"
    assert score > 0.5

def test_analyze_relationship():
    """Test l'analyse des relations entre entités."""
    analyzer = DataAnalyzer()
    entity1 = {
        "name": "client",
        "attributes": [
            {"name": "id", "type": "integer"},
            {"name": "nom", "type": "varchar"}
        ]
    }
    entity2 = {
        "name": "commande",
        "attributes": [
            {"name": "id", "type": "integer"},
            {"name": "client_id", "type": "integer"},
            {"name": "date", "type": "date"}
        ]
    }
    
    relationship = analyzer.analyze_relationship(entity1, entity2)
    
    assert relationship is not None
    assert relationship["type"] == "ONE_TO_MANY"
    assert relationship["source"] == "client"
    assert relationship["target"] == "commande"

def test_detect_n_ary_relations():
    """Test la détection des relations n-aires."""
    analyzer = DataAnalyzer()
    test_text = "Une Commande relie un Client, un Produit et un Vendeur avec une quantité et un prix"
    
    relations = analyzer.detect_n_ary_relations(test_text)
    
    assert len(relations) == 1
    relation = relations[0]
    assert len(relation["entities"]) >= 3
    assert "Client" in relation["entities"]
    assert "Produit" in relation["entities"]
    assert "Vendeur" in relation["entities"]
    assert len(relation["attributes"]) >= 2

def test_analyze_attribute():
    """Test l'analyse des attributs."""
    analyzer = DataAnalyzer()
    test_words = ["prix", "decimal", "positif"]
    
    attr_info = analyzer._analyze_attribute(test_words)
    
    assert attr_info is not None
    assert attr_info["name"] == "prix"
    assert attr_info["type"] == "DECIMAL"
    assert "CHECK" in attr_info["constraints"][0]

def test_validate_model():
    """Test la validation du modèle."""
    analyzer = DataAnalyzer()
    analyzer.detected_entities = {
        "client": {
            "name": "client",
            "attributes": [
                {"name": "id", "type": "integer", "primary_key": True},
                {"name": "nom", "type": "varchar"}
            ],
            "primary_key": ["id"],
            "foreign_keys": []
        },
        "commande": {
            "name": "commande",
            "attributes": [
                {"name": "id", "type": "integer", "primary_key": True},
                {"name": "client_id", "type": "integer"},
                {"name": "date", "type": "date"}
            ],
            "primary_key": ["id"],
            "foreign_keys": [
                {"column": "client_id", "referenced_table": "client"}
            ]
        }
    }
    
    # La validation ne devrait pas lever d'exception
    analyzer._validate_model()
    
    # Vérifier que le modèle est toujours cohérent
    assert len(analyzer.detected_entities) == 2
    assert "client" in analyzer.detected_entities
    assert "commande" in analyzer.detected_entities

def test_detect_composite_key():
    """Test la détection des clés composées."""
    analyzer = DataAnalyzer()
    entity = {
        "name": "inscription",
        "attributes": [
            {"name": "etudiant_id", "type": "integer"},
            {"name": "cours_id", "type": "integer"},
            {"name": "date_inscription", "type": "date"}
        ]
    }
    
    primary_key = analyzer.detect_primary_key(entity)
    
    assert len(primary_key) == 2
    assert "etudiant_id" in primary_key
    assert "cours_id" in primary_key

def test_analyze_data_types():
    """Test l'analyse des types de données."""
    analyzer = DataAnalyzer()
    sample_data = [
        {"id": 1, "nom": "Dupont", "age": 25, "salaire": 35000.50},
        {"id": 2, "nom": "Martin", "age": 30, "salaire": 42000.75}
    ]
    
    data_types = analyzer.analyze_data_types(sample_data)
    
    assert data_types["id"] == "INTEGER"
    assert data_types["nom"] == "VARCHAR"
    assert data_types["age"] == "INTEGER"
    assert data_types["salaire"] == "DECIMAL"

def test_detect_constraints():
    """Test la détection des contraintes."""
    analyzer = DataAnalyzer()
    sample_data = [
        {"id": 1, "email": "test1@test.com", "age": 25},
        {"id": 2, "email": "test2@test.com", "age": 30},
        {"id": 3, "email": "test1@test.com", "age": 35}  # Email dupliqué
    ]
    
    constraints = analyzer.detect_constraints(sample_data)
    
    assert "email" in constraints
    assert "UNIQUE" in constraints["email"]
    assert "age" in constraints
    assert "CHECK" in constraints["age"]

def test_analyze_sample_size():
    """Test l'analyse de la taille des échantillons."""
    analyzer = DataAnalyzer()
    sample_data = [{"id": i} for i in range(1000)]
    
    sample_info = analyzer.analyze_sample_size(sample_data)
    
    assert sample_info["total_records"] == 1000
    assert sample_info["recommended_sample_size"] <= 1000
    assert sample_info["confidence_level"] > 0.95

def test_invalid_data_handling():
    """Test la gestion des données invalides."""
    analyzer = DataAnalyzer()
    invalid_data = [
        {"id": 1, "age": "invalid"},
        {"id": 2, "age": None},
        {"id": 3, "age": -1}
    ]
    
    analysis_result = analyzer.analyze_data(invalid_data)
    
    assert "warnings" in analysis_result
    assert len(analysis_result["warnings"]) > 0
    assert any("invalid" in str(w).lower() for w in analysis_result["warnings"]) 