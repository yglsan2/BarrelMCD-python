#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Démonstration de l'import Markdown pour BarrelMCD
"""

import sys
import os

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from views.markdown_mcd_parser import MarkdownMCDParser

def demo_basic_import():
    """Démonstration d'un import basique"""
    print("=== DÉMONSTRATION IMPORT MARKDOWN ===")
    print()
    
    # Exemple de contenu markdown
    markdown_content = """# Système de Gestion d'Étudiants

## Etudiant
- id (integer) PK : identifiant unique
- nom (varchar) : nom de l'étudiant
- prenom (varchar) : prénom de l'étudiant
- email (varchar) : adresse email
- date_naissance (date) : date de naissance
- numero_etudiant (varchar) : numéro d'étudiant

## Cours
- id (integer) PK : identifiant unique
- nom (varchar) : nom du cours
- description (text) : description du cours
- credits (integer) : nombre de crédits
- professeur (varchar) : nom du professeur

## Inscription
- id (integer) PK : identifiant unique
- date_inscription (date) : date d'inscription
- note (decimal) : note obtenue
- statut (varchar) : statut de l'inscription

### Etudiant <-> Inscription : S'inscrit
**Un étudiant peut s'inscrire à plusieurs cours**
Etudiant : 1,1
Inscription : 0,n

### Cours <-> Inscription : Comprend
**Un cours peut avoir plusieurs inscriptions**
Cours : 1,1
Inscription : 0,n
"""
    
    # Créer le parseur
    parser = MarkdownMCDParser()
    
    print("📝 Contenu Markdown d'entrée:")
    print(markdown_content)
    print()
    
    # Parser le contenu
    print("🔄 Parsing en cours...")
    mcd_structure = parser.parse_markdown(markdown_content)
    
    # Afficher les résultats
    print("✅ Résultats du parsing:")
    print(f"   📊 Entités détectées: {len(mcd_structure['entities'])}")
    print(f"   🔗 Associations détectées: {len(mcd_structure['associations'])}")
    print()
    
    # Afficher les entités
    print("🏗️  Entités:")
    for entity_name, entity_data in mcd_structure['entities'].items():
        print(f"   📋 {entity_name}")
        print(f"      🔑 Clé primaire: {entity_data.get('primary_key', 'Aucune')}")
        print(f"      📝 Attributs ({len(entity_data['attributes'])}):")
        for attr in entity_data['attributes']:
            print(f"         • {attr['name']} ({attr['type']}) : {attr.get('description', '')}")
        print()
    
    # Afficher les associations
    print("🔗 Associations:")
    for association in mcd_structure['associations']:
        print(f"   🔄 {association['name']}")
        print(f"      📍 {association['entity1']} ({association['cardinality1']}) - {association['entity2']} ({association['cardinality2']})")
        if association.get('description'):
            print(f"      📄 Description: {association['description']}")
        print()
    
    # Validation
    print("✅ Validation:")
    errors = parser.validate_mcd(mcd_structure)
    if errors:
        print("   ❌ Erreurs détectées:")
        for error in errors:
            print(f"      • {error}")
    else:
        print("   ✅ MCD valide !")
    
    return mcd_structure

def demo_advanced_features():
    """Démonstration des fonctionnalités avancées"""
    print("\n=== FONCTIONNALITÉS AVANCÉES ===")
    print()
    
    parser = MarkdownMCDParser()
    
    # Générer un template
    print("📋 Génération de template:")
    template = parser.generate_markdown_template()
    print(template)
    print()
    
    # Test avec des erreurs
    print("⚠️  Test avec erreurs:")
    invalid_content = """# MCD avec erreurs

## Client
- id (integer) PK : identifiant

### Client <-> Produit : Achete
**Association vers une entité inexistante**
Client : 1,1
Produit : 0,n
"""
    
    mcd_structure = parser.parse_markdown(invalid_content)
    errors = parser.validate_mcd(mcd_structure)
    
    print("   Erreurs détectées:")
    for error in errors:
        print(f"      • {error}")

def demo_export_json():
    """Démonstration de l'export JSON"""
    print("\n=== EXPORT JSON ===")
    print()
    
    # Créer un MCD simple
    markdown_content = """# Test Export

## Test
- id (integer) PK : identifiant
- nom (varchar) : nom
"""
    
    parser = MarkdownMCDParser()
    mcd_structure = parser.parse_markdown(markdown_content)
    
    # Exporter en JSON
    import json
    json_output = json.dumps(mcd_structure, indent=2, ensure_ascii=False)
    
    print("📄 Export JSON:")
    print(json_output)

def main():
    """Fonction principale de démonstration"""
    print("🚀 DÉMONSTRATION IMPORT MARKDOWN - BARRELMCD")
    print("=" * 50)
    
    # Démonstration basique
    demo_basic_import()
    
    # Démonstration des fonctionnalités avancées
    demo_advanced_features()
    
    # Démonstration de l'export JSON
    demo_export_json()
    
    print("\n" + "=" * 50)
    print("✅ Démonstration terminée !")
    print("\n💡 Pour utiliser cette fonctionnalité dans BarrelMCD:")
    print("   1. Lancez l'application: python main.py")
    print("   2. Cliquez sur le bouton 'Markdown' dans la barre d'outils")
    print("   3. Ou utilisez le raccourci Ctrl+M")
    print("   4. Importez votre fichier .md ou éditez directement")

if __name__ == "__main__":
    main() 