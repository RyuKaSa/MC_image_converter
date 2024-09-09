import json
import os
import asyncio
import websockets  # WebSocket communication
from PIL import Image
from scripts.helper_functions import resize_image, generate_setblock_commands, create_png_output, create_schematic_output

# Ensure the output_files directory exists
os.makedirs('output_files', exist_ok=True)

# Function to ask the user for input via the console
def get_user_input():
    # Prompt for output format
    output_format = input("Please enter the output format (png, schem, setblock): ").strip().lower()

    # Common inputs
    input_image_path = input("Enter the path to the image file: ").strip() or 'images/original_image.png'
    width = int(input("Enter the width (default is 16): ").strip() or 16)

    # PNG and Schematic specific inputs
    if output_format == 'png':
        return output_format, input_image_path, width, None, None, False
    
    if output_format == 'schem':
        orientation = input("Should the structure be vertical or horizontal (vertical/horizontal)? ").strip().lower()
        vertical = True if orientation == 'vertical' else False
        return output_format, input_image_path, width, vertical, None, False

    # Setblock specific inputs
    if output_format == 'setblock':
        start_coords = input("Enter the starting coordinates (x,y,z) separated by commas (default is 0,60,0): ").strip() or "0,60,0"
        start_coords = tuple(map(int, start_coords.split(',')))
        websocket_run = input("Do you want to send the commands via WebSocket (yes/no)? ").strip().lower() == 'yes'
        return output_format, input_image_path, width, None, start_coords, websocket_run

    print("Invalid format. Please restart the program.")
    return None, None, None, None, None, None

# Function to send WebSocket commands
async def send_command(command):
    uri = "ws://localhost:8887"  # Ensure this is the WebSocket port configured in your server
    try:
        # Connect to the WebSocket for each command
        async with websockets.connect(uri) as websocket:
            # print(f"Sending command: {command}")  # Debugging print
            await websocket.send(f"Command {command}")
    except Exception as e:
        print(f"Error during WebSocket communication: {e}")  # Print any errors

# Function to send all commands from the JSON file
async def send_commands_from_json(json_file):
    # Load the setblock commands from the JSON file
    with open(json_file, 'r') as file:
        commands = json.load(file)
    
    # Send a dummy command first
    await send_command("/say Starting setblock commands...")

    # Duplicate the first command and append it to the end of the list
    first_command = commands[0]
    commands.append(first_command)

    # Join all commands with new lines
    command_block = '\n'.join([f"Command {command}" for command in commands])

    # Send all commands at once
    await send_command(command_block)

# Main function to convert image and process output
def convert_and_run(input_image_path, rgb_values_path, manual_json_path, output_type='png', width=16, texture_folder='textures', start_coords=(0, 60, 0), websocket_run=False):
    # Load the RGB values JSON file
    with open(rgb_values_path, 'r') as rgb_file:
        rgb_values = json.load(rgb_file)

    # Load the manual.json file
    with open(manual_json_path, 'r') as manual_file:
        manual_data = json.load(manual_file)

    # Open and resize the input image based on the user-specified width
    image = Image.open(input_image_path).convert('RGB')
    resized_image, resized_height = resize_image(image, width)

    block_size = 16  # Minecraft block texture size

    print(f"Using block size: {block_size}px for each block")

    # Generate PNG, schematic, or setblock commands based on user input
    if output_type == 'png':
        output_png_path = 'output_files/output_image.png'
        create_png_output(resized_image, rgb_values, manual_data, output_png_path, texture_folder, block_size)
    elif output_type == 'schem':
        output_schem_path = 'output_files/output_schematic.schem'
        create_schematic_output(resized_image, rgb_values, output_schem_path, orientation='vertical')
    elif output_type == 'setblock':
        output_json_path = 'output_files/setblock_commands.json'
        generate_setblock_commands(resized_image, rgb_values, start_coords, output_json_path)

        # Optionally send the commands via WebSocket
        if websocket_run:
            print("Preparing to send commands via WebSocket...")  # Debugging print
            asyncio.get_event_loop().run_until_complete(send_commands_from_json(output_json_path))

# Main program logic
def main():
    output_format, input_image_path, width, vertical, start_coords, websocket_run = get_user_input()

    if output_format:
        if output_format == 'png':
            convert_and_run(input_image_path, 'database/rgb_values.json', 'database/manual.json', output_type='png', width=width, texture_folder='textures')
        elif output_format == 'schem':
            convert_and_run(input_image_path, 'database/rgb_values.json', 'database/manual.json', output_type='schem', width=width, texture_folder='textures', websocket_run=websocket_run)
        elif output_format == 'setblock':
            convert_and_run(input_image_path, 'database/rgb_values.json', 'database/manual.json', output_type='setblock', width=width, texture_folder='textures', start_coords=start_coords, websocket_run=websocket_run)

if __name__ == "__main__":
    main()
