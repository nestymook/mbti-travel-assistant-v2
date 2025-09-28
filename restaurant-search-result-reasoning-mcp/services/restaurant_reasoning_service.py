"""
Restaurant reasoning service for intelligent recommendation analysis.

This module provides the core business logic for restaurant sentiment analysis
and recommendation, integrating validation, sentiment analysis, and recommendation
algorithms to provide structured recommendation results.
"""

import json
import logging
from typing import List, Dict, Any, Optional, Union
from dataclasses import asdict

from models.restaurant_models import Restaurant, Sentiment, RecommendationResult, SentimentAnalysis
from models.validation_models import ValidationResult, ValidationError, ValidationErrorType
from services.validation_service import RestaurantDataValidator
from services.sentiment_service import SentimentAnalysisService
from services.recommendation_service import RecommendationAlgorithm


logger = logging.getLogger(__name__)


class RestaurantReasoningService:
    """
    Core service for restaurant sentiment analysis and intelligent recommendations.
    
    Integrates validation, sentiment analysis, and recommendation algorithms
    to provide comprehensive restaurant reasoning functionality for MCP tools.
    """
    
    def __init__(
        self, 
        minimum_responses: int = 1,
        default_candidate_count: int = 20,
        random_seed: Optional[int] = None,
        strict_validation: bool = False
    ):
        """
        Initialize the restaurant reasoning service.
        
        Args:
            minimum_responses: Minimum sentiment responses required for valid analysis
            default_candidate_count: Default number of candidates to select
            random_seed: Optional seed for reproducible random selection
            strict_validation: If True, treat validation warnings as errors
        """
        self.minimum_responses = minimum_responses
        self.default_candidate_count = default_candidate_count
        self.random_seed = random_seed
        self.strict_validation = strict_validation
        
        # Initialize service components
        self.validator = RestaurantDataValidator(strict_mode=strict_validation)
        self.sentiment_service = SentimentAnalysisService(minimum_responses=minimum_responses)
        self.recommendation_algorithm = RecommendationAlgorithm(random_seed=random_seed)
        
        self.logger = logging.getLogger(__name__)
        
        self.logger.info(
            f"Initialized RestaurantReasoningService with "
            f"min_responses={minimum_responses}, "
            f"candidate_count={default_candidate_count}, "
            f"random_seed={random_seed}, "
            f"strict_validation={strict_validation}"
        )
    
    def analyze_and_recommend(
        self, 
        restaurant_data: List[Dict[str, Any]], 
        ranking_method: str = "sentiment_likes",
        candidate_count: Optional[int] = None
    ) -> RecommendationResult:
        """
        Analyze restaurant sentiment data and provide intelligent recommendations.
        
        This is the main entry point for the reasoning service, integrating
        validation, sentiment analysis, and recommendation algorithms.
        
        Args:
            restaurant_data: List of restaurant dictionaries with sentiment data
            ranking_method: Ranking method ("sentiment_likes" or "combined_sentiment")
            candidate_count: Number of candidates to select (uses default if None)
            
        Returns:
            RecommendationResult with candidates, recommendation, and analysis
            
        Raises:
            ValueError: If restaurant data is invalid or no valid restaurants found
            
        Requirements: 1.1, 1.2, 1.6, 1.7, 2.1
        """
        try:
            self.logger.info(
                f"Starting restaurant analysis with {len(restaurant_data)} restaurants, "
                f"method={ranking_method}, candidate_count={candidate_count or self.default_candidate_count}"
            )
            
            # Step 1: Validate input data
            validation_result = self._validate_input_data(restaurant_data, ranking_method)
            if not validation_result.is_valid:
                error_summary = self._format_validation_errors(validation_result)
                raise ValueError(f"Invalid restaurant data: {error_summary}")
            
            # Step 2: Convert to Restaurant objects
            restaurants = self._convert_to_restaurant_objects(restaurant_data)
            
            # Step 3: Filter valid restaurants with sentiment data
            valid_restaurants = self._filter_valid_restaurants(restaurants)
            if not valid_restaurants:
                raise ValueError("No valid restaurants with sentiment data found")
            
            self.logger.info(
                f"Validated {len(valid_restaurants)} out of {len(restaurants)} restaurants"
            )
            
            # Step 4: Perform sentiment analysis and ranking
            candidate_count = candidate_count or self.default_candidate_count
            recommendation_result = self.recommendation_algorithm.analyze_and_recommend(
                restaurants=valid_restaurants,
                ranking_method=ranking_method,
                candidate_count=candidate_count
            )
            
            # Step 5: Enhance result with additional analysis
            enhanced_result = self._enhance_recommendation_result(
                recommendation_result, 
                restaurant_data, 
                valid_restaurants
            )
            
            self.logger.info(
                f"Generated recommendation: {enhanced_result.recommendation.name} "
                f"from {len(enhanced_result.candidates)} candidates"
            )
            
            return enhanced_result
            
        except Exception as e:
            self.logger.error(f"Error in analyze_and_recommend: {str(e)}")
            raise
    
    def analyze_sentiment_only(
        self, 
        restaurant_data: List[Dict[str, Any]], 
        ranking_method: str = "sentiment_likes"
    ) -> SentimentAnalysis:
        """
        Analyze restaurant sentiment data without providing recommendations.
        
        Args:
            restaurant_data: List of restaurant dictionaries with sentiment data
            ranking_method: Ranking method for analysis
            
        Returns:
            SentimentAnalysis object with aggregate statistics
            
        Raises:
            ValueError: If restaurant data is invalid
        """
        try:
            self.logger.info(
                f"Starting sentiment analysis for {len(restaurant_data)} restaurants, "
                f"method={ranking_method}"
            )
            
            # Validate and convert data
            validation_result = self._validate_input_data(restaurant_data, ranking_method)
            if not validation_result.is_valid:
                error_summary = self._format_validation_errors(validation_result)
                raise ValueError(f"Invalid restaurant data: {error_summary}")
            
            restaurants = self._convert_to_restaurant_objects(restaurant_data)
            valid_restaurants = self._filter_valid_restaurants(restaurants)
            
            # Perform sentiment analysis
            sentiment_analysis = self.sentiment_service.analyze_restaurant_list(
                valid_restaurants, ranking_method
            )
            
            self.logger.info(
                f"Completed sentiment analysis for {sentiment_analysis.restaurant_count} restaurants"
            )
            
            return sentiment_analysis
            
        except Exception as e:
            self.logger.error(f"Error in analyze_sentiment_only: {str(e)}")
            raise
    
    def validate_restaurant_data(self, restaurant_data: List[Dict[str, Any]]) -> ValidationResult:
        """
        Validate restaurant data structure and content.
        
        Args:
            restaurant_data: List of restaurant dictionaries to validate
            
        Returns:
            ValidationResult with validation status and errors
        """
        try:
            return self.validator.validate_restaurant_list(restaurant_data)
        except Exception as e:
            self.logger.error(f"Error validating restaurant data: {str(e)}")
            result = ValidationResult(is_valid=False, total_count=len(restaurant_data) if isinstance(restaurant_data, list) else 0)
            error = ValidationError(
                restaurant_id="validation",
                field="root",
                error_type=ValidationErrorType.STRUCTURE_ERROR,
                message=f"Validation error: {str(e)}"
            )
            result.add_error(error)
            return result
    
    def format_recommendation_response(
        self, 
        result: RecommendationResult, 
        include_analysis: bool = True
    ) -> str:
        """
        Format recommendation results into a structured JSON response.
        
        Args:
            result: RecommendationResult to format
            include_analysis: Whether to include detailed analysis summary
            
        Returns:
            JSON string with formatted recommendation response
        """
        try:
            response_data = {
                "recommendation": result.recommendation.to_dict(),
                "candidates": [restaurant.to_dict() for restaurant in result.candidates],
                "ranking_method": result.ranking_method,
                "candidate_count": len(result.candidates),
                "timestamp": self._get_current_timestamp()
            }
            
            if include_analysis:
                response_data["analysis_summary"] = result.analysis_summary
            
            return json.dumps(response_data, indent=2)
            
        except Exception as e:
            self.logger.error(f"Error formatting recommendation response: {str(e)}")
            # Return error response
            error_response = {
                "error": "Failed to format recommendation response",
                "message": str(e),
                "timestamp": self._get_current_timestamp()
            }
            return json.dumps(error_response, indent=2)
    
    def format_sentiment_response(self, analysis: SentimentAnalysis) -> str:
        """
        Format sentiment analysis results into a structured JSON response.
        
        Args:
            analysis: SentimentAnalysis to format
            
        Returns:
            JSON string with formatted sentiment analysis response
        """
        try:
            response_data = {
                "sentiment_analysis": analysis.to_dict(),
                "timestamp": self._get_current_timestamp()
            }
            
            return json.dumps(response_data, indent=2)
            
        except Exception as e:
            self.logger.error(f"Error formatting sentiment response: {str(e)}")
            # Return error response
            error_response = {
                "error": "Failed to format sentiment analysis response",
                "message": str(e),
                "timestamp": self._get_current_timestamp()
            }
            return json.dumps(error_response, indent=2)
    
    def format_error_response(
        self, 
        error_message: str, 
        error_type: str = "ValidationError",
        details: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Format error information into a structured JSON response.
        
        Args:
            error_message: Main error message
            error_type: Type of error (e.g., "ValidationError", "ProcessingError")
            details: Optional additional error details
            
        Returns:
            JSON string with formatted error response
        """
        try:
            error_response = {
                "error": {
                    "type": error_type,
                    "message": error_message,
                    "timestamp": self._get_current_timestamp()
                }
            }
            
            if details:
                error_response["error"]["details"] = details
            
            return json.dumps(error_response, indent=2)
            
        except Exception as e:
            # Fallback error response
            fallback_response = {
                "error": {
                    "type": "SystemError",
                    "message": f"Failed to format error response: {str(e)}",
                    "original_error": error_message,
                    "timestamp": self._get_current_timestamp()
                }
            }
            return json.dumps(fallback_response, indent=2)
    
    def _validate_input_data(
        self, 
        restaurant_data: List[Dict[str, Any]], 
        ranking_method: str
    ) -> ValidationResult:
        """
        Validate input data and parameters.
        
        Args:
            restaurant_data: Restaurant data to validate
            ranking_method: Ranking method to validate
            
        Returns:
            ValidationResult with validation status
        """
        # Validate ranking method
        valid_methods = ["sentiment_likes", "combined_sentiment"]
        if ranking_method not in valid_methods:
            result = ValidationResult(is_valid=False, total_count=0)
            error = ValidationError(
                restaurant_id="parameter",
                field="ranking_method",
                error_type=ValidationErrorType.INVALID_VALUE,
                message=f"Invalid ranking method: {ranking_method}",
                expected_value=f"one of {valid_methods}",
                actual_value=ranking_method
            )
            result.add_error(error)
            return result
        
        # Validate restaurant data structure
        return self.validator.validate_restaurant_list(restaurant_data)
    
    def _convert_to_restaurant_objects(self, restaurant_data: List[Dict[str, Any]]) -> List[Restaurant]:
        """
        Convert restaurant dictionaries to Restaurant objects.
        
        Args:
            restaurant_data: List of restaurant dictionaries
            
        Returns:
            List of Restaurant objects
        """
        restaurants = []
        
        for i, data in enumerate(restaurant_data):
            try:
                # Sanitize data first
                sanitized_data = self.validator.sanitize_restaurant_data(data)
                
                # Create Restaurant object
                restaurant = Restaurant.from_dict(sanitized_data)
                restaurants.append(restaurant)
                
            except Exception as e:
                self.logger.warning(
                    f"Failed to convert restaurant at index {i} to Restaurant object: {str(e)}"
                )
                # Skip invalid restaurants in non-strict mode
                if self.strict_validation:
                    raise ValueError(f"Failed to convert restaurant at index {i}: {str(e)}")
        
        return restaurants
    
    def _filter_valid_restaurants(self, restaurants: List[Restaurant]) -> List[Restaurant]:
        """
        Filter restaurants with valid sentiment data.
        
        Args:
            restaurants: List of Restaurant objects
            
        Returns:
            List of restaurants with valid sentiment data
        """
        valid_restaurants = []
        
        for restaurant in restaurants:
            # Check if restaurant has valid sentiment data
            if restaurant.sentiment.total_responses() >= self.minimum_responses:
                valid_restaurants.append(restaurant)
            else:
                self.logger.debug(
                    f"Filtered out restaurant {restaurant.name} "
                    f"(insufficient sentiment responses: {restaurant.sentiment.total_responses()})"
                )
        
        return valid_restaurants
    
    def _enhance_recommendation_result(
        self, 
        result: RecommendationResult, 
        original_data: List[Dict[str, Any]], 
        valid_restaurants: List[Restaurant]
    ) -> RecommendationResult:
        """
        Enhance recommendation result with additional analysis information.
        
        Args:
            result: Original RecommendationResult
            original_data: Original input data
            valid_restaurants: Filtered valid restaurants
            
        Returns:
            Enhanced RecommendationResult
        """
        # Add additional analysis information
        enhanced_summary = result.analysis_summary.copy()
        
        # Add data quality metrics
        enhanced_summary["data_quality"] = {
            "total_input_restaurants": len(original_data),
            "valid_restaurants": len(valid_restaurants),
            "filtered_restaurants": len(original_data) - len(valid_restaurants),
            "data_completeness_rate": len(valid_restaurants) / len(original_data) if original_data else 0.0
        }
        
        # Add recommendation confidence metrics
        if result.candidates:
            scores = self.recommendation_algorithm.calculate_ranking_scores(
                result.candidates, result.ranking_method
            )
            score_values = list(scores.values())
            
            if score_values:
                recommendation_score = scores.get(result.recommendation.id, 0.0)
                enhanced_summary["recommendation_confidence"] = {
                    "recommendation_score": recommendation_score,
                    "score_percentile": self._calculate_percentile(recommendation_score, score_values),
                    "score_above_average": recommendation_score > (sum(score_values) / len(score_values)),
                    "candidates_with_higher_score": sum(1 for s in score_values if s > recommendation_score)
                }
        
        # Create enhanced result
        enhanced_result = RecommendationResult(
            candidates=result.candidates,
            recommendation=result.recommendation,
            ranking_method=result.ranking_method,
            analysis_summary=enhanced_summary
        )
        
        return enhanced_result
    
    def _format_validation_errors(self, validation_result: ValidationResult) -> str:
        """
        Format validation errors into a readable summary.
        
        Args:
            validation_result: ValidationResult with errors
            
        Returns:
            Formatted error summary string
        """
        if not validation_result.errors:
            return "No validation errors"
        
        error_summary = f"{len(validation_result.errors)} validation errors found"
        
        # Group errors by type
        error_types = {}
        for error in validation_result.errors:
            error_type = error.error_type.value if hasattr(error.error_type, 'value') else str(error.error_type)
            if error_type not in error_types:
                error_types[error_type] = []
            error_types[error_type].append(error.message)
        
        # Add error type summary
        type_summaries = []
        for error_type, messages in error_types.items():
            type_summaries.append(f"{error_type}: {len(messages)} errors")
        
        if type_summaries:
            error_summary += f" ({', '.join(type_summaries)})"
        
        return error_summary
    
    def _calculate_percentile(self, value: float, values: List[float]) -> float:
        """
        Calculate percentile rank of a value within a list of values.
        
        Args:
            value: Value to calculate percentile for
            values: List of all values
            
        Returns:
            Percentile rank (0.0 to 100.0)
        """
        if not values:
            return 0.0
        
        sorted_values = sorted(values)
        rank = sum(1 for v in sorted_values if v <= value)
        percentile = (rank / len(sorted_values)) * 100
        
        return round(percentile, 2)
    
    def _get_current_timestamp(self) -> str:
        """
        Get current timestamp in ISO format.
        
        Returns:
            ISO formatted timestamp string
        """
        from datetime import datetime
        return datetime.utcnow().isoformat() + "Z"