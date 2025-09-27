# Implementation Plan

- [ ] 1. Set up new project structure and core dependencies for reasoning MCP
  - Create new directory structure for restaurant reasoning MCP server (separate from existing search server)
  - Set up new requirements.txt with mcp>=1.10.0, bedrock-agentcore, bedrock-agentcore-starter-toolkit, pydantic>=2.0.0
  - Create new Python package structure with __init__.py files for reasoning functionality
  - Initialize new models/, services/, and tests/ directories for reasoning components
  - _Requirements: 5.1, 7.1_

- [ ] 2. Implement data models for sentiment analysis and recommendations
  - [ ] 2.1 Create new sentiment analysis data models using dataclasses
    - Create new models/restaurant_models.py with Sentiment, Restaurant, and RecommendationResult models
    - Add sentiment calculation methods (likes_percentage, combined_positive_percentage) to Sentiment class
    - Create RecommendationResult model for structured recommendation responses with candidates and recommendation
    - Add JSON serialization/deserialization methods for all reasoning models
    - _Requirements: 1.1, 1.9, 1.10, 6.1_

  - [ ] 2.2 Create new validation and configuration models
    - Create new models/validation_models.py with ValidationResult, ValidationError, and ReasoningConfig models
    - Create new models/auth_models.py with authentication models (CognitoConfig, JWTClaims, UserContext) 
    - Create model conversion utilities for configuration management
    - Add error handling models for reasoning-specific errors
    - _Requirements: 2.7, 2.8, 11.1, 12.1_

- [ ] 3. Implement sentiment analysis service
  - [ ] 3.1 Create core sentiment analysis functionality
    - Write services/sentiment_service.py with SentimentAnalysisService class
    - Implement calculate_sentiment_score and calculate_combined_score methods
    - Create sentiment percentage calculations and validation logic
    - Add error handling for invalid sentiment data
    - _Requirements: 1.1, 1.3, 1.4, 1.9_

  - [ ] 3.2 Write unit tests for sentiment analysis service
    - Create tests/test_sentiment_service.py with comprehensive test coverage
    - Test sentiment score calculations with various data sets
    - Test percentage calculations for likes and combined sentiment
    - Test edge cases (zero responses, negative values, missing data)
    - _Requirements: 1.1, 1.3, 1.4, 1.9_

- [ ] 4. Implement recommendation algorithm service
  - [ ] 4.1 Create restaurant ranking algorithms
    - Write services/recommendation_service.py with RecommendationAlgorithm class
    - Implement rank_by_likes method for sentiment likes ranking
    - Implement rank_by_combined_sentiment method for combined sentiment ranking
    - Create candidate selection and random recommendation logic
    - _Requirements: 1.2, 1.3, 1.5, 1.6_

  - [ ] 4.2 Write unit tests for recommendation algorithms
    - Create tests/test_recommendation_service.py with comprehensive test coverage
    - Test ranking consistency with different restaurant data sets
    - Test tie-breaking logic in ranking algorithms
    - Test candidate selection with various list sizes (less than 20, exactly 20, more than 20)
    - Test random recommendation selection and reproducibility with seeds
    - _Requirements: 1.2, 1.3, 1.5, 1.6, 1.8_

- [ ] 5. Implement data validation service
  - [ ] 5.1 Create restaurant data validator
    - Write services/validation_service.py with RestaurantDataValidator class
    - Implement validate_restaurant_structure method for required fields validation
    - Create validate_sentiment_structure method for sentiment data validation
    - Add sanitization and error reporting functionality
    - _Requirements: 1.9, 2.7, 2.8, 3.3_

  - [ ] 5.2 Write unit tests for data validation
    - Create tests/test_validation_service.py with comprehensive test coverage
    - Test validation with valid and invalid restaurant data structures
    - Test sentiment data validation with missing fields and invalid types
    - Test error reporting and validation result formatting
    - _Requirements: 1.9, 2.7, 2.8, 3.3_

