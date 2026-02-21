"""
Unit tests for encryption manager
"""
import unittest
import tempfile
import os
import sys

# Add parent directory to path to import src modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.encryption_manager import EncryptionManager

class TestEncryptionManager(unittest.TestCase):
    """Test cases for EncryptionManager"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_data = b"Test secret data for encryption testing!"
        self.password = "test_password_123"
    
    def test_encrypt_decrypt_with_password(self):
        """Test encryption and decryption with password"""
        manager = EncryptionManager(self.password)
        
        # Encrypt
        encrypted_data, key = manager.encrypt_data(self.test_data)
        
        self.assertIsNotNone(encrypted_data)
        self.assertIsNotNone(key)
        self.assertNotEqual(encrypted_data, self.test_data)
        
        # Decrypt with password
        manager2 = EncryptionManager(self.password)
        decrypted_data, message = manager2.decrypt_data(encrypted_data, password=self.password)
        
        self.assertIsNotNone(decrypted_data)
        self.assertEqual(decrypted_data, self.test_data)
        self.assertIn("successful", message.lower())
    
    def test_encrypt_decrypt_with_key(self):
        """Test encryption and decryption with key"""
        manager = EncryptionManager()
        
        # Encrypt
        encrypted_data, key = manager.encrypt_data(self.test_data)
        
        # Decrypt with key
        decrypted_data, message = manager.decrypt_data(encrypted_data, key=key)
        
        self.assertIsNotNone(decrypted_data)
        self.assertEqual(decrypted_data, self.test_data)
        self.assertIn("successful", message.lower())
    
    def test_wrong_password_fails(self):
        """Test that wrong password fails decryption"""
        manager = EncryptionManager(self.password)
        
        encrypted_data, key = manager.encrypt_data(self.test_data)
        
        # Try wrong password
        decrypted_data, message = manager.decrypt_data(encrypted_data, password="wrong_password")
        
        self.assertIsNone(decrypted_data)
        self.assertIn("failed", message.lower())
    
    def test_wrong_key_fails(self):
        """Test that wrong key fails decryption"""
        manager = EncryptionManager()
        
        encrypted_data, key = manager.encrypt_data(self.test_data)
        
        # Create wrong key (Fernet keys are 44 bytes when base64 encoded)
        wrong_key = b"x" * 44
        
        decrypted_data, message = manager.decrypt_data(encrypted_data, key=wrong_key)
        
        self.assertIsNone(decrypted_data)
        self.assertIn("failed", message.lower())
    
    def test_key_hash(self):
        """Test key hash generation"""
        manager = EncryptionManager(self.password)
        
        encrypted_data, key = manager.encrypt_data(self.test_data)
        key_hash = manager.get_key_hash(key)
        
        self.assertEqual(len(key_hash), 64)  # SHA256 produces 64 char hex
        self.assertIsInstance(key_hash, str)
    
    def test_empty_data(self):
        """Test encryption of empty data"""
        manager = EncryptionManager(self.password)
        
        encrypted_data, key = manager.encrypt_data(b"")
        
        self.assertIsNotNone(encrypted_data)
        
        decrypted_data, message = manager.decrypt_data(encrypted_data, password=self.password)
        
        self.assertEqual(decrypted_data, b"")
    
    def test_no_password_no_key(self):
        """Test encryption without password (auto-generated key)"""
        manager = EncryptionManager()
        
        encrypted_data, key = manager.encrypt_data(self.test_data)
        
        self.assertIsNotNone(key)
        self.assertNotEqual(encrypted_data, self.test_data)
        
        # Decrypt with key
        decrypted_data, message = manager.decrypt_data(encrypted_data, key=key)
        
        self.assertEqual(decrypted_data, self.test_data)
    
    def test_large_data(self):
        """Test encryption of large data"""
        manager = EncryptionManager(self.password)
        
        # Generate 1MB of test data
        large_data = os.urandom(1024 * 1024)
        
        encrypted_data, key = manager.encrypt_data(large_data)
        
        self.assertIsNotNone(encrypted_data)
        
        decrypted_data, message = manager.decrypt_data(encrypted_data, password=self.password)
        
        self.assertEqual(decrypted_data, large_data)
    
    def test_special_characters_password(self):
        """Test with password containing special characters"""
        special_password = "!@#$%^&*()_+{}[]|\\:;\"'<>,.?/~`"
        manager = EncryptionManager(special_password)
        
        encrypted_data, key = manager.encrypt_data(self.test_data)
        
        decrypted_data, message = manager.decrypt_data(encrypted_data, password=special_password)
        
        self.assertEqual(decrypted_data, self.test_data)
    
    def test_unicode_data(self):
        """Test encryption of unicode data"""
        unicode_data = "Hello 世界 🌍".encode('utf-8')
        manager = EncryptionManager(self.password)
        
        encrypted_data, key = manager.encrypt_data(unicode_data)
        
        decrypted_data, message = manager.decrypt_data(encrypted_data, password=self.password)
        
        self.assertEqual(decrypted_data, unicode_data)


if __name__ == '__main__':
    unittest.main()