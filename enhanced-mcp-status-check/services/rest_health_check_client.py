"""
REST Health Check Client

This module implements the REST Health Check Client for performing HTTP health checks
on MCP server health endpoints with proper validation and retry logic.
"""

import asyncio
import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
import aiohttp
import logging

from models.dual_health_models import (
    RESTHealthCheckResponse,
    RESTValidationResult,
    RESTHealthCheckResult,
    EnhancedServerConfig
)
from models.auth_models import (
    AuthenticationConfig,
    AuthenticationError
)
from services.authentication_service import AuthenticationService


logger = logging.getLogger(__name__)


class RESTHealthCheckClient:
    """
    REST Health Check Client for HTTP health endpoints.
    
    This client performs HTTP health checks on MCP server REST endpoints
    with proper validation, retry logic, and error handling.
    """
    
    def __init__(self, session: Optional[aiohttp.ClientSession] = None, auth_service: Optional[AuthenticationService] = None):
        """
        Initialize REST Health Check Client.
        
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
    
    async def send_health_request(
        self,
        health_endpoint_url: str,
        auth_headers: Optional[Dict[str, str]] = None,
        timeout: int = 8
    ) -> RESTHealthCheckResponse:
        """
        Send HTTP GET request to health endpoint.
        
        Args:
            health_endpoint_url: Health endpoint URL
            auth_headers: Optional authentication headers
            timeout: Request timeout in seconds
            
        Returns:
            RESTHealthCheckResponse: HTTP response data
            
        Raises:
            aiohttp.ClientError: On HTTP client errors
            asyncio.TimeoutError: On request timeout
        """
        if self._session is None:
            raise RuntimeError("Client session not initialized. Use async context manager.")
        
        # Prepare headers
        headers = {
            'Accept': 'application/json',
            'User-Agent': 'Enhanced-MCP-Status-Check/1.0'
        }
        if auth_headers:
            headers.update(auth_headers)
        
        logger.debug(f"Sending REST health request to {health_endpoint_url}")
        
        start_time = time.time()
        
        # Send GET request
        async with self._session.get(
            health_endpoint_url,
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=timeout)
        ) as response:
            end_time = time.time()
            response_time_ms = (end_time - start_time) * 1000
            
            # Get response headers
            response_headers = dict(response.headers)
            
            # Get response body
            response_text = await response.text()
            response_body = None
            
            # Try to parse JSON response
            if response_text:
                try:
                    response_body = json.loads(response_text)
                except json.JSONDecodeError:
                    # Not JSON, keep as text in a wrapper
                    response_body = {"raw_response": response_text}
            
            logger.debug(f"REST response status: {response.status}")
            logger.debug(f"REST response time: {response_time_ms:.2f}ms")
            logger.debug(f"REST response body: {response_body}")
            
            return RESTHealthCheckResponse(
                status_code=response.status,
                headers=response_headers,
                body=response_body,
                response_time_ms=response_time_ms,
                url=health_endpoint_url
            )
    
    def validate_rest_response(
        self,
        response: RESTHealthCheckResponse
    ) -> RESTValidationResult:
        """
        Validate REST health check response.
        
        Args:
            response: REST health check response
            
        Returns:
            RESTValidationResult: Validation result
        """
        validation_errors = []
        
        # Validate HTTP status code
        http_status_valid = response.is_success()
        if not http_status_valid:
            validation_errors.append(f"HTTP status {response.status_code} indicates failure")
        
        # Validate response format
        response_format_valid = True
        if response.body is None:
            validation_errors.append("Empty response body")
            response_format_valid = False
        elif not isinstance(response.body, dict):
            validation_errors.append("Response body is not valid JSON object")
            response_format_valid = False
        
        # Check for health indicators
        health_indicators_present = False
        server_metrics = None
        
        if response.body and isinstance(response.body, dict):
            # Look for common health indicators
            health_fields = ['status', 'health', 'healthy', 'state', 'ok']
            for field in health_fields:
                if field in response.body:
                    health_indicators_present = True
                    break
            
            # Extract server metrics if available
            metrics_fields = ['metrics', 'stats', 'statistics', 'performance']
            for field in metrics_fields:
                if field in response.body:
                    server_metrics = response.body[field]
                    break
            
            # Check for specific health check patterns
            if 'status' in response.body:
                status_value = response.body['status']
                if isinstance(status_value, str):
                    if status_value.lower() not in ['ok', 'healthy', 'up', 'running', 'active']:
                        validation_errors.append(f"Health status indicates problem: {status_value}")
            
            # Check for error indicators
            error_fields = ['error', 'errors', 'failure', 'failed']
            for field in error_fields:
                if field in response.body and response.body[field]:
                    validation_errors.append(f"Response contains error indicator: {field}")
        
        # Determine overall validity
        is_valid = (
            http_status_valid and
            response_format_valid and
            health_indicators_present and
            len(validation_errors) == 0
        )
        
        return RESTValidationResult(
            is_valid=is_valid,
            http_status_valid=http_status_valid,
            response_format_valid=response_format_valid,
            health_indicators_present=health_indicators_present,
            validation_errors=validation_errors,
            server_metrics=server_metrics
        )
    
    async def perform_rest_health_check_with_retry(
        self,
        health_endpoint_url: str,
        auth_headers: Optional[Dict[str, str]] = None,
        timeout: int = 8,
        max_retries: int = 2,
        backoff_factor: float = 1.0
    ) -> RESTHealthCheckResponse:
        """
        Perform REST health check with exponential backoff retry logic.
        
        Args:
            health_endpoint_url: Health endpoint URL
            auth_headers: Optional authentication headers
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            backoff_factor: Exponential backoff multiplier
            
        Returns:
            RESTHealthCheckResponse: Health check response
            
        Raises:
            Exception: If all retry attempts fail
        """
        last_exception = None
        
        for attempt in range(max_retries + 1):  # +1 for initial attempt
            try:
                response = await self.send_health_request(
                    health_endpoint_url=health_endpoint_url,
                    auth_headers=auth_headers,
                    timeout=timeout
                )
                
                # Return immediately on success
                if response.is_success():
                    return response
                
                # For non-success HTTP status, still return the response
                # (caller can decide if this should trigger retry)
                if attempt == max_retries:
                    return response
                
            except Exception as e:
                last_exception = e
                logger.warning(f"REST health check attempt {attempt + 1} failed: {e}")
                
                # Don't retry on the last attempt
                if attempt == max_retries:
                    break
                
                # Calculate backoff delay
                delay = backoff_factor * (2 ** attempt)
                logger.debug(f"Retrying in {delay} seconds...")
                await asyncio.sleep(delay)
        
        # All attempts failed, raise the last exception
        raise last_exception or Exception("All retry attempts failed")
    
    async def perform_rest_health_check(
        self,
        server_config: EnhancedServerConfig
    ) -> RESTHealthCheckResult:
        """
        Perform complete REST health check for a server.
        
        Args:
            server_config: Enhanced server configuration
            
        Returns:
            RESTHealthCheckResult: Complete REST health check result
        """
        start_time = time.time()
        timestamp = datetime.now()
        
        # Initialize result with defaults
        result = RESTHealthCheckResult(
            server_name=server_config.server_name,
            timestamp=timestamp,
            success=False,
            response_time_ms=0.0,
            health_endpoint_url=server_config.rest_health_endpoint_url
        )
        
        if not server_config.rest_enabled:
            result.connection_error = "REST health checks disabled in configuration"
            return result
        
        if not server_config.rest_health_endpoint_url:
            result.connection_error = "REST health endpoint URL not configured"
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
                            logger.error(f"REST authentication failed for {server_config.server_name}: {auth_result.error_message}")
                    
                    except Exception as e:
                        auth_error = f"Authentication error: {str(e)}"
                        logger.error(f"REST authentication error for {server_config.server_name}: {e}")
            
            # Fallback to legacy authentication headers
            if server_config.jwt_token:
                auth_headers['Authorization'] = f'Bearer {server_config.jwt_token}'
            if server_config.auth_headers:
                auth_headers.update(server_config.auth_headers)
            
            # If authentication failed and no fallback, return error
            if auth_error and not auth_headers:
                result.connection_error = auth_error
                result.http_error = "Authentication failed"
                return result
            
            # Perform health check with retry
            response = await self.perform_rest_health_check_with_retry(
                health_endpoint_url=server_config.rest_health_endpoint_url,
                auth_headers=auth_headers,
                timeout=server_config.rest_timeout_seconds,
                max_retries=server_config.rest_retry_attempts,
                backoff_factor=1.0
            )
            
            # Calculate total response time
            end_time = time.time()
            result.response_time_ms = (end_time - start_time) * 1000
            
            # Store response data
            result.status_code = response.status_code
            result.response_body = response.body
            
            # Validate response
            validation_result = self.validate_rest_response(response)
            result.validation_result = validation_result
            
            # Extract server health data
            if response.body and isinstance(response.body, dict):
                # Extract server metrics
                if validation_result.server_metrics:
                    result.server_metrics = validation_result.server_metrics
                
                # Extract circuit breaker states
                if 'circuit_breaker' in response.body:
                    result.circuit_breaker_states = response.body['circuit_breaker']
                elif 'circuit_breakers' in response.body:
                    result.circuit_breaker_states = response.body['circuit_breakers']
                
                # Extract system health
                if 'system' in response.body:
                    result.system_health = response.body['system']
                elif 'health' in response.body and isinstance(response.body['health'], dict):
                    result.system_health = response.body['health']
            
            # Handle HTTP errors
            if not response.is_success():
                result.http_error = f"HTTP {response.status_code}"
                if response.body and isinstance(response.body, dict):
                    error_msg = response.body.get('error') or response.body.get('message')
                    if error_msg:
                        result.http_error += f": {error_msg}"
            
            # Determine success based on validation
            result.success = validation_result.is_valid
            
            logger.info(f"REST health check completed for {server_config.server_name}: "
                       f"success={result.success}, status={result.status_code}, "
                       f"response_time={result.response_time_ms:.2f}ms")
            
        except asyncio.TimeoutError:
            result.connection_error = f"Request timeout after {server_config.rest_timeout_seconds} seconds"
            result.response_time_ms = server_config.rest_timeout_seconds * 1000
            logger.error(f"REST health check timeout for {server_config.server_name}")
            
        except aiohttp.ClientError as e:
            result.http_error = f"HTTP client error: {str(e)}"
            end_time = time.time()
            result.response_time_ms = (end_time - start_time) * 1000
            logger.error(f"REST health check client error for {server_config.server_name}: {e}")
            
        except Exception as e:
            result.connection_error = f"Unexpected error: {str(e)}"
            end_time = time.time()
            result.response_time_ms = (end_time - start_time) * 1000
            logger.error(f"REST health check unexpected error for {server_config.server_name}: {e}")
        
        return result
    
    async def check_multiple_servers_rest(
        self,
        server_configs: List[EnhancedServerConfig],
        max_concurrent: int = 5
    ) -> List[RESTHealthCheckResult]:
        """
        Perform REST health checks for multiple servers concurrently.
        
        Args:
            server_configs: List of server configurations
            max_concurrent: Maximum concurrent requests
            
        Returns:
            List[RESTHealthCheckResult]: Health check results
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def check_server(config: EnhancedServerConfig) -> RESTHealthCheckResult:
            async with semaphore:
                return await self.perform_rest_health_check(config)
        
        # Execute health checks concurrently
        tasks = [check_server(config) for config in server_configs]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle exceptions
        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                # Create error result
                error_result = RESTHealthCheckResult(
                    server_name=server_configs[i].server_name,
                    timestamp=datetime.now(),
                    success=False,
                    response_time_ms=0.0,
                    health_endpoint_url=server_configs[i].rest_health_endpoint_url,
                    connection_error=f"Task execution error: {str(result)}"
                )
                final_results.append(error_result)
            else:
                final_results.append(result)
        
        return final_results
    
    def extract_health_metrics(
        self,
        response_body: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Extract health metrics from REST response body.
        
        Args:
            response_body: Response body dictionary
            
        Returns:
            Dict[str, Any]: Extracted health metrics
        """
        metrics = {}
        
        if not response_body or not isinstance(response_body, dict):
            return metrics
        
        # Extract common metric patterns
        metric_patterns = {
            'uptime': ['uptime', 'up_time', 'running_time'],
            'memory_usage': ['memory', 'mem', 'memory_usage', 'memory_used'],
            'cpu_usage': ['cpu', 'cpu_usage', 'cpu_percent'],
            'request_count': ['requests', 'request_count', 'total_requests'],
            'error_count': ['errors', 'error_count', 'total_errors'],
            'response_time': ['response_time', 'avg_response_time', 'latency'],
            'active_connections': ['connections', 'active_connections', 'conn_count']
        }
        
        for metric_name, patterns in metric_patterns.items():
            for pattern in patterns:
                if pattern in response_body:
                    metrics[metric_name] = response_body[pattern]
                    break
        
        # Extract nested metrics
        if 'metrics' in response_body and isinstance(response_body['metrics'], dict):
            metrics.update(response_body['metrics'])
        
        if 'stats' in response_body and isinstance(response_body['stats'], dict):
            metrics.update(response_body['stats'])
        
        return metrics
    
    def determine_health_status(
        self,
        response: RESTHealthCheckResponse,
        validation_result: RESTValidationResult
    ) -> str:
        """
        Determine health status from REST response.
        
        Args:
            response: REST health check response
            validation_result: Validation result
            
        Returns:
            str: Health status (HEALTHY, DEGRADED, UNHEALTHY)
        """
        # Check HTTP status first
        if not response.is_success():
            return "UNHEALTHY"
        
        # Check validation result
        if not validation_result.is_valid:
            return "UNHEALTHY"
        
        # Check response body for specific status
        if response.body and isinstance(response.body, dict):
            status_value = response.body.get('status', '').lower()
            
            if status_value in ['healthy', 'ok', 'up', 'running', 'active']:
                return "HEALTHY"
            elif status_value in ['degraded', 'warning', 'partial']:
                return "DEGRADED"
            elif status_value in ['unhealthy', 'down', 'failed', 'error']:
                return "UNHEALTHY"
        
        # Default to healthy if all checks pass
        return "HEALTHY"