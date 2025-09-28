"""
Tests for Performance Optimization

This module contains comprehensive tests for performance optimization features
including caching, connection pooling, and parallel processing.
"""

import asyncio
import pytest
import time
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta

from services.cache_service import CacheService
from services.performance_monitor import PerformanceMonitor, MetricType
from services.mcp_client_manager import MCPClientManager, MCPConnectionPool, MCPConnectionConfig
from models.restaurant_models import Restaurant, Sentiment


class TestCacheServicePerformance:
    """Test cache service performance features."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.cache_service = CacheService(default_ttl=300)
        
        self.sample_restaurants = [
            {
                "id": "rest_001",
                "name": "Test Restaurant 1",
                "district": "Central district",
                "sentiment": {"likes": 85, "dislikes": 10, "neutral": 5}
            },
            {
                "id": "rest_002",
                "name": "Test Restaurant 2", 
                "district": "Central district",
                "sentiment": {"likes": 70, "dislikes": 15, "neutral": 15}
            }
        ]
    
    def test_cache_key_generation_performance(self):
        """Test cache key generation performance."""
        start_time = time.time()
        
        # Generate many cache keys
        for i in range(1000):
            district = f"District_{i % 10}"
            meal_time = f"meal_{i % 3}"
            key = self.cache_service.generate_search_cache_key(district, meal_time)
            assert key is not None
        
        duration = time.time() - start_time
        assert duration < 1.0  # Should complete in less than 1 second
    
    def test_cache_performance_under_load(self):
        """Test cache performance under high load."""
        # Cache many entries
        for i in range(100):
            cache_key = f"test_key_{i}"
            response_data = f"test_response_{i}"
            self.cache_service.cache_response(cache_key, response_data, 300)
        
        # Measure retrieval performance
        start_time = time.time()
        
        for i in range(100):
            cache_key = f"test_key_{i}"
            result = self.cache_service.get_cached_response(cache_key)
            assert result == f"test_response_{i}"
        
        duration = time.time() - start_time
        assert duration < 0.5  # Should complete in less than 0.5 seconds
    
    def test_cache_statistics_performance(self):
        """Test cache statistics calculation performance."""
        # Add many cache entries
        for i in range(500):
            self.cache_service.cache_search_results(
                f"District_{i % 10}",
                f"meal_{i % 3}",
                self.sample_restaurants
            )
        
        # Generate cache hits and misses
        for i in range(100):
            self.cache_service.get_cached_search_results(f"District_{i % 10}", f"meal_{i % 3}")
        
        start_time = time.time()
        stats = self.cache_service.get_cache_stats()
        duration = time.time() - start_time
        
        assert duration < 0.1  # Statistics should be fast
        assert stats["total_entries"] > 0
        assert stats["cache_hits"] > 0
    
    def test_lru_cleanup_performance(self):
        """Test LRU cleanup performance."""
        # Add many cache entries
        for i in range(1000):
            cache_key = f"test_key_{i}"
            self.cache_service.cache_response(cache_key, f"response_{i}", 300)
        
        start_time = time.time()
        removed_count = self.cache_service.cleanup_least_recently_used(100)
        duration = time.time() - start_time
        
        assert duration < 1.0  # Cleanup should be fast
        assert removed_count == 900  # Should remove 900 entries
        assert len(self.cache_service._cache) == 100


class TestPerformanceMonitor:
    """Test performance monitoring functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.monitor = PerformanceMonitor(retention_hours=1)
    
    def test_metric_recording_performance(self):
        """Test performance of metric recording."""
        start_time = time.time()
        
        # Record many metrics
        for i in range(1000):
            self.monitor.record_metric(
                MetricType.RESPONSE_TIME,
                0.1 + (i % 10) * 0.01,
                {"operation": f"test_{i % 5}"}
            )
        
        duration = time.time() - start_time
        assert duration < 1.0  # Should complete in less than 1 second
    
    def test_stats_calculation_performance(self):
        """Test performance of statistics calculation."""
        # Record metrics
        for i in range(500):
            self.monitor.record_metric(
                MetricType.RESPONSE_TIME,
                0.1 + (i % 10) * 0.01,
                {"operation": "test"}
            )
        
        start_time = time.time()
        stats = self.monitor.get_stats(MetricType.RESPONSE_TIME)
        duration = time.time() - start_time
        
        assert duration < 0.1  # Statistics should be fast
        assert len(stats) > 0
    
    @pytest.mark.asyncio
    async def test_operation_measurement_performance(self):
        """Test performance of operation measurement."""
        async def dummy_operation():
            await asyncio.sleep(0.01)  # Simulate work
        
        start_time = time.time()
        
        # Measure many operations
        for i in range(100):
            async with self.monitor.measure_operation(f"test_op_{i % 5}"):
                await dummy_operation()
        
        total_duration = time.time() - start_time
        
        # Should complete reasonably fast (allowing for the sleep time)
        assert total_duration < 2.0
        
        # Check that metrics were recorded
        stats = self.monitor.get_stats(MetricType.RESPONSE_TIME)
        assert len(stats) > 0
    
    def test_mcp_performance_report_generation(self):
        """Test MCP performance report generation."""
        # Record MCP call metrics
        for i in range(100):
            server = f"server_{i % 3}"
            tool = f"tool_{i % 2}"
            duration = 0.1 + (i % 10) * 0.01
            success = i % 10 != 0  # 10% failure rate
            
            self.monitor.record_mcp_call(server, tool, duration, success)
        
        start_time = time.time()
        report = self.monitor.get_mcp_performance_report()
        duration = time.time() - start_time
        
        assert duration < 0.1  # Report generation should be fast
        assert "servers" in report
        assert "tools" in report
        assert "overall" in report