- [ ] 6. Implement restaurant reasoning service business logic
  - [ ] 6.1 Create core restaurant reasoning functionality
    - Write services/restaurant_reasoning_service.py with RestaurantReasoningService class
    - Implement analyze_and_recommend method integrating validation, analysis, and recommendation
    - Create response formatting utilities for structured recommendation results
    - Add comprehensive error handling and logging
    - _Requirements: 1.1, 1.2, 1.6, 1.7, 2.1_

  - [ ] 6.2 Write unit tests for restaurant reasoning service
    - Create tests/test_restaurant_reasoning_service.py with comprehensive test coverage
    - Test end-to-end reasoning workflow with sample restaurant data
    - Test both ranking methods (sentiment_likes and combined_sentiment)
    - Test error handling for invalid data and edge cases
    - _Requirements: 1.1, 1.2, 1.6, 1.7, 2.1_

- [ ] 7. Create new FastMCP server with reasoning tools
  - [ ] 7.1 Create new main MCP server for restaurant reasoning
    - Create new restaurant_reasoning_mcp_server.py with FastMCP(host="0.0.0.0", stateless_http=True) configuration
    - Implement @mcp.tool() decorated functions for recommend_restaurants and analyze_restaurant_sentiment
    - Add proper parameter validation for restaurant data input (list of restaurant objects with sentiment)
    - Create JSON response formatting for MCP reasoning tool results
    - _Requirements: 2.1, 2.2, 4.1, 4.2, 7.1_

  - [ ] 7.2 Implement sentiment analysis MCP tool
    - Create analyze_restaurant_sentiment tool for analysis without recommendation
    - Integrate with sentiment analysis service for data processing
    - Add proper error handling and response formatting for sentiment analysis
    - Implement parameter validation for restaurant data structure with sentiment fields
    - _Requirements: 2.1, 2.2, 4.1, 4.2_

  - [ ] 7.3 Create new MCP tool tests
    - Create new tests/test_reasoning_mcp_tools.py for reasoning functionality
    - Test MCP tool registration and parameter validation for reasoning tools
    - Test tool execution with valid and invalid restaurant data with sentiment
    - Test response formatting and JSON serialization for recommendations
    - _Requirements: 2.1, 2.2, 4.1, 4.2_

- [ ] 8. Create new testing infrastructure for reasoning
  - [ ] 8.1 Create new MCP client tests for reasoning tools
    - Create new tests/test_reasoning_mcp_client.py using MCP ClientSession and streamable_http transport
    - Implement tool listing and invocation testing for new reasoning MCP server
    - Add test cases for reasoning tools using sample restaurant data with sentiment
    - Create helper functions for testing recommendation logic and sentiment analysis
    - _Requirements: 4.1, 4.2_

  - [ ] 8.2 Create comprehensive reasoning test scenarios
    - Create new sample restaurant data with various sentiment scenarios for testing
    - Write test scenarios covering different ranking methods (sentiment_likes vs combined_sentiment) and data sizes
    - Add edge case test data for error handling validation (missing sentiment, invalid data)
    - Create performance test data with large restaurant lists for reasoning operations
    - _Requirements: 1.1, 1.2, 2.1, 2.2_

- [ ] 9. Reuse existing authentication setup for reasoning MCP server
  - [ ] 9.1 Copy existing Cognito configuration for reasoning server
    - Copy existing cognito_config.json and setup_cognito.py for reasoning MCP server
    - Reuse existing Cognito user pool and app client for JWT authentication
    - Use existing test user for reasoning server authentication testing
    - Adapt existing Cognito configuration for reasoning server AgentCore Runtime setup
    - _Requirements: 11.1, 11.2, 7.1_

  - [ ] 9.2 Create new remote MCP client with existing authentication for reasoning
    - Create new tests/test_reasoning_remote_client.py using existing JWT token authentication
    - Reuse existing bearer token retrieval from Cognito using boto3 for reasoning server
    - Add AgentCore Runtime URL construction and connection logic for reasoning server
    - Create authenticated tool invocation testing for reasoning tools with existing auth setup
    - _Requirements: 4.1, 4.2, 11.1, 11.2_

