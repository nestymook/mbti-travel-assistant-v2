"""
MCP Client Manager for MBTI Travel Assistant

This module provides MCP client connection management for communicating with
existing restaurant MCP servers. It handles connections to both the restaurant
search MCP server and restaurant reasoning MCP server, implementing connection
pooling, retry logic, and proper error handling.
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any, Union, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import httpx
from contextlib import asynccontextmanager
from enum import Enum
import time
import random
from concurrent.futures import ThreadPoolExecutor

from mcp.client.session import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from mcp.types import Tool, CallToolResult

from config.settings import settings
from models.restaurant_models import Restaurant, Sentiment
from services.performance_monitor import performance_monitor, MetricType


# Configure logging
logger = logging.getLogger(__name__)


class CircuitBreakerState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class MCPErrorType(Enum):
    """Types of MCP errors for categorization"""
    CONNECTION_ERROR = "connection_error"
    TIMEOUT_ERROR = "timeout_error"
    AUTHENTICATION_ERROR = "authentication_error"
    TOOL_ERROR = "tool_error"
    PARSING_ERROR = "parsing_error"
    RATE_LIMIT_ERROR = "rate_limit_error"
    SERVER_ERROR = "server_error"
    UNKNOWN_ERROR = "unknown_error"


@dataclass
class MCPConnectionConfig:
    """Configuration for MCP client connections"""
    endpoint: str
    timeout: int = 30
    retry_attempts: int = 3
    retry_delay: float = 1.0
    max_retry_delay: float = 60.0
    connection_pool_size: int = 10
    max_concurrent_calls: int = 5
    circuit_breaker_failure_threshold: int = 5
    circuit_breaker_recovery_timeout: int = 60
    circuit_breaker_expected_exception_types: tuple = (
        ConnectionError, TimeoutError, httpx.ConnectError, httpx.TimeoutException
    )
    enable_connection_pooling: bool = True
    pool_keepalive_timeout: int = 300  # 5 minutes


@dataclass
class MCPConnectionStats:
    """Statistics for MCP connection monitoring"""
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    average_response_time: float = 0.0
    last_successful_call: Optional[datetime] = None
    last_failed_call: Optional[datetime] = None
    consecutive_failures: int = 0
    circuit_breaker_trips: int = 0
    error_counts_by_type: Dict[MCPErrorType, int] = None
    
    def __post_init__(self):
        if self.error_counts_by_type is None:
            self.error_counts_by_type = {error_type: 0 for error_type in MCPErrorType}


class MCPConnectionError(Exception):
    """Exception raised for MCP connection errors"""
    def __init__(self, message: str, server_name: str, original_error: Optional[Exception] = None):
        self.message = message
        self.server_name = server_name
        self.original_error = original_error
        super().__init__(f"MCP connection error for {server_name}: {message}")


class MCPToolCallError(Exception):
    """Exception raised for MCP tool call errors"""
    def __init__(self, message: str, tool_name: str, server_name: str, original_error: Optional[Exception] = None):
        self.message = message
        self.tool_name = tool_name
        self.server_name = server_name
        self.original_error = original_error
        super().__init__(f"MCP tool call error for {tool_name} on {server_name}: {message}")


class MCPCircuitBreakerOpenError(Exception):
    """Exception raised when circuit breaker is open"""
    def __init__(self, server_name: str, failure_count: int, recovery_time: datetime):
        self.server_name = server_name
        self.failure_count = failure_count
        self.recovery_time = recovery_time
        super().__init__(f"Circuit breaker open for {server_name}. Recovery expected at {recovery_time}")


@dataclass
class MCPConnection:
    """Represents a pooled MCP connection"""
    session: ClientSession
    created_at: datetime
    last_used: datetime
    use_count: int = 0
    is_healthy: bool = True
    
    def mark_used(self):
        """Mark connection as used"""
        self.last_used = datetime.now()
        self.use_count += 1
    
    def is_expired(self, keepalive_timeout: int) -> bool:
        """Check if connection has expired"""
        return (datetime.now() - self.last_used).total_seconds() > keepalive_timeout


class MCPConnectionPool:
    """
    Connection pool for MCP client connections.
    
    Manages a pool of reusable MCP client connections to improve performance
    and reduce connection overhead.
    """
    
    def __init__(self, config: MCPConnectionConfig, server_name: str):
        """
        Initialize connection pool.
        
        Args:
            config: MCP connection configuration
            server_name: Name of the MCP server
        """
        self.config = config
        self.server_name = server_name
        self._pool: List[MCPConnection] = []
        self._pool_lock = asyncio.Lock()
        self._active_connections = 0
        self._total_connections_created = 0
        self._cleanup_task: Optional[asyncio.Task] = None
        
        # Start cleanup task
        try:
            loop = asyncio.get_event_loop()
            self._cleanup_task = loop.create_task(self._cleanup_expired_connections())
        except RuntimeError:
            pass  # No event loop running
        
        logger.info(f"Initialized connection pool for {server_name} with size {config.connection_pool_size}")
    
    async def get_connection(self) -> MCPConnection:
        """
        Get a connection from the pool or create a new one.
        
        Returns:
            MCPConnection instance
        """
        async with self._pool_lock:
            # Try to get a healthy connection from the pool
            for i, conn in enumerate(self._pool):
                if conn.is_healthy and not conn.is_expired(self.config.pool_keepalive_timeout):
                    # Remove from pool and return
                    connection = self._pool.pop(i)
                    connection.mark_used()
                    self._active_connections += 1
                    logger.debug(f"Reused connection from pool for {self.server_name}")
                    return connection
            
            # No available connections, create a new one
            if self._active_connections < self.config.connection_pool_size:
                connection = await self._create_connection()
                self._active_connections += 1
                self._total_connections_created += 1
                logger.debug(f"Created new connection for {self.server_name}")
                return connection
            else:
                raise MCPConnectionError(
                    f"Connection pool exhausted (max: {self.config.connection_pool_size})",
                    self.server_name
                )
    
    async def return_connection(self, connection: MCPConnection):
        """
        Return a connection to the pool.
        
        Args:
            connection: Connection to return
        """
        async with self._pool_lock:
            self._active_connections -= 1
            
            if connection.is_healthy and not connection.is_expired(self.config.pool_keepalive_timeout):
                # Return healthy connection to pool
                if len(self._pool) < self.config.connection_pool_size:
                    self._pool.append(connection)
                    logger.debug(f"Returned connection to pool for {self.server_name}")
                else:
                    # Pool is full, close the connection
                    await self._close_connection(connection)
            else:
                # Connection is unhealthy or expired, close it
                await self._close_connection(connection)
    
    async def _create_connection(self) -> MCPConnection:
        """Create a new MCP connection"""
        try:
            headers = {
                "Content-Type": "application/json",
                "User-Agent": f"mbti-travel-assistant-mcp/1.0.0"
            }
            
            async with streamablehttp_client(self.config.endpoint, headers=headers) as (read, write, _):
                session = ClientSession(read, write)
                await session.initialize()
                
                now = datetime.now()
                connection = MCPConnection(
                    session=session,
                    created_at=now,
                    last_used=now
                )
                
                return connection
                
        except Exception as e:
            raise MCPConnectionError(f"Failed to create connection", self.server_name, e)
    
    async def _close_connection(self, connection: MCPConnection):
        """Close an MCP connection"""
        try:
            # Note: MCP ClientSession doesn't have an explicit close method
            # The connection will be closed when the context manager exits
            logger.debug(f"Closed connection for {self.server_name}")
        except Exception as e:
            logger.warning(f"Error closing connection for {self.server_name}: {e}")
    
    async def _cleanup_expired_connections(self):
        """Background task to clean up expired connections"""
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute
                
                async with self._pool_lock:
                    expired_connections = []
                    
                    for i, conn in enumerate(self._pool):
                        if conn.is_expired(self.config.pool_keepalive_timeout):
                            expired_connections.append((i, conn))
                    
                    # Remove expired connections (in reverse order to maintain indices)
                    for i, conn in reversed(expired_connections):
                        self._pool.pop(i)
                        await self._close_connection(conn)
                    
                    if expired_connections:
                        logger.info(f"Cleaned up {len(expired_connections)} expired connections for {self.server_name}")
                
            except Exception as e:
                logger.error(f"Error in connection cleanup for {self.server_name}: {e}")
    
    def get_pool_stats(self) -> Dict[str, Any]:
        """Get connection pool statistics"""
        return {
            "pool_size": len(self._pool),
            "active_connections": self._active_connections,
            "max_pool_size": self.config.connection_pool_size,
            "total_connections_created": self._total_connections_created,
            "pool_utilization": self._active_connections / self.config.connection_pool_size
        }
    
    async def shutdown(self):
        """Shutdown the connection pool"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
        
        async with self._pool_lock:
            for conn in self._pool:
                await self._close_connection(conn)
            self._pool.clear()
        
        logger.info(f"Connection pool shutdown for {self.server_name}")


