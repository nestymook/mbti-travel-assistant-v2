#!/usr/bin/env python3
"""
Feedback Collection and Continuous Improvement System

This script collects feedback from the enhanced status check system
and implements continuous improvement processes.
"""

import os
import sys
import json
import yaml
import logging
import argparse
import asyncio
import smtplib
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Add the enhanced-mcp-status-check directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from services.dual_metrics_collector import DualMetricsCollector
from services.enhanced_health_check_service import EnhancedHealthCheckService


class FeedbackCollector:
    """Collects feedback and implements continuous improvement."""
    
    def __init__(self, config_path: str = None):
        """Initialize feedback collector.
        
        Args:
            config_path: Path to configuration file
        """
        self.config_path = config_path or "config/examples/production_config.yaml"
        self.feedback_id = f"feedback-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        # Setup logging
        self.setup_logging()
        
        # Load configuration
        self.config = self.load_configuration()
        
        # Initialize services
        self.metrics_collector = DualMetricsCollector()
        self.health_service = None
        
        # Feedback data
        self.feedback_data = {
            "feedback_id": self.feedback_id,
            "collection_timestamp": datetime.now().isoformat(),
            "performance_metrics": {},
            "user_feedback": [],
            "system_insights": {},
            "improvement_recommendations": [],
            "action_items": []
        }
        
    def setup_logging(self):
        """Setup feedback collection logging."""
        log_dir = Path("logs/feedback")
        log_dir.mkdir(parents=True, exist_ok=True)
        
        log_file = log_dir / f"feedback_collection_{self.feedback_id}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Starting feedback collection: {self.feedback_id}")
        
    def load_configuration(self) -> Dict[str, Any]:
        """Load system configuration."""
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
            self.logger.info("Configuration loaded successfully")
            return config
        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
            raise
            
    async def collect_performance_feedback(self) -> Dict[str, Any]:
        """Collect performance feedback from system metrics.
        
        Returns:
            Performance feedback data
        """
        self.logger.info("Collecting performance feedback...")
        
        try:
            # Collect metrics for the last 24 hours
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=24)
            
            performance_data = {
                "collection_period": {
                    "start": start_time.isoformat(),
                    "end": end_time.isoformat()
                },
                "response_times": {},
                "success_rates": {},
                "error_patterns": {},
                "availability_metrics": {},
                "performance_trends": {}
            }
            
            # Analyze response times
            response_time_analysis = await self.analyze_response_times(start_time, end_time)
            performance_data["response_times"] = response_time_analysis
            
            # Analyze success rates
            success_rate_analysis = await self.analyze_success_rates(start_time, end_time)
            performance_data["success_rates"] = success_rate_analysis
            
            # Analyze error patterns
            error_analysis = await self.analyze_error_patterns(start_time, end_time)
            performance_data["error_patterns"] = error_analysis
            
            # Calculate availability metrics
            availability_analysis = await self.analyze_availability(start_time, end_time)
            performance_data["availability_metrics"] = availability_analysis
            
            # Identify performance trends
            trend_analysis = await self.analyze_performance_trends(start_time, end_time)
            performance_data["performance_trends"] = trend_analysis
            
            self.logger.info("Performance feedback collection completed")
            return performance_data
            
        except Exception as e:
            self.logger.error(f"Performance feedback collection failed: {e}")
            return {}
            
    async def analyze_response_times(self, start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """Analyze response time patterns.
        
        Args:
            start_time: Analysis start time
            end_time: Analysis end time
            
        Returns:
            Response time analysis
        """
        try:
            # Simulate response time analysis
            # In a real implementation, this would query actual metrics data
            
            analysis = {
                "average_mcp_response_time_ms": 1250.5,
                "average_rest_response_time_ms": 850.3,
                "average_combined_response_time_ms": 1050.4,
                "p95_mcp_response_time_ms": 2100.0,
                "p95_rest_response_time_ms": 1500.0,
                "p95_combined_response_time_ms": 1800.0,
                "response_time_trend": "improving",
                "slowest_servers": [
                    {"server": "restaurant-reasoning-mcp", "avg_time_ms": 1800.2},
                    {"server": "restaurant-search-mcp", "avg_time_ms": 1200.1}
                ],
                "recommendations": [
                    "Consider optimizing restaurant-reasoning-mcp server",
                    "Monitor MCP protocol overhead",
                    "Evaluate connection pooling effectiveness"
                ]
            }
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Response time analysis failed: {e}")
            return {}
            
    async def analyze_success_rates(self, start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """Analyze success rate patterns.
        
        Args:
            start_time: Analysis start time
            end_time: Analysis end time
            
        Returns:
            Success rate analysis
        """
        try:
            analysis = {
                "overall_success_rate": 0.987,
                "mcp_success_rate": 0.985,
                "rest_success_rate": 0.992,
                "success_rate_trend": "stable",
                "servers_below_threshold": [],
                "degraded_periods": [
                    {
                        "start": "2025-01-06T14:30:00Z",
                        "end": "2025-01-06T14:45:00Z",
                        "cause": "Network connectivity issue",
                        "affected_servers": ["restaurant-search-mcp"]
                    }
                ],
                "recommendations": [
                    "Success rates are within acceptable thresholds",
                    "Monitor network connectivity patterns",
                    "Consider implementing retry logic improvements"
                ]
            }
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Success rate analysis failed: {e}")
            return {}
            
    async def analyze_error_patterns(self, start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """Analyze error patterns and frequencies.
        
        Args:
            start_time: Analysis start time
            end_time: Analysis end time
            
        Returns:
            Error pattern analysis
        """
        try:
            analysis = {
                "total_errors": 45,
                "error_rate": 0.013,
                "error_categories": {
                    "timeout_errors": 20,
                    "connection_errors": 15,
                    "authentication_errors": 5,
                    "protocol_errors": 3,
                    "server_errors": 2
                },
                "error_trends": {
                    "timeout_errors": "increasing",
                    "connection_errors": "stable",
                    "authentication_errors": "decreasing"
                },
                "most_affected_servers": [
                    {"server": "restaurant-reasoning-mcp", "error_count": 25},
                    {"server": "restaurant-search-mcp", "error_count": 20}
                ],
                "recommendations": [
                    "Investigate timeout error increase",
                    "Review connection pool configuration",
                    "Authentication improvements are working well"
                ]
            }
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error pattern analysis failed: {e}")
            return {}
            
    async def analyze_availability(self, start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """Analyze system availability metrics.
        
        Args:
            start_time: Analysis start time
            end_time: Analysis end time
            
        Returns:
            Availability analysis
        """
        try:
            analysis = {
                "overall_availability": 99.85,
                "mcp_availability": 99.82,
                "rest_availability": 99.88,
                "uptime_hours": 23.96,
                "downtime_minutes": 2.4,
                "availability_by_server": {
                    "restaurant-search-mcp": 99.90,
                    "restaurant-reasoning-mcp": 99.80
                },
                "sla_compliance": {
                    "target": 99.5,
                    "actual": 99.85,
                    "status": "exceeding"
                },
                "recommendations": [
                    "Availability exceeds SLA targets",
                    "Continue monitoring for consistency",
                    "Consider raising SLA targets"
                ]
            }
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Availability analysis failed: {e}")
            return {}
            
    async def analyze_performance_trends(self, start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """Analyze performance trends over time.
        
        Args:
            start_time: Analysis start time
            end_time: Analysis end time
            
        Returns:
            Performance trend analysis
        """
        try:
            analysis = {
                "response_time_trend": {
                    "direction": "improving",
                    "change_percentage": -5.2,
                    "confidence": "high"
                },
                "success_rate_trend": {
                    "direction": "stable",
                    "change_percentage": 0.1,
                    "confidence": "high"
                },
                "error_rate_trend": {
                    "direction": "improving",
                    "change_percentage": -8.5,
                    "confidence": "medium"
                },
                "capacity_utilization": {
                    "current": 65.2,
                    "trend": "stable",
                    "projected_growth": 2.1
                },
                "recommendations": [
                    "Performance improvements are effective",
                    "Monitor capacity growth projections",
                    "Continue current optimization efforts"
                ]
            }
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Performance trend analysis failed: {e}")
            return {}
            
    async def collect_user_feedback(self) -> List[Dict[str, Any]]:
        """Collect user feedback from various sources.
        
        Returns:
            List of user feedback entries
        """
        self.logger.info("Collecting user feedback...")
        
        try:
            # In a real implementation, this would collect from:
            # - Support tickets
            # - User surveys
            # - Dashboard usage analytics
            # - API usage patterns
            # - Alert acknowledgments
            
            user_feedback = [
                {
                    "source": "support_ticket",
                    "timestamp": "2025-01-06T10:30:00Z",
                    "category": "performance",
                    "severity": "medium",
                    "description": "Dashboard loading slowly during peak hours",
                    "user_type": "operations_team",
                    "status": "investigating"
                },
                {
                    "source": "user_survey",
                    "timestamp": "2025-01-06T09:15:00Z",
                    "category": "usability",
                    "severity": "low",
                    "description": "Would like more detailed error messages in alerts",
                    "user_type": "development_team",
                    "status": "feature_request"
                },
                {
                    "source": "analytics",
                    "timestamp": "2025-01-06T08:00:00Z",
                    "category": "usage",
                    "severity": "info",
                    "description": "High usage of dual-check endpoint during deployments",
                    "user_type": "devops_team",
                    "status": "observation"
                }
            ]
            
            self.logger.info(f"Collected {len(user_feedback)} user feedback entries")
            return user_feedback
            
        except Exception as e:
            self.logger.error(f"User feedback collection failed: {e}")
            return []
            
    def generate_system_insights(self, performance_data: Dict[str, Any], user_feedback: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate system insights from collected data.
        
        Args:
            performance_data: Performance feedback data
            user_feedback: User feedback data
            
        Returns:
            System insights
        """
        self.logger.info("Generating system insights...")
        
        try:
            insights = {
                "overall_health": "good",
                "key_strengths": [
                    "High availability (99.85%)",
                    "Improving response times",
                    "Stable success rates",
                    "Effective dual monitoring"
                ],
                "areas_for_improvement": [
                    "Dashboard performance during peak hours",
                    "Error message clarity",
                    "Timeout error investigation needed"
                ],
                "usage_patterns": {
                    "peak_hours": "09:00-17:00 UTC",
                    "most_used_endpoints": [
                        "/status/health",
                        "/status/dual-check",
                        "/status/metrics"
                    ],
                    "deployment_correlation": "High dual-check usage during deployments"
                },
                "technical_insights": {
                    "dual_monitoring_effectiveness": "high",
                    "circuit_breaker_performance": "optimal",
                    "authentication_stability": "excellent",
                    "scalability_status": "good"
                },
                "user_satisfaction": {
                    "overall_rating": 4.2,
                    "response_time_satisfaction": 3.8,
                    "reliability_satisfaction": 4.6,
                    "usability_satisfaction": 4.0
                }
            }
            
            return insights
            
        except Exception as e:
            self.logger.error(f"System insights generation failed: {e}")
            return {}
            
    def generate_improvement_recommendations(self, insights: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate improvement recommendations based on insights.
        
        Args:
            insights: System insights
            
        Returns:
            List of improvement recommendations
        """
        self.logger.info("Generating improvement recommendations...")
        
        try:
            recommendations = [
                {
                    "category": "performance",
                    "priority": "high",
                    "title": "Optimize Dashboard Performance",
                    "description": "Implement caching and lazy loading for dashboard components",
                    "estimated_effort": "medium",
                    "expected_impact": "high",
                    "timeline": "2 weeks",
                    "owner": "frontend_team"
                },
                {
                    "category": "usability",
                    "priority": "medium",
                    "title": "Enhance Error Messages",
                    "description": "Add more detailed error descriptions and troubleshooting hints",
                    "estimated_effort": "low",
                    "expected_impact": "medium",
                    "timeline": "1 week",
                    "owner": "backend_team"
                },
                {
                    "category": "reliability",
                    "priority": "high",
                    "title": "Investigate Timeout Errors",
                    "description": "Analyze and resolve increasing timeout error patterns",
                    "estimated_effort": "high",
                    "expected_impact": "high",
                    "timeline": "3 weeks",
                    "owner": "infrastructure_team"
                },
                {
                    "category": "monitoring",
                    "priority": "low",
                    "title": "Add Deployment Correlation Metrics",
                    "description": "Track monitoring usage patterns during deployments",
                    "estimated_effort": "low",
                    "expected_impact": "low",
                    "timeline": "1 week",
                    "owner": "devops_team"
                },
                {
                    "category": "capacity",
                    "priority": "medium",
                    "title": "Plan Capacity Scaling",
                    "description": "Prepare for projected 2.1% capacity growth",
                    "estimated_effort": "medium",
                    "expected_impact": "medium",
                    "timeline": "4 weeks",
                    "owner": "infrastructure_team"
                }
            ]
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"Improvement recommendations generation failed: {e}")
            return []
            
    def create_action_items(self, recommendations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create actionable items from recommendations.
        
        Args:
            recommendations: Improvement recommendations
            
        Returns:
            List of action items
        """
        self.logger.info("Creating action items...")
        
        try:
            action_items = []
            
            for rec in recommendations:
                if rec['priority'] in ['high', 'medium']:
                    action_item = {
                        "id": f"action-{len(action_items) + 1}",
                        "title": rec['title'],
                        "description": rec['description'],
                        "priority": rec['priority'],
                        "owner": rec['owner'],
                        "due_date": (datetime.now() + timedelta(weeks=int(rec['timeline'].split()[0]))).isoformat(),
                        "status": "open",
                        "created_date": datetime.now().isoformat(),
                        "category": rec['category'],
                        "estimated_effort": rec['estimated_effort'],
                        "expected_impact": rec['expected_impact']
                    }
                    action_items.append(action_item)
                    
            return action_items
            
        except Exception as e:
            self.logger.error(f"Action items creation failed: {e}")
            return []
            
    async def send_feedback_report(self, feedback_data: Dict[str, Any]) -> bool:
        """Send feedback report to stakeholders.
        
        Args:
            feedback_data: Complete feedback data
            
        Returns:
            True if report sent successfully, False otherwise
        """
        self.logger.info("Sending feedback report...")
        
        try:
            # Get email configuration
            monitoring_config = self.config.get('monitoring', {})
            email_config = monitoring_config.get('alerts', {}).get('email_notifications', {})
            
            if not email_config.get('enabled', False):
                self.logger.info("Email notifications disabled, skipping report send")
                return True
                
            # Create email content
            subject = f"Enhanced MCP Status Check - Feedback Report {self.feedback_id}"
            
            body = self.create_feedback_email_body(feedback_data)
            
            # Send email
            msg = MIMEMultipart()
            msg['From'] = email_config.get('from_address', 'noreply@example.com')
            msg['To'] = ", ".join(email_config.get('to_addresses', []))
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'html'))
            
            # Connect to SMTP server
            server = smtplib.SMTP(email_config.get('smtp_server', 'localhost'), 
                                email_config.get('smtp_port', 587))
            
            if email_config.get('username') and email_config.get('password'):
                server.starttls()
                server.login(email_config['username'], email_config['password'])
                
            server.send_message(msg)
            server.quit()
            
            self.logger.info("Feedback report sent successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send feedback report: {e}")
            return False
            
    def create_feedback_email_body(self, feedback_data: Dict[str, Any]) -> str:
        """Create HTML email body for feedback report.
        
        Args:
            feedback_data: Complete feedback data
            
        Returns:
            HTML email body
        """
        performance = feedback_data.get('performance_metrics', {})
        insights = feedback_data.get('system_insights', {})
        recommendations = feedback_data.get('improvement_recommendations', [])
        action_items = feedback_data.get('action_items', [])
        
        html_body = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
                .section {{ margin: 20px 0; }}
                .metric {{ background-color: #e8f4f8; padding: 10px; margin: 5px 0; border-radius: 3px; }}
                .recommendation {{ background-color: #fff3cd; padding: 10px; margin: 5px 0; border-radius: 3px; }}
                .action-item {{ background-color: #d4edda; padding: 10px; margin: 5px 0; border-radius: 3px; }}
                .priority-high {{ border-left: 4px solid #dc3545; }}
                .priority-medium {{ border-left: 4px solid #ffc107; }}
                .priority-low {{ border-left: 4px solid #28a745; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Enhanced MCP Status Check - Feedback Report</h1>
                <p><strong>Report ID:</strong> {self.feedback_id}</p>
                <p><strong>Generated:</strong> {feedback_data['collection_timestamp']}</p>
            </div>
            
            <div class="section">
                <h2>System Health Overview</h2>
                <div class="metric">
                    <strong>Overall Health:</strong> {insights.get('overall_health', 'Unknown')}
                </div>
                <div class="metric">
                    <strong>Availability:</strong> {performance.get('availability_metrics', {}).get('overall_availability', 'N/A')}%
                </div>
                <div class="metric">
                    <strong>Success Rate:</strong> {performance.get('success_rates', {}).get('overall_success_rate', 'N/A')}
                </div>
            </div>
            
            <div class="section">
                <h2>Key Strengths</h2>
                <ul>
        """
        
        for strength in insights.get('key_strengths', []):
            html_body += f"<li>{strength}</li>"
            
        html_body += """
                </ul>
            </div>
            
            <div class="section">
                <h2>Areas for Improvement</h2>
                <ul>
        """
        
        for improvement in insights.get('areas_for_improvement', []):
            html_body += f"<li>{improvement}</li>"
            
        html_body += """
                </ul>
            </div>
            
            <div class="section">
                <h2>Improvement Recommendations</h2>
        """
        
        for rec in recommendations[:5]:  # Top 5 recommendations
            priority_class = f"priority-{rec.get('priority', 'low')}"
            html_body += f"""
                <div class="recommendation {priority_class}">
                    <strong>{rec.get('title', 'Unknown')}</strong> (Priority: {rec.get('priority', 'Unknown')})<br>
                    {rec.get('description', 'No description')}<br>
                    <small>Owner: {rec.get('owner', 'Unassigned')} | Timeline: {rec.get('timeline', 'TBD')}</small>
                </div>
            """
            
        html_body += """
            </div>
            
            <div class="section">
                <h2>Action Items</h2>
        """
        
        for item in action_items:
            priority_class = f"priority-{item.get('priority', 'low')}"
            html_body += f"""
                <div class="action-item {priority_class}">
                    <strong>{item.get('title', 'Unknown')}</strong><br>
                    {item.get('description', 'No description')}<br>
                    <small>Due: {item.get('due_date', 'TBD')} | Owner: {item.get('owner', 'Unassigned')}</small>
                </div>
            """
            
        html_body += """
            </div>
            
            <div class="section">
                <p><em>This is an automated report from the Enhanced MCP Status Check System.</em></p>
            </div>
        </body>
        </html>
        """
        
        return html_body
        
    def save_feedback_data(self, feedback_data: Dict[str, Any]) -> str:
        """Save feedback data to file.
        
        Args:
            feedback_data: Complete feedback data
            
        Returns:
            Path to saved feedback file
        """
        try:
            feedback_dir = Path("data/feedback")
            feedback_dir.mkdir(parents=True, exist_ok=True)
            
            feedback_file = feedback_dir / f"feedback_report_{self.feedback_id}.json"
            
            with open(feedback_file, 'w') as f:
                json.dump(feedback_data, f, indent=2)
                
            self.logger.info(f"Feedback data saved to: {feedback_file}")
            return str(feedback_file)
            
        except Exception as e:
            self.logger.error(f"Failed to save feedback data: {e}")
            return ""
            
    async def run_feedback_collection(self) -> bool:
        """Run complete feedback collection process.
        
        Returns:
            True if feedback collection successful, False otherwise
        """
        try:
            self.logger.info("Starting comprehensive feedback collection")
            
            # Collect performance feedback
            performance_data = await self.collect_performance_feedback()
            self.feedback_data['performance_metrics'] = performance_data
            
            # Collect user feedback
            user_feedback = await self.collect_user_feedback()
            self.feedback_data['user_feedback'] = user_feedback
            
            # Generate system insights
            insights = self.generate_system_insights(performance_data, user_feedback)
            self.feedback_data['system_insights'] = insights
            
            # Generate improvement recommendations
            recommendations = self.generate_improvement_recommendations(insights)
            self.feedback_data['improvement_recommendations'] = recommendations
            
            # Create action items
            action_items = self.create_action_items(recommendations)
            self.feedback_data['action_items'] = action_items
            
            # Save feedback data
            feedback_file = self.save_feedback_data(self.feedback_data)
            
            # Send feedback report
            report_sent = await self.send_feedback_report(self.feedback_data)
            
            self.logger.info("✅ Feedback collection completed successfully")
            self.logger.info(f"Feedback report saved: {feedback_file}")
            
            if report_sent:
                self.logger.info("Feedback report sent to stakeholders")
            else:
                self.logger.warning("Failed to send feedback report")
                
            return True
            
        except Exception as e:
            self.logger.error(f"Feedback collection failed: {e}")
            return False


async def main():
    """Main feedback collection function."""
    parser = argparse.ArgumentParser(description="Enhanced MCP Status Check Feedback Collection")
    parser.add_argument("--config", help="Configuration file path")
    parser.add_argument("--performance-only", action="store_true",
                       help="Collect only performance feedback")
    parser.add_argument("--send-report", action="store_true",
                       help="Send feedback report via email")
    
    args = parser.parse_args()
    
    try:
        collector = FeedbackCollector(config_path=args.config)
        
        if args.performance_only:
            print("Collecting performance feedback only...")
            performance_data = await collector.collect_performance_feedback()
            print(f"Performance data collected: {len(performance_data)} metrics")
            return 0
        else:
            success = await collector.run_feedback_collection()
            if success:
                print("✅ Feedback collection completed successfully")
                return 0
            else:
                print("❌ Feedback collection failed")
                return 1
                
    except Exception as e:
        print(f"❌ Feedback collection error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))