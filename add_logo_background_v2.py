#!/usr/bin/env python3
"""
Add professional background to logo v2 - with lighter color and rounded corners
"""
from PIL import Image, ImageDraw
import os

# Logo paths
logo_path = "logo3.png"

# Open the logo
logo = Image.open(logo_path)
width, height = logo.size

# Add padding
padding_x = 80
padding_y = 50
new_width = width + (padding_x * 2)
new_height = height + (padding_y * 2)

# Create background with lighter green (matching the site's secondary color)
# Secondary color: #2d8b6f
background = Image.new('RGBA', (new_width, new_height), (45, 139, 111, 255))  # #2d8b6f

# Paste the logo onto the background (centered)
logo_rgba = logo.convert('RGBA')
x = (new_width - width) // 2
y = (new_height - height) // 2
background.paste(logo_rgba, (x, y), logo_rgba)

# Create rounded rectangle mask
corner_radius = 25
mask = Image.new('L', (new_width, new_height), 0)
draw = ImageDraw.Draw(mask)
draw.rounded_rectangle([0, 0, new_width, new_height], corner_radius, fill=255)

# Apply rounded corners
final = Image.new('RGBA', (new_width, new_height), (0, 0, 0, 0))
final.paste(background, (0, 0))
final.putalpha(mask)

# Save the result
output_path = "static/images/logo3_final.png"
final.save(output_path, 'PNG')
print(f"✅ Logo with rounded background saved to: {output_path}")

# Also create a navbar-friendly version (smaller height)
navbar_height = 60
scale = navbar_height / new_height
navbar_width = int(new_width * scale)

navbar_logo = final.resize((navbar_width, navbar_height), Image.Resampling.LANCZOS)
navbar_logo.save("static/images/logo_navbar.png", 'PNG')
print(f"✅ Navbar logo saved to: static/images/logo_navbar.png ({navbar_width}x{navbar_height}px)")
