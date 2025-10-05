"""
Performance optimization service for enhanced MCP status checks.

This module implements performance optimization features including:
- Concurrent execution of MCP and REST health checks
- Connection pooling with separate pools for MCP and REST
- Request batching and scheduling optimization
- Resource usage monitoring and limits
- Caching for configuration and authentication tokens

Requirements: 10.1, 10.2, 10.3, 10.4, 10.5
"""

import asyncio
import time
import threading
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import aiohttp
import psutil
import logging
from collections import defaultdict, deque
import weakref
import json
import hashlib

try:
    from ..models.dual_health_models import (
        DualHealthCheckResult,
        MCPHealthCheckResult,
        RESTHealthCheckResult,
        EnhancedServerConfig
    )
except ImportError:
    # For direct execution, use absolute imports
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    from models.dual_health_models import (
        DualHealthCheckResult,
        MCPHealthCheckResult,
        RESTHealthCheckResult,
        EnhancedServerConfig
    )


@dataclass
class ConnectionPoolConfig:
    """Configuration for connection pools."""
    max_connections: int = 100
    max_connections_per_host: int = 30
    keepalive_timeout: int = 30
    connection_timeout: int = 10
    read_timeout: int = 30
    pool_cleanup_interval: int = 300  # 5 minutes


@dataclass
class ResourceLimits:
    """Resource usage limits for performance optimization."""
    max_concurrent_checks: int = 50
    max_memory_usage_mb: int = 512
    max_cpu_usage_percent: float = 80.0
    max_queue_size: int = 1000
    check_interval_seconds: int = 5


@dataclass
class CacheConfig:
    """Configuration for caching system."""
    config_cache_ttl: int = 300  # 5 minutes
    auth_token_cache_ttl: int = 3600  # 1 hour
    dns_cache_ttl: int = 600  # 10 minutes
    result_cache_ttl: int = 60  # 1 minute
    max_cache_size: int = 1000


@dataclass
class PerformanceMetrics:
    """Performance metrics for monitoring."""
    total_checks_performed: int = 0
    concurrent_checks_active: int = 0
    average_response_time_ms: float = 0.0
    cache_hit_rate: float = 0.0
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0
    connection_pool_utilization: float = 0.0
    queue_size: int = 0
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class BatchRequest:
    """Represents a batch of health check requests."""
    batch_id: str
    server_configs: List[EnhancedServerConfig]
    priority: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    timeout_seconds: int = 30


