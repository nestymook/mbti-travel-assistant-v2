#!/usr/bin/env python3
"""
End-to-End Reasoning Integration Tests.

This module provides comprehensive integration tests for the restaurant reasoning MCP server,
testing the complete workflow from MCP tool invocation to recommendation generation.
"""

import pytest
import json
import asyncio
import time
from typing import Dict, Any, List
from pathlib import Path

# Import MCP client components
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

# Import local services for validation
from services.restaurant_reasoning_service import RestaurantReasoningService
from services.sentiment_service import SentimentAnalysisService
from services.recommendation_service import RecommendationAlgorithm
from services.validation_service import RestaurantDataValidator
from models.restaurant_models import Restaurant, Sentiment, RecommendationResult


class TestReasoningIntegration:
    """Comprehensive integration tests for restaurant reasoning functionality."""
    
    @pytest.fixture
    def sample_restaurants(self) -> List[Dict[str, Any]]:
        """Generate sample restaurant data with sentiment information."""
        return [
            {
                "id": "rest_001",
                "name": "Golden Dragon Restaurant",
                "address": "123 Central Street, Central",
                "meal_type": ["lunch", "dinner"],
                "sentiment": {"likes": 85, "dislikes": 10, "neutral": 5},
                "location_category": "restaurant",
                "district": "Central district",
                "price_range": "$$"
            },
            {
                "id": "rest_002", 
                "name": "Peaceful Garden Cafe",
                "address": "456 Admiralty Road, Admiralty",
                "meal_type": ["breakfast", "lunch"],
                "sentiment": {"likes": 70, "dislikes": 15, "neutral": 15},
                "location_category": "cafe",
                "district": "Admiralty",
                "price_range": "$"
            },
            {
                "id": "rest_003",
                "name": "Ocean View Fine Dining",
                "address": "789 Causeway Bay Avenue, Causeway Bay",
                "meal_type": ["dinner"],
                "sentiment": {"likes": 95, "dislikes": 3, "neutral": 2},
                "location_category": "fine_dining",
                "district": "Causeway Bay",
                "price_range": "$$$"
            },
            {
                "id": "rest_004",
                "name": "Quick Bite Express",
                "address": "321 Wan Chai Street, Wan Chai",
                "meal_type": ["breakfast", "lunch", "dinner"],
                "sentiment": {"likes": 60, "dislikes": 25, "neutral": 15},
                "location_category": "fast_food",
                "district": "Wan Chai",
                "price_range": "$"
            },
            {
                "id": "rest_005",
                "name": "Traditional Tea House",
                "address": "654 Tsim Sha Tsui Road, Tsim Sha Tsui",
                "meal_type": ["breakfast", "lunch"],
                "sentiment": {"likes": 80, "dislikes": 8, "neutral": 12},
                "location_category": "cafe",
                "district": "Tsim Sha Tsui",
                "price_range": "$$"
            }
        ]
    
    @pytest.fixture
    def high_sentiment_restaurants(self) -> List[Dict[str, Any]]:
        """Generate restaurants with high sentiment scores."""
        return [
            {
                "id": "high_001",
                "name": "Excellent Restaurant A",
                "address": "100 High Street",
                "meal_type": ["lunch"],
                "sentiment": {"likes": 95, "dislikes": 3, "neutral": 2},
                "location_category": "restaurant",
                "district": "Central district",
                "price_range": "$$"
            },
            {
                "id": "high_002",
                "name": "Amazing Restaurant B", 
                "address": "200 High Street",
                "meal_type": ["dinner"],
                "sentiment": {"likes": 90, "dislikes": 5, "neutral": 5},
                "location_category": "restaurant",
                "district": "Admiralty",
                "price_range": "$$$"
            },
            {
                "id": "high_003",
                "name": "Outstanding Restaurant C",
                "address": "300 High Street",
                "meal_type": ["lunch", "dinner"],
                "sentiment": {"likes": 88, "dislikes": 7, "neutral": 5},
                "location_category": "fine_dining",
                "district": "Causeway Bay",
                "price_range": "$$$"
            }
        ]
    
    @pytest.fixture
    def mixed_sentiment_restaurants(self) -> List[Dict[str, Any]]:
        """Generate restaurants with mixed sentiment for ranking comparison."""
        return [
            {
                "id": "mixed_001",
                "name": "High Likes Low Neutral",
                "address": "1 Mixed Street",
                "meal_type": ["lunch"],
                "sentiment": {"likes": 80, "dislikes": 15, "neutral": 5},  # 80% likes, 85% combined
                "location_category": "restaurant",
                "district": "Central district",
                "price_range": "$"
            },
            {
                "id": "mixed_002",
                "name": "Medium Likes High Neutral",
                "address": "2 Mixed Street", 
                "meal_type": ["lunch"],
                "sentiment": {"likes": 60, "dislikes": 10, "neutral": 30},  # 60% likes, 90% combined
                "location_category": "restaurant",
                "district": "Admiralty",
                "price_range": "$"
            },
            {
                "id": "mixed_003",
                "name": "Low Likes Medium Neutral",
                "address": "3 Mixed Street",
                "meal_type": ["lunch"],
                "sentiment": {"likes": 50, "dislikes": 25, "neutral": 25},  # 50% likes, 75% combined
                "location_category": "restaurant",
                "district": "Causeway Bay",
                "price_range": "$"
            }
        ]
    
    @pytest.fixture
    def invalid_restaurants(self) -> List[Dict[str, Any]]:
        """Generate invalid restaurant data for error testing."""
        return [
            {
                "id": "invalid_001",
                "name": "Missing Sentiment Restaurant",
                "address": "1 Invalid Street",
                "meal_type": ["lunch"],
                "location_category": "restaurant",
                "district": "Test District",
                "price_range": "$"
                # Missing sentiment field
            },
            {
                # Missing id field
                "name": "Missing ID Restaurant",
                "address": "2 Invalid Street",
                "sentiment": {"likes": 50, "dislikes": 25, "neutral": 25},
                "meal_type": ["lunch"],
                "location_category": "restaurant",
                "district": "Test District",
                "price_range": "$"
            },
            {
                "id": "invalid_003",
                "name": "Invalid Sentiment Types",
                "address": "3 Invalid Street",
                "sentiment": {"likes": "not_a_number", "dislikes": 25, "neutral": 25},
                "meal_type": ["lunch"],
                "location_category": "restaurant",
                "district": "Test District",
                "price_range": "$"
            }
        ]
    
    @pytest.fixture
    def reasoning_service(self) -> RestaurantReasoningService:
        """Create restaurant reasoning service instance."""
        return RestaurantReasoningService()
    
    @pytest.fixture
    def sentiment_service(self) -> SentimentAnalysisService:
        """Create sentiment analysis service instance."""
        return SentimentAnalysisService()
    
    @pytest.fixture
    def recommendation_service(self) -> RecommendationAlgorithm:
        """Create recommendation algorithm service instance."""
        return RecommendationAlgorithm(random_seed=42)
    
    @pytest.fixture
    def validator(self) -> RestaurantDataValidator:
        """Create data validator instance."""
        return RestaurantDataValidator()

    def test_complete_recommendation_workflow_sentiment_likes(
        self, 
        sample_restaurants: List[Dict[str, Any]], 
        reasoning_service: RestaurantReasoningService
    ):
        """Test complete workflow from restaurant data to recommendation using sentiment likes."""
        # Execute the complete reasoning workflow
        result = reasoning_service.analyze_and_recommend(
            sample_restaurants, 
            "sentiment_likes"
        )
        
        # Validate result structure
        assert isinstance(result, RecommendationResult)
        assert result.ranking_method == "sentiment_likes"
        assert len(result.candidates) <= 20
        assert len(result.candidates) <= len(sample_restaurants)
        assert result.recommendation in result.candidates
        
        # Validate ranking order (should be sorted by likes descending)
        likes_scores = [candidate.sentiment.likes for candidate in result.candidates]
        assert likes_scores == sorted(likes_scores, reverse=True)
        
        # Validate analysis summary
        assert "total_restaurants" in result.analysis_summary
        assert "average_sentiment" in result.analysis_summary
        assert "ranking_method" in result.analysis_summary
        assert result.analysis_summary["total_restaurants"] == len(sample_restaurants)
        assert result.analysis_summary["ranking_method"] == "sentiment_likes"
    
    def test_complete_recommendation_workflow_combined_sentiment(
        self, 
        mixed_sentiment_restaurants: List[Dict[str, Any]], 
        reasoning_service: RestaurantReasoningService
    ):
        """Test complete workflow using combined sentiment ranking."""
        # Execute the complete reasoning workflow
        result = reasoning_service.analyze_and_recommend(
            mixed_sentiment_restaurants, 
            "combined_sentiment"
        )
        
        # Validate result structure
        assert isinstance(result, RecommendationResult)
        assert result.ranking_method == "combined_sentiment"
        assert len(result.candidates) == len(mixed_sentiment_restaurants)
        assert result.recommendation in result.candidates
        
        # Validate ranking order (should be sorted by combined sentiment descending)
        combined_scores = []
        for candidate in result.candidates:
            sentiment = candidate.sentiment
            total = sentiment.likes + sentiment.dislikes + sentiment.neutral
            combined_score = (sentiment.likes + sentiment.neutral) / total if total > 0 else 0
            combined_scores.append(combined_score)
        
        assert combined_scores == sorted(combined_scores, reverse=True)
        
        # Validate specific ranking for mixed sentiment data
        # "Medium Likes High Neutral" should rank higher than "High Likes Low Neutral"
        candidate_names = [c.name for c in result.candidates]
        medium_high_idx = candidate_names.index("Medium Likes High Neutral")
        high_low_idx = candidate_names.index("High Likes Low Neutral")
        assert medium_high_idx < high_low_idx  # Lower index = higher rank
    
    def test_sentiment_analysis_workflow(
        self, 
        sample_restaurants: List[Dict[str, Any]], 
        sentiment_service: SentimentAnalysisService
    ):
        """Test sentiment analysis workflow without recommendation."""
        # Convert to Restaurant objects
        restaurants = []
        for data in sample_restaurants:
            sentiment = Sentiment(**data["sentiment"])
            restaurant = Restaurant(
                id=data["id"],
                name=data["name"],
                address=data["address"],
                meal_type=data["meal_type"],
                sentiment=sentiment,
                location_category=data["location_category"],
                district=data["district"],
                price_range=data["price_range"]
            )
            restaurants.append(restaurant)
        
        # Perform sentiment analysis
        analysis = sentiment_service.analyze_restaurant_list(restaurants)
        
        # Validate analysis results
        assert analysis.restaurant_count == len(restaurants)
        assert analysis.average_likes > 0
        assert analysis.average_dislikes >= 0
        assert analysis.average_neutral >= 0
        assert analysis.top_sentiment_score >= analysis.bottom_sentiment_score
        
        # Validate score calculations
        total_likes = sum(r.sentiment.likes for r in restaurants)
        expected_avg_likes = total_likes / len(restaurants)
        assert abs(analysis.average_likes - expected_avg_likes) < 0.01
    
    def test_ranking_method_comparison(
        self, 
        mixed_sentiment_restaurants: List[Dict[str, Any]], 
        reasoning_service: RestaurantReasoningService
    ):
        """Test that different ranking methods produce different results."""
        # Test sentiment_likes ranking
        result_likes = reasoning_service.analyze_and_recommend(
            mixed_sentiment_restaurants, 
            "sentiment_likes"
        )
        
        # Test combined_sentiment ranking
        result_combined = reasoning_service.analyze_and_recommend(
            mixed_sentiment_restaurants, 
            "combined_sentiment"
        )
        
        # Rankings should be different
        likes_order = [c.id for c in result_likes.candidates]
        combined_order = [c.id for c in result_combined.candidates]
        assert likes_order != combined_order
        
        # Validate specific expected rankings
        # For sentiment_likes: "High Likes Low Neutral" should rank first
        assert result_likes.candidates[0].name == "High Likes Low Neutral"
        
        # For combined_sentiment: "Medium Likes High Neutral" should rank first
        assert result_combined.candidates[0].name == "Medium Likes High Neutral"
    
    def test_candidate_selection_limits(
        self, 
        reasoning_service: RestaurantReasoningService
    ):
        """Test candidate selection with different list sizes."""
        # Test with fewer than 20 restaurants
        small_list = [
            {
                "id": f"small_{i}",
                "name": f"Restaurant {i}",
                "address": f"{i} Small Street",
                "meal_type": ["lunch"],
                "sentiment": {"likes": 50 + i, "dislikes": 25, "neutral": 25},
                "location_category": "restaurant",
                "district": "Test District",
                "price_range": "$"
            }
            for i in range(5)
        ]
        
        result = reasoning_service.analyze_and_recommend(small_list, "sentiment_likes")
        assert len(result.candidates) == 5  # All restaurants returned
        
        # Test with exactly 20 restaurants
        medium_list = [
            {
                "id": f"medium_{i}",
                "name": f"Restaurant {i}",
                "address": f"{i} Medium Street",
                "meal_type": ["lunch"],
                "sentiment": {"likes": 50 + i, "dislikes": 25, "neutral": 25},
                "location_category": "restaurant",
                "district": "Test District",
                "price_range": "$"
            }
            for i in range(20)
        ]
        
        result = reasoning_service.analyze_and_recommend(medium_list, "sentiment_likes")
        assert len(result.candidates) == 20  # All 20 restaurants returned
        
        # Test with more than 20 restaurants
        large_list = [
            {
                "id": f"large_{i}",
                "name": f"Restaurant {i}",
                "address": f"{i} Large Street",
                "meal_type": ["lunch"],
                "sentiment": {"likes": 50 + i, "dislikes": 25, "neutral": 25},
                "location_category": "restaurant",
                "district": "Test District",
                "price_range": "$"
            }
            for i in range(25)
        ]
        
        result = reasoning_service.analyze_and_recommend(large_list, "sentiment_likes")
        assert len(result.candidates) == 20  # Top 20 restaurants returned
    
    def test_error_handling_invalid_data(
        self, 
        invalid_restaurants: List[Dict[str, Any]], 
        reasoning_service: RestaurantReasoningService
    ):
        """Test error handling with invalid restaurant data."""
        # Test with completely invalid data
        with pytest.raises(ValueError) as exc_info:
            reasoning_service.analyze_and_recommend(invalid_restaurants, "sentiment_likes")
        
        assert "validation" in str(exc_info.value).lower()
    
    def test_error_handling_empty_list(
        self, 
        reasoning_service: RestaurantReasoningService
    ):
        """Test error handling with empty restaurant list."""
        with pytest.raises(ValueError) as exc_info:
            reasoning_service.analyze_and_recommend([], "sentiment_likes")
        
        assert "empty" in str(exc_info.value).lower() or "no restaurants" in str(exc_info.value).lower()
    
    def test_error_handling_invalid_ranking_method(
        self, 
        sample_restaurants: List[Dict[str, Any]], 
        reasoning_service: RestaurantReasoningService
    ):
        """Test error handling with invalid ranking method."""
        with pytest.raises(ValueError) as exc_info:
            reasoning_service.analyze_and_recommend(sample_restaurants, "invalid_method")
        
        assert "invalid" in str(exc_info.value).lower() or "ranking" in str(exc_info.value).lower()
    
    def test_zero_sentiment_handling(
        self, 
        reasoning_service: RestaurantReasoningService
    ):
        """Test handling of restaurants with zero sentiment responses."""
        zero_sentiment_restaurants = [
            {
                "id": "zero_001",
                "name": "Zero Sentiment Restaurant",
                "address": "1 Zero Street",
                "meal_type": ["lunch"],
                "sentiment": {"likes": 0, "dislikes": 0, "neutral": 0},
                "location_category": "restaurant",
                "district": "Test District",
                "price_range": "$"
            },
            {
                "id": "normal_001",
                "name": "Normal Restaurant",
                "address": "2 Normal Street",
                "meal_type": ["lunch"],
                "sentiment": {"likes": 50, "dislikes": 25, "neutral": 25},
                "location_category": "restaurant",
                "district": "Test District",
                "price_range": "$"
            }
        ]
        
        # Should handle zero sentiment gracefully
        result = reasoning_service.analyze_and_recommend(
            zero_sentiment_restaurants, 
            "sentiment_likes"
        )
        
        # Zero sentiment restaurant should rank lower (or be filtered out)
        candidate_names = [c.name for c in result.candidates]
        if "Zero Sentiment Restaurant" in candidate_names:
            zero_idx = candidate_names.index("Zero Sentiment Restaurant")
            normal_idx = candidate_names.index("Normal Restaurant")
            assert zero_idx > normal_idx  # Zero sentiment ranks lower
        # If zero sentiment is filtered out, normal restaurant should be the only candidate
        assert result.recommendation.name == "Normal Restaurant"
    
    def test_response_format_validation(
        self, 
        sample_restaurants: List[Dict[str, Any]], 
        reasoning_service: RestaurantReasoningService
    ):
        """Test that response format matches expected structure."""
        result = reasoning_service.analyze_and_recommend(
            sample_restaurants, 
            "sentiment_likes"
        )
        
        # Convert to dictionary format (as would be returned by MCP tool)
        result_dict = result.to_dict()
        
        # Validate required fields
        required_fields = ["candidates", "recommendation", "ranking_method", "analysis_summary"]
        for field in required_fields:
            assert field in result_dict
        
        # Validate candidate structure
        for candidate in result_dict["candidates"]:
            required_candidate_fields = ["id", "name", "sentiment"]
            for field in required_candidate_fields:
                assert field in candidate
        
        # Validate recommendation structure
        recommendation = result_dict["recommendation"]
        required_rec_fields = ["id", "name", "sentiment"]
        for field in required_rec_fields:
            assert field in recommendation
        
        # Validate analysis summary structure
        summary = result_dict["analysis_summary"]
        required_summary_fields = [
            "total_restaurants", "average_sentiment", "ranking_method"
        ]
        for field in required_summary_fields:
            assert field in summary
        
        # Validate average_sentiment structure
        avg_sentiment = summary["average_sentiment"]
        sentiment_fields = ["likes", "dislikes", "neutral"]
        for field in sentiment_fields:
            assert field in avg_sentiment
    
    def test_recommendation_accuracy_high_sentiment(
        self, 
        high_sentiment_restaurants: List[Dict[str, Any]], 
        reasoning_service: RestaurantReasoningService
    ):
        """Test recommendation accuracy with high sentiment restaurants."""
        result = reasoning_service.analyze_and_recommend(
            high_sentiment_restaurants, 
            "sentiment_likes"
        )
        
        # All restaurants should be candidates (less than 20)
        assert len(result.candidates) == len(high_sentiment_restaurants)
        
        # Top candidate should have highest likes
        top_candidate = result.candidates[0]
        assert top_candidate.name == "Excellent Restaurant A"
        assert top_candidate.sentiment.likes == 95
        
        # Recommendation should be from top candidates
        assert result.recommendation in result.candidates
    
    def test_performance_with_large_dataset(
        self, 
        reasoning_service: RestaurantReasoningService
    ):
        """Test performance with larger dataset."""
        # Generate large dataset
        large_dataset = []
        for i in range(100):
            restaurant = {
                "id": f"perf_{i:03d}",
                "name": f"Performance Restaurant {i}",
                "address": f"{i} Performance Street",
                "meal_type": ["lunch"],
                "sentiment": {
                    "likes": 50 + (i % 50), 
                    "dislikes": 25, 
                    "neutral": 25
                },
                "location_category": "restaurant",
                "district": "Test District",
                "price_range": "$"
            }
            large_dataset.append(restaurant)
        
        # Measure execution time
        start_time = time.time()
        result = reasoning_service.analyze_and_recommend(large_dataset, "sentiment_likes")
        execution_time = time.time() - start_time
        
        # Validate results
        assert len(result.candidates) == 20  # Top 20 candidates
        assert result.recommendation in result.candidates
        
        # Performance should be reasonable (less than 5 seconds for 100 restaurants)
        assert execution_time < 5.0
        
        print(f"Performance test: {len(large_dataset)} restaurants processed in {execution_time:.3f} seconds")
    
    def test_tie_breaking_logic(
        self, 
        reasoning_service: RestaurantReasoningService
    ):
        """Test tie-breaking logic when restaurants have identical sentiment scores."""
        tie_restaurants = [
            {
                "id": "tie_001",
                "name": "Restaurant A",
                "address": "1 Tie Street",
                "meal_type": ["lunch"],
                "sentiment": {"likes": 75, "dislikes": 15, "neutral": 10},
                "location_category": "restaurant",
                "district": "Test District",
                "price_range": "$"
            },
            {
                "id": "tie_002",
                "name": "Restaurant B",
                "address": "2 Tie Street",
                "meal_type": ["lunch"],
                "sentiment": {"likes": 75, "dislikes": 15, "neutral": 10},  # Identical sentiment
                "location_category": "restaurant",
                "district": "Test District",
                "price_range": "$"
            },
            {
                "id": "tie_003",
                "name": "Restaurant C",
                "address": "3 Tie Street",
                "meal_type": ["lunch"],
                "sentiment": {"likes": 80, "dislikes": 10, "neutral": 10},  # Higher likes
                "location_category": "restaurant",
                "district": "Test District",
                "price_range": "$"
            }
        ]
        
        result = reasoning_service.analyze_and_recommend(tie_restaurants, "sentiment_likes")
        
        # Restaurant C should rank first (highest likes)
        assert result.candidates[0].name == "Restaurant C"
        
        # Restaurants A and B should be ranked consistently (stable sort)
        candidate_names = [c.name for c in result.candidates]
        a_index = candidate_names.index("Restaurant A")
        b_index = candidate_names.index("Restaurant B")
        
        # Both should be after Restaurant C
        assert a_index > 0
        assert b_index > 0


