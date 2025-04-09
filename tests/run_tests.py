#!/usr/bin/env python
"""
Script pour exécuter tous les tests unitaires de BarrelMCD.
"""

import unittest
import sys
import os

def run_tests():
    """Exécute tous les tests unitaires."""
    # Ajouter le répertoire parent au chemin de recherche des modules
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    
    # Découvrir et exécuter tous les tests
    loader = unittest.TestLoader()
    start_dir = os.path.dirname(__file__)
    suite = loader.discover(start_dir, pattern='test_*.py')
    
    # Exécuter les tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Retourner le code de sortie en fonction du résultat des tests
    return 0 if result.wasSuccessful() else 1

if __name__ == '__main__':
    sys.exit(run_tests()) 