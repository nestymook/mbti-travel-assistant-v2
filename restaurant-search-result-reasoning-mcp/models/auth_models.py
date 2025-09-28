"""
Authentication data models for reasoning MCP server.

This module contains models for AWS Cognito authentication, JWT token handling,
and user context management for the restaurant reasoning system.
"""

import json
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone


@dataclass
class CognitoConfig:
    """
    AWS Cognito User Pool configuration.
    
    Contains all necessary configuration for Cognito authentication
    including user pool details and JWT validation settings.
    """
    user_pool_id: str
    client_id: str
    region: str
    discovery_url: str
    jwks_url: str
    issuer_url: str
    user_pool_domain: Optional[str] = None
    client_secret: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert Cognito config to dictionary."""
        result = {
            "user_pool_id": self.user_pool_id,
            "client_id": self.client_id,
            "region": self.region,
            "discovery_url": self.discovery_url,
            "jwks_url": self.jwks_url,
            "issuer_url": self.issuer_url
        }
        
        if self.user_pool_domain is not None:
            result["user_pool_domain"] = self.user_pool_domain
            
        if self.client_secret is not None:
            result["client_secret"] = self.client_secret
            
        return result
    
    def to_json(self) -> str:
        """Convert Cognito config to JSON string."""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CognitoConfig":
        """Create CognitoConfig instance from dictionary."""
        return cls(
            user_pool_id=data["user_pool_id"],
            client_id=data["client_id"],
            region=data["region"],
            discovery_url=data["discovery_url"],
            jwks_url=data["jwks_url"],
            issuer_url=data["issuer_url"],
            user_pool_domain=data.get("user_pool_domain"),
            client_secret=data.get("client_secret")
        )
    
    @classmethod
    def from_json(cls, json_str: str) -> "CognitoConfig":
        """Create CognitoConfig instance from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)


@dataclass
class JWTClaims:
    """
    JWT token claims extracted from Cognito tokens.
    
    Contains standard and custom claims from JWT tokens
    for user identification and authorization.
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
    
    def is_expired(self) -> bool:
        """Check if the JWT token is expired."""
        current_time = int(datetime.now(timezone.utc).timestamp())
        return current_time >= self.exp
    
    def time_until_expiry(self) -> int:
        """Get seconds until token expiry."""
        current_time = int(datetime.now(timezone.utc).timestamp())
        return max(0, self.exp - current_time)
    
    def is_access_token(self) -> bool:
        """Check if this is an access token."""
        return self.token_use == "access"
    
    def is_id_token(self) -> bool:
        """Check if this is an ID token."""
        return self.token_use == "id"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert JWT claims to dictionary."""
        result = {
            "user_id": self.user_id,
            "username": self.username,
            "email": self.email,
            "client_id": self.client_id,
            "token_use": self.token_use,
            "exp": self.exp,
            "iat": self.iat,
            "iss": self.iss,
            "aud": self.aud,
            "is_expired": self.is_expired(),
            "time_until_expiry": self.time_until_expiry()
        }
        
        if self.auth_time is not None:
            result["auth_time"] = self.auth_time
            
        if self.custom_claims:
            result["custom_claims"] = self.custom_claims
            
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "JWTClaims":
        """Create JWTClaims instance from dictionary."""
        return cls(
            user_id=data["user_id"],
            username=data["username"],
            email=data["email"],
            client_id=data["client_id"],
            token_use=data["token_use"],
            exp=data["exp"],
            iat=data["iat"],
            iss=data["iss"],
            aud=data["aud"],
            auth_time=data.get("auth_time"),
            custom_claims=data.get("custom_claims", {})
        )


