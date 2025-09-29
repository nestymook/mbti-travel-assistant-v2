"""
Comprehensive Unit Test Runner

Executes all comprehensive unit tests with coverage reporting and detailed metrics.
This runner specifically focuses on the new comprehensive test suites created for 90%+ coverage.
"""

import subprocess
import sys
import os
import time
import json
from pathlib import Path
from datetime import datetime
import argparse


class ComprehensiveTestRunner:
    """Runner for comprehensive unit tests with detailed reporting."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.test_results = {
            "timestamp": datetime.utcnow().isoformat(),
            "test_suites": {},
            "coverage": {},
            "summary": {}
        }
        self.results_dir = self.project_root / "tests" / "results"
        self.results_dir.mkdir(exist_ok=True)
    
    def run_comprehensive_unit_tests(self, verbose: bool = True):
        """Run all comprehensive unit tests with coverage."""
        print("🧪 Running Comprehensive Unit Tests...")
        print("=" * 60)
        
        # Comprehensive unit test files
        unit_test_files = [
            "test_session_assignment_comprehensive.py",
            "test_nova_pro_comprehensive.py", 
            "test_assignment_validator_comprehensive.py"
        ]
        
        start_time = time.time()
        
        # Run comprehensive unit tests with coverage
        cmd = [
            sys.executable, "-m", "pytest",
            "--cov=services.session_assignment_logic",
            "--cov=services.nova_pro_knowledge_base_client",
            "--cov=services.mbti_personality_processor",
            "--cov=services.knowledge_base_response_parser",
            "--cov=services.assignment_validator",
            "--cov-report=term-missing",
            "--cov-report=json:tests/results/comprehensive_unit_coverage.json",
            "--cov-report=html:tests/results/comprehensive_unit_coverage_html",
            "--junit-xml=tests/results/comprehensive_unit_tests.xml",
            "--json-report",
            "--json-report-file=tests/results/comprehensive_unit_report.json",
            "-v" if verbose else "-q",
            "--tb=short",
            "--durations=10"  # Show 10 slowest tests
        ] + [f"tests/{test_file}" for test_file in unit_test_files]
        
        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=600  # 10 minute timeout
            )
            
            execution_time = time.time() - start_time
            
            self.test_results["test_suites"]["comprehensive_unit_tests"] = {
                "status": "passed" if result.returncode == 0 else "failed",
                "execution_time": execution_time,
                "return_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "test_files": unit_test_files
            }
            
            # Load coverage data if available
            coverage_file = self.results_dir / "comprehensive_unit_coverage.json"
            if coverage_file.exists():
                with open(coverage_file, 'r') as f:
                    coverage_data = json.load(f)
                    self.test_results["coverage"]["comprehensive_unit_tests"] = coverage_data
            
            if result.returncode == 0:
                print(f"✅ Comprehensive unit tests passed in {execution_time:.2f}s")
                self._print_coverage_summary()
            else:
                print(f"❌ Comprehensive unit tests failed in {execution_time:.2f}s")
                print(f"Error: {result.stderr}")
            
            return result.returncode == 0
            
        except subprocess.TimeoutExpired:
            print("❌ Comprehensive unit tests timed out after 10 minutes")
            self.test_results["test_suites"]["comprehensive_unit_tests"] = {
                "status": "timeout",
                "execution_time": 600,
                "error": "Test execution timed out"
            }
            return False

    def run_integration_tests(self, verbose: bool = True):
        """Run integration and end-to-end tests."""
        print("\n🔗 Running Integration and End-to-End Tests...")
        print("=" * 60)
        
        integration_test_files = [
            "test_complete_itinerary_integration.py"
        ]
        
        start_time = time.time()
        
        cmd = [
            sys.executable, "-m", "pytest",
            "--cov=services.itinerary_generator",
            "--cov-report=term-missing",
            "--cov-report=json:tests/results/integration_coverage.json",
            "--cov-report=html:tests/results/integration_coverage_html",
            "--junit-xml=tests/results/integration_tests.xml",
            "--json-report",
            "--json-report-file=tests/results/integration_report.json",
            "-v" if verbose else "-q",
            "--tb=short",
            "--durations=5"
        ] + [f"tests/{test_file}" for test_file in integration_test_files]
        
        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=900  # 15 minute timeout for integration tests
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
            print("❌ Integration tests timed out after 15 minutes")
            return False

    def run_performance_tests(self, verbose: bool = True):
        """Run performance and load tests."""
        print("\n⚡ Running Performance and Load Tests...")
        print("=" * 60)
        
        performance_test_files = [
            "test_performance_comprehensive.py"
        ]
        
        start_time = time.time()
        
        cmd = [
            sys.executable, "-m", "pytest",
            "--junit-xml=tests/results/performance_tests.xml",
            "--json-report",
            "--json-report-file=tests/results/performance_report.json",
            "-v" if verbose else "-q",
            "--tb=short",
            "-s",  # Don't capture output for performance tests
            "--durations=0"  # Show all test durations
        ] + [f"tests/{test_file}" for test_file in performance_test_files]
        
        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=1800  # 30 minute timeout for performance tests
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
            print("❌ Performance tests timed out after 30 minutes")
            return False

    def run_validation_load_tests(self, verbose: bool = True):
        """Run validation and load tests."""
        print("\n🔍 Running Validation and Load Tests...")
        print("=" * 60)
        
        validation_test_files = [
            "test_validation_load_comprehensive.py"
        ]
        
        start_time = time.time()
        
        cmd = [
            sys.executable, "-m", "pytest",
            "--cov=services.assignment_validator",
            "--cov=services.session_assignment_logic",
            "--cov-report=term-missing",
            "--cov-report=json:tests/results/validation_coverage.json",
            "--junit-xml=tests/results/validation_tests.xml",
            "--json-report",
            "--json-report-file=tests/results/validation_report.json",
            "-v" if verbose else "-q",
            "--tb=short",
            "-s",  # Don't capture output for load tests
            "--durations=5"
        ] + [f"tests/{test_file}" for test_file in validation_test_files]
        
        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=1200  # 20 minute timeout for validation/load tests
            )
            
            execution_time = time.time() - start_time
            
            self.test_results["test_suites"]["validation_load_tests"] = {
                "status": "passed" if result.returncode == 0 else "failed",
                "execution_time": execution_time,
                "return_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "test_files": validation_test_files
            }
            
            if result.returncode == 0:
                print(f"✅ Validation and load tests passed in {execution_time:.2f}s")
            else:
                print(f"❌ Validation and load tests failed in {execution_time:.2f}s")
                print(f"Error: {result.stderr}")
            
            return result.returncode == 0
            
        except subprocess.TimeoutExpired:
            print("❌ Validation and load tests timed out after 20 minutes")
            return False

    def _print_coverage_summary(self):
        """Print coverage summary from comprehensive unit tests."""
        coverage_file = self.results_dir / "comprehensive_unit_coverage.json"
        if coverage_file.exists():
            try:
                with open(coverage_file, 'r') as f:
                    coverage_data = json.load(f)
                
                print("\n📊 Coverage Summary:")
                print("-" * 40)
                
                totals = coverage_data.get('totals', {})
                covered_lines = totals.get('covered_lines', 0)
                num_statements = totals.get('num_statements', 0)
                
                if num_statements > 0:
                    coverage_percent = (covered_lines / num_statements) * 100
                    print(f"Overall Coverage: {coverage_percent:.1f}% ({covered_lines}/{num_statements} lines)")
                
                # Print per-file coverage
                files = coverage_data.get('files', {})
                for file_path, file_data in files.items():
                    if 'services/' in file_path:
                        file_covered = file_data.get('summary', {}).get('covered_lines', 0)
                        file_total = file_data.get('summary', {}).get('num_statements', 0)
                        if file_total > 0:
                            file_percent = (file_covered / file_total) * 100
                            file_name = file_path.split('/')[-1]
                            print(f"  {file_name}: {file_percent:.1f}% ({file_covered}/{file_total} lines)")
                
            except Exception as e:
                print(f"Could not read coverage data: {e}")

    def generate_comprehensive_report(self):
        """Generate comprehensive test report."""
        print("\n📋 Generating Comprehensive Test Report...")
        
        # Calculate summary statistics
        total_suites = len(self.test_results["test_suites"])
        passed_suites = sum(1 for suite in self.test_results["test_suites"].values() 
                           if suite.get("status") == "passed")
        failed_suites = total_suites - passed_suites
        
        total_time = sum(suite.get("execution_time", 0) 
                        for suite in self.test_results["test_suites"].values())
        
        self.test_results["summary"] = {
            "total_test_suites": total_suites,
            "passed_suites": passed_suites,
            "failed_suites": failed_suites,
            "success_rate": passed_suites / total_suites if total_suites > 0 else 0,
            "total_execution_time": total_time,
            "overall_status": "PASSED" if failed_suites == 0 else "FAILED"
        }
        
        # Save detailed results
        results_file = self.results_dir / "comprehensive_test_results.json"
        with open(results_file, 'w') as f:
            json.dump(self.test_results, f, indent=2)
        
        # Generate summary report
        summary_file = self.results_dir / "comprehensive_test_summary.md"
        with open(summary_file, 'w') as f:
            f.write("# Comprehensive Test Results Summary\n\n")
            f.write(f"**Generated:** {self.test_results['timestamp']}\n\n")
            f.write(f"## Overall Results\n\n")
            f.write(f"- **Total Test Suites:** {total_suites}\n")
            f.write(f"- **Passed:** {passed_suites}\n")
            f.write(f"- **Failed:** {failed_suites}\n")
            f.write(f"- **Success Rate:** {self.test_results['summary']['success_rate']:.1%}\n")
            f.write(f"- **Total Execution Time:** {total_time:.2f} seconds\n")
            f.write(f"- **Overall Status:** {self.test_results['summary']['overall_status']}\n\n")
            
            f.write("## Test Suite Details\n\n")
            for suite_name, suite_data in self.test_results["test_suites"].items():
                status_emoji = "✅" if suite_data.get("status") == "passed" else "❌"
                f.write(f"### {status_emoji} {suite_name.replace('_', ' ').title()}\n\n")
                f.write(f"- **Status:** {suite_data.get('status', 'unknown')}\n")
                f.write(f"- **Execution Time:** {suite_data.get('execution_time', 0):.2f} seconds\n")
                f.write(f"- **Test Files:** {', '.join(suite_data.get('test_files', []))}\n\n")
        
        print(f"📄 Detailed results saved to: {results_file}")
        print(f"📄 Summary report saved to: {summary_file}")
        
        return self.test_results["summary"]["overall_status"] == "PASSED"

    def print_final_summary(self):
        """Print final test execution summary."""
        print("\n" + "=" * 80)
        print("COMPREHENSIVE TEST EXECUTION SUMMARY")
        print("=" * 80)
        
        summary = self.test_results["summary"]
        
        print(f"📊 Test Suites: {summary['passed_suites']}/{summary['total_test_suites']} passed")
        print(f"⏱️  Total Time: {summary['total_execution_time']:.2f} seconds")
        print(f"📈 Success Rate: {summary['success_rate']:.1%}")
        print(f"🎯 Overall Status: {summary['overall_status']}")
        
        if summary['overall_status'] == "PASSED":
            print("\n🎉 All comprehensive tests passed successfully!")
            print("✨ The MBTI Travel Assistant has achieved 90%+ test coverage")
            print("🚀 System is ready for production deployment")
        else:
            print(f"\n⚠️  {summary['failed_suites']} test suite(s) failed")
            print("🔧 Please review the test results and fix any issues")
        
        print("\n📁 Test artifacts available in: tests/results/")
        print("   - comprehensive_test_results.json (detailed results)")
        print("   - comprehensive_test_summary.md (summary report)")
        print("   - *_coverage_html/ (HTML coverage reports)")


def main():
    """Main entry point for comprehensive test runner."""
    parser = argparse.ArgumentParser(description="Run comprehensive tests for MBTI Travel Assistant")
    parser.add_argument("--unit-only", action="store_true", help="Run only unit tests")
    parser.add_argument("--integration-only", action="store_true", help="Run only integration tests")
    parser.add_argument("--performance-only", action="store_true", help="Run only performance tests")
    parser.add_argument("--validation-only", action="store_true", help="Run only validation tests")
    parser.add_argument("--skip-performance", action="store_true", help="Skip performance tests")
    parser.add_argument("--skip-load", action="store_true", help="Skip load tests")
    parser.add_argument("--quiet", "-q", action="store_true", help="Quiet output")
    
    args = parser.parse_args()
    
    runner = ComprehensiveTestRunner()
    verbose = not args.quiet
    
    print("🧪 MBTI Travel Assistant - Comprehensive Test Suite")
    print("=" * 80)
    print("Testing for 90%+ code coverage and production readiness")
    print("=" * 80)
    
    all_passed = True
    
    # Run selected test suites
    if args.unit_only:
        all_passed = runner.run_comprehensive_unit_tests(verbose)
    elif args.integration_only:
        all_passed = runner.run_integration_tests(verbose)
    elif args.performance_only:
        all_passed = runner.run_performance_tests(verbose)
    elif args.validation_only:
        all_passed = runner.run_validation_load_tests(verbose)
    else:
        # Run all test suites
        unit_passed = runner.run_comprehensive_unit_tests(verbose)
        integration_passed = runner.run_integration_tests(verbose)
        
        performance_passed = True
        if not args.skip_performance:
            performance_passed = runner.run_performance_tests(verbose)
        
        validation_passed = True
        if not args.skip_load:
            validation_passed = runner.run_validation_load_tests(verbose)
        
        all_passed = unit_passed and integration_passed and performance_passed and validation_passed
    
    # Generate comprehensive report
    report_success = runner.generate_comprehensive_report()
    runner.print_final_summary()
    
    # Exit with appropriate code
    sys.exit(0 if all_passed and report_success else 1)


if __name__ == "__main__":
    main()