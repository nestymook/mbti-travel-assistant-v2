#!/usr/bin/env python3
"""
Verification script for reasoning endpoints implementation.

This script verifies that the restaurant reasoning endpoints are properly
implemented and registered in the FastAPI application.
"""

import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import app
from fastapi.routing import APIRoute


def verify_reasoning_endpoints():
    """Verify that the reasoning endpoints are properly registered."""
    
    print("🔍 Verifying AgentCore Gateway reasoning endpoints...")
    print("=" * 60)
    
    # Get all routes from the FastAPI app
    routes = []
    for route in app.routes:
        if isinstance(route, APIRoute):
            routes.append({
                'path': route.path,
                'methods': list(route.methods),
                'name': route.name
            })
    
    # Check for reasoning endpoints
    reasoning_endpoints = [
        {
            'path': '/api/v1/restaurants/recommend',
            'method': 'POST',
            'description': 'Restaurant recommendation endpoint'
        },
        {
            'path': '/api/v1/restaurants/analyze', 
            'method': 'POST',
            'description': 'Restaurant sentiment analysis endpoint'
        }
    ]
    
    print("📋 Checking for reasoning endpoints:")
    print("-" * 40)
    
    all_found = True
    
    for endpoint in reasoning_endpoints:
        found = False
        for route in routes:
            if route['path'] == endpoint['path'] and endpoint['method'] in route['methods']:
                found = True
                print(f"✅ {endpoint['method']} {endpoint['path']} - {endpoint['description']}")
                break
        
        if not found:
            print(f"❌ {endpoint['method']} {endpoint['path']} - {endpoint['description']} (NOT FOUND)")
            all_found = False
    
    print("\n📊 All registered API routes:")
    print("-" * 40)
    
    # Sort routes by path for better readability
    sorted_routes = sorted(routes, key=lambda x: x['path'])
    
    for route in sorted_routes:
        methods_str = ', '.join(sorted(route['methods']))
        print(f"  {methods_str:<10} {route['path']}")
    
    print(f"\n📈 Summary:")
    print(f"  Total routes: {len(routes)}")
    print(f"  Reasoning endpoints found: {'✅ All found' if all_found else '❌ Some missing'}")
    
    if all_found:
        print("\n🎉 SUCCESS: All reasoning endpoints are properly implemented!")
        return True
    else:
        print("\n❌ FAILURE: Some reasoning endpoints are missing!")
        return False


if __name__ == "__main__":
    success = verify_reasoning_endpoints()
    sys.exit(0 if success else 1)