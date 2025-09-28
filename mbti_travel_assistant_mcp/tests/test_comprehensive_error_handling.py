"""
Comprehensive Error Handling Tests

Tests for the enhanced error handling system including MCP client errors,
circuit breaker functionality, and system error handling.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch

from services.error_handler import ErrorHandler, SystemErrorType
from services.mcp_client_manager import (
    MCPClientManager,
    MCPConnectionError,
    MCPToolCallError,
    MCPCircuitBreakerOpenError,
    MCPCircuitBreaker,
    MCPConnectionConfig,
    CircuitBreakerState
)
from models.auth_models import AuthenticationError
from services.auth_service import AuthenticationError as AuthError


class TestErrorHandler:
    """Test cases for the ErrorHandler service"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.error_handler = ErrorHandler()
        self.correlation_id = "test-correlation-123"
    
    def test_handle_validation_error(self):
        """Test handling of validation errors"""
        error = ValueError("District parameter is required")
        
        result = self.error_handler.handle_error(error, self.correlation_id)
        
        assert result["error"]["error_type"] == "validation_error"
        assert "validation failed" in result["error"]["message"]
        assert "district" in result["error"]["message"].lower()
        assert len(result["error"]["suggested_actions"]) > 0
        assert result["metadata"]["correlation_id"] == self.correlation_id
    
    def test_handle_jwt_authentication_error(self):
        """Test handling of JWT authentication errors"""
        error = AuthenticationError(
            error_code="TOKEN_EXPIRED",
            error_message="Token has expired",
            error_type="authentication_error",
            suggested_action="Obtain a new token"
        )
        
        result = self.error_handler.handle_error(error, self.correlation_id)
        
        assert result["error"]["error_type"] == "authentication_error"
        assert "expired" in result["error"]["message"].lower()
        assert any("token" in action.lower() for action in result["error"]["suggested_actions"])
    
    def test_handle_jwt_validation_error(self):
        """Test handling of JWT validation errors"""
        # Use a simple Exception for this test since AuthError has complex constructor
        error = Exception("Authentication failed: Invalid token signature")
        
        result = self.error_handler.handle_error(error, self.correlation_id)
        
        assert result["error"]["error_type"] == "authentication_error"
        assert "authentication" in result["error"]["message"].lower()
    
    def test_handle_mcp_connection_error(self):
        """Test handling of MCP connection errors"""
        error = MCPConnectionError(
            "Connection refused",
            "restaurant-search-mcp"
        )
        
        result = self.error_handler.handle_error(error, self.correlation_id)
        
        assert result["error"]["error_type"] == "connection_error"
        assert "restaurant-search-mcp" in result["error"]["message"]
        assert result["error"]["retry_after"] == 30
    
    def test_handle_mcp_tool_error(self):
        """Test handling of MCP tool call errors"""
        error = MCPToolCallError(
            "Tool execution failed",
            "search_restaurants_combined",
            "restaurant-search-mcp"
        )
        
        result = self.error_handler.handle_error(error, self.correlation_id)
        
        assert result["error"]["error_type"] == "service_error"
        assert "search_restaurants_combined" in result["error"]["message"]
        assert result["error"]["retry_after"] == 10
    
    def test_handle_mcp_circuit_breaker_error(self):
        """Test handling of MCP circuit breaker errors"""
        recovery_time = datetime.now() + timedelta(minutes=2)
        error = MCPCircuitBreakerOpenError(
            "restaurant-search-mcp",
            5,
            recovery_time
        )
        
        result = self.error_handler.handle_error(error, self.correlation_id)
        
        assert result["error"]["error_type"] == "service_unavailable"
        assert "temporarily unavailable" in result["error"]["message"]
        assert result["error"]["retry_after"] >= 60
    
    def test_handle_malformed_payload_error(self):
        """Test handling of malformed payload errors"""
        payload = {"invalid": "data"}
        validation_errors = [
            "Missing required field: district",
            "Invalid meal_time value"
        ]
        
        result = self.error_handler.handle_malformed_payload_error(
            payload, validation_errors, self.correlation_id
        )
        
        assert result["error"]["error_type"] == "validation_error"
        assert "malformed" in result["error"]["message"]
        assert result["error"]["validation_errors"] == validation_errors
    
    def test_handle_authentication_failure(self):
        """Test handling of authentication failures"""
        failure_reason = "Token has expired"
        headers = {"Authorization": "Bearer expired-token"}
        
        result = self.error_handler.handle_authentication_failure(
            failure_reason, self.correlation_id, headers
        )
        
        assert result["error"]["error_type"] == "authentication_error"
        assert "expired" in result["error"]["message"]
        assert result["error"]["failure_reason"] == failure_reason
    
    def test_error_message_truncation(self):
        """Test that long error messages are truncated"""
        long_message = "x" * 600  # Longer than max_error_message_length
        error = ValueError(long_message)
        
        result = self.error_handler.handle_error(error, self.correlation_id)
        
        assert len(result["error"]["message"]) <= 500
        assert result["error"]["message"].endswith("...")


