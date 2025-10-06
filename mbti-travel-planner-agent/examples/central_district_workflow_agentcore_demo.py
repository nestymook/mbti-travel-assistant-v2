"""
Demo script for Central District Workflow with AgentCore Integration

This script demonstrates the updated Central District workflow that uses AgentCore
Runtime API instead of HTTP gateway calls. It shows parallel execution, error
handling, and monitoring capabilities.
"""

import asyncio
import json
import logging
import sys
import os
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from services.central_district_workflow import (
    CentralDistrictWorkflow,
    search_central_district_restaurants,
    validate_central_district_workflow_health
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def demo_basic_workflow():
    """Demonstrate basic workflow execution."""
    print("\n" + "="*60)
    print("DEMO: Basic Central District Workflow with AgentCore")
    print("="*60)
    
    try:
        # Execute basic workflow
        result = await search_central_district_restaurants(
            meal_types=["lunch"],
            include_recommendations=True,
            environment="development",
            max_results=5
        )
        
        print(f"\n✅ Workflow Status: {'SUCCESS' if result.success else 'FAILED'}")
        print(f"📊 Restaurants Found: {result.restaurants_found}")
        print(f"⏱️  Execution Time: {result.execution_time:.2f}s")
        
        if result.search_execution_time_ms:
            print(f"🔍 Search Time: {result.search_execution_time_ms}ms")
        
        if result.reasoning_execution_time_ms:
            print(f"🧠 Reasoning Time: {result.reasoning_execution_time_ms}ms")
        
        if result.parallel_execution:
            print("⚡ Parallel Execution: ENABLED")
        
        if result.recommendations:
            print(f"🌟 Recommendations: Available")
        
        if result.formatted_response:
            print(f"\n📝 Formatted Response Preview:")
            print("-" * 40)
            # Show first 300 characters of response
            preview = result.formatted_response[:300]
            if len(result.formatted_response) > 300:
                preview += "..."
            print(preview)
        
        if result.agent_performance_metrics:
            print(f"\n📈 Performance Metrics:")
            print(f"   Search Tool Calls: {result.agent_performance_metrics.get('search_tool_metrics', {}).get('total_calls', 'N/A')}")
            print(f"   Reasoning Tool Calls: {result.agent_performance_metrics.get('reasoning_tool_metrics', {}).get('total_calls', 'N/A')}")
        
        return result
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        logger.error(f"Basic workflow demo failed: {e}")
        return None


async def demo_parallel_workflow():
    """Demonstrate parallel workflow execution."""
    print("\n" + "="*60)
    print("DEMO: Parallel Workflow with MBTI Recommendations")
    print("="*60)
    
    try:
        # Execute parallel workflow with MBTI
        result = await search_central_district_restaurants(
            meal_types=["lunch", "dinner"],
            mbti_type="ENFP",
            preferences={
                "cuisine_preference": "Asian",
                "price_range": "$$",
                "atmosphere": "social"
            },
            environment="development",
            max_results=10,
            use_parallel_execution=True
        )
        
        print(f"\n✅ Parallel Workflow Status: {'SUCCESS' if result.success else 'FAILED'}")
        print(f"📊 Restaurants Found: {result.restaurants_found}")
        print(f"⏱️  Total Execution Time: {result.execution_time:.2f}s")
        print(f"⚡ Parallel Execution: {'YES' if result.parallel_execution else 'NO'}")
        
        if result.recommendations:
            print(f"🧠 MBTI Analysis: Available")
            if isinstance(result.recommendations, dict):
                confidence = result.recommendations.get('confidence_score', 0)
                print(f"🎯 Confidence Score: {confidence:.2f}")
        
        return result
        
    except Exception as e:
        print(f"\n❌ Parallel demo failed: {e}")
        logger.error(f"Parallel workflow demo failed: {e}")
        return None


async def demo_health_monitoring():
    """Demonstrate health monitoring and validation."""
    print("\n" + "="*60)
    print("DEMO: Workflow Health Monitoring")
    print("="*60)
    
    try:
        # Validate workflow health
        health_results = await validate_central_district_workflow_health(
            environment="development"
        )
        
        print(f"\n🏥 Health Validation Status:")
        
        if "health_status" in health_results:
            health = health_results["health_status"]
            overall_health = health.get("overall_health", "unknown")
            print(f"   Overall Health: {overall_health.upper()}")
            print(f"   Environment: {health.get('environment', 'unknown')}")
            
            if "components" in health:
                components = health["components"]
                if "search_agent" in components:
                    search_health = components["search_agent"]["health"]
                    print(f"   Search Agent: {search_health.upper()}")
                
                if "reasoning_agent" in components:
                    reasoning_health = components["reasoning_agent"]["health"]
                    print(f"   Reasoning Agent: {reasoning_health.upper()}")
                
                if "workflow" in components:
                    workflow_metrics = components["workflow"]
                    print(f"   Workflow Calls: {workflow_metrics.get('total_calls', 0)}")
                    print(f"   Workflow Errors: {workflow_metrics.get('total_errors', 0)}")
        
        if "connectivity_tests" in health_results:
            connectivity = health_results["connectivity_tests"]
            overall_status = connectivity.get("overall_status", "unknown")
            print(f"\n🔗 Connectivity Status: {overall_status.upper()}")
            
            if "tests" in connectivity:
                tests = connectivity["tests"]
                for agent_name, test_result in tests.items():
                    status = test_result.get("status", "unknown")
                    response_time = test_result.get("response_time_ms", 0)
                    print(f"   {agent_name}: {status.upper()} ({response_time}ms)")
        
        return health_results
        
    except Exception as e:
        print(f"\n❌ Health monitoring demo failed: {e}")
        logger.error(f"Health monitoring demo failed: {e}")
        return None


async def demo_error_scenarios():
    """Demonstrate error handling scenarios."""
    print("\n" + "="*60)
    print("DEMO: Error Handling Scenarios")
    print("="*60)
    
    try:
        # Test with invalid environment (should handle gracefully)
        print("\n🧪 Testing invalid environment handling...")
        
        try:
            result = await search_central_district_restaurants(
                meal_types=["invalid_meal_type"],  # This should be handled
                environment="development",
                max_results=5
            )
            
            if result:
                print(f"   Result: {'SUCCESS' if result.success else 'HANDLED GRACEFULLY'}")
                if not result.success:
                    print(f"   Error Message: {result.error_message}")
            
        except Exception as e:
            print(f"   Exception handled: {type(e).__name__}: {e}")
        
        # Test with no meal types (should work)
        print("\n🧪 Testing no meal type filters...")
        
        result = await search_central_district_restaurants(
            meal_types=None,
            environment="development",
            max_results=3
        )
        
        if result:
            print(f"   Result: {'SUCCESS' if result.success else 'FAILED'}")
            print(f"   Restaurants Found: {result.restaurants_found}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error scenarios demo failed: {e}")
        logger.error(f"Error scenarios demo failed: {e}")
        return False


async def demo_workflow_direct():
    """Demonstrate direct workflow usage."""
    print("\n" + "="*60)
    print("DEMO: Direct Workflow Instance Usage")
    print("="*60)
    
    try:
        # Create workflow instance directly
        workflow = CentralDistrictWorkflow(environment="development")
        
        print(f"🏗️  Workflow initialized for environment: {workflow.config.environment}")
        print(f"🔍 Search Agent ARN: ...{workflow.config.agentcore.restaurant_search_agent_arn[-20:]}")
        print(f"🧠 Reasoning Agent ARN: ...{workflow.config.agentcore.restaurant_reasoning_agent_arn[-20:]}")
        
        # Get health status
        health_status = workflow.get_workflow_health_status()
        print(f"\n🏥 Initial Health Status: {health_status.get('overall_health', 'unknown').upper()}")
        
        # Test connectivity (this will likely fail in demo environment)
        print(f"\n🔗 Testing agent connectivity...")
        connectivity_results = await workflow.validate_agent_connectivity()
        overall_status = connectivity_results.get("overall_status", "unknown")
        print(f"   Connectivity Status: {overall_status.upper()}")
        
        # Reset performance metrics
        workflow.reset_performance_metrics()
        print(f"📊 Performance metrics reset")
        
        return workflow
        
    except Exception as e:
        print(f"\n❌ Direct workflow demo failed: {e}")
        logger.error(f"Direct workflow demo failed: {e}")
        return None


async def main():
    """Run all demo scenarios."""
    print("🚀 Starting Central District Workflow AgentCore Demo")
    print(f"📅 Demo started at: {datetime.now().isoformat()}")
    
    # Run all demos
    demos = [
        ("Basic Workflow", demo_basic_workflow),
        ("Parallel Workflow", demo_parallel_workflow),
        ("Health Monitoring", demo_health_monitoring),
        ("Error Scenarios", demo_error_scenarios),
        ("Direct Workflow", demo_workflow_direct)
    ]
    
    results = {}
    
    for demo_name, demo_func in demos:
        try:
            print(f"\n🎯 Running {demo_name} demo...")
            result = await demo_func()
            results[demo_name] = {"success": True, "result": result}
        except Exception as e:
            print(f"❌ {demo_name} demo failed: {e}")
            results[demo_name] = {"success": False, "error": str(e)}
    
    # Summary
    print("\n" + "="*60)
    print("DEMO SUMMARY")
    print("="*60)
    
    successful_demos = sum(1 for r in results.values() if r["success"])
    total_demos = len(results)
    
    print(f"✅ Successful Demos: {successful_demos}/{total_demos}")
    
    for demo_name, result in results.items():
        status = "✅ PASS" if result["success"] else "❌ FAIL"
        print(f"   {demo_name}: {status}")
        if not result["success"]:
            print(f"      Error: {result['error']}")
    
    print(f"\n📅 Demo completed at: {datetime.now().isoformat()}")
    
    if successful_demos == total_demos:
        print("🎉 All demos completed successfully!")
    else:
        print("⚠️  Some demos failed - this is expected in a demo environment without actual AgentCore agents")


if __name__ == "__main__":
    # Run the demo
    asyncio.run(main())