#!/usr/bin/env python3
"""
Comprehensive Test Runner for Restaurant Reasoning MCP Server.

This script runs all comprehensive tests including integration tests and deployment
validation tests, providing a summary of test results and coverage.
"""

import subprocess
import sys
import time
from pathlib import Path
import json


def run_test_suite(test_file: str, description: str) -> dict:
    """Run a test suite and return results."""
    print(f"\n{'='*60}")
    print(f"Running {description}")
    print(f"{'='*60}")
    
    start_time = time.time()
    
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", test_file, "-v", "--tb=short"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        
        execution_time = time.time() - start_time
        
        # Parse test results from stdout
        test_stats = {}
        if result.stdout:
            lines = result.stdout.split('\n')
            for line in lines:
                if 'passed' in line and ('failed' in line or 'skipped' in line):
                    # Look for summary line like "15 passed in 0.44s"
                    import re
                    match = re.search(r'(\d+)\s+passed', line)
                    if match:
                        test_stats['passed'] = int(match.group(1))
                    match = re.search(r'(\d+)\s+failed', line)
                    if match:
                        test_stats['failed'] = int(match.group(1))
                    match = re.search(r'(\d+)\s+skipped', line)
                    if match:
                        test_stats['skipped'] = int(match.group(1))
        
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "execution_time": execution_time,
            "stats": test_stats
        }
        
    except Exception as e:
        return {
            "success": False,
            "stdout": "",
            "stderr": str(e),
            "execution_time": time.time() - start_time,
            "stats": {}
        }


def main():
    """Run comprehensive test suite."""
    print("Restaurant Reasoning MCP Server - Comprehensive Test Suite")
    print("=" * 60)
    
    # Test suites to run
    test_suites = [
        {
            "file": "tests/test_reasoning_integration.py",
            "description": "End-to-End Integration Tests",
            "critical": True
        },
        {
            "file": "tests/test_reasoning_deployment.py", 
            "description": "Deployment Validation Tests",
            "critical": False  # May skip if deployment not available
        }
    ]
    
    results = {}
    total_passed = 0
    total_failed = 0
    total_skipped = 0
    total_execution_time = 0
    
    # Run each test suite
    for suite in test_suites:
        result = run_test_suite(suite["file"], suite["description"])
        results[suite["description"]] = result
        
        # Print immediate results
        if result["success"]:
            print(f"✅ {suite['description']} - PASSED")
        else:
            print(f"❌ {suite['description']} - FAILED")
            if suite["critical"]:
                print("   ⚠️  This is a critical test suite!")
        
        # Print test statistics if available
        if result["stats"]:
            stats = result["stats"]
            print(f"   Tests: {stats.get('passed', 0)} passed, {stats.get('failed', 0)} failed, {stats.get('skipped', 0)} skipped")
            total_passed += stats.get('passed', 0)
            total_failed += stats.get('failed', 0)
            total_skipped += stats.get('skipped', 0)
        
        print(f"   Execution time: {result['execution_time']:.2f}s")
        total_execution_time += result['execution_time']
        
        # Print errors if any
        if not result["success"] and result["stderr"]:
            print(f"   Error: {result['stderr'][:200]}...")
    
    # Print summary
    print(f"\n{'='*60}")
    print("COMPREHENSIVE TEST SUMMARY")
    print(f"{'='*60}")
    
    successful_suites = sum(1 for r in results.values() if r["success"])
    total_suites = len(results)
    
    print(f"Test Suites: {successful_suites}/{total_suites} passed")
    print(f"Individual Tests: {total_passed} passed, {total_failed} failed, {total_skipped} skipped")
    print(f"Total Execution Time: {total_execution_time:.2f}s")
    
    # Determine overall result
    critical_failures = []
    for suite in test_suites:
        if suite["critical"] and not results[suite["description"]]["success"]:
            critical_failures.append(suite["description"])
    
    if critical_failures:
        print(f"\n❌ CRITICAL TEST FAILURES:")
        for failure in critical_failures:
            print(f"   - {failure}")
        print("\n⚠️  Please fix critical test failures before deployment!")
        return 1
    elif total_failed > 0:
        print(f"\n⚠️  Some tests failed, but no critical failures detected.")
        print("   Review failed tests and consider fixing before deployment.")
        return 1
    else:
        print(f"\n✅ ALL TESTS PASSED!")
        print("   System is ready for deployment.")
        return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)