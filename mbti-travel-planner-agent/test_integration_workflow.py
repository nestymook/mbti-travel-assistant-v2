"""
Simple Integration Test Execution Script

This script provides a simple way to run the complete workflow integration tests
for task 12 verification.
"""

import sys
import subprocess
from pathlib import Path

def run_integration_tests():
    """Run the integration tests for complete workflow."""
    
    print("🚀 Running Complete Workflow Integration Tests")
    print("=" * 60)
    
    # Get the project root directory
    project_root = Path(__file__).parent
    
    # Test files to run
    test_files = [
        "tests/test_complete_workflow_integration.py",
        "tests/test_nova_pro_integration.py", 
        "tests/test_workflow_error_scenarios.py"
    ]
    
    all_passed = True
    
    for test_file in test_files:
        test_path = project_root / test_file
        
        if not test_path.exists():
            print(f"⚠️  Test file not found: {test_file}")
            continue
            
        print(f"\n📋 Running: {test_file}")
        print("-" * 40)
        
        try:
            # Run pytest with basic options
            result = subprocess.run([
                sys.executable, "-m", "pytest",
                str(test_path),
                "-v",
                "--tb=short"
            ], cwd=project_root)
            
            if result.returncode == 0:
                print(f"✅ {test_file} - PASSED")
            else:
                print(f"❌ {test_file} - FAILED")
                all_passed = False
                
        except Exception as e:
            print(f"💥 Error running {test_file}: {e}")
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 All integration tests PASSED!")
        print("Task 12 - Complete workflow integration tests are working correctly.")
    else:
        print("⚠️  Some integration tests FAILED!")
        print("Please check the output above for details.")
    print("=" * 60)
    
    return all_passed

if __name__ == "__main__":
    success = run_integration_tests()
    sys.exit(0 if success else 1)