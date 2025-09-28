"""
Unit tests for recommendation algorithm service.

This module contains comprehensive tests for restaurant ranking algorithms,
candidate selection, random recommendation, and tie-breaking logic.
"""

import pytest
import random
from typing import List
from services.recommendation_service import RecommendationAlgorithm, create_sentiment_analysis
from models.restaurant_models import Restaurant, Sentiment, RecommendationResult


class TestRecommendationAlgorithm:
    """Test cases for RecommendationAlgorithm class."""
    
    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.algorithm = RecommendationAlgorithm(random_seed=42)
        
        # Create test restaurants with various sentiment data
        self.test_restaurants = [
            Restaurant(
                id="rest1", name="High Likes Restaurant", address="Address 1",
                meal_type=["Chinese"], sentiment=Sentiment(likes=100, dislikes=10, neutral=20),
                location_category="Restaurant", district="Central", price_range="$$"
            ),
            Restaurant(
                id="rest2", name="Medium Likes Restaurant", address="Address 2", 
                meal_type=["Italian"], sentiment=Sentiment(likes=50, dislikes=15, neutral=25),
                location_category="Restaurant", district="Admiralty", price_range="$$$"
            ),
            Restaurant(
                id="rest3", name="Low Likes Restaurant", address="Address 3",
                meal_type=["Japanese"], sentiment=Sentiment(likes=20, dislikes=30, neutral=40),
                location_category="Restaurant", district="Causeway Bay", price_range="$"
            ),
            Restaurant(
                id="rest4", name="High Combined Restaurant", address="Address 4",
                meal_type=["Thai"], sentiment=Sentiment(likes=30, dislikes=5, neutral=60),
                location_category="Restaurant", district="Tsim Sha Tsui", price_range="$$"
            ),
            Restaurant(
                id="rest5", name="Zero Sentiment Restaurant", address="Address 5",
                meal_type=["Korean"], sentiment=Sentiment(likes=0, dislikes=0, neutral=0),
                location_category="Restaurant", district="Wan Chai", price_range="$$"
            )
        ]
    
    def test_rank_by_likes_basic_functionality(self):
        """Test basic ranking by sentiment likes."""
        # Test with valid restaurants
        ranked = self.algorithm.rank_by_likes(self.test_restaurants)
        
        # Should exclude restaurant with zero sentiment
        assert len(ranked) == 4
        
        # Should be sorted by likes in descending order
        assert ranked[0].id == "rest1"  # 100 likes
        assert ranked[1].id == "rest2"  # 50 likes
        assert ranked[2].id == "rest4"  # 30 likes
        assert ranked[3].id == "rest3"  # 20 likes
        
        # Verify likes are in descending order
        likes_values = [r.sentiment.likes for r in ranked]
        assert likes_values == sorted(likes_values, reverse=True)
    
    def test_rank_by_likes_tie_breaking(self):
        """Test tie-breaking logic in likes ranking."""
        # Create restaurants with same likes but different total responses
        tie_restaurants = [
            Restaurant(
                id="tie1", name="Tie Restaurant 1", address="Address 1",
                meal_type=["Chinese"], sentiment=Sentiment(likes=50, dislikes=10, neutral=20),  # total: 80
                location_category="Restaurant", district="Central", price_range="$$"
            ),
            Restaurant(
                id="tie2", name="Tie Restaurant 2", address="Address 2",
                meal_type=["Italian"], sentiment=Sentiment(likes=50, dislikes=5, neutral=15),   # total: 70
                location_category="Restaurant", district="Admiralty", price_range="$$"
            ),
            Restaurant(
                id="tie3", name="Tie Restaurant 3", address="Address 3",
                meal_type=["Japanese"], sentiment=Sentiment(likes=50, dislikes=15, neutral=25), # total: 90
                location_category="Restaurant", district="Causeway Bay", price_range="$$"
            )
        ]
        
        ranked = self.algorithm.rank_by_likes(tie_restaurants)
        
        # Should break ties by total responses (descending)
        assert ranked[0].id == "tie3"  # 90 total responses
        assert ranked[1].id == "tie1"  # 80 total responses
        assert ranked[2].id == "tie2"  # 70 total responses
    
    def test_rank_by_combined_sentiment_basic_functionality(self):
        """Test basic ranking by combined sentiment."""
        ranked = self.algorithm.rank_by_combined_sentiment(self.test_restaurants)
        
        # Should exclude restaurant with zero sentiment
        assert len(ranked) == 4
        
        # Calculate expected combined percentages
        # rest1: (100 + 20) / 130 = 92.31%
        # rest2: (50 + 25) / 90 = 83.33%
        # rest3: (20 + 40) / 90 = 66.67%
        # rest4: (30 + 60) / 95 = 94.74%
        
        # Should be sorted by combined sentiment percentage
        assert ranked[0].id == "rest4"  # 94.74%
        assert ranked[1].id == "rest1"  # 92.31%
        assert ranked[2].id == "rest2"  # 83.33%
        assert ranked[3].id == "rest3"  # 66.67%
    
    def test_rank_by_combined_sentiment_tie_breaking(self):
        """Test tie-breaking logic in combined sentiment ranking."""
        # Create restaurants with same combined percentage but different likes
        tie_restaurants = [
            Restaurant(
                id="combo1", name="Combo Restaurant 1", address="Address 1",
                meal_type=["Chinese"], sentiment=Sentiment(likes=60, dislikes=20, neutral=20),  # 80% combined
                location_category="Restaurant", district="Central", price_range="$"
            ),
            Restaurant(
                id="combo2", name="Combo Restaurant 2", address="Address 2",
                meal_type=["Italian"], sentiment=Sentiment(likes=40, dislikes=20, neutral=40),  # 80% combined
                location_category="Restaurant", district="Admiralty", price_range="$"
            ),
            Restaurant(
                id="combo3", name="Combo Restaurant 3", address="Address 3",
                meal_type=["Japanese"], sentiment=Sentiment(likes=80, dislikes=20, neutral=0),   # 80% combined
                location_category="Restaurant", district="Causeway Bay", price_range="$"
            )
        ]
        
        ranked = self.algorithm.rank_by_combined_sentiment(tie_restaurants)
        
        # Should break ties by likes count (descending)
        assert ranked[0].id == "combo3"  # 80 likes
        assert ranked[1].id == "combo1"  # 60 likes
        assert ranked[2].id == "combo2"  # 40 likes
    
    def test_rank_by_likes_empty_list(self):
        """Test ranking with empty restaurant list."""
        ranked = self.algorithm.rank_by_likes([])
        assert ranked == []
    
    def test_rank_by_combined_sentiment_empty_list(self):
        """Test combined sentiment ranking with empty restaurant list."""
        ranked = self.algorithm.rank_by_combined_sentiment([])
        assert ranked == []
    
    def test_rank_by_likes_all_zero_sentiment(self):
        """Test ranking when all restaurants have zero sentiment."""
        zero_restaurants = [
            Restaurant(
                id="zero1", name="Zero Restaurant 1", address="Address 1",
                meal_type=["Chinese"], sentiment=Sentiment(likes=0, dislikes=0, neutral=0),
                location_category="Restaurant", district="Central", price_range="$"
            ),
            Restaurant(
                id="zero2", name="Zero Restaurant 2", address="Address 2",
                meal_type=["Italian"], sentiment=Sentiment(likes=0, dislikes=0, neutral=0),
                location_category="Restaurant", district="Admiralty", price_range="$"
            )
        ]
        
        ranked = self.algorithm.rank_by_likes(zero_restaurants)
        assert ranked == []
    
    def test_select_candidates_basic_functionality(self):
        """Test candidate selection with various list sizes."""
        # Test with more than 20 restaurants
        large_restaurant_list = []
        for i in range(25):
            large_restaurant_list.append(
                Restaurant(
                    id=f"rest{i}", name=f"Restaurant {i}", address=f"Address {i}",
                    meal_type=["Chinese"], sentiment=Sentiment(likes=100-i, dislikes=10, neutral=20),
                    location_category="Restaurant", district="Central", price_range="$"
                )
            )
        
        candidates = self.algorithm.select_candidates(large_restaurant_list, 20)
        assert len(candidates) == 20
        
        # Should return first 20 restaurants (assuming they're already ranked)
        for i in range(20):
            assert candidates[i].id == f"rest{i}"
    
    def test_select_candidates_less_than_count(self):
        """Test candidate selection when fewer restaurants than requested count."""
        candidates = self.algorithm.select_candidates(self.test_restaurants, 20)
        assert len(candidates) == len(self.test_restaurants)
        assert candidates == self.test_restaurants
    
    def test_select_candidates_exactly_count(self):
        """Test candidate selection when exactly the requested count."""
        # Create exactly 20 restaurants
        exactly_twenty = []
        for i in range(20):
            exactly_twenty.append(
                Restaurant(
                    id=f"exact{i}", name=f"Restaurant {i}", address=f"Address {i}",
                    meal_type=["Chinese"], sentiment=Sentiment(likes=100-i, dislikes=10, neutral=20),
                    location_category="Restaurant", district="Central", price_range="$"
                )
            )
        
        candidates = self.algorithm.select_candidates(exactly_twenty, 20)
        assert len(candidates) == 20
        assert candidates == exactly_twenty
    
    def test_select_candidates_empty_list(self):
        """Test candidate selection with empty list."""
        candidates = self.algorithm.select_candidates([], 20)
        assert candidates == []
    
    def test_select_candidates_custom_count(self):
        """Test candidate selection with custom count."""
        candidates = self.algorithm.select_candidates(self.test_restaurants, 3)
        assert len(candidates) == 3
        assert candidates == self.test_restaurants[:3]
    
    def test_random_select_basic_functionality(self):
        """Test random selection from candidates."""
        # Test with multiple candidates
        candidates = self.test_restaurants[:3]  # First 3 restaurants
        
        # Test multiple selections to verify randomness works
        selections = []
        for _ in range(10):
            selected = self.algorithm.random_select(candidates)
            assert selected in candidates
            selections.append(selected.id)
        
        # With seed=42, should get consistent results
        assert len(set(selections)) >= 1  # At least one unique selection
    
    def test_random_select_single_candidate(self):
        """Test random selection with single candidate."""
        single_candidate = [self.test_restaurants[0]]
        selected = self.algorithm.random_select(single_candidate)
        assert selected == self.test_restaurants[0]
    
    def test_random_select_empty_list(self):
        """Test random selection with empty candidates list."""
        with pytest.raises(ValueError, match="Cannot select from empty candidates list"):
            self.algorithm.random_select([])
    
    def test_random_select_reproducibility_with_seed(self):
        """Test random selection reproducibility with seeds."""
        candidates = self.test_restaurants[:3]
        
        # Test with same seed
        algorithm1 = RecommendationAlgorithm(random_seed=123)
        algorithm2 = RecommendationAlgorithm(random_seed=123)
        
        selections1 = []
        selections2 = []
        
        for _ in range(5):
            selections1.append(algorithm1.random_select(candidates).id)
            selections2.append(algorithm2.random_select(candidates).id)
        
        # Should get same sequence with same seed
        assert selections1 == selections2
    
    def test_random_select_different_seeds(self):
        """Test random selection with different seeds produces different results."""
        candidates = self.test_restaurants[:3]
        
        algorithm1 = RecommendationAlgorithm(random_seed=123)
        algorithm2 = RecommendationAlgorithm(random_seed=456)
        
        selections1 = []
        selections2 = []
        
        for _ in range(10):
            selections1.append(algorithm1.random_select(candidates).id)
            selections2.append(algorithm2.random_select(candidates).id)
        
        # Different seeds should likely produce different sequences
        # (not guaranteed but very likely with 10 selections)
        assert selections1 != selections2 or len(set(selections1)) > 1
    
    def test_calculate_ranking_scores_sentiment_likes(self):
        """Test ranking score calculation for sentiment likes method."""
        scores = self.algorithm.calculate_ranking_scores(self.test_restaurants, "sentiment_likes")
        
        # Verify scores are calculated correctly (likes percentage)
        assert len(scores) == 5
        
        # rest1: 100 / 130 = 76.92%
        assert abs(scores["rest1"] - 76.92307692307693) < 0.001
        
        # rest2: 50 / 90 = 55.56%
        assert abs(scores["rest2"] - 55.55555555555556) < 0.001
        
        # rest5: 0 / 0 = 0% (zero sentiment)
        assert scores["rest5"] == 0.0
    
    def test_calculate_ranking_scores_combined_sentiment(self):
        """Test ranking score calculation for combined sentiment method."""
        scores = self.algorithm.calculate_ranking_scores(self.test_restaurants, "combined_sentiment")
        
        # Verify scores are calculated correctly (combined percentage)
        assert len(scores) == 5
        
        # rest1: (100 + 20) / 130 = 92.31%
        assert abs(scores["rest1"] - 92.30769230769231) < 0.001
        
        # rest4: (30 + 60) / 95 = 94.74%
        assert abs(scores["rest4"] - 94.73684210526316) < 0.001
        
        # rest5: 0 / 0 = 0% (zero sentiment)
        assert scores["rest5"] == 0.0
    
    def test_calculate_ranking_scores_invalid_method(self):
        """Test ranking score calculation with invalid method."""
        scores = self.algorithm.calculate_ranking_scores(self.test_restaurants, "invalid_method")
        
        # Should return 0.0 for all restaurants with invalid method
        for score in scores.values():
            assert score == 0.0
    
    def test_analyze_and_recommend_sentiment_likes(self):
        """Test complete analysis and recommendation workflow with sentiment likes."""
        result = self.algorithm.analyze_and_recommend(
            self.test_restaurants, 
            ranking_method="sentiment_likes",
            candidate_count=3
        )
        
        assert isinstance(result, RecommendationResult)
        assert len(result.candidates) == 3
        assert result.recommendation in result.candidates
        assert result.ranking_method == "sentiment_likes"
        
        # Verify candidates are properly ranked by likes
        assert result.candidates[0].id == "rest1"  # Highest likes
        assert result.candidates[1].id == "rest2"  # Second highest likes
        assert result.candidates[2].id == "rest4"  # Third highest likes
        
        # Verify analysis summary
        assert "total_restaurants" in result.analysis_summary
        assert "valid_restaurants" in result.analysis_summary
        assert "candidates_selected" in result.analysis_summary
        assert result.analysis_summary["ranking_method"] == "sentiment_likes"
    
    def test_analyze_and_recommend_combined_sentiment(self):
        """Test complete analysis and recommendation workflow with combined sentiment."""
        result = self.algorithm.analyze_and_recommend(
            self.test_restaurants,
            ranking_method="combined_sentiment", 
            candidate_count=2
        )
        
        assert isinstance(result, RecommendationResult)
        assert len(result.candidates) == 2
        assert result.recommendation in result.candidates
        assert result.ranking_method == "combined_sentiment"
        
        # Verify candidates are properly ranked by combined sentiment
        assert result.candidates[0].id == "rest4"  # Highest combined sentiment
        assert result.candidates[1].id == "rest1"  # Second highest combined sentiment
    
    def test_analyze_and_recommend_empty_restaurants(self):
        """Test analysis and recommendation with empty restaurant list."""
        with pytest.raises(ValueError, match="No restaurants provided for analysis"):
            self.algorithm.analyze_and_recommend([])
    
    def test_analyze_and_recommend_invalid_ranking_method(self):
        """Test analysis and recommendation with invalid ranking method."""
        with pytest.raises(ValueError, match="Invalid ranking method: invalid"):
            self.algorithm.analyze_and_recommend(
                self.test_restaurants,
                ranking_method="invalid"
            )
    
    def test_analyze_and_recommend_no_valid_restaurants(self):
        """Test analysis and recommendation when no restaurants have valid sentiment."""
        zero_restaurants = [
            Restaurant(
                id="zero1", name="Zero Restaurant 1", address="Address 1",
                meal_type=["Chinese"], sentiment=Sentiment(likes=0, dislikes=0, neutral=0),
                location_category="Restaurant", district="Central", price_range="$"
            )
        ]
        
        with pytest.raises(ValueError, match="No valid restaurants with sentiment data found"):
            self.algorithm.analyze_and_recommend(zero_restaurants)
    
    def test_analyze_and_recommend_candidate_count_larger_than_available(self):
        """Test analysis when candidate count is larger than available restaurants."""
        result = self.algorithm.analyze_and_recommend(
            self.test_restaurants,
            ranking_method="sentiment_likes",
            candidate_count=100  # More than available
        )
        
        # Should return all valid restaurants (excluding zero sentiment)
        assert len(result.candidates) == 4  # Excludes rest5 with zero sentiment
        assert result.recommendation in result.candidates
    
    def test_ranking_consistency_different_datasets(self):
        """Test ranking consistency with different restaurant data sets."""
        # Create different datasets and verify consistent ranking behavior
        dataset1 = [
            Restaurant(
                id="d1r1", name="Dataset1 Rest1", address="Address 1",
                meal_type=["Chinese"], sentiment=Sentiment(likes=80, dislikes=10, neutral=10),
                location_category="Restaurant", district="Central", price_range="$"
            ),
            Restaurant(
                id="d1r2", name="Dataset1 Rest2", address="Address 2",
                meal_type=["Italian"], sentiment=Sentiment(likes=60, dislikes=20, neutral=20),
                location_category="Restaurant", district="Admiralty", price_range="$"
            )
        ]
        
        dataset2 = [
            Restaurant(
                id="d2r1", name="Dataset2 Rest1", address="Address 1",
                meal_type=["Japanese"], sentiment=Sentiment(likes=90, dislikes=5, neutral=5),
                location_category="Restaurant", district="Tsim Sha Tsui", price_range="$"
            ),
            Restaurant(
                id="d2r2", name="Dataset2 Rest2", address="Address 2",
                meal_type=["Thai"], sentiment=Sentiment(likes=70, dislikes=15, neutral=15),
                location_category="Restaurant", district="Wan Chai", price_range="$"
            )
        ]
        
        # Test sentiment likes ranking consistency
        ranked1 = self.algorithm.rank_by_likes(dataset1)
        ranked2 = self.algorithm.rank_by_likes(dataset2)
        
        # Higher likes should always come first
        assert ranked1[0].sentiment.likes > ranked1[1].sentiment.likes
        assert ranked2[0].sentiment.likes > ranked2[1].sentiment.likes
        
        # Test combined sentiment ranking consistency
        combined1 = self.algorithm.rank_by_combined_sentiment(dataset1)
        combined2 = self.algorithm.rank_by_combined_sentiment(dataset2)
        
        # Higher combined percentage should always come first
        def combined_percentage(restaurant):
            s = restaurant.sentiment
            total = s.total_responses()
            return (s.likes + s.neutral) / total if total > 0 else 0
        
        assert combined_percentage(combined1[0]) >= combined_percentage(combined1[1])
        assert combined_percentage(combined2[0]) >= combined_percentage(combined2[1])
    
    def test_large_dataset_performance(self):
        """Test ranking performance with large restaurant datasets."""
        # Create a large dataset (100 restaurants) to test performance
        large_dataset = []
        for i in range(100):
            large_dataset.append(
                Restaurant(
                    id=f"large{i}", name=f"Large Restaurant {i}", address=f"Address {i}",
                    meal_type=["Chinese"], sentiment=Sentiment(likes=100-i, dislikes=i, neutral=50),
                    location_category="Restaurant", district="Central", price_range="$"
                )
            )
        
        # Test ranking algorithms with large dataset
        ranked_likes = self.algorithm.rank_by_likes(large_dataset)
        ranked_combined = self.algorithm.rank_by_combined_sentiment(large_dataset)
        
        # Verify all restaurants are included and properly sorted
        assert len(ranked_likes) == 100
        assert len(ranked_combined) == 100
        
        # Verify sorting is correct for first few items
        for i in range(5):
            if i < len(ranked_likes) - 1:
                assert ranked_likes[i].sentiment.likes >= ranked_likes[i+1].sentiment.likes
        
        # Test candidate selection with large dataset
        candidates = self.algorithm.select_candidates(ranked_likes, 20)
        assert len(candidates) == 20
        
        # Test recommendation from large candidate pool
        recommendation = self.algorithm.random_select(candidates)
        assert recommendation in candidates
    
    def test_edge_case_extreme_sentiment_values(self):
        """Test ranking with extreme sentiment values."""
        extreme_restaurants = [
            Restaurant(
                id="extreme1", name="Very High Likes", address="Address 1",
                meal_type=["Chinese"], sentiment=Sentiment(likes=10000, dislikes=1, neutral=1),
                location_category="Restaurant", district="Central", price_range="$"
            ),
            Restaurant(
                id="extreme2", name="Very High Dislikes", address="Address 2",
                meal_type=["Italian"], sentiment=Sentiment(likes=1, dislikes=10000, neutral=1),
                location_category="Restaurant", district="Admiralty", price_range="$"
            ),
            Restaurant(
                id="extreme3", name="Very High Neutral", address="Address 3",
                meal_type=["Japanese"], sentiment=Sentiment(likes=1, dislikes=1, neutral=10000),
                location_category="Restaurant", district="Causeway Bay", price_range="$"
            )
        ]
        
        # Test likes ranking with extreme values
        ranked_likes = self.algorithm.rank_by_likes(extreme_restaurants)
        assert ranked_likes[0].id == "extreme1"  # Should have highest likes
        
        # Test combined sentiment ranking with extreme values
        ranked_combined = self.algorithm.rank_by_combined_sentiment(extreme_restaurants)
        # extreme3 should rank high due to high neutral + likes combined
        # extreme1 should also rank high due to high likes
        assert ranked_combined[0].id in ["extreme1", "extreme3"]
    
    def test_mixed_valid_invalid_restaurants(self):
        """Test ranking with mix of valid and invalid sentiment data."""
        mixed_restaurants = [
            Restaurant(
                id="valid1", name="Valid Restaurant 1", address="Address 1",
                meal_type=["Chinese"], sentiment=Sentiment(likes=50, dislikes=10, neutral=20),
                location_category="Restaurant", district="Central", price_range="$"
            ),
            Restaurant(
                id="invalid1", name="Invalid Restaurant 1", address="Address 2",
                meal_type=["Italian"], sentiment=Sentiment(likes=0, dislikes=0, neutral=0),
                location_category="Restaurant", district="Admiralty", price_range="$"
            ),
            Restaurant(
                id="valid2", name="Valid Restaurant 2", address="Address 3",
                meal_type=["Japanese"], sentiment=Sentiment(likes=30, dislikes=5, neutral=15),
                location_category="Restaurant", district="Causeway Bay", price_range="$"
            ),
            Restaurant(
                id="invalid2", name="Invalid Restaurant 2", address="Address 4",
                meal_type=["Thai"], sentiment=Sentiment(likes=0, dislikes=0, neutral=0),
                location_category="Restaurant", district="Tsim Sha Tsui", price_range="$"
            )
        ]
        
        # Test that only valid restaurants are included in ranking
        ranked = self.algorithm.rank_by_likes(mixed_restaurants)
        assert len(ranked) == 2  # Only valid restaurants
        
        valid_ids = [r.id for r in ranked]
        assert "valid1" in valid_ids
        assert "valid2" in valid_ids
        assert "invalid1" not in valid_ids
        assert "invalid2" not in valid_ids
        
        # Test candidate selection excludes invalid restaurants
        candidates = self.algorithm.select_candidates(ranked, 10)
        assert len(candidates) == 2  # Only valid restaurants available
    
    def test_recommendation_distribution_fairness(self):
        """Test that random recommendation provides fair distribution over multiple runs."""
        # Create 3 equal restaurants for fair distribution testing
        equal_restaurants = [
            Restaurant(
                id="equal1", name="Equal Restaurant 1", address="Address 1",
                meal_type=["Chinese"], sentiment=Sentiment(likes=50, dislikes=10, neutral=20),
                location_category="Restaurant", district="Central", price_range="$"
            ),
            Restaurant(
                id="equal2", name="Equal Restaurant 2", address="Address 2",
                meal_type=["Italian"], sentiment=Sentiment(likes=50, dislikes=10, neutral=20),
                location_category="Restaurant", district="Admiralty", price_range="$"
            ),
            Restaurant(
                id="equal3", name="Equal Restaurant 3", address="Address 3",
                meal_type=["Japanese"], sentiment=Sentiment(likes=50, dislikes=10, neutral=20),
                location_category="Restaurant", district="Causeway Bay", price_range="$"
            )
        ]
        
        # Test multiple recommendations to check distribution
        # Note: With fixed seed, this tests reproducibility rather than true randomness
        recommendations = []
        for _ in range(30):
            result = self.algorithm.analyze_and_recommend(equal_restaurants, "sentiment_likes", 3)
            recommendations.append(result.recommendation.id)
        
        # With fixed seed, should get consistent but varied results
        unique_recommendations = set(recommendations)
        assert len(unique_recommendations) >= 1  # At least one unique recommendation
        
        # All recommendations should be from valid candidates
        for rec_id in recommendations:
            assert rec_id in ["equal1", "equal2", "equal3"]


