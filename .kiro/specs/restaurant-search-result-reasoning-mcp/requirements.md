# Requirements Document

## Introduction

This feature involves creating an MCP-enabled application that provides intelligent restaurant recommendation services based on sentiment analysis. The application will use AWS Bedrock AgentCore and Python to analyze restaurant data and provide smart recommendations by evaluating customer sentiment metrics (likes, dislikes, neutral responses). The system will be containerized using Docker and serve requests through MCP (Model Context Protocol) tools, enabling AI models to process restaurant lists and generate data-driven recommendations.

The application focuses on sentiment-based reasoning rather than search functionality, taking restaurant data as input and applying algorithmic analysis to identify top candidates and provide personalized recommendations. The system integrates with existing restaurant data sources and provides structured outputs for foundation models to deliver enhanced user experiences.

## Requirements

### Requirement 1

**User Story:** As a foundation model, I want to analyze restaurant sentiment data and provide intelligent recommendations, so that I can suggest the best restaurants based on customer satisfaction metrics.

#### Acceptance Criteria

1. WHEN a list of restaurants in JSON format is received THEN the system SHALL analyze sentiment data (likes, dislikes, neutral) for each restaurant
2. WHEN selecting candidates THEN the system SHALL rank restaurants by either highest sentiment likes OR highest combined likes plus neutral percentage
3. WHEN ranking by sentiment likes THEN the system SHALL sort restaurants in descending order by the "likes" value in the sentiment field
4. WHEN ranking by combined sentiment THEN the system SHALL calculate (likes + neutral) percentage and sort in descending order
5. WHEN candidates are selected THEN the system SHALL return the top 10 restaurants from the ranked list for lunch and dinner meal types, and top 20 restaurants for breakfast meal type
6. WHEN providing a recommendation THEN the system SHALL randomly select 1 restaurant from the top candidates (10 for lunch/dinner, 20 for breakfast)
7. WHEN returning results THEN the system SHALL provide both the complete candidate list (10 for lunch/dinner, 20 for breakfast) and the single recommended restaurant
8. IF fewer than the required number of restaurants are provided THEN the system SHALL return all available restaurants as candidates
9. WHEN meal type context is available THEN the system SHALL determine candidate count based on meal type: breakfast (20 candidates), lunch (10 candidates), dinner (10 candidates)
10. IF meal type context is not available THEN the system SHALL default to 10 candidates for general restaurant recommendations
11. IF sentiment data is missing or invalid for a restaurant THEN the system SHALL exclude it from ranking calculations
12. WHEN sentiment percentages are calculated THEN the system SHALL ensure they are based on total sentiment responses (likes + dislikes + neutral)

### Requirement 2

**User Story:** As a foundation model, I want to use an MCP tool for restaurant recommendation reasoning, so that I can process restaurant lists and generate intelligent recommendations based on sentiment analysis.

#### Acceptance Criteria

1. WHEN the MCP server exposes tools THEN it SHALL include a `recommend_restaurants` tool that accepts a list of restaurant JSON objects
2. WHEN the `recommend_restaurants` tool is called THEN it SHALL accept parameters for restaurant list and ranking method (sentiment_likes or combined_sentiment)
3. WHEN processing restaurant data THEN the tool SHALL validate that each restaurant contains required fields: id, name, sentiment (with likes, dislikes, neutral)
4. WHEN ranking method is "sentiment_likes" THEN the tool SHALL rank restaurants by sentiment.likes in descending order
5. WHEN ranking method is "combined_sentiment" THEN the tool SHALL rank by (sentiment.likes + sentiment.neutral) percentage
6. WHEN returning results THEN the tool SHALL provide a structured response with "candidates" (top 20) and "recommendation" (1 random from top 20)
7. WHEN invalid restaurant data is provided THEN the tool SHALL return appropriate error messages with details about missing or invalid fields
8. IF the restaurant list is empty THEN the tool SHALL return an error indicating no restaurants to process

### Requirement 3

**User Story:** As a foundation model, I want to receive restaurant data from external sources, so that I can perform sentiment-based analysis and recommendations on current restaurant information.

#### Acceptance Criteria

