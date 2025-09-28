"""
Comprehensive Integration Tests for BedrockAgentCore Entrypoint

Tests the complete entrypoint functionality including request processing,
authentication integration, MCP orchestration, and response formatting.
"""

import pytest
import json
import asyncio
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock, MagicMock

# Import main entrypoint
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import process_restaurant_request
from models.restaurant_models import Restaurant, Sentiment
from models.auth_models import JWTClaims, UserContext


class TestEntrypointIntegration:
    """Integration tests for BedrockAgentCore entrypoint functionality."""
    
    @pytest.fixture
    def sample_restaurants(self):
        """Create sample restaurant data for testing."""
        return [
            Restaurant(
                id="rest_001",
                name="Central Breakfast Cafe",
                address="123 Central Street",
                district="Central district",
                meal_type=["breakfast"],
                sentiment=Sentiment(likes=85, dislikes=10, neutral=5),
                price_range="$",
                operating_hours={"Monday": ["07:00", "11:30"]},
                location_category="Shopping Mall"
            ),
            Restaurant(
                id="rest_002",
                name="Morning Delights",
                address="456 Central Avenue",
                district="Central district",
                meal_type=["breakfast"],
                sentiment=Sentiment(likes=75, dislikes=15, neutral=10),
                price_range="$$",
                operating_hours={"Monday": ["06:30", "12:00"]},
                location_category="Street Food"
            )
        ]
    
    @pytest.fixture
    def sample_reasoning_results(self, sample_restaurants):
        """Create sample reasoning results."""
        return {
            "recommendation": {
                "id": "rest_001",
                "name": "Central Breakfast Cafe",
                "address": "123 Central Street",
                "district": "Central district",
                "meal_type": ["breakfast"],
                "sentiment": {"likes": 85, "dislikes": 10, "neutral": 5},
                "price_range": "$",
                "operating_hours": {"Monday": ["07:00", "11:30"]},
                "location_category": "Shopping Mall"
            },
            "candidates": [
                {
                    "id": "rest_002",
                    "name": "Morning Delights",
                    "address": "456 Central Avenue",
                    "district": "Central district",
                    "meal_type": ["breakfast"],
                    "sentiment": {"likes": 75, "dislikes": 15, "neutral": 10},
                    "price_range": "$$",
                    "operating_hours": {"Monday": ["06:30", "12:00"]},
                    "location_category": "Street Food"
                }
            ],
            "ranking_method": "sentiment_likes",
            "analysis_summary": {
                "total_restaurants": 2,
                "average_sentiment": 80.0
            }
        }
    
    @pytest.fixture
    def jwt_claims(self):
        """Create test JWT claims."""
        return JWTClaims(
            user_id="test-user-123",
            username="testuser",
            email="test@example.com",
            client_id="test-client-id",
            token_use="access",
            exp=int((datetime.utcnow()).timestamp()) + 3600,
            iat=int(datetime.utcnow().timestamp()),
            iss="https://cognito-idp.us-east-1.amazonaws.com/us-east-1_test123",
            aud="test-client-id"
        )
    
    def test_entrypoint_basic_request_processing(self, sample_restaurants, sample_reasoning_results):
        """Test basic request processing through entrypoint."""
        payload = {
            "district": "Central district",
            "meal_time": "breakfast"
        }
        
        with patch('main.restaurant_agent') as mock_agent, \
             patch('main.response_formatter') as mock_formatter, \
             patch('main.cache_service') as mock_cache, \
             patch('main.settings') as mock_settings:
            
            # Configure settings
            mock_settings.authentication.require_authentication = False
            mock_settings.cache.enable_response_cache = True
            
            # Mock cache miss
            mock_cache.get_cached_response.return_value = None
            
            # Mock agent processing
            mock_agent.process_request = AsyncMock(return_value=sample_reasoning_results)
            
            # Mock response formatting
            formatted_response = {
                "recommendation": sample_reasoning_results["recommendation"],
                "candidates": sample_reasoning_results["candidates"],
                "metadata": {
                    "search_criteria": {"district": "Central district", "meal_time": "breakfast"},
                    "total_found": 2,
                    "timestamp": datetime.utcnow().isoformat(),
                    "processing_time_ms": 150.5,
                    "cache_hit": False,
                    "mcp_calls": ["search", "reasoning"]
                }
            }
            mock_formatter.format_response.return_value = formatted_response
            
            # Process request
            result = process_restaurant_request(payload)
            
            # Verify result is valid JSON
            response_data = json.loads(result)
            
            # Verify structure
            assert "recommendation" in response_data
            assert "candidates" in response_data
            assert "metadata" in response_data
            
            # Verify recommendation
            assert response_data["recommendation"]["id"] == "rest_001"
            assert response_data["recommendation"]["name"] == "Central Breakfast Cafe"
            
            # Verify candidates
            assert len(response_data["candidates"]) == 1
            assert response_data["candidates"][0]["id"] == "rest_002"
            
            # Verify metadata
            assert response_data["metadata"]["search_criteria"]["district"] == "Central district"
            assert response_data["metadata"]["search_criteria"]["meal_time"] == "breakfast"
            assert response_data["metadata"]["cache_hit"] is False
            
            # Verify agent was called with correct parameters
            mock_agent.process_request.assert_called_once()
            call_args = mock_agent.process_request.call_args
            assert call_args[1]["district"] == "Central district"
            assert call_args[1]["meal_time"] == "breakfast"
    
    def test_entrypoint_with_authentication(self, sample_reasoning_results, jwt_claims):
        """Test entrypoint with JWT authentication enabled."""
        payload = {
            "district": "Admiralty",
            "meal_time": "lunch",
            "auth_token": "Bearer valid.jwt.token"
        }
        
        with patch('main.restaurant_agent') as mock_agent, \
             patch('main.response_formatter') as mock_formatter, \
             patch('main.cache_service') as mock_cache, \
             patch('main.jwt_auth_handler') as mock_auth, \
             patch('main.settings') as mock_settings:
            
            # Enable authentication
            mock_settings.authentication.require_authentication = True
            mock_settings.authentication.cognito_user_pool_id = "us-east-1_test123"
            mock_settings.cache.enable_response_cache = False
            
            # Mock successful authentication
            mock_validation_result = Mock()
            mock_validation_result.is_valid = True
            mock_validation_result.user_context = UserContext(
                user_id=jwt_claims.user_id,
                username=jwt_claims.username,
                email=jwt_claims.email,
                authenticated=True,
                token_claims=jwt_claims
            )
            mock_validation_result.validation_time_ms = 75
            
            mock_auth.validate_request_token = AsyncMock(return_value=mock_validation_result)
            
            # Mock agent processing
            mock_agent.process_request = AsyncMock(return_value=sample_reasoning_results)
            
            # Mock response formatting
            formatted_response = {
                "recommendation": sample_reasoning_results["recommendation"],
                "candidates": sample_reasoning_results["candidates"],
                "metadata": {
                    "search_criteria": {"district": "Admiralty", "meal_time": "lunch"},
                    "total_found": 2,
                    "timestamp": datetime.utcnow().isoformat(),
                    "processing_time_ms": 200.0,
                    "authentication_time_ms": 75,
                    "user_id": jwt_claims.user_id
                }
            }
            mock_formatter.format_response.return_value = formatted_response
            
            # Process request
            result = process_restaurant_request(payload)
            
            # Verify result
            response_data = json.loads(result)
            
            # Verify authentication was performed
            mock_auth.validate_request_token.assert_called_once()
            
            # Verify user context was passed to agent
            mock_agent.process_request.assert_called_once()
            call_args = mock_agent.process_request.call_args
            assert call_args[1]["user_context"] is not None
            assert call_args[1]["user_context"].user_id == jwt_claims.user_id
            
            # Verify response includes authentication metadata
            assert response_data["metadata"]["authentication_time_ms"] == 75
            assert response_data["metadata"]["user_id"] == jwt_claims.user_id
    
    def test_entrypoint_authentication_failure(self):
        """Test entrypoint with authentication failure."""
        payload = {
            "district": "Central district",
            "meal_time": "breakfast",
            "auth_token": "Bearer invalid.jwt.token"
        }
        
        with patch('main.jwt_auth_handler') as mock_auth, \
             patch('main.settings') as mock_settings, \
             patch('main.error_handler') as mock_error_handler:
            
            # Enable authentication
            mock_settings.authentication.require_authentication = True
            mock_settings.authentication.cognito_user_pool_id = "us-east-1_test123"
            
            # Mock authentication failure
            mock_validation_result = Mock()
            mock_validation_result.is_valid = False
            mock_validation_result.error = Mock()
            mock_validation_result.error.error_code = "INVALID_TOKEN"
            mock_validation_result.error.message = "JWT token is invalid"
            mock_validation_result.validation_time_ms = 25
            
            mock_auth.validate_request_token = AsyncMock(return_value=mock_validation_result)
            
            # Mock error handler
            mock_error_handler.handle_authentication_failure.return_value = {
                "recommendation": None,
                "candidates": [],
                "metadata": {
                    "timestamp": datetime.utcnow().isoformat(),
                    "authentication_failed": True
                },
                "error": {
                    "error_type": "authentication_error",
                    "error_code": "INVALID_TOKEN",
                    "message": "JWT token is invalid",
                    "suggested_actions": ["Provide a valid JWT token", "Check token format"]
                }
            }
            
            # Process request
            result = process_restaurant_request(payload)
            
            # Verify authentication error response
            response_data = json.loads(result)
            
            assert "error" in response_data
            assert response_data["error"]["error_type"] == "authentication_error"
            assert response_data["error"]["error_code"] == "INVALID_TOKEN"
            assert response_data["recommendation"] is None
            assert response_data["candidates"] == []
    
    def test_entrypoint_with_cache_hit(self, sample_reasoning_results):
        """Test entrypoint with cache hit."""
        payload = {
            "district": "Central district",
            "meal_time": "breakfast"
        }
        
        # Prepare cached response
        cached_response = {
            "recommendation": sample_reasoning_results["recommendation"],
            "candidates": sample_reasoning_results["candidates"],
            "metadata": {
                "search_criteria": {"district": "Central district", "meal_time": "breakfast"},
                "total_found": 2,
                "timestamp": datetime.utcnow().isoformat(),
                "processing_time_ms": 5.0,  # Very fast due to cache
                "cache_hit": True,
                "cached_at": datetime.utcnow().isoformat()
            }
        }
        
        with patch('main.cache_service') as mock_cache, \
             patch('main.settings') as mock_settings:
            
            # Configure settings
            mock_settings.authentication.require_authentication = False
            mock_settings.cache.enable_response_cache = True
            
            # Mock cache hit
            mock_cache.get_cached_response.return_value = json.dumps(cached_response)
            
            # Process request
            result = process_restaurant_request(payload)
            
            # Verify cached response
            response_data = json.loads(result)
            
            assert response_data["metadata"]["cache_hit"] is True
            assert response_data["metadata"]["processing_time_ms"] == 5.0
            assert "cached_at" in response_data["metadata"]
            
            # Verify cache was checked
            mock_cache.get_cached_response.assert_called_once()
    
    def test_entrypoint_natural_language_query(self, sample_reasoning_results):
        """Test entrypoint with natural language query."""
        payload = {
            "natural_language_query": "Find me a good breakfast place in Central district"
        }
        
        with patch('main.restaurant_agent') as mock_agent, \
             patch('main.response_formatter') as mock_formatter, \
             patch('main.cache_service') as mock_cache, \
             patch('main.settings') as mock_settings:
            
            # Configure settings
            mock_settings.authentication.require_authentication = False
            mock_settings.cache.enable_response_cache = False
            
            # Mock agent processing
            mock_agent.process_request = AsyncMock(return_value=sample_reasoning_results)
            
            # Mock response formatting
            formatted_response = {
                "recommendation": sample_reasoning_results["recommendation"],
                "candidates": sample_reasoning_results["candidates"],
                "metadata": {
                    "search_criteria": {
                        "natural_language_query": "Find me a good breakfast place in Central district"
                    },
                    "total_found": 2,
                    "timestamp": datetime.utcnow().isoformat(),
                    "processing_time_ms": 300.0,
                    "query_type": "natural_language"
                }
            }
            mock_formatter.format_response.return_value = formatted_response
            
            # Process request
            result = process_restaurant_request(payload)
            
            # Verify result
            response_data = json.loads(result)
            
            # Verify natural language query was processed
            assert response_data["metadata"]["search_criteria"]["natural_language_query"] == payload["natural_language_query"]
            assert response_data["metadata"]["query_type"] == "natural_language"
            
            # Verify agent was called with natural language query
            mock_agent.process_request.assert_called_once()
            call_args = mock_agent.process_request.call_args
            assert call_args[1]["natural_language_query"] == payload["natural_language_query"]
    
    def test_entrypoint_error_handling(self):
        """Test entrypoint error handling for various failure scenarios."""
        payload = {
            "district": "Central district",
            "meal_time": "breakfast"
        }
        
        with patch('main.restaurant_agent') as mock_agent, \
             patch('main.error_handler') as mock_error_handler, \
             patch('main.settings') as mock_settings:
            
            # Configure settings
            mock_settings.authentication.require_authentication = False
            
            # Mock agent failure
            mock_agent.process_request = AsyncMock(side_effect=Exception("Agent processing failed"))
            
            # Mock error handler
            mock_error_handler.handle_error.return_value = {
                "recommendation": None,
                "candidates": [],
                "metadata": {
                    "timestamp": datetime.utcnow().isoformat(),
                    "error_handled": True
                },
                "error": {
                    "error_type": "internal_error",
                    "message": "An unexpected error occurred while processing your request",
                    "suggested_actions": ["Try again in a few moments", "Contact support if issue persists"]
                }
            }
            
            # Process request
            result = process_restaurant_request(payload)
            
            # Verify error response
            response_data = json.loads(result)
            
            assert "error" in response_data
            assert response_data["error"]["error_type"] == "internal_error"
            assert response_data["recommendation"] is None
            assert response_data["candidates"] == []
            
            # Verify error handler was called
            mock_error_handler.handle_error.assert_called_once()
    
    def test_entrypoint_validation_errors(self):
        """Test entrypoint with various validation errors."""
        test_cases = [
            ({}, "Empty payload should fail validation"),
            ({"invalid_field": "value"}, "Invalid field should fail validation"),
            ({"district": ""}, "Empty district should fail validation"),
            ({"meal_time": "invalid_meal"}, "Invalid meal time should fail validation")
        ]
        
        for payload, description in test_cases:
            with patch('main.error_handler') as mock_error_handler, \
                 patch('main.settings') as mock_settings:
                
                # Configure settings
                mock_settings.authentication.require_authentication = False
                
                # Mock error handler
                mock_error_handler.handle_malformed_payload_error.return_value = {
                    "recommendation": None,
                    "candidates": [],
                    "metadata": {
                        "timestamp": datetime.utcnow().isoformat(),
                        "validation_failed": True
                    },
                    "error": {
                        "error_type": "validation_error",
                        "message": "Request payload is malformed or invalid",
                        "suggested_actions": ["Check request format", "Provide required fields"]
                    }
                }
                
                # Process request
                result = process_restaurant_request(payload)
                
                # Verify validation error response
                response_data = json.loads(result)
                
                assert "error" in response_data, f"Failed for case: {description}"
                assert response_data["error"]["error_type"] == "validation_error", f"Failed for case: {description}"
    
    def test_entrypoint_performance_metrics(self, sample_reasoning_results):
        """Test that entrypoint properly tracks performance metrics."""
        payload = {
            "district": "Central district",
            "meal_time": "breakfast"
        }
        
        with patch('main.restaurant_agent') as mock_agent, \
             patch('main.response_formatter') as mock_formatter, \
             patch('main.cache_service') as mock_cache, \
             patch('main.settings') as mock_settings, \
             patch('main._log_request_metrics') as mock_log_metrics:
            
            # Configure settings
            mock_settings.authentication.require_authentication = False
            mock_settings.cache.enable_response_cache = False
            
            # Mock agent processing with delay
            async def slow_process(*args, **kwargs):
                await asyncio.sleep(0.1)  # Simulate processing time
                return sample_reasoning_results
            
            mock_agent.process_request = slow_process
            
            # Mock response formatting
            formatted_response = {
                "recommendation": sample_reasoning_results["recommendation"],
                "candidates": sample_reasoning_results["candidates"],
                "metadata": {
                    "search_criteria": {"district": "Central district", "meal_time": "breakfast"},
                    "total_found": 2,
                    "timestamp": datetime.utcnow().isoformat(),
                    "processing_time_ms": 150.0
                }
            }
            mock_formatter.format_response.return_value = formatted_response
            
            # Process request
            result = process_restaurant_request(payload)
            
            # Verify metrics were logged
            mock_log_metrics.assert_called_once()
            
            # Verify metrics call arguments
            call_args = mock_log_metrics.call_args[0]
            correlation_id = call_args[0]
            start_time = call_args[1]
            logged_payload = call_args[2]
            response_size = call_args[3]
            success = call_args[4]
            
            assert isinstance(correlation_id, str)
            assert isinstance(start_time, datetime)
            assert logged_payload == payload
            assert response_size > 0
            assert success is True
    
    def test_entrypoint_concurrent_requests(self, sample_reasoning_results):
        """Test entrypoint handling concurrent requests."""
        payloads = [
            {"district": "Central district", "meal_time": "breakfast"},
            {"district": "Admiralty", "meal_time": "lunch"},
            {"district": "Causeway Bay", "meal_time": "dinner"}
        ]
        
        with patch('main.restaurant_agent') as mock_agent, \
             patch('main.response_formatter') as mock_formatter, \
             patch('main.cache_service') as mock_cache, \
             patch('main.settings') as mock_settings:
            
            # Configure settings
            mock_settings.authentication.require_authentication = False
            mock_settings.cache.enable_response_cache = False
            
            # Mock agent processing
            mock_agent.process_request = AsyncMock(return_value=sample_reasoning_results)
            
            # Mock response formatting
            mock_formatter.format_response.return_value = {
                "recommendation": sample_reasoning_results["recommendation"],
                "candidates": sample_reasoning_results["candidates"],
                "metadata": {"total_found": 2}
            }
            
            # Process requests concurrently
            results = []
            for payload in payloads:
                result = process_restaurant_request(payload)
                results.append(json.loads(result))
            
            # Verify all requests were processed successfully
            assert len(results) == 3
            for result in results:
                assert "recommendation" in result
                assert "candidates" in result
                assert "metadata" in result
            
            # Verify agent was called for each request
            assert mock_agent.process_request.call_count == 3


if __name__ == "__main__":
    pytest.main([__file__])