@dataclass
class AuthenticationTokens:
    """
    Complete set of authentication tokens from Cognito.
    
    Contains ID token, access token, and refresh token
    with metadata about token validity and usage.
    """
    id_token: str
    access_token: str
    refresh_token: str
    expires_in: int
    token_type: str = "Bearer"
    issued_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Set issued_at timestamp if not provided."""
        if self.issued_at is None:
            self.issued_at = datetime.now(timezone.utc)
    
    def is_expired(self) -> bool:
        """Check if tokens are expired based on expires_in."""
        if self.issued_at is None:
            return True
        
        current_time = datetime.now(timezone.utc)
        expiry_time = self.issued_at.timestamp() + self.expires_in
        return current_time.timestamp() >= expiry_time
    
    def time_until_expiry(self) -> int:
        """Get seconds until token expiry."""
        if self.issued_at is None:
            return 0
        
        current_time = datetime.now(timezone.utc)
        expiry_time = self.issued_at.timestamp() + self.expires_in
        return max(0, int(expiry_time - current_time.timestamp()))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert authentication tokens to dictionary."""
        result = {
            "id_token": self.id_token,
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "expires_in": self.expires_in,
            "token_type": self.token_type,
            "is_expired": self.is_expired(),
            "time_until_expiry": self.time_until_expiry()
        }
        
        if self.issued_at is not None:
            result["issued_at"] = self.issued_at.isoformat()
            
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AuthenticationTokens":
        """Create AuthenticationTokens instance from dictionary."""
        issued_at = None
        if "issued_at" in data:
            issued_at = datetime.fromisoformat(data["issued_at"])
        
        return cls(
            id_token=data["id_token"],
            access_token=data["access_token"],
            refresh_token=data["refresh_token"],
            expires_in=data["expires_in"],
            token_type=data.get("token_type", "Bearer"),
            issued_at=issued_at
        )


@dataclass
class UserContext:
    """
    User context information for authenticated requests.
    
    Contains user details and authentication status
    for request processing and audit logging.
    """
    user_id: str
    username: str
    email: str
    authenticated: bool
    token_claims: JWTClaims
    session_id: Optional[str] = None
    permissions: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def has_permission(self, permission: str) -> bool:
        """Check if user has specific permission."""
        return permission in self.permissions
    
    def add_permission(self, permission: str) -> None:
        """Add permission to user context."""
        if permission not in self.permissions:
            self.permissions.append(permission)
    
    def remove_permission(self, permission: str) -> None:
        """Remove permission from user context."""
        if permission in self.permissions:
            self.permissions.remove(permission)
    
    def is_token_expired(self) -> bool:
        """Check if user's token is expired."""
        return self.token_claims.is_expired()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert user context to dictionary."""
        result = {
            "user_id": self.user_id,
            "username": self.username,
            "email": self.email,
            "authenticated": self.authenticated,
            "token_claims": self.token_claims.to_dict(),
            "permissions": self.permissions,
            "metadata": self.metadata,
            "is_token_expired": self.is_token_expired()
        }
        
        if self.session_id is not None:
            result["session_id"] = self.session_id
            
        return result
    
    def to_json(self) -> str:
        """Convert user context to JSON string."""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UserContext":
        """Create UserContext instance from dictionary."""
        token_claims = JWTClaims.from_dict(data["token_claims"])
        
        return cls(
            user_id=data["user_id"],
            username=data["username"],
            email=data["email"],
            authenticated=data["authenticated"],
            token_claims=token_claims,
            session_id=data.get("session_id"),
            permissions=data.get("permissions", []),
            metadata=data.get("metadata", {})
        )


@dataclass
class AuthenticationError:
    """
    Authentication error information.
    
    Contains detailed error information for authentication failures
    with troubleshooting guidance.
    """
    error_code: str
    error_message: str
    error_type: str
    suggested_action: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    request_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert authentication error to dictionary."""
        result = {
            "error_code": self.error_code,
            "error_message": self.error_message,
            "error_type": self.error_type,
            "suggested_action": self.suggested_action,
            "timestamp": self.timestamp.isoformat()
        }
        
        if self.request_id is not None:
            result["request_id"] = self.request_id
            
        return result
    
    def to_json(self) -> str:
        """Convert authentication error to JSON string."""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AuthenticationError":
        """Create AuthenticationError instance from dictionary."""
        timestamp = datetime.fromisoformat(data["timestamp"])
        
        return cls(
            error_code=data["error_code"],
            error_message=data["error_message"],
            error_type=data["error_type"],
            suggested_action=data["suggested_action"],
            timestamp=timestamp,
            request_id=data.get("request_id")
        )