"""
Database manager for audit logging and session persistence
"""
import sqlite3
from datetime import datetime
from typing import List, Dict, Any
import json
import os
import hashlib

class DatabaseManager:
    """Manages SQLite database for steganography operations"""
    
    def __init__(self, db_path: str = "steganography.db"):
        """
        Initialize database connection
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create operations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS operations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                operation_type TEXT NOT NULL,
                input_file TEXT,
                output_file TEXT,
                data_size INTEGER,
                encryption_used BOOLEAN,
                success BOOLEAN,
                error_message TEXT,
                metadata TEXT
            )
        ''')
        
        # Create sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT UNIQUE NOT NULL,
                start_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                end_time DATETIME,
                total_operations INTEGER DEFAULT 0,
                platform TEXT,
                user_agent TEXT
            )
        ''')
        
        # Create file_hashes table for integrity verification
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS file_hashes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT UNIQUE NOT NULL,
                hash_algorithm TEXT DEFAULT 'SHA256',
                file_hash TEXT NOT NULL,
                computed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                verified BOOLEAN DEFAULT TRUE
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def log_operation(self, operation_type: str, input_file: str = None, 
                     output_file: str = None, data_size: int = None, 
                     encryption_used: bool = False, success: bool = True, 
                     error_message: str = None, metadata: Dict = None):
        """
        Log an operation to the database
        
        Args:
            operation_type: 'embed' or 'extract'
            input_file: Input file path
            output_file: Output file path
            data_size: Size of hidden data in bytes
            encryption_used: Whether encryption was used
            success: Whether operation succeeded
            error_message: Error message if failed
            metadata: Additional metadata as dictionary
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        metadata_json = json.dumps(metadata) if metadata else None
        
        cursor.execute('''
            INSERT INTO operations 
            (operation_type, input_file, output_file, data_size, 
             encryption_used, success, error_message, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (operation_type, input_file, output_file, data_size, 
              encryption_used, success, error_message, metadata_json))
        
        conn.commit()
        conn.close()
    
    def start_session(self, session_id: str, platform: str = None, 
                     user_agent: str = None) -> bool:
        """
        Start a new session
        
        Args:
            session_id: Unique session identifier
            platform: Platform information
            user_agent: User agent string
            
        Returns:
            True if session started successfully
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO sessions (session_id, platform, user_agent)
                VALUES (?, ?, ?)
            ''', (session_id, platform, user_agent))
            
            conn.commit()
            conn.close()
            return True
        except:
            return False
    
    def end_session(self, session_id: str):
        """End a session"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE sessions 
            SET end_time = CURRENT_TIMESTAMP
            WHERE session_id = ?
        ''', (session_id,))
        
        conn.commit()
        conn.close()
    
    def get_operation_history(self, limit: int = 100) -> List[Dict]:
        """
        Retrieve operation history
        
        Args:
            limit: Maximum number of records to return
            
        Returns:
            List of operation dictionaries
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM operations 
            ORDER BY timestamp DESC 
            LIMIT ?
        ''', (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def store_file_hash(self, file_path: str, file_hash: str, 
                       algorithm: str = 'SHA256'):
        """
        Store file hash for integrity verification
        
        Args:
            file_path: Path to file
            file_hash: Computed hash
            algorithm: Hash algorithm used
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO file_hashes 
            (file_path, hash_algorithm, file_hash)
            VALUES (?, ?, ?)
        ''', (file_path, algorithm, file_hash))
        
        conn.commit()
        conn.close()
    
    def verify_file_integrity(self, file_path: str) -> Dict[str, Any]:
        """
        Verify file integrity against stored hash
        
        Args:
            file_path: Path to file to verify
            
        Returns:
            Dictionary with verification results
        """
        if not os.path.exists(file_path):
            return {'verified': False, 'error': 'File not found'}
        
        # Compute current hash
        sha256_hash = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            current_hash = sha256_hash.hexdigest()
        except:
            return {'verified': False, 'error': 'Could not read file'}
        
        # Get stored hash
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT file_hash FROM file_hashes 
            WHERE file_path = ?
        ''', (file_path,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            stored_hash = result[0]
            verified = (current_hash == stored_hash)
            
            return {
                'verified': verified,
                'current_hash': current_hash,
                'stored_hash': stored_hash,
                'match': verified
            }
        else:
            return {
                'verified': False,
                'error': 'No stored hash found',
                'current_hash': current_hash
            }