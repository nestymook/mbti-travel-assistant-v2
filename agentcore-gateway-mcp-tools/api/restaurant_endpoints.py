"""
Restaurant search API endpoints for AgentCore Gateway.

This module provides RESTful HTTP endpoints for restaurant search operations
that interface with the underlying MCP tools through the MCP client manager.
"""

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request
from typing import Dict, Any

from models.request_models import (
    DistrictSearchRequest,
    MealTypeSearchRequest,
    CombinedSearchRequest,
    RestaurantRecommendationRequest,
    SentimentAnalysisRequest
)
from models.response_models import (
    RestaurantSearchResponse,
    RecommendationResponse,
    SentimentAnalysisResponse,
    ErrorResponse
)
from services.mcp_client_manager import get_mcp_client_manager, MCPClientManager
from middleware.auth_middleware import get_current_user, UserContext

logger = structlog.get_logger(__name__)

# Create router for restaurant endpoints
router = APIRouter(
    prefix="/api/v1/restaurants",
    tags=["Restaurant Search"],
    responses={
        401: {"model": ErrorResponse, "description": "Authentication required"},
        403: {"model": ErrorResponse, "description": "Access forbidden"},
        422: {"model": ErrorResponse, "description": "Validation error"},
        503: {"model": ErrorResponse, "description": "MCP server unavailable"}
    }
)


@router.post(
    "/search/district",
    response_model=RestaurantSearchResponse,
    summary="Search restaurants by district",
    description="Search for restaurants in specific Hong Kong districts using the MCP search tool"
)
async def search_restaurants_by_district(
    request: DistrictSearchRequest,
    current_user: UserContext = Depends(get_current_user),
    mcp_client: MCPClientManager = Depends(get_mcp_client_manager)
) -> RestaurantSearchResponse:
    """
    Search for restaurants by district.
    
    This endpoint calls the search_restaurants_by_district MCP tool to find
    restaurants located in the specified Hong Kong districts.
    
    Args:
        request: District search request with list of districts
        current_user: Authenticated user context
        mcp_client: MCP client manager for server communication
        
    Returns:
        RestaurantSearchResponse: Search results with restaurant data
        
    Raises:
        HTTPException: If MCP server is unavailable or request fails
    """
    logger.info(
        "District search request",
        districts=request.districts,
        user_id=current_user.user_id,
        username=current_user.username
    )
    
    try:
        # Prepare user context for MCP call
        user_context = {
            "user_id": current_user.user_id,
            "username": current_user.username,
            "email": current_user.email,
            "token": current_user.token_claims.get("access_token")
        }
        
        # Call MCP tool
        result = await mcp_client.call_mcp_tool(
            server_name="restaurant-search",
            tool_name="search_restaurants_by_district",
            parameters={"districts": request.districts},
            user_context=user_context
        )
        
        logger.info(
            "District search completed",
            districts=request.districts,
            result_count=len(result.get("restaurants", [])),
            user_id=current_user.user_id
        )
        
        # Transform MCP result to match response model
        restaurants = result.get("restaurants", [])
        
        return RestaurantSearchResponse(
            success=True,
            restaurants=restaurants,
            metadata={
                "total_results": len(restaurants),
                "search_criteria": {"districts": request.districts},
                "execution_time_ms": 0.0,  # Will be populated by actual execution time
                "data_sources": ["mcp_restaurant_search"]
            }
        )
        
    except Exception as e:
        logger.error(
            "District search failed",
            districts=request.districts,
            error=str(e),
            user_id=current_user.user_id
        )
        
        # Check if it's an MCP server error
        if "MCP server" in str(e) or "unavailable" in str(e).lower():
            raise HTTPException(
                status_code=503,
                detail={
                    "type": "ServiceUnavailable",
                    "message": "Restaurant search service is temporarily unavailable",
                    "details": "Please try again in a few moments",
                    "retry_after": 30
                }
            )
        
        raise HTTPException(
            status_code=500,
            detail={
                "type": "InternalServerError",
                "message": "Restaurant search failed",
                "details": str(e)
            }
        )


