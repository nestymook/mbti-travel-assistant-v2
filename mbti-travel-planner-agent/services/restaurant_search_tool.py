"""
Restaurant Search Tool with AgentCore Integration

This module provides a restaurant search tool that uses direct AgentCore Runtime API calls
instead of HTTP gateway intermediaries. It maintains backward compatibility with the existing
interface while providing better performance and reliability.

Features:
- Direct AgentCore agent invocation
- Comprehensive monitoring and observability
- Automatic correlation ID tracking
- Performance metrics collection
- Error handling with fallback responses
"""

import asyncio
import json
import logging
import time
from typing import Dict, Any, List, Optional, Union, TYPE_CHECKING
from dataclasses import dataclass
from datetime import datetime

# Type hints only imports to avoid circular dependency
if TYPE_CHECKING:
    from .tool_registry import ToolRegistry, ToolMetadata

# Import comprehensive error handling
from .agentcore_error_handler import (
    AgentCoreError,
    AgentInvocationError,
    AgentTimeoutError,
    AgentUnavailableError,
    get_agentcore_error_handler
)

# Import monitoring middleware
from .agentcore_monitoring_middleware import (
    monitor_restaurant_search,
    get_monitoring_middleware,
    AgentOperationType
)

try:
    from strands import tool
    STRANDS_AVAILABLE = True
except ImportError:
    try:
        # Try alternative import path
        from strands_agents.tools import Tool as StrandsAgentTool
        # Create a tool decorator that mimics strands.tool behavior
        def tool(func=None, *, name=None, description=None):
            def decorator(f):
                # Create a Tool object that behaves like the decorated function
                tool_obj = StrandsAgentTool(
                    name=name or f.__name__,
                    description=description or f.__doc__ or "",
                    function=f
                )
                # Make the tool object callable like the original function
                def wrapper(*args, **kwargs):
                    return f(*args, **kwargs)
                wrapper.name = tool_obj.name
                wrapper.description = tool_obj.description
                wrapper._tool_obj = tool_obj
                return wrapper
            return decorator(func) if func else decorator
        STRANDS_AVAILABLE = True
    except ImportError:
        # Mock tool decorator for testing when neither is available
        def tool(func=None, *, name=None, description=None):
            def decorator(f):
                f.name = name or f.__name__
                f.description = description or f.__doc__ or ""
                return f
            return decorator(func) if func else decorator
        STRANDS_AVAILABLE = False

from .agentcore_runtime_client import (
    AgentCoreRuntimeClient, 
    AgentCoreError, 
    AuthenticationError, 
    AgentInvocationError,
    AgentResponse
)
from .authentication_manager import AuthenticationManager, CognitoConfig

logger = logging.getLogger(__name__)


@dataclass
class RestaurantSearchResult:
    """Result from restaurant search."""
    restaurants: List[Dict]
    total_count: int
    search_metadata: Dict
    execution_time_ms: int
    success: bool = True
    error_message: Optional[str] = None
    fallback_data: Optional[Dict[str, Any]] = None