class MCPCircuitBreaker:
    """
    Circuit breaker implementation for MCP client connections.
    
    Implements the circuit breaker pattern to prevent cascading failures
    when MCP servers are unavailable or experiencing issues.
    """
    
    def __init__(self, config: MCPConnectionConfig, server_name: str):
        """
        Initialize circuit breaker with configuration.
        
        Args:
            config: MCP connection configuration
            server_name: Name of the MCP server for logging
        """
        self.config = config
        self.server_name = server_name
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.recovery_time: Optional[datetime] = None
        self._lock = asyncio.Lock()
    
    async def call(self, operation_func, *args, **kwargs):
        """
        Execute operation with circuit breaker protection.
        
        Args:
            operation_func: Async function to execute
            *args: Arguments for operation function
            **kwargs: Keyword arguments for operation function
            
        Returns:
            Result from operation function
            
        Raises:
            MCPCircuitBreakerOpenError: If circuit breaker is open
        """
        async with self._lock:
            current_time = datetime.now()
            
            # Check if circuit breaker should transition states
            if self.state == CircuitBreakerState.OPEN:
                if current_time >= self.recovery_time:
                    logger.info(f"Circuit breaker transitioning to HALF_OPEN for {self.server_name}")
                    self.state = CircuitBreakerState.HALF_OPEN
                else:
                    raise MCPCircuitBreakerOpenError(
                        self.server_name,
                        self.failure_count,
                        self.recovery_time
                    )
        
        try:
            result = await operation_func(*args, **kwargs)
            
            # Success - reset circuit breaker if needed
            async with self._lock:
                if self.state == CircuitBreakerState.HALF_OPEN:
                    logger.info(f"Circuit breaker transitioning to CLOSED for {self.server_name}")
                    self.state = CircuitBreakerState.CLOSED
                    self.failure_count = 0
                    self.last_failure_time = None
                    self.recovery_time = None
            
            return result
            
        except Exception as e:
            async with self._lock:
                self.failure_count += 1
                self.last_failure_time = current_time
                
                # Check if we should trip the circuit breaker
                if (self.failure_count >= self.config.circuit_breaker_failure_threshold and
                    self.state == CircuitBreakerState.CLOSED):
                    
                    logger.warning(
                        f"Circuit breaker tripping to OPEN for {self.server_name} "
                        f"after {self.failure_count} failures"
                    )
                    
                    self.state = CircuitBreakerState.OPEN
                    self.recovery_time = current_time + timedelta(
                        seconds=self.config.circuit_breaker_recovery_timeout
                    )
                
                elif self.state == CircuitBreakerState.HALF_OPEN:
                    logger.warning(f"Circuit breaker returning to OPEN for {self.server_name}")
                    self.state = CircuitBreakerState.OPEN
                    self.recovery_time = current_time + timedelta(
                        seconds=self.config.circuit_breaker_recovery_timeout
                    )
            
            raise e
    
    def get_state_info(self) -> Dict[str, Any]:
        """Get current circuit breaker state information."""
        return {
            "state": self.state.value,
            "failure_count": self.failure_count,
            "last_failure_time": self.last_failure_time.isoformat() if self.last_failure_time else None,
            "recovery_time": self.recovery_time.isoformat() if self.recovery_time else None,
            "failure_threshold": self.config.circuit_breaker_failure_threshold,
            "recovery_timeout": self.config.circuit_breaker_recovery_timeout
        }


