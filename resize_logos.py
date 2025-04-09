from PIL import Image
import subprocess
import os

def convert_svg_to_png(svg_path, png_path, size):
    """Convertit un fichier SVG en PNG avec ImageMagick."""
    try:
        subprocess.run([
            'magick',
            'convert',
            '-density', '300',  # Haute résolution pour la conversion
            '-resize', f'{size[0]}x{size[1]}',
            '-background', 'none',  # Fond transparent
            svg_path,
            png_path
        ], check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Erreur lors de la conversion de {svg_path}: {str(e)}")
        return False
    except FileNotFoundError:
        print("ImageMagick n'est pas installé. Veuillez l'installer depuis https://imagemagick.org/")
        return False

def create_logo_variants():
    """Crée différentes variantes des logos pour différentes tailles d'écran."""
    # Définir les tailles pour différents appareils
    sizes = {
        'desktop': (200, 200),  # Logo plus grand pour desktop (avec texte)
        'tablet': (120, 120),   # Logo moyen pour tablette (sans texte)
        'mobile': (80, 80)      # Petit logo pour mobile (sans texte)
    }
    
    # Créer les dossiers pour chaque taille s'ils n'existent pas
    for device in sizes.keys():
        os.makedirs(f"static/img/{device}", exist_ok=True)
    
    # Logo avec texte (pour desktop)
    convert_svg_to_png(
        "BARREL v4 avec.svg",
        "static/img/desktop/logo_full.png",
        sizes['desktop']
    )
    
    # Logo sans texte (pour tablette et mobile)
    for device in ['tablet', 'mobile']:
        convert_svg_to_png(
            "BARREL v4 sans.svg",
            f"static/img/{device}/logo_simple.png",
            sizes[device]
        )

def main():
    try:
        create_logo_variants()
        print("Les logos ont été générés avec succès !")
        
        # Afficher les tailles des fichiers générés
        for root, dirs, files in os.walk("static/img"):
            for file in files:
                if file.endswith('.png'):
                    path = os.path.join(root, file)
                    size = os.path.getsize(path) / 1024  # Taille en Ko
                    print(f"{path}: {size:.2f} Ko")
                    
    except Exception as e:
        print(f"Erreur lors de la génération des logos : {str(e)}")

if __name__ == "__main__":
    main() 