"""
Integration tests for the complete observability system.

This module tests the end-to-end observability functionality including:
- Request tracking through middleware
- Metrics collection and reporting
- Health monitoring
- Security event logging
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, patch, AsyncMock
from fastapi import FastAPI, Depends, HTTPException
from fastapi.testclient import TestClient
from datetime import datetime, timezone

from middleware.observability_middleware import ObservabilityMiddleware
from middleware.jwt_validator import UserContext
from api.observability_endpoints import router as observability_router
from services.observability_service import ObservabilityService, SecurityEventType
from services.mcp_client_manager import MCPServerHealth, MCPServerStatus


class TestObservabilityIntegration:
    """Integration tests for complete observability system."""
    
    @pytest.fixture
    def mock_cloudwatch_client(self):
        """Mock CloudWatch client."""
        client = Mock()
        client.list_metrics.return_value = {"Metrics": []}
        client.put_metric_data.return_value = {"ResponseMetadata": {"HTTPStatusCode": 200}}
        return client
    
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
    def observability_service(self, mock_cloudwatch_client):
        """Create real observability service with mocked CloudWatch."""
        with patch('boto3.client', return_value=mock_cloudwatch_client):
            service = ObservabilityService(
                aws_region="us-east-1",
                service_name="test-integration-service"
            )
        return service
    
    @pytest.fixture
    def app_with_full_observability(self, observability_service, mock_mcp_client_manager):
        """Create FastAPI app with full observability stack."""
        app = FastAPI(title="Test Observability App")
        
        # Add observability middleware
        app.add_middleware(
            ObservabilityMiddleware,
            bypass_paths=["/health", "/metrics", "/docs"]
        )
        
        # Mock the global service functions
        with patch('services.observability_service.get_observability_service', return_value=observability_service), \
             patch('services.mcp_client_manager.get_mcp_client_manager', return_value=mock_mcp_client_manager), \
             patch('middleware.observability_middleware.get_observability_service', return_value=observability_service):
            
            # Include observability endpoints
            app.include_router(observability_router)
            
            # Test endpoints
            @app.get("/api/test")
            async def test_endpoint():
                return {"message": "success"}
            
            @app.get("/api/test-auth")
            async def test_auth_endpoint(request):
                # Simulate authenticated user
                request.state.user_context = UserContext(
                    user_id="test-user-123",
                    username="testuser",
                    email="test@example.com",
                    token_claims={"sub": "test-user-123"},
                    authenticated_at=datetime.now(timezone.utc)
                )
                return {"message": "authenticated"}
            
            @app.get("/api/test-mcp")
            async def test_mcp_endpoint(request):
                # Simulate MCP server calls
                from middleware.observability_middleware import add_mcp_server_call_tracking
                
                add_mcp_server_call_tracking(
                    request=request,
                    server_name="search-server",
                    tool_name="search_restaurants",
                    duration_ms=25.0
                )
                
                add_mcp_server_call_tracking(
                    request=request,
                    server_name="reasoning-server",
                    tool_name="analyze_sentiment",
                    duration_ms=50.0
                )
                
                return {"message": "mcp calls completed"}
            
            @app.get("/api/test-error")
            async def test_error_endpoint():
                raise HTTPException(status_code=500, detail="Test error")
            
            @app.get("/api/test-auth-error")
            async def test_auth_error_endpoint():
                raise HTTPException(status_code=401, detail="Authentication failed")
        
        return app
    
    @pytest.fixture
    def client(self, app_with_full_observability):
        """Create test client."""
        return TestClient(app_with_full_observability)
    
    def test_successful_request_end_to_end(self, client, observability_service):
        """Test successful request tracking end-to-end."""
        # Make a request
        response = client.get("/api/test")
        
        assert response.status_code == 200
        assert response.json() == {"message": "success"}
        
        # Check that metrics were recorded
        assert len(observability_service.performance_history) == 1
        
        metrics = observability_service.performance_history[0]
        assert metrics.endpoint == "/api/test"
        assert metrics.method == "GET"
        assert metrics.status_code == 200
        assert metrics.duration_ms > 0
        assert metrics.user_id is None
        assert metrics.mcp_server_calls == 0
        
        # Check operational stats
        assert observability_service.stats.total_requests == 1
        assert observability_service.stats.successful_requests == 1
        assert observability_service.stats.failed_requests == 0
    
    def test_authenticated_request_end_to_end(self, client, observability_service):
        """Test authenticated request tracking end-to-end."""
        # Make an authenticated request
        response = client.get("/api/test-auth")
        
        assert response.status_code == 200
        
        # Check that metrics were recorded with user context
        assert len(observability_service.performance_history) == 1
        
        metrics = observability_service.performance_history[0]
        assert metrics.user_id == "test-user-123"
        
        # Check that security event was logged
        assert len(observability_service.security_events) == 1
        
        event = observability_service.security_events[0]
        assert event.event_type == SecurityEventType.AUTH_SUCCESS
        assert event.user_id == "test-user-123"
        assert event.endpoint == "/api/test-auth"
    
    def test_mcp_server_calls_end_to_end(self, client, observability_service):
        """Test MCP server call tracking end-to-end."""
        # Make a request that simulates MCP server calls
        response = client.get("/api/test-mcp")
        
        assert response.status_code == 200
        
        # Check that metrics were recorded with MCP server calls
        assert len(observability_service.performance_history) == 1
        
        metrics = observability_service.performance_history[0]
        assert metrics.mcp_server_calls == 2
        assert metrics.mcp_server_duration_ms == 75.0  # 25.0 + 50.0
        
        # Check operational stats
        assert observability_service.stats.mcp_server_calls == 2
    
    def test_error_request_end_to_end(self, client, observability_service):
        """Test error request tracking end-to-end."""
        # Make a request that causes an error
        response = client.get("/api/test-error")
        
        assert response.status_code == 500
        
        # Check that error metrics were recorded
        assert len(observability_service.performance_history) == 1
        
        metrics = observability_service.performance_history[0]
        assert metrics.status_code == 500
        
        # Check operational stats
        assert observability_service.stats.total_requests == 1
        assert observability_service.stats.successful_requests == 0
        assert observability_service.stats.failed_requests == 1
    
    def test_authentication_error_end_to_end(self, client, observability_service):
        """Test authentication error tracking end-to-end."""
        # Make a request that causes an authentication error
        response = client.get("/api/test-auth-error")
        
        assert response.status_code == 401
        
        # Check that security event was logged
        assert len(observability_service.security_events) == 1
        
        event = observability_service.security_events[0]
        assert event.event_type == SecurityEventType.AUTH_FAILURE
        assert event.endpoint == "/api/test-auth-error"
        
        # Check operational stats
        assert observability_service.stats.auth_failures == 1
    
    def test_health_endpoint_integration(self, client, observability_service, mock_mcp_client_manager):
        """Test health endpoint integration."""
        # Make some requests first to generate data
        client.get("/api/test")
        client.get("/api/test-auth")
        
        # Check health endpoint
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "healthy"
        assert data["service"] == "test-integration-service"
        assert "uptime_seconds" in data
        assert "mcp_servers" in data
        assert "observability" in data
        
        # Check observability data includes our metrics
        observability_data = data["observability"]
        assert observability_data["total_requests"] == 2
        assert observability_data["performance_history_size"] == 2
        assert observability_data["security_events_count"] == 1
    
    def test_metrics_endpoint_integration(self, client, observability_service):
        """Test metrics endpoint integration."""
        # Make some requests first to generate data
        client.get("/api/test")
        client.get("/api/test-mcp")
        client.get("/api/test-error")
        
        # Check metrics endpoint
        response = client.get("/metrics")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["service"] == "agentcore-gateway-mcp-tools"
        
        metrics = data["metrics"]
        assert metrics["total_requests"] == 3
        assert metrics["successful_requests"] == 2
        assert metrics["failed_requests"] == 1
        assert metrics["mcp_server_calls"] == 2
        assert metrics["performance_history_size"] == 3
    
    def test_performance_metrics_endpoint_integration(self, client, observability_service):
        """Test performance metrics endpoint integration."""
        # Make requests with different performance characteristics
        client.get("/api/test")
        client.get("/api/test-mcp")  # This one has MCP calls
        
        # Check performance metrics endpoint
        response = client.get("/metrics/performance")
        
        assert response.status_code == 200
        data = response.json()
        
        summary = data["performance_summary"]
        assert summary["total_requests"] == 2
        assert summary["avg_duration_ms"] > 0
        
        # Check endpoint breakdown
        breakdown = data["endpoint_breakdown"]
        assert "/api/test" in breakdown
        assert "/api/test-mcp" in breakdown
        
        # The MCP endpoint should have higher MCP call average
        mcp_endpoint_stats = breakdown["/api/test-mcp"]
        assert mcp_endpoint_stats["avg_mcp_calls"] == 2.0
        
        regular_endpoint_stats = breakdown["/api/test"]
        assert regular_endpoint_stats["avg_mcp_calls"] == 0.0
    
    def test_security_metrics_endpoint_integration(self, client, observability_service):
        """Test security metrics endpoint integration."""
        # Make requests that generate security events
        client.get("/api/test-auth")  # Success
        client.get("/api/test-auth-error")  # Failure
        
        # Check security metrics endpoint
        response = client.get("/metrics/security")
        
        assert response.status_code == 200
        data = response.json()
        
        summary = data["security_summary"]
        assert summary["total_events"] == 2
        assert summary["total_auth_failures"] == 1
        
        event_types = summary["event_types"]
        assert event_types["auth_success"] == 1
        assert event_types["auth_failure"] == 1
        
        # Check endpoint breakdown
        breakdown = data["endpoint_breakdown"]
        assert "/api/test-auth" in breakdown
        assert "/api/test-auth-error" in breakdown
    
    def test_mcp_metrics_endpoint_integration(self, client, mock_mcp_client_manager):
        """Test MCP metrics endpoint integration."""
        response = client.get("/metrics/mcp")
        
        assert response.status_code == 200
        data = response.json()
        
        summary = data["mcp_summary"]
        assert summary["total_servers"] == 2
        assert summary["healthy_servers"] == 2
        assert summary["health_rate_percent"] == 100.0
        
        details = data["server_details"]
        assert "search-server" in details
        assert "reasoning-server" in details
    
    def test_bypass_paths_not_tracked(self, client, observability_service):
        """Test that bypass paths are not tracked for authentication."""
        # Make requests to bypass paths
        client.get("/health")
        client.get("/metrics")
        
        # Should have performance metrics but no security events
        assert len(observability_service.performance_history) == 2
        assert len(observability_service.security_events) == 0
        
        # Check that requests were counted
        assert observability_service.stats.total_requests == 2
        assert observability_service.stats.successful_requests == 2
    
    def test_multiple_requests_aggregation(self, client, observability_service):
        """Test that multiple requests are properly aggregated."""
        # Make multiple requests
        for i in range(5):
            client.get("/api/test")
        
        for i in range(3):
            client.get("/api/test-auth")
        
        for i in range(2):
            client.get("/api/test-error")
        
        # Check aggregated stats
        assert observability_service.stats.total_requests == 10
        assert observability_service.stats.successful_requests == 8
        assert observability_service.stats.failed_requests == 2
        assert len(observability_service.performance_history) == 10
        assert len(observability_service.security_events) == 3  # Only auth successes
        
        # Check metrics endpoint reflects aggregated data
        response = client.get("/metrics")
        data = response.json()
        
        metrics = data["metrics"]
        assert metrics["total_requests"] == 10
        assert metrics["successful_requests"] == 8
        assert metrics["failed_requests"] == 2
    
    def test_concurrent_requests_handling(self, app_with_full_observability, observability_service):
        """Test that concurrent requests are handled properly."""
        import threading
        import requests
        from unittest.mock import patch
        
        # Start the app in a separate thread (simplified test)
        results = []
        
        def make_request():
            client = TestClient(app_with_full_observability)
            response = client.get("/api/test")
            results.append(response.status_code)
        
        # Make concurrent requests
        threads = []
        for i in range(5):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check that all requests were successful
        assert len(results) == 5
        assert all(status == 200 for status in results)
        
        # Check that all requests were tracked
        assert observability_service.stats.total_requests == 5
        assert len(observability_service.performance_history) == 5
    
    @pytest.mark.asyncio
    async def test_cloudwatch_metrics_integration(self, observability_service, mock_cloudwatch_client):
        """Test CloudWatch metrics integration."""
        # Simulate some requests by directly calling the service
        observability_service.log_request_end(
            request_id="test-req-1",
            endpoint="/api/test",
            method="GET",
            status_code=200,
            start_time=time.time() - 0.1,
            mcp_server_calls=1,
            mcp_server_duration_ms=25.0
        )
        
        # Wait a bit for async CloudWatch calls to complete
        await asyncio.sleep(0.1)
        
        # Verify CloudWatch client was called
        mock_cloudwatch_client.put_metric_data.assert_called()
        
        # Check the metrics data
        call_args = mock_cloudwatch_client.put_metric_data.call_args
        assert call_args[1]["Namespace"] == "AgentCore/test-integration-service"
        
        metric_data = call_args[1]["MetricData"]
        metric_names = [m["MetricName"] for m in metric_data]
        
        assert "RequestDuration" in metric_names
        assert "RequestCount" in metric_names
        assert "MCPServerCalls" in metric_names
        assert "MCPServerDuration" in metric_names


class TestObservabilityPerformance:
    """Performance tests for observability system."""
    
    @pytest.fixture
    def lightweight_app(self):
        """Create lightweight app for performance testing."""
        app = FastAPI()
        
        # Mock observability service to avoid CloudWatch calls
        mock_service = Mock()
        mock_service.log_request_start.return_value = time.time()
        mock_service.log_request_end.return_value = None
        mock_service.log_security_event.return_value = None
        
        with patch('middleware.observability_middleware.get_observability_service', 
                  return_value=mock_service):
            app.add_middleware(ObservabilityMiddleware)
        
        @app.get("/fast")
        async def fast_endpoint():
            return {"status": "ok"}
        
        return app
    
    def test_observability_overhead(self, lightweight_app):
        """Test that observability middleware has minimal overhead."""
        client = TestClient(lightweight_app)
        
        # Measure time for requests with observability
        start_time = time.time()
        for i in range(100):
            response = client.get("/fast")
            assert response.status_code == 200
        end_time = time.time()
        
        total_time = end_time - start_time
        avg_time_per_request = total_time / 100
        
        # Should be very fast (less than 10ms per request including HTTP overhead)
        assert avg_time_per_request < 0.01, f"Average time per request: {avg_time_per_request:.4f}s"
    
    def test_memory_usage_with_history_limits(self):
        """Test that memory usage is controlled with history limits."""
        service = ObservabilityService(
            aws_region="us-east-1",
            service_name="memory-test"
        )
        service.max_history_size = 10
        service.cloudwatch_client = None  # Disable CloudWatch for this test
        
        # Add many performance metrics
        for i in range(100):
            service.log_request_end(
                request_id=f"req-{i}",
                endpoint="/api/test",
                method="GET",
                status_code=200,
                start_time=time.time() - 0.001
            )
        
        # Should only keep the last 10
        assert len(service.performance_history) == 10
        assert service.performance_history[0].request_id == "req-90"
        assert service.performance_history[-1].request_id == "req-99"
        
        # Add many security events
        for i in range(50):
            service.log_security_event(
                event_type=SecurityEventType.AUTH_SUCCESS,
                user_id=f"user-{i}",
                ip_address="192.168.1.1",
                user_agent="test",
                endpoint="/api/test",
                details={}
            )
        
        # Should only keep the last 10
        assert len(service.security_events) == 10
        assert service.security_events[0].user_id == "user-40"
        assert service.security_events[-1].user_id == "user-49"