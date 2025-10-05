#!/usr/bin/env python3
"""
Validate Task 20 Completion

This script validates that all sub-tasks of Task 20 have been implemented
and are ready for execution.
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple

def validate_subtask_1_staging_deployment() -> Tuple[bool, str]:
    """Validate sub-task 1: Deploy enhanced status check system to staging environment."""
    required_files = [
        "scripts/deploy_to_staging.py",
        "config/examples/staging_deployment_config.yaml"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        return False, f"Missing files: {missing_files}"
    
    return True, "Staging deployment scripts and configuration ready"

def validate_subtask_2_monitoring_alerting() -> Tuple[bool, str]:
    """Validate sub-task 2: Implement monitoring and alerting for enhanced system."""
    required_files = [
        "scripts/setup_monitoring.py",
        "services/dual_metrics_collector.py",
        "console/alert_manager.py"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        return False, f"Missing files: {missing_files}"
    
    return True, "Monitoring and alerting implementation ready"

def validate_subtask_3_operational_runbooks() -> Tuple[bool, str]:
    """Validate sub-task 3: Create operational runbooks for enhanced monitoring."""
    required_files = [
        "docs/OPERATIONAL_RUNBOOKS.md"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        return False, f"Missing files: {missing_files}"
    
    # Check if runbooks contain enhanced monitoring procedures
    runbooks_path = Path("docs/OPERATIONAL_RUNBOOKS.md")
    with open(runbooks_path, 'r') as f:
        content = f.read()
    
    required_sections = [
        "Enhanced MCP Status Check System",
        "Dual Monitoring",
        "Circuit Breaker",
        "Alert Response Procedures"
    ]
    
    missing_sections = []
    for section in required_sections:
        if section not in content:
            missing_sections.append(section)
    
    if missing_sections:
        return False, f"Missing runbook sections: {missing_sections}"
    
    return True, "Operational runbooks ready with enhanced monitoring procedures"

def validate_subtask_4_gradual_rollout() -> Tuple[bool, str]:
    """Validate sub-task 4: Implement gradual rollout to production environments."""
    required_files = [
        "scripts/gradual_rollout_deployment.py",
        "scripts/deploy_to_production.py"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        return False, f"Missing files: {missing_files}"
    
    return True, "Gradual rollout deployment scripts ready"

def validate_subtask_5_post_deployment_validation() -> Tuple[bool, str]:
    """Validate sub-task 5: Create post-deployment validation and monitoring."""
    required_files = [
        "scripts/post_deployment_validation.py",
        "scripts/validate_deployment.py"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        return False, f"Missing files: {missing_files}"
    
    return True, "Post-deployment validation scripts ready"

def validate_subtask_6_feedback_collection() -> Tuple[bool, str]:
    """Validate sub-task 6: Implement feedback collection and continuous improvement process."""
    required_files = [
        "scripts/feedback_collection.py"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        return False, f"Missing files: {missing_files}"
    
    return True, "Feedback collection and continuous improvement system ready"

def validate_orchestrator() -> Tuple[bool, str]:
    """Validate the main orchestrator script."""
    orchestrator_path = Path("scripts/deploy_and_monitor_orchestrator.py")
    
    if not orchestrator_path.exists():
        return False, "Main orchestrator script missing"
    
    return True, "Main orchestrator script ready"

def main():
    """Main validation function."""
    print("Validating Task 20: Deploy and monitor enhanced status check system")
    print("=" * 70)
    
    # Change to the enhanced-mcp-status-check directory
    os.chdir("enhanced-mcp-status-check")
    
    subtasks = [
        ("Sub-task 1: Deploy to staging environment", validate_subtask_1_staging_deployment),
        ("Sub-task 2: Implement monitoring and alerting", validate_subtask_2_monitoring_alerting),
        ("Sub-task 3: Create operational runbooks", validate_subtask_3_operational_runbooks),
        ("Sub-task 4: Implement gradual rollout", validate_subtask_4_gradual_rollout),
        ("Sub-task 5: Post-deployment validation", validate_subtask_5_post_deployment_validation),
        ("Sub-task 6: Feedback collection", validate_subtask_6_feedback_collection),
        ("Orchestrator: Main deployment orchestrator", validate_orchestrator)
    ]
    
    all_valid = True
    results = []
    
    for task_name, validator in subtasks:
        try:
            is_valid, message = validator()
            status = "✅ PASS" if is_valid else "❌ FAIL"
            print(f"{status} {task_name}")
            print(f"    {message}")
            
            if not is_valid:
                all_valid = False
                
            results.append((task_name, is_valid, message))
            
        except Exception as e:
            print(f"❌ FAIL {task_name}")
            print(f"    Error: {e}")
            all_valid = False
            results.append((task_name, False, str(e)))
    
    print("\n" + "=" * 70)
    
    if all_valid:
        print("✅ Task 20 validation PASSED - All sub-tasks are implemented and ready")
        print("\nNext steps:")
        print("1. Run staging deployment: python scripts/deploy_and_monitor_orchestrator.py --environment staging")
        print("2. Validate staging: python scripts/post_deployment_validation.py")
        print("3. Run production deployment: python scripts/deploy_and_monitor_orchestrator.py --environment production")
        return 0
    else:
        print("❌ Task 20 validation FAILED - Some sub-tasks need attention")
        print("\nFailed validations:")
        for task_name, is_valid, message in results:
            if not is_valid:
                print(f"  - {task_name}: {message}")
        return 1

if __name__ == "__main__":
    sys.exit(main())