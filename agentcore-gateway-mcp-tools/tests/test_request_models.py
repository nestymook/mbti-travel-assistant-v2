"""
Unit tests for request models.

This module contains comprehensive tests for all request models including
validation rules, field constraints, and error handling.
"""

import pytest
from pydantic import ValidationError
from typing import List, Dict, Any

from models.request_models import (
    MealType,
    RankingMethod,
    DistrictSearchRequest,
    MealTypeSearchRequest,
    CombinedSearchRequest,
    RestaurantData,
    RestaurantRecommendationRequest,
    SentimentAnalysisRequest
)


class TestMealTypeEnum:
    """Test MealType enum."""
    
    def test_valid_meal_types(self):
        """Test valid meal type values."""
        assert MealType.BREAKFAST == "breakfast"
        assert MealType.LUNCH == "lunch"
        assert MealType.DINNER == "dinner"
    
    def test_meal_type_list(self):
        """Test getting list of all meal types."""
        meal_types = list(MealType)
        assert len(meal_types) == 3
        assert MealType.BREAKFAST in meal_types
        assert MealType.LUNCH in meal_types
        assert MealType.DINNER in meal_types


class TestRankingMethodEnum:
    """Test RankingMethod enum."""
    
    def test_valid_ranking_methods(self):
        """Test valid ranking method values."""
        assert RankingMethod.SENTIMENT_LIKES == "sentiment_likes"
        assert RankingMethod.COMBINED_SENTIMENT == "combined_sentiment"


class TestDistrictSearchRequest:
    """Test DistrictSearchRequest model."""
    
    def test_valid_district_search_request(self):
        """Test valid district search request."""
        request = DistrictSearchRequest(
            districts=["Central district", "Admiralty"]
        )
        assert request.districts == ["Central district", "Admiralty"]
    
    def test_single_district(self):
        """Test request with single district."""
        request = DistrictSearchRequest(districts=["Central district"])
        assert request.districts == ["Central district"]
    
    def test_empty_districts_list(self):
        """Test validation error for empty districts list."""
        with pytest.raises(ValidationError) as exc_info:
            DistrictSearchRequest(districts=[])
        
        errors = exc_info.value.errors()
        assert len(errors) > 0
        assert any("List should have at least 1 item" in str(error) for error in errors)
    
    def test_missing_districts_field(self):
        """Test validation error for missing districts field."""
        with pytest.raises(ValidationError) as exc_info:
            DistrictSearchRequest()
        
        errors = exc_info.value.errors()
        assert len(errors) > 0
        assert any(error["type"] == "missing" for error in errors)
    
    def test_districts_with_empty_strings(self):
        """Test handling of empty strings in districts list."""
        request = DistrictSearchRequest(
            districts=["Central district", "", "  ", "Admiralty"]
        )
        # Should filter out empty strings and whitespace-only strings
        assert request.districts == ["Central district", "Admiralty"]
    
    def test_duplicate_districts_removed(self):
        """Test that duplicate districts are removed."""
        request = DistrictSearchRequest(
            districts=["Central district", "Admiralty", "Central district"]
        )
        assert request.districts == ["Central district", "Admiralty"]
    
    def test_districts_whitespace_trimmed(self):
        """Test that district names are trimmed of whitespace."""
        request = DistrictSearchRequest(
            districts=[" Central district ", "  Admiralty  "]
        )
        assert request.districts == ["Central district", "Admiralty"]
    
    def test_too_many_districts(self):
        """Test validation error for too many districts."""
        districts = [f"District {i}" for i in range(25)]  # More than max_items=20
        with pytest.raises(ValidationError) as exc_info:
            DistrictSearchRequest(districts=districts)
        
        errors = exc_info.value.errors()
        assert len(errors) > 0
        assert any("List should have at most 20 items" in str(error) for error in errors)
    
    def test_all_empty_districts(self):
        """Test validation error when all districts are empty."""
        with pytest.raises(ValidationError) as exc_info:
            DistrictSearchRequest(districts=["", "  ", "\t"])
        
        errors = exc_info.value.errors()
        assert len(errors) > 0
        assert any("At least one valid district name is required" in str(error) for error in errors)


