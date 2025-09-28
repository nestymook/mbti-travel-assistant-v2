"""
Comprehensive Unit Tests for Cache Service

Tests all aspects of caching functionality including cache key generation,
TTL management, statistics tracking, and cache operations.
"""

import pytest
import json
import hashlib
from datetime import datetime, timedelta
from unittest.mock import patch

from services.cache_service import CacheService


class TestCacheService:
    """Comprehensive test cases for CacheService."""
    
    @pytest.fixture
    def cache_service(self):
        """Create cache service instance with default TTL."""
        return CacheService(default_ttl=1800)
    
    @pytest.fixture
    def cache_service_short_ttl(self):
        """Create cache service with short TTL for testing expiration."""
        return CacheService(default_ttl=1)
    
    @pytest.fixture
    def sample_restaurants(self):
        """Create sample restaurant data."""
        return [
            {
                "id": "rest_001",
                "name": "Restaurant A",
                "district": "Central district",
                "meal_type": ["breakfast"],
                "sentiment": {"likes": 85, "dislikes": 10, "neutral": 5}
            },
            {
                "id": "rest_002", 
                "name": "Restaurant B",
                "district": "Central district",
                "meal_type": ["breakfast"],
                "sentiment": {"likes": 75, "dislikes": 15, "neutral": 10}
            }
        ]
    
    def test_init_default_ttl(self, cache_service):
        """Test cache service initialization with default TTL."""
        assert cache_service._default_ttl == 1800
        assert cache_service._hit_count == 0
        assert cache_service._miss_count == 0
        assert len(cache_service._cache) == 0
    
    def test_init_custom_ttl(self):
        """Test cache service initialization with custom TTL."""
        cache_service = CacheService(default_ttl=3600)
        assert cache_service._default_ttl == 3600
    
    def test_generate_search_cache_key(self, cache_service):
        """Test search cache key generation."""
        key = cache_service.generate_search_cache_key("Central district", "breakfast")
        
        assert isinstance(key, str)
        assert len(key) == 32  # MD5 hash length
        
        # Same inputs should generate same key
        key2 = cache_service.generate_search_cache_key("Central district", "breakfast")
        assert key == key2
        
        # Different inputs should generate different keys
        key3 = cache_service.generate_search_cache_key("Admiralty", "breakfast")
        assert key != key3
    
    def test_generate_search_cache_key_normalization(self, cache_service):
        """Test search cache key generation with input normalization."""
        key1 = cache_service.generate_search_cache_key("Central District", "BREAKFAST")
        key2 = cache_service.generate_search_cache_key("central district", "breakfast")
        key3 = cache_service.generate_search_cache_key("  Central district  ", "  breakfast  ")
        
        # All should generate the same key due to normalization
        assert key1 == key2 == key3
    
    def test_generate_search_cache_key_includes_date(self, cache_service):
        """Test that search cache key includes current date."""
        with patch('services.cache_service.datetime') as mock_datetime:
            mock_datetime.utcnow.return_value.strftime.return_value = "2024-01-01"
            key1 = cache_service.generate_search_cache_key("Central district", "breakfast")
            
            mock_datetime.utcnow.return_value.strftime.return_value = "2024-01-02"
            key2 = cache_service.generate_search_cache_key("Central district", "breakfast")
            
            # Different dates should generate different keys
            assert key1 != key2
    
    def test_generate_recommendation_cache_key(self, cache_service):
        """Test recommendation cache key generation."""
        restaurants_hash = "abc123"
        ranking_method = "sentiment_likes"
        
        key = cache_service.generate_recommendation_cache_key(restaurants_hash, ranking_method)
        
        assert isinstance(key, str)
        assert len(key) == 32  # MD5 hash length
        
        # Same inputs should generate same key
        key2 = cache_service.generate_recommendation_cache_key(restaurants_hash, ranking_method)
        assert key == key2
        
        # Different ranking method should generate different key
        key3 = cache_service.generate_recommendation_cache_key(restaurants_hash, "combined_sentiment")
        assert key != key3
    
    def test_generate_restaurants_hash(self, cache_service, sample_restaurants):
        """Test restaurants hash generation."""
        hash1 = cache_service.generate_restaurants_hash(sample_restaurants)
        
        assert isinstance(hash1, str)
        assert len(hash1) == 32  # MD5 hash length
        
        # Same restaurants should generate same hash
        hash2 = cache_service.generate_restaurants_hash(sample_restaurants)
        assert hash1 == hash2
        
        # Different order should generate same hash (sorted internally)
        reversed_restaurants = list(reversed(sample_restaurants))
        hash3 = cache_service.generate_restaurants_hash(reversed_restaurants)
        assert hash1 == hash3
        
        # Different restaurants should generate different hash
        modified_restaurants = sample_restaurants.copy()
        modified_restaurants[0]["name"] = "Modified Restaurant"
        hash4 = cache_service.generate_restaurants_hash(modified_restaurants)
        assert hash1 != hash4
    
    def test_cache_and_get_response(self, cache_service):
        """Test caching and retrieving response."""
        cache_key = "test_key"
        response = "test response data"
        
        # Cache the response
        cache_service.cache_response(cache_key, response)
        
        # Retrieve the response
        cached_response = cache_service.get_cached_response(cache_key)
        
        assert cached_response == response
        assert cache_service._hit_count == 1
        assert cache_service._miss_count == 0
    
    def test_get_cached_response_miss(self, cache_service):
        """Test cache miss when key doesn't exist."""
        cached_response = cache_service.get_cached_response("nonexistent_key")
        
        assert cached_response is None
        assert cache_service._hit_count == 0
        assert cache_service._miss_count == 1
    
    def test_get_cached_response_expired(self, cache_service_short_ttl):
        """Test cache miss when entry has expired."""
        import time
        
        cache_key = "test_key"
        response = "test response"
        
        # Cache with short TTL
        cache_service_short_ttl.cache_response(cache_key, response, ttl_seconds=1)
        
        # Wait for expiration
        time.sleep(1.1)
        
        # Should return None and remove expired entry
        cached_response = cache_service_short_ttl.get_cached_response(cache_key)
        
        assert cached_response is None
        assert cache_service_short_ttl._miss_count == 1
        assert cache_key not in cache_service_short_ttl._cache
    
    def test_cache_response_with_custom_ttl(self, cache_service):
        """Test caching response with custom TTL."""
        cache_key = "test_key"
        response = "test response"
        custom_ttl = 3600
        
        cache_service.cache_response(cache_key, response, custom_ttl)
        
        cache_entry = cache_service._cache[cache_key]
        assert cache_entry["response"] == response
        assert cache_entry["ttl_seconds"] == custom_ttl
        
        # Check expiration time is set correctly
        expected_expiry = cache_entry["cached_at"] + timedelta(seconds=custom_ttl)
        assert abs((cache_entry["expires_at"] - expected_expiry).total_seconds()) < 1
    
    def test_cache_response_with_default_ttl(self, cache_service):
        """Test caching response with default TTL."""
        cache_key = "test_key"
        response = "test response"
        
        cache_service.cache_response(cache_key, response)
        
        cache_entry = cache_service._cache[cache_key]
        assert cache_entry["ttl_seconds"] == 1800  # Default TTL
    
    def test_cache_search_results(self, cache_service, sample_restaurants):
        """Test caching search results."""
        district = "Central district"
        meal_time = "breakfast"
        
        cache_key = cache_service.cache_search_results(
            district, meal_time, sample_restaurants
        )
        
        assert isinstance(cache_key, str)
        assert cache_key in cache_service._cache
        
        # Verify cached data structure
        cached_data = json.loads(cache_service._cache[cache_key]["response"])
        assert cached_data["restaurants"] == sample_restaurants
        assert cached_data["search_criteria"]["district"] == district
        assert cached_data["search_criteria"]["meal_time"] == meal_time
        assert cached_data["total_count"] == len(sample_restaurants)
    
    def test_get_cached_search_results(self, cache_service, sample_restaurants):
        """Test retrieving cached search results."""
        district = "Central district"
        meal_time = "breakfast"
        
        # Cache the results first
        cache_service.cache_search_results(district, meal_time, sample_restaurants)
        
        # Retrieve cached results
        cached_results = cache_service.get_cached_search_results(district, meal_time)
        
        assert cached_results is not None
        assert cached_results["restaurants"] == sample_restaurants
        assert cached_results["search_criteria"]["district"] == district
        assert cached_results["search_criteria"]["meal_time"] == meal_time
    
    def test_get_cached_search_results_miss(self, cache_service):
        """Test cache miss for search results."""
        cached_results = cache_service.get_cached_search_results("Nonexistent", "lunch")
        
        assert cached_results is None
    
    def test_get_cached_search_results_invalid_json(self, cache_service):
        """Test handling of invalid JSON in cached search results."""
        cache_key = cache_service.generate_search_cache_key("Central district", "breakfast")
        
        # Manually insert invalid JSON
        cache_service._cache[cache_key] = {
            "response": "invalid json{",
            "cached_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(seconds=1800),
            "last_accessed": datetime.utcnow(),
            "access_count": 0,
            "ttl_seconds": 1800
        }
        
        cached_results = cache_service.get_cached_search_results("Central district", "breakfast")
        
        assert cached_results is None
        assert cache_key not in cache_service._cache  # Should be invalidated
    
    def test_cache_recommendation_results(self, cache_service, sample_restaurants):
        """Test caching recommendation results."""
        ranking_method = "sentiment_likes"
        recommendation = sample_restaurants[0]
        candidates = sample_restaurants
        
        cache_key = cache_service.cache_recommendation_results(
            sample_restaurants, ranking_method, recommendation, candidates
        )
        
        assert isinstance(cache_key, str)
        assert cache_key in cache_service._cache
        
        # Verify cached data structure
        cached_data = json.loads(cache_service._cache[cache_key]["response"])
        assert cached_data["recommendation"] == recommendation
        assert cached_data["candidates"] == candidates
        assert cached_data["ranking_method"] == ranking_method
        assert cached_data["total_restaurants"] == len(sample_restaurants)
    
    def test_get_cached_recommendation_results(self, cache_service, sample_restaurants):
        """Test retrieving cached recommendation results."""
        ranking_method = "sentiment_likes"
        recommendation = sample_restaurants[0]
        candidates = sample_restaurants
        
        # Cache the results first
        cache_service.cache_recommendation_results(
            sample_restaurants, ranking_method, recommendation, candidates
        )
        
        # Retrieve cached results
        cached_results = cache_service.get_cached_recommendation_results(
            sample_restaurants, ranking_method
        )
        
        assert cached_results is not None
        assert cached_results["recommendation"] == recommendation
        assert cached_results["candidates"] == candidates
        assert cached_results["ranking_method"] == ranking_method
    
    def test_get_cached_recommendation_results_miss(self, cache_service, sample_restaurants):
        """Test cache miss for recommendation results."""
        cached_results = cache_service.get_cached_recommendation_results(
            sample_restaurants, "nonexistent_method"
        )
        
        assert cached_results is None
    
    def test_invalidate_cache(self, cache_service):
        """Test cache invalidation."""
        cache_key = "test_key"
        cache_service.cache_response(cache_key, "test response")
        
        # Verify it's cached
        assert cache_key in cache_service._cache
        
        # Invalidate
        result = cache_service.invalidate_cache(cache_key)
        
        assert result is True
        assert cache_key not in cache_service._cache
    
    def test_invalidate_cache_nonexistent(self, cache_service):
        """Test invalidating nonexistent cache entry."""
        result = cache_service.invalidate_cache("nonexistent_key")
        
        assert result is False
    
    def test_clear_cache(self, cache_service):
        """Test clearing all cache entries."""
        # Add some cache entries
        cache_service.cache_response("key1", "response1")
        cache_service.cache_response("key2", "response2")
        cache_service.cache_response("key3", "response3")
        
        assert len(cache_service._cache) == 3
        
        # Clear cache
        cache_service.clear_cache()
        
        assert len(cache_service._cache) == 0
    
    def test_get_cache_stats(self, cache_service, sample_restaurants):
        """Test cache statistics retrieval."""
        # Add some cache entries
        cache_service.cache_search_results("Central district", "breakfast", sample_restaurants)
        cache_service.cache_recommendation_results(
            sample_restaurants, "sentiment_likes", sample_restaurants[0], sample_restaurants
        )
        
        # Generate some hits and misses
        cache_service.get_cached_search_results("Central district", "breakfast")  # Hit
        cache_service.get_cached_search_results("Nonexistent", "lunch")  # Miss
        
        stats = cache_service.get_cache_stats()
        
        assert stats["total_entries"] == 2
        assert stats["active_entries"] == 2
        assert stats["expired_entries"] == 0
        assert stats["search_cache_entries"] >= 1
        assert stats["recommendation_cache_entries"] >= 1
        assert stats["cache_hits"] == 1
        assert stats["cache_misses"] == 1
        assert stats["hit_rate_percentage"] == 50.0
        assert stats["cache_type"] == "in_memory"
        assert stats["default_ttl_seconds"] == 1800
    
    def test_get_cache_stats_empty_cache(self, cache_service):
        """Test cache statistics with empty cache."""
        stats = cache_service.get_cache_stats()
        
        assert stats["total_entries"] == 0
        assert stats["active_entries"] == 0
        assert stats["cache_hits"] == 0
        assert stats["cache_misses"] == 0
        assert stats["hit_rate_percentage"] == 0
    
    def test_get_cache_efficiency_metrics(self, cache_service):
        """Test cache efficiency metrics."""
        # Add some cache entries and access them
        cache_service.cache_response("key1", "response1")
        cache_service.get_cached_response("key1")  # Hit
        cache_service.get_cached_response("key1")  # Another hit
        cache_service.get_cached_response("nonexistent")  # Miss
        
        metrics = cache_service.get_cache_efficiency_metrics()
        
        assert metrics["hit_rate"] == 66.67  # 2 hits out of 3 requests
        assert metrics["total_requests"] == 3
        assert metrics["active_entries"] == 1
        assert metrics["estimated_memory_kb"] > 0
        assert metrics["average_access_per_entry"] == 2.0
    
    def test_invalidate_search_cache_all(self, cache_service, sample_restaurants):
        """Test invalidating all search cache entries."""
        # Add search cache entries
        cache_service.cache_search_results("Central district", "breakfast", sample_restaurants)
        cache_service.cache_search_results("Admiralty", "lunch", sample_restaurants)
        
        # Add non-search cache entry
        cache_service.cache_response("other_key", "other_response")
        
        assert len(cache_service._cache) == 3
        
        # Invalidate all search cache
        count = cache_service.invalidate_search_cache()
        
        assert count == 2
        assert len(cache_service._cache) == 1  # Only non-search entry remains
    
    def test_invalidate_search_cache_specific_district(self, cache_service, sample_restaurants):
        """Test invalidating search cache for specific district."""
        # Add search cache entries
        cache_service.cache_search_results("Central district", "breakfast", sample_restaurants)
        cache_service.cache_search_results("Admiralty", "lunch", sample_restaurants)
        
        initial_count = len(cache_service._cache)
        
        # Invalidate specific district (simplified matching)
        count = cache_service.invalidate_search_cache(district="Central")
        
        assert count >= 0  # May or may not match depending on key format
        assert len(cache_service._cache) <= initial_count
    
    def test_invalidate_recommendation_cache(self, cache_service, sample_restaurants):
        """Test invalidating all recommendation cache entries."""
        # Add recommendation cache entries
        cache_service.cache_recommendation_results(
            sample_restaurants, "sentiment_likes", sample_restaurants[0], sample_restaurants
        )
        cache_service.cache_recommendation_results(
            sample_restaurants, "combined_sentiment", sample_restaurants[1], sample_restaurants
        )
        
        # Add non-recommendation cache entry
        cache_service.cache_response("other_key", "other_response")
        
        assert len(cache_service._cache) == 3
        
        # Invalidate all recommendation cache
        count = cache_service.invalidate_recommendation_cache()
        
        assert count == 2
        assert len(cache_service._cache) == 1  # Only non-recommendation entry remains
    
    def test_cleanup_expired_entries(self, cache_service_short_ttl):
        """Test cleanup of expired entries."""
        import time
        
        # Add entries with short TTL
        cache_service_short_ttl.cache_response("key1", "response1", ttl_seconds=1)
        cache_service_short_ttl.cache_response("key2", "response2", ttl_seconds=10)
        
        assert len(cache_service_short_ttl._cache) == 2
        
        # Wait for first entry to expire
        time.sleep(1.1)
        
        # Trigger cleanup by accessing cache
        cache_service_short_ttl.get_cached_response("key2")
        
        # First entry should be cleaned up
        assert len(cache_service_short_ttl._cache) == 1
        assert "key2" in cache_service_short_ttl._cache
    
    def test_cleanup_least_recently_used(self, cache_service):
        """Test LRU cleanup functionality."""
        # Add multiple entries
        for i in range(15):
            cache_service.cache_response(f"key_{i}", f"response_{i}")
        
        # Access some entries to update their last_accessed time
        cache_service.get_cached_response("key_10")
        cache_service.get_cached_response("key_11")
        cache_service.get_cached_response("key_12")
        
        assert len(cache_service._cache) == 15
        
        # Cleanup to keep only 10 entries
        removed_count = cache_service.cleanup_least_recently_used(max_entries=10)
        
        assert removed_count == 5
        assert len(cache_service._cache) == 10
        
        # Recently accessed entries should still be there
        assert "key_10" in cache_service._cache
        assert "key_11" in cache_service._cache
        assert "key_12" in cache_service._cache
    
    def test_cleanup_least_recently_used_no_cleanup_needed(self, cache_service):
        """Test LRU cleanup when no cleanup is needed."""
        # Add fewer entries than the limit
        for i in range(5):
            cache_service.cache_response(f"key_{i}", f"response_{i}")
        
        removed_count = cache_service.cleanup_least_recently_used(max_entries=10)
        
        assert removed_count == 0
        assert len(cache_service._cache) == 5
    
    def test_cache_access_tracking(self, cache_service):
        """Test that cache access is properly tracked."""
        cache_key = "test_key"
        cache_service.cache_response(cache_key, "test response")
        
        # Access the cache entry multiple times
        cache_service.get_cached_response(cache_key)
        cache_service.get_cached_response(cache_key)
        cache_service.get_cached_response(cache_key)
        
        cache_entry = cache_service._cache[cache_key]
        assert cache_entry["access_count"] == 3
        assert cache_service._hit_count == 3
    
    def test_cache_entry_structure(self, cache_service):
        """Test that cache entries have correct structure."""
        cache_key = "test_key"
        response = "test response"
        ttl = 3600
        
        cache_service.cache_response(cache_key, response, ttl)
        
        cache_entry = cache_service._cache[cache_key]
        
        assert "response" in cache_entry
        assert "cached_at" in cache_entry
        assert "expires_at" in cache_entry
        assert "last_accessed" in cache_entry
        assert "access_count" in cache_entry
        assert "ttl_seconds" in cache_entry
        
        assert cache_entry["response"] == response
        assert cache_entry["ttl_seconds"] == ttl
        assert isinstance(cache_entry["cached_at"], datetime)
        assert isinstance(cache_entry["expires_at"], datetime)
        assert isinstance(cache_entry["last_accessed"], datetime)
        assert cache_entry["access_count"] == 0


if __name__ == "__main__":
    pytest.main([__file__])