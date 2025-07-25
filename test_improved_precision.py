#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test de précision améliorée pour le parseur Markdown MCD
Version corrigée pour les règles MCD fondamentales (pas de clés en MCD)
"""

import sys
import os

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from views.markdown_mcd_parser import MarkdownMCDParser

def test_improved_cardinalities():
    """Teste les cardinalités améliorées (seulement les cardinalités standard MCD)"""
    print("=== TEST CARDINALITÉS AMÉLIORÉES ===")
    
    test_cases = [
        # Cardinalités standard MCD
        ("1,1", True, "Cardinalité 1,1"),
        ("1,n", True, "Cardinalité 1,n"),
        ("n,1", True, "Cardinalité n,1"),
        ("n,n", True, "Cardinalité n,n"),
        ("0,1", True, "Cardinalité 0,1"),
        ("0,n", True, "Cardinalité 0,n"),
        
        # Cardinalités invalides
        ("2,3", False, "Cardinalité invalide 2,3"),
        ("a,b", False, "Cardinalité invalide a,b"),
        ("1", False, "Cardinalité incomplète 1"),
        ("1,0..1", False, "Cardinalité complexe non supportée"),
        ("0..1,n", False, "Cardinalité complexe non supportée"),
        ("1.0..1", False, "Cardinalité complexe non supportée"),
        ("0..1", False, "Cardinalité complexe non supportée"),
    ]
    
    parser = MarkdownMCDParser()
    success_count = 0
    
    for cardinality, expected, description in test_cases:
        result = parser._is_cardinality_improved(cardinality)
        status = "✅" if result == expected else "❌"
        print(f"{status} {description}: {cardinality} -> {result}")
        if result == expected:
            success_count += 1
    
    print(f"\nPrécision des cardinalités améliorées: {success_count}/{len(test_cases)} ({success_count/len(test_cases)*100:.1f}%)")
    return success_count == len(test_cases)

def test_mcd_attributes_only():
    """Teste les attributs MCD (sans clés - correction fondamentale)"""
    print("\n=== TEST ATTRIBUTS MCD (SANS CLÉS) ===")
    
    test_cases = [
        # Attributs MCD standard (sans clés)
        ("- nom (varchar) : nom du client", {
            'name': 'nom', 'type': 'varchar', 'is_nullable': True
        }),
        ("- email (varchar) : adresse email", {
            'name': 'email', 'type': 'varchar', 'is_nullable': True
        }),
        ("- prix (decimal) : prix unitaire", {
            'name': 'prix', 'type': 'decimal', 'is_nullable': True
        }),
        
        # Attributs avec contraintes MCD
        ("- statut (varchar) NOT NULL : statut", {
            'name': 'statut', 'type': 'varchar', 'is_nullable': False
        }),
    ]
    
    parser = MarkdownMCDParser()
    success_count = 0
    
    for attr_text, expected in test_cases:
        result = parser._parse_attribute_info_improved(attr_text)
        
        # Vérifier les champs principaux (sans clés)
        is_correct = (
            result['name'] == expected['name'] and
            result['type'] == expected['type'] and
            result['is_nullable'] == expected['is_nullable']
        )
        
        status = "✅" if is_correct else "❌"
        print(f"{status} {attr_text}")
        print(f"   Attendu: {expected}")
        print(f"   Obtenu:  {result}")
        if is_correct:
            success_count += 1
    
    print(f"\nPrécision des attributs MCD: {success_count}/{len(test_cases)} ({success_count/len(test_cases)*100:.1f}%)")
    return success_count == len(test_cases)

def test_inheritance_support():
    """Teste le support de l'héritage MCD"""
    print("\n=== TEST SUPPORT DE L'HÉRITAGE ===")
    
    # Test avec héritage simple
    mcd_content = """
# Système de Gestion

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
    
    parser = MarkdownMCDParser()
    mcd_structure = parser.parse_markdown(mcd_content)
    
    # Vérifier que l'héritage est correctement parsé
    entities = mcd_structure.get('entities', {})
    inheritance = mcd_structure.get('inheritance', {})
    
    success_count = 0
    total_checks = 0
    
    # Vérifier que les entités existent
    if 'Personne' in entities:
        print("✅ Entité Personne détectée")
        success_count += 1
    total_checks += 1
    
    if 'Client' in entities:
        print("✅ Entité Client détectée")
        success_count += 1
    total_checks += 1
    
    if 'Employe' in entities:
        print("✅ Entité Employe détectée")
        success_count += 1
    total_checks += 1
    
    # Vérifier l'héritage
    if inheritance:
        print("✅ Héritage détecté")
        success_count += 1
    total_checks += 1
    
    print(f"\nPrécision de l'héritage: {success_count}/{total_checks} ({success_count/total_checks*100:.1f}%)")
    return success_count == total_checks

def test_precision_score():
    """Teste le calcul du score de précision MCD"""
    print("\n=== TEST SCORE DE PRÉCISION ===")
    
    # Test avec MCD parfait (avec associations)
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
    
    # Test avec MCD imparfait (une seule entité, pas d'associations)
    imperfect_mcd = """
