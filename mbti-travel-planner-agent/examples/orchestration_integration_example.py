"""
Tool Orchestration Integration Example

This example demonstrates how to integrate the tool orchestration engine
with the existing MBTI Travel Planner Agent.

Features demonstrated:
- Initializing the orchestration engine
- Registering existing tools
- Processing user requests through orchestration
- Monitoring performance and health
"""

import asyncio
import logging
from typing import Dict, Any, Optional

# Import orchestration components
from services.tool_orchestration_engine import (
    ToolOrchestrationEngine, OrchestrationConfig, UserContext, RequestType
)
from services.tool_registration_helper import ToolRegistrationHelper
from services.tool_registry import ToolHealthStatus

# Import existing tools (these would be the actual tool instances)
# from services.restaurant_search_tool import RestaurantSearchTool
# from services.restaurant_reasoning_tool import RestaurantReasoningTool

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OrchestrationIntegrationExample:
    """
    Example class showing how to integrate tool orchestration with the main agent.
    """
    
    def __init__(self, environment: str = "development"):
        """Initialize the orchestration integration example."""
        self.environment = environment
        self.orchestration_engine = None
        self.registration_helper = None
        
        # Mock tool instances (in real implementation, these would be actual tools)
        self.restaurant_search_tool = MockRestaurantSearchTool()
        self.restaurant_reasoning_tool = MockRestaurantReasoningTool()
    
    async def initialize_orchestration(self) -> None:
        """Initialize the orchestration engine and register tools."""
        logger.info("Initializing tool orchestration system")
        
        # Initialize orchestration engine with configuration
        config_path = "config/orchestration_config.yaml"
        self.orchestration_engine = ToolOrchestrationEngine(
            environment=self.environment,
            config_path=config_path
        )
        
        # Initialize registration helper
        self.registration_helper = ToolRegistrationHelper(self.orchestration_engine)
        
        # Register existing tools
        self.registration_helper.register_existing_tools(
            restaurant_search_tool=self.restaurant_search_tool,
            restaurant_reasoning_tool=self.restaurant_reasoning_tool
        )
        
        # Perform initial health checks
        health_status = await self.registration_helper.perform_initial_health_checks()
        logger.info(f"Initial health check results: {health_status}")
        
        logger.info("Tool orchestration system initialized successfully")
    
    async def process_user_request(self, 
                                  request_text: str,
                                  user_id: Optional[str] = None,
                                  session_id: Optional[str] = None,
                                  mbti_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Process a user request through the orchestration engine.
        
        Args:
            request_text: User's request text
            user_id: Optional user ID
            session_id: Optional session ID
            mbti_type: Optional MBTI personality type
            
        Returns:
            Orchestration result dictionary
        """
        if not self.orchestration_engine:
            raise RuntimeError("Orchestration engine not initialized")
        
        # Create user context
        user_context = UserContext(
            user_id=user_id,
            session_id=session_id,
            mbti_type=mbti_type,
            conversation_history=[],  # Could be populated from session history
            preferences={},  # Could be loaded from user profile
            location_context="Hong Kong"  # Default location context
        )
        
        logger.info(f"Processing request through orchestration: {request_text[:100]}...")
        
        # Process request through orchestration engine
        result = await self.orchestration_engine.orchestrate_request(
            request_text=request_text,
            user_context=user_context
        )
        
        logger.info(f"Orchestration completed: success={result.success}, "
                   f"tools_used={len(result.tools_used)}, "
                   f"execution_time={result.execution_time_ms:.2f}ms")
        
        return result.to_dict()
    
    async def get_orchestration_status(self) -> Dict[str, Any]:
        """Get current orchestration system status."""
        if not self.orchestration_engine:
            return {"error": "Orchestration engine not initialized"}
        
        # Get orchestration engine status
        engine_status = self.orchestration_engine.get_orchestration_status()
        
        # Get performance metrics
        performance_metrics = self.orchestration_engine.get_performance_metrics()
        
        # Get registry statistics
        registry_stats = self.orchestration_engine.tool_registry.get_registry_statistics()
        
        # Get registration summary
        registration_summary = self.registration_helper.get_registration_summary()
        
        return {
            "engine_status": engine_status,
            "performance_metrics": performance_metrics,
            "registry_statistics": registry_stats,
            "registration_summary": registration_summary
        }
    
    async def demonstrate_orchestration_scenarios(self) -> None:
        """Demonstrate various orchestration scenarios."""
        logger.info("Demonstrating orchestration scenarios")
        
        # Scenario 1: Restaurant search by location
        logger.info("=== Scenario 1: Restaurant search by location ===")
        result1 = await self.process_user_request(
            "Find restaurants in Central district",
            user_id="demo_user_1",
            session_id="demo_session_1"
        )
        logger.info(f"Result 1: {result1['success']}, tools: {result1['tools_used']}")
        
        # Scenario 2: Restaurant search by meal type
        logger.info("=== Scenario 2: Restaurant search by meal type ===")
        result2 = await self.process_user_request(
            "I'm looking for good breakfast places",
            user_id="demo_user_2",
            session_id="demo_session_2"
        )
        logger.info(f"Result 2: {result2['success']}, tools: {result2['tools_used']}")
        
        # Scenario 3: Restaurant recommendations with MBTI
        logger.info("=== Scenario 3: Restaurant recommendations with MBTI ===")
        result3 = await self.process_user_request(
            "Recommend some restaurants based on my personality",
            user_id="demo_user_3",
            session_id="demo_session_3",
            mbti_type="ENFP"
        )
        logger.info(f"Result 3: {result3['success']}, tools: {result3['tools_used']}")
        
        # Scenario 4: Combined search and recommendation
        logger.info("=== Scenario 4: Combined search and recommendation ===")
        result4 = await self.process_user_request(
            "Find lunch restaurants in Admiralty and recommend the best ones",
            user_id="demo_user_4",
            session_id="demo_session_4",
            mbti_type="INTJ"
        )
        logger.info(f"Result 4: {result4['success']}, tools: {result4['tools_used']}")
        
        # Show final status
        status = await self.get_orchestration_status()
        logger.info(f"Final orchestration status: {status['engine_status']}")


# Mock tool classes for demonstration
class MockRestaurantSearchTool:
    """Mock restaurant search tool for demonstration."""
    
    async def search_restaurants(self, **kwargs) -> Dict[str, Any]:
        """Mock search restaurants method."""
        await asyncio.sleep(0.1)  # Simulate processing time
        
        return {
            "restaurants": [
                {"name": "Mock Restaurant 1", "district": "Central", "cuisine": "Italian"},
                {"name": "Mock Restaurant 2", "district": "Central", "cuisine": "Chinese"}
            ],
            "total_count": 2,
            "search_parameters": kwargs
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Mock health check method."""
        return {"healthy": True, "response_time_ms": 50}


class MockRestaurantReasoningTool:
    """Mock restaurant reasoning tool for demonstration."""
    
    async def recommend_restaurants(self, **kwargs) -> Dict[str, Any]:
        """Mock recommend restaurants method."""
        await asyncio.sleep(0.2)  # Simulate processing time
        
        return {
            "recommendations": [
                {
                    "restaurant": "Mock Restaurant 1",
                    "score": 0.95,
                    "reasoning": "Excellent match for your preferences"
                }
            ],
            "ranking_method": "sentiment_likes",
            "parameters": kwargs
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Mock health check method."""
        return {"healthy": True, "response_time_ms": 75}


async def main():
    """Main function to run the orchestration integration example."""
    logger.info("Starting Tool Orchestration Integration Example")
    
    # Create and initialize the example
    example = OrchestrationIntegrationExample(environment="development")
    
    try:
        # Initialize orchestration system
        await example.initialize_orchestration()
        
        # Demonstrate various scenarios
        await example.demonstrate_orchestration_scenarios()
        
        # Show final status
        final_status = await example.get_orchestration_status()
        logger.info("=== Final System Status ===")
        logger.info(f"Total tools: {final_status['registry_statistics']['total_tools']}")
        logger.info(f"Active workflows: {final_status['engine_status']['active_workflows']}")
        logger.info(f"Performance metrics available for: {len(final_status['performance_metrics'])} tools")
        
    except Exception as e:
        logger.error(f"Example execution failed: {e}")
        raise
    
    logger.info("Tool Orchestration Integration Example completed successfully")


if __name__ == "__main__":
    asyncio.run(main())