1. WHEN restaurant data is needed THEN the system SHALL accept restaurant lists from external MCP tools or API calls
2. WHEN integrating with existing restaurant search tools THEN the system SHALL be compatible with data formats from restaurant search services
3. WHEN restaurant data is received THEN it SHALL validate the JSON structure contains required sentiment and restaurant information
4. WHEN processing external data THEN the system SHALL handle different data sources gracefully
5. IF external data sources are unavailable THEN the system SHALL provide appropriate error handling and fallback responses

### Requirement 4

**User Story:** As a foundation model, I want to use MCP tools to interact with the restaurant search service, so that I can integrate restaurant search capabilities into my responses.

#### Acceptance Criteria

1. WHEN the MCP server is running THEN it SHALL expose restaurant search tools via MCP protocol
2. WHEN an MCP tool is called THEN the system SHALL process the request and return structured restaurant data
3. WHEN invalid parameters are provided to MCP tools THEN the system SHALL return validation error messages
4. IF the MCP server is unavailable THEN foundation models SHALL receive appropriate connection error messages

### Requirement 5

**User Story:** As a system administrator, I want the application to run in a Docker container, so that I can deploy and manage it consistently across environments.

#### Acceptance Criteria

1. WHEN the Docker container is built THEN it SHALL include all necessary dependencies for Python, boto3, and Bedrock AgentCore
2. WHEN the container is started THEN it SHALL automatically start the MCP server and begin serving requests
3. WHEN the container receives a stop signal THEN it SHALL gracefully shutdown the MCP server
4. IF container health checks are implemented THEN they SHALL verify the MCP server is responding correctly

### Requirement 6

**User Story:** As a foundation model, I want to receive structured restaurant data with all relevant information, so that I can provide comprehensive restaurant details to users.

#### Acceptance Criteria

1. WHEN restaurant data is returned THEN it SHALL include id, name, address, mealType (array of cuisine types), sentiment (likes, dislikes, neutral), locationCategory, district, priceRange, and operatingHours
2. WHEN restaurant metadata is available THEN it SHALL include dataQuality, version, and qualityScore information from the metadata field
3. WHEN file metadata is returned THEN it SHALL include timestamp, version, district, locationCategory, recordCount, fileSize, sanitizedAt, and sanitizationVersion from the file's metadata section
4. WHEN operatingHours are returned THEN they SHALL include "Mon - Fri", "Sat - Sun", and "Public Holiday" with arrays of time ranges
5. IF any required data fields are missing THEN the system SHALL handle gracefully and indicate missing information

### Requirement 7

**User Story:** As a system integrator, I want the application to follow Bedrock AgentCore patterns, so that it integrates properly with AWS Bedrock services.

#### Acceptance Criteria

1. WHEN implementing the MCP server THEN it SHALL follow the patterns demonstrated in the AgentCore gateway tutorial
2. WHEN hosting the MCP server THEN it SHALL follow the patterns from the AgentCore runtime hosting tutorial
3. WHEN implementing authentication THEN it SHALL follow the inbound auth example patterns
4. IF AgentCore integration fails THEN the system SHALL provide detailed error messages for troubleshooting

### Requirement 8 - AgentCore Foundation Model Configuration

**User Story:** As a system administrator, I want to configure a foundation model in AgentCore, so that natural language queries can be processed and converted to MCP tool calls.

#### Acceptance Criteria

1. WHEN AgentCore is configured THEN it SHALL include a foundation model specification (e.g., Claude 3.5 Sonnet)
2. WHEN the foundation model is configured THEN it SHALL have access to all available MCP tools and their parameter schemas
3. WHEN model parameters are set THEN they SHALL be optimized for restaurant search tasks (appropriate temperature, max tokens, etc.)
4. WHEN system prompts are configured THEN they SHALL include context about Hong Kong districts and restaurant search capabilities
5. WHEN tool calling is enabled THEN the model SHALL be able to invoke MCP tools with correct parameter formatting
6. IF model configuration fails THEN the system SHALL provide detailed error messages for troubleshooting

### Requirement 9 - AgentCore Runtime Integration

**User Story:** As a system integrator, I want AgentCore Runtime to properly bridge natural language queries to MCP tool calls, so that the complete restaurant search workflow functions seamlessly.

#### Acceptance Criteria

