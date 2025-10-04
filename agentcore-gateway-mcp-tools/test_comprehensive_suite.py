#!/usr/bin/env python3
"""
Comprehensive test suite runner for AgentCore Gateway MCP Tools.

This script executes all test categories required by task 11 and provides
detailed reporting on test coverage and results.
"""

import sys
import subprocess
import os
import json
import time
from pathlib import Path
from typing import Dict, List, Any
from dataclasses import dataclass, asdict


@dataclass
class TestResult:
    """Test result data structure."""
    category: str
    file: str
    passed: int
    failed: int
    skipped: int
    errors: int
    duration: float
    success: bool
    output: str = ""
    error_output: str = ""


@dataclass
class TestSummary:
    """Overall test summary."""
    total_categories: int
    total_files: int
    total_tests: int
    total_passed: int
    total_failed: int
    total_skipped: int
    total_errors: int
    total_duration: float
    success_rate: float
    results: List[TestResult]


class ComprehensiveTestRunner:
    """Comprehensive test runner for all test categories."""
    
    def __init__(self):
        """Initialize test runner."""
        self.workspace_root = Path(__file__).parent
        self.test_categories = {
            "Unit Tests - Authentication & JWT": [
                "tests/test_auth_middleware.py",
                "tests/test_jwt_validation.py"
            ],
            "Unit Tests - MCP Client Manager": [
                "tests/test_mcp_client_manager.py"
            ],
            "Integration Tests - MCP Communication": [
                "tests/test_mcp_client_integration.py"
            ],
            "End-to-End API Tests": [
                "tests/test_api_endpoints_e2e.py",
                "tests/test_restaurant_endpoints.py",
                "tests/test_tool_metadata_endpoints.py",
                "tests/test_reasoning_endpoints_integration.py",
                "tests/test_reasoning_endpoints_unit.py"
            ],
            "Security Tests - Authentication Bypass": [
                "tests/test_security_bypass_attempts.py"
            ],
            "Performance Tests - Concurrent Handling": [
                "tests/test_performance_concurrent.py"
            ],
            "Backward Compatibility Tests": [
                "tests/test_backward_compatibility.py"
            ],
            "Model Validation Tests": [
                "tests/test_request_models.py",
                "tests/test_response_models.py",
                "tests/test_validation_models.py",
                "tests/test_tool_metadata_models.py"
            ],
            "Error Handling Tests": [
                "tests/test_error_handler.py",
                "tests/test_error_handling_integration.py",
                "tests/test_error_service.py",
                "tests/test_error_models.py"
            ],
            "Observability Tests": [
                "tests/test_observability_endpoints.py",
                "tests/test_observability_integration.py",
                "tests/test_observability_middleware.py",
                "tests/test_observability_service.py"
            ]
        }
        
        # Task 11 requirements mapping
        self.requirements_mapping = {
            "7.1": ["Unit Tests - Authentication & JWT"],
            "7.2": ["Unit Tests - MCP Client Manager", "Integration Tests - MCP Communication"],
            "7.3": ["End-to-End API Tests"],
            "7.4": [
                "Security Tests - Authentication Bypass",
                "Performance Tests - Concurrent Handling", 
                "Backward Compatibility Tests"
            ]
        }
    
    def setup_environment(self):
        """Set up test environment."""
        os.environ["PYTHONPATH"] = str(self.workspace_root)
        os.environ["TESTING"] = "1"
        os.environ["LOG_LEVEL"] = "WARNING"  # Reduce log noise during testing
        
        print("🔧 Setting up test environment...")
        print(f"   Workspace: {self.workspace_root}")
        print(f"   Python path: {os.environ['PYTHONPATH']}")
        print(f"   Test categories: {len(self.test_categories)}")
    
    def run_test_file(self, test_file: str, category: str) -> TestResult:
        """Run a single test file and return results."""
        file_path = self.workspace_root / test_file
        
        if not file_path.exists():
            return TestResult(
                category=category,
                file=test_file,
                passed=0,
                failed=1,
                skipped=0,
                errors=0,
                duration=0.0,
                success=False,
                error_output=f"Test file not found: {test_file}"
            )
        
        print(f"   📋 Running {test_file}")
        
        start_time = time.time()
        
        try:
            # Run pytest with standard output
            result = subprocess.run([
                sys.executable, "-m", "pytest",
                str(file_path),
                "-v",
                "--tb=short",
                "--disable-warnings",
                "--no-header"
            ], capture_output=True, text=True, timeout=180)
            
            duration = time.time() - start_time
            
            # Parse pytest output for test counts
            passed, failed, skipped, errors = self._parse_pytest_output(result.stdout)
            
            success = result.returncode == 0 and failed == 0 and errors == 0
            
            return TestResult(
                category=category,
                file=test_file,
                passed=passed,
                failed=failed,
                skipped=skipped,
                errors=errors,
                duration=duration,
                success=success,
                output=result.stdout,
                error_output=result.stderr
            )
            
        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            return TestResult(
                category=category,
                file=test_file,
                passed=0,
                failed=0,
                skipped=0,
                errors=1,
                duration=duration,
                success=False,
                error_output="Test execution timed out (180s)"
            )
        except Exception as e:
            duration = time.time() - start_time
            return TestResult(
                category=category,
                file=test_file,
                passed=0,
                failed=0,
                skipped=0,
                errors=1,
                duration=duration,
                success=False,
                error_output=f"Test execution error: {str(e)}"
            )
    
    def _parse_pytest_output(self, output: str) -> tuple:
        """Parse pytest output to extract test counts."""
        passed = failed = skipped = errors = 0
        
        lines = output.split('\n')
        for line in lines:
            line = line.strip().lower()
            
            # Look for summary line like "5 passed, 2 failed, 1 skipped"
            if 'passed' in line or 'failed' in line or 'error' in line:
                parts = line.split(',')
                for part in parts:
                    part = part.strip()
                    if 'passed' in part:
                        try:
                            passed = int(part.split()[0])
                        except (ValueError, IndexError):
                            pass
                    elif 'failed' in part:
                        try:
                            failed = int(part.split()[0])
                        except (ValueError, IndexError):
                            pass
                    elif 'skipped' in part:
                        try:
                            skipped = int(part.split()[0])
                        except (ValueError, IndexError):
                            pass
                    elif 'error' in part:
                        try:
                            errors = int(part.split()[0])
                        except (ValueError, IndexError):
                            pass
        
        # If no counts found, try to count individual test results
        if passed == 0 and failed == 0 and skipped == 0 and errors == 0:
            for line in lines:
                if '::' in line and ('PASSED' in line or 'FAILED' in line or 'SKIPPED' in line or 'ERROR' in line):
                    if 'PASSED' in line:
                        passed += 1
                    elif 'FAILED' in line:
                        failed += 1
                    elif 'SKIPPED' in line:
                        skipped += 1
                    elif 'ERROR' in line:
                        errors += 1
        
        return passed, failed, skipped, errors
    
    def run_category(self, category: str, test_files: List[str]) -> List[TestResult]:
        """Run all tests in a category."""
        print(f"\n🔍 {category}")
        print("=" * 70)
        
        results = []
        for test_file in test_files:
            result = self.run_test_file(test_file, category)
            results.append(result)
            
            # Print immediate result
            if result.success:
                print(f"   ✅ {test_file} - {result.passed} passed ({result.duration:.2f}s)")
            else:
                print(f"   ❌ {test_file} - {result.failed} failed, {result.errors} errors ({result.duration:.2f}s)")
                if result.error_output:
                    print(f"      Error: {result.error_output[:100]}...")
        
        # Category summary
        category_passed = sum(r.passed for r in results)
        category_failed = sum(r.failed for r in results)
        category_errors = sum(r.errors for r in results)
        category_duration = sum(r.duration for r in results)
        category_success = all(r.success for r in results)
        
        status = "✅" if category_success else "❌"
        print(f"\n{status} {category} Summary:")
        print(f"   Files: {len(results)}, Passed: {category_passed}, Failed: {category_failed}, Errors: {category_errors}")
        print(f"   Duration: {category_duration:.2f}s")
        
        return results
    
    def run_all_tests(self) -> TestSummary:
        """Run all test categories."""
        print("🚀 Starting Comprehensive Test Suite")
        print("=" * 70)
        
        self.setup_environment()
        
        all_results = []
        start_time = time.time()
        
        for category, test_files in self.test_categories.items():
            category_results = self.run_category(category, test_files)
            all_results.extend(category_results)
        
        total_duration = time.time() - start_time
        
        # Calculate summary statistics
        total_files = len(all_results)
        total_tests = sum(r.passed + r.failed + r.skipped + r.errors for r in all_results)
        total_passed = sum(r.passed for r in all_results)
        total_failed = sum(r.failed for r in all_results)
        total_skipped = sum(r.skipped for r in all_results)
        total_errors = sum(r.errors for r in all_results)
        
        success_rate = (total_passed / max(total_tests, 1)) * 100
        
        return TestSummary(
            total_categories=len(self.test_categories),
            total_files=total_files,
            total_tests=total_tests,
            total_passed=total_passed,
            total_failed=total_failed,
            total_skipped=total_skipped,
            total_errors=total_errors,
            total_duration=total_duration,
            success_rate=success_rate,
            results=all_results
        )
    
    def print_detailed_summary(self, summary: TestSummary):
        """Print detailed test summary."""
        print("\n" + "=" * 70)
        print("📊 COMPREHENSIVE TEST SUITE SUMMARY")
        print("=" * 70)
        
        # Overall statistics
        print(f"Total Categories: {summary.total_categories}")
        print(f"Total Test Files: {summary.total_files}")
        print(f"Total Tests: {summary.total_tests}")
        print(f"Duration: {summary.total_duration:.2f}s")
        print()
        
        # Results breakdown
        print("📈 RESULTS BREAKDOWN:")
        print(f"✅ Passed: {summary.total_passed}")
        print(f"❌ Failed: {summary.total_failed}")
        print(f"⏭️  Skipped: {summary.total_skipped}")
        print(f"💥 Errors: {summary.total_errors}")
        print(f"📊 Success Rate: {summary.success_rate:.1f}%")
        print()
        
        # Category breakdown
        print("📋 CATEGORY BREAKDOWN:")
        category_stats = {}
        for result in summary.results:
            if result.category not in category_stats:
                category_stats[result.category] = {
                    'files': 0, 'passed': 0, 'failed': 0, 'errors': 0, 'success': True
                }
            
            stats = category_stats[result.category]
            stats['files'] += 1
            stats['passed'] += result.passed
            stats['failed'] += result.failed
            stats['errors'] += result.errors
            stats['success'] = stats['success'] and result.success
        
        for category, stats in category_stats.items():
            status = "✅" if stats['success'] else "❌"
            print(f"{status} {category}:")
            print(f"   Files: {stats['files']}, Passed: {stats['passed']}, Failed: {stats['failed']}, Errors: {stats['errors']}")
        
        print()
        
        # Requirements coverage
        print("🎯 TASK 11 REQUIREMENTS COVERAGE:")
        for req_id, categories in self.requirements_mapping.items():
            req_success = True
            for category in categories:
                if category in category_stats:
                    req_success = req_success and category_stats[category]['success']
                else:
                    req_success = False
            
            status = "✅" if req_success else "❌"
            print(f"{status} Requirement {req_id}: {', '.join(categories)}")
        
        print()
        
        # Failed tests details
        failed_results = [r for r in summary.results if not r.success]
        if failed_results:
            print("🔍 FAILED TESTS DETAILS:")
            for result in failed_results:
                print(f"❌ {result.file} ({result.category})")
                if result.error_output:
                    print(f"   Error: {result.error_output[:200]}...")
                if result.failed > 0:
                    print(f"   Failed: {result.failed} tests")
                if result.errors > 0:
                    print(f"   Errors: {result.errors}")
                print()
        
        # Final verdict
        print("🏁 FINAL VERDICT:")
        if summary.success_rate >= 95:
            print("🎉 EXCELLENT! All tests passed. Gateway is ready for deployment.")
        elif summary.success_rate >= 80:
            print("✅ GOOD! Most tests passed. Minor issues need attention.")
        elif summary.success_rate >= 60:
            print("⚠️  FAIR! Significant issues need to be resolved.")
        else:
            print("❌ POOR! Major issues prevent deployment.")
        
        print(f"Overall Success Rate: {summary.success_rate:.1f}%")
    
    def save_results(self, summary: TestSummary, filename: str = "test_results.json"):
        """Save test results to JSON file."""
        results_file = self.workspace_root / filename
        
        # Convert to serializable format
        data = {
            "summary": asdict(summary),
            "timestamp": time.time(),
            "requirements_coverage": {}
        }
        
        # Add requirements coverage
        category_stats = {}
        for result in summary.results:
            if result.category not in category_stats:
                category_stats[result.category] = {'success': True}
            category_stats[result.category]['success'] = (
                category_stats[result.category]['success'] and result.success
            )
        
        for req_id, categories in self.requirements_mapping.items():
            req_success = all(
                category_stats.get(cat, {'success': False})['success'] 
                for cat in categories
            )
            data["requirements_coverage"][req_id] = req_success
        
        with open(results_file, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        
        print(f"📄 Test results saved to: {results_file}")


def main():
    """Main test runner function."""
    runner = ComprehensiveTestRunner()
    
    try:
        summary = runner.run_all_tests()
        runner.print_detailed_summary(summary)
        runner.save_results(summary)
        
        # Exit with appropriate code
        if summary.success_rate >= 95:
            sys.exit(0)  # Success
        elif summary.success_rate >= 80:
            sys.exit(1)  # Minor issues
        else:
            sys.exit(2)  # Major issues
            
    except KeyboardInterrupt:
        print("\n⏹️  Test execution interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n💥 Test runner error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()