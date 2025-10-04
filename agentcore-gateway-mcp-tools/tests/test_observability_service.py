"""
Tests for the observability service.

This module tests the comprehensive observability features including:
- Structured logging with user context and performance metrics
- CloudWatch metrics integration
- Security event logging
- Health monitoring
- Operational statistics collection
"""

import pytest
import asyncio
import time
from datetime import datetime, timezone
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any

from services.observability_service import (
    ObservabilityService,
    PerformanceMetrics,
    SecurityEvent,
    SecurityEventType,
    OperationalStats,
    get_observability_service,
    shutdown_observability_service
)
from middleware.jwt_validator import UserContext
from services.mcp_client_manager import MCPServerHealth, MCPServerStatus


class TestObservabilityService:
    """Test cases for ObservabilityService."""
    
    @pytest.fixture
    def mock_cloudwatch_client(self):
        """Mock CloudWatch client."""
        client = Mock()
        client.list_metrics.return_value = {"Metrics": []}
        client.put_metric_data.return_value = {"ResponseMetadata": {"HTTPStatusCode": 200}}
        return client
    
    @pytest.fixture
    def observability_service(self, mock_cloudwatch_client):
        """Create observability service with mocked CloudWatch."""
        with patch('boto3.client', return_value=mock_cloudwatch_client):
            service = ObservabilityService(
                aws_region="us-east-1",
                service_name="test-service"
            )
        return service
    
    @pytest.fixture
    def user_context(self):
        """Create test user context."""
        return UserContext(
            user_id="test-user-123",
            username="testuser",
            email="test@example.com",
            token_claims={"sub": "test-user-123", "aud": "test-client"},
            authenticated_at=datetime.now(timezone.utc)
        )
    
    @pytest.fixture
    def mock_mcp_client_manager(self):
        """Mock MCP client manager."""
        manager = Mock()
        manager.get_all_server_status.return_value = {
            "search-server": MCPServerHealth(
                status=MCPServerStatus.HEALTHY,
                last_check=time.time(),
                response_time=50.0,
                error_message=None,
                consecutive_failures=0
            ),
            "reasoning-server": MCPServerHealth(
                status=MCPServerStatus.HEALTHY,
                last_check=time.time(),
                response_time=75.0,
                error_message=None,
                consecutive_failures=0
            )
        }
        return manager
    
    def test_initialization(self, observability_service):
        """Test service initialization."""
        assert observability_service.service_name == "test-service"
        assert observability_service.aws_region == "us-east-1"
        assert observability_service.metrics_namespace == "AgentCore/test-service"
        assert observability_service.cloudwatch_client is not None
        assert isinstance(observability_service.stats, OperationalStats)
        assert observability_service.performance_history == []
        assert observability_service.security_events == []
    
    def test_log_request_start(self, observability_service, user_context):
        """Test request start logging."""
        start_time = observability_service.log_request_start(
            request_id="req-123",
            endpoint="/api/test",
            method="GET",
            user_context=user_context,
            ip_address="192.168.1.1",
            user_agent="test-agent"
        )
        
        assert isinstance(start_time, float)
        assert start_time > 0
    
    def test_log_request_end(self, observability_service, user_context):
        """Test request end logging and metrics collection."""
        start_time = time.time() - 0.1  # 100ms ago
        
        observability_service.log_request_end(
            request_id="req-123",
            endpoint="/api/test",
            method="GET",
            status_code=200,
            start_time=start_time,
            user_context=user_context,
            mcp_server_calls=2,
            mcp_server_duration_ms=50.0
        )
        
        # Check that performance metrics were recorded
        assert len(observability_service.performance_history) == 1
        metrics = observability_service.performance_history[0]
        
        assert metrics.request_id == "req-123"
        assert metrics.endpoint == "/api/test"
        assert metrics.method == "GET"
        assert metrics.status_code == 200
        assert metrics.user_id == "test-user-123"
        assert metrics.mcp_server_calls == 2
        assert metrics.mcp_server_duration_ms == 50.0
        assert metrics.duration_ms > 0
        
        # Check operational stats were updated
        assert observability_service.stats.total_requests == 1
        assert observability_service.stats.successful_requests == 1
        assert observability_service.stats.failed_requests == 0
        assert observability_service.stats.mcp_server_calls == 2
    
    def test_log_request_end_with_error(self, observability_service):
        """Test request end logging with error."""
        start_time = time.time() - 0.1
        
        observability_service.log_request_end(
            request_id="req-456",
            endpoint="/api/test",
            method="POST",
            status_code=500,
            start_time=start_time,
            error="Internal server error"
        )
        
        # Check that metrics were recorded
        assert len(observability_service.performance_history) == 1
        metrics = observability_service.performance_history[0]
        
        assert metrics.status_code == 500
        assert observability_service.stats.total_requests == 1
        assert observability_service.stats.successful_requests == 0
        assert observability_service.stats.failed_requests == 1
    
    def test_log_security_event(self, observability_service, user_context):
        """Test security event logging."""
        observability_service.log_security_event(
            event_type=SecurityEventType.AUTH_SUCCESS,
            user_id=user_context.user_id,
            ip_address="192.168.1.1",
            user_agent="test-agent",
            endpoint="/api/test",
            details={"username": user_context.username}
        )
        
        # Check that security event was recorded
        assert len(observability_service.security_events) == 1
        event = observability_service.security_events[0]
        
        assert event.event_type == SecurityEventType.AUTH_SUCCESS
        assert event.user_id == user_context.user_id
        assert event.ip_address == "192.168.1.1"
        assert event.user_agent == "test-agent"
        assert event.endpoint == "/api/test"
        assert event.details["username"] == user_context.username
    
    def test_log_security_event_auth_failure(self, observability_service):
        """Test authentication failure security event."""
        observability_service.log_security_event(
            event_type=SecurityEventType.AUTH_FAILURE,
            user_id=None,
            ip_address="192.168.1.1",
            user_agent="test-agent",
            endpoint="/api/test",
            details={"error": "Invalid token"}
        )
        
        # Check that auth failure was counted
        assert observability_service.stats.auth_failures == 1
        assert len(observability_service.security_events) == 1
    
    def test_log_mcp_server_call(self, observability_service):
        """Test MCP server call logging."""
        observability_service.log_mcp_server_call(
            server_name="search-server",
            tool_name="search_restaurants",
            duration_ms=25.5,
            success=True
        )
        
        # This should be logged but not affect internal stats directly
        # (stats are updated through request end logging)
    
    def test_log_mcp_server_call_with_error(self, observability_service):
        """Test MCP server call logging with error."""
        observability_service.log_mcp_server_call(
            server_name="search-server",
            tool_name="search_restaurants",
            duration_ms=100.0,
            success=False,
            error="Connection timeout"
        )
        
        # This should be logged with error details
    
    @pytest.mark.asyncio
    async def test_get_health_status(self, observability_service, mock_mcp_client_manager):
        """Test health status retrieval."""
        health_data = await observability_service.get_health_status(mock_mcp_client_manager)
        
        assert health_data["status"] == "healthy"
        assert health_data["service"] == "test-service"
        assert health_data["version"] == "1.0.0"
        assert "uptime_seconds" in health_data
        assert "mcp_servers" in health_data
        assert "observability" in health_data
        
        # Check MCP server status
        mcp_servers = health_data["mcp_servers"]
        assert "search-server" in mcp_servers
        assert "reasoning-server" in mcp_servers
        assert mcp_servers["search-server"]["status"] == "healthy"
        assert mcp_servers["reasoning-server"]["status"] == "healthy"
    
    @pytest.mark.asyncio
    async def test_get_health_status_degraded(self, observability_service):
        """Test health status with degraded MCP servers."""
        mock_manager = Mock()
        mock_manager.get_all_server_status.return_value = {
            "search-server": MCPServerHealth(
                status=MCPServerStatus.HEALTHY,
                last_check=time.time(),
                response_time=50.0,
                error_message=None
            ),
            "reasoning-server": MCPServerHealth(
                status=MCPServerStatus.UNHEALTHY,
                last_check=time.time(),
                response_time=None,
                error_message="Connection failed"
            )
        }
        
        health_data = await observability_service.get_health_status(mock_manager)
        
        assert health_data["status"] == "degraded"
        assert health_data["mcp_servers"]["reasoning-server"]["status"] == "unhealthy"
        assert health_data["mcp_servers"]["reasoning-server"]["error"] == "Connection failed"
    
    @pytest.mark.asyncio
    async def test_get_health_status_error(self, observability_service):
        """Test health status with exception."""
        mock_manager = Mock()
        mock_manager.get_all_server_status.side_effect = Exception("Test error")
        
        health_data = await observability_service.get_health_status(mock_manager)
        
        assert health_data["status"] == "unhealthy"
        assert "error" in health_data
        assert "Test error" in health_data["error"]
    
    def test_get_operational_stats(self, observability_service):
        """Test operational statistics retrieval."""
        # Add some test data
        observability_service.stats.total_requests = 100
        observability_service.stats.successful_requests = 95
        observability_service.stats.failed_requests = 5
        observability_service.stats.auth_failures = 2
        observability_service.stats.mcp_server_calls = 150
        
        # Add performance history
        for i in range(10):
            metrics = PerformanceMetrics(
                request_id=f"req-{i}",
                endpoint="/api/test",
                method="GET",
                status_code=200,
                duration_ms=50.0 + i * 10
            )
            observability_service.performance_history.append(metrics)
        
        stats = observability_service.get_operational_stats()
        
        assert stats["total_requests"] == 100
        assert stats["successful_requests"] == 95
        assert stats["failed_requests"] == 5
        assert stats["auth_failures"] == 2
        assert stats["mcp_server_calls"] == 150
        assert stats["performance_history_size"] == 10
        assert stats["avg_response_time_ms"] > 0
        assert stats["cloudwatch_enabled"] is True
        assert "uptime_seconds" in stats
        assert "last_updated" in stats
    
    def test_performance_history_trimming(self, observability_service):
        """Test that performance history is trimmed when it exceeds max size."""
        observability_service.max_history_size = 5
        
        # Add more metrics than max size
        for i in range(10):
            metrics = PerformanceMetrics(
                request_id=f"req-{i}",
                endpoint="/api/test",
                method="GET",
                status_code=200,
                duration_ms=50.0
            )
            observability_service._add_performance_metrics(metrics)
        
        # Should only keep the last 5
        assert len(observability_service.performance_history) == 5
        assert observability_service.performance_history[0].request_id == "req-5"
        assert observability_service.performance_history[-1].request_id == "req-9"
    
    def test_security_events_trimming(self, observability_service):
        """Test that security events are trimmed when they exceed max size."""
        observability_service.max_history_size = 3
        
        # Add more events than max size
        for i in range(5):
            event = SecurityEvent(
                event_type=SecurityEventType.AUTH_SUCCESS,
                user_id=f"user-{i}",
                ip_address="192.168.1.1",
                user_agent="test-agent",
                endpoint="/api/test",
                details={}
            )
            observability_service._add_security_event(event)
        
        # Should only keep the last 3
        assert len(observability_service.security_events) == 3
        assert observability_service.security_events[0].user_id == "user-2"
        assert observability_service.security_events[-1].user_id == "user-4"
    
    @pytest.mark.asyncio
    async def test_send_performance_metrics_success(self, observability_service, mock_cloudwatch_client):
        """Test successful CloudWatch metrics sending."""
        metrics = PerformanceMetrics(
            request_id="req-123",
            endpoint="/api/test",
            method="GET",
            status_code=200,
            duration_ms=100.0,
            mcp_server_calls=2,
            mcp_server_duration_ms=50.0
        )
        
        await observability_service._send_performance_metrics(metrics)
        
        # Verify CloudWatch client was called
        mock_cloudwatch_client.put_metric_data.assert_called_once()
        call_args = mock_cloudwatch_client.put_metric_data.call_args
        
        assert call_args[1]["Namespace"] == "AgentCore/test-service"
        metric_data = call_args[1]["MetricData"]
        
        # Should have RequestDuration, RequestCount, MCPServerCalls, MCPServerDuration
        assert len(metric_data) == 4
        
        metric_names = [m["MetricName"] for m in metric_data]
        assert "RequestDuration" in metric_names
        assert "RequestCount" in metric_names
        assert "MCPServerCalls" in metric_names
        assert "MCPServerDuration" in metric_names
    
    @pytest.mark.asyncio
    async def test_send_performance_metrics_no_cloudwatch(self):
        """Test metrics sending when CloudWatch is not available."""
        service = ObservabilityService(aws_region="us-east-1", service_name="test-service")
        service.cloudwatch_client = None
        
        metrics = PerformanceMetrics(
            request_id="req-123",
            endpoint="/api/test",
            method="GET",
            status_code=200,
            duration_ms=100.0
        )
        
        # Should not raise an exception
        await service._send_performance_metrics(metrics)
    
    @pytest.mark.asyncio
    async def test_send_security_metrics_success(self, observability_service, mock_cloudwatch_client):
        """Test successful security metrics sending."""
        event = SecurityEvent(
            event_type=SecurityEventType.AUTH_FAILURE,
            user_id="user-123",
            ip_address="192.168.1.1",
            user_agent="test-agent",
            endpoint="/api/test",
            details={}
        )
        
        await observability_service._send_security_metrics(event)
        
        # Verify CloudWatch client was called
        mock_cloudwatch_client.put_metric_data.assert_called_once()
        call_args = mock_cloudwatch_client.put_metric_data.call_args
        
        assert call_args[1]["Namespace"] == "AgentCore/test-service"
        metric_data = call_args[1]["MetricData"]
        
        assert len(metric_data) == 1
        assert metric_data[0]["MetricName"] == "SecurityEvents"
        assert metric_data[0]["Value"] == 1
        
        dimensions = metric_data[0]["Dimensions"]
        assert len(dimensions) == 2
        assert {"Name": "EventType", "Value": "auth_failure"} in dimensions
        assert {"Name": "Endpoint", "Value": "/api/test"} in dimensions
    
    @pytest.mark.asyncio
    async def test_send_mcp_metrics_success(self, observability_service, mock_cloudwatch_client):
        """Test successful MCP metrics sending."""
        await observability_service._send_mcp_metrics(
            server_name="search-server",
            tool_name="search_restaurants",
            duration_ms=75.5,
            success=True
        )
        
        # Verify CloudWatch client was called
        mock_cloudwatch_client.put_metric_data.assert_called_once()
        call_args = mock_cloudwatch_client.put_metric_data.call_args
        
        metric_data = call_args[1]["MetricData"]
        assert len(metric_data) == 2
        
        metric_names = [m["MetricName"] for m in metric_data]
        assert "MCPToolCalls" in metric_names
        assert "MCPToolDuration" in metric_names


