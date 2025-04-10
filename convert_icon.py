from cairosvg import svg2png
from PIL import Image
import io

def svg_to_ico(svg_path, ico_path, size=(256, 256)):
    # Convertir SVG en PNG en mémoire
    png_data = svg2png(url=svg_path, output_width=size[0], output_height=size[1])
    
    # Créer une image PIL à partir des données PNG
    img = Image.open(io.BytesIO(png_data))
    
    # Sauvegarder en ICO
    img.save(ico_path, format='ICO', sizes=[(size[0], size[1])])

# Convertir le logo
svg_to_ico('images/barrelAvec.svg', 'images/icon.ico') 