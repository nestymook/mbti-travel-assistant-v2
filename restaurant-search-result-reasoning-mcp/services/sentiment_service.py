"""
Sentiment analysis service for restaurant reasoning MCP server.

This module provides core sentiment analysis functionality including
sentiment score calculations, percentage calculations, and validation logic
for restaurant sentiment data processing.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

from models.restaurant_models import Restaurant, Sentiment, SentimentAnalysis
from models.validation_models import ValidationResult, ValidationError, ValidationErrorType


logger = logging.getLogger(__name__)


@dataclass
class SentimentScoreResult:
    """Result of sentiment score calculation with metadata."""
    score: float
    method: str
    total_responses: int
    is_valid: bool
    error_message: Optional[str] = None


class SentimentAnalysisService:
    """
    Service for analyzing restaurant sentiment data and calculating scores.
    
    Provides methods for sentiment score calculations, percentage calculations,
    and validation of sentiment data for restaurant recommendation algorithms.
    """
    
    def __init__(self, minimum_responses: int = 1):
        """
        Initialize sentiment analysis service.
        
        Args:
            minimum_responses: Minimum number of sentiment responses required
                             for valid sentiment calculation (default: 1)
        """
        self.minimum_responses = minimum_responses
        self.logger = logging.getLogger(__name__)
    
    def calculate_sentiment_score(self, sentiment: Sentiment) -> SentimentScoreResult:
        """
        Calculate sentiment score based on likes percentage.
        
        This method calculates the percentage of likes out of total responses
        as the primary sentiment score for ranking restaurants.
        
        Args:
            sentiment: Sentiment object with likes, dislikes, neutral counts
            
        Returns:
            SentimentScoreResult with score and metadata
            
        Raises:
            ValueError: If sentiment data is invalid
        """
        try:
            # Validate sentiment data
            validation_result = self._validate_sentiment_data(sentiment)
            if not validation_result.is_valid:
                error_msg = f"Invalid sentiment data: {validation_result.errors[0].message}"
                self.logger.warning(error_msg)
                return SentimentScoreResult(
                    score=0.0,
                    method="sentiment_likes",
                    total_responses=0,
                    is_valid=False,
                    error_message=error_msg
                )
            
            total_responses = sentiment.total_responses()
            
            # Check minimum responses requirement
            if total_responses < self.minimum_responses:
                error_msg = f"Insufficient responses: {total_responses} < {self.minimum_responses}"
                self.logger.debug(error_msg)
                return SentimentScoreResult(
                    score=0.0,
                    method="sentiment_likes",
                    total_responses=total_responses,
                    is_valid=False,
                    error_message=error_msg
                )
            
            # Calculate likes percentage
            score = sentiment.likes_percentage()
            
            self.logger.debug(
                f"Calculated sentiment score: {score:.2f}% "
                f"({sentiment.likes}/{total_responses} likes)"
            )
            
            return SentimentScoreResult(
                score=score,
                method="sentiment_likes",
                total_responses=total_responses,
                is_valid=True
            )
            
        except Exception as e:
            error_msg = f"Error calculating sentiment score: {str(e)}"
            self.logger.error(error_msg)
            return SentimentScoreResult(
                score=0.0,
                method="sentiment_likes",
                total_responses=0,
                is_valid=False,
                error_message=error_msg
            )
    
    def calculate_combined_score(self, sentiment: Sentiment) -> SentimentScoreResult:
        """
        Calculate combined sentiment score based on likes + neutral percentage.
        
        This method calculates the percentage of positive sentiment (likes + neutral)
        out of total responses for a more inclusive ranking approach.
        
        Args:
            sentiment: Sentiment object with likes, dislikes, neutral counts
            
        Returns:
            SentimentScoreResult with combined score and metadata
            
        Raises:
            ValueError: If sentiment data is invalid
        """
        try:
            # Validate sentiment data
            validation_result = self._validate_sentiment_data(sentiment)
            if not validation_result.is_valid:
                error_msg = f"Invalid sentiment data: {validation_result.errors[0].message}"
                self.logger.warning(error_msg)
                return SentimentScoreResult(
                    score=0.0,
                    method="combined_sentiment",
                    total_responses=0,
                    is_valid=False,
                    error_message=error_msg
                )
            
            total_responses = sentiment.total_responses()
            
            # Check minimum responses requirement
            if total_responses < self.minimum_responses:
                error_msg = f"Insufficient responses: {total_responses} < {self.minimum_responses}"
                self.logger.debug(error_msg)
                return SentimentScoreResult(
                    score=0.0,
                    method="combined_sentiment",
                    total_responses=total_responses,
                    is_valid=False,
                    error_message=error_msg
                )
            
            # Calculate combined positive percentage
            score = sentiment.combined_positive_percentage()
            
            self.logger.debug(
                f"Calculated combined score: {score:.2f}% "
                f"({sentiment.likes + sentiment.neutral}/{total_responses} positive)"
            )
            
            return SentimentScoreResult(
                score=score,
                method="combined_sentiment",
                total_responses=total_responses,
                is_valid=True
            )
            
        except Exception as e:
            error_msg = f"Error calculating combined score: {str(e)}"
            self.logger.error(error_msg)
            return SentimentScoreResult(
                score=0.0,
                method="combined_sentiment",
                total_responses=0,
                is_valid=False,
                error_message=error_msg
            )
    
    def get_sentiment_percentages(self, sentiment: Sentiment) -> Dict[str, float]:
        """
        Calculate all sentiment percentages for detailed analysis.
        
        Args:
            sentiment: Sentiment object with likes, dislikes, neutral counts
            
        Returns:
            Dictionary with percentage breakdowns for all sentiment types
        """
        try:
            total_responses = sentiment.total_responses()
            
            if total_responses == 0:
                return {
                    "likes_percentage": 0.0,
                    "dislikes_percentage": 0.0,
                    "neutral_percentage": 0.0,
                    "combined_positive_percentage": 0.0,
                    "total_responses": 0
                }
            
            likes_pct = (sentiment.likes / total_responses) * 100
            dislikes_pct = (sentiment.dislikes / total_responses) * 100
            neutral_pct = (sentiment.neutral / total_responses) * 100
            combined_positive_pct = ((sentiment.likes + sentiment.neutral) / total_responses) * 100
            
            return {
                "likes_percentage": round(likes_pct, 2),
                "dislikes_percentage": round(dislikes_pct, 2),
                "neutral_percentage": round(neutral_pct, 2),
                "combined_positive_percentage": round(combined_positive_pct, 2),
                "total_responses": total_responses
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating sentiment percentages: {str(e)}")
            return {
                "likes_percentage": 0.0,
                "dislikes_percentage": 0.0,
                "neutral_percentage": 0.0,
                "combined_positive_percentage": 0.0,
                "total_responses": 0
            }
    
    def rank_restaurants_by_score(
        self, 
        restaurants: List[Restaurant], 
        score_method: str = "sentiment_likes"
    ) -> List[Tuple[Restaurant, SentimentScoreResult]]:
        """
        Rank restaurants by sentiment score using specified method.
        
        Args:
            restaurants: List of Restaurant objects to rank
            score_method: Scoring method ("sentiment_likes" or "combined_sentiment")
            
        Returns:
            List of tuples (Restaurant, SentimentScoreResult) sorted by score descending
        """
        try:
            scored_restaurants = []
            
            for restaurant in restaurants:
                if score_method == "combined_sentiment":
                    score_result = self.calculate_combined_score(restaurant.sentiment)
                else:
                    score_result = self.calculate_sentiment_score(restaurant.sentiment)
                
                scored_restaurants.append((restaurant, score_result))
            
            # Sort by score (descending), then by total responses (descending) for tie-breaking
            scored_restaurants.sort(
                key=lambda x: (x[1].score, x[1].total_responses),
                reverse=True
            )
            
            self.logger.info(
                f"Ranked {len(scored_restaurants)} restaurants by {score_method}. "
                f"Top score: {scored_restaurants[0][1].score:.2f}% "
                f"(Restaurant: {scored_restaurants[0][0].name})"
            )
            
            return scored_restaurants
            
        except Exception as e:
            self.logger.error(f"Error ranking restaurants: {str(e)}")
            return []
    
    def validate_sentiment_data(self, sentiment: Sentiment) -> ValidationResult:
        """
        Public method to validate sentiment data structure and values.
        
        Args:
            sentiment: Sentiment object to validate
            
        Returns:
            ValidationResult with validation status and any errors
        """
        return self._validate_sentiment_data(sentiment)
    
    def analyze_restaurant_list(
        self, 
        restaurants: List[Restaurant], 
        ranking_method: str = "sentiment_likes"
    ) -> SentimentAnalysis:
        """
        Perform comprehensive sentiment analysis on a list of restaurants.
        
        Args:
            restaurants: List of Restaurant objects to analyze
            ranking_method: Method used for ranking analysis
            
        Returns:
            SentimentAnalysis object with aggregate statistics
        """
        try:
            if not restaurants:
                return SentimentAnalysis(
                    restaurant_count=0,
                    average_likes=0.0,
                    average_dislikes=0.0,
                    average_neutral=0.0,
                    top_sentiment_score=0.0,
                    bottom_sentiment_score=0.0,
                    ranking_method=ranking_method
                )
            
            # Calculate scores for all restaurants
            scored_restaurants = self.rank_restaurants_by_score(restaurants, ranking_method)
            valid_scores = [score.score for _, score in scored_restaurants if score.is_valid]
            
            # Calculate averages
            total_likes = sum(r.sentiment.likes for r in restaurants)
            total_dislikes = sum(r.sentiment.dislikes for r in restaurants)
            total_neutral = sum(r.sentiment.neutral for r in restaurants)
            restaurant_count = len(restaurants)
            
            avg_likes = total_likes / restaurant_count
            avg_dislikes = total_dislikes / restaurant_count
            avg_neutral = total_neutral / restaurant_count
            
            # Get top and bottom scores
            top_score = max(valid_scores) if valid_scores else 0.0
            bottom_score = min(valid_scores) if valid_scores else 0.0
            
            analysis = SentimentAnalysis(
                restaurant_count=restaurant_count,
                average_likes=round(avg_likes, 2),
                average_dislikes=round(avg_dislikes, 2),
                average_neutral=round(avg_neutral, 2),
                top_sentiment_score=round(top_score, 2),
                bottom_sentiment_score=round(bottom_score, 2),
                ranking_method=ranking_method
            )
            
            self.logger.info(
                f"Analyzed {restaurant_count} restaurants. "
                f"Score range: {bottom_score:.2f}% - {top_score:.2f}%"
            )
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error analyzing restaurant list: {str(e)}")
            return SentimentAnalysis(
                restaurant_count=0,
                average_likes=0.0,
                average_dislikes=0.0,
                average_neutral=0.0,
                top_sentiment_score=0.0,
                bottom_sentiment_score=0.0,
                ranking_method=ranking_method
            )
    
    def _validate_sentiment_data(self, sentiment: Sentiment) -> ValidationResult:
        """
        Internal method to validate sentiment data structure and values.
        
        Args:
            sentiment: Sentiment object to validate
            
        Returns:
            ValidationResult with validation status and any errors
        """
        result = ValidationResult(is_valid=True)
        
        try:
            # Check for negative values
            if sentiment.likes < 0:
                error = ValidationError(
                    restaurant_id="unknown",
                    field="sentiment.likes",
                    error_type=ValidationErrorType.INVALID_VALUE,
                    message="Likes count cannot be negative",
                    expected_value=">= 0",
                    actual_value=str(sentiment.likes)
                )
                result.add_error(error)
            
            if sentiment.dislikes < 0:
                error = ValidationError(
                    restaurant_id="unknown",
                    field="sentiment.dislikes",
                    error_type=ValidationErrorType.INVALID_VALUE,
                    message="Dislikes count cannot be negative",
                    expected_value=">= 0",
                    actual_value=str(sentiment.dislikes)
                )
                result.add_error(error)
            
            if sentiment.neutral < 0:
                error = ValidationError(
                    restaurant_id="unknown",
                    field="sentiment.neutral",
                    error_type=ValidationErrorType.INVALID_VALUE,
                    message="Neutral count cannot be negative",
                    expected_value=">= 0",
                    actual_value=str(sentiment.neutral)
                )
                result.add_error(error)
            
            # Check for zero total responses (warning, not error)
            total_responses = sentiment.total_responses()
            if total_responses == 0:
                result.add_warning("Sentiment has zero total responses")
            
            # Check for extremely large values (potential data corruption)
            max_reasonable_responses = 1000000  # 1 million responses per category
            if (sentiment.likes > max_reasonable_responses or 
                sentiment.dislikes > max_reasonable_responses or 
                sentiment.neutral > max_reasonable_responses):
                result.add_warning("Sentiment values are unusually large")
            
        except Exception as e:
            error = ValidationError(
                restaurant_id="unknown",
                field="sentiment",
                error_type=ValidationErrorType.STRUCTURE_ERROR,
                message=f"Error validating sentiment data: {str(e)}"
            )
            result.add_error(error)
        
        return result