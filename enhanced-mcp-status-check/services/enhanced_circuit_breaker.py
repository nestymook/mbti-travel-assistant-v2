"""
Enhanced Circuit Breaker with Dual Path Support

This module implements an enhanced circuit breaker that supports dual monitoring paths
(MCP and REST) with intelligent traffic routing and path availability determination.
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from dataclasses import dataclass, field
from collections import defaultdict, deque

from models.dual_health_models import (
    DualHealthCheckResult,
    MCPHealthCheckResult,
    RESTHealthCheckResult,
    ServerStatus,
    EnhancedCircuitBreakerState
)


logger = logging.getLogger(__name__)


class PathType(Enum):
    """Available monitoring path types."""
    MCP = "mcp"
    REST = "rest"
    BOTH = "both"
    NONE = "none"


@dataclass
class CircuitBreakerConfig:
    """Configuration for enhanced circuit breaker."""
    
    # Failure thresholds
    failure_threshold: int = 5  # Number of failures to open circuit
    success_threshold: int = 3  # Number of successes to close circuit
    timeout_seconds: int = 60   # Circuit breaker timeout
    
    # Path-specific settings
    mcp_failure_threshold: int = 3
    rest_failure_threshold: int = 3
    require_both_paths_healthy: bool = False
    
    # Recovery settings
    recovery_timeout_seconds: int = 30
    half_open_max_requests: int = 5
    
    # History settings
    failure_history_window_minutes: int = 10
    max_history_size: int = 100
    
    def validate(self) -> List[str]:
        """Validate circuit breaker configuration."""
        errors = []
        
        if self.failure_threshold <= 0:
            errors.append("Failure threshold must be positive")
        
        if self.success_threshold <= 0:
            errors.append("Success threshold must be positive")
        
        if self.timeout_seconds <= 0:
            errors.append("Timeout seconds must be positive")
        
        if self.mcp_failure_threshold <= 0:
            errors.append("MCP failure threshold must be positive")
        
        if self.rest_failure_threshold <= 0:
            errors.append("REST failure threshold must be positive")
        
        if self.recovery_timeout_seconds <= 0:
            errors.append("Recovery timeout must be positive")
        
        if self.half_open_max_requests <= 0:
            errors.append("Half-open max requests must be positive")
        
        return errors


@dataclass
class PathState:
    """State information for a monitoring path."""
    
    path_type: PathType
    state: EnhancedCircuitBreakerState = EnhancedCircuitBreakerState.CLOSED
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: Optional[datetime] = None
    last_success_time: Optional[datetime] = None
    opened_time: Optional[datetime] = None
    half_open_requests: int = 0
    
    def reset_counts(self):
        """Reset failure and success counts."""
        self.failure_count = 0
        self.success_count = 0
        self.half_open_requests = 0
    
    def is_available(self) -> bool:
        """Check if path is available for traffic."""
        return self.state in [
            EnhancedCircuitBreakerState.CLOSED,
            EnhancedCircuitBreakerState.HALF_OPEN
        ]


@dataclass
class FailureRecord:
    """Record of a failure event."""
    
    timestamp: datetime
    path_type: PathType
    error_message: str
    response_time_ms: float = 0.0


class EnhancedCircuitBreaker:
    """
    Enhanced Circuit Breaker with dual path support.
    
    This circuit breaker manages separate states for MCP and REST monitoring paths,
    implements intelligent traffic routing, and provides path availability determination.
    """
    
    def __init__(self, config: Optional[CircuitBreakerConfig] = None):
        """
        Initialize Enhanced Circuit Breaker.
        
        Args:
            config: Circuit breaker configuration
        """
        self.config = config or CircuitBreakerConfig()
        
        # Validate configuration
        config_errors = self.config.validate()
        if config_errors:
            raise ValueError(f"Invalid circuit breaker configuration: {config_errors}")
        
        # Server states: server_name -> {PathType -> PathState}
        self.server_states: Dict[str, Dict[PathType, PathState]] = defaultdict(
            lambda: {
                PathType.MCP: PathState(PathType.MCP),
                PathType.REST: PathState(PathType.REST)
            }
        )
        
        # Failure history: server_name -> deque of FailureRecord
        self.failure_history: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=self.config.max_history_size)
        )
        
        # Lock for thread safety
        self._lock = asyncio.Lock()
        
        logger.info(f"Enhanced Circuit Breaker initialized with config: {self.config}")
    
    async def evaluate_circuit_state(
        self,
        server_name: str,
        dual_result: DualHealthCheckResult
    ) -> EnhancedCircuitBreakerState:
        """
        Evaluate circuit breaker state based on dual health check result.
        
        Args:
            server_name: Name of the server
            dual_result: Dual health check result
            
        Returns:
            EnhancedCircuitBreakerState: Updated circuit breaker state
        """
        async with self._lock:
            # Update path states based on results
            await self._update_path_states(server_name, dual_result)
            
            # Determine overall circuit state
            overall_state = await self._determine_overall_state(server_name)
            
            # Clean up old failure records
            await self._cleanup_failure_history(server_name)
            
            logger.debug(f"Circuit state for {server_name}: {overall_state}")
            
            return overall_state
    
    async def _update_path_states(
        self,
        server_name: str,
        dual_result: DualHealthCheckResult
    ):
        """Update individual path states based on health check results."""
        server_states = self.server_states[server_name]
        
        # Update MCP path state
        if dual_result.mcp_result:
            await self._update_single_path_state(
                server_name=server_name,
                path_state=server_states[PathType.MCP],
                success=dual_result.mcp_success,
                error_message=dual_result.mcp_error_message,
                response_time_ms=dual_result.mcp_response_time_ms
            )
        
        # Update REST path state
        if dual_result.rest_result:
            await self._update_single_path_state(
                server_name=server_name,
                path_state=server_states[PathType.REST],
                success=dual_result.rest_success,
                error_message=dual_result.rest_error_message,
                response_time_ms=dual_result.rest_response_time_ms
            )
    
    async def _update_single_path_state(
        self,
        server_name: str,
        path_state: PathState,
        success: bool,
        error_message: Optional[str] = None,
        response_time_ms: float = 0.0
    ):
        """Update state for a single monitoring path."""
        current_time = datetime.now()
        
        if success:
            # Handle successful request
            path_state.success_count += 1
            path_state.last_success_time = current_time
            
            # Reset failure count on success
            if path_state.state == EnhancedCircuitBreakerState.CLOSED:
                path_state.failure_count = 0
            
            # Handle half-open state
            elif path_state.state == EnhancedCircuitBreakerState.HALF_OPEN:
                path_state.half_open_requests += 1
                
                # Close circuit if enough successes
                if path_state.success_count >= self.config.success_threshold:
                    path_state.state = EnhancedCircuitBreakerState.CLOSED
                    path_state.reset_counts()
                    logger.info(f"Circuit closed for {server_name} {path_state.path_type.value} path")
        
        else:
            # Handle failed request
            path_state.failure_count += 1
            path_state.last_failure_time = current_time
            
            # Record failure
            failure_record = FailureRecord(
                timestamp=current_time,
                path_type=path_state.path_type,
                error_message=error_message or "Unknown error",
                response_time_ms=response_time_ms
            )
            self.failure_history[server_name].append(failure_record)
            
            # Check if circuit should open
            failure_threshold = (
                self.config.mcp_failure_threshold 
                if path_state.path_type == PathType.MCP 
                else self.config.rest_failure_threshold
            )
            
            if path_state.failure_count >= failure_threshold:
                if path_state.state == EnhancedCircuitBreakerState.CLOSED:
                    path_state.state = EnhancedCircuitBreakerState.OPEN
                    path_state.opened_time = current_time
                    logger.warning(f"Circuit opened for {server_name} {path_state.path_type.value} path")
                
                elif path_state.state == EnhancedCircuitBreakerState.HALF_OPEN:
                    path_state.state = EnhancedCircuitBreakerState.OPEN
                    path_state.opened_time = current_time
                    path_state.reset_counts()
                    logger.warning(f"Circuit re-opened for {server_name} {path_state.path_type.value} path")
        
        # Check for timeout-based state transitions
        await self._check_timeout_transitions(path_state)
    
    async def _check_timeout_transitions(self, path_state: PathState):
        """Check for timeout-based state transitions."""
        current_time = datetime.now()
        
        if path_state.state == EnhancedCircuitBreakerState.OPEN and path_state.opened_time:
            timeout_duration = timedelta(seconds=self.config.timeout_seconds)
            
            if current_time - path_state.opened_time >= timeout_duration:
                path_state.state = EnhancedCircuitBreakerState.HALF_OPEN
                path_state.reset_counts()
                logger.info(f"Circuit transitioned to half-open for {path_state.path_type.value} path")
    
    async def _determine_overall_state(self, server_name: str) -> EnhancedCircuitBreakerState:
        """Determine overall circuit breaker state from individual path states."""
        server_states = self.server_states[server_name]
        mcp_state = server_states[PathType.MCP]
        rest_state = server_states[PathType.REST]
        
        # If both paths are closed, overall is closed
        if (mcp_state.state == EnhancedCircuitBreakerState.CLOSED and 
            rest_state.state == EnhancedCircuitBreakerState.CLOSED):
            return EnhancedCircuitBreakerState.CLOSED
        
        # If both paths are open, overall is open
        if (mcp_state.state == EnhancedCircuitBreakerState.OPEN and 
            rest_state.state == EnhancedCircuitBreakerState.OPEN):
            return EnhancedCircuitBreakerState.OPEN
        
        # Mixed states - determine based on configuration
        if self.config.require_both_paths_healthy:
            # Strict mode: require both paths to be healthy
            if (mcp_state.state == EnhancedCircuitBreakerState.OPEN or 
                rest_state.state == EnhancedCircuitBreakerState.OPEN):
                return EnhancedCircuitBreakerState.OPEN
            else:
                return EnhancedCircuitBreakerState.HALF_OPEN
        
        # Permissive mode: allow partial availability
        if mcp_state.state == EnhancedCircuitBreakerState.CLOSED:
            if rest_state.state == EnhancedCircuitBreakerState.OPEN:
                return EnhancedCircuitBreakerState.MCP_ONLY
        
        if rest_state.state == EnhancedCircuitBreakerState.CLOSED:
            if mcp_state.state == EnhancedCircuitBreakerState.OPEN:
                return EnhancedCircuitBreakerState.REST_ONLY
        
        # Default to half-open for mixed states
        return EnhancedCircuitBreakerState.HALF_OPEN
    
    def _should_allow_path_traffic_internal(self, path_state: PathState) -> bool:
        """
        Internal method to determine if path traffic should be allowed (no lock required).
        
        Args:
            path_state: Path state to check
            
        Returns:
            bool: True if path traffic should be allowed
        """
        # Check if path is available
        if not path_state.is_available():
            return False
        
        # Check half-open request limit
        if (path_state.state == EnhancedCircuitBreakerState.HALF_OPEN and 
            path_state.half_open_requests >= self.config.half_open_max_requests):
            return False
        
        return True

    async def should_allow_mcp_traffic(self, server_name: str) -> bool:
        """
        Determine if MCP traffic should be allowed.
        
        Args:
            server_name: Name of the server
            
        Returns:
            bool: True if MCP traffic should be allowed
        """
        async with self._lock:
            server_states = self.server_states[server_name]
            mcp_state = server_states[PathType.MCP]
            
            return self._should_allow_path_traffic_internal(mcp_state)
    
    async def should_allow_rest_traffic(self, server_name: str) -> bool:
        """
        Determine if REST traffic should be allowed.
        
        Args:
            server_name: Name of the server
            
        Returns:
            bool: True if REST traffic should be allowed
        """
        async with self._lock:
            server_states = self.server_states[server_name]
            rest_state = server_states[PathType.REST]
            
            return self._should_allow_path_traffic_internal(rest_state)
    
    async def get_available_paths(self, server_name: str) -> List[str]:
        """
        Get list of available monitoring paths.
        
        Args:
            server_name: Name of the server
            
        Returns:
            List[str]: Available paths ("mcp", "rest", "both", "none")
        """
        mcp_allowed = await self.should_allow_mcp_traffic(server_name)
        rest_allowed = await self.should_allow_rest_traffic(server_name)
        
        if mcp_allowed and rest_allowed:
            return ["mcp", "rest", "both"]
        elif mcp_allowed:
            return ["mcp"]
        elif rest_allowed:
            return ["rest"]
        else:
            return ["none"]
    
    async def get_circuit_breaker_state(self, server_name: str) -> Dict[str, Any]:
        """
        Get detailed circuit breaker state for a server.
        
        Args:
            server_name: Name of the server
            
        Returns:
            Dict[str, Any]: Detailed circuit breaker state
        """
        async with self._lock:
            server_states = self.server_states[server_name]
            failure_history = list(self.failure_history[server_name])
            
            # Calculate failure rates
            current_time = datetime.now()
            window_start = current_time - timedelta(minutes=self.config.failure_history_window_minutes)
            
            recent_failures = [
                f for f in failure_history 
                if f.timestamp >= window_start
            ]
            
            mcp_failures = [f for f in recent_failures if f.path_type == PathType.MCP]
            rest_failures = [f for f in recent_failures if f.path_type == PathType.REST]
            
            # Calculate available paths without calling external methods that need locks
            mcp_allowed = self._should_allow_path_traffic_internal(server_states[PathType.MCP])
            rest_allowed = self._should_allow_path_traffic_internal(server_states[PathType.REST])
            
            if mcp_allowed and rest_allowed:
                available_paths = ["mcp", "rest", "both"]
            elif mcp_allowed:
                available_paths = ["mcp"]
            elif rest_allowed:
                available_paths = ["rest"]
            else:
                available_paths = ["none"]
            
            return {
                "server_name": server_name,
                "timestamp": current_time.isoformat(),
                "mcp_path": {
                    "state": server_states[PathType.MCP].state.value,
                    "failure_count": server_states[PathType.MCP].failure_count,
                    "success_count": server_states[PathType.MCP].success_count,
                    "last_failure_time": (
                        server_states[PathType.MCP].last_failure_time.isoformat()
                        if server_states[PathType.MCP].last_failure_time else None
                    ),
                    "last_success_time": (
                        server_states[PathType.MCP].last_success_time.isoformat()
                        if server_states[PathType.MCP].last_success_time else None
                    ),
                    "recent_failures": len(mcp_failures),
                    "is_available": server_states[PathType.MCP].is_available()
                },
                "rest_path": {
                    "state": server_states[PathType.REST].state.value,
                    "failure_count": server_states[PathType.REST].failure_count,
                    "success_count": server_states[PathType.REST].success_count,
                    "last_failure_time": (
                        server_states[PathType.REST].last_failure_time.isoformat()
                        if server_states[PathType.REST].last_failure_time else None
                    ),
                    "last_success_time": (
                        server_states[PathType.REST].last_success_time.isoformat()
                        if server_states[PathType.REST].last_success_time else None
                    ),
                    "recent_failures": len(rest_failures),
                    "is_available": server_states[PathType.REST].is_available()
                },
                "overall_state": (await self._determine_overall_state(server_name)).value,
                "available_paths": available_paths,
                "total_recent_failures": len(recent_failures),
                "config": {
                    "failure_threshold": self.config.failure_threshold,
                    "mcp_failure_threshold": self.config.mcp_failure_threshold,
                    "rest_failure_threshold": self.config.rest_failure_threshold,
                    "timeout_seconds": self.config.timeout_seconds,
                    "require_both_paths_healthy": self.config.require_both_paths_healthy
                }
            }
    
    async def _cleanup_failure_history(self, server_name: str):
        """Clean up old failure records outside the history window."""
        current_time = datetime.now()
        window_start = current_time - timedelta(minutes=self.config.failure_history_window_minutes)
        
        failure_history = self.failure_history[server_name]
        
        # Remove old failures
        while failure_history and failure_history[0].timestamp < window_start:
            failure_history.popleft()
    
    async def reset_circuit_breaker(self, server_name: str, path_type: Optional[PathType] = None):
        """
        Reset circuit breaker state for a server.
        
        Args:
            server_name: Name of the server
            path_type: Optional specific path to reset (None for all paths)
        """
        async with self._lock:
            server_states = self.server_states[server_name]
            
            if path_type is None:
                # Reset all paths
                for path_state in server_states.values():
                    path_state.state = EnhancedCircuitBreakerState.CLOSED
                    path_state.reset_counts()
                    path_state.last_failure_time = None
                    path_state.last_success_time = None
                    path_state.opened_time = None
                
                # Clear failure history
                self.failure_history[server_name].clear()
                
                logger.info(f"Reset all circuit breaker paths for {server_name}")
            
            else:
                # Reset specific path
                if path_type in server_states:
                    path_state = server_states[path_type]
                    path_state.state = EnhancedCircuitBreakerState.CLOSED
                    path_state.reset_counts()
                    path_state.last_failure_time = None
                    path_state.last_success_time = None
                    path_state.opened_time = None
                    
                    # Remove failures for this path
                    failure_history = self.failure_history[server_name]
                    filtered_failures = deque(
                        [f for f in failure_history if f.path_type != path_type],
                        maxlen=self.config.max_history_size
                    )
                    self.failure_history[server_name] = filtered_failures
                    
                    logger.info(f"Reset circuit breaker {path_type.value} path for {server_name}")
    
    async def get_all_circuit_states(self) -> Dict[str, Dict[str, Any]]:
        """
        Get circuit breaker states for all servers.
        
        Returns:
            Dict[str, Dict[str, Any]]: Circuit states for all servers
        """
        all_states = {}
        
        for server_name in self.server_states.keys():
            all_states[server_name] = await self.get_circuit_breaker_state(server_name)
        
        return all_states
    
    async def get_circuit_breaker_metrics(self) -> Dict[str, Any]:
        """
        Get overall circuit breaker metrics.
        
        Returns:
            Dict[str, Any]: Circuit breaker metrics
        """
        all_states = await self.get_all_circuit_states()
        
        total_servers = len(all_states)
        mcp_open_count = 0
        rest_open_count = 0
        both_available_count = 0
        none_available_count = 0
        
        for state in all_states.values():
            if state["mcp_path"]["state"] == "OPEN":
                mcp_open_count += 1
            if state["rest_path"]["state"] == "OPEN":
                rest_open_count += 1
            
            available_paths = state["available_paths"]
            if "both" in available_paths:
                both_available_count += 1
            elif "none" in available_paths:
                none_available_count += 1
        
        return {
            "total_servers": total_servers,
            "mcp_circuits_open": mcp_open_count,
            "rest_circuits_open": rest_open_count,
            "both_paths_available": both_available_count,
            "no_paths_available": none_available_count,
            "mcp_availability_rate": (
                (total_servers - mcp_open_count) / total_servers 
                if total_servers > 0 else 0.0
            ),
            "rest_availability_rate": (
                (total_servers - rest_open_count) / total_servers 
                if total_servers > 0 else 0.0
            ),
            "dual_path_availability_rate": (
                both_available_count / total_servers 
                if total_servers > 0 else 0.0
            )
        }
    
    def update_config(self, new_config: CircuitBreakerConfig) -> bool:
        """
        Update circuit breaker configuration.
        
        Args:
            new_config: New configuration
            
        Returns:
            bool: True if update successful
        """
        config_errors = new_config.validate()
        if config_errors:
            logger.error(f"Cannot update config due to validation errors: {config_errors}")
            return False
        
        self.config = new_config
        logger.info("Circuit breaker configuration updated successfully")
        return True