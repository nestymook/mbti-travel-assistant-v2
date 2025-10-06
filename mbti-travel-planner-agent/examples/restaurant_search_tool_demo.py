"""
Restaurant Search Tool Demo

This example demonstrates how to use the RestaurantSearchTool with AgentCore integration
to replace HTTP gateway calls with direct agent invocation.
"""

import asyncio
import json
import logging
from typing import List

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from services.restaurant_search_tool import RestaurantSearchTool, create_restaurant_search_tools
from services.agentcore_runtime_client import AgentCoreRuntimeClient
from services.authentication_manager import AuthenticationManager, CognitoConfig
from config.agentcore_config import load_agentcore_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def demo_restaurant_search_tool():
    """Demonstrate the RestaurantSearchTool functionality."""
    
    try:
        # Load configuration
        logger.info("Loading AgentCore configuration...")
        config = load_agentcore_config(environment='development')
        
        # Initialize authentication manager
        logger.info("Initializing authentication manager...")
        auth_manager = AuthenticationManager(config.cognito)
        
        # Initialize AgentCore Runtime client
        logger.info("Initializing AgentCore Runtime client...")
        runtime_client = AgentCoreRuntimeClient(region=config.agentcore.region)
        
        # Initialize restaurant search tool
        logger.info("Initializing restaurant search tool...")
        search_tool = RestaurantSearchTool(
            runtime_client=runtime_client,
            search_agent_arn=config.agentcore.restaurant_search_agent_arn,
            auth_manager=auth_manager
        )
        
        # Demo 1: Search restaurants by district
        logger.info("\n=== Demo 1: Search restaurants by district ===")
        districts = ["Central district", "Admiralty"]
        result = await search_tool.search_restaurants_by_district(districts)
        
        if result.success:
            logger.info(f"Found {result.total_count} restaurants in {len(districts)} districts")
            logger.info(f"Execution time: {result.execution_time_ms}ms")
            
            # Show first few restaurants
            for i, restaurant in enumerate(result.restaurants[:3]):
                logger.info(f"  {i+1}. {restaurant.get('name', 'Unknown')} - {restaurant.get('district', 'Unknown district')}")
        else:
            logger.error(f"District search failed: {result.error_message}")
        
        # Demo 2: Search restaurants by meal type
        logger.info("\n=== Demo 2: Search restaurants by meal type ===")
        meal_types = ["lunch", "dinner"]
        result = await search_tool.search_restaurants_by_meal_type(meal_types)
        
        if result.success:
            logger.info(f"Found {result.total_count} restaurants for {len(meal_types)} meal types")
            logger.info(f"Execution time: {result.execution_time_ms}ms")
        else:
            logger.error(f"Meal type search failed: {result.error_message}")
        
        # Demo 3: Combined search
        logger.info("\n=== Demo 3: Combined district and meal type search ===")
        districts = ["Central district"]
        meal_types = ["lunch"]
        result = await search_tool.search_restaurants_combined(districts, meal_types)
        
        if result.success:
            logger.info(f"Found {result.total_count} restaurants matching both criteria")
            logger.info(f"Execution time: {result.execution_time_ms}ms")
            logger.info(f"Search metadata: {json.dumps(result.search_metadata, indent=2)}")
        else:
            logger.error(f"Combined search failed: {result.error_message}")
        
        # Demo 4: Backward compatibility methods
        logger.info("\n=== Demo 4: Backward compatibility methods ===")
        
        # Test district search tool method
        result_json = search_tool.search_restaurants_by_district_tool(["Central district"])
        result_data = json.loads(result_json)
        
        if result_data.get("success"):
            logger.info(f"Backward compatible district search: {result_data['total_count']} restaurants found")
        else:
            logger.error(f"Backward compatible district search failed: {result_data.get('error', {}).get('message')}")
        
        # Test combined search tool method
        result_json = search_tool.search_restaurants_combined_tool(
            districts=["Central district"], 
            meal_types=["dinner"]
        )
        result_data = json.loads(result_json)
        
        if result_data.get("success"):
            logger.info(f"Backward compatible combined search: {result_data['total_count']} restaurants found")
        else:
            logger.error(f"Backward compatible combined search failed: {result_data.get('error', {}).get('message')}")
        
        # Demo 5: Performance metrics
        logger.info("\n=== Demo 5: Performance metrics ===")
        metrics = search_tool.get_performance_metrics()
        logger.info(f"Performance metrics: {json.dumps(metrics, indent=2)}")
        
        # Clean up
        await runtime_client.close()
        
        logger.info("\n=== Demo completed successfully ===")
        
    except Exception as e:
        logger.error(f"Demo failed with error: {e}")
        raise


