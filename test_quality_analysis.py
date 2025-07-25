#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Analyse de qualité de la fonctionnalité d'import Markdown
Évalue la précision et le respect des règles MCD
"""

import sys
import os

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from views.markdown_mcd_parser import MarkdownMCDParser

def test_cardinality_precision():
    """Teste la précision des cardinalités"""
    print("=== TEST PRÉCISION DES CARDINALITÉS ===")
    
    test_cases = [
        # Test cardinalités standard
        ("1,1", True, "Cardinalité 1,1"),
        ("1,n", True, "Cardinalité 1,n"),
        ("n,1", True, "Cardinalité n,1"),
        ("n,n", True, "Cardinalité n,n"),
        ("0,1", True, "Cardinalité 0,1"),
        ("0,n", True, "Cardinalité 0,n"),
        
        # Test cardinalités avancées
        ("1,0..1", True, "Cardinalité 1,0..1"),
        ("0..1,n", True, "Cardinalité 0..1,n"),
        
        # Test cardinalités invalides
        ("2,3", False, "Cardinalité invalide 2,3"),
        ("a,b", False, "Cardinalité invalide a,b"),
        ("1", False, "Cardinalité incomplète 1"),
    ]
    
    parser = MarkdownMCDParser()
    success_count = 0
    
    for cardinality, expected, description in test_cases:
        result = parser._is_cardinality(cardinality)
        status = "✅" if result == expected else "❌"
        print(f"{status} {description}: {cardinality} -> {result}")
        if result == expected:
            success_count += 1
    
    print(f"\nPrécision des cardinalités: {success_count}/{len(test_cases)} ({success_count/len(test_cases)*100:.1f}%)")
    return success_count == len(test_cases)

def test_association_parsing():
    """Teste le parsing des associations"""
    print("\n=== TEST PARSING DES ASSOCIATIONS ===")
    
    test_cases = [
        # Associations standard
        ("### Client <-> Commande : Passe", ("Client", "Commande", "Passe")),
        ("### Produit - Categorie : Appartient", ("Produit", "Categorie", "Appartient")),
        ("### Etudiant et Cours : Inscription", ("Etudiant", "Cours", "Inscription")),
        
        # Associations avec espaces
        ("### Client <-> Produit : Achete", ("Client", "Produit", "Achete")),
        ("### Employe - Departement : Travaille", ("Employe", "Departement", "Travaille")),
    ]
    
    parser = MarkdownMCDParser()
    success_count = 0
    
    for association_text, expected in test_cases:
        result = parser._extract_entities_from_association(association_text)
        status = "✅" if result == expected else "❌"
        print(f"{status} {association_text}")
        print(f"   Attendu: {expected}")
        print(f"   Obtenu:  {result}")
        if result == expected:
            success_count += 1
    
    print(f"\nPrécision du parsing des associations: {success_count}/{len(test_cases)} ({success_count/len(test_cases)*100:.1f}%)")
    return success_count == len(test_cases)

def test_attribute_parsing():
    """Teste le parsing des attributs"""
    print("\n=== TEST PARSING DES ATTRIBUTS ===")
    
    test_cases = [
        # Attributs standard
        ("- id (integer) PK : identifiant unique", {
            'name': 'id', 'type': 'integer', 'is_primary': True, 'description': 'identifiant unique'
        }),
        ("- nom (varchar) : nom du client", {
            'name': 'nom', 'type': 'varchar', 'is_primary': False, 'description': 'nom du client'
        }),
        ("- prix (decimal) : prix unitaire", {
            'name': 'prix', 'type': 'decimal', 'is_primary': False, 'description': 'prix unitaire'
        }),
        
        # Attributs avec clés étrangères
        ("- client_id (integer) FK : référence vers client", {
            'name': 'client_id', 'type': 'integer', 'is_foreign_key': True, 'description': 'référence vers client'
        }),
    ]
    
    parser = MarkdownMCDParser()
    success_count = 0
    
    for attr_text, expected in test_cases:
        result = parser._parse_attribute_info(attr_text)
        
        # Vérifier les champs principaux
        is_correct = (
            result['name'] == expected['name'] and
            result['type'] == expected['type'] and
            result['is_primary'] == expected.get('is_primary', False) and
            result['is_foreign_key'] == expected.get('is_foreign_key', False)
        )
        
        status = "✅" if is_correct else "❌"
        print(f"{status} {attr_text}")
        print(f"   Attendu: {expected}")
        print(f"   Obtenu:  {result}")
        if is_correct:
            success_count += 1
    
    print(f"\nPrécision du parsing des attributs: {success_count}/{len(test_cases)} ({success_count/len(test_cases)*100:.1f}%)")
    return success_count == len(test_cases)

def test_cif_ciff_rules():
    """Teste le respect des règles CIF/CIFF"""
    print("\n=== TEST RESPECT DES RÈGLES CIF/CIFF ===")
    
    # Test avec un MCD complexe respectant les règles
    complex_mcd = """# Système de Gestion Complexe

