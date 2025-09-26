# Restaurant Search MCP - AgentCore Runtime Deployment Guide

This guide explains how to deploy the Restaurant Search MCP server to Amazon Bedrock AgentCore Runtime.

## Prerequisites

### AWS Setup
1. **AWS Account**: Ensure you have an AWS account with appropriate permissions
2. **AWS CLI**: Install and configure AWS CLI with credentials
   ```bash
   aws configure
   ```
3. **Required IAM Permissions**:
   - `BedrockAgentCoreFullAccess`
   - `AmazonBedrockFullAccess`
   - `AmazonCognitoFullAccess`
   - `IAMFullAccess` (for auto-creation of execution roles)
   - `AmazonEC2ContainerRegistryFullAccess` (for ECR repository)

### Python Environment
1. **Python 3.10+**: Ensure Python 3.10 or later is installed
2. **Dependencies**: Install required packages
   ```bash
   pip install -r requirements.txt
   ```

## Deployment Files

The deployment consists of several key files:

### Core Deployment Scripts
- **`deploy_agentcore.py`**: Main deployment configuration script
- **`execute_deployment.py`**: Complete deployment workflow executor
- **`setup_cognito.py`**: Cognito User Pool setup for authentication

### Testing and Validation
- **`test_deployment_config.py`**: Validates deployment readiness
- **`demo_deployment_workflow.py`**: Demonstrates deployment process
- **`tests/test_remote_client.py`**: Tests deployed MCP server

### Configuration Files
- **`requirements.txt`**: Python dependencies
- **`restaurant_mcp_server.py`**: MCP server implementation
- **`config/`**: District and restaurant configuration data

## Deployment Process

### Step 1: Validate Deployment Readiness

Before deploying, run the readiness test to ensure all components are properly configured:

```bash
python test_deployment_config.py
```

This will check:
- ✅ Required files exist
- ✅ Python syntax is valid
- ✅ MCP tools are properly configured
- ✅ Configuration directory structure is correct
- ⚠️ Python packages (install with `pip install -r requirements.txt`)

### Step 2: Run Complete Deployment

Execute the full deployment workflow:

```bash
python execute_deployment.py
```

This will automatically:
1. **Validate Prerequisites**: Check AWS credentials, files, and dependencies
2. **Setup Cognito Authentication**: Create User Pool and App Client if needed
3. **Configure AgentCore Runtime**: Set up deployment configuration
4. **Launch Deployment**: Deploy MCP server to AgentCore Runtime
5. **Monitor Status**: Wait for deployment to reach READY state
6. **Test Connectivity**: Verify deployment is working correctly

### Step 3: Manual Deployment Steps (Alternative)

If you prefer to run steps manually:

#### 3.1 Setup Cognito Authentication
```bash
python setup_cognito.py --region us-east-1 --email your-test-email@example.com
```

#### 3.2 Configure AgentCore Runtime
```bash
python deploy_agentcore.py --configure-only
```

#### 3.3 Launch Deployment
```bash
python deploy_agentcore.py --launch-only
```

#### 3.4 Check Deployment Status
```bash
python deploy_agentcore.py --status-only
```

## Configuration Options

### AgentCore Runtime Configuration

The deployment uses these default settings:
- **Entrypoint**: `restaurant_mcp_server.py`
- **Protocol**: `MCP`
- **Agent Name**: `restaurant_search_mcp`
- **Region**: `us-east-1`
- **Auto-create Execution Role**: `True`
- **Auto-create ECR Repository**: `True`

### Cognito Authentication Configuration

- **User Pool Name**: `restaurant-search-mcp-pool`
- **App Client Name**: `restaurant-search-mcp-client`
- **Authentication Flows**: `USER_PASSWORD_AUTH`, `USER_SRP_AUTH`
- **Token Validity**: 60 minutes (Access/ID), 30 days (Refresh)

### MCP Tools Available

The deployed server exposes these MCP tools:
1. **`search_restaurants_by_district`**: Search restaurants by district name(s)
2. **`search_restaurants_by_meal_type`**: Search restaurants by meal time
3. **`search_restaurants_combined`**: Search with both district and meal type filters

## Testing the Deployment

### Remote Client Testing

After successful deployment, test the MCP server:

