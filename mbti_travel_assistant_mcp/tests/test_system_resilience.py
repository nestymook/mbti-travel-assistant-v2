"""
Tests for System Resilience Service

This module tests the comprehensive system resilience features including
graceful degradation, caching, error handling, and monitoring.
"""

import pytest
import asyncio
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch

from services.system_resilience import (
    SystemResilienceService,
    ServiceStatus,
    CacheStrategy,
    DegradationConfig,
    CacheConfig,
    ServiceHealth,
    CacheEntry
)


class TestSystemResilienceService:
    """Test cases for SystemResilienceService."""
    
    @pytest.fixture
    def resilience_service(self):
        """Create a SystemResilienceService instance for testing."""
        degradation_config = DegradationConfig(
            error_threshold=3,
            error_window_minutes=5,
            recovery_threshold=2,
            max_degradation_time_minutes=10,
            enable_circuit_breaker=True,
            circuit_breaker_timeout_seconds=30
        )
        
        cache_config = CacheConfig(
            max_size_mb=10,
            default_ttl_seconds=60,
            cleanup_interval_seconds=30,
            strategy=CacheStrategy.HYBRID,
            enable_persistence=False  # Disable for tests
        )
        
        return SystemResilienceService(
            degradation_config=degradation_config,
            cache_config=cache_config
        )
    
    @pytest.mark.asyncio
    async def test_successful_operation_execution(self, resilience_service):
        """Test successful operation execution with caching."""
        # Mock operation
        async def mock_operation(value):
            return f"result_{value}"
        
        # Execute operation
        result = await resilience_service.execute_with_resilience(
            service_name="test_service",
            operation=mock_operation,
            cache_key="test_key",
            cache_ttl=60,
            "test_value"
        )
        
        assert result == "result_test_value"
        
        # Check that result was cached
        cached_result = await resilience_service.get_cached_data("test_key")
        assert cached_result == "result_test_value"
        
        # Check service health
        health = resilience_service.get_system_health()
        assert "test_service" in health["services"]
        assert health["services"]["test_service"]["status"] == ServiceStatus.HEALTHY.value
    
    @pytest.mark.asyncio
    async def test_cache_hit(self, resilience_service):
        """Test cache hit scenario."""
        # Cache some data
        await resilience_service.cache_data("test_key", "cached_value", 60)
        
        # Mock operation that should not be called
        mock_operation = Mock()
        
        # Execute operation - should return cached value
        result = await resilience_service.execute_with_resilience(
            service_name="test_service",
            operation=mock_operation,
            cache_key="test_key"
        )
        
        assert result == "cached_value"
        mock_operation.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_operation_failure_with_fallback(self, resilience_service):
        """Test operation failure with successful fallback."""
        # Mock failing primary operation
        async def failing_operation():
            raise Exception("Primary operation failed")
        
        # Mock successful fallback operation
        async def fallback_operation():
            return "fallback_result"
        
        # Execute operation
        result = await resilience_service.execute_with_resilience(
            service_name="test_service",
            operation=failing_operation,
            fallback_operation=fallback_operation
        )
        
        assert result == "fallback_result"
        
        # Check that error was recorded
        health = resilience_service.get_system_health()
        assert health["services"]["test_service"]["error_count"] > 0
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_functionality(self, resilience_service):
        """Test circuit breaker opens after repeated failures."""
        # Mock failing operation
        async def failing_operation():
            raise Exception("Service unavailable")
        
        # Mock fallback operation
        async def fallback_operation():
            return "fallback_result"
        
        # Execute multiple failing operations to trigger circuit breaker
        for i in range(5):
            try:
                await resilience_service.execute_with_resilience(
                    service_name="test_service",
                    operation=failing_operation,
                    fallback_operation=fallback_operation
                )
            except Exception:
                pass  # Expected failures
        
        # Check that circuit breaker is open
        health = resilience_service.get_system_health()
        assert len(health["circuit_breakers"]) > 0
        
        # Next operation should use fallback immediately
        result = await resilience_service.execute_with_resilience(
            service_name="test_service",
            operation=failing_operation,
            fallback_operation=fallback_operation
        )
        
        assert result == "fallback_result"
    
    @pytest.mark.asyncio
    async def test_cache_expiration(self, resilience_service):
        """Test cache entry expiration."""
        # Cache data with short TTL
        await resilience_service.cache_data("test_key", "cached_value", 1)
        
        # Verify data is cached
        result = await resilience_service.get_cached_data("test_key")
        assert result == "cached_value"
        
        # Wait for expiration
        await asyncio.sleep(2)
        
        # Verify data is expired
        result = await resilience_service.get_cached_data("test_key")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_cache_eviction_lru(self, resilience_service):
        """Test LRU cache eviction."""
        # Fill cache beyond capacity
        for i in range(20):
            await resilience_service.cache_data(f"key_{i}", f"value_{i}", 300)
        
        # Access some entries to make them recently used
        await resilience_service.get_cached_data("key_15")
        await resilience_service.get_cached_data("key_16")
        await resilience_service.get_cached_data("key_17")
        
        # Force eviction by adding more data
        await resilience_service._evict_cache_entries()
        
        # Recently accessed entries should still be cached
        assert await resilience_service.get_cached_data("key_15") == "value_15"
        assert await resilience_service.get_cached_data("key_16") == "value_16"
        assert await resilience_service.get_cached_data("key_17") == "value_17"
    
    @pytest.mark.asyncio
    async def test_stale_cache_fallback(self, resilience_service):
        """Test fallback to stale cached data."""
        # Cache data with short TTL
        await resilience_service.cache_data("test_key", "stale_value", 1)
        
        # Wait for expiration
        await asyncio.sleep(2)
        
        # Mock failing operation
        async def failing_operation():
            raise Exception("Service unavailable")
        
        # Execute operation - should return stale cached data as fallback
        result = await resilience_service.execute_with_resilience(
            service_name="test_service",
            operation=failing_operation,
            cache_key="test_key"
        )
        
        assert result == "stale_value"
    
    @pytest.mark.asyncio
    async def test_service_degradation_and_recovery(self, resilience_service):
        """Test service degradation and recovery cycle."""
        # Start background tasks
        await resilience_service.start()
        
        try:
            # Simulate multiple errors to trigger degradation
            for i in range(4):
                await resilience_service._record_error(
                    "test_service",
                    Exception(f"Error {i}"),
                    100.0
                )
            
            # Check service is degraded
            health = resilience_service.get_system_health()
            service_health = health["services"]["test_service"]
            assert service_health["status"] in [ServiceStatus.DEGRADED.value, ServiceStatus.CRITICAL.value]
            
            # Simulate successful operations for recovery
            for i in range(5):
                await resilience_service._record_success("test_service", 50.0)
            
            # Service should recover
            health = resilience_service.get_system_health()
            service_health = health["services"]["test_service"]
            assert service_health["status"] == ServiceStatus.HEALTHY.value
            
        finally:
            await resilience_service.stop()
    
    @pytest.mark.asyncio
    async def test_operation_timeout(self, resilience_service):
        """Test operation timeout handling."""
        # Mock slow operation
        async def slow_operation():
            await asyncio.sleep(35)  # Longer than timeout
            return "slow_result"
        
        # Mock fallback operation
        async def fallback_operation():
            return "timeout_fallback"
        
        # Execute operation - should timeout and use fallback
        result = await resilience_service.execute_with_resilience(
            service_name="test_service",
            operation=slow_operation,
            fallback_operation=fallback_operation
        )
        
        assert result == "timeout_fallback"
    
    def test_cache_stats(self, resilience_service):
        """Test cache statistics calculation."""
        # Get initial stats
        stats = resilience_service.get_cache_stats()
        assert stats["cached_queries"] == 0
        assert stats["total_cached_results"] == 0
        
        # Add some cache entries
        asyncio.run(resilience_service.cache_data("key1", "value1", 60))
        asyncio.run(resilience_service.cache_data("key2", "value2", 60))
        
        # Check updated stats
        stats = resilience_service.get_cache_stats()
        assert stats["cached_queries"] == 2
        assert stats["total_cached_results"] == 2
    
    def test_system_health_reporting(self, resilience_service):
        """Test comprehensive system health reporting."""
        # Add some test data
        asyncio.run(resilience_service._record_error(
            "service1", Exception("Test error"), 100.0
        ))
        asyncio.run(resilience_service._record_success("service1", 50.0))
        asyncio.run(resilience_service.cache_data("test_key", "test_value", 60))
        
        # Get health report
        health = resilience_service.get_system_health()
        
        assert "services" in health
        assert "circuit_breakers" in health
        assert "cache_stats" in health
        assert "error_summary" in health
        
        # Check service health details
        assert "service1" in health["services"]
        service_health = health["services"]["service1"]
        assert "status" in service_health
        assert "error_rate" in service_health
        assert "uptime_percentage" in service_health
    
    def test_performance_metrics(self, resilience_service):
        """Test performance metrics collection."""
        # Add some performance data
        asyncio.run(resilience_service._record_success("service1", 100.0))
        asyncio.run(resilience_service._record_success("service1", 200.0))
        asyncio.run(resilience_service._record_success("service1", 150.0))
        
        # Get performance metrics
        metrics = resilience_service.get_performance_metrics()
        
        assert "service1" in metrics
        service_metrics = metrics["service1"]
        assert service_metrics["avg_response_time_ms"] == 150.0
        assert service_metrics["min_response_time_ms"] == 100.0
        assert service_metrics["max_response_time_ms"] == 200.0
        assert service_metrics["total_operations"] == 3
    
    @pytest.mark.asyncio
    async def test_empty_result_fallback(self, resilience_service):
        """Test empty result fallback for different service types."""
        # Mock failing operation
        async def failing_operation():
            raise Exception("Service unavailable")
        
        # Test tourist spots service
        result = await resilience_service.execute_with_resilience(
            service_name="tourist_spots_service",
            operation=failing_operation
        )
        assert result == []
        
        # Test restaurants service
        result = await resilience_service.execute_with_resilience(
            service_name="restaurants_service",
            operation=failing_operation
        )
        assert result == []
        
        # Test itinerary service
        result = await resilience_service.execute_with_resilience(
            service_name="itinerary_service",
            operation=failing_operation
        )
        assert isinstance(result, dict)
        assert "main_itinerary" in result
        assert result["fallback_used"] is True
    
    @pytest.mark.asyncio
    async def test_background_tasks_lifecycle(self, resilience_service):
        """Test background tasks start and stop correctly."""
        # Start service
        await resilience_service.start()
        
        assert resilience_service._cleanup_task is not None
        assert resilience_service._monitoring_task is not None
        assert not resilience_service._cleanup_task.done()
        assert not resilience_service._monitoring_task.done()
        
        # Stop service
        await resilience_service.stop()
        
        assert resilience_service._cleanup_task.done()
        assert resilience_service._monitoring_task.done()


