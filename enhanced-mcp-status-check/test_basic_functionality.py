#!/usr/bin/env python3
"""
Basic functionality test for performance optimization features.
"""

import asyncio
import sys
import os

# Add the parent directory to the path for imports
sys.path.append(os.path.dirname(__file__))

from services.performance_optimizer import (
    CacheManager,
    CacheConfig,
    ResourceMonitor,
    ResourceLimits,
    ConnectionPoolManager,
    ConnectionPoolConfig,
    BatchScheduler
)


def test_cache_manager():
    """Test basic cache manager functionality."""
    print("Testing CacheManager...")
    
    config = CacheConfig(max_cache_size=10)
    cache_manager = CacheManager(config)
    
    # Test set and get
    cache_manager.set('test', 'hello world', 'greeting')
    result = cache_manager.get('test', 'greeting')
    
    assert result == 'hello world', f"Expected 'hello world', got {result}"
    print("✓ Cache set/get works")
    
    # Test cache miss
    result = cache_manager.get('test', 'nonexistent')
    assert result is None, f"Expected None, got {result}"
    print("✓ Cache miss works")
    
    # Test cache stats
    stats = cache_manager.get_stats()
    assert 'test' in stats, "Expected 'test' category in stats"
    print("✓ Cache stats work")
    
    print("CacheManager tests passed!\n")


def test_resource_monitor():
    """Test basic resource monitor functionality."""
    print("Testing ResourceMonitor...")
    
    limits = ResourceLimits(max_concurrent_checks=3, max_queue_size=5)
    monitor = ResourceMonitor(limits)
    
    # Test check registration
    success = monitor.register_check('test_check_1')
    if not success:
        # Debug why registration failed
        memory_usage = __import__('psutil').virtual_memory().percent
        cpu_usage = __import__('psutil').cpu_percent(interval=0.1)
        print(f"Registration failed - Memory: {memory_usage}%, CPU: {cpu_usage}%")
        print(f"Limits - Max concurrent: {limits.max_concurrent_checks}, Max CPU: {limits.max_cpu_usage_percent}")
    assert success, "Should be able to register first check"
    print("✓ Check registration works")
    
    # Test resource stats
    stats = monitor.get_resource_stats()
    assert stats['active_checks'] == 1, f"Expected 1 active check, got {stats['active_checks']}"
    print("✓ Resource stats work")
    
    # Test queue functionality
    queue_success = monitor.add_to_queue('queued_check', priority=1)
    assert queue_success, "Should be able to add to queue"
    print("✓ Queue functionality works")
    
    # Test unregistration
    monitor.unregister_check('test_check_1')
    stats = monitor.get_resource_stats()
    assert stats['active_checks'] == 0, f"Expected 0 active checks, got {stats['active_checks']}"
    print("✓ Check unregistration works")
    
    print("ResourceMonitor tests passed!\n")


async def test_connection_pool_manager():
    """Test basic connection pool manager functionality."""
    print("Testing ConnectionPoolManager...")
    
    config = ConnectionPoolConfig(max_connections=5)
    pool_manager = ConnectionPoolManager(config)
    
    # Test initialization
    await pool_manager.initialize()
    print("✓ Pool initialization works")
    
    # Test getting sessions
    mcp_session = await pool_manager.get_mcp_session()
    rest_session = await pool_manager.get_rest_session()
    
    assert mcp_session is not None, "MCP session should not be None"
    assert rest_session is not None, "REST session should not be None"
    print("✓ Session retrieval works")
    
    # Test pool stats
    stats = pool_manager.get_pool_stats()
    assert 'mcp_pool' in stats, "Expected mcp_pool in stats"
    assert 'rest_pool' in stats, "Expected rest_pool in stats"
    print("✓ Pool stats work")
    
    # Cleanup
    await pool_manager.close()
    print("✓ Pool cleanup works")
    
    print("ConnectionPoolManager tests passed!\n")


async def test_batch_scheduler():
    """Test basic batch scheduler functionality."""
    print("Testing BatchScheduler...")
    
    scheduler = BatchScheduler(max_batch_size=2, batch_timeout=1)
    
    # Create mock server config
    class MockServerConfig:
        def __init__(self, name):
            self.server_name = name
    
    # Test adding requests
    batch_id = await scheduler.add_request(MockServerConfig('server1'), priority=1)
    assert batch_id is not None, "Batch ID should not be None"
    print("✓ Request addition works")
    
    # Test getting ready batches (should be empty initially)
    ready_batches = await scheduler.get_ready_batches()
    assert isinstance(ready_batches, list), "Ready batches should be a list"
    print("✓ Ready batches retrieval works")
    
    print("BatchScheduler tests passed!\n")


async def main():
    """Run all basic functionality tests."""
    print("=== Enhanced MCP Status Check - Performance Optimization Tests ===\n")
    
    try:
        # Test synchronous components
        test_cache_manager()
        test_resource_monitor()
        
        # Test asynchronous components
        await test_connection_pool_manager()
        await test_batch_scheduler()
        
        print("🎉 All basic functionality tests passed!")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
        
    return 0


if __name__ == '__main__':
    exit_code = asyncio.run(main())
    sys.exit(exit_code)