- [ ] 10. Configure and deploy new reasoning MCP server to Bedrock AgentCore Runtime
  - [ ] 10.1 Set up new AgentCore Runtime deployment configuration for reasoning server
    - Create new deploy_reasoning_agentcore.py script using bedrock-agentcore-starter-toolkit Runtime class
    - Set up JWT authorizer configuration with existing Cognito integration for reasoning server
    - Configure auto-creation of execution role and ECR repository for reasoning server
    - Add proper protocol="MCP" and agent_name="restaurant_reasoning_mcp" configuration
    - _Requirements: 5.1, 5.2, 7.1, 11.1, 13.1_

  - [ ] 10.2 Deploy new reasoning MCP server to AgentCore Runtime
    - Execute agentcore_runtime.configure() with entrypoint="restaurant_reasoning_mcp_server.py"
    - Launch deployment using agentcore_runtime.launch() for reasoning server
    - Monitor deployment status until READY state for reasoning server
    - Store deployment configuration and test connectivity for reasoning functionality
    - _Requirements: 5.1, 5.2, 7.1, 11.1_

- [ ] 11. Copy existing JWT Token Management and Cognito Authentication for reasoning server
  - [ ] 11.1 Copy existing Cognito authentication service for reasoning server
    - Copy existing services/auth_service.py with CognitoAuthenticator class with SRP authentication
    - Reuse existing authenticate_user method using boto3 cognito-idp client with USER_SRP_AUTH flow
    - Reuse existing token refresh functionality using refresh tokens for reasoning server
    - Adapt existing error handling for authentication failures and invalid credentials
    - _Requirements: 11.1, 11.2, 12.1, 12.2_

  - [ ] 11.2 Copy existing JWT token validation service for reasoning server
    - Copy existing TokenValidator class with comprehensive JWT validation logic
    - Reuse existing JWKS key fetching and caching from Cognito discovery URL for reasoning server
    - Reuse existing token signature verification using RS256 algorithm and Cognito public keys
    - Reuse existing token claims extraction and validation (exp, iss, aud, client_id) for reasoning server
    - _Requirements: 11.3, 11.4, 12.3, 12.4, 14.1, 14.2_

  - [ ] 11.3 Adapt existing unit tests for authentication services
    - Copy and adapt existing authentication tests for reasoning server context
    - Test SRP authentication flow with existing Cognito setup for reasoning server
    - Test JWT token validation with existing tokens and JWKS keys for reasoning server
    - Test error handling for expired tokens, invalid signatures, and malformed tokens
    - _Requirements: 11.1, 11.2, 12.1, 12.2, 12.3_

- [ ] 12. Copy existing Authentication Middleware for reasoning MCP Server
  - [ ] 12.1 Copy existing FastMCP authentication middleware for reasoning server
    - Copy existing services/auth_middleware.py with AuthenticationMiddleware class for FastMCP server integration
    - Reuse existing JWT token extraction from Authorization Bearer headers for reasoning server
    - Reuse existing request authentication pipeline with token validation for reasoning server
    - Adapt existing user context injection into request state for authenticated reasoning requests
    - _Requirements: 11.4, 11.5, 13.4, 13.5, 14.3_

  - [ ] 12.2 Create new reasoning MCP server with existing authentication integration
    - Create new restaurant_reasoning_mcp_server.py using existing authentication middleware
    - Add authentication bypass for health check endpoints (/health, /metrics) for reasoning server
    - Implement proper error responses for authentication failures (401, 403) in reasoning server
    - Add user context logging for audit and debugging purposes for reasoning operations
    - _Requirements: 11.1, 11.4, 13.4, 14.4, 15.1, 15.2_

  - [ ] 12.3 Adapt existing authentication integration tests for reasoning server
    - Copy and adapt existing authentication integration tests for reasoning server context
    - Test reasoning MCP server with valid JWT tokens from existing Cognito setup
    - Test authentication failure scenarios with invalid, expired, and malformed tokens for reasoning server
    - Test middleware bypass for health check endpoints in reasoning server
    - _Requirements: 11.4, 12.5, 13.4, 14.1, 15.1_

