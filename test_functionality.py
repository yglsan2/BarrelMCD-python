#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script de test pour vérifier les fonctionnalités de BarrelMCD
"""

import sys
import json
import pandas as pd
from PyQt5.QtWidgets import QApplication
from views.main_window import MainWindow
from views.data_analyzer import DataAnalyzer
from views.mcd_drawer import MCDDrawer

def test_data_analyzer():
    """Test de l'analyseur de données"""
    print("=== Test de l'analyseur de données ===")
    
    analyzer = DataAnalyzer()
    
    # Test avec des données JSON
    test_data = {
        "users": [
            {"id": 1, "name": "John", "email": "john@example.com", "age": 30},
            {"id": 2, "name": "Jane", "email": "jane@example.com", "age": 25}
        ],
        "products": [
            {"id": 1, "name": "Laptop", "price": 999.99, "category": "Electronics"},
            {"id": 2, "name": "Mouse", "price": 29.99, "category": "Electronics"}
        ],
        "orders": [
            {"id": 1, "user_id": 1, "product_id": 1, "quantity": 1, "total": 999.99},
            {"id": 2, "user_id": 2, "product_id": 2, "quantity": 2, "total": 59.98}
        ]
    }
    
    try:
        result = analyzer.analyze_data(test_data, format_type='json')
        print("✅ Analyse JSON réussie")
        print(f"Entités détectées: {list(result['entities'].keys())}")
        print(f"Relations détectées: {len(result['relations'])}")
        return result
    except Exception as e:
        print(f"❌ Erreur lors de l'analyse JSON: {e}")
        return None

def test_mcd_drawer():
    """Test du dessinateur MCD"""
    print("\n=== Test du dessinateur MCD ===")
    
    drawer = MCDDrawer()
    
    # Données de test
    test_mcd = {
        "entities": [
            {
                "name": "User",
                "attributes": [
                    {"name": "id", "type": "INTEGER", "is_pk": True},
                    {"name": "name", "type": "VARCHAR(100)", "is_pk": False},
                    {"name": "email", "type": "VARCHAR(255)", "is_pk": False}
                ]
            },
            {
                "name": "Product",
                "attributes": [
                    {"name": "id", "type": "INTEGER", "is_pk": True},
                    {"name": "name", "type": "VARCHAR(100)", "is_pk": False},
                    {"name": "price", "type": "DECIMAL(10,2)", "is_pk": False}
                ]
            }
        ],
        "relations": [
            {
                "name": "orders",
                "entity1": "User",
                "entity2": "Product",
                "cardinality": "1:N"
            }
        ]
    }
    
    try:
        # Créer une application Qt pour tester le dessin
        app = QApplication(sys.argv)
        from PyQt5.QtWidgets import QGraphicsScene
        scene = QGraphicsScene()
        drawer.draw_mcd(scene, test_mcd)
        print("✅ Dessin MCD réussi")
        print(f"Nombre d'éléments dans la scène: {len(scene.items())}")
        return True
    except Exception as e:
        print(f"❌ Erreur lors du dessin MCD: {e}")
        return False

def test_import_export():
    """Test des fonctionnalités d'import/export"""
    print("\n=== Test des fonctionnalités d'import/export ===")
    
    # Créer des données de test
    test_csv_data = pd.DataFrame({
        'user_id': [1, 2, 3],
        'name': ['John', 'Jane', 'Bob'],
        'email': ['john@example.com', 'jane@example.com', 'bob@example.com'],
        'age': [30, 25, 35]
    })
    
    try:
        # Test export CSV
        test_csv_data.to_csv('/tmp/test_users.csv', index=False)
        print("✅ Export CSV réussi")
        
        # Test import CSV
        imported_data = pd.read_csv('/tmp/test_users.csv')
        print(f"✅ Import CSV réussi - {len(imported_data)} lignes")
        
        # Test export JSON
        test_json_data = {
            "users": test_csv_data.to_dict('records')
        }
        with open('/tmp/test_users.json', 'w') as f:
            json.dump(test_json_data, f, indent=2)
        print("✅ Export JSON réussi")
        
        return True
    except Exception as e:
        print(f"❌ Erreur lors des tests d'import/export: {e}")
        return False

def test_ui_components():
    """Test des composants UI"""
    print("\n=== Test des composants UI ===")
    
    try:
        app = QApplication(sys.argv)
        
        # Test de la fenêtre principale
        window = MainWindow()
        print("✅ Fenêtre principale créée avec succès")
        
        # Vérifier les composants principaux
        if hasattr(window, 'data_analyzer'):
            print("✅ Analyseur de données disponible")
        if hasattr(window, 'mcd_drawer'):
            print("✅ Dessinateur MCD disponible")
        if hasattr(window, 'sql_inspector'):
            print("✅ Inspecteur SQL disponible")
        
        return True
    except Exception as e:
        print(f"❌ Erreur lors des tests UI: {e}")
        return False

def main():
    """Fonction principale de test"""
    print("🚀 Démarrage des tests BarrelMCD")
    print("=" * 50)
    
    # Tests des fonctionnalités principales
    test_data_analyzer()
    test_mcd_drawer()
    test_import_export()
    test_ui_components()
    
    print("\n" + "=" * 50)
    print("✅ Tests terminés")
    print("\n📋 Recommandations d'amélioration:")
    print("1. Améliorer la détection automatique des relations")
    print("2. Ajouter plus de templates d'entités")
    print("3. Implémenter l'export vers UML")
    print("4. Ajouter la validation des modèles")
    print("5. Améliorer l'interface tactile")
    print("6. Ajouter la collaboration en temps réel")
    print("7. Implémenter l'historique des modifications")
    print("8. Ajouter des raccourcis clavier avancés")

if __name__ == "__main__":
    main() 