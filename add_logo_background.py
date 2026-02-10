#!/usr/bin/env python3
"""
Add professional background to logo
"""
from PIL import Image
import os

# Logo paths
logo_path = "logo3.png"
output_path = "static/images/logo3_bg.png"

# Open the logo
logo = Image.open(logo_path)

# Create a new image with green background (matching the site's primary color)
# The color is #1a5f4a (dark green)
width, height = logo.size

# Add some padding around the logo
padding_x = 60
padding_y = 40
new_width = width + (padding_x * 2)
new_height = height + (padding_y * 2)

# Create background with gradient effect
background = Image.new('RGB', (new_width, new_height), '#1a5f4a')

# Paste the logo onto the background (centered)
logo_rgb = logo.convert('RGBA')
background_rgba = background.convert('RGBA')

# Calculate position to center the logo
x = (new_width - width) // 2
y = (new_height - height) // 2

# Paste using alpha channel
background_rgba.paste(logo_rgb, (x, y), logo_rgb)

# Convert back to RGB for saving as PNG
final = background_rgba.convert('RGB')

# Save the result
final.save(output_path, 'PNG', quality=95)

print(f"✅ Logo with background saved to: {output_path}")
print(f"   Size: {new_width}x{new_height}px")

# Also create a version with rounded corners (optional)
from PIL import ImageDraw

# Create rounded rectangle mask
mask = Image.new('L', (new_width, new_height), 0)
draw = ImageDraw.Draw(mask)
corner_radius = 30
draw.rounded_rectangle([0, 0, new_width, new_height], corner_radius, fill=255)

# Apply rounded corners
final_rounded = Image.new('RGBA', (new_width, new_height), (0, 0, 0, 0))
final_rounded.paste(background_rgba, (0, 0))
final_rounded.putalpha(mask)

# Save rounded version
final_rounded.save("static/images/logo3_rounded.png", 'PNG')
print(f"✅ Logo with rounded corners saved to: static/images/logo3_rounded.png")