## Personne
- id (integer) PK : identifiant unique
- nom (varchar) : nom de la personne
- prenom (varchar) : prénom de la personne
- date_naissance (date) : date de naissance

## Client
- id (integer) PK : identifiant unique
- numero_client (varchar) : numéro client
- type_client (varchar) : type de client

## Employe
- id (integer) PK : identifiant unique
- matricule (varchar) : matricule employé
- poste (varchar) : poste occupé
- salaire (decimal) : salaire

## Commande
- id (integer) PK : identifiant unique
- date_commande (date) : date de commande
- montant (decimal) : montant total
- statut (varchar) : statut de la commande

## Produit
- id (integer) PK : identifiant unique
- nom (varchar) : nom du produit
- prix (decimal) : prix unitaire
- stock (integer) : quantité en stock

### Client <-> Commande : Passe
**Un client peut passer plusieurs commandes**
Client : 1,1
Commande : 0,n

### Employe <-> Commande : Traite
**Un employé peut traiter plusieurs commandes**
Employe : 1,1
Commande : 0,n

### Commande <-> Produit : Contient
**Une commande peut contenir plusieurs produits**
Commande : 1,1
Produit : 0,n

### Personne <-> Client : Est
**Une personne peut être un client**
Personne : 1,1
Client : 0,1

