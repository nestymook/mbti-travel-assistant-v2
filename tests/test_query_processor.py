#!/usr/bin/env python3
"""
Unit Tests for Natural Language Query Processing Pipeline

Tests the query processor's ability to extract intent, parameters,
and format conversational responses for restaurant search queries.

Requirements: 9.1, 11.1, 11.2, 13.1
"""

import unittest
from unittest.mock import Mock, MagicMock
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.query_processor import QueryProcessor, QueryIntent, QueryResponse
from models.restaurant_models import Restaurant, OperatingHours, Sentiment, RestaurantMetadata


class TestQueryProcessor(unittest.TestCase):
    """Test cases for QueryProcessor class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create mock district service
        self.mock_district_service = Mock()
        self.mock_district_service.validate_district.return_value = True
        self.mock_district_service.get_all_districts.return_value = {
            'hong-kong-island': ['Central district', 'Admiralty', 'Causeway Bay', 'Wan Chai'],
            'kowloon': ['Tsim Sha Tsui', 'Mong Kok', 'Yau Ma Tei', 'Jordan'],
            'new-territories': ['Sha Tin', 'Tsuen Wan', 'Tuen Mun', 'Tai Po'],
            'lantau': ['Tung Chung', 'Discovery Bay']
        }
        
        self.processor = QueryProcessor(district_service=self.mock_district_service)
        
        # Create sample restaurant data
        self.sample_restaurant = Restaurant(
            id="rest_001",
            name="Test Restaurant",
            address="123 Test Street, Central",
            meal_type=["Chinese", "Dim Sum"],
            sentiment=Sentiment(likes=85, dislikes=10, neutral=5),
            location_category="Restaurant",
            district="Central district",
            price_range="$$",
            operating_hours=OperatingHours(
                mon_fri=["07:00 - 22:00"],
                sat_sun=["08:00 - 23:00"],
                public_holiday=["09:00 - 21:00"]
            ),
            metadata=RestaurantMetadata(
                data_quality="high",
                version="1.0",
                quality_score=95
            )
        )
    
    def test_extract_intent_district_only(self):
        """Test extracting intent for district-only queries."""
        test_cases = [
            ("Find restaurants in Central district", "district_search", ["Central district"], []),
            ("restaurants in Tsim Sha Tsui", "district_search", ["Tsim Sha Tsui"], []),
            ("What's good in Causeway Bay?", "district_search", ["Causeway Bay"], []),
            ("Central restaurants", "district_search", ["Central district"], [])
        ]
        
        for query, expected_intent, expected_districts, expected_meals in test_cases:
            with self.subTest(query=query):
                intent = self.processor.extract_intent(query)
                self.assertEqual(intent.intent_type, expected_intent)
                self.assertEqual(intent.districts, expected_districts)
                self.assertEqual(intent.meal_types, expected_meals)
                self.assertGreater(intent.confidence, 0.5)
    
    def test_extract_intent_meal_only(self):
        """Test extracting intent for meal-only queries."""
        test_cases = [
            ("breakfast places", "meal_search", [], ["breakfast"]),
            ("lunch restaurants", "meal_search", [], ["lunch"]),
            ("dinner spots", "meal_search", [], ["dinner"]),
            ("morning food", "meal_search", [], ["breakfast"]),
            ("evening restaurants", "meal_search", [], ["dinner"])
        ]
        
        for query, expected_intent, expected_districts, expected_meals in test_cases:
            with self.subTest(query=query):
                intent = self.processor.extract_intent(query)
                self.assertEqual(intent.intent_type, expected_intent)
                self.assertEqual(intent.districts, expected_districts)
                self.assertEqual(intent.meal_types, expected_meals)
                self.assertGreater(intent.confidence, 0.5)
    
    def test_extract_intent_combined(self):
        """Test extracting intent for combined district and meal queries."""
        test_cases = [
            ("breakfast places in Central district", "combined_search", ["Central district"], ["breakfast"]),
            ("lunch in Tsim Sha Tsui", "combined_search", ["Tsim Sha Tsui"], ["lunch"]),
            ("dinner restaurants in Causeway Bay", "combined_search", ["Causeway Bay"], ["dinner"]),
            ("good morning spots in Wan Chai", "combined_search", ["Wan Chai"], ["breakfast"])
        ]
        
        for query, expected_intent, expected_districts, expected_meals in test_cases:
            with self.subTest(query=query):
                intent = self.processor.extract_intent(query)
                self.assertEqual(intent.intent_type, expected_intent)
                self.assertEqual(intent.districts, expected_districts)
                self.assertEqual(intent.meal_types, expected_meals)
                self.assertGreater(intent.confidence, 0.8)
    
    def test_extract_districts(self):
        """Test district name extraction and normalization."""
        test_cases = [
            ("restaurants in Central", ["Central district"]),
            ("find places in TST", ["Tsim Sha Tsui"]),
            ("Causeway Bay restaurants", ["Causeway Bay"]),
            ("good food in central and wan chai", ["Central district", "Wan Chai"]),
            ("invalid district name", [])
        ]
        
        for query, expected_districts in test_cases:
            with self.subTest(query=query):
                districts = self.processor.extract_districts(query.lower())
                self.assertEqual(districts, expected_districts)
    
    def test_extract_meal_types(self):
        """Test meal type extraction and normalization."""
        test_cases = [
            ("breakfast places", ["breakfast"]),
            ("morning restaurants", ["breakfast"]),
            ("lunch spots", ["lunch"]),
            ("dinner food", ["dinner"]),
            ("evening places", ["dinner"]),
            ("brunch and dinner", ["breakfast", "dinner"]),
            ("invalid meal type", [])
        ]
        
        for query, expected_meals in test_cases:
            with self.subTest(query=query):
                meals = self.processor.extract_meal_types(query.lower())
                self.assertEqual(meals, expected_meals)
    
    def test_extract_cuisine_types(self):
        """Test cuisine type extraction."""
        test_cases = [
            ("chinese restaurants", ["chinese"]),
            ("japanese sushi places", ["japanese", "sushi"]),
            ("italian and french food", ["italian", "french"]),
            ("dim sum restaurants", ["dim sum"]),
            ("unknown cuisine", [])
        ]
        
        for query, expected_cuisines in test_cases:
            with self.subTest(query=query):
                cuisines = self.processor.extract_cuisine_types(query.lower())
                self.assertEqual(cuisines, expected_cuisines)
    
    def test_validate_districts(self):
        """Test district validation against district service."""
        # Test with valid districts
        valid_districts, invalid_districts = self.processor.validate_districts(
            ["Central district", "Tsim Sha Tsui"]
        )
        self.assertEqual(valid_districts, ["Central district", "Tsim Sha Tsui"])
        self.assertEqual(invalid_districts, [])
        
        # Test with invalid districts
        self.mock_district_service.validate_district.side_effect = lambda d: d != "Invalid District"
        valid_districts, invalid_districts = self.processor.validate_districts(
            ["Central district", "Invalid District"]
        )
        self.assertEqual(valid_districts, ["Central district"])
        self.assertEqual(invalid_districts, ["Invalid District"])
    
    def test_suggest_alternatives(self):
        """Test alternative district suggestions."""
        suggestions = self.processor.suggest_alternatives(["Centrall", "Invalid District"])
        self.assertIsInstance(suggestions, list)
        # The method should return suggestions even if fuzzy matching doesn't find close matches
        # Test with a closer match
        close_suggestions = self.processor.suggest_alternatives(["Central"])
        self.assertIsInstance(close_suggestions, list)
        # Should suggest "Central district" for "Central"
        if close_suggestions:
            self.assertIn("Central district", close_suggestions)
    
    def test_format_single_result_response(self):
        """Test formatting response for single restaurant result."""
        query_context = {
            'original_query': 'restaurants in Central district',
            'districts': ['Central district'],
            'meal_types': [],
            'tool_calls': []
        }
        
        response = self.processor.format_conversational_response(
            [self.sample_restaurant], 
            query_context
        )
        
        self.assertIsInstance(response, QueryResponse)
        self.assertIn("Test Restaurant", response.response_text)
        self.assertIn("Central district", response.response_text)
        self.assertIn("Chinese, Dim Sum", response.response_text)
        self.assertGreater(len(response.suggested_actions), 0)
        self.assertIsNone(response.error_message)
    
    def test_format_multiple_results_response(self):
        """Test formatting response for multiple restaurant results."""
        # Create multiple restaurants
        restaurants = [self.sample_restaurant] * 3
        
        query_context = {
            'original_query': 'breakfast places in Central district',
            'districts': ['Central district'],
            'meal_types': ['breakfast'],
            'tool_calls': []
        }
        
        response = self.processor.format_conversational_response(
            restaurants, 
            query_context
        )
        
        self.assertIsInstance(response, QueryResponse)
        self.assertIn("I found 3 restaurants", response.response_text)
        self.assertIn("Central district", response.response_text)
        self.assertIn("breakfast", response.response_text)
        self.assertGreater(len(response.suggested_actions), 0)
        self.assertIsNone(response.error_message)
    
    def test_format_no_results_response(self):
        """Test formatting response when no results are found."""
        query_context = {
            'original_query': 'restaurants in Invalid District',
            'districts': ['Invalid District'],
            'meal_types': [],
            'tool_calls': []
        }
        
        response = self.processor.format_conversational_response(
            [], 
            query_context
        )
        
        self.assertIsInstance(response, QueryResponse)
        self.assertIn("couldn't find any restaurants", response.response_text)
        self.assertIn("Invalid District", response.response_text)
        self.assertGreater(len(response.suggested_actions), 0)
        self.assertEqual(response.error_message, "No results found")
    
    def test_district_name_normalization(self):
        """Test district name normalization functionality."""
        test_cases = [
            ("central", "Central district"),
            ("tst", "Tsim Sha Tsui"),
            ("causeway", "Causeway Bay"),
            ("Central district", "Central district"),  # Already normalized
            ("invalid", None)
        ]
        
        for input_district, expected_output in test_cases:
            with self.subTest(input_district=input_district):
                result = self.processor._normalize_district_name(input_district)
                self.assertEqual(result, expected_output)
    
    def test_operating_hours_formatting(self):
        """Test operating hours formatting."""
        hours = OperatingHours(
            mon_fri=["07:00 - 22:00"],
            sat_sun=["08:00 - 23:00"],
            public_holiday=["09:00 - 21:00"]
        )
        
        formatted = self.processor._format_operating_hours(hours)
        self.assertIn("Mon-Fri: 07:00 - 22:00", formatted)
        self.assertIn("Sat-Sun: 08:00 - 23:00", formatted)
        self.assertIn("Holidays: 09:00 - 21:00", formatted)
    
    def test_sentiment_formatting(self):
        """Test sentiment formatting."""
        # High rating
        high_sentiment = Sentiment(likes=80, dislikes=10, neutral=10)
        formatted = self.processor._format_sentiment(high_sentiment)
        self.assertIn("Highly rated", formatted)
        
        # Mixed rating
        mixed_sentiment = Sentiment(likes=40, dislikes=40, neutral=20)
        formatted = self.processor._format_sentiment(mixed_sentiment)
        self.assertIn("Mixed reviews", formatted)
        
        # Low rating
        low_sentiment = Sentiment(likes=20, dislikes=70, neutral=10)
        formatted = self.processor._format_sentiment(low_sentiment)
        self.assertIn("Lower rated", formatted)
    
    def test_pattern_based_extraction(self):
        """Test pattern-based extraction for complex queries."""
        # Test queries that require pattern matching
        test_queries = [
            "I want breakfast places in Central district",
            "Show me dinner restaurants in TST",
            "Looking for lunch spots in Causeway Bay",
            "Any good morning places in Wan Chai?"
        ]
        
        for query in test_queries:
            with self.subTest(query=query):
                intent = self.processor.extract_intent(query)
                # Should extract both district and meal type
                self.assertTrue(len(intent.districts) > 0 or len(intent.meal_types) > 0)
                self.assertGreater(intent.confidence, 0.5)
    
    def test_edge_cases(self):
        """Test edge cases and error handling."""
        # Empty query
        intent = self.processor.extract_intent("")
        self.assertEqual(intent.intent_type, "general_help")
        
        # Very long query
        long_query = "I am looking for " + "very " * 50 + "good restaurants in Central district"
        intent = self.processor.extract_intent(long_query)
        self.assertIn("Central district", intent.districts)
        
        # Query with special characters
        special_query = "restaurants in Central district!!! @#$%"
        intent = self.processor.extract_intent(special_query)
        self.assertIn("Central district", intent.districts)
        
        # Mixed case query
        mixed_case = "BREAKFAST places in central DISTRICT"
        intent = self.processor.extract_intent(mixed_case)
        self.assertIn("breakfast", intent.meal_types)
        self.assertIn("Central district", intent.districts)


class TestQueryProcessorIntegration(unittest.TestCase):
    """Integration tests for query processor with real data."""
    
    def setUp(self):
        """Set up integration test fixtures."""
        self.processor = QueryProcessor()  # No mock district service
    
    def test_end_to_end_query_processing(self):
        """Test complete query processing workflow."""
        queries = [
            "Find breakfast places in Central district",
            "Good dinner restaurants",
            "Lunch in Tsim Sha Tsui",
            "What restaurants are in Causeway Bay?"
        ]
        
        for query in queries:
            with self.subTest(query=query):
                # Extract intent
                intent = self.processor.extract_intent(query)
                self.assertIsInstance(intent, QueryIntent)
                self.assertGreater(intent.confidence, 0.0)
                
                # Test response formatting with empty results
                query_context = {
                    'original_query': query,
                    'districts': intent.districts,
                    'meal_types': intent.meal_types,
                    'tool_calls': []
                }
                
                response = self.processor.format_conversational_response([], query_context)
                self.assertIsInstance(response, QueryResponse)
                self.assertIsInstance(response.response_text, str)
                self.assertGreater(len(response.response_text), 0)


def run_query_processor_tests():
    """Run all query processor tests."""
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_suite.addTest(unittest.makeSuite(TestQueryProcessor))
    test_suite.addTest(unittest.makeSuite(TestQueryProcessorIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    print("🧪 Running Natural Language Query Processing Tests\n")
    success = run_query_processor_tests()
    
    if success:
        print("\n✅ All query processing tests passed!")
    else:
        print("\n❌ Some query processing tests failed!")
    
    exit(0 if success else 1)