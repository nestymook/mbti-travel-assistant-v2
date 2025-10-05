"""
Unit Tests for Enhanced Circuit Breaker

This module contains comprehensive unit tests for the Enhanced Circuit Breaker
with dual path support, covering all scenarios and edge cases.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from services.enhanced_circuit_breaker import (
    EnhancedCircuitBreaker,
    CircuitBreakerConfig,
    PathState,
    PathType,
    FailureRecord
)
from models.dual_health_models import (
    DualHealthCheckResult,
    MCPHealthCheckResult,
    RESTHealthCheckResult,
    ServerStatus,
    EnhancedCircuitBreakerState
)


class TestCircuitBreakerConfig:
    """Test CircuitBreakerConfig class."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = CircuitBreakerConfig()
        
        assert config.failure_threshold == 5
        assert config.success_threshold == 3
        assert config.timeout_seconds == 60
        assert config.mcp_failure_threshold == 3
        assert config.rest_failure_threshold == 3
        assert config.require_both_paths_healthy is False
        assert config.recovery_timeout_seconds == 30
        assert config.half_open_max_requests == 5
        assert config.failure_history_window_minutes == 10
        assert config.max_history_size == 100
    
    def test_config_validation_success(self):
        """Test successful configuration validation."""
        config = CircuitBreakerConfig(
            failure_threshold=3,
            success_threshold=2,
            timeout_seconds=30,
            mcp_failure_threshold=2,
            rest_failure_threshold=2
        )
        
        errors = config.validate()
        assert errors == []
    
    def test_config_validation_failures(self):
        """Test configuration validation failures."""
        config = CircuitBreakerConfig(
            failure_threshold=0,
            success_threshold=-1,
            timeout_seconds=0,
            mcp_failure_threshold=-1,
            rest_failure_threshold=0,
            recovery_timeout_seconds=-1,
            half_open_max_requests=0
        )
        
        errors = config.validate()
        assert len(errors) == 7
        assert "Failure threshold must be positive" in errors
        assert "Success threshold must be positive" in errors
        assert "Timeout seconds must be positive" in errors
        assert "MCP failure threshold must be positive" in errors
        assert "REST failure threshold must be positive" in errors
        assert "Recovery timeout must be positive" in errors
        assert "Half-open max requests must be positive" in errors


class TestPathState:
    """Test PathState class."""
    
    def test_path_state_initialization(self):
        """Test PathState initialization."""
        state = PathState(PathType.MCP)
        
        assert state.path_type == PathType.MCP
        assert state.state == EnhancedCircuitBreakerState.CLOSED
        assert state.failure_count == 0
        assert state.success_count == 0
        assert state.last_failure_time is None
        assert state.last_success_time is None
        assert state.opened_time is None
        assert state.half_open_requests == 0
    
    def test_reset_counts(self):
        """Test resetting counts."""
        state = PathState(PathType.REST)
        state.failure_count = 5
        state.success_count = 3
        state.half_open_requests = 2
        
        state.reset_counts()
        
        assert state.failure_count == 0
        assert state.success_count == 0
        assert state.half_open_requests == 0
    
    def test_is_available(self):
        """Test path availability check."""
        state = PathState(PathType.MCP)
        
        # Closed state should be available
        state.state = EnhancedCircuitBreakerState.CLOSED
        assert state.is_available() is True
        
        # Half-open state should be available
        state.state = EnhancedCircuitBreakerState.HALF_OPEN
        assert state.is_available() is True
        
        # Open state should not be available
        state.state = EnhancedCircuitBreakerState.OPEN
        assert state.is_available() is False
        
        # Path-specific states should not be available
        state.state = EnhancedCircuitBreakerState.MCP_ONLY
        assert state.is_available() is False
        
        state.state = EnhancedCircuitBreakerState.REST_ONLY
        assert state.is_available() is False


