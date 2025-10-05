"""
Tests for Enhanced Health Check Service

This module contains comprehensive tests for the Enhanced Health Check Service
orchestrator including dual health checks, concurrent execution, connection pooling,
and resource management.
"""

import asyncio
import pytest
import time
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from typing import List, Optional

from models.dual_health_models import (
    EnhancedServerConfig,
    MCPHealthCheckResult,
    RESTHealthCheckResult,
    DualHealthCheckResult,
    AggregationConfig,
    PriorityConfig,
    ServerStatus
)
from services.enhanced_health_check_service import (
    EnhancedHealthCheckService,
    ConnectionPoolManager,
    create_enhanced_health_check_service
)


class TestConnectionPoolManager:
    """Test cases for ConnectionPoolManager."""
    
    @pytest.mark.asyncio
    async def test_connection_pool_manager_initialization(self):
        """Test connection pool manager initialization."""
        pool_manager = ConnectionPoolManager(
            mcp_pool_size=5,
            rest_pool_size=8,
            connection_timeout=15,
            total_timeout=45
        )
        
        assert pool_manager.mcp_pool_size == 5
        assert pool_manager.rest_pool_size == 8
        assert pool_manager.connection_timeout == 15
        assert pool_manager.total_timeout == 45
        assert pool_manager._mcp_session is None
        assert pool_manager._rest_session is None
    
    @pytest.mark.asyncio
    async def test_get_mcp_session_creation(self):
        """Test MCP session creation."""
        async with ConnectionPoolManager() as pool_manager:
            session = await pool_manager.get_mcp_session()
            
            assert session is not None
            assert not session.closed
            assert pool_manager._mcp_session is session
            
            # Second call should return same session
            session2 = await pool_manager.get_mcp_session()
            assert session2 is session
    
    @pytest.mark.asyncio
    async def test_get_rest_session_creation(self):
        """Test REST session creation."""
        async with ConnectionPoolManager() as pool_manager:
            session = await pool_manager.get_rest_session()
            
            assert session is not None
            assert not session.closed
            assert pool_manager._rest_session is session
            
            # Second call should return same session
            session2 = await pool_manager.get_rest_session()
            assert session2 is session
    
    @pytest.mark.asyncio
    async def test_close_sessions(self):
        """Test session cleanup."""
        pool_manager = ConnectionPoolManager()
        
        # Create sessions
        mcp_session = await pool_manager.get_mcp_session()
        rest_session = await pool_manager.get_rest_session()
        
        assert not mcp_session.closed
        assert not rest_session.closed
        
        # Close sessions
        await pool_manager.close_sessions()
        
        assert mcp_session.closed
        assert rest_session.closed


