"""
Configuration settings for AgentCore Gateway MCP Tools.

This module provides centralized configuration management using Pydantic settings
with environment variable support.
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List, Optional
import os


class CognitoSettings(BaseSettings):
    """Cognito authentication settings."""
    
    user_pool_id: str = Field(default="us-east-1_KePRX24Bn", env="COGNITO_USER_POOL_ID")
    client_id: str = Field(default="1ofgeckef3po4i3us4j1m4chvd", env="COGNITO_CLIENT_ID")
    region: str = Field(default="us-east-1", env="COGNITO_REGION")
    discovery_url: str = Field(
        default="https://cognito-idp.us-east-1.amazonaws.com/us-east-1_KePRX24Bn/.well-known/openid-configuration",
        env="COGNITO_DISCOVERY_URL"
    )
    jwks_uri: str = Field(
        default="https://cognito-idp.us-east-1.amazonaws.com/us-east-1_KePRX24Bn/.well-known/jwks.json",
        env="COGNITO_JWKS_URI"
    )
    issuer: str = Field(
        default="https://cognito-idp.us-east-1.amazonaws.com/us-east-1_KePRX24Bn",
        env="COGNITO_ISSUER"
    )
    token_use: str = Field(default="access", env="COGNITO_TOKEN_USE")
    algorithm: str = Field(default="RS256", env="JWT_ALGORITHM")
    audience: str = Field(default="1ofgeckef3po4i3us4j1m4chvd", env="JWT_AUDIENCE")


class MCPServerSettings(BaseSettings):
    """MCP server connection settings."""
    
    search_server_url: str = Field(
        default="http://restaurant-search-mcp:8080",
        env="MCP_SEARCH_SERVER_URL"
    )
    reasoning_server_url: str = Field(
        default="http://restaurant-reasoning-mcp:8080",
        env="MCP_REASONING_SERVER_URL"
    )
    connection_timeout: int = Field(default=30, env="MCP_CONNECTION_TIMEOUT")
    request_timeout: int = Field(default=60, env="MCP_REQUEST_TIMEOUT")
    max_retries: int = Field(default=3, env="MCP_MAX_RETRIES")
    retry_delay: float = Field(default=1.0, env="MCP_RETRY_DELAY")


class ApplicationSettings(BaseSettings):
    """Main application settings."""
    
    # Server configuration
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8080, env="PORT")
    debug: bool = Field(default=False, env="DEBUG")
    reload: bool = Field(default=False, env="RELOAD")
    
    # Logging configuration
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    # AWS configuration
    aws_region: str = Field(default="us-east-1", env="AWS_REGION")
    aws_default_region: str = Field(default="us-east-1", env="AWS_DEFAULT_REGION")
    
    # Observability configuration
    enable_metrics: bool = Field(default=True, env="ENABLE_METRICS")
    enable_tracing: bool = Field(default=True, env="ENABLE_TRACING")
    otel_service_name: str = Field(
        default="agentcore-gateway-mcp-tools",
        env="OTEL_SERVICE_NAME"
    )
    
    # Security configuration
    bypass_paths: List[str] = Field(
        default=["/health", "/metrics", "/docs", "/redoc", "/openapi.json", "/"],
        env="BYPASS_PATHS"
    )
    
    # CORS configuration
    cors_origins: List[str] = Field(default=["*"], env="CORS_ORIGINS")
    cors_allow_credentials: bool = Field(default=True, env="CORS_ALLOW_CREDENTIALS")
    cors_allow_methods: List[str] = Field(default=["*"], env="CORS_ALLOW_METHODS")
    cors_allow_headers: List[str] = Field(default=["*"], env="CORS_ALLOW_HEADERS")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


class Settings(BaseSettings):
    """Combined application settings."""
    
    app: ApplicationSettings = ApplicationSettings()
    cognito: CognitoSettings = CognitoSettings()
    mcp: MCPServerSettings = MCPServerSettings()
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get the global settings instance."""
    return settings


def load_cognito_config() -> dict:
    """Load Cognito configuration from JSON file or environment variables."""
    config_file = "cognito_config.json"
    
    if os.path.exists(config_file):
        import json
        with open(config_file, 'r') as f:
            config = json.load(f)
        return config
    
    # Fallback to environment variables
    return {
        "user_pool_id": settings.cognito.user_pool_id,
        "client_id": settings.cognito.client_id,
        "region": settings.cognito.region,
        "discovery_url": settings.cognito.discovery_url,
        "jwks_uri": settings.cognito.jwks_uri,
        "issuer": settings.cognito.issuer,
        "token_use": settings.cognito.token_use,
        "bypass_paths": settings.app.bypass_paths
    }