@router.post(
    "/search/meal-type",
    response_model=RestaurantSearchResponse,
    summary="Search restaurants by meal type",
    description="Search for restaurants that serve specific meal types (breakfast, lunch, dinner)"
)
async def search_restaurants_by_meal_type(
    request: MealTypeSearchRequest,
    current_user: UserContext = Depends(get_current_user),
    mcp_client: MCPClientManager = Depends(get_mcp_client_manager)
) -> RestaurantSearchResponse:
    """
    Search for restaurants by meal type.
    
    This endpoint calls the search_restaurants_by_meal_type MCP tool to find
    restaurants that serve the specified meal types based on their operating hours.
    
    Args:
        request: Meal type search request with list of meal types
        current_user: Authenticated user context
        mcp_client: MCP client manager for server communication
        
    Returns:
        RestaurantSearchResponse: Search results with restaurant data
        
    Raises:
        HTTPException: If MCP server is unavailable or request fails
    """
    logger.info(
        "Meal type search request",
        meal_types=[mt.value for mt in request.meal_types],
        user_id=current_user.user_id,
        username=current_user.username
    )
    
    try:
        # Prepare user context for MCP call
        user_context = {
            "user_id": current_user.user_id,
            "username": current_user.username,
            "email": current_user.email,
            "token": current_user.token_claims.get("access_token")
        }
        
        # Convert enum values to strings for MCP call
        meal_types_str = [mt.value for mt in request.meal_types]
        
        # Call MCP tool
        result = await mcp_client.call_mcp_tool(
            server_name="restaurant-search",
            tool_name="search_restaurants_by_meal_type",
            parameters={"meal_types": meal_types_str},
            user_context=user_context
        )
        
        logger.info(
            "Meal type search completed",
            meal_types=meal_types_str,
            result_count=len(result.get("restaurants", [])),
            user_id=current_user.user_id
        )
        
        # Transform MCP result to match response model
        restaurants = result.get("restaurants", [])
        
        return RestaurantSearchResponse(
            success=True,
            restaurants=restaurants,
            metadata={
                "total_results": len(restaurants),
                "search_criteria": {"meal_types": meal_types_str},
                "execution_time_ms": 0.0,  # Will be populated by actual execution time
                "data_sources": ["mcp_restaurant_search"]
            }
        )
        
    except Exception as e:
        logger.error(
            "Meal type search failed",
            meal_types=[mt.value for mt in request.meal_types],
            error=str(e),
            user_id=current_user.user_id
        )
        
        # Check if it's an MCP server error
        if "MCP server" in str(e) or "unavailable" in str(e).lower():
            raise HTTPException(
                status_code=503,
                detail={
                    "type": "ServiceUnavailable",
                    "message": "Restaurant search service is temporarily unavailable",
                    "details": "Please try again in a few moments",
                    "retry_after": 30
                }
            )
        
        raise HTTPException(
            status_code=500,
            detail={
                "type": "InternalServerError",
                "message": "Restaurant search failed",
                "details": str(e)
            }
        )


