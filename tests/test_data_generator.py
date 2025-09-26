"""Test Data Generator for Restaurant Search MCP Server.

This module generates test data for edge cases and error handling validation.
It creates various scenarios with different operating hours patterns, district
configurations, and data quality issues to thoroughly test the system.
"""

import json
import os
from typing import Dict, List, Any, Optional
from datetime import datetime, time
import uuid


class TestDataGenerator:
    """Generator for test data scenarios."""
    
    def __init__(self, output_dir: str = "tests/test_data"):
        """Initialize test data generator.
        
        Args:
            output_dir: Directory to output test data files
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def generate_restaurant_with_hours(self, 
                                     name: str,
                                     district: str,
                                     hours_pattern: str) -> Dict[str, Any]:
        """Generate a restaurant with specific operating hours pattern.
        
        Args:
            name: Restaurant name
            district: District name
            hours_pattern: Pattern type (breakfast_only, lunch_only, dinner_only, 
                          all_day, split_hours, midnight_cross, invalid_format)
                          
        Returns:
            Restaurant data dictionary
        """
        base_restaurant = {
            "id": str(uuid.uuid4()),
            "name": name,
            "address": f"Test Address, {district}",
            "mealType": ["test", "cuisine"],
            "sentiment": {
                "likes": 50,
                "dislikes": 5,
                "neutral": 10
            },
            "locationCategory": "Test Region",
            "district": district,
            "priceRange": "$101-200",
            "metadata": {
                "dataQuality": "complete",
                "version": "1.0.0",
                "qualityScore": 100
            }
        }
        
        # Generate operating hours based on pattern
        if hours_pattern == "breakfast_only":
            base_restaurant["operatingHours"] = {
                "Mon - Fri": ["07:00 - 11:00"],
                "Sat - Sun": ["08:00 - 11:30"],
                "Public Holiday": ["08:00 - 11:30"]
            }
        elif hours_pattern == "lunch_only":
            base_restaurant["operatingHours"] = {
                "Mon - Fri": ["11:30 - 15:30"],
                "Sat - Sun": ["12:00 - 16:00"],
                "Public Holiday": ["12:00 - 16:00"]
            }
        elif hours_pattern == "dinner_only":
            base_restaurant["operatingHours"] = {
                "Mon - Fri": ["18:00 - 22:30"],
                "Sat - Sun": ["17:30 - 23:00"],
                "Public Holiday": ["17:30 - 23:00"]
            }
        elif hours_pattern == "all_day":
            base_restaurant["operatingHours"] = {
                "Mon - Fri": ["06:00 - 23:00"],
                "Sat - Sun": ["06:00 - 23:30"],
                "Public Holiday": ["07:00 - 23:00"]
            }
        elif hours_pattern == "split_hours":
            base_restaurant["operatingHours"] = {
                "Mon - Fri": ["07:00 - 11:30", "17:30 - 22:00"],
                "Sat - Sun": ["08:00 - 12:00", "18:00 - 23:00"],
                "Public Holiday": ["08:00 - 12:00", "18:00 - 22:30"]
            }
        elif hours_pattern == "midnight_cross":
            base_restaurant["operatingHours"] = {
                "Mon - Fri": ["22:00 - 02:00"],
                "Sat - Sun": ["21:00 - 03:00"],
                "Public Holiday": ["22:00 - 02:00"]
            }
        elif hours_pattern == "invalid_format":
            base_restaurant["operatingHours"] = {
                "Mon - Fri": ["7am - 11pm"],  # Invalid format
                "Sat - Sun": ["8:00-23:00"],  # Missing space
                "Public Holiday": ["invalid"]  # Completely invalid
            }
        elif hours_pattern == "boundary_times":
            # Test exact boundary times for meal periods
            base_restaurant["operatingHours"] = {
                "Mon - Fri": ["07:00 - 11:29", "11:30 - 17:29", "17:30 - 22:30"],
                "Sat - Sun": ["07:00 - 22:30"],
                "Public Holiday": ["07:00 - 22:30"]
            }
        elif hours_pattern == "empty_hours":
            base_restaurant["operatingHours"] = {
                "Mon - Fri": [],
                "Sat - Sun": [],
                "Public Holiday": []
            }
        elif hours_pattern == "missing_days":
            base_restaurant["operatingHours"] = {
                "Mon - Fri": ["09:00 - 18:00"]
                # Missing Sat-Sun and Public Holiday
            }
        else:
            # Default pattern
            base_restaurant["operatingHours"] = {
                "Mon - Fri": ["09:00 - 18:00"],
                "Sat - Sun": ["10:00 - 17:00"],
                "Public Holiday": ["10:00 - 17:00"]
            }
        
        return base_restaurant
    
    def generate_test_district_data(self) -> Dict[str, List[Dict[str, Any]]]:
        """Generate test restaurant data for various districts with different patterns.
        
        Returns:
            Dictionary mapping district names to restaurant lists
        """
        test_data = {}
        
        # Test district with breakfast-only restaurants
        test_data["Breakfast District"] = [
            self.generate_restaurant_with_hours("Early Bird Cafe", "Breakfast District", "breakfast_only"),
            self.generate_restaurant_with_hours("Morning Glory", "Breakfast District", "breakfast_only"),
            self.generate_restaurant_with_hours("Dawn Diner", "Breakfast District", "boundary_times")
        ]
        
        # Test district with lunch-only restaurants
        test_data["Lunch District"] = [
            self.generate_restaurant_with_hours("Midday Bistro", "Lunch District", "lunch_only"),
            self.generate_restaurant_with_hours("Noon Noodles", "Lunch District", "lunch_only"),
            self.generate_restaurant_with_hours("Lunch Box", "Lunch District", "split_hours")
        ]
        
        # Test district with dinner-only restaurants
        test_data["Dinner District"] = [
            self.generate_restaurant_with_hours("Evening Eats", "Dinner District", "dinner_only"),
            self.generate_restaurant_with_hours("Night Kitchen", "Dinner District", "dinner_only"),
            self.generate_restaurant_with_hours("Late Night Diner", "Dinner District", "midnight_cross")
        ]
        
        # Test district with mixed meal times
        test_data["Mixed District"] = [
            self.generate_restaurant_with_hours("All Day Diner", "Mixed District", "all_day"),
            self.generate_restaurant_with_hours("Split Schedule", "Mixed District", "split_hours"),
            self.generate_restaurant_with_hours("Boundary Tester", "Mixed District", "boundary_times"),
            self.generate_restaurant_with_hours("Normal Hours", "Mixed District", "default")
        ]
        
        # Test district with problematic data
        test_data["Problem District"] = [
            self.generate_restaurant_with_hours("Invalid Hours", "Problem District", "invalid_format"),
            self.generate_restaurant_with_hours("Empty Hours", "Problem District", "empty_hours"),
            self.generate_restaurant_with_hours("Missing Days", "Problem District", "missing_days")
        ]
        
        return test_data
    
    def generate_test_files(self) -> Dict[str, str]:
        """Generate test data files for various scenarios.
        
        Returns:
            Dictionary mapping scenario names to file paths
        """
        test_data = self.generate_test_district_data()
        file_paths = {}
        
        for district_name, restaurants in test_data.items():
            # Create file metadata
            file_data = {
                "metadata": {
                    "timestamp": datetime.now().isoformat() + "Z",
                    "version": "1.0.0",
                    "district": district_name,
                    "locationCategory": "Test Region",
                    "recordCount": len(restaurants),
                    "fileSize": 0,
                    "sanitizedAt": datetime.now().isoformat() + "Z",
                    "sanitizationVersion": "1.0.0"
                },
                "restaurants": restaurants
            }
            
            # Write to file
            safe_name = district_name.lower().replace(" ", "_")
            file_path = os.path.join(self.output_dir, f"{safe_name}.json")
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(file_data, f, indent=2, ensure_ascii=False)
            
            file_paths[district_name] = file_path
        
        return file_paths
    
    def generate_edge_case_scenarios(self) -> List[Dict[str, Any]]:
        """Generate edge case test scenarios.
        
        Returns:
            List of edge case scenario definitions
        """
        scenarios = []
        
        # Meal time boundary scenarios
        scenarios.extend([
            {
                "name": "Exact breakfast end boundary",
                "description": "Restaurant closes exactly at 11:29 (breakfast end)",
                "restaurant": self.generate_restaurant_with_hours(
                    "Boundary Breakfast", "Test District", "custom"
                ),
                "custom_hours": {
                    "Mon - Fri": ["07:00 - 11:29"],
                    "Sat - Sun": ["07:00 - 11:29"],
                    "Public Holiday": ["07:00 - 11:29"]
                },
                "expected_meal_types": ["breakfast"]
            },
            {
                "name": "Exact lunch start boundary",
                "description": "Restaurant opens exactly at 11:30 (lunch start)",
                "restaurant": self.generate_restaurant_with_hours(
                    "Boundary Lunch", "Test District", "custom"
                ),
                "custom_hours": {
                    "Mon - Fri": ["11:30 - 15:00"],
                    "Sat - Sun": ["11:30 - 15:00"],
                    "Public Holiday": ["11:30 - 15:00"]
                },
                "expected_meal_types": ["lunch"]
            },
            {
                "name": "Spans breakfast and lunch",
                "description": "Restaurant spans breakfast-lunch boundary",
                "restaurant": self.generate_restaurant_with_hours(
                    "Span Breakfast Lunch", "Test District", "custom"
                ),
                "custom_hours": {
                    "Mon - Fri": ["10:00 - 14:00"],
                    "Sat - Sun": ["10:00 - 14:00"],
                    "Public Holiday": ["10:00 - 14:00"]
                },
                "expected_meal_types": ["breakfast", "lunch"]
            },
            {
                "name": "Spans lunch and dinner",
                "description": "Restaurant spans lunch-dinner boundary",
                "restaurant": self.generate_restaurant_with_hours(
                    "Span Lunch Dinner", "Test District", "custom"
                ),
                "custom_hours": {
                    "Mon - Fri": ["16:00 - 20:00"],
                    "Sat - Sun": ["16:00 - 20:00"],
                    "Public Holiday": ["16:00 - 20:00"]
                },
                "expected_meal_types": ["lunch", "dinner"]
            }
        ])
        
        # Apply custom hours to scenarios
        for scenario in scenarios:
            if "custom_hours" in scenario:
                scenario["restaurant"]["operatingHours"] = scenario["custom_hours"]
        
        return scenarios
    
    def create_comprehensive_test_data(self) -> Dict[str, Any]:
        """Create comprehensive test data package.
        
        Returns:
            Dictionary containing all test data and metadata
        """
        # Generate all test files
        file_paths = self.generate_test_files()
        
        # Generate edge case scenarios
        edge_cases = self.generate_edge_case_scenarios()
        
        # Create summary
        summary = {
            "generated_at": datetime.now().isoformat(),
            "output_directory": self.output_dir,
            "test_files": file_paths,
            "edge_case_scenarios": len(edge_cases),
            "total_test_restaurants": sum(
                len(data["restaurants"]) 
                for data in [json.load(open(path)) for path in file_paths.values()]
            ),
            "test_categories": {
                "breakfast_only": "Restaurants only open during breakfast hours",
                "lunch_only": "Restaurants only open during lunch hours", 
                "dinner_only": "Restaurants only open during dinner hours",
                "all_day": "Restaurants open all day across meal periods",
                "split_hours": "Restaurants with split operating hours",
                "boundary_times": "Restaurants with exact meal period boundaries",
                "invalid_data": "Restaurants with invalid or problematic data",
                "edge_cases": "Special boundary and overlap scenarios"
            }
        }
        
        # Save summary
        summary_path = os.path.join(self.output_dir, "test_data_summary.json")
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2)
        
        # Save edge cases
        edge_cases_path = os.path.join(self.output_dir, "edge_case_scenarios.json")
        with open(edge_cases_path, 'w', encoding='utf-8') as f:
            json.dump(edge_cases, f, indent=2, ensure_ascii=False)
        
        return {
            "summary": summary,
            "edge_cases": edge_cases,
            "file_paths": file_paths
        }


def main():
    """Generate test data when run directly."""
    print("🧪 Generating test data for Restaurant Search MCP Server...")
    
    generator = TestDataGenerator()
    result = generator.create_comprehensive_test_data()
    
    print(f"✅ Test data generated successfully!")
    print(f"📁 Output directory: {generator.output_dir}")
    print(f"📊 Generated files: {len(result['file_paths'])}")
    print(f"🎯 Edge case scenarios: {len(result['edge_cases'])}")
    print(f"🍽️  Total test restaurants: {result['summary']['total_test_restaurants']}")
    
    print("\n📋 Generated test files:")
    for district, path in result['file_paths'].items():
        print(f"  - {district}: {path}")
    
    print(f"\n📄 Summary file: {os.path.join(generator.output_dir, 'test_data_summary.json')}")
    print(f"🔍 Edge cases file: {os.path.join(generator.output_dir, 'edge_case_scenarios.json')}")
    
    print("\n🚀 Use this test data with the comprehensive test scenarios!")


if __name__ == "__main__":
    main()