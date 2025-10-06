"""
Restaurant Reasoning Tool Demo

This script demonstrates how to use the RestaurantReasoningTool with AgentCore integration
to get MBTI-based restaurant recommendations and sentiment analysis.
"""

import asyncio
import json
import logging
from typing import Dict, Any, List

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import the required classes
from services.restaurant_reasoning_tool import (
    RestaurantReasoningTool,
    create_restaurant_reasoning_tools
)
from services.agentcore_runtime_client import AgentCoreRuntimeClient
from services.authentication_manager import AuthenticationManager
from config.agentcore_environment_config import load_agentcore_environment_config


def get_sample_restaurants() -> List[Dict[str, Any]]:
    """Get sample restaurant data for demonstration."""
    return [
        {
            "id": "rest_001",
            "name": "Central Bistro",
            "cuisine": "French",
            "district": "Central district",
            "sentiment": {
                "likes": 180,
                "dislikes": 25,
                "neutral": 35
            },
            "price_range": "$$$",
            "address": "123 Central Street, Central",
            "description": "Elegant French bistro with harbor views",
            "operating_hours": {
                "monday": "11:00-22:00",
                "tuesday": "11:00-22:00",
                "wednesday": "11:00-22:00",
                "thursday": "11:00-22:00",
                "friday": "11:00-23:00",
                "saturday": "10:00-23:00",
                "sunday": "10:00-22:00"
            }
        },
        {
            "id": "rest_002",
            "name": "Admiralty Dim Sum",
            "cuisine": "Chinese",
            "district": "Admiralty",
            "sentiment": {
                "likes": 220,
                "dislikes": 18,
                "neutral": 42
            },
            "price_range": "$$",
            "address": "456 Admiralty Road, Admiralty",
            "description": "Traditional dim sum with modern presentation",
            "operating_hours": {
                "monday": "07:00-15:00",
                "tuesday": "07:00-15:00",
                "wednesday": "07:00-15:00",
                "thursday": "07:00-15:00",
                "friday": "07:00-15:00",
                "saturday": "07:00-16:00",
                "sunday": "07:00-16:00"
            }
        },
        {
            "id": "rest_003",
            "name": "Causeway Bay Ramen",
            "cuisine": "Japanese",
            "district": "Causeway Bay",
            "sentiment": {
                "likes": 150,
                "dislikes": 30,
                "neutral": 20
            },
            "price_range": "$$",
            "address": "789 Causeway Street, Causeway Bay",
            "description": "Authentic ramen shop with rich tonkotsu broth",
            "operating_hours": {
                "monday": "18:00-23:00",
                "tuesday": "18:00-23:00",
                "wednesday": "18:00-23:00",
                "thursday": "18:00-23:00",
                "friday": "18:00-24:00",
                "saturday": "18:00-24:00",
                "sunday": "18:00-23:00"
            }
        }
    ]


def get_sample_preferences() -> Dict[str, Any]:
    """Get sample user preferences for demonstration."""
    return {
        "cuisine_preferences": ["French", "Chinese", "Japanese"],
        "price_range": "$$-$$$",
        "dietary_restrictions": [],
        "atmosphere": "social",
        "group_size": 4,
        "special_occasions": ["business_dinner", "date_night"],
        "preferred_districts": ["Central district", "Admiralty"]
    }


async def demo_basic_sentiment_analysis():
    """Demonstrate basic restaurant sentiment analysis."""
    print("\n" + "="*60)
    print("DEMO: Basic Restaurant Sentiment Analysis")
    print("="*60)
    
    try:
        # Load configuration
        config = load_agentcore_environment_config()
        print(f"Loaded configuration for environment: {config.environment}")
        
        # Create authentication manager
        auth_manager = AuthenticationManager(config.cognito)
        
        # Create runtime client
        runtime_client = AgentCoreRuntimeClient(
            cognito_config=config.cognito,
            region=config.agentcore.region
        )
        
        # Create reasoning tool
        reasoning_tool = RestaurantReasoningTool(
            runtime_client=runtime_client,
            reasoning_agent_arn=config.agentcore.restaurant_reasoning_agent_arn,
            auth_manager=auth_manager
        )
        
        # Get sample data
        restaurants = get_sample_restaurants()
        
        print(f"\nAnalyzing sentiment for {len(restaurants)} restaurants...")
        print("Restaurants:")
        for restaurant in restaurants:
            sentiment = restaurant["sentiment"]
            total_reviews = sum(sentiment.values())
            print(f"  - {restaurant['name']}: {sentiment['likes']} likes, {sentiment['dislikes']} dislikes, {sentiment['neutral']} neutral ({total_reviews} total)")
        
        # Perform sentiment analysis
        result = await reasoning_tool.analyze_restaurant_sentiment(
            restaurants=restaurants,
            ranking_method="sentiment_likes"
        )
        
        if result.success:
            print(f"\n✅ Analysis completed successfully!")
            print(f"Confidence Score: {result.confidence_score:.2f}")
            print(f"Execution Time: {result.execution_time_ms}ms")
            print(f"\nReasoning: {result.reasoning}")
            
            print(f"\nTop Recommendations:")
            for i, rec in enumerate(result.recommendations[:3], 1):
                print(f"  {i}. {rec.get('name', 'Unknown')} (Score: {rec.get('score', 0):.2f})")
                if 'reasoning' in rec:
                    print(f"     Reason: {rec['reasoning']}")
        else:
            print(f"❌ Analysis failed: {result.error_message}")
            
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        logger.exception("Demo error")


