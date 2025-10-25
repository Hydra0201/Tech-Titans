# tests/test_metrics.py
import unittest
from unittest.mock import Mock, MagicMock, patch
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import from the correct module name
from app.services.rules_metric import (
    fetch_metric_rules, 
    save_project_metrics, 
    metric_recompute, 
    upsert_runtime_scores
)
from app.services.types import MetricRule, in_bounds


class TestMetricsFunctions(unittest.TestCase):

    def setUp(self):
        self.mock_conn = MagicMock()
        self.mock_result = MagicMock()
        self.mock_conn.execute.return_value = self.mock_result

    def test_fetch_metric_rules(self):
        """Test fetching metric rules from database"""
        # Mock database response
        mock_rows = [
            {
                'id': 1,
                'metric_name': 'levels',
                'intervention_id': 101,
                'lower': 5.0,
                'upper': 10.0,
                'multiplier': 1.5,
                'reasoning': 'High levels boost effectiveness'
            },
            {
                'id': 2,
                'metric_name': 'external_wall_area',
                'intervention_id': 102,
                'lower': None,
                'upper': 1000.0,
                'multiplier': 0.8,
                'reasoning': 'Small wall area reduces effectiveness'
            }
        ]
        
        self.mock_result.mappings.return_value.all.return_value = mock_rows
        
        # Call function
        result = fetch_metric_rules(self.mock_conn)
        
        # Verify database call
        self.mock_conn.execute.assert_called_once()
        
        # Verify results
        self.assertEqual(len(result), 2)
        
        rule1 = result[0]
        self.assertIsInstance(rule1, MetricRule)
        self.assertEqual(rule1.id, 1)
        self.assertEqual(rule1.metric_name, 'levels')
        self.assertEqual(rule1.intervention_id, 101)
        self.assertEqual(rule1.lower, 5.0)
        self.assertEqual(rule1.upper, 10.0)
        self.assertEqual(rule1.multiplier, 1.5)
        self.assertEqual(rule1.reason, 'High levels boost effectiveness')
        
        rule2 = result[1]
        self.assertEqual(rule2.id, 2)
        self.assertEqual(rule2.lower, None)
        self.assertEqual(rule2.upper, 1000.0)

    def test_fetch_metric_rules_empty(self):
        """Test fetching metric rules when no rules exist"""
        self.mock_result.mappings.return_value.all.return_value = []
        
        result = fetch_metric_rules(self.mock_conn)
        self.assertEqual(result, [])

    def test_save_project_metrics_success(self):
        """Test successful saving of project metrics"""
        metrics = {
            'levels': 5,
            'external_wall_area': 1500.5,
            'footprint_area': 200.0,
            'invalid_metric': 999,  # Should be filtered out
            'gifa_total': None,  # Should be filtered out
        }
        
        self.mock_result.rowcount = 3
        
        result = save_project_metrics(self.mock_conn, 123, metrics)
        
        # Should call execute multiple times (insert + update)
        self.assertEqual(self.mock_conn.execute.call_count, 2)
        
        # First call should be the INSERT with ON CONFLICT
        first_call_args = self.mock_conn.execute.call_args_list[0]
        self.assertIn('INSERT INTO projects', str(first_call_args[0][0]))
        
        # Second call should be the UPDATE
        second_call_args = self.mock_conn.execute.call_args_list[1]
        self.assertIn('UPDATE projects', str(second_call_args[0][0]))
        
        # Should return rowcount
        self.assertEqual(result, 3)

    def test_save_project_metrics_no_valid_metrics(self):
        """Test saving metrics with no valid metrics"""
        metrics = {
            'invalid_metric': 999,
            'another_invalid': 123,
            'gifa_total': None,
        }
        
        result = save_project_metrics(self.mock_conn, 123, metrics)
        
        # Should not execute any queries
        self.mock_conn.execute.assert_not_called()
        self.assertEqual(result, 0)

    def test_save_project_metrics_empty_dict(self):
        """Test saving empty metrics dictionary"""
        result = save_project_metrics(self.mock_conn, 123, {})
        self.assertEqual(result, 0)
        
        result = save_project_metrics(self.mock_conn, 123, None)
        self.assertEqual(result, 0)

    def test_save_project_metrics_type_conversion(self):
        """Test type conversion for metric values"""
        metrics = {
            'levels': '5',  # String that can be converted to float
            'external_wall_area': 1500.5,
            'opening_pct': 'invalid',  # Should be filtered out
        }
        
        self.mock_result.rowcount = 2
        
        result = save_project_metrics(self.mock_conn, 456, metrics)
        
        # Should process valid conversions
        self.assertEqual(result, 2)
        self.mock_conn.execute.assert_called()

    def test_metric_recompute_no_base_effectiveness(self):
        """Test recompute when no base effectiveness data exists"""
        self.mock_result.mappings.return_value.all.return_value = []
        
        result = metric_recompute(self.mock_conn, 123)
        self.assertEqual(result, {})

    @patch('app.services.rules_metric.fetch_metric_rules')
    def test_metric_recompute_no_rules(self, mock_fetch_rules):
        """Test recompute when no metric rules exist"""
        # Mock base effectiveness
        base_rows = [
            {'id': 101, 'base_effectiveness': 0.5},
            {'id': 102, 'base_effectiveness': 0.8},
        ]
        self.mock_result.mappings.return_value.all.return_value = base_rows
        mock_fetch_rules.return_value = []
        
        result = metric_recompute(self.mock_conn, 123)
        
        # Should return base effectiveness unchanged
        expected = {101: 0.5, 102: 0.8}
        self.assertEqual(result, expected)

    @patch('app.services.rules_metric.fetch_metric_rules')
    def test_metric_recompute_with_rules_no_project_metrics(self, mock_fetch_rules):
        """Test recompute with rules but no project metrics"""
        # Mock base effectiveness
        base_rows = [
            {'id': 101, 'base_effectiveness': 0.5},
            {'id': 102, 'base_effectiveness': 0.8},
        ]
        self.mock_result.mappings.return_value.all.return_value = base_rows
        
        # Mock rules
        rules = [
            MetricRule(
                id=1,
                metric_name='levels',
                intervention_id=101,
                lower=5.0,
                upper=10.0,
                multiplier=1.5,
                reason='Test rule'
            )
        ]
        mock_fetch_rules.return_value = rules
        
        # Mock project query returns no row
        self.mock_result.mappings.return_value.one_or_none.return_value = None
        
        result = metric_recompute(self.mock_conn, 123)
        
        # Should return base effectiveness unchanged (no metrics to apply rules)
        expected = {101: 0.5, 102: 0.8}
        self.assertEqual(result, expected)

    @patch('app.services.rules_metric.fetch_metric_rules')
    def test_metric_recompute_with_rules_and_metrics(self, mock_fetch_rules):
        """Test recompute with rules and project metrics"""
        # Mock base effectiveness
        base_rows = [
            {'id': 101, 'base_effectiveness': 0.5},
            {'id': 102, 'base_effectiveness': 0.8},
            {'id': 103, 'base_effectiveness': 1.0},
        ]
        self.mock_result.mappings.return_value.all.return_value = base_rows
        
        # Mock rules
        rules = [
            MetricRule(
                id=1,
                metric_name='levels',
                intervention_id=101,
                lower=5.0,
                upper=10.0,
                multiplier=1.5,  # Will apply (levels=7 is in bounds)
                reason='Levels rule'
            ),
            MetricRule(
                id=2,
                metric_name='external_wall_area',
                intervention_id=101,
                lower=None,
                upper=1000.0,
                multiplier=0.8,  # Will NOT apply (wall_area=1200 is out of bounds)
                reason='Wall area rule'
            ),
            MetricRule(
                id=3,
                metric_name='footprint_area',
                intervention_id=102,
                lower=200.0,
                upper=None,
                multiplier=2.0,  # Will apply (footprint=250 is in bounds)
                reason='Footprint rule'
            ),
        ]
        mock_fetch_rules.return_value = rules
        
        # Mock project metrics
        project_metrics = {
            'levels': 7.0,
            'external_wall_area': 1200.0,
            'footprint_area': 250.0,
        }
        self.mock_result.mappings.return_value.one_or_none.return_value = project_metrics
        
        result = metric_recompute(self.mock_conn, 123)
        
        # Verify calculations:
        # Intervention 101: 0.5 * 1.5 (levels rule) = 0.75
        # Intervention 102: 0.8 * 2.0 (footprint rule) = 1.6
        # Intervention 103: 1.0 * 1.0 (no rules) = 1.0
        expected = {101: 0.75, 102: 1.6, 103: 1.0}
        self.assertEqual(result, expected)

    @patch('app.services.rules_metric.fetch_metric_rules')
    def test_metric_recompute_multiple_rules_same_intervention(self, mock_fetch_rules):
        """Test recompute with multiple rules for same intervention"""
        base_rows = [{'id': 101, 'base_effectiveness': 1.0}]
        self.mock_result.mappings.return_value.all.return_value = base_rows
        
        rules = [
            MetricRule(
                id=1,
                metric_name='levels',
                intervention_id=101,
                lower=5.0,
                upper=None,
                multiplier=1.5,
                reason='First rule'
            ),
            MetricRule(
                id=2,
                metric_name='external_wall_area',
                intervention_id=101,
                lower=None,
                upper=1000.0,
                multiplier=2.0,
                reason='Second rule'
            ),
        ]
        mock_fetch_rules.return_value = rules
        
        project_metrics = {
            'levels': 7.0,  # In bounds for first rule
            'external_wall_area': 800.0,  # In bounds for second rule
        }
        self.mock_result.mappings.return_value.one_or_none.return_value = project_metrics
        
        result = metric_recompute(self.mock_conn, 123)
        
        # Should multiply both multipliers: 1.0 * 1.5 * 2.0 = 3.0
        expected = {101: 3.0}
        self.assertEqual(result, expected)

    def test_upsert_runtime_scores(self):
        """Test upserting runtime scores"""
        scores = {
            101: 0.75,
            102: 1.6,
            103: 1.0,
        }
        
        upsert_runtime_scores(self.mock_conn, 123, scores)
        
        # Should call execute once with the correct payload
        self.mock_conn.execute.assert_called_once()
        
        call_args = self.mock_conn.execute.call_args
        sql_text = str(call_args[0][0])
        params = call_args[0][1]
        
        self.assertIn('INSERT INTO runtime_scores', sql_text)
        self.assertIn('ON CONFLICT', sql_text)
        self.assertIn('DO UPDATE', sql_text)
        
        # Verify payload structure
        self.assertEqual(len(params), 3)
        self.assertEqual(params[0]['project_id'], 123)
        self.assertEqual(params[0]['intervention_id'], 101)
        self.assertEqual(params[0]['score'], 0.75)

    def test_upsert_runtime_scores_empty(self):
        """Test upserting empty scores"""
        upsert_runtime_scores(self.mock_conn, 123, {})
        
        # Should not execute any query
        self.mock_conn.execute.assert_not_called()

    def test_upsert_runtime_scores_none(self):
        """Test upserting None scores"""
        upsert_runtime_scores(self.mock_conn, 123, None)
        
        # Should not execute any query
        self.mock_conn.execute.assert_not_called()


