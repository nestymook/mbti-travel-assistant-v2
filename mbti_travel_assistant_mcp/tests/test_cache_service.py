"""
Tests for Cache Service

This module contains comprehensive tests for the cache service functionality
including response caching, cache key generation, and TTL management.
"""

import json
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch

from services.cache_service import CacheService


class TestCacheService:
    """Test cases for CacheService."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.cache_service = CacheService(default_ttl=300)  # 5 minutes
        
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
        
        self.sample_recommendation = {
            "id": "rest_001",
            "name": "Test Restaurant 1",
            "district": "Central district"
        }
        
        self.sample_candidates = [
            {
                "id": "rest_002",
                "name": "Test Restaurant 2", 
                "district": "Central district"
            }
        ]
    
    def test_cache_service_initialization(self):
        """Test cache service initialization."""
        cache_service = CacheService(default_ttl=600)
        assert cache_service._default_ttl == 600
        assert cache_service._hit_count == 0
        assert cache_service._miss_count == 0
        assert len(cache_service._cache) == 0
    
    def test_generate_search_cache_key(self):
        """Test search cache key generation."""
        key1 = self.cache_service.generate_search_cache_key("Central district", "breakfast")
        key2 = self.cache_service.generate_search_cache_key("central district", "breakfast")
        key3 = self.cache_service.generate_search_cache_key("Central district", "lunch")
        
        # Same district/meal_time should generate same key (case insensitive)
        assert key1 == key2
        
        # Different meal_time should generate different key
        assert key1 != key3
        
        # Keys should be consistent
        key1_repeat = self.cache_service.generate_search_cache_key("Central district", "breakfast")
        assert key1 == key1_repeat
    
    def test_generate_recommendation_cache_key(self):
        """Test recommendation cache key generation."""
        restaurants_hash = self.cache_service.generate_restaurants_hash(self.sample_restaurants)
        
        key1 = self.cache_service.generate_recommendation_cache_key(restaurants_hash, "sentiment_likes")
        key2 = self.cache_service.generate_recommendation_cache_key(restaurants_hash, "combined_sentiment")
        
        # Different ranking methods should generate different keys
        assert key1 != key2
        
        # Same parameters should generate same key
        key1_repeat = self.cache_service.generate_recommendation_cache_key(restaurants_hash, "sentiment_likes")
        assert key1 == key1_repeat
    
    def test_generate_restaurants_hash(self):
        """Test restaurant list hashing."""
        hash1 = self.cache_service.generate_restaurants_hash(self.sample_restaurants)
        
        # Same restaurants in different order should generate same hash
        reversed_restaurants = list(reversed(self.sample_restaurants))
        hash2 = self.cache_service.generate_restaurants_hash(reversed_restaurants)
        assert hash1 == hash2
        
        # Different restaurants should generate different hash
        modified_restaurants = self.sample_restaurants.copy()
        modified_restaurants[0]["name"] = "Modified Restaurant"
        hash3 = self.cache_service.generate_restaurants_hash(modified_restaurants)
        assert hash1 != hash3
    
    def test_basic_cache_operations(self):
        """Test basic cache get/set operations."""
        cache_key = "test_key"
        response_data = "test_response"
        
        # Cache miss initially
        result = self.cache_service.get_cached_response(cache_key)
        assert result is None
        assert self.cache_service._miss_count == 1
        
        # Cache the response
        self.cache_service.cache_response(cache_key, response_data, 300)
        
        # Cache hit
        result = self.cache_service.get_cached_response(cache_key)
        assert result == response_data
        assert self.cache_service._hit_count == 1
    
    def test_cache_expiration(self):
        """Test cache TTL expiration."""
        cache_key = "test_expiration"
        response_data = "test_response"
        
        # Cache with very short TTL
        self.cache_service.cache_response(cache_key, response_data, 1)
        
        # Should be available immediately
        result = self.cache_service.get_cached_response(cache_key)
        assert result == response_data
        
        # Mock time to simulate expiration
        future_time = datetime.utcnow() + timedelta(seconds=2)
        with patch('services.cache_service.datetime') as mock_datetime:
            mock_datetime.utcnow.return_value = future_time
            result = self.cache_service.get_cached_response(cache_key)
            assert result is None
    
    def test_cache_search_results(self):
        """Test caching of search results."""
        district = "Central district"
        meal_time = "breakfast"
        
        # Cache search results
        cache_key = self.cache_service.cache_search_results(
            district, meal_time, self.sample_restaurants, 600
        )
        
        # Retrieve cached results
        cached_results = self.cache_service.get_cached_search_results(district, meal_time)
        
        assert cached_results is not None
        assert cached_results["restaurants"] == self.sample_restaurants
        assert cached_results["search_criteria"]["district"] == district
        assert cached_results["search_criteria"]["meal_time"] == meal_time
        assert cached_results["total_count"] == len(self.sample_restaurants)
    
    def test_cache_recommendation_results(self):
        """Test caching of recommendation results."""
        ranking_method = "sentiment_likes"
        
        # Cache recommendation results
        cache_key = self.cache_service.cache_recommendation_results(
            self.sample_restaurants,
            ranking_method,
            self.sample_recommendation,
            self.sample_candidates,
            600
        )
        
        # Retrieve cached results
        cached_results = self.cache_service.get_cached_recommendation_results(
            self.sample_restaurants, ranking_method
        )
        
        assert cached_results is not None
        assert cached_results["recommendation"] == self.sample_recommendation
        assert cached_results["candidates"] == self.sample_candidates
        assert cached_results["ranking_method"] == ranking_method
        assert cached_results["total_restaurants"] == len(self.sample_restaurants)
    
    def test_cache_invalidation(self):
        """Test cache invalidation functionality."""
        cache_key = "test_invalidation"
        response_data = "test_response"
        
        # Cache a response
        self.cache_service.cache_response(cache_key, response_data, 300)
        assert self.cache_service.get_cached_response(cache_key) == response_data
        
        # Invalidate the cache entry
        result = self.cache_service.invalidate_cache(cache_key)
        assert result is True
        
        # Should be cache miss now
        assert self.cache_service.get_cached_response(cache_key) is None
        
        # Invalidating non-existent key should return False
        result = self.cache_service.invalidate_cache("non_existent_key")
        assert result is False
    
    def test_search_cache_invalidation(self):
        """Test search-specific cache invalidation."""
        # Cache multiple search results
        self.cache_service.cache_search_results("Central district", "breakfast", self.sample_restaurants)
        self.cache_service.cache_search_results("Admiralty", "lunch", self.sample_restaurants)
        self.cache_service.cache_search_results("Causeway Bay", "dinner", self.sample_restaurants)
        
        # Invalidate all search cache
        invalidated_count = self.cache_service.invalidate_search_cache()
        assert invalidated_count == 3
        
        # Verify all search results are gone
        assert self.cache_service.get_cached_search_results("Central district", "breakfast") is None
        assert self.cache_service.get_cached_search_results("Admiralty", "lunch") is None
        assert self.cache_service.get_cached_search_results("Causeway Bay", "dinner") is None
    
    def test_recommendation_cache_invalidation(self):
        """Test recommendation-specific cache invalidation."""
        # Cache multiple recommendation results
        self.cache_service.cache_recommendation_results(
            self.sample_restaurants, "sentiment_likes", 
            self.sample_recommendation, self.sample_candidates
        )
        self.cache_service.cache_recommendation_results(
            self.sample_restaurants, "combined_sentiment",
            self.sample_recommendation, self.sample_candidates
        )
        
        # Invalidate all recommendation cache
        invalidated_count = self.cache_service.invalidate_recommendation_cache()
        assert invalidated_count == 2
        
        # Verify all recommendation results are gone
        assert self.cache_service.get_cached_recommendation_results(
            self.sample_restaurants, "sentiment_likes"
        ) is None
        assert self.cache_service.get_cached_recommendation_results(
            self.sample_restaurants, "combined_sentiment"
        ) is None
    
    def test_cache_statistics(self):
        """Test cache statistics functionality."""
        # Initially empty cache
        stats = self.cache_service.get_cache_stats()
        assert stats["total_entries"] == 0
        assert stats["active_entries"] == 0
        assert stats["cache_hits"] == 0
        assert stats["cache_misses"] == 0
        assert stats["hit_rate_percentage"] == 0
        
        # Add some cache entries
        self.cache_service.cache_search_results("Central district", "breakfast", self.sample_restaurants)
        self.cache_service.cache_recommendation_results(
            self.sample_restaurants, "sentiment_likes",
            self.sample_recommendation, self.sample_candidates
        )
        
        # Generate some hits and misses
        self.cache_service.get_cached_search_results("Central district", "breakfast")  # hit
        self.cache_service.get_cached_search_results("Admiralty", "lunch")  # miss
        
        stats = self.cache_service.get_cache_stats()
        assert stats["total_entries"] == 2
        assert stats["active_entries"] == 2
        assert stats["search_cache_entries"] == 1
        assert stats["recommendation_cache_entries"] == 1
        assert stats["cache_hits"] == 1
        assert stats["cache_misses"] == 1
        assert stats["hit_rate_percentage"] == 50.0
    
    def test_cache_efficiency_metrics(self):
        """Test cache efficiency metrics."""
        # Add cache entries
        self.cache_service.cache_search_results("Central district", "breakfast", self.sample_restaurants)
        
        # Generate some access
        self.cache_service.get_cached_search_results("Central district", "breakfast")
        self.cache_service.get_cached_search_results("Central district", "breakfast")
        
        metrics = self.cache_service.get_cache_efficiency_metrics()
        
        assert "hit_rate" in metrics
        assert "total_requests" in metrics
        assert "active_entries" in metrics
        assert "estimated_memory_kb" in metrics
        assert "average_access_per_entry" in metrics
        
        assert metrics["active_entries"] == 1
        assert metrics["total_requests"] == 2
        assert metrics["hit_rate"] == 100.0  # Both requests were hits
    
    def test_lru_cleanup(self):
        """Test least recently used cleanup."""
        # Add multiple cache entries
        for i in range(10):
            self.cache_service.cache_response(f"key_{i}", f"response_{i}", 300)
        
        assert len(self.cache_service._cache) == 10
        
        # Access some entries to update their last_accessed time
        self.cache_service.get_cached_response("key_5")
        self.cache_service.get_cached_response("key_7")
        self.cache_service.get_cached_response("key_9")
        
        # Cleanup to keep only 5 entries
        removed_count = self.cache_service.cleanup_least_recently_used(5)
        
        assert removed_count == 5
        assert len(self.cache_service._cache) == 5
        
        # Recently accessed entries should still be there
        assert self.cache_service.get_cached_response("key_5") is not None
        assert self.cache_service.get_cached_response("key_7") is not None
        assert self.cache_service.get_cached_response("key_9") is not None
    
    def test_clear_cache(self):
        """Test clearing all cache entries."""
        # Add some cache entries
        self.cache_service.cache_search_results("Central district", "breakfast", self.sample_restaurants)
        self.cache_service.cache_recommendation_results(
            self.sample_restaurants, "sentiment_likes",
            self.sample_recommendation, self.sample_candidates
        )
        
        assert len(self.cache_service._cache) == 2
        
        # Clear cache
        self.cache_service.clear_cache()
        
        assert len(self.cache_service._cache) == 0
        
        # Verify all entries are gone
        assert self.cache_service.get_cached_search_results("Central district", "breakfast") is None
        assert self.cache_service.get_cached_recommendation_results(
            self.sample_restaurants, "sentiment_likes"
        ) is None
    
    def test_malformed_cache_data_handling(self):
        """Test handling of malformed cached data."""
        # Manually insert malformed data
        cache_key = self.cache_service.generate_search_cache_key("Central district", "breakfast")
        self.cache_service.cache_response(cache_key, "invalid_json_data", 300)
        
        # Should handle gracefully and return None
        result = self.cache_service.get_cached_search_results("Central district", "breakfast")
        assert result is None
        
        # Cache entry should be invalidated
        assert cache_key not in self.cache_service._cache


class TestCacheServiceIntegration:
    """Integration tests for cache service with other components."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.cache_service = CacheService(default_ttl=300)
    
    def test_cache_workflow_integration(self):
        """Test complete cache workflow integration."""
        district = "Central district"
        meal_time = "breakfast"
        ranking_method = "sentiment_likes"
        
        restaurants = [
            {
                "id": "rest_001",
                "name": "Test Restaurant 1",
                "district": district,
                "sentiment": {"likes": 85, "dislikes": 10, "neutral": 5}
            }
        ]
        
        recommendation = restaurants[0]
        candidates = []
        
        # Step 1: Cache search results
        search_cache_key = self.cache_service.cache_search_results(
            district, meal_time, restaurants
        )
        
        # Step 2: Cache recommendation results
        rec_cache_key = self.cache_service.cache_recommendation_results(
            restaurants, ranking_method, recommendation, candidates
        )
        
        # Step 3: Retrieve both from cache
        cached_search = self.cache_service.get_cached_search_results(district, meal_time)
        cached_recommendation = self.cache_service.get_cached_recommendation_results(
            restaurants, ranking_method
        )
        
        # Verify complete workflow
        assert cached_search is not None
        assert cached_search["restaurants"] == restaurants
        
        assert cached_recommendation is not None
        assert cached_recommendation["recommendation"] == recommendation
        assert cached_recommendation["candidates"] == candidates
        
        # Verify cache statistics
        stats = self.cache_service.get_cache_stats()
        assert stats["active_entries"] == 2
        assert stats["search_cache_entries"] == 1
        assert stats["recommendation_cache_entries"] == 1
        assert stats["cache_hits"] == 2  # Two successful retrievals