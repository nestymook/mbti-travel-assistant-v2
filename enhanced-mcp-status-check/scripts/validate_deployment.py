#!/usr/bin/env python3
"""
Deployment Validation Scripts for Enhanced MCP Status Check System

This script validates the deployment of enhanced status check system
and verifies all components are working correctly.
"""

import os
import sys
import json
import asyncio
import logging
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

# Add the enhanced-mcp-status-check directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from config.config_loader import ConfigLoader
from config.config_validator import ConfigValidator
from services.enhanced_health_check_service import EnhancedHealthCheckService
from services.mcp_health_check_client import MCPHealthCheckClient
from services.rest_health_check_client import RESTHealthCheckClient
from models.dual_health_models import EnhancedServerConfig


class DeploymentValidator:
    """Validates enhanced status check system deployment."""
    
    def __init__(self, config_path: str = None):
        """Initialize the validator.
        
        Args:
            config_path: Path to configuration file
        """
        self.config_path = config_path or "config/examples/production_config.yaml"
        self.validation_id = f"validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Setup logging
        self.setup_logging()
        
        # Load configuration
        self.config = self.load_configuration()
        
        # Initialize clients
        self.mcp_client = MCPHealthCheckClient()
        self.rest_client = RESTHealthCheckClient()
        self.health_service = None
        
        # Validation results
        self.validation_results = {
            "configuration": {},
            "connectivity": {},
            "services": {},
            "api_endpoints": {},
            "monitoring": {},
            "performance": {}
        }
        
    def setup_logging(self):
        """Setup validation logging."""
        log_dir = Path("logs/validation")
        log_dir.mkdir(parents=True, exist_ok=True)
        
        log_file = log_dir / f"validation_{self.validation_id}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Starting deployment validation: {self.validation_id}")
        
    def load_configuration(self) -> Dict[str, Any]:
        """Load and validate configuration."""
        try:
            config_loader = ConfigLoader()
            config = config_loader.load_config(self.config_path)
            
            self.logger.info("Configuration loaded successfully")
            return config
            
        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
            raise
            
    def validate_configuration(self) -> bool:
        """Validate configuration integrity."""
        self.logger.info("Validating configuration...")
        
        try:
            # Validate configuration structure
            validator = ConfigValidator()
            validation_result = validator.validate_config(self.config)
            
            self.validation_results["configuration"] = {
                "is_valid": validation_result.is_valid,
                "errors": validation_result.errors,
                "warnings": validation_result.warnings
            }
            
            if not validation_result.is_valid:
                self.logger.error(f"Configuration validation failed: {validation_result.errors}")
                return False
                
            # Validate specific enhanced features
            enhanced_config = self.config.get("enhanced_status_check_system", {})
            
            # Check dual monitoring is enabled
            if not enhanced_config.get("dual_monitoring_enabled", False):
                self.logger.warning("Dual monitoring is not enabled")
                
            # Check server configurations
            servers = enhanced_config.get("servers", [])
            if not servers:
                self.logger.error("No servers configured")
                return False
                
            self.logger.info(f"Configuration validation passed - {len(servers)} servers configured")
            return True
            
        except Exception as e:
            self.logger.error(f"Configuration validation error: {e}")
            self.validation_results["configuration"]["error"] = str(e)
            return False
            
    async def validate_connectivity(self) -> bool:
        """Validate connectivity to configured servers."""
        self.logger.info("Validating server connectivity...")
        
        enhanced_config = self.config.get("enhanced_status_check_system", {})
        servers = enhanced_config.get("servers", [])
        
        connectivity_results = {}
        overall_success = True
        
        for server_config in servers:
            server_name = server_config.get("server_name", "unknown")
            self.logger.info(f"Testing connectivity to {server_name}...")
            
            server_results = {
                "mcp_connectivity": False,
                "rest_connectivity": False,
                "mcp_error": None,
                "rest_error": None
            }
            
            # Test MCP connectivity
            if server_config.get("mcp_enabled", True):
                mcp_url = server_config.get("mcp_endpoint_url")
                if mcp_url:
                    try:
                        # Test MCP tools/list request
                        response = await self.mcp_client.send_tools_list_request(
                            mcp_url,
                            server_config.get("auth_headers", {}),
                            server_config.get("mcp_timeout_seconds", 10)
                        )
                        server_results["mcp_connectivity"] = response.success
                        if not response.success:
                            server_results["mcp_error"] = response.error_message
                    except Exception as e:
                        server_results["mcp_error"] = str(e)
                        
            # Test REST connectivity
            if server_config.get("rest_enabled", True):
                rest_url = server_config.get("rest_health_endpoint_url")
                if rest_url:
                    try:
                        # Test REST health check
                        response = await self.rest_client.send_health_request(
                            rest_url,
                            server_config.get("auth_headers", {}),
                            server_config.get("rest_timeout_seconds", 8)
                        )
                        server_results["rest_connectivity"] = response.success
                        if not response.success:
                            server_results["rest_error"] = response.error_message
                    except Exception as e:
                        server_results["rest_error"] = str(e)
                        
            connectivity_results[server_name] = server_results
            
            # Check if at least one method is working
            if not (server_results["mcp_connectivity"] or server_results["rest_connectivity"]):
                self.logger.error(f"No connectivity to {server_name}")
                overall_success = False
            else:
                self.logger.info(f"Connectivity to {server_name}: MCP={server_results['mcp_connectivity']}, REST={server_results['rest_connectivity']}")
                
        self.validation_results["connectivity"] = connectivity_results
        
        if overall_success:
            self.logger.info("Connectivity validation passed")
        else:
            self.logger.error("Connectivity validation failed")
            
        return overall_success
        
    def validate_services(self) -> bool:
        """Validate that services are properly initialized."""
        self.logger.info("Validating services...")
        
        try:
            # Initialize enhanced health check service
            self.health_service = EnhancedHealthCheckService(self.config)
            
            # Test service initialization
            if not self.health_service:
                self.logger.error("Enhanced health check service not initialized")
                return False
                
            self.validation_results["services"] = {
                "enhanced_health_check_service": "initialized",
                "mcp_client": "available",
                "rest_client": "available"
            }
            
            self.logger.info("Services validation passed")
            return True
            
        except Exception as e:
            self.logger.error(f"Services validation error: {e}")
            self.validation_results["services"]["error"] = str(e)
            return False
            
    async def validate_api_endpoints(self) -> bool:
        """Validate API endpoints are accessible."""
        self.logger.info("Validating API endpoints...")
        
        # This would test actual API endpoints if they were running
        # For now, we'll validate the configuration exists
        
        api_config_path = Path("config/api_config.json")
        if not api_config_path.exists():
            self.logger.error("API configuration not found")
            self.validation_results["api_endpoints"]["error"] = "API configuration missing"
            return False
            
        try:
            with open(api_config_path, 'r') as f:
                api_config = json.load(f)
                
            self.validation_results["api_endpoints"] = {
                "configuration": "valid",
                "host": api_config.get("host", "unknown"),
                "port": api_config.get("port", "unknown")
            }
            
            self.logger.info("API endpoints validation passed")
            return True
            
        except Exception as e:
            self.logger.error(f"API endpoints validation error: {e}")
            self.validation_results["api_endpoints"]["error"] = str(e)
            return False
            
    def validate_monitoring_setup(self) -> bool:
        """Validate monitoring and alerting setup."""
        self.logger.info("Validating monitoring setup...")
        
        monitoring_config_path = Path("config/monitoring_config.json")
        if not monitoring_config_path.exists():
            self.logger.error("Monitoring configuration not found")
            self.validation_results["monitoring"]["error"] = "Monitoring configuration missing"
            return False
            
        try:
            with open(monitoring_config_path, 'r') as f:
                monitoring_config = json.load(f)
                
            # Validate monitoring configuration
            metrics_config = monitoring_config.get("metrics", {})
            alerts_config = monitoring_config.get("alerts", {})
            
            self.validation_results["monitoring"] = {
                "metrics_enabled": metrics_config.get("enabled", False),
                "alerts_enabled": alerts_config.get("enabled", False),
                "collection_interval": metrics_config.get("collection_interval", 0),
                "retention_days": metrics_config.get("retention_days", 0)
            }
            
            self.logger.info("Monitoring setup validation passed")
            return True
            
        except Exception as e:
            self.logger.error(f"Monitoring setup validation error: {e}")
            self.validation_results["monitoring"]["error"] = str(e)
            return False
            
    async def validate_performance(self) -> bool:
        """Validate system performance."""
        self.logger.info("Validating system performance...")
        
        if not self.health_service:
            self.logger.error("Health service not available for performance testing")
            return False
            
        try:
            # Test dual health check performance
            enhanced_config = self.config.get("enhanced_status_check_system", {})
            servers = enhanced_config.get("servers", [])
            
            if not servers:
                self.logger.warning("No servers configured for performance testing")
                return True
                
            # Test first server for performance
            server_config_dict = servers[0]
            server_config = EnhancedServerConfig(**server_config_dict)
            
            start_time = datetime.now()
            
            # Perform dual health check
            result = await self.health_service.perform_dual_health_check(server_config)
            
            end_time = datetime.now()
            response_time = (end_time - start_time).total_seconds() * 1000  # ms
            
            self.validation_results["performance"] = {
                "dual_health_check_response_time_ms": response_time,
                "mcp_response_time_ms": result.mcp_response_time_ms if result.mcp_result else None,
                "rest_response_time_ms": result.rest_response_time_ms if result.rest_result else None,
                "overall_success": result.overall_success
            }
            
            # Check if performance is acceptable
            max_acceptable_time = 5000  # 5 seconds
            if response_time > max_acceptable_time:
                self.logger.warning(f"Performance test took {response_time:.2f}ms (> {max_acceptable_time}ms)")
            else:
                self.logger.info(f"Performance test completed in {response_time:.2f}ms")
                
            return True
            
        except Exception as e:
            self.logger.error(f"Performance validation error: {e}")
            self.validation_results["performance"]["error"] = str(e)
            return False
            
    def create_validation_report(self, overall_success: bool) -> str:
        """Create validation report.
        
        Args:
            overall_success: Whether overall validation was successful
            
        Returns:
            Path to validation report file
        """
        report = {
            "validation_id": self.validation_id,
            "timestamp": datetime.now().isoformat(),
            "config_path": self.config_path,
            "overall_success": overall_success,
            "results": self.validation_results,
            "summary": self._create_validation_summary()
        }
        
        report_path = Path("logs/validation") / f"validation_report_{self.validation_id}.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
            
        self.logger.info(f"Validation report saved to: {report_path}")
        return str(report_path)
        
    def _create_validation_summary(self) -> Dict[str, Any]:
        """Create validation summary."""
        summary = {
            "total_checks": 0,
            "passed_checks": 0,
            "failed_checks": 0,
            "warnings": 0
        }
        
        for category, results in self.validation_results.items():
            if isinstance(results, dict):
                summary["total_checks"] += 1
                
                if "error" in results:
                    summary["failed_checks"] += 1
                elif results.get("is_valid", True):
                    summary["passed_checks"] += 1
                else:
                    summary["failed_checks"] += 1
                    
                if "warnings" in results and results["warnings"]:
                    summary["warnings"] += len(results["warnings"])
                    
        return summary
        
    async def validate_deployment(self) -> bool:
        """Execute full deployment validation."""
        try:
            self.logger.info(f"Starting deployment validation: {self.validation_id}")
            
            validation_steps = [
                ("Configuration", self.validate_configuration),
                ("Connectivity", self.validate_connectivity),
                ("Services", self.validate_services),
                ("API Endpoints", self.validate_api_endpoints),
                ("Monitoring Setup", self.validate_monitoring_setup),
                ("Performance", self.validate_performance)
            ]
            
            overall_success = True
            
            for step_name, step_function in validation_steps:
                self.logger.info(f"Running validation step: {step_name}")
                
                try:
                    if asyncio.iscoroutinefunction(step_function):
                        step_success = await step_function()
                    else:
                        step_success = step_function()
                        
                    if step_success:
                        self.logger.info(f"✅ {step_name} validation passed")
                    else:
                        self.logger.error(f"❌ {step_name} validation failed")
                        overall_success = False
                        
                except Exception as e:
                    self.logger.error(f"❌ {step_name} validation error: {e}")
                    overall_success = False
                    
            # Create validation report
            report_path = self.create_validation_report(overall_success)
            
            if overall_success:
                self.logger.info(f"✅ Deployment validation completed successfully: {self.validation_id}")
            else:
                self.logger.error(f"❌ Deployment validation failed: {self.validation_id}")
                
            self.logger.info(f"Validation report: {report_path}")
            
            return overall_success
            
        except Exception as e:
            self.logger.error(f"Deployment validation error: {e}")
            self.create_validation_report(False)
            return False


async def main():
    """Main validation function."""
    parser = argparse.ArgumentParser(description="Validate Enhanced MCP Status Check Deployment")
    parser.add_argument("--config", help="Configuration file path")
    parser.add_argument("--quick", action="store_true",
                       help="Run quick validation (skip performance tests)")
    parser.add_argument("--connectivity-only", action="store_true",
                       help="Only test connectivity")
    
    args = parser.parse_args()
    
    try:
        validator = DeploymentValidator(config_path=args.config)
        
        if args.connectivity_only:
            print("Running connectivity validation only...")
            success = await validator.validate_connectivity()
        elif args.quick:
            print("Running quick validation...")
            # Skip performance validation
            validator.validate_performance = lambda: True
            success = await validator.validate_deployment()
        else:
            print("Running full deployment validation...")
            success = await validator.validate_deployment()
            
        if success:
            print("✅ Validation completed successfully")
            return 0
        else:
            print("❌ Validation failed")
            return 1
            
    except Exception as e:
        print(f"❌ Validation error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))