# Implementation Plan

- [x] 1. Add get_connection_config method to EnvironmentConfig class










  - Import ConnectionConfig with lazy loading to avoid circular dependencies
  - Create method that maps environment configuration to ConnectionConfig parameters
  - Use agentcore.timeout_seconds for timeout_seconds parameter
  - Use performance.max_connections for max_connections parameter
  - Use performance.max_connections_per_host for max_connections_per_host parameter
  - Set keepalive_timeout to 30 seconds as reasonable default
  - Set enable_cleanup_closed to True as recommended setting
  - _Requirements: 1.1, 1.2, 1.3, 2.1, 2.2, 2.3_


- [x] 2. Implement configuration validation and error handling











- [ ] 2. Implement configuration validation and error handling
  - Add validation for timeout_seconds to ensure it's between 1-300 seconds
  - Add validation for max_connections to ensure it's positive
  - Add validation for max_connections_per_host to ensure it's positive and not greater than max_connections
  - Create clear error messages for each validation failure
  - Handle ImportError for ConnectionConfig
 import gracefully
  - _Requirements: 1.4, 4.1, 4.2, 4.3, 4.4_

- [x] 3. Add logging and debugging support





  - Add DEBUG level logging when connection config is created successfully
  - Log the configuration values being used (timeout, max_connections, max_connections_per_host)
  - Add ERROR level logging for validation failures
  - Use structured logging format for better observability
  - _Requirements: 4.5, 1.5_

- [ ]* 4. Create unit tests for get_connection_config method
  - Test successful creation of ConnectionConfig with valid environment configuration
  - Test validation error handling for invalid timeout values (0, negative, > 300)
  - Test validation error handling for invalid connection pool settings
  - Test that returned ConnectionConfig has expected values from environment config
  - Test ImportError handling when ConnectionConfig cannot be imported
  - Test logging output for both success and error cases
  - _Requirements: All requirements for validation_

- [ ]* 5. Create integration tests for health check service
  - Test that AgentCoreHealthCheckService initializes successfully after the fix
  - Test that health checks for restaurant_search agent work without configuration errors
  - Test that health checks for restaurant_reasoning agent work without configuration errors
  - Test that background health checks run 

successfully
  - Test that health check results are properly returned
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [x] 6. Verify backward compatibility and existing functionality






  - Verify that existing EnvironmentConfig methods continue to work unchanged
  - Verify that other AgentCoreRuntimeClient instances in the system continue to work
  - Verify that configuration loading for all environments works properly
  - Test that existing error handling and validation remains functional
  - Ensure no impact on other services using environment configuration
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [x] 7. Fix AgentCore execution role IAM permissions for GetAgentRuntime access
  - Identify the AgentCore execution role: AmazonBedrockAgentCoreSDKRuntime-us-east-1-849e62e6e2
  - Create IAM policy with bedrock-agentcore:GetAgentRuntime permission for resource arn:aws:bedrock-agentcore:us-east-1:209803798463:runtime/restaurant_search_agent-mN8bgq2Y1j
  - Add bedrock-agentcore:ListAgentRuntimes permission for general runtime listing
  - Add bedrock-agentcore:DescribeAgentRuntime permission for detailed runtime information
  - Create script to apply the IAM policy to the AgentCore execution role
  - Test that health check service can successfully call GetAgentRuntime without AccessDeniedException
  - Verify that the assumed role BedrockAgentCore-8cdaf416-b4aa-4382-b66e-80fb3510bdde has the required permissions
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_