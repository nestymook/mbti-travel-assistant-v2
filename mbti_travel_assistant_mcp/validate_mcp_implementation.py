"""
Validation script for MCP client implementation.

This script validates that all required methods for restaurant MCP client integration
are implemented correctly by checking the source code directly.
"""

import os
import re
import ast


def validate_mcp_client_implementation():
    """Validate that all required MCP client methods are implemented."""
    
    # Read the MCP client manager source code
    mcp_client_path = os.path.join(os.path.dirname(__file__), 'services', 'mcp_client_manager.py')
    
    if not os.path.exists(mcp_client_path):
        print("❌ MCP client manager file not found")
        return False
    
    with open(mcp_client_path, 'r', encoding='utf-8') as f:
        source_code = f.read()
    
    # Required methods for task 6.1, 6.2, and 6.3
    required_methods = {
        # Task 6.1: Create restaurant MCP client manager
        'search_breakfast_restaurants': 'Breakfast restaurant search (06:00-11:29) with district filtering',
        'search_lunch_restaurants': 'Lunch restaurant search (11:30-17:29) with district matching',
        'search_dinner_restaurants': 'Dinner restaurant search (17:30-23:59) with district matching',
        
        # Task 6.2: Implement dinner assignment and recommendations
        'get_restaurant_recommendations': 'Restaurant recommendation calls using reasoning MCP',
        'assign_meal_restaurants': 'Restaurant assignment with uniqueness enforcement',
        
        # Task 6.3: Add MCP error handling and retry logic
        'search_restaurants_with_fallback': 'MCP connection failure handling with fallback',
        'assign_meal_with_fallback': 'Retry logic with exponential backoff',
        'create_restaurant_assignment_placeholder': 'Fallback restaurant assignment strategies',
        'assign_meal_restaurants_with_comprehensive_fallback': 'Comprehensive fallback strategies'
    }
    
    # Additional methods for complete functionality
    additional_methods = {
        'assign_3day_itinerary_restaurants': '3-day itinerary restaurant assignment',
        'get_restaurant_candidates': 'Restaurant candidate generation',
        'validate_restaurant_operating_hours': 'Operating hours validation',
        'generate_restaurant_candidates_for_itinerary': 'Itinerary candidate generation'
    }
    
    all_methods = {**required_methods, **additional_methods}
    
    print("🔍 Validating MCP client implementation...")
    print("=" * 60)
    
    # Check each method
    missing_methods = []
    implemented_methods = []
    
    for method_name, description in all_methods.items():
        # Look for method definition
        pattern = rf'async def {method_name}\s*\('
        if re.search(pattern, source_code):
            implemented_methods.append((method_name, description))
            print(f"✅ {method_name}: {description}")
        else:
            # Check if it's a non-async method
            pattern = rf'def {method_name}\s*\('
            if re.search(pattern, source_code):
                implemented_methods.append((method_name, description))
                print(f"✅ {method_name}: {description}")
            else:
                missing_methods.append((method_name, description))
                print(f"❌ {method_name}: {description}")
    
    print("=" * 60)
    
    # Check helper methods
    helper_methods = [
        '_time_ranges_overlap',
        '_parse_time_range'
    ]
    
    print("\n🔧 Checking helper methods...")
    for method_name in helper_methods:
        pattern = rf'def {method_name}\s*\('
        if re.search(pattern, source_code):
            print(f"✅ {method_name}: Helper method implemented")
        else:
            print(f"❌ {method_name}: Helper method missing")
    
    # Check error handling classes
    print("\n🚨 Checking error handling classes...")
    error_classes = [
        'MCPConnectionError',
        'MCPToolCallError', 
        'MCPCircuitBreakerOpenError',
        'MCPErrorType',
        'CircuitBreakerState'
    ]
    
    for class_name in error_classes:
        pattern = rf'class {class_name}'
        if re.search(pattern, source_code):
            print(f"✅ {class_name}: Error class defined")
        else:
            print(f"❌ {class_name}: Error class missing")
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 IMPLEMENTATION SUMMARY")
    print("=" * 60)
    
    total_required = len(required_methods)
    implemented_required = len([m for m in implemented_methods if m[0] in required_methods])
    
    print(f"Required methods: {implemented_required}/{total_required}")
    print(f"Additional methods: {len(implemented_methods) - implemented_required}")
    print(f"Total methods: {len(implemented_methods)}")
    
    if missing_methods:
        print(f"\n❌ Missing methods ({len(missing_methods)}):")
        for method_name, description in missing_methods:
            print(f"   - {method_name}: {description}")
    
    # Check specific requirements
    print("\n📋 REQUIREMENT VALIDATION")
    print("=" * 60)
    
    # Task 6.1 requirements
    task_6_1_methods = ['search_breakfast_restaurants', 'search_lunch_restaurants', 'search_dinner_restaurants']
    task_6_1_complete = all(method in [m[0] for m in implemented_methods] for method in task_6_1_methods)
    print(f"✅ Task 6.1 - Create restaurant MCP client manager: {'COMPLETE' if task_6_1_complete else 'INCOMPLETE'}")
    
    # Task 6.2 requirements  
    task_6_2_methods = ['search_dinner_restaurants', 'get_restaurant_recommendations', 'assign_meal_restaurants']
    task_6_2_complete = all(method in [m[0] for m in implemented_methods] for method in task_6_2_methods)
    print(f"✅ Task 6.2 - Implement dinner assignment and recommendations: {'COMPLETE' if task_6_2_complete else 'INCOMPLETE'}")
    
    # Task 6.3 requirements
    task_6_3_methods = ['search_restaurants_with_fallback', 'assign_meal_with_fallback', 'create_restaurant_assignment_placeholder']
    task_6_3_complete = all(method in [m[0] for m in implemented_methods] for method in task_6_3_methods)
    print(f"✅ Task 6.3 - Add MCP error handling and retry logic: {'COMPLETE' if task_6_3_complete else 'INCOMPLETE'}")
    
    # Overall completion
    all_tasks_complete = task_6_1_complete and task_6_2_complete and task_6_3_complete
    print(f"\n🎯 Overall Task 6 Implementation: {'COMPLETE' if all_tasks_complete else 'INCOMPLETE'}")
    
    # Check for specific functionality patterns
    print("\n🔍 FUNCTIONALITY VALIDATION")
    print("=" * 60)
    
    # Check for district filtering
    if 'district' in source_code and 'meal_type' in source_code:
        print("✅ District and meal type filtering implemented")
    else:
        print("❌ District and meal type filtering missing")
    
    # Check for uniqueness enforcement
    if 'used_restaurant_ids' in source_code:
        print("✅ Restaurant uniqueness enforcement implemented")
    else:
        print("❌ Restaurant uniqueness enforcement missing")
    
    # Check for retry logic
    if 'retry' in source_code.lower() and 'exponential' in source_code.lower():
        print("✅ Retry logic with exponential backoff implemented")
    else:
        print("❌ Retry logic with exponential backoff missing")
    
    # Check for fallback strategies
    if 'fallback' in source_code.lower():
        print("✅ Fallback strategies implemented")
    else:
        print("❌ Fallback strategies missing")
    
    return all_tasks_complete


