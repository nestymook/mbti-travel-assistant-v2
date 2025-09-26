# Implementation Plan

- [x] 1. Set up project structure and core dependencies





  - Create directory structure following AgentCore patterns (services/, models/, tests/)
  - Set up requirements.txt with mcp>=1.10.0, boto3, bedrock-agentcore, bedrock-agentcore-starter-toolkit
  - Create basic Python package structure with __init__.py files
  - _Requirements: 5.1, 8.1_

- [x] 2. Implement data models and validation




  - [x] 2.1 Create restaurant data models using dataclasses


    - Implement OperatingHours, Sentiment, RestaurantMetadata, and Restaurant models in models/restaurant_models.py
    - Create FileMetadata and RestaurantDataFile models for local JSON data structure
    - Add JSON serialization/deserialization methods using dataclasses and json
    - _Requirements: 7.1, 7.2, 7.4_

  - [x] 2.2 Create district configuration models


    - Implement DistrictConfig, RegionConfig, and MasterConfig models in models/district_models.py
    - Add validation methods for district names and configuration integrity
    - Create model conversion utilities for JSON config files in config/ directory
    - _Requirements: 9.1, 9.2, 9.5_

- [x] 3. Implement district service for configuration management




  - [x] 3.1 Create district configuration loader


    - Write DistrictService class in services/district_service.py to load config/districts/ files
    - Implement district name validation and region mapping using local config files
    - Create methods to get local file paths for districts (config/restaurants/{region}/{district}.json)
    - Add error handling for missing or invalid configuration files
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_

  - [x] 3.2 Write unit tests for district service


    - Test district configuration loading from existing config/districts/ files
    - Test district name validation with valid and invalid names from actual config
    - Test local file path generation for different districts
    - Test error handling for missing configuration files
    - _Requirements: 9.1, 9.2, 9.3_

- [ ] 4. Implement time service for meal type calculations
  - [ ] 4.1 Create time parsing and validation utilities
    - Write TimeService class with time range parsing methods
    - Implement time overlap detection for meal periods
    - Create meal type validation (breakfast: 07:00-11:29, lunch: 11:30-17:29, dinner: 17:30-22:30)
    - Add support for multiple time ranges in operating hours
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

  - [ ] 4.2 Write unit tests for time service
    - Test time range parsing with various formats
    - Test meal type overlap detection with sample operating hours
    - Test edge cases like midnight crossover and invalid time formats
    - Test multiple time range scenarios
    - _Requirements: 2.1, 2.2, 2.3, 2.5, 2.6_

- [ ] 5. Implement data access layer for local restaurant files
  - [ ] 5.1 Create local file data access client
    - Write DataAccessClient class in services/data_access.py for local file operations
    - Implement restaurant data retrieval from config/restaurants/ directory structure
    - Add error handling for file access issues and missing files
    - Create JSON parsing utilities for restaurant data files
    - _Requirements: 3.1, 3.2, 3.3, 3.4_

  - [ ] 5.2 Write unit tests for data access client
    - Test local file access and data retrieval with existing config/restaurants/ files
    - Test error handling for missing files and invalid JSON
    - Test JSON parsing with actual restaurant data from config directory
    - Test malformed data handling
    - _Requirements: 3.1, 3.2, 3.3_

- [ ] 6. Implement restaurant service business logic
  - [ ] 6.1 Create core restaurant search functionality
    - Write RestaurantService class in services/restaurant_service.py with district and meal type search methods
    - Implement search_by_districts method using district service and data access client
    - Implement search_by_meal_types method using time service for operating hours analysis
    - Create search_combined method for filtering by both criteria
    - _Requirements: 1.1, 1.2, 1.3, 2.1, 2.2, 2.3, 6.1, 6.2, 6.3_

  - [ ] 6.2 Write unit tests for restaurant service
    - Test district-based search with actual restaurant data from config/restaurants/
    - Test meal type search with various operating hours scenarios from real data
    - Test combined search with multiple criteria
    - Test error handling for invalid districts and meal types
    - _Requirements: 1.1, 1.2, 1.3, 2.1, 2.2, 2.3, 6.1, 6.2, 6.3, 6.4_

- [ ] 7. Implement FastMCP server with restaurant search tools
  - [ ] 7.1 Create main MCP server using FastMCP
    - Write restaurant_mcp_server.py with FastMCP(host="0.0.0.0", stateless_http=True) configuration
    - Implement @mcp.tool() decorated functions for restaurant search
    - Create search_restaurants_by_district tool with proper parameter validation
    - Add JSON response formatting for MCP tool results
    - _Requirements: 4.1, 4.2, 4.3, 8.1, 8.2_

  - [ ] 7.2 Implement meal type search MCP tool
    - Create search_restaurants_by_meal_type tool with meal type validation ("breakfast", "lunch", "dinner")
    - Integrate with time service for operating hours analysis
    - Add proper error handling and response formatting
    - Implement parameter validation for meal type enum values
    - _Requirements: 4.1, 4.2, 4.3, 2.1, 2.2, 2.3_

  - [ ] 7.3 Implement combined search MCP tool
    - Create search_restaurants_combined tool with optional parameters (districts=None, meal_types=None)
    - Integrate district and meal type filtering logic
    - Add comprehensive error handling and validation
    - Implement proper JSON response structure with metadata
    - _Requirements: 4.1, 4.2, 4.3, 6.1, 6.2, 6.3, 6.4_

