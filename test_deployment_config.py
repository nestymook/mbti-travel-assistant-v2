#!/usr/bin/env python3
"""
Test Deployment Configuration for Restaurant Search MCP

This script tests the deployment configuration without actually deploying
to verify that all components are properly configured.

Requirements: 5.1, 5.2, 5.3, 8.1, 8.2, 8.3
"""

import json
import os
import sys
import time
from typing import Dict, Any, List


def test_file_exists(file_path: str, description: str) -> bool:
    """Test if a required file exists.
    
    Args:
        file_path: Path to the file to check.
        description: Description of the file for error messages.
        
    Returns:
        True if file exists, False otherwise.
    """
    if os.path.exists(file_path):
        print(f"✓ {description}: {file_path}")
        return True
    else:
        print(f"✗ {description} missing: {file_path}")
        return False


def test_python_imports() -> bool:
    """Test that required Python packages can be imported.
    
    Returns:
        True if all imports succeed, False otherwise.
    """
    print("\n🐍 Testing Python Package Imports:")
    
    required_packages = [
        ('mcp', 'Model Context Protocol'),
        ('boto3', 'AWS SDK'),
        ('bedrock_agentcore_starter_toolkit', 'AgentCore Starter Toolkit')
    ]
    
    all_imports_ok = True
    
    for package_name, description in required_packages:
        try:
            __import__(package_name)
            print(f"✓ {description}: {package_name}")
        except ImportError:
            print(f"✗ {description} not available: {package_name}")
            all_imports_ok = False
    
    return all_imports_ok


