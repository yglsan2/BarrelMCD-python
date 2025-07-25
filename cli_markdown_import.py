#!/usr/bin/env python3
"""
BarrelMCD - Import Markdown CLI
================================

Interface en ligne de commande pour importer des fichiers markdown
et générer des MCD complets de grande taille.
"""

import argparse
import sys
import os
from pathlib import Path
from typing import Dict, List, Optional
import json
import time

# Ajouter le répertoire parent au path pour les imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from views.markdown_mcd_parser import MarkdownMCDParser
from views.model_converter import ModelConverter


class MarkdownMCDCLI:
    """Interface CLI pour l'import de fichiers markdown vers MCD"""
    
    def __init__(self):
        self.parser = MarkdownMCDParser()
        self.converter = ModelConverter()
        
    def load_markdown_file(self, file_path: str) -> str:
        """Charge un fichier markdown avec gestion des gros fichiers"""
        try:
            file_size = os.path.getsize(file_path)
            print(f"📁 Chargement du fichier: {file_path}")
            print(f"📊 Taille du fichier: {file_size:,} octets ({file_size/1024:.1f} KB)")
            
            if file_size > 10 * 1024 * 1024:  # 10MB
                print("⚠️  Fichier volumineux détecté, traitement optimisé...")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            print(f"✅ Fichier chargé: {len(content)} caractères")
            return content
            
        except FileNotFoundError:
            print(f"❌ Erreur: Fichier '{file_path}' non trouvé")
            sys.exit(1)
        except UnicodeDecodeError:
            print(f"❌ Erreur: Problème d'encodage dans '{file_path}'")
            sys.exit(1)
        except Exception as e:
            print(f"❌ Erreur lors du chargement: {e}")
            sys.exit(1)
    
    def parse_markdown_to_mcd(self, markdown_content: str) -> Dict:
        """Parse le contenu markdown vers MCD avec gestion des gros fichiers"""
        print("🔄 Parsing du markdown vers MCD...")
        start_time = time.time()
        
        try:
            mcd_structure = self.parser.parse_markdown(markdown_content)
            
            parsing_time = time.time() - start_time
            print(f"✅ Parsing terminé en {parsing_time:.2f}s")
            
            # Statistiques détaillées
            entities_count = len(mcd_structure.get('entities', {}))
            associations_count = len(mcd_structure.get('associations', []))
            precision_score = mcd_structure.get('metadata', {}).get('precision_score', 0)
            
            print(f"📊 Statistiques MCD:")
            print(f"   • Entités: {entities_count}")
            print(f"   • Associations: {associations_count}")
            print(f"   • Score de précision: {precision_score:.1f}%")
            
            # Détails des entités
            if entities_count > 0:
                print(f"📋 Entités détectées:")
                for entity_name, entity in mcd_structure['entities'].items():
                    attrs_count = len(entity.get('attributes', []))
                    print(f"   • {entity_name}: {attrs_count} attributs")
            
            # Détails des associations
            if associations_count > 0:
                print(f"🔗 Associations détectées:")
                for assoc in mcd_structure['associations']:
                    print(f"   • {assoc['entity1']} <-> {assoc['entity2']}: {assoc['name']}")
                    print(f"     Cardinalités: {assoc['cardinality1']} / {assoc['cardinality2']}")
            
            return mcd_structure
            
        except Exception as e:
            print(f"❌ Erreur lors du parsing: {e}")
            sys.exit(1)
    
    def generate_models(self, mcd_structure: Dict, output_format: str = "all") -> Dict:
        """Génère les modèles MLD, MPD et SQL à partir du MCD"""
        print("🔄 Génération des modèles...")
        start_time = time.time()
        
        models = {"mcd": mcd_structure}
        
        try:
            # Conversion MCD -> MLD
            print("  📊 Génération MLD...")
            mld_structure = self.converter._convert_to_mld(mcd_structure)
            models["mld"] = mld_structure
            
            # Conversion MLD -> MPD
            print("  📊 Génération MPD...")
            mpd_structure = self.converter.generate_mpd(mld_structure, "mysql")
            models["mpd"] = mpd_structure
            
            # Génération SQL
            print("  📊 Génération SQL...")
            sql_script = self.converter.generate_sql_from_mpd(mpd_structure)
            models["sql"] = sql_script
            
            generation_time = time.time() - start_time
            print(f"✅ Génération terminée en {generation_time:.2f}s")
            
            # Statistiques des modèles générés
            print(f"📊 Statistiques des modèles:")
            print(f"   • Tables MLD: {len(mld_structure.get('tables', {}))}")
            print(f"   • Clés étrangères MLD: {len(mld_structure.get('foreign_keys', []))}")
            print(f"   • Tables MPD: {len(mpd_structure.get('tables', {}))}")
            print(f"   • Longueur SQL: {len(sql_script)} caractères")
            
            return models
            
        except Exception as e:
            print(f"❌ Erreur lors de la génération: {e}")
            sys.exit(1)
    
    def save_outputs(self, models: Dict, output_dir: str, base_name: str):
        """Sauvegarde les modèles générés dans différents formats"""
        print(f"💾 Sauvegarde des modèles dans: {output_dir}")
        
        # Créer le répertoire de sortie
        os.makedirs(output_dir, exist_ok=True)
        
        try:
            # Sauvegarder le MCD en JSON
            mcd_file = os.path.join(output_dir, f"{base_name}_mcd.json")
            with open(mcd_file, 'w', encoding='utf-8') as f:
                json.dump(models["mcd"], f, indent=2, ensure_ascii=False)
            print(f"✅ MCD sauvegardé: {mcd_file}")
            
            # Sauvegarder le MLD en JSON
            mld_file = os.path.join(output_dir, f"{base_name}_mld.json")
            with open(mld_file, 'w', encoding='utf-8') as f:
                json.dump(models["mld"], f, indent=2, ensure_ascii=False)
            print(f"✅ MLD sauvegardé: {mld_file}")
            
            # Sauvegarder le MPD en JSON
            mpd_file = os.path.join(output_dir, f"{base_name}_mpd.json")
            with open(mpd_file, 'w', encoding='utf-8') as f:
                json.dump(models["mpd"], f, indent=2, ensure_ascii=False)
            print(f"✅ MPD sauvegardé: {mpd_file}")
            
            # Sauvegarder le SQL
            sql_file = os.path.join(output_dir, f"{base_name}.sql")
            with open(sql_file, 'w', encoding='utf-8') as f:
                f.write(models["sql"])
            print(f"✅ SQL sauvegardé: {sql_file}")
            
            # Créer un rapport de génération
            report_file = os.path.join(output_dir, f"{base_name}_report.txt")
            self._generate_report(models, report_file)
            print(f"✅ Rapport généré: {report_file}")
            
        except Exception as e:
            print(f"❌ Erreur lors de la sauvegarde: {e}")
            sys.exit(1)
    
    def _generate_report(self, models: Dict, report_file: str):
        """Génère un rapport détaillé de la conversion"""
        mcd = models["mcd"]
        mld = models["mld"]
        mpd = models["mpd"]
        sql = models["sql"]
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write("RAPPORT DE CONVERSION MARKDOWN -> MCD\n")
            f.write("=" * 60 + "\n\n")
            
            # Statistiques MCD
            f.write("📊 STATISTIQUES MCD\n")
            f.write("-" * 30 + "\n")
            f.write(f"Entités: {len(mcd.get('entities', {}))}\n")
            f.write(f"Associations: {len(mcd.get('associations', []))}\n")
            f.write(f"Score de précision: {mcd.get('metadata', {}).get('precision_score', 0):.1f}%\n\n")
            
            # Détails des entités
            f.write("📋 ENTITÉS DÉTECTÉES\n")
            f.write("-" * 30 + "\n")
            for entity_name, entity in mcd.get('entities', {}).items():
                attrs = entity.get('attributes', [])
                f.write(f"• {entity_name}: {len(attrs)} attributs\n")
                for attr in attrs:
                    f.write(f"  - {attr['name']} ({attr['type']})\n")
            f.write("\n")
            
            # Détails des associations
            f.write("🔗 ASSOCIATIONS DÉTECTÉES\n")
            f.write("-" * 30 + "\n")
            for assoc in mcd.get('associations', []):
                f.write(f"• {assoc['entity1']} <-> {assoc['entity2']}: {assoc['name']}\n")
                f.write(f"  Cardinalités: {assoc['cardinality1']} / {assoc['cardinality2']}\n")
            f.write("\n")
            
            # Statistiques MLD
            f.write("📊 STATISTIQUES MLD\n")
            f.write("-" * 30 + "\n")
            f.write(f"Tables: {len(mld.get('tables', {}))}\n")
            f.write(f"Clés étrangères: {len(mld.get('foreign_keys', []))}\n")
            f.write(f"Contraintes: {len(mld.get('constraints', []))}\n\n")
            
            # Statistiques MPD
            f.write("📊 STATISTIQUES MPD\n")
            f.write("-" * 30 + "\n")
            f.write(f"Tables: {len(mpd.get('tables', {}))}\n")
            f.write(f"Index: {len(mpd.get('indexes', []))}\n")
            f.write(f"SGBD: {mpd.get('dbms', 'mysql')}\n\n")
            
            # Statistiques SQL
            f.write("📊 STATISTIQUES SQL\n")
            f.write("-" * 30 + "\n")
            f.write(f"Longueur du script: {len(sql)} caractères\n")
            f.write(f"Nombre de lignes: {sql.count(chr(10)) + 1}\n")
            f.write(f"Tables créées: {sql.count('CREATE TABLE')}\n")
            f.write(f"Clés étrangères: {sql.count('FOREIGN KEY')}\n")
            f.write(f"Index créés: {sql.count('CREATE INDEX')}\n")
    
    def run(self, input_file: str, output_dir: str = "output", format_only: str = "all"):
        """Exécute le processus complet d'import"""
        print("🚀 BARRELMCD - IMPORT MARKDOWN CLI")
        print("=" * 50)
        
        # Vérifier que le fichier d'entrée existe
        if not os.path.exists(input_file):
            print(f"❌ Erreur: Fichier '{input_file}' non trouvé")
            sys.exit(1)
        
        # Charger le fichier markdown
        markdown_content = self.load_markdown_file(input_file)
        
        # Parser vers MCD
        mcd_structure = self.parse_markdown_to_mcd(markdown_content)
        
        # Générer les modèles
        models = self.generate_models(mcd_structure, format_only)
        
        # Sauvegarder les résultats
        base_name = Path(input_file).stem
        self.save_outputs(models, output_dir, base_name)
        
        print("\n🎉 CONVERSION TERMINÉE AVEC SUCCÈS!")
        print(f"📁 Résultats sauvegardés dans: {output_dir}")
        print(f"📄 Fichiers générés:")
        print(f"   • {base_name}_mcd.json")
        print(f"   • {base_name}_mld.json") 
        print(f"   • {base_name}_mpd.json")
        print(f"   • {base_name}.sql")
        print(f"   • {base_name}_report.txt")


def main():
    """Fonction principale du CLI"""
    parser = argparse.ArgumentParser(
        description="BarrelMCD - Import de fichiers markdown vers MCD",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples d'utilisation:
  python cli_markdown_import.py fichier.md
  python cli_markdown_import.py fichier.md -o ./sortie
  python cli_markdown_import.py fichier.md --format mcd-only
        """
    )
    
    parser.add_argument(
        "input_file",
        help="Fichier markdown à convertir"
    )
    
    parser.add_argument(
        "-o", "--output",
        default="output",
        help="Répertoire de sortie (défaut: output)"
    )
    
    parser.add_argument(
        "--format",
        choices=["mcd-only", "mld-only", "mpd-only", "sql-only", "all"],
        default="all",
        help="Format de sortie (défaut: all)"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Mode verbeux"
    )
    
    args = parser.parse_args()
    
    # Créer et exécuter le CLI
    cli = MarkdownMCDCLI()
    cli.run(args.input_file, args.output, args.format)


if __name__ == "__main__":
    main() 