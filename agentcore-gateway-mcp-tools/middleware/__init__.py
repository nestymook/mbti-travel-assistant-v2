"""
Middleware package for AgentCore Gateway MCP Tools.

This package contains authentication and request processing middleware.
"""

from .auth_middleware import AuthenticationMiddleware, get_current_user
from .jwt_validator import JWTValidator, UserContext

__all__ = [
    "AuthenticationMiddleware",
    "JWTValidator", 
    "UserContext",
    "get_current_user"
]