class TestMealTypeSearchRequest:
    """Test MealTypeSearchRequest model."""
    
    def test_valid_meal_type_search_request(self):
        """Test valid meal type search request."""
        request = MealTypeSearchRequest(
            meal_types=[MealType.BREAKFAST, MealType.LUNCH]
        )
        assert request.meal_types == [MealType.BREAKFAST, MealType.LUNCH]
    
    def test_single_meal_type(self):
        """Test request with single meal type."""
        request = MealTypeSearchRequest(meal_types=[MealType.DINNER])
        assert request.meal_types == [MealType.DINNER]
    
    def test_all_meal_types(self):
        """Test request with all meal types."""
        request = MealTypeSearchRequest(
            meal_types=[MealType.BREAKFAST, MealType.LUNCH, MealType.DINNER]
        )
        assert len(request.meal_types) == 3
    
    def test_empty_meal_types_list(self):
        """Test validation error for empty meal types list."""
        with pytest.raises(ValidationError) as exc_info:
            MealTypeSearchRequest(meal_types=[])
        
        errors = exc_info.value.errors()
        assert len(errors) > 0
        assert any("List should have at least 1 item" in str(error) for error in errors)
    
    def test_missing_meal_types_field(self):
        """Test validation error for missing meal types field."""
        with pytest.raises(ValidationError) as exc_info:
            MealTypeSearchRequest()
        
        errors = exc_info.value.errors()
        assert len(errors) > 0
        assert any(error["type"] == "missing" for error in errors)
    
    def test_duplicate_meal_types_removed(self):
        """Test that duplicate meal types are removed."""
        request = MealTypeSearchRequest(
            meal_types=[MealType.BREAKFAST, MealType.LUNCH, MealType.BREAKFAST]
        )
        assert request.meal_types == [MealType.BREAKFAST, MealType.LUNCH]
    
    def test_invalid_meal_type(self):
        """Test validation error for invalid meal type."""
        with pytest.raises(ValidationError) as exc_info:
            MealTypeSearchRequest(meal_types=["invalid_meal_type"])
        
        errors = exc_info.value.errors()
        assert len(errors) > 0
        assert any("Input should be 'breakfast', 'lunch' or 'dinner'" in str(error) for error in errors)
    
    def test_too_many_meal_types(self):
        """Test validation error for too many meal types."""
        # Since there are only 3 valid meal types, this test uses duplicates
        with pytest.raises(ValidationError) as exc_info:
            MealTypeSearchRequest(meal_types=["breakfast", "lunch", "dinner", "brunch"])
        
        errors = exc_info.value.errors()
        assert len(errors) > 0


