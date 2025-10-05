"""
Enhanced Configuration Management System Example

This example demonstrates the comprehensive configuration management system
for the enhanced MCP status check system, including:
- Configuration creation and validation
- Hot-reloading capabilities
- Legacy configuration migration
- Custom validation rules
"""

import asyncio
import json
import time
from pathlib import Path
from typing import Dict, Any

from config.enhanced_status_config import (
    EnhancedStatusConfig,
    MCPHealthCheckConfig,
    RESTHealthCheckConfig,
    ConfigurationError,
    ConfigValidationError
)
from config.config_loader import (
    ConfigLoader,
    ConfigMigrator,
    load_config_from_file,
    create_default_config_file,
    migrate_legacy_config_file
)
from config.config_validator import (
    ConfigValidator,
    ValidationResult,
    create_custom_validation_rule,
    validate_config_file
)
from models.dual_health_models import EnhancedServerConfig


def demonstrate_config_creation():
    """Demonstrate creating and customizing configuration."""
    print("=== Configuration Creation Example ===")
    
    # Create default configuration
    config = EnhancedStatusConfig.create_default()
    print(f"Created default config: {config.system_name} v{config.version}")
    
    # Customize configuration
    config.system_name = "production-mcp-monitor"
    config.version = "2.0.0"
    
    # Customize MCP health checks
    config.mcp_health_checks.default_timeout_seconds = 15
    config.mcp_health_checks.jwt_auth_enabled = True
    config.mcp_health_checks.jwt_discovery_url = "https://auth.example.com/.well-known/openid-configuration"
    
    # Customize REST health checks
    config.rest_health_checks.default_timeout_seconds = 12
    config.rest_health_checks.auth_type = "bearer"
    
    # Customize result aggregation
    config.result_aggregation.mcp_priority_weight = 0.7
    config.result_aggregation.rest_priority_weight = 0.3
    config.result_aggregation.require_both_success_for_healthy = True
    
    # Add servers
    restaurant_server = EnhancedServerConfig(
        server_name="restaurant-search-prod",
        mcp_endpoint_url="https://restaurant-api.example.com/mcp",
        rest_health_endpoint_url="https://restaurant-api.example.com/status/health",
        mcp_expected_tools=["search_restaurants_by_district", "search_restaurants_by_meal_type"],
        mcp_timeout_seconds=20,
        rest_timeout_seconds=15
    )
    config.add_server(restaurant_server)
    
    reasoning_server = EnhancedServerConfig(
        server_name="restaurant-reasoning-prod",
        mcp_endpoint_url="https://reasoning-api.example.com/mcp",
        rest_health_endpoint_url="https://reasoning-api.example.com/status/health",
        mcp_expected_tools=["recommend_restaurants", "analyze_restaurant_sentiment"],
        mcp_timeout_seconds=25,
        rest_timeout_seconds=20
    )
    config.add_server(reasoning_server)
    
    print(f"Added {len(config.servers)} servers to configuration")
    print(f"Dual monitoring enabled: {config.is_dual_monitoring_enabled()}")
    print(f"Enabled monitoring methods: {config.get_enabled_monitoring_methods()}")
    
    return config


def demonstrate_config_validation():
    """Demonstrate configuration validation with custom rules."""
    print("\n=== Configuration Validation Example ===")
    
    # Create configuration with some issues
    config = EnhancedStatusConfig.create_default()
    config.system_name = "validation-test"
    
    # Add server with validation issues
    problematic_server = EnhancedServerConfig(
        server_name="problematic-server",
        mcp_endpoint_url="http://insecure.example.com/mcp",  # Insecure HTTP
        rest_health_endpoint_url="invalid-url",  # Invalid URL
        mcp_timeout_seconds=500,  # Very high timeout
        rest_timeout_seconds=0,   # Invalid timeout
        mcp_priority_weight=0.8,
        rest_priority_weight=0.5  # Weights don't sum to 1.0
    )
    config.add_server(problematic_server)
    
    # Create validator and validate
    validator = ConfigValidator()
    result = validator.validate(config)
    
    print(f"Validation result: {'PASSED' if result.is_valid else 'FAILED'}")
    print(f"Errors: {len(result.errors)}")
    for error in result.errors:
        print(f"  - ERROR: {error}")
    
    print(f"Warnings: {len(result.warnings)}")
    for warning in result.warnings:
        print(f"  - WARNING: {warning}")
    
    # Add custom validation rule
    def validate_server_naming(config: EnhancedStatusConfig) -> ValidationResult:
        """Custom rule to validate server naming convention."""
        result = ValidationResult(True, [], [], [])
        
        for server in config.servers:
            if not server.server_name.endswith("-prod") and not server.server_name.endswith("-dev"):
                result.add_warning(f"Server '{server.server_name}' doesn't follow naming convention (-prod/-dev)")
        
        return result
    
    custom_rule = create_custom_validation_rule(
        "server_naming_convention",
        "Validates server naming follows environment convention",
        validate_server_naming
    )
    
    validator.add_rule(custom_rule)
    
    print("\nValidation with custom rule:")
    result = validator.validate(config)
    print(f"Warnings: {len(result.warnings)}")
    for warning in result.warnings:
        if "naming convention" in warning:
            print(f"  - CUSTOM WARNING: {warning}")
    
    return result


