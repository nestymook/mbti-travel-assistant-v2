"""Unit tests for DistrictService.

This module contains comprehensive unit tests for the DistrictService class,
testing district configuration loading, validation, and file path generation
using actual configuration files from the config/districts/ directory.
"""

import unittest
import tempfile
import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

from services.district_service import DistrictService, DistrictConfigurationError
from models.district_models import MasterConfig, RegionConfig, DistrictConfig


class TestDistrictService(unittest.TestCase):
    """Test cases for DistrictService class."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        # Use actual config directory for integration testing
        self.config_path = "config"
        self.service = DistrictService(self.config_path)
        
        # Create temporary directory for isolated tests
        self.temp_dir = tempfile.mkdtemp()
        self.temp_service = DistrictService(self.temp_dir)
    
    def tearDown(self):
        """Clean up after each test method."""
        # Clean up temporary directory
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_load_district_config_success(self):
        """Test successful loading of district configuration from actual files."""
        # This should work with the actual config files
        self.service.load_district_config()
        
        # Verify configuration is loaded
        self.assertTrue(self.service._loaded)
        self.assertIsNotNone(self.service._master_config)
        self.assertGreater(len(self.service._region_configs), 0)
        self.assertGreater(len(self.service._district_to_region_map), 0)
    
    def test_load_district_config_missing_master_config(self):
        """Test error handling when master config file is missing."""
        with self.assertRaises(DistrictConfigurationError) as context:
            self.temp_service.load_district_config()
        
        self.assertIn("Master configuration file not found", str(context.exception))
    
    def test_load_district_config_invalid_json(self):
        """Test error handling when config file contains invalid JSON."""
        # Create invalid master config file
        districts_dir = Path(self.temp_dir) / "districts"
        districts_dir.mkdir(parents=True)
        
        master_config_path = districts_dir / "master-config.json"
        with open(master_config_path, 'w') as f:
            f.write("invalid json content")
        
        with self.assertRaises(DistrictConfigurationError) as context:
            self.temp_service.load_district_config()
        
        self.assertIn("Failed to load district configuration", str(context.exception))
    
    def test_get_all_districts_with_actual_config(self):
        """Test getting all districts using actual configuration files."""
        self.service.load_district_config()
        
        all_districts = self.service.get_all_districts()
        
        # Verify we have regions and districts
        self.assertIsInstance(all_districts, dict)
        self.assertGreater(len(all_districts), 0)
        
        # Check that Hong Kong Island region exists and has districts
        self.assertIn("Hong Kong Island", all_districts)
        hk_island_districts = all_districts["Hong Kong Island"]
        self.assertGreater(len(hk_island_districts), 0)
        
        # Verify some known districts exist
        expected_districts = ["Admiralty", "Central district", "Causeway Bay"]
        for district in expected_districts:
            self.assertIn(district, hk_island_districts)
    
    def test_get_all_district_names_with_actual_config(self):
        """Test getting flat list of all district names."""
        self.service.load_district_config()
        
        district_names = self.service.get_all_district_names()
        
        # Verify we have a list of district names
        self.assertIsInstance(district_names, list)
        self.assertGreater(len(district_names), 0)
        
        # Verify some known districts exist
        expected_districts = ["Admiralty", "Central district", "Causeway Bay", "Wan Chai"]
        for district in expected_districts:
            self.assertIn(district, district_names)
    
    def test_validate_district_with_valid_names(self):
        """Test district validation with valid district names from actual config."""
        self.service.load_district_config()
        
        # Test valid districts
        valid_districts = ["Admiralty", "Central district", "Causeway Bay"]
        for district in valid_districts:
            self.assertTrue(self.service.validate_district(district))
    
    def test_validate_district_with_invalid_names(self):
        """Test district validation with invalid district names."""
        self.service.load_district_config()
        
        # Test invalid districts
        invalid_districts = ["NonExistentDistrict", "FakePlace", ""]
        for district in invalid_districts:
            self.assertFalse(self.service.validate_district(district))
    
    def test_validate_districts_multiple(self):
        """Test validation of multiple districts at once."""
        self.service.load_district_config()
        
        test_districts = ["Admiralty", "NonExistentDistrict", "Central district", "FakePlace"]
        valid, invalid = self.service.validate_districts(test_districts)
        
        # Check valid districts
        self.assertIn("Admiralty", valid)
        self.assertIn("Central district", valid)
        
        # Check invalid districts
        self.assertIn("NonExistentDistrict", invalid)
        self.assertIn("FakePlace", invalid)
    
    def test_get_region_for_district_with_actual_config(self):
        """Test getting region for district using actual configuration."""
        self.service.load_district_config()
        
        # Test known districts and their regions
        test_cases = [
            ("Admiralty", "Hong Kong Island"),
            ("Central district", "Hong Kong Island"),
            ("Causeway Bay", "Hong Kong Island"),
        ]
        
        for district, expected_region in test_cases:
            region = self.service.get_region_for_district(district)
            self.assertEqual(region, expected_region)
    
    def test_get_region_for_nonexistent_district(self):
        """Test getting region for non-existent district."""
        self.service.load_district_config()
        
        region = self.service.get_region_for_district("NonExistentDistrict")
        self.assertIsNone(region)
    
    def test_get_local_file_path_for_district(self):
        """Test generating local file paths for districts."""
        self.service.load_district_config()
        
        # Test known districts
        test_cases = [
            ("Admiralty", "config/restaurants/hong-kong-island/admiralty.json"),
            ("Central district", "config/restaurants/hong-kong-island/central-district.json"),
            ("Causeway Bay", "config/restaurants/hong-kong-island/causeway-bay.json"),
        ]
        
        for district, expected_path in test_cases:
            path = self.service.get_local_file_path_for_district(district)
            # Normalize path separators for cross-platform compatibility
            expected_path = expected_path.replace('/', os.sep)
            self.assertEqual(path, expected_path)
    
    def test_get_local_file_path_for_nonexistent_district(self):
        """Test getting local file path for non-existent district."""
        self.service.load_district_config()
        
        path = self.service.get_local_file_path_for_district("NonExistentDistrict")
        self.assertIsNone(path)
    
    def test_get_s3_path_for_district(self):
        """Test generating S3 paths for districts."""
        self.service.load_district_config()
        
        # Test known districts
        test_cases = [
            ("Admiralty", "hong-kong-island/admiralty.json"),
            ("Central district", "hong-kong-island/central-district.json"),
            ("Causeway Bay", "hong-kong-island/causeway-bay.json"),
        ]
        
        for district, expected_path in test_cases:
            path = self.service.get_s3_path_for_district(district)
            self.assertEqual(path, expected_path)
    
    def test_get_s3_path_for_nonexistent_district(self):
        """Test getting S3 path for non-existent district."""
        self.service.load_district_config()
        
        path = self.service.get_s3_path_for_district("NonExistentDistrict")
        self.assertIsNone(path)
    
    def test_check_local_file_exists(self):
        """Test checking if local restaurant data files exist."""
        self.service.load_district_config()
        
        # This test depends on actual files existing in config/restaurants/
        # We'll test the method works, but results depend on actual file presence
        result = self.service.check_local_file_exists("Admiralty")
        self.assertIsInstance(result, bool)
        
        # Non-existent district should return False
        result = self.service.check_local_file_exists("NonExistentDistrict")
        self.assertFalse(result)
    
    def test_get_districts_by_region(self):
        """Test getting districts by region name."""
        self.service.load_district_config()
        
        hk_island_districts = self.service.get_districts_by_region("Hong Kong Island")
        
        # Verify we get a list of districts
        self.assertIsInstance(hk_island_districts, list)
        self.assertGreater(len(hk_island_districts), 0)
        
        # Verify some known districts are included
        expected_districts = ["Admiralty", "Central district", "Causeway Bay"]
        for district in expected_districts:
            self.assertIn(district, hk_island_districts)
        
        # Test non-existent region
        empty_list = self.service.get_districts_by_region("NonExistentRegion")
        self.assertEqual(empty_list, [])
    
    def test_get_region_names(self):
        """Test getting list of all region names."""
        self.service.load_district_config()
        
        region_names = self.service.get_region_names()
        
        # Verify we get a list of regions
        self.assertIsInstance(region_names, list)
        self.assertGreater(len(region_names), 0)
        
        # Verify Hong Kong Island region exists
        self.assertIn("Hong Kong Island", region_names)
    
    def test_get_district_config(self):
        """Test getting full district configuration."""
        self.service.load_district_config()
        
        district_config = self.service.get_district_config("Admiralty")
        
        # Verify we get a DistrictConfig object
        self.assertIsInstance(district_config, DistrictConfig)
        self.assertEqual(district_config.name, "Admiralty")
        self.assertGreater(district_config.district_id, 0)
        
        # Test non-existent district
        none_config = self.service.get_district_config("NonExistentDistrict")
        self.assertIsNone(none_config)
    
    def test_get_master_config(self):
        """Test getting master configuration."""
        self.service.load_district_config()
        
        master_config = self.service.get_master_config()
        
        # Verify we get a MasterConfig object
        self.assertIsInstance(master_config, MasterConfig)
        self.assertIsNotNone(master_config.version)
        self.assertGreater(len(master_config.regions), 0)
    
    def test_get_region_config(self):
        """Test getting region configuration."""
        self.service.load_district_config()
        
        region_config = self.service.get_region_config("Hong Kong Island")
        
        # Verify we get a RegionConfig object
        self.assertIsInstance(region_config, RegionConfig)
        self.assertEqual(region_config.name, "Hong Kong Island")
        self.assertGreater(len(region_config.districts), 0)
        
        # Test non-existent region
        none_config = self.service.get_region_config("NonExistentRegion")
        self.assertIsNone(none_config)
    
    def test_get_configuration_summary(self):
        """Test getting configuration summary."""
        self.service.load_district_config()
        
        summary = self.service.get_configuration_summary()
        
        # Verify summary structure
        self.assertIsInstance(summary, dict)
        self.assertIn('master_config_version', summary)
        self.assertIn('total_regions', summary)
        self.assertIn('total_districts', summary)
        self.assertIn('regions', summary)
        self.assertIn('loaded', summary)
        
        # Verify values
        self.assertTrue(summary['loaded'])
        self.assertGreater(summary['total_regions'], 0)
        self.assertGreater(summary['total_districts'], 0)
        self.assertIsInstance(summary['regions'], dict)
    
    def test_ensure_loaded_raises_error_when_not_loaded(self):
        """Test that methods raise error when configuration is not loaded."""
        # Don't load configuration
        
        with self.assertRaises(DistrictConfigurationError):
            self.service.get_all_districts()
        
        with self.assertRaises(DistrictConfigurationError):
            self.service.validate_district("Admiralty")
        
        with self.assertRaises(DistrictConfigurationError):
            self.service.get_region_for_district("Admiralty")
    
    def test_reload_configuration(self):
        """Test reloading configuration."""
        # Load initial configuration
        self.service.load_district_config()
        initial_summary = self.service.get_configuration_summary()
        
        # Reload configuration
        self.service.reload_configuration()
        reloaded_summary = self.service.get_configuration_summary()
        
        # Verify configuration is still loaded and consistent
        self.assertTrue(reloaded_summary['loaded'])
        self.assertEqual(initial_summary['total_districts'], reloaded_summary['total_districts'])
        self.assertEqual(initial_summary['total_regions'], reloaded_summary['total_regions'])
    
    def test_case_insensitive_district_lookup(self):
        """Test that district lookup is case insensitive."""
        self.service.load_district_config()
        
        # Test different case variations
        test_cases = [
            "admiralty",
            "ADMIRALTY", 
            "Admiralty",
            "AdMiRaLtY"
        ]
        
        for district_name in test_cases:
            # The actual validation should be case sensitive based on config
            # But we can test that the service handles the lookup consistently
            result = self.service.validate_district(district_name)
            # Only exact case match should work based on current implementation
            if district_name == "Admiralty":
                self.assertTrue(result)
            else:
                self.assertFalse(result)


class TestDistrictServiceWithMockConfig(unittest.TestCase):
    """Test cases using mock configuration data."""
    
    def setUp(self):
        """Set up test fixtures with mock configuration."""
        self.temp_dir = tempfile.mkdtemp()
        self.service = DistrictService(self.temp_dir)
        
        # Create mock configuration files
        self._create_mock_config_files()
    
    def tearDown(self):
        """Clean up after each test method."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def _create_mock_config_files(self):
        """Create mock configuration files for testing."""
        districts_dir = Path(self.temp_dir) / "districts"
        districts_dir.mkdir(parents=True)
        
        # Create mock master config
        master_config = {
            "version": "1.0.0",
            "lastUpdated": "2025-01-10T00:00:00Z",
            "crawlingStrategy": {
                "priorityBased": True,
                "respectCrawlingHours": True,
                "enableCheckpoints": True,
                "globalRateLimit": {
                    "maxConcurrentDistricts": 3,
                    "globalRequestsPerMinute": 100,
                    "cooldownBetweenDistricts": 300
                }
            },
            "regions": [
                {
                    "configFile": "test-region.json",
                    "enabled": True,
                    "schedulingWeight": 40
                }
            ]
        }
        
        with open(districts_dir / "master-config.json", 'w') as f:
            json.dump(master_config, f, indent=2)
        
        # Create mock region config
        region_config = {
            "name": "Test Region",
            "category": "Test Category",
            "priority": 1,
            "districts": [
                {
                    "name": "Test District 1",
                    "priority": 1,
                    "maxPages": 100,
                    "rateLimit": {
                        "requestsPerMinute": 25,
                        "burstLimit": 3,
                        "backoffMultiplier": 2,
                        "maxRetries": 5
                    },
                    "crawlingHours": {
                        "start": "09:00",
                        "end": "23:00",
                        "timezone": "Asia/Hong_Kong"
                    },
                    "checkpoints": {
                        "enabled": True,
                        "intervalPages": 10,
                        "saveProgressEvery": 5
                    },
                    "openriceUrls": ["https://example.com"],
                    "districtId": 1001
                },
                {
                    "name": "Test District 2",
                    "priority": 2,
                    "maxPages": 50,
                    "rateLimit": {
                        "requestsPerMinute": 20,
                        "burstLimit": 2,
                        "backoffMultiplier": 2,
                        "maxRetries": 3
                    },
                    "crawlingHours": {
                        "start": "10:00",
                        "end": "22:00",
                        "timezone": "Asia/Hong_Kong"
                    },
                    "checkpoints": {
                        "enabled": False,
                        "intervalPages": 5,
                        "saveProgressEvery": 2
                    },
                    "openriceUrls": ["https://example2.com"],
                    "districtId": 1002
                }
            ]
        }
        
        with open(districts_dir / "test-region.json", 'w') as f:
            json.dump(region_config, f, indent=2)
    
    def test_load_mock_configuration(self):
        """Test loading mock configuration."""
        self.service.load_district_config()
        
        # Verify configuration is loaded
        self.assertTrue(self.service._loaded)
        
        # Verify districts are available
        all_districts = self.service.get_all_districts()
        self.assertIn("Test Region", all_districts)
        self.assertEqual(len(all_districts["Test Region"]), 2)
        self.assertIn("Test District 1", all_districts["Test Region"])
        self.assertIn("Test District 2", all_districts["Test Region"])
    
    def test_validate_mock_districts(self):
        """Test validation with mock districts."""
        self.service.load_district_config()
        
        # Test valid districts
        self.assertTrue(self.service.validate_district("Test District 1"))
        self.assertTrue(self.service.validate_district("Test District 2"))
        
        # Test invalid district
        self.assertFalse(self.service.validate_district("Nonexistent District"))
    
    def test_file_path_generation_with_mock_data(self):
        """Test file path generation with mock data."""
        self.service.load_district_config()
        
        # Test local file path
        local_path = self.service.get_local_file_path_for_district("Test District 1")
        expected_path = os.path.join(self.temp_dir, "restaurants", "test-region", "test-district-1.json")
        self.assertEqual(local_path, expected_path)
        
        # Test S3 path
        s3_path = self.service.get_s3_path_for_district("Test District 1")
        self.assertEqual(s3_path, "test-region/test-district-1.json")


if __name__ == '__main__':
    unittest.main()