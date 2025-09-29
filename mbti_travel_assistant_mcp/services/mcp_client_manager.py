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
from services.connection_pool_manager import connection_pool_manager


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
        
        # Connection pools (using global connection pool manager)
        self.search_pool = MCPConnectionPool(self.search_config, "restaurant-search-mcp")
        self.reasoning_pool = MCPConnectionPool(self.reasoning_config, "restaurant-reasoning-mcp")
        
        # Semaphores for concurrent call limiting
        self._search_semaphore = asyncio.Semaphore(self.search_config.max_concurrent_calls)
        self._reasoning_semaphore = asyncio.Semaphore(self.reasoning_config.max_concurrent_calls)
        
        # Initialize connection pool manager with server endpoints
        self._initialize_connection_pools()
        
        # Circuit breakers
        self.search_circuit_breaker = MCPCircuitBreaker(self.search_config, "restaurant-search-mcp")
        self.reasoning_circuit_breaker = MCPCircuitBreaker(self.reasoning_config, "restaurant-reasoning-mcp")
        
        # Thread pool for CPU-intensive operations
        self._thread_pool = ThreadPoolExecutor(max_workers=4, thread_name_prefix="mcp-worker")
        
        logger.info(f"Initialized MCP client manager with search endpoint: {self.search_config.endpoint}")
        logger.info(f"Initialized MCP client manager with reasoning endpoint: {self.reasoning_config.endpoint}")
        logger.info(f"Connection pooling enabled: search={self.search_config.enable_connection_pooling}, reasoning={self.reasoning_config.enable_connection_pooling}")
    
    def _initialize_connection_pools(self):
        """Initialize connection pools for MCP servers"""
        try:
            # Warm up connections to both servers
            asyncio.create_task(self._warm_up_connections())
        except RuntimeError:
            # No event loop running, will warm up on first use
            pass
    
    async def _warm_up_connections(self):
        """Warm up connection pools for better initial performance"""
        try:
            server_endpoints = [
                self.search_config.endpoint,
                self.reasoning_config.endpoint
            ]
            
            await connection_pool_manager.warm_up_connections(
                server_endpoints,
                connections_per_server=2
            )
            
            logger.info("Warmed up MCP connection pools")
            
        except Exception as e:
            logger.warning(f"Failed to warm up connection pools: {e}")
    
    async def execute_parallel_mcp_operations(
        self,
        operations: List[Dict[str, Any]],
        max_concurrent: int = 5
    ) -> List[Any]:
        """
        Execute multiple MCP operations in parallel for improved performance.
        
        Args:
            operations: List of operation dictionaries with server, tool, and parameters
            max_concurrent: Maximum concurrent operations
            
        Returns:
            List of operation results
        """
        start_time = time.time()
        
        # Use connection pool manager for parallel execution
        results = await connection_pool_manager.execute_parallel_operations(
            operations,
            max_concurrent
        )
        
        # Record performance metrics
        duration = time.time() - start_time
        successful_ops = len([r for r in results if not isinstance(r, Exception)])
        failed_ops = len(results) - successful_ops
        
        performance_monitor.record_metric(
            MetricType.RESPONSE_TIME,
            duration,
            {"operation": "parallel_mcp_operations", "type": "batch"},
            {
                "total_operations": len(operations),
                "successful_operations": successful_ops,
                "failed_operations": failed_ops,
                "max_concurrent": max_concurrent
            }
        )
        
        # Record throughput
        throughput = len(operations) / duration if duration > 0 else 0
        performance_monitor.record_metric(
            MetricType.THROUGHPUT,
            throughput,
            {"operation": "parallel_mcp_operations"}
        )
        
        logger.info(
            f"Executed {len(operations)} parallel MCP operations in {duration:.2f}s "
            f"({throughput:.2f} ops/sec), {successful_ops} successful, {failed_ops} failed"
        )
        
        return results
    
    async def search_restaurants_parallel(
        self,
        search_requests: List[Dict[str, Any]],
        max_concurrent: int = 3
    ) -> List[List[Restaurant]]:
        """
        Execute multiple restaurant search requests in parallel.
        
        Args:
            search_requests: List of search request dictionaries
            max_concurrent: Maximum concurrent searches
            
        Returns:
            List of restaurant lists for each search request
        """
        operations = []
        
        for request in search_requests:
            operation = {
                "server_endpoint": self.search_config.endpoint,
                "tool_name": request.get("tool_name", "search_restaurants_by_meal_type"),
                "parameters": request.get("parameters", {}),
                "headers": {"Content-Type": "application/json"}
            }
            operations.append(operation)
        
        # Execute operations in parallel using performance monitoring
        results = await performance_monitor.measure_parallel_operations(
            [self._execute_search_operation(op) for op in operations],
            "parallel_restaurant_search",
            max_concurrent
        )
        
        # Process results and convert to Restaurant objects
        processed_results = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Parallel search operation failed: {result}")
                processed_results.append([])  # Empty list for failed operations
            else:
                try:
                    restaurants = self._parse_restaurant_search_response(result)
                    processed_results.append(restaurants)
                except Exception as e:
                    logger.error(f"Failed to parse search result: {e}")
                    processed_results.append([])
        
        return processed_results
    
    async def _execute_search_operation(self, operation: Dict[str, Any]) -> Any:
        """Execute a single search operation"""
        async with connection_pool_manager.get_connection(
            operation["server_endpoint"],
            operation.get("headers", {})
        ) as session:
            result = await session.call_tool(
                operation["tool_name"],
                operation["parameters"]
            )
            return result
    
    async def get_restaurant_recommendations_parallel(
        self,
        recommendation_requests: List[Dict[str, Any]],
        max_concurrent: int = 2
    ) -> List[Dict[str, Any]]:
        """
        Execute multiple restaurant recommendation requests in parallel.
        
        Args:
            recommendation_requests: List of recommendation request dictionaries
            max_concurrent: Maximum concurrent recommendations
            
        Returns:
            List of recommendation results
        """
        operations = []
        
        for request in recommendation_requests:
            operation = {
                "server_endpoint": self.reasoning_config.endpoint,
                "tool_name": "recommend_restaurants",
                "parameters": request.get("parameters", {}),
                "headers": {"Content-Type": "application/json"}
            }
            operations.append(operation)
        
        # Execute operations in parallel using performance monitoring
        results = await performance_monitor.measure_parallel_operations(
            [self._execute_recommendation_operation(op) for op in operations],
            "parallel_restaurant_recommendations",
            max_concurrent
        )
        
        # Process results
        processed_results = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Parallel recommendation operation failed: {result}")
                processed_results.append({})  # Empty dict for failed operations
            else:
                try:
                    recommendation = self._parse_recommendation_response(result)
                    processed_results.append(recommendation)
                except Exception as e:
                    logger.error(f"Failed to parse recommendation result: {e}")
                    processed_results.append({})
        
        return processed_results
    
    async def _execute_recommendation_operation(self, operation: Dict[str, Any]) -> Any:
        """Execute a single recommendation operation"""
        async with connection_pool_manager.get_connection(
            operation["server_endpoint"],
            operation.get("headers", {})
        ) as session:
            result = await session.call_tool(
                operation["tool_name"],
                operation["parameters"]
            )
            return result
    
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
            raise
    
    def get_comprehensive_performance_metrics(self) -> Dict[str, Any]:
        """
        Get comprehensive performance metrics for MCP operations.
        
        Returns:
            Dictionary with detailed performance metrics
        """
        # Get connection pool stats from global manager
        pool_stats = connection_pool_manager.get_pool_stats()
        
        # Record connection pool metrics in performance monitor
        performance_monitor.record_connection_pool_metrics(pool_stats)
        
        # Get MCP-specific performance report
        mcp_report = performance_monitor.get_mcp_performance_report()
        
        # Get performance optimization recommendations
        recommendations = performance_monitor.get_performance_optimization_recommendations()
        
        return {
            "connection_pools": pool_stats,
            "mcp_performance": mcp_report,
            "local_stats": {
                "search_mcp": {
                    "total_calls": self.search_stats.total_calls,
                    "successful_calls": self.search_stats.successful_calls,
                    "failed_calls": self.search_stats.failed_calls,
                    "average_response_time": self.search_stats.average_response_time,
                    "consecutive_failures": self.search_stats.consecutive_failures,
                    "circuit_breaker_trips": self.search_stats.circuit_breaker_trips,
                    "error_counts": {k.value: v for k, v in self.search_stats.error_counts_by_type.items()},
                    "circuit_breaker_state": self.search_circuit_breaker.get_state_info()
                },
                "reasoning_mcp": {
                    "total_calls": self.reasoning_stats.total_calls,
                    "successful_calls": self.reasoning_stats.successful_calls,
                    "failed_calls": self.reasoning_stats.failed_calls,
                    "average_response_time": self.reasoning_stats.average_response_time,
                    "consecutive_failures": self.reasoning_stats.consecutive_failures,
                    "circuit_breaker_trips": self.reasoning_stats.circuit_breaker_trips,
                    "error_counts": {k.value: v for k, v in self.reasoning_stats.error_counts_by_type.items()},
                    "circuit_breaker_state": self.reasoning_circuit_breaker.get_state_info()
                }
            },
            "performance_recommendations": recommendations,
            "system_metrics": performance_monitor.get_system_metrics()
        }
    
    async def optimize_performance(self) -> Dict[str, Any]:
        """
        Perform performance optimization tasks.
        
        Returns:
            Dictionary with optimization results
        """
        optimization_results = {
            "actions_taken": [],
            "recommendations": [],
            "before_metrics": {},
            "after_metrics": {}
        }
        
        # Get baseline metrics
        optimization_results["before_metrics"] = self.get_comprehensive_performance_metrics()
        
        # Clean up expired connections
        try:
            await connection_pool_manager._cleanup_expired_connections()
            optimization_results["actions_taken"].append("Cleaned up expired connections")
        except Exception as e:
            logger.warning(f"Failed to clean up expired connections: {e}")
        
        # Reset circuit breakers if they've been open too long
        try:
            if self.search_circuit_breaker.state == CircuitBreakerState.OPEN:
                # Force half-open state to test recovery
                self.search_circuit_breaker.state = CircuitBreakerState.HALF_OPEN
                optimization_results["actions_taken"].append("Reset search circuit breaker to half-open")
            
            if self.reasoning_circuit_breaker.state == CircuitBreakerState.OPEN:
                # Force half-open state to test recovery
                self.reasoning_circuit_breaker.state = CircuitBreakerState.HALF_OPEN
                optimization_results["actions_taken"].append("Reset reasoning circuit breaker to half-open")
        except Exception as e:
            logger.warning(f"Failed to reset circuit breakers: {e}")
        
        # Warm up connections if pools are empty
        try:
            pool_stats = connection_pool_manager.get_pool_stats()
            if pool_stats["global_stats"]["idle_connections"] < 2:
                await self._warm_up_connections()
                optimization_results["actions_taken"].append("Warmed up connection pools")
        except Exception as e:
            logger.warning(f"Failed to warm up connections: {e}")
        
        # Get post-optimization metrics
        optimization_results["after_metrics"] = self.get_comprehensive_performance_metrics()
        
        # Generate recommendations
        optimization_results["recommendations"] = performance_monitor.get_performance_optimization_recommendations()
        
        logger.info(f"Performance optimization completed: {len(optimization_results['actions_taken'])} actions taken")
        
        return optimization_results MCPToolCallError(
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
    
    # MBTI Travel Assistant Specific Methods
    
    async def search_breakfast_restaurants(
        self,
        district: str,
        used_restaurant_ids: Optional[set] = None
    ) -> List[Restaurant]:
        """
        Search for breakfast restaurants (06:00-11:29) in specified district.
        
        Args:
            district: District name for restaurant search
            used_restaurant_ids: Set of restaurant IDs already used (for uniqueness)
            
        Returns:
            List of breakfast restaurants in the district
            
        Raises:
            MCPToolCallError: If the MCP tool call fails
            MCPConnectionError: If connection to MCP server fails
        """
        logger.info(f"Searching breakfast restaurants in district: {district}")
        
        # Search for breakfast restaurants
        restaurants = await self.search_restaurants(district=district, meal_type="breakfast")
        
        # Filter out already used restaurants if provided
        if used_restaurant_ids:
            restaurants = [r for r in restaurants if r.id not in used_restaurant_ids]
        
        logger.info(f"Found {len(restaurants)} breakfast restaurants in {district}")
        return restaurants
    
    async def search_lunch_restaurants(
        self,
        districts: List[str],
        used_restaurant_ids: Optional[set] = None
    ) -> List[Restaurant]:
        """
        Search for lunch restaurants (11:30-17:29) in specified districts.
        
        Args:
            districts: List of district names (morning and afternoon spot districts)
            used_restaurant_ids: Set of restaurant IDs already used (for uniqueness)
            
        Returns:
            List of lunch restaurants in the districts
            
        Raises:
            MCPToolCallError: If the MCP tool call fails
            MCPConnectionError: If connection to MCP server fails
        """
        logger.info(f"Searching lunch restaurants in districts: {districts}")
        
        all_restaurants = []
        
        # Search in each district
        for district in districts:
            try:
                restaurants = await self.search_restaurants(district=district, meal_type="lunch")
                all_restaurants.extend(restaurants)
            except Exception as e:
                logger.warning(f"Failed to search lunch restaurants in {district}: {e}")
                continue
        
        # Remove duplicates based on restaurant ID
        unique_restaurants = {}
        for restaurant in all_restaurants:
            if restaurant.id not in unique_restaurants:
                unique_restaurants[restaurant.id] = restaurant
        
        restaurants = list(unique_restaurants.values())
        
        # Filter out already used restaurants if provided
        if used_restaurant_ids:
            restaurants = [r for r in restaurants if r.id not in used_restaurant_ids]
        
        logger.info(f"Found {len(restaurants)} unique lunch restaurants across districts")
        return restaurants
    
    async def search_dinner_restaurants(
        self,
        districts: List[str],
        used_restaurant_ids: Optional[set] = None
    ) -> List[Restaurant]:
        """
        Search for dinner restaurants (17:30-23:59) in specified districts.
        
        Args:
            districts: List of district names (afternoon and night spot districts)
            used_restaurant_ids: Set of restaurant IDs already used (for uniqueness)
            
        Returns:
            List of dinner restaurants in the districts
            
        Raises:
            MCPToolCallError: If the MCP tool call fails
            MCPConnectionError: If connection to MCP server fails
        """
        logger.info(f"Searching dinner restaurants in districts: {districts}")
        
        all_restaurants = []
        
        # Search in each district
        for district in districts:
            try:
                restaurants = await self.search_restaurants(district=district, meal_type="dinner")
                all_restaurants.extend(restaurants)
            except Exception as e:
                logger.warning(f"Failed to search dinner restaurants in {district}: {e}")
                continue
        
        # Remove duplicates based on restaurant ID
        unique_restaurants = {}
        for restaurant in all_restaurants:
            if restaurant.id not in unique_restaurants:
                unique_restaurants[restaurant.id] = restaurant
        
        restaurants = list(unique_restaurants.values())
        
        # Filter out already used restaurants if provided
        if used_restaurant_ids:
            restaurants = [r for r in restaurants if r.id not in used_restaurant_ids]
        
        logger.info(f"Found {len(restaurants)} unique dinner restaurants across districts")
        return restaurants
    
    async def get_restaurant_recommendations(
        self,
        restaurants: List[Restaurant],
        ranking_method: str = "sentiment_likes"
    ) -> Dict[str, Any]:
        """
        Get restaurant recommendations using reasoning MCP server.
        
        Args:
            restaurants: List of restaurants to analyze and rank
            ranking_method: Ranking method ("sentiment_likes" or "combined_sentiment")
            
        Returns:
            Dictionary with recommendation and candidates from reasoning MCP
            
        Raises:
            MCPToolCallError: If the MCP tool call fails
            MCPConnectionError: If connection to MCP server fails
        """
        logger.info(f"Getting restaurant recommendations for {len(restaurants)} restaurants")
        
        if not restaurants:
            return {
                "recommendation": None,
                "candidates": [],
                "ranking_method": ranking_method,
                "analysis_summary": {
                    "total_restaurants": 0,
                    "average_sentiment_likes": 0,
                    "average_positive_sentiment": 0
                }
            }
        
        # Use the existing analyze_restaurants method which calls reasoning MCP
        result = await self.analyze_restaurants(restaurants, ranking_method)
        
        logger.info(f"Received recommendations with {len(result.get('candidates', []))} candidates")
        return result
    
    async def assign_meal_restaurants(
        self,
        morning_district: str,
        afternoon_district: Optional[str] = None,
        night_district: Optional[str] = None,
        used_restaurant_ids: Optional[set] = None
    ) -> Dict[str, Optional[Restaurant]]:
        """
        Assign restaurants for all three meals of a day with district matching.
        
        Args:
            morning_district: District for morning tourist spot (for breakfast)
            afternoon_district: District for afternoon tourist spot (for lunch)
            night_district: District for night tourist spot (for dinner)
            used_restaurant_ids: Set of restaurant IDs already used (for uniqueness)
            
        Returns:
            Dictionary with breakfast, lunch, and dinner restaurant assignments
        """
        logger.info(f"Assigning meal restaurants for districts: morning={morning_district}, "
                   f"afternoon={afternoon_district}, night={night_district}")
        
        if used_restaurant_ids is None:
            used_restaurant_ids = set()
        
        assignments = {
            "breakfast": None,
            "lunch": None,
            "dinner": None
        }
        
        # Assign breakfast restaurant
        try:
            breakfast_restaurants = await self.search_breakfast_restaurants(
                morning_district, used_restaurant_ids
            )
            if breakfast_restaurants:
                # Get recommendation for best breakfast restaurant
                breakfast_rec = await self.get_restaurant_recommendations(breakfast_restaurants)
                if breakfast_rec.get("recommendation"):
                    assignments["breakfast"] = self._dict_to_restaurant(breakfast_rec["recommendation"])
                    used_restaurant_ids.add(assignments["breakfast"].id)
                    logger.info(f"Assigned breakfast restaurant: {assignments['breakfast'].name}")
        except Exception as e:
            logger.error(f"Failed to assign breakfast restaurant: {e}")
        
        # Assign lunch restaurant
        try:
            lunch_districts = [morning_district]
            if afternoon_district and afternoon_district != morning_district:
                lunch_districts.append(afternoon_district)
            
            lunch_restaurants = await self.search_lunch_restaurants(
                lunch_districts, used_restaurant_ids
            )
            if lunch_restaurants:
                # Get recommendation for best lunch restaurant
                lunch_rec = await self.get_restaurant_recommendations(lunch_restaurants)
                if lunch_rec.get("recommendation"):
                    assignments["lunch"] = self._dict_to_restaurant(lunch_rec["recommendation"])
                    used_restaurant_ids.add(assignments["lunch"].id)
                    logger.info(f"Assigned lunch restaurant: {assignments['lunch'].name}")
        except Exception as e:
            logger.error(f"Failed to assign lunch restaurant: {e}")
        
        # Assign dinner restaurant
        try:
            dinner_districts = []
            if afternoon_district:
                dinner_districts.append(afternoon_district)
            if night_district and night_district not in dinner_districts:
                dinner_districts.append(night_district)
            if not dinner_districts:
                dinner_districts = [morning_district]  # Fallback to morning district
            
            dinner_restaurants = await self.search_dinner_restaurants(
                dinner_districts, used_restaurant_ids
            )
            if dinner_restaurants:
                # Get recommendation for best dinner restaurant
                dinner_rec = await self.get_restaurant_recommendations(dinner_restaurants)
                if dinner_rec.get("recommendation"):
                    assignments["dinner"] = self._dict_to_restaurant(dinner_rec["recommendation"])
                    used_restaurant_ids.add(assignments["dinner"].id)
                    logger.info(f"Assigned dinner restaurant: {assignments['dinner'].name}")
        except Exception as e:
            logger.error(f"Failed to assign dinner restaurant: {e}")
        
        logger.info(f"Meal assignment complete: breakfast={'✓' if assignments['breakfast'] else '✗'}, "
                   f"lunch={'✓' if assignments['lunch'] else '✗'}, "
                   f"dinner={'✓' if assignments['dinner'] else '✗'}")
        
        return assignments
    
    async def get_restaurant_candidates(
        self,
        meal_type: str,
        districts: List[str],
        used_restaurant_ids: Optional[set] = None,
        limit: int = 10
    ) -> List[Restaurant]:
        """
        Get candidate restaurants for a specific meal type and districts.
        
        Args:
            meal_type: Type of meal ("breakfast", "lunch", "dinner")
            districts: List of districts to search in
            used_restaurant_ids: Set of restaurant IDs already used (for uniqueness)
            limit: Maximum number of candidates to return
            
        Returns:
            List of candidate restaurants
        """
        logger.info(f"Getting {meal_type} restaurant candidates in districts: {districts}")
        
        if used_restaurant_ids is None:
            used_restaurant_ids = set()
        
        all_restaurants = []
        
        # Search in each district
        for district in districts:
            try:
                restaurants = await self.search_restaurants(district=district, meal_type=meal_type)
                all_restaurants.extend(restaurants)
            except Exception as e:
                logger.warning(f"Failed to search {meal_type} restaurants in {district}: {e}")
                continue
        
        # Remove duplicates and used restaurants
        unique_restaurants = {}
        for restaurant in all_restaurants:
            if (restaurant.id not in unique_restaurants and 
                restaurant.id not in used_restaurant_ids):
                unique_restaurants[restaurant.id] = restaurant
        
        candidates = list(unique_restaurants.values())
        
        # Get recommendations to rank candidates
        if candidates:
            try:
                rec_result = await self.get_restaurant_recommendations(candidates)
                if rec_result.get("candidates"):
                    # Convert candidates back to Restaurant objects and limit
                    ranked_candidates = []
                    for candidate_dict in rec_result["candidates"][:limit]:
                        try:
                            candidate = self._dict_to_restaurant(candidate_dict)
                            ranked_candidates.append(candidate)
                        except Exception as e:
                            logger.warning(f"Failed to convert candidate to Restaurant: {e}")
                            continue
                    candidates = ranked_candidates
                else:
                    candidates = candidates[:limit]
            except Exception as e:
                logger.warning(f"Failed to get recommendations for candidates: {e}")
                candidates = candidates[:limit]
        
        logger.info(f"Found {len(candidates)} {meal_type} restaurant candidates")
        return candidates
    
    async def validate_restaurant_operating_hours(
        self,
        restaurant: Restaurant,
        meal_type: str
    ) -> bool:
        """
        Validate that restaurant operating hours match the meal type.
        
        Args:
            restaurant: Restaurant to validate
            meal_type: Expected meal type ("breakfast", "lunch", "dinner")
            
        Returns:
            True if operating hours match meal type, False otherwise
        """
        if not restaurant.operating_hours:
            # No operating hours specified, assume always open
            return True
        
        # Define meal time ranges
        meal_time_ranges = {
            "breakfast": ("06:00", "11:29"),
            "lunch": ("11:30", "17:29"),
            "dinner": ("17:30", "23:59")
        }
        
        if meal_type not in meal_time_ranges:
            logger.warning(f"Unknown meal type: {meal_type}")
            return False
        
        expected_start, expected_end = meal_time_ranges[meal_type]
        
        # Check if any operating hours overlap with meal time
        for day_type in ["mon_fri", "sat_sun", "public_holiday"]:
            hours_list = getattr(restaurant.operating_hours, day_type, [])
            for time_range in hours_list:
                if self._time_ranges_overlap(time_range, f"{expected_start} - {expected_end}"):
                    return True
        
        return False
    
    def _time_ranges_overlap(self, range1: str, range2: str) -> bool:
        """
        Check if two time ranges overlap.
        
        Args:
            range1: First time range (e.g., "09:00 - 18:00")
            range2: Second time range (e.g., "11:30 - 17:29")
            
        Returns:
            True if ranges overlap, False otherwise
        """
        try:
            # Parse time ranges
            start1, end1 = self._parse_time_range(range1)
            start2, end2 = self._parse_time_range(range2)
            
            # Check for overlap
            return start1 <= end2 and start2 <= end1
            
        except Exception as e:
            logger.warning(f"Failed to parse time ranges '{range1}' and '{range2}': {e}")
            return True  # Assume overlap if parsing fails
    
    def _parse_time_range(self, time_range: str) -> Tuple[int, int]:
        """
        Parse time range string into start and end minutes from midnight.
        
        Args:
            time_range: Time range string (e.g., "09:00 - 18:00")
            
        Returns:
            Tuple of (start_minutes, end_minutes) from midnight
        """
        import re
        
        # Extract start and end times
        match = re.match(r'(\d{2}):(\d{2})\s*-\s*(\d{2}):(\d{2})', time_range.strip())
        if not match:
            raise ValueError(f"Invalid time range format: {time_range}")
        
        start_hour, start_min, end_hour, end_min = map(int, match.groups())
        
        # Convert to minutes from midnight
        start_minutes = start_hour * 60 + start_min
        end_minutes = end_hour * 60 + end_min
        
        return start_minutes, end_minutes
    
    async def assign_3day_itinerary_restaurants(
        self,
        day_districts: List[Dict[str, str]]
    ) -> Dict[str, Dict[str, Optional[Restaurant]]]:
        """
        Assign restaurants for a complete 3-day itinerary with uniqueness enforcement.
        
        Args:
            day_districts: List of 3 dictionaries, each containing:
                - morning: Morning tourist spot district
                - afternoon: Afternoon tourist spot district (optional)
                - night: Night tourist spot district (optional)
                
        Returns:
            Dictionary with restaurant assignments for each day:
            {
                "day_1": {"breakfast": Restaurant, "lunch": Restaurant, "dinner": Restaurant},
                "day_2": {"breakfast": Restaurant, "lunch": Restaurant, "dinner": Restaurant},
                "day_3": {"breakfast": Restaurant, "lunch": Restaurant, "dinner": Restaurant}
            }
        """
        logger.info("Assigning restaurants for complete 3-day itinerary")
        
        if len(day_districts) != 3:
            raise ValueError("day_districts must contain exactly 3 days")
        
        used_restaurant_ids = set()
        itinerary_restaurants = {}
        
        for day_num, districts in enumerate(day_districts, 1):
            day_key = f"day_{day_num}"
            logger.info(f"Assigning restaurants for {day_key}")
            
            # Assign meals for this day
            day_assignments = await self.assign_meal_restaurants(
                morning_district=districts["morning"],
                afternoon_district=districts.get("afternoon"),
                night_district=districts.get("night"),
                used_restaurant_ids=used_restaurant_ids
            )
            
            itinerary_restaurants[day_key] = day_assignments
            
            # Update used restaurant IDs
            for meal, restaurant in day_assignments.items():
                if restaurant:
                    used_restaurant_ids.add(restaurant.id)
        
        # Log summary
        total_assigned = sum(
            1 for day in itinerary_restaurants.values()
            for restaurant in day.values()
            if restaurant is not None
        )
        
        logger.info(f"3-day itinerary restaurant assignment complete: "
                   f"{total_assigned}/9 meals assigned, "
                   f"{len(used_restaurant_ids)} unique restaurants used")
        
        return itinerary_restaurants
    
    async def generate_restaurant_candidates_for_itinerary(
        self,
        day_districts: List[Dict[str, str]],
        used_restaurant_ids: Optional[set] = None,
        candidates_per_meal: int = 5
    ) -> Dict[str, Dict[str, List[Restaurant]]]:
        """
        Generate restaurant candidates for a complete 3-day itinerary.
        
        Args:
            day_districts: List of 3 dictionaries with district information
            used_restaurant_ids: Set of restaurant IDs already used
            candidates_per_meal: Number of candidates per meal type
            
        Returns:
            Dictionary with candidate restaurants for each day and meal:
            {
                "day_1": {
                    "breakfast": [Restaurant, ...],
                    "lunch": [Restaurant, ...],
                    "dinner": [Restaurant, ...]
                },
                ...
            }
        """
        logger.info("Generating restaurant candidates for 3-day itinerary")
        
        if used_restaurant_ids is None:
            used_restaurant_ids = set()
        
        candidates = {}
        
        for day_num, districts in enumerate(day_districts, 1):
            day_key = f"day_{day_num}"
            candidates[day_key] = {}
            
            # Generate breakfast candidates
            try:
                breakfast_candidates = await self.get_restaurant_candidates(
                    meal_type="breakfast",
                    districts=[districts["morning"]],
                    used_restaurant_ids=used_restaurant_ids,
                    limit=candidates_per_meal
                )
                candidates[day_key]["breakfast"] = breakfast_candidates
            except Exception as e:
                logger.error(f"Failed to get breakfast candidates for {day_key}: {e}")
                candidates[day_key]["breakfast"] = []
            
            # Generate lunch candidates
            try:
                lunch_districts = [districts["morning"]]
                if districts.get("afternoon"):
                    lunch_districts.append(districts["afternoon"])
                
                lunch_candidates = await self.get_restaurant_candidates(
                    meal_type="lunch",
                    districts=lunch_districts,
                    used_restaurant_ids=used_restaurant_ids,
                    limit=candidates_per_meal
                )
                candidates[day_key]["lunch"] = lunch_candidates
            except Exception as e:
                logger.error(f"Failed to get lunch candidates for {day_key}: {e}")
                candidates[day_key]["lunch"] = []
            
            # Generate dinner candidates
            try:
                dinner_districts = []
                if districts.get("afternoon"):
                    dinner_districts.append(districts["afternoon"])
                if districts.get("night"):
                    dinner_districts.append(districts["night"])
                if not dinner_districts:
                    dinner_districts = [districts["morning"]]
                
                dinner_candidates = await self.get_restaurant_candidates(
                    meal_type="dinner",
                    districts=dinner_districts,
                    used_restaurant_ids=used_restaurant_ids,
                    limit=candidates_per_meal
                )
                candidates[day_key]["dinner"] = dinner_candidates
            except Exception as e:
                logger.error(f"Failed to get dinner candidates for {day_key}: {e}")
                candidates[day_key]["dinner"] = []
        
        # Log summary
        total_candidates = sum(
            len(meal_candidates)
            for day in candidates.values()
            for meal_candidates in day.values()
        )
        
        logger.info(f"Generated {total_candidates} restaurant candidates across 3 days")
        return candidates
    
    # Error Handling and Fallback Strategies
    
    async def search_restaurants_with_fallback(
        self,
        primary_district: str,
        meal_type: str,
        fallback_districts: Optional[List[str]] = None,
        used_restaurant_ids: Optional[set] = None
    ) -> List[Restaurant]:
        """
        Search for restaurants with fallback to adjacent districts if primary search fails.
        
        Args:
            primary_district: Primary district to search in
            meal_type: Type of meal ("breakfast", "lunch", "dinner")
            fallback_districts: List of fallback districts to try
            used_restaurant_ids: Set of restaurant IDs already used
            
        Returns:
            List of restaurants found
        """
        if used_restaurant_ids is None:
            used_restaurant_ids = set()
        
        # Try primary district first
        try:
            logger.info(f"Searching {meal_type} restaurants in primary district: {primary_district}")
            restaurants = await self.search_restaurants(district=primary_district, meal_type=meal_type)
            
            # Filter out used restaurants
            available_restaurants = [r for r in restaurants if r.id not in used_restaurant_ids]
            
            if available_restaurants:
                logger.info(f"Found {len(available_restaurants)} {meal_type} restaurants in primary district")
                return available_restaurants
            else:
                logger.warning(f"No available {meal_type} restaurants in primary district {primary_district}")
        
        except Exception as e:
            logger.error(f"Failed to search {meal_type} restaurants in primary district {primary_district}: {e}")
        
        # Try fallback districts
        if fallback_districts:
            for fallback_district in fallback_districts:
                try:
                    logger.info(f"Trying fallback district for {meal_type}: {fallback_district}")
                    restaurants = await self.search_restaurants(district=fallback_district, meal_type=meal_type)
                    
                    # Filter out used restaurants
                    available_restaurants = [r for r in restaurants if r.id not in used_restaurant_ids]
                    
                    if available_restaurants:
                        logger.info(f"Found {len(available_restaurants)} {meal_type} restaurants in fallback district")
                        return available_restaurants
                
                except Exception as e:
                    logger.error(f"Failed to search {meal_type} restaurants in fallback district {fallback_district}: {e}")
                    continue
        
        # Try searching without district filter as last resort
        try:
            logger.warning(f"Trying {meal_type} search without district filter as last resort")
            restaurants = await self.search_restaurants(meal_type=meal_type)
            
            # Filter out used restaurants
            available_restaurants = [r for r in restaurants if r.id not in used_restaurant_ids]
            
            if available_restaurants:
                logger.info(f"Found {len(available_restaurants)} {meal_type} restaurants without district filter")
                return available_restaurants
        
        except Exception as e:
            logger.error(f"Failed to search {meal_type} restaurants without district filter: {e}")
        
        logger.error(f"All fallback strategies failed for {meal_type} restaurant search")
        return []
    
    async def assign_meal_with_fallback(
        self,
        meal_type: str,
        primary_district: str,
        fallback_districts: Optional[List[str]] = None,
        used_restaurant_ids: Optional[set] = None
    ) -> Optional[Restaurant]:
        """
        Assign a restaurant for a specific meal with fallback strategies.
        
        Args:
            meal_type: Type of meal ("breakfast", "lunch", "dinner")
            primary_district: Primary district to search in
            fallback_districts: List of fallback districts to try
            used_restaurant_ids: Set of restaurant IDs already used
            
        Returns:
            Assigned restaurant or None if all strategies fail
        """
        logger.info(f"Assigning {meal_type} restaurant with fallback strategies")
        
        if used_restaurant_ids is None:
            used_restaurant_ids = set()
        
        # Search with fallback districts
        restaurants = await self.search_restaurants_with_fallback(
            primary_district=primary_district,
            meal_type=meal_type,
            fallback_districts=fallback_districts,
            used_restaurant_ids=used_restaurant_ids
        )
        
        if not restaurants:
            logger.error(f"No {meal_type} restaurants found with any fallback strategy")
            return None
        
        # Get recommendation for the best restaurant
        try:
            recommendation_result = await self.get_restaurant_recommendations(restaurants)
            
            if recommendation_result.get("recommendation"):
                restaurant = self._dict_to_restaurant(recommendation_result["recommendation"])
                logger.info(f"Successfully assigned {meal_type} restaurant: {restaurant.name}")
                return restaurant
            else:
                # Fallback to first available restaurant
                restaurant = restaurants[0]
                logger.warning(f"Using first available {meal_type} restaurant as fallback: {restaurant.name}")
                return restaurant
        
        except Exception as e:
            logger.error(f"Failed to get recommendation for {meal_type} restaurants: {e}")
            
            # Fallback to first available restaurant
            if restaurants:
                restaurant = restaurants[0]
                logger.warning(f"Using first available {meal_type} restaurant as final fallback: {restaurant.name}")
                return restaurant
        
        return None
    
    async def create_restaurant_assignment_placeholder(
        self,
        meal_type: str,
        district: str,
        error_message: str
    ) -> Dict[str, Any]:
        """
        Create a placeholder restaurant assignment when MCP servers are unavailable.
        
        Args:
            meal_type: Type of meal ("breakfast", "lunch", "dinner")
            district: District where restaurant was needed
            error_message: Error message explaining the failure
            
        Returns:
            Dictionary with placeholder restaurant information
        """
        return {
            "id": f"placeholder_{meal_type}_{district}",
            "name": f"Restaurant Assignment Unavailable",
            "address": f"District: {district}",
            "meal_type": [meal_type],
            "district": district,
            "error": {
                "type": "mcp_service_unavailable",
                "message": error_message,
                "suggested_actions": [
                    "Retry the request later",
                    "Check MCP server connectivity",
                    "Use cached restaurant data if available"
                ]
            },
            "is_placeholder": True
        }
    
    async def assign_meal_restaurants_with_comprehensive_fallback(
        self,
        morning_district: str,
        afternoon_district: Optional[str] = None,
        night_district: Optional[str] = None,
        used_restaurant_ids: Optional[set] = None,
        adjacent_districts: Optional[Dict[str, List[str]]] = None
    ) -> Dict[str, Any]:
        """
        Assign restaurants for all meals with comprehensive fallback strategies.
        
        Args:
            morning_district: District for morning tourist spot
            afternoon_district: District for afternoon tourist spot
            night_district: District for night tourist spot
            used_restaurant_ids: Set of restaurant IDs already used
            adjacent_districts: Dictionary mapping districts to adjacent districts
            
        Returns:
            Dictionary with restaurant assignments and error information
        """
        logger.info("Assigning meal restaurants with comprehensive fallback strategies")
        
        if used_restaurant_ids is None:
            used_restaurant_ids = set()
        
        if adjacent_districts is None:
            adjacent_districts = {}
        
        assignments = {
            "breakfast": None,
            "lunch": None,
            "dinner": None,
            "errors": [],
            "fallback_used": []
        }
        
        # Assign breakfast with fallback
        try:
            breakfast_fallbacks = adjacent_districts.get(morning_district, [])
            breakfast_restaurant = await self.assign_meal_with_fallback(
                meal_type="breakfast",
                primary_district=morning_district,
                fallback_districts=breakfast_fallbacks,
                used_restaurant_ids=used_restaurant_ids
            )
            
            if breakfast_restaurant:
                assignments["breakfast"] = breakfast_restaurant
                used_restaurant_ids.add(breakfast_restaurant.id)
            else:
                error_msg = f"Failed to assign breakfast restaurant in {morning_district}"
                assignments["errors"].append(error_msg)
                assignments["breakfast"] = await self.create_restaurant_assignment_placeholder(
                    "breakfast", morning_district, error_msg
                )
        
        except Exception as e:
            error_msg = f"Critical error assigning breakfast restaurant: {str(e)}"
            logger.error(error_msg)
            assignments["errors"].append(error_msg)
            assignments["breakfast"] = await self.create_restaurant_assignment_placeholder(
                "breakfast", morning_district, error_msg
            )
        
        # Assign lunch with fallback
        try:
            lunch_districts = [morning_district]
            if afternoon_district and afternoon_district != morning_district:
                lunch_districts.append(afternoon_district)
            
            lunch_fallbacks = []
            for district in lunch_districts:
                lunch_fallbacks.extend(adjacent_districts.get(district, []))
            
            # Remove duplicates
            lunch_fallbacks = list(set(lunch_fallbacks) - set(lunch_districts))
            
            lunch_restaurant = await self.assign_meal_with_fallback(
                meal_type="lunch",
                primary_district=lunch_districts[0],
                fallback_districts=lunch_districts[1:] + lunch_fallbacks,
                used_restaurant_ids=used_restaurant_ids
            )
            
            if lunch_restaurant:
                assignments["lunch"] = lunch_restaurant
                used_restaurant_ids.add(lunch_restaurant.id)
            else:
                error_msg = f"Failed to assign lunch restaurant in districts {lunch_districts}"
                assignments["errors"].append(error_msg)
                assignments["lunch"] = await self.create_restaurant_assignment_placeholder(
                    "lunch", lunch_districts[0], error_msg
                )
        
        except Exception as e:
            error_msg = f"Critical error assigning lunch restaurant: {str(e)}"
            logger.error(error_msg)
            assignments["errors"].append(error_msg)
            assignments["lunch"] = await self.create_restaurant_assignment_placeholder(
                "lunch", afternoon_district or morning_district, error_msg
            )
        
        # Assign dinner with fallback
        try:
            dinner_districts = []
            if afternoon_district:
                dinner_districts.append(afternoon_district)
            if night_district and night_district not in dinner_districts:
                dinner_districts.append(night_district)
            if not dinner_districts:
                dinner_districts = [morning_district]
            
            dinner_fallbacks = []
            for district in dinner_districts:
                dinner_fallbacks.extend(adjacent_districts.get(district, []))
            
            # Remove duplicates
            dinner_fallbacks = list(set(dinner_fallbacks) - set(dinner_districts))
            
            dinner_restaurant = await self.assign_meal_with_fallback(
                meal_type="dinner",
                primary_district=dinner_districts[0],
                fallback_districts=dinner_districts[1:] + dinner_fallbacks,
                used_restaurant_ids=used_restaurant_ids
            )
            
            if dinner_restaurant:
                assignments["dinner"] = dinner_restaurant
                used_restaurant_ids.add(dinner_restaurant.id)
            else:
                error_msg = f"Failed to assign dinner restaurant in districts {dinner_districts}"
                assignments["errors"].append(error_msg)
                assignments["dinner"] = await self.create_restaurant_assignment_placeholder(
                    "dinner", dinner_districts[0], error_msg
                )
        
        except Exception as e:
            error_msg = f"Critical error assigning dinner restaurant: {str(e)}"
            logger.error(error_msg)
            assignments["errors"].append(error_msg)
            assignments["dinner"] = await self.create_restaurant_assignment_placeholder(
                "dinner", night_district or afternoon_district or morning_district, error_msg
            )
        
        # Log summary
        successful_assignments = sum(1 for meal in ["breakfast", "lunch", "dinner"] 
                                   if assignments[meal] and not assignments[meal].get("is_placeholder"))
        
        logger.info(f"Meal assignment with fallback complete: {successful_assignments}/3 successful, "
                   f"{len(assignments['errors'])} errors")
        
        return assignments

    async def shutdown(self):
        """Shutdown the MCP client manager and clean up resources"""
        logger.info("Shutting down MCP client manager")
        
        # Shutdown connection pools
        await self.search_pool.shutdown()
        await self.reasoning_pool.shutdown()
        
        # Shutdown thread pool
        self._thread_pool.shutdown(wait=True)
        
        logger.info("MCP client manager shutdown complete")