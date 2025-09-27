#!/usr/bin/env python3
"""
Complete Restaurant Search Conversational Agent Deployment

This script deploys the complete conversational restaurant search system
including both the MCP server and the foundation model agent to 
Amazon Bedrock AgentCore Runtime.

Requirements: 12.1, 12.2, 13.1, 13.2
"""

import json
import os
import sys
import time
import asyncio
from typing import Dict, Any, Optional

import boto3
from botocore.exceptions import ClientError


class CompleteSystemDeployment:
    """Deploy complete restaurant search conversational system."""
    
    def __init__(self, region: str = "us-east-1"):
        """Initialize complete system deployment.
        
        Args:
            region: AWS region for deployment.
        """
        self.region = region
        self.session = boto3.Session(region_name=region)
        self.deployment_status = {
            'mcp_server': {'deployed': False, 'arn': None, 'status': None},
            'conversational_agent': {'deployed': False, 'arn': None, 'status': None},
            'system_ready': False
        }
        
    def check_prerequisites(self) -> Dict[str, bool]:
        """Check if all prerequisites are met for deployment.
        
        Returns:
            Dictionary of prerequisite check results.
        """
        print("🔍 Checking deployment prerequisites...\n")
        
        checks = {
            'cognito_config': False,
            'mcp_server_code': False,
            'requirements_file': False,
            'district_config': False,
            'aws_credentials': False,
            'bedrock_access': False
        }
        
        # Check Cognito configuration
        if os.path.exists("cognito_config.json"):
            try:
                with open("cognito_config.json", 'r') as f:
                    config = json.load(f)
                if 'app_client' in config and 'discovery_url' in config:
                    checks['cognito_config'] = True
                    print("✅ Cognito configuration found")
                else:
                    print("❌ Cognito configuration incomplete")
            except Exception as e:
                print(f"❌ Error reading Cognito config: {e}")
        else:
            print("❌ Cognito configuration not found (run setup_cognito.py)")
        
        # Check MCP server code
        if os.path.exists("restaurant_mcp_server.py"):
            checks['mcp_server_code'] = True
            print("✅ MCP server code found")
        else:
            print("❌ MCP server code not found")
        
        # Check requirements file
        if os.path.exists("requirements.txt"):
            checks['requirements_file'] = True
            print("✅ Requirements file found")
        else:
            print("❌ Requirements file not found")
        
        # Check district configuration
        if os.path.exists("config/districts/master-config.json"):
            checks['district_config'] = True
            print("✅ District configuration found")
        else:
            print("❌ District configuration not found")
        
        # Check AWS credentials
        try:
            sts = self.session.client('sts')
            identity = sts.get_caller_identity()
            checks['aws_credentials'] = True
            print(f"✅ AWS credentials valid (Account: {identity['Account']})")
        except Exception as e:
            print(f"❌ AWS credentials invalid: {e}")
        
        # Check Bedrock access
        try:
            bedrock = self.session.client('bedrock', region_name=self.region)
            models = bedrock.list_foundation_models()
            checks['bedrock_access'] = True
            print("✅ Bedrock access confirmed")
        except Exception as e:
            print(f"❌ Bedrock access failed: {e}")
        
        print()
        return checks
    
    def deploy_mcp_server(self) -> Dict[str, Any]:
        """Deploy the MCP server component.
        
        Returns:
            MCP server deployment result.
        """
        print("🚀 Deploying MCP Server Component...\n")
        
        try:
            # Import and run MCP deployment
            from deploy_agentcore import AgentCoreDeployment
            
            mcp_deployment = AgentCoreDeployment(region=self.region)
            result = mcp_deployment.deploy_complete_workflow()
            
            if result['deployment_successful']:
                self.deployment_status['mcp_server']['deployed'] = True
                
                # Extract ARN from deployment result
                final_status = result.get('final_status', {})
                if 'endpoint' in final_status:
                    self.deployment_status['mcp_server']['arn'] = final_status['endpoint'].get('arn')
                    self.deployment_status['mcp_server']['status'] = final_status['endpoint'].get('status')
                
                print("✅ MCP Server deployment completed successfully")
            else:
                print("❌ MCP Server deployment failed")
            
            return result
            
        except Exception as e:
            print(f"❌ Error deploying MCP server: {e}")
            return {'deployment_successful': False, 'error': str(e)}
    
    def deploy_conversational_agent(self) -> Dict[str, Any]:
        """Deploy the conversational agent component.
        
        Returns:
            Conversational agent deployment result.
        """
        print("\n🤖 Deploying Conversational Agent Component...\n")
        
        try:
            # Import and run conversational agent deployment
            from deploy_conversational_agent import ConversationalAgentDeployment
            
            agent_deployment = ConversationalAgentDeployment(region=self.region)
            result = agent_deployment.deploy_complete_conversational_agent()
            
            if result['deployment_successful']:
                self.deployment_status['conversational_agent']['deployed'] = True
                
                # Extract ARN from deployment result
                final_status = result.get('final_status', {})
                if 'agent' in final_status:
                    self.deployment_status['conversational_agent']['arn'] = final_status['agent'].get('arn')
                    self.deployment_status['conversational_agent']['status'] = final_status['agent'].get('status')
                
                print("✅ Conversational Agent deployment completed successfully")
            else:
                print("❌ Conversational Agent deployment failed")
            
            return result
            
        except Exception as e:
            print(f"❌ Error deploying conversational agent: {e}")
            return {'deployment_successful': False, 'error': str(e)}
    
    def test_end_to_end_system(self) -> Dict[str, Any]:
        """Test the complete end-to-end system functionality.
        
        Returns:
            End-to-end test results.
        """
        print("\n🧪 Testing End-to-End System Functionality...\n")
        
        try:
            # Run conversational flow tests
            from tests.test_conversational_flow import ConversationalFlowTester
            
            tester = ConversationalFlowTester()
            results = tester.run_conversational_tests()
            
            # Run error handling tests
            error_results = tester.test_error_handling()
            
            # Combine results
            combined_results = {
                'conversational_tests': results,
                'error_handling_tests': error_results,
                'overall_success': results['passed_tests'] >= (results['total_tests'] * 0.8)
            }
            
            if combined_results['overall_success']:
                print("✅ End-to-end system tests passed")
            else:
                print("⚠️ Some end-to-end system tests failed")
            
            return combined_results
            
        except Exception as e:
            print(f"❌ Error running end-to-end tests: {e}")
            return {'overall_success': False, 'error': str(e)}
    
    def validate_system_integration(self) -> Dict[str, Any]:
        """Validate that MCP server and conversational agent are properly integrated.
        
        Returns:
            Integration validation results.
        """
        print("\n🔗 Validating System Integration...\n")
        
        validation_results = {
            'mcp_server_accessible': False,
            'agent_can_call_tools': False,
            'authentication_working': False,
            'natural_language_processing': False,
            'overall_integration': False
        }
        
        try:
            # Check if MCP server is accessible
            if (self.deployment_status['mcp_server']['deployed'] and 
                self.deployment_status['mcp_server']['status'] == 'READY'):
                validation_results['mcp_server_accessible'] = True
                print("✅ MCP server is accessible")
            else:
                print("❌ MCP server is not accessible")
            
            # Check if conversational agent is ready
            if (self.deployment_status['conversational_agent']['deployed'] and 
                self.deployment_status['conversational_agent']['status'] == 'READY'):
                validation_results['agent_can_call_tools'] = True
                print("✅ Conversational agent is ready")
            else:
                print("❌ Conversational agent is not ready")
            
            # Check authentication (if Cognito config exists)
            if os.path.exists("cognito_config.json"):
                validation_results['authentication_working'] = True
                print("✅ Authentication configuration is available")
            else:
                print("⚠️ Authentication configuration not found")
            
            # Test natural language processing
            try:
                from services.query_processor import QueryProcessor
                processor = QueryProcessor()
                intent = processor.extract_intent("Find restaurants in Central district")
                if intent.districts and intent.confidence > 0.5:
                    validation_results['natural_language_processing'] = True
                    print("✅ Natural language processing is working")
                else:
                    print("❌ Natural language processing failed")
            except Exception as e:
                print(f"❌ Natural language processing error: {e}")
            
            # Overall integration check
            validation_results['overall_integration'] = all([
                validation_results['mcp_server_accessible'],
                validation_results['agent_can_call_tools'],
                validation_results['natural_language_processing']
            ])
            
            if validation_results['overall_integration']:
                print("\n🎉 System integration validation passed!")
                self.deployment_status['system_ready'] = True
            else:
                print("\n⚠️ System integration validation failed")
            
            return validation_results
            
        except Exception as e:
            print(f"❌ Error validating system integration: {e}")
            validation_results['error'] = str(e)
            return validation_results
    
    def generate_deployment_summary(self) -> str:
        """Generate comprehensive deployment summary.
        
        Returns:
            Deployment summary as formatted string.
        """
        summary = "# Restaurant Search Conversational Agent - Deployment Summary\n\n"
        
        # System status
        summary += "## System Status\n\n"
        summary += f"**Overall System Ready:** {'✅ Yes' if self.deployment_status['system_ready'] else '❌ No'}\n\n"
        
        # MCP Server status
        mcp_status = self.deployment_status['mcp_server']
        summary += "### MCP Server\n"
        summary += f"- **Deployed:** {'✅ Yes' if mcp_status['deployed'] else '❌ No'}\n"
        summary += f"- **Status:** {mcp_status['status'] or 'Unknown'}\n"
        summary += f"- **ARN:** {mcp_status['arn'] or 'Not available'}\n\n"
        
        # Conversational Agent status
        agent_status = self.deployment_status['conversational_agent']
        summary += "### Conversational Agent\n"
        summary += f"- **Deployed:** {'✅ Yes' if agent_status['deployed'] else '❌ No'}\n"
        summary += f"- **Status:** {agent_status['status'] or 'Unknown'}\n"
        summary += f"- **ARN:** {agent_status['arn'] or 'Not available'}\n\n"
        
        # Usage instructions
        if self.deployment_status['system_ready']:
            summary += "## Usage Instructions\n\n"
            summary += "Your conversational restaurant search agent is ready! You can now:\n\n"
            summary += "1. **Send natural language queries** like:\n"
            summary += "   - 'Find restaurants in Central district'\n"
            summary += "   - 'Breakfast places in Tsim Sha Tsui'\n"
            summary += "   - 'Good dinner spots'\n\n"
            summary += "2. **Use the AgentCore Runtime API** to interact with the agent\n"
            summary += "3. **Authenticate using JWT tokens** from Cognito\n\n"
        else:
            summary += "## Next Steps\n\n"
            summary += "The system is not fully ready. Please:\n\n"
            summary += "1. Check the deployment logs for errors\n"
            summary += "2. Ensure all prerequisites are met\n"
            summary += "3. Re-run the deployment if necessary\n\n"
        
        # Technical details
        summary += "## Technical Details\n\n"
        summary += f"- **Region:** {self.region}\n"
        summary += f"- **Foundation Model:** Claude 3.5 Sonnet\n"
        summary += f"- **MCP Protocol:** Enabled\n"
        summary += f"- **Authentication:** JWT via Cognito\n"
        summary += f"- **Natural Language Processing:** Enabled\n\n"
        
        return summary
    
    def save_deployment_config(self) -> None:
        """Save complete deployment configuration."""
        config = {
            'deployment_timestamp': time.time(),
            'region': self.region,
            'deployment_status': self.deployment_status,
            'system_ready': self.deployment_status['system_ready']
        }
        
        try:
            with open("complete_system_deployment.json", "w") as f:
                json.dump(config, f, indent=2, default=str)
            print(f"✅ Deployment configuration saved to: complete_system_deployment.json")
        except Exception as e:
            print(f"⚠️ Could not save deployment configuration: {e}")
    
    def deploy_complete_system(self) -> Dict[str, Any]:
        """Execute complete system deployment workflow.
        
        Returns:
            Complete deployment results.
        """
        print("🚀 Starting Complete Restaurant Search System Deployment\n")
        print("=" * 60)
        
        deployment_results = {
            'started_at': time.time(),
            'prerequisites_met': False,
            'mcp_deployment': None,
            'agent_deployment': None,
            'integration_validation': None,
            'end_to_end_tests': None,
            'overall_success': False
        }
        
        try:
            # Step 1: Check prerequisites
            print("\n📋 Step 1: Checking Prerequisites")
            prerequisites = self.check_prerequisites()
            deployment_results['prerequisites'] = prerequisites
            
            # Check if critical prerequisites are met
            critical_checks = ['cognito_config', 'mcp_server_code', 'aws_credentials']
            prerequisites_met = all(prerequisites.get(check, False) for check in critical_checks)
            deployment_results['prerequisites_met'] = prerequisites_met
            
            if not prerequisites_met:
                print("❌ Critical prerequisites not met. Please resolve issues before continuing.")
                return deployment_results
            
            print("✅ Prerequisites check passed")
            
            # Step 2: Deploy MCP Server
            print("\n" + "=" * 60)
            print("📋 Step 2: Deploying MCP Server")
            mcp_result = self.deploy_mcp_server()
            deployment_results['mcp_deployment'] = mcp_result
            
            if not mcp_result.get('deployment_successful'):
                print("❌ MCP Server deployment failed. Cannot continue.")
                return deployment_results
            
            # Step 3: Deploy Conversational Agent
            print("\n" + "=" * 60)
            print("📋 Step 3: Deploying Conversational Agent")
            agent_result = self.deploy_conversational_agent()
            deployment_results['agent_deployment'] = agent_result
            
            if not agent_result.get('deployment_successful'):
                print("❌ Conversational Agent deployment failed.")
                # Continue with validation to see partial system status
            
            # Step 4: Validate Integration
            print("\n" + "=" * 60)
            print("📋 Step 4: Validating System Integration")
            integration_result = self.validate_system_integration()
            deployment_results['integration_validation'] = integration_result
            
            # Step 5: Run End-to-End Tests
            print("\n" + "=" * 60)
            print("📋 Step 5: Running End-to-End Tests")
            test_result = self.test_end_to_end_system()
            deployment_results['end_to_end_tests'] = test_result
            
            # Determine overall success
            deployment_results['overall_success'] = (
                mcp_result.get('deployment_successful', False) and
                agent_result.get('deployment_successful', False) and
                integration_result.get('overall_integration', False) and
                test_result.get('overall_success', False)
            )
            
            # Step 6: Generate Summary
            print("\n" + "=" * 60)
            print("📋 Step 6: Generating Deployment Summary")
            
            summary = self.generate_deployment_summary()
            
            # Save summary to file
            try:
                with open("deployment_summary.md", "w", encoding='utf-8') as f:
                    f.write(summary)
                print("✅ Deployment summary saved to: deployment_summary.md")
            except Exception as e:
                print(f"⚠️ Could not save deployment summary: {e}")
            
            # Save deployment configuration
            self.save_deployment_config()
            
            # Final status
            print("\n" + "=" * 60)
            if deployment_results['overall_success']:
                print("🎉 COMPLETE SYSTEM DEPLOYMENT SUCCESSFUL!")
                print("\nYour conversational restaurant search agent is ready to use!")
                print("You can now send natural language queries and get restaurant recommendations.")
            else:
                print("⚠️ DEPLOYMENT COMPLETED WITH ISSUES")
                print("\nSome components may not be fully functional.")
                print("Please check the logs and deployment summary for details.")
            
            deployment_results['completed_at'] = time.time()
            return deployment_results
            
        except Exception as e:
            print(f"\n💥 Deployment failed with error: {e}")
            deployment_results['error'] = str(e)
            deployment_results['completed_at'] = time.time()
            return deployment_results


