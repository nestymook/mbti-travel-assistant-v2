# Requirements Document

## Introduction

This feature involves creating an MBTI Travel Assistant that operates as a Bedrock AgentCore runtime service that receives HTTP requests with MBTI personality parameters and generates comprehensive 3-day travel itineraries. The system uses Amazon Nova Pro foundation model to query an OpenSearch knowledge base for MBTI-matched tourist spots and integrates with existing MCP servers for restaurant recommendations.

The application follows the BedrockAgentCore runtime pattern with an entrypoint that receives MBTI personality types (4-character codes), processes them through Nova Pro to extract personality-matched tourist spots from the knowledge base, and creates detailed 3-day itineraries with morning/afternoon/night sessions plus breakfast/lunch/dinner restaurant assignments. The system integrates with existing MCP servers: `restaurant-search-mcp` and `restaurant-search-result-reasoning-mcp` for restaurant data and recommendations.

## Requirements

### Requirement 1 - MBTI Personality Processing and Knowledge Base Integration

**User Story:** As a web server, I want to send HTTP requests with MBTI personality parameters to the MBTI Travel Assistant, so that I can receive comprehensive 3-day travel itineraries with personality-matched tourist spots and restaurant recommendations.

#### Acceptance Criteria

1. WHEN an HTTP request is received with JWT authentication THEN the system SHALL validate the JWT token and extract user context
2. WHEN a payload contains MBTI_personality parameter (4-character code) THEN the system SHALL validate the MBTI format and pass it to Nova Pro foundation model
3. WHEN Nova Pro processes the MBTI personality THEN it SHALL query the OpenSearch knowledge base using optimized prompts to extract personality-matched tourist spots
4. WHEN knowledge base queries are executed THEN the system SHALL use efficient search strategies similar to `test_single_mbti_type.py` but optimized for faster response times
5. WHEN tourist spots are retrieved THEN the system SHALL create a 3-day itinerary with morning/afternoon/night sessions following strict assignment logic
6. WHEN itinerary sessions are assigned THEN the system SHALL ensure no tourist spot is repeated across the entire 3-day period
7. WHEN the final response is generated THEN it SHALL include complete itinerary data, candidate tourist spots, and restaurant assignments in structured JSON format
8. WHEN authentication fails THEN the system SHALL return HTTP 401 with appropriate error messages
9. IF knowledge base queries fail THEN the system SHALL handle errors gracefully and provide fallback itinerary options

### Requirement 2 - 3-Day Itinerary Generation with Session Assignment Logic

**User Story:** As a travel planning system, I want to generate structured 3-day itineraries with morning/afternoon/night sessions, so that users receive comprehensive travel plans with personality-matched tourist spots and optimal scheduling.

#### Acceptance Criteria

1. WHEN generating a 3-day itinerary THEN the system SHALL create exactly 3 days with morning (07:00-11:59), afternoon (12:00-17:59), and night (18:00-23:59) sessions
2. WHEN assigning morning sessions THEN the system SHALL select MBTI-matched tourist spots with morning operating hours or no operating hours, marking as "MBTI match" when successful
3. WHEN assigning afternoon sessions THEN the system SHALL prioritize tourist spots in the same district as the morning spot, then same area, with afternoon operating hours or no operating hours
4. WHEN assigning night sessions THEN the system SHALL prioritize tourist spots in the same district as morning/afternoon spots, with night operating hours or no operating hours
5. WHEN MBTI-matched spots are unavailable THEN the system SHALL assign random unassigned spots from non-MBTI categories, marking as "MBTI not match"
6. WHEN assigning spots for day 2 and 3 THEN the system SHALL ensure no tourist spot is repeated from previous days or sessions
7. WHEN session assignment fails THEN the system SHALL provide fallback assignment logic while maintaining the no-repeat constraint
8. WHEN all sessions are assigned THEN each tourist spot SHALL include all original fields plus a new "MBTI_match" boolean field
9. IF insufficient tourist spots exist THEN the system SHALL assign available spots and mark remaining sessions as unavailable
10. WHEN itinerary is complete THEN the system SHALL validate that no tourist spot appears twice across all 9 sessions (3 days × 3 sessions)

### Requirement 3 - Restaurant Assignment and MCP Integration

**User Story:** As an itinerary generation system, I want to assign breakfast, lunch, and dinner restaurants for each day using MCP tools, so that users receive complete dining recommendations that match their tourist spot locations.

