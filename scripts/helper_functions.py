import json
import os
import math
from PIL import Image
import mcschematic

# Function to find the closest RGB value using Euclidean distance
def find_closest_rgb(rgb, rgb_values):
    closest_block = None
    closest_distance = float('inf')
    
    for block, block_rgb in rgb_values.items():
        # Calculate the Euclidean distance between the current pixel and block's RGB
        distance = math.sqrt(sum((rgb[i] - block_rgb[i]) ** 2 for i in range(3)))
        if distance < closest_distance:
            closest_distance = distance
            closest_block = block

    return closest_block

# Function to resize the image based on the user-specified width and maintain aspect ratio
def resize_image(image, width):
    aspect_ratio = image.height / image.width
    new_height = int(width * aspect_ratio)
    print(f"Resizing image to width {width}, height {new_height}")
    return image.resize((width, new_height)), new_height

# Function to get the correct PNG file from manual.json
def get_texture_file(block_name, manual_data):
    if block_name in manual_data:
        textures = manual_data[block_name]
        # Prefer the side texture if available
        for texture in textures:
            if 'side' in texture:
                return texture
        return textures[0]  # Return the first texture if no "side" texture is found
    return None

# Function to create a PNG output using the full block textures without scaling them
def create_png_output(image, rgb_values, manual_data, output_path, texture_folder, block_size):
    # Calculate the output image size based on the resized image dimensions and block texture size
    output_width = image.width * block_size
    output_height = image.height * block_size
    output_image = Image.new('RGB', (output_width, output_height))
    
    print(f"Creating output image with size: {output_width}x{output_height}")
    
    for x in range(image.width):
        for y in range(image.height):
            pixel_rgb = image.getpixel((x, y))
            closest_block = find_closest_rgb(pixel_rgb, rgb_values)
            
            # Get the correct texture file name from manual.json
            texture_file_name = get_texture_file(closest_block, manual_data)
            
            if texture_file_name:
                texture_file = os.path.join(texture_folder, texture_file_name)

                # Check if the texture file exists
                if os.path.exists(texture_file):
                    block_texture = Image.open(texture_file).convert('RGB')
                    # Paste the full block texture at the correct position in the output image
                    output_image.paste(block_texture, (x * block_size, y * block_size))
                else:
                    print(f"Texture not found for block: {closest_block}")
            else:
                print(f"No texture found for block: {closest_block} in manual.json")

    output_image.save(output_path)
    print(f"PNG output saved at {output_path}")

# Function to create a schematic output using mcschematic
def create_schematic_output(image, rgb_values, output_schem_path, orientation='vertical'):
    schem = mcschematic.MCSchematic()

    for x in range(image.width):
        for y in range(image.height):
            pixel_rgb = image.getpixel((x, y))
            closest_block = find_closest_rgb(pixel_rgb, rgb_values)
            
            # Place blocks either flat (on XZ plane) or vertical (on XY plane with 180-degree flip on Y-axis)
            if orientation == 'vertical':
                flipped_y = image.height - y - 1  # Flip the Y-axis to achieve the 180-degree flip
                schem.setBlock((x, flipped_y, 0), closest_block)  # Standing up vertically (XY plane)
            else:
                schem.setBlock((x, 0, y), closest_block)  # Laying flat (XZ plane)

    # If no directory is provided, use the current working directory
    output_folder = os.path.dirname(output_schem_path)
    if output_folder == '':
        output_folder = '.'

    # Ensure the folder exists
    os.makedirs(output_folder, exist_ok=True)

    # Save the schematic file with correct path handling
    schem.save(output_folder, os.path.basename(output_schem_path).replace('.schem', ''), mcschematic.Version.JE_1_18_2)
    print(f"Schematic file saved at {os.path.join(output_folder, os.path.basename(output_schem_path))}")

def generate_setblock_commands(image, rgb_values, starting_position, output_json_path):
    setblock_commands = []
    start_x, start_y, start_z = starting_position
    
    for x in range(image.width):
        for y in range(image.height):
            pixel_rgb = image.getpixel((x, y))
            closest_block = find_closest_rgb(pixel_rgb, rgb_values)
            command = f"/setblock {start_x + x} {start_y + y} {start_z} {closest_block}"
            setblock_commands.append(command)

    with open(output_json_path, 'w') as output_file:
        json.dump(setblock_commands, output_file, indent=4)
    
    print(f"Setblock commands saved to {output_json_path}")
