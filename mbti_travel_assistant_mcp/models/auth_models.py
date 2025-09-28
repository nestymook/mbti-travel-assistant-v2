"""Authentication data models for MBTI Travel Assistant MCP.

This module contains models for AWS Cognito authentication, JWT token handling,
and user context management for the MBTI Travel Assistant system.
Follows PEP8 style guidelines and supports BedrockAgentCore runtime patterns.
"""

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List


@dataclass
class CognitoConfig:
    """AWS Cognito User Pool configuration.
    
    Contains all necessary configuration for Cognito authentication
    including user pool details and JWT validation settings.
    
    Attributes:
        user_pool_id: AWS Cognito User Pool ID
        client_id: Cognito App Client ID
        region: AWS region for the User Pool
        discovery_url: OpenID Connect discovery URL
        jwks_url: JSON Web Key Set URL for token validation
        issuer_url: JWT token issuer URL
        user_pool_domain: Optional Cognito domain for hosted UI
        client_secret: Optional client secret for confidential clients
    """
    user_pool_id: str
    client_id: str
    region: str
    discovery_url: str
    jwks_url: str
    issuer_url: str
    user_pool_domain: Optional[str] = None
    client_secret: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CognitoConfig':
        """Create CognitoConfig instance from dictionary.
        
        Args:
            data: Dictionary containing Cognito configuration
            
        Returns:
            CognitoConfig instance
        """
        return cls(
            user_pool_id=data['user_pool_id'],
            client_id=data['client_id'],
            region=data['region'],
            discovery_url=data['discovery_url'],
            jwks_url=data['jwks_url'],
            issuer_url=data['issuer_url'],
            user_pool_domain=data.get('user_pool_domain'),
            client_secret=data.get('client_secret')
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert Cognito config to dictionary.
        
        Returns:
            Dictionary representation of Cognito config
        """
        result = {
            'user_pool_id': self.user_pool_id,
            'client_id': self.client_id,
            'region': self.region,
            'discovery_url': self.discovery_url,
            'jwks_url': self.jwks_url,
            'issuer_url': self.issuer_url
        }
        
        if self.user_pool_domain is not None:
            result['user_pool_domain'] = self.user_pool_domain
            
        if self.client_secret is not None:
            result['client_secret'] = self.client_secret
            
        return result

    def validate(self) -> List[str]:
        """Validate Cognito configuration.
        
        Returns:
            List of validation error messages
        """
        errors = []
        
        # Validate required string fields
        required_fields = [
            ('user_pool_id', self.user_pool_id),
            ('client_id', self.client_id),
            ('region', self.region),
            ('discovery_url', self.discovery_url),
            ('jwks_url', self.jwks_url),
            ('issuer_url', self.issuer_url)
        ]
        
        for field_name, value in required_fields:
            if not isinstance(value, str):
                errors.append(f"{field_name} must be a string")
            elif len(value.strip()) == 0:
                errors.append(f"{field_name} cannot be empty")
        
        # Validate URL formats
        url_fields = [
            ('discovery_url', self.discovery_url),
            ('jwks_url', self.jwks_url),
            ('issuer_url', self.issuer_url)
        ]
        
        for field_name, url in url_fields:
            if isinstance(url, str) and url:
                if not (url.startswith('http://') or url.startswith('https://')):
                    errors.append(f"{field_name} must be a valid URL")
        
        return errors


@dataclass
class JWTClaims:
    """JWT token claims extracted from Cognito tokens.
    
    Contains standard and custom claims from JWT tokens
    for user identification and authorization.
    
    Attributes:
        user_id: Unique user identifier (sub claim)
        username: Username from Cognito
        email: User email address
        client_id: Cognito client ID
        token_use: Token type (access or id)
        exp: Expiration timestamp
        iat: Issued at timestamp
        iss: Token issuer
        aud: Token audience
        auth_time: Authentication time (optional)
        custom_claims: Additional custom claims
    """
    user_id: str
    username: str
    email: str
    client_id: str
    token_use: str
    exp: int
    iat: int
    iss: str
    aud: str
    auth_time: Optional[int] = None
    custom_claims: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'JWTClaims':
        """Create JWTClaims instance from dictionary.
        
        Args:
            data: Dictionary containing JWT claims
            
        Returns:
            JWTClaims instance
        """
        return cls(
            user_id=data.get('sub', data.get('user_id', '')),
            username=data.get('cognito:username', data.get('username', '')),
            email=data.get('email', ''),
            client_id=data.get('client_id', data.get('aud', '')),
            token_use=data.get('token_use', ''),
            exp=data.get('exp', 0),
            iat=data.get('iat', 0),
            iss=data.get('iss', ''),
            aud=data.get('aud', ''),
            auth_time=data.get('auth_time'),
            custom_claims=data.get('custom_claims', {})
        )

    def is_expired(self) -> bool:
        """Check if the JWT token is expired.
        
        Returns:
            True if token is expired, False otherwise
        """
        current_time = int(datetime.now(timezone.utc).timestamp())
        return current_time >= self.exp

    def time_until_expiry(self) -> int:
        """Get seconds until token expiry.
        
        Returns:
            Seconds until expiry (0 if already expired)
        """
        current_time = int(datetime.now(timezone.utc).timestamp())
        return max(0, self.exp - current_time)

    def is_access_token(self) -> bool:
        """Check if this is an access token.
        
        Returns:
            True if access token, False otherwise
        """
        return self.token_use == 'access'

    def is_id_token(self) -> bool:
        """Check if this is an ID token.
        
        Returns:
            True if ID token, False otherwise
        """
        return self.token_use == 'id'

    def to_dict(self) -> Dict[str, Any]:
        """Convert JWT claims to dictionary.
        
        Returns:
            Dictionary representation of JWT claims
        """
        result = {
            'user_id': self.user_id,
            'username': self.username,
            'email': self.email,
            'client_id': self.client_id,
            'token_use': self.token_use,
            'exp': self.exp,
            'iat': self.iat,
            'iss': self.iss,
            'aud': self.aud,
            'is_expired': self.is_expired(),
            'time_until_expiry': self.time_until_expiry()
        }
        
        if self.auth_time is not None:
            result['auth_time'] = self.auth_time
            
        if self.custom_claims:
            result['custom_claims'] = self.custom_claims
            
        return result

    def validate(self) -> List[str]:
        """Validate JWT claims structure.
        
        Returns:
            List of validation error messages
        """
        errors = []
        
        # Validate required string fields
        required_string_fields = [
            ('user_id', self.user_id),
            ('username', self.username),
            ('email', self.email),
            ('client_id', self.client_id),
            ('token_use', self.token_use),
            ('iss', self.iss),
            ('aud', self.aud)
        ]
        
        for field_name, value in required_string_fields:
            if not isinstance(value, str):
                errors.append(f"{field_name} must be a string")
            elif len(value.strip()) == 0:
                errors.append(f"{field_name} cannot be empty")
        
        # Validate numeric fields
        numeric_fields = [
            ('exp', self.exp),
            ('iat', self.iat)
        ]
        
        for field_name, value in numeric_fields:
            if not isinstance(value, int):
                errors.append(f"{field_name} must be an integer")
            elif value <= 0:
                errors.append(f"{field_name} must be positive")
        
        # Validate token_use value
        if isinstance(self.token_use, str):
            valid_token_uses = ['access', 'id']
            if self.token_use not in valid_token_uses:
                errors.append(
                    f"token_use must be one of: {', '.join(valid_token_uses)}"
                )
        
        # Validate email format (basic check)
        if isinstance(self.email, str) and self.email:
            if '@' not in self.email:
                errors.append("email must be a valid email address")
        
        return errors


@dataclass
class UserContext:
    """User context information for authenticated requests.
    
    Contains user details and authentication status
    for request processing and audit logging.
    
    Attributes:
        user_id: Unique user identifier
        username: Username from authentication
        email: User email address
        authenticated: Whether user is authenticated
        token_claims: JWT token claims
        session_id: Optional session identifier
        permissions: List of user permissions
        metadata: Additional user metadata
    """
    user_id: str
    username: str
    email: str
    authenticated: bool
    token_claims: JWTClaims
    session_id: Optional[str] = None
    permissions: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserContext':
        """Create UserContext instance from dictionary.
        
        Args:
            data: Dictionary containing user context data
            
        Returns:
            UserContext instance
        """
        token_claims = JWTClaims.from_dict(data['token_claims'])
        
        return cls(
            user_id=data['user_id'],
            username=data['username'],
            email=data['email'],
            authenticated=data['authenticated'],
            token_claims=token_claims,
            session_id=data.get('session_id'),
            permissions=data.get('permissions', []),
            metadata=data.get('metadata', {})
        )

    def has_permission(self, permission: str) -> bool:
        """Check if user has specific permission.
        
        Args:
            permission: Permission to check
            
        Returns:
            True if user has permission, False otherwise
        """
        return permission in self.permissions

    def add_permission(self, permission: str) -> None:
        """Add permission to user context.
        
        Args:
            permission: Permission to add
        """
        if permission not in self.permissions:
            self.permissions.append(permission)

    def remove_permission(self, permission: str) -> None:
        """Remove permission from user context.
        
        Args:
            permission: Permission to remove
        """
        if permission in self.permissions:
            self.permissions.remove(permission)

    def is_token_expired(self) -> bool:
        """Check if user's token is expired.
        
        Returns:
            True if token is expired, False otherwise
        """
        return self.token_claims.is_expired()

    def to_dict(self) -> Dict[str, Any]:
        """Convert user context to dictionary.
        
        Returns:
            Dictionary representation of user context
        """
        result = {
            'user_id': self.user_id,
            'username': self.username,
            'email': self.email,
            'authenticated': self.authenticated,
            'token_claims': self.token_claims.to_dict(),
            'permissions': self.permissions,
            'metadata': self.metadata,
            'is_token_expired': self.is_token_expired()
        }
        
        if self.session_id is not None:
            result['session_id'] = self.session_id
            
        return result

    def validate(self) -> List[str]:
        """Validate user context structure.
        
        Returns:
            List of validation error messages
        """
        errors = []
        
        # Validate required string fields
        required_string_fields = [
            ('user_id', self.user_id),
            ('username', self.username),
            ('email', self.email)
        ]
        
        for field_name, value in required_string_fields:
            if not isinstance(value, str):
                errors.append(f"{field_name} must be a string")
            elif len(value.strip()) == 0:
                errors.append(f"{field_name} cannot be empty")
        
        # Validate authenticated field
        if not isinstance(self.authenticated, bool):
            errors.append("authenticated must be a boolean")
        
        # Validate token_claims
        if not isinstance(self.token_claims, JWTClaims):
            errors.append("token_claims must be a JWTClaims object")
        else:
            claims_errors = self.token_claims.validate()
            errors.extend([f"token_claims.{error}" for error in claims_errors])
        
        # Validate permissions list
        if not isinstance(self.permissions, list):
            errors.append("permissions must be a list")
        else:
            for i, permission in enumerate(self.permissions):
                if not isinstance(permission, str):
                    errors.append(f"permissions[{i}] must be a string")
        
        # Validate metadata
        if not isinstance(self.metadata, dict):
            errors.append("metadata must be a dictionary")
        
        return errors


@dataclass
class AuthenticationError:
    """Authentication error information.
    
    Contains detailed error information for authentication failures
    with troubleshooting guidance.
    
    Attributes:
        error_code: Specific error code
        error_message: Human-readable error message
        error_type: Category of error
        suggested_action: Suggested action to resolve error
        timestamp: When the error occurred
        request_id: Optional request identifier
    """
    error_code: str
    error_message: str
    error_type: str
    suggested_action: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    request_id: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AuthenticationError':
        """Create AuthenticationError instance from dictionary.
        
        Args:
            data: Dictionary containing error data
            
        Returns:
            AuthenticationError instance
        """
        timestamp_str = data.get('timestamp')
        if isinstance(timestamp_str, str):
            timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        else:
            timestamp = timestamp_str or datetime.now(timezone.utc)
        
        return cls(
            error_code=data['error_code'],
            error_message=data['error_message'],
            error_type=data['error_type'],
            suggested_action=data['suggested_action'],
            timestamp=timestamp,
            request_id=data.get('request_id')
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert authentication error to dictionary.
        
        Returns:
            Dictionary representation of error
        """
        result = {
            'error_code': self.error_code,
            'error_message': self.error_message,
            'error_type': self.error_type,
            'suggested_action': self.suggested_action,
            'timestamp': self.timestamp.isoformat()
        }
        
        if self.request_id is not None:
            result['request_id'] = self.request_id
            
        return result

    @classmethod
    def invalid_token(cls, message: str = "Invalid JWT token") -> 'AuthenticationError':
        """Create invalid token error.
        
        Args:
            message: Custom error message
            
        Returns:
            AuthenticationError for invalid token
        """
        return cls(
            error_code='INVALID_TOKEN',
            error_message=message,
            error_type='authentication_error',
            suggested_action='Provide a valid JWT token in Authorization header'
        )

    @classmethod
    def expired_token(cls, message: str = "JWT token has expired") -> 'AuthenticationError':
        """Create expired token error.
        
        Args:
            message: Custom error message
            
        Returns:
            AuthenticationError for expired token
        """
        return cls(
            error_code='EXPIRED_TOKEN',
            error_message=message,
            error_type='authentication_error',
            suggested_action='Refresh your authentication token and try again'
        )

    @classmethod
    def missing_token(cls, message: str = "Authorization header missing") -> 'AuthenticationError':
        """Create missing token error.
        
        Args:
            message: Custom error message
            
        Returns:
            AuthenticationError for missing token
        """
        return cls(
            error_code='MISSING_TOKEN',
            error_message=message,
            error_type='authentication_error',
            suggested_action='Include Authorization header with Bearer token'
        )

    @classmethod
    def cognito_error(cls, message: str) -> 'AuthenticationError':
        """Create Cognito service error.
        
        Args:
            message: Error message from Cognito
            
        Returns:
            AuthenticationError for Cognito service issues
        """
        return cls(
            error_code='COGNITO_ERROR',
            error_message=f"Cognito authentication failed: {message}",
            error_type='service_error',
            suggested_action='Check Cognito configuration and try again'
        )