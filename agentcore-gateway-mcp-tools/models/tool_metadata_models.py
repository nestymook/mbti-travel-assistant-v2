"""
Tool metadata models for AgentCore Gateway MCP Tools.

This module contains Pydantic models for providing comprehensive tool metadata
to foundation models. These models help AI models understand when and how to
use each restaurant search and reasoning tool effectively.
"""

from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field
from enum import Enum


class ParameterType(str, Enum):
    """Parameter types for tool metadata."""
    STRING = "string"
    INTEGER = "integer"
    NUMBER = "number"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"


class ToolCategory(str, Enum):
    """Categories of tools available."""
    SEARCH = "search"
    ANALYSIS = "analysis"
    RECOMMENDATION = "recommendation"


class MBTIPersonalityType(str, Enum):
    """MBTI personality types for integration guidance."""
    ENFJ = "ENFJ"
    ENFP = "ENFP"
    ENTJ = "ENTJ"
    ENTP = "ENTP"
    ESFJ = "ESFJ"
    ESFP = "ESFP"
    ESTJ = "ESTJ"
    ESTP = "ESTP"
    INFJ = "INFJ"
    INFP = "INFP"
    INTJ = "INTJ"
    INTP = "INTP"
    ISFJ = "ISFJ"
    ISFP = "ISFP"
    ISTJ = "ISTJ"
    ISTP = "ISTP"


class ParameterSchema(BaseModel):
    """Schema definition for tool parameters."""
    
    type: ParameterType = Field(..., description="Parameter data type")
    description: str = Field(..., description="Parameter description")
    required: bool = Field(default=False, description="Whether parameter is required")
    default: Optional[Any] = Field(None, description="Default value if not required")
    enum: Optional[List[str]] = Field(None, description="Valid enum values")
    min_items: Optional[int] = Field(None, description="Minimum items for arrays")
    max_items: Optional[int] = Field(None, description="Maximum items for arrays")
    pattern: Optional[str] = Field(None, description="Regex pattern for string validation")
    example: Optional[Any] = Field(None, description="Example value")
    
    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "type": "array",
                "description": "List of Hong Kong districts to search",
                "required": True,
                "min_items": 1,
                "max_items": 20,
                "example": ["Central district", "Admiralty"]
            }
        }


class ResponseSchema(BaseModel):
    """Schema definition for tool responses."""
    
    type: ParameterType = Field(..., description="Response data type")
    description: str = Field(..., description="Response description")
    properties: Optional[Dict[str, ParameterSchema]] = Field(None, description="Object properties")
    items: Optional["ResponseSchema"] = Field(None, description="Array item schema")
    example: Optional[Any] = Field(None, description="Example response")
    
    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "type": "object",
                "description": "Restaurant search results",
                "properties": {
                    "restaurants": {
                        "type": "array",
                        "description": "List of matching restaurants"
                    }
                }
            }
        }


class UseCaseScenario(BaseModel):
    """Use case scenario for tool usage."""
    
    scenario: str = Field(..., description="Scenario description")
    when_to_use: str = Field(..., description="When to use this tool")
    example_input: Dict[str, Any] = Field(..., description="Example input for this scenario")
    expected_outcome: str = Field(..., description="Expected outcome description")
    
    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "scenario": "Tourist looking for breakfast options in Central",
                "when_to_use": "When user wants restaurants in specific districts for specific meal times",
                "example_input": {
                    "districts": ["Central district"],
                    "meal_types": ["breakfast"]
                },
                "expected_outcome": "List of restaurants in Central district that serve breakfast"
            }
        }


class MBTIIntegrationGuidance(BaseModel):
    """MBTI personality type integration guidance."""
    
    personality_type: MBTIPersonalityType = Field(..., description="MBTI personality type")
    preferences: List[str] = Field(..., description="Preferences for this personality type")
    search_patterns: List[str] = Field(..., description="Common search patterns")
    recommendation_focus: str = Field(..., description="What to focus on for recommendations")
    
    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "personality_type": "ENFP",
                "preferences": ["Variety", "Social atmosphere", "Unique experiences"],
                "search_patterns": ["Multiple districts", "All meal types", "High sentiment scores"],
                "recommendation_focus": "Restaurants with high social engagement and positive reviews"
            }
        }


class ToolExample(BaseModel):
    """Example usage of a tool."""
    
    title: str = Field(..., description="Example title")
    description: str = Field(..., description="Example description")
    input: Dict[str, Any] = Field(..., description="Example input")
    output: Dict[str, Any] = Field(..., description="Example output")
    notes: Optional[str] = Field(None, description="Additional notes")
    
    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "title": "Search restaurants in Central for lunch",
                "description": "Find lunch restaurants in Central district",
                "input": {
                    "districts": ["Central district"],
                    "meal_types": ["lunch"]
                },
                "output": {
                    "success": True,
                    "restaurants": [
                        {
                            "id": "rest_001",
                            "name": "Central Lunch Spot",
                            "district": "Central district"
                        }
                    ]
                },
                "notes": "This example shows combined search functionality"
            }
        }


