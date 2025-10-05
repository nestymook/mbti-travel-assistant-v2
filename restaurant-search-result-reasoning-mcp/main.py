"""
Main entrypoint for Restaurant Reasoning MCP using BedrockAgentCoreApp.

This module implements the BedrockAgentCoreApp entrypoint that processes user prompts
and restaurant data, using Strands Agent to automatically select and execute MCP tools 
for restaurant sentiment analysis and intelligent recommendations.
Enhanced with dual monitoring capabilities using MCP tools/list and REST health checks.
"""

import json
import logging
import traceback
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, List

from bedrock_agentcore import BedrockAgentCoreApp
from strands import Agent
from strands_agents.tools import Tool

from services.restaurant_reasoning_service import RestaurantReasoningService
from services.sentiment_service import SentimentAnalysisService
from services.recommendation_service import RecommendationAlgorithm
from services.validation_service import RestaurantDataValidator
from models.restaurant_models import Restaurant, Sentiment, RecommendationResult
from services.enhanced_reasoning_status_service import (
    initialize_enhanced_reasoning_status_service, 
    start_enhanced_reasoning_status_service
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize the BedrockAgentCoreApp
app = BedrockAgentCoreApp()

# Initialize services
reasoning_service = RestaurantReasoningService()
sentiment_service = SentimentAnalysisService()
recommendation_algorithm = RecommendationAlgorithm()
data_validator = RestaurantDataValidator()


def create_reasoning_mcp_tools() -> List[Tool]:
    """Create MCP tools for restaurant reasoning with the Strands Agent."""
    
    def recommend_restaurants(restaurants: List[Dict[str, Any]], 
                            ranking_method: str = "sentiment_likes") -> str:
        """
        Analyze restaurant sentiment data and provide intelligent recommendations.
        
        Args:
            restaurants: List of restaurant objects with sentiment data
            ranking_method: Ranking method ("sentiment_likes" or "combined_sentiment")
            
        Returns:
            JSON string containing candidate list (top 20) and single recommendation
        """
        try:
            logger.info(f"Processing recommendation request for {len(restaurants)} restaurants with method: {ranking_method}")
            
            # Use the reasoning service to analyze and recommend
            result = reasoning_service.analyze_and_recommend(restaurants, ranking_method)
            
            # Format response with metadata
            response_data = {
                "success": True,
                "recommendation_type": "intelligent_analysis",
                "ranking_method": ranking_method,
                "total_restaurants": len(restaurants),
                "candidates_count": len(result.candidates),
                "recommendation": {
                    "id": result.recommendation.id,
                    "name": result.recommendation.name,
                    "address": getattr(result.recommendation, 'address', 'Address not available'),
                    "sentiment": {
                        "likes": result.recommendation.sentiment.likes,
                        "dislikes": result.recommendation.sentiment.dislikes,
                        "neutral": result.recommendation.sentiment.neutral,
                        "likes_percentage": result.recommendation.sentiment.likes_percentage(),
                        "combined_positive_percentage": result.recommendation.sentiment.combined_positive_percentage()
                    },
                    "meal_type": getattr(result.recommendation, 'meal_type', []),
                    "district": getattr(result.recommendation, 'district', 'Not specified'),
                    "price_range": getattr(result.recommendation, 'price_range', 'Not specified')
                },
                "candidates": [
                    {
                        "id": candidate.id,
                        "name": candidate.name,
                        "sentiment_score": candidate.sentiment.likes_percentage() if ranking_method == "sentiment_likes" else candidate.sentiment.combined_positive_percentage(),
                        "likes": candidate.sentiment.likes,
                        "total_responses": candidate.sentiment.total_responses()
                    }
                    for candidate in result.candidates[:10]  # Show top 10 in summary
                ],
                "analysis_summary": result.analysis_summary,
                "timestamp": datetime.now().isoformat()
            }
            
            return json.dumps(response_data, ensure_ascii=False, indent=2)
            
        except Exception as e:
            logger.error(f"Error in recommend_restaurants: {e}")
            error_response = {
                "success": False,
                "error": {
                    "message": str(e),
                    "type": "recommendation_error"
                },
                "ranking_method": ranking_method,
                "total_restaurants": len(restaurants) if restaurants else 0,
                "timestamp": datetime.now().isoformat()
            }
            return json.dumps(error_response, ensure_ascii=False, indent=2)
    
    def analyze_restaurant_sentiment(restaurants: List[Dict[str, Any]]) -> str:
        """
        Analyze sentiment data for a list of restaurants without providing recommendations.
        
        Args:
            restaurants: List of restaurant objects with sentiment data
            
        Returns:
            JSON string containing sentiment analysis results
        """
        try:
            logger.info(f"Processing sentiment analysis for {len(restaurants)} restaurants")
            
            # Validate restaurant data
            validation_errors = []
            valid_restaurants = []
            
            for i, restaurant_data in enumerate(restaurants):
                validation_result = data_validator.validate_restaurant_structure(restaurant_data)
                if validation_result.is_valid:
                    valid_restaurants.append(restaurant_data)
                else:
                    validation_errors.append({
                        "index": i,
                        "restaurant_id": restaurant_data.get('id', f'restaurant_{i}'),
                        "errors": validation_result.errors
                    })
            
            if not valid_restaurants:
                raise ValueError("No valid restaurants found for sentiment analysis")
            
            # Perform sentiment analysis
            sentiment_scores = []
            total_likes = 0
            total_dislikes = 0
            total_neutral = 0
            
            for restaurant_data in valid_restaurants:
                sentiment_data = restaurant_data.get('sentiment', {})
                sentiment = Sentiment(
                    likes=sentiment_data.get('likes', 0),
                    dislikes=sentiment_data.get('dislikes', 0),
                    neutral=sentiment_data.get('neutral', 0)
                )
                
                likes_pct = sentiment.likes_percentage()
                combined_pct = sentiment.combined_positive_percentage()
                
                sentiment_scores.append({
                    "restaurant_id": restaurant_data.get('id'),
                    "restaurant_name": restaurant_data.get('name'),
                    "likes": sentiment.likes,
                    "dislikes": sentiment.dislikes,
                    "neutral": sentiment.neutral,
                    "total_responses": sentiment.total_responses(),
                    "likes_percentage": likes_pct,
                    "combined_positive_percentage": combined_pct
                })
                
                total_likes += sentiment.likes
                total_dislikes += sentiment.dislikes
                total_neutral += sentiment.neutral
            
            # Calculate overall statistics
            total_responses = total_likes + total_dislikes + total_neutral
            avg_likes_pct = (total_likes / total_responses * 100) if total_responses > 0 else 0
            avg_combined_pct = ((total_likes + total_neutral) / total_responses * 100) if total_responses > 0 else 0
            
            response_data = {
                "success": True,
                "analysis_type": "sentiment_analysis",
                "total_restaurants_analyzed": len(valid_restaurants),
                "validation_errors": validation_errors,
                "overall_statistics": {
                    "total_likes": total_likes,
                    "total_dislikes": total_dislikes,
                    "total_neutral": total_neutral,
                    "total_responses": total_responses,
                    "average_likes_percentage": round(avg_likes_pct, 2),
                    "average_combined_positive_percentage": round(avg_combined_pct, 2)
                },
                "restaurant_sentiment_scores": sentiment_scores,
                "timestamp": datetime.now().isoformat()
            }
            
            return json.dumps(response_data, ensure_ascii=False, indent=2)
            
        except Exception as e:
            logger.error(f"Error in analyze_restaurant_sentiment: {e}")
            error_response = {
                "success": False,
                "error": {
                    "message": str(e),
                    "type": "sentiment_analysis_error"
                },
                "total_restaurants": len(restaurants) if restaurants else 0,
                "timestamp": datetime.now().isoformat()
            }
            return json.dumps(error_response, ensure_ascii=False, indent=2)
    
    # Create Tool objects for Strands Agent with detailed schemas
    tools = [
        Tool(
            name="recommend_restaurants",
            description="""Analyze restaurant sentiment data and provide intelligent recommendations.
            Use this tool when users want recommendations based on customer satisfaction metrics.
            The tool analyzes sentiment data (likes, dislikes, neutral) to rank restaurants and 
            provides both a list of top candidates and a single recommended restaurant.
            
            Ranking methods:
            - sentiment_likes: Ranks by highest number of likes
            - combined_sentiment: Ranks by combined likes + neutral percentage
            
            Returns top 20 candidates and randomly selects 1 recommendation from the top candidates.""",
            function=recommend_restaurants,
            parameters={
                "type": "object",
                "properties": {
                    "restaurants": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "string", "description": "Unique restaurant identifier"},
                                "name": {"type": "string", "description": "Restaurant name"},
                                "sentiment": {
                                    "type": "object",
                                    "properties": {
                                        "likes": {"type": "integer", "minimum": 0},
                                        "dislikes": {"type": "integer", "minimum": 0},
                                        "neutral": {"type": "integer", "minimum": 0}
                                    },
                                    "required": ["likes", "dislikes", "neutral"]
                                }
                            },
                            "required": ["id", "name", "sentiment"]
                        },
                        "description": "List of restaurant objects with sentiment data",
                        "minItems": 1
                    },
                    "ranking_method": {
                        "type": "string",
                        "enum": ["sentiment_likes", "combined_sentiment"],
                        "default": "sentiment_likes",
                        "description": "Method for ranking restaurants: 'sentiment_likes' (by likes count) or 'combined_sentiment' (by likes + neutral percentage)"
                    }
                },
                "required": ["restaurants"],
                "additionalProperties": False
            }
        ),
        Tool(
            name="analyze_restaurant_sentiment",
            description="""Analyze sentiment data for restaurants without providing recommendations.
            Use this tool when users want to understand sentiment patterns, statistics, or 
            analysis of restaurant customer satisfaction without needing a specific recommendation.
            
            Provides detailed sentiment analysis including:
            - Individual restaurant sentiment scores and percentages
            - Overall statistics across all restaurants
            - Validation results for data quality
            - Likes percentage and combined positive (likes + neutral) percentage""",
            function=analyze_restaurant_sentiment,
            parameters={
                "type": "object",
                "properties": {
                    "restaurants": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "string", "description": "Unique restaurant identifier"},
                                "name": {"type": "string", "description": "Restaurant name"},
                                "sentiment": {
                                    "type": "object",
                                    "properties": {
                                        "likes": {"type": "integer", "minimum": 0},
                                        "dislikes": {"type": "integer", "minimum": 0},
                                        "neutral": {"type": "integer", "minimum": 0}
                                    },
                                    "required": ["likes", "dislikes", "neutral"]
                                }
                            },
                            "required": ["id", "name", "sentiment"]
                        },
                        "description": "List of restaurant objects with sentiment data for analysis",
                        "minItems": 1
                    }
                },
                "required": ["restaurants"],
                "additionalProperties": False
            }
        )
    ]
    
    return tools


