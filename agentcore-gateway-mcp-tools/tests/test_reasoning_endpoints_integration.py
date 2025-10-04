"""
Integration tests for restaurant reasoning endpoints.

This module contains focused integration tests for the restaurant recommendation
and sentiment analysis endpoints with proper authentication mocking.
"""

import pytest
import json
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from datetime import datetime, timezone

from main import app
from models.request_models import MealType, RankingMethod
from middleware.jwt_validator import UserContext


class TestReasoningEndpoints:
    """Test class for restaurant reasoning endpoints."""
    
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
    def auth_headers(self):
        """Authentication headers for requests."""
        return {"Authorization": "Bearer test-jwt-token"}
    
    def test_recommend_restaurants_success(self, mock_user_context, mock_mcp_client, auth_headers):
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
        
        with patch("api.restaurant_endpoints.get_current_user", return_value=mock_user_context), \
             patch("api.restaurant_endpoints.get_mcp_client_manager", return_value=mock_mcp_client), \
             patch("middleware.auth_middleware.get_current_user", return_value=mock_user_context):
            
            client = TestClient(app)
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
                headers=auth_headers
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["ranking_method"] == "sentiment_likes"
        assert "recommendation" in data
        assert "candidates" in data
        assert "analysis_summary" in data
        
        # Verify MCP call
        mock_mcp_client.call_mcp_tool.assert_called_once_with(
            server_name="restaurant-reasoning",
            tool_name="recommend_restaurants",
            parameters={
                "restaurants": [
                    {
                        "id": "rest_001",
                        "name": "Test Restaurant",
                        "sentiment": {"likes": 95, "dislikes": 3, "neutral": 2},
                        "address": None,
                        "district": None,
                        "meal_type": None,
                        "price_range": None,
                        "location_category": None
                    }
                ],
                "ranking_method": "sentiment_likes"
            },
            user_context={
                "user_id": "test-user-123",
                "username": "testuser",
                "email": "test@example.com",
                "token": "test-access-token"
            }
        )
    
    def test_recommend_restaurants_combined_sentiment_method(self, mock_user_context, mock_mcp_client, auth_headers):
        """Test restaurant recommendation with combined sentiment ranking method."""
        # Mock MCP response
        mock_response = {
            "recommendation": {
                "id": "rest_002",
                "name": "Balanced Restaurant",
                "sentiment": {"likes": 80, "dislikes": 5, "neutral": 15}
            },
            "candidates": [
                {
                    "id": "rest_002",
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
        
        with patch("api.restaurant_endpoints.get_current_user", return_value=mock_user_context), \
             patch("api.restaurant_endpoints.get_mcp_client_manager", return_value=mock_mcp_client):
            
            client = TestClient(app)
            response = client.post(
                "/api/v1/restaurants/recommend",
                json={
                    "restaurants": [
                        {
                            "id": "rest_002",
                            "name": "Balanced Restaurant",
                            "sentiment": {"likes": 80, "dislikes": 5, "neutral": 15}
                        }
                    ],
                    "ranking_method": "combined_sentiment"
                },
                headers=auth_headers
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["ranking_method"] == "combined_sentiment"
        assert data["recommendation"]["name"] == "Balanced Restaurant"
        
        # Verify MCP call with correct ranking method
        mock_mcp_client.call_mcp_tool.assert_called_once_with(
            server_name="restaurant-reasoning",
            tool_name="recommend_restaurants",
            parameters={
                "restaurants": [
                    {
                        "id": "rest_002",
                        "name": "Balanced Restaurant",
                        "sentiment": {"likes": 80, "dislikes": 5, "neutral": 15},
                        "address": None,
                        "district": None,
                        "meal_type": None,
                        "price_range": None,
                        "location_category": None
                    }
                ],
                "ranking_method": "combined_sentiment"
            },
            user_context={
                "user_id": "test-user-123",
                "username": "testuser",
                "email": "test@example.com",
                "token": "test-access-token"
            }
        )
    
    def test_recommend_restaurants_mcp_server_unavailable(self, mock_user_context, mock_mcp_client, auth_headers):
        """Test restaurant recommendation when MCP server is unavailable."""
        # Mock MCP server error
        mock_mcp_client.call_mcp_tool.side_effect = Exception("MCP server unavailable")
        
        with patch("api.restaurant_endpoints.get_current_user", return_value=mock_user_context), \
             patch("api.restaurant_endpoints.get_mcp_client_manager", return_value=mock_mcp_client):
            
            client = TestClient(app)
            response = client.post(
                "/api/v1/restaurants/recommend",
                json={
                    "restaurants": [
                        {
                            "id": "rest_001",
                            "name": "Test Restaurant",
                            "sentiment": {"likes": 95, "dislikes": 3, "neutral": 2}
                        }
                    ]
                },
                headers=auth_headers
            )
        
        assert response.status_code == 503
        data = response.json()
        assert data["detail"]["type"] == "ServiceUnavailable"
        assert "temporarily unavailable" in data["detail"]["message"]
        assert data["detail"]["retry_after"] == 30
    
    def test_analyze_sentiment_success(self, mock_user_context, mock_mcp_client, auth_headers):
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
        
        with patch("api.restaurant_endpoints.get_current_user", return_value=mock_user_context), \
             patch("api.restaurant_endpoints.get_mcp_client_manager", return_value=mock_mcp_client):
            
            client = TestClient(app)
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
                headers=auth_headers
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["restaurant_count"] == 2
        assert data["ranking_method"] == "sentiment_likes"
        assert "sentiment_analysis" in data
        assert data["sentiment_analysis"]["average_likes"] == 77.5
        
        # Verify MCP call
        mock_mcp_client.call_mcp_tool.assert_called_once_with(
            server_name="restaurant-reasoning",
            tool_name="analyze_restaurant_sentiment",
            parameters={
                "restaurants": [
                    {
                        "id": "rest_001",
                        "name": "Restaurant A",
                        "sentiment": {"likes": 85, "dislikes": 10, "neutral": 5},
                        "address": None,
                        "district": None,
                        "meal_type": None,
                        "price_range": None,
                        "location_category": None
                    },
                    {
                        "id": "rest_002",
                        "name": "Restaurant B",
                        "sentiment": {"likes": 70, "dislikes": 20, "neutral": 10},
                        "address": None,
                        "district": None,
                        "meal_type": None,
                        "price_range": None,
                        "location_category": None
                    }
                ]
            },
            user_context={
                "user_id": "test-user-123",
                "username": "testuser",
                "email": "test@example.com",
                "token": "test-access-token"
            }
        )
    
    def test_analyze_sentiment_single_restaurant(self, mock_user_context, mock_mcp_client, auth_headers):
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
        
        with patch("api.restaurant_endpoints.get_current_user", return_value=mock_user_context), \
             patch("api.restaurant_endpoints.get_mcp_client_manager", return_value=mock_mcp_client):
            
            client = TestClient(app)
            response = client.post(
                "/api/v1/restaurants/analyze",
                json={
                    "restaurants": [
                        {
                            "id": "rest_001",
                            "name": "Excellent Restaurant",
                            "sentiment": {"likes": 90, "dislikes": 5, "neutral": 5}
                        }
                    ]
                },
                headers=auth_headers
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["restaurant_count"] == 1
        assert data["sentiment_analysis"]["average_likes"] == 90.0
    
    def test_analyze_sentiment_mcp_server_unavailable(self, mock_user_context, mock_mcp_client, auth_headers):
        """Test sentiment analysis when MCP server is unavailable."""
        # Mock MCP server error
        mock_mcp_client.call_mcp_tool.side_effect = Exception("MCP server unavailable")
        
        with patch("api.restaurant_endpoints.get_current_user", return_value=mock_user_context), \
             patch("api.restaurant_endpoints.get_mcp_client_manager", return_value=mock_mcp_client):
            
            client = TestClient(app)
            response = client.post(
                "/api/v1/restaurants/analyze",
                json={
                    "restaurants": [
                        {
                            "id": "rest_001",
                            "name": "Test Restaurant",
                            "sentiment": {"likes": 85, "dislikes": 10, "neutral": 5}
                        }
                    ]
                },
                headers=auth_headers
            )
        
        assert response.status_code == 503
        data = response.json()
        assert data["detail"]["type"] == "ServiceUnavailable"
        assert "temporarily unavailable" in data["detail"]["message"]
        assert data["detail"]["retry_after"] == 30
    
    def test_recommend_restaurants_validation_error(self, auth_headers):
        """Test restaurant recommendation with validation error."""
        client = TestClient(app)
        response = client.post(
            "/api/v1/restaurants/recommend",
            json={
                "restaurants": [
                    {
                        "id": "rest_001",
                        "name": "Test Restaurant",
                        "sentiment": {"likes": -5}  # Missing required fields and negative value
                    }
                ]
            },
            headers=auth_headers
        )
        
        assert response.status_code == 422
        data = response.json()
        assert "validation error" in data["detail"][0]["msg"].lower()
    
    def test_analyze_sentiment_validation_error(self, auth_headers):
        """Test sentiment analysis with validation error."""
        client = TestClient(app)
        response = client.post(
            "/api/v1/restaurants/analyze",
            json={
                "restaurants": []  # Empty restaurants list
            },
            headers=auth_headers
        )
        
        assert response.status_code == 422
        data = response.json()
        assert "validation error" in data["detail"][0]["msg"].lower()
    
    def test_reasoning_endpoints_authentication_required(self):
        """Test that authentication is required for reasoning endpoints."""
        client = TestClient(app)
        
        endpoints = [
            ("/api/v1/restaurants/recommend", {
                "restaurants": [
                    {
                        "id": "rest_001",
                        "name": "Test Restaurant",
                        "sentiment": {"likes": 85, "dislikes": 10, "neutral": 5}
                    }
                ]
            }),
            ("/api/v1/restaurants/analyze", {
                "restaurants": [
                    {
                        "id": "rest_001",
                        "name": "Test Restaurant",
                        "sentiment": {"likes": 85, "dislikes": 10, "neutral": 5}
                    }
                ]
            })
        ]
        
        for endpoint, payload in endpoints:
            response = client.post(endpoint, json=payload)
            assert response.status_code == 401
            data = response.json()
            assert data["success"] is False
            assert data["error"]["type"] == "AuthenticationError"
            assert "Authorization header required" in data["error"]["message"]