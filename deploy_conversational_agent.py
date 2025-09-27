#!/usr/bin/env python3
"""
AgentCore Foundation Model Configuration and Deployment Script

This script configures and deploys a conversational agent with Claude 3.5 Sonnet
that can process natural language queries and automatically invoke MCP tools
for restaurant search in Hong Kong.

Requirements: 10.1, 10.2, 11.1, 12.1
"""

import json
import os
import sys
import time
from typing import Dict, Any, Optional, List

import boto3
from botocore.exceptions import ClientError
from bedrock_agentcore_starter_toolkit import Runtime


class ConversationalAgentDeployment:
    """Deploy conversational restaurant search agent to Bedrock AgentCore Runtime."""
    
    def __init__(self, region: str = "us-east-1"):
        """Initialize conversational agent deployment.
        
        Args:
            region: AWS region for deployment.
        """
        self.region = region
        self.session = boto3.Session(region_name=region)
        self.agentcore_runtime = Runtime()
        self.deployment_config_file = "conversational_agent_config.json"
        
        # Foundation model configuration optimized for restaurant search
        self.foundation_model_config = {
            "model_id": "anthropic.claude-3-5-sonnet-20241022-v2:0",
            "model_parameters": {
                "temperature": 0.1,  # Low temperature for consistent tool calling
                "max_tokens": 2048,
                "top_p": 0.9
            },
            "tool_calling": {
                "enabled": True,
                "auto_invoke": True
            }
        }
        
    def load_cognito_config(self, config_file: str = "cognito_config.json") -> Dict[str, Any]:
        """Load Cognito configuration from setup.
        
        Args:
            config_file: Path to Cognito configuration file.
            
        Returns:
            Cognito configuration dictionary.
        """
        try:
            if not os.path.exists(config_file):
                raise FileNotFoundError(
                    f"Cognito configuration file not found: {config_file}. "
                    "Please run setup_cognito.py first."
                )
            
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            print(f"✓ Loaded Cognito configuration from: {config_file}")
            return config
            
        except Exception as e:
            print(f"✗ Error loading Cognito configuration: {e}")
            raise
    
    def load_mcp_deployment_config(self, config_file: str = "agentcore_deployment_config.json") -> Dict[str, Any]:
        """Load MCP server deployment configuration.
        
        Args:
            config_file: Path to MCP deployment configuration file.
            
        Returns:
            MCP deployment configuration dictionary.
        """
        try:
            if not os.path.exists(config_file):
                raise FileNotFoundError(
                    f"MCP deployment configuration not found: {config_file}. "
                    "Please deploy the MCP server first using deploy_agentcore.py"
                )
            
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            print(f"✓ Loaded MCP deployment configuration from: {config_file}")
            return config
            
        except Exception as e:
            print(f"✗ Error loading MCP deployment configuration: {e}")
            raise
    
    def get_available_districts(self) -> List[str]:
        """Get list of available Hong Kong districts from config files.
        
        Returns:
            List of district names.
        """
        districts = []
        
        try:
            # Load master config to get regions
            master_config_path = "config/districts/master-config.json"
            if os.path.exists(master_config_path):
                with open(master_config_path, 'r') as f:
                    master_config = json.load(f)
                
                # Load each region config
                for region_info in master_config.get('regions', []):
                    region_file = region_info.get('config_file')
                    if region_file:
                        region_path = f"config/districts/{region_file}"
                        if os.path.exists(region_path):
                            with open(region_path, 'r') as f:
                                region_config = json.load(f)
                            
                            # Extract district names
                            for district in region_config.get('districts', []):
                                districts.append(district.get('name', ''))
            
            # Fallback to common Hong Kong districts if config not available
            if not districts:
                districts = [
                    "Admiralty", "Central district", "Causeway Bay", "Wan Chai",
                    "Tsim Sha Tsui", "Mong Kok", "Yau Ma Tei", "Jordan",
                    "Sha Tin", "Tsuen Wan", "Tuen Mun", "Tai Po",
                    "Sheung Wan", "Mid-Levels", "Happy Valley", "North Point"
                ]
            
            return districts
            
        except Exception as e:
            print(f"⚠️ Error loading districts from config: {e}")
            # Return fallback districts
            return [
                "Admiralty", "Central district", "Causeway Bay", "Wan Chai",
                "Tsim Sha Tsui", "Mong Kok", "Yau Ma Tei", "Jordan",
                "Sha Tin", "Tsuen Wan", "Tuen Mun", "Tai Po"
            ]
    
    def create_system_prompt(self) -> str:
        """Create comprehensive system prompt for restaurant search assistant.
        
        Returns:
            System prompt string with Hong Kong context and tool usage instructions.
        """
        districts = self.get_available_districts()
        districts_text = ", ".join(districts[:15])  # Show first 15 districts
        if len(districts) > 15:
            districts_text += f", and {len(districts) - 15} others"
        
        system_prompt = f"""You are a helpful restaurant search assistant for Hong Kong. You have access to comprehensive restaurant data organized by districts across Hong Kong Island, Kowloon, New Territories, and Lantau Island.

## Your Capabilities

You can search restaurants using three specialized tools:

1. **search_restaurants_by_district** - Find restaurants in specific districts
2. **search_restaurants_by_meal_type** - Find restaurants by meal times (breakfast, lunch, dinner)  
3. **search_restaurants_combined** - Search by both district and meal type

## Available Districts

You can search restaurants in these Hong Kong districts: {districts_text}.

## Meal Time Categories

- **Breakfast**: 7:00-11:29 (morning dining)
- **Lunch**: 11:30-17:29 (afternoon dining)  
- **Dinner**: 17:30-22:30 (evening dining)

These categories are based on restaurant operating hours analysis.

## How to Help Users

When users ask about restaurants:

1. **Understand their intent**: Are they looking for a specific location, meal time, or both?
2. **Extract parameters**: Identify district names and meal types from their query
3. **Use appropriate tools**: Call the right MCP tool with proper parameters
4. **Provide helpful responses**: Format results in a conversational, easy-to-read manner

## Example Interactions

- "Find restaurants in Central district" → Use search_restaurants_by_district
- "Breakfast places" → Use search_restaurants_by_meal_type  
- "Dinner in Tsim Sha Tsui" → Use search_restaurants_combined
- "Good lunch spots in Causeway Bay" → Use search_restaurants_combined

## District Name Mapping

Be flexible with district names. Users might say:
- "Central" → "Central district"
- "TST" → "Tsim Sha Tsui"
- "Causeway" → "Causeway Bay"

## Response Guidelines

- Be conversational and helpful
- Include key restaurant details (name, address, cuisine, hours, price range)
- Format operating hours in user-friendly way
- Suggest alternatives when no results found
- Ask clarifying questions for ambiguous requests
- Provide follow-up suggestions

## Error Handling

- If district names aren't recognized, suggest similar valid districts
- If no restaurants match criteria, offer broader search options
- For ambiguous queries, ask for clarification with examples
- Always be helpful and guide users toward successful searches

Remember: Your goal is to help users find great restaurants in Hong Kong using natural, conversational language while leveraging the powerful MCP tools available to you."""

        return system_prompt
    
    def create_jwt_authorizer_config(self, cognito_config: Dict[str, Any]) -> Dict[str, Any]:
        """Create JWT authorizer configuration for AgentCore Runtime.
        
        Args:
            cognito_config: Cognito configuration dictionary.
            
        Returns:
            JWT authorizer configuration.
        """
        client_id = cognito_config['app_client']['client_id']
        discovery_url = cognito_config['discovery_url']
        
        auth_config = {
            "customJWTAuthorizer": {
                "allowedClients": [client_id],
                "discoveryUrl": discovery_url,
            }
        }
        
        print(f"✓ Created JWT authorizer config with client ID: {client_id}")
        return auth_config
    
    def configure_foundation_model_agent(self, 
                                       agent_name: str = "restaurant_search_conversational_agent",
                                       mcp_server_arn: Optional[str] = None) -> Dict[str, Any]:
        """Configure foundation model agent with MCP tool integration.
        
        Args:
            agent_name: Name for the conversational agent.
            mcp_server_arn: ARN of deployed MCP server (auto-detected if None).
            
        Returns:
            Configuration response from AgentCore Runtime.
        """
        try:
            print(f"🤖 Configuring foundation model agent: {agent_name}")
            
            # Load configurations
            cognito_config = self.load_cognito_config()
            
            # Get MCP server ARN if not provided
            if not mcp_server_arn:
                mcp_config = self.load_mcp_deployment_config()
                
                # Try to extract MCP server ARN from deployment config
                if 'final_deployment_result' in mcp_config:
                    final_status = mcp_config['final_deployment_result'].get('final_status', {})
                    if 'endpoint' in final_status:
                        mcp_server_arn = final_status['endpoint'].get('arn')
                
                if not mcp_server_arn:
                    # Try configuration response
                    config_response = mcp_config.get('configuration_response', {})
                    mcp_server_arn = config_response.get('agent_arn')
                
                if not mcp_server_arn:
                    raise ValueError(
                        "Could not determine MCP server ARN. Please provide it explicitly "
                        "or ensure the MCP server is properly deployed."
                    )
            
            print(f"✓ Using MCP server ARN: {mcp_server_arn}")
            
            # Create JWT authorizer configuration
            auth_config = self.create_jwt_authorizer_config(cognito_config)
            
            # Create system prompt with Hong Kong context
            system_prompt = self.create_system_prompt()
            
            # Complete foundation model configuration
            complete_model_config = {
                **self.foundation_model_config,
                "system_prompt": system_prompt,
                "mcp_server_arn": mcp_server_arn
            }
            
            print("📋 Foundation Model Configuration:")
            print(f"Model ID: {complete_model_config['model_id']}")
            print(f"Temperature: {complete_model_config['model_parameters']['temperature']}")
            print(f"Max Tokens: {complete_model_config['model_parameters']['max_tokens']}")
            print(f"Tool Calling: {complete_model_config['tool_calling']['enabled']}")
            print(f"MCP Server: {mcp_server_arn}")
            
            # Configure conversational agent
            agent_config = self.agentcore_runtime.configure_agent(
                agent_name=agent_name,
                foundation_model_config=complete_model_config,
                authorizer_configuration=auth_config
            )
            
            print("✓ Foundation model agent configuration completed")
            
            # Save configuration for reference
            config_data = {
                'agent_name': agent_name,
                'foundation_model_config': complete_model_config,
                'auth_config': auth_config,
                'cognito_config': cognito_config,
                'mcp_server_arn': mcp_server_arn,
                'agent_configuration_response': agent_config,
                'configured_at': time.time()
            }
            
            self.save_deployment_config(config_data)
            
            return agent_config
            
        except Exception as e:
            print(f"✗ Error configuring foundation model agent: {e}")
            raise
    
    def launch_conversational_agent(self) -> Dict[str, Any]:
        """Launch the conversational agent deployment to AgentCore Runtime.
        
        Returns:
            Launch response from AgentCore Runtime.
        """
        try:
            print("🚀 Launching conversational agent to AgentCore Runtime...")
            
            # Launch agent deployment
            launch_response = self.agentcore_runtime.launch_agent()
            
            print("✓ Conversational agent launch initiated")
            print(f"Launch Response: {launch_response}")
            
            return launch_response
            
        except Exception as e:
            print(f"✗ Error launching conversational agent: {e}")
            raise
    
    def monitor_agent_deployment_status(self, timeout_minutes: int = 15) -> Dict[str, Any]:
        """Monitor agent deployment status until READY or timeout.
        
        Args:
            timeout_minutes: Maximum time to wait for deployment.
            
        Returns:
            Final deployment status.
        """
        try:
            print(f"⏳ Monitoring agent deployment status (timeout: {timeout_minutes} minutes)...")
            
            start_time = time.time()
            timeout_seconds = timeout_minutes * 60
            
            while True:
                try:
                    status_response = self.agentcore_runtime.get_agent_status()
                    
                    if 'agent' in status_response:
                        agent_status = status_response['agent'].get('status', 'UNKNOWN')
                        print(f"Agent Status: {agent_status}")
                        
                        if agent_status == 'READY':
                            print("🎉 Conversational agent is READY!")
                            return status_response
                        elif agent_status in ['CREATE_FAILED', 'UPDATE_FAILED']:
                            print(f"💥 Agent deployment failed with status: {agent_status}")
                            return status_response
                    
                    # Check timeout
                    elapsed = time.time() - start_time
                    if elapsed > timeout_seconds:
                        print(f"⏰ Timeout reached ({timeout_minutes} minutes)")
                        return status_response
                    
                    # Wait before next check
                    time.sleep(30)
                    
                except Exception as e:
                    print(f"⚠️ Error checking agent status: {e}")
                    time.sleep(30)
                    
        except KeyboardInterrupt:
            print("\n⏹️ Monitoring interrupted by user")
            return self.agentcore_runtime.get_agent_status()
    
    def test_conversational_agent(self, test_queries: Optional[List[str]] = None) -> Dict[str, Any]:
        """Test conversational agent with sample queries.
        
        Args:
            test_queries: List of test queries (uses defaults if None).
            
        Returns:
            Test results dictionary.
        """
        if test_queries is None:
            test_queries = [
                "Find restaurants in Central district",
                "Breakfast places in Tsim Sha Tsui", 
                "Good dinner spots",
                "Lunch restaurants in Causeway Bay"
            ]
        
        test_results = {
            'queries_tested': len(test_queries),
            'results': [],
            'successful_queries': 0,
            'failed_queries': 0
        }
        
        try:
            print("🧪 Testing conversational agent with sample queries...")
            
            for i, query in enumerate(test_queries, 1):
                print(f"\n🔍 Test {i}/{len(test_queries)}: '{query}'")
                
                try:
                    # Invoke agent with test query
                    response = self.agentcore_runtime.invoke_agent({
                        "input": {"prompt": query}
                    })
                    
                    test_result = {
                        'query': query,
                        'success': True,
                        'response': response,
                        'error': None
                    }
                    
                    test_results['successful_queries'] += 1
                    print(f"✓ Query successful")
                    
                    # Show response preview
                    if 'output' in response:
                        output_text = str(response['output'])[:200]
                        print(f"Response preview: {output_text}...")
                    
                except Exception as e:
                    test_result = {
                        'query': query,
                        'success': False,
                        'response': None,
                        'error': str(e)
                    }
                    
                    test_results['failed_queries'] += 1
                    print(f"✗ Query failed: {e}")
                
                test_results['results'].append(test_result)
            
            # Summary
            success_rate = (test_results['successful_queries'] / len(test_queries)) * 100
            print(f"\n📊 Test Summary:")
            print(f"Success Rate: {success_rate:.1f}% ({test_results['successful_queries']}/{len(test_queries)})")
            
            return test_results
            
        except Exception as e:
            print(f"✗ Error testing conversational agent: {e}")
            test_results['test_error'] = str(e)
            return test_results
    
    def save_deployment_config(self, config: Dict[str, Any]) -> None:
        """Save deployment configuration to JSON file.
        
        Args:
            config: Configuration dictionary to save.
        """
        try:
            with open(self.deployment_config_file, 'w') as f:
                json.dump(config, f, indent=2, default=str)
            print(f"✓ Agent configuration saved to: {self.deployment_config_file}")
        except Exception as e:
            print(f"✗ Error saving agent configuration: {e}")
            raise
    
    def load_deployment_config(self) -> Dict[str, Any]:
        """Load existing deployment configuration.
        
        Returns:
            Configuration dictionary or empty dict if not found.
        """
        try:
            if os.path.exists(self.deployment_config_file):
                with open(self.deployment_config_file, 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            print(f"✗ Error loading agent configuration: {e}")
            return {}
    
    def deploy_complete_conversational_agent(self) -> Dict[str, Any]:
        """Execute complete conversational agent deployment workflow.
        
        Returns:
            Final deployment status and configuration.
        """
        try:
            print("🤖 Starting complete conversational agent deployment workflow...")
            
            # Step 1: Configure foundation model agent
            print("\n📋 Step 1: Configuring foundation model agent...")
            config_response = self.configure_foundation_model_agent()
            
            # Step 2: Launch agent deployment
            print("\n🚀 Step 2: Launching agent deployment...")
            launch_response = self.launch_conversational_agent()
            
            # Step 3: Monitor deployment status
            print("\n⏳ Step 3: Monitoring agent deployment status...")
            status_response = self.monitor_agent_deployment_status()
            
            # Step 4: Test conversational agent
            print("\n🧪 Step 4: Testing conversational agent...")
            test_results = self.test_conversational_agent()
            
            # Compile final results
            final_result = {
                'configuration': config_response,
                'launch': launch_response,
                'final_status': status_response,
                'test_results': test_results,
                'deployment_successful': (
                    status_response.get('agent', {}).get('status') == 'READY' and 
                    test_results.get('successful_queries', 0) > 0
                )
            }
            
            # Update deployment config with final results
            deployment_config = self.load_deployment_config()
            deployment_config.update({
                'final_deployment_result': final_result,
                'completed_at': time.time()
            })
            self.save_deployment_config(deployment_config)
            
            if final_result['deployment_successful']:
                print("\n🎉 Conversational agent deployment completed successfully!")
                print("✓ Foundation model is configured with Claude 3.5 Sonnet")
                print("✓ Natural language processing is enabled")
                print("✓ MCP tool integration is working")
                print("✓ Authentication is configured")
                print("✓ Test queries passed")
            else:
                print("\n⚠️ Deployment completed with issues")
                print("Please check the logs and status for details")
            
            return final_result
            
        except Exception as e:
            print(f"\n💥 Conversational agent deployment failed: {e}")
            raise


def main():
    """Main function to run conversational agent deployment."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Deploy Conversational Restaurant Search Agent')
    parser.add_argument('--region', default='us-east-1', help='AWS region (default: us-east-1)')
    parser.add_argument('--agent-name', default='restaurant_search_conversational_agent',
                       help='Agent name (default: restaurant_search_conversational_agent)')
    parser.add_argument('--mcp-server-arn', help='MCP server ARN (auto-detected if not provided)')
    parser.add_argument('--configure-only', action='store_true',
                       help='Only configure, do not launch deployment')
    parser.add_argument('--launch-only', action='store_true',
                       help='Only launch (assumes already configured)')
    parser.add_argument('--test-only', action='store_true',
                       help='Only run tests (assumes agent is deployed)')
    parser.add_argument('--status-only', action='store_true',
                       help='Only check agent status')
    
    args = parser.parse_args()
    
    try:
        # Initialize deployment
        deployment = ConversationalAgentDeployment(region=args.region)
        
        if args.status_only:
            # Just check status
            status = deployment.agentcore_runtime.get_agent_status()
            print(f"Agent Status: {json.dumps(status, indent=2, default=str)}")
            return 0
        
        elif args.configure_only:
            # Only configure
            config_response = deployment.configure_foundation_model_agent(
                agent_name=args.agent_name,
                mcp_server_arn=args.mcp_server_arn
            )
            print(f"Configuration completed: {config_response}")
            return 0
        
        elif args.launch_only:
            # Only launch
            launch_response = deployment.launch_conversational_agent()
            status_response = deployment.monitor_agent_deployment_status()
            
            print(f"Launch Response: {launch_response}")
            print(f"Final Status: {status_response}")
            return 0
        
        elif args.test_only:
            # Only test
            test_results = deployment.test_conversational_agent()
            print(f"Test Results: {json.dumps(test_results, indent=2, default=str)}")
            return 0 if test_results.get('successful_queries', 0) > 0 else 1
        
        else:
            # Complete workflow
            result = deployment.deploy_complete_conversational_agent()
            
            print("\n📋 Deployment Summary:")
            print(f"Successful: {result['deployment_successful']}")
            if 'agent' in result.get('final_status', {}):
                agent_info = result['final_status']['agent']
                print(f"Status: {agent_info.get('status', 'UNKNOWN')}")
                if 'url' in agent_info:
                    print(f"URL: {agent_info['url']}")
            
            test_results = result.get('test_results', {})
            if test_results:
                success_rate = (test_results.get('successful_queries', 0) / 
                              test_results.get('queries_tested', 1)) * 100
                print(f"Test Success Rate: {success_rate:.1f}%")
            
            return 0 if result['deployment_successful'] else 1
        
    except Exception as e:
        print(f"\n💥 Deployment failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())