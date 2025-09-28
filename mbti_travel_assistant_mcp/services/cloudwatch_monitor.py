"""
CloudWatch Integration Service

This module provides CloudWatch integration for metrics, logs, and alarms
for the MBTI Travel Assistant MCP service.
"""

import asyncio
import logging
import json
import time
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

import boto3
from botocore.exceptions import ClientError, NoCredentialsError

logger = logging.getLogger(__name__)


class MetricUnit(Enum):
    """CloudWatch metric units"""
    SECONDS = "Seconds"
    MILLISECONDS = "Milliseconds"
    MICROSECONDS = "Microseconds"
    COUNT = "Count"
    PERCENT = "Percent"
    BYTES = "Bytes"
    KILOBYTES = "Kilobytes"
    MEGABYTES = "Megabytes"
    GIGABYTES = "Gigabytes"
    BYTES_PER_SECOND = "Bytes/Second"
    COUNT_PER_SECOND = "Count/Second"


@dataclass
class CloudWatchMetric:
    """CloudWatch metric data point"""
    metric_name: str
    value: float
    unit: MetricUnit
    dimensions: Dict[str, str]
    timestamp: Optional[datetime] = None
    namespace: str = "MBTI/TravelAssistant"


@dataclass
class AlarmConfiguration:
    """CloudWatch alarm configuration"""
    alarm_name: str
    metric_name: str
    namespace: str
    statistic: str
    threshold: float
    comparison_operator: str
    evaluation_periods: int
    period: int
    dimensions: Dict[str, str]
    alarm_description: str
    treat_missing_data: str = "notBreaching"
    actions_enabled: bool = True
    alarm_actions: List[str] = None
    ok_actions: List[str] = None


