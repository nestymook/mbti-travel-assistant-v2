#!/usr/bin/env python3
"""
Interactive Authentication Service for MBTI Travel Planner Agent
This service provides interactive Cognito authentication with username/password prompts
and manages JWT tokens throughout the test workflow.
"""
import asyncio
import base64
import getpass
import hashlib
import hmac
import json
import logging
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

import boto3
from botocore.exceptions import ClientError, NoCredentialsError

# Configure logging
logger = logging.getLogger(__name__)


class InteractiveAuthService:
    """Interactive authentication service for Cognito user authentication."""
    
    def __init__(self, cognito_config_path: str = "config/cognito_config.json"):
        """Initialize the interactive authentication service."""
        self.cognito_config_path = cognito_config_path
        self.cognito_config = None
        self.cognito_client = None
        self.jwt_token = None
        self.id_token = None
        self.refresh_token = None
        self.token_expiry = None
        self.username = None
        
        # Default test user
        self.default_username = "test@mbti-travel.com"
        
        logger.info("Interactive authentication service initialized")
    
    def calculate_secret_hash(self, username: str) -> str:
        """Calculate SECRET_HASH for Cognito authentication."""
        if not self.cognito_config or 'client_secret' not in self.cognito_config:
            logger.error(f"❌ Client secret not available. Config: {self.cognito_config}")
            raise ValueError("Client secret not available for SECRET_HASH calculation")
        
        client_id = self.cognito_config['client_id']
        client_secret = self.cognito_config['client_secret']
        
        logger.debug(f"🔐 Calculating SECRET_HASH for username: {username}")
        logger.debug(f"🔐 Client ID: {client_id}")
        logger.debug(f"🔐 Client Secret length: {len(client_secret)} chars")
        
        # Create the message: username + client_id (this is the standard format)
        message = username + client_id
        logger.debug(f"🔐 Message for HMAC: {message}")
        
        # Calculate HMAC-SHA256
        dig = hmac.new(
            client_secret.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).digest()
        
        # Return base64 encoded result
        secret_hash = base64.b64encode(dig).decode()
        logger.debug(f"🔐 SECRET_HASH calculated: {secret_hash[:20]}...")
        
        # Validate the SECRET_HASH format
        if len(secret_hash) < 40:  # HMAC-SHA256 base64 should be longer
            logger.warning(f"⚠️ SECRET_HASH seems too short: {len(secret_hash)} chars")
        
        return secret_hash
    
    def load_cognito_config(self) -> Dict[str, Any]:
        """Load Cognito configuration from file."""
        try:
            if os.path.exists(self.cognito_config_path):
                with open(self.cognito_config_path, 'r') as f:
                    raw_config = json.load(f)
                
                # Handle nested configuration structure
                config = {}
                
                # Extract region
                config['region'] = raw_config.get('region', 'us-east-1')
                
                # Extract user pool ID
                if 'user_pool' in raw_config and 'user_pool_id' in raw_config['user_pool']:
                    config['user_pool_id'] = raw_config['user_pool']['user_pool_id']
                elif 'user_pool_id' in raw_config:
                    config['user_pool_id'] = raw_config['user_pool_id']
                else:
                    raise ValueError("user_pool_id not found in configuration")
                
                # Extract client ID
                if 'app_client' in raw_config and 'client_id' in raw_config['app_client']:
                    config['client_id'] = raw_config['app_client']['client_id']
                elif 'client_id' in raw_config:
                    config['client_id'] = raw_config['client_id']
                else:
                    raise ValueError("client_id not found in configuration")
                
                # Extract client secret (optional)
                if 'app_client' in raw_config and 'client_secret' in raw_config['app_client']:
                    config['client_secret'] = raw_config['app_client']['client_secret']
                    logger.debug(f"🔐 Client secret loaded from app_client: {config['client_secret'][:10]}...")
                elif 'client_secret' in raw_config:
                    config['client_secret'] = raw_config['client_secret']
                    logger.debug(f"🔐 Client secret loaded from root: {config['client_secret'][:10]}...")
                else:
                    logger.warning("⚠️ No client secret found in configuration")
                
                # Validate required fields
                required_fields = ['user_pool_id', 'client_id', 'region']
                missing_fields = [field for field in required_fields if field not in config]
                
                if missing_fields:
                    raise ValueError(f"Missing required Cognito config fields: {missing_fields}")
                
                self.cognito_config = config
                logger.info(f"✅ Cognito configuration loaded from {self.cognito_config_path}")
                logger.info(f"User Pool ID: {config['user_pool_id']}")
                logger.info(f"Client ID: {config['client_id']}")
                logger.info(f"Region: {config['region']}")
                return config
            else:
                raise FileNotFoundError(f"Cognito config file not found: {self.cognito_config_path}")
                
        except Exception as e:
            logger.error(f"❌ Failed to load Cognito configuration: {e}")
            raise
    
    def initialize_cognito_client(self):
        """Initialize the Cognito Identity Provider client."""
        try:
            if not self.cognito_config:
                self.load_cognito_config()
            
            # Initialize Cognito client
            self.cognito_client = boto3.client(
                'cognito-idp',
                region_name=self.cognito_config['region']
            )
            
            logger.info(f"✅ Cognito client initialized for region: {self.cognito_config['region']}")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Cognito client: {e}")
            raise
    
    def prompt_for_credentials(self) -> tuple[str, str]:
        """Prompt user for username and password, with environment variable fallback."""
        # Check for environment variables first
        env_username = os.getenv('TEST_USERNAME')
        env_password = os.getenv('TEST_PASSWORD')
        
        if env_username and env_password:
            logger.info(f"Using credentials from environment variables")
            print("✅ Using credentials from environment variables")
            return env_username, env_password
        
        # Check for non-interactive mode (only if explicitly requested AND not forced interactive)
        force_interactive = os.getenv('FORCE_INTERACTIVE', '').lower() in ['true', '1', 'yes']
        non_interactive = os.getenv('NON_INTERACTIVE', '').lower() in ['true', '1', 'yes']
        
        if non_interactive and not force_interactive:
            # Use default credentials for non-interactive mode
            default_password = "TestPass1234!"  # Default test password
            logger.info(f"Non-interactive mode: using default credentials")
            print("✅ Non-interactive mode: using default test credentials")
            return self.default_username, default_password
        
        # Interactive mode - always prompt for credentials
        print("\n" + "=" * 60)
        print("COGNITO AUTHENTICATION REQUIRED")
        print("=" * 60)
        
        try:
            # Prompt for username with default
            username_prompt = f"Username (default: {self.default_username}): "
            username = input(username_prompt).strip()
            if not username:
                username = self.default_username
                print(f"Using default username: {username}")
            
            # Always prompt for password in interactive mode
            print("Please enter your password:")
            password = getpass.getpass("Password: ")
            
            if not password:
                # If no password entered, use default for test user
                if username == self.default_username:
                    password = "TestPass1234!"
                    print("Using default password for test user")
                else:
                    raise ValueError("Password cannot be empty")
            
            print("✅ Credentials entered successfully")
            return username, password
            
        except (KeyboardInterrupt, EOFError) as e:
            # Fallback to default credentials if interactive input fails
            logger.warning(f"Interactive input interrupted ({type(e).__name__}), falling back to default credentials")
            print("⚠️ Interactive input interrupted, using default test credentials")
            return self.default_username, "TestPass1234!"
        except Exception as e:
            logger.error(f"Error during credential prompting: {e}")
            # Fallback to default credentials
            logger.warning("Falling back to default credentials due to error")
            print("⚠️ Error during input, using default test credentials")
            return self.default_username, "TestPass1234!"
    
    async def authenticate_user(self, username: str = None, password: str = None) -> Dict[str, Any]:
        """Authenticate user with Cognito and obtain JWT tokens."""
        try:
            # Initialize Cognito client if not already done
            if not self.cognito_client:
                self.initialize_cognito_client()
            
            # Prompt for credentials if not provided
            if not username or not password:
                username, password = self.prompt_for_credentials()
            
            self.username = username
            logger.info(f"🔐 Authenticating user: {username}")
            
            # Calculate SECRET_HASH if client secret is available
            auth_parameters = {
                'USERNAME': username,
                'PASSWORD': password
            }
            
            if 'client_secret' in self.cognito_config:
                secret_hash = self.calculate_secret_hash(username)
                auth_parameters['SECRET_HASH'] = secret_hash
                logger.debug("✅ SECRET_HASH calculated and included")
            
            # Perform authentication - try different auth flows
            auth_start = datetime.utcnow()
            
            # First try USER_PASSWORD_AUTH
            try:
                logger.debug("🔐 Attempting USER_PASSWORD_AUTH flow...")
                response = self.cognito_client.initiate_auth(
                    ClientId=self.cognito_config['client_id'],
                    AuthFlow='USER_PASSWORD_AUTH',
                    AuthParameters=auth_parameters
                )
                logger.debug("✅ USER_PASSWORD_AUTH successful")
            except ClientError as e:
                if e.response['Error']['Code'] == 'NotAuthorizedException' and 'SecretHash' in e.response['Error']['Message']:
                    logger.warning("⚠️ USER_PASSWORD_AUTH failed with SecretHash error, trying ADMIN_NO_SRP_AUTH...")
                    
                    # Try ADMIN_NO_SRP_AUTH as fallback
                    try:
                        response = self.cognito_client.admin_initiate_auth(
                            UserPoolId=self.cognito_config['user_pool_id'],
                            ClientId=self.cognito_config['client_id'],
                            AuthFlow='ADMIN_NO_SRP_AUTH',
                            AuthParameters=auth_parameters
                        )
                        logger.debug("✅ ADMIN_NO_SRP_AUTH successful")
                    except ClientError as admin_error:
                        logger.error(f"❌ Both auth flows failed. USER_PASSWORD_AUTH: {e.response['Error']['Message']}")
                        logger.error(f"❌ ADMIN_NO_SRP_AUTH: {admin_error.response['Error']['Message']}")
                        raise e  # Re-raise the original error
                else:
                    raise e  # Re-raise if it's not a SecretHash error
            
            auth_time = (datetime.utcnow() - auth_start).total_seconds()
            
            # Extract tokens
            auth_result = response['AuthenticationResult']
            self.jwt_token = auth_result['AccessToken']
            self.id_token = auth_result['IdToken']
            self.refresh_token = auth_result.get('RefreshToken')
            
            # Store username for future use (like refresh token)
            self.username = username
            
            # Calculate token expiry
            expires_in = auth_result.get('ExpiresIn', 3600)  # Default 1 hour
            self.token_expiry = datetime.utcnow() + timedelta(seconds=expires_in)
            
            # Prepare authentication result
            auth_info = {
                'username': username,
                'jwt_token': self.jwt_token,
                'id_token': self.id_token,
                'refresh_token': self.refresh_token,
                'token_expiry': self.token_expiry.isoformat(),
                'authentication_time_seconds': auth_time,
                'expires_in_seconds': expires_in
            }
            
            logger.info(f"✅ Authentication successful for {username}")
            logger.info(f"🕒 Token expires at: {self.token_expiry.strftime('%Y-%m-%d %H:%M:%S UTC')}")
            logger.info(f"⚡ Authentication time: {auth_time:.3f} seconds")
            
            return auth_info
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            
            if error_code == 'NotAuthorizedException':
                logger.error("❌ Authentication failed: Invalid username or password")
                raise ValueError("Invalid username or password")
            elif error_code == 'UserNotFoundException':
                logger.error(f"❌ User not found: {username}")
                raise ValueError(f"User not found: {username}")
            elif error_code == 'UserNotConfirmedException':
                logger.error(f"❌ User not confirmed: {username}")
                raise ValueError(f"User account not confirmed: {username}")
            else:
                logger.error(f"❌ Cognito authentication error: {error_code} - {error_message}")
                raise ValueError(f"Authentication error: {error_message}")
                
        except Exception as e:
            logger.error(f"❌ Authentication failed: {e}")
            raise
    
    async def get_jwt_token(self) -> str:
        """Get current JWT token, refreshing if necessary."""
        try:
            # Check if we have a valid token
            if self.jwt_token and self.token_expiry:
                # Check if token is still valid (with 5-minute buffer)
                buffer_time = timedelta(minutes=5)
                if datetime.utcnow() < (self.token_expiry - buffer_time):
                    logger.debug("✅ Using existing JWT token")
                    return self.jwt_token
                else:
                    logger.info("🔄 JWT token expired, refreshing...")
                    return await self.refresh_jwt_token()
            
            # No token available, need to authenticate
            logger.info("🔐 No JWT token available, authentication required")
            auth_info = await self.authenticate_user()
            return auth_info['jwt_token']
            
        except Exception as e:
            logger.error(f"❌ Failed to get JWT token: {e}")
            raise
    
    async def refresh_jwt_token(self) -> str:
        """Refresh JWT token using refresh token."""
        try:
            if not self.refresh_token:
                logger.warning("⚠️ No refresh token available, re-authenticating...")
                auth_info = await self.authenticate_user()
                return auth_info['jwt_token']
            
            if not self.cognito_client:
                self.initialize_cognito_client()
            
            logger.info("🔄 Refreshing JWT token...")
            
            # Prepare auth parameters for refresh
            auth_parameters = {
                'REFRESH_TOKEN': self.refresh_token
            }
            
            # Try refresh without SECRET_HASH first (some configurations don't need it)
            try:
                logger.debug("🔄 Attempting refresh without SECRET_HASH...")
                response = self.cognito_client.initiate_auth(
                    ClientId=self.cognito_config['client_id'],
                    AuthFlow='REFRESH_TOKEN_AUTH',
                    AuthParameters=auth_parameters
                )
                logger.debug("✅ Refresh successful without SECRET_HASH")
                
            except ClientError as e:
                if 'SecretHash' in e.response['Error']['Message'] and 'client_secret' in self.cognito_config and self.username:
                    logger.debug("🔄 Refresh failed without SECRET_HASH, trying with SECRET_HASH...")
                    
                    # Add SECRET_HASH and try again
                    secret_hash = self.calculate_secret_hash(self.username)
                    auth_parameters['SECRET_HASH'] = secret_hash
                    
                    response = self.cognito_client.initiate_auth(
                        ClientId=self.cognito_config['client_id'],
                        AuthFlow='REFRESH_TOKEN_AUTH',
                        AuthParameters=auth_parameters
                    )
                    logger.debug("✅ Refresh successful with SECRET_HASH")
                else:
                    # If it's not a SECRET_HASH issue or we don't have the required info, re-raise
                    raise e
            
            # Update tokens
            auth_result = response['AuthenticationResult']
            self.jwt_token = auth_result['AccessToken']
            self.id_token = auth_result['IdToken']
            
            # Update expiry
            expires_in = auth_result.get('ExpiresIn', 3600)
            self.token_expiry = datetime.utcnow() + timedelta(seconds=expires_in)
            
            logger.info("✅ JWT token refreshed successfully")
            logger.info(f"🕒 New token expires at: {self.token_expiry.strftime('%Y-%m-%d %H:%M:%S UTC')}")
            
            return self.jwt_token
            
        except Exception as e:
            logger.error(f"❌ Failed to refresh JWT token: {e}")
            # Fall back to re-authentication
            logger.info("🔄 Falling back to re-authentication...")
            auth_info = await self.authenticate_user()
            return auth_info['jwt_token']
    
    def get_authentication_headers(self) -> Dict[str, str]:
        """Get authentication headers for API requests."""
        if not self.jwt_token:
            raise ValueError("No JWT token available. Please authenticate first.")
        
        return {
            'Authorization': f'Bearer {self.jwt_token}',
            'Content-Type': 'application/json'
        }
    
    def get_user_info(self) -> Dict[str, Any]:
        """Get current user information."""
        return {
            'username': self.username,
            'authenticated': self.jwt_token is not None,
            'token_expiry': self.token_expiry.isoformat() if self.token_expiry else None,
            'has_refresh_token': self.refresh_token is not None
        }
    
    def is_authenticated(self) -> bool:
        """Check if user is currently authenticated with valid token."""
        if not self.jwt_token or not self.token_expiry:
            return False
        
        # Check if token is still valid
        return datetime.utcnow() < self.token_expiry
    
    async def logout(self):
        """Logout user and clear tokens."""
        try:
            if self.jwt_token and self.cognito_client:
                # Revoke the token
                self.cognito_client.global_sign_out(
                    AccessToken=self.jwt_token
                )
                logger.info("✅ User signed out from Cognito")
        except Exception as e:
            logger.warning(f"⚠️ Error during logout: {e}")
        finally:
            # Clear all tokens and user info
            self.jwt_token = None
            self.id_token = None
            self.refresh_token = None
            self.token_expiry = None
            self.username = None
            logger.info("🔓 Local authentication state cleared")
    
    def validate_token_format(self, token: str) -> bool:
        """Validate JWT token format (basic validation)."""
        try:
            # JWT tokens have 3 parts separated by dots
            parts = token.split('.')
            if len(parts) != 3:
                return False
            
            # Each part should be base64 encoded
            import base64
            for part in parts:
                # Add padding if needed
                padded = part + '=' * (4 - len(part) % 4)
                base64.b64decode(padded)
            
            return True
        except Exception:
            return False


