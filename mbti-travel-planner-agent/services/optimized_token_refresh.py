"""
Optimized Token Refresh Service

This module provides optimized JWT token refresh capabilities to minimize
authentication overhead. It implements proactive token refresh, token pooling,
and intelligent refresh scheduling.

Features:
- Proactive token refresh before expiration
- Token pooling for multiple concurrent requests
- Intelligent refresh scheduling based on usage patterns
- Background refresh tasks
- Token validation and health monitoring
- Refresh rate limiting and backoff
"""

import asyncio
import logging
import time
import threading
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Callable, Awaitable
from enum import Enum
import uuid

from .authentication_manager import AuthenticationManager, TokenInfo, TokenStatus

logger = logging.getLogger(__name__)


class RefreshStrategy(Enum):
    """Token refresh strategies."""
    REACTIVE = "reactive"  # Refresh only when needed
    PROACTIVE = "proactive"  # Refresh before expiration
    PREDICTIVE = "predictive"  # Refresh based on usage patterns
    POOLED = "pooled"  # Maintain pool of valid tokens


@dataclass
class RefreshConfig:
    """Configuration for optimized token refresh."""
    strategy: RefreshStrategy = RefreshStrategy.PROACTIVE
    proactive_refresh_threshold_seconds: int = 300  # 5 minutes before expiry
    token_pool_size: int = 3  # Number of tokens to maintain in pool
    background_refresh_enabled: bool = True
    background_refresh_interval_seconds: int = 60  # 1 minute
    max_concurrent_refreshes: int = 2
    refresh_rate_limit_per_minute: int = 10
    enable_usage_prediction: bool = True
    usage_history_size: int = 100
    min_token_lifetime_seconds: int = 600  # 10 minutes
    
    # Backoff configuration for failed refreshes
    refresh_backoff_base_seconds: float = 1.0
    refresh_backoff_max_seconds: float = 60.0
    refresh_backoff_multiplier: float = 2.0


@dataclass
class TokenUsageMetrics:
    """Metrics for token usage patterns."""
    total_requests: int = 0
    requests_per_minute: float = 0.0
    peak_requests_per_minute: float = 0.0
    average_token_lifetime_seconds: float = 0.0
    refresh_success_rate: float = 1.0
    last_usage_time: Optional[datetime] = None
    usage_history: deque = field(default_factory=lambda: deque(maxlen=100))
    
    def record_usage(self):
        """Record token usage."""
        now = datetime.utcnow()
        self.total_requests += 1
        self.last_usage_time = now
        self.usage_history.append(now)
        
        # Calculate requests per minute
        if len(self.usage_history) > 1:
            time_span = (self.usage_history[-1] - self.usage_history[0]).total_seconds() / 60
            if time_span > 0:
                self.requests_per_minute = len(self.usage_history) / time_span
                self.peak_requests_per_minute = max(self.peak_requests_per_minute, self.requests_per_minute)
    
    def predict_next_refresh_time(self, current_expiry: datetime) -> datetime:
        """Predict optimal next refresh time based on usage patterns."""
        if not self.usage_history or len(self.usage_history) < 2:
            # Default to 5 minutes before expiry
            return current_expiry - timedelta(minutes=5)
        
        # Calculate average time between requests
        if self.requests_per_minute > 0:
            # If high usage, refresh earlier
            if self.requests_per_minute > 5:  # More than 5 requests per minute
                refresh_buffer = timedelta(minutes=10)
            elif self.requests_per_minute > 1:  # More than 1 request per minute
                refresh_buffer = timedelta(minutes=7)
            else:
                refresh_buffer = timedelta(minutes=5)
        else:
            refresh_buffer = timedelta(minutes=3)
        
        return current_expiry - refresh_buffer


