"""
Main entrypoint for Restaurant Search MCP using BedrockAgentCoreApp.

This module implements the BedrockAgentCoreApp entrypoint that processes user prompts
and uses Strands Agent to automatically select and execute MCP tools for restaurant search.
"""

import json
import logging
import traceback
from datetime import datetime
from typing import Dict, Any, Optional, List

from bedrock_agentcore import BedrockAgentCoreApp
from strands_agents import Agent
from strands_agents.tools import Tool

from services.restaurant_service import RestaurantService
from services.district_service import DistrictService
from services.time_service import TimeService
from services.data_access import DataAccessClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize the BedrockAgentCoreApp
app = BedrockAgentCoreApp()

# Initialize services
data_access_client = DataAccessClient()
district_service = DistrictService()
time_service = TimeService()
restaurant_service = RestaurantService(data_access_client, district_service, time_service)

# Load district configuration on startup
try:
    district_service.load_district_config()
    logger.info("District configuration loaded successfully")
except Exception as e:
    logger.error(f"Failed to load district configuration: {e}")
    raise


def create_mcp_tools() -> list[Tool]:
    """Create MCP tools for the Strands Agent."""
    
    def search_restaurants_by_district(districts: list[str]) -> str:
        """
        Search for restaurants in specific districts.
        
        Args:
            districts: List of district names to search (e.g., ["Central district", "Tsim Sha Tsui"])
            
        Returns:
            JSON string containing restaurant data and metadata
        """
        try:
            logger.info(f"Searching restaurants by districts: {districts}")
            results = restaurant_service.search_by_districts(districts)
            
            response_data = {
                "success": True,
                "query_type": "district_search",
                "districts": districts,
                "restaurant_count": len(results),
                "restaurants": [restaurant.to_dict() for restaurant in results]
            }
            
            return json.dumps(response_data, ensure_ascii=False, indent=2)
            
        except Exception as e:
            logger.error(f"Error in search_restaurants_by_district: {e}")
            error_response = {
                "success": False,
                "error": str(e),
                "query_type": "district_search",
                "districts": districts
            }
            return json.dumps(error_response, ensure_ascii=False, indent=2)
    
    def search_restaurants_by_meal_type(meal_types: list[str]) -> str:
        """
        Search for restaurants by meal type based on operating hours.
        
        Args:
            meal_types: List of meal types ("breakfast", "lunch", "dinner")
            
        Returns:
            JSON string containing restaurant data filtered by operating hours
        """
        try:
            logger.info(f"Searching restaurants by meal types: {meal_types}")
            results = restaurant_service.search_by_meal_types(meal_types)
            
            response_data = {
                "success": True,
                "query_type": "meal_type_search",
                "meal_types": meal_types,
                "restaurant_count": len(results),
                "restaurants": [restaurant.to_dict() for restaurant in results]
            }
            
            return json.dumps(response_data, ensure_ascii=False, indent=2)
            
        except Exception as e:
            logger.error(f"Error in search_restaurants_by_meal_type: {e}")
            error_response = {
                "success": False,
                "error": str(e),
                "query_type": "meal_type_search",
                "meal_types": meal_types
            }
            return json.dumps(error_response, ensure_ascii=False, indent=2)
    
    def search_restaurants_combined(districts: Optional[list[str]] = None, 
                                  meal_types: Optional[list[str]] = None) -> str:
        """
        Search for restaurants by both district and meal type.
        
        Args:
            districts: Optional list of district names
            meal_types: Optional list of meal types ("breakfast", "lunch", "dinner")
            
        Returns:
            JSON string containing filtered restaurant data
        """
        try:
            logger.info(f"Combined search - districts: {districts}, meal_types: {meal_types}")
            results = restaurant_service.search_combined(districts, meal_types)
            
            response_data = {
                "success": True,
                "query_type": "combined_search",
                "districts": districts,
                "meal_types": meal_types,
                "restaurant_count": len(results),
                "restaurants": [restaurant.to_dict() for restaurant in results]
            }
            
            return json.dumps(response_data, ensure_ascii=False, indent=2)
            
        except Exception as e:
            logger.error(f"Error in search_restaurants_combined: {e}")
            error_response = {
                "success": False,
                "error": str(e),
                "query_type": "combined_search",
                "districts": districts,
                "meal_types": meal_types
            }
            return json.dumps(error_response, ensure_ascii=False, indent=2)
    
    # Create Tool objects for Strands Agent with detailed schemas
    tools = [
        Tool(
            name="search_restaurants_by_district",
            description="""Search for restaurants in specific Hong Kong districts. 
            Use this tool when users ask about restaurants in particular locations or areas.
            Available districts include: Admiralty, Central district, Causeway Bay, Wan Chai, 
            Tsim Sha Tsui, Mong Kok, Sha Tin, Tsuen Wan, and many others across Hong Kong Island, 
            Kowloon, New Territories, and Lantau.""",
            function=search_restaurants_by_district,
            parameters={
                "type": "object",
                "properties": {
                    "districts": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of Hong Kong district names. Examples: ['Central district'], ['Tsim Sha Tsui', 'Causeway Bay'], ['Admiralty']",
                        "minItems": 1
                    }
                },
                "required": ["districts"],
                "additionalProperties": False
            }
        ),
        Tool(
            name="search_restaurants_by_meal_type",
            description="""Search for restaurants by meal type based on their operating hours.
            Use this tool when users ask about breakfast, lunch, or dinner places.
            - Breakfast: 7:00-11:29 (morning dining)
            - Lunch: 11:30-17:29 (midday dining) 
            - Dinner: 17:30-22:30 (evening dining)
            The tool analyzes restaurant operating hours to determine meal availability.""",
            function=search_restaurants_by_meal_type,
            parameters={
                "type": "object",
                "properties": {
                    "meal_types": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": ["breakfast", "lunch", "dinner"]
                        },
                        "description": "List of meal types to search for. Use 'breakfast' for morning (7:00-11:29), 'lunch' for midday (11:30-17:29), 'dinner' for evening (17:30-22:30)",
                        "minItems": 1
                    }
                },
                "required": ["meal_types"],
                "additionalProperties": False
            }
        ),
        Tool(
            name="search_restaurants_combined",
            description="""Search for restaurants using both district and meal type filters.
            Use this tool when users specify both location and meal time preferences.
            This is the most flexible search option that can filter by either or both criteria.
            If only one parameter is provided, it will search by that single criterion.""",
            function=search_restaurants_combined,
            parameters={
                "type": "object",
                "properties": {
                    "districts": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional list of Hong Kong district names to filter by location",
                        "minItems": 1
                    },
                    "meal_types": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": ["breakfast", "lunch", "dinner"]
                        },
                        "description": "Optional list of meal types to filter by dining time",
                        "minItems": 1
                    }
                },
                "additionalProperties": False,
                "anyOf": [
                    {"required": ["districts"]},
                    {"required": ["meal_types"]},
                    {"required": ["districts", "meal_types"]}
                ]
            }
        )
    ]
    
    return tools


