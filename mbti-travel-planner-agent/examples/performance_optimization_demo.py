"""
Performance Optimization Demo

This script demonstrates the performance optimizations implemented in the
MBTI Travel Planner Agent, including response caching, connection pooling,
parallel execution, and optimized token refresh.

Usage:
    python examples/performance_optimization_demo.py
"""

import asyncio
import json
import logging
import time
from typing import Dict, Any, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import performance optimization services
from services.response_cache import ResponseCache, CacheConfig
from services.connection_pool_manager import ConnectionPoolManager, ConnectionConfig
from services.parallel_execution_service import ParallelExecutionService, ExecutionConfig, TaskDefinition
from services.optimized_token_refresh import OptimizedTokenRefreshService, RefreshConfig, RefreshStrategy
from services.agentcore_runtime_client import AgentCoreRuntimeClient
from services.authentication_manager import AuthenticationManager, CognitoConfig
from services.restaurant_search_tool import RestaurantSearchTool
from services.restaurant_reasoning_tool import RestaurantReasoningTool

# Configuration
COGNITO_CONFIG = CognitoConfig(
    user_pool_id="us-east-1_KePRX24Bn",
    client_id="1ofgeckef3po4i3us4j1m4chvd",
    client_secret="t69uogl8jl9qu9nvsrpifu0gpruj02l9q8rnoci36bipc8me4r9",
    region="us-east-1"
)

SEARCH_AGENT_ARN = "arn:aws:bedrock-agentcore:us-east-1:209803798463:runtime/restaurant_search_agent-mN8bgq2Y1j"
REASONING_AGENT_ARN = "arn:aws:bedrock-agentcore:us-east-1:209803798463:runtime/restaurant_search_result_reasoning_agent-MSns5D6SLE"


async def demo_response_caching():
    """Demonstrate response caching capabilities."""
    logger.info("=== Response Caching Demo ===")
    
    # Configure cache with custom settings
    cache_config = CacheConfig(
        default_ttl_seconds=300,  # 5 minutes
        max_cache_size=100,
        operation_ttl_overrides={
            "search_restaurants": 600,  # 10 minutes for search
            "get_recommendations": 300   # 5 minutes for recommendations
        }
    )
    
    async with ResponseCache(cache_config) as cache:
        # Simulate repeated queries
        test_params = {
            "districts": ["Central district"],
            "meal_types": ["lunch"]
        }
        
        # First call - cache miss
        start_time = time.time()
        
        async def mock_search():
            await asyncio.sleep(0.5)  # Simulate API call delay
            return {"restaurants": [{"name": "Test Restaurant", "district": "Central district"}]}
        
        result1 = await cache.get_or_compute(
            "search_restaurants",
            test_params,
            mock_search
        )
        
        first_call_time = time.time() - start_time
        logger.info(f"First call (cache miss): {first_call_time:.3f}s")
        
        # Second call - cache hit
        start_time = time.time()
        result2 = await cache.get_or_compute(
            "search_restaurants",
            test_params,
            mock_search
        )
        
        second_call_time = time.time() - start_time
        logger.info(f"Second call (cache hit): {second_call_time:.3f}s")
        
        # Verify results are identical
        assert result1 == result2
        logger.info(f"Cache speedup: {first_call_time / second_call_time:.1f}x faster")
        
        # Display cache statistics
        stats = cache.get_statistics()
        if stats:
            logger.info(f"Cache statistics: {json.dumps(stats, indent=2)}")


async def demo_connection_pooling():
    """Demonstrate connection pooling capabilities."""
    logger.info("=== Connection Pooling Demo ===")
    
    # Configure connection pool
    pool_config = ConnectionConfig(
        max_connections_per_pool=5,
        min_connections_per_pool=2,
        max_idle_time_seconds=300,
        health_check_interval_seconds=30
    )
    
    async with ConnectionPoolManager(pool_config) as pool_manager:
        # Simulate multiple concurrent requests
        async def make_request(request_id: int):
            async with pool_manager.get_client('bedrock-agent-runtime', 'us-east-1') as client:
                # Simulate using the client
                await asyncio.sleep(0.1)
                return f"Request {request_id} completed"
        
        # Execute multiple requests concurrently
        start_time = time.time()
        tasks = [make_request(i) for i in range(10)]
        results = await asyncio.gather(*tasks)
        
        execution_time = time.time() - start_time
        logger.info(f"10 concurrent requests completed in {execution_time:.3f}s")
        
        # Display pool statistics
        stats = pool_manager.get_pool_statistics()
        logger.info(f"Pool statistics: {json.dumps(stats, indent=2)}")


async def demo_parallel_execution():
    """Demonstrate parallel execution capabilities."""
    logger.info("=== Parallel Execution Demo ===")
    
    execution_config = ExecutionConfig(
        max_concurrent_tasks=5,
        default_timeout_seconds=30
    )
    
    service = ParallelExecutionService(execution_config)
    
    # Create mock tasks with different execution times
    async def mock_task(task_id: str, delay: float):
        await asyncio.sleep(delay)
        return f"Task {task_id} completed after {delay}s"
    
    tasks = [
        TaskDefinition(
            task_id=f"task_{i}",
            task_func=lambda i=i: mock_task(f"task_{i}", 0.1 * (i + 1))
        )
        for i in range(5)
    ]
    
    # Execute tasks in parallel
    start_time = time.time()
    result = await service.execute_parallel(tasks)
    execution_time = time.time() - start_time
    
    logger.info(f"Parallel execution completed in {execution_time:.3f}s")
    logger.info(f"Success rate: {result.success_rate:.1%}")
    logger.info(f"Successful tasks: {result.successful_tasks}/{result.total_tasks}")
    
    # Compare with sequential execution
    start_time = time.time()
    for task in tasks:
        await task.task_func()
    sequential_time = time.time() - start_time
    
    logger.info(f"Sequential execution would take: {sequential_time:.3f}s")
    logger.info(f"Parallel speedup: {sequential_time / execution_time:.1f}x faster")
    
    # Display execution statistics
    stats = service.get_execution_statistics()
    logger.info(f"Execution statistics: {json.dumps(stats, indent=2)}")


