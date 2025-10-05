"""
Performance and Concurrent Integration Tests.

Comprehensive integration tests for performance monitoring and concurrent dual monitoring.
Tests concurrent execution, resource management, performance optimization, and scalability.

Requirements covered: 3.1, 3.2
"""

import pytest
import asyncio
import time
import statistics
from unittest.mock import AsyncMock, patch
from typing import List, Dict, Any

from models.dual_health_models import (
    DualHealthCheckResult,
    EnhancedServerConfig,
    ServerStatus
)
from services.enhanced_health_check_service import EnhancedHealthCheckService
from services.performance_optimizer import PerformanceOptimizer


class TestPerformanceConcurrentIntegration:
    """Integration tests for performance and concurrent monitoring."""

    @pytest.fixture
    async def enhanced_service(self):
        """Create enhanced health check service for testing."""
        service = EnhancedHealthCheckService()
        await service.initialize()
        return service

    @pytest.fixture
    def performance_optimizer(self):
        """Create performance optimizer for testing."""
        return PerformanceOptimizer()

    @pytest.fixture
    def server_configs_small(self):
        """Create small set of server configurations for testing."""
        configs = []
        for i in range(3):
            config = EnhancedServerConfig(
                server_name=f"perf-server-{i}",
                mcp_endpoint_url=f"http://localhost:808{i}/mcp",
                rest_health_endpoint_url=f"http://localhost:808{i}/status/health",
                mcp_enabled=True,
                rest_enabled=True,
                mcp_timeout_seconds=5,
                rest_timeout_seconds=5
            )
            configs.append(config)
        return configs

    @pytest.fixture
    def server_configs_large(self):
        """Create large set of server configurations for testing."""
        configs = []
        for i in range(20):
            config = EnhancedServerConfig(
                server_name=f"scale-server-{i}",
                mcp_endpoint_url=f"http://localhost:{8080 + i}/mcp",
                rest_health_endpoint_url=f"http://localhost:{8080 + i}/status/health",
                mcp_enabled=True,
                rest_enabled=True,
                mcp_timeout_seconds=10,
                rest_timeout_seconds=8
            )
            configs.append(config)
        return configs

    async def test_concurrent_dual_monitoring_basic_performance(self, enhanced_service, server_configs_small):
        """
        Test basic concurrent dual monitoring performance.
        
        Requirements: 3.1, 3.2
        """
        with patch('aiohttp.ClientSession.post') as mock_post, \
             patch('aiohttp.ClientSession.get') as mock_get:
            
            # Configure successful responses with simulated delay
            async def mock_delayed_post(*args, **kwargs):
                await asyncio.sleep(0.1)  # 100ms delay
                mock_response = AsyncMock()
                mock_response.status = 200
                mock_response.json.return_value = {
                    "jsonrpc": "2.0",
                    "id": "test-123",
                    "result": {"tools": [{"name": "search_restaurants"}]}
                }
                return mock_response

            async def mock_delayed_get(*args, **kwargs):
                await asyncio.sleep(0.05)  # 50ms delay
                mock_response = AsyncMock()
                mock_response.status = 200
                mock_response.json.return_value = {"status": "healthy"}
                return mock_response

            mock_post.side_effect = mock_delayed_post
            mock_get.side_effect = mock_delayed_get

            # Measure concurrent execution time
            start_time = time.time()
            results = await enhanced_service.check_multiple_servers_dual(server_configs_small)
            end_time = time.time()

            # Verify results
            assert len(results) == 3
            for result in results:
                assert result.mcp_success is True
                assert result.rest_success is True
                assert result.overall_success is True

            # Verify concurrent execution was efficient
            execution_time = end_time - start_time
            # Should be much faster than sequential (3 * 0.15s = 0.45s)
            assert execution_time < 0.3  # Should complete in under 300ms

    async def test_concurrent_monitoring_resource_management(self, enhanced_service, server_configs_large):
        """
        Test resource management during concurrent monitoring of many servers.
        
        Requirements: 3.1, 3.2
        """
        connection_count = {'active': 0, 'max_active': 0}

        async def mock_resource_tracked_post(*args, **kwargs):
            connection_count['active'] += 1
            connection_count['max_active'] = max(connection_count['max_active'], connection_count['active'])
            
            await asyncio.sleep(0.02)  # Small delay
            
            connection_count['active'] -= 1
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = {
                "jsonrpc": "2.0",
                "id": "test-123",
                "result": {"tools": [{"name": "search_restaurants"}]}
            }
            return mock_response

        async def mock_resource_tracked_get(*args, **kwargs):
            connection_count['active'] += 1
            connection_count['max_active'] = max(connection_count['max_active'], connection_count['active'])
            
            await asyncio.sleep(0.01)  # Small delay
            
            connection_count['active'] -= 1
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = {"status": "healthy"}
            return mock_response

        with patch('aiohttp.ClientSession.post', side_effect=mock_resource_tracked_post), \
             patch('aiohttp.ClientSession.get', side_effect=mock_resource_tracked_get):

            results = await enhanced_service.check_multiple_servers_dual(server_configs_large)

            # Verify all requests completed successfully
            assert len(results) == 20
            for result in results:
                assert result.overall_success is True

            # Verify resource management (connection pooling should limit concurrent connections)
            # With 20 servers and dual monitoring, we expect some connection limiting
            assert connection_count['max_active'] <= 40  # Should not exceed reasonable limits

    async def test_concurrent_monitoring_with_mixed_response_times(self, enhanced_service, server_configs_small):
        """
        Test concurrent monitoring with servers having different response times.
        
        Requirements: 3.1, 3.2
        """
        response_times = [0.05, 0.15, 0.25]  # Different delays for each server
        
        def create_mock_post(delay):
            async def mock_post(*args, **kwargs):
                await asyncio.sleep(delay)
                mock_response = AsyncMock()
                mock_response.status = 200
                mock_response.json.return_value = {
                    "jsonrpc": "2.0",
                    "id": "test-123",
                    "result": {"tools": [{"name": "search_restaurants"}]}
                }
                return mock_response
            return mock_post

        def create_mock_get(delay):
            async def mock_get(*args, **kwargs):
                await asyncio.sleep(delay / 2)  # REST is faster
                mock_response = AsyncMock()
                mock_response.status = 200
                mock_response.json.return_value = {"status": "healthy"}
                return mock_response
            return mock_get

        # Test each server configuration with different response times
        for i, (config, delay) in enumerate(zip(server_configs_small, response_times)):
            with patch('aiohttp.ClientSession.post', side_effect=create_mock_post(delay)), \
                 patch('aiohttp.ClientSession.get', side_effect=create_mock_get(delay)):

                start_time = time.time()
                result = await enhanced_service.perform_dual_health_check(config)
                end_time = time.time()

                # Verify result
                assert result.overall_success is True
                
                # Verify response time measurement
                execution_time = (end_time - start_time) * 1000  # Convert to milliseconds
                assert result.mcp_response_time_ms >= delay * 1000 * 0.8  # Within 20% tolerance
                assert result.rest_response_time_ms >= (delay / 2) * 1000 * 0.8

    async def test_concurrent_monitoring_failure_isolation(self, enhanced_service, server_configs_small):
        """
        Test that failures in one server don't affect concurrent monitoring of others.
        
        Requirements: 3.1, 3.2
        """
        call_counts = {f'server-{i}': {'mcp': 0, 'rest': 0} for i in range(3)}

        def mock_post_side_effect(*args, **kwargs):
            url = kwargs.get('url', args[0] if args else '')
            
            if '8080' in url:
                # First server fails
                mock_response = AsyncMock()
                mock_response.status = 500
                mock_response.json.return_value = {"error": "Server error"}
                call_counts['server-0']['mcp'] += 1
                return mock_response
            elif '8081' in url:
                # Second server succeeds
                mock_response = AsyncMock()
                mock_response.status = 200
                mock_response.json.return_value = {
                    "jsonrpc": "2.0",
                    "id": "test-123",
                    "result": {"tools": [{"name": "search_restaurants"}]}
                }
                call_counts['server-1']['mcp'] += 1
                return mock_response
            else:
                # Third server succeeds
                mock_response = AsyncMock()
                mock_response.status = 200
                mock_response.json.return_value = {
                    "jsonrpc": "2.0",
                    "id": "test-123",
                    "result": {"tools": [{"name": "search_restaurants"}]}
                }
                call_counts['server-2']['mcp'] += 1
                return mock_response

        def mock_get_side_effect(*args, **kwargs):
            url = kwargs.get('url', args[0] if args else '')
            
            # All REST endpoints succeed
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = {"status": "healthy"}
            
            if '8080' in url:
                call_counts['server-0']['rest'] += 1
            elif '8081' in url:
                call_counts['server-1']['rest'] += 1
            else:
                call_counts['server-2']['rest'] += 1
                
            return mock_response

        with patch('aiohttp.ClientSession.post', side_effect=mock_post_side_effect), \
             patch('aiohttp.ClientSession.get', side_effect=mock_get_side_effect):

            results = await enhanced_service.check_multiple_servers_dual(server_configs_small)

            # Verify failure isolation
            assert len(results) == 3
            assert results[0].overall_success is False  # First server failed MCP
            assert results[1].overall_success is True   # Second server succeeded
            assert results[2].overall_success is True   # Third server succeeded

            # Verify all servers were attempted
            for i in range(3):
                assert call_counts[f'server-{i}']['mcp'] == 1
                assert call_counts[f'server-{i}']['rest'] == 1

    async def test_concurrent_monitoring_timeout_handling(self, enhanced_service, server_configs_small):
        """
        Test timeout handling in concurrent monitoring scenarios.
        
        Requirements: 3.1, 3.2
        """
        # Set short timeouts for testing
        for config in server_configs_small:
            config.mcp_timeout_seconds = 1
            config.rest_timeout_seconds = 1

        timeout_scenarios = [
            (0.5, 0.5),   # Both succeed within timeout
            (1.5, 0.5),   # MCP times out, REST succeeds
            (0.5, 1.5),   # MCP succeeds, REST times out
            (1.5, 1.5)    # Both timeout
        ]

        for i, (mcp_delay, rest_delay) in enumerate(timeout_scenarios[:len(server_configs_small)]):
            async def mock_delayed_post(*args, **kwargs):
                if mcp_delay > 1.0:
                    raise asyncio.TimeoutError("MCP timeout")
                await asyncio.sleep(mcp_delay)
                mock_response = AsyncMock()
                mock_response.status = 200
                mock_response.json.return_value = {
                    "jsonrpc": "2.0",
                    "id": "test-123",
                    "result": {"tools": [{"name": "search_restaurants"}]}
                }
                return mock_response

            async def mock_delayed_get(*args, **kwargs):
                if rest_delay > 1.0:
                    raise asyncio.TimeoutError("REST timeout")
                await asyncio.sleep(rest_delay)
                mock_response = AsyncMock()
                mock_response.status = 200
                mock_response.json.return_value = {"status": "healthy"}
                return mock_response

            with patch('aiohttp.ClientSession.post', side_effect=mock_delayed_post), \
                 patch('aiohttp.ClientSession.get', side_effect=mock_delayed_get):

                result = await enhanced_service.perform_dual_health_check(server_configs_small[i])

                # Verify timeout handling
                expected_mcp_success = mcp_delay <= 1.0
                expected_rest_success = rest_delay <= 1.0
                
                assert result.mcp_success == expected_mcp_success
                assert result.rest_success == expected_rest_success

    async def test_performance_metrics_collection_during_concurrent_monitoring(self, enhanced_service, server_configs_small):
        """
        Test performance metrics collection during concurrent monitoring.
        
        Requirements: 3.1, 3.2
        """
        with patch('aiohttp.ClientSession.post') as mock_post, \
             patch('aiohttp.ClientSession.get') as mock_get:
            
            # Configure responses with varying performance characteristics
            async def mock_variable_post(*args, **kwargs):
                url = kwargs.get('url', args[0] if args else '')
                if '8080' in url:
                    await asyncio.sleep(0.1)  # 100ms
                elif '8081' in url:
                    await asyncio.sleep(0.2)  # 200ms
                else:
                    await asyncio.sleep(0.05)  # 50ms
                
                mock_response = AsyncMock()
                mock_response.status = 200
                mock_response.json.return_value = {
                    "jsonrpc": "2.0",
                    "id": "test-123",
                    "result": {"tools": [{"name": "search_restaurants"}]}
                }
                return mock_response

            async def mock_variable_get(*args, **kwargs):
                url = kwargs.get('url', args[0] if args else '')
                if '8080' in url:
                    await asyncio.sleep(0.05)  # 50ms
                elif '8081' in url:
                    await asyncio.sleep(0.1)   # 100ms
                else:
                    await asyncio.sleep(0.02)  # 20ms
                
                mock_response = AsyncMock()
                mock_response.status = 200
                mock_response.json.return_value = {"status": "healthy"}
                return mock_response

            mock_post.side_effect = mock_variable_post
            mock_get.side_effect = mock_variable_get

            results = await enhanced_service.check_multiple_servers_dual(server_configs_small)

            # Verify performance metrics were collected
            assert len(results) == 3
            
            # Verify response times reflect the delays
            expected_mcp_times = [100, 200, 50]  # milliseconds
            expected_rest_times = [50, 100, 20]  # milliseconds
            
            for i, result in enumerate(results):
                assert result.mcp_response_time_ms >= expected_mcp_times[i] * 0.8  # 20% tolerance
                assert result.rest_response_time_ms >= expected_rest_times[i] * 0.8
                assert result.combined_response_time_ms > 0

    async def test_concurrent_monitoring_memory_usage_optimization(self, enhanced_service, server_configs_large):
        """
        Test memory usage optimization during concurrent monitoring of many servers.
        
        Requirements: 3.1, 3.2
        """
        import gc
        import psutil
        import os

        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss

        with patch('aiohttp.ClientSession.post') as mock_post, \
             patch('aiohttp.ClientSession.get') as mock_get:
            
            # Configure lightweight responses
            mock_post.return_value.__aenter__.return_value.status = 200
            mock_post.return_value.__aenter__.return_value.json.return_value = {
                "jsonrpc": "2.0",
                "id": "test-123",
                "result": {"tools": [{"name": "search_restaurants"}]}
            }
            
            mock_get.return_value.__aenter__.return_value.status = 200
            mock_get.return_value.__aenter__.return_value.json.return_value = {"status": "healthy"}

            # Perform concurrent monitoring
            results = await enhanced_service.check_multiple_servers_dual(server_configs_large)

            # Force garbage collection
            gc.collect()
            
            # Get final memory usage
            final_memory = process.memory_info().rss
            memory_increase = final_memory - initial_memory

            # Verify results
            assert len(results) == 20
            for result in results:
                assert result.overall_success is True

            # Verify memory usage is reasonable (less than 50MB increase for 20 servers)
            assert memory_increase < 50 * 1024 * 1024  # 50MB

    async def test_concurrent_monitoring_cpu_usage_optimization(self, enhanced_service, server_configs_small):
        """
        Test CPU usage optimization during concurrent monitoring.
        
        Requirements: 3.1, 3.2
        """
        import psutil
        
        # Monitor CPU usage during concurrent operations
        cpu_samples = []
        
        async def monitor_cpu():
            for _ in range(10):  # Sample CPU usage 10 times
                cpu_samples.append(psutil.cpu_percent(interval=0.1))
                await asyncio.sleep(0.1)

        with patch('aiohttp.ClientSession.post') as mock_post, \
             patch('aiohttp.ClientSession.get') as mock_get:
            
            # Configure responses with some processing delay
            async def mock_cpu_intensive_post(*args, **kwargs):
                # Simulate some CPU work
                await asyncio.sleep(0.05)
                mock_response = AsyncMock()
                mock_response.status = 200
                mock_response.json.return_value = {
                    "jsonrpc": "2.0",
                    "id": "test-123",
                    "result": {"tools": [{"name": "search_restaurants"}]}
                }
                return mock_response

            async def mock_cpu_intensive_get(*args, **kwargs):
                # Simulate some CPU work
                await asyncio.sleep(0.03)
                mock_response = AsyncMock()
                mock_response.status = 200
                mock_response.json.return_value = {"status": "healthy"}
                return mock_response

            mock_post.side_effect = mock_cpu_intensive_post
            mock_get.side_effect = mock_cpu_intensive_get

            # Run concurrent monitoring and CPU monitoring
            monitoring_task = asyncio.create_task(monitor_cpu())
            results_task = asyncio.create_task(
                enhanced_service.check_multiple_servers_dual(server_configs_small)
            )

            results, _ = await asyncio.gather(results_task, monitoring_task)

            # Verify results
            assert len(results) == 3
            for result in results:
                assert result.overall_success is True

            # Verify CPU usage remained reasonable
            if cpu_samples:
                avg_cpu = statistics.mean(cpu_samples)
                max_cpu = max(cpu_samples)
                
                # CPU usage should be reasonable for concurrent operations
                assert avg_cpu < 80.0  # Average CPU usage under 80%
                assert max_cpu < 95.0  # Peak CPU usage under 95%

    async def test_concurrent_monitoring_scalability_limits(self, enhanced_service):
        """
        Test scalability limits of concurrent monitoring system.
        
        Requirements: 3.1, 3.2
        """
        # Test with increasing numbers of servers
        server_counts = [5, 10, 15, 20]
        execution_times = []

        for count in server_counts:
            # Create server configurations
            configs = []
            for i in range(count):
                config = EnhancedServerConfig(
                    server_name=f"scale-test-{i}",
                    mcp_endpoint_url=f"http://localhost:{8080 + i}/mcp",
                    rest_health_endpoint_url=f"http://localhost:{8080 + i}/status/health",
                    mcp_enabled=True,
                    rest_enabled=True
                )
                configs.append(config)

            with patch('aiohttp.ClientSession.post') as mock_post, \
                 patch('aiohttp.ClientSession.get') as mock_get:
                
                # Configure fast responses
                mock_post.return_value.__aenter__.return_value.status = 200
                mock_post.return_value.__aenter__.return_value.json.return_value = {
                    "jsonrpc": "2.0",
                    "id": "test-123",
                    "result": {"tools": [{"name": "search_restaurants"}]}
                }
                
                mock_get.return_value.__aenter__.return_value.status = 200
                mock_get.return_value.__aenter__.return_value.json.return_value = {"status": "healthy"}

                # Measure execution time
                start_time = time.time()
                results = await enhanced_service.check_multiple_servers_dual(configs)
                end_time = time.time()

                execution_time = end_time - start_time
                execution_times.append(execution_time)

                # Verify all servers were processed
                assert len(results) == count
                for result in results:
                    assert result.overall_success is True

        # Verify scalability characteristics
        # Execution time should scale sub-linearly due to concurrency
        time_per_server = [t / c for t, c in zip(execution_times, server_counts)]
        
        # Time per server should decrease or remain stable as we scale up
        # (indicating good concurrent performance)
        assert time_per_server[-1] <= time_per_server[0] * 1.5  # Allow 50% increase max

    async def test_concurrent_monitoring_error_recovery_performance(self, enhanced_service, server_configs_small):
        """
        Test performance of error recovery in concurrent monitoring scenarios.
        
        Requirements: 3.1, 3.2
        """
        retry_counts = {'mcp': 0, 'rest': 0}
        
        def mock_post_with_retries(*args, **kwargs):
            retry_counts['mcp'] += 1
            if retry_counts['mcp'] <= 2:  # First two calls fail
                mock_response = AsyncMock()
                mock_response.status = 503
                mock_response.json.return_value = {"error": "Service unavailable"}
                return mock_response
            else:  # Third call succeeds
                mock_response = AsyncMock()
                mock_response.status = 200
                mock_response.json.return_value = {
                    "jsonrpc": "2.0",
                    "id": "test-123",
                    "result": {"tools": [{"name": "search_restaurants"}]}
                }
                return mock_response

        def mock_get_with_retries(*args, **kwargs):
            retry_counts['rest'] += 1
            if retry_counts['rest'] <= 1:  # First call fails
                mock_response = AsyncMock()
                mock_response.status = 502
                mock_response.json.return_value = {"error": "Bad gateway"}
                return mock_response
            else:  # Second call succeeds
                mock_response = AsyncMock()
                mock_response.status = 200
                mock_response.json.return_value = {"status": "healthy"}
                return mock_response

        # Configure retry attempts
        for config in server_configs_small:
            config.mcp_retry_attempts = 3
            config.rest_retry_attempts = 2

        with patch('aiohttp.ClientSession.post', side_effect=mock_post_with_retries), \
             patch('aiohttp.ClientSession.get', side_effect=mock_get_with_retries):

            start_time = time.time()
            results = await enhanced_service.check_multiple_servers_dual(server_configs_small)
            end_time = time.time()

            # Verify error recovery worked
            assert len(results) == 3
            for result in results:
                assert result.overall_success is True

            # Verify retry performance was reasonable
            execution_time = end_time - start_time
            # Should complete within reasonable time despite retries
            assert execution_time < 5.0  # Under 5 seconds for 3 servers with retries