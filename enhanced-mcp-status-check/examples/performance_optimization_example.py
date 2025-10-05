"""
Example demonstrating performance optimization features.

This example shows how to use the performance optimization components
for enhanced MCP status checks including:
- Concurrent execution
- Connection pooling
- Caching
- Resource monitoring
- Performance benchmarking

Requirements: 10.1, 10.2, 10.3, 10.4, 10.5
"""

import asyncio
import logging
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
    EnhancedServerConfig,
    DualHealthCheckResult
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def create_sample_server_configs() -> List[EnhancedServerConfig]:
    """Create sample server configurations for testing."""
    return [
        EnhancedServerConfig(
            server_name='restaurant-search-mcp',
            mcp_endpoint_url='http://localhost:8080',
            rest_health_endpoint_url='http://localhost:8080/status/health',
            mcp_timeout_seconds=10,
            rest_timeout_seconds=8,
            mcp_expected_tools=[
                'search_restaurants_by_district',
                'search_restaurants_by_meal_type',
                'search_restaurants_combined'
            ]
        ),
        EnhancedServerConfig(
            server_name='restaurant-reasoning-mcp',
            mcp_endpoint_url='http://localhost:8081',
            rest_health_endpoint_url='http://localhost:8081/status/health',
            mcp_timeout_seconds=10,
            rest_timeout_seconds=8,
            mcp_expected_tools=[
                'recommend_restaurants',
                'analyze_restaurant_sentiment'
            ]
        ),
        EnhancedServerConfig(
            server_name='mbti-travel-assistant',
            mcp_endpoint_url='http://localhost:8082',
            rest_health_endpoint_url='http://localhost:8082/status/health',
            mcp_timeout_seconds=15,
            rest_timeout_seconds=10,
            mcp_expected_tools=[
                'get_mbti_recommendations',
                'analyze_personality_preferences'
            ]
        )
    ]


async def demonstrate_performance_optimizer():
    """Demonstrate performance optimization features."""
    logger.info("=== Performance Optimization Demo ===")
    
    # Configure performance optimization
    connection_config = ConnectionPoolConfig(
        max_connections=50,
        max_connections_per_host=20,
        keepalive_timeout=30,
        connection_timeout=10,
        read_timeout=30
    )
    
    resource_limits = ResourceLimits(
        max_concurrent_checks=20,
        max_memory_usage_mb=512,
        max_cpu_usage_percent=80.0,
        max_queue_size=100
    )
    
    cache_config = CacheConfig(
        config_cache_ttl=300,
        auth_token_cache_ttl=3600,
        dns_cache_ttl=600,
        result_cache_ttl=60,
        max_cache_size=1000
    )
    
    # Create performance optimizer
    optimizer = PerformanceOptimizer(
        connection_config=connection_config,
        resource_limits=resource_limits,
        cache_config=cache_config
    )
    
    # Initialize optimizer
    await optimizer.initialize()
    logger.info("Performance optimizer initialized")
    
    try:
        # Create sample server configurations
        server_configs = await create_sample_server_configs()
        
        # Create health check service
        health_service = EnhancedHealthCheckService()
        
        # Demonstrate caching
        await demonstrate_caching(optimizer, server_configs)
        
        # Demonstrate concurrent execution
        await demonstrate_concurrent_execution(optimizer, health_service, server_configs)
        
        # Demonstrate resource monitoring
        await demonstrate_resource_monitoring(optimizer)
        
        # Demonstrate batch scheduling
        await demonstrate_batch_scheduling(optimizer, server_configs)
        
        # Show performance metrics
        await show_performance_metrics(optimizer)
        
        # Show optimization recommendations
        show_optimization_recommendations(optimizer)
        
    finally:
        await optimizer.shutdown()
        logger.info("Performance optimizer shutdown")


async def demonstrate_caching(optimizer: PerformanceOptimizer, server_configs: List[EnhancedServerConfig]):
    """Demonstrate caching functionality."""
    logger.info("\n--- Caching Demo ---")
    
    cache_manager = optimizer.cache_manager
    
    # Cache configuration data
    config_data = {
        'servers': [config.server_name for config in server_configs],
        'timeout_settings': {
            'mcp': 10,
            'rest': 8
        }
    }
    
    cache_manager.set('config', config_data, 'server_config')
    logger.info("Cached server configuration")
    
    # Cache authentication tokens
    auth_tokens = {
        'restaurant-search-mcp': 'token_123',
        'restaurant-reasoning-mcp': 'token_456',
        'mbti-travel-assistant': 'token_789'
    }
    
    for server_name, token in auth_tokens.items():
        cache_manager.set('auth_tokens', token, server_name)
    
    logger.info("Cached authentication tokens")
    
    # Cache DNS resolutions
    dns_cache = {
        'localhost': '127.0.0.1',
        'api.example.com': '192.168.1.100'
    }
    
    for hostname, ip in dns_cache.items():
        cache_manager.set('dns', ip, hostname)
        
    logger.info("Cached DNS resolutions")
    
    # Demonstrate cache retrieval
    cached_config = cache_manager.get('config', 'server_config')
    logger.info(f"Retrieved cached config: {cached_config}")
    
    cached_token = cache_manager.get('auth_tokens', 'restaurant-search-mcp')
    logger.info(f"Retrieved cached token: {cached_token}")
    
    # Show cache statistics
    cache_stats = cache_manager.get_stats()
    logger.info(f"Cache statistics: {cache_stats}")