#### Acceptance Criteria

1. WHEN assigning breakfast restaurants THEN the system SHALL search for restaurants operating 06:00-11:29 in the same district as the morning tourist spot
2. WHEN assigning lunch restaurants THEN the system SHALL search for restaurants operating 11:30-17:29 in the same district as morning or afternoon tourist spots
3. WHEN assigning dinner restaurants THEN the system SHALL search for restaurants operating 17:30-23:59 in the same district as afternoon or night tourist spots
4. WHEN calling restaurant MCP tools THEN the system SHALL use `restaurant-search-mcp` for search operations and `restaurant-search-result-reasoning-mcp` for recommendations
5. WHEN restaurant searches are executed THEN the system SHALL ensure no restaurant is assigned twice across the entire 3-day itinerary
6. WHEN restaurant data is retrieved THEN the system SHALL include all original restaurant fields in the response
7. WHEN restaurant assignment fails for a meal THEN the system SHALL expand search to adjacent districts or provide fallback options
8. WHEN MCP calls are made THEN the system SHALL handle connection failures and implement retry logic
9. IF restaurant MCP servers are unavailable THEN the system SHALL provide meal assignment placeholders with error notifications
10. WHEN all meals are assigned THEN the system SHALL validate restaurant operating hours match the assigned meal times

### Requirement 4 - Candidate Lists Generation

**User Story:** As a travel planning system, I want to generate candidate lists for tourist spots and restaurants, so that users have alternative options for each day of their itinerary.

#### Acceptance Criteria

1. WHEN generating tourist spot candidates THEN the system SHALL identify unassigned tourist spots matching the Areas or Locations for each day
2. WHEN tourist spot candidates are found THEN the system SHALL ensure no spot appears in both main itinerary and candidate lists
3. WHEN tourist spot candidates match the MBTI personality THEN they SHALL be marked with "MBTI_match": true
4. WHEN generating restaurant candidates THEN the system SHALL search for unassigned restaurants matching meal time and district criteria for each day
5. WHEN restaurant candidates are identified THEN they SHALL follow the same district matching rules as main restaurant assignments
6. WHEN breakfast candidates are generated THEN they SHALL operate 06:00-11:29 in the same district as morning tourist spots
7. WHEN lunch candidates are generated THEN they SHALL operate 11:30-17:29 in districts matching morning or afternoon tourist spots
8. WHEN dinner candidates are generated THEN they SHALL operate 17:30-23:59 in districts matching afternoon or night tourist spots
9. WHEN candidate lists are complete THEN they SHALL include all original fields from tourist spot and restaurant records
10. IF insufficient candidates exist THEN the system SHALL provide available candidates and note limitations in metadata

### Requirement 5 - Nova Pro Foundation Model Integration

**User Story:** As an MBTI travel system, I want to use Amazon Nova Pro foundation model to query the OpenSearch knowledge base efficiently, so that I can retrieve personality-matched tourist spots quickly and accurately.

#### Acceptance Criteria

1. WHEN receiving MBTI personality parameters THEN Nova Pro SHALL validate the 4-character MBTI format (e.g., INFJ, ENFP)
2. WHEN querying the knowledge base THEN Nova Pro SHALL use optimized prompts based on `test_single_mbti_type.py` patterns but with improved performance
3. WHEN executing knowledge base searches THEN the system SHALL implement faster query strategies than the current multi-prompt approach
4. WHEN processing MBTI personalities THEN Nova Pro SHALL understand personality traits and match them to appropriate tourist spot characteristics
5. WHEN tourist spots are retrieved THEN Nova Pro SHALL parse and structure the data for itinerary generation
6. WHEN knowledge base responses are received THEN the system SHALL validate data completeness and handle missing information
7. IF knowledge base queries fail THEN Nova Pro SHALL implement retry logic and provide fallback search strategies
8. WHEN multiple tourist spots are found THEN Nova Pro SHALL prioritize spots based on MBTI personality alignment
9. IF insufficient MBTI-matched spots exist THEN Nova Pro SHALL identify suitable non-MBTI spots as alternatives
10. WHEN knowledge base integration is complete THEN the system SHALL cache frequently requested MBTI personality results for performance optimization

### Requirement 6 - Complete JSON Response Structure

