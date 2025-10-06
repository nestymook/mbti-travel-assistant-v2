"""
Restaurant Reasoning Tool with AgentCore Integration

This module provides a restaurant reasoning tool that uses direct AgentCore Runtime API calls
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
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from datetime import datetime

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
    monitor_restaurant_reasoning,
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
class RecommendationResult:
    """Result from restaurant reasoning."""
    recommendations: List[Dict]
    reasoning: str
    confidence_score: float
    mbti_analysis: Dict
    execution_time_ms: int
    success: bool = True
    error_message: Optional[str] = None


class RestaurantReasoningTool:
    """Tool for restaurant reasoning using AgentCore agent."""
    
    def __init__(
        self, 
        runtime_client: AgentCoreRuntimeClient,
        reasoning_agent_arn: str,
        auth_manager: Optional[AuthenticationManager] = None
    ):
        """
        Initialize restaurant reasoning tool.
        
        Args:
            runtime_client: AgentCore Runtime client
            reasoning_agent_arn: ARN of the restaurant reasoning agent
            auth_manager: Authentication manager (optional)
        """
        self.runtime_client = runtime_client
        self.reasoning_agent_arn = reasoning_agent_arn
        self.auth_manager = auth_manager
        
        # Initialize monitoring middleware
        self.monitoring_middleware = get_monitoring_middleware()
        
        # Performance tracking (legacy - now handled by monitoring service)
        self.call_count = 0
        self.error_count = 0
        self.total_response_time = 0.0
        
        logger.info(f"Restaurant reasoning tool initialized with agent: {reasoning_agent_arn}")
    
    async def get_recommendations(
        self, 
        restaurants: List[Dict], 
        mbti_type: str, 
        preferences: Dict,
        ranking_method: str = "sentiment_likes",
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        request_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        enable_caching: bool = True,
        cache_ttl_override: Optional[int] = None
    ) -> RecommendationResult:
        """
        Get MBTI-based restaurant recommendations using AgentCore agent.
        
        Args:
            restaurants: List of restaurant objects with sentiment data
            mbti_type: MBTI personality type (e.g., "ENFP", "INTJ")
            preferences: User preferences dictionary
            ranking_method: Ranking method ("sentiment_likes" or "combined_sentiment")
            user_id: Optional user ID for error context
            session_id: Optional session ID for error context
            request_id: Optional request ID for error context
            correlation_id: Optional correlation ID for request tracing
            
        Returns:
            RecommendationResult object
        """
        # Use monitoring context manager for comprehensive observability
        async with self.monitoring_middleware.monitoring_context(
            operation_type=AgentOperationType.RESTAURANT_REASONING,
            agent_arn=self.reasoning_agent_arn,
            user_id=user_id,
            session_id=session_id,
            request_id=request_id,
            correlation_id=correlation_id
        ) as context:
            start_time = time.time()
            operation = "get_recommendations"
            
            try:
                # Validate input parameters
                if not restaurants:
                    raise ValueError("Restaurants list cannot be empty")
                
                if not isinstance(restaurants, list):
                    raise ValueError("Restaurants must be provided as a list")
                
                if not mbti_type or not isinstance(mbti_type, str):
                    raise ValueError("MBTI type must be a non-empty string")
                
                # Validate MBTI type format
                mbti_type = mbti_type.upper().strip()
                if len(mbti_type) != 4 or not all(c in 'EINTFPJS' for c in mbti_type):
                    raise ValueError(f"Invalid MBTI type format: {mbti_type}")
                
                if not isinstance(preferences, dict):
                    raise ValueError("Preferences must be provided as a dictionary")
                
                # Validate ranking method
                valid_ranking_methods = {"sentiment_likes", "combined_sentiment"}
                if ranking_method not in valid_ranking_methods:
                    raise ValueError(
                        f"Invalid ranking method: {ranking_method}. "
                        f"Valid methods are: {list(valid_ranking_methods)}"
                    )
                
                # Validate restaurant data structure
                for i, restaurant in enumerate(restaurants):
                    if not isinstance(restaurant, dict):
                        raise ValueError(f"Restaurant {i} must be a dictionary")
                    
                    # Check for required fields
                    required_fields = ["name", "sentiment"]
                    missing_fields = [field for field in required_fields if field not in restaurant]
                    if missing_fields:
                        logger.warning(f"Restaurant {i} missing recommended fields: {missing_fields}")
                    
                    # Validate sentiment data if present
                    if "sentiment" in restaurant:
                        sentiment = restaurant["sentiment"]
                        if not isinstance(sentiment, dict):
                            raise ValueError(f"Restaurant {i} sentiment must be a dictionary")
                        
                        # Check for sentiment fields (not strictly required, but recommended)
                        sentiment_fields = ["likes", "dislikes", "neutral"]
                        missing_sentiment = [field for field in sentiment_fields if field not in sentiment]
                        if missing_sentiment:
                            logger.warning(f"Restaurant {i} sentiment missing fields: {missing_sentiment}")
                
                # Prepare input for AgentCore agent
                reasoning_request = {
                    "action": "get_recommendations",
                    "parameters": {
                        "restaurants": restaurants,
                        "mbti_type": mbti_type,
                        "preferences": preferences,
                        "ranking_method": ranking_method
                    }
                }
                
                input_text = json.dumps(reasoning_request, ensure_ascii=False)
                
                logger.info(f"Getting recommendations for {len(restaurants)} restaurants, MBTI: {mbti_type} [correlation_id: {context.correlation_id}]")
                
                # Log invocation start
                self.monitoring_middleware.monitoring_service.log_agent_invocation_start(
                    agent_arn=self.reasoning_agent_arn,
                    operation_type=AgentOperationType.RESTAURANT_REASONING,
                    input_text=input_text,
                    session_id=session_id,
                    user_id=user_id,
                    request_id=request_id,
                    correlation_id=context.correlation_id
                )
                
                # Invoke AgentCore agent with performance optimizations
                response = await self.runtime_client.invoke_agent(
                    agent_arn=self.reasoning_agent_arn,
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
                
                # Log successful invocation result
                self.monitoring_middleware.monitoring_service.log_agent_invocation_result(
                    correlation_id=context.correlation_id,
                    agent_arn=self.reasoning_agent_arn,
                    operation_type=AgentOperationType.RESTAURANT_REASONING,
                    response=response
                )
                
                # Update performance metrics
                self.call_count += 1
                self.total_response_time += execution_time_ms
                
                logger.info(f"Successfully generated recommendations for MBTI type: {mbti_type} [correlation_id: {context.correlation_id}]")
                
                return RecommendationResult(
                    recommendations=result_data.get('recommendations', []),
                    reasoning=result_data.get('reasoning', ''),
                    confidence_score=result_data.get('confidence_score', 0.0),
                    mbti_analysis=result_data.get('mbti_analysis', {}),
                    execution_time_ms=execution_time_ms,
                    success=True
                )
                
            except AgentCoreError as e:
                execution_time_ms = int((time.time() - start_time) * 1000)
                
                # Log error invocation result
                self.monitoring_middleware.monitoring_service.log_agent_invocation_result(
                    correlation_id=context.correlation_id,
                    agent_arn=self.reasoning_agent_arn,
                    operation_type=AgentOperationType.RESTAURANT_REASONING,
                    error=e
                )
                
                logger.error(f"AgentCore error in {operation}: {e} [correlation_id: {context.correlation_id}]")
                
                # Update performance metrics
                self.error_count += 1
                self.call_count += 1
                
                return RecommendationResult(
                    recommendations=[],
                    reasoning=f"AgentCore error: {str(e)}",
                    confidence_score=0.0,
                    mbti_analysis={},
                    execution_time_ms=execution_time_ms,
                    success=False,
                    error_message=str(e)
                )
                
            except Exception as e:
                execution_time_ms = int((time.time() - start_time) * 1000)
                
                # Log error invocation result
                self.monitoring_middleware.monitoring_service.log_agent_invocation_result(
                    correlation_id=context.correlation_id,
                    agent_arn=self.reasoning_agent_arn,
                    operation_type=AgentOperationType.RESTAURANT_REASONING,
                    error=e
                )
                
                logger.error(f"Unexpected error in {operation}: {e} [correlation_id: {context.correlation_id}]")
                
                # Update performance metrics
                self.error_count += 1
                self.call_count += 1
                
                return RecommendationResult(
                    recommendations=[],
                    reasoning=f"Error generating recommendations: {str(e)}",
                    confidence_score=0.0,
                    mbti_analysis={},
                    execution_time_ms=execution_time_ms,
                    success=False,
                    error_message=str(e)
                )
    
    async def analyze_restaurant_sentiment(
        self, 
        restaurants: List[Dict],
        ranking_method: str = "sentiment_likes",
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        request_id: Optional[str] = None,
        correlation_id: Optional[str] = None
    ) -> RecommendationResult:
        """
        Analyze restaurant sentiment data and provide rankings.
        
        Args:
            restaurants: List of restaurant objects with sentiment data
            ranking_method: Ranking method ("sentiment_likes" or "combined_sentiment")
            user_id: Optional user ID for error context
            session_id: Optional session ID for error context
            request_id: Optional request ID for error context
            correlation_id: Optional correlation ID for request tracing
            
        Returns:
            RecommendationResult object with sentiment analysis
        """
        # Use monitoring context manager for comprehensive observability
        async with self.monitoring_middleware.monitoring_context(
            operation_type=AgentOperationType.RESTAURANT_REASONING,
            agent_arn=self.reasoning_agent_arn,
            user_id=user_id,
            session_id=session_id,
            request_id=request_id,
            correlation_id=correlation_id
        ) as context:
            start_time = time.time()
            operation = "analyze_restaurant_sentiment"
            
            try:
                # Validate input parameters
                if not restaurants:
                    raise ValueError("Restaurants list cannot be empty")
                
                if not isinstance(restaurants, list):
                    raise ValueError("Restaurants must be provided as a list")
                
                # Validate ranking method
                valid_ranking_methods = {"sentiment_likes", "combined_sentiment"}
                if ranking_method not in valid_ranking_methods:
                    raise ValueError(
                        f"Invalid ranking method: {ranking_method}. "
                        f"Valid methods are: {list(valid_ranking_methods)}"
                    )
                
                # Prepare input for AgentCore agent
                analysis_request = {
                    "action": "analyze_restaurant_sentiment",
                    "parameters": {
                        "restaurants": restaurants,
                        "ranking_method": ranking_method
                    }
                }
                
                input_text = json.dumps(analysis_request, ensure_ascii=False)
                
                logger.info(f"Analyzing sentiment for {len(restaurants)} restaurants")
                
                # Invoke AgentCore agent
                response = await self.runtime_client.invoke_agent(
                    agent_arn=self.reasoning_agent_arn,
                    input_text=input_text
                )
                
                # Parse response
                result_data = self._parse_agent_response(response)
                
                execution_time_ms = int((time.time() - start_time) * 1000)
                
                # Update performance metrics
                self.call_count += 1
                self.total_response_time += execution_time_ms
                
                logger.info(f"Successfully analyzed sentiment using {ranking_method} method")
                
                return RecommendationResult(
                    recommendations=result_data.get('recommendations', []),
                    reasoning=result_data.get('reasoning', ''),
                    confidence_score=result_data.get('confidence_score', 0.0),
                    mbti_analysis=result_data.get('analysis', {}),
                    execution_time_ms=execution_time_ms,
                    success=True
                )
                
            except Exception as e:
                execution_time_ms = int((time.time() - start_time) * 1000)
                self.error_count += 1
                self.call_count += 1  # Increment call count even for errors
                
                logger.error(f"Error in {operation}: {e}")
                
                return RecommendationResult(
                    recommendations=[],
                    reasoning=f"Error analyzing sentiment: {str(e)}",
                    confidence_score=0.0,
                    mbti_analysis={},
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
                'recommendations': [],
                'reasoning': response.output_text,
                'confidence_score': 0.0,
                'mbti_analysis': {},
                'metadata': {
                    'raw_response': response.output_text,
                    'session_id': response.session_id,
                    'agent_metadata': response.metadata
                }
            }
            
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse agent response as JSON: {e}")
            return {
                'recommendations': [],
                'reasoning': response.output_text,
                'confidence_score': 0.0,
                'mbti_analysis': {},
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
                'recommendations': [],
                'reasoning': f"Error parsing response: {str(e)}",
                'confidence_score': 0.0,
                'mbti_analysis': {},
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
                "Restaurant recommendation service is temporarily unavailable. "
                "Please try again later."
            )
            error_response["error"]["fallback"] = (
                "I can still help with general restaurant search and travel planning."
            )
        elif isinstance(error, AuthenticationError):
            error_response["error"]["user_message"] = (
                "Authentication issue with restaurant recommendation service."
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
                "An unexpected error occurred while generating restaurant recommendations."
            )
            error_response["error"]["fallback"] = (
                "Please try rephrasing your request or ask about other travel topics."
            )
        
        return json.dumps(error_response, ensure_ascii=False, indent=2)
    
    def _format_success_response(self, result: RecommendationResult) -> str:
        """
        Format successful responses for backward compatibility.
        
        Args:
            result: The successful result from the reasoning
            
        Returns:
            JSON string with formatted result
        """
        response = {
            "success": True,
            "recommendations": result.recommendations,
            "reasoning": result.reasoning,
            "confidence_score": result.confidence_score,
            "mbti_analysis": result.mbti_analysis,
            "execution_time_ms": result.execution_time_ms
        }
        
        return json.dumps(response, ensure_ascii=False, indent=2)
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for the tool."""
        avg_response_time = (
            self.total_response_time / max(self.call_count, 1)
            if self.call_count > 0 else 0
        )
        
        return {
            "total_calls": self.call_count,
            "total_errors": self.error_count,
            "error_rate": self.error_count / max(self.call_count, 1),
            "average_response_time_ms": avg_response_time,
            "agent_arn": self.reasoning_agent_arn
        }
    
    # Backward compatibility methods that return JSON strings
    def recommend_restaurants_tool(
        self, 
        restaurants: List[Dict[str, Any]], 
        ranking_method: str = "sentiment_likes"
    ) -> str:
        """
        Get intelligent restaurant recommendations (backward compatible interface).
        
        Args:
            restaurants: List of restaurant objects with sentiment data
            ranking_method: Ranking method ("sentiment_likes" or "combined_sentiment")
            
        Returns:
            JSON string with recommendation and analysis
        """
        try:
            # Execute async operation
            async def _recommend():
                return await self.analyze_restaurant_sentiment(restaurants, ranking_method)
            
            # Handle event loop properly
            try:
                loop = asyncio.get_running_loop()
                # We're in an event loop, need to handle differently
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, _recommend())
                    result = future.result(timeout=120)  # 2 minute timeout
            except RuntimeError:
                # No event loop running, safe to use asyncio.run()
                result = asyncio.run(_recommend())
            
            if result.success:
                return self._format_success_response(result)
            else:
                return self._format_error_response(
                    Exception(result.error_message),
                    "recommend_restaurants",
                    {"ranking_method": ranking_method, "restaurant_count": len(restaurants)}
                )
                
        except Exception as e:
            return self._format_error_response(
                e,
                "recommend_restaurants",
                {"ranking_method": ranking_method, "restaurant_count": len(restaurants)}
            )
    
    def get_mbti_recommendations_tool(
        self, 
        restaurants: List[Dict], 
        mbti_type: str, 
        preferences: Dict,
        ranking_method: str = "sentiment_likes"
    ) -> str:
        """
        Get MBTI-based restaurant recommendations (backward compatible interface).
        
        Args:
            restaurants: List of restaurant objects with sentiment data
            mbti_type: MBTI personality type (e.g., "ENFP", "INTJ")
            preferences: User preferences dictionary
            ranking_method: Ranking method ("sentiment_likes" or "combined_sentiment")
            
        Returns:
            JSON string with MBTI-based recommendations and analysis
        """
        try:
            # Execute async operation
            async def _recommend():
                return await self.get_recommendations(restaurants, mbti_type, preferences, ranking_method)
            
            # Handle event loop properly
            try:
                loop = asyncio.get_running_loop()
                # We're in an event loop, need to handle differently
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, _recommend())
                    result = future.result(timeout=120)  # 2 minute timeout
            except RuntimeError:
                # No event loop running, safe to use asyncio.run()
                result = asyncio.run(_recommend())
            
            if result.success:
                return self._format_success_response(result)
            else:
                return self._format_error_response(
                    Exception(result.error_message),
                    "get_mbti_recommendations",
                    {
                        "mbti_type": mbti_type, 
                        "ranking_method": ranking_method, 
                        "restaurant_count": len(restaurants)
                    }
                )
                
        except Exception as e:
            return self._format_error_response(
                e,
                "get_mbti_recommendations",
                {
                    "mbti_type": mbti_type, 
                    "ranking_method": ranking_method, 
                    "restaurant_count": len(restaurants)
                }
            )


