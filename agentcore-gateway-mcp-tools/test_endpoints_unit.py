#!/usr/bin/env python3
"""
Unit tests for restaurant search endpoints without MCP server dependencies.

This script tests the endpoint logic without requiring actual MCP servers
by mocking all external dependencies.
"""

import sys
import json
from pathlib import Path
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from datetime import datetime, timezone

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Mock the MCP client manager before importing the main app
with patch('services.mcp_client_manager.get_mcp_client_manager') as mock_get_mcp:
    mock_mcp_client = AsyncMock()
    mock_get_mcp.return_value = mock_mcp_client
    
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

def test_district_search_validation():
    """Test district search request validation."""
    print("🔍 Testing district search validation...")
    
    client = TestClient(app)
    
    # Test empty districts list
    response = client.post(
        "/api/v1/restaurants/search/district",
        json={"districts": []}
    )
    
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data
    
    print("✅ District search validation test passed")

def test_meal_type_search_validation():
    """Test meal type search request validation."""
    print("🔍 Testing meal type search validation...")
    
    client = TestClient(app)
    
    # Test invalid meal type
    response = client.post(
        "/api/v1/restaurants/search/meal-type",
        json={"meal_types": ["invalid_meal"]}
    )
    
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data
    
    print("✅ Meal type search validation test passed")

def test_combined_search_validation():
    """Test combined search request validation."""
    print("🔍 Testing combined search validation...")
    
    client = TestClient(app)
    
    # Test no filters provided
    response = client.post(
        "/api/v1/restaurants/search/combined",
        json={}
    )
    
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data
    
    print("✅ Combined search validation test passed")

def test_recommendation_validation():
    """Test restaurant recommendation request validation."""
    print("🔍 Testing recommendation validation...")
    
    client = TestClient(app)
    
    # Test empty restaurants list
    response = client.post(
        "/api/v1/restaurants/recommend",
        json={"restaurants": []}
    )
    
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data
    
    print("✅ Recommendation validation test passed")

def test_sentiment_analysis_validation():
    """Test sentiment analysis request validation."""
    print("🔍 Testing sentiment analysis validation...")
    
    client = TestClient(app)
    
    # Test invalid sentiment data
    response = client.post(
        "/api/v1/restaurants/analyze",
        json={
            "restaurants": [
                {
                    "id": "rest_001",
                    "name": "Test Restaurant",
                    "sentiment": {"likes": -5}  # Missing required fields and negative value
                }
            ]
        }
    )
    
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data
    
    print("✅ Sentiment analysis validation test passed")

def test_authentication_required():
    """Test that authentication is required."""
    print("🔍 Testing authentication requirement...")
    
    client = TestClient(app)
    
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
    
    print("✅ Authentication requirement test passed")

def test_openapi_docs():
    """Test that OpenAPI documentation is available."""
    print("🔍 Testing OpenAPI documentation...")
    
    client = TestClient(app)
    
    # Test OpenAPI JSON
    response = client.get("/openapi.json")
    assert response.status_code == 200
    data = response.json()
    assert "openapi" in data
    assert "info" in data
    assert data["info"]["title"] == "AgentCore Gateway for MCP Tools"
    
    # Test Swagger UI
    response = client.get("/docs")
    assert response.status_code == 200
    
    print("✅ OpenAPI documentation test passed")

def test_endpoint_structure():
    """Test that all expected endpoints are available."""
    print("🔍 Testing endpoint structure...")
    
    client = TestClient(app)
    
    # Get OpenAPI spec to check endpoints
    response = client.get("/openapi.json")
    assert response.status_code == 200
    openapi_spec = response.json()
    
    # Check that all expected paths exist
    expected_paths = [
        "/health",
        "/",
        "/auth/test",
        "/api/v1/restaurants/search/district",
        "/api/v1/restaurants/search/meal-type",
        "/api/v1/restaurants/search/combined",
        "/api/v1/restaurants/recommend",
        "/api/v1/restaurants/analyze",
        "/tools/metadata"
    ]
    
    paths = openapi_spec.get("paths", {})
    for expected_path in expected_paths:
        assert expected_path in paths, f"Expected path {expected_path} not found in OpenAPI spec"
    
    print("✅ Endpoint structure test passed")

def run_all_tests():
    """Run all unit tests."""
    print("🚀 Running AgentCore Gateway Unit Tests")
    print("=" * 60)
    
    tests = [
        test_health_endpoint,
        test_root_endpoint,
        test_district_search_validation,
        test_meal_type_search_validation,
        test_combined_search_validation,
        test_recommendation_validation,
        test_sentiment_analysis_validation,
        test_authentication_required,
        test_openapi_docs,
        test_endpoint_structure
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
        print("🎉 All unit tests passed!")
        return True
    else:
        print("🔧 Some tests need attention")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)