class TestCombinedSearchRequest:
    """Test CombinedSearchRequest model."""
    
    def test_valid_combined_search_request(self):
        """Test valid combined search request."""
        request = CombinedSearchRequest(
            districts=["Central district"],
            meal_types=[MealType.LUNCH]
        )
        assert request.districts == ["Central district"]
        assert request.meal_types == [MealType.LUNCH]
    
    def test_districts_only(self):
        """Test request with only districts."""
        request = CombinedSearchRequest(districts=["Central district", "Admiralty"])
        assert request.districts == ["Central district", "Admiralty"]
        assert request.meal_types is None
    
    def test_meal_types_only(self):
        """Test request with only meal types."""
        request = CombinedSearchRequest(meal_types=[MealType.BREAKFAST, MealType.DINNER])
        assert request.districts is None
        assert request.meal_types == [MealType.BREAKFAST, MealType.DINNER]
    
    def test_both_none_validation_error(self):
        """Test validation error when both districts and meal_types are None."""
        with pytest.raises(ValidationError) as exc_info:
            CombinedSearchRequest()
        
        errors = exc_info.value.errors()
        assert len(errors) > 0
        assert any("At least one of 'districts' or 'meal_types' must be provided" in str(error) for error in errors)
    
    def test_both_empty_lists_validation_error(self):
        """Test validation error when both districts and meal_types are empty lists."""
        with pytest.raises(ValidationError) as exc_info:
            CombinedSearchRequest(districts=[], meal_types=[])
        
        errors = exc_info.value.errors()
        assert len(errors) > 0
    
    def test_districts_validation_applied(self):
        """Test that district validation rules are applied."""
        request = CombinedSearchRequest(
            districts=[" Central district ", "Admiralty", "Central district"],
            meal_types=[MealType.LUNCH]
        )
        # Should trim whitespace and remove duplicates
        assert request.districts == ["Central district", "Admiralty"]
    
    def test_meal_types_validation_applied(self):
        """Test that meal type validation rules are applied."""
        request = CombinedSearchRequest(
            districts=["Central district"],
            meal_types=[MealType.BREAKFAST, MealType.LUNCH, MealType.BREAKFAST]
        )
        # Should remove duplicates
        assert request.meal_types == [MealType.BREAKFAST, MealType.LUNCH]


class TestRestaurantData:
    """Test RestaurantData model."""
    
    def test_valid_restaurant_data(self):
        """Test valid restaurant data."""
        data = RestaurantData(
            id="rest_001",
            name="Great Restaurant",
            sentiment={"likes": 85, "dislikes": 10, "neutral": 5},
            address="123 Main St",
            district="Central district"
        )
        assert data.id == "rest_001"
        assert data.name == "Great Restaurant"
        assert data.sentiment == {"likes": 85, "dislikes": 10, "neutral": 5}
    
    def test_minimal_restaurant_data(self):
        """Test restaurant data with only required fields."""
        data = RestaurantData(
            id="rest_001",
            name="Restaurant",
            sentiment={"likes": 50, "dislikes": 20, "neutral": 30}
        )
        assert data.id == "rest_001"
        assert data.name == "Restaurant"
        assert data.address is None
        assert data.district is None
    
    def test_missing_required_fields(self):
        """Test validation error for missing required fields."""
        with pytest.raises(ValidationError) as exc_info:
            RestaurantData(sentiment={"likes": 50, "dislikes": 20, "neutral": 30})
        
        errors = exc_info.value.errors()
        assert len(errors) >= 2  # Missing id and name
        missing_fields = [error["loc"][0] for error in errors if error["type"] == "missing"]
        assert "id" in missing_fields
        assert "name" in missing_fields
    
    def test_invalid_sentiment_structure(self):
        """Test validation error for invalid sentiment structure."""
        with pytest.raises(ValidationError) as exc_info:
            RestaurantData(
                id="rest_001",
                name="Restaurant",
                sentiment={"likes": 50, "dislikes": 20}  # Missing 'neutral'
            )
        
        errors = exc_info.value.errors()
        assert len(errors) > 0
        assert any("Sentiment missing required fields" in str(error) for error in errors)
    
    def test_negative_sentiment_values(self):
        """Test validation error for negative sentiment values."""
        with pytest.raises(ValidationError) as exc_info:
            RestaurantData(
                id="rest_001",
                name="Restaurant",
                sentiment={"likes": -5, "dislikes": 20, "neutral": 30}
            )
        
        errors = exc_info.value.errors()
        assert len(errors) > 0
        assert any("must be a non-negative integer" in str(error) for error in errors)
    
    def test_non_integer_sentiment_values(self):
        """Test validation error for non-integer sentiment values."""
        with pytest.raises(ValidationError) as exc_info:
            RestaurantData(
                id="rest_001",
                name="Restaurant",
                sentiment={"likes": "fifty", "dislikes": 20, "neutral": 30}
            )
        
        errors = exc_info.value.errors()
        assert len(errors) > 0
        assert any("Input should be a valid integer" in str(error) for error in errors)
    
    def test_non_dict_sentiment(self):
        """Test validation error for non-dictionary sentiment."""
        with pytest.raises(ValidationError) as exc_info:
            RestaurantData(
                id="rest_001",
                name="Restaurant",
                sentiment="invalid"
            )
        
        errors = exc_info.value.errors()
        assert len(errors) > 0
        assert any("Input should be a valid dictionary" in str(error) for error in errors)


