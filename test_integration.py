"""
Integration tests for complete steganography workflow
"""
import unittest
import tempfile
import os
from PIL import Image
import numpy as np
import sys
import hashlib

# Add parent directory to path to import src modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.steganography_engine import SteganographyEngine
from src.encryption_manager import EncryptionManager
from src.database_manager import DatabaseManager

class TestIntegration(unittest.TestCase):
    """Integration tests for complete workflow"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.engine = SteganographyEngine()
        self.encryption = EncryptionManager()
        
        # Create test database
        self.db_path = tempfile.mktemp(suffix='.db')
        self.db_manager = DatabaseManager(self.db_path)
        
        # Create test image
        self.test_image_path = tempfile.mktemp(suffix='.png')
        self.create_test_image()
        
        # Test data
        self.test_data = b"Integration test secret data!"
    
    def tearDown(self):
        """Clean up test fixtures"""
        for path in [self.test_image_path, self.db_path]:
            if os.path.exists(path):
                os.remove(path)
    
    def create_test_image(self, size=(200, 200)):
        """Create a test image"""
        img_array = np.random.randint(0, 256, (size[0], size[1], 3), dtype=np.uint8)
        img = Image.fromarray(img_array, 'RGB')
        img.save(self.test_image_path)
    
    def test_complete_workflow_with_encryption(self):
        """Test complete encode->database->decode workflow with encryption"""
        password = "secure_password_123"
        output_path = tempfile.mktemp(suffix='.png')
        
        try:
            # 1. Encrypt data
            encryption_mgr = EncryptionManager(password)
            encrypted_data, key = encryption_mgr.encrypt_data(self.test_data)
            
            # 2. Embed encrypted data
            success, message = self.engine.embed_data(
                self.test_image_path,
                encrypted_data,
                output_path,
                bits_per_pixel=2,
                use_compression=True
            )
            
            self.assertTrue(success, f"Embedding failed: {message}")
            
            # 3. Log operation to database
            metadata = {
                'bits_per_pixel': 2,
                'compression': True,
                'encryption': 'AES-256',
                'key_hash': encryption_mgr.get_key_hash(key)
            }
            
            self.db_manager.log_operation(
                operation_type='embed',
                input_file=self.test_image_path,
                output_file=output_path,
                data_size=len(encrypted_data),
                encryption_used=True,
                success=True,
                metadata=metadata
            )
            
            # 4. Store file hash for integrity
            with open(output_path, 'rb') as f:
                file_hash = hashlib.sha256(f.read()).hexdigest()
            self.db_manager.store_file_hash(output_path, file_hash)
            
            # 5. Verify file integrity
            integrity_result = self.db_manager.verify_file_integrity(output_path)
            self.assertTrue(integrity_result['verified'])
            
            # 6. Extract data
            extracted_encrypted, extract_msg = self.engine.extract_data(output_path)
            self.assertIsNotNone(extracted_encrypted, f"Extraction failed: {extract_msg}")
            
            # 7. Decrypt data
            decryption_mgr = EncryptionManager(password)
            decrypted_data, decrypt_msg = decryption_mgr.decrypt_data(
                extracted_encrypted, password=password
            )
            
            self.assertIsNotNone(decrypted_data, f"Decryption failed: {decrypt_msg}")
            self.assertEqual(decrypted_data, self.test_data)
            
            # 8. Log extraction operation
            self.db_manager.log_operation(
                operation_type='extract',
                input_file=output_path,
                data_size=len(decrypted_data),
                encryption_used=True,
                success=True
            )
            
            # 9. Verify operation history
            history = self.db_manager.get_operation_history(limit=10)
            self.assertGreaterEqual(len(history), 2)
            
            embed_ops = [op for op in history if op['operation_type'] == 'embed']
            extract_ops = [op for op in history if op['operation_type'] == 'extract']
            
            self.assertGreaterEqual(len(embed_ops), 1)
            self.assertGreaterEqual(len(extract_ops), 1)
            
        finally:
            if os.path.exists(output_path):
                os.remove(output_path)
    
    def test_workflow_without_encryption(self):
        """Test workflow without encryption"""
        output_path = tempfile.mktemp(suffix='.png')
        
        try:
            # Embed data
            success, message = self.engine.embed_data(
                self.test_image_path,
                self.test_data,
                output_path,
                bits_per_pixel=1
            )
            
            self.assertTrue(success)
            
            # Log operation
            self.db_manager.log_operation(
                operation_type='embed',
                input_file=self.test_image_path,
                output_file=output_path,
                data_size=len(self.test_data),
                encryption_used=False,
                success=True
            )
            
            # Extract data
            extracted_data, message = self.engine.extract_data(output_path)
            
            self.assertIsNotNone(extracted_data)
            self.assertEqual(extracted_data, self.test_data)
            
            # Verify no encryption was used
            history = self.db_manager.get_operation_history(limit=1)
            self.assertFalse(history[0]['encryption_used'])
            
        finally:
            if os.path.exists(output_path):
                os.remove(output_path)
    
    def test_session_tracking(self):
        """Test session tracking in workflow"""
        session_id = 'integration_test_session'
        
        # Start session
        self.db_manager.start_session(session_id, 'integration_test', 'TestRunner')
        
        # Perform operations
        for i in range(3):
            self.db_manager.log_operation(
                operation_type=f'test_{i}',
                input_file=f'test_{i}.png',
                success=True
            )
        
        # End session
        self.db_manager.end_session(session_id)
        
        # Verify session in database
        import sqlite3
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM sessions WHERE session_id = ?', (session_id,))
        session = cursor.fetchone()
        
        conn.close()
        
        self.assertIsNotNone(session)
        self.assertEqual(session[1], session_id)  # session_id column
        self.assertIsNotNone(session[3])  # end_time should be set
    
    def test_error_handling_workflow(self):
        """Test error handling in complete workflow"""
        # Try to embed too much data
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
            
            # Log failed operation
            self.db_manager.log_operation(
                operation_type='embed',
                input_file=self.test_image_path,
                output_file=output_path,
                data_size=len(overflow_data),
                encryption_used=False,
                success=False,
                error_message=message
            )
            
            # Verify failed operation in history
            history = self.db_manager.get_operation_history(limit=1)
            self.assertFalse(history[0]['success'])
            self.assertIsNotNone(history[0]['error_message'])
            
        finally:
            if os.path.exists(output_path):
                os.remove(output_path)
    
    def test_different_image_formats(self):
        """Test workflow with different image formats"""
        test_formats = [
            ('JPEG', '.jpg'),
            ('PNG', '.png'),
            ('BMP', '.bmp')
        ]
        
        for format_name, extension in test_formats:
            with self.subTest(format=format_name):
                # Create image in specific format
                img_path = tempfile.mktemp(suffix=extension)
                img_array = np.random.randint(0, 256, (100, 100, 3), dtype=np.uint8)
                img = Image.fromarray(img_array, 'RGB')
                img.save(img_path, format=format_name)
                
                output_path = tempfile.mktemp(suffix='.png')
                
                try:
                    # Test embedding
                    success, message = self.engine.embed_data(
                        img_path,
                        self.test_data,
                        output_path,
                        bits_per_pixel=1
                    )
                    
                    self.assertTrue(success, f"Failed with {format_name}: {message}")
                    
                    # Test extraction
                    extracted_data, message = self.engine.extract_data(output_path)
                    
                    self.assertIsNotNone(extracted_data, 
                                       f"Extraction failed with {format_name}: {message}")
                    self.assertEqual(extracted_data, self.test_data)
                    
                finally:
                    for path in [img_path, output_path]:
                        if os.path.exists(path):
                            os.remove(path)
    
    def test_multiple_operations(self):
        """Test multiple encode/decode operations"""
        num_operations = 3
        output_paths = []
        
        try:
            for i in range(num_operations):
                # Create unique test data
                test_data = f"Test data {i}".encode('utf-8')
                output_path = tempfile.mktemp(suffix='.png')
                output_paths.append(output_path)
                
                # Encode
                success, message = self.engine.embed_data(
                    self.test_image_path,
                    test_data,
                    output_path,
                    bits_per_pixel=1
                )
                
                self.assertTrue(success)
                
                # Log operation
                self.db_manager.log_operation(
                    operation_type='embed',
                    input_file=self.test_image_path,
                    output_file=output_path,
                    data_size=len(test_data),
                    encryption_used=False,
                    success=True
                )
                
                # Decode
                extracted_data, message = self.engine.extract_data(output_path)
                
                self.assertIsNotNone(extracted_data)
                self.assertEqual(extracted_data, test_data)
            
            # Verify all operations were logged
            history = self.db_manager.get_operation_history(limit=10)
            embed_ops = [op for op in history if op['operation_type'] == 'embed']
            self.assertEqual(len(embed_ops), num_operations)
            
        finally:
            for path in output_paths:
                if os.path.exists(path):
                    os.remove(path)
    
    def test_compression_with_encryption(self):
        """Test compression combined with encryption"""
        password = "test_password"
        compressible_data = b"AAAAA" * 1000  # Highly compressible
        
        output_path = tempfile.mktemp(suffix='.png')
        
        try:
            # Encrypt
            enc_mgr = EncryptionManager(password)
            encrypted_data, key = enc_mgr.encrypt_data(compressible_data)
            
            # Embed with compression
            success, message = self.engine.embed_data(
                self.test_image_path,
                encrypted_data,
                output_path,
                bits_per_pixel=2,
                use_compression=True
            )
            
            self.assertTrue(success)
            
            # Extract
            extracted_encrypted, message = self.engine.extract_data(output_path)
            self.assertIsNotNone(extracted_encrypted)
            
            # Decrypt
            decrypted_data, message = enc_mgr.decrypt_data(extracted_encrypted, password=password)
            self.assertIsNotNone(decrypted_data)
            self.assertEqual(decrypted_data, compressible_data)
            
        finally:
            if os.path.exists(output_path):
                os.remove(output_path)


if __name__ == '__main__':
    unittest.main()