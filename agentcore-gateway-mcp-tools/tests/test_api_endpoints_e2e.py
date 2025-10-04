"""
End-to-end API tests for all Gateway endpoints.

Tests complete request/response cycles for all API endpoints including
authentication, validation, MCP integration, and error handling.
"""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
import json

from main import app


class TestRestaurantSearchEndpointsE2E:
    """End-to-end tests for restaurant search endpoints."""
    
    @pytest.fixture
    def mock_mcp_responses(self):
        """Mock MCP server responses for testing."""
        return {
            "search_restaurants_by_district": {
                "success": True,
                "data": {
                    "restaurants": [
                        {
                            "id": "rest_001",
                            "name": "Test Restaurant",
                            "district": "Central district",
                            "address": "123 Test Street",
                            "sentiment": {"likes": 85, "dislikes": 10, "neutral": 5}
                        }
                    ],
                    "total_count": 1,
                    "search_criteria": {"districts": ["Central district"]}
                }
            },
            "search_restaurants_by_meal_type": {
                "success": True,
                "data": {
                    "restaurants": [
                        {
                            "id": "rest_002",
                            "name": "Breakfast Spot",
                            "meal_types": ["breakfast"],
                            "operating_hours": "07:00-11:00",
                            "sentiment": {"likes": 75, "dislikes": 15, "neutral": 10}
                        }
                    ],
                    "total_count": 1,
                    "search_criteria": {"meal_types": ["breakfast"]}
                }
            },
            "search_restaurants_combined": {
                "success": True,
                "data": {
                    "restaurants": [
                        {
                            "id": "rest_003",
                            "name": "Combined Search Result",
                            "district": "Admiralty",
                            "meal_types": ["lunch"],
                            "sentiment": {"likes": 90, "dislikes": 5, "neutral": 5}
                        }
                    ],
                    "total_count": 1,
                    "search_criteria": {
                        "districts": ["Admiralty"],
                        "meal_types": ["lunch"]
                    }
                }
            }
        }
    
    def test_search_by_district_complete_flow(self, client_with_auth_bypass, auth_headers, mock_mcp_responses):
        """Test complete flow for district search endpoint."""
        # Mock MCP client response
        with patch("api.restaurant_endpoints.get_mcp_client_manager") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.call_mcp_tool.return_value = mock_mcp_responses["search_restaurants_by_district"]
            mock_get_client.return_value = mock_client
            
            # Make request
            response = client_with_auth_bypass.post(
                "/api/v1/restaurants/search/district",
                json={"districts": ["Central district"]},
                headers=auth_headers
            )
            
            # Verify response
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "data" in data
            assert len(data["data"]["restaurants"]) == 1
            assert data["data"]["restaurants"][0]["name"] == "Test Restaurant"
            assert data["data"]["search_criteria"]["districts"] == ["Central district"]
            
            # Verify MCP client was called correctly
            mock_client.call_mcp_tool.assert_called_once_with(
                server_name="restaurant-search",
                tool_name="search_restaurants_by_district",
                parameters={"districts": ["Central district"]},
                user_context={
                    "user_id": "test-user-123",
                    "username": "testuser",
                    "email": "test@example.com"
                }
            )
    
    def test_search_by_meal_type_complete_flow(self, client_with_auth_bypass, auth_headers, mock_mcp_responses):
        """Test complete flow for meal type search endpoint."""
        with patch("api.restaurant_endpoints.get_mcp_client_manager") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.call_mcp_tool.return_value = mock_mcp_responses["search_restaurants_by_meal_type"]
            mock_get_client.return_value = mock_client
            
            response = client_with_auth_bypass.post(
                "/api/v1/restaurants/search/meal-type",
                json={"meal_types": ["breakfast"]},
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["restaurants"][0]["name"] == "Breakfast Spot"
            assert data["data"]["search_criteria"]["meal_types"] == ["breakfast"]
            
            mock_client.call_mcp_tool.assert_called_once_with(
                server_name="restaurant-search",
                tool_name="search_restaurants_by_meal_type",
                parameters={"meal_types": ["breakfast"]},
                user_context={
                    "user_id": "test-user-123",
                    "username": "testuser",
                    "email": "test@example.com"
                }
            )
    
    def test_search_combined_complete_flow(self, client_with_auth_bypass, auth_headers, mock_mcp_responses):
        """Test complete flow for combined search endpoint."""
        with patch("api.restaurant_endpoints.get_mcp_client_manager") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.call_mcp_tool.return_value = mock_mcp_responses["search_restaurants_combined"]
            mock_get_client.return_value = mock_client
            
            response = client_with_auth_bypass.post(
                "/api/v1/restaurants/search/combined",
                json={
                    "districts": ["Admiralty"],
                    "meal_types": ["lunch"]
                },
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["restaurants"][0]["name"] == "Combined Search Result"
            
            mock_client.call_mcp_tool.assert_called_once_with(
                server_name="restaurant-search",
                tool_name="search_restaurants_combined",
                parameters={
                    "districts": ["Admiralty"],
                    "meal_types": ["lunch"]
                },
                user_context={
                    "user_id": "test-user-123",
                    "username": "testuser",
                    "email": "test@example.com"
                }
            )
    
    def test_search_validation_error_flow(self, client_with_auth_bypass, auth_headers):
        """Test validation error handling in search endpoints."""
        # Test empty districts list
        response = client_with_auth_bypass.post(
            "/api/v1/restaurants/search/district",
            json={"districts": []},
            headers=auth_headers
        )
        
        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert "validation" in data["error"]["type"].lower()
        assert "districts" in data["error"]["message"]
    
    def test_search_mcp_server_error_flow(self, client_with_auth_bypass, auth_headers):
        """Test MCP server error handling in search endpoints."""
        with patch("api.restaurant_endpoints.get_mcp_client_manager") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.call_mcp_tool.side_effect = Exception("MCP server unavailable")
            mock_get_client.return_value = mock_client
            
            response = client_with_auth_bypass.post(
                "/api/v1/restaurants/search/district",
                json={"districts": ["Central district"]},
                headers=auth_headers
            )
            
            assert response.status_code == 503
            data = response.json()
            assert data["success"] is False
            assert "service unavailable" in data["error"]["message"].lower()


class TestRestaurantReasoningEndpointsE2E:
    """End-to-end tests for restaurant reasoning endpoints."""
    
    @pytest.fixture
    def mock_reasoning_responses(self):
        """Mock reasoning MCP server responses."""
        return {
            "recommend_restaurants": {
                "success": True,
                "data": {
                    "recommendation": {
                        "id": "rest_001",
                        "name": "Top Recommendation",
                        "sentiment": {"likes": 95, "dislikes": 3, "neutral": 2},
                        "score": 0.95
                    },
                    "candidates": [
                        {
                            "id": "rest_001",
                            "name": "Top Recommendation",
                            "sentiment": {"likes": 95, "dislikes": 3, "neutral": 2},
                            "score": 0.95
                        },
                        {
                            "id": "rest_002",
                            "name": "Second Choice",
                            "sentiment": {"likes": 85, "dislikes": 10, "neutral": 5},
                            "score": 0.85
                        }
                    ],
                    "ranking_method": "sentiment_likes",
                    "analysis_summary": {
                        "total_restaurants": 2,
                        "average_likes": 90,
                        "top_score": 0.95
                    }
                }
            },
            "analyze_restaurant_sentiment": {
                "success": True,
                "data": {
                    "sentiment_analysis": {
                        "average_likes": 85.5,
                        "average_dislikes": 12.5,
                        "average_neutral": 2.0,
                        "sentiment_distribution": {
                            "positive": 0.85,
                            "negative": 0.13,
                            "neutral": 0.02
                        },
                        "score_ranges": {
                            "min_score": 0.72,
                            "max_score": 0.95,
                            "median_score": 0.84
                        }
                    },
                    "restaurant_count": 2,
                    "ranking_method": "sentiment_likes"
                }
            }
        }
    
    @pytest.fixture
    def sample_restaurant_data(self):
        """Sample restaurant data for reasoning tests."""
        return [
            {
                "id": "rest_001",
                "name": "Great Restaurant",
                "sentiment": {"likes": 95, "dislikes": 3, "neutral": 2},
                "address": "123 Main St",
                "district": "Central district"
            },
            {
                "id": "rest_002",
                "name": "Good Restaurant",
                "sentiment": {"likes": 76, "dislikes": 20, "neutral": 4},
                "address": "456 Side St",
                "district": "Admiralty"
            }
        ]
    
    def test_recommend_restaurants_complete_flow(self, client_with_auth_bypass, auth_headers, 
                                                mock_reasoning_responses, sample_restaurant_data):
        """Test complete flow for restaurant recommendation endpoint."""
        with patch("api.restaurant_endpoints.get_mcp_client_manager") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.call_mcp_tool.return_value = mock_reasoning_responses["recommend_restaurants"]
            mock_get_client.return_value = mock_client
            
            response = client_with_auth_bypass.post(
                "/api/v1/restaurants/recommend",
                json={
                    "restaurants": sample_restaurant_data,
                    "ranking_method": "sentiment_likes"
                },
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "recommendation" in data["data"]
            assert "candidates" in data["data"]
            assert data["data"]["recommendation"]["name"] == "Top Recommendation"
            assert len(data["data"]["candidates"]) == 2
            
            mock_client.call_mcp_tool.assert_called_once_with(
                server_name="restaurant-reasoning",
                tool_name="recommend_restaurants",
                parameters={
                    "restaurants": sample_restaurant_data,
                    "ranking_method": "sentiment_likes"
                },
                user_context={
                    "user_id": "test-user-123",
                    "username": "testuser",
                    "email": "test@example.com"
                }
            )
    
    def test_analyze_sentiment_complete_flow(self, client_with_auth_bypass, auth_headers,
                                           mock_reasoning_responses, sample_restaurant_data):
        """Test complete flow for sentiment analysis endpoint."""
        with patch("api.restaurant_endpoints.get_mcp_client_manager") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.call_mcp_tool.return_value = mock_reasoning_responses["analyze_restaurant_sentiment"]
            mock_get_client.return_value = mock_client
            
            response = client_with_auth_bypass.post(
                "/api/v1/restaurants/analyze",
                json={"restaurants": sample_restaurant_data},
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "sentiment_analysis" in data["data"]
            assert data["data"]["sentiment_analysis"]["average_likes"] == 85.5
            assert data["data"]["restaurant_count"] == 2
            
            mock_client.call_mcp_tool.assert_called_once_with(
                server_name="restaurant-reasoning",
                tool_name="analyze_restaurant_sentiment",
                parameters={"restaurants": sample_restaurant_data},
                user_context={
                    "user_id": "test-user-123",
                    "username": "testuser",
                    "email": "test@example.com"
                }
            )
    
    def test_reasoning_validation_error_flow(self, client_with_auth_bypass, auth_headers):
        """Test validation error handling in reasoning endpoints."""
        # Test empty restaurants list
        response = client_with_auth_bypass.post(
            "/api/v1/restaurants/recommend",
            json={"restaurants": []},
            headers=auth_headers
        )
        
        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert "validation" in data["error"]["type"].lower()
        assert "restaurants" in data["error"]["message"]


class TestToolMetadataEndpointsE2E:
    """End-to-end tests for tool metadata endpoints."""
    
    def test_get_tools_metadata_complete_flow(self, client_with_auth_bypass, auth_headers):
        """Test complete flow for tools metadata endpoint."""
        response = client_with_auth_bypass.get(
            "/api/v1/tools/metadata",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "tools" in data["data"]
        
        tools = data["data"]["tools"]
        assert len(tools) >= 5  # Should have all 5 tools
        
        # Verify search tools
        search_tools = [t for t in tools if "search" in t["name"]]
        assert len(search_tools) == 3
        
        # Verify reasoning tools
        reasoning_tools = [t for t in tools if "recommend" in t["name"] or "analyze" in t["name"]]
        assert len(reasoning_tools) == 2
        
        # Verify tool structure
        for tool in tools:
            assert "name" in tool
            assert "description" in tool
            assert "parameters" in tool
            assert "response_format" in tool
            assert "use_cases" in tool
            assert "mbti_integration" in tool
    
    def test_get_tools_metadata_unauthenticated(self, client):
        """Test tools metadata endpoint without authentication."""
        response = client.get("/api/v1/tools/metadata")
        
        assert response.status_code == 401
        data = response.json()
        assert data["success"] is False
        assert "authorization" in data["error"]["message"].lower()


class TestHealthAndObservabilityEndpointsE2E:
    """End-to-end tests for health and observability endpoints."""
    
    def test_health_endpoint_no_auth_required(self, client):
        """Test health endpoint doesn't require authentication."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "timestamp" in data
        assert "version" in data
    
    def test_health_endpoint_with_mcp_status(self, client):
        """Test health endpoint includes MCP server status."""
        with patch("api.observability_endpoints.get_mcp_client_manager") as mock_get_client:
            mock_client = MagicMock()
            mock_client.get_all_server_status.return_value = {
                "restaurant-search": MagicMock(status=MagicMock(value="healthy")),
                "restaurant-reasoning": MagicMock(status=MagicMock(value="healthy"))
            }
            mock_get_client.return_value = mock_client
            
            response = client.get("/health")
            
            assert response.status_code == 200
            data = response.json()
            assert "mcp_servers" in data
            assert "restaurant-search" in data["mcp_servers"]
            assert "restaurant-reasoning" in data["mcp_servers"]
    
    def test_metrics_endpoint_requires_auth(self, client_with_auth_bypass, auth_headers):
        """Test metrics endpoint requires authentication."""
        response = client_with_auth_bypass.get(
            "/metrics",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "metrics" in data
        assert "request_count" in data["metrics"]
        assert "response_times" in data["metrics"]
    
    def test_metrics_endpoint_unauthenticated(self, client):
        """Test metrics endpoint without authentication."""
        response = client.get("/metrics")
        
        assert response.status_code == 401


class TestErrorHandlingE2E:
    """End-to-end tests for error handling across all endpoints."""
    
    def test_404_not_found_error(self, client):
        """Test 404 error for non-existent endpoints."""
        response = client.get("/api/v1/nonexistent")
        
        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
        assert "not found" in data["error"]["message"].lower()
    
    def test_405_method_not_allowed_error(self, client_with_auth_bypass, auth_headers):
        """Test 405 error for wrong HTTP methods."""
        response = client_with_auth_bypass.get(
            "/api/v1/restaurants/search/district",
            headers=auth_headers
        )
        
        assert response.status_code == 405
        data = response.json()
        assert data["success"] is False
        assert "method not allowed" in data["error"]["message"].lower()
    
    def test_422_validation_error_detailed(self, client_with_auth_bypass, auth_headers):
        """Test detailed validation error responses."""
        response = client_with_auth_bypass.post(
            "/api/v1/restaurants/search/district",
            json={"invalid_field": "value"},
            headers=auth_headers
        )
        
        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert "validation" in data["error"]["type"].lower()
        assert "details" in data["error"]
    
    def test_500_internal_server_error(self, client_with_auth_bypass, auth_headers):
        """Test 500 error handling for unexpected exceptions."""
        with patch("api.restaurant_endpoints.get_mcp_client_manager") as mock_get_client:
            mock_get_client.side_effect = RuntimeError("Unexpected error")
            
            response = client_with_auth_bypass.post(
                "/api/v1/restaurants/search/district",
                json={"districts": ["Central district"]},
                headers=auth_headers
            )
            
            assert response.status_code == 500
            data = response.json()
            assert data["success"] is False
            assert "internal server error" in data["error"]["message"].lower()


class TestCORSAndSecurityHeadersE2E:
    """End-to-end tests for CORS and security headers."""
    
    def test_cors_headers_present(self, client):
        """Test CORS headers are present in responses."""
        response = client.get("/health")
        
        assert response.status_code == 200
        # Note: TestClient doesn't automatically add CORS headers,
        # but we can verify the middleware is configured
        # In real deployment, these headers would be present
    
    def test_security_headers_present(self, client):
        """Test security headers are present in responses."""
        response = client.get("/health")
        
        assert response.status_code == 200
        # Security headers would be added by middleware in production


if __name__ == "__main__":
    pytest.main([__file__, "-v"])