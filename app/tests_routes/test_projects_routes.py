# tests/test_projects_routes.py
import unittest
from unittest.mock import Mock, MagicMock, patch
import jwt
from flask import Flask
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestProjectsRoutes(unittest.TestCase):
    
    def setUp(self):
        self.app = Flask(__name__)
        self.app.config['TESTING'] = True
        self.app.config['JWT_SECRET'] = 'test-secret-key'
        self.client = self.app.test_client()
        
        # Import and register blueprint
        from app.routes.projects import projects_bp
        self.app.register_blueprint(projects_bp)
        
        # Mock dependencies with proper transaction setup
        self.mock_conn = MagicMock()
        self.mock_result = MagicMock()
        self.mock_conn.execute.return_value = self.mock_result
        
        # Setup proper transaction mocking
        self.mock_tx = MagicMock()
        self.mock_tx.is_active = True
        self.mock_tx.rollback = MagicMock()
        self.mock_tx.commit = MagicMock()
        
        self.mock_conn.begin.return_value = self.mock_tx
        self.mock_conn.begin_nested.return_value = self.mock_tx
        self.mock_conn.in_transaction = False
        self.mock_conn.exec_driver_sql = MagicMock()  # Add missing method
        
    def _create_token(self, user_id="1"):
        """Create a JWT token"""
        return jwt.encode(
            {"sub": user_id, "role": "Client", "email": "user@example.com"},
            self.app.config['JWT_SECRET'],
            algorithm="HS256"
        )
    
    @patch('app.routes.projects.get_conn')
    def test_create_project_missing_name(self, mock_get_conn):
        """Test project creation without name"""
        mock_get_conn.return_value.__enter__.return_value = self.mock_conn
        
        token = self._create_token()
        
        response = self.client.post(
            '/projects',
            json={},  # No name
            headers={'Authorization': f'Bearer {token}'}
        )
        
        self.assertEqual(response.status_code, 400)
    
    @patch('app.routes.projects.get_conn')
    def test_get_project(self, mock_get_conn):
        """Test getting a project"""
        mock_get_conn.return_value.__enter__.return_value = self.mock_conn
        
        # Mock project response
        mock_project = {
            'id': 1,
            'name': 'Test Project',
            'status': 'draft',
            'created_at': '2023-01-01T00:00:00',
            'updated_at': '2023-01-01T00:00:00'
        }
        self.mock_result.mappings.return_value.one_or_none.return_value = mock_project
        
        token = self._create_token()
        
        response = self.client.get(
            '/projects/1',
            headers={'Authorization': f'Bearer {token}'}
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('project', data)
        self.assertEqual(data['project']['name'], 'Test Project')
    
    @patch('app.routes.projects.get_conn')
    def test_get_project_not_found(self, mock_get_conn):
        """Test getting non-existent project"""
        mock_get_conn.return_value.__enter__.return_value = self.mock_conn
        
        # Mock no project found
        self.mock_result.mappings.return_value.one_or_none.return_value = None
        
        token = self._create_token()
        
        response = self.client.get(
            '/projects/999',
            headers={'Authorization': f'Bearer {token}'}
        )
        
        self.assertEqual(response.status_code, 404)
    
    @patch('app.routes.projects.get_conn')
    def test_patch_project(self, mock_get_conn):
        """Test updating a project"""
        mock_get_conn.return_value.__enter__.return_value = self.mock_conn
        
        # Mock project update response
        mock_updated_project = {
            'id': 1,
            'name': 'Updated Project',
            'status': 'active',
            'created_at': '2023-01-01T00:00:00',
            'updated_at': '2023-01-02T00:00:00'
        }
        self.mock_result.mappings.return_value.one_or_none.return_value = mock_updated_project
        
        token = self._create_token()
        
        response = self.client.patch(
            '/projects/1',
            json={'name': 'Updated Project', 'status': 'active'},
            headers={'Authorization': f'Bearer {token}'}
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['project']['name'], 'Updated Project')
    
    @patch('app.routes.projects.get_conn')
    def test_delete_project(self, mock_get_conn):
        """Test deleting a project"""
        mock_get_conn.return_value.__enter__.return_value = self.mock_conn
        
        # Mock project deletion response
        mock_deleted_project = {'id': 1}
        self.mock_result.mappings.return_value.one_or_none.return_value = mock_deleted_project
        
        token = self._create_token()
        
        response = self.client.delete(
            '/projects/1',
            headers={'Authorization': f'Bearer {token}'}
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data['deleted'])
        self.assertEqual(data['id'], 1)

if __name__ == '__main__':
    unittest.main()