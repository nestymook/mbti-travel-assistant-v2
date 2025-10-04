#!/usr/bin/env python3
"""
AgentCore Gateway Deployment Script

This script deploys the AWS Bedrock AgentCore Gateway using the native MCP protocol
router configuration files. It creates the Gateway with proper MCP server routing,
JWT authentication, circuit breaker, and health check configurations.

Requirements Implemented:
- 5.1, 5.2: AWS CLI commands for Gateway creation with native MCP configuration
- 2.1: Gateway appears in Bedrock AgentCore console
- 1.1, 1.2: Native MCP protocol routing without conversion
- 3.1, 3.2, 3.3: JWT authentication over MCP protocol headers
"""

import json
import yaml
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, Any, Optional, List
import boto3
from botocore.exceptions import ClientError, NoCredentialsError


class AgentCoreGatewayDeployer:
    """Deploys AWS Bedrock AgentCore Gateway with native MCP protocol routing."""
    
    def __init__(self, region: str = "us-east-1", config_dir: str = "config"):
        """
        Initialize the gateway deployer.
        
        Args:
            region: AWS region for deployment
            config_dir: Directory containing configuration files
        """
        self.region = region
        self.config_dir = Path(config_dir)
        self.gateway_name = "agentcore-mcp-gateway"
        
        # Initialize AWS clients
        try:
            self.sts_client = boto3.client('sts', region_name=region)
            self.bedrock_agentcore_control_client = boto3.client('bedrock-agentcore-control', region_name=region)
            self.cloudwatch_client = boto3.client('cloudwatch', region_name=region)
            self.iam_client = boto3.client('iam', region_name=region)
            
            # Get account ID
            self.account_id = self.sts_client.get_caller_identity()['Account']
            
        except NoCredentialsError:
            print("❌ AWS credentials not configured. Please run 'aws configure'")
            sys.exit(1)
        except Exception as e:
            print(f"❌ Error initializing AWS clients: {e}")
            sys.exit(1)
    
    def deploy_gateway(self) -> bool:
        """
        Deploy the AgentCore Gateway as an AgentCore Runtime.
        
        Since AWS Bedrock AgentCore Gateway service is not available,
        we deploy the HTTP-to-MCP gateway as an AgentCore Runtime.
        
        Returns:
            True if deployment successful, False otherwise
        """
        print("🚀 Deploying AWS Bedrock AgentCore Gateway")
        print("=" * 80)
        print("ℹ️  Attempting to create native AWS Bedrock AgentCore Gateway.")
        print("   Will fall back to AgentCore Runtime deployment if not available.")
        print()
        
        try:
            # Step 1: Load configuration files
            gateway_config = self._load_gateway_config()
            if not gateway_config:
                return False
            
            # Step 2: Check if gateway already exists
            existing_gateway = self._check_existing_gateway()
            if existing_gateway:
                print(f"⚠️  Gateway '{self.gateway_name}' already exists")
                update_choice = input("Do you want to update it? (y/N): ").lower().strip()
                if update_choice != 'y':
                    print("❌ Deployment cancelled")
                    return False
            
            # Step 3: Try to create AWS Bedrock AgentCore Gateway
            print("\n🔍 Attempting to create AWS Bedrock AgentCore Gateway...")
            gateway_id = self._create_native_agentcore_gateway(gateway_config)
            
            if gateway_id:
                # Native AgentCore Gateway created successfully
                print(f"✅ Native AgentCore Gateway created: {gateway_id}")
                
                # Step 4: Wait for Gateway to be active
                if not self._wait_for_gateway_active(gateway_id):
                    return False
                
                # Step 5: Configure Gateway monitoring
                self._setup_gateway_monitoring(gateway_id)
                
                # Step 6: Verify Gateway in console
                self._verify_console_integration(gateway_id)
                
                # Step 7: Test Gateway functionality
                self._test_gateway_functionality(gateway_id)
                
                print("\n🎉 Native AgentCore Gateway deployment completed successfully!")
                print(f"✅ Gateway ID: {gateway_id}")
                print(f"✅ Gateway Name: {self.gateway_name}")
                print(f"✅ Region: {self.region}")
                print(f"✅ Console URL: https://console.aws.amazon.com/bedrock/home?region={self.region}#/agentcore/gateways/{gateway_id}")
                
                return True
            else:
                # Fall back to AgentCore Runtime deployment
                print("\n⚠️  Native AgentCore Gateway service not available. Falling back to AgentCore Runtime deployment...")
                return self._deploy_as_agentcore_runtime()
            
        except Exception as e:
            print(f"❌ Gateway deployment failed: {e}")
            return False
    
    def _validate_configurations(self) -> bool:
        """Validate all configuration files before deployment."""
        print("\n🔍 Validating configuration files...")
        
        # Run the validation script
        validation_script = Path(__file__).parent / "validate_gateway_config.py"
        
        try:
            result = subprocess.run([
                sys.executable, str(validation_script)
            ], capture_output=True, text=True, cwd=self.config_dir.parent)
            
            if result.returncode == 0:
                print("✅ Configuration validation passed")
                return True
            else:
                print("❌ Configuration validation failed:")
                print(result.stdout)
                print(result.stderr)
                return False
                
        except Exception as e:
            print(f"❌ Error running configuration validation: {e}")
            return False
    
    def _load_gateway_config(self) -> Optional[Dict[str, Any]]:
        """Load the main gateway configuration file."""
        print("\n📋 Loading gateway configuration...")
        
        config_file = self.config_dir / "gateway-config.yaml"
        
        try:
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f)
            
            print("✅ Gateway configuration loaded successfully")
            return config
            
        except Exception as e:
            print(f"❌ Error loading gateway configuration: {e}")
            return None
    
    def _check_existing_agentcore_runtime(self) -> Optional[Dict[str, Any]]:
        """Check if an AgentCore Runtime with the same name already exists."""
        print("\n🔍 Checking for existing AgentCore Runtime...")
        
        try:
            # Check if there's an existing .bedrock_agentcore.yaml file
            agentcore_config = self.config_dir.parent / ".bedrock_agentcore.yaml"
            if agentcore_config.exists():
                with open(agentcore_config, 'r') as f:
                    config = yaml.safe_load(f)
                    
                if 'bedrock_agentcore' in config.get('agents', {}).get('main', {}):
                    runtime_info = config['agents']['main']['bedrock_agentcore']
                    print(f"⚠️  Found existing AgentCore Runtime: {runtime_info.get('agent_arn', 'Unknown ARN')}")
                    return runtime_info
            
            print("✅ No existing AgentCore Runtime found")
            return None
            
        except Exception as e:
            print(f"❌ Error checking existing AgentCore Runtime: {e}")
            return None
    
    def _check_existing_gateway(self) -> Optional[Dict[str, Any]]:
        """Check if a gateway with the same name already exists using boto3."""
        print("\n🔍 Checking for existing gateway...")
        
        try:
            response = self.bedrock_agentcore_control_client.list_gateways()
            
            for gateway in response.get('gateways', []):
                if gateway.get('gatewayName') == self.gateway_name:
                    print(f"⚠️  Found existing gateway: {gateway['gatewayId']}")
                    return gateway
            
            print("✅ No existing gateway found")
            return None
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'AccessDeniedException':
                print("❌ Access denied. Please check your AWS permissions for Bedrock AgentCore")
            elif error_code in ['InvalidAction', 'UnknownOperation']:
                print("⚠️  AWS Bedrock AgentCore Gateway service may not be available in this region")
                print("    Proceeding with AgentCore Runtime deployment instead...")
                return None
            else:
                print(f"❌ Error checking existing gateways: {e}")
            return None
        except Exception as e:
            print(f"❌ Error checking existing gateways: {e}")
            return None
    
    def _create_gateway_iam_role(self) -> Optional[str]:
        """Create IAM role for the AgentCore Gateway."""
        print("\n🔐 Creating IAM role for Gateway...")
        
        role_name = f"{self.gateway_name}-role"
        
        # Trust policy for AgentCore Gateway
        trust_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {
                        "Service": "bedrock-agentcore.amazonaws.com"
                    },
                    "Action": "sts:AssumeRole"
                }
            ]
        }
        
        # Permissions policy for Gateway operations
        permissions_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "bedrock:InvokeModel",
                        "bedrock:InvokeModelWithResponseStream",
                        "bedrock-agentcore:*",
                        "logs:CreateLogGroup",
                        "logs:CreateLogStream",
                        "logs:PutLogEvents",
                        "cloudwatch:PutMetricData",
                        "xray:PutTraceSegments",
                        "xray:PutTelemetryRecords"
                    ],
                    "Resource": "*"
                }
            ]
        }
        
        try:
            # Check if role already exists
            try:
                response = self.iam_client.get_role(RoleName=role_name)
                role_arn = response['Role']['Arn']
                print(f"✅ Using existing IAM role: {role_arn}")
                return role_arn
            except ClientError as e:
                if e.response['Error']['Code'] != 'NoSuchEntity':
                    raise
            
            # Create the role
            response = self.iam_client.create_role(
                RoleName=role_name,
                AssumeRolePolicyDocument=json.dumps(trust_policy),
                Description=f"IAM role for AgentCore Gateway {self.gateway_name}"
            )
            
            role_arn = response['Role']['Arn']
            
            # Attach permissions policy
            self.iam_client.put_role_policy(
                RoleName=role_name,
                PolicyName=f"{role_name}-permissions",
                PolicyDocument=json.dumps(permissions_policy)
            )
            
            print(f"✅ Created IAM role: {role_arn}")
            
            # Wait for role to be available
            time.sleep(10)
            
            return role_arn
            
        except Exception as e:
            print(f"❌ Error creating IAM role: {e}")
            return None
    
    def _create_native_agentcore_gateway(self, gateway_config: Dict[str, Any]) -> Optional[str]:
        """Try to create a native AWS Bedrock AgentCore Gateway using boto3."""
        try:
            print("🔍 Creating AWS Bedrock AgentCore Gateway using boto3...")
            
            # Extract configuration from YAML
            spec = gateway_config['spec']
            metadata = gateway_config['metadata']
            
            # Define tool schemas for existing MCP servers
            tool_definitions = []
            
            for server in spec['mcp_servers']:
                for tool in server['tools']:
                    tool_schema = {
                        "toolName": tool['name'],
                        "toolType": "agentcore_runtime",
                        "agentCoreRuntimeArn": self._get_agentcore_runtime_arn(server['name']),
                        "description": tool['description'],
                        "inputSchema": {
                            "type": "object",
                            "properties": self._get_tool_input_schema(tool['name'])
                        }
                    }
                    tool_definitions.append(tool_schema)
            
            # Create IAM role for Gateway first
            gateway_role_arn = self._create_gateway_iam_role()
            if not gateway_role_arn:
                print("❌ Failed to create IAM role for Gateway")
                return None
            
            # Create the Gateway using boto3 with correct parameters (control plane)
            response = self.bedrock_agentcore_control_client.create_gateway(
                name=self.gateway_name,
                description=metadata.get('description', 'AgentCore Gateway for native MCP protocol routing'),
                roleArn=gateway_role_arn,
                protocolType='MCP',
                protocolConfiguration={
                    'mcp': {
                        'supportedVersions': ['2024-11-05'],
                        'instructions': 'Gateway for restaurant search and reasoning MCP tools with MBTI travel planning integration',
                        'searchType': 'SEMANTIC'
                    }
                },
                authorizerType='CUSTOM_JWT',
                authorizerConfiguration={
                    'customJWTAuthorizer': {
                        'discoveryUrl': spec['authentication']['jwt_validation']['discovery_url'],
                        'allowedClients': [spec['authentication']['jwt_validation']['client_id']]
                    }
                }
            )
            
            gateway_id = response['gatewayId']
            print(f"✅ Gateway created successfully: {gateway_id}")
            
            return gateway_id
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            
            if error_code in ['InvalidAction', 'UnknownOperation', 'AccessDeniedException']:
                print(f"⚠️  AWS Bedrock AgentCore Gateway service not available: {error_code}")
                print(f"    Error: {error_message}")
                return None
            else:
                print(f"❌ AWS API Error creating gateway: {error_code} - {error_message}")
                return None
        except Exception as e:
            print(f"⚠️  Could not create native AgentCore Gateway: {e}")
            return None
    

    
    def _deploy_as_agentcore_runtime(self) -> bool:
        """Deploy the gateway as an AgentCore Runtime instead of native Gateway."""
        print("\n🔄 Deploying as AgentCore Runtime...")
        
        try:
            # Use the existing deploy_agentcore.py script
            deploy_script = self.config_dir.parent / "scripts" / "deploy_agentcore.py"
            
            if not deploy_script.exists():
                print("❌ AgentCore deployment script not found")
                return False
            
            # Run the AgentCore deployment script
            deploy_command = [
                sys.executable, str(deploy_script),
                '--agent-name', self.gateway_name,
                '--region', self.region
            ]
            
            print(f"Executing: {' '.join(deploy_command)}")
            result = subprocess.run(
                deploy_command,
                cwd=str(self.config_dir.parent),
                check=True
            )
            
            print("✅ AgentCore Runtime deployment completed successfully!")
            print(f"✅ Agent Name: {self.gateway_name}")
            print(f"✅ Region: {self.region}")
            print(f"✅ Console URL: https://console.aws.amazon.com/bedrock/home?region={self.region}#/agentcore/runtimes")
            
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ AgentCore Runtime deployment failed: {e}")
            return False
        except Exception as e:
            print(f"❌ Error deploying as AgentCore Runtime: {e}")
            return False
    

    
    def _get_agentcore_runtime_arn(self, server_name: str) -> str:
        """Get the AgentCore Runtime ARN for a given MCP server."""
        # Map server names to their AgentCore Runtime ARNs
        server_arns = {
            "restaurant-search-mcp": "arn:aws:bedrock-agentcore:us-east-1:209803798463:runtime/restaurant_search_conversational_agent-dsuHTs5FJn",
            "restaurant-reasoning-mcp": "arn:aws:bedrock-agentcore:us-east-1:209803798463:runtime/restaurant_reasoning_mcp-UFz1VQCFu1",
            "mbti-travel-assistant-mcp": "arn:aws:bedrock-agentcore:us-east-1:209803798463:runtime/main-DUQgnrHqCl"
        }
        
        return server_arns.get(server_name, f"arn:aws:bedrock-agentcore:{self.region}:{self.account_id}:runtime/{server_name}")
    
    def _get_tool_input_schema(self, tool_name: str) -> Dict[str, Any]:
        """Get the input schema for a specific tool."""
        # Define input schemas for each tool
        tool_schemas = {
            "search_restaurants_by_district": {
                "districts": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of Hong Kong districts to search"
                }
            },
            "search_restaurants_by_meal_type": {
                "meal_types": {
                    "type": "array",
                    "items": {"type": "string", "enum": ["breakfast", "lunch", "dinner"]},
                    "description": "List of meal types to search for"
                }
            },
            "search_restaurants_combined": {
                "districts": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional list of districts to filter by"
                },
                "meal_types": {
                    "type": "array",
                    "items": {"type": "string", "enum": ["breakfast", "lunch", "dinner"]},
                    "description": "Optional list of meal types to filter by"
                }
            },
            "recommend_restaurants": {
                "restaurants": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "name": {"type": "string"},
                            "sentiment": {
                                "type": "object",
                                "properties": {
                                    "likes": {"type": "integer"},
                                    "dislikes": {"type": "integer"},
                                    "neutral": {"type": "integer"}
                                }
                            }
                        }
                    },
                    "description": "List of restaurants with sentiment data"
                },
                "ranking_method": {
                    "type": "string",
                    "enum": ["sentiment_likes", "combined_sentiment"],
                    "description": "Method to use for ranking restaurants"
                }
            },
            "analyze_restaurant_sentiment": {
                "restaurants": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "name": {"type": "string"},
                            "sentiment": {
                                "type": "object",
                                "properties": {
                                    "likes": {"type": "integer"},
                                    "dislikes": {"type": "integer"},
                                    "neutral": {"type": "integer"}
                                }
                            }
                        }
                    },
                    "description": "List of restaurants to analyze sentiment for"
                }
            },
            "create_mbti_itinerary": {
                "personality_type": {
                    "type": "string",
                    "pattern": "^[EIJP][NSFT][FT][JP]$",
                    "description": "MBTI personality type (e.g., ENFP, ISTJ)"
                },
                "preferences": {
                    "type": "object",
                    "properties": {
                        "budget": {"type": "string"},
                        "interests": {"type": "array", "items": {"type": "string"}},
                        "duration": {"type": "integer", "default": 3}
                    },
                    "description": "Travel preferences and constraints"
                }
            },
            "get_personality_recommendations": {
                "personality_type": {
                    "type": "string",
                    "pattern": "^[EIJP][NSFT][FT][JP]$",
                    "description": "MBTI personality type"
                },
                "category": {
                    "type": "string",
                    "enum": ["restaurants", "activities", "accommodations"],
                    "description": "Category of recommendations to get"
                }
            }
        }
        
        return tool_schemas.get(tool_name, {
            "query": {
                "type": "string",
                "description": "Query parameter for the tool"
            }
        })
    
    def _format_mcp_servers_for_api(self, mcp_servers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format MCP servers configuration for the API."""
        formatted_servers = []
        
        for server in mcp_servers:
            formatted_server = {
                'serverName': server['name'],
                'endpoint': server['endpoint'],
                'protocol': server['protocol'],
                'transport': server.get('transport', 'stdio'),
                'healthCheck': {
                    'path': server['health_check']['path'],
                    'interval': server['health_check']['interval'],
                    'timeout': server['health_check']['timeout'],
                    'retries': server['health_check']['retries']
                },
                'tools': [
                    {
                        'name': tool['name'],
                        'description': tool['description'],
                        'schemaRef': tool['schema_ref']
                    }
                    for tool in server['tools']
                ],
                'metadata': server.get('metadata', {})
            }
            formatted_servers.append(formatted_server)
        
        return formatted_servers
    
    def _update_gateway(self, gateway_id: str, gateway_config: Dict[str, Any]) -> bool:
        """Update an existing gateway."""
        print(f"\n🔄 Updating existing gateway: {gateway_id}")
        
        try:
            spec = gateway_config['spec']
            
            update_params = {
                'gatewayId': gateway_id,
                'gatewayConfiguration': {
                    'mcpServers': self._format_mcp_servers_for_api(spec['mcp_servers']),
                    'authentication': spec['authentication'],
                    'circuitBreaker': spec.get('circuit_breaker', {}),
                    'loadBalancing': spec.get('load_balancing', {}),
                    'observability': spec.get('observability', {}),
                    'security': spec.get('security', {})
                }
            }
            
            response = self.bedrock_agentcore_control_client.update_gateway(**update_params)
            
            print("✅ Gateway updated successfully")
            return True
            
        except Exception as e:
            print(f"❌ Error updating gateway: {e}")
            return False
    
    def _wait_for_gateway_active(self, gateway_id: str, timeout: int = 300) -> bool:
        """Wait for the gateway to become active using boto3."""
        print(f"\n⏳ Waiting for gateway to become active (timeout: {timeout}s)...")
        
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                response = self.bedrock_agentcore_control_client.get_gateway(gatewayId=gateway_id)
                status = response['gateway']['status']
                
                print(f"   Gateway status: {status}")
                
                if status == 'ACTIVE':
                    print("✅ Gateway is now active")
                    return True
                elif status == 'FAILED':
                    print("❌ Gateway deployment failed")
                    return False
                
                time.sleep(10)
                
            except ClientError as e:
                print(f"❌ Error checking gateway status: {e}")
                return False
            except Exception as e:
                print(f"❌ Error checking gateway status: {e}")
                return False
        
        print("❌ Timeout waiting for gateway to become active")
        return False
    
    def _setup_gateway_monitoring(self, gateway_id: str) -> None:
        """Set up CloudWatch monitoring for the gateway."""
        print("\n📊 Setting up gateway monitoring...")
        
        try:
            # Create CloudWatch dashboard
            dashboard_body = {
                "widgets": [
                    {
                        "type": "metric",
                        "properties": {
                            "metrics": [
                                ["AWS/BedrockAgentCore", "RequestCount", "GatewayId", gateway_id],
                                [".", "ErrorRate", ".", "."],
                                [".", "ResponseTime", ".", "."]
                            ],
                            "period": 300,
                            "stat": "Average",
                            "region": self.region,
                            "title": f"AgentCore Gateway Metrics - {self.gateway_name}"
                        }
                    }
                ]
            }
            
            self.cloudwatch_client.put_dashboard(
                DashboardName=f"AgentCore-Gateway-{self.gateway_name}",
                DashboardBody=json.dumps(dashboard_body)
            )
            
            print("✅ CloudWatch dashboard created")
            
        except Exception as e:
            print(f"⚠️  Warning: Could not set up monitoring: {e}")
    
    def _verify_console_integration(self, gateway_id: str) -> None:
        """Verify that the gateway appears in the AgentCore console."""
        print("\n🖥️  Verifying console integration...")
        
        try:
            response = self.bedrock_agentcore_control_client.get_gateway(gatewayId=gateway_id)
            gateway = response['gateway']
            
            print(f"✅ Gateway visible in console:")
            print(f"   Name: {gateway['gatewayName']}")
            print(f"   Status: {gateway['status']}")
            print(f"   Created: {gateway.get('createdAt', 'Unknown')}")
            print(f"   Console URL: https://console.aws.amazon.com/bedrock/home?region={self.region}#/agentcore/gateways/{gateway_id}")
            
        except Exception as e:
            print(f"⚠️  Warning: Could not verify console integration: {e}")
    
    def _test_gateway_functionality(self, gateway_id: str) -> None:
        """Test basic gateway functionality."""
        print("\n🧪 Testing gateway functionality...")
        
        try:
            # Test gateway health endpoint
            response = self.bedrock_agentcore_control_client.invoke_gateway(
                gatewayId=gateway_id,
                request={
                    'method': 'GET',
                    'path': '/health'
                }
            )
            
            if response.get('statusCode') == 200:
                print("✅ Gateway health check passed")
            else:
                print(f"⚠️  Gateway health check returned status: {response.get('statusCode')}")
            
        except Exception as e:
            print(f"⚠️  Warning: Could not test gateway functionality: {e}")
    
    def list_gateways(self) -> None:
        """List all existing gateways using boto3."""
        print("📋 Listing existing AgentCore Gateways...")
        
        try:
            response = self.bedrock_agentcore_control_client.list_gateways()
            gateways = response.get('gateways', [])
            
            if not gateways:
                print("No gateways found")
                return
            
            print(f"\nFound {len(gateways)} gateway(s):")
            print("-" * 80)
            
            for gateway in gateways:
                print(f"Name: {gateway['gatewayName']}")
                print(f"ID: {gateway['gatewayId']}")
                print(f"Status: {gateway['status']}")
                print(f"Created: {gateway.get('createdAt', 'Unknown')}")
                print("-" * 80)
                
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code in ['InvalidAction', 'UnknownOperation', 'AccessDeniedException']:
                print(f"⚠️  AWS Bedrock AgentCore Gateway service not available: {error_code}")
                print("    Listing AgentCore Runtimes instead...")
                self._list_agentcore_runtimes()
            else:
                print(f"❌ Error listing gateways: {e}")
        except Exception as e:
            print(f"❌ Error listing gateways: {e}")
    
    def _list_agentcore_runtimes(self) -> None:
        """List AgentCore Runtimes as fallback."""
        try:
            # Try to list agent runtimes using bedrock-agentcore-control client
            response = self.bedrock_agentcore_control_client.list_agent_runtimes()
            runtimes = response.get('agentRuntimes', [])
            
            if not runtimes:
                print("No AgentCore Runtimes found")
                return
            
            print(f"\nFound {len(runtimes)} AgentCore Runtime(s):")
            print("-" * 80)
            
            for runtime in runtimes:
                print(f"Name: {runtime.get('agentName', 'Unknown')}")
                print(f"ARN: {runtime.get('agentArn', 'Unknown')}")
                print(f"Status: {runtime.get('status', 'Unknown')}")
                print(f"Created: {runtime.get('createdAt', 'Unknown')}")
                print("-" * 80)
                
        except Exception as e:
            print(f"❌ Error listing AgentCore Runtimes: {e}")
            print("    This may indicate that AgentCore services are not available in this region")
    
    def delete_gateway(self, gateway_id: str) -> bool:
        """Delete a gateway."""
        print(f"🗑️  Deleting gateway: {gateway_id}")
        
        try:
            self.bedrock_agentcore_control_client.delete_gateway(gatewayId=gateway_id)
            print("✅ Gateway deletion initiated")
            return True
            
        except Exception as e:
            print(f"❌ Error deleting gateway: {e}")
            return False


def main():
    """Main function to handle command line arguments and run deployment."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Deploy AWS Bedrock AgentCore Gateway for native MCP protocol routing")
    parser.add_argument("--region", default="us-east-1", help="AWS region (default: us-east-1)")
    parser.add_argument("--config-dir", default="config", help="Configuration directory (default: config)")
    parser.add_argument("--list", action="store_true", help="List existing gateways")
    parser.add_argument("--delete", help="Delete gateway by ID")
    
    args = parser.parse_args()
    
    # Change to the script directory
    script_dir = Path(__file__).parent
    config_dir = script_dir.parent / args.config_dir
    
    # Initialize deployer
    deployer = AgentCoreGatewayDeployer(args.region, str(config_dir))
    
    # Handle different operations
    if args.list:
        deployer.list_gateways()
    elif args.delete:
        success = deployer.delete_gateway(args.delete)
        sys.exit(0 if success else 1)
    else:
        # Deploy gateway
        success = deployer.deploy_gateway()
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()