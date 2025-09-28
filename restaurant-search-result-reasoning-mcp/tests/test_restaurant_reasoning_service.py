"""
Unit tests for restaurant reasoning service.

This module provides comprehensive test coverage for the RestaurantReasoningService
including end-to-end reasoning workflow, ranking methods, and error handling.
"""

import unittest
from unittest.mock import patch, MagicMock
import logging
import json
from typing import List

# Import the modules to test
from services.restaurant_reasoning_service import RestaurantReasoningService
from models.restaurant_models import Restaurant, Sentiment, RecommendationResult, SentimentAnalysis
from models.validation_models import ValidationResult, ValidationError, ValidationErrorType


class TestRestaurantReasoningService(unittest.TestCase):
    """Test cases for RestaurantReasoningService class."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.reasoning_service = RestaurantReasoningService(
            minimum_responses=1,
            default_candidate_count=20,
            random_seed=42,  # Fixed seed for reproducible tests
            strict_validation=False
        )
        
        self.strict_reasoning_service = RestaurantReasoningService(
            minimum_responses=1,
            default_candidate_count=20,
            random_seed=42,
            strict_validation=True
        )
        
        # Sample restaurant data for testing
        self.sample_restaurant_data = [
            {
                "id": "rest_001",
                "name": "Great Restaurant",
                "address": "123 Main St",
                "meal_type": ["lunch", "dinner"],
                "sentiment": {"likes": 85, "dislikes": 10, "neutral": 5},
                "location_category": "urban",
                "district": "Central",
                "price_range": "$"
            },
            {
                "id": "rest_002", 
                "name": "Good Eats",
                "address": "456 Oak Ave",
                "meal_type": ["breakfast", "lunch"],
                "sentiment": {"likes": 70, "dislikes": 20, "neutral": 10},
                "location_category": "suburban",
                "district": "North",
                "price_range": "$"
            },
            {
                "id": "rest_003",
                "name": "Average Place",
                "address": "789 Pine Rd",
                "meal_type": ["dinner"],
                "sentiment": {"likes": 40, "dislikes": 30, "neutral": 30},
                "location_category": "urban",
                "district": "South",
                "price_range": "$$"
            },
            {
                "id": "rest_004",
                "name": "Popular Spot",
                "address": "321 Elm St",
                "meal_type": ["lunch", "dinner"],
                "sentiment": {"likes": 90, "dislikes": 5, "neutral": 5},
                "location_category": "urban",
                "district": "Central",
                "price_range": "$"
            },
            {
                "id": "rest_005",
                "name": "Neutral Choice",
                "address": "654 Maple Dr",
                "meal_type": ["breakfast"],
                "sentiment": {"likes": 30, "dislikes": 10, "neutral": 60},
                "location_category": "suburban",
                "district": "East",
                "price_range": "$"
            }
        ]
        
        # Invalid restaurant data for error testing
        self.invalid_restaurant_data = [
            {
                "id": "invalid_001",
                "name": "Missing Sentiment",
                "address": "123 Test St"
                # Missing sentiment field
            },
            {
                "id": "invalid_002",
                "name": "Invalid Sentiment",
                "address": "456 Test Ave",
                "sentiment": {"likes": -5, "dislikes": 10, "neutral": 5}  # Negative likes
            },
            {
                # Missing required fields
                "address": "789 Test Rd",
                "sentiment": {"likes": 10, "dislikes": 5, "neutral": 3}
            }
        ]
    
    def test_initialization(self):
        """Test RestaurantReasoningService initialization."""
        service = RestaurantReasoningService(
            minimum_responses=5,
            default_candidate_count=15,
            random_seed=123,
            strict_validation=True
        )
        
        self.assertEqual(service.minimum_responses, 5)
        self.assertEqual(service.default_candidate_count, 15)
        self.assertEqual(service.random_seed, 123)
        self.assertTrue(service.strict_validation)
        self.assertIsNotNone(service.validator)
        self.assertIsNotNone(service.sentiment_service)
        self.assertIsNotNone(service.recommendation_algorithm)
    
    def test_analyze_and_recommend_sentiment_likes(self):
        """Test end-to-end recommendation workflow with sentiment_likes ranking."""
        result = self.reasoning_service.analyze_and_recommend(
            restaurant_data=self.sample_restaurant_data,
            ranking_method="sentiment_likes",
            candidate_count=3
        )
        
        # Verify result structure
        self.assertIsInstance(result, RecommendationResult)
        self.assertEqual(len(result.candidates), 3)
        self.assertIn(result.recommendation, result.candidates)
        self.assertEqual(result.ranking_method, "sentiment_likes")
        
        # Verify candidates are sorted by sentiment likes (descending)
        candidate_likes = [c.sentiment.likes for c in result.candidates]
        self.assertEqual(candidate_likes, sorted(candidate_likes, reverse=True))
        
        # Verify analysis summary contains expected fields
        self.assertIn("data_quality", result.analysis_summary)
        self.assertIn("recommendation_confidence", result.analysis_summary)
        self.assertEqual(result.analysis_summary["data_quality"]["total_input_restaurants"], 5)
        self.assertEqual(result.analysis_summary["data_quality"]["valid_restaurants"], 5)
    
    def test_analyze_and_recommend_combined_sentiment(self):
        """Test end-to-end recommendation workflow with combined_sentiment ranking."""
        result = self.reasoning_service.analyze_and_recommend(
            restaurant_data=self.sample_restaurant_data,
            ranking_method="combined_sentiment",
            candidate_count=4
        )
        
        # Verify result structure
        self.assertIsInstance(result, RecommendationResult)
        self.assertEqual(len(result.candidates), 4)
        self.assertIn(result.recommendation, result.candidates)
        self.assertEqual(result.ranking_method, "combined_sentiment")
        
        # Verify candidates are sorted by combined sentiment (descending)
        candidate_scores = [c.combined_sentiment_score() for c in result.candidates]
        self.assertEqual(candidate_scores, sorted(candidate_scores, reverse=True))
    
    def test_analyze_and_recommend_invalid_ranking_method(self):
        """Test error handling for invalid ranking method."""
        with self.assertRaises(ValueError) as context:
            self.reasoning_service.analyze_and_recommend(
                restaurant_data=self.sample_restaurant_data,
                ranking_method="invalid_method"
            )
        
        # The error message includes validation details
        error_msg = str(context.exception)
        self.assertTrue("Invalid restaurant data" in error_msg or "Invalid ranking method" in error_msg)
    
    def test_analyze_and_recommend_empty_data(self):
        """Test error handling for empty restaurant data."""
        with self.assertRaises(ValueError) as context:
            self.reasoning_service.analyze_and_recommend(
                restaurant_data=[],
                ranking_method="sentiment_likes"
            )
        
        # The error message includes validation details
        error_msg = str(context.exception)
        self.assertTrue("Invalid restaurant data" in error_msg or "No valid restaurants" in error_msg)
    
    def test_analyze_and_recommend_invalid_data(self):
        """Test error handling for invalid restaurant data."""
        with self.assertRaises(ValueError) as context:
            self.reasoning_service.analyze_and_recommend(
                restaurant_data=self.invalid_restaurant_data,
                ranking_method="sentiment_likes"
            )
        
        self.assertIn("Invalid restaurant data", str(context.exception))
    
    def test_analyze_sentiment_only(self):
        """Test sentiment analysis without recommendation."""
        analysis = self.reasoning_service.analyze_sentiment_only(
            restaurant_data=self.sample_restaurant_data,
            ranking_method="sentiment_likes"
        )
        
        # Verify analysis structure
        self.assertIsInstance(analysis, SentimentAnalysis)
        self.assertEqual(analysis.restaurant_count, 5)
        self.assertEqual(analysis.ranking_method, "sentiment_likes")
        self.assertGreater(analysis.average_likes, 0)
        self.assertGreaterEqual(analysis.top_sentiment_score, analysis.bottom_sentiment_score)
    
    def test_validate_restaurant_data_valid(self):
        """Test validation of valid restaurant data."""
        result = self.reasoning_service.validate_restaurant_data(self.sample_restaurant_data)
        
        self.assertIsInstance(result, ValidationResult)
        self.assertTrue(result.is_valid)
        self.assertEqual(len(result.errors), 0)
        self.assertEqual(result.valid_count, 5)
        self.assertEqual(result.total_count, 5)
    
    def test_validate_restaurant_data_invalid(self):
        """Test validation of invalid restaurant data."""
        result = self.reasoning_service.validate_restaurant_data(self.invalid_restaurant_data)
        
        self.assertIsInstance(result, ValidationResult)
        self.assertFalse(result.is_valid)
        self.assertGreater(len(result.errors), 0)
        self.assertEqual(result.total_count, 3)
    
    def test_format_recommendation_response(self):
        """Test formatting of recommendation response."""
        result = self.reasoning_service.analyze_and_recommend(
            restaurant_data=self.sample_restaurant_data,
            ranking_method="sentiment_likes",
            candidate_count=3
        )
        
        # Test with analysis included
        response_json = self.reasoning_service.format_recommendation_response(result, include_analysis=True)
        response_data = json.loads(response_json)
        
        self.assertIn("recommendation", response_data)
        self.assertIn("candidates", response_data)
        self.assertIn("ranking_method", response_data)
        self.assertIn("analysis_summary", response_data)
        self.assertIn("timestamp", response_data)
        self.assertEqual(response_data["candidate_count"], 3)
    
    def test_format_sentiment_response(self):
        """Test formatting of sentiment analysis response."""
        analysis = self.reasoning_service.analyze_sentiment_only(
            restaurant_data=self.sample_restaurant_data,
            ranking_method="combined_sentiment"
        )
        
        response_json = self.reasoning_service.format_sentiment_response(analysis)
        response_data = json.loads(response_json)
        
        self.assertIn("sentiment_analysis", response_data)
        self.assertIn("timestamp", response_data)
        self.assertEqual(response_data["sentiment_analysis"]["restaurant_count"], 5)
        self.assertEqual(response_data["sentiment_analysis"]["ranking_method"], "combined_sentiment")
    
    def test_format_error_response(self):
        """Test formatting of error responses."""
        # Test basic error response
        error_json = self.reasoning_service.format_error_response(
            error_message="Test error message",
            error_type="TestError"
        )
        error_data = json.loads(error_json)
        
        self.assertIn("error", error_data)
        self.assertEqual(error_data["error"]["type"], "TestError")
        self.assertEqual(error_data["error"]["message"], "Test error message")
        self.assertIn("timestamp", error_data["error"])
    
    def test_recommendation_reproducibility(self):
        """Test that recommendations are reproducible with fixed random seed."""
        # Create two services with same seed
        service1 = RestaurantReasoningService(random_seed=42)
        service2 = RestaurantReasoningService(random_seed=42)
        
        # Get recommendations from both services
        result1 = service1.analyze_and_recommend(
            restaurant_data=self.sample_restaurant_data,
            ranking_method="sentiment_likes",
            candidate_count=3
        )
        
        result2 = service2.analyze_and_recommend(
            restaurant_data=self.sample_restaurant_data,
            ranking_method="sentiment_likes",
            candidate_count=3
        )
        
        # Recommendations should be identical with same seed
        self.assertEqual(result1.recommendation.id, result2.recommendation.id)
        self.assertEqual(len(result1.candidates), len(result2.candidates))
    
    def test_edge_case_single_restaurant(self):
        """Test recommendation with single valid restaurant."""
        single_restaurant = [{
            "id": "rest_001",
            "name": "Only Restaurant",
            "address": "123 Main St",
            "meal_type": ["lunch"],
            "sentiment": {"likes": 30, "dislikes": 5, "neutral": 10},
            "location_category": "urban",
            "district": "Central",
            "price_range": "$"
        }]
        
        result = self.reasoning_service.analyze_and_recommend(
            restaurant_data=single_restaurant,
            ranking_method="sentiment_likes"
        )
        
        self.assertEqual(len(result.candidates), 1)
        self.assertEqual(result.recommendation.id, "rest_001")
        self.assertEqual(result.recommendation, result.candidates[0])
    
    def test_large_candidate_count(self):
        """Test recommendation with candidate count larger than available restaurants."""
        result = self.reasoning_service.analyze_and_recommend(
            restaurant_data=self.sample_restaurant_data,
            ranking_method="sentiment_likes",
            candidate_count=100  # More than available restaurants
        )
        
        # Should return all available restaurants
        self.assertEqual(len(result.candidates), 5)
        self.assertIn(result.recommendation, result.candidates)


if __name__ == '__main__':
    unittest.main(verbosity=2)