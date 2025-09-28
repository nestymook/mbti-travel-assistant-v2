#!/usr/bin/env python3
"""
Test Data Generator for Restaurant Reasoning MCP.

This script generates comprehensive test data for various scenarios including
edge cases, performance testing, and error validation scenarios.
"""

import json
import base64
import random
import os
from typing import Dict, Any, List
from pathlib import Path


class TestDataGenerator:
    """Generator for comprehensive test data scenarios."""
    
    def __init__(self, output_dir: str = "tests"):
        """Initialize the test data generator."""
        self.output_dir = Path(output_dir)
        self.request_dir = self.output_dir / "request"
        self.response_dir = self.output_dir / "response"
        self.payload_dir = self.output_dir / "payload"
        self.results_dir = self.output_dir / "results"
        
        # Ensure directories exist
        for directory in [self.request_dir, self.response_dir, self.payload_dir, self.results_dir]:
            directory.mkdir(parents=True, exist_ok=True)
    
    def generate_restaurant_data(
        self, 
        count: int, 
        scenario: str = "normal",
        seed: int = 42
    ) -> List[Dict[str, Any]]:
        """Generate restaurant data for different scenarios."""
        random.seed(seed)
        restaurants = []
        
        for i in range(count):
            if scenario == "normal":
                likes = random.randint(30, 100)
                dislikes = random.randint(5, 30)
                neutral = random.randint(5, 25)
            elif scenario == "high_sentiment":
                likes = random.randint(80, 100)
                dislikes = random.randint(1, 10)
                neutral = random.randint(1, 10)
            elif scenario == "low_sentiment":
                likes = random.randint(10, 40)
                dislikes = random.randint(30, 60)
                neutral = random.randint(10, 30)
            elif scenario == "mixed_sentiment":
                if i % 3 == 0:
                    likes, dislikes, neutral = 90, 5, 5
                elif i % 3 == 1:
                    likes, dislikes, neutral = 50, 30, 20
                else:
                    likes, dislikes, neutral = 20, 60, 20
            elif scenario == "edge_case":
                if i == 0:
                    likes, dislikes, neutral = 0, 0, 0  # Zero sentiment
                elif i == 1:
                    likes, dislikes, neutral = 1, 0, 0  # Minimal sentiment
                elif i == 2:
                    likes, dislikes, neutral = 0, 0, 100  # All neutral
                else:
                    likes, dislikes, neutral = 50, 25, 25
            else:
                likes = random.randint(20, 80)
                dislikes = random.randint(10, 40)
                neutral = random.randint(5, 30)
            
            restaurant = {
                "id": f"{scenario}_{i:04d}",
                "name": f"{scenario.title()} Restaurant {i}",
                "address": f"{i} {scenario.title()} Street",
                "meal_type": random.choice([
                    ["breakfast"], ["lunch"], ["dinner"],
                    ["breakfast", "lunch"], ["lunch", "dinner"],
                    ["breakfast", "lunch", "dinner"]
                ]),
                "sentiment": {"likes": likes, "dislikes": dislikes, "neutral": neutral},
                "location_category": random.choice(["restaurant", "cafe", "fast_food", "fine_dining"]),
                "district": random.choice([
                    "Central district", "Admiralty", "Causeway Bay", "Wan Chai",
                    "Tsim Sha Tsui", "Mong Kok", "Sheung Wan"
                ]),
                "price_range": random.choice(["$", "$$", "$$$", "$$$$"])
            }
            restaurants.append(restaurant)
        
        return restaurants
    
    def generate_invalid_data_scenarios(self) -> Dict[str, List[Dict[str, Any]]]:
        """Generate invalid data scenarios for error testing."""
        return {
            "missing_sentiment": [
                {
                    "id": "invalid_001",
                    "name": "Missing Sentiment Restaurant",
                    "address": "1 Invalid Street",
                    "meal_type": ["lunch"],
                    "location_category": "restaurant",
                    "district": "Test District",
                    "price_range": "$"
                }
            ],
            "missing_id": [
                {
                    "name": "Missing ID Restaurant",
                    "address": "2 Invalid Street",
                    "sentiment": {"likes": 50, "dislikes": 25, "neutral": 25},
                    "meal_type": ["lunch"],
                    "location_category": "restaurant",
                    "district": "Test District",
                    "price_range": "$"
                }
            ],
            "missing_name": [
                {
                    "id": "invalid_003",
                    "address": "3 Invalid Street",
                    "sentiment": {"likes": 50, "dislikes": 25, "neutral": 25},
                    "meal_type": ["lunch"],
                    "location_category": "restaurant",
                    "district": "Test District",
                    "price_range": "$"
                }
            ],
            "invalid_sentiment_types": [
                {
                    "id": "invalid_004",
                    "name": "Invalid Sentiment Types",
                    "address": "4 Invalid Street",
                    "sentiment": {"likes": "not_a_number", "dislikes": 25, "neutral": 25},
                    "meal_type": ["lunch"],
                    "location_category": "restaurant",
                    "district": "Test District",
                    "price_range": "$"
                }
            ],
            "negative_sentiment": [
                {
                    "id": "invalid_005",
                    "name": "Negative Sentiment",
                    "address": "5 Invalid Street",
                    "sentiment": {"likes": -10, "dislikes": 25, "neutral": 25},
                    "meal_type": ["lunch"],
                    "location_category": "restaurant",
                    "district": "Test District",
                    "price_range": "$"
                }
            ],
            "incomplete_sentiment": [
                {
                    "id": "invalid_006",
                    "name": "Incomplete Sentiment",
                    "address": "6 Invalid Street",
                    "sentiment": {"likes": 50},  # Missing dislikes and neutral
                    "meal_type": ["lunch"],
                    "location_category": "restaurant",
                    "district": "Test District",
                    "price_range": "$"
                }
            ]
        }
    
    def create_test_request(
        self, 
        tool_name: str, 
        restaurants: List[Dict[str, Any]], 
        ranking_method: str = "sentiment_likes"
    ) -> Dict[str, Any]:
        """Create a test request structure."""
        request = {
            "tool_name": tool_name,
            "parameters": {
                "restaurants": restaurants
            }
        }
        
        if tool_name == "recommend_restaurants":
            request["parameters"]["ranking_method"] = ranking_method
        
        return request
    
    def save_request_file(self, filename: str, request_data: Dict[str, Any]) -> None:
        """Save request data to JSON file."""
        filepath = self.request_dir / f"{filename}.json"
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(request_data, f, indent=2, ensure_ascii=False)
        print(f"Created request file: {filepath}")
    
    def save_payload_file(self, filename: str, request_data: Dict[str, Any]) -> None:
        """Save request data as base64 encoded payload."""
        json_str = json.dumps(request_data, separators=(',', ':'))
        encoded = base64.b64encode(json_str.encode('utf-8')).decode('utf-8')
        
        filepath = self.payload_dir / f"{filename}.b64"
        with open(filepath, 'w') as f:
            f.write(encoded)
        print(f"Created payload file: {filepath}")
    
    def generate_all_test_scenarios(self) -> None:
        """Generate all test scenarios and save to files."""
        print("Generating comprehensive test scenarios...")
        
        # 1. Basic recommendation scenarios
        print("\n1. Basic recommendation scenarios:")
        
        # Small dataset - sentiment likes
        small_restaurants = self.generate_restaurant_data(5, "normal")
        request = self.create_test_request("recommend_restaurants", small_restaurants, "sentiment_likes")
        self.save_request_file("small_dataset_sentiment_likes", request)
        self.save_payload_file("small_dataset_sentiment_likes", request)
        
        # Small dataset - combined sentiment
        request = self.create_test_request("recommend_restaurants", small_restaurants, "combined_sentiment")
        self.save_request_file("small_dataset_combined_sentiment", request)
        self.save_payload_file("small_dataset_combined_sentiment", request)
        
        # 2. Sentiment analysis scenarios
        print("\n2. Sentiment analysis scenarios:")
        
        # Basic sentiment analysis
        request = self.create_test_request("analyze_restaurant_sentiment", small_restaurants)
        self.save_request_file("basic_sentiment_analysis", request)
        self.save_payload_file("basic_sentiment_analysis", request)
        
        # 3. Different data sizes
        print("\n3. Different data sizes:")
        
        sizes = [1, 10, 20, 25, 50, 100]
        for size in sizes:
            restaurants = self.generate_restaurant_data(size, "normal")
            request = self.create_test_request("recommend_restaurants", restaurants, "sentiment_likes")
            self.save_request_file(f"dataset_size_{size}", request)
            self.save_payload_file(f"dataset_size_{size}", request)
        
        # 4. Different sentiment scenarios
        print("\n4. Different sentiment scenarios:")
        
        scenarios = ["high_sentiment", "low_sentiment", "mixed_sentiment", "edge_case"]
        for scenario in scenarios:
            restaurants = self.generate_restaurant_data(10, scenario)
            request = self.create_test_request("recommend_restaurants", restaurants, "sentiment_likes")
            self.save_request_file(f"scenario_{scenario}", request)
            self.save_payload_file(f"scenario_{scenario}", request)
        
        # 5. Ranking method comparison
        print("\n5. Ranking method comparison:")
        
        # Dataset where ranking methods produce different results
        comparison_restaurants = [
            {
                "id": "comp_001",
                "name": "High Likes Low Neutral",
                "address": "1 Comparison Street",
                "meal_type": ["lunch"],
                "sentiment": {"likes": 80, "dislikes": 15, "neutral": 5},  # 80% likes, 85% combined
                "location_category": "restaurant",
                "district": "Test District",
                "price_range": "$"
            },
            {
                "id": "comp_002",
                "name": "Medium Likes High Neutral",
                "address": "2 Comparison Street",
                "meal_type": ["lunch"],
                "sentiment": {"likes": 60, "dislikes": 10, "neutral": 30},  # 60% likes, 90% combined
                "location_category": "restaurant",
                "district": "Test District",
                "price_range": "$"
            },
            {
                "id": "comp_003",
                "name": "Low Likes Medium Neutral",
                "address": "3 Comparison Street",
                "meal_type": ["lunch"],
                "sentiment": {"likes": 50, "dislikes": 25, "neutral": 25},  # 50% likes, 75% combined
                "location_category": "restaurant",
                "district": "Test District",
                "price_range": "$"
            }
        ]
        
        for method in ["sentiment_likes", "combined_sentiment"]:
            request = self.create_test_request("recommend_restaurants", comparison_restaurants, method)
            self.save_request_file(f"ranking_comparison_{method}", request)
            self.save_payload_file(f"ranking_comparison_{method}", request)
        
        # 6. Error scenarios
        print("\n6. Error scenarios:")
        
        invalid_scenarios = self.generate_invalid_data_scenarios()
        for scenario_name, restaurants in invalid_scenarios.items():
            request = self.create_test_request("recommend_restaurants", restaurants, "sentiment_likes")
            self.save_request_file(f"error_{scenario_name}", request)
            self.save_payload_file(f"error_{scenario_name}", request)
        
        # 7. Performance testing
        print("\n7. Performance testing:")
        
        performance_sizes = [500, 1000, 2000]
        for size in performance_sizes:
            restaurants = self.generate_restaurant_data(size, "normal")
            request = self.create_test_request("recommend_restaurants", restaurants, "sentiment_likes")
            self.save_request_file(f"performance_test_{size}", request)
            # Note: Not creating payload files for large datasets due to size
        
        print(f"\n✅ Test data generation completed!")
        print(f"Files saved to:")
        print(f"  - Requests: {self.request_dir}")
        print(f"  - Payloads: {self.payload_dir}")
    
    def generate_expected_responses(self) -> None:
        """Generate expected response templates."""
        print("\nGenerating expected response templates...")
        
        # Success response template
        success_template = {
            "success": True,
            "data": {
                "recommendation": {
                    "id": "example_001",
                    "name": "Example Restaurant",
                    "sentiment": {"likes": 85, "dislikes": 10, "neutral": 5}
                },
                "candidates": [],
                "ranking_method": "sentiment_likes",
                "candidate_count": 0,
                "analysis_summary": {
                    "restaurant_count": 0,
                    "average_likes": 0.0,
                    "average_dislikes": 0.0,
                    "average_neutral": 0.0,
                    "top_sentiment_score": 0.0,
                    "bottom_sentiment_score": 0.0,
                    "ranking_method": "sentiment_likes"
                },
                "timestamp": "2024-01-01T00:00:00Z"
            }
        }
        
        # Error response template
        error_template = {
            "success": False,
            "error": {
                "type": "ValidationError",
                "message": "Example error message",
                "timestamp": "2024-01-01T00:00:00Z",
                "details": {
                    "invalid_restaurants": [],
                    "valid_count": 0,
                    "total_count": 0
                }
            }
        }
        
        # Sentiment analysis response template
        sentiment_template = {
            "success": True,
            "data": {
                "sentiment_analysis": {
                    "restaurant_count": 0,
                    "average_likes": 0.0,
                    "average_dislikes": 0.0,
                    "average_neutral": 0.0,
                    "top_sentiment_score": 0.0,
                    "bottom_sentiment_score": 0.0,
                    "ranking_method": "sentiment_likes"
                },
                "restaurant_count": 0,
                "ranking_method": "sentiment_likes",
                "timestamp": "2024-01-01T00:00:00Z"
            }
        }
        
        # Save templates
        templates = {
            "success_response_template": success_template,
            "error_response_template": error_template,
            "sentiment_analysis_response_template": sentiment_template
        }
        
        for name, template in templates.items():
            filepath = self.response_dir / f"{name}.json"
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(template, f, indent=2, ensure_ascii=False)
            print(f"Created response template: {filepath}")


def main():
    """Main function to generate all test data."""
    print("Restaurant Reasoning MCP Test Data Generator")
    print("=" * 50)
    
    # Change to the script directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    # Generate test data
    generator = TestDataGenerator()
    generator.generate_all_test_scenarios()
    generator.generate_expected_responses()
    
    print("\n" + "=" * 50)
    print("Test data generation completed successfully!")


if __name__ == "__main__":
    main()