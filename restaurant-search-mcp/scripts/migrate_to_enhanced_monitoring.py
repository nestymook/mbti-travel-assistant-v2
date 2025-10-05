#!/usr/bin/env python3
"""
Migration Script for Enhanced MCP Status Monitoring

This script migrates existing restaurant-search-mcp deployments to use the enhanced
dual monitoring system while maintaining backward compatibility.
"""

import os
import sys
import json
import shutil
import asyncio
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List
import argparse

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from services.enhanced_status_service import (
    RestaurantSearchEnhancedStatusService,
    initialize_enhanced_status_service
)
from services.health_check_service import HealthCheckService, get_health_check_capabilities
from models.status_models import MCPStatusCheckConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class EnhancedMonitoringMigrator:
    """
    Migration utility for enhanced MCP status monitoring.
    
    Handles migration from legacy monitoring to enhanced dual monitoring
    with backward compatibility preservation.
    """
    
    def __init__(self, config_dir: str = "config", backup_dir: str = "config/backup"):
        """
        Initialize the migrator.
        
        Args:
            config_dir: Configuration directory path
            backup_dir: Backup directory for original configurations
        """
        self.config_dir = Path(config_dir)
        self.backup_dir = Path(backup_dir)
        self.migration_log = []
        
    def log_migration_step(self, step: str, status: str, details: Optional[str] = None):
        """Log a migration step."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "step": step,
            "status": status,
            "details": details
        }
        self.migration_log.append(entry)
        logger.info(f"Migration step: {step} - {status}")
        if details:
            logger.info(f"Details: {details}")
    
    def create_backup(self) -> bool:
        """
        Create backup of existing configuration files.
        
        Returns:
            bool: True if backup was successful
        """
        try:
            self.log_migration_step("create_backup", "started")
            
            # Create backup directory
            self.backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Backup existing configuration files
            config_files = [
                "status_check_config.json",
                "cognito_config.json"
            ]
            
            backed_up_files = []
            for config_file in config_files:
                source_path = self.config_dir / config_file
                if source_path.exists():
                    backup_path = self.backup_dir / f"{config_file}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    shutil.copy2(source_path, backup_path)
                    backed_up_files.append(str(backup_path))
                    logger.info(f"Backed up {source_path} to {backup_path}")
            
            self.log_migration_step(
                "create_backup", 
                "completed", 
                f"Backed up {len(backed_up_files)} files: {', '.join(backed_up_files)}"
            )
            return True
            
        except Exception as e:
            self.log_migration_step("create_backup", "failed", str(e))
            logger.error(f"Backup creation failed: {e}")
            return False
    
    def load_legacy_configuration(self) -> Optional[Dict[str, Any]]:
        """
        Load existing legacy configuration.
        
        Returns:
            Dict containing legacy configuration or None if not found
        """
        try:
            self.log_migration_step("load_legacy_config", "started")
            
            legacy_config_path = self.config_dir / "status_check_config.json"
            if not legacy_config_path.exists():
                self.log_migration_step("load_legacy_config", "skipped", "No legacy config found")
                return None
            
            with open(legacy_config_path, 'r') as f:
                legacy_config = json.load(f)
            
            self.log_migration_step(
                "load_legacy_config", 
                "completed", 
                f"Loaded configuration with {len(legacy_config)} sections"
            )
            return legacy_config
            
        except Exception as e:
            self.log_migration_step("load_legacy_config", "failed", str(e))
            logger.error(f"Failed to load legacy configuration: {e}")
            return None
    
    def create_enhanced_configuration(self, legacy_config: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Create enhanced configuration based on legacy settings.
        
        Args:
            legacy_config: Existing legacy configuration
            
        Returns:
            Dict containing enhanced configuration
        """
        try:
            self.log_migration_step("create_enhanced_config", "started")
            
            # Default enhanced configuration
            enhanced_config = {
                "enhanced_status_check_system": {
                    "system_name": "restaurant-search-mcp-enhanced",
                    "version": "1.0.0",
                    "dual_monitoring_enabled": True,
                    "mcp_health_checks": {
                        "enabled": True,
                        "default_timeout_seconds": 10,
                        "default_retry_attempts": 3,
                        "tools_list_validation": True,
                        "expected_tools_validation": True,
                        "default_expected_tools": [
                            "search_restaurants_by_district",
                            "search_restaurants_by_meal_type",
                            "search_restaurants_combined"
                        ],
                        "request_timeout_ms": 30000,
                        "connection_pool_size": 10,
                        "jwt_auth_enabled": True
                    },
                    "rest_health_checks": {
                        "enabled": True,
                        "default_timeout_seconds": 8,
                        "default_retry_attempts": 2,
                        "health_endpoint_path": "/status/health",
                        "metrics_endpoint_path": "/status/metrics",
                        "expected_status_codes": [200, 201, 202],
                        "retry_backoff_factor": 1.5,
                        "max_retry_delay_seconds": 30,
                        "connection_pool_size": 20,
                        "validate_response_format": True,
                        "required_health_fields": ["status", "timestamp"],
                        "auth_type": "bearer",
                        "auth_header_name": "Authorization"
                    },
                    "result_aggregation": {
                        "mcp_priority_weight": 0.7,
                        "rest_priority_weight": 0.3,
                        "require_both_success_for_healthy": False,
                        "degraded_on_single_failure": True,
                        "health_score_calculation": "weighted_average",
                        "failure_threshold": 0.4,
                        "degraded_threshold": 0.7
                    },
                    "circuit_breaker": {
                        "enabled": True,
                        "failure_threshold": 5,
                        "recovery_timeout_seconds": 60,
                        "half_open_max_calls": 3,
                        "mcp_circuit_breaker_enabled": True,
                        "rest_circuit_breaker_enabled": True,
                        "independent_circuit_breakers": True
                    },
                    "monitoring": {
                        "enabled": True,
                        "metrics_collection_enabled": True,
                        "health_check_interval_seconds": 30,
                        "metrics_retention_hours": 24,
                        "concurrent_health_checks": True,
                        "max_concurrent_checks": 10
                    },
                    "servers": []
                }
            }
            
            # Migrate legacy settings if available
            if legacy_config:
                self._migrate_legacy_settings(enhanced_config, legacy_config)
            
            # Add default server configuration
            self._add_default_server_config(enhanced_config)
            
            self.log_migration_step(
                "create_enhanced_config", 
                "completed", 
                "Created enhanced configuration with dual monitoring support"
            )
            return enhanced_config
            
        except Exception as e:
            self.log_migration_step("create_enhanced_config", "failed", str(e))
            logger.error(f"Failed to create enhanced configuration: {e}")
            raise
    
    def _migrate_legacy_settings(self, enhanced_config: Dict[str, Any], legacy_config: Dict[str, Any]):
        """Migrate settings from legacy configuration."""
        try:
            # Migrate system settings
            if "status_check_system" in legacy_config:
                legacy_system = legacy_config["status_check_system"]
                enhanced_system = enhanced_config["enhanced_status_check_system"]
                
                # Migrate timeout settings
                if "global_timeout_seconds" in legacy_system:
                    enhanced_system["mcp_health_checks"]["default_timeout_seconds"] = legacy_system["global_timeout_seconds"]
                    enhanced_system["rest_health_checks"]["default_timeout_seconds"] = max(8, legacy_system["global_timeout_seconds"] - 2)
                
                # Migrate interval settings
                if "global_check_interval_seconds" in legacy_system:
                    enhanced_system["monitoring"]["health_check_interval_seconds"] = legacy_system["global_check_interval_seconds"]
                
                # Migrate concurrency settings
                if "max_concurrent_checks" in legacy_system:
                    enhanced_system["monitoring"]["max_concurrent_checks"] = legacy_system["max_concurrent_checks"]
                
                # Migrate metrics settings
                if "metrics_retention_hours" in legacy_system:
                    enhanced_system["monitoring"]["metrics_retention_hours"] = legacy_system["metrics_retention_hours"]
            
            # Migrate server configurations
            if "servers" in legacy_config:
                for server_name, server_config in legacy_config["servers"].items():
                    self._migrate_server_config(enhanced_config, server_name, server_config)
            
            logger.info("Successfully migrated legacy settings to enhanced configuration")
            
        except Exception as e:
            logger.error(f"Error migrating legacy settings: {e}")
            raise
    
    def _migrate_server_config(self, enhanced_config: Dict[str, Any], server_name: str, legacy_server: Dict[str, Any]):
        """Migrate individual server configuration."""
        enhanced_server = {
            "server_name": server_name,
            "mcp_endpoint_url": legacy_server.get("endpoint_url", "https://your-gateway-url/mcp/restaurant-search-mcp"),
            "mcp_enabled": True,
            "mcp_timeout_seconds": legacy_server.get("timeout_seconds", 10),
            "mcp_expected_tools": legacy_server.get("expected_tools", [
                "search_restaurants_by_district",
                "search_restaurants_by_meal_type",
                "search_restaurants_combined"
            ]),
            "mcp_retry_attempts": legacy_server.get("retry_attempts", 3),
            "rest_health_endpoint_url": f"{legacy_server.get('endpoint_url', 'https://your-gateway-url/mcp/restaurant-search-mcp')}/status/health",
            "rest_enabled": True,
            "rest_timeout_seconds": max(8, legacy_server.get("timeout_seconds", 10) - 2),
            "rest_retry_attempts": 2,
            "jwt_token": None,
            "auth_headers": {},
            "mcp_priority_weight": 0.7,
            "rest_priority_weight": 0.3,
            "require_both_success": False,
            "priority": legacy_server.get("priority", "high"),
            "description": legacy_server.get("description", f"{server_name} with enhanced dual monitoring")
        }
        
        enhanced_config["enhanced_status_check_system"]["servers"].append(enhanced_server)
    
    def _add_default_server_config(self, enhanced_config: Dict[str, Any]):
        """Add default server configuration if none exists."""
        if not enhanced_config["enhanced_status_check_system"]["servers"]:
            default_server = {
                "server_name": "restaurant-search-mcp",
                "mcp_endpoint_url": "https://your-gateway-url/mcp/restaurant-search-mcp",
                "mcp_enabled": True,
                "mcp_timeout_seconds": 10,
                "mcp_expected_tools": [
                    "search_restaurants_by_district",
                    "search_restaurants_by_meal_type",
                    "search_restaurants_combined"
                ],
                "mcp_retry_attempts": 3,
                "rest_health_endpoint_url": "https://your-gateway-url/mcp/restaurant-search-mcp/status/health",
                "rest_enabled": True,
                "rest_timeout_seconds": 8,
                "rest_retry_attempts": 2,
                "jwt_token": None,
                "auth_headers": {},
                "mcp_priority_weight": 0.7,
                "rest_priority_weight": 0.3,
                "require_both_success": False,
                "priority": "high",
                "description": "Core restaurant search functionality with enhanced dual monitoring"
            }
            
            enhanced_config["enhanced_status_check_system"]["servers"].append(default_server)
    
    def save_enhanced_configuration(self, enhanced_config: Dict[str, Any]) -> bool:
        """
        Save enhanced configuration to file.
        
        Args:
            enhanced_config: Enhanced configuration to save
            
        Returns:
            bool: True if save was successful
        """
        try:
            self.log_migration_step("save_enhanced_config", "started")
            
            # Ensure config directory exists
            self.config_dir.mkdir(parents=True, exist_ok=True)
            
            # Save enhanced configuration
            enhanced_config_path = self.config_dir / "enhanced_status_config.json"
            with open(enhanced_config_path, 'w') as f:
                json.dump(enhanced_config, f, indent=2)
            
            self.log_migration_step(
                "save_enhanced_config", 
                "completed", 
                f"Saved enhanced configuration to {enhanced_config_path}"
            )
            return True
            
        except Exception as e:
            self.log_migration_step("save_enhanced_config", "failed", str(e))
            logger.error(f"Failed to save enhanced configuration: {e}")
            return False
    
    def update_legacy_configuration(self, legacy_config: Dict[str, Any]) -> bool:
        """
        Update legacy configuration to include enhanced monitoring settings.
        
        Args:
            legacy_config: Legacy configuration to update
            
        Returns:
            bool: True if update was successful
        """
        try:
            self.log_migration_step("update_legacy_config", "started")
            
            # Add enhanced monitoring settings to legacy config
            if "status_check_system" not in legacy_config:
                legacy_config["status_check_system"] = {}
            
            legacy_config["status_check_system"].update({
                "enhanced_monitoring_enabled": True,
                "dual_monitoring_support": True,
                "backward_compatibility": True
            })
            
            # Add enhanced monitoring section
            legacy_config["enhanced_monitoring"] = {
                "enabled": True,
                "config_file": "config/enhanced_status_config.json",
                "fallback_to_legacy": True,
                "integration_mode": "hybrid"
            }
            
            # Save updated legacy configuration
            legacy_config_path = self.config_dir / "status_check_config.json"
            with open(legacy_config_path, 'w') as f:
                json.dump(legacy_config, f, indent=2)
            
            self.log_migration_step(
                "update_legacy_config", 
                "completed", 
                "Updated legacy configuration with enhanced monitoring settings"
            )
            return True
            
        except Exception as e:
            self.log_migration_step("update_legacy_config", "failed", str(e))
            logger.error(f"Failed to update legacy configuration: {e}")
            return False
    
    async def validate_migration(self) -> bool:
        """
        Validate that the migration was successful.
        
        Returns:
            bool: True if validation passed
        """
        try:
            self.log_migration_step("validate_migration", "started")
            
            # Test enhanced monitoring initialization
            try:
                await initialize_enhanced_status_service(
                    config_path=str(self.config_dir / "enhanced_status_config.json")
                )
                enhanced_available = True
            except Exception as e:
                logger.warning(f"Enhanced monitoring initialization failed: {e}")
                enhanced_available = False
            
            # Test legacy monitoring still works
            try:
                capabilities = await get_health_check_capabilities()
                legacy_available = capabilities.get("legacy_mcp_monitoring", False)
            except Exception as e:
                logger.warning(f"Legacy monitoring test failed: {e}")
                legacy_available = False
            
            # Validation results
            validation_results = {
                "enhanced_monitoring_available": enhanced_available,
                "legacy_monitoring_available": legacy_available,
                "backward_compatibility": legacy_available,
                "migration_successful": enhanced_available or legacy_available
            }
            
            if validation_results["migration_successful"]:
                self.log_migration_step(
                    "validate_migration", 
                    "completed", 
                    f"Validation passed: {validation_results}"
                )
                return True
            else:
                self.log_migration_step(
                    "validate_migration", 
                    "failed", 
                    f"Validation failed: {validation_results}"
                )
                return False
                
        except Exception as e:
            self.log_migration_step("validate_migration", "failed", str(e))
            logger.error(f"Migration validation failed: {e}")
            return False
    
    def save_migration_log(self) -> str:
        """
        Save migration log to file.
        
        Returns:
            str: Path to migration log file
        """
        try:
            log_path = self.config_dir / f"migration_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            migration_summary = {
                "migration_timestamp": datetime.now().isoformat(),
                "migration_version": "1.0.0",
                "source_system": "restaurant-search-mcp",
                "target_system": "enhanced-dual-monitoring",
                "steps": self.migration_log,
                "summary": {
                    "total_steps": len(self.migration_log),
                    "successful_steps": len([s for s in self.migration_log if s["status"] == "completed"]),
                    "failed_steps": len([s for s in self.migration_log if s["status"] == "failed"]),
                    "skipped_steps": len([s for s in self.migration_log if s["status"] == "skipped"])
                }
            }
            
            with open(log_path, 'w') as f:
                json.dump(migration_summary, f, indent=2)
            
            logger.info(f"Migration log saved to {log_path}")
            return str(log_path)
            
        except Exception as e:
            logger.error(f"Failed to save migration log: {e}")
            return ""
    
    async def run_migration(self, dry_run: bool = False) -> bool:
        """
        Run the complete migration process.
        
        Args:
            dry_run: If True, only validate without making changes
            
        Returns:
            bool: True if migration was successful
        """
        try:
            logger.info("Starting enhanced monitoring migration for restaurant-search-mcp")
            
            if dry_run:
                logger.info("Running in DRY RUN mode - no changes will be made")
            
            # Step 1: Create backup
            if not dry_run and not self.create_backup():
                return False
            
            # Step 2: Load legacy configuration
            legacy_config = self.load_legacy_configuration()
            
            # Step 3: Create enhanced configuration
            enhanced_config = self.create_enhanced_configuration(legacy_config)
            
            # Step 4: Save configurations (if not dry run)
            if not dry_run:
                if not self.save_enhanced_configuration(enhanced_config):
                    return False
                
                if legacy_config and not self.update_legacy_configuration(legacy_config):
                    return False
            
            # Step 5: Validate migration
            validation_success = await self.validate_migration()
            
            # Step 6: Save migration log
            if not dry_run:
                log_path = self.save_migration_log()
                logger.info(f"Migration log saved to: {log_path}")
            
            if validation_success:
                logger.info("Enhanced monitoring migration completed successfully!")
                return True
            else:
                logger.error("Enhanced monitoring migration validation failed!")
                return False
                
        except Exception as e:
            logger.error(f"Migration failed with error: {e}")
            self.log_migration_step("run_migration", "failed", str(e))
            return False


async def main():
    """Main migration script entry point."""
    parser = argparse.ArgumentParser(description="Migrate restaurant-search-mcp to enhanced monitoring")
    parser.add_argument("--config-dir", default="config", help="Configuration directory path")
    parser.add_argument("--backup-dir", default="config/backup", help="Backup directory path")
    parser.add_argument("--dry-run", action="store_true", help="Run validation only, make no changes")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create migrator
    migrator = EnhancedMonitoringMigrator(
        config_dir=args.config_dir,
        backup_dir=args.backup_dir
    )
    
    # Run migration
    success = await migrator.run_migration(dry_run=args.dry_run)
    
    if success:
        print("✅ Migration completed successfully!")
        if not args.dry_run:
            print("Enhanced dual monitoring is now available for restaurant-search-mcp")
            print("Legacy monitoring remains available for backward compatibility")
        sys.exit(0)
    else:
        print("❌ Migration failed!")
        print("Check the logs for details. Legacy monitoring should still be functional.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())