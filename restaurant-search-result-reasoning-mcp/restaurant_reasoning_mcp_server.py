"""Restaurant Reasoning MCP Server with Authentication and Status Monitoring.

This module implements a FastMCP server that provides restaurant sentiment analysis
and recommendation tools for foundation models. It exposes MCP tools for analyzing
restaurant sentiment data and generating intelligent recommendations based on
customer satisfaction metrics.

The server follows Bedrock AgentCore patterns with stateless HTTP transport,
JWT authentication via Cognito, status monitoring system, and proper error handling 
for MCP tool integration.
"""

import json
import logging
import os
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional

from mcp.server.fastmcp import FastMCP
from fastapi import Request, Response
from fastapi.responses import JSONResponse

from services.restaurant_reasoning_service import RestaurantReasoningService
from services.auth_middleware import AuthenticationMiddleware, AuthenticationConfig, AuthenticationHelper
from models.restaurant_models import Restaurant, Sentiment, RecommendationResult, SentimentAnalysis
from models.validation_models import ValidationResult, ValidationError

# Status check system imports
from services.circuit_breaker import get_reasoning_status_manager
from services.status_config_loader import get_config_loader
from services.health_check_service import HealthCheckService
from api.status_endpoints import create_reasoning_status_endpoints


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Load Cognito configuration for authentication
def load_cognito_config() -> Dict[str, Any]:
    """Load Cognito configuration from file."""
    try:
        config_path = os.path.join(os.path.dirname(__file__), 'cognito_config.json')
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        return {
            'user_pool_id': config['user_pool']['user_pool_id'],
            'client_id': config['app_client']['client_id'],
            'region': config['region'],
            'discovery_url': config['discovery_url']
        }
    except Exception as e:
        logger.error(f"Failed to load Cognito configuration: {e}")
        # Return default config for development
        return {
            'user_pool_id': 'us-east-1_wBAxW7yd4',
            'client_id': '26k0pnja579pdpb1pt6savs27e',
            'region': 'us-east-1',
            'discovery_url': 'https://cognito-idp.us-east-1.amazonaws.com/us-east-1_wBAxW7yd4/.well-known/openid-configuration'
        }

# Create FastMCP server with AgentCore Runtime compatibility
mcp = FastMCP("restaurant-reasoning-mcp")

# Load authentication configuration
cognito_config = load_cognito_config()

# Configure authentication middleware with bypass for health check and status endpoints
auth_config = AuthenticationConfig(
    cognito_config=cognito_config,
    bypass_paths=['/health', '/metrics', '/docs', '/openapi.json', '/', '/status/*'],
    require_authentication=True,
    log_user_context=True
)

# Note: Authentication middleware will be configured during server startup
# FastMCP handles middleware differently than direct FastAPI apps

# Initialize restaurant reasoning service
reasoning_service = RestaurantReasoningService(
    minimum_responses=1,
    default_candidate_count=20,
    random_seed=None,  # Use random seed for production
    strict_validation=False
)

# Initialize status check system components
status_manager = get_reasoning_status_manager()
config_loader = get_config_loader()
health_service = None  # Will be initialized during startup

# Background task for continuous health checks
health_check_task = None
health_check_stop_event = asyncio.Event()


def validate_restaurant_list_parameter(restaurants: Any) -> tuple[bool, str]:
    """
    Validate that the restaurants parameter is a proper list of dictionaries.
    
    Args:
        restaurants: Parameter to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(restaurants, list):
        return False, f"Restaurants parameter must be a list, got {type(restaurants).__name__}"
    
    if not restaurants:
        return False, "Restaurants list cannot be empty"
    
    for i, restaurant in enumerate(restaurants):
        if not isinstance(restaurant, dict):
            return False, f"Restaurant at index {i} must be a dictionary, got {type(restaurant).__name__}"
    
    return True, ""


def validate_ranking_method_parameter(ranking_method: str) -> tuple[bool, str]:
    """
    Validate that the ranking method parameter is valid.
    
    Args:
        ranking_method: Ranking method to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    valid_methods = ["sentiment_likes", "combined_sentiment"]
    
    if not isinstance(ranking_method, str):
        return False, f"Ranking method must be a string, got {type(ranking_method).__name__}"
    
    if ranking_method not in valid_methods:
        return False, f"Invalid ranking method '{ranking_method}'. Valid methods: {valid_methods}"
    
    return True, ""


