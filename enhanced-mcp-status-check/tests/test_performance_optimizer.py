"""
Tests for performance optimization features.

This module tests all performance optimization components including:
- Concurrent execution
- Connection pooling
- Request batching and scheduling
- Resource monitoring
- Caching
- Performance benchmarking

Requirements: 10.1, 10.2, 10.3, 10.4, 10.5
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta
from typing import List

from ..services.performance_optimizer import (
    PerformanceOptimizer,
    ConnectionPoolManager,
    CacheManager,
    ResourceMonitor,
    BatchScheduler,
    ConnectionPoolConfig,
    ResourceLimits,
    CacheConfig,
    PerformanceMetrics,
    BatchRequest
)
from ..services.performance_benchmarker import (
    PerformanceBenchmarker,
    BenchmarkConfig,
    BenchmarkResult,
    LoadTestScenario,
    MetricsCollector
)
from ..models.dual_health_models import (
    DualHealthCheckResult,
    MCPHealthCheckResult,
    RESTHealthCheckResult,
    EnhancedServerConfig
)


class TestConnectionPoolManager:
    """Test connection pool management."""
    
    @pytest.fixture
    def pool_config(self):
        return ConnectionPoolConfig(
            max_connections=10,
            max_connections_per_host=5,
            keepalive_timeout=30,
            connection_timeout=5,
            read_timeout=10
        )
        
    @pytest.fixture
    def pool_manager(self, pool_config):
        return ConnectionPoolManager(pool_config)
        
    @pytest.mark.asyncio
    async def test_initialize_pools(self, pool_manager):
        """Test connection pool initialization."""
        await pool_manager.initialize()
        
        assert pool_manager.mcp_pool is not None
        assert pool_manager.rest_pool is not None
        
        await pool_manager.close()
        
    @pytest.mark.asyncio
    async def test_get_sessions(self, pool_manager):
        """Test getting connection sessions."""
        mcp_session = await pool_manager.get_mcp_session()
        rest_session = await pool_manager.get_rest_session()
        
        assert mcp_session is not None
        assert rest_session is not None
        assert mcp_session != rest_session
        
        await pool_manager.close()
        
    @pytest.mark.asyncio
    async def test_pool_stats(self, pool_manager):
        """Test connection pool statistics."""
        await pool_manager.initialize()
        
        stats = pool_manager.get_pool_stats()
        
        assert 'mcp_pool' in stats
        assert 'rest_pool' in stats
        assert 'active' in stats['mcp_pool']
        assert 'available' in stats['mcp_pool']
        assert 'total' in stats['mcp_pool']
        
        await pool_manager.close()
        
    @pytest.mark.asyncio
    async def test_pool_cleanup(self, pool_manager):
        """Test periodic pool cleanup."""
        await pool_manager.initialize()
        
        # Start cleanup task
        cleanup_task = asyncio.create_task(pool_manager._periodic_cleanup())
        
        # Let it run briefly
        await asyncio.sleep(0.1)
        
        # Cancel and cleanup
        cleanup_task.cancel()
        await pool_manager.close()


class TestCacheManager:
    """Test cache management."""
    
    @pytest.fixture
    def cache_config(self):
        return CacheConfig(
            config_cache_ttl=60,
            auth_token_cache_ttl=300,
            dns_cache_ttl=120,
            result_cache_ttl=30,
            max_cache_size=100
        )
        
    @pytest.fixture
    def cache_manager(self, cache_config):
        return CacheManager(cache_config)
        
    def test_cache_set_get(self, cache_manager):
        """Test basic cache set and get operations."""
        # Test setting and getting values
        cache_manager.set('config', {'key': 'value'}, 'test_key')
        result = cache_manager.get('config', 'test_key')
        
        assert result == {'key': 'value'}
        
    def test_cache_expiration(self, cache_manager):
        """Test cache expiration."""
        # Set with very short TTL
        cache_manager.set('config', 'test_value', 1, 'test_key')
        
        # Should be available immediately
        assert cache_manager.get('config', 'test_key') == 'test_value'
        
        # Wait for expiration
        time.sleep(1.1)
        
        # Should be expired
        assert cache_manager.get('config', 'test_key') is None
        
    def test_cache_eviction(self, cache_manager):
        """Test cache eviction when size limit is reached."""
        # Fill cache to limit
        for i in range(cache_manager.config.max_cache_size + 10):
            cache_manager.set('config', f'value_{i}', f'key_{i}')
            
        # Check that cache size is maintained
        cache_stats = cache_manager.get_stats()
        assert cache_stats['config']['total_items'] <= cache_manager.config.max_cache_size
        
    def test_cache_stats(self, cache_manager):
        """Test cache statistics."""
        # Add some items
        cache_manager.set('config', 'value1', 'key1')
        cache_manager.set('auth_tokens', 'token1', 'key2')
        
        stats = cache_manager.get_stats()
        
        assert 'config' in stats
        assert 'auth_tokens' in stats
        assert stats['config']['total_items'] >= 1
        assert stats['auth_tokens']['total_items'] >= 1
        
    def test_clear_category(self, cache_manager):
        """Test clearing cache category."""
        cache_manager.set('config', 'value1', 'key1')
        cache_manager.set('config', 'value2', 'key2')
        
        assert cache_manager.get('config', 'key1') == 'value1'
        
        cache_manager.clear_category('config')
        
        assert cache_manager.get('config', 'key1') is None
        assert cache_manager.get('config', 'key2') is None
        
    @pytest.mark.asyncio
    async def test_cleanup_task(self, cache_manager):
        """Test periodic cleanup task."""
        await cache_manager.start_cleanup_task()
        
        # Add expired item
        cache_manager.set('config', 'value', 'key', ttl=1)
        time.sleep(1.1)
        
        # Wait for cleanup
        await asyncio.sleep(0.1)
        
        await cache_manager.stop_cleanup_task()


class TestResourceMonitor:
    """Test resource monitoring."""
    
    @pytest.fixture
    def resource_limits(self):
        return ResourceLimits(
            max_concurrent_checks=5,
            max_memory_usage_mb=100,
            max_cpu_usage_percent=80.0,
            max_queue_size=10,
            check_interval_seconds=1
        )
        
    @pytest.fixture
    def resource_monitor(self, resource_limits):
        return ResourceMonitor(resource_limits)
        
    def test_register_check(self, resource_monitor):
        """Test check registration."""
        # Should be able to register checks up to limit
        for i in range(resource_monitor.limits.max_concurrent_checks):
            assert resource_monitor.register_check(f'check_{i}')
            
        # Should fail when limit is reached
        assert not resource_monitor.register_check('check_overflow')
        
    def test_unregister_check(self, resource_monitor):
        """Test check unregistration."""
        resource_monitor.register_check('test_check')
        assert 'test_check' in resource_monitor._active_checks
        
        resource_monitor.unregister_check('test_check')
        assert 'test_check' not in resource_monitor._active_checks
        
    def test_queue_management(self, resource_monitor):
        """Test queue management."""
        # Fill up active checks
        for i in range(resource_monitor.limits.max_concurrent_checks):
            resource_monitor.register_check(f'check_{i}')
            
        # Add to queue
        assert resource_monitor.add_to_queue('queued_check', priority=1)
        
        # Get from queue
        next_check = resource_monitor.get_next_from_queue()
        assert next_check == 'queued_check'
        
    def test_resource_stats(self, resource_monitor):
        """Test resource statistics."""
        resource_monitor.register_check('test_check')
        resource_monitor.add_to_queue('queued_check')
        
        stats = resource_monitor.get_resource_stats()
        
        assert stats['active_checks'] == 1
        assert stats['queue_size'] == 1
        assert 'memory_usage_percent' in stats
        assert 'cpu_usage_percent' in stats
        
    @pytest.mark.asyncio
    async def test_monitoring_task(self, resource_monitor):
        """Test resource monitoring task."""
        await resource_monitor.start_monitoring()
        
        # Let it run briefly
        await asyncio.sleep(0.1)
        
        await resource_monitor.stop_monitoring()


class TestBatchScheduler:
    """Test batch scheduling."""
    
    @pytest.fixture
    def batch_scheduler(self):
        return BatchScheduler(max_batch_size=3, batch_timeout=2)
        
    @pytest.fixture
    def sample_server_config(self):
        return EnhancedServerConfig(
            server_name='test_server',
            mcp_endpoint_url='http://localhost:8080',
            rest_health_endpoint_url='http://localhost:8080/health'
        )
        
    @pytest.mark.asyncio
    async def test_add_request(self, batch_scheduler, sample_server_config):
        """Test adding requests to batch."""
        batch_id = await batch_scheduler.add_request(sample_server_config)
        
        assert batch_id is not None
        assert batch_id in batch_scheduler._pending_requests
        
    @pytest.mark.asyncio
    async def test_batch_size_limit(self, batch_scheduler, sample_server_config):
        """Test batch size limit."""
        batch_ids = []
        
        # Add requests up to batch size
        for i in range(batch_scheduler.max_batch_size):
            batch_id = await batch_scheduler.add_request(sample_server_config)
            batch_ids.append(batch_id)
            
        # All should be in same batch
        assert len(set(batch_ids)) == 1
        
        # Next request should create new batch
        new_batch_id = await batch_scheduler.add_request(sample_server_config)
        assert new_batch_id not in batch_ids
        
    @pytest.mark.asyncio
    async def test_batch_timeout(self, batch_scheduler, sample_server_config):
        """Test batch timeout."""
        await batch_scheduler.add_request(sample_server_config)
        
        # Wait for timeout
        await asyncio.sleep(batch_scheduler.batch_timeout + 0.1)
        
        ready_batches = await batch_scheduler.get_ready_batches()
        assert len(ready_batches) == 1
        
    @pytest.mark.asyncio
    async def test_scheduler_task(self, batch_scheduler, sample_server_config):
        """Test batch scheduler task."""
        await batch_scheduler.start_scheduler()
        
        await batch_scheduler.add_request(sample_server_config)
        
        # Let scheduler run
        await asyncio.sleep(0.1)
        
        await batch_scheduler.stop_scheduler()


class TestPerformanceOptimizer:
    """Test main performance optimizer."""
    
    @pytest.fixture
    def optimizer(self):
        return PerformanceOptimizer()
        
    @pytest.fixture
    def sample_server_configs(self):
        return [
            EnhancedServerConfig(
                server_name=f'server_{i}',
                mcp_endpoint_url=f'http://localhost:808{i}',
                rest_health_endpoint_url=f'http://localhost:808{i}/health'
            )
            for i in range(3)
        ]
        
    @pytest.mark.asyncio
    async def test_initialize_shutdown(self, optimizer):
        """Test optimizer initialization and shutdown."""
        await optimizer.initialize()
        
        assert optimizer.connection_manager.mcp_pool is not None
        assert optimizer.connection_manager.rest_pool is not None
        
        await optimizer.shutdown()
        
    @pytest.mark.asyncio
    async def test_concurrent_health_checks(self, optimizer, sample_server_configs):
        """Test concurrent health check execution."""
        await optimizer.initialize()
        
        # Mock health check function
        async def mock_health_check(config):
            await asyncio.sleep(0.1)  # Simulate work
            return DualHealthCheckResult(
                server_name=config.server_name,
                timestamp=datetime.now(),
                overall_status='HEALTHY',
                overall_success=True,
                mcp_result=None,
                mcp_success=True,
                mcp_response_time_ms=100.0,
                mcp_tools_count=5,
                mcp_error_message=None,
                rest_result=None,
                rest_success=True,
                rest_response_time_ms=80.0,
                rest_status_code=200,
                rest_error_message=None,
                combined_response_time_ms=90.0,
                health_score=1.0,
                available_paths=['mcp', 'rest']
            )
            
        start_time = time.time()
        results = await optimizer.execute_concurrent_health_checks(
            sample_server_configs, mock_health_check
        )
        end_time = time.time()
        
        # Should complete faster than sequential execution
        assert end_time - start_time < 0.5  # Should be much faster than 3 * 0.1
        assert len(results) == len(sample_server_configs)
        
        await optimizer.shutdown()
        
    def test_performance_metrics(self, optimizer):
        """Test performance metrics collection."""
        # Update metrics
        optimizer._update_metrics(100.0)
        
        metrics = optimizer.get_performance_metrics()
        
        assert isinstance(metrics, PerformanceMetrics)
        assert metrics.total_checks_performed > 0
        assert metrics.average_response_time_ms > 0
        
    def test_optimization_recommendations(self, optimizer):
        """Test optimization recommendations."""
        # Set some metrics that should trigger recommendations
        optimizer.metrics.average_response_time_ms = 6000  # High response time
        optimizer.metrics.cache_hit_rate = 0.3  # Low cache hit rate
        
        recommendations = optimizer.get_optimization_recommendations()
        
        assert len(recommendations) > 0
        assert any('response time' in rec.lower() for rec in recommendations)
        assert any('cache' in rec.lower() for rec in recommendations)


class TestPerformanceBenchmarker:
    """Test performance benchmarking."""
    
    @pytest.fixture
    def optimizer(self):
        return PerformanceOptimizer()
        
    @pytest.fixture
    def benchmarker(self, optimizer):
        return PerformanceBenchmarker(optimizer)
        
    @pytest.fixture
    def benchmark_config(self):
        return BenchmarkConfig(
            name='test_benchmark',
            description='Test benchmark configuration',
            duration_seconds=5,
            concurrent_users=[1, 2],
            server_counts=[1, 2],
            iterations=1
        )
        
    @pytest.fixture
    def sample_server_configs(self):
        return [
            EnhancedServerConfig(
                server_name=f'server_{i}',
                mcp_endpoint_url=f'http://localhost:808{i}',
                rest_health_endpoint_url=f'http://localhost:808{i}/health'
            )
            for i in range(2)
        ]
        
    @pytest.mark.asyncio
    async def test_run_single_benchmark(self, benchmarker, benchmark_config, sample_server_configs):
        """Test running a single benchmark."""
        await benchmarker.optimizer.initialize()
        
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
                    mcp_response_time_ms=50.0,
                    mcp_tools_count=5,
                    mcp_error_message=None,
                    rest_result=None,
                    rest_success=True,
                    rest_response_time_ms=40.0,
                    rest_status_code=200,
                    rest_error_message=None,
                    combined_response_time_ms=45.0,
                    health_score=1.0,
                    available_paths=['mcp', 'rest']
                )
                for config in configs
            ]
            
        result = await benchmarker._run_single_benchmark(
            benchmark_config, 1, sample_server_configs[:1], mock_health_check, 0
        )
        
        assert isinstance(result, BenchmarkResult)
        assert result.config_name == benchmark_config.name
        assert result.concurrent_users == 1
        assert result.server_count == 1
        assert result.total_requests > 0
        
        await benchmarker.optimizer.shutdown()
        
    @pytest.mark.asyncio
    async def test_load_test_scenario(self, benchmarker, sample_server_configs):
        """Test load test scenario execution."""
        await benchmarker.optimizer.initialize()
        
        scenario = LoadTestScenario(
            name='test_scenario',
            description='Test load scenario',
            concurrent_users=2,
            duration_seconds=3,
            server_configs=sample_server_configs[:1]
        )
        
        # Mock health check function
        async def mock_health_check(configs):
            await asyncio.sleep(0.01)
            return []
            
        result = await benchmarker.run_load_test(scenario, mock_health_check)
        
        assert isinstance(result, BenchmarkResult)
        assert result.config_name == scenario.name
        
        await benchmarker.optimizer.shutdown()
        
    def test_benchmark_result_serialization(self):
        """Test benchmark result serialization."""
        result = BenchmarkResult(
            config_name='test',
            timestamp=datetime.now(),
            concurrent_users=5,
            server_count=3,
            iteration=1,
            total_requests=100,
            successful_requests=95,
            failed_requests=5,
            requests_per_second=10.0,
            average_response_time_ms=100.0,
            median_response_time_ms=90.0,
            p95_response_time_ms=150.0,
            p99_response_time_ms=200.0,
            min_response_time_ms=50.0,
            max_response_time_ms=300.0,
            peak_memory_usage_mb=256.0,
            average_cpu_usage_percent=45.0,
            peak_cpu_usage_percent=80.0,
            connection_pool_utilization=0.7,
            cache_hit_rate=0.85,
            timeout_errors=2,
            connection_errors=1,
            authentication_errors=1,
            other_errors=1
        )
        
        result_dict = result.to_dict()
        
        assert result_dict['config_name'] == 'test'
        assert result_dict['concurrent_users'] == 5
        assert result_dict['total_requests'] == 100
        assert 'timestamp' in result_dict


class TestMetricsCollector:
    """Test metrics collection."""
    
    @pytest.fixture
    def metrics_collector(self):
        return MetricsCollector()
        
    @pytest.mark.asyncio
    async def test_metrics_collection(self, metrics_collector):
        """Test metrics collection process."""
        await metrics_collector.start()
        
        # Let it collect some metrics
        await asyncio.sleep(0.2)
        
        await metrics_collector.stop()
        
        # Should have collected some metrics
        assert len(metrics_collector.metrics_history) > 0
        
        # Check metric structure
        metric = metrics_collector.metrics_history[0]
        assert 'timestamp' in metric
        assert 'memory_mb' in metric
        assert 'cpu_percent' in metric
        
    @pytest.mark.asyncio
    async def test_final_metrics(self, metrics_collector):
        """Test final metrics aggregation."""
        # Add some mock metrics
        metrics_collector.metrics_history = [
            {
                'timestamp': datetime.now(),
                'memory_mb': 100.0,
                'cpu_percent': 50.0
            },
            {
                'timestamp': datetime.now(),
                'memory_mb': 150.0,
                'cpu_percent': 70.0
            }
        ]
        
        final_metrics = await metrics_collector.get_final_metrics()
        
        assert final_metrics['peak_memory_mb'] == 150.0
        assert final_metrics['avg_cpu_percent'] == 60.0
        assert final_metrics['peak_cpu_percent'] == 70.0


class TestIntegration:
    """Integration tests for performance optimization."""
    
    @pytest.mark.asyncio
    async def test_end_to_end_optimization(self):
        """Test end-to-end performance optimization."""
        # Create optimizer with custom configs
        connection_config = ConnectionPoolConfig(max_connections=5)
        resource_limits = ResourceLimits(max_concurrent_checks=3)
        cache_config = CacheConfig(max_cache_size=50)
        
        optimizer = PerformanceOptimizer(
            connection_config, resource_limits, cache_config
        )
        
        await optimizer.initialize()
        
        try:
            # Test caching
            optimizer.cache_manager.set('config', {'test': 'value'}, 'test_key')
            cached_value = optimizer.cache_manager.get('config', 'test_key')
            assert cached_value == {'test': 'value'}
            
            # Test resource monitoring
            assert optimizer.resource_monitor.can_start_check('test_check')
            assert optimizer.resource_monitor.register_check('test_check')
            
            # Test metrics
            optimizer._update_metrics(100.0)
            metrics = optimizer.get_performance_metrics()
            assert metrics.total_checks_performed > 0
            
            # Test recommendations
            recommendations = optimizer.get_optimization_recommendations()
            assert isinstance(recommendations, list)
            
        finally:
            await optimizer.shutdown()
            
    @pytest.mark.asyncio
    async def test_concurrent_execution_with_limits(self):
        """Test concurrent execution with resource limits."""
        resource_limits = ResourceLimits(max_concurrent_checks=2)
        optimizer = PerformanceOptimizer(resource_limits=resource_limits)
        
        await optimizer.initialize()
        
        try:
            server_configs = [
                EnhancedServerConfig(
                    server_name=f'server_{i}',
                    mcp_endpoint_url=f'http://localhost:808{i}',
                    rest_health_endpoint_url=f'http://localhost:808{i}/health'
                )
                for i in range(5)  # More servers than concurrent limit
            ]
            
            async def mock_health_check(config):
                await asyncio.sleep(0.1)
                return DualHealthCheckResult(
                    server_name=config.server_name,
                    timestamp=datetime.now(),
                    overall_status='HEALTHY',
                    overall_success=True,
                    mcp_result=None,
                    mcp_success=True,
                    mcp_response_time_ms=100.0,
                    mcp_tools_count=5,
                    mcp_error_message=None,
                    rest_result=None,
                    rest_success=True,
                    rest_response_time_ms=80.0,
                    rest_status_code=200,
                    rest_error_message=None,
                    combined_response_time_ms=90.0,
                    health_score=1.0,
                    available_paths=['mcp', 'rest']
                )
                
            results = await optimizer.execute_concurrent_health_checks(
                server_configs, mock_health_check, max_concurrent=2
            )
            
            # Should get results for all servers despite concurrency limit
            assert len(results) == len(server_configs)
            
        finally:
            await optimizer.shutdown()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])