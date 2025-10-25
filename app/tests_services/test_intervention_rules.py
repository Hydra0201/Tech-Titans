# tests/test_intervention_rules.py
import unittest
from unittest.mock import Mock, MagicMock, patch
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.rules_intervention import (
    fetch_intervention_rules, 
    intervention_recompute
)
from app.services.types import InterventionRule


class TestInterventionRulesFunctions(unittest.TestCase):

    def setUp(self):
        self.mock_conn = MagicMock()
        self.mock_result = MagicMock()
        self.mock_conn.execute.return_value = self.mock_result

    def assertDictAlmostEqual(self, dict1, dict2, places=7):
        """Helper method to compare dictionaries with floating point values"""
        self.assertEqual(dict1.keys(), dict2.keys())
        for key in dict1:
            self.assertAlmostEqual(dict1[key], dict2[key], places=places)

    def test_fetch_intervention_rules(self):
        """Test fetching intervention rules from database"""
        # Mock database response
        mock_rows = [
            {
                'id': 1,
                'cause_intervention': 101,
                'effected_intervention': 201,
                'metric_type': 'dependency',
                'lower': 0.5,
                'upper': 1.0,
                'multiplier': 1.2,
                'reasoning': 'Positive dependency effect'
            },
            {
                'id': 2,
                'cause_intervention': 102,
                'effected_intervention': 202,
                'metric_type': 'conflict',
                'lower': None,
                'upper': 0.8,
                'multiplier': 0.7,
                'reasoning': 'Negative conflict effect'
            }
        ]
        
        self.mock_result.mappings.return_value.all.return_value = mock_rows
        
        # Call function
        result = fetch_intervention_rules(self.mock_conn)
        
        # Verify database call
        self.mock_conn.execute.assert_called_once()
        
        # Verify results
        self.assertEqual(len(result), 2)
        
        rule1 = result[0]
        self.assertIsInstance(rule1, InterventionRule)
        self.assertEqual(rule1.id, 1)
        self.assertEqual(rule1.cause_intervention_id, 101)
        self.assertEqual(rule1.effect_intervention_id, 201)
        self.assertEqual(rule1.metric_type, 'dependency')
        self.assertEqual(rule1.lower, 0.5)
        self.assertEqual(rule1.upper, 1.0)
        self.assertEqual(rule1.multiplier, 1.2)
        self.assertEqual(rule1.reason, 'Positive dependency effect')
        
        rule2 = result[1]
        self.assertEqual(rule2.id, 2)
        self.assertEqual(rule2.cause_intervention_id, 102)
        self.assertEqual(rule2.lower, None)
        self.assertEqual(rule2.upper, 0.8)

    def test_fetch_intervention_rules_empty(self):
        """Test fetching intervention rules when no rules exist"""
        self.mock_result.mappings.return_value.all.return_value = []
        
        result = fetch_intervention_rules(self.mock_conn)
        self.assertEqual(result, [])

    def test_intervention_recompute_no_rules(self):
        """Test recompute when no rules exist for the cause intervention"""
        # Mock no rules found
        self.mock_result.mappings.return_value.all.return_value = []
        
        result = intervention_recompute(self.mock_conn, 123, 101)
        
        # Should return empty dict
        self.assertEqual(result, {})
        
        # Should only call execute once (for rules query)
        self.mock_conn.execute.assert_called_once()

    def test_intervention_recompute_single_rule(self):
        """Test recompute with a single intervention rule"""
        # Mock rules response
        mock_rules = [
            {
                'id': 1,
                'effect_id': 201,
                'multiplier': 1.5
            }
        ]
        
        # Mock current scores response
        mock_scores = [
            {
                'intervention_id': 201,
                'current_score': 0.8
            }
        ]
        
        # Set up mock to return different values for different calls
        self.mock_result.mappings.return_value.all.side_effect = [mock_rules, mock_scores]
        
        result = intervention_recompute(self.mock_conn, 123, 101)
        
        # Verify calculations: 0.8 * 1.5 = 1.2 (with floating point tolerance)
        expected = {201: 1.2}
        self.assertDictAlmostEqual(result, expected)
        
        # Should call execute 3 times: rules query, scores query, upsert
        self.assertEqual(self.mock_conn.execute.call_count, 3)
        
        # Verify upsert call
        upsert_call = self.mock_conn.execute.call_args_list[2]
        self.assertIn('INSERT INTO runtime_scores', str(upsert_call[0][0]))

    def test_intervention_recompute_multiple_rules_same_effect(self):
        """Test recompute with multiple rules affecting the same intervention"""
        # Mock rules response - two rules affecting same intervention
        mock_rules = [
            {
                'id': 1,
                'effect_id': 201,
                'multiplier': 1.2
            },
            {
                'id': 2,
                'effect_id': 201,
                'multiplier': 1.5
            }
        ]
        
        # Mock current scores response
        mock_scores = [
            {
                'intervention_id': 201,
                'current_score': 1.0
            }
        ]
        
        self.mock_result.mappings.return_value.all.side_effect = [mock_rules, mock_scores]
        
        result = intervention_recompute(self.mock_conn, 123, 101)
        
        # Verify calculations: 1.0 * 1.2 * 1.5 = 1.8 (with floating point tolerance)
        expected = {201: 1.8}
        self.assertDictAlmostEqual(result, expected)

    def test_intervention_recompute_multiple_rules_different_effects(self):
        """Test recompute with multiple rules affecting different interventions"""
        # Mock rules response
        mock_rules = [
            {
                'id': 1,
                'effect_id': 201,
                'multiplier': 1.2
            },
            {
                'id': 2,
                'effect_id': 202,
                'multiplier': 0.8
            },
            {
                'id': 3,
                'effect_id': 203,
                'multiplier': 1.5
            }
        ]
        
        # Mock current scores response
        mock_scores = [
            {
                'intervention_id': 201,
                'current_score': 1.0
            },
            {
                'intervention_id': 202,
                'current_score': 0.5
            },
            {
                'intervention_id': 203,
                'current_score': 0.8
            }
        ]
        
        self.mock_result.mappings.return_value.all.side_effect = [mock_rules, mock_scores]
        
        result = intervention_recompute(self.mock_conn, 123, 101)
        
        # Verify calculations (with floating point tolerance)
        expected = {
            201: 1.0 * 1.2,  # 1.2
            202: 0.5 * 0.8,  # 0.4
            203: 0.8 * 1.5   # 1.2
        }
        self.assertDictAlmostEqual(result, expected)

    def test_intervention_recompute_fallback_to_base_effectiveness(self):
        """Test recompute falls back to base_effectiveness when runtime score is missing"""
        # Mock rules response
        mock_rules = [
            {
                'id': 1,
                'effect_id': 201,
                'multiplier': 1.5
            }
        ]
        
        # Mock current scores response with base_effectiveness fallback
        mock_scores = [
            {
                'intervention_id': 201,
                'current_score': 0.6  # This comes from base_effectiveness since no runtime score
            }
        ]
        
        self.mock_result.mappings.return_value.all.side_effect = [mock_rules, mock_scores]
        
        result = intervention_recompute(self.mock_conn, 123, 101)
        
        # Verify calculations: 0.6 * 1.5 = 0.9 (with floating point tolerance)
        expected = {201: 0.9}
        self.assertDictAlmostEqual(result, expected)

    def test_intervention_recompute_zero_base_effectiveness(self):
        """Test recompute with zero base effectiveness"""
        # Mock rules response
        mock_rules = [
            {
                'id': 1,
                'effect_id': 201,
                'multiplier': 1.5
            }
        ]
        
        # Mock current scores response with zero score
        mock_scores = [
            {
                'intervention_id': 201,
                'current_score': 0.0
            }
        ]
        
        self.mock_result.mappings.return_value.all.side_effect = [mock_rules, mock_scores]
        
        result = intervention_recompute(self.mock_conn, 123, 101)
        
        # Verify calculations: 0.0 * 1.5 = 0.0
        expected = {201: 0.0}
        self.assertDictAlmostEqual(result, expected)

    def test_intervention_recompute_negative_multiplier(self):
        """Test recompute with negative multiplier"""
        # Mock rules response
        mock_rules = [
            {
                'id': 1,
                'effect_id': 201,
                'multiplier': -1.0
            }
        ]
        
        # Mock current scores response
        mock_scores = [
            {
                'intervention_id': 201,
                'current_score': 0.8
            }
        ]
        
        self.mock_result.mappings.return_value.all.side_effect = [mock_rules, mock_scores]
        
        result = intervention_recompute(self.mock_conn, 123, 101)
        
        # Verify calculations: 0.8 * -1.0 = -0.8
        expected = {201: -0.8}
        self.assertDictAlmostEqual(result, expected)

    def test_intervention_recompute_complex_multipliers(self):
        """Test recompute with complex multiplier combinations"""
        # Mock rules response - multiple rules with fractional multipliers
        mock_rules = [
            {
                'id': 1,
                'effect_id': 201,
                'multiplier': 0.5
            },
            {
                'id': 2,
                'effect_id': 201,
                'multiplier': 2.0
            },
            {
                'id': 3,
                'effect_id': 202,
                'multiplier': 1.1
            },
            {
                'id': 4,
                'effect_id': 202,
                'multiplier': 1.1
            }
        ]
        
        # Mock current scores response
        mock_scores = [
            {
                'intervention_id': 201,
                'current_score': 1.0
            },
            {
                'intervention_id': 202,
                'current_score': 1.0
            }
        ]
        
        self.mock_result.mappings.return_value.all.side_effect = [mock_rules, mock_scores]
        
        result = intervention_recompute(self.mock_conn, 123, 101)
        
        # Verify calculations (with floating point tolerance)
        expected = {
            201: 1.0 * 0.5 * 2.0,  # 1.0
            202: 1.0 * 1.1 * 1.1   # 1.21
        }
        self.assertDictAlmostEqual(result, expected)

    def test_intervention_recompute_payload_structure(self):
        """Test that the upsert payload is correctly structured"""
        # Mock rules response
        mock_rules = [
            {
                'id': 1,
                'effect_id': 201,
                'multiplier': 1.5
            },
            {
                'id': 2,
                'effect_id': 202,
                'multiplier': 0.8
            }
        ]
        
        # Mock current scores response
        mock_scores = [
            {
                'intervention_id': 201,
                'current_score': 1.0
            },
            {
                'intervention_id': 202,
                'current_score': 0.5
            }
        ]
        
        self.mock_result.mappings.return_value.all.side_effect = [mock_rules, mock_scores]
        
        result = intervention_recompute(self.mock_conn, 123, 101)
        
        # Verify upsert call parameters
        upsert_call = self.mock_conn.execute.call_args_list[2]
        params = upsert_call[0][1]  # Get the payload parameter
        
        # Should have 2 items in payload
        self.assertEqual(len(params), 2)
        
        # Verify first payload item (with floating point tolerance)
        self.assertEqual(params[0]['project_id'], 123)
        self.assertEqual(params[0]['intervention_id'], 201)
        self.assertAlmostEqual(params[0]['score'], 1.5, places=7)  # 1.0 * 1.5
        
        # Verify second payload item (with floating point tolerance)
        self.assertEqual(params[1]['project_id'], 123)
        self.assertEqual(params[1]['intervention_id'], 202)
        self.assertAlmostEqual(params[1]['score'], 0.4, places=7)  # 0.5 * 0.8

    def test_intervention_recompute_missing_effect_intervention(self):
        """Test recompute when an effect intervention doesn't exist in scores"""
        # Mock rules response
        mock_rules = [
            {
                'id': 1,
                'effect_id': 201,
                'multiplier': 1.5
            },
            {
                'id': 2,
                'effect_id': 999,  # This intervention doesn't exist in scores
                'multiplier': 2.0
            }
        ]
        
        # Mock current scores response - only 201 exists
        mock_scores = [
            {
                'intervention_id': 201,
                'current_score': 1.0
            }
        ]
        
        self.mock_result.mappings.return_value.all.side_effect = [mock_rules, mock_scores]
        
        result = intervention_recompute(self.mock_conn, 123, 101)
        
        # Should only return scores for interventions that exist
        expected = {201: 1.5}
        self.assertDictAlmostEqual(result, expected)
        
        # Should only upsert existing interventions
        upsert_call = self.mock_conn.execute.call_args_list[2]
        params = upsert_call[0][1]
        self.assertEqual(len(params), 1)  # Only one intervention to upsert


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions"""
    
    def setUp(self):
        self.mock_conn = MagicMock()
        self.mock_result = MagicMock()
        self.mock_conn.execute.return_value = self.mock_result

    def assertDictAlmostEqual(self, dict1, dict2, places=7):
        """Helper method to compare dictionaries with floating point values"""
        self.assertEqual(dict1.keys(), dict2.keys())
        for key in dict1:
            self.assertAlmostEqual(dict1[key], dict2[key], places=places)

    def test_intervention_recompute_empty_multipliers(self):
        """Test when multiplier aggregation results in empty dict"""
        # This shouldn't happen in practice, but test the logic
        # Mock rules response
        mock_rules = []  # No rules
        
        self.mock_result.mappings.return_value.all.return_value = mock_rules
        
        result = intervention_recompute(self.mock_conn, 123, 101)
        
        self.assertEqual(result, {})
        # Should only call execute once (for rules query)
        self.mock_conn.execute.assert_called_once()

    def test_intervention_recompute_very_small_multipliers(self):
        """Test with very small multiplier values"""
        # Mock rules response
        mock_rules = [
            {
                'id': 1,
                'effect_id': 201,
                'multiplier': 0.001
            }
        ]
        
        # Mock current scores response
        mock_scores = [
            {
                'intervention_id': 201,
                'current_score': 1000.0
            }
        ]
        
        self.mock_result.mappings.return_value.all.side_effect = [mock_rules, mock_scores]
        
        result = intervention_recompute(self.mock_conn, 123, 101)
        
        # Verify calculations: 1000.0 * 0.001 = 1.0
        expected = {201: 1.0}
        self.assertDictAlmostEqual(result, expected)

    def test_intervention_recompute_large_values(self):
        """Test with large values that might cause floating point issues"""
        # Mock rules response
        mock_rules = [
            {
                'id': 1,
                'effect_id': 201,
                'multiplier': 1000.0
            }
        ]
        
        # Mock current scores response
        mock_scores = [
            {
                'intervention_id': 201,
                'current_score': 1000.0
            }
        ]
        
        self.mock_result.mappings.return_value.all.side_effect = [mock_rules, mock_scores]
        
        result = intervention_recompute(self.mock_conn, 123, 101)
        
        # Verify calculations: 1000.0 * 1000.0 = 1000000.0
        expected = {201: 1000000.0}
        self.assertDictAlmostEqual(result, expected)


if __name__ == '__main__':
    unittest.main()