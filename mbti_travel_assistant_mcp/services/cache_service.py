"""
Cache Service

This module provides comprehensive caching functionality for MBTI personality results,
tourist spots, restaurant recommendations, and complete itinerary responses to improve
performance and reduce load on knowledge base and MCP servers.
"""

import json
import logging
import hashlib
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class CacheService:
    """
    Comprehensive caching service for MBTI Travel Assistant.
    
    This service provides in-memory caching with TTL support to improve
    performance for frequently requested MBTI personality results, tourist spots,
    restaurant recommendations, and complete itinerary responses.
    
    Supports:
    - MBTI personality results caching
    - Tourist spot data caching
    - Restaurant search and recommendation caching
    - Complete itinerary response caching
    - TTL-based cache expiration and invalidation
    """
    
    def __init__(self, default_ttl: int = 1800, mbti_ttl: int = 3600, tourist_spots_ttl: int = 7200):
        """
        Initialize the cache service with in-memory storage.
        
        Args:
            default_ttl: Default TTL in seconds (30 minutes)
            mbti_ttl: TTL for MBTI personality results (60 minutes)
            tourist_spots_ttl: TTL for tourist spot data (120 minutes)
        """
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._default_ttl = default_ttl
        self._mbti_ttl = mbti_ttl
        self._tourist_spots_ttl = tourist_spots_ttl
        self._hit_count = 0
        self._miss_count = 0
        logger.info(
            f"Initialized CacheService with TTLs - default: {default_ttl}s, "
            f"MBTI: {mbti_ttl}s, tourist_spots: {tourist_spots_ttl}s"
        )
    
    def generate_search_cache_key(self, district: str, meal_time: str) -> str:
        """
        Generate cache key for restaurant search results.
        
        Args:
            district: District name
            meal_time: Meal time (breakfast, lunch, dinner)
            
        Returns:
            Cache key string
        """
        # Normalize inputs for consistent caching
        district_normalized = district.lower().strip()
        meal_time_normalized = meal_time.lower().strip()
        
        # Include date to ensure daily cache refresh
        date_str = datetime.utcnow().strftime("%Y-%m-%d")
        
        key_data = f"search:{district_normalized}:{meal_time_normalized}:{date_str}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def generate_recommendation_cache_key(self, restaurants_hash: str, ranking_method: str) -> str:
        """
        Generate cache key for recommendation results.
        
        Args:
            restaurants_hash: Hash of restaurant list
            ranking_method: Ranking method used
            
        Returns:
            Cache key string
        """
        key_data = f"recommendation:{restaurants_hash}:{ranking_method}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def generate_restaurants_hash(self, restaurants: List[Dict[str, Any]]) -> str:
        """
        Generate hash for a list of restaurants for cache key generation.
        
        Args:
            restaurants: List of restaurant dictionaries
            
        Returns:
            Hash string representing the restaurant list
        """
        # Sort restaurants by ID for consistent hashing
        sorted_restaurants = sorted(restaurants, key=lambda r: r.get('id', ''))
        restaurants_str = json.dumps(sorted_restaurants, sort_keys=True)
        return hashlib.md5(restaurants_str.encode()).hexdigest()
    
    def generate_mbti_cache_key(self, mbti_personality: str) -> str:
        """
        Generate cache key for MBTI personality results.
        
        Args:
            mbti_personality: 4-character MBTI personality code (e.g., INFJ, ENFP)
            
        Returns:
            Cache key string for MBTI personality results
        """
        # Normalize MBTI personality for consistent caching
        mbti_normalized = mbti_personality.upper().strip()
        
        # Include date to ensure daily cache refresh for tourist spots
        date_str = datetime.utcnow().strftime("%Y-%m-%d")
        
        key_data = f"mbti:{mbti_normalized}:{date_str}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def generate_tourist_spots_cache_key(self, mbti_personality: str, query_type: str = "default") -> str:
        """
        Generate cache key for tourist spots data.
        
        Args:
            mbti_personality: 4-character MBTI personality code
            query_type: Type of query (default, fallback, etc.)
            
        Returns:
            Cache key string for tourist spots data
        """
        mbti_normalized = mbti_personality.upper().strip()
        query_type_normalized = query_type.lower().strip()
        
        # Include date for daily refresh
        date_str = datetime.utcnow().strftime("%Y-%m-%d")
        
        key_data = f"tourist_spots:{mbti_normalized}:{query_type_normalized}:{date_str}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def generate_itinerary_cache_key(self, mbti_personality: str, request_hash: str) -> str:
        """
        Generate cache key for complete itinerary responses.
        
        Args:
            mbti_personality: 4-character MBTI personality code
            request_hash: Hash of the complete request parameters
            
        Returns:
            Cache key string for complete itinerary
        """
        mbti_normalized = mbti_personality.upper().strip()
        
        # Include hour for shorter cache duration on complete itineraries
        hour_str = datetime.utcnow().strftime("%Y-%m-%d-%H")
        
        key_data = f"itinerary:{mbti_normalized}:{request_hash}:{hour_str}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def get_cached_response(self, cache_key: str) -> Optional[str]:
        """
        Get cached response for the given key.
        
        Args:
            cache_key: Cache key to lookup
            
        Returns:
            Cached response string if found and not expired, None otherwise
        """
        if cache_key not in self._cache:
            self._miss_count += 1
            return None
        
        cache_entry = self._cache[cache_key]
        
        # Check if cache entry has expired
        if datetime.utcnow() > cache_entry["expires_at"]:
            # Remove expired entry
            del self._cache[cache_key]
            logger.debug(f"Cache entry expired and removed: {cache_key}")
            self._miss_count += 1
            return None
        
        # Update access time for LRU tracking
        cache_entry["last_accessed"] = datetime.utcnow()
        cache_entry["access_count"] = cache_entry.get("access_count", 0) + 1
        
        self._hit_count += 1
        logger.info(f"Cache hit for key: {cache_key}")
        return cache_entry["response"]
    
    def cache_response(
        self,
        cache_key: str,
        response: str,
        ttl_seconds: Optional[int] = None
    ) -> None:
        """
        Cache a response with the given TTL.
        
        Args:
            cache_key: Key to store the response under
            response: Response string to cache
            ttl_seconds: Time to live in seconds (uses default if None)
        """
        if ttl_seconds is None:
            ttl_seconds = self._default_ttl
            
        expires_at = datetime.utcnow() + timedelta(seconds=ttl_seconds)
        now = datetime.utcnow()
        
        self._cache[cache_key] = {
            "response": response,
            "cached_at": now,
            "expires_at": expires_at,
            "last_accessed": now,
            "access_count": 0,
            "ttl_seconds": ttl_seconds
        }
        
        logger.info(
            f"Cached response",
            extra={
                "cache_key": cache_key,
                "ttl_seconds": ttl_seconds,
                "expires_at": expires_at.isoformat()
            }
        )
        
        # Clean up expired entries periodically
        self._cleanup_expired_entries()
    
    def cache_search_results(
        self,
        district: str,
        meal_time: str,
        restaurants: List[Dict[str, Any]],
        ttl_seconds: Optional[int] = None
    ) -> str:
        """
        Cache restaurant search results.
        
        Args:
            district: District name
            meal_time: Meal time
            restaurants: List of restaurant dictionaries
            ttl_seconds: TTL in seconds (uses default if None)
            
        Returns:
            Cache key used for storage
        """
        cache_key = self.generate_search_cache_key(district, meal_time)
        response_data = {
            "restaurants": restaurants,
            "search_criteria": {
                "district": district,
                "meal_time": meal_time
            },
            "cached_at": datetime.utcnow().isoformat(),
            "total_count": len(restaurants)
        }
        
        self.cache_response(cache_key, json.dumps(response_data), ttl_seconds)
        return cache_key
    
    def get_cached_search_results(self, district: str, meal_time: str) -> Optional[Dict[str, Any]]:
        """
        Get cached restaurant search results.
        
        Args:
            district: District name
            meal_time: Meal time
            
        Returns:
            Cached search results or None if not found/expired
        """
        cache_key = self.generate_search_cache_key(district, meal_time)
        cached_response = self.get_cached_response(cache_key)
        
        if cached_response:
            try:
                return json.loads(cached_response)
            except json.JSONDecodeError:
                logger.error(f"Failed to parse cached search results for key: {cache_key}")
                self.invalidate_cache(cache_key)
        
        return None
    
    def cache_recommendation_results(
        self,
        restaurants: List[Dict[str, Any]],
        ranking_method: str,
        recommendation: Dict[str, Any],
        candidates: List[Dict[str, Any]],
        ttl_seconds: Optional[int] = None
    ) -> str:
        """
        Cache recommendation results.
        
        Args:
            restaurants: Original restaurant list
            ranking_method: Ranking method used
            recommendation: Recommended restaurant
            candidates: Candidate restaurants
            ttl_seconds: TTL in seconds (uses default if None)
            
        Returns:
            Cache key used for storage
        """
        restaurants_hash = self.generate_restaurants_hash(restaurants)
        cache_key = self.generate_recommendation_cache_key(restaurants_hash, ranking_method)
        
        response_data = {
            "recommendation": recommendation,
            "candidates": candidates,
            "ranking_method": ranking_method,
            "restaurants_hash": restaurants_hash,
            "cached_at": datetime.utcnow().isoformat(),
            "total_restaurants": len(restaurants)
        }
        
        self.cache_response(cache_key, json.dumps(response_data), ttl_seconds)
        return cache_key
    
    def get_cached_recommendation_results(
        self,
        restaurants: List[Dict[str, Any]],
        ranking_method: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached recommendation results.
        
        Args:
            restaurants: Restaurant list to check cache for
            ranking_method: Ranking method used
            
        Returns:
            Cached recommendation results or None if not found/expired
        """
        restaurants_hash = self.generate_restaurants_hash(restaurants)
        cache_key = self.generate_recommendation_cache_key(restaurants_hash, ranking_method)
        cached_response = self.get_cached_response(cache_key)
        
        if cached_response:
            try:
                return json.loads(cached_response)
            except json.JSONDecodeError:
                logger.error(f"Failed to parse cached recommendation results for key: {cache_key}")
                self.invalidate_cache(cache_key)
        
        return None
    
    def cache_mbti_personality_results(
        self,
        mbti_personality: str,
        tourist_spots: List[Dict[str, Any]],
        query_metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Cache MBTI personality query results from knowledge base.
        
        Args:
            mbti_personality: 4-character MBTI personality code
            tourist_spots: List of tourist spots matching the personality
            query_metadata: Optional metadata about the query
            
        Returns:
            Cache key used for storage
        """
        cache_key = self.generate_mbti_cache_key(mbti_personality)
        
        response_data = {
            "mbti_personality": mbti_personality.upper(),
            "tourist_spots": tourist_spots,
            "total_spots": len(tourist_spots),
            "query_metadata": query_metadata or {},
            "cached_at": datetime.utcnow().isoformat(),
            "cache_type": "mbti_personality_results"
        }
        
        self.cache_response(cache_key, json.dumps(response_data), self._mbti_ttl)
        logger.info(f"Cached MBTI personality results for {mbti_personality}: {len(tourist_spots)} spots")
        return cache_key
    
    def get_cached_mbti_personality_results(self, mbti_personality: str) -> Optional[Dict[str, Any]]:
        """
        Get cached MBTI personality query results.
        
        Args:
            mbti_personality: 4-character MBTI personality code
            
        Returns:
            Cached MBTI personality results or None if not found/expired
        """
        cache_key = self.generate_mbti_cache_key(mbti_personality)
        cached_response = self.get_cached_response(cache_key)
        
        if cached_response:
            try:
                result = json.loads(cached_response)
                logger.info(f"Cache hit for MBTI personality {mbti_personality}: {result.get('total_spots', 0)} spots")
                return result
            except json.JSONDecodeError:
                logger.error(f"Failed to parse cached MBTI results for key: {cache_key}")
                self.invalidate_cache(cache_key)
        
        return None
    
    def cache_tourist_spots_data(
        self,
        mbti_personality: str,
        tourist_spots: List[Dict[str, Any]],
        query_type: str = "default",
        processing_metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Cache tourist spots data for specific MBTI personality.
        
        Args:
            mbti_personality: 4-character MBTI personality code
            tourist_spots: List of tourist spots data
            query_type: Type of query (default, fallback, etc.)
            processing_metadata: Optional metadata about processing
            
        Returns:
            Cache key used for storage
        """
        cache_key = self.generate_tourist_spots_cache_key(mbti_personality, query_type)
        
        response_data = {
            "mbti_personality": mbti_personality.upper(),
            "query_type": query_type,
            "tourist_spots": tourist_spots,
            "total_spots": len(tourist_spots),
            "processing_metadata": processing_metadata or {},
            "cached_at": datetime.utcnow().isoformat(),
            "cache_type": "tourist_spots_data"
        }
        
        self.cache_response(cache_key, json.dumps(response_data), self._tourist_spots_ttl)
        logger.info(f"Cached tourist spots data for {mbti_personality} ({query_type}): {len(tourist_spots)} spots")
        return cache_key
    
    def get_cached_tourist_spots_data(
        self,
        mbti_personality: str,
        query_type: str = "default"
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached tourist spots data for specific MBTI personality.
        
        Args:
            mbti_personality: 4-character MBTI personality code
            query_type: Type of query (default, fallback, etc.)
            
        Returns:
            Cached tourist spots data or None if not found/expired
        """
        cache_key = self.generate_tourist_spots_cache_key(mbti_personality, query_type)
        cached_response = self.get_cached_response(cache_key)
        
        if cached_response:
            try:
                result = json.loads(cached_response)
                logger.info(
                    f"Cache hit for tourist spots {mbti_personality} ({query_type}): "
                    f"{result.get('total_spots', 0)} spots"
                )
                return result
            except json.JSONDecodeError:
                logger.error(f"Failed to parse cached tourist spots data for key: {cache_key}")
                self.invalidate_cache(cache_key)
        
        return None
    
    def cache_complete_itinerary(
        self,
        mbti_personality: str,
        request_params: Dict[str, Any],
        itinerary_response: Dict[str, Any]
    ) -> str:
        """
        Cache complete itinerary response.
        
        Args:
            mbti_personality: 4-character MBTI personality code
            request_params: Original request parameters
            itinerary_response: Complete itinerary response
            
        Returns:
            Cache key used for storage
        """
        # Generate hash of request parameters for cache key
        request_str = json.dumps(request_params, sort_keys=True)
        request_hash = hashlib.md5(request_str.encode()).hexdigest()
        
        cache_key = self.generate_itinerary_cache_key(mbti_personality, request_hash)
        
        response_data = {
            "mbti_personality": mbti_personality.upper(),
            "request_hash": request_hash,
            "request_params": request_params,
            "itinerary_response": itinerary_response,
            "cached_at": datetime.utcnow().isoformat(),
            "cache_type": "complete_itinerary"
        }
        
        # Use shorter TTL for complete itineraries (1 hour)
        itinerary_ttl = 3600
        self.cache_response(cache_key, json.dumps(response_data), itinerary_ttl)
        logger.info(f"Cached complete itinerary for {mbti_personality}")
        return cache_key
    
    def get_cached_complete_itinerary(
        self,
        mbti_personality: str,
        request_params: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached complete itinerary response.
        
        Args:
            mbti_personality: 4-character MBTI personality code
            request_params: Original request parameters
            
        Returns:
            Cached complete itinerary or None if not found/expired
        """
        request_str = json.dumps(request_params, sort_keys=True)
        request_hash = hashlib.md5(request_str.encode()).hexdigest()
        
        cache_key = self.generate_itinerary_cache_key(mbti_personality, request_hash)
        cached_response = self.get_cached_response(cache_key)
        
        if cached_response:
            try:
                result = json.loads(cached_response)
                logger.info(f"Cache hit for complete itinerary {mbti_personality}")
                return result.get("itinerary_response")
            except json.JSONDecodeError:
                logger.error(f"Failed to parse cached itinerary for key: {cache_key}")
                self.invalidate_cache(cache_key)
        
        return None
    
    def invalidate_cache(self, cache_key: str) -> bool:
        """
        Invalidate a specific cache entry.
        
        Args:
            cache_key: Key to invalidate
            
        Returns:
            True if entry was found and removed, False otherwise
        """
        if cache_key in self._cache:
            del self._cache[cache_key]
            logger.info(f"Cache entry invalidated: {cache_key}")
            return True
        
        return False
    
    def clear_cache(self) -> None:
        """Clear all cache entries."""
        entry_count = len(self._cache)
        self._cache.clear()
        logger.info(f"Cache cleared, removed {entry_count} entries")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        now = datetime.utcnow()
        active_entries = 0
        expired_entries = 0
        search_entries = 0
        recommendation_entries = 0
        mbti_entries = 0
        tourist_spots_entries = 0
        itinerary_entries = 0
        total_access_count = 0
        
        for key, entry in self._cache.items():
            if now <= entry["expires_at"]:
                active_entries += 1
                total_access_count += entry.get("access_count", 0)
                
                # Categorize cache entries by type
                if "search:" in key:
                    search_entries += 1
                elif "recommendation:" in key:
                    recommendation_entries += 1
                elif "mbti:" in key:
                    mbti_entries += 1
                elif "tourist_spots:" in key:
                    tourist_spots_entries += 1
                elif "itinerary:" in key:
                    itinerary_entries += 1
            else:
                expired_entries += 1
        
        total_requests = self._hit_count + self._miss_count
        hit_rate = (self._hit_count / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "total_entries": len(self._cache),
            "active_entries": active_entries,
            "expired_entries": expired_entries,
            "search_cache_entries": search_entries,
            "recommendation_cache_entries": recommendation_entries,
            "mbti_cache_entries": mbti_entries,
            "tourist_spots_cache_entries": tourist_spots_entries,
            "itinerary_cache_entries": itinerary_entries,
            "cache_hits": self._hit_count,
            "cache_misses": self._miss_count,
            "hit_rate_percentage": round(hit_rate, 2),
            "total_access_count": total_access_count,
            "cache_type": "in_memory",
            "ttl_config": {
                "default_ttl_seconds": self._default_ttl,
                "mbti_ttl_seconds": self._mbti_ttl,
                "tourist_spots_ttl_seconds": self._tourist_spots_ttl
            }
        }
    
    def get_cache_efficiency_metrics(self) -> Dict[str, Any]:
        """
        Get cache efficiency metrics for performance monitoring.
        
        Returns:
            Dictionary with efficiency metrics
        """
        stats = self.get_cache_stats()
        
        # Calculate memory usage estimation (rough)
        memory_usage_bytes = 0
        for entry in self._cache.values():
            memory_usage_bytes += len(str(entry["response"]).encode('utf-8'))
        
        return {
            "hit_rate": stats["hit_rate_percentage"],
            "total_requests": stats["cache_hits"] + stats["cache_misses"],
            "active_entries": stats["active_entries"],
            "estimated_memory_kb": round(memory_usage_bytes / 1024, 2),
            "average_access_per_entry": (
                stats["total_access_count"] / stats["active_entries"]
                if stats["active_entries"] > 0 else 0
            )
        }
    
    def invalidate_search_cache(self, district: Optional[str] = None, meal_time: Optional[str] = None) -> int:
        """
        Invalidate search cache entries.
        
        Args:
            district: Specific district to invalidate (all if None)
            meal_time: Specific meal time to invalidate (all if None)
            
        Returns:
            Number of entries invalidated
        """
        keys_to_remove = []
        
        for key in self._cache.keys():
            if "search:" in key:
                if district is None and meal_time is None:
                    # Remove all search cache entries
                    keys_to_remove.append(key)
                else:
                    # Check if this entry matches the criteria
                    # This is a simplified check - in production you might want more sophisticated matching
                    if district and district.lower() in key.lower():
                        keys_to_remove.append(key)
                    elif meal_time and meal_time.lower() in key.lower():
                        keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self._cache[key]
        
        if keys_to_remove:
            logger.info(f"Invalidated {len(keys_to_remove)} search cache entries")
        
        return len(keys_to_remove)
    
    def invalidate_recommendation_cache(self) -> int:
        """
        Invalidate all recommendation cache entries.
        
        Returns:
            Number of entries invalidated
        """
        keys_to_remove = []
        
        for key in self._cache.keys():
            if "recommendation:" in key:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self._cache[key]
        
        if keys_to_remove:
            logger.info(f"Invalidated {len(keys_to_remove)} recommendation cache entries")
        
        return len(keys_to_remove)
    
    def invalidate_mbti_cache(self, mbti_personality: Optional[str] = None) -> int:
        """
        Invalidate MBTI personality cache entries.
        
        Args:
            mbti_personality: Specific MBTI personality to invalidate (all if None)
            
        Returns:
            Number of entries invalidated
        """
        keys_to_remove = []
        
        for key in self._cache.keys():
            if "mbti:" in key:
                if mbti_personality is None:
                    # Remove all MBTI cache entries
                    keys_to_remove.append(key)
                else:
                    # Check if this entry matches the specific MBTI personality
                    if mbti_personality.upper() in key.upper():
                        keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self._cache[key]
        
        if keys_to_remove:
            personality_info = f" for {mbti_personality}" if mbti_personality else ""
            logger.info(f"Invalidated {len(keys_to_remove)} MBTI cache entries{personality_info}")
        
        return len(keys_to_remove)
    
    def invalidate_tourist_spots_cache(self, mbti_personality: Optional[str] = None) -> int:
        """
        Invalidate tourist spots cache entries.
        
        Args:
            mbti_personality: Specific MBTI personality to invalidate (all if None)
            
        Returns:
            Number of entries invalidated
        """
        keys_to_remove = []
        
        for key in self._cache.keys():
            if "tourist_spots:" in key:
                if mbti_personality is None:
                    # Remove all tourist spots cache entries
                    keys_to_remove.append(key)
                else:
                    # Check if this entry matches the specific MBTI personality
                    if mbti_personality.upper() in key.upper():
                        keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self._cache[key]
        
        if keys_to_remove:
            personality_info = f" for {mbti_personality}" if mbti_personality else ""
            logger.info(f"Invalidated {len(keys_to_remove)} tourist spots cache entries{personality_info}")
        
        return len(keys_to_remove)
    
    def invalidate_itinerary_cache(self, mbti_personality: Optional[str] = None) -> int:
        """
        Invalidate complete itinerary cache entries.
        
        Args:
            mbti_personality: Specific MBTI personality to invalidate (all if None)
            
        Returns:
            Number of entries invalidated
        """
        keys_to_remove = []
        
        for key in self._cache.keys():
            if "itinerary:" in key:
                if mbti_personality is None:
                    # Remove all itinerary cache entries
                    keys_to_remove.append(key)
                else:
                    # Check if this entry matches the specific MBTI personality
                    if mbti_personality.upper() in key.upper():
                        keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self._cache[key]
        
        if keys_to_remove:
            personality_info = f" for {mbti_personality}" if mbti_personality else ""
            logger.info(f"Invalidated {len(keys_to_remove)} itinerary cache entries{personality_info}")
        
        return len(keys_to_remove)
    
    def invalidate_all_mbti_related_cache(self, mbti_personality: Optional[str] = None) -> Dict[str, int]:
        """
        Invalidate all MBTI-related cache entries (MBTI, tourist spots, and itineraries).
        
        Args:
            mbti_personality: Specific MBTI personality to invalidate (all if None)
            
        Returns:
            Dictionary with counts of invalidated entries by type
        """
        results = {
            "mbti_entries": self.invalidate_mbti_cache(mbti_personality),
            "tourist_spots_entries": self.invalidate_tourist_spots_cache(mbti_personality),
            "itinerary_entries": self.invalidate_itinerary_cache(mbti_personality)
        }
        
        total_invalidated = sum(results.values())
        personality_info = f" for {mbti_personality}" if mbti_personality else ""
        logger.info(f"Invalidated {total_invalidated} total MBTI-related cache entries{personality_info}")
        
        return results
    
    def _cleanup_expired_entries(self) -> None:
        """Clean up expired cache entries with enhanced logging."""
        now = datetime.utcnow()
        expired_keys = []
        
        for key, entry in self._cache.items():
            if now > entry["expires_at"]:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self._cache[key]
        
        if expired_keys:
            logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")
    
    def cleanup_least_recently_used(self, max_entries: int = 1000) -> int:
        """
        Clean up least recently used entries if cache size exceeds limit.
        
        Args:
            max_entries: Maximum number of entries to keep
            
        Returns:
            Number of entries removed
        """
        if len(self._cache) <= max_entries:
            return 0
        
        # Sort entries by last accessed time
        sorted_entries = sorted(
            self._cache.items(),
            key=lambda x: x[1].get("last_accessed", datetime.min)
        )
        
        # Remove oldest entries
        entries_to_remove = len(self._cache) - max_entries
        keys_to_remove = [entry[0] for entry in sorted_entries[:entries_to_remove]]
        
        for key in keys_to_remove:
            del self._cache[key]
        
        logger.info(f"Removed {len(keys_to_remove)} LRU cache entries")
        return len(keys_to_remove)