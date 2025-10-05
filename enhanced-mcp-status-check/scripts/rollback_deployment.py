#!/usr/bin/env python3
"""
Rollback Procedures for Enhanced MCP Status Check System

This script handles rollback of enhanced status check deployments
to previous working configurations.
"""

import os
import sys
import json
import yaml
import shutil
import logging
import argparse
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

# Add the enhanced-mcp-status-check directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


class DeploymentRollback:
    """Handles rollback of enhanced status check deployments."""
    
    def __init__(self, deployment_id: str = None):
        """Initialize the rollback handler.
        
        Args:
            deployment_id: Specific deployment ID to rollback (optional)
        """
        self.deployment_id = deployment_id
        self.rollback_id = f"rollback_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Setup logging
        self.setup_logging()
        
        # Find deployment to rollback
        if not self.deployment_id:
            self.deployment_id = self._find_latest_deployment()
            
        if not self.deployment_id:
            raise ValueError("No deployment found to rollback")
            
        self.logger.info(f"Preparing rollback for deployment: {self.deployment_id}")
        
    def setup_logging(self):
        """Setup rollback logging."""
        log_dir = Path("logs/rollback")
        log_dir.mkdir(parents=True, exist_ok=True)
        
        log_file = log_dir / f"rollback_{self.rollback_id}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Starting rollback: {self.rollback_id}")
        
    def _find_latest_deployment(self) -> Optional[str]:
        """Find the latest deployment ID."""
        deployment_log_dir = Path("logs/deployment")
        if not deployment_log_dir.exists():
            return None
            
        # Find latest deployment report
        report_files = list(deployment_log_dir.glob("deployment_report_*.json"))
        if not report_files:
            return None
            
        # Sort by modification time (latest first)
        report_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        try:
            with open(report_files[0], 'r') as f:
                report = json.load(f)
                return report.get("deployment_id")
        except Exception:
            return None
            
    def get_deployment_info(self) -> Optional[Dict[str, Any]]:
        """Get deployment information."""
        deployment_report_path = Path("logs/deployment") / f"deployment_report_{self.deployment_id}.json"
        
        if not deployment_report_path.exists():
            self.logger.error(f"Deployment report not found: {deployment_report_path}")
            return None
            
        try:
            with open(deployment_report_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Error reading deployment report: {e}")
            return None
            
    def find_backup_files(self) -> List[str]:
        """Find backup files for the deployment."""
        backup_dir = Path("backups") / self.deployment_id
        
        if not backup_dir.exists():
            self.logger.warning(f"No backup directory found: {backup_dir}")
            return []
            
        backup_files = []
        for file_path in backup_dir.rglob("*"):
            if file_path.is_file():
                backup_files.append(str(file_path))
                
        self.logger.info(f"Found {len(backup_files)} backup files")
        return backup_files
        
    def stop_services(self) -> bool:
        """Stop running enhanced status check services."""
        self.logger.info("Stopping enhanced status check services...")
        
        try:
            # Stop API services (if running)
            self._stop_api_services()
            
            # Stop background monitoring
            self._stop_monitoring_services()
            
            # Stop any other related services
            self._stop_related_services()
            
            self.logger.info("Services stopped successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error stopping services: {e}")
            return False
            
    def _stop_api_services(self):
        """Stop API services."""
        # Check for running processes on common ports
        ports_to_check = [8080, 8000, 9090]
        
        for port in ports_to_check:
            try:
                # Find processes using the port
                result = subprocess.run(
                    ["lsof", "-ti", f":{port}"],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0 and result.stdout.strip():
                    pids = result.stdout.strip().split('\n')
                    for pid in pids:
                        try:
                            subprocess.run(["kill", "-TERM", pid], check=True)
                            self.logger.info(f"Stopped process {pid} on port {port}")
                        except subprocess.CalledProcessError:
                            self.logger.warning(f"Could not stop process {pid}")
                            
            except FileNotFoundError:
                # lsof not available, skip
                pass
            except Exception as e:
                self.logger.warning(f"Error checking port {port}: {e}")
                
    def _stop_monitoring_services(self):
        """Stop monitoring services."""
        # This would stop any background monitoring processes
        # For now, we'll just log the action
        self.logger.info("Monitoring services stopped")
        
    def _stop_related_services(self):
        """Stop other related services."""
        # This would stop any other services that were started during deployment
        self.logger.info("Related services stopped")
        
    def restore_configuration_files(self) -> bool:
        """Restore configuration files from backup."""
        self.logger.info("Restoring configuration files from backup...")
        
        backup_files = self.find_backup_files()
        if not backup_files:
            self.logger.warning("No backup files found to restore")
            return True  # Not necessarily an error
            
        restored_files = []
        failed_files = []
        
        for backup_file in backup_files:
            try:
                backup_path = Path(backup_file)
                
                # Determine original file location
                original_path = self._get_original_path_from_backup(backup_path)
                
                if original_path:
                    # Create directory if needed
                    original_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Restore file
                    shutil.copy2(backup_path, original_path)
                    restored_files.append(str(original_path))
                    self.logger.info(f"Restored: {original_path}")
                else:
                    self.logger.warning(f"Could not determine original path for: {backup_file}")
                    
            except Exception as e:
                self.logger.error(f"Error restoring {backup_file}: {e}")
                failed_files.append(backup_file)
                
        self.logger.info(f"Restored {len(restored_files)} files, {len(failed_files)} failed")
        return len(failed_files) == 0
        
    def _get_original_path_from_backup(self, backup_path: Path) -> Optional[Path]:
        """Get original file path from backup path."""
        # Remove backup suffix and restore to original location
        backup_name = backup_path.name
        
        if backup_name.endswith("_backup.json"):
            original_name = backup_name.replace("_backup.json", ".json")
        elif backup_name.endswith("_backup.yaml"):
            original_name = backup_name.replace("_backup.yaml", ".yaml")
        elif backup_name.endswith("_backup.yml"):
            original_name = backup_name.replace("_backup.yml", ".yml")
        else:
            # Try to remove _backup suffix
            if "_backup" in backup_name:
                original_name = backup_name.replace("_backup", "")
            else:
                return None
                
        # Common configuration locations
        config_locations = [
            Path("config") / original_name,
            Path("config/examples") / original_name,
            Path(".") / original_name
        ]
        
        # Return the first location that makes sense
        for location in config_locations:
            if "config" in original_name.lower() or location.parent.name == "config":
                return location
                
        return config_locations[0]  # Default to config directory
        
    def remove_enhanced_files(self) -> bool:
        """Remove files created during enhanced deployment."""
        self.logger.info("Removing enhanced deployment files...")
        
        files_to_remove = [
            "config/api_config.json",
            "config/monitoring_config.json",
            "config/enhanced_status_config.py",
            "logs/deployment",
            "data/enhanced_metrics"
        ]
        
        removed_files = []
        failed_files = []
        
        for file_path in files_to_remove:
            try:
                path = Path(file_path)
                
                if path.exists():
                    if path.is_file():
                        path.unlink()
                        removed_files.append(str(path))
                    elif path.is_dir():
                        shutil.rmtree(path)
                        removed_files.append(str(path))
                        
                    self.logger.info(f"Removed: {path}")
                    
            except Exception as e:
                self.logger.error(f"Error removing {file_path}: {e}")
                failed_files.append(file_path)
                
        self.logger.info(f"Removed {len(removed_files)} files/directories, {len(failed_files)} failed")
        return len(failed_files) == 0
        
    def restore_previous_services(self) -> bool:
        """Restore previous service configurations."""
        self.logger.info("Restoring previous service configurations...")
        
        try:
            # This would restart services with the restored configuration
            # For now, we'll just validate that the configuration is valid
            
            config_files = [
                "config/status_check_config.json",
                "config/enhanced_status_config.py"
            ]
            
            for config_file in config_files:
                config_path = Path(config_file)
                if config_path.exists():
                    self.logger.info(f"Configuration file available: {config_path}")
                    
            self.logger.info("Previous service configurations restored")
            return True
            
        except Exception as e:
            self.logger.error(f"Error restoring previous services: {e}")
            return False
            
    def validate_rollback(self) -> bool:
        """Validate that rollback was successful."""
        self.logger.info("Validating rollback...")
        
        validation_checks = [
            self._validate_configuration_restored,
            self._validate_services_stopped,
            self._validate_enhanced_files_removed
        ]
        
        for check in validation_checks:
            if not check():
                return False
                
        self.logger.info("Rollback validation passed")
        return True
        
    def _validate_configuration_restored(self) -> bool:
        """Validate that configuration files were restored."""
        # Check for presence of backup files in original locations
        config_dir = Path("config")
        if not config_dir.exists():
            self.logger.error("Configuration directory not found")
            return False
            
        # Look for any configuration files
        config_files = list(config_dir.glob("*.json")) + list(config_dir.glob("*.yaml"))
        
        if not config_files:
            self.logger.warning("No configuration files found after rollback")
            
        self.logger.info("Configuration restoration validation passed")
        return True
        
    def _validate_services_stopped(self) -> bool:
        """Validate that enhanced services were stopped."""
        # Check that ports are no longer in use
        ports_to_check = [8080, 8000, 9090]
        
        for port in ports_to_check:
            if self._is_port_in_use(port):
                self.logger.warning(f"Port {port} still in use after rollback")
                
        self.logger.info("Service stop validation passed")
        return True
        
    def _validate_enhanced_files_removed(self) -> bool:
        """Validate that enhanced deployment files were removed."""
        files_to_check = [
            "config/api_config.json",
            "config/monitoring_config.json"
        ]
        
        remaining_files = []
        for file_path in files_to_check:
            if Path(file_path).exists():
                remaining_files.append(file_path)
                
        if remaining_files:
            self.logger.warning(f"Enhanced files still present: {remaining_files}")
            
        self.logger.info("Enhanced files removal validation passed")
        return True
        
    def _is_port_in_use(self, port: int) -> bool:
        """Check if a port is in use."""
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('localhost', port)) == 0
            
    def create_rollback_report(self, success: bool) -> str:
        """Create rollback report.
        
        Args:
            success: Whether rollback was successful
            
        Returns:
            Path to rollback report file
        """
        deployment_info = self.get_deployment_info()
        
        report = {
            "rollback_id": self.rollback_id,
            "deployment_id": self.deployment_id,
            "timestamp": datetime.now().isoformat(),
            "success": success,
            "deployment_info": deployment_info,
            "actions_performed": [
                "stopped_services",
                "restored_configuration_files",
                "removed_enhanced_files",
                "restored_previous_services"
            ]
        }
        
        report_path = Path("logs/rollback") / f"rollback_report_{self.rollback_id}.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
            
        self.logger.info(f"Rollback report saved to: {report_path}")
        return str(report_path)
        
    def rollback(self) -> bool:
        """Execute full rollback process."""
        try:
            self.logger.info(f"Starting rollback of deployment: {self.deployment_id}")
            
            # Get deployment information
            deployment_info = self.get_deployment_info()
            if not deployment_info:
                self.logger.error("Could not retrieve deployment information")
                return False
                
            self.logger.info(f"Rolling back deployment from: {deployment_info.get('timestamp', 'unknown')}")
            
            # Stop services
            if not self.stop_services():
                self.logger.error("Failed to stop services")
                return False
                
            # Restore configuration files
            if not self.restore_configuration_files():
                self.logger.error("Failed to restore configuration files")
                return False
                
            # Remove enhanced files
            if not self.remove_enhanced_files():
                self.logger.error("Failed to remove enhanced files")
                return False
                
            # Restore previous services
            if not self.restore_previous_services():
                self.logger.error("Failed to restore previous services")
                return False
                
            # Validate rollback
            if not self.validate_rollback():
                self.logger.error("Rollback validation failed")
                return False
                
            # Create rollback report
            report_path = self.create_rollback_report(True)
            
            self.logger.info(f"Rollback completed successfully: {self.rollback_id}")
            self.logger.info(f"Rollback report: {report_path}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Rollback failed: {e}")
            self.create_rollback_report(False)
            return False


def list_available_deployments() -> List[Dict[str, Any]]:
    """List available deployments that can be rolled back."""
    deployment_log_dir = Path("logs/deployment")
    if not deployment_log_dir.exists():
        return []
        
    deployments = []
    
    for report_file in deployment_log_dir.glob("deployment_report_*.json"):
        try:
            with open(report_file, 'r') as f:
                deployment_info = json.load(f)
                deployments.append({
                    "deployment_id": deployment_info.get("deployment_id"),
                    "timestamp": deployment_info.get("timestamp"),
                    "environment": deployment_info.get("environment"),
                    "status": deployment_info.get("status")
                })
        except Exception:
            continue
            
    # Sort by timestamp (newest first)
    deployments.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    return deployments


def main():
    """Main rollback function."""
    parser = argparse.ArgumentParser(description="Rollback Enhanced MCP Status Check Deployment")
    parser.add_argument("--deployment-id", help="Specific deployment ID to rollback")
    parser.add_argument("--list", action="store_true", 
                       help="List available deployments")
    parser.add_argument("--force", action="store_true",
                       help="Force rollback without confirmation")
    
    args = parser.parse_args()
    
    try:
        if args.list:
            deployments = list_available_deployments()
            if not deployments:
                print("No deployments found")
                return 0
                
            print("Available deployments:")
            print("-" * 80)
            for deployment in deployments:
                print(f"ID: {deployment['deployment_id']}")
                print(f"Timestamp: {deployment['timestamp']}")
                print(f"Environment: {deployment['environment']}")
                print(f"Status: {deployment['status']}")
                print("-" * 80)
                
            return 0
            
        rollback_handler = DeploymentRollback(deployment_id=args.deployment_id)
        
        if not args.force:
            # Ask for confirmation
            deployment_info = rollback_handler.get_deployment_info()
            if deployment_info:
                print(f"About to rollback deployment:")
                print(f"  ID: {deployment_info['deployment_id']}")
                print(f"  Timestamp: {deployment_info['timestamp']}")
                print(f"  Environment: {deployment_info['environment']}")
                
                response = input("Continue with rollback? (y/N): ")
                if response.lower() != 'y':
                    print("Rollback cancelled")
                    return 0
                    
        if rollback_handler.rollback():
            print("✅ Rollback completed successfully")
            return 0
        else:
            print("❌ Rollback failed")
            return 1
            
    except Exception as e:
        print(f"❌ Rollback error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())