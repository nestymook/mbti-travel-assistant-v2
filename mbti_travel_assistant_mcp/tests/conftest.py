"""
Pytest configuration and fixtures for MBTI Travel Assistant MCP tests.

This module provides common test fixtures and configuration for the test suite,
including mock services, test data, and test environment setup.
"""

import pytest
import asyncio
from typing import Dict, Any, List
from unittest.mock import Mock, AsyncMock
from datetime import datetime

# Test data and fixtures
from config.settings import ApplicationSettings
from models.restaurant_models import Restaurant, Sentiment
from models.request_models import RecommendationRequest


@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_settings():
    """Provide test configuration settings."""
    return ApplicationSettings(
        environment="test",
        mcp_client=ApplicationSettings.MCPClientSettings(
            search_mcp_endpoint="http://test-search:8000",
            reasoning_mcp_endpoint="http://test-reasoning:8000",
            mcp_connection_timeout=10,
            mcp_retry_attempts=1
        ),
        authentication=ApplicationSettings.AuthenticationSettings(
            cognito_user_pool_id="us-east-1_test123",
            cognito_region="us-east-1",
            jwt_algorithm="RS256",
            token_cache_ttl=60
        ),
        cache=ApplicationSettings.CacheSettings(
            cache_enabled=False,  # Disable cache for tests
            cache_ttl=300
        ),
        agentcore=ApplicationSettings.AgentCoreSettings(
            runtime_port=8080,
            agent_model="anthropic.claude-3-5-sonnet-20241022-v2:0",
            agent_temperature=0.1,
            agent_max_tokens=1000
        ),
        logging=ApplicationSettings.LoggingSettings(
            log_level="DEBUG",
            log_format="text",
            tracing_enabled=False,
            metrics_enabled=False
        )
    )


@pytest.fixture
def sample_restaurant():
    """Provide a sample restaurant object for testing."""
    return Restaurant(
        id="rest_001",
        name="Test Restaurant",
        address="123 Test Street",
        district="Central district",
        meal_type=["breakfast", "lunch"],
        sentiment=Sentiment(likes=85, dislikes=10, neutral=5),
        price_range="$$",
        operating_hours={
            "monday": ["07:00-11:30", "12:00-15:00"],
            "tuesday": ["07:00-11:30", "12:00-15:00"]
        },
        location_category="urban"
    )


@pytest.fixture
def sample_restaurants(sample_restaurant):
    """Provide a list of sample restaurants for testing."""
    restaurants = []
    
    for i in range(20):
        restaurant = Restaurant(
            id=f"rest_{i:03d}",
            name=f"Test Restaurant {i+1}",
            address=f"{100+i} Test Street",
            district="Central district",
            meal_type=["breakfast", "lunch"],
            sentiment=Sentiment(
                likes=80 - i,
                dislikes=10 + i//2,
                neutral=5 + i//3
            ),
            price_range="$$" if i % 2 == 0 else "$$$",
            operating_hours={
                "monday": ["07:00-11:30", "12:00-15:00"],
                "tuesday": ["07:00-11:30", "12:00-15:00"]
            },
            location_category="urban"
        )
        restaurants.append(restaurant)
    
    return restaurants


@pytest.fixture
def sample_request():
    """Provide a sample recommendation request for testing."""
    return RecommendationRequest(
        district="Central district",
        meal_time="breakfast"
    )


@pytest.fixture
def sample_payload():
    """Provide a sample HTTP payload for testing."""
    return {
        "district": "Central district",
        "meal_time": "breakfast",
        "auth_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.test.token"
    }


@pytest.fixture
def mock_auth_service():
    """Provide a mock authentication service."""
    mock_service = Mock()
    mock_service.validate_token.return_value = {
        "sub": "test-user-123",
        "email": "test@example.com",
        "aud": "test-client-id"
    }
    return mock_service


@pytest.fixture
def mock_mcp_client_manager():
    """Provide a mock MCP client manager."""
    mock_manager = Mock()
    
    # Mock search restaurants method
    async def mock_search_restaurants(district, meal_time):
        return [
            {
                "id": f"rest_{i:03d}",
                "name": f"Restaurant {i+1}",
                "district": district,
                "meal_type": [meal_time],
                "sentiment": {"likes": 80-i, "dislikes": 10, "neutral": 5}
            }
            for i in range(20)
        ]
    
    mock_manager.search_restaurants = AsyncMock(side_effect=mock_search_restaurants)
    
    # Mock analyze restaurants method
    async def mock_analyze_restaurants(restaurants):
        return {
            "recommendation": restaurants[0] if restaurants else None,
            "candidates": restaurants[1:20] if len(restaurants) > 1 else [],
            "ranking_method": "sentiment_likes"
        }
    
    mock_manager.analyze_restaurants = AsyncMock(side_effect=mock_analyze_restaurants)
    
    return mock_manager


@pytest.fixture
def mock_restaurant_agent():
    """Provide a mock restaurant agent."""
    mock_agent = Mock()
    
    async def mock_process_request(district, meal_time, user_context=None, correlation_id=None):
        return {
            "recommendation": {
                "id": "rest_001",
                "name": "Best Restaurant",
                "district": district,
                "meal_type": [meal_time],
                "sentiment": {"likes": 95, "dislikes": 3, "neutral": 2}
            },
            "candidates": [
                {
                    "id": f"rest_{i:03d}",
                    "name": f"Restaurant {i+1}",
                    "district": district,
                    "meal_type": [meal_time],
                    "sentiment": {"likes": 80-i, "dislikes": 10, "neutral": 5}
                }
                for i in range(1, 20)
            ]
        }
    
    mock_agent.process_request = AsyncMock(side_effect=mock_process_request)
    
    return mock_agent


