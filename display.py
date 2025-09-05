from PIL import Image
import sys
import argparse

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

def create_display_image(digits, text, platform_number, output_path="display_output.png"):
    """
    Create a 128x16 display image with digits, min.png, text, and platform character.
    
    Args:
        digits: String of digits to display at the start
        text: Text to display after min.png
        platform_number: Platform number (1-12) for the platform character
        output_path: Path to save the output PNG file
    """
    # Validate platform number
    if not (1 <= platform_number <= 12):
        print(f"Error: Platform number must be between 1 and 12, got {platform_number}")
        sys.exit(1)
    
    # Create 128x16 output image with WHITE background
    output_img = Image.new('RGB', (128, 16), color='white')
    
    # Load required images
    try:
        tall_digits_img = Image.open("tall-digits.png")
        min_img = Image.open("min.png")
        unifont_img = Image.open("unifont-16.0.04.bmp")
    except FileNotFoundError as e:
        print(f"Error: Could not load required image file: {e}")
        sys.exit(1)
    
    current_x = 0
    
    # 1. Paste digits from tall-digits.png (4x16 each)
    for digit_char in digits:
        if digit_char.isdigit():
            digit_img = get_digit_from_tall_digits(tall_digits_img, digit_char)
            if current_x + 4 <= 128:  # Make sure we don't exceed width
                output_img.paste(digit_img, (current_x, 0))
                current_x += 4
        else:
            print(f"Warning: '{digit_char}' is not a digit, skipping")
    
    # 2. Paste min.png as is
    if current_x + min_img.width <= 128:
        output_img.paste(min_img, (current_x, 0))
        current_x += min_img.width
    else:
        print("Warning: Not enough space for min.png")
    
    # Reserve space for platform character at the end (16 pixels)
    max_text_width = 128 - 16
    
    # 3. Render text using unifont
    for char in text:
        if current_x >= max_text_width:  # Save space for platform character
            break
            
        codepoint = ord(char)
        char_img = get_character_from_unifont(unifont_img, codepoint)
        
        # Determine character width (8 or 16 pixels based on character type)
        char_width = 16 if (char in ('=', '@', '#') or codepoint >= 128 and not (0x0400 <= codepoint <= 0x04FF)) else 8
        
        if current_x + char_width <= max_text_width:
            output_img.paste(char_img, (current_x, 0))
            current_x += char_width
        else:
            # Try to fit with reduced width
            remaining_width = max_text_width - current_x
            if remaining_width > 0:
                # Crop character to fit remaining space
                cropped_char = char_img.crop((0, 0, remaining_width, 16))
                output_img.paste(cropped_char, (current_x, 0))
            break
    
    # 4. Add platform character at the end (0x278A + platform_number)
    platform_char = get_platform_character(unifont_img, platform_number)
    platform_x = 128 - 16  # Position at the rightmost 16 pixels
    output_img.paste(platform_char, (platform_x, 0))
    
    # Save the result
    output_img.save(output_path)
    print(f"Display image created: digits='{digits}', text='{text}', platform={platform_number}")
    print(f"Platform character codepoint: 0x{0x278A + platform_number:04X}")
    print(f"Saved to: {output_path}")
    
    return output_img

def main():
    """
    Main function to handle command line arguments and create display.
    """
    parser = argparse.ArgumentParser(description='Create 128x16 display with digits, min.png, text, and platform number')
    parser.add_argument('digits', help='Digits to display at the start (e.g., "123")')
    parser.add_argument('text', help='Text to render after min.png')
    parser.add_argument('platform', type=int, help='Platform number (1-12) for station platform character')
    parser.add_argument('-o', '--output', default='display_output.png', 
                       help='Output PNG file path (default: display_output.png)')
    
    args = parser.parse_args()
    
    try:
        create_display_image(args.digits, args.text, args.platform, args.output)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()