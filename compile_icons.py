#!/usr/bin/env python3

import argparse
import asyncio
import os
from io import BytesIO

from cairosvg import svg2png
from PIL import Image
import discord
from discord.ext import commands

from config import BOT_TOKEN, HOME_GUILD_ID

# Define the maximum file size for the compressed images (in bytes)
MAX_FILE_SIZE = 256 * 1024  # 256 kB

# Define the image dimensions
OUTPUT_WIDTH = 128
OUTPUT_HEIGHT = 128

def process(args):
    # Load the SVG files into a list
    svg_files = os.listdir(args.svg_path)

    # Load the background images into a list
    bg_files = os.listdir(args.bg_path)

    # Remove existing compiled images
    print('Clearing existing output...')
    for existing_file in os.listdir(args.output_path):
        os.remove(os.path.join(args.output_path, existing_file))

    print('Combining {} foreground images with {} backgrounds.'.format(len(svg_files), len(bg_files)))
    # Loop through all combinations of SVG files and backgrounds
    for svg_file in svg_files:
        for bg_file in bg_files:
            # Load the SVG file
            svg_buf = BytesIO()
            svg2png(url=os.path.join(args.svg_path, svg_file), parent_width=OUTPUT_WIDTH, parent_height=OUTPUT_HEIGHT, write_to=svg_buf)
            svg = Image.open(svg_buf)

            # Load the background image
            bg = Image.open(os.path.join(args.bg_path, bg_file))

            # Resize the SVG file to match the size of the background image
            svg = svg.resize(bg.size)

            # Paste the SVG file onto the background image
            bg.paste(svg, (0, 0), svg)

            # Resize the image to 128x128
            bg = bg.resize((OUTPUT_WIDTH, OUTPUT_HEIGHT))

            # Compress the image to the desired file size
            quality = 95
            while True:
                buffer = BytesIO()
                bg.save(buffer, format='PNG', optimize=True, quality=quality)
                if buffer.tell() <= MAX_FILE_SIZE or quality == 5:
                    break
                quality -= 5
                buffer.close()
            compressed_image = Image.open(buffer)

            # Save the compressed image as a PNG file
            output_filename = os.path.splitext(svg_file)[0] + os.path.splitext(bg_file)[0] + '.png'
            output_filepath = os.path.join(args.output_path, output_filename)
            compressed_image.save(output_filepath, format='PNG')
            print('Wrote new file {}, quality={}'.format(output_filepath, quality))
    if args.upload:
        upload(args.output_path)
    
def upload(output_path):
    client = discord.Client(token=BOT_TOKEN, intents=discord.Intents(guilds=True, emojis=True))
    @client.event
    async def on_ready():
        guild = client.get_guild(int(HOME_GUILD_ID))
        # Delete all existing custom emojis first
        for emoji in await guild.fetch_emojis():
            print(f'Deleting {emoji.name} ({emoji.id})')
            await emoji.delete()
        # Upload the new custom emojis
        for filename in os.listdir(output_path):
            with open(os.path.join(output_path, filename), 'rb') as image_file:
                await guild.create_custom_emoji(name=filename.split('.')[0], image=image_file.read())
            print('Uploaded {}'.format(filename))
        await client.close()
        print('Done!')
    client.run(BOT_TOKEN)

def main():
    parser = argparse.ArgumentParser(description='Compile board/piece PNGs and optionally upload')
    parser.add_argument('--svg_path', type=str, default='resources/raw/fg', help='Path to SVG file')
    parser.add_argument('--bg_path', type=str, default='resources/raw/bg', help='Path to background image file')
    parser.add_argument('--output_path', type=str, default='resources/compiled', help='Output path for compiled image file')
    parser.add_argument('--upload', dest='upload', action='store_true', help='Upload to Discord endpoint')
    parser.set_defaults(upload=False)
    args = parser.parse_args()
    process(args)

if __name__ == '__main__':
    main()