class TestConnectionPooling:
    """Test connection pooling functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = MCPConnectionConfig(
            endpoint="http://test-mcp-server:8000",
            connection_pool_size=5,
            enable_connection_pooling=True
        )
        self.pool = MCPConnectionPool(self.config, "test-server")
    
    @pytest.mark.asyncio
    async def test_connection_pool_creation_performance(self):
        """Test connection pool creation performance."""
        start_time = time.time()
        
        # Create multiple connection pools
        pools = []
        for i in range(10):
            config = MCPConnectionConfig(
                endpoint=f"http://test-server-{i}:8000",
                connection_pool_size=3
            )
            pool = MCPConnectionPool(config, f"test-server-{i}")
            pools.append(pool)
        
        duration = time.time() - start_time
        assert duration < 1.0  # Pool creation should be fast
        
        # Cleanup
        for pool in pools:
            await pool.shutdown()
    
    def test_pool_stats_performance(self):
        """Test connection pool statistics performance."""
        start_time = time.time()
        
        # Get stats many times
        for i in range(1000):
            stats = self.pool.get_pool_stats()
            assert "pool_size" in stats
        
        duration = time.time() - start_time
        assert duration < 0.1  # Stats should be very fast


class TestMCPClientManagerPerformance:
    """Test MCP client manager performance optimizations."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Mock settings
        self.mock_settings = Mock()
        self.mock_settings.mcp_client.search_mcp_endpoint = "http://search-mcp:8000"
        self.mock_settings.mcp_client.reasoning_mcp_endpoint = "http://reasoning-mcp:8000"
        self.mock_settings.mcp_client.mcp_connection_timeout = 30
        self.mock_settings.mcp_client.mcp_retry_attempts = 3
        
        with patch('services.mcp_client_manager.settings', self.mock_settings):
            self.client_manager = MCPClientManager()
    
    @pytest.mark.asyncio
    async def test_parallel_search_performance(self):
        """Test parallel search performance."""
        # Mock the search_restaurants method
        async def mock_search(district, meal_type):
            await asyncio.sleep(0.01)  # Simulate network delay
            return [
                Restaurant(
                    id=f"rest_{district}_{meal_type}",
                    name=f"Restaurant in {district}",
                    address="Test Address",
                    district=district,
                    meal_type=[meal_type],
                    sentiment=Sentiment(likes=80, dislikes=10, neutral=10),
                    price_range="$$",
                    operating_hours={"monday": ["09:00-22:00"]},
                    location_category="restaurant"
                )
            ]
        
        self.client_manager.search_restaurants = mock_search
        
        # Test sequential vs parallel performance
        search_requests = [
            ("Central district", "breakfast"),
            ("Admiralty", "lunch"),
            ("Causeway Bay", "dinner"),
            ("Tsim Sha Tsui", "breakfast"),
            ("Wan Chai", "lunch")
        ]
        
        # Sequential execution
        start_time = time.time()
        sequential_results = []
        for district, meal_type in search_requests:
            result = await self.client_manager.search_restaurants(district, meal_type)
            sequential_results.append(result)
        sequential_duration = time.time() - start_time
        
        # Parallel execution
        start_time = time.time()
        parallel_results = await self.client_manager.batch_search_restaurants(search_requests)
        parallel_duration = time.time() - start_time
        
        # Parallel should be significantly faster
        assert parallel_duration < sequential_duration * 0.8
        assert len(parallel_results) == len(search_requests)
    
    @pytest.mark.asyncio
    async def test_search_and_analyze_parallel_performance(self):
        """Test combined search and analyze parallel performance."""
        # Mock both methods
        async def mock_search(district, meal_type):
            await asyncio.sleep(0.01)
            return [
                Restaurant(
                    id=f"rest_{district}_{meal_type}",
                    name=f"Restaurant in {district}",
                    address="Test Address",
                    district=district,
                    meal_type=[meal_type],
                    sentiment=Sentiment(likes=80, dislikes=10, neutral=10),
                    price_range="$$",
                    operating_hours={"monday": ["09:00-22:00"]},
                    location_category="restaurant"
                )
            ]
        
        async def mock_analyze(restaurants, ranking_method):
            await asyncio.sleep(0.01)
            return {
                "recommendation": restaurants[0] if restaurants else None,
                "candidates": restaurants[1:] if len(restaurants) > 1 else [],
                "ranking_method": ranking_method,
                "analysis_summary": {"total_analyzed": len(restaurants)}
            }
        
        self.client_manager.search_restaurants = mock_search
        self.client_manager.analyze_restaurants = mock_analyze
        
        search_requests = [
            ("Central district", "breakfast"),
            ("Admiralty", "lunch"),
            ("Causeway Bay", "dinner")
        ]
        
        start_time = time.time()
        results = await self.client_manager.search_and_analyze_parallel(
            search_requests, "sentiment_likes"
        )
        duration = time.time() - start_time
        
        # Should complete reasonably fast
        assert duration < 0.5
        assert len(results) == len(search_requests)
        
        # Verify results structure
        for result in results:
            assert "search_criteria" in result
            assert "restaurants_found" in result
            assert "recommendation" in result
            assert "candidates" in result
    
    def test_connection_stats_performance(self):
        """Test connection statistics performance."""
        start_time = time.time()
        
        # Get stats many times
        for i in range(100):
            stats = self.client_manager.get_connection_stats()
            assert "search_mcp" in stats
            assert "reasoning_mcp" in stats
        
        duration = time.time() - start_time
        assert duration < 0.5  # Stats should be fast
    
    @pytest.mark.asyncio
    async def test_health_check_parallel_performance(self):
        """Test parallel health check performance."""
        # Mock the session context managers
        mock_session = AsyncMock()
        mock_session.list_tools.return_value = ["tool1", "tool2"]
        
        async def mock_get_session(*args, **kwargs):
            await asyncio.sleep(0.01)  # Simulate network delay
            return mock_session
        
        self.client_manager._get_mcp_session = AsyncMock(return_value=mock_session)
        
        start_time = time.time()
        health_status = await self.client_manager.health_check()
        duration = time.time() - start_time
        
        # Should complete faster than sequential checks
        assert duration < 0.1  # Parallel execution should be fast
        assert "search_mcp" in health_status
        assert "reasoning_mcp" in health_status


