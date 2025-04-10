from svglib.svglib import svg2rlg
from reportlab.graphics import renderPM
from PIL import Image
import io

# Charger et convertir le SVG en PNG
drawing = svg2rlg('images/barrelAvec.svg')
png_data = renderPM.drawToString(drawing, fmt='PNG')

# Convertir le PNG en ICO
img = Image.open(io.BytesIO(png_data))
img.save('images/icon.ico', format='ICO', sizes=[(256, 256)]) 