1. WHEN a user sends `{"input": {"prompt": "Find restaurants in Central district"}}` THEN AgentCore SHALL process the natural language and call the appropriate MCP tool
2. WHEN the foundation model generates MCP tool calls THEN AgentCore SHALL route them to the deployed MCP server
3. WHEN MCP tools return restaurant data THEN AgentCore SHALL pass the results back to the foundation model for response formatting
4. WHEN errors occur in the pipeline THEN AgentCore SHALL provide meaningful error messages to users
5. WHEN the system is under load THEN AgentCore SHALL handle concurrent requests efficiently
6. IF the MCP server is unavailable THEN AgentCore SHALL provide appropriate fallback responses

### Requirement 10 - Response Formatting and User Experience

**User Story:** As an end user, I want to receive well-formatted restaurant recommendations, so that I can easily understand and act on the search results.

#### Acceptance Criteria

1. WHEN restaurant results are returned THEN they SHALL be formatted in a conversational, easy-to-read manner
2. WHEN multiple restaurants are found THEN they SHALL be presented in a logical order (e.g., by district, then by name)
3. WHEN restaurant details are shown THEN they SHALL include key information like name, address, cuisine type, and operating hours
4. WHEN operating hours are displayed THEN they SHALL be formatted in a user-friendly way (e.g., "Open for breakfast: Mon-Fri 7:00-11:30")
5. WHEN no restaurants match the criteria THEN the response SHALL suggest alternative searches or nearby options
6. WHEN errors occur THEN the error messages SHALL be user-friendly and provide guidance on how to refine the search

### Requirement 11 - Cognito Authentication Integration

**User Story:** As a system administrator, I want to integrate AWS Cognito authentication with the MCP server, so that only authenticated users can access restaurant search functionality through AgentCore.

#### Acceptance Criteria

1. WHEN the MCP server starts THEN it SHALL configure AWS Cognito User Pool integration for authentication
2. WHEN AgentCore makes requests to the MCP server THEN it SHALL include valid JWT tokens from Cognito authentication
3. WHEN JWT tokens are received THEN the system SHALL validate them against the Cognito User Pool's JWKS endpoint
4. WHEN token validation fails THEN the system SHALL return HTTP 401 Unauthorized with appropriate error messages
5. WHEN tokens are expired THEN the system SHALL reject requests and indicate token refresh is required
6. IF Cognito configuration is invalid THEN the system SHALL fail to start with clear error messages

### Requirement 12 - JWT Token Management

**User Story:** As a system integrator, I want to handle JWT token creation and validation, so that the authentication flow works seamlessly with Bedrock AgentCore.

#### Acceptance Criteria

1. WHEN authenticating users THEN the system SHALL use AWS SDK to call Cognito's InitiateAuth API with SRP protocol
2. WHEN authentication succeeds THEN Cognito SHALL return ID, access, and refresh tokens
3. WHEN tokens are generated THEN they SHALL include appropriate claims for user identification and authorization
4. WHEN validating JWT tokens THEN the system SHALL verify signature using Cognito's public keys from JWKS endpoint
5. WHEN tokens expire THEN the system SHALL support refresh token flow to obtain new access tokens
6. IF SRP authentication fails THEN the system SHALL return appropriate error messages for credential issues

### Requirement 13 - AgentCore Authentication Configuration

**User Story:** As a system administrator, I want to configure AgentCore with Cognito authentication, so that the complete system enforces proper access controls.

#### Acceptance Criteria

1. WHEN AgentCore is deployed THEN it SHALL be configured with customJWTAuthorizer pointing to Cognito User Pool
2. WHEN the discovery URL is configured THEN it SHALL point to the Cognito User Pool's OpenID Connect configuration
3. WHEN allowedClients are specified THEN only those client IDs SHALL be permitted to access the agent
4. WHEN authentication is enabled THEN all requests to AgentCore SHALL require valid JWT tokens
5. WHEN tokens are validated THEN AgentCore SHALL pass them through to the MCP server for additional validation
6. IF authentication configuration is missing THEN AgentCore deployment SHALL fail with clear error messages

### Requirement 14 - Security and Token Validation

**User Story:** As a security administrator, I want robust JWT token validation, so that the system maintains proper security controls for restaurant data access.

#### Acceptance Criteria

