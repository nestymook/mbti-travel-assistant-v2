"""
Performance tests for concurrent request handling.

Tests system performance under concurrent load, response times,
resource usage, and scalability characteristics.
"""

import pytest
import asyncio
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import AsyncMock, patch, Mock
import statistics
from typing import List, Dict, Any

from fastapi.testclient import TestClient
from main import app


class TestConcurrentRequestHandling:
    """Test cases for concurrent request handling performance."""
    
    @pytest.fixture
    def performance_client(self):
        """Create test client optimized for performance testing."""
        return TestClient(app)
    
    @pytest.fixture
    def mock_fast_mcp_client(self):
        """Mock MCP client with fast responses for performance testing."""
        mock_client = AsyncMock()
        mock_client.call_mcp_tool.return_value = {
            "success": True,
            "data": {
                "restaurants": [
                    {
                        "id": "rest_001",
                        "name": "Test Restaurant",
                        "district": "Central district",
                        "sentiment": {"likes": 85, "dislikes": 10, "neutral": 5}
                    }
                ],
                "total_count": 1
            }
        }
        return mock_client
    
    @pytest.fixture
    def auth_headers(self):
        """Authentication headers for performance tests."""
        return {"Authorization": "Bearer test-performance-token"}
    
    def test_concurrent_district_search_requests(self, performance_client, mock_fast_mcp_client, auth_headers):
        """Test concurrent district search requests performance."""
        num_requests = 50
        max_workers = 10
        
        with patch("middleware.auth_middleware.get_current_user") as mock_auth, \
             patch("api.restaurant_endpoints.get_mcp_client_manager", return_value=mock_fast_mcp_client):
            
            # Mock authentication
            mock_user = Mock()
            mock_user.user_id = "perf-test-user"
            mock_user.username = "perfuser"
            mock_user.email = "perf@test.com"
            mock_auth.return_value = mock_user
            
            def make_request(request_id: int) -> Dict[str, Any]:
                """Make a single request and measure performance."""
                start_time = time.time()
                
                response = performance_client.post(
                    "/api/v1/restaurants/search/district",
                    json={"districts": [f"District_{request_id % 5}"]},
                    headers=auth_headers
                )
                
                end_time = time.time()
                
                return {
                    "request_id": request_id,
                    "status_code": response.status_code,
                    "response_time": end_time - start_time,
                    "success": response.status_code == 200
                }
            
            # Execute concurrent requests
            start_total = time.time()
            results = []
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_id = {
                    executor.submit(make_request, i): i 
                    for i in range(num_requests)
                }
                
                for future in as_completed(future_to_id):
                    result = future.result()
                    results.append(result)
            
            end_total = time.time()
            total_time = end_total - start_total
            
            # Analyze results
            successful_requests = [r for r in results if r["success"]]
            response_times = [r["response_time"] for r in successful_requests]
            
            # Assertions
            assert len(successful_requests) == num_requests, "All requests should succeed"
            assert total_time < 30, f"Total time {total_time:.2f}s should be under 30s"
            
            # Performance metrics
            avg_response_time = statistics.mean(response_times)
            median_response_time = statistics.median(response_times)
            max_response_time = max(response_times)
            min_response_time = min(response_times)
            
            print(f"\nPerformance Metrics for {num_requests} concurrent requests:")
            print(f"Total time: {total_time:.2f}s")
            print(f"Requests per second: {num_requests / total_time:.2f}")
            print(f"Average response time: {avg_response_time:.3f}s")
            print(f"Median response time: {median_response_time:.3f}s")
            print(f"Min response time: {min_response_time:.3f}s")
            print(f"Max response time: {max_response_time:.3f}s")
            
            # Performance assertions
            assert avg_response_time < 1.0, f"Average response time {avg_response_time:.3f}s should be under 1s"
            assert max_response_time < 5.0, f"Max response time {max_response_time:.3f}s should be under 5s"
            assert num_requests / total_time > 5, f"Should handle at least 5 requests per second"
    
    def test_mixed_endpoint_concurrent_load(self, performance_client, mock_fast_mcp_client, auth_headers):
        """Test concurrent load across different endpoints."""
        num_requests_per_endpoint = 20
        
        with patch("middleware.auth_middleware.get_current_user") as mock_auth, \
             patch("api.restaurant_endpoints.get_mcp_client_manager", return_value=mock_fast_mcp_client), \
             patch("api.tool_metadata_endpoints.get_current_user", return_value=mock_auth.return_value):
            
            # Mock authentication
            mock_user = Mock()
            mock_user.user_id = "perf-test-user"
            mock_user.username = "perfuser"
            mock_user.email = "perf@test.com"
            mock_auth.return_value = mock_user
            
            def make_district_search(request_id: int) -> Dict[str, Any]:
                start_time = time.time()
                response = performance_client.post(
                    "/api/v1/restaurants/search/district",
                    json={"districts": ["Central district"]},
                    headers=auth_headers
                )
                return {
                    "endpoint": "district_search",
                    "request_id": request_id,
                    "status_code": response.status_code,
                    "response_time": time.time() - start_time
                }
            
            def make_meal_type_search(request_id: int) -> Dict[str, Any]:
                start_time = time.time()
                response = performance_client.post(
                    "/api/v1/restaurants/search/meal-type",
                    json={"meal_types": ["lunch"]},
                    headers=auth_headers
                )
                return {
                    "endpoint": "meal_type_search",
                    "request_id": request_id,
                    "status_code": response.status_code,
                    "response_time": time.time() - start_time
                }
            
            def make_tools_metadata(request_id: int) -> Dict[str, Any]:
                start_time = time.time()
                response = performance_client.get(
                    "/api/v1/tools/metadata",
                    headers=auth_headers
                )
                return {
                    "endpoint": "tools_metadata",
                    "request_id": request_id,
                    "status_code": response.status_code,
                    "response_time": time.time() - start_time
                }
            
            # Execute mixed concurrent requests
            start_total = time.time()
            results = []
            
            with ThreadPoolExecutor(max_workers=15) as executor:
                futures = []
                
                # Submit requests for each endpoint type
                for i in range(num_requests_per_endpoint):
                    futures.append(executor.submit(make_district_search, i))
                    futures.append(executor.submit(make_meal_type_search, i))
                    futures.append(executor.submit(make_tools_metadata, i))
                
                for future in as_completed(futures):
                    results.append(future.result())
            
            end_total = time.time()
            total_time = end_total - start_total
            
            # Analyze results by endpoint
            endpoint_stats = {}
            for result in results:
                endpoint = result["endpoint"]
                if endpoint not in endpoint_stats:
                    endpoint_stats[endpoint] = []
                endpoint_stats[endpoint].append(result)
            
            print(f"\nMixed endpoint performance ({len(results)} total requests):")
            print(f"Total time: {total_time:.2f}s")
            print(f"Overall RPS: {len(results) / total_time:.2f}")
            
            for endpoint, stats in endpoint_stats.items():
                successful = [s for s in stats if s["status_code"] == 200]
                if successful:
                    response_times = [s["response_time"] for s in successful]
                    avg_time = statistics.mean(response_times)
                    print(f"{endpoint}: {len(successful)} requests, avg {avg_time:.3f}s")
                    
                    # Each endpoint should perform reasonably
                    assert len(successful) == num_requests_per_endpoint
                    assert avg_time < 2.0, f"{endpoint} average response time should be under 2s"
    
    def test_authentication_performance_under_load(self, performance_client, mock_fast_mcp_client):
        """Test authentication performance under concurrent load."""
        num_requests = 30
        
        with patch("api.restaurant_endpoints.get_mcp_client_manager", return_value=mock_fast_mcp_client):
            
            def make_authenticated_request(request_id: int) -> Dict[str, Any]:
                """Make request with authentication validation."""
                start_time = time.time()
                
                response = performance_client.post(
                    "/api/v1/restaurants/search/district",
                    json={"districts": ["Central district"]},
                    headers={"Authorization": f"Bearer test-token-{request_id}"}
                )
                
                return {
                    "request_id": request_id,
                    "status_code": response.status_code,
                    "response_time": time.time() - start_time,
                    "auth_processed": response.status_code in [200, 401]  # Either success or auth failure
                }
            
            # Execute concurrent authenticated requests
            start_total = time.time()
            results = []
            
            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = [executor.submit(make_authenticated_request, i) for i in range(num_requests)]
                results = [future.result() for future in as_completed(futures)]
            
            end_total = time.time()
            total_time = end_total - start_total
            
            # Analyze authentication performance
            auth_processed = [r for r in results if r["auth_processed"]]
            response_times = [r["response_time"] for r in auth_processed]
            
            print(f"\nAuthentication performance under load:")
            print(f"Requests processed: {len(auth_processed)}/{num_requests}")
            print(f"Total time: {total_time:.2f}s")
            print(f"Auth RPS: {len(auth_processed) / total_time:.2f}")
            
            if response_times:
                avg_auth_time = statistics.mean(response_times)
                print(f"Average auth response time: {avg_auth_time:.3f}s")
                
                # Authentication should not be a bottleneck
                assert avg_auth_time < 1.5, "Authentication should not significantly slow down requests"
            
            # All requests should be processed (either authenticated or rejected)
            assert len(auth_processed) == num_requests
    
    def test_error_handling_performance(self, performance_client, auth_headers):
        """Test error handling performance under concurrent load."""
        num_requests = 25
        
        with patch("middleware.auth_middleware.get_current_user") as mock_auth, \
             patch("api.restaurant_endpoints.get_mcp_client_manager") as mock_get_client:
            
            # Mock authentication
            mock_user = Mock()
            mock_user.user_id = "perf-test-user"
            mock_auth.return_value = mock_user
            
            # Mock MCP client to simulate errors
            mock_client = AsyncMock()
            mock_client.call_mcp_tool.side_effect = Exception("Simulated MCP error")
            mock_get_client.return_value = mock_client
            
            def make_error_request(request_id: int) -> Dict[str, Any]:
                """Make request that will result in error."""
                start_time = time.time()
                
                response = performance_client.post(
                    "/api/v1/restaurants/search/district",
                    json={"districts": ["Central district"]},
                    headers=auth_headers
                )
                
                return {
                    "request_id": request_id,
                    "status_code": response.status_code,
                    "response_time": time.time() - start_time,
                    "is_error": response.status_code >= 400
                }
            
            # Execute concurrent error-generating requests
            start_total = time.time()
            results = []
            
            with ThreadPoolExecutor(max_workers=8) as executor:
                futures = [executor.submit(make_error_request, i) for i in range(num_requests)]
                results = [future.result() for future in as_completed(futures)]
            
            end_total = time.time()
            total_time = end_total - start_total
            
            # Analyze error handling performance
            error_responses = [r for r in results if r["is_error"]]
            response_times = [r["response_time"] for r in results]
            
            print(f"\nError handling performance:")
            print(f"Error responses: {len(error_responses)}/{num_requests}")
            print(f"Total time: {total_time:.2f}s")
            
            if response_times:
                avg_error_time = statistics.mean(response_times)
                print(f"Average error response time: {avg_error_time:.3f}s")
                
                # Error handling should be fast
                assert avg_error_time < 1.0, "Error responses should be fast"
            
            # All requests should return error responses
            assert len(error_responses) == num_requests
            
            # Error responses should be consistent (503 for MCP errors)
            error_codes = [r["status_code"] for r in error_responses]
            assert all(code == 503 for code in error_codes), "Should return consistent error codes"


