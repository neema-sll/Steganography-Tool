#!/usr/bin/env python3
"""
Main entry point for Steganography Tool
Secure Data Hider - A comprehensive steganography tool with GUI and CLI
"""
import sys
import os
import argparse

__version__ = '1.0.0'
__author__ = 'Neema Lama'


def print_banner():
    """Print application banner"""
    banner = """
    ╔══════════════════════════════════════════════════════════╗
    ║     🔒 SECURE DATA HIDER - STEGANOGRAPHY TOOL v1.0      ║
    ║         Hide secret data in images with AES encryption    ║
    ╚══════════════════════════════════════════════════════════╝
    """
    print(banner)


def check_dependencies():
    """Check if required dependencies are installed"""
    missing = []
    
    try:
        import PIL
    except ImportError:
        missing.append('Pillow')
    
    try:
        import numpy
    except ImportError:
        missing.append('numpy')
    
    try:
        import cryptography
    except ImportError:
        missing.append('cryptography')
    
    if missing:
        print("❌ Missing dependencies:", ', '.join(missing))
        print("\nPlease install them using:")
        print("  pip install -r requirements.txt")
        return False
    
    return True


def main():
    """Main entry point"""
    print_banner()
    
    # Parse arguments
    parser = argparse.ArgumentParser(
        description="Secure Data Hider - Steganography Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--cli', 
        action='store_true',
        help='Run in CLI mode (default: GUI mode)'
    )
    
    parser.add_argument(
        '--version', 
        action='version',
        version=f'Steganography Tool v{__version__}'
    )
    
    parser.add_argument(
        '--check',
        action='store_true',
        help='Check dependencies and exit'
    )
    
    args, unknown = parser.parse_known_args()
    
    # Check dependencies if requested
    if args.check:
        if check_dependencies():
            print("✅ All dependencies are installed")
            return 0
        return 1
    
    # Check dependencies before running
    if not check_dependencies():
        print("\n❌ Please install missing dependencies and try again.")
        return 1
    
    try:
        if args.cli or (len(sys.argv) > 1 and sys.argv[1] in ['encode', 'decode', 'capacity', 'history', 'integrity']):
            # CLI mode
            print("Running in CLI mode...\n")
            from src.cli import main as cli_main
            
            # Pass all arguments except the first one (script name)
            if len(sys.argv) > 1:
                # Already have CLI commands, pass through
                return cli_main()
            else:
                # Just --cli flag, show help
                sys.argv = [sys.argv[0], '--help']
                return cli_main()
        else:
            # GUI mode
            print("Starting GUI application...")
            print("(Use '--cli' flag for command-line interface)\n")
            from src.gui import main as gui_main
            gui_main()
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("\nMake sure you're running from the correct directory:")
        print("  cd steganography-tool")
        print("  python run.py")
        return 1
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())