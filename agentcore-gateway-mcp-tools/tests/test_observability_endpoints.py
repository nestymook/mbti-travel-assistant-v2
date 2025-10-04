"""
Tests for the observability endpoints.

This module tests the health check, metrics, and operational statistics endpoints.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI
from datetime import datetime, timezone

from api.observability_endpoints import router
from services.observability_service import OperationalStats, SecurityEventType, PerformanceMetrics
from services.mcp_client_manager import MCPServerHealth, MCPServerStatus


class TestObservabilityEndpoints:
    """Test cases for observability endpoints."""
    
    @pytest.fixture
    def mock_observability_service(self):
        """Mock observability service."""
        service = Mock()
        
        # Mock health status
        service.get_health_status = AsyncMock(return_value={
            "status": "healthy",
            "service": "agentcore-gateway-mcp-tools",
            "version": "1.0.0",
            "uptime_seconds": 3600.0,
            "timestamp": "2025-01-03T10:00:00Z",
            "mcp_servers": {
                "search-server": {
                    "status": "healthy",
                    "last_check": "2025-01-03T10:00:00Z",
                    "error": None,
                    "response_time_ms": 50.0
                },
                "reasoning-server": {
                    "status": "healthy",
                    "last_check": "2025-01-03T10:00:00Z",
                    "error": None,
                    "response_time_ms": 75.0
                }
            },
            "observability": {
                "cloudwatch_enabled": True,
                "metrics_namespace": "AgentCore/test-service",
                "total_requests": 100,
                "performance_history_size": 50,
                "security_events_count": 10
            }
        })
        
        # Mock operational stats
        service.get_operational_stats.return_value = {
            "total_requests": 100,
            "successful_requests": 95,
            "failed_requests": 5,
            "auth_failures": 2,
            "avg_response_time_ms": 150.5,
            "mcp_server_calls": 200,
            "uptime_seconds": 3600.0,
            "last_updated": "2025-01-03T10:00:00Z",
            "performance_history_size": 50,
            "security_events_count": 10,
            "recent_security_events": 3,
            "cloudwatch_enabled": True,
            "metrics_namespace": "AgentCore/test-service"
        }
        
        # Mock performance history
        service.performance_history = [
            PerformanceMetrics(
                request_id=f"req-{i}",
                endpoint="/api/test",
                method="GET",
                status_code=200,
                duration_ms=50.0 + i * 10,
                user_id="user-123",
                mcp_server_calls=1,
                mcp_server_duration_ms=25.0
            ) for i in range(10)
        ]
        
        # Mock security events
        service.security_events = []
        
        # Mock service properties
        service.metrics_namespace = "AgentCore/test-service"
        service.cloudwatch_client = Mock()
        service.aws_region = "us-east-1"
        service.max_history_size = 1000
        
        return service
    
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
    
    @pytest.fixture
    def app(self, mock_observability_service, mock_mcp_client_manager):
        """Create FastAPI app with observability endpoints."""
        app = FastAPI()
        
        # Mock the dependency functions
        app.dependency_overrides = {
            "services.observability_service.get_observability_service": lambda: mock_observability_service,
            "services.mcp_client_manager.get_mcp_client_manager": lambda: mock_mcp_client_manager
        }
        
        app.include_router(router)
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return TestClient(app)
    
    def test_health_check_healthy(self, client, mock_observability_service):
        """Test health check endpoint with healthy status."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "healthy"
        assert data["service"] == "agentcore-gateway-mcp-tools"
        assert data["version"] == "1.0.0"
        assert "uptime_seconds" in data
        assert "mcp_servers" in data
        assert "observability" in data
        
        # Check MCP servers
        mcp_servers = data["mcp_servers"]
        assert "search-server" in mcp_servers
        assert "reasoning-server" in mcp_servers
        assert mcp_servers["search-server"]["status"] == "healthy"
        assert mcp_servers["reasoning-server"]["status"] == "healthy"
        
        # Verify observability service was called
        mock_observability_service.get_health_status.assert_called_once()
    
    def test_health_check_degraded(self, client, mock_observability_service):
        """Test health check endpoint with degraded status."""
        # Mock degraded health status
        mock_observability_service.get_health_status.return_value = AsyncMock(return_value={
            "status": "degraded",
            "service": "agentcore-gateway-mcp-tools",
            "version": "1.0.0",
            "mcp_servers": {
                "search-server": {"status": "healthy"},
                "reasoning-server": {"status": "unhealthy", "error": "Connection failed"}
            }
        })()
        
        response = client.get("/health")
        
        assert response.status_code == 200  # Still return 200 for degraded
        data = response.json()
        
        assert data["status"] == "degraded"
        assert data["mcp_servers"]["reasoning-server"]["status"] == "unhealthy"
    
    def test_health_check_unhealthy(self, client, mock_observability_service):
        """Test health check endpoint with unhealthy status."""
        # Mock unhealthy health status
        mock_observability_service.get_health_status.return_value = AsyncMock(return_value={
            "status": "unhealthy",
            "service": "agentcore-gateway-mcp-tools",
            "error": "Critical system failure"
        })()
        
        response = client.get("/health")
        
        assert response.status_code == 503
        data = response.json()
        
        assert data["status"] == "unhealthy"
        assert "error" in data
    
    def test_health_check_exception(self, client, mock_observability_service):
        """Test health check endpoint with exception."""
        # Mock exception
        mock_observability_service.get_health_status.side_effect = Exception("Test error")
        
        response = client.get("/health")
        
        assert response.status_code == 503
        data = response.json()
        
        assert data["status"] == "unhealthy"
        assert "error" in data
        assert "Test error" in data["error"]
    
    def test_metrics_endpoint(self, client, mock_observability_service):
        """Test metrics endpoint."""
        response = client.get("/metrics")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["service"] == "agentcore-gateway-mcp-tools"
        assert data["version"] == "1.0.0"
        assert "metrics" in data
        assert "collection_info" in data
        
        # Check metrics data
        metrics = data["metrics"]
        assert metrics["total_requests"] == 100
        assert metrics["successful_requests"] == 95
        assert metrics["failed_requests"] == 5
        assert metrics["auth_failures"] == 2
        assert metrics["avg_response_time_ms"] == 150.5
        assert metrics["mcp_server_calls"] == 200
        
        # Check collection info
        collection_info = data["collection_info"]
        assert collection_info["metrics_namespace"] == "AgentCore/test-service"
        assert collection_info["cloudwatch_enabled"] is True
        assert collection_info["aws_region"] == "us-east-1"
        
        # Verify observability service was called
        mock_observability_service.get_operational_stats.assert_called_once()
    
    def test_metrics_endpoint_exception(self, client, mock_observability_service):
        """Test metrics endpoint with exception."""
        # Mock exception
        mock_observability_service.get_operational_stats.side_effect = Exception("Metrics error")
        
        response = client.get("/metrics")
        
        assert response.status_code == 500
        data = response.json()
        
        assert data["detail"]["error"] == "metrics_collection_failed"
        assert "Metrics error" in data["detail"]["message"]
    
    def test_performance_metrics_endpoint(self, client, mock_observability_service):
        """Test performance metrics endpoint."""
        response = client.get("/metrics/performance")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["service"] == "agentcore-gateway-mcp-tools"
        assert "performance_summary" in data
        assert "endpoint_breakdown" in data
        assert "data_range" in data
        
        # Check performance summary
        summary = data["performance_summary"]
        assert summary["total_requests"] == 10
        assert "avg_duration_ms" in summary
        assert "min_duration_ms" in summary
        assert "max_duration_ms" in summary
        assert "p50_duration_ms" in summary
        assert "p95_duration_ms" in summary
        assert "p99_duration_ms" in summary
        
        # Check endpoint breakdown
        breakdown = data["endpoint_breakdown"]
        assert "/api/test" in breakdown
        
        endpoint_stats = breakdown["/api/test"]
        assert endpoint_stats["count"] == 10
        assert "avg_duration_ms" in endpoint_stats
        assert "avg_mcp_calls" in endpoint_stats
        assert "status_codes" in endpoint_stats
        
        # Check data range
        data_range = data["data_range"]
        assert data_range["limit"] == 100
        assert data_range["actual_records"] == 10
    
    def test_performance_metrics_endpoint_with_limit(self, client, mock_observability_service):
        """Test performance metrics endpoint with custom limit."""
        response = client.get("/metrics/performance?limit=5")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should only return last 5 records
        assert data["data_range"]["limit"] == 5
        assert data["data_range"]["actual_records"] == 5
        assert data["performance_summary"]["total_requests"] == 5
    
    def test_performance_metrics_endpoint_no_data(self, client, mock_observability_service):
        """Test performance metrics endpoint with no data."""
        # Mock empty performance history
        mock_observability_service.performance_history = []
        
        response = client.get("/metrics/performance")
        
        assert response.status_code == 200
        data = response.json()
        
        summary = data["performance_summary"]
        assert summary["total_requests"] == 0
        assert "message" in summary
        assert data["endpoint_breakdown"] == {}
    
    def test_performance_metrics_endpoint_exception(self, client, mock_observability_service):
        """Test performance metrics endpoint with exception."""
        # Mock exception
        mock_observability_service.performance_history = None
        
        response = client.get("/metrics/performance")
        
        assert response.status_code == 500
        data = response.json()
        
        assert data["detail"]["error"] == "performance_metrics_failed"
    
    def test_security_metrics_endpoint(self, client, mock_observability_service):
        """Test security metrics endpoint."""
        # Mock security events
        from services.observability_service import SecurityEvent
        mock_observability_service.security_events = [
            SecurityEvent(
                event_type=SecurityEventType.AUTH_SUCCESS,
                user_id="user-123",
                ip_address="192.168.1.1",
                user_agent="test-agent",
                endpoint="/api/test",
                details={}
            ),
            SecurityEvent(
                event_type=SecurityEventType.AUTH_FAILURE,
                user_id=None,
                ip_address="192.168.1.2",
                user_agent="test-agent",
                endpoint="/api/test",
                details={}
            )
        ]
        mock_observability_service.stats.auth_failures = 1
        
        response = client.get("/metrics/security")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["service"] == "agentcore-gateway-mcp-tools"
        assert "security_summary" in data
        assert "endpoint_breakdown" in data
        assert "data_range" in data
        
        # Check security summary
        summary = data["security_summary"]
        assert summary["total_events"] == 2
        assert summary["total_auth_failures"] == 1
        assert "event_types" in summary
        
        event_types = summary["event_types"]
        assert event_types["auth_success"] == 1
        assert event_types["auth_failure"] == 1
        
        # Check endpoint breakdown
        breakdown = data["endpoint_breakdown"]
        assert "/api/test" in breakdown
        
        endpoint_events = breakdown["/api/test"]
        assert endpoint_events["auth_success"] == 1
        assert endpoint_events["auth_failure"] == 1
    
    def test_security_metrics_endpoint_no_data(self, client, mock_observability_service):
        """Test security metrics endpoint with no data."""
        # Mock empty security events
        mock_observability_service.security_events = []
        
        response = client.get("/metrics/security")
        
        assert response.status_code == 200
        data = response.json()
        
        summary = data["security_summary"]
        assert summary["total_events"] == 0
        assert summary["event_types"] == {}
        assert data["endpoint_breakdown"] == {}
    
    def test_security_metrics_endpoint_exception(self, client, mock_observability_service):
        """Test security metrics endpoint with exception."""
        # Mock exception
        mock_observability_service.security_events = None
        
        response = client.get("/metrics/security")
        
        assert response.status_code == 500
        data = response.json()
        
        assert data["detail"]["error"] == "security_metrics_failed"
    
    def test_mcp_metrics_endpoint(self, client, mock_mcp_client_manager):
        """Test MCP metrics endpoint."""
        response = client.get("/metrics/mcp")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["service"] == "agentcore-gateway-mcp-tools"
        assert "mcp_summary" in data
        assert "server_details" in data
        
        # Check MCP summary
        summary = data["mcp_summary"]
        assert summary["total_servers"] == 2
        assert summary["healthy_servers"] == 2
        assert summary["health_rate_percent"] == 100.0  # 2/2 * 100
        assert "avg_response_time_ms" in summary
        
        # Check server details
        details = data["server_details"]
        assert "search-server" in details
        assert "reasoning-server" in details
        
        search_server = details["search-server"]
        assert search_server["status"] == "healthy"
        assert search_server["response_time_ms"] == 50.0
        assert search_server["consecutive_failures"] == 0
        
        reasoning_server = details["reasoning-server"]
        assert reasoning_server["status"] == "healthy"
        assert reasoning_server["response_time_ms"] == 75.0
        assert reasoning_server["consecutive_failures"] == 0
    
    def test_mcp_metrics_endpoint_exception(self, client, mock_mcp_client_manager):
        """Test MCP metrics endpoint with exception."""
        # Mock exception
        mock_mcp_client_manager.get_all_server_status.side_effect = Exception("MCP error")
        
        response = client.get("/metrics/mcp")
        
        assert response.status_code == 500
        data = response.json()
        
        assert data["detail"]["error"] == "mcp_metrics_failed"
        assert "MCP error" in data["detail"]["message"]


