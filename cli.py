"""
Command Line Interface for Steganography Tool
"""
import argparse
import sys
import os
from pathlib import Path
from datetime import datetime
from .steganography_engine import SteganographyEngine
from .encryption_manager import EncryptionManager
from .database_manager import DatabaseManager


class SteganographyCLI:
    """Command Line Interface for the tool"""
    
    def __init__(self):
        self.engine = SteganographyEngine()
        self.db_manager = DatabaseManager()
        self.session_id = f"cli_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.db_manager.start_session(self.session_id, "CLI", "Steganography CLI")
        
    def encode(self, args):
        """Encode data into image"""
        try:
            # Read secret data
            if args.text:
                secret_data = args.text.encode('utf-8')
            elif args.file:
                with open(args.file, 'rb') as f:
                    secret_data = f.read()
            else:
                print("Error: No secret data provided")
                return 1
            
            # Apply encryption if requested
            if args.password:
                encryption_mgr = EncryptionManager(args.password)
                encrypted_data, key = encryption_mgr.encrypt_data(secret_data)
                secret_data = encrypted_data
                print(f"Encryption key (save this!): {key.hex()}")
            
            # Determine output path
            if args.output:
                output_path = args.output
            else:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_path = f"stego_{timestamp}.png"
            
            # Encode data
            print(f"Encoding data into {args.image}...")
            success, message = self.engine.embed_data(
                cover_image_path=args.image,
                secret_data=secret_data,
                output_path=output_path,
                bits_per_pixel=args.bits,
                use_compression=not args.no_compress
            )
            
            # Log operation
            metadata = {
                'bits_per_pixel': args.bits,
                'compression': not args.no_compress,
                'encryption': bool(args.password)
            }
            
            self.db_manager.log_operation(
                operation_type='embed',
                input_file=args.image,
                output_file=output_path,
                data_size=len(secret_data),
                encryption_used=bool(args.password),
                success=success,
                metadata=metadata
            )
            
            if success:
                print(f"Success! {message}")
                return 0
            else:
                print(f"Error: {message}")
                return 1
                
        except Exception as e:
            print(f"Error: {str(e)}")
            return 1
    
    def decode(self, args):
        """Decode data from image"""
        try:
            print(f"Decoding data from {args.image}...")
            
            # Extract data
            extracted_data, message = self.engine.extract_data(args.image)
            
            if extracted_data is None:
                print(f"Error: {message}")
                return 1
            
            # Try decryption if password provided
            if args.password or args.key:
                encryption_mgr = EncryptionManager(args.password)
                
                if args.key:
                    key = bytes.fromhex(args.key)
                    decrypted_data, decrypt_msg = encryption_mgr.decrypt_data(
                        extracted_data, key=key
                    )
                else:
                    decrypted_data, decrypt_msg = encryption_mgr.decrypt_data(
                        extracted_data, password=args.password
                    )
                
                if decrypted_data:
                    extracted_data = decrypted_data
                    message += f"\n{decrypt_msg}"
                else:
                    print(f"Error: {decrypt_msg}")
                    return 1
            
            # Output the data
            if args.output:
                with open(args.output, 'wb') as f:
                    f.write(extracted_data)
                print(f"Data written to {args.output}")
            else:
                # Try to display as text
                try:
                    text_data = extracted_data.decode('utf-8')
                    print(f"Extracted text:\n{text_data}")
                except:
                    print(f"Binary data (hex): {extracted_data.hex()[:200]}..." if len(extracted_data) > 100 else extracted_data.hex())
            
            # Log operation
            self.db_manager.log_operation(
                operation_type='extract',
                input_file=args.image,
                data_size=len(extracted_data),
                encryption_used=bool(args.password or args.key),
                success=True
            )
            
            print(f"Success! {message}")
            return 0
            
        except Exception as e:
            print(f"Error: {str(e)}")
            return 1
    
    def capacity(self, args):
        """Calculate embedding capacity"""
        try:
            capacity_info = self.engine.calculate_capacity(args.image, args.bits)
            
            print(f"Image: {args.image}")
            print(f"Total pixels: {capacity_info['pixels']:,}")
            print(f"Channels: {capacity_info['channels']}")
            print(f"Bits per pixel: {capacity_info['bits_per_pixel']}")
            print(f"Available capacity: {capacity_info['available_bytes']:,} bytes")
            print(f"  ({capacity_info['available_bits']:,} bits)")
            print(f"Header overhead: {capacity_info['header_bits']} bits")
            
            return 0
        except Exception as e:
            print(f"Error: {str(e)}")
            return 1
    
    def history(self, args):
        """Show operation history"""
        try:
            history = self.db_manager.get_operation_history(limit=args.limit)
            
            if not history:
                print("No operations recorded")
                return 0
            
            print(f"{'ID':<4} {'Timestamp':<19} {'Operation':<10} {'Input':<30} {'Size':<10} {'Success':<8}")
            print("-" * 85)
            
            for record in history:
                input_file = Path(record['input_file']).name if record['input_file'] else 'N/A'
                size = f"{record['data_size']}B" if record['data_size'] else 'N/A'
                success = '✓' if record['success'] else '✗'
                
                print(f"{record['id']:<4} {record['timestamp']:<19} "
                      f"{record['operation_type']:<10} {input_file:<30} "
                      f"{size:<10} {success:<8}")
            
            return 0
        except Exception as e:
            print(f"Error: {str(e)}")
            return 1
    
    def integrity(self, args):
        """Verify file integrity"""
        try:
            result = self.db_manager.verify_file_integrity(args.file)
            
            if result['verified']:
                print(f"✓ File integrity verified")
                print(f"  Hash: {result['current_hash']}")
                return 0
            else:
                print(f"✗ File integrity check failed")
                if 'error' in result:
                    print(f"  Error: {result['error']}")
                if 'current_hash' in result:
                    print(f"  Current hash: {result['current_hash']}")
                if 'stored_hash' in result:
                    print(f"  Stored hash: {result['stored_hash']}")
                return 1
                
        except Exception as e:
            print(f"Error: {str(e)}")
            return 1
    
    def run(self):
        """Parse arguments and run appropriate command"""
        parser = argparse.ArgumentParser(
            description="Secure Data Hider - Steganography Tool",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  %(prog)s encode -i cover.png -t "secret message" -o stego.png
  %(prog)s encode -i cover.jpg -f secret.txt -p password123
  %(prog)s decode -i stego.png -p password123
  %(prog)s capacity -i image.jpg --bits 2
  %(prog)s history --limit 10
            """
        )
        
        subparsers = parser.add_subparsers(dest='command', help='Command to execute')
        
        # Encode command
        encode_parser = subparsers.add_parser('encode', help='Encode data into image')
        encode_parser.add_argument('-i', '--image', required=True, help='Cover image path')
        encode_parser.add_argument('-t', '--text', help='Secret text to hide')
        encode_parser.add_argument('-f', '--file', help='Secret file to hide')
        encode_parser.add_argument('-o', '--output', help='Output stego image path')
        encode_parser.add_argument('-p', '--password', help='Encryption password')
        encode_parser.add_argument('-b', '--bits', type=int, default=1, choices=[1, 2, 3],
                                 help='Bits per pixel (default: 1)')
        encode_parser.add_argument('--no-compress', action='store_true',
                                 help='Disable data compression')
        
        # Decode command
        decode_parser = subparsers.add_parser('decode', help='Decode data from image')
        decode_parser.add_argument('-i', '--image', required=True, help='Stego image path')
        decode_parser.add_argument('-o', '--output', help='Output file path')
        decode_parser.add_argument('-p', '--password', help='Decryption password')
        decode_parser.add_argument('-k', '--key', help='Decryption key (hex)')
        
        # Capacity command
        capacity_parser = subparsers.add_parser('capacity', help='Calculate embedding capacity')
        capacity_parser.add_argument('-i', '--image', required=True, help='Image path')
        capacity_parser.add_argument('-b', '--bits', type=int, default=1, choices=[1, 2, 3],
                                   help='Bits per pixel (default: 1)')
        
        # History command
        history_parser = subparsers.add_parser('history', help='Show operation history')
        history_parser.add_argument('-l', '--limit', type=int, default=20,
                                  help='Number of records to show (default: 20)')
        
        # Integrity command
        integrity_parser = subparsers.add_parser('integrity', help='Verify file integrity')
        integrity_parser.add_argument('-f', '--file', required=True, help='File to verify')
        
        # Parse arguments
        args = parser.parse_args()
        
        if not args.command:
            parser.print_help()
            return 1
        
        # Execute command
        if args.command == 'encode':
            return self.encode(args)
        elif args.command == 'decode':
            return self.decode(args)
        elif args.command == 'capacity':
            return self.capacity(args)
        elif args.command == 'history':
            return self.history(args)
        elif args.command == 'integrity':
            return self.integrity(args)
        
        return 0


def main():
    """CLI entry point"""
    cli = SteganographyCLI()
    return cli.run()


if __name__ == "__main__":
    sys.exit(main())