class RestaurantSearchTool:
    """Tool for searching restaurants using AgentCore agent with comprehensive monitoring."""
    
    def __init__(
        self, 
        runtime_client: AgentCoreRuntimeClient,
        search_agent_arn: str,
        auth_manager: Optional[AuthenticationManager] = None,
        tool_registry: Optional['ToolRegistry'] = None
    ):
        """
        Initialize restaurant search tool.
        
        Args:
            runtime_client: AgentCore Runtime client
            search_agent_arn: ARN of the restaurant search agent
            auth_manager: Authentication manager (optional)
            tool_registry: Tool registry for orchestration integration (optional)
        """
        self.runtime_client = runtime_client
        self.search_agent_arn = search_agent_arn
        self.auth_manager = auth_manager
        self.tool_registry = tool_registry
        
        # Initialize monitoring middleware
        self.monitoring_middleware = get_monitoring_middleware()
        
        # Performance tracking (legacy - now handled by monitoring service)
        self.call_count = 0
        self.error_count = 0
        self.total_response_time = 0.0
        
        # Tool metadata for orchestration
        self.tool_id = "restaurant_search_tool"
        self.tool_metadata = self._create_tool_metadata()
        
        # Register with orchestration engine if registry provided
        if self.tool_registry:
            self._register_with_orchestration()
        
        logger.info(f"Restaurant search tool initialized with agent: {search_agent_arn}")
        logger.info("Monitoring and observability features enabled")
    
    async def search_restaurants_by_district(
        self, 
        districts: List[str],
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        request_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        enable_caching: bool = True,
        cache_ttl_override: Optional[int] = None
    ) -> RestaurantSearchResult:
        """
        Search restaurants by district using AgentCore agent.
        
        Args:
            districts: List of district names to search
            user_id: Optional user ID for error context
            session_id: Optional session ID for error context
            request_id: Optional request ID for error context
            correlation_id: Optional correlation ID for request tracing
            
        Returns:
            RestaurantSearchResult object
        """
        # Use monitoring context manager for comprehensive observability
        async with self.monitoring_middleware.monitoring_context(
            operation_type=AgentOperationType.RESTAURANT_SEARCH,
            agent_arn=self.search_agent_arn,
            user_id=user_id,
            session_id=session_id,
            request_id=request_id,
            correlation_id=correlation_id
        ) as context:
            start_time = time.time()
            operation = "search_restaurants_by_district"
            error_handler = get_agentcore_error_handler()
            
            try:
                # Validate input parameters
                if not districts:
                    raise ValueError("Districts list cannot be empty")
                
                if not isinstance(districts, list):
                    raise ValueError("Districts must be provided as a list")
                
                if not all(isinstance(d, str) and d.strip() for d in districts):
                    raise ValueError("All districts must be non-empty strings")
                
                # Prepare input for AgentCore agent
                search_request = {
                    "action": "search_restaurants_by_district",
                    "parameters": {
                        "districts": districts
                    }
                }
                
                input_text = json.dumps(search_request, ensure_ascii=False)
                
                logger.info(f"Searching restaurants in districts: {districts} [correlation_id: {context.correlation_id}]")
                
                # Log invocation start
                self.monitoring_middleware.monitoring_service.log_agent_invocation_start(
                    agent_arn=self.search_agent_arn,
                    operation_type=AgentOperationType.RESTAURANT_SEARCH,
                    input_text=input_text,
                    session_id=session_id,
                    user_id=user_id,
                    request_id=request_id,
                    correlation_id=context.correlation_id
                )
                
                # Invoke AgentCore agent with comprehensive error handling and performance optimizations
                response = await self.runtime_client.invoke_agent(
                    agent_arn=self.search_agent_arn,
                    input_text=input_text,
                    session_id=session_id,
                    user_id=user_id,
                    request_id=request_id,
                    enable_caching=enable_caching,
                    cache_ttl_override=cache_ttl_override
                )
            
                # Parse response
                result_data = self._parse_agent_response(response)
                
                execution_time_ms = int((time.time() - start_time) * 1000)
                
                # Update performance metrics (legacy)
                self.call_count += 1
                self.total_response_time += execution_time_ms
                
                # Log successful invocation result
                self.monitoring_middleware.monitoring_service.log_agent_invocation_result(
                    correlation_id=context.correlation_id,
                    agent_arn=self.search_agent_arn,
                    operation_type=AgentOperationType.RESTAURANT_SEARCH,
                    response=response,
                    error=None
                )
                
                logger.info(f"Successfully found restaurants in {len(districts)} districts [correlation_id: {context.correlation_id}]")
                
                return RestaurantSearchResult(
                    restaurants=result_data.get('restaurants', []),
                    total_count=len(result_data.get('restaurants', [])),
                    search_metadata={
                        **result_data.get('metadata', {}),
                        'districts_searched': districts,
                        'agent_arn': self.search_agent_arn,
                        'operation': operation,
                        'correlation_id': context.correlation_id
                    },
                    execution_time_ms=execution_time_ms,
                    success=True
                )
            
            except AgentCoreError as e:
                # Handle AgentCore-specific errors with fallback
                execution_time_ms = int((time.time() - start_time) * 1000)
                self.error_count += 1
                
                # Log error invocation result
                self.monitoring_middleware.monitoring_service.log_agent_invocation_result(
                    correlation_id=context.correlation_id,
                    agent_arn=self.search_agent_arn,
                    operation_type=AgentOperationType.RESTAURANT_SEARCH,
                    response=None,
                    error=e
                )
                
                logger.error(f"AgentCore error in {operation}: {e} [correlation_id: {context.correlation_id}]")
                
                # Create fallback response
                fallback = self.runtime_client.create_fallback_response(
                    operation, self.search_agent_arn, user_id, session_id
                )
                
                return RestaurantSearchResult(
                    restaurants=[],
                    total_count=0,
                    search_metadata={
                        'districts_searched': districts,
                        'agent_arn': self.search_agent_arn,
                        'operation': operation,
                        'error_type': type(e).__name__,
                        'fallback_provided': True,
                        'correlation_id': context.correlation_id
                    },
                    execution_time_ms=execution_time_ms,
                    success=False,
                    error_message=fallback.get('message', str(e)),
                    fallback_data=fallback
                )
                
            except Exception as e:
                # Handle other errors
                execution_time_ms = int((time.time() - start_time) * 1000)
                self.error_count += 1
                
                # Log error invocation result
                self.monitoring_middleware.monitoring_service.log_agent_invocation_result(
                    correlation_id=context.correlation_id,
                    agent_arn=self.search_agent_arn,
                    operation_type=AgentOperationType.RESTAURANT_SEARCH,
                    response=None,
                    error=e
                )
                
                logger.error(f"Unexpected error in {operation}: {e} [correlation_id: {context.correlation_id}]")
                
                return RestaurantSearchResult(
                    restaurants=[],
                    total_count=0,
                    search_metadata={
                        'districts_searched': districts,
                        'agent_arn': self.search_agent_arn,
                        'operation': operation,
                        'error': str(e),
                        'correlation_id': context.correlation_id
                    },
                    execution_time_ms=execution_time_ms,
                    success=False,
                    error_message=str(e)
                )
    
    async def search_restaurants_by_meal_type(
        self, 
        meal_types: List[str]
    ) -> RestaurantSearchResult:
        """
        Search restaurants by meal type using AgentCore agent.
        
        Args:
            meal_types: List of meal types to search ("breakfast", "lunch", "dinner")
            
        Returns:
            RestaurantSearchResult object
        """
        start_time = time.time()
        operation = "search_restaurants_by_meal_type"
        
        try:
            # Validate input parameters
            if not meal_types:
                raise ValueError("Meal types list cannot be empty")
            
            if not isinstance(meal_types, list):
                raise ValueError("Meal types must be provided as a list")
            
            valid_meal_types = {"breakfast", "lunch", "dinner"}
            invalid_types = [mt for mt in meal_types if mt not in valid_meal_types]
            if invalid_types:
                raise ValueError(
                    f"Invalid meal types: {invalid_types}. "
                    f"Valid types are: {list(valid_meal_types)}"
                )
            
            # Prepare input for AgentCore agent
            search_request = {
                "action": "search_restaurants_by_meal_type",
                "parameters": {
                    "meal_types": meal_types
                }
            }
            
            input_text = json.dumps(search_request, ensure_ascii=False)
            
            logger.info(f"Searching restaurants for meal types: {meal_types}")
            
            # Invoke AgentCore agent
            response = await self.runtime_client.invoke_agent(
                agent_arn=self.search_agent_arn,
                input_text=input_text
            )
            
            # Parse response
            result_data = self._parse_agent_response(response)
            
            execution_time_ms = int((time.time() - start_time) * 1000)
            
            # Update performance metrics
            self.call_count += 1
            self.total_response_time += execution_time_ms
            
            logger.info(f"Successfully found restaurants for {len(meal_types)} meal types")
            
            return RestaurantSearchResult(
                restaurants=result_data.get('restaurants', []),
                total_count=len(result_data.get('restaurants', [])),
                search_metadata={
                    **result_data.get('metadata', {}),
                    'meal_types_searched': meal_types,
                    'agent_arn': self.search_agent_arn,
                    'operation': operation
                },
                execution_time_ms=execution_time_ms,
                success=True
            )
            
        except Exception as e:
            execution_time_ms = int((time.time() - start_time) * 1000)
            self.error_count += 1
            
            logger.error(f"Error in {operation}: {e}")
            
            return RestaurantSearchResult(
                restaurants=[],
                total_count=0,
                search_metadata={
                    'meal_types_searched': meal_types,
                    'agent_arn': self.search_agent_arn,
                    'operation': operation,
                    'error': str(e)
                },
                execution_time_ms=execution_time_ms,
                success=False,
                error_message=str(e)
            )
    
    async def search_restaurants_combined(
        self, 
        districts: Optional[List[str]] = None,
        meal_types: Optional[List[str]] = None
    ) -> RestaurantSearchResult:
        """
        Search restaurants using combined district and meal type filters.
        
        Args:
            districts: Optional list of district names to search
            meal_types: Optional list of meal types to search
            
        Returns:
            RestaurantSearchResult object
        """
        start_time = time.time()
        operation = "search_restaurants_combined"
        
        try:
            # Validate that at least one filter is provided
            if not districts and not meal_types:
                raise ValueError(
                    "At least one of 'districts' or 'meal_types' must be provided"
                )
            
            # Validate districts if provided
            if districts is not None:
                if not isinstance(districts, list):
                    raise ValueError("Districts must be provided as a list")
                
                if not districts:
                    raise ValueError("Districts list cannot be empty when provided")
                
                if not all(isinstance(d, str) and d.strip() for d in districts):
                    raise ValueError("All districts must be non-empty strings")
            
            # Validate meal types if provided
            if meal_types is not None:
                if not isinstance(meal_types, list):
                    raise ValueError("Meal types must be provided as a list")
                
                if not meal_types:
                    raise ValueError("Meal types list cannot be empty when provided")
                
                valid_meal_types = {"breakfast", "lunch", "dinner"}
                invalid_types = [mt for mt in meal_types if mt not in valid_meal_types]
                if invalid_types:
                    raise ValueError(
                        f"Invalid meal types: {invalid_types}. "
                        f"Valid types are: {list(valid_meal_types)}"
                    )
            
            # Prepare input for AgentCore agent
            search_request = {
                "action": "search_restaurants_combined",
                "parameters": {
                    "districts": districts,
                    "meal_types": meal_types
                }
            }
            
            input_text = json.dumps(search_request, ensure_ascii=False)
            
            logger.info(f"Combined search - Districts: {districts}, Meal types: {meal_types}")
            
            # Invoke AgentCore agent
            response = await self.runtime_client.invoke_agent(
                agent_arn=self.search_agent_arn,
                input_text=input_text
            )
            
            # Parse response
            result_data = self._parse_agent_response(response)
            
            execution_time_ms = int((time.time() - start_time) * 1000)
            
            # Update performance metrics
            self.call_count += 1
            self.total_response_time += execution_time_ms
            
            filter_count = (1 if districts else 0) + (1 if meal_types else 0)
            logger.info(f"Successfully performed combined search with {filter_count} filters")
            
            return RestaurantSearchResult(
                restaurants=result_data.get('restaurants', []),
                total_count=len(result_data.get('restaurants', [])),
                search_metadata={
                    **result_data.get('metadata', {}),
                    'districts_searched': districts,
                    'meal_types_searched': meal_types,
                    'agent_arn': self.search_agent_arn,
                    'operation': operation
                },
                execution_time_ms=execution_time_ms,
                success=True
            )
            
        except Exception as e:
            execution_time_ms = int((time.time() - start_time) * 1000)
            self.error_count += 1
            
            logger.error(f"Error in {operation}: {e}")
            
            return RestaurantSearchResult(
                restaurants=[],
                total_count=0,
                search_metadata={
                    'districts_searched': districts,
                    'meal_types_searched': meal_types,
                    'agent_arn': self.search_agent_arn,
                    'operation': operation,
                    'error': str(e)
                },
                execution_time_ms=execution_time_ms,
                success=False,
                error_message=str(e)
            )
    
    def _parse_agent_response(self, response: AgentResponse) -> Dict[str, Any]:
        """
        Parse AgentCore agent response.
        
        Args:
            response: AgentResponse from AgentCore
            
        Returns:
            Parsed response data
        """
        try:
            # Try to parse as JSON first
            if response.output_text.strip().startswith('{'):
                return json.loads(response.output_text)
            
            # If not JSON, try to extract JSON from text
            import re
            json_match = re.search(r'\{.*\}', response.output_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            
            # If no JSON found, create a structured response
            return {
                'restaurants': [],
                'metadata': {
                    'raw_response': response.output_text,
                    'session_id': response.session_id,
                    'agent_metadata': response.metadata
                }
            }
            
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse agent response as JSON: {e}")
            return {
                'restaurants': [],
                'metadata': {
                    'parse_error': str(e),
                    'raw_response': response.output_text,
                    'session_id': response.session_id,
                    'agent_metadata': response.metadata
                }
            }
        except Exception as e:
            logger.error(f"Unexpected error parsing agent response: {e}")
            return {
                'restaurants': [],
                'metadata': {
                    'error': str(e),
                    'raw_response': response.output_text,
                    'session_id': response.session_id,
                    'agent_metadata': response.metadata
                }
            }
    
    def _format_error_response(
        self, 
        error: Exception, 
        operation: str, 
        parameters: Dict[str, Any]
    ) -> str:
        """
        Format error responses for backward compatibility.
        
        Args:
            error: The exception that occurred
            operation: Name of the operation that failed
            parameters: Parameters that were passed to the operation
            
        Returns:
            JSON string with error information
        """
        error_response = {
            "success": False,
            "error": {
                "type": type(error).__name__,
                "message": str(error),
                "operation": operation,
                "parameters": parameters
            }
        }
        
        # Add specific error details based on error type
        if isinstance(error, AgentInvocationError):
            error_response["error"]["user_message"] = (
                "Restaurant search service is temporarily unavailable. "
                "Please try again later."
            )
            error_response["error"]["fallback"] = (
                "I can still help with general travel planning questions."
            )
        elif isinstance(error, AuthenticationError):
            error_response["error"]["user_message"] = (
                "Authentication issue with restaurant search service."
            )
            error_response["error"]["fallback"] = (
                "Please contact support if this issue persists."
            )
        elif isinstance(error, ValueError):
            error_response["error"]["user_message"] = (
                f"Invalid request parameters: {str(error)}"
            )
            error_response["error"]["fallback"] = (
                "Please check your request parameters and try again."
            )
        else:
            error_response["error"]["user_message"] = (
                "An unexpected error occurred while searching for restaurants."
            )
            error_response["error"]["fallback"] = (
                "Please try rephrasing your request or ask about other travel topics."
            )
        
        return json.dumps(error_response, ensure_ascii=False, indent=2)
    
    def _format_success_response(self, result: RestaurantSearchResult) -> str:
        """
        Format successful responses for backward compatibility.
        
        Args:
            result: The successful result from the search
            
        Returns:
            JSON string with formatted result
        """
        response = {
            "success": True,
            "restaurants": result.restaurants,
            "total_count": result.total_count,
            "metadata": result.search_metadata,
            "execution_time_ms": result.execution_time_ms
        }
        
        return json.dumps(response, ensure_ascii=False, indent=2)
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for the tool."""
        avg_response_time = (
            self.total_response_time / max(self.call_count, 1)
            if self.call_count > 0 else 0
        )
        
        metrics = {
            "total_calls": self.call_count,
            "total_errors": self.error_count,
            "error_rate": self.error_count / max(self.call_count, 1),
            "average_response_time_ms": avg_response_time,
            "agent_arn": self.search_agent_arn
        }
        
        # Update orchestration registry if available
        if self.tool_registry:
            self.tool_registry.update_tool_performance_metrics(self.tool_id, metrics)
        
        return metrics
    
    def _create_tool_metadata(self) -> 'ToolMetadata':
        """Create tool metadata for orchestration registration."""
        from .tool_registry import ToolMetadata, ToolCapability, ToolType, PerformanceCharacteristics, ResourceRequirements
        
        capabilities = [
            ToolCapability(
                name="search_by_district",
                description="Search restaurants by district/location",
                required_parameters=["districts"],
                optional_parameters=["meal_types"],
                use_cases=["location-based restaurant discovery", "district filtering"]
            ),
            ToolCapability(
                name="search_by_meal_type", 
                description="Search restaurants by meal type (breakfast, lunch, dinner)",
                required_parameters=["meal_types"],
                optional_parameters=["districts"],
                use_cases=["meal-specific restaurant search", "time-based filtering"]
            ),
            ToolCapability(
                name="combined_search",
                description="Search restaurants using combined district and meal type filters",
                required_parameters=[],
                optional_parameters=["districts", "meal_types"],
                use_cases=["multi-criteria search", "flexible filtering"]
            )
        ]
        
        performance_chars = PerformanceCharacteristics(
            average_response_time_ms=2000.0,
            success_rate=0.95,
            throughput_requests_per_minute=30,
            resource_requirements=ResourceRequirements(
                cpu_cores=0.5,
                memory_mb=256,
                network_bandwidth_mbps=5.0,
                storage_mb=50
            )
        )
        
        return ToolMetadata(
            id=self.tool_id,
            name="Restaurant Search Tool",
            description="Comprehensive restaurant search tool using AgentCore with district and meal type filtering",
            tool_type=ToolType.RESTAURANT_SEARCH,
            capabilities=capabilities,
            version="2.0.0",
            mcp_server_url=None,  # Direct AgentCore integration
            mcp_tool_name="restaurant_search",
            input_schema={
                "type": "object",
                "properties": {
                    "districts": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of district names to search"
                    },
                    "meal_types": {
                        "type": "array", 
                        "items": {"type": "string", "enum": ["breakfast", "lunch", "dinner"]},
                        "description": "List of meal types to filter by"
                    }
                }
            },
            output_schema={
                "type": "object",
                "properties": {
                    "restaurants": {
                        "type": "array",
                        "items": {"type": "object"},
                        "description": "List of matching restaurants"
                    },
                    "total_count": {
                        "type": "integer",
                        "description": "Total number of restaurants found"
                    },
                    "search_metadata": {
                        "type": "object",
                        "description": "Search execution metadata"
                    }
                }
            },
            performance_characteristics=performance_chars,
            health_check_endpoint=None,
            health_check_interval_seconds=60,
            tags={"restaurant", "search", "agentcore", "location", "meal_type"},
            category="restaurant_services"
        )
    
    def _register_with_orchestration(self) -> None:
        """Register this tool with the orchestration engine."""
        try:
            self.tool_registry.register_tool(self.tool_metadata, self)
            logger.info(f"Restaurant search tool registered with orchestration engine: {self.tool_id}")
        except Exception as e:
            logger.error(f"Failed to register restaurant search tool with orchestration: {e}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check for orchestration monitoring."""
        try:
            # Test basic connectivity with a minimal search
            test_result = await self.search_restaurants_by_district(
                districts=["Central district"],
                user_id="health_check",
                session_id="health_check"
            )
            
            return {
                "healthy": test_result.success,
                "response_time_ms": test_result.execution_time_ms,
                "error": test_result.error_message,
                "agent_arn": self.search_agent_arn,
                "last_check": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e),
                "agent_arn": self.search_agent_arn,
                "last_check": datetime.utcnow().isoformat()
            }
    
    # Backward compatibility methods that return JSON strings
    def search_restaurants_by_district_tool(self, districts: List[str]) -> str:
        """
        Search restaurants by district (backward compatible interface).
        
        Args:
            districts: List of district names to search
            
        Returns:
            JSON string containing restaurant data and metadata
        """
        try:
            # Execute async operation
            async def _search():
                return await self.search_restaurants_by_district(districts)
            
            result = asyncio.run(_search())
            
            if result.success:
                return self._format_success_response(result)
            else:
                return self._format_error_response(
                    Exception(result.error_message),
                    "search_restaurants_by_district",
                    {"districts": districts}
                )
                
        except Exception as e:
            return self._format_error_response(
                e,
                "search_restaurants_by_district",
                {"districts": districts}
            )
    
    def search_restaurants_combined_tool(
        self, 
        districts: Optional[List[str]] = None,
        meal_types: Optional[List[str]] = None
    ) -> str:
        """
        Search restaurants using combined filters (backward compatible interface).
        
        Args:
            districts: Optional list of district names to search
            meal_types: Optional list of meal types to search
            
        Returns:
            JSON string containing restaurant data matching the specified criteria
        """
        try:
            # Execute async operation
            async def _search():
                return await self.search_restaurants_combined(districts, meal_types)
            
            result = asyncio.run(_search())
            
            if result.success:
                return self._format_success_response(result)
            else:
                return self._format_error_response(
                    Exception(result.error_message),
                    "search_restaurants_combined",
                    {"districts": districts, "meal_types": meal_types}
                )
                
        except Exception as e:
            return self._format_error_response(
                e,
                "search_restaurants_combined",
                {"districts": districts, "meal_types": meal_types}
            )


