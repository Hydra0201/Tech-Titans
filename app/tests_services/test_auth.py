# Make sure JWT_SECRET is set for testing to run the test do this before
# export JWT_SECRET="test-secret-key-for-testing-only"

import unittest
from unittest.mock import patch, MagicMock
import datetime
import jwt
import os
import sys
from werkzeug.security import generate_password_hash, check_password_hash

# Mock the database dependencies before importing auth
sys.modules['app.db.engine'] = MagicMock()
sys.modules['app.models.user'] = MagicMock()

# Create proper mock enums
class MockRoleEnum:
    Admin = "admin"
    User = "user"
    
    def __init__(self, value):
        if value not in [self.Admin, self.User]:
            raise ValueError(f"Invalid role: {value}")
        self.value = value

class MockAccessLevelEnum:
    View = "view"
    Edit = "edit"
    
    def __init__(self, value):
        if value not in [self.View, self.Edit]:
            raise ValueError(f"Invalid access level: {value}")
        self.value = value

# Apply the mocks before importing auth
import app.services.auth as auth_module
auth_module.RoleEnum = MockRoleEnum
auth_module.AccessLevelEnum = MockAccessLevelEnum

from app.services.auth import AuthService, _norm_email, _assert_valid_email, EMAIL_RE, JWT_SECRET, JWT_ALGORITHM

class TestAuthHelpers(unittest.TestCase):
    
    def test_norm_email(self):
        """Test email normalization"""
        self.assertEqual(_norm_email("  TEST@Example.COM  "), "test@example.com")
        self.assertEqual(_norm_email(None), "")
        self.assertEqual(_norm_email(""), "")
    
    def test_assert_valid_email(self):
        """Test email validation"""
        # Valid emails
        _assert_valid_email("test@example.com")
        _assert_valid_email("user.name@domain.co.uk")
        
        # Invalid emails should raise ValueError
        with self.assertRaises(ValueError):
            _assert_valid_email("invalid-email")
        with self.assertRaises(ValueError):
            _assert_valid_email("missing@domain")
        with self.assertRaises(ValueError):
            _assert_valid_email("@nodomain.com")

class TestAuthServicePassword(unittest.TestCase):
    
    def test_hash_password(self):
        """Test password hashing"""
        password = "test_password123"
        hashed = AuthService.hash_password(password)
        
        # Should not be the same as plain text
        self.assertNotEqual(hashed, password)
        # Should be a string
        self.assertIsInstance(hashed, str)
        # Should be verifiable
        self.assertTrue(AuthService.verify_password(hashed, password))
    
    def test_verify_password(self):
        """Test password verification"""
        password = "test_password123"
        hashed = generate_password_hash(password)
        
        # Correct password should return True
        self.assertTrue(AuthService.verify_password(hashed, password))
        # Wrong password should return False
        self.assertFalse(AuthService.verify_password(hashed, "wrong_password"))
        # Empty password should return False
        self.assertFalse(AuthService.verify_password(hashed, ""))

