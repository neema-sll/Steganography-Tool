"""
Utility functions for the steganography tool
"""
import hashlib
import os
from typing import Optional, Tuple
from PIL import Image

def calculate_file_hash(file_path: str, algorithm: str = 'sha256') -> Optional[str]:
    """
    Calculate file hash
    
    Args:
        file_path: Path to file
        algorithm: Hash algorithm ('md5', 'sha1', 'sha256')
        
    Returns:
        Hex digest of file hash or None if error
    """
    hash_func = hashlib.new(algorithm)
    
    try:
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_func.update(chunk)
        return hash_func.hexdigest()
    except Exception:
        return None

def validate_image_file(file_path: str) -> Tuple[bool, str]:
    """
    Validate if file is a valid image
    
    Args:
        file_path: Path to image file
        
    Returns:
        Tuple of (is_valid, message)
    """
    if not os.path.exists(file_path):
        return False, "File does not exist"
    
    try:
        with Image.open(file_path) as img:
            img.verify()  # Verify it's a valid image
            img = Image.open(file_path)  # Reopen for format check
            
            # Check if format is supported
            if img.format not in ['PNG', 'JPEG', 'JPG', 'BMP', 'TIFF']:
                return False, f"Unsupported image format: {img.format}"
            
            # Check image mode
            if img.mode not in ['L', 'RGB', 'RGBA']:
                return False, f"Unsupported image mode: {img.mode}"
            
            return True, f"Valid {img.format} image, size: {img.size}, mode: {img.mode}"
    except Exception as e:
        return False, f"Invalid image file: {str(e)}"

def get_file_size_mb(file_path: str) -> float:
    """
    Get file size in megabytes
    
    Args:
        file_path: Path to file
        
    Returns:
        Size in MB
    """
    if os.path.exists(file_path):
        return os.path.getsize(file_path) / (1024 * 1024)
    return 0.0

def format_file_size(bytes_size: int) -> str:
    """
    Format file size in human readable format
    
    Args:
        bytes_size: Size in bytes
        
    Returns:
        Formatted string (e.g., "1.23 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.2f} TB"

def ensure_directory_exists(dir_path: str) -> bool:
    """
    Ensure directory exists, create if not
    
    Args:
        dir_path: Directory path
        
    Returns:
        True if directory exists or was created
    """
    try:
        os.makedirs(dir_path, exist_ok=True)
        return True
    except Exception:
        return False

def generate_random_filename(prefix: str = 'file', extension: str = '.png') -> str:
    """
    Generate random filename with timestamp
    
    Args:
        prefix: Filename prefix
        extension: File extension
        
    Returns:
        Generated filename
    """
    from datetime import datetime
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    return f"{prefix}_{timestamp}{extension}"