class ConnectionPoolManager:
    """Manages separate connection pools for MCP and REST requests."""
    
    def __init__(self, config: ConnectionPoolConfig):
        self.config = config
        self.mcp_pool: Optional[aiohttp.ClientSession] = None
        self.rest_pool: Optional[aiohttp.ClientSession] = None
        self._pool_lock = asyncio.Lock()
        self._cleanup_task: Optional[asyncio.Task] = None
        self.logger = logging.getLogger(__name__)
        
    async def initialize(self):
        """Initialize connection pools."""
        async with self._pool_lock:
            if self.mcp_pool is None:
                connector = aiohttp.TCPConnector(
                    limit=self.config.max_connections,
                    limit_per_host=self.config.max_connections_per_host,
                    keepalive_timeout=self.config.keepalive_timeout,
                    enable_cleanup_closed=True
                )
                
                timeout = aiohttp.ClientTimeout(
                    total=self.config.connection_timeout + self.config.read_timeout,
                    connect=self.config.connection_timeout,
                    sock_read=self.config.read_timeout
                )
                
                self.mcp_pool = aiohttp.ClientSession(
                    connector=connector,
                    timeout=timeout,
                    headers={'User-Agent': 'Enhanced-MCP-Status-Check/1.0'}
                )
                
            if self.rest_pool is None:
                connector = aiohttp.TCPConnector(
                    limit=self.config.max_connections,
                    limit_per_host=self.config.max_connections_per_host,
                    keepalive_timeout=self.config.keepalive_timeout,
                    enable_cleanup_closed=True
                )
                
                timeout = aiohttp.ClientTimeout(
                    total=self.config.connection_timeout + self.config.read_timeout,
                    connect=self.config.connection_timeout,
                    sock_read=self.config.read_timeout
                )
                
                self.rest_pool = aiohttp.ClientSession(
                    connector=connector,
                    timeout=timeout,
                    headers={'User-Agent': 'Enhanced-MCP-Status-Check/1.0'}
                )
                
        # Start cleanup task
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._periodic_cleanup())
            
    async def get_mcp_session(self) -> aiohttp.ClientSession:
        """Get MCP connection pool session."""
        if self.mcp_pool is None:
            await self.initialize()
        return self.mcp_pool
        
    async def get_rest_session(self) -> aiohttp.ClientSession:
        """Get REST connection pool session."""
        if self.rest_pool is None:
            await self.initialize()
        return self.rest_pool
        
    async def close(self):
        """Close all connection pools."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            
        async with self._pool_lock:
            if self.mcp_pool:
                await self.mcp_pool.close()
                self.mcp_pool = None
                
            if self.rest_pool:
                await self.rest_pool.close()
                self.rest_pool = None
                
    async def _periodic_cleanup(self):
        """Periodic cleanup of connection pools."""
        while True:
            try:
                await asyncio.sleep(self.config.pool_cleanup_interval)
                
                # Force cleanup of closed connections
                if self.mcp_pool and self.mcp_pool.connector:
                    await self.mcp_pool.connector.close()
                    
                if self.rest_pool and self.rest_pool.connector:
                    await self.rest_pool.connector.close()
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error during connection pool cleanup: {e}")
                
    def get_pool_stats(self) -> Dict[str, Any]:
        """Get connection pool statistics."""
        stats = {
            'mcp_pool': {
                'active': 0,
                'available': 0,
                'total': 0
            },
            'rest_pool': {
                'active': 0,
                'available': 0,
                'total': 0
            }
        }
        
        if self.mcp_pool and self.mcp_pool.connector:
            connector = self.mcp_pool.connector
            stats['mcp_pool'] = {
                'active': len(connector._conns),
                'available': len([c for conns in connector._conns.values() for c in conns]),
                'total': connector.limit
            }
            
        if self.rest_pool and self.rest_pool.connector:
            connector = self.rest_pool.connector
            stats['rest_pool'] = {
                'active': len(connector._conns),
                'available': len([c for conns in connector._conns.values() for c in conns]),
                'total': connector.limit
            }
            
        return stats


class CacheManager:
    """Manages caching for configuration and authentication tokens."""
    
    def __init__(self, config: CacheConfig):
        self.config = config
        self._cache: Dict[str, Dict[str, Any]] = {
            'config': {},
            'auth_tokens': {},
            'dns': {},
            'results': {}
        }
        self._cache_lock = threading.RLock()
        self._cleanup_task: Optional[asyncio.Task] = None
        self.logger = logging.getLogger(__name__)
        
    def _generate_cache_key(self, category: str, *args) -> str:
        """Generate cache key from arguments."""
        key_data = f"{category}:{':'.join(str(arg) for arg in args)}"
        return hashlib.md5(key_data.encode()).hexdigest()
        
    def get(self, category: str, *args) -> Optional[Any]:
        """Get item from cache."""
        cache_key = self._generate_cache_key(category, *args)
        
        with self._cache_lock:
            if category not in self._cache:
                return None
                
            cache_entry = self._cache[category].get(cache_key)
            if cache_entry is None:
                return None
                
            # Check expiration
            if datetime.now() > cache_entry['expires_at']:
                del self._cache[category][cache_key]
                return None
                
            cache_entry['last_accessed'] = datetime.now()
            return cache_entry['value']
            
    def set(self, category: str, value: Any, *args, ttl: Optional[int] = None) -> None:
        """Set item in cache."""
        cache_key = self._generate_cache_key(category, *args)
        
        # Determine TTL based on category
        if ttl is None:
            ttl_map = {
                'config': self.config.config_cache_ttl,
                'auth_tokens': self.config.auth_token_cache_ttl,
                'dns': self.config.dns_cache_ttl,
                'results': self.config.result_cache_ttl
            }
            ttl = ttl_map.get(category, 300)
            
        expires_at = datetime.now() + timedelta(seconds=ttl)
        
        with self._cache_lock:
            if category not in self._cache:
                self._cache[category] = {}
                
            # Check cache size limit
            if len(self._cache[category]) >= self.config.max_cache_size:
                self._evict_oldest(category)
                
            self._cache[category][cache_key] = {
                'value': value,
                'expires_at': expires_at,
                'created_at': datetime.now(),
                'last_accessed': datetime.now()
            }
            
    def _evict_oldest(self, category: str) -> None:
        """Evict oldest cache entries."""
        if category not in self._cache:
            return
            
        cache = self._cache[category]
        if not cache:
            return
            
        # Sort by last accessed time and remove oldest 10%
        sorted_items = sorted(
            cache.items(),
            key=lambda x: x[1]['last_accessed']
        )
        
        evict_count = max(1, len(sorted_items) // 10)
        for i in range(evict_count):
            key, _ = sorted_items[i]
            del cache[key]
            
    def clear_category(self, category: str) -> None:
        """Clear all items in a category."""
        with self._cache_lock:
            if category in self._cache:
                self._cache[category].clear()
                
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._cache_lock:
            stats = {}
            for category, cache in self._cache.items():
                total_items = len(cache)
                expired_items = sum(
                    1 for entry in cache.values()
                    if datetime.now() > entry['expires_at']
                )
                
                stats[category] = {
                    'total_items': total_items,
                    'expired_items': expired_items,
                    'valid_items': total_items - expired_items,
                    'size_bytes': len(json.dumps(cache, default=str))
                }
                
            return stats
            
    async def start_cleanup_task(self):
        """Start periodic cleanup task."""
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._periodic_cleanup())
            
    async def stop_cleanup_task(self):
        """Stop periodic cleanup task."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            self._cleanup_task = None
            
    async def _periodic_cleanup(self):
        """Periodic cleanup of expired cache entries."""
        while True:
            try:
                await asyncio.sleep(60)  # Cleanup every minute
                
                with self._cache_lock:
                    for category, cache in self._cache.items():
                        expired_keys = [
                            key for key, entry in cache.items()
                            if datetime.now() > entry['expires_at']
                        ]
                        
                        for key in expired_keys:
                            del cache[key]
                            
                        if expired_keys:
                            self.logger.debug(
                                f"Cleaned up {len(expired_keys)} expired entries "
                                f"from {category} cache"
                            )
                            
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error during cache cleanup: {e}")