def test_mcp_server_syntax() -> bool:
    """Test that the MCP server file has valid Python syntax.
    
    Returns:
        True if syntax is valid, False otherwise.
    """
    print("\n📝 Testing MCP Server Syntax:")
    
    try:
        with open('restaurant_mcp_server.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Compile to check syntax
        compile(content, 'restaurant_mcp_server.py', 'exec')
        print("✓ MCP server syntax is valid")
        return True
        
    except SyntaxError as e:
        print(f"✗ Syntax error in MCP server: {e}")
        return False
    except FileNotFoundError:
        print("✗ MCP server file not found: restaurant_mcp_server.py")
        return False
    except Exception as e:
        print(f"✗ Error checking MCP server syntax: {e}")
        return False


def test_requirements_file() -> bool:
    """Test that requirements.txt contains necessary dependencies.
    
    Returns:
        True if requirements are valid, False otherwise.
    """
    print("\n📦 Testing Requirements File:")
    
    try:
        with open('requirements.txt', 'r', encoding='utf-8') as f:
            requirements = f.read().strip().split('\n')
        
        required_packages = [
            'mcp',
            'boto3',
            'bedrock-agentcore',
            'bedrock-agentcore-starter-toolkit'
        ]
        
        missing_packages = []
        for package in required_packages:
            found = any(package in req for req in requirements)
            if found:
                print(f"✓ Required package found: {package}")
            else:
                print(f"✗ Required package missing: {package}")
                missing_packages.append(package)
        
        return len(missing_packages) == 0
        
    except FileNotFoundError:
        print("✗ Requirements file not found: requirements.txt")
        return False
    except Exception as e:
        print(f"✗ Error checking requirements: {e}")
        return False


def test_deployment_scripts() -> bool:
    """Test that deployment scripts have valid syntax.
    
    Returns:
        True if all scripts are valid, False otherwise.
    """
    print("\n🚀 Testing Deployment Scripts:")
    
    scripts = [
        ('deploy_agentcore.py', 'AgentCore deployment script'),
        ('execute_deployment.py', 'Deployment execution script'),
        ('setup_cognito.py', 'Cognito setup script')
    ]
    
    all_scripts_ok = True
    
    for script_path, description in scripts:
        try:
            with open(script_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Compile to check syntax
            compile(content, script_path, 'exec')
            print(f"✓ {description} syntax is valid")
            
        except SyntaxError as e:
            print(f"✗ Syntax error in {description}: {e}")
            all_scripts_ok = False
        except FileNotFoundError:
            print(f"✗ {description} not found: {script_path}")
            all_scripts_ok = False
        except Exception as e:
            print(f"✗ Error checking {description}: {e}")
            all_scripts_ok = False
    
    return all_scripts_ok


def test_mcp_tools_configuration() -> bool:
    """Test that MCP tools are properly configured in the server.
    
    Returns:
        True if MCP tools are configured, False otherwise.
    """
    print("\n🔧 Testing MCP Tools Configuration:")
    
    try:
        with open('restaurant_mcp_server.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for required MCP tool decorators
        required_tools = [
            'search_restaurants_by_district',
            'search_restaurants_by_meal_type',
            'search_restaurants_combined'
        ]
        
        all_tools_found = True
        for tool_name in required_tools:
            if f'def {tool_name}' in content and '@mcp.tool()' in content:
                print(f"✓ MCP tool found: {tool_name}")
            else:
                print(f"✗ MCP tool missing or not decorated: {tool_name}")
                all_tools_found = False
        
        # Check for FastMCP configuration
        if 'FastMCP(' in content and 'stateless_http=True' in content:
            print("✓ FastMCP configured with stateless_http=True")
        else:
            print("✗ FastMCP not properly configured")
            all_tools_found = False
        
        # Check for protocol configuration
        if 'transport="streamable-http"' in content:
            print("✓ Streamable HTTP transport configured")
        else:
            print("✗ Streamable HTTP transport not configured")
            all_tools_found = False
        
        return all_tools_found
        
    except Exception as e:
        print(f"✗ Error checking MCP tools configuration: {e}")
        return False


def test_config_directory_structure() -> bool:
    """Test that configuration directory structure is correct.
    
    Returns:
        True if structure is correct, False otherwise.
    """
    print("\n📁 Testing Configuration Directory Structure:")
    
    required_dirs = [
        'config',
        'config/districts',
        'config/restaurants'
    ]
    
    required_files = [
        'config/districts/master-config.json',
        'config/districts/hong-kong-island.json',
        'config/districts/kowloon.json',
        'config/districts/new-territories.json',
        'config/districts/lantau.json'
    ]
    
    all_structure_ok = True
    
    # Check directories
    for dir_path in required_dirs:
        if os.path.isdir(dir_path):
            print(f"✓ Directory exists: {dir_path}")
        else:
            print(f"✗ Directory missing: {dir_path}")
            all_structure_ok = False
    
    # Check configuration files
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✓ Config file exists: {file_path}")
        else:
            print(f"✗ Config file missing: {file_path}")
            all_structure_ok = False
    
    return all_structure_ok


def generate_deployment_readiness_report() -> Dict[str, Any]:
    """Generate a comprehensive deployment readiness report.
    
    Returns:
        Dictionary containing test results and readiness status.
    """
    print("🔍 Restaurant Search MCP - Deployment Readiness Test")
    print("=" * 60)
    
    # Run all tests
    tests = [
        ("Required Files", lambda: all([
            test_file_exists('restaurant_mcp_server.py', 'MCP Server'),
            test_file_exists('requirements.txt', 'Requirements File'),
            test_file_exists('deploy_agentcore.py', 'Deployment Script'),
            test_file_exists('execute_deployment.py', 'Execution Script'),
            test_file_exists('setup_cognito.py', 'Cognito Setup Script')
        ])),
        ("Python Imports", test_python_imports),
        ("MCP Server Syntax", test_mcp_server_syntax),
        ("Requirements File", test_requirements_file),
        ("Deployment Scripts", test_deployment_scripts),
        ("MCP Tools Configuration", test_mcp_tools_configuration),
        ("Config Directory Structure", test_config_directory_structure)
    ]
    
    results = {}
    all_tests_passed = True
    
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        try:
            result = test_func()
            results[test_name] = result
            if not result:
                all_tests_passed = False
        except Exception as e:
            print(f"✗ Test failed with exception: {e}")
            results[test_name] = False
            all_tests_passed = False
    
    # Generate summary
    print("\n" + "=" * 60)
    print("📊 DEPLOYMENT READINESS SUMMARY")
    print("=" * 60)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:.<30} {status}")
    
    overall_status = "✅ READY FOR DEPLOYMENT" if all_tests_passed else "❌ NOT READY"
    print(f"\nOverall Status: {overall_status}")
    
    if all_tests_passed:
        print("\n🎉 All tests passed! The MCP server is ready for deployment.")
        print("\n📋 Next Steps:")
        print("1. Ensure AWS credentials are configured: aws configure")
        print("2. Run Cognito setup: python setup_cognito.py")
        print("3. Execute deployment: python execute_deployment.py")
    else:
        print("\n⚠️ Some tests failed. Please address the issues before deployment.")
        print("\n🔧 Common Solutions:")
        print("- Install missing packages: pip install -r requirements.txt")
        print("- Fix syntax errors in Python files")
        print("- Ensure all required files are present")
        print("- Check configuration directory structure")
    
    return {
        'overall_ready': all_tests_passed,
        'test_results': results,
        'timestamp': time.time()
    }


def main():
    """Main function to run deployment readiness tests."""
    try:
        import time
        
        # Generate readiness report
        report = generate_deployment_readiness_report()
        
        # Save report to file
        with open('deployment_readiness_report.json', 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"\n📄 Readiness report saved to: deployment_readiness_report.json")
        
        return 0 if report['overall_ready'] else 1
        
    except Exception as e:
        print(f"\n💥 Test execution failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())