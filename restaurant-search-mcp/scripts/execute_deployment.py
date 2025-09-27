#!/usr/bin/env python3
"""
Execute AgentCore Runtime Deployment for Restaurant Search MCP

This script executes the actual deployment of the Restaurant Search MCP server
to Amazon Bedrock AgentCore Runtime. It handles the complete deployment workflow
including configuration, launch, monitoring, and validation.

Requirements: 5.1, 5.2, 5.3, 8.1, 8.2, 8.3
"""

import json
import os
import sys
import time
from typing import Dict, Any

from deploy_agentcore import AgentCoreDeployment


def validate_prerequisites() -> bool:
    """Validate that all prerequisites are met for deployment.
    
    Returns:
        True if all prerequisites are met, False otherwise.
    """
    print("🔍 Validating deployment prerequisites...")
    
    # Check required files
    required_files = [
        'restaurant_mcp_server.py',
        'requirements.txt',
        'cognito_config.json'
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print(f"✗ Missing required files: {missing_files}")
        print("Please ensure all files are present before deployment:")
        for file_path in missing_files:
            if file_path == 'cognito_config.json':
                print(f"  - Run: python setup_cognito.py")
            else:
                print(f"  - Create: {file_path}")
        return False
    
    # Check AWS credentials
    try:
        import boto3
        session = boto3.Session()
        credentials = session.get_credentials()
        if not credentials:
            print("✗ AWS credentials not configured")
            print("Please run: aws configure")
            return False
        print("✓ AWS credentials configured")
    except Exception as e:
        print(f"✗ Error checking AWS credentials: {e}")
        return False
    
    # Check required Python packages
    try:
        import bedrock_agentcore_starter_toolkit
        import mcp
        print("✓ Required Python packages available")
    except ImportError as e:
        print(f"✗ Missing required Python package: {e}")
        print("Please run: pip install -r requirements.txt")
        return False
    
    print("✓ All prerequisites validated")
    return True


def execute_cognito_setup_if_needed() -> bool:
    """Execute Cognito setup if configuration doesn't exist.
    
    Returns:
        True if Cognito is configured, False otherwise.
    """
    if os.path.exists('cognito_config.json'):
        print("✓ Cognito configuration already exists")
        return True
    
    print("⚠️ Cognito configuration not found, running setup...")
    
    try:
        from setup_cognito import CognitoSetup
        
        cognito_setup = CognitoSetup()
        config = cognito_setup.setup_complete_cognito()
        
        if config:
            print("✓ Cognito setup completed successfully")
            return True
        else:
            print("✗ Cognito setup failed")
            return False
            
    except Exception as e:
        print(f"✗ Error during Cognito setup: {e}")
        return False


def main():
    """Main execution function for deployment."""
    print("🚀 Starting Restaurant Search MCP Deployment to AgentCore Runtime")
    print("=" * 70)
    
    try:
        # Step 1: Validate prerequisites
        print("\n📋 Step 1: Validating Prerequisites")
        if not validate_prerequisites():
            print("💥 Prerequisites validation failed")
            return 1
        
        # Step 2: Ensure Cognito is set up
        print("\n🔐 Step 2: Ensuring Cognito Authentication Setup")
        if not execute_cognito_setup_if_needed():
            print("💥 Cognito setup failed")
            return 1
        
        # Step 3: Initialize deployment
        print("\n🏗️ Step 3: Initializing AgentCore Deployment")
        deployment = AgentCoreDeployment()
        
        # Step 4: Execute complete deployment workflow
        print("\n🚀 Step 4: Executing Deployment Workflow")
        result = deployment.deploy_complete_workflow()
        
        # Step 5: Display results
        print("\n📊 Step 5: Deployment Results")
        print("=" * 50)
        
        if result['deployment_successful']:
            print("🎉 DEPLOYMENT SUCCESSFUL!")
            print("\n✅ Summary:")
            print("  - MCP server deployed to AgentCore Runtime")
            print("  - JWT authentication configured with Cognito")
            print("  - Connectivity test passed")
            print("  - Ready to serve MCP tool requests")
            
            # Display endpoint information if available
            if 'endpoint' in result.get('final_status', {}):
                endpoint_info = result['final_status']['endpoint']
                print(f"\n🔗 Endpoint Information:")
                print(f"  - Status: {endpoint_info.get('status', 'UNKNOWN')}")
                if 'url' in endpoint_info:
                    print(f"  - URL: {endpoint_info['url']}")
                if 'arn' in endpoint_info:
                    print(f"  - ARN: {endpoint_info['arn']}")
            
            # Display configuration files
            print(f"\n📁 Configuration Files:")
            print(f"  - Cognito Config: cognito_config.json")
            print(f"  - Deployment Config: agentcore_deployment_config.json")
            
            print(f"\n🧪 Next Steps:")
            print(f"  - Test the deployment using: python tests/test_remote_client.py")
            print(f"  - Monitor deployment status: python deploy_agentcore.py --status-only")
            
        else:
            print("❌ DEPLOYMENT FAILED")
            print("\n❗ Issues:")
            
            # Check specific failure points
            final_status = result.get('final_status', {})
            if 'endpoint' in final_status:
                endpoint_status = final_status['endpoint'].get('status', 'UNKNOWN')
                if endpoint_status in ['CREATE_FAILED', 'UPDATE_FAILED']:
                    print(f"  - Deployment status: {endpoint_status}")
            
            if not result.get('connectivity_test', False):
                print("  - Connectivity test failed")
            
            print(f"\n🔧 Troubleshooting:")
            print(f"  - Check AWS credentials and permissions")
            print(f"  - Verify Cognito configuration")
            print(f"  - Check deployment logs in AWS console")
            print(f"  - Run: python deploy_agentcore.py --status-only")
        
        # Save execution summary
        execution_summary = {
            'execution_time': time.time(),
            'deployment_successful': result['deployment_successful'],
            'result': result
        }
        
        with open('deployment_execution_summary.json', 'w') as f:
            json.dump(execution_summary, f, indent=2, default=str)
        
        print(f"\n📄 Execution summary saved to: deployment_execution_summary.json")
        
        return 0 if result['deployment_successful'] else 1
        
    except KeyboardInterrupt:
        print("\n⏹️ Deployment interrupted by user")
        return 1
    except Exception as e:
        print(f"\n💥 Deployment execution failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())