class TestCacheEntry:
    """Test cases for CacheEntry data class."""
    
    def test_cache_entry_creation(self):
        """Test CacheEntry creation and attributes."""
        now = datetime.now()
        entry = CacheEntry(
            key="test_key",
            data="test_data",
            created_at=now,
            last_accessed=now,
            access_count=1,
            ttl_seconds=60,
            size_bytes=100
        )
        
        assert entry.key == "test_key"
        assert entry.data == "test_data"
        assert entry.created_at == now
        assert entry.last_accessed == now
        assert entry.access_count == 1
        assert entry.ttl_seconds == 60
        assert entry.size_bytes == 100


class TestServiceHealth:
    """Test cases for ServiceHealth data class."""
    
    def test_service_health_creation(self):
        """Test ServiceHealth creation and attributes."""
        now = datetime.now()
        health = ServiceHealth(
            service_name="test_service",
            status=ServiceStatus.HEALTHY,
            last_check=now,
            error_count=0,
            success_count=10,
            response_time_ms=100.0,
            error_rate=0.0,
            uptime_percentage=100.0,
            last_error=None
        )
        
        assert health.service_name == "test_service"
        assert health.status == ServiceStatus.HEALTHY
        assert health.last_check == now
        assert health.error_count == 0
        assert health.success_count == 10
        assert health.response_time_ms == 100.0
        assert health.error_rate == 0.0
        assert health.uptime_percentage == 100.0
        assert health.last_error is None


