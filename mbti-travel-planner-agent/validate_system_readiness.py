#!/usr/bin/env python3
"""
System Readiness Validation Script

This script validates that all components are properly configured and available
before running the comprehensive three-day workflow test.
"""

import os
import sys
import json
import logging
from typing import Dict, Any

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def check_environment_variables() -> Dict[str, Any]:
    """Check required environment variables."""
    logger.info("Checking environment variables...")
    
    required_vars = [
        'AWS_REGION',
        'ENVIRONMENT'
    ]
    
    optional_vars = [
        'AWS_ACCESS_KEY_ID',
        'AWS_SECRET_ACCESS_KEY',
        'AWS_SESSION_TOKEN'
    ]
    
    env_status = {
        'required_vars_present': True,
        'missing_required': [],
        'optional_vars_present': [],
        'missing_optional': []
    }
    
    # Check required variables
    for var in required_vars:
        if os.getenv(var):
            logger.info(f"✅ {var}: Present")
        else:
            logger.warning(f"❌ {var}: Missing")
            env_status['required_vars_present'] = False
            env_status['missing_required'].append(var)
    
    # Check optional variables
    for var in optional_vars:
        if os.getenv(var):
            env_status['optional_vars_present'].append(var)
            logger.info(f"✅ {var}: Present")
        else:
            env_status['missing_optional'].append(var)
            logger.info(f"ℹ️ {var}: Not set (optional)")
    
    return env_status

def check_configuration_files() -> Dict[str, Any]:
    """Check for required configuration files."""
    logger.info("Checking configuration files...")
    
    config_files = [
        'config/cognito_config.json',
        'config/agentcore_config.py',
        '.bedrock_agentcore.yaml'
    ]
    
    config_status = {
        'all_files_present': True,
        'present_files': [],
        'missing_files': []
    }
    
    for config_file in config_files:
        if os.path.exists(config_file):
            config_status['present_files'].append(config_file)
            logger.info(f"✅ {config_file}: Present")
        else:
            config_status['missing_files'].append(config_file)
            config_status['all_files_present'] = False
            logger.warning(f"❌ {config_file}: Missing")
    
    return config_status

def check_python_dependencies() -> Dict[str, Any]:
    """Check for required Python dependencies."""
    logger.info("Checking Python dependencies...")
    
    required_packages = [
        'boto3',
        'aiohttp',
        'asyncio',
        'json',
        'logging',
        'uuid',
        'datetime'
    ]
    
    optional_packages = [
        'pytest',
        'pytest-asyncio'
    ]
    
    dep_status = {
        'all_required_present': True,
        'present_packages': [],
        'missing_packages': [],
        'optional_present': []
    }
    
    # Check required packages
    for package in required_packages:
        try:
            __import__(package)
            dep_status['present_packages'].append(package)
            logger.info(f"✅ {package}: Available")
        except ImportError:
            dep_status['missing_packages'].append(package)
            dep_status['all_required_present'] = False
            logger.warning(f"❌ {package}: Missing")
    
    # Check optional packages
    for package in optional_packages:
        try:
            __import__(package)
            dep_status['optional_present'].append(package)
            logger.info(f"✅ {package}: Available (optional)")
        except ImportError:
            logger.info(f"ℹ️ {package}: Not available (optional)")
    
    return dep_status

def check_agentcore_configuration() -> Dict[str, Any]:
    """Check AgentCore configuration."""
    logger.info("Checking AgentCore configuration...")
    
    agentcore_status = {
        'config_loadable': False,
        'restaurant_search_arn_configured': False,
        'restaurant_reasoning_arn_configured': False,
        'cognito_config_valid': False
    }
    
    try:
        from config.agentcore_environment_config import get_agentcore_config
        
        config = get_agentcore_config('production')
        agentcore_status['config_loadable'] = True
        logger.info("✅ AgentCore config: Loadable")
        
        # Check for agent ARNs
        if hasattr(config, 'agentcore'):
            if hasattr(config.agentcore, 'restaurant_search_agent_arn'):
                agentcore_status['restaurant_search_arn_configured'] = True
                logger.info("✅ Restaurant search agent ARN: Configured")
            else:
                logger.warning("❌ Restaurant search agent ARN: Not configured")
            
            if hasattr(config.agentcore, 'restaurant_reasoning_agent_arn'):
                agentcore_status['restaurant_reasoning_arn_configured'] = True
                logger.info("✅ Restaurant reasoning agent ARN: Configured")
            else:
                logger.warning("❌ Restaurant reasoning agent ARN: Not configured")
        
    except Exception as e:
        logger.error(f"❌ AgentCore config error: {e}")
    
    # Check Cognito configuration
    try:
        cognito_config_path = 'config/cognito_config.json'
        if os.path.exists(cognito_config_path):
            with open(cognito_config_path, 'r') as f:
                cognito_config = json.load(f)
                
            required_cognito_fields = ['user_pool_id', 'client_id', 'client_secret', 'region']
            if all(field in cognito_config for field in required_cognito_fields):
                agentcore_status['cognito_config_valid'] = True
                logger.info("✅ Cognito config: Valid")
            else:
                logger.warning("❌ Cognito config: Missing required fields")
        else:
            logger.warning("❌ Cognito config: File not found")
            
    except Exception as e:
        logger.error(f"❌ Cognito config error: {e}")
    
    return agentcore_status

