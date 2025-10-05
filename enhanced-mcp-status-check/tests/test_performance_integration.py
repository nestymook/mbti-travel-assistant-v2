"""
Integration tests for performance optimization features.

This module provides comprehensive integration tests for all performance
optimization components working together.

Requirements: 10.1, 10.2, 10.3, 10.4, 10.5
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
from typing import List

from ..services.performance_optimizer import (
    PerformanceOptimizer,
    ConnectionPoolConfig,
    ResourceLimits,
    CacheConfig
)
from ..services.performance_benchmarker import (
    PerformanceBenchmarker,
    BenchmarkConfig,
    LoadTestScenario
)
from ..services.enhanced_health_check_service import EnhancedHealthCheckService
from ..models.dual_health_models import (
    DualHealthCheckResult,
    MCPHealthCheckResult,
    RESTHealthCheckResult,
    EnhancedServerConfig
)


class TestPerformanceOptimizationIntegration:
    """Integration tests for performance optimization."""
    
    @pytest.fixture
    def sample_server_configs(self):
        """Create sample server configurations."""
        return [
            EnhancedServerConfig(
                server_name='test-server-1',
                mcp_endpoint_url='http://localhost:8080',
                rest_health_endpoint_url='http://localhost:8080/health',
                mcp_timeout_seconds=10,
                rest_timeout_seconds=8,
                mcp_expected_tools=['tool1', 'tool2']
            ),
            EnhancedServerConfig(
                server_name='test-server-2',
                mcp_endpoint_url='http://localhost:8081',
                rest_health_endpoint_url='http://localhost:8081/health',
                mcp_timeout_seconds=10,
                rest_timeout_seconds=8,
                mcp_expected_tools=['tool3', 'tool4']
            ),
            EnhancedServerConfig(
                server_name='test-server-3',
                mcp_endpoint_url='http://localhost:8082',
                rest_health_endpoint_url='http://localhost:8082/health',
                mcp_timeout_seconds=10,
                rest_timeout_seconds=8,
                mcp_expected_tools=['tool5', 'tool6']
            )
        ]
        
    @pytest.fixture
    def performance_optimizer(self):
        """Create performance optimizer with test configuration."""
        connection_config = ConnectionPoolConfig(
            max_connections=20,
            max_connections_per_host=10,
            keepalive_timeout=30
        )
        
        resource_limits = ResourceLimits(
            max_concurrent_checks=10,
            max_memory_usage_mb=256,
            max_cpu_usage_percent=80.0,
            max_queue_size=50
        )
        
        cache_config = CacheConfig(
            config_cache_ttl=60,
            auth_token_cache_ttl=300,
            max_cache_size=100
        )
        
        return PerformanceOptimizer(
            connection_config=connection_config,
            resource_limits=resource_limits,
            cache_config=cache_config
        )
        
    @pytest.fixture
    async def mock_health_check_service(self):
        """Create mock health check service."""
        service = Mock(spec=EnhancedHealthCheckService)
        
        async def mock_dual_check(config):
            # Simulate variable response times
            delay = 0.1 + (hash(config.server_name) % 100) / 1000
            await asyncio.sleep(delay)
            
            return DualHealthCheckResult(
                server_name=config.server_name,
                timestamp=datetime.now(),
                overall_status='HEALTHY',
                overall_success=True,
                mcp_result=MCPHealthCheckResult(
                    server_name=config.server_name,
                    timestamp=datetime.now(),
                    success=True,
                    response_time_ms=delay * 1000 * 0.6,
                    tools_list_response=None,
                    tools_count=len(config.mcp_expected_tools or []),
                    expected_tools_found=config.mcp_expected_tools or [],
                    missing_tools=[],
                    validation_errors=[],
                    request_id='test_request',
                    jsonrpc_version='2.0',
                    mcp_error=None
                ),
                mcp_success=True,
                mcp_response_time_ms=delay * 1000 * 0.6,
                mcp_tools_count=len(config.mcp_expected_tools or []),
                mcp_error_message=None,
                rest_result=RESTHealthCheckResult(
                    server_name=config.server_name,
                    timestamp=datetime.now(),
                    success=True,
                    response_time_ms=delay * 1000 * 0.4,
                    status_code=200,
                    response_body={'status': 'healthy'},
                    health_endpoint_url=config.rest_health_endpoint_url,
                    server_metrics={'cpu': 45.0, 'memory': 60.0},
                    circuit_breaker_states={'default': 'CLOSED'},
                    system_health={'uptime': 3600},
                    http_error=None,
                    connection_error=None
                ),
                rest_success=True,
                rest_response_time_ms=delay * 1000 * 0.4,
                rest_status_code=200,
                rest_error_message=None,
                combined_response_time_ms=delay * 1000,
                health_score=1.0,
                available_paths=['mcp', 'rest']
            )
            
        service.perform_dual_health_check = AsyncMock(side_effect=mock_dual_check)
        return service
        
    @pytest.mark.asyncio
    async def test_full_optimization_workflow(
        self,
        performance_optimizer,
        sample_server_configs,
        mock_health_check_service
    ):
        """Test complete performance optimization workflow."""
        await performance_optimizer.initialize()
        
        try:
            # Test caching functionality
            cache_manager = performance_optimizer.cache_manager
            
            # Cache server configurations
            for config in sample_server_configs:
                cache_manager.set('config', config.to_dict(), config.server_name)
                
            # Cache authentication tokens
            for config in sample_server_configs:
                cache_manager.set('auth_tokens', f'token_{config.server_name}', config.server_name)
                
            # Verify caching works
            cached_config = cache_manager.get('config', sample_server_configs[0].server_name)
            assert cached_config is not None
            
            cached_token = cache_manager.get('auth_tokens', sample_server_configs[0].server_name)
            assert cached_token == f'token_{sample_server_configs[0].server_name}'
            
            # Test concurrent execution with resource monitoring
            async def health_check_wrapper(config):
                return await mock_health_check_service.perform_dual_health_check(config)
                
            start_time = time.time()
            results = await performance_optimizer.execute_concurrent_health_checks(
                sample_server_configs,
                health_check_wrapper,
                max_concurrent=5
            )
            execution_time = time.time() - start_time
            
            # Verify results
            assert len(results) == len(sample_server_configs)
            assert all(isinstance(result, DualHealthCheckResult) for result in results)
            assert execution_time < 1.0  # Should be faster than sequential
            
            # Test resource monitoring
            resource_stats = performance_optimizer.resource_monitor.get_resource_stats()
            assert 'active_checks' in resource_stats
            assert 'memory_usage_percent' in resource_stats
            
            # Test performance metrics
            metrics = performance_optimizer.get_performance_metrics()
            assert metrics.total_checks_performed > 0
            assert metrics.average_response_time_ms > 0
            
            # Test optimization recommendations
            recommendations = performance_optimizer.get_optimization_recommendations()
            assert isinstance(recommendations, list)
            
        finally:
            await performance_optimizer.shutdown()
            
    @pytest.mark.asyncio
    async def test_concurrent_execution_with_limits(
        self,
        performance_optimizer,
        sample_server_configs,
        mock_health_check_service
    ):
        """Test concurrent execution respects resource limits."""
        await performance_optimizer.initialize()
        
        try:
            # Create more servers than concurrent limit
            extended_configs = sample_server_configs * 5  # 15 servers total
            
            async def health_check_wrapper(config):
                return await mock_health_check_service.perform_dual_health_check(config)
                
            # Set low concurrent limit
            max_concurrent = 3
            
            start_time = time.time()
            results = await performance_optimizer.execute_concurrent_health_checks(
                extended_configs,
                health_check_wrapper,
                max_concurrent=max_concurrent
            )
            execution_time = time.time() - start_time
            
            # Should get results for all servers
            assert len(results) == len(extended_configs)
            
            # Should take longer due to concurrency limits
            # but still faster than pure sequential
            expected_min_time = len(extended_configs) / max_concurrent * 0.1 * 0.8
            assert execution_time >= expected_min_time
            
        finally:
            await performance_optimizer.shutdown()
            
    @pytest.mark.asyncio
    async def test_caching_performance_impact(
        self,
        performance_optimizer,
        sample_server_configs
    ):
        """Test caching performance impact."""
        await performance_optimizer.initialize()
        
        try:
            cache_manager = performance_optimizer.cache_manager
            
            # Test cache miss performance
            start_time = time.time()
            for i in range(100):
                result = cache_manager.get('config', f'key_{i}')
                assert result is None
            cache_miss_time = time.time() - start_time
            
            # Populate cache
            for i in range(100):
                cache_manager.set('config', {'data': f'value_{i}'}, f'key_{i}')
                
            # Test cache hit performance
            start_time = time.time()
            for i in range(100):
                result = cache_manager.get('config', f'key_{i}')
                assert result is not None
            cache_hit_time = time.time() - start_time
            
            # Cache hits should be faster than misses
            assert cache_hit_time <= cache_miss_time
            
            # Test cache statistics
            stats = cache_manager.get_stats()
            assert stats['config']['total_items'] == 100
            
        finally:
            await performance_optimizer.shutdown()
            
    @pytest.mark.asyncio
    async def test_batch_processing_optimization(
        self,
        performance_optimizer,
        sample_server_configs
    ):
        """Test batch processing optimization."""
        await performance_optimizer.initialize()
        
        try:
            batch_scheduler = performance_optimizer.batch_scheduler
            await batch_scheduler.start_scheduler()
            
            # Add requests to batches
            batch_ids = []
            for config in sample_server_configs:
                batch_id = await batch_scheduler.add_request(config, priority=1)
                batch_ids.append(batch_id)
                
            # Wait for batch processing
            await asyncio.sleep(batch_scheduler.batch_timeout + 0.5)
            
            # Check that batches were created
            ready_batches = await batch_scheduler.get_ready_batches()
            
            # Should have at least one batch
            total_servers_in_batches = sum(
                len(batch.server_configs) for batch in ready_batches
            )
            assert total_servers_in_batches >= len(sample_server_configs)
            
            await batch_scheduler.stop_scheduler()
            
        finally:
            await performance_optimizer.shutdown()
            
    @pytest.mark.asyncio
    async def test_resource_monitoring_limits(
        self,
        performance_optimizer,
        sample_server_configs
    ):
        """Test resource monitoring and limits enforcement."""
        await performance_optimizer.initialize()
        
        try:
            resource_monitor = performance_optimizer.resource_monitor
            await resource_monitor.start_monitoring()
            
            # Fill up to concurrent limit
            check_ids = []
            for i in range(resource_monitor.limits.max_concurrent_checks):
                check_id = f'test_check_{i}'
                success = resource_monitor.register_check(check_id)
                if success:
                    check_ids.append(check_id)
                    
            # Should have registered up to limit
            assert len(check_ids) == resource_monitor.limits.max_concurrent_checks
            
            # Next registration should fail
            overflow_success = resource_monitor.register_check('overflow_check')
            assert not overflow_success
            
            # Test queue functionality
            queue_success = resource_monitor.add_to_queue('queued_check', priority=1)
            assert queue_success
            
            # Unregister one check
            resource_monitor.unregister_check(check_ids[0])
            
            # Should now be able to register again
            new_success = resource_monitor.register_check('new_check')
            assert new_success
            
            # Cleanup
            for check_id in check_ids[1:]:
                resource_monitor.unregister_check(check_id)
            resource_monitor.unregister_check('new_check')
            
            await resource_monitor.stop_monitoring()
            
        finally:
            await performance_optimizer.shutdown()


class TestPerformanceBenchmarkingIntegration:
    """Integration tests for performance benchmarking."""
    
    @pytest.fixture
    def sample_server_configs(self):
        """Create sample server configurations."""
        return [
            EnhancedServerConfig(
                server_name=f'benchmark-server-{i}',
                mcp_endpoint_url=f'http://localhost:808{i}',
                rest_health_endpoint_url=f'http://localhost:808{i}/health'
            )
            for i in range(3)
        ]
        
    @pytest.fixture
    def performance_optimizer(self):
        """Create performance optimizer for benchmarking."""
        return PerformanceOptimizer(
            connection_config=ConnectionPoolConfig(max_connections=10),
            resource_limits=ResourceLimits(max_concurrent_checks=5),
            cache_config=CacheConfig(max_cache_size=50)
        )
        
    @pytest.fixture
    def benchmarker(self, performance_optimizer):
        """Create performance benchmarker."""
        return PerformanceBenchmarker(performance_optimizer)
        
    @pytest.mark.asyncio
    async def test_benchmark_execution(
        self,
        benchmarker,
        sample_server_configs
    ):
        """Test benchmark execution."""
        await benchmarker.optimizer.initialize()
        
        try:
            # Create simple benchmark config
            config = BenchmarkConfig(
                name='integration_test',
                description='Integration test benchmark',
                duration_seconds=3,
                concurrent_users=[1, 2],
                server_counts=[1, 2],
                iterations=1,
                warmup_duration=1,
                cooldown_duration=1
            )
            
            # Mock health check function
            async def mock_health_check(configs):
                await asyncio.sleep(0.01)  # Quick simulation
                return [
                    DualHealthCheckResult(
                        server_name=config.server_name,
                        timestamp=datetime.now(),
                        overall_status='HEALTHY',
                        overall_success=True,
                        mcp_result=None,
                        mcp_success=True,
                        mcp_response_time_ms=10.0,
                        mcp_tools_count=2,
                        mcp_error_message=None,
                        rest_result=None,
                        rest_success=True,
                        rest_response_time_ms=8.0,
                        rest_status_code=200,
                        rest_error_message=None,
                        combined_response_time_ms=9.0,
                        health_score=1.0,
                        available_paths=['mcp', 'rest']
                    )
                    for config in configs
                ]
                
            # Run benchmark
            results = await benchmarker.run_benchmark(
                config, mock_health_check, sample_server_configs
            )
            
            # Verify results
            assert len(results) > 0
            
            # Should have results for each combination
            expected_combinations = len(config.concurrent_users) * len(config.server_counts) * config.iterations
            assert len(results) == expected_combinations
            
            # Verify result structure
            for result in results:
                assert result.config_name == config.name
                assert result.total_requests >= 0
                assert result.requests_per_second >= 0
                assert result.average_response_time_ms >= 0
                
        finally:
            await benchmarker.optimizer.shutdown()
            
    @pytest.mark.asyncio
    async def test_load_test_scenario(
        self,
        benchmarker,
        sample_server_configs
    ):
        """Test load test scenario execution."""
        await benchmarker.optimizer.initialize()
        
        try:
            # Create load test scenario
            scenario = LoadTestScenario(
                name='integration_load_test',
                description='Integration load test',
                concurrent_users=3,
                duration_seconds=5,
                ramp_up_seconds=1,
                ramp_down_seconds=1,
                server_configs=sample_server_configs[:2]
            )
            
            # Mock health check function
            async def mock_health_check(configs):
                await asyncio.sleep(0.005)  # Very quick
                return []
                
            # Run load test
            result = await benchmarker.run_load_test(scenario, mock_health_check)
            
            # Verify result
            assert result.config_name == scenario.name
            assert result.concurrent_users == scenario.concurrent_users
            assert result.server_count == len(scenario.server_configs)
            
        finally:
            await benchmarker.optimizer.shutdown()
            
    @pytest.mark.asyncio
    async def test_benchmark_with_performance_optimization(
        self,
        benchmarker,
        sample_server_configs
    ):
        """Test benchmarking with performance optimization features."""
        await benchmarker.optimizer.initialize()
        
        try:
            # Enable caching
            cache_manager = benchmarker.optimizer.cache_manager
            
            # Pre-populate cache
            for config in sample_server_configs:
                cache_manager.set('config', config.to_dict(), config.server_name)
                cache_manager.set('auth_tokens', f'token_{config.server_name}', config.server_name)
                
            # Create benchmark that will benefit from caching
            config = BenchmarkConfig(
                name='cached_benchmark',
                description='Benchmark with caching',
                duration_seconds=2,
                concurrent_users=[2],
                server_counts=[2],
                iterations=1
            )
            
            # Mock health check that uses cache
            async def cached_health_check(configs):
                # Simulate cache lookups
                for config in configs:
                    cached_config = cache_manager.get('config', config.server_name)
                    cached_token = cache_manager.get('auth_tokens', config.server_name)
                    
                await asyncio.sleep(0.005)  # Reduced time due to caching
                
                return [
                    DualHealthCheckResult(
                        server_name=config.server_name,
                        timestamp=datetime.now(),
                        overall_status='HEALTHY',
                        overall_success=True,
                        mcp_result=None,
                        mcp_success=True,
                        mcp_response_time_ms=5.0,  # Faster due to caching
                        mcp_tools_count=2,
                        mcp_error_message=None,
                        rest_result=None,
                        rest_success=True,
                        rest_response_time_ms=4.0,
                        rest_status_code=200,
                        rest_error_message=None,
                        combined_response_time_ms=4.5,
                        health_score=1.0,
                        available_paths=['mcp', 'rest']
                    )
                    for config in configs
                ]
                
            # Run benchmark
            results = await benchmarker.run_benchmark(
                config, cached_health_check, sample_server_configs
            )
            
            # Verify caching improved performance
            assert len(results) > 0
            
            # Check cache statistics
            cache_stats = cache_manager.get_stats()
            assert cache_stats['config']['total_items'] > 0
            assert cache_stats['auth_tokens']['total_items'] > 0
            
            # Verify performance metrics
            optimizer_metrics = benchmarker.optimizer.get_performance_metrics()
            assert optimizer_metrics.cache_hit_rate > 0
            
        finally:
            await benchmarker.optimizer.shutdown()


class TestPerformanceOptimizationStressTest:
    """Stress tests for performance optimization."""
    
    @pytest.mark.asyncio
    async def test_high_concurrency_stress(self):
        """Test performance under high concurrency."""
        # Create optimizer with higher limits for stress testing
        optimizer = PerformanceOptimizer(
            connection_config=ConnectionPoolConfig(max_connections=50),
            resource_limits=ResourceLimits(max_concurrent_checks=25),
            cache_config=CacheConfig(max_cache_size=500)
        )
        
        await optimizer.initialize()
        
        try:
            # Create many server configurations
            server_configs = [
                EnhancedServerConfig(
                    server_name=f'stress-server-{i}',
                    mcp_endpoint_url=f'http://localhost:808{i % 10}',
                    rest_health_endpoint_url=f'http://localhost:808{i % 10}/health'
                )
                for i in range(50)
            ]
            
            # Mock health check with variable delays
            async def stress_health_check(config):
                delay = 0.01 + (hash(config.server_name) % 50) / 10000
                await asyncio.sleep(delay)
                
                return DualHealthCheckResult(
                    server_name=config.server_name,
                    timestamp=datetime.now(),
                    overall_status='HEALTHY',
                    overall_success=True,
                    mcp_result=None,
                    mcp_success=True,
                    mcp_response_time_ms=delay * 1000,
                    mcp_tools_count=3,
                    mcp_error_message=None,
                    rest_result=None,
                    rest_success=True,
                    rest_response_time_ms=delay * 800,
                    rest_status_code=200,
                    rest_error_message=None,
                    combined_response_time_ms=delay * 900,
                    health_score=1.0,
                    available_paths=['mcp', 'rest']
                )
                
            # Execute stress test
            start_time = time.time()
            results = await optimizer.execute_concurrent_health_checks(
                server_configs, stress_health_check, max_concurrent=20
            )
            execution_time = time.time() - start_time
            
            # Verify all requests completed
            assert len(results) == len(server_configs)
            
            # Should complete in reasonable time despite high load
            assert execution_time < 10.0  # Should not take more than 10 seconds
            
            # Check resource usage stayed within limits
            resource_stats = optimizer.resource_monitor.get_resource_stats()
            assert resource_stats['active_checks'] == 0  # All should be completed
            
            # Check performance metrics
            metrics = optimizer.get_performance_metrics()
            assert metrics.total_checks_performed >= len(server_configs)
            
        finally:
            await optimizer.shutdown()
            
    @pytest.mark.asyncio
    async def test_memory_usage_under_load(self):
        """Test memory usage under sustained load."""
        optimizer = PerformanceOptimizer(
            resource_limits=ResourceLimits(
                max_concurrent_checks=15,
                max_memory_usage_mb=128  # Lower limit for testing
            )
        )
        
        await optimizer.initialize()
        
        try:
            # Monitor memory usage during sustained operations
            initial_metrics = optimizer.get_performance_metrics()
            initial_memory = initial_metrics.memory_usage_mb
            
            # Perform multiple rounds of health checks
            server_configs = [
                EnhancedServerConfig(
                    server_name=f'memory-test-{i}',
                    mcp_endpoint_url=f'http://localhost:8080',
                    rest_health_endpoint_url=f'http://localhost:8080/health'
                )
                for i in range(20)
            ]
            
            async def memory_test_health_check(config):
                await asyncio.sleep(0.01)
                return DualHealthCheckResult(
                    server_name=config.server_name,
                    timestamp=datetime.now(),
                    overall_status='HEALTHY',
                    overall_success=True,
                    mcp_result=None,
                    mcp_success=True,
                    mcp_response_time_ms=10.0,
                    mcp_tools_count=2,
                    mcp_error_message=None,
                    rest_result=None,
                    rest_success=True,
                    rest_response_time_ms=8.0,
                    rest_status_code=200,
                    rest_error_message=None,
                    combined_response_time_ms=9.0,
                    health_score=1.0,
                    available_paths=['mcp', 'rest']
                )
                
            # Run multiple rounds
            for round_num in range(5):
                results = await optimizer.execute_concurrent_health_checks(
                    server_configs, memory_test_health_check
                )
                assert len(results) == len(server_configs)
                
                # Check memory usage
                current_metrics = optimizer.get_performance_metrics()
                
                # Memory should not grow excessively
                memory_growth = current_metrics.memory_usage_mb - initial_memory
                assert memory_growth < 50  # Should not grow by more than 50MB
                
        finally:
            await optimizer.shutdown()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])