# Requirements Document

## Introduction

This feature involves creating an MCP-enabled application that allows foundation models to search restaurant data stored in S3 by district and meal time. The application will use AWS Bedrock AgentCore, boto3, and Python to provide a comprehensive restaurant search service. The system will be containerized using Docker and serve requests through MCP (Model Context Protocol) tools, enabling AI models to query restaurant information based on district names and meal time analysis of operating hours.

The restaurant data is organized hierarchically with regions (Hong Kong Island, Kowloon, New Territories, Lantau) containing multiple districts, with each district having its own JSON file containing restaurant data. The system will read district configuration locally from master-config.json and regional config files, while restaurant data will be retrieved from S3 bucket restaurant-data-209803798463-us-east-1/restaurants/.

## Requirements

### Requirement 1

**User Story:** As a foundation model, I want to search for restaurants by district name, so that I can provide location-specific restaurant recommendations to users.

#### Acceptance Criteria

1. WHEN a district search request is made THEN the system SHALL load district configuration locally and retrieve restaurant data from S3 path restaurant-data-209803798463-us-east-1/restaurants/{region}/{district}.json
2. WHEN an invalid district name is provided THEN the system SHALL return an appropriate error message listing available districts
3. WHEN multiple districts are requested THEN the system SHALL return restaurants from all specified districts across all regions
4. WHEN the system starts THEN it SHALL load master-config.json and regional config files to understand available districts and their hierarchy
5. IF no restaurants exist in a district THEN the system SHALL return an empty result set with appropriate messaging

### Requirement 2

**User Story:** As a foundation model, I want to search for restaurants by meal time (breakfast, lunch, dinner), so that I can recommend restaurants that are open during specific meal times by examining their operating hours.

#### Acceptance Criteria

1. WHEN a breakfast search is requested THEN the system SHALL examine restaurant operatingHours and return restaurants if any operating hours fall within 07:00 - 11:29
2. WHEN a lunch search is requested THEN the system SHALL examine restaurant operatingHours and return restaurants if any operating hours fall within 11:30 - 17:29
3. WHEN a dinner search is requested THEN the system SHALL examine restaurant operatingHours and return restaurants if any operating hours fall within 17:30 - 22:30
4. WHEN examining operating hours THEN the system SHALL check "Mon - Fri", "Sat - Sun", and "Public Holiday" time ranges
5. WHEN operating hours contain multiple time ranges (e.g., ["11:30 - 15:30", "18:00 - 22:30"]) THEN the system SHALL return the restaurant if any time range overlaps with the meal time
6. IF any of a restaurant's operating hours fall within multiple meal periods THEN the system SHALL include it in results for all applicable meal times
7. IF operating hours data is missing or invalid THEN the system SHALL exclude the restaurant from meal-based searches

### Requirement 3

**User Story:** As a foundation model, I want to access restaurant data from S3 storage, so that I can work with the most current restaurant information.

#### Acceptance Criteria

1. WHEN the system starts THEN it SHALL connect to S3 bucket restaurant-data-209803798463-us-east-1/restaurants/
2. WHEN restaurant data is requested THEN the system SHALL retrieve JSON files from the S3 location
3. WHEN S3 data is unavailable THEN the system SHALL handle the error gracefully and return appropriate error messages
4. IF S3 credentials are invalid THEN the system SHALL return authentication error messages

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

**User Story:** As a foundation model, I want to search restaurants using only district and meal time criteria, so that I can provide focused restaurant recommendations based on location and dining time.

#### Acceptance Criteria

1. WHEN both district and meal time are specified THEN the system SHALL return restaurants that match both criteria
2. WHEN only district is specified THEN the system SHALL return all restaurants in that district regardless of meal time
3. WHEN only meal time is specified THEN the system SHALL examine operating hours and return restaurants from all districts that serve the specified meal
4. WHEN no restaurants match the specified criteria THEN the system SHALL return an empty result set with appropriate messaging

### Requirement 7

**User Story:** As a foundation model, I want to receive structured restaurant data with all relevant information, so that I can provide comprehensive restaurant details to users.

#### Acceptance Criteria

1. WHEN restaurant data is returned THEN it SHALL include id, name, address, mealType (array of cuisine types), sentiment (likes, dislikes, neutral), locationCategory, district, priceRange, and operatingHours
2. WHEN restaurant metadata is available THEN it SHALL include dataQuality, version, and qualityScore information from the metadata field
3. WHEN file metadata is returned THEN it SHALL include timestamp, version, district, locationCategory, recordCount, fileSize, sanitizedAt, and sanitizationVersion from the file's metadata section
4. WHEN operatingHours are returned THEN they SHALL include "Mon - Fri", "Sat - Sun", and "Public Holiday" with arrays of time ranges
5. IF any required data fields are missing THEN the system SHALL handle gracefully and indicate missing information

### Requirement 8

**User Story:** As a system integrator, I want the application to follow Bedrock AgentCore patterns, so that it integrates properly with AWS Bedrock services.

#### Acceptance Criteria

1. WHEN implementing the MCP server THEN it SHALL follow the patterns demonstrated in the AgentCore gateway tutorial
2. WHEN hosting the MCP server THEN it SHALL follow the patterns from the AgentCore runtime hosting tutorial
3. WHEN implementing authentication THEN it SHALL follow the inbound auth example patterns
4. IF AgentCore integration fails THEN the system SHALL provide detailed error messages for troubleshooting
### R
equirement 9

