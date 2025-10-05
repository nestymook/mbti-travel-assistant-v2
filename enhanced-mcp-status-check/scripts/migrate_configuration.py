#!/usr/bin/env python3
"""
Configuration Migration Utilities for Enhanced MCP Status Check System

This script handles migration from existing status check configurations
to the new enhanced dual monitoring system.
"""

import os
import sys
import json
import yaml
import shutil
import logging
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

# Add the enhanced-mcp-status-check directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from config.config_validator import ConfigValidator


class ConfigurationMigrator:
    """Handles migration of existing configurations to enhanced format."""
    
    def __init__(self, backup_enabled: bool = True):
        """Initialize the migrator.
        
        Args:
            backup_enabled: Whether to create backups during migration
        """
        self.backup_enabled = backup_enabled
        self.migration_id = f"migration_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Setup logging
        self.setup_logging()
        
        # Migration mappings
        self.field_mappings = self._create_field_mappings()
        
    def setup_logging(self):
        """Setup migration logging."""
        log_dir = Path("logs/migration")
        log_dir.mkdir(parents=True, exist_ok=True)
        
        log_file = log_dir / f"migration_{self.migration_id}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Starting configuration migration: {self.migration_id}")
        
    def _create_field_mappings(self) -> Dict[str, Dict[str, str]]:
        """Create field mappings for different configuration formats."""
        return {
            "restaurant_search_mcp": {
                "server_name": "server_name",
                "mcp_endpoint": "mcp_endpoint_url",
                "health_endpoint": "rest_health_endpoint_url",
                "timeout": "mcp_timeout_seconds",
                "retry_attempts": "mcp_retry_attempts"
            },
            "restaurant_reasoning_mcp": {
                "server_name": "server_name",
                "mcp_url": "mcp_endpoint_url",
                "status_url": "rest_health_endpoint_url",
                "timeout_seconds": "rest_timeout_seconds",
                "max_retries": "rest_retry_attempts"
            },
            "legacy_status_check": {
                "name": "server_name",
                "endpoint": "mcp_endpoint_url",
                "health_check_url": "rest_health_endpoint_url",
                "timeout": "mcp_timeout_seconds"
            }
        }
        
    def detect_configuration_format(self, config_path: str) -> Optional[str]:
        """Detect the format of an existing configuration file.
        
        Args:
            config_path: Path to configuration file
            
        Returns:
            Configuration format identifier or None if unknown
        """
        try:
            config_data = self._load_config_file(config_path)
            
            # Check for restaurant-search-mcp format
            if "restaurant_search_servers" in config_data:
                return "restaurant_search_mcp"
                
            # Check for restaurant-reasoning-mcp format
            if "reasoning_servers" in config_data:
                return "restaurant_reasoning_mcp"
                
            # Check for legacy status check format
            if "status_check_servers" in config_data:
                return "legacy_status_check"
                
            # Check for enhanced format (already migrated)
            if "enhanced_status_check_system" in config_data:
                return "enhanced_format"
                
            self.logger.warning(f"Unknown configuration format: {config_path}")
            return None
            
        except Exception as e:
            self.logger.error(f"Error detecting configuration format: {e}")
            return None
            
    def _load_config_file(self, config_path: str) -> Dict[str, Any]:
        """Load configuration file (JSON or YAML)."""
        path = Path(config_path)
        
        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
            
        with open(path, 'r') as f:
            if path.suffix.lower() in ['.yaml', '.yml']:
                return yaml.safe_load(f)
            else:
                return json.load(f)
                
    def backup_configuration(self, config_path: str) -> str:
        """Create backup of existing configuration.
        
        Args:
            config_path: Path to configuration file
            
        Returns:
            Path to backup file
        """
        if not self.backup_enabled:
            return ""
            
        backup_dir = Path("backups") / self.migration_id
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        source_path = Path(config_path)
        backup_path = backup_dir / f"{source_path.stem}_backup{source_path.suffix}"
        
        shutil.copy2(source_path, backup_path)
        self.logger.info(f"Configuration backed up to: {backup_path}")
        
        return str(backup_path)
        
    def migrate_restaurant_search_mcp_config(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """Migrate restaurant-search-mcp configuration format."""
        self.logger.info("Migrating restaurant-search-mcp configuration")
        
        enhanced_config = {
            "enhanced_status_check_system": {
                "dual_monitoring_enabled": True,
                "mcp_health_checks": {
                    "enabled": True,
                    "default_timeout_seconds": 10,
                    "tools_list_validation": True,
                    "expected_tools_validation": True
                },
                "rest_health_checks": {
                    "enabled": True,
                    "default_timeout_seconds": 8,
                    "health_endpoint_path": "/status/health",
                    "metrics_endpoint_path": "/status/metrics"
                },
                "result_aggregation": {
                    "mcp_priority_weight": 0.6,
                    "rest_priority_weight": 0.4,
                    "require_both_success_for_healthy": False,
                    "degraded_on_single_failure": True
                },
                "servers": []
            }
        }
        
        # Migrate server configurations
        servers = config_data.get("restaurant_search_servers", [])
        for server in servers:
            enhanced_server = self._migrate_server_config(
                server, "restaurant_search_mcp"
            )
            enhanced_config["enhanced_status_check_system"]["servers"].append(enhanced_server)
            
        return enhanced_config
        
    def migrate_restaurant_reasoning_mcp_config(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """Migrate restaurant-reasoning-mcp configuration format."""
        self.logger.info("Migrating restaurant-reasoning-mcp configuration")
        
        enhanced_config = {
            "enhanced_status_check_system": {
                "dual_monitoring_enabled": True,
                "mcp_health_checks": {
                    "enabled": True,
                    "default_timeout_seconds": 12,
                    "tools_list_validation": True,
                    "expected_tools_validation": True
                },
                "rest_health_checks": {
                    "enabled": True,
                    "default_timeout_seconds": 10,
                    "health_endpoint_path": "/status/health",
                    "metrics_endpoint_path": "/status/metrics"
                },
                "result_aggregation": {
                    "mcp_priority_weight": 0.7,
                    "rest_priority_weight": 0.3,
                    "require_both_success_for_healthy": False,
                    "degraded_on_single_failure": True
                },
                "servers": []
            }
        }
        
        # Migrate server configurations
        servers = config_data.get("reasoning_servers", [])
        for server in servers:
            enhanced_server = self._migrate_server_config(
                server, "restaurant_reasoning_mcp"
            )
            enhanced_config["enhanced_status_check_system"]["servers"].append(enhanced_server)
            
        return enhanced_config
        
    def migrate_legacy_status_check_config(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """Migrate legacy status check configuration format."""
        self.logger.info("Migrating legacy status check configuration")
        
        enhanced_config = {
            "enhanced_status_check_system": {
                "dual_monitoring_enabled": True,
                "mcp_health_checks": {
                    "enabled": True,
                    "default_timeout_seconds": 8,
                    "tools_list_validation": False,  # Legacy may not support this
                    "expected_tools_validation": False
                },
                "rest_health_checks": {
                    "enabled": True,
                    "default_timeout_seconds": 5,
                    "health_endpoint_path": "/health",
                    "metrics_endpoint_path": "/metrics"
                },
                "result_aggregation": {
                    "mcp_priority_weight": 0.5,
                    "rest_priority_weight": 0.5,
                    "require_both_success_for_healthy": False,
                    "degraded_on_single_failure": True
                },
                "servers": []
            }
        }
        
        # Migrate server configurations
        servers = config_data.get("status_check_servers", [])
        for server in servers:
            enhanced_server = self._migrate_server_config(
                server, "legacy_status_check"
            )
            enhanced_config["enhanced_status_check_system"]["servers"].append(enhanced_server)
            
        return enhanced_config
        
    def _migrate_server_config(self, server_config: Dict[str, Any], format_type: str) -> Dict[str, Any]:
        """Migrate individual server configuration."""
        mappings = self.field_mappings.get(format_type, {})
        
        enhanced_server = {
            "server_name": "unknown",
            "mcp_endpoint_url": "",
            "mcp_enabled": True,
            "mcp_timeout_seconds": 10,
            "mcp_expected_tools": [],
            "mcp_retry_attempts": 3,
            "rest_health_endpoint_url": "",
            "rest_enabled": True,
            "rest_timeout_seconds": 8,
            "rest_retry_attempts": 2,
            "jwt_token": None,
            "auth_headers": {},
            "mcp_priority_weight": 0.6,
            "rest_priority_weight": 0.4,
            "require_both_success": False
        }
        
        # Map fields from old format to new format
        for old_field, new_field in mappings.items():
            if old_field in server_config:
                enhanced_server[new_field] = server_config[old_field]
                
        # Set default expected tools based on server type
        if format_type == "restaurant_search_mcp":
            enhanced_server["mcp_expected_tools"] = [
                "search_restaurants_by_district",
                "search_restaurants_by_meal_type",
                "search_restaurants_combined"
            ]
        elif format_type == "restaurant_reasoning_mcp":
            enhanced_server["mcp_expected_tools"] = [
                "search_restaurants_by_district",
                "search_restaurants_by_meal_type",
                "search_restaurants_combined",
                "analyze_restaurant_recommendations"
            ]
            
        return enhanced_server
        
    def validate_migrated_config(self, config_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate migrated configuration.
        
        Args:
            config_data: Migrated configuration data
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        try:
            validator = ConfigValidator()
            validation_result = validator.validate_config(config_data)
            
            return validation_result.is_valid, validation_result.errors
            
        except Exception as e:
            return False, [f"Validation error: {str(e)}"]
            
    def migrate_configuration_file(self, source_path: str, target_path: str = None) -> bool:
        """Migrate a configuration file.
        
        Args:
            source_path: Path to source configuration file
            target_path: Path to target configuration file (optional)
            
        Returns:
            True if migration successful, False otherwise
        """
        try:
            # Detect configuration format
            config_format = self.detect_configuration_format(source_path)
            if not config_format:
                self.logger.error(f"Cannot detect configuration format: {source_path}")
                return False
                
            if config_format == "enhanced_format":
                self.logger.info(f"Configuration already in enhanced format: {source_path}")
                return True
                
            # Load existing configuration
            config_data = self._load_config_file(source_path)
            
            # Create backup
            backup_path = self.backup_configuration(source_path)
            
            # Migrate configuration
            if config_format == "restaurant_search_mcp":
                migrated_config = self.migrate_restaurant_search_mcp_config(config_data)
            elif config_format == "restaurant_reasoning_mcp":
                migrated_config = self.migrate_restaurant_reasoning_mcp_config(config_data)
            elif config_format == "legacy_status_check":
                migrated_config = self.migrate_legacy_status_check_config(config_data)
            else:
                self.logger.error(f"Unsupported configuration format: {config_format}")
                return False
                
            # Validate migrated configuration
            is_valid, errors = self.validate_migrated_config(migrated_config)
            if not is_valid:
                self.logger.error(f"Migrated configuration validation failed: {errors}")
                return False
                
            # Save migrated configuration
            if not target_path:
                target_path = source_path
                
            self._save_config_file(migrated_config, target_path)
            
            self.logger.info(f"Configuration migrated successfully: {source_path} -> {target_path}")
            if backup_path:
                self.logger.info(f"Original configuration backed up to: {backup_path}")
                
            return True
            
        except Exception as e:
            self.logger.error(f"Configuration migration failed: {e}")
            return False
            
    def _save_config_file(self, config_data: Dict[str, Any], config_path: str):
        """Save configuration file (JSON or YAML)."""
        path = Path(config_path)
        
        # Create directory if it doesn't exist
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, 'w') as f:
            if path.suffix.lower() in ['.yaml', '.yml']:
                yaml.dump(config_data, f, default_flow_style=False, indent=2)
            else:
                json.dump(config_data, f, indent=2)
                
    def migrate_directory(self, source_dir: str, target_dir: str = None) -> Dict[str, bool]:
        """Migrate all configuration files in a directory.
        
        Args:
            source_dir: Source directory path
            target_dir: Target directory path (optional)
            
        Returns:
            Dictionary mapping file paths to migration success status
        """
        source_path = Path(source_dir)
        if not source_path.exists():
            self.logger.error(f"Source directory not found: {source_dir}")
            return {}
            
        if not target_dir:
            target_dir = source_dir
            
        target_path = Path(target_dir)
        target_path.mkdir(parents=True, exist_ok=True)
        
        results = {}
        
        # Find configuration files
        config_patterns = ["*.json", "*.yaml", "*.yml"]
        config_files = []
        
        for pattern in config_patterns:
            config_files.extend(source_path.glob(pattern))
            
        for config_file in config_files:
            relative_path = config_file.relative_to(source_path)
            target_file = target_path / relative_path
            
            success = self.migrate_configuration_file(
                str(config_file), str(target_file)
            )
            results[str(config_file)] = success
            
        return results
        
    def create_migration_report(self, results: Dict[str, bool]) -> str:
        """Create migration report.
        
        Args:
            results: Migration results dictionary
            
        Returns:
            Path to migration report file
        """
        successful_migrations = sum(1 for success in results.values() if success)
        total_migrations = len(results)
        
        report = {
            "migration_id": self.migration_id,
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_files": total_migrations,
                "successful_migrations": successful_migrations,
                "failed_migrations": total_migrations - successful_migrations,
                "success_rate": f"{(successful_migrations / total_migrations * 100):.1f}%" if total_migrations > 0 else "0%"
            },
            "results": results,
            "backup_enabled": self.backup_enabled
        }
        
        report_path = Path("logs/migration") / f"migration_report_{self.migration_id}.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
            
        self.logger.info(f"Migration report saved to: {report_path}")
        return str(report_path)


def main():
    """Main migration function."""
    parser = argparse.ArgumentParser(description="Migrate MCP Status Check Configurations")
    parser.add_argument("source", help="Source configuration file or directory")
    parser.add_argument("--target", help="Target configuration file or directory")
    parser.add_argument("--no-backup", action="store_true", 
                       help="Disable backup creation")
    parser.add_argument("--validate-only", action="store_true",
                       help="Only validate configuration format, don't migrate")
    
    args = parser.parse_args()
    
    try:
        migrator = ConfigurationMigrator(backup_enabled=not args.no_backup)
        
        source_path = Path(args.source)
        
        if args.validate_only:
            if source_path.is_file():
                config_format = migrator.detect_configuration_format(args.source)
                if config_format:
                    print(f"✅ Configuration format detected: {config_format}")
                    return 0
                else:
                    print("❌ Unknown configuration format")
                    return 1
            else:
                print("❌ Validation only supports single files")
                return 1
                
        if source_path.is_file():
            # Migrate single file
            success = migrator.migrate_configuration_file(args.source, args.target)
            if success:
                print("✅ Configuration migration completed successfully")
                return 0
            else:
                print("❌ Configuration migration failed")
                return 1
        elif source_path.is_dir():
            # Migrate directory
            results = migrator.migrate_directory(args.source, args.target)
            report_path = migrator.create_migration_report(results)
            
            successful = sum(1 for success in results.values() if success)
            total = len(results)
            
            print(f"Migration completed: {successful}/{total} files migrated successfully")
            print(f"Migration report: {report_path}")
            
            return 0 if successful == total else 1
        else:
            print(f"❌ Source path not found: {args.source}")
            return 1
            
    except Exception as e:
        print(f"❌ Migration error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())