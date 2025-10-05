#!/usr/bin/env python3
"""
Simple test runner for integration tests that bypasses package import issues.
"""

import sys
import os
import asyncio
import unittest
from unittest.mock import AsyncMock, patch

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import test modules directly
from tests.test_comprehensive_integration import TestComprehensiveIntegration
from tests.test_mcp_protocol_integration import TestMCPProtocolIntegration
from tests.test_rest_health_integration import TestRESTHealthIntegration
from tests.test_failure_scenarios_integration import TestFailureScenariosIntegration
from tests.test_authentication_integration import TestAuthenticationIntegration
from tests.test_performance_concurrent_integration import TestPerformanceConcurrentIntegration


async def run_integration_tests():
    """Run all integration tests."""
    print("=" * 80)
    print("ENHANCED MCP STATUS CHECK - COMPREHENSIVE INTEGRATION TESTS")
    print("=" * 80)
    
    test_results = {
        'passed': 0,
        'failed': 0,
        'errors': []
    }
    
    # Test classes to run
    test_classes = [
        ('Comprehensive Integration', TestComprehensiveIntegration),
        ('MCP Protocol Integration', TestMCPProtocolIntegration),
        ('REST Health Integration', TestRESTHealthIntegration),
        ('Failure Scenarios Integration', TestFailureScenariosIntegration),
        ('Authentication Integration', TestAuthenticationIntegration),
        ('Performance Concurrent Integration', TestPerformanceConcurrentIntegration)
    ]
    
    for test_name, test_class in test_classes:
        print(f"\n{'-' * 60}")
        print(f"Running {test_name} Tests")
        print(f"{'-' * 60}")
        
        try:
            # Create test instance
            test_instance = test_class()
            
            # Get all test methods
            test_methods = [method for method in dir(test_instance) 
                          if method.startswith('test_') and callable(getattr(test_instance, method))]
            
            for method_name in test_methods:
                try:
                    print(f"  Running {method_name}...", end=" ")
                    
                    # Get the test method
                    test_method = getattr(test_instance, method_name)
                    
                    # Run the test
                    if asyncio.iscoroutinefunction(test_method):
                        await test_method()
                    else:
                        test_method()
                    
                    print("PASSED")
                    test_results['passed'] += 1
                    
                except Exception as e:
                    print(f"FAILED - {str(e)}")
                    test_results['failed'] += 1
                    test_results['errors'].append(f"{test_name}.{method_name}: {str(e)}")
                    
        except Exception as e:
            print(f"ERROR setting up {test_name}: {str(e)}")
            test_results['errors'].append(f"{test_name} setup: {str(e)}")
    
    # Print summary
    print(f"\n{'=' * 80}")
    print("TEST SUMMARY")
    print(f"{'=' * 80}")
    print(f"Total Passed: {test_results['passed']}")
    print(f"Total Failed: {test_results['failed']}")
    print(f"Total Tests: {test_results['passed'] + test_results['failed']}")
    
    if test_results['errors']:
        print(f"\nErrors ({len(test_results['errors'])}):")
        for error in test_results['errors']:
            print(f"  - {error}")
    
    return test_results['failed'] == 0


def main():
    """Main test runner."""
    try:
        success = asyncio.run(run_integration_tests())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nTests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()