def create_reasoning_strands_agent() -> Agent:
    """Create and configure the Strands Agent with reasoning MCP tools."""
    
    # Enhanced system prompt for restaurant reasoning assistant
    system_prompt = """You are an intelligent restaurant recommendation assistant that specializes in 
    sentiment analysis and data-driven recommendations. You help users analyze restaurant customer 
    satisfaction data and provide smart recommendations based on sentiment metrics.
    
    ## Your Capabilities:
    You can analyze restaurant sentiment data including:
    - Customer likes, dislikes, and neutral responses
    - Sentiment percentages and satisfaction scores
    - Ranking algorithms for identifying top restaurants
    - Intelligent recommendation selection from top candidates
    
    ## Tool Selection Guidelines:
    - Use recommend_restaurants when users want specific restaurant recommendations based on sentiment
    - Use analyze_restaurant_sentiment when users want to understand sentiment patterns or statistics
    - Choose ranking methods based on user preferences:
      * sentiment_likes: Focus on restaurants with highest customer likes
      * combined_sentiment: Consider both likes and neutral responses (more inclusive)
    
    ## Data Requirements:
    Restaurant data must include:
    - id: Unique identifier
    - name: Restaurant name  
    - sentiment: Object with likes, dislikes, neutral (all integers ≥ 0)
    
    Optional fields: address, meal_type, district, price_range, operating_hours
    
    ## Response Style:
    - Provide clear explanations of sentiment analysis results
    - Explain ranking methodology when giving recommendations
    - Include key metrics (likes percentage, total responses, sentiment scores)
    - Format responses in a conversational, easy-to-understand manner
    - Suggest alternative approaches when appropriate
    
    ## Error Handling:
    - Validate restaurant data structure before analysis
    - Provide helpful error messages for invalid data
    - Suggest corrections for common data format issues
    - Handle edge cases (zero responses, missing fields) gracefully
    
    ## Analysis Insights:
    - Explain what sentiment metrics mean for restaurant quality
    - Compare different ranking methods and their implications
    - Provide context about recommendation confidence and methodology
    - Highlight interesting patterns in sentiment data
    
    Remember: Your goal is to help users make data-driven decisions about restaurants using 
    customer sentiment analysis and intelligent recommendation algorithms!"""
    
    # Create reasoning MCP tools
    tools = create_reasoning_mcp_tools()
    
    # Configure Strands Agent with optimized parameters for reasoning tasks
    agent = Agent(
        model="amazon.nova-pro-v1:0",
        system_prompt=system_prompt,
        tools=tools,
        temperature=0.1,  # Low temperature for consistent analytical reasoning
        max_tokens=2048,  # Sufficient for detailed analysis and explanations
        top_p=0.9,       # Focused but allows for creative explanations
        tool_choice="auto"  # Let the model choose appropriate reasoning tools
    )
    
    return agent


