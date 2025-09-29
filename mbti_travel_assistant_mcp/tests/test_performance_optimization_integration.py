"""
Test Performance Optimization Integration

Tests for the enhanced caching system, connection pooling, and parallel processing
capabilities implemented for task 11.
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta

from services.cache_service import CacheService
from services.connection_pool_manager import ConnectionPoolManager, PooledConnection, ConnectionState
from services.performance_monitor import PerformanceMonitor, MetricType
from services.mcp_client_manager import MCPClientManager


class TestCacheServiceEnhancements:
    """Test enhanced cache service with MBTI personality caching"""
    
    @pytest.fixture
    def cache_service(self):
        """Create cache service instance for testing"""
        return CacheService(
            default_ttl=1800,
            mbti_ttl=3600,
            tourist_spots_ttl=7200
        )
    
    def test_mbti_cache_key_generation(self, cache_service):
        """Test MBTI personality cache key generation"""
        key1 = cache_service.generate_mbti_cache_key("INFJ")
        key2 = cache_service.generate_mbti_cache_key("infj")  # Case insensitive
        key3 = cache_service.generate_mbti_cache_key("ENFP")
        
        # Same personality should generate same key (case insensitive)
        assert key1 == key2
        # Different personalities should generate different keys
        assert key1 != key3
        # Keys should be consistent
        assert len(key1) == 32  # MD5 hash length
    
    def test_tourist_spots_cache_key_generation(self, cache_service):
        """Test tourist spots cache key generation"""
        key1 = cache_service.generate_tourist_spots_cache_key("INFJ", "default")
        key2 = cache_service.generate_tourist_spots_cache_key("INFJ", "fallback")
        key3 = cache_service.generate_tourist_spots_cache_key("ENFP", "default")
        
        # Same personality, different query types should be different
        assert key1 != key2
        # Different personalities should be different
        assert key1 != key3
        # Keys should be consistent
        assert len(key1) == 32
    
    def test_cache_mbti_personality_results(self, cache_service):
        """Test caching MBTI personality results"""
        mbti_personality = "INFJ"
        tourist_spots = [
            {"id": "spot1", "name": "Museum", "district": "Central"},
            {"id": "spot2", "name": "Park", "district": "Admiralty"}
        ]
        query_metadata = {"query_time": "2025-01-01T12:00:00Z"}
        
        # Cache the results
        cache_key = cache_service.cache_mbti_personality_results(
            mbti_personality, tourist_spots, query_metadata
        )
        
        # Retrieve cached results
        cached_result = cache_service.get_cached_mbti_personality_results(mbti_personality)
        
        assert cached_result is not None
        assert cached_result["mbti_personality"] == "INFJ"
        assert cached_result["total_spots"] == 2
        assert cached_result["tourist_spots"] == tourist_spots
        assert cached_result["query_metadata"] == query_metadata
        assert cached_result["cache_type"] == "mbti_personality_results"
    
    def test_cache_tourist_spots_data(self, cache_service):
        """Test caching tourist spots data"""
        mbti_personality = "ENFP"
        tourist_spots = [
            {"id": "spot3", "name": "Market", "district": "Causeway Bay"},
            {"id": "spot4", "name": "Beach", "district": "Repulse Bay"}
        ]
        processing_metadata = {"processing_time": 2.5}
        
        # Cache the data
        cache_key = cache_service.cache_tourist_spots_data(
            mbti_personality, tourist_spots, "default", processing_metadata
        )
        
        # Retrieve cached data
        cached_result = cache_service.get_cached_tourist_spots_data(mbti_personality, "default")
        
        assert cached_result is not None
        assert cached_result["mbti_personality"] == "ENFP"
        assert cached_result["query_type"] == "default"
        assert cached_result["total_spots"] == 2
        assert cached_result["tourist_spots"] == tourist_spots
        assert cached_result["processing_metadata"] == processing_metadata
    
    def test_cache_complete_itinerary(self, cache_service):
        """Test caching complete itinerary responses"""
        mbti_personality = "INTJ"
        request_params = {"user_id": "test123", "preferences": ["museums", "quiet"]}
        itinerary_response = {
            "main_itinerary": {"day_1": {}, "day_2": {}, "day_3": {}},
            "candidate_tourist_spots": {},
            "candidate_restaurants": {},
            "metadata": {"generation_time": "2025-01-01T12:00:00Z"}
        }
        
        # Cache the itinerary
        cache_key = cache_service.cache_complete_itinerary(
            mbti_personality, request_params, itinerary_response
        )
        
        # Retrieve cached itinerary
        cached_result = cache_service.get_cached_complete_itinerary(
            mbti_personality, request_params
        )
        
        assert cached_result is not None
        assert cached_result == itinerary_response
    
    def test_cache_invalidation_by_mbti_type(self, cache_service):
        """Test cache invalidation for specific MBTI types"""
        # Cache data for multiple MBTI types
        cache_service.cache_mbti_personality_results("INFJ", [{"id": "spot1"}])
        cache_service.cache_mbti_personality_results("ENFP", [{"id": "spot2"}])
        cache_service.cache_tourist_spots_data("INFJ", [{"id": "spot3"}])
        
        # Invalidate only INFJ caches
        invalidated_mbti = cache_service.invalidate_mbti_cache("INFJ")
        invalidated_spots = cache_service.invalidate_tourist_spots_cache("INFJ")
        
        # INFJ caches should be invalidated
        assert cache_service.get_cached_mbti_personality_results("INFJ") is None
        assert cache_service.get_cached_tourist_spots_data("INFJ") is None
        
        # ENFP cache should still exist
        assert cache_service.get_cached_mbti_personality_results("ENFP") is not None
    
    def test_enhanced_cache_stats(self, cache_service):
        """Test enhanced cache statistics with new cache types"""
        # Add various cache entries
        cache_service.cache_mbti_personality_results("INFJ", [{"id": "spot1"}])
        cache_service.cache_tourist_spots_data("ENFP", [{"id": "spot2"}])
        cache_service.cache_search_results("Central", "lunch", [{"id": "rest1"}])
        
        stats = cache_service.get_cache_stats()
        
        assert "mbti_cache_entries" in stats
        assert "tourist_spots_cache_entries" in stats
        assert "search_cache_entries" in stats
        assert "ttl_config" in stats
        assert stats["ttl_config"]["mbti_ttl_seconds"] == 3600
        assert stats["ttl_config"]["tourist_spots_ttl_seconds"] == 7200


class TestConnectionPoolManager:
    """Test connection pool manager functionality"""
    
    @pytest.fixture
    def pool_manager(self):
        """Create connection pool manager for testing"""
        return ConnectionPoolManager(
            max_connections_per_server=5,
            max_idle_connections=2,
            connection_timeout=10
        )
    
    @pytest.mark.asyncio
    async def test_connection_pool_creation(self, pool_manager):
        """Test connection pool creation and management"""
        server_endpoint = "http://test-server:8080"
        
        # Mock the streamablehttp_client
        with patch('services.connection_pool_manager.streamablehttp_client') as mock_client:
            mock_session = AsyncMock()
            mock_client.return_value.__aenter__.return_value = (
                AsyncMock(), AsyncMock(), AsyncMock()
            )
            
            # Create a connection
            connection = await pool_manager._create_connection(server_endpoint)
            
            assert connection.server_endpoint == server_endpoint
            assert connection.state == ConnectionState.IDLE
            assert isinstance(connection.created_at, datetime)
    
    @pytest.mark.asyncio
    async def test_parallel_operations_execution(self, pool_manager):
        """Test parallel operations execution"""
        operations = [
            {
                "server_endpoint": "http://server1:8080",
                "tool_name": "search_restaurants",
                "parameters": {"district": "Central"}
            },
            {
                "server_endpoint": "http://server2:8080", 
                "tool_name": "recommend_restaurants",
                "parameters": {"restaurants": []}
            }
        ]
        
        # Mock the connection manager
        with patch.object(pool_manager, 'get_connection') as mock_get_conn:
            mock_session = AsyncMock()
            mock_session.call_tool.return_value = {"result": "success"}
            mock_get_conn.return_value.__aenter__.return_value = mock_session
            
            results = await pool_manager.execute_parallel_operations(operations, max_concurrent=2)
            
            assert len(results) == 2
            assert all(result["result"] == "success" for result in results if not isinstance(result, Exception))
    
    def test_pool_statistics(self, pool_manager):
        """Test connection pool statistics"""
        stats = pool_manager.get_pool_stats()
        
        assert "global_stats" in stats
        assert "pool_stats" in stats
        assert "configuration" in stats
        
        global_stats = stats["global_stats"]
        assert "total_connections_created" in global_stats
        assert "active_connections" in global_stats
        assert "idle_connections" in global_stats
    
    @pytest.mark.asyncio
    async def test_connection_warmup(self, pool_manager):
        """Test connection pool warmup functionality"""
        server_endpoints = ["http://server1:8080", "http://server2:8080"]
        
        with patch.object(pool_manager, '_create_connection') as mock_create:
            mock_connection = PooledConnection(
                connection_id="test_conn",
                server_endpoint="http://server1:8080",
                session=AsyncMock(),
                state=ConnectionState.IDLE,
                created_at=datetime.now(),
                last_used=datetime.now()
            )
            mock_create.return_value = mock_connection
            
            await pool_manager.warm_up_connections(server_endpoints, connections_per_server=1)
            
            # Should have created connections for both servers
            assert mock_create.call_count == 2


class TestPerformanceMonitorEnhancements:
    """Test enhanced performance monitor functionality"""
    
    @pytest.fixture
    def performance_monitor(self):
        """Create performance monitor for testing"""
        return PerformanceMonitor(retention_hours=1)
    
    @pytest.mark.asyncio
    async def test_parallel_operations_measurement(self, performance_monitor):
        """Test measurement of parallel operations"""
        async def mock_operation():
            await asyncio.sleep(0.1)
            return "success"
        
        async def failing_operation():
            await asyncio.sleep(0.05)
            raise ValueError("Test error")
        
        operations = [mock_operation, mock_operation, failing_operation]
        
        results = await performance_monitor.measure_parallel_operations(
            operations, "test_parallel_ops", max_concurrent=2
        )
        
        assert len(results) == 3
        successful_results = [r for r in results if not isinstance(r, Exception)]
        failed_results = [r for r in results if isinstance(r, Exception)]
        
        assert len(successful_results) == 2
        assert len(failed_results) == 1
        
        # Check that metrics were recorded
        stats = performance_monitor.get_stats(MetricType.RESPONSE_TIME)
        assert len(stats) > 0
    
    def test_connection_pool_metrics_recording(self, performance_monitor):
        """Test recording of connection pool metrics"""
        pool_stats = {
            "global_stats": {
                "active_connections": 5,
                "idle_connections": 3,
                "failed_connections": 1
            },
            "pool_stats": {
                "server1": {
                    "active_connections": 2,
                    "idle_connections": 1,
                    "failed_connections": 0
                }
            }
        }
        
        performance_monitor.record_connection_pool_metrics(pool_stats)
        
        # Check that connection metrics were recorded
        connection_stats = performance_monitor.get_stats(MetricType.CONNECTION_COUNT)
        assert len(connection_stats) > 0
    
    def test_performance_optimization_recommendations(self, performance_monitor):
        """Test performance optimization recommendations"""
        # Record some slow operations
        performance_monitor.record_metric(MetricType.RESPONSE_TIME, 12.0, {"operation": "slow_op"})
        performance_monitor.record_metric(MetricType.ERROR_RATE, 0.3, {"operation": "failing_op"})
        performance_monitor.record_metric(MetricType.CACHE_HIT_RATE, 0.2, {"operation": "cache_op"})
        
        recommendations = performance_monitor.get_performance_optimization_recommendations()
        
        assert len(recommendations) > 0
        
        # Should have recommendations for slow operations, high error rates, and low cache hit rates
        recommendation_types = [r["type"] for r in recommendations]
        assert "performance" in recommendation_types
        assert "reliability" in recommendation_types
        assert "caching" in recommendation_types


class TestMCPClientManagerEnhancements:
    """Test enhanced MCP client manager with performance optimizations"""
    
    @pytest.fixture
    def mcp_manager(self):
        """Create MCP client manager for testing"""
        with patch('services.mcp_client_manager.settings') as mock_settings:
            mock_settings.mcp_client.search_mcp_endpoint = "http://search-server:8080"
            mock_settings.mcp_client.reasoning_mcp_endpoint = "http://reasoning-server:8080"
            mock_settings.mcp_client.mcp_connection_timeout = 30
            mock_settings.mcp_client.mcp_retry_attempts = 3
            
            return MCPClientManager()
    
    @pytest.mark.asyncio
    async def test_parallel_restaurant_search(self, mcp_manager):
        """Test parallel restaurant search functionality"""
        search_requests = [
            {"parameters": {"districts": ["Central"], "meal_types": ["lunch"]}},
            {"parameters": {"districts": ["Admiralty"], "meal_types": ["dinner"]}}
        ]
        
        with patch.object(mcp_manager, '_execute_search_operation') as mock_execute:
            mock_execute.return_value = {
                "restaurants": [{"id": "rest1", "name": "Test Restaurant"}]
            }
            
            with patch.object(mcp_manager, '_parse_restaurant_search_response') as mock_parse:
                mock_parse.return_value = [{"id": "rest1", "name": "Test Restaurant"}]
                
                results = await mcp_manager.search_restaurants_parallel(search_requests, max_concurrent=2)
                
                assert len(results) == 2
                assert all(isinstance(result, list) for result in results)
    
    @pytest.mark.asyncio
    async def test_parallel_restaurant_recommendations(self, mcp_manager):
        """Test parallel restaurant recommendations functionality"""
        recommendation_requests = [
            {"parameters": {"restaurants": [{"id": "rest1"}], "ranking_method": "sentiment_likes"}},
            {"parameters": {"restaurants": [{"id": "rest2"}], "ranking_method": "combined_sentiment"}}
        ]
        
        with patch.object(mcp_manager, '_execute_recommendation_operation') as mock_execute:
            mock_execute.return_value = {
                "recommendation": {"id": "rest1", "name": "Recommended Restaurant"},
                "candidates": []
            }
            
            with patch.object(mcp_manager, '_parse_recommendation_response') as mock_parse:
                mock_parse.return_value = {
                    "recommendation": {"id": "rest1", "name": "Recommended Restaurant"},
                    "candidates": []
                }
                
                results = await mcp_manager.get_restaurant_recommendations_parallel(
                    recommendation_requests, max_concurrent=2
                )
                
                assert len(results) == 2
                assert all(isinstance(result, dict) for result in results)
    
    def test_comprehensive_performance_metrics(self, mcp_manager):
        """Test comprehensive performance metrics collection"""
        with patch('services.mcp_client_manager.connection_pool_manager') as mock_pool_manager:
            mock_pool_manager.get_pool_stats.return_value = {
                "global_stats": {"active_connections": 5},
                "pool_stats": {}
            }
            
            with patch('services.mcp_client_manager.performance_monitor') as mock_monitor:
                mock_monitor.get_mcp_performance_report.return_value = {"servers": {}}
                mock_monitor.get_performance_optimization_recommendations.return_value = []
                mock_monitor.get_system_metrics.return_value = {"cpu_percent": 50.0}
                
                metrics = mcp_manager.get_comprehensive_performance_metrics()
                
                assert "connection_pools" in metrics
                assert "mcp_performance" in metrics
                assert "local_stats" in metrics
                assert "performance_recommendations" in metrics
                assert "system_metrics" in metrics
                
                # Check local stats structure
                local_stats = metrics["local_stats"]
                assert "search_mcp" in local_stats
                assert "reasoning_mcp" in local_stats
    
    @pytest.mark.asyncio
    async def test_performance_optimization(self, mcp_manager):
        """Test performance optimization functionality"""
        with patch('services.mcp_client_manager.connection_pool_manager') as mock_pool_manager:
            mock_pool_manager._cleanup_expired_connections = AsyncMock()
            mock_pool_manager.get_pool_stats.return_value = {
                "global_stats": {"idle_connections": 0}
            }
            
            with patch.object(mcp_manager, '_warm_up_connections') as mock_warmup:
                mock_warmup.return_value = None
                
                with patch.object(mcp_manager, 'get_comprehensive_performance_metrics') as mock_metrics:
                    mock_metrics.return_value = {"test": "metrics"}
                    
                    results = await mcp_manager.optimize_performance()
                    
                    assert "actions_taken" in results
                    assert "recommendations" in results
                    assert "before_metrics" in results
                    assert "after_metrics" in results
                    
                    # Should have taken some optimization actions
                    assert len(results["actions_taken"]) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])