class TestAuthServiceJWT(unittest.TestCase):
    
    def setUp(self):
        self.user_id = 1
        self.email = "test@example.com"
        self.role = "admin"
    
    def test_generate_token(self):
        """Test JWT token generation"""
        token = AuthService.generate_token(self.user_id, self.email, self.role)
        
        # Should return a string
        self.assertIsInstance(token, str)
        
        # Should be decodable and contain correct data
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        self.assertEqual(payload["user_id"], self.user_id)
        self.assertEqual(payload["email"], self.email)
        self.assertEqual(payload["role"], self.role)
        self.assertIn("exp", payload)
    
    def test_verify_token_valid(self):
        """Test valid token verification"""
        token = AuthService.generate_token(self.user_id, self.email, self.role)
        
        payload = AuthService.verify_token(token)
        self.assertIsNotNone(payload)
        self.assertEqual(payload["user_id"], self.user_id)
        self.assertEqual(payload["email"], self.email)
    
    def test_verify_token_with_bearer_prefix(self):
        """Test token verification with Bearer prefix"""
        token = AuthService.generate_token(self.user_id, self.email, self.role)
        bearer_token = f"Bearer {token}"
        
        payload = AuthService.verify_token(bearer_token)
        self.assertIsNotNone(payload)
        self.assertEqual(payload["user_id"], self.user_id)
    
    def test_verify_token_invalid(self):
        """Test invalid token verification"""
        # Expired token
        expired_payload = {
            "user_id": self.user_id,
            "email": self.email,
            "role": self.role,
            "exp": datetime.datetime.utcnow() - datetime.timedelta(hours=1)
        }
        expired_token = jwt.encode(expired_payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
        
        self.assertIsNone(AuthService.verify_token(expired_token))
        self.assertIsNone(AuthService.verify_token("invalid_token"))
        self.assertIsNone(AuthService.verify_token(""))
        self.assertIsNone(AuthService.verify_token(None))

class TestAuthServiceUserFlows(unittest.TestCase):
    
    def setUp(self):
        self.valid_user_data = {
            "email": "test@example.com",
            "password": "secure_password123",
            "role": "user",
            "name": "Test User",
            "default_access_level": "view"
        }
    
    @patch('app.services.auth.SessionLocal')
    def test_authenticate_user_success(self, mock_session_local):
        """Test successful user authentication"""
        # Mock database response - use a real dict instead of MagicMock for row
        mock_session = MagicMock()
        mock_session_local.return_value.__enter__.return_value = mock_session
        
        mock_row = {
            'id': 1,
            'email': 'test@example.com',
            'password_hash': generate_password_hash('correct_password'),
            'role': 'user',
            'name': 'Test User'
        }
        
        mock_session.execute.return_value.mappings.return_value.first.return_value = mock_row
        
        result = AuthService.authenticate_user('test@example.com', 'correct_password')
        
        self.assertIsNotNone(result)
        self.assertEqual(result['id'], 1)
        self.assertEqual(result['email'], 'test@example.com')
    
    @patch('app.services.auth.SessionLocal')
    def test_authenticate_user_wrong_password(self, mock_session_local):
        """Test authentication with wrong password"""
        mock_session = MagicMock()
        mock_session_local.return_value.__enter__.return_value = mock_session
        
        mock_row = {
            'password_hash': generate_password_hash('correct_password')
        }
        
        mock_session.execute.return_value.mappings.return_value.first.return_value = mock_row
        
        result = AuthService.authenticate_user('test@example.com', 'wrong_password')
        self.assertIsNone(result)
    
    @patch('app.services.auth.SessionLocal')
    def test_authenticate_user_not_found(self, mock_session_local):
        """Test authentication with non-existent user"""
        mock_session = MagicMock()
        mock_session_local.return_value.__enter__.return_value = mock_session
        
        mock_session.execute.return_value.mappings.return_value.first.return_value = None
        
        result = AuthService.authenticate_user('nonexistent@example.com', 'password')
        self.assertIsNone(result)
    
    def test_authenticate_user_invalid_email(self):
        """Test authentication with invalid email"""
        result = AuthService.authenticate_user('invalid-email', 'password')
        self.assertIsNone(result)
    
    def test_authenticate_user_empty_credentials(self):
        """Test authentication with empty credentials"""
        self.assertIsNone(AuthService.authenticate_user('', 'password'))
        self.assertIsNone(AuthService.authenticate_user('test@example.com', ''))
        self.assertIsNone(AuthService.authenticate_user('', ''))

    @patch('app.services.auth.SessionLocal')
    def test_create_user_success(self, mock_session_local):
        """Test successful user creation"""
        mock_session = MagicMock()
        mock_session_local.return_value.__enter__.return_value = mock_session
        
        # Mock no existing user
        mock_session.execute.return_value.scalar.return_value = None
        
        # Mock successful insertion
        mock_new_user = {
            'id': 1,
            'email': 'test@example.com',
            'role': 'user',
            'name': 'Test User',
            'default_access_level': 'view',
            'created_at': datetime.datetime.now()
        }
        mock_session.execute.return_value.mappings.return_value.first.return_value = mock_new_user
        
        result = AuthService.create_user(self.valid_user_data)
        
        self.assertEqual(result['id'], 1)
        self.assertEqual(result['email'], 'test@example.com')
        mock_session.commit.assert_called_once()
    
    @patch('app.services.auth.SessionLocal')
    def test_create_user_duplicate_email(self, mock_session_local):
        """Test user creation with duplicate email"""
        mock_session = MagicMock()
        mock_session_local.return_value.__enter__.return_value = mock_session
        
        # Mock existing user
        mock_session.execute.return_value.scalar.return_value = 1
        
        with self.assertRaises(ValueError) as context:
            AuthService.create_user(self.valid_user_data)
        
        self.assertEqual(str(context.exception), "email_exists")
    
    @patch('app.services.auth.SessionLocal')
    def test_create_user_invalid_role(self, mock_session_local):
        """Test user creation with invalid role"""
        mock_session = MagicMock()
        mock_session_local.return_value.__enter__.return_value = mock_session
        
        # Mock no existing user first to bypass email check
        mock_session.execute.return_value.scalar.return_value = None
        
        invalid_data = self.valid_user_data.copy()
        invalid_data['role'] = 'invalid_role'
        
        with self.assertRaises(ValueError) as context:
            AuthService.create_user(invalid_data)
        
        self.assertEqual(str(context.exception), "invalid_role")
    
    @patch('app.services.auth.SessionLocal')
    def test_create_user_invalid_access_level(self, mock_session_local):
        """Test user creation with invalid access level"""
        mock_session = MagicMock()
        mock_session_local.return_value.__enter__.return_value = mock_session
        
        # Mock no existing user first to bypass email check
        mock_session.execute.return_value.scalar.return_value = None
        
        invalid_data = self.valid_user_data.copy()
        invalid_data['default_access_level'] = 'invalid_level'
        
        with self.assertRaises(ValueError) as context:
            AuthService.create_user(invalid_data)
        
        self.assertEqual(str(context.exception), "invalid_access_level")
    
    @patch('app.services.auth.SessionLocal')
    def test_create_user_no_password(self, mock_session_local):
        """Test user creation without password"""
        mock_session = MagicMock()
        mock_session_local.return_value.__enter__.return_value = mock_session
        
        # Mock no existing user first to bypass email check
        mock_session.execute.return_value.scalar.return_value = None
        
        invalid_data = self.valid_user_data.copy()
        invalid_data['password'] = ""
        
        with self.assertRaises(ValueError) as context:
            AuthService.create_user(invalid_data)
        
        self.assertEqual(str(context.exception), "invalid_password")

    @patch('app.services.auth.SessionLocal')
    def test_get_user_by_id_found(self, mock_session_local):
        """Test getting user by ID when user exists"""
        mock_session = MagicMock()
        mock_session_local.return_value.__enter__.return_value = mock_session
        
        mock_user = {
            'id': 1,
            'email': 'test@example.com',
            'role': 'user',
            'name': 'Test User'
        }
        mock_session.execute.return_value.mappings.return_value.first.return_value = mock_user
        
        result = AuthService.get_user_by_id(1)
        self.assertEqual(result, mock_user)
    
    @patch('app.services.auth.SessionLocal')
    def test_get_user_by_id_not_found(self, mock_session_local):
        """Test getting user by ID when user doesn't exist"""
        mock_session = MagicMock()
        mock_session_local.return_value.__enter__.return_value = mock_session
        
        mock_session.execute.return_value.mappings.return_value.first.return_value = None
        
        result = AuthService.get_user_by_id(999)
        self.assertIsNone(result)

    @patch('app.services.auth.SessionLocal')
    def test_update_user_success(self, mock_session_local):
        """Test successful user update"""
        mock_session = MagicMock()
        mock_session_local.return_value.__enter__.return_value = mock_session
        
        # Mock user exists
        mock_session.execute.return_value.scalar.return_value = True
        
        # Mock successful update
        updated_user = {
            'id': 1,
            'email': 'updated@example.com',
            'name': 'Updated Name',
            'role': 'admin',
            'default_access_level': 'edit'
        }
        mock_session.execute.return_value.mappings.return_value.first.return_value = updated_user
        
        update_data = {
            'email': 'updated@example.com',
            'name': 'Updated Name',
            'role': 'admin',
            'default_access_level': 'edit'
        }
        
        result = AuthService.update_user(1, update_data)
        self.assertEqual(result, updated_user)
        mock_session.commit.assert_called_once()
    
    @patch('app.services.auth.SessionLocal')
    def test_update_user_not_found(self, mock_session_local):
        """Test updating non-existent user"""
        mock_session = MagicMock()
        mock_session_local.return_value.__enter__.return_value = mock_session
        
        # Mock user doesn't exist
        mock_session.execute.return_value.scalar.return_value = False
        
        result = AuthService.update_user(999, {'name': 'New Name'})
        self.assertIsNone(result)
    
    def test_update_user_no_fields(self):
        """Test update with no fields to update"""
        with self.assertRaises(ValueError) as context:
            AuthService.update_user(1, {})
        
        self.assertEqual(str(context.exception), "no_fields_to_update")
    
    @patch('app.services.auth.SessionLocal')
    def test_is_admin_user_not_found(self, mock_session_local):
        """Test is_admin returns False for non-existent user"""
        mock_session = MagicMock()
        mock_session_local.return_value.__enter__.return_value = mock_session
        
        mock_session.execute.return_value.scalar.return_value = None
        
        result = AuthService.is_admin(999)
        self.assertFalse(result)

if __name__ == '__main__':
    unittest.main()