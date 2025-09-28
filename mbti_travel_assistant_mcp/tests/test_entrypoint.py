"""
Test suite for BedrockAgentCore runtime entrypoint.

This module tests the main entrypoint function and request processing pipeline
to ensure compliance with requirements 2.1, 2.2, and 6.1.
"""

import json
import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

# Import the main module
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import (
    process_restaurant_request,
    _validate_and_parse_payload,
    _authenticate_request,
    _route_request_by_type,
    _format_final_response,
    _generate_cache_key,
    _log_request_metrics,
    _handle_processing_error
)


class TestEntrypointFunction:
    """Test the main @app.entrypoint function."""
    
    def test_valid_payload_processing(self):
        """Test processing of valid payload with district and meal_time."""
        payload = {
            "district": "Central district",
            "meal_time": "breakfast"
        }
        
        with patch('main.restaurant_agent') as mock_agent, \
             patch('main.response_formatter') as mock_formatter, \
             patch('main.cache_service') as mock_cache:
            
            # Mock agent response
            mock_agent.process_request = AsyncMock(return_value={
                "recommendation": {"id": "rest_001", "name": "Test Restaurant"},
                "candidates": []
            })
            
            # Mock formatter response
            mock_formatter.format_response.return_value = {
                "recommendation": {"id": "rest_001", "name": "Test Restaurant"},
                "candidates": [],
                "metadata": {
                    "search_criteria": {"district": "Central district", "meal_time": "breakfast"},
                    "total_found": 1,
                    "timestamp": datetime.utcnow().isoformat(),
                    "processing_time_ms": 100,
                    "cache_hit": False,
                    "mcp_calls": []
                }
            }
            
            # Mock cache
            mock_cache.get_cached_response.return_value = None
            
            result = process_restaurant_request(payload)
            
            # Verify result is valid JSON
            response_data = json.loads(result)
            assert "recommendation" in response_data
            assert "candidates" in response_data
            assert "metadata" in response_data
    
    def test_empty_payload_handling(self):
        """Test handling of empty payload."""
        payload = {}
        
        result = process_restaurant_request(payload)
        response_data = json.loads(result)
        
        # Should return error response
        assert "error" in response_data
        assert response_data["error"]["error_type"] == "validation_error"
    
    def test_authentication_integration(self):
        """Test JWT authentication integration."""
        payload = {
            "district": "Central district",
            "meal_time": "lunch",
            "auth_token": "mock_jwt_token"
        }
        
        with patch('main.jwt_auth_handler') as mock_auth, \
             patch('main.restaurant_agent') as mock_agent, \
             patch('main.response_formatter') as mock_formatter, \
             patch('main.settings') as mock_settings:
            
            # Enable authentication
            mock_settings.authentication.cognito_user_pool_id = "test_pool"
            mock_settings.authentication.require_authentication = False
            
            # Mock successful authentication
            mock_validation_result = Mock()
            mock_validation_result.is_valid = True
            mock_validation_result.user_context = Mock()
            mock_validation_result.user_context.to_dict.return_value = {"user_id": "test_user"}
            mock_validation_result.validation_time_ms = 50
            
            mock_auth.validate_token.return_value = mock_validation_result
            
            # Mock agent and formatter
            mock_agent.process_request = AsyncMock(return_value={
                "recommendation": {"id": "rest_001"},
                "candidates": []
            })
            mock_formatter.format_response.return_value = {
                "recommendation": {"id": "rest_001"},
                "candidates": [],
                "metadata": {}
            }
            
            result = process_restaurant_request(payload)
            
            # Verify authentication was called
            mock_auth.validate_token.assert_called_once_with("mock_jwt_token")
            
            # Verify result is valid
            response_data = json.loads(result)
            assert "recommendation" in response_data


