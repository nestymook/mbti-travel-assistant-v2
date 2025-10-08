# Three-Day Workflow Comprehensive Test

This document describes the comprehensive test suite for validating the MBTI Travel Planner Agent's three-day workflow functionality, including AgentCore HTTPS communication with JWT authentication.

## Overview

The test suite validates three critical aspects of the system:

1. **Hard-coded Request Processing**: Processing a three-day itinerary request for specific districts (Central, Tsim Sha Tsui, Causeway Bay)
2. **Restaurant Search & Reasoning Communication**: AgentCore HTTPS + JWT communication with restaurant search and reasoning AI agents
3. **Response Assembly**: Complete response assembly and return to requestor

## Test Components

### 1. System Readiness Validation (`validate_system_readiness.py`)

Validates that all system components are properly configured before running tests.

**Checks:**
- Environment variables (AWS_REGION, ENVIRONMENT)
- Configuration files (cognito_config.json, agentcore_config.py, .bedrock_agentcore.yaml)
- Python dependencies (boto3, aiohttp, etc.)
- AgentCore configuration (agent ARNs, Cognito setup)
- Main component imports (main.py, services)

### 2. Comprehensive Workflow Test (`test_three_day_workflow_comprehensive.py`)

Main test suite that validates the complete three-day workflow.

**Test Scenarios:**
- **Test 1**: System Readiness Check
- **Test 2**: Hard-coded Three-Day Request Processing
- **Test 3**: Restaurant Search AgentCore HTTPS + JWT Communication
- **Test 4**: Restaurant Reasoning AgentCore HTTPS + JWT Communication
- **Test 5**: Complete Three-Day Workflow Integration
- **Test 6**: Response Assembly and Formatting
- **Test 7**: Performance and Communication Metrics

### 3. Test Execution Script (`run_three_day_workflow_test.py`)

Simple execution script with proper environment setup and error handling.

## Quick Start

### Prerequisites

1. **Environment Setup**:
   ```bash
   export AWS_REGION=us-east-1
   export ENVIRONMENT=production
   ```

2. **Configuration Files**:
   - `config/cognito_config.json` - Cognito authentication configuration
   - `config/agentcore_config.py` - AgentCore runtime configuration
   - `.bedrock_agentcore.yaml` - AgentCore deployment configuration

3. **Dependencies**:
   ```bash
   pip install boto3 aiohttp asyncio
   ```

### Running the Tests

#### Step 1: Validate System Readiness

```bash
cd mbti-travel-planner-agent
python validate_system_readiness.py
```

**Expected Output:**
```
MBTI Travel Planner Agent - System Readiness Validation
============================================================
✅ AWS_REGION: Present
✅ ENVIRONMENT: Present
✅ config/cognito_config.json: Present
✅ AgentCore config: Loadable
✅ Restaurant search agent ARN: Configured
✅ Main components: Importable

============================================================
SYSTEM READINESS SUMMARY
============================================================
Overall Ready: ✅ YES
Readiness Score: 95.0%

Recommendations:
  1. System is ready for testing
```

#### Step 2: Run Comprehensive Test

```bash
python run_three_day_workflow_test.py
```

**Expected Output:**
```
MBTI Travel Planner Agent - Three-Day Workflow Test
============================================================
Environment setup complete:
  ENVIRONMENT: production
  AWS_REGION: us-east-1

================================================================================
STARTING COMPREHENSIVE THREE-DAY WORKFLOW TEST
================================================================================

============================================================
TEST 1: SYSTEM READINESS FOR THREE-DAY WORKFLOW
============================================================
✅ JWT token successfully obtained
✅ System readiness check PASSED - Ready for three-day workflow

============================================================
TEST 2: HARD-CODED THREE-DAY REQUEST PROCESSING
============================================================
✅ Hard-coded three-day request processing PASSED
Response time: 2.34 seconds

============================================================
TEST 3: RESTAURANT SEARCH AGENTCORE HTTPS + JWT COMMUNICATION
============================================================
✅ JWT token obtained in 0.245 seconds
✅ Central district: 15 restaurants found
✅ Tsim Sha Tsui: 12 restaurants found
✅ Causeway Bay: 18 restaurants found
✅ Combined search: 45 restaurants found
✅ Restaurant search AgentCore HTTPS + JWT communication PASSED

============================================================
TEST 4: RESTAURANT REASONING AGENTCORE HTTPS + JWT COMMUNICATION
============================================================
✅ JWT token obtained for reasoning agent in 0.198 seconds
✅ Recommendation: Causeway Trendy Bistro
✅ Candidates: 3
✅ Sentiment analysis for 3 restaurants
✅ Restaurant reasoning AgentCore HTTPS + JWT communication PASSED

============================================================
TEST 5: COMPLETE THREE-DAY WORKFLOW INTEGRATION
============================================================
✅ Complete three-day workflow integration PASSED
Workflow time: 5.67s, Restaurant recommendations: 6

============================================================
TEST 6: RESPONSE ASSEMBLY AND FORMATTING
============================================================
✅ Response assembly and formatting PASSED

============================================================
TEST 7: PERFORMANCE AND COMMUNICATION METRICS
============================================================
✅ Performance and communication metrics PASSED
Overall grade: A

================================================================================
THREE-DAY WORKFLOW TEST SUMMARY
================================================================================
Session ID: three_day_test_a1b2c3d4
Environment: production
MBTI Type: ENFP
Districts: Central district, Tsim Sha Tsui, Causeway Bay
Execution Time: 12.45 seconds
Tests Executed: 7
Tests Passed: 7
Tests Failed: 0
Overall Success Rate: 100.0%

Key Findings:
  ✅ System Ready For Three Day Workflow: True
  ✅ Agentcore Https Communication Working: True
  ✅ Jwt Authentication Working: True
  ✅ Three Day Workflow Complete: True
  ✅ Response Assembly Working: True
  ✅ Performance Meets Benchmarks: True

Recommendations:
  1. All tests passed successfully - system is ready for production use

📄 Detailed report saved to: three_day_workflow_report_three_day_test_a1b2c3d4_20241009_143022.json

🎉 All tests completed successfully!
```

