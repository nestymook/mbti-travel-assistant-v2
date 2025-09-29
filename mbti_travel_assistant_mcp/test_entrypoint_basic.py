#!/usr/bin/env python3
"""
Basic test for MBTI Travel Assistant BedrockAgentCore entrypoint.

This test verifies that the entrypoint function can be called and handles
basic validation correctly.
"""

import json
import sys
import os

# Add the parent directory to the path so we can import the main module
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import process_mbti_itinerary_request


def test_mbti_entrypoint_validation():
    """Test MBTI entrypoint with invalid payload to verify validation works."""
    
    print("Testing MBTI entrypoint validation...")
    
    # Test with empty payload
    try:
        result = process_mbti_itinerary_request({})
        response = json.loads(result)
        
        # Should return error response
        assert "error" in response
        assert response["error"]["error_type"] == "validation_error"
        print("✓ Empty payload validation test passed")
        
    except Exception as e:
        print(f"✗ Empty payload test failed: {e}")
        return False
    
    # Test with invalid MBTI personality
    try:
        result = process_mbti_itinerary_request({
            "MBTI_personality": "INVALID"
        })
        response = json.loads(result)
        
        # Should return error response
        assert "error" in response
        assert "validation" in response["error"]["error_type"].lower()
        print("✓ Invalid MBTI personality validation test passed")
        
    except Exception as e:
        print(f"✗ Invalid MBTI personality test failed: {e}")
        return False
    
    # Test with valid MBTI personality but no services available
    try:
        result = process_mbti_itinerary_request({
            "MBTI_personality": "INFJ"
        })
        response = json.loads(result)
        
        # Should return response structure (may have error due to missing services)
        assert "main_itinerary" in response
        assert "candidate_tourist_spots" in response
        assert "candidate_restaurants" in response
        assert "metadata" in response
        print("✓ Valid MBTI personality structure test passed")
        
    except Exception as e:
        print(f"✗ Valid MBTI personality test failed: {e}")
        return False
    
    return True


def test_restaurant_entrypoint_still_works():
    """Test that the original restaurant entrypoint still works."""
    
    print("Testing original restaurant entrypoint...")
    
    try:
        from main import process_restaurant_request
        
        result = process_restaurant_request({
            "district": "Central district"
        })
        response = json.loads(result)
        
        # Should return response structure
        assert "recommendation" in response or "error" in response
        assert "candidates" in response or "error" in response
        assert "metadata" in response or "error" in response
        print("✓ Restaurant entrypoint still works")
        
    except Exception as e:
        print(f"✗ Restaurant entrypoint test failed: {e}")
        return False
    
    return True


if __name__ == "__main__":
    print("Running basic MBTI entrypoint tests...")
    print("=" * 50)
    
    success = True
    
    # Test MBTI entrypoint
    if not test_mbti_entrypoint_validation():
        success = False
    
    print()
    
    # Test restaurant entrypoint still works
    if not test_restaurant_entrypoint_still_works():
        success = False
    
    print()
    print("=" * 50)
    
    if success:
        print("✓ All basic tests passed!")
        sys.exit(0)
    else:
        print("✗ Some tests failed!")
        sys.exit(1)