class TestObservabilityServiceGlobal:
    """Test global observability service functions."""
    
    def test_get_observability_service_singleton(self):
        """Test that get_observability_service returns singleton."""
        # Clear any existing instance
        shutdown_observability_service()
        
        service1 = get_observability_service()
        service2 = get_observability_service()
        
        assert service1 is service2
        
        # Cleanup
        shutdown_observability_service()
    
    def test_shutdown_observability_service(self):
        """Test observability service shutdown."""
        # Get service instance
        service = get_observability_service()
        assert service is not None
        
        # Shutdown
        shutdown_observability_service()
        
        # Getting service again should create new instance
        new_service = get_observability_service()
        assert new_service is not service
        
        # Cleanup
        shutdown_observability_service()


class TestPerformanceMetrics:
    """Test PerformanceMetrics dataclass."""
    
    def test_performance_metrics_creation(self):
        """Test PerformanceMetrics creation and defaults."""
        metrics = PerformanceMetrics(
            request_id="req-123",
            endpoint="/api/test",
            method="GET",
            status_code=200,
            duration_ms=100.0
        )
        
        assert metrics.request_id == "req-123"
        assert metrics.endpoint == "/api/test"
        assert metrics.method == "GET"
        assert metrics.status_code == 200
        assert metrics.duration_ms == 100.0
        assert metrics.user_id is None
        assert metrics.mcp_server_calls == 0
        assert metrics.mcp_server_duration_ms == 0.0
        assert isinstance(metrics.timestamp, datetime)
    
    def test_performance_metrics_with_user(self):
        """Test PerformanceMetrics with user context."""
        metrics = PerformanceMetrics(
            request_id="req-123",
            endpoint="/api/test",
            method="GET",
            status_code=200,
            duration_ms=100.0,
            user_id="user-123",
            mcp_server_calls=2,
            mcp_server_duration_ms=50.0
        )
        
        assert metrics.user_id == "user-123"
        assert metrics.mcp_server_calls == 2
        assert metrics.mcp_server_duration_ms == 50.0