# Initialize the Strands Agent for reasoning
reasoning_strands_agent = create_reasoning_strands_agent()


def extract_user_prompt_and_data(payload: Dict[str, Any]) -> tuple[str, Optional[List[Dict[str, Any]]]]:
    """
    Extract user prompt and restaurant data from AgentCore Runtime payload.
    
    Args:
        payload: The payload received from AgentCore Runtime
        
    Returns:
        Tuple of (user_prompt, restaurant_data) where restaurant_data may be None
        
    Raises:
        ValueError: If payload structure is invalid or prompt is missing
    """
    try:
        user_prompt = None
        restaurant_data = None
        
        # Handle different payload structures for prompt extraction
        if "input" in payload:
            if isinstance(payload["input"], dict):
                if "prompt" in payload["input"]:
                    user_prompt = payload["input"]["prompt"]
                elif "message" in payload["input"]:
                    user_prompt = payload["input"]["message"]
                
                # Look for restaurant data in input
                if "restaurant_data" in payload["input"]:
                    restaurant_data = payload["input"]["restaurant_data"]
                elif "restaurants" in payload["input"]:
                    restaurant_data = payload["input"]["restaurants"]
                    
            elif isinstance(payload["input"], str):
                user_prompt = payload["input"]
        
        if not user_prompt:
            if "prompt" in payload:
                user_prompt = payload["prompt"]
            elif "message" in payload:
                user_prompt = payload["message"]
        
        # Look for restaurant data at top level
        if not restaurant_data:
            if "restaurant_data" in payload:
                restaurant_data = payload["restaurant_data"]
            elif "restaurants" in payload:
                restaurant_data = payload["restaurants"]
        
        # If no recognized prompt structure, try to extract any string value
        if not user_prompt:
            for key, value in payload.items():
                if isinstance(value, str) and len(value.strip()) > 0:
                    logger.warning(f"Using fallback prompt extraction from key: {key}")
                    user_prompt = value
                    break
        
        if not user_prompt:
            raise ValueError("No valid prompt found in payload")
        
        return user_prompt, restaurant_data
        
    except Exception as e:
        logger.error(f"Error extracting prompt and data from payload: {e}")
        logger.error(f"Payload structure: {json.dumps(payload, indent=2)}")
        raise ValueError(f"Invalid payload structure: {e}")


