#!/usr/bin/env python3
"""
End-to-end authentication tests for Restaurant Reasoning MCP server.

This test suite validates the complete authentication flow from Cognito login
to reasoning MCP tool execution, including JWT token propagation through
AgentCore Runtime to the reasoning MCP server.

Requirements: 13.1, 13.2, 13.4, 14.1, 15.1
"""

import json
import os
import sys
import asyncio
import getpass
from typing import Dict, Any, Optional, List
import time
from dataclasses import dataclass

import boto3
from botocore.exceptions import ClientError
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

# Import existing authentication services
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.auth_service import CognitoAuthenticator, AuthenticationError, TokenValidator
from services.auth_error_handler import AuthenticationErrorHandler
from services.security_monitor import SecurityMonitor


@dataclass
class AuthTestResult:
    """Container for authentication test results."""
    test_name: str
    success: bool
    error_message: Optional[str] = None
    execution_time: float = 0.0
    details: Optional[Dict[str, Any]] = None


class ReasoningE2EAuthTester:
    """End-to-end authentication tester for reasoning MCP server."""
    
    def __init__(self, cognito_config: Dict[str, Any]):
        """
        Initialize E2E authentication tester.
        
        Args:
            cognito_config: Cognito configuration dictionary
        """
        self.cognito_config = cognito_config
        self.test_results: List[AuthTestResult] = []
        
        # Initialize authentication services
        self.authenticator = CognitoAuthenticator(
            user_pool_id=cognito_config['user_pool']['user_pool_id'],
            client_id=cognito_config['app_client']['client_id'],
            region=cognito_config['region']
        )
        
        self.token_validator = TokenValidator({
            'user_pool_id': cognito_config['user_pool']['user_pool_id'],
            'client_id': cognito_config['app_client']['client_id'],
            'region': cognito_config['region'],
            'discovery_url': cognito_config['discovery_url']
        })
        
        self.error_handler = AuthenticationErrorHandler()
        self.security_monitor = SecurityMonitor()
        
        # Test credentials (will be prompted securely)
        self.test_username = None
        self.test_password = None
        self.access_token = None
        self.agentcore_runtime_url = None
    
    def setup_test_credentials(self) -> bool:
        """
        Setup test credentials by prompting user securely.
        
        Returns:
            True if credentials are provided, False otherwise
        """
        try:
            print("🔐 Setting up test credentials for E2E authentication tests...")
            
            # Prompt for username
            default_username = self.cognito_config.get('test_user', {}).get('username', 'testing_user@test.com.hk')
            username = input(f"Enter test username (default: {default_username}): ").strip()
            if not username:
                username = default_username
            
            # Prompt for password securely
            password = getpass.getpass(f"Enter password for {username}: ")
            
            if not password:
                print("❌ Password is required for authentication tests")
                return False
            
            self.test_username = username
            self.test_password = password
            
            print(f"✓ Test credentials configured for: {username}")
            return True
            
        except Exception as e:
            print(f"✗ Failed to setup test credentials: {e}")
            return False
    
    async def test_cognito_authentication_flow(self) -> AuthTestResult:
        """
        Test complete Cognito authentication flow with SRP.
        
        Returns:
            AuthTestResult with test outcome
        """
        start_time = time.time()
        
        try:
            print("🧪 Testing Cognito authentication flow...")
            
            # Test SRP authentication
            tokens = self.authenticator.authenticate_user(
                self.test_username, 
                self.test_password
            )
            
            # Validate tokens
            if not tokens.access_token or not tokens.id_token:
                return AuthTestResult(
                    test_name="cognito_authentication_flow",
                    success=False,
                    error_message="Missing tokens in authentication response",
                    execution_time=time.time() - start_time
                )
            
            # Store access token for subsequent tests
            self.access_token = tokens.access_token
            
            # Test token validation
            claims = await self.token_validator.validate_jwt_token(tokens.access_token)
            
            # Validate claims
            if not claims.user_id or not claims.username:
                return AuthTestResult(
                    test_name="cognito_authentication_flow",
                    success=False,
                    error_message="Invalid claims in JWT token",
                    execution_time=time.time() - start_time
                )
            
            execution_time = time.time() - start_time
            
            return AuthTestResult(
                test_name="cognito_authentication_flow",
                success=True,
                execution_time=execution_time,
                details={
                    'token_type': tokens.token_type,
                    'expires_in': tokens.expires_in,
                    'user_id': claims.user_id,
                    'username': claims.username,
                    'client_id': claims.client_id,
                    'token_use': claims.token_use
                }
            )
            
        except AuthenticationError as e:
            return AuthTestResult(
                test_name="cognito_authentication_flow",
                success=False,
                error_message=f"{e.error_type}: {e.message}",
                execution_time=time.time() - start_time,
                details={
                    'error_code': e.error_code,
                    'suggested_action': e.suggested_action
                }
            )
        except Exception as e:
            return AuthTestResult(
                test_name="cognito_authentication_flow",
                success=False,
                error_message=f"Unexpected error: {str(e)}",
                execution_time=time.time() - start_time
            )
    
    async def test_jwt_token_propagation(self) -> AuthTestResult:
        """
        Test JWT token propagation through AgentCore Runtime.
        
        Returns:
            AuthTestResult with test outcome
        """
        start_time = time.time()
        
        try:
            print("🧪 Testing JWT token propagation through AgentCore Runtime...")
            
            if not self.access_token:
                return AuthTestResult(
                    test_name="jwt_token_propagation",
                    success=False,
                    error_message="No access token available for propagation test",
                    execution_time=time.time() - start_time
                )
            
            # Construct AgentCore Runtime URL
            agent_arn = self.get_reasoning_agent_arn()
            if not agent_arn:
                return AuthTestResult(
                    test_name="jwt_token_propagation",
                    success=False,
                    error_message="Could not determine reasoning agent ARN",
                    execution_time=time.time() - start_time
                )
            
            mcp_url = self.construct_agentcore_runtime_url(agent_arn)
            
            # Test MCP connection with JWT token
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            # Attempt to connect and initialize MCP session
            async with streamablehttp_client(mcp_url, headers=headers) as (read, write, _):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    
                    # List tools to verify connection
                    tools = await session.list_tools()
                    
                    if not tools.tools:
                        return AuthTestResult(
                            test_name="jwt_token_propagation",
                            success=False,
                            error_message="No MCP tools available - token propagation may have failed",
                            execution_time=time.time() - start_time
                        )
            
            execution_time = time.time() - start_time
            
            return AuthTestResult(
                test_name="jwt_token_propagation",
                success=True,
                execution_time=execution_time,
                details={
                    'mcp_url': mcp_url,
                    'tools_count': len(tools.tools),
                    'tools_available': [tool.name for tool in tools.tools]
                }
            )
            
        except Exception as e:
            return AuthTestResult(
                test_name="jwt_token_propagation",
                success=False,
                error_message=f"Token propagation failed: {str(e)}",
                execution_time=time.time() - start_time
            )
    
    async def test_reasoning_mcp_tool_execution(self) -> AuthTestResult:
        """
        Test authenticated reasoning MCP tool execution.
        
        Returns:
            AuthTestResult with test outcome
        """
        start_time = time.time()
        
        try:
            print("🧪 Testing authenticated reasoning MCP tool execution...")
            
            if not self.access_token:
                return AuthTestResult(
                    test_name="reasoning_mcp_tool_execution",
                    success=False,
                    error_message="No access token available for tool execution test",
                    execution_time=time.time() - start_time
                )
            
            # Get MCP URL
            agent_arn = self.get_reasoning_agent_arn()
            mcp_url = self.construct_agentcore_runtime_url(agent_arn)
            
            # Prepare test data
            sample_restaurants = [
                {
                    "id": "test_001",
                    "name": "Test Restaurant 1",
                    "address": "123 Test Street",
                    "sentiment": {"likes": 90, "dislikes": 5, "neutral": 5},
                    "meal_type": ["Test Cuisine"],
                    "district": "Test District",
                    "price_range": "$"
                },
                {
                    "id": "test_002",
                    "name": "Test Restaurant 2", 
                    "address": "456 Test Avenue",
                    "sentiment": {"likes": 85, "dislikes": 10, "neutral": 5},
                    "meal_type": ["Test Cuisine"],
                    "district": "Test District",
                    "price_range": "$$"
                }
            ]
            
            # Test authenticated MCP tool calls
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            async with streamablehttp_client(mcp_url, headers=headers) as (read, write, _):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    
                    # Test recommend_restaurants tool
                    recommendation_result = await session.call_tool(
                        "recommend_restaurants",
                        {
                            "restaurants": sample_restaurants,
                            "ranking_method": "sentiment_likes"
                        }
                    )
                    
                    if not recommendation_result.content:
                        return AuthTestResult(
                            test_name="reasoning_mcp_tool_execution",
                            success=False,
                            error_message="No content returned from recommend_restaurants tool",
                            execution_time=time.time() - start_time
                        )
                    
                    # Parse and validate result
                    result_data = json.loads(recommendation_result.content[0].text)
                    
                    if 'candidates' not in result_data or 'recommendation' not in result_data:
                        return AuthTestResult(
                            test_name="reasoning_mcp_tool_execution",
                            success=False,
                            error_message="Invalid response format from reasoning tool",
                            execution_time=time.time() - start_time
                        )
                    
                    # Test analyze_restaurant_sentiment tool
                    sentiment_result = await session.call_tool(
                        "analyze_restaurant_sentiment",
                        {"restaurants": sample_restaurants}
                    )
                    
                    if not sentiment_result.content:
                        return AuthTestResult(
                            test_name="reasoning_mcp_tool_execution",
                            success=False,
                            error_message="No content returned from analyze_restaurant_sentiment tool",
                            execution_time=time.time() - start_time
                        )
            
            execution_time = time.time() - start_time
            
            return AuthTestResult(
                test_name="reasoning_mcp_tool_execution",
                success=True,
                execution_time=execution_time,
                details={
                    'recommendation_tool_success': True,
                    'sentiment_analysis_tool_success': True,
                    'candidates_count': len(result_data.get('candidates', [])),
                    'recommended_restaurant': result_data.get('recommendation', {}).get('name', 'Unknown')
                }
            )
            
        except Exception as e:
            return AuthTestResult(
                test_name="reasoning_mcp_tool_execution",
                success=False,
                error_message=f"Tool execution failed: {str(e)}",
                execution_time=time.time() - start_time
            )
    
    async def test_authentication_error_handling(self) -> AuthTestResult:
        """
        Test authentication error handling at AgentCore and MCP server levels.
        
        Returns:
            AuthTestResult with test outcome
        """
        start_time = time.time()
        
        try:
            print("🧪 Testing authentication error handling...")
            
            # Get MCP URL
            agent_arn = self.get_reasoning_agent_arn()
            mcp_url = self.construct_agentcore_runtime_url(agent_arn)
            
            error_scenarios = []
            
            # Test 1: Invalid token
            try:
                invalid_headers = {
                    'Authorization': 'Bearer invalid_token_12345',
                    'Content-Type': 'application/json'
                }
                
                async with streamablehttp_client(mcp_url, headers=invalid_headers) as (read, write, _):
                    async with ClientSession(read, write) as session:
                        await session.initialize()
                
                error_scenarios.append({
                    'scenario': 'invalid_token',
                    'expected_failure': True,
                    'actual_result': 'unexpected_success'
                })
                
            except Exception as e:
                error_scenarios.append({
                    'scenario': 'invalid_token',
                    'expected_failure': True,
                    'actual_result': 'expected_failure',
                    'error_message': str(e)
                })
            
            # Test 2: Missing Authorization header
            try:
                no_auth_headers = {'Content-Type': 'application/json'}
                
                async with streamablehttp_client(mcp_url, headers=no_auth_headers) as (read, write, _):
                    async with ClientSession(read, write) as session:
                        await session.initialize()
                
                error_scenarios.append({
                    'scenario': 'missing_auth_header',
                    'expected_failure': True,
                    'actual_result': 'unexpected_success'
                })
                
            except Exception as e:
                error_scenarios.append({
                    'scenario': 'missing_auth_header',
                    'expected_failure': True,
                    'actual_result': 'expected_failure',
                    'error_message': str(e)
                })
            
            # Test 3: Expired token (simulate by using an old token format)
            try:
                expired_headers = {
                    'Authorization': 'Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiYWRtaW4iOnRydWUsImV4cCI6MTUxNjIzOTAyMn0.invalid',
                    'Content-Type': 'application/json'
                }
                
                async with streamablehttp_client(mcp_url, headers=expired_headers) as (read, write, _):
                    async with ClientSession(read, write) as session:
                        await session.initialize()
                
                error_scenarios.append({
                    'scenario': 'expired_token',
                    'expected_failure': True,
                    'actual_result': 'unexpected_success'
                })
                
            except Exception as e:
                error_scenarios.append({
                    'scenario': 'expired_token',
                    'expected_failure': True,
                    'actual_result': 'expected_failure',
                    'error_message': str(e)
                })
            
            # Evaluate results
            all_scenarios_handled_correctly = all(
                scenario['actual_result'] == 'expected_failure' 
                for scenario in error_scenarios
            )
            
            execution_time = time.time() - start_time
            
            return AuthTestResult(
                test_name="authentication_error_handling",
                success=all_scenarios_handled_correctly,
                execution_time=execution_time,
                details={
                    'error_scenarios': error_scenarios,
                    'total_scenarios': len(error_scenarios),
                    'correctly_handled': sum(1 for s in error_scenarios if s['actual_result'] == 'expected_failure')
                }
            )
            
        except Exception as e:
            return AuthTestResult(
                test_name="authentication_error_handling",
                success=False,
                error_message=f"Error handling test failed: {str(e)}",
                execution_time=time.time() - start_time
            )
    
    def get_reasoning_agent_arn(self) -> Optional[str]:
        """
        Get reasoning agent ARN from deployment configuration.
        
        Returns:
            Agent ARN or None if not found
        """
        try:
            # Try to load from deployment config
            if os.path.exists('agentcore_deployment_config.json'):
                with open('agentcore_deployment_config.json', 'r') as f:
                    deployment_config = json.load(f)
                    return deployment_config.get('agent_arn')
            
            # Try to load from bedrock agentcore config
            if os.path.exists('.bedrock_agentcore.yaml'):
                import yaml
                with open('.bedrock_agentcore.yaml', 'r') as f:
                    config = yaml.safe_load(f)
                    agents = config.get('agents', {})
                    reasoning_agent = agents.get('restaurant_reasoning_mcp', {})
                    bedrock_config = reasoning_agent.get('bedrock_agentcore', {})
                    return bedrock_config.get('agent_arn')
            
            # Default ARN pattern
            return "arn:aws:bedrock-agentcore:us-east-1:209803798463:runtime/restaurant_reasoning_mcp"
            
        except Exception as e:
            print(f"⚠️ Could not determine agent ARN: {e}")
            return None
    
    def construct_agentcore_runtime_url(self, agent_arn: str) -> str:
        """
        Construct AgentCore Runtime URL from agent ARN.
        
        Args:
            agent_arn: AgentCore Runtime agent ARN
            
        Returns:
            MCP endpoint URL
        """
        try:
            # Extract region and agent name from ARN
            arn_parts = agent_arn.split(':')
            region = arn_parts[3]
            agent_name = arn_parts[5].split('/')[-1]
            
            # Construct AgentCore Runtime URL
            return f"https://{agent_name}.{region}.bedrock-agentcore.amazonaws.com"
            
        except Exception as e:
            print(f"✗ Failed to construct runtime URL: {e}")
            return None
    
    async def run_comprehensive_e2e_tests(self) -> Dict[str, Any]:
        """
        Run comprehensive end-to-end authentication tests.
        
        Returns:
            Dictionary with complete test results
        """
        print("🚀 Starting comprehensive E2E authentication tests for reasoning server...")
        print("=" * 80)
        
        # Setup test credentials
        if not self.setup_test_credentials():
            return {
                'overall_success': False,
                'error': 'Failed to setup test credentials',
                'test_results': []
            }
        
        # Run all test scenarios
        test_methods = [
            self.test_cognito_authentication_flow,
            self.test_jwt_token_propagation,
            self.test_reasoning_mcp_tool_execution,
            self.test_authentication_error_handling
        ]
        
        for test_method in test_methods:
            try:
                result = await test_method()
                self.test_results.append(result)
                
                # Display immediate result
                status = "✅" if result.success else "❌"
                print(f"{status} {result.test_name}: {result.execution_time:.2f}s")
                
                if not result.success:
                    print(f"   Error: {result.error_message}")
                elif result.details:
                    print(f"   Details: {json.dumps(result.details, indent=2)}")
                
            except Exception as e:
                error_result = AuthTestResult(
                    test_name=test_method.__name__,
                    success=False,
                    error_message=f"Test execution failed: {str(e)}"
                )
                self.test_results.append(error_result)
                print(f"❌ {test_method.__name__}: Test execution failed - {str(e)}")
        
        # Calculate overall results
        successful_tests = sum(1 for result in self.test_results if result.success)
        total_tests = len(self.test_results)
        overall_success = successful_tests == total_tests
        
        return {
            'overall_success': overall_success,
            'successful_tests': successful_tests,
            'total_tests': total_tests,
            'test_results': [
                {
                    'test_name': result.test_name,
                    'success': result.success,
                    'error_message': result.error_message,
                    'execution_time': result.execution_time,
                    'details': result.details
                }
                for result in self.test_results
            ]
        }
    
    def generate_test_report(self, results: Dict[str, Any]) -> str:
        """
        Generate comprehensive test report.
        
        Args:
            results: Test results dictionary
            
        Returns:
            Formatted test report string
        """
        report = []
        report.append("=" * 80)
        report.append("🧪 REASONING MCP SERVER E2E AUTHENTICATION TEST REPORT")
        report.append("=" * 80)
        
        # Overall summary
        overall_status = "✅ PASSED" if results['overall_success'] else "❌ FAILED"
        report.append(f"Overall Status: {overall_status}")
        report.append(f"Tests Passed: {results['successful_tests']}/{results['total_tests']}")
        report.append("")
        
        # Individual test results
        report.append("📋 Individual Test Results:")
        report.append("-" * 40)
        
        for test_result in results['test_results']:
            status = "✅" if test_result['success'] else "❌"
            report.append(f"{status} {test_result['test_name']}")
            report.append(f"   Execution Time: {test_result['execution_time']:.2f}s")
            
            if not test_result['success'] and test_result['error_message']:
                report.append(f"   Error: {test_result['error_message']}")
            
            if test_result['details']:
                report.append(f"   Details: {json.dumps(test_result['details'], indent=6)}")
            
            report.append("")
        
        # Recommendations
        report.append("💡 Recommendations:")
        report.append("-" * 20)
        
        if results['overall_success']:
            report.append("✅ All authentication tests passed successfully!")
            report.append("✅ JWT token propagation is working correctly")
            report.append("✅ Reasoning MCP tools are accessible with authentication")
            report.append("✅ Error handling is functioning as expected")
        else:
            failed_tests = [r for r in results['test_results'] if not r['success']]
            
            for failed_test in failed_tests:
                report.append(f"❌ Fix {failed_test['test_name']}:")
                
                if 'cognito_authentication' in failed_test['test_name']:
                    report.append("   - Verify Cognito User Pool configuration")
                    report.append("   - Check test user credentials and status")
                    report.append("   - Ensure SRP authentication is enabled")
                
                elif 'jwt_token_propagation' in failed_test['test_name']:
                    report.append("   - Verify AgentCore Runtime JWT authorizer configuration")
                    report.append("   - Check discovery URL and allowed clients")
                    report.append("   - Ensure reasoning MCP server is deployed")
                
                elif 'mcp_tool_execution' in failed_test['test_name']:
                    report.append("   - Verify reasoning MCP server implementation")
                    report.append("   - Check tool registration and parameter schemas")
                    report.append("   - Review MCP server authentication middleware")
                
                elif 'error_handling' in failed_test['test_name']:
                    report.append("   - Verify authentication error responses")
                    report.append("   - Check JWT token validation logic")
                    report.append("   - Ensure proper error codes are returned")
        
        report.append("")
        report.append("=" * 80)
        
        return "\n".join(report)


