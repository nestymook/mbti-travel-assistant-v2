#!/usr/bin/env python3
"""
AWS Test Runner for Restaurant Reasoning MCP Server.

This script provides options to run different types of tests against the AWS-deployed instance.
"""

import asyncio
import sys
from pathlib import Path

def print_menu():
    """Print the test menu."""
    print("\n🧪 AWS Restaurant Reasoning MCP Server - Test Menu")
    print("=" * 60)
    print("1. 🔧 Comprehensive AWS Deployment Tests")
    print("   - Full deployment validation")
    print("   - JWT authentication testing")
    print("   - Performance and error handling")
    print("   - Detailed reporting")
    print()
    print("2. 🎯 Direct MCP Tools Testing")
    print("   - Quick MCP tool validation")
    print("   - JWT authentication")
    print("   - Tool functionality testing")
    print("   - Focused on core features")
    print()
    print("3. ❌ Exit")
    print("=" * 60)

async def run_comprehensive_tests():
    """Run comprehensive AWS deployment tests."""
    print("\n🚀 Running Comprehensive AWS Deployment Tests...")
    print("This will test all aspects of the AWS deployment including authentication,")
    print("connectivity, performance, and error handling.\n")
    
    try:
        # Import and run comprehensive tests
        from test_aws_deployment_comprehensive import AWSDeploymentTester
        
        tester = AWSDeploymentTester()
        results = await tester.run_comprehensive_tests()
        
        # Print results summary
        summary = results.get("summary", {})
        print(f"\n📊 Comprehensive Test Results:")
        print(f"   Total Tests: {summary.get('total_tests', 0)}")
        print(f"   Passed: {summary.get('passed_tests', 0)} ✅")
        print(f"   Failed: {summary.get('failed_tests', 0)} ❌")
        print(f"   Success Rate: {summary.get('success_rate_percent', 0):.1f}%")
        print(f"   Overall Status: {summary.get('overall_status', 'UNKNOWN')}")
        
        # Save results
        tester.save_results("comprehensive_aws_test_results.json")
        
        return summary.get('overall_status') == "SUCCESS"
        
    except Exception as e:
        print(f"❌ Comprehensive tests failed: {e}")
        return False

async def run_direct_mcp_tests():
    """Run direct MCP tools tests."""
    print("\n🎯 Running Direct MCP Tools Tests...")
    print("This will test the MCP tools directly with JWT authentication.\n")
    
    try:
        # Import and run direct MCP tests
        from test_aws_mcp_tools_direct import MCPToolsTester
        
        tester = MCPToolsTester()
        results = await tester.run_all_tests()
        
        # Print results summary
        summary = results.get("summary", {})
        print(f"\n📊 MCP Tools Test Results:")
        print(f"   Total Tests: {summary.get('total_tests', 0)}")
        print(f"   Passed: {summary.get('passed_tests', 0)} ✅")
        print(f"   Failed: {summary.get('failed_tests', 0)} ❌")
        print(f"   Success Rate: {summary.get('success_rate', 0):.1f}%")
        print(f"   Overall Status: {summary.get('overall_status', 'UNKNOWN')}")
        
        # Save results
        tester.save_results(results, "direct_mcp_test_results.json")
        
        return summary.get('overall_status') == "SUCCESS"
        
    except Exception as e:
        print(f"❌ Direct MCP tests failed: {e}")
        return False

async def main():
    """Main menu and test execution."""
    print("🍽️ Restaurant Reasoning MCP Server - AWS Testing Suite")
    print("Testing AWS-deployed instance with JWT authentication")
    
    while True:
        print_menu()
        
        try:
            choice = input("Select test option (1-3): ").strip()
            
            if choice == "1":
                success = await run_comprehensive_tests()
                if success:
                    print("\n🎉 Comprehensive tests completed successfully!")
                else:
                    print("\n⚠️ Some comprehensive tests failed. Check the results for details.")
                
                input("\nPress Enter to continue...")
                
            elif choice == "2":
                success = await run_direct_mcp_tests()
                if success:
                    print("\n🎉 Direct MCP tests completed successfully!")
                else:
                    print("\n⚠️ Some MCP tests failed. Check the results for details.")
                
                input("\nPress Enter to continue...")
                
            elif choice == "3":
                print("\n👋 Goodbye!")
                break
                
            else:
                print("\n❌ Invalid choice. Please select 1, 2, or 3.")
                input("Press Enter to continue...")
                
        except KeyboardInterrupt:
            print("\n\n👋 Test interrupted by user. Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            input("Press Enter to continue...")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        sys.exit(0)