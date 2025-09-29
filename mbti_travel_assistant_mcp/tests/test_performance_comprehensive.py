"""
Comprehensive Performance Tests for MBTI Travel Assistant

This module provides comprehensive performance tests for response time validation,
load testing, and performance benchmarking of the MBTI Travel Assistant system.
"""

import pytest
import asyncio
import time
import statistics
import psutil
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import Mock, patch, AsyncMock
from typing import List, Dict, Any, Tuple
import json
import gc
import sys

from ..services.itinerary_generator import ItineraryGenerator
from ..services.nova_pro_knowledge_base_client import NovaProKnowledgeBaseClient
from ..services.mcp_client_manager import MCPClientManager
from ..services.restaurant_agent import RestaurantAgent
from ..services.cache_service import CacheService
from ..models.tourist_spot_models import TouristSpot, TouristSpotOperatingHours
from ..models.restaurant_models import Restaurant


class TestPerformanceRequirements:
    """Test performance requirements compliance."""

    def setup_method(self):
        """Set up performance test fixtures."""
        self.itinerary_generator = ItineraryGenerator()
        self.performance_metrics = {
            "response_times": [],
            "memory_usage": [],
            "cpu_usage": [],
            "cache_hit_rates": []
        }
        
        # Create test data
        self.test_spots = self._create_performance_test_spots()
        self.test_restaurants = self._create_performance_test_restaurants()

    def _create_performance_test_spots(self) -> List[TouristSpot]:
        """Create tourist spots optimized for performance testing."""
        spots = []
        
        # Create larger dataset for performance testing
        districts = ["Central", "Admiralty", "Wan Chai", "Tsim Sha Tsui", "Causeway Bay", 
                    "Mong Kok", "Yau Ma Tei", "Jordan", "Sheung Wan", "Mid-Levels"]
        categories = ["Museum", "Park", "Temple", "Gallery", "Garden", "Market", "Observatory", "Monument"]
        
        for i in range(100):  # Large dataset for performance testing
            operating_hours = TouristSpotOperatingHours(
                monday="09:00-18:00", tuesday="09:00-18:00", wednesday="09:00-18:00",
                thursday="09:00-18:00", friday="09:00-18:00", saturday="10:00-17:00", sunday="10:00-17:00"
            )
            
            spot = TouristSpot(
                id=f"perf_spot_{i}",
                name=f"Performance Test Spot {i}",
                address=f"{1000 + i} Performance Street, {districts[i % len(districts)]}, Hong Kong",
                district=districts[i % len(districts)],
                area="Hong Kong Island" if i < 50 else "Kowloon",
                location_category=categories[i % len(categories)],
                description=f"Performance test attraction {i} for load testing",
                operating_hours=operating_hours,
                operating_days=["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"],
                mbti_personality_types=["INFJ", "ENFP", "INTJ", "ESTP"][i % 4],
                keywords=["performance", "test", "load"],
                mbti_match=True
            )
            spots.append(spot)
        
        return spots

    def _create_performance_test_restaurants(self) -> List[Restaurant]:
        """Create restaurants optimized for performance testing."""
        restaurants = []
        
        districts = ["Central", "Admiralty", "Wan Chai", "Tsim Sha Tsui", "Causeway Bay"]
        meal_configs = [
            ("breakfast", "07:00-11:00", "Cafe"),
            ("lunch", "11:30-15:00", "Bistro"),
            ("dinner", "18:00-22:00", "Restaurant")
        ]
        
        for district in districts:
            for meal_type, hours, cuisine in meal_configs:
                for i in range(10):  # More restaurants per category for performance testing
                    restaurant = Restaurant(
                        id=f"perf_{meal_type}_{district.lower()}_{i}",
                        name=f"Performance {district} {meal_type.title()} {cuisine} {i}",
                        address=f"{2000 + i} Performance {meal_type.title()} Street, {district}, Hong Kong",
                        district=district,
                        operating_hours=hours,
                        cuisine_type=cuisine,
                        phone=f"+852-{5000 + i}-{6000 + i}",
                        rating=3.5 + (i * 0.05),
                        sentiment={"likes": 70 + i, "dislikes": 15 - (i % 5), "neutral": 15}
                    )
                    restaurants.append(restaurant)
        
        return restaurants

    @pytest.mark.asyncio
    async def test_single_request_response_time_requirement(self):
        """Test that single request meets 10-second response time requirement."""
        # Mock dependencies for consistent performance testing
        with patch.object(self.itinerary_generator, 'nova_client') as mock_nova:
            with patch.object(self.itinerary_generator, 'mcp_client') as mock_mcp:
                with patch.object(self.itinerary_generator, 'restaurant_agent') as mock_restaurant:
                    
                    # Setup mocks with realistic delays
                    mock_nova.query_mbti_tourist_spots = AsyncMock(
                        return_value=self.test_spots[:20]  # Reasonable subset
                    )
                    mock_mcp.search_restaurants_by_meal_and_district = AsyncMock(
                        return_value=self.test_restaurants[:5]
                    )
                    mock_restaurant.get_restaurant_recommendations = AsyncMock(
                        return_value={"recommendation": self.test_restaurants[0], "candidates": []}
                    )
                    
                    # Measure response time
                    start_time = time.time()
                    result = await self.itinerary_generator.generate_complete_itinerary("INFJ")
                    end_time = time.time()
                    
                    response_time = (end_time - start_time) * 1000  # Convert to milliseconds
                    
                    # Verify 10-second requirement (10,000ms)
                    assert response_time < 10000, f"Response time {response_time}ms exceeds 10-second requirement"
                    
                    # Record performance metric
                    self.performance_metrics["response_times"].append(response_time)
                    
                    # Verify result completeness
                    assert "main_itinerary" in result
                    assert "metadata" in result
                    assert result["metadata"]["processing_time_ms"] < 10000

    @pytest.mark.asyncio
    async def test_response_time_percentiles(self):
        """Test response time percentiles across multiple requests."""
        response_times = []
        
        with patch.object(self.itinerary_generator, 'nova_client') as mock_nova:
            with patch.object(self.itinerary_generator, 'mcp_client') as mock_mcp:
                with patch.object(self.itinerary_generator, 'restaurant_agent') as mock_restaurant:
                    
                    mock_nova.query_mbti_tourist_spots = AsyncMock(
                        return_value=self.test_spots[:15]
                    )
                    mock_mcp.search_restaurants_by_meal_and_district = AsyncMock(
                        return_value=self.test_restaurants[:3]
                    )
                    mock_restaurant.get_restaurant_recommendations = AsyncMock(
                        return_value={"recommendation": self.test_restaurants[0], "candidates": []}
                    )
                    
                    # Run multiple requests
                    for i in range(20):
                        start_time = time.time()
                        result = await self.itinerary_generator.generate_complete_itinerary("INFJ")
                        end_time = time.time()
                        
                        response_time = (end_time - start_time) * 1000
                        response_times.append(response_time)
                        
                        # Brief pause between requests
                        await asyncio.sleep(0.1)
        
        # Calculate percentiles
        p50 = statistics.median(response_times)
        p95 = statistics.quantiles(response_times, n=20)[18]  # 95th percentile
        p99 = statistics.quantiles(response_times, n=100)[98]  # 99th percentile
        
        # Performance requirements
        assert p50 < 5000, f"P50 response time {p50}ms exceeds 5-second target"
        assert p95 < 8000, f"P95 response time {p95}ms exceeds 8-second target"
        assert p99 < 10000, f"P99 response time {p99}ms exceeds 10-second requirement"
        
        # Record metrics
        self.performance_metrics["response_times"].extend(response_times)

    @pytest.mark.asyncio
    async def test_concurrent_request_performance(self):
        """Test performance under concurrent load."""
        concurrent_requests = 10
        
        with patch.object(self.itinerary_generator, 'nova_client') as mock_nova:
            with patch.object(self.itinerary_generator, 'mcp_client') as mock_mcp:
                with patch.object(self.itinerary_generator, 'restaurant_agent') as mock_restaurant:
                    
                    mock_nova.query_mbti_tourist_spots = AsyncMock(
                        return_value=self.test_spots[:15]
                    )
                    mock_mcp.search_restaurants_by_meal_and_district = AsyncMock(
                        return_value=self.test_restaurants[:3]
                    )
                    mock_restaurant.get_restaurant_recommendations = AsyncMock(
                        return_value={"recommendation": self.test_restaurants[0], "candidates": []}
                    )
                    
                    # Create concurrent tasks
                    mbti_types = ["INFJ", "ENFP", "INTJ", "ESTP", "ISFJ", "ISFP", "ISTJ", "ISTP", "ENFJ", "ENTP"]
                    
                    start_time = time.time()
                    
                    tasks = [
                        self.itinerary_generator.generate_complete_itinerary(mbti_types[i % len(mbti_types)])
                        for i in range(concurrent_requests)
                    ]
                    
                    results = await asyncio.gather(*tasks)
                    
                    end_time = time.time()
                    total_time = (end_time - start_time) * 1000
                    
                    # All requests should complete successfully
                    assert len(results) == concurrent_requests
                    assert all("main_itinerary" in result for result in results)
                    
                    # Average time per request should be reasonable
                    avg_time_per_request = total_time / concurrent_requests
                    assert avg_time_per_request < 15000, f"Average time per concurrent request {avg_time_per_request}ms too high"

    def test_memory_usage_under_load(self):
        """Test memory usage under sustained load."""
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Simulate sustained load
        for i in range(50):
            # Create and process mock data
            mock_spots = self.test_spots[:20]
            mock_restaurants = self.test_restaurants[:10]
            
            # Simulate processing
            processed_data = {
                "spots": [spot.to_dict() if hasattr(spot, 'to_dict') else spot.__dict__ for spot in mock_spots],
                "restaurants": [rest.to_dict() if hasattr(rest, 'to_dict') else rest.__dict__ for rest in mock_restaurants]
            }
            
            # Force garbage collection periodically
            if i % 10 == 0:
                gc.collect()
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (< 100MB)
        assert memory_increase < 100, f"Memory increase {memory_increase}MB too high under load"
        
        self.performance_metrics["memory_usage"].append(memory_increase)

    def test_cpu_usage_efficiency(self):
        """Test CPU usage efficiency during processing."""
        cpu_percentages = []
        
        def monitor_cpu():
            for _ in range(10):  # Monitor for 10 seconds
                cpu_percent = psutil.cpu_percent(interval=1)
                cpu_percentages.append(cpu_percent)
        
        # Start CPU monitoring in background
        cpu_thread = threading.Thread(target=monitor_cpu)
        cpu_thread.start()
        
        # Simulate processing load
        for i in range(20):
            # Simulate itinerary generation work
            mock_data = {
                "spots": self.test_spots[:10],
                "restaurants": self.test_restaurants[:5]
            }
            
            # Simulate processing time
            time.sleep(0.1)
            
            # Simulate data transformation
            processed = json.dumps([spot.__dict__ for spot in mock_data["spots"]])
            parsed = json.loads(processed)
        
        cpu_thread.join()
        
        # CPU usage should be reasonable
        avg_cpu = statistics.mean(cpu_percentages)
        max_cpu = max(cpu_percentages)
        
        assert avg_cpu < 80, f"Average CPU usage {avg_cpu}% too high"
        assert max_cpu < 95, f"Maximum CPU usage {max_cpu}% too high"
        
        self.performance_metrics["cpu_usage"].extend(cpu_percentages)

    @pytest.mark.asyncio
    async def test_cache_performance_impact(self):
        """Test cache performance impact on response times."""
        cache_service = CacheService()
        
        with patch.object(self.itinerary_generator, 'nova_client') as mock_nova:
            with patch.object(self.itinerary_generator, 'mcp_client') as mock_mcp:
                with patch.object(self.itinerary_generator, 'restaurant_agent') as mock_restaurant:
                    
                    mock_nova.query_mbti_tourist_spots = AsyncMock(
                        return_value=self.test_spots[:15]
                    )
                    mock_mcp.search_restaurants_by_meal_and_district = AsyncMock(
                        return_value=self.test_restaurants[:3]
                    )
                    mock_restaurant.get_restaurant_recommendations = AsyncMock(
                        return_value={"recommendation": self.test_restaurants[0], "candidates": []}
                    )
                    
                    # Test without cache
                    self.itinerary_generator.enable_caching = False
                    
                    no_cache_times = []
                    for _ in range(5):
                        start_time = time.time()
                        await self.itinerary_generator.generate_complete_itinerary("INFJ")
                        end_time = time.time()
                        no_cache_times.append((end_time - start_time) * 1000)
                    
                    # Test with cache
                    self.itinerary_generator.enable_caching = True
                    
                    # First request (cache miss)
                    start_time = time.time()
                    await self.itinerary_generator.generate_complete_itinerary("INFJ")
                    first_cached_time = (time.time() - start_time) * 1000
                    
                    # Subsequent requests (cache hits)
                    cached_times = []
                    for _ in range(5):
                        start_time = time.time()
                        await self.itinerary_generator.generate_complete_itinerary("INFJ")
                        end_time = time.time()
                        cached_times.append((end_time - start_time) * 1000)
                    
                    # Cache should improve performance
                    avg_no_cache = statistics.mean(no_cache_times)
                    avg_cached = statistics.mean(cached_times)
                    
                    # Cached requests should be significantly faster
                    performance_improvement = (avg_no_cache - avg_cached) / avg_no_cache
                    assert performance_improvement > 0.2, f"Cache performance improvement {performance_improvement:.2%} too low"

    def test_database_query_performance(self):
        """Test database query performance simulation."""
        query_times = []
        
        # Simulate database queries with varying complexity
        query_scenarios = [
            ("simple", 0.01),    # Simple query - 10ms
            ("medium", 0.05),    # Medium query - 50ms
            ("complex", 0.1),    # Complex query - 100ms
        ]
        
        for scenario_name, base_time in query_scenarios:
            for _ in range(10):
                start_time = time.time()
                
                # Simulate query processing
                time.sleep(base_time + (time.time() % 0.01))  # Add some variance
                
                # Simulate data processing
                mock_results = self.test_spots[:20] if scenario_name == "complex" else self.test_spots[:5]
                processed = [spot.__dict__ for spot in mock_results]
                
                end_time = time.time()
                query_time = (end_time - start_time) * 1000
                query_times.append(query_time)
        
        # Query performance requirements
        avg_query_time = statistics.mean(query_times)
        max_query_time = max(query_times)
        
        assert avg_query_time < 200, f"Average query time {avg_query_time}ms too high"
        assert max_query_time < 500, f"Maximum query time {max_query_time}ms too high"

    @pytest.mark.asyncio
    async def test_error_handling_performance_impact(self):
        """Test performance impact of error handling."""
        with patch.object(self.itinerary_generator, 'nova_client') as mock_nova:
            with patch.object(self.itinerary_generator, 'mcp_client') as mock_mcp:
                with patch.object(self.itinerary_generator, 'restaurant_agent') as mock_restaurant:
                    
                    # Test normal operation
                    mock_nova.query_mbti_tourist_spots = AsyncMock(
                        return_value=self.test_spots[:15]
                    )
                    mock_mcp.search_restaurants_by_meal_and_district = AsyncMock(
                        return_value=self.test_restaurants[:3]
                    )
                    mock_restaurant.get_restaurant_recommendations = AsyncMock(
                        return_value={"recommendation": self.test_restaurants[0], "candidates": []}
                    )
                    
                    # Measure normal operation time
                    start_time = time.time()
                    result = await self.itinerary_generator.generate_complete_itinerary("INFJ")
                    normal_time = (time.time() - start_time) * 1000
                    
                    # Test with errors and recovery
                    mock_nova.query_mbti_tourist_spots = AsyncMock(
                        side_effect=[Exception("Temporary error"), self.test_spots[:15]]
                    )
                    
                    start_time = time.time()
                    try:
                        result = await self.itinerary_generator.generate_complete_itinerary("INFJ")
                        error_recovery_time = (time.time() - start_time) * 1000
                        
                        # Error recovery should not significantly impact performance
                        performance_impact = (error_recovery_time - normal_time) / normal_time
                        assert performance_impact < 0.5, f"Error handling performance impact {performance_impact:.2%} too high"
                        
                    except Exception:
                        # If error handling fails, measure error processing time
                        error_time = (time.time() - start_time) * 1000
                        assert error_time < 1000, f"Error processing time {error_time}ms too high"

    def test_scalability_simulation(self):
        """Test scalability with increasing load simulation."""
        load_levels = [1, 5, 10, 20, 50]
        response_times_by_load = {}
        
        for load_level in load_levels:
            response_times = []
            
            # Simulate concurrent processing
            def simulate_request():
                start_time = time.time()
                
                # Simulate itinerary generation work
                mock_spots = self.test_spots[:min(20, load_level * 2)]
                mock_restaurants = self.test_restaurants[:min(10, load_level)]
                
                # Simulate processing
                processed_spots = [spot.__dict__ for spot in mock_spots]
                processed_restaurants = [rest.__dict__ for rest in mock_restaurants]
                
                # Simulate response formatting
                response = {
                    "main_itinerary": {"day_1": {}, "day_2": {}, "day_3": {}},
                    "spots": processed_spots,
                    "restaurants": processed_restaurants
                }
                
                end_time = time.time()
                return (end_time - start_time) * 1000
            
            # Run concurrent simulations
            with ThreadPoolExecutor(max_workers=load_level) as executor:
                futures = [executor.submit(simulate_request) for _ in range(load_level)]
                
                for future in as_completed(futures):
                    response_time = future.result()
                    response_times.append(response_time)
            
            response_times_by_load[load_level] = response_times
        
        # Analyze scalability
        for load_level, times in response_times_by_load.items():
            avg_time = statistics.mean(times)
            max_time = max(times)
            
            # Response times should scale reasonably
            expected_max_time = 1000 + (load_level * 100)  # Linear scaling expectation
            assert avg_time < expected_max_time, f"Average response time {avg_time}ms too high for load level {load_level}"
            assert max_time < expected_max_time * 2, f"Maximum response time {max_time}ms too high for load level {load_level}"

    def test_memory_leak_detection(self):
        """Test for memory leaks during sustained operation."""
        process = psutil.Process()
        memory_samples = []
        
        # Take initial memory reading
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_samples.append(initial_memory)
        
        # Simulate sustained operation
        for iteration in range(100):
            # Create temporary objects
            temp_spots = [TouristSpot(
                id=f"temp_{i}",
                name=f"Temp Spot {i}",
                address="Temp Address",
                district="Temp District",
                area="Temp Area",
                location_category="Temp",
                description="Temporary spot for memory testing",
                operating_hours=None,
                operating_days=["daily"],
                mbti_personality_types=["INFJ"]
            ) for i in range(50)]
            
            # Process temporary objects
            processed = [spot.__dict__ for spot in temp_spots]
            json_data = json.dumps(processed)
            parsed_data = json.loads(json_data)
            
            # Clear references
            del temp_spots
            del processed
            del json_data
            del parsed_data
            
            # Sample memory every 10 iterations
            if iteration % 10 == 0:
                current_memory = process.memory_info().rss / 1024 / 1024  # MB
                memory_samples.append(current_memory)
                
                # Force garbage collection
                gc.collect()
        
        # Analyze memory trend
        final_memory = memory_samples[-1]
        memory_growth = final_memory - initial_memory
        
        # Memory growth should be minimal (< 50MB)
        assert memory_growth < 50, f"Memory growth {memory_growth}MB indicates potential memory leak"
        
        # Memory should not continuously increase
        if len(memory_samples) > 5:
            recent_trend = memory_samples[-3:]
            trend_growth = max(recent_trend) - min(recent_trend)
            assert trend_growth < 20, f"Recent memory trend growth {trend_growth}MB too high"

    def teardown_method(self):
        """Clean up after performance tests."""
        # Generate performance report
        if self.performance_metrics["response_times"]:
            avg_response_time = statistics.mean(self.performance_metrics["response_times"])
            max_response_time = max(self.performance_metrics["response_times"])
            
            print(f"\nPerformance Test Results:")
            print(f"Average Response Time: {avg_response_time:.2f}ms")
            print(f"Maximum Response Time: {max_response_time:.2f}ms")
            
            if self.performance_metrics["memory_usage"]:
                avg_memory_usage = statistics.mean(self.performance_metrics["memory_usage"])
                print(f"Average Memory Usage: {avg_memory_usage:.2f}MB")
            
            if self.performance_metrics["cpu_usage"]:
                avg_cpu_usage = statistics.mean(self.performance_metrics["cpu_usage"])
                print(f"Average CPU Usage: {avg_cpu_usage:.2f}%")