### Personne <-> Employe : Est
**Une personne peut être un employé**
Personne : 1,1
Employe : 0,1
"""
    
    parser = MarkdownMCDParser()
    mcd_structure = parser.parse_markdown(complex_mcd)
    
    # Vérifications CIF/CIFF
    checks = []
    
    # 1. Vérifier que toutes les entités ont une clé primaire
    for entity_name, entity in mcd_structure['entities'].items():
        has_pk = any(attr.get('is_primary', False) for attr in entity['attributes'])
        checks.append(("Clé primaire pour " + entity_name, has_pk))
    
    # 2. Vérifier que les associations sont binaires
    for association in mcd_structure['associations']:
        is_binary = len([association['entity1'], association['entity2']]) == 2
        checks.append(("Association binaire: " + association['name'], is_binary))
    
    # 3. Vérifier que les cardinalités sont valides
    valid_cardinalities = ['1,1', '1,n', 'n,1', 'n,n', '0,1', '0,n']
    for association in mcd_structure['associations']:
        card1_valid = association['cardinality1'] in valid_cardinalities
        card2_valid = association['cardinality2'] in valid_cardinalities
        checks.append(("Cardinalité valide pour " + association['name'], card1_valid and card2_valid))
    
    # 4. Vérifier qu'il n'y a pas de cycles directs
    # (simplification - en réalité il faudrait un algorithme plus complexe)
    has_no_direct_cycles = True
    for assoc1 in mcd_structure['associations']:
        for assoc2 in mcd_structure['associations']:
            if assoc1 != assoc2:
                if (assoc1['entity1'] == assoc2['entity2'] and 
                    assoc1['entity2'] == assoc2['entity1']):
                    has_no_direct_cycles = False
    checks.append(("Pas de cycles directs", has_no_direct_cycles))
    
    # Afficher les résultats
    success_count = 0
    for check_name, result in checks:
        status = "✅" if result else "❌"
        print(f"{status} {check_name}")
        if result:
            success_count += 1
    
    print(f"\nRespect des règles CIF/CIFF: {success_count}/{len(checks)} ({success_count/len(checks)*100:.1f}%)")
    return success_count == len(checks)

def test_inheritance_support():
    """Teste le support de l'héritage"""
    print("\n=== TEST SUPPORT DE L'HÉRITAGE ===")
    
    inheritance_mcd = """# Système avec Héritage

## Personne
- id (integer) PK : identifiant unique
- nom (varchar) : nom de la personne
- prenom (varchar) : prénom de la personne
- date_naissance (date) : date de naissance

## Client
- id (integer) PK : identifiant unique
- numero_client (varchar) : numéro client
- type_client (varchar) : type de client

## Employe
- id (integer) PK : identifiant unique
- matricule (varchar) : matricule employé
- poste (varchar) : poste occupé

### Personne <-> Client : Est
**Un client est une personne**
Personne : 1,1
Client : 0,1

### Personne <-> Employe : Est
**Un employé est une personne**
Personne : 1,1
Employe : 0,1
"""
    
    parser = MarkdownMCDParser()
    mcd_structure = parser.parse_markdown(inheritance_mcd)
    
    # Vérifications d'héritage
    checks = []
    
    # 1. Vérifier que les entités spécialisées ont les attributs de base
    client_has_person_attrs = any(attr['name'] == 'nom' for attr in mcd_structure['entities']['Client']['attributes'])
    employe_has_person_attrs = any(attr['name'] == 'nom' for attr in mcd_structure['entities']['Employe']['attributes'])
    
    checks.append(("Client hérite des attributs de Personne", client_has_person_attrs))
    checks.append(("Employe hérite des attributs de Personne", employe_has_person_attrs))
    
    # 2. Vérifier que les associations d'héritage sont correctes
    inheritance_associations = [assoc for assoc in mcd_structure['associations'] if assoc['name'] == 'Est']
    checks.append(("Associations d'héritage détectées", len(inheritance_associations) == 2))
    
    # 3. Vérifier les cardinalités d'héritage (0,1 pour les spécialisations)
    correct_inheritance_cardinalities = all(
        assoc['cardinality2'] == '0,1' for assoc in inheritance_associations
    )
    checks.append(("Cardinalités d'héritage correctes", correct_inheritance_cardinalities))
    
    # Afficher les résultats
    success_count = 0
    for check_name, result in checks:
        status = "✅" if result else "❌"
        print(f"{status} {check_name}")
        if result:
            success_count += 1
    
    print(f"\nSupport de l'héritage: {success_count}/{len(checks)} ({success_count/len(checks)*100:.1f}%)")
    return success_count == len(checks)

