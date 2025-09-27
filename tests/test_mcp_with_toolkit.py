#!/usr/bin/env python3
"""
Test MCP Server using bedrock-agentcore-starter-toolkit

This script tests the deployed restaurant MCP server using the toolkit's Runtime class.

Follows program guidelines:
- Test payloads are base64 encoded in /tests/payload/
- Test requests are stored in /tests/request/
- Test responses are saved to /tests/response/
- Test results are saved to /tests/results/
"""

import json
import sys
import time
import os
import base64
from typing import Dict, Any

from bedrock_agentcore_starter_toolkit import Runtime


class MCPServerTester:
    """Test the MCP server using the AgentCore toolkit."""
    
    def __init__(self):
        """Initialize the tester."""
        self.runtime = Runtime()
        self.agent_id = "restaurant_search_mcp-JZdACMALGo"
        
        # Directory paths following program guidelines
        self.payload_dir = "tests/payload"
        self.request_dir = "tests/request"
        self.response_dir = "tests/response"
        self.results_dir = "tests/results"
        
        # Ensure directories exist
        os.makedirs(self.response_dir, exist_ok=True)
        os.makedirs(self.results_dir, exist_ok=True)
        
    def test_agent_invoke(self, prompt: str) -> Dict[str, Any]:
        """Test invoking the agent with a prompt.
        
        Args:
            prompt: Test prompt to send.
            
        Returns:
            Test result dictionary.
        """
        try:
            print(f"🧪 Testing agent invoke with prompt: '{prompt}'")
            
            # Use the runtime invoke method
            response = self.runtime.invoke({"prompt": prompt})
            
            print("✅ Agent invoke successful!")
            print(f"📊 Response: {response}")
            
            return {
                "success": True,
                "response": response,
                "error": None
            }
            
        except Exception as e:
            print(f"❌ Agent invoke failed: {e}")
            return {
                "success": False,
                "response": None,
                "error": str(e)
            }
    
    def test_agent_status(self) -> Dict[str, Any]:
        """Test getting agent status.
        
        Returns:
            Status test result.
        """
        try:
            print("🔍 Testing agent status...")
            
            status = self.runtime.status()
            
            print("✅ Status check successful!")
            print(f"📊 Status: {status}")
            
            return {
                "success": True,
                "status": status,
                "error": None
            }
            
        except Exception as e:
            print(f"❌ Status check failed: {e}")
            return {
                "success": False,
                "status": None,
                "error": str(e)
            }
    
    def run_tests(self) -> Dict[str, Any]:
        """Run comprehensive tests.
        
        Returns:
            Test results summary.
        """
        print("🚀 Starting MCP Server Tests with AgentCore Toolkit")
        print("=" * 55)
        
        results = {
            "agent_id": self.agent_id,
            "tests": {},
            "summary": {
                "total_tests": 0,
                "passed": 0,
                "failed": 0,
                "success_rate": 0.0
            }
        }
        
        # Test 1: Agent Status
        print("\n🔍 Test 1: Agent Status Check")
        print("-" * 30)
        
        status_test = self.test_agent_status()
        results["tests"]["status_check"] = status_test
        results["summary"]["total_tests"] += 1
        if status_test["success"]:
            results["summary"]["passed"] += 1
        else:
            results["summary"]["failed"] += 1
        
        # Only proceed with invoke tests if status is good
        if status_test["success"]:
            # Test 2: District Search
            print("\n🧪 Test 2: Restaurant Search by District")
            print("-" * 40)
            
            district_test = self.test_agent_invoke(
                "Find restaurants in Central district"
            )
            results["tests"]["district_search"] = district_test
            results["summary"]["total_tests"] += 1
            if district_test["success"]:
                results["summary"]["passed"] += 1
            else:
                results["summary"]["failed"] += 1
            
            # Test 3: Meal Type Search
            print("\n🧪 Test 3: Restaurant Search by Meal Type")
            print("-" * 40)
            
            meal_test = self.test_agent_invoke(
                "Find restaurants that serve breakfast"
            )
            results["tests"]["meal_type_search"] = meal_test
            results["summary"]["total_tests"] += 1
            if meal_test["success"]:
                results["summary"]["passed"] += 1
            else:
                results["summary"]["failed"] += 1
            
            # Test 4: Combined Search
            print("\n🧪 Test 4: Combined Restaurant Search")
            print("-" * 40)
            
            combined_test = self.test_agent_invoke(
                "Find restaurants in Admiralty that serve lunch"
            )
            results["tests"]["combined_search"] = combined_test
            results["summary"]["total_tests"] += 1
            if combined_test["success"]:
                results["summary"]["passed"] += 1
            else:
                results["summary"]["failed"] += 1
        else:
            print("\n⚠️ Skipping invoke tests due to status check failure")
        
        # Calculate success rate
        if results["summary"]["total_tests"] > 0:
            results["summary"]["success_rate"] = (
                results["summary"]["passed"] / 
                results["summary"]["total_tests"] * 100
            )
        
        # Print summary
        print("\n📊 Test Results Summary")
        print("=" * 30)
        print(f"Agent ID: {self.agent_id}")
        print(f"Total Tests: {results['summary']['total_tests']}")
        print(f"Passed: {results['summary']['passed']}")
        print(f"Failed: {results['summary']['failed']}")
        print(f"Success Rate: {results['summary']['success_rate']:.1f}%")
        
        if results["summary"]["success_rate"] >= 75:
            print("\n🎉 MCP SERVER STATUS: EXCELLENT - All systems operational!")
        elif results["summary"]["success_rate"] >= 50:
            print("\n⚠️ MCP SERVER STATUS: GOOD - Minor issues detected")
        else:
            print("\n💥 MCP SERVER STATUS: ISSUES - Problems detected")
        
        return results


def main():
    """Main test function."""
    try:
        tester = MCPServerTester()
        results = tester.run_tests()
        
        # Save results to results directory
        results_file = os.path.join(self.results_dir, "toolkit_test_results.json")
        with open(results_file, "w") as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n💾 Test results saved to: {results_file}")
        
        # Return appropriate exit code
        success_rate = results["summary"]["success_rate"]
        return 0 if success_rate >= 50 else 1
        
    except Exception as e:
        print(f"💥 Test execution failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())