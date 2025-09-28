# AWS Testing Suite for Restaurant Reasoning MCP Server

This directory contains comprehensive tests for the Restaurant Reasoning MCP Server deployed on AWS with JWT authentication.

## 🎯 Overview

The AWS-deployed Restaurant Reasoning MCP Server uses:
- **AWS Bedrock AgentCore Runtime** for hosting
- **Amazon Nova Pro** model for reasoning
- **JWT authentication** via Amazon Cognito
- **MCP protocol** for tool communication

## 🧪 Test Files

### 1. `run_aws_tests.py` - Main Test Runner
Interactive menu-driven test runner that provides options for different test types.

**Usage:**
```bash
python tests/run_aws_tests.py
```

**Features:**
- Interactive menu selection
- Comprehensive or focused testing options
- Automatic result saving
- User-friendly progress reporting

### 2. `test_aws_deployment_comprehensive.py` - Full Deployment Testing
Comprehensive test suite covering all aspects of the AWS deployment.

**Test Categories:**
- ✅ JWT Authentication Setup
- ✅ Deployment Information Validation
- ✅ Authenticated Connectivity Testing
- ✅ MCP Client with JWT
- ✅ MCP Tools Functionality
- ✅ Performance Testing (multiple dataset sizes)
- ✅ Error Handling and Edge Cases

**Usage:**
```bash
python tests/test_aws_deployment_comprehensive.py
```

### 3. `test_aws_mcp_tools_direct.py` - Direct MCP Tools Testing
Focused testing of MCP tools with JWT authentication.

**Test Coverage:**
- ✅ MCP Connection and Tool Discovery
- ✅ `recommend_restaurants` with `sentiment_likes` method
- ✅ `recommend_restaurants` with `combined_sentiment` method
- ✅ `analyze_restaurant_sentiment` functionality

**Usage:**
```bash
python tests/test_aws_mcp_tools_direct.py
```

## 🔐 Authentication Requirements

All tests require JWT authentication with Amazon Cognito:

### Test User Credentials
- **Email:** `testing_user@test.com.hk`
- **Password:** *Required user input (not stored)*
- **User Pool:** `us-east-1_wBAxW7yd4`
- **Client ID:** `26k0pnja579pdpb1pt6savs27e`

### Authentication Flow
1. User enters password securely (hidden input)
2. Script authenticates with Cognito using `USER_PASSWORD_AUTH`
3. JWT token obtained and used for all subsequent requests
4. Token validated and used in MCP client headers

## 🚀 Quick Start

### Prerequisites
```bash
pip install boto3 mcp bedrock-agentcore-starter-toolkit
```

### Run Tests
```bash
# Interactive test runner (recommended)
python tests/run_aws_tests.py

# Or run specific tests directly
python tests/test_aws_mcp_tools_direct.py
python tests/test_aws_deployment_comprehensive.py
```

### Expected Prompts
```
🔐 JWT Authentication Required
==================================================
Test User Email: testing_user@test.com.hk
AWS Region: us-east-1
User Pool ID: us-east-1_wBAxW7yd4
Enter password for test user: [hidden input]
```

## 📊 Test Results

### Result Files
- `mcp_tools_test_results.json` - Direct MCP tools test results
- `comprehensive_aws_test_results.json` - Full deployment test results
- `aws_deployment_test_results.json` - Default comprehensive results

### Sample Success Output
```
📊 Test Summary:
   Total Tests: 7
   Passed: 7 ✅
   Failed: 0 ❌
   Success Rate: 100.0%
   Overall Status: SUCCESS

🎉 All tests passed! AWS deployment is working correctly.
```

## 🛠️ Test Data

### Restaurant Test Data Structure
```json
{
  "id": "rest_001",
  "name": "Golden Dragon Restaurant",
  "address": "123 Central District, Hong Kong",
  "district": "Central district",
  "location_category": "Hong Kong Island",
  "meal_type": ["lunch", "dinner"],
  "price_range": "$$",
  "sentiment": {
    "likes": 85,
    "dislikes": 10,
    "neutral": 5
  }
}
```

### Test Scenarios
- **Basic Dataset:** 5 restaurants with varied sentiment scores
- **Large Dataset:** 50 restaurants for performance testing
- **Edge Cases:** Zero sentiment, perfect scores, controversial ratings
- **Error Cases:** Empty lists, invalid methods, malformed data

## 🔧 AWS Configuration

### Agent Details
- **Agent ARN:** `arn:aws:bedrock-agentcore:us-east-1:209803798463:runtime/restaurant_reasoning_mcp-UFz1VQCFu1`
- **Region:** `us-east-1`
- **Platform:** `linux/arm64`
- **Model:** Amazon Nova Pro (`amazon.nova-pro-v1:0`)

### MCP Endpoint
- **URL Pattern:** `https://runtime.bedrock-agentcore.{region}.amazonaws.com/runtime/{agent_id}/mcp`
- **Authentication:** Bearer JWT token in Authorization header
- **Protocol:** MCP over HTTP with streaming support

## 🐛 Troubleshooting

### Common Issues

#### Authentication Failures
```
❌ Authentication failed: An error occurred (NotAuthorizedException)
```
**Solution:** Verify password and ensure test user exists in Cognito User Pool

#### MCP Connection Issues
```
❌ MCP connection failed: Connection refused
```
**Solution:** Check agent status and ensure it's in READY state

#### Tool Not Found
```
❌ Tool 'recommend_restaurants' not found
```
**Solution:** Verify agent deployment and MCP server is running correctly

### Debug Commands
```bash
# Check agent status
aws bedrock-agentcore describe-runtime --runtime-id restaurant_reasoning_mcp-UFz1VQCFu1 --region us-east-1

# View logs
aws logs tail /aws/bedrock-agentcore/runtimes/restaurant_reasoning_mcp-UFz1VQCFu1-DEFAULT --follow --region us-east-1
```

## 📈 Performance Expectations

### Response Times
- **Small Dataset (3 restaurants):** < 500ms
- **Medium Dataset (10 restaurants):** < 1000ms
- **Large Dataset (20+ restaurants):** < 2000ms

### Success Criteria
- ✅ All authentication tests pass
- ✅ MCP connection established successfully
- ✅ All tools return valid responses
- ✅ Performance within expected ranges
- ✅ Error handling works gracefully

## 🔄 Continuous Testing

### Automated Testing
These tests can be integrated into CI/CD pipelines with:
- Environment variable for test credentials
- Automated result parsing
- Slack/email notifications for failures

### Monitoring Integration
- CloudWatch alarms for test failures
- Performance regression detection
- Automated rollback on test failures

## 📞 Support

### Logs and Monitoring
- **CloudWatch Logs:** `/aws/bedrock-agentcore/runtimes/restaurant_reasoning_mcp-UFz1VQCFu1-DEFAULT`
- **X-Ray Traces:** Available in AWS X-Ray console
- **Observability Dashboard:** GenAI Observability in CloudWatch

### Contact
For issues with the testing suite or AWS deployment, check:
1. Test result files for detailed error information
2. CloudWatch logs for runtime issues
3. AWS Bedrock AgentCore documentation
4. MCP protocol specifications

---

**Last Updated:** September 28, 2025  
**Version:** 2.0.0  
**AWS Region:** us-east-1  
**Authentication:** JWT with Amazon Cognito