def create_restaurant_reasoning_tools(
    runtime_client: AgentCoreRuntimeClient,
    reasoning_agent_arn: str,
    auth_manager: Optional[AuthenticationManager] = None
) -> List:
    """
    Create restaurant reasoning tools using AgentCore Runtime API.
    
    This function creates Strands Agent tools that use the AgentCore Runtime client
    to communicate directly with the restaurant reasoning agent.
    
    Args:
        runtime_client: AgentCore Runtime client
        reasoning_agent_arn: ARN of the restaurant reasoning agent
        auth_manager: Authentication manager (optional)
        
    Returns:
        List of tool functions for restaurant reasoning functionality
    """
    try:
        # Initialize the restaurant reasoning tool
        reasoning_tool = RestaurantReasoningTool(
            runtime_client=runtime_client,
            reasoning_agent_arn=reasoning_agent_arn,
            auth_manager=auth_manager
        )
        
        # Create tool functions using the @tool decorator
        @tool(
            name="recommend_restaurants",
            description="""Analyze restaurant sentiment data and provide intelligent recommendations using AgentCore Runtime API.
            
            This tool connects directly to the restaurant reasoning agent deployed in Bedrock AgentCore
            to analyze sentiment data (likes, dislikes, neutral) and provide ranked recommendations
            with detailed analysis and reasoning.
            
            The tool supports two ranking methods:
            - "sentiment_likes": Ranks restaurants by highest number of likes
            - "combined_sentiment": Ranks by combined positive sentiment (likes + neutral percentage)
            
            The tool returns comprehensive recommendation data including:
            - Top recommended restaurant with detailed information
            - List of candidate restaurants ranked by sentiment
            - Detailed sentiment analysis and reasoning
            - Confidence score for the recommendations
            - Execution metadata and performance metrics
            
            Input restaurants must include sentiment data with 'likes', 'dislikes', and 'neutral' counts.
            The tool handles missing or invalid data gracefully with appropriate error messages.
            """
        )
        def recommend_restaurants(
            restaurants: List[Dict[str, Any]], 
            ranking_method: str = "sentiment_likes"
        ) -> str:
            """
            Analyze restaurant sentiment data and provide intelligent recommendations.
            
            Args:
                restaurants: List of restaurant objects with sentiment data
                ranking_method: Ranking method ("sentiment_likes" or "combined_sentiment")
                
            Returns:
                JSON string with recommendation and analysis
            """
            return reasoning_tool.recommend_restaurants_tool(restaurants, ranking_method)
        
        @tool(
            name="get_mbti_recommendations",
            description="""Generate MBTI personality-based restaurant recommendations using AgentCore Runtime API.
            
            This tool connects directly to the restaurant reasoning agent to provide personalized
            restaurant recommendations based on MBTI personality types and user preferences.
            
            The tool analyzes:
            - MBTI personality traits and dining preferences
            - Restaurant sentiment data and customer feedback
            - User-specified preferences and requirements
            - Cultural and cuisine compatibility factors
            
            Supported MBTI types: All 16 types (ENFP, INTJ, ESFJ, etc.)
            
            The tool returns:
            - Personalized restaurant recommendations with MBTI analysis
            - Detailed reasoning for each recommendation
            - Personality-based dining insights and tips
            - Confidence scores and recommendation rankings
            - Cultural and cuisine compatibility analysis
            
            The recommendations consider MBTI traits such as:
            - Extroversion vs Introversion (social dining preferences)
            - Sensing vs Intuition (traditional vs innovative cuisine)
            - Thinking vs Feeling (logical vs emotional dining choices)
            - Judging vs Perceiving (structured vs flexible dining experiences)
            """
        )
        def get_mbti_recommendations(
            restaurants: List[Dict], 
            mbti_type: str, 
            preferences: Dict,
            ranking_method: str = "sentiment_likes"
        ) -> str:
            """
            Generate MBTI personality-based restaurant recommendations.
            
            Args:
                restaurants: List of restaurant objects with sentiment data
                mbti_type: MBTI personality type (e.g., "ENFP", "INTJ")
                preferences: User preferences dictionary
                ranking_method: Ranking method ("sentiment_likes" or "combined_sentiment")
                
            Returns:
                JSON string with MBTI-based recommendations and analysis
            """
            return reasoning_tool.get_mbti_recommendations_tool(
                restaurants, mbti_type, preferences, ranking_method
            )
        
        tools = [recommend_restaurants, get_mbti_recommendations]
        
        logger.info(f"Created {len(tools)} restaurant reasoning tools using AgentCore Runtime API")
        return tools
        
    except Exception as e:
        logger.error(f"Failed to create restaurant reasoning tools: {e}")
        return []


# Export main classes and functions
__all__ = [
    'RestaurantReasoningTool',
    'RecommendationResult',
    'create_restaurant_reasoning_tools'
]