"""
MCP Health Check Client

This module implements the MCP Health Check Client for performing native MCP
tools/list health checks using JSON-RPC 2.0 protocol.
"""

import asyncio
import json
import time
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
import aiohttp
import logging

from models.dual_health_models import (
    MCPToolsListRequest,
    MCPToolsListResponse,
    MCPValidationResult,
    MCPHealthCheckResult,
    EnhancedServerConfig
)
from models.auth_models import (
    AuthenticationConfig,
    AuthenticationError
)
from services.authentication_service import AuthenticationService


logger = logging.getLogger(__name__)


class MCPHealthCheckClient:
    """
    MCP Health Check Client for tools/list requests.
    
    This client performs native MCP protocol health checks by sending JSON-RPC 2.0
    tools/list requests and validating the responses.
    """
    
    def __init__(self, session: Optional[aiohttp.ClientSession] = None, auth_service: Optional[AuthenticationService] = None):
        """
        Initialize MCP Health Check Client.
        
        Args:
            session: Optional aiohttp ClientSession for connection reuse
            auth_service: Optional authentication service for secure requests
        """
        self._session = session
        self._owned_session = session is None
        self._auth_service = auth_service
        self._owned_auth_service = auth_service is None
        
    async def __aenter__(self):
        """Async context manager entry."""
        if self._session is None:
            self._session = aiohttp.ClientSession()
        if self._auth_service is None:
            self._auth_service = AuthenticationService(self._session)
            await self._auth_service.__aenter__()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._owned_auth_service and self._auth_service:
            await self._auth_service.__aexit__(exc_type, exc_val, exc_tb)
        if self._owned_session and self._session:
            await self._session.close()
    
    def create_mcp_request(self, request_id: Optional[str] = None) -> MCPToolsListRequest:
        """
        Create MCP tools/list JSON-RPC 2.0 request.
        
        Args:
            request_id: Optional request ID, generates UUID if not provided
            
        Returns:
            MCPToolsListRequest: Formatted MCP request
        """
        if request_id is None:
            request_id = str(uuid.uuid4())
        
        return MCPToolsListRequest(
            jsonrpc="2.0",
            method="tools/list",
            id=request_id,
            params={}
        )
    
    async def send_tools_list_request(
        self,
        endpoint_url: str,
        auth_headers: Optional[Dict[str, str]] = None,
        timeout: int = 10,
        request_id: Optional[str] = None
    ) -> MCPToolsListResponse:
        """
        Send MCP tools/list request to server.
        
        Args:
            endpoint_url: MCP server endpoint URL
            auth_headers: Optional authentication headers
            timeout: Request timeout in seconds
            request_id: Optional request ID
            
        Returns:
            MCPToolsListResponse: MCP response
            
        Raises:
            aiohttp.ClientError: On HTTP client errors
            asyncio.TimeoutError: On request timeout
            json.JSONDecodeError: On invalid JSON response
        """
        if self._session is None:
            raise RuntimeError("Client session not initialized. Use async context manager.")
        
        # Create MCP request
        mcp_request = self.create_mcp_request(request_id)
        
        # Prepare headers
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        if auth_headers:
            headers.update(auth_headers)
        
        logger.debug(f"Sending MCP tools/list request to {endpoint_url}")
        logger.debug(f"Request: {mcp_request.to_json()}")
        
        # Send request
        async with self._session.post(
            endpoint_url,
            json=mcp_request.to_dict(),
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=timeout)
        ) as response:
            response_text = await response.text()
            
            logger.debug(f"MCP response status: {response.status}")
            logger.debug(f"MCP response: {response_text}")
            
            # Parse JSON response
            try:
                response_data = json.loads(response_text)
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON response from MCP server: {e}")
                # Create error response
                return MCPToolsListResponse(
                    jsonrpc="2.0",
                    id=mcp_request.id,
                    error={
                        "code": -32700,
                        "message": "Parse error",
                        "data": f"Invalid JSON: {str(e)}"
                    }
                )
            
            # Handle HTTP errors
            if response.status >= 400:
                logger.error(f"HTTP error {response.status} from MCP server")
                return MCPToolsListResponse(
                    jsonrpc="2.0",
                    id=mcp_request.id,
                    error={
                        "code": -32000,
                        "message": f"HTTP {response.status}",
                        "data": response_text
                    }
                )
            
            # Create response object
            return MCPToolsListResponse.from_dict(response_data)
    
    def validate_tools_list_response(
        self,
        response: MCPToolsListResponse,
        expected_tools: Optional[List[str]] = None
    ) -> MCPValidationResult:
        """
        Validate MCP tools/list response.
        
        Args:
            response: MCP tools/list response
            expected_tools: Optional list of expected tool names
            
        Returns:
            MCPValidationResult: Validation result
        """
        validation_errors = []
        expected_tools = expected_tools or []
        
        # Validate JSON-RPC format
        format_errors = response.validate()
        validation_errors.extend(format_errors)
        
        # Check if response indicates success
        if not response.is_success():
            validation_errors.append("MCP response indicates failure")
            return MCPValidationResult(
                is_valid=False,
                tools_count=0,
                expected_tools_found=[],
                missing_tools=expected_tools,
                validation_errors=validation_errors,
                tool_schemas_valid=False
            )
        
        # Extract tools from response
        tools = response.get_tools()
        tools_count = len(tools)
        
        # Validate tools structure
        tool_schemas_valid = True
        for tool in tools:
            if not isinstance(tool, dict):
                validation_errors.append(f"Invalid tool format: {tool}")
                tool_schemas_valid = False
                continue
            
            # Check required tool fields
            if 'name' not in tool:
                validation_errors.append(f"Tool missing 'name' field: {tool}")
                tool_schemas_valid = False
            
            if 'description' not in tool:
                validation_errors.append(f"Tool missing 'description' field: {tool}")
                tool_schemas_valid = False
            
            # Validate input schema if present
            if 'inputSchema' in tool:
                input_schema = tool['inputSchema']
                if not isinstance(input_schema, dict):
                    validation_errors.append(f"Invalid inputSchema for tool {tool.get('name', 'unknown')}")
                    tool_schemas_valid = False
        
        # Check expected tools
        tool_names = [tool.get('name', '') for tool in tools if isinstance(tool, dict)]
        expected_tools_found = [name for name in expected_tools if name in tool_names]
        missing_tools = [name for name in expected_tools if name not in tool_names]
        
        if missing_tools:
            validation_errors.append(f"Missing expected tools: {missing_tools}")
        
        # Determine overall validity
        is_valid = (
            len(format_errors) == 0 and
            response.is_success() and
            tool_schemas_valid and
            len(missing_tools) == 0
        )
        
        return MCPValidationResult(
            is_valid=is_valid,
            tools_count=tools_count,
            expected_tools_found=expected_tools_found,
            missing_tools=missing_tools,
            validation_errors=validation_errors,
            tool_schemas_valid=tool_schemas_valid
        )
    
    async def perform_mcp_health_check(
        self,
        server_config: EnhancedServerConfig
    ) -> MCPHealthCheckResult:
        """
        Perform complete MCP health check for a server.
        
        Args:
            server_config: Enhanced server configuration
            
        Returns:
            MCPHealthCheckResult: Complete MCP health check result
        """
        start_time = time.time()
        timestamp = datetime.now()
        
        # Initialize result with defaults
        result = MCPHealthCheckResult(
            server_name=server_config.server_name,
            timestamp=timestamp,
            success=False,
            response_time_ms=0.0,
            request_id="",
            jsonrpc_version="2.0"
        )
        
        if not server_config.mcp_enabled:
            result.connection_error = "MCP health checks disabled in configuration"
            return result
        
        if not server_config.mcp_endpoint_url:
            result.connection_error = "MCP endpoint URL not configured"
            return result
        
        try:
            # Prepare authentication headers using authentication service
            auth_headers = {}
            auth_error = None
            
            if hasattr(server_config, 'auth_config') and server_config.auth_config:
                if self._auth_service:
                    try:
                        # Refresh token if needed
                        await self._auth_service.refresh_token_if_needed(
                            server_config.server_name, 
                            server_config.auth_config
                        )
                        
                        # Get authentication headers
                        auth_result = await self._auth_service.authenticate(
                            server_config.server_name,
                            server_config.auth_config
                        )
                        
                        if auth_result.success:
                            auth_headers.update(auth_result.auth_headers)
                        else:
                            auth_error = f"Authentication failed: {auth_result.error_message}"
                            logger.error(f"MCP authentication failed for {server_config.server_name}: {auth_result.error_message}")
                    
                    except Exception as e:
                        auth_error = f"Authentication error: {str(e)}"
                        logger.error(f"MCP authentication error for {server_config.server_name}: {e}")
            
            # Fallback to legacy authentication headers
            if server_config.jwt_token:
                auth_headers['Authorization'] = f'Bearer {server_config.jwt_token}'
            if server_config.auth_headers:
                auth_headers.update(server_config.auth_headers)
            
            # If authentication failed and no fallback, return error
            if auth_error and not auth_headers:
                result.connection_error = auth_error
                result.mcp_error = {"code": -32000, "message": "Authentication failed", "data": auth_error}
                return result
            
            # Generate request ID
            request_id = f"{server_config.server_name}-{int(timestamp.timestamp())}"
            result.request_id = request_id
            
            # Send tools/list request with retry logic
            response = None
            last_error = None
            
            for attempt in range(server_config.mcp_retry_attempts):
                try:
                    response = await self.send_tools_list_request(
                        endpoint_url=server_config.mcp_endpoint_url,
                        auth_headers=auth_headers,
                        timeout=server_config.mcp_timeout_seconds,
                        request_id=request_id
                    )
                    break
                except Exception as e:
                    last_error = e
                    logger.warning(f"MCP request attempt {attempt + 1} failed: {e}")
                    if attempt < server_config.mcp_retry_attempts - 1:
                        await asyncio.sleep(1)  # Brief delay between retries
            
            if response is None:
                result.connection_error = f"All {server_config.mcp_retry_attempts} attempts failed: {last_error}"
                return result
            
            # Calculate response time
            end_time = time.time()
            result.response_time_ms = (end_time - start_time) * 1000
            
            # Store response
            result.tools_list_response = response
            
            # Check for MCP errors
            if response.error:
                result.mcp_error = response.error
                result.success = False
                return result
            
            # Validate response
            validation_result = self.validate_tools_list_response(
                response=response,
                expected_tools=server_config.mcp_expected_tools
            )
            
            result.validation_result = validation_result
            result.tools_count = validation_result.tools_count
            result.expected_tools_found = validation_result.expected_tools_found
            result.missing_tools = validation_result.missing_tools
            
            # Determine success
            result.success = validation_result.is_valid
            
            logger.info(f"MCP health check completed for {server_config.server_name}: "
                       f"success={result.success}, tools={result.tools_count}, "
                       f"response_time={result.response_time_ms:.2f}ms")
            
        except asyncio.TimeoutError:
            result.connection_error = f"Request timeout after {server_config.mcp_timeout_seconds} seconds"
            result.response_time_ms = server_config.mcp_timeout_seconds * 1000
            logger.error(f"MCP health check timeout for {server_config.server_name}")
            
        except aiohttp.ClientError as e:
            result.connection_error = f"HTTP client error: {str(e)}"
            end_time = time.time()
            result.response_time_ms = (end_time - start_time) * 1000
            logger.error(f"MCP health check client error for {server_config.server_name}: {e}")
            
        except Exception as e:
            result.connection_error = f"Unexpected error: {str(e)}"
            end_time = time.time()
            result.response_time_ms = (end_time - start_time) * 1000
            logger.error(f"MCP health check unexpected error for {server_config.server_name}: {e}")
        
        return result
    
    async def perform_mcp_health_check_with_retry(
        self,
        server_config: EnhancedServerConfig,
        max_retries: Optional[int] = None
    ) -> MCPHealthCheckResult:
        """
        Perform MCP health check with custom retry logic.
        
        Args:
            server_config: Enhanced server configuration
            max_retries: Override retry attempts from config
            
        Returns:
            MCPHealthCheckResult: Health check result
        """
        retry_attempts = max_retries or server_config.mcp_retry_attempts
        
        # Create a copy of config with custom retry attempts
        config_copy = EnhancedServerConfig.from_dict(server_config.to_dict())
        config_copy.mcp_retry_attempts = retry_attempts
        
        return await self.perform_mcp_health_check(config_copy)
    
    async def check_multiple_servers_mcp(
        self,
        server_configs: List[EnhancedServerConfig],
        max_concurrent: int = 5
    ) -> List[MCPHealthCheckResult]:
        """
        Perform MCP health checks for multiple servers concurrently.
        
        Args:
            server_configs: List of server configurations
            max_concurrent: Maximum concurrent requests
            
        Returns:
            List[MCPHealthCheckResult]: Health check results
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def check_server(config: EnhancedServerConfig) -> MCPHealthCheckResult:
            async with semaphore:
                return await self.perform_mcp_health_check(config)
        
        # Execute health checks concurrently
        tasks = [check_server(config) for config in server_configs]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle exceptions
        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                # Create error result
                error_result = MCPHealthCheckResult(
                    server_name=server_configs[i].server_name,
                    timestamp=datetime.now(),
                    success=False,
                    response_time_ms=0.0,
                    connection_error=f"Task execution error: {str(result)}"
                )
                final_results.append(error_result)
            else:
                final_results.append(result)
        
        return final_results