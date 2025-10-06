"""
Central District Search Workflow for MBTI Travel Planner Agent with AgentCore Integration

This module implements a complete workflow for searching restaurants in Hong Kong's
Central district using direct AgentCore Runtime API calls instead of HTTP gateway
intermediaries. It provides better performance, reliability, and ecosystem integration.

The workflow follows the complete pipeline:
1. Search → Find restaurants in Central district using AgentCore search agent
2. Analyze → Process restaurant data and sentiment
3. Recommend → Generate intelligent recommendations using AgentCore reasoning agent
4. Format → Present results in user-friendly format

Key improvements in AgentCore version:
- Direct agent-to-agent communication via AgentCore Runtime API
- Parallel execution for independent operations
- Enhanced error handling with circuit breaker patterns
- Comprehensive monitoring and observability
- Performance optimizations with connection pooling

Requirements covered: 2.4, 7.4, 8.2, 8.3
"""

import json
import logging
import asyncio
import time
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

from .agentcore_runtime_client import AgentCoreRuntimeClient, AgentCoreError, AuthenticationError, AgentInvocationError
from .authentication_manager import AuthenticationManager, CognitoConfig as AuthCognitoConfig
from .restaurant_search_tool import RestaurantSearchTool, RestaurantSearchResult
from .restaurant_reasoning_tool import RestaurantReasoningTool, RecommendationResult
from config.agentcore_environment_config import load_agentcore_environment_config, EnvironmentConfig

# Import monitoring middleware
from .agentcore_monitoring_middleware import (
    monitor_central_district_workflow,
    get_monitoring_middleware,
    AgentOperationType
)

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class WorkflowResult:
    """Result of the Central district search workflow."""
    success: bool
    restaurants_found: int
    recommendations: Optional[Dict[str, Any]] = None
    formatted_response: Optional[str] = None
    error_message: Optional[str] = None
    partial_results: bool = False
    execution_time: Optional[float] = None
    # New fields for AgentCore integration
    search_execution_time_ms: Optional[int] = None
    reasoning_execution_time_ms: Optional[int] = None
    parallel_execution: bool = False
    agent_performance_metrics: Optional[Dict[str, Any]] = None