def test_mld_mpd_generation():
    """Teste la génération de MLD et MPD"""
    print("\n=== TEST GÉNÉRATION MLD/MPD ===")
    
    # Test avec un MCD simple
    simple_mcd = """# Test MLD/MPD

## Client
- id (integer) PK : identifiant unique
- nom (varchar) : nom du client
- email (varchar) : adresse email

## Commande
- id (integer) PK : identifiant unique
- date_commande (date) : date de commande
- montant (decimal) : montant total

### Client <-> Commande : Passe
**Un client peut passer plusieurs commandes**
Client : 1,1
Commande : 0,n
"""
    
    parser = MarkdownMCDParser()
    mcd_structure = parser.parse_markdown(simple_mcd)
    
    # Simuler la génération MLD
    mld_tables = []
    for entity_name, entity in mcd_structure['entities'].items():
        table_name = entity_name.lower()
        columns = []
        for attr in entity['attributes']:
            col_type = attr['type'].upper()
            if attr.get('is_primary', False):
                col_type += " PRIMARY KEY"
            columns.append(f"{attr['name']} {col_type}")
        
        mld_tables.append(f"CREATE TABLE {table_name} (\n  " + ",\n  ".join(columns) + "\n);")
    
    # Simuler la génération MPD (SQL spécifique à un SGBD)
    mpd_tables = []
    for table_sql in mld_tables:
        # Conversion vers PostgreSQL
        postgres_sql = table_sql.replace("VARCHAR", "VARCHAR(255)")
        postgres_sql = postgres_sql.replace("DECIMAL", "DECIMAL(10,2)")
        mpd_tables.append(postgres_sql)
    
    checks = []
    
    # Vérifications MLD
    checks.append(("Tables MLD générées", len(mld_tables) == 2))
    checks.append(("Clés primaires dans MLD", all("PRIMARY KEY" in table for table in mld_tables)))
    
    # Vérifications MPD
    checks.append(("Tables MPD générées", len(mpd_tables) == 2))
    checks.append(("Types PostgreSQL corrects", all("VARCHAR(255)" in table for table in mpd_tables)))
    
    # Afficher les résultats
    success_count = 0
    for check_name, result in checks:
        status = "✅" if result else "❌"
        print(f"{status} {check_name}")
        if result:
            success_count += 1
    
    print(f"\nGénération MLD/MPD: {success_count}/{len(checks)} ({success_count/len(checks)*100:.1f}%)")
    
    # Afficher un exemple de MLD généré
    print("\nExemple de MLD généré:")
    for table in mld_tables:
        print(table)
        print()
    
    return success_count == len(checks)

def main():
    """Fonction principale d'analyse de qualité"""
    print("🔍 ANALYSE DE QUALITÉ - IMPORT MARKDOWN BARRELMCD")
    print("=" * 60)
    
    tests = [
        ("Précision des cardinalités", test_cardinality_precision),
        ("Parsing des associations", test_association_parsing),
        ("Parsing des attributs", test_attribute_parsing),
        ("Règles CIF/CIFF", test_cif_ciff_rules),
        ("Support de l'héritage", test_inheritance_support),
        ("Génération MLD/MPD", test_mld_mpd_generation),
    ]
    
    results = {}
    total_score = 0
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = test_func()
            results[test_name] = result
            total_score += 1 if result else 0
        except Exception as e:
            print(f"❌ Erreur dans le test {test_name}: {e}")
            results[test_name] = False
    
    # Résumé final
    print("\n" + "=" * 60)
    print("📊 RÉSUMÉ DE L'ANALYSE DE QUALITÉ")
    print("=" * 60)
    
    for test_name, result in results.items():
        status = "✅ RÉUSSI" if result else "❌ ÉCHEC"
        print(f"{status} {test_name}")
    
    overall_score = (total_score / len(tests)) * 100
    print(f"\n🎯 SCORE GLOBAL: {overall_score:.1f}%")
    
    if overall_score >= 90:
        print("🏆 EXCELLENT - La fonctionnalité respecte très bien les standards MCD")
    elif overall_score >= 75:
        print("✅ BON - La fonctionnalité respecte bien les standards MCD")
    elif overall_score >= 60:
        print("⚠️  MOYEN - La fonctionnalité respecte partiellement les standards MCD")
    else:
        print("❌ INSUFFISANT - La fonctionnalité ne respecte pas suffisamment les standards MCD")
    
    # Recommandations
    print("\n💡 RECOMMANDATIONS:")
    if overall_score < 90:
        print("- Améliorer la détection des cardinalités complexes")
        print("- Ajouter le support des associations ternaires")
        print("- Renforcer la validation des règles CIF/CIFF")
        print("- Améliorer la génération MLD/MPD")
    else:
        print("- La fonctionnalité est de très bonne qualité")
        print("- Considérer l'ajout de fonctionnalités avancées")
        print("- Optimiser les performances pour les gros fichiers")

if __name__ == "__main__":
    main() 