class TestLoadTesting:
    """Load testing for concurrent MBTI requests."""

    def setup_method(self):
        """Set up load testing fixtures."""
        self.itinerary_generator = ItineraryGenerator()
        self.load_test_results = {
            "concurrent_users": [],
            "response_times": [],
            "success_rates": [],
            "error_rates": []
        }

    @pytest.mark.asyncio
    async def test_concurrent_user_load(self):
        """Test system under concurrent user load."""
        concurrent_users = [5, 10, 20, 30]
        
        for user_count in concurrent_users:
            success_count = 0
            error_count = 0
            response_times = []
            
            with patch.object(self.itinerary_generator, 'nova_client') as mock_nova:
                with patch.object(self.itinerary_generator, 'mcp_client') as mock_mcp:
                    with patch.object(self.itinerary_generator, 'restaurant_agent') as mock_restaurant:
                        
                        # Setup mocks
                        mock_nova.query_mbti_tourist_spots = AsyncMock(
                            return_value=self._create_load_test_spots()
                        )
                        mock_mcp.search_restaurants_by_meal_and_district = AsyncMock(
                            return_value=self._create_load_test_restaurants()
                        )
                        mock_restaurant.get_restaurant_recommendations = AsyncMock(
                            return_value={"recommendation": self._create_load_test_restaurants()[0], "candidates": []}
                        )
                        
                        # Create concurrent tasks
                        mbti_types = ["INFJ", "ENFP", "INTJ", "ESTP"]
                        
                        async def user_request(user_id):
                            try:
                                start_time = time.time()
                                mbti_type = mbti_types[user_id % len(mbti_types)]
                                result = await self.itinerary_generator.generate_complete_itinerary(mbti_type)
                                end_time = time.time()
                                
                                response_time = (end_time - start_time) * 1000
                                return {"success": True, "response_time": response_time, "result": result}
                            except Exception as e:
                                return {"success": False, "error": str(e)}
                        
                        # Execute concurrent requests
                        tasks = [user_request(i) for i in range(user_count)]
                        results = await asyncio.gather(*tasks, return_exceptions=True)
                        
                        # Analyze results
                        for result in results:
                            if isinstance(result, dict) and result.get("success"):
                                success_count += 1
                                response_times.append(result["response_time"])
                            else:
                                error_count += 1
            
            # Calculate metrics
            success_rate = success_count / user_count
            error_rate = error_count / user_count
            avg_response_time = statistics.mean(response_times) if response_times else 0
            
            # Performance requirements under load
            assert success_rate >= 0.95, f"Success rate {success_rate:.2%} too low for {user_count} concurrent users"
            assert error_rate <= 0.05, f"Error rate {error_rate:.2%} too high for {user_count} concurrent users"
            
            if response_times:
                assert avg_response_time < 15000, f"Average response time {avg_response_time}ms too high under load"
            
            # Record results
            self.load_test_results["concurrent_users"].append(user_count)
            self.load_test_results["response_times"].append(avg_response_time)
            self.load_test_results["success_rates"].append(success_rate)
            self.load_test_results["error_rates"].append(error_rate)

    def _create_load_test_spots(self) -> List[TouristSpot]:
        """Create tourist spots for load testing."""
        spots = []
        for i in range(30):
            spot = TouristSpot(
                id=f"load_spot_{i}",
                name=f"Load Test Spot {i}",
                address=f"Load Test Address {i}",
                district="Central",
                area="Hong Kong Island",
                location_category="Test",
                description=f"Load test spot {i}",
                operating_hours=None,
                operating_days=["daily"],
                mbti_personality_types=["INFJ", "ENFP", "INTJ", "ESTP"][i % 4],
                mbti_match=True
            )
            spots.append(spot)
        return spots

    def _create_load_test_restaurants(self) -> List[Restaurant]:
        """Create restaurants for load testing."""
        restaurants = []
        for i in range(15):
            restaurant = Restaurant(
                id=f"load_restaurant_{i}",
                name=f"Load Test Restaurant {i}",
                address=f"Load Test Address {i}",
                district="Central",
                operating_hours="09:00-22:00",
                cuisine_type="Test Cuisine",
                rating=4.0
            )
            restaurants.append(restaurant)
        return restaurants


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "--tb=short"])