class TokenPool:
    """Pool of valid tokens for high-throughput scenarios."""
    
    def __init__(self, pool_size: int, auth_manager: AuthenticationManager):
        """
        Initialize token pool.
        
        Args:
            pool_size: Maximum number of tokens to maintain
            auth_manager: Authentication manager for token refresh
        """
        self.pool_size = pool_size
        self.auth_manager = auth_manager
        
        # Token storage
        self._tokens: deque = deque(maxlen=pool_size)
        self._lock = threading.RLock()
        
        # Pool statistics
        self.pool_hits = 0
        self.pool_misses = 0
        self.pool_refreshes = 0
        
        logger.debug(f"Token pool initialized with size: {pool_size}")
    
    async def get_token(self) -> str:
        """
        Get a valid token from the pool.
        
        Returns:
            Valid JWT token
        """
        with self._lock:
            # Try to find a valid token in the pool
            while self._tokens:
                token_info = self._tokens.popleft()
                if isinstance(token_info, TokenInfo) and not token_info.is_expired(buffer_seconds=60):
                    self.pool_hits += 1
                    # Put token back at the end of the queue
                    self._tokens.append(token_info)
                    return token_info.token
            
            # No valid tokens in pool
            self.pool_misses += 1
        
        # Get fresh token and add to pool
        fresh_token = await self.auth_manager.get_valid_token()
        
        with self._lock:
            # Add to pool if we have the current token info
            if self.auth_manager.current_token:
                self._tokens.append(self.auth_manager.current_token)
                self.pool_refreshes += 1
        
        return fresh_token
    
    async def refresh_pool(self):
        """Refresh all tokens in the pool."""
        with self._lock:
            # Clear expired tokens
            valid_tokens = []
            for token_info in self._tokens:
                if isinstance(token_info, TokenInfo) and not token_info.is_expired(buffer_seconds=300):
                    valid_tokens.append(token_info)
            
            self._tokens.clear()
            self._tokens.extend(valid_tokens)
            
            # Fill pool to desired size
            while len(self._tokens) < self.pool_size:
                try:
                    fresh_token = await self.auth_manager.refresh_token()
                    if self.auth_manager.current_token:
                        self._tokens.append(self.auth_manager.current_token)
                        self.pool_refreshes += 1
                except Exception as e:
                    logger.warning(f"Failed to refresh token for pool: {e}")
                    break
    
    def get_pool_stats(self) -> Dict[str, Any]:
        """Get pool statistics."""
        with self._lock:
            total_requests = self.pool_hits + self.pool_misses
            hit_rate = self.pool_hits / max(total_requests, 1)
            
            return {
                "pool_size": len(self._tokens),
                "max_pool_size": self.pool_size,
                "pool_hits": self.pool_hits,
                "pool_misses": self.pool_misses,
                "pool_refreshes": self.pool_refreshes,
                "hit_rate": hit_rate,
                "total_requests": total_requests
            }