def format_error_response(
    error_message: str, 
    error_type: str = "ValidationError",
    details: Optional[Dict[str, Any]] = None
) -> str:
    """
    Format error response for MCP tools.
    
    Args:
        error_message: Error message to include
        error_type: Type of error
        details: Optional additional error details
        
    Returns:
        JSON string containing formatted error response
    """
    response = {
        'success': False,
        'error': {
            'type': error_type,
            'message': error_message,
            'timestamp': datetime.utcnow().isoformat() + "Z"
        }
    }
    
    if details:
        response['error']['details'] = details
        
    return json.dumps(response, indent=2)


def log_mcp_tool_invocation(tool_name: str, parameters: Dict[str, Any], user_context: Optional[Any] = None) -> None:
    """
    Log MCP tool invocation for audit purposes with user context.
    
    Args:
        tool_name: Name of the MCP tool being invoked
        parameters: Parameters passed to the tool (sensitive data removed)
        user_context: Authenticated user context for audit logging
    """
    try:
        # Create sanitized parameters for logging (remove sensitive data)
        sanitized_params = parameters.copy()
        
        # Log restaurant count instead of full data
        if 'restaurants' in sanitized_params:
            restaurant_count = len(sanitized_params['restaurants']) if isinstance(sanitized_params['restaurants'], list) else 0
            sanitized_params['restaurants'] = f"<{restaurant_count} restaurants>"
        
        # Add user context for audit logging
        audit_info = {
            'tool_name': tool_name,
            'parameters': sanitized_params,
            'timestamp': datetime.utcnow().isoformat() + "Z",
            'server_type': 'reasoning_mcp'
        }
        
        if user_context:
            audit_info['user_context'] = {
                'user_id': getattr(user_context, 'user_id', 'unknown'),
                'username': getattr(user_context, 'username', 'unknown'),
                'email': getattr(user_context, 'email', 'unknown')
            }
        
        logger.info(f"MCP tool invocation for reasoning operations: {json.dumps(audit_info)}")
        
    except Exception as e:
        logger.error(f"Failed to log MCP tool invocation for reasoning server: {e}")


# Add health check endpoint that bypasses authentication
@mcp.custom_route("/health", methods=["GET"])
async def health_check(request: Request) -> Response:
    """Health check endpoint for reasoning server (bypasses authentication)."""
    try:
        health_status = get_server_health()
        status_code = 200 if health_status['status'] == 'healthy' else 503
        return JSONResponse(status_code=status_code, content=health_status)
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat() + "Z",
                'server_type': 'reasoning_mcp'
            }
        )


# Add metrics endpoint that bypasses authentication
@mcp.custom_route("/metrics", methods=["GET"])
async def metrics_endpoint(request: Request) -> Response:
    """Metrics endpoint for reasoning server (bypasses authentication)."""
    try:
        metrics = get_server_metrics()
        return JSONResponse(status_code=200, content=metrics)
    except Exception as e:
        logger.error(f"Metrics collection failed: {e}")
        return JSONResponse(
            status_code=500,
            content={
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat() + "Z",
                'server_type': 'reasoning_mcp'
            }
        )


async def initialize_status_check_system():
    """Initialize the status check system for reasoning server."""
    global health_service, health_check_task
    
    try:
        logger.info("Initializing reasoning status check system...")
        
        # Load server configurations
        server_configs = config_loader.get_server_configs()
        enabled_servers = config_loader.get_enabled_servers()
        
        logger.info(f"Found {len(server_configs)} reasoning server configs, {len(enabled_servers)} enabled")
        
        # Add enabled servers to status manager
        for server_name, config in server_configs.items():
            if config.enabled:
                await status_manager.add_server(server_name, config.circuit_breaker)
                logger.info(f"Added reasoning server '{server_name}' to status monitoring")
        
        # Initialize health check service
        system_config = config_loader.get_system_config()
        health_service = HealthCheckService(
            timeout_seconds=system_config.get('global_timeout_seconds', 10),
            max_concurrent_checks=system_config.get('max_concurrent_checks', 5)
        )
        
        # Start continuous health checks if enabled
        if system_config.get('enabled', True) and enabled_servers:
            enabled_configs = [config for config in server_configs.values() if config.enabled]
            
            async def health_check_callback(results):
                """Callback to handle health check results."""
                for result in results:
                    await status_manager.record_health_check_result(result)
                    
                    if result.success:
                        logger.debug(f"Reasoning server '{result.server_name}' health check passed")
                    else:
                        logger.warning(f"Reasoning server '{result.server_name}' health check failed: {result.error_message}")
            
            # Start background health check task
            health_check_task = asyncio.create_task(
                health_service.run_continuous_health_checks(
                    enabled_configs,
                    health_check_callback,
                    health_check_stop_event
                )
            )
            
            logger.info(f"Started continuous health checks for {len(enabled_configs)} reasoning servers")
        
        logger.info("Reasoning status check system initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize reasoning status check system: {e}")
        # Don't fail server startup if status check system fails
        pass