def create_restaurant_search_tools(
    runtime_client: AgentCoreRuntimeClient,
    search_agent_arn: str,
    auth_manager: Optional[AuthenticationManager] = None
) -> List:
    """
    Create restaurant search tools using AgentCore Runtime API.
    
    This function creates Strands Agent tools that use the AgentCore Runtime client
    to communicate directly with the restaurant search agent.
    
    Args:
        runtime_client: AgentCore Runtime client
        search_agent_arn: ARN of the restaurant search agent
        auth_manager: Authentication manager (optional)
        
    Returns:
        List of tool functions for restaurant search functionality
    """
    try:
        # Initialize the restaurant search tool
        search_tool = RestaurantSearchTool(
            runtime_client=runtime_client,
            search_agent_arn=search_agent_arn,
            auth_manager=auth_manager
        )
        
        # Create tool functions using the @tool decorator
        @tool(
            name="search_restaurants_by_district",
            description="""Search for restaurants in specific Hong Kong districts using AgentCore Runtime API.
            
            This tool connects directly to the restaurant search agent deployed in Bedrock AgentCore
            and retrieves restaurant data filtered by district location. 
            
            Available districts include: Central district, Admiralty, Causeway Bay, Tsim Sha Tsui, 
            Wan Chai, Mong Kok, Sheung Wan, Tsuen Wan, Sha Tin, Tuen Mun, Yuen Long, Tai Po, 
            Fanling, Sheung Shui, Ma On Shan, Tseung Kwan O, Kwun Tong, Kowloon Bay, Ngau Tau Kok, 
            Kwai Chung, Tsing Yi, Tung Chung, Discovery Bay, and many others.
            
            The tool returns detailed restaurant information including:
            - Restaurant name, address, and contact details
            - Sentiment data (likes, dislikes, neutral ratings)
            - Price range and cuisine type
            - Operating hours and meal availability
            - District location and accessibility information
            """
        )
        def search_restaurants_by_district(districts: List[str]) -> str:
            """
            Search for restaurants in specific districts.
            
            Args:
                districts: List of district names to search
                
            Returns:
                JSON string containing restaurant data and metadata
            """
            return search_tool.search_restaurants_by_district_tool(districts)
        
        @tool(
            name="search_restaurants_combined",
            description="""Search for restaurants using combined district and meal type filters via AgentCore Runtime API.
            
            This tool provides flexible restaurant search capabilities by connecting directly to the 
            restaurant search agent and applying both location and timing filters. 
            Either or both parameters can be specified to narrow down search results.
            
            Meal type filtering is based on restaurant operating hours:
            - Breakfast: Restaurants open between 07:00-11:29
            - Lunch: Restaurants open between 11:30-17:29  
            - Dinner: Restaurants open between 17:30-22:30
            
            The tool returns comprehensive restaurant data including:
            - Restaurant details (name, address, contact information)
            - Sentiment analysis (customer satisfaction metrics)
            - Operating hours and meal service availability
            - Price range and cuisine categories
            - Location and accessibility details
            - Search metadata (total results, execution time, filters applied)
            
            Note: At least one of districts or meal_types must be provided.
            """
        )
        def search_restaurants_combined(
            districts: Optional[List[str]] = None,
            meal_types: Optional[List[str]] = None
        ) -> str:
            """
            Search for restaurants using combined district and meal type filters.
            
            Args:
                districts: Optional list of district names to filter by
                meal_types: Optional list of meal types to filter by 
                          (valid values: "breakfast", "lunch", "dinner")
                
            Returns:
                JSON string containing restaurant data matching the specified criteria
            """
            return search_tool.search_restaurants_combined_tool(districts, meal_types)
        
        tools = [search_restaurants_by_district, search_restaurants_combined]
        
        logger.info(f"Created {len(tools)} restaurant search tools using AgentCore Runtime API")
        return tools
        
    except Exception as e:
        logger.error(f"Failed to create restaurant search tools: {e}")
        return []


# Export main classes and functions
__all__ = [
    'RestaurantSearchTool',
    'RestaurantSearchResult',
    'create_restaurant_search_tools'
]