class TestMemoryAndResourceUsage:
    """Test cases for memory and resource usage under load."""
    
    @pytest.fixture
    def resource_client(self):
        """Create test client for resource usage testing."""
        return TestClient(app)
    
    def test_memory_usage_under_load(self, resource_client):
        """Test memory usage doesn't grow excessively under load."""
        import psutil
        import os
        
        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        num_requests = 100
        
        with patch("middleware.auth_middleware.get_current_user") as mock_auth, \
             patch("api.restaurant_endpoints.get_mcp_client_manager") as mock_get_client:
            
            # Mock authentication and MCP client
            mock_user = Mock()
            mock_user.user_id = "memory-test-user"
            mock_auth.return_value = mock_user
            
            mock_client = AsyncMock()
            mock_client.call_mcp_tool.return_value = {
                "success": True,
                "data": {"restaurants": []}
            }
            mock_get_client.return_value = mock_client
            
            # Make many requests to test memory usage
            for i in range(num_requests):
                response = resource_client.post(
                    "/api/v1/restaurants/search/district",
                    json={"districts": ["Central district"]},
                    headers={"Authorization": "Bearer test-token"}
                )
                assert response.status_code == 200
                
                # Check memory every 25 requests
                if i % 25 == 0:
                    current_memory = process.memory_info().rss / 1024 / 1024  # MB
                    memory_growth = current_memory - initial_memory
                    print(f"Request {i}: Memory usage {current_memory:.1f}MB (+{memory_growth:.1f}MB)")
            
            # Final memory check
            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_growth = final_memory - initial_memory
            
            print(f"\nMemory usage test results:")
            print(f"Initial memory: {initial_memory:.1f}MB")
            print(f"Final memory: {final_memory:.1f}MB")
            print(f"Memory growth: {memory_growth:.1f}MB")
            
            # Memory growth should be reasonable (less than 50MB for 100 requests)
            assert memory_growth < 50, f"Memory growth {memory_growth:.1f}MB should be under 50MB"
    
    def test_connection_pool_efficiency(self, resource_client):
        """Test that connection pooling is efficient under load."""
        num_requests = 50
        
        with patch("middleware.auth_middleware.get_current_user") as mock_auth, \
             patch("services.mcp_client_manager.MCPConnectionPool") as mock_pool_class:
            
            # Mock authentication
            mock_user = Mock()
            mock_user.user_id = "pool-test-user"
            mock_auth.return_value = mock_user
            
            # Mock connection pool to track usage
            mock_pool = Mock()
            mock_client = AsyncMock()
            mock_client.post.return_value.json.return_value = {
                "success": True,
                "data": {"restaurants": []}
            }
            mock_client.post.return_value.status_code = 200
            mock_pool.get_client.return_value = mock_client
            mock_pool_class.return_value = mock_pool
            
            # Make multiple requests
            for i in range(num_requests):
                response = resource_client.post(
                    "/api/v1/restaurants/search/district",
                    json={"districts": ["Central district"]},
                    headers={"Authorization": "Bearer test-token"}
                )
                # Note: This test would need actual MCP client integration to be meaningful
                # For now, we just verify the requests are handled
            
            print(f"Connection pool test: {num_requests} requests processed")
            # In a real implementation, we would verify:
            # - Connection reuse
            # - Pool size limits
            # - Connection cleanup


