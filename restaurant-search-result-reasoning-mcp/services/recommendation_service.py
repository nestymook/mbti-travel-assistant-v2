"""
Restaurant recommendation algorithm service.

This module implements the core recommendation algorithms for ranking restaurants
based on sentiment analysis and selecting candidates for recommendations.
"""

import random
from typing import List, Dict, Any, Optional
from models.restaurant_models import Restaurant, RecommendationResult, SentimentAnalysis


class RecommendationAlgorithm:
    """
    Core recommendation algorithm for restaurant sentiment analysis.
    
    Provides ranking methods based on sentiment likes and combined sentiment,
    candidate selection, and random recommendation logic.
    """
    
    def __init__(self, random_seed: Optional[int] = None):
        """
        Initialize recommendation algorithm.
        
        Args:
            random_seed: Optional seed for reproducible random selection.
        """
        self.random_seed = random_seed
        self._random = random.Random(random_seed)
    
    def rank_by_likes(self, restaurants: List[Restaurant]) -> List[Restaurant]:
        """
        Rank restaurants by sentiment likes in descending order.
        
        Algorithm:
        1. Sort restaurants by sentiment.likes in descending order
        2. Handle ties by secondary sort on total responses
        3. Return ranked list
        
        Args:
            restaurants: List of restaurants to rank.
            
        Returns:
            List of restaurants sorted by likes (highest first).
            
        Requirements: 1.2, 1.3
        """
        if not restaurants:
            return []
        
        # Filter out restaurants with invalid sentiment data
        valid_restaurants = [
            r for r in restaurants 
            if r.sentiment.total_responses() > 0
        ]
        
        # Sort by likes (descending), then by total responses (descending) for tie-breaking
        return sorted(
            valid_restaurants,
            key=lambda r: (r.sentiment.likes, r.sentiment.total_responses()),
            reverse=True
        )
    
    def rank_by_combined_sentiment(self, restaurants: List[Restaurant]) -> List[Restaurant]:
        """
        Rank restaurants by combined likes + neutral percentage.
        
        Algorithm:
        1. Calculate (likes + neutral) / total_responses for each restaurant
        2. Sort by percentage in descending order
        3. Handle ties by secondary sort on absolute likes count
        4. Return ranked list
        
        Args:
            restaurants: List of restaurants to rank.
            
        Returns:
            List of restaurants sorted by combined sentiment (highest first).
            
        Requirements: 1.2, 1.4
        """
        if not restaurants:
            return []
        
        # Filter out restaurants with invalid sentiment data
        valid_restaurants = [
            r for r in restaurants 
            if r.sentiment.total_responses() > 0
        ]
        
        def combined_score(restaurant: Restaurant) -> float:
            """Calculate combined sentiment score."""
            sentiment = restaurant.sentiment
            total = sentiment.total_responses()
            if total == 0:
                return 0.0
            return (sentiment.likes + sentiment.neutral) / total
        
        # Sort by combined score (descending), then by likes (descending) for tie-breaking
        return sorted(
            valid_restaurants,
            key=lambda r: (combined_score(r), r.sentiment.likes),
            reverse=True
        )
    
    def select_candidates(self, ranked_restaurants: List[Restaurant], count: int = 20) -> List[Restaurant]:
        """
        Select top candidates from ranked restaurant list.
        
        Args:
            ranked_restaurants: List of restaurants already ranked.
            count: Number of candidates to select (default 20).
            
        Returns:
            Top N restaurants from the ranked list.
            
        Requirements: 1.5, 1.8
        """
        if not ranked_restaurants:
            return []
        
        # Return all restaurants if fewer than requested count
        if len(ranked_restaurants) <= count:
            return ranked_restaurants.copy()
        
        # Return top N candidates
        return ranked_restaurants[:count]
    
    def random_select(self, candidates: List[Restaurant]) -> Restaurant:
        """
        Randomly select one restaurant from candidates.
        
        Args:
            candidates: List of candidate restaurants.
            
        Returns:
            Randomly selected restaurant.
            
        Raises:
            ValueError: If candidates list is empty.
            
        Requirements: 1.6
        """
        if not candidates:
            raise ValueError("Cannot select from empty candidates list")
        
        return self._random.choice(candidates)
    
    def calculate_ranking_scores(self, restaurants: List[Restaurant], method: str) -> Dict[str, float]:
        """
        Calculate ranking scores for restaurants based on method.
        
        Args:
            restaurants: List of restaurants to score.
            method: Ranking method ("sentiment_likes" or "combined_sentiment").
            
        Returns:
            Dictionary mapping restaurant IDs to their scores.
        """
        scores = {}
        
        for restaurant in restaurants:
            if restaurant.sentiment.total_responses() == 0:
                scores[restaurant.id] = 0.0
                continue
                
            if method == "sentiment_likes":
                scores[restaurant.id] = restaurant.sentiment.likes_percentage()
            elif method == "combined_sentiment":
                scores[restaurant.id] = restaurant.sentiment.combined_positive_percentage()
            else:
                scores[restaurant.id] = 0.0
        
        return scores
    
    def analyze_and_recommend(
        self, 
        restaurants: List[Restaurant], 
        ranking_method: str = "sentiment_likes",
        candidate_count: int = 20
    ) -> RecommendationResult:
        """
        Complete analysis and recommendation workflow.
        
        Args:
            restaurants: List of restaurants to analyze.
            ranking_method: Method for ranking ("sentiment_likes" or "combined_sentiment").
            candidate_count: Number of candidates to select.
            
        Returns:
            RecommendationResult with candidates and recommendation.
            
        Raises:
            ValueError: If no valid restaurants or invalid ranking method.
            
        Requirements: 1.1, 1.2, 1.5, 1.6, 1.7
        """
        if not restaurants:
            raise ValueError("No restaurants provided for analysis")
        
        # Rank restaurants based on method
        if ranking_method == "sentiment_likes":
            ranked_restaurants = self.rank_by_likes(restaurants)
        elif ranking_method == "combined_sentiment":
            ranked_restaurants = self.rank_by_combined_sentiment(restaurants)
        else:
            raise ValueError(f"Invalid ranking method: {ranking_method}")
        
        if not ranked_restaurants:
            raise ValueError("No valid restaurants with sentiment data found")
        
        # Select top candidates
        candidates = self.select_candidates(ranked_restaurants, candidate_count)
        
        # Random recommendation from candidates
        recommendation = self.random_select(candidates)
        
        # Generate analysis summary
        analysis_summary = self._generate_analysis_summary(
            restaurants, ranked_restaurants, candidates, ranking_method
        )
        
        return RecommendationResult(
            candidates=candidates,
            recommendation=recommendation,
            ranking_method=ranking_method,
            analysis_summary=analysis_summary
        )
    
    def _generate_analysis_summary(
        self,
        original_restaurants: List[Restaurant],
        ranked_restaurants: List[Restaurant],
        candidates: List[Restaurant],
        ranking_method: str
    ) -> Dict[str, Any]:
        """
        Generate analysis summary for recommendation result.
        
        Args:
            original_restaurants: Original input restaurants.
            ranked_restaurants: Restaurants after ranking.
            candidates: Selected candidates.
            ranking_method: Method used for ranking.
            
        Returns:
            Dictionary containing analysis metadata.
        """
        # Calculate sentiment statistics
        valid_restaurants = [r for r in original_restaurants if r.sentiment.total_responses() > 0]
        
        if not valid_restaurants:
            return {
                "total_restaurants": len(original_restaurants),
                "valid_restaurants": 0,
                "candidates_selected": len(candidates),
                "ranking_method": ranking_method,
                "average_sentiment": {},
                "top_score": 0.0,
                "bottom_score": 0.0
            }
        
        # Calculate average sentiment
        total_likes = sum(r.sentiment.likes for r in valid_restaurants)
        total_dislikes = sum(r.sentiment.dislikes for r in valid_restaurants)
        total_neutral = sum(r.sentiment.neutral for r in valid_restaurants)
        count = len(valid_restaurants)
        
        # Calculate scores for top and bottom
        scores = self.calculate_ranking_scores(valid_restaurants, ranking_method)
        score_values = list(scores.values())
        
        return {
            "total_restaurants": len(original_restaurants),
            "valid_restaurants": len(valid_restaurants),
            "candidates_selected": len(candidates),
            "ranking_method": ranking_method,
            "average_sentiment": {
                "likes": total_likes / count,
                "dislikes": total_dislikes / count,
                "neutral": total_neutral / count
            },
            "top_score": max(score_values) if score_values else 0.0,
            "bottom_score": min(score_values) if score_values else 0.0,
            "score_range": max(score_values) - min(score_values) if score_values else 0.0
        }


