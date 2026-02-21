"""
AES Encryption Manager using cryptography library
"""
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os
import hashlib
from typing import Tuple, Optional 

class EncryptionManager:
    """Handles AES encryption for steganography payloads"""
    
    def __init__(self, password: str = None):
        """
        Initialize encryption manager
        
        Args:
            password: Password for key derivation
        """
        self.password = password.encode() if password else None
        self.salt = b'steg_salt_2024'  # In production, generate unique salt per file
        
    def generate_key(self) -> bytes:
        """Generate encryption key from password"""
        if not self.password:
            # Generate random key if no password
            return Fernet.generate_key()
        
        # Use PBKDF2HMAC for key derivation
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self.salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(self.password))
        return key
    
    def encrypt_data(self, data: bytes, password: str = None) -> Tuple[bytes, bytes]:
        """
        Encrypt data using AES
        
        Args:
            data: Data to encrypt
            password: Optional password override
            
        Returns:
            Tuple of (encrypted_data, key)
        """
        if password:
            self.password = password.encode()
        
        key = self.generate_key()
        fernet = Fernet(key)
        
        # Add integrity check
        encrypted_data = fernet.encrypt(data)
        
        return encrypted_data, key
    
    def decrypt_data(self, encrypted_data: bytes, key: bytes = None, 
                    password: str = None) -> Tuple[Optional[bytes], str]:
        """
        Decrypt data using AES
        
        Args:
            encrypted_data: Data to decrypt
            key: Encryption key (if available)
            password: Password for key derivation
            
        Returns:
            Tuple of (decrypted_data, status_message)
        """
        try:
            if not key and password:
                self.password = password.encode()
                key = self.generate_key()
            elif not key:
                return None, "No key or password provided"
            
            fernet = Fernet(key)
            decrypted_data = fernet.decrypt(encrypted_data)
            
            return decrypted_data, "Decryption successful"
            
        except Exception as e:
            return None, f"Decryption failed: {str(e)}"
    
    def get_key_hash(self, key: bytes) -> str:
        """Generate SHA-256 hash of key for verification"""
        return hashlib.sha256(key).hexdigest()