@pytest.fixture
def mock_cache_service():
    """Provide a mock cache service."""
    mock_service = Mock()
    mock_service.get_cached_response.return_value = None
    mock_service.cache_response.return_value = None
    return mock_service


@pytest.fixture
def mock_response_formatter():
    """Provide a mock response formatter."""
    mock_formatter = Mock()
    
    def mock_format_response(response_data, request, start_time, correlation_id):
        return {
            "recommendation": response_data.get("recommendation"),
            "candidates": response_data.get("candidates", []),
            "metadata": {
                "search_criteria": {
                    "district": request.district,
                    "meal_time": request.meal_time
                },
                "total_found": len(response_data.get("candidates", [])) + 1,
                "timestamp": datetime.utcnow().isoformat(),
                "processing_time_ms": 1000,
                "correlation_id": correlation_id
            }
        }
    
    mock_formatter.format_response.side_effect = mock_format_response
    
    return mock_formatter


@pytest.fixture
def mock_error_handler():
    """Provide a mock error handler."""
    mock_handler = Mock()
    
    def mock_handle_error(error, correlation_id):
        return {
            "error": {
                "error_type": "test_error",
                "message": str(error),
                "suggested_actions": ["Try again"],
                "error_code": "TEST_001",
                "correlation_id": correlation_id
            }
        }
    
    mock_handler.handle_error.side_effect = mock_handle_error
    
    return mock_handler


@pytest.fixture
def jwt_token():
    """Provide a sample JWT token for testing."""
    return "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsImtpZCI6InRlc3Qta2V5In0.eyJzdWIiOiJ0ZXN0LXVzZXItMTIzIiwiYXVkIjoidGVzdC1jbGllbnQtaWQiLCJpc3MiOiJodHRwczovL2NvZ25pdG8taWRwLnVzLWVhc3QtMS5hbWF6b25hd3MuY29tL3VzLWVhc3QtMV90ZXN0MTIzIiwiZXhwIjo5OTk5OTk5OTk5LCJpYXQiOjE2MDAwMDAwMDAsImVtYWlsIjoidGVzdEBleGFtcGxlLmNvbSJ9.test-signature"


@pytest.fixture
def mcp_search_response():
    """Provide a sample MCP search response."""
    return {
        "restaurants": [
            {
                "id": f"rest_{i:03d}",
                "name": f"Restaurant {i+1}",
                "address": f"{100+i} Main Street",
                "district": "Central district",
                "meal_type": ["breakfast"],
                "sentiment": {
                    "likes": 80 - i,
                    "dislikes": 10 + i//2,
                    "neutral": 5 + i//3
                },
                "price_range": "$$",
                "operating_hours": {
                    "monday": ["07:00-11:30"]
                },
                "location_category": "urban"
            }
            for i in range(25)
        ],
        "total_found": 25,
        "search_criteria": {
            "districts": ["Central district"],
            "meal_types": ["breakfast"]
        }
    }


@pytest.fixture
def mcp_reasoning_response():
    """Provide a sample MCP reasoning response."""
    return {
        "recommendation": {
            "id": "rest_001",
            "name": "Top Restaurant",
            "sentiment": {"likes": 95, "dislikes": 3, "neutral": 2}
        },
        "candidates": [
            {
                "id": f"rest_{i:03d}",
                "name": f"Restaurant {i+1}",
                "sentiment": {"likes": 80-i, "dislikes": 10, "neutral": 5}
            }
            for i in range(1, 20)
        ],
        "ranking_method": "sentiment_likes",
        "analysis_summary": {
            "total_restaurants": 20,
            "avg_sentiment_score": 75.5
        }
    }


# Test utilities
class TestUtils:
    """Utility functions for testing."""
    
    @staticmethod
    def create_test_restaurant(
        restaurant_id: str = "test_001",
        name: str = "Test Restaurant",
        district: str = "Central district",
        likes: int = 80,
        dislikes: int = 10,
        neutral: int = 5
    ) -> Restaurant:
        """Create a test restaurant with specified parameters."""
        return Restaurant(
            id=restaurant_id,
            name=name,
            address="123 Test Street",
            district=district,
            meal_type=["breakfast", "lunch"],
            sentiment=Sentiment(likes=likes, dislikes=dislikes, neutral=neutral),
            price_range="$$",
            operating_hours={
                "monday": ["07:00-11:30", "12:00-15:00"]
            },
            location_category="urban"
        )
    
    @staticmethod
    def create_test_payload(
        district: str = "Central district",
        meal_time: str = "breakfast",
        include_auth: bool = True
    ) -> Dict[str, Any]:
        """Create a test request payload."""
        payload = {
            "district": district,
            "meal_time": meal_time
        }
        
        if include_auth:
            payload["auth_token"] = "test.jwt.token"
        
        return payload


@pytest.fixture
def test_utils():
    """Provide test utility functions."""
    return TestUtils