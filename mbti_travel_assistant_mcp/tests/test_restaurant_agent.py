"""
Tests for RestaurantAgent - Strands Agent Implementation

This module tests the RestaurantAgent service that implements the internal
LLM agent using Strands Agents framework for restaurant recommendation
orchestration.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from services.restaurant_agent import RestaurantAgent
from models.restaurant_models import Restaurant, Sentiment, OperatingHours, RestaurantMetadata


@pytest.fixture
def sample_restaurant():
    """Create a sample restaurant for testing."""
    return Restaurant(
        id="rest_001",
        name="Test Restaurant",
        address="123 Test Street, Central",
        meal_type=["Chinese", "Dim Sum"],
        sentiment=Sentiment(likes=85, dislikes=10, neutral=5),
        location_category="Shopping Mall",
        district="Central district",
        price_range="$$",
        operating_hours=OperatingHours(
            mon_fri=["07:00 - 11:30", "11:30 - 15:30"],
            sat_sun=["08:00 - 16:00"],
            public_holiday=["08:00 - 16:00"]
        ),
        metadata=RestaurantMetadata(
            data_quality="high",
            version="1.0",
            quality_score=95
        )
    )


@pytest.fixture
def mock_mcp_client_manager():
    """Create a mock MCP client manager."""
    mock_manager = Mock()
    mock_manager.search_restaurants = AsyncMock()
    mock_manager.analyze_restaurants = AsyncMock()
    return mock_manager


@pytest.fixture
def restaurant_agent(mock_mcp_client_manager):
    """Create a RestaurantAgent with mocked dependencies."""
    with patch('services.restaurant_agent.MCPClientManager', return_value=mock_mcp_client_manager):
        agent = RestaurantAgent()
        agent.mcp_client_manager = mock_mcp_client_manager
        return agent


class TestRestaurantAgent:
    """Test cases for RestaurantAgent."""
    
    def test_agent_initialization(self, restaurant_agent):
        """Test that the agent initializes correctly."""
        assert restaurant_agent is not None
        assert restaurant_agent.agent is not None
        assert restaurant_agent.mcp_client_manager is not None
    
    @pytest.mark.asyncio
    async def test_process_parameters(self, restaurant_agent):
        """Test parameter processing and normalization."""
        # Test district normalization
        params = await restaurant_agent._process_parameters(
            district="central",
            meal_time="morning",
            user_context=None,
            correlation_id="test_001"
        )
        
        assert params["district"] == "Central district"
        assert params["meal_time"] == "breakfast"
        assert params["user_preferences"] == {}
    
    @pytest.mark.asyncio
    async def test_process_parameters_with_user_context(self, restaurant_agent):
        """Test parameter processing with user context."""
        user_context = {
            "sub": "user_123",
            "custom:preferences": {"cuisine": "Chinese"},
            "custom:dietary_restrictions": ["vegetarian"]
        }
        
        params = await restaurant_agent._process_parameters(
            district="Admiralty",
            meal_time="lunch",
            user_context=user_context,
            correlation_id="test_002"
        )
        
        assert params["district"] == "Admiralty"
        assert params["meal_time"] == "lunch"
        assert params["user_preferences"]["user_id"] == "user_123"
        assert params["user_preferences"]["dietary_restrictions"] == ["vegetarian"]
    
    @pytest.mark.asyncio
    async def test_filter_search_results(self, restaurant_agent, sample_restaurant):
        """Test filtering of search results."""
        # Create restaurants with different sentiment data
        restaurants = [
            sample_restaurant,  # Has sentiment data
            Restaurant(
                id="rest_002",
                name="No Sentiment Restaurant",
                address="456 Test Ave",
                meal_type=["Western"],
                sentiment=Sentiment(likes=0, dislikes=0, neutral=0),  # No sentiment
                location_category="Street",
                district="Central district",
                price_range="$",
                operating_hours=OperatingHours(
                    mon_fri=["09:00 - 18:00"],
                    sat_sun=["10:00 - 16:00"],
                    public_holiday=["10:00 - 16:00"]
                ),
                metadata=RestaurantMetadata(
                    data_quality="medium",
                    version="1.0",
                    quality_score=70
                )
            )
        ]
        
        processed_params = {"user_preferences": {}}
        
        filtered = await restaurant_agent._filter_search_results(
            restaurants, processed_params, "test_003"
        )
        
        # Should only include restaurant with sentiment data
        assert len(filtered) == 1
        assert filtered[0].id == "rest_001"
    
    @pytest.mark.asyncio
    async def test_validate_reasoning_results(self, restaurant_agent, sample_restaurant):
        """Test validation and enhancement of reasoning results."""
        reasoning_results = {
            "recommendation": None,
            "candidates": [sample_restaurant.to_dict()],
            "ranking_method": "sentiment_likes"
        }
        
        processed_params = {
            "district": "Central district",
            "meal_time": "breakfast"
        }
        
        validated = await restaurant_agent._validate_reasoning_results(
            reasoning_results, processed_params, "test_004"
        )
        
        # Should promote first candidate to recommendation
        assert validated["recommendation"] is not None
        assert len(validated["candidates"]) == 0  # Moved to recommendation
        assert "search_criteria" in validated
        assert validated["search_criteria"]["district"] == "Central district"
    
    @pytest.mark.asyncio
    async def test_search_restaurants_success(self, restaurant_agent, sample_restaurant):
        """Test successful restaurant search."""
        # Mock successful search
        restaurant_agent.mcp_client_manager.search_restaurants.return_value = [sample_restaurant]
        
        results = await restaurant_agent._search_restaurants(
            district="Central district",
            meal_time="breakfast",
            correlation_id="test_005"
        )
        
        assert len(results) == 1
        assert results[0].id == "rest_001"
        restaurant_agent.mcp_client_manager.search_restaurants.assert_called_once_with(
            district="Central district",
            meal_time="breakfast"
        )
    
    @pytest.mark.asyncio
    async def test_analyze_restaurants_success(self, restaurant_agent, sample_restaurant):
        """Test successful restaurant analysis."""
        # Mock successful analysis
        expected_results = {
            "recommendation": sample_restaurant.to_dict(),
            "candidates": [],
            "ranking_method": "sentiment_likes",
            "analysis_summary": {"total_restaurants": 1}
        }
        restaurant_agent.mcp_client_manager.analyze_restaurants.return_value = expected_results
        
        results = await restaurant_agent._analyze_restaurants(
            restaurants=[sample_restaurant],
            correlation_id="test_006"
        )
        
        assert results["recommendation"] is not None
        assert results["ranking_method"] == "sentiment_likes"
        restaurant_agent.mcp_client_manager.analyze_restaurants.assert_called_once_with(
            restaurants=[sample_restaurant],
            ranking_method="sentiment_likes"
        )
    
    @pytest.mark.asyncio
    async def test_analyze_restaurants_empty_input(self, restaurant_agent):
        """Test analysis with empty restaurant list."""
        results = await restaurant_agent._analyze_restaurants(
            restaurants=[],
            correlation_id="test_007"
        )
        
        assert results["recommendation"] is None
        assert results["candidates"] == []
        assert "No restaurants available for analysis" in results["analysis_summary"]["message"]
    
    @pytest.mark.asyncio
    async def test_process_request_full_workflow(self, restaurant_agent, sample_restaurant):
        """Test the complete request processing workflow."""
        # Mock the MCP client calls
        restaurant_agent.mcp_client_manager.search_restaurants.return_value = [sample_restaurant]
        restaurant_agent.mcp_client_manager.analyze_restaurants.return_value = {
            "recommendation": sample_restaurant.to_dict(),
            "candidates": [],
            "ranking_method": "sentiment_likes",
            "analysis_summary": {"total_restaurants": 1}
        }
        
        # Mock the Strands Agent response
        mock_agent_response = Mock()
        mock_agent_response.content = '{"recommendation": {"id": "rest_001", "name": "Test Restaurant"}, "candidates": [], "metadata": {}}'
        
        with patch.object(restaurant_agent.agent, 'process', return_value=mock_agent_response):
            result = await restaurant_agent.process_request(
                district="Central district",
                meal_time="breakfast",
                user_context=None,
                correlation_id="test_008"
            )
        
        assert "recommendation" in result
        assert "candidates" in result
        assert "metadata" in result
    
    @pytest.mark.asyncio
    async def test_process_request_with_mcp_error(self, restaurant_agent):
        """Test request processing when MCP calls fail."""
        # Mock MCP client to raise an exception
        restaurant_agent.mcp_client_manager.search_restaurants.side_effect = Exception("MCP connection failed")
        
        with pytest.raises(Exception) as exc_info:
            await restaurant_agent.process_request(
                district="Central district",
                meal_time="breakfast",
                correlation_id="test_009"
            )
        
        assert "MCP connection failed" in str(exc_info.value)
    
    def test_system_prompt_content(self, restaurant_agent):
        """Test that the system prompt contains required elements."""
        system_prompt = restaurant_agent._get_system_prompt()
        
        # Check for key elements in the system prompt
        assert "restaurant recommendation orchestration agent" in system_prompt.lower()
        assert "mcp server" in system_prompt.lower()
        assert "json" in system_prompt.lower()
        assert "recommendation" in system_prompt.lower()
        assert "candidates" in system_prompt.lower()
    
    def test_fallback_format_response(self, restaurant_agent, sample_restaurant):
        """Test fallback response formatting."""
        reasoning_results = {
            "recommendation": sample_restaurant.to_dict(),
            "candidates": [],
            "ranking_method": "sentiment_likes"
        }
        
        start_time = datetime.utcnow()
        
        response = restaurant_agent._fallback_format_response(
            reasoning_results,
            district="Central district",
            meal_time="breakfast",
            start_time=start_time
        )
        
        assert response["recommendation"] is not None
        assert response["candidates"] == []
        assert response["metadata"]["formatted_by"] == "fallback"
        assert response["metadata"]["search_criteria"]["district"] == "Central district"


if __name__ == "__main__":
    pytest.main([__file__])