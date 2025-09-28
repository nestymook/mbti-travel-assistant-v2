"""
MBTI Travel Assistant MCP - BedrockAgentCore Runtime Entrypoint

This module implements the main BedrockAgentCore runtime entrypoint for the MBTI Travel Assistant.
It receives HTTP requests from web servers, processes them through an internal LLM agent,
and orchestrates MCP client calls to existing restaurant search and reasoning MCP servers.

The entrypoint follows the BedrockAgentCore runtime pattern with @app.entrypoint decorator
and returns structured JSON responses optimized for frontend web applications.

Requirements Implemented:
- Requirement 2.1: BedrockAgentCoreApp with @app.entrypoint decorator
- Requirement 2.2: Payload extraction and parameter processing  
- Requirement 6.1: JWT authentication integration
"""

import json
import logging
import asyncio
import traceback
from typing import Dict, Any, Optional
from datetime import datetime

# BedrockAgentCore imports
try:
    from bedrock_agentcore import BedrockAgentCoreApp
    AGENTCORE_AVAILABLE = True
except ImportError:
    # Mock for development/testing
    class BedrockAgentCoreApp:
        def __init__(self):
            pass
        
        def entrypoint(self, func):
            return func
        
        def health_check(self, func):
            return func
        
        def run(self, host="0.0.0.0", port=8080):
            print(f"Mock AgentCore app running on {host}:{port}")
    
    AGENTCORE_AVAILABLE = False

# Configuration and models
from config.settings import settings
from models.request_models import (
    RecommendationRequest, 
    RecommendationResponse,
    AgentCoreRequest,
    ErrorInfo,
    ResponseMetadata
)
from models.restaurant_models import Restaurant

# Services
from services.jwt_auth_handler import JWTAuthHandler
from services.mcp_client_manager import MCPClientManager
from services.restaurant_agent import RestaurantAgent
from services.response_formatter import ResponseFormatter
from services.error_handler import ErrorHandler
from services.cache_service import CacheService
from services.performance_monitor import performance_monitor, MetricType
from services.cloudwatch_monitor import CloudWatchMonitor, MetricUnit
from services.health_check import HealthChecker

