#!/usr/bin/env python3
"""
Simple execution script for the Three-Day Workflow Comprehensive Test

This script provides an easy way to run the comprehensive three-day workflow test
with proper environment setup and error handling.
"""

import asyncio
import os
import sys
import logging
from datetime import datetime

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f'three_day_workflow_test_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)

logger = logging.getLogger(__name__)

def setup_environment():
    """Setup environment variables for testing."""
    # Set default environment if not specified
    if not os.getenv('ENVIRONMENT'):
        os.environ['ENVIRONMENT'] = 'production'
    
    # Set AWS region if not specified
    if not os.getenv('AWS_REGION'):
        os.environ['AWS_REGION'] = 'us-east-1'
    
    # Set default session configuration
    if not os.getenv('SESSION_ID'):
        os.environ['SESSION_ID'] = f'test_session_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
    
    logger.info(f"Environment setup complete:")
    logger.info(f"  ENVIRONMENT: {os.getenv('ENVIRONMENT')}")
    logger.info(f"  AWS_REGION: {os.getenv('AWS_REGION')}")
    logger.info(f"  SESSION_ID: {os.getenv('SESSION_ID')}")

async def run_test():
    """Run the comprehensive three-day workflow test."""
    try:
        # Import the test suite
        from test_three_day_workflow_comprehensive import ThreeDayWorkflowTest
        
        logger.info("Starting Three-Day Workflow Comprehensive Test...")
        
        # Initialize test suite
        test_suite = ThreeDayWorkflowTest()
        
        # Run the comprehensive test
        test_report = await test_suite.run_comprehensive_test()
        
        # Print results summary
        print_test_summary(test_report)
        
        # Save report
        save_test_report(test_report)
        
        # Return success/failure based on results
        summary = test_report.get('test_summary', {})
        success_rate = summary.get('overall_success_rate', 0)
        
        if success_rate >= 0.8:
            logger.info(f"✅ Test suite PASSED with {success_rate:.1%} success rate")
            return 0
        else:
            logger.warning(f"⚠️ Test suite PARTIAL SUCCESS with {success_rate:.1%} success rate")
            return 1
            
    except ImportError as e:
        logger.error(f"❌ Failed to import test suite: {e}")
        logger.error("Make sure all dependencies are installed and the test file exists")
        return 1
    except Exception as e:
        logger.error(f"❌ Test execution failed: {e}")
        return 1

def print_test_summary(test_report):
    """Print a formatted test summary."""
    print("\n" + "=" * 80)
    print("THREE-DAY WORKFLOW TEST SUMMARY")
    print("=" * 80)
    
    summary = test_report.get('test_summary', {})
    findings = test_report.get('key_findings', {})
    recommendations = test_report.get('recommendations', [])
    
    # Basic info
    print(f"Session ID: {summary.get('test_session_id', 'N/A')}")
    print(f"Environment: {summary.get('environment', 'N/A')}")
    print(f"MBTI Type: {summary.get('mbti_type_tested', 'N/A')}")
    print(f"Districts: {', '.join(summary.get('districts_tested', []))}")
    print(f"Execution Time: {summary.get('total_execution_time_seconds', 0):.2f} seconds")
    
    # Test results
    print(f"\nTest Results:")
    print(f"  Total Tests: {summary.get('total_tests', 0)}")
    print(f"  Passed: {summary.get('successful_tests', 0)}")
    print(f"  Failed: {summary.get('failed_tests', 0)}")
    print(f"  Success Rate: {summary.get('overall_success_rate', 0):.1%}")
    
    # Key findings
    print(f"\nKey Findings:")
    for finding, status in findings.items():
        status_icon = "✅" if status else "❌"
        finding_name = finding.replace('_', ' ').title()
        print(f"  {status_icon} {finding_name}")
    
    # Recommendations
    if recommendations:
        print(f"\nRecommendations:")
        for i, rec in enumerate(recommendations, 1):
            print(f"  {i}. {rec}")

def save_test_report(test_report):
    """Save the test report to a file."""
    try:
        import json
        
        summary = test_report.get('test_summary', {})
        session_id = summary.get('test_session_id', 'unknown')
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        filename = f"three_day_workflow_report_{session_id}_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(test_report, f, indent=2, default=str)
        
        print(f"\n📄 Detailed report saved to: {filename}")
        
    except Exception as e:
        logger.error(f"Failed to save test report: {e}")

def main():
    """Main execution function."""
    print("MBTI Travel Planner Agent - Three-Day Workflow Test")
    print("=" * 60)
    
    # Setup environment
    setup_environment()
    
    # Run the test
    try:
        exit_code = asyncio.run(run_test())
        
        if exit_code == 0:
            print("\n🎉 All tests completed successfully!")
        else:
            print("\n⚠️ Some tests failed or had issues. Check the logs for details.")
        
        return exit_code
        
    except KeyboardInterrupt:
        print("\n⏹️ Test execution interrupted by user")
        return 130
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())