**User Story:** As a frontend web application, I want to receive comprehensive 3-day itinerary data in structured JSON format, so that I can display complete travel plans with tourist spots, restaurants, and candidate options.

#### Acceptance Criteria

1. WHEN returning itinerary responses THEN the system SHALL provide a JSON response with "main_itinerary", "candidate_tourist_spots", "candidate_restaurants", and "metadata" top-level fields
2. WHEN the "main_itinerary" field is populated THEN it SHALL contain exactly 3 days with morning/afternoon/night sessions and breakfast/lunch/dinner assignments
3. WHEN tourist spot objects are returned THEN they SHALL include all original fields plus the new "MBTI_match" boolean field
4. WHEN restaurant objects are returned THEN they SHALL include all original restaurant fields (id, name, address, district, operating_hours, etc.)
5. WHEN candidate lists are provided THEN they SHALL be organized by day and meal/session type for easy frontend consumption
6. WHEN metadata is included THEN it SHALL contain MBTI_personality, generation_timestamp, total_spots_found, total_restaurants_found, and processing_time
7. WHEN errors occur THEN the response SHALL include an "error" field with error_type, message, and suggested_actions
8. WHEN the response is generated THEN all JSON SHALL be properly formatted and validated for frontend consumption
9. IF partial data is available THEN the system SHALL return available data with appropriate status indicators
10. WHEN operating hours are included THEN they SHALL be formatted consistently for frontend display and validation

### Requirement 7 - Session Assignment Logic Validation

**User Story:** As a quality assurance system, I want to validate that session assignment logic is strictly applied, so that itineraries meet all business rules and constraints.

#### Acceptance Criteria

1. WHEN validating morning sessions THEN the system SHALL verify tourist spots have morning operating hours (07:00-11:59) or no operating hours
2. WHEN validating afternoon sessions THEN the system SHALL verify tourist spots have afternoon operating hours (12:00-17:59) or no operating hours  
3. WHEN validating night sessions THEN the system SHALL verify tourist spots have night operating hours (18:00-23:59) or no operating hours
4. WHEN validating district matching THEN the system SHALL verify afternoon and night spots prioritize same district as morning spot
5. WHEN validating area matching THEN the system SHALL verify fallback to same area when same district is unavailable
6. WHEN validating uniqueness THEN the system SHALL ensure no tourist spot appears twice across all 9 sessions (3 days × 3 sessions)
7. WHEN validating MBTI matching THEN the system SHALL verify MBTI_match field accurately reflects personality alignment
8. WHEN validating restaurant assignments THEN the system SHALL verify meal times match restaurant operating hours
9. WHEN validating restaurant districts THEN the system SHALL verify restaurants are in same districts as corresponding tourist spots
10. IF validation fails THEN the system SHALL log specific validation errors and attempt correction or provide detailed error responses

### Requirement 8 - JWT Authentication and Security Integration

**User Story:** As a web server, I want to authenticate securely with the MBTI Travel Assistant using JWT tokens, so that only authorized requests are processed and system access is properly controlled.

#### Acceptance Criteria

1. WHEN HTTP requests are received THEN the system SHALL validate JWT tokens in the Authorization header
2. WHEN making MCP client calls to external servers THEN the system SHALL include appropriate authentication for MCP connections
3. WHEN JWT token validation fails THEN the system SHALL return HTTP 401 Unauthorized with appropriate error messages
4. WHEN logging system activities THEN the system SHALL exclude sensitive authentication information from logs
5. WHEN rate limiting occurs THEN the system SHALL implement appropriate backoff strategies for HTTP and MCP calls
6. IF security violations are detected THEN the system SHALL log security events for monitoring
7. WHEN handling request processing THEN the system SHALL maintain secure context throughout the processing pipeline
8. WHEN processing request payloads THEN the system SHALL validate and sanitize all input data
9. IF unauthorized access is attempted THEN the system SHALL reject requests and log security incidents
10. WHEN authentication is successful THEN the system SHALL extract user context for personalized itinerary generation

### Requirement 9 - Error Handling and Resilience

**User Story:** As a system operator, I want the travel assistant to handle failures gracefully, so that users receive helpful feedback even when underlying services are unavailable.

#### Acceptance Criteria

