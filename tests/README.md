# Restaurant Search MCP Server - Testing Infrastructure

This directory contains comprehensive testing infrastructure for the Restaurant Search MCP Server, including local MCP client testing, comprehensive scenario validation, test data generation, and AWS deployment testing.

## Directory Structure (Following Program Guidelines)

### `/tests/payload/`
Base64 encoded test payloads:
- `mcp_initialize_request.b64` - MCP initialization request
- `mcp_tools_list_request.b64` - MCP tools list request  
- `district_search_prompt.b64` - District search prompt
- `meal_type_search_prompt.b64` - Meal type search prompt
- `combined_search_prompt.b64` - Combined search prompt
- `general_conversation_prompt.b64` - General conversation prompt

### `/tests/request/`
JSON request files (human-readable versions):
- `mcp_initialize_request.json` - MCP initialization request
- `mcp_tools_list_request.json` - MCP tools list request
- `district_search_prompt.json` - District search prompt
- `meal_type_search_prompt.json` - Meal type search prompt
- `combined_search_prompt.json` - Combined search prompt
- `general_conversation_prompt.json` - General conversation prompt

### `/tests/response/`
Test response files (generated during test execution):
- `mcp_initialize_response.json` - MCP initialization response
- `mcp_tools_list_response.json` - MCP tools list response
- `district_search_response.json` - District search response
- `meal_type_search_response.json` - Meal type search response
- `combined_search_response.json` - Combined search response
- `general_conversation_response.json` - General conversation response

### `/tests/results/`
Test execution results and summaries:
- `authenticated_mcp_test_results.json` - Authenticated MCP test results
- `toolkit_test_results.json` - Toolkit test results
- `mcp_deployment_test_results.json` - Deployment test results

## Overview

The testing infrastructure validates all MCP tools and requirements using real configuration data from the `config/` directory and generated test scenarios for edge cases.

## Test Components

### AWS Deployment Tests

#### 1. Authenticated MCP Tests (`test_authenticated_mcp.py`)
Tests for the deployed authenticated MCP server in AWS:
- AgentCore invoke command testing
- AWS CLI bedrock-agentcore invoke testing
- Comprehensive restaurant search scenarios
- Response validation and error handling
- Results saved to `/tests/results/authenticated_mcp_test_results.json`

#### 2. Toolkit Tests (`test_mcp_with_toolkit.py`)
Tests using bedrock-agentcore-starter-toolkit:
- Runtime status checking
- Agent invocation testing
- Toolkit integration validation
- Results saved to `/tests/results/toolkit_test_results.json`

#### 3. Deployment Tests (`test_mcp_deployment.py`)
Basic MCP deployment validation:
- MCP initialization testing
- Tools list validation
- No-auth agent testing
- Results saved to `/tests/results/mcp_deployment_test_results.json`

### Local Development Tests

#### 4. Local MCP Client (`test_mcp_client.py`)

Basic MCP client for testing server connectivity and tool functionality.

**Features:**
- Connection testing to local MCP server
- Tool listing and schema validation
- Basic tool invocation testing
- Error handling validation
- Response format validation

**Usage:**
```bash
# Run basic MCP client tests
python tests/test_mcp_client.py [server_url]

# Default server URL is http://localhost:8080
python tests/test_mcp_client.py
```

#### 5. Comprehensive Test Scenarios (`test_scenarios.py`)

Advanced test scenarios using real config data and edge cases.

**Features:**
- District search scenarios using actual district configuration
- Meal type search scenarios with various operating hours patterns
- Combined search scenarios with multiple criteria
- Edge case testing for error handling
- Validation against specific requirements

**Test Categories:**
- **District Search Tests**: Valid/invalid districts, multiple districts, case sensitivity
- **Meal Type Search Tests**: Breakfast/lunch/dinner periods, boundary conditions, invalid types
- **Combined Search Tests**: Mixed criteria, parameter validation, complex scenarios
- **Edge Case Tests**: Unicode handling, performance testing, boundary conditions