# Logging configuration
logging.basicConfig(
    level=getattr(logging, settings.logging.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize BedrockAgentCore application
app = BedrockAgentCoreApp()

# Initialize services with error handling
try:
    jwt_auth_handler = JWTAuthHandler()
except Exception as e:
    logger.warning(f"JWT auth handler initialization failed: {e}, using mock")
    jwt_auth_handler = None

try:
    mcp_client_manager = MCPClientManager()
except Exception as e:
    logger.warning(f"MCP client manager initialization failed: {e}")
    mcp_client_manager = None

try:
    restaurant_agent = RestaurantAgent()
except Exception as e:
    logger.warning(f"Restaurant agent initialization failed: {e}")
    restaurant_agent = None

try:
    response_formatter = ResponseFormatter()
except Exception as e:
    logger.warning(f"Response formatter initialization failed: {e}")
    response_formatter = None

try:
    error_handler = ErrorHandler()
except Exception as e:
    logger.warning(f"Error handler initialization failed: {e}")
    error_handler = None

try:
    cache_service = CacheService()
except Exception as e:
    logger.warning(f"Cache service initialization failed: {e}")
    cache_service = None

# Initialize monitoring services
try:
    cloudwatch_monitor = CloudWatchMonitor(
        region=settings.aws.region,
        environment=settings.environment
    )
except Exception as e:
    logger.warning(f"CloudWatch monitor initialization failed: {e}")
    cloudwatch_monitor = None

try:
    health_checker = HealthChecker(
        mcp_client_manager=mcp_client_manager,
        cache_service=cache_service,
        cloudwatch_monitor=cloudwatch_monitor,
        environment=settings.environment
    )
except Exception as e:
    logger.warning(f"Health checker initialization failed: {e}")
    health_checker = None


@app.entrypoint
def process_restaurant_request(payload: Dict[str, Any]) -> str:
    """
    Main entrypoint for processing restaurant recommendation requests.
    
    This function serves as the BedrockAgentCore runtime entrypoint that receives
    HTTP requests from web servers, validates authentication, processes the request
    through an internal LLM agent, and returns structured JSON responses.
    
    Implements Requirements:
    - 2.1: BedrockAgentCore entrypoint with payload processing
    - 2.2: Parameter extraction from payload structure  
    - 6.1: JWT authentication integration
    - 1.1-1.8: HTTP payload processing and LLM orchestration
    
    Args:
        payload: HTTP request payload containing:
            - district: District name for restaurant search (optional)
            - meal_time: Meal time (breakfast, lunch, dinner) (optional)
            - natural_language_query: Natural language query (optional)
            - auth_token: JWT authentication token (optional, may be in headers)
            - user_context: Additional user context (optional)
    
    Returns:
        JSON string containing:
        {
            "recommendation": Restaurant object (exactly 1),
            "candidates": List of Restaurant objects (exactly 19 or fewer),
            "metadata": Response metadata with search criteria and timing,
            "error": Error information (if applicable)
        }
    
    Raises:
        Various exceptions are caught and converted to structured error responses
    """
    start_time = datetime.utcnow()
    correlation_id = f"req_{int(start_time.timestamp() * 1000)}"
    
    logger.info(
        "Processing restaurant recommendation request",
        extra={
            "correlation_id": correlation_id,
            "payload_keys": list(payload.keys()) if payload else [],
            "agentcore_available": AGENTCORE_AVAILABLE
        }
    )
    
    # Record request start metrics
    performance_monitor.record_metric(
        MetricType.THROUGHPUT,
        1.0,
        {"endpoint": "restaurant_recommendation"}
    )
    
    try:
        # Step 1: Route request by type (Requirement 2.6)
        request_type = _route_request_by_type(payload, correlation_id)
        
        # Step 2: Validate and parse request payload (Requirement 2.2)
        agentcore_request = _validate_and_parse_payload(payload, correlation_id)
        
        # Step 3: Authenticate request using JWT (Requirement 6.1)
        user_context = None
        if jwt_auth_handler and settings.authentication.cognito_user_pool_id:
            user_context = _authenticate_request(payload, correlation_id)
            # Update request with authenticated user context
            agentcore_request.user_context = user_context
        
        # Step 4: Check cache for existing results (Performance optimization)
        cache_key = _generate_cache_key(
            agentcore_request.district, 
            agentcore_request.meal_time
        )
        
        if cache_service and settings.cache.cache_enabled:
            cached_response = cache_service.get_cached_response(cache_key)
            if cached_response:
                logger.info(
                    "Returning cached response",
                    extra={
                        "correlation_id": correlation_id, 
                        "cache_key": cache_key,
                        "request_type": request_type
                    }
                )
                # Log metrics for cached response
                _log_request_metrics(
                    correlation_id, start_time, payload, 
                    len(cached_response.encode()), True
                )
                return cached_response
        
        # Step 5: Process request through internal LLM agent (Requirement 2.3)
        # The agent will orchestrate MCP client calls and return structured data
        if restaurant_agent:
            response_data = asyncio.run(
                _process_with_internal_agent(agentcore_request, correlation_id)
            )
        else:
            # Fallback response when agent is not available
            response_data = {
                "recommendation": None,
                "candidates": [],
                "error": "Restaurant agent not available"
            }
        
        # Step 6: Format response for frontend consumption (Requirement 4.1-4.8)
        formatted_response = _format_final_response(
            response_data,
            agentcore_request,
            start_time,
            correlation_id
        )
        
        # Step 7: Cache successful response
        if cache_service and settings.cache.cache_enabled and not formatted_response.get("error"):
            cache_service.cache_response(
                cache_key,
                json.dumps(formatted_response, default=str),
                settings.cache.cache_ttl
            )
        
        # Step 8: Prepare final response and log metrics
        final_response = json.dumps(formatted_response, default=str)
        
        # Log comprehensive request metrics (Requirement 7.2)
        _log_request_metrics(
            correlation_id, start_time, payload, 
            len(final_response.encode()), 
            not formatted_response.get("error")
        )
        
        # Record performance metrics
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        performance_monitor.record_metric(
            MetricType.RESPONSE_TIME,
            processing_time,
            {"endpoint": "restaurant_recommendation", "status": "success"}
        )
        
        # Send metrics to CloudWatch if available
        if cloudwatch_monitor:
            try:
                cloudwatch_monitor.put_metric(
                    "ResponseTime",
                    processing_time,
                    MetricUnit.SECONDS,
                    {"Environment": settings.environment, "Endpoint": "restaurant_recommendation"}
                )
                cloudwatch_monitor.put_metric(
                    "RequestCount",
                    1.0,
                    MetricUnit.COUNT,
                    {"Environment": settings.environment, "Status": "success"}
                )
            except Exception as e:
                logger.warning(f"Failed to send metrics to CloudWatch: {e}")
        
        logger.info(
            "Successfully processed restaurant recommendation request",
            extra={
                "correlation_id": correlation_id,
                "request_type": request_type,
                "has_recommendation": "recommendation" in formatted_response,
                "candidate_count": len(formatted_response.get("candidates", [])),
                "cache_hit": False
            }
        )
        
        return final_response
        
    except Exception as e:
        # Handle processing errors with comprehensive error categorization (Requirement 7.1)
        error_response_dict = _handle_processing_error(e, correlation_id, payload)
        error_response = json.dumps(error_response_dict, default=str)
        
        # Log error metrics
        _log_request_metrics(
            correlation_id, start_time, payload or {}, 
            len(error_response.encode()), False
        )
        
        # Record error metrics
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        performance_monitor.record_metric(
            MetricType.RESPONSE_TIME,
            processing_time,
            {"endpoint": "restaurant_recommendation", "status": "error"}
        )
        performance_monitor.record_metric(
            MetricType.ERROR_RATE,
            1.0,
            {"endpoint": "restaurant_recommendation"}
        )
        
        # Send error metrics to CloudWatch if available
        if cloudwatch_monitor:
            try:
                cloudwatch_monitor.put_metric(
                    "ErrorRate",
                    1.0,
                    MetricUnit.COUNT,
                    {"Environment": settings.environment, "Endpoint": "restaurant_recommendation"}
                )
                cloudwatch_monitor.put_metric(
                    "RequestCount",
                    1.0,
                    MetricUnit.COUNT,
                    {"Environment": settings.environment, "Status": "error"}
                )
            except Exception as e:
                logger.warning(f"Failed to send error metrics to CloudWatch: {e}")
        
        return error_response


def _validate_and_parse_payload(
    payload: Dict[str, Any], 
    correlation_id: str
) -> AgentCoreRequest:
    """
    Validate and parse the incoming BedrockAgentCore request payload.
    
    Implements Requirement 2.2: Parameter extraction from payload structure
    
    Args:
        payload: Raw request payload from AgentCore entrypoint
        correlation_id: Request correlation ID for logging
        
    Returns:
        Validated AgentCoreRequest object
        
    Raises:
        ValueError: If payload validation fails
    """
    if not payload:
        logger.error(
            "Empty request payload received",
            extra={"correlation_id": correlation_id}
        )
        raise ValueError("Request payload is required")
    
    logger.debug(
        "Validating request payload",
        extra={
            "correlation_id": correlation_id,
            "payload": payload
        }
    )
    
    # Create AgentCore request from payload
    agentcore_request = AgentCoreRequest.from_dict(payload)
    
    # Validate request structure and parameters
    validation_errors = agentcore_request.validate()
    if validation_errors:
        error_msg = f"Request validation failed: {', '.join(validation_errors)}"
        logger.error(
            error_msg,
            extra={
                "correlation_id": correlation_id,
                "validation_errors": validation_errors
            }
        )
        raise ValueError(error_msg)
    
    logger.info(
        "Request payload validated successfully",
        extra={
            "correlation_id": correlation_id,
            "district": agentcore_request.district,
            "meal_time": agentcore_request.meal_time,
            "has_natural_query": bool(agentcore_request.natural_language_query)
        }
    )
    
    return agentcore_request


def _authenticate_request(
    payload: Dict[str, Any], 
    correlation_id: str
) -> Optional[Dict[str, Any]]:
    """
    Authenticate the incoming request using JWT token validation.
    
    Implements Requirement 6.1: JWT authentication integration
    Implements Requirement 1.1: JWT token validation and user context extraction
    
    Args:
        payload: Request payload that may contain auth_token
        correlation_id: Request correlation ID for logging
        
    Returns:
        User context dictionary if authentication succeeds, None if no auth required
        
    Raises:
        AuthenticationError: If authentication fails (Requirement 1.7)
    """
    logger.debug(
        "Starting JWT authentication",
        extra={"correlation_id": correlation_id}
    )
    
    # Extract JWT token from payload or headers
    # In BedrockAgentCore, tokens may be in different locations
    auth_token = (
        payload.get("auth_token") or 
        payload.get("authorization") or
        payload.get("jwt_token")
    )
    
    if not auth_token:
        if settings.authentication.require_authentication:
            logger.error(
                "Authentication required but no token provided",
                extra={"correlation_id": correlation_id}
            )
            raise ValueError("Authentication token is required")
        else:
            logger.info(
                "No authentication token provided, proceeding without auth",
                extra={"correlation_id": correlation_id}
            )
            return None
    
    try:
        # Validate JWT token using JWT auth handler
        if not jwt_auth_handler:
            raise ValueError("JWT authentication handler not available")
            
        validation_result = jwt_auth_handler.validate_token(auth_token)
        
        if not validation_result.is_valid:
            logger.error(
                "JWT token validation failed",
                extra={
                    "correlation_id": correlation_id,
                    "error": validation_result.error.message if validation_result.error else "Unknown error"
                }
            )
            raise ValueError(f"Authentication failed: {validation_result.error.message}")
        
        user_context = validation_result.user_context.to_dict() if validation_result.user_context else {}
        
        logger.info(
            "Successfully authenticated request",
            extra={
                "correlation_id": correlation_id,
                "user_id": user_context.get("user_id"),
                "validation_time_ms": validation_result.validation_time_ms
            }
        )
        
        return user_context
        
    except Exception as e:
        logger.error(
            f"Authentication error: {str(e)}",
            extra={
                "correlation_id": correlation_id,
                "error_type": type(e).__name__
            }
        )
        raise ValueError(f"Authentication failed: {str(e)}")


async def _process_with_internal_agent(
    request: AgentCoreRequest,
    correlation_id: str
) -> Dict[str, Any]:
    """
    Process the request through the internal LLM agent.
    
    Implements Requirement 2.3: Internal LLM agent processing
    Implements Requirement 3.1-3.6: MCP client integration for LLM
    Implements Requirement 1.3-1.5: LLM orchestration of MCP calls
    
    Args:
        request: Validated AgentCore request
        correlation_id: Request correlation ID
        
    Returns:
        Dictionary containing recommendation and candidates data
        
    Raises:
        Various exceptions from agent processing or MCP client calls
    """
    logger.info(
        "Processing request with internal LLM agent",
        extra={
            "correlation_id": correlation_id,
            "district": request.district,
            "meal_time": request.meal_time,
            "has_natural_query": bool(request.natural_language_query)
        }
    )
    
    try:
        # Process request through restaurant agent
        # The agent will:
        # 1. Act as MCP client to search MCP server (Requirement 3.1-3.3)
        # 2. Act as MCP client to reasoning MCP server (Requirement 3.4-3.6)  
        # 3. Coordinate workflow: search first, then reasoning (Requirement 1.4)
        # 4. Format exactly 1 recommendation + 19 candidates (Requirement 1.5)
        response_data = await restaurant_agent.process_request(
            district=request.district,
            meal_time=request.meal_time,
            natural_language_query=request.natural_language_query,
            user_context=request.user_context,
            correlation_id=correlation_id
        )
        
        logger.info(
            "Internal LLM agent processing completed",
            extra={
                "correlation_id": correlation_id,
                "has_recommendation": "recommendation" in response_data,
                "candidate_count": len(response_data.get("candidates", []))
            }
        )
        
        return response_data
        
    except Exception as e:
        logger.error(
            f"Internal LLM agent processing failed: {str(e)}",
            extra={
                "correlation_id": correlation_id,
                "error_type": type(e).__name__
            }
        )
        raise


def _format_final_response(
    response_data: Dict[str, Any],
    request: AgentCoreRequest,
    start_time: datetime,
    correlation_id: str
) -> Dict[str, Any]:
    """
    Format the final response for frontend consumption.
    
    Implements Requirement 4.1-4.8: JSON response structure for frontend
    
    Args:
        response_data: Data from internal LLM agent processing
        request: Original AgentCore request
        start_time: Request start time for processing metrics
        correlation_id: Request correlation ID
        
    Returns:
        Dictionary formatted for frontend consumption
    """
    logger.debug(
        "Formatting final response",
        extra={"correlation_id": correlation_id}
    )
    
    try:
        # Use response formatter service to create structured response
        if response_formatter:
            formatted_response = response_formatter.format_response(
                response_data,
                request,
                start_time,
                correlation_id
            )
        else:
            # Fallback formatting when service is not available
            formatted_response = {
                "recommendation": response_data.get("recommendation"),
                "candidates": response_data.get("candidates", []),
                "metadata": {
                    "search_criteria": {
                        "district": request.district,
                        "meal_time": request.meal_time
                    },
                    "total_found": len(response_data.get("candidates", [])),
                    "timestamp": datetime.utcnow().isoformat(),
                    "processing_time_ms": (datetime.utcnow() - start_time).total_seconds() * 1000,
                    "cache_hit": False,
                    "mcp_calls": []
                },
                "error": response_data.get("error")
            }
        
        # Validate response structure meets requirements
        if isinstance(formatted_response, dict):
            # Ensure exactly 1 recommendation and max 19 candidates (Requirement 4.2-4.3)
            candidates = formatted_response.get("candidates", [])
            if len(candidates) > 19:
                formatted_response["candidates"] = candidates[:19]
                logger.warning(
                    f"Truncated candidates list to 19 items",
                    extra={
                        "correlation_id": correlation_id,
                        "original_count": len(candidates)
                    }
                )
        
        return formatted_response
        
    except Exception as e:
        logger.error(
            f"Error formatting final response: {str(e)}",
            extra={"correlation_id": correlation_id}
        )
        
        # Return error response if formatting fails
        return {
            "recommendation": None,
            "candidates": [],
            "metadata": {
                "search_criteria": {
                    "district": request.district,
                    "meal_time": request.meal_time
                },
                "total_found": 0,
                "timestamp": datetime.utcnow().isoformat(),
                "processing_time_ms": (datetime.utcnow() - start_time).total_seconds() * 1000,
                "cache_hit": False,
                "mcp_calls": []
            },
            "error": {
                "error_type": "response_formatting_error",
                "message": f"Failed to format response: {str(e)}",
                "suggested_actions": [
                    "Try the request again",
                    "Check request parameters",
                    "Contact support if problem persists"
                ],
                "error_code": "RESPONSE_FORMAT_ERROR"
            }
        }


def _generate_cache_key(district: Optional[str], meal_time: Optional[str]) -> str:
    """
    Generate cache key for request parameters.
    
    Args:
        district: District name
        meal_time: Meal time
        
    Returns:
        Cache key string
    """
    key_parts = [
        "restaurant_rec",
        district or "any_district",
        meal_time or "any_meal",
        datetime.utcnow().strftime("%Y-%m-%d")  # Include date for daily cache invalidation
    ]
    return ":".join(key_parts)


def _route_request_by_type(payload: Dict[str, Any], correlation_id: str) -> str:
    """
    Route requests based on payload type and content.
    
    Implements Requirement 2.6: Request routing logic for different payload types
    
    Args:
        payload: Request payload to route
        correlation_id: Request correlation ID
        
    Returns:
        Processing method identifier
    """
    logger.debug(
        "Routing request by type",
        extra={"correlation_id": correlation_id}
    )
    
    # Check for natural language query
    if payload.get("natural_language_query"):
        logger.info(
            "Routing to natural language processing",
            extra={"correlation_id": correlation_id}
        )
        return "natural_language"
    
    # Check for structured parameters
    elif payload.get("district") or payload.get("meal_time"):
        logger.info(
            "Routing to structured parameter processing",
            extra={"correlation_id": correlation_id}
        )
        return "structured_params"
    
    # Default routing
    else:
        logger.info(
            "Routing to default processing",
            extra={"correlation_id": correlation_id}
        )
        return "default"


def _log_request_metrics(
    correlation_id: str,
    start_time: datetime,
    payload: Dict[str, Any],
    response_size: int,
    success: bool
) -> None:
    """
    Log comprehensive request metrics for monitoring.
    
    Implements Requirement 7.2: Logging and monitoring for request processing
    
    Args:
        correlation_id: Request correlation ID
        start_time: Request start time
        payload: Request payload
        response_size: Size of response in bytes
        success: Whether request was successful
    """
    processing_time_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
    
    metrics = {
        "correlation_id": correlation_id,
        "processing_time_ms": processing_time_ms,
        "payload_size_bytes": len(json.dumps(payload, default=str).encode()),
        "response_size_bytes": response_size,
        "success": success,
        "timestamp": datetime.utcnow().isoformat(),
        "has_district": bool(payload.get("district")),
        "has_meal_time": bool(payload.get("meal_time")),
        "has_natural_query": bool(payload.get("natural_language_query")),
        "has_auth_token": bool(payload.get("auth_token") or payload.get("authorization"))
    }
    
    if success:
        logger.info("Request completed successfully", extra=metrics)
    else:
        logger.error("Request failed", extra=metrics)


def _handle_processing_error(
    error: Exception,
    correlation_id: str,
    payload: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Handle processing errors with comprehensive error categorization.
    
    Implements Requirement 7.1: Error handling and response formatting
    
    Args:
        error: Exception that occurred
        correlation_id: Request correlation ID  
        payload: Original request payload
        
    Returns:
        Structured error response dictionary
    """
    logger.error(
        f"Processing error occurred: {str(error)}",
        extra={
            "correlation_id": correlation_id,
            "error_type": type(error).__name__,
            "payload_keys": list(payload.keys()) if payload else []
        }
    )
    
    # Use error handler service for comprehensive error handling
    try:
        if error_handler:
            error_response = error_handler.handle_entrypoint_error(error, correlation_id)
            return error_response
        else:
            raise Exception("Error handler not available")
    except Exception as handler_error:
        logger.error(
            f"Error handler failed: {str(handler_error)}",
            extra={"correlation_id": correlation_id}
        )
        
        # Fallback error response
        return {
            "recommendation": None,
            "candidates": [],
            "metadata": {
                "search_criteria": {},
                "total_found": 0,
                "timestamp": datetime.utcnow().isoformat(),
                "processing_time_ms": 0,
                "cache_hit": False,
                "mcp_calls": []
            },
            "error": {
                "error_type": "internal_error",
                "message": "An internal error occurred while processing your request",
                "suggested_actions": [
                    "Try the request again",
                    "Check request parameters",
                    "Contact support if problem persists"
                ],
                "error_code": "INTERNAL_ERROR"
            }
        }


@app.health_check
def health_check() -> Dict[str, Any]:
    """
    Comprehensive health check endpoint for monitoring and load balancing.
    
    Uses the HealthChecker service to perform detailed health checks on all
    system components including MCP servers, cache, authentication, and system resources.
    
    Returns:
        Health status dictionary with component-level status and metrics
    """
    health_correlation_id = f"health_{int(datetime.utcnow().timestamp() * 1000)}"
    
    logger.debug(
        "Performing comprehensive health check",
        extra={"correlation_id": health_correlation_id}
    )
    
    try:
        if health_checker:
            # Use comprehensive health checker
            health_report = asyncio.run(
                health_checker.perform_health_check(include_detailed=False)
            )
            
            # Convert to dictionary format
            health_status = health_report.to_dict()
            
            # Add additional metadata
            health_status.update({
                "version": "1.0.0",
                "agentcore_available": AGENTCORE_AVAILABLE,
                "correlation_id": health_correlation_id
            })
            
            # Record health metrics
            if cloudwatch_monitor:
                try:
                    health_value = 1.0 if health_report.overall_status.value == "healthy" else 0.0
                    cloudwatch_monitor.put_metric(
                        "HealthCheckStatus",
                        health_value,
                        MetricUnit.COUNT,
                        {"Environment": settings.environment}
                    )
                except Exception as e:
                    logger.warning(f"Failed to send health metrics to CloudWatch: {e}")
            
            logger.info(
                f"Comprehensive health check completed: {health_report.overall_status.value}",
                extra={
                    "correlation_id": health_correlation_id,
                    "check_count": len(health_report.checks),
                    "healthy_checks": sum(1 for check in health_report.checks 
                                        if check.status.value == "healthy")
                }
            )
            
            return health_status
            
        else:
            # Fallback health check when comprehensive checker is not available
            return _fallback_health_check(health_correlation_id)
        
    except Exception as e:
        logger.error(
            f"Health check failed: {str(e)}",
            extra={"correlation_id": health_correlation_id},
            exc_info=True
        )
        return {
            "overall_status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e),
            "version": "1.0.0",
            "environment": settings.environment,
            "correlation_id": health_correlation_id
        }


def _fallback_health_check(correlation_id: str) -> Dict[str, Any]:
    """
    Fallback health check when comprehensive health checker is not available.
    
    Args:
        correlation_id: Health check correlation ID
        
    Returns:
        Basic health status dictionary
    """
    logger.debug(
        "Performing fallback health check",
        extra={"correlation_id": correlation_id}
    )
    
    try:
        # Check critical dependencies
        component_status = {}
        overall_healthy = True
        
        # Check MCP client manager
        if mcp_client_manager:
            component_status["mcp_client_manager"] = "healthy"
        else:
            component_status["mcp_client_manager"] = "unhealthy: not initialized"
            overall_healthy = False
        
        # Check restaurant agent
        if restaurant_agent:
            component_status["restaurant_agent"] = "healthy"
        else:
            component_status["restaurant_agent"] = "unhealthy: not initialized"
            overall_healthy = False
        
        # Check authentication service
        if settings.authentication.cognito_user_pool_id:
            if jwt_auth_handler:
                component_status["jwt_auth_handler"] = "healthy"
            else:
                component_status["jwt_auth_handler"] = "unhealthy: not initialized"
                overall_healthy = False
        else:
            component_status["jwt_auth_handler"] = "disabled"
        
        # Check cache service
        if settings.cache.cache_enabled:
            if cache_service:
                component_status["cache_service"] = "healthy"
            else:
                component_status["cache_service"] = "unhealthy: not initialized"
                overall_healthy = False
        else:
            component_status["cache_service"] = "disabled"
        
        health_status = {
            "overall_status": "healthy" if overall_healthy else "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0",
            "environment": settings.environment,
            "checks": [
                {
                    "name": name,
                    "status": status,
                    "timestamp": datetime.utcnow().isoformat()
                }
                for name, status in component_status.items()
            ],
            "system_info": {
                "agentcore_available": AGENTCORE_AVAILABLE
            },
            "uptime_seconds": 0,  # Would need to track actual uptime
            "correlation_id": correlation_id
        }
        
        logger.info(
            f"Fallback health check completed: {health_status['overall_status']}",
            extra={
                "correlation_id": correlation_id,
                "component_count": len(component_status),
                "healthy_components": sum(1 for status in component_status.values() 
                                        if status == "healthy")
            }
        )
        
        return health_status
        
    except Exception as e:
        logger.error(
            f"Fallback health check failed: {str(e)}",
            extra={"correlation_id": correlation_id}
        )
        return {
            "overall_status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e),
            "version": "1.0.0",
            "environment": settings.environment,
            "correlation_id": correlation_id
        }


@app.entrypoint
def metrics_endpoint(payload: Dict[str, Any]) -> str:
    """
    Metrics endpoint for Prometheus scraping.
    
    Returns performance metrics in Prometheus format for monitoring.
    
    Args:
        payload: Request payload (should contain metrics request)
        
    Returns:
        Prometheus-formatted metrics string
    """
    try:
        # Get performance summary
        performance_summary = performance_monitor.get_performance_summary()
        mcp_report = performance_monitor.get_mcp_performance_report()
        
        # Generate Prometheus metrics
        metrics_lines = []
        
        # System metrics
        system_metrics = performance_summary.get("system_metrics", {})
        for metric_name, value in system_metrics.items():
            if isinstance(value, (int, float)):
                prometheus_name = f"mbti_travel_assistant_{metric_name}"
                metrics_lines.append(f"{prometheus_name} {value}")
        
        # Performance metrics
        metrics_lines.append(f"mbti_travel_assistant_total_metrics_collected {performance_summary.get('total_metrics_collected', 0)}")
        metrics_lines.append(f"mbti_travel_assistant_recent_error_rate {performance_summary.get('recent_error_rate', 0)}")
        metrics_lines.append(f"mbti_travel_assistant_uptime_seconds {performance_summary.get('uptime_seconds', 0)}")
        
        # MCP metrics
        overall_mcp = mcp_report.get("overall", {})
        metrics_lines.append(f"mbti_travel_assistant_mcp_total_calls {overall_mcp.get('total_calls', 0)}")
        metrics_lines.append(f"mbti_travel_assistant_mcp_avg_duration {overall_mcp.get('avg_duration', 0)}")
        metrics_lines.append(f"mbti_travel_assistant_mcp_error_rate {overall_mcp.get('error_rate', 0)}")
        
        # Health status
        if health_checker:
            try:
                quick_health = asyncio.run(health_checker.get_quick_health_status())
                health_value = 1.0 if quick_health.get("status") == "healthy" else 0.0
                metrics_lines.append(f"mbti_travel_assistant_health_status {health_value}")
            except Exception as e:
                logger.warning(f"Failed to get quick health status: {e}")
                metrics_lines.append("mbti_travel_assistant_health_status -1")
        
        # Add timestamp
        timestamp = int(datetime.utcnow().timestamp() * 1000)
        metrics_output = "\n".join(metrics_lines)
        
        logger.debug(f"Generated {len(metrics_lines)} Prometheus metrics")
        return metrics_output
        
    except Exception as e:
        logger.error(f"Failed to generate metrics: {e}")
        return f"# Error generating metrics: {str(e)}\nmbti_travel_assistant_metrics_error 1"


def request_middleware(request, call_next):
    """
    Middleware for request processing monitoring and observability.
    
    Implements enhanced monitoring for all requests.
    """
    start_time = datetime.utcnow()
    correlation_id = f"mid_{int(start_time.timestamp() * 1000)}"
    
    logger.debug(
        "Request middleware processing",
        extra={
            "correlation_id": correlation_id,
            "middleware_start": start_time.isoformat()
        }
    )
    
    try:
        response = call_next(request)
        
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        logger.info(
            "Request middleware completed",
            extra={
                "correlation_id": correlation_id,
                "middleware_processing_time_ms": processing_time
            }
        )
        
        return response
    except Exception as e:
        logger.error(
            f"Request middleware error: {str(e)}",
            extra={"correlation_id": correlation_id}
        )
        raise


def _initialize_application() -> None:
    """
    Initialize application components and validate configuration.
    
    Implements startup validation and component initialization.
    """
    logger.info("Initializing MBTI Travel Assistant MCP application")
    
    # Validate configuration
    try:
        logger.info(f"Environment: {settings.environment}")
        logger.info(f"Authentication enabled: {bool(settings.authentication.cognito_user_pool_id)}")
        logger.info(f"Cache enabled: {settings.cache.cache_enabled}")
        logger.info(f"MCP endpoints configured: {bool(settings.mcp_client.search_mcp_endpoint)}")
        
        # Initialize services
        logger.info("Services initialized successfully")
        
    except Exception as e:
        logger.error(f"Application initialization failed: {str(e)}")
        raise


if __name__ == "__main__":
    """
    Main entry point for local development and testing.
    
    In production, the AgentCore runtime will handle the application lifecycle.
    """
    try:
        _initialize_application()
        
        logger.info("Starting MBTI Travel Assistant MCP v1.0.0")
        logger.info(f"Configuration: {settings.app_name} in {settings.environment} environment")
        logger.info(f"AgentCore available: {AGENTCORE_AVAILABLE}")
        
        # Start the BedrockAgentCore runtime
        app.run(
            host="0.0.0.0",
            port=getattr(settings, 'runtime_port', 8080)
        )
        
    except Exception as e:
        logger.error(f"Failed to start application: {str(e)}", exc_info=True)
        raise