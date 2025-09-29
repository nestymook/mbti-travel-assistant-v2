"""
Test suite for Restaurant MCP Client Integration

This module tests the restaurant MCP client integration functionality
including meal-specific searches, recommendations, error handling, and fallback strategies.
"""

import pytest
import asyncio
import sys
import os
from unittest.mock import AsyncMock, MagicMock, patch
from typing import List, Dict, Any

# Add the parent directory to the path so we can import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock the performance monitor to avoid psutil dependency
with patch.dict('sys.modules', {'psutil': MagicMock()}):
    from services.mcp_client_manager import (
        MCPClientManager,
        MCPConnectionError,
        MCPToolCallError,
        MCPCircuitBreakerOpenError
    )
    from models.restaurant_models import Restaurant, Sentiment, OperatingHours, RestaurantMetadata


@pytest.fixture
def mock_restaurant():
    """Create a mock restaurant for testing."""
    return Restaurant(
        id="test_restaurant_001",
        name="Test Restaurant",
        address="123 Test Street, Test District",
        meal_type=["breakfast", "lunch"],
        sentiment=Sentiment(likes=85, dislikes=10, neutral=5),
        location_category="Restaurant",
        district="Test District",
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


@pytest.fixture
def mock_restaurants_list(mock_restaurant):
    """Create a list of mock restaurants for testing."""
    restaurants = []
    for i in range(5):
        restaurant = Restaurant(
            id=f"test_restaurant_{i:03d}",
            name=f"Test Restaurant {i}",
            address=f"{i} Test Street, Test District",
            meal_type=["breakfast", "lunch", "dinner"],
            sentiment=Sentiment(likes=80 + i, dislikes=10, neutral=5),
            location_category="Restaurant",
            district="Test District",
            price_range="$$",
            operating_hours=OperatingHours(
                mon_fri=["07:00 - 22:00"],
                sat_sun=["08:00 - 23:00"],
                public_holiday=["09:00 - 21:00"]
            ),
            metadata=RestaurantMetadata(
                data_quality="high",
                version="1.0",
                quality_score=90 + i
            )
        )
        restaurants.append(restaurant)
    return restaurants


@pytest.fixture
def mcp_client_manager():
    """Create MCP client manager for testing."""
    with patch('services.mcp_client_manager.settings') as mock_settings:
        mock_settings.mcp_client.search_mcp_endpoint = "http://test-search-mcp"
        mock_settings.mcp_client.reasoning_mcp_endpoint = "http://test-reasoning-mcp"
        mock_settings.mcp_client.mcp_connection_timeout = 30
        mock_settings.mcp_client.mcp_retry_attempts = 3
        
        return MCPClientManager()


class TestRestaurantMCPClientIntegration:
    """Test restaurant MCP client integration functionality."""
    
    @pytest.mark.asyncio
    async def test_search_breakfast_restaurants(self, mcp_client_manager, mock_restaurants_list):
        """Test breakfast restaurant search functionality."""
        # Mock the search_restaurants method
        with patch.object(mcp_client_manager, 'search_restaurants', new_callable=AsyncMock) as mock_search:
            mock_search.return_value = mock_restaurants_list
            
            # Test breakfast search
            result = await mcp_client_manager.search_breakfast_restaurants("Central district")
            
            # Verify the call
            mock_search.assert_called_once_with(district="Central district", meal_type="breakfast")
            assert len(result) == 5
            assert all(isinstance(r, Restaurant) for r in result)
    
    @pytest.mark.asyncio
    async def test_search_breakfast_restaurants_with_used_ids(self, mcp_client_manager, mock_restaurants_list):
        """Test breakfast restaurant search with used restaurant IDs filtering."""
        # Mock the search_restaurants method
        with patch.object(mcp_client_manager, 'search_restaurants', new_callable=AsyncMock) as mock_search:
            mock_search.return_value = mock_restaurants_list
            
            # Test with used restaurant IDs
            used_ids = {"test_restaurant_001", "test_restaurant_002"}
            result = await mcp_client_manager.search_breakfast_restaurants(
                "Central district", 
                used_restaurant_ids=used_ids
            )
            
            # Verify filtering
            assert len(result) == 3  # 5 - 2 used
            assert all(r.id not in used_ids for r in result)
    
    @pytest.mark.asyncio
    async def test_search_lunch_restaurants_multiple_districts(self, mcp_client_manager, mock_restaurants_list):
        """Test lunch restaurant search across multiple districts."""
        # Mock the search_restaurants method
        with patch.object(mcp_client_manager, 'search_restaurants', new_callable=AsyncMock) as mock_search:
            mock_search.return_value = mock_restaurants_list
            
            # Test lunch search in multiple districts
            districts = ["Central district", "Admiralty"]
            result = await mcp_client_manager.search_lunch_restaurants(districts)
            
            # Verify calls for each district
            assert mock_search.call_count == 2
            mock_search.assert_any_call(district="Central district", meal_type="lunch")
            mock_search.assert_any_call(district="Admiralty", meal_type="lunch")
            
            # Should have unique restaurants (duplicates removed)
            assert len(result) == 5
    
    @pytest.mark.asyncio
    async def test_search_dinner_restaurants_with_error_handling(self, mcp_client_manager, mock_restaurants_list):
        """Test dinner restaurant search with error handling."""
        # Mock the search_restaurants method to fail for first district
        with patch.object(mcp_client_manager, 'search_restaurants', new_callable=AsyncMock) as mock_search:
            def side_effect(district=None, meal_type=None):
                if district == "Failing District":
                    raise MCPConnectionError("Connection failed", "test-server")
                return mock_restaurants_list
            
            mock_search.side_effect = side_effect
            
            # Test dinner search with one failing district
            districts = ["Failing District", "Working District"]
            result = await mcp_client_manager.search_dinner_restaurants(districts)
            
            # Should still get results from working district
            assert len(result) == 5
            assert mock_search.call_count == 2
    
    @pytest.mark.asyncio
    async def test_get_restaurant_recommendations(self, mcp_client_manager, mock_restaurants_list):
        """Test restaurant recommendations functionality."""
        # Mock the analyze_restaurants method
        mock_recommendation_result = {
            "recommendation": {
                "id": "test_restaurant_001",
                "name": "Best Restaurant",
                "district": "Central district"
            },
            "candidates": [
                {"id": "test_restaurant_002", "name": "Second Best"},
                {"id": "test_restaurant_003", "name": "Third Best"}
            ],
            "ranking_method": "sentiment_likes"
        }
        
        with patch.object(mcp_client_manager, 'analyze_restaurants', new_callable=AsyncMock) as mock_analyze:
            mock_analyze.return_value = mock_recommendation_result
            
            # Test recommendations
            result = await mcp_client_manager.get_restaurant_recommendations(mock_restaurants_list)
            
            # Verify the call and result
            mock_analyze.assert_called_once_with(mock_restaurants_list, "sentiment_likes")
            assert result["recommendation"]["id"] == "test_restaurant_001"
            assert len(result["candidates"]) == 2
    
    @pytest.mark.asyncio
    async def test_assign_meal_restaurants(self, mcp_client_manager, mock_restaurants_list):
        """Test meal restaurant assignment functionality."""
        # Mock all search methods
        with patch.object(mcp_client_manager, 'search_breakfast_restaurants', new_callable=AsyncMock) as mock_breakfast, \
             patch.object(mcp_client_manager, 'search_lunch_restaurants', new_callable=AsyncMock) as mock_lunch, \
             patch.object(mcp_client_manager, 'search_dinner_restaurants', new_callable=AsyncMock) as mock_dinner, \
             patch.object(mcp_client_manager, 'get_restaurant_recommendations', new_callable=AsyncMock) as mock_rec, \
             patch.object(mcp_client_manager, '_dict_to_restaurant') as mock_dict_to_restaurant:
            
            # Setup mocks
            mock_breakfast.return_value = mock_restaurants_list[:2]
            mock_lunch.return_value = mock_restaurants_list[2:4]
            mock_dinner.return_value = mock_restaurants_list[4:]
            
            mock_rec.return_value = {
                "recommendation": {"id": "test_restaurant_001", "name": "Test Restaurant"}
            }
            
            mock_dict_to_restaurant.return_value = mock_restaurants_list[0]
            
            # Test meal assignment
            result = await mcp_client_manager.assign_meal_restaurants(
                morning_district="Central district",
                afternoon_district="Admiralty",
                night_district="Causeway Bay"
            )
            
            # Verify all meals were assigned
            assert result["breakfast"] is not None
            assert result["lunch"] is not None
            assert result["dinner"] is not None
            
            # Verify method calls
            mock_breakfast.assert_called_once()
            mock_lunch.assert_called_once()
            mock_dinner.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_assign_3day_itinerary_restaurants(self, mcp_client_manager):
        """Test 3-day itinerary restaurant assignment."""
        # Mock the assign_meal_restaurants method
        mock_day_assignment = {
            "breakfast": MagicMock(id="breakfast_001"),
            "lunch": MagicMock(id="lunch_001"),
            "dinner": MagicMock(id="dinner_001")
        }
        
        with patch.object(mcp_client_manager, 'assign_meal_restaurants', new_callable=AsyncMock) as mock_assign:
            mock_assign.return_value = mock_day_assignment
            
            # Test 3-day assignment
            day_districts = [
                {"morning": "Central district", "afternoon": "Admiralty", "night": "Causeway Bay"},
                {"morning": "Tsim Sha Tsui", "afternoon": "Mong Kok", "night": "Yau Ma Tei"},
                {"morning": "Wan Chai", "afternoon": "Central district", "night": "Admiralty"}
            ]
            
            result = await mcp_client_manager.assign_3day_itinerary_restaurants(day_districts)
            
            # Verify structure
            assert len(result) == 3
            assert "day_1" in result
            assert "day_2" in result
            assert "day_3" in result
            
            # Verify all days have meal assignments
            for day in result.values():
                assert "breakfast" in day
                assert "lunch" in day
                assert "dinner" in day
            
            # Verify method was called 3 times
            assert mock_assign.call_count == 3
    
    @pytest.mark.asyncio
    async def test_search_restaurants_with_fallback(self, mcp_client_manager, mock_restaurants_list):
        """Test restaurant search with fallback districts."""
        # Mock search_restaurants to fail for primary district
        with patch.object(mcp_client_manager, 'search_restaurants', new_callable=AsyncMock) as mock_search:
            def side_effect(district=None, meal_type=None):
                if district == "Primary District":
                    raise MCPConnectionError("Primary district failed", "test-server")
                elif district == "Fallback District":
                    return mock_restaurants_list
                return []
            
            mock_search.side_effect = side_effect
            
            # Test fallback functionality
            result = await mcp_client_manager.search_restaurants_with_fallback(
                primary_district="Primary District",
                meal_type="lunch",
                fallback_districts=["Fallback District"]
            )
            
            # Should get results from fallback district
            assert len(result) == 5
            assert mock_search.call_count == 2
    
    @pytest.mark.asyncio
    async def test_assign_meal_with_fallback(self, mcp_client_manager, mock_restaurants_list):
        """Test meal assignment with fallback strategies."""
        # Mock methods
        with patch.object(mcp_client_manager, 'search_restaurants_with_fallback', new_callable=AsyncMock) as mock_search, \
             patch.object(mcp_client_manager, 'get_restaurant_recommendations', new_callable=AsyncMock) as mock_rec, \
             patch.object(mcp_client_manager, '_dict_to_restaurant') as mock_dict_to_restaurant:
            
            mock_search.return_value = mock_restaurants_list
            mock_rec.return_value = {
                "recommendation": {"id": "test_restaurant_001", "name": "Best Restaurant"}
            }
            mock_dict_to_restaurant.return_value = mock_restaurants_list[0]
            
            # Test meal assignment with fallback
            result = await mcp_client_manager.assign_meal_with_fallback(
                meal_type="dinner",
                primary_district="Primary District",
                fallback_districts=["Fallback District"]
            )
            
            # Verify assignment
            assert result is not None
            assert result.id == "test_restaurant_001"
            
            # Verify method calls
            mock_search.assert_called_once()
            mock_rec.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_restaurant_assignment_placeholder(self, mcp_client_manager):
        """Test creation of restaurant assignment placeholders."""
        # Test placeholder creation
        placeholder = await mcp_client_manager.create_restaurant_assignment_placeholder(
            meal_type="breakfast",
            district="Test District",
            error_message="MCP server unavailable"
        )
        
        # Verify placeholder structure
        assert placeholder["id"] == "placeholder_breakfast_Test District"
        assert placeholder["name"] == "Restaurant Assignment Unavailable"
        assert placeholder["district"] == "Test District"
        assert placeholder["is_placeholder"] is True
        assert "error" in placeholder
        assert placeholder["error"]["type"] == "mcp_service_unavailable"
    
    @pytest.mark.asyncio
    async def test_validate_restaurant_operating_hours(self, mcp_client_manager, mock_restaurant):
        """Test restaurant operating hours validation."""
        # Test breakfast validation (should pass)
        is_valid_breakfast = await mcp_client_manager.validate_restaurant_operating_hours(
            mock_restaurant, "breakfast"
        )
        assert is_valid_breakfast is True
        
        # Test with restaurant that has no operating hours
        no_hours_restaurant = Restaurant(
            id="no_hours_001",
            name="No Hours Restaurant",
            address="Test Address",
            meal_type=["breakfast"],
            sentiment=Sentiment(likes=50, dislikes=5, neutral=5),
            location_category="Restaurant",
            district="Test District",
            price_range="$",
            operating_hours=None,
            metadata=RestaurantMetadata(data_quality="medium", version="1.0", quality_score=80)
        )
        
        is_valid_no_hours = await mcp_client_manager.validate_restaurant_operating_hours(
            no_hours_restaurant, "lunch"
        )
        assert is_valid_no_hours is True  # No hours means always open
    
    @pytest.mark.asyncio
    async def test_comprehensive_fallback_assignment(self, mcp_client_manager, mock_restaurants_list):
        """Test comprehensive fallback assignment functionality."""
        # Mock assign_meal_with_fallback to fail for some meals
        with patch.object(mcp_client_manager, 'assign_meal_with_fallback', new_callable=AsyncMock) as mock_assign, \
             patch.object(mcp_client_manager, 'create_restaurant_assignment_placeholder', new_callable=AsyncMock) as mock_placeholder:
            
            def assign_side_effect(meal_type, **kwargs):
                if meal_type == "breakfast":
                    return mock_restaurants_list[0]  # Success
                elif meal_type == "lunch":
                    return None  # Failure
                else:  # dinner
                    raise MCPConnectionError("Dinner assignment failed", "test-server")
            
            mock_assign.side_effect = assign_side_effect
            mock_placeholder.return_value = {"is_placeholder": True, "meal_type": "placeholder"}
            
            # Test comprehensive fallback
            result = await mcp_client_manager.assign_meal_restaurants_with_comprehensive_fallback(
                morning_district="Central district",
                afternoon_district="Admiralty",
                night_district="Causeway Bay"
            )
            
            # Verify results
            assert result["breakfast"] is not None
            assert not result["breakfast"].get("is_placeholder", False)  # Real assignment
            assert result["lunch"].get("is_placeholder", False)  # Placeholder
            assert result["dinner"].get("is_placeholder", False)  # Placeholder
            assert len(result["errors"]) == 2  # lunch and dinner failed
    
    def test_time_ranges_overlap(self, mcp_client_manager):
        """Test time range overlap detection."""
        # Test overlapping ranges
        assert mcp_client_manager._time_ranges_overlap("09:00 - 18:00", "11:30 - 17:29") is True
        assert mcp_client_manager._time_ranges_overlap("06:00 - 11:29", "07:00 - 22:00") is True
        
        # Test non-overlapping ranges
        assert mcp_client_manager._time_ranges_overlap("06:00 - 11:29", "12:00 - 18:00") is False
        assert mcp_client_manager._time_ranges_overlap("18:00 - 23:59", "06:00 - 11:29") is False
    
    def test_parse_time_range(self, mcp_client_manager):
        """Test time range parsing."""
        # Test valid time range
        start, end = mcp_client_manager._parse_time_range("09:00 - 18:00")
        assert start == 540  # 9 * 60
        assert end == 1080   # 18 * 60
        
        # Test with spaces
        start, end = mcp_client_manager._parse_time_range("06:30 - 23:45")
        assert start == 390  # 6 * 60 + 30
        assert end == 1425   # 23 * 60 + 45
        
        # Test invalid format
        with pytest.raises(ValueError):
            mcp_client_manager._parse_time_range("invalid format")


class TestMCPClientErrorHandling:
    """Test MCP client error handling and resilience."""
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_functionality(self, mcp_client_manager):
        """Test circuit breaker functionality."""
        # Mock search_restaurants to always fail
        with patch.object(mcp_client_manager, 'search_restaurants', new_callable=AsyncMock) as mock_search:
            mock_search.side_effect = MCPConnectionError("Connection failed", "test-server")
            
            # Test that circuit breaker eventually opens
            with pytest.raises(MCPConnectionError):
                await mcp_client_manager.search_breakfast_restaurants("Test District")
    
    @pytest.mark.asyncio
    async def test_retry_logic_with_exponential_backoff(self, mcp_client_manager):
        """Test retry logic with exponential backoff."""
        # Mock search_restaurants to fail twice then succeed
        call_count = 0
        
        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise MCPConnectionError("Temporary failure", "test-server")
            return []
        
        with patch.object(mcp_client_manager, 'search_restaurants', new_callable=AsyncMock) as mock_search:
            mock_search.side_effect = side_effect
            
            # Should succeed after retries
            result = await mcp_client_manager.search_breakfast_restaurants("Test District")
            assert result == []
            assert call_count == 3  # Failed twice, succeeded on third try
    
    @pytest.mark.asyncio
    async def test_connection_pool_management(self, mcp_client_manager):
        """Test connection pool management."""
        # Test that connection pool stats are available
        stats = mcp_client_manager.get_connection_stats()
        
        assert "search_mcp" in stats
        assert "reasoning_mcp" in stats
        assert "performance_summary" in stats
        
        # Verify structure of stats
        search_stats = stats["search_mcp"]
        assert "total_calls" in search_stats
        assert "successful_calls" in search_stats
        assert "failed_calls" in search_stats
        assert "circuit_breaker" in search_stats
        assert "connection_pool" in search_stats


if __name__ == "__main__":
    pytest.main([__file__, "-v"])