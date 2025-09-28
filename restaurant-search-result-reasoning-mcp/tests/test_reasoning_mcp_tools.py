#!/usr/bin/env python3
"""
Test suite for Restaurant Reasoning MCP Tools.

This module provides comprehensive tests for the MCP tools exposed by the
restaurant reasoning server, including parameter validation, tool execution,
response formatting, and error handling scenarios.
"""

import sys
import os
import json
import unittest
from typing import Dict, Any, List

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from restaurant_reasoning_mcp_server import (
    recommend_restaurants,
    analyze_restaurant_sentiment,
    validate_restaurant_list_parameter,
    validate_ranking_method_parameter,
    format_error_response
)


class TestReasoningMCPTools(unittest.TestCase):
    """Test cases for restaurant reasoning MCP tools."""
    
    def setUp(self):
        """Set up test data for MCP tool tests."""
        # Valid test restaurant data
        self.valid_restaurants = [
            {
                "id": "rest_001",
                "name": "Excellent Dim Sum",
                "address": "123 Central Street",
                "meal_type": ["breakfast", "lunch"],
                "sentiment": {"likes": 85, "dislikes": 10, "neutral": 5},
                "location_category": "restaurant",
                "district": "Central district",
                "price_range": "$$$"
            },
            {
                "id": "rest_002", 
                "name": "Great Noodle House",
                "address": "456 Admiralty Road",
                "meal_type": ["lunch", "dinner"],
                "sentiment": {"likes": 70, "dislikes": 15, "neutral": 15},
                "location_category": "restaurant",
                "district": "Admiralty",
                "price_range": "$$"
            },
            {
                "id": "rest_003",
                "name": "Amazing Seafood",
                "address": "789 Causeway Bay",
                "meal_type": ["dinner"],
                "sentiment": {"likes": 95, "dislikes": 3, "neutral": 2},
                "location_category": "restaurant", 
                "district": "Causeway Bay",
                "price_range": "$$$$"
            },
            {
                "id": "rest_004",
                "name": "Good Coffee Shop",
                "address": "321 Wan Chai",
                "meal_type": ["breakfast"],
                "sentiment": {"likes": 60, "dislikes": 20, "neutral": 20},
                "location_category": "cafe",
                "district": "Wan Chai",
                "price_range": "$"
            }
        ]
        
        # Invalid restaurant data for testing validation
        self.invalid_restaurants = [
            {
                "id": "invalid_001",
                "name": "Missing Sentiment",
                "address": "Test Address"
                # Missing sentiment field
            },
            {
                "id": "invalid_002",
                "name": "Invalid Sentiment",
                "sentiment": {"likes": "not_a_number", "dislikes": 5, "neutral": 3}
            }
        ]
        
        # Minimal valid restaurant for edge case testing
        self.minimal_restaurant = [{
            "id": "minimal_001",
            "name": "Minimal Restaurant",
            "address": "Minimal Address",
            "meal_type": ["lunch"],
            "sentiment": {"likes": 1, "dislikes": 0, "neutral": 0},
            "location_category": "restaurant",
            "district": "Test District",
            "price_range": "$"
        }]
    
    def test_recommend_restaurants_valid_input(self):
        """Test recommend_restaurants with valid input data."""
        # Test with sentiment_likes ranking
        result = recommend_restaurants(self.valid_restaurants, "sentiment_likes")
        
        # Parse JSON response
        response = json.loads(result)
        
        # Verify response structure
        self.assertTrue(response["success"])
        self.assertIn("data", response)
        
        data = response["data"]
        self.assertIn("recommendation", data)
        self.assertIn("candidates", data)
        self.assertIn("ranking_method", data)
        self.assertIn("analysis_summary", data)
        
        # Verify ranking method
        self.assertEqual(data["ranking_method"], "sentiment_likes")
        
        # Verify we have candidates and a recommendation
        self.assertGreater(len(data["candidates"]), 0)
        self.assertIsInstance(data["recommendation"], dict)
        
        # Verify recommendation is from candidates
        recommendation_id = data["recommendation"]["id"]
        candidate_ids = [c["id"] for c in data["candidates"]]
        self.assertIn(recommendation_id, candidate_ids)
    
    def test_recommend_restaurants_combined_sentiment(self):
        """Test recommend_restaurants with combined_sentiment ranking method."""
        result = recommend_restaurants(self.valid_restaurants, "combined_sentiment")
        
        response = json.loads(result)
        
        self.assertTrue(response["success"])
        self.assertEqual(response["data"]["ranking_method"], "combined_sentiment")
        
        # Verify candidates are properly ranked by combined sentiment
        candidates = response["data"]["candidates"]
        self.assertGreater(len(candidates), 0)
        
        # Check that each candidate has sentiment data
        for candidate in candidates:
            self.assertIn("sentiment", candidate)
            sentiment = candidate["sentiment"]
            self.assertIn("likes", sentiment)
            self.assertIn("dislikes", sentiment)
            self.assertIn("neutral", sentiment)
    
    def test_recommend_restaurants_minimal_data(self):
        """Test recommend_restaurants with minimal valid data."""
        result = recommend_restaurants(self.minimal_restaurant, "sentiment_likes")
        
        response = json.loads(result)
        
        self.assertTrue(response["success"])
        self.assertEqual(len(response["data"]["candidates"]), 1)
        self.assertEqual(response["data"]["recommendation"]["id"], "minimal_001")
    
    def test_recommend_restaurants_invalid_parameters(self):
        """Test recommend_restaurants with invalid parameters."""
        # Test with empty list
        result = recommend_restaurants([], "sentiment_likes")
        response = json.loads(result)
        self.assertFalse(response["success"])
        self.assertEqual(response["error"]["type"], "ValidationError")
        
        # Test with non-list parameter
        result = recommend_restaurants("not_a_list", "sentiment_likes")
        response = json.loads(result)
        self.assertFalse(response["success"])
        self.assertEqual(response["error"]["type"], "ValidationError")
        
        # Test with invalid ranking method
        result = recommend_restaurants(self.valid_restaurants, "invalid_method")
        response = json.loads(result)
        self.assertFalse(response["success"])
        self.assertEqual(response["error"]["type"], "ValidationError")
    
    def test_recommend_restaurants_invalid_restaurant_data(self):
        """Test recommend_restaurants with invalid restaurant data."""
        result = recommend_restaurants(self.invalid_restaurants, "sentiment_likes")
        
        response = json.loads(result)
        
        # Should fail validation
        self.assertFalse(response["success"])
        self.assertEqual(response["error"]["type"], "ValidationError")
    
    def test_analyze_restaurant_sentiment_valid_input(self):
        """Test analyze_restaurant_sentiment with valid input data."""
        result = analyze_restaurant_sentiment(self.valid_restaurants)
        
        response = json.loads(result)
        
        # Verify response structure
        self.assertTrue(response["success"])
        self.assertIn("data", response)
        
        data = response["data"]
        self.assertIn("sentiment_analysis", data)
        self.assertIn("restaurant_count", data)
        self.assertIn("ranking_method", data)
        
        # Verify sentiment analysis structure
        analysis = data["sentiment_analysis"]
        self.assertIn("restaurant_count", analysis)
        self.assertIn("average_likes", analysis)
        self.assertIn("average_dislikes", analysis)
        self.assertIn("average_neutral", analysis)
        self.assertIn("top_sentiment_score", analysis)
        self.assertIn("bottom_sentiment_score", analysis)
        
        # Verify restaurant count matches input
        self.assertEqual(data["restaurant_count"], len(self.valid_restaurants))
    
    def test_analyze_restaurant_sentiment_minimal_data(self):
        """Test analyze_restaurant_sentiment with minimal data."""
        result = analyze_restaurant_sentiment(self.minimal_restaurant)
        
        response = json.loads(result)
        
        self.assertTrue(response["success"])
        self.assertEqual(response["data"]["restaurant_count"], 1)
    
    def test_analyze_restaurant_sentiment_invalid_parameters(self):
        """Test analyze_restaurant_sentiment with invalid parameters."""
        # Test with empty list
        result = analyze_restaurant_sentiment([])
        response = json.loads(result)
        self.assertFalse(response["success"])
        self.assertEqual(response["error"]["type"], "ValidationError")
        
        # Test with non-list parameter
        result = analyze_restaurant_sentiment("not_a_list")
        response = json.loads(result)
        self.assertFalse(response["success"])
        self.assertEqual(response["error"]["type"], "ValidationError")
    
    def test_analyze_restaurant_sentiment_invalid_data(self):
        """Test analyze_restaurant_sentiment with invalid restaurant data."""
        result = analyze_restaurant_sentiment(self.invalid_restaurants)
        
        response = json.loads(result)
        
        # Should fail validation
        self.assertFalse(response["success"])
        self.assertEqual(response["error"]["type"], "ValidationError")
    
    def test_validate_restaurant_list_parameter(self):
        """Test restaurant list parameter validation function."""
        # Valid list
        is_valid, error_msg = validate_restaurant_list_parameter(self.valid_restaurants)
        self.assertTrue(is_valid)
        self.assertEqual(error_msg, "")
        
        # Empty list
        is_valid, error_msg = validate_restaurant_list_parameter([])
        self.assertFalse(is_valid)
        self.assertIn("cannot be empty", error_msg)
        
        # Non-list
        is_valid, error_msg = validate_restaurant_list_parameter("not_a_list")
        self.assertFalse(is_valid)
        self.assertIn("must be a list", error_msg)
        
        # List with non-dict items
        is_valid, error_msg = validate_restaurant_list_parameter(["not_a_dict"])
        self.assertFalse(is_valid)
        self.assertIn("must be a dictionary", error_msg)
    
    def test_validate_ranking_method_parameter(self):
        """Test ranking method parameter validation function."""
        # Valid methods
        is_valid, error_msg = validate_ranking_method_parameter("sentiment_likes")
        self.assertTrue(is_valid)
        self.assertEqual(error_msg, "")
        
        is_valid, error_msg = validate_ranking_method_parameter("combined_sentiment")
        self.assertTrue(is_valid)
        self.assertEqual(error_msg, "")
        
        # Invalid method
        is_valid, error_msg = validate_ranking_method_parameter("invalid_method")
        self.assertFalse(is_valid)
        self.assertIn("Invalid ranking method", error_msg)
        
        # Non-string
        is_valid, error_msg = validate_ranking_method_parameter(123)
        self.assertFalse(is_valid)
        self.assertIn("must be a string", error_msg)
    
    def test_format_error_response(self):
        """Test error response formatting function."""
        # Basic error response
        result = format_error_response("Test error message", "TestError")
        response = json.loads(result)
        
        self.assertFalse(response["success"])
        self.assertEqual(response["error"]["type"], "TestError")
        self.assertEqual(response["error"]["message"], "Test error message")
        self.assertIn("timestamp", response["error"])
        
        # Error response with details
        details = {"field": "test_field", "value": "test_value"}
        result = format_error_response("Test error", "TestError", details)
        response = json.loads(result)
        
        self.assertEqual(response["error"]["details"], details)
    
    def test_response_json_serialization(self):
        """Test that all MCP tool responses are valid JSON."""
        # Test successful responses
        result = recommend_restaurants(self.valid_restaurants, "sentiment_likes")
        self.assertIsInstance(json.loads(result), dict)
        
        result = analyze_restaurant_sentiment(self.valid_restaurants)
        self.assertIsInstance(json.loads(result), dict)
        
        # Test error responses
        result = recommend_restaurants([], "sentiment_likes")
        self.assertIsInstance(json.loads(result), dict)
        
        result = analyze_restaurant_sentiment([])
        self.assertIsInstance(json.loads(result), dict)
    
    def test_mcp_tool_parameter_schemas(self):
        """Test that MCP tools handle parameter schemas correctly."""
        # Test that tools can handle various parameter combinations
        test_cases = [
            # Valid cases
            (self.valid_restaurants, "sentiment_likes"),
            (self.valid_restaurants, "combined_sentiment"),
            (self.minimal_restaurant, "sentiment_likes"),
            
            # Invalid cases that should be handled gracefully
            ([], "sentiment_likes"),
            (self.valid_restaurants, "invalid_method"),
            ("not_a_list", "sentiment_likes")
        ]
        
        for restaurants, ranking_method in test_cases:
            try:
                result = recommend_restaurants(restaurants, ranking_method)
                response = json.loads(result)
                
                # Should always return a valid JSON response
                self.assertIn("success", response)
                
                if not response["success"]:
                    # Error responses should have proper structure
                    self.assertIn("error", response)
                    self.assertIn("type", response["error"])
                    self.assertIn("message", response["error"])
                
            except Exception as e:
                self.fail(f"MCP tool should handle all inputs gracefully, but got exception: {e}")