class CloudWatchMonitor:
    """
    CloudWatch integration service for metrics, logs, and alarms.
    
    Provides methods to send custom metrics, create alarms, and manage
    CloudWatch dashboards for the MBTI Travel Assistant.
    """
    
    def __init__(
        self,
        region: str = "us-east-1",
        namespace: str = "MBTI/TravelAssistant",
        environment: str = "development"
    ):
        """
        Initialize CloudWatch monitor.
        
        Args:
            region: AWS region
            namespace: CloudWatch namespace for metrics
            environment: Environment name (development, staging, production)
        """
        self.region = region
        self.namespace = namespace
        self.environment = environment
        
        try:
            self.session = boto3.Session()
            self.cloudwatch = self.session.client('cloudwatch', region_name=region)
            self.logs = self.session.client('logs', region_name=region)
            
            # Verify credentials
            self.cloudwatch.list_metrics(Namespace=namespace, MaxRecords=1)
            logger.info(f"Initialized CloudWatch monitor for {environment} in {region}")
            
        except NoCredentialsError:
            logger.error("AWS credentials not found for CloudWatch integration")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize CloudWatch monitor: {e}")
            raise
    
    def put_metric(
        self,
        metric_name: str,
        value: float,
        unit: MetricUnit,
        dimensions: Optional[Dict[str, str]] = None,
        timestamp: Optional[datetime] = None
    ) -> bool:
        """
        Send a single metric to CloudWatch.
        
        Args:
            metric_name: Name of the metric
            value: Metric value
            unit: Metric unit
            dimensions: Optional dimensions for the metric
            timestamp: Optional timestamp (defaults to now)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            metric_data = {
                'MetricName': metric_name,
                'Value': value,
                'Unit': unit.value
            }
            
            if dimensions:
                metric_data['Dimensions'] = [
                    {'Name': k, 'Value': v} for k, v in dimensions.items()
                ]
            
            if timestamp:
                metric_data['Timestamp'] = timestamp
            
            self.cloudwatch.put_metric_data(
                Namespace=self.namespace,
                MetricData=[metric_data]
            )
            
            logger.debug(f"Sent metric to CloudWatch: {metric_name} = {value}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send metric to CloudWatch: {e}")
            return False
    
    def put_metrics_batch(self, metrics: List[CloudWatchMetric]) -> bool:
        """
        Send multiple metrics to CloudWatch in a batch.
        
        Args:
            metrics: List of CloudWatch metrics
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # CloudWatch allows max 20 metrics per batch
            batch_size = 20
            
            for i in range(0, len(metrics), batch_size):
                batch = metrics[i:i + batch_size]
                metric_data = []
                
                for metric in batch:
                    data = {
                        'MetricName': metric.metric_name,
                        'Value': metric.value,
                        'Unit': metric.unit.value
                    }
                    
                    if metric.dimensions:
                        data['Dimensions'] = [
                            {'Name': k, 'Value': v} for k, v in metric.dimensions.items()
                        ]
                    
                    if metric.timestamp:
                        data['Timestamp'] = metric.timestamp
                    
                    metric_data.append(data)
                
                self.cloudwatch.put_metric_data(
                    Namespace=metric.namespace or self.namespace,
                    MetricData=metric_data
                )
            
            logger.debug(f"Sent {len(metrics)} metrics to CloudWatch in batches")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send metrics batch to CloudWatch: {e}")
            return False
    
    def create_alarm(self, alarm_config: AlarmConfiguration) -> bool:
        """
        Create a CloudWatch alarm.
        
        Args:
            alarm_config: Alarm configuration
            
        Returns:
            True if successful, False otherwise
        """
        try:
            alarm_params = {
                'AlarmName': alarm_config.alarm_name,
                'ComparisonOperator': alarm_config.comparison_operator,
                'EvaluationPeriods': alarm_config.evaluation_periods,
                'MetricName': alarm_config.metric_name,
                'Namespace': alarm_config.namespace,
                'Period': alarm_config.period,
                'Statistic': alarm_config.statistic,
                'Threshold': alarm_config.threshold,
                'ActionsEnabled': alarm_config.actions_enabled,
                'AlarmDescription': alarm_config.alarm_description,
                'TreatMissingData': alarm_config.treat_missing_data
            }
            
            if alarm_config.dimensions:
                alarm_params['Dimensions'] = [
                    {'Name': k, 'Value': v} for k, v in alarm_config.dimensions.items()
                ]
            
            if alarm_config.alarm_actions:
                alarm_params['AlarmActions'] = alarm_config.alarm_actions
            
            if alarm_config.ok_actions:
                alarm_params['OKActions'] = alarm_config.ok_actions
            
            self.cloudwatch.put_metric_alarm(**alarm_params)
            
            logger.info(f"Created CloudWatch alarm: {alarm_config.alarm_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create CloudWatch alarm: {e}")
            return False
    
    def create_standard_alarms(self, agent_name: str) -> List[str]:
        """
        Create standard set of alarms for the MBTI Travel Assistant.
        
        Args:
            agent_name: Name of the agent for alarm naming
            
        Returns:
            List of created alarm names
        """
        created_alarms = []
        
        # Standard alarm configurations
        alarm_configs = [
            # High error rate alarm
            AlarmConfiguration(
                alarm_name=f"{agent_name}-{self.environment}-high-error-rate",
                metric_name="ErrorRate",
                namespace=self.namespace,
                statistic="Average",
                threshold=0.05,  # 5% error rate
                comparison_operator="GreaterThanThreshold",
                evaluation_periods=2,
                period=300,  # 5 minutes
                dimensions={"Environment": self.environment, "Service": agent_name},
                alarm_description=f"High error rate for {agent_name} in {self.environment}"
            ),
            
            # High response time alarm
            AlarmConfiguration(
                alarm_name=f"{agent_name}-{self.environment}-high-response-time",
                metric_name="ResponseTime",
                namespace=self.namespace,
                statistic="Average",
                threshold=5.0,  # 5 seconds
                comparison_operator="GreaterThanThreshold",
                evaluation_periods=2,
                period=300,
                dimensions={"Environment": self.environment, "Service": agent_name},
                alarm_description=f"High response time for {agent_name} in {self.environment}"
            ),
            
            # Low throughput alarm
            AlarmConfiguration(
                alarm_name=f"{agent_name}-{self.environment}-low-throughput",
                metric_name="Throughput",
                namespace=self.namespace,
                statistic="Average",
                threshold=1.0,  # 1 request per second
                comparison_operator="LessThanThreshold",
                evaluation_periods=3,
                period=300,
                dimensions={"Environment": self.environment, "Service": agent_name},
                alarm_description=f"Low throughput for {agent_name} in {self.environment}"
            ),
            
            # High memory usage alarm
            AlarmConfiguration(
                alarm_name=f"{agent_name}-{self.environment}-high-memory-usage",
                metric_name="MemoryUsage",
                namespace=self.namespace,
                statistic="Average",
                threshold=80.0,  # 80% memory usage
                comparison_operator="GreaterThanThreshold",
                evaluation_periods=2,
                period=300,
                dimensions={"Environment": self.environment, "Service": agent_name},
                alarm_description=f"High memory usage for {agent_name} in {self.environment}"
            ),
            
            # MCP connection failures alarm
            AlarmConfiguration(
                alarm_name=f"{agent_name}-{self.environment}-mcp-connection-failures",
                metric_name="MCPConnectionFailures",
                namespace=self.namespace,
                statistic="Sum",
                threshold=5.0,  # 5 failures in 5 minutes
                comparison_operator="GreaterThanThreshold",
                evaluation_periods=1,
                period=300,
                dimensions={"Environment": self.environment, "Service": agent_name},
                alarm_description=f"MCP connection failures for {agent_name} in {self.environment}"
            )
        ]
        
        for alarm_config in alarm_configs:
            if self.create_alarm(alarm_config):
                created_alarms.append(alarm_config.alarm_name)
        
        logger.info(f"Created {len(created_alarms)} standard alarms")
        return created_alarms
    
    def create_dashboard(self, agent_name: str) -> bool:
        """
        Create a CloudWatch dashboard for the MBTI Travel Assistant.
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            True if successful, False otherwise
        """
        try:
            dashboard_name = f"{agent_name}-{self.environment}-dashboard"
            
            dashboard_body = {
                "widgets": [
                    # Response time widget
                    {
                        "type": "metric",
                        "x": 0,
                        "y": 0,
                        "width": 12,
                        "height": 6,
                        "properties": {
                            "metrics": [
                                [self.namespace, "ResponseTime", "Environment", self.environment, "Service", agent_name],
                                [".", "MCPCallDuration", ".", ".", ".", ".", "Server", "search-mcp"],
                                [".", ".", ".", ".", ".", ".", "Server", "reasoning-mcp"]
                            ],
                            "period": 300,
                            "stat": "Average",
                            "region": self.region,
                            "title": "Response Times",
                            "yAxis": {
                                "left": {
                                    "min": 0
                                }
                            }
                        }
                    },
                    
                    # Error rate widget
                    {
                        "type": "metric",
                        "x": 12,
                        "y": 0,
                        "width": 12,
                        "height": 6,
                        "properties": {
                            "metrics": [
                                [self.namespace, "ErrorRate", "Environment", self.environment, "Service", agent_name],
                                [".", "MCPErrorRate", ".", ".", ".", ".", "Server", "search-mcp"],
                                [".", ".", ".", ".", ".", ".", "Server", "reasoning-mcp"]
                            ],
                            "period": 300,
                            "stat": "Average",
                            "region": self.region,
                            "title": "Error Rates",
                            "yAxis": {
                                "left": {
                                    "min": 0,
                                    "max": 1
                                }
                            }
                        }
                    },
                    
                    # Throughput widget
                    {
                        "type": "metric",
                        "x": 0,
                        "y": 6,
                        "width": 12,
                        "height": 6,
                        "properties": {
                            "metrics": [
                                [self.namespace, "Throughput", "Environment", self.environment, "Service", agent_name],
                                [".", "RequestCount", ".", ".", ".", "."]
                            ],
                            "period": 300,
                            "stat": "Sum",
                            "region": self.region,
                            "title": "Throughput",
                            "yAxis": {
                                "left": {
                                    "min": 0
                                }
                            }
                        }
                    },
                    
                    # System resources widget
                    {
                        "type": "metric",
                        "x": 12,
                        "y": 6,
                        "width": 12,
                        "height": 6,
                        "properties": {
                            "metrics": [
                                [self.namespace, "CPUUsage", "Environment", self.environment, "Service", agent_name],
                                [".", "MemoryUsage", ".", ".", ".", "."]
                            ],
                            "period": 300,
                            "stat": "Average",
                            "region": self.region,
                            "title": "System Resources",
                            "yAxis": {
                                "left": {
                                    "min": 0,
                                    "max": 100
                                }
                            }
                        }
                    },
                    
                    # Cache performance widget
                    {
                        "type": "metric",
                        "x": 0,
                        "y": 12,
                        "width": 12,
                        "height": 6,
                        "properties": {
                            "metrics": [
                                [self.namespace, "CacheHitRate", "Environment", self.environment, "Service", agent_name],
                                [".", "CacheSize", ".", ".", ".", "."]
                            ],
                            "period": 300,
                            "stat": "Average",
                            "region": self.region,
                            "title": "Cache Performance"
                        }
                    },
                    
                    # Logs widget
                    {
                        "type": "log",
                        "x": 12,
                        "y": 12,
                        "width": 12,
                        "height": 6,
                        "properties": {
                            "query": f"SOURCE '/aws/lambda/{agent_name}-{self.environment}'\n| fields @timestamp, @message\n| filter @message like /ERROR/\n| sort @timestamp desc\n| limit 100",
                            "region": self.region,
                            "title": "Recent Errors",
                            "view": "table"
                        }
                    }
                ]
            }
            
            self.cloudwatch.put_dashboard(
                DashboardName=dashboard_name,
                DashboardBody=json.dumps(dashboard_body)
            )
            
            logger.info(f"Created CloudWatch dashboard: {dashboard_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create CloudWatch dashboard: {e}")
            return False
    
    def create_log_group(self, log_group_name: str, retention_days: int = 7) -> bool:
        """
        Create a CloudWatch log group.
        
        Args:
            log_group_name: Name of the log group
            retention_days: Log retention period in days
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if log group already exists
            try:
                self.logs.describe_log_groups(logGroupNamePrefix=log_group_name)
                logger.info(f"Log group already exists: {log_group_name}")
                return True
            except ClientError as e:
                if e.response['Error']['Code'] != 'ResourceNotFoundException':
                    raise
            
            # Create log group
            self.logs.create_log_group(logGroupName=log_group_name)
            
            # Set retention policy
            self.logs.put_retention_policy(
                logGroupName=log_group_name,
                retentionInDays=retention_days
            )
            
            logger.info(f"Created log group: {log_group_name} with {retention_days} days retention")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create log group: {e}")
            return False
    
    def send_log_event(
        self,
        log_group_name: str,
        log_stream_name: str,
        message: str,
        timestamp: Optional[int] = None
    ) -> bool:
        """
        Send a log event to CloudWatch Logs.
        
        Args:
            log_group_name: Name of the log group
            log_stream_name: Name of the log stream
            message: Log message
            timestamp: Optional timestamp (milliseconds since epoch)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create log stream if it doesn't exist
            try:
                self.logs.create_log_stream(
                    logGroupName=log_group_name,
                    logStreamName=log_stream_name
                )
            except ClientError as e:
                if e.response['Error']['Code'] != 'ResourceAlreadyExistsException':
                    raise
            
            # Get sequence token
            response = self.logs.describe_log_streams(
                logGroupName=log_group_name,
                logStreamNamePrefix=log_stream_name
            )
            
            sequence_token = None
            for stream in response['logStreams']:
                if stream['logStreamName'] == log_stream_name:
                    sequence_token = stream.get('uploadSequenceToken')
                    break
            
            # Send log event
            log_event = {
                'timestamp': timestamp or int(time.time() * 1000),
                'message': message
            }
            
            put_params = {
                'logGroupName': log_group_name,
                'logStreamName': log_stream_name,
                'logEvents': [log_event]
            }
            
            if sequence_token:
                put_params['sequenceToken'] = sequence_token
            
            self.logs.put_log_events(**put_params)
            
            logger.debug(f"Sent log event to CloudWatch: {log_group_name}/{log_stream_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send log event to CloudWatch: {e}")
            return False
    
    def get_metric_statistics(
        self,
        metric_name: str,
        start_time: datetime,
        end_time: datetime,
        period: int = 300,
        statistic: str = "Average",
        dimensions: Optional[Dict[str, str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get metric statistics from CloudWatch.
        
        Args:
            metric_name: Name of the metric
            start_time: Start time for statistics
            end_time: End time for statistics
            period: Period in seconds
            statistic: Statistic type (Average, Sum, Maximum, etc.)
            dimensions: Optional dimensions filter
            
        Returns:
            List of metric data points
        """
        try:
            params = {
                'Namespace': self.namespace,
                'MetricName': metric_name,
                'StartTime': start_time,
                'EndTime': end_time,
                'Period': period,
                'Statistics': [statistic]
            }
            
            if dimensions:
                params['Dimensions'] = [
                    {'Name': k, 'Value': v} for k, v in dimensions.items()
                ]
            
            response = self.cloudwatch.get_metric_statistics(**params)
            
            # Sort by timestamp
            datapoints = sorted(response['Datapoints'], key=lambda x: x['Timestamp'])
            
            return datapoints
            
        except Exception as e:
            logger.error(f"Failed to get metric statistics: {e}")
            return []
    
    def get_alarm_history(
        self,
        alarm_name: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Get alarm history from CloudWatch.
        
        Args:
            alarm_name: Name of the alarm
            start_time: Optional start time
            end_time: Optional end time
            
        Returns:
            List of alarm history items
        """
        try:
            params = {'AlarmName': alarm_name}
            
            if start_time:
                params['StartDate'] = start_time
            if end_time:
                params['EndDate'] = end_time
            
            response = self.cloudwatch.describe_alarm_history(**params)
            
            return response['AlarmHistoryItems']
            
        except Exception as e:
            logger.error(f"Failed to get alarm history: {e}")
            return []
    
    def cleanup_old_metrics(self, days_to_keep: int = 7) -> bool:
        """
        Clean up old metrics (placeholder - CloudWatch handles retention automatically).
        
        Args:
            days_to_keep: Number of days to keep metrics
            
        Returns:
            True (CloudWatch handles retention automatically)
        """
        logger.info(f"CloudWatch automatically handles metric retention (typically 15 months)")
        return True