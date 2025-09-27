#!/usr/bin/env python3
"""
Test MCP server with authentication integration.

This script tests the MCP server with authentication middleware
to ensure proper integration and error handling.
"""

import os
import sys
import json
import time
import subprocess
import requests
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_mcp_server_authentication():
    """Test MCP server authentication integration."""
    print("=" * 80)
    print("MCP SERVER AUTHENTICATION INTEGRATION TEST")
    print("=" * 80)
    print(f"Test started at: {datetime.now().isoformat()}")
    print()
    
    # Test configuration
    test_results = {
        'timestamp': datetime.now().isoformat(),
        'tests': {}
    }
    
    # Test 1: Server startup with authentication disabled
    print("Test 1: MCP Server startup with authentication disabled")
    print("-" * 60)
    
    try:
        # Set environment variable to disable authentication for testing
        env = os.environ.copy()
        env['REQUIRE_AUTHENTICATION'] = 'false'
        
        # Start MCP server in background
        print("Starting MCP server with authentication disabled...")
        
        server_process = subprocess.Popen([
            sys.executable, "restaurant_mcp_server.py"
        ], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # Give server time to start
        time.sleep(3)
        
        # Check if server is running
        if server_process.poll() is None:
            print("✓ MCP server started successfully")
            test_results['tests']['server_startup_no_auth'] = True
            
            # Test health endpoint
            try:
                response = requests.get("http://localhost:8080/health", timeout=5)
                if response.status_code == 200:
                    print("✓ Health endpoint accessible")
                    print(f"  Response: {response.json()}")
                    test_results['tests']['health_endpoint'] = True
                else:
                    print(f"✗ Health endpoint returned status {response.status_code}")
                    test_results['tests']['health_endpoint'] = False
                    
            except Exception as e:
                print(f"✗ Health endpoint test failed: {e}")
                test_results['tests']['health_endpoint'] = False
            
            # Test metrics endpoint
            try:
                response = requests.get("http://localhost:8080/metrics", timeout=5)
                if response.status_code == 200:
                    print("✓ Metrics endpoint accessible")
                    print(f"  Response: {response.json()}")
                    test_results['tests']['metrics_endpoint'] = True
                else:
                    print(f"✗ Metrics endpoint returned status {response.status_code}")
                    test_results['tests']['metrics_endpoint'] = False
                    
            except Exception as e:
                print(f"✗ Metrics endpoint test failed: {e}")
                test_results['tests']['metrics_endpoint'] = False
        
        else:
            print("✗ MCP server failed to start")
            stdout, stderr = server_process.communicate()
            print(f"STDOUT: {stdout}")
            print(f"STDERR: {stderr}")
            test_results['tests']['server_startup_no_auth'] = False
        
        # Cleanup
        if server_process.poll() is None:
            server_process.terminate()
            server_process.wait(timeout=5)
            print("✓ MCP server stopped")
        
    except Exception as e:
        print(f"✗ Server startup test failed: {e}")
        test_results['tests']['server_startup_no_auth'] = False
    
    print()
    
    # Test 2: Server startup with authentication enabled
    print("Test 2: MCP Server startup with authentication enabled")
    print("-" * 60)
    
    try:
        # Set environment variable to enable authentication
        env = os.environ.copy()
        env['REQUIRE_AUTHENTICATION'] = 'true'
        
        # Start MCP server in background
        print("Starting MCP server with authentication enabled...")
        
        server_process = subprocess.Popen([
            sys.executable, "restaurant_mcp_server.py"
        ], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # Give server time to start
        time.sleep(3)
        
        # Check if server is running
        if server_process.poll() is None:
            print("✓ MCP server started successfully with authentication")
            test_results['tests']['server_startup_with_auth'] = True
            
            # Test health endpoint (should still work - bypass authentication)
            try:
                response = requests.get("http://localhost:8080/health", timeout=5)
                if response.status_code == 200:
                    print("✓ Health endpoint accessible (bypasses authentication)")
                    test_results['tests']['health_endpoint_bypass'] = True
                else:
                    print(f"✗ Health endpoint returned status {response.status_code}")
                    test_results['tests']['health_endpoint_bypass'] = False
                    
            except Exception as e:
                print(f"✗ Health endpoint test failed: {e}")
                test_results['tests']['health_endpoint_bypass'] = False
            
            # Test protected endpoint without authentication (should fail)
            try:
                # Try to access a protected endpoint without auth
                response = requests.post("http://localhost:8080/", 
                                       json={"method": "tools/list"}, 
                                       timeout=5)
                
                if response.status_code == 401:
                    print("✓ Protected endpoint correctly requires authentication")
                    test_results['tests']['auth_required'] = True
                else:
                    print(f"⚠ Protected endpoint returned unexpected status {response.status_code}")
                    test_results['tests']['auth_required'] = False
                    
            except Exception as e:
                print(f"⚠ Protected endpoint test failed: {e}")
                test_results['tests']['auth_required'] = False
        
        else:
            print("✗ MCP server failed to start with authentication")
            stdout, stderr = server_process.communicate()
            print(f"STDOUT: {stdout}")
            print(f"STDERR: {stderr}")
            test_results['tests']['server_startup_with_auth'] = False
        
        # Cleanup
        if server_process.poll() is None:
            server_process.terminate()
            server_process.wait(timeout=5)
            print("✓ MCP server stopped")
        
    except Exception as e:
        print(f"✗ Server startup with auth test failed: {e}")
        test_results['tests']['server_startup_with_auth'] = False
    
    print()
    
    # Test 3: Authentication middleware components
    print("Test 3: Authentication middleware components")
    print("-" * 60)
    
    try:
        from services.auth_middleware import (
            AuthenticationConfig, 
            create_authentication_middleware,
            AuthenticationHelper
        )
        
        # Test configuration creation
        test_config = {
            'user_pool_id': 'us-east-1_test123',
            'client_id': 'test-client-id',
            'region': 'us-east-1',
            'discovery_url': 'https://test.example.com/.well-known/openid-configuration'
        }
        
        config = AuthenticationConfig(
            cognito_config=test_config,
            bypass_paths=['/health', '/metrics'],
            require_authentication=True
        )
        
        print("✓ AuthenticationConfig created successfully")
        test_results['tests']['auth_config_creation'] = True
        
        # Test middleware factory
        middleware_factory = create_authentication_middleware(
            cognito_config=test_config,
            bypass_paths=['/health', '/metrics'],
            require_authentication=True
        )
        
        print("✓ Authentication middleware factory created successfully")
        test_results['tests']['middleware_factory_creation'] = True
        
    except Exception as e:
        print(f"✗ Authentication middleware component test failed: {e}")
        test_results['tests']['auth_config_creation'] = False
        test_results['tests']['middleware_factory_creation'] = False
    
    # Save test results
    results_dir = os.path.join(os.path.dirname(__file__), "results")
    os.makedirs(results_dir, exist_ok=True)
    
    results_file = os.path.join(results_dir, f"mcp_server_auth_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    
    try:
        with open(results_file, 'w') as f:
            json.dump(test_results, f, indent=2)
        
        print(f"✓ Test results saved to: {results_file}")
        
    except Exception as e:
        print(f"⚠ Could not save test results: {e}")
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    passed_tests = sum(1 for result in test_results['tests'].values() if result)
    total_tests = len(test_results['tests'])
    
    print(f"Tests passed: {passed_tests}/{total_tests}")
    
    if passed_tests == total_tests:
        print("✓ All MCP server authentication tests PASSED")
        return True
    else:
        print("✗ Some MCP server authentication tests FAILED")
        for test_name, result in test_results['tests'].items():
            status = "✓" if result else "✗"
            print(f"  {status} {test_name}")
        return False


if __name__ == "__main__":
    success = test_mcp_server_authentication()
    sys.exit(0 if success else 1)