class TestSecurityEvent:
    """Test SecurityEvent dataclass."""
    
    def test_security_event_creation(self):
        """Test SecurityEvent creation and defaults."""
        event = SecurityEvent(
            event_type=SecurityEventType.AUTH_SUCCESS,
            user_id="user-123",
            ip_address="192.168.1.1",
            user_agent="test-agent",
            endpoint="/api/test",
            details={"username": "testuser"}
        )
        
        assert event.event_type == SecurityEventType.AUTH_SUCCESS
        assert event.user_id == "user-123"
        assert event.ip_address == "192.168.1.1"
        assert event.user_agent == "test-agent"
        assert event.endpoint == "/api/test"
        assert event.details["username"] == "testuser"
        assert isinstance(event.timestamp, datetime)


class TestOperationalStats:
    """Test OperationalStats dataclass."""
    
    def test_operational_stats_defaults(self):
        """Test OperationalStats default values."""
        stats = OperationalStats()
        
        assert stats.total_requests == 0
        assert stats.successful_requests == 0
        assert stats.failed_requests == 0
        assert stats.auth_failures == 0
        assert stats.avg_response_time_ms == 0.0
        assert stats.mcp_server_calls == 0
        assert stats.uptime_seconds == 0.0
        assert isinstance(stats.last_updated, datetime)
    
    def test_operational_stats_with_values(self):
        """Test OperationalStats with custom values."""
        stats = OperationalStats(
            total_requests=100,
            successful_requests=95,
            failed_requests=5,
            auth_failures=2,
            avg_response_time_ms=150.5,
            mcp_server_calls=200,
            uptime_seconds=3600.0
        )
        
        assert stats.total_requests == 100
        assert stats.successful_requests == 95
        assert stats.failed_requests == 5
        assert stats.auth_failures == 2
        assert stats.avg_response_time_ms == 150.5
        assert stats.mcp_server_calls == 200
        assert stats.uptime_seconds == 3600.0