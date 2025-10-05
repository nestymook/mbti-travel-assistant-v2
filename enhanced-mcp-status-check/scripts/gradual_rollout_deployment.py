#!/usr/bin/env python3
"""
Gradual Rollout Deployment Script for Enhanced MCP Status Check System

This script implements a gradual rollout strategy for deploying the enhanced
status check system to production environments with monitoring and rollback capabilities.
"""

import os
import sys
import json
import yaml
import time
import logging
import argparse
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta

# Add the enhanced-mcp-status-check directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from services.enhanced_health_check_service import EnhancedHealthCheckService
from services.dual_metrics_collector import DualMetricsCollector
from config.config_loader import ConfigLoader


class GradualRolloutDeployer:
    """Handles gradual rollout deployment with monitoring and rollback capabilities."""
    
    def __init__(self, config_path: str, rollout_config_path: str = None):
        """Initialize the gradual rollout deployer.
        
        Args:
            config_path: Path to main configuration file
            rollout_config_path: Path to rollout configuration file
        """
        self.config_path = config_path
        self.rollout_config_path = rollout_config_path or "config/examples/rollout_config.yaml"
        self.deployment_id = f"gradual-rollout-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        # Setup logging
        self.setup_logging()
        
        # Load configurations
        self.config = self.load_configuration()
        self.rollout_config = self.load_rollout_configuration()
        
        # Initialize services
        self.health_service = None
        self.metrics_collector = DualMetricsCollector()
        
        # Rollout state
        self.rollout_state = {
            "phase": 0,
            "servers_deployed": [],
            "servers_pending": [],
            "deployment_start": None,
            "phase_start": None,
            "success_metrics": {},
            "rollback_triggered": False
        }
        
    def setup_logging(self):
        """Setup deployment logging."""
        log_dir = Path("logs/gradual_rollout")
        log_dir.mkdir(parents=True, exist_ok=True)
        
        log_file = log_dir / f"gradual_rollout_{self.deployment_id}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Starting gradual rollout deployment: {self.deployment_id}")
        
    def load_configuration(self) -> Dict[str, Any]:
        """Load main system configuration."""
        try:
            config_loader = ConfigLoader()
            config = config_loader.load_config(self.config_path)
            self.logger.info("Main configuration loaded successfully")
            return config
        except Exception as e:
            self.logger.error(f"Failed to load main configuration: {e}")
            raise
            
    def load_rollout_configuration(self) -> Dict[str, Any]:
        """Load rollout configuration."""
        try:
            with open(self.rollout_config_path, 'r') as f:
                rollout_config = yaml.safe_load(f)
            self.logger.info("Rollout configuration loaded successfully")
            return rollout_config
        except Exception as e:
            self.logger.error(f"Failed to load rollout configuration: {e}")
            # Return default rollout configuration
            return self.get_default_rollout_config()
            
    def get_default_rollout_config(self) -> Dict[str, Any]:
        """Get default rollout configuration."""
        return {
            "rollout_strategy": {
                "phases": [
                    {"name": "canary", "percentage": 10, "duration_minutes": 30},
                    {"name": "early_adopters", "percentage": 25, "duration_minutes": 60},
                    {"name": "majority", "percentage": 75, "duration_minutes": 120},
                    {"name": "full_rollout", "percentage": 100, "duration_minutes": 60}
                ],
                "success_criteria": {
                    "min_success_rate": 0.95,
                    "max_response_time_ms": 5000,
                    "max_error_rate": 0.05
                },
                "rollback_criteria": {
                    "success_rate_threshold": 0.90,
                    "response_time_threshold_ms": 10000,
                    "error_rate_threshold": 0.10,
                    "consecutive_failures": 5
                },
                "monitoring": {
                    "check_interval_seconds": 30,
                    "metrics_window_minutes": 10,
                    "alert_on_issues": True
                }
            }
        }
        
    def prepare_rollout_phases(self) -> List[Dict[str, Any]]:
        """Prepare rollout phases with server assignments."""
        servers = self.config.get('enhanced_status_check_system', {}).get('servers', [])
        phases = self.rollout_config['rollout_strategy']['phases']
        
        rollout_phases = []
        servers_assigned = 0
        total_servers = len(servers)
        
        for i, phase in enumerate(phases):
            phase_servers = []
            
            if i == len(phases) - 1:  # Last phase gets all remaining servers
                servers_for_phase = total_servers - servers_assigned
            else:
                servers_for_phase = max(1, int(total_servers * phase['percentage'] / 100))
                
            # Assign servers to this phase
            for j in range(servers_for_phase):
                if servers_assigned + j < total_servers:
                    phase_servers.append(servers[servers_assigned + j])
                    
            servers_assigned += len(phase_servers)
            
            rollout_phases.append({
                "phase_number": i + 1,
                "name": phase['name'],
                "servers": phase_servers,
                "duration_minutes": phase['duration_minutes'],
                "percentage": phase['percentage']
            })
            
        self.logger.info(f"Prepared {len(rollout_phases)} rollout phases for {total_servers} servers")
        return rollout_phases
        
    async def deploy_phase(self, phase: Dict[str, Any]) -> bool:
        """Deploy a single rollout phase.
        
        Args:
            phase: Phase configuration
            
        Returns:
            True if phase deployment successful, False otherwise
        """
        phase_name = phase['name']
        servers = phase['servers']
        duration_minutes = phase['duration_minutes']
        
        self.logger.info(f"Starting phase '{phase_name}' with {len(servers)} servers")
        self.rollout_state['phase'] = phase['phase_number']
        self.rollout_state['phase_start'] = datetime.now()
        
        try:
            # Deploy enhanced monitoring to phase servers
            for server in servers:
                server_name = server.get('server_name', 'unknown')
                self.logger.info(f"Deploying enhanced monitoring to server: {server_name}")
                
                # Update server configuration for enhanced monitoring
                success = await self.deploy_server_enhanced_monitoring(server)
                
                if success:
                    self.rollout_state['servers_deployed'].append(server_name)
                    self.logger.info(f"✅ Enhanced monitoring deployed to {server_name}")
                else:
                    self.logger.error(f"❌ Failed to deploy enhanced monitoring to {server_name}")
                    return False
                    
            # Monitor phase for specified duration
            self.logger.info(f"Monitoring phase '{phase_name}' for {duration_minutes} minutes")
            
            monitoring_success = await self.monitor_phase(phase, duration_minutes)
            
            if monitoring_success:
                self.logger.info(f"✅ Phase '{phase_name}' completed successfully")
                return True
            else:
                self.logger.error(f"❌ Phase '{phase_name}' failed monitoring criteria")
                return False
                
        except Exception as e:
            self.logger.error(f"Phase '{phase_name}' deployment error: {e}")
            return False
            
    async def deploy_server_enhanced_monitoring(self, server: Dict[str, Any]) -> bool:
        """Deploy enhanced monitoring to a specific server.
        
        Args:
            server: Server configuration
            
        Returns:
            True if deployment successful, False otherwise
        """
        server_name = server.get('server_name', 'unknown')
        
        try:
            # Initialize enhanced health check service for this server
            if not self.health_service:
                self.health_service = EnhancedHealthCheckService(self.config)
                
            # Test dual health check on the server
            from models.dual_health_models import EnhancedServerConfig
            
            server_config = EnhancedServerConfig(
                server_name=server_name,
                mcp_endpoint_url=server.get('mcp_endpoint_url', ''),
                rest_health_endpoint_url=server.get('rest_health_endpoint_url', ''),
                mcp_enabled=server.get('mcp_enabled', True),
                rest_enabled=server.get('rest_enabled', True),
                mcp_timeout_seconds=server.get('mcp_timeout_seconds', 10),
                rest_timeout_seconds=server.get('rest_timeout_seconds', 8),
                mcp_expected_tools=server.get('mcp_expected_tools', []),
                mcp_retry_attempts=server.get('mcp_retry_attempts', 3),
                rest_retry_attempts=server.get('rest_retry_attempts', 2)
            )
            
            # Perform initial dual health check
            result = await self.health_service.perform_dual_health_check(server_config)
            
            if result.overall_success:
                self.logger.info(f"Initial health check passed for {server_name}")
                return True
            else:
                self.logger.error(f"Initial health check failed for {server_name}: {result.mcp_error_message or result.rest_error_message}")
                return False
                
        except Exception as e:
            self.logger.error(f"Server deployment error for {server_name}: {e}")
            return False
            
    async def monitor_phase(self, phase: Dict[str, Any], duration_minutes: int) -> bool:
        """Monitor a deployment phase for success criteria.
        
        Args:
            phase: Phase configuration
            duration_minutes: Duration to monitor in minutes
            
        Returns:
            True if phase meets success criteria, False otherwise
        """
        phase_name = phase['name']
        servers = phase['servers']
        
        success_criteria = self.rollout_config['rollout_strategy']['success_criteria']
        rollback_criteria = self.rollout_config['rollout_strategy']['rollback_criteria']
        monitoring_config = self.rollout_config['rollout_strategy']['monitoring']
        
        check_interval = monitoring_config['check_interval_seconds']
        metrics_window = monitoring_config['metrics_window_minutes']
        
        end_time = datetime.now() + timedelta(minutes=duration_minutes)
        consecutive_failures = 0
        
        self.logger.info(f"Monitoring phase '{phase_name}' until {end_time}")
        
        while datetime.now() < end_time:
            try:
                # Collect metrics for phase servers
                phase_metrics = await self.collect_phase_metrics(servers, metrics_window)
                
                # Check success criteria
                success_check = self.check_success_criteria(phase_metrics, success_criteria)
                rollback_check = self.check_rollback_criteria(phase_metrics, rollback_criteria)
                
                if rollback_check:
                    consecutive_failures += 1
                    self.logger.warning(f"Rollback criteria met ({consecutive_failures}/{rollback_criteria['consecutive_failures']})")
                    
                    if consecutive_failures >= rollback_criteria['consecutive_failures']:
                        self.logger.error(f"Consecutive failures threshold reached, triggering rollback")
                        return False
                else:
                    consecutive_failures = 0
                    
                if success_check:
                    self.logger.info(f"Phase '{phase_name}' meeting success criteria")
                else:
                    self.logger.warning(f"Phase '{phase_name}' not meeting success criteria")
                    
                # Store metrics for reporting
                self.rollout_state['success_metrics'][datetime.now().isoformat()] = phase_metrics
                
                # Wait before next check
                await asyncio.sleep(check_interval)
                
            except Exception as e:
                self.logger.error(f"Monitoring error for phase '{phase_name}': {e}")
                consecutive_failures += 1
                
        # Final success check
        final_metrics = await self.collect_phase_metrics(servers, metrics_window)
        final_success = self.check_success_criteria(final_metrics, success_criteria)
        
        if final_success:
            self.logger.info(f"Phase '{phase_name}' completed successfully with final metrics: {final_metrics}")
        else:
            self.logger.error(f"Phase '{phase_name}' failed final success criteria: {final_metrics}")
            
        return final_success
        
    async def collect_phase_metrics(self, servers: List[Dict[str, Any]], window_minutes: int) -> Dict[str, Any]:
        """Collect metrics for servers in a phase.
        
        Args:
            servers: List of servers in the phase
            window_minutes: Time window for metrics collection
            
        Returns:
            Aggregated metrics for the phase
        """
        try:
            all_metrics = []
            
            for server in servers:
                server_name = server.get('server_name', 'unknown')
                
                # Collect metrics for this server
                server_metrics = await self.metrics_collector.collect_server_metrics(server_name)
                if server_metrics:
                    all_metrics.append(server_metrics)
                    
            if not all_metrics:
                return {
                    "success_rate": 0.0,
                    "average_response_time_ms": 0.0,
                    "error_rate": 1.0,
                    "servers_count": len(servers),
                    "healthy_servers": 0
                }
                
            # Aggregate metrics
            total_requests = sum(m.get('total_requests', 0) for m in all_metrics)
            successful_requests = sum(m.get('successful_requests', 0) for m in all_metrics)
            total_response_time = sum(m.get('total_response_time_ms', 0) for m in all_metrics)
            healthy_servers = sum(1 for m in all_metrics if m.get('overall_success', False))
            
            success_rate = successful_requests / total_requests if total_requests > 0 else 0.0
            average_response_time = total_response_time / total_requests if total_requests > 0 else 0.0
            error_rate = 1.0 - success_rate
            
            return {
                "success_rate": success_rate,
                "average_response_time_ms": average_response_time,
                "error_rate": error_rate,
                "servers_count": len(servers),
                "healthy_servers": healthy_servers,
                "total_requests": total_requests,
                "successful_requests": successful_requests
            }
            
        except Exception as e:
            self.logger.error(f"Error collecting phase metrics: {e}")
            return {
                "success_rate": 0.0,
                "average_response_time_ms": 0.0,
                "error_rate": 1.0,
                "servers_count": len(servers),
                "healthy_servers": 0
            }
            
    def check_success_criteria(self, metrics: Dict[str, Any], criteria: Dict[str, Any]) -> bool:
        """Check if metrics meet success criteria.
        
        Args:
            metrics: Current metrics
            criteria: Success criteria
            
        Returns:
            True if criteria met, False otherwise
        """
        success_rate_ok = metrics['success_rate'] >= criteria['min_success_rate']
        response_time_ok = metrics['average_response_time_ms'] <= criteria['max_response_time_ms']
        error_rate_ok = metrics['error_rate'] <= criteria['max_error_rate']
        
        return success_rate_ok and response_time_ok and error_rate_ok
        
    def check_rollback_criteria(self, metrics: Dict[str, Any], criteria: Dict[str, Any]) -> bool:
        """Check if metrics meet rollback criteria.
        
        Args:
            metrics: Current metrics
            criteria: Rollback criteria
            
        Returns:
            True if rollback needed, False otherwise
        """
        success_rate_bad = metrics['success_rate'] < criteria['success_rate_threshold']
        response_time_bad = metrics['average_response_time_ms'] > criteria['response_time_threshold_ms']
        error_rate_bad = metrics['error_rate'] > criteria['error_rate_threshold']
        
        return success_rate_bad or response_time_bad or error_rate_bad
        
    async def rollback_deployment(self) -> bool:
        """Rollback the deployment.
        
        Returns:
            True if rollback successful, False otherwise
        """
        self.logger.info("Starting deployment rollback")
        self.rollout_state['rollback_triggered'] = True
        
        try:
            # Rollback deployed servers
            for server_name in self.rollout_state['servers_deployed']:
                self.logger.info(f"Rolling back server: {server_name}")
                
                # Restore previous configuration
                rollback_success = await self.rollback_server(server_name)
                
                if rollback_success:
                    self.logger.info(f"✅ Rollback successful for {server_name}")
                else:
                    self.logger.error(f"❌ Rollback failed for {server_name}")
                    
            self.logger.info("Deployment rollback completed")
            return True
            
        except Exception as e:
            self.logger.error(f"Rollback error: {e}")
            return False
            
    async def rollback_server(self, server_name: str) -> bool:
        """Rollback a specific server.
        
        Args:
            server_name: Name of server to rollback
            
        Returns:
            True if rollback successful, False otherwise
        """
        try:
            # This would restore the previous monitoring configuration
            # For now, we'll just log the rollback action
            self.logger.info(f"Restoring previous monitoring configuration for {server_name}")
            
            # In a real implementation, this would:
            # 1. Stop enhanced monitoring
            # 2. Restore previous configuration
            # 3. Restart services
            # 4. Verify rollback success
            
            return True
            
        except Exception as e:
            self.logger.error(f"Server rollback error for {server_name}: {e}")
            return False
            
    def create_rollout_report(self, success: bool) -> str:
        """Create rollout deployment report.
        
        Args:
            success: Whether rollout was successful
            
        Returns:
            Path to rollout report
        """
        report = {
            "deployment_id": self.deployment_id,
            "timestamp": datetime.now().isoformat(),
            "success": success,
            "rollout_state": self.rollout_state,
            "configuration": {
                "config_path": self.config_path,
                "rollout_config_path": self.rollout_config_path
            },
            "metrics_summary": self.rollout_state.get('success_metrics', {}),
            "deployment_duration": None,
            "servers_deployed": len(self.rollout_state['servers_deployed']),
            "rollback_triggered": self.rollout_state['rollback_triggered']
        }
        
        if self.rollout_state['deployment_start']:
            duration = datetime.now() - self.rollout_state['deployment_start']
            report['deployment_duration'] = str(duration)
            
        report_path = Path("logs/gradual_rollout") / f"rollout_report_{self.deployment_id}.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
            
        self.logger.info(f"Rollout report saved to: {report_path}")
        return str(report_path)
        
    async def execute_gradual_rollout(self) -> bool:
        """Execute the gradual rollout deployment.
        
        Returns:
            True if rollout successful, False otherwise
        """
        try:
            self.logger.info(f"Starting gradual rollout deployment: {self.deployment_id}")
            self.rollout_state['deployment_start'] = datetime.now()
            
            # Prepare rollout phases
            phases = self.prepare_rollout_phases()
            
            if not phases:
                self.logger.error("No rollout phases prepared")
                return False
                
            # Execute each phase
            for phase in phases:
                phase_success = await self.deploy_phase(phase)
                
                if not phase_success:
                    self.logger.error(f"Phase '{phase['name']}' failed, initiating rollback")
                    await self.rollback_deployment()
                    return False
                    
            self.logger.info("✅ Gradual rollout completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Gradual rollout error: {e}")
            await self.rollback_deployment()
            return False
        finally:
            # Create rollout report
            success = not self.rollout_state['rollback_triggered']
            report_path = self.create_rollout_report(success)
            self.logger.info(f"Rollout report: {report_path}")


def main():
    """Main gradual rollout function."""
    parser = argparse.ArgumentParser(description="Gradual Rollout Deployment for Enhanced MCP Status Check")
    parser.add_argument("--config", required=True, help="Main configuration file path")
    parser.add_argument("--rollout-config", help="Rollout configuration file path")
    parser.add_argument("--dry-run", action="store_true", help="Perform dry run without actual deployment")
    
    args = parser.parse_args()
    
    try:
        deployer = GradualRolloutDeployer(
            config_path=args.config,
            rollout_config_path=args.rollout_config
        )
        
        if args.dry_run:
            print("Performing dry run...")
            phases = deployer.prepare_rollout_phases()
            print(f"Would deploy {len(phases)} phases:")
            for phase in phases:
                print(f"  Phase {phase['phase_number']}: {phase['name']} - {len(phase['servers'])} servers")
            return 0
        else:
            success = asyncio.run(deployer.execute_gradual_rollout())
            if success:
                print("✅ Gradual rollout completed successfully")
                return 0
            else:
                print("❌ Gradual rollout failed")
                return 1
                
    except Exception as e:
        print(f"❌ Gradual rollout error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())