"""
Custom LSB Steganography Engine with OOP Design
Uses custom algorithms instead of built-in libraries
"""
import struct
import hashlib
from PIL import Image
import numpy as np
from typing import Tuple, Optional
import threading
import time

class SteganographyEngine:
    """Main steganography engine with custom LSB algorithm"""
    
    def __init__(self, encryption_key: bytes = None):
        """
        Initialize steganography engine
        
        Args:
            encryption_key: Optional encryption key for additional security
        """
        self.encryption_key = encryption_key
        self.max_threads = 4
        self.compression_level = 6  # 0-9, higher = more compression
        
    def calculate_capacity(self, image_path: str, bits_per_pixel: int = 1) -> dict:
        """
        Calculate maximum embeddable data size
        
        Args:
            image_path: Path to cover image
            bits_per_pixel: How many LSBs to use (1-3)
            
        Returns:
            Dictionary with capacity information
        """
        try:
            with Image.open(image_path) as img:
                # Convert to RGB if necessary for consistent processing
                if img.mode not in ['RGB', 'RGBA']:
                    img = img.convert('RGB')
                img_array = np.array(img)
                
            total_pixels = img_array.size
            if len(img_array.shape) == 3:  # RGB/RGBA
                channels = img_array.shape[2]
            else:  # Grayscale
                channels = 1
            
            # Header size: 32 bits for data length + 8 bits for metadata
            header_bits = 40
            
            # Calculate capacity
            usable_bits = total_pixels * bits_per_pixel
            available_bits = usable_bits - header_bits
            
            # Convert to bytes
            available_bytes = max(0, available_bits // 8)
            
            return {
                'pixels': total_pixels,
                'channels': channels,
                'bits_per_pixel': bits_per_pixel,
                'available_bytes': available_bytes,
                'available_bits': available_bits,
                'header_bits': header_bits,
                'image_mode': img.mode,
                'image_size': img.size
            }
            
        except Exception as e:
            raise ValueError(f"Capacity calculation failed: {str(e)}")
    
    def embed_data(self, cover_image_path: str, secret_data: bytes, 
                   output_path: str, bits_per_pixel: int = 1, 
                   use_compression: bool = True) -> Tuple[bool, str]:
        """
        Embed secret data into cover image using custom LSB algorithm
        
        Args:
            cover_image_path: Path to cover image
            secret_data: Bytes to hide
            output_path: Output stego image path
            bits_per_pixel: Number of LSBs to modify
            use_compression: Whether to compress data before embedding
            
        Returns:
            Tuple of (success, message)
        """
        start_time = time.time()
        
        try:
            # Validate bits_per_pixel
            if bits_per_pixel not in [1, 2, 3]:
                return False, "Bits per pixel must be 1, 2, or 3"
            
            # Open and validate image
            with Image.open(cover_image_path) as img:
                # Convert to RGB for consistent processing
                if img.mode not in ['RGB', 'RGBA']:
                    img = img.convert('RGB')
                img_array = np.array(img)
                original_mode = img.mode
                
                # Store original image info for validation
                original_dtype = img_array.dtype
            
            # Compress data if requested
            if use_compression and len(secret_data) > 100:  # Only compress if beneficial
                import zlib
                try:
                    compressed_data = zlib.compress(secret_data, self.compression_level)
                    if len(compressed_data) < len(secret_data):  # Only use if compression helps
                        secret_data = compressed_data
                        compression_flag = 1
                    else:
                        compression_flag = 0
                except:
                    compression_flag = 0
            else:
                compression_flag = 0
            
            # Add metadata header: [4 bytes data length][1 byte metadata]
            data_length = len(secret_data)
            metadata = (compression_flag << 7) | (bits_per_pixel & 0x07)
            
            header = struct.pack('>IB', data_length, metadata)
            data_to_hide = header + secret_data
            
            # Convert to bits
            data_bits = self._bytes_to_bits(data_to_hide)
            
            # Calculate required capacity
            capacity_info = self.calculate_capacity(cover_image_path, bits_per_pixel)
            required_bits = len(data_bits)
            
            if required_bits > capacity_info['available_bits']:
                return False, f"Data too large. Available: {capacity_info['available_bytes']}B, Required: {len(data_to_hide)}B"
            
            # Embed data
            stego_array = self._embed_bits_safe(img_array, data_bits, bits_per_pixel)
            
            # Ensure the array is uint8 and values are in range
            stego_array = np.clip(stego_array, 0, 255).astype(np.uint8)
            
            # Save stego image
            stego_image = Image.fromarray(stego_array, mode='RGB')
            stego_image.save(output_path, format='PNG')  # Save as PNG to avoid compression artifacts
            
            elapsed_time = time.time() - start_time
            
            return True, f"Embedding successful! Output: {output_path}\n" \
                        f"Data size: {len(secret_data)} bytes\n" \
                        f"Capacity used: {(required_bits/capacity_info['available_bits'])*100:.1f}%\n" \
                        f"Time: {elapsed_time:.2f}s"
            
        except Exception as e:
            return False, f"Embedding failed: {str(e)}"
    
    def extract_data(self, stego_image_path: str) -> Tuple[Optional[bytes], str]:
        """
        Extract hidden data from stego image
        
        Args:
            stego_image_path: Path to stego image
            
        Returns:
            Tuple of (extracted_data, message)
        """
        start_time = time.time()
        
        try:
            # Open image
            with Image.open(stego_image_path) as img:
                # Convert to RGB for consistent processing
                if img.mode not in ['RGB', 'RGBA']:
                    img = img.convert('RGB')
                img_array = np.array(img)
            
            # Flatten the image array
            flat_array = img_array.flatten()
            
            # Extract header first (40 bits)
            header_bits = []
            for i in range(40):
                if i < len(flat_array):
                    header_bits.append(flat_array[i] & 1)
                else:
                    return None, "Image too small to contain valid data"
            
            # Convert header bits to bytes
            header_bytes = self._bits_to_bytes(header_bits)
            
            # Parse header
            if len(header_bytes) >= 5:
                data_length = struct.unpack('>I', header_bytes[:4])[0]
                metadata = header_bytes[4]
                compression_flag = (metadata >> 7) & 1
                bits_per_pixel = metadata & 0x07
                
                # Validate extracted values
                if data_length > 10000000:  # Sanity check (max 10MB)
                    return None, "Invalid data length in header"
                if bits_per_pixel not in [1, 2, 3]:
                    bits_per_pixel = 1  # Default to 1 if invalid
            else:
                return None, "Invalid stego image: Header corrupted"
            
            # Calculate total bits needed
            total_bits_needed = 40 + (data_length * 8)
            
            if total_bits_needed > len(flat_array) * bits_per_pixel:
                return None, f"Image too small: Need {total_bits_needed} bits, only {len(flat_array) * bits_per_pixel} available"
            
            # Extract data bits
            data_bits = []
            for i in range(40, min(total_bits_needed, len(flat_array) * bits_per_pixel)):
                pixel_idx = i // bits_per_pixel
                bit_pos = i % bits_per_pixel
                
                if pixel_idx < len(flat_array):
                    bit = (flat_array[pixel_idx] >> bit_pos) & 1
                    data_bits.append(bit)
            
            # Convert to bytes
            extracted_bytes = self._bits_to_bytes(data_bits)
            
            # Trim to actual data length
            extracted_bytes = extracted_bytes[:data_length]
            
            # Decompress if needed
            if compression_flag == 1:
                import zlib
                try:
                    extracted_bytes = zlib.decompress(extracted_bytes)
                except Exception as e:
                    return None, f"Decompression failed: {str(e)}"
            
            elapsed_time = time.time() - start_time
            
            return extracted_bytes, f"Extraction successful!\n" \
                                   f"Data size: {len(extracted_bytes)} bytes\n" \
                                   f"Time: {elapsed_time:.2f}s"
            
        except Exception as e:
            return None, f"Extraction failed: {str(e)}"
    
    def _embed_bits_safe(self, img_array: np.ndarray, data_bits: list, 
                        bits_per_pixel: int) -> np.ndarray:
        """
        Embed bits safely without overflow issues
        
        Args:
            img_array: Original image array
            data_bits: Bits to embed
            bits_per_pixel: Number of LSBs to use
            
        Returns:
            Modified image array
        """
        # Create a copy and convert to int32 for safe manipulation
        stego_array = img_array.copy().astype(np.int32)
        
        # Flatten the array for easier processing
        original_shape = stego_array.shape
        flat_array = stego_array.reshape(-1)
        
        bit_idx = 0
        total_bits = len(data_bits)
        
        # Embed each bit
        for i in range(0, min(len(flat_array) * bits_per_pixel, total_bits * bits_per_pixel)):
            if bit_idx >= total_bits:
                break
            
            pixel_idx = i // bits_per_pixel
            bit_pos = i % bits_per_pixel
            
            if pixel_idx < len(flat_array):
                bit_value = data_bits[bit_idx]
                
                # Clear the target bit and set new value
                # First clear the bit at position bit_pos
                mask = ~(1 << bit_pos)
                flat_array[pixel_idx] = flat_array[pixel_idx] & mask
                # Then set the new bit value
                flat_array[pixel_idx] = flat_array[pixel_idx] | (bit_value << bit_pos)
                
                if bit_pos == bits_per_pixel - 1:
                    bit_idx += 1
        
        # Clip values to uint8 range
        flat_array = np.clip(flat_array, 0, 255)
        
        # Reshape back to original dimensions
        stego_array = flat_array.reshape(original_shape)
        
        return stego_array
    
    def _embed_bits_threaded(self, img_array: np.ndarray, data_bits: list, 
                           bits_per_pixel: int) -> np.ndarray:
        """
        Embed bits using multi-threading for large images
        This is a wrapper around _embed_bits_safe for compatibility
        """
        return self._embed_bits_safe(img_array, data_bits, bits_per_pixel)
    
    def _bytes_to_bits(self, data: bytes) -> list:
        """Convert bytes to list of bits (1s and 0s)"""
        bits = []
        for byte in data:
            for i in range(7, -1, -1):
                bits.append((byte >> i) & 1)
        return bits
    
    def _bits_to_bytes(self, bits: list) -> bytes:
        """Convert list of bits to bytes"""
        if not bits:
            return b''
        
        # Pad to multiple of 8
        while len(bits) % 8 != 0:
            bits.append(0)
        
        bytes_list = []
        for i in range(0, len(bits), 8):
            byte = 0
            for j in range(8):
                if i + j < len(bits):
                    byte = (byte << 1) | bits[i + j]
            bytes_list.append(byte)
        
        return bytes(bytes_list)
    
    def verify_integrity(self, original_image: str, stego_image: str) -> Tuple[bool, str]:
        """
        Verify that stego image hasn't been tampered with
        
        Args:
            original_image: Path to original image
            stego_image: Path to stego image
            
        Returns:
            Tuple of (is_valid, message)
        """
        try:
            with Image.open(original_image) as img1, Image.open(stego_image) as img2:
                if img1.size != img2.size:
                    return False, "Image dimensions don't match"
                
                # Compare visual similarity
                arr1 = np.array(img1.convert('RGB'))
                arr2 = np.array(img2.convert('RGB'))
                
                # Calculate mean squared error
                mse = np.mean((arr1 - arr2) ** 2)
                
                if mse < 10:  # Threshold for acceptable difference
                    return True, f"Integrity verified. MSE: {mse:.2f}"
                else:
                    return False, f"Possible tampering detected. MSE: {mse:.2f}"
                    
        except Exception as e:
            return False, f"Verification failed: {str(e)}"