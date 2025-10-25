# tests/test_theme_weights_routes.py
import unittest
from unittest.mock import Mock, MagicMock, patch
import jwt
from flask import Flask
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestThemeWeightsRoutes(unittest.TestCase):
    
    def setUp(self):
        self.app = Flask(__name__)
        self.app.config['TESTING'] = True
        self.app.config['JWT_SECRET'] = 'test-secret-key'
        self.client = self.app.test_client()
        
        # Import and register blueprint
        from app.routes.theme_weights import theme_weights_bp
        self.app.register_blueprint(theme_weights_bp)
        
        # Mock dependencies
        self.mock_conn = MagicMock()
        self.mock_result = MagicMock()
        self.mock_conn.execute.return_value = self.mock_result
        self.mock_conn.begin.return_value = MagicMock()
        
    def _create_token(self):
        """Create a JWT token"""
        return jwt.encode(
            {"sub": "1", "role": "Client", "email": "user@example.com"},
            self.app.config['JWT_SECRET'],
            algorithm="HS256"
        )
    
    @patch('app.routes.theme_weights.get_conn')
    def test_list_themes(self, mock_get_conn):
        """Test listing all themes"""
        mock_get_conn.return_value.__enter__.return_value = self.mock_conn
        
        # Mock themes response
        mock_themes = [
            {'id': 1, 'name': 'Theme 1', 'description': 'Description 1'},
            {'id': 2, 'name': 'Theme 2', 'description': 'Description 2'}
        ]
        self.mock_result.mappings.return_value.all.return_value = mock_themes
        
        token = self._create_token()
        
        response = self.client.get(
            '/api/themes',
            headers={'Authorization': f'Bearer {token}'}
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('themes', data)
        self.assertEqual(len(data['themes']), 2)
    
    @patch('app.routes.theme_weights.get_conn')
    def test_get_project_theme_scores(self, mock_get_conn):
        """Test getting theme scores for a project"""
        mock_get_conn.return_value.__enter__.return_value = self.mock_conn
        
        # Mock project exists
        self.mock_result.scalar_one_or_none.return_value = True
        
        # Mock theme scores
        mock_scores = [
            {'id': 1, 'name': 'Theme 1', 'weight_raw': 0.5, 'weight_norm': 0.5},
            {'id': 2, 'name': 'Theme 2', 'weight_raw': 0.5, 'weight_norm': 0.5}
        ]
        self.mock_result.mappings.return_value.all.return_value = mock_scores
        
        token = self._create_token()
        
        response = self.client.get(
            '/api/projects/123/theme-scores',
            headers={'Authorization': f'Bearer {token}'}
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['project_id'], 123)
        self.assertIn('themes', data)
        self.assertIn('weights', data)
    
    @patch('app.routes.theme_weights.get_conn')
    @patch('app.routes.theme_weights.apply_weights')
    def test_upsert_theme_weights(self, mock_apply_weights, mock_get_conn):
        """Test upserting theme weights"""
        mock_get_conn.return_value.__enter__.return_value = self.mock_conn
        mock_apply_weights.return_value = 5
        
        # Mock project exists
        self.mock_result.scalar_one_or_none.return_value = True
        
        token = self._create_token()
        
        response = self.client.put(
            '/api/projects/123/theme-scores',
            json={
                'weights': {
                    '1': 0.6,
                    '2': 0.4
                }
            },
            headers={'Authorization': f'Bearer {token}'}
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['project_id'], 123)
        self.assertEqual(data['sum_raw'], 1.0)
        self.assertEqual(data['sum_norm'], 1.0)
        self.assertEqual(data['updated'], 2)
        self.assertFalse(data['dry_run'])
        
        # Verify apply_weights was called
        mock_apply_weights.assert_called_once()
    
    @patch('app.routes.theme_weights.get_conn')
    def test_upsert_theme_weights_dry_run(self, mock_get_conn):
        """Test upserting theme weights with dry run"""
        mock_get_conn.return_value.__enter__.return_value = self.mock_conn
        
        # Mock project exists
        self.mock_result.scalar_one_or_none.return_value = True
        
        token = self._create_token()
        
        response = self.client.put(
            '/api/projects/123/theme-scores?dry_run=true',
            json={
                'weights': {
                    '1': 0.6,
                    '2': 0.4
                }
            },
            headers={'Authorization': f'Bearer {token}'}
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data['dry_run'])
    
    @patch('app.routes.theme_weights.get_conn')
    def test_upsert_theme_weights_invalid_data(self, mock_get_conn):
        """Test upserting theme weights with invalid data"""
        token = self._create_token()
        
        # No weights provided
        response = self.client.put(
            '/api/projects/123/theme-scores',
            json={},
            headers={'Authorization': f'Bearer {token}'}
        )
        
        self.assertEqual(response.status_code, 400)
        
        # Negative weights
        response = self.client.put(
            '/api/projects/123/theme-scores',
            json={
                'weights': {
                    '1': -0.5,
                    '2': 1.5
                }
            },
            headers={'Authorization': f'Bearer {token}'}
        )
        
        self.assertEqual(response.status_code, 400)

if __name__ == '__main__':
    unittest.main()