def main():
    """Main function to run complete system deployment."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Deploy Complete Restaurant Search Conversational System')
    parser.add_argument('--region', default='us-east-1', help='AWS region (default: us-east-1)')
    parser.add_argument('--check-only', action='store_true', help='Only check prerequisites')
    parser.add_argument('--mcp-only', action='store_true', help='Only deploy MCP server')
    parser.add_argument('--agent-only', action='store_true', help='Only deploy conversational agent')
    parser.add_argument('--test-only', action='store_true', help='Only run tests')
    
    args = parser.parse_args()
    
    try:
        deployment = CompleteSystemDeployment(region=args.region)
        
        if args.check_only:
            prerequisites = deployment.check_prerequisites()
            all_met = all(prerequisites.values())
            print(f"\nAll prerequisites met: {'✅ Yes' if all_met else '❌ No'}")
            return 0 if all_met else 1
        
        elif args.mcp_only:
            result = deployment.deploy_mcp_server()
            return 0 if result.get('deployment_successful') else 1
        
        elif args.agent_only:
            result = deployment.deploy_conversational_agent()
            return 0 if result.get('deployment_successful') else 1
        
        elif args.test_only:
            result = deployment.test_end_to_end_system()
            return 0 if result.get('overall_success') else 1
        
        else:
            # Complete deployment
            result = deployment.deploy_complete_system()
            return 0 if result.get('overall_success') else 1
        
    except Exception as e:
        print(f"\n💥 Deployment script failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())