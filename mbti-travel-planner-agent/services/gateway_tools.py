"""
Gateway HTTP Tools for MBTI Travel Planner Agent

This module provides restaurant search tools that use the Gateway HTTP Client
to communicate with the agentcore-gateway-mcp-tools service. These tools replace
the MCP client-based tools with simpler HTTP API calls.
"""

import json
import logging
import asyncio
from typing import Dict, Any, List, Optional

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

from .gateway_http_client import (
    GatewayHTTPClient, 
    GatewayError, 
    GatewayConnectionError, 
    GatewayServiceError, 
    GatewayValidationError,
    create_gateway_client
)
from .central_district_workflow import CentralDistrictWorkflow, WorkflowResult

# Configure logging
logger = logging.getLogger(__name__)


class GatewayToolsManager:
    """
    Manager for Gateway HTTP-based tools.
    
    This class provides restaurant search and recommendation tools that use
    the Gateway HTTP Client to communicate with the deployed gateway service.
    """
    
    def __init__(self, environment: str = None, base_url: str = None, auth_token: str = None):
        """
        Initialize the Gateway Tools Manager.
        
        Args:
            environment: Target environment (development, staging, production)
            base_url: Override base URL for gateway service
            auth_token: JWT authentication token (optional)
        """
        self.client = create_gateway_client(
            environment=environment,
            base_url=base_url,
            auth_token=auth_token
        )
        logger.info(f"Gateway Tools Manager initialized for {self.client.environment.value} environment")
    
    def set_auth_token(self, token: str) -> None:
        """Set the JWT authentication token."""
        self.client.set_auth_token(token)
    
    def _format_error_response(self, error: Exception, operation: str, parameters: Dict[str, Any]) -> str:
        """
        Format error responses for tool functions.
        
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
        if isinstance(error, GatewayConnectionError):
            error_response["error"]["user_message"] = (
                "Restaurant search service is temporarily unavailable. "
                "Please try again later."
            )
            error_response["error"]["fallback"] = (
                "I can still help with general travel planning questions."
            )
        elif isinstance(error, GatewayServiceError):
            error_response["error"]["user_message"] = (
                f"Restaurant search encountered an issue: {str(error)}"
            )
            error_response["error"]["fallback"] = (
                "Let me know if you'd like help with other travel planning topics."
            )
        elif isinstance(error, GatewayValidationError):
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
    
    def _format_success_response(self, result: Dict[str, Any]) -> str:
        """
        Format successful responses for tool functions.
        
        Args:
            result: The successful result from the gateway
            
        Returns:
            JSON string with formatted result
        """
        return json.dumps(result, ensure_ascii=False, indent=2)
    
    async def _execute_async_operation(self, operation_func, *args, **kwargs):
        """
        Execute an async operation and handle any errors.
        
        Args:
            operation_func: The async function to execute
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function
            
        Returns:
            The result of the operation
        """
        try:
            return await operation_func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in async operation {operation_func.__name__}: {e}")
            raise
    
    def search_restaurants_by_district_tool(self, districts: List[str]) -> str:
        """
        Search for restaurants in specific districts using Gateway HTTP client.
        
        This tool calls the gateway's district search endpoint to find restaurants
        located in the specified Hong Kong districts.
        
        Args:
            districts: List of district names to search (e.g., ["Central district", "Admiralty"])
            
        Returns:
            JSON string containing restaurant data and metadata
        """
        operation = "search_restaurants_by_district"
        parameters = {"districts": districts}
        
        try:
            logger.info(f"Searching restaurants in districts: {districts}")
            
            # Validate input parameters
            if not districts:
                raise GatewayValidationError("Districts list cannot be empty")
            
            if not isinstance(districts, list):
                raise GatewayValidationError("Districts must be provided as a list")
            
            if not all(isinstance(d, str) and d.strip() for d in districts):
                raise GatewayValidationError("All districts must be non-empty strings")
            
            # Execute async operation
            async def _search():
                return await self.client.search_restaurants_by_district(districts)
            
            result = asyncio.run(_search())
            
            # Check if the operation was successful
            if not result.get("success", True):
                error_info = result.get("error", {})
                raise GatewayServiceError(
                    message=error_info.get("message", "Unknown service error"),
                    status_code=error_info.get("status_code"),
                    response_data=result
                )
            
            logger.info(f"Successfully found restaurants in {len(districts)} districts")
            return self._format_success_response(result)
            
        except Exception as e:
            logger.error(f"Error in {operation}: {e}")
            return self._format_error_response(e, operation, parameters)
    
    def search_restaurants_combined_tool(self, 
                                       districts: Optional[List[str]] = None,
                                       meal_types: Optional[List[str]] = None) -> str:
        """
        Search for restaurants using combined district and meal type filters.
        
        This tool calls the gateway's combined search endpoint to find restaurants
        that match both location and meal timing criteria.
        
        Args:
            districts: Optional list of district names to search
            meal_types: Optional list of meal types ("breakfast", "lunch", "dinner")
            
        Returns:
            JSON string containing restaurant data matching the specified criteria
        """
        operation = "search_restaurants_combined"
        parameters = {"districts": districts, "meal_types": meal_types}
        
        try:
            logger.info(f"Combined search - Districts: {districts}, Meal types: {meal_types}")
            
            # Validate that at least one filter is provided
            if not districts and not meal_types:
                raise GatewayValidationError(
                    "At least one of 'districts' or 'meal_types' must be provided"
                )
            
            # Validate districts if provided
            if districts is not None:
                if not isinstance(districts, list):
                    raise GatewayValidationError("Districts must be provided as a list")
                
                if not districts:
                    raise GatewayValidationError("Districts list cannot be empty when provided")
                
                if not all(isinstance(d, str) and d.strip() for d in districts):
                    raise GatewayValidationError("All districts must be non-empty strings")
            
            # Validate meal types if provided
            if meal_types is not None:
                if not isinstance(meal_types, list):
                    raise GatewayValidationError("Meal types must be provided as a list")
                
                if not meal_types:
                    raise GatewayValidationError("Meal types list cannot be empty when provided")
                
                valid_meal_types = {"breakfast", "lunch", "dinner"}
                invalid_types = [mt for mt in meal_types if mt not in valid_meal_types]
                if invalid_types:
                    raise GatewayValidationError(
                        f"Invalid meal types: {invalid_types}. "
                        f"Valid types are: {list(valid_meal_types)}"
                    )
            
            # Execute async operation
            async def _search():
                return await self.client.search_restaurants_combined(districts, meal_types)
            
            result = asyncio.run(_search())
            
            # Check if the operation was successful
            if not result.get("success", True):
                error_info = result.get("error", {})
                raise GatewayServiceError(
                    message=error_info.get("message", "Unknown service error"),
                    status_code=error_info.get("status_code"),
                    response_data=result
                )
            
            filter_count = (1 if districts else 0) + (1 if meal_types else 0)
            logger.info(f"Successfully performed combined search with {filter_count} filters")
            return self._format_success_response(result)
            
        except Exception as e:
            logger.error(f"Error in {operation}: {e}")
            return self._format_error_response(e, operation, parameters)


def create_restaurant_search_tools(environment: str = None, 
                                 base_url: str = None, 
                                 auth_token: str = None) -> List:
    """
    Create restaurant search tools using Gateway HTTP client.
    
    This function creates Strands Agent tools that use the Gateway HTTP Client
    to communicate with the agentcore-gateway-mcp-tools service for restaurant search.
    
    Args:
        environment: Target environment (development, staging, production)
        base_url: Override base URL for gateway service
        auth_token: JWT authentication token (optional)
        
    Returns:
        List of tool functions for restaurant search functionality
    """
    try:
        # Initialize the tools manager
        tools_manager = GatewayToolsManager(
            environment=environment,
            base_url=base_url,
            auth_token=auth_token
        )
        
        # Create tool functions using the @tool decorator
        @tool(
            name="search_restaurants_by_district",
            description="""Search for restaurants in specific Hong Kong districts using Gateway HTTP API.
            
            This tool connects to the agentcore-gateway-mcp-tools service deployed in Bedrock AgentCore
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
            return tools_manager.search_restaurants_by_district_tool(districts)
        
        @tool(
            name="search_restaurants_combined",
            description="""Search for restaurants using combined district and meal type filters via Gateway HTTP API.
            
            This tool provides flexible restaurant search capabilities by connecting to the 
            agentcore-gateway-mcp-tools service and applying both location and timing filters. 
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
        def search_restaurants_combined(districts: Optional[List[str]] = None,
                                      meal_types: Optional[List[str]] = None) -> str:
            """
            Search for restaurants using combined district and meal type filters.
            
            Args:
                districts: Optional list of district names to filter by
                meal_types: Optional list of meal types to filter by 
                          (valid values: "breakfast", "lunch", "dinner")
                
            Returns:
                JSON string containing restaurant data matching the specified criteria
            """
            return tools_manager.search_restaurants_combined_tool(districts, meal_types)
        
        tools = [search_restaurants_by_district, search_restaurants_combined]
        
        logger.info(f"Created {len(tools)} restaurant search tools using Gateway HTTP client")
        return tools
        
    except Exception as e:
        logger.error(f"Failed to create restaurant search tools: {e}")
        return []


def create_central_district_workflow_tools(environment: str = None, 
                                         base_url: str = None, 
                                         auth_token: str = None) -> List:
    """
    Create Central district search workflow tools using Gateway HTTP client.
    
    This function creates a comprehensive workflow tool that implements the complete
    search → analyze → recommend → format pipeline for Central district restaurants.
    
    Args:
        environment: Target environment (development, staging, production)
        base_url: Override base URL for gateway service
        auth_token: JWT authentication token (optional)
        
    Returns:
        List of workflow tool functions for Central district search
    """
    try:
        # Initialize the workflow
        workflow = CentralDistrictWorkflow(
            environment=environment,
            auth_token=auth_token
        )
        
        @tool(
            name="search_central_district_restaurants",
            description="""Complete workflow for searching restaurants in Hong Kong's Central district with intelligent recommendations.
            
            This tool implements a comprehensive search and recommendation pipeline:
            1. **Search**: Finds restaurants in Central district (Hong Kong's main business district)
            2. **Analyze**: Processes restaurant sentiment data and ratings
            3. **Recommend**: Generates intelligent recommendations based on customer feedback
            4. **Format**: Presents results in a user-friendly format with detailed information
            
            The tool provides:
            - Complete restaurant details (name, address, ratings, price range)
            - Sentiment analysis with customer satisfaction metrics
            - Intelligent recommendations with reasoning
            - Meal type filtering (breakfast, lunch, dinner) based on operating hours
            - User-friendly formatting with travel tips and suggestions
            - Comprehensive error handling with fallback responses
            
            Central district features:
            - Hong Kong's main business and financial district
            - Located on Hong Kong Island with harbor views
            - Accessible via MTR Central Station
            - Diverse dining options from casual to fine dining
            - Popular with both business travelers and tourists
            
            The tool handles edge cases including:
            - No restaurants found (provides alternative suggestions)
            - Partial results (indicates when results are limited)
            - Service unavailable (provides general Central district information)
            """
        )
        def search_central_district_restaurants(meal_types: Optional[List[str]] = None,
                                               include_recommendations: bool = True) -> str:
            """
            Execute complete Central district restaurant search workflow.
            
            Args:
                meal_types: Optional meal type filters (valid values: "breakfast", "lunch", "dinner")
                include_recommendations: Whether to generate intelligent recommendations (default: True)
                
            Returns:
                Formatted string with complete search results, recommendations, and travel tips
            """
            async def _execute_workflow():
                return await workflow.execute_complete_workflow(
                    meal_types=meal_types,
                    include_recommendations=include_recommendations
                )
            
            try:
                # Check if we're already in an event loop
                try:
                    loop = asyncio.get_running_loop()
                    # We're in an event loop, need to handle differently
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(asyncio.run, _execute_workflow())
                        result = future.result(timeout=120)  # 2 minute timeout
                except RuntimeError:
                    # No event loop running, safe to use asyncio.run()
                    result = asyncio.run(_execute_workflow())
                
                # Return the formatted response
                if result.formatted_response:
                    return result.formatted_response
                elif result.success:
                    return f"Found {result.restaurants_found} restaurants in Central district, but formatting failed."
                else:
                    return result.error_message or "Central district search workflow failed."
                    
            except Exception as e:
                logger.error(f"Error in Central district workflow tool: {e}")
                return workflow._format_error_response(e, meal_types)
        
        # Ensure the tool has the correct attributes
        if not hasattr(search_central_district_restaurants, 'name'):
            search_central_district_restaurants.name = "search_central_district_restaurants"
        if not hasattr(search_central_district_restaurants, 'description'):
            search_central_district_restaurants.description = """Complete workflow for searching restaurants in Hong Kong's Central district with intelligent recommendations."""
        
        tools = [search_central_district_restaurants]
        
        logger.info(f"Created {len(tools)} Central district workflow tools")
        return tools
        
    except Exception as e:
        logger.error(f"Failed to create Central district workflow tools: {e}")
        return []


def create_restaurant_recommendation_tools(environment: str = None, 
                                         base_url: str = None, 
                                         auth_token: str = None) -> List:
    """
    Create restaurant recommendation tools using Gateway HTTP client.
    
    This function creates Strands Agent Tool objects that use the Gateway HTTP Client
    to communicate with the agentcore-gateway-mcp-tools service for restaurant recommendations.
    
    Args:
        environment: Target environment (development, staging, production)
        base_url: Override base URL for gateway service
        auth_token: JWT authentication token (optional)
        
    Returns:
        List of Tool objects for restaurant recommendation functionality
    """
    try:
        # Initialize the tools manager
        tools_manager = GatewayToolsManager(
            environment=environment,
            base_url=base_url,
            auth_token=auth_token
        )
        
        def recommend_restaurants_tool(restaurants: List[Dict[str, Any]], 
                                     ranking_method: str = "sentiment_likes") -> str:
            """
            Get intelligent restaurant recommendations with sentiment-based ranking.
            
            This tool calls the gateway's recommendation endpoint to analyze restaurant
            sentiment data and provide ranked recommendations with detailed analysis.
            
            Args:
                restaurants: List of restaurant objects with sentiment data
                ranking_method: Ranking method ("sentiment_likes" or "combined_sentiment")
                
            Returns:
                JSON string with recommendation and analysis
            """
            operation = "recommend_restaurants"
            parameters = {"ranking_method": ranking_method, "restaurant_count": len(restaurants)}
            
            try:
                logger.info(f"Generating recommendations for {len(restaurants)} restaurants")
                
                # Validate input parameters
                if not restaurants:
                    raise GatewayValidationError("Restaurants list cannot be empty")
                
                if not isinstance(restaurants, list):
                    raise GatewayValidationError("Restaurants must be provided as a list")
                
                valid_ranking_methods = {"sentiment_likes", "combined_sentiment"}
                if ranking_method not in valid_ranking_methods:
                    raise GatewayValidationError(
                        f"Invalid ranking method: {ranking_method}. "
                        f"Valid methods are: {list(valid_ranking_methods)}"
                    )
                
                # Validate restaurant data structure
                for i, restaurant in enumerate(restaurants):
                    if not isinstance(restaurant, dict):
                        raise GatewayValidationError(f"Restaurant {i} must be a dictionary")
                    
                    # Check for required fields
                    required_fields = ["id", "name", "sentiment"]
                    missing_fields = [field for field in required_fields if field not in restaurant]
                    if missing_fields:
                        raise GatewayValidationError(
                            f"Restaurant {i} missing required fields: {missing_fields}"
                        )
                    
                    # Validate sentiment data
                    sentiment = restaurant.get("sentiment", {})
                    if not isinstance(sentiment, dict):
                        raise GatewayValidationError(f"Restaurant {i} sentiment must be a dictionary")
                    
                    sentiment_fields = ["likes", "dislikes", "neutral"]
                    missing_sentiment = [field for field in sentiment_fields if field not in sentiment]
                    if missing_sentiment:
                        raise GatewayValidationError(
                            f"Restaurant {i} sentiment missing fields: {missing_sentiment}"
                        )
                
                # Execute async operation
                async def _recommend():
                    return await tools_manager.client.recommend_restaurants(restaurants, ranking_method)
                
                result = asyncio.run(_recommend())
                
                # Check if the operation was successful
                if not result.get("success", True):
                    error_info = result.get("error", {})
                    raise GatewayServiceError(
                        message=error_info.get("message", "Unknown service error"),
                        status_code=error_info.get("status_code"),
                        response_data=result
                    )
                
                logger.info(f"Successfully generated recommendations using {ranking_method} method")
                return tools_manager._format_success_response(result)
                
            except Exception as e:
                logger.error(f"Error in {operation}: {e}")
                return tools_manager._format_error_response(e, operation, parameters)
        
        # Create tool function using the @tool decorator
        @tool(
            name="recommend_restaurants",
            description="""Analyze restaurant sentiment data and provide intelligent recommendations using Gateway HTTP API.
            
            This tool connects to the agentcore-gateway-mcp-tools service deployed in Bedrock AgentCore
            to analyze sentiment data (likes, dislikes, neutral) and provide ranked recommendations
            with detailed analysis and reasoning.
            
            The tool supports two ranking methods:
            - "sentiment_likes": Ranks restaurants by highest number of likes
            - "combined_sentiment": Ranks by combined positive sentiment (likes + neutral percentage)
            
            The tool returns comprehensive recommendation data including:
            - Top recommended restaurant with detailed information
            - List of candidate restaurants ranked by sentiment
            - Analysis summary with statistical insights
            - Ranking methodology explanation
            - Sentiment score distributions and averages
            
            Example restaurant object structure:
            {
                "id": "rest_001",
                "name": "Restaurant Name",
                "sentiment": {"likes": 85, "dislikes": 10, "neutral": 5},
                "address": "123 Main St",
                "district": "Central district"
            }
            """
        )
        def recommend_restaurants(restaurants: List[Dict[str, Any]], 
                                ranking_method: str = "sentiment_likes") -> str:
            """
            Analyze restaurant sentiment data and provide intelligent recommendations.
            
            Args:
                restaurants: List of restaurant objects with sentiment data
                          Each restaurant must have: id, name, sentiment (with likes, dislikes, neutral)
                ranking_method: Ranking method ("sentiment_likes" or "combined_sentiment")
                
            Returns:
                JSON string with recommendation and analysis
            """
            return recommend_restaurants_tool(restaurants, ranking_method)
        
        tools = [recommend_restaurants]
        
        logger.info(f"Created {len(tools)} restaurant recommendation tools using Gateway HTTP client")
        return tools
        
    except Exception as e:
        logger.error(f"Failed to create restaurant recommendation tools: {e}")
        return []


# Export main functions
__all__ = [
    'GatewayToolsManager',
    'create_restaurant_search_tools',
    'create_restaurant_recommendation_tools',
    'create_central_district_workflow_tools'
]