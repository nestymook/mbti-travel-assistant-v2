"""
AgentCore Runtime Client

This module provides a comprehensive client for making AgentCore Runtime API calls
with connection management, retry logic, and performance optimizations.

Enhanced Performance Features:
- Response caching for repeated queries
- Connection pooling with health monitoring
- Parallel execution for independent agent calls
- Optimized token refresh with proactive strategies
"""

import asyncio
import json
import logging
import time
import uuid
import urllib.parse
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, AsyncIterator, List
from dataclasses import dataclass, field
from enum import Enum

import aiohttp
import requests

# Import the comprehensive error handling system
from .agentcore_error_handler import (
    AgentCoreError,
    AgentInvocationError,
    AuthenticationError,
    AgentTimeoutError,
    AgentUnavailableError,
    AgentCoreErrorHandler,
    AgentCoreErrorContext,
    get_agentcore_error_handler
)

# Import the new API models for proper parameter mapping and response parsing
try:
    from models.agentcore_api_models import (
        AgentCoreInvocationRequest,
        AgentCoreInvocationResponse,
        AgentCoreStreamingResponse,
        AgentCoreAPITransformer
    )
except ImportError:
    # Fallback for relative imports
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
    from models.agentcore_api_models import (
        AgentCoreInvocationRequest,
        AgentCoreInvocationResponse,
        AgentCoreStreamingResponse,
        AgentCoreAPITransformer
    )

# Import performance optimization services (lazy imports to avoid circular dependencies)
# These will be imported when needed to avoid circular import issues

logger = logging.getLogger(__name__)


class ConfigurationError(AgentCoreError):
    """Configuration-related errors."""
    pass


from .agentcore_error_handler import (
    RetryConfig,
    CircuitBreakerConfig,
    CircuitBreakerState
)


@dataclass
class ConnectionConfig:
    """Configuration for connection management."""
    timeout_seconds: int = 30
    max_connections: int = 100
    max_connections_per_host: int = 10
    keepalive_timeout: int = 30
    enable_cleanup_closed: bool = True


@dataclass
class AgentRequest:
    """Request to AgentCore agent."""
    input_text: str
    session_id: Optional[str] = None
    metadata: Optional[Dict] = None


@dataclass
class AgentResponse:
    """Response from AgentCore agent."""
    output_text: str
    session_id: str
    metadata: Dict
    execution_time_ms: int
    agent_arn: str


@dataclass
class AgentStreamingResponse:
    """Streaming response chunk from AgentCore agent."""
    chunk_text: str
    session_id: str
    is_final: bool
    metadata: Optional[Dict] = None


@dataclass
class HealthStatus:
    """Health status of the client."""
    is_healthy: bool
    last_check: datetime
    error_count: int
    circuit_breaker_state: CircuitBreakerState
    connection_pool_status: Dict[str, Any]