async def demo_mbti_recommendations():
    """Demonstrate MBTI-based restaurant recommendations."""
    print("\n" + "="*60)
    print("DEMO: MBTI-Based Restaurant Recommendations")
    print("="*60)
    
    try:
        # Load configuration
        config = load_agentcore_environment_config()
        
        # Create authentication manager
        auth_manager = AuthenticationManager(config.cognito)
        
        # Create runtime client
        runtime_client = AgentCoreRuntimeClient(
            cognito_config=config.cognito,
            region=config.agentcore.region
        )
        
        # Create reasoning tool
        reasoning_tool = RestaurantReasoningTool(
            runtime_client=runtime_client,
            reasoning_agent_arn=config.agentcore.restaurant_reasoning_agent_arn,
            auth_manager=auth_manager
        )
        
        # Get sample data
        restaurants = get_sample_restaurants()
        preferences = get_sample_preferences()
        mbti_type = "ENFP"
        
        print(f"\nGenerating recommendations for MBTI type: {mbti_type}")
        print(f"User preferences: {json.dumps(preferences, indent=2)}")
        
        # Get MBTI-based recommendations
        result = await reasoning_tool.get_recommendations(
            restaurants=restaurants,
            mbti_type=mbti_type,
            preferences=preferences,
            ranking_method="combined_sentiment"
        )
        
        if result.success:
            print(f"\n✅ Recommendations generated successfully!")
            print(f"Confidence Score: {result.confidence_score:.2f}")
            print(f"Execution Time: {result.execution_time_ms}ms")
            
            print(f"\nMBTI Analysis:")
            if result.mbti_analysis:
                for key, value in result.mbti_analysis.items():
                    print(f"  {key}: {value}")
            
            print(f"\nPersonalized Recommendations:")
            for i, rec in enumerate(result.recommendations, 1):
                print(f"\n  {i}. {rec.get('name', 'Unknown')} (Score: {rec.get('score', 0):.2f})")
                if 'reasoning' in rec:
                    print(f"     MBTI Match: {rec['reasoning']}")
                if 'mbti_match' in rec:
                    match_data = rec['mbti_match']
                    print(f"     Personality Alignment: {match_data}")
            
            print(f"\nOverall Reasoning:")
            print(f"  {result.reasoning}")
            
        else:
            print(f"❌ Recommendations failed: {result.error_message}")
            
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        logger.exception("Demo error")


def demo_backward_compatibility():
    """Demonstrate backward compatibility with existing tool interface."""
    print("\n" + "="*60)
    print("DEMO: Backward Compatibility Interface")
    print("="*60)
    
    try:
        # Load configuration
        config = load_agentcore_environment_config()
        
        # Create authentication manager
        auth_manager = AuthenticationManager(config.cognito)
        
        # Create runtime client
        runtime_client = AgentCoreRuntimeClient(
            cognito_config=config.cognito,
            region=config.agentcore.region
        )
        
        # Create reasoning tool
        reasoning_tool = RestaurantReasoningTool(
            runtime_client=runtime_client,
            reasoning_agent_arn=config.agentcore.restaurant_reasoning_agent_arn,
            auth_manager=auth_manager
        )
        
        # Get sample data
        restaurants = get_sample_restaurants()
        
        print(f"\nUsing backward compatible interface...")
        print("This interface returns JSON strings for compatibility with existing code.")
        
        # Test backward compatible method
        response_json = reasoning_tool.recommend_restaurants_tool(
            restaurants=restaurants,
            ranking_method="sentiment_likes"
        )
        
        # Parse and display response
        response_data = json.loads(response_json)
        
        if response_data.get("success", False):
            print(f"\n✅ Backward compatible call successful!")
            print(f"Response format: JSON string")
            print(f"Success: {response_data['success']}")
            print(f"Recommendations count: {len(response_data.get('recommendations', []))}")
            print(f"Execution time: {response_data.get('execution_time_ms', 0)}ms")
            
            print(f"\nSample response structure:")
            print(json.dumps(response_data, indent=2)[:500] + "...")
            
        else:
            print(f"❌ Backward compatible call failed")
            print(f"Error: {response_data.get('error', {})}")
            
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        logger.exception("Demo error")


