"""
System Resilience Service

This module provides comprehensive system resilience features including
graceful degradation for service failures, caching for frequently requested data,
and comprehensive error logging and monitoring.

Requirements: 9.4, 9.5, 9.7
"""

import asyncio
import json
import time
import logging
from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime, timedelta
import hashlib
import pickle
from pathlib import Path

try:
    import structlog
    logger = structlog.get_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


class ServiceStatus(Enum):
    """Service status levels for degradation management."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    CRITICAL = "critical"
    UNAVAILABLE = "unavailable"


class CacheStrategy(Enum):
    """Cache strategies for different data types."""
    LRU = "lru"  # Least Recently Used
    TTL = "ttl"  # Time To Live
    HYBRID = "hybrid"  # LRU + TTL


@dataclass
class ServiceHealth:
    """Service health information."""
    service_name: str
    status: ServiceStatus
    last_check: datetime
    error_count: int
    success_count: int
    response_time_ms: float
    error_rate: float
    uptime_percentage: float
    last_error: Optional[str] = None


@dataclass
class CacheEntry:
    """Cache entry with metadata."""
    key: str
    data: Any
    created_at: datetime
    last_accessed: datetime
    access_count: int
    ttl_seconds: Optional[int] = None
    size_bytes: int = 0


@dataclass
class DegradationConfig:
    """Configuration for service degradation."""
    error_threshold: int = 5
    error_window_minutes: int = 5
    recovery_threshold: int = 3
    max_degradation_time_minutes: int = 30
    enable_circuit_breaker: bool = True
    circuit_breaker_timeout_seconds: int = 60


@dataclass
class CacheConfig:
    """Configuration for caching system."""
    max_size_mb: int = 100
    default_ttl_seconds: int = 300
    cleanup_interval_seconds: int = 60
    strategy: CacheStrategy = CacheStrategy.HYBRID
    enable_persistence: bool = True
    persistence_path: str = "cache"


class SystemResilienceService:
    """
    Service providing comprehensive system resilience features.
    
    This service implements:
    - Graceful degradation for service failures
    - Intelligent caching with multiple strategies
    - Comprehensive error logging and monitoring
    - Circuit breaker patterns
    - Health monitoring and alerting
    """
    
    def __init__(
        self,
        degradation_config: Optional[DegradationConfig] = None,
        cache_config: Optional[CacheConfig] = None
    ):
        """Initialize system resilience service.
        
        Args:
            degradation_config: Configuration for service degradation
            cache_config: Configuration for caching system
        """
        self.degradation_config = degradation_config or DegradationConfig()
        self.cache_config = cache_config or CacheConfig()
        
        # Service health tracking
        self._service_health: Dict[str, ServiceHealth] = {}
        self._circuit_breakers: Dict[str, Dict[str, Any]] = {}
        
        # Caching system
        self._cache: Dict[str, CacheEntry] = {}
        self._cache_stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'size_bytes': 0
        }
        
        # Error tracking and monitoring
        self._error_log: List[Dict[str, Any]] = []
        self._performance_metrics: Dict[str, List[float]] = {}
        
        # Background tasks
        self._cleanup_task: Optional[asyncio.Task] = None
        self._monitoring_task: Optional[asyncio.Task] = None
        
        # Initialize persistence directory
        if self.cache_config.enable_persistence:
            Path(self.cache_config.persistence_path).mkdir(parents=True, exist_ok=True)
        
        logger.info(
            "System Resilience Service initialized",
            degradation_config=asdict(self.degradation_config),
            cache_config=asdict(self.cache_config)
        )
    
    async def start(self) -> None:
        """Start background tasks for resilience monitoring."""
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._cache_cleanup_loop())
        
        if self._monitoring_task is None:
            self._monitoring_task = asyncio.create_task(self._health_monitoring_loop())
        
        # Load persisted cache if enabled
        if self.cache_config.enable_persistence:
            await self._load_cache_from_disk()
        
        logger.info("System resilience service started")
    
    async def stop(self) -> None:
        """Stop background tasks and persist cache."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
        
        # Persist cache if enabled
        if self.cache_config.enable_persistence:
            await self._persist_cache_to_disk()
        
        logger.info("System resilience service stopped")
    
    async def execute_with_resilience(
        self,
        service_name: str,
        operation: Callable,
        fallback_operation: Optional[Callable] = None,
        cache_key: Optional[str] = None,
        cache_ttl: Optional[int] = None,
        *args,
        **kwargs
    ) -> Any:
        """Execute an operation with full resilience features.
        
        Args:
            service_name: Name of the service being called
            operation: Primary operation to execute
            fallback_operation: Fallback operation if primary fails
            cache_key: Key for caching results
            cache_ttl: TTL for cached results
            *args: Arguments for the operation
            **kwargs: Keyword arguments for the operation
            
        Returns:
            Result of the operation or fallback
        """
        start_time = time.time()
        
        # Check cache first
        if cache_key:
            cached_result = await self.get_cached_data(cache_key)
            if cached_result is not None:
                logger.debug(
                    "Cache hit for operation",
                    service_name=service_name,
                    cache_key=cache_key
                )
                return cached_result
        
        # Check circuit breaker
        if self._is_circuit_breaker_open(service_name):
            logger.warning(
                "Circuit breaker open, using fallback",
                service_name=service_name
            )
            return await self._execute_fallback(
                service_name, fallback_operation, cache_key, *args, **kwargs
            )
        
        # Execute primary operation
        try:
            result = await self._execute_operation_with_monitoring(
                service_name, operation, *args, **kwargs
            )
            
            # Cache successful result
            if cache_key and result is not None:
                await self.cache_data(cache_key, result, cache_ttl)
            
            # Update success metrics
            execution_time = (time.time() - start_time) * 1000
            await self._record_success(service_name, execution_time)
            
            return result
            
        except Exception as error:
            # Record error
            execution_time = (time.time() - start_time) * 1000
            await self._record_error(service_name, error, execution_time)
            
            # Check if we should degrade service
            if await self._should_degrade_service(service_name):
                logger.warning(
                    "Service degraded due to errors, using fallback",
                    service_name=service_name,
                    error=str(error)
                )
                return await self._execute_fallback(
                    service_name, fallback_operation, cache_key, *args, **kwargs
                )
            
            # Re-raise error if no fallback available
            raise
    
    async def _execute_operation_with_monitoring(
        self,
        service_name: str,
        operation: Callable,
        *args,
        **kwargs
    ) -> Any:
        """Execute operation with monitoring and timeout."""
        try:
            # Add timeout to prevent hanging operations
            result = await asyncio.wait_for(
                operation(*args, **kwargs) if asyncio.iscoroutinefunction(operation)
                else asyncio.get_event_loop().run_in_executor(None, operation, *args, **kwargs),
                timeout=30.0  # 30 second timeout
            )
            return result
            
        except asyncio.TimeoutError:
            logger.error(
                "Operation timed out",
                service_name=service_name,
                timeout_seconds=30
            )
            raise
        except Exception as e:
            logger.error(
                "Operation failed",
                service_name=service_name,
                error=str(e),
                error_type=type(e).__name__
            )
            raise
    
    async def _execute_fallback(
        self,
        service_name: str,
        fallback_operation: Optional[Callable],
        cache_key: Optional[str],
        *args,
        **kwargs
    ) -> Any:
        """Execute fallback operation or return cached data."""
        # Try fallback operation first
        if fallback_operation:
            try:
                logger.info(
                    "Executing fallback operation",
                    service_name=service_name
                )
                result = await self._execute_operation_with_monitoring(
                    f"{service_name}_fallback", fallback_operation, *args, **kwargs
                )
                return result
            except Exception as fallback_error:
                logger.error(
                    "Fallback operation failed",
                    service_name=service_name,
                    error=str(fallback_error)
                )
        
        # Try to return stale cached data
        if cache_key:
            stale_data = await self.get_cached_data(cache_key, allow_stale=True)
            if stale_data is not None:
                logger.info(
                    "Returning stale cached data as fallback",
                    service_name=service_name,
                    cache_key=cache_key
                )
                return stale_data
        
        # Return empty/default result as last resort
        logger.warning(
            "No fallback available, returning empty result",
            service_name=service_name
        )
        return self._get_empty_result(service_name)
    
    def _get_empty_result(self, service_name: str) -> Any:
        """Get appropriate empty result for service."""
        # Return service-specific empty results
        if "tourist_spots" in service_name.lower():
            return []
        elif "restaurants" in service_name.lower():
            return []
        elif "itinerary" in service_name.lower():
            return {
                "main_itinerary": {},
                "candidate_tourist_spots": [],
                "candidate_restaurants": [],
                "metadata": {
                    "fallback_used": True,
                    "service_degraded": True
                }
            }
        else:
            return None
    
    async def cache_data(
        self,
        key: str,
        data: Any,
        ttl_seconds: Optional[int] = None
    ) -> None:
        """Cache data with specified TTL.
        
        Args:
            key: Cache key
            data: Data to cache
            ttl_seconds: Time to live in seconds
        """
        if ttl_seconds is None:
            ttl_seconds = self.cache_config.default_ttl_seconds
        
        # Calculate data size
        try:
            data_bytes = pickle.dumps(data)
            size_bytes = len(data_bytes)
        except Exception:
            size_bytes = len(str(data).encode('utf-8'))
        
        # Check cache size limits
        if await self._should_evict_for_size(size_bytes):
            await self._evict_cache_entries()
        
        # Create cache entry
        now = datetime.now()
        cache_entry = CacheEntry(
            key=key,
            data=data,
            created_at=now,
            last_accessed=now,
            access_count=1,
            ttl_seconds=ttl_seconds,
            size_bytes=size_bytes
        )
        
        self._cache[key] = cache_entry
        self._cache_stats['size_bytes'] += size_bytes
        
        logger.debug(
            "Data cached",
            key=key,
            size_bytes=size_bytes,
            ttl_seconds=ttl_seconds
        )
    
    async def get_cached_data(
        self,
        key: str,
        allow_stale: bool = False
    ) -> Optional[Any]:
        """Get cached data by key.
        
        Args:
            key: Cache key
            allow_stale: Whether to return expired data
            
        Returns:
            Cached data or None if not found/expired
        """
        if key not in self._cache:
            self._cache_stats['misses'] += 1
            return None
        
        entry = self._cache[key]
        now = datetime.now()
        
        # Check if entry is expired
        if entry.ttl_seconds and not allow_stale:
            age_seconds = (now - entry.created_at).total_seconds()
            if age_seconds > entry.ttl_seconds:
                # Remove expired entry
                await self._remove_cache_entry(key)
                self._cache_stats['misses'] += 1
                return None
        
        # Update access information
        entry.last_accessed = now
        entry.access_count += 1
        
        self._cache_stats['hits'] += 1
        
        logger.debug(
            "Cache hit",
            key=key,
            age_seconds=(now - entry.created_at).total_seconds(),
            access_count=entry.access_count
        )
        
        return entry.data
    
    async def _should_evict_for_size(self, new_size_bytes: int) -> bool:
        """Check if cache eviction is needed for new data."""
        max_size_bytes = self.cache_config.max_size_mb * 1024 * 1024
        current_size = self._cache_stats['size_bytes']
        
        return (current_size + new_size_bytes) > max_size_bytes
    
    async def _evict_cache_entries(self) -> None:
        """Evict cache entries based on strategy."""
        if self.cache_config.strategy == CacheStrategy.LRU:
            await self._evict_lru()
        elif self.cache_config.strategy == CacheStrategy.TTL:
            await self._evict_expired()
        else:  # HYBRID
            await self._evict_expired()
            if await self._should_evict_for_size(0):
                await self._evict_lru()
    
    async def _evict_lru(self) -> None:
        """Evict least recently used entries."""
        if not self._cache:
            return
        
        # Sort by last accessed time
        sorted_entries = sorted(
            self._cache.items(),
            key=lambda x: x[1].last_accessed
        )
        
        # Remove oldest 25% of entries
        evict_count = max(1, len(sorted_entries) // 4)
        
        for i in range(evict_count):
            key, _ = sorted_entries[i]
            await self._remove_cache_entry(key)
            self._cache_stats['evictions'] += 1
        
        logger.info(
            "LRU cache eviction completed",
            evicted_count=evict_count,
            remaining_entries=len(self._cache)
        )
    
    async def _evict_expired(self) -> None:
        """Evict expired cache entries."""
        now = datetime.now()
        expired_keys = []
        
        for key, entry in self._cache.items():
            if entry.ttl_seconds:
                age_seconds = (now - entry.created_at).total_seconds()
                if age_seconds > entry.ttl_seconds:
                    expired_keys.append(key)
        
        for key in expired_keys:
            await self._remove_cache_entry(key)
            self._cache_stats['evictions'] += 1
        
        if expired_keys:
            logger.info(
                "Expired cache entries removed",
                expired_count=len(expired_keys)
            )
    
    async def _remove_cache_entry(self, key: str) -> None:
        """Remove a cache entry and update stats."""
        if key in self._cache:
            entry = self._cache[key]
            self._cache_stats['size_bytes'] -= entry.size_bytes
            del self._cache[key]
    
    async def _record_success(self, service_name: str, response_time_ms: float) -> None:
        """Record successful operation."""
        if service_name not in self._service_health:
            self._service_health[service_name] = ServiceHealth(
                service_name=service_name,
                status=ServiceStatus.HEALTHY,
                last_check=datetime.now(),
                error_count=0,
                success_count=0,
                response_time_ms=0.0,
                error_rate=0.0,
                uptime_percentage=100.0
            )
        
        health = self._service_health[service_name]
        health.success_count += 1
        health.last_check = datetime.now()
        health.response_time_ms = response_time_ms
        
        # Update performance metrics
        if service_name not in self._performance_metrics:
            self._performance_metrics[service_name] = []
        
        self._performance_metrics[service_name].append(response_time_ms)
        
        # Keep only recent metrics (last 100 operations)
        if len(self._performance_metrics[service_name]) > 100:
            self._performance_metrics[service_name] = self._performance_metrics[service_name][-100:]
        
        # Update error rate
        total_operations = health.success_count + health.error_count
        health.error_rate = (health.error_count / total_operations) * 100 if total_operations > 0 else 0
        
        # Check if service should recover from degraded state
        if health.status != ServiceStatus.HEALTHY and health.error_count == 0:
            await self._recover_service(service_name)
    
    async def _record_error(
        self,
        service_name: str,
        error: Exception,
        response_time_ms: float
    ) -> None:
        """Record error for service."""
        if service_name not in self._service_health:
            self._service_health[service_name] = ServiceHealth(
                service_name=service_name,
                status=ServiceStatus.HEALTHY,
                last_check=datetime.now(),
                error_count=0,
                success_count=0,
                response_time_ms=0.0,
                error_rate=0.0,
                uptime_percentage=100.0
            )
        
        health = self._service_health[service_name]
        health.error_count += 1
        health.last_check = datetime.now()
        health.last_error = str(error)
        health.response_time_ms = response_time_ms
        
        # Update error rate
        total_operations = health.success_count + health.error_count
        health.error_rate = (health.error_count / total_operations) * 100 if total_operations > 0 else 0
        
        # Log error with context
        error_entry = {
            'timestamp': datetime.now().isoformat(),
            'service_name': service_name,
            'error_type': type(error).__name__,
            'error_message': str(error),
            'response_time_ms': response_time_ms,
            'error_rate': health.error_rate
        }
        
        self._error_log.append(error_entry)
        
        # Keep only recent errors (last 1000)
        if len(self._error_log) > 1000:
            self._error_log = self._error_log[-1000:]
        
        logger.error(
            "Service error recorded",
            service_name=service_name,
            error_type=type(error).__name__,
            error_message=str(error),
            error_count=health.error_count,
            error_rate=health.error_rate
        )
    
    async def _should_degrade_service(self, service_name: str) -> bool:
        """Check if service should be degraded based on error patterns."""
        if service_name not in self._service_health:
            return False
        
        health = self._service_health[service_name]
        
        # Check error threshold
        if health.error_count >= self.degradation_config.error_threshold:
            # Check if errors occurred within the time window
            recent_errors = [
                error for error in self._error_log
                if (error['service_name'] == service_name and
                    datetime.fromisoformat(error['timestamp']) > 
                    datetime.now() - timedelta(minutes=self.degradation_config.error_window_minutes))
            ]
            
            if len(recent_errors) >= self.degradation_config.error_threshold:
                await self._degrade_service(service_name)
                return True
        
        return False
    
    async def _degrade_service(self, service_name: str) -> None:
        """Degrade service status."""
        if service_name in self._service_health:
            health = self._service_health[service_name]
            
            if health.status == ServiceStatus.HEALTHY:
                health.status = ServiceStatus.DEGRADED
            elif health.status == ServiceStatus.DEGRADED:
                health.status = ServiceStatus.CRITICAL
            
            # Open circuit breaker if enabled
            if self.degradation_config.enable_circuit_breaker:
                self._circuit_breakers[service_name] = {
                    'opened_at': datetime.now(),
                    'failure_count': health.error_count,
                    'timeout_seconds': self.degradation_config.circuit_breaker_timeout_seconds
                }
            
            logger.warning(
                "Service degraded",
                service_name=service_name,
                new_status=health.status.value,
                error_count=health.error_count,
                error_rate=health.error_rate
            )
    
    async def _recover_service(self, service_name: str) -> None:
        """Recover service from degraded state."""
        if service_name in self._service_health:
            health = self._service_health[service_name]
            health.status = ServiceStatus.HEALTHY
            health.error_count = 0
            
            # Close circuit breaker
            if service_name in self._circuit_breakers:
                del self._circuit_breakers[service_name]
            
            logger.info(
                "Service recovered",
                service_name=service_name,
                success_count=health.success_count
            )
    
    def _is_circuit_breaker_open(self, service_name: str) -> bool:
        """Check if circuit breaker is open for service."""
        if service_name not in self._circuit_breakers:
            return False
        
        breaker = self._circuit_breakers[service_name]
        opened_at = breaker['opened_at']
        timeout_seconds = breaker['timeout_seconds']
        
        # Check if timeout has passed
        if datetime.now() > opened_at + timedelta(seconds=timeout_seconds):
            # Half-open state - allow one request to test
            del self._circuit_breakers[service_name]
            logger.info(
                "Circuit breaker half-open",
                service_name=service_name
            )
            return False
        
        return True
    
    async def _cache_cleanup_loop(self) -> None:
        """Background task for cache cleanup."""
        while True:
            try:
                await asyncio.sleep(self.cache_config.cleanup_interval_seconds)
                await self._evict_expired()
                
                # Persist cache periodically if enabled
                if self.cache_config.enable_persistence:
                    await self._persist_cache_to_disk()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(
                    "Cache cleanup error",
                    error=str(e)
                )
    
    async def _health_monitoring_loop(self) -> None:
        """Background task for health monitoring."""
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute
                await self._update_health_metrics()
                await self._check_service_recovery()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(
                    "Health monitoring error",
                    error=str(e)
                )
    
    async def _update_health_metrics(self) -> None:
        """Update health metrics for all services."""
        for service_name, health in self._service_health.items():
            # Calculate uptime percentage
            total_operations = health.success_count + health.error_count
            if total_operations > 0:
                health.uptime_percentage = (health.success_count / total_operations) * 100
            
            # Log health status
            logger.debug(
                "Service health update",
                service_name=service_name,
                status=health.status.value,
                error_rate=health.error_rate,
                uptime_percentage=health.uptime_percentage
            )
    
    async def _check_service_recovery(self) -> None:
        """Check if degraded services can be recovered."""
        for service_name, health in self._service_health.items():
            if health.status != ServiceStatus.HEALTHY:
                # Check if enough time has passed for recovery
                if health.last_check < datetime.now() - timedelta(
                    minutes=self.degradation_config.max_degradation_time_minutes
                ):
                    await self._recover_service(service_name)
    
    async def _persist_cache_to_disk(self) -> None:
        """Persist cache to disk."""
        try:
            cache_file = Path(self.cache_config.persistence_path) / "cache.pkl"
            
            # Convert cache to serializable format
            serializable_cache = {}
            for key, entry in self._cache.items():
                serializable_cache[key] = {
                    'data': entry.data,
                    'created_at': entry.created_at.isoformat(),
                    'last_accessed': entry.last_accessed.isoformat(),
                    'access_count': entry.access_count,
                    'ttl_seconds': entry.ttl_seconds,
                    'size_bytes': entry.size_bytes
                }
            
            with open(cache_file, 'wb') as f:
                pickle.dump(serializable_cache, f)
            
            logger.debug(
                "Cache persisted to disk",
                entries=len(serializable_cache),
                file_path=str(cache_file)
            )
            
        except Exception as e:
            logger.error(
                "Failed to persist cache",
                error=str(e)
            )
    
    async def _load_cache_from_disk(self) -> None:
        """Load cache from disk."""
        try:
            cache_file = Path(self.cache_config.persistence_path) / "cache.pkl"
            
            if not cache_file.exists():
                return
            
            with open(cache_file, 'rb') as f:
                serializable_cache = pickle.load(f)
            
            # Convert back to cache entries
            now = datetime.now()
            loaded_count = 0
            
            for key, data in serializable_cache.items():
                try:
                    created_at = datetime.fromisoformat(data['created_at'])
                    last_accessed = datetime.fromisoformat(data['last_accessed'])
                    
                    # Check if entry is still valid
                    if data['ttl_seconds']:
                        age_seconds = (now - created_at).total_seconds()
                        if age_seconds > data['ttl_seconds']:
                            continue  # Skip expired entries
                    
                    entry = CacheEntry(
                        key=key,
                        data=data['data'],
                        created_at=created_at,
                        last_accessed=last_accessed,
                        access_count=data['access_count'],
                        ttl_seconds=data['ttl_seconds'],
                        size_bytes=data['size_bytes']
                    )
                    
                    self._cache[key] = entry
                    self._cache_stats['size_bytes'] += entry.size_bytes
                    loaded_count += 1
                    
                except Exception as e:
                    logger.warning(
                        "Failed to load cache entry",
                        key=key,
                        error=str(e)
                    )
                    continue
            
            logger.info(
                "Cache loaded from disk",
                loaded_entries=loaded_count,
                total_entries=len(serializable_cache)
            )
            
        except Exception as e:
            logger.error(
                "Failed to load cache from disk",
                error=str(e)
            )
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get comprehensive system health information.
        
        Returns:
            Dictionary with system health data
        """
        return {
            'services': {
                name: {
                    'status': health.status.value,
                    'error_rate': health.error_rate,
                    'uptime_percentage': health.uptime_percentage,
                    'response_time_ms': health.response_time_ms,
                    'last_check': health.last_check.isoformat(),
                    'error_count': health.error_count,
                    'success_count': health.success_count,
                    'last_error': health.last_error
                }
                for name, health in self._service_health.items()
            },
            'circuit_breakers': {
                name: {
                    'opened_at': breaker['opened_at'].isoformat(),
                    'failure_count': breaker['failure_count'],
                    'timeout_seconds': breaker['timeout_seconds']
                }
                for name, breaker in self._circuit_breakers.items()
            },
            'cache_stats': {
                **self._cache_stats,
                'entries': len(self._cache),
                'hit_rate': (
                    self._cache_stats['hits'] / 
                    (self._cache_stats['hits'] + self._cache_stats['misses'])
                    if (self._cache_stats['hits'] + self._cache_stats['misses']) > 0 else 0
                ) * 100
            },
            'error_summary': {
                'total_errors': len(self._error_log),
                'recent_errors': len([
                    error for error in self._error_log
                    if datetime.fromisoformat(error['timestamp']) > 
                    datetime.now() - timedelta(hours=1)
                ])
            }
        }
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for all services.
        
        Returns:
            Dictionary with performance metrics
        """
        metrics = {}
        
        for service_name, response_times in self._performance_metrics.items():
            if response_times:
                metrics[service_name] = {
                    'avg_response_time_ms': sum(response_times) / len(response_times),
                    'min_response_time_ms': min(response_times),
                    'max_response_time_ms': max(response_times),
                    'total_operations': len(response_times),
                    'p95_response_time_ms': self._calculate_percentile(response_times, 95),
                    'p99_response_time_ms': self._calculate_percentile(response_times, 99)
                }
        
        return metrics
    
    def _calculate_percentile(self, values: List[float], percentile: int) -> float:
        """Calculate percentile value from list."""
        if not values:
            return 0.0
        
        sorted_values = sorted(values)
        index = int((percentile / 100) * len(sorted_values))
        index = min(index, len(sorted_values) - 1)
        
        return sorted_values[index]
    
    def clear_error_log(self) -> None:
        """Clear error log for monitoring reset."""
        self._error_log.clear()
        logger.info("Error log cleared")
    
    def reset_metrics(self) -> None:
        """Reset all metrics for monitoring purposes."""
        self._service_health.clear()
        self._circuit_breakers.clear()
        self._error_log.clear()
        self._performance_metrics.clear()
        self._cache_stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'size_bytes': 0
        }
        logger.info("All metrics reset")