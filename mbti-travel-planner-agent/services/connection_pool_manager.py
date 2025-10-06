"""
Connection Pool Manager

This module provides connection pooling and management for AgentCore Runtime clients
to optimize performance and resource usage. It implements connection reuse,
health monitoring, and automatic cleanup.

Features:
- Connection pooling with configurable limits
- Connection health monitoring and validation
- Automatic connection cleanup and recycling
- Load balancing across multiple connections
- Connection statistics and monitoring
- Thread-safe operations
"""

import asyncio
import logging
import time
import threading
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Callable, AsyncContextManager
from enum import Enum
from contextlib import asynccontextmanager

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class ConnectionState(Enum):
    """Connection states."""
    IDLE = "idle"
    ACTIVE = "active"
    UNHEALTHY = "unhealthy"
    CLOSED = "closed"


@dataclass
class ConnectionConfig:
    """Configuration for connection pool."""
    max_connections_per_pool: int = 10
    min_connections_per_pool: int = 2
    max_idle_time_seconds: int = 300  # 5 minutes
    connection_timeout_seconds: int = 30
    health_check_interval_seconds: int = 60  # 1 minute
    max_connection_age_seconds: int = 3600  # 1 hour
    enable_connection_validation: bool = True
    enable_health_monitoring: bool = True
    
    # Boto3 client configuration
    boto3_config: Dict[str, Any] = field(default_factory=lambda: {
        'max_pool_connections': 50,
        'retries': {'max_attempts': 1, 'mode': 'standard'},
        'read_timeout': 30,
        'connect_timeout': 10
    })


@dataclass
class ConnectionMetrics:
    """Connection metrics and statistics."""
    created_at: datetime
    last_used: datetime
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    last_health_check: Optional[datetime] = None
    health_check_failures: int = 0
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.total_requests == 0:
            return 1.0
        return self.successful_requests / self.total_requests
    
    @property
    def age_seconds(self) -> float:
        """Get connection age in seconds."""
        return (datetime.utcnow() - self.created_at).total_seconds()
    
    @property
    def idle_time_seconds(self) -> float:
        """Get idle time in seconds."""
        return (datetime.utcnow() - self.last_used).total_seconds()


class PooledConnection:
    """A pooled connection wrapper."""
    
    def __init__(
        self, 
        connection_id: str,
        client: Any,
        config: ConnectionConfig,
        region: str
    ):
        """
        Initialize pooled connection.
        
        Args:
            connection_id: Unique connection identifier
            client: Boto3 client instance
            config: Connection configuration
            region: AWS region
        """
        self.connection_id = connection_id
        self.client = client
        self.config = config
        self.region = region
        
        # Connection state
        self.state = ConnectionState.IDLE
        self.metrics = ConnectionMetrics(
            created_at=datetime.utcnow(),
            last_used=datetime.utcnow()
        )
        
        # Thread safety
        self._lock = threading.RLock()
        
        logger.debug(f"Created pooled connection: {connection_id}")
    
    def acquire(self) -> bool:
        """
        Acquire connection for use.
        
        Returns:
            True if successfully acquired, False otherwise
        """
        with self._lock:
            if self.state != ConnectionState.IDLE:
                return False
            
            self.state = ConnectionState.ACTIVE
            self.metrics.last_used = datetime.utcnow()
            return True
    
    def release(self, success: bool = True):
        """
        Release connection back to pool.
        
        Args:
            success: Whether the operation was successful
        """
        with self._lock:
            if self.state == ConnectionState.ACTIVE:
                self.state = ConnectionState.IDLE
                self.metrics.total_requests += 1
                
                if success:
                    self.metrics.successful_requests += 1
                else:
                    self.metrics.failed_requests += 1
                
                self.metrics.last_used = datetime.utcnow()
    
    def mark_unhealthy(self):
        """Mark connection as unhealthy."""
        with self._lock:
            self.state = ConnectionState.UNHEALTHY
            self.metrics.health_check_failures += 1
    
    def close(self):
        """Close connection."""
        with self._lock:
            self.state = ConnectionState.CLOSED
            # Boto3 clients don't need explicit closing
            logger.debug(f"Closed connection: {self.connection_id}")
    
    def is_healthy(self) -> bool:
        """Check if connection is healthy."""
        with self._lock:
            # Check state
            if self.state == ConnectionState.UNHEALTHY:
                return False
            
            # Check age
            if self.metrics.age_seconds > self.config.max_connection_age_seconds:
                return False
            
            # Check success rate
            if self.metrics.success_rate < 0.8 and self.metrics.total_requests > 10:
                return False
            
            return True
    
    def should_recycle(self) -> bool:
        """Check if connection should be recycled."""
        with self._lock:
            # Check if unhealthy
            if not self.is_healthy():
                return True
            
            # Check idle time
            if self.metrics.idle_time_seconds > self.config.max_idle_time_seconds:
                return True
            
            # Check age
            if self.metrics.age_seconds > self.config.max_connection_age_seconds:
                return True
            
            return False
    
    async def health_check(self) -> bool:
        """
        Perform health check on connection.
        
        Returns:
            True if healthy, False otherwise
        """
        if not self.config.enable_connection_validation:
            return True
        
        try:
            # Simple health check - list foundation models
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client.list_foundation_models()
            )
            
            with self._lock:
                self.metrics.last_health_check = datetime.utcnow()
                return True
                
        except Exception as e:
            logger.warning(f"Health check failed for connection {self.connection_id}: {e}")
            self.mark_unhealthy()
            return False
    
    def get_info(self) -> Dict[str, Any]:
        """Get connection information."""
        with self._lock:
            return {
                "connection_id": self.connection_id,
                "state": self.state.value,
                "region": self.region,
                "created_at": self.metrics.created_at.isoformat(),
                "last_used": self.metrics.last_used.isoformat(),
                "age_seconds": self.metrics.age_seconds,
                "idle_time_seconds": self.metrics.idle_time_seconds,
                "total_requests": self.metrics.total_requests,
                "successful_requests": self.metrics.successful_requests,
                "failed_requests": self.metrics.failed_requests,
                "success_rate": self.metrics.success_rate,
                "health_check_failures": self.metrics.health_check_failures,
                "is_healthy": self.is_healthy(),
                "should_recycle": self.should_recycle()
            }


