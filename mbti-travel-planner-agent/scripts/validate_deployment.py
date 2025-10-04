#!/usr/bin/env python3
"""
Deployment Validation Script

This script validates that all components of the mbti-travel-planner-agent
work correctly after deployment. It performs comprehensive checks including
configuration validation, service connectivity, tool functionality, and
end-to-end workflow testing.

Features:
- Configuration validation and environment checks
- Gateway connectivity and authentication testing
- Tool functionality validation
- Nova Pro model integration testing
- End-to-end workflow validation
- Deployment health assessment
"""

import asyncio
import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import argparse
import importlib.util

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.environment_loader import EnvironmentConfigLoader
from config.validate_config import ConfigValidator
from services.gateway_http_client import GatewayHTTPClient, Environment
from services.gateway_tools import create_gateway_tools
from services.health_check_service import get_health_check_service
from services.logging_service import get_logging_service
from services.error_handler import ErrorHandler


class DeploymentValidator:
    """Comprehensive deployment validation for the MBTI Travel Planner Agent."""
    
    def __init__(self, environment: str = "production", verbose: bool = False):
        """
        Initialize the deployment validator.
        
        Args:
            environment: Environment to validate (development, staging, production)
            verbose: Enable verbose logging
        """
        self.environment = environment
        self.verbose = verbose
        
        # Setup logging
        logging.basicConfig(
            level=logging.DEBUG if verbose else logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger("deployment_validator")
        
        # Initialize services
        self.logging_service = get_logging_service()
        self.error_handler = ErrorHandler("deployment_validator")
        self.health_service = get_health_check_service()
        
        # Validation results
        self.validation_results = {
            "timestamp": datetime.utcnow().isoformat(),
            "environment": environment,
            "validations": {},
            "summary": {}
        }
        
        self.logger.info(f"Initialized deployment validator for {environment}")
    
    async def validate_configuration(self) -> Dict[str, Any]:
        """Validate configuration files and environment setup."""
        validation_name = "configuration"
        self.logger.info("Validating configuration and environment setup")
        
        result = {
            "validation_name": validation_name,
            "success": True,
            "checks": {},
            "errors": []
        }
        
        try:
            # Check environment configuration
            env_loader = EnvironmentConfigLoader()
            
            # Validate gateway configuration
            gateway_config_path = project_root / "config" / "environments" / "gateway.json"
            if gateway_config_path.exists():
                with open(gateway_config_path, 'r') as f:
                    gateway_config = json.load(f)
                
                if self.environment in gateway_config:
                    env_config = gateway_config[self.environment]
                    result["checks"]["gateway_config"] = {
                        "success": True,
                        "base_url": env_config.get("base_url"),
                        "endpoints": list(env_config.get("endpoints", {}).keys()),
                        "auth_required": env_config.get("auth_required", False)
                    }
                    self.logger.info(f"✓ Gateway configuration valid for {self.environment}")
                else:
                    result["success"] = False
                    result["errors"].append(f"Environment '{self.environment}' not found in gateway config")
                    result["checks"]["gateway_config"] = {"success": False}
            else:
                result["success"] = False
                result["errors"].append("Gateway configuration file not found")
                result["checks"]["gateway_config"] = {"success": False}
            
            # Validate required files
            required_files = [
                "main.py",
                "requirements.txt",
                ".bedrock_agentcore.yaml",
                "services/gateway_http_client.py",
                "services/gateway_tools.py",
                "services/error_handler.py"
            ]
            
            missing_files = []
            for file_path in required_files:
                full_path = project_root / file_path
                if not full_path.exists():
                    missing_files.append(file_path)
            
            if missing_files:
                result["success"] = False
                result["errors"].extend([f"Missing required file: {f}" for f in missing_files])
                result["checks"]["required_files"] = {"success": False, "missing": missing_files}
            else:
                result["checks"]["required_files"] = {"success": True}
                self.logger.info("✓ All required files present")
            
            # Validate Python dependencies
            try:
                import httpx
                import pydantic
                import strands_agents
                result["checks"]["dependencies"] = {"success": True}
                self.logger.info("✓ Required Python dependencies available")
            except ImportError as e:
                result["success"] = False
                result["errors"].append(f"Missing Python dependency: {e}")
                result["checks"]["dependencies"] = {"success": False, "error": str(e)}
            
            # Validate configuration using ConfigValidator
            try:
                config_validator = ConfigValidator()
                validation_result = config_validator.validate_all_configs()
                
                if validation_result["valid"]:
                    result["checks"]["config_validation"] = {"success": True}
                    self.logger.info("✓ Configuration validation passed")
                else:
                    result["success"] = False
                    result["errors"].extend(validation_result.get("errors", []))
                    result["checks"]["config_validation"] = {
                        "success": False,
                        "errors": validation_result.get("errors", [])
                    }
            except Exception as e:
                result["errors"].append(f"Configuration validation failed: {e}")
                result["checks"]["config_validation"] = {"success": False, "error": str(e)}
            
        except Exception as e:
            result["success"] = False
            result["errors"].append(f"Configuration validation error: {e}")
            self.logger.error(f"✗ Configuration validation failed: {e}")
        
        self.validation_results["validations"][validation_name] = result
        return result
    
    async def validate_gateway_connectivity(self) -> Dict[str, Any]:
        """Validate gateway connectivity and authentication."""
        validation_name = "gateway_connectivity"
        self.logger.info("Validating gateway connectivity")
        
        result = {
            "validation_name": validation_name,
            "success": True,
            "checks": {},
            "errors": []
        }
        
        try:
            # Initialize gateway client
            env_enum = Environment.PRODUCTION
            if self.environment == "development":
                env_enum = Environment.DEVELOPMENT
            elif self.environment == "staging":
                env_enum = Environment.STAGING
            
            gateway_client = GatewayHTTPClient(environment=env_enum)
            
            # Test basic connectivity
            try:
                # Test with a simple district search
                search_result = await gateway_client.search_restaurants_by_district(["Central district"])
                
                if search_result.get("success", False):
                    result["checks"]["basic_connectivity"] = {
                        "success": True,
                        "response_time_ms": search_result.get("metadata", {}).get("execution_time_ms", 0),
                        "restaurant_count": len(search_result.get("restaurants", []))
                    }
                    self.logger.info("✓ Gateway connectivity test passed")
                else:
                    result["success"] = False
                    result["errors"].append(f"Gateway search failed: {search_result.get('error', 'Unknown error')}")
                    result["checks"]["basic_connectivity"] = {"success": False}
                
            except Exception as e:
                result["success"] = False
                result["errors"].append(f"Gateway connectivity test failed: {e}")
                result["checks"]["basic_connectivity"] = {"success": False, "error": str(e)}
            
            # Test all endpoints
            endpoints_to_test = [
                ("district_search", lambda: gateway_client.search_restaurants_by_district(["Central district"])),
                ("combined_search", lambda: gateway_client.search_restaurants_combined(
                    districts=["Central district"], meal_types=["lunch"]
                )),
                ("recommendation", lambda: gateway_client.recommend_restaurants([
                    {
                        "id": "test_001",
                        "name": "Test Restaurant",
                        "sentiment": {"likes": 85, "dislikes": 10, "neutral": 5}
                    }
                ]))
            ]
            
            endpoint_results = {}
            for endpoint_name, test_func in endpoints_to_test:
                try:
                    start_time = time.time()
                    endpoint_result = await test_func()
                    response_time = (time.time() - start_time) * 1000
                    
                    endpoint_results[endpoint_name] = {
                        "success": endpoint_result.get("success", False),
                        "response_time_ms": response_time,
                        "error": endpoint_result.get("error")
                    }
                    
                    if endpoint_result.get("success", False):
                        self.logger.info(f"✓ {endpoint_name} endpoint test passed")
                    else:
                        self.logger.warning(f"⚠ {endpoint_name} endpoint test failed")
                        result["success"] = False
                        result["errors"].append(f"{endpoint_name} endpoint failed")
                
                except Exception as e:
                    endpoint_results[endpoint_name] = {
                        "success": False,
                        "error": str(e)
                    }
                    result["success"] = False
                    result["errors"].append(f"{endpoint_name} endpoint error: {e}")
                    self.logger.error(f"✗ {endpoint_name} endpoint test failed: {e}")
            
            result["checks"]["endpoint_tests"] = endpoint_results
            
        except Exception as e:
            result["success"] = False
            result["errors"].append(f"Gateway connectivity validation error: {e}")
            self.logger.error(f"✗ Gateway connectivity validation failed: {e}")
        
        self.validation_results["validations"][validation_name] = result
        return result
    
    async def validate_tool_functionality(self) -> Dict[str, Any]:
        """Validate that all gateway tools function correctly."""
        validation_name = "tool_functionality"
        self.logger.info("Validating tool functionality")
        
        result = {
            "validation_name": validation_name,
            "success": True,
            "checks": {},
            "errors": []
        }
        
        try:
            # Create gateway tools
            env_enum = Environment.PRODUCTION
            if self.environment == "development":
                env_enum = Environment.DEVELOPMENT
            elif self.environment == "staging":
                env_enum = Environment.STAGING
            
            tools = create_gateway_tools(environment=env_enum)
            
            # Test each tool
            tool_tests = [
                {
                    "name": "search_restaurants_by_district_tool",
                    "args": {"districts": ["Central district"]},
                    "expected_keys": ["success", "restaurants"]
                },
                {
                    "name": "search_restaurants_combined_tool",
                    "args": {"districts": ["Central district"], "meal_types": ["lunch"]},
                    "expected_keys": ["success", "restaurants"]
                },
                {
                    "name": "recommend_restaurants_tool",
                    "args": {
                        "restaurants": [
                            {
                                "id": "test_001",
                                "name": "Test Restaurant",
                                "sentiment": {"likes": 85, "dislikes": 10, "neutral": 5}
                            }
                        ]
                    },
                    "expected_keys": ["success"]
                }
            ]
            
            tool_results = {}
            for tool_test in tool_tests:
                tool_name = tool_test["name"]
                
                try:
                    # Find the tool function
                    tool_func = None
                    for tool in tools:
                        if hasattr(tool, 'name') and tool.name == tool_name:
                            tool_func = tool.func
                            break
                        elif hasattr(tool, '__name__') and tool.__name__ == tool_name:
                            tool_func = tool
                            break
                    
                    if tool_func is None:
                        tool_results[tool_name] = {
                            "success": False,
                            "error": "Tool function not found"
                        }
                        result["success"] = False
                        result["errors"].append(f"Tool {tool_name} not found")
                        continue
                    
                    # Execute tool
                    start_time = time.time()
                    if asyncio.iscoroutinefunction(tool_func):
                        tool_result = await tool_func(**tool_test["args"])
                    else:
                        tool_result = tool_func(**tool_test["args"])
                    
                    response_time = (time.time() - start_time) * 1000
                    
                    # Validate result structure
                    has_expected_keys = all(
                        key in tool_result for key in tool_test["expected_keys"]
                    )
                    
                    tool_results[tool_name] = {
                        "success": has_expected_keys and tool_result.get("success", False),
                        "response_time_ms": response_time,
                        "result_keys": list(tool_result.keys()) if isinstance(tool_result, dict) else [],
                        "error": tool_result.get("error") if isinstance(tool_result, dict) else None
                    }
                    
                    if tool_results[tool_name]["success"]:
                        self.logger.info(f"✓ {tool_name} test passed")
                    else:
                        self.logger.warning(f"⚠ {tool_name} test failed")
                        result["success"] = False
                        result["errors"].append(f"Tool {tool_name} validation failed")
                
                except Exception as e:
                    tool_results[tool_name] = {
                        "success": False,
                        "error": str(e)
                    }
                    result["success"] = False
                    result["errors"].append(f"Tool {tool_name} error: {e}")
                    self.logger.error(f"✗ {tool_name} test failed: {e}")
            
            result["checks"]["tool_tests"] = tool_results
            
        except Exception as e:
            result["success"] = False
            result["errors"].append(f"Tool functionality validation error: {e}")
            self.logger.error(f"✗ Tool functionality validation failed: {e}")
        
        self.validation_results["validations"][validation_name] = result
        return result
    
    async def validate_nova_pro_integration(self) -> Dict[str, Any]:
        """Validate Nova Pro model integration."""
        validation_name = "nova_pro_integration"
        self.logger.info("Validating Nova Pro model integration")
        
        result = {
            "validation_name": validation_name,
            "success": True,
            "checks": {},
            "errors": []
        }
        
        try:
            # Check if main.py can be imported and has correct model configuration
            main_path = project_root / "main.py"
            if main_path.exists():
                # Read main.py to check for Nova Pro configuration
                with open(main_path, 'r') as f:
                    main_content = f.read()
                
                # Check for Nova Pro model specification
                if "amazon.nova-pro-v1:0" in main_content:
                    result["checks"]["model_specification"] = {"success": True}
                    self.logger.info("✓ Nova Pro model specification found")
                else:
                    result["success"] = False
                    result["errors"].append("Nova Pro model specification not found in main.py")
                    result["checks"]["model_specification"] = {"success": False}
                
                # Check for proper agent initialization
                if "Agent(" in main_content and "tools=" in main_content:
                    result["checks"]["agent_initialization"] = {"success": True}
                    self.logger.info("✓ Agent initialization structure found")
                else:
                    result["success"] = False
                    result["errors"].append("Proper agent initialization not found")
                    result["checks"]["agent_initialization"] = {"success": False}
                
            else:
                result["success"] = False
                result["errors"].append("main.py file not found")
                result["checks"]["main_file"] = {"success": False}
            
            # Check bedrock_agentcore.yaml configuration
            agentcore_config_path = project_root / ".bedrock_agentcore.yaml"
            if agentcore_config_path.exists():
                with open(agentcore_config_path, 'r') as f:
                    agentcore_content = f.read()
                
                # Check for proper platform specification
                if "linux/arm64" in agentcore_content:
                    result["checks"]["platform_config"] = {"success": True}
                    self.logger.info("✓ ARM64 platform configuration found")
                else:
                    result["success"] = False
                    result["errors"].append("ARM64 platform not specified in .bedrock_agentcore.yaml")
                    result["checks"]["platform_config"] = {"success": False}
                
            else:
                result["success"] = False
                result["errors"].append(".bedrock_agentcore.yaml file not found")
                result["checks"]["agentcore_config"] = {"success": False}
            
        except Exception as e:
            result["success"] = False
            result["errors"].append(f"Nova Pro integration validation error: {e}")
            self.logger.error(f"✗ Nova Pro integration validation failed: {e}")
        
        self.validation_results["validations"][validation_name] = result
        return result
    
    async def validate_end_to_end_workflow(self) -> Dict[str, Any]:
        """Validate complete end-to-end workflow."""
        validation_name = "end_to_end_workflow"
        self.logger.info("Validating end-to-end workflow")
        
        result = {
            "validation_name": validation_name,
            "success": True,
            "checks": {},
            "errors": []
        }
        
        try:
            # Test Central district workflow
            env_enum = Environment.PRODUCTION
            if self.environment == "development":
                env_enum = Environment.DEVELOPMENT
            elif self.environment == "staging":
                env_enum = Environment.STAGING
            
            gateway_client = GatewayHTTPClient(environment=env_enum)
            
            # Step 1: Search for restaurants in Central district
            search_start = time.time()
            search_result = await gateway_client.search_restaurants_by_district(["Central district"])
            search_time = (time.time() - search_start) * 1000
            
            if search_result.get("success", False) and search_result.get("restaurants"):
                result["checks"]["restaurant_search"] = {
                    "success": True,
                    "response_time_ms": search_time,
                    "restaurant_count": len(search_result["restaurants"])
                }
                self.logger.info(f"✓ Restaurant search completed: {len(search_result['restaurants'])} restaurants found")
                
                # Step 2: Get recommendations for found restaurants
                recommend_start = time.time()
                recommend_result = await gateway_client.recommend_restaurants(
                    search_result["restaurants"][:5]  # Use first 5 restaurants
                )
                recommend_time = (time.time() - recommend_start) * 1000
                
                if recommend_result.get("success", False):
                    result["checks"]["restaurant_recommendation"] = {
                        "success": True,
                        "response_time_ms": recommend_time,
                        "has_recommendation": "recommendation" in recommend_result,
                        "has_candidates": "candidates" in recommend_result
                    }
                    self.logger.info("✓ Restaurant recommendation completed")
                    
                    # Step 3: Validate complete workflow timing
                    total_time = search_time + recommend_time
                    if total_time < 30000:  # Less than 30 seconds
                        result["checks"]["workflow_performance"] = {
                            "success": True,
                            "total_time_ms": total_time,
                            "search_time_ms": search_time,
                            "recommend_time_ms": recommend_time
                        }
                        self.logger.info(f"✓ Workflow performance acceptable: {total_time:.2f}ms total")
                    else:
                        result["success"] = False
                        result["errors"].append(f"Workflow too slow: {total_time:.2f}ms")
                        result["checks"]["workflow_performance"] = {"success": False, "total_time_ms": total_time}
                    
                else:
                    result["success"] = False
                    result["errors"].append("Restaurant recommendation failed")
                    result["checks"]["restaurant_recommendation"] = {"success": False}
                
            else:
                result["success"] = False
                result["errors"].append("Restaurant search failed or returned no results")
                result["checks"]["restaurant_search"] = {"success": False}
            
        except Exception as e:
            result["success"] = False
            result["errors"].append(f"End-to-end workflow validation error: {e}")
            self.logger.error(f"✗ End-to-end workflow validation failed: {e}")
        
        self.validation_results["validations"][validation_name] = result
        return result
    
    async def validate_health_monitoring(self) -> Dict[str, Any]:
        """Validate health monitoring and observability."""
        validation_name = "health_monitoring"
        self.logger.info("Validating health monitoring")
        
        result = {
            "validation_name": validation_name,
            "success": True,
            "checks": {},
            "errors": []
        }
        
        try:
            # Test health check service
            health_results = await self.health_service.check_all_endpoints()
            
            if health_results:
                healthy_count = sum(1 for r in health_results.values() if r.status == "healthy")
                total_count = len(health_results)
                
                result["checks"]["health_service"] = {
                    "success": healthy_count > 0,
                    "healthy_endpoints": healthy_count,
                    "total_endpoints": total_count,
                    "health_percentage": (healthy_count / total_count * 100) if total_count > 0 else 0
                }
                
                if healthy_count > 0:
                    self.logger.info(f"✓ Health monitoring working: {healthy_count}/{total_count} endpoints healthy")
                else:
                    result["success"] = False
                    result["errors"].append("No healthy endpoints found")
                    self.logger.warning("⚠ No healthy endpoints found")
            else:
                result["success"] = False
                result["errors"].append("Health check service returned no results")
                result["checks"]["health_service"] = {"success": False}
            
            # Test logging service
            try:
                self.logging_service.log_info("Deployment validation test log entry")
                result["checks"]["logging_service"] = {"success": True}
                self.logger.info("✓ Logging service functional")
            except Exception as e:
                result["errors"].append(f"Logging service error: {e}")
                result["checks"]["logging_service"] = {"success": False, "error": str(e)}
            
            # Test error handling
            try:
                test_error = Exception("Test error for validation")
                self.error_handler.handle_error(test_error, "deployment_validation_test")
                result["checks"]["error_handling"] = {"success": True}
                self.logger.info("✓ Error handling functional")
            except Exception as e:
                result["errors"].append(f"Error handling test failed: {e}")
                result["checks"]["error_handling"] = {"success": False, "error": str(e)}
            
        except Exception as e:
            result["success"] = False
            result["errors"].append(f"Health monitoring validation error: {e}")
            self.logger.error(f"✗ Health monitoring validation failed: {e}")
        
        self.validation_results["validations"][validation_name] = result
        return result
    
    async def run_all_validations(self) -> Dict[str, Any]:
        """Run all deployment validations."""
        self.logger.info(f"Starting deployment validation for {self.environment}")
        start_time = time.time()
        
        # Run all validations
        validations = [
            self.validate_configuration(),
            self.validate_gateway_connectivity(),
            self.validate_tool_functionality(),
            self.validate_nova_pro_integration(),
            self.validate_end_to_end_workflow(),
            self.validate_health_monitoring()
        ]
        
        results = await asyncio.gather(*validations, return_exceptions=True)
        
        # Process results
        successful_validations = 0
        total_validations = len(validations)
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                validation_name = f"validation_{i}"
                self.logger.error(f"Validation {validation_name} raised exception: {result}")
                self.validation_results["validations"][validation_name] = {
                    "validation_name": validation_name,
                    "success": False,
                    "error": str(result)
                }
            elif result.get("success", False):
                successful_validations += 1
        
        # Generate summary
        total_time = time.time() - start_time
        self.validation_results["summary"] = {
            "total_validations": total_validations,
            "successful_validations": successful_validations,
            "success_rate_percent": (successful_validations / total_validations) * 100,
            "overall_success": successful_validations == total_validations,
            "environment": self.environment,
            "validation_duration_seconds": total_time,
            "deployment_status": "VALID" if successful_validations == total_validations else "INVALID"
        }
        
        # Log summary
        summary = self.validation_results["summary"]
        if summary["overall_success"]:
            self.logger.info(f"✓ All validations passed ({successful_validations}/{total_validations})")
            self.logger.info(f"✓ Deployment is VALID for {self.environment}")
        else:
            self.logger.warning(f"⚠ Some validations failed ({successful_validations}/{total_validations})")
            self.logger.warning(f"✗ Deployment is INVALID for {self.environment}")
        
        return self.validation_results
    
    def save_results(self, output_file: Optional[str] = None) -> str:
        """Save validation results to a JSON file."""
        if output_file is None:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            output_file = f"deployment_validation_{self.environment}_{timestamp}.json"
        
        output_path = project_root / "tests" / "results" / output_file
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(self.validation_results, f, indent=2)
        
        self.logger.info(f"Validation results saved to: {output_path}")
        return str(output_path)
    
    def print_summary(self) -> None:
        """Print a formatted summary of validation results."""
        summary = self.validation_results.get("summary", {})
        
        print("\n" + "="*70)
        print(f"DEPLOYMENT VALIDATION SUMMARY")
        print("="*70)
        print(f"Environment: {summary.get('environment', 'Unknown')}")
        print(f"Validation Time: {self.validation_results.get('timestamp', 'Unknown')}")
        print(f"Duration: {summary.get('validation_duration_seconds', 0):.2f} seconds")
        print()
        
        status = summary.get('deployment_status', 'UNKNOWN')
        status_symbol = "✓" if status == "VALID" else "✗"
        print(f"Deployment Status: {status_symbol} {status}")
        print(f"Success Rate: {summary.get('success_rate_percent', 0):.1f}% ({summary.get('successful_validations', 0)}/{summary.get('total_validations', 0)})")
        print()
        
        print("Validation Details:")
        print("-" * 50)
        
        for validation_name, validation_result in self.validation_results.get("validations", {}).items():
            status = "✓ PASS" if validation_result.get("success") else "✗ FAIL"
            print(f"{validation_name:30} {status}")
            
            # Show check details
            checks = validation_result.get("checks", {})
            for check_name, check_result in checks.items():
                check_status = "✓" if check_result.get("success") else "✗"
                print(f"  {check_name:26} {check_status}")
            
            # Show errors
            errors = validation_result.get("errors", [])
            for error in errors:
                print(f"  Error: {error}")
        
        print("\n" + "="*70)


async def main():
    """Main function to run deployment validation."""
    parser = argparse.ArgumentParser(description="Validate deployment of mbti-travel-planner-agent")
    parser.add_argument(
        "--environment", "-e",
        choices=["development", "staging", "production"],
        default="production",
        help="Environment to validate (default: production)"
    )
    parser.add_argument(
        "--output", "-o",
        help="Output file for validation results (default: auto-generated)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Suppress summary output"
    )
    
    args = parser.parse_args()
    
    # Initialize validator
    validator = DeploymentValidator(
        environment=args.environment,
        verbose=args.verbose
    )
    
    try:
        # Run validations
        results = await validator.run_all_validations()
        
        # Save results
        output_file = validator.save_results(args.output)
        
        # Print summary unless quiet mode
        if not args.quiet:
            validator.print_summary()
        
        # Exit with appropriate code
        success = results.get("summary", {}).get("overall_success", False)
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\nValidation interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"Validation failed with error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())