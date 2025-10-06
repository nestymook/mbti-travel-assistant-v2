# Requirements Document

## Introduction

The MBTI Travel Planner Agent is experiencing health check failures with the error: `'EnvironmentConfig' object has no attribute 'get_connection_config'`. This error occurs in the `AgentCoreHealthCheckService` when it tries to create an `AgentCoreRuntimeClient` and calls `self.config.get_connection_config()` on the `EnvironmentConfig` object.

The issue is that the `EnvironmentConfig` class in `config/agentcore_environment_config.py` does not have a `get_connection_config()` method, but the health check service expects this method to exist to obtain connection configuration for the AgentCore Runtime client.

This is a critical bug that prevents the health monitoring system from functioning properly, which impacts the reliability and observability of the agent system.

## Requirements

### Requirement 1: Fix EnvironmentConfig Connection Configuration

**User Story:** As a system administrator, I want the health check service to work properly, so that I can monitor the status of restaurant search and reasoning agents.

#### Acceptance Criteria

1. WHEN the `AgentCoreHealthCheckService` calls `self.config.get_connection_config()` THEN the `EnvironmentConfig` object SHALL provide a valid `ConnectionConfig` object
2. WHEN the `get_connection_config()` method is called THEN it SHALL return a `ConnectionConfig` with appropriate timeout, connection pool, and keepalive settings
3. WHEN the connection configuration is created THEN it SHALL use values from the performance configuration section of the environment config
4. WHEN the health check service initializes THEN it SHALL successfully create an `AgentCoreRuntimeClient` without errors
5. WHEN the system starts up THEN the health check logs SHALL show successful initialization instead of the current error

### Requirement 2: Maintain Configuration Consistency

**User Story:** As a developer, I want the connection configuration to be consistent with the existing performance configuration, so that the system uses unified settings across all components.

#### Acceptance Criteria

1. WHEN creating the `ConnectionConfig` THEN it SHALL use the `timeout_seconds` from the AgentCore configuration
2. WHEN creating the `ConnectionConfig` THEN it SHALL use the `max_connections` and `max_connections_per_host` from the performance configuration
3. WHEN the performance configuration is updated THEN the connection configuration SHALL reflect those changes
4. WHEN the connection configuration is requested THEN it SHALL be consistent with other runtime client instances in the system
5. WHEN configuration validation runs THEN it SHALL verify that connection settings are within valid ranges

### Requirement 3: Backward Compatibility

**User Story:** As a system integrator, I want the fix to maintain backward compatibility with existing code, so that other components continue to work without changes.

#### Acceptance Criteria

1. WHEN existing code calls other methods on `EnvironmentConfig` THEN they SHALL continue to work as before
2. WHEN the `AgentCoreRuntimeClient` is created elsewhere in the system THEN it SHALL continue to work with the same connection configuration approach
3. WHEN configuration loading occurs THEN all existing configuration properties SHALL remain available and unchanged
4. WHEN the system runs in different environments THEN the connection configuration SHALL adapt appropriately
5. WHEN other services use the environment configuration THEN they SHALL not be affected by the addition of the new method

### Requirement 4: Error Handling and Validation

**User Story:** As a DevOps engineer, I want proper error handling for connection configuration, so that configuration issues are detected early and provide clear guidance.

#### Acceptance Criteria

1. WHEN connection configuration values are invalid THEN the system SHALL raise clear validation errors
2. WHEN required configuration is missing THEN the system SHALL provide helpful error messages indicating what needs to be configured
3. WHEN connection pool settings are inconsistent THEN the system SHALL detect and report the configuration conflict
4. WHEN timeout values are out of range THEN the system SHALL validate and reject invalid values with appropriate messages
5. WHEN the connection configuration is created THEN it SHALL log the settings being used for debugging purposes

### Requirement 5: Health Check Service Recovery

**User Story:** As a site reliability engineer, I want the health check service to resume normal operation after the fix, so that I can monitor agent health and performance.

#### Acceptance Criteria

1. WHEN the health check service starts THEN it SHALL successfully initialize without the `get_connection_config` error
2. WHEN health checks run for restaurant search agents THEN they SHALL complete successfully and report status
3. WHEN health checks run for restaurant reasoning agents THEN they SHALL complete successfully and report status
4. WHEN the health check service performs background checks THEN they SHALL execute without configuration-related errors
5. WHEN health check results are requested THEN they SHALL provide accurate status information for both agents

### Requirement 6: AgentCore IAM Permissions Fix

**User Story:** As a system administrator, I want the AgentCore health check service to have proper IAM permissions to access Bedrock AgentCore resources, so that health checks can successfully query agent runtime status.

#### Acceptance Criteria

1. WHEN the health check service calls `bedrock-agentcore:GetAgentRuntime` THEN the assumed role SHALL have the necessary permissions to perform this operation
2. WHEN the AgentCore execution role `AmazonBedrockAgentCoreSDKRuntime-us-east-1-849e62e6e2` assumes the runtime role THEN it SHALL have `bedrock-agentcore:GetAgentRuntime` permission
3. WHEN health checks query the agent runtime `arn:aws:bedrock-agentcore:us-east-1:209803798463:runtime/restaurant_search_agent-mN8bgq2Y1j` THEN the operation SHALL succeed without AccessDeniedException
4. WHEN the IAM policy is applied THEN it SHALL include permissions for all necessary AgentCore operations including GetAgentRuntime, ListAgentRuntimes, and DescribeAgentRuntime
5. WHEN the health check service runs after the IAM fix THEN it SHALL successfully retrieve agent runtime status without permission errors