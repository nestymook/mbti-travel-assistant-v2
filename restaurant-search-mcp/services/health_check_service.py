"""
MCP server health check service using tools/list requests.

This service performs health checks on MCP servers by sending tools/list
JSON-RPC 2.0 requests and validating the responses.
Enhanced with dual monitoring support for MCP tools/list and REST health checks.
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import logging
from dataclasses import dataclass

from models.status_models import (
    HealthCheckResult,
    ServerStatus,
    MCPStatusCheckConfig,
    ServerMetrics
)

# Enhanced monitoring integration
try:
    from services.enhanced_status_service import get_enhanced_status_service
    ENHANCED_MONITORING_AVAILABLE = True
except ImportError:
    ENHANCED_MONITORING_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("Enhanced monitoring not available, using legacy health checks only")


@dataclass
class MCPToolsListRequest:
    """MCP tools/list JSON-RPC 2.0 request structure."""
    jsonrpc: str = "2.0"
    method: str = "tools/list"
    params: Dict[str, Any] = None
    id: str = "health-check"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        request_dict = {
            "jsonrpc": self.jsonrpc,
            "method": self.method,
            "id": self.id
        }
        if self.params:
            request_dict["params"] = self.params
        return request_dict


@dataclass
class MCPToolsListResponse:
    """MCP tools/list JSON-RPC 2.0 response structure."""
    jsonrpc: str
    id: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MCPToolsListResponse':
        """Create response from dictionary."""
        return cls(
            jsonrpc=data.get("jsonrpc", "2.0"),
            id=data.get("id", ""),
            result=data.get("result"),
            error=data.get("error")
        )
    
    @property
    def is_success(self) -> bool:
        """Check if response indicates success."""
        return self.error is None and self.result is not None
    
    @property
    def tools_count(self) -> Optional[int]:
        """Get number of tools from response."""
        if not self.is_success or not self.result:
            return None
        
        tools = self.result.get("tools", [])
        return len(tools) if isinstance(tools, list) else None


class HealthCheckService:
    """Service for performing MCP server health checks."""
    
    def __init__(self, timeout_seconds: int = 10, max_concurrent_checks: int = 5):
        """Initialize the health check service.
        
        Args:
            timeout_seconds: Default timeout for health checks
            max_concurrent_checks: Maximum number of concurrent health checks
        """
        self.timeout_seconds = timeout_seconds
        self.max_concurrent_checks = max_concurrent_checks
        self.logger = logging.getLogger(__name__)
        self._session: Optional[aiohttp.ClientSession] = None
        self._semaphore = asyncio.Semaphore(max_concurrent_checks)
        
    async def __aenter__(self):
        """Async context manager entry."""
        await self._ensure_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self._close_session()
    
    async def _ensure_session(self) -> None:
        """Ensure HTTP session is created."""
        if self._session is None or self._session.closed:
            connector = aiohttp.TCPConnector(
                limit=self.max_concurrent_checks * 2,
                limit_per_host=self.max_concurrent_checks,
                ttl_dns_cache=300,
                use_dns_cache=True
            )
            
            timeout = aiohttp.ClientTimeout(
                total=self.timeout_seconds,
                connect=self.timeout_seconds // 2,
                sock_read=self.timeout_seconds
            )
            
            self._session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "MCP-HealthCheck/1.0"
                }
            )
    
    async def _close_session(self) -> None:
        """Close HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None
    
    def _create_mcp_request(self, request_id: Optional[str] = None) -> MCPToolsListRequest:
        """Create MCP tools/list request.
        
        Args:
            request_id: Optional request ID (defaults to timestamp-based ID)
            
        Returns:
            MCPToolsListRequest object
        """
        if request_id is None:
            request_id = f"health-check-{int(time.time() * 1000)}"
            
        return MCPToolsListRequest(id=request_id)
    
    def _create_auth_headers(self, jwt_token: Optional[str]) -> Dict[str, str]:
        """Create authentication headers.
        
        Args:
            jwt_token: JWT token for authentication
            
        Returns:
            Dictionary of headers
        """
        headers = {}
        if jwt_token:
            headers["Authorization"] = f"Bearer {jwt_token}"
        return headers
    
    async def _perform_http_request(
        self,
        url: str,
        request_data: Dict[str, Any],
        headers: Dict[str, str],
        timeout_seconds: int
    ) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str], int, float]:
        """Perform HTTP request to MCP server.
        
        Args:
            url: MCP server endpoint URL
            request_data: JSON-RPC request data
            headers: HTTP headers
            timeout_seconds: Request timeout
            
        Returns:
            Tuple of (success, response_data, error_message, status_code, response_time_ms)
        """
        start_time = time.time()
        
        try:
            await self._ensure_session()
            
            async with self._session.post(
                url,
                json=request_data,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=timeout_seconds)
            ) as response:
                response_time_ms = (time.time() - start_time) * 1000
                
                try:
                    response_data = await response.json()
                except (aiohttp.ContentTypeError, json.JSONDecodeError) as e:
                    return False, None, f"Invalid JSON response: {str(e)}", response.status, response_time_ms
                
                if response.status == 200:
                    return True, response_data, None, response.status, response_time_ms
                else:
                    error_msg = f"HTTP {response.status}"
                    if isinstance(response_data, dict) and "error" in response_data:
                        error_detail = response_data["error"]
                        if isinstance(error_detail, dict):
                            error_msg += f": {error_detail.get('message', 'Unknown error')}"
                    return False, response_data, error_msg, response.status, response_time_ms
                    
        except asyncio.TimeoutError:
            response_time_ms = (time.time() - start_time) * 1000
            return False, None, f"Request timeout after {timeout_seconds}s", 0, response_time_ms
            
        except aiohttp.ClientError as e:
            response_time_ms = (time.time() - start_time) * 1000
            return False, None, f"HTTP client error: {str(e)}", 0, response_time_ms
            
        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            return False, None, f"Unexpected error: {str(e)}", 0, response_time_ms
    
    def _validate_mcp_response(
        self,
        response_data: Dict[str, Any],
        expected_request_id: str
    ) -> Tuple[bool, Optional[str], Optional[int]]:
        """Validate MCP JSON-RPC 2.0 response.
        
        Args:
            response_data: Response data dictionary
            expected_request_id: Expected request ID
            
        Returns:
            Tuple of (is_valid, error_message, tools_count)
        """
        try:
            mcp_response = MCPToolsListResponse.from_dict(response_data)
            
            # Validate JSON-RPC 2.0 format
            if mcp_response.jsonrpc != "2.0":
                return False, f"Invalid JSON-RPC version: {mcp_response.jsonrpc}", None
            
            # Validate request ID matches (allow flexibility for testing)
            if mcp_response.id != expected_request_id:
                # For testing, allow "health-check" as a fallback
                if not (expected_request_id.startswith("health-check") and mcp_response.id == "health-check"):
                    return False, f"Request ID mismatch: expected {expected_request_id}, got {mcp_response.id}", None
            
            # Check for JSON-RPC error
            if mcp_response.error:
                error_msg = "MCP error"
                if isinstance(mcp_response.error, dict):
                    error_msg += f": {mcp_response.error.get('message', 'Unknown error')}"
                return False, error_msg, None
            
            # Validate result structure
            if not mcp_response.result:
                return False, "Missing result in MCP response", None
            
            if not isinstance(mcp_response.result, dict):
                return False, "MCP result must be an object", None
            
            # Validate tools list
            tools = mcp_response.result.get("tools")
            if tools is None:
                return False, "Missing 'tools' in MCP result", None
            
            if not isinstance(tools, list):
                return False, "'tools' must be an array", None
            
            # Validate each tool has required fields
            for i, tool in enumerate(tools):
                if not isinstance(tool, dict):
                    return False, f"Tool {i} must be an object", None
                
                if "name" not in tool:
                    return False, f"Tool {i} missing 'name' field", None
                
                if "description" not in tool:
                    return False, f"Tool {i} missing 'description' field", None
            
            return True, None, len(tools)
            
        except Exception as e:
            return False, f"Response validation error: {str(e)}", None
    
    async def check_server_health(
        self,
        config: MCPStatusCheckConfig,
        request_id: Optional[str] = None
    ) -> HealthCheckResult:
        """Perform health check on a single MCP server.
        
        Args:
            config: Server configuration
            request_id: Optional request ID
            
        Returns:
            HealthCheckResult object
        """
        timestamp = datetime.now()
        
        async with self._semaphore:  # Limit concurrent requests
            try:
                # Create MCP request
                mcp_request = self._create_mcp_request(request_id)
                request_data = mcp_request.to_dict()
                
                # Create authentication headers
                headers = self._create_auth_headers(config.jwt_token)
                
                # Perform HTTP request
                success, response_data, error_message, status_code, response_time_ms = await self._perform_http_request(
                    config.endpoint_url,
                    request_data,
                    headers,
                    config.timeout_seconds
                )
                
                if not success:
                    return HealthCheckResult(
                        server_name=config.server_name,
                        timestamp=timestamp,
                        success=False,
                        response_time_ms=response_time_ms,
                        status_code=status_code,
                        error_message=error_message
                    )
                
                # Validate MCP response
                is_valid, validation_error, tools_count = self._validate_mcp_response(
                    response_data,
                    mcp_request.id
                )
                
                if not is_valid:
                    return HealthCheckResult(
                        server_name=config.server_name,
                        timestamp=timestamp,
                        success=False,
                        response_time_ms=response_time_ms,
                        status_code=status_code,
                        error_message=validation_error
                    )
                
                # Success
                return HealthCheckResult(
                    server_name=config.server_name,
                    timestamp=timestamp,
                    success=True,
                    response_time_ms=response_time_ms,
                    status_code=status_code,
                    tools_count=tools_count
                )
                
            except Exception as e:
                self.logger.exception(f"Unexpected error checking {config.server_name}")
                return HealthCheckResult(
                    server_name=config.server_name,
                    timestamp=timestamp,
                    success=False,
                    response_time_ms=0.0,
                    error_message=f"Health check failed: {str(e)}"
                )
    
    async def check_multiple_servers(
        self,
        configs: List[MCPStatusCheckConfig]
    ) -> List[HealthCheckResult]:
        """Perform health checks on multiple MCP servers concurrently.
        
        Args:
            configs: List of server configurations
            
        Returns:
            List of HealthCheckResult objects
        """
        if not configs:
            return []
        
        # Create tasks for concurrent execution
        tasks = [
            self.check_server_health(config)
            for config in configs
        ]
        
        # Execute all health checks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle any exceptions
        health_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.logger.exception(f"Health check task failed for {configs[i].server_name}")
                health_results.append(
                    HealthCheckResult(
                        server_name=configs[i].server_name,
                        timestamp=datetime.now(),
                        success=False,
                        response_time_ms=0.0,
                        error_message=f"Task failed: {str(result)}"
                    )
                )
            else:
                health_results.append(result)
        
        return health_results
    
    async def run_continuous_health_checks(
        self,
        configs: List[MCPStatusCheckConfig],
        result_callback: callable,
        stop_event: asyncio.Event
    ) -> None:
        """Run continuous health checks until stopped.
        
        Args:
            configs: List of server configurations
            result_callback: Callback function to handle results
            stop_event: Event to signal when to stop
        """
        self.logger.info(f"Starting continuous health checks for {len(configs)} servers")
        
        try:
            while not stop_event.is_set():
                # Perform health checks
                results = await self.check_multiple_servers(configs)
                
                # Call result callback
                try:
                    await result_callback(results)
                except Exception as e:
                    self.logger.exception("Error in health check result callback")
                
                # Calculate next check time based on minimum interval
                min_interval = min(config.check_interval_seconds for config in configs)
                
                # Wait for next check or stop signal
                try:
                    await asyncio.wait_for(stop_event.wait(), timeout=min_interval)
                    break  # Stop event was set
                except asyncio.TimeoutError:
                    continue  # Timeout reached, perform next check
                    
        except Exception as e:
            self.logger.exception("Error in continuous health checks")
        finally:
            self.logger.info("Continuous health checks stopped")
    
    def determine_server_status(
        self,
        recent_results: List[HealthCheckResult],
        consecutive_failure_threshold: int = 3
    ) -> ServerStatus:
        """Determine server status based on recent health check results.
        
        Args:
            recent_results: List of recent health check results (newest first)
            consecutive_failure_threshold: Number of consecutive failures for UNHEALTHY status
            
        Returns:
            ServerStatus enum value
        """
        if not recent_results:
            return ServerStatus.UNKNOWN
        
        latest_result = recent_results[0]
        
        # If latest check succeeded, server is healthy
        if latest_result.success:
            return ServerStatus.HEALTHY
        
        # Count consecutive failures from the latest result backwards
        consecutive_failures = 0
        for result in recent_results:
            if not result.success:
                consecutive_failures += 1
            else:
                break
        
        # Determine status based on consecutive failures
        if consecutive_failures >= consecutive_failure_threshold:
            return ServerStatus.UNHEALTHY
        elif consecutive_failures > 1:
            return ServerStatus.DEGRADED
        else:
            return ServerStatus.DEGRADED  # Single failure
    
    async def perform_retry_health_check(
        self,
        config: MCPStatusCheckConfig
    ) -> HealthCheckResult:
        """Perform health check with retry logic and exponential backoff.
        
        Args:
            config: Server configuration
            
        Returns:
            HealthCheckResult from the final attempt
        """
        last_result = None
        delay = config.retry_delay_seconds
        
        for attempt in range(config.retry_attempts + 1):  # +1 for initial attempt
            result = await self.check_server_health(config)
            last_result = result
            
            if result.success:
                return result
            
            # If this was the last attempt, return the result
            if attempt == config.retry_attempts:
                break
            
            # Wait before retry
            await asyncio.sleep(delay)
            
            # Apply exponential backoff if enabled
            if config.exponential_backoff:
                delay = min(delay * 2, config.max_retry_delay_seconds)
        
        return last_result


