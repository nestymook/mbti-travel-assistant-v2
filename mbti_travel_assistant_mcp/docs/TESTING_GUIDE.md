# Restaurant Search MCP - Testing Guide

## 🧪 Overview

This guide covers testing the deployed Restaurant Search MCP server, including authentication, MCP tools, and end-to-end functionality.

## 📋 Test Categories

### 1. Authentication Tests
Verify JWT authentication with Cognito

### 2. MCP Tool Tests
Test individual MCP tools functionality

### 3. Integration Tests
End-to-end testing with deployed agent

### 4. Performance Tests
Load and performance validation

## 🔐 Authentication Testing

### Quick Authentication Test
```bash
python test_auth_prompt.py
```

**What it tests:**
- Cognito connection
- JWT token generation
- Token validation
- User credentials

**Expected Output:**
```
✅ Authentication successful!
Access token length: 1072
Token client_id: 1ofgeckef3po4i3us4j1m4chvd
Token username: 4428f438-20a1-7021-c626-786491287b40
```

### Simple Authentication Test
```bash
python test_simple_auth.py
```

**Features:**
- Basic Cognito authentication
- No admin permissions required
- Secure password prompting

## 🛠️ MCP Tool Testing (Recommended Method)

### Kiro MCP Integration Testing ⭐
**This is the best and most accurate way to test MCP tools.**

Kiro IDE has built-in MCP integration that allows direct testing of MCP tools:

#### Quick Test Commands
```python
# Test 1: District Search
search_restaurants_by_district(["Central district"])

# Test 2: Meal Type Search  
search_restaurants_by_meal_type(["breakfast"])

# Test 3: Combined Search
search_restaurants_combined(
    districts=["Central district"], 
    meal_types=["dinner"]
)
```

#### Natural Language Testing
Use Kiro's chat interface:
```
Find restaurants in Central district
Show me breakfast places in Tsim Sha Tsui
I want dinner in Causeway Bay
```

#### Comprehensive Guide
📚 **[Complete Kiro MCP Testing Guide](KIRO_MCP_TESTING_GUIDE.md)**  
🚀 **[Quick Start Guide](../KIRO_MCP_QUICK_START.md)**

### Available Districts
- **Hong Kong Island**: Central district, Admiralty, Causeway Bay, Wan Chai
- **Kowloon**: Tsim Sha Tsui, Mong Kok, Yau Ma Tei, Jordan
- **New Territories**: Sha Tin, Tai Po, Yuen Long, Tuen Mun
- **Islands**: Lantau Island, Discovery Bay, Tung Chung

### Available Meal Types
- **Breakfast**: 07:00-11:29
- **Lunch**: 11:30-17:29
- **Dinner**: 17:30-22:30

## 🚀 Deployed Agent Testing

### MCP Endpoint Invoke Test (Recommended)
```bash
python test_mcp_endpoint_invoke.py
```

**What it tests:**
- MCP tools functionality
- AgentCore Runtime invoke method
- Proper MCP protocol communication
- Agent deployment status

**Features:**
- Direct MCP tool testing simulation
- Runtime.invoke() method testing
- Comprehensive error analysis
- Authentication reference testing

### Legacy Agent Test
```bash
python test_deployed_agent_toolkit.py
```

**What it tests:**
- Agent deployment status
- JWT authentication flow
- MCP invoke attempts
- Error handling

**Note:** This test may show authentication mismatches (SigV4 vs JWT) which is expected behavior.

