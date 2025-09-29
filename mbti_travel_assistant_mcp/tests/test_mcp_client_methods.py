"""
Simple test to validate MCP client methods are properly implemented.

This test validates that all required methods for restaurant MCP client integration
are implemented and have the correct signatures.
"""

import inspect
import sys
import os

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_mcp_client_methods_exist():
    """Test that all required MCP client methods are implemented."""
    
    # Import with mocked dependencies
    from unittest.mock import MagicMock, patch
    
    with patch.dict('sys.modules', {
        'psutil': MagicMock(),
        'services.performance_monitor': MagicMock(),
        'config.settings': MagicMock()
    }):
        from services.mcp_client_manager import MCPClientManager
        
        # Create instance
        manager = MCPClientManager()
        
        # Test that all required methods exist
        required_methods = [
            'search_breakfast_restaurants',
            'search_lunch_restaurants', 
            'search_dinner_restaurants',
            'get_restaurant_recommendations',
            'assign_meal_restaurants',
            'assign_3day_itinerary_restaurants',
            'get_restaurant_candidates',
            'validate_restaurant_operating_hours',
            'search_restaurants_with_fallback',
            'assign_meal_with_fallback',
            'create_restaurant_assignment_placeholder',
            'assign_meal_restaurants_with_comprehensive_fallback',
            'generate_restaurant_candidates_for_itinerary'
        ]
        
        for method_name in required_methods:
            assert hasattr(manager, method_name), f"Method {method_name} not found"
            method = getattr(manager, method_name)
            assert callable(method), f"Method {method_name} is not callable"
            
            # Check if it's an async method
            if method_name != 'validate_restaurant_operating_hours':  # This one might not be async
                assert inspect.iscoroutinefunction(method), f"Method {method_name} should be async"
        
        print("✅ All required MCP client methods are implemented")
        
        # Test method signatures
        breakfast_sig = inspect.signature(manager.search_breakfast_restaurants)
        assert 'district' in breakfast_sig.parameters
        assert 'used_restaurant_ids' in breakfast_sig.parameters
        
        lunch_sig = inspect.signature(manager.search_lunch_restaurants)
        assert 'districts' in lunch_sig.parameters
        assert 'used_restaurant_ids' in lunch_sig.parameters
        
        dinner_sig = inspect.signature(manager.search_dinner_restaurants)
        assert 'districts' in dinner_sig.parameters
        assert 'used_restaurant_ids' in dinner_sig.parameters
        
        recommendations_sig = inspect.signature(manager.get_restaurant_recommendations)
        assert 'restaurants' in recommendations_sig.parameters
        assert 'ranking_method' in recommendations_sig.parameters
        
        print("✅ All method signatures are correct")
        
        # Test helper methods
        helper_methods = [
            '_time_ranges_overlap',
            '_parse_time_range'
        ]
        
        for method_name in helper_methods:
            assert hasattr(manager, method_name), f"Helper method {method_name} not found"
            method = getattr(manager, method_name)
            assert callable(method), f"Helper method {method_name} is not callable"
        
        print("✅ All helper methods are implemented")


def test_time_parsing_functionality():
    """Test time parsing functionality without async dependencies."""
    
    from unittest.mock import MagicMock, patch
    
    with patch.dict('sys.modules', {
        'psutil': MagicMock(),
        'services.performance_monitor': MagicMock(),
        'config.settings': MagicMock()
    }):
        from services.mcp_client_manager import MCPClientManager
        
        manager = MCPClientManager()
        
        # Test time range parsing
        start, end = manager._parse_time_range("09:00 - 18:00")
        assert start == 540  # 9 * 60
        assert end == 1080   # 18 * 60
        
        # Test time range overlap
        assert manager._time_ranges_overlap("09:00 - 18:00", "11:30 - 17:29") is True
        assert manager._time_ranges_overlap("06:00 - 11:29", "12:00 - 18:00") is False
        
        print("✅ Time parsing functionality works correctly")


def test_error_classes_exist():
    """Test that all required error classes are defined."""
    
    from unittest.mock import MagicMock, patch
    
    with patch.dict('sys.modules', {
        'psutil': MagicMock(),
        'services.performance_monitor': MagicMock(),
        'config.settings': MagicMock()
    }):
        from services.mcp_client_manager import (
            MCPConnectionError,
            MCPToolCallError,
            MCPCircuitBreakerOpenError,
            MCPErrorType,
            CircuitBreakerState
        )
        
        # Test error classes exist and are exceptions
        assert issubclass(MCPConnectionError, Exception)
        assert issubclass(MCPToolCallError, Exception)
        assert issubclass(MCPCircuitBreakerOpenError, Exception)
        
        # Test enums exist
        assert hasattr(MCPErrorType, 'CONNECTION_ERROR')
        assert hasattr(MCPErrorType, 'TIMEOUT_ERROR')
        assert hasattr(MCPErrorType, 'AUTHENTICATION_ERROR')
        
        assert hasattr(CircuitBreakerState, 'CLOSED')
        assert hasattr(CircuitBreakerState, 'OPEN')
        assert hasattr(CircuitBreakerState, 'HALF_OPEN')
        
        print("✅ All error classes and enums are properly defined")


if __name__ == "__main__":
    test_mcp_client_methods_exist()
    test_time_parsing_functionality()
    test_error_classes_exist()
    print("\n🎉 All MCP client integration tests passed!")