```bash
python tests/test_remote_client.py
```

This will:
- Authenticate with Cognito to get JWT token
- Connect to deployed AgentCore Runtime endpoint
- List available MCP tools
- Test each tool with sample data

### Manual Testing with MCP Client

You can also test manually using the MCP client pattern:

```python
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

# Use the endpoint URL from deployment
mcp_url = "https://bedrock-agentcore.us-east-1.amazonaws.com/runtimes/YOUR_AGENT_ARN/invocations"
headers = {"authorization": f"Bearer {jwt_token}"}

async with streamablehttp_client(mcp_url, headers) as (read, write, _):
    async with ClientSession(read, write) as session:
        await session.initialize()
        tools = await session.list_tools()
        result = await session.call_tool("search_restaurants_by_district", 
                                       {"districts": ["Central district"]})
```

## Monitoring and Management

### Deployment Status

Check deployment status anytime:
```bash
python deploy_agentcore.py --status-only
```

### Configuration Files

After deployment, these files contain important information:
- **`cognito_config.json`**: Cognito User Pool and App Client details
- **`agentcore_deployment_config.json`**: AgentCore Runtime configuration
- **`deployment_execution_summary.json`**: Deployment execution results

### AWS Console Monitoring

Monitor your deployment in the AWS Console:
1. **Bedrock AgentCore**: View runtime status and logs
2. **Amazon ECR**: Check container repository
3. **Amazon Cognito**: Manage user pool and authentication
4. **CloudWatch**: View logs and metrics

## Troubleshooting

### Common Issues

#### 1. AWS Credentials Not Configured
```
Error: AWS credentials not configured
Solution: Run `aws configure` and provide your credentials
```

#### 2. Missing Python Dependencies
```
Error: ModuleNotFoundError: No module named 'mcp'
Solution: Run `pip install -r requirements.txt`
```

#### 3. Cognito Configuration Missing
```
Error: Cognito configuration file not found
Solution: Run `python setup_cognito.py` first
```

#### 4. Deployment Timeout
```
Error: Deployment timeout reached
Solution: Check AWS Console for detailed error messages
```

### Getting Help

1. **Check Logs**: Review deployment logs in AWS CloudWatch
2. **Validate Configuration**: Run `python test_deployment_config.py`
3. **Check Status**: Run `python deploy_agentcore.py --status-only`
4. **AWS Support**: Contact AWS Support for AgentCore-specific issues

## Security Considerations

### Authentication
- JWT tokens are used for authentication via Amazon Cognito
- Tokens expire after 60 minutes and must be refreshed
- Test user credentials should be changed in production

### Network Security
- AgentCore Runtime endpoints use HTTPS
- All communication is encrypted in transit
- IAM roles provide least-privilege access

### Data Security
- Restaurant data is retrieved from S3 with read-only access
- No sensitive data is stored in the MCP server
- All inputs are validated before processing

## Production Deployment

### Before Production
1. **Change Test User**: Create production users in Cognito
2. **Review IAM Permissions**: Ensure least-privilege access
3. **Configure Monitoring**: Set up CloudWatch alarms
4. **Test Thoroughly**: Run comprehensive integration tests
5. **Document Procedures**: Create operational runbooks

### Scaling Considerations
- AgentCore Runtime automatically scales based on demand
- Monitor performance metrics in CloudWatch
- Consider regional deployment for global users
- Implement proper error handling and retry logic

## Cost Optimization

### AgentCore Runtime Costs
- Pay-per-use pricing model
- No charges when not processing requests
- Monitor usage in AWS Cost Explorer

### Associated Service Costs
- Amazon Cognito: Free tier available
- Amazon ECR: Storage and data transfer charges
- CloudWatch: Logs and metrics storage

## Next Steps

After successful deployment:
1. **Integrate with Foundation Models**: Use MCP tools in your AI applications
2. **Monitor Performance**: Set up CloudWatch dashboards
3. **Expand Functionality**: Add more MCP tools as needed
4. **Scale Deployment**: Consider multi-region deployment
5. **Optimize Costs**: Monitor and optimize resource usage

---

For additional support, refer to the [Amazon Bedrock AgentCore documentation](https://docs.aws.amazon.com/bedrock/) or contact AWS Support.