### Expected Behavior
- **MCP Tools**: Should work via Kiro MCP integration
- **Runtime.invoke()**: May fail due to authentication method mismatch (toolkit uses SigV4, agent expects JWT)
- **Agent Status**: Should show READY for both agent and endpoint
- **HTTP 404 Errors**: Expected for direct HTTP calls (MCP agents don't expose REST endpoints)

## 📊 Test Results Interpretation

### Successful Authentication
```
✅ Authentication successful!
🔍 Agent Status: READY
🔍 Endpoint Status: READY
🔍 Protocol: MCP
```

### Expected HTTP 404 Errors
```
✗ All endpoints failed. Last: HTTP 404: Invalid api path
```

**This is normal** - MCP protocol agents don't expose HTTP REST endpoints.

### MCP Tool Success
```json
{
  "success": true,
  "data": {
    "restaurants": [...],
    "count": 5,
    "metadata": {
      "search_criteria": {
        "districts": ["Central district"]
      }
    }
  }
}
```

## 🔧 Test Scripts Overview

### Essential Test Scripts

#### 1. `test_auth_prompt.py` ⭐
**Purpose**: Authentication testing  
**Usage**: `python test_auth_prompt.py`  
**Features**: Secure password prompting, token validation

#### 2. `test_deployed_agent_toolkit.py` ⭐
**Purpose**: Comprehensive agent testing  
**Usage**: `python test_deployed_agent_toolkit.py`  
**Features**: Status checking, authentication flow testing

#### 3. `test_simple_auth.py`
**Purpose**: Basic authentication validation  
**Usage**: `python test_simple_auth.py`  
**Features**: Simple Cognito connection test

### Legacy/Deprecated Scripts
These scripts are kept for reference but not actively maintained:

- `test_conversational_agent.py` - Superseded by toolkit test
- `test_deployed_conversational_agent.py` - Redundant functionality
- `test_agentcore_*` variants - Multiple similar implementations

## 🎯 Testing Workflow

### 1. Pre-Deployment Testing
```bash
# Test authentication setup
python test_auth_prompt.py

# Verify Cognito configuration
python debug_auth.py
```

### 2. Post-Deployment Testing
```bash
# Check deployment status
python deploy_agentcore.py --status-only

# Test deployed agent
python test_deployed_agent_toolkit.py
```

### 3. MCP Tool Testing
```bash
# Use Kiro MCP integration to test tools directly
# This is the recommended approach for functional testing
```

## 🔍 Troubleshooting Tests

### Authentication Issues
```bash
# Debug authentication problems
python debug_auth.py

# Check user status (requires admin permissions)
python update_test_user.py --check-only
```

### Deployment Issues
```bash
# Check agent status
python deploy_agentcore.py --status-only

# View deployment logs
aws logs tail /aws/bedrock-agentcore/runtimes/AGENT_ID-DEFAULT --since 1h
```

## 📈 Test Automation

### Environment Variables
```bash
# Set password for automated testing
export COGNITO_TEST_PASSWORD="your_password"

# Run tests without prompting
python test_deployed_agent_toolkit.py
```

### CI/CD Integration
```bash
# Automated test suite
python -m pytest tests/ -v

# Authentication test only
python test_auth_prompt.py --non-interactive
```

## 📋 Test Checklist

### Pre-Deployment
- [ ] AWS credentials configured
- [ ] Cognito setup completed
- [ ] Test user created
- [ ] Authentication working

### Post-Deployment
- [ ] Agent status: READY
- [ ] Endpoint status: READY
- [ ] JWT authentication working
- [ ] MCP tools functional

### Functional Testing
- [ ] District search working
- [ ] Meal type search working
- [ ] Combined search working
- [ ] Error handling proper

## 🎉 Success Criteria

### Authentication Success
- JWT tokens generated successfully
- Token validation passes
- User authentication works

### Deployment Success
- Agent status: READY
- Endpoint status: READY
- No deployment errors

### MCP Tool Success
- All tools return valid responses
- District data available
- Search functionality working

## 📚 Related Documentation

- [Deployment Guide](DEPLOYMENT_GUIDE.md)
- [Authentication Setup](COGNITO_SETUP_GUIDE.md)
- [MCP Tool Usage](MCP_TOOL_USAGE_EXAMPLES.md)
- [Troubleshooting](TROUBLESHOOTING_GUIDE.md)

---

**Last Updated**: September 27, 2025  
**Version**: 1.0.0