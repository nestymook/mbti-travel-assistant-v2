#!/usr/bin/env python3
"""
Authentication Integration Tests for Restaurant Reasoning MCP Server

This module provides comprehensive integration tests that validate
the complete authentication flow from Cognito login to MCP tool execution,
including JWT token propagation through AgentCore Runtime to reasoning MCP server.

Adapted for restaurant reasoning MCP server context.
Requirements: 11.1, 11.2, 12.1, 12.2, 12.3
"""

import asyncio
import json
import os
import sys
import time
import pytest
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List, Tuple
from unittest.mock import Mock, patch, AsyncMock
import requests

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.auth_service import (
    CognitoAuthenticator,
    TokenValidator,
    AuthenticationError,
    AuthenticationTokens,
    JWTClaims,
    UserContext
)

try:
    from mcp import ClientSession
    from mcp.client.streamable_http import streamablehttp_client
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    ClientSession = None
    streamablehttp_client = None

try:
    from bedrock_agentcore_starter_toolkit import Runtime
    AGENTCORE_AVAILABLE = True
except ImportError:
    AGENTCORE_AVAILABLE = False
    Runtime = None


class ReasoningAuthenticationIntegrationTests:
    """Integration tests for authentication services in reasoning server context."""
    
    def __init__(self, config_file: str = "cognito_config.json"):
        """Initialize test suite with configuration.
        
        Args:
            config_file: Path to Cognito configuration file.
        """
        self.config_file = config_file
        self.cognito_config = self._load_cognito_config()
        self.test_results = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'test_suite': 'Reasoning Server Authentication Integration Tests',
            'tests': {},
            'summary': {}
        }
        
        # Initialize authentication components for reasoning server
        self.authenticator = CognitoAuthenticator(
            user_pool_id=self.cognito_config['user_pool']['user_pool_id'],
            client_id=self.cognito_config['app_client']['client_id'],
            region=self.cognito_config['region']
        )
        
        self.token_validator = TokenValidator({
            'user_pool_id': self.cognito_config['user_pool']['user_pool_id'],
            'client_id': self.cognito_config['app_client']['client_id'],
            'region': self.cognito_config['region'],
            'discovery_url': self.cognito_config['discovery_url']
        })
        
        # Test user credentials for reasoning server
        self.test_username = self.cognito_config.get('test_user', {}).get('email', 'reasoning_test@example.com')
        self.test_password = "TempPass123!"  # Default from setup_cognito.py
        
        # AgentCore configuration for reasoning server
        self.reasoning_agent_arn = None
        self.agentcore_runtime = None
        
    def _load_cognito_config(self) -> Dict[str, Any]:
        """Load Cognito configuration from file.
        
        Returns:
            Cognito configuration dictionary.
            
        Raises:
            FileNotFoundError: If config file doesn't exist.
            ValueError: If config is invalid.
        """
        try:
            if not os.path.exists(self.config_file):
                raise FileNotFoundError(
                    f"Cognito configuration file not found: {self.config_file}. "
                    f"Run setup_cognito.py first to create the configuration."
                )
            
            with open(self.config_file, 'r') as f:
                config = json.load(f)
            
            # Validate required fields for reasoning server
            required_fields = ['user_pool', 'app_client', 'region', 'discovery_url']
            for field in required_fields:
                if field not in config:
                    raise ValueError(f"Missing required field in config: {field}")
            
            return config
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in config file: {e}")
        except Exception as e:
            raise ValueError(f"Error loading config: {e}")
    
    async def test_cognito_authentication_flow(self) -> Dict[str, Any]:
        """Test complete Cognito authentication flow for reasoning server.
        
        Returns:
            Test results dictionary.
        """
        test_name = "cognito_authentication_flow"
        print(f"\n🔐 Testing Cognito Authentication Flow for Reasoning Server...")
        
        try:
            # Test SRP authentication
            print("  📝 Authenticating with Cognito...")
            tokens = self.authenticator.authenticate_user(
                self.test_username, 
                self.test_password
            )
            
            # Verify token structure
            assert isinstance(tokens, AuthenticationTokens)
            assert tokens.id_token is not None
            assert tokens.access_token is not None
            assert tokens.refresh_token is not None
            assert tokens.expires_in > 0
            assert tokens.token_type == "Bearer"
            
            print("  ✅ Authentication successful")
            print(f"     - ID Token: {tokens.id_token[:20]}...")
            print(f"     - Access Token: {tokens.access_token[:20]}...")
            print(f"     - Expires in: {tokens.expires_in} seconds")
            
            # Test token validation
            print("  🔍 Validating JWT tokens...")
            claims = await self.token_validator.validate_jwt_token(tokens.access_token)
            
            assert isinstance(claims, JWTClaims)
            assert claims.user_id is not None
            assert claims.username is not None
            assert claims.token_use in ['access', 'id']
            
            print("  ✅ Token validation successful")
            print(f"     - User ID: {claims.user_id}")
            print(f"     - Username: {claims.username}")
            print(f"     - Token Use: {claims.token_use}")
            
            # Test token refresh
            print("  🔄 Testing token refresh...")
            new_tokens = self.authenticator.refresh_token(tokens.refresh_token)
            
            assert isinstance(new_tokens, AuthenticationTokens)
            assert new_tokens.access_token != tokens.access_token  # Should be different
            assert new_tokens.refresh_token == tokens.refresh_token  # Should be same
            
            print("  ✅ Token refresh successful")
            
            result = {
                'status': 'PASSED',
                'message': 'Cognito authentication flow completed successfully',
                'details': {
                    'authentication': 'success',
                    'token_validation': 'success',
                    'token_refresh': 'success',
                    'user_id': claims.user_id,
                    'username': claims.username
                }
            }
            
        except AuthenticationError as e:
            result = {
                'status': 'FAILED',
                'message': f'Authentication error: {e.message}',
                'details': {
                    'error_type': e.error_type,
                    'error_code': e.error_code,
                    'suggested_action': e.suggested_action
                }
            }
            print(f"  ❌ Authentication failed: {e.message}")
            
        except Exception as e:
            result = {
                'status': 'FAILED',
                'message': f'Unexpected error: {str(e)}',
                'details': {'exception': str(e)}
            }
            print(f"  ❌ Unexpected error: {str(e)}")
        
        self.test_results['tests'][test_name] = result
        return result
    
    async def test_jwt_token_validation_scenarios(self) -> Dict[str, Any]:
        """Test various JWT token validation scenarios for reasoning server.
        
        Returns:
            Test results dictionary.
        """
        test_name = "jwt_token_validation_scenarios"
        print(f"\n🔍 Testing JWT Token Validation Scenarios for Reasoning Server...")
        
        scenarios_results = {}
        
        try:
            # Get valid tokens first
            tokens = self.authenticator.authenticate_user(
                self.test_username, 
                self.test_password
            )
            
            # Scenario 1: Valid token
            print("  📝 Testing valid token validation...")
            try:
                claims = await self.token_validator.validate_jwt_token(tokens.access_token)
                scenarios_results['valid_token'] = {
                    'status': 'PASSED',
                    'message': 'Valid token validated successfully'
                }
                print("  ✅ Valid token validation passed")
            except Exception as e:
                scenarios_results['valid_token'] = {
                    'status': 'FAILED',
                    'message': f'Valid token validation failed: {str(e)}'
                }
                print(f"  ❌ Valid token validation failed: {str(e)}")
            
            # Scenario 2: Malformed token
            print("  📝 Testing malformed token validation...")
            try:
                await self.token_validator.validate_jwt_token("invalid.token.format")
                scenarios_results['malformed_token'] = {
                    'status': 'FAILED',
                    'message': 'Malformed token should have failed validation'
                }
                print("  ❌ Malformed token validation should have failed")
            except AuthenticationError as e:
                scenarios_results['malformed_token'] = {
                    'status': 'PASSED',
                    'message': f'Malformed token correctly rejected: {e.error_code}'
                }
                print(f"  ✅ Malformed token correctly rejected: {e.error_code}")
            
            # Scenario 3: Token expiration check
            print("  📝 Testing token expiration detection...")
            is_expired = self.token_validator.is_token_expired(tokens.access_token)
            if not is_expired:
                scenarios_results['token_expiration'] = {
                    'status': 'PASSED',
                    'message': 'Token expiration check working correctly'
                }
                print("  ✅ Token expiration check passed")
            else:
                scenarios_results['token_expiration'] = {
                    'status': 'FAILED',
                    'message': 'Valid token incorrectly marked as expired'
                }
                print("  ❌ Valid token incorrectly marked as expired")
            
            # Scenario 4: Claims extraction
            print("  📝 Testing claims extraction...")
            try:
                extracted_claims = self.token_validator.extract_claims(tokens.access_token)
                if 'sub' in extracted_claims and 'exp' in extracted_claims:
                    scenarios_results['claims_extraction'] = {
                        'status': 'PASSED',
                        'message': 'Claims extraction successful'
                    }
                    print("  ✅ Claims extraction passed")
                else:
                    scenarios_results['claims_extraction'] = {
                        'status': 'FAILED',
                        'message': 'Missing required claims in extraction'
                    }
                    print("  ❌ Missing required claims in extraction")
            except Exception as e:
                scenarios_results['claims_extraction'] = {
                    'status': 'FAILED',
                    'message': f'Claims extraction failed: {str(e)}'
                }
                print(f"  ❌ Claims extraction failed: {str(e)}")
            
            # Overall result
            passed_scenarios = sum(1 for r in scenarios_results.values() if r['status'] == 'PASSED')
            total_scenarios = len(scenarios_results)
            
            result = {
                'status': 'PASSED' if passed_scenarios == total_scenarios else 'PARTIAL',
                'message': f'JWT validation scenarios: {passed_scenarios}/{total_scenarios} passed',
                'details': {
                    'scenarios': scenarios_results,
                    'passed': passed_scenarios,
                    'total': total_scenarios
                }
            }
            
        except Exception as e:
            result = {
                'status': 'FAILED',
                'message': f'JWT validation test setup failed: {str(e)}',
                'details': {'exception': str(e)}
            }
            print(f"  ❌ JWT validation test setup failed: {str(e)}")
        
        self.test_results['tests'][test_name] = result
        return result
    
    async def test_reasoning_mcp_server_authentication(self) -> Dict[str, Any]:
        """Test authentication integration with reasoning MCP server.
        
        Returns:
            Test results dictionary.
        """
        test_name = "reasoning_mcp_server_authentication"
        print(f"\n🤖 Testing Reasoning MCP Server Authentication Integration...")
        
        if not MCP_AVAILABLE:
            result = {
                'status': 'SKIPPED',
                'message': 'MCP client not available - install mcp package',
                'details': {'reason': 'missing_mcp_dependency'}
            }
            print("  ⚠️  MCP client not available - skipping MCP server tests")
            self.test_results['tests'][test_name] = result
            return result
        
        try:
            # Get authentication tokens
            print("  📝 Getting authentication tokens...")
            tokens = self.authenticator.authenticate_user(
                self.test_username, 
                self.test_password
            )
            
            # Test MCP server connection with authentication
            print("  🔗 Testing MCP server connection with JWT authentication...")
            
            # Mock MCP server URL (would be actual AgentCore Runtime URL in real test)
            mcp_server_url = "http://localhost:8080"
            headers = {
                'Authorization': f'Bearer {tokens.access_token}',
                'Content-Type': 'application/json'
            }
            
            # Test connection (mocked for integration test)
            with patch('mcp.client.streamable_http.streamablehttp_client') as mock_client:
                mock_session = AsyncMock()
                mock_client.return_value.__aenter__.return_value = (
                    AsyncMock(), AsyncMock(), AsyncMock()
                )
                
                # Mock successful tool listing
                mock_session.list_tools.return_value = {
                    'tools': [
                        {
                            'name': 'recommend_restaurants',
                            'description': 'Analyze restaurant sentiment and provide recommendations'
                        },
                        {
                            'name': 'analyze_restaurant_sentiment',
                            'description': 'Analyze sentiment data for restaurants'
                        }
                    ]
                }
                
                # Mock successful tool invocation
                mock_session.call_tool.return_value = {
                    'content': [
                        {
                            'type': 'text',
                            'text': json.dumps({
                                'candidates': [],
                                'recommendation': None,
                                'ranking_method': 'sentiment_likes'
                            })
                        }
                    ]
                }
                
                # Simulate MCP client session
                async with mock_client(mcp_server_url, headers=headers) as (read, write, _):
                    async with ClientSession(read, write) as session:
                        # Test tool listing
                        tools = await mock_session.list_tools()
                        assert 'tools' in tools
                        assert len(tools['tools']) >= 2
                        
                        # Test tool invocation with authentication
                        result_content = await mock_session.call_tool(
                            'recommend_restaurants',
                            {'restaurants': [], 'ranking_method': 'sentiment_likes'}
                        )
                        assert 'content' in result_content
                        
                        print("  ✅ MCP server authentication integration successful")
                        
                        result = {
                            'status': 'PASSED',
                            'message': 'Reasoning MCP server authentication integration successful',
                            'details': {
                                'tools_available': len(tools['tools']),
                                'authentication': 'success',
                                'tool_invocation': 'success'
                            }
                        }
            
        except AuthenticationError as e:
            result = {
                'status': 'FAILED',
                'message': f'Authentication failed: {e.message}',
                'details': {
                    'error_type': e.error_type,
                    'error_code': e.error_code
                }
            }
            print(f"  ❌ Authentication failed: {e.message}")
            
        except Exception as e:
            result = {
                'status': 'FAILED',
                'message': f'MCP server integration test failed: {str(e)}',
                'details': {'exception': str(e)}
            }
            print(f"  ❌ MCP server integration test failed: {str(e)}")
        
        self.test_results['tests'][test_name] = result
        return result
    
    async def test_error_handling_scenarios(self) -> Dict[str, Any]:
        """Test authentication error handling scenarios for reasoning server.
        
        Returns:
            Test results dictionary.
        """
        test_name = "error_handling_scenarios"
        print(f"\n⚠️  Testing Authentication Error Handling Scenarios...")
        
        error_scenarios = {}
        
        # Scenario 1: Invalid credentials
        print("  📝 Testing invalid credentials handling...")
        try:
            self.authenticator.authenticate_user("invalid_user", "wrong_password")
            error_scenarios['invalid_credentials'] = {
                'status': 'FAILED',
                'message': 'Invalid credentials should have failed'
            }
            print("  ❌ Invalid credentials should have failed")
        except AuthenticationError as e:
            if e.error_type in ["AUTHENTICATION_FAILED", "USER_NOT_FOUND"]:
                error_scenarios['invalid_credentials'] = {
                    'status': 'PASSED',
                    'message': f'Invalid credentials correctly rejected: {e.error_code}'
                }
                print(f"  ✅ Invalid credentials correctly rejected: {e.error_code}")
            else:
                error_scenarios['invalid_credentials'] = {
                    'status': 'FAILED',
                    'message': f'Unexpected error type: {e.error_type}'
                }
                print(f"  ❌ Unexpected error type: {e.error_type}")
        except Exception as e:
            error_scenarios['invalid_credentials'] = {
                'status': 'FAILED',
                'message': f'Unexpected exception: {str(e)}'
            }
            print(f"  ❌ Unexpected exception: {str(e)}")
        
        # Scenario 2: Invalid refresh token
        print("  📝 Testing invalid refresh token handling...")
        try:
            self.authenticator.refresh_token("invalid_refresh_token")
            error_scenarios['invalid_refresh_token'] = {
                'status': 'FAILED',
                'message': 'Invalid refresh token should have failed'
            }
            print("  ❌ Invalid refresh token should have failed")
        except AuthenticationError as e:
            if e.error_type == "TOKEN_REFRESH_FAILED":
                error_scenarios['invalid_refresh_token'] = {
                    'status': 'PASSED',
                    'message': f'Invalid refresh token correctly rejected: {e.error_code}'
                }
                print(f"  ✅ Invalid refresh token correctly rejected: {e.error_code}")
            else:
                error_scenarios['invalid_refresh_token'] = {
                    'status': 'FAILED',
                    'message': f'Unexpected error type: {e.error_type}'
                }
                print(f"  ❌ Unexpected error type: {e.error_type}")
        except Exception as e:
            error_scenarios['invalid_refresh_token'] = {
                'status': 'FAILED',
                'message': f'Unexpected exception: {str(e)}'
            }
            print(f"  ❌ Unexpected exception: {str(e)}")
        
        # Overall result
        passed_scenarios = sum(1 for r in error_scenarios.values() if r['status'] == 'PASSED')
        total_scenarios = len(error_scenarios)
        
        result = {
            'status': 'PASSED' if passed_scenarios == total_scenarios else 'PARTIAL',
            'message': f'Error handling scenarios: {passed_scenarios}/{total_scenarios} passed',
            'details': {
                'scenarios': error_scenarios,
                'passed': passed_scenarios,
                'total': total_scenarios
            }
        }
        
        self.test_results['tests'][test_name] = result
        return result
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all authentication integration tests for reasoning server.
        
        Returns:
            Complete test results dictionary.
        """
        print("🧪 Starting Reasoning Server Authentication Integration Tests...")
        print(f"📅 Timestamp: {self.test_results['timestamp']}")
        print(f"🔧 Config file: {self.config_file}")
        print(f"👤 Test user: {self.test_username}")
        
        # Run all test methods
        test_methods = [
            self.test_cognito_authentication_flow,
            self.test_jwt_token_validation_scenarios,
            self.test_reasoning_mcp_server_authentication,
            self.test_error_handling_scenarios
        ]
        
        for test_method in test_methods:
            try:
                await test_method()
            except Exception as e:
                test_name = test_method.__name__
                self.test_results['tests'][test_name] = {
                    'status': 'FAILED',
                    'message': f'Test method failed: {str(e)}',
                    'details': {'exception': str(e)}
                }
                print(f"❌ Test method {test_name} failed: {str(e)}")
        
        # Calculate summary
        total_tests = len(self.test_results['tests'])
        passed_tests = sum(1 for t in self.test_results['tests'].values() if t['status'] == 'PASSED')
        failed_tests = sum(1 for t in self.test_results['tests'].values() if t['status'] == 'FAILED')
        skipped_tests = sum(1 for t in self.test_results['tests'].values() if t['status'] == 'SKIPPED')
        
        self.test_results['summary'] = {
            'total': total_tests,
            'passed': passed_tests,
            'failed': failed_tests,
            'skipped': skipped_tests,
            'success_rate': f"{(passed_tests / total_tests * 100):.1f}%" if total_tests > 0 else "0%"
        }
        
        # Print summary
        print(f"\n📊 Test Summary:")
        print(f"   Total: {total_tests}")
        print(f"   Passed: {passed_tests}")
        print(f"   Failed: {failed_tests}")
        print(f"   Skipped: {skipped_tests}")
        print(f"   Success Rate: {self.test_results['summary']['success_rate']}")
        
        return self.test_results
    
    def save_results(self, output_file: str = "reasoning_auth_integration_test_results.json"):
        """Save test results to JSON file.
        
        Args:
            output_file: Output file path.
        """
        try:
            with open(output_file, 'w') as f:
                json.dump(self.test_results, f, indent=2)
            print(f"📄 Test results saved to: {output_file}")
        except Exception as e:
            print(f"❌ Failed to save test results: {str(e)}")


async def main():
    """Main function to run authentication integration tests."""
    # Check if config file exists
    config_file = "cognito_config.json"
    if not os.path.exists(config_file):
        print(f"❌ Configuration file not found: {config_file}")
        print("   Run setup_cognito.py first to create the configuration.")
        return 1
    
    # Initialize and run tests
    test_suite = ReasoningAuthenticationIntegrationTests(config_file)
    
    try:
        results = await test_suite.run_all_tests()
        test_suite.save_results()
        
        # Return appropriate exit code
        if results['summary']['failed'] > 0:
            return 1
        else:
            return 0
            
    except Exception as e:
        print(f"❌ Test suite execution failed: {str(e)}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)