def check_main_components() -> Dict[str, Any]:
    """Check if main components can be imported."""
    logger.info("Checking main components...")
    
    component_status = {
        'main_importable': False,
        'agentcore_client_available': False,
        'auth_manager_available': False,
        'services_importable': False
    }
    
    try:
        # Try to import main components
        from main import (
            app, 
            agentcore_client, 
            auth_manager, 
            AGENTCORE_AVAILABLE
        )
        
        component_status['main_importable'] = True
        component_status['agentcore_client_available'] = agentcore_client is not None
        component_status['auth_manager_available'] = auth_manager is not None
        
        logger.info("✅ Main components: Importable")
        logger.info(f"✅ AgentCore available: {AGENTCORE_AVAILABLE}")
        
    except ImportError as e:
        logger.warning(f"⚠️ Main components import issue: {e}")
    except Exception as e:
        logger.error(f"❌ Main components error: {e}")
    
    # Check service imports
    try:
        from services.agentcore_runtime_client import AgentCoreRuntimeClient
        from services.authentication_manager import AuthenticationManager
        from services.restaurant_search_tool import RestaurantSearchTool
        from services.restaurant_reasoning_tool import RestaurantReasoningTool
        
        component_status['services_importable'] = True
        logger.info("✅ Service components: Importable")
        
    except ImportError as e:
        logger.warning(f"⚠️ Service components import issue: {e}")
    except Exception as e:
        logger.error(f"❌ Service components error: {e}")
    
    return component_status

def generate_readiness_report(checks: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """Generate overall readiness report."""
    
    # Calculate overall readiness
    critical_checks = [
        checks['environment']['required_vars_present'],
        checks['dependencies']['all_required_present'],
        checks['components']['main_importable']
    ]
    
    important_checks = [
        checks['configuration']['all_files_present'],
        checks['agentcore']['config_loadable'],
        checks['agentcore']['cognito_config_valid']
    ]
    
    overall_ready = all(critical_checks) and any(important_checks)
    
    readiness_score = (
        sum(critical_checks) * 0.6 +  # Critical checks worth 60%
        sum(important_checks) * 0.4    # Important checks worth 40%
    ) / (len(critical_checks) + len(important_checks))
    
    report = {
        'overall_ready': overall_ready,
        'readiness_score': readiness_score,
        'critical_issues': [],
        'warnings': [],
        'recommendations': []
    }
    
    # Identify critical issues
    if not checks['environment']['required_vars_present']:
        report['critical_issues'].append("Required environment variables are missing")
    
    if not checks['dependencies']['all_required_present']:
        report['critical_issues'].append("Required Python dependencies are missing")
    
    if not checks['components']['main_importable']:
        report['critical_issues'].append("Main components cannot be imported")
    
    # Identify warnings
    if not checks['configuration']['all_files_present']:
        report['warnings'].append("Some configuration files are missing")
    
    if not checks['agentcore']['config_loadable']:
        report['warnings'].append("AgentCore configuration cannot be loaded")
    
    if not checks['agentcore']['cognito_config_valid']:
        report['warnings'].append("Cognito configuration is invalid or missing")
    
    # Generate recommendations
    if report['critical_issues']:
        report['recommendations'].append("Fix critical issues before running tests")
    
    if report['warnings']:
        report['recommendations'].append("Address configuration warnings for full functionality")
    
    if not report['critical_issues'] and not report['warnings']:
        report['recommendations'].append("System is ready for testing")
    
    return report

def main():
    """Main validation function."""
    print("MBTI Travel Planner Agent - System Readiness Validation")
    print("=" * 60)
    
    # Run all checks
    checks = {
        'environment': check_environment_variables(),
        'configuration': check_configuration_files(),
        'dependencies': check_python_dependencies(),
        'agentcore': check_agentcore_configuration(),
        'components': check_main_components()
    }
    
    # Generate readiness report
    report = generate_readiness_report(checks)
    
    # Print summary
    print("\n" + "=" * 60)
    print("SYSTEM READINESS SUMMARY")
    print("=" * 60)
    
    print(f"Overall Ready: {'✅ YES' if report['overall_ready'] else '❌ NO'}")
    print(f"Readiness Score: {report['readiness_score']:.1%}")
    
    if report['critical_issues']:
        print(f"\nCritical Issues:")
        for issue in report['critical_issues']:
            print(f"  ❌ {issue}")
    
    if report['warnings']:
        print(f"\nWarnings:")
        for warning in report['warnings']:
            print(f"  ⚠️ {warning}")
    
    if report['recommendations']:
        print(f"\nRecommendations:")
        for i, rec in enumerate(report['recommendations'], 1):
            print(f"  {i}. {rec}")
    
    # Save detailed report
    try:
        with open('system_readiness_report.json', 'w') as f:
            json.dump({
                'checks': checks,
                'report': report
            }, f, indent=2, default=str)
        print(f"\n📄 Detailed report saved to: system_readiness_report.json")
    except Exception as e:
        logger.error(f"Failed to save report: {e}")
    
    # Return appropriate exit code
    return 0 if report['overall_ready'] else 1

if __name__ == "__main__":
    sys.exit(main())