async def shutdown_status_check_system():
    """Shutdown the status check system for reasoning server."""
    global health_check_task, health_service
    
    try:
        logger.info("Shutting down reasoning status check system...")
        
        # Stop health check task
        if health_check_task and not health_check_task.done():
            health_check_stop_event.set()
            try:
                await asyncio.wait_for(health_check_task, timeout=5.0)
            except asyncio.TimeoutError:
                health_check_task.cancel()
                logger.warning("Health check task did not stop gracefully, cancelled")
        
        # Close health service
        if health_service:
            await health_service._close_session()
        
        logger.info("Reasoning status check system shutdown complete")
        
    except Exception as e:
        logger.error(f"Error during reasoning status check system shutdown: {e}")


# Register status check endpoints
try:
    status_endpoints = create_reasoning_status_endpoints(mcp.app, status_manager)
    logger.info("Registered reasoning status check endpoints")
except Exception as e:
    logger.error(f"Failed to register reasoning status check endpoints: {e}")


# Add startup and shutdown event handlers
@mcp.app.on_event("startup")
async def startup_event():
    """Handle server startup events."""
    logger.info("Starting reasoning MCP server startup sequence...")
    await initialize_status_check_system()
    logger.info("Reasoning MCP server startup complete")


@mcp.app.on_event("shutdown")
async def shutdown_event():
    """Handle server shutdown events."""
    logger.info("Starting reasoning MCP server shutdown sequence...")
    await shutdown_status_check_system()
    logger.info("Reasoning MCP server shutdown complete")


@mcp.tool()
def recommend_restaurants(
    restaurants: List[Dict[str, Any]], 
    ranking_method: str = "sentiment_likes"
) -> str:
    """
    Analyze restaurant sentiment data and provide intelligent recommendations.
    
    This tool analyzes a list of restaurants with sentiment data (likes, dislikes, neutral)
    and provides both a ranked list of top candidates and a single recommendation.
    The ranking can be based on either highest sentiment likes or combined positive sentiment.
    
    Args:
        restaurants: List of restaurant objects with sentiment data. Each restaurant must have:
                    - id: string identifier
                    - name: restaurant name  
                    - sentiment: object with likes, dislikes, neutral (integers)
                    - Other fields like address, district, etc. are optional
        ranking_method: Ranking method to use:
                       - "sentiment_likes": Rank by highest likes count
                       - "combined_sentiment": Rank by (likes + neutral) percentage
                       
    Returns:
        JSON string containing:
        - recommendation: Single recommended restaurant from top candidates
        - candidates: List of top 20 restaurants (or all if fewer than 20)
        - ranking_method: Method used for ranking
        - analysis_summary: Statistical analysis of the restaurant data
        
    Example:
        recommend_restaurants([
            {
                "id": "rest_001",
                "name": "Great Restaurant",
                "sentiment": {"likes": 85, "dislikes": 10, "neutral": 5},
                "address": "123 Main St",
                "district": "Central"
            }
        ], "sentiment_likes")
    """
    try:
        # Log tool invocation (no request context available in MCP tools)
        log_mcp_tool_invocation('recommend_restaurants', {
            'restaurants': restaurants,
            'ranking_method': ranking_method
        }, None)
        
        logger.info(f"Processing recommendation request for {len(restaurants) if isinstance(restaurants, list) else 0} restaurants")
        
        # Validate input parameters
        is_valid, error_msg = validate_restaurant_list_parameter(restaurants)
        if not is_valid:
            return format_error_response(error_msg, "ValidationError")
        
        is_valid, error_msg = validate_ranking_method_parameter(ranking_method)
        if not is_valid:
            return format_error_response(error_msg, "ValidationError")
        
        # Perform restaurant analysis and recommendation
        recommendation_result = reasoning_service.analyze_and_recommend(
            restaurant_data=restaurants,
            ranking_method=ranking_method,
            candidate_count=20
        )
        
        # Format successful response
        response = {
            'success': True,
            'data': {
                'recommendation': recommendation_result.recommendation.to_dict(),
                'candidates': [restaurant.to_dict() for restaurant in recommendation_result.candidates],
                'ranking_method': recommendation_result.ranking_method,
                'candidate_count': len(recommendation_result.candidates),
                'analysis_summary': recommendation_result.analysis_summary,
                'timestamp': datetime.utcnow().isoformat() + "Z"
            }
        }
        
        logger.info(
            f"Generated recommendation: {recommendation_result.recommendation.name} "
            f"from {len(recommendation_result.candidates)} candidates using {ranking_method}"
        )
        
        return json.dumps(response, indent=2)
        
    except ValueError as e:
        logger.error(f"Validation error in recommend_restaurants: {e}")
        return format_error_response(str(e), "ValidationError")
        
    except Exception as e:
        logger.error(f"Unexpected error in recommend_restaurants: {e}")
        # Check if this is an authentication error
        if "authentication" in str(e).lower() or "unauthorized" in str(e).lower():
            return format_error_response(
                "Authentication required for reasoning operations",
                "AuthenticationError",
                {"status_code": 401, "suggested_action": "Provide valid JWT token in Authorization header"}
            )
        
        return format_error_response(
            f"An unexpected error occurred during recommendation analysis: {str(e)}",
            "ProcessingError"
        )


