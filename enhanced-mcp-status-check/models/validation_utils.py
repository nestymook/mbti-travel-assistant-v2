"""
Validation utilities for enhanced MCP status check data models.

This module provides comprehensive validation methods for configuration data
and health check results to ensure data integrity and proper system operation.
"""

import re
from typing import List, Dict, Any, Optional, Union
from urllib.parse import urlparse
from .dual_health_models import (
    EnhancedServerConfig,
    AggregationConfig,
    PriorityConfig,
    MCPToolsListRequest,
    MCPToolsListResponse,
    RESTHealthCheckResponse
)


class ValidationError(Exception):
    """Custom exception for validation errors."""
    
    def __init__(self, message: str, field: str = None, errors: List[str] = None):
        self.message = message
        self.field = field
        self.errors = errors or []
        super().__init__(self.message)


class ConfigurationValidator:
    """Validator for enhanced server configurations."""
    
    @staticmethod
    def validate_url(url: str, scheme_required: bool = True) -> List[str]:
        """Validate URL format and accessibility requirements."""
        errors = []
        
        if not url:
            errors.append("URL cannot be empty")
            return errors
        
        try:
            parsed = urlparse(url)
            
            if scheme_required and not parsed.scheme:
                errors.append("URL must include scheme (http/https)")
            
            if not parsed.netloc:
                errors.append("URL must include hostname")
            
            if parsed.scheme and parsed.scheme not in ['http', 'https']:
                errors.append("URL scheme must be http or https")
            
            # Check for common URL issues
            if parsed.hostname and parsed.hostname.startswith('.'):
                errors.append("Invalid hostname format")
            
            if parsed.port and (parsed.port < 1 or parsed.port > 65535):
                errors.append("Port number must be between 1 and 65535")
                
        except Exception as e:
            errors.append(f"Invalid URL format: {str(e)}")
        
        return errors
    
    @staticmethod
    def validate_server_name(server_name: str) -> List[str]:
        """Validate server name format and requirements."""
        errors = []
        
        if not server_name:
            errors.append("Server name cannot be empty")
            return errors
        
        # Check length
        if len(server_name) < 3:
            errors.append("Server name must be at least 3 characters long")
        
        if len(server_name) > 64:
            errors.append("Server name cannot exceed 64 characters")
        
        # Check format (alphanumeric, hyphens, underscores)
        if not re.match(r'^[a-zA-Z0-9_-]+$', server_name):
            errors.append("Server name can only contain letters, numbers, hyphens, and underscores")
        
        # Check that it doesn't start or end with special characters
        if server_name.startswith(('-', '_')) or server_name.endswith(('-', '_')):
            errors.append("Server name cannot start or end with hyphens or underscores")
        
        return errors
    
    @staticmethod
    def validate_timeout_value(timeout: int, min_value: int = 1, max_value: int = 300) -> List[str]:
        """Validate timeout values."""
        errors = []
        
        if timeout < min_value:
            errors.append(f"Timeout must be at least {min_value} seconds")
        
        if timeout > max_value:
            errors.append(f"Timeout cannot exceed {max_value} seconds")
        
        return errors
    
    @staticmethod
    def validate_retry_attempts(retry_attempts: int, max_attempts: int = 10) -> List[str]:
        """Validate retry attempt values."""
        errors = []
        
        if retry_attempts < 0:
            errors.append("Retry attempts cannot be negative")
        
        if retry_attempts > max_attempts:
            errors.append(f"Retry attempts cannot exceed {max_attempts}")
        
        return errors
    
    @staticmethod
    def validate_expected_tools(expected_tools: List[str]) -> List[str]:
        """Validate expected tools list."""
        errors = []
        
        if not isinstance(expected_tools, list):
            errors.append("Expected tools must be a list")
            return errors
        
        for i, tool in enumerate(expected_tools):
            if not isinstance(tool, str):
                errors.append(f"Tool at index {i} must be a string")
                continue
            
            if not tool.strip():
                errors.append(f"Tool at index {i} cannot be empty")
                continue
            
            # Validate tool name format (basic validation)
            if not re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', tool):
                errors.append(f"Tool '{tool}' has invalid format (must start with letter, contain only letters, numbers, underscores)")
        
        # Check for duplicates
        if len(expected_tools) != len(set(expected_tools)):
            errors.append("Expected tools list contains duplicates")
        
        return errors
    
    @staticmethod
    def validate_auth_headers(auth_headers: Dict[str, str]) -> List[str]:
        """Validate authentication headers."""
        errors = []
        
        if not isinstance(auth_headers, dict):
            errors.append("Auth headers must be a dictionary")
            return errors
        
        for key, value in auth_headers.items():
            if not isinstance(key, str) or not isinstance(value, str):
                errors.append(f"Auth header '{key}' must have string key and value")
                continue
            
            # Check for common header format issues
            if not key.strip():
                errors.append("Auth header key cannot be empty")
            
            if not value.strip():
                errors.append(f"Auth header '{key}' value cannot be empty")
            
            # Check for potentially sensitive headers that should be handled carefully
            sensitive_headers = ['authorization', 'x-api-key', 'x-auth-token']
            if key.lower() in sensitive_headers and len(value) < 10:
                errors.append(f"Auth header '{key}' appears to have a very short value, which may be invalid")
        
        return errors
    
    @classmethod
    def validate_enhanced_server_config(cls, config: EnhancedServerConfig) -> List[str]:
        """Comprehensive validation of enhanced server configuration."""
        errors = []
        
        # Validate server name
        errors.extend(cls.validate_server_name(config.server_name))
        
        # Validate MCP configuration if enabled
        if config.mcp_enabled:
            errors.extend(cls.validate_url(config.mcp_endpoint_url))
            errors.extend(cls.validate_timeout_value(config.mcp_timeout_seconds))
            errors.extend(cls.validate_retry_attempts(config.mcp_retry_attempts))
            errors.extend(cls.validate_expected_tools(config.mcp_expected_tools))
        
        # Validate REST configuration if enabled
        if config.rest_enabled:
            errors.extend(cls.validate_url(config.rest_health_endpoint_url))
            errors.extend(cls.validate_timeout_value(config.rest_timeout_seconds))
            errors.extend(cls.validate_retry_attempts(config.rest_retry_attempts))
        
        # Validate authentication configuration
        errors.extend(cls.validate_auth_headers(config.auth_headers))
        
        # Validate JWT token if provided
        if config.jwt_token:
            if len(config.jwt_token) < 20:
                errors.append("JWT token appears to be too short")
            
            # Basic JWT format check (three parts separated by dots)
            jwt_parts = config.jwt_token.split('.')
            if len(jwt_parts) != 3:
                errors.append("JWT token must have three parts separated by dots")
        
        # Use the model's built-in validation
        errors.extend(config.validate())
        
        return errors


