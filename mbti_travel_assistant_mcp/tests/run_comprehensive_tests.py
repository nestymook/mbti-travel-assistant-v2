"""
Comprehensive Test Runner

Executes all unit tests, integration tests, and performance tests
with coverage reporting and detailed metrics.
"""

import subprocess
import sys
import os
import time
import json
from pathlib import Path
from datetime import datetime


class TestRunner:
    """Comprehensive test runner with coverage and reporting."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.test_results = {
            "timestamp": datetime.utcnow().isoformat(),
            "test_suites": {},
            "coverage": {},
            "summary": {}
        }
    
    def run_unit_tests(self):
        """Run all unit tests with coverage."""
        print("🧪 Running Unit Tests...")
        
        unit_test_files = [
            "test_mcp_client_manager.py",
            "test_jwt_auth_handler.py", 
            "test_response_validation.py",
            "test_response_formatter.py",
            "test_error_handler.py",
            "test_cache_service_comprehensive.py",
            "test_restaurant_agent_comprehensive.py"
        ]
        
        start_time = time.time()
        
        # Run unit tests with coverage
        cmd = [
            sys.executable, "-m", "pytest",
            "--cov=services",
            "--cov=models", 
            "--cov=main",
            "--cov-report=term-missing",
            "--cov-report=json:tests/results/unit_coverage.json",
            "--cov-report=html:tests/results/unit_coverage_html",
            "--junit-xml=tests/results/unit_tests.xml",
            "-v",
            "--tb=short"
        ] + [f"tests/{test_file}" for test_file in unit_test_files]
        
        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            execution_time = time.time() - start_time
            
            self.test_results["test_suites"]["unit_tests"] = {
                "status": "passed" if result.returncode == 0 else "failed",
                "execution_time": execution_time,
                "return_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "test_files": unit_test_files
            }
            
            # Load coverage data if available
            coverage_file = self.project_root / "tests" / "results" / "unit_coverage.json"
            if coverage_file.exists():
                with open(coverage_file, 'r') as f:
                    coverage_data = json.load(f)
                    self.test_results["coverage"]["unit_tests"] = coverage_data
            
            if result.returncode == 0:
                print(f"✅ Unit tests passed in {execution_time:.2f}s")
            else:
                print(f"❌ Unit tests failed in {execution_time:.2f}s")
                print(f"Error: {result.stderr}")
            
            return result.returncode == 0
            
        except subprocess.TimeoutExpired:
            print("❌ Unit tests timed out after 5 minutes")
            self.test_results["test_suites"]["unit_tests"] = {
                "status": "timeout",
                "execution_time": 300,
                "error": "Test execution timed out"
            }
            return False
        except Exception as e:
            print(f"❌ Error running unit tests: {e}")
            self.test_results["test_suites"]["unit_tests"] = {
                "status": "error",
                "error": str(e)
            }
            return False
    
    def run_integration_tests(self):
        """Run all integration tests."""
        print("🔗 Running Integration Tests...")
        
        integration_test_files = [
            "test_entrypoint_integration.py",
            "test_mock_mcp_integration.py",
            "test_cognito_integration.py",
            "test_mcp_integration.py",
            "test_jwt_integration.py"
        ]
        
        start_time = time.time()
        
        # Run integration tests
        cmd = [
            sys.executable, "-m", "pytest",
            "--junit-xml=tests/results/integration_tests.xml",
            "-v",
            "--tb=short",
            "-m", "not slow"  # Skip slow tests by default
        ] + [f"tests/{test_file}" for test_file in integration_test_files]
        
        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=600  # 10 minute timeout
            )
            
            execution_time = time.time() - start_time
            
            self.test_results["test_suites"]["integration_tests"] = {
                "status": "passed" if result.returncode == 0 else "failed",
                "execution_time": execution_time,
                "return_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "test_files": integration_test_files
            }
            
            if result.returncode == 0:
                print(f"✅ Integration tests passed in {execution_time:.2f}s")
            else:
                print(f"❌ Integration tests failed in {execution_time:.2f}s")
                print(f"Error: {result.stderr}")
            
            return result.returncode == 0
            
        except subprocess.TimeoutExpired:
            print("❌ Integration tests timed out after 10 minutes")
            self.test_results["test_suites"]["integration_tests"] = {
                "status": "timeout",
                "execution_time": 600,
                "error": "Test execution timed out"
            }
            return False
        except Exception as e:
            print(f"❌ Error running integration tests: {e}")
            self.test_results["test_suites"]["integration_tests"] = {
                "status": "error",
                "error": str(e)
            }
            return False
    
    def run_performance_tests(self):
        """Run performance and load tests."""
        print("⚡ Running Performance Tests...")
        
        performance_test_files = [
            "test_performance_load.py"
        ]
        
        start_time = time.time()
        
        # Run performance tests
        cmd = [
            sys.executable, "-m", "pytest",
            "--junit-xml=tests/results/performance_tests.xml",
            "-v",
            "--tb=short",
            "-s"  # Don't capture output for performance metrics
        ] + [f"tests/{test_file}" for test_file in performance_test_files]
        
        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=900  # 15 minute timeout
            )
            
            execution_time = time.time() - start_time
            
            self.test_results["test_suites"]["performance_tests"] = {
                "status": "passed" if result.returncode == 0 else "failed",
                "execution_time": execution_time,
                "return_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "test_files": performance_test_files
            }
            
            if result.returncode == 0:
                print(f"✅ Performance tests passed in {execution_time:.2f}s")
            else:
                print(f"❌ Performance tests failed in {execution_time:.2f}s")
                print(f"Error: {result.stderr}")
            
            return result.returncode == 0
            
        except subprocess.TimeoutExpired:
            print("❌ Performance tests timed out after 15 minutes")
            self.test_results["test_suites"]["performance_tests"] = {
                "status": "timeout",
                "execution_time": 900,
                "error": "Test execution timed out"
            }
            return False
        except Exception as e:
            print(f"❌ Error running performance tests: {e}")
            self.test_results["test_suites"]["performance_tests"] = {
                "status": "error",
                "error": str(e)
            }
            return False
    
    def generate_summary_report(self):
        """Generate comprehensive test summary report."""
        print("\n📊 Generating Test Summary Report...")
        
        # Calculate summary statistics
        total_suites = len(self.test_results["test_suites"])
        passed_suites = sum(1 for suite in self.test_results["test_suites"].values() 
                           if suite.get("status") == "passed")
        failed_suites = sum(1 for suite in self.test_results["test_suites"].values() 
                           if suite.get("status") == "failed")
        
        total_time = sum(suite.get("execution_time", 0) 
                        for suite in self.test_results["test_suites"].values())
        
        self.test_results["summary"] = {
            "total_test_suites": total_suites,
            "passed_suites": passed_suites,
            "failed_suites": failed_suites,
            "success_rate": (passed_suites / total_suites * 100) if total_suites > 0 else 0,
            "total_execution_time": total_time,
            "overall_status": "passed" if failed_suites == 0 else "failed"
        }
        
        # Extract coverage information
        if "unit_tests" in self.test_results["coverage"]:
            coverage_data = self.test_results["coverage"]["unit_tests"]
            if "totals" in coverage_data:
                self.test_results["summary"]["coverage_percentage"] = coverage_data["totals"]["percent_covered"]
        
        # Create results directory
        results_dir = self.project_root / "tests" / "results"
        results_dir.mkdir(exist_ok=True)
        
        # Save detailed results
        results_file = results_dir / "comprehensive_test_results.json"
        with open(results_file, 'w') as f:
            json.dump(self.test_results, f, indent=2)
        
        # Generate human-readable report
        report_file = results_dir / "test_summary_report.md"
        with open(report_file, 'w') as f:
            f.write(self._generate_markdown_report())
        
        print(f"📄 Detailed results saved to: {results_file}")
        print(f"📄 Summary report saved to: {report_file}")
    
    def _generate_markdown_report(self):
        """Generate markdown summary report."""
        summary = self.test_results["summary"]
        
        report = f"""# Comprehensive Test Results

