"""
Enhanced Health Check Service Example

This example demonstrates how to use the Enhanced Health Check Service orchestrator
for dual health monitoring with concurrent execution and resource management.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import List

from models.dual_health_models import (
    EnhancedServerConfig,
    AggregationConfig,
    PriorityConfig,
    ServerStatus
)
from services.enhanced_health_check_service import (
    EnhancedHealthCheckService,
    ConnectionPoolManager,
    create_enhanced_health_check_service
)


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_sample_server_configs() -> List[EnhancedServerConfig]:
    """Create sample server configurations for demonstration."""
    return [
        EnhancedServerConfig(
            server_name="restaurant-search-mcp",
            mcp_endpoint_url="http://localhost:8080/mcp",
            mcp_enabled=True,
            mcp_timeout_seconds=10,
            mcp_expected_tools=[
                "search_restaurants_by_district",
                "search_restaurants_by_meal_type",
                "search_restaurants_combined"
            ],
            rest_health_endpoint_url="http://localhost:8080/status/health",
            rest_enabled=True,
            rest_timeout_seconds=8,
            jwt_token="eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
            auth_headers={"X-API-Key": "restaurant-search-key"},
            mcp_priority_weight=0.7,
            rest_priority_weight=0.3
        ),
        EnhancedServerConfig(
            server_name="restaurant-reasoning-mcp",
            mcp_endpoint_url="http://localhost:8081/mcp",
            mcp_enabled=True,
            mcp_timeout_seconds=12,
            mcp_expected_tools=[
                "recommend_restaurants",
                "analyze_restaurant_sentiment"
            ],
            rest_health_endpoint_url="http://localhost:8081/status/health",
            rest_enabled=True,
            rest_timeout_seconds=6,
            jwt_token="eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
            auth_headers={"X-API-Key": "restaurant-reasoning-key"},
            mcp_priority_weight=0.6,
            rest_priority_weight=0.4
        ),
        EnhancedServerConfig(
            server_name="mbti-travel-assistant-mcp",
            mcp_endpoint_url="http://localhost:8082/mcp",
            mcp_enabled=True,
            mcp_timeout_seconds=15,
            mcp_expected_tools=[
                "get_mbti_personality_analysis",
                "generate_travel_itinerary",
                "search_tourist_spots"
            ],
            rest_health_endpoint_url="http://localhost:8082/status/health",
            rest_enabled=True,
            rest_timeout_seconds=10,
            jwt_token="eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
            auth_headers={"X-API-Key": "mbti-travel-key"},
            mcp_priority_weight=0.5,
            rest_priority_weight=0.5
        )
    ]


def create_custom_aggregation_config() -> AggregationConfig:
    """Create custom aggregation configuration."""
    priority_config = PriorityConfig(
        mcp_priority_weight=0.6,
        rest_priority_weight=0.4,
        require_both_success_for_healthy=False,
        degraded_on_single_failure=True
    )
    
    return AggregationConfig(
        priority_config=priority_config,
        health_score_calculation="weighted_average",
        failure_threshold=0.4,
        degraded_threshold=0.7
    )


async def example_single_server_dual_check():
    """Example: Single server dual health check."""
    print("\n=== Single Server Dual Health Check Example ===")
    
    # Create server configuration
    config = EnhancedServerConfig(
        server_name="example-server",
        mcp_endpoint_url="http://localhost:8080/mcp",
        rest_health_endpoint_url="http://localhost:8080/status/health",
        mcp_expected_tools=["search_restaurants", "recommend_restaurants"],
        jwt_token="example-jwt-token"
    )
    
    # Create service with custom configuration
    aggregation_config = create_custom_aggregation_config()
    
    async with create_enhanced_health_check_service(
        aggregation_config=aggregation_config,
        max_concurrent_servers=5,
        max_concurrent_per_server=2
    ) as service:
        try:
            # Perform dual health check
            result = await service.perform_dual_health_check(config)
            
            # Display results
            print(f"Server: {result.server_name}")
            print(f"Overall Status: {result.overall_status.value}")
            print(f"Overall Success: {result.overall_success}")
            print(f"Health Score: {result.health_score:.3f}")
            print(f"Available Paths: {result.available_paths}")
            
            if result.mcp_result:
                print(f"MCP Success: {result.mcp_success}")
                print(f"MCP Response Time: {result.mcp_response_time_ms:.2f}ms")
                print(f"MCP Tools Count: {result.mcp_tools_count}")
                if result.mcp_error_message:
                    print(f"MCP Error: {result.mcp_error_message}")
            
            if result.rest_result:
                print(f"REST Success: {result.rest_success}")
                print(f"REST Response Time: {result.rest_response_time_ms:.2f}ms")
                print(f"REST Status Code: {result.rest_status_code}")
                if result.rest_error_message:
                    print(f"REST Error: {result.rest_error_message}")
            
            print(f"Combined Response Time: {result.combined_response_time_ms:.2f}ms")
            
        except Exception as e:
            print(f"Error performing health check: {e}")


async def example_multiple_servers_batch_check():
    """Example: Multiple servers batch health check."""
    print("\n=== Multiple Servers Batch Health Check Example ===")
    
    # Create server configurations
    server_configs = create_sample_server_configs()
    
    # Create service with high concurrency
    async with create_enhanced_health_check_service(
        max_concurrent_servers=10,
        max_concurrent_per_server=3,
        mcp_pool_size=15,
        rest_pool_size=20
    ) as service:
        try:
            # Perform batch health checks
            start_time = datetime.now()
            results = await service.check_multiple_servers_dual(
                server_configs,
                timeout_per_server=30
            )
            end_time = datetime.now()
            
            # Display summary
            total_time = (end_time - start_time).total_seconds() * 1000
            print(f"Batch check completed in {total_time:.2f}ms")
            print(f"Checked {len(results)} servers")
            
            # Count results by status
            status_counts = {}
            for result in results:
                status = result.overall_status.value
                status_counts[status] = status_counts.get(status, 0) + 1
            
            print(f"Status distribution: {status_counts}")
            
            # Display individual results
            for result in results:
                print(f"\n{result.server_name}:")
                print(f"  Status: {result.overall_status.value}")
                print(f"  Score: {result.health_score:.3f}")
                print(f"  MCP: {'✓' if result.mcp_success else '✗'} "
                      f"({result.mcp_response_time_ms:.1f}ms)")
                print(f"  REST: {'✓' if result.rest_success else '✗'} "
                      f"({result.rest_response_time_ms:.1f}ms)")
                print(f"  Paths: {', '.join(result.available_paths)}")
                
                if result.mcp_error_message:
                    print(f"  MCP Error: {result.mcp_error_message}")
                if result.rest_error_message:
                    print(f"  REST Error: {result.rest_error_message}")
            
        except Exception as e:
            print(f"Error performing batch health checks: {e}")


async def example_circuit_breaker_integration():
    """Example: Health check with circuit breaker integration."""
    print("\n=== Circuit Breaker Integration Example ===")
    
    config = create_sample_server_configs()[0]
    
    async with create_enhanced_health_check_service() as service:
        # Test different circuit breaker states
        circuit_breaker_states = ["CLOSED", "MCP_ONLY", "REST_ONLY", "OPEN"]
        
        for state in circuit_breaker_states:
            try:
                print(f"\nTesting circuit breaker state: {state}")
                
                result = await service.perform_health_check_with_circuit_breaker(
                    config, circuit_breaker_state=state
                )
                
                print(f"  Result: {result.overall_status.value}")
                print(f"  MCP Enabled: {result.mcp_success}")
                print(f"  REST Enabled: {result.rest_success}")
                print(f"  Available Paths: {result.available_paths}")
                
            except Exception as e:
                print(f"  Error: {e}")


async def example_retry_with_backoff():
    """Example: Health check with retry and backoff."""
    print("\n=== Retry with Backoff Example ===")
    
    config = create_sample_server_configs()[0]
    
    async with create_enhanced_health_check_service() as service:
        try:
            print("Performing health check with retry backoff...")
            
            start_time = datetime.now()
            result = await service.health_check_with_retry_backoff(
                config,
                max_retries=3,
                backoff_factor=1.5
            )
            end_time = datetime.now()
            
            total_time = (end_time - start_time).total_seconds() * 1000
            
            print(f"Completed in {total_time:.2f}ms")
            print(f"Final Status: {result.overall_status.value}")
            print(f"Success: {result.overall_success}")
            print(f"Health Score: {result.health_score:.3f}")
            
        except Exception as e:
            print(f"Error: {e}")


async def example_connection_pool_monitoring():
    """Example: Connection pool monitoring."""
    print("\n=== Connection Pool Monitoring Example ===")
    
    async with create_enhanced_health_check_service(
        mcp_pool_size=8,
        rest_pool_size=12
    ) as service:
        # Get initial stats
        stats = await service.get_connection_pool_stats()
        print("Initial connection pool stats:")
        print(json.dumps(stats, indent=2))
        
        # Perform some health checks to activate pools
        config = create_sample_server_configs()[0]
        
        try:
            await service.perform_dual_health_check(config)
        except Exception:
            pass  # Ignore errors for this example
        
        # Get updated stats
        stats = await service.get_connection_pool_stats()
        print("\nConnection pool stats after health check:")
        print(json.dumps(stats, indent=2))
        
        # Show active checks
        active_checks = service.get_active_checks()
        print(f"\nActive checks: {len(active_checks)}")
        for task_name, status in active_checks.items():
            print(f"  {task_name}: {status}")


async def example_cancellation_and_cleanup():
    """Example: Task cancellation and cleanup."""
    print("\n=== Task Cancellation and Cleanup Example ===")
    
    configs = create_sample_server_configs()
    
    async with create_enhanced_health_check_service() as service:
        # Start multiple health checks without awaiting
        print("Starting multiple health checks...")
        
        tasks = []
        for config in configs:
            task = asyncio.create_task(
                service.perform_dual_health_check(config)
            )
            tasks.append(task)
        
        # Give them time to start
        await asyncio.sleep(0.1)
        
        # Check active tasks
        active_checks = service.get_active_checks()
        print(f"Active checks: {len(active_checks)}")
        
        # Cancel specific server checks
        print("Cancelling checks for first server...")
        await service.cancel_server_checks(configs[0].server_name)
        
        # Check remaining active tasks
        active_checks = service.get_active_checks()
        print(f"Remaining active checks: {len(active_checks)}")
        
        # Cancel all remaining checks
        print("Cancelling all remaining checks...")
        await service.cancel_all_checks()
        
        # Verify cleanup
        active_checks = service.get_active_checks()
        print(f"Final active checks: {len(active_checks)}")
        
        # Wait for tasks to complete (they should be cancelled)
        results = await asyncio.gather(*tasks, return_exceptions=True)
        cancelled_count = sum(1 for r in results if isinstance(r, asyncio.CancelledError))
        print(f"Cancelled tasks: {cancelled_count}/{len(tasks)}")


async def example_custom_aggregation_rules():
    """Example: Custom aggregation rules."""
    print("\n=== Custom Aggregation Rules Example ===")
    
    # Create different aggregation configurations
    configs = [
        # Conservative: require both to succeed
        AggregationConfig(
            priority_config=PriorityConfig(
                mcp_priority_weight=0.5,
                rest_priority_weight=0.5,
                require_both_success_for_healthy=True,
                degraded_on_single_failure=True
            ),
            health_score_calculation="minimum",
            failure_threshold=0.3,
            degraded_threshold=0.8
        ),
        # Permissive: MCP-focused
        AggregationConfig(
            priority_config=PriorityConfig(
                mcp_priority_weight=0.8,
                rest_priority_weight=0.2,
                require_both_success_for_healthy=False,
                degraded_on_single_failure=False
            ),
            health_score_calculation="weighted_average",
            failure_threshold=0.6,
            degraded_threshold=0.7
        ),
        # Balanced: equal weighting
        AggregationConfig(
            priority_config=PriorityConfig(
                mcp_priority_weight=0.5,
                rest_priority_weight=0.5,
                require_both_success_for_healthy=False,
                degraded_on_single_failure=True
            ),
            health_score_calculation="maximum",
            failure_threshold=0.4,
            degraded_threshold=0.6
        )
    ]
    
    server_config = create_sample_server_configs()[0]
    
    for i, agg_config in enumerate(configs):
        print(f"\nTesting aggregation config {i+1}:")
        print(f"  MCP weight: {agg_config.priority_config.mcp_priority_weight}")
        print(f"  REST weight: {agg_config.priority_config.rest_priority_weight}")
        print(f"  Require both: {agg_config.priority_config.require_both_success_for_healthy}")
        print(f"  Calculation: {agg_config.health_score_calculation}")
        
        async with create_enhanced_health_check_service(
            aggregation_config=agg_config
        ) as service:
            try:
                result = await service.perform_dual_health_check(server_config)
                print(f"  Result: {result.overall_status.value}")
                print(f"  Score: {result.health_score:.3f}")
            except Exception as e:
                print(f"  Error: {e}")


async def main():
    """Run all examples."""
    print("Enhanced Health Check Service Examples")
    print("=" * 50)
    
    examples = [
        example_single_server_dual_check,
        example_multiple_servers_batch_check,
        example_circuit_breaker_integration,
        example_retry_with_backoff,
        example_connection_pool_monitoring,
        example_cancellation_and_cleanup,
        example_custom_aggregation_rules
    ]
    
    for example_func in examples:
        try:
            await example_func()
        except Exception as e:
            print(f"Example {example_func.__name__} failed: {e}")
        
        print("\n" + "-" * 50)
    
    print("\nAll examples completed!")


if __name__ == "__main__":
    asyncio.run(main())