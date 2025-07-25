#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script pour convertir les fichiers SVG en PNG pour les icônes de fenêtre
"""

import os
import cairosvg

def convert_svg_to_png():
    """Convertit les fichiers SVG en PNG"""
    
    # Chemin vers le dossier logos
    logos_dir = os.path.join(os.path.dirname(__file__), "docs", "logos")
    
    # Fichiers SVG à convertir
    svg_files = [
        "BARREL v4 sans.svg",
        "BARREL v4 avec.svg"
    ]
    
    for svg_file in svg_files:
        svg_path = os.path.join(logos_dir, svg_file)
        if os.path.exists(svg_path):
            # Nom du fichier PNG de sortie
            png_name = svg_file.replace(".svg", "_converted.png")
            png_path = os.path.join(logos_dir, png_name)
            
            try:
                print(f"Conversion de {svg_file} en {png_name}...")
                cairosvg.svg2png(url=svg_path, write_to=png_path, output_width=512, output_height=512)
                print(f"✅ Conversion réussie: {png_name}")
            except Exception as e:
                print(f"❌ Erreur lors de la conversion de {svg_file}: {e}")
        else:
            print(f"⚠️ Fichier non trouvé: {svg_path}")

if __name__ == "__main__":
    convert_svg_to_png() 