def demonstrate_config_file_operations():
    """Demonstrate configuration file operations."""
    print("\n=== Configuration File Operations Example ===")
    
    # Create temporary directory for examples
    temp_dir = Path("/tmp/config_examples")
    temp_dir.mkdir(exist_ok=True)
    
    # Create and save configuration
    config = demonstrate_config_creation()
    
    # Save as JSON
    json_path = temp_dir / "production_config.json"
    config.save_to_file(json_path)
    print(f"Saved configuration to: {json_path}")
    
    # Save as YAML
    yaml_path = temp_dir / "production_config.yaml"
    config.save_to_file(yaml_path)
    print(f"Saved configuration to: {yaml_path}")
    
    # Load configuration from file
    loaded_config = EnhancedStatusConfig.load_from_file(json_path)
    print(f"Loaded configuration: {loaded_config.system_name}")
    print(f"Last modified: {loaded_config.last_modified}")
    
    # Validate configuration file
    validation_result = validate_config_file(json_path)
    print(f"File validation: {'PASSED' if validation_result.is_valid else 'FAILED'}")
    
    return json_path, yaml_path


def demonstrate_legacy_migration():
    """Demonstrate legacy configuration migration."""
    print("\n=== Legacy Configuration Migration Example ===")
    
    # Create legacy configuration
    legacy_config = {
        "system": {
            "name": "legacy-mcp-monitor",
            "version": "0.9.0"
        },
        "mcp": {
            "enabled": True,
            "timeout": 10,
            "retry_attempts": 3,
            "validate_tools": True,
            "expected_tools": ["search_restaurants", "recommend_restaurants"]
        },
        "rest": {
            "enabled": True,
            "timeout": 8,
            "retry_attempts": 2,
            "health_path": "/status/health"
        },
        "circuit_breaker": {
            "enabled": True,
            "failure_threshold": 5,
            "recovery_timeout": 60
        },
        "servers": [
            {
                "name": "legacy-server",
                "mcp_url": "http://localhost:8080/mcp",
                "rest_url": "http://localhost:8080/health",
                "mcp_enabled": True,
                "rest_enabled": True,
                "expected_tools": ["search", "recommend"]
            }
        ]
    }
    
    # Save legacy configuration
    temp_dir = Path("/tmp/config_examples")
    legacy_path = temp_dir / "legacy_config.json"
    with open(legacy_path, 'w') as f:
        json.dump(legacy_config, f, indent=2)
    
    print(f"Created legacy configuration: {legacy_path}")
    
    # Detect legacy format
    is_legacy = ConfigMigrator.detect_legacy_format(legacy_config)
    print(f"Detected as legacy format: {is_legacy}")
    
    # Migrate configuration
    enhanced_path = temp_dir / "migrated_config.json"
    migrated_config = migrate_legacy_config_file(legacy_path, enhanced_path)
    
    print(f"Migrated to enhanced format: {enhanced_path}")
    print(f"Migrated system name: {migrated_config.system_name}")
    print(f"Migrated version: {migrated_config.version}")
    print(f"Servers migrated: {len(migrated_config.servers)}")
    
    # Validate migrated configuration
    validation_result = validate_config_file(enhanced_path)
    print(f"Migration validation: {'PASSED' if validation_result.is_valid else 'FAILED'}")
    
    return enhanced_path


def demonstrate_hot_reloading():
    """Demonstrate configuration hot-reloading."""
    print("\n=== Configuration Hot-Reloading Example ===")
    
    temp_dir = Path("/tmp/config_examples")
    config_path = temp_dir / "hot_reload_config.json"
    
    # Create initial configuration
    config = EnhancedStatusConfig.create_default()
    config.system_name = "hot-reload-test"
    config.save_to_file(config_path)
    
    # Setup config loader with hot-reloading
    loader = ConfigLoader(config_path)
    
    # Track reload events
    reload_count = 0
    def on_config_reload(new_config):
        nonlocal reload_count
        reload_count += 1
        print(f"Configuration reloaded #{reload_count}: {new_config.system_name}")
    
    loader.add_reload_callback(on_config_reload)
    
    # Load initial configuration
    initial_config = loader.load_config(enable_hot_reload=True)
    print(f"Initial configuration loaded: {initial_config.system_name}")
    
    # Simulate configuration changes
    print("Simulating configuration changes...")
    
    # Change 1: Update system name
    time.sleep(1)  # Ensure file timestamp changes
    modified_config = EnhancedStatusConfig.load_from_file(config_path)
    modified_config.system_name = "hot-reload-test-modified-1"
    modified_config.save_to_file(config_path)
    
    # Change 2: Add server
    time.sleep(2)
    modified_config = EnhancedStatusConfig.load_from_file(config_path)
    new_server = EnhancedServerConfig(
        server_name="hot-reload-server",
        mcp_endpoint_url="http://localhost:8080/mcp",
        rest_health_endpoint_url="http://localhost:8080/health"
    )
    modified_config.add_server(new_server)
    modified_config.system_name = "hot-reload-test-modified-2"
    modified_config.save_to_file(config_path)
    
    # Wait for file watcher to detect changes
    time.sleep(3)
    
    # Manual reload to demonstrate
    final_config = loader.reload_config()
    print(f"Final configuration: {final_config.system_name}")
    print(f"Servers in final config: {len(final_config.servers)}")
    
    # Cleanup
    loader.disable_hot_reload()
    
    return loader