- [ ] 8. Create local testing infrastructure
  - [ ] 8.1 Write local MCP client for testing
    - Create tests/test_mcp_client.py using MCP ClientSession and streamable_http transport
    - Implement tool listing and invocation testing for local FastMCP server
    - Add test cases for all three MCP tools using existing config data
    - Create helper functions for running local tests against localhost:8080
    - _Requirements: 4.1, 4.2, 4.3_

  - [ ] 8.2 Create comprehensive test scenarios
    - Use existing district configuration files from config/districts/ for testing
    - Use actual restaurant data from config/restaurants/ for test scenarios
    - Write test scenarios covering various search combinations with real data
    - Add edge case test data for error handling validation
    - _Requirements: 1.1, 1.2, 2.1, 2.2, 9.1_

- [ ] 9. Implement authentication setup using Amazon Cognito
  - [ ] 9.1 Create Cognito user pool configuration
    - Write setup_cognito.py script using bedrock-agentcore-starter-toolkit utilities
    - Configure Cognito user pool with app client for JWT authentication
    - Create test user for authentication testing
    - Store Cognito configuration for AgentCore Runtime setup
    - _Requirements: 8.3, 8.4_

  - [ ] 9.2 Write remote MCP client with authentication
    - Create tests/test_remote_client.py with JWT token authentication
    - Implement bearer token retrieval from Cognito using boto3
    - Add AgentCore Runtime URL construction and connection logic
    - Create authenticated tool invocation testing with proper headers
    - _Requirements: 4.1, 4.2, 4.3, 8.3, 8.4_

- [ ] 10. Configure and deploy to Bedrock AgentCore Runtime
  - [ ] 10.1 Set up AgentCore Runtime deployment configuration
    - Create deploy_agentcore.py script using bedrock-agentcore-starter-toolkit Runtime class
    - Set up JWT authorizer configuration with Cognito integration
    - Configure auto-creation of execution role and ECR repository
    - Add proper protocol="MCP" and agent_name="restaurant_search_mcp" configuration
    - _Requirements: 5.1, 5.2, 5.3, 8.1, 8.2, 8.3_

  - [ ] 10.2 Deploy MCP server to AgentCore Runtime
    - Execute agentcore_runtime.configure() with entrypoint="restaurant_mcp_server.py"
    - Launch deployment using agentcore_runtime.launch()
    - Monitor deployment status until READY state
    - Store deployment configuration and test connectivity
    - _Requirements: 5.1, 5.2, 5.3, 8.1, 8.2, 8.3_

- [ ] 11. Create comprehensive testing and validation
  - [ ] 11.1 Write end-to-end integration tests
    - Create tests/test_integration.py that uses real local data and district configuration
    - Test complete workflow from MCP tool invocation to restaurant data retrieval
    - Validate response formats and data accuracy using actual config/restaurants/ data
    - Test error scenarios with invalid inputs and missing data
    - _Requirements: 1.1, 1.2, 1.3, 2.1, 2.2, 2.3, 3.1, 3.2, 3.3_

  - [ ] 11.2 Write deployment validation tests
    - Create tests/test_deployment.py for deployed MCP server using remote client
    - Validate authentication flow with Cognito JWT tokens
    - Test all MCP tools against deployed AgentCore Runtime
    - Verify performance and response times meet requirements
    - _Requirements: 4.1, 4.2, 4.3, 8.3, 8.4_

- [ ] 12. Create Docker configuration and documentation
  - [ ] 12.1 Verify auto-generated Dockerfile and requirements
    - Review Dockerfile generated by AgentCore starter toolkit
    - Validate requirements.txt includes mcp>=1.10.0, boto3, bedrock-agentcore, bedrock-agentcore-starter-toolkit
    - Test local Docker build and container execution
    - Add any missing configuration or environment variables for config/ directory access
    - _Requirements: 5.1, 5.2, 5.3_

  - [ ] 12.2 Write deployment and usage documentation
    - Create README.md with setup and deployment instructions
    - Document MCP tool usage and parameter specifications for all three tools
    - Add troubleshooting guide for common deployment issues
    - Create examples of MCP client usage and integration patterns
    - _Requirements: 4.1, 4.2, 4.3, 8.1, 8.2, 8.3_