#!/usr/bin/env python3
"""
Monitoring Setup Script

This script sets up comprehensive monitoring and observability for the
MBTI Travel Assistant MCP service, including CloudWatch integration,
health checks, and alerting.
"""

import asyncio
import logging
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

import boto3
from botocore.exceptions import ClientError, NoCredentialsError

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.cloudwatch_monitor import CloudWatchMonitor, AlarmConfiguration, MetricUnit
from services.health_check import HealthChecker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MonitoringSetup:
    """
    Sets up comprehensive monitoring and observability infrastructure.
    
    Configures CloudWatch dashboards, alarms, log groups, and health checks
    for the MBTI Travel Assistant MCP service.
    """
    
    def __init__(
        self,
        environment: str = "development",
        region: str = "us-east-1",
        agent_name: str = "mbti-travel-assistant-mcp"
    ):
        """
        Initialize monitoring setup.
        
        Args:
            environment: Environment name (development, staging, production)
            region: AWS region
            agent_name: Name of the agent/service
        """
        self.environment = environment
        self.region = region
        self.agent_name = agent_name
        self.namespace = "MBTI/TravelAssistant"
        
        # Initialize CloudWatch monitor
        self.cloudwatch_monitor = CloudWatchMonitor(
            region=region,
            namespace=self.namespace,
            environment=environment
        )
        
        logger.info(f"Initialized monitoring setup for {agent_name} in {environment}")
    
    async def setup_complete_monitoring(self) -> Dict[str, Any]:
        """
        Set up complete monitoring infrastructure.
        
        Returns:
            Dictionary with setup results
        """
        logger.info("Setting up complete monitoring infrastructure...")
        
        results = {
            "timestamp": datetime.utcnow().isoformat(),
            "environment": self.environment,
            "agent_name": self.agent_name,
            "components": {}
        }
        
        try:
            # 1. Create CloudWatch log groups
            log_groups_result = await self._setup_log_groups()
            results["components"]["log_groups"] = log_groups_result
            
            # 2. Create CloudWatch dashboard
            dashboard_result = await self._setup_dashboard()
            results["components"]["dashboard"] = dashboard_result
            
            # 3. Create CloudWatch alarms
            alarms_result = await self._setup_alarms()
            results["components"]["alarms"] = alarms_result
            
            # 4. Setup custom metrics
            metrics_result = await self._setup_custom_metrics()
            results["components"]["custom_metrics"] = metrics_result
            
            # 5. Create SNS topics for alerting
            sns_result = await self._setup_sns_topics()
            results["components"]["sns_topics"] = sns_result
            
            # 6. Setup health check endpoints
            health_check_result = await self._setup_health_checks()
            results["components"]["health_checks"] = health_check_result
            
            # 7. Create monitoring configuration files
            config_result = await self._create_monitoring_configs()
            results["components"]["configurations"] = config_result
            
            results["status"] = "success"
            results["summary"] = self._generate_setup_summary(results)
            
            logger.info("Complete monitoring setup completed successfully")
            return results
            
        except Exception as e:
            logger.error(f"Monitoring setup failed: {e}")
            results["status"] = "failed"
            results["error"] = str(e)
            return results
    
    async def _setup_log_groups(self) -> Dict[str, Any]:
        """Setup CloudWatch log groups"""
        logger.info("Setting up CloudWatch log groups...")
        
        log_groups = [
            {
                "name": f"/aws/lambda/{self.agent_name}-{self.environment}",
                "retention_days": 7 if self.environment == "development" else 30
            },
            {
                "name": f"/mbti/travel-assistant/{self.environment}/application",
                "retention_days": 14 if self.environment == "development" else 90
            },
            {
                "name": f"/mbti/travel-assistant/{self.environment}/mcp-calls",
                "retention_days": 7 if self.environment == "development" else 30
            },
            {
                "name": f"/mbti/travel-assistant/{self.environment}/security",
                "retention_days": 30 if self.environment == "development" else 365
            },
            {
                "name": f"/mbti/travel-assistant/{self.environment}/performance",
                "retention_days": 14 if self.environment == "development" else 60
            }
        ]
        
        created_groups = []
        failed_groups = []
        
        for log_group in log_groups:
            try:
                success = self.cloudwatch_monitor.create_log_group(
                    log_group["name"],
                    log_group["retention_days"]
                )
                
                if success:
                    created_groups.append(log_group["name"])
                    logger.info(f"Created log group: {log_group['name']}")
                else:
                    failed_groups.append(log_group["name"])
                    
            except Exception as e:
                logger.error(f"Failed to create log group {log_group['name']}: {e}")
                failed_groups.append(log_group["name"])
        
        return {
            "created": created_groups,
            "failed": failed_groups,
            "total": len(log_groups)
        }
    
    async def _setup_dashboard(self) -> Dict[str, Any]:
        """Setup CloudWatch dashboard"""
        logger.info("Setting up CloudWatch dashboard...")
        
        try:
            success = self.cloudwatch_monitor.create_dashboard(self.agent_name)
            
            if success:
                dashboard_name = f"{self.agent_name}-{self.environment}-dashboard"
                dashboard_url = f"https://{self.region}.console.aws.amazon.com/cloudwatch/home?region={self.region}#dashboards:name={dashboard_name}"
                
                return {
                    "created": True,
                    "dashboard_name": dashboard_name,
                    "dashboard_url": dashboard_url
                }
            else:
                return {
                    "created": False,
                    "error": "Dashboard creation failed"
                }
                
        except Exception as e:
            logger.error(f"Failed to create dashboard: {e}")
            return {
                "created": False,
                "error": str(e)
            }
    
    async def _setup_alarms(self) -> Dict[str, Any]:
        """Setup CloudWatch alarms"""
        logger.info("Setting up CloudWatch alarms...")
        
        try:
            # Create standard alarms
            created_alarms = self.cloudwatch_monitor.create_standard_alarms(self.agent_name)
            
            # Create additional environment-specific alarms
            additional_alarms = await self._create_additional_alarms()
            created_alarms.extend(additional_alarms)
            
            return {
                "created": created_alarms,
                "total": len(created_alarms)
            }
            
        except Exception as e:
            logger.error(f"Failed to create alarms: {e}")
            return {
                "created": [],
                "error": str(e)
            }
    
    async def _create_additional_alarms(self) -> List[str]:
        """Create additional environment-specific alarms"""
        additional_alarms = []
        
        # Environment-specific alarm configurations
        if self.environment == "production":
            # More strict thresholds for production
            alarm_configs = [
                AlarmConfiguration(
                    alarm_name=f"{self.agent_name}-{self.environment}-jwt-auth-failures",
                    metric_name="JWTAuthFailures",
                    namespace=self.namespace,
                    statistic="Sum",
                    threshold=10.0,  # 10 failures in 5 minutes
                    comparison_operator="GreaterThanThreshold",
                    evaluation_periods=1,
                    period=300,
                    dimensions={"Environment": self.environment, "Service": self.agent_name},
                    alarm_description=f"High JWT authentication failures for {self.agent_name}"
                ),
                AlarmConfiguration(
                    alarm_name=f"{self.agent_name}-{self.environment}-cache-miss-rate",
                    metric_name="CacheMissRate",
                    namespace=self.namespace,
                    statistic="Average",
                    threshold=0.8,  # 80% miss rate
                    comparison_operator="GreaterThanThreshold",
                    evaluation_periods=2,
                    period=300,
                    dimensions={"Environment": self.environment, "Service": self.agent_name},
                    alarm_description=f"High cache miss rate for {self.agent_name}"
                )
            ]
        else:
            # More relaxed thresholds for development/staging
            alarm_configs = [
                AlarmConfiguration(
                    alarm_name=f"{self.agent_name}-{self.environment}-service-unavailable",
                    metric_name="ServiceUnavailable",
                    namespace=self.namespace,
                    statistic="Sum",
                    threshold=1.0,  # Any service unavailable events
                    comparison_operator="GreaterThanThreshold",
                    evaluation_periods=1,
                    period=300,
                    dimensions={"Environment": self.environment, "Service": self.agent_name},
                    alarm_description=f"Service unavailable events for {self.agent_name}"
                )
            ]
        
        for alarm_config in alarm_configs:
            try:
                if self.cloudwatch_monitor.create_alarm(alarm_config):
                    additional_alarms.append(alarm_config.alarm_name)
            except Exception as e:
                logger.error(f"Failed to create alarm {alarm_config.alarm_name}: {e}")
        
        return additional_alarms
    
    async def _setup_custom_metrics(self) -> Dict[str, Any]:
        """Setup custom metrics collection"""
        logger.info("Setting up custom metrics...")
        
        # Define custom metrics to track
        custom_metrics = [
            "RestaurantRecommendations",
            "MCPCallLatency",
            "CacheOperations",
            "AuthenticationAttempts",
            "UserSessions",
            "RestaurantSearches",
            "SentimentAnalysisRequests"
        ]
        
        # Send initial metrics to establish them in CloudWatch
        established_metrics = []
        
        for metric_name in custom_metrics:
            try:
                success = self.cloudwatch_monitor.put_metric(
                    metric_name,
                    0.0,
                    MetricUnit.COUNT,
                    {"Environment": self.environment, "Service": self.agent_name}
                )
                
                if success:
                    established_metrics.append(metric_name)
                    
            except Exception as e:
                logger.error(f"Failed to establish metric {metric_name}: {e}")
        
        return {
            "established": established_metrics,
            "total": len(custom_metrics)
        }
    
    async def _setup_sns_topics(self) -> Dict[str, Any]:
        """Setup SNS topics for alerting"""
        logger.info("Setting up SNS topics for alerting...")
        
        try:
            sns_client = boto3.client('sns', region_name=self.region)
            
            # Define SNS topics
            topics = [
                {
                    "name": f"{self.agent_name}-{self.environment}-critical-alerts",
                    "display_name": f"MBTI Travel Assistant Critical Alerts ({self.environment})"
                },
                {
                    "name": f"{self.agent_name}-{self.environment}-warning-alerts",
                    "display_name": f"MBTI Travel Assistant Warning Alerts ({self.environment})"
                },
                {
                    "name": f"{self.agent_name}-{self.environment}-security-alerts",
                    "display_name": f"MBTI Travel Assistant Security Alerts ({self.environment})"
                }
            ]
            
            created_topics = []
            
            for topic in topics:
                try:
                    response = sns_client.create_topic(
                        Name=topic["name"],
                        Attributes={
                            'DisplayName': topic["display_name"]
                        }
                    )
                    
                    topic_arn = response['TopicArn']
                    created_topics.append({
                        "name": topic["name"],
                        "arn": topic_arn
                    })
                    
                    logger.info(f"Created SNS topic: {topic['name']}")
                    
                except Exception as e:
                    logger.error(f"Failed to create SNS topic {topic['name']}: {e}")
            
            return {
                "created": created_topics,
                "total": len(topics)
            }
            
        except Exception as e:
            logger.error(f"Failed to setup SNS topics: {e}")
            return {
                "created": [],
                "error": str(e)
            }
    
    async def _setup_health_checks(self) -> Dict[str, Any]:
        """Setup health check configuration"""
        logger.info("Setting up health check configuration...")
        
        try:
            # Create health check configuration
            health_config = {
                "enabled": True,
                "interval_seconds": 30,
                "timeout_seconds": 10,
                "checks": [
                    {
                        "name": "mcp_search_server",
                        "type": "mcp_connection",
                        "critical": True,
                        "timeout": 5
                    },
                    {
                        "name": "mcp_reasoning_server",
                        "type": "mcp_connection",
                        "critical": True,
                        "timeout": 5
                    },
                    {
                        "name": "cache_service",
                        "type": "cache_operation",
                        "critical": False,
                        "timeout": 3
                    },
                    {
                        "name": "system_resources",
                        "type": "system_check",
                        "critical": True,
                        "thresholds": {
                            "cpu_percent": 90,
                            "memory_percent": 90,
                            "disk_percent": 95
                        }
                    },
                    {
                        "name": "cloudwatch_connectivity",
                        "type": "aws_service",
                        "critical": False,
                        "timeout": 5
                    }
                ],
                "alerting": {
                    "enabled": True,
                    "critical_threshold": 2,  # Number of failed critical checks
                    "notification_channels": [
                        "cloudwatch_alarms",
                        "application_logs"
                    ]
                }
            }
            
            # Save health check configuration
            config_path = Path("config") / "health_check_config.json"
            config_path.parent.mkdir(exist_ok=True)
            
            with open(config_path, 'w') as f:
                json.dump(health_config, f, indent=2)
            
            return {
                "configured": True,
                "config_path": str(config_path),
                "checks_count": len(health_config["checks"])
            }
            
        except Exception as e:
            logger.error(f"Failed to setup health checks: {e}")
            return {
                "configured": False,
                "error": str(e)
            }
    
    async def _create_monitoring_configs(self) -> Dict[str, Any]:
        """Create monitoring configuration files"""
        logger.info("Creating monitoring configuration files...")
        
        created_configs = []
        
        try:
            # 1. Prometheus configuration for environment
            prometheus_config = self._generate_prometheus_config()
            prometheus_path = Path("monitoring") / f"prometheus.{self.environment}.yml"
            
            with open(prometheus_path, 'w') as f:
                import yaml
                yaml.dump(prometheus_config, f, default_flow_style=False)
            
            created_configs.append(str(prometheus_path))
            
            # 2. Alerting rules configuration
            alerting_rules = self._generate_alerting_rules()
            rules_path = Path("monitoring") / "rules" / f"{self.environment}_alerts.yml"
            rules_path.parent.mkdir(exist_ok=True)
            
            with open(rules_path, 'w') as f:
                import yaml
                yaml.dump(alerting_rules, f, default_flow_style=False)
            
            created_configs.append(str(rules_path))
            
            # 3. Grafana dashboard configuration
            dashboard_config = self._generate_grafana_dashboard_config()
            dashboard_path = Path("monitoring") / f"grafana_dashboard_{self.environment}.json"
            
            with open(dashboard_path, 'w') as f:
                json.dump(dashboard_config, f, indent=2)
            
            created_configs.append(str(dashboard_path))
            
            # 4. Monitoring deployment configuration
            deployment_config = self._generate_monitoring_deployment_config()
            deployment_path = Path("monitoring") / f"deployment_{self.environment}.yml"
            
            with open(deployment_path, 'w') as f:
                import yaml
                yaml.dump(deployment_config, f, default_flow_style=False)
            
            created_configs.append(str(deployment_path))
            
            return {
                "created": created_configs,
                "total": len(created_configs)
            }
            
        except Exception as e:
            logger.error(f"Failed to create monitoring configs: {e}")
            return {
                "created": created_configs,
                "error": str(e)
            }
    
    def _generate_prometheus_config(self) -> Dict[str, Any]:
        """Generate Prometheus configuration for environment"""
        return {
            "global": {
                "scrape_interval": "15s",
                "evaluation_interval": "15s",
                "external_labels": {
                    "cluster": f"mbti-travel-assistant-{self.environment}",
                    "environment": self.environment
                }
            },
            "rule_files": [
                f"rules/{self.environment}_alerts.yml"
            ],
            "scrape_configs": [
                {
                    "job_name": "mbti-travel-assistant",
                    "static_configs": [
                        {"targets": [f"mbti-travel-assistant:9090"]}
                    ],
                    "metrics_path": "/metrics",
                    "scrape_interval": "15s",
                    "scrape_timeout": "10s"
                },
                {
                    "job_name": "health-checks",
                    "static_configs": [
                        {"targets": [f"mbti-travel-assistant:8080"]}
                    ],
                    "metrics_path": "/health/metrics",
                    "scrape_interval": "30s"
                }
            ]
        }
    
    def _generate_alerting_rules(self) -> Dict[str, Any]:
        """Generate alerting rules for environment"""
        # Environment-specific thresholds
        thresholds = {
            "development": {
                "error_rate": 0.1,  # 10%
                "response_time": 10.0,  # 10 seconds
                "cpu_usage": 90,  # 90%
                "memory_usage": 90  # 90%
            },
            "staging": {
                "error_rate": 0.05,  # 5%
                "response_time": 5.0,  # 5 seconds
                "cpu_usage": 80,  # 80%
                "memory_usage": 80  # 80%
            },
            "production": {
                "error_rate": 0.02,  # 2%
                "response_time": 3.0,  # 3 seconds
                "cpu_usage": 70,  # 70%
                "memory_usage": 70  # 70%
            }
        }
        
        env_thresholds = thresholds.get(self.environment, thresholds["development"])
        
        return {
            "groups": [
                {
                    "name": f"mbti_travel_assistant_{self.environment}",
                    "rules": [
                        {
                            "alert": "HighErrorRate",
                            "expr": f"rate(http_requests_total{{job=\"mbti-travel-assistant\",status=~\"5..\",environment=\"{self.environment}\"}}[5m]) / rate(http_requests_total{{job=\"mbti-travel-assistant\",environment=\"{self.environment}\"}}[5m]) > {env_thresholds['error_rate']}",
                            "for": "2m",
                            "labels": {
                                "severity": "critical",
                                "service": "mbti-travel-assistant",
                                "environment": self.environment
                            },
                            "annotations": {
                                "summary": f"High error rate in {self.environment}",
                                "description": f"Error rate is above {env_thresholds['error_rate']*100}% for more than 2 minutes"
                            }
                        },
                        {
                            "alert": "HighResponseTime",
                            "expr": f"histogram_quantile(0.95, rate(http_request_duration_seconds_bucket{{job=\"mbti-travel-assistant\",environment=\"{self.environment}\"}}[5m])) > {env_thresholds['response_time']}",
                            "for": "5m",
                            "labels": {
                                "severity": "warning",
                                "service": "mbti-travel-assistant",
                                "environment": self.environment
                            },
                            "annotations": {
                                "summary": f"High response time in {self.environment}",
                                "description": f"95th percentile response time is above {env_thresholds['response_time']}s"
                            }
                        },
                        {
                            "alert": "MCPServerDown",
                            "expr": f"up{{job=\"mcp-servers\",environment=\"{self.environment}\"}} == 0",
                            "for": "1m",
                            "labels": {
                                "severity": "critical",
                                "service": "mcp-servers",
                                "environment": self.environment
                            },
                            "annotations": {
                                "summary": f"MCP server is down in {self.environment}",
                                "description": "MCP server is not responding"
                            }
                        }
                    ]
                }
            ]
        }
    
    def _generate_grafana_dashboard_config(self) -> Dict[str, Any]:
        """Generate Grafana dashboard configuration"""
        # Load base dashboard and customize for environment
        try:
            dashboard_path = Path("monitoring") / "grafana_dashboard.json"
            if dashboard_path.exists():
                with open(dashboard_path, 'r') as f:
                    base_dashboard = json.load(f)
                
                # Customize for environment
                dashboard = base_dashboard.copy()
                dashboard["dashboard"]["title"] = f"MBTI Travel Assistant - {self.environment.title()}"
                dashboard["dashboard"]["tags"].append(self.environment)
                
                return dashboard
            else:
                # Return minimal dashboard if base doesn't exist
                return {
                    "dashboard": {
                        "title": f"MBTI Travel Assistant - {self.environment.title()}",
                        "tags": ["mbti", "travel-assistant", self.environment],
                        "panels": []
                    }
                }
                
        except Exception as e:
            logger.warning(f"Failed to load base dashboard: {e}")
            return {"error": str(e)}
    
    def _generate_monitoring_deployment_config(self) -> Dict[str, Any]:
        """Generate monitoring deployment configuration"""
        return {
            "version": "3.8",
            "services": {
                "prometheus": {
                    "image": "prom/prometheus:latest",
                    "container_name": f"prometheus-{self.environment}",
                    "ports": ["9090:9090"],
                    "volumes": [
                        f"./monitoring/prometheus.{self.environment}.yml:/etc/prometheus/prometheus.yml",
                        f"./monitoring/rules:/etc/prometheus/rules"
                    ],
                    "command": [
                        "--config.file=/etc/prometheus/prometheus.yml",
                        "--storage.tsdb.path=/prometheus",
                        "--web.console.libraries=/etc/prometheus/console_libraries",
                        "--web.console.templates=/etc/prometheus/consoles",
                        "--storage.tsdb.retention.time=7d",
                        "--web.enable-lifecycle"
                    ]
                },
                "grafana": {
                    "image": "grafana/grafana:latest",
                    "container_name": f"grafana-{self.environment}",
                    "ports": ["3000:3000"],
                    "environment": {
                        "GF_SECURITY_ADMIN_PASSWORD": "admin123",
                        "GF_INSTALL_PLUGINS": "grafana-clock-panel,grafana-simple-json-datasource"
                    },
                    "volumes": [
                        "grafana-storage:/var/lib/grafana",
                        f"./monitoring/grafana_dashboard_{self.environment}.json:/etc/grafana/provisioning/dashboards/dashboard.json"
                    ]
                }
            },
            "volumes": {
                "grafana-storage": {}
            }
        }
    
    def _generate_setup_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate setup summary"""
        summary = {
            "total_components": len(results["components"]),
            "successful_components": 0,
            "failed_components": 0,
            "warnings": []
        }
        
        for component, result in results["components"].items():
            if isinstance(result, dict):
                if result.get("created") or result.get("configured") or result.get("established"):
                    summary["successful_components"] += 1
                elif result.get("error"):
                    summary["failed_components"] += 1
                    summary["warnings"].append(f"{component}: {result['error']}")
        
        summary["success_rate"] = (
            summary["successful_components"] / summary["total_components"] * 100
            if summary["total_components"] > 0 else 0
        )
        
        return summary


async def main():
    """Main setup function"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Setup monitoring and observability for MBTI Travel Assistant',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Setup monitoring for development
  python setup_monitoring.py --environment development
  
  # Setup monitoring for production with custom region
  python setup_monitoring.py --environment production --region us-west-2
  
  # Setup only CloudWatch components
  python setup_monitoring.py --environment staging --cloudwatch-only
        """
    )
    
    parser.add_argument('--environment', default='development',
                       choices=['development', 'staging', 'production'],
                       help='Environment to setup monitoring for')
    parser.add_argument('--region', default='us-east-1',
                       help='AWS region')
    parser.add_argument('--agent-name', default='mbti-travel-assistant-mcp',
                       help='Agent/service name')
    parser.add_argument('--cloudwatch-only', action='store_true',
                       help='Setup only CloudWatch components')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Configure logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # Initialize monitoring setup
        monitoring_setup = MonitoringSetup(
            environment=args.environment,
            region=args.region,
            agent_name=args.agent_name
        )
        
        # Run setup
        results = await monitoring_setup.setup_complete_monitoring()
        
        # Display results
        print("\n" + "="*60)
        print("MONITORING SETUP RESULTS")
        print("="*60)
        print(f"Environment: {results['environment']}")
        print(f"Agent Name: {results['agent_name']}")
        print(f"Status: {results['status'].upper()}")
        
        if results["status"] == "success":
            summary = results["summary"]
            print(f"Success Rate: {summary['success_rate']:.1f}%")
            print(f"Successful Components: {summary['successful_components']}")
            print(f"Failed Components: {summary['failed_components']}")
            
            if summary["warnings"]:
                print("\nWarnings:")
                for warning in summary["warnings"]:
                    print(f"  - {warning}")
            
            print("\nComponents Setup:")
            for component, result in results["components"].items():
                status = "✓" if (result.get("created") or result.get("configured") or result.get("established")) else "✗"
                print(f"  {status} {component.replace('_', ' ').title()}")
        else:
            print(f"Error: {results.get('error', 'Unknown error')}")
        
        print("="*60)
        
        # Save results to file
        results_file = f"monitoring_setup_results_{args.environment}.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\nDetailed results saved to: {results_file}")
        
        if results["status"] == "success":
            print("\nNext steps:")
            print("1. Verify CloudWatch dashboard is accessible")
            print("2. Test health check endpoints")
            print("3. Configure alert notification channels")
            print("4. Review and adjust alarm thresholds if needed")
        
    except Exception as e:
        logger.error(f"Monitoring setup failed: {str(e)}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())    
def _generate_alertmanager_config(self) -> Dict[str, Any]:
        """Generate Alertmanager configuration"""
        return {
            "global": {
                "smtp_smarthost": "localhost:587",
                "smtp_from": f"alerts@{self.agent_name}.com"
            },
            "route": {
                "group_by": ["alertname"],
                "group_wait": "10s",
                "group_interval": "10s",
                "repeat_interval": "1h",
                "receiver": "web.hook"
            },
            "receivers": [
                {
                    "name": "web.hook",
                    "webhook_configs": [
                        {
                            "url": f"http://{self.agent_name}:8080/alerts/webhook",
                            "send_resolved": True
                        }
                    ]
                }
            ]
        }
    
    def _generate_performance_dashboard_config(self) -> Dict[str, Any]:
        """Generate performance dashboard configuration"""
        return {
            "dashboard": {
                "id": None,
                "title": f"MBTI Travel Assistant Performance - {self.environment.title()}",
                "tags": ["mbti", "travel-assistant", "performance", self.environment],
                "style": "dark",
                "timezone": "browser",
                "refresh": "10s",
                "time": {
                    "from": "now-30m",
                    "to": "now"
                },
                "panels": [
                    {
                        "id": 1,
                        "title": "Real-time Performance Metrics",
                        "type": "stat",
                        "gridPos": {"h": 4, "w": 24, "x": 0, "y": 0},
                        "targets": [
                            {
                                "expr": f"rate(http_requests_total{{job=\"{self.agent_name}\"}}[1m])",
                                "legendFormat": "Requests/sec",
                                "refId": "A"
                            },
                            {
                                "expr": f"histogram_quantile(0.95, rate(http_request_duration_seconds_bucket{{job=\"{self.agent_name}\"}}[1m]))",
                                "legendFormat": "95th Percentile Response Time",
                                "refId": "B"
                            },
                            {
                                "expr": f"rate(http_requests_total{{job=\"{self.agent_name}\",status=~\"5..\"}}[1m]) / rate(http_requests_total{{job=\"{self.agent_name}\"}}[1m])",
                                "legendFormat": "Error Rate",
                                "refId": "C"
                            }
                        ]
                    },
                    {
                        "id": 2,
                        "title": "Alert Status",
                        "type": "stat",
                        "gridPos": {"h": 4, "w": 12, "x": 0, "y": 4},
                        "targets": [
                            {
                                "expr": f"active_alerts{{environment=\"{self.environment}\"}}",
                                "legendFormat": "Active Alerts",
                                "refId": "A"
                            }
                        ]
                    },
                    {
                        "id": 3,
                        "title": "System Health",
                        "type": "stat",
                        "gridPos": {"h": 4, "w": 12, "x": 12, "y": 4},
                        "targets": [
                            {
                                "expr": f"health_status{{environment=\"{self.environment}\"}}",
                                "legendFormat": "Health Status",
                                "refId": "A"
                            }
                        ]
                    }
                ]
            }
        }


async def setup_comprehensive_monitoring():
    """Setup comprehensive monitoring with all components"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Setup comprehensive monitoring for MBTI Travel Assistant'
    )
    parser.add_argument('--environment', default='development',
                       choices=['development', 'staging', 'production'],
                       help='Environment name')
    parser.add_argument('--region', default='us-east-1',
                       help='AWS region')
    parser.add_argument('--agent-name', default='mbti-travel-assistant-mcp',
                       help='Agent name')
    parser.add_argument('--enable-alerting', action='store_true',
                       help='Enable alerting system')
    parser.add_argument('--enable-performance-dashboard', action='store_true',
                       help='Enable performance dashboard')
    
    args = parser.parse_args()
    
    try:
        # Setup basic monitoring
        monitoring_setup = MonitoringSetup(
            environment=args.environment,
            region=args.region,
            agent_name=args.agent_name
        )
        
        result = await monitoring_setup.setup_complete_monitoring()
        
        # Setup alerting system if requested
        if args.enable_alerting:
            from services.alerting_system import AlertingSystem, NotificationChannel, AlertSeverity
            
            alerting = AlertingSystem(environment=args.environment)
            
            # Add default notification channels
            if args.environment == "production":
                # Email notifications for production
                email_channel = NotificationChannel(
                    name="email_alerts",
                    type="email",
                    config={
                        "recipients": ["ops@example.com", "alerts@example.com"],
                        "host": "smtp.example.com",
                        "port": 587,
                        "username": "alerts@example.com",
                        "password": "password",
                        "from_email": "alerts@example.com"
                    },
                    severity_filter=[AlertSeverity.CRITICAL, AlertSeverity.WARNING]
                )
                alerting.add_notification_channel(email_channel)
                
                # Slack notifications
                slack_channel = NotificationChannel(
                    name="slack_alerts",
                    type="slack",
                    config={
                        "webhook_url": "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK",
                        "channel": "#alerts"
                    },
                    severity_filter=[AlertSeverity.CRITICAL, AlertSeverity.WARNING]
                )
                alerting.add_notification_channel(slack_channel)
            
            logger.info("Alerting system configured")
        
        # Setup performance dashboard if requested
        if args.enable_performance_dashboard:
            from services.performance_dashboard import PerformanceDashboard
            from services.cloudwatch_monitor import CloudWatchMonitor
            
            cloudwatch_monitor = CloudWatchMonitor(
                region=args.region,
                environment=args.environment
            )
            
            dashboard = PerformanceDashboard(
                cloudwatch_monitor=cloudwatch_monitor,
                environment=args.environment
            )
            
            logger.info("Performance dashboard configured")
        
        if result["status"] == "success":
            print("\n" + "="*60)
            print("🎉 COMPREHENSIVE MONITORING SETUP SUCCESSFUL! 🎉")
            print("="*60)
            print(f"Environment: {args.environment}")
            print(f"Agent: {args.agent_name}")
            print(f"Region: {args.region}")
            print(f"Components: {result['summary']['successful_components']}/{result['summary']['total_components']}")
            print(f"Success Rate: {result['summary']['success_rate']:.1f}%")
            if args.enable_alerting:
                print("✓ Alerting system enabled")
            if args.enable_performance_dashboard:
                print("✓ Performance dashboard enabled")
            print("="*60)
            return 0
        else:
            print("\n" + "="*60)
            print("⚠️ MONITORING SETUP COMPLETED WITH ISSUES")
            print("="*60)
            print(f"Success Rate: {result['summary']['success_rate']:.1f}%")
            print(f"Warnings: {len(result['summary']['warnings'])}")
            for warning in result['summary']['warnings']:
                print(f"  - {warning}")
            print("="*60)
            return 1
            
    except Exception as e:
        logger.error(f"Comprehensive monitoring setup failed: {e}")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(asyncio.run(setup_comprehensive_monitoring()))