@mcp.tool()
def analyze_restaurant_sentiment(restaurants: List[Dict[str, Any]]) -> str:
    """
    Analyze sentiment data for a list of restaurants without providing recommendations.
    
    This tool performs sentiment analysis on restaurant data to provide statistical
    insights about customer satisfaction metrics without selecting specific recommendations.
    Useful for understanding overall sentiment patterns in a restaurant dataset.
    
    Args:
        restaurants: List of restaurant objects with sentiment data. Each restaurant must have:
                    - id: string identifier
                    - name: restaurant name
                    - sentiment: object with likes, dislikes, neutral (integers)
                    - Other fields are optional for analysis
                    
    Returns:
        JSON string containing:
        - sentiment_analysis: Statistical analysis including averages and score ranges
        - restaurant_count: Number of restaurants analyzed
        - ranking_method: Method used for analysis (defaults to sentiment_likes)
        
    Example:
        analyze_restaurant_sentiment([
            {
                "id": "rest_001", 
                "name": "Restaurant A",
                "sentiment": {"likes": 85, "dislikes": 10, "neutral": 5}
            },
            {
                "id": "rest_002",
                "name": "Restaurant B", 
                "sentiment": {"likes": 70, "dislikes": 20, "neutral": 10}
            }
        ])
    """
    try:
        # Log tool invocation (no request context available in MCP tools)
        log_mcp_tool_invocation('analyze_restaurant_sentiment', {
            'restaurants': restaurants
        }, None)
        
        logger.info(f"Processing sentiment analysis for {len(restaurants) if isinstance(restaurants, list) else 0} restaurants")
        
        # Validate input parameters
        is_valid, error_msg = validate_restaurant_list_parameter(restaurants)
        if not is_valid:
            return format_error_response(error_msg, "ValidationError")
        
        # Perform sentiment analysis
        sentiment_analysis = reasoning_service.analyze_sentiment_only(
            restaurant_data=restaurants,
            ranking_method="sentiment_likes"  # Default method for analysis
        )
        
        # Format successful response
        response = {
            'success': True,
            'data': {
                'sentiment_analysis': sentiment_analysis.to_dict(),
                'restaurant_count': sentiment_analysis.restaurant_count,
                'ranking_method': sentiment_analysis.ranking_method,
                'timestamp': datetime.utcnow().isoformat() + "Z"
            }
        }
        
        logger.info(
            f"Completed sentiment analysis for {sentiment_analysis.restaurant_count} restaurants"
        )
        
        return json.dumps(response, indent=2)
        
    except ValueError as e:
        logger.error(f"Validation error in analyze_restaurant_sentiment: {e}")
        return format_error_response(str(e), "ValidationError")
        
    except Exception as e:
        logger.error(f"Unexpected error in analyze_restaurant_sentiment: {e}")
        # Check if this is an authentication error
        if "authentication" in str(e).lower() or "unauthorized" in str(e).lower():
            return format_error_response(
                "Authentication required for reasoning operations",
                "AuthenticationError", 
                {"status_code": 401, "suggested_action": "Provide valid JWT token in Authorization header"}
            )
        
        return format_error_response(
            f"An unexpected error occurred during sentiment analysis: {str(e)}",
            "ProcessingError"
        )


