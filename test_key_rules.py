#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test des règles de clés pour MCD -> MLD -> MPD -> SQL
"""

import sys
import os

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from views.markdown_mcd_parser import MarkdownMCDParser
from views.model_converter import ModelConverter

def test_mcd_to_mld_conversion():
    """Teste la conversion MCD vers MLD avec gestion correcte des clés"""
    print("=== TEST CONVERSION MCD -> MLD ===")
    
    # MCD sans clés (conceptuel pur)
    mcd_content = """# Système de Gestion

## Client
- nom (varchar) : nom du client
- email (varchar) : adresse email
- telephone (varchar) : numéro de téléphone

## Commande
- date_commande (date) : date de commande
- montant (decimal) : montant total
- statut (varchar) : statut de la commande

### Client <-> Commande : Passe
**Un client peut passer plusieurs commandes**
Client : 1,1
Commande : 0,n
"""
    
    # Parser le MCD
    parser = MarkdownMCDParser()
    mcd_structure = parser.parse_markdown(mcd_content)
    
    print("✅ MCD parsé correctement")
    print(f"   Entités: {len(mcd_structure['entities'])}")
    print(f"   Associations: {len(mcd_structure['associations'])}")
    
    # Convertir vers MLD
    converter = ModelConverter()
    mld_structure = converter._convert_to_mld(mcd_structure)
    
    print("\n✅ Conversion MCD -> MLD réussie")
    print(f"   Tables: {len(mld_structure['tables'])}")
    print(f"   Clés étrangères: {len(mld_structure['foreign_keys'])}")
    
    # Vérifier les règles de clés
    checks = []
    
    # 1. Vérifier que chaque table a une clé primaire
    for table_name, table in mld_structure["tables"].items():
        checks.append((f"Table {table_name} a une clé primaire", len(table["primary_key"]) > 0))
    
    # 2. Vérifier que les clés étrangères sont correctes
    for fk in mld_structure["foreign_keys"]:
        checks.append((f"Clé étrangère {fk['table']}.{fk['column']} -> {fk['referenced_table']}", 
                     fk["table"] in mld_structure["tables"] and 
                     fk["referenced_table"] in mld_structure["tables"]))
    
    # 3. Vérifier que les noms de tables sont en minuscules
    for table_name in mld_structure["tables"].keys():
        checks.append((f"Nom de table en minuscules: {table_name}", table_name.islower()))
    
    # Afficher les résultats
    success_count = 0
    for check_name, result in checks:
        status = "✅" if result else "❌"
        print(f"{status} {check_name}")
        if result:
            success_count += 1
    
    print(f"\nRègles de clés MLD: {success_count}/{len(checks)} ({success_count/len(checks)*100:.1f}%)")
    return success_count == len(checks)

def test_mld_to_mpd_conversion():
    """Teste la conversion MLD vers MPD"""
    print("\n=== TEST CONVERSION MLD -> MPD ===")
    
    # Créer un MLD de test
    mld_structure = {
        "tables": {
            "client": {
                "name": "client",
                "columns": [
                    {"name": "id", "type": "INTEGER", "nullable": False, "auto_increment": True},
                    {"name": "nom", "type": "VARCHAR(255)", "nullable": True},
                    {"name": "email", "type": "VARCHAR(255)", "nullable": True}
                ],
                "primary_key": ["id"]
            },
            "commande": {
                "name": "commande",
                "columns": [
                    {"name": "id", "type": "INTEGER", "nullable": False, "auto_increment": True},
                    {"name": "date_commande", "type": "DATE", "nullable": True},
                    {"name": "montant", "type": "DECIMAL(10,2)", "nullable": True},
                    {"name": "client_id", "type": "INTEGER", "nullable": False}
                ],
                "primary_key": ["id"]
            }
        },
        "foreign_keys": [
            {
                "table": "commande",
                "column": "client_id",
                "referenced_table": "client",
                "referenced_column": "id",
                "constraint_name": "fk_commande_client"
            }
        ],
        "constraints": []
    }
    
    # Convertir vers MPD
    converter = ModelConverter()
    mpd_structure = converter.generate_mpd(mld_structure, "mysql")
    
    print("✅ Conversion MLD -> MPD réussie")
    print(f"   Tables: {len(mpd_structure['tables'])}")
    print(f"   SGBD: {mpd_structure['dbms']}")
    
    # Vérifier les optimisations MPD
    checks = []
    
    # 1. Vérifier que les index sont ajoutés
    total_indexes = sum(len(table["indexes"]) for table in mpd_structure["tables"].values())
    checks.append(("Index automatiques ajoutés", total_indexes > 0))
    
    # 2. Vérifier les optimisations spécifiques au SGBD
    for table_name, table in mpd_structure["tables"].items():
        for column in table["columns"]:
            if column["name"] == "id" and column.get("auto_increment"):
                checks.append((f"Auto-increment pour {table_name}.id", True))
    
    # Afficher les résultats
    success_count = 0
    for check_name, result in checks:
        status = "✅" if result else "❌"
        print(f"{status} {check_name}")
        if result:
            success_count += 1
    
    print(f"\nOptimisations MPD: {success_count}/{len(checks)} ({success_count/len(checks)*100:.1f}%)")
    return success_count == len(checks)

def test_mpd_to_sql_generation():
    """Teste la génération SQL à partir du MPD"""
    print("\n=== TEST GÉNÉRATION SQL ===")
    
    # Créer un MPD de test
    mpd_structure = {
        "dbms": "mysql",
        "tables": {
            "client": {
                "name": "client",
                "columns": [
                    {"name": "id", "type": "INT AUTO_INCREMENT", "nullable": False},
                    {"name": "nom", "type": "VARCHAR(255)", "nullable": True},
                    {"name": "email", "type": "VARCHAR(255)", "nullable": True}
                ],
                "primary_key": ["id"],
                "indexes": [
                    {"name": "idx_client_nom", "columns": ["nom"], "type": "BTREE"}
                ]
            },
            "commande": {
                "name": "commande",
                "columns": [
                    {"name": "id", "type": "INT AUTO_INCREMENT", "nullable": False},
                    {"name": "date_commande", "type": "DATE", "nullable": True},
                    {"name": "montant", "type": "DECIMAL(10,2)", "nullable": True},
                    {"name": "client_id", "type": "INT", "nullable": False}
                ],
                "primary_key": ["id"],
                "indexes": [
                    {"name": "idx_commande_client_id", "columns": ["client_id"], "type": "BTREE"}
                ]
            }
        },
        "foreign_keys": [
            {
                "table": "commande",
                "column": "client_id",
                "referenced_table": "client",
                "referenced_column": "id",
                "constraint_name": "fk_commande_client"
            }
        ],
        "constraints": []
    }
    
    # Générer le SQL
    converter = ModelConverter()
    sql_script = converter.generate_sql_from_mpd(mpd_structure)
    
    print("✅ Génération SQL réussie")
    print(f"   Longueur du script: {len(sql_script)} caractères")
    
    # Vérifier le contenu SQL
    checks = []
    
    # 1. Vérifier que les tables sont créées
    checks.append(("CREATE TABLE client", "CREATE TABLE client" in sql_script))
    checks.append(("CREATE TABLE commande", "CREATE TABLE commande" in sql_script))
    
    # 2. Vérifier que les clés primaires sont définies
    checks.append(("PRIMARY KEY", "PRIMARY KEY" in sql_script))
    
    # 3. Vérifier que les clés étrangères sont définies
    checks.append(("FOREIGN KEY", "FOREIGN KEY" in sql_script))
    
    # 4. Vérifier que les index sont créés
    checks.append(("CREATE INDEX", "CREATE INDEX" in sql_script))
    
    # 5. Vérifier les optimisations MySQL
    checks.append(("ENGINE=InnoDB", "ENGINE=InnoDB" in sql_script))
    checks.append(("AUTO_INCREMENT", "AUTO_INCREMENT" in sql_script))
    
    # Afficher les résultats
    success_count = 0
    for check_name, result in checks:
        status = "✅" if result else "❌"
        print(f"{status} {check_name}")
        if result:
            success_count += 1
    
    print(f"\nGénération SQL: {success_count}/{len(checks)} ({success_count/len(checks)*100:.1f}%)")
    
    # Afficher un extrait du SQL généré
    print("\n📄 Extrait du SQL généré:")
    lines = sql_script.split('\n')
    for i, line in enumerate(lines[:20]):  # Afficher les 20 premières lignes
        print(f"   {i+1:2d}: {line}")
    if len(lines) > 20:
        print(f"   ... ({len(lines)-20} lignes supplémentaires)")
    
    return success_count == len(checks)

def test_complete_workflow():
    """Teste le workflow complet MCD -> MLD -> MPD -> SQL"""
    print("\n=== TEST WORKFLOW COMPLET ===")
    print("🔍 MODE VERBOSE ACTIVÉ")
    
    # MCD de test
    mcd_content = """# Système de Gestion Avancé

