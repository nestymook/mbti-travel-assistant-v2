"""
JWT Authentication Handler for MBTI Travel Assistant MCP.

This module provides a comprehensive JWT authentication handler that integrates
with AWS Cognito User Pools for token validation, user context extraction,
and security monitoring. Follows PEP8 style guidelines and BedrockAgentCore patterns.
"""

import json
import logging
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from datetime import datetime, timezone
import asyncio
import boto3
from botocore.exceptions import ClientError
import jwt
import requests
from jwt.algorithms import RSAAlgorithm

from models.auth_models import (
    CognitoConfig, JWTClaims, UserContext, AuthenticationError
)
from services.auth_service import TokenValidator, AuthenticationError as AuthError
from services.auth_error_handler import AuthenticationErrorHandler
from services.security_monitor import get_security_monitor
from config.settings import settings


# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class TokenValidationResult:
    """Result of JWT token validation."""
    is_valid: bool
    user_context: Optional[UserContext] = None
    error: Optional[AuthenticationError] = None
    claims: Optional[JWTClaims] = None
    validation_time_ms: Optional[int] = None


@dataclass
class AuthenticationContext:
    """Context information for authentication requests."""
    client_ip: str
    user_agent: str
    request_path: str
    request_method: str
    timestamp: datetime
    request_id: Optional[str] = None


