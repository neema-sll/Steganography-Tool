from PIL import Image, ImageDraw
import numpy as np

# Create a simple test image
img = Image.new('RGB', (500, 500), color='white')
draw = ImageDraw.Draw(img)
draw.rectangle([100, 100, 400, 400], fill='blue')
draw.text((200, 250), "TEST", fill='white')
img.save('test.jpg')
print("Created test.jpg")