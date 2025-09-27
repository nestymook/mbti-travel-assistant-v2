#!/usr/bin/env python3
"""
Quick test script to verify MCP tools work correctly.
"""

import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(__file__))

from src.restaurant_mcp_server import (
    search_restaurants_by_district,
    search_restaurants_by_meal_type,
    search_restaurants_combined
)

def test_mcp_tools():
    """Test the MCP tools to ensure they work correctly."""
    
    print("Testing MCP Tools...")
    print("=" * 50)
    
    # Test 1: Search by district
    print("\n1. Testing search_restaurants_by_district:")
    try:
        result = search_restaurants_by_district(["Central district"])
        print(f"✅ District search successful - found data")
        print(f"Response length: {len(result)} characters")
    except Exception as e:
        print(f"❌ District search failed: {e}")
    
    # Test 2: Search by meal type
    print("\n2. Testing search_restaurants_by_meal_type:")
    try:
        result = search_restaurants_by_meal_type(["lunch"])
        print(f"✅ Meal type search successful - found data")
        print(f"Response length: {len(result)} characters")
    except Exception as e:
        print(f"❌ Meal type search failed: {e}")
    
    # Test 3: Combined search
    print("\n3. Testing search_restaurants_combined:")
    try:
        result = search_restaurants_combined(
            districts=["Central district"], 
            meal_types=["lunch"]
        )
        print(f"✅ Combined search successful - found data")
        print(f"Response length: {len(result)} characters")
    except Exception as e:
        print(f"❌ Combined search failed: {e}")
    
    print("\n" + "=" * 50)
    print("MCP Tools test completed!")

if __name__ == "__main__":
    test_mcp_tools()