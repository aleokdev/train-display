import sys
import argparse
from modules.image_gen import ImageGenerator
from modules.gui import run_gui
from modules.ipixel import IPixelScreen
import asyncio

def run_cli():
    parser = argparse.ArgumentParser(
        description="Create 128x16 display with digits, min.png, text, and platform number"
    )
    parser.add_argument("digits", help='Digits to display at the start (e.g., "123")')
    parser.add_argument("text", help="Text to render after min.png")
    parser.add_argument(
        "platform",
        type=int,
        nargs='?',
        help="Platform number (1-12) for station platform character",
    )
    parser.add_argument("-d", "--delay", help="Delay of the train", type=int, default=0)
    parser.add_argument("-W", "--width", help="Width of the image", type=int,default=128)
    parser.add_argument("-H", "--height", help="Height of the image", type=int, default=16)
    parser.add_argument(
        "-o",
        "--output",
        default="display_output.png",
        help="Output PNG file path (default: display_output.png)",
    )
    parser.add_argument('-m', '--mac', help="MAC address of display to use")

    args = parser.parse_args()

    img_gen = ImageGenerator(args.width, args.height, "#000000", "#ffffff")

    image = img_gen.gen_image(args.digits, args.text, args.delay, args.platform)

    if args.mac:
        screen = IPixelScreen(args.mac)
        asyncio.run(screen.update_screen(image))
    else:
        image.save(args.output)