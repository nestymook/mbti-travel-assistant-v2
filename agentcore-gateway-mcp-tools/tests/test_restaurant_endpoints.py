"""
Integration tests for restaurant search endpoints.

This module contains comprehensive tests for all restaurant search API endpoints
including authentication, validation, and MCP integration.
"""

import pytest
import json
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from datetime import datetime, timezone

from main import app
from models.request_models import MealType, RankingMethod
from middleware.jwt_validator import UserContext


class TestRestaurantSearchEndpoints:
    """Test class for restaurant search endpoints."""
    
    def test_district_search_success(self, client_with_auth_bypass, mock_user_context, mock_mcp_client, auth_headers):
        """Test successful district search."""
        # Mock MCP response
        mock_response = {
            "restaurants": [
                {
                    "id": "rest_001",
                    "name": "Test Restaurant",
                    "district": "Central district",
                    "address": "123 Test St"
                }
            ],
            "metadata": {
                "total_count": 1,
                "districts": ["Central district"]
            }
        }
        mock_mcp_client.call_mcp_tool.return_value = mock_response
        
        response = client_with_auth_bypass.post(
            "/api/v1/restaurants/search/district",
            json={"districts": ["Central district", "Admiralty"]},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["metadata"]["total_results"] == 1
        assert data["metadata"]["search_criteria"]["districts"] == ["Central district", "Admiralty"]
        assert data["metadata"]["data_sources"] == ["mcp_restaurant_search"]
        
        # Verify MCP call
        mock_mcp_client.call_mcp_tool.assert_called_once_with(
            server_name="restaurant-search",
            tool_name="search_restaurants_by_district",
            parameters={"districts": ["Central district", "Admiralty"]},
            user_context={
                "user_id": "test-user-123",
                "username": "testuser",
                "email": "test@example.com",
                "token": "test-access-token"
            }
        )
    
    def test_district_search_validation_error(self, client, auth_headers):
        """Test district search with validation error."""
        with patch("api.restaurant_endpoints.get_current_user"):
            response = client.post(
                "/api/v1/restaurants/search/district",
                json={"districts": []},  # Empty districts list
                headers=auth_headers
            )
        
        assert response.status_code == 422
        data = response.json()
        assert "validation error" in data["detail"][0]["msg"].lower()
    
    def test_district_search_mcp_server_unavailable(self, client, mock_user_context, mock_mcp_client, auth_headers):
        """Test district search when MCP server is unavailable."""
        # Mock MCP server error
        mock_mcp_client.call_mcp_tool.side_effect = Exception("MCP server unavailable")
        
        with patch("api.restaurant_endpoints.get_current_user", return_value=mock_user_context), \
             patch("api.restaurant_endpoints.get_mcp_client_manager", return_value=mock_mcp_client):
            
            response = client.post(
                "/api/v1/restaurants/search/district",
                json={"districts": ["Central district"]},
                headers=auth_headers
            )
        
        assert response.status_code == 503
        data = response.json()
        assert data["detail"]["type"] == "ServiceUnavailable"
        assert "temporarily unavailable" in data["detail"]["message"]
        assert data["detail"]["retry_after"] == 30
    
    def test_meal_type_search_success(self, client, mock_user_context, mock_mcp_client, auth_headers):
        """Test successful meal type search."""
        # Mock MCP response
        mock_response = {
            "restaurants": [
                {
                    "id": "rest_001",
                    "name": "Breakfast Place",
                    "meal_types": ["breakfast", "lunch"]
                }
            ],
            "metadata": {
                "total_count": 1,
                "meal_types": ["breakfast", "lunch"]
            }
        }
        mock_mcp_client.call_mcp_tool.return_value = mock_response
        
        with patch("api.restaurant_endpoints.get_current_user", return_value=mock_user_context), \
             patch("api.restaurant_endpoints.get_mcp_client_manager", return_value=mock_mcp_client):
            
            response = client.post(
                "/api/v1/restaurants/search/meal-type",
                json={"meal_types": ["breakfast", "lunch"]},
                headers=auth_headers
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["metadata"]["total_results"] == 1
        assert data["metadata"]["search_criteria"]["meal_types"] == ["breakfast", "lunch"]
        assert data["metadata"]["data_sources"] == ["mcp_restaurant_search"]
        
        # Verify MCP call
        mock_mcp_client.call_mcp_tool.assert_called_once_with(
            server_name="restaurant-search",
            tool_name="search_restaurants_by_meal_type",
            parameters={"meal_types": ["breakfast", "lunch"]},
            user_context={
                "user_id": "test-user-123",
                "username": "testuser",
                "email": "test@example.com",
                "token": "test-access-token"
            }
        )
    
    def test_meal_type_search_invalid_meal_type(self, client, auth_headers):
        """Test meal type search with invalid meal type."""
        with patch("api.restaurant_endpoints.get_current_user"):
            response = client.post(
                "/api/v1/restaurants/search/meal-type",
                json={"meal_types": ["invalid_meal"]},
                headers=auth_headers
            )
        
        assert response.status_code == 422
        data = response.json()
        assert "validation error" in data["detail"][0]["msg"].lower()
    
    def test_combined_search_success(self, client, mock_user_context, mock_mcp_client, auth_headers):
        """Test successful combined search."""
        # Mock MCP response
        mock_response = {
            "restaurants": [
                {
                    "id": "rest_001",
                    "name": "Combined Restaurant",
                    "district": "Central district",
                    "meal_types": ["lunch"]
                }
            ],
            "metadata": {
                "total_count": 1,
                "districts": ["Central district"],
                "meal_types": ["lunch"]
            }
        }
        mock_mcp_client.call_mcp_tool.return_value = mock_response
        
        with patch("api.restaurant_endpoints.get_current_user", return_value=mock_user_context), \
             patch("api.restaurant_endpoints.get_mcp_client_manager", return_value=mock_mcp_client):
            
            response = client.post(
                "/api/v1/restaurants/search/combined",
                json={
                    "districts": ["Central district"],
                    "meal_types": ["lunch"]
                },
                headers=auth_headers
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["metadata"]["total_results"] == 1
        assert data["metadata"]["search_criteria"]["districts"] == ["Central district"]
        assert data["metadata"]["search_criteria"]["meal_types"] == ["lunch"]
        assert data["metadata"]["data_sources"] == ["mcp_restaurant_search"]
        
        # Verify MCP call
        mock_mcp_client.call_mcp_tool.assert_called_once_with(
            server_name="restaurant-search",
            tool_name="search_restaurants_combined",
            parameters={
                "districts": ["Central district"],
                "meal_types": ["lunch"]
            },
            user_context={
                "user_id": "test-user-123",
                "username": "testuser",
                "email": "test@example.com",
                "token": "test-access-token"
            }
        )
    
    def test_combined_search_districts_only(self, client, mock_user_context, mock_mcp_client, auth_headers):
        """Test combined search with districts only."""
        mock_response = {"restaurants": [], "metadata": {}}
        mock_mcp_client.call_mcp_tool.return_value = mock_response
        
        with patch("api.restaurant_endpoints.get_current_user", return_value=mock_user_context), \
             patch("api.restaurant_endpoints.get_mcp_client_manager", return_value=mock_mcp_client):
            
            response = client.post(
                "/api/v1/restaurants/search/combined",
                json={"districts": ["Central district"]},
                headers=auth_headers
            )
        
        assert response.status_code == 200
        
        # Verify MCP call parameters
        mock_mcp_client.call_mcp_tool.assert_called_once_with(
            server_name="restaurant-search",
            tool_name="search_restaurants_combined",
            parameters={"districts": ["Central district"]},
            user_context={
                "user_id": "test-user-123",
                "username": "testuser",
                "email": "test@example.com",
                "token": "test-access-token"
            }
        )
    
    def test_combined_search_meal_types_only(self, client, mock_user_context, mock_mcp_client, auth_headers):
        """Test combined search with meal types only."""
        mock_response = {"restaurants": [], "metadata": {}}
        mock_mcp_client.call_mcp_tool.return_value = mock_response
        
        with patch("api.restaurant_endpoints.get_current_user", return_value=mock_user_context), \
             patch("api.restaurant_endpoints.get_mcp_client_manager", return_value=mock_mcp_client):
            
            response = client.post(
                "/api/v1/restaurants/search/combined",
                json={"meal_types": ["dinner"]},
                headers=auth_headers
            )
        
        assert response.status_code == 200
        
        # Verify MCP call parameters
        mock_mcp_client.call_mcp_tool.assert_called_once_with(
            server_name="restaurant-search",
            tool_name="search_restaurants_combined",
            parameters={"meal_types": ["dinner"]},
            user_context={
                "user_id": "test-user-123",
                "username": "testuser",
                "email": "test@example.com",
                "token": "test-access-token"
            }
        )
    
    def test_combined_search_no_filters(self, client, auth_headers):
        """Test combined search with no filters provided."""
        with patch("api.restaurant_endpoints.get_current_user"):
            response = client.post(
                "/api/v1/restaurants/search/combined",
                json={},
                headers=auth_headers
            )
        
        assert response.status_code == 422
        data = response.json()
        assert "At least one of 'districts' or 'meal_types' must be provided" in str(data)
    
    def test_recommend_restaurants_success(self, client_with_auth_bypass, mock_user_context, mock_mcp_client, auth_headers):
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
        
        response = client_with_auth_bypass.post(
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
    
    def test_recommend_restaurants_invalid_sentiment(self, client, auth_headers):
        """Test restaurant recommendation with invalid sentiment data."""
        with patch("api.restaurant_endpoints.get_current_user"):
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
    
    def test_analyze_sentiment_success(self, client_with_auth_bypass, mock_user_context, mock_mcp_client, auth_headers):
        """Test successful sentiment analysis."""
        # Mock MCP response
        mock_response = {
            "sentiment_analysis": {
                "average_likes": 77.5,
                "average_dislikes": 15.0,
                "average_neutral": 7.5,
                "total_restaurants": 2
            },
            "restaurant_count": 2,
            "ranking_method": "sentiment_likes"
        }
        mock_mcp_client.call_mcp_tool.return_value = mock_response
        
        response = client_with_auth_bypass.post(
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
    
    def test_analyze_sentiment_duplicate_ids(self, client, auth_headers):
        """Test sentiment analysis with duplicate restaurant IDs."""
        with patch("api.restaurant_endpoints.get_current_user"):
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
                            "id": "rest_001",  # Duplicate ID
                            "name": "Restaurant B",
                            "sentiment": {"likes": 70, "dislikes": 20, "neutral": 10}
                        }
                    ]
                },
                headers=auth_headers
            )
        
        assert response.status_code == 422
        data = response.json()
        assert "Restaurant IDs must be unique" in str(data)
    
    def test_authentication_required(self, client):
        """Test that authentication is required for all endpoints."""
        endpoints = [
            ("/api/v1/restaurants/search/district", {"districts": ["Central district"]}),
            ("/api/v1/restaurants/search/meal-type", {"meal_types": ["lunch"]}),
            ("/api/v1/restaurants/search/combined", {"districts": ["Central district"]}),
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
    
    def test_invalid_jwt_token(self, client):
        """Test endpoints with invalid JWT token."""
        invalid_headers = {"Authorization": "Bearer invalid-token"}
        
        with patch("api.restaurant_endpoints.get_current_user") as mock_get_user:
            mock_get_user.side_effect = Exception("Invalid JWT token")
            
            response = client.post(
                "/api/v1/restaurants/search/district",
                json={"districts": ["Central district"]},
                headers=invalid_headers
            )
        
        assert response.status_code == 500  # Exception handling in middleware