class HealthCheckValidator:
    """Validator for health check results and responses."""
    
    @staticmethod
    def validate_mcp_tools_list_request(request: MCPToolsListRequest) -> List[str]:
        """Validate MCP tools/list request format."""
        return request.validate()
    
    @staticmethod
    def validate_mcp_tools_list_response(response: MCPToolsListResponse) -> List[str]:
        """Validate MCP tools/list response format."""
        errors = response.validate()
        
        # Additional validation for tools list content
        if response.is_success():
            tools = response.get_tools()
            for i, tool in enumerate(tools):
                if not isinstance(tool, dict):
                    errors.append(f"Tool at index {i} must be a dictionary")
                    continue
                
                # Check required tool fields
                required_fields = ['name']
                for field in required_fields:
                    if field not in tool:
                        errors.append(f"Tool at index {i} missing required field '{field}'")
                
                # Validate tool name
                if 'name' in tool:
                    tool_name = tool['name']
                    if not isinstance(tool_name, str) or not tool_name.strip():
                        errors.append(f"Tool at index {i} has invalid name")
        
        return errors
    
    @staticmethod
    def validate_rest_health_response(response: RESTHealthCheckResponse) -> List[str]:
        """Validate REST health check response."""
        errors = []
        
        # Validate HTTP status code
        if not (100 <= response.status_code <= 599):
            errors.append(f"Invalid HTTP status code: {response.status_code}")
        
        # Validate headers
        if not isinstance(response.headers, dict):
            errors.append("Response headers must be a dictionary")
        
        # Validate response body if present
        if response.body is not None:
            if not isinstance(response.body, dict):
                errors.append("Response body must be a dictionary or None")
            else:
                # Check for common health check fields
                health_fields = ['status', 'health', 'state', 'healthy']
                has_health_field = any(field in response.body for field in health_fields)
                if not has_health_field:
                    errors.append("Response body should contain at least one health indicator field")
        
        # Validate response time
        if response.response_time_ms < 0:
            errors.append("Response time cannot be negative")
        
        if response.response_time_ms > 300000:  # 5 minutes
            errors.append("Response time seems unusually high (>5 minutes)")
        
        # Validate URL
        if response.url:
            url_errors = ConfigurationValidator.validate_url(response.url)
            errors.extend([f"Response URL: {error}" for error in url_errors])
        
        return errors
    
    @staticmethod
    def validate_health_score(health_score: float) -> List[str]:
        """Validate health score value."""
        errors = []
        
        if not (0.0 <= health_score <= 1.0):
            errors.append(f"Health score must be between 0.0 and 1.0, got {health_score}")
        
        return errors
    
    @staticmethod
    def validate_available_paths(available_paths: List[str]) -> List[str]:
        """Validate available monitoring paths."""
        errors = []
        
        valid_paths = ['mcp', 'rest', 'both', 'none']
        for path in available_paths:
            if path not in valid_paths:
                errors.append(f"Invalid monitoring path: {path}")
        
        # Check for logical inconsistencies
        if 'both' in available_paths and ('mcp' in available_paths or 'rest' in available_paths):
            errors.append("Cannot have 'both' path with individual 'mcp' or 'rest' paths")
        
        if 'none' in available_paths and len(available_paths) > 1:
            errors.append("Cannot have 'none' path with other paths")
        
        return errors


