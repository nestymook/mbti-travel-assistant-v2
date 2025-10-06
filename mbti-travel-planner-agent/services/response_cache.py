"""
Response Cache Service

This module provides response caching for repeated queries to improve performance
and reduce load on AgentCore agents. It implements TTL-based caching with
configurable cache sizes and eviction policies.

Features:
- TTL-based cache expiration
- LRU eviction policy
- Thread-safe operations
- Cache statistics and monitoring
- Configurable cache sizes per operation type
- Cache key generation with content hashing
"""

import asyncio
import hashlib
import json
import logging
import time
import threading
from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Union, Callable, TypeVar, Generic
from enum import Enum

logger = logging.getLogger(__name__)

T = TypeVar('T')


class CacheEvictionPolicy(Enum):
    """Cache eviction policies."""
    LRU = "lru"  # Least Recently Used
    LFU = "lfu"  # Least Frequently Used
    TTL_ONLY = "ttl_only"  # Only TTL-based eviction


@dataclass
class CacheEntry(Generic[T]):
    """Cache entry with metadata."""
    value: T
    created_at: datetime
    expires_at: datetime
    access_count: int = 0
    last_accessed: datetime = field(default_factory=datetime.utcnow)
    
    def is_expired(self) -> bool:
        """Check if cache entry is expired."""
        return datetime.utcnow() >= self.expires_at
    
    def access(self) -> None:
        """Mark entry as accessed."""
        self.access_count += 1
        self.last_accessed = datetime.utcnow()
    
    def time_until_expiry(self) -> timedelta:
        """Get time until entry expires."""
        return self.expires_at - datetime.utcnow()


@dataclass
class CacheConfig:
    """Configuration for response cache."""
    default_ttl_seconds: int = 300  # 5 minutes
    max_cache_size: int = 1000
    eviction_policy: CacheEvictionPolicy = CacheEvictionPolicy.LRU
    cleanup_interval_seconds: int = 60  # 1 minute
    enable_statistics: bool = True
    
    # Operation-specific TTL settings
    operation_ttl_overrides: Dict[str, int] = field(default_factory=lambda: {
        "search_restaurants_by_district": 600,  # 10 minutes
        "search_restaurants_by_meal_type": 900,  # 15 minutes
        "search_restaurants_combined": 600,  # 10 minutes
        "get_recommendations": 300,  # 5 minutes
        "analyze_restaurant_sentiment": 1800,  # 30 minutes
    })
    
    # Operation-specific cache size limits
    operation_size_limits: Dict[str, int] = field(default_factory=lambda: {
        "search_restaurants_by_district": 200,
        "search_restaurants_by_meal_type": 100,
        "search_restaurants_combined": 300,
        "get_recommendations": 500,
        "analyze_restaurant_sentiment": 200,
    })


@dataclass
class CacheStatistics:
    """Cache performance statistics."""
    total_requests: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    cache_evictions: int = 0
    cache_cleanups: int = 0
    total_entries: int = 0
    memory_usage_bytes: int = 0
    
    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate."""
        if self.total_requests == 0:
            return 0.0
        return self.cache_hits / self.total_requests
    
    @property
    def miss_rate(self) -> float:
        """Calculate cache miss rate."""
        return 1.0 - self.hit_rate
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert statistics to dictionary."""
        return {
            "total_requests": self.total_requests,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "cache_evictions": self.cache_evictions,
            "cache_cleanups": self.cache_cleanups,
            "total_entries": self.total_entries,
            "memory_usage_bytes": self.memory_usage_bytes,
            "hit_rate": self.hit_rate,
            "miss_rate": self.miss_rate
        }


