# Implementation Plan - MBTI Travel Planner AgentCore API Integration Fix

- [x] 1. Fix AgentCore Runtime Client API Integration





  - Update service name from 'bedrock-agent-runtime' to 'bedrock-agentcore-control'
  - Remove unsupported 'cognito_config' parameter from initialization
  - Replace 'InvokeAgent' operation with 'invoke_agent_runtime'
  - Update API parameter mapping for AgentCore compatibility
  - _Requirements: 1.1, 1.2, 1.3, 2.1, 2.3_





- [ ] 2. Add Missing Methods to Monitoring Service

  - Add missing 'log_error' method to AgentCoreMonitoringService class



  - Update method signatures to match current SDK expectations
  - Fix initialization compatibility issues
  - Ensure all required monitoring methods are available
  - _Requirements: 2.2, 4.4_




- [ ] 3. Update Health Check Service for AgentCore APIs

  - Modify health check logic to use 'get_agent_runtime' for status verification
  - Update agent connectivity tests to use 'invoke_agent_runtime'
  - Fix health status reporting to show accurate agent availability




  - Update error handling for AgentCore-specific exceptions
  - _Requirements: 3.1, 3.2, 3.3_

- [x] 4. Fix Connection Pool Manager Service Configuration




  - Update connection pool to use 'bedrock-agentcore-control' service
  - Fix service endpoint configuration for AgentCore
  - Update connection parameters and retry logic
  - Ensure proper connection pooling for AgentCore operations
  - _Requirements: 2.3, 4.1_



- [-] 5. Implement AgentCore-Specific Error Handling


  - Create AgentCore exception classes (AgentCoreError, AgentCoreInvocationError, etc.)
  - Update error handling to catch and properly handle AgentCore exceptions
  - Implement retry logic with exponential backoff for failed invocations
  - Add proper error logging and monitoring for AgentCore operations
  - _Requirements: 2.4, 3.4_

- [x] 6. Update API Request and Response Models








  - Create AgentCoreInvocationRequest model with correct parameter mapping
  - Create AgentCoreInvocationResponse model to parse AgentCore responses
  - Update data transformation logic for AgentCore API compatibility
  - Ensure backward compatibility with existing response formats
  - _Requirements: 2.3, 4.2_


- [x] 7. Fix Main Application Initialization









  - Update main.py to handle AgentCore client initialization correctly
  - Remove problematic parameter passing that causes SDK errors
  - Fix error handling during application startup
  - Ensure clean initialization without compatibility issues
  - _Requirements: 1.4, 2.1, 4.3_

- [ ]* 8. Create Unit Tests for AgentCore API Integration
  - Write unit tests for AgentCoreRuntimeClient with correct service usage
  - Test API parameter mapping and response parsing
  - Test error handling scenarios and exception raising
  - Verify method availability and signature compatibility
  - _Requirements: 1.1, 1.2, 1.3, 2.1, 2.2, 2.3_

- [ ]* 9. Create Integration Tests for End-to-End Workflow
  - Test MBTI agent to restaurant search agent communication
  - Test MBTI agent to restaurant reasoning agent communication
  - Verify complete restaurant recommendation workflow
  - Test health check accuracy and agent status reporting
  - _Requirements: 3.3, 5.1, 5.2, 5.3, 5.4_

- [x] 10. Validate and Deploy AgentCore API Fixes







  - Test agent initialization without SDK compatibility errors
  - Verify health checks report 2/2 agents as healthy
  - Validate end-to-end restaurant recommendation functionality
  - Confirm all existing features continue to work properly
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 5.1, 5.2, 5.3, 5.4_