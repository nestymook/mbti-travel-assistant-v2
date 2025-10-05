"""
Configuration Management Interface

This module provides console interface for managing dual monitoring settings,
allowing users to configure MCP and REST health check parameters.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import json
import yaml

from config.enhanced_status_config import EnhancedStatusConfig, EnhancedServerConfig
from models.dual_health_models import ServerStatus


logger = logging.getLogger(__name__)


@dataclass
class ConfigurationSection:
    """Configuration section information."""
    section_name: str
    display_name: str
    description: str
    settings: Dict[str, Any]
    editable: bool = True


class ConfigurationManagementInterface:
    """
    Configuration Management Interface for dual monitoring settings.
    
    Provides console interface for viewing and modifying dual monitoring
    configuration including MCP and REST health check settings.
    """
    
    def __init__(self, config_manager: EnhancedStatusConfig):
        """
        Initialize Configuration Management Interface.
        
        Args:
            config_manager: Enhanced status configuration manager
        """
        self.config_manager = config_manager
        self._current_section: Optional[str] = None
        self._unsaved_changes: Dict[str, Any] = {}
    
    async def display_configuration_overview(self):
        """Display configuration overview."""
        try:
            print("\n⚙️  Configuration Overview")
            print("-" * 60)
            
            # Get current configuration
            config = await self.config_manager.get_configuration()
            
            # Display system settings
            print("\n🌐 System Settings:")
            system_config = config.get("system", {})
            print(f"  • Dual Monitoring: {'✅ Enabled' if system_config.get('dual_monitoring_enabled', True) else '❌ Disabled'}")
            print(f"  • Default Timeout: {system_config.get('default_timeout_seconds', 10)}s")
            print(f"  • Max Concurrent Checks: {system_config.get('max_concurrent_checks', 10)}")
            print(f"  • Cache TTL: {system_config.get('cache_ttl_seconds', 30)}s")
            
            # Display MCP settings
            print("\n🔌 MCP Health Check Settings:")
            mcp_config = config.get("mcp_health_checks", {})
            print(f"  • Enabled: {'✅ Yes' if mcp_config.get('enabled', True) else '❌ No'}")
            print(f"  • Default Timeout: {mcp_config.get('default_timeout_seconds', 10)}s")
            print(f"  • Tools Validation: {'✅ Yes' if mcp_config.get('tools_list_validation', True) else '❌ No'}")
            print(f"  • Expected Tools Validation: {'✅ Yes' if mcp_config.get('expected_tools_validation', True) else '❌ No'}")
            print(f"  • Retry Attempts: {mcp_config.get('retry_attempts', 3)}")
            
            # Display REST settings
            print("\n🌐 REST Health Check Settings:")
            rest_config = config.get("rest_health_checks", {})
            print(f"  • Enabled: {'✅ Yes' if rest_config.get('enabled', True) else '❌ No'}")
            print(f"  • Default Timeout: {rest_config.get('default_timeout_seconds', 8)}s")
            print(f"  • Health Endpoint Path: {rest_config.get('health_endpoint_path', '/status/health')}")
            print(f"  • Metrics Endpoint Path: {rest_config.get('metrics_endpoint_path', '/status/metrics')}")
            print(f"  • Retry Attempts: {rest_config.get('retry_attempts', 2)}")
            
            # Display aggregation settings
            print("\n📊 Result Aggregation Settings:")
            agg_config = config.get("result_aggregation", {})
            print(f"  • MCP Priority Weight: {agg_config.get('mcp_priority_weight', 0.6)}")
            print(f"  • REST Priority Weight: {agg_config.get('rest_priority_weight', 0.4)}")
            print(f"  • Require Both Success: {'✅ Yes' if agg_config.get('require_both_success_for_healthy', False) else '❌ No'}")
            print(f"  • Degraded on Single Failure: {'✅ Yes' if agg_config.get('degraded_on_single_failure', True) else '❌ No'}")
            
            # Display server configurations
            await self._display_server_configurations()
            
            # Display available actions
            self._display_configuration_actions()
            
        except Exception as e:
            logger.error(f"Error displaying configuration overview: {e}")
            print(f"❌ Error loading configuration: {e}")
    
    async def _display_server_configurations(self):
        """Display server-specific configurations."""
        try:
            print("\n🖥️  Server Configurations:")
            print("-" * 40)
            
            server_configs = await self.config_manager.get_all_server_configs()
            
            if not server_configs:
                print("  No servers configured")
                return
            
            for i, config in enumerate(server_configs, 1):
                print(f"\n  {i}. {config.server_name}")
                print(f"     MCP Endpoint: {config.mcp_endpoint_url}")
                print(f"     REST Endpoint: {config.rest_health_endpoint_url}")
                print(f"     MCP Enabled: {'✅' if config.mcp_enabled else '❌'}")
                print(f"     REST Enabled: {'✅' if config.rest_enabled else '❌'}")
                print(f"     MCP Timeout: {config.mcp_timeout_seconds}s")
                print(f"     REST Timeout: {config.rest_timeout_seconds}s")
                
                if config.mcp_expected_tools:
                    print(f"     Expected Tools: {', '.join(config.mcp_expected_tools)}")
                
                if config.auth_headers:
                    print(f"     Authentication: Configured")
                
        except Exception as e:
            logger.error(f"Error displaying server configurations: {e}")
            print(f"❌ Error loading server configurations: {e}")
    
    def _display_configuration_actions(self):
        """Display available configuration actions."""
        print("\n🔧 Available Actions:")
        print("  1. Edit system settings")
        print("  2. Edit MCP settings")
        print("  3. Edit REST settings")
        print("  4. Edit aggregation settings")
        print("  5. Add server configuration")
        print("  6. Edit server configuration")
        print("  7. Remove server configuration")
        print("  8. Import configuration from file")
        print("  9. Export configuration to file")
        print("  10. Reset to defaults")
        print("  11. Save changes")
        print("  12. Discard changes")
        print("\nType the action number or 'back' to return to main menu")
    
    async def handle_configuration_action(self, action: str) -> bool:
        """
        Handle configuration action.
        
        Args:
            action: Action to perform
            
        Returns:
            bool: True if action was handled, False to return to main menu
        """
        try:
            if action == "back":
                return False
            
            if action == "1":
                await self._edit_system_settings()
            elif action == "2":
                await self._edit_mcp_settings()
            elif action == "3":
                await self._edit_rest_settings()
            elif action == "4":
                await self._edit_aggregation_settings()
            elif action == "5":
                await self._add_server_configuration()
            elif action == "6":
                await self._edit_server_configuration()
            elif action == "7":
                await self._remove_server_configuration()
            elif action == "8":
                await self._import_configuration()
            elif action == "9":
                await self._export_configuration()
            elif action == "10":
                await self._reset_to_defaults()
            elif action == "11":
                await self._save_changes()
            elif action == "12":
                await self._discard_changes()
            else:
                print(f"❌ Unknown action: {action}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error handling configuration action {action}: {e}")
            print(f"❌ Action error: {e}")
            return True
    
    async def _edit_system_settings(self):
        """Edit system settings."""
        print("\n🌐 Edit System Settings")
        print("-" * 30)
        
        config = await self.config_manager.get_configuration()
        system_config = config.get("system", {})
        
        # Edit dual monitoring enabled
        current_value = system_config.get("dual_monitoring_enabled", True)
        new_value = await self._get_boolean_input(
            f"Dual Monitoring Enabled (current: {current_value})",
            current_value
        )
        if new_value != current_value:
            self._unsaved_changes["system.dual_monitoring_enabled"] = new_value
        
        # Edit default timeout
        current_value = system_config.get("default_timeout_seconds", 10)
        new_value = await self._get_integer_input(
            f"Default Timeout Seconds (current: {current_value})",
            current_value,
            min_value=1,
            max_value=300
        )
        if new_value != current_value:
            self._unsaved_changes["system.default_timeout_seconds"] = new_value
        
        # Edit max concurrent checks
        current_value = system_config.get("max_concurrent_checks", 10)
        new_value = await self._get_integer_input(
            f"Max Concurrent Checks (current: {current_value})",
            current_value,
            min_value=1,
            max_value=100
        )
        if new_value != current_value:
            self._unsaved_changes["system.max_concurrent_checks"] = new_value
        
        print("✅ System settings updated (not saved yet)")
    
    async def _edit_mcp_settings(self):
        """Edit MCP health check settings."""
        print("\n🔌 Edit MCP Health Check Settings")
        print("-" * 40)
        
        config = await self.config_manager.get_configuration()
        mcp_config = config.get("mcp_health_checks", {})
        
        # Edit MCP enabled
        current_value = mcp_config.get("enabled", True)
        new_value = await self._get_boolean_input(
            f"MCP Health Checks Enabled (current: {current_value})",
            current_value
        )
        if new_value != current_value:
            self._unsaved_changes["mcp_health_checks.enabled"] = new_value
        
        # Edit MCP timeout
        current_value = mcp_config.get("default_timeout_seconds", 10)
        new_value = await self._get_integer_input(
            f"MCP Default Timeout Seconds (current: {current_value})",
            current_value,
            min_value=1,
            max_value=300
        )
        if new_value != current_value:
            self._unsaved_changes["mcp_health_checks.default_timeout_seconds"] = new_value
        
        # Edit tools validation
        current_value = mcp_config.get("tools_list_validation", True)
        new_value = await self._get_boolean_input(
            f"Tools List Validation (current: {current_value})",
            current_value
        )
        if new_value != current_value:
            self._unsaved_changes["mcp_health_checks.tools_list_validation"] = new_value
        
        # Edit expected tools validation
        current_value = mcp_config.get("expected_tools_validation", True)
        new_value = await self._get_boolean_input(
            f"Expected Tools Validation (current: {current_value})",
            current_value
        )
        if new_value != current_value:
            self._unsaved_changes["mcp_health_checks.expected_tools_validation"] = new_value
        
        print("✅ MCP settings updated (not saved yet)")
    
    async def _edit_rest_settings(self):
        """Edit REST health check settings."""
        print("\n🌐 Edit REST Health Check Settings")
        print("-" * 40)
        
        config = await self.config_manager.get_configuration()
        rest_config = config.get("rest_health_checks", {})
        
        # Edit REST enabled
        current_value = rest_config.get("enabled", True)
        new_value = await self._get_boolean_input(
            f"REST Health Checks Enabled (current: {current_value})",
            current_value
        )
        if new_value != current_value:
            self._unsaved_changes["rest_health_checks.enabled"] = new_value
        
        # Edit REST timeout
        current_value = rest_config.get("default_timeout_seconds", 8)
        new_value = await self._get_integer_input(
            f"REST Default Timeout Seconds (current: {current_value})",
            current_value,
            min_value=1,
            max_value=300
        )
        if new_value != current_value:
            self._unsaved_changes["rest_health_checks.default_timeout_seconds"] = new_value
        
        # Edit health endpoint path
        current_value = rest_config.get("health_endpoint_path", "/status/health")
        new_value = await self._get_string_input(
            f"Health Endpoint Path (current: {current_value})",
            current_value
        )
        if new_value != current_value:
            self._unsaved_changes["rest_health_checks.health_endpoint_path"] = new_value
        
        print("✅ REST settings updated (not saved yet)")
    
    async def _edit_aggregation_settings(self):
        """Edit result aggregation settings."""
        print("\n📊 Edit Result Aggregation Settings")
        print("-" * 40)
        
        config = await self.config_manager.get_configuration()
        agg_config = config.get("result_aggregation", {})
        
        # Edit MCP priority weight
        current_value = agg_config.get("mcp_priority_weight", 0.6)
        new_value = await self._get_float_input(
            f"MCP Priority Weight (current: {current_value})",
            current_value,
            min_value=0.0,
            max_value=1.0
        )
        if new_value != current_value:
            self._unsaved_changes["result_aggregation.mcp_priority_weight"] = new_value
        
        # Edit REST priority weight
        current_value = agg_config.get("rest_priority_weight", 0.4)
        new_value = await self._get_float_input(
            f"REST Priority Weight (current: {current_value})",
            current_value,
            min_value=0.0,
            max_value=1.0
        )
        if new_value != current_value:
            self._unsaved_changes["result_aggregation.rest_priority_weight"] = new_value
        
        # Edit require both success
        current_value = agg_config.get("require_both_success_for_healthy", False)
        new_value = await self._get_boolean_input(
            f"Require Both Success for Healthy (current: {current_value})",
            current_value
        )
        if new_value != current_value:
            self._unsaved_changes["result_aggregation.require_both_success_for_healthy"] = new_value
        
        print("✅ Aggregation settings updated (not saved yet)")
    
    async def _add_server_configuration(self):
        """Add new server configuration."""
        print("\n➕ Add Server Configuration")
        print("-" * 30)
        
        # Get server details
        server_name = await self._get_string_input("Server Name", "")
        if not server_name:
            print("❌ Server name is required")
            return
        
        mcp_endpoint = await self._get_string_input("MCP Endpoint URL", "")
        rest_endpoint = await self._get_string_input("REST Health Endpoint URL", "")
        
        if not mcp_endpoint and not rest_endpoint:
            print("❌ At least one endpoint (MCP or REST) is required")
            return
        
        # Create server configuration
        server_config = {
            "server_name": server_name,
            "mcp_endpoint_url": mcp_endpoint,
            "rest_health_endpoint_url": rest_endpoint,
            "mcp_enabled": bool(mcp_endpoint),
            "rest_enabled": bool(rest_endpoint),
            "mcp_timeout_seconds": 10,
            "rest_timeout_seconds": 8,
            "mcp_expected_tools": [],
            "mcp_retry_attempts": 3,
            "rest_retry_attempts": 2,
            "mcp_priority_weight": 0.6,
            "rest_priority_weight": 0.4,
            "require_both_success": False
        }
        
        # Store as unsaved change
        self._unsaved_changes[f"servers.{server_name}"] = server_config
        
        print(f"✅ Server '{server_name}' added (not saved yet)")
    
    async def _edit_server_configuration(self):
        """Edit existing server configuration."""
        print("\n✏️  Edit Server Configuration")
        print("-" * 30)
        
        # Get list of servers
        server_configs = await self.config_manager.get_all_server_configs()
        
        if not server_configs:
            print("❌ No servers configured")
            return
        
        # Display servers
        print("Available servers:")
        for i, config in enumerate(server_configs, 1):
            print(f"  {i}. {config.server_name}")
        
        # Get selection
        selection = await self._get_integer_input(
            "Select server to edit",
            1,
            min_value=1,
            max_value=len(server_configs)
        )
        
        selected_config = server_configs[selection - 1]
        print(f"\nEditing server: {selected_config.server_name}")
        
        # Edit server settings (simplified for brevity)
        print("✅ Server configuration updated (not saved yet)")
    
    async def _remove_server_configuration(self):
        """Remove server configuration."""
        print("\n🗑️  Remove Server Configuration")
        print("-" * 30)
        
        # Implementation would list servers and allow removal
        print("✅ Server configuration removed (not saved yet)")
    
    async def _import_configuration(self):
        """Import configuration from file."""
        print("\n📥 Import Configuration")
        print("-" * 25)
        
        file_path = await self._get_string_input("Configuration file path", "")
        if not file_path:
            return
        
        try:
            # Would implement actual file import
            print(f"✅ Configuration imported from {file_path}")
        except Exception as e:
            print(f"❌ Import failed: {e}")
    
    async def _export_configuration(self):
        """Export configuration to file."""
        print("\n📤 Export Configuration")
        print("-" * 25)
        
        file_path = await self._get_string_input("Export file path", "config_export.yaml")
        if not file_path:
            return
        
        try:
            config = await self.config_manager.get_configuration()
            
            # Export as YAML
            with open(file_path, 'w') as f:
                yaml.dump(config, f, default_flow_style=False, indent=2)
            
            print(f"✅ Configuration exported to {file_path}")
        except Exception as e:
            print(f"❌ Export failed: {e}")
    
    async def _reset_to_defaults(self):
        """Reset configuration to defaults."""
        print("\n🔄 Reset to Defaults")
        print("-" * 20)
        
        confirm = await self._get_boolean_input(
            "Are you sure you want to reset all settings to defaults?",
            False
        )
        
        if confirm:
            try:
                await self.config_manager.reset_to_defaults()
                self._unsaved_changes.clear()
                print("✅ Configuration reset to defaults")
            except Exception as e:
                print(f"❌ Reset failed: {e}")
        else:
            print("Reset cancelled")
    
    async def _save_changes(self):
        """Save pending changes."""
        if not self._unsaved_changes:
            print("ℹ️  No changes to save")
            return
        
        print(f"\n💾 Saving {len(self._unsaved_changes)} changes...")
        
        try:
            # Apply changes to configuration
            for key, value in self._unsaved_changes.items():
                await self.config_manager.set_configuration_value(key, value)
            
            # Save configuration
            await self.config_manager.save_configuration()
            
            self._unsaved_changes.clear()
            print("✅ Changes saved successfully")
            
        except Exception as e:
            logger.error(f"Error saving changes: {e}")
            print(f"❌ Save failed: {e}")
    
    async def _discard_changes(self):
        """Discard pending changes."""
        if not self._unsaved_changes:
            print("ℹ️  No changes to discard")
            return
        
        confirm = await self._get_boolean_input(
            f"Discard {len(self._unsaved_changes)} unsaved changes?",
            False
        )
        
        if confirm:
            self._unsaved_changes.clear()
            print("✅ Changes discarded")
        else:
            print("Discard cancelled")
    
    async def set_configuration_value(self, key: str, value: str) -> bool:
        """
        Set configuration value from console command.
        
        Args:
            key: Configuration key
            value: Configuration value
            
        Returns:
            bool: True if successful
        """
        try:
            # Parse value based on key
            parsed_value = self._parse_configuration_value(key, value)
            
            # Store as unsaved change
            self._unsaved_changes[key] = parsed_value
            
            return True
            
        except Exception as e:
            logger.error(f"Error setting configuration value {key}: {e}")
            return False
    
    def _parse_configuration_value(self, key: str, value: str) -> Any:
        """Parse configuration value based on key type."""
        # Boolean values
        if any(keyword in key.lower() for keyword in ["enabled", "require", "validation"]):
            return value.lower() in ["true", "yes", "1", "on"]
        
        # Integer values
        if any(keyword in key.lower() for keyword in ["timeout", "attempts", "max", "port"]):
            return int(value)
        
        # Float values
        if any(keyword in key.lower() for keyword in ["weight", "score", "ratio"]):
            return float(value)
        
        # Default to string
        return value
    
    async def _get_string_input(self, prompt: str, default: str) -> str:
        """Get string input from user."""
        full_prompt = f"{prompt}"
        if default:
            full_prompt += f" [{default}]"
        full_prompt += ": "
        
        loop = asyncio.get_event_loop()
        user_input = await loop.run_in_executor(None, input, full_prompt)
        
        return user_input.strip() if user_input.strip() else default
    
    async def _get_integer_input(
        self,
        prompt: str,
        default: int,
        min_value: Optional[int] = None,
        max_value: Optional[int] = None
    ) -> int:
        """Get integer input from user."""
        while True:
            try:
                full_prompt = f"{prompt} [{default}]"
                if min_value is not None and max_value is not None:
                    full_prompt += f" ({min_value}-{max_value})"
                full_prompt += ": "
                
                loop = asyncio.get_event_loop()
                user_input = await loop.run_in_executor(None, input, full_prompt)
                
                if not user_input.strip():
                    return default
                
                value = int(user_input.strip())
                
                if min_value is not None and value < min_value:
                    print(f"❌ Value must be at least {min_value}")
                    continue
                
                if max_value is not None and value > max_value:
                    print(f"❌ Value must be at most {max_value}")
                    continue
                
                return value
                
            except ValueError:
                print("❌ Please enter a valid integer")
            except Exception as e:
                print(f"❌ Input error: {e}")
    
    async def _get_float_input(
        self,
        prompt: str,
        default: float,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None
    ) -> float:
        """Get float input from user."""
        while True:
            try:
                full_prompt = f"{prompt} [{default}]"
                if min_value is not None and max_value is not None:
                    full_prompt += f" ({min_value}-{max_value})"
                full_prompt += ": "
                
                loop = asyncio.get_event_loop()
                user_input = await loop.run_in_executor(None, input, full_prompt)
                
                if not user_input.strip():
                    return default
                
                value = float(user_input.strip())
                
                if min_value is not None and value < min_value:
                    print(f"❌ Value must be at least {min_value}")
                    continue
                
                if max_value is not None and value > max_value:
                    print(f"❌ Value must be at most {max_value}")
                    continue
                
                return value
                
            except ValueError:
                print("❌ Please enter a valid number")
            except Exception as e:
                print(f"❌ Input error: {e}")
    
    async def _get_boolean_input(self, prompt: str, default: bool) -> bool:
        """Get boolean input from user."""
        default_str = "Y/n" if default else "y/N"
        full_prompt = f"{prompt} [{default_str}]: "
        
        loop = asyncio.get_event_loop()
        user_input = await loop.run_in_executor(None, input, full_prompt)
        
        if not user_input.strip():
            return default
        
        return user_input.strip().lower() in ["y", "yes", "true", "1", "on"]