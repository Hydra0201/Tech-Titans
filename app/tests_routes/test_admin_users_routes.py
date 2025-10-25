# tests/test_admin_users_routes.py
import unittest
from unittest.mock import Mock, MagicMock, patch
import jwt
from flask import Flask, g
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestAdminUsersRoutes(unittest.TestCase):
    
    def setUp(self):
        self.app = Flask(__name__)
        self.app.config['TESTING'] = True
        self.app.config['JWT_SECRET'] = 'test-secret-key'
        self.client = self.app.test_client()
        
        # Import and register blueprint
        from app.routes.admin_users import admin_users_bp
        self.app.register_blueprint(admin_users_bp)
        
    def _create_admin_token(self):
        """Create a valid admin JWT token"""
        return jwt.encode(
            {"sub": "1", "role": "Admin", "email": "admin@example.com"},
            self.app.config['JWT_SECRET'],
            algorithm="HS256"
        )
    
    def _create_user_token(self):
        """Create a non-admin user JWT token"""
        return jwt.encode(
            {"sub": "2", "role": "Client", "email": "user@example.com"},
            self.app.config['JWT_SECRET'],
            algorithm="HS256"
        )
    
    def _create_mock_connection(self):
        """Helper to create a properly mocked database connection"""
        mock_conn = MagicMock()
        mock_result = MagicMock()
        mock_conn.execute.return_value = mock_result
        
        # Setup proper transaction mocking
        mock_tx = MagicMock()
        mock_tx.is_active = True
        mock_tx.rollback = MagicMock()
        mock_tx.commit = MagicMock()
        
        mock_conn.begin.return_value = mock_tx
        mock_conn.begin_nested.return_value = mock_tx
        mock_conn.in_transaction = Mock(return_value=False)  # This should be a callable method
        
        return mock_conn, mock_result
    
    @patch('app.routes.admin_users.get_conn')
    def test_create_user_success(self, mock_get_conn):
        """Test successful user creation by admin"""
        mock_conn, mock_result = self._create_mock_connection()
        mock_get_conn.return_value.__enter__.return_value = mock_conn
        
        # Mock database response
        mock_row = {
            'id': 1,
            'email': 'test@example.com',
            'name': 'Test User',
            'role': 'Client',
            'default_access_level': 'view',
            'created_at': '2023-01-01T00:00:00'
        }
        mock_result.mappings.return_value.one.return_value = mock_row
        
        token = self._create_admin_token()
        
        response = self.client.post(
            '/admin/users',
            json={
                'name': 'Test User',
                'email': 'test@example.com',
                'password': 'password123',
                'role': 'Client',
                'default_access_level': 'view'
            },
            headers={'Authorization': f'Bearer {token}'}
        )
        
        self.assertEqual(response.status_code, 201)
        data = response.get_json()
        self.assertIn('user', data)
        self.assertEqual(data['user']['email'], 'test@example.com')
    
    @patch('app.routes.admin_users.get_conn')
    def test_create_user_unauthorized(self, mock_get_conn):
        """Test user creation without authentication"""
        response = self.client.post(
            '/admin/users',
            json={
                'name': 'Test User',
                'email': 'test@example.com',
                'password': 'password123',
                'role': 'Client'
            }
        )
        
        self.assertEqual(response.status_code, 401)
        data = response.get_json()
        self.assertEqual(data['error'], 'unauthorized')
    
    @patch('app.routes.admin_users.get_conn')
    def test_create_user_forbidden(self, mock_get_conn):
        """Test user creation by non-admin user"""
        token = self._create_user_token()
        
        response = self.client.post(
            '/admin/users',
            json={
                'name': 'Test User',
                'email': 'test@example.com',
                'password': 'password123',
                'role': 'Client'
            },
            headers={'Authorization': f'Bearer {token}'}
        )
        
        self.assertEqual(response.status_code, 403)
        data = response.get_json()
        self.assertEqual(data['error'], 'forbidden')
    
    @patch('app.routes.admin_users.get_conn')
    def test_create_user_invalid_email(self, mock_get_conn):
        """Test user creation with invalid email"""
        token = self._create_admin_token()
        
        response = self.client.post(
            '/admin/users',
            json={
                'name': 'Test User',
                'email': 'invalid-email',
                'password': 'password123',
                'role': 'Client'
            },
            headers={'Authorization': f'Bearer {token}'}
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertEqual(data['error'], 'invalid_email')
    
    @patch('app.routes.admin_users.get_conn')
    def test_create_user_missing_required_fields(self, mock_get_conn):
        """Test user creation with missing required fields"""
        token = self._create_admin_token()
        
        response = self.client.post(
            '/admin/users',
            json={
                'name': 'Test User',
                # Missing email and password
                'role': 'Client'
            },
            headers={'Authorization': f'Bearer {token}'}
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertEqual(data['error'], 'bad_request')

if __name__ == '__main__':
    unittest.main()