class TestEnhancedCircuitBreaker:
    """Test EnhancedCircuitBreaker class."""
    
    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return CircuitBreakerConfig(
            failure_threshold=3,
            success_threshold=2,
            timeout_seconds=30,
            mcp_failure_threshold=2,
            rest_failure_threshold=2,
            recovery_timeout_seconds=15,
            half_open_max_requests=3
        )
    
    @pytest.fixture
    def circuit_breaker(self, config):
        """Create circuit breaker instance."""
        return EnhancedCircuitBreaker(config)
    
    def test_initialization(self, config):
        """Test circuit breaker initialization."""
        cb = EnhancedCircuitBreaker(config)
        
        assert cb.config == config
        assert len(cb.server_states) == 0
        assert len(cb.failure_history) == 0
    
    def test_initialization_with_invalid_config(self):
        """Test initialization with invalid configuration."""
        invalid_config = CircuitBreakerConfig(failure_threshold=0)
        
        with pytest.raises(ValueError, match="Invalid circuit breaker configuration"):
            EnhancedCircuitBreaker(invalid_config)
    
    def test_initialization_with_default_config(self):
        """Test initialization with default configuration."""
        cb = EnhancedCircuitBreaker()
        
        assert cb.config is not None
        assert cb.config.failure_threshold == 5
    
    @pytest.mark.asyncio
    async def test_evaluate_circuit_state_both_success(self, circuit_breaker):
        """Test circuit state evaluation with both paths successful."""
        # Create successful dual result
        mcp_result = MCPHealthCheckResult(
            server_name="test-server",
            timestamp=datetime.now(),
            success=True,
            response_time_ms=100.0
        )
        
        rest_result = RESTHealthCheckResult(
            server_name="test-server",
            timestamp=datetime.now(),
            success=True,
            response_time_ms=80.0
        )
        
        dual_result = DualHealthCheckResult(
            server_name="test-server",
            timestamp=datetime.now(),
            overall_status=ServerStatus.HEALTHY,
            overall_success=True,
            mcp_result=mcp_result,
            mcp_success=True,
            rest_result=rest_result,
            rest_success=True
        )
        
        state = await circuit_breaker.evaluate_circuit_state("test-server", dual_result)
        
        assert state == EnhancedCircuitBreakerState.CLOSED
    
    @pytest.mark.asyncio
    async def test_evaluate_circuit_state_both_failure(self, circuit_breaker):
        """Test circuit state evaluation with both paths failing."""
        # Create failed dual result
        mcp_result = MCPHealthCheckResult(
            server_name="test-server",
            timestamp=datetime.now(),
            success=False,
            response_time_ms=5000.0,
            connection_error="Connection timeout"
        )
        
        rest_result = RESTHealthCheckResult(
            server_name="test-server",
            timestamp=datetime.now(),
            success=False,
            response_time_ms=5000.0,
            status_code=500,
            http_error="Internal server error"
        )
        
        dual_result = DualHealthCheckResult(
            server_name="test-server",
            timestamp=datetime.now(),
            overall_status=ServerStatus.UNHEALTHY,
            overall_success=False,
            mcp_result=mcp_result,
            mcp_success=False,
            mcp_error_message="Connection timeout",
            rest_result=rest_result,
            rest_success=False,
            rest_error_message="Internal server error"
        )
        
        # Trigger multiple failures to open circuit
        for _ in range(3):
            state = await circuit_breaker.evaluate_circuit_state("test-server", dual_result)
        
        assert state == EnhancedCircuitBreakerState.OPEN
    
    @pytest.mark.asyncio
    async def test_evaluate_circuit_state_mixed_results(self, circuit_breaker):
        """Test circuit state evaluation with mixed results."""
        # MCP success, REST failure
        mcp_result = MCPHealthCheckResult(
            server_name="test-server",
            timestamp=datetime.now(),
            success=True,
            response_time_ms=100.0
        )
        
        rest_result = RESTHealthCheckResult(
            server_name="test-server",
            timestamp=datetime.now(),
            success=False,
            response_time_ms=5000.0,
            status_code=503,
            http_error="Service unavailable"
        )
        
        dual_result = DualHealthCheckResult(
            server_name="test-server",
            timestamp=datetime.now(),
            overall_status=ServerStatus.DEGRADED,
            overall_success=False,
            mcp_result=mcp_result,
            mcp_success=True,
            rest_result=rest_result,
            rest_success=False,
            rest_error_message="Service unavailable"
        )
        
        # Trigger failures for REST path only
        for _ in range(3):
            state = await circuit_breaker.evaluate_circuit_state("test-server", dual_result)
        
        # Should result in MCP_ONLY state
        assert state == EnhancedCircuitBreakerState.MCP_ONLY
    
    @pytest.mark.asyncio
    async def test_should_allow_mcp_traffic(self, circuit_breaker):
        """Test MCP traffic allowance logic."""
        server_name = "test-server"
        
        # Initially should allow traffic
        assert await circuit_breaker.should_allow_mcp_traffic(server_name) is True
        
        # Create failing MCP result
        mcp_result = MCPHealthCheckResult(
            server_name=server_name,
            timestamp=datetime.now(),
            success=False,
            response_time_ms=5000.0,
            connection_error="Connection failed"
        )
        
        dual_result = DualHealthCheckResult(
            server_name=server_name,
            timestamp=datetime.now(),
            overall_status=ServerStatus.UNHEALTHY,
            overall_success=False,
            mcp_result=mcp_result,
            mcp_success=False,
            mcp_error_message="Connection failed"
        )
        
        # Trigger failures to open MCP circuit
        for _ in range(3):
            await circuit_breaker.evaluate_circuit_state(server_name, dual_result)
        
        # Should not allow MCP traffic when circuit is open
        assert await circuit_breaker.should_allow_mcp_traffic(server_name) is False
    
    @pytest.mark.asyncio
    async def test_should_allow_rest_traffic(self, circuit_breaker):
        """Test REST traffic allowance logic."""
        server_name = "test-server"
        
        # Initially should allow traffic
        assert await circuit_breaker.should_allow_rest_traffic(server_name) is True
        
        # Create failing REST result
        rest_result = RESTHealthCheckResult(
            server_name=server_name,
            timestamp=datetime.now(),
            success=False,
            response_time_ms=5000.0,
            status_code=500,
            http_error="Internal server error"
        )
        
        dual_result = DualHealthCheckResult(
            server_name=server_name,
            timestamp=datetime.now(),
            overall_status=ServerStatus.UNHEALTHY,
            overall_success=False,
            rest_result=rest_result,
            rest_success=False,
            rest_error_message="Internal server error"
        )
        
        # Trigger failures to open REST circuit
        for _ in range(3):
            await circuit_breaker.evaluate_circuit_state(server_name, dual_result)
        
        # Should not allow REST traffic when circuit is open
        assert await circuit_breaker.should_allow_rest_traffic(server_name) is False
    
    @pytest.mark.asyncio
    async def test_get_available_paths_both_available(self, circuit_breaker):
        """Test getting available paths when both are available."""
        server_name = "test-server"
        
        paths = await circuit_breaker.get_available_paths(server_name)
        
        assert "mcp" in paths
        assert "rest" in paths
        assert "both" in paths
        assert len(paths) == 3
    
    @pytest.mark.asyncio
    async def test_get_available_paths_mcp_only(self, circuit_breaker):
        """Test getting available paths when only MCP is available."""
        server_name = "test-server"
        
        # Fail REST path
        rest_result = RESTHealthCheckResult(
            server_name=server_name,
            timestamp=datetime.now(),
            success=False,
            response_time_ms=5000.0,
            status_code=500
        )
        
        dual_result = DualHealthCheckResult(
            server_name=server_name,
            timestamp=datetime.now(),
            overall_status=ServerStatus.DEGRADED,
            overall_success=False,
            rest_result=rest_result,
            rest_success=False
        )
        
        # Trigger REST failures
        for _ in range(3):
            await circuit_breaker.evaluate_circuit_state(server_name, dual_result)
        
        paths = await circuit_breaker.get_available_paths(server_name)
        
        assert paths == ["mcp"]
    
    @pytest.mark.asyncio
    async def test_get_available_paths_none_available(self, circuit_breaker):
        """Test getting available paths when none are available."""
        server_name = "test-server"
        
        # Create failing dual result
        mcp_result = MCPHealthCheckResult(
            server_name=server_name,
            timestamp=datetime.now(),
            success=False,
            response_time_ms=5000.0
        )
        
        rest_result = RESTHealthCheckResult(
            server_name=server_name,
            timestamp=datetime.now(),
            success=False,
            response_time_ms=5000.0,
            status_code=500
        )
        
        dual_result = DualHealthCheckResult(
            server_name=server_name,
            timestamp=datetime.now(),
            overall_status=ServerStatus.UNHEALTHY,
            overall_success=False,
            mcp_result=mcp_result,
            mcp_success=False,
            rest_result=rest_result,
            rest_success=False
        )
        
        # Trigger failures for both paths
        for _ in range(3):
            await circuit_breaker.evaluate_circuit_state(server_name, dual_result)
        
        paths = await circuit_breaker.get_available_paths(server_name)
        
        assert paths == ["none"]
    
    @pytest.mark.asyncio
    async def test_half_open_state_transition(self, circuit_breaker):
        """Test transition to half-open state after timeout."""
        server_name = "test-server"
        
        # Create failing result
        mcp_result = MCPHealthCheckResult(
            server_name=server_name,
            timestamp=datetime.now(),
            success=False,
            response_time_ms=5000.0
        )
        
        dual_result = DualHealthCheckResult(
            server_name=server_name,
            timestamp=datetime.now(),
            overall_status=ServerStatus.UNHEALTHY,
            overall_success=False,
            mcp_result=mcp_result,
            mcp_success=False
        )
        
        # Trigger failures to open circuit
        for _ in range(3):
            await circuit_breaker.evaluate_circuit_state(server_name, dual_result)
        
        # Manually set opened time to past to simulate timeout
        server_states = circuit_breaker.server_states[server_name]
        mcp_state = server_states[PathType.MCP]
        mcp_state.opened_time = datetime.now() - timedelta(seconds=35)
        
        # Evaluate again to trigger timeout transition
        await circuit_breaker.evaluate_circuit_state(server_name, dual_result)
        
        # Should transition to half-open
        assert mcp_state.state == EnhancedCircuitBreakerState.HALF_OPEN
    
    @pytest.mark.asyncio
    async def test_half_open_recovery(self, circuit_breaker):
        """Test recovery from half-open state with successful requests."""
        server_name = "test-server"
        
        # First, open the circuit
        failing_result = DualHealthCheckResult(
            server_name=server_name,
            timestamp=datetime.now(),
            overall_status=ServerStatus.UNHEALTHY,
            overall_success=False,
            mcp_result=MCPHealthCheckResult(
                server_name=server_name,
                timestamp=datetime.now(),
                success=False,
                response_time_ms=5000.0
            ),
            mcp_success=False
        )
        
        for _ in range(3):
            await circuit_breaker.evaluate_circuit_state(server_name, failing_result)
        
        # Transition to half-open
        server_states = circuit_breaker.server_states[server_name]
        mcp_state = server_states[PathType.MCP]
        mcp_state.state = EnhancedCircuitBreakerState.HALF_OPEN
        mcp_state.reset_counts()
        
        # Send successful requests
        success_result = DualHealthCheckResult(
            server_name=server_name,
            timestamp=datetime.now(),
            overall_status=ServerStatus.HEALTHY,
            overall_success=True,
            mcp_result=MCPHealthCheckResult(
                server_name=server_name,
                timestamp=datetime.now(),
                success=True,
                response_time_ms=100.0
            ),
            mcp_success=True
        )
        
        # Send enough successful requests to close circuit
        for _ in range(2):
            await circuit_breaker.evaluate_circuit_state(server_name, success_result)
        
        # Circuit should be closed
        assert mcp_state.state == EnhancedCircuitBreakerState.CLOSED
    
    @pytest.mark.asyncio
    async def test_half_open_request_limit(self, circuit_breaker):
        """Test half-open request limit enforcement."""
        server_name = "test-server"
        
        # Set MCP path to half-open with max requests reached
        server_states = circuit_breaker.server_states[server_name]
        mcp_state = server_states[PathType.MCP]
        mcp_state.state = EnhancedCircuitBreakerState.HALF_OPEN
        mcp_state.half_open_requests = circuit_breaker.config.half_open_max_requests
        
        # Should not allow more requests
        assert await circuit_breaker.should_allow_mcp_traffic(server_name) is False
    
    @pytest.mark.asyncio
    async def test_get_circuit_breaker_state(self, circuit_breaker):
        """Test getting detailed circuit breaker state."""
        server_name = "test-server"
        
        # Trigger some activity
        dual_result = DualHealthCheckResult(
            server_name=server_name,
            timestamp=datetime.now(),
            overall_status=ServerStatus.HEALTHY,
            overall_success=True,
            mcp_result=MCPHealthCheckResult(
                server_name=server_name,
                timestamp=datetime.now(),
                success=True,
                response_time_ms=100.0
            ),
            mcp_success=True,
            rest_result=RESTHealthCheckResult(
                server_name=server_name,
                timestamp=datetime.now(),
                success=True,
                response_time_ms=80.0
            ),
            rest_success=True
        )
        
        await circuit_breaker.evaluate_circuit_state(server_name, dual_result)
        
        state = await circuit_breaker.get_circuit_breaker_state(server_name)
        
        assert state["server_name"] == server_name
        assert "timestamp" in state
        assert "mcp_path" in state
        assert "rest_path" in state
        assert "overall_state" in state
        assert "available_paths" in state
        assert "config" in state
        
        # Check MCP path details
        mcp_path = state["mcp_path"]
        assert mcp_path["state"] == "CLOSED"
        assert mcp_path["success_count"] == 1
        assert mcp_path["is_available"] is True
        
        # Check REST path details
        rest_path = state["rest_path"]
        assert rest_path["state"] == "CLOSED"
        assert rest_path["success_count"] == 1
        assert rest_path["is_available"] is True
    
    @pytest.mark.asyncio
    async def test_reset_circuit_breaker_all_paths(self, circuit_breaker):
        """Test resetting all circuit breaker paths."""
        server_name = "test-server"
        
        # Create some failure state
        failing_result = DualHealthCheckResult(
            server_name=server_name,
            timestamp=datetime.now(),
            overall_status=ServerStatus.UNHEALTHY,
            overall_success=False,
            mcp_result=MCPHealthCheckResult(
                server_name=server_name,
                timestamp=datetime.now(),
                success=False,
                response_time_ms=5000.0
            ),
            mcp_success=False
        )
        
        await circuit_breaker.evaluate_circuit_state(server_name, failing_result)
        
        # Reset circuit breaker
        await circuit_breaker.reset_circuit_breaker(server_name)
        
        # Check that state is reset
        server_states = circuit_breaker.server_states[server_name]
        mcp_state = server_states[PathType.MCP]
        rest_state = server_states[PathType.REST]
        
        assert mcp_state.state == EnhancedCircuitBreakerState.CLOSED
        assert mcp_state.failure_count == 0
        assert mcp_state.success_count == 0
        assert rest_state.state == EnhancedCircuitBreakerState.CLOSED
        assert rest_state.failure_count == 0
        assert rest_state.success_count == 0
        
        # Check that failure history is cleared
        assert len(circuit_breaker.failure_history[server_name]) == 0
    
    @pytest.mark.asyncio
    async def test_reset_circuit_breaker_specific_path(self, circuit_breaker):
        """Test resetting specific circuit breaker path."""
        server_name = "test-server"
        
        # Create failure state for MCP path
        failing_result = DualHealthCheckResult(
            server_name=server_name,
            timestamp=datetime.now(),
            overall_status=ServerStatus.DEGRADED,
            overall_success=False,
            mcp_result=MCPHealthCheckResult(
                server_name=server_name,
                timestamp=datetime.now(),
                success=False,
                response_time_ms=5000.0
            ),
            mcp_success=False,
            rest_result=RESTHealthCheckResult(
                server_name=server_name,
                timestamp=datetime.now(),
                success=True,
                response_time_ms=100.0
            ),
            rest_success=True
        )
        
        await circuit_breaker.evaluate_circuit_state(server_name, failing_result)
        
        # Reset only MCP path
        await circuit_breaker.reset_circuit_breaker(server_name, PathType.MCP)
        
        # Check that only MCP state is reset
        server_states = circuit_breaker.server_states[server_name]
        mcp_state = server_states[PathType.MCP]
        rest_state = server_states[PathType.REST]
        
        assert mcp_state.state == EnhancedCircuitBreakerState.CLOSED
        assert mcp_state.failure_count == 0
        assert rest_state.success_count == 1  # REST state should be preserved
    
    @pytest.mark.asyncio
    async def test_get_circuit_breaker_metrics(self, circuit_breaker):
        """Test getting overall circuit breaker metrics."""
        # Create multiple servers with different states
        servers = ["server1", "server2", "server3"]
        
        # Server 1: Healthy server
        healthy_result = DualHealthCheckResult(
            server_name=servers[0],
            timestamp=datetime.now(),
            overall_status=ServerStatus.HEALTHY,
            overall_success=True,
            mcp_result=MCPHealthCheckResult(
                server_name=servers[0],
                timestamp=datetime.now(),
                success=True,
                response_time_ms=150.0,
                tools_count=5
            ),
            mcp_success=True,
            rest_result=RESTHealthCheckResult(
                server_name=servers[0],
                timestamp=datetime.now(),
                success=True,
                response_time_ms=120.0,
                status_code=200
            ),
            rest_success=True
        )
        await circuit_breaker.evaluate_circuit_state(servers[0], healthy_result)
        
        # Server 2: MCP failed server
        mcp_failed_result = DualHealthCheckResult(
            server_name=servers[1],
            timestamp=datetime.now(),
            overall_status=ServerStatus.DEGRADED,
            overall_success=False,
            mcp_result=MCPHealthCheckResult(
                server_name=servers[1],
                timestamp=datetime.now(),
                success=False,
                response_time_ms=5000.0,
                connection_error="MCP connection failed"
            ),
            mcp_success=False,
            mcp_error_message="MCP connection failed",
            rest_result=RESTHealthCheckResult(
                server_name=servers[1],
                timestamp=datetime.now(),
                success=True,
                response_time_ms=120.0,
                status_code=200
            ),
            rest_success=True
        )
        # Trigger MCP failures
        for _ in range(3):
            await circuit_breaker.evaluate_circuit_state(servers[1], mcp_failed_result)
        
        # Server 3: Both paths failed server
        both_failed_result = DualHealthCheckResult(
            server_name=servers[2],
            timestamp=datetime.now(),
            overall_status=ServerStatus.UNHEALTHY,
            overall_success=False,
            mcp_result=MCPHealthCheckResult(
                server_name=servers[2],
                timestamp=datetime.now(),
                success=False,
                response_time_ms=5000.0,
                connection_error="MCP connection failed"
            ),
            mcp_success=False,
            mcp_error_message="MCP connection failed",
            rest_result=RESTHealthCheckResult(
                server_name=servers[2],
                timestamp=datetime.now(),
                success=False,
                response_time_ms=5000.0,
                status_code=500,
                http_error="Internal server error"
            ),
            rest_success=False,
            rest_error_message="Internal server error"
        )
        # Trigger failures for both paths
        for _ in range(3):
            await circuit_breaker.evaluate_circuit_state(servers[2], both_failed_result)
        
        metrics = await circuit_breaker.get_circuit_breaker_metrics()
        
        assert metrics["total_servers"] == 3
        assert metrics["mcp_circuits_open"] == 2  # server2 and server3
        assert metrics["rest_circuits_open"] == 1  # server3 only
        assert metrics["both_paths_available"] == 1  # server1 only
        assert metrics["no_paths_available"] == 1  # server3 only
        
        # Check availability rates
        assert metrics["mcp_availability_rate"] == 1/3  # Only server1 has MCP available
        assert metrics["rest_availability_rate"] == 2/3  # server1 and server2 have REST available
        assert metrics["dual_path_availability_rate"] == 1/3  # Only server1 has both available
    
    @pytest.mark.asyncio
    async def test_require_both_paths_healthy_config(self):
        """Test circuit breaker with require_both_paths_healthy configuration."""
        config = CircuitBreakerConfig(
            failure_threshold=2,
            mcp_failure_threshold=1,
            rest_failure_threshold=1,
            require_both_paths_healthy=True
        )
        
        circuit_breaker = EnhancedCircuitBreaker(config)
        server_name = "test-server"
        
        # Create mixed result (MCP success, REST failure)
        dual_result = DualHealthCheckResult(
            server_name=server_name,
            timestamp=datetime.now(),
            overall_status=ServerStatus.DEGRADED,
            overall_success=False,
            mcp_result=MCPHealthCheckResult(
                server_name=server_name,
                timestamp=datetime.now(),
                success=True,
                response_time_ms=100.0
            ),
            mcp_success=True,
            rest_result=RESTHealthCheckResult(
                server_name=server_name,
                timestamp=datetime.now(),
                success=False,
                response_time_ms=5000.0,
                status_code=500
            ),
            rest_success=False
        )
        
        # Trigger REST failure
        state = await circuit_breaker.evaluate_circuit_state(server_name, dual_result)
        
        # With require_both_paths_healthy=True, should open circuit even with partial failure
        assert state == EnhancedCircuitBreakerState.OPEN
    
    def test_update_config_success(self, circuit_breaker):
        """Test successful configuration update."""
        new_config = CircuitBreakerConfig(
            failure_threshold=10,
            success_threshold=5,
            timeout_seconds=120
        )
        
        result = circuit_breaker.update_config(new_config)
        
        assert result is True
        assert circuit_breaker.config == new_config
    
    def test_update_config_failure(self, circuit_breaker):
        """Test configuration update failure with invalid config."""
        invalid_config = CircuitBreakerConfig(failure_threshold=0)
        
        result = circuit_breaker.update_config(invalid_config)
        
        assert result is False
        assert circuit_breaker.config != invalid_config
    
    @pytest.mark.asyncio
    async def test_failure_history_cleanup(self, circuit_breaker):
        """Test cleanup of old failure records."""
        server_name = "test-server"
        
        # Create old failure record
        old_failure = FailureRecord(
            timestamp=datetime.now() - timedelta(minutes=15),
            path_type=PathType.MCP,
            error_message="Old failure"
        )
        
        circuit_breaker.failure_history[server_name].append(old_failure)
        
        # Create recent failure
        dual_result = DualHealthCheckResult(
            server_name=server_name,
            timestamp=datetime.now(),
            overall_status=ServerStatus.UNHEALTHY,
            overall_success=False,
            mcp_result=MCPHealthCheckResult(
                server_name=server_name,
                timestamp=datetime.now(),
                success=False,
                response_time_ms=5000.0
            ),
            mcp_success=False,
            mcp_error_message="Recent failure"
        )
        
        await circuit_breaker.evaluate_circuit_state(server_name, dual_result)
        
        # Old failure should be cleaned up
        failure_history = circuit_breaker.failure_history[server_name]
        assert len(failure_history) == 1
        assert failure_history[0].error_message == "Recent failure"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])