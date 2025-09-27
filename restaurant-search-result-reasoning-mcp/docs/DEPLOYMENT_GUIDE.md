# Restaurant Search MCP - Deployment Guide

## 🚀 Overview

This guide covers the deployment of the Restaurant Search MCP server to Amazon Bedrock AgentCore Runtime.

## 📋 Prerequisites

### Required Software
- Python 3.10+
- AWS CLI configured with appropriate credentials
- Docker (for local testing, optional)

### Required AWS Permissions
- `BedrockAgentCoreFullAccess`
- `AmazonBedrockFullAccess`
- IAM permissions for role creation
- ECR repository access

### Required Files
- `main.py` - BedrockAgentCoreApp entrypoint
- `restaurant_mcp_server.py` - MCP server implementation
- `requirements.txt` - Python dependencies
- `cognito_config.json` - Authentication configuration

## 🔧 Deployment Methods

### Method 1: Complete Deployment (Recommended)
Use the comprehensive deployment script that handles the entire workflow:

```bash
python execute_deployment.py
```

**Features:**
- Validates prerequisites
- Configures AgentCore Runtime
- Launches deployment with CodeBuild
- Monitors deployment status
- Tests connectivity

### Method 2: Manual Deployment
For more control over the deployment process:

```bash
# Step 1: Configure AgentCore
python deploy_agentcore.py --configure-only

# Step 2: Launch deployment
python deploy_agentcore.py --launch-only

# Step 3: Check status
python deploy_agentcore.py --status-only
```

## 📁 Key Configuration Files

### `.bedrock_agentcore.yaml`
```yaml
default_agent: restaurant_search_conversational_agent
agents:
  restaurant_search_conversational_agent:
    name: restaurant_search_conversational_agent
    entrypoint: main.py
    platform: linux/arm64
    protocol_configuration:
      server_protocol: MCP
    authorizer_configuration:
      customJWTAuthorizer:
        allowedClients: [CLIENT_ID]
        discoveryUrl: COGNITO_DISCOVERY_URL
```

### `cognito_config.json`
```json
{
  "user_pool": {
    "user_pool_id": "us-east-1_XXXXXXXXX"
  },
  "app_client": {
    "client_id": "XXXXXXXXXXXXXXXXXXXXXXXXXX"
  },
  "region": "us-east-1",
  "discovery_url": "https://cognito-idp.us-east-1.amazonaws.com/..."
}
```

## 🔐 Authentication Setup

### Cognito Configuration
If you don't have Cognito configured, the deployment script will set it up automatically:

```bash
python setup_cognito.py
```

### Test User Creation
Create a test user for authentication testing:

```bash
python create_test_user_cli.py
```

## 📊 Deployment Process

### 1. Prerequisites Validation
- AWS credentials check
- Required files verification
- Python dependencies validation

### 2. AgentCore Configuration
- Runtime configuration
- Authentication setup
- Container configuration

### 3. CodeBuild Deployment
- ARM64 container build
- ECR repository creation
- Image deployment

### 4. Status Monitoring
- Agent status verification
- Endpoint readiness check
- Connectivity testing

## 🎯 Expected Results

### Successful Deployment
```
🎉 DEPLOYMENT SUCCESSFUL!

✅ Summary:
  - MCP server deployed to AgentCore Runtime
  - JWT authentication configured with Cognito
  - Connectivity test passed
  - Ready to serve MCP tool requests

Agent ARN: arn:aws:bedrock-agentcore:us-east-1:ACCOUNT:runtime/restaurant_search_conversational_agent-XXXXX
```

### Agent Information
- **Status**: READY
- **Protocol**: MCP
- **Authentication**: JWT (Cognito)
- **Platform**: linux/arm64
- **Network**: PUBLIC

## 🔍 Troubleshooting

### Common Issues

#### 1. Authentication Errors
```bash
# Check Cognito configuration
python debug_auth.py

# Verify JWT tokens
python test_auth_prompt.py
```

#### 2. Deployment Failures
```bash
# Check deployment status
python deploy_agentcore.py --status-only

# View logs
aws logs tail /aws/bedrock-agentcore/runtimes/AGENT_ID-DEFAULT --follow
```

#### 3. Container Build Issues
- Ensure ARM64 platform compatibility
- Check Dockerfile configuration
- Verify requirements.txt dependencies

### Log Locations
- **Agent Logs**: `/aws/bedrock-agentcore/runtimes/AGENT_ID-DEFAULT`
- **CodeBuild Logs**: AWS CodeBuild console
- **Deployment Logs**: Local `deployment_execution_summary.json`

## 📈 Monitoring

### CloudWatch Dashboards
- GenAI Observability Dashboard
- Custom metrics and alarms
- X-Ray tracing integration

### Health Checks
```bash
# Check agent status
python deploy_agentcore.py --status-only

# Test authentication
python test_auth_prompt.py
```

## 🔄 Updates and Redeployment

### Code Updates
```bash
# Redeploy with latest code
python execute_deployment.py
```

### Configuration Changes
```bash
# Update configuration only
python deploy_agentcore.py --configure-only
```

## 📚 Related Documentation

- [Testing Guide](TESTING_GUIDE.md)
- [Authentication Setup](COGNITO_SETUP_GUIDE.md)
- [MCP Tool Usage](MCP_TOOL_USAGE_EXAMPLES.md)
- [Troubleshooting](TROUBLESHOOTING_GUIDE.md)

---

**Last Updated**: September 27, 2025  
**Version**: 1.0.0