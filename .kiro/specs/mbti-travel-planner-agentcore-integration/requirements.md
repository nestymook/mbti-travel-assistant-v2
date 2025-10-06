# Requirements Document

## Introduction

The MBTI Travel Planner Agent currently uses HTTP gateway calls to communicate with restaurant search and reasoning services through the `agentcore-gateway-mcp-tools` service. However, there are two deployed Bedrock AgentCore agents (`restaurant_search_agent` and `restaurant_search_result_reasoning_agent`) that provide the same functionality and should be used instead.

This feature will update the `mbti-travel-planner-agent` to call the deployed AgentCore agents directly using the AgentCore Runtime API, eliminating the need for HTTP gateway intermediaries. This approach follows AgentCore best practices for agent-to-agent communication and provides better performance, reliability, and ecosystem integration.

**Current Architecture:**
`mbti-travel-planner-agent` → HTTP Gateway → `agentcore-gateway-mcp-tools` → MCP calls

**Target Architecture:**
`mbti-travel-planner-agent` → AgentCore Runtime API → `restaurant_search_agent` & `restaurant_search_result_reasoning_agent`

## Requirements

### Requirement 1: AgentCore Agent Integration

**User Story:** As a developer, I want the MBTI Travel Planner Agent to use deployed AgentCore agents for restaurant search and reasoning, so that the system has better performance, reliability, and proper AgentCore ecosystem integration.

#### Acceptance Criteria

1. WHEN the MBTI Travel Planner Agent needs restaurant search functionality THEN it SHALL call the `restaurant_search_agent` (ARN: `arn:aws:bedrock-agentcore:us-east-1:209803798463:runtime/restaurant_search_agent-mN8bgq2Y1j`) using AgentCore Runtime API
2. WHEN the MBTI Travel Planner Agent needs restaurant reasoning functionality THEN it SHALL call the `restaurant_search_result_reasoning_agent` (ARN: `arn:aws:bedrock-agentcore:us-east-1:209803798463:runtime/restaurant_search_result_reasoning_agent-MSns5D6SLE`) using AgentCore Runtime API
3. WHEN making AgentCore agent calls THEN the system SHALL use proper JWT authentication with the configured Cognito client
4. WHEN AgentCore agent calls fail THEN the system SHALL provide appropriate error handling and fallback responses
5. WHEN the system starts up THEN it SHALL validate that the target AgentCore agents are accessible and properly configured

### Requirement 2: Direct AgentCore Agent Communication

**User Story:** As a system architect, I want to replace the current HTTP gateway-based tools with direct AgentCore agent calls, so that the system uses native AgentCore agent-to-agent communication patterns and eliminates unnecessary intermediary layers.

#### Acceptance Criteria

1. WHEN the system initializes THEN it SHALL remove HTTP gateway client dependencies and replace them with AgentCore Runtime client
2. WHEN creating restaurant search tools THEN the system SHALL use AgentCore Runtime API to call `restaurant_search_agent` directly
3. WHEN creating restaurant reasoning tools THEN the system SHALL use AgentCore Runtime API to call `restaurant_search_result_reasoning_agent` directly
4. WHEN the Central District workflow executes THEN it SHALL orchestrate direct calls to both AgentCore agents in sequence
5. WHEN tool functions are called THEN they SHALL return the same data format as the current HTTP gateway tools for backward compatibility

### Requirement 3: Authentication and Security

**User Story:** As a security engineer, I want the AgentCore agent calls to use proper JWT authentication, so that the system maintains security standards and access control.

#### Acceptance Criteria

1. WHEN making AgentCore agent calls THEN the system SHALL use JWT tokens from the configured Cognito client (`1ofgeckef3po4i3us4j1m4chvd`)
2. WHEN JWT tokens expire THEN the system SHALL automatically refresh them using the Cognito configuration
3. WHEN authentication fails THEN the system SHALL log the error and provide appropriate user feedback
4. WHEN the system starts THEN it SHALL validate the Cognito configuration and JWT discovery URL
5. WHEN making agent calls THEN the system SHALL include proper authorization headers with valid JWT tokens

### Requirement 4: Error Handling and Resilience

**User Story:** As an operations engineer, I want robust error handling for AgentCore agent calls, so that the system provides reliable service even when individual agents are unavailable.

#### Acceptance Criteria

1. WHEN an AgentCore agent is unavailable THEN the system SHALL provide a graceful fallback response with helpful information
2. WHEN AgentCore agent calls timeout THEN the system SHALL retry with exponential backoff up to 3 attempts
3. WHEN both restaurant agents are unavailable THEN the system SHALL still provide general MBTI travel planning assistance
4. WHEN agent calls fail THEN the system SHALL log detailed error information for debugging
5. WHEN the system encounters authentication errors THEN it SHALL attempt token refresh before failing

### Requirement 5: Configuration Management

**User Story:** As a DevOps engineer, I want environment-based configuration for AgentCore agent ARNs and settings, so that the system can work across different deployment environments.

#### Acceptance Criteria

1. WHEN the system starts THEN it SHALL load AgentCore agent ARNs from environment-specific configuration
2. WHEN deploying to different environments THEN the system SHALL use the appropriate agent ARNs for that environment
3. WHEN configuration is invalid THEN the system SHALL fail fast with clear error messages
4. WHEN environment variables are missing THEN the system SHALL use sensible defaults or fail with helpful guidance
5. WHEN the system runs in development mode THEN it SHALL provide additional logging and debugging information

### Requirement 6: Monitoring and Observability

**User Story:** As a site reliability engineer, I want comprehensive monitoring of AgentCore agent calls, so that I can track performance, errors, and usage patterns.

#### Acceptance Criteria

1. WHEN AgentCore agent calls are made THEN the system SHALL log performance metrics including response time and success rate
2. WHEN agent calls fail THEN the system SHALL log detailed error information with context
3. WHEN the system processes requests THEN it SHALL track which agents were called and their response times
4. WHEN monitoring health checks run THEN they SHALL verify connectivity to both restaurant agents
5. WHEN the system starts THEN it SHALL log the configuration and availability of target agents

### Requirement 7: Backward Compatibility

**User Story:** As a client application developer, I want the updated agent to maintain the same API interface, so that existing integrations continue to work without changes.

#### Acceptance Criteria

1. WHEN the agent receives requests THEN it SHALL maintain the same input/output format as the current implementation
2. WHEN restaurant search tools are called THEN they SHALL return data in the same JSON structure as before
3. WHEN restaurant reasoning tools are called THEN they SHALL return recommendation data in the same format
4. WHEN the Central District workflow runs THEN it SHALL produce the same formatted output structure
5. WHEN errors occur THEN they SHALL be formatted consistently with the current error response format

### Requirement 8: Performance Optimization

**User Story:** As an end user, I want faster response times for restaurant search and recommendations, so that I can get travel planning assistance quickly.

#### Acceptance Criteria

1. WHEN making AgentCore agent calls THEN the system SHALL use connection pooling and keep-alive connections
2. WHEN multiple agent calls are needed THEN the system SHALL make them in parallel where possible
3. WHEN agent responses are received THEN the system SHALL cache results appropriately to avoid redundant calls
4. WHEN the system processes requests THEN the total response time SHALL be no more than 20% slower than current HTTP gateway implementation
5. WHEN agents are called repeatedly THEN the system SHALL reuse authentication tokens until they expire