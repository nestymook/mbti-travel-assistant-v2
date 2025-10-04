#!/usr/bin/env python3
"""
Agent Health and Performance Monitoring Script

This script monitors the health and performance of the mbti-travel-planner-agent
by checking various metrics including gateway connectivity, response times,
error rates, and system health indicators.

Features:
- Continuous health monitoring with configurable intervals
- Performance metrics collection and analysis
- Alert generation for health issues
- Historical data tracking and reporting
- Dashboard-style output for monitoring
- Integration with logging and observability systems
"""

import asyncio
import json
import logging
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
import argparse
import signal
from dataclasses import dataclass, field
from collections import deque
import statistics

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from services.health_check_service import get_health_check_service, HealthStatus
from services.gateway_http_client import GatewayHTTPClient, Environment
from services.logging_service import get_logging_service
from services.error_handler import ErrorHandler


@dataclass
class HealthMetric:
    """Represents a health metric data point."""
    timestamp: datetime
    metric_name: str
    value: float
    status: str
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AlertRule:
    """Defines an alert rule for monitoring."""
    name: str
    condition: Callable[[List[HealthMetric]], bool]
    severity: str  # "info", "warning", "critical"
    message_template: str
    cooldown_minutes: int = 5
    last_triggered: Optional[datetime] = None


