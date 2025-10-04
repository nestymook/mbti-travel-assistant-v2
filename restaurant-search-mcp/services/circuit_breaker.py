"""
Circuit breaker implementation for MCP server health checks.

This module provides circuit breaker functionality to prevent cascading failures
when MCP servers are experiencing issues.
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, Optional, Callable, Any
import logging
from dataclasses import dataclass, field

from models.status_models import (
    CircuitBreakerState,
    CircuitBreakerConfig,
    HealthCheckResult,
    ServerMetrics
)


@dataclass
class CircuitBreakerStats:
    """Statistics for circuit breaker operation."""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    circuit_open_count: int = 0
    circuit_half_open_count: int = 0
    last_failure_time: Optional[datetime] = None
    last_success_time: Optional[datetime] = None
    last_state_change_time: Optional[datetime] = None
    
    @property
    def failure_rate(self) -> float:
        """Calculate failure rate as percentage."""
        if self.total_requests == 0:
            return 0.0
        return (self.failed_requests / self.total_requests) * 100.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "failure_rate": self.failure_rate,
            "circuit_open_count": self.circuit_open_count,
            "circuit_half_open_count": self.circuit_half_open_count,
            "last_failure_time": self.last_failure_time.isoformat() if self.last_failure_time else None,
            "last_success_time": self.last_success_time.isoformat() if self.last_success_time else None,
            "last_state_change_time": self.last_state_change_time.isoformat() if self.last_state_change_time else None
        }


class CircuitBreaker:
    """Circuit breaker for protecting against cascading failures."""
    
    def __init__(self, name: str, config: CircuitBreakerConfig):
        """Initialize circuit breaker.
        
        Args:
            name: Name of the circuit breaker (typically server name)
            config: Circuit breaker configuration
        """
        self.name = name
        self.config = config
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.last_success_time: Optional[datetime] = None
        self.last_state_change_time = datetime.now()
        self.half_open_calls = 0
        self.stats = CircuitBreakerStats()
        self.logger = logging.getLogger(f"{__name__}.{name}")
        self._lock = asyncio.Lock()
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute a function through the circuit breaker.
        
        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            CircuitBreakerOpenError: If circuit is open
            Exception: Any exception from the wrapped function
        """
        async with self._lock:
            # Check if circuit should allow the call
            if not await self._can_execute():
                raise CircuitBreakerOpenError(f"Circuit breaker '{self.name}' is OPEN")
            
            # Track the call attempt
            self.stats.total_requests += 1
            
            # If in half-open state, track the call
            if self.state == CircuitBreakerState.HALF_OPEN:
                self.half_open_calls += 1
        
        # Execute the function
        start_time = time.time()
        try:
            result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
            
            # Record success
            await self._record_success()
            return result
            
        except Exception as e:
            # Record failure
            await self._record_failure()
            raise e
    
    async def _can_execute(self) -> bool:
        """Check if the circuit breaker allows execution.
        
        Returns:
            True if execution is allowed, False otherwise
        """
        now = datetime.now()
        
        if self.state == CircuitBreakerState.CLOSED:
            return True
        
        elif self.state == CircuitBreakerState.OPEN:
            # Check if timeout period has elapsed
            if self.last_failure_time:
                time_since_failure = now - self.last_failure_time
                if time_since_failure.total_seconds() >= self.config.timeout_seconds:
                    # Transition to half-open
                    await self._transition_to_half_open()
                    return True
            return False
        
        elif self.state == CircuitBreakerState.HALF_OPEN:
            # Allow limited calls in half-open state
            return self.half_open_calls < self.config.half_open_max_calls
        
        return False
    
    async def _record_success(self) -> None:
        """Record a successful operation."""
        async with self._lock:
            self.success_count += 1
            self.failure_count = 0  # Reset failure count on success
            self.last_success_time = datetime.now()
            self.stats.successful_requests += 1
            self.stats.last_success_time = self.last_success_time
            
            # Check for state transitions
            if self.state == CircuitBreakerState.HALF_OPEN:
                if self.success_count >= self.config.recovery_threshold:
                    await self._transition_to_closed()
            
            self.logger.debug(f"Recorded success. Success count: {self.success_count}, State: {self.state.value}")
    
    async def _record_failure(self) -> None:
        """Record a failed operation."""
        async with self._lock:
            self.failure_count += 1
            self.success_count = 0  # Reset success count on failure
            self.last_failure_time = datetime.now()
            self.stats.failed_requests += 1
            self.stats.last_failure_time = self.last_failure_time
            
            # Check for state transitions
            if self.state == CircuitBreakerState.CLOSED:
                if self.failure_count >= self.config.failure_threshold:
                    await self._transition_to_open()
            elif self.state == CircuitBreakerState.HALF_OPEN:
                # Any failure in half-open state transitions back to open
                await self._transition_to_open()
            
            self.logger.debug(f"Recorded failure. Failure count: {self.failure_count}, State: {self.state.value}")
    
    async def _transition_to_open(self) -> None:
        """Transition circuit breaker to OPEN state."""
        old_state = self.state
        self.state = CircuitBreakerState.OPEN
        self.last_state_change_time = datetime.now()
        self.stats.circuit_open_count += 1
        self.stats.last_state_change_time = self.last_state_change_time
        
        self.logger.warning(f"Circuit breaker '{self.name}' transitioned from {old_state.value} to OPEN")
    
    async def _transition_to_half_open(self) -> None:
        """Transition circuit breaker to HALF_OPEN state."""
        old_state = self.state
        self.state = CircuitBreakerState.HALF_OPEN
        self.half_open_calls = 0
        self.success_count = 0
        self.failure_count = 0
        self.last_state_change_time = datetime.now()
        self.stats.circuit_half_open_count += 1
        self.stats.last_state_change_time = self.last_state_change_time
        
        self.logger.info(f"Circuit breaker '{self.name}' transitioned from {old_state.value} to HALF_OPEN")
    
    async def _transition_to_closed(self) -> None:
        """Transition circuit breaker to CLOSED state."""
        old_state = self.state
        self.state = CircuitBreakerState.CLOSED
        self.half_open_calls = 0
        self.success_count = 0
        self.failure_count = 0
        self.last_state_change_time = datetime.now()
        self.stats.last_state_change_time = self.last_state_change_time
        
        self.logger.info(f"Circuit breaker '{self.name}' transitioned from {old_state.value} to CLOSED")
    
    async def force_open(self) -> None:
        """Force the circuit breaker to OPEN state."""
        async with self._lock:
            await self._transition_to_open()
            self.logger.warning(f"Circuit breaker '{self.name}' was forced OPEN")
    
    async def force_closed(self) -> None:
        """Force the circuit breaker to CLOSED state."""
        async with self._lock:
            await self._transition_to_closed()
            self.logger.info(f"Circuit breaker '{self.name}' was forced CLOSED")
    
    async def reset(self) -> None:
        """Reset the circuit breaker to initial state."""
        async with self._lock:
            self.state = CircuitBreakerState.CLOSED
            self.failure_count = 0
            self.success_count = 0
            self.half_open_calls = 0
            self.last_state_change_time = datetime.now()
            self.stats = CircuitBreakerStats()
            
            self.logger.info(f"Circuit breaker '{self.name}' was reset")
    
    def get_state(self) -> CircuitBreakerState:
        """Get current circuit breaker state.
        
        Returns:
            Current CircuitBreakerState
        """
        return self.state
    
    def get_stats(self) -> CircuitBreakerStats:
        """Get circuit breaker statistics.
        
        Returns:
            CircuitBreakerStats object
        """
        return self.stats
    
    def is_available(self) -> bool:
        """Check if the circuit breaker is available for requests.
        
        Returns:
            True if available, False if circuit is open
        """
        if self.state == CircuitBreakerState.OPEN:
            # Check if timeout has elapsed
            if self.last_failure_time:
                time_since_failure = datetime.now() - self.last_failure_time
                return time_since_failure.total_seconds() >= self.config.timeout_seconds
            return False
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert circuit breaker to dictionary for JSON serialization.
        
        Returns:
            Dictionary representation
        """
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "half_open_calls": self.half_open_calls,
            "last_failure_time": self.last_failure_time.isoformat() if self.last_failure_time else None,
            "last_success_time": self.last_success_time.isoformat() if self.last_success_time else None,
            "last_state_change_time": self.last_state_change_time.isoformat(),
            "config": self.config.to_dict(),
            "stats": self.stats.to_dict(),
            "is_available": self.is_available()
        }


class CircuitBreakerOpenError(Exception):
    """Exception raised when circuit breaker is open."""
    pass


class StatusCheckManager:
    """Centralized manager for server status checking with circuit breakers and metrics."""
    
    def __init__(self):
        """Initialize the status check manager."""
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.server_metrics: Dict[str, ServerMetrics] = {}
        self.logger = logging.getLogger(__name__)
        self._lock = asyncio.Lock()
    
    async def add_server(self, server_name: str, circuit_breaker_config: CircuitBreakerConfig) -> None:
        """Add a server to be monitored.
        
        Args:
            server_name: Name of the server
            circuit_breaker_config: Circuit breaker configuration
        """
        async with self._lock:
            if server_name not in self.circuit_breakers:
                self.circuit_breakers[server_name] = CircuitBreaker(server_name, circuit_breaker_config)
                self.server_metrics[server_name] = ServerMetrics(server_name)
                self.logger.info(f"Added server '{server_name}' to status check manager")
    
    async def remove_server(self, server_name: str) -> None:
        """Remove a server from monitoring.
        
        Args:
            server_name: Name of the server to remove
        """
        async with self._lock:
            if server_name in self.circuit_breakers:
                del self.circuit_breakers[server_name]
                del self.server_metrics[server_name]
                self.logger.info(f"Removed server '{server_name}' from status check manager")
    
    async def record_health_check_result(self, result: HealthCheckResult) -> None:
        """Record a health check result and update metrics.
        
        Args:
            result: Health check result to record
        """
        server_name = result.server_name
        
        # Ensure server is being tracked
        if server_name not in self.server_metrics:
            self.logger.warning(f"Received result for unknown server: {server_name}")
            return
        
        # Update server metrics
        async with self._lock:
            metrics = self.server_metrics[server_name]
            metrics.update_with_result(result)
        
        # Update circuit breaker
        circuit_breaker = self.circuit_breakers.get(server_name)
        if circuit_breaker:
            if result.success:
                await circuit_breaker._record_success()
            else:
                await circuit_breaker._record_failure()
    
    async def is_server_available(self, server_name: str) -> bool:
        """Check if a server is available (circuit breaker allows requests).
        
        Args:
            server_name: Name of the server
            
        Returns:
            True if server is available, False otherwise
        """
        circuit_breaker = self.circuit_breakers.get(server_name)
        if circuit_breaker:
            return circuit_breaker.is_available()
        return True  # If no circuit breaker, assume available
    
    async def get_server_circuit_breaker_state(self, server_name: str) -> Optional[CircuitBreakerState]:
        """Get the circuit breaker state for a server.
        
        Args:
            server_name: Name of the server
            
        Returns:
            CircuitBreakerState or None if server not found
        """
        circuit_breaker = self.circuit_breakers.get(server_name)
        return circuit_breaker.get_state() if circuit_breaker else None
    
    async def get_server_metrics(self, server_name: str) -> Optional[ServerMetrics]:
        """Get metrics for a specific server.
        
        Args:
            server_name: Name of the server
            
        Returns:
            ServerMetrics or None if server not found
        """
        return self.server_metrics.get(server_name)
    
    async def get_all_server_metrics(self) -> Dict[str, ServerMetrics]:
        """Get metrics for all servers.
        
        Returns:
            Dictionary mapping server names to ServerMetrics
        """
        async with self._lock:
            return self.server_metrics.copy()
    
    async def get_all_circuit_breaker_states(self) -> Dict[str, CircuitBreakerState]:
        """Get circuit breaker states for all servers.
        
        Returns:
            Dictionary mapping server names to CircuitBreakerState
        """
        return {
            name: cb.get_state()
            for name, cb in self.circuit_breakers.items()
        }
    
    async def force_circuit_breaker_open(self, server_name: str) -> bool:
        """Force a server's circuit breaker to OPEN state.
        
        Args:
            server_name: Name of the server
            
        Returns:
            True if successful, False if server not found
        """
        circuit_breaker = self.circuit_breakers.get(server_name)
        if circuit_breaker:
            await circuit_breaker.force_open()
            return True
        return False
    
    async def force_circuit_breaker_closed(self, server_name: str) -> bool:
        """Force a server's circuit breaker to CLOSED state.
        
        Args:
            server_name: Name of the server
            
        Returns:
            True if successful, False if server not found
        """
        circuit_breaker = self.circuit_breakers.get(server_name)
        if circuit_breaker:
            await circuit_breaker.force_closed()
            return True
        return False
    
    async def reset_circuit_breaker(self, server_name: str) -> bool:
        """Reset a server's circuit breaker to initial state.
        
        Args:
            server_name: Name of the server
            
        Returns:
            True if successful, False if server not found
        """
        circuit_breaker = self.circuit_breakers.get(server_name)
        if circuit_breaker:
            await circuit_breaker.reset()
            return True
        return False
    
    async def reset_server_metrics(self, server_name: str) -> bool:
        """Reset metrics for a specific server.
        
        Args:
            server_name: Name of the server
            
        Returns:
            True if successful, False if server not found
        """
        if server_name in self.server_metrics:
            async with self._lock:
                self.server_metrics[server_name] = ServerMetrics(server_name)
            return True
        return False
    
    async def get_system_health_summary(self) -> Dict[str, Any]:
        """Get overall system health summary.
        
        Returns:
            Dictionary with system health information
        """
        async with self._lock:
            total_servers = len(self.server_metrics)
            healthy_servers = 0
            unhealthy_servers = 0
            degraded_servers = 0
            
            circuit_breaker_states = {
                "closed": 0,
                "open": 0,
                "half_open": 0
            }
            
            for server_name, metrics in self.server_metrics.items():
                # Determine health based on recent performance
                if metrics.consecutive_failures == 0 and metrics.total_requests > 0:
                    healthy_servers += 1
                elif metrics.consecutive_failures >= 5:
                    unhealthy_servers += 1
                else:
                    degraded_servers += 1
                
                # Count circuit breaker states
                cb_state = await self.get_server_circuit_breaker_state(server_name)
                if cb_state:
                    circuit_breaker_states[cb_state.value] += 1
            
            return {
                "timestamp": datetime.now().isoformat(),
                "total_servers": total_servers,
                "healthy_servers": healthy_servers,
                "unhealthy_servers": unhealthy_servers,
                "degraded_servers": degraded_servers,
                "overall_health_percentage": (healthy_servers / total_servers * 100) if total_servers > 0 else 100.0,
                "circuit_breaker_states": circuit_breaker_states
            }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert status check manager to dictionary for JSON serialization.
        
        Returns:
            Dictionary representation
        """
        return {
            "servers": {
                name: {
                    "metrics": metrics.to_dict(),
                    "circuit_breaker": cb.to_dict()
                }
                for name, metrics in self.server_metrics.items()
                for cb in [self.circuit_breakers.get(name)]
                if cb is not None
            }
        }


# Global status check manager instance
_status_manager: Optional[StatusCheckManager] = None


def get_status_manager() -> StatusCheckManager:
    """Get the global status check manager instance.
    
    Returns:
        StatusCheckManager instance
    """
    global _status_manager
    if _status_manager is None:
        _status_manager = StatusCheckManager()
    return _status_manager