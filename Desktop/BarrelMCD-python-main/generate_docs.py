import os
import sys
from pathlib import Path
from models.doc_generator import DocGenerator
import logging

def setup_logging():
    """Configure le système de logging."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('doc_generation.log')
        ]
    )

def main():
    """Point d'entrée principal pour la génération de documentation."""
    setup_logging()
    
    # Obtenir le répertoire racine du projet
    root_dir = Path(__file__).parent
    
    # Créer le générateur de documentation
    doc_gen = DocGenerator(output_dir=root_dir / "docs")
    
    # Générer la documentation
    logging.info("Début de la génération de la documentation...")
    success = doc_gen.generate_all(str(root_dir))
    
    if success:
        logging.info("Documentation générée avec succès dans le répertoire 'docs'")
        logging.info(f"Vous pouvez ouvrir {root_dir / 'docs' / 'index.html'} dans votre navigateur")
    else:
        logging.error("Erreur lors de la génération de la documentation")
        sys.exit(1)

if __name__ == "__main__":
    main() 