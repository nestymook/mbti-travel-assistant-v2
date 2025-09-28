# Response Formatting Service Implementation

## Overview

This document describes the implementation of the response formatting service for the MBTI Travel Assistant MCP, which provides structured JSON response formatting for frontend consumption with comprehensive validation.

## Implementation Summary

### Task 7.1: JSON Response Formatter

**Location**: `services/response_formatter.py`

**Key Features Implemented**:

1. **Structured Response Formatting** (Requirement 4.1)
   - JSON response with "recommendation" and "candidates" top-level fields
   - Exactly 1 recommendation and up to 19 candidates
   - Complete restaurant details with all required fields

2. **Metadata Generation** (Requirement 4.5)
   - Search criteria with district, meal time, and natural language query
   - Timestamps in ISO 8601 format with UTC indicator
   - Processing time metrics and correlation IDs
   - MCP call tracking and cache hit indicators

3. **Error Response Formatting** (Requirement 4.7)
   - Standardized error codes using ErrorCode enum
   - Structured error messages with suggested actions
   - Timestamps and correlation tracking for errors
   - Fallback response generation for critical failures

4. **Restaurant Data Formatting** (Requirement 4.4)
   - All required fields: id, name, address, district, mealType, sentiment, priceRange, operatingHours, locationCategory
   - Optional fields: cuisineType, rating, imageUrl
   - Consistent operating hours formatting (e.g., "Mon-Fri: 07:00-11:30")
   - Enhanced sentiment data with calculated percentages

### Task 7.2: Response Validation

**Location**: `services/response_validator.py`

**Key Features Implemented**:

1. **JSON Schema Validation** (Requirement 4.8)
   - Comprehensive JSON schema for restaurant recommendation responses
   - Validation of all required fields and data types
   - Optional jsonschema library integration with graceful fallback

2. **Response Size and Structure Validation**
   - Maximum response size limit (1MB) with automatic truncation
   - Maximum candidates limit (19) with sanitization
   - Structure validation for all response components
   - Business rule validation (e.g., recommendation in candidates)

3. **Fallback Response Generation** (Requirement 7.8)
   - Standardized fallback responses for edge cases
   - Error response creation with appropriate error codes
   - Response sanitization to meet size constraints
   - Graceful handling of validation failures

## Key Components

### ResponseFormatter Class

```python
class ResponseFormatter:
    def format_response(self, response_data, request, start_time, correlation_id)
    def _format_candidates(self, candidates)
    def _format_restaurant(self, restaurant_data)
    def _format_operating_hours(self, hours_data)
    def _format_sentiment(self, sentiment_data)
    def _format_metadata(self, metadata, request, processing_time, correlation_id)
    def _format_error_with_code(self, error_data)
    def create_no_results_response(self, request, processing_time, correlation_id)
```

### ResponseValidator Class

```python
class ResponseValidator:
    def validate_response(self, response)
    def _validate_structure(self, response)
    def _validate_restaurant(self, restaurant, context)
    def _validate_sentiment(self, sentiment, context)
    def _validate_metadata(self, metadata)
    def _validate_business_rules(self, response)
    def create_fallback_response(self, error_message, correlation_id)
    def sanitize_response(self, response)
```

### ErrorCode Enum

Standardized error codes for consistent error handling:
- `VALIDATION_ERROR`
- `AUTHENTICATION_ERROR`
- `MCP_UNAVAILABLE`
- `PARSING_ERROR`
- `TIMEOUT_ERROR`
- `RATE_LIMIT_ERROR`
- `INTERNAL_ERROR`
- `NO_RESULTS_FOUND`
- `FORMATTING_ERROR`

## Integration

The ResponseFormatter integrates with ResponseValidator to provide:

1. **Automatic Validation**: All formatted responses are validated before return
2. **Sanitization**: Oversized responses are automatically truncated
3. **Fallback Handling**: Invalid responses trigger fallback response generation
4. **Warning Logging**: Validation warnings are logged for monitoring

## Testing

**Location**: `tests/test_response_validation.py`

**Test Coverage**:
- Valid response validation
- Invalid structure handling
- Business rule validation
- Size limit enforcement
- Fallback response generation
- Integration with ResponseFormatter

## Dependencies Added

- `jsonschema>=4.20.0` for JSON schema validation (optional)

## Usage Example

```python
from services.response_formatter import ResponseFormatter
from models.request_models import RecommendationRequest

formatter = ResponseFormatter()

response_data = {
    "recommendation": {...},
    "candidates": [...],
    "metadata": {...}
}

request = RecommendationRequest(district="Central district", meal_time="breakfast")
start_time = datetime.utcnow()

formatted_response = formatter.format_response(
    response_data, 
    request, 
    start_time, 
    "correlation-123"
)
```

## Requirements Satisfied

- ✅ **4.1**: JSON response with "recommendation" and "candidates" fields
- ✅ **4.2**: Exactly 1 restaurant object in recommendation field
- ✅ **4.3**: Exactly 19 restaurant objects in candidates (or fewer)
- ✅ **4.4**: Complete restaurant details with all required fields
- ✅ **4.5**: Metadata field with search criteria, total found, and timestamp
- ✅ **4.7**: Error field with error type, message, and suggested actions
- ✅ **4.8**: Properly formatted and validated JSON for frontend consumption
- ✅ **4.9**: Restaurant images and media URLs when available
- ✅ **4.10**: Consistently formatted operating hours
- ✅ **7.8**: Fallback response generation for edge cases

## Performance Considerations

1. **Response Size Monitoring**: Automatic size checking and truncation
2. **Validation Caching**: Schema validation results can be cached
3. **Graceful Degradation**: Continues operation even if validation fails
4. **Memory Efficiency**: Streaming validation for large responses

## Security Considerations

1. **Input Sanitization**: All input data is validated and sanitized
2. **Error Information**: Sensitive data is excluded from error responses
3. **Size Limits**: Prevents memory exhaustion from oversized responses
4. **Schema Validation**: Prevents injection attacks through structured validation