- [ ] 13. Configure new AgentCore Runtime with existing Cognito Authentication for reasoning server
  - [ ] 13.1 Create new AgentCore deployment with existing JWT authorizer for reasoning server
    - Create new deploy_reasoning_agentcore.py using existing customJWTAuthorizer configuration
    - Configure allowedClients with existing Cognito app client ID for reasoning server
    - Set discoveryUrl to existing Cognito User Pool OpenID Connect configuration endpoint
    - Update AgentCore Runtime configuration to enforce JWT authentication for reasoning server
    - _Requirements: 13.1, 13.2, 13.3, 13.6_

  - [ ] 13.2 Create new authenticated test client for reasoning AgentCore
    - Create new tests/test_reasoning_remote_client.py using existing Cognito authentication flow
    - Implement JWT token retrieval using existing CognitoAuthenticator service for reasoning server
    - Add Bearer token headers to all reasoning AgentCore Runtime requests
    - Create test scenarios for authenticated reasoning MCP tool invocations
    - _Requirements: 13.4, 13.5, 12.5, 12.6_

  - [ ] 13.3 Write new end-to-end authentication tests for reasoning server
    - Create new tests/test_reasoning_e2e_auth.py with comprehensive test coverage
    - Test complete authentication flow from existing Cognito login to reasoning MCP tool execution
    - Validate JWT token propagation through AgentCore Runtime to reasoning MCP server
    - Test authentication error handling at both AgentCore and reasoning MCP server levels
    - _Requirements: 13.1, 13.2, 13.4, 14.1, 15.1_

- [ ] 14. Copy existing Comprehensive Authentication Error Handling for reasoning server
  - [ ] 14.1 Copy existing authentication error response system for reasoning server
    - Copy existing services/auth_error_handler.py with AuthenticationErrorHandler class with standardized error responses
    - Reuse existing error handlers for token expiration, invalid format, and unauthorized clients for reasoning server
    - Adapt existing error codes and suggested actions for different authentication failure types in reasoning context
    - Reuse existing user-friendly error messages with troubleshooting guidance for reasoning server
    - _Requirements: 15.1, 15.2, 15.3, 15.4, 15.5_

  - [ ] 14.2 Copy existing security logging and monitoring for reasoning server
    - Copy existing services/security_monitor.py for security event logging for authentication attempts and failures
    - Add audit logging for user context and reasoning MCP tool invocations
    - Reuse existing monitoring for suspicious authentication patterns in reasoning server
    - Ensure sensitive information is not logged in error messages or audit trails for reasoning operations
    - _Requirements: 14.4, 14.5, 15.6_

  - [ ] 14.3 Adapt existing security and error handling tests for reasoning server
    - Copy and adapt existing security tests for reasoning server context
    - Test all authentication error scenarios with appropriate error responses for reasoning server
    - Test security logging functionality without exposing sensitive data for reasoning operations
    - Test error message clarity and troubleshooting guidance for reasoning server
    - _Requirements: 15.1, 15.2, 15.3, 15.4, 15.5, 15.6_

- [ ] 15. Create new EntryPoint Integration for Restaurant Reasoning
  - [ ] 15.1 Create new BedrockAgentCoreApp entrypoint for reasoning
    - Create new main.py with BedrockAgentCoreApp and @app.entrypoint decorator for reasoning functionality
    - Implement payload processing to extract user prompts and restaurant data from AgentCore Runtime requests
    - Create Strands Agent integration with reasoning MCP tools (recommend_restaurants, analyze_restaurant_sentiment)
    - Add error handling for invalid restaurant data payloads and reasoning-specific errors
    - _Requirements: 16.1, 16.2, 16.3, 16.6_

  - [ ] 15.2 Configure new Strands Agent with reasoning tools
    - Set up Strands Agent with Claude 3.5 Sonnet model configuration for reasoning tasks
    - Configure agent with restaurant reasoning MCP tools and proper tool descriptions
    - Add system prompts focused on sentiment analysis and recommendation logic
    - Implement tool parameter schema definitions for restaurant data input with sentiment
    - _Requirements: 16.4, 16.5, 16.10_

  - [ ] 15.3 Create new entrypoint response formatting for reasoning
    - Create response formatting utilities for recommendation results and sentiment analysis
    - Add conversational response integration for reasoning results
    - Implement error response formatting for reasoning-specific errors
    - Add logging and debugging capabilities for reasoning tool invocations
    - _Requirements: 16.6, 16.8, 16.9_

  - [ ] 15.4 Write new entrypoint reasoning integration tests
    - Create new tests/test_reasoning_entrypoint.py for reasoning functionality
    - Test payload processing with restaurant data for reasoning operations
    - Test Strands Agent integration with reasoning tools
    - Test response formatting for recommendation results and error handling
    - _Requirements: 16.1, 16.2, 16.8, 16.9_