def get_server_health() -> Dict[str, Any]:
    """
    Get server health status for internal monitoring.
    
    Returns:
        Dictionary containing server health information
    """
    try:
        # Test reasoning service functionality
        test_data = [{
            "id": "test_001",
            "name": "Test Restaurant",
            "sentiment": {"likes": 10, "dislikes": 2, "neutral": 3},
            "address": "Test Address",
            "meal_type": ["lunch"],
            "location_category": "test",
            "district": "test",
            "price_range": "$$"
        }]
        
        # Test validation
        validation_result = reasoning_service.validate_restaurant_data(test_data)
        
        health_status = {
            'status': 'healthy' if validation_result.is_valid else 'degraded',
            'timestamp': datetime.utcnow().isoformat() + "Z",
            'services': {
                'reasoning_service': validation_result.is_valid,
                'validation_service': True,
                'sentiment_service': True,
                'recommendation_service': True
            },
            'version': '1.0.0',
            'server_type': 'restaurant_reasoning_mcp'
        }
        
        return health_status
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            'status': 'unhealthy',
            'timestamp': datetime.utcnow().isoformat() + "Z",
            'error': str(e),
            'version': '1.0.0',
            'server_type': 'restaurant_reasoning_mcp'
        }


def get_server_metrics() -> Dict[str, Any]:
    """
    Get server metrics for internal monitoring.
    
    Returns:
        Dictionary containing server metrics
    """
    try:
        metrics = {
            'mcp_server_status': 'running',
            'server_type': 'restaurant_reasoning_mcp',
            'available_tools': ['recommend_restaurants', 'analyze_restaurant_sentiment'],
            'tool_count': 2,
            'reasoning_service_config': {
                'minimum_responses': reasoning_service.minimum_responses,
                'default_candidate_count': reasoning_service.default_candidate_count,
                'strict_validation': reasoning_service.strict_validation
            },
            'timestamp': datetime.utcnow().isoformat() + "Z"
        }
        
        return metrics
        
    except Exception as e:
        logger.error(f"Metrics collection failed: {e}")
        return {
            'mcp_server_status': 'error',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat() + "Z"
        }


if __name__ == "__main__":
    logger.info("Starting Restaurant Reasoning MCP Server with Authentication and Status Monitoring")
    
    # Log server configuration
    logger.info(f"Server configuration:")
    logger.info(f"  - Host: 0.0.0.0")
    logger.info(f"  - Stateless HTTP: True")
    logger.info(f"  - Authentication: Enabled (JWT via Cognito)")
    logger.info(f"  - Status Monitoring: Enabled")
    logger.info(f"  - User Pool ID: {cognito_config.get('user_pool_id', 'Not configured')}")
    logger.info(f"  - Client ID: {cognito_config.get('client_id', 'Not configured')}")
    logger.info(f"  - Bypass paths: {auth_config.bypass_paths}")
    logger.info(f"  - Minimum responses: {reasoning_service.minimum_responses}")
    logger.info(f"  - Default candidate count: {reasoning_service.default_candidate_count}")
    logger.info(f"  - Strict validation: {reasoning_service.strict_validation}")
    
    # Test service initialization
    try:
        health_status = get_server_health()
        logger.info(f"Service health check: {health_status['status']}")
        
        if health_status['status'] != 'healthy':
            logger.warning("Some services may not be functioning properly")
            if 'error' in health_status:
                logger.error(f"Health check error: {health_status['error']}")
        
        metrics = get_server_metrics()
        logger.info(f"Available MCP tools: {metrics.get('available_tools', [])}")
        
    except Exception as e:
        logger.error(f"Service initialization test failed: {e}")
        logger.warning("Server will start but some functionality may not work properly")
    
    # Test status check system configuration
    try:
        system_config = config_loader.get_system_config()
        server_configs = config_loader.get_server_configs()
        enabled_servers = config_loader.get_enabled_servers()
        
        logger.info(f"Status check system configuration:")
        logger.info(f"  - System enabled: {system_config.get('enabled', True)}")
        logger.info(f"  - Check interval: {system_config.get('global_check_interval_seconds', 30)}s")
        logger.info(f"  - Timeout: {system_config.get('global_timeout_seconds', 10)}s")
        logger.info(f"  - Total servers configured: {len(server_configs)}")
        logger.info(f"  - Enabled servers: {len(enabled_servers)}")
        
        if enabled_servers:
            logger.info(f"  - Enabled server names: {', '.join(enabled_servers)}")
        
    except Exception as e:
        logger.warning(f"Could not load status check configuration: {e}")
    
    # Start the MCP server
    logger.info("Starting authenticated FastMCP server with stateless HTTP transport for AgentCore Runtime")
    logger.info("Available endpoints:")
    logger.info(f"  - Health check (bypass): GET /health")
    logger.info(f"  - Metrics (bypass): GET /metrics")
    logger.info(f"  - Status endpoints (bypass): GET /status/*")
    logger.info(f"  - MCP tools (authenticated): recommend_restaurants, analyze_restaurant_sentiment")
    
    try:
        mcp.run()
    except Exception as e:
        logger.error(f"Failed to start authenticated reasoning MCP server: {e}")
        raise