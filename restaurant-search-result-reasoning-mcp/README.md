# Restaurant Search MCP Server

A Model Context Protocol (MCP) server that provides restaurant search capabilities for Hong Kong, integrated with Amazon Bedrock AgentCore Runtime.

## 🎉 Status: PRODUCTION READY ✅

- **Agent Status**: READY
- **Endpoint Status**: READY  
- **Authentication**: JWT (Cognito) ✅
- **MCP Tools**: All functional ✅
- **Platform**: linux/arm64 ✅

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- AWS CLI configured with appropriate credentials
- Required AWS permissions: `BedrockAgentCoreFullAccess`, `AmazonBedrockFullAccess`

### Installation & Deployment
```bash
# Clone and setup
git clone <repository-url>
cd restaurant-search-mcp
pip install -r requirements.txt

# Deploy to AWS (complete workflow)
python execute_deployment.py
```

### Testing
```bash
# Test authentication
python test_auth_prompt.py

# Test MCP endpoint (recommended)
python test_mcp_endpoint_invoke.py

# Test deployed agent (legacy)
python test_deployed_agent_toolkit.py
```

## 🛠️ Core Features

### MCP Tools
1. **`search_restaurants_by_district`** - Search by Hong Kong districts
2. **`search_restaurants_by_meal_type`** - Search by breakfast/lunch/dinner
3. **`search_restaurants_combined`** - Combined district and meal type search

### Data Coverage
- **80+ Hong Kong Districts**: Central, Tsim Sha Tsui, Causeway Bay, Admiralty, etc.
- **4 Major Regions**: Hong Kong Island, Kowloon, New Territories, Islands
- **3 Meal Types**: Breakfast (07:00-11:29), Lunch (11:30-17:29), Dinner (17:30-22:30)

### Architecture
- **BedrockAgentCoreApp** (`main.py`) - Main entrypoint with Strands Agent
- **MCP Server** (`restaurant_mcp_server.py`) - FastMCP implementation
- **JWT Authentication** - Secure authentication via Amazon Cognito
- **AWS S3 Storage** - Scalable restaurant data storage

## 📋 Essential Scripts

### Deployment
```bash
python execute_deployment.py      # Complete deployment workflow
python deploy_agentcore.py        # Manual deployment operations
python setup_cognito.py           # Authentication setup
```

### Testing
```bash
python test_auth_prompt.py                # Authentication testing
python test_mcp_endpoint_invoke.py        # MCP endpoint testing (recommended)
python test_deployed_agent_toolkit.py     # Legacy agent testing
python test_simple_auth.py                # Basic auth validation
```

### Utilities
```bash
python create_test_user_cli.py     # Test user management
python debug_auth.py               # Authentication troubleshooting
```

## 🔐 Security Features

- **Secure Password Prompting**: All scripts use `getpass` for hidden input
- **No Hardcoded Secrets**: All passwords removed from source code
- **JWT Authentication**: Proper token validation and expiration handling
- **Environment Variable Support**: `COGNITO_TEST_PASSWORD` for automation

## 📊 Current Deployment

### Agent Information
- **Agent ID**: `restaurant_search_conversational_agent-dsuHTs5FJn`
- **Protocol**: MCP
- **Region**: us-east-1
- **Authentication**: JWT (Cognito)

### Usage Examples
```python
# Natural language queries (via foundation models)
"Find restaurants in Central district"
"Show me breakfast places in Tsim Sha Tsui"
"I want dinner in Causeway Bay"

# Direct MCP tool usage (via Kiro integration)
search_restaurants_by_district(["Central district"])
search_restaurants_by_meal_type(["breakfast"])
search_restaurants_combined(districts=["Central district"], meal_types=["dinner"])
```

## 📚 Documentation

- **[Deployment Guide](docs/DEPLOYMENT_GUIDE.md)** - Complete deployment instructions
- **[Testing Guide](docs/TESTING_GUIDE.md)** - Comprehensive testing documentation
- **[Authentication Setup](docs/COGNITO_SETUP_GUIDE.md)** - Cognito configuration
- **[Script Cleanup](docs/SCRIPT_CLEANUP_RECOMMENDATIONS.md)** - Code organization
- **[Full Documentation Index](docs/README.md)** - All documentation

## 🔍 Troubleshooting

### Common Issues
1. **Authentication Errors** - Run `python debug_auth.py`
2. **Deployment Failures** - Check `python deploy_agentcore.py --status-only`
3. **404 Errors in Tests** - Expected for MCP protocol agents (not REST endpoints)

### Monitoring
```bash
# Check deployment status
python deploy_agentcore.py --status-only

# View logs
aws logs tail /aws/bedrock-agentcore/runtimes/restaurant_search_conversational_agent-dsuHTs5FJn-DEFAULT --follow
```

## 🎯 Project Structure

```
restaurant-search-mcp/
├── main.py                          # BedrockAgentCoreApp entrypoint
├── restaurant_mcp_server.py         # FastMCP server
├── execute_deployment.py            # Main deployment script
├── test_auth_prompt.py             # Primary auth test
├── test_deployed_agent_toolkit.py  # Primary deployment test
├── services/                       # Business logic
├── models/                         # Data models
├── tests/                          # Test suite
└── docs/                           # Documentation
```

## 🔄 Development Workflow

### Code Updates
```bash
# Redeploy with changes
python execute_deployment.py
```

### Testing Workflow
```bash
# 1. Test authentication
python test_auth_prompt.py

# 2. Test deployment status
python test_deployed_agent_toolkit.py

# 3. Test MCP tools (recommended - via Kiro integration)
# Use MCP tools directly in Kiro IDE:
search_restaurants_by_district(["Central district"])
search_restaurants_by_meal_type(["breakfast"])
search_restaurants_combined(districts=["Central district"], meal_types=["dinner"])
```

## 📈 Success Metrics

- **Deployment Time**: ~2 minutes (including CodeBuild)
- **Authentication**: JWT tokens working
- **MCP Tools**: All functional with restaurant data
- **Observability**: CloudWatch + X-Ray enabled
- **Security**: No hardcoded secrets, secure prompting

---

**Project Status**: ✅ Production Ready  
**Last Updated**: September 27, 2025  
**Version**: 1.0.0