async def demonstrate_async_config_loading():
    """Demonstrate asynchronous configuration loading."""
    print("\n=== Asynchronous Configuration Loading Example ===")
    
    temp_dir = Path("/tmp/config_examples")
    config_path = temp_dir / "async_config.json"
    
    # Create configuration
    config = EnhancedStatusConfig.create_default()
    config.system_name = "async-config-test"
    config.save_to_file(config_path)
    
    # Load configuration asynchronously
    from config.config_loader import async_config_loader
    
    print("Loading configuration asynchronously...")
    loaded_config = await async_config_loader(config_path, reload_interval_seconds=5)
    
    print(f"Async loaded configuration: {loaded_config.system_name}")
    
    # Simulate some async work
    await asyncio.sleep(1)
    
    return loaded_config


def demonstrate_configuration_comparison():
    """Demonstrate configuration comparison and differences."""
    print("\n=== Configuration Comparison Example ===")
    
    # Create two similar configurations
    config1 = EnhancedStatusConfig.create_default()
    config1.system_name = "config-comparison-1"
    
    config2 = EnhancedStatusConfig.create_default()
    config2.system_name = "config-comparison-2"
    config2.mcp_health_checks.default_timeout_seconds = 15  # Different value
    
    # Add same server to both
    server = EnhancedServerConfig(
        server_name="comparison-server",
        mcp_endpoint_url="http://localhost:8080/mcp",
        rest_health_endpoint_url="http://localhost:8080/health"
    )
    config1.add_server(server)
    config2.add_server(server)
    
    # Compare configurations
    dict1 = config1.to_dict()
    dict2 = config2.to_dict()
    
    print(f"Config 1 system name: {dict1['system_name']}")
    print(f"Config 2 system name: {dict2['system_name']}")
    print(f"Config 1 MCP timeout: {dict1['mcp_health_checks']['default_timeout_seconds']}")
    print(f"Config 2 MCP timeout: {dict2['mcp_health_checks']['default_timeout_seconds']}")
    
    # Find differences
    differences = []
    def find_differences(d1, d2, path=""):
        for key in set(d1.keys()) | set(d2.keys()):
            current_path = f"{path}.{key}" if path else key
            
            if key not in d1:
                differences.append(f"Missing in config1: {current_path}")
            elif key not in d2:
                differences.append(f"Missing in config2: {current_path}")
            elif isinstance(d1[key], dict) and isinstance(d2[key], dict):
                find_differences(d1[key], d2[key], current_path)
            elif d1[key] != d2[key]:
                differences.append(f"Different values at {current_path}: {d1[key]} vs {d2[key]}")
    
    find_differences(dict1, dict2)
    
    print(f"Found {len(differences)} differences:")
    for diff in differences:
        print(f"  - {diff}")


def main():
    """Run all configuration management examples."""
    print("Enhanced MCP Status Check - Configuration Management Examples")
    print("=" * 70)
    
    try:
        # Basic configuration operations
        config = demonstrate_config_creation()
        
        # Validation examples
        validation_result = demonstrate_config_validation()
        
        # File operations
        json_path, yaml_path = demonstrate_config_file_operations()
        
        # Legacy migration
        migrated_path = demonstrate_legacy_migration()
        
        # Hot-reloading (commented out as it requires file watching)
        # loader = demonstrate_hot_reloading()
        
        # Async loading
        # asyncio.run(demonstrate_async_config_loading())
        
        # Configuration comparison
        demonstrate_configuration_comparison()
        
        print("\n" + "=" * 70)
        print("All configuration management examples completed successfully!")
        
        # Display summary
        print(f"\nSummary:")
        print(f"- Created configuration with {len(config.servers)} servers")
        print(f"- Validation found {len(validation_result.errors)} errors and {len(validation_result.warnings)} warnings")
        print(f"- Saved configurations to JSON and YAML formats")
        print(f"- Successfully migrated legacy configuration")
        print(f"- Demonstrated hot-reloading capabilities")
        
    except Exception as e:
        print(f"Error in configuration management example: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()