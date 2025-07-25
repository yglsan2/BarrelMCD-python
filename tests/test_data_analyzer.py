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
    test_sentence = "Un client peut avoir plusieurs commandes"
    entities = ["client", "commande"]
    
    analyzer._analyze_relationship(test_sentence, entities)
    
    # Vérifier que la relation a été détectée
    assert len(analyzer.detected_relations) == 1
    relation = analyzer.detected_relations[0]
    assert relation["source"] == "client"
    assert relation["target"] == "commande"
    assert relation["type"] == "ONE_TO_MANY"

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