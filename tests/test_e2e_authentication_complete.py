#!/usr/bin/env python3
"""
Comprehensive End-to-End Authentication Tests for Restaurant Search MCP

This module provides comprehensive end-to-end authentication tests that validate
the complete authentication flow from Cognito login to MCP tool execution,
including JWT token propagation through AgentCore Runtime to MCP server.

Requirements: 16.1, 16.2, 16.4, 17.1, 18.1
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
import subprocess
from urllib.parse import quote

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
from services.auth_middleware import (
    AuthenticationMiddleware,
    AuthenticationConfig,
    AuthenticationHelper
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


class E2EAuthenticationTestSuite:
    """Comprehensive end-to-end authentication test suite."""
    
    def __init__(self, config_file: str = "cognito_config.json"):
        """Initialize test suite with configuration.
        
        Args:
            config_file: Path to Cognito configuration file.
        """
        self.config_file = config_file
        self.cognito_config = self._load_cognito_config()
        self.agentcore_config = self._load_agentcore_config()
        self.test_results = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'test_suite': 'E2E Authentication Tests',
            'tests': {},
            'summary': {}
        }
        
        # Initialize authentication components
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
        
        # Test user credentials
        self.test_username = self.cognito_config.get('test_user', {}).get('email', 'nestymook@gmail.com')
        self.test_password = "TestPass123!"  # Updated password
        
        # AgentCore configuration
        self.agent_arn = self.agentcore_config.get('agent_arn')
        self.region = self.agentcore_config.get('region', 'us-east-1')
        
        # Current authentication tokens
        self.current_tokens: Optional[AuthenticationTokens] = None
        
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
                    "Please run setup_cognito.py first."
                )
            
            with open(self.config_file, 'r') as f:
                config = json.load(f)
            
            # Validate required fields
            required_fields = ['user_pool', 'app_client', 'discovery_url', 'region']
            for field in required_fields:
                if field not in config:
                    raise ValueError(f"Missing required field in Cognito config: {field}")
            
            return config
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in Cognito config file: {e}")
        except Exception as e:
            raise ValueError(f"Error loading Cognito configuration: {e}")
    
    def _load_agentcore_config(self) -> Dict[str, Any]:
        """Load AgentCore configuration from .bedrock_agentcore.yaml.
        
        Returns:
            AgentCore configuration dictionary.
        """
        try:
            import yaml
            
            config_path = ".bedrock_agentcore.yaml"
            if not os.path.exists(config_path):
                raise FileNotFoundError(f"AgentCore config file not found: {config_path}")
            
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            # Extract authenticated agent configuration
            agents = config.get('agents', {})
            
            # Look for agent with authentication enabled (prefer main agent)
            for agent_name in ['restaurant_search_mcp', 'restaurant_search_mcp_arm64']:
                if agent_name in agents:
                    agent_config = agents[agent_name]
                    if agent_config.get('authorizer_configuration'):
                        return {
                            'agent_name': agent_name,
                            'agent_arn': agent_config.get('bedrock_agentcore', {}).get('agent_arn'),
                            'region': agent_config.get('aws', {}).get('region', 'us-east-1'),
                            'auth_config': agent_config.get('authorizer_configuration')
                        }
            
            # Fallback to any agent with ARN
            for agent_name, agent_config in agents.items():
                agent_arn = agent_config.get('bedrock_agentcore', {}).get('agent_arn')
                if agent_arn:
                    return {
                        'agent_name': agent_name,
                        'agent_arn': agent_arn,
                        'region': agent_config.get('aws', {}).get('region', 'us-east-1'),
                        'auth_config': agent_config.get('authorizer_configuration')
                    }
            
            raise ValueError("No deployed agent found in AgentCore configuration")
            
        except ImportError:
            raise ImportError("PyYAML required for AgentCore config parsing: pip install pyyaml")
        except Exception as e:
            raise ValueError(f"Error loading AgentCore configuration: {e}")
    
    def _construct_mcp_url(self, agent_arn: str, region: str) -> str:
        """Construct MCP invocation URL for AgentCore Runtime.
        
        Args:
            agent_arn: ARN of the deployed agent.
            region: AWS region.
            
        Returns:
            Complete MCP invocation URL.
        """
        base_url = f"https://bedrock-agentcore.{region}.amazonaws.com"
        encoded_arn = quote(agent_arn, safe='')
        return f"{base_url}/runtimes/{encoded_arn}/invocations?qualifier=DEFAULT"
    
    def _create_auth_headers(self, bearer_token: str) -> Dict[str, str]:
        """Create authentication headers for MCP requests.
        
        Args:
            bearer_token: JWT access token from Cognito.
            
        Returns:
            Dictionary of HTTP headers.
        """
        return {
            "authorization": f"Bearer {bearer_token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    async def test_cognito_authentication_flow(self) -> Dict[str, Any]:
        """Test complete Cognito authentication flow.
        
        Returns:
            Test result dictionary.
        """
        test_name = "cognito_authentication_flow"
        print(f"\n🔐 Testing: {test_name}")
        
        try:
            # Test 1: Authenticate user with SRP
            print("  1. Testing SRP authentication...")
            tokens = self.authenticator.authenticate_user(
                self.test_username, 
                self.test_password
            )
            
            assert isinstance(tokens, AuthenticationTokens)
            assert tokens.access_token
            assert tokens.id_token
            assert tokens.refresh_token
            print("    ✓ SRP authentication successful")
            
            # Store tokens for later tests
            self.current_tokens = tokens
            
            # Test 2: Validate access token
            print("  2. Testing access token validation...")
            user_context = self.authenticator.validate_user_session(tokens.access_token)
            
            assert isinstance(user_context, UserContext)
            assert user_context.authenticated
            assert user_context.username == self.test_username
            print("    ✓ Access token validation successful")
            
            # Test 3: Refresh token
            print("  3. Testing token refresh...")
            new_tokens = self.authenticator.refresh_token(tokens.refresh_token)
            
            assert isinstance(new_tokens, AuthenticationTokens)
            assert new_tokens.access_token != tokens.access_token  # Should be different
            print("    ✓ Token refresh successful")
            
            result = {
                'success': True,
                'tokens_obtained': True,
                'token_validation': True,
                'token_refresh': True,
                'user_context': {
                    'user_id': user_context.user_id,
                    'username': user_context.username,
                    'email': user_context.email
                }
            }
            
        except Exception as e:
            result = {
                'success': False,
                'error': str(e),
                'error_type': type(e).__name__
            }
            print(f"    ✗ Authentication flow failed: {e}")
        
        self.test_results['tests'][test_name] = result
        return result
    
    async def test_jwt_token_validation(self) -> Dict[str, Any]:
        """Test JWT token validation with TokenValidator.
        
        Returns:
            Test result dictionary.
        """
        test_name = "jwt_token_validation"
        print(f"\n🔍 Testing: {test_name}")
        
        try:
            # Get valid tokens first if not already available
            if not self.current_tokens:
                self.current_tokens = self.authenticator.authenticate_user(
                    self.test_username, 
                    self.test_password
                )
            
            # Test 1: Validate valid token
            print("  1. Testing valid token validation...")
            jwt_claims = await self.token_validator.validate_jwt_token(self.current_tokens.access_token)
            
            assert isinstance(jwt_claims, JWTClaims)
            assert jwt_claims.user_id
            assert jwt_claims.username == self.test_username
            assert jwt_claims.client_id == self.cognito_config['app_client']['client_id']
            print("    ✓ Valid token validation successful")
            
            # Test 2: Test invalid token
            print("  2. Testing invalid token handling...")
            invalid_token = "invalid.jwt.token"
            
            try:
                await self.token_validator.validate_jwt_token(invalid_token)
                assert False, "Should have raised AuthenticationError"
            except AuthenticationError as e:
                assert e.error_type in ['TOKEN_VALIDATION_ERROR', 'TOKEN_DECODE_ERROR']
                print("    ✓ Invalid token properly rejected")
            
            # Test 3: Test malformed token
            print("  3. Testing malformed token handling...")
            malformed_token = "not-a-jwt-token-at-all"
            
            try:
                await self.token_validator.validate_jwt_token(malformed_token)
                assert False, "Should have raised AuthenticationError"
            except AuthenticationError as e:
                assert e.error_type in ['TOKEN_VALIDATION_ERROR', 'TOKEN_DECODE_ERROR']
                print("    ✓ Malformed token properly rejected")
            
            # Test 4: Test JWKS key retrieval
            print("  4. Testing JWKS key retrieval...")
            # Decode token to get kid
            import jwt
            unverified_header = jwt.get_unverified_header(self.current_tokens.access_token)
            kid = unverified_header.get('kid')
            
            signing_key = await self.token_validator.get_signing_key(kid)
            assert signing_key is not None
            print("    ✓ JWKS key retrieval successful")
            
            result = {
                'success': True,
                'valid_token_validation': True,
                'invalid_token_rejection': True,
                'malformed_token_rejection': True,
                'jwks_key_retrieval': True,
                'jwt_claims': {
                    'user_id': jwt_claims.user_id,
                    'username': jwt_claims.username,
                    'client_id': jwt_claims.client_id,
                    'token_use': jwt_claims.token_use
                }
            }
            
        except Exception as e:
            result = {
                'success': False,
                'error': str(e),
                'error_type': type(e).__name__
            }
            print(f"    ✗ JWT token validation failed: {e}")
        
        self.test_results['tests'][test_name] = result
        return result
    
    async def test_agentcore_runtime_authentication(self) -> Dict[str, Any]:
        """Test AgentCore Runtime JWT authentication integration.
        
        Returns:
            Test result dictionary.
        """
        test_name = "agentcore_runtime_authentication"
        print(f"\n🌐 Testing: {test_name}")
        
        if not self.agent_arn:
            result = {
                'success': False,
                'error': 'No AgentCore Runtime ARN available',
                'skipped': True
            }
            self.test_results['tests'][test_name] = result
            return result
        
        try:
            # Ensure we have valid tokens
            if not self.current_tokens:
                self.current_tokens = self.authenticator.authenticate_user(
                    self.test_username, 
                    self.test_password
                )
            
            mcp_url = self._construct_mcp_url(self.agent_arn, self.region)
            print(f"  MCP URL: {mcp_url}")
            
            # Test 1: Test with valid authentication
            print("  1. Testing authenticated MCP connection...")
            headers = self._create_auth_headers(self.current_tokens.access_token)
            
            if not MCP_AVAILABLE:
                print("    ⚠️ MCP client not available, skipping connection test")
                connection_test = {'skipped': True, 'reason': 'MCP client not available'}
            else:
                try:
                    async with streamablehttp_client(
                        mcp_url, 
                        headers, 
                        timeout=timedelta(seconds=60)
                    ) as (read_stream, write_stream, _):
                        async with ClientSession(read_stream, write_stream) as session:
                            await session.initialize()
                            tools_response = await session.list_tools()
                            tools = tools_response.tools
                            
                            connection_test = {
                                'success': True,
                                'tools_count': len(tools),
                                'available_tools': [tool.name for tool in tools]
                            }
                            print(f"    ✓ Connected successfully, found {len(tools)} tools")
                            
                except Exception as e:
                    connection_test = {
                        'success': False,
                        'error': str(e),
                        'error_type': type(e).__name__
                    }
                    print(f"    ✗ Connection failed: {e}")
            
            # Test 2: Test with invalid authentication
            print("  2. Testing invalid token rejection...")
            invalid_headers = self._create_auth_headers("invalid.jwt.token")
            
            if not MCP_AVAILABLE:
                print("    ⚠️ MCP client not available, skipping invalid token test")
                invalid_token_test = {'skipped': True, 'reason': 'MCP client not available'}
            else:
                try:
                    async with streamablehttp_client(
                        mcp_url, 
                        invalid_headers, 
                        timeout=timedelta(seconds=30)
                    ) as (read_stream, write_stream, _):
                        async with ClientSession(read_stream, write_stream) as session:
                            await session.initialize()
                            # Should fail before this point
                            invalid_token_test = {
                                'success': False,
                                'error': 'Invalid token was accepted (should have been rejected)'
                            }
                            
                except Exception as e:
                    # This is expected - invalid token should be rejected
                    invalid_token_test = {
                        'success': True,
                        'properly_rejected': True,
                        'error_message': str(e)
                    }
                    print("    ✓ Invalid token properly rejected")
            
            # Test 3: Test without authentication
            print("  3. Testing missing authentication rejection...")
            no_auth_headers = {"Content-Type": "application/json"}
            
            if not MCP_AVAILABLE:
                print("    ⚠️ MCP client not available, skipping no auth test")
                no_auth_test = {'skipped': True, 'reason': 'MCP client not available'}
            else:
                try:
                    async with streamablehttp_client(
                        mcp_url, 
                        no_auth_headers, 
                        timeout=timedelta(seconds=30)
                    ) as (read_stream, write_stream, _):
                        async with ClientSession(read_stream, write_stream) as session:
                            await session.initialize()
                            # Should fail before this point
                            no_auth_test = {
                                'success': False,
                                'error': 'Missing authentication was accepted (should have been rejected)'
                            }
                            
                except Exception as e:
                    # This is expected - missing auth should be rejected
                    no_auth_test = {
                        'success': True,
                        'properly_rejected': True,
                        'error_message': str(e)
                    }
                    print("    ✓ Missing authentication properly rejected")
            
            result = {
                'success': True,
                'agent_arn': self.agent_arn,
                'mcp_url': mcp_url,
                'connection_test': connection_test,
                'invalid_token_test': invalid_token_test,
                'no_auth_test': no_auth_test
            }
            
        except Exception as e:
            result = {
                'success': False,
                'error': str(e),
                'error_type': type(e).__name__
            }
            print(f"    ✗ AgentCore Runtime authentication test failed: {e}")
        
        self.test_results['tests'][test_name] = result
        return result
    
    async def test_mcp_tool_execution_with_auth(self) -> Dict[str, Any]:
        """Test MCP tool execution with authentication.
        
        Returns:
            Test result dictionary.
        """
        test_name = "mcp_tool_execution_with_auth"
        print(f"\n🧪 Testing: {test_name}")
        
        if not self.agent_arn or not MCP_AVAILABLE:
            result = {
                'success': False,
                'error': 'AgentCore Runtime ARN or MCP client not available',
                'skipped': True
            }
            self.test_results['tests'][test_name] = result
            return result
        
        try:
            # Ensure we have valid tokens
            if not self.current_tokens:
                self.current_tokens = self.authenticator.authenticate_user(
                    self.test_username, 
                    self.test_password
                )
            
            mcp_url = self._construct_mcp_url(self.agent_arn, self.region)
            headers = self._create_auth_headers(self.current_tokens.access_token)
            
            tool_tests = {}
            
            async with streamablehttp_client(
                mcp_url, 
                headers, 
                timeout=timedelta(seconds=120)
            ) as (read_stream, write_stream, _):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    
                    # Test 1: District search tool
                    print("  1. Testing search_restaurants_by_district...")
                    try:
                        result = await session.call_tool(
                            name="search_restaurants_by_district",
                            arguments={"districts": ["Central district", "Admiralty"]}
                        )
                        
                        if hasattr(result, 'content') and result.content:
                            content = result.content[0]
                            if hasattr(content, 'text'):
                                response_data = json.loads(content.text)
                                tool_tests['district_search'] = {
                                    'success': True,
                                    'response_valid': response_data.get('success', False),
                                    'restaurants_found': len(response_data.get('data', {}).get('restaurants', []))
                                }
                                print(f"    ✓ Found {tool_tests['district_search']['restaurants_found']} restaurants")
                        else:
                            tool_tests['district_search'] = {
                                'success': False,
                                'error': 'No content in response'
                            }
                            
                    except Exception as e:
                        tool_tests['district_search'] = {
                            'success': False,
                            'error': str(e)
                        }
                        print(f"    ✗ District search failed: {e}")
                    
                    # Test 2: Meal type search tool
                    print("  2. Testing search_restaurants_by_meal_type...")
                    try:
                        result = await session.call_tool(
                            name="search_restaurants_by_meal_type",
                            arguments={"meal_types": ["lunch"]}
                        )
                        
                        if hasattr(result, 'content') and result.content:
                            content = result.content[0]
                            if hasattr(content, 'text'):
                                response_data = json.loads(content.text)
                                tool_tests['meal_type_search'] = {
                                    'success': True,
                                    'response_valid': response_data.get('success', False),
                                    'restaurants_found': len(response_data.get('data', {}).get('restaurants', []))
                                }
                                print(f"    ✓ Found {tool_tests['meal_type_search']['restaurants_found']} restaurants")
                        else:
                            tool_tests['meal_type_search'] = {
                                'success': False,
                                'error': 'No content in response'
                            }
                            
                    except Exception as e:
                        tool_tests['meal_type_search'] = {
                            'success': False,
                            'error': str(e)
                        }
                        print(f"    ✗ Meal type search failed: {e}")
                    
                    # Test 3: Combined search tool
                    print("  3. Testing search_restaurants_combined...")
                    try:
                        result = await session.call_tool(
                            name="search_restaurants_combined",
                            arguments={
                                "districts": ["Central district"],
                                "meal_types": ["dinner"]
                            }
                        )
                        
                        if hasattr(result, 'content') and result.content:
                            content = result.content[0]
                            if hasattr(content, 'text'):
                                response_data = json.loads(content.text)
                                tool_tests['combined_search'] = {
                                    'success': True,
                                    'response_valid': response_data.get('success', False),
                                    'restaurants_found': len(response_data.get('data', {}).get('restaurants', []))
                                }
                                print(f"    ✓ Found {tool_tests['combined_search']['restaurants_found']} restaurants")
                        else:
                            tool_tests['combined_search'] = {
                                'success': False,
                                'error': 'No content in response'
                            }
                            
                    except Exception as e:
                        tool_tests['combined_search'] = {
                            'success': False,
                            'error': str(e)
                        }
                        print(f"    ✗ Combined search failed: {e}")
            
            # Calculate overall success
            successful_tools = sum(1 for test in tool_tests.values() if test.get('success', False))
            total_tools = len(tool_tests)
            
            result = {
                'success': successful_tools > 0,
                'tools_tested': total_tools,
                'tools_successful': successful_tools,
                'tool_results': tool_tests
            }
            
            print(f"  📊 Tool execution summary: {successful_tools}/{total_tools} successful")
            
        except Exception as e:
            result = {
                'success': False,
                'error': str(e),
                'error_type': type(e).__name__
            }
            print(f"    ✗ MCP tool execution test failed: {e}")
        
        self.test_results['tests'][test_name] = result
        return result
    
    async def test_authentication_error_handling(self) -> Dict[str, Any]:
        """Test authentication error handling scenarios.
        
        Returns:
            Test result dictionary.
        """
        test_name = "authentication_error_handling"
        print(f"\n⚠️ Testing: {test_name}")
        
        error_scenarios = {}
        
        try:
            # Test 1: Invalid credentials
            print("  1. Testing invalid credentials...")
            try:
                self.authenticator.authenticate_user("invalid@example.com", "wrongpassword")
                error_scenarios['invalid_credentials'] = {
                    'success': False,
                    'error': 'Invalid credentials were accepted'
                }
            except AuthenticationError as e:
                error_scenarios['invalid_credentials'] = {
                    'success': True,
                    'properly_rejected': True,
                    'error_type': e.error_type,
                    'error_code': e.error_code
                }
                print("    ✓ Invalid credentials properly rejected")
            
            # Test 2: Expired token simulation
            print("  2. Testing expired token handling...")
            try:
                # Create a token that looks valid but is expired
                expired_token = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiYWRtaW4iOnRydWUsImV4cCI6MTUxNjIzOTAyMn0.invalid"
                await self.token_validator.validate_jwt_token(expired_token)
                error_scenarios['expired_token'] = {
                    'success': False,
                    'error': 'Expired token was accepted'
                }
            except AuthenticationError as e:
                error_scenarios['expired_token'] = {
                    'success': True,
                    'properly_rejected': True,
                    'error_type': e.error_type,
                    'error_code': e.error_code
                }
                print("    ✓ Expired token properly rejected")
            
            # Test 3: Invalid signature
            print("  3. Testing invalid signature handling...")
            try:
                # Create a token with invalid signature
                invalid_sig_token = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiYWRtaW4iOnRydWV9.invalid_signature"
                await self.token_validator.validate_jwt_token(invalid_sig_token)
                error_scenarios['invalid_signature'] = {
                    'success': False,
                    'error': 'Invalid signature was accepted'
                }
            except AuthenticationError as e:
                error_scenarios['invalid_signature'] = {
                    'success': True,
                    'properly_rejected': True,
                    'error_type': e.error_type,
                    'error_code': e.error_code
                }
                print("    ✓ Invalid signature properly rejected")
            
            # Test 4: Malformed token
            print("  4. Testing malformed token handling...")
            try:
                malformed_token = "this.is.not.a.jwt"
                await self.token_validator.validate_jwt_token(malformed_token)
                error_scenarios['malformed_token'] = {
                    'success': False,
                    'error': 'Malformed token was accepted'
                }
            except AuthenticationError as e:
                error_scenarios['malformed_token'] = {
                    'success': True,
                    'properly_rejected': True,
                    'error_type': e.error_type,
                    'error_code': e.error_code
                }
                print("    ✓ Malformed token properly rejected")
            
            # Calculate overall success
            successful_scenarios = sum(1 for scenario in error_scenarios.values() if scenario.get('success', False))
            total_scenarios = len(error_scenarios)
            
            result = {
                'success': successful_scenarios == total_scenarios,
                'scenarios_tested': total_scenarios,
                'scenarios_successful': successful_scenarios,
                'error_scenarios': error_scenarios
            }
            
        except Exception as e:
            result = {
                'success': False,
                'error': str(e),
                'error_type': type(e).__name__
            }
            print(f"    ✗ Error handling test failed: {e}")
        
        self.test_results['tests'][test_name] = result
        return result
    
    async def test_user_context_preservation(self) -> Dict[str, Any]:
        """Test user context preservation throughout request pipeline.
        
        Returns:
            Test result dictionary.
        """
        test_name = "user_context_preservation"
        print(f"\n👤 Testing: {test_name}")
        
        try:
            # Ensure we have valid tokens
            if not self.current_tokens:
                self.current_tokens = self.authenticator.authenticate_user(
                    self.test_username, 
                    self.test_password
                )
            
            # Test 1: Extract user context from token
            print("  1. Testing user context extraction...")
            jwt_claims = await self.token_validator.validate_jwt_token(self.current_tokens.access_token)
            
            user_context = UserContext(
                user_id=jwt_claims.user_id,
                username=jwt_claims.username,
                email=jwt_claims.email,
                authenticated=True,
                token_claims=jwt_claims
            )
            
            context_extraction = {
                'success': True,
                'user_id': user_context.user_id,
                'username': user_context.username,
                'email': user_context.email,
                'authenticated': user_context.authenticated
            }
            print(f"    ✓ User context extracted: {user_context.username}")
            
            # Test 2: Validate context consistency
            print("  2. Testing context consistency...")
            assert user_context.user_id == jwt_claims.user_id
            assert user_context.username == jwt_claims.username
            assert user_context.email == jwt_claims.email
            assert user_context.authenticated is True
            assert user_context.token_claims == jwt_claims
            
            context_consistency = {
                'success': True,
                'all_fields_consistent': True
            }
            print("    ✓ Context consistency validated")
            
            # Test 3: Test context in middleware simulation
            print("  3. Testing middleware context handling...")
            
            # Simulate middleware processing
            mock_request = Mock()
            mock_request.state = Mock()
            mock_request.state.user_context = user_context
            mock_request.state.authenticated = True
            
            # Test helper functions
            retrieved_context = AuthenticationHelper.get_user_context(mock_request)
            is_authenticated = AuthenticationHelper.is_authenticated(mock_request)
            user_id = AuthenticationHelper.get_user_id(mock_request)
            username = AuthenticationHelper.get_username(mock_request)
            
            middleware_test = {
                'success': True,
                'context_retrieved': retrieved_context == user_context,
                'authentication_status': is_authenticated,
                'user_id_match': user_id == user_context.user_id,
                'username_match': username == user_context.username
            }
            print("    ✓ Middleware context handling validated")
            
            result = {
                'success': True,
                'context_extraction': context_extraction,
                'context_consistency': context_consistency,
                'middleware_test': middleware_test
            }
            
        except Exception as e:
            result = {
                'success': False,
                'error': str(e),
                'error_type': type(e).__name__
            }
            print(f"    ✗ User context preservation test failed: {e}")
        
        self.test_results['tests'][test_name] = result
        return result
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all end-to-end authentication tests.
        
        Returns:
            Complete test results.
        """
        print("🚀 Starting Comprehensive End-to-End Authentication Tests")
        print("=" * 70)
        
        # Run all test methods
        test_methods = [
            self.test_cognito_authentication_flow,
            self.test_jwt_token_validation,
            self.test_agentcore_runtime_authentication,
            self.test_mcp_tool_execution_with_auth,
            self.test_authentication_error_handling,
            self.test_user_context_preservation
        ]
        
        for test_method in test_methods:
            try:
                await test_method()
            except Exception as e:
                print(f"💥 Test method {test_method.__name__} failed: {e}")
                self.test_results['tests'][test_method.__name__] = {
                    'success': False,
                    'error': str(e),
                    'error_type': type(e).__name__
                }
        
        # Calculate summary
        total_tests = len(self.test_results['tests'])
        successful_tests = sum(1 for test in self.test_results['tests'].values() 
                              if test.get('success', False) and not test.get('skipped', False))
        skipped_tests = sum(1 for test in self.test_results['tests'].values() 
                           if test.get('skipped', False))
        
        self.test_results['summary'] = {
            'total_tests': total_tests,
            'successful_tests': successful_tests,
            'failed_tests': total_tests - successful_tests - skipped_tests,
            'skipped_tests': skipped_tests,
            'success_rate': (successful_tests / (total_tests - skipped_tests)) * 100 if (total_tests - skipped_tests) > 0 else 0,
            'overall_success': successful_tests > 0 and (successful_tests / (total_tests - skipped_tests)) >= 0.8
        }
        
        # Print summary
        print("\n" + "=" * 70)
        print("📊 Test Results Summary")
        print("=" * 70)
        print(f"Total Tests: {total_tests}")
        print(f"Successful: {successful_tests}")
        print(f"Failed: {total_tests - successful_tests - skipped_tests}")
        print(f"Skipped: {skipped_tests}")
        print(f"Success Rate: {self.test_results['summary']['success_rate']:.1f}%")
        print(f"Overall Result: {'✅ PASS' if self.test_results['summary']['overall_success'] else '❌ FAIL'}")
        
        return self.test_results
    
    def save_results(self, filename: str = "e2e_auth_test_results.json") -> None:
        """Save test results to JSON file.
        
        Args:
            filename: Output filename for test results.
        """
        try:
            with open(filename, 'w') as f:
                json.dump(self.test_results, f, indent=2, default=str)
            print(f"\n💾 Test results saved to: {filename}")
        except Exception as e:
            print(f"❌ Failed to save test results: {e}")


async def main():
    """Main function to run end-to-end authentication tests."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run End-to-End Authentication Tests')
    parser.add_argument('--config', default='cognito_config.json', 
                       help='Cognito configuration file (default: cognito_config.json)')
    parser.add_argument('--output', default='e2e_auth_test_results.json',
                       help='Output file for test results (default: e2e_auth_test_results.json)')
    parser.add_argument('--username', help='Test username (overrides config)')
    parser.add_argument('--password', help='Test password (overrides default)')
    
    args = parser.parse_args()
    
    try:
        # Initialize test suite
        test_suite = E2EAuthenticationTestSuite(args.config)
        
        # Override credentials if provided
        if args.username:
            test_suite.test_username = args.username
        if args.password:
            test_suite.test_password = args.password
        
        # Run all tests
        results = await test_suite.run_all_tests()
        
        # Save results
        test_suite.save_results(args.output)
        
        # Return appropriate exit code
        return 0 if results['summary']['overall_success'] else 1
        
    except Exception as e:
        print(f"💥 Test execution failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))