class AggregationValidator:
    """Validator for aggregation configurations and results."""
    
    @staticmethod
    def validate_priority_config(config: PriorityConfig) -> List[str]:
        """Validate priority configuration."""
        return config.validate()
    
    @staticmethod
    def validate_aggregation_config(config: AggregationConfig) -> List[str]:
        """Validate aggregation configuration."""
        return config.validate()
    
    @staticmethod
    def validate_weight_distribution(weights: Dict[str, float]) -> List[str]:
        """Validate weight distribution for aggregation."""
        errors = []
        
        total_weight = sum(weights.values())
        if abs(total_weight - 1.0) > 0.001:
            errors.append(f"Weights must sum to 1.0, got {total_weight}")
        
        for name, weight in weights.items():
            if not (0.0 <= weight <= 1.0):
                errors.append(f"Weight '{name}' must be between 0.0 and 1.0, got {weight}")
        
        return errors


def validate_configuration_data(data: Dict[str, Any]) -> List[str]:
    """
    Comprehensive validation of configuration data dictionary.
    
    Args:
        data: Configuration data dictionary
        
    Returns:
        List of validation error messages
    """
    errors = []
    
    try:
        # Try to create and validate EnhancedServerConfig
        config = EnhancedServerConfig.from_dict(data)
        errors.extend(ConfigurationValidator.validate_enhanced_server_config(config))
    except Exception as e:
        errors.append(f"Failed to parse configuration: {str(e)}")
    
    return errors


def validate_health_check_data(data: Dict[str, Any]) -> List[str]:
    """
    Comprehensive validation of health check result data.
    
    Args:
        data: Health check result data dictionary
        
    Returns:
        List of validation error messages
    """
    errors = []
    
    # Validate common fields
    if 'server_name' in data:
        errors.extend(ConfigurationValidator.validate_server_name(data['server_name']))
    
    if 'health_score' in data:
        errors.extend(HealthCheckValidator.validate_health_score(data['health_score']))
    
    if 'available_paths' in data:
        errors.extend(HealthCheckValidator.validate_available_paths(data['available_paths']))
    
    return errors