async def demonstrate_concurrent_execution(
    optimizer: PerformanceOptimizer,
    health_service: EnhancedHealthCheckService,
    server_configs: List[EnhancedServerConfig]
):
    """Demonstrate concurrent health check execution."""
    logger.info("\n--- Concurrent Execution Demo ---")
    
    # Mock health check function for demonstration
    async def mock_health_check(config: EnhancedServerConfig) -> DualHealthCheckResult:
        """Mock health check that simulates real work."""
        # Simulate network delay
        await asyncio.sleep(0.5)
        
        return DualHealthCheckResult(
            server_name=config.server_name,
            timestamp=datetime.now(),
            overall_status='HEALTHY',
            overall_success=True,
            mcp_result=None,
            mcp_success=True,
            mcp_response_time_ms=250.0,
            mcp_tools_count=len(config.mcp_expected_tools or []),
            mcp_error_message=None,
            rest_result=None,
            rest_success=True,
            rest_response_time_ms=200.0,
            rest_status_code=200,
            rest_error_message=None,
            combined_response_time_ms=225.0,
            health_score=1.0,
            available_paths=['mcp', 'rest']
        )
    
    # Execute health checks sequentially (for comparison)
    start_time = asyncio.get_event_loop().time()
    sequential_results = []
    for config in server_configs:
        result = await mock_health_check(config)
        sequential_results.append(result)
    sequential_time = asyncio.get_event_loop().time() - start_time
    
    logger.info(f"Sequential execution time: {sequential_time:.2f} seconds")
    
    # Execute health checks concurrently
    start_time = asyncio.get_event_loop().time()
    concurrent_results = await optimizer.execute_concurrent_health_checks(
        server_configs, mock_health_check, max_concurrent=10
    )
    concurrent_time = asyncio.get_event_loop().time() - start_time
    
    logger.info(f"Concurrent execution time: {concurrent_time:.2f} seconds")
    logger.info(f"Performance improvement: {(sequential_time / concurrent_time):.2f}x faster")
    
    # Verify results
    assert len(concurrent_results) == len(server_configs)
    logger.info(f"Successfully processed {len(concurrent_results)} health checks concurrently")


async def demonstrate_resource_monitoring(optimizer: PerformanceOptimizer):
    """Demonstrate resource monitoring."""
    logger.info("\n--- Resource Monitoring Demo ---")
    
    resource_monitor = optimizer.resource_monitor
    
    # Start monitoring
    await resource_monitor.start_monitoring()
    
    # Simulate registering multiple checks
    check_ids = []
    for i in range(5):
        check_id = f'demo_check_{i}'
        if resource_monitor.register_check(check_id):
            check_ids.append(check_id)
            logger.info(f"Registered check: {check_id}")
        else:
            logger.warning(f"Failed to register check: {check_id} (resource limits)")
    
    # Show resource statistics
    stats = resource_monitor.get_resource_stats()
    logger.info(f"Resource stats: {stats}")
    
    # Simulate queue usage
    for i in range(3):
        queue_check_id = f'queued_check_{i}'
        if resource_monitor.add_to_queue(queue_check_id, priority=i):
            logger.info(f"Added to queue: {queue_check_id} (priority: {i})")
    
    # Process queue
    while True:
        next_check = resource_monitor.get_next_from_queue()
        if next_check is None:
            break
        logger.info(f"Processing from queue: {next_check}")
    
    # Cleanup registered checks
    for check_id in check_ids:
        resource_monitor.unregister_check(check_id)
        logger.info(f"Unregistered check: {check_id}")
    
    await resource_monitor.stop_monitoring()


async def demonstrate_batch_scheduling(
    optimizer: PerformanceOptimizer,
    server_configs: List[EnhancedServerConfig]
):
    """Demonstrate batch scheduling."""
    logger.info("\n--- Batch Scheduling Demo ---")
    
    batch_scheduler = optimizer.batch_scheduler
    
    # Start scheduler
    await batch_scheduler.start_scheduler()
    
    # Add requests to batches
    batch_ids = []
    for i, config in enumerate(server_configs):
        batch_id = await batch_scheduler.add_request(config, priority=i % 3)
        batch_ids.append(batch_id)
        logger.info(f"Added {config.server_name} to batch {batch_id} (priority: {i % 3})")
    
    # Wait for batches to be ready
    await asyncio.sleep(batch_scheduler.batch_timeout + 0.5)
    
    # Get ready batches
    ready_batches = await batch_scheduler.get_ready_batches()
    logger.info(f"Ready batches: {len(ready_batches)}")
    
    for batch in ready_batches:
        logger.info(
            f"Batch {batch.batch_id}: {len(batch.server_configs)} servers, "
            f"priority: {batch.priority}"
        )
    
    await batch_scheduler.stop_scheduler()


