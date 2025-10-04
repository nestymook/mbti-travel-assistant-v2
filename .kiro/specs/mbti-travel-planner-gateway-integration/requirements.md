# Requirements Document

## Introduction

This feature updates the mbti-travel-planner-agent to connect directly to the agentcore-gateway-mcp-tools instead of connecting to individual MCP servers (restaurant-search-mcp and restaurant-search-result-reasoning-mcp). The updated agent will use the Amazon Nova Pro foundation model (amazon.nova-pro-v1:0) and communicate with the gateway through RESTful HTTP endpoints to search for restaurants in the "Central" district and receive restaurant recommendations.

The agentcore-gateway-mcp-tools project has already been deployed to Bedrock AgentCore and exposes restaurant search and reasoning capabilities through a unified HTTP API gateway. This integration will simplify the architecture by removing the need for direct MCP client connections and JWT authentication complexity.

## Requirements

### Requirement 1

**User Story:** As a travel planner agent, I want to connect to the agentcore-gateway-mcp-tools through HTTP endpoints, so that I can access restaurant search and reasoning capabilities without managing complex MCP client connections.

#### Acceptance Criteria

1. WHEN the agent is initialized THEN it SHALL configure HTTP client connections to the agentcore-gateway-mcp-tools endpoint
2. WHEN the agent needs restaurant data THEN it SHALL make HTTP requests to the gateway instead of MCP client calls
3. WHEN the gateway is unavailable THEN the agent SHALL handle connection errors gracefully and provide fallback responses
4. IF the HTTP request fails THEN the agent SHALL log appropriate error messages and return user-friendly error responses

### Requirement 2

**User Story:** As a travel planner agent, I want to use the Amazon Nova Pro foundation model (amazon.nova-pro-v1:0), so that I can provide high-quality responses with the latest model capabilities.

#### Acceptance Criteria

1. WHEN the agent is created THEN it SHALL use the "amazon.nova-pro-v1:0" model specification
2. WHEN processing user requests THEN the agent SHALL leverage Nova Pro's enhanced reasoning capabilities
3. WHEN generating responses THEN the agent SHALL maintain appropriate temperature and token limits for Nova Pro
4. IF the Nova Pro model is unavailable THEN the agent SHALL log the error and fail gracefully

### Requirement 3

**User Story:** As a user, I want to search for restaurants in the "Central" district, so that I can get restaurant recommendations for that specific Hong Kong location.

#### Acceptance Criteria

1. WHEN a user requests restaurants in "Central" district THEN the agent SHALL call the gateway's district search endpoint
2. WHEN the gateway returns restaurant data THEN the agent SHALL process and present the results in a user-friendly format
3. WHEN no restaurants are found THEN the agent SHALL inform the user that no results were available
4. IF the search request fails THEN the agent SHALL provide an appropriate error message to the user

### Requirement 4

**User Story:** As a user, I want to receive restaurant recommendations based on sentiment analysis, so that I can make informed dining decisions.

#### Acceptance Criteria

1. WHEN restaurant data is available THEN the agent SHALL call the gateway's recommendation endpoint
2. WHEN the gateway returns recommendations THEN the agent SHALL present the top recommended restaurants with reasoning
3. WHEN sentiment analysis is performed THEN the agent SHALL explain the recommendation criteria used
4. IF recommendation analysis fails THEN the agent SHALL still provide the basic restaurant list without recommendations

### Requirement 5

**User Story:** As a developer, I want the agent to handle authentication seamlessly, so that users don't need to manage authentication credentials manually.

#### Acceptance Criteria

1. WHEN making HTTP requests to the gateway THEN the agent SHALL include appropriate authentication headers if required
2. WHEN authentication fails THEN the agent SHALL attempt to refresh credentials or provide clear error messages
3. WHEN the gateway requires no authentication THEN the agent SHALL work without authentication overhead
4. IF authentication is misconfigured THEN the agent SHALL log detailed error information for debugging

### Requirement 6

**User Story:** As a system administrator, I want comprehensive error handling and logging, so that I can monitor and troubleshoot the agent's performance.

#### Acceptance Criteria

1. WHEN HTTP requests are made THEN the agent SHALL log request details and response status
2. WHEN errors occur THEN the agent SHALL log detailed error information including stack traces
3. WHEN the gateway is unreachable THEN the agent SHALL log connectivity issues with appropriate severity levels
4. IF performance issues occur THEN the agent SHALL log timing information for debugging

### Requirement 7

**User Story:** As a user, I want the agent to provide a complete restaurant search and recommendation workflow, so that I can get comprehensive dining suggestions for my travel planning.

#### Acceptance Criteria

1. WHEN I ask about restaurants in Central district THEN the agent SHALL search for restaurants and provide recommendations
2. WHEN restaurant data is retrieved THEN the agent SHALL analyze sentiment and rank restaurants appropriately
3. WHEN presenting results THEN the agent SHALL include restaurant details, ratings, and recommendation reasoning
4. IF the complete workflow cannot be executed THEN the agent SHALL provide partial results with explanations of what data is available

### Requirement 8

**User Story:** As a developer, I want the agent configuration to be environment-aware, so that it can connect to different gateway instances for development, staging, and production.

#### Acceptance Criteria

1. WHEN the agent starts THEN it SHALL read environment configuration to determine the correct gateway endpoint
2. WHEN running in different environments THEN the agent SHALL use appropriate gateway URLs and authentication settings
3. WHEN configuration is missing THEN the agent SHALL use sensible defaults or fail with clear error messages
4. IF environment variables are misconfigured THEN the agent SHALL validate configuration and report specific issues