class AgentCoreRuntimeClient:
    """Client for making AgentCore Runtime API calls with performance optimizations."""
    
    def __init__(
        self,
        region: str = "us-east-1",
        retry_config: Optional[RetryConfig] = None,
        circuit_breaker_config: Optional[CircuitBreakerConfig] = None,
        connection_config: Optional[ConnectionConfig] = None,
        enable_caching: bool = True,
        enable_connection_pooling: bool = True,
        enable_parallel_execution: bool = True,
        cache_config: Optional[Any] = None,
        pool_config: Optional[Any] = None,
        execution_config: Optional[Any] = None,
        jwt_token: Optional[str] = None,
        authentication_manager: Optional[Any] = None,
        user_id: Optional[str] = None
    ):
        """
        Initialize AgentCore Runtime client with JWT authentication and performance optimizations.
        
        Args:
            region: AWS region
            retry_config: Retry configuration
            circuit_breaker_config: Circuit breaker configuration
            connection_config: Connection configuration
            enable_caching: Enable response caching
            enable_connection_pooling: Enable connection pooling
            enable_parallel_execution: Enable parallel execution
            cache_config: Cache configuration
            pool_config: Connection pool configuration
            execution_config: Parallel execution configuration
            jwt_token: JWT token for authentication
            authentication_manager: Authentication manager for token management
            user_id: User ID for AgentCore Runtime User ID header (defaults to 'agentcore-client')
        """
        self.region = region
        self.retry_config = retry_config or RetryConfig()
        self.circuit_breaker_config = circuit_breaker_config or CircuitBreakerConfig()
        self.connection_config = connection_config or ConnectionConfig()
        
        # JWT Authentication
        self.jwt_token = jwt_token
        self.authentication_manager = authentication_manager
        self.user_id = user_id or 'agentcore-client'  # Default to generic user ID if not provided
        
        # AgentCore HTTP endpoint configuration
        self.agent_base_url = f"https://bedrock-agentcore.{region}.amazonaws.com"
        
        # Performance optimization flags
        self.enable_caching = enable_caching
        self.enable_connection_pooling = enable_connection_pooling
        self.enable_parallel_execution = enable_parallel_execution
        
        # Initialize performance optimization services with lazy imports
        self.response_cache = None
        self.connection_pool_manager = None
        self.parallel_execution_service = None
        
        if self.enable_caching:
            try:
                from .response_cache import get_response_cache, CacheConfig
                if cache_config is None:
                    cache_config = CacheConfig()  # Use default configuration
                self.response_cache = get_response_cache(cache_config)
                logger.debug("Response caching enabled")
            except ImportError as e:
                logger.warning(f"Could not enable response caching: {e}")
        
        if self.enable_connection_pooling:
            try:
                from .connection_pool_manager import get_connection_pool_manager, ConnectionConfig as PoolConnectionConfig
                if pool_config is None:
                    pool_config = PoolConnectionConfig()  # Use default configuration
                self.connection_pool_manager = get_connection_pool_manager(pool_config)
                logger.debug("Connection pooling enabled")
            except ImportError as e:
                logger.warning(f"Could not enable connection pooling: {e}")
        
        if self.enable_parallel_execution:
            try:
                from .parallel_execution_service import get_parallel_execution_service, ExecutionConfig
                if execution_config is None:
                    execution_config = ExecutionConfig()  # Use default configuration
                self.parallel_execution_service = get_parallel_execution_service(execution_config)
                logger.debug("Parallel execution enabled")
            except ImportError as e:
                logger.warning(f"Could not enable parallel execution: {e}")
        
        # Initialize HTTP session for AgentCore API calls
        self._init_http_session()
        
        # Initialize comprehensive error handler
        self.error_handler = get_agentcore_error_handler()
        
        # Performance tracking
        self.call_count = 0
        self.error_count = 0
        self.total_response_time = 0.0
        self.last_health_check: Optional[datetime] = None
        
        logger.info(f"AgentCore Runtime client initialized for region: {region} with JWT authentication and performance optimizations")
    
    def _init_http_session(self):
        """Initialize HTTP session for additional HTTP calls."""
        # Store session configuration for lazy initialization
        self._session_config = {
            'timeout': aiohttp.ClientTimeout(total=self.connection_config.timeout_seconds),
            'connector_config': {
                'limit': self.connection_config.max_connections,
                'limit_per_host': self.connection_config.max_connections_per_host,
                'keepalive_timeout': self.connection_config.keepalive_timeout,
                'enable_cleanup_closed': self.connection_config.enable_cleanup_closed
            }
        }
        
        self.http_session = None  # Will be initialized when needed
        
        logger.debug("HTTP session configuration prepared")
    
    async def _get_jwt_token(self) -> str:
        """
        Get valid JWT token for authentication.
        
        Returns:
            Valid JWT token string
            
        Raises:
            AuthenticationError: If token cannot be obtained
        """
        logger.debug(f"🔐 _get_jwt_token called - auth_manager: {self.authentication_manager is not None}, jwt_token: {self.jwt_token is not None}")
        
        if self.authentication_manager:
            # Use authentication manager for automatic token refresh
            logger.debug("🔐 Using authentication manager for token")
            return await self.authentication_manager.get_valid_token()
        elif self.jwt_token:
            # Use provided JWT token
            logger.debug(f"🔐 Using provided JWT token: {self.jwt_token[:20]}...")
            return self.jwt_token
        else:
            logger.error("🔐 No JWT token or authentication manager available")
            raise AuthenticationError("No JWT token or authentication manager provided")
    
    def _get_http_session(self):
        """Get or create HTTP session."""
        if self.http_session is None:
            try:
                # Try to get running event loop
                loop = asyncio.get_running_loop()
                connector = aiohttp.TCPConnector(
                    loop=loop,
                    **self._session_config['connector_config']
                )
                self.http_session = aiohttp.ClientSession(
                    timeout=self._session_config['timeout'],
                    connector=connector,
                    loop=loop
                )
            except RuntimeError:
                # No running event loop, create session without loop
                connector = aiohttp.TCPConnector(
                    **self._session_config['connector_config']
                )
                self.http_session = aiohttp.ClientSession(
                    timeout=self._session_config['timeout'],
                    connector=connector
                )
        
        return self.http_session
    
    async def invoke_agent(
        self,
        agent_arn: str,
        input_text: str,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        request_id: Optional[str] = None,
        enable_caching: Optional[bool] = None,
        cache_ttl_override: Optional[int] = None
    ) -> AgentCoreInvocationResponse:
        """
        Invoke an AgentCore agent with input text and performance optimizations.
        
        Args:
            agent_arn: ARN of the target agent
            input_text: Input text for the agent
            session_id: Optional session ID
            user_id: Optional user ID for error context
            request_id: Optional request ID for error context
            enable_caching: Override caching setting for this call
            cache_ttl_override: Override cache TTL for this call
            
        Returns:
            AgentCoreInvocationResponse object with proper parameter mapping
            
        Raises:
            AgentInvocationError: If agent invocation fails
            AuthenticationError: If authentication fails
        """
        # Create AgentCore request with proper parameter mapping
        agentcore_request = AgentCoreInvocationRequest(
            agent_runtime_arn=agent_arn,
            input_text=input_text,
            session_id=session_id
        )
        
        # Validate the request
        agentcore_request.validate()
        
        # Determine if caching should be used for this call
        use_caching = (enable_caching if enable_caching is not None 
                      else self.enable_caching and self.response_cache is not None)
        
        # Check cache first if enabled
        if use_caching:
            cache_key_params = {
                "agent_arn": agent_arn,
                "input_text": input_text,
                "session_id": agentcore_request.session_id
            }
            
            cached_response = await self.response_cache.get(
                operation="invoke_agent",
                parameters=cache_key_params,
                agent_arn=agent_arn
            )
            
            if cached_response is not None:
                logger.debug(f"Cache hit for agent invocation: {agent_arn}")
                return cached_response
        
        start_time = time.time()
        
        # Create error context for comprehensive error handling
        context = self.error_handler.create_error_context(
            agent_arn=agent_arn,
            operation="invoke_agent",
            input_text=input_text,
            session_id=agentcore_request.session_id,
            user_id=user_id,
            request_id=request_id
        )
        
        try:
            # Use comprehensive error handling with circuit breaker and retry
            async def protected_call():
                return await self._invoke_agent_http_with_request(agentcore_request)
            
            raw_response = await self.error_handler.execute_with_protection(protected_call, context)
            
            execution_time_ms = int((time.time() - start_time) * 1000)
            
            # Update performance metrics
            self.call_count += 1
            self.total_response_time += execution_time_ms
            
            # Create structured response using new API models
            agent_response = AgentCoreInvocationResponse.from_api_response(
                response=raw_response,
                agent_arn=agent_arn,
                execution_time_ms=execution_time_ms
            )
            
            # Cache the response if caching is enabled
            if use_caching:
                await self.response_cache.set(
                    operation="invoke_agent",
                    parameters=cache_key_params,
                    value=agent_response,
                    agent_arn=agent_arn,
                    ttl_override=cache_ttl_override
                )
            
            logger.debug(f"Agent invocation successful: {agent_arn} in {execution_time_ms}ms")
            return agent_response
            
        except Exception as e:
            self.error_count += 1
            execution_time_ms = int((time.time() - start_time) * 1000)
            
            logger.error(f"Agent invocation failed: {agent_arn} - {str(e)}")
            
            # Re-raise AgentCore errors as-is
            if isinstance(e, AgentCoreError):
                raise
            else:
                # Wrap other exceptions in AgentInvocationError
                raise AgentInvocationError(
                    f"Failed to invoke agent: {str(e)}",
                    agent_arn
                ) from e
    
    async def _invoke_agent_http_with_request(
        self,
        request: AgentCoreInvocationRequest
    ) -> Dict[str, Any]:
        """
        Invoke agent using HTTP requests with JWT authentication.
        
        Args:
            request: AgentCore invocation request with proper parameter mapping
            
        Returns:
            Raw response from agent
        """
        try:
            # Get JWT token
            jwt_token = await self._get_jwt_token()
            
            # Extract agent ID from ARN
            agent_arn = request.agent_runtime_arn
            if "runtime/" in agent_arn:
                agent_id = agent_arn.split("runtime/")[-1]
            else:
                agent_id = agent_arn.split("/")[-1]
            
            # URL encode the agent ARN
            encoded_agent_arn = urllib.parse.quote(agent_arn, safe='')
            
            # Construct AgentCore endpoint URL
            agent_endpoint = f"{self.agent_base_url}/runtimes/{encoded_agent_arn}/invocations?qualifier=DEFAULT"
            
            # Prepare headers with MCP protocol support
            headers = {
                'Authorization': f'Bearer {jwt_token}',
                'X-Amzn-Bedrock-AgentCore-Runtime-User-Id': self.user_id,
                'Content-Type': 'application/json',
                'Accept': 'application/json, text/event-stream'  # MCP requires both content types
            }
            
            # Prepare payload
            payload = {
                "prompt": request.input_text,
                "sessionId": request.session_id,
                "enableTrace": True
            }
            
            logger.debug(f"Invoking agent via HTTP: {agent_endpoint}")
            logger.debug(f"Session ID: {request.session_id}")
            
            # Make HTTP request using requests library for synchronous call
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: requests.post(
                    agent_endpoint,
                    headers=headers,
                    json=payload,
                    timeout=self.connection_config.timeout_seconds,
                    stream=True
                )
            )
            
            if response.status_code == 200:
                # Handle streaming response
                response_text = ""
                for line in response.iter_lines(decode_unicode=True):
                    if line.startswith("data: "):
                        try:
                            chunk = json.loads(line[6:])  # Parse SSE data
                            if "completion" in chunk:
                                response_text += chunk["completion"]["bytes"].decode("utf-8")
                            elif "trace" in chunk:
                                logger.debug(f"Trace: {chunk['trace']}")
                        except json.JSONDecodeError:
                            continue
                
                # Return response in expected format
                return {
                    'output': response_text,
                    'metadata': {
                        'agent_id': agent_id,
                        'session_id': request.session_id,
                        'status_code': response.status_code
                    }
                }
            else:
                # Handle HTTP errors
                error_text = response.text
                logger.error(f"HTTP request failed: {response.status_code} - {error_text}")
                
                if response.status_code == 401:
                    raise AuthenticationError(
                        f"Authentication failed: {error_text}",
                        auth_type="JWT",
                        details={"status_code": response.status_code}
                    )
                elif response.status_code == 403:
                    raise AuthenticationError(
                        f"Access denied: {error_text}",
                        auth_type="JWT",
                        details={"status_code": response.status_code}
                    )
                elif response.status_code == 408 or response.status_code == 504:
                    raise AgentTimeoutError(
                        f"Agent call timed out: {error_text}",
                        timeout_duration=self.connection_config.timeout_seconds,
                        agent_arn=agent_arn
                    )
                elif response.status_code == 429:
                    raise AgentUnavailableError(
                        f"Agent is throttled: {error_text}",
                        agent_arn
                    )
                else:
                    raise AgentInvocationError(
                        f"Agent invocation failed: HTTP {response.status_code} - {error_text}",
                        agent_arn,
                        response.status_code,
                        {"error_text": error_text}
                    )
                    
        except requests.exceptions.Timeout as e:
            raise AgentTimeoutError(
                f"Agent call timed out: {str(e)}",
                timeout_duration=self.connection_config.timeout_seconds,
                agent_arn=request.agent_runtime_arn
            )
        except requests.exceptions.ConnectionError as e:
            raise AgentUnavailableError(
                f"Agent is unavailable: {str(e)}",
                request.agent_runtime_arn
            )
        except requests.exceptions.RequestException as e:
            raise AgentInvocationError(
                f"HTTP request failed: {str(e)}",
                request.agent_runtime_arn
            )
        except AuthenticationError:
            raise
        except Exception as e:
            # Check for specific error patterns
            error_str = str(e).lower()
            if 'timeout' in error_str:
                raise AgentTimeoutError(
                    f"Agent call timed out: {str(e)}",
                    timeout_duration=self.connection_config.timeout_seconds,
                    agent_arn=request.agent_runtime_arn
                )
            elif 'connection' in error_str or 'network' in error_str:
                raise AgentUnavailableError(
                    f"Agent is unavailable: {str(e)}",
                    request.agent_runtime_arn
                )
            else:
                raise AgentInvocationError(
                    f"Agent invocation failed: {str(e)}",
                    request.agent_runtime_arn
                )
    

    
    def create_fallback_response(self, operation: str, agent_arn: str, 
                               user_id: Optional[str] = None, 
                               session_id: Optional[str] = None) -> Dict[str, Any]:
        """Create fallback response when agent is unavailable."""
        context = self.error_handler.create_error_context(
            agent_arn=agent_arn,
            operation=operation,
            user_id=user_id,
            session_id=session_id
        )
        
        return self.error_handler.create_fallback_response(operation, context)
    
    async def invoke_agent_with_streaming(
        self,
        agent_arn: str,
        input_text: str,
        session_id: Optional[str] = None
    ) -> AsyncIterator[AgentCoreStreamingResponse]:
        """
        Invoke agent with streaming response using new API models.
        
        Args:
            agent_arn: ARN of the target agent
            input_text: Input text for the agent
            session_id: Optional session ID
            
        Yields:
            AgentCoreStreamingResponse objects with proper parameter mapping
        """
        # Create AgentCore request with proper parameter mapping
        agentcore_request = AgentCoreInvocationRequest(
            agent_runtime_arn=agent_arn,
            input_text=input_text,
            session_id=session_id
        )
        
        # Validate the request
        agentcore_request.validate()
        
        try:
            # Get JWT token
            jwt_token = await self._get_jwt_token()
            
            # Extract agent ID from ARN
            agent_arn = agentcore_request.agent_runtime_arn
            if "runtime/" in agent_arn:
                agent_id = agent_arn.split("runtime/")[-1]
            else:
                agent_id = agent_arn.split("/")[-1]
            
            # URL encode the agent ARN
            encoded_agent_arn = urllib.parse.quote(agent_arn, safe='')
            
            # Construct AgentCore endpoint URL
            agent_endpoint = f"{self.agent_base_url}/runtimes/{encoded_agent_arn}/invocations?qualifier=DEFAULT"
            
            # Prepare headers
            headers = {
                'Authorization': f'Bearer {jwt_token}',
                'X-Amzn-Bedrock-AgentCore-Runtime-User-Id': self.user_id,
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            
            # Prepare payload
            payload = {
                "prompt": agentcore_request.input_text,
                "sessionId": agentcore_request.session_id,
                "enableTrace": True
            }
            
            logger.debug(f"Invoking agent with streaming via HTTP: {agent_endpoint}")
            
            # Make HTTP request for streaming
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: requests.post(
                    agent_endpoint,
                    headers=headers,
                    json=payload,
                    timeout=self.connection_config.timeout_seconds,
                    stream=True
                )
            )
            
            if response.status_code == 200:
                chunk_index = 0
                
                # Process streaming response
                for line in response.iter_lines(decode_unicode=True):
                    if line.startswith("data: "):
                        try:
                            chunk = json.loads(line[6:])  # Parse SSE data
                            if "completion" in chunk:
                                chunk_text = chunk["completion"]["bytes"].decode("utf-8")
                                
                                # Use new streaming response model
                                streaming_response = AgentCoreStreamingResponse(
                                    chunk_text=chunk_text,
                                    session_id=agentcore_request.session_id,
                                    is_final=False,
                                    chunk_index=chunk_index
                                )
                                yield streaming_response
                                chunk_index += 1
                            elif "trace" in chunk:
                                logger.debug(f"Trace: {chunk['trace']}")
                        except json.JSONDecodeError:
                            continue
                
                # Send final chunk
                final_response = AgentCoreStreamingResponse(
                    chunk_text="",
                    session_id=agentcore_request.session_id,
                    is_final=True,
                    chunk_index=chunk_index
                )
                yield final_response
            else:
                # Handle HTTP errors for streaming
                error_text = response.text
                raise AgentInvocationError(
                    f"Streaming invocation failed: HTTP {response.status_code} - {error_text}",
                    agent_arn
                )
            
        except Exception as e:
            logger.error(f"Streaming invocation failed: {agent_arn} - {str(e)}")
            raise AgentInvocationError(
                f"Failed to invoke agent with streaming: {str(e)}",
                agent_arn
            ) from e
    
    def get_health_status(self) -> HealthStatus:
        """Get client health and connectivity status."""
        self.last_health_check = datetime.utcnow()
        
        # Check connection pool status
        connection_pool_status = {
            "total_connections": self.connection_config.max_connections,
            "connections_per_host": self.connection_config.max_connections_per_host,
            "timeout_seconds": self.connection_config.timeout_seconds
        }
        
        # Get circuit breaker stats from error handler
        cb_stats = self.error_handler.get_circuit_breaker_stats()
        
        # Determine health based on error rate and circuit breaker states
        error_rate = self.error_count / max(self.call_count, 1)
        
        # Check if any circuit breakers are open
        any_cb_open = any(
            stats.get("state") == "open" 
            for stats in cb_stats.values() 
            if isinstance(stats, dict)
        )
        
        is_healthy = (
            error_rate < 0.5 and  # Less than 50% error rate
            not any_cb_open  # No circuit breakers are open
        )
        
        return HealthStatus(
            is_healthy=is_healthy,
            last_check=self.last_health_check,
            error_count=self.error_count,
            circuit_breaker_state=CircuitBreakerState.OPEN if any_cb_open else CircuitBreakerState.CLOSED,
            connection_pool_status=connection_pool_status
        )
    
    async def invoke_agents_parallel(
        self,
        agent_calls: List[Dict[str, Any]],
        execution_id: Optional[str] = None
    ) -> Dict[str, AgentResponse]:
        """
        Invoke multiple agents in parallel for improved performance.
        
        Args:
            agent_calls: List of agent call configurations
                Each dict should contain: agent_arn, input_text, session_id (optional)
            execution_id: Optional execution identifier
            
        Returns:
            Dictionary mapping call IDs to AgentResponse objects
        """
        if not self.enable_parallel_execution or not self.parallel_execution_service:
            # Fall back to sequential execution
            results = {}
            for i, call_config in enumerate(agent_calls):
                call_id = call_config.get('call_id', f"call_{i}")
                try:
                    response = await self.invoke_agent(
                        agent_arn=call_config['agent_arn'],
                        input_text=call_config['input_text'],
                        session_id=call_config.get('session_id')
                    )
                    results[call_id] = response
                except Exception as e:
                    logger.error(f"Sequential agent call {call_id} failed: {e}")
                    # Continue with other calls
            return results
        
        # Use parallel execution service
        from .parallel_execution_service import TaskDefinition
        
        tasks = []
        for i, call_config in enumerate(agent_calls):
            call_id = call_config.get('call_id', f"call_{i}")
            
            async def create_task_func(config=call_config):
                return await self.invoke_agent(
                    agent_arn=config['agent_arn'],
                    input_text=config['input_text'],
                    session_id=config.get('session_id'),
                    enable_caching=config.get('enable_caching')
                )
            
            task = TaskDefinition(
                task_id=call_id,
                task_func=create_task_func,
                timeout_seconds=call_config.get('timeout_seconds', 60)
            )
            tasks.append(task)
        
        # Execute in parallel
        result = await self.parallel_execution_service.execute_parallel(
            tasks, execution_id
        )
        
        # Return successful results
        return result.get_successful_results()
    
    async def execute_restaurant_workflow_parallel(
        self,
        search_agent_arn: str,
        reasoning_agent_arn: str,
        search_input: str,
        reasoning_input_template: str,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute restaurant search and reasoning workflow with parallel optimization.
        
        Args:
            search_agent_arn: ARN of search agent
            reasoning_agent_arn: ARN of reasoning agent
            search_input: Input for search agent
            reasoning_input_template: Template for reasoning input (will be filled with search results)
            session_id: Optional session ID
            
        Returns:
            Combined workflow results
        """
        if not self.enable_parallel_execution or not self.parallel_execution_service:
            # Sequential execution
            search_response = await self.invoke_agent(
                agent_arn=search_agent_arn,
                input_text=search_input,
                session_id=session_id
            )
            
            # Use search results in reasoning input
            reasoning_input = reasoning_input_template.format(
                search_results=search_response.output_text
            )
            
            reasoning_response = await self.invoke_agent(
                agent_arn=reasoning_agent_arn,
                input_text=reasoning_input,
                session_id=session_id
            )
            
            return {
                "search_result": search_response,
                "reasoning_result": reasoning_response,
                "parallel_execution": False
            }
        
        # Use parallel execution service for optimized workflow
        async def search_func():
            return await self.invoke_agent(
                agent_arn=search_agent_arn,
                input_text=search_input,
                session_id=session_id
            )
        
        async def reasoning_func(search_result):
            if search_result:
                reasoning_input = reasoning_input_template.format(
                    search_results=search_result.output_text
                )
            else:
                reasoning_input = reasoning_input_template.format(search_results="")
            
            return await self.invoke_agent(
                agent_arn=reasoning_agent_arn,
                input_text=reasoning_input,
                session_id=session_id
            )
        
        result = await self.parallel_execution_service.execute_restaurant_workflow(
            search_func, reasoning_func, enable_parallel_search=True
        )
        
        return result
    
    def invalidate_cache(
        self, 
        operation: Optional[str] = None,
        agent_arn: Optional[str] = None
    ) -> int:
        """
        Invalidate response cache entries.
        
        Args:
            operation: Optional operation to invalidate
            agent_arn: Optional agent ARN to invalidate
            
        Returns:
            Number of entries invalidated
        """
        if not self.response_cache:
            return 0
        
        return self.response_cache.invalidate(operation, agent_arn=agent_arn)
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get comprehensive performance metrics."""
        avg_response_time = (
            self.total_response_time / max(self.call_count, 1)
            if self.call_count > 0 else 0
        )
        
        # Get circuit breaker stats from error handler
        cb_stats = self.error_handler.get_circuit_breaker_stats()
        
        metrics = {
            "client_metrics": {
                "total_calls": self.call_count,
                "total_errors": self.error_count,
                "error_rate": self.error_count / max(self.call_count, 1),
                "average_response_time_ms": avg_response_time,
                "circuit_breaker_stats": cb_stats
            }
        }
        
        # Add cache metrics if available
        if self.response_cache:
            cache_stats = self.response_cache.get_statistics()
            if cache_stats:
                metrics["cache_metrics"] = cache_stats
        
        # Add connection pool metrics if available
        if self.connection_pool_manager:
            pool_stats = self.connection_pool_manager.get_pool_statistics()
            metrics["connection_pool_metrics"] = pool_stats
        
        # Add parallel execution metrics if available
        if self.parallel_execution_service:
            execution_stats = self.parallel_execution_service.get_execution_statistics()
            metrics["parallel_execution_metrics"] = execution_stats
        
        return metrics
    
    # Backward Compatibility Methods
    
    async def invoke_agent_legacy(
        self,
        agent_arn: str,
        input_text: str,
        session_id: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Invoke agent with legacy response format for backward compatibility.
        
        Args:
            agent_arn: ARN of the target agent
            input_text: Input text for the agent
            session_id: Optional session ID
            **kwargs: Additional legacy parameters
            
        Returns:
            Dictionary in legacy response format
        """
        # Use new API models internally
        response = await self.invoke_agent(
            agent_arn=agent_arn,
            input_text=input_text,
            session_id=session_id,
            **kwargs
        )
        
        # Transform to legacy format using API transformer
        return AgentCoreAPITransformer.ensure_backward_compatibility(response)
    
    def transform_response_for_compatibility(
        self,
        response: AgentCoreInvocationResponse
    ) -> Dict[str, Any]:
        """
        Transform new response format to maintain backward compatibility.
        
        Args:
            response: AgentCore response object
            
        Returns:
            Dictionary with both new and legacy fields
        """
        return AgentCoreAPITransformer.ensure_backward_compatibility(response)
    
    async def close(self):
        """Close client and cleanup resources."""
        if self.http_session is not None:
            await self.http_session.close()
            self.http_session = None
        
        # Close performance optimization services
        if self.response_cache:
            await self.response_cache.close()
        
        if self.connection_pool_manager:
            await self.connection_pool_manager.close()
        
        # Note: parallel_execution_service is typically a singleton and doesn't need explicit closing
        
        logger.info("AgentCore Runtime client closed with all performance optimization services")
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()


def create_agentcore_client_with_jwt(
    jwt_token: str,
    region: str = "us-east-1",
    **kwargs
) -> AgentCoreRuntimeClient:
    """
    Create AgentCore Runtime client with JWT token.
    
    Args:
        jwt_token: JWT token for authentication
        region: AWS region
        **kwargs: Additional client configuration
        
    Returns:
        Configured AgentCore Runtime client
    """
    return AgentCoreRuntimeClient(
        region=region,
        jwt_token=jwt_token,
        **kwargs
    )


def create_agentcore_client_with_auth_manager(
    authentication_manager: Any,
    region: str = "us-east-1",
    **kwargs
) -> AgentCoreRuntimeClient:
    """
    Create AgentCore Runtime client with authentication manager.
    
    Args:
        authentication_manager: Authentication manager instance
        region: AWS region
        **kwargs: Additional client configuration
        
    Returns:
        Configured AgentCore Runtime client
    """
    return AgentCoreRuntimeClient(
        region=region,
        authentication_manager=authentication_manager,
        **kwargs
    )


# Export main classes
__all__ = [
    'AgentCoreRuntimeClient',
    'AgentRequest',
    'AgentResponse',
    'AgentStreamingResponse',
    'HealthStatus',
    'RetryConfig',
    'CircuitBreakerConfig',
    'ConnectionConfig',
    'AgentCoreError',
    'AuthenticationError',
    'AgentInvocationError',
    'ConfigurationError',
    'create_agentcore_client_with_jwt',
    'create_agentcore_client_with_auth_manager'
]