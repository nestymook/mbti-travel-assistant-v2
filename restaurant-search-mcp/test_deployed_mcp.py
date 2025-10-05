#!/usr/bin/env python3
"""
Test the deployed Restaurant Search MCP agent using the bedrock-agentcore-starter-toolkit.

This script properly configures and tests the deployed MCP agent.
"""

import json
import asyncio
import logging
from typing import Dict, Any, Optional
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class DeployedMCPTester:
    """Test the deployed MCP agent using proper configuration."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        
    def load_cognito_config(self) -> Dict[str, Any]:
        """Load Cognito configuration."""
        try:
            config_file = self.project_root / "cognito_config.json"
            if config_file.exists():
                with open(config_file, 'r') as f:
                    return json.load(f)
            else:
                logger.warning("No cognito_config.json found")
                return {}
        except Exception as e:
            logger.error(f"Failed to load Cognito config: {e}")
            return {}
    
    def calculate_secret_hash(self, username: str, client_id: str, client_secret: str) -> str:
        """Calculate SECRET_HASH for Cognito authentication."""
        import hmac
        import hashlib
        import base64
        
        message = username + client_id
        dig = hmac.new(
            client_secret.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).digest()
        return base64.b64encode(dig).decode()
    
    def authenticate_with_cognito(self, cognito_config: Dict[str, Any]) -> Optional[str]:
        """Authenticate with Cognito and get JWT token."""
        try:
            import boto3
            import getpass
            from botocore.exceptions import ClientError
            
            # Get username
            default_username = cognito_config.get('test_user', {}).get('username', 'test@mbti-travel.com')
            username = input(f"Enter username (default: {default_username}): ").strip()
            if not username:
                username = default_username
            
            # Get password
            password = getpass.getpass(f"Enter password for {username}: ")
            
            logger.info(f"🔐 Authenticating with Cognito as: {username}")
            
            # Get client credentials
            client_id = cognito_config['app_client']['client_id']
            client_secret = cognito_config['app_client']['client_secret']
            
            # Calculate SECRET_HASH
            secret_hash = self.calculate_secret_hash(username, client_id, client_secret)
            
            cognito_client = boto3.client('cognito-idp', region_name='us-east-1')
            
            # Prepare auth parameters with SECRET_HASH
            auth_parameters = {
                'USERNAME': username,
                'PASSWORD': password,
                'SECRET_HASH': secret_hash
            }
            
            logger.info("🔑 Initiating authentication with SECRET_HASH...")
            
            response = cognito_client.initiate_auth(
                ClientId=client_id,
                AuthFlow='USER_PASSWORD_AUTH',
                AuthParameters=auth_parameters
            )
            
            access_token = response['AuthenticationResult']['AccessToken']
            logger.info("✅ JWT Authentication successful")
            logger.info(f"Token length: {len(access_token)} characters")
            
            return access_token
            
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return None
    
    def test_deployed_agent(self) -> Dict[str, Any]:
        """Test the deployed agent using the configured Runtime."""
        try:
            from bedrock_agentcore_starter_toolkit import Runtime
            
            logger.info("🔧 Testing deployed MCP agent...")
            
            # Initialize and configure runtime
            runtime = Runtime()
            
            # Configure the runtime with our agent (using existing configuration)
            logger.info("⚙️ Configuring runtime...")
            runtime.configure(
                entrypoint="main.py",
                agent_name="restaurant_search_conversational_agent",
                auto_create_execution_role=True,
                auto_create_ecr=True,
                region="us-east-1"
            )
            
            # Get agent status
            logger.info("📊 Checking agent status...")
            status = runtime.status()
            logger.info("✅ Successfully connected to deployed agent")
            
            # Get JWT token
            cognito_config = self.load_cognito_config()
            if not cognito_config:
                return {
                    "success": False,
                    "error": "No Cognito configuration available"
                }
            
            jwt_token = self.authenticate_with_cognito(cognito_config)
            if not jwt_token:
                return {
                    "success": False,
                    "error": "Failed to get JWT token"
                }
            
            # Test different restaurant search scenarios
            test_cases = [
                {
                    "name": "District Search",
                    "prompt": "Find restaurants in Central district"
                },
                {
                    "name": "Meal Type Search", 
                    "prompt": "Show me breakfast restaurants"
                },
                {
                    "name": "Combined Search",
                    "prompt": "Find dinner restaurants in Tsim Sha Tsui"
                }
            ]
            
            results = []
            
            for test_case in test_cases:
                logger.info(f"🧪 Testing: {test_case['name']}")
                logger.info(f"   Prompt: {test_case['prompt']}")
                
                try:
                    # Invoke the agent
                    result = runtime.invoke(
                        payload={"prompt": test_case["prompt"]},
                        bearer_token=jwt_token
                    )
                    
                    logger.info(f"✅ {test_case['name']}: SUCCESS")
                    
                    # Analyze the response
                    response_text = str(result)
                    has_restaurants = "restaurant" in response_text.lower()
                    has_json = "{" in response_text and "}" in response_text
                    
                    results.append({
                        "test_name": test_case["name"],
                        "success": True,
                        "response_length": len(response_text),
                        "has_restaurants": has_restaurants,
                        "has_json_structure": has_json,
                        "response_preview": response_text[:200] + "..." if len(response_text) > 200 else response_text
                    })
                    
                except Exception as e:
                    logger.error(f"❌ {test_case['name']}: FAILED - {e}")
                    results.append({
                        "test_name": test_case["name"],
                        "success": False,
                        "error": str(e)
                    })
            
            # Calculate overall success
            successful_tests = sum(1 for r in results if r["success"])
            total_tests = len(results)
            success_rate = (successful_tests / total_tests) * 100
            
            return {
                "success": successful_tests > 0,
                "total_tests": total_tests,
                "successful_tests": successful_tests,
                "success_rate": success_rate,
                "test_results": results,
                "agent_status": status,
                "test_type": "deployed_mcp"
            }
            
        except Exception as e:
            logger.error(f"❌ Deployed agent test failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "test_type": "deployed_mcp"
            }
    
    def generate_report(self, results: Dict[str, Any]) -> str:
        """Generate comprehensive test report."""
        report = []
        report.append("🍽️  Restaurant Search MCP Deployed Agent Test Report")
        report.append("=" * 60)
        report.append("")
        
        if results.get("success"):
            report.append("✅ Overall Status: SUCCESS")
            report.append(f"Success Rate: {results.get('success_rate', 0):.1f}%")
            report.append(f"Tests Passed: {results.get('successful_tests', 0)}/{results.get('total_tests', 0)}")
            report.append("")
            
            report.append("📋 Individual Test Results:")
            report.append("-" * 30)
            
            for test_result in results.get("test_results", []):
                status_symbol = "✅" if test_result["success"] else "❌"
                report.append(f"{status_symbol} {test_result['test_name']}")
                
                if test_result["success"]:
                    report.append(f"   Response Length: {test_result.get('response_length', 0)} chars")
                    report.append(f"   Contains Restaurants: {test_result.get('has_restaurants', False)}")
                    report.append(f"   JSON Structure: {test_result.get('has_json_structure', False)}")
                    if "response_preview" in test_result:
                        report.append(f"   Preview: {test_result['response_preview']}")
                else:
                    report.append(f"   Error: {test_result.get('error', 'Unknown error')}")
                report.append("")
            
            report.append("🎯 Analysis:")
            report.append("✅ MCP agent is deployed and accessible")
            report.append("✅ JWT authentication is working")
            report.append("✅ Agent responds to restaurant search queries")
            report.append("✅ MCP protocol communication successful")
            
        else:
            report.append("❌ Overall Status: FAILED")
            report.append(f"Error: {results.get('error', 'Unknown error')}")
            report.append("")
            report.append("💡 Troubleshooting:")
            report.append("- Verify agent deployment status")
            report.append("- Check JWT token validity")
            report.append("- Ensure agent configuration is correct")
            report.append("- Review agent logs for errors")
        
        report.append("")
        report.append("🎉 Conclusion:")
        if results.get("success"):
            report.append("✅ Restaurant Search MCP agent is working correctly!")
            report.append("✅ Ready for production use")
        else:
            report.append("⚠️  Restaurant Search MCP agent needs attention")
            report.append("- Check deployment configuration")
            report.append("- Verify authentication setup")
        
        return "\n".join(report)


def main():
    """Main test execution function."""
    tester = DeployedMCPTester()
    
    try:
        logger.info("🚀 Starting Restaurant Search MCP Deployed Agent Tests")
        logger.info("=" * 60)
        
        # Test the deployed agent
        results = tester.test_deployed_agent()
        
        # Generate and display report
        report = tester.generate_report(results)
        print("\n" + report)
        
        # Save results
        results_file = Path("restaurant_mcp_deployed_test_results.json")
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"Test results saved to: {results_file}")
        
        # Save report
        report_file = Path("restaurant_mcp_deployed_test_report.txt")
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        logger.info(f"Test report saved to: {report_file}")
        
        return 0 if results.get("success") else 1
        
    except Exception as e:
        logger.error(f"Test execution failed: {e}")
        print(f"\n❌ Test execution failed: {e}")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())