def create_strands_agent() -> Agent:
    """Create and configure the Strands Agent with MCP tools."""
    
    # Enhanced system prompt for restaurant search assistant
    system_prompt = """You are a knowledgeable and friendly restaurant search assistant for Hong Kong. 
    You help users discover restaurants across Hong Kong's diverse districts and dining times.
    
    ## Your Capabilities:
    You have access to comprehensive restaurant data organized by districts across:
    - Hong Kong Island: Admiralty, Central district, Causeway Bay, Wan Chai, etc.
    - Kowloon: Tsim Sha Tsui, Mong Kok, Yau Ma Tei, etc.
    - New Territories: Sha Tin, Tsuen Wan, Tai Po, etc.
    - Lantau: Tung Chung, Discovery Bay, etc.
    
    ## Meal Time Classifications:
    - Breakfast: 7:00-11:29 (morning dining, cafes, dim sum)
    - Lunch: 11:30-17:29 (business lunch, casual dining)
    - Dinner: 17:30-22:30 (evening dining, fine dining)
    
    ## Tool Selection Guidelines:
    - Use search_restaurants_by_district when users specify locations
    - Use search_restaurants_by_meal_type when users ask about specific meal times
    - Use search_restaurants_combined when users specify both location and meal time
    - Choose the most specific tool based on user intent
    
    ## Response Style:
    - Be conversational and helpful
    - Include key restaurant details (name, address, cuisine, hours, price range)
    - Format operating hours in a user-friendly way
    - Suggest alternatives when no results are found
    - Ask clarifying questions when the request is ambiguous
    - Provide context about districts or meal times when helpful
    
    ## Error Handling:
    - If a district name isn't recognized, suggest similar or nearby districts
    - If no restaurants match criteria, suggest broader searches or alternatives
    - Always maintain a helpful and positive tone
    
    Remember: Your goal is to help users find great dining experiences in Hong Kong!"""
    
    # Create MCP tools
    tools = create_mcp_tools()
    
    # Configure Strands Agent with optimized parameters
    agent = Agent(
        model="anthropic.claude-3-5-sonnet-20241022-v2:0",
        system_prompt=system_prompt,
        tools=tools,
        temperature=0.1,  # Low temperature for consistent tool calling
        max_tokens=2048,  # Sufficient for detailed responses
        top_p=0.9,       # Focused but not overly restrictive
        tool_choice="auto"  # Let the model choose appropriate tools
    )
    
    return agent


