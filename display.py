import sys
from modules.gui import run_gui
from modules.cli import run_cli

def main():
    if len(sys.argv) == 1:
         run_gui()
    else:
         run_cli()

if __name__ == "__main__":
    main()