## Test Configuration

### Districts Tested
- **Central district**: Business and upscale dining focus
- **Tsim Sha Tsui**: Cultural attractions and diverse restaurants
- **Causeway Bay**: Shopping and trendy food spots

### MBTI Type Tested
- **ENFP**: Extraverted, Intuitive, Feeling, Perceiving personality type

### Communication Protocols
- **AgentCore HTTPS**: Direct HTTPS calls to AgentCore Runtime endpoints
- **JWT Authentication**: Cognito-based JWT token authentication
- **Structured Prompts**: AI-optimized prompt format for agent communication

## Performance Benchmarks

| Metric | Benchmark | Description |
|--------|-----------|-------------|
| JWT Authentication | < 1 second | Time to obtain JWT token |
| AgentCore API Call | < 5 seconds | Individual agent invocation time |
| Total Workflow | < 30 seconds | Complete three-day workflow execution |
| API Success Rate | > 95% | Percentage of successful API calls |

## Test Results Analysis

### Success Criteria

A test run is considered successful if:
- All 7 test scenarios pass
- Overall success rate ≥ 80%
- Performance benchmarks are met
- All three districts are covered
- Restaurant data includes sentiment analysis
- MBTI matching is present in responses

### Common Issues and Solutions

#### Issue: JWT Authentication Fails
**Symptoms**: `JWT token acquisition failed` errors
**Solution**: 
1. Check `config/cognito_config.json` configuration
2. Verify AWS credentials and region
3. Ensure Cognito User Pool is properly configured

#### Issue: AgentCore Communication Fails
**Symptoms**: `AgentCore not available` or connection errors
**Solution**:
1. Verify agent ARNs in configuration
2. Check AWS permissions for AgentCore access
3. Ensure agents are deployed and running

#### Issue: Restaurant Data Missing
**Symptoms**: Empty restaurant results or missing sentiment data
**Solution**:
1. Check restaurant search agent deployment
2. Verify restaurant database connectivity
3. Validate search parameters and districts

## Detailed Test Reports

Each test run generates a detailed JSON report containing:

```json
{
  "test_summary": {
    "test_session_id": "three_day_test_a1b2c3d4",
    "environment": "production",
    "mbti_type_tested": "ENFP",
    "districts_tested": ["Central district", "Tsim Sha Tsui", "Causeway Bay"],
    "total_execution_time_seconds": 12.45,
    "overall_success_rate": 1.0
  },
  "key_findings": {
    "system_ready_for_three_day_workflow": true,
    "agentcore_https_communication_working": true,
    "jwt_authentication_working": true,
    "three_day_workflow_complete": true,
    "response_assembly_working": true,
    "performance_meets_benchmarks": true
  },
  "detailed_results": {
    "system_readiness": { /* detailed test results */ },
    "restaurant_search_agentcore_communication": { /* detailed test results */ },
    "restaurant_reasoning_agentcore_communication": { /* detailed test results */ }
    // ... more detailed results
  }
}
```

## Integration with CI/CD

### GitHub Actions Example

```yaml
name: Three-Day Workflow Test

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test-workflow:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        pip install boto3 aiohttp asyncio
    
    - name: Configure AWS credentials
      uses: aws-actions/configure-aws-credentials@v1
      with:
        aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
        aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        aws-region: us-east-1
    
    - name: Validate system readiness
      run: |
        cd mbti-travel-planner-agent
        python validate_system_readiness.py
    
    - name: Run three-day workflow test
      run: |
        cd mbti-travel-planner-agent
        python run_three_day_workflow_test.py
    
    - name: Upload test results
      uses: actions/upload-artifact@v2
      if: always()
      with:
        name: test-results
        path: mbti-travel-planner-agent/three_day_workflow_report_*.json
```

## Troubleshooting

### Debug Mode

Enable debug logging by setting the environment variable:
```bash
export PYTHONPATH=.
export LOG_LEVEL=DEBUG
python run_three_day_workflow_test.py
```

### Manual Component Testing

Test individual components:

```python
# Test JWT authentication
from services.authentication_manager import AuthenticationManager
auth_manager = AuthenticationManager()
token = await auth_manager.get_jwt_token()

# Test AgentCore client
from services.agentcore_runtime_client import AgentCoreRuntimeClient
client = AgentCoreRuntimeClient()
health = client.get_health_status()

# Test restaurant search
from services.restaurant_search_tool import RestaurantSearchTool
search_tool = RestaurantSearchTool(client, agent_arn, auth_manager)
results = await search_tool.search_restaurants_by_district(["Central district"])
```

### Log Analysis

Check log files for detailed execution information:
- `three_day_workflow_test_YYYYMMDD_HHMMSS.log` - Test execution logs
- `system_readiness_report.json` - System readiness validation results
- `three_day_workflow_report_*.json` - Detailed test results

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review the detailed test reports
3. Enable debug logging for more information
4. Validate system readiness before running tests

## Version History

- **v1.0**: Initial comprehensive test suite
- **v1.1**: Added AgentCore HTTPS + JWT communication testing
- **v1.2**: Enhanced performance benchmarking and metrics collection