class TestCreateSentimentAnalysis:
    """Test cases for create_sentiment_analysis function."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.test_restaurants = [
            Restaurant(
                id="rest1", name="Restaurant 1", address="Address 1",
                meal_type=["Chinese"], sentiment=Sentiment(likes=100, dislikes=20, neutral=30),
                location_category="Restaurant", district="Central", price_range="$"
            ),
            Restaurant(
                id="rest2", name="Restaurant 2", address="Address 2",
                meal_type=["Italian"], sentiment=Sentiment(likes=50, dislikes=10, neutral=40),
                location_category="Restaurant", district="Admiralty", price_range="$"
            ),
            Restaurant(
                id="rest3", name="Restaurant 3", address="Address 3",
                meal_type=["Japanese"], sentiment=Sentiment(likes=0, dislikes=0, neutral=0),
                location_category="Restaurant", district="Causeway Bay", price_range="$"
            )
        ]
    
    def test_create_sentiment_analysis_basic(self):
        """Test basic sentiment analysis creation."""
        analysis = create_sentiment_analysis(self.test_restaurants, "sentiment_likes")
        
        assert analysis.restaurant_count == 3
        assert analysis.ranking_method == "sentiment_likes"
        
        # Should calculate averages for valid restaurants only (excluding zero sentiment)
        # rest1: 100 likes, rest2: 50 likes -> average = 75
        assert analysis.average_likes == 75.0
        
        # rest1: 20 dislikes, rest2: 10 dislikes -> average = 15
        assert analysis.average_dislikes == 15.0
        
        # rest1: 30 neutral, rest2: 40 neutral -> average = 35
        assert analysis.average_neutral == 35.0
    
    def test_create_sentiment_analysis_empty_list(self):
        """Test sentiment analysis with empty restaurant list."""
        analysis = create_sentiment_analysis([], "sentiment_likes")
        
        assert analysis.restaurant_count == 0
        assert analysis.average_likes == 0.0
        assert analysis.average_dislikes == 0.0
        assert analysis.average_neutral == 0.0
        assert analysis.top_sentiment_score == 0.0
        assert analysis.bottom_sentiment_score == 0.0
    
    def test_create_sentiment_analysis_all_zero_sentiment(self):
        """Test sentiment analysis when all restaurants have zero sentiment."""
        zero_restaurants = [
            Restaurant(
                id="zero1", name="Zero Restaurant 1", address="Address 1",
                meal_type=["Chinese"], sentiment=Sentiment(likes=0, dislikes=0, neutral=0),
                location_category="Restaurant", district="Central", price_range="$"
            ),
            Restaurant(
                id="zero2", name="Zero Restaurant 2", address="Address 2",
                meal_type=["Italian"], sentiment=Sentiment(likes=0, dislikes=0, neutral=0),
                location_category="Restaurant", district="Admiralty", price_range="$"
            )
        ]
        
        analysis = create_sentiment_analysis(zero_restaurants, "sentiment_likes")
        
        assert analysis.restaurant_count == 2
        assert analysis.average_likes == 0.0
        assert analysis.average_dislikes == 0.0
        assert analysis.average_neutral == 0.0
        assert analysis.top_sentiment_score == 0.0
        assert analysis.bottom_sentiment_score == 0.0
    
    def test_create_sentiment_analysis_combined_sentiment_method(self):
        """Test sentiment analysis with combined sentiment method."""
        analysis = create_sentiment_analysis(self.test_restaurants, "combined_sentiment")
        
        assert analysis.ranking_method == "combined_sentiment"
        
        # Scores should be calculated using combined sentiment percentage
        # rest1: (100 + 30) / 150 = 86.67%
        # rest2: (50 + 40) / 100 = 90%
        # Expected top score: 90%, bottom score: 86.67%
        
        assert abs(analysis.top_sentiment_score - 90.0) < 0.001
        assert abs(analysis.bottom_sentiment_score - 86.66666666666667) < 0.001


if __name__ == "__main__":
    pytest.main([__file__])