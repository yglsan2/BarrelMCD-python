from PIL import Image, ImageDraw

# Créer une nouvelle image avec un fond transparent
size = (256, 256)
image = Image.new('RGBA', size, (0, 0, 0, 0))
draw = ImageDraw.Draw(image)

# Dessiner un cercle bleu
circle_color = (26, 82, 118)  # #1A5276 en RGB
draw.ellipse([50, 50, 206, 206], fill=circle_color)

# Sauvegarder en ICO
image.save('images/icon.ico', format='ICO', sizes=[(256, 256)]) 