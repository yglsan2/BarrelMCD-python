import os
import platform
import subprocess
import sys

def build_windows():
    """Build pour Windows"""
    subprocess.run([
        'pyinstaller',
        '--name=BarrelMCD',
        '--windowed',
        '--onefile',
        '--debug=all',  # Active le mode debug
        '--clean',      # Nettoie le cache
        '--log-level=DEBUG',  # Log détaillé
        '--hidden-import=PyQt5.QtCore',
        '--hidden-import=PyQt5.QtGui',
        '--hidden-import=PyQt5.QtWidgets',
        '--hidden-import=PyQt5.sip',
        '--hidden-import=PyQt5.QtGui.QScreen',
        '--hidden-import=views.loop_animations',
        '--hidden-import=views.main_window',
        '--hidden-import=views.model_manager',
        '--hidden-import=views.data_analyzer',
        '--hidden-import=views.sql_generator',
        '--hidden-import=models.attribute',
        '--hidden-import=models.model',
        '--hidden-import=models.data_types',
        '--hidden-import=models.quantity_manager',
        '--hidden-import=typing',
        'main.py'
    ])

def build_linux():
    """Build pour Linux"""
    subprocess.run([
        'pyinstaller',
        '--name=BarrelMCD',
        '--onefile',
        '--debug=all',
        '--clean',
        '--log-level=DEBUG',
        '--hidden-import=PyQt5.QtCore',
        '--hidden-import=PyQt5.QtGui',
        '--hidden-import=PyQt5.QtWidgets',
        '--hidden-import=PyQt5.sip',
        '--hidden-import=PyQt5.QtGui.QScreen',
        '--hidden-import=views.loop_animations',
        '--hidden-import=views.main_window',
        '--hidden-import=views.model_manager',
        '--hidden-import=views.data_analyzer',
        '--hidden-import=views.sql_generator',
        '--hidden-import=models.attribute',
        '--hidden-import=models.model',
        '--hidden-import=models.data_types',
        '--hidden-import=models.quantity_manager',
        '--hidden-import=typing',
        'main.py'
    ])

def build_macos():
    """Build pour macOS"""
    # Créer le setup.py pour py2app
    with open('setup.py', 'w') as f:
        f.write('''
from setuptools import setup

APP = ['main.py']
DATA_FILES = [
    ('css', ['css']),
    ('js', ['js']),
    ('images', ['images']),
    ('views', ['views']),
    ('models', ['models']),
]
OPTIONS = {
    'argv_emulation': True,
    'packages': ['PyQt5'],
    'iconfile': 'images/barrelAvec.svg',
    'debug': True,
    'strip': False,
    'plist': {
        'CFBundleName': 'BarrelMCD',
        'CFBundleDisplayName': 'BarrelMCD',
        'CFBundleGetInfoString': "Application de modélisation de données",
        'CFBundleVersion': "1.0.0",
        'CFBundleShortVersionString': "1.0.0",
        'NSHighResolutionCapable': True,
    }
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
''')
    # Installer py2app si nécessaire
    subprocess.run([sys.executable, '-m', 'pip', 'install', 'py2app'])
    # Construire l'application
    subprocess.run([sys.executable, 'setup.py', 'py2app', '-A'])  # -A pour le mode alias (développement)

def main():
    """Fonction principale de build"""
    system = platform.system().lower()
    
    print(f"Construction pour {system}...")
    
    try:
        if system == 'windows':
            build_windows()
        elif system == 'linux':
            build_linux()
        elif system == 'darwin':  # macOS
            build_macos()
        else:
            print(f"Système d'exploitation non supporté : {system}")
            sys.exit(1)
        
        print("Construction terminée !")
        
    except subprocess.CalledProcessError as e:
        print(f"Erreur lors de la construction : {e}")
        print("Vérifiez les logs dans le dossier 'build' pour plus de détails")
        sys.exit(1)
    except Exception as e:
        print(f"Erreur inattendue : {e}")
        sys.exit(1)

if __name__ == '__main__':
    main() 