# Initialize the Strands Agent
strands_agent = create_strands_agent()


def extract_user_prompt(payload: Dict[str, Any]) -> str:
    """
    Extract user prompt from AgentCore Runtime payload.
    
    Args:
        payload: The payload received from AgentCore Runtime
        
    Returns:
        The user prompt string
        
    Raises:
        ValueError: If payload structure is invalid or prompt is missing
    """
    try:
        # Handle different payload structures
        if "input" in payload:
            if isinstance(payload["input"], dict):
                if "prompt" in payload["input"]:
                    return payload["input"]["prompt"]
                elif "message" in payload["input"]:
                    return payload["input"]["message"]
            elif isinstance(payload["input"], str):
                return payload["input"]
        
        if "prompt" in payload:
            return payload["prompt"]
        
        if "message" in payload:
            return payload["message"]
        
        # If no recognized structure, try to extract any string value
        for key, value in payload.items():
            if isinstance(value, str) and len(value.strip()) > 0:
                logger.warning(f"Using fallback prompt extraction from key: {key}")
                return value
        
        raise ValueError("No valid prompt found in payload")
        
    except Exception as e:
        logger.error(f"Error extracting prompt from payload: {e}")
        logger.error(f"Payload structure: {json.dumps(payload, indent=2)}")
        raise ValueError(f"Invalid payload structure: {e}")


