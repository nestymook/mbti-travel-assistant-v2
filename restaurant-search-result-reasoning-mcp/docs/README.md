# Restaurant Search MCP - Documentation

## 📚 Documentation Index

This directory contains comprehensive documentation for the Restaurant Search MCP project.

## 🚀 Quick Start

1. **[Deployment Guide](DEPLOYMENT_GUIDE.md)** - Deploy the MCP server to AWS
2. **[Testing Guide](TESTING_GUIDE.md)** - Test the deployed system
3. **[Authentication Setup](COGNITO_SETUP_GUIDE.md)** - Configure Cognito authentication

## 📖 Core Documentation

### Deployment & Operations
- **[Deployment Guide](DEPLOYMENT_GUIDE.md)** - Complete deployment instructions
- **[Authentication Setup](COGNITO_SETUP_GUIDE.md)** - Cognito configuration guide
- **[Script Cleanup Recommendations](SCRIPT_CLEANUP_RECOMMENDATIONS.md)** - Code organization

### Testing & Validation
- **[Testing Guide](TESTING_GUIDE.md)** - Comprehensive testing instructions
- **[MCP Tool Usage Examples](MCP_TOOL_USAGE_EXAMPLES.md)** - Tool usage documentation
- **[Authentication Usage Examples](AUTHENTICATION_USAGE_EXAMPLES.md)** - Auth examples

### Project Status
- **[Final Deployment Success](../FINAL_DEPLOYMENT_SUCCESS.md)** - Deployment completion status
- **[Deployment Success Summary](../DEPLOYMENT_SUCCESS_SUMMARY.md)** - Technical details
- **[Password Security Update](../PASSWORD_SECURITY_UPDATE.md)** - Security improvements

## 🎯 Essential Scripts

### Deployment
```bash
# Complete deployment workflow
python execute_deployment.py

# Manual deployment steps
python deploy_agentcore.py
```

### Testing
```bash
# Authentication testing
python test_auth_prompt.py

# Comprehensive agent testing
python test_deployed_agent_toolkit.py
```

### Setup
```bash
# Cognito setup
python setup_cognito.py

# Test user creation
python create_test_user_cli.py
```

## 🏗️ Architecture Overview

### Components
- **BedrockAgentCoreApp** (`main.py`) - Main entrypoint with Strands Agent
- **MCP Server** (`restaurant_mcp_server.py`) - FastMCP implementation
- **Restaurant Service** - Business logic and data access
- **Authentication** - JWT via Amazon Cognito

### MCP Tools
1. **`search_restaurants_by_district`** - Search by Hong Kong districts
2. **`search_restaurants_by_meal_type`** - Search by breakfast/lunch/dinner
3. **`search_restaurants_combined`** - Combined district and meal type search

### Data Sources
- **S3 Bucket**: Restaurant data storage
- **District Service**: Hong Kong geographic data
- **Time Service**: Meal time classification

## 🔐 Security Features

- **JWT Authentication** via Amazon Cognito
- **Secure Password Prompting** in all test scripts
- **No Hardcoded Secrets** in source code
- **Environment Variable Support** for automation

## 📊 Deployment Status

### Current Status: ✅ PRODUCTION READY

- **Agent Status**: READY
- **Endpoint Status**: READY
- **Authentication**: JWT (Cognito) ✅
- **MCP Tools**: All functional ✅
- **Platform**: linux/arm64 ✅

### Agent Information
- **Agent ID**: `restaurant_search_conversational_agent-dsuHTs5FJn`
- **Protocol**: MCP
- **Region**: us-east-1
- **Network**: PUBLIC

## 🛠️ Development Workflow

### 1. Setup
```bash
# Clone and setup
git clone <repository>
cd restaurant-search-mcp
pip install -r requirements.txt
```

### 2. Authentication
```bash
# Setup Cognito (one-time)
python setup_cognito.py

# Create test user
python create_test_user_cli.py
```

### 3. Deploy
```bash
# Deploy to AWS
python execute_deployment.py
```

### 4. Test
```bash
# Test authentication
python test_auth_prompt.py

# Test deployed agent
python test_deployed_agent_toolkit.py
```

## 🔍 Troubleshooting

### Common Issues
1. **Authentication Errors** - Check Cognito configuration
2. **Deployment Failures** - Verify AWS permissions
3. **404 Errors in Tests** - Expected for MCP protocol agents

### Debug Commands
```bash
# Check authentication
python debug_auth.py

# Check deployment status
python deploy_agentcore.py --status-only

# View logs
aws logs tail /aws/bedrock-agentcore/runtimes/AGENT_ID-DEFAULT --follow
```

## 📈 Monitoring

### CloudWatch Integration
- **Logs**: `/aws/bedrock-agentcore/runtimes/AGENT_ID-DEFAULT`
- **Metrics**: Custom CloudWatch metrics
- **Tracing**: X-Ray integration
- **Dashboard**: GenAI Observability Console

### Health Checks
- Agent status monitoring
- Authentication flow validation
- MCP tool functionality testing

## 🔄 Updates & Maintenance

### Code Updates
```bash
# Redeploy with latest changes
python execute_deployment.py
```

### Configuration Updates
```bash
# Update AgentCore configuration
python deploy_agentcore.py --configure-only
```

### User Management
```bash
# Update test user
python update_test_user.py

# Reset password
python update_test_user_password.py
```

## 📚 Additional Resources

### AWS Documentation
- [Amazon Bedrock AgentCore Developer Guide](https://docs.aws.amazon.com/bedrock-agentcore/)
- [Amazon Cognito Documentation](https://docs.aws.amazon.com/cognito/)
- [Model Context Protocol (MCP)](https://modelcontextprotocol.io/)

### Project Resources
- [GitHub Repository](https://github.com/your-org/restaurant-search-mcp)
- [Issue Tracker](https://github.com/your-org/restaurant-search-mcp/issues)
- [Contributing Guidelines](../CONTRIBUTING.md)

---

**Documentation Version**: 1.0.0  
**Last Updated**: September 27, 2025  
**Status**: Complete and Current