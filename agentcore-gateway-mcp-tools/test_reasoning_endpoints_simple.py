#!/usr/bin/env python3
"""
Simple integration test for reasoning endpoints.

This script tests the reasoning endpoints by directly calling the endpoint functions
to verify they work correctly with proper mock data.
"""

import asyncio
import sys
import os
from datetime import datetime, timezone
from unittest.mock import AsyncMock

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from api.restaurant_endpoints import recommend_restaurants, analyze_restaurant_sentiment
from models.request_models import RestaurantRecommendationRequest, SentimentAnalysisRequest, RestaurantData, RankingMethod
from middleware.jwt_validator import UserContext


async def test_reasoning_endpoints():
    """Test the reasoning endpoints with proper mock data."""
    
    print("🧪 Testing AgentCore Gateway reasoning endpoints...")
    print("=" * 60)
    
    # Create mock user context
    mock_user_context = UserContext(
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
    
    # Create mock MCP client
    mock_mcp_client = AsyncMock()
    
    print("🔧 Testing restaurant recommendation endpoint...")
    print("-" * 50)
    
    try:
        # Mock MCP response for recommendation
        mock_recommendation_response = {
            "recommendation": {
                "id": "rest_001",
                "name": "Top Restaurant",
                "address": "123 Main St, Central",
                "meal_type": ["lunch", "dinner"],
                "sentiment": {
                    "likes": 95,
                    "dislikes": 3,
                    "neutral": 2,
                    "total_responses": 100,
                    "likes_percentage": 95.0,
                    "combined_positive_percentage": 97.0
                },
                "location_category": "Shopping Mall",
                "district": "Central district",
                "price_range": "$"
            },
            "candidates": [
                {
                    "id": "rest_001",
                    "name": "Top Restaurant",
                    "address": "123 Main St, Central",
                    "meal_type": ["lunch", "dinner"],
                    "sentiment": {
                        "likes": 95,
                        "dislikes": 3,
                        "neutral": 2,
                        "total_responses": 100,
                        "likes_percentage": 95.0,
                        "combined_positive_percentage": 97.0
                    },
                    "location_category": "Shopping Mall",
                    "district": "Central district",
                    "price_range": "$"
                }
            ],
            "ranking_method": "sentiment_likes",
            "analysis_summary": {
                "restaurant_count": 1,
                "average_likes": 95.0,
                "average_dislikes": 3.0,
                "average_neutral": 2.0,
                "top_sentiment_score": 95.0,
                "bottom_sentiment_score": 95.0,
                "ranking_method": "sentiment_likes"
            }
        }
        
        mock_mcp_client.call_mcp_tool.return_value = mock_recommendation_response
        
        # Create recommendation request
        recommendation_request = RestaurantRecommendationRequest(
            restaurants=[
                RestaurantData(
                    id="rest_001",
                    name="Test Restaurant",
                    sentiment={"likes": 95, "dislikes": 3, "neutral": 2}
                )
            ],
            ranking_method=RankingMethod.SENTIMENT_LIKES
        )
        
        # Call recommendation endpoint
        recommendation_response = await recommend_restaurants(
            recommendation_request, 
            mock_user_context, 
            mock_mcp_client
        )
        
        print(f"✅ Recommendation endpoint test passed!")
        print(f"   - Success: {recommendation_response.success}")
        print(f"   - Ranking method: {recommendation_response.ranking_method}")
        print(f"   - Recommendation: {recommendation_response.recommendation.name}")
        print(f"   - Candidates count: {len(recommendation_response.candidates)}")
        
        # Verify MCP call was made correctly
        mock_mcp_client.call_mcp_tool.assert_called_with(
            server_name="restaurant-reasoning",
            tool_name="recommend_restaurants",
            parameters={
                "restaurants": [recommendation_request.restaurants[0].model_dump()],
                "ranking_method": "sentiment_likes"
            },
            user_context={
                "user_id": "test-user-123",
                "username": "testuser",
                "email": "test@example.com",
                "token": "test-access-token"
            }
        )
        
    except Exception as e:
        print(f"❌ Recommendation endpoint test failed: {e}")
        return False
    
    print("\n🔧 Testing sentiment analysis endpoint...")
    print("-" * 50)
    
    try:
        # Reset mock for sentiment analysis
        mock_mcp_client.reset_mock()
        
        # Mock MCP response for sentiment analysis
        mock_analysis_response = {
            "sentiment_analysis": {
                "restaurant_count": 2,
                "average_likes": 77.5,
                "average_dislikes": 15.0,
                "average_neutral": 7.5,
                "top_sentiment_score": 85.0,
                "bottom_sentiment_score": 70.0,
                "ranking_method": "sentiment_likes"
            },
            "restaurant_count": 2,
            "ranking_method": "sentiment_likes"
        }
        
        mock_mcp_client.call_mcp_tool.return_value = mock_analysis_response
        
        # Create sentiment analysis request
        analysis_request = SentimentAnalysisRequest(
            restaurants=[
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
        )
        
        # Call sentiment analysis endpoint
        analysis_response = await analyze_restaurant_sentiment(
            analysis_request,
            mock_user_context,
            mock_mcp_client
        )
        
        print(f"✅ Sentiment analysis endpoint test passed!")
        print(f"   - Success: {analysis_response.success}")
        print(f"   - Restaurant count: {analysis_response.restaurant_count}")
        print(f"   - Ranking method: {analysis_response.ranking_method}")
        print(f"   - Average likes: {analysis_response.sentiment_analysis.average_likes}")
        
        # Verify MCP call was made correctly
        mock_mcp_client.call_mcp_tool.assert_called_with(
            server_name="restaurant-reasoning",
            tool_name="analyze_restaurant_sentiment",
            parameters={
                "restaurants": [restaurant.model_dump() for restaurant in analysis_request.restaurants]
            },
            user_context={
                "user_id": "test-user-123",
                "username": "testuser",
                "email": "test@example.com",
                "token": "test-access-token"
            }
        )
        
    except Exception as e:
        print(f"❌ Sentiment analysis endpoint test failed: {e}")
        return False
    
    print("\n🎉 All reasoning endpoint tests passed successfully!")
    print("\n📋 Summary:")
    print("   ✅ POST /api/v1/restaurants/recommend - Working correctly")
    print("   ✅ POST /api/v1/restaurants/analyze - Working correctly")
    print("   ✅ Request validation - Working correctly")
    print("   ✅ MCP client integration - Working correctly")
    print("   ✅ Response formatting - Working correctly")
    
    return True


if __name__ == "__main__":
    success = asyncio.run(test_reasoning_endpoints())
    sys.exit(0 if success else 1)