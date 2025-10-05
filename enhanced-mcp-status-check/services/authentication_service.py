"""
Authentication Service for Enhanced MCP Status Check

This service handles authentication for both MCP and REST health checks,
including JWT token management, automatic refresh, and secure credential storage.
"""

import asyncio
import base64
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import aiohttp
import jwt
import logging

from models.auth_models import (
    AuthenticationType,
    AuthenticationConfig,
    AuthenticationResult,
    AuthenticationError,
    JWTTokenInfo,
    SecureCredentialStore,
    AuthenticationMetrics
)


logger = logging.getLogger(__name__)


class AuthenticationService:
    """
    Authentication service for MCP and REST health checks.
    
    Provides JWT authentication, token refresh, and secure credential management
    for both MCP tools/list requests and REST health check requests.
    """
    
    def __init__(self, session: Optional[aiohttp.ClientSession] = None):
        """
        Initialize authentication service.
        
        Args:
            session: Optional aiohttp ClientSession for HTTP requests
        """
        self._session = session
        self._owned_session = session is None
        self._credential_store = SecureCredentialStore()
        self._metrics = AuthenticationMetrics()
        self._refresh_locks: Dict[str, asyncio.Lock] = {}
    
    async def __aenter__(self):
        """Async context manager entry."""
        if self._session is None:
            self._session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._owned_session and self._session:
            await self._session.close()
    
    async def authenticate(
        self,
        server_name: str,
        auth_config: AuthenticationConfig,
        force_refresh: bool = False
    ) -> AuthenticationResult:
        """
        Perform authentication and return headers for requests.
        
        Args:
            server_name: Server identifier for credential storage
            auth_config: Authentication configuration
            force_refresh: Force token refresh even if not expired
            
        Returns:
            AuthenticationResult: Authentication result with headers
        """
        try:
            if auth_config.auth_type == AuthenticationType.NONE:
                return AuthenticationResult(success=True)
            
            elif auth_config.auth_type == AuthenticationType.JWT:
                return await self._authenticate_jwt(server_name, auth_config, force_refresh)
            
            elif auth_config.auth_type == AuthenticationType.BEARER_TOKEN:
                return self._authenticate_bearer_token(auth_config)
            
            elif auth_config.auth_type == AuthenticationType.API_KEY:
                return self._authenticate_api_key(auth_config)
            
            elif auth_config.auth_type == AuthenticationType.BASIC_AUTH:
                return self._authenticate_basic_auth(auth_config)
            
            elif auth_config.auth_type == AuthenticationType.OAUTH2:
                return await self._authenticate_oauth2(server_name, auth_config, force_refresh)
            
            elif auth_config.auth_type == AuthenticationType.CUSTOM_HEADER:
                return self._authenticate_custom_headers(auth_config)
            
            else:
                error_msg = f"Unsupported authentication type: {auth_config.auth_type}"
                self._metrics.record_auth_attempt(False, "UNSUPPORTED_AUTH_TYPE")
                return AuthenticationResult(
                    success=False,
                    error_message=error_msg,
                    error_type="UNSUPPORTED_AUTH_TYPE"
                )
        
        except Exception as e:
            logger.error(f"Authentication error for {server_name}: {e}")
            self._metrics.record_auth_attempt(False, "UNEXPECTED_ERROR")
            return AuthenticationResult(
                success=False,
                error_message=f"Authentication error: {str(e)}",
                error_type="UNEXPECTED_ERROR"
            )
    
    async def _authenticate_jwt(
        self,
        server_name: str,
        auth_config: AuthenticationConfig,
        force_refresh: bool = False
    ) -> AuthenticationResult:
        """
        Perform JWT authentication with automatic token refresh.
        
        Args:
            server_name: Server identifier
            auth_config: Authentication configuration
            force_refresh: Force token refresh
            
        Returns:
            AuthenticationResult: JWT authentication result
        """
        # Check for existing valid token
        if not force_refresh:
            existing_token = self._credential_store.get_token(server_name)
            if existing_token and not existing_token.is_expired(auth_config.refresh_buffer_seconds):
                self._metrics.record_auth_attempt(True)
                return AuthenticationResult(
                    success=True,
                    auth_headers={"Authorization": f"Bearer {existing_token.token}"},
                    token_info=existing_token,
                    expires_at=existing_token.expires_at
                )
        
        # Use provided token or obtain new one
        if auth_config.jwt_token:
            # Parse and validate provided token
            try:
                token_info = self._parse_jwt_token(auth_config.jwt_token)
                self._credential_store.store_token(server_name, token_info)
                
                self._metrics.record_auth_attempt(True)
                return AuthenticationResult(
                    success=True,
                    auth_headers={"Authorization": f"Bearer {token_info.token}"},
                    token_info=token_info,
                    expires_at=token_info.expires_at
                )
            
            except Exception as e:
                logger.error(f"Invalid JWT token for {server_name}: {e}")
                self._metrics.record_auth_attempt(False, "INVALID_JWT_TOKEN")
                return AuthenticationResult(
                    success=False,
                    error_message=f"Invalid JWT token: {str(e)}",
                    error_type="INVALID_JWT_TOKEN"
                )
        
        # Obtain token using client credentials
        elif auth_config.jwt_client_id and auth_config.jwt_client_secret:
            return await self._obtain_jwt_token(server_name, auth_config)
        
        else:
            self._metrics.record_auth_attempt(False, "MISSING_JWT_CREDENTIALS")
            return AuthenticationResult(
                success=False,
                error_message="JWT authentication requires token or client credentials",
                error_type="MISSING_JWT_CREDENTIALS"
            )
    
    async def _obtain_jwt_token(
        self,
        server_name: str,
        auth_config: AuthenticationConfig
    ) -> AuthenticationResult:
        """
        Obtain JWT token using client credentials flow.
        
        Args:
            server_name: Server identifier
            auth_config: Authentication configuration
            
        Returns:
            AuthenticationResult: Token acquisition result
        """
        if not auth_config.jwt_discovery_url:
            self._metrics.record_auth_attempt(False, "MISSING_DISCOVERY_URL")
            return AuthenticationResult(
                success=False,
                error_message="JWT discovery URL is required for client credentials flow",
                error_type="MISSING_DISCOVERY_URL"
            )
        
        try:
            # Get token endpoint from discovery document
            token_endpoint = await self._get_token_endpoint(auth_config.jwt_discovery_url)
            
            # Request token using client credentials
            token_data = await self._request_client_credentials_token(
                token_endpoint=token_endpoint,
                client_id=auth_config.jwt_client_id,
                client_secret=auth_config.jwt_client_secret,
                scope=auth_config.jwt_scope
            )
            
            # Parse token response
            access_token = token_data.get("access_token")
            if not access_token:
                self._metrics.record_auth_attempt(False, "NO_ACCESS_TOKEN")
                return AuthenticationResult(
                    success=False,
                    error_message="No access token in response",
                    error_type="NO_ACCESS_TOKEN"
                )
            
            # Create token info
            expires_in = token_data.get("expires_in", 3600)  # Default 1 hour
            expires_at = datetime.now() + timedelta(seconds=expires_in)
            
            token_info = JWTTokenInfo(
                token=access_token,
                expires_at=expires_at,
                issued_at=datetime.now(),
                scopes=auth_config.jwt_scope
            )
            
            # Store token
            self._credential_store.store_token(server_name, token_info)
            
            self._metrics.record_auth_attempt(True)
            return AuthenticationResult(
                success=True,
                auth_headers={"Authorization": f"Bearer {access_token}"},
                token_info=token_info,
                expires_at=expires_at
            )
        
        except Exception as e:
            logger.error(f"Failed to obtain JWT token for {server_name}: {e}")
            self._metrics.record_auth_attempt(False, "TOKEN_ACQUISITION_FAILED")
            return AuthenticationResult(
                success=False,
                error_message=f"Failed to obtain JWT token: {str(e)}",
                error_type="TOKEN_ACQUISITION_FAILED"
            )
    
    async def _get_token_endpoint(self, discovery_url: str) -> str:
        """
        Get token endpoint from OIDC discovery document.
        
        Args:
            discovery_url: OIDC discovery URL
            
        Returns:
            str: Token endpoint URL
            
        Raises:
            AuthenticationError: If discovery fails
        """
        if self._session is None:
            raise AuthenticationError("HTTP session not initialized")
        
        try:
            async with self._session.get(discovery_url) as response:
                if response.status != 200:
                    raise AuthenticationError(f"Discovery request failed: HTTP {response.status}")
                
                discovery_data = await response.json()
                token_endpoint = discovery_data.get("token_endpoint")
                
                if not token_endpoint:
                    raise AuthenticationError("No token endpoint in discovery document")
                
                return token_endpoint
        
        except aiohttp.ClientError as e:
            raise AuthenticationError(f"Discovery request failed: {str(e)}")
        except json.JSONDecodeError as e:
            raise AuthenticationError(f"Invalid discovery document: {str(e)}")
    
    async def _request_client_credentials_token(
        self,
        token_endpoint: str,
        client_id: str,
        client_secret: str,
        scope: List[str]
    ) -> Dict[str, Any]:
        """
        Request token using client credentials flow.
        
        Args:
            token_endpoint: Token endpoint URL
            client_id: OAuth2 client ID
            client_secret: OAuth2 client secret
            scope: Requested scopes
            
        Returns:
            Dict[str, Any]: Token response data
            
        Raises:
            AuthenticationError: If token request fails
        """
        if self._session is None:
            raise AuthenticationError("HTTP session not initialized")
        
        # Prepare request data
        data = {
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret
        }
        
        if scope:
            data["scope"] = " ".join(scope)
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json"
        }
        
        try:
            async with self._session.post(
                token_endpoint,
                data=data,
                headers=headers
            ) as response:
                response_data = await response.json()
                
                if response.status != 200:
                    error_msg = response_data.get("error_description", f"HTTP {response.status}")
                    raise AuthenticationError(f"Token request failed: {error_msg}")
                
                return response_data
        
        except aiohttp.ClientError as e:
            raise AuthenticationError(f"Token request failed: {str(e)}")
        except json.JSONDecodeError as e:
            raise AuthenticationError(f"Invalid token response: {str(e)}")
    
    def _parse_jwt_token(self, token: str) -> JWTTokenInfo:
        """
        Parse JWT token and extract metadata.
        
        Args:
            token: JWT token string
            
        Returns:
            JWTTokenInfo: Parsed token information
            
        Raises:
            AuthenticationError: If token parsing fails
        """
        try:
            # Decode without verification to extract claims
            # In production, should verify signature with proper key
            decoded = jwt.decode(token, options={"verify_signature": False})
            
            # Extract standard claims
            expires_at = None
            if "exp" in decoded:
                expires_at = datetime.fromtimestamp(decoded["exp"])
            
            issued_at = None
            if "iat" in decoded:
                issued_at = datetime.fromtimestamp(decoded["iat"])
            
            scopes = []
            if "scope" in decoded:
                if isinstance(decoded["scope"], str):
                    scopes = decoded["scope"].split()
                elif isinstance(decoded["scope"], list):
                    scopes = decoded["scope"]
            
            return JWTTokenInfo(
                token=token,
                expires_at=expires_at,
                issued_at=issued_at,
                issuer=decoded.get("iss"),
                audience=decoded.get("aud"),
                subject=decoded.get("sub"),
                scopes=scopes
            )
        
        except jwt.InvalidTokenError as e:
            raise AuthenticationError(f"Invalid JWT token: {str(e)}")
        except Exception as e:
            raise AuthenticationError(f"Failed to parse JWT token: {str(e)}")
    
    def _authenticate_bearer_token(self, auth_config: AuthenticationConfig) -> AuthenticationResult:
        """
        Authenticate using bearer token.
        
        Args:
            auth_config: Authentication configuration
            
        Returns:
            AuthenticationResult: Authentication result
        """
        if not auth_config.bearer_token:
            self._metrics.record_auth_attempt(False, "MISSING_BEARER_TOKEN")
            return AuthenticationResult(
                success=False,
                error_message="Bearer token is required",
                error_type="MISSING_BEARER_TOKEN"
            )
        
        self._metrics.record_auth_attempt(True)
        return AuthenticationResult(
            success=True,
            auth_headers={"Authorization": f"Bearer {auth_config.bearer_token}"}
        )
    
    def _authenticate_api_key(self, auth_config: AuthenticationConfig) -> AuthenticationResult:
        """
        Authenticate using API key.
        
        Args:
            auth_config: Authentication configuration
            
        Returns:
            AuthenticationResult: Authentication result
        """
        if not auth_config.api_key:
            self._metrics.record_auth_attempt(False, "MISSING_API_KEY")
            return AuthenticationResult(
                success=False,
                error_message="API key is required",
                error_type="MISSING_API_KEY"
            )
        
        self._metrics.record_auth_attempt(True)
        return AuthenticationResult(
            success=True,
            auth_headers={auth_config.api_key_header: auth_config.api_key}
        )
    
    def _authenticate_basic_auth(self, auth_config: AuthenticationConfig) -> AuthenticationResult:
        """
        Authenticate using basic authentication.
        
        Args:
            auth_config: Authentication configuration
            
        Returns:
            AuthenticationResult: Authentication result
        """
        if not auth_config.username or not auth_config.password:
            self._metrics.record_auth_attempt(False, "MISSING_BASIC_CREDENTIALS")
            return AuthenticationResult(
                success=False,
                error_message="Username and password are required for basic auth",
                error_type="MISSING_BASIC_CREDENTIALS"
            )
        
        # Encode credentials
        credentials = f"{auth_config.username}:{auth_config.password}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        
        self._metrics.record_auth_attempt(True)
        return AuthenticationResult(
            success=True,
            auth_headers={"Authorization": f"Basic {encoded_credentials}"}
        )
    
    async def _authenticate_oauth2(
        self,
        server_name: str,
        auth_config: AuthenticationConfig,
        force_refresh: bool = False
    ) -> AuthenticationResult:
        """
        Authenticate using OAuth2 client credentials flow.
        
        Args:
            server_name: Server identifier
            auth_config: Authentication configuration
            force_refresh: Force token refresh
            
        Returns:
            AuthenticationResult: Authentication result
        """
        # Check for existing valid token
        if not force_refresh:
            existing_token = self._credential_store.get_token(server_name)
            if existing_token and not existing_token.is_expired(auth_config.refresh_buffer_seconds):
                self._metrics.record_auth_attempt(True)
                return AuthenticationResult(
                    success=True,
                    auth_headers={"Authorization": f"Bearer {existing_token.token}"},
                    token_info=existing_token,
                    expires_at=existing_token.expires_at
                )
        
        # Request new token
        try:
            token_data = await self._request_client_credentials_token(
                token_endpoint=auth_config.oauth2_token_url,
                client_id=auth_config.oauth2_client_id,
                client_secret=auth_config.oauth2_client_secret,
                scope=auth_config.oauth2_scope
            )
            
            access_token = token_data.get("access_token")
            if not access_token:
                self._metrics.record_auth_attempt(False, "NO_ACCESS_TOKEN")
                return AuthenticationResult(
                    success=False,
                    error_message="No access token in OAuth2 response",
                    error_type="NO_ACCESS_TOKEN"
                )
            
            # Create token info
            expires_in = token_data.get("expires_in", 3600)
            expires_at = datetime.now() + timedelta(seconds=expires_in)
            
            token_info = JWTTokenInfo(
                token=access_token,
                expires_at=expires_at,
                issued_at=datetime.now(),
                scopes=auth_config.oauth2_scope
            )
            
            # Store token
            self._credential_store.store_token(server_name, token_info)
            
            self._metrics.record_auth_attempt(True)
            return AuthenticationResult(
                success=True,
                auth_headers={"Authorization": f"Bearer {access_token}"},
                token_info=token_info,
                expires_at=expires_at
            )
        
        except Exception as e:
            logger.error(f"OAuth2 authentication failed for {server_name}: {e}")
            self._metrics.record_auth_attempt(False, "OAUTH2_FAILED")
            return AuthenticationResult(
                success=False,
                error_message=f"OAuth2 authentication failed: {str(e)}",
                error_type="OAUTH2_FAILED"
            )
    
    def _authenticate_custom_headers(self, auth_config: AuthenticationConfig) -> AuthenticationResult:
        """
        Authenticate using custom headers.
        
        Args:
            auth_config: Authentication configuration
            
        Returns:
            AuthenticationResult: Authentication result
        """
        if not auth_config.custom_headers:
            self._metrics.record_auth_attempt(False, "MISSING_CUSTOM_HEADERS")
            return AuthenticationResult(
                success=False,
                error_message="Custom headers are required",
                error_type="MISSING_CUSTOM_HEADERS"
            )
        
        self._metrics.record_auth_attempt(True)
        return AuthenticationResult(
            success=True,
            auth_headers=auth_config.custom_headers.copy()
        )
    
    async def refresh_token_if_needed(
        self,
        server_name: str,
        auth_config: AuthenticationConfig
    ) -> AuthenticationResult:
        """
        Refresh token if it's expired or will expire soon.
        
        Args:
            server_name: Server identifier
            auth_config: Authentication configuration
            
        Returns:
            AuthenticationResult: Refresh result
        """
        # Only applicable for token-based authentication
        if auth_config.auth_type not in [AuthenticationType.JWT, AuthenticationType.OAUTH2]:
            return AuthenticationResult(success=True)
        
        if not auth_config.auto_refresh_enabled:
            return AuthenticationResult(success=True)
        
        # Check if token needs refresh
        existing_token = self._credential_store.get_token(server_name)
        if not existing_token or not existing_token.is_expired(auth_config.refresh_buffer_seconds):
            return AuthenticationResult(success=True)
        
        # Use lock to prevent concurrent refresh attempts
        if server_name not in self._refresh_locks:
            self._refresh_locks[server_name] = asyncio.Lock()
        
        async with self._refresh_locks[server_name]:
            # Check again in case another coroutine already refreshed
            current_token = self._credential_store.get_token(server_name)
            if current_token and not current_token.is_expired(auth_config.refresh_buffer_seconds):
                return AuthenticationResult(success=True)
            
            # Perform refresh
            logger.info(f"Refreshing token for {server_name}")
            refresh_result = await self.authenticate(server_name, auth_config, force_refresh=True)
            
            if refresh_result.success:
                self._metrics.record_token_refresh(True)
                logger.info(f"Token refreshed successfully for {server_name}")
            else:
                self._metrics.record_token_refresh(False, refresh_result.error_type)
                logger.error(f"Token refresh failed for {server_name}: {refresh_result.error_message}")
            
            return refresh_result
    
    def get_authentication_headers(
        self,
        server_name: str,
        auth_config: AuthenticationConfig
    ) -> Dict[str, str]:
        """
        Get current authentication headers for a server.
        
        Args:
            server_name: Server identifier
            auth_config: Authentication configuration
            
        Returns:
            Dict[str, str]: Authentication headers
        """
        if auth_config.auth_type == AuthenticationType.NONE:
            return {}
        
        # For token-based auth, get stored token
        if auth_config.auth_type in [AuthenticationType.JWT, AuthenticationType.OAUTH2]:
            token_info = self._credential_store.get_token(server_name)
            if token_info and not token_info.is_expired():
                return {"Authorization": f"Bearer {token_info.token}"}
        
        # For other auth types, generate headers directly
        auth_result = asyncio.run(self.authenticate(server_name, auth_config))
        return auth_result.auth_headers if auth_result.success else {}
    
    def get_metrics(self) -> AuthenticationMetrics:
        """
        Get authentication metrics.
        
        Returns:
            AuthenticationMetrics: Current authentication metrics
        """
        return self._metrics
    
    def cleanup_expired_tokens(self) -> int:
        """
        Clean up expired tokens from storage.
        
        Returns:
            int: Number of expired tokens removed
        """
        return self._credential_store.cleanup_expired_tokens()
    
    def clear_credentials(self, server_name: Optional[str] = None) -> None:
        """
        Clear stored credentials.
        
        Args:
            server_name: Specific server to clear, or None to clear all
        """
        if server_name:
            self._credential_store.remove_token(server_name)
        else:
            self._credential_store.clear_all()
    
    def list_authenticated_servers(self) -> List[str]:
        """
        List servers with stored authentication tokens.
        
        Returns:
            List[str]: List of server names with stored tokens
        """
        return self._credential_store.list_stored_servers()