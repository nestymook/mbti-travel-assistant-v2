#!/usr/bin/env python3
"""
Minimal Restaurant Reasoning MCP Server for testing.
"""

import json
import logging
from typing import List, Dict, Any

from mcp.server.fastmcp import FastMCP

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastMCP server
mcp = FastMCP("minimal-restaurant-reasoning-mcp")

@mcp.tool()
def recommend_restaurants(restaurants: List[Dict[str, Any]], ranking_method: str = "sentiment_likes") -> str:
    """
    Analyze restaurant sentiment data and provide intelligent recommendations.
    
    Args:
        restaurants: List of restaurant objects with sentiment data
        ranking_method: Ranking method ("sentiment_likes" or "combined_sentiment")
        
    Returns:
        JSON string containing recommendation results
    """
    try:
        logger.info(f"Processing recommendation request for {len(restaurants)} restaurants")
        
        # Simple recommendation logic for testing
        if not restaurants:
            return json.dumps({"error": "No restaurants provided"})
        
        # Sort by likes (simple implementation)
        sorted_restaurants = sorted(
            restaurants, 
            key=lambda r: r.get('sentiment', {}).get('likes', 0), 
            reverse=True
        )
        
        top_restaurant = sorted_restaurants[0] if sorted_restaurants else None
        
        result = {
            "success": True,
            "recommendation": {
                "id": top_restaurant.get('id', 'unknown'),
                "name": top_restaurant.get('name', 'Unknown Restaurant'),
                "likes": top_restaurant.get('sentiment', {}).get('likes', 0)
            },
            "total_restaurants": len(restaurants),
            "ranking_method": ranking_method
        }
        
        return json.dumps(result, indent=2)
        
    except Exception as e:
        logger.error(f"Error in recommend_restaurants: {e}")
        return json.dumps({"error": str(e)})

@mcp.tool()
def analyze_restaurant_sentiment(restaurants: List[Dict[str, Any]]) -> str:
    """
    Analyze sentiment data for restaurants.
    
    Args:
        restaurants: List of restaurant objects with sentiment data
        
    Returns:
        JSON string containing sentiment analysis results
    """
    try:
        logger.info(f"Analyzing sentiment for {len(restaurants)} restaurants")
        
        if not restaurants:
            return json.dumps({"error": "No restaurants provided"})
        
        total_likes = sum(r.get('sentiment', {}).get('likes', 0) for r in restaurants)
        total_dislikes = sum(r.get('sentiment', {}).get('dislikes', 0) for r in restaurants)
        
        result = {
            "success": True,
            "analysis": {
                "total_restaurants": len(restaurants),
                "total_likes": total_likes,
                "total_dislikes": total_dislikes,
                "average_likes": total_likes / len(restaurants) if restaurants else 0
            }
        }
        
        return json.dumps(result, indent=2)
        
    except Exception as e:
        logger.error(f"Error in analyze_restaurant_sentiment: {e}")
        return json.dumps({"error": str(e)})

if __name__ == "__main__":
    logger.info("Starting Minimal Restaurant Reasoning MCP Server")
    try:
        mcp.run()
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        raise