class TestRestaurantRecommendationRequest:
    """Test RestaurantRecommendationRequest model."""
    
    def test_valid_recommendation_request(self):
        """Test valid recommendation request."""
        restaurants = [
            RestaurantData(
                id="rest_001",
                name="Restaurant A",
                sentiment={"likes": 85, "dislikes": 10, "neutral": 5}
            ),
            RestaurantData(
                id="rest_002",
                name="Restaurant B",
                sentiment={"likes": 70, "dislikes": 20, "neutral": 10}
            )
        ]
        
        request = RestaurantRecommendationRequest(
            restaurants=restaurants,
            ranking_method=RankingMethod.SENTIMENT_LIKES
        )
        
        assert len(request.restaurants) == 2
        assert request.ranking_method == RankingMethod.SENTIMENT_LIKES
    
    def test_default_ranking_method(self):
        """Test default ranking method."""
        restaurants = [
            RestaurantData(
                id="rest_001",
                name="Restaurant A",
                sentiment={"likes": 85, "dislikes": 10, "neutral": 5}
            )
        ]
        
        request = RestaurantRecommendationRequest(restaurants=restaurants)
        assert request.ranking_method == RankingMethod.SENTIMENT_LIKES
    
    def test_empty_restaurants_list(self):
        """Test validation error for empty restaurants list."""
        with pytest.raises(ValidationError) as exc_info:
            RestaurantRecommendationRequest(restaurants=[])
        
        errors = exc_info.value.errors()
        assert len(errors) > 0
        assert any("List should have at least 1 item" in str(error) for error in errors)
    
    def test_duplicate_restaurant_ids(self):
        """Test validation error for duplicate restaurant IDs."""
        restaurants = [
            RestaurantData(
                id="rest_001",
                name="Restaurant A",
                sentiment={"likes": 85, "dislikes": 10, "neutral": 5}
            ),
            RestaurantData(
                id="rest_001",  # Duplicate ID
                name="Restaurant B",
                sentiment={"likes": 70, "dislikes": 20, "neutral": 10}
            )
        ]
        
        with pytest.raises(ValidationError) as exc_info:
            RestaurantRecommendationRequest(restaurants=restaurants)
        
        errors = exc_info.value.errors()
        assert len(errors) > 0
        assert any("Restaurant IDs must be unique" in str(error) for error in errors)
    
    def test_too_many_restaurants(self):
        """Test validation error for too many restaurants."""
        restaurants = [
            RestaurantData(
                id=f"rest_{i:03d}",
                name=f"Restaurant {i}",
                sentiment={"likes": 50, "dislikes": 25, "neutral": 25}
            )
            for i in range(1001)  # More than max_items=1000
        ]
        
        with pytest.raises(ValidationError) as exc_info:
            RestaurantRecommendationRequest(restaurants=restaurants)
        
        errors = exc_info.value.errors()
        assert len(errors) > 0
        assert any("List should have at most 1000 items" in str(error) for error in errors)
    
    def test_invalid_ranking_method(self):
        """Test validation error for invalid ranking method."""
        restaurants = [
            RestaurantData(
                id="rest_001",
                name="Restaurant A",
                sentiment={"likes": 85, "dislikes": 10, "neutral": 5}
            )
        ]
        
        with pytest.raises(ValidationError) as exc_info:
            RestaurantRecommendationRequest(
                restaurants=restaurants,
                ranking_method="invalid_method"
            )
        
        errors = exc_info.value.errors()
        assert len(errors) > 0
        assert any("Input should be 'sentiment_likes' or 'combined_sentiment'" in str(error) for error in errors)