class ConnectionPool:
    """Connection pool for a specific region and service."""
    
    def __init__(
        self, 
        region: str, 
        service_name: str,
        config: ConnectionConfig
    ):
        """
        Initialize connection pool.
        
        Args:
            region: AWS region
            service_name: AWS service name
            config: Connection configuration
        """
        self.region = region
        self.service_name = service_name
        self.config = config
        
        # Connection storage
        self._connections: Dict[str, PooledConnection] = {}
        self._idle_connections: deque = deque()
        self._connection_counter = 0
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Health monitoring
        self._health_check_task: Optional[asyncio.Task] = None
        self._health_monitoring_active = False
        
        logger.info(f"Created connection pool for {service_name} in {region}")
        
        # Start health monitoring if enabled
        if config.enable_health_monitoring:
            self._start_health_monitoring()
    
    def _start_health_monitoring(self):
        """Start background health monitoring."""
        try:
            loop = asyncio.get_running_loop()
            if not self._health_monitoring_active:
                self._health_monitoring_active = True
                self._health_check_task = loop.create_task(self._health_monitor())
                logger.debug(f"Started health monitoring for pool: {self.region}/{self.service_name}")
        except RuntimeError:
            logger.debug("No event loop running, health monitoring disabled")
    
    async def _health_monitor(self):
        """Background health monitoring task."""
        while self._health_monitoring_active:
            try:
                await asyncio.sleep(self.config.health_check_interval_seconds)
                await self._perform_health_checks()
                self._cleanup_unhealthy_connections()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in health monitoring: {e}")
        
        logger.debug(f"Health monitoring stopped for pool: {self.region}/{self.service_name}")
    
    async def _perform_health_checks(self):
        """Perform health checks on idle connections."""
        with self._lock:
            idle_connections = list(self._idle_connections)
        
        for connection in idle_connections:
            if isinstance(connection, PooledConnection):
                try:
                    is_healthy = await connection.health_check()
                    if not is_healthy:
                        self._remove_connection(connection.connection_id)
                except Exception as e:
                    logger.warning(f"Health check error for {connection.connection_id}: {e}")
                    self._remove_connection(connection.connection_id)
    
    def _cleanup_unhealthy_connections(self):
        """Clean up unhealthy and old connections."""
        with self._lock:
            connections_to_remove = []
            
            for conn_id, connection in self._connections.items():
                if connection.should_recycle():
                    connections_to_remove.append(conn_id)
            
            for conn_id in connections_to_remove:
                self._remove_connection(conn_id)
            
            if connections_to_remove:
                logger.debug(f"Cleaned up {len(connections_to_remove)} connections")
    
    def _create_connection(self) -> PooledConnection:
        """Create a new connection."""
        self._connection_counter += 1
        connection_id = f"{self.region}-{self.service_name}-{self._connection_counter}"
        
        # Create boto3 config
        boto3_config = Config(
            region_name=self.region,
            **self.config.boto3_config
        )
        
        # Create client
        client = boto3.client(self.service_name, config=boto3_config)
        
        # Create pooled connection
        connection = PooledConnection(
            connection_id=connection_id,
            client=client,
            config=self.config,
            region=self.region
        )
        
        return connection
    
    def _remove_connection(self, connection_id: str):
        """Remove connection from pool."""
        with self._lock:
            if connection_id in self._connections:
                connection = self._connections[connection_id]
                connection.close()
                del self._connections[connection_id]
                
                # Remove from idle queue if present
                try:
                    self._idle_connections.remove(connection)
                except ValueError:
                    pass  # Not in idle queue
                
                logger.debug(f"Removed connection: {connection_id}")
    
    @asynccontextmanager
    async def get_connection(self) -> AsyncContextManager[PooledConnection]:
        """
        Get connection from pool with automatic release.
        
        Yields:
            PooledConnection instance
        """
        connection = None
        success = True
        
        try:
            # Try to get idle connection first
            with self._lock:
                while self._idle_connections:
                    candidate = self._idle_connections.popleft()
                    if isinstance(candidate, PooledConnection) and candidate.acquire():
                        connection = candidate
                        break
                
                # Create new connection if needed and under limit
                if connection is None and len(self._connections) < self.config.max_connections_per_pool:
                    connection = self._create_connection()
                    if connection.acquire():
                        self._connections[connection.connection_id] = connection
                    else:
                        connection = None
            
            if connection is None:
                raise RuntimeError(f"No available connections in pool (max: {self.config.max_connections_per_pool})")
            
            yield connection
            
        except Exception as e:
            success = False
            logger.error(f"Error using pooled connection: {e}")
            raise
        
        finally:
            if connection:
                connection.release(success)
                
                # Return to idle queue if still healthy
                if connection.is_healthy() and connection.state == ConnectionState.IDLE:
                    with self._lock:
                        self._idle_connections.append(connection)
                else:
                    # Remove unhealthy connection
                    self._remove_connection(connection.connection_id)
    
    def ensure_minimum_connections(self):
        """Ensure minimum number of connections are available."""
        with self._lock:
            current_count = len(self._connections)
            needed = self.config.min_connections_per_pool - current_count
            
            for _ in range(needed):
                if len(self._connections) < self.config.max_connections_per_pool:
                    connection = self._create_connection()
                    self._connections[connection.connection_id] = connection
                    self._idle_connections.append(connection)
    
    def get_pool_stats(self) -> Dict[str, Any]:
        """Get pool statistics."""
        with self._lock:
            total_connections = len(self._connections)
            idle_connections = len(self._idle_connections)
            active_connections = total_connections - idle_connections
            
            # Calculate aggregate metrics
            total_requests = sum(conn.metrics.total_requests for conn in self._connections.values())
            successful_requests = sum(conn.metrics.successful_requests for conn in self._connections.values())
            failed_requests = sum(conn.metrics.failed_requests for conn in self._connections.values())
            
            success_rate = successful_requests / max(total_requests, 1)
            
            return {
                "region": self.region,
                "service_name": self.service_name,
                "total_connections": total_connections,
                "idle_connections": idle_connections,
                "active_connections": active_connections,
                "max_connections": self.config.max_connections_per_pool,
                "min_connections": self.config.min_connections_per_pool,
                "total_requests": total_requests,
                "successful_requests": successful_requests,
                "failed_requests": failed_requests,
                "success_rate": success_rate,
                "health_monitoring_active": self._health_monitoring_active
            }
    
    def get_connection_details(self) -> List[Dict[str, Any]]:
        """Get detailed information about all connections."""
        with self._lock:
            return [conn.get_info() for conn in self._connections.values()]
    
    async def close(self):
        """Close connection pool and cleanup resources."""
        self._health_monitoring_active = False
        
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass
        
        with self._lock:
            # Close all connections
            for connection in self._connections.values():
                connection.close()
            
            self._connections.clear()
            self._idle_connections.clear()
        
        logger.info(f"Closed connection pool for {self.service_name} in {self.region}")


