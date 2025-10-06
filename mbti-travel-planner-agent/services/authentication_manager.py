"""
Authentication Manager

This module provides JWT authentication management for AgentCore calls,
including automatic token refresh, caching, and thread-safe operations.

Enhanced features:
- Automatic token refresh with expiry checking
- Thread-safe token caching and refresh logic
- Comprehensive authentication error handling
- Token validation and JWKS caching
- Multiple authentication flow support
- Configuration validation
- Comprehensive monitoring and observability
"""

import asyncio
import base64
import hashlib
import hmac
import json
import logging
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Callable, Union
from dataclasses import dataclass, field
from enum import Enum

import boto3
import jwt
import requests
from botocore.exceptions import ClientError, BotoCoreError

# Import AuthenticationError - create if doesn't exist
try:
    from .agentcore_runtime_client import AuthenticationError
except ImportError:
    class AuthenticationError(Exception):
        """Authentication-related errors."""
        pass

# Import monitoring middleware
from .agentcore_monitoring_middleware import monitor_authentication, get_monitoring_middleware

logger = logging.getLogger(__name__)


class AuthenticationFlow(Enum):
    """Supported authentication flows."""
    SERVICE_ACCOUNT = "service_account"
    CLIENT_CREDENTIALS = "client_credentials"
    TEST_USER = "test_user"
    REFRESH_TOKEN = "refresh_token"


class TokenStatus(Enum):
    """Token status enumeration."""
    VALID = "valid"
    EXPIRED = "expired"
    INVALID = "invalid"
    NOT_FOUND = "not_found"


@dataclass
class CognitoConfig:
    """Cognito authentication configuration."""
    user_pool_id: str
    client_id: str
    client_secret: str
    region: str = "us-east-1"
    discovery_url: str = ""
    test_user_email: str = "test@mbti-travel.com"
    test_user_password: str = "TestPass1234!"
    service_account_username: str = "service-account"
    token_refresh_buffer_seconds: int = 300  # 5 minutes
    jwks_cache_duration_hours: int = 1
    max_retry_attempts: int = 3
    retry_backoff_base: float = 1.0
    
    def __post_init__(self):
        """Set discovery URL if not provided and validate configuration."""
        if not self.discovery_url:
            self.discovery_url = (
                f"https://cognito-idp.{self.region}.amazonaws.com/"
                f"{self.user_pool_id}/.well-known/openid-configuration"
            )
        
        # Validate required fields
        self._validate_config()
    
    def _validate_config(self):
        """Validate configuration parameters."""
        required_fields = ['user_pool_id', 'client_id', 'client_secret', 'region']
        for field_name in required_fields:
            if not getattr(self, field_name):
                raise ValueError(f"Required configuration field '{field_name}' is missing or empty")
        
        # Validate discovery URL format
        if not self.discovery_url.endswith('/.well-known/openid-configuration'):
            raise ValueError(
                f"Discovery URL must end with '/.well-known/openid-configuration', "
                f"got: {self.discovery_url}"
            )
        
        # Validate region format
        if not self.region or len(self.region.split('-')) < 3:
            raise ValueError(f"Invalid AWS region format: {self.region}")
        
        # Validate user pool ID format
        if not self.user_pool_id.startswith(f"{self.region}_"):
            raise ValueError(
                f"User pool ID should start with region prefix '{self.region}_', "
                f"got: {self.user_pool_id}"
            )


