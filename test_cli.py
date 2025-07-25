#!/usr/bin/env python3
"""
Test du CLI BarrelMCD
======================

Script de test pour vérifier toutes les fonctionnalités du CLI.
"""

import os
import sys
import subprocess
import json
from pathlib import Path

def test_cli_basic():
    """Test basique du CLI"""
    print("🧪 TEST CLI BASIQUE")
    print("=" * 40)
    
    # Test avec le fichier complexe
    result = subprocess.run([
        "python", "cli_markdown_import.py", 
        "examples/complex_system.md"
    ], capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ Test basique réussi")
        print(f"📊 Sortie: {len(result.stdout)} caractères")
        return True
    else:
        print("❌ Test basique échoué")
        print(f"Erreur: {result.stderr}")
        return False

def test_cli_with_output_dir():
    """Test du CLI avec répertoire de sortie personnalisé"""
    print("\n🧪 TEST CLI AVEC RÉPERTOIRE DE SORTIE")
    print("=" * 40)
    
    output_dir = "test_output"
    
    # Nettoyer le répertoire de test
    if os.path.exists(output_dir):
        import shutil
        shutil.rmtree(output_dir)
    
    result = subprocess.run([
        "python", "cli_markdown_import.py", 
        "examples/complex_system.md",
        "-o", output_dir
    ], capture_output=True, text=True)
    
    if result.returncode == 0:
        # Vérifier que les fichiers ont été créés
        expected_files = [
            "complex_system_mcd.json",
            "complex_system_mld.json", 
            "complex_system_mpd.json",
            "complex_system.sql",
            "complex_system_report.txt"
        ]
        
        all_files_exist = True
        for file_name in expected_files:
            file_path = os.path.join(output_dir, file_name)
            if os.path.exists(file_path):
                file_size = os.path.getsize(file_path)
                print(f"✅ {file_name}: {file_size:,} octets")
            else:
                print(f"❌ {file_name}: manquant")
                all_files_exist = False
        
        return all_files_exist
    else:
        print("❌ Test avec répertoire de sortie échoué")
        print(f"Erreur: {result.stderr}")
        return False

def test_cli_formats():
    """Test des différents formats de sortie"""
    print("\n🧪 TEST DES DIFFÉRENTS FORMATS")
    print("=" * 40)
    
    formats = ["mcd-only", "mld-only", "mpd-only", "sql-only"]
    
    for format_type in formats:
        print(f"\n📊 Test format: {format_type}")
        
        output_dir = f"test_output_{format_type}"
        
        # Nettoyer le répertoire de test
        if os.path.exists(output_dir):
            import shutil
            shutil.rmtree(output_dir)
        
        result = subprocess.run([
            "python", "cli_markdown_import.py", 
            "examples/complex_system.md",
            "-o", output_dir,
            "--format", format_type
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            # Vérifier les fichiers générés selon le format
            if format_type == "mcd-only":
                expected_files = ["complex_system_mcd.json"]
            elif format_type == "mld-only":
                expected_files = ["complex_system_mld.json"]
            elif format_type == "mpd-only":
                expected_files = ["complex_system_mpd.json"]
            elif format_type == "sql-only":
                expected_files = ["complex_system.sql"]
            
            all_files_exist = True
            for file_name in expected_files:
                file_path = os.path.join(output_dir, file_name)
                if os.path.exists(file_path):
                    file_size = os.path.getsize(file_path)
                    print(f"  ✅ {file_name}: {file_size:,} octets")
                else:
                    print(f"  ❌ {file_name}: manquant")
                    all_files_exist = False
            
            if not all_files_exist:
                return False
        else:
            print(f"  ❌ Test format {format_type} échoué")
            print(f"  Erreur: {result.stderr}")
            return False
    
    return True

def test_cli_help():
    """Test de l'aide du CLI"""
    print("\n🧪 TEST AIDE CLI")
    print("=" * 40)
    
    result = subprocess.run([
        "python", "cli_markdown_import.py", 
        "--help"
    ], capture_output=True, text=True)
    
    if result.returncode == 0 and "BarrelMCD" in result.stdout:
        print("✅ Aide CLI affichée correctement")
        return True
    else:
        print("❌ Aide CLI échouée")
        return False

def test_cli_error_handling():
    """Test de la gestion d'erreurs"""
    print("\n🧪 TEST GESTION D'ERREURS")
    print("=" * 40)
    
    # Test avec un fichier inexistant
    result = subprocess.run([
        "python", "cli_markdown_import.py", 
        "fichier_inexistant.md"
    ], capture_output=True, text=True)
    
    if result.returncode != 0 and ("non trouvé" in result.stderr or "non trouvé" in result.stdout):
        print("✅ Gestion d'erreur fichier inexistant OK")
        return True
    else:
        print("❌ Gestion d'erreur fichier inexistant échouée")
        return False

def validate_generated_files():
    """Valide le contenu des fichiers générés"""
    print("\n🧪 VALIDATION DES FICHIERS GÉNÉRÉS")
    print("=" * 40)
    
    output_dir = "output"
    
    # Valider le fichier MCD JSON
    mcd_file = os.path.join(output_dir, "complex_system_mcd.json")
    if os.path.exists(mcd_file):
        try:
            with open(mcd_file, 'r', encoding='utf-8') as f:
                mcd_data = json.load(f)
            
            entities_count = len(mcd_data.get('entities', {}))
            associations_count = len(mcd_data.get('associations', []))
            precision_score = mcd_data.get('metadata', {}).get('precision_score', 0)
            
            print(f"✅ MCD JSON valide:")
            print(f"   • Entités: {entities_count}")
            print(f"   • Associations: {associations_count}")
            print(f"   • Score de précision: {precision_score:.1f}%")
            
            if entities_count >= 16 and associations_count >= 18 and precision_score > 90:
                print("✅ Validation MCD réussie")
            else:
                print("❌ Validation MCD échouée")
                return False
                
        except Exception as e:
            print(f"❌ Erreur validation MCD: {e}")
            return False
    
    # Valider le fichier SQL
    sql_file = os.path.join(output_dir, "complex_system.sql")
    if os.path.exists(sql_file):
        try:
            with open(sql_file, 'r', encoding='utf-8') as f:
                sql_content = f.read()
            
            create_table_count = sql_content.count("CREATE TABLE")
            foreign_key_count = sql_content.count("FOREIGN KEY")
            primary_key_count = sql_content.count("PRIMARY KEY")
            
            print(f"✅ SQL valide:")
            print(f"   • Tables créées: {create_table_count}")
            print(f"   • Clés étrangères: {foreign_key_count}")
            print(f"   • Clés primaires: {primary_key_count}")
            
            if create_table_count >= 16 and foreign_key_count >= 18:
                print("✅ Validation SQL réussie")
            else:
                print("❌ Validation SQL échouée")
                return False
                
        except Exception as e:
            print(f"❌ Erreur validation SQL: {e}")
            return False
    
    return True

def main():
    """Fonction principale de test"""
    print("🚀 TESTS CLI BARRELMCD")
    print("=" * 50)
    
    tests = [
        ("Test basique", test_cli_basic),
        ("Test répertoire de sortie", test_cli_with_output_dir),
        ("Test formats", test_cli_formats),
        ("Test aide", test_cli_help),
        ("Test gestion d'erreurs", test_cli_error_handling),
        ("Validation fichiers", validate_generated_files),
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
    
    print("\n" + "=" * 50)
    print(f"📊 RÉSULTATS DES TESTS")
    print(f"✅ Tests réussis: {passed_tests}/{total_tests}")
    print(f"📈 Taux de réussite: {passed_tests/total_tests*100:.1f}%")
    
    if passed_tests == total_tests:
        print("\n🎉 TOUS LES TESTS CLI SONT RÉUSSIS!")
        print("🚀 Le CLI BarrelMCD est prêt à être utilisé!")
    else:
        print(f"\n⚠️  {total_tests - passed_tests} test(s) ont échoué")
    
    return passed_tests == total_tests

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 