from PIL import Image, ImageTk
import sys
import argparse
import tkinter as tk
from tkinter import ttk

def split_digits(number: int | str) -> list[str]:
    """
    Return the individual decimal digits of `number` as a list of characters.

    - Accepts ints, numeric strings and floats.
    - Preserves leading zeros for string input (e.g. "007" -> [0,0,7]).
    - Ignores sign and non-digit characters (decimal point, etc).
    - If no digits are found returns [0].
    """
    s = str(number)
    # strip sign characters
    if s and s[0] in "+-":
        s = s[1:]
    digits = [ch for ch in s if ch.isdigit()]
    return digits if digits else ['0']

def get_digit_from_tall_digits(tall_digits_img, digit):
    """
    Extract a 4x16 digit from tall-digits.png.
    
    Args:
        tall_digits_img: PIL Image object of tall-digits.png
        digit: Digit character ('0'-'9')
    
    Returns:
        PIL Image of the 4x16 digit
    """
    digit_index = int(digit)
    # Each digit is 4 pixels wide, 16 pixels tall
    x_pos = digit_index * 4
    digit_region = tall_digits_img.crop((x_pos, 0, x_pos + 4, 16))
    return digit_region

def get_digit_from_small_digits(small_digits_img, digit):
    """
    Extract a 4x7 digit from small-digits.png.
    
    Args:
        small_digits_img: PIL Image object of small-digits.png
        digit: Digit character ('0'-'9')
    
    Returns:
        PIL Image of the 4x7 digit
    """
    digit_index = int(digit)
    # Each digit is 4 pixels wide, 16 pixels tall
    x_pos = digit_index * 4
    digit_region = small_digits_img.crop((x_pos, 0, x_pos + 4, 7))
    return digit_region

def get_character_from_unifont(bitmap, unicode_codepoint):
    """
    Extract a 16x16 character from unifont bitmap based on UTF-16 codepoint.
    
    Args:
        bitmap: PIL Image object of the unifont bitmap
        unicode_codepoint: Unicode codepoint (integer)
    
    Returns:
        PIL Image of the 16x16 character with proper contrast
    """
    # Split the UTF-16 codepoint into high and low bytes
    high_byte = (unicode_codepoint >> 8) & 0xFF
    low_byte = unicode_codepoint & 0xFF
    
    # Calculate position in the bitmap
    # Characters start at (32, 64) and are 16x16 pixels
    # Rows represent high byte, columns represent low byte
    char_x = 32 + (low_byte * 16)
    char_y = 64 + (high_byte * 16)
    
    # Extract the 16x16 character region
    char_region = bitmap.crop((char_x, char_y, char_x + 16, char_y + 16))
    
    return char_region

def colorize_image(img, color):
    """
    Convert pixels to color given while preserving transparency.
    
    Args:
        img: PIL Image with white pixels and transparency
        
    Returns:
        PIL Image with white pixels changed to foreground color
    """
    # Create a new image with the foreground color
    colored = Image.new("RGBA", img.size, color)
    
    # Use the original image's alpha channel as a mask
    # This will make transparent pixels remain transparent
    # and opaque pixels take the foreground color
    colored.putalpha(img.getchannel("A"))
    
    return colored

def get_text_width(text: str) -> int:
    total_width = 0
    for char in text:
        codepoint = ord(char)
        # Determine character width (8 or 16 pixels based on character type)
        char_width = 16 if (char in ('=', '@', '#') or codepoint >= 128 and not (0x0400 <= codepoint <= 0x04FF)) else 8
        total_width += char_width
    return total_width


