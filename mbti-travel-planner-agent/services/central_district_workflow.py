"""
Central District Search Workflow for MBTI Travel Planner Agent

This module implements a complete workflow for searching restaurants in Hong Kong's
Central district, including search, analysis, recommendation, and user-friendly formatting.

The workflow follows the complete pipeline:
1. Search → Find restaurants in Central district
2. Analyze → Process restaurant data and sentiment
3. Recommend → Generate intelligent recommendations
4. Format → Present results in user-friendly format

Requirements covered: 3.1, 3.2, 3.3, 7.1, 7.2, 7.3, 7.4
"""

import json
import logging
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

from .gateway_http_client import GatewayHTTPClient, GatewayError, create_gateway_client
from .error_handler import ErrorHandler, ErrorContext, ErrorSeverity

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


class CentralDistrictWorkflow:
    """
    Complete workflow for Central district restaurant search and recommendations.
    
    This class implements the full pipeline from search to formatted user response,
    handling all edge cases and providing comprehensive error handling.
    """
    
    CENTRAL_DISTRICT_NAMES = [
        "Central district",
        "Central",
        "Central District"
    ]
    
    def __init__(self, environment: str = None, auth_token: str = None):
        """
        Initialize the Central district workflow.
        
        Args:
            environment: Target environment (development, staging, production)
            auth_token: JWT authentication token (optional)
        """
        self.client = create_gateway_client(
            environment=environment,
            auth_token=auth_token
        )
        self.error_handler = ErrorHandler("central_district_workflow")
        
        logger.info(f"Central District Workflow initialized for {self.client.environment.value} environment")
    
    def set_auth_token(self, token: str) -> None:
        """Set the JWT authentication token."""
        self.client.set_auth_token(token)
    
    async def execute_complete_workflow(self, 
                                      meal_types: Optional[List[str]] = None,
                                      include_recommendations: bool = True,
                                      max_results: int = 20) -> WorkflowResult:
        """
        Execute the complete Central district search workflow.
        
        This method implements the full pipeline:
        1. Search for restaurants in Central district
        2. Optionally filter by meal types
        3. Analyze sentiment data
        4. Generate recommendations
        5. Format user-friendly response
        
        Args:
            meal_types: Optional meal type filters (breakfast, lunch, dinner)
            include_recommendations: Whether to generate recommendations
            max_results: Maximum number of results to process
            
        Returns:
            WorkflowResult with complete pipeline results
        """
        start_time = datetime.now()
        
        try:
            logger.info(f"Starting Central district workflow with meal_types={meal_types}")
            
            # Step 1: Search for restaurants in Central district
            search_result = await self._search_central_restaurants(meal_types)
            
            if not search_result["success"]:
                return WorkflowResult(
                    success=False,
                    restaurants_found=0,
                    error_message=search_result.get("error_message", "Search failed"),
                    execution_time=(datetime.now() - start_time).total_seconds()
                )
            
            restaurants = search_result.get("restaurants", [])
            
            # Handle no results case
            if not restaurants:
                formatted_response = self._format_no_results_response(meal_types)
                return WorkflowResult(
                    success=True,
                    restaurants_found=0,
                    formatted_response=formatted_response,
                    execution_time=(datetime.now() - start_time).total_seconds()
                )
            
            # Limit results if needed
            if len(restaurants) > max_results:
                restaurants = restaurants[:max_results]
                partial_results = True
                logger.info(f"Limited results to {max_results} restaurants")
            else:
                partial_results = False
            
            # Step 2: Generate recommendations if requested
            recommendations = None
            if include_recommendations and restaurants:
                recommendations = await self._generate_recommendations(restaurants)
            
            # Step 3: Format user-friendly response
            formatted_response = self._format_complete_response(
                restaurants=restaurants,
                recommendations=recommendations,
                meal_types=meal_types,
                partial_results=partial_results,
                search_metadata=search_result.get("metadata", {})
            )
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            logger.info(f"Central district workflow completed successfully in {execution_time:.2f}s")
            logger.info(f"Found {len(restaurants)} restaurants, recommendations: {bool(recommendations)}")
            
            return WorkflowResult(
                success=True,
                restaurants_found=len(restaurants),
                recommendations=recommendations,
                formatted_response=formatted_response,
                partial_results=partial_results,
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"Central district workflow failed after {execution_time:.2f}s: {e}")
            
            # Log error with context
            self.error_handler.log_error(
                error=e,
                context=ErrorContext(
                    operation="execute_complete_workflow",
                    environment=self.client.environment.value,
                    additional_data={
                        "meal_types": meal_types,
                        "include_recommendations": include_recommendations,
                        "max_results": max_results,
                        "execution_time": execution_time
                    }
                ),
                severity=ErrorSeverity.HIGH
            )
            
            # Create fallback response
            fallback_response = self._format_error_response(e, meal_types)
            
            return WorkflowResult(
                success=False,
                restaurants_found=0,
                error_message=str(e),
                formatted_response=fallback_response,
                execution_time=execution_time
            )
    
    async def _search_central_restaurants(self, meal_types: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Search for restaurants in Central district with optional meal type filtering.
        
        Args:
            meal_types: Optional meal type filters
            
        Returns:
            Search results dictionary
        """
        try:
            if meal_types:
                # Use combined search with both district and meal type filters
                logger.info("Performing combined search for Central district with meal type filters")
                result = await self.client.search_restaurants_combined(
                    districts=self.CENTRAL_DISTRICT_NAMES,
                    meal_types=meal_types
                )
            else:
                # Use district-only search
                logger.info("Performing district search for Central district")
                result = await self.client.search_restaurants_by_district(
                    districts=self.CENTRAL_DISTRICT_NAMES
                )
            
            # Validate result structure
            if not isinstance(result, dict):
                raise ValueError("Invalid search result format")
            
            if not result.get("success", True):
                error_info = result.get("error", {})
                raise GatewayError(f"Search failed: {error_info.get('message', 'Unknown error')}")
            
            restaurants = result.get("restaurants", [])
            metadata = result.get("metadata", {})
            
            logger.info(f"Search completed: found {len(restaurants)} restaurants")
            
            return {
                "success": True,
                "restaurants": restaurants,
                "metadata": metadata
            }
            
        except Exception as e:
            logger.error(f"Error searching Central district restaurants: {e}")
            return {
                "success": False,
                "error_message": str(e),
                "restaurants": [],
                "metadata": {}
            }
    
    async def _generate_recommendations(self, restaurants: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Generate intelligent recommendations from restaurant data.
        
        Args:
            restaurants: List of restaurant objects with sentiment data
            
        Returns:
            Recommendations dictionary or None if failed
        """
        try:
            logger.info(f"Generating recommendations for {len(restaurants)} restaurants")
            
            # Validate restaurant data has sentiment information
            valid_restaurants = []
            for restaurant in restaurants:
                if (isinstance(restaurant, dict) and 
                    "sentiment" in restaurant and 
                    isinstance(restaurant["sentiment"], dict)):
                    valid_restaurants.append(restaurant)
            
            if not valid_restaurants:
                logger.warning("No restaurants with valid sentiment data for recommendations")
                return None
            
            # Generate recommendations using sentiment_likes method
            result = await self.client.recommend_restaurants(
                restaurants=valid_restaurants,
                ranking_method="sentiment_likes"
            )
            
            if not result.get("success", True):
                logger.warning("Recommendation generation failed")
                return None
            
            logger.info("Recommendations generated successfully")
            return result
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return None
    
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


# Convenience function for easy workflow execution
async def search_central_district_restaurants(meal_types: Optional[List[str]] = None,
                                            include_recommendations: bool = True,
                                            environment: str = None,
                                            auth_token: str = None) -> WorkflowResult:
    """
    Convenience function to execute the Central district search workflow.
    
    Args:
        meal_types: Optional meal type filters (breakfast, lunch, dinner)
        include_recommendations: Whether to generate recommendations
        environment: Target environment (development, staging, production)
        auth_token: JWT authentication token (optional)
        
    Returns:
        WorkflowResult with complete pipeline results
    """
    workflow = CentralDistrictWorkflow(environment=environment, auth_token=auth_token)
    return await workflow.execute_complete_workflow(
        meal_types=meal_types,
        include_recommendations=include_recommendations
    )


# Export main classes and functions
__all__ = [
    'CentralDistrictWorkflow',
    'WorkflowResult',
    'search_central_district_restaurants'
]