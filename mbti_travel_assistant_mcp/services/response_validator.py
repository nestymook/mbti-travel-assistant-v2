"""
Response Validation Service

This module provides comprehensive validation for API responses including
JSON schema validation, size validation, and structure validation.

Implements requirements 4.8, 7.8:
- JSON schema validation for output responses
- Response size and structure validation  
- Fallback response generation for edge cases
"""

import json
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of response validation."""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    size_bytes: int
    
    
class ResponseValidator:
    """
    Service for validating API responses against schema and size constraints.
    
    Implements requirement 4.8: JSON schema validation for output responses
    Implements requirement 7.8: response size and structure validation
    """
    
    # Maximum response size in bytes (1MB)
    MAX_RESPONSE_SIZE = 1024 * 1024
    
    # Maximum number of candidates
    MAX_CANDIDATES = 19
    
    # JSON Schema for restaurant recommendation response
    RESPONSE_SCHEMA = {
        "type": "object",
        "required": ["recommendation", "candidates", "metadata"],
        "properties": {
            "recommendation": {
                "oneOf": [
                    {"type": "null"},
                    {"$ref": "#/definitions/restaurant"}
                ]
            },
            "candidates": {
                "type": "array",
                "maxItems": MAX_CANDIDATES,
                "items": {"$ref": "#/definitions/restaurant"}
            },
            "metadata": {"$ref": "#/definitions/metadata"},
            "error": {"$ref": "#/definitions/error"}
        },
        "additionalProperties": False,
        "definitions": {
            "restaurant": {
                "type": "object",
                "required": [
                    "id", "name", "address", "district", "mealType",
                    "sentiment", "priceRange", "operatingHours", "locationCategory"
                ],
                "properties": {
                    "id": {"type": "string", "minLength": 1},
                    "name": {"type": "string", "minLength": 1},
                    "address": {"type": "string"},
                    "district": {"type": "string"},
                    "mealType": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "sentiment": {"$ref": "#/definitions/sentiment"},
                    "priceRange": {"type": "string"},
                    "operatingHours": {
                        "type": "object",
                        "additionalProperties": {"type": "string"}
                    },
                    "locationCategory": {"type": "string"},
                    "cuisineType": {"type": "string"},
                    "rating": {"type": "number", "minimum": 0, "maximum": 5},
                    "imageUrl": {"type": "string", "format": "uri"}
                },
                "additionalProperties": False
            },
            "sentiment": {
                "type": "object",
                "required": ["likes", "dislikes", "neutral", "total"],
                "properties": {
                    "likes": {"type": "integer", "minimum": 0},
                    "dislikes": {"type": "integer", "minimum": 0},
                    "neutral": {"type": "integer", "minimum": 0},
                    "total": {"type": "integer", "minimum": 0},
                    "positivePercentage": {"type": "number", "minimum": 0, "maximum": 100},
                    "likesPercentage": {"type": "number", "minimum": 0, "maximum": 100}
                },
                "additionalProperties": False
            },
            "metadata": {
                "type": "object",
                "required": ["searchCriteria", "totalFound", "timestamp"],
                "properties": {
                    "searchCriteria": {
                        "type": "object",
                        "properties": {
                            "district": {"type": ["string", "null"]},
                            "mealTime": {"type": ["string", "null"]},
                            "naturalLanguageQuery": {"type": ["string", "null"]}
                        }
                    },
                    "totalFound": {"type": "integer", "minimum": 0},
                    "timestamp": {"type": "string", "format": "date-time"},
                    "processingTimeMs": {"type": "number", "minimum": 0},
                    "correlationId": {"type": ["string", "null"]},
                    "mcpCalls": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "cacheHit": {"type": "boolean"},
                    "agentVersion": {"type": "string"},
                    "responseGenerated": {"type": "string"}
                },
                "additionalProperties": True
            },
            "error": {
                "type": "object",
                "required": ["errorType", "message", "suggestedActions"],
                "properties": {
                    "errorType": {"type": "string"},
                    "errorCode": {"type": "string"},
                    "message": {"type": "string"},
                    "suggestedActions": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "timestamp": {"type": "string", "format": "date-time"},
                    "details": {"type": "object"}
                },
                "additionalProperties": False
            }
        }
    }
    
    def __init__(self):
        """Initialize the response validator."""
        try:
            import jsonschema
            self.jsonschema = jsonschema
            self.validator = jsonschema.Draft7Validator(self.RESPONSE_SCHEMA)
        except ImportError:
            logger.warning("jsonschema not available, schema validation disabled")
            self.jsonschema = None
            self.validator = None
    
    def validate_response(self, response: Dict[str, Any]) -> ValidationResult:
        """
        Validate a complete response against schema and size constraints.
        
        Implements requirement 4.8: JSON schema validation for output responses
        
        Args:
            response: Response dictionary to validate
            
        Returns:
            ValidationResult with validation status and details
        """
        errors = []
        warnings = []
        
        # Calculate response size
        try:
            response_json = json.dumps(response, ensure_ascii=False)
            size_bytes = len(response_json.encode('utf-8'))
        except Exception as e:
            errors.append(f"Failed to serialize response to JSON: {str(e)}")
            size_bytes = 0
        
        # Validate response size
        if size_bytes > self.MAX_RESPONSE_SIZE:
            errors.append(f"Response size {size_bytes} bytes exceeds maximum {self.MAX_RESPONSE_SIZE} bytes")
        
        # Validate JSON schema if available
        if self.validator:
            schema_errors = list(self.validator.iter_errors(response))
            for error in schema_errors:
                errors.append(f"Schema validation error: {error.message} at {'.'.join(str(p) for p in error.path)}")
        
        # Validate structure manually
        structure_errors, structure_warnings = self._validate_structure(response)
        errors.extend(structure_errors)
        warnings.extend(structure_warnings)
        
        # Validate business rules
        business_errors, business_warnings = self._validate_business_rules(response)
        errors.extend(business_errors)
        warnings.extend(business_warnings)
        
        is_valid = len(errors) == 0
        
        if not is_valid:
            logger.error(f"Response validation failed: {errors}")
        elif warnings:
            logger.warning(f"Response validation warnings: {warnings}")
        
        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            size_bytes=size_bytes
        )
    
    def _validate_structure(self, response: Dict[str, Any]) -> Tuple[List[str], List[str]]:
        """
        Validate response structure manually.
        
        Args:
            response: Response dictionary to validate
            
        Returns:
            Tuple of (errors, warnings)
        """
        errors = []
        warnings = []
        
        # Check required top-level fields
        required_fields = ["recommendation", "candidates", "metadata"]
        for field in required_fields:
            if field not in response:
                errors.append(f"Missing required field: {field}")
        
        # Validate recommendation
        if "recommendation" in response:
            rec = response["recommendation"]
            if rec is not None:
                rec_errors, rec_warnings = self._validate_restaurant(rec, "recommendation")
                errors.extend(rec_errors)
                warnings.extend(rec_warnings)
        
        # Validate candidates
        if "candidates" in response:
            candidates = response["candidates"]
            if not isinstance(candidates, list):
                errors.append("Candidates must be a list")
            else:
                if len(candidates) > self.MAX_CANDIDATES:
                    errors.append(f"Too many candidates: {len(candidates)} > {self.MAX_CANDIDATES}")
                
                for i, candidate in enumerate(candidates):
                    cand_errors, cand_warnings = self._validate_restaurant(candidate, f"candidates[{i}]")
                    errors.extend(cand_errors)
                    warnings.extend(cand_warnings)
        
        # Validate metadata
        if "metadata" in response:
            meta_errors, meta_warnings = self._validate_metadata(response["metadata"])
            errors.extend(meta_errors)
            warnings.extend(meta_warnings)
        
        # Validate error if present
        if "error" in response:
            error_errors, error_warnings = self._validate_error(response["error"])
            errors.extend(error_errors)
            warnings.extend(error_warnings)
        
        return errors, warnings
    
    def _validate_restaurant(self, restaurant: Dict[str, Any], context: str) -> Tuple[List[str], List[str]]:
        """
        Validate restaurant object structure.
        
        Args:
            restaurant: Restaurant dictionary to validate
            context: Context for error messages
            
        Returns:
            Tuple of (errors, warnings)
        """
        errors = []
        warnings = []
        
        if not isinstance(restaurant, dict):
            errors.append(f"{context}: Restaurant must be an object")
            return errors, warnings
        
        # Check required fields
        required_fields = [
            "id", "name", "address", "district", "mealType",
            "sentiment", "priceRange", "operatingHours", "locationCategory"
        ]
        
        for field in required_fields:
            if field not in restaurant:
                errors.append(f"{context}: Missing required field '{field}'")
        
        # Validate specific fields
        if "id" in restaurant and not restaurant["id"]:
            errors.append(f"{context}: ID cannot be empty")
        
        if "name" in restaurant and not restaurant["name"]:
            errors.append(f"{context}: Name cannot be empty")
        
        if "mealType" in restaurant:
            meal_type = restaurant["mealType"]
            if not isinstance(meal_type, list):
                errors.append(f"{context}: mealType must be a list")
        
        if "sentiment" in restaurant:
            sent_errors, sent_warnings = self._validate_sentiment(restaurant["sentiment"], f"{context}.sentiment")
            errors.extend(sent_errors)
            warnings.extend(sent_warnings)
        
        if "rating" in restaurant:
            rating = restaurant["rating"]
            if not isinstance(rating, (int, float)) or rating < 0 or rating > 5:
                errors.append(f"{context}: Rating must be a number between 0 and 5")
        
        return errors, warnings
    
    def _validate_sentiment(self, sentiment: Dict[str, Any], context: str) -> Tuple[List[str], List[str]]:
        """
        Validate sentiment object structure.
        
        Args:
            sentiment: Sentiment dictionary to validate
            context: Context for error messages
            
        Returns:
            Tuple of (errors, warnings)
        """
        errors = []
        warnings = []
        
        if not isinstance(sentiment, dict):
            errors.append(f"{context}: Sentiment must be an object")
            return errors, warnings
        
        # Check required fields
        required_fields = ["likes", "dislikes", "neutral", "total"]
        for field in required_fields:
            if field not in sentiment:
                errors.append(f"{context}: Missing required field '{field}'")
        
        # Validate numeric fields
        for field in ["likes", "dislikes", "neutral", "total"]:
            if field in sentiment:
                value = sentiment[field]
                if not isinstance(value, int) or value < 0:
                    errors.append(f"{context}: {field} must be a non-negative integer")
        
        # Validate calculated totals (only if all values are valid integers)
        if all(field in sentiment for field in ["likes", "dislikes", "neutral", "total"]):
            try:
                likes = int(sentiment["likes"])
                dislikes = int(sentiment["dislikes"])
                neutral = int(sentiment["neutral"])
                total = int(sentiment["total"])
                
                calculated_total = likes + dislikes + neutral
                if total != calculated_total:
                    warnings.append(f"{context}: Total {total} doesn't match calculated total {calculated_total}")
            except (ValueError, TypeError):
                # Skip total validation if values are not numeric
                pass
        
        return errors, warnings
    
    def _validate_metadata(self, metadata: Dict[str, Any]) -> Tuple[List[str], List[str]]:
        """
        Validate metadata object structure.
        
        Args:
            metadata: Metadata dictionary to validate
            
        Returns:
            Tuple of (errors, warnings)
        """
        errors = []
        warnings = []
        
        if not isinstance(metadata, dict):
            errors.append("Metadata must be an object")
            return errors, warnings
        
        # Check required fields
        required_fields = ["searchCriteria", "totalFound", "timestamp"]
        for field in required_fields:
            if field not in metadata:
                errors.append(f"Metadata missing required field '{field}'")
        
        # Validate specific fields
        if "totalFound" in metadata:
            total_found = metadata["totalFound"]
            if not isinstance(total_found, int) or total_found < 0:
                errors.append("totalFound must be a non-negative integer")
        
        if "processingTimeMs" in metadata:
            processing_time = metadata["processingTimeMs"]
            if not isinstance(processing_time, (int, float)) or processing_time < 0:
                errors.append("processingTimeMs must be a non-negative number")
        
        if "timestamp" in metadata:
            timestamp = metadata["timestamp"]
            if not isinstance(timestamp, str):
                errors.append("timestamp must be a string")
            else:
                # Try to parse timestamp
                try:
                    datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                except ValueError:
                    errors.append("timestamp must be a valid ISO 8601 datetime")
        
        return errors, warnings
    
    def _validate_error(self, error: Dict[str, Any]) -> Tuple[List[str], List[str]]:
        """
        Validate error object structure.
        
        Args:
            error: Error dictionary to validate
            
        Returns:
            Tuple of (errors, warnings)
        """
        errors = []
        warnings = []
        
        if not isinstance(error, dict):
            errors.append("Error must be an object")
            return errors, warnings
        
        # Check required fields
        required_fields = ["errorType", "message", "suggestedActions"]
        for field in required_fields:
            if field not in error:
                errors.append(f"Error missing required field '{field}'")
        
        # Validate specific fields
        if "suggestedActions" in error:
            actions = error["suggestedActions"]
            if not isinstance(actions, list):
                errors.append("suggestedActions must be a list")
            elif not actions:
                warnings.append("suggestedActions is empty")
        
        return errors, warnings
    
    def _validate_business_rules(self, response: Dict[str, Any]) -> Tuple[List[str], List[str]]:
        """
        Validate business rules and constraints.
        
        Args:
            response: Response dictionary to validate
            
        Returns:
            Tuple of (errors, warnings)
        """
        errors = []
        warnings = []
        
        # Check that we have either a recommendation or an error
        has_recommendation = response.get("recommendation") is not None
        has_candidates = len(response.get("candidates", [])) > 0
        has_error = "error" in response
        
        if not has_recommendation and not has_candidates and not has_error:
            warnings.append("Response has no recommendation, candidates, or error - may be empty result")
        
        # If we have a recommendation, it should also be in candidates
        if has_recommendation and has_candidates:
            recommendation_id = response["recommendation"].get("id")
            candidate_ids = [c.get("id") for c in response["candidates"] if isinstance(c, dict)]
            
            if recommendation_id and recommendation_id not in candidate_ids:
                warnings.append("Recommendation is not included in candidates list")
        
        # Check metadata consistency
        if "metadata" in response:
            metadata = response["metadata"]
            total_found = metadata.get("totalFound", 0)
            actual_candidates = len(response.get("candidates", []))
            
            if total_found < actual_candidates:
                warnings.append(f"totalFound ({total_found}) is less than actual candidates ({actual_candidates})")
        
        return errors, warnings
    
    def create_fallback_response(
        self,
        error_message: str,
        correlation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a fallback response for edge cases.
        
        Implements requirement 7.8: fallback response generation for edge cases
        
        Args:
            error_message: Error message to include
            correlation_id: Request correlation ID
            
        Returns:
            Fallback response dictionary
        """
        current_time = datetime.utcnow()
        
        return {
            "recommendation": None,
            "candidates": [],
            "metadata": {
                "searchCriteria": {
                    "district": None,
                    "mealTime": None,
                    "naturalLanguageQuery": None
                },
                "totalFound": 0,
                "timestamp": current_time.isoformat() + "Z",
                "processingTimeMs": 0.0,
                "correlationId": correlation_id,
                "mcpCalls": [],
                "cacheHit": False,
                "agentVersion": "1.0.0",
                "responseGenerated": current_time.strftime("%Y-%m-%d %H:%M:%S UTC")
            },
            "error": {
                "errorType": "INTERNAL_ERROR",
                "errorCode": "INTERNAL_ERROR",
                "message": error_message,
                "suggestedActions": [
                    "Try again in a few moments",
                    "Contact support if the issue persists"
                ],
                "timestamp": current_time.isoformat() + "Z",
                "details": {
                    "fallback": True,
                    "generated_at": current_time.isoformat()
                }
            }
        }
    
    def sanitize_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitize response to ensure it meets size and structure constraints.
        
        Args:
            response: Response dictionary to sanitize
            
        Returns:
            Sanitized response dictionary
        """
        # Make a copy to avoid modifying the original
        sanitized = response.copy()
        
        # Limit candidates to maximum allowed
        if "candidates" in sanitized and isinstance(sanitized["candidates"], list):
            if len(sanitized["candidates"]) > self.MAX_CANDIDATES:
                logger.warning(f"Truncating candidates from {len(sanitized['candidates'])} to {self.MAX_CANDIDATES}")
                sanitized["candidates"] = sanitized["candidates"][:self.MAX_CANDIDATES]
        
        # Check size and truncate if necessary
        try:
            response_json = json.dumps(sanitized, ensure_ascii=False)
            size_bytes = len(response_json.encode('utf-8'))
            
            if size_bytes > self.MAX_RESPONSE_SIZE:
                logger.warning(f"Response size {size_bytes} exceeds limit, truncating")
                
                # Progressively remove candidates until size is acceptable
                while (len(sanitized.get("candidates", [])) > 0 and 
                       len(json.dumps(sanitized, ensure_ascii=False).encode('utf-8')) > self.MAX_RESPONSE_SIZE):
                    sanitized["candidates"].pop()
                
                # Update metadata to reflect truncation
                if "metadata" in sanitized:
                    sanitized["metadata"]["truncated"] = True
                    sanitized["metadata"]["originalCandidateCount"] = len(response.get("candidates", []))
        
        except Exception as e:
            logger.error(f"Failed to sanitize response: {str(e)}")
        
        return sanitized