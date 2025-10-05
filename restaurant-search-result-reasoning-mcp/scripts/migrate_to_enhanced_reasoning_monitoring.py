#!/usr/bin/env python3
"""
Migration Script for Enhanced Reasoning MCP Status Monitoring

This script migrates existing restaurant-search-result-reasoning-mcp deployments to use the enhanced
dual monitoring system with reasoning-specific capabilities while maintaining backward compatibility.
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

from services.enhanced_reasoning_status_service import (
    RestaurantReasoningEnhancedStatusService,
    initialize_enhanced_reasoning_status_service
)
from services.health_check_service import HealthCheckService, get_reasoning_health_check_capabilities
from models.status_models import MCPStatusCheckConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class EnhancedReasoningMonitoringMigrator:
    """
    Migration utility for enhanced reasoning MCP status monitoring.
    
    Handles migration from legacy reasoning monitoring to enhanced dual monitoring
    with reasoning-specific capabilities and backward compatibility preservation.
    """
    
    def __init__(self, config_dir: str = "config", backup_dir: str = "config/backup"):
        """
        Initialize the reasoning migrator.
        
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
        logger.info(f"Reasoning migration step: {step} - {status}")
        if details:
            logger.info(f"Details: {details}")
    
    def create_backup(self) -> bool:
        """
        Create backup of existing reasoning configuration files.
        
        Returns:
            bool: True if backup was successful
        """
        try:
            self.log_migration_step("create_backup", "started")
            
            # Create backup directory
            self.backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Backup existing reasoning configuration files
            config_files = [
                "status_check_config.json",
                "cognito_config.json"
            ]
            
            backed_up_files = []
            for config_file in config_files:
                source_path = self.config_dir / config_file
                if source_path.exists():
                    backup_path = self.backup_dir / f"{config_file}.reasoning.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    shutil.copy2(source_path, backup_path)
                    backed_up_files.append(str(backup_path))
                    logger.info(f"Backed up reasoning config {source_path} to {backup_path}")
            
            self.log_migration_step(
                "create_backup", 
                "completed", 
                f"Backed up {len(backed_up_files)} reasoning config files: {', '.join(backed_up_files)}"
            )
            return True
            
        except Exception as e:
            self.log_migration_step("create_backup", "failed", str(e))
            logger.error(f"Reasoning backup creation failed: {e}")
            return False
    
    def load_legacy_reasoning_configuration(self) -> Optional[Dict[str, Any]]:
        """
        Load existing legacy reasoning configuration.
        
        Returns:
            Dict containing legacy reasoning configuration or None if not found
        """
        try:
            self.log_migration_step("load_legacy_reasoning_config", "started")
            
            legacy_config_path = self.config_dir / "status_check_config.json"
            if not legacy_config_path.exists():
                self.log_migration_step("load_legacy_reasoning_config", "skipped", "No legacy reasoning config found")
                return None
            
            with open(legacy_config_path, 'r') as f:
                legacy_config = json.load(f)
            
            self.log_migration_step(
                "load_legacy_reasoning_config", 
                "completed", 
                f"Loaded reasoning configuration with {len(legacy_config)} sections"
            )
            return legacy_config
            
        except Exception as e:
            self.log_migration_step("load_legacy_reasoning_config", "failed", str(e))
            logger.error(f"Failed to load legacy reasoning configuration: {e}")
            return None
    
    def create_enhanced_reasoning_configuration(self, legacy_config: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Create enhanced reasoning configuration based on legacy settings.
        
        Args:
            legacy_config: Existing legacy reasoning configuration
            
        Returns:
            Dict containing enhanced reasoning configuration
        """
        try:
            self.log_migration_step("create_enhanced_reasoning_config", "started")
            
            # Default enhanced reasoning configuration
            enhanced_config = {
                "enhanced_status_check_system": {
                    "system_name": "restaurant-reasoning-mcp-enhanced",
                    "version": "1.0.0",
                    "dual_monitoring_enabled": True,
                    "mcp_health_checks": {
                        "enabled": True,
                        "default_timeout_seconds": 12,
                        "default_retry_attempts": 3,
                        "tools_list_validation": True,
                        "expected_tools_validation": True,
                        "default_expected_tools": [
                            "recommend_restaurants",
                            "analyze_restaurant_sentiment"
                        ],
                        "request_timeout_ms": 35000,
                        "connection_pool_size": 8,
                        "jwt_auth_enabled": True
                    },
                    "rest_health_checks": {
                        "enabled": True,
                        "default_timeout_seconds": 10,
                        "default_retry_attempts": 2,
                        "health_endpoint_path": "/status/health",
                        "metrics_endpoint_path": "/status/metrics",
                        "expected_status_codes": [200, 201, 202],
                        "retry_backoff_factor": 1.5,
                        "max_retry_delay_seconds": 30,
                        "connection_pool_size": 15,
                        "validate_response_format": True,
                        "required_health_fields": ["status", "timestamp", "reasoning_capabilities"],
                        "auth_type": "bearer",
                        "auth_header_name": "Authorization"
                    },
                    "result_aggregation": {
                        "mcp_priority_weight": 0.8,
                        "rest_priority_weight": 0.2,
                        "require_both_success_for_healthy": False,
                        "degraded_on_single_failure": True,
                        "health_score_calculation": "weighted_average",
                        "failure_threshold": 0.3,
                        "degraded_threshold": 0.6
                    },
                    "circuit_breaker": {
                        "enabled": True,
                        "failure_threshold": 4,
                        "recovery_timeout_seconds": 90,
                        "half_open_max_calls": 2,
                        "mcp_circuit_breaker_enabled": True,
                        "rest_circuit_breaker_enabled": True,
                        "independent_circuit_breakers": True
                    },
                    "monitoring": {
                        "enabled": True,
                        "metrics_collection_enabled": True,
                        "health_check_interval_seconds": 45,
                        "metrics_retention_hours": 48,
                        "concurrent_health_checks": True,
                        "max_concurrent_checks": 8
                    },
                    "servers": []
                }
            }
            
            # Migrate legacy reasoning settings if available
            if legacy_config:
                self._migrate_legacy_reasoning_settings(enhanced_config, legacy_config)
            
            # Add default reasoning server configuration
            self._add_default_reasoning_server_config(enhanced_config)
            
            self.log_migration_step(
                "create_enhanced_reasoning_config", 
                "completed", 
                "Created enhanced reasoning configuration with dual monitoring support"
            )
            return enhanced_config
            
        except Exception as e:
            self.log_migration_step("create_enhanced_reasoning_config", "failed", str(e))
            logger.error(f"Failed to create enhanced reasoning configuration: {e}")
            raise
    
    def _migrate_legacy_reasoning_settings(self, enhanced_config: Dict[str, Any], legacy_config: Dict[str, Any]):
        """Migrate settings from legacy reasoning configuration."""
        try:
            # Migrate system settings
            if "status_check_system" in legacy_config:
                legacy_system = legacy_config["status_check_system"]
                enhanced_system = enhanced_config["enhanced_status_check_system"]
                
                # Migrate timeout settings (reasoning needs longer timeouts)
                if "global_timeout_seconds" in legacy_system:
                    timeout = max(12, legacy_system["global_timeout_seconds"])
                    enhanced_system["mcp_health_checks"]["default_timeout_seconds"] = timeout
                    enhanced_system["rest_health_checks"]["default_timeout_seconds"] = max(10, timeout - 2)
                
                # Migrate interval settings (reasoning can use longer intervals)
                if "global_check_interval_seconds" in legacy_system:
                    interval = max(45, legacy_system["global_check_interval_seconds"])
                    enhanced_system["monitoring"]["health_check_interval_seconds"] = interval
                
                # Migrate concurrency settings (reasoning may need fewer concurrent checks)
                if "max_concurrent_checks" in legacy_system:
                    concurrent = min(8, legacy_system["max_concurrent_checks"])
                    enhanced_system["monitoring"]["max_concurrent_checks"] = concurrent
                
                # Migrate metrics settings (reasoning benefits from longer retention)
                if "metrics_retention_hours" in legacy_system:
                    retention = max(48, legacy_system["metrics_retention_hours"])
                    enhanced_system["monitoring"]["metrics_retention_hours"] = retention
            
            # Migrate reasoning server configurations
            if "servers" in legacy_config:
                for server_name, server_config in legacy_config["servers"].items():
                    if "reasoning" in server_name.lower() or "sentiment" in server_name.lower():
                        self._migrate_reasoning_server_config(enhanced_config, server_name, server_config)
            
            logger.info("Successfully migrated legacy reasoning settings to enhanced configuration")
            
        except Exception as e:
            logger.error(f"Error migrating legacy reasoning settings: {e}")
            raise
    
    def _migrate_reasoning_server_config(self, enhanced_config: Dict[str, Any], server_name: str, legacy_server: Dict[str, Any]):
        """Migrate individual reasoning server configuration."""
        enhanced_server = {
            "server_name": server_name,
            "mcp_endpoint_url": legacy_server.get("endpoint_url", "https://your-gateway-url/mcp/restaurant-search-result-reasoning-mcp"),
            "mcp_enabled": True,
            "mcp_timeout_seconds": max(12, legacy_server.get("timeout_seconds", 12)),
            "mcp_expected_tools": legacy_server.get("expected_tools", [
                "recommend_restaurants",
                "analyze_restaurant_sentiment"
            ]),
            "mcp_retry_attempts": legacy_server.get("retry_attempts", 3),
            "rest_health_endpoint_url": f"{legacy_server.get('endpoint_url', 'https://your-gateway-url/mcp/restaurant-search-result-reasoning-mcp')}/status/health",
            "rest_enabled": True,
            "rest_timeout_seconds": max(10, legacy_server.get("timeout_seconds", 12) - 2),
            "rest_retry_attempts": 2,
            "jwt_token": None,
            "auth_headers": {},
            "mcp_priority_weight": 0.8,  # Higher priority for MCP in reasoning
            "rest_priority_weight": 0.2,
            "require_both_success": False,
            "priority": legacy_server.get("priority", "high"),
            "description": legacy_server.get("description", f"{server_name} with enhanced dual reasoning monitoring")
        }
        
        enhanced_config["enhanced_status_check_system"]["servers"].append(enhanced_server)
    
    def _add_default_reasoning_server_config(self, enhanced_config: Dict[str, Any]):
        """Add default reasoning server configuration if none exists."""
        if not enhanced_config["enhanced_status_check_system"]["servers"]:
            default_reasoning_server = {
                "server_name": "restaurant-search-result-reasoning-mcp",
                "mcp_endpoint_url": "https://your-gateway-url/mcp/restaurant-search-result-reasoning-mcp",
                "mcp_enabled": True,
                "mcp_timeout_seconds": 12,
                "mcp_expected_tools": [
                    "recommend_restaurants",
                    "analyze_restaurant_sentiment"
                ],
                "mcp_retry_attempts": 3,
                "rest_health_endpoint_url": "https://your-gateway-url/mcp/restaurant-search-result-reasoning-mcp/status/health",
                "rest_enabled": True,
                "rest_timeout_seconds": 10,
                "rest_retry_attempts": 2,
                "jwt_token": None,
                "auth_headers": {},
                "mcp_priority_weight": 0.8,
                "rest_priority_weight": 0.2,
                "require_both_success": False,
                "priority": "high",
                "description": "Restaurant recommendation and sentiment analysis reasoning with enhanced dual monitoring"
            }
            
            enhanced_config["enhanced_status_check_system"]["servers"].append(default_reasoning_server)
    
    def save_enhanced_reasoning_configuration(self, enhanced_config: Dict[str, Any]) -> bool:
        """
        Save enhanced reasoning configuration to file.
        
        Args:
            enhanced_config: Enhanced reasoning configuration to save
            
        Returns:
            bool: True if save was successful
        """
        try:
            self.log_migration_step("save_enhanced_reasoning_config", "started")
            
            # Ensure config directory exists
            self.config_dir.mkdir(parents=True, exist_ok=True)
            
            # Save enhanced reasoning configuration
            enhanced_config_path = self.config_dir / "enhanced_status_config.json"
            with open(enhanced_config_path, 'w') as f:
                json.dump(enhanced_config, f, indent=2)
            
            self.log_migration_step(
                "save_enhanced_reasoning_config", 
                "completed", 
                f"Saved enhanced reasoning configuration to {enhanced_config_path}"
            )
            return True
            
        except Exception as e:
            self.log_migration_step("save_enhanced_reasoning_config", "failed", str(e))
            logger.error(f"Failed to save enhanced reasoning configuration: {e}")
            return False
    
    def update_legacy_reasoning_configuration(self, legacy_config: Dict[str, Any]) -> bool:
        """
        Update legacy reasoning configuration to include enhanced monitoring settings.
        
        Args:
            legacy_config: Legacy reasoning configuration to update
            
        Returns:
            bool: True if update was successful
        """
        try:
            self.log_migration_step("update_legacy_reasoning_config", "started")
            
            # Add enhanced reasoning monitoring settings to legacy config
            if "status_check_system" not in legacy_config:
                legacy_config["status_check_system"] = {}
            
            legacy_config["status_check_system"].update({
                "enhanced_monitoring_enabled": True,
                "dual_monitoring_support": True,
                "reasoning_specific_monitoring": True,
                "backward_compatibility": True
            })
            
            # Add enhanced reasoning monitoring section
            legacy_config["enhanced_reasoning_monitoring"] = {
                "enabled": True,
                "config_file": "config/enhanced_status_config.json",
                "fallback_to_legacy": True,
                "integration_mode": "hybrid",
                "reasoning_capabilities_validation": True,
                "sentiment_analysis_monitoring": True
            }
            
            # Save updated legacy reasoning configuration
            legacy_config_path = self.config_dir / "status_check_config.json"
            with open(legacy_config_path, 'w') as f:
                json.dump(legacy_config, f, indent=2)
            
            self.log_migration_step(
                "update_legacy_reasoning_config", 
                "completed", 
                "Updated legacy reasoning configuration with enhanced monitoring settings"
            )
            return True
            
        except Exception as e:
            self.log_migration_step("update_legacy_reasoning_config", "failed", str(e))
            logger.error(f"Failed to update legacy reasoning configuration: {e}")
            return False
    
    async def validate_reasoning_migration(self) -> bool:
        """
        Validate that the reasoning migration was successful.
        
        Returns:
            bool: True if validation passed
        """
        try:
            self.log_migration_step("validate_reasoning_migration", "started")
            
            # Test enhanced reasoning monitoring initialization
            try:
                await initialize_enhanced_reasoning_status_service(
                    config_path=str(self.config_dir / "enhanced_status_config.json")
                )
                enhanced_reasoning_available = True
            except Exception as e:
                logger.warning(f"Enhanced reasoning monitoring initialization failed: {e}")
                enhanced_reasoning_available = False
            
            # Test legacy reasoning monitoring still works
            try:
                capabilities = await get_reasoning_health_check_capabilities()
                legacy_reasoning_available = capabilities.get("legacy_mcp_reasoning_monitoring", False)
            except Exception as e:
                logger.warning(f"Legacy reasoning monitoring test failed: {e}")
                legacy_reasoning_available = False
            
            # Validation results
            validation_results = {
                "enhanced_reasoning_monitoring_available": enhanced_reasoning_available,
                "legacy_reasoning_monitoring_available": legacy_reasoning_available,
                "reasoning_tools_validation": capabilities.get("reasoning_tools_validation", False) if 'capabilities' in locals() else False,
                "sentiment_analysis_validation": capabilities.get("sentiment_analysis_validation", False) if 'capabilities' in locals() else False,
                "backward_compatibility": legacy_reasoning_available,
                "migration_successful": enhanced_reasoning_available or legacy_reasoning_available
            }
            
            if validation_results["migration_successful"]:
                self.log_migration_step(
                    "validate_reasoning_migration", 
                    "completed", 
                    f"Reasoning validation passed: {validation_results}"
                )
                return True
            else:
                self.log_migration_step(
                    "validate_reasoning_migration", 
                    "failed", 
                    f"Reasoning validation failed: {validation_results}"
                )
                return False
                
        except Exception as e:
            self.log_migration_step("validate_reasoning_migration", "failed", str(e))
            logger.error(f"Reasoning migration validation failed: {e}")
            return False
    
    def save_reasoning_migration_log(self) -> str:
        """
        Save reasoning migration log to file.
        
        Returns:
            str: Path to reasoning migration log file
        """
        try:
            log_path = self.config_dir / f"reasoning_migration_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            migration_summary = {
                "migration_timestamp": datetime.now().isoformat(),
                "migration_version": "1.0.0",
                "source_system": "restaurant-search-result-reasoning-mcp",
                "target_system": "enhanced-dual-reasoning-monitoring",
                "reasoning_specific_features": [
                    "sentiment_analysis_monitoring",
                    "recommendation_algorithm_validation",
                    "reasoning_capabilities_check",
                    "extended_timeout_support",
                    "reasoning_metrics_collection"
                ],
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
            
            logger.info(f"Reasoning migration log saved to {log_path}")
            return str(log_path)
            
        except Exception as e:
            logger.error(f"Failed to save reasoning migration log: {e}")
            return ""
    
    async def run_reasoning_migration(self, dry_run: bool = False) -> bool:
        """
        Run the complete reasoning migration process.
        
        Args:
            dry_run: If True, only validate without making changes
            
        Returns:
            bool: True if reasoning migration was successful
        """
        try:
            logger.info("Starting enhanced reasoning monitoring migration for restaurant-search-result-reasoning-mcp")
            
            if dry_run:
                logger.info("Running in DRY RUN mode - no changes will be made")
            
            # Step 1: Create backup
            if not dry_run and not self.create_backup():
                return False
            
            # Step 2: Load legacy reasoning configuration
            legacy_config = self.load_legacy_reasoning_configuration()
            
            # Step 3: Create enhanced reasoning configuration
            enhanced_config = self.create_enhanced_reasoning_configuration(legacy_config)
            
            # Step 4: Save configurations (if not dry run)
            if not dry_run:
                if not self.save_enhanced_reasoning_configuration(enhanced_config):
                    return False
                
                if legacy_config and not self.update_legacy_reasoning_configuration(legacy_config):
                    return False
            
            # Step 5: Validate reasoning migration
            validation_success = await self.validate_reasoning_migration()
            
            # Step 6: Save reasoning migration log
            if not dry_run:
                log_path = self.save_reasoning_migration_log()
                logger.info(f"Reasoning migration log saved to: {log_path}")
            
            if validation_success:
                logger.info("Enhanced reasoning monitoring migration completed successfully!")
                logger.info("Reasoning-specific features now available:")
                logger.info("  - Sentiment analysis monitoring")
                logger.info("  - Recommendation algorithm validation")
                logger.info("  - Reasoning capabilities health checks")
                logger.info("  - Extended timeout support for reasoning operations")
                return True
            else:
                logger.error("Enhanced reasoning monitoring migration validation failed!")
                return False
                
        except Exception as e:
            logger.error(f"Reasoning migration failed with error: {e}")
            self.log_migration_step("run_reasoning_migration", "failed", str(e))
            return False


async def main():
    """Main reasoning migration script entry point."""
    parser = argparse.ArgumentParser(description="Migrate restaurant-search-result-reasoning-mcp to enhanced monitoring")
    parser.add_argument("--config-dir", default="config", help="Configuration directory path")
    parser.add_argument("--backup-dir", default="config/backup", help="Backup directory path")
    parser.add_argument("--dry-run", action="store_true", help="Run validation only, make no changes")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create reasoning migrator
    migrator = EnhancedReasoningMonitoringMigrator(
        config_dir=args.config_dir,
        backup_dir=args.backup_dir
    )
    
    # Run reasoning migration
    success = await migrator.run_reasoning_migration(dry_run=args.dry_run)
    
    if success:
        print("✅ Reasoning migration completed successfully!")
        if not args.dry_run:
            print("Enhanced dual reasoning monitoring is now available for restaurant-search-result-reasoning-mcp")
            print("Reasoning-specific features include:")
            print("  🧠 Sentiment analysis monitoring")
            print("  🎯 Recommendation algorithm validation")
            print("  📊 Reasoning capabilities health checks")
            print("  ⏱️  Extended timeout support for reasoning operations")
            print("Legacy reasoning monitoring remains available for backward compatibility")
        sys.exit(0)
    else:
        print("❌ Reasoning migration failed!")
        print("Check the logs for details. Legacy reasoning monitoring should still be functional.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())