1. WHEN knowledge base queries fail THEN the system SHALL provide meaningful error messages and attempt alternative search strategies
2. WHEN network timeouts occur THEN the system SHALL retry requests with exponential backoff
3. WHEN malformed responses are received THEN the system SHALL handle parsing errors and provide fallback responses
4. WHEN partial data is available THEN the system SHALL return available information with appropriate disclaimers
5. WHEN MCP server calls fail THEN the system SHALL fall back to cached data or provide placeholder recommendations
6. WHEN tourist spot data is incomplete THEN the system SHALL filter out incomplete records and note data limitations
7. IF all services fail THEN the system SHALL provide cached itineraries when available
8. WHEN errors are logged THEN they SHALL include sufficient context for debugging without exposing sensitive data
9. WHEN system health checks fail THEN the system SHALL report status appropriately to monitoring systems
10. IF critical errors occur THEN the system SHALL alert administrators while maintaining user experience

### Requirement 10 - Performance and Scalability

**User Story:** As a system administrator, I want the travel assistant to perform efficiently under load, so that users receive timely responses even during peak usage periods.

#### Acceptance Criteria

1. WHEN processing MBTI requests THEN the system SHALL respond within 10 seconds for complete 3-day itinerary generation
2. WHEN making multiple knowledge base queries THEN the system SHALL optimize query strategies for faster response times than current multi-prompt approach
3. WHEN caching is implemented THEN the system SHALL cache frequently requested MBTI personality results and tourist spot data
4. WHEN under high load THEN the system SHALL implement request queuing and load balancing
5. WHEN memory usage is high THEN the system SHALL implement appropriate garbage collection and memory management
6. WHEN concurrent requests are processed THEN the system SHALL handle them efficiently without blocking
7. IF response times exceed thresholds THEN the system SHALL log performance metrics for optimization
8. WHEN scaling horizontally THEN the system SHALL support stateless operation for multiple instances
9. WHEN monitoring performance THEN the system SHALL expose metrics for response times, error rates, and throughput
10. IF performance degrades THEN the system SHALL implement circuit breakers to prevent cascade failures

### Requirement 11 - Deployment and Configuration

**User Story:** As a DevOps engineer, I want to deploy and configure the travel assistant consistently across environments, so that I can manage the system reliably in development, staging, and production.

#### Acceptance Criteria

1. WHEN deploying the application THEN it SHALL be containerized using Docker with ARM64 architecture support
2. WHEN configuring knowledge base endpoints THEN they SHALL be externalized as environment variables
3. WHEN setting up authentication THEN Cognito configuration SHALL be provided through secure configuration management
4. WHEN deploying to different environments THEN the system SHALL support environment-specific configuration
5. WHEN health checks are implemented THEN they SHALL verify connectivity to knowledge base and MCP servers
6. WHEN logging is configured THEN it SHALL support structured logging with appropriate log levels
7. IF configuration is invalid THEN the system SHALL fail to start with clear error messages
8. WHEN monitoring is set up THEN it SHALL integrate with CloudWatch and other AWS monitoring services
9. WHEN secrets are managed THEN they SHALL be stored securely using AWS Secrets Manager or similar
10. IF deployment fails THEN the system SHALL provide detailed error information for troubleshooting

### Requirement 12 - Testing and Quality Assurance

**User Story:** As a developer, I want comprehensive testing coverage for the travel assistant, so that I can ensure reliability and correctness of 3-day itinerary generation.

#### Acceptance Criteria

1. WHEN unit tests are implemented THEN they SHALL cover itinerary generation logic with at least 90% code coverage
2. WHEN integration tests are created THEN they SHALL verify connectivity and data flow with knowledge base and MCP servers
3. WHEN testing itinerary functionality THEN tests SHALL validate complete 3-day itineraries for various MBTI personality types
4. WHEN testing session assignment logic THEN tests SHALL verify strict adherence to morning/afternoon/night assignment rules
5. WHEN testing error scenarios THEN tests SHALL verify graceful handling of knowledge base failures and malformed data
6. WHEN performance testing is conducted THEN it SHALL validate response times under expected load conditions
7. WHEN security testing is performed THEN it SHALL verify authentication, authorization, and data protection
8. IF test failures occur THEN they SHALL provide clear diagnostic information for debugging
9. WHEN regression testing is automated THEN it SHALL run on every code change and deployment
10. IF quality gates fail THEN the system SHALL prevent deployment until issues are resolved