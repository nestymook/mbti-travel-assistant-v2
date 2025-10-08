#!/usr/bin/env python3
"""
Enhanced JWT Token Manager for MBTI Travel Planner Agent

This module provides comprehensive JWT token management and injection throughout
the entire agent workflow, ensuring all components have access to valid JWT tokens
for AgentCore authentication.

Key Features:
- Centralized JWT token management
- Automatic token propagation to all components
- Token validation and refresh capabilities
- Thread-safe token updates
- Comprehensive logging and monitoring
"""

import asyncio
import logging
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
import jwt
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class TokenInfo:
    """JWT token information container."""
    token: str
    expires_at: Optional[datetime] = None
    username: Optional[str] = None
    issued_at: Optional[datetime] = None
    refresh_token: Optional[str] = None


class EnhancedJWTTokenManager:
    """Enhanced JWT token manager with comprehensive injection capabilities."""
    
    def __init__(self):
        """Initialize the enhanced JWT token manager."""
        self._current_token: Optional[TokenInfo] = None
        self._token_lock = threading.RLock()
        self._injection_callbacks: List[Callable[[str], None]] = []
        self._component_registry: Dict[str, Any] = {}
        self._token_update_count = 0
        self._last_update_time: Optional[datetime] = None
        
        logger.info("Enhanced JWT Token Manager initialized")
    
    def register_component(self, name: str, component: Any) -> None:
        """Register a component for JWT token injection."""
        with self._token_lock:
            self._component_registry[name] = component
            logger.debug(f"Registered component for JWT injection: {name}")
            
            # If we have a current token, inject it immediately
            if self._current_token:
                self._inject_token_to_component(name, component, self._current_token.token)
    
    def register_injection_callback(self, callback: Callable[[str], None]) -> None:
        """Register a callback function for JWT token updates."""
        with self._token_lock:
            self._injection_callbacks.append(callback)
            logger.debug(f"Registered JWT injection callback: {callback.__name__}")
    
    def set_jwt_token(self, token: str, username: Optional[str] = None, 
                     expires_at: Optional[datetime] = None, 
                     refresh_token: Optional[str] = None) -> bool:
        """
        Set the JWT token and propagate it to all registered components.
        
        Args:
            token: JWT token string
            username: Username associated with the token
            expires_at: Token expiration time
            refresh_token: Refresh token for token renewal
            
        Returns:
            bool: True if token was successfully set and propagated
        """
        try:
            with self._token_lock:
                # Validate token format
                if not self._validate_token_format(token):
                    logger.error("Invalid JWT token format provided")
                    return False
                
                # Extract token information if not provided
                if not expires_at or not username:
                    try:
                        decoded = jwt.decode(token, options={"verify_signature": False})
                        if not username:
                            username = decoded.get('cognito:username', decoded.get('username', 'unknown'))
                        if not expires_at:
                            exp_timestamp = decoded.get('exp')
                            if exp_timestamp:
                                expires_at = datetime.fromtimestamp(exp_timestamp)
                    except Exception as decode_error:
                        logger.warning(f"Could not decode JWT token for metadata: {decode_error}")
                
                # Create token info
                self._current_token = TokenInfo(
                    token=token,
                    expires_at=expires_at,
                    username=username,
                    issued_at=datetime.utcnow(),
                    refresh_token=refresh_token
                )
                
                # Propagate token to all registered components
                success_count = self._propagate_token_to_all_components(token)
                
                # Execute injection callbacks
                callback_success_count = self._execute_injection_callbacks(token)
                
                # Update metrics
                self._token_update_count += 1
                self._last_update_time = datetime.utcnow()
                
                logger.info(f"✅ JWT token set and propagated successfully")
                logger.info(f"👤 Username: {username}")
                logger.info(f"🕒 Expires: {expires_at.strftime('%Y-%m-%d %H:%M:%S UTC') if expires_at else 'Unknown'}")
                logger.info(f"📡 Components updated: {success_count}")
                logger.info(f"🔄 Callbacks executed: {callback_success_count}")
                
                return True
                
        except Exception as e:
            logger.error(f"❌ Failed to set JWT token: {e}")
            return False
    
    def get_current_token(self) -> Optional[str]:
        """Get the current JWT token."""
        with self._token_lock:
            return self._current_token.token if self._current_token else None
    
    def get_token_info(self) -> Optional[TokenInfo]:
        """Get complete token information."""
        with self._token_lock:
            return self._current_token
    
    def is_token_valid(self) -> bool:
        """Check if the current token is valid and not expired."""
        with self._token_lock:
            if not self._current_token:
                return False
            
            # Check expiration
            if self._current_token.expires_at:
                if datetime.utcnow() >= self._current_token.expires_at:
                    logger.warning("JWT token has expired")
                    return False
            
            # Validate format
            return self._validate_token_format(self._current_token.token)
    
    def refresh_token_if_needed(self, refresh_callback: Optional[Callable[[], str]] = None) -> bool:
        """
        Refresh the token if it's close to expiration.
        
        Args:
            refresh_callback: Function to call for token refresh
            
        Returns:
            bool: True if token was refreshed or is still valid
        """
        with self._token_lock:
            if not self._current_token:
                logger.warning("No current token to refresh")
                return False
            
            # Check if token needs refresh (within 5 minutes of expiration)
            if self._current_token.expires_at:
                time_until_expiry = self._current_token.expires_at - datetime.utcnow()
                if time_until_expiry.total_seconds() < 300:  # 5 minutes
                    logger.info("JWT token needs refresh (expires soon)")
                    
                    if refresh_callback:
                        try:
                            new_token = refresh_callback()
                            if new_token:
                                return self.set_jwt_token(new_token, self._current_token.username)
                        except Exception as e:
                            logger.error(f"Token refresh failed: {e}")
                            return False
                    else:
                        logger.warning("Token needs refresh but no refresh callback provided")
                        return False
            
            return True
    
    def clear_token(self) -> None:
        """Clear the current token and notify all components."""
        with self._token_lock:
            if self._current_token:
                logger.info(f"Clearing JWT token for user: {self._current_token.username}")
                self._current_token = None
                
                # Notify components about token clearing
                for name, component in self._component_registry.items():
                    try:
                        self._clear_token_from_component(name, component)
                    except Exception as e:
                        logger.warning(f"Failed to clear token from component {name}: {e}")
    
    def get_injection_status(self) -> Dict[str, Any]:
        """Get comprehensive status of JWT token injection."""
        with self._token_lock:
            return {
                'has_token': self._current_token is not None,
                'token_valid': self.is_token_valid(),
                'username': self._current_token.username if self._current_token else None,
                'expires_at': self._current_token.expires_at.isoformat() if self._current_token and self._current_token.expires_at else None,
                'registered_components': len(self._component_registry),
                'registered_callbacks': len(self._injection_callbacks),
                'update_count': self._token_update_count,
                'last_update': self._last_update_time.isoformat() if self._last_update_time else None,
                'component_names': list(self._component_registry.keys())
            }
    
    def _validate_token_format(self, token: str) -> bool:
        """Validate JWT token format."""
        try:
            parts = token.split('.')
            if len(parts) != 3:
                return False
            
            # Try to decode without verification
            jwt.decode(token, options={"verify_signature": False})
            return True
        except Exception:
            return False
    
    def _propagate_token_to_all_components(self, token: str) -> int:
        """Propagate JWT token to all registered components."""
        success_count = 0
        
        for name, component in self._component_registry.items():
            try:
                if self._inject_token_to_component(name, component, token):
                    success_count += 1
            except Exception as e:
                logger.warning(f"Failed to inject token to component {name}: {e}")
        
        return success_count
    
    def _inject_token_to_component(self, name: str, component: Any, token: str) -> bool:
        """Inject JWT token to a specific component."""
        try:
            # AgentCore Runtime Client
            if hasattr(component, 'jwt_token'):
                component.jwt_token = token
                logger.debug(f"✅ JWT token injected to {name} (direct attribute)")
                return True
            
            # Authentication Manager
            if hasattr(component, 'set_jwt_token'):
                component.set_jwt_token(token)
                logger.debug(f"✅ JWT token injected to {name} (set_jwt_token method)")
                return True
            
            # Tool with runtime_client
            if hasattr(component, 'runtime_client') and hasattr(component.runtime_client, 'jwt_token'):
                component.runtime_client.jwt_token = token
                logger.debug(f"✅ JWT token injected to {name} (runtime_client)")
                return True
            
            # Wrapped tool patterns
            if hasattr(component, '_tool_obj') and hasattr(component._tool_obj, 'runtime_client'):
                if hasattr(component._tool_obj.runtime_client, 'jwt_token'):
                    component._tool_obj.runtime_client.jwt_token = token
                    logger.debug(f"✅ JWT token injected to {name} (_tool_obj pattern)")
                    return True
            
            # Original tool pattern
            if hasattr(component, 'original_tool') and hasattr(component.original_tool, 'runtime_client'):
                if hasattr(component.original_tool.runtime_client, 'jwt_token'):
                    component.original_tool.runtime_client.jwt_token = token
                    logger.debug(f"✅ JWT token injected to {name} (original_tool pattern)")
                    return True
            
            # Agent with tools
            if hasattr(component, 'tools'):
                tools_updated = 0
                for tool in component.tools:
                    if self._inject_token_to_tool(tool, token):
                        tools_updated += 1
                
                if tools_updated > 0:
                    logger.debug(f"✅ JWT token injected to {name} ({tools_updated} tools)")
                    return True
            
            logger.debug(f"⚠️ No JWT injection method found for component {name}")
            return False
            
        except Exception as e:
            logger.warning(f"Failed to inject JWT token to component {name}: {e}")
            return False
    
    def _inject_token_to_tool(self, tool: Any, token: str) -> bool:
        """Inject JWT token to a specific tool."""
        try:
            # Direct runtime_client
            if hasattr(tool, 'runtime_client') and hasattr(tool.runtime_client, 'jwt_token'):
                tool.runtime_client.jwt_token = token
                return True
            
            # Wrapped tool patterns
            if hasattr(tool, '_tool_obj') and hasattr(tool._tool_obj, 'runtime_client'):
                if hasattr(tool._tool_obj.runtime_client, 'jwt_token'):
                    tool._tool_obj.runtime_client.jwt_token = token
                    return True
            
            # Original tool pattern
            if hasattr(tool, 'original_tool') and hasattr(tool.original_tool, 'runtime_client'):
                if hasattr(tool.original_tool.runtime_client, 'jwt_token'):
                    tool.original_tool.runtime_client.jwt_token = token
                    return True
            
            return False
            
        except Exception:
            return False
    
    def _clear_token_from_component(self, name: str, component: Any) -> None:
        """Clear JWT token from a specific component."""
        try:
            if hasattr(component, 'jwt_token'):
                component.jwt_token = None
            elif hasattr(component, 'clear_jwt_token'):
                component.clear_jwt_token()
            elif hasattr(component, 'runtime_client') and hasattr(component.runtime_client, 'jwt_token'):
                component.runtime_client.jwt_token = None
        except Exception as e:
            logger.warning(f"Failed to clear token from component {name}: {e}")
    
    def _execute_injection_callbacks(self, token: str) -> int:
        """Execute all registered injection callbacks."""
        success_count = 0
        
        for callback in self._injection_callbacks:
            try:
                callback(token)
                success_count += 1
                logger.debug(f"✅ JWT injection callback executed: {callback.__name__}")
            except Exception as e:
                logger.warning(f"JWT injection callback failed {callback.__name__}: {e}")
        
        return success_count


# Global instance for use throughout the application
enhanced_jwt_manager = EnhancedJWTTokenManager()


def inject_jwt_token_globally(token: str, username: Optional[str] = None, 
                             expires_at: Optional[datetime] = None) -> bool:
    """
    Global function to inject JWT token throughout the entire application.
    
    Args:
        token: JWT token string
        username: Username associated with the token
        expires_at: Token expiration time
        
    Returns:
        bool: True if token was successfully injected
    """
    return enhanced_jwt_manager.set_jwt_token(token, username, expires_at)


def register_component_for_jwt_injection(name: str, component: Any) -> None:
    """
    Register a component to receive JWT token updates.
    
    Args:
        name: Component name for identification
        component: Component object to receive JWT tokens
    """
    enhanced_jwt_manager.register_component(name, component)


def get_current_jwt_token() -> Optional[str]:
    """Get the current JWT token."""
    return enhanced_jwt_manager.get_current_token()


def get_jwt_injection_status() -> Dict[str, Any]:
    """Get comprehensive JWT injection status."""
    return enhanced_jwt_manager.get_injection_status()