class TestObservabilityEndpointsIntegration:
    """Integration tests for observability endpoints."""
    
    def test_health_endpoint_dependency_injection(self):
        """Test that health endpoint properly injects dependencies."""
        app = FastAPI()
        app.include_router(router)
        
        # Mock dependencies
        mock_observability_service = Mock()
        mock_observability_service.get_health_status = AsyncMock(return_value={
            "status": "healthy",
            "service": "test"
        })
        
        mock_mcp_client_manager = Mock()
        
        app.dependency_overrides = {
            "services.observability_service.get_observability_service": lambda: mock_observability_service,
            "services.mcp_client_manager.get_mcp_client_manager": lambda: mock_mcp_client_manager
        }
        
        client = TestClient(app)
        response = client.get("/health")
        
        assert response.status_code == 200
        mock_observability_service.get_health_status.assert_called_once_with(mock_mcp_client_manager)
    
    def test_metrics_endpoint_dependency_injection(self):
        """Test that metrics endpoint properly injects dependencies."""
        app = FastAPI()
        app.include_router(router)
        
        # Mock dependencies
        mock_observability_service = Mock()
        mock_observability_service.get_operational_stats.return_value = {
            "total_requests": 0
        }
        mock_observability_service.metrics_namespace = "test"
        mock_observability_service.cloudwatch_client = None
        mock_observability_service.aws_region = "us-east-1"
        mock_observability_service.max_history_size = 1000
        
        app.dependency_overrides = {
            "services.observability_service.get_observability_service": lambda: mock_observability_service
        }
        
        client = TestClient(app)
        response = client.get("/metrics")
        
        assert response.status_code == 200
        mock_observability_service.get_operational_stats.assert_called_once()