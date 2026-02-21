"""
Unit tests for steganography engine
"""
import unittest
import tempfile
import os
from PIL import Image
import numpy as np
import sys
import os

# Add parent directory to path to import src modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.steganography_engine import SteganographyEngine

class TestSteganographyEngine(unittest.TestCase):
    """Test cases for SteganographyEngine"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.engine = SteganographyEngine()
        
        # Create test image
        self.test_image_path = tempfile.mktemp(suffix='.png')
        self.create_test_image()
        
        # Test data
        self.test_data = b"Test secret message for steganography!"
        
    def tearDown(self):
        """Clean up test fixtures"""
        if os.path.exists(self.test_image_path):
            os.remove(self.test_image_path)
    
    def create_test_image(self, size=(100, 100)):
        """Create a test image"""
        img_array = np.random.randint(0, 256, (size[0], size[1], 3), dtype=np.uint8)
        img = Image.fromarray(img_array, 'RGB')
        img.save(self.test_image_path)
    
    def test_capacity_calculation(self):
        """Test capacity calculation"""
        capacity = self.engine.calculate_capacity(self.test_image_path, bits_per_pixel=1)
        
        self.assertIn('pixels', capacity)
        self.assertIn('available_bytes', capacity)
        self.assertIn('available_bits', capacity)
        
        # 100x100 RGB image = 30,000 pixels
        self.assertEqual(capacity['pixels'], 30000)
        
        # With 1 bit per pixel, should have reasonable capacity
        self.assertGreater(capacity['available_bytes'], 1000)
    
    def test_embed_extract_cycle(self):
        """Test complete embed/extract cycle"""
        output_path = tempfile.mktemp(suffix='.png')
        
        try:
            # Embed data
            success, message = self.engine.embed_data(
                self.test_image_path,
                self.test_data,
                output_path,
                bits_per_pixel=1
            )
            
            self.assertTrue(success, f"Embedding failed: {message}")
            self.assertTrue(os.path.exists(output_path))
            
            # Extract data
            extracted_data, message = self.engine.extract_data(output_path)
            
            self.assertIsNotNone(extracted_data, f"Extraction failed: {message}")
            self.assertEqual(extracted_data, self.test_data)
            
        finally:
            if os.path.exists(output_path):
                os.remove(output_path)
    
    def test_different_bits_per_pixel(self):
        """Test with different bits per pixel settings"""
        for bits in [1, 2, 3]:
            with self.subTest(bits=bits):
                output_path = tempfile.mktemp(suffix='.png')
                
                try:
                    success, message = self.engine.embed_data(
                        self.test_image_path,
                        self.test_data,
                        output_path,
                        bits_per_pixel=bits
                    )
                    
                    self.assertTrue(success, f"Embedding failed with bits={bits}: {message}")
                    
                    extracted_data, message = self.engine.extract_data(output_path)
                    
                    self.assertIsNotNone(extracted_data, 
                                       f"Extraction failed with bits={bits}: {message}")
                    self.assertEqual(extracted_data, self.test_data)
                    
                finally:
                    if os.path.exists(output_path):
                        os.remove(output_path)
    
    def test_large_data_embedding(self):
        """Test embedding data close to capacity"""
        capacity = self.engine.calculate_capacity(self.test_image_path, bits_per_pixel=2)
        max_data_size = capacity['available_bytes'] - 100  # Leave some margin
        
        # Generate test data of appropriate size
        large_data = os.urandom(max_data_size)
        
        output_path = tempfile.mktemp(suffix='.png')
        
        try:
            success, message = self.engine.embed_data(
                self.test_image_path,
                large_data,
                output_path,
                bits_per_pixel=2
            )
            
            self.assertTrue(success, f"Large data embedding failed: {message}")
            
            extracted_data, message = self.engine.extract_data(output_path)
            
            self.assertIsNotNone(extracted_data)
            self.assertEqual(extracted_data, large_data)
            
        finally:
            if os.path.exists(output_path):
                os.remove(output_path)
    
    def test_overflow_data(self):
        """Test that overflow data is rejected"""
        capacity = self.engine.calculate_capacity(self.test_image_path, bits_per_pixel=1)
        overflow_data = os.urandom(capacity['available_bytes'] + 1000)
        
        output_path = tempfile.mktemp(suffix='.png')
        
        try:
            success, message = self.engine.embed_data(
                self.test_image_path,
                overflow_data,
                output_path,
                bits_per_pixel=1
            )
            
            self.assertFalse(success)
            self.assertIn("too large", message.lower())
            
        finally:
            if os.path.exists(output_path):
                os.remove(output_path)
    
    def test_compression(self):
        """Test data compression"""
        # Create data that compresses well
        compressible_data = b"A" * 1000
        
        output_path = tempfile.mktemp(suffix='.png')
        
        try:
            # Test with compression
            success, message = self.engine.embed_data(
                self.test_image_path,
                compressible_data,
                output_path,
                bits_per_pixel=1,
                use_compression=True
            )
            
            self.assertTrue(success)
            
            extracted_data, message = self.engine.extract_data(output_path)
            
            self.assertIsNotNone(extracted_data)
            self.assertEqual(extracted_data, compressible_data)
            
        finally:
            if os.path.exists(output_path):
                os.remove(output_path)
    
    def test_no_compression(self):
        """Test without compression"""
        # Create random data
        random_data = os.urandom(500)
        
        output_path = tempfile.mktemp(suffix='.png')
        
        try:
            # Test without compression
            success, message = self.engine.embed_data(
                self.test_image_path,
                random_data,
                output_path,
                bits_per_pixel=1,
                use_compression=False
            )
            
            self.assertTrue(success)
            
            extracted_data, message = self.engine.extract_data(output_path)
            
            self.assertIsNotNone(extracted_data)
            self.assertEqual(extracted_data, random_data)
            
        finally:
            if os.path.exists(output_path):
                os.remove(output_path)
    
    def test_invalid_image(self):
        """Test with invalid image file"""
        invalid_path = "/nonexistent/image.png"
        
        with self.assertRaises(ValueError):
            self.engine.calculate_capacity(invalid_path)
    
    def test_bytes_to_bits_conversion(self):
        """Test byte-to-bit conversion"""
        test_bytes = b"\x01\x02\x03"  # 00000001 00000010 00000011
        
        bits = self.engine._bytes_to_bits(test_bytes)
        
        self.assertEqual(len(bits), 24)
        self.assertEqual(bits[:8], [0, 0, 0, 0, 0, 0, 0, 1])
        self.assertEqual(bits[8:16], [0, 0, 0, 0, 0, 0, 1, 0])
    
    def test_bits_to_bytes_conversion(self):
        """Test bit-to-byte conversion"""
        bits = [0, 0, 0, 0, 0, 0, 0, 1,  # 1
                0, 0, 0, 0, 0, 0, 1, 0,  # 2
                0, 0, 0, 0, 0, 0, 1, 1]  # 3
        
        bytes_data = self.engine._bits_to_bytes(bits)
        
        self.assertEqual(bytes_data, b"\x01\x02\x03")
    
    def test_empty_data(self):
        """Test embedding empty data"""
        output_path = tempfile.mktemp(suffix='.png')
        
        try:
            success, message = self.engine.embed_data(
                self.test_image_path,
                b"",
                output_path,
                bits_per_pixel=1
            )
            
            self.assertTrue(success)
            
            extracted_data, message = self.engine.extract_data(output_path)
            
            self.assertIsNotNone(extracted_data)
            self.assertEqual(extracted_data, b"")
            
        finally:
            if os.path.exists(output_path):
                os.remove(output_path)
    
    def test_different_image_formats(self):
        """Test with different image formats"""
        # Create test images in different formats
        formats = [
            ('PNG', '.png'),
            ('JPEG', '.jpg'),
            ('BMP', '.bmp')
        ]
        
        for fmt, ext in formats:
            with self.subTest(format=fmt):
                # Create image
                img_path = tempfile.mktemp(suffix=ext)
                img_array = np.random.randint(0, 256, (50, 50, 3), dtype=np.uint8)
                img = Image.fromarray(img_array, 'RGB')
                img.save(img_path, format=fmt)
                
                output_path = tempfile.mktemp(suffix='.png')
                
                try:
                    # Test embedding
                    success, message = self.engine.embed_data(
                        img_path,
                        self.test_data,
                        output_path,
                        bits_per_pixel=1
                    )
                    
                    self.assertTrue(success, f"Failed with {fmt}: {message}")
                    
                    # Test extraction
                    extracted_data, message = self.engine.extract_data(output_path)
                    
                    self.assertIsNotNone(extracted_data)
                    self.assertEqual(extracted_data, self.test_data)
                    
                finally:
                    if os.path.exists(img_path):
                        os.remove(img_path)
                    if os.path.exists(output_path):
                        os.remove(output_path)
    
    def test_grayscale_image(self):
        """Test with grayscale image"""
        # Create grayscale image
        img_path = tempfile.mktemp(suffix='.png')
        img_array = np.random.randint(0, 256, (100, 100), dtype=np.uint8)
        img = Image.fromarray(img_array, 'L')
        img.save(img_path)
        
        output_path = tempfile.mktemp(suffix='.png')
        
        try:
            # Test embedding
            success, message = self.engine.embed_data(
                img_path,
                self.test_data,
                output_path,
                bits_per_pixel=1
            )
            
            self.assertTrue(success)
            
            # Test extraction
            extracted_data, message = self.engine.extract_data(output_path)
            
            self.assertIsNotNone(extracted_data)
            self.assertEqual(extracted_data, self.test_data)
            
        finally:
            if os.path.exists(img_path):
                os.remove(img_path)
            if os.path.exists(output_path):
                os.remove(output_path)


if __name__ == '__main__':
    unittest.main()