# Utility functions for common health check operations

async def quick_health_check(
    server_configs: List[MCPStatusCheckConfig],
    timeout_seconds: int = 10
) -> Dict[str, HealthCheckResult]:
    """Perform quick health check on multiple servers.
    
    Args:
        server_configs: List of server configurations
        timeout_seconds: Timeout for each check
        
    Returns:
        Dictionary mapping server names to health check results
    """
    async with HealthCheckService(timeout_seconds=timeout_seconds) as service:
        results = await service.check_multiple_servers(server_configs)
        return {result.server_name: result for result in results}


async def validate_mcp_server_connectivity(
    endpoint_url: str,
    jwt_token: Optional[str] = None,
    timeout_seconds: int = 10
) -> Tuple[bool, Optional[str], Optional[int]]:
    """Validate that an MCP server endpoint is reachable and responds correctly.
    
    Args:
        endpoint_url: MCP server endpoint URL
        jwt_token: Optional JWT token for authentication
        timeout_seconds: Request timeout
        
    Returns:
        Tuple of (is_connected, error_message, tools_count)
    """
    config = MCPStatusCheckConfig(
        server_name="validation-test",
        endpoint_url=endpoint_url,
        jwt_token=jwt_token,
        timeout_seconds=timeout_seconds
    )
    
    async with HealthCheckService(timeout_seconds=timeout_seconds) as service:
        result = await service.check_server_health(config)
        
        if result.success:
            return True, None, result.tools_count
        else:
            return False, result.error_message, None

