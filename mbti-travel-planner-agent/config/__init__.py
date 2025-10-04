"""
Configuration Management Package

This package provides comprehensive configuration management for the MBTI Travel Planner Agent,
including environment detection, validation, and gateway endpoint configuration.
"""

from .environment_loader import (
    GatewayEnvironmentConfig,
    EnvironmentConfigLoader,
    get_config_loader,
    load_environment_config,
    validate_current_environment
)

from .gateway_config import (
    EnvironmentConfig,
    GatewayConfigManager,
    get_config_manager,
    get_gateway_config,
    create_environment_file
)

# Export main classes and functions
__all__ = [
    # Environment loader
    'GatewayEnvironmentConfig',
    'EnvironmentConfigLoader',
    'get_config_loader',
    'load_environment_config',
    'validate_current_environment',
    
    # Gateway config (legacy support)
    'EnvironmentConfig',
    'GatewayConfigManager',
    'get_config_manager',
    'get_gateway_config',
    'create_environment_file'
]

# Version information
__version__ = '1.0.0'
__author__ = 'MBTI Travel Planner Team'
__description__ = 'Configuration management for MBTI Travel Planner Agent'