class TestMCPToolIntegration(unittest.TestCase):
    """Integration tests for MCP tools with the reasoning service."""
    
    def setUp(self):
        """Set up integration test data."""
        # Large dataset for testing performance and edge cases
        self.large_dataset = []
        for i in range(25):  # More than default candidate count of 20
            restaurant = {
                "id": f"rest_{i:03d}",
                "name": f"Restaurant {i}",
                "address": f"{i} Test Street",
                "meal_type": ["lunch"],
                "sentiment": {
                    "likes": 50 + i,  # Varying likes for ranking
                    "dislikes": 10,
                    "neutral": 5
                },
                "location_category": "restaurant",
                "district": "Test District",
                "price_range": "$$"
            }
            self.large_dataset.append(restaurant)
    
    def test_candidate_selection_with_large_dataset(self):
        """Test that candidate selection works correctly with datasets larger than 20."""
        result = recommend_restaurants(self.large_dataset, "sentiment_likes")
        response = json.loads(result)
        
        self.assertTrue(response["success"])
        
        # Should return exactly 20 candidates (default limit)
        candidates = response["data"]["candidates"]
        self.assertEqual(len(candidates), 20)
        
        # Candidates should be properly ranked (highest likes first)
        likes_scores = [c["sentiment"]["likes"] for c in candidates]
        self.assertEqual(likes_scores, sorted(likes_scores, reverse=True))
        
        # Recommendation should be from the candidates
        recommendation_id = response["data"]["recommendation"]["id"]
        candidate_ids = [c["id"] for c in candidates]
        self.assertIn(recommendation_id, candidate_ids)
    
    def test_ranking_consistency(self):
        """Test that ranking methods produce consistent results."""
        # Test sentiment_likes ranking
        result1 = recommend_restaurants(self.large_dataset, "sentiment_likes")
        result2 = recommend_restaurants(self.large_dataset, "sentiment_likes")
        
        response1 = json.loads(result1)
        response2 = json.loads(result2)
        
        # Candidates should be in the same order (deterministic ranking)
        candidates1 = response1["data"]["candidates"]
        candidates2 = response2["data"]["candidates"]
        
        candidate_ids1 = [c["id"] for c in candidates1]
        candidate_ids2 = [c["id"] for c in candidates2]
        
        self.assertEqual(candidate_ids1, candidate_ids2)
    
    def test_sentiment_analysis_accuracy(self):
        """Test that sentiment analysis produces accurate statistics."""
        result = analyze_restaurant_sentiment(self.large_dataset)
        response = json.loads(result)
        
        self.assertTrue(response["success"])
        
        analysis = response["data"]["sentiment_analysis"]
        
        # Verify restaurant count
        self.assertEqual(analysis["restaurant_count"], len(self.large_dataset))
        
        # Verify average calculations
        expected_avg_likes = sum(r["sentiment"]["likes"] for r in self.large_dataset) / len(self.large_dataset)
        self.assertAlmostEqual(analysis["average_likes"], expected_avg_likes, places=2)
        
        # Verify score ranges
        likes_scores = [r["sentiment"]["likes"] for r in self.large_dataset]
        expected_top_score = max(likes_scores) / (max(likes_scores) + 10 + 5) * 100  # likes percentage
        expected_bottom_score = min(likes_scores) / (min(likes_scores) + 10 + 5) * 100
        
        self.assertAlmostEqual(analysis["top_sentiment_score"], expected_top_score, places=2)
        self.assertAlmostEqual(analysis["bottom_sentiment_score"], expected_bottom_score, places=2)


def run_mcp_tool_tests():
    """Run all MCP tool tests and display results."""
    print("Running Restaurant Reasoning MCP Tool Tests...")
    print("=" * 60)
    
    # Create test suite
    loader = unittest.TestLoader()
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_suite.addTest(loader.loadTestsFromTestCase(TestReasoningMCPTools))
    test_suite.addTest(loader.loadTestsFromTestCase(TestMCPToolIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print("\n" + "=" * 60)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print("\nFailures:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback}")
    
    if result.errors:
        print("\nErrors:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback}")
    
    success = len(result.failures) == 0 and len(result.errors) == 0
    print(f"\nOverall result: {'✅ PASSED' if success else '❌ FAILED'}")
    
    return success


if __name__ == "__main__":
    success = run_mcp_tool_tests()
    sys.exit(0 if success else 1)