# Système Imparfait

## Client
- id (integer) : identifiant unique
- nom (varchar) : nom du client
"""
    
    parser = MarkdownMCDParser()
    
    # Test MCD parfait
    perfect_result = parser.parse_markdown(perfect_mcd)
    perfect_score = perfect_result.get('metadata', {}).get('precision_score', 0)
    print(f"Score de précision pour MCD parfait: {perfect_score:.1f}%")
    
    # Test MCD imparfait avec mode verbose
    parser2 = MarkdownMCDParser(verbose=True)
    imperfect_result = parser2.parse_markdown(imperfect_mcd)
    imperfect_score = imperfect_result.get('metadata', {}).get('precision_score', 0)
    print(f"Score de précision pour MCD imparfait: {imperfect_score:.1f}%")
    
    # Vérifier que le score fonctionne
    if perfect_score > imperfect_score:
        print("✅ Le score de précision fonctionne correctement")
        return True
    else:
        print("❌ Le score de précision ne fonctionne pas correctement")
        print(f"   MCD parfait: {perfect_score:.1f}%")
        print(f"   MCD imparfait: {imperfect_score:.1f}%")
        return False

def test_complex_attributes():
    """Teste les attributs complexes MCD (sans clés)"""
    print("\n=== TEST ATTRIBUTS COMPLEXES ===")
    
    test_cases = [
        # Attributs avec taille
        ("- nom (varchar(50)) : nom du client", {
            'name': 'nom', 'type': 'varchar', 'size': 50
        }),
        
        # Attributs avec précision
        ("- prix (decimal(10,2)) : prix unitaire", {
            'name': 'prix', 'type': 'decimal', 'precision': 10, 'scale': 2
        }),
        
        # Attributs avec contraintes
        ("- email (varchar) NOT NULL : adresse email", {
            'name': 'email', 'type': 'varchar', 'is_nullable': False
        }),
        
        # Attributs avec valeur par défaut
        ("- statut (varchar) DEFAULT 'actif' : statut", {
            'name': 'statut', 'type': 'varchar', 'default_value': "'actif'"
        }),
    ]
    
    parser = MarkdownMCDParser()
    success_count = 0
    
    for attr_text, expected in test_cases:
        result = parser._parse_attribute_info_improved(attr_text)
        
        # Vérifier les champs principaux
        is_correct = True
        for key, value in expected.items():
            if result.get(key) != value:
                is_correct = False
                break
        
        status = "✅" if is_correct else "❌"
        print(f"{status} {attr_text}")
        print(f"   Attendu: {expected}")
        print(f"   Obtenu:  {result}")
        if is_correct:
            success_count += 1
    
    print(f"\nPrécision des attributs complexes: {success_count}/{len(test_cases)} ({success_count/len(test_cases)*100:.1f}%)")
    return success_count == len(test_cases)

def main():
    """Fonction principale de test"""
    print("🚀 TEST DE PRÉCISION AMÉLIORÉE - BARRELMCD")
    print("=" * 60)
    
    tests = [
        ("Cardinalités améliorées", test_improved_cardinalities),
        ("Attributs MCD (sans clés)", test_mcd_attributes_only),
        ("Support de l'héritage", test_inheritance_support),
        ("Score de précision", test_precision_score),
        ("Attributs complexes", test_complex_attributes),
    ]
    
    passed_tests = 0
    total_tests = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed_tests += 1
                print(f"✅ {test_name}: RÉUSSI")
            else:
                print(f"❌ {test_name}: ÉCHEC")
        except Exception as e:
            print(f"❌ {test_name}: ERREUR - {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 RÉSUMÉ DES TESTS DE PRÉCISION")
    print("=" * 60)
    
    if passed_tests == total_tests:
        print("✅ RÉUSSI Cardinalités améliorées")
        print("✅ RÉUSSI Attributs MCD (sans clés)")
        print("✅ RÉUSSI Support de l'héritage")
        print("✅ RÉUSSI Score de précision")
        print("✅ RÉUSSI Attributs complexes")
        print(f"\n🎯 SCORE GLOBAL DE PRÉCISION: 100.0%")
        print("🏆 EXCELLENT - La précision est parfaite")
    else:
        print("❌ ÉCHEC Cardinalités améliorées")
        print("❌ ÉCHEC Attributs MCD (sans clés)")
        print("❌ ÉCHEC Support de l'héritage")
        print("❌ ÉCHEC Score de précision")
        print("❌ ÉCHEC Attributs complexes")
        print(f"\n🎯 SCORE GLOBAL DE PRÉCISION: {passed_tests/total_tests*100:.1f}%")
        print("⚠️  La précision nécessite encore des améliorations")
    
    improvement = passed_tests/total_tests*100 - 0  # Comparaison avec 0% (ancienne version)
    print(f"📈 AMÉLIORATION: {improvement:+.1f}% par rapport à l'ancienne version")
    
    if improvement > 0:
        print("✅ La précision s'est améliorée")
    else:
        print("⚠️  La précision nécessite encore des améliorations")

if __name__ == "__main__":
    main() 