"""
Unit tests for sentiment analysis service.

This module contains comprehensive test coverage for the SentimentAnalysisService
including sentiment score calculations, percentage calculations, ranking algorithms,
and edge case handling.
"""

import unittest
from unittest.mock import patch, MagicMock
import logging
from typing import List

# Import the modules to test
from services.sentiment_service import SentimentAnalysisService, SentimentScoreResult
from models.restaurant_models import Sentiment, Restaurant, SentimentAnalysis
from models.validation_models import ValidationResult, ValidationError, ValidationErrorType


class TestSentimentAnalysisService(unittest.TestCase):
    """Test cases for SentimentAnalysisService class."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.service = SentimentAnalysisService(minimum_responses=1)
        
        # Create test sentiment data
        self.valid_sentiment = Sentiment(likes=80, dislikes=15, neutral=5)
        self.zero_sentiment = Sentiment(likes=0, dislikes=0, neutral=0)
        self.negative_sentiment = Sentiment(likes=-5, dislikes=10, neutral=3)
        self.high_likes_sentiment = Sentiment(likes=95, dislikes=3, neutral=2)
        self.high_neutral_sentiment = Sentiment(likes=20, dislikes=10, neutral=70)
        
        # Create test restaurants
        self.test_restaurants = [
            Restaurant(
                id="rest1",
                name="High Likes Restaurant",
                address="123 Main St",
                meal_type=["Chinese"],
                sentiment=self.high_likes_sentiment,
                location_category="Urban",
                district="Central",
                price_range="$$"
            ),
            Restaurant(
                id="rest2",
                name="Balanced Restaurant",
                address="456 Oak Ave",
                meal_type=["Italian"],
                sentiment=self.valid_sentiment,
                location_category="Urban",
                district="Admiralty",
                price_range="$$$"
            ),
            Restaurant(
                id="rest3",
                name="High Neutral Restaurant",
                address="789 Pine Rd",
                meal_type=["Japanese"],
                sentiment=self.high_neutral_sentiment,
                location_category="Suburban",
                district="Causeway Bay",
                price_range="$$$$"
            )
        ]
    
    def test_calculate_sentiment_score_valid_data(self):
        """Test sentiment score calculation with valid data."""
        result = self.service.calculate_sentiment_score(self.valid_sentiment)
        
        self.assertTrue(result.is_valid)
        self.assertEqual(result.method, "sentiment_likes")
        self.assertEqual(result.total_responses, 100)
        self.assertEqual(result.score, 80.0)  # 80/100 * 100 = 80%
        self.assertIsNone(result.error_message)
    
    def test_calculate_sentiment_score_zero_responses(self):
        """Test sentiment score calculation with zero responses."""
        result = self.service.calculate_sentiment_score(self.zero_sentiment)
        
        self.assertFalse(result.is_valid)
        self.assertEqual(result.method, "sentiment_likes")
        self.assertEqual(result.total_responses, 0)
        self.assertEqual(result.score, 0.0)
        self.assertIn("Insufficient responses", result.error_message)
    
    def test_calculate_sentiment_score_negative_values(self):
        """Test sentiment score calculation with negative values."""
        result = self.service.calculate_sentiment_score(self.negative_sentiment)
        
        self.assertFalse(result.is_valid)
        self.assertEqual(result.score, 0.0)
        self.assertIn("Invalid sentiment data", result.error_message)
    
    def test_calculate_combined_score_valid_data(self):
        """Test combined sentiment score calculation with valid data."""
        result = self.service.calculate_combined_score(self.valid_sentiment)
        
        self.assertTrue(result.is_valid)
        self.assertEqual(result.method, "combined_sentiment")
        self.assertEqual(result.total_responses, 100)
        self.assertEqual(result.score, 85.0)  # (80+5)/100 * 100 = 85%
        self.assertIsNone(result.error_message)
    
    def test_calculate_combined_score_high_neutral(self):
        """Test combined score with high neutral sentiment."""
        result = self.service.calculate_combined_score(self.high_neutral_sentiment)
        
        self.assertTrue(result.is_valid)
        self.assertEqual(result.method, "combined_sentiment")
        self.assertEqual(result.total_responses, 100)
        self.assertEqual(result.score, 90.0)  # (20+70)/100 * 100 = 90%
    
    def test_calculate_combined_score_zero_responses(self):
        """Test combined score calculation with zero responses."""
        result = self.service.calculate_combined_score(self.zero_sentiment)
        
        self.assertFalse(result.is_valid)
        self.assertEqual(result.method, "combined_sentiment")
        self.assertEqual(result.total_responses, 0)
        self.assertEqual(result.score, 0.0)
        self.assertIn("Insufficient responses", result.error_message)
    
    def test_get_sentiment_percentages_valid_data(self):
        """Test sentiment percentage calculations with valid data."""
        percentages = self.service.get_sentiment_percentages(self.valid_sentiment)
        
        expected = {
            "likes_percentage": 80.0,
            "dislikes_percentage": 15.0,
            "neutral_percentage": 5.0,
            "combined_positive_percentage": 85.0,
            "total_responses": 100
        }
        
        self.assertEqual(percentages, expected)
    
    def test_get_sentiment_percentages_zero_responses(self):
        """Test sentiment percentage calculations with zero responses."""
        percentages = self.service.get_sentiment_percentages(self.zero_sentiment)
        
        expected = {
            "likes_percentage": 0.0,
            "dislikes_percentage": 0.0,
            "neutral_percentage": 0.0,
            "combined_positive_percentage": 0.0,
            "total_responses": 0
        }
        
        self.assertEqual(percentages, expected)
    
    def test_get_sentiment_percentages_rounding(self):
        """Test sentiment percentage calculations with rounding."""
        # Create sentiment with values that require rounding
        sentiment = Sentiment(likes=33, dislikes=33, neutral=34)  # Total: 100
        percentages = self.service.get_sentiment_percentages(sentiment)
        
        self.assertEqual(percentages["likes_percentage"], 33.0)
        self.assertEqual(percentages["dislikes_percentage"], 33.0)
        self.assertEqual(percentages["neutral_percentage"], 34.0)
        self.assertEqual(percentages["combined_positive_percentage"], 67.0)
    
    def test_rank_restaurants_by_sentiment_likes(self):
        """Test restaurant ranking by sentiment likes."""
        ranked = self.service.rank_restaurants_by_score(
            self.test_restaurants, 
            "sentiment_likes"
        )
        
        self.assertEqual(len(ranked), 3)
        
        # Check ranking order (highest likes first)
        self.assertEqual(ranked[0][0].name, "High Likes Restaurant")  # 95% likes
        self.assertEqual(ranked[1][0].name, "Balanced Restaurant")     # 80% likes
        self.assertEqual(ranked[2][0].name, "High Neutral Restaurant") # 20% likes
        
        # Check scores
        self.assertEqual(ranked[0][1].score, 95.0)
        self.assertEqual(ranked[1][1].score, 80.0)
        self.assertEqual(ranked[2][1].score, 20.0)
    
    def test_rank_restaurants_by_combined_sentiment(self):
        """Test restaurant ranking by combined sentiment."""
        ranked = self.service.rank_restaurants_by_score(
            self.test_restaurants, 
            "combined_sentiment"
        )
        
        self.assertEqual(len(ranked), 3)
        
        # Check ranking order (highest combined score first)
        self.assertEqual(ranked[0][0].name, "High Likes Restaurant")   # 97% combined
        self.assertEqual(ranked[1][0].name, "High Neutral Restaurant") # 90% combined
        self.assertEqual(ranked[2][0].name, "Balanced Restaurant")     # 85% combined
        
        # Check scores
        self.assertEqual(ranked[0][1].score, 97.0)  # (95+2)/100
        self.assertEqual(ranked[1][1].score, 90.0)  # (20+70)/100
        self.assertEqual(ranked[2][1].score, 85.0)  # (80+5)/100
    
    def test_rank_restaurants_empty_list(self):
        """Test restaurant ranking with empty list."""
        ranked = self.service.rank_restaurants_by_score([], "sentiment_likes")
        
        self.assertEqual(len(ranked), 0)
    
    def test_rank_restaurants_tie_breaking(self):
        """Test restaurant ranking with tied scores (tie-breaking by total responses)."""
        # Create restaurants with same likes percentage but different total responses
        restaurant1 = Restaurant(
            id="tie1",
            name="Tie Restaurant 1",
            address="Address 1",
            meal_type=["Food"],
            sentiment=Sentiment(likes=40, dislikes=10, neutral=0),  # 80%, 50 total
            location_category="Urban",
            district="District",
            price_range="$$"
        )
        
        restaurant2 = Restaurant(
            id="tie2",
            name="Tie Restaurant 2",
            address="Address 2",
            meal_type=["Food"],
            sentiment=Sentiment(likes=80, dislikes=20, neutral=0),  # 80%, 100 total
            location_category="Urban",
            district="District",
            price_range="$$"
        )
        
        ranked = self.service.rank_restaurants_by_score(
            [restaurant1, restaurant2], 
            "sentiment_likes"
        )
        
        # Restaurant with more total responses should rank higher in tie
        self.assertEqual(ranked[0][0].name, "Tie Restaurant 2")
        self.assertEqual(ranked[1][0].name, "Tie Restaurant 1")
        
        # Both should have same score
        self.assertEqual(ranked[0][1].score, 80.0)
        self.assertEqual(ranked[1][1].score, 80.0)
    
    def test_validate_sentiment_data_valid(self):
        """Test sentiment data validation with valid data."""
        result = self.service.validate_sentiment_data(self.valid_sentiment)
        
        self.assertTrue(result.is_valid)
        self.assertEqual(len(result.errors), 0)
        self.assertEqual(len(result.warnings), 0)
    
    def test_validate_sentiment_data_negative_values(self):
        """Test sentiment data validation with negative values."""
        result = self.service.validate_sentiment_data(self.negative_sentiment)
        
        self.assertFalse(result.is_valid)
        self.assertGreater(len(result.errors), 0)
        
        # Check that negative likes error is present
        error_messages = [error.message for error in result.errors]
        self.assertTrue(any("negative" in msg.lower() for msg in error_messages))
    
    def test_validate_sentiment_data_zero_responses_warning(self):
        """Test sentiment data validation with zero responses (should generate warning)."""
        result = self.service.validate_sentiment_data(self.zero_sentiment)
        
        self.assertTrue(result.is_valid)  # Zero responses is valid, just warned
        self.assertEqual(len(result.errors), 0)
        self.assertGreater(len(result.warnings), 0)
        self.assertIn("zero total responses", result.warnings[0])
    
    def test_validate_sentiment_data_large_values_warning(self):
        """Test sentiment data validation with unusually large values."""
        large_sentiment = Sentiment(likes=2000000, dislikes=1000000, neutral=500000)
        result = self.service.validate_sentiment_data(large_sentiment)
        
        self.assertTrue(result.is_valid)  # Large values are valid, just warned
        self.assertEqual(len(result.errors), 0)
        self.assertGreater(len(result.warnings), 0)
        self.assertIn("unusually large", result.warnings[0])
    
    def test_analyze_restaurant_list_valid_data(self):
        """Test comprehensive restaurant list analysis."""
        analysis = self.service.analyze_restaurant_list(
            self.test_restaurants, 
            "sentiment_likes"
        )
        
        self.assertEqual(analysis.restaurant_count, 3)
        self.assertEqual(analysis.ranking_method, "sentiment_likes")
        
        # Check averages (should be calculated correctly)
        expected_avg_likes = (95 + 80 + 20) / 3  # 65.0
        expected_avg_dislikes = (3 + 15 + 10) / 3  # 9.33
        expected_avg_neutral = (2 + 5 + 70) / 3  # 25.67
        
        self.assertAlmostEqual(analysis.average_likes, expected_avg_likes, places=2)
        self.assertAlmostEqual(analysis.average_dislikes, expected_avg_dislikes, places=2)
        self.assertAlmostEqual(analysis.average_neutral, expected_avg_neutral, places=2)
        
        # Check score range
        self.assertEqual(analysis.top_sentiment_score, 95.0)
        self.assertEqual(analysis.bottom_sentiment_score, 20.0)
    
    def test_analyze_restaurant_list_empty(self):
        """Test restaurant list analysis with empty list."""
        analysis = self.service.analyze_restaurant_list([], "sentiment_likes")
        
        self.assertEqual(analysis.restaurant_count, 0)
        self.assertEqual(analysis.average_likes, 0.0)
        self.assertEqual(analysis.average_dislikes, 0.0)
        self.assertEqual(analysis.average_neutral, 0.0)
        self.assertEqual(analysis.top_sentiment_score, 0.0)
        self.assertEqual(analysis.bottom_sentiment_score, 0.0)
    
    def test_analyze_restaurant_list_combined_method(self):
        """Test restaurant list analysis with combined sentiment method."""
        analysis = self.service.analyze_restaurant_list(
            self.test_restaurants, 
            "combined_sentiment"
        )
        
        self.assertEqual(analysis.restaurant_count, 3)
        self.assertEqual(analysis.ranking_method, "combined_sentiment")
        
        # Score range should be different for combined method
        self.assertEqual(analysis.top_sentiment_score, 97.0)  # High likes restaurant
        self.assertEqual(analysis.bottom_sentiment_score, 85.0)  # Balanced restaurant
    
    def test_minimum_responses_configuration(self):
        """Test service configuration with different minimum responses."""
        service_strict = SentimentAnalysisService(minimum_responses=10)
        
        # Sentiment with less than 10 responses should be invalid
        low_response_sentiment = Sentiment(likes=5, dislikes=2, neutral=1)  # 8 total
        result = service_strict.calculate_sentiment_score(low_response_sentiment)
        
        self.assertFalse(result.is_valid)
        self.assertIn("Insufficient responses", result.error_message)
    
    def test_error_handling_in_calculations(self):
        """Test error handling when calculations fail."""
        # Mock the sentiment object to raise an exception during percentage calculation
        mock_sentiment = MagicMock()
        mock_sentiment.likes = 10
        mock_sentiment.dislikes = 5
        mock_sentiment.neutral = 3
        mock_sentiment.total_responses.return_value = 18
        mock_sentiment.likes_percentage.side_effect = Exception("Test error")
        
        result = self.service.calculate_sentiment_score(mock_sentiment)
        
        self.assertFalse(result.is_valid)
        self.assertIn("Error calculating sentiment score", result.error_message)
    
    def test_error_handling_in_percentages(self):
        """Test error handling in percentage calculations."""
        # Mock sentiment to raise exception
        mock_sentiment = MagicMock()
        mock_sentiment.total_responses.side_effect = Exception("Test error")
        
        percentages = self.service.get_sentiment_percentages(mock_sentiment)
        
        # Should return zero percentages on error
        expected = {
            "likes_percentage": 0.0,
            "dislikes_percentage": 0.0,
            "neutral_percentage": 0.0,
            "combined_positive_percentage": 0.0,
            "total_responses": 0
        }
        
        self.assertEqual(percentages, expected)
    
    def test_logging_functionality(self):
        """Test that logging works correctly."""
        # Test that the service has a logger attribute
        self.assertTrue(hasattr(self.service, 'logger'))
        
        # Test successful calculation (should log debug message)
        with patch.object(self.service.logger, 'debug') as mock_debug:
            self.service.calculate_sentiment_score(self.valid_sentiment)
            mock_debug.assert_called()
        
        # Test error logging with invalid sentiment
        with patch.object(self.service.logger, 'error') as mock_error:
            mock_sentiment = MagicMock()
            mock_sentiment.likes = 10
            mock_sentiment.dislikes = 5
            mock_sentiment.neutral = 3
            mock_sentiment.total_responses.return_value = 18
            mock_sentiment.likes_percentage.side_effect = Exception("Test error")
            self.service.calculate_sentiment_score(mock_sentiment)
            mock_error.assert_called()
    
    def test_edge_case_single_response_type(self):
        """Test edge cases with only one type of response."""
        # Only likes
        likes_only = Sentiment(likes=100, dislikes=0, neutral=0)
        result = self.service.calculate_sentiment_score(likes_only)
        self.assertTrue(result.is_valid)
        self.assertEqual(result.score, 100.0)
        
        # Only dislikes
        dislikes_only = Sentiment(likes=0, dislikes=100, neutral=0)
        result = self.service.calculate_sentiment_score(dislikes_only)
        self.assertTrue(result.is_valid)
        self.assertEqual(result.score, 0.0)
        
        # Only neutral
        neutral_only = Sentiment(likes=0, dislikes=0, neutral=100)
        result = self.service.calculate_sentiment_score(neutral_only)
        self.assertTrue(result.is_valid)
        self.assertEqual(result.score, 0.0)
        
        # Combined score for neutral only
        result = self.service.calculate_combined_score(neutral_only)
        self.assertTrue(result.is_valid)
        self.assertEqual(result.score, 100.0)
    
    def test_precision_and_rounding(self):
        """Test precision and rounding in calculations."""
        # Create sentiment that results in repeating decimals
        sentiment = Sentiment(likes=1, dislikes=1, neutral=1)  # 33.333...% each
        
        percentages = self.service.get_sentiment_percentages(sentiment)
        
        # Check that values are properly rounded to 2 decimal places
        self.assertEqual(percentages["likes_percentage"], 33.33)
        self.assertEqual(percentages["dislikes_percentage"], 33.33)
        self.assertEqual(percentages["neutral_percentage"], 33.33)
        self.assertEqual(percentages["combined_positive_percentage"], 66.67)


class TestSentimentScoreResult(unittest.TestCase):
    """Test cases for SentimentScoreResult dataclass."""
    
    def test_sentiment_score_result_creation(self):
        """Test creation of SentimentScoreResult."""
        result = SentimentScoreResult(
            score=85.5,
            method="sentiment_likes",
            total_responses=100,
            is_valid=True
        )
        
        self.assertEqual(result.score, 85.5)
        self.assertEqual(result.method, "sentiment_likes")
        self.assertEqual(result.total_responses, 100)
        self.assertTrue(result.is_valid)
        self.assertIsNone(result.error_message)
    
    def test_sentiment_score_result_with_error(self):
        """Test creation of SentimentScoreResult with error."""
        result = SentimentScoreResult(
            score=0.0,
            method="combined_sentiment",
            total_responses=0,
            is_valid=False,
            error_message="Test error message"
        )
        
        self.assertEqual(result.score, 0.0)
        self.assertEqual(result.method, "combined_sentiment")
        self.assertEqual(result.total_responses, 0)
        self.assertFalse(result.is_valid)
        self.assertEqual(result.error_message, "Test error message")


if __name__ == '__main__':
    # Configure logging for tests
    logging.basicConfig(level=logging.DEBUG)
    
    # Run the tests
    unittest.main()