def format_response(agent_response: str, success: bool = True, error: Optional[str] = None, 
                   metadata: Optional[Dict[str, Any]] = None) -> str:
    """
    Format the response to ensure JSON-serializable output with comprehensive metadata.
    
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
            "agent_type": "restaurant_search_assistant",
            "version": "1.0.0"
        }
        
        if error:
            response_data["error"] = {
                "message": error,
                "type": "processing_error" if not success else "warning"
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
            "response": "Unable to format response properly",
            "error": {
                "message": "Response formatting error",
                "type": "serialization_error",
                "details": str(e)
            },
            "timestamp": datetime.now().isoformat(),
            "agent_type": "restaurant_search_assistant"
        }
        return json.dumps(fallback_response, ensure_ascii=False)
    
    except Exception as e:
        logger.error(f"Unexpected error formatting response: {e}")
        # Ultimate fallback - simple string response
        return json.dumps({
            "success": False,
            "response": "System error occurred",
            "error": {"message": "Internal error", "type": "system_error"},
            "timestamp": datetime.now().isoformat()
        }, ensure_ascii=False)


def format_error_response(error_message: str, error_type: str = "processing_error", 
                         user_friendly_message: Optional[str] = None) -> str:
    """
    Format user-friendly error responses with troubleshooting guidance.
    
    Args:
        error_message: Technical error message
        error_type: Type of error (validation_error, processing_error, system_error)
        user_friendly_message: Optional user-friendly error message
        
    Returns:
        JSON-serializable error response
    """
    if not user_friendly_message:
        # Generate user-friendly messages based on error type
        if "district" in error_message.lower():
            user_friendly_message = ("I don't recognize that district name. "
                                   "Could you try a well-known Hong Kong district like "
                                   "Central district, Tsim Sha Tsui, or Causeway Bay?")
        elif "meal" in error_message.lower():
            user_friendly_message = ("Please specify a valid meal type: "
                                   "breakfast, lunch, or dinner.")
        elif "payload" in error_message.lower():
            user_friendly_message = ("I'm having trouble understanding your request. "
                                   "Could you please rephrase your question about restaurants?")
        else:
            user_friendly_message = ("I'm experiencing technical difficulties. "
                                   "Please try again in a moment.")
    
    error_data = {
        "success": False,
        "response": user_friendly_message,
        "error": {
            "message": error_message,
            "type": error_type,
            "user_message": user_friendly_message
        },
        "timestamp": datetime.now().isoformat(),
        "agent_type": "restaurant_search_assistant",
        "suggestions": get_error_suggestions(error_type)
    }
    
    return json.dumps(error_data, ensure_ascii=False, indent=2)


def get_error_suggestions(error_type: str) -> List[str]:
    """
    Get helpful suggestions based on error type.
    
    Args:
        error_type: The type of error that occurred
        
    Returns:
        List of helpful suggestions for the user
    """
    suggestions = {
        "validation_error": [
            "Try asking about restaurants in a specific Hong Kong district",
            "Specify a meal type: breakfast, lunch, or dinner",
            "Use district names like 'Central district' or 'Tsim Sha Tsui'"
        ],
        "processing_error": [
            "Try rephrasing your question",
            "Be more specific about the location or meal type",
            "Ask about a different district or time"
        ],
        "system_error": [
            "Please try again in a few moments",
            "Check your internet connection",
            "Try a simpler query first"
        ]
    }
    
    return suggestions.get(error_type, [
        "Please try rephrasing your question",
        "Be more specific about what you're looking for"
    ])


def log_request_processing(payload: Dict[str, Any], user_prompt: str, 
                          success: bool, error: Optional[str] = None) -> None:
    """
    Log request processing details for debugging and monitoring.
    
    Args:
        payload: Original payload received
        user_prompt: Extracted user prompt
        success: Whether processing was successful
        error: Optional error message
    """
    log_data = {
        "timestamp": datetime.now().isoformat(),
        "payload_keys": list(payload.keys()) if payload else [],
        "user_prompt_length": len(user_prompt) if user_prompt else 0,
        "success": success,
        "has_error": error is not None
    }
    
    if success:
        logger.info(f"Request processed successfully: {log_data}")
    else:
        logger.error(f"Request processing failed: {log_data}, error: {error}")
    
    # Log payload structure for debugging (without sensitive data)
    if not success and payload:
        logger.debug(f"Payload structure for failed request: {json.dumps(payload, indent=2)}")


@app.entrypoint
def process_request(payload: Dict[str, Any]) -> str:
    """
    Main entrypoint for processing AgentCore Runtime requests.
    
    Args:
        payload: The payload received from AgentCore Runtime
        
    Returns:
        JSON-serializable string containing the formatted response
    """
    user_prompt = None
    
    try:
        logger.info(f"Processing entrypoint request with payload keys: {list(payload.keys())}")
        
        # Extract user prompt from payload
        user_prompt = extract_user_prompt(payload)
        logger.info(f"Extracted user prompt: {user_prompt[:100]}..." if len(user_prompt) > 100 else f"Extracted user prompt: {user_prompt}")
        
        # Process the prompt with Strands Agent
        agent_response = strands_agent.run(user_prompt)
        logger.info("Agent response generated successfully")
        
        # Create metadata for successful response
        metadata = {
            "prompt_length": len(user_prompt),
            "processing_time": "completed",
            "tools_available": ["search_restaurants_by_district", "search_restaurants_by_meal_type", "search_restaurants_combined"]
        }
        
        # Format and return response
        formatted_response = format_response(agent_response, success=True, metadata=metadata)
        
        # Log successful processing
        log_request_processing(payload, user_prompt, success=True)
        
        return formatted_response
        
    except ValueError as e:
        logger.error(f"Payload validation error: {e}")
        
        # Log failed processing
        log_request_processing(payload, user_prompt, success=False, error=str(e))
        
        # Return user-friendly error response
        return format_error_response(
            error_message=str(e),
            error_type="validation_error",
            user_friendly_message="I'm sorry, I couldn't understand your request. Please try rephrasing your question about restaurants in Hong Kong."
        )
        
    except Exception as e:
        logger.error(f"Unexpected error in entrypoint: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        # Log failed processing
        log_request_processing(payload, user_prompt, success=False, error=str(e))
        
        # Return system error response
        return format_error_response(
            error_message=str(e),
            error_type="system_error",
            user_friendly_message="I'm experiencing technical difficulties. Please try again in a moment."
        )


if __name__ == "__main__":
    # Run the BedrockAgentCore application
    logger.info("Starting Restaurant Search MCP EntryPoint")
    app.run()