#!/usr/bin/env python3
"""
Comprehensive Reasoning Test Scenarios.

This module provides comprehensive test scenarios for restaurant reasoning functionality,
including various sentiment scenarios, different ranking methods, data sizes, edge cases,
and performance testing with large restaurant lists.
"""

import sys
import os
import json
import unittest
import random
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from services.restaurant_reasoning_service import RestaurantReasoningService
from models.restaurant_models import Restaurant, Sentiment, RecommendationResult


@dataclass
class TestScenario:
    """Test scenario configuration."""
    name: str
    description: str
    restaurants: List[Dict[str, Any]]
    ranking_method: str
    expected_top_restaurant_id: Optional[str] = None
    expected_candidate_count: Optional[int] = None
    should_fail: bool = False
    error_type: Optional[str] = None


class RestaurantDataGenerator:
    """Generator for various restaurant test data scenarios."""
    
    @staticmethod
    def create_basic_sentiment_scenario() -> List[Dict[str, Any]]:
        """Create basic sentiment test data with clear ranking."""
        return [
            {
                "id": "basic_001",
                "name": "High Likes Restaurant",
                "address": "1 Test Street",
                "meal_type": ["lunch"],
                "sentiment": {"likes": 95, "dislikes": 3, "neutral": 2},
                "location_category": "restaurant",
                "district": "Test District",
                "price_range": "$$"
            },
            {
                "id": "basic_002",
                "name": "Medium Likes Restaurant",
                "address": "2 Test Street",
                "meal_type": ["lunch"],
                "sentiment": {"likes": 70, "dislikes": 20, "neutral": 10},
                "location_category": "restaurant",
                "district": "Test District",
                "price_range": "$"
            },
            {
                "id": "basic_003",
                "name": "Low Likes Restaurant",
                "address": "3 Test Street",
                "meal_type": ["lunch"],
                "sentiment": {"likes": 45, "dislikes": 35, "neutral": 20},
                "location_category": "restaurant",
                "district": "Test District",
                "price_range": "$"
            }
        ]
    
    @staticmethod
    def create_combined_sentiment_scenario() -> List[Dict[str, Any]]:
        """Create test data where combined sentiment ranking differs from likes ranking."""
        return [
            {
                "id": "combined_001",
                "name": "High Likes Low Neutral",
                "address": "1 Combined Street",
                "meal_type": ["lunch"],
                "sentiment": {"likes": 80, "dislikes": 15, "neutral": 5},  # 80% likes, 85% combined
                "location_category": "restaurant",
                "district": "Test District",
                "price_range": "$$"
            },
            {
                "id": "combined_002",
                "name": "Medium Likes High Neutral",
                "address": "2 Combined Street",
                "meal_type": ["lunch"],
                "sentiment": {"likes": 60, "dislikes": 10, "neutral": 30},  # 60% likes, 90% combined
                "location_category": "restaurant",
                "district": "Test District",
                "price_range": "$"
            },
            {
                "id": "combined_003",
                "name": "Low Likes Medium Neutral",
                "address": "3 Combined Street",
                "meal_type": ["lunch"],
                "sentiment": {"likes": 50, "dislikes": 25, "neutral": 25},  # 50% likes, 75% combined
                "location_category": "restaurant",
                "district": "Test District",
                "price_range": "$"
            }
        ]
    
    @staticmethod
    def create_tie_breaking_scenario() -> List[Dict[str, Any]]:
        """Create test data with tied sentiment scores to test tie-breaking logic."""
        return [
            {
                "id": "tie_001",
                "name": "Tied Restaurant A",
                "address": "1 Tie Street",
                "meal_type": ["lunch"],
                "sentiment": {"likes": 80, "dislikes": 10, "neutral": 10},  # Same percentage
                "location_category": "restaurant",
                "district": "Test District",
                "price_range": "$"
            },
            {
                "id": "tie_002",
                "name": "Tied Restaurant B",
                "address": "2 Tie Street",
                "meal_type": ["lunch"],
                "sentiment": {"likes": 80, "dislikes": 10, "neutral": 10},  # Same percentage
                "location_category": "restaurant",
                "district": "Test District",
                "price_range": "$"
            },
            {
                "id": "tie_003",
                "name": "Different Restaurant",
                "address": "3 Tie Street",
                "meal_type": ["lunch"],
                "sentiment": {"likes": 70, "dislikes": 15, "neutral": 15},  # Different percentage
                "location_category": "restaurant",
                "district": "Test District",
                "price_range": "$"
            }
        ]
    
    @staticmethod
    def create_edge_case_scenarios() -> Dict[str, List[Dict[str, Any]]]:
        """Create various edge case test scenarios."""
        return {
            "zero_sentiment": [
                {
                    "id": "zero_001",
                    "name": "Zero Sentiment Restaurant",
                    "address": "1 Zero Street",
                    "meal_type": ["lunch"],
                    "sentiment": {"likes": 0, "dislikes": 0, "neutral": 0},
                    "location_category": "restaurant",
                    "district": "Test District",
                    "price_range": "$"
                }
            ],
            "single_response": [
                {
                    "id": "single_001",
                    "name": "Single Response Restaurant",
                    "address": "1 Single Street",
                    "meal_type": ["lunch"],
                    "sentiment": {"likes": 1, "dislikes": 0, "neutral": 0},
                    "location_category": "restaurant",
                    "district": "Test District",
                    "price_range": "$"
                }
            ],
            "high_dislikes": [
                {
                    "id": "dislike_001",
                    "name": "High Dislikes Restaurant",
                    "address": "1 Dislike Street",
                    "meal_type": ["lunch"],
                    "sentiment": {"likes": 10, "dislikes": 80, "neutral": 10},
                    "location_category": "restaurant",
                    "district": "Test District",
                    "price_range": "$"
                }
            ],
            "all_neutral": [
                {
                    "id": "neutral_001",
                    "name": "All Neutral Restaurant",
                    "address": "1 Neutral Street",
                    "meal_type": ["lunch"],
                    "sentiment": {"likes": 0, "dislikes": 0, "neutral": 100},
                    "location_category": "restaurant",
                    "district": "Test District",
                    "price_range": "$"
                }
            ]
        }
    
    @staticmethod
    def create_invalid_data_scenarios() -> Dict[str, List[Dict[str, Any]]]:
        """Create invalid data scenarios for error handling testing."""
        return {
            "missing_sentiment": [
                {
                    "id": "invalid_001",
                    "name": "Missing Sentiment Restaurant",
                    "address": "1 Invalid Street",
                    "meal_type": ["lunch"],
                    # Missing sentiment field
                    "location_category": "restaurant",
                    "district": "Test District",
                    "price_range": "$"
                }
            ],
            "missing_required_fields": [
                {
                    # Missing id and name
                    "address": "2 Invalid Street",
                    "sentiment": {"likes": 50, "dislikes": 25, "neutral": 25}
                }
            ],
            "invalid_sentiment_types": [
                {
                    "id": "invalid_003",
                    "name": "Invalid Sentiment Types",
                    "address": "3 Invalid Street",
                    "sentiment": {"likes": "not_a_number", "dislikes": 25, "neutral": 25},
                    "location_category": "restaurant",
                    "district": "Test District",
                    "price_range": "$"
                }
            ],
            "negative_sentiment": [
                {
                    "id": "invalid_004",
                    "name": "Negative Sentiment",
                    "address": "4 Invalid Street",
                    "sentiment": {"likes": -10, "dislikes": 25, "neutral": 25},
                    "location_category": "restaurant",
                    "district": "Test District",
                    "price_range": "$"
                }
            ],
            "incomplete_sentiment": [
                {
                    "id": "invalid_005",
                    "name": "Incomplete Sentiment",
                    "address": "5 Invalid Street",
                    "sentiment": {"likes": 50},  # Missing dislikes and neutral
                    "location_category": "restaurant",
                    "district": "Test District",
                    "price_range": "$"
                }
            ]
        }
    
    @staticmethod
    def create_large_dataset(size: int = 100) -> List[Dict[str, Any]]:
        """Create large dataset for performance testing."""
        restaurants = []
        random.seed(42)  # For reproducible results
        
        for i in range(size):
            # Generate varied sentiment data
            likes = random.randint(10, 100)
            dislikes = random.randint(5, 50)
            neutral = random.randint(0, 30)
            
            restaurant = {
                "id": f"large_{i:04d}",
                "name": f"Restaurant {i}",
                "address": f"{i} Performance Street",
                "meal_type": random.choice([["breakfast"], ["lunch"], ["dinner"], ["lunch", "dinner"]]),
                "sentiment": {"likes": likes, "dislikes": dislikes, "neutral": neutral},
                "location_category": random.choice(["restaurant", "cafe", "fast_food"]),
                "district": random.choice(["District A", "District B", "District C"]),
                "price_range": random.choice(["$", "$$", "$$$"])
            }
            restaurants.append(restaurant)
        
        return restaurants
    
    @staticmethod
    def create_varied_size_datasets() -> Dict[str, List[Dict[str, Any]]]:
        """Create datasets of various sizes for testing."""
        generator = RestaurantDataGenerator()
        
        return {
            "tiny": generator.create_large_dataset(1),
            "small": generator.create_large_dataset(5),
            "medium": generator.create_large_dataset(20),
            "large": generator.create_large_dataset(50),
            "extra_large": generator.create_large_dataset(100),
            "huge": generator.create_large_dataset(500)
        }


