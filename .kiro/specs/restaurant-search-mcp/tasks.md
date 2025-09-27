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

- [x] 4. Implement time service for meal type calculations





  - [x] 4.1 Create time parsing and validation utilities


    - Write TimeService class with time range parsing methods
    - Implement time overlap detection for meal periods
    - Create meal type validation (breakfast: 07:00-11:29, lunch: 11:30-17:29, dinner: 17:30-22:30)
    - Add support for multiple time ranges in operating hours
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

  - [x] 4.2 Write unit tests for time service


    - Test time range parsing with various formats
    - Test meal type overlap detection with sample operating hours
    - Test edge cases like midnight crossover and invalid time formats
    - Test multiple time range scenarios
    - _Requirements: 2.1, 2.2, 2.3, 2.5, 2.6_

- [x] 5. Implement data access layer for S3 restaurant files





  - [x] 5.1 Create S3-based data access client




    - Write DataAccessClient class in services/data_access.py for S3 operations
    - Implement restaurant data retrieval from S3 bucket restaurant-data-209803798463-us-east-1/restaurants/
    - Add error handling for S3 access issues, authentication failures, and missing files
    - Create JSON parsing utilities for restaurant data files from S3
    - Implement local district configuration loading from config/districts/
    - _Requirements: 3.1, 3.2, 3.3, 3.4_


  - [x] 5.2 Write unit tests for data access client

    - Test S3 data access and retrieval with mocked S3 responses
    - Test error handling for S3 authentication failures, missing files, and invalid JSON
    - Test JSON parsing with actual restaurant data structure from S3
    - Test local district configuration loading from config/districts/
    - Test malformed data handling for both S3 and local config
    - _Requirements: 3.1, 3.2, 3.3_

- [x] 6. Implement restaurant service business logic




  - [x] 6.1 Create core restaurant search functionality


    - Write RestaurantService class in services/restaurant_service.py with district and meal type search methods
    - Implement search_by_districts method using district service and data access client
    - Implement search_by_meal_types method using time service for operating hours analysis
    - Create search_combined method for filtering by both criteria
    - _Requirements: 1.1, 1.2, 1.3, 2.1, 2.2, 2.3, 6.1, 6.2, 6.3_

  - [x] 6.2 Write unit tests for restaurant service


    - Test district-based search with actual restaurant data from config/restaurants/
    - Test meal type search with various operating hours scenarios from real data
    - Test combined search with multiple criteria
    - Test error handling for invalid districts and meal types
    - _Requirements: 1.1, 1.2, 1.3, 2.1, 2.2, 2.3, 6.1, 6.2, 6.3, 6.4_

- [x] 7. Implement FastMCP server with restaurant search tools





  - [x] 7.1 Create main MCP server using FastMCP


    - Write restaurant_mcp_server.py with FastMCP(host="0.0.0.0", stateless_http=True) configuration
    - Implement @mcp.tool() decorated functions for restaurant search
    - Create search_restaurants_by_district tool with proper parameter validation
    - Add JSON response formatting for MCP tool results
    - _Requirements: 4.1, 4.2, 4.3, 8.1, 8.2_

  - [x] 7.2 Implement meal type search MCP tool


    - Create search_restaurants_by_meal_type tool with meal type validation ("breakfast", "lunch", "dinner")
    - Integrate with time service for operating hours analysis
    - Add proper error handling and response formatting
    - Implement parameter validation for meal type enum values
    - _Requirements: 4.1, 4.2, 4.3, 2.1, 2.2, 2.3_

  - [x] 7.3 Implement combined search MCP tool


    - Create search_restaurants_combined tool with optional parameters (districts=None, meal_types=None)
    - Integrate district and meal type filtering logic
    - Add comprehensive error handling and validation
    - Implement proper JSON response structure with metadata
    - _Requirements: 4.1, 4.2, 4.3, 6.1, 6.2, 6.3, 6.4_

- [x] 8. Create local testing infrastructure




  - [x] 8.1 Write local MCP client for testing


    - Create tests/test_mcp_client.py using MCP ClientSession and streamable_http transport
    - Implement tool listing and invocation testing for local FastMCP server
    - Add test cases for all three MCP tools using existing config data
    - Create helper functions for running local tests against localhost:8080
    - _Requirements: 4.1, 4.2, 4.3_

  - [x] 8.2 Create comprehensive test scenarios


    - Use existing district configuration files from config/districts/ for testing
    - Use actual restaurant data from config/restaurants/ for test scenarios
    - Write test scenarios covering various search combinations with real data
    - Add edge case test data for error handling validation
    - _Requirements: 1.1, 1.2, 2.1, 2.2, 9.1_

