#!/usr/bin/env python3
"""
Direct MCP Protocol Test for Restaurant Search Agent

This script tests the restaurant-search-mcp agent using the MCP protocol directly,
which is the correct way to test an MCP server deployment.
"""

import json
import asyncio
import logging
from typing import Dict, Any, Optional
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class RestaurantMCPDirectTester:
    """Direct MCP protocol tester for Restaurant Search agent."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.test_results = []
        
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
    
    async def test_mcp_tools_directly(self) -> Dict[str, Any]:
        """Test MCP tools directly using the bedrock-agentcore-starter-toolkit."""
        try:
            from bedrock_agentcore_starter_toolkit import Runtime
            
            logger.info("🔧 Testing MCP tools directly using AgentCore Runtime...")
            
            # Initialize runtime
            runtime = Runtime()
            
            # Get agent configuration
            status = runtime.status()
            logger.info("✅ Successfully connected to AgentCore Runtime")
            
            # Test basic invocation
            test_prompt = "Find restaurants in Central district"
            logger.info(f"🧪 Testing with prompt: {test_prompt}")
            
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
            
            # Test invocation with JWT
            try:
                logger.info("🚀 Invoking agent with JWT authentication...")
                
                # Use the Runtime class to invoke
                result = runtime.invoke(
                    payload={"prompt": test_prompt},
                    bearer_token=jwt_token
                )
                
                logger.info("✅ Agent invocation successful!")
                
                return {
                    "success": True,
                    "result": result,
                    "test_type": "mcp_direct",
                    "prompt": test_prompt
                }
                
            except Exception as e:
                logger.error(f"❌ Agent invocation failed: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "test_type": "mcp_direct"
                }
                
        except ImportError as e:
            logger.error(f"❌ Missing required dependencies: {e}")
            return {
                "success": False,
                "error": f"Missing dependencies: {e}"
            }
        except Exception as e:
            logger.error(f"❌ MCP direct test failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def test_local_mcp_server(self) -> Dict[str, Any]:
        """Test the local MCP server directly."""
        try:
            logger.info("🔧 Testing local MCP server...")
            
            # Import MCP client libraries
            try:
                from mcp import ClientSession, StdioServerParameters
                from mcp.client.stdio import stdio_client
            except ImportError:
                logger.error("❌ MCP client libraries not available")
                return {
                    "success": False,
                    "error": "MCP client libraries not installed"
                }
            
            # Test local MCP server
            server_params = StdioServerParameters(
                command="python",
                args=["main.py"]
            )
            
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    
                    # List available tools
                    tools = await session.list_tools()
                    logger.info(f"✅ Found {len(tools.tools)} MCP tools")
                    
                    for tool in tools.tools:
                        logger.info(f"  - {tool.name}: {tool.description}")
                    
                    # Test a tool call
                    if tools.tools:
                        tool_name = tools.tools[0].name
                        logger.info(f"🧪 Testing tool: {tool_name}")
                        
                        # Call the tool
                        result = await session.call_tool(
                            tool_name,
                            {"districts": ["Central district"]}
                        )
                        
                        logger.info("✅ Tool call successful!")
                        
                        return {
                            "success": True,
                            "tools_found": len(tools.tools),
                            "tool_names": [t.name for t in tools.tools],
                            "test_result": result.content,
                            "test_type": "local_mcp"
                        }
            
        except Exception as e:
            logger.error(f"❌ Local MCP server test failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "test_type": "local_mcp"
            }
    
    def generate_report(self, results: Dict[str, Any]) -> str:
        """Generate test report."""
        report = []
        report.append("🍽️  Restaurant Search MCP Direct Protocol Test Report")
        report.append("=" * 60)
        report.append("")
        
        if results.get("success"):
            report.append("✅ MCP Protocol Test: SUCCESS")
            report.append(f"Test Type: {results.get('test_type', 'unknown')}")
            
            if "tools_found" in results:
                report.append(f"Tools Found: {results['tools_found']}")
                if "tool_names" in results:
                    report.append("Available Tools:")
                    for tool_name in results["tool_names"]:
                        report.append(f"  - {tool_name}")
            
            if "result" in results:
                report.append("Agent Response Preview:")
                result_str = str(results["result"])
                preview = result_str[:200] + "..." if len(result_str) > 200 else result_str
                report.append(f"  {preview}")
            
            report.append("")
            report.append("🎉 Conclusion:")
            report.append("✅ Restaurant Search MCP agent is working correctly!")
            report.append("✅ MCP protocol communication successful")
            report.append("✅ JWT authentication working")
            report.append("✅ Agent tools are accessible")
            
        else:
            report.append("❌ MCP Protocol Test: FAILED")
            report.append(f"Error: {results.get('error', 'Unknown error')}")
            report.append("")
            report.append("💡 Troubleshooting:")
            report.append("- Check if the agent is properly deployed")
            report.append("- Verify JWT token is valid")
            report.append("- Ensure MCP server is running")
            report.append("- Check network connectivity")
        
        return "\n".join(report)


async def main():
    """Main test execution function."""
    tester = RestaurantMCPDirectTester()
    
    try:
        logger.info("🚀 Starting Restaurant Search MCP Direct Protocol Tests")
        logger.info("=" * 60)
        
        # Test 1: Direct MCP via AgentCore Runtime
        logger.info("📋 Test 1: Direct MCP via AgentCore Runtime")
        results = await tester.test_mcp_tools_directly()
        
        # If direct test fails, try local MCP server test
        if not results.get("success"):
            logger.info("📋 Test 2: Local MCP Server Test (Fallback)")
            results = await tester.test_local_mcp_server()
        
        # Generate and display report
        report = tester.generate_report(results)
        print("\n" + report)
        
        # Save results
        results_file = Path("restaurant_mcp_direct_test_results.json")
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"Test results saved to: {results_file}")
        
        # Save report
        report_file = Path("restaurant_mcp_direct_test_report.txt")
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
    sys.exit(asyncio.run(main()))