class TestEnhancedHealthCheckService:
    """Test cases for EnhancedHealthCheckService."""
    
    def create_test_server_config(
        self,
        server_name: str = "test-server",
        mcp_enabled: bool = True,
        rest_enabled: bool = True
    ) -> EnhancedServerConfig:
        """Create test server configuration."""
        return EnhancedServerConfig(
            server_name=server_name,
            mcp_endpoint_url="http://localhost:8080/mcp",
            mcp_enabled=mcp_enabled,
            mcp_timeout_seconds=5,
            mcp_expected_tools=["search_restaurants", "recommend_restaurants"],
            rest_health_endpoint_url="http://localhost:8080/status/health",
            rest_enabled=rest_enabled,
            rest_timeout_seconds=3,
            jwt_token="test-token",
            auth_headers={"X-API-Key": "test-key"}
        )
    
    def create_mock_mcp_result(
        self,
        server_name: str = "test-server",
        success: bool = True,
        response_time_ms: float = 100.0
    ) -> MCPHealthCheckResult:
        """Create mock MCP health check result."""
        return MCPHealthCheckResult(
            server_name=server_name,
            timestamp=datetime.now(),
            success=success,
            response_time_ms=response_time_ms,
            tools_count=2 if success else None,
            expected_tools_found=["search_restaurants", "recommend_restaurants"] if success else [],
            missing_tools=[] if success else ["search_restaurants", "recommend_restaurants"],
            request_id="test-request-123"
        )
    
    def create_mock_rest_result(
        self,
        server_name: str = "test-server",
        success: bool = True,
        response_time_ms: float = 80.0
    ) -> RESTHealthCheckResult:
        """Create mock REST health check result."""
        return RESTHealthCheckResult(
            server_name=server_name,
            timestamp=datetime.now(),
            success=success,
            response_time_ms=response_time_ms,
            status_code=200 if success else 500,
            response_body={"status": "healthy"} if success else {"status": "unhealthy"},
            health_endpoint_url="http://localhost:8080/status/health"
        )
    
    @pytest.mark.asyncio
    async def test_service_initialization(self):
        """Test service initialization."""
        async with create_enhanced_health_check_service(
            max_concurrent_servers=5,
            max_concurrent_per_server=3
        ) as service:
            assert service.max_concurrent_servers == 5
            assert service.max_concurrent_per_server == 3
            assert service.aggregator is not None
            assert service.pool_manager is not None
            assert len(service._active_tasks) == 0
    
    @pytest.mark.asyncio
    async def test_perform_mcp_health_check_disabled(self):
        """Test MCP health check when disabled."""
        async with create_enhanced_health_check_service() as service:
            config = self.create_test_server_config(mcp_enabled=False)
            
            result = await service.perform_mcp_health_check(config)
            
            assert result.server_name == "test-server"
            assert not result.success
            assert "disabled" in result.connection_error.lower()
    
    @pytest.mark.asyncio
    async def test_perform_rest_health_check_disabled(self):
        """Test REST health check when disabled."""
        async with create_enhanced_health_check_service() as service:
            config = self.create_test_server_config(rest_enabled=False)
            
            result = await service.perform_rest_health_check(config)
            
            assert result.server_name == "test-server"
            assert not result.success
            assert "disabled" in result.connection_error.lower()
    
    @pytest.mark.asyncio
    async def test_perform_dual_health_check_both_enabled(self):
        """Test dual health check with both MCP and REST enabled."""
        config = self.create_test_server_config()
        
        with patch('services.enhanced_health_check_service.MCPHealthCheckClient') as mock_mcp_client, \
             patch('services.enhanced_health_check_service.RESTHealthCheckClient') as mock_rest_client:
            
            # Mock MCP client
            mock_mcp_instance = AsyncMock()
            mock_mcp_instance.perform_mcp_health_check.return_value = self.create_mock_mcp_result()
            mock_mcp_client.return_value.__aenter__.return_value = mock_mcp_instance
            
            # Mock REST client
            mock_rest_instance = AsyncMock()
            mock_rest_instance.perform_rest_health_check.return_value = self.create_mock_rest_result()
            mock_rest_client.return_value.__aenter__.return_value = mock_rest_instance
            
            async with create_enhanced_health_check_service() as service:
                result = await service.perform_dual_health_check(config)
                
                assert result.server_name == "test-server"
                assert result.overall_success
                assert result.overall_status == ServerStatus.HEALTHY
                assert result.mcp_success
                assert result.rest_success
                assert "both" in result.available_paths
                assert result.health_score > 0.0
    
    @pytest.mark.asyncio
    async def test_perform_dual_health_check_mcp_only(self):
        """Test dual health check with only MCP enabled."""
        config = self.create_test_server_config(rest_enabled=False)
        
        with patch('services.enhanced_health_check_service.MCPHealthCheckClient') as mock_mcp_client:
            # Mock MCP client
            mock_mcp_instance = AsyncMock()
            mock_mcp_instance.perform_mcp_health_check.return_value = self.create_mock_mcp_result()
            mock_mcp_client.return_value.__aenter__.return_value = mock_mcp_instance
            
            async with create_enhanced_health_check_service() as service:
                result = await service.perform_dual_health_check(config)
                
                assert result.server_name == "test-server"
                assert result.mcp_success
                assert not result.rest_success
                assert "mcp" in result.available_paths
                assert "rest" not in result.available_paths
    
    @pytest.mark.asyncio
    async def test_perform_dual_health_check_rest_only(self):
        """Test dual health check with only REST enabled."""
        config = self.create_test_server_config(mcp_enabled=False)
        
        with patch('services.enhanced_health_check_service.RESTHealthCheckClient') as mock_rest_client:
            # Mock REST client
            mock_rest_instance = AsyncMock()
            mock_rest_instance.perform_rest_health_check.return_value = self.create_mock_rest_result()
            mock_rest_client.return_value.__aenter__.return_value = mock_rest_instance
            
            async with create_enhanced_health_check_service() as service:
                result = await service.perform_dual_health_check(config)
                
                assert result.server_name == "test-server"
                assert not result.mcp_success
                assert result.rest_success
                assert "rest" in result.available_paths
                assert "mcp" not in result.available_paths
    
    @pytest.mark.asyncio
    async def test_perform_dual_health_check_neither_enabled(self):
        """Test dual health check with neither MCP nor REST enabled."""
        config = self.create_test_server_config(mcp_enabled=False, rest_enabled=False)
        
        async with create_enhanced_health_check_service() as service:
            result = await service.perform_dual_health_check(config)
            
            assert result.server_name == "test-server"
            assert not result.overall_success
            assert result.overall_status == ServerStatus.UNKNOWN
            assert "none" in result.available_paths
    
    @pytest.mark.asyncio
    async def test_perform_dual_health_check_timeout(self):
        """Test dual health check with timeout."""
        config = self.create_test_server_config()
        
        with patch('services.enhanced_health_check_service.MCPHealthCheckClient') as mock_mcp_client, \
             patch('services.enhanced_health_check_service.RESTHealthCheckClient') as mock_rest_client:
            
            # Mock clients to simulate slow response
            async def slow_mcp_check(*args, **kwargs):
                await asyncio.sleep(10)  # Longer than timeout
                return self.create_mock_mcp_result()
            
            async def slow_rest_check(*args, **kwargs):
                await asyncio.sleep(10)  # Longer than timeout
                return self.create_mock_rest_result()
            
            mock_mcp_instance = AsyncMock()
            mock_mcp_instance.perform_mcp_health_check.side_effect = slow_mcp_check
            mock_mcp_client.return_value.__aenter__.return_value = mock_mcp_instance
            
            mock_rest_instance = AsyncMock()
            mock_rest_instance.perform_rest_health_check.side_effect = slow_rest_check
            mock_rest_client.return_value.__aenter__.return_value = mock_rest_instance
            
            async with create_enhanced_health_check_service() as service:
                result = await service.perform_dual_health_check(config, timeout_override=1)
                
                assert result.server_name == "test-server"
                assert not result.overall_success
                assert result.overall_status == ServerStatus.UNHEALTHY
                assert "timeout" in result.mcp_error_message.lower()
                assert "timeout" in result.rest_error_message.lower()
    
    @pytest.mark.asyncio
    async def test_check_multiple_servers_dual(self):
        """Test batch dual health checks for multiple servers."""
        configs = [
            self.create_test_server_config("server-1"),
            self.create_test_server_config("server-2"),
            self.create_test_server_config("server-3")
        ]
        
        with patch('services.enhanced_health_check_service.MCPHealthCheckClient') as mock_mcp_client, \
             patch('services.enhanced_health_check_service.RESTHealthCheckClient') as mock_rest_client:
            
            # Mock MCP client
            mock_mcp_instance = AsyncMock()
            mock_mcp_instance.perform_mcp_health_check.side_effect = [
                self.create_mock_mcp_result("server-1"),
                self.create_mock_mcp_result("server-2"),
                self.create_mock_mcp_result("server-3")
            ]
            mock_mcp_client.return_value.__aenter__.return_value = mock_mcp_instance
            
            # Mock REST client
            mock_rest_instance = AsyncMock()
            mock_rest_instance.perform_rest_health_check.side_effect = [
                self.create_mock_rest_result("server-1"),
                self.create_mock_rest_result("server-2"),
                self.create_mock_rest_result("server-3")
            ]
            mock_rest_client.return_value.__aenter__.return_value = mock_rest_instance
            
            async with create_enhanced_health_check_service() as service:
                results = await service.check_multiple_servers_dual(configs)
                
                assert len(results) == 3
                for i, result in enumerate(results):
                    assert result.server_name == f"server-{i+1}"
                    assert result.overall_success
                    assert result.overall_status == ServerStatus.HEALTHY
    
    @pytest.mark.asyncio
    async def test_check_multiple_servers_dual_empty_list(self):
        """Test batch dual health checks with empty server list."""
        async with create_enhanced_health_check_service() as service:
            results = await service.check_multiple_servers_dual([])
            assert results == []
    
    @pytest.mark.asyncio
    async def test_check_multiple_servers_dual_with_failures(self):
        """Test batch dual health checks with some server failures."""
        configs = [
            self.create_test_server_config("server-1"),
            self.create_test_server_config("server-2")
        ]
        
        with patch('services.enhanced_health_check_service.MCPHealthCheckClient') as mock_mcp_client, \
             patch('services.enhanced_health_check_service.RESTHealthCheckClient') as mock_rest_client:
            
            # Mock MCP client - first succeeds, second fails
            mock_mcp_instance = AsyncMock()
            mock_mcp_instance.perform_mcp_health_check.side_effect = [
                self.create_mock_mcp_result("server-1", success=True),
                self.create_mock_mcp_result("server-2", success=False)
            ]
            mock_mcp_client.return_value.__aenter__.return_value = mock_mcp_instance
            
            # Mock REST client - both succeed
            mock_rest_instance = AsyncMock()
            mock_rest_instance.perform_rest_health_check.side_effect = [
                self.create_mock_rest_result("server-1", success=True),
                self.create_mock_rest_result("server-2", success=True)
            ]
            mock_rest_client.return_value.__aenter__.return_value = mock_rest_instance
            
            async with create_enhanced_health_check_service() as service:
                results = await service.check_multiple_servers_dual(configs)
                
                assert len(results) == 2
                assert results[0].overall_success  # Both MCP and REST succeed
                assert not results[1].overall_success  # MCP fails, should be degraded
                assert results[1].overall_status == ServerStatus.DEGRADED
    
    @pytest.mark.asyncio
    async def test_cancel_all_checks(self):
        """Test cancelling all active health checks."""
        config = self.create_test_server_config()
        
        with patch('services.enhanced_health_check_service.MCPHealthCheckClient') as mock_mcp_client, \
             patch('services.enhanced_health_check_service.RESTHealthCheckClient') as mock_rest_client:
            
            # Mock clients to simulate slow response
            async def slow_check(*args, **kwargs):
                await asyncio.sleep(5)
                return self.create_mock_mcp_result()
            
            mock_mcp_instance = AsyncMock()
            mock_mcp_instance.perform_mcp_health_check.side_effect = slow_check
            mock_mcp_client.return_value.__aenter__.return_value = mock_mcp_instance
            
            mock_rest_instance = AsyncMock()
            mock_rest_instance.perform_rest_health_check.side_effect = slow_check
            mock_rest_client.return_value.__aenter__.return_value = mock_rest_instance
            
            async with create_enhanced_health_check_service() as service:
                # Start health check (don't await)
                task = asyncio.create_task(service.perform_dual_health_check(config))
                
                # Give it time to start
                await asyncio.sleep(0.1)
                
                # Should have active tasks
                assert len(service._active_tasks) > 0
                
                # Cancel all checks
                await service.cancel_all_checks()
                
                # Should have no active tasks
                assert len(service._active_tasks) == 0
                
                # Original task should be cancelled
                assert task.cancelled() or task.done()
    
    @pytest.mark.asyncio
    async def test_cancel_server_checks(self):
        """Test cancelling health checks for specific server."""
        configs = [
            self.create_test_server_config("server-1"),
            self.create_test_server_config("server-2")
        ]
        
        with patch('services.enhanced_health_check_service.MCPHealthCheckClient') as mock_mcp_client, \
             patch('services.enhanced_health_check_service.RESTHealthCheckClient') as mock_rest_client:
            
            # Mock clients to simulate slow response
            async def slow_check(*args, **kwargs):
                await asyncio.sleep(5)
                return self.create_mock_mcp_result()
            
            mock_mcp_instance = AsyncMock()
            mock_mcp_instance.perform_mcp_health_check.side_effect = slow_check
            mock_mcp_client.return_value.__aenter__.return_value = mock_mcp_instance
            
            mock_rest_instance = AsyncMock()
            mock_rest_instance.perform_rest_health_check.side_effect = slow_check
            mock_rest_client.return_value.__aenter__.return_value = mock_rest_instance
            
            async with create_enhanced_health_check_service() as service:
                # Start health checks for both servers
                task1 = asyncio.create_task(service.perform_dual_health_check(configs[0]))
                task2 = asyncio.create_task(service.perform_dual_health_check(configs[1]))
                
                # Give them time to start
                await asyncio.sleep(0.1)
                
                # Should have active tasks for both servers
                initial_task_count = len(service._active_tasks)
                assert initial_task_count > 0
                
                # Cancel checks for server-1 only
                await service.cancel_server_checks("server-1")
                
                # Should have fewer active tasks
                remaining_task_count = len(service._active_tasks)
                assert remaining_task_count < initial_task_count
                
                # Clean up remaining tasks
                await service.cancel_all_checks()
                
                # Tasks should be cancelled
                assert task1.cancelled() or task1.done()
                assert task2.cancelled() or task2.done()
    
    @pytest.mark.asyncio
    async def test_get_active_checks(self):
        """Test getting active check information."""
        async with create_enhanced_health_check_service() as service:
            # Initially no active checks
            active_checks = service.get_active_checks()
            assert len(active_checks) == 0
            
            # Create a real async task for testing
            async def dummy_task():
                await asyncio.sleep(1)
            
            task = asyncio.create_task(dummy_task())
            service._active_tasks["test-task"] = task
            
            try:
                active_checks = service.get_active_checks()
                assert len(active_checks) == 1
                assert "test-task" in active_checks
                assert active_checks["test-task"] == "running"
            finally:
                # Clean up the task
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
    
    @pytest.mark.asyncio
    async def test_perform_health_check_with_circuit_breaker(self):
        """Test health check with circuit breaker states."""
        config = self.create_test_server_config()
        
        with patch('services.enhanced_health_check_service.MCPHealthCheckClient') as mock_mcp_client, \
             patch('services.enhanced_health_check_service.RESTHealthCheckClient') as mock_rest_client:
            
            mock_mcp_instance = AsyncMock()
            mock_mcp_instance.perform_mcp_health_check.return_value = self.create_mock_mcp_result()
            mock_mcp_client.return_value.__aenter__.return_value = mock_mcp_instance
            
            mock_rest_instance = AsyncMock()
            mock_rest_instance.perform_rest_health_check.return_value = self.create_mock_rest_result()
            mock_rest_client.return_value.__aenter__.return_value = mock_rest_instance
            
            async with create_enhanced_health_check_service() as service:
                # Test MCP_ONLY circuit breaker state
                result = await service.perform_health_check_with_circuit_breaker(
                    config, circuit_breaker_state="MCP_ONLY"
                )
                assert result.mcp_success
                assert not result.rest_success  # Should be disabled
                
                # Test REST_ONLY circuit breaker state
                result = await service.perform_health_check_with_circuit_breaker(
                    config, circuit_breaker_state="REST_ONLY"
                )
                assert not result.mcp_success  # Should be disabled
                assert result.rest_success
                
                # Test OPEN circuit breaker state
                result = await service.perform_health_check_with_circuit_breaker(
                    config, circuit_breaker_state="OPEN"
                )
                assert not result.overall_success
                assert result.overall_status == ServerStatus.UNHEALTHY
                assert "circuit breaker open" in result.mcp_error_message.lower()
    
    @pytest.mark.asyncio
    async def test_get_connection_pool_stats(self):
        """Test getting connection pool statistics."""
        async with create_enhanced_health_check_service() as service:
            stats = await service.get_connection_pool_stats()
            
            assert "mcp_pool" in stats
            assert "rest_pool" in stats
            assert "active_tasks" in stats
            assert "server_semaphore_available" in stats
            assert "per_server_semaphore_available" in stats
            
            assert stats["active_tasks"] == 0
            assert stats["mcp_pool"]["configured_size"] == 10
            assert stats["rest_pool"]["configured_size"] == 15
    
    def test_update_concurrency_limits(self):
        """Test updating concurrency limits."""
        async def run_test():
            async with create_enhanced_health_check_service() as service:
                original_servers = service.max_concurrent_servers
                original_per_server = service.max_concurrent_per_server
                
                service.update_concurrency_limits(
                    max_concurrent_servers=20,
                    max_concurrent_per_server=5
                )
                
                assert service.max_concurrent_servers == 20
                assert service.max_concurrent_per_server == 5
                assert service.max_concurrent_servers != original_servers
                assert service.max_concurrent_per_server != original_per_server
        
        asyncio.run(run_test())
    
    @pytest.mark.asyncio
    async def test_health_check_with_retry_backoff_success_first_attempt(self):
        """Test health check with retry backoff - success on first attempt."""
        config = self.create_test_server_config()
        
        with patch('services.enhanced_health_check_service.MCPHealthCheckClient') as mock_mcp_client, \
             patch('services.enhanced_health_check_service.RESTHealthCheckClient') as mock_rest_client:
            
            mock_mcp_instance = AsyncMock()
            mock_mcp_instance.perform_mcp_health_check.return_value = self.create_mock_mcp_result()
            mock_mcp_client.return_value.__aenter__.return_value = mock_mcp_instance
            
            mock_rest_instance = AsyncMock()
            mock_rest_instance.perform_rest_health_check.return_value = self.create_mock_rest_result()
            mock_rest_client.return_value.__aenter__.return_value = mock_rest_instance
            
            async with create_enhanced_health_check_service() as service:
                start_time = time.time()
                result = await service.health_check_with_retry_backoff(config, max_retries=3)
                end_time = time.time()
                
                assert result.overall_success
                assert result.overall_status == ServerStatus.HEALTHY
                # Should complete quickly on first attempt
                assert (end_time - start_time) < 1.0
    
    @pytest.mark.asyncio
    async def test_health_check_with_retry_backoff_success_after_retries(self):
        """Test health check with retry backoff - success after retries."""
        config = self.create_test_server_config()
        
        with patch('services.enhanced_health_check_service.MCPHealthCheckClient') as mock_mcp_client, \
             patch('services.enhanced_health_check_service.RESTHealthCheckClient') as mock_rest_client:
            
            # Mock to fail first two attempts, succeed on third
            call_count = 0
            
            async def mock_dual_check(*args, **kwargs):
                nonlocal call_count
                call_count += 1
                if call_count < 3:
                    return DualHealthCheckResult(
                        server_name="test-server",
                        timestamp=datetime.now(),
                        overall_status=ServerStatus.UNHEALTHY,
                        overall_success=False,
                        available_paths=["none"]
                    )
                else:
                    return DualHealthCheckResult(
                        server_name="test-server",
                        timestamp=datetime.now(),
                        overall_status=ServerStatus.HEALTHY,
                        overall_success=True,
                        available_paths=["both"]
                    )
            
            async with create_enhanced_health_check_service() as service:
                # Patch the perform_dual_health_check method
                service.perform_dual_health_check = mock_dual_check
                
                start_time = time.time()
                result = await service.health_check_with_retry_backoff(
                    config, max_retries=3, backoff_factor=1.1  # Small backoff for faster test
                )
                end_time = time.time()
                
                assert result.overall_success
                assert result.overall_status == ServerStatus.HEALTHY
                assert call_count == 3  # Should have made 3 attempts
                # Should take some time due to backoff
                assert (end_time - start_time) > 1.0
    
    @pytest.mark.asyncio
    async def test_health_check_with_retry_backoff_all_attempts_fail(self):
        """Test health check with retry backoff - all attempts fail."""
        config = self.create_test_server_config()
        
        async def mock_dual_check(*args, **kwargs):
            return DualHealthCheckResult(
                server_name="test-server",
                timestamp=datetime.now(),
                overall_status=ServerStatus.UNHEALTHY,
                overall_success=False,
                available_paths=["none"]
            )
        
        async with create_enhanced_health_check_service() as service:
            # Patch the perform_dual_health_check method
            service.perform_dual_health_check = mock_dual_check
            
            result = await service.health_check_with_retry_backoff(
                config, max_retries=2, backoff_factor=1.1  # Small backoff for faster test
            )
            
            assert not result.overall_success
            assert result.overall_status == ServerStatus.UNHEALTHY


