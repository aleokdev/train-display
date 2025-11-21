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

class ImageGenerator:
    def __init__(self, width: int, height: int, background: float | tuple[float, ...] | str | None, foreground: float | tuple[float, ...] | str = "#ffffff"):
        self.width = width
        self.height = height
        self.background = background
        try:
            self._tall_digits_img = colorize_image(Image.open("assets/tall-digits.png").convert("RGBA"), "#1f4cdf")
            self._min_img = colorize_image(Image.open("assets/min.png").convert("RGBA"), "#606060")
            self._unifont_img = colorize_image(Image.open("assets/unifont-16.0.04.png").convert("RGBA"), foreground)
            self._small_digits_img = colorize_image(Image.open("assets/small-digits.png").convert("RGBA"), "#ff0000")
            self._plus_img = colorize_image(Image.open("assets/plus.png").convert("RGBA"), "#ff0000")

        except FileNotFoundError as e:
            raise Exception(f"Error: Could not load required image file: {e}")
        


    def gen_image(self, minutes: int, text: str, delay, platform_number: int | None = None, text_offset: tuple[int, int] = (0, 0)) -> Image.Image:
        # Validate platform number
        if platform_number is int and not (1 <= platform_number <= 12):
            raise Exception(f"Error: Platform number must be between 1 and 12, got {platform_number}")

        output_img = Image.new('RGBA', (self.width, self.height), color = self.background)
        digits = split_digits(minutes)
        minutes_width = 11
        digits_width = len(digits) * 4 - 1
        current_x = int((minutes_width - digits_width) / 2)

        # 1. Paste digits from tall-digits.png (4x16 each)
        for digit_char in digits:
            digit_img = get_digit_from_tall_digits(self._tall_digits_img, digit_char)
            if current_x + 4 <= self.width:  # Make sure we don't exceed width
                output_img.alpha_composite(digit_img, (current_x, 0))
                current_x += 4
        
        # 2. Paste min.png as is
        output_img.alpha_composite(self._min_img, (0, 0))

        delay_x = current_x

        if current_x < minutes_width:
            current_x = minutes_width
        
        # Reserve space for platform character at the end (16 pixels)
        if platform_number is not None:
            max_text_width = self.width - 16
        else:
            max_text_width = self.width
        
        # 3. Render text using unifont
        for char in text:
            if current_x >= max_text_width:  # Save space for platform character
                break
                
            codepoint = ord(char)
            char_img = get_character_from_unifont(self._unifont_img, codepoint)
            
            # Determine character width (8 or 16 pixels based on character type)
            char_width = 16 if (char in ('=', '@', '#') or codepoint >= 128 and not (0x0400 <= codepoint <= 0x04FF)) else 8
            
            if current_x + char_width <= max_text_width:
                output_img.alpha_composite(char_img, (current_x, 0))
                current_x += char_width
            else:
                # Try to fit with reduced width
                remaining_width = max_text_width - current_x
                if remaining_width > 0:
                    # Crop character to fit remaining space
                    cropped_char = char_img.crop((0, 0, remaining_width, 16))
                    output_img.alpha_composite(cropped_char, (current_x, 0))
                break
        
        # 4. Add platform character at the end (0x278A + platform_number)
        if platform_number is not None:
            platform_char = get_platform_character(self._unifont_img, platform_number)
            platform_x = self.width - 16  # Position at the rightmost 16 pixels
            output_img.paste(platform_char, (platform_x, 0))

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
