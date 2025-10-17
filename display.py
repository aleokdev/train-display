from PIL import Image, ImageTk
import sys
import argparse
import tkinter as tk
from tkinter import ttk
from image_gen import ImageGenerator

class TrainDisplayGUI:
    """
    GUI application for the train display.
    """
    
    def __init__(self, root):
        self.root = root
        self.root.title("Train Departure Display")
        self.root.resizable(False, False)
        self.image_gen = ImageGenerator(128, 16, '#ffffffff')
        
        # Create main frame
        main_frame = ttk.Frame(root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Input fields
        ttk.Label(main_frame, text="Minutes until departure:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.digits_var = tk.IntVar(value=15)
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
            display_img = self.image_gen.gen_image(digits, text, platform, delay)
            
            if display_img is not None:
                # Scale the image by 4x using nearest neighbor to maintain pixel art look
                scaled_img = display_img.resize((self.image_gen.width * 4, self.image_gen.height * 4), Image.NEAREST)
                
                # Convert to PhotoImage for tkinter
                self.photo = ImageTk.PhotoImage(scaled_img)
                
                # Update the label
                self.display_label.configure(image=self.photo, text="")
            else:
                self.display_label.configure(image="", text="Error creating display")

        except Exception as e:
            self.display_label.configure(image="", text=f"Error: {e}")

def run_gui():
        root = tk.Tk()
        app = TrainDisplayGUI(root)
        root.mainloop()

def run_cli():
        parser = argparse.ArgumentParser(description='Create 128x16 display with digits, min.png, text, and platform number')
        parser.add_argument('digits', help='Digits to display at the start (e.g., "123")')
        parser.add_argument('text', help='Text to render after min.png')
        parser.add_argument('platform', type=int, help='Platform number (1-12) for station platform character')
        parser.add_argument('-d', '--delay', help='Delay of the train', default=0)
        parser.add_argument('-W', '--width', help='Width of the image', default=128)
        parser.add_argument('-H', '--height', help='Height of the image', default=16)
        parser.add_argument('-o', '--output', default='display_output.png', 
                        help='Output PNG file path (default: display_output.png)')
        
        args = parser.parse_args()

        img_gen = ImageGenerator(args.width, args.height, '#ffffff')
        
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

def main():
    if len(sys.argv) == 1:
         run_gui()
    else:
         run_cli()

if __name__ == "__main__":
    main()