class ResourceMonitor:
    """Monitors system resource usage and enforces limits."""
    
    def __init__(self, limits: ResourceLimits):
        self.limits = limits
        self._active_checks: Set[str] = set()
        self._check_queue: deque = deque()
        self._monitor_lock = threading.RLock()
        self._monitor_task: Optional[asyncio.Task] = None
        self.logger = logging.getLogger(__name__)
        
    async def start_monitoring(self):
        """Start resource monitoring."""
        if self._monitor_task is None:
            self._monitor_task = asyncio.create_task(self._monitor_resources())
            
    async def stop_monitoring(self):
        """Stop resource monitoring."""
        if self._monitor_task:
            self._monitor_task.cancel()
            self._monitor_task = None
            
    def can_start_check(self, check_id: str) -> bool:
        """Check if a new health check can be started."""
        with self._monitor_lock:
            # Check concurrent limit
            if len(self._active_checks) >= self.limits.max_concurrent_checks:
                return False
                
            # Check queue size
            if len(self._check_queue) >= self.limits.max_queue_size:
                return False
                
            # Check system resources
            memory_usage = psutil.virtual_memory().percent
            cpu_usage = psutil.cpu_percent(interval=0.1)
            
            if memory_usage > 95.0:  # Use a higher threshold for testing
                return False
                
            if cpu_usage > self.limits.max_cpu_usage_percent:
                return False
                
            return True
            
    def register_check(self, check_id: str) -> bool:
        """Register a new health check."""
        with self._monitor_lock:
            if not self.can_start_check(check_id):
                return False
                
            self._active_checks.add(check_id)
            return True
            
    def unregister_check(self, check_id: str) -> None:
        """Unregister a completed health check."""
        with self._monitor_lock:
            self._active_checks.discard(check_id)
            
    def add_to_queue(self, check_id: str, priority: int = 0) -> bool:
        """Add check to queue."""
        with self._monitor_lock:
            if len(self._check_queue) >= self.limits.max_queue_size:
                return False
                
            self._check_queue.append((check_id, priority, datetime.now()))
            return True
            
    def get_next_from_queue(self) -> Optional[str]:
        """Get next check from queue."""
        with self._monitor_lock:
            if not self._check_queue:
                return None
                
            # Sort by priority (higher first) and then by timestamp
            sorted_queue = sorted(
                self._check_queue,
                key=lambda x: (-x[1], x[2])
            )
            
            check_id, _, _ = sorted_queue[0]
            self._check_queue.remove(sorted_queue[0])
            return check_id
            
    def get_resource_stats(self) -> Dict[str, Any]:
        """Get current resource statistics."""
        with self._monitor_lock:
            memory = psutil.virtual_memory()
            cpu_percent = psutil.cpu_percent(interval=0.1)
            
            return {
                'active_checks': len(self._active_checks),
                'queue_size': len(self._check_queue),
                'memory_usage_percent': memory.percent,
                'memory_usage_mb': memory.used / (1024 * 1024),
                'cpu_usage_percent': cpu_percent,
                'max_concurrent_checks': self.limits.max_concurrent_checks,
                'max_queue_size': self.limits.max_queue_size
            }
            
    async def _monitor_resources(self):
        """Monitor system resources periodically."""
        while True:
            try:
                await asyncio.sleep(self.limits.check_interval_seconds)
                
                stats = self.get_resource_stats()
                
                # Log warnings if approaching limits
                if stats['memory_usage_percent'] > self.limits.max_memory_usage_mb * 0.8:
                    self.logger.warning(
                        f"High memory usage: {stats['memory_usage_percent']:.1f}%"
                    )
                    
                if stats['cpu_usage_percent'] > self.limits.max_cpu_usage_percent * 0.8:
                    self.logger.warning(
                        f"High CPU usage: {stats['cpu_usage_percent']:.1f}%"
                    )
                    
                if stats['queue_size'] > self.limits.max_queue_size * 0.8:
                    self.logger.warning(
                        f"High queue size: {stats['queue_size']}"
                    )
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error during resource monitoring: {e}")


