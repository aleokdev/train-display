import sys
import argparse
from modules.image_gen import ImageGenerator
from modules.gui import run_gui


def run_cli():
    parser = argparse.ArgumentParser(
        description="Create 128x16 display with digits, min.png, text, and platform number"
    )
    parser.add_argument("digits", help='Digits to display at the start (e.g., "123")')
    parser.add_argument("text", help="Text to render after min.png")
    parser.add_argument(
        "platform",
        type=int,
        help="Platform number (1-12) for station platform character",
    )
    parser.add_argument("-d", "--delay", help="Delay of the train", default=0)
    parser.add_argument("-W", "--width", help="Width of the image", default=128)
    parser.add_argument("-H", "--height", help="Height of the image", default=16)
    parser.add_argument(
        "-o",
        "--output",
        default="display_output.png",
        help="Output PNG file path (default: display_output.png)",
    )

    args = parser.parse_args()

    img_gen = ImageGenerator(args.width, args.height, "#ffffff")

    try:
        image = img_gen.gen_image(args.digits, args.text, args.platform, args.delay)
    except Exception as e:
        print(f"Error when generating image: {e}")
        sys.exit(1)

    try:
        image.save(args.output)
    except Exception as e:
        print(f"Error when saving image: {e}")
        sys.exit(1)