class TestSentimentAnalysisRequest:
    """Test SentimentAnalysisRequest model."""
    
    def test_valid_sentiment_analysis_request(self):
        """Test valid sentiment analysis request."""
        restaurants = [
            RestaurantData(
                id="rest_001",
                name="Restaurant A",
                sentiment={"likes": 85, "dislikes": 10, "neutral": 5}
            ),
            RestaurantData(
                id="rest_002",
                name="Restaurant B",
                sentiment={"likes": 70, "dislikes": 20, "neutral": 10}
            )
        ]
        
        request = SentimentAnalysisRequest(restaurants=restaurants)
        assert len(request.restaurants) == 2
    
    def test_single_restaurant(self):
        """Test request with single restaurant."""
        restaurants = [
            RestaurantData(
                id="rest_001",
                name="Restaurant A",
                sentiment={"likes": 85, "dislikes": 10, "neutral": 5}
            )
        ]
        
        request = SentimentAnalysisRequest(restaurants=restaurants)
        assert len(request.restaurants) == 1
    
    def test_empty_restaurants_list(self):
        """Test validation error for empty restaurants list."""
        with pytest.raises(ValidationError) as exc_info:
            SentimentAnalysisRequest(restaurants=[])
        
        errors = exc_info.value.errors()
        assert len(errors) > 0
        assert any("List should have at least 1 item" in str(error) for error in errors)
    
    def test_duplicate_restaurant_ids(self):
        """Test validation error for duplicate restaurant IDs."""
        restaurants = [
            RestaurantData(
                id="rest_001",
                name="Restaurant A",
                sentiment={"likes": 85, "dislikes": 10, "neutral": 5}
            ),
            RestaurantData(
                id="rest_001",  # Duplicate ID
                name="Restaurant B",
                sentiment={"likes": 70, "dislikes": 20, "neutral": 10}
            )
        ]
        
        with pytest.raises(ValidationError) as exc_info:
            SentimentAnalysisRequest(restaurants=restaurants)
        
        errors = exc_info.value.errors()
        assert len(errors) > 0
        assert any("Restaurant IDs must be unique" in str(error) for error in errors)
    
    def test_missing_restaurants_field(self):
        """Test validation error for missing restaurants field."""
        with pytest.raises(ValidationError) as exc_info:
            SentimentAnalysisRequest()
        
        errors = exc_info.value.errors()
        assert len(errors) > 0
        assert any(error["type"] == "missing" for error in errors)


# Integration tests for model serialization
class TestModelSerialization:
    """Test model serialization and deserialization."""
    
    def test_district_search_request_serialization(self):
        """Test DistrictSearchRequest serialization."""
        request = DistrictSearchRequest(districts=["Central district", "Admiralty"])
        
        # Test dict conversion
        request_dict = request.dict()
        assert request_dict["districts"] == ["Central district", "Admiralty"]
        
        # Test JSON conversion
        request_json = request.json()
        assert "Central district" in request_json
        assert "Admiralty" in request_json
    
    def test_restaurant_data_serialization(self):
        """Test RestaurantData serialization."""
        data = RestaurantData(
            id="rest_001",
            name="Great Restaurant",
            sentiment={"likes": 85, "dislikes": 10, "neutral": 5},
            address="123 Main St",
            district="Central district",
            meal_type=["lunch", "dinner"],
            price_range="$$"
        )
        
        # Test dict conversion
        data_dict = data.dict()
        assert data_dict["id"] == "rest_001"
        assert data_dict["sentiment"]["likes"] == 85
        
        # Test JSON conversion
        data_json = data.json()
        assert "rest_001" in data_json
        assert "Great Restaurant" in data_json
    
    def test_model_from_dict(self):
        """Test creating models from dictionaries."""
        request_dict = {
            "districts": ["Central district", "Admiralty"]
        }
        
        request = DistrictSearchRequest(**request_dict)
        assert request.districts == ["Central district", "Admiralty"]