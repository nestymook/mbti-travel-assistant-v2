#!/usr/bin/env python3
"""
Authentication Components Validation Tests

This script validates that all authentication components are working correctly
before running the full end-to-end tests. It tests individual components
in isolation to ensure they function properly.

Requirements: 16.1, 16.2, 16.4, 17.1, 18.1
"""

import asyncio
import json
import os
import sys
from datetime import datetime, timezone
from typing import Dict, Any, Optional

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


class AuthComponentValidator:
    """Validator for authentication components."""
    
    def __init__(self, config_file: str = "cognito_config.json"):
        """Initialize validator.
        
        Args:
            config_file: Path to Cognito configuration file.
        """
        self.config_file = config_file
        self.cognito_config = self._load_cognito_config()
        self.test_results = {}
        
        # Test credentials
        self.test_username = self.cognito_config.get('test_user', {}).get('email', 'nestymook@gmail.com')
        self.test_password = "TestPass123!"
    
    def _load_cognito_config(self) -> Dict[str, Any]:
        """Load Cognito configuration from file."""
        try:
            if not os.path.exists(self.config_file):
                raise FileNotFoundError(f"Config file not found: {self.config_file}")
            
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            raise ValueError(f"Error loading Cognito config: {e}")
    
    def test_cognito_authenticator_initialization(self) -> Dict[str, Any]:
        """Test CognitoAuthenticator initialization."""
        test_name = "cognito_authenticator_initialization"
        print(f"🔧 Testing: {test_name}")
        
        try:
            authenticator = CognitoAuthenticator(
                user_pool_id=self.cognito_config['user_pool']['user_pool_id'],
                client_id=self.cognito_config['app_client']['client_id'],
                region=self.cognito_config['region']
            )
            
            # Validate initialization
            assert authenticator.user_pool_id == self.cognito_config['user_pool']['user_pool_id']
            assert authenticator.client_id == self.cognito_config['app_client']['client_id']
            assert authenticator.region == self.cognito_config['region']
            assert authenticator.cognito_client is not None
            
            result = {
                'success': True,
                'user_pool_id': authenticator.user_pool_id,
                'client_id': authenticator.client_id,
                'region': authenticator.region
            }
            print("  ✅ CognitoAuthenticator initialized successfully")
            
        except Exception as e:
            result = {
                'success': False,
                'error': str(e),
                'error_type': type(e).__name__
            }
            print(f"  ❌ CognitoAuthenticator initialization failed: {e}")
        
        self.test_results[test_name] = result
        return result
    
    async def test_token_validator_initialization(self) -> Dict[str, Any]:
        """Test TokenValidator initialization."""
        test_name = "token_validator_initialization"
        print(f"🔧 Testing: {test_name}")
        
        try:
            validator_config = {
                'user_pool_id': self.cognito_config['user_pool']['user_pool_id'],
                'client_id': self.cognito_config['app_client']['client_id'],
                'region': self.cognito_config['region'],
                'discovery_url': self.cognito_config['discovery_url']
            }
            
            validator = TokenValidator(validator_config)
            
            # Validate initialization
            assert validator.user_pool_id == validator_config['user_pool_id']
            assert validator.client_id == validator_config['client_id']
            assert validator.region == validator_config['region']
            assert validator.discovery_url == validator_config['discovery_url']
            assert validator.jwks_url is not None
            assert validator.issuer_url is not None
            
            result = {
                'success': True,
                'user_pool_id': validator.user_pool_id,
                'client_id': validator.client_id,
                'region': validator.region,
                'discovery_url': validator.discovery_url,
                'jwks_url': validator.jwks_url,
                'issuer_url': validator.issuer_url
            }
            print("  ✅ TokenValidator initialized successfully")
            
        except Exception as e:
            result = {
                'success': False,
                'error': str(e),
                'error_type': type(e).__name__
            }
            print(f"  ❌ TokenValidator initialization failed: {e}")
        
        self.test_results[test_name] = result
        return result
    
    def test_authentication_middleware_initialization(self) -> Dict[str, Any]:
        """Test AuthenticationMiddleware initialization."""
        test_name = "authentication_middleware_initialization"
        print(f"🔧 Testing: {test_name}")
        
        try:
            cognito_config = {
                'user_pool_id': self.cognito_config['user_pool']['user_pool_id'],
                'client_id': self.cognito_config['app_client']['client_id'],
                'region': self.cognito_config['region'],
                'discovery_url': self.cognito_config['discovery_url']
            }
            
            auth_config = AuthenticationConfig(
                cognito_config=cognito_config,
                bypass_paths=['/health', '/metrics'],
                require_authentication=True,
                log_user_context=True
            )
            
            # Test middleware initialization (without FastAPI app)
            middleware = AuthenticationMiddleware(None, auth_config)
            
            # Validate initialization
            assert middleware.config == auth_config
            assert isinstance(middleware.token_validator, TokenValidator)
            
            result = {
                'success': True,
                'bypass_paths': auth_config.bypass_paths,
                'require_authentication': auth_config.require_authentication,
                'log_user_context': auth_config.log_user_context
            }
            print("  ✅ AuthenticationMiddleware initialized successfully")
            
        except Exception as e:
            result = {
                'success': False,
                'error': str(e),
                'error_type': type(e).__name__
            }
            print(f"  ❌ AuthenticationMiddleware initialization failed: {e}")
        
        self.test_results[test_name] = result
        return result
    
    def test_authentication_helper_functions(self) -> Dict[str, Any]:
        """Test AuthenticationHelper utility functions."""
        test_name = "authentication_helper_functions"
        print(f"🔧 Testing: {test_name}")
        
        try:
            # Create mock user context
            jwt_claims = JWTClaims(
                user_id='test-user-123',
                username='test@example.com',
                email='test@example.com',
                client_id='test-client',
                token_use='access',
                exp=int((datetime.now(timezone.utc)).timestamp()) + 3600,
                iat=int(datetime.now(timezone.utc).timestamp()),
                iss='https://cognito-idp.us-east-1.amazonaws.com/test-pool',
                aud='test-client'
            )
            
            user_context = UserContext(
                user_id=jwt_claims.user_id,
                username=jwt_claims.username,
                email=jwt_claims.email,
                authenticated=True,
                token_claims=jwt_claims
            )
            
            # Create mock request with user context
            from unittest.mock import Mock
            mock_request = Mock()
            mock_request.state = Mock()
            mock_request.state.user_context = user_context
            mock_request.state.authenticated = True
            
            # Test helper functions
            retrieved_context = AuthenticationHelper.get_user_context(mock_request)
            is_authenticated = AuthenticationHelper.is_authenticated(mock_request)
            user_id = AuthenticationHelper.get_user_id(mock_request)
            username = AuthenticationHelper.get_username(mock_request)
            
            # Validate results
            assert retrieved_context == user_context
            assert is_authenticated is True
            assert user_id == user_context.user_id
            assert username == user_context.username
            
            # Test with request without context
            mock_request_no_context = Mock()
            mock_request_no_context.state = Mock()
            mock_request_no_context.state.user_context = None
            mock_request_no_context.state.authenticated = False
            
            no_context = AuthenticationHelper.get_user_context(mock_request_no_context)
            not_authenticated = AuthenticationHelper.is_authenticated(mock_request_no_context)
            
            assert no_context is None
            assert not_authenticated is False
            
            result = {
                'success': True,
                'context_retrieval': True,
                'authentication_check': True,
                'user_id_extraction': True,
                'username_extraction': True,
                'no_context_handling': True
            }
            print("  ✅ AuthenticationHelper functions work correctly")
            
        except Exception as e:
            result = {
                'success': False,
                'error': str(e),
                'error_type': type(e).__name__
            }
            print(f"  ❌ AuthenticationHelper functions failed: {e}")
        
        self.test_results[test_name] = result
        return result
    
    def test_authentication_error_creation(self) -> Dict[str, Any]:
        """Test AuthenticationError creation and handling."""
        test_name = "authentication_error_creation"
        print(f"🔧 Testing: {test_name}")
        
        try:
            # Test error creation
            error = AuthenticationError(
                error_type="TEST_ERROR",
                error_code="TEST_CODE",
                message="Test error message",
                details="Test error details",
                suggested_action="Test suggested action"
            )
            
            # Validate error properties
            assert error.error_type == "TEST_ERROR"
            assert error.error_code == "TEST_CODE"
            assert error.message == "Test error message"
            assert error.details == "Test error details"
            assert error.suggested_action == "Test suggested action"
            
            # Test error raising and catching
            try:
                raise error
            except AuthenticationError as caught_error:
                assert caught_error.error_type == "TEST_ERROR"
                assert caught_error.error_code == "TEST_CODE"
                assert str(caught_error) == "Test error message"
            
            result = {
                'success': True,
                'error_creation': True,
                'error_properties': True,
                'error_raising': True
            }
            print("  ✅ AuthenticationError works correctly")
            
        except Exception as e:
            result = {
                'success': False,
                'error': str(e),
                'error_type': type(e).__name__
            }
            print(f"  ❌ AuthenticationError test failed: {e}")
        
        self.test_results[test_name] = result
        return result
    
    def test_data_model_creation(self) -> Dict[str, Any]:
        """Test authentication data model creation."""
        test_name = "data_model_creation"
        print(f"🔧 Testing: {test_name}")
        
        try:
            # Test AuthenticationTokens
            tokens = AuthenticationTokens(
                id_token="test_id_token",
                access_token="test_access_token",
                refresh_token="test_refresh_token",
                expires_in=3600,
                token_type="Bearer"
            )
            
            assert tokens.id_token == "test_id_token"
            assert tokens.access_token == "test_access_token"
            assert tokens.refresh_token == "test_refresh_token"
            assert tokens.expires_in == 3600
            assert tokens.token_type == "Bearer"
            
            # Test JWTClaims
            jwt_claims = JWTClaims(
                user_id='test-user-123',
                username='test@example.com',
                email='test@example.com',
                client_id='test-client',
                token_use='access',
                exp=int(datetime.now(timezone.utc).timestamp()) + 3600,
                iat=int(datetime.now(timezone.utc).timestamp()),
                iss='https://cognito-idp.us-east-1.amazonaws.com/test-pool',
                aud='test-client'
            )
            
            assert jwt_claims.user_id == 'test-user-123'
            assert jwt_claims.username == 'test@example.com'
            assert jwt_claims.email == 'test@example.com'
            assert jwt_claims.client_id == 'test-client'
            assert jwt_claims.token_use == 'access'
            
            # Test UserContext
            user_context = UserContext(
                user_id=jwt_claims.user_id,
                username=jwt_claims.username,
                email=jwt_claims.email,
                authenticated=True,
                token_claims=jwt_claims
            )
            
            assert user_context.user_id == jwt_claims.user_id
            assert user_context.username == jwt_claims.username
            assert user_context.email == jwt_claims.email
            assert user_context.authenticated is True
            assert user_context.token_claims == jwt_claims
            
            result = {
                'success': True,
                'authentication_tokens': True,
                'jwt_claims': True,
                'user_context': True
            }
            print("  ✅ Data models work correctly")
            
        except Exception as e:
            result = {
                'success': False,
                'error': str(e),
                'error_type': type(e).__name__
            }
            print(f"  ❌ Data model test failed: {e}")
        
        self.test_results[test_name] = result
        return result
    
    async def run_all_validation_tests(self) -> Dict[str, Any]:
        """Run all validation tests.
        
        Returns:
            Complete validation results.
        """
        print("🔧 Starting Authentication Components Validation")
        print("=" * 60)
        
        # Run all validation tests
        validation_methods = [
            self.test_cognito_authenticator_initialization,
            self.test_token_validator_initialization,
            self.test_authentication_middleware_initialization,
            self.test_authentication_helper_functions,
            self.test_authentication_error_creation,
            self.test_data_model_creation
        ]
        
        for method in validation_methods:
            try:
                if asyncio.iscoroutinefunction(method):
                    await method()
                else:
                    method()
            except Exception as e:
                print(f"💥 Validation method {method.__name__} failed: {e}")
                self.test_results[method.__name__] = {
                    'success': False,
                    'error': str(e),
                    'error_type': type(e).__name__
                }
        
        # Calculate summary
        total_tests = len(self.test_results)
        successful_tests = sum(1 for result in self.test_results.values() if result.get('success', False))
        
        summary = {
            'total_tests': total_tests,
            'successful_tests': successful_tests,
            'failed_tests': total_tests - successful_tests,
            'success_rate': (successful_tests / total_tests) * 100 if total_tests > 0 else 0,
            'all_passed': successful_tests == total_tests
        }
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 Validation Summary")
        print("=" * 60)
        print(f"Total Tests: {total_tests}")
        print(f"Successful: {successful_tests}")
        print(f"Failed: {total_tests - successful_tests}")
        print(f"Success Rate: {summary['success_rate']:.1f}%")
        print(f"Overall Result: {'✅ PASS' if summary['all_passed'] else '❌ FAIL'}")
        
        return {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'validation_suite': 'Authentication Components Validation',
            'tests': self.test_results,
            'summary': summary
        }


async def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Validate Authentication Components')
    parser.add_argument('--config', default='cognito_config.json',
                       help='Cognito configuration file (default: cognito_config.json)')
    parser.add_argument('--output', help='Output file for results')
    
    args = parser.parse_args()
    
    try:
        validator = AuthComponentValidator(args.config)
        results = await validator.run_all_validation_tests()
        
        # Save results if requested
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            print(f"\n💾 Validation results saved to: {args.output}")
        
        return 0 if results['summary']['all_passed'] else 1
        
    except Exception as e:
        print(f"💥 Validation failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))