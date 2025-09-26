"""Unit tests for RestaurantService.

This module contains comprehensive unit tests for the RestaurantService class,
testing district-based search, meal type search, combined search, and error
handling using actual restaurant data from config/restaurants/ directory.
"""

import unittest
import tempfile
import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock, Mock

from services.restaurant_service import RestaurantService, RestaurantSearchError
from models.restaurant_models import (
    Restaurant, OperatingHours, Sentiment, RestaurantMetadata, 
    RestaurantDataFile, FileMetadata
)


class TestRestaurantService(unittest.TestCase):
    """Test cases for RestaurantService class."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        # Use actual config directory for integration testing
        self.config_path = "config"
        self.service = RestaurantService(self.config_path)
        
        # Create sample restaurant data for testing
        self.sample_restaurant_1 = Restaurant(
            id="test-1",
            name="Test Breakfast Restaurant",
            address="123 Test Street",
            meal_type=["breakfast", "western"],
            sentiment=Sentiment(likes=50, dislikes=5, neutral=10),
            location_category="Hong Kong Island",
            district="Admiralty",
            price_range="$50-100",
            operating_hours=OperatingHours(
                mon_fri=["07:00 - 11:00"],
                sat_sun=["08:00 - 12:00"],
                public_holiday=["08:00 - 12:00"]
            ),
            metadata=RestaurantMetadata(
                data_quality="complete",
                version="1.0.0",
                quality_score=100
            )
        )
        
        self.sample_restaurant_2 = Restaurant(
            id="test-2",
            name="Test Lunch Restaurant",
            address="456 Test Avenue",
            meal_type=["lunch", "chinese"],
            sentiment=Sentiment(likes=80, dislikes=10, neutral=15),
            location_category="Kowloon",
            district="Tsim Sha Tsui",
            price_range="$100-200",
            operating_hours=OperatingHours(
                mon_fri=["12:00 - 15:00"],
                sat_sun=["11:30 - 16:00"],
                public_holiday=["11:30 - 16:00"]
            ),
            metadata=RestaurantMetadata(
                data_quality="complete",
                version="1.0.0",
                quality_score=95
            )
        )
        
        self.sample_restaurant_3 = Restaurant(
            id="test-3",
            name="Test All Day Restaurant",
            address="789 Test Road",
            meal_type=["breakfast", "lunch", "dinner"],
            sentiment=Sentiment(likes=120, dislikes=8, neutral=20),
            location_category="Hong Kong Island",
            district="Central district",
            price_range="$200-300",
            operating_hours=OperatingHours(
                mon_fri=["07:00 - 22:00"],
                sat_sun=["08:00 - 23:00"],
                public_holiday=["08:00 - 23:00"]
            ),
            metadata=RestaurantMetadata(
                data_quality="complete",
                version="1.0.0",
                quality_score=98
            )
        )
        
        # Sample file metadata
        self.sample_file_metadata = FileMetadata(
            timestamp="2025-09-26T10:00:00Z",
            version="1.0.0",
            district="Test District",
            location_category="Test Region",
            record_count=3,
            file_size=1024,
            sanitized_at="2025-09-26T10:00:00Z",
            sanitization_version="1.0.0"
        )
    
    def test_initialization(self):
        """Test RestaurantService initialization."""
        service = RestaurantService("config")
        self.assertIsNotNone(service.district_service)
        self.assertIsNotNone(service.time_service)
        self.assertIsNotNone(service.data_access_client)
        self.assertFalse(service._initialized)
    
    @patch('services.restaurant_service.DataAccessClient')
    def test_search_by_districts_success(self, mock_data_client_class):
        """Test successful district-based search."""
        # Mock the data access client
        mock_data_client = Mock()
        mock_data_client_class.return_value = mock_data_client
        
        # Create sample restaurant data file
        sample_data_file = RestaurantDataFile(
            metadata=self.sample_file_metadata,
            restaurants=[self.sample_restaurant_1, self.sample_restaurant_2]
        )
        
        mock_data_client.get_multiple_restaurant_data.return_value = {
            'admiralty': sample_data_file
        }
        
        # Create service with mocked client
        service = RestaurantService(self.config_path)
        service.data_access_client = mock_data_client
        
        # Test search
        results = service.search_by_districts(['Admiralty'])
        
        # Verify results
        self.assertEqual(len(results), 2)
        self.assertIn(self.sample_restaurant_1, results)
        self.assertIn(self.sample_restaurant_2, results)
        
        # Verify mock was called correctly
        mock_data_client.get_multiple_restaurant_data.assert_called_once()
        call_args = mock_data_client.get_multiple_restaurant_data.call_args[0][0]
        self.assertIn(('hong-kong-island', 'admiralty'), call_args)
    
    def test_search_by_districts_empty_list(self):
        """Test error handling for empty districts list."""
        with self.assertRaises(RestaurantSearchError) as context:
            self.service.search_by_districts([])
        
        self.assertIn("Districts list cannot be empty", str(context.exception))
    
    def test_search_by_districts_invalid_district(self):
        """Test error handling for invalid district names."""
        with self.assertRaises(RestaurantSearchError) as context:
            self.service.search_by_districts(['InvalidDistrict'])
        
        self.assertIn("Invalid districts", str(context.exception))
        self.assertIn("InvalidDistrict", str(context.exception))
    
    @patch('services.restaurant_service.DataAccessClient')
    def test_search_by_meal_types_success(self, mock_data_client_class):
        """Test successful meal type-based search."""
        # Mock the data access client
        mock_data_client = Mock()
        mock_data_client_class.return_value = mock_data_client
        
        # Create sample restaurant data file with restaurants serving different meals
        sample_data_file = RestaurantDataFile(
            metadata=self.sample_file_metadata,
            restaurants=[self.sample_restaurant_1, self.sample_restaurant_2, self.sample_restaurant_3]
        )
        
        mock_data_client.get_multiple_restaurant_data.return_value = {
            'admiralty': sample_data_file
        }
        
        # Create service with mocked client
        service = RestaurantService(self.config_path)
        service.data_access_client = mock_data_client
        
        # Test search for breakfast
        results = service.search_by_meal_types(['breakfast'])
        
        # Should return restaurants 1 and 3 (both serve breakfast)
        self.assertEqual(len(results), 2)
        restaurant_names = [r.name for r in results]
        self.assertIn("Test Breakfast Restaurant", restaurant_names)
        self.assertIn("Test All Day Restaurant", restaurant_names)
    
    def test_search_by_meal_types_empty_list(self):
        """Test error handling for empty meal types list."""
        with self.assertRaises(RestaurantSearchError) as context:
            self.service.search_by_meal_types([])
        
        self.assertIn("Meal types list cannot be empty", str(context.exception))
    
    def test_search_by_meal_types_invalid_meal_type(self):
        """Test error handling for invalid meal types."""
        with self.assertRaises(RestaurantSearchError) as context:
            self.service.search_by_meal_types(['invalidmeal'])
        
        self.assertIn("Invalid meal types", str(context.exception))
        self.assertIn("invalidmeal", str(context.exception))
    
    @patch('services.restaurant_service.DataAccessClient')
    def test_search_combined_districts_and_meal_types(self, mock_data_client_class):
        """Test combined search with both districts and meal types."""
        # Mock the data access client
        mock_data_client = Mock()
        mock_data_client_class.return_value = mock_data_client
        
        # Create sample restaurant data file
        sample_data_file = RestaurantDataFile(
            metadata=self.sample_file_metadata,
            restaurants=[self.sample_restaurant_1, self.sample_restaurant_2, self.sample_restaurant_3]
        )
        
        mock_data_client.get_multiple_restaurant_data.return_value = {
            'admiralty': sample_data_file
        }
        
        # Create service with mocked client
        service = RestaurantService(self.config_path)
        service.data_access_client = mock_data_client
        
        # Test combined search
        results = service.search_combined(
            districts=['Admiralty'],
            meal_types=['breakfast']
        )
        
        # Should return restaurants that are in Admiralty AND serve breakfast
        self.assertEqual(len(results), 2)
        restaurant_names = [r.name for r in results]
        self.assertIn("Test Breakfast Restaurant", restaurant_names)
        self.assertIn("Test All Day Restaurant", restaurant_names)
    
    @patch('services.restaurant_service.DataAccessClient')
    def test_search_combined_districts_only(self, mock_data_client_class):
        """Test combined search with districts only."""
        # Mock the data access client
        mock_data_client = Mock()
        mock_data_client_class.return_value = mock_data_client
        
        sample_data_file = RestaurantDataFile(
            metadata=self.sample_file_metadata,
            restaurants=[self.sample_restaurant_1]
        )
        
        mock_data_client.get_multiple_restaurant_data.return_value = {
            'admiralty': sample_data_file
        }
        
        # Create service with mocked client
        service = RestaurantService(self.config_path)
        service.data_access_client = mock_data_client
        
        # Test search with districts only
        results = service.search_combined(districts=['Admiralty'])
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].name, "Test Breakfast Restaurant")
    
    @patch('services.restaurant_service.DataAccessClient')
    def test_search_combined_meal_types_only(self, mock_data_client_class):
        """Test combined search with meal types only."""
        # Mock the data access client
        mock_data_client = Mock()
        mock_data_client_class.return_value = mock_data_client
        
        sample_data_file = RestaurantDataFile(
            metadata=self.sample_file_metadata,
            restaurants=[self.sample_restaurant_1, self.sample_restaurant_2]
        )
        
        mock_data_client.get_multiple_restaurant_data.return_value = {
            'admiralty': sample_data_file
        }
        
        # Create service with mocked client
        service = RestaurantService(self.config_path)
        service.data_access_client = mock_data_client
        
        # Test search with meal types only
        results = service.search_combined(meal_types=['breakfast'])
        
        # Should return only the breakfast restaurant
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].name, "Test Breakfast Restaurant")
    
    def test_search_combined_no_parameters(self):
        """Test error handling when no parameters are provided."""
        with self.assertRaises(RestaurantSearchError) as context:
            self.service.search_combined()
        
        self.assertIn("At least one of districts or meal_types must be provided", str(context.exception))
    
    def test_get_available_districts(self):
        """Test getting available districts."""
        # This test uses actual configuration
        districts = self.service.get_available_districts()
        
        # Verify we get a dictionary with regions
        self.assertIsInstance(districts, dict)
        self.assertGreater(len(districts), 0)
        
        # Check that we have expected regions
        expected_regions = ['Hong Kong Island', 'Kowloon', 'New Territories', 'Islands']
        for region in expected_regions:
            if region in districts:
                self.assertIsInstance(districts[region], list)
                self.assertGreater(len(districts[region]), 0)
    
    @patch('services.restaurant_service.DataAccessClient')
    def test_get_restaurant_count_by_district(self, mock_data_client_class):
        """Test getting restaurant count by district."""
        # Mock the data access client
        mock_data_client = Mock()
        mock_data_client_class.return_value = mock_data_client
        
        sample_data_file = RestaurantDataFile(
            metadata=self.sample_file_metadata,
            restaurants=[self.sample_restaurant_1, self.sample_restaurant_2]
        )
        
        mock_data_client.get_multiple_restaurant_data.return_value = {
            'admiralty': sample_data_file
        }
        
        # Create service with mocked client
        service = RestaurantService(self.config_path)
        service.data_access_client = mock_data_client
        
        # Test count
        counts = service.get_restaurant_count_by_district(['Admiralty'])
        
        self.assertEqual(counts['Admiralty'], 2)
    
    def test_get_meal_type_analysis_empty_list(self):
        """Test meal type analysis with empty restaurant list."""
        analysis = self.service.get_meal_type_analysis([])
        
        expected = {
            'total_restaurants': 0,
            'meal_type_counts': {'breakfast': 0, 'lunch': 0, 'dinner': 0},
            'restaurants_by_meal_type': {'breakfast': [], 'lunch': [], 'dinner': []}
        }
        
        self.assertEqual(analysis, expected)
    
    def test_get_meal_type_analysis_with_restaurants(self):
        """Test meal type analysis with restaurant list."""
        restaurants = [self.sample_restaurant_1, self.sample_restaurant_2, self.sample_restaurant_3]
        analysis = self.service.get_meal_type_analysis(restaurants)
        
        # Verify structure
        self.assertEqual(analysis['total_restaurants'], 3)
        self.assertIn('meal_type_counts', analysis)
        self.assertIn('restaurants_by_meal_type', analysis)
        
        # Check that breakfast count includes restaurants 1 and 3
        self.assertGreaterEqual(analysis['meal_type_counts']['breakfast'], 2)
    
    def test_test_services(self):
        """Test the service testing functionality."""
        results = self.service.test_services()
        
        # Verify structure
        self.assertIn('district_service', results)
        self.assertIn('s3_connection', results)
        self.assertIn('time_service', results)
        
        # All results should be boolean
        for key, value in results.items():
            self.assertIsInstance(value, bool)
    
    @patch('services.restaurant_service.DataAccessClient')
    def test_data_access_error_handling(self, mock_data_client_class):
        """Test error handling when data access fails."""
        # Mock the data access client to raise an exception
        mock_data_client = Mock()
        mock_data_client_class.return_value = mock_data_client
        mock_data_client.get_multiple_restaurant_data.side_effect = Exception("S3 connection failed")
        
        # Create service with mocked client
        service = RestaurantService(self.config_path)
        service.data_access_client = mock_data_client
        
        # Test that search raises RestaurantSearchError
        with self.assertRaises(RestaurantSearchError) as context:
            service.search_by_districts(['Admiralty'])
        
        self.assertIn("Failed to retrieve restaurant data", str(context.exception))
    
    def test_integration_with_actual_data(self):
        """Integration test using actual restaurant data files."""
        # This test requires actual config files to be present
        if not Path("config/restaurants/hong-kong-island/admiralty.json").exists():
            self.skipTest("Actual restaurant data files not available")
        
        # Test with actual data - this will use real S3 if credentials are available
        # or fail gracefully if not
        try:
            # Test getting available districts (should work with local config)
            districts = self.service.get_available_districts()
            self.assertGreater(len(districts), 0)
            
            # Test service testing (may fail on S3 but should test other services)
            test_results = self.service.test_services()
            self.assertIn('district_service', test_results)
            
        except Exception as e:
            # If this fails due to missing AWS credentials, that's expected
            if "credentials" in str(e).lower() or "aws" in str(e).lower():
                self.skipTest(f"AWS credentials not available for integration test: {e}")
            else:
                raise
    
    def test_meal_type_filtering_edge_cases(self):
        """Test meal type filtering with edge cases."""
        # Create restaurant with complex operating hours
        complex_restaurant = Restaurant(
            id="complex-1",
            name="Complex Hours Restaurant",
            address="Complex Street",
            meal_type=["mixed"],
            sentiment=Sentiment(likes=50, dislikes=5, neutral=10),
            location_category="Test",
            district="Test",
            price_range="$100-200",
            operating_hours=OperatingHours(
                mon_fri=["11:00 - 14:00", "18:00 - 22:00"],  # Lunch and dinner
                sat_sun=["10:00 - 15:00"],  # Brunch (covers breakfast and lunch)
                public_holiday=["08:00 - 23:00"]  # All day
            ),
            metadata=RestaurantMetadata(
                data_quality="complete",
                version="1.0.0",
                quality_score=90
            )
        )
        
        # Test meal type analysis
        analysis = self.service.get_meal_type_analysis([complex_restaurant])
        
        # This restaurant should serve multiple meal types
        self.assertEqual(analysis['total_restaurants'], 1)
        # Should serve at least lunch (11:00-14:00 overlaps with lunch period 11:30-17:29)
        self.assertGreaterEqual(analysis['meal_type_counts']['lunch'], 1)


if __name__ == '__main__':
    unittest.main()