from PIL import Image, ImageDraw

def create_icon(size):
    # Create image with purple background
    img = Image.new('RGB', (size, size), color='#7c3aed')
    draw = ImageDraw.Draw(img)
    
    # Draw a chat bubble shape
    # Main bubble (white)
    draw.ellipse([size*0.1, size*0.2, size*0.9, size*0.85], fill='white', outline='#7c3aed', width=max(2, size//32))
    
    # Chat tail
    points = [(size*0.3, size*0.8), (size*0.2, size*0.95), (size*0.4, size*0.8)]
    draw.polygon(points, fill='white', outline='#7c3aed')
    
    # Draw simple face (two dots and smile)
    draw.ellipse([size*0.35, size*0.4, size*0.45, size*0.5], fill='#7c3aed')
    draw.ellipse([size*0.55, size*0.4, size*0.65, size*0.5], fill='#7c3aed')
    draw.arc([size*0.35, size*0.5, size*0.65, size*0.7], 0, 180, fill='#7c3aed', width=max(2, size//32))
    
    return img

# Create icons in different sizes
for size in [16, 48, 128]:
    icon = create_icon(size)
    icon.save(f'icon{size}.png')
    print(f'Created icon{size}.png')

print('All icons created successfully!')