class TestMCPCircuitBreaker:
    """Test cases for the MCP Circuit Breaker"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.config = MCPConnectionConfig(
            endpoint="http://test-mcp-server",
            circuit_breaker_failure_threshold=3,
            circuit_breaker_recovery_timeout=60
        )
        self.circuit_breaker = MCPCircuitBreaker(self.config, "test-server")
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_closed_state(self):
        """Test circuit breaker in closed state"""
        async def successful_operation():
            return "success"
        
        result = await self.circuit_breaker.call(successful_operation)
        
        assert result == "success"
        assert self.circuit_breaker.state == CircuitBreakerState.CLOSED
        assert self.circuit_breaker.failure_count == 0
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_failure_counting(self):
        """Test circuit breaker failure counting"""
        async def failing_operation():
            raise ConnectionError("Connection failed")
        
        # First two failures should not trip the breaker
        for i in range(2):
            with pytest.raises(ConnectionError):
                await self.circuit_breaker.call(failing_operation)
            assert self.circuit_breaker.state == CircuitBreakerState.CLOSED
            assert self.circuit_breaker.failure_count == i + 1
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_trips_to_open(self):
        """Test circuit breaker trips to open state"""
        async def failing_operation():
            raise ConnectionError("Connection failed")
        
        # Trip the circuit breaker
        for i in range(3):
            with pytest.raises(ConnectionError):
                await self.circuit_breaker.call(failing_operation)
        
        assert self.circuit_breaker.state == CircuitBreakerState.OPEN
        assert self.circuit_breaker.failure_count == 3
        assert self.circuit_breaker.recovery_time is not None
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_open_state_blocks_calls(self):
        """Test circuit breaker blocks calls when open"""
        async def any_operation():
            return "should not execute"
        
        # Trip the circuit breaker first
        async def failing_operation():
            raise ConnectionError("Connection failed")
        
        for i in range(3):
            with pytest.raises(ConnectionError):
                await self.circuit_breaker.call(failing_operation)
        
        # Now calls should be blocked
        with pytest.raises(MCPCircuitBreakerOpenError):
            await self.circuit_breaker.call(any_operation)
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_half_open_recovery(self):
        """Test circuit breaker recovery through half-open state"""
        async def failing_operation():
            raise ConnectionError("Connection failed")
        
        async def successful_operation():
            return "success"
        
        # Trip the circuit breaker
        for i in range(3):
            with pytest.raises(ConnectionError):
                await self.circuit_breaker.call(failing_operation)
        
        # Manually set recovery time to past (simulate time passage)
        self.circuit_breaker.recovery_time = datetime.now() - timedelta(seconds=1)
        
        # Next call should transition to half-open and succeed
        result = await self.circuit_breaker.call(successful_operation)
        
        assert result == "success"
        assert self.circuit_breaker.state == CircuitBreakerState.CLOSED
        assert self.circuit_breaker.failure_count == 0
    
    def test_circuit_breaker_state_info(self):
        """Test circuit breaker state information"""
        state_info = self.circuit_breaker.get_state_info()
        
        assert "state" in state_info
        assert "failure_count" in state_info
        assert "failure_threshold" in state_info
        assert "recovery_timeout" in state_info
        assert state_info["state"] == "closed"
        assert state_info["failure_threshold"] == 3


class TestMCPClientManagerErrorHandling:
    """Test cases for MCP Client Manager error handling"""
    
    def setup_method(self):
        """Set up test fixtures"""
        with patch('config.settings.settings') as mock_settings:
            mock_settings.mcp_client.search_mcp_endpoint = "http://test-search"
            mock_settings.mcp_client.reasoning_mcp_endpoint = "http://test-reasoning"
            mock_settings.mcp_client.mcp_connection_timeout = 30
            mock_settings.mcp_client.mcp_retry_attempts = 3
            
            self.mcp_manager = MCPClientManager()
    
    def test_error_classification(self):
        """Test error classification functionality"""
        # Test connection error
        conn_error = ConnectionError("Connection refused")
        assert self.mcp_manager._classify_error(conn_error).value == "connection_error"
        
        # Test timeout error
        timeout_error = TimeoutError("Request timed out")
        assert self.mcp_manager._classify_error(timeout_error).value == "timeout_error"
        
        # Test authentication error
        auth_error = Exception("Authentication failed")
        assert self.mcp_manager._classify_error(auth_error).value == "authentication_error"
        
        # Test parsing error
        parse_error = ValueError("JSON decode error")
        assert self.mcp_manager._classify_error(parse_error).value == "parsing_error"
    
    def test_retryable_error_detection(self):
        """Test retryable error detection"""
        # Retryable errors
        conn_error = ConnectionError("Connection refused")
        assert self.mcp_manager._is_retryable_error(conn_error, self.mcp_manager._classify_error(conn_error))
        
        timeout_error = TimeoutError("Request timed out")
        assert self.mcp_manager._is_retryable_error(timeout_error, self.mcp_manager._classify_error(timeout_error))
        
        # Non-retryable errors
        auth_error = Exception("Authentication failed")
        assert not self.mcp_manager._is_retryable_error(auth_error, self.mcp_manager._classify_error(auth_error))
        
        parse_error = ValueError("Invalid parameter format")
        assert not self.mcp_manager._is_retryable_error(parse_error, self.mcp_manager._classify_error(parse_error))
    
    def test_retry_delay_calculation(self):
        """Test retry delay calculation with exponential backoff"""
        base_delay = 1.0
        max_delay = 60.0
        
        # Test exponential backoff
        delay_0 = self.mcp_manager._calculate_retry_delay(0, base_delay, max_delay)
        delay_1 = self.mcp_manager._calculate_retry_delay(1, base_delay, max_delay)
        delay_2 = self.mcp_manager._calculate_retry_delay(2, base_delay, max_delay)
        
        # Delays should generally increase (with jitter)
        assert delay_0 >= 0.1  # Minimum delay
        assert delay_1 > delay_0 * 0.5  # Should be roughly double (accounting for jitter)
        assert delay_2 > delay_1 * 0.5
        
        # Should not exceed max delay
        large_delay = self.mcp_manager._calculate_retry_delay(10, base_delay, max_delay)
        assert large_delay <= max_delay
    
    def test_connection_stats_with_errors(self):
        """Test connection statistics include error information"""
        # Simulate some statistics
        self.mcp_manager.search_stats.total_calls = 10
        self.mcp_manager.search_stats.successful_calls = 7
        self.mcp_manager.search_stats.failed_calls = 3
        self.mcp_manager.search_stats.consecutive_failures = 2
        self.mcp_manager.search_stats.circuit_breaker_trips = 1
        
        stats = self.mcp_manager.get_connection_stats()
        
        assert stats["search_mcp"]["total_calls"] == 10
        assert stats["search_mcp"]["successful_calls"] == 7
        assert stats["search_mcp"]["failed_calls"] == 3
        assert stats["search_mcp"]["consecutive_failures"] == 2
        assert stats["search_mcp"]["circuit_breaker_trips"] == 1
        assert stats["search_mcp"]["success_rate"] == 0.7
        assert "error_counts_by_type" in stats["search_mcp"]
        assert "circuit_breaker" in stats["search_mcp"]


@pytest.mark.asyncio
async def test_integration_error_handling_flow():
    """Integration test for complete error handling flow"""
    error_handler = ErrorHandler()
    
    # Test MCP connection error flow
    mcp_error = MCPConnectionError(
        "Connection timeout",
        "restaurant-search-mcp",
        TimeoutError("Connection timed out after 30s")
    )
    
    result = error_handler.handle_error(mcp_error, "test-correlation-456")
    
    # Verify structured response
    assert result["recommendation"] is None
    assert result["candidates"] == []
    assert result["metadata"]["correlation_id"] == "test-correlation-456"
    assert result["metadata"]["error_handled"] is True
    assert result["error"]["error_type"] == "connection_error"
    assert "restaurant-search-mcp" in result["error"]["message"]
    assert result["error"]["retry_after"] == 30
    assert len(result["error"]["suggested_actions"]) > 0


if __name__ == "__main__":
    pytest.main([__file__])