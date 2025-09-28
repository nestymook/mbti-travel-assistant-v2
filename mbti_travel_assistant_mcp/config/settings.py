"""
Configuration settings for MBTI Travel Assistant MCP

This module provides configuration management for the BedrockAgentCore runtime,
including MCP client endpoints, authentication settings, and operational parameters.
"""

import os
from typing import Optional, List
from pydantic import Field
from pydantic_settings import BaseSettings


class MCPClientSettings(BaseSettings):
    """MCP Client configuration settings"""
    
    # Restaurant Search MCP Server Configuration
    search_mcp_endpoint: str = Field(
        default="",
        env="SEARCH_MCP_ENDPOINT",
        description="Endpoint URL for restaurant search MCP server"
    )
    
    # Restaurant Reasoning MCP Server Configuration  
    reasoning_mcp_endpoint: str = Field(
        default="",
        env="REASONING_MCP_ENDPOINT", 
        description="Endpoint URL for restaurant reasoning MCP server"
    )
    
    # MCP Connection Settings
    mcp_connection_timeout: int = Field(
        default=30,
        env="MCP_CONNECTION_TIMEOUT",
        description="Timeout for MCP client connections in seconds"
    )
    
    mcp_retry_attempts: int = Field(
        default=3,
        env="MCP_RETRY_ATTEMPTS",
        description="Number of retry attempts for failed MCP calls"
    )


class AuthenticationSettings(BaseSettings):
    """Authentication configuration settings"""
    
    # Cognito Configuration
    cognito_user_pool_id: str = Field(
        default="",
        env="COGNITO_USER_POOL_ID",
        description="AWS Cognito User Pool ID for JWT validation"
    )
    
    cognito_region: str = Field(
        default="us-east-1",
        env="COGNITO_REGION",
        description="AWS region for Cognito User Pool"
    )
    
    # JWT Configuration
    jwt_algorithm: str = Field(
        default="RS256",
        env="JWT_ALGORITHM",
        description="JWT signature algorithm"
    )
    
    jwt_audience: Optional[str] = Field(
        default=None,
        env="JWT_AUDIENCE",
        description="Expected JWT audience"
    )
    
    # Token Settings
    token_cache_ttl: int = Field(
        default=300,
        env="TOKEN_CACHE_TTL",
        description="JWT token cache TTL in seconds"
    )


class CacheSettings(BaseSettings):
    """Caching configuration settings"""
    
    # Cache Configuration
    cache_enabled: bool = Field(
        default=True,
        env="CACHE_ENABLED",
        description="Enable response caching"
    )
    
    cache_ttl: int = Field(
        default=1800,
        env="CACHE_TTL",
        description="Cache TTL in seconds (30 minutes default)"
    )
    
    # Redis Configuration (if using Redis cache)
    redis_url: Optional[str] = Field(
        default=None,
        env="REDIS_URL",
        description="Redis connection URL for distributed caching"
    )


class AgentCoreSettings(BaseSettings):
    """BedrockAgentCore runtime settings"""
    
    # Runtime Configuration
    runtime_port: int = Field(
        default=8080,
        env="RUNTIME_PORT",
        description="Port for AgentCore runtime server"
    )
    
    # Strands Agent Configuration
    agent_model: str = Field(
        default="amazon.nova-pro-v1:0:300k",
        env="AGENT_MODEL",
        description="Foundation model for Strands Agent"
    )
    
    agent_temperature: float = Field(
        default=0.1,
        env="AGENT_TEMPERATURE",
        description="Temperature setting for agent responses"
    )
    
    agent_max_tokens: int = Field(
        default=4096,
        env="AGENT_MAX_TOKENS",
        description="Maximum tokens for agent responses"
    )


class LoggingSettings(BaseSettings):
    """Logging and observability settings"""
    
    # Logging Configuration
    log_level: str = Field(
        default="INFO",
        env="LOG_LEVEL",
        description="Logging level (DEBUG, INFO, WARNING, ERROR)"
    )
    
    log_format: str = Field(
        default="json",
        env="LOG_FORMAT",
        description="Log format (json, text)"
    )
    
    # Observability
    tracing_enabled: bool = Field(
        default=True,
        env="TRACING_ENABLED",
        description="Enable OpenTelemetry tracing"
    )
    
    metrics_enabled: bool = Field(
        default=True,
        env="METRICS_ENABLED",
        description="Enable metrics collection"
    )


class ApplicationSettings(BaseSettings):
    """Main application settings"""
    
    # Application Metadata
    app_name: str = "mbti-travel-assistant-mcp"
    app_version: str = "1.0.0"
    
    # AWS Configuration
    aws_region: str = Field(
        default="us-east-1",
        env="AWS_REGION",
        description="AWS region for services"
    )
    
    # Environment
    environment: str = Field(
        default="development",
        env="ENVIRONMENT",
        description="Application environment (development, staging, production)"
    )
    
    # Component Settings
    mcp_client: MCPClientSettings = MCPClientSettings()
    authentication: AuthenticationSettings = AuthenticationSettings()
    cache: CacheSettings = CacheSettings()
    agentcore: AgentCoreSettings = AgentCoreSettings()
    logging: LoggingSettings = LoggingSettings()
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global settings instance
settings = ApplicationSettings()