class AuthenticationTestHelper:
    """Helper class for authentication testing scenarios."""
    
    def __init__(self, auth_service: InteractiveAuthService):
        self.auth_service = auth_service
    
    async def test_authentication_flow(self) -> Dict[str, Any]:
        """Test the complete authentication flow."""
        test_results = {
            'config_loading': False,
            'client_initialization': False,
            'user_authentication': False,
            'token_validation': False,
            'token_refresh': False,
            'authentication_time_ms': 0,
            'errors': []
        }
        
        try:
            # Test config loading
            self.auth_service.load_cognito_config()
            test_results['config_loading'] = True
            
            # Test client initialization
            self.auth_service.initialize_cognito_client()
            test_results['client_initialization'] = True
            
            # Test user authentication
            auth_start = datetime.utcnow()
            auth_info = await self.auth_service.authenticate_user()
            auth_time = (datetime.utcnow() - auth_start).total_seconds() * 1000
            test_results['user_authentication'] = True
            test_results['authentication_time_ms'] = auth_time
            
            # Test token validation
            jwt_token = await self.auth_service.get_jwt_token()
            if jwt_token and self.auth_service.validate_token_format(jwt_token):
                test_results['token_validation'] = True
            
            # Test token refresh (if refresh token available)
            if self.auth_service.refresh_token:
                refreshed_token = await self.auth_service.refresh_jwt_token()
                if refreshed_token:
                    test_results['token_refresh'] = True
                    
        except Exception as e:
            test_results['errors'].append(str(e))
        
        return test_results
    
    def generate_test_report(self, test_results: Dict[str, Any]) -> str:
        """Generate a formatted test report."""
        report = []
        report.append("AUTHENTICATION TEST REPORT")
        report.append("=" * 40)
        
        # Test results
        for test_name, result in test_results.items():
            if test_name == 'errors':
                continue
            
            status = "✅ PASS" if result else "❌ FAIL"
            test_display = test_name.replace('_', ' ').title()
            
            if test_name == 'authentication_time_ms':
                report.append(f"{test_display}: {result:.0f}ms")
            else:
                report.append(f"{test_display}: {status}")
        
        # Errors
        if test_results.get('errors'):
            report.append("\nErrors:")
            for error in test_results['errors']:
                report.append(f"  - {error}")
        
        return "\n".join(report)


# Example usage and testing
async def main():
    """Example usage of the interactive authentication service."""
    print("Interactive Authentication Service - Test Mode")
    print("=" * 60)
    
    try:
        # Initialize authentication service
        auth_service = InteractiveAuthService()
        
        # Test authentication flow
        test_helper = AuthenticationTestHelper(auth_service)
        test_results = await test_helper.test_authentication_flow()
        
        # Print test report
        print("\n" + test_helper.generate_test_report(test_results))
        
        # Show user info
        if auth_service.is_authenticated():
            user_info = auth_service.get_user_info()
            print(f"\nAuthenticated User: {user_info['username']}")
            print(f"Token Expires: {user_info['token_expiry']}")
        
        # Cleanup
        await auth_service.logout()
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)