async def demo_strands_tools_integration():
    """Demonstrate integration with Strands tools."""
    
    try:
        logger.info("\n=== Demo: Strands Tools Integration ===")
        
        # Load configuration
        config = load_agentcore_config(environment='development')
        
        # Initialize authentication manager
        auth_manager = AuthenticationManager(config.cognito)
        
        # Initialize AgentCore Runtime client
        runtime_client = AgentCoreRuntimeClient(region=config.agentcore.region)
        
        # Create Strands tools
        logger.info("Creating Strands tools...")
        tools = create_restaurant_search_tools(
            runtime_client=runtime_client,
            search_agent_arn=config.agentcore.restaurant_search_agent_arn,
            auth_manager=auth_manager
        )
        
        logger.info(f"Created {len(tools)} Strands tools:")
        for tool in tools:
            logger.info(f"  - {tool.name}: {tool.description[:100]}...")
        
        # Test tool invocation
        if tools:
            logger.info("\nTesting tool invocation...")
            district_search_tool = next((t for t in tools if t.name == "search_restaurants_by_district"), None)
            
            if district_search_tool:
                # Call the tool function
                result_json = district_search_tool(["Central district"])
                result = json.loads(result_json)
                
                if result.get("success"):
                    logger.info(f"Tool invocation successful: {result['total_count']} restaurants found")
                else:
                    logger.error(f"Tool invocation failed: {result.get('error', {}).get('message')}")
            else:
                logger.warning("District search tool not found")
        
        # Clean up
        await runtime_client.close()
        
        logger.info("Strands tools integration demo completed")
        
    except Exception as e:
        logger.error(f"Strands tools demo failed: {e}")
        raise


async def demo_error_handling():
    """Demonstrate error handling capabilities."""
    
    try:
        logger.info("\n=== Demo: Error Handling ===")
        
        # Load configuration
        config = load_agentcore_config(environment='development')
        
        # Initialize with invalid agent ARN to test error handling
        runtime_client = AgentCoreRuntimeClient(region=config.agentcore.region)
        
        search_tool = RestaurantSearchTool(
            runtime_client=runtime_client,
            search_agent_arn="arn:aws:bedrock-agentcore:us-east-1:123456789012:runtime/invalid-agent",
            auth_manager=None  # No auth manager to test fallback
        )
        
        # Test validation errors
        logger.info("Testing validation errors...")
        
        # Empty districts list
        result = await search_tool.search_restaurants_by_district([])
        logger.info(f"Empty districts validation: {'PASS' if not result.success else 'FAIL'}")
        
        # Invalid meal types
        result = await search_tool.search_restaurants_by_meal_type(["invalid_meal"])
        logger.info(f"Invalid meal types validation: {'PASS' if not result.success else 'FAIL'}")
        
        # No parameters for combined search
        result = await search_tool.search_restaurants_combined()
        logger.info(f"No parameters validation: {'PASS' if not result.success else 'FAIL'}")
        
        # Test agent invocation error (with invalid ARN)
        logger.info("Testing agent invocation error...")
        result = await search_tool.search_restaurants_by_district(["Central district"])
        logger.info(f"Agent invocation error handling: {'PASS' if not result.success else 'FAIL'}")
        
        # Test backward compatibility error responses
        logger.info("Testing backward compatibility error responses...")
        result_json = search_tool.search_restaurants_by_district_tool([])
        result_data = json.loads(result_json)
        
        if not result_data.get("success") and "error" in result_data:
            logger.info("Backward compatibility error format: PASS")
            logger.info(f"Error details: {result_data['error']['user_message']}")
        else:
            logger.info("Backward compatibility error format: FAIL")
        
        # Clean up
        await runtime_client.close()
        
        logger.info("Error handling demo completed")
        
    except Exception as e:
        logger.error(f"Error handling demo failed: {e}")
        raise


async def main():
    """Run all demos."""
    
    logger.info("Starting Restaurant Search Tool Demo")
    logger.info("=" * 60)
    
    try:
        # Run basic functionality demo
        await demo_restaurant_search_tool()
        
        # Run Strands tools integration demo
        await demo_strands_tools_integration()
        
        # Run error handling demo
        await demo_error_handling()
        
        logger.info("\n" + "=" * 60)
        logger.info("All demos completed successfully!")
        
    except Exception as e:
        logger.error(f"Demo suite failed: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    # Run the demo
    exit_code = asyncio.run(main())
    exit(exit_code)