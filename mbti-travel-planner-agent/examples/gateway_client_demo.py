"""
Gateway HTTP Client Demonstration

This script demonstrates how to use the Gateway HTTP Client to communicate
with the AgentCore Gateway MCP Tools service.
"""

import asyncio
import json
import logging
from typing import Dict, Any

from services.gateway_http_client import (
    GatewayHTTPClient,
    Environment,
    create_gateway_client
)
from config.gateway_config import get_gateway_config

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


async def demo_basic_usage():
    """Demonstrate basic HTTP client usage."""
    print("\n🔧 Basic HTTP Client Usage")
    print("=" * 50)
    
    # Create client for development environment
    client = GatewayHTTPClient(environment=Environment.DEVELOPMENT)
    
    print(f"Environment: {client.environment.value}")
    print(f"Base URL: {client.endpoints.base_url}")
    print(f"Timeout: {client.endpoints.timeout}s")
    
    # Set authentication token (if available)
    auth_token = "your_jwt_token_here"  # Replace with actual token
    client.set_auth_token(auth_token)
    
    print("✅ Client configured successfully")


async def demo_search_operations():
    """Demonstrate restaurant search operations."""
    print("\n🔍 Restaurant Search Operations")
    print("=" * 50)
    
    client = create_gateway_client(environment="development")
    
    # 1. Search by district
    print("\n1. Searching restaurants by district...")
    districts = ["Central district", "Admiralty"]
    result = await client.search_restaurants_by_district(districts)
    
    if result["success"]:
        print(f"✅ Found restaurants in {len(districts)} districts")
        print(f"   Total results: {result.get('data', {}).get('total_count', 0)}")
    else:
        print(f"❌ Search failed: {result['error']['message']}")
    
    # 2. Search by meal type
    print("\n2. Searching restaurants by meal type...")
    meal_types = ["lunch", "dinner"]
    result = await client.search_restaurants_by_meal_type(meal_types)
    
    if result["success"]:
        print(f"✅ Found restaurants for {len(meal_types)} meal types")
    else:
        print(f"❌ Search failed: {result['error']['message']}")
    
    # 3. Combined search
    print("\n3. Combined search (district + meal type)...")
    result = await client.search_restaurants_combined(
        districts=["Central district"],
        meal_types=["lunch"]
    )
    
    if result["success"]:
        print("✅ Combined search completed")
    else:
        print(f"❌ Combined search failed: {result['error']['message']}")


async def demo_recommendation_operations():
    """Demonstrate restaurant recommendation operations."""
    print("\n🎯 Restaurant Recommendation Operations")
    print("=" * 50)
    
    client = create_gateway_client(environment="development")
    
    # Sample restaurant data
    sample_restaurants = [
        {
            "id": "rest_001",
            "name": "Great Cantonese Restaurant",
            "district": "Central district",
            "sentiment": {"likes": 85, "dislikes": 10, "neutral": 5},
            "cuisine_type": "Cantonese",
            "price_range": "$$"
        },
        {
            "id": "rest_002", 
            "name": "Popular Dim Sum Place",
            "district": "Central district",
            "sentiment": {"likes": 92, "dislikes": 5, "neutral": 3},
            "cuisine_type": "Dim Sum",
            "price_range": "$"
        },
        {
            "id": "rest_003",
            "name": "Average Restaurant",
            "district": "Admiralty",
            "sentiment": {"likes": 60, "dislikes": 25, "neutral": 15},
            "cuisine_type": "International",
            "price_range": "$$$"
        }
    ]
    
    # 1. Get recommendations
    print("\n1. Getting restaurant recommendations...")
    result = await client.recommend_restaurants(
        restaurants=sample_restaurants,
        ranking_method="sentiment_likes"
    )
    
    if result["success"]:
        print("✅ Recommendations generated")
        recommendation = result.get("data", {}).get("recommendation", {})
        if recommendation:
            print(f"   Top recommendation: {recommendation.get('name', 'N/A')}")
            print(f"   Recommendation score: {recommendation.get('recommendation_score', 'N/A')}")
    else:
        print(f"❌ Recommendation failed: {result['error']['message']}")
    
    # 2. Analyze sentiment
    print("\n2. Analyzing restaurant sentiment...")
    result = await client.analyze_restaurant_sentiment(sample_restaurants)
    
    if result["success"]:
        print("✅ Sentiment analysis completed")
        analysis = result.get("data", {}).get("sentiment_analysis", {})
        if analysis:
            print(f"   Average likes: {analysis.get('average_likes', 'N/A')}")
            print(f"   Average dislikes: {analysis.get('average_dislikes', 'N/A')}")
    else:
        print(f"❌ Sentiment analysis failed: {result['error']['message']}")