class ImageGenerator:
    def __init__(self, width: int, height: int, background: float | tuple[float, ...] | str | None, foreground: float | tuple[float, ...] | str = "#ffffff"):
        self.width = width
        self.height = height
        self.background = background
        try:
            self._tall_digits_img = colorize_image(Image.open("assets/tall-digits.png").convert("RGBA"), "#17c711")
            self._colon_img = colorize_image(Image.open("assets/colon.png").convert("RGBA"), "#3bf834")
            self._min_img = colorize_image(Image.open("assets/min.png").convert("RGBA"), "#606060")
            self._unifont_img = colorize_image(Image.open("assets/unifont-16.0.04.png").convert("RGBA"), foreground)
            self._small_digits_img = colorize_image(Image.open("assets/small-digits.png").convert("RGBA"), "#ff0000")
            self._plus_img = colorize_image(Image.open("assets/plus.png").convert("RGBA"), "#ff0000")
            self._overlay_img = Image.open("assets/overlay.png").convert("RGBA")

        except FileNotFoundError as e:
            raise Exception(f"Error: Could not load required image file: {e}")
        


    def gen_image(self, time: str, text: str, delay, platform_number: int | None = None, text_x_offset: int = 0) -> Image.Image:
        # Validate platform number
        if platform_number is int and not (1 <= platform_number <= 12):
            raise Exception(f"Error: Platform number must be between 1 and 12, got {platform_number}")

        output_img = Image.new('RGBA', (self.width, self.height), color = self.background)
        current_x = 0

        # 1. Paste digits from tall-digits.png (4x16 each)
        for time_char in time:
            if time_char == ':':
                if current_x + 1 <= self.width:  # Make sure we don't exceed width
                    output_img.alpha_composite(self._colon_img, (current_x, 5))
                    current_x += 2
            else:
                digit_img = get_digit_from_tall_digits(self._tall_digits_img, time_char)
                if current_x + 4 <= self.width:  # Make sure we don't exceed width
                    output_img.alpha_composite(digit_img, (current_x, 5))
                    current_x += 4
        
        delay_x = current_x

        target_rect = (current_x, 0, self.width, self.height)

        # 3. Render text using unifont
        text_x = current_x + text_x_offset
        for char in text:
            if text_x >= self.width:
                break
            codepoint = ord(char)
            char_img = get_character_from_unifont(self._unifont_img, codepoint)
            
            # Determine character width (8 or 16 pixels based on character type)
            char_width = 16 if (char in ('=', '@', '#') or codepoint >= 128 and not (0x0400 <= codepoint <= 0x04FF)) else 8
                
            if target_rect[0] - text_x >= char_width:
                # before first cropped char
                # ignore
                pass
            elif target_rect[0] - text_x < 0:
                # after first cropped char
                # we are fully inside the target rect, no cropping needed
                output_img.alpha_composite(char_img, (text_x, 0))
            else:
                # first char in target rect, which is cropped
                cropped = char_img.crop((target_rect[0] - text_x, 0, char_width, 16))
                output_img.alpha_composite(cropped, (target_rect[0], 0))
            
            text_x += char_width
        
        # 4. Add platform character at the end (0x278A + platform_number)
        if platform_number is not None:
            digits = split_digits(platform_number)
            offset = 9 - len(digits) * 2
            for char in digits:
                digit = get_digit_from_small_digits(self._small_digits_img, char)
                output_img.alpha_composite(digit, (offset, -1))
                offset += 4

        # 5. Overwrite delay text on top
        if int(delay) != 0:
            output_img.alpha_composite(self._plus_img, (delay_x, 0))
            delay_x += 4
            for digit_char in str(delay):
                if digit_char.isdigit():
                    digit_img = get_digit_from_small_digits(self._small_digits_img, digit_char)
                    if delay_x + 4 <= self.width:  # Make sure we don't exceed width
                        output_img.alpha_composite(digit_img, (delay_x, 0))
                        delay_x += 4
                else:
                    print(f"Warning: '{digit_char}' is not a digit, skipping")

        output_img.alpha_composite(self._overlay_img)

        return output_img

def get_platform_character(bitmap, platform_idx):
    """
    Get the platform character at 0x278A + idx.
    
    Args:
        bitmap: PIL Image object of the unifont bitmap
        platform_idx: Platform index (1-12)
    
    Returns:
        PIL Image of the 16x16 platform character
    """
    # Calculate the Unicode codepoint: 0x278A + platform_idx
    codepoint = 0x278A + platform_idx - 1
    return get_character_from_unifont(bitmap, codepoint)