- [x] 9. Implement authentication setup using Amazon Cognito





  - [x] 9.1 Create Cognito user pool configuration


    - Write setup_cognito.py script using bedrock-agentcore-starter-toolkit utilities
    - Configure Cognito user pool with app client for JWT authentication
    - Create test user for authentication testing
    - Store Cognito configuration for AgentCore Runtime setup
    - _Requirements: 8.3, 8.4_

  - [x] 9.2 Write remote MCP client with authentication


    - Create tests/test_remote_client.py with JWT token authentication
    - Implement bearer token retrieval from Cognito using boto3
    - Add AgentCore Runtime URL construction and connection logic
    - Create authenticated tool invocation testing with proper headers
    - _Requirements: 4.1, 4.2, 4.3, 8.3, 8.4_

- [x] 10. Configure and deploy to Bedrock AgentCore Runtime





  - [x] 10.1 Set up AgentCore Runtime deployment configuration

    - Create deploy_agentcore.py script using bedrock-agentcore-starter-toolkit Runtime class
    - Set up JWT authorizer configuration with Cognito integration
    - Configure auto-creation of execution role and ECR repository
    - Add proper protocol="MCP" and agent_name="restaurant_search_mcp" configuration
    - _Requirements: 5.1, 5.2, 5.3, 8.1, 8.2, 8.3_

  - [x] 10.2 Deploy MCP server to AgentCore Runtime


    - Execute agentcore_runtime.configure() with entrypoint="restaurant_mcp_server.py"
    - Launch deployment using agentcore_runtime.launch()
    - Monitor deployment status until READY state
    - Store deployment configuration and test connectivity
    - _Requirements: 5.1, 5.2, 5.3, 8.1, 8.2, 8.3_

- [x] 11. Create comprehensive testing and validation


  - [x] 11.1 Write end-to-end integration tests

    - Create tests/test_integration.py that uses real local data and district configuration
    - Test complete workflow from MCP tool invocation to restaurant data retrieval
    - Validate response formats and data accuracy using actual config/restaurants/ data
    - Test error scenarios with invalid inputs and missing data
    - _Requirements: 1.1, 1.2, 1.3, 2.1, 2.2, 2.3, 3.1, 3.2, 3.3_

  - [x] 11.2 Write deployment validation tests

    - Create tests/test_deployment.py for deployed MCP server using remote client
    - Validate authentication flow with Cognito JWT tokens
    - Test all MCP tools against deployed AgentCore Runtime
    - Verify performance and response times meet requirements
    - _Requirements: 4.1, 4.2, 4.3, 8.3, 8.4_

- [x] 12. Create Docker configuration and documentation


  - [x] 12.1 Verify auto-generated Dockerfile and requirements

    - Review Dockerfile generated by AgentCore starter toolkit
    - Validate requirements.txt includes mcp>=1.10.0, boto3, bedrock-agentcore, bedrock-agentcore-starter-toolkit
    - Test local Docker build and container execution
    - Add any missing configuration or environment variables for config/ directory access
    - _Requirements: 5.1, 5.2, 5.3_

  - [x] 12.2 Write deployment and usage documentation


    - Create README.md with setup and deployment instructions
    - Document MCP tool usage and parameter specifications for all three tools
    - Add troubleshooting guide for common deployment issues
    - Create examples of MCP client usage and integration patterns
    - _Requirements: 4.1, 4.2, 4.3, 8.1, 8.2, 8.3_

- [x] 13. Implement Foundation Model Integration for Natural Language Processing





  - [x] 13.1 Create AgentCore Foundation Model configuration


    - Configure Claude 3.5 Sonnet model in AgentCore with appropriate system prompts
    - Set up model parameters optimized for restaurant search tasks (temperature, max tokens)
    - Configure tool calling capabilities to automatically invoke MCP tools
    - Add context about Hong Kong districts and restaurant search capabilities to system prompts
    - _Requirements: 10.1, 10.2, 11.1, 12.1_

  - [x] 13.2 Implement natural language query processing pipeline


    - Create query processing logic to extract districts and meal types from natural language
    - Implement intent recognition for restaurant search queries
    - Add parameter validation and district name mapping (e.g., "Central" → "Central district")
    - Create conversational response formatting for restaurant results
    - _Requirements: 9.1, 11.1, 11.2, 13.1_

  - [x] 13.3 Deploy complete conversational agent to AgentCore Runtime


    - Configure AgentCore Runtime to host both MCP server and foundation model
    - Set up proper routing between natural language processing and MCP tool calls
    - Test end-to-end conversational flow from user query to formatted response
    - Validate that users can interact using natural language like "Find breakfast places in Central district"
    - _Requirements: 12.1, 12.2, 13.1, 13.2_