class ResponseCache:
    """
    Thread-safe response cache with TTL and configurable eviction policies.
    
    This cache is designed to store responses from AgentCore agents to improve
    performance for repeated queries. It supports different TTL values for
    different operation types and implements LRU eviction.
    """
    
    def __init__(self, config: Optional[CacheConfig] = None):
        """
        Initialize response cache.
        
        Args:
            config: Cache configuration
        """
        self.config = config or CacheConfig()
        
        # Thread-safe cache storage
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = threading.RLock()
        
        # Statistics tracking
        self.stats = CacheStatistics() if self.config.enable_statistics else None
        
        # Background cleanup task
        self._cleanup_task: Optional[asyncio.Task] = None
        self._cleanup_running = False
        
        logger.info(f"Response cache initialized with max size: {self.config.max_cache_size}")
        
        # Start background cleanup if in async context
        try:
            loop = asyncio.get_running_loop()
            self._start_cleanup_task()
        except RuntimeError:
            # No event loop running, cleanup will be manual
            logger.debug("No event loop running, background cleanup disabled")
    
    def _start_cleanup_task(self):
        """Start background cleanup task."""
        if not self._cleanup_running:
            self._cleanup_running = True
            self._cleanup_task = asyncio.create_task(self._background_cleanup())
            logger.debug("Background cache cleanup task started")
    
    async def _background_cleanup(self):
        """Background task to clean up expired entries."""
        while self._cleanup_running:
            try:
                await asyncio.sleep(self.config.cleanup_interval_seconds)
                self._cleanup_expired_entries()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in background cache cleanup: {e}")
        
        logger.debug("Background cache cleanup task stopped")
    
    def _cleanup_expired_entries(self):
        """Clean up expired cache entries."""
        with self._lock:
            expired_keys = []
            
            for key, entry in self._cache.items():
                if entry.is_expired():
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self._cache[key]
                if self.stats:
                    self.stats.cache_cleanups += 1
            
            if expired_keys:
                logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")
    
    def _generate_cache_key(
        self, 
        operation: str, 
        parameters: Dict[str, Any],
        agent_arn: Optional[str] = None
    ) -> str:
        """
        Generate cache key for operation and parameters.
        
        Args:
            operation: Operation name
            parameters: Operation parameters
            agent_arn: Optional agent ARN
            
        Returns:
            Cache key string
        """
        # Create a deterministic representation of parameters
        param_str = json.dumps(parameters, sort_keys=True, ensure_ascii=False)
        
        # Include agent ARN if provided
        if agent_arn:
            key_data = f"{operation}:{agent_arn}:{param_str}"
        else:
            key_data = f"{operation}:{param_str}"
        
        # Generate hash for consistent key length
        key_hash = hashlib.sha256(key_data.encode('utf-8')).hexdigest()[:16]
        
        return f"{operation}:{key_hash}"
    
    def _get_ttl_for_operation(self, operation: str) -> int:
        """Get TTL for specific operation."""
        return self.config.operation_ttl_overrides.get(
            operation, 
            self.config.default_ttl_seconds
        )
    
    def _enforce_size_limit(self, operation: str):
        """Enforce cache size limits using eviction policy."""
        with self._lock:
            # Get operation-specific size limit
            operation_limit = self.config.operation_size_limits.get(operation)
            total_limit = self.config.max_cache_size
            
            # Count entries for this operation
            operation_entries = [
                key for key in self._cache.keys() 
                if key.startswith(f"{operation}:")
            ]
            
            # Check operation-specific limit
            if operation_limit and len(operation_entries) > operation_limit:
                excess = len(operation_entries) - operation_limit
                self._evict_entries(operation_entries[:excess])
            
            # Check total cache size limit
            if len(self._cache) > total_limit:
                excess = len(self._cache) - total_limit
                all_keys = list(self._cache.keys())
                self._evict_entries(all_keys[:excess])
    
    def _evict_entries(self, keys_to_evict: list):
        """Evict specified cache entries."""
        for key in keys_to_evict:
            if key in self._cache:
                del self._cache[key]
                if self.stats:
                    self.stats.cache_evictions += 1
        
        if keys_to_evict:
            logger.debug(f"Evicted {len(keys_to_evict)} cache entries")
    
    async def get(
        self, 
        operation: str, 
        parameters: Dict[str, Any],
        agent_arn: Optional[str] = None
    ) -> Optional[Any]:
        """
        Get cached response for operation and parameters.
        
        Args:
            operation: Operation name
            parameters: Operation parameters
            agent_arn: Optional agent ARN
            
        Returns:
            Cached response or None if not found/expired
        """
        cache_key = self._generate_cache_key(operation, parameters, agent_arn)
        
        with self._lock:
            if self.stats:
                self.stats.total_requests += 1
            
            if cache_key not in self._cache:
                if self.stats:
                    self.stats.cache_misses += 1
                return None
            
            entry = self._cache[cache_key]
            
            # Check if entry is expired
            if entry.is_expired():
                del self._cache[cache_key]
                if self.stats:
                    self.stats.cache_misses += 1
                    self.stats.cache_cleanups += 1
                return None
            
            # Mark as accessed and move to end (LRU)
            entry.access()
            self._cache.move_to_end(cache_key)
            
            if self.stats:
                self.stats.cache_hits += 1
            
            logger.debug(f"Cache hit for operation: {operation}")
            return entry.value
    
    async def set(
        self, 
        operation: str, 
        parameters: Dict[str, Any], 
        value: Any,
        agent_arn: Optional[str] = None,
        ttl_override: Optional[int] = None
    ) -> None:
        """
        Cache response for operation and parameters.
        
        Args:
            operation: Operation name
            parameters: Operation parameters
            value: Response value to cache
            agent_arn: Optional agent ARN
            ttl_override: Optional TTL override in seconds
        """
        cache_key = self._generate_cache_key(operation, parameters, agent_arn)
        
        # Determine TTL
        ttl_seconds = ttl_override or self._get_ttl_for_operation(operation)
        
        # Create cache entry
        now = datetime.utcnow()
        entry = CacheEntry(
            value=value,
            created_at=now,
            expires_at=now + timedelta(seconds=ttl_seconds)
        )
        
        with self._lock:
            # Add to cache
            self._cache[cache_key] = entry
            self._cache.move_to_end(cache_key)  # Mark as most recently used
            
            if self.stats:
                self.stats.total_entries = len(self._cache)
            
            # Enforce size limits
            self._enforce_size_limit(operation)
        
        logger.debug(f"Cached response for operation: {operation} (TTL: {ttl_seconds}s)")
    
    async def get_or_compute(
        self, 
        operation: str, 
        parameters: Dict[str, Any], 
        compute_func: Callable[[], Any],
        agent_arn: Optional[str] = None,
        ttl_override: Optional[int] = None
    ) -> Any:
        """
        Get cached response or compute and cache new response.
        
        Args:
            operation: Operation name
            parameters: Operation parameters
            compute_func: Function to compute response if not cached
            agent_arn: Optional agent ARN
            ttl_override: Optional TTL override in seconds
            
        Returns:
            Cached or computed response
        """
        # Try to get from cache first
        cached_result = await self.get(operation, parameters, agent_arn)
        if cached_result is not None:
            return cached_result
        
        # Compute new result
        result = await compute_func()
        
        # Cache the result
        await self.set(operation, parameters, result, agent_arn, ttl_override)
        
        return result
    
    def invalidate(
        self, 
        operation: Optional[str] = None, 
        parameters: Optional[Dict[str, Any]] = None,
        agent_arn: Optional[str] = None
    ) -> int:
        """
        Invalidate cache entries.
        
        Args:
            operation: Optional operation name to invalidate
            parameters: Optional specific parameters to invalidate
            agent_arn: Optional agent ARN to invalidate
            
        Returns:
            Number of entries invalidated
        """
        with self._lock:
            if operation and parameters:
                # Invalidate specific entry
                cache_key = self._generate_cache_key(operation, parameters, agent_arn)
                if cache_key in self._cache:
                    del self._cache[cache_key]
                    return 1
                return 0
            
            elif operation:
                # Invalidate all entries for operation
                keys_to_remove = [
                    key for key in self._cache.keys() 
                    if key.startswith(f"{operation}:")
                ]
                for key in keys_to_remove:
                    del self._cache[key]
                return len(keys_to_remove)
            
            else:
                # Invalidate all entries
                count = len(self._cache)
                self._cache.clear()
                return count
    
    def get_statistics(self) -> Optional[Dict[str, Any]]:
        """Get cache statistics."""
        if not self.stats:
            return None
        
        with self._lock:
            # Update current stats
            self.stats.total_entries = len(self._cache)
            
            # Estimate memory usage (rough approximation)
            self.stats.memory_usage_bytes = sum(
                len(str(entry.value)) + len(key) + 200  # Rough overhead estimate
                for key, entry in self._cache.items()
            )
            
            return self.stats.to_dict()
    
    def get_cache_info(self) -> Dict[str, Any]:
        """Get detailed cache information."""
        with self._lock:
            operation_counts = {}
            expired_count = 0
            
            for key, entry in self._cache.items():
                operation = key.split(':')[0]
                operation_counts[operation] = operation_counts.get(operation, 0) + 1
                
                if entry.is_expired():
                    expired_count += 1
            
            return {
                "total_entries": len(self._cache),
                "expired_entries": expired_count,
                "operation_counts": operation_counts,
                "config": {
                    "max_cache_size": self.config.max_cache_size,
                    "default_ttl_seconds": self.config.default_ttl_seconds,
                    "eviction_policy": self.config.eviction_policy.value,
                    "cleanup_interval_seconds": self.config.cleanup_interval_seconds
                }
            }
    
    async def close(self):
        """Close cache and cleanup resources."""
        self._cleanup_running = False
        
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        with self._lock:
            self._cache.clear()
        
        logger.info("Response cache closed")
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()


# Global cache instance
_global_cache: Optional[ResponseCache] = None


def get_response_cache(config: Optional[CacheConfig] = None) -> ResponseCache:
    """
    Get global response cache instance.
    
    Args:
        config: Optional cache configuration
        
    Returns:
        ResponseCache instance
    """
    global _global_cache
    
    if _global_cache is None:
        _global_cache = ResponseCache(config)
    
    return _global_cache


def configure_response_cache(config: CacheConfig) -> ResponseCache:
    """
    Configure global response cache with new settings.
    
    Args:
        config: New cache configuration
        
    Returns:
        New ResponseCache instance
    """
    global _global_cache
    
    # Close existing cache if it exists
    if _global_cache is not None:
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(_global_cache.close())
        except RuntimeError:
            pass
    
    _global_cache = ResponseCache(config)
    return _global_cache


# Export main classes and functions
__all__ = [
    'ResponseCache',
    'CacheConfig',
    'CacheStatistics',
    'CacheEvictionPolicy',
    'get_response_cache',
    'configure_response_cache'
]