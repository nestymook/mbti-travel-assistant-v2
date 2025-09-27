"""Restaurant Search MCP Server.

This module implements a FastMCP server that provides restaurant search tools
for foundation models. It exposes MCP tools for searching restaurants by district,
meal type, and combined criteria using AWS S3 data and local district configuration.

The server follows Bedrock AgentCore patterns with stateless HTTP transport,
JWT authentication via Cognito, and proper error handling for MCP tool integration.
"""

import json
import logging
import os
from datetime import datetime
from typing import List, Optional, Dict, Any

from mcp.server.fastmcp import FastMCP

from services.restaurant_service import RestaurantService, RestaurantSearchError
from services.auth_middleware import create_authentication_middleware, AuthenticationHelper
from services.security_monitor import get_security_monitor
from models.restaurant_models import Restaurant


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
        
        # Transform to format expected by TokenValidator
        cognito_config = {
            'user_pool_id': config['user_pool']['user_pool_id'],
            'client_id': config['app_client']['client_id'],
            'region': config['region'],
            'discovery_url': config['discovery_url']
        }
        
        logger.info(f"Loaded Cognito configuration for User Pool: {cognito_config['user_pool_id']}")
        return cognito_config
        
    except Exception as e:
        logger.error(f"Failed to load Cognito configuration: {e}")
        # Return minimal config for testing without authentication
        return {
            'user_pool_id': 'test-pool',
            'client_id': 'test-client',
            'region': 'us-east-1',
            'discovery_url': 'https://test.example.com/.well-known/openid-configuration'
        }

# Create FastMCP server with stdio transport for Kiro MCP integration
mcp = FastMCP("restaurant-search-mcp")

# Load authentication configuration
cognito_config = load_cognito_config()

# Configure authentication middleware
# Authentication can be disabled via environment variable for testing
require_auth = os.getenv('REQUIRE_AUTHENTICATION', 'true').lower() == 'true'
bypass_paths = ['/health', '/metrics', '/docs', '/openapi.json', '/']

# Note: FastMCP doesn't expose the underlying FastAPI app directly
# Authentication will be handled at the AgentCore Runtime level
# This is a placeholder for when FastMCP supports middleware
auth_middleware_config = None

if require_auth:
    logger.info("Authentication enabled - JWT tokens required")
    logger.info("Note: Authentication will be handled by AgentCore Runtime JWT authorizer")
    auth_middleware_config = {
        'cognito_config': cognito_config,
        'bypass_paths': bypass_paths,
        'require_authentication': True,
        'log_user_context': True
    }
else:
    logger.warning("Authentication disabled - running in development mode")

# Initialize restaurant service
restaurant_service = RestaurantService()

# Initialize security monitor
security_monitor = get_security_monitor()


def format_restaurant_response(restaurants: List[Restaurant], 
                             metadata: Optional[Dict[str, Any]] = None) -> str:
    """Format restaurant data for MCP tool response.
    
    Args:
        restaurants: List of Restaurant objects
        metadata: Optional metadata to include in response
        
    Returns:
        JSON string containing formatted restaurant data
    """
    try:
        # Convert restaurants to dictionaries
        restaurant_dicts = []
        for restaurant in restaurants:
            restaurant_dict = {
                'id': restaurant.id,
                'name': restaurant.name,
                'address': restaurant.address,
                'meal_type': restaurant.meal_type,
                'sentiment': {
                    'likes': restaurant.sentiment.likes,
                    'dislikes': restaurant.sentiment.dislikes,
                    'neutral': restaurant.sentiment.neutral
                },
                'location_category': restaurant.location_category,
                'district': restaurant.district,
                'price_range': restaurant.price_range,
                'operating_hours': {
                    'mon_fri': restaurant.operating_hours.mon_fri,
                    'sat_sun': restaurant.operating_hours.sat_sun,
                    'public_holiday': restaurant.operating_hours.public_holiday
                },
                'metadata': {
                    'data_quality': restaurant.metadata.data_quality,
                    'version': restaurant.metadata.version,
                    'quality_score': restaurant.metadata.quality_score
                }
            }
            restaurant_dicts.append(restaurant_dict)
        
        # Create response structure
        response = {
            'success': True,
            'data': {
                'restaurants': restaurant_dicts,
                'count': len(restaurant_dicts)
            }
        }
        
        # Add metadata if provided
        if metadata:
            response['data']['metadata'] = metadata
            
        return json.dumps(response, indent=2)
        
    except Exception as e:
        logger.error(f"Error formatting restaurant response: {e}")
        return json.dumps({
            'success': False,
            'error': f'Failed to format response: {str(e)}'
        })