class TestRequestRouting:
    """Test request routing logic."""
    
    def test_natural_language_routing(self):
        """Test routing for natural language queries."""
        payload = {"natural_language_query": "Find me a good breakfast place"}
        correlation_id = "test_123"
        
        result = _route_request_by_type(payload, correlation_id)
        assert result == "natural_language"
    
    def test_structured_params_routing(self):
        """Test routing for structured parameters."""
        payload = {"district": "Central district", "meal_time": "dinner"}
        correlation_id = "test_123"
        
        result = _route_request_by_type(payload, correlation_id)
        assert result == "structured_params"
    
    def test_default_routing(self):
        """Test default routing."""
        payload = {"some_other_field": "value"}
        correlation_id = "test_123"
        
        result = _route_request_by_type(payload, correlation_id)
        assert result == "default"


class TestPayloadValidation:
    """Test payload validation and parsing."""
    
    def test_valid_payload_parsing(self):
        """Test parsing of valid payload."""
        payload = {
            "district": "Central district",
            "meal_time": "breakfast",
            "natural_language_query": "Find breakfast places"
        }
        correlation_id = "test_123"
        
        result = _validate_and_parse_payload(payload, correlation_id)
        
        assert result.district == "Central district"
        assert result.meal_time == "breakfast"
        assert result.natural_language_query == "Find breakfast places"
    
    def test_invalid_payload_validation(self):
        """Test validation of invalid payload."""
        payload = {}  # Empty payload should fail validation
        correlation_id = "test_123"
        
        with pytest.raises(ValueError) as exc_info:
            _validate_and_parse_payload(payload, correlation_id)
        
        assert "validation failed" in str(exc_info.value).lower()


class TestCacheKeyGeneration:
    """Test cache key generation."""
    
    def test_cache_key_with_params(self):
        """Test cache key generation with parameters."""
        district = "Central district"
        meal_time = "breakfast"
        
        cache_key = _generate_cache_key(district, meal_time)
        
        assert "restaurant_rec" in cache_key
        assert "Central district" in cache_key
        assert "breakfast" in cache_key
        assert datetime.utcnow().strftime("%Y-%m-%d") in cache_key
    
    def test_cache_key_with_none_params(self):
        """Test cache key generation with None parameters."""
        cache_key = _generate_cache_key(None, None)
        
        assert "restaurant_rec" in cache_key
        assert "any_district" in cache_key
        assert "any_meal" in cache_key


class TestErrorHandling:
    """Test error handling functionality."""
    
    def test_processing_error_handling(self):
        """Test processing error handling."""
        error = ValueError("Test error")
        correlation_id = "test_123"
        payload = {"district": "Central district"}
        
        with patch('main.error_handler') as mock_error_handler:
            mock_error_handler.handle_entrypoint_error.return_value = {
                "error": {
                    "error_type": "validation_error",
                    "message": "Test error",
                    "error_code": "TEST_ERROR"
                }
            }
            
            result = _handle_processing_error(error, correlation_id, payload)
            
            assert "error" in result
            assert result["error"]["error_type"] == "validation_error"
    
    def test_error_handler_failure_fallback(self):
        """Test fallback when error handler fails."""
        error = ValueError("Test error")
        correlation_id = "test_123"
        payload = {"district": "Central district"}
        
        with patch('main.error_handler') as mock_error_handler:
            # Make error handler fail
            mock_error_handler.handle_entrypoint_error.side_effect = Exception("Handler failed")
            
            result = _handle_processing_error(error, correlation_id, payload)
            
            # Should return fallback error response
            assert "error" in result
            assert result["error"]["error_type"] == "internal_error"


class TestMetricsLogging:
    """Test metrics logging functionality."""
    
    def test_request_metrics_logging(self):
        """Test request metrics logging."""
        correlation_id = "test_123"
        start_time = datetime.utcnow()
        payload = {"district": "Central district", "meal_time": "breakfast"}
        response_size = 1024
        success = True
        
        with patch('main.logger') as mock_logger:
            _log_request_metrics(correlation_id, start_time, payload, response_size, success)
            
            # Verify logging was called
            mock_logger.info.assert_called_once()
            
            # Check log message contains expected data
            call_args = mock_logger.info.call_args
            extra_data = call_args[1]['extra']
            
            assert extra_data['correlation_id'] == correlation_id
            assert extra_data['response_size_bytes'] == response_size
            assert extra_data['success'] == success
            assert 'processing_time_ms' in extra_data


if __name__ == "__main__":
    pytest.main([__file__])