class TestReasoningScenarios(unittest.TestCase):
    """Test cases for comprehensive reasoning scenarios."""
    
    def setUp(self):
        """Set up test environment."""
        self.reasoning_service = RestaurantReasoningService(
            minimum_responses=1,
            default_candidate_count=20,
            random_seed=42,  # For reproducible tests
            strict_validation=False
        )
        self.generator = RestaurantDataGenerator()
    
    def test_basic_sentiment_likes_ranking(self):
        """Test basic sentiment likes ranking scenario."""
        restaurants = self.generator.create_basic_sentiment_scenario()
        
        result = self.reasoning_service.analyze_and_recommend(
            restaurant_data=restaurants,
            ranking_method="sentiment_likes",
            candidate_count=20
        )
        
        # Verify ranking order (highest likes first)
        self.assertEqual(result.candidates[0].id, "basic_001")  # 95 likes
        self.assertEqual(result.candidates[1].id, "basic_002")  # 70 likes
        self.assertEqual(result.candidates[2].id, "basic_003")  # 45 likes
        
        # Verify recommendation is from candidates
        self.assertIn(result.recommendation.id, [c.id for c in result.candidates])
    
    def test_combined_sentiment_ranking_difference(self):
        """Test that combined sentiment ranking produces different results than likes ranking."""
        restaurants = self.generator.create_combined_sentiment_scenario()
        
        # Test sentiment_likes ranking
        likes_result = self.reasoning_service.analyze_and_recommend(
            restaurant_data=restaurants,
            ranking_method="sentiment_likes",
            candidate_count=20
        )
        
        # Test combined_sentiment ranking
        combined_result = self.reasoning_service.analyze_and_recommend(
            restaurant_data=restaurants,
            ranking_method="combined_sentiment",
            candidate_count=20
        )
        
        # Verify different ranking orders
        likes_order = [c.id for c in likes_result.candidates]
        combined_order = [c.id for c in combined_result.candidates]
        
        # For likes ranking: combined_001 (80) > combined_002 (60) > combined_003 (50)
        self.assertEqual(likes_order, ["combined_001", "combined_002", "combined_003"])
        
        # For combined ranking: combined_002 (90%) > combined_001 (85%) > combined_003 (75%)
        self.assertEqual(combined_order, ["combined_002", "combined_001", "combined_003"])
    
    def test_tie_breaking_logic(self):
        """Test tie-breaking logic when restaurants have identical sentiment scores."""
        restaurants = self.generator.create_tie_breaking_scenario()
        
        result = self.reasoning_service.analyze_and_recommend(
            restaurant_data=restaurants,
            ranking_method="sentiment_likes",
            candidate_count=20
        )
        
        # Both tie_001 and tie_002 have same sentiment, should be ranked consistently
        # Different restaurant should be ranked lower
        top_two_ids = [result.candidates[0].id, result.candidates[1].id]
        self.assertIn("tie_001", top_two_ids)
        self.assertIn("tie_002", top_two_ids)
        self.assertEqual(result.candidates[2].id, "tie_003")
    
    def test_edge_case_scenarios(self):
        """Test various edge case scenarios."""
        edge_cases = self.generator.create_edge_case_scenarios()
        
        # Test zero sentiment (should handle gracefully)
        zero_result = self.reasoning_service.analyze_and_recommend(
            restaurant_data=edge_cases["zero_sentiment"],
            ranking_method="sentiment_likes",
            candidate_count=20
        )
        self.assertEqual(len(zero_result.candidates), 1)
        self.assertEqual(zero_result.recommendation.id, "zero_001")
        
        # Test single response
        single_result = self.reasoning_service.analyze_and_recommend(
            restaurant_data=edge_cases["single_response"],
            ranking_method="sentiment_likes",
            candidate_count=20
        )
        self.assertEqual(len(single_result.candidates), 1)
        self.assertEqual(single_result.recommendation.id, "single_001")
        
        # Test high dislikes (should still work)
        dislike_result = self.reasoning_service.analyze_and_recommend(
            restaurant_data=edge_cases["high_dislikes"],
            ranking_method="sentiment_likes",
            candidate_count=20
        )
        self.assertEqual(len(dislike_result.candidates), 1)
        
        # Test all neutral (should work with combined sentiment)
        neutral_result = self.reasoning_service.analyze_and_recommend(
            restaurant_data=edge_cases["all_neutral"],
            ranking_method="combined_sentiment",
            candidate_count=20
        )
        self.assertEqual(len(neutral_result.candidates), 1)
    
    def test_invalid_data_error_handling(self):
        """Test error handling for invalid data scenarios."""
        invalid_scenarios = self.generator.create_invalid_data_scenarios()
        
        # Test missing sentiment
        with self.assertRaises(ValueError):
            self.reasoning_service.analyze_and_recommend(
                restaurant_data=invalid_scenarios["missing_sentiment"],
                ranking_method="sentiment_likes",
                candidate_count=20
            )
        
        # Test missing required fields
        with self.assertRaises(ValueError):
            self.reasoning_service.analyze_and_recommend(
                restaurant_data=invalid_scenarios["missing_required_fields"],
                ranking_method="sentiment_likes",
                candidate_count=20
            )
        
        # Test invalid sentiment types
        with self.assertRaises(ValueError):
            self.reasoning_service.analyze_and_recommend(
                restaurant_data=invalid_scenarios["invalid_sentiment_types"],
                ranking_method="sentiment_likes",
                candidate_count=20
            )
    
    def test_various_dataset_sizes(self):
        """Test reasoning with various dataset sizes."""
        datasets = self.generator.create_varied_size_datasets()
        
        for size_name, restaurants in datasets.items():
            with self.subTest(size=size_name):
                result = self.reasoning_service.analyze_and_recommend(
                    restaurant_data=restaurants,
                    ranking_method="sentiment_likes",
                    candidate_count=20
                )
                
                # Verify candidate count logic
                expected_count = min(len(restaurants), 20)
                self.assertEqual(len(result.candidates), expected_count)
                
                # Verify recommendation is from candidates
                self.assertIn(result.recommendation.id, [c.id for c in result.candidates])
                
                # Verify analysis summary
                self.assertEqual(result.analysis_summary["restaurant_count"], len(restaurants))
    
    def test_performance_with_large_dataset(self):
        """Test performance with large dataset."""
        import time
        
        large_dataset = self.generator.create_large_dataset(1000)
        
        # Measure performance
        start_time = time.time()
        result = self.reasoning_service.analyze_and_recommend(
            restaurant_data=large_dataset,
            ranking_method="sentiment_likes",
            candidate_count=20
        )
        end_time = time.time()
        
        processing_time = end_time - start_time
        
        # Verify results
        self.assertEqual(len(result.candidates), 20)
        self.assertIn(result.recommendation.id, [c.id for c in result.candidates])
        
        # Performance assertion (should complete within reasonable time)
        self.assertLess(processing_time, 5.0, f"Processing took {processing_time:.2f}s, expected < 5s")
        
        print(f"Performance test: Processed {len(large_dataset)} restaurants in {processing_time:.3f}s")
    
    def test_ranking_method_consistency(self):
        """Test that ranking methods produce consistent results across multiple runs."""
        restaurants = self.generator.create_large_dataset(50)
        
        # Run multiple times with same seed
        results = []
        for _ in range(3):
            result = self.reasoning_service.analyze_and_recommend(
                restaurant_data=restaurants,
                ranking_method="sentiment_likes",
                candidate_count=20
            )
            results.append([c.id for c in result.candidates])
        
        # All runs should produce identical candidate order
        for i in range(1, len(results)):
            self.assertEqual(results[0], results[i], "Ranking should be consistent across runs")
    
    def test_sentiment_analysis_accuracy(self):
        """Test accuracy of sentiment analysis calculations."""
        restaurants = self.generator.create_basic_sentiment_scenario()
        
        analysis = self.reasoning_service.analyze_sentiment_only(
            restaurant_data=restaurants,
            ranking_method="sentiment_likes"
        )
        
        # Verify calculations
        expected_avg_likes = (95 + 70 + 45) / 3
        expected_avg_dislikes = (3 + 20 + 35) / 3
        expected_avg_neutral = (2 + 10 + 20) / 3
        
        self.assertAlmostEqual(analysis.average_likes, expected_avg_likes, places=2)
        self.assertAlmostEqual(analysis.average_dislikes, expected_avg_dislikes, places=2)
        self.assertAlmostEqual(analysis.average_neutral, expected_avg_neutral, places=2)
        
        # Verify score ranges
        self.assertGreater(analysis.top_sentiment_score, analysis.bottom_sentiment_score)
    
    def test_candidate_selection_edge_cases(self):
        """Test candidate selection with edge cases."""
        # Test with exactly 20 restaurants
        exactly_20 = self.generator.create_large_dataset(20)
        result_20 = self.reasoning_service.analyze_and_recommend(
            restaurant_data=exactly_20,
            ranking_method="sentiment_likes",
            candidate_count=20
        )
        self.assertEqual(len(result_20.candidates), 20)
        
        # Test with more than 20 restaurants
        more_than_20 = self.generator.create_large_dataset(25)
        result_more = self.reasoning_service.analyze_and_recommend(
            restaurant_data=more_than_20,
            ranking_method="sentiment_likes",
            candidate_count=20
        )
        self.assertEqual(len(result_more.candidates), 20)
        
        # Test with fewer than 20 restaurants
        fewer_than_20 = self.generator.create_large_dataset(15)
        result_fewer = self.reasoning_service.analyze_and_recommend(
            restaurant_data=fewer_than_20,
            ranking_method="sentiment_likes",
            candidate_count=20
        )
        self.assertEqual(len(result_fewer.candidates), 15)


