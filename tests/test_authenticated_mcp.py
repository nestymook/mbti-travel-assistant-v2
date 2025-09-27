#!/usr/bin/env python3
"""
Test Authenticated MCP Server Deployment in AWS

This script tests the deployed restaurant MCP server with Cognito authentication
using the AgentCore invoke command.

Follows program guidelines:
- Test payloads are base64 encoded in /tests/payload/
- Test requests are stored in /tests/request/
- Test responses are saved to /tests/response/
- Test results are saved to /tests/results/
"""

import json
import subprocess
import time
import sys
import base64
import os
from typing import Dict, Any, Optional


class AuthenticatedMCPTester:
    """Test the authenticated MCP server deployment."""
    
    def __init__(self):
        """Initialize the tester with agent configuration."""
        self.agent_id = "restaurant_search_mcp-JZdACMALGo"
        self.agent_arn = f"arn:aws:bedrock-agentcore:us-east-1:209803798463:runtime/{self.agent_id}"
        self.region = "us-east-1"
        
        # Directory paths following program guidelines
        self.payload_dir = "tests/payload"
        self.request_dir = "tests/request"
        self.response_dir = "tests/response"
        self.results_dir = "tests/results"
        
        # Ensure directories exist
        os.makedirs(self.response_dir, exist_ok=True)
        os.makedirs(self.results_dir, exist_ok=True)
        
    def load_base64_payload(self, payload_file: str) -> str:
        """Load base64 encoded payload from file.
        
        Args:
            payload_file: Name of the payload file in payload directory.
            
        Returns:
            Base64 encoded payload string.
        """
        payload_path = os.path.join(self.payload_dir, payload_file)
        with open(payload_path, 'r') as f:
            return f.read().strip()
    
    def save_response(self, response_file: str, response_data: Any) -> None:
        """Save response data to response directory.
        
        Args:
            response_file: Name of the response file.
            response_data: Response data to save.
        """
        response_path = os.path.join(self.response_dir, response_file)
        with open(response_path, 'w') as f:
            if isinstance(response_data, str):
                f.write(response_data)
            else:
                json.dump(response_data, f, indent=2, default=str)
    
    def test_agentcore_invoke(self, test_name: str, payload_file: str) -> Dict[str, Any]:
        """Test using agentcore invoke command with base64 payload.
        
        Args:
            test_name: Name of the test for logging.
            payload_file: Name of the base64 payload file.
            
        Returns:
            Test result dictionary.
        """
        try:
            # Load base64 payload
            payload_b64 = self.load_base64_payload(payload_file)
            payload_json = base64.b64decode(payload_b64).decode('utf-8')
            payload_data = json.loads(payload_json)
            
            print(f"🧪 Testing {test_name} with payload: {payload_data}")
            
            # Use agentcore invoke command
            cmd = ["agentcore", "invoke", payload_json]
            
            print(f"Command: {' '.join(cmd[:2])} [payload omitted]")
            
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=120,
                cwd="."
            )
            
            if result.returncode == 0:
                print("✅ AgentCore invoke successful!")
                
                try:
                    # Parse the response
                    response_text = result.stdout.strip()
                    print(f"📊 Response: {response_text}")
                    
                    # Save response to file
                    response_file = f"{test_name}_response.json"
                    self.save_response(response_file, response_text)
                    
                    return {
                        "success": True,
                        "response": response_text,
                        "response_file": response_file,
                        "error": None
                    }
                    
                except Exception as e:
                    print(f"⚠️ Error parsing response: {e}")
                    
                    # Save error response
                    error_file = f"{test_name}_error_response.txt"
                    self.save_response(error_file, result.stdout)
                    
                    return {
                        "success": True,
                        "response": result.stdout,
                        "response_file": error_file,
                        "error": f"Parse error: {e}"
                    }
            else:
                print(f"❌ AgentCore invoke failed (exit code {result.returncode}):")
                print(f"STDOUT: {result.stdout}")
                print(f"STDERR: {result.stderr}")
                
                # Save error response
                error_file = f"{test_name}_error.txt"
                self.save_response(error_file, {
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "returncode": result.returncode
                })
                
                return {
                    "success": False,
                    "response": None,
                    "response_file": error_file,
                    "error": result.stderr
                }
                
        except subprocess.TimeoutExpired:
            print("⏰ Request timed out")
            return {
                "success": False,
                "response": None,
                "error": "Timeout"
            }
        except Exception as e:
            print(f"💥 Unexpected error: {e}")
            return {
                "success": False,
                "response": None,
                "error": str(e)
            }
    
    def test_aws_cli_invoke(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Test using AWS CLI bedrock-agentcore invoke.
        
        Args:
            payload: JSON payload to send.
            
        Returns:
            Test result dictionary.
        """
        try:
            print(f"🧪 Testing AWS CLI invoke with payload")
            
            # Create temporary file for response
            response_file = "aws_invoke_response.json"
            
            cmd = [
                "aws", "bedrock-agentcore", "invoke-agent-runtime",
                "--agent-runtime-arn", self.agent_arn,
                "--region", self.region,
                "--payload", json.dumps(payload),
                response_file
            ]
            
            print(f"Command: aws bedrock-agentcore invoke-agent-runtime --agent-runtime-arn {self.agent_arn} ...")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode == 0:
                print("✅ AWS CLI invoke successful!")
                
                try:
                    # Read response from file
                    with open(response_file, 'r') as f:
                        response = json.load(f)
                    
                    print(f"📊 Response: {json.dumps(response, indent=2)}")
                    
                    return {
                        "success": True,
                        "response": response,
                        "error": None
                    }
                    
                except Exception as e:
                    print(f"⚠️ Error reading response: {e}")
                    return {
                        "success": True,
                        "response": result.stdout,
                        "error": f"Response read error: {e}"
                    }
            else:
                print(f"❌ AWS CLI invoke failed (exit code {result.returncode}):")
                print(f"STDOUT: {result.stdout}")
                print(f"STDERR: {result.stderr}")
                
                return {
                    "success": False,
                    "response": None,
                    "error": result.stderr
                }
                
        except subprocess.TimeoutExpired:
            print("⏰ Request timed out")
            return {
                "success": False,
                "response": None,
                "error": "Timeout"
            }
        except Exception as e:
            print(f"💥 Unexpected error: {e}")
            return {
                "success": False,
                "response": None,
                "error": str(e)
            }
    
    def run_comprehensive_tests(self) -> Dict[str, Any]:
        """Run comprehensive tests of the MCP server.
        
        Returns:
            Test results summary.
        """
        print("🚀 Starting Comprehensive MCP Server Tests")
        print("=" * 50)
        
        test_results = {
            "agent_info": {
                "agent_id": self.agent_id,
                "agent_arn": self.agent_arn,
                "region": self.region
            },
            "tests": {},
            "summary": {
                "total_tests": 0,
                "passed": 0,
                "failed": 0,
                "success_rate": 0.0
            }
        }
        
        # Test 1: Basic restaurant search by district
        print("\n🧪 Test 1: Restaurant Search by District")
        print("-" * 40)
        
        district_test = self.test_agentcore_invoke(
            "district_search",
            "district_search_prompt.b64"
        )
        test_results["tests"]["district_search"] = district_test
        test_results["summary"]["total_tests"] += 1
        if district_test["success"]:
            test_results["summary"]["passed"] += 1
        else:
            test_results["summary"]["failed"] += 1
        
        # Test 2: Restaurant search by meal type
        print("\n🧪 Test 2: Restaurant Search by Meal Type")
        print("-" * 40)
        
        meal_test = self.test_agentcore_invoke(
            "meal_type_search",
            "meal_type_search_prompt.b64"
        )
        test_results["tests"]["meal_type_search"] = meal_test
        test_results["summary"]["total_tests"] += 1
        if meal_test["success"]:
            test_results["summary"]["passed"] += 1
        else:
            test_results["summary"]["failed"] += 1
        
        # Test 3: Combined search
        print("\n🧪 Test 3: Combined Restaurant Search")
        print("-" * 40)
        
        combined_test = self.test_agentcore_invoke(
            "combined_search",
            "combined_search_prompt.b64"
        )
        test_results["tests"]["combined_search"] = combined_test
        test_results["summary"]["total_tests"] += 1
        if combined_test["success"]:
            test_results["summary"]["passed"] += 1
        else:
            test_results["summary"]["failed"] += 1
        
        # Test 4: General conversation
        print("\n🧪 Test 4: General Conversation")
        print("-" * 40)
        
        general_test = self.test_agentcore_invoke(
            "general_conversation",
            "general_conversation_prompt.b64"
        )
        test_results["tests"]["general_conversation"] = general_test
        test_results["summary"]["total_tests"] += 1
        if general_test["success"]:
            test_results["summary"]["passed"] += 1
        else:
            test_results["summary"]["failed"] += 1
        
        # Calculate success rate
        if test_results["summary"]["total_tests"] > 0:
            test_results["summary"]["success_rate"] = (
                test_results["summary"]["passed"] / 
                test_results["summary"]["total_tests"] * 100
            )
        
        # Print summary
        print("\n📊 Test Results Summary")
        print("=" * 30)
        print(f"Total Tests: {test_results['summary']['total_tests']}")
        print(f"Passed: {test_results['summary']['passed']}")
        print(f"Failed: {test_results['summary']['failed']}")
        print(f"Success Rate: {test_results['summary']['success_rate']:.1f}%")
        
        if test_results["summary"]["success_rate"] >= 75:
            print("\n🎉 DEPLOYMENT STATUS: SUCCESS - MCP server is working well!")
        elif test_results["summary"]["success_rate"] >= 50:
            print("\n⚠️ DEPLOYMENT STATUS: PARTIAL - Some issues detected")
        else:
            print("\n💥 DEPLOYMENT STATUS: FAILED - Major issues detected")
        
        return test_results


def main():
    """Main test function."""
    try:
        tester = AuthenticatedMCPTester()
        results = tester.run_comprehensive_tests()
        
        # Save results to results directory
        results_file = os.path.join(tester.results_dir, "authenticated_mcp_test_results.json")
        with open(results_file, "w") as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n💾 Test results saved to: {results_file}")
        
        # Return appropriate exit code
        success_rate = results["summary"]["success_rate"]
        return 0 if success_rate >= 75 else 1
        
    except Exception as e:
        print(f"💥 Test execution failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())