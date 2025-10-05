#!/usr/bin/env python3
"""
Validation script for integration tests.
Checks that all required test methods are implemented and properly structured.
"""

import os
import ast
import sys
from typing import Dict, List, Set


def analyze_test_file(file_path: str) -> Dict[str, List[str]]:
    """Analyze a test file and extract test methods."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    try:
        tree = ast.parse(content)
    except SyntaxError as e:
        print(f"Syntax error in {file_path}: {e}")
        return {}
    
    test_methods = {}
    
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name.startswith('Test'):
            class_methods = []
            for item in node.body:
                if isinstance(item, ast.AsyncFunctionDef) and item.name.startswith('test_'):
                    class_methods.append(item.name)
                elif isinstance(item, ast.FunctionDef) and item.name.startswith('test_'):
                    class_methods.append(item.name)
            
            if class_methods:
                test_methods[node.name] = class_methods
    
    return test_methods


def validate_integration_tests():
    """Validate all integration test files."""
    print("=" * 80)
    print("INTEGRATION TESTS VALIDATION")
    print("=" * 80)
    
    # Define required test coverage
    required_coverage = {
        'test_comprehensive_integration.py': {
            'TestComprehensiveIntegration': [
                'test_end_to_end_dual_health_check_flow_success',
                'test_mcp_tools_list_request_validation',
                'test_rest_health_check_request_response_handling',
                'test_failure_scenario_mcp_fails_rest_succeeds',
                'test_failure_scenario_rest_fails_mcp_succeeds',
                'test_failure_scenario_both_fail',
                'test_authentication_integration_mcp_jwt',
                'test_authentication_integration_rest_bearer_token',
                'test_authentication_failure_scenarios',
                'test_concurrent_dual_monitoring_performance',
                'test_concurrent_monitoring_with_mixed_failures'
            ]
        },
        'test_mcp_protocol_integration.py': {
            'TestMCPProtocolIntegration': [
                'test_mcp_tools_list_request_generation',
                'test_mcp_tools_list_response_validation_success',
                'test_mcp_tools_list_response_validation_missing_tools',
                'test_mcp_jsonrpc_error_response_handling',
                'test_mcp_authentication_header_inclusion'
            ]
        },
        'test_rest_health_integration.py': {
            'TestRESTHealthIntegration': [
                'test_rest_health_request_generation',
                'test_rest_health_response_validation_success',
                'test_rest_health_http_status_code_handling',
                'test_rest_health_authentication_headers',
                'test_rest_health_retry_logic_with_exponential_backoff'
            ]
        },
        'test_failure_scenarios_integration.py': {
            'TestFailureScenariosIntegration': [
                'test_mcp_timeout_rest_success_scenario',
                'test_rest_timeout_mcp_success_scenario',
                'test_both_timeout_scenario',
                'test_mcp_authentication_failure_rest_success',
                'test_cascading_failure_scenario'
            ]
        },
        'test_authentication_integration.py': {
            'TestAuthenticationIntegration': [
                'test_jwt_authentication_mcp_success',
                'test_jwt_authentication_rest_success',
                'test_bearer_token_authentication_integration',
                'test_jwt_token_validation_failure',
                'test_jwt_token_expiration_and_refresh'
            ]
        },
        'test_performance_concurrent_integration.py': {
            'TestPerformanceConcurrentIntegration': [
                'test_concurrent_dual_monitoring_basic_performance',
                'test_concurrent_monitoring_resource_management',
                'test_concurrent_monitoring_with_mixed_response_times',
                'test_concurrent_monitoring_failure_isolation',
                'test_concurrent_monitoring_timeout_handling'
            ]
        }
    }
    
    tests_dir = os.path.join(os.path.dirname(__file__), 'tests')
    validation_results = {
        'total_files': 0,
        'valid_files': 0,
        'total_tests': 0,
        'missing_tests': [],
        'extra_tests': [],
        'errors': []
    }
    
    for test_file, expected_classes in required_coverage.items():
        file_path = os.path.join(tests_dir, test_file)
        validation_results['total_files'] += 1
        
        print(f"\nValidating {test_file}...")
        
        if not os.path.exists(file_path):
            validation_results['errors'].append(f"Missing test file: {test_file}")
            continue
        
        try:
            actual_methods = analyze_test_file(file_path)
            
            for class_name, expected_methods in expected_classes.items():
                if class_name not in actual_methods:
                    validation_results['errors'].append(f"Missing test class: {class_name} in {test_file}")
                    continue
                
                actual_methods_set = set(actual_methods[class_name])
                expected_methods_set = set(expected_methods)
                
                # Check for missing methods
                missing = expected_methods_set - actual_methods_set
                if missing:
                    validation_results['missing_tests'].extend([f"{class_name}.{method}" for method in missing])
                
                # Check for extra methods (not necessarily bad, but worth noting)
                extra = actual_methods_set - expected_methods_set
                if extra:
                    validation_results['extra_tests'].extend([f"{class_name}.{method}" for method in extra])
                
                validation_results['total_tests'] += len(actual_methods_set)
                
                print(f"  {class_name}: {len(actual_methods_set)} test methods")
                if missing:
                    print(f"    Missing: {', '.join(missing)}")
                if extra:
                    print(f"    Extra: {', '.join(extra)}")
            
            validation_results['valid_files'] += 1
            
        except Exception as e:
            validation_results['errors'].append(f"Error analyzing {test_file}: {str(e)}")
    
    # Print summary
    print(f"\n{'=' * 80}")
    print("VALIDATION SUMMARY")
    print(f"{'=' * 80}")
    print(f"Files validated: {validation_results['valid_files']}/{validation_results['total_files']}")
    print(f"Total test methods found: {validation_results['total_tests']}")
    print(f"Missing tests: {len(validation_results['missing_tests'])}")
    print(f"Extra tests: {len(validation_results['extra_tests'])}")
    print(f"Errors: {len(validation_results['errors'])}")
    
    if validation_results['missing_tests']:
        print(f"\nMissing Tests:")
        for test in validation_results['missing_tests']:
            print(f"  - {test}")
    
    if validation_results['extra_tests']:
        print(f"\nExtra Tests (not required but present):")
        for test in validation_results['extra_tests']:
            print(f"  + {test}")
    
    if validation_results['errors']:
        print(f"\nErrors:")
        for error in validation_results['errors']:
            print(f"  ! {error}")
    
    # Check requirements coverage
    print(f"\n{'=' * 80}")
    print("REQUIREMENTS COVERAGE ANALYSIS")
    print(f"{'=' * 80}")
    
    requirements_coverage = {
        '1.1': 'MCP tools/list request generation and handling',
        '1.2': 'MCP tools/list response validation',
        '2.1': 'REST health check request generation and handling',
        '2.2': 'REST health check response validation',
        '3.1': 'Dual health check result aggregation',
        '3.2': 'Combined status determination and metrics',
        '9.1': 'MCP authentication integration',
        '9.2': 'REST authentication integration'
    }
    
    print("Requirements coverage by test files:")
    for req_id, description in requirements_coverage.items():
        print(f"  {req_id}: {description}")
        # Count test files that cover this requirement
        covering_files = []
        for test_file in required_coverage.keys():
            file_path = os.path.join(tests_dir, test_file)
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if f"Requirements: {req_id}" in content or f"Requirements covered: {req_id}" in content:
                        covering_files.append(test_file)
        
        if covering_files:
            print(f"    Covered by: {', '.join(covering_files)}")
        else:
            print(f"    ⚠️  No explicit coverage found")
    
    return len(validation_results['errors']) == 0 and len(validation_results['missing_tests']) == 0


def main():
    """Main validation function."""
    try:
        success = validate_integration_tests()
        print(f"\n{'=' * 80}")
        if success:
            print("✅ VALIDATION PASSED - All integration tests are properly structured")
        else:
            print("❌ VALIDATION FAILED - Issues found in integration tests")
        print(f"{'=' * 80}")
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"Validation error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()