def format_reasoning_response(agent_response: str, success: bool = True, 
                            error: Optional[str] = None, 
                            metadata: Optional[Dict[str, Any]] = None) -> str:
    """
    Format the response for reasoning operations with comprehensive metadata.
    
    Args:
        agent_response: The response from the Strands Agent
        success: Whether the operation was successful
        error: Optional error message
        metadata: Optional additional metadata to include
        
    Returns:
        JSON-serializable string response
    """
    try:
        response_data = {
            "success": success,
            "response": agent_response,
            "timestamp": datetime.now().isoformat(),
            "agent_type": "restaurant_reasoning_assistant",
            "version": "1.0.0",
            "capabilities": [
                "sentiment_analysis",
                "intelligent_recommendations", 
                "ranking_algorithms",
                "data_validation"
            ]
        }
        
        if error:
            response_data["error"] = {
                "message": error,
                "type": "reasoning_error" if not success else "warning"
            }
        
        if metadata:
            response_data["metadata"] = metadata
        
        # Ensure response is properly formatted and serializable
        formatted_json = json.dumps(response_data, ensure_ascii=False, indent=2)
        
        # Validate JSON serialization
        json.loads(formatted_json)  # This will raise an exception if invalid
        
        return formatted_json
        
    except (TypeError, ValueError) as e:
        logger.error(f"JSON serialization error: {e}")
        # Create a safe fallback response
        fallback_response = {
            "success": False,
            "response": "Unable to format reasoning response properly",
            "error": {
                "message": "Response formatting error",
                "type": "serialization_error",
                "details": str(e)
            },
            "timestamp": datetime.now().isoformat(),
            "agent_type": "restaurant_reasoning_assistant"
        }
        return json.dumps(fallback_response, ensure_ascii=False)
    
    except Exception as e:
        logger.error(f"Unexpected error formatting reasoning response: {e}")
        # Ultimate fallback - simple string response
        return json.dumps({
            "success": False,
            "response": "System error occurred during reasoning",
            "error": {"message": "Internal reasoning error", "type": "system_error"},
            "timestamp": datetime.now().isoformat()
        }, ensure_ascii=False)