1. WHEN validating JWT tokens THEN the system SHALL verify token signature, expiration, issuer, and audience claims
2. WHEN tokens contain user information THEN the system SHALL extract and log user context for audit purposes
3. WHEN token validation occurs THEN it SHALL use cached JWKS keys with appropriate refresh intervals
4. WHEN suspicious authentication attempts are detected THEN the system SHALL log security events
5. WHEN tokens are processed THEN sensitive information SHALL NOT be logged or exposed in error messages
6. IF token validation libraries are unavailable THEN the system SHALL fail securely by rejecting all requests

### Requirement 15 - Authentication Error Handling

**User Story:** As a developer, I want clear authentication error responses, so that I can troubleshoot and resolve authentication issues effectively.

#### Acceptance Criteria

1. WHEN authentication fails THEN the system SHALL return specific error codes for different failure types
2. WHEN tokens are malformed THEN the system SHALL return HTTP 400 with "Invalid token format" message
3. WHEN tokens are expired THEN the system SHALL return HTTP 401 with "Token expired" message and refresh guidance
4. WHEN Cognito services are unavailable THEN the system SHALL return HTTP 503 with "Authentication service unavailable"
5. WHEN JWKS endpoint is unreachable THEN the system SHALL use cached keys if available or return appropriate errors
6. IF authentication errors occur THEN they SHALL be logged with sufficient detail for debugging without exposing sensitive data

### Requirement 16 - MCP EntryPoint Integration

**User Story:** As a system integrator, I want to create an MCP entrypoint using BedrockAgentCoreApp, so that the system can receive payloads and trigger the LLM to choose and execute available MCP tools for restaurant search operations.

#### Acceptance Criteria

1. WHEN the application starts THEN it SHALL create a BedrockAgentCoreApp instance with an @app.entrypoint decorator
2. WHEN a payload is received at the entrypoint THEN it SHALL extract the user prompt from the payload structure
3. WHEN the entrypoint processes a request THEN it SHALL pass the user message to the Strands Agent for LLM processing
4. WHEN the LLM processes the user message THEN it SHALL automatically select and call appropriate MCP tools based on the query intent
5. WHEN MCP tools are executed THEN the results SHALL be integrated into the agent's response generation
6. WHEN the agent generates a response THEN it SHALL return a JSON-serializable string containing the formatted results
7. WHEN the application runs THEN it SHALL use app.run() to start the BedrockAgentCore runtime server
8. IF payload structure is invalid THEN the entrypoint SHALL handle the error gracefully and return appropriate error messages
9. IF the Strands Agent fails to process the message THEN the system SHALL return a fallback response with error details
10. WHEN multiple MCP tool calls are needed THEN the agent SHALL orchestrate them appropriately to fulfill the user's request
##
# Requirement 17 - MCP Server Status Check System

**User Story:** As a system administrator, I want to monitor the health and availability of the restaurant reasoning MCP server, so that I can ensure reliable service delivery and quickly identify issues.

#### Acceptance Criteria

1. WHEN the status check system is enabled THEN it SHALL perform health checks using MCP tools/list requests to validate server connectivity and tool availability
2. WHEN performing health checks THEN the system SHALL send standard MCP JSON-RPC 2.0 requests with method "tools/list" to the reasoning server endpoint
3. WHEN a successful health check occurs THEN the system SHALL validate that the response contains the expected reasoning tools: "recommend_restaurants" and "analyze_restaurant_sentiment"
4. WHEN health check requests are made THEN they SHALL include proper JWT Bearer token authentication for AgentCore Gateway endpoints
5. WHEN health checks fail THEN the system SHALL implement circuit breaker functionality to prevent cascading failures
6. WHEN circuit breaker thresholds are exceeded THEN the system SHALL automatically open the circuit and stop sending requests until recovery conditions are met
7. WHEN the system tracks metrics THEN it SHALL record response times, success/failure rates, uptime percentages, and consecutive failure counts
8. WHEN status information is requested THEN the system SHALL provide REST API endpoints for health status, server metrics, and circuit breaker states
9. WHEN authentication errors occur (403 Unauthorized) THEN the system SHALL handle them gracefully and attempt token refresh if configured
10. WHEN timeout errors occur THEN the system SHALL implement exponential backoff retry logic with configurable maximum retry delays
11. WHEN status checks are performed THEN they SHALL run continuously with configurable intervals (default 30 seconds) until explicitly stopped
12. IF the reasoning MCP server is unavailable THEN the status system SHALL report appropriate error states and maintain historical metrics for troubleshooting