class TestIntegratedPerformanceOptimization:
    """Test integrated performance optimization features."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.cache_service = CacheService(default_ttl=300)
        self.performance_monitor = PerformanceMonitor(retention_hours=1)
    
    @pytest.mark.asyncio
    async def test_cache_and_monitor_integration(self):
        """Test integration between cache and performance monitoring."""
        # Simulate cache operations with monitoring
        for i in range(50):
            district = f"District_{i % 5}"
            meal_time = f"meal_{i % 3}"
            
            # Check cache first
            start_time = time.time()
            cached_result = self.cache_service.get_cached_search_results(district, meal_time)
            cache_duration = time.time() - start_time
            
            if cached_result:
                # Cache hit
                self.performance_monitor.record_cache_performance(True, "search")
                self.performance_monitor.record_metric(
                    MetricType.RESPONSE_TIME,
                    cache_duration,
                    {"operation": "cache_hit", "type": "search"}
                )
            else:
                # Cache miss - simulate MCP call
                self.performance_monitor.record_cache_performance(False, "search")
                
                # Simulate MCP call duration
                mcp_duration = 0.1 + (i % 10) * 0.01
                self.performance_monitor.record_mcp_call(
                    "restaurant-search-mcp",
                    "search_restaurants_combined",
                    mcp_duration,
                    True
                )
                
                # Cache the result
                sample_restaurants = [{"id": f"rest_{i}", "name": f"Restaurant {i}"}]
                self.cache_service.cache_search_results(
                    district, meal_time, sample_restaurants
                )
        
        # Verify performance metrics
        cache_stats = self.performance_monitor.get_stats(MetricType.CACHE_HIT_RATE)
        response_stats = self.performance_monitor.get_stats(MetricType.RESPONSE_TIME)
        mcp_stats = self.performance_monitor.get_stats(MetricType.MCP_CALL_DURATION)
        
        assert len(cache_stats) > 0
        assert len(response_stats) > 0
        assert len(mcp_stats) > 0
        
        # Verify cache effectiveness
        cache_service_stats = self.cache_service.get_cache_stats()
        assert cache_service_stats["cache_hits"] > 0
        assert cache_service_stats["hit_rate_percentage"] > 0
    
    def test_performance_optimization_summary(self):
        """Test comprehensive performance optimization summary."""
        # Simulate various operations
        for i in range(100):
            # Cache operations
            self.cache_service.cache_response(f"key_{i}", f"response_{i}", 300)
            if i % 2 == 0:
                self.cache_service.get_cached_response(f"key_{i}")
            
            # Performance metrics
            self.performance_monitor.record_metric(
                MetricType.RESPONSE_TIME,
                0.1 + (i % 10) * 0.01,
                {"operation": f"op_{i % 5}"}
            )
            
            self.performance_monitor.record_mcp_call(
                f"server_{i % 3}",
                f"tool_{i % 2}",
                0.05 + (i % 5) * 0.01,
                i % 10 != 0  # 10% failure rate
            )
        
        # Get comprehensive summary
        cache_stats = self.cache_service.get_cache_stats()
        cache_efficiency = self.cache_service.get_cache_efficiency_metrics()
        performance_summary = self.performance_monitor.get_performance_summary()
        mcp_report = self.performance_monitor.get_mcp_performance_report()
        
        # Verify all summaries contain expected data
        assert cache_stats["total_entries"] > 0
        assert cache_stats["hit_rate_percentage"] > 0
        
        assert cache_efficiency["hit_rate"] > 0
        assert cache_efficiency["total_requests"] > 0
        
        assert performance_summary["total_metrics_collected"] > 0
        assert performance_summary["recent_error_rate"] >= 0
        
        assert mcp_report["overall"]["total_calls"] > 0
        assert len(mcp_report["servers"]) > 0
        assert len(mcp_report["tools"]) > 0