def format_reasoning_error_response(error_message: str, error_type: str = "reasoning_error", 
                                  user_friendly_message: Optional[str] = None) -> str:
    """
    Format user-friendly error responses for reasoning operations.
    
    Args:
        error_message: Technical error message
        error_type: Type of error (validation_error, reasoning_error, data_error)
        user_friendly_message: Optional user-friendly error message
        
    Returns:
        JSON-serializable error response
    """
    if not user_friendly_message:
        # Generate user-friendly messages based on error type
        if "sentiment" in error_message.lower():
            user_friendly_message = ("I need restaurant data with sentiment information (likes, dislikes, neutral) "
                                   "to perform analysis. Please provide restaurant data with customer feedback metrics.")
        elif "validation" in error_message.lower() or "invalid" in error_message.lower():
            user_friendly_message = ("The restaurant data format seems incorrect. Please ensure each restaurant "
                                   "has an 'id', 'name', and 'sentiment' object with likes, dislikes, and neutral counts.")
        elif "empty" in error_message.lower() or "no restaurants" in error_message.lower():
            user_friendly_message = ("I don't see any restaurant data to analyze. Please provide a list of restaurants "
                                   "with sentiment information for analysis and recommendations.")
        elif "payload" in error_message.lower():
            user_friendly_message = ("I'm having trouble understanding your request. Please provide restaurant data "
                                   "and specify what kind of analysis or recommendations you'd like.")
        else:
            user_friendly_message = ("I'm experiencing technical difficulties with the sentiment analysis. "
                                   "Please try again with properly formatted restaurant data.")
    
    error_data = {
        "success": False,
        "response": user_friendly_message,
        "error": {
            "message": error_message,
            "type": error_type,
            "user_message": user_friendly_message
        },
        "timestamp": datetime.now().isoformat(),
        "agent_type": "restaurant_reasoning_assistant",
        "suggestions": get_reasoning_error_suggestions(error_type)
    }
    
    return json.dumps(error_data, ensure_ascii=False, indent=2)


def get_reasoning_error_suggestions(error_type: str) -> List[str]:
    """
    Get helpful suggestions for reasoning errors.
    
    Args:
        error_type: The type of error that occurred
        
    Returns:
        List of helpful suggestions for the user
    """
    suggestions = {
        "validation_error": [
            "Ensure each restaurant has 'id', 'name', and 'sentiment' fields",
            "Sentiment data should include 'likes', 'dislikes', and 'neutral' as integers",
            "Check that all sentiment values are non-negative numbers"
        ],
        "reasoning_error": [
            "Try providing restaurant data with valid sentiment information",
            "Specify whether you want recommendations or just sentiment analysis",
            "Check that restaurant data includes customer feedback metrics"
        ],
        "data_error": [
            "Provide restaurant data in the correct JSON format",
            "Include sentiment data for each restaurant",
            "Ensure all required fields are present and properly formatted"
        ]
    }
    
    return suggestions.get(error_type, [
        "Please provide restaurant data with sentiment information",
        "Specify what kind of analysis or recommendations you need",
        "Check the data format and try again"
    ])


def log_reasoning_request_processing(payload: Dict[str, Any], user_prompt: str, 
                                   has_restaurant_data: bool, success: bool, 
                                   error: Optional[str] = None) -> None:
    """
    Log reasoning request processing details for debugging and monitoring.
    
    Args:
        payload: Original payload received
        user_prompt: Extracted user prompt
        has_restaurant_data: Whether restaurant data was provided
        success: Whether processing was successful
        error: Optional error message
    """
    log_data = {
        "timestamp": datetime.now().isoformat(),
        "payload_keys": list(payload.keys()) if payload else [],
        "user_prompt_length": len(user_prompt) if user_prompt else 0,
        "has_restaurant_data": has_restaurant_data,
        "success": success,
        "has_error": error is not None,
        "operation_type": "restaurant_reasoning"
    }
    
    if success:
        logger.info(f"Reasoning request processed successfully: {log_data}")
    else:
        logger.error(f"Reasoning request processing failed: {log_data}, error: {error}")
    
    # Log payload structure for debugging (without sensitive data)
    if not success and payload:
        logger.debug(f"Payload structure for failed reasoning request: {json.dumps(payload, indent=2)}")