**Generated:** {self.test_results["timestamp"]}

## Summary

- **Overall Status:** {'✅ PASSED' if summary["overall_status"] == "passed" else '❌ FAILED'}
- **Test Suites:** {summary["passed_suites"]}/{summary["total_test_suites"]} passed
- **Success Rate:** {summary["success_rate"]:.1f}%
- **Total Execution Time:** {summary["total_execution_time"]:.2f}s
"""
        
        if "coverage_percentage" in summary:
            report += f"- **Code Coverage:** {summary['coverage_percentage']:.1f}%\n"
        
        report += "\n## Test Suite Results\n\n"
        
        for suite_name, suite_data in self.test_results["test_suites"].items():
            status_icon = "✅" if suite_data.get("status") == "passed" else "❌"
            execution_time = suite_data.get("execution_time", 0)
            
            report += f"### {suite_name.replace('_', ' ').title()}\n\n"
            report += f"- **Status:** {status_icon} {suite_data.get('status', 'unknown').upper()}\n"
            report += f"- **Execution Time:** {execution_time:.2f}s\n"
            
            if "test_files" in suite_data:
                report += f"- **Test Files:** {len(suite_data['test_files'])}\n"
                for test_file in suite_data["test_files"]:
                    report += f"  - {test_file}\n"
            
            if suite_data.get("status") == "failed" and "stderr" in suite_data:
                report += f"\n**Error Output:**\n```\n{suite_data['stderr'][:500]}...\n```\n"
            
            report += "\n"
        
        # Add coverage details if available
        if "unit_tests" in self.test_results["coverage"]:
            coverage_data = self.test_results["coverage"]["unit_tests"]
            if "files" in coverage_data:
                report += "## Code Coverage Details\n\n"
                report += "| File | Coverage | Missing Lines |\n"
                report += "|------|----------|---------------|\n"
                
                for file_path, file_data in coverage_data["files"].items():
                    filename = file_path.split("/")[-1]
                    coverage_pct = file_data["summary"]["percent_covered"]
                    missing_lines = len(file_data.get("missing_lines", []))
                    report += f"| {filename} | {coverage_pct:.1f}% | {missing_lines} |\n"
        
        report += f"\n## Recommendations\n\n"
        
        if summary["success_rate"] < 100:
            report += "- ❗ Some tests are failing. Review the error output above and fix failing tests.\n"
        
        if "coverage_percentage" in summary and summary["coverage_percentage"] < 90:
            report += f"- ❗ Code coverage is {summary['coverage_percentage']:.1f}%, below the 90% target. Add more unit tests.\n"
        
        if summary["total_execution_time"] > 300:
            report += "- ⚠️ Test execution time is high. Consider optimizing slow tests or running them separately.\n"
        
        if summary["success_rate"] == 100 and summary.get("coverage_percentage", 0) >= 90:
            report += "- ✅ All tests passing with good coverage! Great work!\n"
        
        return report
    
    def print_summary(self):
        """Print test execution summary to console."""
        summary = self.test_results["summary"]
        
        print("\n" + "="*60)
        print("📊 COMPREHENSIVE TEST RESULTS SUMMARY")
        print("="*60)
        
        print(f"Overall Status: {'✅ PASSED' if summary['overall_status'] == 'passed' else '❌ FAILED'}")
        print(f"Test Suites: {summary['passed_suites']}/{summary['total_test_suites']} passed ({summary['success_rate']:.1f}%)")
        print(f"Total Time: {summary['total_execution_time']:.2f}s")
        
        if "coverage_percentage" in summary:
            coverage_icon = "✅" if summary["coverage_percentage"] >= 90 else "⚠️"
            print(f"Coverage: {coverage_icon} {summary['coverage_percentage']:.1f}%")
        
        print("\nTest Suite Breakdown:")
        for suite_name, suite_data in self.test_results["test_suites"].items():
            status_icon = "✅" if suite_data.get("status") == "passed" else "❌"
            execution_time = suite_data.get("execution_time", 0)
            print(f"  {status_icon} {suite_name.replace('_', ' ').title()}: {execution_time:.2f}s")
        
        print("="*60)
    
    def run_all_tests(self):
        """Run all test suites and generate comprehensive report."""
        print("🚀 Starting Comprehensive Test Suite")
        print("="*60)
        
        # Create results directory
        results_dir = self.project_root / "tests" / "results"
        results_dir.mkdir(exist_ok=True)
        
        # Run all test suites
        unit_success = self.run_unit_tests()
        integration_success = self.run_integration_tests()
        performance_success = self.run_performance_tests()
        
        # Generate reports
        self.generate_summary_report()
        self.print_summary()
        
        # Return overall success
        return unit_success and integration_success and performance_success


def main():
    """Main entry point for test runner."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Comprehensive Test Runner")
    parser.add_argument("--unit-only", action="store_true", help="Run only unit tests")
    parser.add_argument("--integration-only", action="store_true", help="Run only integration tests")
    parser.add_argument("--performance-only", action="store_true", help="Run only performance tests")
    parser.add_argument("--skip-performance", action="store_true", help="Skip performance tests")
    
    args = parser.parse_args()
    
    runner = TestRunner()
    
    if args.unit_only:
        success = runner.run_unit_tests()
        runner.generate_summary_report()
        runner.print_summary()
    elif args.integration_only:
        success = runner.run_integration_tests()
        runner.generate_summary_report()
        runner.print_summary()
    elif args.performance_only:
        success = runner.run_performance_tests()
        runner.generate_summary_report()
        runner.print_summary()
    else:
        # Run all tests (optionally skip performance)
        unit_success = runner.run_unit_tests()
        integration_success = runner.run_integration_tests()
        
        if args.skip_performance:
            performance_success = True
            print("⏭️ Skipping performance tests")
        else:
            performance_success = runner.run_performance_tests()
        
        runner.generate_summary_report()
        runner.print_summary()
        
        success = unit_success and integration_success and performance_success
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()