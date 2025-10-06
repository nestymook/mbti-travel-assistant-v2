#!/usr/bin/env python3
"""
Test script to demonstrate the enhanced logging and debugging support
for the get_connection_config method.

This script shows the structured logging output for both successful
configuration creation and error scenarios.
"""

import logging
import sys
import os
from unittest.mock import MagicMock, patch

# Add the parent directory to the path to import the config module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from config.agentcore_environment_config import (
    EnvironmentConfig, 
    AgentCoreConfig, 
    CognitoConfig, 
    PerformanceConfig,
    MonitoringConfig
)

def setup_logging():
    """Set up logging to show the structured logging output."""
    # Configure logging to show DEBUG level messages
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s - %(extra)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    
    # Create a custom formatter that shows extra data nicely
    class StructuredFormatter(logging.Formatter):
        def format(self, record):
            # Format the base message
            base_msg = super().format(record)
            
            # Add extra data if present
            if hasattr(record, 'operation'):
                extra_info = []
                for key, value in record.__dict__.items():
                    if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 
                                 'pathname', 'filename', 'module', 'lineno', 'funcName',
                                 'created', 'msecs', 'relativeCreated', 'thread', 
                                 'threadName', 'processName', 'process', 'getMessage',
                                 'exc_info', 'exc_text', 'stack_info']:
                        extra_info.append(f"{key}={value}")
                
                if extra_info:
                    base_msg += f" | EXTRA: {', '.join(extra_info)}"
            
            return base_msg
    
    # Apply the custom formatter
    for handler in logging.getLogger().handlers:
        handler.setFormatter(StructuredFormatter())

def create_test_config():
    """Create a test environment configuration."""
    agentcore_config = AgentCoreConfig(
        restaurant_search_agent_arn="arn:aws:bedrock-agentcore:us-east-1:123456789012:runtime/test-search",
        restaurant_reasoning_agent_arn="arn:aws:bedrock-agentcore:us-east-1:123456789012:runtime/test-reasoning",
        region="us-east-1",
        timeout_seconds=30,
        max_retries=3
    )
    
    cognito_config = CognitoConfig(
        user_pool_id="us-east-1_TestPool",
        client_id="test-client-id",
        client_secret="test-client-secret",
        region="us-east-1"
    )
    
    performance_config = PerformanceConfig(
        max_connections=100,
        max_connections_per_host=10
    )
    
    monitoring_config = MonitoringConfig()
    
    return EnvironmentConfig(
        environment="development",
        agentcore=agentcore_config,
        cognito=cognito_config,
        performance=performance_config,
        monitoring=monitoring_config,
        debug_mode=True
    )

def test_successful_connection_config():
    """Test successful connection config creation with logging."""
    print("\n" + "="*80)
    print("TESTING SUCCESSFUL CONNECTION CONFIG CREATION")
    print("="*80)
    
    config = create_test_config()
    
    # Mock the ConnectionConfig class
    mock_connection_config = MagicMock()
    mock_instance = MagicMock()
    mock_instance.timeout_seconds = 30
    mock_instance.max_connections = 100
    mock_instance.max_connections_per_host = 10
    mock_instance.keepalive_timeout = 30
    mock_instance.enable_cleanup_closed = True
    mock_connection_config.return_value = mock_instance
    
    with patch.dict('sys.modules', {
        'services.agentcore_runtime_client': MagicMock(ConnectionConfig=mock_connection_config)
    }):
        try:
            result = config.get_connection_config()
            print(f"\n✅ SUCCESS: ConnectionConfig created successfully")
            print(f"Result: {result}")
        except Exception as e:
            print(f"\n❌ ERROR: {e}")

def test_validation_error_logging():
    """Test validation error logging."""
    print("\n" + "="*80)
    print("TESTING VALIDATION ERROR LOGGING")
    print("="*80)
    
    # Start with a valid config
    config = create_test_config()
    
    # Modify the config to have invalid values that will be caught in get_connection_config
    # This bypasses the PerformanceConfig validation
    config.agentcore.timeout_seconds = 500  # Invalid: > 300
    config.performance.max_connections = 0  # Invalid: must be positive
    config.performance.max_connections_per_host = 20  # Invalid: exceeds max_connections
    
    # Mock the ConnectionConfig class
    mock_connection_config = MagicMock()
    
    with patch.dict('sys.modules', {
        'services.agentcore_runtime_client': MagicMock(ConnectionConfig=mock_connection_config)
    }):
        try:
            result = config.get_connection_config()
            print(f"\n❌ UNEXPECTED: Should have failed with validation errors")
        except ValueError as e:
            print(f"\n✅ EXPECTED ERROR: Validation failed as expected")
            print(f"Error message: {str(e)[:200]}...")

def test_import_error_logging():
    """Test import error logging."""
    print("\n" + "="*80)
    print("TESTING IMPORT ERROR LOGGING")
    print("="*80)
    
    config = create_test_config()
    
    # Mock import failure
    with patch.dict('sys.modules', {'services.agentcore_runtime_client': None}):
        try:
            result = config.get_connection_config()
            print(f"\n❌ UNEXPECTED: Should have failed with import error")
        except ImportError as e:
            print(f"\n✅ EXPECTED ERROR: Import failed as expected")
            print(f"Error message: {str(e)[:200]}...")

def main():
    """Run all logging tests."""
    print("Connection Config Logging Test Suite")
    print("This demonstrates the enhanced logging and debugging support")
    
    # Set up logging
    setup_logging()
    
    # Run tests
    test_successful_connection_config()
    test_validation_error_logging()
    test_import_error_logging()
    
    print("\n" + "="*80)
    print("LOGGING TEST SUITE COMPLETED")
    print("="*80)
    print("\nKey features demonstrated:")
    print("✅ DEBUG level logging for successful configuration creation")
    print("✅ Structured logging format with extra data")
    print("✅ Configuration values logged for debugging")
    print("✅ ERROR level logging for validation failures")
    print("✅ Comprehensive error context and troubleshooting information")
    print("✅ Import error handling with detailed error messages")

if __name__ == "__main__":
    main()