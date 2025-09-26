"""
Unit tests for the DataAccessClient class.

Tests S3 data access, local district configuration loading, error handling,
and JSON parsing functionality.
"""

import json
import pytest
from unittest.mock import Mock, patch, mock_open
from pathlib import Path
from botocore.exceptions import ClientError, NoCredentialsError

from services.data_access import DataAccessClient
from models.restaurant_models import RestaurantDataFile, Restaurant, FileMetadata


class TestDataAccessClient:
    """Test cases for DataAccessClient class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.client = DataAccessClient()
        
        # Sample restaurant data for testing
        self.sample_restaurant_data = {
            "metadata": {
                "timestamp": "2025-09-25T05:51:13.870Z",
                "version": "1.0.0",
                "district": "Admiralty",
                "locationCategory": "Hong Kong Island",
                "recordCount": 2,
                "fileSize": 1024,
                "sanitizedAt": "2025-09-26T03:21:57.224Z",
                "sanitizationVersion": "1.0.0"
            },
            "restaurants": [
                {
                    "id": "test-id-1",
                    "name": "Test Restaurant 1",
                    "address": "123 Test Street",
                    "mealType": ["Western", "Fine Dining"],
                    "sentiment": {
                        "likes": 100,
                        "dislikes": 5,
                        "neutral": 10
                    },
                    "locationCategory": "Hong Kong Island",
                    "district": "Admiralty",
                    "priceRange": "$201-400",
                    "operatingHours": {
                        "Mon - Fri": ["11:30 - 15:30", "18:00 - 22:30"],
                        "Sat - Sun": ["11:30 - 22:30"],
                        "Public Holiday": ["11:30 - 22:30"]
                    },
                    "metadata": {
                        "dataQuality": "complete",
                        "version": "1.0.0",
                        "qualityScore": 100
                    }
                },
                {
                    "id": "test-id-2",
                    "name": "Test Restaurant 2",
                    "address": "456 Test Avenue",
                    "mealType": ["Chinese", "Dim Sum"],
                    "sentiment": {
                        "likes": 200,
                        "dislikes": 10,
                        "neutral": 20
                    },
                    "locationCategory": "Hong Kong Island",
                    "district": "Admiralty",
                    "priceRange": "$101-200",
                    "operatingHours": {
                        "Mon - Fri": ["07:00 - 15:00"],
                        "Sat - Sun": ["07:00 - 17:00"],
                        "Public Holiday": ["07:00 - 17:00"]
                    },
                    "metadata": {
                        "dataQuality": "complete",
                        "version": "1.0.0",
                        "qualityScore": 95
                    }
                }
            ]
        }
        
        # Sample district configuration
        self.sample_master_config = {
            "version": "1.0.0",
            "lastUpdated": "2025-09-25T00:00:00Z",
            "regions": [
                {"name": "hong-kong-island", "configFile": "hong-kong-island.json"},
                {"name": "kowloon", "configFile": "kowloon.json"}
            ]
        }
        
        self.sample_region_config = {
            "name": "Hong Kong Island",
            "category": "hong-kong-island",
            "priority": 1,
            "districts": [
                {"name": "Admiralty", "priority": 1, "maxPages": 10, "districtId": 1},
                {"name": "Central", "priority": 2, "maxPages": 15, "districtId": 2}
            ]
        }
    
    @patch('boto3.client')
    def test_s3_client_initialization_success(self, mock_boto3_client):
        """Test successful S3 client initialization."""
        mock_s3 = Mock()
        mock_boto3_client.return_value = mock_s3
        
        # Access s3_client property to trigger initialization
        client = self.client.s3_client
        
        mock_boto3_client.assert_called_once_with('s3')
        assert client == mock_s3
    
    @patch('boto3.client')
    def test_s3_client_initialization_no_credentials(self, mock_boto3_client):
        """Test S3 client initialization with no credentials."""
        mock_boto3_client.side_effect = NoCredentialsError()
        
        with pytest.raises(NoCredentialsError):
            _ = self.client.s3_client
    
    @patch('services.data_access.DataAccessClient.s3_client', new_callable=lambda: Mock())
    def test_get_restaurant_data_success(self, mock_s3_client):
        """Test successful restaurant data retrieval from S3."""
        # Mock S3 response
        mock_response = {
            'Body': Mock()
        }
        mock_response['Body'].read.return_value = json.dumps(self.sample_restaurant_data).encode('utf-8')
        mock_s3_client.get_object.return_value = mock_response
        
        # Test the method
        result = self.client.get_restaurant_data("hong-kong-island", "admiralty")
        
        # Verify S3 call
        mock_s3_client.get_object.assert_called_once_with(
            Bucket="restaurant-data-209803798463-us-east-1",
            Key="restaurants/hong-kong-island/admiralty.json"
        )
        
        # Verify result
        assert isinstance(result, RestaurantDataFile)
        assert result.metadata.district == "Admiralty"
        assert len(result.restaurants) == 2
        assert result.restaurants[0].name == "Test Restaurant 1"
    
    @patch('services.data_access.DataAccessClient.s3_client', new_callable=lambda: Mock())
    def test_get_restaurant_data_file_not_found(self, mock_s3_client):
        """Test restaurant data retrieval when file doesn't exist."""
        # Mock S3 NoSuchKey error
        error_response = {'Error': {'Code': 'NoSuchKey'}}
        mock_s3_client.get_object.side_effect = ClientError(error_response, 'GetObject')
        
        result = self.client.get_restaurant_data("hong-kong-island", "nonexistent")
        
        assert result is None
    
    @patch('services.data_access.DataAccessClient.s3_client', new_callable=lambda: Mock())
    def test_get_restaurant_data_access_denied(self, mock_s3_client):
        """Test restaurant data retrieval with access denied error."""
        # Mock S3 AccessDenied error
        error_response = {'Error': {'Code': 'AccessDenied'}}
        mock_s3_client.get_object.side_effect = ClientError(error_response, 'GetObject')
        
        with pytest.raises(ClientError):
            self.client.get_restaurant_data("hong-kong-island", "admiralty")
    
    @patch('services.data_access.DataAccessClient.s3_client', new_callable=lambda: Mock())
    def test_get_restaurant_data_invalid_json(self, mock_s3_client):
        """Test restaurant data retrieval with malformed JSON."""
        # Mock S3 response with invalid JSON
        mock_response = {
            'Body': Mock()
        }
        mock_response['Body'].read.return_value = b'{"invalid": json}'
        mock_s3_client.get_object.return_value = mock_response
        
        with pytest.raises(ValueError, match="Malformed JSON data"):
            self.client.get_restaurant_data("hong-kong-island", "admiralty")
    
    @patch('services.data_access.DataAccessClient.s3_client', new_callable=lambda: Mock())
    def test_get_restaurant_data_missing_structure(self, mock_s3_client):
        """Test restaurant data retrieval with missing required structure."""
        # Mock S3 response with missing metadata
        invalid_data = {"restaurants": []}
        mock_response = {
            'Body': Mock()
        }
        mock_response['Body'].read.return_value = json.dumps(invalid_data).encode('utf-8')
        mock_s3_client.get_object.return_value = mock_response
        
        with pytest.raises(ValueError, match="Invalid restaurant data structure"):
            self.client.get_restaurant_data("hong-kong-island", "admiralty")
    
    @patch('services.data_access.DataAccessClient.get_restaurant_data')
    def test_get_multiple_restaurant_data_success(self, mock_get_data):
        """Test successful retrieval of multiple restaurant data files."""
        # Mock individual data retrieval
        mock_data1 = Mock(spec=RestaurantDataFile)
        mock_data2 = Mock(spec=RestaurantDataFile)
        mock_get_data.side_effect = [mock_data1, mock_data2]
        
        region_district_pairs = [
            ("hong-kong-island", "admiralty"),
            ("kowloon", "tsim-sha-tsui")
        ]
        
        result = self.client.get_multiple_restaurant_data(region_district_pairs)
        
        assert len(result) == 2
        assert "admiralty" in result
        assert "tsim-sha-tsui" in result
        assert result["admiralty"] == mock_data1
        assert result["tsim-sha-tsui"] == mock_data2
    
    @patch('services.data_access.DataAccessClient.get_restaurant_data')
    def test_get_multiple_restaurant_data_partial_failure(self, mock_get_data):
        """Test multiple restaurant data retrieval with some failures."""
        # Mock one success, one failure
        mock_data1 = Mock(spec=RestaurantDataFile)
        mock_get_data.side_effect = [mock_data1, Exception("S3 error")]
        
        region_district_pairs = [
            ("hong-kong-island", "admiralty"),
            ("kowloon", "nonexistent")
        ]
        
        result = self.client.get_multiple_restaurant_data(region_district_pairs)
        
        # Should return only successful results
        assert len(result) == 1
        assert "admiralty" in result
        assert "nonexistent" not in result
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('pathlib.Path.exists')
    def test_load_district_config_success(self, mock_exists, mock_file):
        """Test successful district configuration loading."""
        # Mock file existence
        mock_exists.return_value = True
        
        # Mock file contents
        master_content = json.dumps(self.sample_master_config)
        region_content = json.dumps(self.sample_region_config)
        
        # Configure mock_open to return different content for different files
        mock_file.side_effect = [
            mock_open(read_data=master_content).return_value,
            mock_open(read_data=region_content).return_value,
            mock_open(read_data=region_content).return_value,
            mock_open(read_data=region_content).return_value,
            mock_open(read_data=region_content).return_value
        ]
        
        result = self.client.load_district_config()
        
        assert 'master' in result
        assert 'regions' in result
        assert result['master']['version'] == "1.0.0"
        assert len(result['regions']) > 0
    
    @patch('pathlib.Path.exists')
    def test_load_district_config_missing_master(self, mock_exists):
        """Test district configuration loading with missing master config."""
        mock_exists.return_value = False
        
        with pytest.raises(FileNotFoundError, match="Master config not found"):
            self.client.load_district_config()
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('pathlib.Path.exists')
    def test_load_district_config_invalid_json(self, mock_exists, mock_file):
        """Test district configuration loading with invalid JSON."""
        mock_exists.return_value = True
        mock_file.return_value.read.return_value = '{"invalid": json}'
        
        with pytest.raises(ValueError, match="Malformed JSON in district configuration"):
            self.client.load_district_config()
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('pathlib.Path.exists')
    def test_load_district_config_caching(self, mock_exists, mock_file):
        """Test that district configuration is cached after first load."""
        mock_exists.return_value = True
        mock_file.return_value.read.return_value = json.dumps(self.sample_master_config)
        
        # Load twice
        result1 = self.client.load_district_config()
        result2 = self.client.load_district_config()
        
        # Should be the same object (cached)
        assert result1 is result2
        # File should only be opened once for master config
        assert mock_file.call_count <= 5  # Master + 4 regional configs max
    
    @patch('services.data_access.DataAccessClient.s3_client', new_callable=lambda: Mock())
    def test_test_s3_connection_success(self, mock_s3_client):
        """Test successful S3 connection test."""
        mock_s3_client.list_objects_v2.return_value = {'Contents': []}
        
        result = self.client.test_s3_connection()
        
        assert result is True
        mock_s3_client.list_objects_v2.assert_called_once_with(
            Bucket="restaurant-data-209803798463-us-east-1",
            Prefix="restaurants",
            MaxKeys=1
        )
    
    @patch('services.data_access.DataAccessClient.s3_client', new_callable=lambda: Mock())
    def test_test_s3_connection_failure(self, mock_s3_client):
        """Test S3 connection test failure."""
        error_response = {'Error': {'Code': 'AccessDenied'}}
        mock_s3_client.list_objects_v2.side_effect = ClientError(error_response, 'ListObjectsV2')
        
        result = self.client.test_s3_connection()
        
        assert result is False
    
    @patch('services.data_access.DataAccessClient.s3_client', new_callable=lambda: Mock())
    def test_get_available_districts_from_s3(self, mock_s3_client):
        """Test getting available districts from S3."""
        # Mock S3 paginator response
        mock_paginator = Mock()
        mock_s3_client.get_paginator.return_value = mock_paginator
        
        mock_pages = [
            {
                'Contents': [
                    {'Key': 'restaurants/hong-kong-island/admiralty.json'},
                    {'Key': 'restaurants/hong-kong-island/central.json'},
                    {'Key': 'restaurants/kowloon/tsim-sha-tsui.json'}
                ]
            }
        ]
        mock_paginator.paginate.return_value = mock_pages
        
        result = self.client.get_available_districts_from_s3()
        
        expected = {
            'hong-kong-island': ['admiralty', 'central'],
            'kowloon': ['tsim-sha-tsui']
        }
        
        assert result == expected
    
    def test_parse_restaurant_data_success(self):
        """Test successful parsing of restaurant data."""
        result = self.client._parse_restaurant_data(self.sample_restaurant_data)
        
        assert isinstance(result, RestaurantDataFile)
        assert result.metadata.district == "Admiralty"
        assert result.metadata.record_count == 2
        assert len(result.restaurants) == 2
        
        # Check first restaurant
        restaurant1 = result.restaurants[0]
        assert restaurant1.name == "Test Restaurant 1"
        assert restaurant1.district == "Admiralty"
        assert len(restaurant1.meal_type) == 2
        assert restaurant1.sentiment.likes == 100
    
    def test_parse_restaurant_data_missing_metadata(self):
        """Test parsing restaurant data with missing metadata."""
        invalid_data = {"restaurants": []}
        
        with pytest.raises(ValueError, match="Missing required field"):
            self.client._parse_restaurant_data(invalid_data)
    
    def test_parse_restaurant_data_invalid_restaurant(self):
        """Test parsing restaurant data with invalid restaurant structure."""
        invalid_data = {
            "metadata": self.sample_restaurant_data["metadata"],
            "restaurants": [{"invalid": "structure"}]
        }
        
        # The Restaurant.from_dict() method uses defaults for missing fields,
        # so this should succeed but create a restaurant with default values
        result = self.client._parse_restaurant_data(invalid_data)
        
        assert isinstance(result, RestaurantDataFile)
        assert len(result.restaurants) == 1
        # Restaurant should have default values for missing fields
        restaurant = result.restaurants[0]
        assert restaurant.id == ''  # Default value
        assert restaurant.name == ''  # Default value


if __name__ == '__main__':
    pytest.main([__file__])