class ToolMetadata(BaseModel):
    """Comprehensive metadata for a single tool."""
    
    name: str = Field(..., description="Tool name")
    display_name: str = Field(..., description="Human-readable tool name")
    category: ToolCategory = Field(..., description="Tool category")
    description: str = Field(..., description="Detailed tool description")
    purpose: str = Field(..., description="Primary purpose of the tool")
    
    # Parameter and response schemas
    parameters: Dict[str, ParameterSchema] = Field(..., description="Parameter schemas")
    response_schema: ResponseSchema = Field(..., description="Response schema")
    
    # Usage guidance
    use_cases: List[UseCaseScenario] = Field(..., description="Use case scenarios")
    mbti_integration: List[MBTIIntegrationGuidance] = Field(..., description="MBTI integration guidance")
    examples: List[ToolExample] = Field(..., description="Usage examples")
    
    # Technical details
    endpoint: str = Field(..., description="API endpoint")
    http_method: str = Field(..., description="HTTP method")
    authentication_required: bool = Field(default=True, description="Whether authentication is required")
    rate_limit: Optional[str] = Field(None, description="Rate limiting information")
    
    # Performance and reliability
    average_response_time_ms: Optional[float] = Field(None, description="Average response time")
    success_rate_percentage: Optional[float] = Field(None, description="Success rate percentage")
    
    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "name": "search_restaurants_by_district",
                "display_name": "Search Restaurants by District",
                "category": "search",
                "description": "Search for restaurants in specific Hong Kong districts",
                "purpose": "Find restaurants located in one or more specified districts",
                "parameters": {
                    "districts": {
                        "type": "array",
                        "description": "List of Hong Kong districts to search",
                        "required": True,
                        "min_items": 1,
                        "example": ["Central district", "Admiralty"]
                    }
                },
                "response_schema": {
                    "type": "object",
                    "description": "Restaurant search results"
                },
                "endpoint": "/api/v1/restaurants/search/district",
                "http_method": "POST",
                "authentication_required": True
            }
        }


class ToolsMetadataResponse(BaseModel):
    """Response model for tools metadata endpoint."""
    
    tools: List[ToolMetadata] = Field(..., description="List of available tools with metadata")
    total_tools: int = Field(..., description="Total number of tools available")
    categories: List[ToolCategory] = Field(..., description="Available tool categories")
    supported_mbti_types: List[MBTIPersonalityType] = Field(..., description="Supported MBTI personality types")
    version: str = Field(..., description="Metadata version")
    last_updated: str = Field(..., description="Last update timestamp")
    
    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "tools": [],
                "total_tools": 5,
                "categories": ["search", "analysis", "recommendation"],
                "supported_mbti_types": ["ENFP", "INTJ", "ESFJ"],
                "version": "1.0.0",
                "last_updated": "2025-01-03T10:30:00Z"
            }
        }


class MCPToolSchema(BaseModel):
    """Native MCP tool schema for tool discovery responses."""
    
    name: str = Field(..., description="Tool name")
    description: str = Field(..., description="Tool description")
    inputSchema: Dict[str, Any] = Field(..., description="JSON Schema for tool parameters")
    meta: Optional[Dict[str, Any]] = Field(None, description="Additional metadata for the tool", alias="_meta")
    
    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "name": "search_restaurants_by_district",
                "description": "Search for restaurants in specific Hong Kong districts",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "districts": {
                            "type": "array",
                            "description": "List of Hong Kong districts to search",
                            "minItems": 1,
                            "maxItems": 20
                        }
                    },
                    "required": ["districts"]
                },
                "meta": {
                    "category": "search",
                    "display_name": "Search Restaurants by District",
                    "endpoint": "/api/v1/restaurants/search/district",
                    "authentication_required": True
                }
            }
        }


class MCPToolDiscoveryResponse(BaseModel):
    """Native MCP tool discovery response model."""
    
    jsonrpc: str = Field(default="2.0", description="JSON-RPC version")
    id: Union[str, int] = Field(..., description="Request ID")
    result: Optional[Dict[str, Any]] = Field(None, description="Tool discovery result")
    error: Optional[Dict[str, Any]] = Field(None, description="Error information if request failed")
    
    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "jsonrpc": "2.0",
                "id": 1,
                "result": {
                    "tools": [
                        {
                            "name": "search_restaurants_by_district",
                            "description": "Search for restaurants in specific Hong Kong districts",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "districts": {
                                        "type": "array",
                                        "description": "List of Hong Kong districts to search"
                                    }
                                },
                                "required": ["districts"]
                            }
                        }
                    ],
                    "_meta": {
                        "gateway_version": "1.0.0",
                        "total_tools": 1,
                        "last_updated": "2025-01-03T10:30:00Z"
                    }
                }
            }
        }


class AggregatedServerInfo(BaseModel):
    """Information about schema aggregation from MCP servers."""
    
    servers: Dict[str, Dict[str, Any]] = Field(..., description="Server aggregation information")
    total_servers: int = Field(..., description="Total number of servers")
    healthy_servers: int = Field(..., description="Number of healthy servers")
    last_aggregation: Optional[str] = Field(None, description="Last aggregation timestamp")
    aggregation_status: str = Field(..., description="Current aggregation status")
    
    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "servers": {
                    "restaurant-search": {
                        "tool_count": 3,
                        "status": "healthy",
                        "last_updated": "2025-01-03T10:30:00Z",
                        "error": None
                    },
                    "restaurant-reasoning": {
                        "tool_count": 2,
                        "status": "healthy",
                        "last_updated": "2025-01-03T10:30:00Z",
                        "error": None
                    }
                },
                "total_servers": 2,
                "healthy_servers": 2,
                "last_aggregation": "2025-01-03T10:30:00Z",
                "aggregation_status": "completed"
            }
        }


# Update forward references
ResponseSchema.model_rebuild()