@dataclass
class TokenInfo:
    """Information about a JWT token."""
    token: str
    expires_at: datetime
    token_type: str = "Bearer"
    refresh_token: Optional[str] = None
    access_token: Optional[str] = None
    issued_at: Optional[datetime] = field(default_factory=datetime.utcnow)
    authentication_flow: Optional[AuthenticationFlow] = None
    
    def is_expired(self, buffer_seconds: int = 300) -> bool:
        """Check if token is expired with buffer."""
        return datetime.utcnow() + timedelta(seconds=buffer_seconds) >= self.expires_at
    
    def time_until_expiry(self) -> timedelta:
        """Get time until token expires."""
        return self.expires_at - datetime.utcnow()
    
    def get_status(self, buffer_seconds: int = 300) -> TokenStatus:
        """Get current token status."""
        if not self.token:
            return TokenStatus.NOT_FOUND
        
        if self.is_expired(buffer_seconds):
            return TokenStatus.EXPIRED
        
        try:
            # Basic token format validation
            parts = self.token.split('.')
            if len(parts) != 3:
                return TokenStatus.INVALID
            return TokenStatus.VALID
        except Exception:
            return TokenStatus.INVALID
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert token info to dictionary."""
        return {
            "token_type": self.token_type,
            "expires_at": self.expires_at.isoformat(),
            "issued_at": self.issued_at.isoformat() if self.issued_at else None,
            "time_until_expiry": str(self.time_until_expiry()),
            "is_expired": self.is_expired(),
            "status": self.get_status().value,
            "authentication_flow": self.authentication_flow.value if self.authentication_flow else None,
            "has_refresh_token": bool(self.refresh_token),
            "has_access_token": bool(self.access_token)
        }


class AuthenticationManager:
    """
    Manages JWT authentication for AgentCore calls.
    
    Features:
    - Automatic token refresh with expiry checking
    - Thread-safe token caching and refresh logic
    - Multiple authentication flow support
    - Comprehensive error handling and retry logic
    - Token validation with JWKS caching
    - Configuration validation
    """
    
    def __init__(self, cognito_config: CognitoConfig):
        """
        Initialize authentication manager.
        
        Args:
            cognito_config: Cognito configuration
            
        Raises:
            ValueError: If configuration is invalid
            AuthenticationError: If initialization fails
        """
        self.config = cognito_config
        
        # Initialize Cognito client with error handling
        try:
            self.cognito_client = boto3.client(
                'cognito-idp', 
                region_name=cognito_config.region
            )
        except Exception as e:
            raise AuthenticationError(f"Failed to initialize Cognito client: {str(e)}")
        
        # Token storage with thread safety
        self.current_token: Optional[TokenInfo] = None
        self.refresh_lock = asyncio.Lock()
        self._thread_lock = threading.RLock()
        
        # JWKS cache for token validation
        self.jwks_cache: Optional[Dict] = None
        self.jwks_cache_expiry: Optional[datetime] = None
        self.jwks_lock = asyncio.Lock()
        
        # Authentication flow preferences (in order of preference)
        self.preferred_flows = [
            AuthenticationFlow.SERVICE_ACCOUNT,
            AuthenticationFlow.TEST_USER,
            AuthenticationFlow.CLIENT_CREDENTIALS
        ]
        
        # Service account credentials
        self.service_username = cognito_config.service_account_username
        self.service_password: Optional[str] = None
        
        # Statistics and monitoring
        self.auth_stats = {
            "total_authentications": 0,
            "successful_authentications": 0,
            "failed_authentications": 0,
            "token_refreshes": 0,
            "last_authentication": None,
            "last_error": None
        }
        
        # Validate configuration and connectivity
        self._validate_initialization()
        
        logger.info(
            f"Authentication manager initialized successfully for user pool: {cognito_config.user_pool_id}"
        )
    
    def _validate_initialization(self):
        """Validate initialization and configuration."""
        try:
            # Test Cognito client connectivity
            self.cognito_client.describe_user_pool(UserPoolId=self.config.user_pool_id)
            logger.debug("Cognito connectivity validated successfully")
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            if error_code == 'ResourceNotFoundException':
                raise AuthenticationError(
                    f"User pool not found: {self.config.user_pool_id}. "
                    f"Please verify the user pool ID and region."
                )
            elif error_code == 'AccessDeniedException':
                raise AuthenticationError(
                    f"Access denied to user pool: {self.config.user_pool_id}. "
                    f"Please verify IAM permissions."
                )
            else:
                raise AuthenticationError(f"Failed to validate user pool: {str(e)}")
        except Exception as e:
            raise AuthenticationError(f"Failed to validate Cognito configuration: {str(e)}")
        
        # Load service account password from environment if available
        import os
        self.service_password = os.getenv('SERVICE_ACCOUNT_PASSWORD')
        
        logger.debug("Authentication manager initialization validation completed")
    
    @monitor_authentication("get_valid_token")
    async def get_valid_token(self) -> str:
        """
        Get valid JWT token with automatic refresh.
        
        This method implements thread-safe token caching and automatic refresh
        with expiry checking. It uses a double-checked locking pattern to
        minimize lock contention.
        
        Returns:
            Valid JWT token string
            
        Raises:
            AuthenticationError: If token cannot be obtained
        """
        # First check without lock (fast path)
        if self.current_token and not self.current_token.is_expired(
            self.config.token_refresh_buffer_seconds
        ):
            return self.current_token.token
        
        # Need to refresh token - acquire lock
        async with self.refresh_lock:
            # Double-check after acquiring lock (prevents race conditions)
            if self.current_token and not self.current_token.is_expired(
                self.config.token_refresh_buffer_seconds
            ):
                return self.current_token.token
            
            # Refresh the token with retry logic
            await self._refresh_token_with_retry()
            
            if not self.current_token or self.current_token.get_status() != TokenStatus.VALID:
                self.auth_stats["failed_authentications"] += 1
                raise AuthenticationError("Failed to obtain valid token after refresh")
            
            self.auth_stats["successful_authentications"] += 1
            return self.current_token.token
    
    @monitor_authentication("refresh_token")
    async def refresh_token(self) -> str:
        """
        Force refresh the JWT token.
        
        This method forces a token refresh regardless of current token status.
        It's useful for handling authentication errors or when a fresh token
        is explicitly required.
        
        Returns:
            New JWT token string
            
        Raises:
            AuthenticationError: If token refresh fails
        """
        async with self.refresh_lock:
            await self._refresh_token_with_retry()
            
            if not self.current_token or self.current_token.get_status() != TokenStatus.VALID:
                self.auth_stats["failed_authentications"] += 1
                raise AuthenticationError("Failed to refresh token")
            
            self.auth_stats["token_refreshes"] += 1
            return self.current_token.token
    
    async def _refresh_token_with_retry(self):
        """Refresh token with exponential backoff retry logic."""
        last_error = None
        
        for attempt in range(self.config.max_retry_attempts):
            try:
                await self._refresh_token()
                self.auth_stats["last_authentication"] = datetime.utcnow().isoformat()
                return
                
            except Exception as e:
                last_error = e
                self.auth_stats["last_error"] = str(e)
                
                if attempt < self.config.max_retry_attempts - 1:
                    # Calculate exponential backoff delay
                    delay = self.config.retry_backoff_base * (2 ** attempt)
                    logger.warning(
                        f"Authentication attempt {attempt + 1} failed: {str(e)}. "
                        f"Retrying in {delay} seconds..."
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"All {self.config.max_retry_attempts} authentication attempts failed")
        
        # All attempts failed
        raise AuthenticationError(
            f"Failed to refresh token after {self.config.max_retry_attempts} attempts. "
            f"Last error: {str(last_error)}"
        )
    
    async def _refresh_token(self):
        """Refresh JWT token from Cognito using preferred authentication flows."""
        self.auth_stats["total_authentications"] += 1
        
        try:
            # Try authentication flows in order of preference
            token_info = await self._try_authentication_flows()
            
            if token_info and token_info.get_status() == TokenStatus.VALID:
                with self._thread_lock:
                    self.current_token = token_info
                
                logger.info(
                    f"Token refreshed successfully using {token_info.authentication_flow.value} flow. "
                    f"Expires at: {token_info.expires_at}"
                )
            else:
                raise AuthenticationError("All authentication flows failed to produce valid token")
                
        except AuthenticationError:
            raise
        except Exception as e:
            logger.error(f"Token refresh failed with unexpected error: {str(e)}")
            raise AuthenticationError(f"Failed to refresh token: {str(e)}") from e
    
    async def _try_authentication_flows(self) -> Optional[TokenInfo]:
        """
        Try different authentication flows in order of preference.
        
        Returns:
            TokenInfo if successful, None if all flows fail
        """
        flow_methods = {
            AuthenticationFlow.SERVICE_ACCOUNT: self._authenticate_service_account,
            AuthenticationFlow.TEST_USER: self._authenticate_test_user,
            AuthenticationFlow.CLIENT_CREDENTIALS: self._authenticate_client_credentials,
            AuthenticationFlow.REFRESH_TOKEN: self._authenticate_refresh_token
        }
        
        # Try refresh token first if we have one
        if (self.current_token and self.current_token.refresh_token and 
            AuthenticationFlow.REFRESH_TOKEN not in self.preferred_flows):
            try:
                logger.debug("Attempting refresh token authentication")
                return await self._authenticate_refresh_token()
            except Exception as e:
                logger.debug(f"Refresh token authentication failed: {str(e)}")
        
        # Try preferred flows in order
        for flow in self.preferred_flows:
            if flow in flow_methods:
                try:
                    logger.debug(f"Attempting {flow.value} authentication")
                    token_info = await flow_methods[flow]()
                    if token_info:
                        return token_info
                except Exception as e:
                    logger.debug(f"{flow.value} authentication failed: {str(e)}")
                    continue
        
        logger.error("All authentication flows failed")
        return None
    
    async def _authenticate_service_account(self) -> TokenInfo:
        """
        Authenticate using service account credentials.
        
        Returns:
            TokenInfo with service account token
            
        Raises:
            AuthenticationError: If service account authentication fails
        """
        if not self.service_password:
            # Try to get service password from environment
            import os
            self.service_password = os.getenv('SERVICE_ACCOUNT_PASSWORD')
            
            if not self.service_password:
                raise AuthenticationError(
                    "Service account password not configured. "
                    "Set SERVICE_ACCOUNT_PASSWORD environment variable."
                )
        
        secret_hash = self._calculate_secret_hash(
            self.service_username,
            self.config.client_id,
            self.config.client_secret
        )
        
        try:
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.cognito_client.admin_initiate_auth(
                    UserPoolId=self.config.user_pool_id,
                    ClientId=self.config.client_id,
                    AuthFlow='ADMIN_NO_SRP_AUTH',
                    AuthParameters={
                        'USERNAME': self.service_username,
                        'PASSWORD': self.service_password,
                        'SECRET_HASH': secret_hash
                    }
                )
            )
            
            token_info = self._parse_auth_response(response, AuthenticationFlow.SERVICE_ACCOUNT)
            logger.debug(f"Service account authentication successful for user: {self.service_username}")
            return token_info
            
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            error_message = e.response.get('Error', {}).get('Message', str(e))
            
            if error_code == 'NotAuthorizedException':
                raise AuthenticationError(f"Service account authentication failed: Invalid credentials")
            elif error_code == 'UserNotFoundException':
                raise AuthenticationError(f"Service account user not found: {self.service_username}")
            else:
                raise AuthenticationError(f"Service account authentication failed: {error_message}")
        except Exception as e:
            raise AuthenticationError(f"Service account authentication error: {str(e)}")
    
    async def _authenticate_client_credentials(self) -> TokenInfo:
        """Authenticate using OAuth 2.0 client credentials flow."""
        # This would be used if Cognito supported client credentials flow
        # For now, we'll skip this implementation
        raise AuthenticationError("Client credentials flow not implemented")
    
    async def _authenticate_test_user(self) -> TokenInfo:
        """
        Authenticate using test user credentials (development only).
        
        Returns:
            TokenInfo with test user token
            
        Raises:
            AuthenticationError: If test user authentication fails
        """
        test_username = self.config.test_user_email
        test_password = self.config.test_user_password
        
        secret_hash = self._calculate_secret_hash(
            test_username,
            self.config.client_id,
            self.config.client_secret
        )
        
        try:
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.cognito_client.admin_initiate_auth(
                    UserPoolId=self.config.user_pool_id,
                    ClientId=self.config.client_id,
                    AuthFlow='ADMIN_NO_SRP_AUTH',
                    AuthParameters={
                        'USERNAME': test_username,
                        'PASSWORD': test_password,
                        'SECRET_HASH': secret_hash
                    }
                )
            )
            
            token_info = self._parse_auth_response(response, AuthenticationFlow.TEST_USER)
            logger.debug(f"Test user authentication successful for user: {test_username}")
            return token_info
            
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            error_message = e.response.get('Error', {}).get('Message', str(e))
            
            if error_code == 'NotAuthorizedException':
                raise AuthenticationError(f"Test user authentication failed: Invalid credentials")
            elif error_code == 'UserNotFoundException':
                raise AuthenticationError(f"Test user not found: {test_username}")
            elif error_code == 'UserNotConfirmedException':
                raise AuthenticationError(f"Test user not confirmed: {test_username}")
            else:
                raise AuthenticationError(f"Test user authentication failed: {error_message}")
        except Exception as e:
            raise AuthenticationError(f"Test user authentication error: {str(e)}")
    
    async def _authenticate_refresh_token(self) -> TokenInfo:
        """
        Authenticate using refresh token.
        
        Returns:
            TokenInfo with refreshed token
            
        Raises:
            AuthenticationError: If refresh token authentication fails
        """
        if not self.current_token or not self.current_token.refresh_token:
            raise AuthenticationError("No refresh token available")
        
        secret_hash = self._calculate_secret_hash(
            self.config.test_user_email,  # Use test user for refresh
            self.config.client_id,
            self.config.client_secret
        )
        
        try:
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.cognito_client.admin_initiate_auth(
                    UserPoolId=self.config.user_pool_id,
                    ClientId=self.config.client_id,
                    AuthFlow='REFRESH_TOKEN_AUTH',
                    AuthParameters={
                        'REFRESH_TOKEN': self.current_token.refresh_token,
                        'SECRET_HASH': secret_hash
                    }
                )
            )
            
            token_info = self._parse_auth_response(response, AuthenticationFlow.REFRESH_TOKEN)
            # Preserve the refresh token if not returned in response
            if not token_info.refresh_token and self.current_token.refresh_token:
                token_info.refresh_token = self.current_token.refresh_token
            
            logger.debug("Refresh token authentication successful")
            return token_info
            
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            error_message = e.response.get('Error', {}).get('Message', str(e))
            
            if error_code == 'NotAuthorizedException':
                raise AuthenticationError("Refresh token expired or invalid")
            else:
                raise AuthenticationError(f"Refresh token authentication failed: {error_message}")
        except Exception as e:
            raise AuthenticationError(f"Refresh token authentication error: {str(e)}")
    
    def _calculate_secret_hash(self, username: str, client_id: str, client_secret: str) -> str:
        """Calculate SECRET_HASH for Cognito authentication."""
        message = username + client_id
        dig = hmac.new(
            client_secret.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).digest()
        return base64.b64encode(dig).decode()
    
    def _parse_auth_response(
        self, 
        response: Dict[str, Any], 
        auth_flow: AuthenticationFlow
    ) -> TokenInfo:
        """
        Parse authentication response and extract token info.
        
        Args:
            response: Cognito authentication response
            auth_flow: Authentication flow used
            
        Returns:
            TokenInfo with parsed token data
            
        Raises:
            AuthenticationError: If response format is invalid
        """
        try:
            auth_result = response['AuthenticationResult']
            id_token = auth_result['IdToken']
            expires_in = auth_result.get('ExpiresIn', 3600)  # Default 1 hour
            
            # Calculate expiry time without buffer (buffer applied during validation)
            expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
            
            return TokenInfo(
                token=id_token,
                expires_at=expires_at,
                token_type="Bearer",
                refresh_token=auth_result.get('RefreshToken'),
                access_token=auth_result.get('AccessToken'),
                issued_at=datetime.utcnow(),
                authentication_flow=auth_flow
            )
            
        except KeyError as e:
            raise AuthenticationError(f"Invalid authentication response format: {str(e)}")
        except Exception as e:
            raise AuthenticationError(f"Failed to parse authentication response: {str(e)}")
    
    def is_token_valid(self) -> bool:
        """Check if current token is valid."""
        return self.current_token is not None and not self.current_token.is_expired()
    
    @monitor_authentication("validate_token")
    async def validate_token(self, token: str) -> Dict[str, Any]:
        """
        Validate JWT token and return claims.
        
        This method validates the token signature, expiration, audience, and issuer
        using the JWKS from Cognito.
        
        Args:
            token: JWT token to validate
            
        Returns:
            Token claims dictionary
            
        Raises:
            AuthenticationError: If token is invalid
        """
        if not token:
            raise AuthenticationError("Token is empty or None")
        
        try:
            # Basic format validation
            parts = token.split('.')
            if len(parts) != 3:
                raise AuthenticationError("Invalid JWT format: token must have 3 parts")
            
            # Get JWKS for token validation
            jwks = await self._get_jwks()
            
            # Expected issuer
            expected_issuer = f"https://cognito-idp.{self.config.region}.amazonaws.com/{self.config.user_pool_id}"
            
            # Decode and validate token
            decoded = jwt.decode(
                token,
                jwks,
                algorithms=["RS256"],
                audience=self.config.client_id,
                issuer=expected_issuer,
                options={
                    "verify_signature": True,
                    "verify_exp": True,
                    "verify_aud": True,
                    "verify_iss": True
                }
            )
            
            logger.debug(f"Token validation successful for subject: {decoded.get('sub', 'unknown')}")
            return decoded
            
        except jwt.ExpiredSignatureError:
            raise AuthenticationError("Token has expired")
        except jwt.InvalidAudienceError:
            raise AuthenticationError(f"Invalid token audience. Expected: {self.config.client_id}")
        except jwt.InvalidIssuerError:
            raise AuthenticationError(f"Invalid token issuer. Expected: {expected_issuer}")
        except jwt.InvalidSignatureError:
            raise AuthenticationError("Invalid token signature")
        except jwt.InvalidTokenError as e:
            raise AuthenticationError(f"Invalid token: {str(e)}")
        except Exception as e:
            raise AuthenticationError(f"Token validation failed: {str(e)}")
    
    async def _get_jwks(self) -> Dict[str, Any]:
        """
        Get JWKS (JSON Web Key Set) for token validation with caching.
        
        Returns:
            JWKS dictionary
            
        Raises:
            AuthenticationError: If JWKS cannot be retrieved
        """
        # Check cache first (thread-safe)
        async with self.jwks_lock:
            if (self.jwks_cache and self.jwks_cache_expiry and 
                datetime.utcnow() < self.jwks_cache_expiry):
                logger.debug("Using cached JWKS")
                return self.jwks_cache
        
        try:
            # Fetch JWKS from Cognito
            jwks_url = f"https://cognito-idp.{self.config.region}.amazonaws.com/{self.config.user_pool_id}/.well-known/jwks.json"
            
            logger.debug(f"Fetching JWKS from: {jwks_url}")
            
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: requests.get(
                    jwks_url, 
                    timeout=10,
                    headers={'User-Agent': 'MBTI-Travel-Planner-Agent/1.0'}
                )
            )
            response.raise_for_status()
            
            jwks = response.json()
            
            # Validate JWKS format
            if 'keys' not in jwks or not isinstance(jwks['keys'], list):
                raise AuthenticationError("Invalid JWKS format: missing or invalid 'keys' field")
            
            if not jwks['keys']:
                raise AuthenticationError("JWKS contains no keys")
            
            # Cache JWKS with thread safety
            async with self.jwks_lock:
                self.jwks_cache = jwks
                self.jwks_cache_expiry = datetime.utcnow() + timedelta(
                    hours=self.config.jwks_cache_duration_hours
                )
            
            logger.debug(f"JWKS cached successfully with {len(jwks['keys'])} keys")
            return jwks
            
        except requests.exceptions.Timeout:
            raise AuthenticationError("Timeout while fetching JWKS")
        except requests.exceptions.ConnectionError:
            raise AuthenticationError("Connection error while fetching JWKS")
        except requests.exceptions.HTTPError as e:
            raise AuthenticationError(f"HTTP error while fetching JWKS: {e.response.status_code}")
        except json.JSONDecodeError:
            raise AuthenticationError("Invalid JSON in JWKS response")
        except Exception as e:
            raise AuthenticationError(f"Failed to fetch JWKS: {str(e)}")
    
    def get_auth_headers(self, token: Optional[str] = None) -> Dict[str, str]:
        """
        Get authentication headers for HTTP requests.
        
        Args:
            token: Optional token to use (uses current token if None)
            
        Returns:
            Dictionary of authentication headers
        """
        if not token:
            if not self.current_token:
                raise AuthenticationError("No valid token available")
            token = self.current_token.token
        
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    
    def get_token_info(self) -> Optional[Dict[str, Any]]:
        """
        Get comprehensive information about current token.
        
        Returns:
            Dictionary with token information or None if no token
        """
        if not self.current_token:
            return None
        
        return self.current_token.to_dict()
    
    def get_authentication_stats(self) -> Dict[str, Any]:
        """
        Get authentication statistics and monitoring information.
        
        Returns:
            Dictionary with authentication statistics
        """
        return {
            **self.auth_stats,
            "current_token_status": self.current_token.get_status().value if self.current_token else "not_found",
            "config_user_pool_id": self.config.user_pool_id,
            "config_client_id": self.config.client_id,
            "preferred_flows": [flow.value for flow in self.preferred_flows],
            "jwks_cache_status": "cached" if self.jwks_cache else "not_cached",
            "jwks_cache_expiry": self.jwks_cache_expiry.isoformat() if self.jwks_cache_expiry else None
        }
    
    async def validate_configuration(self) -> Dict[str, Any]:
        """
        Validate authentication configuration and connectivity.
        
        Returns:
            Dictionary with validation results
        """
        validation_results = {
            "config_valid": True,
            "cognito_connectivity": False,
            "jwks_accessible": False,
            "discovery_url_valid": False,
            "errors": []
        }
        
        try:
            # Validate configuration
            self.config._validate_config()
        except Exception as e:
            validation_results["config_valid"] = False
            validation_results["errors"].append(f"Configuration validation failed: {str(e)}")
        
        # Test Cognito connectivity
        try:
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.cognito_client.describe_user_pool(UserPoolId=self.config.user_pool_id)
            )
            validation_results["cognito_connectivity"] = True
        except Exception as e:
            validation_results["errors"].append(f"Cognito connectivity failed: {str(e)}")
        
        # Test JWKS accessibility
        try:
            await self._get_jwks()
            validation_results["jwks_accessible"] = True
        except Exception as e:
            validation_results["errors"].append(f"JWKS access failed: {str(e)}")
        
        # Test discovery URL
        try:
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: requests.get(self.config.discovery_url, timeout=10)
            )
            if response.status_code == 200:
                validation_results["discovery_url_valid"] = True
            else:
                validation_results["errors"].append(f"Discovery URL returned status: {response.status_code}")
        except Exception as e:
            validation_results["errors"].append(f"Discovery URL test failed: {str(e)}")
        
        return validation_results
    
    async def test_authentication(self) -> Dict[str, Any]:
        """
        Comprehensive authentication test and status information.
        
        Returns:
            Dictionary with detailed authentication test results
        """
        test_start_time = datetime.utcnow()
        
        try:
            # Try to get a valid token
            token = await self.get_valid_token()
            
            # Validate the token
            claims = await self.validate_token(token)
            
            test_duration = (datetime.utcnow() - test_start_time).total_seconds()
            
            return {
                "success": True,
                "token_obtained": True,
                "token_valid": True,
                "test_duration_seconds": test_duration,
                "user_pool_id": self.config.user_pool_id,
                "client_id": self.config.client_id,
                "authentication_flow": self.current_token.authentication_flow.value if self.current_token else None,
                "token_claims": {
                    "sub": claims.get("sub"),
                    "email": claims.get("email"),
                    "exp": claims.get("exp"),
                    "iat": claims.get("iat"),
                    "token_use": claims.get("token_use"),
                    "auth_time": claims.get("auth_time")
                },
                "token_info": self.get_token_info(),
                "auth_stats": self.get_authentication_stats()
            }
            
        except Exception as e:
            test_duration = (datetime.utcnow() - test_start_time).total_seconds()
            
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
                "test_duration_seconds": test_duration,
                "token_obtained": self.current_token is not None,
                "token_valid": False,
                "user_pool_id": self.config.user_pool_id,
                "client_id": self.config.client_id,
                "auth_stats": self.get_authentication_stats()
            }
    
    async def cleanup(self):
        """
        Cleanup resources and reset state.
        
        This method should be called when shutting down the authentication manager
        to ensure proper cleanup of sensitive data and resources.
        """
        with self._thread_lock:
            self.current_token = None
            self.service_password = None
        
        async with self.jwks_lock:
            self.jwks_cache = None
            self.jwks_cache_expiry = None
        
        # Reset statistics
        self.auth_stats = {
            "total_authentications": 0,
            "successful_authentications": 0,
            "failed_authentications": 0,
            "token_refreshes": 0,
            "last_authentication": None,
            "last_error": None
        }
        
        logger.info("Authentication manager cleaned up successfully")
    
    def set_preferred_flows(self, flows: list[AuthenticationFlow]):
        """
        Set preferred authentication flows in order of preference.
        
        Args:
            flows: List of authentication flows in order of preference
        """
        self.preferred_flows = flows
        logger.info(f"Authentication flows updated: {[flow.value for flow in flows]}")
    
    async def force_token_refresh(self) -> str:
        """
        Force immediate token refresh, bypassing cache.
        
        This method is useful for handling authentication errors or when
        a fresh token is explicitly required.
        
        Returns:
            New JWT token string
            
        Raises:
            AuthenticationError: If token refresh fails
        """
        # Clear current token to force refresh
        with self._thread_lock:
            self.current_token = None
        
        return await self.refresh_token()
    
    def is_configuration_valid(self) -> bool:
        """
        Quick check if configuration is valid.
        
        Returns:
            True if configuration is valid, False otherwise
        """
        try:
            self.config._validate_config()
            return True
        except Exception:
            return False


# Configuration error class
class ConfigurationError(Exception):
    """Configuration-related errors."""
    pass


# Factory function for creating authentication manager from config file
def create_authentication_manager(config_path: str = None) -> AuthenticationManager:
    """
    Create authentication manager from configuration file.
    
    Args:
        config_path: Path to Cognito configuration file
        
    Returns:
        AuthenticationManager instance
        
    Raises:
        ConfigurationError: If configuration loading fails
        ValueError: If configuration is invalid
        AuthenticationError: If initialization fails
    """
    import os
    
    if not config_path:
        # Default config path
        config_dir = os.path.dirname(os.path.dirname(__file__))  # Go up to project root
        config_path = os.path.join(config_dir, "config", "cognito_config.json")
    
    if not os.path.exists(config_path):
        raise ConfigurationError(f"Configuration file not found: {config_path}")
    
    try:
        with open(config_path, 'r') as f:
            config_data = json.load(f)
        
        # Extract configuration with defaults
        cognito_config = CognitoConfig(
            user_pool_id=config_data["user_pool"]["user_pool_id"],
            client_id=config_data["app_client"]["client_id"],
            client_secret=config_data["app_client"]["client_secret"],
            region=config_data.get("region", "us-east-1"),
            discovery_url=config_data.get("discovery_url", ""),
            test_user_email=config_data.get("test_user", {}).get("email", "test@mbti-travel.com"),
            test_user_password=config_data.get("test_user", {}).get("password", "TestPass1234!")
        )
        
        return AuthenticationManager(cognito_config)
        
    except KeyError as e:
        raise ConfigurationError(f"Missing required configuration field: {str(e)}")
    except json.JSONDecodeError as e:
        raise ConfigurationError(f"Invalid JSON in configuration file: {str(e)}")
    except Exception as e:
        raise ConfigurationError(f"Failed to create authentication manager from config: {str(e)}")


def create_authentication_manager_from_env() -> AuthenticationManager:
    """
    Create authentication manager from environment variables.
    
    Expected environment variables:
    - COGNITO_USER_POOL_ID
    - COGNITO_CLIENT_ID
    - COGNITO_CLIENT_SECRET
    - COGNITO_REGION (optional, defaults to us-east-1)
    - COGNITO_DISCOVERY_URL (optional)
    - TEST_USER_EMAIL (optional)
    - TEST_USER_PASSWORD (optional)
    
    Returns:
        AuthenticationManager instance
        
    Raises:
        ConfigurationError: If required environment variables are missing
        ValueError: If configuration is invalid
        AuthenticationError: If initialization fails
    """
    import os
    
    required_vars = ['COGNITO_USER_POOL_ID', 'COGNITO_CLIENT_ID', 'COGNITO_CLIENT_SECRET']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        raise ConfigurationError(f"Missing required environment variables: {', '.join(missing_vars)}")
    
    try:
        cognito_config = CognitoConfig(
            user_pool_id=os.getenv('COGNITO_USER_POOL_ID'),
            client_id=os.getenv('COGNITO_CLIENT_ID'),
            client_secret=os.getenv('COGNITO_CLIENT_SECRET'),
            region=os.getenv('COGNITO_REGION', 'us-east-1'),
            discovery_url=os.getenv('COGNITO_DISCOVERY_URL', ''),
            test_user_email=os.getenv('TEST_USER_EMAIL', 'test@mbti-travel.com'),
            test_user_password=os.getenv('TEST_USER_PASSWORD', 'TestPass1234!')
        )
        
        return AuthenticationManager(cognito_config)
        
    except Exception as e:
        raise ConfigurationError(f"Failed to create authentication manager from environment: {str(e)}")


# Export main classes and functions
__all__ = [
    'AuthenticationManager',
    'CognitoConfig',
    'TokenInfo',
    'AuthenticationFlow',
    'TokenStatus',
    'AuthenticationError',
    'ConfigurationError',
    'create_authentication_manager',
    'create_authentication_manager_from_env'
]