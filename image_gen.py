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

class ImageGenerator:
    def __init__(self, width: int, height: int, background: float | tuple[float, ...] | str | None):
        self.width = width
        self.height = height
        self.background = background
        try:
            self._tall_digits_img = Image.open("tall-digits.png")
            self._min_img = Image.open("min.png")
            self._unifont_img = Image.open("unifont-16.0.04.bmp")
            self._small_digits_img = Image.open("small-digits.png")
            self._plus_img = Image.open("plus.png")
        except FileNotFoundError as e:
            raise Exception(f"Error: Could not load required image file: {e}")
        


    def gen_image(self, minutes: int, text: str, platform_number, delay) -> Image.Image:
        # Validate platform number
        if not (1 <= platform_number <= 12):
            raise Exception(f"Error: Platform number must be between 1 and 12, got {platform_number}")

        output_img = Image.new('RGB', (self.width, self.height), color = self.background)
        digits = split_digits(minutes)
        current_x = 0
        
        # 1. Paste digits from tall-digits.png (4x16 each)
        for digit_char in digits:
            digit_img = get_digit_from_tall_digits(self._tall_digits_img, digit_char)
            if current_x + 4 <= self.width:  # Make sure we don't exceed width
                output_img.paste(digit_img, (current_x, 0))
                current_x += 4
        
        # 2. Paste min.png as is
        if current_x + self._min_img.width <= self.width:
            output_img.paste(self._min_img, (current_x, 0))
            current_x += self._min_img.width
        else:
            print("Warning: Not enough space for min.png")

        delay_x = current_x
        
        # Reserve space for platform character at the end (16 pixels)
        max_text_width = self.width - 16
        
        # 3. Render text using unifont
        for char in text:
            if current_x >= max_text_width:  # Save space for platform character
                break
                
            codepoint = ord(char)
            char_img = get_character_from_unifont(self._unifont_img, codepoint)
            
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
        platform_char = get_platform_character(self._unifont_img, platform_number)
        platform_x = self.width - 16  # Position at the rightmost 16 pixels
        output_img.paste(platform_char, (platform_x, 0))

        # 5. Overwrite delay text on top
        if int(delay) != 0:
            output_img.paste(self._plus_img, (delay_x, 0))
            delay_x += 4
            for digit_char in str(delay):
                if digit_char.isdigit():
                    digit_img = get_digit_from_small_digits(self._small_digits_img, digit_char)
                    if delay_x + 4 <= self.width:  # Make sure we don't exceed width
                        output_img.paste(digit_img, (delay_x, 0))
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

def create_display_image(digits, text, platform_number, delay, output_path="display_output.png"):
    """
    Create a 128x16 display image with digits, min.png, text, and platform character.
    
    Args:
        digits: String of digits to display at the start
        text: Text to display after min.png
        platform_number: Platform number (1-12) for the platform character
        output_path: Path to save the output PNG file
    
    Returns:
        PIL Image object of the created display
    """
    # Validate platform number
    if not (1 <= platform_number <= 12):
        print(f"Error: Platform number must be between 1 and 12, got {platform_number}")
        return None
    
    # Create 128x16 output image with WHITE background
    output_img = Image.new('RGB', (128, 16), color='white')
    
    # Load required images
    try:
        tall_digits_img = Image.open("tall-digits.png")
        min_img = Image.open("min.png")
        unifont_img = Image.open("unifont-16.0.04.bmp")
        small_digits_img = Image.open("small-digits.png")
        plus_img = Image.open("plus.png")
    except FileNotFoundError as e:
        print(f"Error: Could not load required image file: {e}")
        return None
    
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

    delay_x = current_x
    
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

    # 5. Overwrite delay text on top
    if int(delay) != 0:
        output_img.paste(plus_img, (delay_x, 0))
        delay_x += 4
        for digit_char in str(delay):
            if digit_char.isdigit():
                digit_img = get_digit_from_small_digits(small_digits_img, digit_char)
                if delay_x + 4 <= 128:  # Make sure we don't exceed width
                    output_img.paste(digit_img, (delay_x, 0))
                    delay_x += 4
            else:
                print(f"Warning: '{digit_char}' is not a digit, skipping")
    
    # Save the result
    output_img.save(output_path)
    print(f"Display image created: digits='{digits}', text='{text}', platform={platform_number}")
    print(f"Platform character codepoint: 0x{0x278A + platform_number:04X}")
    print(f"Saved to: {output_path}")
    
    return output_img

class TrainDisplayGUI:
    """
    GUI application for the train display.
    """
    
    def __init__(self, root):
        self.root = root
        self.root.title("Train Departure Display")
        self.root.resizable(False, False)
        
        # Create main frame
        main_frame = ttk.Frame(root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Input fields
        ttk.Label(main_frame, text="Minutes until departure:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.digits_var = tk.StringVar(value="15")
        digits_entry = ttk.Entry(main_frame, textvariable=self.digits_var, width=10)
        digits_entry.grid(row=0, column=1, sticky=tk.W, padx=(5, 0), pady=2)
        
        ttk.Label(main_frame, text="Station name:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.text_var = tk.StringVar(value="Central Station")
        text_entry = ttk.Entry(main_frame, textvariable=self.text_var, width=30)
        text_entry.grid(row=1, column=1, sticky=tk.W, padx=(5, 0), pady=2)
        
        ttk.Label(main_frame, text="Platform number (1-12):").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.platform_var = tk.StringVar(value="1")
        platform_spinbox = ttk.Spinbox(main_frame, from_=1, to=12, textvariable=self.platform_var, width=10)
        platform_spinbox.grid(row=2, column=1, sticky=tk.W, padx=(5, 0), pady=2)

        ttk.Label(main_frame, text="Delay:").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.delay_var = tk.StringVar(value="2")
        digits_entry = ttk.Entry(main_frame, textvariable=self.delay_var, width=10)
        digits_entry.grid(row=3, column=1, sticky=tk.W, padx=(5, 0), pady=2)
        
        # Update button
        update_button = ttk.Button(main_frame, text="Update Display", command=self.update_display)
        update_button.grid(row=4, column=0, columnspan=2, pady=10)
        
        # Display area
        self.display_label = ttk.Label(main_frame, text="Display will appear here")
        self.display_label.grid(row=5, column=0, columnspan=2, pady=10)
        
        # Generate initial display
        self.update_display()
    
    def update_display(self):
        """Update the display with current input values."""
        try:
            digits = self.digits_var.get()
            text = self.text_var.get()
            platform = int(self.platform_var.get())
            delay = self.delay_var.get()
            
            # Create the display image
            display_img = create_display_image(digits, text, platform, delay)
            
            if display_img is not None:
                # Scale the image by 4x using nearest neighbor to maintain pixel art look
                scaled_img = display_img.resize((512, 64), Image.NEAREST)
                
                # Convert to PhotoImage for tkinter
                self.photo = ImageTk.PhotoImage(scaled_img)
                
                # Update the label
                self.display_label.configure(image=self.photo, text="")
            else:
                self.display_label.configure(image="", text="Error creating display")
                
        except ValueError:
            self.display_label.configure(image="", text="Invalid platform number")
        except Exception as e:
            self.display_label.configure(image="", text=f"Error: {e}")

def main():
    """
    Main function to start the GUI application.
    """
    root = tk.Tk()
    app = TrainDisplayGUI(root)
    root.mainloop()

def main_cli():
    """
    Original CLI function (kept for backward compatibility).
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