class TestDegradationConfig:
    """Test cases for DegradationConfig."""
    
    def test_default_config(self):
        """Test default degradation configuration."""
        config = DegradationConfig()
        
        assert config.error_threshold == 5
        assert config.error_window_minutes == 5
        assert config.recovery_threshold == 3
        assert config.max_degradation_time_minutes == 30
        assert config.enable_circuit_breaker is True
        assert config.circuit_breaker_timeout_seconds == 60
    
    def test_custom_config(self):
        """Test custom degradation configuration."""
        config = DegradationConfig(
            error_threshold=10,
            error_window_minutes=10,
            recovery_threshold=5,
            max_degradation_time_minutes=60,
            enable_circuit_breaker=False,
            circuit_breaker_timeout_seconds=120
        )
        
        assert config.error_threshold == 10
        assert config.error_window_minutes == 10
        assert config.recovery_threshold == 5
        assert config.max_degradation_time_minutes == 60
        assert config.enable_circuit_breaker is False
        assert config.circuit_breaker_timeout_seconds == 120


class TestCacheConfig:
    """Test cases for CacheConfig."""
    
    def test_default_config(self):
        """Test default cache configuration."""
        config = CacheConfig()
        
        assert config.max_size_mb == 100
        assert config.default_ttl_seconds == 300
        assert config.cleanup_interval_seconds == 60
        assert config.strategy == CacheStrategy.HYBRID
        assert config.enable_persistence is True
        assert config.persistence_path == "cache"
    
    def test_custom_config(self):
        """Test custom cache configuration."""
        config = CacheConfig(
            max_size_mb=50,
            default_ttl_seconds=600,
            cleanup_interval_seconds=120,
            strategy=CacheStrategy.LRU,
            enable_persistence=False,
            persistence_path="custom_cache"
        )
        
        assert config.max_size_mb == 50
        assert config.default_ttl_seconds == 600
        assert config.cleanup_interval_seconds == 120
        assert config.strategy == CacheStrategy.LRU
        assert config.enable_persistence is False
        assert config.persistence_path == "custom_cache"


if __name__ == "__main__":
    pytest.main([__file__])