async def demo_error_handling():
    """Demonstrate error handling capabilities."""
    print("\n⚠️  Error Handling Demonstration")
    print("=" * 50)
    
    client = create_gateway_client(environment="development")
    
    # 1. Validation errors
    print("\n1. Testing validation errors...")
    
    # Empty districts
    result = await client.search_restaurants_by_district([])
    print(f"   Empty districts: {result['error']['type']} - {result['error']['message'][:50]}...")
    
    # Invalid meal types
    result = await client.search_restaurants_by_meal_type(["brunch", "snack"])
    print(f"   Invalid meal types: {result['error']['type']} - {result['error']['message'][:50]}...")
    
    # 2. Connection errors
    print("\n2. Testing connection errors...")
    
    # Invalid URL
    invalid_client = GatewayHTTPClient(base_url="http://invalid-gateway.example.com")
    result = await invalid_client.search_restaurants_by_district(["Central district"])
    print(f"   Invalid URL: {result['error']['type']} - {result['error']['message'][:50]}...")
    
    print("\n✅ Error handling working correctly")


async def demo_environment_configurations():
    """Demonstrate different environment configurations."""
    print("\n🌍 Environment Configurations")
    print("=" * 50)
    
    environments = ["development", "staging", "production"]
    
    for env_name in environments:
        print(f"\n{env_name.upper()} Environment:")
        
        # Get configuration
        config = get_gateway_config(env_name)
        print(f"  Base URL: {config.base_url}")
        print(f"  Timeout: {config.timeout}s")
        print(f"  Max Retries: {config.max_retries}")
        print(f"  Auth Required: {config.auth_required}")
        print(f"  Description: {config.description}")
        
        # Create client
        client = create_gateway_client(environment=env_name)
        print(f"  Client Environment: {client.environment.value}")
        print(f"  Client Base URL: {client.endpoints.base_url}")


async def demo_health_monitoring():
    """Demonstrate health check and metrics."""
    print("\n💊 Health Monitoring")
    print("=" * 50)
    
    client = create_gateway_client(environment="development")
    
    # Health check
    print("\n1. Health Check...")
    result = await client.health_check()
    
    if result.get("success", True):
        print("✅ Gateway is healthy")
        if "status" in result:
            print(f"   Status: {result['status']}")
            print(f"   Timestamp: {result.get('timestamp', 'N/A')}")
    else:
        print(f"❌ Gateway health check failed: {result['error']['message']}")
    
    # Metrics
    print("\n2. Service Metrics...")
    result = await client.get_metrics()
    
    if result.get("success", True):
        print("✅ Metrics retrieved")
        if "requests_total" in result:
            print(f"   Total Requests: {result.get('requests_total', 'N/A')}")
            print(f"   Average Response Time: {result.get('average_response_time_ms', 'N/A')}ms")
    else:
        print(f"❌ Metrics retrieval failed: {result['error']['message']}")


async def main():
    """Run all demonstrations."""
    print("🚀 Gateway HTTP Client Demonstration")
    print("=" * 60)
    print("This demo shows how to use the Gateway HTTP Client to communicate")
    print("with the AgentCore Gateway MCP Tools service.")
    print("=" * 60)
    
    demos = [
        demo_basic_usage,
        demo_environment_configurations,
        demo_search_operations,
        demo_recommendation_operations,
        demo_error_handling,
        demo_health_monitoring
    ]
    
    for demo in demos:
        try:
            await demo()
        except Exception as e:
            print(f"❌ Demo {demo.__name__} failed: {e}")
    
    print("\n" + "=" * 60)
    print("🎉 Demonstration completed!")
    print("\nNote: Some operations may fail if the gateway service is not running.")
    print("This is expected behavior and demonstrates the error handling capabilities.")


if __name__ == "__main__":
    asyncio.run(main())