def demo_tool_creation():
    """Demonstrate creating Strands Agent tools."""
    print("\n" + "="*60)
    print("DEMO: Strands Agent Tool Creation")
    print("="*60)
    
    try:
        # Load configuration
        config = load_agentcore_environment_config()
        
        # Create authentication manager
        auth_manager = AuthenticationManager(config.cognito)
        
        # Create runtime client
        runtime_client = AgentCoreRuntimeClient(
            cognito_config=config.cognito,
            region=config.agentcore.region
        )
        
        print(f"Creating restaurant reasoning tools...")
        
        # Create tools using the factory function
        tools = create_restaurant_reasoning_tools(
            runtime_client=runtime_client,
            reasoning_agent_arn=config.agentcore.restaurant_reasoning_agent_arn,
            auth_manager=auth_manager
        )
        
        print(f"\n✅ Created {len(tools)} tools successfully!")
        
        print(f"\nAvailable tools:")
        for i, tool in enumerate(tools, 1):
            print(f"  {i}. {tool.name}")
            print(f"     Description: {tool.description[:100]}...")
            
        # Demonstrate tool usage
        if tools:
            print(f"\nDemonstrating tool usage...")
            recommend_tool = next((t for t in tools if t.name == "recommend_restaurants"), None)
            
            if recommend_tool:
                restaurants = get_sample_restaurants()
                
                print(f"Calling {recommend_tool.name} with {len(restaurants)} restaurants...")
                
                # Note: In a real Strands Agent, this would be called automatically
                # Here we're just demonstrating the interface
                result_json = recommend_tool(restaurants, "sentiment_likes")
                result_data = json.loads(result_json)
                
                if result_data.get("success", False):
                    print(f"✅ Tool call successful!")
                    print(f"Recommendations: {len(result_data.get('recommendations', []))}")
                else:
                    print(f"❌ Tool call failed: {result_data.get('error', {})}")
            
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        logger.exception("Demo error")


def demo_performance_metrics():
    """Demonstrate performance metrics tracking."""
    print("\n" + "="*60)
    print("DEMO: Performance Metrics Tracking")
    print("="*60)
    
    try:
        # Load configuration
        config = load_agentcore_environment_config()
        
        # Create authentication manager
        auth_manager = AuthenticationManager(config.cognito)
        
        # Create runtime client
        runtime_client = AgentCoreRuntimeClient(
            cognito_config=config.cognito,
            region=config.agentcore.region
        )
        
        # Create reasoning tool
        reasoning_tool = RestaurantReasoningTool(
            runtime_client=runtime_client,
            reasoning_agent_arn=config.agentcore.restaurant_reasoning_agent_arn,
            auth_manager=auth_manager
        )
        
        print(f"Initial metrics:")
        initial_metrics = reasoning_tool.get_performance_metrics()
        print(json.dumps(initial_metrics, indent=2))
        
        # Simulate some calls (these would normally be real calls)
        print(f"\nSimulating performance tracking...")
        reasoning_tool.call_count = 10
        reasoning_tool.error_count = 2
        reasoning_tool.total_response_time = 15000  # 15 seconds total
        
        print(f"Updated metrics after simulated calls:")
        updated_metrics = reasoning_tool.get_performance_metrics()
        print(json.dumps(updated_metrics, indent=2))
        
        print(f"\nMetrics explanation:")
        print(f"  - Total calls: {updated_metrics['total_calls']}")
        print(f"  - Total errors: {updated_metrics['total_errors']}")
        print(f"  - Error rate: {updated_metrics['error_rate']:.1%}")
        print(f"  - Average response time: {updated_metrics['average_response_time_ms']:.0f}ms")
        print(f"  - Agent ARN: {updated_metrics['agent_arn']}")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        logger.exception("Demo error")


async def main():
    """Run all demonstrations."""
    print("Restaurant Reasoning Tool Demo")
    print("=" * 60)
    print("This demo shows how to use the RestaurantReasoningTool with AgentCore integration.")
    print("Note: This demo uses mock responses since it requires actual AgentCore agents.")
    
    # Run demonstrations
    await demo_basic_sentiment_analysis()
    await demo_mbti_recommendations()
    demo_backward_compatibility()
    demo_tool_creation()
    demo_performance_metrics()
    
    print("\n" + "="*60)
    print("Demo completed!")
    print("="*60)
    print("\nKey features demonstrated:")
    print("  ✅ Basic restaurant sentiment analysis")
    print("  ✅ MBTI-based personalized recommendations")
    print("  ✅ Backward compatibility with existing interfaces")
    print("  ✅ Strands Agent tool creation")
    print("  ✅ Performance metrics tracking")
    print("\nThe RestaurantReasoningTool is ready for integration with AgentCore!")


if __name__ == "__main__":
    # Run the demo
    asyncio.run(main())