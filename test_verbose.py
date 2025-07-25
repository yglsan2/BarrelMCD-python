#!/usr/bin/env python3
"""
Test verbose pour identifier tous les problèmes du parseur MCD
"""

import sys
import os

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from views.markdown_mcd_parser import MarkdownMCDParser

def test_verbose_parsing():
    """Test avec mode verbose pour identifier les problèmes"""
    print("🚀 TEST VERBOSE - IDENTIFICATION DES PROBLÈMES")
    print("=" * 60)
    
    # Test 1: Cardinalités invalides
    print("\n🧪 TEST 1: CARDINALITÉS INVALIDES")
    print("-" * 40)
    
    parser = MarkdownMCDParser(verbose=True)
    
    test_cardinalities = [
        ("1,1", True, "Cardinalité standard valide"),
        ("1,n", True, "Cardinalité standard valide"),
        ("2,3", False, "Cardinalité invalide"),
        ("1", False, "Cardinalité incomplète"),
        ("a,b", False, "Cardinalité invalide"),
        ("0..1", False, "Cardinalité complexe"),
    ]
    
    for cardinality, expected, description in test_cardinalities:
        result = parser._is_cardinality_improved(cardinality)
        status = "✅" if result == expected else "❌"
        print(f"{status} {description}: {cardinality} -> {result} (attendu: {expected})")
    
    # Test 2: Héritage
    print("\n🧪 TEST 2: HÉRITAGE")
    print("-" * 40)
    
    inheritance_content = """
# Système avec Héritage

## Personne
- id (integer) : identifiant unique
- nom (varchar) : nom de la personne
- email (varchar) : adresse email

## Client hérite de Personne
- numero_client (varchar) : numéro de client
- date_inscription (date) : date d'inscription

## Employe hérite de Personne
- matricule (varchar) : matricule employé
- salaire (decimal) : salaire
"""
    
    parser2 = MarkdownMCDParser(verbose=True)
    result = parser2.parse_markdown(inheritance_content)
    
    print(f"\nRésultats héritage:")
    print(f"  - Entités: {len(result.get('entities', {}))}")
    print(f"  - Héritage: {len(result.get('inheritance', {}))}")
    print(f"  - Score: {result.get('metadata', {}).get('precision_score', 0):.1f}%")
    
    # Test 3: Score de précision différent
    print("\n🧪 TEST 3: SCORE DE PRÉCISION")
    print("-" * 40)
    
    # MCD parfait
    perfect_mcd = """
# Système Parfait

## Client
- id (integer) : identifiant unique
- nom (varchar) : nom du client
- email (varchar) : adresse email

## Commande
- id (integer) : identifiant unique
- date_commande (date) : date de commande
- montant (decimal) : montant

## Client <-> Commande : Passe
**Un client peut passer plusieurs commandes**
Client : 1,1
Commande : 0,n
"""
    
    # MCD imparfait (sans associations)
    imperfect_mcd = """
# Système Imparfait

## Client
- id (integer) : identifiant unique
- nom (varchar) : nom du client

## Commande
- id (integer) : identifiant unique
- date_commande (date) : date de commande
"""
    
    parser3 = MarkdownMCDParser(verbose=True)
    perfect_result = parser3.parse_markdown(perfect_mcd)
    perfect_score = perfect_result.get('metadata', {}).get('precision_score', 0)
    
    parser4 = MarkdownMCDParser(verbose=True)
    imperfect_result = parser4.parse_markdown(imperfect_mcd)
    imperfect_score = imperfect_result.get('metadata', {}).get('precision_score', 0)
    
    print(f"Score MCD parfait: {perfect_score:.1f}%")
    print(f"Score MCD imparfait: {imperfect_score:.1f}%")
    print(f"Différence: {perfect_score - imperfect_score:.1f}%")
    
    # Test 4: Attributs complexes
    print("\n🧪 TEST 4: ATTRIBUTS COMPLEXES")
    print("-" * 40)
    
    test_attributes = [
        "- nom (varchar(50)) : nom du client",
        "- prix (decimal(10,2)) : prix unitaire",
        "- email (varchar) NOT NULL : adresse email",
        "- statut (varchar) DEFAULT 'actif' : statut",
    ]
    
    parser5 = MarkdownMCDParser(verbose=True)
    
    for attr_text in test_attributes:
        result = parser5._parse_attribute_info_improved(attr_text)
        print(f"Attribut: {attr_text}")
        print(f"  Résultat: {result}")
        print()

def main():
    """Fonction principale"""
    test_verbose_parsing()

if __name__ == "__main__":
    main() 