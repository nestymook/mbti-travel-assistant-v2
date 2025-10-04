"""
Unit tests for restaurant reasoning endpoints.

This module contains unit tests for the restaurant recommendation
and sentiment analysis endpoint functions.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone

from api.restaurant_endpoints import recommend_restaurants, analyze_restaurant_sentiment
from models.request_models import RestaurantRecommendationRequest, SentimentAnalysisRequest, RestaurantData, RankingMethod
from middleware.jwt_validator import UserContext


class TestReasoningEndpointsUnit:
    """Unit tests for reasoning endpoint functions."""
    
    @pytest.fixture
    def mock_user_context(self):
        """Mock authenticated user context."""
        return UserContext(
            user_id="test-user-123",
            username="testuser",
            email="test@example.com",
            token_claims={
                "sub": "test-user-123",
                "token_use": "access",
                "aud": "test-client-id",
                "iss": "https://cognito-idp.us-east-1.amazonaws.com/us-east-1_TEST",
                "access_token": "test-access-token"
            },
            authenticated_at=datetime.now(timezone.utc)
        )
    
    @pytest.fixture
    def mock_mcp_client(self):
        """Mock MCP client manager."""
        mock_client = AsyncMock()
        mock_client.call_mcp_tool = AsyncMock()
        return mock_client
    
    @pytest.fixture
    def sample_restaurant_data(self):
        """Sample restaurant data for testing."""
        return RestaurantData(
            id="rest_001",
            name="Test Restaurant",
            sentiment={"likes": 95, "dislikes": 3, "neutral": 2}
        )
    
    @pytest.mark.asyncio
    async def test_recommend_restaurants_success(self, mock_user_context, mock_mcp_client, sample_restaurant_data):
        """Test successful restaurant recommendation."""
        # Mock MCP response
        mock_response = {
            "recommendation": {
                "id": "rest_001",
                "name": "Top Restaurant",
                "sentiment": {"likes": 95, "dislikes": 3, "neutral": 2}
            },
            "candidates": [
                {
                    "id": "rest_001",
                    "name": "Top Restaurant",
                    "sentiment": {"likes": 95, "dislikes": 3, "neutral": 2}
                }
            ],
            "ranking_method": "sentiment_likes",
            "analysis_summary": {
                "total_restaurants": 1,
                "average_likes": 95.0
            }
        }
        mock_mcp_client.call_mcp_tool.return_value = mock_response
        
        # Create request
        request = RestaurantRecommendationRequest(
            restaurants=[sample_restaurant_data],
            ranking_method=RankingMethod.SENTIMENT_LIKES
        )
        
        # Call endpoint function
        response = await recommend_restaurants(request, mock_user_context, mock_mcp_client)
        
        # Verify response
        assert response.success is True
        assert response.ranking_method == "sentiment_likes"
        assert response.recommendation is not None
        assert response.candidates is not None
        assert response.analysis_summary is not None
        
        # Verify MCP call
        mock_mcp_client.call_mcp_tool.assert_called_once_with(
            server_name="restaurant-reasoning",
            tool_name="recommend_restaurants",
            parameters={
                "restaurants": [sample_restaurant_data.model_dump()],
                "ranking_method": "sentiment_likes"
            },
            user_context={
                "user_id": "test-user-123",
                "username": "testuser",
                "email": "test@example.com",
                "token": "test-access-token"
            }
        )
    
    @pytest.mark.asyncio
    async def test_recommend_restaurants_combined_sentiment(self, mock_user_context, mock_mcp_client, sample_restaurant_data):
        """Test restaurant recommendation with combined sentiment ranking."""
        # Mock MCP response
        mock_response = {
            "recommendation": {
                "id": "rest_001",
                "name": "Balanced Restaurant",
                "sentiment": {"likes": 80, "dislikes": 5, "neutral": 15}
            },
            "candidates": [
                {
                    "id": "rest_001",
                    "name": "Balanced Restaurant",
                    "sentiment": {"likes": 80, "dislikes": 5, "neutral": 15}
                }
            ],
            "ranking_method": "combined_sentiment",
            "analysis_summary": {
                "total_restaurants": 1,
                "average_likes": 80.0,
                "combined_positive_percentage": 95.0
            }
        }
        mock_mcp_client.call_mcp_tool.return_value = mock_response
        
        # Create request with combined sentiment ranking
        request = RestaurantRecommendationRequest(
            restaurants=[sample_restaurant_data],
            ranking_method=RankingMethod.COMBINED_SENTIMENT
        )
        
        # Call endpoint function
        response = await recommend_restaurants(request, mock_user_context, mock_mcp_client)
        
        # Verify response
        assert response.success is True
        assert response.ranking_method == "combined_sentiment"
        assert response.recommendation is not None
        
        # Verify MCP call with correct ranking method
        mock_mcp_client.call_mcp_tool.assert_called_once_with(
            server_name="restaurant-reasoning",
            tool_name="recommend_restaurants",
            parameters={
                "restaurants": [sample_restaurant_data.model_dump()],
                "ranking_method": "combined_sentiment"
            },
            user_context={
                "user_id": "test-user-123",
                "username": "testuser",
                "email": "test@example.com",
                "token": "test-access-token"
            }
        )
    
    @pytest.mark.asyncio
    async def test_recommend_restaurants_mcp_error(self, mock_user_context, mock_mcp_client, sample_restaurant_data):
        """Test restaurant recommendation with MCP server error."""
        # Mock MCP server error
        mock_mcp_client.call_mcp_tool.side_effect = Exception("MCP server unavailable")
        
        # Create request
        request = RestaurantRecommendationRequest(
            restaurants=[sample_restaurant_data],
            ranking_method=RankingMethod.SENTIMENT_LIKES
        )
        
        # Call endpoint function and expect HTTPException
        with pytest.raises(Exception) as exc_info:
            await recommend_restaurants(request, mock_user_context, mock_mcp_client)
        
        # Verify exception details
        assert "MCP server unavailable" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_analyze_sentiment_success(self, mock_user_context, mock_mcp_client):
        """Test successful sentiment analysis."""
        # Mock MCP response
        mock_response = {
            "sentiment_analysis": {
                "average_likes": 77.5,
                "average_dislikes": 15.0,
                "average_neutral": 7.5,
                "total_restaurants": 2,
                "score_ranges": {
                    "likes": {"min": 70, "max": 85},
                    "dislikes": {"min": 10, "max": 20},
                    "neutral": {"min": 5, "max": 10}
                }
            },
            "restaurant_count": 2,
            "ranking_method": "sentiment_likes"
        }
        mock_mcp_client.call_mcp_tool.return_value = mock_response
        
        # Create request with multiple restaurants
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
        
        # Call endpoint function
        response = await analyze_restaurant_sentiment(request, mock_user_context, mock_mcp_client)
        
        # Verify response
        assert response.success is True
        assert response.restaurant_count == 2
        assert response.ranking_method == "sentiment_likes"
        assert response.sentiment_analysis is not None
        
        # Verify MCP call
        mock_mcp_client.call_mcp_tool.assert_called_once_with(
            server_name="restaurant-reasoning",
            tool_name="analyze_restaurant_sentiment",
            parameters={
                "restaurants": [restaurant.model_dump() for restaurant in restaurants]
            },
            user_context={
                "user_id": "test-user-123",
                "username": "testuser",
                "email": "test@example.com",
                "token": "test-access-token"
            }
        )
    
    @pytest.mark.asyncio
    async def test_analyze_sentiment_single_restaurant(self, mock_user_context, mock_mcp_client):
        """Test sentiment analysis with single restaurant."""
        # Mock MCP response
        mock_response = {
            "sentiment_analysis": {
                "average_likes": 90.0,
                "average_dislikes": 5.0,
                "average_neutral": 5.0,
                "total_restaurants": 1
            },
            "restaurant_count": 1,
            "ranking_method": "sentiment_likes"
        }
        mock_mcp_client.call_mcp_tool.return_value = mock_response
        
        # Create request with single restaurant
        restaurant = RestaurantData(
            id="rest_001",
            name="Excellent Restaurant",
            sentiment={"likes": 90, "dislikes": 5, "neutral": 5}
        )
        
        request = SentimentAnalysisRequest(restaurants=[restaurant])
        
        # Call endpoint function
        response = await analyze_restaurant_sentiment(request, mock_user_context, mock_mcp_client)
        
        # Verify response
        assert response.success is True
        assert response.restaurant_count == 1
        assert response.sentiment_analysis["average_likes"] == 90.0
    
    @pytest.mark.asyncio
    async def test_analyze_sentiment_mcp_error(self, mock_user_context, mock_mcp_client, sample_restaurant_data):
        """Test sentiment analysis with MCP server error."""
        # Mock MCP server error
        mock_mcp_client.call_mcp_tool.side_effect = Exception("MCP server unavailable")
        
        # Create request
        request = SentimentAnalysisRequest(restaurants=[sample_restaurant_data])
        
        # Call endpoint function and expect HTTPException
        with pytest.raises(Exception) as exc_info:
            await analyze_restaurant_sentiment(request, mock_user_context, mock_mcp_client)
        
        # Verify exception details
        assert "MCP server unavailable" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_recommend_restaurants_multiple_restaurants(self, mock_user_context, mock_mcp_client):
        """Test restaurant recommendation with multiple restaurants."""
        # Mock MCP response
        mock_response = {
            "recommendation": {
                "id": "rest_001",
                "name": "Best Restaurant",
                "sentiment": {"likes": 95, "dislikes": 3, "neutral": 2}
            },
            "candidates": [
                {
                    "id": "rest_001",
                    "name": "Best Restaurant",
                    "sentiment": {"likes": 95, "dislikes": 3, "neutral": 2}
                },
                {
                    "id": "rest_002",
                    "name": "Good Restaurant",
                    "sentiment": {"likes": 80, "dislikes": 10, "neutral": 10}
                }
            ],
            "ranking_method": "sentiment_likes",
            "analysis_summary": {
                "total_restaurants": 2,
                "average_likes": 87.5
            }
        }
        mock_mcp_client.call_mcp_tool.return_value = mock_response
        
        # Create request with multiple restaurants
        restaurants = [
            RestaurantData(
                id="rest_001",
                name="Best Restaurant",
                sentiment={"likes": 95, "dislikes": 3, "neutral": 2}
            ),
            RestaurantData(
                id="rest_002",
                name="Good Restaurant",
                sentiment={"likes": 80, "dislikes": 10, "neutral": 10}
            )
        ]
        
        request = RestaurantRecommendationRequest(
            restaurants=restaurants,
            ranking_method=RankingMethod.SENTIMENT_LIKES
        )
        
        # Call endpoint function
        response = await recommend_restaurants(request, mock_user_context, mock_mcp_client)
        
        # Verify response
        assert response.success is True
        assert response.ranking_method == "sentiment_likes"
        assert len(response.candidates) == 2
        assert response.analysis_summary["total_restaurants"] == 2
        
        # Verify MCP call
        mock_mcp_client.call_mcp_tool.assert_called_once_with(
            server_name="restaurant-reasoning",
            tool_name="recommend_restaurants",
            parameters={
                "restaurants": [restaurant.model_dump() for restaurant in restaurants],
                "ranking_method": "sentiment_likes"
            },
            user_context={
                "user_id": "test-user-123",
                "username": "testuser",
                "email": "test@example.com",
                "token": "test-access-token"
            }
        )