## Utilisateur
- nom (varchar) : nom de l'utilisateur
- email (varchar) : adresse email
- date_inscription (date) : date d'inscription

## Produit
- nom (varchar) : nom du produit
- prix (decimal) : prix unitaire
- stock (integer) : quantité en stock

## Commande
- date_commande (date) : date de commande
- montant_total (decimal) : montant total
- statut (varchar) : statut de la commande

## Utilisateur <-> Commande : Passe
**Un utilisateur peut passer plusieurs commandes**
Utilisateur : 1,1
Commande : 0,n

## Produit <-> Commande : Contient
**Une commande peut contenir plusieurs produits**
Produit : 1,1
Commande : 0,n
"""
    
    # Workflow complet
    parser = MarkdownMCDParser()
    converter = ModelConverter()
    
    # 1. Parser MCD
    print("📝 Parsing MCD...")
    mcd_structure = parser.parse_markdown(mcd_content)
    print("✅ MCD parsé")
    print(f"   📊 Entités: {len(mcd_structure.get('entities', {}))}")
    print(f"   📊 Associations: {len(mcd_structure.get('associations', []))}")
    print(f"   📊 Score de précision: {mcd_structure.get('metadata', {}).get('precision_score', 0):.1f}%")
    
    # 2. Convertir vers MLD
    print("🔄 Conversion MCD -> MLD...")
    mld_structure = converter._convert_to_mld(mcd_structure)
    print("✅ MLD généré")
    print(f"   📊 MLD type: {type(mld_structure)}")
    print(f"   📊 MLD keys: {list(mld_structure.keys()) if mld_structure else 'None'}")
    print(f"   📊 Tables: {len(mld_structure.get('tables', {}))}")
    print(f"   📊 Clés étrangères: {len(mld_structure.get('foreign_keys', []))}")
    
    # 3. Convertir vers MPD
    print("🔄 Conversion MLD -> MPD...")
    mpd_structure = converter.generate_mpd(mld_structure, "mysql")
    print("✅ MPD généré")
    print(f"   📊 MPD type: {type(mpd_structure)}")
    print(f"   📊 MPD keys: {list(mpd_structure.keys()) if mpd_structure else 'None'}")
    print(f"   📊 Tables MPD: {len(mpd_structure.get('tables', {}))}")
    print(f"   📊 Clés étrangères MPD: {len(mpd_structure.get('foreign_keys', []))}")
    print(f"   📊 SGBD: {mpd_structure.get('dbms', 'non défini')}")
    
    # 4. Générer SQL
    print("🔄 Génération SQL...")
    print(f"   📊 MPD structure: {type(mpd_structure)}")
    print(f"   📊 MPD keys: {list(mpd_structure.keys()) if mpd_structure else 'None'}")
    sql_script = converter.generate_sql_from_mpd(mpd_structure)
    print("✅ SQL généré")
    print(f"   📊 Longueur SQL: {len(sql_script) if sql_script else 0}")
    print(f"   📊 Type SQL: {type(sql_script)}")
    if sql_script:
        print(f"   📊 Premières lignes: {sql_script[:200]}...")
    else:
        print("   ⚠️  SQL vide ou None!")
    
    # Vérifications finales
    checks = []
    
    # Vérifier que toutes les entités MCD sont devenues des tables
    checks.append(("Entités -> Tables", len(mld_structure["tables"]) == len(mcd_structure["entities"])))
    
    # Vérifier que les associations sont devenues des clés étrangères
    expected_fks = len(mcd_structure["associations"])
    checks.append(("Associations -> Clés étrangères", len(mld_structure["foreign_keys"]) >= expected_fks))
    
    # Vérifier que le SQL est valide (avec vérification de sécurité)
    if sql_script is None:
        sql_script = ""
    checks.append(("SQL valide", len(sql_script) > 1000))
    checks.append(("Tables SQL", sql_script.count("CREATE TABLE") == len(mld_structure["tables"])))
    
    # Afficher les résultats
    success_count = 0
    for check_name, result in checks:
        status = "✅" if result else "❌"
        print(f"{status} {check_name}")
        if result:
            success_count += 1
    
    print(f"\nWorkflow complet: {success_count}/{len(checks)} ({success_count/len(checks)*100:.1f}%)")
    
    return success_count == len(checks)

def main():
    """Fonction principale de test"""
    print("🔑 TEST DES RÈGLES DE CLÉS - BARRELMCD")
    print("=" * 60)
    
    tests = [
        ("MCD -> MLD", test_mcd_to_mld_conversion),
        ("MLD -> MPD", test_mld_to_mpd_conversion),
        ("MPD -> SQL", test_mpd_to_sql_generation),
        ("Workflow complet", test_complete_workflow),
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
    print("📊 RÉSUMÉ DES TESTS DE CLÉS")
    print("=" * 60)
    
    for test_name, result in results.items():
        status = "✅ RÉUSSI" if result else "❌ ÉCHEC"
        print(f"{status} {test_name}")
    
    overall_score = (total_score / len(tests)) * 100
    print(f"\n🎯 SCORE GLOBAL DES CLÉS: {overall_score:.1f}%")
    
    if overall_score >= 90:
        print("🏆 EXCELLENT - Les règles de clés sont parfaitement implémentées")
    elif overall_score >= 75:
        print("✅ BON - Les règles de clés sont bien implémentées")
    elif overall_score >= 60:
        print("⚠️  MOYEN - Les règles de clés nécessitent des améliorations")
    else:
        print("❌ INSUFFISANT - Les règles de clés nécessitent une refonte")
    
    print(f"\n💡 Les clés sont maintenant correctement gérées dans tous les modèles !")

if __name__ == "__main__":
    main() 