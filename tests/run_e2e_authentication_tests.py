#!/usr/bin/env python3
"""
End-to-End Authentication Test Runner

This script runs comprehensive end-to-end authentication tests for the
Restaurant Search MCP server, validating the complete authentication flow
from Cognito login to MCP tool execution through AgentCore Runtime.

Requirements: 16.1, 16.2, 16.4, 17.1, 18.1
"""

import asyncio
import json
import os
import sys
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from test_e2e_authentication_complete import E2EAuthenticationTestSuite


class E2EAuthTestRunner:
    """Test runner for end-to-end authentication tests."""
    
    def __init__(self):
        """Initialize test runner."""
        self.start_time = None
        self.end_time = None
        self.results = None
    
    def print_banner(self):
        """Print test banner."""
        print("🔐" * 35)
        print("🔐  END-TO-END AUTHENTICATION TESTS  🔐")
        print("🔐" * 35)
        print()
        print("Testing complete authentication flow:")
        print("  ✓ Cognito SRP authentication")
        print("  ✓ JWT token validation")
        print("  ✓ AgentCore Runtime integration")
        print("  ✓ MCP tool execution with auth")
        print("  ✓ Error handling scenarios")
        print("  ✓ User context preservation")
        print()
    
    def check_prerequisites(self) -> Dict[str, Any]:
        """Check test prerequisites.
        
        Returns:
            Dictionary with prerequisite check results.
        """
        print("🔍 Checking Prerequisites...")
        
        checks = {}
        
        # Check Cognito configuration
        cognito_config_path = "cognito_config.json"
        if os.path.exists(cognito_config_path):
            try:
                with open(cognito_config_path, 'r') as f:
                    config = json.load(f)
                
                required_fields = ['user_pool', 'app_client', 'discovery_url', 'region']
                missing_fields = [field for field in required_fields if field not in config]
                
                if missing_fields:
                    checks['cognito_config'] = {
                        'status': 'error',
                        'message': f'Missing fields: {missing_fields}'
                    }
                else:
                    checks['cognito_config'] = {
                        'status': 'ok',
                        'user_pool_id': config['user_pool']['user_pool_id'],
                        'client_id': config['app_client']['client_id']
                    }
                    
            except Exception as e:
                checks['cognito_config'] = {
                    'status': 'error',
                    'message': f'Error reading config: {e}'
                }
        else:
            checks['cognito_config'] = {
                'status': 'error',
                'message': 'Cognito configuration file not found'
            }
        
        # Check AgentCore configuration
        agentcore_config_path = ".bedrock_agentcore.yaml"
        if os.path.exists(agentcore_config_path):
            try:
                import yaml
                with open(agentcore_config_path, 'r') as f:
                    config = yaml.safe_load(f)
                
                agents = config.get('agents', {})
                deployed_agents = []
                
                for agent_name, agent_config in agents.items():
                    agent_arn = agent_config.get('bedrock_agentcore', {}).get('agent_arn')
                    if agent_arn:
                        deployed_agents.append({
                            'name': agent_name,
                            'arn': agent_arn,
                            'has_auth': bool(agent_config.get('authorizer_configuration'))
                        })
                
                if deployed_agents:
                    checks['agentcore_config'] = {
                        'status': 'ok',
                        'deployed_agents': deployed_agents
                    }
                else:
                    checks['agentcore_config'] = {
                        'status': 'warning',
                        'message': 'No deployed agents found'
                    }
                    
            except ImportError:
                checks['agentcore_config'] = {
                    'status': 'error',
                    'message': 'PyYAML required: pip install pyyaml'
                }
            except Exception as e:
                checks['agentcore_config'] = {
                    'status': 'error',
                    'message': f'Error reading config: {e}'
                }
        else:
            checks['agentcore_config'] = {
                'status': 'warning',
                'message': 'AgentCore configuration file not found'
            }
        
        # Check MCP client availability
        try:
            from mcp import ClientSession
            from mcp.client.streamable_http import streamablehttp_client
            checks['mcp_client'] = {
                'status': 'ok',
                'message': 'MCP client available'
            }
        except ImportError:
            checks['mcp_client'] = {
                'status': 'warning',
                'message': 'MCP client not available (some tests will be skipped)'
            }
        
        # Check AWS credentials
        try:
            import boto3
            session = boto3.Session()
            credentials = session.get_credentials()
            if credentials:
                checks['aws_credentials'] = {
                    'status': 'ok',
                    'message': 'AWS credentials available'
                }
            else:
                checks['aws_credentials'] = {
                    'status': 'error',
                    'message': 'AWS credentials not found'
                }
        except Exception as e:
            checks['aws_credentials'] = {
                'status': 'error',
                'message': f'AWS credential check failed: {e}'
            }
        
        # Print results
        for check_name, result in checks.items():
            status_icon = {
                'ok': '✅',
                'warning': '⚠️',
                'error': '❌'
            }.get(result['status'], '❓')
            
            print(f"  {status_icon} {check_name}: {result.get('message', result['status'])}")
        
        print()
        return checks
    
    def can_run_tests(self, checks: Dict[str, Any]) -> bool:
        """Check if tests can run based on prerequisites.
        
        Args:
            checks: Prerequisite check results.
            
        Returns:
            True if tests can run, False otherwise.
        """
        # Must have Cognito config and AWS credentials
        required_checks = ['cognito_config', 'aws_credentials']
        
        for check_name in required_checks:
            if checks.get(check_name, {}).get('status') == 'error':
                print(f"❌ Cannot run tests: {check_name} check failed")
                return False
        
        return True
    
    async def run_tests(self, config_file: str = "cognito_config.json",
                       username: Optional[str] = None,
                       password: Optional[str] = None) -> Dict[str, Any]:
        """Run end-to-end authentication tests.
        
        Args:
            config_file: Path to Cognito configuration file.
            username: Test username (optional).
            password: Test password (optional).
            
        Returns:
            Test results dictionary.
        """
        self.start_time = time.time()
        
        try:
            # Initialize test suite
            print("🚀 Initializing Test Suite...")
            test_suite = E2EAuthenticationTestSuite(config_file)
            
            # Override credentials if provided
            if username:
                test_suite.test_username = username
                print(f"  Using custom username: {username}")
            if password:
                test_suite.test_password = password
                print("  Using custom password")
            
            print(f"  Test user: {test_suite.test_username}")
            print(f"  User Pool: {test_suite.cognito_config['user_pool']['user_pool_id']}")
            print(f"  Client ID: {test_suite.cognito_config['app_client']['client_id']}")
            
            if test_suite.agent_arn:
                print(f"  Agent ARN: {test_suite.agent_arn}")
            else:
                print("  ⚠️ No AgentCore Runtime ARN found (some tests will be skipped)")
            
            print()
            
            # Run tests
            self.results = await test_suite.run_all_tests()
            
            return self.results
            
        except Exception as e:
            print(f"💥 Test execution failed: {e}")
            self.results = {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'test_suite': 'E2E Authentication Tests',
                'tests': {},
                'summary': {
                    'total_tests': 0,
                    'successful_tests': 0,
                    'failed_tests': 1,
                    'skipped_tests': 0,
                    'success_rate': 0,
                    'overall_success': False
                },
                'execution_error': str(e)
            }
            return self.results
        finally:
            self.end_time = time.time()
    
    def print_detailed_results(self):
        """Print detailed test results."""
        if not self.results:
            print("❌ No test results available")
            return
        
        print("\n" + "=" * 70)
        print("📋 DETAILED TEST RESULTS")
        print("=" * 70)
        
        for test_name, test_result in self.results.get('tests', {}).items():
            status_icon = "✅" if test_result.get('success', False) else "❌"
            if test_result.get('skipped', False):
                status_icon = "⏭️"
            
            print(f"\n{status_icon} {test_name}")
            print("-" * 50)
            
            if test_result.get('skipped', False):
                print(f"  Status: SKIPPED")
                print(f"  Reason: {test_result.get('error', 'Unknown')}")
            elif test_result.get('success', False):
                print(f"  Status: PASSED")
                
                # Print specific test details
                if 'user_context' in test_result:
                    context = test_result['user_context']
                    print(f"  User ID: {context.get('user_id', 'N/A')}")
                    print(f"  Username: {context.get('username', 'N/A')}")
                    print(f"  Email: {context.get('email', 'N/A')}")
                
                if 'jwt_claims' in test_result:
                    claims = test_result['jwt_claims']
                    print(f"  Token Use: {claims.get('token_use', 'N/A')}")
                    print(f"  Client ID: {claims.get('client_id', 'N/A')}")
                
                if 'tools_tested' in test_result:
                    print(f"  Tools Tested: {test_result['tools_tested']}")
                    print(f"  Tools Successful: {test_result['tools_successful']}")
                
                if 'scenarios_tested' in test_result:
                    print(f"  Error Scenarios: {test_result['scenarios_tested']}")
                    print(f"  Scenarios Passed: {test_result['scenarios_successful']}")
                    
            else:
                print(f"  Status: FAILED")
                print(f"  Error: {test_result.get('error', 'Unknown error')}")
                print(f"  Error Type: {test_result.get('error_type', 'Unknown')}")
    
    def print_execution_summary(self):
        """Print execution summary."""
        if not self.results or not self.start_time or not self.end_time:
            return
        
        execution_time = self.end_time - self.start_time
        
        print("\n" + "=" * 70)
        print("⏱️ EXECUTION SUMMARY")
        print("=" * 70)
        print(f"Start Time: {datetime.fromtimestamp(self.start_time).strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"End Time: {datetime.fromtimestamp(self.end_time).strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Duration: {execution_time:.2f} seconds")
        
        summary = self.results.get('summary', {})
        print(f"Total Tests: {summary.get('total_tests', 0)}")
        print(f"Successful: {summary.get('successful_tests', 0)}")
        print(f"Failed: {summary.get('failed_tests', 0)}")
        print(f"Skipped: {summary.get('skipped_tests', 0)}")
        print(f"Success Rate: {summary.get('success_rate', 0):.1f}%")
        
        overall_result = "PASS" if summary.get('overall_success', False) else "FAIL"
        result_icon = "🎉" if summary.get('overall_success', False) else "💥"
        print(f"\nOverall Result: {result_icon} {overall_result}")
    
    def save_results(self, filename: str = None):
        """Save test results to file.
        
        Args:
            filename: Output filename (optional).
        """
        if not self.results:
            print("❌ No results to save")
            return
        
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"e2e_auth_test_results_{timestamp}.json"
        
        try:
            # Add execution metadata
            if self.start_time and self.end_time:
                self.results['execution_metadata'] = {
                    'start_time': self.start_time,
                    'end_time': self.end_time,
                    'duration_seconds': self.end_time - self.start_time,
                    'start_time_iso': datetime.fromtimestamp(self.start_time).isoformat(),
                    'end_time_iso': datetime.fromtimestamp(self.end_time).isoformat()
                }
            
            with open(filename, 'w') as f:
                json.dump(self.results, f, indent=2, default=str)
            
            print(f"\n💾 Test results saved to: {filename}")
            
        except Exception as e:
            print(f"❌ Failed to save results: {e}")


async def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Run End-to-End Authentication Tests for Restaurant Search MCP'
    )
    parser.add_argument('--config', default='cognito_config.json',
                       help='Cognito configuration file (default: cognito_config.json)')
    parser.add_argument('--username', help='Test username (overrides config)')
    parser.add_argument('--password', help='Test password (overrides default)')
    parser.add_argument('--output', help='Output file for results (auto-generated if not specified)')
    parser.add_argument('--skip-prereq', action='store_true',
                       help='Skip prerequisite checks')
    parser.add_argument('--detailed', action='store_true',
                       help='Show detailed test results')
    
    args = parser.parse_args()
    
    runner = E2EAuthTestRunner()
    
    try:
        # Print banner
        runner.print_banner()
        
        # Check prerequisites
        if not args.skip_prereq:
            checks = runner.check_prerequisites()
            if not runner.can_run_tests(checks):
                print("❌ Prerequisites not met. Cannot run tests.")
                return 1
        
        # Run tests
        results = await runner.run_tests(
            config_file=args.config,
            username=args.username,
            password=args.password
        )
        
        # Print results
        if args.detailed:
            runner.print_detailed_results()
        
        runner.print_execution_summary()
        
        # Save results
        runner.save_results(args.output)
        
        # Return appropriate exit code
        return 0 if results['summary']['overall_success'] else 1
        
    except KeyboardInterrupt:
        print("\n⏹️ Tests interrupted by user")
        return 130
    except Exception as e:
        print(f"💥 Test runner failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))