@router.post(
    "/search/combined",
    response_model=RestaurantSearchResponse,
    summary="Search restaurants by combined criteria",
    description="Search for restaurants using both district and meal type filters"
)
async def search_restaurants_combined(
    request: CombinedSearchRequest,
    current_user: UserContext = Depends(get_current_user),
    mcp_client: MCPClientManager = Depends(get_mcp_client_manager)
) -> RestaurantSearchResponse:
    """
    Search for restaurants using combined criteria.
    
    This endpoint calls the search_restaurants_combined MCP tool to find
    restaurants that match both district and meal type criteria.
    
    Args:
        request: Combined search request with optional districts and meal types
        current_user: Authenticated user context
        mcp_client: MCP client manager for server communication
        
    Returns:
        RestaurantSearchResponse: Search results with restaurant data
        
    Raises:
        HTTPException: If MCP server is unavailable or request fails
    """
    logger.info(
        "Combined search request",
        districts=request.districts,
        meal_types=[mt.value for mt in request.meal_types] if request.meal_types else None,
        user_id=current_user.user_id,
        username=current_user.username
    )
    
    try:
        # Prepare user context for MCP call
        user_context = {
            "user_id": current_user.user_id,
            "username": current_user.username,
            "email": current_user.email,
            "token": current_user.token_claims.get("access_token")
        }
        
        # Prepare parameters
        parameters = {}
        if request.districts:
            parameters["districts"] = request.districts
        if request.meal_types:
            parameters["meal_types"] = [mt.value for mt in request.meal_types]
        
        # Call MCP tool
        result = await mcp_client.call_mcp_tool(
            server_name="restaurant-search",
            tool_name="search_restaurants_combined",
            parameters=parameters,
            user_context=user_context
        )
        
        logger.info(
            "Combined search completed",
            districts=request.districts,
            meal_types=[mt.value for mt in request.meal_types] if request.meal_types else None,
            result_count=len(result.get("restaurants", [])),
            user_id=current_user.user_id
        )
        
        # Transform MCP result to match response model
        restaurants = result.get("restaurants", [])
        search_criteria = {}
        if request.districts:
            search_criteria["districts"] = request.districts
        if request.meal_types:
            search_criteria["meal_types"] = [mt.value for mt in request.meal_types]
        
        return RestaurantSearchResponse(
            success=True,
            restaurants=restaurants,
            metadata={
                "total_results": len(restaurants),
                "search_criteria": search_criteria,
                "execution_time_ms": 0.0,  # Will be populated by actual execution time
                "data_sources": ["mcp_restaurant_search"]
            }
        )
        
    except Exception as e:
        logger.error(
            "Combined search failed",
            districts=request.districts,
            meal_types=[mt.value for mt in request.meal_types] if request.meal_types else None,
            error=str(e),
            user_id=current_user.user_id
        )
        
        # Check if it's an MCP server error
        if "MCP server" in str(e) or "unavailable" in str(e).lower():
            raise HTTPException(
                status_code=503,
                detail={
                    "type": "ServiceUnavailable",
                    "message": "Restaurant search service is temporarily unavailable",
                    "details": "Please try again in a few moments",
                    "retry_after": 30
                }
            )
        
        raise HTTPException(
            status_code=500,
            detail={
                "type": "InternalServerError",
                "message": "Restaurant search failed",
                "details": str(e)
            }
        )


@router.post(
    "/recommend",
    response_model=RecommendationResponse,
    summary="Get restaurant recommendations",
    description="Analyze restaurant sentiment data and provide intelligent recommendations"
)
async def recommend_restaurants(
    request: RestaurantRecommendationRequest,
    current_user: UserContext = Depends(get_current_user),
    mcp_client: MCPClientManager = Depends(get_mcp_client_manager)
) -> RecommendationResponse:
    """
    Get restaurant recommendations based on sentiment analysis.
    
    This endpoint calls the recommend_restaurants MCP tool to analyze
    restaurant sentiment data and provide ranked recommendations.
    
    Args:
        request: Restaurant recommendation request with restaurant data
        current_user: Authenticated user context
        mcp_client: MCP client manager for server communication
        
    Returns:
        RestaurantRecommendationResponse: Recommendations with analysis
        
    Raises:
        HTTPException: If MCP server is unavailable or request fails
    """
    logger.info(
        "Restaurant recommendation request",
        restaurant_count=len(request.restaurants),
        ranking_method=request.ranking_method.value,
        user_id=current_user.user_id,
        username=current_user.username
    )
    
    try:
        # Prepare user context for MCP call
        user_context = {
            "user_id": current_user.user_id,
            "username": current_user.username,
            "email": current_user.email,
            "token": current_user.token_claims.get("access_token")
        }
        
        # Convert restaurant data to dict format for MCP call
        restaurants_data = [restaurant.model_dump() for restaurant in request.restaurants]
        
        # Call MCP tool
        result = await mcp_client.call_mcp_tool(
            server_name="restaurant-reasoning",
            tool_name="recommend_restaurants",
            parameters={
                "restaurants": restaurants_data,
                "ranking_method": request.ranking_method.value
            },
            user_context=user_context
        )
        
        logger.info(
            "Restaurant recommendation completed",
            restaurant_count=len(request.restaurants),
            ranking_method=request.ranking_method.value,
            user_id=current_user.user_id
        )
        
        # Transform MCP result to match response model
        recommendation = result.get("recommendation", {})
        candidates = result.get("candidates", [])
        analysis_summary = result.get("analysis_summary", {})
        
        return RecommendationResponse(
            success=True,
            recommendation=recommendation,
            candidates=candidates,
            ranking_method=request.ranking_method.value,
            analysis_summary=analysis_summary
        )
        
    except Exception as e:
        logger.error(
            "Restaurant recommendation failed",
            restaurant_count=len(request.restaurants),
            ranking_method=request.ranking_method.value,
            error=str(e),
            user_id=current_user.user_id
        )
        
        # Check if it's an MCP server error
        if "MCP server" in str(e) or "unavailable" in str(e).lower():
            raise HTTPException(
                status_code=503,
                detail={
                    "type": "ServiceUnavailable",
                    "message": "Restaurant reasoning service is temporarily unavailable",
                    "details": "Please try again in a few moments",
                    "retry_after": 30
                }
            )
        
        raise HTTPException(
            status_code=500,
            detail={
                "type": "InternalServerError",
                "message": "Restaurant recommendation failed",
                "details": str(e)
            }
        )