class TestInBoundsFunction(unittest.TestCase):
    """Test the in_bounds helper function"""
    
    def test_in_bounds_both_bounds(self):
        """Test with both lower and upper bounds"""
        # Within bounds
        self.assertTrue(in_bounds(5.0, 1.0, 10.0))
        self.assertTrue(in_bounds(1.0, 1.0, 10.0))  # Equal to lower
        self.assertTrue(in_bounds(10.0, 1.0, 10.0))  # Equal to upper
        
        # Outside bounds
        self.assertFalse(in_bounds(0.5, 1.0, 10.0))
        self.assertFalse(in_bounds(10.5, 1.0, 10.0))

    def test_in_bounds_lower_only(self):
        """Test with only lower bound"""
        self.assertTrue(in_bounds(5.0, 1.0, None))
        self.assertTrue(in_bounds(1.0, 1.0, None))  # Equal to lower
        self.assertFalse(in_bounds(0.5, 1.0, None))

    def test_in_bounds_upper_only(self):
        """Test with only upper bound"""
        self.assertTrue(in_bounds(5.0, None, 10.0))
        self.assertTrue(in_bounds(10.0, None, 10.0))  # Equal to upper
        self.assertFalse(in_bounds(10.5, None, 10.0))

    def test_in_bounds_no_bounds(self):
        """Test with no bounds (always True)"""
        self.assertTrue(in_bounds(5.0, None, None))
        self.assertTrue(in_bounds(-100.0, None, None))
        self.assertTrue(in_bounds(1000.0, None, None))

    def test_in_bounds_none_value(self):
        """Test with None value"""
        self.assertFalse(in_bounds(None, 1.0, 10.0))
        self.assertFalse(in_bounds(None, None, 10.0))
        self.assertFalse(in_bounds(None, 1.0, None))
        self.assertFalse(in_bounds(None, None, None))

    def test_in_bounds_edge_cases(self):
        """Test edge cases"""
        # Zero bounds
        self.assertTrue(in_bounds(0.0, 0.0, 0.0))
        self.assertTrue(in_bounds(0.0, -1.0, 1.0))
        
        # Negative bounds
        self.assertTrue(in_bounds(-5.0, -10.0, 0.0))
        self.assertFalse(in_bounds(-15.0, -10.0, 0.0))



if __name__ == '__main__':
    unittest.main()