**Usage:**
```bash
# Run comprehensive scenario tests
python tests/test_scenarios.py [server_url]

# Show scenario summary
python -c "from tests.test_scenarios import ComprehensiveTestScenarios; ComprehensiveTestScenarios().print_scenario_summary()"
```

#### 6. Test Data Generator (`test_data_generator.py`)

Generates test data for edge cases and error handling validation.

**Features:**
- Restaurants with specific operating hours patterns
- Boundary condition test cases
- Invalid data scenarios
- Edge case scenario generation

**Generated Test Data:**
- **Breakfast District**: Restaurants only open for breakfast
- **Lunch District**: Restaurants only open for lunch  
- **Dinner District**: Restaurants only open for dinner
- **Mixed District**: Restaurants with various meal time patterns
- **Problem District**: Restaurants with invalid/problematic data

**Usage:**
```bash
# Generate test data
python tests/test_data_generator.py

# Output will be in tests/test_data/ directory
```

#### 7. Test Runner (`run_local_tests.py`)

Unified test runner that executes all test suites.

**Features:**
- Runs all test categories in sequence
- Provides comprehensive result summary
- Shows configuration information
- Handles test failures gracefully

**Usage:**
```bash
# Run all tests
python tests/run_local_tests.py [server_url]

# Show help and test information
python tests/run_local_tests.py --help
```

## Test Configuration

### Prerequisites

1. **MCP Server Running**: The restaurant MCP server must be running locally
   ```bash
   python restaurant_mcp_server.py
   ```

2. **Configuration Data**: Config data must be available in `config/` directory
   - `config/districts/`: District configuration files
   - `config/restaurants/`: Restaurant data files by region

3. **Dependencies**: Required Python packages
   ```bash
   pip install mcp
   ```

### Configuration Files Used

The tests use real configuration data:

- **Master Config**: `config/districts/master-config.json`
- **Regional Configs**: `config/districts/{region}.json`
- **Restaurant Data**: `config/restaurants/{region}/{district}.json`

## Test Scenarios

### District Search Tests

Tests the `search_restaurants_by_district` tool:

- ✅ Single valid district
- ✅ Multiple valid districts from same region
- ✅ Multiple districts across regions
- ❌ Invalid district names
- ❌ Empty districts list
- ❌ Invalid parameter types

### Meal Type Search Tests

Tests the `search_restaurants_by_meal_type` tool:

- ✅ Individual meal types (breakfast, lunch, dinner)
- ✅ Multiple meal types
- ✅ Case insensitive meal types
- ❌ Invalid meal types (brunch, snack)
- ❌ Empty meal types list
- ❌ Invalid parameter types

### Combined Search Tests

Tests the `search_restaurants_combined` tool:

- ✅ Districts only
- ✅ Meal types only
- ✅ Both districts and meal types
- ❌ No parameters provided
- ❌ Empty parameter lists
- ❌ Invalid combinations

### Edge Case Tests

Special scenarios for boundary conditions:

- Unicode district names
- Case sensitivity testing
- Performance with large parameter lists
- Meal time boundary conditions (11:29/11:30, 17:29/17:30)
- Invalid operating hours formats

## Requirements Coverage

The tests validate all requirements from the specification:

### Requirement 1 (District Search)
- 1.1: District search functionality ✅
- 1.2: Invalid district handling ✅
- 1.3: Multiple district support ✅

### Requirement 2 (Meal Type Search)
- 2.1: Breakfast period (07:00-11:29) ✅
- 2.2: Lunch period (11:30-17:29) ✅
- 2.3: Dinner period (17:30-22:30) ✅
- 2.4: Operating hours analysis ✅
- 2.5: Multiple time ranges ✅
- 2.6: Multiple meal periods ✅
- 2.7: Invalid data handling ✅

### Requirement 4 (MCP Tools)
- 4.1: MCP tool exposure ✅
- 4.2: Tool parameter processing ✅
- 4.3: Error handling ✅

