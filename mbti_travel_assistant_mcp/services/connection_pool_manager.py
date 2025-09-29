"""
Connection Pool Manager

This module provides connection pooling for MCP client connections to improve
performance and resource utilization for the MBTI Travel Assistant.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, AsyncContextManager
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import weakref
from contextlib import asynccontextmanager
import aiohttp
from mcp.client import ClientSession
from mcp.client.streamable_http import streamablehttp_client

logger = logging.getLogger(__name__)


class ConnectionState(Enum):
    """Connection states"""
    IDLE = "idle"
    ACTIVE = "active"
    FAILED = "failed"
    CLOSED = "closed"


@dataclass
class PooledConnection:
    """Represents a pooled MCP connection"""
    connection_id: str
    server_endpoint: str
    session: Optional[ClientSession]
    state: ConnectionState
    created_at: datetime
    last_used: datetime
    use_count: int = 0
    error_count: int = 0
    
    def mark_used(self):
        """Mark connection as used"""
        self.last_used = datetime.now()
        self.use_count += 1
        self.state = ConnectionState.ACTIVE
    
    def mark_idle(self):
        """Mark connection as idle"""
        self.state = ConnectionState.IDLE
    
    def mark_failed(self):
        """Mark connection as failed"""
        self.error_count += 1
        self.state = ConnectionState.FAILED
    
    def is_expired(self, max_age_minutes: int = 30) -> bool:
        """Check if connection is expired"""
        age = datetime.now() - self.created_at
        return age > timedelta(minutes=max_age_minutes)
    
    def is_stale(self, max_idle_minutes: int = 10) -> bool:
        """Check if connection is stale (idle too long)"""
        idle_time = datetime.now() - self.last_used
        return idle_time > timedelta(minutes=max_idle_minutes)


class ConnectionPoolManager:
    """
    Connection pool manager for MCP client connections.
    
    Manages pools of connections to different MCP servers to improve performance
    through connection reuse and parallel processing capabilities.
    """
    
    def __init__(
        self,
        max_connections_per_server: int = 10,
        max_idle_connections: int = 5,
        connection_timeout: int = 30,
        max_connection_age_minutes: int = 30,
        max_idle_time_minutes: int = 10
    ):
        """
        Initialize connection pool manager.
        
        Args:
            max_connections_per_server: Maximum connections per MCP server
            max_idle_connections: Maximum idle connections to keep
            connection_timeout: Connection timeout in seconds
            max_connection_age_minutes: Maximum age of connections
            max_idle_time_minutes: Maximum idle time before closing
        """
        self.max_connections_per_server = max_connections_per_server
        self.max_idle_connections = max_idle_connections
        self.connection_timeout = connection_timeout
        self.max_connection_age_minutes = max_connection_age_minutes
        self.max_idle_time_minutes = max_idle_time_minutes
        
        # Connection pools by server endpoint
        self._pools: Dict[str, List[PooledConnection]] = {}
        self._pool_locks: Dict[str, asyncio.Lock] = {}
        self._connection_counter = 0
        self._cleanup_task: Optional[asyncio.Task] = None
        
        # Statistics
        self._stats = {
            "total_connections_created": 0,
            "total_connections_reused": 0,
            "total_connections_closed": 0,
            "active_connections": 0,
            "idle_connections": 0,
            "failed_connections": 0
        }
        
        # Start cleanup task
        self._start_cleanup_task()
        
        logger.info(
            f"Initialized ConnectionPoolManager - max_per_server: {max_connections_per_server}, "
            f"max_idle: {max_idle_connections}, timeout: {connection_timeout}s"
        )
    
    def _start_cleanup_task(self):
        """Start background cleanup task"""
        try:
            loop = asyncio.get_event_loop()
            self._cleanup_task = loop.create_task(self._cleanup_connections())
        except RuntimeError:
            # No event loop running, task will be started when needed
            pass
    
    async def _cleanup_connections(self):
        """Background task to clean up expired and stale connections"""
        while True:
            try:
                await asyncio.sleep(60)  # Run every minute
                await self._cleanup_expired_connections()
                await self._cleanup_stale_connections()
            except Exception as e:
                logger.error(f"Error in connection cleanup: {e}")
    
    async def _cleanup_expired_connections(self):
        """Clean up expired connections"""
        cleaned_count = 0
        
        for server_endpoint in list(self._pools.keys()):
            async with self._get_pool_lock(server_endpoint):
                pool = self._pools.get(server_endpoint, [])
                active_connections = []
                
                for conn in pool:
                    if conn.is_expired(self.max_connection_age_minutes):
                        await self._close_connection(conn)
                        cleaned_count += 1
                    else:
                        active_connections.append(conn)
                
                self._pools[server_endpoint] = active_connections
        
        if cleaned_count > 0:
            logger.info(f"Cleaned up {cleaned_count} expired connections")
    
    async def _cleanup_stale_connections(self):
        """Clean up stale idle connections"""
        cleaned_count = 0
        
        for server_endpoint in list(self._pools.keys()):
            async with self._get_pool_lock(server_endpoint):
                pool = self._pools.get(server_endpoint, [])
                active_connections = []
                idle_count = 0
                
                for conn in pool:
                    if (conn.state == ConnectionState.IDLE and 
                        conn.is_stale(self.max_idle_time_minutes) and
                        idle_count >= self.max_idle_connections):
                        await self._close_connection(conn)
                        cleaned_count += 1
                    else:
                        active_connections.append(conn)
                        if conn.state == ConnectionState.IDLE:
                            idle_count += 1
                
                self._pools[server_endpoint] = active_connections
        
        if cleaned_count > 0:
            logger.info(f"Cleaned up {cleaned_count} stale connections")
    
    def _get_pool_lock(self, server_endpoint: str) -> asyncio.Lock:
        """Get or create lock for server pool"""
        if server_endpoint not in self._pool_locks:
            self._pool_locks[server_endpoint] = asyncio.Lock()
        return self._pool_locks[server_endpoint]
    
    async def _create_connection(self, server_endpoint: str, headers: Optional[Dict[str, str]] = None) -> PooledConnection:
        """Create a new MCP connection"""
        self._connection_counter += 1
        connection_id = f"conn_{self._connection_counter}_{int(datetime.now().timestamp())}"
        
        try:
            # Create MCP client connection
            read, write, close_func = await asyncio.wait_for(
                streamablehttp_client(server_endpoint, headers or {}),
                timeout=self.connection_timeout
            )
            
            session = ClientSession(read, write)
            await session.initialize()
            
            connection = PooledConnection(
                connection_id=connection_id,
                server_endpoint=server_endpoint,
                session=session,
                state=ConnectionState.IDLE,
                created_at=datetime.now(),
                last_used=datetime.now()
            )
            
            self._stats["total_connections_created"] += 1
            logger.debug(f"Created new connection {connection_id} to {server_endpoint}")
            
            return connection
            
        except Exception as e:
            logger.error(f"Failed to create connection to {server_endpoint}: {e}")
            raise
    
    async def _close_connection(self, connection: PooledConnection):
        """Close a connection"""
        try:
            if connection.session:
                # Close the session if it has a close method
                if hasattr(connection.session, 'close'):
                    await connection.session.close()
            
            connection.state = ConnectionState.CLOSED
            self._stats["total_connections_closed"] += 1
            logger.debug(f"Closed connection {connection.connection_id}")
            
        except Exception as e:
            logger.warning(f"Error closing connection {connection.connection_id}: {e}")
    
    @asynccontextmanager
    async def get_connection(
        self,
        server_endpoint: str,
        headers: Optional[Dict[str, str]] = None
    ) -> AsyncContextManager[ClientSession]:
        """
        Get a pooled connection to an MCP server.
        
        Args:
            server_endpoint: MCP server endpoint URL
            headers: Optional HTTP headers
            
        Yields:
            ClientSession for MCP operations
        """
        connection = None
        
        try:
            # Get connection from pool or create new one
            connection = await self._get_or_create_connection(server_endpoint, headers)
            connection.mark_used()
            
            yield connection.session
            
            # Mark connection as idle when done
            connection.mark_idle()
            self._stats["total_connections_reused"] += 1
            
        except Exception as e:
            if connection:
                connection.mark_failed()
            logger.error(f"Error using connection to {server_endpoint}: {e}")
            raise
    
    async def _get_or_create_connection(
        self,
        server_endpoint: str,
        headers: Optional[Dict[str, str]] = None
    ) -> PooledConnection:
        """Get existing connection from pool or create new one"""
        async with self._get_pool_lock(server_endpoint):
            pool = self._pools.get(server_endpoint, [])
            
            # Look for idle connection
            for connection in pool:
                if (connection.state == ConnectionState.IDLE and 
                    not connection.is_expired(self.max_connection_age_minutes)):
                    logger.debug(f"Reusing connection {connection.connection_id}")
                    return connection
            
            # Check if we can create new connection
            active_connections = [c for c in pool if c.state in [ConnectionState.IDLE, ConnectionState.ACTIVE]]
            
            if len(active_connections) >= self.max_connections_per_server:
                # Wait for a connection to become available
                logger.warning(f"Connection pool full for {server_endpoint}, waiting...")
                await asyncio.sleep(0.1)  # Brief wait
                
                # Try again to find idle connection
                for connection in pool:
                    if connection.state == ConnectionState.IDLE:
                        return connection
                
                # If still no idle connection, create new one anyway (overflow)
                logger.warning(f"Creating overflow connection for {server_endpoint}")
            
            # Create new connection
            connection = await self._create_connection(server_endpoint, headers)
            
            # Add to pool
            if server_endpoint not in self._pools:
                self._pools[server_endpoint] = []
            self._pools[server_endpoint].append(connection)
            
            return connection
    
    async def execute_parallel_operations(
        self,
        operations: List[Dict[str, Any]],
        max_concurrent: int = 5
    ) -> List[Any]:
        """
        Execute multiple MCP operations in parallel using connection pool.
        
        Args:
            operations: List of operation dictionaries with 'server_endpoint', 'tool_name', 'parameters'
            max_concurrent: Maximum concurrent operations
            
        Returns:
            List of operation results
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def execute_operation(operation: Dict[str, Any]) -> Any:
            async with semaphore:
                server_endpoint = operation['server_endpoint']
                tool_name = operation['tool_name']
                parameters = operation.get('parameters', {})
                headers = operation.get('headers', {})
                
                async with self.get_connection(server_endpoint, headers) as session:
                    result = await session.call_tool(tool_name, parameters)
                    return result
        
        # Execute all operations concurrently
        tasks = [execute_operation(op) for op in operations]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        logger.info(f"Executed {len(operations)} parallel operations with max_concurrent={max_concurrent}")
        return results
    
    def get_pool_stats(self) -> Dict[str, Any]:
        """Get connection pool statistics"""
        pool_stats = {}
        total_active = 0
        total_idle = 0
        total_failed = 0
        
        for server_endpoint, pool in self._pools.items():
            active = len([c for c in pool if c.state == ConnectionState.ACTIVE])
            idle = len([c for c in pool if c.state == ConnectionState.IDLE])
            failed = len([c for c in pool if c.state == ConnectionState.FAILED])
            
            pool_stats[server_endpoint] = {
                "total_connections": len(pool),
                "active_connections": active,
                "idle_connections": idle,
                "failed_connections": failed,
                "oldest_connection_age_minutes": (
                    (datetime.now() - min(c.created_at for c in pool)).total_seconds() / 60
                    if pool else 0
                )
            }
            
            total_active += active
            total_idle += idle
            total_failed += failed
        
        # Update global stats
        self._stats["active_connections"] = total_active
        self._stats["idle_connections"] = total_idle
        self._stats["failed_connections"] = total_failed
        
        return {
            "global_stats": self._stats,
            "pool_stats": pool_stats,
            "configuration": {
                "max_connections_per_server": self.max_connections_per_server,
                "max_idle_connections": self.max_idle_connections,
                "connection_timeout": self.connection_timeout,
                "max_connection_age_minutes": self.max_connection_age_minutes,
                "max_idle_time_minutes": self.max_idle_time_minutes
            }
        }
    
    async def warm_up_connections(
        self,
        server_endpoints: List[str],
        connections_per_server: int = 2,
        headers: Optional[Dict[str, str]] = None
    ):
        """
        Warm up connection pools by pre-creating connections.
        
        Args:
            server_endpoints: List of server endpoints to warm up
            connections_per_server: Number of connections to create per server
            headers: Optional HTTP headers
        """
        logger.info(f"Warming up connections to {len(server_endpoints)} servers")
        
        for server_endpoint in server_endpoints:
            try:
                for i in range(connections_per_server):
                    connection = await self._create_connection(server_endpoint, headers)
                    
                    # Add to pool
                    if server_endpoint not in self._pools:
                        self._pools[server_endpoint] = []
                    self._pools[server_endpoint].append(connection)
                    
                logger.info(f"Warmed up {connections_per_server} connections to {server_endpoint}")
                
            except Exception as e:
                logger.error(f"Failed to warm up connections to {server_endpoint}: {e}")
    
    async def close_all_connections(self):
        """Close all connections in all pools"""
        total_closed = 0
        
        for server_endpoint, pool in self._pools.items():
            for connection in pool:
                await self._close_connection(connection)
                total_closed += 1
        
        self._pools.clear()
        self._pool_locks.clear()
        
        if self._cleanup_task:
            self._cleanup_task.cancel()
        
        logger.info(f"Closed all {total_closed} connections")
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on connection pools.
        
        Returns:
            Health check results
        """
        health_results = {
            "overall_status": "healthy",
            "server_health": {},
            "issues": []
        }
        
        for server_endpoint, pool in self._pools.items():
            server_health = {
                "status": "healthy",
                "total_connections": len(pool),
                "healthy_connections": 0,
                "failed_connections": 0,
                "issues": []
            }
            
            for connection in pool:
                if connection.state == ConnectionState.FAILED:
                    server_health["failed_connections"] += 1
                    server_health["issues"].append(f"Connection {connection.connection_id} failed")
                else:
                    server_health["healthy_connections"] += 1
            
            # Determine server health status
            if server_health["failed_connections"] > len(pool) * 0.5:
                server_health["status"] = "unhealthy"
                health_results["overall_status"] = "degraded"
                health_results["issues"].append(f"Server {server_endpoint} has high failure rate")
            elif server_health["failed_connections"] > 0:
                server_health["status"] = "degraded"
                if health_results["overall_status"] == "healthy":
                    health_results["overall_status"] = "degraded"
            
            health_results["server_health"][server_endpoint] = server_health
        
        return health_results


# Global connection pool manager instance
connection_pool_manager = ConnectionPoolManager()