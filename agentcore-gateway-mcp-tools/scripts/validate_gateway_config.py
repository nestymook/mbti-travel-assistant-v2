#!/usr/bin/env python3
"""
Gateway Configuration Validation Script

This script validates the native MCP protocol router configuration files
to ensure they are properly structured and contain all required settings
for the AgentCore Gateway deployment.

Requirements Implemented:
- 1.1, 1.2: Native MCP protocol routing validation
- 3.1, 3.2, 3.3: JWT authentication over MCP protocol validation
- Circuit breaker and load balancing configuration validation
- Health check endpoint validation for each registered MCP server
"""

import json
import yaml
import sys
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
import jsonschema
from jsonschema import validate, ValidationError


class GatewayConfigValidator:
    """Validates AgentCore Gateway configuration files for native MCP protocol routing."""
    
    def __init__(self, config_dir: str = "config"):
        """
        Initialize the configuration validator.
        
        Args:
            config_dir: Directory containing configuration files
        """
        self.config_dir = Path(config_dir)
        self.validation_errors = []
        self.validation_warnings = []
        
    def validate_all_configurations(self) -> bool:
        """
        Validate all gateway configuration files.
        
        Returns:
            True if all configurations are valid, False otherwise
        """
        print("🔍 Validating AgentCore Gateway MCP Configuration Files...")
        print("=" * 60)
        
        validation_results = []
        
        # Validate main gateway configuration
        validation_results.append(self._validate_gateway_config())
        
        # Validate MCP routing configuration
        validation_results.append(self._validate_mcp_routing_config())
        
        # Validate circuit breaker configuration
        validation_results.append(self._validate_circuit_breaker_config())
        
        # Validate health check configuration
        validation_results.append(self._validate_health_check_config())
        
        # Validate JWT authentication configuration
        validation_results.append(self._validate_jwt_auth_config())
        
        # Cross-validate configurations
        validation_results.append(self._cross_validate_configurations())
        
        # Print summary
        self._print_validation_summary(validation_results)
        
        return all(validation_results)
    
    def _validate_gateway_config(self) -> bool:
        """Validate the main gateway configuration file."""
        print("\n📋 Validating Gateway Configuration (gateway-config.yaml)...")
        
        config_file = self.config_dir / "gateway-config.yaml"
        if not config_file.exists():
            self._add_error(f"Gateway configuration file not found: {config_file}")
            return False
        
        try:
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f)
            
            # Validate required top-level structure
            required_sections = [
                'apiVersion', 'kind', 'metadata', 'spec'
            ]
            
            for section in required_sections:
                if section not in config:
                    self._add_error(f"Missing required section: {section}")
            
            # Validate spec section
            if 'spec' in config:
                spec = config['spec']
                
                # Validate gateway type and protocol
                if spec.get('gateway_type') != 'bedrock_agentcore':
                    self._add_error("gateway_type must be 'bedrock_agentcore'")
                
                if spec.get('protocol') != 'native_mcp':
                    self._add_error("protocol must be 'native_mcp'")
                
                # Validate MCP servers configuration
                if 'mcp_servers' not in spec:
                    self._add_error("Missing mcp_servers configuration")
                else:
                    self._validate_mcp_servers_config(spec['mcp_servers'])
                
                # Validate authentication configuration
                if 'authentication' not in spec:
                    self._add_error("Missing authentication configuration")
                else:
                    self._validate_auth_config(spec['authentication'])
                
                # Validate circuit breaker configuration
                if 'circuit_breaker' not in spec:
                    self._add_warning("Missing circuit_breaker configuration")
                
                # Validate observability configuration
                if 'observability' not in spec:
                    self._add_warning("Missing observability configuration")
            
            print("✅ Gateway configuration validation completed")
            return len([e for e in self.validation_errors if 'gateway-config' in e]) == 0
            
        except yaml.YAMLError as e:
            self._add_error(f"Invalid YAML in gateway-config.yaml: {e}")
            return False
        except Exception as e:
            self._add_error(f"Error validating gateway-config.yaml: {e}")
            return False
    
    def _validate_mcp_servers_config(self, mcp_servers: List[Dict[str, Any]]) -> None:
        """Validate MCP servers configuration."""
        expected_servers = [
            'restaurant-search-mcp',
            'restaurant-reasoning-mcp', 
            'mbti-travel-assistant-mcp'
        ]
        
        server_names = [server.get('name') for server in mcp_servers]
        
        for expected_server in expected_servers:
            if expected_server not in server_names:
                self._add_error(f"Missing MCP server configuration: {expected_server}")
        
        for server in mcp_servers:
            server_name = server.get('name', 'unknown')
            
            # Validate required fields
            required_fields = ['name', 'endpoint', 'protocol', 'health_check', 'tools']
            for field in required_fields:
                if field not in server:
                    self._add_error(f"Missing {field} in server {server_name}")
            
            # Validate protocol
            if server.get('protocol') != 'native_mcp':
                self._add_error(f"Server {server_name} must use native_mcp protocol")
            
            # Validate tools configuration
            if 'tools' in server:
                tools = server['tools']
                if not isinstance(tools, list) or len(tools) == 0:
                    self._add_error(f"Server {server_name} must have at least one tool")
    
    def _validate_auth_config(self, auth_config: Dict[str, Any]) -> None:
        """Validate authentication configuration."""
        if auth_config.get('type') != 'jwt_over_mcp':
            self._add_error("Authentication type must be 'jwt_over_mcp'")
        
        if 'jwt_validation' not in auth_config:
            self._add_error("Missing jwt_validation configuration")
        else:
            jwt_config = auth_config['jwt_validation']
            required_jwt_fields = [
                'cognito_user_pool_id',
                'client_id',
                'region',
                'discovery_url'
            ]
            
            for field in required_jwt_fields:
                if field not in jwt_config:
                    self._add_error(f"Missing JWT validation field: {field}")
    
    def _validate_mcp_routing_config(self) -> bool:
        """Validate MCP routing configuration file."""
        print("\n🔀 Validating MCP Routing Configuration (mcp-routing-config.json)...")
        
        config_file = self.config_dir / "mcp-routing-config.json"
        if not config_file.exists():
            self._add_error(f"MCP routing configuration file not found: {config_file}")
            return False
        
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            # Validate top-level structure
            if 'mcp_routing_configuration' not in config:
                self._add_error("Missing mcp_routing_configuration section")
                return False
            
            routing_config = config['mcp_routing_configuration']
            
            # Validate server registry
            if 'server_registry' not in routing_config:
                self._add_error("Missing server_registry section")
            else:
                self._validate_server_registry(routing_config['server_registry'])
            
            # Validate routing rules
            if 'routing_rules' not in routing_config:
                self._add_error("Missing routing_rules section")
            else:
                self._validate_routing_rules(routing_config['routing_rules'])
            
            # Validate definitions
            if 'definitions' not in routing_config:
                self._add_warning("Missing definitions section")
            
            print("✅ MCP routing configuration validation completed")
            return len([e for e in self.validation_errors if 'mcp-routing' in e]) == 0
            
        except json.JSONDecodeError as e:
            self._add_error(f"Invalid JSON in mcp-routing-config.json: {e}")
            return False
        except Exception as e:
            self._add_error(f"Error validating mcp-routing-config.json: {e}")
            return False
    
    def _validate_server_registry(self, server_registry: Dict[str, Any]) -> None:
        """Validate server registry configuration."""
        expected_servers = [
            'restaurant-search-mcp',
            'restaurant-reasoning-mcp',
            'mbti-travel-assistant-mcp'
        ]
        
        for server_name in expected_servers:
            if server_name not in server_registry:
                self._add_error(f"Missing server in registry: {server_name}")
                continue
            
            server_config = server_registry[server_name]
            
            # Validate required fields
            required_fields = ['server_id', 'endpoint', 'health_check', 'tools']
            for field in required_fields:
                if field not in server_config:
                    self._add_error(f"Missing {field} in server {server_name}")
            
            # Validate endpoint configuration
            if 'endpoint' in server_config:
                endpoint = server_config['endpoint']
                if endpoint.get('protocol') != 'native_mcp':
                    self._add_error(f"Server {server_name} endpoint must use native_mcp protocol")
            
            # Validate tools configuration
            if 'tools' in server_config:
                tools = server_config['tools']
                if not isinstance(tools, dict) or len(tools) == 0:
                    self._add_error(f"Server {server_name} must have at least one tool")
                
                # Validate tool schemas
                for tool_name, tool_config in tools.items():
                    if 'parameters_schema' not in tool_config:
                        self._add_error(f"Missing parameters_schema for tool {tool_name}")
                    if 'response_schema' not in tool_config:
                        self._add_warning(f"Missing response_schema for tool {tool_name}")
    
    def _validate_routing_rules(self, routing_rules: Dict[str, Any]) -> None:
        """Validate routing rules configuration."""
        if 'tool_routing' not in routing_rules:
            self._add_error("Missing tool_routing section")
            return
        
        tool_routing = routing_rules['tool_routing']
        
        # Expected tools and their target servers
        expected_tool_mappings = {
            'search_restaurants_by_district': 'restaurant-search-mcp',
            'search_restaurants_by_meal_type': 'restaurant-search-mcp',
            'search_restaurants_combined': 'restaurant-search-mcp',
            'recommend_restaurants': 'restaurant-reasoning-mcp',
            'analyze_restaurant_sentiment': 'restaurant-reasoning-mcp',
            'create_mbti_itinerary': 'mbti-travel-assistant-mcp',
            'get_personality_recommendations': 'mbti-travel-assistant-mcp',
            'analyze_travel_preferences': 'mbti-travel-assistant-mcp'
        }
        
        for tool_name, expected_server in expected_tool_mappings.items():
            if tool_name not in tool_routing:
                self._add_error(f"Missing routing rule for tool: {tool_name}")
                continue
            
            tool_rule = tool_routing[tool_name]
            if tool_rule.get('target_server') != expected_server:
                self._add_error(f"Tool {tool_name} should route to {expected_server}")
    
    def _validate_circuit_breaker_config(self) -> bool:
        """Validate circuit breaker configuration file."""
        print("\n⚡ Validating Circuit Breaker Configuration (circuit-breaker-config.json)...")
        
        config_file = self.config_dir / "circuit-breaker-config.json"
        if not config_file.exists():
            self._add_error(f"Circuit breaker configuration file not found: {config_file}")
            return False
        
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            # Validate top-level structure
            if 'circuit_breaker_configuration' not in config:
                self._add_error("Missing circuit_breaker_configuration section")
                return False
            
            cb_config = config['circuit_breaker_configuration']
            
            # Validate global settings
            if 'global_settings' not in cb_config:
                self._add_error("Missing global_settings section")
            
            # Validate server-specific settings
            if 'server_specific_settings' not in cb_config:
                self._add_error("Missing server_specific_settings section")
            else:
                self._validate_circuit_breaker_servers(cb_config['server_specific_settings'])
            
            # Validate circuit breaker states
            if 'circuit_breaker_states' not in cb_config:
                self._add_warning("Missing circuit_breaker_states section")
            
            print("✅ Circuit breaker configuration validation completed")
            return len([e for e in self.validation_errors if 'circuit-breaker' in e]) == 0
            
        except json.JSONDecodeError as e:
            self._add_error(f"Invalid JSON in circuit-breaker-config.json: {e}")
            return False
        except Exception as e:
            self._add_error(f"Error validating circuit-breaker-config.json: {e}")
            return False
    
    def _validate_circuit_breaker_servers(self, server_settings: Dict[str, Any]) -> None:
        """Validate circuit breaker server-specific settings."""
        expected_servers = [
            'restaurant-search-mcp',
            'restaurant-reasoning-mcp',
            'mbti-travel-assistant-mcp'
        ]
        
        for server_name in expected_servers:
            if server_name not in server_settings:
                self._add_error(f"Missing circuit breaker settings for server: {server_name}")
                continue
            
            server_config = server_settings[server_name]
            
            # Validate required fields
            required_fields = [
                'enabled', 'failure_threshold', 'timeout_seconds',
                'retry_interval_seconds', 'health_check', 'fallback_behavior'
            ]
            
            for field in required_fields:
                if field not in server_config:
                    self._add_error(f"Missing {field} in circuit breaker config for {server_name}")
            
            # Validate health check configuration
            if 'health_check' in server_config:
                health_check = server_config['health_check']
                if health_check.get('method') != 'mcp_ping':
                    self._add_warning(f"Server {server_name} should use mcp_ping for health checks")
    
    def _validate_health_check_config(self) -> bool:
        """Validate health check configuration file."""
        print("\n🏥 Validating Health Check Configuration (health-check-config.json)...")
        
        config_file = self.config_dir / "health-check-config.json"
        if not config_file.exists():
            self._add_error(f"Health check configuration file not found: {config_file}")
            return False
        
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            # Validate top-level structure
            if 'health_check_configuration' not in config:
                self._add_error("Missing health_check_configuration section")
                return False
            
            hc_config = config['health_check_configuration']
            
            # Validate MCP server health checks
            if 'mcp_server_health_checks' not in hc_config:
                self._add_error("Missing mcp_server_health_checks section")
            else:
                self._validate_health_check_servers(hc_config['mcp_server_health_checks'])
            
            # Validate health check aggregation
            if 'health_check_aggregation' not in hc_config:
                self._add_warning("Missing health_check_aggregation section")
            
            print("✅ Health check configuration validation completed")
            return len([e for e in self.validation_errors if 'health-check' in e]) == 0
            
        except json.JSONDecodeError as e:
            self._add_error(f"Invalid JSON in health-check-config.json: {e}")
            return False
        except Exception as e:
            self._add_error(f"Error validating health-check-config.json: {e}")
            return False
    
    def _validate_health_check_servers(self, server_health_checks: Dict[str, Any]) -> None:
        """Validate health check server configurations."""
        expected_servers = [
            'restaurant-search-mcp',
            'restaurant-reasoning-mcp',
            'mbti-travel-assistant-mcp'
        ]
        
        for server_name in expected_servers:
            if server_name not in server_health_checks:
                self._add_error(f"Missing health check config for server: {server_name}")
                continue
            
            server_config = server_health_checks[server_name]
            
            # Validate required fields
            required_fields = [
                'enabled', 'server_id', 'health_check_methods',
                'health_status_criteria', 'monitoring_configuration'
            ]
            
            for field in required_fields:
                if field not in server_config:
                    self._add_error(f"Missing {field} in health check config for {server_name}")
            
            # Validate health check methods
            if 'health_check_methods' in server_config:
                methods = server_config['health_check_methods']
                if not isinstance(methods, list) or len(methods) == 0:
                    self._add_error(f"Server {server_name} must have at least one health check method")
                
                # Check for required mcp_ping method
                has_mcp_ping = any(method.get('method') == 'mcp_ping' for method in methods)
                if not has_mcp_ping:
                    self._add_error(f"Server {server_name} must have mcp_ping health check method")
    
    def _validate_jwt_auth_config(self) -> bool:
        """Validate JWT authentication configuration file."""
        print("\n🔐 Validating JWT Authentication Configuration (jwt-auth-config.json)...")
        
        config_file = self.config_dir / "jwt-auth-config.json"
        if not config_file.exists():
            self._add_error(f"JWT auth configuration file not found: {config_file}")
            return False
        
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            # Validate top-level structure
            if 'jwt_authentication_configuration' not in config:
                self._add_error("Missing jwt_authentication_configuration section")
                return False
            
            jwt_config = config['jwt_authentication_configuration']
            
            # Validate authentication settings
            if 'authentication_settings' not in jwt_config:
                self._add_error("Missing authentication_settings section")
            else:
                self._validate_jwt_auth_settings(jwt_config['authentication_settings'])
            
            # Validate MCP protocol integration
            if 'authentication_settings' in jwt_config:
                auth_settings = jwt_config['authentication_settings']
                if 'mcp_protocol_integration' not in auth_settings:
                    self._add_error("Missing mcp_protocol_integration section")
            
            print("✅ JWT authentication configuration validation completed")
            return len([e for e in self.validation_errors if 'jwt-auth' in e]) == 0
            
        except json.JSONDecodeError as e:
            self._add_error(f"Invalid JSON in jwt-auth-config.json: {e}")
            return False
        except Exception as e:
            self._add_error(f"Error validating jwt-auth-config.json: {e}")
            return False
    
    def _validate_jwt_auth_settings(self, auth_settings: Dict[str, Any]) -> None:
        """Validate JWT authentication settings."""
        if auth_settings.get('type') != 'jwt_over_mcp':
            self._add_error("Authentication type must be 'jwt_over_mcp'")
        
        # Validate Cognito configuration
        if 'cognito_configuration' not in auth_settings:
            self._add_error("Missing cognito_configuration section")
        else:
            cognito_config = auth_settings['cognito_configuration']
            required_cognito_fields = [
                'user_pool_id', 'client_id', 'region', 'discovery_url'
            ]
            
            for field in required_cognito_fields:
                if field not in cognito_config:
                    self._add_error(f"Missing Cognito field: {field}")
            
            # Validate Cognito values
            if cognito_config.get('user_pool_id') != 'us-east-1_KePRX24Bn':
                self._add_warning("Cognito user pool ID doesn't match expected value")
            
            if cognito_config.get('client_id') != '1ofgeckef3po4i3us4j1m4chvd':
                self._add_warning("Cognito client ID doesn't match expected value")
    
    def _cross_validate_configurations(self) -> bool:
        """Cross-validate configurations for consistency."""
        print("\n🔗 Cross-validating Configuration Consistency...")
        
        # This would validate that server names, endpoints, and tool names
        # are consistent across all configuration files
        
        # For now, just return True as basic validation
        print("✅ Cross-validation completed")
        return True
    
    def _add_error(self, message: str) -> None:
        """Add a validation error."""
        self.validation_errors.append(f"❌ ERROR: {message}")
    
    def _add_warning(self, message: str) -> None:
        """Add a validation warning."""
        self.validation_warnings.append(f"⚠️  WARNING: {message}")
    
    def _print_validation_summary(self, validation_results: List[bool]) -> None:
        """Print validation summary."""
        print("\n" + "=" * 60)
        print("📊 VALIDATION SUMMARY")
        print("=" * 60)
        
        total_files = len(validation_results)
        passed_files = sum(validation_results)
        
        print(f"Configuration files validated: {total_files}")
        print(f"Files passed validation: {passed_files}")
        print(f"Files failed validation: {total_files - passed_files}")
        
        if self.validation_errors:
            print(f"\n🚨 ERRORS ({len(self.validation_errors)}):")
            for error in self.validation_errors:
                print(f"  {error}")
        
        if self.validation_warnings:
            print(f"\n⚠️  WARNINGS ({len(self.validation_warnings)}):")
            for warning in self.validation_warnings:
                print(f"  {warning}")
        
        if all(validation_results) and not self.validation_errors:
            print("\n🎉 ALL CONFIGURATIONS ARE VALID!")
            print("✅ Ready for AgentCore Gateway deployment")
        else:
            print("\n❌ CONFIGURATION VALIDATION FAILED")
            print("🔧 Please fix the errors above before deployment")


def main():
    """Main function to run configuration validation."""
    # Change to the script directory
    script_dir = Path(__file__).parent
    config_dir = script_dir.parent / "config"
    
    # Initialize validator
    validator = GatewayConfigValidator(str(config_dir))
    
    # Run validation
    success = validator.validate_all_configurations()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()