class OptimizedTokenRefreshService:
    """
    Optimized token refresh service with multiple strategies and performance optimizations.
    
    This service minimizes authentication overhead by implementing intelligent
    token refresh strategies, pooling, and predictive refresh scheduling.
    """
    
    def __init__(
        self, 
        auth_manager: AuthenticationManager,
        config: Optional[RefreshConfig] = None
    ):
        """
        Initialize optimized token refresh service.
        
        Args:
            auth_manager: Authentication manager
            config: Refresh configuration
        """
        self.auth_manager = auth_manager
        self.config = config or RefreshConfig()
        
        # Usage metrics and prediction
        self.usage_metrics = TokenUsageMetrics()
        
        # Token pool for high-throughput scenarios
        self.token_pool: Optional[TokenPool] = None
        if self.config.strategy == RefreshStrategy.POOLED:
            self.token_pool = TokenPool(self.config.token_pool_size, auth_manager)
        
        # Background refresh management
        self._background_task: Optional[asyncio.Task] = None
        self._background_running = False
        self._refresh_semaphore = asyncio.Semaphore(self.config.max_concurrent_refreshes)
        
        # Rate limiting
        self._refresh_timestamps: deque = deque(maxlen=self.config.refresh_rate_limit_per_minute)
        self._refresh_backoff_delay = self.config.refresh_backoff_base_seconds
        
        # Performance tracking
        self.refresh_stats = {
            "total_refreshes": 0,
            "successful_refreshes": 0,
            "failed_refreshes": 0,
            "proactive_refreshes": 0,
            "reactive_refreshes": 0,
            "background_refreshes": 0,
            "total_refresh_time_ms": 0
        }
        
        logger.info(f"Optimized token refresh service initialized with strategy: {self.config.strategy.value}")
        
        # Start background refresh if enabled
        if self.config.background_refresh_enabled:
            self._start_background_refresh()
    
    def _start_background_refresh(self):
        """Start background refresh task."""
        try:
            loop = asyncio.get_running_loop()
            if not self._background_running:
                self._background_running = True
                self._background_task = loop.create_task(self._background_refresh_loop())
                logger.debug("Background token refresh task started")
        except RuntimeError:
            logger.debug("No event loop running, background refresh disabled")
    
    async def _background_refresh_loop(self):
        """Background task for proactive token refresh."""
        while self._background_running:
            try:
                await asyncio.sleep(self.config.background_refresh_interval_seconds)
                await self._perform_background_refresh()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in background refresh: {e}")
        
        logger.debug("Background token refresh task stopped")
    
    async def _perform_background_refresh(self):
        """Perform background token refresh based on strategy."""
        if not self._should_perform_background_refresh():
            return
        
        try:
            if self.config.strategy == RefreshStrategy.POOLED and self.token_pool:
                await self.token_pool.refresh_pool()
                self.refresh_stats["background_refreshes"] += 1
            
            elif self.config.strategy in [RefreshStrategy.PROACTIVE, RefreshStrategy.PREDICTIVE]:
                if self._should_refresh_proactively():
                    await self._refresh_with_rate_limiting()
                    self.refresh_stats["background_refreshes"] += 1
                    self.refresh_stats["proactive_refreshes"] += 1
        
        except Exception as e:
            logger.warning(f"Background refresh failed: {e}")
    
    def _should_perform_background_refresh(self) -> bool:
        """Check if background refresh should be performed."""
        # Don't refresh if no recent usage
        if (self.usage_metrics.last_usage_time and 
            (datetime.utcnow() - self.usage_metrics.last_usage_time).total_seconds() > 3600):
            return False
        
        # Check rate limiting
        if self._is_rate_limited():
            return False
        
        return True
    
    def _should_refresh_proactively(self) -> bool:
        """Check if token should be refreshed proactively."""
        current_token = self.auth_manager.current_token
        if not current_token:
            return True
        
        if self.config.strategy == RefreshStrategy.PROACTIVE:
            # Refresh if within threshold of expiration
            return current_token.is_expired(self.config.proactive_refresh_threshold_seconds)
        
        elif self.config.strategy == RefreshStrategy.PREDICTIVE:
            # Use usage patterns to predict optimal refresh time
            predicted_refresh_time = self.usage_metrics.predict_next_refresh_time(current_token.expires_at)
            return datetime.utcnow() >= predicted_refresh_time
        
        return False
    
    def _is_rate_limited(self) -> bool:
        """Check if refresh is rate limited."""
        now = datetime.utcnow()
        
        # Clean old timestamps
        cutoff = now - timedelta(minutes=1)
        while self._refresh_timestamps and self._refresh_timestamps[0] < cutoff:
            self._refresh_timestamps.popleft()
        
        # Check if we've exceeded the rate limit
        return len(self._refresh_timestamps) >= self.config.refresh_rate_limit_per_minute
    
    async def _refresh_with_rate_limiting(self) -> str:
        """Refresh token with rate limiting and backoff."""
        if self._is_rate_limited():
            logger.debug("Token refresh rate limited, waiting...")
            await asyncio.sleep(self._refresh_backoff_delay)
        
        async with self._refresh_semaphore:
            start_time = time.time()
            
            try:
                token = await self.auth_manager.refresh_token()
                
                # Record successful refresh
                self._refresh_timestamps.append(datetime.utcnow())
                self.refresh_stats["total_refreshes"] += 1
                self.refresh_stats["successful_refreshes"] += 1
                
                # Reset backoff delay on success
                self._refresh_backoff_delay = self.config.refresh_backoff_base_seconds
                
                refresh_time_ms = int((time.time() - start_time) * 1000)
                self.refresh_stats["total_refresh_time_ms"] += refresh_time_ms
                
                logger.debug(f"Token refreshed successfully in {refresh_time_ms}ms")
                return token
                
            except Exception as e:
                # Record failed refresh
                self.refresh_stats["total_refreshes"] += 1
                self.refresh_stats["failed_refreshes"] += 1
                
                # Increase backoff delay
                self._refresh_backoff_delay = min(
                    self._refresh_backoff_delay * self.config.refresh_backoff_multiplier,
                    self.config.refresh_backoff_max_seconds
                )
                
                logger.warning(f"Token refresh failed: {e}")
                raise
    
    async def get_valid_token(self) -> str:
        """
        Get valid token using optimized refresh strategy.
        
        Returns:
            Valid JWT token
        """
        # Record usage for prediction
        if self.config.enable_usage_prediction:
            self.usage_metrics.record_usage()
        
        # Use appropriate strategy
        if self.config.strategy == RefreshStrategy.POOLED and self.token_pool:
            return await self.token_pool.get_token()
        
        elif self.config.strategy == RefreshStrategy.REACTIVE:
            # Standard reactive refresh
            token = await self.auth_manager.get_valid_token()
            if self.auth_manager.current_token and self.auth_manager.current_token.is_expired():
                self.refresh_stats["reactive_refreshes"] += 1
            return token
        
        elif self.config.strategy in [RefreshStrategy.PROACTIVE, RefreshStrategy.PREDICTIVE]:
            # Check if proactive refresh is needed
            if self._should_refresh_proactively():
                try:
                    return await self._refresh_with_rate_limiting()
                except Exception as e:
                    logger.warning(f"Proactive refresh failed, falling back to reactive: {e}")
                    # Fall back to reactive refresh
                    return await self.auth_manager.get_valid_token()
            else:
                # Token is still valid
                return await self.auth_manager.get_valid_token()
        
        else:
            # Default to reactive
            return await self.auth_manager.get_valid_token()
    
    async def force_refresh(self) -> str:
        """
        Force token refresh regardless of current state.
        
        Returns:
            New JWT token
        """
        return await self._refresh_with_rate_limiting()
    
    async def warm_up_tokens(self):
        """Warm up token pool or cache for high-throughput scenarios."""
        if self.config.strategy == RefreshStrategy.POOLED and self.token_pool:
            logger.info("Warming up token pool...")
            await self.token_pool.refresh_pool()
        else:
            # Ensure we have a fresh token
            await self.get_valid_token()
        
        logger.info("Token warm-up completed")
    
    def get_refresh_statistics(self) -> Dict[str, Any]:
        """Get token refresh statistics."""
        stats = self.refresh_stats.copy()
        
        # Calculate derived metrics
        if stats["total_refreshes"] > 0:
            stats["refresh_success_rate"] = stats["successful_refreshes"] / stats["total_refreshes"]
            stats["average_refresh_time_ms"] = stats["total_refresh_time_ms"] / stats["total_refreshes"]
        else:
            stats["refresh_success_rate"] = 1.0
            stats["average_refresh_time_ms"] = 0
        
        # Add usage metrics
        stats["usage_metrics"] = {
            "total_requests": self.usage_metrics.total_requests,
            "requests_per_minute": self.usage_metrics.requests_per_minute,
            "peak_requests_per_minute": self.usage_metrics.peak_requests_per_minute,
            "last_usage_time": self.usage_metrics.last_usage_time.isoformat() if self.usage_metrics.last_usage_time else None
        }
        
        # Add pool statistics if using pooled strategy
        if self.token_pool:
            stats["pool_stats"] = self.token_pool.get_pool_stats()
        
        # Add configuration
        stats["config"] = {
            "strategy": self.config.strategy.value,
            "proactive_refresh_threshold_seconds": self.config.proactive_refresh_threshold_seconds,
            "background_refresh_enabled": self.config.background_refresh_enabled,
            "token_pool_size": self.config.token_pool_size if self.token_pool else 0
        }
        
        return stats
    
    def get_token_health_info(self) -> Dict[str, Any]:
        """Get current token health information."""
        current_token = self.auth_manager.current_token
        
        if not current_token:
            return {
                "has_token": False,
                "status": "no_token",
                "time_until_expiry": None,
                "should_refresh": True
            }
        
        time_until_expiry = current_token.time_until_expiry()
        should_refresh = self._should_refresh_proactively()
        
        return {
            "has_token": True,
            "status": current_token.get_status().value,
            "time_until_expiry": str(time_until_expiry),
            "time_until_expiry_seconds": time_until_expiry.total_seconds(),
            "should_refresh": should_refresh,
            "is_expired": current_token.is_expired(),
            "expires_at": current_token.expires_at.isoformat(),
            "authentication_flow": current_token.authentication_flow.value if current_token.authentication_flow else None
        }
    
    async def close(self):
        """Close service and cleanup resources."""
        self._background_running = False
        
        if self._background_task:
            self._background_task.cancel()
            try:
                await self._background_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Optimized token refresh service closed")
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()


# Global optimized token refresh service
_global_token_refresh_service: Optional[OptimizedTokenRefreshService] = None


def get_optimized_token_refresh_service(
    auth_manager: AuthenticationManager,
    config: Optional[RefreshConfig] = None
) -> OptimizedTokenRefreshService:
    """
    Get global optimized token refresh service instance.
    
    Args:
        auth_manager: Authentication manager
        config: Optional refresh configuration
        
    Returns:
        OptimizedTokenRefreshService instance
    """
    global _global_token_refresh_service
    
    if _global_token_refresh_service is None:
        _global_token_refresh_service = OptimizedTokenRefreshService(auth_manager, config)
    
    return _global_token_refresh_service


# Export main classes and functions
__all__ = [
    'OptimizedTokenRefreshService',
    'TokenPool',
    'RefreshConfig',
    'RefreshStrategy',
    'TokenUsageMetrics',
    'get_optimized_token_refresh_service'
]