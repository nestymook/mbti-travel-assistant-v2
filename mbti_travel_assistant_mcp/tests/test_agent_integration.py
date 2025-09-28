"""
Integration test for RestaurantAgent orchestration logic

This test verifies that the agent orchestration workflow functions correctly
with mock MCP client responses.
"""

import asyncio
import json
from unittest.mock import Mock, AsyncMock

# Add the project root to Python path for imports
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.restaurant_agent import RestaurantAgent
from models.restaurant_models import Restaurant, Sentiment, OperatingHours, RestaurantMetadata


async def test_agent_orchestration():
    """Test the complete agent orchestration workflow."""
    
    # Create a sample restaurant
    sample_restaurant = Restaurant(
        id="rest_001",
        name="Test Restaurant",
        address="123 Test Street, Central",
        meal_type=["Chinese", "Dim Sum"],
        sentiment=Sentiment(likes=85, dislikes=10, neutral=5),
        location_category="Shopping Mall",
        district="Central district",
        price_range="$$",
        operating_hours=OperatingHours(
            mon_fri=["07:00 - 11:30", "11:30 - 15:30"],
            sat_sun=["08:00 - 16:00"],
            public_holiday=["08:00 - 16:00"]
        ),
        metadata=RestaurantMetadata(
            data_quality="high",
            version="1.0",
            quality_score=95
        )
    )
    
    # Create RestaurantAgent
    agent = RestaurantAgent()
    
    # Mock the MCP client manager
    mock_mcp_manager = Mock()
    mock_mcp_manager.search_restaurants = AsyncMock(return_value=[sample_restaurant])
    mock_mcp_manager.analyze_restaurants = AsyncMock(return_value={
        "recommendation": sample_restaurant.to_dict(),
        "candidates": [],
        "ranking_method": "sentiment_likes",
        "analysis_summary": {"total_restaurants": 1}
    })
    
    agent.mcp_client_manager = mock_mcp_manager
    
    # Test the orchestration
    result = await agent.process_request(
        district="Central district",
        meal_time="breakfast",
        user_context=None,
        correlation_id="test_integration"
    )
    
    # Verify the result structure
    assert "recommendation" in result
    assert "candidates" in result
    assert "metadata" in result
    
    # Verify MCP client calls were made
    mock_mcp_manager.search_restaurants.assert_called_once()
    mock_mcp_manager.analyze_restaurants.assert_called_once()
    
    print("✓ Agent orchestration test passed")
    print(f"✓ Result structure: {list(result.keys())}")
    
    return result


async def test_parameter_processing():
    """Test parameter processing and normalization."""
    
    agent = RestaurantAgent()
    
    # Test district normalization
    params = await agent._process_parameters(
        district="central",
        meal_time="morning",
        user_context=None,
        correlation_id="test_params"
    )
    
    assert params["district"] == "Central district"
    assert params["meal_time"] == "breakfast"
    
    print("✓ Parameter processing test passed")
    print(f"✓ Normalized district: {params['district']}")
    print(f"✓ Normalized meal_time: {params['meal_time']}")
    
    return params


async def main():
    """Run all integration tests."""
    print("Running RestaurantAgent integration tests...")
    print("=" * 50)
    
    try:
        # Test parameter processing
        await test_parameter_processing()
        print()
        
        # Test full orchestration
        result = await test_agent_orchestration()
        print()
        
        print("=" * 50)
        print("✓ All integration tests passed!")
        
        # Print sample result
        print("\nSample orchestration result:")
        print(json.dumps(result, indent=2, default=str))
        
    except Exception as e:
        print(f"✗ Integration test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())