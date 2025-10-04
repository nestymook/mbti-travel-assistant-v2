#!/usr/bin/env python3
"""
Simple integration test for restaurant search endpoints.

This script tests the basic functionality of the FastAPI application
and restaurant search endpoints without requiring actual MCP servers.
"""

import sys
import json
from pathlib import Path
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from datetime import datetime, timezone

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from main import app
from middleware.jwt_validator import UserContext

def create_mock_user():
    """Create a mock authenticated user."""
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

def create_mock_mcp_client():
    """Create a mock MCP client manager."""
    mock_client = AsyncMock()
    
    # Mock search responses
    mock_search_response = {
        "restaurants": [
            {
                "id": "rest_001",
                "name": "Test Restaurant",
                "address": "123 Test St, Central",
                "meal_type": ["lunch", "dinner"],
                "sentiment": {
                    "likes": 85,
                    "dislikes": 10,
                    "neutral": 5,
                    "total_responses": 100,
                    "likes_percentage": 85.0,
                    "combined_positive_percentage": 90.0
                },
                "location_category": "Shopping Mall",
                "district": "Central district",
                "price_range": "$"
            }
        ],
        "metadata": {
            "total_count": 1,
            "execution_time": 0.15
        }
    }
    
    # Mock recommendation response
    mock_recommendation_response = {
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
            "restaurant_count": 1,
            "average_likes": 95.0,
            "average_dislikes": 3.0,
            "average_neutral": 2.0,
            "top_sentiment_score": 95.0,
            "bottom_sentiment_score": 95.0,
            "ranking_method": "sentiment_likes"
        }
    }
    
    # Mock sentiment analysis response
    mock_sentiment_response = {
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
    
    def mock_call_mcp_tool(server_name, tool_name, parameters, user_context=None):
        """Mock MCP tool calls based on tool name."""
        if tool_name in ["search_restaurants_by_district", "search_restaurants_by_meal_type", "search_restaurants_combined"]:
            return mock_search_response
        elif tool_name == "recommend_restaurants":
            return mock_recommendation_response
        elif tool_name == "analyze_restaurant_sentiment":
            return mock_sentiment_response
        else:
            raise ValueError(f"Unknown tool: {tool_name}")
    
    mock_client.call_mcp_tool.side_effect = mock_call_mcp_tool
    return mock_client

def test_health_endpoint():
    """Test the health check endpoint."""
    print("🔍 Testing health endpoint...")
    
    client = TestClient(app)
    response = client.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "agentcore-gateway-mcp-tools"
    assert data["version"] == "1.0.0"
    
    print("✅ Health endpoint test passed")

def test_root_endpoint():
    """Test the root endpoint."""
    print("🔍 Testing root endpoint...")
    
    client = TestClient(app)
    response = client.get("/")
    
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "AgentCore Gateway for MCP Tools"
    assert "endpoints" in data
    
    print("✅ Root endpoint test passed")

def test_district_search_endpoint():
    """Test the district search endpoint."""
    print("🔍 Testing district search endpoint...")
    
    client = TestClient(app)
    mock_user = create_mock_user()
    mock_mcp_client = create_mock_mcp_client()
    
    # Mock both the dependency and the JWT validator
    with patch("api.restaurant_endpoints.get_current_user", return_value=mock_user), \
         patch("api.restaurant_endpoints.get_mcp_client_manager", return_value=mock_mcp_client), \
         patch("middleware.auth_middleware.jwt_validator.validate_token", return_value=mock_user):
        
        response = client.post(
            "/api/v1/restaurants/search/district",
            json={"districts": ["Central district", "Admiralty"]},
            headers={"Authorization": "Bearer test-token"}
        )
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "restaurants" in data
    assert len(data["restaurants"]) == 1
    assert data["restaurants"][0]["name"] == "Test Restaurant"
    
    print("✅ District search endpoint test passed")

def test_meal_type_search_endpoint():
    """Test the meal type search endpoint."""
    print("🔍 Testing meal type search endpoint...")
    
    client = TestClient(app)
    mock_user = create_mock_user()
    mock_mcp_client = create_mock_mcp_client()
    
    with patch("api.restaurant_endpoints.get_current_user", return_value=mock_user), \
         patch("api.restaurant_endpoints.get_mcp_client_manager", return_value=mock_mcp_client), \
         patch("middleware.auth_middleware.jwt_validator.validate_token", return_value=mock_user):
        
        response = client.post(
            "/api/v1/restaurants/search/meal-type",
            json={"meal_types": ["breakfast", "lunch"]},
            headers={"Authorization": "Bearer test-token"}
        )
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "restaurants" in data
    assert len(data["restaurants"]) == 1
    
    print("✅ Meal type search endpoint test passed")

def test_combined_search_endpoint():
    """Test the combined search endpoint."""
    print("🔍 Testing combined search endpoint...")
    
    client = TestClient(app)
    mock_user = create_mock_user()
    mock_mcp_client = create_mock_mcp_client()
    
    with patch("api.restaurant_endpoints.get_current_user", return_value=mock_user), \
         patch("api.restaurant_endpoints.get_mcp_client_manager", return_value=mock_mcp_client), \
         patch("middleware.auth_middleware.jwt_validator.validate_token", return_value=mock_user):
        
        response = client.post(
            "/api/v1/restaurants/search/combined",
            json={
                "districts": ["Central district"],
                "meal_types": ["lunch"]
            },
            headers={"Authorization": "Bearer test-token"}
        )
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "restaurants" in data
    
    print("✅ Combined search endpoint test passed")

def test_recommend_restaurants_endpoint():
    """Test the restaurant recommendation endpoint."""
    print("🔍 Testing restaurant recommendation endpoint...")
    
    client = TestClient(app)
    mock_user = create_mock_user()
    mock_mcp_client = create_mock_mcp_client()
    
    with patch("api.restaurant_endpoints.get_current_user", return_value=mock_user), \
         patch("api.restaurant_endpoints.get_mcp_client_manager", return_value=mock_mcp_client), \
         patch("middleware.auth_middleware.jwt_validator.validate_token", return_value=mock_user):
        
        response = client.post(
            "/api/v1/restaurants/recommend",
            json={
                "restaurants": [
                    {
                        "id": "rest_001",
                        "name": "Test Restaurant",
                        "sentiment": {"likes": 95, "dislikes": 3, "neutral": 2}
                    }
                ],
                "ranking_method": "sentiment_likes"
            },
            headers={"Authorization": "Bearer test-token"}
        )
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "recommendation" in data
    assert "candidates" in data
    assert data["ranking_method"] == "sentiment_likes"
    
    print("✅ Restaurant recommendation endpoint test passed")

def test_analyze_sentiment_endpoint():
    """Test the sentiment analysis endpoint."""
    print("🔍 Testing sentiment analysis endpoint...")
    
    client = TestClient(app)
    mock_user = create_mock_user()
    mock_mcp_client = create_mock_mcp_client()
    
    with patch("api.restaurant_endpoints.get_current_user", return_value=mock_user), \
         patch("api.restaurant_endpoints.get_mcp_client_manager", return_value=mock_mcp_client), \
         patch("middleware.auth_middleware.jwt_validator.validate_token", return_value=mock_user):
        
        response = client.post(
            "/api/v1/restaurants/analyze",
            json={
                "restaurants": [
                    {
                        "id": "rest_001",
                        "name": "Restaurant A",
                        "sentiment": {"likes": 85, "dislikes": 10, "neutral": 5}
                    },
                    {
                        "id": "rest_002",
                        "name": "Restaurant B",
                        "sentiment": {"likes": 70, "dislikes": 20, "neutral": 10}
                    }
                ]
            },
            headers={"Authorization": "Bearer test-token"}
        )
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "sentiment_analysis" in data
    assert data["restaurant_count"] == 2
    
    print("✅ Sentiment analysis endpoint test passed")

def test_authentication_required():
    """Test that authentication is required."""
    print("🔍 Testing authentication requirement...")
    
    client = TestClient(app)
    
    # Test without Authorization header
    response = client.post(
        "/api/v1/restaurants/search/district",
        json={"districts": ["Central district"]}
    )
    
    assert response.status_code == 401
    data = response.json()
    assert data["success"] is False
    assert data["error"]["type"] == "AuthenticationError"
    
    print("✅ Authentication requirement test passed")

def test_validation_errors():
    """Test request validation."""
    print("🔍 Testing request validation...")
    
    client = TestClient(app)
    mock_user = create_mock_user()
    
    with patch("api.restaurant_endpoints.get_current_user", return_value=mock_user), \
         patch("middleware.auth_middleware.jwt_validator.validate_token", return_value=mock_user):
        # Test empty districts list
        response = client.post(
            "/api/v1/restaurants/search/district",
            json={"districts": []},
            headers={"Authorization": "Bearer test-token"}
        )
    
    assert response.status_code == 422
    
    print("✅ Request validation test passed")

def run_all_tests():
    """Run all integration tests."""
    print("🚀 Running AgentCore Gateway Integration Tests")
    print("=" * 60)
    
    tests = [
        test_health_endpoint,
        test_root_endpoint,
        test_district_search_endpoint,
        test_meal_type_search_endpoint,
        test_combined_search_endpoint,
        test_recommend_restaurants_endpoint,
        test_analyze_sentiment_endpoint,
        test_authentication_required,
        test_validation_errors
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"❌ {test.__name__} failed: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS")
    print("=" * 60)
    print(f"Total tests: {len(tests)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Success rate: {(passed / len(tests)) * 100:.1f}%")
    
    if failed == 0:
        print("🎉 All integration tests passed!")
        return True
    else:
        print("🔧 Some tests need attention")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)