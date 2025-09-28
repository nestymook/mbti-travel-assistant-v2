"""
Performance and Load Testing Suite

Tests concurrent request handling, response time validation,
and load testing for MCP client connection management.
"""

import pytest
import asyncio
import time
import statistics
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import json

# Import components for testing
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import process_restaurant_request
from services.mcp_client_manager import MCPClientManager
from services.restaurant_agent import RestaurantAgent
from services.cache_service import CacheService
from models.restaurant_models import Restaurant, Sentiment


class TestPerformanceAndLoad:
    """Performance and load testing suite."""
    
    @pytest.fixture
    def sample_restaurants(self):
        """Create sample restaurant data for testing."""
        restaurants = []
        for i in range(50):  # Create 50 restaurants for load testing
            restaurants.append(Restaurant(
                id=f"rest_{i:03d}",
                name=f"Restaurant {i}",
                address=f"{i} Test Street",
                district="Central district" if i % 2 == 0 else "Admiralty",
                meal_type=["breakfast", "lunch", "dinner"],
                sentiment=Sentiment(likes=80 + i % 20, dislikes=10 + i % 10, neutral=5 + i % 5),
                price_range="$" if i % 3 == 0 else "$$" if i % 3 == 1 else "$$$",
                operating_hours={"Monday": ["07:00", "22:00"]},
                location_category="Shopping Mall" if i % 2 == 0 else "Street Food"
            ))
        return restaurants
    
    @pytest.fixture
    def sample_reasoning_results(self, sample_restaurants):
        """Create sample reasoning results for testing."""
        return {
            "recommendation": {
                "id": "rest_001",
                "name": "Restaurant 1",
                "address": "1 Test Street",
                "district": "Central district",
                "meal_type": ["breakfast"],
                "sentiment": {"likes": 85, "dislikes": 10, "neutral": 5},
                "price_range": "$",
                "operating_hours": {"Monday": ["07:00", "22:00"]},
                "location_category": "Shopping Mall"
            },
            "candidates": [
                {
                    "id": f"rest_{i:03d}",
                    "name": f"Restaurant {i}",
                    "address": f"{i} Test Street",
                    "district": "Central district" if i % 2 == 0 else "Admiralty",
                    "meal_type": ["breakfast"],
                    "sentiment": {"likes": 80 + i % 20, "dislikes": 10 + i % 10, "neutral": 5 + i % 5},
                    "price_range": "$",
                    "operating_hours": {"Monday": ["07:00", "22:00"]},
                    "location_category": "Shopping Mall"
                }
                for i in range(2, 21)  # 19 candidates
            ],
            "ranking_method": "sentiment_likes",
            "analysis_summary": {
                "total_restaurants": 50,
                "average_sentiment": 85.0
            }
        }
    
    def test_single_request_response_time(self, sample_restaurants, sample_reasoning_results):
        """Test response time for a single request meets requirements."""
        payload = {
            "district": "Central district",
            "meal_time": "breakfast"
        }
        
        with patch('main.restaurant_agent') as mock_agent, \
             patch('main.response_formatter') as mock_formatter, \
             patch('main.cache_service') as mock_cache, \
             patch('main.settings') as mock_settings:
            
            # Configure settings
            mock_settings.authentication.require_authentication = False
            mock_settings.cache.enable_response_cache = False
            
            # Mock agent processing
            mock_agent.process_request = AsyncMock(return_value=sample_reasoning_results)
            
            # Mock response formatting
            mock_formatter.format_response.return_value = {
                "recommendation": sample_reasoning_results["recommendation"],
                "candidates": sample_reasoning_results["candidates"],
                "metadata": {
                    "search_criteria": {"district": "Central district", "meal_time": "breakfast"},
                    "total_found": 20,
                    "timestamp": datetime.utcnow().isoformat(),
                    "processing_time_ms": 150.0
                }
            }
            
            # Measure response time
            start_time = time.time()
            result = process_restaurant_request(payload)
            end_time = time.time()
            
            response_time = (end_time - start_time) * 1000  # Convert to milliseconds
            
            # Verify response time meets requirement (< 5000ms)
            assert response_time < 5000, f"Response time {response_time}ms exceeds 5000ms requirement"
            
            # Verify response is valid
            response_data = json.loads(result)
            assert "recommendation" in response_data
            assert "candidates" in response_data
            
            print(f"✅ Single request response time: {response_time:.2f}ms")
    
    def test_concurrent_request_handling(self, sample_reasoning_results):
        """Test handling of concurrent requests."""
        num_concurrent_requests = 10
        payloads = [
            {
                "district": f"District_{i}",
                "meal_time": "breakfast" if i % 3 == 0 else "lunch" if i % 3 == 1 else "dinner"
            }
            for i in range(num_concurrent_requests)
        ]
        
        with patch('main.restaurant_agent') as mock_agent, \
             patch('main.response_formatter') as mock_formatter, \
             patch('main.cache_service') as mock_cache, \
             patch('main.settings') as mock_settings:
            
            # Configure settings
            mock_settings.authentication.require_authentication = False
            mock_settings.cache.enable_response_cache = False
            
            # Mock agent processing with slight delay
            async def mock_process(*args, **kwargs):
                await asyncio.sleep(0.1)  # Simulate processing time
                return sample_reasoning_results
            
            mock_agent.process_request = mock_process
            
            # Mock response formatting
            mock_formatter.format_response.return_value = {
                "recommendation": sample_reasoning_results["recommendation"],
                "candidates": sample_reasoning_results["candidates"],
                "metadata": {"total_found": 20}
            }
            
            # Process requests concurrently using ThreadPoolExecutor
            start_time = time.time()
            results = []
            response_times = []
            
            with ThreadPoolExecutor(max_workers=num_concurrent_requests) as executor:
                # Submit all requests
                future_to_payload = {
                    executor.submit(self._process_request_with_timing, payload): payload
                    for payload in payloads
                }
                
                # Collect results
                for future in as_completed(future_to_payload):
                    result, request_time = future.result()
                    results.append(result)
                    response_times.append(request_time)
            
            total_time = time.time() - start_time
            
            # Verify all requests completed successfully
            assert len(results) == num_concurrent_requests
            for result in results:
                response_data = json.loads(result)
                assert "recommendation" in response_data
                assert "candidates" in response_data
            
            # Verify performance metrics
            avg_response_time = statistics.mean(response_times)
            max_response_time = max(response_times)
            min_response_time = min(response_times)
            
            # All requests should complete within reasonable time
            assert max_response_time < 5000, f"Max response time {max_response_time}ms exceeds limit"
            assert avg_response_time < 2000, f"Average response time {avg_response_time}ms too high"
            
            print(f"✅ Concurrent requests: {num_concurrent_requests}")
            print(f"✅ Total time: {total_time:.2f}s")
            print(f"✅ Average response time: {avg_response_time:.2f}ms")
            print(f"✅ Min response time: {min_response_time:.2f}ms")
            print(f"✅ Max response time: {max_response_time:.2f}ms")
    
    def _process_request_with_timing(self, payload):
        """Helper method to process request and measure timing."""
        start_time = time.time()
        result = process_restaurant_request(payload)
        end_time = time.time()
        
        response_time = (end_time - start_time) * 1000  # Convert to milliseconds
        return result, response_time
    
    @pytest.mark.asyncio
    async def test_mcp_client_connection_performance(self, sample_restaurants):
        """Test MCP client connection management performance."""
        with patch('services.mcp_client_manager.settings') as mock_settings:
            mock_settings.mcp_client.search_mcp_endpoint = "mock://search-mcp"
            mock_settings.mcp_client.reasoning_mcp_endpoint = "mock://reasoning-mcp"
            mock_settings.mcp_client.mcp_connection_timeout = 30
            mock_settings.mcp_client.mcp_retry_attempts = 3
            
            manager = MCPClientManager()
            
            # Mock MCP session
            mock_session = Mock()
            mock_session.call_tool = AsyncMock()
            mock_session.list_tools = AsyncMock(return_value=[Mock(), Mock()])
            
            # Mock successful search response
            mock_result = Mock()
            mock_result.isError = False
            mock_result.content = [Mock(text=json.dumps({
                "success": True,
                "data": {
                    "restaurants": [
                        {
                            "id": "rest_001",
                            "name": "Test Restaurant",
                            "district": "Central district",
                            "meal_type": ["breakfast"],
                            "sentiment": {"likes": 85, "dislikes": 10, "neutral": 5},
                            "price_range": "$",
                            "operating_hours": {"Monday": ["07:00", "11:30"]},
                            "location_category": "Shopping Mall"
                        }
                    ]
                }
            }))]
            
            mock_session.call_tool.return_value = mock_result
            
            # Mock session context manager
            async def mock_get_session(endpoint):
                return mock_session
            
            manager._get_mcp_session = mock_get_session
            
            # Test multiple concurrent MCP calls
            num_calls = 20
            start_time = time.time()
            
            tasks = []
            for i in range(num_calls):
                task = manager.search_restaurants(
                    district=f"District_{i % 5}",
                    meal_time="breakfast"
                )
                tasks.append(task)
            
            # Execute all calls concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            total_time = time.time() - start_time
            
            # Verify all calls completed successfully
            successful_calls = 0
            for result in results:
                if isinstance(result, Exception):
                    print(f"❌ Call failed: {result}")
                else:
                    successful_calls += 1
                    assert isinstance(result, list)
            
            success_rate = successful_calls / num_calls * 100
            avg_time_per_call = (total_time / num_calls) * 1000  # ms
            
            # Performance assertions
            assert success_rate >= 95, f"Success rate {success_rate}% below 95% threshold"
            assert avg_time_per_call < 1000, f"Average call time {avg_time_per_call}ms too high"
            
            print(f"✅ MCP concurrent calls: {num_calls}")
            print(f"✅ Success rate: {success_rate:.1f}%")
            print(f"✅ Total time: {total_time:.2f}s")
            print(f"✅ Average time per call: {avg_time_per_call:.2f}ms")
    
    def test_cache_performance_impact(self, sample_reasoning_results):
        """Test performance impact of caching."""
        payload = {
            "district": "Central district",
            "meal_time": "breakfast"
        }
        
        # Test without cache
        with patch('main.restaurant_agent') as mock_agent, \
             patch('main.response_formatter') as mock_formatter, \
             patch('main.cache_service') as mock_cache, \
             patch('main.settings') as mock_settings:
            
            # Configure settings - cache disabled
            mock_settings.authentication.require_authentication = False
            mock_settings.cache.enable_response_cache = False
            
            # Mock cache miss
            mock_cache.get_cached_response.return_value = None
            
            # Mock agent processing with delay
            async def slow_process(*args, **kwargs):
                await asyncio.sleep(0.2)  # Simulate slow processing
                return sample_reasoning_results
            
            mock_agent.process_request = slow_process
            
            # Mock response formatting
            formatted_response = {
                "recommendation": sample_reasoning_results["recommendation"],
                "candidates": sample_reasoning_results["candidates"],
                "metadata": {"cache_hit": False}
            }
            mock_formatter.format_response.return_value = formatted_response
            
            # Measure time without cache
            start_time = time.time()
            result_no_cache = process_restaurant_request(payload)
            time_no_cache = (time.time() - start_time) * 1000
        
        # Test with cache hit
        with patch('main.cache_service') as mock_cache, \
             patch('main.settings') as mock_settings:
            
            # Configure settings - cache enabled
            mock_settings.authentication.require_authentication = False
            mock_settings.cache.enable_response_cache = True
            
            # Mock cache hit
            cached_response = {
                "recommendation": sample_reasoning_results["recommendation"],
                "candidates": sample_reasoning_results["candidates"],
                "metadata": {"cache_hit": True, "processing_time_ms": 5.0}
            }
            mock_cache.get_cached_response.return_value = json.dumps(cached_response)
            
            # Measure time with cache
            start_time = time.time()
            result_cached = process_restaurant_request(payload)
            time_cached = (time.time() - start_time) * 1000
        
        # Verify cache provides significant performance improvement
        cache_speedup = time_no_cache / time_cached if time_cached > 0 else float('inf')
        
        assert time_cached < time_no_cache, "Cache should be faster than no cache"
        assert cache_speedup > 5, f"Cache speedup {cache_speedup:.1f}x should be > 5x"
        
        # Verify both responses are valid
        response_no_cache = json.loads(result_no_cache)
        response_cached = json.loads(result_cached)
        
        assert "recommendation" in response_no_cache
        assert "recommendation" in response_cached
        
        print(f"✅ Time without cache: {time_no_cache:.2f}ms")
        print(f"✅ Time with cache: {time_cached:.2f}ms")
        print(f"✅ Cache speedup: {cache_speedup:.1f}x")
    
    def test_memory_usage_under_load(self, sample_reasoning_results):
        """Test memory usage under sustained load."""
        import psutil
        import gc
        
        # Get initial memory usage
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        num_requests = 100
        payloads = [
            {
                "district": f"District_{i % 10}",
                "meal_time": ["breakfast", "lunch", "dinner"][i % 3]
            }
            for i in range(num_requests)
        ]
        
        with patch('main.restaurant_agent') as mock_agent, \
             patch('main.response_formatter') as mock_formatter, \
             patch('main.cache_service') as mock_cache, \
             patch('main.settings') as mock_settings:
            
            # Configure settings
            mock_settings.authentication.require_authentication = False
            mock_settings.cache.enable_response_cache = False
            
            # Mock agent processing
            mock_agent.process_request = AsyncMock(return_value=sample_reasoning_results)
            
            # Mock response formatting
            mock_formatter.format_response.return_value = {
                "recommendation": sample_reasoning_results["recommendation"],
                "candidates": sample_reasoning_results["candidates"],
                "metadata": {"total_found": 20}
            }
            
            # Process all requests
            memory_samples = []
            for i, payload in enumerate(payloads):
                result = process_restaurant_request(payload)
                
                # Sample memory usage every 10 requests
                if i % 10 == 0:
                    current_memory = process.memory_info().rss / 1024 / 1024  # MB
                    memory_samples.append(current_memory)
                
                # Verify response is valid
                response_data = json.loads(result)
                assert "recommendation" in response_data
        
        # Force garbage collection
        gc.collect()
        
        # Get final memory usage
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        max_memory = max(memory_samples) if memory_samples else final_memory
        
        # Memory usage should not increase excessively
        assert memory_increase < 100, f"Memory increase {memory_increase:.1f}MB too high"
        assert max_memory < initial_memory + 150, f"Peak memory {max_memory:.1f}MB too high"
        
        print(f"✅ Initial memory: {initial_memory:.1f}MB")
        print(f"✅ Final memory: {final_memory:.1f}MB")
        print(f"✅ Memory increase: {memory_increase:.1f}MB")
        print(f"✅ Peak memory: {max_memory:.1f}MB")
        print(f"✅ Processed {num_requests} requests")
    
    def test_response_time_percentiles(self, sample_reasoning_results):
        """Test response time percentiles under load."""
        num_requests = 50
        payloads = [
            {
                "district": "Central district",
                "meal_time": "breakfast"
            }
            for _ in range(num_requests)
        ]
        
        with patch('main.restaurant_agent') as mock_agent, \
             patch('main.response_formatter') as mock_formatter, \
             patch('main.cache_service') as mock_cache, \
             patch('main.settings') as mock_settings:
            
            # Configure settings
            mock_settings.authentication.require_authentication = False
            mock_settings.cache.enable_response_cache = False
            
            # Mock agent processing with variable delay
            async def variable_process(*args, **kwargs):
                # Simulate variable processing time
                import random
                delay = random.uniform(0.05, 0.3)  # 50-300ms
                await asyncio.sleep(delay)
                return sample_reasoning_results
            
            mock_agent.process_request = variable_process
            
            # Mock response formatting
            mock_formatter.format_response.return_value = {
                "recommendation": sample_reasoning_results["recommendation"],
                "candidates": sample_reasoning_results["candidates"],
                "metadata": {"total_found": 20}
            }
            
            # Process all requests and measure response times
            response_times = []
            
            for payload in payloads:
                start_time = time.time()
                result = process_restaurant_request(payload)
                end_time = time.time()
                
                response_time = (end_time - start_time) * 1000  # ms
                response_times.append(response_time)
                
                # Verify response is valid
                response_data = json.loads(result)
                assert "recommendation" in response_data
        
        # Calculate percentiles
        response_times.sort()
        p50 = statistics.median(response_times)
        p95 = response_times[int(0.95 * len(response_times))]
        p99 = response_times[int(0.99 * len(response_times))]
        avg_time = statistics.mean(response_times)
        
        # Performance assertions
        assert p50 < 2000, f"P50 response time {p50:.2f}ms exceeds 2000ms"
        assert p95 < 4000, f"P95 response time {p95:.2f}ms exceeds 4000ms"
        assert p99 < 5000, f"P99 response time {p99:.2f}ms exceeds 5000ms"
        assert avg_time < 1500, f"Average response time {avg_time:.2f}ms exceeds 1500ms"
        
        print(f"✅ Processed {num_requests} requests")
        print(f"✅ Average response time: {avg_time:.2f}ms")
        print(f"✅ P50 response time: {p50:.2f}ms")
        print(f"✅ P95 response time: {p95:.2f}ms")
        print(f"✅ P99 response time: {p99:.2f}ms")
    
    def test_cache_service_performance(self):
        """Test cache service performance under load."""
        cache_service = CacheService(default_ttl=1800)
        
        # Test cache write performance
        num_entries = 1000
        large_data = {"data": "x" * 1000}  # 1KB of data per entry
        
        start_time = time.time()
        for i in range(num_entries):
            cache_key = f"test_key_{i}"
            cache_service.cache_response(cache_key, json.dumps(large_data))
        write_time = time.time() - start_time
        
        # Test cache read performance
        start_time = time.time()
        hits = 0
        for i in range(num_entries):
            cache_key = f"test_key_{i}"
            result = cache_service.get_cached_response(cache_key)
            if result:
                hits += 1
        read_time = time.time() - start_time
        
        # Performance assertions
        write_rate = num_entries / write_time  # entries per second
        read_rate = num_entries / read_time    # entries per second
        hit_rate = hits / num_entries * 100    # percentage
        
        assert write_rate > 1000, f"Cache write rate {write_rate:.0f} entries/sec too low"
        assert read_rate > 5000, f"Cache read rate {read_rate:.0f} entries/sec too low"
        assert hit_rate == 100, f"Cache hit rate {hit_rate:.1f}% should be 100%"
        
        # Test cache statistics
        stats = cache_service.get_cache_stats()
        assert stats["total_entries"] == num_entries
        assert stats["active_entries"] == num_entries
        assert stats["cache_hits"] == num_entries
        
        print(f"✅ Cache write rate: {write_rate:.0f} entries/sec")
        print(f"✅ Cache read rate: {read_rate:.0f} entries/sec")
        print(f"✅ Cache hit rate: {hit_rate:.1f}%")
        print(f"✅ Cache entries: {stats['total_entries']}")
    
    def test_error_handling_performance(self, sample_reasoning_results):
        """Test that error handling doesn't significantly impact performance."""
        num_requests = 20
        error_rate = 0.2  # 20% of requests will fail
        
        payloads = [
            {
                "district": "Central district",
                "meal_time": "breakfast"
            }
            for _ in range(num_requests)
        ]
        
        with patch('main.restaurant_agent') as mock_agent, \
             patch('main.response_formatter') as mock_formatter, \
             patch('main.error_handler') as mock_error_handler, \
             patch('main.settings') as mock_settings:
            
            # Configure settings
            mock_settings.authentication.require_authentication = False
            mock_settings.cache.enable_response_cache = False
            
            # Mock agent processing with some failures
            call_count = 0
            async def sometimes_fail_process(*args, **kwargs):
                nonlocal call_count
                call_count += 1
                
                if call_count % int(1/error_rate) == 0:  # Fail every 5th request (20%)
                    raise Exception("Simulated processing error")
                
                await asyncio.sleep(0.1)  # Normal processing time
                return sample_reasoning_results
            
            mock_agent.process_request = sometimes_fail_process
            
            # Mock response formatting
            mock_formatter.format_response.return_value = {
                "recommendation": sample_reasoning_results["recommendation"],
                "candidates": sample_reasoning_results["candidates"],
                "metadata": {"total_found": 20}
            }
            
            # Mock error handler
            mock_error_handler.handle_error.return_value = {
                "recommendation": None,
                "candidates": [],
                "error": {"error_type": "internal_error", "message": "Processing failed"}
            }
            
            # Process all requests and measure response times
            response_times = []
            successful_requests = 0
            error_requests = 0
            
            for payload in payloads:
                start_time = time.time()
                result = process_restaurant_request(payload)
                end_time = time.time()
                
                response_time = (end_time - start_time) * 1000  # ms
                response_times.append(response_time)
                
                # Check if request was successful or error
                response_data = json.loads(result)
                if "error" in response_data:
                    error_requests += 1
                else:
                    successful_requests += 1
        
        # Verify error rate is as expected
        actual_error_rate = error_requests / num_requests
        assert abs(actual_error_rate - error_rate) < 0.1, f"Error rate {actual_error_rate:.2f} not close to expected {error_rate:.2f}"
        
        # Verify error handling doesn't significantly slow down responses
        avg_response_time = statistics.mean(response_times)
        max_response_time = max(response_times)
        
        assert avg_response_time < 1000, f"Average response time {avg_response_time:.2f}ms too high with errors"
        assert max_response_time < 2000, f"Max response time {max_response_time:.2f}ms too high with errors"
        
        print(f"✅ Processed {num_requests} requests")
        print(f"✅ Successful requests: {successful_requests}")
        print(f"✅ Error requests: {error_requests}")
        print(f"✅ Error rate: {actual_error_rate:.1%}")
        print(f"✅ Average response time: {avg_response_time:.2f}ms")
        print(f"✅ Max response time: {max_response_time:.2f}ms")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])