def format_error_response(error_message: str, 
                         error_type: str = "SearchError",
                         details: Optional[Dict[str, Any]] = None) -> str:
    """Format error response for MCP tools.
    
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
            'message': error_message
        }
    }
    
    if details:
        response['error']['details'] = details
        
    return json.dumps(response, indent=2)


# Note: FastMCP doesn't support custom HTTP endpoints like health checks
# Health monitoring will be handled by AgentCore Runtime
# The MCP server provides tools, not HTTP endpoints

def get_server_health() -> dict:
    """Get server health status for internal monitoring."""
    try:
        # Test basic service functionality
        test_results = restaurant_service.test_services()
        
        health_status = {
            'status': 'healthy' if all(test_results.values()) else 'degraded',
            'timestamp': datetime.now().isoformat(),
            'services': test_results,
            'version': '1.0.0',
            'authentication_enabled': require_auth
        }
        
        return health_status
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            'status': 'unhealthy',
            'timestamp': datetime.now().isoformat(),
            'error': str(e),
            'version': '1.0.0'
        }

def get_server_metrics() -> dict:
    """Get server metrics for internal monitoring."""
    try:
        # Get basic service metrics
        available_districts = restaurant_service.get_available_districts()
        
        # Get security metrics
        security_metrics = security_monitor.get_security_metrics()
        
        metrics = {
            'mcp_server_status': 'running',
            'authentication_enabled': require_auth,
            'available_districts_count': len(available_districts) if available_districts else 0,
            'security_metrics': {
                'total_auth_attempts': security_metrics.total_auth_attempts,
                'successful_auths': security_metrics.successful_auths,
                'failed_auths': security_metrics.failed_auths,
                'token_validations': security_metrics.token_validations,
                'suspicious_activities': security_metrics.suspicious_activities,
                'blocked_ips': security_metrics.blocked_ips
            },
            'timestamp': datetime.now().isoformat()
        }
        
        return metrics
        
    except Exception as e:
        logger.error(f"Metrics collection failed: {e}")
        return {
            'mcp_server_status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }


def log_mcp_tool_invocation(tool_name: str, parameters: Dict[str, Any]) -> None:
    """Log MCP tool invocation for security audit.
    
    Args:
        tool_name: Name of the MCP tool being invoked
        parameters: Parameters passed to the tool
    """
    try:
        # Create mock user and request context since FastMCP doesn't provide direct access
        # In production, this would be extracted from the authenticated request
        user_context = {
            'user_id': 'mcp_user',  # Would be extracted from JWT token
            'username': 'mcp_user',  # Would be extracted from JWT token
            'email': 'unknown'  # Would be extracted from JWT token
        }
        
        request_context = {
            'path': f'/mcp/tools/{tool_name}',
            'method': 'POST',
            'client_ip': 'unknown',  # Would be extracted from request
            'user_agent': 'MCP Client',  # Would be extracted from request
            'timestamp': datetime.now().isoformat()
        }
        
        # Log the tool invocation
        security_monitor.log_mcp_tool_invocation(
            tool_name=tool_name,
            user_context=user_context,
            request_context=request_context,
            parameters=parameters
        )
        
    except Exception as e:
        logger.error(f"Failed to log MCP tool invocation: {e}")

@mcp.tool()
def search_restaurants_by_district(districts: List[str]) -> str:
    """Search for restaurants in specific districts.
    
    This tool searches for restaurants located in the specified districts.
    It validates district names against the local configuration and retrieves
    restaurant data from S3 storage.
    
    Args:
        districts: List of district names to search (e.g., ["Central district", "Admiralty"])
        
    Returns:
        JSON string containing restaurant data and metadata
        
    Example:
        search_restaurants_by_district(["Central district", "Admiralty"])
    """
    try:
        # Log MCP tool invocation for security audit
        log_mcp_tool_invocation('search_restaurants_by_district', {'districts': districts})
        
        logger.info(f"Searching restaurants by districts: {districts}")
        
        # Validate input parameters
        if not districts:
            return format_error_response(
                "Districts parameter is required and cannot be empty",
                "ValidationError"
            )
        
        if not isinstance(districts, list):
            return format_error_response(
                "Districts parameter must be a list of strings",
                "ValidationError"
            )
        
        # Validate all items are strings
        for district in districts:
            if not isinstance(district, str):
                return format_error_response(
                    f"All district names must be strings, got: {type(district).__name__}",
                    "ValidationError"
                )
        
        # Search for restaurants
        restaurants = restaurant_service.search_by_districts(districts)
        
        # Get additional metadata
        available_districts = restaurant_service.get_available_districts()
        district_counts = restaurant_service.get_restaurant_count_by_district(districts)
        
        metadata = {
            'search_criteria': {
                'districts': districts,
                'search_type': 'district'
            },
            'district_counts': district_counts,
            'available_districts': available_districts
        }
        
        logger.info(f"Found {len(restaurants)} restaurants in districts: {districts}")
        return format_restaurant_response(restaurants, metadata)
        
    except RestaurantSearchError as e:
        logger.error(f"Restaurant search error: {e}")
        
        # Check if it's a district validation error
        if "Invalid districts:" in str(e):
            try:
                available_districts = restaurant_service.get_available_districts()
                details = {
                    'available_districts': available_districts,
                    'requested_districts': districts
                }
                return format_error_response(str(e), "ValidationError", details)
            except Exception:
                pass
        
        return format_error_response(str(e), "RestaurantSearchError")
        
    except Exception as e:
        logger.error(f"Unexpected error in search_restaurants_by_district: {e}")
        return format_error_response(
            f"An unexpected error occurred: {str(e)}",
            "InternalError"
        )


@mcp.tool()
def search_restaurants_by_meal_type(meal_types: List[str]) -> str:
    """Search for restaurants by meal type based on operating hours.
    
    This tool searches for restaurants that serve specific meal types by analyzing
    their operating hours. It checks if restaurants are open during breakfast
    (07:00-11:29), lunch (11:30-17:29), or dinner (17:30-22:30) periods.
    
    Args:
        meal_types: List of meal types to search for (valid values: "breakfast", "lunch", "dinner")
        
    Returns:
        JSON string containing restaurant data filtered by meal type availability
        
    Example:
        search_restaurants_by_meal_type(["breakfast", "lunch"])
    """
    try:
        # Log MCP tool invocation for security audit
        log_mcp_tool_invocation('search_restaurants_by_meal_type', {'meal_types': meal_types})
        
        logger.info(f"Searching restaurants by meal types: {meal_types}")
        
        # Validate input parameters
        if not meal_types:
            return format_error_response(
                "Meal types parameter is required and cannot be empty",
                "ValidationError"
            )
        
        if not isinstance(meal_types, list):
            return format_error_response(
                "Meal types parameter must be a list of strings",
                "ValidationError"
            )
        
        # Validate all items are strings
        for meal_type in meal_types:
            if not isinstance(meal_type, str):
                return format_error_response(
                    f"All meal type names must be strings, got: {type(meal_type).__name__}",
                    "ValidationError"
                )
        
        # Validate meal type values
        valid_meal_types = {"breakfast", "lunch", "dinner"}
        invalid_meal_types = []
        for meal_type in meal_types:
            if meal_type.lower() not in valid_meal_types:
                invalid_meal_types.append(meal_type)
        
        if invalid_meal_types:
            details = {
                'invalid_meal_types': invalid_meal_types,
                'valid_meal_types': list(valid_meal_types),
                'requested_meal_types': meal_types
            }
            return format_error_response(
                f"Invalid meal types: {invalid_meal_types}. Valid meal types are: {list(valid_meal_types)}",
                "ValidationError",
                details
            )
        
        # Search for restaurants
        restaurants = restaurant_service.search_by_meal_types(meal_types)
        
        # Get meal type analysis
        meal_analysis = restaurant_service.get_meal_type_analysis(restaurants)
        
        metadata = {
            'search_criteria': {
                'meal_types': meal_types,
                'search_type': 'meal_type'
            },
            'meal_analysis': meal_analysis,
            'meal_periods': {
                'breakfast': '07:00 - 11:29',
                'lunch': '11:30 - 17:29',
                'dinner': '17:30 - 22:30'
            }
        }
        
        logger.info(f"Found {len(restaurants)} restaurants serving meal types: {meal_types}")
        return format_restaurant_response(restaurants, metadata)
        
    except RestaurantSearchError as e:
        logger.error(f"Restaurant search error: {e}")
        
        # Check if it's a meal type validation error
        if "Invalid meal types:" in str(e):
            details = {
                'valid_meal_types': list(valid_meal_types),
                'requested_meal_types': meal_types
            }
            return format_error_response(str(e), "ValidationError", details)
        
        return format_error_response(str(e), "RestaurantSearchError")
        
    except Exception as e:
        logger.error(f"Unexpected error in search_restaurants_by_meal_type: {e}")
        return format_error_response(
            f"An unexpected error occurred: {str(e)}",
            "InternalError"
        )


@mcp.tool()
def search_restaurants_combined(districts: Optional[List[str]] = None, 
                               meal_types: Optional[List[str]] = None) -> str:
    """Search for restaurants by both district and meal type criteria.
    
    This tool provides flexible restaurant search by combining district and meal type
    filters. You can specify either districts, meal types, or both. If both are provided,
    restaurants must match both criteria to be included in results.
    
    Args:
        districts: Optional list of district names to search (e.g., ["Central district", "Admiralty"])
        meal_types: Optional list of meal types to filter by (valid values: "breakfast", "lunch", "dinner")
        
    Returns:
        JSON string containing restaurant data matching the specified criteria
        
    Examples:
        search_restaurants_combined(districts=["Central district"], meal_types=["breakfast"])
        search_restaurants_combined(districts=["Admiralty", "Causeway Bay"])
        search_restaurants_combined(meal_types=["lunch", "dinner"])
    """
    try:
        # Log MCP tool invocation for security audit
        log_mcp_tool_invocation('search_restaurants_combined', {
            'districts': districts,
            'meal_types': meal_types
        })
        
        logger.info(f"Combined search - districts: {districts}, meal_types: {meal_types}")
        
        # Validate that at least one parameter is provided
        if not districts and not meal_types:
            return format_error_response(
                "At least one of 'districts' or 'meal_types' parameters must be provided",
                "ValidationError"
            )
        
        # Validate districts parameter if provided
        if districts is not None:
            if not isinstance(districts, list):
                return format_error_response(
                    "Districts parameter must be a list of strings",
                    "ValidationError"
                )
            
            if not districts:  # Empty list
                return format_error_response(
                    "Districts list cannot be empty when provided",
                    "ValidationError"
                )
            
            # Validate all items are strings
            for district in districts:
                if not isinstance(district, str):
                    return format_error_response(
                        f"All district names must be strings, got: {type(district).__name__}",
                        "ValidationError"
                    )
        
        # Validate meal_types parameter if provided
        if meal_types is not None:
            if not isinstance(meal_types, list):
                return format_error_response(
                    "Meal types parameter must be a list of strings",
                    "ValidationError"
                )
            
            if not meal_types:  # Empty list
                return format_error_response(
                    "Meal types list cannot be empty when provided",
                    "ValidationError"
                )
            
            # Validate all items are strings
            for meal_type in meal_types:
                if not isinstance(meal_type, str):
                    return format_error_response(
                        f"All meal type names must be strings, got: {type(meal_type).__name__}",
                        "ValidationError"
                    )
            
            # Validate meal type values
            valid_meal_types = {"breakfast", "lunch", "dinner"}
            invalid_meal_types = []
            for meal_type in meal_types:
                if meal_type.lower() not in valid_meal_types:
                    invalid_meal_types.append(meal_type)
            
            if invalid_meal_types:
                details = {
                    'invalid_meal_types': invalid_meal_types,
                    'valid_meal_types': list(valid_meal_types),
                    'requested_meal_types': meal_types
                }
                return format_error_response(
                    f"Invalid meal types: {invalid_meal_types}. Valid meal types are: {list(valid_meal_types)}",
                    "ValidationError",
                    details
                )
        
        # Perform combined search
        restaurants = restaurant_service.search_combined(districts, meal_types)
        
        # Build comprehensive metadata
        metadata = {
            'search_criteria': {
                'districts': districts,
                'meal_types': meal_types,
                'search_type': 'combined'
            }
        }
        
        # Add district-specific metadata if districts were provided
        if districts:
            try:
                available_districts = restaurant_service.get_available_districts()
                district_counts = restaurant_service.get_restaurant_count_by_district(districts)
                metadata['district_info'] = {
                    'available_districts': available_districts,
                    'district_counts': district_counts
                }
            except Exception as e:
                logger.warning(f"Could not get district metadata: {e}")
        
        # Add meal type analysis if meal types were provided
        if meal_types:
            try:
                meal_analysis = restaurant_service.get_meal_type_analysis(restaurants)
                metadata['meal_analysis'] = meal_analysis
                metadata['meal_periods'] = {
                    'breakfast': '07:00 - 11:29',
                    'lunch': '11:30 - 17:29',
                    'dinner': '17:30 - 22:30'
                }
            except Exception as e:
                logger.warning(f"Could not get meal type analysis: {e}")
        
        # Add search summary
        search_summary = []
        if districts:
            search_summary.append(f"{len(districts)} district(s)")
        if meal_types:
            search_summary.append(f"{len(meal_types)} meal type(s)")
        
        metadata['search_summary'] = {
            'criteria': " and ".join(search_summary),
            'results_count': len(restaurants)
        }
        
        logger.info(f"Combined search found {len(restaurants)} restaurants")
        return format_restaurant_response(restaurants, metadata)
        
    except RestaurantSearchError as e:
        logger.error(f"Restaurant search error: {e}")
        
        # Provide specific error details based on error type
        details = {}
        if "Invalid districts:" in str(e):
            try:
                available_districts = restaurant_service.get_available_districts()
                details = {
                    'available_districts': available_districts,
                    'requested_districts': districts
                }
            except Exception:
                pass
        elif "Invalid meal types:" in str(e):
            details = {
                'valid_meal_types': ["breakfast", "lunch", "dinner"],
                'requested_meal_types': meal_types
            }
        
        return format_error_response(str(e), "RestaurantSearchError", details if details else None)
        
    except Exception as e:
        logger.error(f"Unexpected error in search_restaurants_combined: {e}")
        return format_error_response(
            f"An unexpected error occurred: {str(e)}",
            "InternalError"
        )


if __name__ == "__main__":
    logger.info("Starting Restaurant Search MCP Server with Authentication")
    
    # Log authentication configuration
    logger.info(f"Authentication required: {require_auth}")
    logger.info(f"Cognito User Pool: {cognito_config.get('user_pool_id', 'N/A')}")
    logger.info(f"Bypass paths: {bypass_paths}")
    
    # Test service initialization
    try:
        test_results = restaurant_service.test_services()
        logger.info(f"Service test results: {test_results}")
        
        if not all(test_results.values()):
            logger.warning("Some services failed initialization tests")
            for service, result in test_results.items():
                if not result:
                    logger.warning(f"Service '{service}' test failed")
    except Exception as e:
        logger.error(f"Service initialization test failed: {e}")
    
    # Test authentication configuration if enabled
    if require_auth:
        try:
            from services.auth_service import TokenValidator
            validator = TokenValidator(cognito_config)
            logger.info("Authentication configuration validated successfully")
            logger.info("Note: JWT authentication will be enforced by AgentCore Runtime")
        except Exception as e:
            logger.error(f"Authentication configuration test failed: {e}")
            logger.warning("Server will start but authentication may not work properly")
    
    # Test health and metrics functions
    try:
        health_status = get_server_health()
        logger.info(f"Server health status: {health_status['status']}")
        
        metrics = get_server_metrics()
        logger.info(f"Server metrics: {metrics['mcp_server_status']}")
    except Exception as e:
        logger.error(f"Health/metrics test failed: {e}")
    
    # Start the MCP server with stdio transport for Kiro integration
    logger.info("Starting FastMCP server with stdio transport")
    
    try:
        mcp.run()
    except Exception as e:
        logger.error(f"Failed to start MCP server: {e}")
        raise