class TestIntegrationScenarios:
    """Integration test scenarios for Enhanced Health Check Service."""
    
    @pytest.mark.asyncio
    async def test_concurrent_dual_health_checks_performance(self):
        """Test performance of concurrent dual health checks."""
        # Create multiple server configurations
        configs = [
            EnhancedServerConfig(
                server_name=f"server-{i}",
                mcp_endpoint_url=f"http://localhost:808{i}/mcp",
                rest_health_endpoint_url=f"http://localhost:808{i}/status/health"
            )
            for i in range(10)
        ]
        
        with patch('services.enhanced_health_check_service.MCPHealthCheckClient') as mock_mcp_client, \
             patch('services.enhanced_health_check_service.RESTHealthCheckClient') as mock_rest_client:
            
            # Mock clients with realistic response times
            async def mock_mcp_check(*args, **kwargs):
                await asyncio.sleep(0.1)  # Simulate 100ms response
                return MCPHealthCheckResult(
                    server_name="test-server",
                    timestamp=datetime.now(),
                    success=True,
                    response_time_ms=100.0,
                    tools_count=2
                )
            
            async def mock_rest_check(*args, **kwargs):
                await asyncio.sleep(0.08)  # Simulate 80ms response
                return RESTHealthCheckResult(
                    server_name="test-server",
                    timestamp=datetime.now(),
                    success=True,
                    response_time_ms=80.0,
                    status_code=200
                )
            
            mock_mcp_instance = AsyncMock()
            mock_mcp_instance.perform_mcp_health_check.side_effect = mock_mcp_check
            mock_mcp_client.return_value.__aenter__.return_value = mock_mcp_instance
            
            mock_rest_instance = AsyncMock()
            mock_rest_instance.perform_rest_health_check.side_effect = mock_rest_check
            mock_rest_client.return_value.__aenter__.return_value = mock_rest_instance
            
            async with create_enhanced_health_check_service(max_concurrent_servers=5) as service:
                start_time = time.time()
                results = await service.check_multiple_servers_dual(configs)
                end_time = time.time()
                
                # Verify results
                assert len(results) == 10
                for result in results:
                    assert result.overall_success
                    assert result.overall_status == ServerStatus.HEALTHY
                
                # Performance check - should complete much faster than sequential
                total_time = end_time - start_time
                sequential_time = 10 * 0.1  # 10 servers * 100ms each
                assert total_time < sequential_time * 0.8  # At least 20% faster
    
    @pytest.mark.asyncio
    async def test_resource_cleanup_on_service_exit(self):
        """Test proper resource cleanup when service exits."""
        config = EnhancedServerConfig(
            server_name="test-server",
            mcp_endpoint_url="http://localhost:8080/mcp",
            rest_health_endpoint_url="http://localhost:8080/status/health"
        )
        
        service = None
        pool_manager = None
        
        with patch('services.enhanced_health_check_service.MCPHealthCheckClient') as mock_mcp_client, \
             patch('services.enhanced_health_check_service.RESTHealthCheckClient') as mock_rest_client:
            
            # Mock clients to simulate slow response
            async def slow_check(*args, **kwargs):
                await asyncio.sleep(5)
                return MCPHealthCheckResult(
                    server_name="test-server",
                    timestamp=datetime.now(),
                    success=True,
                    response_time_ms=100.0
                )
            
            mock_mcp_instance = AsyncMock()
            mock_mcp_instance.perform_mcp_health_check.side_effect = slow_check
            mock_mcp_client.return_value.__aenter__.return_value = mock_mcp_instance
            
            mock_rest_instance = AsyncMock()
            mock_rest_instance.perform_rest_health_check.side_effect = slow_check
            mock_rest_client.return_value.__aenter__.return_value = mock_rest_instance
            
            # Create service and start a long-running check
            async with create_enhanced_health_check_service() as svc:
                service = svc
                pool_manager = svc.pool_manager
                
                # Start health check (don't await)
                task = asyncio.create_task(service.perform_dual_health_check(config))
                
                # Give it time to start
                await asyncio.sleep(0.1)
                
                # Should have active tasks
                assert len(service._active_tasks) > 0
                
                # Get sessions to verify they exist
                mcp_session = await pool_manager.get_mcp_session()
                rest_session = await pool_manager.get_rest_session()
                
                assert not mcp_session.closed
                assert not rest_session.closed
            
            # After exiting context manager, everything should be cleaned up
            assert len(service._active_tasks) == 0
            
            # Sessions should be closed
            assert mcp_session.closed
            assert rest_session.closed
            
            # Task should be cancelled
            assert task.cancelled() or task.done()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])