async def show_performance_metrics(optimizer: PerformanceOptimizer):
    """Show current performance metrics."""
    logger.info("\n--- Performance Metrics ---")
    
    metrics = optimizer.get_performance_metrics()
    
    logger.info(f"Total checks performed: {metrics.total_checks_performed}")
    logger.info(f"Active concurrent checks: {metrics.concurrent_checks_active}")
    logger.info(f"Average response time: {metrics.average_response_time_ms:.2f} ms")
    logger.info(f"Cache hit rate: {metrics.cache_hit_rate:.2%}")
    logger.info(f"Memory usage: {metrics.memory_usage_mb:.2f} MB")
    logger.info(f"CPU usage: {metrics.cpu_usage_percent:.2f}%")
    logger.info(f"Connection pool utilization: {metrics.connection_pool_utilization:.2%}")
    logger.info(f"Queue size: {metrics.queue_size}")
    logger.info(f"Last updated: {metrics.last_updated}")


def show_optimization_recommendations(optimizer: PerformanceOptimizer):
    """Show optimization recommendations."""
    logger.info("\n--- Optimization Recommendations ---")
    
    recommendations = optimizer.get_optimization_recommendations()
    
    if recommendations:
        for i, recommendation in enumerate(recommendations, 1):
            logger.info(f"{i}. {recommendation}")
    else:
        logger.info("No optimization recommendations at this time")


async def demonstrate_performance_benchmarking():
    """Demonstrate performance benchmarking."""
    logger.info("\n=== Performance Benchmarking Demo ===")
    
    # Create optimizer for benchmarking
    optimizer = PerformanceOptimizer()
    await optimizer.initialize()
    
    try:
        # Create benchmarker
        benchmarker = PerformanceBenchmarker(optimizer)
        
        # Create server configurations
        server_configs = await create_sample_server_configs()
        
        # Define benchmark configuration
        benchmark_config = BenchmarkConfig(
            name='demo_benchmark',
            description='Demonstration benchmark for performance optimization',
            duration_seconds=10,
            concurrent_users=[1, 2, 5],
            server_counts=[1, 2, 3],
            iterations=2,
            warmup_duration=2,
            cooldown_duration=1
        )
        
        # Mock health check function
        async def mock_health_check(configs):
            await asyncio.sleep(0.1)  # Simulate work
            return [
                DualHealthCheckResult(
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
                for config in configs
            ]
        
        # Run benchmark
        logger.info("Starting performance benchmark...")
        results = await benchmarker.run_benchmark(
            benchmark_config, mock_health_check, server_configs
        )
        
        # Display results
        logger.info(f"Benchmark completed with {len(results)} results")
        
        for result in results[:3]:  # Show first 3 results
            logger.info(
                f"Config: {result.config_name}, "
                f"Users: {result.concurrent_users}, "
                f"Servers: {result.server_count}, "
                f"RPS: {result.requests_per_second:.2f}, "
                f"Avg RT: {result.average_response_time_ms:.2f}ms, "
                f"Success Rate: {(result.successful_requests/result.total_requests*100):.1f}%"
            )
        
        # Generate performance report
        report_file = benchmarker.generate_performance_report(results)
        logger.info(f"Performance report generated: {report_file}")
        
        # Demonstrate load test scenario
        await demonstrate_load_test_scenario(benchmarker, server_configs)
        
    finally:
        await optimizer.shutdown()


async def demonstrate_load_test_scenario(
    benchmarker: PerformanceBenchmarker,
    server_configs: List[EnhancedServerConfig]
):
    """Demonstrate load test scenario."""
    logger.info("\n--- Load Test Scenario Demo ---")
    
    # Define load test scenario
    scenario = LoadTestScenario(
        name='peak_load_test',
        description='Simulate peak load conditions',
        concurrent_users=10,
        duration_seconds=15,
        ramp_up_seconds=5,
        ramp_down_seconds=3,
        think_time_ms=500,
        server_configs=server_configs
    )
    
    # Mock health check function
    async def mock_health_check(configs):
        await asyncio.sleep(0.05)  # Quick simulation
        return []
    
    # Run load test
    logger.info(f"Starting load test: {scenario.name}")
    result = await benchmarker.run_load_test(scenario, mock_health_check)
    
    logger.info(f"Load test completed:")
    logger.info(f"  Total requests: {result.total_requests}")
    logger.info(f"  Successful requests: {result.successful_requests}")
    logger.info(f"  Failed requests: {result.failed_requests}")
    logger.info(f"  Requests per second: {result.requests_per_second:.2f}")
    logger.info(f"  Average response time: {result.average_response_time_ms:.2f}ms")


async def main():
    """Main demonstration function."""
    logger.info("Starting Enhanced MCP Status Check Performance Optimization Demo")
    
    try:
        # Demonstrate performance optimization
        await demonstrate_performance_optimizer()
        
        # Demonstrate performance benchmarking
        await demonstrate_performance_benchmarking()
        
        logger.info("\nDemo completed successfully!")
        
    except Exception as e:
        logger.error(f"Demo failed with error: {e}")
        raise


if __name__ == '__main__':
    asyncio.run(main())