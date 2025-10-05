"""
Enhanced Health Check Service

This module implements the Enhanced Health Check Service orchestrator that coordinates
dual health monitoring using both MCP tools/list requests and REST API health checks
with concurrent execution, connection pooling, and resource management.
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
import aiohttp
from contextlib import asynccontextmanager

from models.dual_health_models import (
    EnhancedServerConfig,
    MCPHealthCheckResult,
    RESTHealthCheckResult,
    DualHealthCheckResult,
    AggregationConfig,
    ServerStatus
)
from services.mcp_health_check_client import MCPHealthCheckClient
from services.rest_health_check_client import RESTHealthCheckClient
from services.health_result_aggregator import HealthResultAggregator
from services.authentication_service import AuthenticationService


logger = logging.getLogger(__name__)


class ConnectionPoolManager:
    """
    Connection pool manager for both MCP and REST connections.
    
    Manages separate connection pools with appropriate limits and timeouts
    for optimal resource utilization.
    """
    
    def __init__(
        self,
        mcp_pool_size: int = 10,
        rest_pool_size: int = 15,
        connection_timeout: int = 30,
        total_timeout: int = 60
    ):
        """
        Initialize connection pool manager.
        
        Args:
            mcp_pool_size: Maximum connections for MCP pool
            rest_pool_size: Maximum connections for REST pool
            connection_timeout: Connection timeout in seconds
            total_timeout: Total request timeout in seconds
        """
        self.mcp_pool_size = mcp_pool_size
        self.rest_pool_size = rest_pool_size
        self.connection_timeout = connection_timeout
        self.total_timeout = total_timeout
        
        self._mcp_session: Optional[aiohttp.ClientSession] = None
        self._rest_session: Optional[aiohttp.ClientSession] = None
        self._session_lock = asyncio.Lock()
    
    async def get_mcp_session(self) -> aiohttp.ClientSession:
        """Get or create MCP client session."""
        async with self._session_lock:
            if self._mcp_session is None or self._mcp_session.closed:
                connector = aiohttp.TCPConnector(
                    limit=self.mcp_pool_size,
                    limit_per_host=5,
                    ttl_dns_cache=300,
                    use_dns_cache=True,
                    keepalive_timeout=30,
                    enable_cleanup_closed=True
                )
                
                timeout = aiohttp.ClientTimeout(
                    total=self.total_timeout,
                    connect=self.connection_timeout
                )
                
                self._mcp_session = aiohttp.ClientSession(
                    connector=connector,
                    timeout=timeout,
                    headers={
                        'User-Agent': 'Enhanced-MCP-Status-Check/1.0 (MCP-Client)'
                    }
                )
                
                logger.debug(f"Created MCP session with pool size {self.mcp_pool_size}")
            
            return self._mcp_session
    
    async def get_rest_session(self) -> aiohttp.ClientSession:
        """Get or create REST client session."""
        async with self._session_lock:
            if self._rest_session is None or self._rest_session.closed:
                connector = aiohttp.TCPConnector(
                    limit=self.rest_pool_size,
                    limit_per_host=8,
                    ttl_dns_cache=300,
                    use_dns_cache=True,
                    keepalive_timeout=30,
                    enable_cleanup_closed=True
                )
                
                timeout = aiohttp.ClientTimeout(
                    total=self.total_timeout,
                    connect=self.connection_timeout
                )
                
                self._rest_session = aiohttp.ClientSession(
                    connector=connector,
                    timeout=timeout,
                    headers={
                        'User-Agent': 'Enhanced-MCP-Status-Check/1.0 (REST-Client)'
                    }
                )
                
                logger.debug(f"Created REST session with pool size {self.rest_pool_size}")
            
            return self._rest_session
    
    async def close_sessions(self):
        """Close all client sessions."""
        async with self._session_lock:
            if self._mcp_session and not self._mcp_session.closed:
                await self._mcp_session.close()
                logger.debug("Closed MCP session")
            
            if self._rest_session and not self._rest_session.closed:
                await self._rest_session.close()
                logger.debug("Closed REST session")
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close_sessions()


class EnhancedHealthCheckService:
    """
    Enhanced Health Check Service orchestrator.
    
    This service coordinates dual health monitoring using both MCP tools/list requests
    and REST API health checks with concurrent execution, intelligent aggregation,
    and comprehensive resource management.
    """
    
    def __init__(
        self,
        aggregation_config: Optional[AggregationConfig] = None,
        max_concurrent_servers: int = 10,
        max_concurrent_per_server: int = 2,
        connection_pool_manager: Optional[ConnectionPoolManager] = None,
        auth_service: Optional[AuthenticationService] = None
    ):
        """
        Initialize Enhanced Health Check Service.
        
        Args:
            aggregation_config: Configuration for result aggregation
            max_concurrent_servers: Maximum concurrent server checks
            max_concurrent_per_server: Maximum concurrent checks per server
            connection_pool_manager: Optional connection pool manager
            auth_service: Optional authentication service for secure requests
        """
        self.aggregator = HealthResultAggregator(aggregation_config)
        self.max_concurrent_servers = max_concurrent_servers
        self.max_concurrent_per_server = max_concurrent_per_server
        
        # Connection pool manager
        self.pool_manager = connection_pool_manager or ConnectionPoolManager()
        self._owned_pool_manager = connection_pool_manager is None
        
        # Authentication service
        self.auth_service = auth_service
        self._owned_auth_service = auth_service is None
        
        # Semaphores for concurrency control
        self.server_semaphore = asyncio.Semaphore(max_concurrent_servers)
        self.per_server_semaphore = asyncio.Semaphore(max_concurrent_per_server)
        
        # Cancellation support
        self._active_tasks: Dict[str, asyncio.Task] = {}
        self._cancellation_event = asyncio.Event()
    
    async def __aenter__(self):
        """Async context manager entry."""
        if self._owned_auth_service and self.auth_service is None:
            # Create authentication service with shared session
            mcp_session = await self.pool_manager.get_mcp_session()
            self.auth_service = AuthenticationService(mcp_session)
            await self.auth_service.__aenter__()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.cancel_all_checks()
        if self._owned_auth_service and self.auth_service:
            await self.auth_service.__aexit__(exc_type, exc_val, exc_tb)
        if self._owned_pool_manager:
            await self.pool_manager.close_sessions()
    
    async def perform_mcp_health_check(
        self,
        server_config: EnhancedServerConfig
    ) -> MCPHealthCheckResult:
        """
        Perform MCP health check for a single server.
        
        Args:
            server_config: Enhanced server configuration
            
        Returns:
            MCPHealthCheckResult: MCP health check result
        """
        if not server_config.mcp_enabled:
            return MCPHealthCheckResult(
                server_name=server_config.server_name,
                timestamp=datetime.now(),
                success=False,
                response_time_ms=0.0,
                connection_error="MCP health checks disabled in configuration"
            )
        
        mcp_session = await self.pool_manager.get_mcp_session()
        
        async with MCPHealthCheckClient(session=mcp_session, auth_service=self.auth_service) as mcp_client:
            return await mcp_client.perform_mcp_health_check(server_config)
    
    async def perform_rest_health_check(
        self,
        server_config: EnhancedServerConfig
    ) -> RESTHealthCheckResult:
        """
        Perform REST health check for a single server.
        
        Args:
            server_config: Enhanced server configuration
            
        Returns:
            RESTHealthCheckResult: REST health check result
        """
        if not server_config.rest_enabled:
            return RESTHealthCheckResult(
                server_name=server_config.server_name,
                timestamp=datetime.now(),
                success=False,
                response_time_ms=0.0,
                health_endpoint_url=server_config.rest_health_endpoint_url,
                connection_error="REST health checks disabled in configuration"
            )
        
        rest_session = await self.pool_manager.get_rest_session()
        
        async with RESTHealthCheckClient(session=rest_session, auth_service=self.auth_service) as rest_client:
            return await rest_client.perform_rest_health_check(server_config)
    
    async def perform_dual_health_check(
        self,
        server_config: EnhancedServerConfig,
        timeout_override: Optional[int] = None
    ) -> DualHealthCheckResult:
        """
        Perform concurrent MCP and REST health checks for a server.
        
        Args:
            server_config: Enhanced server configuration
            timeout_override: Optional timeout override in seconds
            
        Returns:
            DualHealthCheckResult: Combined dual health check result
        """
        start_time = time.time()
        server_name = server_config.server_name
        
        logger.info(f"Starting dual health check for {server_name}")
        
        # Create tasks for concurrent execution
        mcp_task = None
        rest_task = None
        
        try:
            async with self.per_server_semaphore:
                # Create concurrent tasks
                tasks = []
                
                if server_config.mcp_enabled:
                    mcp_task = asyncio.create_task(
                        self.perform_mcp_health_check(server_config),
                        name=f"mcp-{server_name}"
                    )
                    tasks.append(mcp_task)
                    self._active_tasks[f"mcp-{server_name}"] = mcp_task
                
                if server_config.rest_enabled:
                    rest_task = asyncio.create_task(
                        self.perform_rest_health_check(server_config),
                        name=f"rest-{server_name}"
                    )
                    tasks.append(rest_task)
                    self._active_tasks[f"rest-{server_name}"] = rest_task
                
                if not tasks:
                    # No checks enabled
                    logger.warning(f"No health checks enabled for {server_name}")
                    return DualHealthCheckResult(
                        server_name=server_name,
                        timestamp=datetime.now(),
                        overall_status=ServerStatus.UNKNOWN,
                        overall_success=False,
                        mcp_error_message="No health checks enabled",
                        rest_error_message="No health checks enabled",
                        available_paths=["none"]
                    )
                
                # Wait for all tasks with timeout
                timeout = timeout_override or max(
                    server_config.mcp_timeout_seconds if server_config.mcp_enabled else 0,
                    server_config.rest_timeout_seconds if server_config.rest_enabled else 0
                ) + 5  # Add buffer
                
                try:
                    results = await asyncio.wait_for(
                        asyncio.gather(*tasks, return_exceptions=True),
                        timeout=timeout
                    )
                except asyncio.TimeoutError:
                    logger.error(f"Dual health check timeout for {server_name} after {timeout}s")
                    # Cancel running tasks
                    for task in tasks:
                        if not task.done():
                            task.cancel()
                    
                    # Create timeout result
                    return DualHealthCheckResult(
                        server_name=server_name,
                        timestamp=datetime.now(),
                        overall_status=ServerStatus.UNHEALTHY,
                        overall_success=False,
                        mcp_error_message="Health check timeout" if server_config.mcp_enabled else None,
                        rest_error_message="Health check timeout" if server_config.rest_enabled else None,
                        combined_response_time_ms=timeout * 1000,
                        available_paths=["none"]
                    )
                
                # Process results
                mcp_result = None
                rest_result = None
                
                result_index = 0
                if server_config.mcp_enabled:
                    mcp_result_or_exception = results[result_index]
                    if isinstance(mcp_result_or_exception, Exception):
                        logger.error(f"MCP health check failed for {server_name}: {mcp_result_or_exception}")
                        mcp_result = MCPHealthCheckResult(
                            server_name=server_name,
                            timestamp=datetime.now(),
                            success=False,
                            response_time_ms=0.0,
                            connection_error=f"Task execution error: {str(mcp_result_or_exception)}"
                        )
                    else:
                        mcp_result = mcp_result_or_exception
                    result_index += 1
                
                if server_config.rest_enabled:
                    rest_result_or_exception = results[result_index]
                    if isinstance(rest_result_or_exception, Exception):
                        logger.error(f"REST health check failed for {server_name}: {rest_result_or_exception}")
                        rest_result = RESTHealthCheckResult(
                            server_name=server_name,
                            timestamp=datetime.now(),
                            success=False,
                            response_time_ms=0.0,
                            health_endpoint_url=server_config.rest_health_endpoint_url,
                            connection_error=f"Task execution error: {str(rest_result_or_exception)}"
                        )
                    else:
                        rest_result = rest_result_or_exception
                
                # Aggregate results
                dual_result = self.aggregator.aggregate_dual_results(
                    mcp_result=mcp_result,
                    rest_result=rest_result
                )
                
                end_time = time.time()
                total_time = (end_time - start_time) * 1000
                
                logger.info(f"Completed dual health check for {server_name}: "
                           f"status={dual_result.overall_status.value}, "
                           f"score={dual_result.health_score:.3f}, "
                           f"total_time={total_time:.2f}ms")
                
                return dual_result
                
        except asyncio.CancelledError:
            logger.info(f"Dual health check cancelled for {server_name}")
            return DualHealthCheckResult(
                server_name=server_name,
                timestamp=datetime.now(),
                overall_status=ServerStatus.UNKNOWN,
                overall_success=False,
                mcp_error_message="Health check cancelled" if server_config.mcp_enabled else None,
                rest_error_message="Health check cancelled" if server_config.rest_enabled else None,
                available_paths=["none"]
            )
        except Exception as e:
            logger.error(f"Unexpected error in dual health check for {server_name}: {e}")
            return DualHealthCheckResult(
                server_name=server_name,
                timestamp=datetime.now(),
                overall_status=ServerStatus.UNKNOWN,
                overall_success=False,
                mcp_error_message=f"Service error: {str(e)}" if server_config.mcp_enabled else None,
                rest_error_message=f"Service error: {str(e)}" if server_config.rest_enabled else None,
                available_paths=["none"]
            )
        
        finally:
            # Clean up active tasks
            if mcp_task:
                self._active_tasks.pop(f"mcp-{server_name}", None)
            if rest_task:
                self._active_tasks.pop(f"rest-{server_name}", None)
    
    async def check_multiple_servers_dual(
        self,
        server_configs: List[EnhancedServerConfig],
        timeout_per_server: Optional[int] = None
    ) -> List[DualHealthCheckResult]:
        """
        Perform dual health checks for multiple servers with batch processing.
        
        Args:
            server_configs: List of server configurations
            timeout_per_server: Optional timeout per server in seconds
            
        Returns:
            List[DualHealthCheckResult]: List of dual health check results
        """
        if not server_configs:
            return []
        
        logger.info(f"Starting batch dual health checks for {len(server_configs)} servers")
        start_time = time.time()
        
        async def check_single_server(config: EnhancedServerConfig) -> DualHealthCheckResult:
            """Check single server with semaphore control."""
            async with self.server_semaphore:
                return await self.perform_dual_health_check(
                    server_config=config,
                    timeout_override=timeout_per_server
                )
        
        # Create tasks for all servers
        tasks = []
        for config in server_configs:
            task = asyncio.create_task(
                check_single_server(config),
                name=f"dual-{config.server_name}"
            )
            tasks.append(task)
            self._active_tasks[f"dual-{config.server_name}"] = task
        
        try:
            # Wait for all tasks to complete
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results and handle exceptions
            final_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Server check failed for {server_configs[i].server_name}: {result}")
                    error_result = DualHealthCheckResult(
                        server_name=server_configs[i].server_name,
                        timestamp=datetime.now(),
                        overall_status=ServerStatus.UNKNOWN,
                        overall_success=False,
                        mcp_error_message=f"Batch execution error: {str(result)}",
                        rest_error_message=f"Batch execution error: {str(result)}",
                        available_paths=["none"]
                    )
                    final_results.append(error_result)
                else:
                    final_results.append(result)
            
            end_time = time.time()
            total_time = (end_time - start_time) * 1000
            
            # Create summary
            summary = self.aggregator.create_aggregation_summary(final_results)
            
            logger.info(f"Completed batch dual health checks: "
                       f"total={summary['total_servers']}, "
                       f"healthy={summary['healthy_servers']}, "
                       f"degraded={summary['degraded_servers']}, "
                       f"unhealthy={summary['unhealthy_servers']}, "
                       f"total_time={total_time:.2f}ms")
            
            return final_results
            
        finally:
            # Clean up active tasks
            for config in server_configs:
                self._active_tasks.pop(f"dual-{config.server_name}", None)
    
    async def cancel_all_checks(self):
        """Cancel all active health checks."""
        if not self._active_tasks:
            return
        
        logger.info(f"Cancelling {len(self._active_tasks)} active health checks")
        
        # Set cancellation event
        self._cancellation_event.set()
        
        # Cancel all active tasks
        for task_name, task in self._active_tasks.items():
            if not task.done():
                logger.debug(f"Cancelling task: {task_name}")
                task.cancel()
        
        # Wait for tasks to complete cancellation
        if self._active_tasks:
            # Filter out non-task objects (like mocks in tests)
            valid_tasks = [task for task in self._active_tasks.values() if asyncio.iscoroutine(task) or hasattr(task, 'cancel')]
            if valid_tasks:
                await asyncio.gather(*valid_tasks, return_exceptions=True)
        
        # Clear active tasks
        self._active_tasks.clear()
        
        # Reset cancellation event
        self._cancellation_event.clear()
        
        logger.info("All health checks cancelled")
    
    async def cancel_server_checks(self, server_name: str):
        """Cancel health checks for a specific server."""
        cancelled_tasks = []
        
        # Find and cancel tasks for the server
        for task_name, task in list(self._active_tasks.items()):
            if server_name in task_name:
                if not task.done():
                    logger.debug(f"Cancelling server task: {task_name}")
                    task.cancel()
                    cancelled_tasks.append(task)
                self._active_tasks.pop(task_name, None)
        
        # Wait for cancellation to complete
        if cancelled_tasks:
            # Filter out non-task objects (like mocks in tests)
            valid_tasks = [task for task in cancelled_tasks if asyncio.iscoroutine(task) or hasattr(task, 'cancel')]
            if valid_tasks:
                await asyncio.gather(*valid_tasks, return_exceptions=True)
            logger.info(f"Cancelled {len(cancelled_tasks)} tasks for server {server_name}")
    
    def get_active_checks(self) -> Dict[str, str]:
        """
        Get information about currently active health checks.
        
        Returns:
            Dict[str, str]: Mapping of task names to their status
        """
        active_checks = {}
        for task_name, task in self._active_tasks.items():
            if task.done():
                if task.cancelled():
                    status = "cancelled"
                elif task.exception():
                    status = f"failed: {task.exception()}"
                else:
                    status = "completed"
            else:
                status = "running"
            active_checks[task_name] = status
        
        return active_checks
    
    async def perform_health_check_with_circuit_breaker(
        self,
        server_config: EnhancedServerConfig,
        circuit_breaker_state: Optional[str] = None
    ) -> DualHealthCheckResult:
        """
        Perform health check with circuit breaker awareness.
        
        Args:
            server_config: Enhanced server configuration
            circuit_breaker_state: Current circuit breaker state
            
        Returns:
            DualHealthCheckResult: Health check result with circuit breaker context
        """
        # Modify configuration based on circuit breaker state
        modified_config = EnhancedServerConfig.from_dict(server_config.to_dict())
        
        if circuit_breaker_state == "MCP_ONLY":
            modified_config.rest_enabled = False
            logger.info(f"Circuit breaker MCP_ONLY mode for {server_config.server_name}")
        elif circuit_breaker_state == "REST_ONLY":
            modified_config.mcp_enabled = False
            logger.info(f"Circuit breaker REST_ONLY mode for {server_config.server_name}")
        elif circuit_breaker_state == "OPEN":
            logger.warning(f"Circuit breaker OPEN for {server_config.server_name}, skipping checks")
            return DualHealthCheckResult(
                server_name=server_config.server_name,
                timestamp=datetime.now(),
                overall_status=ServerStatus.UNHEALTHY,
                overall_success=False,
                mcp_error_message="Circuit breaker open",
                rest_error_message="Circuit breaker open",
                available_paths=["none"]
            )
        
        return await self.perform_dual_health_check(modified_config)
    
    async def get_connection_pool_stats(self) -> Dict[str, Any]:
        """
        Get connection pool statistics.
        
        Returns:
            Dict[str, Any]: Connection pool statistics
        """
        stats = {
            "mcp_pool": {
                "configured_size": self.pool_manager.mcp_pool_size,
                "active": False,
                "closed": True
            },
            "rest_pool": {
                "configured_size": self.pool_manager.rest_pool_size,
                "active": False,
                "closed": True
            },
            "active_tasks": len(self._active_tasks),
            "server_semaphore_available": self.server_semaphore._value,
            "per_server_semaphore_available": self.per_server_semaphore._value
        }
        
        # Check MCP session status
        if self.pool_manager._mcp_session:
            stats["mcp_pool"]["active"] = True
            stats["mcp_pool"]["closed"] = self.pool_manager._mcp_session.closed
            if hasattr(self.pool_manager._mcp_session, '_connector'):
                connector = self.pool_manager._mcp_session._connector
                if hasattr(connector, '_conns'):
                    stats["mcp_pool"]["connections"] = len(connector._conns)
        
        # Check REST session status
        if self.pool_manager._rest_session:
            stats["rest_pool"]["active"] = True
            stats["rest_pool"]["closed"] = self.pool_manager._rest_session.closed
            if hasattr(self.pool_manager._rest_session, '_connector'):
                connector = self.pool_manager._rest_session._connector
                if hasattr(connector, '_conns'):
                    stats["rest_pool"]["connections"] = len(connector._conns)
        
        return stats
    
    def update_concurrency_limits(
        self,
        max_concurrent_servers: Optional[int] = None,
        max_concurrent_per_server: Optional[int] = None
    ):
        """
        Update concurrency limits for health checks.
        
        Args:
            max_concurrent_servers: New maximum concurrent servers
            max_concurrent_per_server: New maximum concurrent checks per server
        """
        if max_concurrent_servers is not None:
            self.max_concurrent_servers = max_concurrent_servers
            # Note: Cannot update existing semaphore, would need service restart
            logger.info(f"Updated max_concurrent_servers to {max_concurrent_servers}")
        
        if max_concurrent_per_server is not None:
            self.max_concurrent_per_server = max_concurrent_per_server
            # Note: Cannot update existing semaphore, would need service restart
            logger.info(f"Updated max_concurrent_per_server to {max_concurrent_per_server}")
    
    async def health_check_with_retry_backoff(
        self,
        server_config: EnhancedServerConfig,
        max_retries: int = 3,
        backoff_factor: float = 1.5
    ) -> DualHealthCheckResult:
        """
        Perform health check with exponential backoff retry logic.
        
        Args:
            server_config: Enhanced server configuration
            max_retries: Maximum number of retry attempts
            backoff_factor: Exponential backoff multiplier
            
        Returns:
            DualHealthCheckResult: Health check result
        """
        last_result = None
        
        for attempt in range(max_retries + 1):
            try:
                result = await self.perform_dual_health_check(server_config)
                
                # Return immediately if successful
                if result.overall_success:
                    if attempt > 0:
                        logger.info(f"Health check succeeded for {server_config.server_name} on attempt {attempt + 1}")
                    return result
                
                # Store result for potential return
                last_result = result
                
                # Don't retry on the last attempt
                if attempt == max_retries:
                    break
                
                # Calculate backoff delay
                delay = backoff_factor ** attempt
                logger.warning(f"Health check failed for {server_config.server_name} on attempt {attempt + 1}, "
                             f"retrying in {delay:.1f}s")
                await asyncio.sleep(delay)
                
            except Exception as e:
                logger.error(f"Health check attempt {attempt + 1} failed for {server_config.server_name}: {e}")
                if attempt == max_retries:
                    # Create error result
                    last_result = DualHealthCheckResult(
                        server_name=server_config.server_name,
                        timestamp=datetime.now(),
                        overall_status=ServerStatus.UNKNOWN,
                        overall_success=False,
                        mcp_error_message=f"Retry failed: {str(e)}",
                        rest_error_message=f"Retry failed: {str(e)}",
                        available_paths=["none"]
                    )
                    break
                
                # Calculate backoff delay
                delay = backoff_factor ** attempt
                await asyncio.sleep(delay)
        
        return last_result or DualHealthCheckResult(
            server_name=server_config.server_name,
            timestamp=datetime.now(),
            overall_status=ServerStatus.UNKNOWN,
            overall_success=False,
            mcp_error_message="All retry attempts failed",
            rest_error_message="All retry attempts failed",
            available_paths=["none"]
        )


@asynccontextmanager
async def create_enhanced_health_check_service(
    aggregation_config: Optional[AggregationConfig] = None,
    max_concurrent_servers: int = 10,
    max_concurrent_per_server: int = 2,
    mcp_pool_size: int = 10,
    rest_pool_size: int = 15
):
    """
    Create Enhanced Health Check Service with proper resource management.
    
    Args:
        aggregation_config: Configuration for result aggregation
        max_concurrent_servers: Maximum concurrent server checks
        max_concurrent_per_server: Maximum concurrent checks per server
        mcp_pool_size: MCP connection pool size
        rest_pool_size: REST connection pool size
        
    Yields:
        EnhancedHealthCheckService: Configured service instance
    """
    pool_manager = ConnectionPoolManager(
        mcp_pool_size=mcp_pool_size,
        rest_pool_size=rest_pool_size
    )
    
    service = EnhancedHealthCheckService(
        aggregation_config=aggregation_config,
        max_concurrent_servers=max_concurrent_servers,
        max_concurrent_per_server=max_concurrent_per_server,
        connection_pool_manager=pool_manager
    )
    
    try:
        yield service
    finally:
        await service.cancel_all_checks()
        await pool_manager.close_sessions()