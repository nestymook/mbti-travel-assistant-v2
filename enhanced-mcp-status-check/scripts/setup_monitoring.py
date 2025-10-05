#!/usr/bin/env python3
"""
Monitoring and Alerting Setup for Enhanced MCP Status Check System

This script sets up comprehensive monitoring and alerting for the
enhanced status check system with dual monitoring capabilities.
"""

import os
import sys
import json
import yaml
import logging
import argparse
import smtplib
import requests
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Add the enhanced-mcp-status-check directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from services.dual_metrics_collector import DualMetricsCollector
# from models.metrics_models import DualHealthMetrics  # Not needed for setup


class MonitoringSetup:
    """Sets up monitoring and alerting for enhanced status check system."""
    
    def __init__(self, config_path: str = None):
        """Initialize monitoring setup.
        
        Args:
            config_path: Path to configuration file
        """
        self.config_path = config_path or "config/examples/production_config.yaml"
        self.setup_id = f"monitoring_setup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Setup logging
        self.setup_logging()
        
        # Load configuration
        self.config = self.load_configuration()
        
        # Initialize metrics collector
        self.metrics_collector = DualMetricsCollector()
        
        # Monitoring configuration
        self.monitoring_config = self.create_monitoring_config()
        
    def setup_logging(self):
        """Setup monitoring setup logging."""
        log_dir = Path("logs/monitoring")
        log_dir.mkdir(parents=True, exist_ok=True)
        
        log_file = log_dir / f"monitoring_setup_{self.setup_id}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Starting monitoring setup: {self.setup_id}")
        
    def load_configuration(self) -> Dict[str, Any]:
        """Load system configuration."""
        try:
            config_path = Path(self.config_path)
            
            with open(config_path, 'r') as f:
                if config_path.suffix.lower() in ['.yaml', '.yml']:
                    config = yaml.safe_load(f)
                else:
                    config = json.load(f)
                    
            self.logger.info("Configuration loaded successfully")
            return config
            
        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
            raise
            
    def create_monitoring_config(self) -> Dict[str, Any]:
        """Create monitoring configuration."""
        return {
            "metrics": {
                "enabled": True,
                "collection_interval": 60,  # seconds
                "retention_days": 30,
                "storage_path": "data/metrics",
                "aggregation_intervals": [300, 900, 3600],  # 5min, 15min, 1hour
                "export_formats": ["json", "prometheus"]
            },
            "alerts": {
                "enabled": True,
                "check_interval": 30,  # seconds
                "email_notifications": {
                    "enabled": False,
                    "smtp_server": "localhost",
                    "smtp_port": 587,
                    "username": "",
                    "password": "",
                    "from_address": "alerts@example.com",
                    "to_addresses": []
                },
                "webhook_notifications": {
                    "enabled": False,
                    "webhook_url": "",
                    "timeout": 10,
                    "retry_attempts": 3
                },
                "alert_rules": self.create_default_alert_rules()
            },
            "dashboards": {
                "enabled": True,
                "refresh_interval": 30,
                "data_retention": 24,  # hours
                "charts": [
                    "server_health_status",
                    "response_times",
                    "success_rates",
                    "error_rates",
                    "dual_monitoring_comparison"
                ]
            },
            "logging": {
                "level": "INFO",
                "file_rotation": True,
                "max_file_size": "10MB",
                "backup_count": 5,
                "log_to_file": True,
                "log_to_console": True
            }
        }
        
    def create_default_alert_rules(self) -> List[Dict[str, Any]]:
        """Create default alert rules."""
        return [
            {
                "name": "server_down",
                "description": "Server is completely down (both MCP and REST failed)",
                "condition": "overall_success == false AND mcp_success == false AND rest_success == false",
                "severity": "critical",
                "cooldown": 300,  # 5 minutes
                "enabled": True
            },
            {
                "name": "dual_monitoring_degraded",
                "description": "One monitoring method failed (degraded state)",
                "condition": "overall_success == true AND (mcp_success == false OR rest_success == false)",
                "severity": "warning",
                "cooldown": 600,  # 10 minutes
                "enabled": True
            },
            {
                "name": "high_response_time",
                "description": "Response time is too high",
                "condition": "combined_response_time_ms > 5000",
                "severity": "warning",
                "cooldown": 300,
                "enabled": True
            },
            {
                "name": "low_success_rate",
                "description": "Success rate dropped below threshold",
                "condition": "success_rate < 0.95",
                "severity": "warning",
                "cooldown": 900,  # 15 minutes
                "enabled": True
            },
            {
                "name": "mcp_tools_missing",
                "description": "Expected MCP tools are missing",
                "condition": "mcp_success == true AND missing_tools_count > 0",
                "severity": "warning",
                "cooldown": 1800,  # 30 minutes
                "enabled": True
            }
        ]
        
    def setup_metrics_collection(self) -> bool:
        """Setup metrics collection system."""
        self.logger.info("Setting up metrics collection...")
        
        try:
            # Create metrics storage directory
            metrics_dir = Path(self.monitoring_config["metrics"]["storage_path"])
            metrics_dir.mkdir(parents=True, exist_ok=True)
            
            # Create metrics configuration file
            metrics_config_path = Path("config/metrics_config.json")
            with open(metrics_config_path, 'w') as f:
                json.dump(self.monitoring_config["metrics"], f, indent=2)
                
            # Initialize metrics collector
            self.metrics_collector.configure(self.monitoring_config["metrics"])
            
            self.logger.info("Metrics collection setup completed")
            return True
            
        except Exception as e:
            self.logger.error(f"Metrics collection setup failed: {e}")
            return False
            
    def setup_alerting_system(self) -> bool:
        """Setup alerting system."""
        self.logger.info("Setting up alerting system...")
        
        try:
            # Create alerts configuration file
            alerts_config_path = Path("config/alerts_config.json")
            with open(alerts_config_path, 'w') as f:
                json.dump(self.monitoring_config["alerts"], f, indent=2)
                
            # Test email configuration if enabled
            if self.monitoring_config["alerts"]["email_notifications"]["enabled"]:
                if not self.test_email_configuration():
                    self.logger.warning("Email configuration test failed")
                    
            # Test webhook configuration if enabled
            if self.monitoring_config["alerts"]["webhook_notifications"]["enabled"]:
                if not self.test_webhook_configuration():
                    self.logger.warning("Webhook configuration test failed")
                    
            self.logger.info("Alerting system setup completed")
            return True
            
        except Exception as e:
            self.logger.error(f"Alerting system setup failed: {e}")
            return False
            
    def test_email_configuration(self) -> bool:
        """Test email notification configuration."""
        try:
            email_config = self.monitoring_config["alerts"]["email_notifications"]
            
            # Create test email
            msg = MIMEMultipart()
            msg['From'] = email_config["from_address"]
            msg['To'] = ", ".join(email_config["to_addresses"][:1])  # Test with first address only
            msg['Subject'] = "Enhanced MCP Status Check - Email Test"
            
            body = """
This is a test email from the Enhanced MCP Status Check monitoring system.

If you receive this email, the email notification system is configured correctly.

Setup ID: {setup_id}
Timestamp: {timestamp}
            """.format(
                setup_id=self.setup_id,
                timestamp=datetime.now().isoformat()
            )
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Connect to SMTP server
            server = smtplib.SMTP(email_config["smtp_server"], email_config["smtp_port"])
            
            if email_config["username"] and email_config["password"]:
                server.starttls()
                server.login(email_config["username"], email_config["password"])
                
            # Send test email
            server.send_message(msg)
            server.quit()
            
            self.logger.info("Email configuration test passed")
            return True
            
        except Exception as e:
            self.logger.error(f"Email configuration test failed: {e}")
            return False
            
    def test_webhook_configuration(self) -> bool:
        """Test webhook notification configuration."""
        try:
            webhook_config = self.monitoring_config["alerts"]["webhook_notifications"]
            
            # Create test payload
            test_payload = {
                "alert_type": "test",
                "message": "Enhanced MCP Status Check - Webhook Test",
                "setup_id": self.setup_id,
                "timestamp": datetime.now().isoformat(),
                "severity": "info"
            }
            
            # Send test webhook
            response = requests.post(
                webhook_config["webhook_url"],
                json=test_payload,
                timeout=webhook_config["timeout"]
            )
            
            if response.status_code == 200:
                self.logger.info("Webhook configuration test passed")
                return True
            else:
                self.logger.error(f"Webhook test failed with status code: {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"Webhook configuration test failed: {e}")
            return False
            
    def setup_dashboards(self) -> bool:
        """Setup monitoring dashboards."""
        self.logger.info("Setting up monitoring dashboards...")
        
        try:
            # Create dashboard configuration
            dashboard_config_path = Path("config/dashboard_config.json")
            with open(dashboard_config_path, 'w') as f:
                json.dump(self.monitoring_config["dashboards"], f, indent=2)
                
            # Create dashboard templates
            self.create_dashboard_templates()
            
            self.logger.info("Dashboard setup completed")
            return True
            
        except Exception as e:
            self.logger.error(f"Dashboard setup failed: {e}")
            return False
            
    def create_dashboard_templates(self):
        """Create dashboard templates."""
        templates_dir = Path("console/templates")
        templates_dir.mkdir(parents=True, exist_ok=True)
        
        # Server health status template
        health_template = {
            "title": "Server Health Status",
            "type": "status_grid",
            "refresh_interval": 30,
            "data_source": "dual_health_metrics",
            "columns": [
                {"field": "server_name", "title": "Server"},
                {"field": "overall_status", "title": "Status"},
                {"field": "mcp_success", "title": "MCP"},
                {"field": "rest_success", "title": "REST"},
                {"field": "combined_response_time_ms", "title": "Response Time (ms)"}
            ]
        }
        
        with open(templates_dir / "server_health_status.json", 'w') as f:
            json.dump(health_template, f, indent=2)
            
        # Response times chart template
        response_time_template = {
            "title": "Response Times",
            "type": "line_chart",
            "refresh_interval": 30,
            "data_source": "dual_health_metrics",
            "x_axis": "timestamp",
            "y_axes": [
                {"field": "mcp_response_time_ms", "label": "MCP Response Time"},
                {"field": "rest_response_time_ms", "label": "REST Response Time"},
                {"field": "combined_response_time_ms", "label": "Combined Response Time"}
            ]
        }
        
        with open(templates_dir / "response_times.json", 'w') as f:
            json.dump(response_time_template, f, indent=2)
            
    def setup_log_rotation(self) -> bool:
        """Setup log rotation."""
        self.logger.info("Setting up log rotation...")
        
        try:
            # Create logrotate configuration
            logrotate_config = """
# Enhanced MCP Status Check log rotation
/path/to/enhanced-mcp-status-check/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 644 user group
}

/path/to/enhanced-mcp-status-check/logs/*/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 user group
}
            """
            
            logrotate_path = Path("config/logrotate.conf")
            with open(logrotate_path, 'w') as f:
                f.write(logrotate_config)
                
            self.logger.info("Log rotation setup completed")
            return True
            
        except Exception as e:
            self.logger.error(f"Log rotation setup failed: {e}")
            return False
            
    def create_monitoring_scripts(self) -> bool:
        """Create monitoring helper scripts."""
        self.logger.info("Creating monitoring scripts...")
        
        try:
            scripts_dir = Path("scripts/monitoring")
            scripts_dir.mkdir(parents=True, exist_ok=True)
            
            # Create metrics collection script
            metrics_script = '''#!/usr/bin/env python3
"""
Metrics Collection Script for Enhanced MCP Status Check System
"""

import sys
import os
import asyncio
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.dual_metrics_collector import DualMetricsCollector
from config.config_loader import ConfigLoader

async def collect_metrics():
    """Collect and store metrics."""
    config_loader = ConfigLoader()
    config = config_loader.load_config("config/examples/production_config.yaml")
    
    collector = DualMetricsCollector()
    await collector.collect_all_metrics(config)

if __name__ == "__main__":
    asyncio.run(collect_metrics())
'''
            
            with open(scripts_dir / "collect_metrics.py", 'w') as f:
                f.write(metrics_script)
                
            # Make script executable
            os.chmod(scripts_dir / "collect_metrics.py", 0o755)
            
            # Create alert checking script
            alert_script = '''#!/usr/bin/env python3
"""
Alert Checking Script for Enhanced MCP Status Check System
"""

import sys
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from console.alert_manager import AlertManager

def check_alerts():
    """Check and process alerts."""
    alert_manager = AlertManager()
    alert_manager.check_all_alerts()

if __name__ == "__main__":
    check_alerts()
'''
            
            with open(scripts_dir / "check_alerts.py", 'w') as f:
                f.write(alert_script)
                
            os.chmod(scripts_dir / "check_alerts.py", 0o755)
            
            self.logger.info("Monitoring scripts created")
            return True
            
        except Exception as e:
            self.logger.error(f"Monitoring scripts creation failed: {e}")
            return False
            
    def setup_cron_jobs(self) -> bool:
        """Setup cron jobs for automated monitoring."""
        self.logger.info("Setting up cron jobs...")
        
        try:
            cron_config = """
# Enhanced MCP Status Check monitoring cron jobs

# Collect metrics every minute
* * * * * /usr/bin/python3 /path/to/enhanced-mcp-status-check/scripts/monitoring/collect_metrics.py

# Check alerts every 30 seconds (using sleep for sub-minute intervals)
* * * * * /usr/bin/python3 /path/to/enhanced-mcp-status-check/scripts/monitoring/check_alerts.py
* * * * * sleep 30; /usr/bin/python3 /path/to/enhanced-mcp-status-check/scripts/monitoring/check_alerts.py

# Daily cleanup of old metrics data
0 2 * * * find /path/to/enhanced-mcp-status-check/data/metrics -name "*.json" -mtime +30 -delete

# Weekly log rotation
0 3 * * 0 /usr/sbin/logrotate /path/to/enhanced-mcp-status-check/config/logrotate.conf
            """
            
            cron_path = Path("config/crontab.txt")
            with open(cron_path, 'w') as f:
                f.write(cron_config)
                
            self.logger.info("Cron jobs configuration created")
            self.logger.info(f"To install cron jobs, run: crontab {cron_path}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Cron jobs setup failed: {e}")
            return False
            
    def create_monitoring_report(self, success: bool) -> str:
        """Create monitoring setup report.
        
        Args:
            success: Whether setup was successful
            
        Returns:
            Path to monitoring setup report
        """
        report = {
            "setup_id": self.setup_id,
            "timestamp": datetime.now().isoformat(),
            "success": success,
            "configuration": self.monitoring_config,
            "components_setup": {
                "metrics_collection": True,
                "alerting_system": True,
                "dashboards": True,
                "log_rotation": True,
                "monitoring_scripts": True,
                "cron_jobs": True
            }
        }
        
        report_path = Path("logs/monitoring") / f"monitoring_setup_report_{self.setup_id}.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
            
        self.logger.info(f"Monitoring setup report saved to: {report_path}")
        return str(report_path)
        
    def setup_monitoring(self) -> bool:
        """Execute full monitoring setup."""
        try:
            self.logger.info(f"Starting monitoring setup: {self.setup_id}")
            
            setup_steps = [
                ("Metrics Collection", self.setup_metrics_collection),
                ("Alerting System", self.setup_alerting_system),
                ("Dashboards", self.setup_dashboards),
                ("Log Rotation", self.setup_log_rotation),
                ("Monitoring Scripts", self.create_monitoring_scripts),
                ("Cron Jobs", self.setup_cron_jobs)
            ]
            
            overall_success = True
            
            for step_name, step_function in setup_steps:
                self.logger.info(f"Setting up: {step_name}")
                
                try:
                    step_success = step_function()
                    if step_success:
                        self.logger.info(f"✅ {step_name} setup completed")
                    else:
                        self.logger.error(f"❌ {step_name} setup failed")
                        overall_success = False
                        
                except Exception as e:
                    self.logger.error(f"❌ {step_name} setup error: {e}")
                    overall_success = False
                    
            # Create monitoring setup report
            report_path = self.create_monitoring_report(overall_success)
            
            if overall_success:
                self.logger.info(f"✅ Monitoring setup completed successfully: {self.setup_id}")
            else:
                self.logger.error(f"❌ Monitoring setup failed: {self.setup_id}")
                
            self.logger.info(f"Monitoring setup report: {report_path}")
            
            return overall_success
            
        except Exception as e:
            self.logger.error(f"Monitoring setup error: {e}")
            self.create_monitoring_report(False)
            return False


def main():
    """Main monitoring setup function."""
    parser = argparse.ArgumentParser(description="Setup Enhanced MCP Status Check Monitoring")
    parser.add_argument("--config", help="Configuration file path")
    parser.add_argument("--test-email", action="store_true",
                       help="Test email configuration only")
    parser.add_argument("--test-webhook", action="store_true",
                       help="Test webhook configuration only")
    
    args = parser.parse_args()
    
    try:
        monitoring_setup = MonitoringSetup(config_path=args.config)
        
        if args.test_email:
            print("Testing email configuration...")
            if monitoring_setup.test_email_configuration():
                print("✅ Email configuration test passed")
                return 0
            else:
                print("❌ Email configuration test failed")
                return 1
                
        elif args.test_webhook:
            print("Testing webhook configuration...")
            if monitoring_setup.test_webhook_configuration():
                print("✅ Webhook configuration test passed")
                return 0
            else:
                print("❌ Webhook configuration test failed")
                return 1
                
        else:
            print("Setting up monitoring and alerting...")
            if monitoring_setup.setup_monitoring():
                print("✅ Monitoring setup completed successfully")
                return 0
            else:
                print("❌ Monitoring setup failed")
                return 1
                
    except Exception as e:
        print(f"❌ Monitoring setup error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())