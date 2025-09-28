"""
MCP Client Manager Demo

This script demonstrates how to use the MCP Client Manager to communicate
with restaurant search and reasoning MCP servers.
"""

import asyncio
import json
from typing import List

from services.mcp_client_manager import MCPClientManager, MCPConnectionError, MCPToolCallError
from models.restaurant_models import Restaurant, Sentiment


async def demo_search_restaurants():
    """Demonstrate restaurant search functionality"""
    print("🔍 Demo: Restaurant Search via MCP Client")
    print("=" * 50)
    
    # Initialize MCP client manager
    mcp_manager = MCPClientManager()
    
    try:
        # Search for breakfast restaurants in Central district
        print("Searching for breakfast restaurants in Central district...")
        restaurants = await mcp_manager.search_restaurants(
            district="Central district",
            meal_type="breakfast"
        )
        
        print(f"✅ Found {len(restaurants)} restaurants")
        
        # Display first few restaurants
        for i, restaurant in enumerate(restaurants[:3]):
            print(f"\n{i+1}. {restaurant.name}")
            print(f"   District: {restaurant.district}")
            print(f"   Address: {restaurant.address}")
            print(f"   Sentiment: {restaurant.sentiment.likes} likes, {restaurant.sentiment.dislikes} dislikes")
            print(f"   Price Range: {restaurant.price_range}")
        
        return restaurants
        
    except MCPConnectionError as e:
        print(f"❌ Connection error: {e}")
        return []
    except MCPToolCallError as e:
        print(f"❌ Tool call error: {e}")
        return []
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return []


async def demo_analyze_restaurants(restaurants: List[Restaurant]):
    """Demonstrate restaurant analysis functionality"""
    print("\n🧠 Demo: Restaurant Analysis via MCP Client")
    print("=" * 50)
    
    if not restaurants:
        print("⚠️ No restaurants to analyze")
        return
    
    # Initialize MCP client manager
    mcp_manager = MCPClientManager()
    
    try:
        # Analyze restaurants for recommendations
        print(f"Analyzing {len(restaurants)} restaurants for recommendations...")
        result = await mcp_manager.analyze_restaurants(
            restaurants=restaurants,
            ranking_method="sentiment_likes"
        )
        
        # Display recommendation
        recommendation = result["recommendation"]
        print(f"\n🏆 Top Recommendation: {recommendation['name']}")
        print(f"   ID: {recommendation['id']}")
        if 'sentiment' in recommendation:
            sentiment = recommendation['sentiment']
            print(f"   Sentiment: {sentiment['likes']} likes, {sentiment['dislikes']} dislikes, {sentiment['neutral']} neutral")
        
        # Display top candidates
        candidates = result["candidates"]
        print(f"\n📋 Top {min(5, len(candidates))} Candidates:")
        for i, candidate in enumerate(candidates[:5]):
            print(f"{i+1}. {candidate['name']}")
            if 'sentiment' in candidate:
                sentiment = candidate['sentiment']
                print(f"   Sentiment: {sentiment['likes']} likes, {sentiment['dislikes']} dislikes")
        
        # Display analysis summary
        if 'analysis_summary' in result:
            summary = result['analysis_summary']
            print(f"\n📊 Analysis Summary:")
            for key, value in summary.items():
                print(f"   {key}: {value}")
        
        return result
        
    except MCPConnectionError as e:
        print(f"❌ Connection error: {e}")
        return None
    except MCPToolCallError as e:
        print(f"❌ Tool call error: {e}")
        return None
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return None


async def demo_health_check():
    """Demonstrate health check functionality"""
    print("\n🏥 Demo: MCP Server Health Check")
    print("=" * 50)
    
    # Initialize MCP client manager
    mcp_manager = MCPClientManager()
    
    try:
        # Perform health check
        print("Checking health of MCP servers...")
        health_status = await mcp_manager.health_check()
        
        # Display search MCP status
        search_status = health_status["search_mcp"]
        print(f"\n🔍 Search MCP Server:")
        print(f"   Status: {search_status['status']}")
        if search_status['status'] == 'healthy':
            print(f"   Available Tools: {search_status.get('tools_count', 'Unknown')}")
        else:
            print(f"   Error: {search_status.get('error', 'Unknown error')}")
        
        # Display reasoning MCP status
        reasoning_status = health_status["reasoning_mcp"]
        print(f"\n🧠 Reasoning MCP Server:")
        print(f"   Status: {reasoning_status['status']}")
        if reasoning_status['status'] == 'healthy':
            print(f"   Available Tools: {reasoning_status.get('tools_count', 'Unknown')}")
        else:
            print(f"   Error: {reasoning_status.get('error', 'Unknown error')}")
        
        return health_status
        
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return None


async def demo_connection_stats():
    """Demonstrate connection statistics"""
    print("\n📊 Demo: Connection Statistics")
    print("=" * 50)
    
    # Initialize MCP client manager
    mcp_manager = MCPClientManager()
    
    # Get connection statistics
    stats = mcp_manager.get_connection_stats()
    
    # Display search MCP stats
    search_stats = stats["search_mcp"]
    print(f"\n🔍 Search MCP Statistics:")
    print(f"   Total Calls: {search_stats['total_calls']}")
    print(f"   Successful Calls: {search_stats['successful_calls']}")
    print(f"   Failed Calls: {search_stats['failed_calls']}")
    print(f"   Success Rate: {search_stats['success_rate']:.2%}")
    print(f"   Average Response Time: {search_stats['average_response_time']:.2f}s")
    
    # Display reasoning MCP stats
    reasoning_stats = stats["reasoning_mcp"]
    print(f"\n🧠 Reasoning MCP Statistics:")
    print(f"   Total Calls: {reasoning_stats['total_calls']}")
    print(f"   Successful Calls: {reasoning_stats['successful_calls']}")
    print(f"   Failed Calls: {reasoning_stats['failed_calls']}")
    print(f"   Success Rate: {reasoning_stats['success_rate']:.2%}")
    print(f"   Average Response Time: {reasoning_stats['average_response_time']:.2f}s")
    
    return stats


async def main():
    """Main demo function"""
    print("🚀 MCP Client Manager Demo")
    print("=" * 50)
    print("This demo shows how the MCP Client Manager communicates with")
    print("restaurant search and reasoning MCP servers.\n")
    
    # Demo 1: Health Check
    await demo_health_check()
    
    # Demo 2: Search Restaurants
    restaurants = await demo_search_restaurants()
    
    # Demo 3: Analyze Restaurants (if we have results)
    if restaurants:
        await demo_analyze_restaurants(restaurants)
    
    # Demo 4: Connection Statistics
    await demo_connection_stats()
    
    print("\n✅ Demo completed!")
    print("\nNote: This demo requires the restaurant search and reasoning MCP servers")
    print("to be running and accessible. If you see connection errors, make sure")
    print("the MCP servers are properly configured and running.")


if __name__ == "__main__":
    # Run the demo
    asyncio.run(main())