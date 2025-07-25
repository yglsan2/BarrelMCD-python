#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script de test pour le parseur Markdown MCD
"""

import sys
import os

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from views.markdown_mcd_parser import MarkdownMCDParser

def test_parser():
    """Teste le parseur markdown avec un exemple"""
    
    # Exemple de contenu markdown
    markdown_content = """# Modèle Conceptuel de Données - Système de Gestion de Bibliothèque

## Livre
- id (integer) PK : identifiant unique du livre
- titre (varchar) : titre du livre
- auteur (varchar) : nom de l'auteur
- isbn (varchar) : numéro ISBN
- annee_publication (integer) : année de publication
- nombre_pages (integer) : nombre de pages
- prix (decimal) : prix du livre
- disponible (boolean) : si le livre est disponible

## Lecteur
- id (integer) PK : identifiant unique du lecteur
- nom (varchar) : nom du lecteur
- prenom (varchar) : prénom du lecteur
- email (varchar) : adresse email
- telephone (varchar) : numéro de téléphone
- date_inscription (date) : date d'inscription
- adresse (varchar) : adresse postale

### Livre <-> Lecteur : Emprunte
**Un lecteur peut emprunter plusieurs livres**
Livre : 1,1
Lecteur : 0,n
"""
    
    # Créer le parseur
    parser = MarkdownMCDParser()
    
    # Parser le contenu
    print("Parsing du contenu markdown...")
    mcd_structure = parser.parse_markdown(markdown_content)
    
    # Afficher les résultats
    print("\n=== RÉSULTATS DU PARSING ===")
    print(f"Nombre d'entités: {len(mcd_structure['entities'])}")
    print(f"Nombre d'associations: {len(mcd_structure['associations'])}")
    
    print("\n=== ENTITÉS ===")
    for entity_name, entity_data in mcd_structure['entities'].items():
        print(f"\nEntité: {entity_name}")
        print(f"  Clé primaire: {entity_data.get('primary_key', 'Aucune')}")
        print(f"  Attributs ({len(entity_data['attributes'])}):")
        for attr in entity_data['attributes']:
            print(f"    - {attr['name']} ({attr['type']}) : {attr.get('description', '')}")
    
    print("\n=== ASSOCIATIONS ===")
    for association in mcd_structure['associations']:
        print(f"\nAssociation: {association['name']}")
        print(f"  {association['entity1']} ({association['cardinality1']}) - {association['entity2']} ({association['cardinality2']})")
        if association.get('description'):
            print(f"  Description: {association['description']}")
    
    # Valider le MCD
    print("\n=== VALIDATION ===")
    errors = parser.validate_mcd(mcd_structure)
    if errors:
        print("Erreurs de validation:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("✅ MCD valide !")
    
    # Générer un template
    print("\n=== TEMPLATE MARKDOWN ===")
    template = parser.generate_markdown_template()
    print(template)

if __name__ == "__main__":
    test_parser() 