### Requirement 6 (Combined Search)
- 6.1: Both criteria matching ✅
- 6.2: Districts only ✅
- 6.3: Meal types only ✅
- 6.4: Parameter validation ✅

### Requirement 9 (District Configuration)
- 9.1: Master config loading ✅
- 9.2: Regional config loading ✅
- 9.4: Missing config handling ✅
- 9.5: District validation ✅

## Running Tests

### AWS Deployment Tests

Test the deployed authenticated MCP server:
```bash
# Test authenticated MCP server
python tests/test_authenticated_mcp.py

# Test with toolkit
python tests/test_mcp_with_toolkit.py

# Test basic deployment
python tests/test_mcp_deployment.py
```

### Local Development Tests

#### Quick Start

1. Start the MCP server:
   ```bash
   python restaurant_mcp_server.py
   ```

2. Run all local tests:
   ```bash
   python tests/run_local_tests.py
   ```

### Individual Test Suites

```bash
# Basic MCP client tests only
python tests/test_mcp_client.py

# Comprehensive scenarios only
python tests/test_scenarios.py

# Generate test data
python tests/test_data_generator.py
```

### Custom Server URL

```bash
# Test against different server
python tests/run_local_tests.py http://localhost:9000
```

## Test Output

### Success Output
```
🏆 OVERALL RESULT
----------------------------------------
✅ ALL TESTS PASSED! MCP server is working correctly.
```

### Failure Output
```
🏆 OVERALL RESULT
----------------------------------------
❌ SOME TESTS FAILED! Check the details above.
Failed test categories: Basic MCP client tests, Comprehensive scenario tests
```

## Troubleshooting

### Common Issues

1. **Connection Failed**
   - Ensure MCP server is running: `python restaurant_mcp_server.py`
   - Check server URL and port
   - Verify no firewall blocking

2. **Config Data Missing**
   - Ensure `config/districts/` directory exists
   - Ensure `config/restaurants/` directory has data files
   - Check file permissions

3. **Tool Not Found**
   - Verify MCP server started successfully
   - Check server logs for errors
   - Ensure all dependencies installed

4. **Test Failures**
   - Check server logs for errors
   - Verify config data integrity
   - Run individual test suites to isolate issues

### Debug Mode

Enable debug logging:
```bash
export PYTHONPATH=.
python -c "
import logging
logging.basicConfig(level=logging.DEBUG)
import asyncio
from tests.run_local_tests import run_all_tests
asyncio.run(run_all_tests())
"
```

## Contributing

When adding new tests:

1. Follow the existing test pattern structure
2. Include requirement references in test scenarios
3. Add both positive and negative test cases
4. Update this README with new test categories
5. Ensure tests use real config data when possible

## Program Guidelines Compliance

All test files follow the established program guidelines:
- ✅ Test payloads are base64 encoded in `/tests/payload/`
- ✅ Test requests are stored in `/tests/request/`
- ✅ Test responses are saved to `/tests/response/`
- ✅ Test results are saved to `/tests/results/`

## Files

### AWS Deployment Tests
- `test_authenticated_mcp.py` - Authenticated MCP server testing
- `test_mcp_with_toolkit.py` - Toolkit integration testing
- `test_mcp_deployment.py` - Basic deployment testing

### Local Development Tests
- `test_mcp_client.py` - Basic MCP client testing
- `test_scenarios.py` - Comprehensive scenario testing
- `test_data_generator.py` - Test data generation
- `run_local_tests.py` - Unified test runner

### Service Tests
- `test_restaurant_service.py` - Restaurant service unit tests
- `test_district_service.py` - District service unit tests
- `test_time_service.py` - Time service unit tests

### Integration Tests
- `test_system_integration.py` - System integration tests
- `test_conversational_flow.py` - Conversational flow tests

### Documentation
- `README.md` - This documentation

### Generated Directories
- `payload/` - Base64 encoded test payloads
- `request/` - JSON request files
- `response/` - Test response files (generated)
- `results/` - Test execution results (generated)
- `test_data/` - Generated test data (created by generator)