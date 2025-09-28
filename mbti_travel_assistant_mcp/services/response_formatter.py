"""
Response Formatter Service

This module provides response formatting functionality for converting
internal agent responses into structured JSON format optimized for
frontend web application consumption.

Implements requirements 4.1, 4.6, 4.7:
- Structured response formatting for frontend consumption
- Metadata generation with search criteria and timestamps  
- Error response formatting with appropriate error codes
"""

import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum

from models.request_models import RecommendationRequest
from models.restaurant_models import Restaurant
from services.response_validator import ResponseValidator

logger = logging.getLogger(__name__)


class ErrorCode(Enum):
    """Standard error codes for API responses."""
    VALIDATION_ERROR = "VALIDATION_ERROR"
    AUTHENTICATION_ERROR = "AUTHENTICATION_ERROR"
    MCP_UNAVAILABLE = "MCP_UNAVAILABLE"
    PARSING_ERROR = "PARSING_ERROR"
    TIMEOUT_ERROR = "TIMEOUT_ERROR"
    RATE_LIMIT_ERROR = "RATE_LIMIT_ERROR"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    NO_RESULTS_FOUND = "NO_RESULTS_FOUND"
    FORMATTING_ERROR = "FORMATTING_ERROR"


class ResponseFormatter:
    """
    Service for formatting agent responses into structured JSON.
    
    This service takes internal agent response data and formats it
    into the standardized JSON structure expected by frontend applications.
    
    Implements requirement 4 acceptance criteria:
    - JSON response with "recommendation" and "candidates" fields
    - Complete restaurant details with all required fields
    - Metadata with search criteria, timestamps, and processing info
    - Proper error formatting with error codes and suggested actions
    """
    
    def __init__(self):
        """Initialize the response formatter with validator."""
        self.validator = ResponseValidator()
    
    def format_response(
        self,
        response_data: Dict[str, Any],
        request: RecommendationRequest,
        start_time: datetime,
        correlation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Format agent response data into structured JSON for frontend consumption.
        
        Implements requirement 4.1: JSON response with "recommendation" and "candidates" fields
        
        Args:
            response_data: Raw response data from agent
            request: Original recommendation request
            start_time: Request start time
            correlation_id: Request correlation ID
            
        Returns:
            Formatted response dictionary with standardized structure
        """
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        logger.info(
            "Formatting response for frontend consumption",
            extra={
                "correlation_id": correlation_id,
                "processing_time_ms": processing_time,
                "has_recommendation": "recommendation" in response_data,
                "candidate_count": len(response_data.get("candidates", []))
            }
        )
        
        try:
            # Extract components from response data
            recommendation = response_data.get("recommendation")
            candidates = response_data.get("candidates", [])
            metadata = response_data.get("metadata", {})
            
            # Validate and format candidates (requirement 4.3: exactly 19 or fewer)
            formatted_candidates = self._format_candidates(candidates)
            
            # Format the response according to requirement 4
            formatted_response = {
                "recommendation": self._format_restaurant(recommendation) if recommendation else None,
                "candidates": formatted_candidates,
                "metadata": self._format_metadata(
                    metadata, request, processing_time, correlation_id
                )
            }
            
            # Add error information if present (requirement 4.7)
            if "error" in response_data:
                formatted_response["error"] = self._format_error_with_code(response_data["error"])
            
            # Validate and sanitize final response structure
            validation_result = self.validator.validate_response(formatted_response)
            
            if not validation_result.is_valid:
                logger.error(
                    f"Response validation failed: {validation_result.errors}",
                    extra={"correlation_id": correlation_id}
                )
                # Return fallback response if validation fails
                return self.validator.create_fallback_response(
                    "Response validation failed",
                    correlation_id
                )
            
            # Sanitize response to ensure size constraints
            sanitized_response = self.validator.sanitize_response(formatted_response)
            
            if validation_result.warnings:
                logger.warning(
                    f"Response validation warnings: {validation_result.warnings}",
                    extra={"correlation_id": correlation_id}
                )
            
            return sanitized_response
            
        except Exception as e:
            logger.error(
                f"Response formatting failed: {str(e)}",
                extra={"correlation_id": correlation_id},
                exc_info=True
            )
            
            # Return standardized error response
            return self._create_error_response(
                ErrorCode.FORMATTING_ERROR,
                "Failed to format response",
                ["Try again", "Contact support if issue persists"],
                request,
                processing_time,
                correlation_id
            )
    
    def _format_candidates(self, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Format and validate candidate restaurants list.
        
        Implements requirement 4.3: exactly 19 restaurant objects (or fewer if insufficient)
        
        Args:
            candidates: List of raw candidate restaurant data
            
        Returns:
            List of formatted candidate restaurants (max 19)
        """
        if not candidates:
            return []
        
        # Limit to 19 candidates as per requirement 4.3
        limited_candidates = candidates[:19]
        
        formatted_candidates = []
        for candidate in limited_candidates:
            formatted_candidate = self._format_restaurant(candidate)
            if formatted_candidate:  # Only include valid restaurants
                formatted_candidates.append(formatted_candidate)
        
        logger.debug(
            f"Formatted {len(formatted_candidates)} candidates from {len(candidates)} raw candidates"
        )
        
        return formatted_candidates

    def _format_restaurant(self, restaurant_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Format individual restaurant data with all required fields.
        
        Implements requirement 4.4: restaurant objects SHALL include id, name, address, 
        district, mealType, sentiment, priceRange, operatingHours, and locationCategory
        
        Args:
            restaurant_data: Raw restaurant data
            
        Returns:
            Formatted restaurant dictionary or None if invalid
        """
        if not restaurant_data:
            return None
        
        try:
            # Ensure all required fields are present (requirement 4.4)
            formatted_restaurant = {
                "id": str(restaurant_data.get("id", "")),
                "name": str(restaurant_data.get("name", "Unknown Restaurant")),
                "address": str(restaurant_data.get("address", "")),
                "district": str(restaurant_data.get("district", "")),
                "mealType": restaurant_data.get("meal_type", restaurant_data.get("mealType", [])),
                "sentiment": self._format_sentiment(restaurant_data.get("sentiment", {})),
                "priceRange": str(restaurant_data.get("price_range", restaurant_data.get("priceRange", "$"))),
                "operatingHours": self._format_operating_hours(
                    restaurant_data.get("operating_hours", restaurant_data.get("operatingHours", {}))
                ),
                "locationCategory": str(restaurant_data.get("location_category", restaurant_data.get("locationCategory", "")))
            }
            
            # Add optional fields if present (requirement 4.9)
            if "cuisine_type" in restaurant_data:
                formatted_restaurant["cuisineType"] = restaurant_data["cuisine_type"]
            
            if "rating" in restaurant_data:
                formatted_restaurant["rating"] = float(restaurant_data["rating"])
            
            if "image_url" in restaurant_data or "imageUrl" in restaurant_data:
                formatted_restaurant["imageUrl"] = restaurant_data.get("image_url", restaurant_data.get("imageUrl"))
            
            # Validate required fields are not empty
            if not formatted_restaurant["id"] or not formatted_restaurant["name"]:
                logger.warning(f"Restaurant missing required fields: {formatted_restaurant}")
                # Return None to filter out invalid restaurants
                return None
            
            return formatted_restaurant
            
        except Exception as e:
            logger.error(f"Failed to format restaurant data: {str(e)}", exc_info=True)
            return None
    
    def _format_operating_hours(self, hours_data: Dict[str, Any]) -> Dict[str, str]:
        """
        Format operating hours consistently for frontend display.
        
        Implements requirement 4.10: operating hours SHALL be formatted consistently 
        for frontend display (e.g., "Mon-Fri: 07:00-11:30")
        
        Args:
            hours_data: Raw operating hours data
            
        Returns:
            Formatted operating hours dictionary
        """
        if not hours_data:
            return {}
        
        formatted_hours = {}
        
        # Handle different input formats
        for day, hours in hours_data.items():
            if isinstance(hours, list) and len(hours) >= 2:
                # Format as "HH:MM-HH:MM"
                formatted_hours[day] = f"{hours[0]}-{hours[1]}"
            elif isinstance(hours, str):
                # Already formatted string
                formatted_hours[day] = hours
            else:
                # Default to closed
                formatted_hours[day] = "Closed"
        
        return formatted_hours

    def _format_sentiment(self, sentiment_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format sentiment data with validation and additional metrics.
        
        Args:
            sentiment_data: Raw sentiment data
            
        Returns:
            Formatted sentiment dictionary with calculated metrics
        """
        likes = max(0, int(sentiment_data.get("likes", 0)))
        dislikes = max(0, int(sentiment_data.get("dislikes", 0)))
        neutral = max(0, int(sentiment_data.get("neutral", 0)))
        
        total = likes + dislikes + neutral
        
        formatted_sentiment = {
            "likes": likes,
            "dislikes": dislikes,
            "neutral": neutral,
            "total": total
        }
        
        # Add calculated percentages
        if total > 0:
            formatted_sentiment["positivePercentage"] = round((likes + neutral) / total * 100, 1)
            formatted_sentiment["likesPercentage"] = round(likes / total * 100, 1)
        else:
            formatted_sentiment["positivePercentage"] = 0.0
            formatted_sentiment["likesPercentage"] = 0.0
        
        return formatted_sentiment
    
    def _format_metadata(
        self,
        metadata: Dict[str, Any],
        request: RecommendationRequest,
        processing_time: float,
        correlation_id: Optional[str]
    ) -> Dict[str, Any]:
        """
        Format response metadata with search criteria and timestamps.
        
        Implements requirement 4.5: metadata field with search_criteria, total_found, and timestamp
        
        Args:
            metadata: Raw metadata from agent
            request: Original request
            processing_time: Processing time in milliseconds
            correlation_id: Request correlation ID
            
        Returns:
            Formatted metadata dictionary
        """
        current_time = datetime.utcnow()
        
        formatted_metadata = {
            "searchCriteria": {
                "district": request.district,
                "mealTime": request.meal_time,
                "naturalLanguageQuery": getattr(request, 'natural_language_query', None)
            },
            "totalFound": int(metadata.get("total_found", 0)),
            "timestamp": current_time.isoformat() + "Z",  # ISO 8601 with UTC indicator
            "processingTimeMs": round(processing_time, 2),
            "correlationId": correlation_id,
            "mcpCalls": metadata.get("mcp_calls", []),
            "cacheHit": bool(metadata.get("cache_hit", False)),
            "agentVersion": metadata.get("agent_version", "1.0.0"),
            "responseGenerated": current_time.strftime("%Y-%m-%d %H:%M:%S UTC")
        }
        
        # Add performance metrics if available
        if "performance_metrics" in metadata:
            formatted_metadata["performanceMetrics"] = metadata["performance_metrics"]
        
        # Add search quality indicators
        if "search_quality" in metadata:
            formatted_metadata["searchQuality"] = metadata["search_quality"]
        
        return formatted_metadata
    
    def _format_error_with_code(self, error_data: Any) -> Dict[str, Any]:
        """
        Format error information with appropriate error codes.
        
        Implements requirement 4.7: error field with error_type, message, and suggested_actions
        
        Args:
            error_data: Raw error data
            
        Returns:
            Formatted error dictionary with standardized error codes
        """
        if isinstance(error_data, dict):
            error_type = error_data.get("error_type", "unknown_error")
            
            # Map to standardized error codes
            if error_type in [e.value for e in ErrorCode]:
                error_code = error_type
            else:
                error_code = ErrorCode.INTERNAL_ERROR.value
            
            return {
                "errorType": error_code,
                "errorCode": error_code,  # For backward compatibility
                "message": str(error_data.get("message", "An error occurred")),
                "suggestedActions": error_data.get("suggested_actions", ["Try again"]),
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "details": error_data.get("details", {})
            }
        else:
            return {
                "errorType": ErrorCode.INTERNAL_ERROR.value,
                "errorCode": ErrorCode.INTERNAL_ERROR.value,
                "message": str(error_data),
                "suggestedActions": ["Try again", "Contact support if issue persists"],
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "details": {}
            }

    def _create_error_response(
        self,
        error_code: ErrorCode,
        message: str,
        suggested_actions: List[str],
        request: RecommendationRequest,
        processing_time: float,
        correlation_id: Optional[str]
    ) -> Dict[str, Any]:
        """
        Create a standardized error response.
        
        Args:
            error_code: Standardized error code
            message: Error message
            suggested_actions: List of suggested actions
            request: Original request
            processing_time: Processing time in milliseconds
            correlation_id: Request correlation ID
            
        Returns:
            Standardized error response dictionary
        """
        return {
            "recommendation": None,
            "candidates": [],
            "metadata": self._format_metadata(
                {"total_found": 0}, request, processing_time, correlation_id
            ),
            "error": {
                "errorType": error_code.value,
                "errorCode": error_code.value,
                "message": message,
                "suggestedActions": suggested_actions,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "details": {}
            }
        }



    def create_no_results_response(
        self,
        request: RecommendationRequest,
        processing_time: float,
        correlation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a response when no restaurants are found.
        
        Args:
            request: Original request
            processing_time: Processing time in milliseconds
            correlation_id: Request correlation ID
            
        Returns:
            No results response dictionary
        """
        return self._create_error_response(
            ErrorCode.NO_RESULTS_FOUND,
            f"No restaurants found for {request.meal_time} in {request.district}",
            [
                "Try a different district",
                "Try a different meal time",
                "Use a broader search query"
            ],
            request,
            processing_time,
            correlation_id
        )