class ConnectionPoolManager:
    """
    Manager for multiple connection pools across regions and services.
    
    This class manages connection pools for different AWS services and regions,
    providing optimized connection reuse and resource management.
    """
    
    def __init__(self, config: Optional[ConnectionConfig] = None):
        """
        Initialize connection pool manager.
        
        Args:
            config: Connection configuration
        """
        self.config = config or ConnectionConfig()
        
        # Pool storage: {(region, service): ConnectionPool}
        self._pools: Dict[tuple, ConnectionPool] = {}
        self._lock = threading.RLock()
        
        logger.info("Connection pool manager initialized")
    
    def _get_pool_key(self, region: str, service_name: str) -> tuple:
        """Get pool key for region and service."""
        return (region, service_name)
    
    def _get_or_create_pool(self, region: str, service_name: str) -> ConnectionPool:
        """Get or create connection pool for region and service."""
        pool_key = self._get_pool_key(region, service_name)
        
        with self._lock:
            if pool_key not in self._pools:
                self._pools[pool_key] = ConnectionPool(region, service_name, self.config)
                logger.debug(f"Created new connection pool: {region}/{service_name}")
            
            return self._pools[pool_key]
    
    @asynccontextmanager
    async def get_client(
        self, 
        service_name: str, 
        region: str = "us-east-1"
    ) -> AsyncContextManager[Any]:
        """
        Get pooled client for service and region.
        
        Args:
            service_name: AWS service name (e.g., 'bedrock-agent-runtime')
            region: AWS region
            
        Yields:
            Boto3 client instance
        """
        pool = self._get_or_create_pool(region, service_name)
        
        async with pool.get_connection() as connection:
            yield connection.client
    
    def ensure_minimum_connections(self, region: str, service_name: str):
        """Ensure minimum connections for specific pool."""
        pool = self._get_or_create_pool(region, service_name)
        pool.ensure_minimum_connections()
    
    def get_pool_statistics(self) -> Dict[str, Any]:
        """Get statistics for all pools."""
        with self._lock:
            pool_stats = {}
            total_stats = {
                "total_pools": len(self._pools),
                "total_connections": 0,
                "total_requests": 0,
                "successful_requests": 0,
                "failed_requests": 0
            }
            
            for (region, service), pool in self._pools.items():
                stats = pool.get_pool_stats()
                pool_key = f"{region}/{service}"
                pool_stats[pool_key] = stats
                
                # Aggregate totals
                total_stats["total_connections"] += stats["total_connections"]
                total_stats["total_requests"] += stats["total_requests"]
                total_stats["successful_requests"] += stats["successful_requests"]
                total_stats["failed_requests"] += stats["failed_requests"]
            
            # Calculate overall success rate
            if total_stats["total_requests"] > 0:
                total_stats["overall_success_rate"] = (
                    total_stats["successful_requests"] / total_stats["total_requests"]
                )
            else:
                total_stats["overall_success_rate"] = 1.0
            
            return {
                "summary": total_stats,
                "pools": pool_stats
            }
    
    def get_detailed_pool_info(self) -> Dict[str, Any]:
        """Get detailed information about all pools and connections."""
        with self._lock:
            detailed_info = {}
            
            for (region, service), pool in self._pools.items():
                pool_key = f"{region}/{service}"
                detailed_info[pool_key] = {
                    "stats": pool.get_pool_stats(),
                    "connections": pool.get_connection_details()
                }
            
            return detailed_info
    
    async def close_all_pools(self):
        """Close all connection pools."""
        with self._lock:
            pools_to_close = list(self._pools.values())
            self._pools.clear()
        
        # Close pools outside of lock to avoid deadlock
        for pool in pools_to_close:
            try:
                await pool.close()
            except Exception as e:
                logger.error(f"Error closing pool: {e}")
        
        logger.info("All connection pools closed")
    
    async def close(self):
        """Close connection pool manager."""
        await self.close_all_pools()
        logger.info("Connection pool manager closed")
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()


# Global connection pool manager
_global_pool_manager: Optional[ConnectionPoolManager] = None


def get_connection_pool_manager(config: Optional[ConnectionConfig] = None) -> ConnectionPoolManager:
    """
    Get global connection pool manager instance.
    
    Args:
        config: Optional connection configuration
        
    Returns:
        ConnectionPoolManager instance
    """
    global _global_pool_manager
    
    if _global_pool_manager is None:
        _global_pool_manager = ConnectionPoolManager(config)
    
    return _global_pool_manager


# Export main classes and functions
__all__ = [
    'ConnectionPoolManager',
    'ConnectionPool',
    'PooledConnection',
    'ConnectionConfig',
    'ConnectionMetrics',
    'ConnectionState',
    'get_connection_pool_manager'
]