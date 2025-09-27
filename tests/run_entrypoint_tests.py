#!/usr/bin/env python3
"""
Test runner for entrypoint integration tests.

This script runs comprehensive tests for the BedrockAgentCoreApp entrypoint
including payload processing, Strands Agent integration, and error handling.
"""

import sys
import os
import json
import subprocess
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def run_tests():
    """Run entrypoint integration tests and generate report."""
    
    print("=" * 60)
    print("ENTRYPOINT INTEGRATION TESTS")
    print("=" * 60)
    print(f"Test started at: {datetime.now().isoformat()}")
    print()
    
    # Test configuration
    test_file = "tests/test_entrypoint_integration.py"
    results_file = "tests/results/entrypoint_test_results.json"
    
    # Ensure results directory exists
    os.makedirs("tests/results", exist_ok=True)
    
    test_results = {
        "test_suite": "entrypoint_integration",
        "timestamp": datetime.now().isoformat(),
        "tests": []
    }
    
    try:
        # Run pytest with verbose output and JSON report
        cmd = [
            sys.executable, "-m", "pytest", 
            test_file,
            "-v",
            "--tb=short",
            "--json-report",
            f"--json-report-file={results_file}"
        ]
        
        print("Running entrypoint integration tests...")
        print(f"Command: {' '.join(cmd)}")
        print()
        
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=project_root)
        
        print("STDOUT:")
        print(result.stdout)
        print()
        
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
            print()
        
        # Parse results
        if os.path.exists(results_file):
            with open(results_file, 'r') as f:
                pytest_results = json.load(f)
            
            test_results.update({
                "total_tests": pytest_results.get("summary", {}).get("total", 0),
                "passed": pytest_results.get("summary", {}).get("passed", 0),
                "failed": pytest_results.get("summary", {}).get("failed", 0),
                "errors": pytest_results.get("summary", {}).get("error", 0),
                "skipped": pytest_results.get("summary", {}).get("skipped", 0),
                "duration": pytest_results.get("duration", 0),
                "exit_code": result.returncode
            })
            
            # Extract individual test results
            for test in pytest_results.get("tests", []):
                test_results["tests"].append({
                    "name": test.get("nodeid", ""),
                    "outcome": test.get("outcome", ""),
                    "duration": test.get("duration", 0),
                    "error": test.get("call", {}).get("longrepr", "") if test.get("outcome") == "failed" else None
                })
        
        else:
            test_results.update({
                "total_tests": 0,
                "passed": 0,
                "failed": 1,
                "errors": 1,
                "exit_code": result.returncode,
                "error": "Could not generate test report"
            })
        
        # Print summary
        print("=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {test_results.get('total_tests', 0)}")
        print(f"Passed: {test_results.get('passed', 0)}")
        print(f"Failed: {test_results.get('failed', 0)}")
        print(f"Errors: {test_results.get('errors', 0)}")
        print(f"Skipped: {test_results.get('skipped', 0)}")
        print(f"Duration: {test_results.get('duration', 0):.2f}s")
        print(f"Exit Code: {test_results.get('exit_code', -1)}")
        print()
        
        # Show failed tests
        failed_tests = [t for t in test_results.get("tests", []) if t["outcome"] == "failed"]
        if failed_tests:
            print("FAILED TESTS:")
            for test in failed_tests:
                print(f"  - {test['name']}")
                if test.get("error"):
                    print(f"    Error: {test['error'][:200]}...")
            print()
        
        # Save detailed results
        with open(results_file, 'w') as f:
            json.dump(test_results, f, indent=2)
        
        print(f"Detailed results saved to: {results_file}")
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"Error running tests: {e}")
        test_results.update({
            "error": str(e),
            "exit_code": -1
        })
        
        with open(results_file, 'w') as f:
            json.dump(test_results, f, indent=2)
        
        return False


def test_payload_formats():
    """Test various payload formats manually."""
    
    print("=" * 60)
    print("MANUAL PAYLOAD FORMAT TESTS")
    print("=" * 60)
    
    try:
        from main import extract_user_prompt, format_response
        
        test_payloads = [
            {
                "name": "Standard AgentCore format",
                "payload": {"input": {"prompt": "Find restaurants in Central district"}}
            },
            {
                "name": "Message format",
                "payload": {"input": {"message": "Show me breakfast places"}}
            },
            {
                "name": "Direct input string",
                "payload": {"input": "Find dinner restaurants"}
            },
            {
                "name": "Top-level prompt",
                "payload": {"prompt": "Search for lunch places"}
            },
            {
                "name": "Alternative field",
                "payload": {"query": "Find good restaurants"}
            }
        ]
        
        for test in test_payloads:
            try:
                prompt = extract_user_prompt(test["payload"])
                print(f"✓ {test['name']}: '{prompt}'")
            except Exception as e:
                print(f"✗ {test['name']}: {e}")
        
        print()
        
        # Test response formatting
        print("Testing response formatting...")
        
        test_response = "I found 3 restaurants in Central district."
        formatted = format_response(test_response, success=True)
        
        # Validate JSON
        import json
        response_data = json.loads(formatted)
        print(f"✓ Response formatting: JSON valid, success={response_data['success']}")
        
        return True
        
    except Exception as e:
        print(f"✗ Manual tests failed: {e}")
        return False


if __name__ == "__main__":
    print("Starting entrypoint integration test suite...")
    print()
    
    # Run manual payload tests first
    manual_success = test_payload_formats()
    
    # Run automated tests
    auto_success = run_tests()
    
    print("=" * 60)
    print("FINAL RESULTS")
    print("=" * 60)
    print(f"Manual Tests: {'PASSED' if manual_success else 'FAILED'}")
    print(f"Automated Tests: {'PASSED' if auto_success else 'FAILED'}")
    print(f"Overall: {'PASSED' if manual_success and auto_success else 'FAILED'}")
    
    sys.exit(0 if manual_success and auto_success else 1)