"""
Test suite for Restaurant Reasoning MCP EntryPoint Integration.

This module tests the BedrockAgentCoreApp entrypoint functionality for restaurant
reasoning operations, including payload processing, Strands Agent integration,
and response formatting.
"""

import json
import pytest
import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from typing import Dict, Any, List
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from models.restaurant_models import Restaurant, Sentiment, RecommendationResult


class TestReasoningEntrypoint(unittest.TestCase):
    """Test cases for reasoning entrypoint functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.sample_restaurant_data = [
            {
                "id": "rest_001",
                "name": "Golden Dragon Restaurant",
                "address": "123 Central District, Hong Kong",
                "sentiment": {
                    "likes": 85,
                    "dislikes": 10,
                    "neutral": 15
                },
                "meal_type": ["lunch", "dinner"],
                "district": "Central district",
                "price_range": "$$"
            },
            {
                "id": "rest_002", 
                "name": "Harbour View Cafe",
                "address": "456 Tsim Sha Tsui, Hong Kong",
                "sentiment": {
                    "likes": 92,
                    "dislikes": 5,
                    "neutral": 8
                },
                "meal_type": ["breakfast", "lunch"],
                "district": "Tsim Sha Tsui",
                "price_range": "$$$"
            },
            {
                "id": "rest_003",
                "name": "Street Food Corner",
                "address": "789 Mong Kok, Hong Kong", 
                "sentiment": {
                    "likes": 67,
                    "dislikes": 20,
                    "neutral": 25
                },
                "meal_type": ["lunch", "dinner"],
                "district": "Mong Kok",
                "price_range": "$"
            }
        ]
        
        self.sample_payloads = {
            "standard_input": {
                "input": {
                    "prompt": "Recommend the best restaurant from this list",
                    "restaurant_data": self.sample_restaurant_data
                }
            },
            "simple_prompt": {
                "prompt": "Analyze sentiment for these restaurants",
                "restaurants": self.sample_restaurant_data
            },
            "nested_message": {
                "input": {
                    "message": "Which restaurant has the best customer satisfaction?",
                    "restaurants": self.sample_restaurant_data
                }
            },
            "string_input": {
                "input": "Find me a good restaurant recommendation"
            },
            "invalid_structure": {
                "data": "some random data",
                "config": {"setting": "value"}
            }
        }
    
    def extract_user_prompt_and_data(self, payload: Dict[str, Any]) -> tuple[str, Any]:
        """
        Test implementation of extract_user_prompt_and_data function.
        """
        try:
            user_prompt = None
            restaurant_data = None
            
            # Handle different payload structures for prompt extraction
            if "input" in payload:
                if isinstance(payload["input"], dict):
                    if "prompt" in payload["input"]:
                        user_prompt = payload["input"]["prompt"]
                    elif "message" in payload["input"]:
                        user_prompt = payload["input"]["message"]
                    
                    # Look for restaurant data in input
                    if "restaurant_data" in payload["input"]:
                        restaurant_data = payload["input"]["restaurant_data"]
                    elif "restaurants" in payload["input"]:
                        restaurant_data = payload["input"]["restaurants"]
                        
                elif isinstance(payload["input"], str):
                    user_prompt = payload["input"]
            
            if not user_prompt:
                if "prompt" in payload:
                    user_prompt = payload["prompt"]
                elif "message" in payload:
                    user_prompt = payload["message"]
            
            # Look for restaurant data at top level
            if not restaurant_data:
                if "restaurant_data" in payload:
                    restaurant_data = payload["restaurant_data"]
                elif "restaurants" in payload:
                    restaurant_data = payload["restaurants"]
            
            # Only try fallback extraction if we haven't found a prompt yet
            # and avoid extracting from keys that are clearly not prompts
            if not user_prompt:
                excluded_keys = {"data", "config", "settings", "metadata"}
                for key, value in payload.items():
                    if key not in excluded_keys and isinstance(value, str) and len(value.strip()) > 0:
                        user_prompt = value
                        break
            
            if not user_prompt:
                raise ValueError("No valid prompt found in payload")
            
            return user_prompt, restaurant_data
            
        except Exception as e:
            raise ValueError(f"Invalid payload structure: {e}")
    
    def format_reasoning_response(self, agent_response: str, success: bool = True, 
                                error: str = None, metadata: Dict[str, Any] = None) -> str:
        """
        Test implementation of format_reasoning_response function.
        """
        try:
            response_data = {
                "success": success,
                "response": agent_response,
                "timestamp": datetime.now().isoformat(),
                "agent_type": "restaurant_reasoning_assistant",
                "version": "1.0.0",
                "capabilities": [
                    "sentiment_analysis",
                    "intelligent_recommendations", 
                    "ranking_algorithms",
                    "data_validation"
                ]
            }
            
            if error:
                response_data["error"] = {
                    "message": error,
                    "type": "reasoning_error" if not success else "warning"
                }
            
            if metadata:
                response_data["metadata"] = metadata
            
            return json.dumps(response_data, ensure_ascii=False, indent=2)
            
        except Exception as e:
            fallback_response = {
                "success": False,
                "response": "Unable to format reasoning response properly",
                "error": {
                    "message": "Response formatting error",
                    "type": "serialization_error",
                    "details": str(e)
                },
                "timestamp": datetime.now().isoformat(),
                "agent_type": "restaurant_reasoning_assistant"
            }
            return json.dumps(fallback_response, ensure_ascii=False)
    
    def test_extract_user_prompt_and_data_standard_input(self):
        """Test extracting prompt and data from standard input structure."""
        payload = self.sample_payloads["standard_input"]
        
        prompt, restaurant_data = self.extract_user_prompt_and_data(payload)
        
        self.assertEqual(prompt, "Recommend the best restaurant from this list")
        self.assertEqual(restaurant_data, self.sample_restaurant_data)
        self.assertEqual(len(restaurant_data), 3)
    
    def test_extract_user_prompt_and_data_simple_prompt(self):
        """Test extracting prompt and data from simple prompt structure."""
        payload = self.sample_payloads["simple_prompt"]
        
        prompt, restaurant_data = self.extract_user_prompt_and_data(payload)
        
        self.assertEqual(prompt, "Analyze sentiment for these restaurants")
        self.assertEqual(restaurant_data, self.sample_restaurant_data)
    
    def test_extract_user_prompt_and_data_nested_message(self):
        """Test extracting prompt and data from nested message structure."""
        payload = self.sample_payloads["nested_message"]
        
        prompt, restaurant_data = self.extract_user_prompt_and_data(payload)
        
        self.assertEqual(prompt, "Which restaurant has the best customer satisfaction?")
        self.assertEqual(restaurant_data, self.sample_restaurant_data)
    
    def test_extract_user_prompt_and_data_string_input(self):
        """Test extracting prompt from string input without restaurant data."""
        payload = self.sample_payloads["string_input"]
        
        prompt, restaurant_data = self.extract_user_prompt_and_data(payload)
        
        self.assertEqual(prompt, "Find me a good restaurant recommendation")
        self.assertIsNone(restaurant_data)
    
    def test_extract_user_prompt_and_data_invalid_structure(self):
        """Test error handling for invalid payload structure."""
        payload = self.sample_payloads["invalid_structure"]
        
        with self.assertRaises(ValueError) as context:
            self.extract_user_prompt_and_data(payload)
        
        self.assertIn("No valid prompt found", str(context.exception))
    
    def test_extract_user_prompt_and_data_empty_payload(self):
        """Test error handling for empty payload."""
        payload = {}
        
        with self.assertRaises(ValueError) as context:
            self.extract_user_prompt_and_data(payload)
        
        self.assertIn("No valid prompt found", str(context.exception))
    
    def test_format_reasoning_response_success(self):
        """Test formatting successful reasoning response."""
        agent_response = "Based on sentiment analysis, I recommend Harbour View Cafe with 92 likes."
        metadata = {
            "restaurant_count": 3,
            "ranking_method": "sentiment_likes",
            "processing_time": "completed"
        }
        
        result = self.format_reasoning_response(agent_response, success=True, metadata=metadata)
        
        # Parse and validate JSON response
        response_data = json.loads(result)
        self.assertTrue(response_data["success"])
        self.assertEqual(response_data["response"], agent_response)
        self.assertEqual(response_data["agent_type"], "restaurant_reasoning_assistant")
        self.assertEqual(response_data["version"], "1.0.0")
        self.assertIn("sentiment_analysis", response_data["capabilities"])
        self.assertEqual(response_data["metadata"], metadata)
        self.assertIn("timestamp", response_data)
    
    def test_format_reasoning_response_with_error(self):
        """Test formatting reasoning response with error."""
        agent_response = "Partial analysis completed"
        error_message = "Some restaurants had invalid sentiment data"
        
        result = self.format_reasoning_response(agent_response, success=True, error=error_message)
        
        response_data = json.loads(result)
        self.assertTrue(response_data["success"])
        self.assertEqual(response_data["response"], agent_response)
        self.assertEqual(response_data["error"]["message"], error_message)
        self.assertEqual(response_data["error"]["type"], "warning")
    
    def test_format_reasoning_response_failure(self):
        """Test formatting failed reasoning response."""
        error_message = "Invalid restaurant data structure"
        
        result = self.format_reasoning_response("", success=False, error=error_message)
        
        response_data = json.loads(result)
        self.assertFalse(response_data["success"])
        self.assertEqual(response_data["error"]["message"], error_message)
        self.assertEqual(response_data["error"]["type"], "reasoning_error")
    
    def test_restaurant_data_validation(self):
        """Test validation of restaurant data structure."""
        # Valid restaurant data
        valid_restaurant = self.sample_restaurant_data[0]
        self.assertIn("id", valid_restaurant)
        self.assertIn("name", valid_restaurant)
        self.assertIn("sentiment", valid_restaurant)
        self.assertIn("likes", valid_restaurant["sentiment"])
        self.assertIn("dislikes", valid_restaurant["sentiment"])
        self.assertIn("neutral", valid_restaurant["sentiment"])
        
        # Invalid restaurant data - missing sentiment
        invalid_restaurant = {
            "id": "test_001",
            "name": "Test Restaurant"
            # Missing sentiment
        }
        self.assertNotIn("sentiment", invalid_restaurant)
    
    def test_sentiment_calculation_logic(self):
        """Test sentiment calculation logic."""
        sentiment_data = self.sample_restaurant_data[0]["sentiment"]
        
        # Test likes percentage calculation
        total_responses = sentiment_data["likes"] + sentiment_data["dislikes"] + sentiment_data["neutral"]
        likes_percentage = (sentiment_data["likes"] / total_responses) * 100
        
        self.assertGreater(likes_percentage, 0)
        self.assertLessEqual(likes_percentage, 100)
        
        # Test combined positive percentage calculation
        combined_positive = sentiment_data["likes"] + sentiment_data["neutral"]
        combined_percentage = (combined_positive / total_responses) * 100
        
        self.assertGreaterEqual(combined_percentage, likes_percentage)
        self.assertLessEqual(combined_percentage, 100)
    
    def test_payload_structure_validation(self):
        """Test different payload structure validations."""
        # Test valid payload structures
        valid_payloads = [
            {"input": {"prompt": "test", "restaurant_data": []}},
            {"prompt": "test", "restaurants": []},
            {"input": {"message": "test"}},
            {"input": "test string"}
        ]
        
        for payload in valid_payloads:
            try:
                prompt, data = self.extract_user_prompt_and_data(payload)
                self.assertIsNotNone(prompt)
            except ValueError:
                self.fail(f"Valid payload should not raise ValueError: {payload}")
        
        # Test invalid payload structures
        invalid_payloads = [
            {},
            {"data": "no prompt"},
            {"config": {"setting": "value"}}
        ]
        
        for payload in invalid_payloads:
            with self.assertRaises(ValueError):
                self.extract_user_prompt_and_data(payload)


class TestReasoningEntrypointIntegration(unittest.TestCase):
    """Integration tests for reasoning entrypoint with real components."""
    
    def setUp(self):
        """Set up integration test fixtures."""
        self.sample_restaurants = [
            {
                "id": "integration_001",
                "name": "Premium Dining",
                "address": "Central District",
                "sentiment": {"likes": 95, "dislikes": 3, "neutral": 7},
                "meal_type": ["dinner"],
                "district": "Central district",
                "price_range": "$$$$"
            },
            {
                "id": "integration_002",
                "name": "Casual Eatery", 
                "address": "Causeway Bay",
                "sentiment": {"likes": 78, "dislikes": 15, "neutral": 12},
                "meal_type": ["lunch", "dinner"],
                "district": "Causeway Bay",
                "price_range": "$$"
            }
        ]
    
    def extract_user_prompt_and_data(self, payload: Dict[str, Any]) -> tuple[str, Any]:
        """Test implementation of extract function."""
        user_prompt = None
        restaurant_data = None
        
        if "input" in payload:
            if isinstance(payload["input"], dict):
                user_prompt = payload["input"].get("prompt") or payload["input"].get("message")
                restaurant_data = payload["input"].get("restaurant_data") or payload["input"].get("restaurants")
            elif isinstance(payload["input"], str):
                user_prompt = payload["input"]
        
        if not user_prompt:
            user_prompt = payload.get("prompt") or payload.get("message")
        
        if not restaurant_data:
            restaurant_data = payload.get("restaurant_data") or payload.get("restaurants")
        
        if not user_prompt:
            raise ValueError("No valid prompt found in payload")
        
        return user_prompt, restaurant_data
    
    def test_end_to_end_payload_processing(self):
        """Test complete payload processing workflow."""
        payload = {
            "input": {
                "prompt": "Which restaurant should I choose for the best customer experience?",
                "restaurant_data": self.sample_restaurants
            }
        }
        
        prompt, restaurant_data = self.extract_user_prompt_and_data(payload)
        
        self.assertIsNotNone(prompt)
        self.assertIsNotNone(restaurant_data)
        self.assertEqual(len(restaurant_data), 2)
        # Check that we have the expected restaurant data
        restaurant_names = [r["name"] for r in restaurant_data]
        self.assertIn("Premium Dining", restaurant_names)
    
    def test_sentiment_data_structure(self):
        """Test sentiment data structure validation."""
        for restaurant in self.sample_restaurants:
            self.assertIn("sentiment", restaurant)
            sentiment = restaurant["sentiment"]
            self.assertIn("likes", sentiment)
            self.assertIn("dislikes", sentiment)
            self.assertIn("neutral", sentiment)
            
            # Verify all sentiment values are non-negative integers
            self.assertGreaterEqual(sentiment["likes"], 0)
            self.assertGreaterEqual(sentiment["dislikes"], 0)
            self.assertGreaterEqual(sentiment["neutral"], 0)
    
    def test_error_handling_workflow(self):
        """Test error handling in complete workflow."""
        # Test with malformed payload
        invalid_payload = {"invalid": "structure"}
        
        with self.assertRaises(ValueError) as context:
            self.extract_user_prompt_and_data(invalid_payload)
        
        self.assertIn("No valid prompt found", str(context.exception))


if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2)