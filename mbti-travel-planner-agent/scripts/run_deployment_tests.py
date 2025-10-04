#!/usr/bin/env python3
"""
Master Deployment and Testing Script

This script orchestrates all deployment and testing scripts for the
mbti-travel-planner-agent. It provides a unified interface to run
connectivity tests, deployment validation, end-to-end testing, and
health monitoring.

Features:
- Run all tests in sequence or individually
- Aggregate results from all test scripts
- Generate comprehensive deployment reports
- Support for different environments
- Parallel test execution options
"""

import asyncio
import json
import logging
import sys
import time
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
import argparse

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class DeploymentTestRunner:
    """Master test runner for deployment validation."""
    
    def __init__(self, environment: str = "production", verbose: bool = False):
        """
        Initialize the test runner.
        
        Args:
            environment: Environment to test
            verbose: Enable verbose logging
        """
        self.environment = environment
        self.verbose = verbose
        
        # Setup logging
        logging.basicConfig(
            level=logging.DEBUG if verbose else logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger("deployment_test_runner")
        
        # Test scripts configuration
        self.scripts_dir = Path(__file__).parent
        self.test_scripts = {
            "connectivity": {
                "script": "test_gateway_connectivity.py",
                "description": "Gateway connectivity and endpoint availability",
                "timeout": 300  # 5 minutes
            },
            "validation": {
                "script": "validate_deployment.py", 
                "description": "Comprehensive deployment validation",
                "timeout": 600  # 10 minutes
            },
            "e2e": {
                "script": "test_central_district_e2e.py",
                "description": "Central district end-to-end functionality",
                "timeout": 900  # 15 minutes
            },
            "health": {
                "script": "monitor_agent_health.py",
                "description": "Agent health and performance monitoring",
                "timeout": 120,  # 2 minutes for single check
                "args": ["--single-check"]
            }
        }
        
        # Results tracking
        self.test_results = {
            "timestamp": datetime.utcnow().isoformat(),
            "environment": environment,
            "test_execution": {},
            "summary": {}
        }
        
        self.logger.info(f"Initialized deployment test runner for {environment}")
    
    async def run_script(self, script_name: str, script_config: Dict[str, Any]) -> Dict[str, Any]:
        """Run a single test script."""
        script_path = self.scripts_dir / script_config["script"]
        
        if not script_path.exists():
            return {
                "success": False,
                "error": f"Script not found: {script_path}",
                "duration_seconds": 0
            }
        
        self.logger.info(f"Running {script_name}: {script_config['description']}")
        
        # Prepare command
        cmd = [
            sys.executable,
            str(script_path),
            "--environment", self.environment,
            "--quiet"  # Suppress individual script output
        ]
        
        if self.verbose:
            cmd.append("--verbose")
        
        # Add script-specific arguments
        if "args" in script_config:
            cmd.extend(script_config["args"])
        
        start_time = time.time()
        
        try:
            # Run the script
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=project_root
            )
            
            # Wait for completion with timeout
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=script_config.get("timeout", 300)
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return {
                    "success": False,
                    "error": f"Script timed out after {script_config.get('timeout', 300)} seconds",
                    "duration_seconds": time.time() - start_time
                }
            
            duration = time.time() - start_time
            
            # Parse results
            result = {
                "success": process.returncode == 0,
                "return_code": process.returncode,
                "duration_seconds": duration,
                "stdout": stdout.decode() if stdout else "",
                "stderr": stderr.decode() if stderr else ""
            }
            
            if not result["success"]:
                result["error"] = f"Script failed with return code {process.returncode}"
                if result["stderr"]:
                    result["error"] += f": {result['stderr']}"
            
            # Try to find and parse result file
            result_file_pattern = f"{script_name}*{self.environment}*.json"
            results_dir = project_root / "tests" / "results"
            
            if results_dir.exists():
                result_files = list(results_dir.glob(result_file_pattern))
                if result_files:
                    # Use the most recent result file
                    latest_result_file = max(result_files, key=lambda f: f.stat().st_mtime)
                    try:
                        with open(latest_result_file, 'r') as f:
                            script_results = json.load(f)
                        result["detailed_results"] = script_results
                        result["result_file"] = str(latest_result_file)
                    except Exception as e:
                        self.logger.warning(f"Could not parse result file {latest_result_file}: {e}")
            
            if result["success"]:
                self.logger.info(f"✓ {script_name} completed successfully ({duration:.2f}s)")
            else:
                self.logger.error(f"✗ {script_name} failed ({duration:.2f}s)")
            
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            self.logger.error(f"✗ {script_name} error: {e}")
            return {
                "success": False,
                "error": str(e),
                "duration_seconds": duration
            }
    
    async def run_all_tests(self, parallel: bool = False) -> Dict[str, Any]:
        """Run all deployment tests."""
        self.logger.info(f"Starting deployment tests for {self.environment}")
        start_time = time.time()
        
        if parallel:
            # Run tests in parallel
            self.logger.info("Running tests in parallel")
            tasks = []
            for script_name, script_config in self.test_scripts.items():
                task = asyncio.create_task(self.run_script(script_name, script_config))
                tasks.append((script_name, task))
            
            # Wait for all tasks to complete
            for script_name, task in tasks:
                try:
                    result = await task
                    self.test_results["test_execution"][script_name] = result
                except Exception as e:
                    self.logger.error(f"Task {script_name} failed: {e}")
                    self.test_results["test_execution"][script_name] = {
                        "success": False,
                        "error": str(e),
                        "duration_seconds": 0
                    }
        else:
            # Run tests sequentially
            self.logger.info("Running tests sequentially")
            for script_name, script_config in self.test_scripts.items():
                result = await self.run_script(script_name, script_config)
                self.test_results["test_execution"][script_name] = result
                
                # Stop on critical failures if not in parallel mode
                if not result["success"] and script_name in ["connectivity", "validation"]:
                    self.logger.warning(f"Critical test {script_name} failed, continuing with remaining tests")
        
        # Generate summary
        total_duration = time.time() - start_time
        successful_tests = sum(1 for r in self.test_results["test_execution"].values() if r["success"])
        total_tests = len(self.test_scripts)
        
        self.test_results["summary"] = {
            "total_tests": total_tests,
            "successful_tests": successful_tests,
            "failed_tests": total_tests - successful_tests,
            "success_rate_percent": (successful_tests / total_tests) * 100,
            "overall_success": successful_tests == total_tests,
            "total_duration_seconds": total_duration,
            "execution_mode": "parallel" if parallel else "sequential",
            "deployment_status": "READY" if successful_tests == total_tests else "ISSUES" if successful_tests >= total_tests * 0.75 else "FAILED"
        }
        
        # Log summary
        summary = self.test_results["summary"]
        if summary["overall_success"]:
            self.logger.info(f"✓ All tests passed ({successful_tests}/{total_tests}) - Deployment is READY")
        elif summary["deployment_status"] == "ISSUES":
            self.logger.warning(f"⚠ Most tests passed ({successful_tests}/{total_tests}) - Deployment has ISSUES")
        else:
            self.logger.error(f"✗ Many tests failed ({successful_tests}/{total_tests}) - Deployment FAILED")
        
        return self.test_results
    
    async def run_specific_tests(self, test_names: List[str]) -> Dict[str, Any]:
        """Run specific tests by name."""
        self.logger.info(f"Running specific tests: {', '.join(test_names)}")
        start_time = time.time()
        
        for test_name in test_names:
            if test_name not in self.test_scripts:
                self.logger.error(f"Unknown test: {test_name}")
                self.test_results["test_execution"][test_name] = {
                    "success": False,
                    "error": f"Unknown test: {test_name}",
                    "duration_seconds": 0
                }
                continue
            
            script_config = self.test_scripts[test_name]
            result = await self.run_script(test_name, script_config)
            self.test_results["test_execution"][test_name] = result
        
        # Generate summary
        total_duration = time.time() - start_time
        successful_tests = sum(1 for r in self.test_results["test_execution"].values() if r["success"])
        total_tests = len(test_names)
        
        self.test_results["summary"] = {
            "total_tests": total_tests,
            "successful_tests": successful_tests,
            "failed_tests": total_tests - successful_tests,
            "success_rate_percent": (successful_tests / total_tests) * 100 if total_tests > 0 else 0,
            "overall_success": successful_tests == total_tests,
            "total_duration_seconds": total_duration,
            "execution_mode": "specific",
            "requested_tests": test_names
        }
        
        return self.test_results
    
    def save_results(self, output_file: Optional[str] = None) -> str:
        """Save test results to a JSON file."""
        if output_file is None:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            output_file = f"deployment_test_results_{self.environment}_{timestamp}.json"
        
        output_path = project_root / "tests" / "results" / output_file
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(self.test_results, f, indent=2)
        
        self.logger.info(f"Test results saved to: {output_path}")
        return str(output_path)
    
    def print_summary(self) -> None:
        """Print a formatted summary of test results."""
        summary = self.test_results.get("summary", {})
        
        print("\n" + "="*80)
        print(f"DEPLOYMENT TEST RESULTS SUMMARY")
        print("="*80)
        print(f"Environment: {summary.get('environment', self.environment)}")
        print(f"Test Time: {self.test_results.get('timestamp', 'Unknown')}")
        print(f"Duration: {summary.get('total_duration_seconds', 0):.2f} seconds")
        print(f"Execution Mode: {summary.get('execution_mode', 'unknown')}")
        print()
        
        deployment_status = summary.get('deployment_status', 'UNKNOWN')
        status_symbols = {"READY": "✓", "ISSUES": "⚠", "FAILED": "✗", "UNKNOWN": "?"}
        status_symbol = status_symbols.get(deployment_status, "?")
        
        print(f"Deployment Status: {status_symbol} {deployment_status}")
        print(f"Success Rate: {summary.get('success_rate_percent', 0):.1f}% ({summary.get('successful_tests', 0)}/{summary.get('total_tests', 0)})")
        print()
        
        print("Individual Test Results:")
        print("-" * 60)
        
        for test_name, test_result in self.test_results.get("test_execution", {}).items():
            status = "✓ PASS" if test_result.get("success") else "✗ FAIL"
            duration = test_result.get("duration_seconds", 0)
            description = self.test_scripts.get(test_name, {}).get("description", "Unknown test")
            
            print(f"{test_name:15} {status:8} {duration:8.2f}s  {description}")
            
            # Show error if failed
            if not test_result.get("success") and test_result.get("error"):
                error_msg = test_result["error"][:100] + "..." if len(test_result["error"]) > 100 else test_result["error"]
                print(f"{'':15} Error: {error_msg}")
            
            # Show result file if available
            if test_result.get("result_file"):
                print(f"{'':15} Results: {test_result['result_file']}")
        
        print("\n" + "="*80)
        
        # Recommendations based on results
        if deployment_status == "READY":
            print("🎉 Deployment validation successful! The agent is ready for use.")
        elif deployment_status == "ISSUES":
            print("⚠️  Deployment has some issues but core functionality works.")
            print("   Review failed tests and consider addressing issues before production use.")
        else:
            print("❌ Deployment validation failed! Critical issues detected.")
            print("   Address failed tests before deploying to production.")
        
        print("="*80)


