"""
Authentication Models for Enhanced MCP Status Check

This module contains authentication-related data models for secure
MCP and REST health check operations.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Union
import json
from abc import ABC, abstractmethod


class AuthenticationType(Enum):
    """Authentication type enumeration."""
    NONE = "NONE"
    JWT = "JWT"
    BEARER_TOKEN = "BEARER_TOKEN"
    API_KEY = "API_KEY"
    BASIC_AUTH = "BASIC_AUTH"
    OAUTH2 = "OAUTH2"
    CUSTOM_HEADER = "CUSTOM_HEADER"


class AuthenticationError(Exception):
    """Authentication-related error."""
    
    def __init__(self, message: str, error_type: str = "AUTH_ERROR", details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.error_type = error_type
        self.details = details or {}


@dataclass
class JWTTokenInfo:
    """JWT token information and metadata."""
    
    token: str
    expires_at: Optional[datetime] = None
    issued_at: Optional[datetime] = None
    issuer: Optional[str] = None
    audience: Optional[str] = None
    subject: Optional[str] = None
    scopes: List[str] = field(default_factory=list)
    
    def is_expired(self, buffer_seconds: int = 60) -> bool:
        """
        Check if token is expired or will expire soon.
        
        Args:
            buffer_seconds: Buffer time before expiration to consider token expired
            
        Returns:
            bool: True if token is expired or will expire within buffer time
        """
        if not self.expires_at:
            return False
        
        buffer_time = datetime.now() + timedelta(seconds=buffer_seconds)
        return self.expires_at <= buffer_time
    
    def time_until_expiry(self) -> Optional[timedelta]:
        """
        Get time until token expiry.
        
        Returns:
            Optional[timedelta]: Time until expiry, None if no expiry set
        """
        if not self.expires_at:
            return None
        
        return self.expires_at - datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "token": self.token,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "issued_at": self.issued_at.isoformat() if self.issued_at else None,
            "issuer": self.issuer,
            "audience": self.audience,
            "subject": self.subject,
            "scopes": self.scopes
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'JWTTokenInfo':
        """Create instance from dictionary."""
        expires_at = None
        if data.get("expires_at"):
            expires_at = datetime.fromisoformat(data["expires_at"])
        
        issued_at = None
        if data.get("issued_at"):
            issued_at = datetime.fromisoformat(data["issued_at"])
        
        return cls(
            token=data.get("token", ""),
            expires_at=expires_at,
            issued_at=issued_at,
            issuer=data.get("issuer"),
            audience=data.get("audience"),
            subject=data.get("subject"),
            scopes=data.get("scopes", [])
        )


@dataclass
class AuthenticationConfig:
    """Authentication configuration for health checks."""
    
    auth_type: AuthenticationType = AuthenticationType.NONE
    
    # JWT Configuration
    jwt_token: Optional[str] = None
    jwt_discovery_url: Optional[str] = None
    jwt_client_id: Optional[str] = None
    jwt_client_secret: Optional[str] = None
    jwt_scope: List[str] = field(default_factory=list)
    
    # Bearer Token Configuration
    bearer_token: Optional[str] = None
    
    # API Key Configuration
    api_key: Optional[str] = None
    api_key_header: str = "X-API-Key"
    
    # Basic Auth Configuration
    username: Optional[str] = None
    password: Optional[str] = None
    
    # OAuth2 Configuration
    oauth2_token_url: Optional[str] = None
    oauth2_client_id: Optional[str] = None
    oauth2_client_secret: Optional[str] = None
    oauth2_scope: List[str] = field(default_factory=list)
    
    # Custom Headers
    custom_headers: Dict[str, str] = field(default_factory=dict)
    
    # Token Refresh Configuration
    auto_refresh_enabled: bool = True
    refresh_buffer_seconds: int = 300  # 5 minutes
    max_refresh_attempts: int = 3
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "auth_type": self.auth_type.value,
            "jwt_token": self.jwt_token,
            "jwt_discovery_url": self.jwt_discovery_url,
            "jwt_client_id": self.jwt_client_id,
            "jwt_client_secret": self.jwt_client_secret,
            "jwt_scope": self.jwt_scope,
            "bearer_token": self.bearer_token,
            "api_key": self.api_key,
            "api_key_header": self.api_key_header,
            "username": self.username,
            "password": self.password,
            "oauth2_token_url": self.oauth2_token_url,
            "oauth2_client_id": self.oauth2_client_id,
            "oauth2_client_secret": self.oauth2_client_secret,
            "oauth2_scope": self.oauth2_scope,
            "custom_headers": self.custom_headers,
            "auto_refresh_enabled": self.auto_refresh_enabled,
            "refresh_buffer_seconds": self.refresh_buffer_seconds,
            "max_refresh_attempts": self.max_refresh_attempts
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AuthenticationConfig':
        """Create instance from dictionary."""
        auth_type = AuthenticationType(data.get("auth_type", "NONE"))
        
        return cls(
            auth_type=auth_type,
            jwt_token=data.get("jwt_token"),
            jwt_discovery_url=data.get("jwt_discovery_url"),
            jwt_client_id=data.get("jwt_client_id"),
            jwt_client_secret=data.get("jwt_client_secret"),
            jwt_scope=data.get("jwt_scope", []),
            bearer_token=data.get("bearer_token"),
            api_key=data.get("api_key"),
            api_key_header=data.get("api_key_header", "X-API-Key"),
            username=data.get("username"),
            password=data.get("password"),
            oauth2_token_url=data.get("oauth2_token_url"),
            oauth2_client_id=data.get("oauth2_client_id"),
            oauth2_client_secret=data.get("oauth2_client_secret"),
            oauth2_scope=data.get("oauth2_scope", []),
            custom_headers=data.get("custom_headers", {}),
            auto_refresh_enabled=data.get("auto_refresh_enabled", True),
            refresh_buffer_seconds=data.get("refresh_buffer_seconds", 300),
            max_refresh_attempts=data.get("max_refresh_attempts", 3)
        )
    
    def validate(self) -> List[str]:
        """Validate authentication configuration."""
        errors = []
        
        if self.auth_type == AuthenticationType.JWT:
            if not self.jwt_token and not (self.jwt_client_id and self.jwt_client_secret):
                errors.append("JWT authentication requires either token or client credentials")
            
            if self.jwt_client_id and self.jwt_client_secret and not self.jwt_discovery_url:
                errors.append("JWT client credentials require discovery URL")
        
        elif self.auth_type == AuthenticationType.BEARER_TOKEN:
            if not self.bearer_token:
                errors.append("Bearer token authentication requires token")
        
        elif self.auth_type == AuthenticationType.API_KEY:
            if not self.api_key:
                errors.append("API key authentication requires key")
            if not self.api_key_header:
                errors.append("API key authentication requires header name")
        
        elif self.auth_type == AuthenticationType.BASIC_AUTH:
            if not self.username or not self.password:
                errors.append("Basic authentication requires username and password")
        
        elif self.auth_type == AuthenticationType.OAUTH2:
            if not all([self.oauth2_token_url, self.oauth2_client_id, self.oauth2_client_secret]):
                errors.append("OAuth2 authentication requires token URL and client credentials")
        
        # Validate refresh configuration
        if self.refresh_buffer_seconds < 0:
            errors.append("Refresh buffer seconds must be non-negative")
        
        if self.max_refresh_attempts < 1:
            errors.append("Max refresh attempts must be at least 1")
        
        return errors
    
    def has_credentials(self) -> bool:
        """Check if configuration has valid credentials."""
        if self.auth_type == AuthenticationType.NONE:
            return True
        
        validation_errors = self.validate()
        return len(validation_errors) == 0


@dataclass
class AuthenticationResult:
    """Result of authentication operation."""
    
    success: bool
    auth_headers: Dict[str, str] = field(default_factory=dict)
    token_info: Optional[JWTTokenInfo] = None
    error_message: Optional[str] = None
    error_type: Optional[str] = None
    expires_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "success": self.success,
            "auth_headers": self.auth_headers,
            "token_info": self.token_info.to_dict() if self.token_info else None,
            "error_message": self.error_message,
            "error_type": self.error_type,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AuthenticationResult':
        """Create instance from dictionary."""
        token_info = None
        if data.get("token_info"):
            token_info = JWTTokenInfo.from_dict(data["token_info"])
        
        expires_at = None
        if data.get("expires_at"):
            expires_at = datetime.fromisoformat(data["expires_at"])
        
        return cls(
            success=data.get("success", False),
            auth_headers=data.get("auth_headers", {}),
            token_info=token_info,
            error_message=data.get("error_message"),
            error_type=data.get("error_type"),
            expires_at=expires_at
        )


@dataclass
class SecureCredentialStore:
    """Secure storage for authentication credentials."""
    
    # In-memory credential storage (should be encrypted in production)
    _credentials: Dict[str, Any] = field(default_factory=dict, init=False)
    _tokens: Dict[str, JWTTokenInfo] = field(default_factory=dict, init=False)
    
    def store_credential(self, key: str, value: Any, encrypt: bool = True) -> None:
        """
        Store credential securely.
        
        Args:
            key: Credential key/identifier
            value: Credential value
            encrypt: Whether to encrypt the value (placeholder for future encryption)
        """
        # TODO: Implement actual encryption in production
        self._credentials[key] = value
    
    def get_credential(self, key: str, decrypt: bool = True) -> Optional[Any]:
        """
        Retrieve credential securely.
        
        Args:
            key: Credential key/identifier
            decrypt: Whether to decrypt the value (placeholder for future encryption)
            
        Returns:
            Optional[Any]: Credential value or None if not found
        """
        # TODO: Implement actual decryption in production
        return self._credentials.get(key)
    
    def store_token(self, server_name: str, token_info: JWTTokenInfo) -> None:
        """
        Store JWT token information.
        
        Args:
            server_name: Server identifier
            token_info: JWT token information
        """
        self._tokens[server_name] = token_info
    
    def get_token(self, server_name: str) -> Optional[JWTTokenInfo]:
        """
        Retrieve JWT token information.
        
        Args:
            server_name: Server identifier
            
        Returns:
            Optional[JWTTokenInfo]: Token information or None if not found
        """
        return self._tokens.get(server_name)
    
    def remove_credential(self, key: str) -> bool:
        """
        Remove credential from storage.
        
        Args:
            key: Credential key/identifier
            
        Returns:
            bool: True if credential was removed, False if not found
        """
        if key in self._credentials:
            del self._credentials[key]
            return True
        return False
    
    def remove_token(self, server_name: str) -> bool:
        """
        Remove token from storage.
        
        Args:
            server_name: Server identifier
            
        Returns:
            bool: True if token was removed, False if not found
        """
        if server_name in self._tokens:
            del self._tokens[server_name]
            return True
        return False
    
    def clear_all(self) -> None:
        """Clear all stored credentials and tokens."""
        self._credentials.clear()
        self._tokens.clear()
    
    def list_stored_servers(self) -> List[str]:
        """
        List servers with stored tokens.
        
        Returns:
            List[str]: List of server names with stored tokens
        """
        return list(self._tokens.keys())
    
    def cleanup_expired_tokens(self) -> int:
        """
        Remove expired tokens from storage.
        
        Returns:
            int: Number of expired tokens removed
        """
        expired_servers = []
        
        for server_name, token_info in self._tokens.items():
            if token_info.is_expired():
                expired_servers.append(server_name)
        
        for server_name in expired_servers:
            del self._tokens[server_name]
        
        return len(expired_servers)


@dataclass
class AuthenticationMetrics:
    """Metrics for authentication operations."""
    
    total_auth_attempts: int = 0
    successful_auth_attempts: int = 0
    failed_auth_attempts: int = 0
    token_refresh_attempts: int = 0
    successful_token_refreshes: int = 0
    failed_token_refreshes: int = 0
    
    # Error tracking
    auth_errors_by_type: Dict[str, int] = field(default_factory=dict)
    last_auth_error: Optional[str] = None
    last_auth_error_time: Optional[datetime] = None
    
    def record_auth_attempt(self, success: bool, error_type: Optional[str] = None) -> None:
        """
        Record authentication attempt.
        
        Args:
            success: Whether authentication was successful
            error_type: Type of error if authentication failed
        """
        self.total_auth_attempts += 1
        
        if success:
            self.successful_auth_attempts += 1
        else:
            self.failed_auth_attempts += 1
            
            if error_type:
                self.auth_errors_by_type[error_type] = self.auth_errors_by_type.get(error_type, 0) + 1
                self.last_auth_error = error_type
                self.last_auth_error_time = datetime.now()
    
    def record_token_refresh(self, success: bool, error_type: Optional[str] = None) -> None:
        """
        Record token refresh attempt.
        
        Args:
            success: Whether token refresh was successful
            error_type: Type of error if refresh failed
        """
        self.token_refresh_attempts += 1
        
        if success:
            self.successful_token_refreshes += 1
        else:
            self.failed_token_refreshes += 1
            
            if error_type:
                self.auth_errors_by_type[error_type] = self.auth_errors_by_type.get(error_type, 0) + 1
    
    def get_auth_success_rate(self) -> float:
        """
        Get authentication success rate.
        
        Returns:
            float: Success rate as percentage (0.0 to 100.0)
        """
        if self.total_auth_attempts == 0:
            return 0.0
        
        return (self.successful_auth_attempts / self.total_auth_attempts) * 100.0
    
    def get_token_refresh_success_rate(self) -> float:
        """
        Get token refresh success rate.
        
        Returns:
            float: Success rate as percentage (0.0 to 100.0)
        """
        if self.token_refresh_attempts == 0:
            return 0.0
        
        return (self.successful_token_refreshes / self.token_refresh_attempts) * 100.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "total_auth_attempts": self.total_auth_attempts,
            "successful_auth_attempts": self.successful_auth_attempts,
            "failed_auth_attempts": self.failed_auth_attempts,
            "token_refresh_attempts": self.token_refresh_attempts,
            "successful_token_refreshes": self.successful_token_refreshes,
            "failed_token_refreshes": self.failed_token_refreshes,
            "auth_errors_by_type": self.auth_errors_by_type,
            "last_auth_error": self.last_auth_error,
            "last_auth_error_time": self.last_auth_error_time.isoformat() if self.last_auth_error_time else None,
            "auth_success_rate": self.get_auth_success_rate(),
            "token_refresh_success_rate": self.get_token_refresh_success_rate()
        }