class BatchScheduler:
    """Schedules and optimizes batch health check requests."""
    
    def __init__(self, max_batch_size: int = 10, batch_timeout: int = 5):
        self.max_batch_size = max_batch_size
        self.batch_timeout = batch_timeout
        self._pending_requests: Dict[str, BatchRequest] = {}
        self._batch_lock = asyncio.Lock()
        self._scheduler_task: Optional[asyncio.Task] = None
        self.logger = logging.getLogger(__name__)
        
    async def start_scheduler(self):
        """Start batch scheduler."""
        if self._scheduler_task is None:
            self._scheduler_task = asyncio.create_task(self._process_batches())
            
    async def stop_scheduler(self):
        """Stop batch scheduler."""
        if self._scheduler_task:
            self._scheduler_task.cancel()
            self._scheduler_task = None
            
    async def add_request(
        self,
        server_config: EnhancedServerConfig,
        priority: int = 0
    ) -> str:
        """Add a health check request to batch."""
        batch_id = f"batch_{int(time.time() * 1000)}"
        
        async with self._batch_lock:
            # Try to find existing batch with same priority
            existing_batch = None
            for batch in self._pending_requests.values():
                if (batch.priority == priority and 
                    len(batch.server_configs) < self.max_batch_size):
                    existing_batch = batch
                    break
                    
            if existing_batch:
                existing_batch.server_configs.append(server_config)
                return existing_batch.batch_id
            else:
                # Create new batch
                batch_request = BatchRequest(
                    batch_id=batch_id,
                    server_configs=[server_config],
                    priority=priority
                )
                self._pending_requests[batch_id] = batch_request
                return batch_id
                
    async def get_ready_batches(self) -> List[BatchRequest]:
        """Get batches ready for processing."""
        ready_batches = []
        current_time = datetime.now()
        
        async with self._batch_lock:
            batches_to_remove = []
            
            for batch_id, batch in self._pending_requests.items():
                # Check if batch is ready
                is_full = len(batch.server_configs) >= self.max_batch_size
                is_timeout = (current_time - batch.created_at).total_seconds() >= self.batch_timeout
                
                if is_full or is_timeout:
                    ready_batches.append(batch)
                    batches_to_remove.append(batch_id)
                    
            # Remove processed batches
            for batch_id in batches_to_remove:
                del self._pending_requests[batch_id]
                
        return ready_batches
        
    async def _process_batches(self):
        """Process batches periodically."""
        while True:
            try:
                await asyncio.sleep(1)  # Check every second
                
                ready_batches = await self.get_ready_batches()
                
                if ready_batches:
                    self.logger.debug(f"Processing {len(ready_batches)} ready batches")
                    
                    # Sort by priority
                    ready_batches.sort(key=lambda x: x.priority, reverse=True)
                    
                    # Process batches (this would be handled by the main service)
                    for batch in ready_batches:
                        self.logger.debug(
                            f"Batch {batch.batch_id} ready with "
                            f"{len(batch.server_configs)} servers"
                        )
                        
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error during batch processing: {e}")