- [x] 14. Implement JWT Token Management and Cognito Authentication




  - [x] 14.1 Create Cognito authentication service


    - Implement CognitoAuthenticator class in services/auth_service.py with SRP authentication
    - Create authenticate_user method using boto3 cognito-idp client with USER_SRP_AUTH flow
    - Implement token refresh functionality using refresh tokens
    - Add proper error handling for authentication failures and invalid credentials
    - _Requirements: 14.1, 14.2, 15.1, 15.2_

  - [x] 14.2 Implement JWT token validation service


    - Create TokenValidator class with comprehensive JWT validation logic
    - Implement JWKS key fetching and caching from Cognito discovery URL
    - Add token signature verification using RS256 algorithm and Cognito public keys
    - Create token claims extraction and validation (exp, iss, aud, client_id)
    - _Requirements: 14.3, 14.4, 15.3, 15.4, 17.1, 17.2_

  - [x] 14.3 Write unit tests for authentication services


    - Test SRP authentication flow with mocked Cognito responses
    - Test JWT token validation with sample tokens and JWKS keys
    - Test error handling for expired tokens, invalid signatures, and malformed tokens
    - Test JWKS key caching and refresh mechanisms
    - _Requirements: 14.1, 14.2, 15.1, 15.2, 15.3_

- [x] 15. Integrate Authentication Middleware with MCP Server





  - [x] 15.1 Create FastMCP authentication middleware


    - Implement AuthenticationMiddleware class for FastMCP server integration
    - Add JWT token extraction from Authorization Bearer headers
    - Create request authentication pipeline with token validation
    - Add user context injection into request state for authenticated requests
    - _Requirements: 14.4, 14.5, 16.4, 16.5, 17.3_

  - [x] 15.2 Update MCP server with authentication integration


    - Modify restaurant_mcp_server.py to include authentication middleware
    - Add authentication bypass for health check endpoints (/health, /metrics)
    - Implement proper error responses for authentication failures (401, 403)
    - Add user context logging for audit and debugging purposes
    - _Requirements: 14.1, 14.4, 16.4, 17.4, 18.1, 18.2_

  - [x] 15.3 Write authentication integration tests


    - Test MCP server with valid JWT tokens from Cognito
    - Test authentication failure scenarios with invalid, expired, and malformed tokens
    - Test middleware bypass for health check endpoints
    - Test user context extraction and request processing with authenticated users
    - _Requirements: 14.4, 15.5, 16.4, 17.1, 18.1_

- [-] 16. Configure AgentCore Runtime with Cognito Authentication



  - [x] 16.1 Update AgentCore deployment with JWT authorizer


    - Modify deploy_agentcore.py to include customJWTAuthorizer configuration
    - Configure allowedClients with Cognito app client ID
    - Set discoveryUrl to Cognito User Pool OpenID Connect configuration endpoint
    - Update AgentCore Runtime configuration to enforce JWT authentication
    - _Requirements: 16.1, 16.2, 16.3, 16.6_

  - [x] 16.2 Create authenticated test client for AgentCore


    - Update tests/test_remote_client.py with Cognito authentication flow
    - Implement JWT token retrieval using CognitoAuthenticator service
    - Add Bearer token headers to all AgentCore Runtime requests
    - Create test scenarios for authenticated MCP tool invocations
    - _Requirements: 16.4, 16.5, 15.5, 15.6_

  - [x] 16.3 Write end-to-end authentication tests









    - Test complete authentication flow from Cognito login to MCP tool execution
    - Validate JWT token propagation through AgentCore Runtime to MCP server
    - Test authentication error handling at both AgentCore and MCP server levels
    - Verify user context preservation throughout the request pipeline
    - _Requirements: 16.1, 16.2, 16.4, 17.1, 18.1_