async def demo_optimized_token_refresh():
    """Demonstrate optimized token refresh capabilities."""
    logger.info("=== Optimized Token Refresh Demo ===")
    
    # Initialize authentication manager
    auth_manager = AuthenticationManager(COGNITO_CONFIG)
    
    # Configure optimized token refresh
    refresh_config = RefreshConfig(
        strategy=RefreshStrategy.PROACTIVE,
        proactive_refresh_threshold_seconds=300,  # 5 minutes
        background_refresh_enabled=True,
        enable_usage_prediction=True
    )
    
    async with OptimizedTokenRefreshService(auth_manager, refresh_config) as token_service:
        # Simulate token usage patterns
        logger.info("Simulating token usage patterns...")
        
        for i in range(5):
            start_time = time.time()
            token = await token_service.get_valid_token()
            token_time = time.time() - start_time
            
            logger.info(f"Token request {i+1}: {token_time:.3f}s")
            
            # Simulate some delay between requests
            await asyncio.sleep(0.1)
        
        # Display token refresh statistics
        stats = token_service.get_refresh_statistics()
        logger.info(f"Token refresh statistics: {json.dumps(stats, indent=2)}")
        
        # Display token health info
        health_info = token_service.get_token_health_info()
        logger.info(f"Token health: {json.dumps(health_info, indent=2)}")


async def demo_integrated_performance():
    """Demonstrate integrated performance optimizations in real workflow."""
    logger.info("=== Integrated Performance Demo ===")
    
    # Initialize authentication manager
    auth_manager = AuthenticationManager(COGNITO_CONFIG)
    
    # Configure optimized token refresh
    refresh_config = RefreshConfig(
        strategy=RefreshStrategy.PROACTIVE,
        background_refresh_enabled=True
    )
    
    token_service = OptimizedTokenRefreshService(auth_manager, refresh_config)
    
    # Initialize AgentCore client with all optimizations enabled
    runtime_client = AgentCoreRuntimeClient(
        region="us-east-1",
        enable_caching=True,
        enable_connection_pooling=True,
        enable_parallel_execution=True
    )
    
    # Initialize tools
    search_tool = RestaurantSearchTool(runtime_client, SEARCH_AGENT_ARN, auth_manager)
    reasoning_tool = RestaurantReasoningTool(runtime_client, REASONING_AGENT_ARN, auth_manager)
    
    try:
        # Test 1: Single search with caching
        logger.info("Test 1: Restaurant search with caching")
        
        start_time = time.time()
        search_result1 = await search_tool.search_restaurants_by_district(
            districts=["Central district"],
            enable_caching=True
        )
        first_search_time = time.time() - start_time
        
        # Repeat same search (should hit cache)
        start_time = time.time()
        search_result2 = await search_tool.search_restaurants_by_district(
            districts=["Central district"],
            enable_caching=True
        )
        second_search_time = time.time() - start_time
        
        logger.info(f"First search: {first_search_time:.3f}s")
        logger.info(f"Second search (cached): {second_search_time:.3f}s")
        logger.info(f"Cache speedup: {first_search_time / second_search_time:.1f}x")
        
        # Test 2: Parallel agent calls
        logger.info("Test 2: Parallel agent execution")
        
        agent_calls = [
            {
                "call_id": "search_central",
                "agent_arn": SEARCH_AGENT_ARN,
                "input_text": json.dumps({
                    "action": "search_restaurants_by_district",
                    "parameters": {"districts": ["Central district"]}
                })
            },
            {
                "call_id": "search_admiralty",
                "agent_arn": SEARCH_AGENT_ARN,
                "input_text": json.dumps({
                    "action": "search_restaurants_by_district",
                    "parameters": {"districts": ["Admiralty"]}
                })
            }
        ]
        
        start_time = time.time()
        parallel_results = await runtime_client.invoke_agents_parallel(agent_calls)
        parallel_time = time.time() - start_time
        
        logger.info(f"Parallel execution: {parallel_time:.3f}s")
        logger.info(f"Parallel results: {len(parallel_results)} successful calls")
        
        # Display comprehensive performance metrics
        metrics = runtime_client.get_performance_metrics()
        logger.info("=== Performance Metrics ===")
        logger.info(json.dumps(metrics, indent=2, default=str))
        
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        
    finally:
        # Cleanup
        await runtime_client.close()
        await token_service.close()


async def main():
    """Run all performance optimization demos."""
    logger.info("Starting Performance Optimization Demos")
    
    try:
        await demo_response_caching()
        await asyncio.sleep(1)
        
        await demo_connection_pooling()
        await asyncio.sleep(1)
        
        await demo_parallel_execution()
        await asyncio.sleep(1)
        
        await demo_optimized_token_refresh()
        await asyncio.sleep(1)
        
        await demo_integrated_performance()
        
    except Exception as e:
        logger.error(f"Demo suite failed: {e}")
        raise
    
    logger.info("All performance optimization demos completed successfully!")


if __name__ == "__main__":
    asyncio.run(main())