def create_sentiment_analysis(
    restaurants: List[Restaurant], 
    ranking_method: str
) -> SentimentAnalysis:
    """
    Create aggregate sentiment analysis for a list of restaurants.
    
    Args:
        restaurants: List of restaurants to analyze.
        ranking_method: Method used for ranking.
        
    Returns:
        SentimentAnalysis object with aggregate statistics.
    """
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
    
    # Filter valid restaurants
    valid_restaurants = [r for r in restaurants if r.sentiment.total_responses() > 0]
    
    if not valid_restaurants:
        return SentimentAnalysis(
            restaurant_count=len(restaurants),
            average_likes=0.0,
            average_dislikes=0.0,
            average_neutral=0.0,
            top_sentiment_score=0.0,
            bottom_sentiment_score=0.0,
            ranking_method=ranking_method
        )
    
    # Calculate averages
    count = len(valid_restaurants)
    avg_likes = sum(r.sentiment.likes for r in valid_restaurants) / count
    avg_dislikes = sum(r.sentiment.dislikes for r in valid_restaurants) / count
    avg_neutral = sum(r.sentiment.neutral for r in valid_restaurants) / count
    
    # Calculate sentiment scores based on method
    algorithm = RecommendationAlgorithm()
    scores = algorithm.calculate_ranking_scores(valid_restaurants, ranking_method)
    score_values = list(scores.values())
    
    return SentimentAnalysis(
        restaurant_count=len(restaurants),
        average_likes=avg_likes,
        average_dislikes=avg_dislikes,
        average_neutral=avg_neutral,
        top_sentiment_score=max(score_values) if score_values else 0.0,
        bottom_sentiment_score=min(score_values) if score_values else 0.0,
        ranking_method=ranking_method
    )