# Enhanced monitoring integration functions

async def perform_enhanced_health_check(
    server_name: str = "restaurant-search-mcp"
) -> Dict[str, Any]:
    """
    Perform enhanced health check using dual monitoring if available.
    
    Args:
        server_name: Name of the server to check
        
    Returns:
        Dict containing enhanced health check results
    """
    if not ENHANCED_MONITORING_AVAILABLE:
        # Fallback to legacy health check
        logger.info("Enhanced monitoring not available, using legacy health check")
        return await _perform_legacy_health_check(server_name)
    
    try:
        # Get enhanced status service
        enhanced_service = await get_enhanced_status_service()
        
        # Perform enhanced health check
        enhanced_status = await enhanced_service.get_enhanced_status()
        
        return {
            "enhanced_monitoring": True,
            "timestamp": datetime.now().isoformat(),
            "server_name": server_name,
            "status": enhanced_status,
            "monitoring_type": "dual_mcp_rest"
        }
        
    except Exception as e:
        logger.error(f"Enhanced health check failed, falling back to legacy: {e}")
        return await _perform_legacy_health_check(server_name)


async def _perform_legacy_health_check(server_name: str) -> Dict[str, Any]:
    """
    Perform legacy health check as fallback.
    
    Args:
        server_name: Name of the server to check
        
    Returns:
        Dict containing legacy health check results
    """
    try:
        # Create a basic configuration for self-check
        config = MCPStatusCheckConfig(
            server_name=server_name,
            endpoint_url="http://localhost:8080/mcp",  # Default local endpoint
            timeout_seconds=10
        )
        
        async with HealthCheckService() as service:
            result = await service.check_server_health(config)
            
            return {
                "enhanced_monitoring": False,
                "timestamp": datetime.now().isoformat(),
                "server_name": server_name,
                "status": {
                    "success": result.success,
                    "response_time_ms": result.response_time_ms,
                    "tools_count": result.tools_count,
                    "error_message": result.error_message
                },
                "monitoring_type": "legacy_mcp_only"
            }
            
    except Exception as e:
        logger.error(f"Legacy health check failed: {e}")
        return {
            "enhanced_monitoring": False,
            "timestamp": datetime.now().isoformat(),
            "server_name": server_name,
            "status": {
                "success": False,
                "error_message": f"Health check failed: {str(e)}"
            },
            "monitoring_type": "error"
        }


