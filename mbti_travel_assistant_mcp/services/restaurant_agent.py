"""
Restaurant Agent Service - Strands Agent Implementation

This module implements the internal LLM agent using Strands Agents framework
for orchestrating restaurant recommendation requests. The agent processes
district and meal time parameters, coordinates MCP client calls, and formats
responses for frontend consumption.
"""

import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

# Set up logger first
logger = logging.getLogger(__name__)

# Strands Agents framework
try:
    from strands_agents import Agent
    from strands_agents.config import AgentConfig
    from strands_agents.models import ModelConfig
    STRANDS_AVAILABLE = True
except ImportError:
    # Mock classes for development/testing when strands_agents is not available
    class Agent:
        def __init__(self, config=None):
            self.config = config
        
        async def process(self, prompt):
            # Mock response for testing
            class MockResponse:
                content = '{"recommendation": null, "candidates": [], "metadata": {}}'
            return MockResponse()
    
    class AgentConfig:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)
    
    class ModelConfig:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)
    
    STRANDS_AVAILABLE = False
    logger.warning("strands_agents not available, using mock implementation")

# Configuration and models
from config.settings import settings
from models.restaurant_models import Restaurant, Sentiment
from services.mcp_client_manager import MCPClientManager


class RestaurantAgent:
    """
    Internal LLM agent for restaurant recommendation orchestration.
    
    This agent uses the Strands Agents framework to process restaurant
    recommendation requests, coordinate MCP client calls to search and
    reasoning servers, and format structured responses.
    """
    
    def __init__(self):
        """Initialize the restaurant agent with Strands Agent configuration."""
        self.mcp_client_manager = MCPClientManager()
        self.agent = self._create_strands_agent()
        
        logger.info(
            "Initialized RestaurantAgent",
            extra={
                "agent_model": settings.agentcore.agent_model,
                "temperature": settings.agentcore.agent_temperature,
                "max_tokens": settings.agentcore.agent_max_tokens
            }
        )
    
    def _create_strands_agent(self) -> Agent:
        """
        Create and configure the Strands Agent with Nova Pro model.
        
        Returns:
            Configured Strands Agent instance
        """
        # Model configuration for Nova Pro
        model_config = ModelConfig(
            model_id=settings.agentcore.agent_model,
            temperature=settings.agentcore.agent_temperature,
            max_tokens=settings.agentcore.agent_max_tokens,
            top_p=0.9,
            top_k=50
        )
        
        # Agent configuration with system prompt
        agent_config = AgentConfig(
            name="restaurant_orchestrator",
            description="Restaurant recommendation orchestration agent",
            model_config=model_config,
            system_prompt=self._get_system_prompt(),
            tools=[],  # Tools will be handled through MCP client calls
            memory_enabled=False,  # Stateless for this use case
            streaming=False
        )
        
        # Create Strands Agent
        agent = Agent(config=agent_config)
        
        return agent
    
    async def _process_parameters(
        self,
        district: Optional[str],
        meal_time: Optional[str],
        user_context: Optional[Dict[str, Any]],
        correlation_id: Optional[str]
    ) -> Dict[str, Any]:
        """
        Process and validate input parameters using agent intelligence.
        
        Args:
            district: Raw district parameter
            meal_time: Raw meal time parameter
            user_context: User context for personalization
            correlation_id: Request correlation ID
            
        Returns:
            Dictionary with processed parameters
        """
        logger.debug(
            "Processing input parameters",
            extra={"correlation_id": correlation_id}
        )
        
        processed_params = {
            "district": district,
            "meal_time": meal_time,
            "user_preferences": {}
        }
        
        # Normalize district parameter
        if district:
            # Handle common district name variations
            district_lower = district.lower().strip()
            if "central" in district_lower and "district" not in district_lower:
                processed_params["district"] = "Central district"
            elif "admiralty" in district_lower:
                processed_params["district"] = "Admiralty"
            elif "causeway" in district_lower and "bay" in district_lower:
                processed_params["district"] = "Causeway Bay"
            else:
                processed_params["district"] = district.strip()
        
        # Normalize meal time parameter
        if meal_time:
            meal_time_lower = meal_time.lower().strip()
            if meal_time_lower in ["breakfast", "morning", "am"]:
                processed_params["meal_time"] = "breakfast"
            elif meal_time_lower in ["lunch", "afternoon", "noon"]:
                processed_params["meal_time"] = "lunch"
            elif meal_time_lower in ["dinner", "evening", "night", "pm"]:
                processed_params["meal_time"] = "dinner"
            else:
                processed_params["meal_time"] = meal_time_lower
        
        # Extract user preferences from context if available
        if user_context:
            processed_params["user_preferences"] = {
                "user_id": user_context.get("sub"),
                "preferences": user_context.get("custom:preferences", {}),
                "dietary_restrictions": user_context.get("custom:dietary_restrictions", [])
            }
        
        logger.debug(
            "Processed parameters",
            extra={
                "correlation_id": correlation_id,
                "processed_district": processed_params["district"],
                "processed_meal_time": processed_params["meal_time"]
            }
        )
        
        return processed_params
    
    async def _filter_search_results(
        self,
        restaurants: List[Restaurant],
        processed_params: Dict[str, Any],
        correlation_id: Optional[str]
    ) -> List[Restaurant]:
        """
        Apply intelligent filtering to search results before reasoning analysis.
        
        Args:
            restaurants: Raw search results
            processed_params: Processed parameters
            correlation_id: Request correlation ID
            
        Returns:
            Filtered list of restaurants
        """
        logger.debug(
            "Filtering search results",
            extra={
                "correlation_id": correlation_id,
                "input_count": len(restaurants)
            }
        )
        
        filtered_restaurants = []
        user_preferences = processed_params.get("user_preferences", {})
        
        for restaurant in restaurants:
            # Basic data quality filter
            if not restaurant.id or not restaurant.name:
                continue
            
            # Apply dietary restrictions if available
            dietary_restrictions = user_preferences.get("dietary_restrictions", [])
            if dietary_restrictions:
                # This would need to be enhanced based on actual dietary restriction data
                # For now, we'll include all restaurants
                pass
            
            # Filter by minimum sentiment data quality
            total_sentiment = (
                restaurant.sentiment.likes + 
                restaurant.sentiment.dislikes + 
                restaurant.sentiment.neutral
            )
            
            # Only include restaurants with some sentiment data
            if total_sentiment > 0:
                filtered_restaurants.append(restaurant)
        
        logger.info(
            "Filtered search results",
            extra={
                "correlation_id": correlation_id,
                "input_count": len(restaurants),
                "output_count": len(filtered_restaurants),
                "filtered_out": len(restaurants) - len(filtered_restaurants)
            }
        )
        
        return filtered_restaurants
    
    async def _validate_reasoning_results(
        self,
        reasoning_results: Dict[str, Any],
        processed_params: Dict[str, Any],
        correlation_id: Optional[str]
    ) -> Dict[str, Any]:
        """
        Validate and enhance reasoning results from MCP server.
        
        Args:
            reasoning_results: Raw results from reasoning MCP server
            processed_params: Processed request parameters
            correlation_id: Request correlation ID
            
        Returns:
            Validated and enhanced reasoning results
        """
        logger.debug(
            "Validating reasoning results",
            extra={"correlation_id": correlation_id}
        )
        
        validated_results = reasoning_results.copy()
        
        # Ensure we have exactly 1 recommendation
        recommendation = validated_results.get("recommendation")
        candidates = validated_results.get("candidates", [])
        
        if not recommendation and candidates:
            # Use the first candidate as recommendation
            validated_results["recommendation"] = candidates[0]
            validated_results["candidates"] = candidates[1:20]  # Limit to 19 remaining
            
            logger.info(
                "Promoted first candidate to recommendation",
                extra={"correlation_id": correlation_id}
            )
        
        # Ensure we have at most 19 candidates
        if len(validated_results.get("candidates", [])) > 19:
            validated_results["candidates"] = validated_results["candidates"][:19]
            
            logger.info(
                "Truncated candidates to 19 items",
                extra={"correlation_id": correlation_id}
            )
        
        # Add search criteria to results
        validated_results["search_criteria"] = {
            "district": processed_params.get("district"),
            "meal_time": processed_params.get("meal_time")
        }
        
        # Enhance analysis summary
        if "analysis_summary" not in validated_results:
            validated_results["analysis_summary"] = {}
        
        validated_results["analysis_summary"].update({
            "recommendation_count": 1 if validated_results.get("recommendation") else 0,
            "candidate_count": len(validated_results.get("candidates", [])),
            "total_results": (
                (1 if validated_results.get("recommendation") else 0) + 
                len(validated_results.get("candidates", []))
            )
        })
        
        logger.debug(
            "Validated reasoning results",
            extra={
                "correlation_id": correlation_id,
                "has_recommendation": bool(validated_results.get("recommendation")),
                "candidate_count": len(validated_results.get("candidates", []))
            }
        )
        
        return validated_results
    
    def _get_system_prompt(self) -> str:
        """
        Get the system prompt for restaurant orchestration tasks.
        
        Returns:
            System prompt string for the agent
        """
        return """You are a restaurant recommendation orchestration agent for the MBTI Travel Assistant.

Your role is to:
1. Process district and meal time parameters from user requests
2. Coordinate calls to restaurant search and reasoning MCP servers
3. Format responses as structured JSON for frontend web applications

WORKFLOW:
1. First, call the restaurant search MCP server to find restaurants matching the district and meal time
2. Then, call the restaurant reasoning MCP server to analyze sentiment and generate recommendations
3. Format the final response with exactly 1 recommendation and up to 19 candidates

RESPONSE FORMAT:
Always return a JSON object with this exact structure:
{
    "recommendation": {
        "id": "restaurant_id",
        "name": "Restaurant Name",
        "address": "Full Address",
        "district": "District Name",
        "meal_type": ["cuisine_types"],
        "sentiment": {"likes": 0, "dislikes": 0, "neutral": 0},
        "price_range": "$$",
        "operating_hours": {"monday": ["07:00-11:30"]},
        "location_category": "category"
    },
    "candidates": [
        // Array of 19 restaurant objects with same structure
    ],
    "metadata": {
        "search_criteria": {"district": "...", "meal_time": "..."},
        "total_found": 0,
        "timestamp": "ISO timestamp",
        "processing_time_ms": 0,
        "mcp_calls": ["search", "reasoning"]
    }
}

IMPORTANT RULES:
- Always validate district and meal_time parameters
- Handle MCP server errors gracefully
- Ensure exactly 1 recommendation and up to 19 candidates
- Include comprehensive metadata for debugging
- Use structured logging for all operations
- Never expose internal system details to users"""
    
    async def process_request(
        self,
        district: Optional[str],
        meal_time: Optional[str],
        user_context: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process restaurant recommendation request through agent orchestration.
        
        This method implements the core orchestration logic:
        1. Validate and process input parameters
        2. Search for restaurants using district and meal_time criteria
        3. Analyze restaurants using sentiment-based reasoning
        4. Format and return structured response
        
        Args:
            district: District name for restaurant search
            meal_time: Meal time (breakfast, lunch, dinner)
            user_context: Authenticated user context
            correlation_id: Request correlation ID for logging
            
        Returns:
            Dictionary containing recommendation and candidates data
            
        Raises:
            Exception: Various exceptions from MCP client calls or agent processing
        """
        start_time = datetime.utcnow()
        
        logger.info(
            "Processing restaurant request with agent orchestration",
            extra={
                "correlation_id": correlation_id,
                "district": district,
                "meal_time": meal_time,
                "has_user_context": user_context is not None
            }
        )
        
        try:
            # Step 1: Process and validate parameters using agent intelligence
            processed_params = await self._process_parameters(
                district, meal_time, user_context, correlation_id
            )
            
            # Step 2: Search for restaurants using MCP client
            search_results = await self._search_restaurants(
                processed_params["district"],
                processed_params["meal_time"],
                correlation_id
            )
            
            # Step 3: Apply pre-analysis filtering if needed
            filtered_restaurants = await self._filter_search_results(
                search_results, processed_params, correlation_id
            )
            
            # Step 4: Analyze restaurants using reasoning MCP client
            reasoning_results = await self._analyze_restaurants(
                filtered_restaurants, correlation_id
            )
            
            # Step 5: Post-process and validate reasoning results
            validated_results = await self._validate_reasoning_results(
                reasoning_results, processed_params, correlation_id
            )
            
            # Step 6: Format response using agent intelligence
            formatted_response = await self._format_agent_response(
                validated_results,
                processed_params["district"],
                processed_params["meal_time"],
                start_time,
                correlation_id
            )
            
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            logger.info(
                "Successfully processed request with agent orchestration",
                extra={
                    "correlation_id": correlation_id,
                    "processing_time_ms": processing_time,
                    "restaurants_found": len(search_results),
                    "filtered_restaurants": len(filtered_restaurants),
                    "has_recommendation": "recommendation" in formatted_response,
                    "candidate_count": len(formatted_response.get("candidates", []))
                }
            )
            
            return formatted_response
            
        except Exception as e:
            logger.error(
                f"Agent orchestration failed: {str(e)}",
                extra={"correlation_id": correlation_id},
                exc_info=True
            )
            raise
    
    async def _search_restaurants(
        self,
        district: Optional[str],
        meal_time: Optional[str],
        correlation_id: Optional[str]
    ) -> List[Restaurant]:
        """
        Search for restaurants using the search MCP server.
        
        Args:
            district: District name for search
            meal_time: Meal time filter
            correlation_id: Request correlation ID
            
        Returns:
            List of Restaurant objects from search MCP server
        """
        logger.info(
            "Calling search MCP server",
            extra={
                "correlation_id": correlation_id,
                "district": district,
                "meal_time": meal_time
            }
        )
        
        try:
            # Validate parameters before making MCP call
            if not district and not meal_time:
                logger.warning(
                    "No search criteria provided, searching all restaurants",
                    extra={"correlation_id": correlation_id}
                )
            
            # Call search MCP server through client manager
            search_results = await self.mcp_client_manager.search_restaurants(
                district=district,
                meal_time=meal_time
            )
            
            logger.info(
                "Search MCP call completed",
                extra={
                    "correlation_id": correlation_id,
                    "restaurants_found": len(search_results)
                }
            )
            
            # Validate search results
            if not search_results:
                logger.warning(
                    "No restaurants found for search criteria",
                    extra={
                        "correlation_id": correlation_id,
                        "district": district,
                        "meal_time": meal_time
                    }
                )
            
            return search_results
            
        except Exception as e:
            logger.error(
                f"Search MCP call failed: {str(e)}",
                extra={"correlation_id": correlation_id},
                exc_info=True
            )
            raise
    
    async def _analyze_restaurants(
        self,
        restaurants: List[Restaurant],
        correlation_id: Optional[str]
    ) -> Dict[str, Any]:
        """
        Analyze restaurants using the reasoning MCP server.
        
        Args:
            restaurants: List of Restaurant objects to analyze
            correlation_id: Request correlation ID
            
        Returns:
            Reasoning results with recommendation and candidates
        """
        logger.info(
            "Calling reasoning MCP server",
            extra={
                "correlation_id": correlation_id,
                "restaurant_count": len(restaurants)
            }
        )
        
        try:
            # Validate input restaurants
            if not restaurants:
                logger.warning(
                    "No restaurants provided for analysis",
                    extra={"correlation_id": correlation_id}
                )
                return {
                    "recommendation": None,
                    "candidates": [],
                    "ranking_method": "sentiment_likes",
                    "analysis_summary": {
                        "total_restaurants": 0,
                        "message": "No restaurants available for analysis"
                    }
                }
            
            # Filter out restaurants with incomplete data
            valid_restaurants = []
            for restaurant in restaurants:
                if restaurant.id and restaurant.name:
                    valid_restaurants.append(restaurant)
                else:
                    logger.debug(
                        f"Skipping restaurant with incomplete data: {restaurant.name or 'Unknown'}",
                        extra={"correlation_id": correlation_id}
                    )
            
            if not valid_restaurants:
                logger.warning(
                    "No valid restaurants after filtering",
                    extra={"correlation_id": correlation_id}
                )
                return {
                    "recommendation": None,
                    "candidates": [],
                    "ranking_method": "sentiment_likes",
                    "analysis_summary": {
                        "total_restaurants": len(restaurants),
                        "valid_restaurants": 0,
                        "message": "No valid restaurants for analysis"
                    }
                }
            
            # Call reasoning MCP server through client manager
            reasoning_results = await self.mcp_client_manager.analyze_restaurants(
                restaurants=valid_restaurants,
                ranking_method="sentiment_likes"
            )
            
            logger.info(
                "Reasoning MCP call completed",
                extra={
                    "correlation_id": correlation_id,
                    "has_recommendation": "recommendation" in reasoning_results,
                    "candidate_count": len(reasoning_results.get("candidates", []))
                }
            )
            
            # Validate reasoning results
            if not reasoning_results.get("recommendation") and not reasoning_results.get("candidates"):
                logger.warning(
                    "Reasoning MCP server returned no results",
                    extra={"correlation_id": correlation_id}
                )
            
            return reasoning_results
            
        except Exception as e:
            logger.error(
                f"Reasoning MCP call failed: {str(e)}",
                extra={"correlation_id": correlation_id},
                exc_info=True
            )
            raise
    
    async def _format_agent_response(
        self,
        reasoning_results: Dict[str, Any],
        district: Optional[str],
        meal_time: Optional[str],
        start_time: datetime,
        correlation_id: Optional[str]
    ) -> Dict[str, Any]:
        """
        Format the final response using agent intelligence.
        
        Args:
            reasoning_results: Results from reasoning MCP server
            district: Original district parameter
            meal_time: Original meal time parameter
            start_time: Request start time
            correlation_id: Request correlation ID
            
        Returns:
            Formatted response dictionary
        """
        logger.info(
            "Formatting agent response",
            extra={"correlation_id": correlation_id}
        )
        
        try:
            # Use Strands Agent to intelligently format the response
            agent_prompt = self._create_formatting_prompt(
                reasoning_results, district, meal_time, start_time
            )
            
            # Get agent response
            agent_response = await self.agent.process(agent_prompt)
            
            # Parse agent response as JSON
            try:
                formatted_response = json.loads(agent_response.content)
            except json.JSONDecodeError:
                # Fallback to manual formatting if agent response is not valid JSON
                logger.warning(
                    "Agent response not valid JSON, using fallback formatting",
                    extra={"correlation_id": correlation_id}
                )
                formatted_response = self._fallback_format_response(
                    reasoning_results, district, meal_time, start_time
                )
            
            # Validate and enhance response
            validated_response = self._validate_and_enhance_response(
                formatted_response, start_time, correlation_id
            )
            
            return validated_response
            
        except Exception as e:
            logger.error(
                f"Response formatting failed: {str(e)}",
                extra={"correlation_id": correlation_id},
                exc_info=True
            )
            
            # Use fallback formatting
            return self._fallback_format_response(
                reasoning_results, district, meal_time, start_time
            )
    
    def _create_formatting_prompt(
        self,
        reasoning_results: Dict[str, Any],
        district: Optional[str],
        meal_time: Optional[str],
        start_time: datetime
    ) -> str:
        """
        Create prompt for agent to format the response.
        
        Args:
            reasoning_results: Results from reasoning MCP server
            district: District parameter
            meal_time: Meal time parameter
            start_time: Request start time
            
        Returns:
            Formatted prompt string
        """
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        prompt = f"""Format the following restaurant recommendation data into the required JSON structure:

REASONING RESULTS:
{json.dumps(reasoning_results, indent=2)}

SEARCH CRITERIA:
- District: {district or 'Any'}
- Meal Time: {meal_time or 'Any'}
- Processing Time: {processing_time:.2f}ms

REQUIREMENTS:
1. Extract exactly 1 recommendation from the reasoning results
2. Extract up to 19 candidates from the reasoning results
3. Include comprehensive metadata
4. Ensure all restaurant objects have complete information
5. Return valid JSON only, no additional text

Format the response according to the system prompt structure."""
        
        return prompt
    
    def _fallback_format_response(
        self,
        reasoning_results: Dict[str, Any],
        district: Optional[str],
        meal_time: Optional[str],
        start_time: datetime
    ) -> Dict[str, Any]:
        """
        Fallback response formatting when agent formatting fails.
        
        Args:
            reasoning_results: Results from reasoning MCP server
            district: District parameter
            meal_time: Meal time parameter
            start_time: Request start time
            
        Returns:
            Formatted response dictionary
        """
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        # Extract recommendation and candidates from reasoning results
        recommendation = reasoning_results.get("recommendation")
        candidates = reasoning_results.get("candidates", [])
        
        # Ensure we have exactly 1 recommendation and up to 19 candidates
        if not recommendation and candidates:
            recommendation = candidates[0]
            candidates = candidates[1:20]  # Take up to 19 remaining
        elif candidates:
            candidates = candidates[:19]  # Limit to 19 candidates
        
        return {
            "recommendation": recommendation,
            "candidates": candidates,
            "metadata": {
                "search_criteria": {
                    "district": district,
                    "meal_time": meal_time
                },
                "total_found": len(candidates) + (1 if recommendation else 0),
                "timestamp": datetime.utcnow().isoformat(),
                "processing_time_ms": processing_time,
                "mcp_calls": ["search", "reasoning"],
                "formatted_by": "fallback"
            }
        }
    
    def _validate_and_enhance_response(
        self,
        response: Dict[str, Any],
        start_time: datetime,
        correlation_id: Optional[str]
    ) -> Dict[str, Any]:
        """
        Validate and enhance the formatted response.
        
        Args:
            response: Formatted response from agent
            start_time: Request start time
            correlation_id: Request correlation ID
            
        Returns:
            Validated and enhanced response
        """
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        # Ensure required fields exist
        if "recommendation" not in response:
            response["recommendation"] = None
        
        if "candidates" not in response:
            response["candidates"] = []
        
        if "metadata" not in response:
            response["metadata"] = {}
        
        # Enhance metadata
        response["metadata"].update({
            "timestamp": datetime.utcnow().isoformat(),
            "processing_time_ms": processing_time,
            "correlation_id": correlation_id,
            "agent_version": "1.0.0"
        })
        
        # Validate candidate count
        if len(response["candidates"]) > 19:
            response["candidates"] = response["candidates"][:19]
            logger.warning(
                "Truncated candidates to 19 items",
                extra={"correlation_id": correlation_id}
            )
        
        return response