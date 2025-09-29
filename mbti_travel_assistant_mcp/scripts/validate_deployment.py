#!/usr/bin/env python3
"""
Deployment Validation Script

This script validates the deployment of the MBTI Travel Assistant MCP
to ensure all components are working correctly and meet performance
and functionality requirements.
"""

import asyncio
import logging
import json
import time
import sys
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from pathlib import Path

import aiohttp
import boto3
from botocore.exceptions import ClientError

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.health_check import HealthChecker, HealthStatus
from services.cloudwatch_monitor import CloudWatchMonitor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DeploymentValidator:
    """
    Validates MBTI Travel Assistant deployment.
    
    Performs comprehensive validation including health checks,
    performance testing, functionality verification, and
    monitoring validation.
    """
    
    def __init__(
        self,
        environment: str,
        agent_name: str,
        region: str = "us-east-1",
        endpoint_url: Optional[str] = None
    ):
        """
        Initialize deployment validator.
        
        Args:
            environment: Environment name
            agent_name: Agent name
            region: AWS region
            endpoint_url: Optional endpoint URL for testing
        """
        self.environment = environment
        self.agent_name = agent_name
        self.region = region
        self.endpoint_url = endpoint_url
        
        # Initialize AWS clients
        self.session = boto3.Session()
        self.cloudwatch = self.session.client('cloudwatch', region_name=region)
        
        # Validation configuration
        self.validation_config = self._load_validation_config()
        
        logger.info(f"Initialized DeploymentValidator for {agent_name} in {environment}")
    
    def _load_validation_config(self) -> Dict[str, Any]:
        """Load validation configuration"""
        config_file = Path(f"config/validation_{self.environment}.json")
        
        if config_file.exists():
            with open(config_file, 'r') as f:
                return json.load(f)
        
        # Default validation configuration
        return {
            "response_time": {
                "max_response_time_ms": 10000 if self.environment == "development" else 5000,
                "percentile_threshold": 95
            },
            "error_rate": {
                "max_error_rate": 0.1 if self.environment == "development" else 0.05,
                "measurement_period_minutes": 5
            },
            "availability": {
                "min_uptime_percentage": 95.0 if self.environment == "development" else 99.0,
                "measurement_period_hours": 1
            }
        }
    
    async def validate_complete_deployment(self) -> Dict[str, Any]:
        """
        Perform complete deployment validation.
        
        Returns:
            Validation result dictionary
        """
        logger.info("Starting complete deployment validation")
        
        validation_result = {
            "timestamp": datetime.utcnow().isoformat(),
            "environment": self.environment,
            "agent_name": self.agent_name,
            "region": self.region,
            "validations": {}
        }
        
        try:
            # 1. Health check validation
            logger.info("Validation 1: Health checks")
            health_result = await self._validate_health_checks()
            validation_result["validations"]["health_checks"] = health_result
            
            # 2. Endpoint connectivity validation
            logger.info("Validation 2: Endpoint connectivity")
            connectivity_result = await self._validate_endpoint_connectivity()
            validation_result["validations"]["connectivity"] = connectivity_result
            
            # 3. Performance validation
            logger.info("Validation 3: Performance metrics")
            performance_result = await self._validate_performance()
            validation_result["validations"]["performance"] = performance_result
            
            # 4. Functionality validation
            logger.info("Validation 4: Functionality tests")
            functionality_result = await self._validate_functionality()
            validation_result["validations"]["functionality"] = functionality_result
            
            # 5. Monitoring validation
            logger.info("Validation 5: Monitoring systems")
            monitoring_result = await self._validate_monitoring()
            validation_result["validations"]["monitoring"] = monitoring_result
            
            # 6. Security validation
            logger.info("Validation 6: Security configuration")
            security_result = await self._validate_security()
            validation_result["validations"]["security"] = security_result
            
            # Calculate overall validation status
            validation_result["overall_status"] = self._calculate_overall_status(validation_result["validations"])
            validation_result["summary"] = self._generate_validation_summary(validation_result["validations"])
            
            logger.info(f"Deployment validation completed - Status: {validation_result['overall_status']}")
            return validation_result
            
        except Exception as e:
            logger.error(f"Deployment validation failed: {e}")
            validation_result["overall_status"] = "failed"
            validation_result["error"] = str(e)
            return validation_result 
   
    async def _validate_health_checks(self) -> Dict[str, Any]:
        """Validate health check endpoints"""
        try:
            if not self.endpoint_url:
                return {
                    "success": False,
                    "error": "No endpoint URL provided for health check validation"
                }
            
            health_endpoints = [
                "/health",
                "/health/ready",
                "/health/live"
            ]
            
            results = {}
            overall_success = True
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
                for endpoint in health_endpoints:
                    try:
                        url = f"{self.endpoint_url.rstrip('/')}{endpoint}"
                        start_time = time.time()
                        
                        async with session.get(url) as response:
                            response_time = (time.time() - start_time) * 1000
                            
                            if response.status == 200:
                                response_data = await response.json()
                                results[endpoint] = {
                                    "success": True,
                                    "status_code": response.status,
                                    "response_time_ms": response_time,
                                    "data": response_data
                                }
                            else:
                                results[endpoint] = {
                                    "success": False,
                                    "status_code": response.status,
                                    "response_time_ms": response_time,
                                    "error": f"Unexpected status code: {response.status}"
                                }
                                overall_success = False
                                
                    except Exception as e:
                        results[endpoint] = {
                            "success": False,
                            "error": str(e)
                        }
                        overall_success = False
            
            return {
                "success": overall_success,
                "endpoints": results,
                "total_endpoints": len(health_endpoints),
                "successful_endpoints": sum(1 for r in results.values() if r.get("success", False))
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _validate_endpoint_connectivity(self) -> Dict[str, Any]:
        """Validate endpoint connectivity and basic functionality"""
        try:
            if not self.endpoint_url:
                return {
                    "success": False,
                    "error": "No endpoint URL provided for connectivity validation"
                }
            
            connectivity_tests = []
            
            # Test basic connectivity
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
                try:
                    start_time = time.time()
                    async with session.get(self.endpoint_url) as response:
                        response_time = (time.time() - start_time) * 1000
                        
                        connectivity_tests.append({
                            "test": "basic_connectivity",
                            "success": response.status in [200, 404],  # 404 is OK for root endpoint
                            "status_code": response.status,
                            "response_time_ms": response_time
                        })
                        
                except Exception as e:
                    connectivity_tests.append({
                        "test": "basic_connectivity",
                        "success": False,
                        "error": str(e)
                    })
                
                # Test CORS headers (if applicable)
                try:
                    async with session.options(self.endpoint_url) as response:
                        cors_headers = {
                            "access-control-allow-origin": response.headers.get("Access-Control-Allow-Origin"),
                            "access-control-allow-methods": response.headers.get("Access-Control-Allow-Methods"),
                            "access-control-allow-headers": response.headers.get("Access-Control-Allow-Headers")
                        }
                        
                        connectivity_tests.append({
                            "test": "cors_headers",
                            "success": True,
                            "cors_headers": cors_headers
                        })
                        
                except Exception as e:
                    connectivity_tests.append({
                        "test": "cors_headers",
                        "success": False,
                        "error": str(e)
                    })
            
            successful_tests = sum(1 for test in connectivity_tests if test.get("success", False))
            
            return {
                "success": successful_tests > 0,
                "tests": connectivity_tests,
                "total_tests": len(connectivity_tests),
                "successful_tests": successful_tests
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _validate_performance(self) -> Dict[str, Any]:
        """Validate performance metrics"""
        try:
            performance_config = self.validation_config.get("response_time", {})
            max_response_time = performance_config.get("max_response_time_ms", 5000)
            
            # Get recent CloudWatch metrics
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(minutes=30)
            
            metrics_to_check = [
                "ResponseTime",
                "ErrorRate",
                "Throughput"
            ]
            
            metric_results = {}
            
            for metric_name in metrics_to_check:
                try:
                    response = self.cloudwatch.get_metric_statistics(
                        Namespace='MBTI/TravelAssistant',
                        MetricName=metric_name,
                        Dimensions=[
                            {
                                'Name': 'Environment',
                                'Value': self.environment
                            },
                            {
                                'Name': 'Service',
                                'Value': self.agent_name
                            }
                        ],
                        StartTime=start_time,
                        EndTime=end_time,
                        Period=300,  # 5 minutes
                        Statistics=['Average', 'Maximum']
                    )
                    
                    datapoints = response.get('Datapoints', [])
                    
                    if datapoints:
                        avg_value = sum(dp['Average'] for dp in datapoints) / len(datapoints)
                        max_value = max(dp['Maximum'] for dp in datapoints)
                        
                        # Validate against thresholds
                        if metric_name == "ResponseTime":
                            success = avg_value <= max_response_time
                        elif metric_name == "ErrorRate":
                            max_error_rate = self.validation_config.get("error_rate", {}).get("max_error_rate", 0.05)
                            success = avg_value <= max_error_rate
                        else:
                            success = True  # No specific threshold for throughput
                        
                        metric_results[metric_name] = {
                            "success": success,
                            "average_value": avg_value,
                            "maximum_value": max_value,
                            "datapoints_count": len(datapoints)
                        }
                    else:
                        metric_results[metric_name] = {
                            "success": False,
                            "error": "No data points available"
                        }
                        
                except Exception as e:
                    metric_results[metric_name] = {
                        "success": False,
                        "error": str(e)
                    }
            
            successful_metrics = sum(1 for result in metric_results.values() if result.get("success", False))
            
            return {
                "success": successful_metrics > 0,
                "metrics": metric_results,
                "total_metrics": len(metrics_to_check),
                "successful_metrics": successful_metrics
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _validate_functionality(self) -> Dict[str, Any]:
        """Validate core functionality"""
        try:
            if not self.endpoint_url:
                return {
                    "success": False,
                    "error": "No endpoint URL provided for functionality validation"
                }
            
            # Test MBTI itinerary generation (if endpoint supports it)
            test_cases = [
                {
                    "name": "health_check_functionality",
                    "endpoint": "/health",
                    "method": "GET",
                    "expected_status": 200
                }
            ]
            
            # Add MBTI-specific tests if we have the right endpoint
            if "/generate-itinerary" in str(self.endpoint_url) or "mbti" in str(self.endpoint_url).lower():
                test_cases.append({
                    "name": "mbti_itinerary_generation",
                    "endpoint": "/generate-itinerary",
                    "method": "POST",
                    "payload": {"MBTI_personality": "INFJ"},
                    "expected_status": 200
                })
            
            functionality_results = []
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=60)) as session:
                for test_case in test_cases:
                    try:
                        url = f"{self.endpoint_url.rstrip('/')}{test_case['endpoint']}"
                        start_time = time.time()
                        
                        if test_case["method"] == "GET":
                            async with session.get(url) as response:
                                response_time = (time.time() - start_time) * 1000
                                success = response.status == test_case["expected_status"]
                                
                                try:
                                    response_data = await response.json()
                                except:
                                    response_data = await response.text()
                                
                                functionality_results.append({
                                    "test": test_case["name"],
                                    "success": success,
                                    "status_code": response.status,
                                    "response_time_ms": response_time,
                                    "response_data": response_data if success else None
                                })
                        
                        elif test_case["method"] == "POST":
                            payload = test_case.get("payload", {})
                            async with session.post(url, json=payload) as response:
                                response_time = (time.time() - start_time) * 1000
                                success = response.status == test_case["expected_status"]
                                
                                try:
                                    response_data = await response.json()
                                except:
                                    response_data = await response.text()
                                
                                functionality_results.append({
                                    "test": test_case["name"],
                                    "success": success,
                                    "status_code": response.status,
                                    "response_time_ms": response_time,
                                    "payload": payload,
                                    "response_data": response_data if success else None
                                })
                                
                    except Exception as e:
                        functionality_results.append({
                            "test": test_case["name"],
                            "success": False,
                            "error": str(e)
                        })
            
            successful_tests = sum(1 for result in functionality_results if result.get("success", False))
            
            return {
                "success": successful_tests > 0,
                "tests": functionality_results,
                "total_tests": len(test_cases),
                "successful_tests": successful_tests
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _validate_monitoring(self) -> Dict[str, Any]:
        """Validate monitoring systems"""
        try:
            monitoring_checks = []
            
            # Check CloudWatch log groups
            logs_client = self.session.client('logs', region_name=self.region)
            expected_log_groups = [
                f"/aws/lambda/{self.agent_name}-{self.environment}",
                f"/mbti/travel-assistant/{self.environment}/application"
            ]
            
            for log_group in expected_log_groups:
                try:
                    logs_client.describe_log_groups(logGroupNamePrefix=log_group)
                    monitoring_checks.append({
                        "check": f"log_group_{log_group.replace('/', '_')}",
                        "success": True,
                        "log_group": log_group
                    })
                except ClientError as e:
                    if e.response['Error']['Code'] == 'ResourceNotFoundException':
                        monitoring_checks.append({
                            "check": f"log_group_{log_group.replace('/', '_')}",
                            "success": False,
                            "error": f"Log group not found: {log_group}"
                        })
                    else:
                        monitoring_checks.append({
                            "check": f"log_group_{log_group.replace('/', '_')}",
                            "success": False,
                            "error": str(e)
                        })
            
            # Check CloudWatch metrics
            try:
                metrics_response = self.cloudwatch.list_metrics(
                    Namespace='MBTI/TravelAssistant',
                    Dimensions=[
                        {
                            'Name': 'Environment',
                            'Value': self.environment
                        }
                    ]
                )
                
                metrics_count = len(metrics_response.get('Metrics', []))
                monitoring_checks.append({
                    "check": "cloudwatch_metrics",
                    "success": metrics_count > 0,
                    "metrics_count": metrics_count
                })
                
            except Exception as e:
                monitoring_checks.append({
                    "check": "cloudwatch_metrics",
                    "success": False,
                    "error": str(e)
                })
            
            # Check CloudWatch alarms
            try:
                alarms_response = self.cloudwatch.describe_alarms(
                    AlarmNamePrefix=f"{self.agent_name}-{self.environment}"
                )
                
                alarms_count = len(alarms_response.get('MetricAlarms', []))
                monitoring_checks.append({
                    "check": "cloudwatch_alarms",
                    "success": alarms_count > 0,
                    "alarms_count": alarms_count
                })
                
            except Exception as e:
                monitoring_checks.append({
                    "check": "cloudwatch_alarms",
                    "success": False,
                    "error": str(e)
                })
            
            successful_checks = sum(1 for check in monitoring_checks if check.get("success", False))
            
            return {
                "success": successful_checks > 0,
                "checks": monitoring_checks,
                "total_checks": len(monitoring_checks),
                "successful_checks": successful_checks
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _validate_security(self) -> Dict[str, Any]:
        """Validate security configuration"""
        try:
            security_checks = []
            
            if self.endpoint_url:
                # Check HTTPS
                is_https = self.endpoint_url.startswith('https://')
                security_checks.append({
                    "check": "https_enabled",
                    "success": is_https,
                    "endpoint": self.endpoint_url
                })
                
                # Check security headers
                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
                    try:
                        async with session.get(f"{self.endpoint_url}/health") as response:
                            security_headers = {
                                "x-content-type-options": response.headers.get("X-Content-Type-Options"),
                                "x-frame-options": response.headers.get("X-Frame-Options"),
                                "x-xss-protection": response.headers.get("X-XSS-Protection"),
                                "strict-transport-security": response.headers.get("Strict-Transport-Security")
                            }
                            
                            headers_present = sum(1 for v in security_headers.values() if v is not None)
                            
                            security_checks.append({
                                "check": "security_headers",
                                "success": headers_present > 0,
                                "headers_present": headers_present,
                                "total_headers": len(security_headers),
                                "headers": security_headers
                            })
                            
                    except Exception as e:
                        security_checks.append({
                            "check": "security_headers",
                            "success": False,
                            "error": str(e)
                        })
            
            # Check IAM roles and policies (basic check)
            try:
                iam_client = self.session.client('iam', region_name=self.region)
                
                # This is a basic check - in practice, you'd check specific roles
                roles_response = iam_client.list_roles(MaxItems=1)
                
                security_checks.append({
                    "check": "iam_access",
                    "success": True,
                    "message": "IAM access verified"
                })
                
            except Exception as e:
                security_checks.append({
                    "check": "iam_access",
                    "success": False,
                    "error": str(e)
                })
            
            successful_checks = sum(1 for check in security_checks if check.get("success", False))
            
            return {
                "success": successful_checks > 0,
                "checks": security_checks,
                "total_checks": len(security_checks),
                "successful_checks": successful_checks
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _calculate_overall_status(self, validations: Dict[str, Any]) -> str:
        """Calculate overall validation status"""
        if not validations:
            return "unknown"
        
        successful_validations = sum(1 for v in validations.values() if v.get("success", False))
        total_validations = len(validations)
        
        success_rate = successful_validations / total_validations if total_validations > 0 else 0
        
        if success_rate >= 0.8:
            return "passed"
        elif success_rate >= 0.6:
            return "passed_with_warnings"
        else:
            return "failed"
    
    def _generate_validation_summary(self, validations: Dict[str, Any]) -> Dict[str, Any]:
        """Generate validation summary"""
        summary = {
            "total_validations": len(validations),
            "successful_validations": 0,
            "failed_validations": 0,
            "warnings": []
        }
        
        for validation_name, validation_result in validations.items():
            if validation_result.get("success", False):
                summary["successful_validations"] += 1
            else:
                summary["failed_validations"] += 1
                error = validation_result.get("error", "Unknown error")
                summary["warnings"].append(f"{validation_name}: {error}")
        
        summary["success_rate"] = (
            summary["successful_validations"] / summary["total_validations"] * 100
            if summary["total_validations"] > 0 else 0
        )
        
        return summary
    
    async def save_validation_report(self, validation_result: Dict[str, Any], output_file: Optional[str] = None) -> str:
        """Save validation report to file"""
        if not output_file:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            output_file = f"deployment_validation_report_{self.environment}_{timestamp}.json"
        
        try:
            with open(output_file, 'w') as f:
                json.dump(validation_result, f, indent=2, default=str)
            
            logger.info(f"Validation report saved to: {output_file}")
            return output_file
            
        except Exception as e:
            logger.error(f"Failed to save validation report: {e}")
            raise


async def main():
    """Main validation function"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Validate MBTI Travel Assistant deployment'
    )
    parser.add_argument('--environment', required=True,
                       choices=['development', 'staging', 'production'],
                       help='Environment name')
    parser.add_argument('--agent-name', default='mbti-travel-assistant-mcp',
                       help='Agent name')
    parser.add_argument('--region', default='us-east-1',
                       help='AWS region')
    parser.add_argument('--endpoint-url',
                       help='Endpoint URL for testing')
    parser.add_argument('--output-file',
                       help='Output file for validation report')
    
    args = parser.parse_args()
    
    try:
        validator = DeploymentValidator(
            environment=args.environment,
            agent_name=args.agent_name,
            region=args.region,
            endpoint_url=args.endpoint_url
        )
        
        result = await validator.validate_complete_deployment()
        
        # Save validation report
        report_file = await validator.save_validation_report(result, args.output_file)
        
        if result["overall_status"] == "passed":
            print("\n" + "="*60)
            print("🎉 DEPLOYMENT VALIDATION PASSED! 🎉")
            print("="*60)
            print(f"Environment: {args.environment}")
            print(f"Agent: {args.agent_name}")
            print(f"Success Rate: {result['summary']['success_rate']:.1f}%")
            print(f"Report File: {report_file}")
            print("="*60)
            return 0
        elif result["overall_status"] == "passed_with_warnings":
            print("\n" + "="*60)
            print("⚠️ DEPLOYMENT VALIDATION PASSED WITH WARNINGS")
            print("="*60)
            print(f"Success Rate: {result['summary']['success_rate']:.1f}%")
            print(f"Warnings: {len(result['summary']['warnings'])}")
            for warning in result['summary']['warnings']:
                print(f"  - {warning}")
            print(f"Report File: {report_file}")
            print("="*60)
            return 0
        else:
            print("\n" + "="*60)
            print("❌ DEPLOYMENT VALIDATION FAILED")
            print("="*60)
            print(f"Success Rate: {result['summary']['success_rate']:.1f}%")
            print(f"Failed Validations: {result['summary']['failed_validations']}")
            for warning in result['summary']['warnings']:
                print(f"  - {warning}")
            print(f"Report File: {report_file}")
            print("="*60)
            return 1
            
    except Exception as e:
        logger.error(f"Deployment validation failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))