class JWTAuthHandler:
    """
    JWT Authentication Handler for validating incoming request tokens.
    
    Provides comprehensive JWT token validation with Cognito User Pool integration,
    token extraction from Authorization headers, and security monitoring.
    Implements requirements 6.1 and 6.3 from the specification.
    """
    
    def __init__(self, cognito_config: Optional[CognitoConfig] = None):
        """
        Initialize JWT authentication handler.
        
        Args:
            cognito_config: Optional Cognito configuration. If None, loads from settings.
        """
        # Load Cognito configuration
        if cognito_config is None:
            self.cognito_config = self._load_cognito_config_from_settings()
        else:
            self.cognito_config = cognito_config
        
        # Validate configuration
        config_errors = self.cognito_config.validate()
        if config_errors:
            raise ValueError(f"Invalid Cognito configuration: {', '.join(config_errors)}")
        
        # Initialize components
        self.token_validator = TokenValidator(self.cognito_config.to_dict())
        self.error_handler = AuthenticationErrorHandler(
            enable_security_logging=True,
            enable_monitoring=True,
            mask_sensitive_data=True
        )
        self.security_monitor = get_security_monitor()
        
        # Initialize Cognito client
        self.cognito_client = boto3.client(
            'cognito-idp',
            region_name=self.cognito_config.region
        )
        
        # Cache for JWKS keys
        self._jwks_cache = {}
        self._jwks_cache_expiry = None
        self._jwks_cache_ttl = settings.authentication.token_cache_ttl
        
        logger.info(f"JWT Auth Handler initialized for User Pool: {self.cognito_config.user_pool_id}")
    
    async def validate_request_token(self, auth_header: str,
                                   auth_context: Optional[AuthenticationContext] = None) -> TokenValidationResult:
        """
        Validate JWT token from HTTP Authorization header.
        
        Args:
            auth_header: Authorization header value (Bearer <token>)
            auth_context: Optional authentication context for logging
            
        Returns:
            TokenValidationResult with validation outcome
        """
        start_time = datetime.now()
        
        try:
            # Extract token from Authorization header
            token = self._extract_bearer_token(auth_header)
            
            # Validate JWT token
            jwt_claims = await self.token_validator.validate_jwt_token(token)
            
            # Create user context
            user_context = self._create_user_context(jwt_claims)
            
            # Calculate validation time
            validation_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            
            # Log successful authentication
            if auth_context:
                self._log_successful_authentication(user_context, auth_context)
            
            logger.debug(f"Token validation successful for user: {user_context.username}")
            
            return TokenValidationResult(
                is_valid=True,
                user_context=user_context,
                claims=jwt_claims,
                validation_time_ms=validation_time_ms
            )
            
        except AuthError as e:
            # Handle authentication errors
            validation_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            
            # Convert to our AuthenticationError format
            auth_error = AuthenticationError(
                error_code=e.error_code,
                error_message=e.message,
                error_type=e.error_type,
                suggested_action=e.suggested_action,
                timestamp=datetime.now(timezone.utc)
            )
            
            # Log failed authentication
            if auth_context:
                self._log_failed_authentication(auth_error, auth_context)
            
            logger.warning(f"Token validation failed: {e.message}")
            
            return TokenValidationResult(
                is_valid=False,
                error=auth_error,
                validation_time_ms=validation_time_ms
            )
            
        except Exception as e:
            # Handle unexpected errors
            validation_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            
            auth_error = AuthenticationError.invalid_token(
                f"Token validation failed: {str(e)}"
            )
            
            if auth_context:
                self._log_failed_authentication(auth_error, auth_context)
            
            logger.error(f"Unexpected error during token validation: {e}")
            
            return TokenValidationResult(
                is_valid=False,
                error=auth_error,
                validation_time_ms=validation_time_ms
            )
    
    def extract_token_from_header(self, auth_header: str) -> str:
        """
        Extract JWT token from Authorization Bearer header.
        
        Args:
            auth_header: Authorization header value
            
        Returns:
            JWT token string
            
        Raises:
            AuthenticationError: If token extraction fails
        """
        return self._extract_bearer_token(auth_header)
    
    async def validate_token_claims(self, token: str) -> JWTClaims:
        """
        Validate JWT token and extract claims.
        
        Args:
            token: JWT token string
            
        Returns:
            JWTClaims with validated token claims
            
        Raises:
            AuthenticationError: If token validation fails
        """
        try:
            return await self.token_validator.validate_jwt_token(token)
        except AuthError as e:
            raise AuthenticationError(
                error_code=e.error_code,
                error_message=e.message,
                error_type=e.error_type,
                suggested_action=e.suggested_action,
                timestamp=datetime.now(timezone.utc)
            )
    
    def get_user_context_from_token(self, token: str) -> UserContext:
        """
        Extract user context from JWT token without full validation.
        
        Args:
            token: JWT token string
            
        Returns:
            UserContext with user information
            
        Note:
            This method extracts claims without signature verification.
            Use validate_request_token for secure validation.
        """
        try:
            # Decode token without verification for context extraction
            decoded_token = jwt.decode(token, options={"verify_signature": False})
            
            # Create JWT claims
            jwt_claims = JWTClaims.from_dict(decoded_token)
            
            # Create user context
            return self._create_user_context(jwt_claims)
            
        except Exception as e:
            logger.warning(f"Failed to extract user context from token: {e}")
            raise AuthenticationError.invalid_token(
                f"Failed to extract user context: {str(e)}"
            )
    
    def is_token_expired(self, token: str) -> bool:
        """
        Check if JWT token is expired without full validation.
        
        Args:
            token: JWT token string
            
        Returns:
            True if token is expired, False otherwise
        """
        try:
            decoded_token = jwt.decode(token, options={"verify_signature": False})
            exp = decoded_token.get('exp', 0)
            current_time = datetime.now(timezone.utc).timestamp()
            return current_time >= exp
        except Exception:
            return True  # Assume expired if we can't decode
    
    async def refresh_jwks_cache(self) -> None:
        """
        Refresh JWKS cache from Cognito endpoint.
        
        This method updates the cached JSON Web Key Set used for
        JWT token signature verification.
        """
        try:
            await self.token_validator._refresh_jwks_cache()
            logger.info("JWKS cache refreshed successfully")
        except Exception as e:
            logger.error(f"Failed to refresh JWKS cache: {e}")
            raise AuthenticationError.cognito_error(
                f"Failed to refresh JWKS cache: {str(e)}"
            )
    
    def get_cognito_user_info(self, access_token: str) -> Dict[str, Any]:
        """
        Get detailed user information from Cognito using access token.
        
        Args:
            access_token: Valid Cognito access token
            
        Returns:
            Dictionary containing user information
            
        Raises:
            AuthenticationError: If user info retrieval fails
        """
        try:
            response = self.cognito_client.get_user(AccessToken=access_token)
            
            # Extract user attributes
            user_attributes = {
                attr['Name']: attr['Value'] 
                for attr in response.get('UserAttributes', [])
            }
            
            return {
                'username': response.get('Username', ''),
                'user_attributes': user_attributes,
                'user_mfa_settings': response.get('UserMFASettingList', []),
                'preferred_mfa_setting': response.get('PreferredMfaSetting'),
                'user_status': user_attributes.get('cognito:user_status', 'UNKNOWN')
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            
            logger.warning(f"Failed to get Cognito user info: {error_message}")
            
            raise AuthenticationError.cognito_error(
                f"Failed to retrieve user information: {error_message}"
            )
        except Exception as e:
            logger.error(f"Unexpected error getting user info: {e}")
            raise AuthenticationError.cognito_error(
                f"Unexpected error retrieving user information: {str(e)}"
            )
    
    def create_authentication_context(self, client_ip: str, user_agent: str,
                                    request_path: str, request_method: str,
                                    request_id: Optional[str] = None) -> AuthenticationContext:
        """
        Create authentication context for request processing.
        
        Args:
            client_ip: Client IP address
            user_agent: User agent string
            request_path: Request path
            request_method: HTTP method
            request_id: Optional request ID
            
        Returns:
            AuthenticationContext for the request
        """
        return AuthenticationContext(
            client_ip=client_ip,
            user_agent=user_agent,
            request_path=request_path,
            request_method=request_method,
            timestamp=datetime.now(timezone.utc),
            request_id=request_id
        )
    
    def _extract_bearer_token(self, auth_header: str) -> str:
        """
        Extract JWT token from Authorization Bearer header.
        
        Args:
            auth_header: Authorization header value
            
        Returns:
            JWT token string
            
        Raises:
            AuthenticationError: If token extraction fails
        """
        if not auth_header:
            raise AuthenticationError.missing_token(
                "Authorization header is required"
            )
        
        if not auth_header.startswith('Bearer '):
            raise AuthenticationError.invalid_token(
                "Authorization header must use Bearer token format"
            )
        
        token = auth_header[7:].strip()  # Remove 'Bearer ' prefix
        
        if not token:
            raise AuthenticationError.invalid_token(
                "Bearer token cannot be empty"
            )
        
        return token
    
    def _create_user_context(self, jwt_claims: JWTClaims) -> UserContext:
        """
        Create user context from JWT claims.
        
        Args:
            jwt_claims: Validated JWT claims
            
        Returns:
            UserContext with user information
        """
        return UserContext(
            user_id=jwt_claims.user_id,
            username=jwt_claims.username,
            email=jwt_claims.email,
            authenticated=True,
            token_claims=jwt_claims,
            session_id=None,  # Could be extracted from custom claims if needed
            permissions=[],   # Could be populated from token claims
            metadata=jwt_claims.custom_claims
        )
    
    def _load_cognito_config_from_settings(self) -> CognitoConfig:
        """
        Load Cognito configuration from application settings.
        
        Returns:
            CognitoConfig instance
            
        Raises:
            ValueError: If configuration is invalid
        """
        auth_settings = settings.authentication
        
        if not auth_settings.cognito_user_pool_id:
            raise ValueError("Cognito User Pool ID not configured")
        
        # Construct URLs based on region and user pool ID
        user_pool_id = auth_settings.cognito_user_pool_id
        region = auth_settings.cognito_region
        
        discovery_url = (
            f"https://cognito-idp.{region}.amazonaws.com/{user_pool_id}"
            "/.well-known/openid-configuration"
        )
        
        jwks_url = (
            f"https://cognito-idp.{region}.amazonaws.com/{user_pool_id}"
            "/.well-known/jwks.json"
        )
        
        issuer_url = f"https://cognito-idp.{region}.amazonaws.com/{user_pool_id}"
        
        return CognitoConfig(
            user_pool_id=user_pool_id,
            client_id=auth_settings.jwt_audience or "default-client",
            region=region,
            discovery_url=discovery_url,
            jwks_url=jwks_url,
            issuer_url=issuer_url
        )
    
    def _log_successful_authentication(self, user_context: UserContext,
                                     auth_context: AuthenticationContext) -> None:
        """
        Log successful authentication for audit purposes.
        
        Args:
            user_context: Authenticated user context
            auth_context: Authentication request context
        """
        try:
            audit_info = {
                'event_type': 'authentication_success',
                'timestamp': auth_context.timestamp.isoformat(),
                'user_id': user_context.user_id,
                'username': user_context.username,
                'email': user_context.email,
                'client_ip': auth_context.client_ip,
                'user_agent': auth_context.user_agent,
                'request_path': auth_context.request_path,
                'request_method': auth_context.request_method,
                'request_id': auth_context.request_id,
                'token_exp': user_context.token_claims.exp,
                'token_iat': user_context.token_claims.iat,
                'token_use': user_context.token_claims.token_use
            }
            
            # Log to security monitor
            self.security_monitor.log_authentication_attempt(
                success=True,
                user_context=user_context.to_dict(),
                request_context=self._auth_context_to_dict(auth_context)
            )
            
            logger.info(f"Authentication successful: {json.dumps(audit_info)}")
            
        except Exception as e:
            logger.warning(f"Failed to log successful authentication: {e}")
    
    def _log_failed_authentication(self, error: AuthenticationError,
                                 auth_context: AuthenticationContext) -> None:
        """
        Log failed authentication for security monitoring.
        
        Args:
            error: Authentication error
            auth_context: Authentication request context
        """
        try:
            audit_info = {
                'event_type': 'authentication_failure',
                'timestamp': auth_context.timestamp.isoformat(),
                'error_type': error.error_type,
                'error_code': error.error_code,
                'error_message': error.error_message,
                'client_ip': auth_context.client_ip,
                'user_agent': auth_context.user_agent,
                'request_path': auth_context.request_path,
                'request_method': auth_context.request_method,
                'request_id': auth_context.request_id
            }
            
            # Log to security monitor
            self.security_monitor.log_authentication_attempt(
                success=False,
                user_context={'user_id': 'unknown', 'username': 'unknown', 'email': 'unknown'},
                request_context=self._auth_context_to_dict(auth_context)
            )
            
            logger.warning(f"Authentication failed: {json.dumps(audit_info)}")
            
        except Exception as e:
            logger.warning(f"Failed to log failed authentication: {e}")
    
    def _auth_context_to_dict(self, auth_context: AuthenticationContext) -> Dict[str, Any]:
        """
        Convert authentication context to dictionary.
        
        Args:
            auth_context: Authentication context
            
        Returns:
            Dictionary representation
        """
        return {
            'client_ip': auth_context.client_ip,
            'user_agent': auth_context.user_agent,
            'path': auth_context.request_path,
            'method': auth_context.request_method,
            'timestamp': auth_context.timestamp.isoformat(),
            'request_id': auth_context.request_id
        }


class JWTAuthHandlerFactory:
    """
    Factory for creating JWT authentication handlers.
    
    Provides convenient methods for creating handlers with different configurations.
    """
    
    @staticmethod
    def create_default_handler() -> JWTAuthHandler:
        """
        Create JWT auth handler with default configuration from settings.
        
        Returns:
            JWTAuthHandler instance
        """
        return JWTAuthHandler()
    
    @staticmethod
    def create_handler_with_config(cognito_config: CognitoConfig) -> JWTAuthHandler:
        """
        Create JWT auth handler with specific Cognito configuration.
        
        Args:
            cognito_config: Cognito configuration
            
        Returns:
            JWTAuthHandler instance
        """
        return JWTAuthHandler(cognito_config)
    
    @staticmethod
    def create_handler_from_dict(config_dict: Dict[str, Any]) -> JWTAuthHandler:
        """
        Create JWT auth handler from configuration dictionary.
        
        Args:
            config_dict: Configuration dictionary
            
        Returns:
            JWTAuthHandler instance
        """
        cognito_config = CognitoConfig.from_dict(config_dict)
        return JWTAuthHandler(cognito_config)


# Export main classes and functions
__all__ = [
    'JWTAuthHandler',
    'JWTAuthHandlerFactory',
    'TokenValidationResult',
    'AuthenticationContext'
]