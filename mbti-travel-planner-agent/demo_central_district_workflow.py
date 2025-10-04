#!/usr/bin/env python3
"""
Demo script for Central District Search Workflow

This script demonstrates the Central district search workflow with mock data
to show how it would work when the gateway service is available.
"""

import json
import logging
import sys
from typing import Dict, Any, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_mock_restaurant_data() -> List[Dict[str, Any]]:
    """Create mock restaurant data for demonstration."""
    return [
        {
            "id": "central_001",
            "name": "The Peak Restaurant",
            "address": "Level 52, International Finance Centre, 8 Finance Street, Central",
            "district": "Central district",
            "price_range": "$$$",
            "meal_type": ["lunch", "dinner"],
            "sentiment": {
                "likes": 145,
                "dislikes": 12,
                "neutral": 23,
                "total_responses": 180,
                "likes_percentage": 80.6,
                "combined_positive_percentage": 93.3
            }
        },
        {
            "id": "central_002", 
            "name": "Harbour View Dim Sum",
            "address": "Shop 3-4, Ground Floor, Central Building, Pedder Street, Central",
            "district": "Central district",
            "price_range": "$$",
            "meal_type": ["breakfast", "lunch"],
            "sentiment": {
                "likes": 98,
                "dislikes": 8,
                "neutral": 14,
                "total_responses": 120,
                "likes_percentage": 81.7,
                "combined_positive_percentage": 93.3
            }
        },
        {
            "id": "central_003",
            "name": "Central Café & Bistro",
            "address": "15-19 Lan Kwai Fong, Central",
            "district": "Central district", 
            "price_range": "$$",
            "meal_type": ["breakfast", "lunch", "dinner"],
            "sentiment": {
                "likes": 76,
                "dislikes": 15,
                "neutral": 19,
                "total_responses": 110,
                "likes_percentage": 69.1,
                "combined_positive_percentage": 86.4
            }
        },
        {
            "id": "central_004",
            "name": "Executive Club Restaurant",
            "address": "45th Floor, Two International Finance Centre, Central",
            "district": "Central district",
            "price_range": "$$$$",
            "meal_type": ["lunch", "dinner"],
            "sentiment": {
                "likes": 203,
                "dislikes": 18,
                "neutral": 29,
                "total_responses": 250,
                "likes_percentage": 81.2,
                "combined_positive_percentage": 92.8
            }
        },
        {
            "id": "central_005",
            "name": "Morning Glory Breakfast House",
            "address": "Ground Floor, 28 Wellington Street, Central",
            "district": "Central district",
            "price_range": "$",
            "meal_type": ["breakfast"],
            "sentiment": {
                "likes": 67,
                "dislikes": 5,
                "neutral": 8,
                "total_responses": 80,
                "likes_percentage": 83.8,
                "combined_positive_percentage": 93.8
            }
        }
    ]


