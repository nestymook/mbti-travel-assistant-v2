"""
Tool Selection System Demo

This demo showcases the intelligent tool selection system including:
- Basic tool selection with capability matching
- Advanced tool selection with user context
- Health status checking and fallback mechanisms
- User preference learning and adaptation
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.tool_selector import ToolSelector, SelectionWeights
from services.advanced_tool_selector import AdvancedToolSelector, HealthCheckStrategy, UserPreferenceProfile
from services.tool_registry import (
    ToolRegistry, ToolMetadata, ToolCapability, ToolType, ToolHealthStatus,
    PerformanceCharacteristics, ResourceRequirements
)
from services.orchestration_types import Intent, UserContext, RequestType


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MockToolInstance:
    """Mock tool instance for demonstration."""
    
    def __init__(self, tool_id: str, success_rate: float = 0.9):
        self.tool_id = tool_id
        self.success_rate = success_rate
    
    async def health_check(self) -> Dict[str, Any]:
        """Mock health check."""
        import random
        is_healthy = random.random() < self.success_rate
        return {
            'healthy': is_healthy,
            'response_time_ms': random.uniform(500, 2000),
            'error': None if is_healthy else "Mock error for demonstration"
        }
    
    async def search_restaurants(self, **kwargs) -> Dict[str, Any]:
        """Mock restaurant search."""
        await asyncio.sleep(0.1)  # Simulate processing time
        return {
            'restaurants': [
                {'name': f'Restaurant {i}', 'district': kwargs.get('districts', ['Central'])[0]}
                for i in range(5)
            ],
            'total_count': 5
        }
    
    async def recommend_restaurants(self, **kwargs) -> Dict[str, Any]:
        """Mock restaurant recommendation."""
        await asyncio.sleep(0.15)  # Simulate processing time
        return {
            'recommendations': [
                {'restaurant': f'Recommended Restaurant {i}', 'score': 0.9 - (i * 0.1)}
                for i in range(3)
            ]
        }


def create_sample_tools() -> Dict[str, ToolMetadata]:
    """Create sample tools for demonstration."""
    
    # Restaurant Search Tool
    search_tool = ToolMetadata(
        id="restaurant_search_tool",
        name="Restaurant Search Tool",
        description="Advanced restaurant search with multiple criteria",
        tool_type=ToolType.RESTAURANT_SEARCH,
        capabilities=[
            ToolCapability(
                name="search_by_district",
                description="Search restaurants by district/location",
                required_parameters=["districts"],
                optional_parameters=["meal_types"],
                use_cases=["location-based restaurant discovery"]
            ),
            ToolCapability(
                name="search_by_meal_type",
                description="Search restaurants by meal type",
                required_parameters=["meal_types"],
                optional_parameters=["districts"],
                use_cases=["meal-specific restaurant search"]
            ),
            ToolCapability(
                name="combined_search",
                description="Combined search with multiple criteria",
                required_parameters=[],
                optional_parameters=["districts", "meal_types"],
                use_cases=["comprehensive restaurant search"]
            )
        ],
        performance_characteristics=PerformanceCharacteristics(
            average_response_time_ms=1200.0,
            success_rate=0.92,
            throughput_requests_per_minute=80,
            resource_requirements=ResourceRequirements(
                cpu_cores=1.0,
                memory_mb=256,
                network_bandwidth_mbps=5.0
            )
        ),
        tags={"search", "restaurants", "location"}
    )
    
    # Restaurant Reasoning Tool
    reasoning_tool = ToolMetadata(
        id="restaurant_reasoning_tool",
        name="Restaurant Reasoning Tool",
        description="AI-powered restaurant recommendations and analysis",
        tool_type=ToolType.RESTAURANT_REASONING,
        capabilities=[
            ToolCapability(
                name="recommend_restaurants",
                description="Generate personalized restaurant recommendations",
                required_parameters=["restaurants"],
                optional_parameters=["user_preferences", "mbti_type"],
                use_cases=["personalized recommendations", "decision support"]
            ),
            ToolCapability(
                name="analyze_sentiment",
                description="Analyze restaurant reviews and sentiment",
                required_parameters=["data"],
                optional_parameters=["analysis_type"],
                use_cases=["sentiment analysis", "review processing"]
            ),
            ToolCapability(
                name="mbti_personalization",
                description="MBTI-based personalization",
                required_parameters=["mbti_type"],
                optional_parameters=["preferences"],
                use_cases=["personality-based recommendations"]
            )
        ],
        performance_characteristics=PerformanceCharacteristics(
            average_response_time_ms=1800.0,
            success_rate=0.88,
            throughput_requests_per_minute=45,
            resource_requirements=ResourceRequirements(
                cpu_cores=2.0,
                memory_mb=512,
                network_bandwidth_mbps=8.0
            )
        ),
        tags={"reasoning", "ai", "recommendations", "mbti"}
    )
    
    # Sentiment Analysis Tool
    sentiment_tool = ToolMetadata(
        id="sentiment_analysis_tool",
        name="Sentiment Analysis Tool",
        description="Specialized sentiment analysis for restaurant reviews",
        tool_type=ToolType.SENTIMENT_ANALYSIS,
        capabilities=[
            ToolCapability(
                name="analyze_sentiment",
                description="Advanced sentiment analysis",
                required_parameters=["text_data"],
                optional_parameters=["language", "domain"],
                use_cases=["review analysis", "feedback processing"]
            )
        ],
        performance_characteristics=PerformanceCharacteristics(
            average_response_time_ms=800.0,
            success_rate=0.95,
            throughput_requests_per_minute=120,
            resource_requirements=ResourceRequirements(
                cpu_cores=0.5,
                memory_mb=128,
                network_bandwidth_mbps=2.0
            )
        ),
        tags={"sentiment", "analysis", "nlp"}
    )
    
    return {
        "restaurant_search_tool": search_tool,
        "restaurant_reasoning_tool": reasoning_tool,
        "sentiment_analysis_tool": sentiment_tool
    }


async def setup_tool_registry() -> ToolRegistry:
    """Set up tool registry with sample tools."""
    registry = ToolRegistry()
    
    # Create and register tools
    tools = create_sample_tools()
    
    for tool_id, tool_metadata in tools.items():
        # Create mock tool instance
        tool_instance = MockToolInstance(tool_id)
        
        # Register tool
        registry.register_tool(tool_metadata, tool_instance)
        
        # Set initial health status
        registry.update_tool_health_status(
            tool_id=tool_id,
            status=ToolHealthStatus.HEALTHY,
            response_time_ms=tool_metadata.performance_characteristics.average_response_time_ms
        )
    
    logger.info(f"Registered {len(tools)} tools in registry")
    return registry


async def demo_basic_tool_selection():
    """Demonstrate basic tool selection functionality."""
    logger.info("=== Basic Tool Selection Demo ===")
    
    # Set up registry
    registry = await setup_tool_registry()
    
    # Create basic tool selector
    selector = ToolSelector(
        tool_registry=registry,
        selection_weights=SelectionWeights(
            capability_weight=0.4,
            performance_weight=0.3,
            health_weight=0.2,
            context_weight=0.05,
            compatibility_weight=0.05
        )
    )
    
    # Test different intents
    test_intents = [
        Intent(
            type=RequestType.RESTAURANT_SEARCH_BY_LOCATION,
            confidence=0.9,
            required_capabilities=["search_by_district"],
            parameters={"districts": ["Central", "Admiralty"]}
        ),
        Intent(
            type=RequestType.RESTAURANT_RECOMMENDATION,
            confidence=0.8,
            required_capabilities=["recommend_restaurants"],
            parameters={"user_preferences": {"cuisine": "Italian"}}
        ),
        Intent(
            type=RequestType.SENTIMENT_ANALYSIS,
            confidence=0.85,
            required_capabilities=["analyze_sentiment"],
            parameters={"text_data": "Restaurant reviews to analyze"}
        )
    ]
    
    for i, intent in enumerate(test_intents, 1):
        logger.info(f"\n--- Test {i}: {intent.type.value} ---")
        
        # Select tools
        selected_tools = await selector.select_tools(
            intent=intent,
            max_tools=3,
            min_score_threshold=0.3
        )
        
        logger.info(f"Selected {len(selected_tools)} tools:")
        for tool in selected_tools:
            logger.info(f"  - {tool.tool_name} (confidence: {tool.confidence:.3f})")
            logger.info(f"    Reason: {tool.selection_reason}")
            logger.info(f"    Fallbacks: {len(tool.fallback_tools)} available")
    
    # Show selection statistics
    stats = selector.get_selection_statistics()
    logger.info(f"\nSelection Statistics: {stats}")


async def demo_advanced_tool_selection():
    """Demonstrate advanced tool selection with user context."""
    logger.info("\n=== Advanced Tool Selection Demo ===")
    
    # Set up registry
    registry = await setup_tool_registry()
    
    # Create advanced tool selector
    advanced_selector = AdvancedToolSelector(
        tool_registry=registry,
        selection_weights=SelectionWeights(),
        health_check_strategy=HealthCheckStrategy.CACHED,
        enable_user_learning=True
    )
    
    # Create user contexts for different scenarios
    user_contexts = [
        UserContext(
            user_id="user_1",
            session_id="session_1",
            mbti_type="ENFP",
            location_context="Central District",
            conversation_history=[
                "I want to find restaurants in Central",
                "Looking for good Italian food",
                "Need recommendations for dinner"
            ],
            preferences={"cuisine": "Italian", "price_range": "mid"}
        ),
        UserContext(
            user_id="user_2",
            session_id="session_2",
            mbti_type="INTJ",
            location_context="Admiralty",
            conversation_history=[
                "Analyze restaurant reviews",
                "Need data-driven recommendations"
            ],
            preferences={"analysis_depth": "detailed", "data_driven": True}
        )
    ]
    
    # Test intent
    intent = Intent(
        type=RequestType.COMBINED_SEARCH_AND_RECOMMENDATION,
        confidence=0.9,
        required_capabilities=["search_by_district", "recommend_restaurants"],
        optional_capabilities=["mbti_personalization"],
        parameters={"districts": ["Central"], "meal_types": ["dinner"]}
    )
    
    for i, user_context in enumerate(user_contexts, 1):
        logger.info(f"\n--- User {i} ({user_context.mbti_type}) ---")
        
        # Select tools with context
        selected_tools = await advanced_selector.select_tools_with_context(
            intent=intent,
            user_context=user_context,
            max_tools=3,
            require_health_check=True
        )
        
        logger.info(f"Selected {len(selected_tools)} tools for {user_context.mbti_type} user:")
        for tool in selected_tools:
            logger.info(f"  - {tool.tool_name} (confidence: {tool.confidence:.3f})")
            logger.info(f"    Reason: {tool.selection_reason}")
            
            # Show performance breakdown
            perf = tool.expected_performance
            logger.info(f"    Performance: capability={perf.get('capability_score', 0):.2f}, "
                       f"health={perf.get('health_score', 0):.2f}, "
                       f"context={perf.get('context_score', 0):.2f}")


async def demo_user_learning():
    """Demonstrate user learning and preference adaptation."""
    logger.info("\n=== User Learning Demo ===")
    
    # Set up registry
    registry = await setup_tool_registry()
    
    # Create advanced tool selector
    advanced_selector = AdvancedToolSelector(
        tool_registry=registry,
        enable_user_learning=True
    )
    
    user_id = "learning_user"
    
    # Simulate user feedback over time
    feedback_scenarios = [
        {"tool_id": "restaurant_search_tool", "success": True, "rating": 0.8, "feedback": "Great search results"},
        {"tool_id": "restaurant_reasoning_tool", "success": True, "rating": 0.9, "feedback": "Excellent recommendations"},
        {"tool_id": "sentiment_analysis_tool", "success": False, "rating": 0.3, "feedback": "Not very accurate"},
        {"tool_id": "restaurant_search_tool", "success": True, "rating": 0.85, "feedback": "Very helpful"},
        {"tool_id": "restaurant_reasoning_tool", "success": True, "rating": 0.95, "feedback": "Perfect for my needs"},
    ]
    
    logger.info("Recording user feedback...")
    for feedback in feedback_scenarios:
        await advanced_selector.record_tool_feedback(
            tool_id=feedback["tool_id"],
            user_id=user_id,
            success=feedback["success"],
            user_rating=feedback["rating"],
            feedback_text=feedback["feedback"]
        )
        logger.info(f"  Recorded: {feedback['tool_id']} - {feedback['rating']:.1f}/1.0")
    
    # Get user profile
    user_profile = await advanced_selector._get_user_profile(user_id)
    logger.info(f"\nUser Profile for {user_id}:")
    logger.info(f"  Preferred tools: {list(user_profile.preferred_tools)}")
    logger.info(f"  Avoided tools: {list(user_profile.avoided_tools)}")
    logger.info(f"  Tool ratings: {user_profile.tool_ratings}")
    logger.info(f"  Usage frequency: {user_profile.usage_frequency}")
    
    # Test selection with learned preferences
    intent = Intent(
        type=RequestType.RESTAURANT_RECOMMENDATION,
        confidence=0.8,
        required_capabilities=["recommend_restaurants"]
    )
    
    user_context = UserContext(user_id=user_id, session_id="learning_session")
    
    selected_tools = await advanced_selector.select_tools_with_context(
        intent=intent,
        user_context=user_context,
        require_health_check=False
    )
    
    logger.info(f"\nTools selected after learning:")
    for tool in selected_tools:
        logger.info(f"  - {tool.tool_name} (confidence: {tool.confidence:.3f})")
        logger.info(f"    Selection influenced by user preferences")


async def demo_health_checking_and_fallbacks():
    """Demonstrate health checking and fallback mechanisms."""
    logger.info("\n=== Health Checking and Fallbacks Demo ===")
    
    # Set up registry
    registry = await setup_tool_registry()
    
    # Create advanced tool selector
    advanced_selector = AdvancedToolSelector(
        tool_registry=registry,
        health_check_strategy=HealthCheckStrategy.IMMEDIATE
    )
    
    # Simulate some tools being unhealthy
    registry.update_tool_health_status(
        tool_id="sentiment_analysis_tool",
        status=ToolHealthStatus.UNHEALTHY,
        error_message="Service temporarily unavailable"
    )
    
    # Test health checking
    logger.info("Checking tool availability...")
    for tool_id in ["restaurant_search_tool", "restaurant_reasoning_tool", "sentiment_analysis_tool"]:
        health_result = await advanced_selector.check_tool_availability(tool_id, force_check=True)
        status = "✓ Healthy" if health_result.is_healthy else "✗ Unhealthy"
        logger.info(f"  {tool_id}: {status} (score: {health_result.health_score:.2f})")
        if health_result.error_message:
            logger.info(f"    Error: {health_result.error_message}")
    
    # Test fallback selection
    logger.info("\nTesting fallback mechanisms...")
    primary_tool_id = "sentiment_analysis_tool"  # This one is unhealthy
    
    fallback_tools = await advanced_selector.get_fallback_tools(
        primary_tool_id=primary_tool_id,
        attempted_tools={primary_tool_id}
    )
    
    logger.info(f"Fallback tools for {primary_tool_id}:")
    for tool_id, confidence in fallback_tools:
        logger.info(f"  - {tool_id} (confidence: {confidence:.3f})")


async def demo_tool_compatibility():
    """Demonstrate tool compatibility validation."""
    logger.info("\n=== Tool Compatibility Demo ===")
    
    # Set up registry
    registry = await setup_tool_registry()
    
    # Create tool selector
    selector = ToolSelector(tool_registry=registry)
    
    # Get all tools for compatibility testing
    all_tools = registry.get_all_tools()
    
    # Test compatibility
    compatibility_result = await selector.validate_tool_compatibility(
        tools=all_tools,
        workflow_requirements={
            'max_execution_time': 5000,  # 5 seconds
            'execution_order': ['Restaurant Search Tool', 'Restaurant Reasoning Tool']
        }
    )
    
    logger.info("Tool Compatibility Analysis:")
    logger.info(f"  Overall compatible: {compatibility_result['compatible']}")
    logger.info(f"  Workflow feasible: {compatibility_result['workflow_feasible']}")
    
    if compatibility_result['issues']:
        logger.info("  Issues found:")
        for issue in compatibility_result['issues']:
            logger.info(f"    - {issue}")
    
    if compatibility_result['recommendations']:
        logger.info("  Recommendations:")
        for rec in compatibility_result['recommendations']:
            logger.info(f"    - {rec}")
    
    # Show compatibility matrix
    logger.info("  Compatibility Matrix:")
    for pair, compat_info in compatibility_result['compatibility_matrix'].items():
        tool1, tool2 = pair.split('_', 1)
        status = "✓" if compat_info['compatible'] else "✗"
        logger.info(f"    {tool1} ↔ {tool2}: {status} (score: {compat_info['compatibility_score']:.2f})")


async def main():
    """Run all demonstrations."""
    logger.info("Starting Tool Selection System Demonstration")
    logger.info("=" * 60)
    
    try:
        # Run all demos
        await demo_basic_tool_selection()
        await demo_advanced_tool_selection()
        await demo_user_learning()
        await demo_health_checking_and_fallbacks()
        await demo_tool_compatibility()
        
        logger.info("\n" + "=" * 60)
        logger.info("Tool Selection System Demonstration Complete!")
        
    except Exception as e:
        logger.error(f"Demo failed: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(main())