def load_cognito_config() -> Dict[str, Any]:
    """Load Cognito configuration from JSON file."""
    try:
        with open('cognito_config.json', 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"✗ Failed to load Cognito config: {e}")
        return {}


async def main():
    """Main function to run E2E authentication tests."""
    print("🚀 Restaurant Reasoning MCP Server - E2E Authentication Tests")
    print("=" * 80)
    
    # Load Cognito configuration
    cognito_config = load_cognito_config()
    if not cognito_config:
        print("❌ Could not load Cognito configuration")
        return 1
    
    print(f"✓ Loaded Cognito config for User Pool: {cognito_config['user_pool']['user_pool_id']}")
    
    # Initialize E2E tester
    tester = ReasoningE2EAuthTester(cognito_config)
    
    # Run comprehensive tests
    results = await tester.run_comprehensive_e2e_tests()
    
    # Generate and display report
    report = tester.generate_test_report(results)
    print(report)
    
    # Save results to file
    try:
        with open('reasoning_auth_e2e_test_results.json', 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print("📄 Test results saved to: reasoning_auth_e2e_test_results.json")
    except Exception as e:
        print(f"⚠️ Could not save test results: {e}")
    
    # Return appropriate exit code
    return 0 if results['overall_success'] else 1


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Run E2E authentication tests for reasoning MCP server')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose output')
    
    args = parser.parse_args()
    
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⚠️ Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Tests failed with error: {e}")
        sys.exit(1)