class AgentHealthMonitor:
    """Comprehensive health and performance monitor for the MBTI Travel Planner Agent."""
    
    def __init__(self, 
                 environment: str = "production",
                 check_interval: int = 60,
                 history_size: int = 1000,
                 verbose: bool = False):
        """
        Initialize the health monitor.
        
        Args:
            environment: Environment to monitor (development, staging, production)
            check_interval: Check interval in seconds
            history_size: Number of historical metrics to keep
            verbose: Enable verbose logging
        """
        self.environment = environment
        self.check_interval = check_interval
        self.history_size = history_size
        self.verbose = verbose
        
        # Setup logging
        logging.basicConfig(
            level=logging.DEBUG if verbose else logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger("agent_health_monitor")
        
        # Initialize services
        self.logging_service = get_logging_service()
        self.error_handler = ErrorHandler("agent_health_monitor")
        self.health_service = get_health_check_service()
        
        # Initialize environment
        env_enum = Environment.PRODUCTION
        if environment == "development":
            env_enum = Environment.DEVELOPMENT
        elif environment == "staging":
            env_enum = Environment.STAGING
        
        self.gateway_client = GatewayHTTPClient(environment=env_enum)
        
        # Monitoring state
        self.is_running = False
        self.metrics_history: deque = deque(maxlen=history_size)
        self.alerts_history: List[Dict[str, Any]] = []
        self.start_time = None
        
        # Performance tracking
        self.performance_stats = {
            "total_checks": 0,
            "successful_checks": 0,
            "failed_checks": 0,
            "average_response_time": 0.0,
            "uptime_percentage": 100.0
        }
        
        # Initialize alert rules
        self.alert_rules = self._initialize_alert_rules()
        
        self.logger.info(f"Initialized agent health monitor for {environment}")
    
    def _initialize_alert_rules(self) -> List[AlertRule]:
        """Initialize alert rules for monitoring."""
        return [
            AlertRule(
                name="high_response_time",
                condition=lambda metrics: any(
                    m.value > 30000 for m in metrics[-5:] 
                    if m.metric_name == "response_time_ms"
                ),
                severity="warning",
                message_template="High response time detected: {value:.2f}ms (threshold: 30000ms)",
                cooldown_minutes=10
            ),
            AlertRule(
                name="service_unavailable",
                condition=lambda metrics: any(
                    m.status == "unhealthy" for m in metrics[-3:]
                    if m.metric_name == "service_health"
                ),
                severity="critical",
                message_template="Service unavailable: {details}",
                cooldown_minutes=5
            ),
            AlertRule(
                name="high_error_rate",
                condition=lambda metrics: self._calculate_error_rate(metrics[-10:]) > 50,
                severity="warning",
                message_template="High error rate: {value:.1f}% (threshold: 50%)",
                cooldown_minutes=15
            ),
            AlertRule(
                name="low_success_rate",
                condition=lambda metrics: self._calculate_success_rate(metrics[-20:]) < 80,
                severity="critical",
                message_template="Low success rate: {value:.1f}% (threshold: 80%)",
                cooldown_minutes=10
            )
        ]
    
    def _calculate_error_rate(self, metrics: List[HealthMetric]) -> float:
        """Calculate error rate from metrics."""
        if not metrics:
            return 0.0
        
        error_metrics = [m for m in metrics if m.metric_name == "operation_result" and m.status == "error"]
        total_metrics = [m for m in metrics if m.metric_name == "operation_result"]
        
        if not total_metrics:
            return 0.0
        
        return (len(error_metrics) / len(total_metrics)) * 100
    
    def _calculate_success_rate(self, metrics: List[HealthMetric]) -> float:
        """Calculate success rate from metrics."""
        if not metrics:
            return 100.0
        
        success_metrics = [m for m in metrics if m.metric_name == "operation_result" and m.status == "success"]
        total_metrics = [m for m in metrics if m.metric_name == "operation_result"]
        
        if not total_metrics:
            return 100.0
        
        return (len(success_metrics) / len(total_metrics)) * 100
    
    async def collect_health_metrics(self) -> List[HealthMetric]:
        """Collect current health metrics."""
        metrics = []
        timestamp = datetime.utcnow()
        
        try:
            # Gateway connectivity metrics
            start_time = time.time()
            search_result = await self.gateway_client.search_restaurants_by_district(["Central district"])
            response_time = (time.time() - start_time) * 1000
            
            # Response time metric
            metrics.append(HealthMetric(
                timestamp=timestamp,
                metric_name="response_time_ms",
                value=response_time,
                status="healthy" if response_time < 15000 else "degraded" if response_time < 30000 else "unhealthy",
                details={"endpoint": "search_restaurants_by_district", "district": "Central district"}
            ))
            
            # Operation result metric
            operation_success = search_result.get("success", False)
            metrics.append(HealthMetric(
                timestamp=timestamp,
                metric_name="operation_result",
                value=1.0 if operation_success else 0.0,
                status="success" if operation_success else "error",
                details={
                    "operation": "restaurant_search",
                    "result_count": len(search_result.get("restaurants", [])),
                    "error": search_result.get("error")
                }
            ))
            
            # Service health metrics from health check service
            health_results = await self.health_service.check_all_endpoints()
            
            for service_name, health_result in health_results.items():
                metrics.append(HealthMetric(
                    timestamp=timestamp,
                    metric_name="service_health",
                    value=health_result.response_time_ms,
                    status=health_result.status,
                    details={
                        "service": service_name,
                        "endpoint": health_result.endpoint,
                        "error": health_result.error_message
                    }
                ))
            
            # Memory and performance metrics
            import psutil
            process = psutil.Process()
            
            metrics.append(HealthMetric(
                timestamp=timestamp,
                metric_name="memory_usage_mb",
                value=process.memory_info().rss / 1024 / 1024,
                status="healthy",
                details={"process_id": process.pid}
            ))
            
            metrics.append(HealthMetric(
                timestamp=timestamp,
                metric_name="cpu_usage_percent",
                value=process.cpu_percent(),
                status="healthy",
                details={"process_id": process.pid}
            ))
            
        except Exception as e:
            self.logger.error(f"Error collecting health metrics: {e}")
            metrics.append(HealthMetric(
                timestamp=timestamp,
                metric_name="collection_error",
                value=1.0,
                status="error",
                details={"error": str(e)}
            ))
        
        return metrics
    
    def add_metrics(self, metrics: List[HealthMetric]) -> None:
        """Add metrics to history and update performance stats."""
        for metric in metrics:
            self.metrics_history.append(metric)
        
        # Update performance stats
        self.performance_stats["total_checks"] += 1
        
        # Count successful operations
        operation_metrics = [m for m in metrics if m.metric_name == "operation_result"]
        if operation_metrics:
            successful_ops = sum(1 for m in operation_metrics if m.status == "success")
            failed_ops = len(operation_metrics) - successful_ops
            
            self.performance_stats["successful_checks"] += successful_ops
            self.performance_stats["failed_checks"] += failed_ops
        
        # Calculate average response time
        response_time_metrics = [m for m in self.metrics_history if m.metric_name == "response_time_ms"]
        if response_time_metrics:
            self.performance_stats["average_response_time"] = statistics.mean(
                [m.value for m in response_time_metrics[-100:]]  # Last 100 measurements
            )
        
        # Calculate uptime percentage
        total_ops = self.performance_stats["successful_checks"] + self.performance_stats["failed_checks"]
        if total_ops > 0:
            self.performance_stats["uptime_percentage"] = (
                self.performance_stats["successful_checks"] / total_ops
            ) * 100
    
    def check_alerts(self, metrics: List[HealthMetric]) -> List[Dict[str, Any]]:
        """Check alert rules and generate alerts."""
        alerts = []
        current_time = datetime.utcnow()
        
        for rule in self.alert_rules:
            # Check cooldown period
            if (rule.last_triggered and 
                current_time - rule.last_triggered < timedelta(minutes=rule.cooldown_minutes)):
                continue
            
            # Evaluate alert condition
            try:
                if rule.condition(list(self.metrics_history)):
                    # Find relevant metric for alert details
                    relevant_metric = None
                    for metric in reversed(metrics):
                        if (rule.name == "high_response_time" and metric.metric_name == "response_time_ms") or \
                           (rule.name == "service_unavailable" and metric.metric_name == "service_health" and metric.status == "unhealthy") or \
                           (rule.name in ["high_error_rate", "low_success_rate"] and metric.metric_name == "operation_result"):
                            relevant_metric = metric
                            break
                    
                    # Generate alert
                    alert = {
                        "timestamp": current_time.isoformat(),
                        "rule_name": rule.name,
                        "severity": rule.severity,
                        "message": rule.message_template.format(
                            value=relevant_metric.value if relevant_metric else 0,
                            details=relevant_metric.details if relevant_metric else {}
                        ),
                        "metric": relevant_metric.__dict__ if relevant_metric else None
                    }
                    
                    alerts.append(alert)
                    rule.last_triggered = current_time
                    
                    # Log alert
                    log_level = logging.CRITICAL if rule.severity == "critical" else logging.WARNING
                    self.logger.log(log_level, f"ALERT [{rule.severity.upper()}]: {alert['message']}")
            
            except Exception as e:
                self.logger.error(f"Error evaluating alert rule {rule.name}: {e}")
        
        return alerts
    
    def get_current_status(self) -> Dict[str, Any]:
        """Get current health status summary."""
        current_time = datetime.utcnow()
        
        # Get recent metrics (last 5 minutes)
        recent_cutoff = current_time - timedelta(minutes=5)
        recent_metrics = [m for m in self.metrics_history if m.timestamp > recent_cutoff]
        
        # Determine overall health status
        overall_status = "healthy"
        if any(m.status == "unhealthy" for m in recent_metrics):
            overall_status = "unhealthy"
        elif any(m.status == "degraded" for m in recent_metrics):
            overall_status = "degraded"
        
        # Get latest metrics by type
        latest_metrics = {}
        for metric_name in ["response_time_ms", "memory_usage_mb", "cpu_usage_percent"]:
            matching_metrics = [m for m in recent_metrics if m.metric_name == metric_name]
            if matching_metrics:
                latest_metrics[metric_name] = matching_metrics[-1].value
        
        # Calculate recent success rate
        recent_success_rate = self._calculate_success_rate(recent_metrics)
        
        return {
            "timestamp": current_time.isoformat(),
            "overall_status": overall_status,
            "environment": self.environment,
            "uptime_seconds": (current_time - self.start_time).total_seconds() if self.start_time else 0,
            "performance_stats": self.performance_stats.copy(),
            "recent_success_rate": recent_success_rate,
            "latest_metrics": latest_metrics,
            "active_alerts": len([a for a in self.alerts_history[-10:] if a.get("severity") in ["warning", "critical"]]),
            "total_metrics_collected": len(self.metrics_history)
        }
    
    def print_dashboard(self) -> None:
        """Print a dashboard-style status display."""
        status = self.get_current_status()
        
        # Clear screen (works on most terminals)
        print("\033[2J\033[H", end="")
        
        print("=" * 80)
        print(f"MBTI TRAVEL PLANNER AGENT - HEALTH MONITOR")
        print("=" * 80)
        print(f"Environment: {status['environment']:20} Status: {status['overall_status'].upper()}")
        print(f"Uptime: {status['uptime_seconds']:.0f}s ({status['uptime_seconds']/3600:.1f}h)")
        print(f"Last Update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Performance metrics
        perf = status['performance_stats']
        print("PERFORMANCE METRICS")
        print("-" * 40)
        print(f"Total Checks: {perf['total_checks']:10}")
        print(f"Successful: {perf['successful_checks']:12} ({status['recent_success_rate']:.1f}% recent)")
        print(f"Failed: {perf['failed_checks']:16}")
        print(f"Avg Response Time: {perf['average_response_time']:.2f}ms")
        print(f"Uptime: {perf['uptime_percentage']:.2f}%")
        print()
        
        # Latest metrics
        latest = status['latest_metrics']
        print("LATEST METRICS")
        print("-" * 40)
        if 'response_time_ms' in latest:
            print(f"Response Time: {latest['response_time_ms']:.2f}ms")
        if 'memory_usage_mb' in latest:
            print(f"Memory Usage: {latest['memory_usage_mb']:.2f}MB")
        if 'cpu_usage_percent' in latest:
            print(f"CPU Usage: {latest['cpu_usage_percent']:.1f}%")
        print()
        
        # Recent alerts
        recent_alerts = self.alerts_history[-5:]
        if recent_alerts:
            print("RECENT ALERTS")
            print("-" * 40)
            for alert in recent_alerts:
                severity_symbol = "🔴" if alert['severity'] == "critical" else "🟡" if alert['severity'] == "warning" else "🔵"
                timestamp = datetime.fromisoformat(alert['timestamp']).strftime('%H:%M:%S')
                print(f"{severity_symbol} {timestamp} [{alert['severity'].upper()}] {alert['message'][:50]}...")
        else:
            print("RECENT ALERTS")
            print("-" * 40)
            print("No recent alerts")
        
        print()
        print("=" * 80)
        print(f"Press Ctrl+C to stop monitoring")
        print("=" * 80)
    
    async def run_monitoring_cycle(self) -> None:
        """Run a single monitoring cycle."""
        try:
            # Collect metrics
            metrics = await self.collect_health_metrics()
            self.add_metrics(metrics)
            
            # Check for alerts
            alerts = self.check_alerts(metrics)
            self.alerts_history.extend(alerts)
            
            # Log metrics if verbose
            if self.verbose:
                for metric in metrics:
                    self.logger.debug(f"Metric: {metric.metric_name}={metric.value} ({metric.status})")
            
        except Exception as e:
            self.logger.error(f"Error in monitoring cycle: {e}")
            self.error_handler.handle_error(e, "monitoring_cycle")
    
    async def start_monitoring(self, dashboard_mode: bool = True) -> None:
        """Start continuous monitoring."""
        self.is_running = True
        self.start_time = datetime.utcnow()
        
        self.logger.info(f"Starting health monitoring (interval: {self.check_interval}s)")
        
        try:
            while self.is_running:
                # Run monitoring cycle
                await self.run_monitoring_cycle()
                
                # Print dashboard if enabled
                if dashboard_mode:
                    self.print_dashboard()
                
                # Wait for next cycle
                await asyncio.sleep(self.check_interval)
                
        except asyncio.CancelledError:
            self.logger.info("Monitoring cancelled")
        except Exception as e:
            self.logger.error(f"Monitoring error: {e}")
        finally:
            self.is_running = False
            self.logger.info("Health monitoring stopped")
    
    def stop_monitoring(self) -> None:
        """Stop monitoring."""
        self.is_running = False
    
    def save_metrics_report(self, output_file: Optional[str] = None) -> str:
        """Save metrics report to a JSON file."""
        if output_file is None:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            output_file = f"agent_health_report_{self.environment}_{timestamp}.json"
        
        output_path = project_root / "tests" / "results" / output_file
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Prepare report data
        report_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "environment": self.environment,
            "monitoring_duration_seconds": (datetime.utcnow() - self.start_time).total_seconds() if self.start_time else 0,
            "current_status": self.get_current_status(),
            "performance_stats": self.performance_stats,
            "alerts_summary": {
                "total_alerts": len(self.alerts_history),
                "critical_alerts": len([a for a in self.alerts_history if a.get("severity") == "critical"]),
                "warning_alerts": len([a for a in self.alerts_history if a.get("severity") == "warning"]),
                "recent_alerts": self.alerts_history[-10:]
            },
            "metrics_summary": {
                "total_metrics": len(self.metrics_history),
                "metric_types": list(set(m.metric_name for m in self.metrics_history)),
                "time_range": {
                    "start": self.metrics_history[0].timestamp.isoformat() if self.metrics_history else None,
                    "end": self.metrics_history[-1].timestamp.isoformat() if self.metrics_history else None
                }
            }
        }
        
        with open(output_path, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        self.logger.info(f"Health report saved to: {output_path}")
        return str(output_path)


async def main():
    """Main function to run agent health monitoring."""
    parser = argparse.ArgumentParser(description="Monitor agent health and performance")
    parser.add_argument(
        "--environment", "-e",
        choices=["development", "staging", "production"],
        default="production",
        help="Environment to monitor (default: production)"
    )
    parser.add_argument(
        "--interval", "-i",
        type=int,
        default=60,
        help="Check interval in seconds (default: 60)"
    )
    parser.add_argument(
        "--duration", "-d",
        type=int,
        help="Monitoring duration in seconds (default: continuous)"
    )
    parser.add_argument(
        "--output", "-o",
        help="Output file for health report (default: auto-generated)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    parser.add_argument(
        "--no-dashboard",
        action="store_true",
        help="Disable dashboard display"
    )
    parser.add_argument(
        "--single-check",
        action="store_true",
        help="Run a single health check and exit"
    )
    
    args = parser.parse_args()
    
    # Initialize monitor
    monitor = AgentHealthMonitor(
        environment=args.environment,
        check_interval=args.interval,
        verbose=args.verbose
    )
    
    # Handle shutdown signals
    def signal_handler(signum, frame):
        print("\nShutdown signal received...")
        monitor.stop_monitoring()
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        if args.single_check:
            # Run single check
            print(f"Running single health check for {args.environment}...")
            monitor.start_time = datetime.utcnow()
            await monitor.run_monitoring_cycle()
            
            status = monitor.get_current_status()
            print(f"\nHealth Status: {status['overall_status'].upper()}")
            print(f"Recent Success Rate: {status['recent_success_rate']:.1f}%")
            
            if status['latest_metrics']:
                print("Latest Metrics:")
                for metric_name, value in status['latest_metrics'].items():
                    print(f"  {metric_name}: {value}")
            
            # Save report
            report_file = monitor.save_metrics_report(args.output)
            print(f"\nReport saved to: {report_file}")
            
        else:
            # Start continuous monitoring
            dashboard_mode = not args.no_dashboard
            
            if args.duration:
                # Monitor for specified duration
                print(f"Starting monitoring for {args.duration} seconds...")
                monitoring_task = asyncio.create_task(monitor.start_monitoring(dashboard_mode))
                
                await asyncio.sleep(args.duration)
                monitor.stop_monitoring()
                
                try:
                    await asyncio.wait_for(monitoring_task, timeout=5.0)
                except asyncio.TimeoutError:
                    monitoring_task.cancel()
            else:
                # Monitor continuously
                await monitor.start_monitoring(dashboard_mode)
            
            # Save final report
            report_file = monitor.save_metrics_report(args.output)
            print(f"\nFinal report saved to: {report_file}")
        
        sys.exit(0)
        
    except KeyboardInterrupt:
        print("\nMonitoring interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"Monitoring failed with error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())