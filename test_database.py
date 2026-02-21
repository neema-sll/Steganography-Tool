"""
Unit tests for database manager
"""
import unittest
import tempfile
import os
import json
import sys
import sqlite3

# Add parent directory to path to import src modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.database_manager import DatabaseManager

class TestDatabaseManager(unittest.TestCase):
    """Test cases for DatabaseManager"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.db_path = tempfile.mktemp(suffix='.db')
        self.db_manager = DatabaseManager(self.db_path)
    
    def tearDown(self):
        """Clean up test fixtures"""
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
    
    def test_database_creation(self):
        """Test database and tables are created"""
        self.assertTrue(os.path.exists(self.db_path))
        
        # Check if tables exist by trying to insert data
        self.db_manager.log_operation(
            operation_type='test',
            input_file='test_input.png',
            output_file='test_output.png',
            data_size=100,
            encryption_used=False,
            success=True
        )
        
        history = self.db_manager.get_operation_history(limit=1)
        
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]['operation_type'], 'test')
    
    def test_log_operation(self):
        """Test logging operations"""
        # Log successful operation
        self.db_manager.log_operation(
            operation_type='embed',
            input_file='input.jpg',
            output_file='output.png',
            data_size=1024,
            encryption_used=True,
            success=True,
            metadata={'bits': 2, 'compression': True}
        )
        
        # Log failed operation
        self.db_manager.log_operation(
            operation_type='extract',
            input_file='corrupted.png',
            data_size=None,
            encryption_used=False,
            success=False,
            error_message='Invalid stego image'
        )
        
        history = self.db_manager.get_operation_history(limit=10)
        
        self.assertEqual(len(history), 2)
        
        # Check first operation (most recent is failed operation)
        op1 = history[0]
        self.assertEqual(op1['operation_type'], 'extract')
        self.assertFalse(op1['success'])
        self.assertIsNotNone(op1['error_message'])
        
        # Check second operation
        op2 = history[1]
        self.assertEqual(op2['operation_type'], 'embed')
        self.assertTrue(op2['success'])
        self.assertEqual(op2['data_size'], 1024)
        self.assertTrue(op2['encryption_used'])
    
    def test_session_management(self):
        """Test session start and end"""
        session_id = 'test_session_123'
        
        # Start session
        success = self.db_manager.start_session(session_id, 'test', 'TestClient')
        self.assertTrue(success)
        
        # End session
        self.db_manager.end_session(session_id)
        
        # Verify session exists in database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM sessions WHERE session_id = ?', (session_id,))
        session = cursor.fetchone()
        
        conn.close()
        
        self.assertIsNotNone(session)
        self.assertEqual(session[1], session_id)  # session_id column
        self.assertIsNotNone(session[3])  # end_time should be set
    
    def test_duplicate_session(self):
        """Test starting duplicate session"""
        session_id = 'test_session_123'
        
        # Start first session
        success1 = self.db_manager.start_session(session_id)
        self.assertTrue(success1)
        
        # Try to start duplicate session
        success2 = self.db_manager.start_session(session_id)
        self.assertFalse(success2)  # Should fail
    
    def test_file_hash_storage(self):
        """Test file hash storage and retrieval"""
        test_file = tempfile.mktemp()
        test_hash = 'a' * 64  # Mock SHA256 hash
        
        # Store hash
        self.db_manager.store_file_hash(test_file, test_hash)
        
        # Verify integrity (file doesn't exist yet)
        result = self.db_manager.verify_file_integrity(test_file)
        
        self.assertEqual(result['stored_hash'], test_hash)
        self.assertFalse(result['verified'])  # File doesn't exist, so can't verify
    
    def test_metadata_json(self):
        """Test JSON metadata storage"""
        metadata = {
            'bits_per_pixel': 2,
            'compression': True,
            'encryption': 'AES-256',
            'custom_field': 'test_value',
            'nested': {'key': 'value'}
        }
        
        self.db_manager.log_operation(
            operation_type='embed',
            input_file='test.png',
            output_file='out.png',
            data_size=500,
            encryption_used=True,
            success=True,
            metadata=metadata
        )
        
        history = self.db_manager.get_operation_history(limit=1)
        
        self.assertIsNotNone(history[0]['metadata'])
        
        # Parse metadata back
        parsed_metadata = json.loads(history[0]['metadata'])
        
        self.assertEqual(parsed_metadata['bits_per_pixel'], 2)
        self.assertEqual(parsed_metadata['custom_field'], 'test_value')
        self.assertEqual(parsed_metadata['nested']['key'], 'value')
    
    def test_get_operation_history_limit(self):
        """Test history limit parameter"""
        # Add multiple operations
        for i in range(15):
            self.db_manager.log_operation(
                operation_type=f'test_{i}',
                input_file=f'input_{i}.png',
                data_size=i * 100,
                success=True
            )
        
        # Get limited history
        history = self.db_manager.get_operation_history(limit=5)
        
        self.assertEqual(len(history), 5)
    
    def test_verify_existing_file(self):
        """Test integrity verification with existing file"""
        # Create a test file
        test_file = tempfile.mktemp()
        with open(test_file, 'w') as f:
            f.write("Test content")
        
        try:
            # Store its hash
            import hashlib
            with open(test_file, 'rb') as f:
                file_hash = hashlib.sha256(f.read()).hexdigest()
            
            self.db_manager.store_file_hash(test_file, file_hash)
            
            # Verify - should pass
            result = self.db_manager.verify_file_integrity(test_file)
            
            self.assertTrue(result['verified'])
            self.assertEqual(result['current_hash'], file_hash)
            
            # Modify file
            with open(test_file, 'a') as f:
                f.write("modified")
            
            # Verify again - should fail
            result = self.db_manager.verify_file_integrity(test_file)
            
            self.assertFalse(result['verified'])
            self.assertNotEqual(result['current_hash'], file_hash)
            
        finally:
            if os.path.exists(test_file):
                os.remove(test_file)
    
    def test_null_values(self):
        """Test logging with null values"""
        self.db_manager.log_operation(
            operation_type='embed',
            input_file=None,
            output_file=None,
            data_size=None,
            encryption_used=False,
            success=True
        )
        
        history = self.db_manager.get_operation_history(limit=1)
        
        self.assertEqual(history[0]['input_file'], None)
        self.assertEqual(history[0]['output_file'], None)
        self.assertEqual(history[0]['data_size'], None)
    
    def test_error_message_logging(self):
        """Test error message logging"""
        error_msg = "Test error message with special chars !@#$%^&*()"
        
        self.db_manager.log_operation(
            operation_type='embed',
            input_file='test.png',
            success=False,
            error_message=error_msg
        )
        
        history = self.db_manager.get_operation_history(limit=1)
        
        self.assertEqual(history[0]['error_message'], error_msg)
    
    def test_multiple_sessions(self):
        """Test multiple sessions"""
        sessions = ['session_1', 'session_2', 'session_3']
        
        for session_id in sessions:
            self.db_manager.start_session(session_id, 'test', 'TestClient')
        
        # Check sessions in database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM sessions')
        count = cursor.fetchone()[0]
        
        conn.close()
        
        self.assertEqual(count, 3)


if __name__ == '__main__':
    unittest.main()