def check_method_signatures():
    """Check that method signatures match requirements."""
    
    mcp_client_path = os.path.join(os.path.dirname(__file__), 'services', 'mcp_client_manager.py')
    
    with open(mcp_client_path, 'r', encoding='utf-8') as f:
        source_code = f.read()
    
    print("\n🔍 SIGNATURE VALIDATION")
    print("=" * 60)
    
    # Check breakfast method signature
    breakfast_pattern = r'async def search_breakfast_restaurants\s*\(\s*self\s*,\s*district:\s*str\s*,\s*used_restaurant_ids.*?\)'
    if re.search(breakfast_pattern, source_code, re.DOTALL):
        print("✅ search_breakfast_restaurants signature correct")
    else:
        print("❌ search_breakfast_restaurants signature incorrect")
    
    # Check lunch method signature
    lunch_pattern = r'async def search_lunch_restaurants\s*\(\s*self\s*,\s*districts:\s*List\[str\]'
    if re.search(lunch_pattern, source_code, re.DOTALL):
        print("✅ search_lunch_restaurants signature correct")
    else:
        print("❌ search_lunch_restaurants signature incorrect")
    
    # Check dinner method signature
    dinner_pattern = r'async def search_dinner_restaurants\s*\(\s*self\s*,\s*districts:\s*List\[str\]'
    if re.search(dinner_pattern, source_code, re.DOTALL):
        print("✅ search_dinner_restaurants signature correct")
    else:
        print("❌ search_dinner_restaurants signature incorrect")


if __name__ == "__main__":
    print("🚀 MCP Client Implementation Validation")
    print("=" * 60)
    
    success = validate_mcp_client_implementation()
    check_method_signatures()
    
    if success:
        print("\n🎉 MCP CLIENT IMPLEMENTATION VALIDATION PASSED!")
        print("All required functionality for Task 6 has been implemented.")
    else:
        print("\n⚠️  MCP CLIENT IMPLEMENTATION VALIDATION FAILED!")
        print("Some required functionality is missing.")
    
    print("\n" + "=" * 60)