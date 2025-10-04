"""
JWT Token Validator for Cognito User Pool authentication.

This module provides JWT token validation using the existing Cognito User Pool
configuration with proper JWKS verification and user context extraction.
"""

import jwt
import requests
import structlog
import json
import base64
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from dataclasses import dataclass
from functools import lru_cache
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from config.settings import get_settings

logger = structlog.get_logger(__name__)


@dataclass
class UserContext:
    """User context extracted from JWT token claims."""
    
    user_id: str
    username: str
    email: Optional[str] = None
    token_claims: Dict[str, Any] = None
    authenticated_at: datetime = None
    
    def __post_init__(self):
        if self.authenticated_at is None:
            self.authenticated_at = datetime.now(timezone.utc)
        if self.token_claims is None:
            self.token_claims = {}


class JWTValidationError(Exception):
    """Exception raised when JWT validation fails."""
    pass


class JWTValidator:
    """JWT token validator for Cognito User Pool authentication."""
    
    def __init__(self):
        self.settings = get_settings()
        self.cognito_config = self.settings.cognito
        self._jwks_cache = {}
        self._jwks_cache_timestamp = None
        
        logger.info(
            "Initializing JWT validator",
            user_pool_id=self.cognito_config.user_pool_id,
            client_id=self.cognito_config.client_id,
            discovery_url=self.cognito_config.discovery_url
        )
    
    @lru_cache(maxsize=1)
    def _get_discovery_document(self) -> Dict[str, Any]:
        """Get OpenID Connect discovery document from Cognito."""
        try:
            response = requests.get(
                self.cognito_config.discovery_url,
                timeout=10
            )
            response.raise_for_status()
            
            discovery_doc = response.json()
            logger.debug(
                "Retrieved discovery document",
                issuer=discovery_doc.get("issuer"),
                jwks_uri=discovery_doc.get("jwks_uri")
            )
            
            return discovery_doc
            
        except requests.RequestException as e:
            logger.error(
                "Failed to retrieve discovery document",
                error=str(e),
                discovery_url=self.cognito_config.discovery_url
            )
            raise JWTValidationError(f"Failed to retrieve discovery document: {e}")
    
    def _get_jwks(self) -> Dict[str, Any]:
        """Get JSON Web Key Set (JWKS) from Cognito."""
        # Cache JWKS for 1 hour
        now = datetime.now(timezone.utc)
        if (self._jwks_cache_timestamp and 
            (now - self._jwks_cache_timestamp).total_seconds() < 3600 and
            self._jwks_cache):
            return self._jwks_cache
        
        try:
            # Get JWKS URI from discovery document
            discovery_doc = self._get_discovery_document()
            jwks_uri = discovery_doc.get("jwks_uri", self.cognito_config.jwks_uri)
            
            response = requests.get(jwks_uri, timeout=10)
            response.raise_for_status()
            
            jwks = response.json()
            self._jwks_cache = jwks
            self._jwks_cache_timestamp = now
            
            logger.debug(
                "Retrieved JWKS",
                keys_count=len(jwks.get("keys", [])),
                jwks_uri=jwks_uri
            )
            
            return jwks
            
        except requests.RequestException as e:
            logger.error(
                "Failed to retrieve JWKS",
                error=str(e),
                jwks_uri=jwks_uri
            )
            raise JWTValidationError(f"Failed to retrieve JWKS: {e}")
    
    def _get_signing_key(self, token_header: Dict[str, Any]) -> str:
        """Get the signing key for JWT verification."""
        kid = token_header.get("kid")
        if not kid:
            raise JWTValidationError("Token header missing 'kid' claim")
        
        jwks = self._get_jwks()
        keys = jwks.get("keys", [])
        
        # Find the key with matching kid
        signing_key = None
        for key in keys:
            if key.get("kid") == kid:
                signing_key = key
                break
        
        if not signing_key:
            raise JWTValidationError(f"Unable to find signing key with kid: {kid}")
        
        # Convert JWK to PEM format using cryptography
        try:
            # Extract RSA key components
            n = self._base64url_decode(signing_key["n"])
            e = self._base64url_decode(signing_key["e"])
            
            # Convert to integers
            n_int = int.from_bytes(n, byteorder='big')
            e_int = int.from_bytes(e, byteorder='big')
            
            # Create RSA public key
            public_key = rsa.RSAPublicNumbers(e_int, n_int).public_key(default_backend())
            
            # Convert to PEM format
            pem_key = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
            
            if isinstance(pem_key, bytes):
                return pem_key.decode('utf-8')
            return pem_key
            
        except Exception as e:
            logger.error(
                "Failed to construct signing key",
                error=str(e),
                kid=kid
            )
            raise JWTValidationError(f"Failed to construct signing key: {e}")
    
    def _base64url_decode(self, data: str) -> bytes:
        """Decode base64url encoded data."""
        # Add padding if necessary
        padding = 4 - len(data) % 4
        if padding != 4:
            data += '=' * padding
        
        return base64.urlsafe_b64decode(data)
    
    def validate_token(self, token: str) -> UserContext:
        """
        Validate JWT token and extract user context.
        
        Args:
            token: JWT token string
            
        Returns:
            UserContext: Validated user context
            
        Raises:
            JWTValidationError: If token validation fails
        """
        try:
            # Decode token header without verification to get kid
            unverified_header = jwt.get_unverified_header(token)
            
            # Get signing key
            signing_key = self._get_signing_key(unverified_header)
            
            # Verify and decode token
            payload = jwt.decode(
                token,
                signing_key,
                algorithms=[self.cognito_config.algorithm],
                audience=self.cognito_config.audience,
                issuer=self.cognito_config.issuer,
                options={
                    "verify_signature": True,
                    "verify_exp": True,
                    "verify_nbf": True,
                    "verify_iat": True,
                    "verify_aud": True,
                    "verify_iss": True
                }
            )
            
            # Validate token_use claim
            token_use = payload.get("token_use")
            if token_use != self.cognito_config.token_use:
                raise JWTValidationError(
                    f"Invalid token_use: expected {self.cognito_config.token_use}, got {token_use}"
                )
            
            # Extract user context
            user_context = self._extract_user_context(payload)
            
            logger.info(
                "JWT token validated successfully",
                user_id=user_context.user_id,
                username=user_context.username,
                token_use=token_use
            )
            
            return user_context
            
        except jwt.ExpiredSignatureError:
            logger.warning("JWT token has expired")
            raise JWTValidationError("Token has expired")
            
        except jwt.InvalidTokenError as e:
            logger.warning(
                "JWT token validation failed",
                error=str(e)
            )
            raise JWTValidationError(f"Invalid token: {e}")
            
        except Exception as e:
            logger.error(
                "Unexpected error during JWT validation",
                error=str(e)
            )
            raise JWTValidationError(f"Token validation failed: {e}")
    
    def _extract_user_context(self, payload: Dict[str, Any]) -> UserContext:
        """Extract user context from JWT payload."""
        # Extract user information from token claims
        user_id = payload.get("sub")
        username = payload.get("username", payload.get("cognito:username"))
        email = payload.get("email")
        
        if not user_id:
            raise JWTValidationError("Token missing required 'sub' claim")
        
        if not username:
            # Fallback to user_id if username not available
            username = user_id
        
        return UserContext(
            user_id=user_id,
            username=username,
            email=email,
            token_claims=payload,
            authenticated_at=datetime.now(timezone.utc)
        )
    
    def is_token_expired(self, token: str) -> bool:
        """Check if token is expired without full validation."""
        try:
            payload = jwt.decode(
                token,
                options={"verify_signature": False, "verify_exp": False}
            )
            exp = payload.get("exp")
            if exp:
                return datetime.fromtimestamp(exp, timezone.utc) < datetime.now(timezone.utc)
            return False
        except Exception:
            return True


# Global JWT validator instance
_jwt_validator = None


def get_jwt_validator() -> JWTValidator:
    """Get the global JWT validator instance."""
    global _jwt_validator
    if _jwt_validator is None:
        _jwt_validator = JWTValidator()
    return _jwt_validator


# FastAPI security scheme
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> UserContext:
    """
    FastAPI dependency to get the current authenticated user from JWT token.
    
    Args:
        credentials: HTTP Bearer token credentials from FastAPI security
        
    Returns:
        UserContext: Validated user context
        
    Raises:
        HTTPException: If authentication fails
    """
    try:
        validator = get_jwt_validator()
        user_context = validator.validate_token(credentials.credentials)
        return user_context
        
    except JWTValidationError as e:
        logger.warning(
            "JWT authentication failed",
            error=str(e),
            token_preview=credentials.credentials[:20] + "..." if len(credentials.credentials) > 20 else credentials.credentials
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error(
            "Unexpected error during authentication",
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service error"
        )