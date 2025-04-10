import os
import re

def convert_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Remplacer les imports PyQt6 par PyQt5
    content = content.replace('from PyQt5.', 'from PyQt5.')
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

def main():
    # Parcourir tous les fichiers Python
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                convert_file(file_path)

if __name__ == '__main__':
    main() 