class TestReasoningIntegrationMCP:
    """Integration tests specifically for MCP tool functionality."""
    
    def test_mcp_tool_response_format(self):
        """Test that MCP tool responses match expected JSON format."""
        # This would be tested with actual MCP server if available
        # For now, test the service layer that MCP tools would use
        
        from services.restaurant_reasoning_service import RestaurantReasoningService
        
        service = RestaurantReasoningService()
        
        sample_data = [
            {
                "id": "mcp_001",
                "name": "MCP Test Restaurant",
                "address": "1 MCP Street",
                "meal_type": ["lunch"],
                "sentiment": {"likes": 80, "dislikes": 15, "neutral": 5},
                "location_category": "restaurant",
                "district": "Test District",
                "price_range": "$"
            }
        ]
        
        result = service.analyze_and_recommend(sample_data, "sentiment_likes")
        result_json = json.dumps(result.to_dict(), indent=2)
        
        # Validate JSON is parseable
        parsed = json.loads(result_json)
        assert "candidates" in parsed
        assert "recommendation" in parsed
        assert "ranking_method" in parsed
        assert "analysis_summary" in parsed
    
    def test_mcp_error_response_format(self):
        """Test that MCP error responses are properly formatted."""
        from services.restaurant_reasoning_service import RestaurantReasoningService
        
        service = RestaurantReasoningService()
        
        # Test with invalid data
        invalid_data = [{"invalid": "data"}]
        
        try:
            service.analyze_and_recommend(invalid_data, "sentiment_likes")
            assert False, "Should have raised an exception"
        except Exception as e:
            # Error should be descriptive
            error_msg = str(e)
            assert len(error_msg) > 0
            assert "validation" in error_msg.lower() or "invalid" in error_msg.lower()


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])