- [x] 17. Implement Comprehensive Authentication Error Handling





  - [x] 17.1 Create authentication error response system


    - Implement AuthenticationErrorHandler class with standardized error responses
    - Create specific error handlers for token expiration, invalid format, and unauthorized clients
    - Add error codes and suggested actions for different authentication failure types
    - Implement user-friendly error messages with troubleshooting guidance
    - _Requirements: 18.1, 18.2, 18.3, 18.4, 18.5_

  - [x] 17.2 Add security logging and monitoring


    - Implement security event logging for authentication attempts and failures
    - Add audit logging for user context and MCP tool invocations
    - Create monitoring for suspicious authentication patterns
    - Ensure sensitive information is not logged in error messages or audit trails
    - _Requirements: 17.4, 17.5, 18.6_

  - [x] 17.3 Write security and error handling tests


    - Test all authentication error scenarios with appropriate error responses
    - Test security logging functionality without exposing sensitive data
    - Test error message clarity and troubleshooting guidance
    - Validate that authentication failures are handled gracefully without system crashes
    - _Requirements: 18.1, 18.2, 18.3, 18.4, 18.5, 18.6_

- [x] 18. Create Authentication Documentation and Usage Examples






  - [x] 18.1 Document Cognito setup and configuration


    - Create detailed guide for setting up Cognito User Pool and app client
    - Document JWT authorizer configuration for AgentCore Runtime
    - Add step-by-step authentication flow documentation
    - Include troubleshooting guide for common authentication issues
    - _Requirements: 14.1, 15.1, 16.1, 16.2, 16.3_

  - [x] 18.2 Create authentication usage examples


    - Write example code for client authentication using SRP protocol
    - Document JWT token usage patterns for MCP client integration
    - Create sample authentication flows for different client types
    - Add examples of error handling and token refresh scenarios
    - _Requirements: 15.1, 15.2, 16.4, 18.1, 18.2_




- [x] 19. Implement MCP EntryPoint Integration with BedrockAgentCoreApp




  - [x] 19.1 Create BedrockAgentCoreApp entrypoint implementation


    - Write main.py with BedrockAgentCoreApp and @app.entrypoint decorator
    - Implement payload processing to extract user prompts from AgentCore Runtime requests
    - Create Strands Agent integration with MCP tools configuration
    - Add error handling for invalid payloads and agent processing failures
    - _Requirements: 19.1, 19.2, 19.3, 19.6_

  - [x] 19.2 Configure Strands Agent with MCP tools


    - Set up Strands Agent with Claude 3.5 Sonnet model configuration
    - Configure agent with restaurant search MCP tools (search_by_district, search_by_meal_type, search_combined)
    - Add system prompts and tool descriptions for proper LLM tool selection
    - Implement tool parameter schema definitions for automatic tool calling
    - _Requirements: 19.4, 19.5, 19.10_

  - [x] 19.3 Implement entrypoint response formatting


    - Create response formatting utilities to ensure JSON-serializable outputs
    - Add conversational response integration from Strands Agent results
    - Implement error response formatting for user-friendly error messages
    - Add logging and debugging capabilities for entrypoint processing
    - _Requirements: 19.6, 19.8, 19.9_

  - [x] 19.4 Write entrypoint integration tests


    - Test payload processing with various AgentCore Runtime payload formats
    - Test Strands Agent integration and automatic MCP tool selection
    - Test response formatting and JSON serialization
    - Test error handling scenarios and graceful failure modes
    - _Requirements: 19.1, 19.2, 19.8, 19.9_

  - [x] 19.5 Update deployment configuration for entrypoint


    - Modify deploy_agentcore.py to use main.py as entrypoint instead of restaurant_mcp_server.py
    - Update .bedrock_agentcore.yaml configuration for entrypoint deployment
    - Add Strands Agent dependencies to requirements.txt
    - Test complete deployment with entrypoint integration
    - _Requirements: 19.7, 19.1_

- [x] 20. Create comprehensive README and usage examples









  - [x] 20.1 Write main project README.md


    - Create comprehensive project overview and architecture description including authentication and entrypoint integration
    - Document installation and setup instructions for BedrockAgentCoreApp entrypoint with Cognito authentication
    - Add usage examples for both MCP tools and natural language queries through entrypoint with authentication
    - Include troubleshooting section and links to detailed guides including authentication and entrypoint issues
    - _Requirements: 4.1, 4.2, 4.3, 9.1, 11.1, 14.1, 16.1, 19.1_

  - [x] 20.2 Create MCP tool usage examples and integration patterns


    - Write example code for integrating MCP tools with BedrockAgentCoreApp entrypoint including authentication
    - Document parameter formats and expected response structures for all tools through entrypoint
    - Create sample queries and expected outputs for testing and validation with entrypoint integration
    - Add examples of error handling and edge case management including authentication and entrypoint errors
    - _Requirements: 4.1, 4.2, 4.3, 6.1, 6.2, 6.3, 18.1, 18.2, 19.1, 19.6_