class MCPClientManager:
    """
    Manages MCP client connections to restaurant search and reasoning MCP servers.
    
    This class provides connection pooling, retry logic, and error handling for
    MCP client connections. It coordinates calls to both the restaurant search
    MCP server and restaurant reasoning MCP server as required by the internal
    LLM agent.
    """
    
    def __init__(self):
        """Initialize MCP client manager with configuration from settings"""
        # Search MCP server configuration
        self.search_config = MCPConnectionConfig(
            endpoint=settings.mcp_client.search_mcp_endpoint,
            timeout=settings.mcp_client.mcp_connection_timeout,
            retry_attempts=settings.mcp_client.mcp_retry_attempts,
            connection_pool_size=getattr(settings.mcp_client, 'connection_pool_size', 10),
            max_concurrent_calls=getattr(settings.mcp_client, 'max_concurrent_calls', 5)
        )
        
        # Reasoning MCP server configuration
        self.reasoning_config = MCPConnectionConfig(
            endpoint=settings.mcp_client.reasoning_mcp_endpoint,
            timeout=settings.mcp_client.mcp_connection_timeout,
            retry_attempts=settings.mcp_client.mcp_retry_attempts,
            connection_pool_size=getattr(settings.mcp_client, 'connection_pool_size', 10),
            max_concurrent_calls=getattr(settings.mcp_client, 'max_concurrent_calls', 5)
        )
        
        # Connection statistics
        self.search_stats = MCPConnectionStats()
        self.reasoning_stats = MCPConnectionStats()
        
        # Connection pools
        self.search_pool = MCPConnectionPool(self.search_config, "restaurant-search-mcp")
        self.reasoning_pool = MCPConnectionPool(self.reasoning_config, "restaurant-reasoning-mcp")
        
        # Semaphores for concurrent call limiting
        self._search_semaphore = asyncio.Semaphore(self.search_config.max_concurrent_calls)
        self._reasoning_semaphore = asyncio.Semaphore(self.reasoning_config.max_concurrent_calls)
        
        # Circuit breakers
        self.search_circuit_breaker = MCPCircuitBreaker(self.search_config, "restaurant-search-mcp")
        self.reasoning_circuit_breaker = MCPCircuitBreaker(self.reasoning_config, "restaurant-reasoning-mcp")
        
        # Thread pool for CPU-intensive operations
        self._thread_pool = ThreadPoolExecutor(max_workers=4, thread_name_prefix="mcp-worker")
        
        logger.info(f"Initialized MCP client manager with search endpoint: {self.search_config.endpoint}")
        logger.info(f"Initialized MCP client manager with reasoning endpoint: {self.reasoning_config.endpoint}")
        logger.info(f"Connection pooling enabled: search={self.search_config.enable_connection_pooling}, reasoning={self.reasoning_config.enable_connection_pooling}")
    
    def _classify_error(self, error: Exception) -> MCPErrorType:
        """
        Classify error type for proper handling and statistics.
        
        Args:
            error: Exception to classify
            
        Returns:
            MCPErrorType enum value
        """
        error_str = str(error).lower()
        error_type_name = type(error).__name__.lower()
        
        if isinstance(error, (ConnectionError, httpx.ConnectError)):
            return MCPErrorType.CONNECTION_ERROR
        elif isinstance(error, (TimeoutError, httpx.TimeoutException, asyncio.TimeoutError)):
            return MCPErrorType.TIMEOUT_ERROR
        elif "authentication" in error_str or "unauthorized" in error_str or "401" in error_str:
            return MCPErrorType.AUTHENTICATION_ERROR
        elif "rate limit" in error_str or "429" in error_str:
            return MCPErrorType.RATE_LIMIT_ERROR
        elif "tool" in error_str or isinstance(error, MCPToolCallError):
            return MCPErrorType.TOOL_ERROR
        elif "json" in error_str or "parse" in error_str:
            return MCPErrorType.PARSING_ERROR
        elif "500" in error_str or "502" in error_str or "503" in error_str:
            return MCPErrorType.SERVER_ERROR
        else:
            return MCPErrorType.UNKNOWN_ERROR
    
    def _is_retryable_error(self, error: Exception, error_type: MCPErrorType) -> bool:
        """
        Determine if an error is retryable.
        
        Args:
            error: Exception that occurred
            error_type: Classified error type
            
        Returns:
            True if error is retryable, False otherwise
        """
        # Non-retryable errors
        non_retryable_types = {
            MCPErrorType.AUTHENTICATION_ERROR,
            MCPErrorType.PARSING_ERROR
        }
        
        if error_type in non_retryable_types:
            return False
        
        # Check for specific non-retryable error messages
        error_str = str(error).lower()
        non_retryable_messages = [
            "invalid parameter",
            "malformed request",
            "bad request",
            "not found"
        ]
        
        for message in non_retryable_messages:
            if message in error_str:
                return False
        
        return True
    
    def _calculate_retry_delay(self, attempt: int, base_delay: float, max_delay: float) -> float:
        """
        Calculate retry delay with exponential backoff and jitter.
        
        Args:
            attempt: Current attempt number (0-based)
            base_delay: Base delay in seconds
            max_delay: Maximum delay in seconds
            
        Returns:
            Delay in seconds
        """
        # Exponential backoff: base_delay * (2 ^ attempt)
        exponential_delay = base_delay * (2 ** attempt)
        
        # Add jitter (±25% of the delay)
        jitter = exponential_delay * 0.25 * (2 * random.random() - 1)
        
        # Apply jitter and cap at max_delay
        delay = min(exponential_delay + jitter, max_delay)
        
        return max(delay, 0.1)  # Minimum 100ms delay
    
    async def _execute_with_retry(
        self,
        operation_func,
        config: MCPConnectionConfig,
        stats: MCPConnectionStats,
        server_name: str,
        operation_name: str
    ) -> Any:
        """
        Execute an MCP operation with retry logic and exponential backoff.
        
        Args:
            operation_func: Async function to execute
            config: MCP connection configuration
            stats: Connection statistics to update
            server_name: Name of the MCP server for logging
            operation_name: Name of the operation for logging
            
        Returns:
            Result from the operation function
            
        Raises:
            MCPConnectionError: If all retry attempts fail
            MCPCircuitBreakerOpenError: If circuit breaker is open
        """
        last_error = None
        last_error_type = None
        
        for attempt in range(config.retry_attempts):
            try:
                start_time = datetime.now()
                result = await operation_func()
                
                # Update statistics for success
                end_time = datetime.now()
                response_time = (end_time - start_time).total_seconds()
                stats.total_calls += 1
                stats.successful_calls += 1
                stats.last_successful_call = end_time
                stats.consecutive_failures = 0  # Reset consecutive failures
                
                # Update average response time
                if stats.average_response_time == 0:
                    stats.average_response_time = response_time
                else:
                    stats.average_response_time = (stats.average_response_time + response_time) / 2
                
                logger.debug(f"Successful {operation_name} on {server_name} (attempt {attempt + 1}, {response_time:.2f}s)")
                return result
                
            except Exception as e:
                last_error = e
                error_type = self._classify_error(e)
                last_error_type = error_type
                
                # Update statistics for failure
                stats.total_calls += 1
                stats.failed_calls += 1
                stats.consecutive_failures += 1
                stats.last_failed_call = datetime.now()
                stats.error_counts_by_type[error_type] += 1
                
                logger.warning(
                    f"Failed {operation_name} on {server_name} "
                    f"(attempt {attempt + 1}/{config.retry_attempts}, error_type: {error_type.value}): {e}"
                )
                
                # Check if error is retryable
                if not self._is_retryable_error(e, error_type):
                    logger.info(f"Non-retryable error for {operation_name} on {server_name}: {error_type.value}")
                    break
                
                # Calculate delay for next retry
                if attempt < config.retry_attempts - 1:
                    retry_delay = self._calculate_retry_delay(attempt, config.retry_delay, config.max_retry_delay)
                    
                    # Add extra delay for rate limiting
                    if error_type == MCPErrorType.RATE_LIMIT_ERROR:
                        retry_delay = min(retry_delay * 2, config.max_retry_delay)
                    
                    logger.debug(f"Retrying {operation_name} on {server_name} in {retry_delay:.2f}s")
                    await asyncio.sleep(retry_delay)
        
        # All retry attempts failed or non-retryable error
        error_message = f"Failed {operation_name} after {config.retry_attempts} attempts"
        if last_error_type:
            error_message += f" (final error type: {last_error_type.value})"
        
        raise MCPConnectionError(
            error_message,
            server_name,
            last_error
        )
    
    @asynccontextmanager
    async def _get_mcp_session(self, config: MCPConnectionConfig, server_name: str, pool: MCPConnectionPool):
        """
        Get an MCP client session with proper connection management.
        
        Args:
            config: MCP connection configuration
            server_name: Name of the MCP server for logging
            pool: Connection pool to use
            
        Yields:
            ClientSession: Active MCP client session
        """
        if not config.endpoint:
            raise MCPConnectionError(f"No endpoint configured for {server_name}", server_name)
        
        if config.enable_connection_pooling:
            # Use connection pooling
            connection = None
            try:
                connection = await pool.get_connection()
                logger.debug(f"Got pooled MCP session with {server_name}")
                yield connection.session
            finally:
                if connection:
                    await pool.return_connection(connection)
        else:
            # Direct connection without pooling
            try:
                headers = {
                    "Content-Type": "application/json",
                    "User-Agent": f"mbti-travel-assistant-mcp/1.0.0"
                }
                
                async with streamablehttp_client(config.endpoint, headers=headers) as (read, write, _):
                    async with ClientSession(read, write) as session:
                        await session.initialize()
                        logger.debug(f"Established direct MCP session with {server_name}")
                        yield session
                        
            except Exception as e:
                logger.error(f"Failed to establish MCP session with {server_name}: {e}")
                raise MCPConnectionError(f"Failed to establish session", server_name, e)
    
    async def search_restaurants(
        self,
        district: Optional[str] = None,
        meal_type: Optional[str] = None
    ) -> List[Restaurant]:
        """
        Call search_restaurants_combined MCP tool on restaurant-search-mcp server.
        
        Args:
            district: District name for search (e.g., "Central district")
            meal_type: Meal time filter (e.g., "breakfast", "lunch", "dinner")
            
        Returns:
            List of restaurants from search MCP server
            
        Raises:
            MCPToolCallError: If the MCP tool call fails
            MCPConnectionError: If connection to MCP server fails
        """
        start_time = time.time()
        
        async def _search_operation():
            async with self._search_semaphore:
                async with self._get_mcp_session(
                    self.search_config, 
                    "restaurant-search-mcp", 
                    self.search_pool
                ) as session:
                    # Prepare parameters for search_restaurants_combined tool
                    params = {}
                    if district:
                        params["districts"] = [district]
                    if meal_type:
                        params["meal_types"] = [meal_type]
                    
                    logger.info(f"Calling search_restaurants_combined with params: {params}")
                    
                    # Call the MCP tool
                    result = await session.call_tool("search_restaurants_combined", params)
                    
                    # Parse the response
                    return self._parse_search_response(result)
        
        try:
            result = await self.search_circuit_breaker.call(
                self._execute_with_retry,
                _search_operation,
                self.search_config,
                self.search_stats,
                "restaurant-search-mcp",
                "search_restaurants_combined"
            )
            
            # Record successful performance metrics
            duration = time.time() - start_time
            performance_monitor.record_mcp_call(
                "restaurant-search-mcp",
                "search_restaurants_combined",
                duration,
                True
            )
            
            return result
            
        except MCPCircuitBreakerOpenError as e:
            # Update circuit breaker trip count
            self.search_stats.circuit_breaker_trips += 1
            duration = time.time() - start_time
            performance_monitor.record_mcp_call(
                "restaurant-search-mcp",
                "search_restaurants_combined",
                duration,
                False,
                "circuit_breaker_open"
            )
            logger.error(f"Circuit breaker open for search MCP: {e}")
            raise MCPConnectionError(
                f"Search service temporarily unavailable (circuit breaker open)",
                "restaurant-search-mcp",
                e
            )
        except (MCPConnectionError, MCPToolCallError) as e:
            duration = time.time() - start_time
            error_type = type(e).__name__
            performance_monitor.record_mcp_call(
                "restaurant-search-mcp",
                "search_restaurants_combined",
                duration,
                False,
                error_type
            )
            raise
        except Exception as e:
            duration = time.time() - start_time
            performance_monitor.record_mcp_call(
                "restaurant-search-mcp",
                "search_restaurants_combined",
                duration,
                False,
                "unknown_error"
            )
            raise MCPToolCallError(
                f"Failed to execute search_restaurants_combined",
                "search_restaurants_combined",
                "restaurant-search-mcp",
                e
            )
    
    async def analyze_restaurants(
        self,
        restaurants: List[Restaurant],
        ranking_method: str = "sentiment_likes"
    ) -> Dict[str, Any]:
        """
        Call recommend_restaurants MCP tool on restaurant-reasoning-mcp server.
        
        Args:
            restaurants: List of restaurants to analyze
            ranking_method: Ranking method ("sentiment_likes" or "combined_sentiment")
            
        Returns:
            Reasoning response with recommendation and candidates
            
        Raises:
            MCPToolCallError: If the MCP tool call fails
            MCPConnectionError: If connection to MCP server fails
        """
        start_time = time.time()
        
        async def _analyze_operation():
            async with self._reasoning_semaphore:
                async with self._get_mcp_session(
                    self.reasoning_config, 
                    "restaurant-reasoning-mcp", 
                    self.reasoning_pool
                ) as session:
                    # Convert restaurants to dictionary format expected by MCP tool
                    restaurant_dicts = [self._restaurant_to_dict(r) for r in restaurants]
                    
                    params = {
                        "restaurants": restaurant_dicts,
                        "ranking_method": ranking_method
                    }
                    
                    logger.info(f"Calling recommend_restaurants with {len(restaurant_dicts)} restaurants, method: {ranking_method}")
                    
                    # Call the MCP tool
                    result = await session.call_tool("recommend_restaurants", params)
                    
                    # Parse the response
                    return self._parse_reasoning_response(result)
        
        try:
            result = await self.reasoning_circuit_breaker.call(
                self._execute_with_retry,
                _analyze_operation,
                self.reasoning_config,
                self.reasoning_stats,
                "restaurant-reasoning-mcp",
                "recommend_restaurants"
            )
            
            # Record successful performance metrics
            duration = time.time() - start_time
            performance_monitor.record_mcp_call(
                "restaurant-reasoning-mcp",
                "recommend_restaurants",
                duration,
                True
            )
            
            return result
            
        except MCPCircuitBreakerOpenError as e:
            # Update circuit breaker trip count
            self.reasoning_stats.circuit_breaker_trips += 1
            duration = time.time() - start_time
            performance_monitor.record_mcp_call(
                "restaurant-reasoning-mcp",
                "recommend_restaurants",
                duration,
                False,
                "circuit_breaker_open"
            )
            logger.error(f"Circuit breaker open for reasoning MCP: {e}")
            raise MCPConnectionError(
                f"Reasoning service temporarily unavailable (circuit breaker open)",
                "restaurant-reasoning-mcp",
                e
            )
        except (MCPConnectionError, MCPToolCallError) as e:
            duration = time.time() - start_time
            error_type = type(e).__name__
            performance_monitor.record_mcp_call(
                "restaurant-reasoning-mcp",
                "recommend_restaurants",
                duration,
                False,
                error_type
            )
            raise
        except Exception as e:
            duration = time.time() - start_time
            performance_monitor.record_mcp_call(
                "restaurant-reasoning-mcp",
                "recommend_restaurants",
                duration,
                False,
                "unknown_error"
            )
            raise MCPToolCallError(
                f"Failed to execute recommend_restaurants",
                "recommend_restaurants",
                "restaurant-reasoning-mcp",
                e
            )
    
    def _parse_search_response(self, result: CallToolResult) -> List[Restaurant]:
        """
        Parse restaurant search MCP tool response into Restaurant objects.
        
        Args:
            result: MCP tool call result
            
        Returns:
            List of Restaurant objects
            
        Raises:
            MCPToolCallError: If response parsing fails
        """
        try:
            if result.isError:
                raise MCPToolCallError(
                    f"MCP tool returned error: {result.content}",
                    "search_restaurants_combined",
                    "restaurant-search-mcp"
                )
            
            # Parse JSON response from MCP tool
            response_text = ""
            for content in result.content:
                if hasattr(content, 'text'):
                    response_text += content.text
                else:
                    response_text += str(content)
            
            response_data = json.loads(response_text)
            
            if not response_data.get("success", False):
                error_msg = response_data.get("error", {}).get("message", "Unknown error")
                raise MCPToolCallError(
                    f"Search MCP tool failed: {error_msg}",
                    "search_restaurants_combined",
                    "restaurant-search-mcp"
                )
            
            # Extract restaurants from response
            restaurants_data = response_data.get("data", {}).get("restaurants", [])
            restaurants = []
            
            for restaurant_data in restaurants_data:
                try:
                    restaurant = self._dict_to_restaurant(restaurant_data)
                    restaurants.append(restaurant)
                except Exception as e:
                    logger.warning(f"Failed to parse restaurant data: {e}")
                    continue
            
            logger.info(f"Successfully parsed {len(restaurants)} restaurants from search response")
            return restaurants
            
        except json.JSONDecodeError as e:
            raise MCPToolCallError(
                f"Failed to parse JSON response: {e}",
                "search_restaurants_combined",
                "restaurant-search-mcp",
                e
            )
        except Exception as e:
            raise MCPToolCallError(
                f"Failed to parse search response: {e}",
                "search_restaurants_combined",
                "restaurant-search-mcp",
                e
            )
    
    def _parse_reasoning_response(self, result: CallToolResult) -> Dict[str, Any]:
        """
        Parse restaurant reasoning MCP tool response.
        
        Args:
            result: MCP tool call result
            
        Returns:
            Dictionary with recommendation and candidates
            
        Raises:
            MCPToolCallError: If response parsing fails
        """
        try:
            if result.isError:
                raise MCPToolCallError(
                    f"MCP tool returned error: {result.content}",
                    "recommend_restaurants",
                    "restaurant-reasoning-mcp"
                )
            
            # Parse JSON response from MCP tool
            response_text = ""
            for content in result.content:
                if hasattr(content, 'text'):
                    response_text += content.text
                else:
                    response_text += str(content)
            
            response_data = json.loads(response_text)
            
            if not response_data.get("success", False):
                error_msg = response_data.get("error", {}).get("message", "Unknown error")
                raise MCPToolCallError(
                    f"Reasoning MCP tool failed: {error_msg}",
                    "recommend_restaurants",
                    "restaurant-reasoning-mcp"
                )
            
            # Extract recommendation and candidates
            data = response_data.get("data", {})
            
            result_dict = {
                "recommendation": data.get("recommendation"),
                "candidates": data.get("candidates", []),
                "ranking_method": data.get("ranking_method", "sentiment_likes"),
                "analysis_summary": data.get("analysis_summary", {})
            }
            
            logger.info(f"Successfully parsed reasoning response with {len(result_dict['candidates'])} candidates")
            return result_dict
            
        except json.JSONDecodeError as e:
            raise MCPToolCallError(
                f"Failed to parse JSON response: {e}",
                "recommend_restaurants",
                "restaurant-reasoning-mcp",
                e
            )
        except Exception as e:
            raise MCPToolCallError(
                f"Failed to parse reasoning response: {e}",
                "recommend_restaurants",
                "restaurant-reasoning-mcp",
                e
            )
    
    def _restaurant_to_dict(self, restaurant: Restaurant) -> Dict[str, Any]:
        """
        Convert Restaurant object to dictionary format expected by MCP tools.
        
        Args:
            restaurant: Restaurant object to convert
            
        Returns:
            Dictionary representation of restaurant
        """
        return {
            "id": restaurant.id,
            "name": restaurant.name,
            "address": restaurant.address,
            "district": restaurant.district,
            "meal_type": restaurant.meal_type,
            "sentiment": {
                "likes": restaurant.sentiment.likes,
                "dislikes": restaurant.sentiment.dislikes,
                "neutral": restaurant.sentiment.neutral
            },
            "price_range": restaurant.price_range,
            "operating_hours": restaurant.operating_hours,
            "location_category": restaurant.location_category,
            "metadata": restaurant.metadata
        }
    
    def _dict_to_restaurant(self, data: Dict[str, Any]) -> Restaurant:
        """
        Convert dictionary data to Restaurant object.
        
        Args:
            data: Dictionary with restaurant data
            
        Returns:
            Restaurant object
        """
        sentiment_data = data.get("sentiment", {})
        sentiment = Sentiment(
            likes=sentiment_data.get("likes", 0),
            dislikes=sentiment_data.get("dislikes", 0),
            neutral=sentiment_data.get("neutral", 0)
        )
        
        return Restaurant(
            id=data.get("id", ""),
            name=data.get("name", ""),
            address=data.get("address", ""),
            district=data.get("district", ""),
            meal_type=data.get("meal_type", []),
            sentiment=sentiment,
            price_range=data.get("price_range", ""),
            operating_hours=data.get("operating_hours", {}),
            location_category=data.get("location_category", ""),
            metadata=data.get("metadata")
        )
    
    async def search_and_analyze_parallel(
        self,
        search_requests: List[Tuple[Optional[str], Optional[str]]],
        ranking_method: str = "sentiment_likes"
    ) -> List[Dict[str, Any]]:
        """
        Perform multiple search and analyze operations in parallel.
        
        Args:
            search_requests: List of (district, meal_type) tuples for search
            ranking_method: Ranking method for analysis
            
        Returns:
            List of analysis results for each search request
        """
        async def _search_and_analyze(district: Optional[str], meal_type: Optional[str]) -> Dict[str, Any]:
            try:
                # Search restaurants
                restaurants = await self.search_restaurants(district, meal_type)
                
                if not restaurants:
                    return {
                        "search_criteria": {"district": district, "meal_type": meal_type},
                        "restaurants_found": 0,
                        "recommendation": None,
                        "candidates": [],
                        "error": "No restaurants found"
                    }
                
                # Analyze restaurants
                analysis_result = await self.analyze_restaurants(restaurants, ranking_method)
                
                return {
                    "search_criteria": {"district": district, "meal_type": meal_type},
                    "restaurants_found": len(restaurants),
                    **analysis_result
                }
                
            except Exception as e:
                logger.error(f"Error in parallel search and analyze for {district}, {meal_type}: {e}")
                return {
                    "search_criteria": {"district": district, "meal_type": meal_type},
                    "restaurants_found": 0,
                    "recommendation": None,
                    "candidates": [],
                    "error": str(e)
                }
        
        # Execute all requests in parallel
        tasks = [
            _search_and_analyze(district, meal_type)
            for district, meal_type in search_requests
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle any exceptions that weren't caught
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                district, meal_type = search_requests[i]
                processed_results.append({
                    "search_criteria": {"district": district, "meal_type": meal_type},
                    "restaurants_found": 0,
                    "recommendation": None,
                    "candidates": [],
                    "error": str(result)
                })
            else:
                processed_results.append(result)
        
        return processed_results
    
    async def batch_search_restaurants(
        self,
        search_requests: List[Tuple[Optional[str], Optional[str]]]
    ) -> List[List[Restaurant]]:
        """
        Perform multiple restaurant searches in parallel.
        
        Args:
            search_requests: List of (district, meal_type) tuples
            
        Returns:
            List of restaurant lists for each search request
        """
        async def _single_search(district: Optional[str], meal_type: Optional[str]) -> List[Restaurant]:
            try:
                return await self.search_restaurants(district, meal_type)
            except Exception as e:
                logger.error(f"Error in batch search for {district}, {meal_type}: {e}")
                return []
        
        tasks = [
            _single_search(district, meal_type)
            for district, meal_type in search_requests
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle exceptions
        processed_results = []
        for result in results:
            if isinstance(result, Exception):
                processed_results.append([])
            else:
                processed_results.append(result)
        
        return processed_results
    
    async def batch_analyze_restaurants(
        self,
        restaurant_lists: List[List[Restaurant]],
        ranking_method: str = "sentiment_likes"
    ) -> List[Dict[str, Any]]:
        """
        Perform multiple restaurant analyses in parallel.
        
        Args:
            restaurant_lists: List of restaurant lists to analyze
            ranking_method: Ranking method for analysis
            
        Returns:
            List of analysis results
        """
        async def _single_analysis(restaurants: List[Restaurant]) -> Dict[str, Any]:
            try:
                if not restaurants:
                    return {
                        "recommendation": None,
                        "candidates": [],
                        "ranking_method": ranking_method,
                        "analysis_summary": {"error": "No restaurants to analyze"}
                    }
                return await self.analyze_restaurants(restaurants, ranking_method)
            except Exception as e:
                logger.error(f"Error in batch analysis: {e}")
                return {
                    "recommendation": None,
                    "candidates": [],
                    "ranking_method": ranking_method,
                    "analysis_summary": {"error": str(e)}
                }
        
        tasks = [_single_analysis(restaurants) for restaurants in restaurant_lists]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle exceptions
        processed_results = []
        for result in results:
            if isinstance(result, Exception):
                processed_results.append({
                    "recommendation": None,
                    "candidates": [],
                    "ranking_method": ranking_method,
                    "analysis_summary": {"error": str(result)}
                })
            else:
                processed_results.append(result)
        
        return processed_results
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on both MCP servers.
        
        Returns:
            Dictionary with health status for each server
        """
        health_status = {
            "search_mcp": {"status": "unknown", "error": None},
            "reasoning_mcp": {"status": "unknown", "error": None}
        }
        
        # Check both servers in parallel
        async def _check_search():
            try:
                async with self._get_mcp_session(
                    self.search_config, 
                    "restaurant-search-mcp", 
                    self.search_pool
                ) as session:
                    tools = await session.list_tools()
                    health_status["search_mcp"]["status"] = "healthy"
                    health_status["search_mcp"]["tools_count"] = len(tools)
            except Exception as e:
                health_status["search_mcp"]["status"] = "unhealthy"
                health_status["search_mcp"]["error"] = str(e)
        
        async def _check_reasoning():
            try:
                async with self._get_mcp_session(
                    self.reasoning_config, 
                    "restaurant-reasoning-mcp", 
                    self.reasoning_pool
                ) as session:
                    tools = await session.list_tools()
                    health_status["reasoning_mcp"]["status"] = "healthy"
                    health_status["reasoning_mcp"]["tools_count"] = len(tools)
            except Exception as e:
                health_status["reasoning_mcp"]["status"] = "unhealthy"
                health_status["reasoning_mcp"]["error"] = str(e)
        
        # Run health checks in parallel
        await asyncio.gather(_check_search(), _check_reasoning(), return_exceptions=True)
        
        return health_status
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """
        Get connection statistics for monitoring.
        
        Returns:
            Dictionary with connection statistics
        """
        return {
            "search_mcp": {
                "total_calls": self.search_stats.total_calls,
                "successful_calls": self.search_stats.successful_calls,
                "failed_calls": self.search_stats.failed_calls,
                "consecutive_failures": self.search_stats.consecutive_failures,
                "circuit_breaker_trips": self.search_stats.circuit_breaker_trips,
                "success_rate": (
                    self.search_stats.successful_calls / self.search_stats.total_calls
                    if self.search_stats.total_calls > 0 else 0
                ),
                "average_response_time": self.search_stats.average_response_time,
                "last_successful_call": (
                    self.search_stats.last_successful_call.isoformat()
                    if self.search_stats.last_successful_call else None
                ),
                "last_failed_call": (
                    self.search_stats.last_failed_call.isoformat()
                    if self.search_stats.last_failed_call else None
                ),
                "error_counts_by_type": {
                    error_type.value: count 
                    for error_type, count in self.search_stats.error_counts_by_type.items()
                },
                "circuit_breaker": self.search_circuit_breaker.get_state_info(),
                "connection_pool": self.search_pool.get_pool_stats()
            },
            "reasoning_mcp": {
                "total_calls": self.reasoning_stats.total_calls,
                "successful_calls": self.reasoning_stats.successful_calls,
                "failed_calls": self.reasoning_stats.failed_calls,
                "consecutive_failures": self.reasoning_stats.consecutive_failures,
                "circuit_breaker_trips": self.reasoning_stats.circuit_breaker_trips,
                "success_rate": (
                    self.reasoning_stats.successful_calls / self.reasoning_stats.total_calls
                    if self.reasoning_stats.total_calls > 0 else 0
                ),
                "average_response_time": self.reasoning_stats.average_response_time,
                "last_successful_call": (
                    self.reasoning_stats.last_successful_call.isoformat()
                    if self.reasoning_stats.last_successful_call else None
                ),
                "last_failed_call": (
                    self.reasoning_stats.last_failed_call.isoformat()
                    if self.reasoning_stats.last_failed_call else None
                ),
                "error_counts_by_type": {
                    error_type.value: count 
                    for error_type, count in self.reasoning_stats.error_counts_by_type.items()
                },
                "circuit_breaker": self.reasoning_circuit_breaker.get_state_info(),
                "connection_pool": self.reasoning_pool.get_pool_stats()
            },
            "performance_summary": performance_monitor.get_mcp_performance_report()
        }
    
    async def shutdown(self):
        """Shutdown the MCP client manager and clean up resources"""
        logger.info("Shutting down MCP client manager")
        
        # Shutdown connection pools
        await self.search_pool.shutdown()
        await self.reasoning_pool.shutdown()
        
        # Shutdown thread pool
        self._thread_pool.shutdown(wait=True)
        
        logger.info("MCP client manager shutdown complete")