@router.post(
    "/analyze",
    response_model=SentimentAnalysisResponse,
    summary="Analyze restaurant sentiment",
    description="Perform sentiment analysis on restaurant data without providing recommendations"
)
async def analyze_restaurant_sentiment(
    request: SentimentAnalysisRequest,
    current_user: UserContext = Depends(get_current_user),
    mcp_client: MCPClientManager = Depends(get_mcp_client_manager)
) -> SentimentAnalysisResponse:
    """
    Analyze restaurant sentiment data.
    
    This endpoint calls the analyze_restaurant_sentiment MCP tool to perform
    statistical analysis on restaurant sentiment data without selecting recommendations.
    
    Args:
        request: Sentiment analysis request with restaurant data
        current_user: Authenticated user context
        mcp_client: MCP client manager for server communication
        
    Returns:
        SentimentAnalysisResponse: Sentiment analysis results
        
    Raises:
        HTTPException: If MCP server is unavailable or request fails
    """
    logger.info(
        "Restaurant sentiment analysis request",
        restaurant_count=len(request.restaurants),
        user_id=current_user.user_id,
        username=current_user.username
    )
    
    try:
        # Prepare user context for MCP call
        user_context = {
            "user_id": current_user.user_id,
            "username": current_user.username,
            "email": current_user.email,
            "token": current_user.token_claims.get("access_token")
        }
        
        # Convert restaurant data to dict format for MCP call
        restaurants_data = [restaurant.model_dump() for restaurant in request.restaurants]
        
        # Call MCP tool
        result = await mcp_client.call_mcp_tool(
            server_name="restaurant-reasoning",
            tool_name="analyze_restaurant_sentiment",
            parameters={"restaurants": restaurants_data},
            user_context=user_context
        )
        
        logger.info(
            "Restaurant sentiment analysis completed",
            restaurant_count=len(request.restaurants),
            user_id=current_user.user_id
        )
        
        # Transform MCP result to match response model
        sentiment_analysis = result.get("sentiment_analysis", {})
        restaurant_count = result.get("restaurant_count", len(request.restaurants))
        ranking_method = result.get("ranking_method", "sentiment_likes")
        
        return SentimentAnalysisResponse(
            success=True,
            sentiment_analysis=sentiment_analysis,
            restaurant_count=restaurant_count,
            ranking_method=ranking_method
        )
        
    except Exception as e:
        logger.error(
            "Restaurant sentiment analysis failed",
            restaurant_count=len(request.restaurants),
            error=str(e),
            user_id=current_user.user_id
        )
        
        # Check if it's an MCP server error
        if "MCP server" in str(e) or "unavailable" in str(e).lower():
            raise HTTPException(
                status_code=503,
                detail={
                    "type": "ServiceUnavailable",
                    "message": "Restaurant reasoning service is temporarily unavailable",
                    "details": "Please try again in a few moments",
                    "retry_after": 30
                }
            )
        
        raise HTTPException(
            status_code=500,
            detail={
                "type": "InternalServerError",
                "message": "Restaurant sentiment analysis failed",
                "details": str(e)
            }
        )