def demo_workflow_formatting():
    """Demonstrate the workflow formatting with mock data."""
    logger.info("Central District Search Workflow Demo")
    logger.info("=" * 50)
    
    # Import the workflow classes
    sys.path.insert(0, '.')
    from services.central_district_workflow import CentralDistrictWorkflow
    
    # Create mock data
    restaurants = create_mock_restaurant_data()
    
    # Create workflow instance (won't actually connect to gateway)
    workflow = CentralDistrictWorkflow(environment="development")
    
    # Demo 1: Basic restaurant formatting
    logger.info("\n1. Basic Restaurant Details Formatting:")
    logger.info("-" * 40)
    
    details_section = workflow._format_restaurant_details(restaurants, limit=3)
    print(details_section)
    
    # Demo 2: Search header formatting
    logger.info("\n2. Search Header Formatting:")
    logger.info("-" * 40)
    
    header = workflow._format_search_header(restaurants, meal_types=["lunch"], partial_results=False)
    print(header)
    
    # Demo 3: Single restaurant formatting with reasoning
    logger.info("\n3. Single Restaurant with Recommendation Reasoning:")
    logger.info("-" * 40)
    
    single_restaurant = workflow._format_single_restaurant(
        restaurants[0], 
        include_index=1, 
        include_reasoning=True
    )
    print(single_restaurant)
    
    # Demo 4: Mock recommendation data formatting
    logger.info("\n4. Recommendations Section Formatting:")
    logger.info("-" * 40)
    
    mock_recommendations = {
        "recommendation": restaurants[0],  # Top recommendation
        "analysis_summary": {
            "restaurant_count": len(restaurants),
            "average_likes": 78.5,
            "top_sentiment_score": 83.8
        }
    }
    
    rec_section = workflow._format_recommendations_section(mock_recommendations)
    print(rec_section)
    
    # Demo 5: Complete response formatting
    logger.info("\n5. Complete Response Formatting:")
    logger.info("-" * 40)
    
    complete_response = workflow._format_complete_response(
        restaurants=restaurants,
        recommendations=mock_recommendations,
        meal_types=["lunch"],
        partial_results=False,
        search_metadata={
            "total_results": len(restaurants),
            "execution_time_ms": 245.7,
            "search_criteria": {
                "districts": ["Central district"],
                "meal_types": ["lunch"]
            }
        }
    )
    print(complete_response)
    
    # Demo 6: No results response
    logger.info("\n6. No Results Response:")
    logger.info("-" * 40)
    
    no_results_response = workflow._format_no_results_response(meal_types=["breakfast"])
    print(no_results_response)
    
    # Demo 7: Error response
    logger.info("\n7. Error Response:")
    logger.info("-" * 40)
    
    error_response = workflow._format_error_response(
        Exception("Connection timeout"), 
        meal_types=["dinner"]
    )
    print(error_response)


def demo_recommendation_reasoning():
    """Demonstrate recommendation reasoning generation."""
    logger.info("\n8. Recommendation Reasoning Examples:")
    logger.info("-" * 40)
    
    sys.path.insert(0, '.')
    from services.central_district_workflow import CentralDistrictWorkflow
    
    workflow = CentralDistrictWorkflow(environment="development")
    
    # Test different sentiment scenarios
    sentiment_scenarios = [
        {"likes": 95, "dislikes": 3, "neutral": 2, "description": "Excellent (95% likes)"},
        {"likes": 80, "dislikes": 10, "neutral": 10, "description": "Very Good (80% likes)"},
        {"likes": 70, "dislikes": 20, "neutral": 10, "description": "Good (70% likes)"},
        {"likes": 60, "dislikes": 25, "neutral": 15, "description": "Decent (60% likes)"},
        {"likes": 45, "dislikes": 35, "neutral": 20, "description": "Mixed (45% likes)"},
        {"likes": 0, "dislikes": 0, "neutral": 0, "description": "No data"}
    ]
    
    for scenario in sentiment_scenarios:
        reasoning = workflow._generate_recommendation_reasoning(scenario)
        print(f"• {scenario['description']}: {reasoning}")


def demo_meal_type_filtering():
    """Demonstrate meal type filtering logic."""
    logger.info("\n9. Meal Type Filtering Examples:")
    logger.info("-" * 40)
    
    restaurants = create_mock_restaurant_data()
    
    # Filter by breakfast
    breakfast_restaurants = [r for r in restaurants if "breakfast" in r.get("meal_type", [])]
    print(f"Breakfast restaurants: {len(breakfast_restaurants)}")
    for r in breakfast_restaurants:
        print(f"  • {r['name']} - {', '.join(r['meal_type'])}")
    
    # Filter by lunch
    lunch_restaurants = [r for r in restaurants if "lunch" in r.get("meal_type", [])]
    print(f"\nLunch restaurants: {len(lunch_restaurants)}")
    for r in lunch_restaurants:
        print(f"  • {r['name']} - {', '.join(r['meal_type'])}")
    
    # Filter by dinner
    dinner_restaurants = [r for r in restaurants if "dinner" in r.get("meal_type", [])]
    print(f"\nDinner restaurants: {len(dinner_restaurants)}")
    for r in dinner_restaurants:
        print(f"  • {r['name']} - {', '.join(r['meal_type'])}")


def main():
    """Main demo execution."""
    try:
        demo_workflow_formatting()
        demo_recommendation_reasoning()
        demo_meal_type_filtering()
        
        logger.info("\n" + "=" * 50)
        logger.info("Demo completed successfully!")
        logger.info("This shows how the Central district workflow would format")
        logger.info("real restaurant data when the gateway service is available.")
        
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())