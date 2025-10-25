# tests/test_building_metrics_routes.py
import unittest
from unittest.mock import Mock, MagicMock, patch
import jwt
from flask import Flask, g
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestBuildingMetricsRoutes(unittest.TestCase):
    
    def setUp(self):
        self.app = Flask(__name__)
        self.app.config['TESTING'] = True
        self.app.config['JWT_SECRET'] = 'test-secret-key'
        self.client = self.app.test_client()
        
        # Import and register blueprint
        from app.routes.building_metrics import metrics_bp
        self.app.register_blueprint(metrics_bp)
        
    def _create_token(self, role="Client"):
        """Create a JWT token"""
        return jwt.encode(
            {"sub": "1", "role": role, "email": "user@example.com"},
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
        mock_conn.exec_driver_sql = MagicMock()  # Add missing method
        
        return mock_conn, mock_result
    
    @patch('app.routes.building_metrics.get_conn')
    @patch('app.routes.building_metrics.rules_metric')
    @patch('app.routes.building_metrics.apply_weights')
    def test_send_metrics_success(self, mock_apply_weights, mock_rules_metric, mock_get_conn):
        """Test successful metrics submission"""
        mock_conn, mock_result = self._create_mock_connection()
        mock_get_conn.return_value.__enter__.return_value = mock_conn
        
        mock_rules_metric.save_project_metrics.return_value = 5
        mock_rules_metric.metric_recompute.return_value = {1: 0.8, 2: 0.9}
        mock_apply_weights.return_value = 10
        
        token = self._create_token()
        
        response = self.client.post(
            '/projects/123/metrics',
            json={
                'levels': 5,
                'external_wall_area': 1500.5
            },
            headers={'Authorization': f'Bearer {token}'}
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['project_id'], 123)
        self.assertEqual(data['updated'], 2)
        self.assertFalse(data['dry_run'])
        
        # Verify service calls
        mock_rules_metric.save_project_metrics.assert_called_once()
        mock_rules_metric.metric_recompute.assert_called_once()
        mock_rules_metric.upsert_runtime_scores.assert_called_once()
        mock_apply_weights.assert_called_once()
    
    @patch('app.routes.building_metrics.get_conn')
    @patch('app.routes.building_metrics.rules_metric')
    @patch('app.routes.building_metrics.apply_weights')
    def test_send_metrics_dry_run(self, mock_apply_weights, mock_rules_metric, mock_get_conn):
        """Test metrics submission with dry run"""
        mock_conn, mock_result = self._create_mock_connection()
        mock_get_conn.return_value.__enter__.return_value = mock_conn
        
        mock_rules_metric.save_project_metrics.return_value = 5
        mock_rules_metric.metric_recompute.return_value = {1: 0.8, 2: 0.9}
        mock_apply_weights.return_value = 10
        
        token = self._create_token()
        
        response = self.client.post(
            '/projects/123/metrics?dry_run=true',
            json={
                'levels': 5,
                'external_wall_area': 1500.5
            },
            headers={'Authorization': f'Bearer {token}'}
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data['dry_run'])
    
    @patch('app.routes.building_metrics.get_conn')
    def test_send_metrics_unauthorized(self, mock_get_conn):
        """Test metrics submission without authentication"""
        response = self.client.post(
            '/projects/123/metrics',
            json={'levels': 5}
        )
        
        self.assertEqual(response.status_code, 401)
    
    @patch('app.routes.building_metrics.get_conn')
    def test_send_metrics_invalid_data(self, mock_get_conn):
        """Test metrics submission with invalid data"""
        token = self._create_token()
        
        # Empty metrics
        response = self.client.post(
            '/projects/123/metrics',
            json={},
            headers={'Authorization': f'Bearer {token}'}
        )
        
        self.assertEqual(response.status_code, 400)
        
        # Non-numeric metrics
        response = self.client.post(
            '/projects/123/metrics',
            json={'levels': 'invalid'},
            headers={'Authorization': f'Bearer {token}'}
        )
        
        self.assertEqual(response.status_code, 400)
    
    @patch('app.routes.building_metrics.get_conn')
    @patch('app.routes.building_metrics.stages')
    def test_get_recommendations(self, mock_stages, mock_get_conn):
        """Test getting recommendations"""
        mock_conn, mock_result = self._create_mock_connection()
        mock_get_conn.return_value.__enter__.return_value = mock_conn
        
        # Mock recommendations
        mock_recommendations = [
            {'id': 1, 'name': 'Intervention 1', 'score': 0.9},
            {'id': 2, 'name': 'Intervention 2', 'score': 0.8}
        ]
        mock_stages.recommendations.return_value = mock_recommendations
        
        token = self._create_token()
        
        response = self.client.get(
            '/projects/123/recommendations',
            headers={'Authorization': f'Bearer {token}'}
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('recommendations', data)
        self.assertEqual(len(data['recommendations']), 2)
    
    @patch('app.routes.building_metrics.get_conn')
    def test_list_user_projects(self, mock_get_conn):
        """Test listing user projects"""
        mock_conn, mock_result = self._create_mock_connection()
        mock_get_conn.return_value.__enter__.return_value = mock_conn
        
        # Mock projects data
        mock_projects = [{'id': 1, 'name': 'Project 1'}, {'id': 2, 'name': 'Project 2'}]
        mock_result.scalar_one.return_value = mock_projects
        
        token = self._create_token()
        
        response = self.client.get(
            '/users/1/projects',
            headers={'Authorization': f'Bearer {token}'}
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('projects', data)

if __name__ == '__main__':
    unittest.main()