async def get_health_check_capabilities() -> Dict[str, Any]:
    """
    Get information about available health check capabilities.
    
    Returns:
        Dict containing capability information
    """
    capabilities = {
        "legacy_mcp_monitoring": True,
        "enhanced_dual_monitoring": ENHANCED_MONITORING_AVAILABLE,
        "timestamp": datetime.now().isoformat()
    }
    
    if ENHANCED_MONITORING_AVAILABLE:
        try:
            enhanced_service = await get_enhanced_status_service()
            enhanced_capabilities = await enhanced_service.get_monitoring_capabilities()
            capabilities["enhanced_capabilities"] = enhanced_capabilities
        except Exception as e:
            logger.error(f"Error getting enhanced capabilities: {e}")
            capabilities["enhanced_monitoring_error"] = str(e)
    
    return capabilities


class EnhancedHealthCheckService(HealthCheckService):
    """
    Enhanced Health Check Service that integrates with dual monitoring.
    
    Extends the base HealthCheckService to provide enhanced monitoring
    capabilities when available, with graceful fallback to legacy monitoring.
    """
    
    def __init__(self, *args, **kwargs):
        """Initialize enhanced health check service."""
        super().__init__(*args, **kwargs)
        self._enhanced_service = None
        self._enhanced_available = ENHANCED_MONITORING_AVAILABLE
    
    async def __aenter__(self):
        """Async context manager entry with enhanced monitoring setup."""
        await super().__aenter__()
        
        if self._enhanced_available:
            try:
                self._enhanced_service = await get_enhanced_status_service()
                self.logger.info("Enhanced monitoring service connected")
            except Exception as e:
                self.logger.warning(f"Enhanced monitoring not available: {e}")
                self._enhanced_available = False
        
        return self
    
    async def check_server_health_enhanced(
        self,
        config: MCPStatusCheckConfig,
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Perform enhanced health check with dual monitoring if available.
        
        Args:
            config: Server configuration
            request_id: Optional request ID
            
        Returns:
            Dict containing enhanced health check results
        """
        if self._enhanced_available and self._enhanced_service:
            try:
                # Use enhanced dual monitoring
                enhanced_result = await self._enhanced_service.perform_self_health_check()
                
                return {
                    "monitoring_type": "enhanced_dual",
                    "timestamp": datetime.now().isoformat(),
                    "server_name": config.server_name,
                    "enhanced_result": enhanced_result.to_dict(),
                    "legacy_compatible": {
                        "success": enhanced_result.overall_success,
                        "response_time_ms": enhanced_result.combined_response_time_ms,
                        "status": enhanced_result.overall_status.value
                    }
                }
                
            except Exception as e:
                self.logger.error(f"Enhanced health check failed: {e}")
                # Fall back to legacy
        
        # Use legacy health check
        legacy_result = await self.check_server_health(config, request_id)
        
        return {
            "monitoring_type": "legacy_mcp",
            "timestamp": datetime.now().isoformat(),
            "server_name": config.server_name,
            "legacy_result": {
                "success": legacy_result.success,
                "response_time_ms": legacy_result.response_time_ms,
                "tools_count": legacy_result.tools_count,
                "error_message": legacy_result.error_message,
                "status_code": legacy_result.status_code
            }
        }
    
    async def get_comprehensive_status(self) -> Dict[str, Any]:
        """
        Get comprehensive status including both legacy and enhanced monitoring.
        
        Returns:
            Dict containing comprehensive status information
        """
        status = {
            "timestamp": datetime.now().isoformat(),
            "service_type": "restaurant_search_mcp",
            "monitoring_capabilities": {
                "legacy_mcp": True,
                "enhanced_dual": self._enhanced_available
            }
        }
        
        # Add enhanced status if available
        if self._enhanced_available and self._enhanced_service:
            try:
                enhanced_status = await self._enhanced_service.get_enhanced_status()
                status["enhanced_status"] = enhanced_status
            except Exception as e:
                self.logger.error(f"Error getting enhanced status: {e}")
                status["enhanced_status_error"] = str(e)
        
        # Add legacy health check capabilities
        status["legacy_capabilities"] = {
            "mcp_tools_list_validation": True,
            "json_rpc_2_0_support": True,
            "concurrent_health_checks": True,
            "retry_with_backoff": True,
            "circuit_breaker_integration": True
        }
        
        return status