class TestScenarioRunner(unittest.TestCase):
    """Test runner for predefined scenarios."""
    
    def setUp(self):
        """Set up scenario runner."""
        self.reasoning_service = RestaurantReasoningService(
            minimum_responses=1,
            default_candidate_count=20,
            random_seed=42,
            strict_validation=False
        )
        self.generator = RestaurantDataGenerator()
    
    def create_test_scenarios(self) -> List[TestScenario]:
        """Create comprehensive test scenarios."""
        scenarios = []
        
        # Basic scenarios
        scenarios.append(TestScenario(
            name="Basic Sentiment Likes Ranking",
            description="Test basic sentiment likes ranking with clear hierarchy",
            restaurants=self.generator.create_basic_sentiment_scenario(),
            ranking_method="sentiment_likes",
            expected_top_restaurant_id="basic_001",
            expected_candidate_count=3
        ))
        
        scenarios.append(TestScenario(
            name="Combined Sentiment Ranking",
            description="Test combined sentiment ranking produces different results",
            restaurants=self.generator.create_combined_sentiment_scenario(),
            ranking_method="combined_sentiment",
            expected_top_restaurant_id="combined_002",
            expected_candidate_count=3
        ))
        
        # Edge case scenarios
        edge_cases = self.generator.create_edge_case_scenarios()
        scenarios.append(TestScenario(
            name="Zero Sentiment Edge Case",
            description="Test handling of restaurants with zero sentiment responses",
            restaurants=edge_cases["zero_sentiment"],
            ranking_method="sentiment_likes",
            expected_candidate_count=1
        ))
        
        scenarios.append(TestScenario(
            name="Single Response Edge Case",
            description="Test handling of restaurants with minimal sentiment data",
            restaurants=edge_cases["single_response"],
            ranking_method="sentiment_likes",
            expected_candidate_count=1
        ))
        
        # Error scenarios
        invalid_data = self.generator.create_invalid_data_scenarios()
        scenarios.append(TestScenario(
            name="Missing Sentiment Error",
            description="Test error handling for missing sentiment data",
            restaurants=invalid_data["missing_sentiment"],
            ranking_method="sentiment_likes",
            should_fail=True,
            error_type="ValueError"
        ))
        
        scenarios.append(TestScenario(
            name="Invalid Sentiment Types Error",
            description="Test error handling for invalid sentiment data types",
            restaurants=invalid_data["invalid_sentiment_types"],
            ranking_method="sentiment_likes",
            should_fail=True,
            error_type="ValueError"
        ))
        
        # Performance scenarios
        scenarios.append(TestScenario(
            name="Large Dataset Performance",
            description="Test performance with large dataset (100 restaurants)",
            restaurants=self.generator.create_large_dataset(100),
            ranking_method="sentiment_likes",
            expected_candidate_count=20
        ))
        
        return scenarios
    
    def test_all_scenarios(self):
        """Run all predefined test scenarios."""
        scenarios = self.create_test_scenarios()
        
        for scenario in scenarios:
            with self.subTest(scenario=scenario.name):
                print(f"\nRunning scenario: {scenario.name}")
                print(f"Description: {scenario.description}")
                
                if scenario.should_fail:
                    # Test error scenarios
                    with self.assertRaises(Exception) as context:
                        self.reasoning_service.analyze_and_recommend(
                            restaurant_data=scenario.restaurants,
                            ranking_method=scenario.ranking_method,
                            candidate_count=20
                        )
                    
                    if scenario.error_type:
                        self.assertIn(scenario.error_type, str(type(context.exception)))
                    
                    print(f"✅ Error scenario handled correctly: {type(context.exception).__name__}")
                
                else:
                    # Test success scenarios
                    result = self.reasoning_service.analyze_and_recommend(
                        restaurant_data=scenario.restaurants,
                        ranking_method=scenario.ranking_method,
                        candidate_count=20
                    )
                    
                    # Verify expected results
                    if scenario.expected_candidate_count is not None:
                        self.assertEqual(len(result.candidates), scenario.expected_candidate_count)
                    
                    if scenario.expected_top_restaurant_id is not None:
                        self.assertEqual(result.candidates[0].id, scenario.expected_top_restaurant_id)
                    
                    # Verify recommendation is from candidates
                    self.assertIn(result.recommendation.id, [c.id for c in result.candidates])
                    
                    print(f"✅ Scenario completed successfully")
                    print(f"   - Candidates: {len(result.candidates)}")
                    print(f"   - Recommendation: {result.recommendation.name}")
                    print(f"   - Ranking method: {result.ranking_method}")


def run_reasoning_scenario_tests():
    """Run all reasoning scenario tests and display results."""
    print("Running Comprehensive Restaurant Reasoning Scenario Tests...")
    print("=" * 70)
    
    # Create test suite
    loader = unittest.TestLoader()
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_suite.addTest(loader.loadTestsFromTestCase(TestReasoningScenarios))
    test_suite.addTest(loader.loadTestsFromTestCase(TestScenarioRunner))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print("\n" + "=" * 70)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print("\nFailures:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback}")
    
    if result.errors:
        print("\nErrors:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback}")
    
    success = len(result.failures) == 0 and len(result.errors) == 0
    print(f"\nOverall result: {'✅ PASSED' if success else '❌ FAILED'}")
    
    return success


if __name__ == "__main__":
    success = run_reasoning_scenario_tests()
    sys.exit(0 if success else 1)