async def main():
    """Main function to run deployment tests."""
    parser = argparse.ArgumentParser(description="Run deployment and testing scripts")
    parser.add_argument(
        "--environment", "-e",
        choices=["development", "staging", "production"],
        default="production",
        help="Environment to test (default: production)"
    )
    parser.add_argument(
        "--tests", "-t",
        nargs="+",
        choices=["connectivity", "validation", "e2e", "health"],
        help="Specific tests to run (default: all tests)"
    )
    parser.add_argument(
        "--parallel", "-p",
        action="store_true",
        help="Run tests in parallel (faster but less detailed error reporting)"
    )
    parser.add_argument(
        "--output", "-o",
        help="Output file for test results (default: auto-generated)"
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
    
    # Initialize test runner
    runner = DeploymentTestRunner(
        environment=args.environment,
        verbose=args.verbose
    )
    
    try:
        # Run tests
        if args.tests:
            results = await runner.run_specific_tests(args.tests)
        else:
            results = await runner.run_all_tests(parallel=args.parallel)
        
        # Save results
        output_file = runner.save_results(args.output)
        
        # Print summary unless quiet mode
        if not args.quiet:
            runner.print_summary()
        
        # Exit with appropriate code
        success = results.get("summary", {}).get("overall_success", False)
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\nTest execution interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"Test execution failed with error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())