- [ ] 16. Create comprehensive testing and validation for new reasoning server
  - [ ] 16.1 Write new end-to-end reasoning integration tests
    - Create new tests/test_reasoning_integration.py with sample restaurant data with sentiment information
    - Test complete workflow from reasoning MCP tool invocation to recommendation generation
    - Validate response formats and recommendation accuracy using test data with sentiment analysis
    - Test error scenarios with invalid inputs and missing sentiment data for reasoning operations
    - _Requirements: 1.1, 1.2, 1.6, 1.7, 2.1, 2.2_

  - [ ] 16.2 Write new deployment validation tests for reasoning server
    - Create new tests/test_reasoning_deployment.py for reasoning MCP server functionality
    - Validate authentication flow with Cognito JWT tokens for reasoning tools
    - Test all reasoning MCP tools against deployed AgentCore Runtime
    - Verify performance and response times meet requirements for reasoning operations
    - _Requirements: 4.1, 4.2, 11.1, 11.2_

- [ ] 17. Create new Docker configuration and documentation for reasoning server
  - [ ] 17.1 Create new Dockerfile and requirements for reasoning server
    - Create new Dockerfile for reasoning server with ARM64 compatibility
    - Create new requirements.txt with mcp>=1.10.0, bedrock-agentcore, bedrock-agentcore-starter-toolkit, pydantic>=2.0.0
    - Test local Docker build and container execution for reasoning server
    - Add any missing configuration or environment variables for reasoning functionality
    - _Requirements: 5.1, 5.2, 5.3_

  - [ ] 17.2 Write new deployment and usage documentation for reasoning server
    - Create new README.md with setup and deployment instructions for reasoning server
    - Document reasoning MCP tool usage and parameter specifications (restaurant data input)
    - Add troubleshooting guide for common deployment issues with reasoning server
    - Create examples of reasoning MCP client usage and integration patterns
    - _Requirements: 4.1, 4.2, 7.1, 11.1_

- [ ] 18. Adapt existing authentication documentation for reasoning server
  - [ ] 18.1 Adapt existing Cognito setup and configuration documentation for reasoning server
    - Copy and adapt existing detailed guide for Cognito User Pool and app client for reasoning server
    - Document JWT authorizer configuration for reasoning server AgentCore Runtime using existing setup
    - Add step-by-step authentication flow documentation for reasoning server using existing auth
    - Include troubleshooting guide for common authentication issues with reasoning server
    - _Requirements: 11.1, 12.1, 13.1, 13.2, 13.3_

  - [ ] 18.2 Adapt existing authentication usage examples for reasoning server
    - Copy and adapt existing example code for client authentication using SRP protocol for reasoning server
    - Document JWT token usage patterns for reasoning MCP client integration using existing auth
    - Create sample authentication flows for different client types with reasoning server
    - Add examples of error handling and token refresh scenarios for reasoning operations
    - _Requirements: 12.1, 12.2, 13.4, 15.1, 15.2_

- [ ] 19. Create comprehensive README and usage examples for new reasoning server
  - [ ] 19.1 Create main project README.md for reasoning functionality
    - Create comprehensive project overview focused on restaurant sentiment analysis and recommendation
    - Document installation and setup instructions for new reasoning MCP server
    - Add usage examples for reasoning tools and natural language queries with restaurant data
    - Include troubleshooting section for reasoning-specific issues and deployment
    - _Requirements: 4.1, 4.2, 9.1, 11.1, 13.1, 16.1_

  - [ ] 19.2 Create reasoning tool usage examples and integration patterns
    - Write example code for integrating reasoning MCP tools with new BedrockAgentCoreApp entrypoint
    - Document parameter formats for restaurant data input and expected recommendation response structures
    - Create sample queries and expected outputs for reasoning testing and validation
    - Add examples of error handling for reasoning-specific edge cases and sentiment analysis errors
    - _Requirements: 4.1, 4.2, 2.1, 2.2, 15.1, 15.2, 16.1, 16.6_