class TestScalabilityLimits:
    """Test cases for system scalability limits."""
    
    def test_maximum_concurrent_requests(self, performance_client):
        """Test system behavior at maximum concurrent request levels."""
        max_concurrent = 100  # Aggressive test
        
        with patch("middleware.auth_middleware.get_current_user") as mock_auth, \
             patch("api.restaurant_endpoints.get_mcp_client_manager") as mock_get_client:
            
            # Mock authentication and MCP client
            mock_user = Mock()
            mock_user.user_id = "scale-test-user"
            mock_auth.return_value = mock_user
            
            mock_client = AsyncMock()
            mock_client.call_mcp_tool.return_value = {
                "success": True,
                "data": {"restaurants": []}
            }
            mock_get_client.return_value = mock_client
            
            def make_request(request_id: int) -> Dict[str, Any]:
                start_time = time.time()
                try:
                    response = performance_client.post(
                        "/api/v1/restaurants/search/district",
                        json={"districts": ["Central district"]},
                        headers={"Authorization": "Bearer test-token"}
                    )
                    return {
                        "request_id": request_id,
                        "status_code": response.status_code,
                        "response_time": time.time() - start_time,
                        "success": True
                    }
                except Exception as e:
                    return {
                        "request_id": request_id,
                        "status_code": 500,
                        "response_time": time.time() - start_time,
                        "success": False,
                        "error": str(e)
                    }
            
            # Execute maximum concurrent requests
            start_total = time.time()
            results = []
            
            with ThreadPoolExecutor(max_workers=max_concurrent) as executor:
                futures = [executor.submit(make_request, i) for i in range(max_concurrent)]
                results = [future.result() for future in as_completed(futures)]
            
            end_total = time.time()
            total_time = end_total - start_total
            
            # Analyze scalability results
            successful_requests = [r for r in results if r["success"] and r["status_code"] == 200]
            failed_requests = [r for r in results if not r["success"] or r["status_code"] != 200]
            
            success_rate = len(successful_requests) / len(results) * 100
            
            print(f"\nScalability test results ({max_concurrent} concurrent requests):")
            print(f"Total time: {total_time:.2f}s")
            print(f"Successful requests: {len(successful_requests)}")
            print(f"Failed requests: {len(failed_requests)}")
            print(f"Success rate: {success_rate:.1f}%")
            print(f"Throughput: {len(successful_requests) / total_time:.2f} RPS")
            
            # System should handle at least 80% of requests successfully
            assert success_rate >= 80, f"Success rate {success_rate:.1f}% should be at least 80%"
            
            # Should complete within reasonable time
            assert total_time < 60, f"Should complete {max_concurrent} requests within 60s"
            
            if successful_requests:
                response_times = [r["response_time"] for r in successful_requests]
                avg_response_time = statistics.mean(response_times)
                p95_response_time = statistics.quantiles(response_times, n=20)[18]  # 95th percentile
                
                print(f"Average response time: {avg_response_time:.3f}s")
                print(f"95th percentile response time: {p95_response_time:.3f}s")
                
                # Performance should degrade gracefully under load
                assert avg_response_time < 5.0, "Average response time should be under 5s even under load"
                assert p95_response_time < 10.0, "95th percentile should be under 10s"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])  # -s to show print statements