class CentralDistrictWorkflow:
    """
    Complete workflow for Central district restaurant search and recommendations using AgentCore.
    
    This class implements the full pipeline from search to formatted user response,
    using direct AgentCore Runtime API calls for better performance and reliability.
    Features parallel execution, comprehensive error handling, and monitoring.
    """
    
    CENTRAL_DISTRICT_NAMES = [
        "Central district",
        "Central",
        "Central District"
    ]
    
    def __init__(self, environment: str = None, config: EnvironmentConfig = None):
        """
        Initialize the Central district workflow with AgentCore integration.
        
        Args:
            environment: Target environment (development, staging, production)
            config: Pre-loaded environment configuration (optional)
        """
        # Load configuration
        if config:
            self.config = config
        else:
            self.config = load_agentcore_environment_config(environment)
        
        # Convert environment config's CognitoConfig to authentication manager's CognitoConfig
        auth_cognito_config = AuthCognitoConfig(
            user_pool_id=self.config.cognito.user_pool_id,
            client_id=self.config.cognito.client_id,
            client_secret=self.config.cognito.client_secret,
            region=self.config.cognito.region,
            discovery_url=self.config.cognito.discovery_url
        )
        
        # Initialize authentication manager
        self.auth_manager = AuthenticationManager(auth_cognito_config)
        
        # Initialize AgentCore Runtime client
        from .agentcore_runtime_client import RetryConfig, ConnectionConfig
        
        retry_config = RetryConfig(
            max_retries=self.config.agentcore.max_retries,
            base_delay=1.0,
            max_delay=60.0
        )
        
        connection_config = ConnectionConfig(
            timeout_seconds=self.config.agentcore.timeout_seconds,
            max_connections=self.config.performance.max_connections,
            max_connections_per_host=self.config.performance.max_connections_per_host
        )
        
        self.runtime_client = AgentCoreRuntimeClient(
            region=self.config.agentcore.region,
            retry_config=retry_config,
            connection_config=connection_config
        )
        
        # Initialize tools
        self.search_tool = RestaurantSearchTool(
            runtime_client=self.runtime_client,
            search_agent_arn=self.config.agentcore.restaurant_search_agent_arn,
            auth_manager=self.auth_manager
        )
        
        self.reasoning_tool = RestaurantReasoningTool(
            runtime_client=self.runtime_client,
            reasoning_agent_arn=self.config.agentcore.restaurant_reasoning_agent_arn,
            auth_manager=self.auth_manager
        )
        
        # Initialize monitoring middleware
        self.monitoring_middleware = get_monitoring_middleware()
        
        # Performance tracking (legacy - now handled by monitoring service)
        self.workflow_call_count = 0
        self.workflow_error_count = 0
        self.total_workflow_time = 0.0
        
        logger.info(f"Central District Workflow initialized for {self.config.environment} environment")
        logger.info(f"Using search agent: {self.config.agentcore.restaurant_search_agent_arn}")
        logger.info(f"Using reasoning agent: {self.config.agentcore.restaurant_reasoning_agent_arn}")
    
    async def initialize_authentication(self) -> None:
        """Initialize authentication for AgentCore agents."""
        try:
            # Ensure authentication manager has valid token
            await self.auth_manager.get_valid_token()
            logger.info("Authentication initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize authentication: {e}")
            raise AuthenticationError(f"Authentication initialization failed: {e}")
    
    async def execute_complete_workflow(self, 
                                      meal_types: Optional[List[str]] = None,
                                      include_recommendations: bool = True,
                                      max_results: int = 20,
                                      mbti_type: Optional[str] = None,
                                      preferences: Optional[Dict[str, Any]] = None,
                                      user_id: Optional[str] = None,
                                      session_id: Optional[str] = None,
                                      request_id: Optional[str] = None,
                                      correlation_id: Optional[str] = None) -> WorkflowResult:
        """
        Execute the complete Central district search workflow using AgentCore agents.
        
        This method implements the full pipeline with parallel execution where possible:
        1. Search for restaurants in Central district using AgentCore search agent
        2. Optionally filter by meal types
        3. Generate recommendations using AgentCore reasoning agent (parallel when possible)
        4. Format user-friendly response with comprehensive monitoring
        
        Args:
            meal_types: Optional meal type filters (breakfast, lunch, dinner)
            include_recommendations: Whether to generate recommendations
            max_results: Maximum number of results to process
            mbti_type: Optional MBTI personality type for personalized recommendations
            preferences: Optional user preferences for recommendations
            user_id: Optional user ID for error context
            session_id: Optional session ID for error context
            request_id: Optional request ID for error context
            correlation_id: Optional correlation ID for request tracing
            
        Returns:
            WorkflowResult with complete pipeline results and performance metrics
        """
        # Use monitoring context manager for comprehensive observability
        async with self.monitoring_middleware.monitoring_context(
            operation_type=AgentOperationType.CENTRAL_DISTRICT_WORKFLOW,
            agent_arn="central_district_workflow",
            user_id=user_id,
            session_id=session_id,
            request_id=request_id,
            correlation_id=correlation_id
        ) as context:
            start_time = time.time()
            workflow_start = datetime.now()
            
            try:
            # Initialize authentication
            await self.initialize_authentication()
            
            # Update performance tracking
            self.workflow_call_count += 1
            
            logger.info(f"Starting AgentCore Central district workflow with meal_types={meal_types} [correlation_id: {context.correlation_id}]")
            logger.info(f"Parallel execution enabled: {self.config.performance.enable_parallel_execution}")
            
            # Step 1: Search for restaurants in Central district
            search_result = await self._search_central_restaurants_agentcore(meal_types)
            
            if not search_result.success:
                return WorkflowResult(
                    success=False,
                    restaurants_found=0,
                    error_message=search_result.error_message,
                    execution_time=(datetime.now() - workflow_start).total_seconds(),
                    search_execution_time_ms=search_result.execution_time_ms
                )
            
            restaurants = search_result.restaurants
            
            # Handle no results case
            if not restaurants:
                formatted_response = self._format_no_results_response(meal_types)
                return WorkflowResult(
                    success=True,
                    restaurants_found=0,
                    formatted_response=formatted_response,
                    execution_time=(datetime.now() - workflow_start).total_seconds(),
                    search_execution_time_ms=search_result.execution_time_ms
                )
            
            # Limit results if needed
            partial_results = False
            if len(restaurants) > max_results:
                restaurants = restaurants[:max_results]
                partial_results = True
                logger.info(f"Limited results to {max_results} restaurants")
            
            # Step 2: Generate recommendations if requested
            recommendations = None
            reasoning_result = None
            
            if include_recommendations and restaurants:
                reasoning_result = await self._generate_recommendations_agentcore(
                    restaurants, mbti_type, preferences
                )
                if reasoning_result.success:
                    recommendations = {
                        "recommendation": reasoning_result.recommendations[0] if reasoning_result.recommendations else None,
                        "analysis_summary": reasoning_result.mbti_analysis,
                        "reasoning": reasoning_result.reasoning,
                        "confidence_score": reasoning_result.confidence_score
                    }
            
            # Step 3: Format user-friendly response
            formatted_response = self._format_complete_response(
                restaurants=restaurants,
                recommendations=recommendations,
                meal_types=meal_types,
                partial_results=partial_results,
                search_metadata=search_result.search_metadata
            )
            
            execution_time = (datetime.now() - workflow_start).total_seconds()
            total_time_ms = int((time.time() - start_time) * 1000)
            
            # Update performance tracking
            self.total_workflow_time += total_time_ms
            
            # Collect performance metrics
            performance_metrics = {
                "search_tool_metrics": self.search_tool.get_performance_metrics(),
                "reasoning_tool_metrics": self.reasoning_tool.get_performance_metrics() if reasoning_result else None,
                "workflow_metrics": {
                    "total_calls": self.workflow_call_count,
                    "total_errors": self.workflow_error_count,
                    "average_execution_time_ms": self.total_workflow_time / max(self.workflow_call_count, 1)
                }
            }
            
            logger.info(f"AgentCore Central district workflow completed successfully in {execution_time:.2f}s")
            logger.info(f"Found {len(restaurants)} restaurants, recommendations: {bool(recommendations)}")
            
            return WorkflowResult(
                success=True,
                restaurants_found=len(restaurants),
                recommendations=recommendations,
                formatted_response=formatted_response,
                partial_results=partial_results,
                execution_time=execution_time,
                search_execution_time_ms=search_result.execution_time_ms,
                reasoning_execution_time_ms=reasoning_result.execution_time_ms if reasoning_result else None,
                parallel_execution=self.config.performance.enable_parallel_execution,
                agent_performance_metrics=performance_metrics
            )
            
        except Exception as e:
            execution_time = (datetime.now() - workflow_start).total_seconds()
            self.workflow_error_count += 1
            
            logger.error(f"AgentCore Central district workflow failed after {execution_time:.2f}s: {e}")
            
            # Create fallback response
            fallback_response = self._format_error_response(e, meal_types)
            
            return WorkflowResult(
                success=False,
                restaurants_found=0,
                error_message=str(e),
                formatted_response=fallback_response,
                execution_time=execution_time
            )
    
    async def _search_central_restaurants_agentcore(self, meal_types: Optional[List[str]] = None) -> RestaurantSearchResult:
        """
        Search for restaurants in Central district using AgentCore search agent.
        
        Args:
            meal_types: Optional meal type filters
            
        Returns:
            RestaurantSearchResult object
        """
        try:
            if meal_types:
                # Use combined search with both district and meal type filters
                logger.info("Performing AgentCore combined search for Central district with meal type filters")
                result = await self.search_tool.search_restaurants_combined(
                    districts=self.CENTRAL_DISTRICT_NAMES,
                    meal_types=meal_types,
                    user_id=user_id,
                    session_id=session_id,
                    request_id=request_id,
                    correlation_id=context.correlation_id
                )
            else:
                # Use district-only search
                logger.info("Performing AgentCore district search for Central district")
                result = await self.search_tool.search_restaurants_by_district(
                    districts=self.CENTRAL_DISTRICT_NAMES,
                    user_id=user_id,
                    session_id=session_id,
                    request_id=request_id,
                    correlation_id=context.correlation_id
                )
            
            logger.info(f"AgentCore search completed: found {result.total_count} restaurants")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in AgentCore Central district restaurant search: {e}")
            return RestaurantSearchResult(
                restaurants=[],
                total_count=0,
                search_metadata={
                    'error': str(e),
                    'districts_searched': self.CENTRAL_DISTRICT_NAMES,
                    'meal_types_searched': meal_types,
                    'operation': 'search_central_restaurants_agentcore'
                },
                execution_time_ms=0,
                success=False,
                error_message=str(e)
            )
    
    async def _generate_recommendations_agentcore(
        self, 
        restaurants: List[Dict[str, Any]], 
        mbti_type: Optional[str] = None,
        preferences: Optional[Dict[str, Any]] = None
    ) -> RecommendationResult:
        """
        Generate intelligent recommendations using AgentCore reasoning agent.
        
        Args:
            restaurants: List of restaurant objects with sentiment data
            mbti_type: Optional MBTI personality type for personalized recommendations
            preferences: Optional user preferences
            
        Returns:
            RecommendationResult object
        """
        try:
            logger.info(f"Generating AgentCore recommendations for {len(restaurants)} restaurants")
            
            # Validate restaurant data has sentiment information
            valid_restaurants = []
            for restaurant in restaurants:
                if (isinstance(restaurant, dict) and 
                    "sentiment" in restaurant and 
                    isinstance(restaurant["sentiment"], dict)):
                    valid_restaurants.append(restaurant)
            
            if not valid_restaurants:
                logger.warning("No restaurants with valid sentiment data for recommendations")
                return RecommendationResult(
                    recommendations=[],
                    reasoning="No restaurants with valid sentiment data available for analysis",
                    confidence_score=0.0,
                    mbti_analysis={},
                    execution_time_ms=0,
                    success=False,
                    error_message="No valid restaurant data for recommendations"
                )
            
            # Choose recommendation method based on available data
            if mbti_type and preferences:
                # Use MBTI-based recommendations
                logger.info(f"Using MBTI-based recommendations for type: {mbti_type}")
                result = await self.reasoning_tool.get_recommendations(
                    restaurants=valid_restaurants,
                    mbti_type=mbti_type,
                    preferences=preferences or {},
                    ranking_method="sentiment_likes",
                    user_id=user_id,
                    session_id=session_id,
                    request_id=request_id,
                    correlation_id=context.correlation_id
                )
            else:
                # Use sentiment-based recommendations
                logger.info("Using sentiment-based recommendations")
                result = await self.reasoning_tool.analyze_restaurant_sentiment(
                    restaurants=valid_restaurants,
                    ranking_method="sentiment_likes",
                    user_id=user_id,
                    session_id=session_id,
                    request_id=request_id,
                    correlation_id=context.correlation_id
                )
            
            if result.success:
                logger.info("AgentCore recommendations generated successfully")
            else:
                logger.warning(f"AgentCore recommendation generation failed: {result.error_message}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating AgentCore recommendations: {e}")
            return RecommendationResult(
                recommendations=[],
                reasoning=f"Error generating recommendations: {str(e)}",
                confidence_score=0.0,
                mbti_analysis={},
                execution_time_ms=0,
                success=False,
                error_message=str(e)
            )
    
    async def execute_parallel_workflow(
        self, 
        meal_types: Optional[List[str]] = None,
        mbti_type: Optional[str] = None,
        preferences: Optional[Dict[str, Any]] = None,
        max_results: int = 20
    ) -> WorkflowResult:
        """
        Execute workflow with parallel optimization where possible.
        
        This method attempts to parallelize independent operations for better performance.
        Currently, search and reasoning are sequential due to data dependency, but this
        method provides a framework for future parallel optimizations.
        
        Args:
            meal_types: Optional meal type filters
            mbti_type: Optional MBTI personality type
            preferences: Optional user preferences
            max_results: Maximum number of results to process
            
        Returns:
            WorkflowResult with parallel execution metadata
        """
        if not self.config.performance.enable_parallel_execution:
            logger.info("Parallel execution disabled, falling back to sequential workflow")
            return await self.execute_complete_workflow(
                meal_types=meal_types,
                include_recommendations=True,
                max_results=max_results,
                mbti_type=mbti_type,
                preferences=preferences
            )
        
        start_time = time.time()
        workflow_start = datetime.now()
        
        try:
            # Initialize authentication
            await self.initialize_authentication()
            
            logger.info("Starting parallel AgentCore workflow execution")
            
            # Step 1: Search (must be first due to data dependency)
            search_result = await self._search_central_restaurants_agentcore(meal_types)
            
            if not search_result.success or not search_result.restaurants:
                # Handle search failure or no results
                return await self.execute_complete_workflow(
                    meal_types=meal_types,
                    include_recommendations=True,
                    max_results=max_results,
                    mbti_type=mbti_type,
                    preferences=preferences
                )
            
            restaurants = search_result.restaurants
            if len(restaurants) > max_results:
                restaurants = restaurants[:max_results]
            
            # Step 2: Parallel operations (currently only reasoning, but framework for future expansion)
            tasks = []
            
            # Add reasoning task
            if mbti_type or preferences:
                reasoning_task = asyncio.create_task(
                    self._generate_recommendations_agentcore(restaurants, mbti_type, preferences),
                    name="reasoning_task"
                )
                tasks.append(("reasoning", reasoning_task))
            
            # Future: Add other parallel tasks here (e.g., additional analysis, caching, etc.)
            
            # Execute parallel tasks
            if tasks:
                logger.info(f"Executing {len(tasks)} parallel tasks")
                results = await asyncio.gather(*[task for _, task in tasks], return_exceptions=True)
                
                # Process results
                reasoning_result = None
                for i, (task_name, _) in enumerate(tasks):
                    if task_name == "reasoning":
                        if isinstance(results[i], Exception):
                            logger.error(f"Reasoning task failed: {results[i]}")
                            reasoning_result = RecommendationResult(
                                recommendations=[],
                                reasoning=f"Parallel reasoning failed: {str(results[i])}",
                                confidence_score=0.0,
                                mbti_analysis={},
                                execution_time_ms=0,
                                success=False,
                                error_message=str(results[i])
                            )
                        else:
                            reasoning_result = results[i]
            else:
                # No parallel tasks, use basic sentiment analysis
                reasoning_result = await self._generate_recommendations_agentcore(restaurants)
            
            # Format recommendations
            recommendations = None
            if reasoning_result and reasoning_result.success:
                recommendations = {
                    "recommendation": reasoning_result.recommendations[0] if reasoning_result.recommendations else None,
                    "analysis_summary": reasoning_result.mbti_analysis,
                    "reasoning": reasoning_result.reasoning,
                    "confidence_score": reasoning_result.confidence_score
                }
            
            # Format response
            formatted_response = self._format_complete_response(
                restaurants=restaurants,
                recommendations=recommendations,
                meal_types=meal_types,
                partial_results=len(search_result.restaurants) > max_results,
                search_metadata=search_result.search_metadata
            )
            
            execution_time = (datetime.now() - workflow_start).total_seconds()
            
            logger.info(f"Parallel AgentCore workflow completed in {execution_time:.2f}s")
            
            return WorkflowResult(
                success=True,
                restaurants_found=len(restaurants),
                recommendations=recommendations,
                formatted_response=formatted_response,
                partial_results=len(search_result.restaurants) > max_results,
                execution_time=execution_time,
                search_execution_time_ms=search_result.execution_time_ms,
                reasoning_execution_time_ms=reasoning_result.execution_time_ms if reasoning_result else None,
                parallel_execution=True,
                agent_performance_metrics={
                    "search_tool_metrics": self.search_tool.get_performance_metrics(),
                    "reasoning_tool_metrics": self.reasoning_tool.get_performance_metrics(),
                    "parallel_tasks_executed": len(tasks)
                }
            )
            
        except Exception as e:
            execution_time = (datetime.now() - workflow_start).total_seconds()
            logger.error(f"Parallel workflow failed after {execution_time:.2f}s: {e}")
            
            # Fallback to sequential workflow
            logger.info("Falling back to sequential workflow due to parallel execution error")
            return await self.execute_complete_workflow(
                meal_types=meal_types,
                include_recommendations=True,
                max_results=max_results,
                mbti_type=mbti_type,
                preferences=preferences
            )
    
    def _format_complete_response(self, 
                                restaurants: List[Dict[str, Any]],
                                recommendations: Optional[Dict[str, Any]] = None,
                                meal_types: Optional[List[str]] = None,
                                partial_results: bool = False,
                                search_metadata: Dict[str, Any] = None) -> str:
        """
        Format a complete, user-friendly response with restaurant details and recommendations.
        
        Args:
            restaurants: List of restaurant objects
            recommendations: Optional recommendation data
            meal_types: Meal type filters applied
            partial_results: Whether results were limited
            search_metadata: Search execution metadata
            
        Returns:
            Formatted response string
        """
        try:
            response_parts = []
            
            # Header with search summary
            header = self._format_search_header(restaurants, meal_types, partial_results)
            response_parts.append(header)
            
            # Recommendations section (if available)
            if recommendations:
                rec_section = self._format_recommendations_section(recommendations)
                response_parts.append(rec_section)
            
            # Restaurant details section
            details_section = self._format_restaurant_details(restaurants, limit=10)
            response_parts.append(details_section)
            
            # Additional information section
            if search_metadata:
                metadata_section = self._format_metadata_section(search_metadata)
                response_parts.append(metadata_section)
            
            # Footer with helpful tips
            footer = self._format_response_footer(meal_types)
            response_parts.append(footer)
            
            return "\n\n".join(response_parts)
            
        except Exception as e:
            logger.error(f"Error formatting complete response: {e}")
            return self._format_basic_response(restaurants, meal_types)
    
    def _format_search_header(self, 
                            restaurants: List[Dict[str, Any]], 
                            meal_types: Optional[List[str]] = None,
                            partial_results: bool = False) -> str:
        """Format the search results header."""
        count = len(restaurants)
        
        if meal_types:
            meal_filter = f" serving {', '.join(meal_types)}"
        else:
            meal_filter = ""
        
        partial_note = " (showing top results)" if partial_results else ""
        
        if count == 0:
            return f"🍽️ **Central District Restaurant Search**\n\nNo restaurants found in Central district{meal_filter}."
        elif count == 1:
            return f"🍽️ **Central District Restaurant Search**\n\nFound 1 restaurant in Central district{meal_filter}{partial_note}:"
        else:
            return f"🍽️ **Central District Restaurant Search**\n\nFound {count} restaurants in Central district{meal_filter}{partial_note}:"
    
    def _format_recommendations_section(self, recommendations: Dict[str, Any]) -> str:
        """Format the recommendations section."""
        try:
            rec_parts = ["🌟 **Top Recommendation**"]
            
            # Get the top recommendation
            top_rec = recommendations.get("recommendation")
            if top_rec:
                rec_details = self._format_single_restaurant(top_rec, include_reasoning=True)
                rec_parts.append(rec_details)
            
            # Add analysis summary if available
            analysis = recommendations.get("analysis_summary", {})
            if analysis:
                summary_parts = []
                if "restaurant_count" in analysis:
                    summary_parts.append(f"Analyzed {analysis['restaurant_count']} restaurants")
                if "average_likes" in analysis:
                    summary_parts.append(f"Average rating: {analysis['average_likes']:.1f}% positive")
                if "top_sentiment_score" in analysis:
                    summary_parts.append(f"Top score: {analysis['top_sentiment_score']:.1f}%")
                
                if summary_parts:
                    rec_parts.append(f"*Analysis: {', '.join(summary_parts)}*")
            
            return "\n".join(rec_parts)
            
        except Exception as e:
            logger.error(f"Error formatting recommendations section: {e}")
            return "🌟 **Recommendations**\n\nRecommendation analysis available but formatting failed."
    
    def _format_restaurant_details(self, restaurants: List[Dict[str, Any]], limit: int = 10) -> str:
        """Format detailed restaurant information."""
        try:
            if not restaurants:
                return ""
            
            details_parts = ["📍 **Restaurant Details**"]
            
            # Show up to limit restaurants
            display_restaurants = restaurants[:limit]
            
            for i, restaurant in enumerate(display_restaurants, 1):
                restaurant_info = self._format_single_restaurant(restaurant, include_index=i)
                details_parts.append(restaurant_info)
            
            # Add note if more restaurants available
            if len(restaurants) > limit:
                remaining = len(restaurants) - limit
                details_parts.append(f"*... and {remaining} more restaurants available*")
            
            return "\n\n".join(details_parts)
            
        except Exception as e:
            logger.error(f"Error formatting restaurant details: {e}")
            return "📍 **Restaurant Details**\n\nRestaurant information available but formatting failed."
    
    def _format_single_restaurant(self, 
                                restaurant: Dict[str, Any], 
                                include_index: Optional[int] = None,
                                include_reasoning: bool = False) -> str:
        """Format a single restaurant's information."""
        try:
            parts = []
            
            # Restaurant name with optional index
            name = restaurant.get("name", "Unknown Restaurant")
            if include_index:
                parts.append(f"**{include_index}. {name}**")
            else:
                parts.append(f"**{name}**")
            
            # Address
            address = restaurant.get("address", "Address not available")
            parts.append(f"📍 {address}")
            
            # Sentiment/Rating information
            sentiment = restaurant.get("sentiment", {})
            if sentiment:
                likes = sentiment.get("likes", 0)
                dislikes = sentiment.get("dislikes", 0)
                neutral = sentiment.get("neutral", 0)
                total = likes + dislikes + neutral
                
                if total > 0:
                    likes_pct = (likes / total) * 100
                    parts.append(f"⭐ {likes_pct:.1f}% positive ({likes} likes, {dislikes} dislikes, {neutral} neutral)")
                else:
                    parts.append("⭐ No ratings available")
            
            # Price range
            price_range = restaurant.get("price_range", "")
            if price_range:
                parts.append(f"💰 Price range: {price_range}")
            
            # Meal types
            meal_types = restaurant.get("meal_type", [])
            if meal_types:
                if isinstance(meal_types, list):
                    meal_str = ", ".join(meal_types)
                else:
                    meal_str = str(meal_types)
                parts.append(f"🍽️ Serves: {meal_str}")
            
            # District (should be Central)
            district = restaurant.get("district", "")
            if district and district != "Central district":
                parts.append(f"📍 District: {district}")
            
            # Recommendation reasoning (if requested)
            if include_reasoning and sentiment:
                reasoning = self._generate_recommendation_reasoning(sentiment)
                if reasoning:
                    parts.append(f"💡 *{reasoning}*")
            
            return "\n".join(parts)
            
        except Exception as e:
            logger.error(f"Error formatting single restaurant: {e}")
            return f"**{restaurant.get('name', 'Unknown Restaurant')}**\nFormatting error occurred"
    
    def _generate_recommendation_reasoning(self, sentiment: Dict[str, Any]) -> str:
        """Generate reasoning text for why a restaurant is recommended."""
        try:
            likes = sentiment.get("likes", 0)
            dislikes = sentiment.get("dislikes", 0)
            neutral = sentiment.get("neutral", 0)
            total = likes + dislikes + neutral
            
            if total == 0:
                return "No customer feedback available"
            
            likes_pct = (likes / total) * 100
            
            if likes_pct >= 90:
                return f"Highly recommended with {likes_pct:.1f}% positive feedback from {total} customers"
            elif likes_pct >= 80:
                return f"Strongly recommended with {likes_pct:.1f}% positive feedback from {total} customers"
            elif likes_pct >= 70:
                return f"Recommended with {likes_pct:.1f}% positive feedback from {total} customers"
            elif likes_pct >= 60:
                return f"Generally positive with {likes_pct:.1f}% positive feedback from {total} customers"
            else:
                return f"Mixed reviews with {likes_pct:.1f}% positive feedback from {total} customers"
                
        except Exception as e:
            logger.error(f"Error generating recommendation reasoning: {e}")
            return "Recommendation analysis available"
    
    def _format_metadata_section(self, metadata: Dict[str, Any]) -> str:
        """Format search metadata information."""
        try:
            if not metadata:
                return ""
            
            meta_parts = ["ℹ️ **Search Information**"]
            
            # Execution time
            exec_time = metadata.get("execution_time_ms")
            if exec_time:
                meta_parts.append(f"Search completed in {exec_time:.1f}ms")
            
            # Search criteria
            criteria = metadata.get("search_criteria", {})
            if criteria:
                criteria_parts = []
                if "districts" in criteria:
                    criteria_parts.append(f"Districts: {', '.join(criteria['districts'])}")
                if "meal_types" in criteria:
                    criteria_parts.append(f"Meal types: {', '.join(criteria['meal_types'])}")
                
                if criteria_parts:
                    meta_parts.append(f"Filters applied: {', '.join(criteria_parts)}")
            
            # Total results
            total_results = metadata.get("total_results")
            if total_results is not None:
                meta_parts.append(f"Total results found: {total_results}")
            
            return "\n".join(meta_parts) if len(meta_parts) > 1 else ""
            
        except Exception as e:
            logger.error(f"Error formatting metadata section: {e}")
            return ""
    
    def _format_response_footer(self, meal_types: Optional[List[str]] = None) -> str:
        """Format helpful footer information."""
        footer_parts = ["💡 **Travel Tips**"]
        
        if meal_types:
            if "breakfast" in meal_types:
                footer_parts.append("• Central district offers excellent breakfast spots with harbor views")
            if "lunch" in meal_types:
                footer_parts.append("• Many lunch venues in Central cater to the business district crowd")
            if "dinner" in meal_types:
                footer_parts.append("• Central's dinner scene ranges from casual to fine dining")
        else:
            footer_parts.append("• Central district is Hong Kong's main business district with diverse dining options")
            footer_parts.append("• Most restaurants are easily accessible via MTR Central Station")
        
        footer_parts.append("• Consider making reservations for popular restaurants, especially during peak hours")
        
        return "\n".join(footer_parts)
    
    def _format_no_results_response(self, meal_types: Optional[List[str]] = None) -> str:
        """Format response when no restaurants are found."""
        meal_filter = f" serving {', '.join(meal_types)}" if meal_types else ""
        
        response_parts = [
            f"🍽️ **Central District Restaurant Search**",
            f"",
            f"No restaurants found in Central district{meal_filter}.",
            f"",
            f"💡 **Suggestions:**",
            f"• Try searching without meal type filters for more options",
            f"• Consider nearby districts like Admiralty or Sheung Wan",
            f"• Check if the meal type filters match your dining time preferences",
            f"",
            f"🗺️ **Alternative Areas:**",
            f"• **Admiralty**: Adjacent to Central with many dining options",
            f"• **Sheung Wan**: Historic area with traditional and modern restaurants",
            f"• **Wan Chai**: Vibrant dining scene just east of Central"
        ]
        
        return "\n".join(response_parts)
    
    def _format_error_response(self, error: Exception, meal_types: Optional[List[str]] = None) -> str:
        """Format response when an error occurs."""
        meal_filter = f" with {', '.join(meal_types)} filters" if meal_types else ""
        
        response_parts = [
            f"🍽️ **Central District Restaurant Search**",
            f"",
            f"I encountered an issue while searching for restaurants in Central district{meal_filter}.",
            f"",
            f"🔧 **What happened:**",
            f"The restaurant search service is temporarily experiencing difficulties.",
            f"",
            f"💡 **What you can do:**",
            f"• Try your search again in a few moments",
            f"• Ask me about general travel planning for Central district",
            f"• I can provide information about Central district attractions and transportation",
            f"",
            f"🗺️ **About Central District:**",
            f"Central is Hong Kong's main business district, located on Hong Kong Island.",
            f"It's home to many skyscrapers, shopping malls, and diverse dining options.",
            f"The area is easily accessible via MTR Central Station and offers harbor views."
        ]
        
        return "\n".join(response_parts)
    
    def _format_basic_response(self, restaurants: List[Dict[str, Any]], meal_types: Optional[List[str]] = None) -> str:
        """Format a basic response when detailed formatting fails."""
        count = len(restaurants)
        meal_filter = f" serving {', '.join(meal_types)}" if meal_types else ""
        
        if count == 0:
            return f"No restaurants found in Central district{meal_filter}."
        
        response_parts = [
            f"Found {count} restaurant{'s' if count != 1 else ''} in Central district{meal_filter}:"
        ]
        
        # Add basic restaurant list
        for i, restaurant in enumerate(restaurants[:5], 1):  # Show first 5
            name = restaurant.get("name", "Unknown Restaurant")
            address = restaurant.get("address", "Address not available")
            response_parts.append(f"{i}. {name} - {address}")
        
        if count > 5:
            response_parts.append(f"... and {count - 5} more restaurants")
        
        return "\n".join(response_parts)
    
    def get_workflow_health_status(self) -> Dict[str, Any]:
        """
        Get comprehensive health status of the workflow and its components.
        
        Returns:
            Dictionary with health status information
        """
        try:
            # Get tool performance metrics
            search_metrics = self.search_tool.get_performance_metrics()
            reasoning_metrics = self.reasoning_tool.get_performance_metrics()
            
            # Calculate workflow health scores
            search_health = "healthy" if search_metrics["error_rate"] < 0.1 else "degraded" if search_metrics["error_rate"] < 0.3 else "unhealthy"
            reasoning_health = "healthy" if reasoning_metrics["error_rate"] < 0.1 else "degraded" if reasoning_metrics["error_rate"] < 0.3 else "unhealthy"
            
            # Overall workflow health
            workflow_error_rate = self.workflow_error_count / max(self.workflow_call_count, 1)
            workflow_health = "healthy" if workflow_error_rate < 0.1 else "degraded" if workflow_error_rate < 0.3 else "unhealthy"
            
            return {
                "overall_health": workflow_health,
                "timestamp": datetime.now().isoformat(),
                "environment": self.config.environment,
                "components": {
                    "search_agent": {
                        "health": search_health,
                        "agent_arn": self.config.agentcore.restaurant_search_agent_arn,
                        "metrics": search_metrics
                    },
                    "reasoning_agent": {
                        "health": reasoning_health,
                        "agent_arn": self.config.agentcore.restaurant_reasoning_agent_arn,
                        "metrics": reasoning_metrics
                    },
                    "workflow": {
                        "health": workflow_health,
                        "total_calls": self.workflow_call_count,
                        "total_errors": self.workflow_error_count,
                        "error_rate": workflow_error_rate,
                        "average_execution_time_ms": self.total_workflow_time / max(self.workflow_call_count, 1)
                    }
                },
                "configuration": {
                    "parallel_execution_enabled": self.config.performance.enable_parallel_execution,
                    "caching_enabled": self.config.performance.enable_caching,
                    "monitoring_enabled": self.config.monitoring.enable_metrics,
                    "debug_mode": self.config.debug_mode
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting workflow health status: {e}")
            return {
                "overall_health": "unknown",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def validate_agent_connectivity(self) -> Dict[str, Any]:
        """
        Validate connectivity to both AgentCore agents.
        
        Returns:
            Dictionary with connectivity test results
        """
        results = {
            "timestamp": datetime.now().isoformat(),
            "environment": self.config.environment,
            "tests": {}
        }
        
        try:
            # Test search agent connectivity
            logger.info("Testing search agent connectivity")
            search_test_start = time.time()
            
            try:
                search_test_result = await self.search_tool.search_restaurants_by_district(["Central district"])
                search_test_time = int((time.time() - search_test_start) * 1000)
                
                results["tests"]["search_agent"] = {
                    "status": "success" if search_test_result.success else "failed",
                    "response_time_ms": search_test_time,
                    "agent_arn": self.config.agentcore.restaurant_search_agent_arn,
                    "error": search_test_result.error_message if not search_test_result.success else None
                }
            except Exception as e:
                search_test_time = int((time.time() - search_test_start) * 1000)
                results["tests"]["search_agent"] = {
                    "status": "error",
                    "response_time_ms": search_test_time,
                    "agent_arn": self.config.agentcore.restaurant_search_agent_arn,
                    "error": str(e)
                }
            
            # Test reasoning agent connectivity
            logger.info("Testing reasoning agent connectivity")
            reasoning_test_start = time.time()
            
            try:
                # Create minimal test data
                test_restaurants = [{
                    "name": "Test Restaurant",
                    "sentiment": {"likes": 10, "dislikes": 2, "neutral": 3}
                }]
                
                reasoning_test_result = await self.reasoning_tool.analyze_restaurant_sentiment(
                    restaurants=test_restaurants,
                    ranking_method="sentiment_likes"
                )
                reasoning_test_time = int((time.time() - reasoning_test_start) * 1000)
                
                results["tests"]["reasoning_agent"] = {
                    "status": "success" if reasoning_test_result.success else "failed",
                    "response_time_ms": reasoning_test_time,
                    "agent_arn": self.config.agentcore.restaurant_reasoning_agent_arn,
                    "error": reasoning_test_result.error_message if not reasoning_test_result.success else None
                }
            except Exception as e:
                reasoning_test_time = int((time.time() - reasoning_test_start) * 1000)
                results["tests"]["reasoning_agent"] = {
                    "status": "error",
                    "response_time_ms": reasoning_test_time,
                    "agent_arn": self.config.agentcore.restaurant_reasoning_agent_arn,
                    "error": str(e)
                }
            
            # Overall connectivity status
            search_ok = results["tests"]["search_agent"]["status"] == "success"
            reasoning_ok = results["tests"]["reasoning_agent"]["status"] == "success"
            
            if search_ok and reasoning_ok:
                results["overall_status"] = "all_agents_healthy"
            elif search_ok or reasoning_ok:
                results["overall_status"] = "partial_connectivity"
            else:
                results["overall_status"] = "no_connectivity"
            
            logger.info(f"Agent connectivity test completed: {results['overall_status']}")
            
        except Exception as e:
            logger.error(f"Error during agent connectivity validation: {e}")
            results["overall_status"] = "test_failed"
            results["error"] = str(e)
        
        return results
    
    def reset_performance_metrics(self) -> None:
        """Reset workflow performance metrics."""
        self.workflow_call_count = 0
        self.workflow_error_count = 0
        self.total_workflow_time = 0.0
        logger.info("Workflow performance metrics reset")


# Convenience functions for easy workflow execution
async def search_central_district_restaurants(
    meal_types: Optional[List[str]] = None,
    include_recommendations: bool = True,
    environment: str = None,
    mbti_type: Optional[str] = None,
    preferences: Optional[Dict[str, Any]] = None,
    max_results: int = 20,
    use_parallel_execution: bool = None
) -> WorkflowResult:
    """
    Convenience function to execute the Central district search workflow using AgentCore.
    
    Args:
        meal_types: Optional meal type filters (breakfast, lunch, dinner)
        include_recommendations: Whether to generate recommendations
        environment: Target environment (development, staging, production)
        mbti_type: Optional MBTI personality type for personalized recommendations
        preferences: Optional user preferences for recommendations
        max_results: Maximum number of results to process
        use_parallel_execution: Override parallel execution setting (None = use config)
        
    Returns:
        WorkflowResult with complete pipeline results and performance metrics
    """
    workflow = CentralDistrictWorkflow(environment=environment)
    
    # Override parallel execution setting if specified
    if use_parallel_execution is not None:
        workflow.config.performance.enable_parallel_execution = use_parallel_execution
    
    if workflow.config.performance.enable_parallel_execution and (mbti_type or preferences):
        # Use parallel execution for better performance
        return await workflow.execute_parallel_workflow(
            meal_types=meal_types,
            mbti_type=mbti_type,
            preferences=preferences,
            max_results=max_results
        )
    else:
        # Use sequential execution
        return await workflow.execute_complete_workflow(
            meal_types=meal_types,
            include_recommendations=include_recommendations,
            max_results=max_results,
            mbti_type=mbti_type,
            preferences=preferences
        )


async def validate_central_district_workflow_health(environment: str = None) -> Dict[str, Any]:
    """
    Convenience function to validate the health of the Central district workflow.
    
    Args:
        environment: Target environment (development, staging, production)
        
    Returns:
        Dictionary with comprehensive health status
    """
    try:
        workflow = CentralDistrictWorkflow(environment=environment)
        
        # Get health status
        health_status = workflow.get_workflow_health_status()
        
        # Validate agent connectivity
        connectivity_results = await workflow.validate_agent_connectivity()
        
        return {
            "health_status": health_status,
            "connectivity_tests": connectivity_results,
            "validation_timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error validating workflow health: {e}")
        return {
            "error": str(e),
            "validation_timestamp": datetime.now().isoformat(),
            "status": "validation_failed"
        }


# Export main classes and functions
__all__ = [
    'CentralDistrictWorkflow',
    'WorkflowResult',
    'search_central_district_restaurants',
    'validate_central_district_workflow_health'
]