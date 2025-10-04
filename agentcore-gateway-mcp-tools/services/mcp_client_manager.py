"""
MCP Client Manager for AgentCore Gateway.

This module provides connection management, pooling, and health monitoring
for MCP server communication with automatic retry logic and exponential backoff.
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import json

import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log
)

from config.settings import get_settings


logger = logging.getLogger(__name__)


class MCPServerStatus(Enum):
    """MCP server health status."""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


# Import MCPServerConfig from config_manager to avoid duplication
from services.config_manager import MCPServerConfig as ConfigMCPServerConfig


@dataclass
class MCPServerHealth:
    """Health status information for an MCP server."""
    status: MCPServerStatus
    last_check: float
    response_time: Optional[float] = None
    error_message: Optional[str] = None
    consecutive_failures: int = 0


class MCPConnectionPool:
    """Connection pool for MCP server HTTP clients."""
    
    def __init__(self, max_connections: int = 10, max_keepalive: int = 5):
        self.max_connections = max_connections
        self.max_keepalive = max_keepalive
        self._clients: Dict[str, httpx.AsyncClient] = {}
        self._lock = asyncio.Lock()
    
    async def get_client(self, server_url: str) -> httpx.AsyncClient:
        """Get or create an HTTP client for the server."""
        async with self._lock:
            if server_url not in self._clients:
                self._clients[server_url] = httpx.AsyncClient(
                    base_url=server_url,
                    timeout=httpx.Timeout(30.0),
                    limits=httpx.Limits(
                        max_connections=self.max_connections,
                        max_keepalive_connections=self.max_keepalive
                    ),
                    headers={
                        "Content-Type": "application/json",
                        "User-Agent": "AgentCore-Gateway-MCP-Client/1.0"
                    }
                )
            return self._clients[server_url]
    
    async def close_all(self):
        """Close all HTTP clients."""
        async with self._lock:
            for client in self._clients.values():
                await client.aclose()
            self._clients.clear()
    
    async def close_client(self, server_url: str):
        """Close a specific HTTP client."""
        async with self._lock:
            if server_url in self._clients:
                await self._clients[server_url].aclose()
                del self._clients[server_url]


class MCPClientManager:
    """
    MCP Client Manager with connection pooling, retry logic, and health monitoring.
    
    This class manages connections to multiple MCP servers, provides automatic
    retry with exponential backoff, and monitors server health.
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.connection_pool = MCPConnectionPool()
        self.servers: Dict[str, ConfigMCPServerConfig] = {}
        self.health_status: Dict[str, MCPServerHealth] = {}
        self._health_check_task: Optional[asyncio.Task] = None
        self._health_check_interval = 30  # seconds
        self._config_manager = None
        self._setup_servers()
    
    def _setup_servers(self):
        """Initialize MCP server configurations."""
        try:
            # Try to get configuration from config manager
            from services.config_manager import get_config_manager
            self._config_manager = get_config_manager()
            
            if self._config_manager and self._config_manager.get_current_config():
                # Use configuration from config manager
                config = self._config_manager.get_current_config()
                self.servers = config.mcp_servers.copy()
                logger.info("Loaded MCP server configurations from config manager", 
                           server_count=len(self.servers))
                
                # Register for configuration changes
                self._config_manager.add_change_callback(self._on_config_change)
            else:
                # Fallback to settings-based configuration
                self._setup_fallback_servers()
                
        except Exception as e:
            logger.warning("Failed to load from config manager, using fallback", error=str(e))
            self._setup_fallback_servers()
    
    def _setup_fallback_servers(self):
        """Setup servers using fallback configuration from settings."""
        # Restaurant Search MCP Server
        search_config = ConfigMCPServerConfig(
            name="restaurant-search",
            url=self.settings.mcp.search_server_url,
            timeout=self.settings.mcp.connection_timeout,
            max_retries=self.settings.mcp.max_retries,
            retry_delay=self.settings.mcp.retry_delay,
            tools=[
                "search_restaurants_by_district",
                "search_restaurants_by_meal_type",
                "search_restaurants_combined"
            ]
        )
        
        # Restaurant Reasoning MCP Server
        reasoning_config = ConfigMCPServerConfig(
            name="restaurant-reasoning",
            url=self.settings.mcp.reasoning_server_url,
            timeout=self.settings.mcp.connection_timeout,
            max_retries=self.settings.mcp.max_retries,
            retry_delay=self.settings.mcp.retry_delay,
            tools=[
                "recommend_restaurants",
                "analyze_restaurant_sentiment"
            ]
        )
        
        self.servers["restaurant-search"] = search_config
        self.servers["restaurant-reasoning"] = reasoning_config
        logger.info("Loaded fallback MCP server configurations", server_count=len(self.servers))
    
    async def _on_config_change(self, new_config):
        """Handle configuration changes."""
        try:
            logger.info("Configuration changed, updating MCP servers")
            
            # Close connections to removed servers
            old_server_urls = {server.url for server in self.servers.values()}
            new_server_urls = {server.url for server in new_config.mcp_servers.values()}
            
            for old_url in old_server_urls - new_server_urls:
                await self.connection_pool.close_client(old_url)
            
            # Update server configurations
            self.servers = new_config.mcp_servers.copy()
            
            # Reset health status for new/changed servers
            for server_name, server_config in self.servers.items():
                if server_name not in self.health_status:
                    self.health_status[server_name] = MCPServerHealth(
                        status=MCPServerStatus.UNKNOWN,
                        last_check=0
                    )
            
            logger.info("MCP server configurations updated", server_count=len(self.servers))
            
        except Exception as e:
            logger.error("Failed to handle configuration change", error=str(e))
        
        # Initialize health status
        for server_name in self.servers:
            self.health_status[server_name] = MCPServerHealth(
                status=MCPServerStatus.UNKNOWN,
                last_check=0.0
            )
    
    async def start(self):
        """Start the MCP client manager and health monitoring."""
        logger.info("Starting MCP Client Manager")
        
        # Start health check task
        self._health_check_task = asyncio.create_task(self._health_check_loop())
        
        # Perform initial health checks
        await self.check_all_servers_health()
        
        logger.info("MCP Client Manager started successfully")
    
    async def stop(self):
        """Stop the MCP client manager and cleanup resources."""
        logger.info("Stopping MCP Client Manager")
        
        # Cancel health check task
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass
        
        # Close all connections
        await self.connection_pool.close_all()
        
        logger.info("MCP Client Manager stopped")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((httpx.RequestError, httpx.TimeoutException)),
        before_sleep=before_sleep_log(logger, logging.WARNING)
    )
    async def call_mcp_tool(
        self,
        server_name: str,
        tool_name: str,
        parameters: Dict[str, Any],
        user_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Call an MCP tool with automatic retry logic.
        
        Args:
            server_name: Name of the MCP server
            tool_name: Name of the tool to call
            parameters: Tool parameters
            user_context: Optional user context for authentication
            
        Returns:
            Tool response data
            
        Raises:
            ValueError: If server or tool is not found
            httpx.RequestError: If request fails after retries
        """
        if server_name not in self.servers:
            raise ValueError(f"Unknown MCP server: {server_name}")
        
        server_config = self.servers[server_name]
        
        if tool_name not in server_config.tools:
            raise ValueError(f"Tool '{tool_name}' not available on server '{server_name}'")
        
        # Check server health before making request
        health = self.health_status.get(server_name)
        if health and health.status == MCPServerStatus.UNHEALTHY:
            logger.warning(f"Server {server_name} is unhealthy, attempting request anyway")
        
        client = await self.connection_pool.get_client(server_config.url)
        
        # Prepare request payload
        payload = {
            "tool": tool_name,
            "parameters": parameters
        }
        
        # Add user context if provided
        if user_context:
            payload["user_context"] = user_context
        
        # Add authentication headers if user context contains token
        headers = {}
        if user_context and "token" in user_context:
            headers["Authorization"] = f"Bearer {user_context['token']}"
        
        start_time = time.time()
        
        try:
            logger.info(f"Calling MCP tool: {server_name}.{tool_name}")
            
            response = await client.post(
                "/invoke",
                json=payload,
                headers=headers,
                timeout=server_config.timeout
            )
            
            response_time = time.time() - start_time
            
            response.raise_for_status()
            result = response.json()
            
            logger.info(
                f"MCP tool call successful: {server_name}.{tool_name} "
                f"(response_time: {response_time:.3f}s)"
            )
            
            # Update health status on successful call
            if server_name in self.health_status:
                self.health_status[server_name].consecutive_failures = 0
            
            return result
            
        except httpx.HTTPStatusError as e:
            logger.error(
                f"MCP tool call failed with HTTP {e.response.status_code}: "
                f"{server_name}.{tool_name} - {e.response.text}"
            )
            
            # Update health status on failure
            if server_name in self.health_status:
                self.health_status[server_name].consecutive_failures += 1
            
            # Re-raise as a more specific error
            raise httpx.RequestError(
                f"MCP server returned HTTP {e.response.status_code}: {e.response.text}"
            ) from e
            
        except (httpx.RequestError, httpx.TimeoutException) as e:
            logger.error(f"MCP tool call failed: {server_name}.{tool_name} - {str(e)}")
            
            # Update health status on failure
            if server_name in self.health_status:
                self.health_status[server_name].consecutive_failures += 1
            
            raise
    
    async def check_server_health(self, server_name: str) -> MCPServerHealth:
        """
        Check the health of a specific MCP server.
        
        Args:
            server_name: Name of the server to check
            
        Returns:
            Health status information
        """
        if server_name not in self.servers:
            raise ValueError(f"Unknown MCP server: {server_name}")
        
        server_config = self.servers[server_name]
        client = await self.connection_pool.get_client(server_config.url)
        
        start_time = time.time()
        
        try:
            response = await client.get(
                server_config.health_check_path,
                timeout=10.0  # Shorter timeout for health checks
            )
            
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                health = MCPServerHealth(
                    status=MCPServerStatus.HEALTHY,
                    last_check=time.time(),
                    response_time=response_time,
                    consecutive_failures=0
                )
                logger.debug(f"Server {server_name} is healthy (response_time: {response_time:.3f}s)")
            else:
                health = MCPServerHealth(
                    status=MCPServerStatus.UNHEALTHY,
                    last_check=time.time(),
                    error_message=f"HTTP {response.status_code}",
                    consecutive_failures=self.health_status.get(server_name, MCPServerHealth(
                        status=MCPServerStatus.UNKNOWN, last_check=0.0
                    )).consecutive_failures + 1
                )
                logger.warning(f"Server {server_name} health check failed: HTTP {response.status_code}")
            
        except Exception as e:
            health = MCPServerHealth(
                status=MCPServerStatus.UNHEALTHY,
                last_check=time.time(),
                error_message=str(e),
                consecutive_failures=self.health_status.get(server_name, MCPServerHealth(
                    status=MCPServerStatus.UNKNOWN, last_check=0.0
                )).consecutive_failures + 1
            )
            logger.warning(f"Server {server_name} health check failed: {str(e)}")
        
        self.health_status[server_name] = health
        return health
    
    async def check_all_servers_health(self) -> Dict[str, MCPServerHealth]:
        """
        Check the health of all configured MCP servers.
        
        Returns:
            Dictionary of server health statuses
        """
        tasks = [
            self.check_server_health(server_name)
            for server_name in self.servers
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        health_results = {}
        for server_name, result in zip(self.servers.keys(), results):
            if isinstance(result, Exception):
                logger.error(f"Health check failed for {server_name}: {result}")
                health_results[server_name] = MCPServerHealth(
                    status=MCPServerStatus.UNHEALTHY,
                    last_check=time.time(),
                    error_message=str(result)
                )
            else:
                health_results[server_name] = result
        
        return health_results
    
    async def _health_check_loop(self):
        """Background task for periodic health checks."""
        while True:
            try:
                await asyncio.sleep(self._health_check_interval)
                await self.check_all_servers_health()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health check loop error: {e}")
    
    def get_server_status(self, server_name: str) -> Optional[MCPServerHealth]:
        """Get the current health status of a server."""
        return self.health_status.get(server_name)
    
    def get_all_server_status(self) -> Dict[str, MCPServerHealth]:
        """Get the current health status of all servers."""
        return self.health_status.copy()
    
    def get_available_tools(self, server_name: Optional[str] = None) -> Dict[str, List[str]]:
        """
        Get available tools for servers.
        
        Args:
            server_name: Optional specific server name
            
        Returns:
            Dictionary mapping server names to their available tools
        """
        if server_name:
            if server_name in self.servers:
                return {server_name: self.servers[server_name].tools}
            else:
                return {}
        
        return {
            name: config.tools
            for name, config in self.servers.items()
        }
    
    def is_server_healthy(self, server_name: str) -> bool:
        """Check if a server is currently healthy."""
        health = self.health_status.get(server_name)
        return health is not None and health.status == MCPServerStatus.HEALTHY
    
    def get_healthy_servers(self) -> List[str]:
        """Get list of currently healthy server names."""
        return [
            name for name, health in self.health_status.items()
            if health.status == MCPServerStatus.HEALTHY
        ]


# Global MCP client manager instance
_mcp_client_manager: Optional[MCPClientManager] = None


async def get_mcp_client_manager() -> MCPClientManager:
    """Get the global MCP client manager instance."""
    global _mcp_client_manager
    
    if _mcp_client_manager is None:
        _mcp_client_manager = MCPClientManager()
        await _mcp_client_manager.start()
    
    return _mcp_client_manager


async def shutdown_mcp_client_manager():
    """Shutdown the global MCP client manager instance."""
    global _mcp_client_manager
    
    if _mcp_client_manager is not None:
        await _mcp_client_manager.stop()
        _mcp_client_manager = None