#!/usr/bin/env python3
"""
MBTI Test Runner
Runs the MBTI personality type tests for the travel assistant.
"""

import sys
import os
import argparse
from pathlib import Path

# Add the parent directory to the path so we can import from services
sys.path.append(str(Path(__file__).parent.parent))

from test_single_mbti_type import SingleMBTITester
from test_mbti_prompts_comprehensive import MBTIPromptsFilteredTester

def run_single_mbti_test(mbti_type: str):
    """Run test for a single MBTI type."""
    print(f"🚀 Running single MBTI test for {mbti_type}")
    tester = SingleMBTITester(mbti_type=mbti_type)
    results = tester.run_test()
    return results

def run_comprehensive_test():
    """Run comprehensive test for all MBTI types."""
    print("🚀 Running comprehensive MBTI test for all types")
    tester = MBTIPromptsFilteredTester()
    results = tester.run_comprehensive_test()
    return results

def main():
    parser = argparse.ArgumentParser(description='Run MBTI personality type tests')
    parser.add_argument('--type', '-t', type=str, help='Specific MBTI type to test (e.g., ENTJ, INFJ)')
    parser.add_argument('--comprehensive', '-c', action='store_true', help='Run comprehensive test for all MBTI types')
    parser.add_argument('--list-types', '-l', action='store_true', help='List available MBTI types')
    
    args = parser.parse_args()
    
    if args.list_types:
        # List available MBTI types
        tester = SingleMBTITester()
        available_types = tester.prompt_loader.list_available_types()
        print("Available MBTI types:")
        for mbti_type in available_types:
            info = tester.prompt_loader.get_personality_info(mbti_type)
            print(f"  {mbti_type}: {info['description']}")
        return
    
    if args.comprehensive:
        results = run_comprehensive_test()
        print(f"\n✅ Comprehensive test completed!")
        print(f"Tested {len(results['all_results'])} MBTI types")
        return
    
    if args.type:
        mbti_type = args.type.upper()
        results = run_single_mbti_test(mbti_type)
        print(f"\n✅ {mbti_type} test completed!")
        print(f"Found {results['total_documents']} documents in {results['execution_time']} seconds")
        return
    
    # Default: run ENTJ test
    print("No specific test specified. Running default ENTJ test.")
    print("Use --help to see all options.")
    results = run_single_mbti_test("ENTJ")
    print(f"\n✅ Default ENTJ test completed!")
    print(f"Found {results['total_documents']} documents in {results['execution_time']} seconds")

if __name__ == "__main__":
    main()