import unittest
from unittest.mock import Mock, MagicMock, patch
import jwt
from datetime import datetime, timezone
from flask import Flask
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestAuthRoutes(unittest.TestCase):
    
    def setUp(self):
        self.app = Flask(__name__)
        self.app.config['TESTING'] = True
        self.app.config['JWT_SECRET'] = 'test-secret-key'
        self.app.config['JWT_EXPIRES_HOURS'] = 24
        self.client = self.app.test_client()
        
        # Import and register blueprint
        from app.routes.auth import auth_bp
        self.app.register_blueprint(auth_bp)
        
        # Mock get_conn
        self.mock_conn = MagicMock()
        self.mock_result = MagicMock()
        self.mock_conn.execute.return_value = self.mock_result
        
    @patch('app.routes.auth.get_conn')
    def test_login_success(self, mock_get_conn):
        """Test successful login"""
        mock_get_conn.return_value.__enter__.return_value = self.mock_conn
        
        # Mock user found in database
        mock_row = {
            'id': 1,
            'email': 'test@example.com',
            'name': 'Test User',
            'role': 'Client',
            'default_access_level': 'view',
            'password_hash': '$2b$12$hashed_password'  # bcrypt format
        }
        self.mock_result.mappings.return_value.one_or_none.return_value = mock_row
        
        # Mock password verification
        with patch('app.routes.auth.pwd_ctx.verify', return_value=True):
            response = self.client.post(
                '/api/auth/login',
                json={
                    'email': 'test@example.com',
                    'password': 'correct_password'
                }
            )
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('access_token', data)
        self.assertIn('user', data)
        self.assertEqual(data['user']['email'], 'test@example.com')
        
        # Verify token is valid
        token = data['access_token']
        payload = jwt.decode(token, self.app.config['JWT_SECRET'], algorithms=['HS256'])
        self.assertEqual(payload['email'], 'test@example.com')
        self.assertEqual(payload['role'], 'Client')
    
    @patch('app.routes.auth.get_conn')
    def test_login_user_not_found(self, mock_get_conn):
        """Test login with non-existent user"""
        mock_get_conn.return_value.__enter__.return_value = self.mock_conn
        
        # Mock no user found
        self.mock_result.mappings.return_value.one_or_none.return_value = None
        
        response = self.client.post(
            '/api/auth/login',
            json={
                'email': 'nonexistent@example.com',
                'password': 'password'
            }
        )
        
        self.assertEqual(response.status_code, 401)
        data = response.get_json()
        self.assertEqual(data['error'], 'invalid_credentials')
    
    @patch('app.routes.auth.get_conn')
    def test_login_wrong_password(self, mock_get_conn):
        """Test login with wrong password"""
        mock_get_conn.return_value.__enter__.return_value = self.mock_conn
        
        # Mock user found
        mock_row = {
            'id': 1,
            'email': 'test@example.com',
            'name': 'Test User',
            'role': 'Client',
            'default_access_level': 'view',
            'password_hash': '$2b$12$hashed_password'
        }
        self.mock_result.mappings.return_value.one_or_none.return_value = mock_row
        
        # Mock password verification failure
        with patch('app.routes.auth.pwd_ctx.verify', return_value=False):
            response = self.client.post(
                '/api/auth/login',
                json={
                    'email': 'test@example.com',
                    'password': 'wrong_password'
                }
            )
        
        self.assertEqual(response.status_code, 401)
        data = response.get_json()
        self.assertEqual(data['error'], 'invalid_credentials')
    
    def test_login_missing_credentials(self):
        """Test login with missing email or password"""
        # Missing email
        response = self.client.post(
            '/api/auth/login',
            json={
                'password': 'password'
            }
        )
        self.assertEqual(response.status_code, 400)
        
        # Missing password
        response = self.client.post(
            '/api/auth/login',
            json={
                'email': 'test@example.com'
            }
        )
        self.assertEqual(response.status_code, 400)
    
    @patch('app.routes.auth.get_conn')
    def test_login_werkzeug_hash(self, mock_get_conn):
        """Test login with Werkzeug PBKDF2 hash"""
        mock_get_conn.return_value.__enter__.return_value = self.mock_conn
        
        # Mock user with Werkzeug hash
        mock_row = {
            'id': 1,
            'email': 'test@example.com',
            'name': 'Test User',
            'role': 'Client',
            'default_access_level': 'view',
            'password_hash': 'pbkdf2:sha256:260000$hashed_password'
        }
        self.mock_result.mappings.return_value.one_or_none.return_value = mock_row
        
        # Mock Werkzeug password verification
        with patch('app.routes.auth.wz_check', return_value=True):
            response = self.client.post(
                '/api/auth/login',
                json={
                    'email': 'test@example.com',
                    'password': 'correct_password'
                }
            )
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('access_token', data)

if __name__ == '__main__':
    unittest.main()