@app.entrypoint
def process_reasoning_request(payload: Dict[str, Any]) -> str:
    """
    Main entrypoint for processing AgentCore Runtime requests for restaurant reasoning.
    
    Args:
        payload: The payload received from AgentCore Runtime
        
    Returns:
        JSON-serializable string containing the formatted reasoning response
    """
    user_prompt = None
    restaurant_data = None
    
    try:
        logger.info(f"Processing reasoning entrypoint request with payload keys: {list(payload.keys())}")
        
        # Extract user prompt and restaurant data from payload
        user_prompt, restaurant_data = extract_user_prompt_and_data(payload)
        logger.info(f"Extracted user prompt: {user_prompt[:100]}..." if len(user_prompt) > 100 else f"Extracted user prompt: {user_prompt}")
        logger.info(f"Restaurant data provided: {restaurant_data is not None}")
        
        # If restaurant data is provided in payload, include it in the prompt context
        enhanced_prompt = user_prompt
        if restaurant_data:
            enhanced_prompt = f"{user_prompt}\n\nRestaurant data to analyze:\n{json.dumps(restaurant_data, indent=2)}"
        
        # Process the prompt with Strands Agent
        agent_response = reasoning_strands_agent.run(enhanced_prompt)
        logger.info("Reasoning agent response generated successfully")
        
        # Create metadata for successful response
        metadata = {
            "prompt_length": len(user_prompt),
            "has_restaurant_data": restaurant_data is not None,
            "restaurant_count": len(restaurant_data) if restaurant_data else 0,
            "processing_time": "completed",
            "tools_available": ["recommend_restaurants", "analyze_restaurant_sentiment"],
            "reasoning_capabilities": ["sentiment_analysis", "intelligent_recommendations", "ranking_algorithms"]
        }
        
        # Format and return response
        formatted_response = format_reasoning_response(agent_response, success=True, metadata=metadata)
        
        # Log successful processing
        log_reasoning_request_processing(payload, user_prompt, restaurant_data is not None, success=True)
        
        return formatted_response
        
    except ValueError as e:
        logger.error(f"Payload validation error: {e}")
        
        # Log failed processing
        log_reasoning_request_processing(payload, user_prompt, restaurant_data is not None, success=False, error=str(e))
        
        # Return user-friendly error response
        return format_reasoning_error_response(
            error_message=str(e),
            error_type="validation_error",
            user_friendly_message="I'm sorry, I couldn't understand your request. Please provide restaurant data with sentiment information for analysis and recommendations."
        )
        
    except Exception as e:
        logger.error(f"Unexpected error in reasoning entrypoint: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        # Log failed processing
        log_reasoning_request_processing(payload, user_prompt, restaurant_data is not None, success=False, error=str(e))
        
        # Return system error response
        return format_reasoning_error_response(
            error_message=str(e),
            error_type="reasoning_error",
            user_friendly_message="I'm experiencing technical difficulties with the sentiment analysis. Please try again in a moment."
        )


async def startup_enhanced_reasoning_monitoring():
    """Initialize and start enhanced reasoning monitoring services."""
    try:
        logger.info("Initializing enhanced reasoning status monitoring")
        await initialize_enhanced_reasoning_status_service()
        await start_enhanced_reasoning_status_service()
        logger.info("Enhanced reasoning status monitoring started successfully")
    except Exception as e:
        logger.error(f"Failed to start enhanced reasoning monitoring: {e}")
        # Continue without enhanced monitoring
        pass


if __name__ == "__main__":
    # Initialize enhanced reasoning monitoring
    try:
        asyncio.run(startup_enhanced_reasoning_monitoring())
    except Exception as e:
        logger.warning(f"Enhanced reasoning monitoring initialization failed: {e}")
    
    # Run the BedrockAgentCore application for reasoning
    logger.info("Starting Restaurant Reasoning MCP EntryPoint with Enhanced Monitoring")
    app.run()