**User Story:** As a system administrator, I want the application to load district configuration from local files, so that the system understands the hierarchical structure of regions and districts.

#### Acceptance Criteria

1. WHEN the system starts THEN it SHALL load master-config.json to understand available regions and their config files
2. WHEN processing district searches THEN it SHALL load regional config files (hong-kong-island.json, kowloon.json, new-territories.json, lantau.json) to get district names and metadata
3. WHEN mapping district names to S3 paths THEN it SHALL use the region/district structure (e.g., hong-kong-island/admiralty.json)
4. IF district configuration files are missing or invalid THEN the system SHALL return appropriate error messages
5. WHEN district validation is needed THEN the system SHALL check against the loaded district configuration

### Requirement 9 - LLM Integration (CRITICAL)

**User Story:** As a foundation model, I want to process natural language queries and automatically call appropriate MCP tools, so that users can search restaurants using conversational language.

#### Acceptance Criteria

1. WHEN a natural language query is received (e.g., "Find restaurants in Central district") THEN the system SHALL parse the intent and extract relevant parameters
2. WHEN district names are mentioned in natural language THEN the system SHALL map them to the correct MCP tool parameters (e.g., "Central district" → `districts: ["Central district"]`)
3. WHEN meal types are mentioned in natural language THEN the system SHALL map them to valid meal type parameters (e.g., "breakfast places" → `meal_types: ["breakfast"]`)
4. WHEN both location and meal time are mentioned THEN the system SHALL use the combined search tool with appropriate parameters
5. WHEN ambiguous queries are received THEN the system SHALL ask for clarification or provide suggestions
6. WHEN invalid district names are mentioned THEN the system SHALL suggest valid alternatives from available districts
7. WHEN the query intent cannot be determined THEN the system SHALL provide helpful guidance on available search options

### Requirement 10 - AgentCore Foundation Model Configuration

**User Story:** As a system administrator, I want to configure a foundation model in AgentCore, so that natural language queries can be processed and converted to MCP tool calls.

#### Acceptance Criteria

1. WHEN AgentCore is configured THEN it SHALL include a foundation model specification (e.g., Claude 3.5 Sonnet)
2. WHEN the foundation model is configured THEN it SHALL have access to all available MCP tools and their parameter schemas
3. WHEN model parameters are set THEN they SHALL be optimized for restaurant search tasks (appropriate temperature, max tokens, etc.)
4. WHEN system prompts are configured THEN they SHALL include context about Hong Kong districts and restaurant search capabilities
5. WHEN tool calling is enabled THEN the model SHALL be able to invoke MCP tools with correct parameter formatting
6. IF model configuration fails THEN the system SHALL provide detailed error messages for troubleshooting

### Requirement 11 - Natural Language Processing Pipeline

**User Story:** As a foundation model, I want to understand restaurant search queries in natural language, so that I can provide intuitive conversational search capabilities.

#### Acceptance Criteria

1. WHEN processing "Find restaurants in [district]" queries THEN the system SHALL call `search_restaurants_by_district` with the specified district
2. WHEN processing "[meal type] restaurants" queries THEN the system SHALL call `search_restaurants_by_meal_type` with the appropriate meal type
3. WHEN processing combined queries like "breakfast places in Central" THEN the system SHALL call `search_restaurants_combined` with both parameters
4. WHEN processing cuisine-specific queries THEN the system SHALL search by district and filter results by cuisine type mentioned
5. WHEN processing time-specific queries THEN the system SHALL map time references to appropriate meal types (e.g., "morning" → "breakfast")
6. WHEN generating responses THEN the system SHALL format restaurant data in a user-friendly, conversational manner
7. WHEN no results are found THEN the system SHALL provide helpful suggestions for alternative searches

### Requirement 12 - AgentCore Runtime Integration

**User Story:** As a system integrator, I want AgentCore Runtime to properly bridge natural language queries to MCP tool calls, so that the complete restaurant search workflow functions seamlessly.

#### Acceptance Criteria

1. WHEN a user sends `{"input": {"prompt": "Find restaurants in Central district"}}` THEN AgentCore SHALL process the natural language and call the appropriate MCP tool
2. WHEN the foundation model generates MCP tool calls THEN AgentCore SHALL route them to the deployed MCP server
3. WHEN MCP tools return restaurant data THEN AgentCore SHALL pass the results back to the foundation model for response formatting
4. WHEN errors occur in the pipeline THEN AgentCore SHALL provide meaningful error messages to users
5. WHEN the system is under load THEN AgentCore SHALL handle concurrent requests efficiently
6. IF the MCP server is unavailable THEN AgentCore SHALL provide appropriate fallback responses

### Requirement 13 - Response Formatting and User Experience

**User Story:** As an end user, I want to receive well-formatted restaurant recommendations, so that I can easily understand and act on the search results.

#### Acceptance Criteria

1. WHEN restaurant results are returned THEN they SHALL be formatted in a conversational, easy-to-read manner
2. WHEN multiple restaurants are found THEN they SHALL be presented in a logical order (e.g., by district, then by name)
3. WHEN restaurant details are shown THEN they SHALL include key information like name, address, cuisine type, and operating hours
4. WHEN operating hours are displayed THEN they SHALL be formatted in a user-friendly way (e.g., "Open for breakfast: Mon-Fri 7:00-11:30")
5. WHEN no restaurants match the criteria THEN the response SHALL suggest alternative searches or nearby options
6. WHEN errors occur THEN the error messages SHALL be user-friendly and provide guidance on how to refine the search