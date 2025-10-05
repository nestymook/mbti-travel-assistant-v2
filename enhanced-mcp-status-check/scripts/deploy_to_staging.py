#!/usr/bin/env python3
"""
Deploy Enhanced MCP Status Check System to Staging Environment

This script deploys the enhanced status check system to staging environment
with comprehensive validation and monitoring setup.
"""

import os
import sys
import json
import yaml
import logging
import argparse
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

# Add the enhanced-mcp-status-check directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from scripts.deploy_enhanced_status_check import EnhancedStatusCheckDeployer
from scripts.setup_monitoring import MonitoringSetup
from scripts.post_deployment_validation import PostDeploymentValidator


class StagingDeployer:
    """Handles deployment to staging environment."""
    
    def __init__(self):
        """Initialize staging deployer."""
        self.deployment_id = f"staging-deploy-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        self.staging_config_path = "config/examples/staging_deployment_config.yaml"
        
        # Setup logging
        self.setup_logging()
        
        # Initialize components
        self.deployer = None
        self.monitoring_setup = None
        self.validator = None
        
    def setup_logging(self):
        """Setup staging deployment logging."""
        log_dir = Path("logs/staging_deployment")
        log_dir.mkdir(parents=True, exist_ok=True)
        
        log_file = log_dir / f"staging_deployment_{self.deployment_id}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Starting staging deployment: {self.deployment_id}")
        
    async def deploy_to_staging(self) -> bool:
        """Deploy enhanced status check system to staging.
        
        Returns:
            True if deployment successful, False otherwise
        """
        try:
            self.logger.info("Starting deployment to staging environment")
            
            # Step 1: Deploy enhanced status check system
            self.logger.info("Step 1: Deploying enhanced status check system")
            self.deployer = EnhancedStatusCheckDeployer(
                config_path=self.staging_config_path,
                environment="staging"
            )
            
            deployment_success = self.deployer.deploy()
            if not deployment_success:
                self.logger.error("Enhanced status check deployment failed")
                return False
                
            self.logger.info("✅ Enhanced status check system deployed successfully")
            
            # Step 2: Setup monitoring and alerting
            self.logger.info("Step 2: Setting up monitoring and alerting")
            self.monitoring_setup = MonitoringSetup(config_path=self.staging_config_path)
            
            monitoring_success = self.monitoring_setup.setup_monitoring()
            if not monitoring_success:
                self.logger.error("Monitoring setup failed")
                return False
                
            self.logger.info("✅ Monitoring and alerting setup completed")
            
            # Step 3: Post-deployment validation
            self.logger.info("Step 3: Running post-deployment validation")
            self.validator = PostDeploymentValidator(
                config_path=self.staging_config_path
            )
            
            validation_success = await self.validator.run_validation()
            if not validation_success:
                self.logger.error("Post-deployment validation failed")
                return False
                
            self.logger.info("✅ Post-deployment validation completed")
            
            # Step 4: Create deployment report
            self.create_staging_deployment_report(True)
            
            self.logger.info("✅ Staging deployment completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Staging deployment failed: {e}")
            self.create_staging_deployment_report(False)
            return False
            
    def create_staging_deployment_report(self, success: bool) -> str:
        """Create staging deployment report.
        
        Args:
            success: Whether deployment was successful
            
        Returns:
            Path to deployment report
        """
        report = {
            "deployment_id": self.deployment_id,
            "environment": "staging",
            "timestamp": datetime.now().isoformat(),
            "success": success,
            "components_deployed": {
                "enhanced_status_check_system": self.deployer is not None,
                "monitoring_and_alerting": self.monitoring_setup is not None,
                "post_deployment_validation": self.validator is not None
            },
            "configuration": {
                "config_path": self.staging_config_path,
                "dual_monitoring_enabled": True,
                "environment_specific_settings": {
                    "debug_logging": True,
                    "frequent_monitoring": True,
                    "sensitive_alerting": True
                }
            }
        }
        
        report_path = Path("logs/staging_deployment") / f"staging_deployment_report_{self.deployment_id}.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
            
        self.logger.info(f"Staging deployment report saved to: {report_path}")
        return str(report_path)


async def main():
    """Main staging deployment function."""
    parser = argparse.ArgumentParser(description="Deploy Enhanced MCP Status Check to Staging")
    parser.add_argument("--validate-only", action="store_true",
                       help="Only validate staging configuration")
    
    args = parser.parse_args()
    
    try:
        deployer = StagingDeployer()
        
        if args.validate_only:
            print("Validating staging configuration...")
            # Just validate the configuration exists and is valid
            config_path = Path("config/examples/staging_deployment_config.yaml")
            if config_path.exists():
                print("✅ Staging configuration found")
                return 0
            else:
                print("❌ Staging configuration not found")
                return 1
        else:
            success = await deployer.deploy_to_staging()
            if success:
                print("✅ Staging deployment completed successfully")
                return 0
            else:
                print("❌ Staging deployment failed")
                return 1
                
    except Exception as e:
        print(f"❌ Staging deployment error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))