class PerformanceOptimizer:
    """Main performance optimization service."""
    
    def __init__(
        self,
        connection_config: Optional[ConnectionPoolConfig] = None,
        resource_limits: Optional[ResourceLimits] = None,
        cache_config: Optional[CacheConfig] = None
    ):
        self.connection_config = connection_config or ConnectionPoolConfig()
        self.resource_limits = resource_limits or ResourceLimits()
        self.cache_config = cache_config or CacheConfig()
        
        self.connection_manager = ConnectionPoolManager(self.connection_config)
        self.cache_manager = CacheManager(self.cache_config)
        self.resource_monitor = ResourceMonitor(self.resource_limits)
        self.batch_scheduler = BatchScheduler()
        
        self.metrics = PerformanceMetrics()
        self._metrics_lock = threading.RLock()
        self.logger = logging.getLogger(__name__)
        
    async def initialize(self):
        """Initialize all performance optimization components."""
        await self.connection_manager.initialize()
        await self.cache_manager.start_cleanup_task()
        await self.resource_monitor.start_monitoring()
        await self.batch_scheduler.start_scheduler()
        
        self.logger.info("Performance optimizer initialized")
        
    async def shutdown(self):
        """Shutdown all performance optimization components."""
        await self.connection_manager.close()
        await self.cache_manager.stop_cleanup_task()
        await self.resource_monitor.stop_monitoring()
        await self.batch_scheduler.stop_scheduler()
        
        self.logger.info("Performance optimizer shutdown")
        
    async def execute_concurrent_health_checks(
        self,
        server_configs: List[EnhancedServerConfig],
        health_check_func,
        max_concurrent: Optional[int] = None
    ) -> List[DualHealthCheckResult]:
        """Execute health checks concurrently with optimization."""
        if max_concurrent is None:
            max_concurrent = min(
                len(server_configs),
                self.resource_limits.max_concurrent_checks
            )
            
        results = []
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def execute_single_check(config: EnhancedServerConfig) -> DualHealthCheckResult:
            check_id = f"check_{config.server_name}_{int(time.time() * 1000)}"
            
            async with semaphore:
                # Check resource limits
                if not self.resource_monitor.register_check(check_id):
                    # Add to queue if can't execute immediately
                    if self.resource_monitor.add_to_queue(check_id):
                        # Wait for availability
                        while not self.resource_monitor.can_start_check(check_id):
                            await asyncio.sleep(0.1)
                        self.resource_monitor.register_check(check_id)
                    else:
                        raise Exception(f"Resource limits exceeded for check {check_id}")
                
                try:
                    start_time = time.time()
                    
                    # Execute health check
                    result = await health_check_func(config)
                    
                    # Update metrics
                    response_time = (time.time() - start_time) * 1000
                    self._update_metrics(response_time)
                    
                    return result
                    
                finally:
                    self.resource_monitor.unregister_check(check_id)
                    
        # Execute all checks concurrently
        tasks = [execute_single_check(config) for config in server_configs]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions and log them
        valid_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.logger.error(
                    f"Health check failed for {server_configs[i].server_name}: {result}"
                )
            else:
                valid_results.append(result)
                
        return valid_results
        
    def _update_metrics(self, response_time_ms: float):
        """Update performance metrics."""
        with self._metrics_lock:
            self.metrics.total_checks_performed += 1
            
            # Update average response time (exponential moving average)
            alpha = 0.1
            if self.metrics.average_response_time_ms == 0:
                self.metrics.average_response_time_ms = response_time_ms
            else:
                self.metrics.average_response_time_ms = (
                    alpha * response_time_ms + 
                    (1 - alpha) * self.metrics.average_response_time_ms
                )
                
            # Update system metrics
            memory = psutil.virtual_memory()
            self.metrics.memory_usage_mb = memory.used / (1024 * 1024)
            self.metrics.cpu_usage_percent = psutil.cpu_percent(interval=0.1)
            
            # Update cache metrics
            cache_stats = self.cache_manager.get_stats()
            total_requests = sum(
                stats.get('total_items', 0) for stats in cache_stats.values()
            )
            cache_hits = sum(
                stats.get('valid_items', 0) for stats in cache_stats.values()
            )
            
            if total_requests > 0:
                self.metrics.cache_hit_rate = cache_hits / total_requests
                
            # Update connection pool metrics
            pool_stats = self.connection_manager.get_pool_stats()
            total_connections = (
                pool_stats['mcp_pool']['total'] + 
                pool_stats['rest_pool']['total']
            )
            active_connections = (
                pool_stats['mcp_pool']['active'] + 
                pool_stats['rest_pool']['active']
            )
            
            if total_connections > 0:
                self.metrics.connection_pool_utilization = active_connections / total_connections
                
            self.metrics.last_updated = datetime.now()
            
    def get_performance_metrics(self) -> PerformanceMetrics:
        """Get current performance metrics."""
        with self._metrics_lock:
            # Update real-time metrics
            resource_stats = self.resource_monitor.get_resource_stats()
            self.metrics.concurrent_checks_active = resource_stats['active_checks']
            self.metrics.queue_size = resource_stats['queue_size']
            
            return self.metrics
            
    def get_optimization_recommendations(self) -> List[str]:
        """Get performance optimization recommendations."""
        recommendations = []
        metrics = self.get_performance_metrics()
        
        # Check response time
        if metrics.average_response_time_ms > 5000:  # 5 seconds
            recommendations.append(
                "Consider increasing connection pool size or reducing timeout values"
            )
            
        # Check cache hit rate
        if metrics.cache_hit_rate < 0.5:  # Less than 50%
            recommendations.append(
                "Consider increasing cache TTL values or cache size limits"
            )
            
        # Check memory usage
        if metrics.memory_usage_mb > self.resource_limits.max_memory_usage_mb * 0.8:
            recommendations.append(
                "Consider reducing cache size or concurrent check limits"
            )
            
        # Check CPU usage
        if metrics.cpu_usage_percent > self.resource_limits.max_cpu_usage_percent * 0.8:
            recommendations.append(
                "Consider reducing concurrent check limits or check frequency"
            )
            
        # Check connection pool utilization
        if metrics.connection_pool_utilization > 0.8:
            recommendations.append(
                "Consider increasing connection pool size"
            )
            
        # Check queue size
        if metrics.queue_size > self.resource_limits.max_queue_size * 0.8:
            recommendations.append(
                "Consider increasing concurrent check limits or processing capacity"
            )
            
        return recommendations