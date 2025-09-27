"""
Data access client for restaurant data stored in AWS S3.

This module provides the DataAccessClient class for retrieving restaurant data
from S3 bucket restaurant-data-209803798463-us-east-1/restaurants/ while
loading district configuration from local files.
"""

import json
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path

import boto3
from botocore.exceptions import ClientError, NoCredentialsError, BotoCoreError

from models.restaurant_models import RestaurantDataFile, Restaurant, FileMetadata


logger = logging.getLogger(__name__)


class DataAccessClient:
    """Client for accessing restaurant data from S3 and district config locally."""
    
    def __init__(self, s3_bucket: str = "restaurant-data-209803798463-us-east-1"):
        """
        Initialize the data access client.
        
        Args:
            s3_bucket: S3 bucket name containing restaurant data
        """
        self.s3_bucket = s3_bucket
        self.s3_prefix = "restaurants"
        self._s3_client = None
        self._district_config = None
        
    @property
    def s3_client(self):
        """Lazy initialization of S3 client."""
        if self._s3_client is None:
            try:
                self._s3_client = boto3.client('s3')
                logger.info("S3 client initialized successfully")
            except NoCredentialsError as e:
                logger.error(f"AWS credentials not found: {e}")
                raise
            except Exception as e:
                logger.error(f"Failed to initialize S3 client: {e}")
                raise
        return self._s3_client
    
    def get_restaurant_data(self, region: str, district: str) -> Optional[RestaurantDataFile]:
        """
        Retrieve restaurant data from S3 for a specific region and district.
        
        Args:
            region: Region name (e.g., 'hong-kong-island')
            district: District name (e.g., 'admiralty')
            
        Returns:
            RestaurantDataFile object or None if not found
            
        Raises:
            ClientError: If S3 access fails
            ValueError: If JSON data is malformed
        """
        s3_key = f"{self.s3_prefix}/{region}/{district}.json"
        
        try:
            logger.info(f"Retrieving restaurant data from s3://{self.s3_bucket}/{s3_key}")
            
            response = self.s3_client.get_object(Bucket=self.s3_bucket, Key=s3_key)
            content = response['Body'].read().decode('utf-8')
            
            # Parse JSON data
            data = json.loads(content)
            
            # Validate required structure
            if 'metadata' not in data or 'restaurants' not in data:
                raise ValueError(f"Invalid restaurant data structure in {s3_key}")
            
            # Convert to data model
            restaurant_data = self._parse_restaurant_data(data)
            
            logger.info(f"Successfully retrieved {len(restaurant_data.restaurants)} restaurants from {district}")
            return restaurant_data
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'NoSuchKey':
                logger.warning(f"Restaurant data not found: s3://{self.s3_bucket}/{s3_key}")
                return None
            elif error_code == 'NoSuchBucket':
                logger.error(f"S3 bucket not found: {self.s3_bucket}")
                raise
            elif error_code == 'AccessDenied':
                logger.error(f"Access denied to S3 bucket: {self.s3_bucket}")
                raise
            else:
                logger.error(f"S3 client error: {e}")
                raise
                
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in restaurant data file {s3_key}: {e}")
            raise ValueError(f"Malformed JSON data in {s3_key}: {e}")
            
        except Exception as e:
            logger.error(f"Unexpected error retrieving restaurant data: {e}")
            raise
    
    def get_multiple_restaurant_data(self, region_district_pairs: List[tuple]) -> Dict[str, RestaurantDataFile]:
        """
        Retrieve restaurant data for multiple region/district pairs.
        
        Args:
            region_district_pairs: List of (region, district) tuples
            
        Returns:
            Dictionary mapping district names to RestaurantDataFile objects
        """
        results = {}
        
        for region, district in region_district_pairs:
            try:
                data = self.get_restaurant_data(region, district)
                if data:
                    results[district] = data
                else:
                    logger.warning(f"No data found for {region}/{district}")
            except Exception as e:
                logger.error(f"Failed to retrieve data for {region}/{district}: {e}")
                # Continue with other districts rather than failing completely
                continue
                
        return results
    
    def _parse_restaurant_data(self, data: Dict[str, Any]) -> RestaurantDataFile:
        """
        Parse raw JSON data into RestaurantDataFile model.
        
        Args:
            data: Raw JSON data from S3
            
        Returns:
            RestaurantDataFile object
            
        Raises:
            ValueError: If required fields are missing
        """
        try:
            # Parse file metadata
            metadata_dict = data['metadata']
            file_metadata = FileMetadata(
                timestamp=metadata_dict.get('timestamp', ''),
                version=metadata_dict.get('version', ''),
                district=metadata_dict.get('district', ''),
                location_category=metadata_dict.get('locationCategory', ''),
                record_count=metadata_dict.get('recordCount', 0),
                file_size=metadata_dict.get('fileSize', 0),
                sanitized_at=metadata_dict.get('sanitizedAt', ''),
                sanitization_version=metadata_dict.get('sanitizationVersion', '')
            )
            
            # Parse restaurants
            restaurants = []
            for restaurant_dict in data['restaurants']:
                restaurant = Restaurant.from_dict(restaurant_dict)
                restaurants.append(restaurant)
            
            return RestaurantDataFile(
                metadata=file_metadata,
                restaurants=restaurants
            )
            
        except KeyError as e:
            raise ValueError(f"Missing required field in restaurant data: {e}")
        except Exception as e:
            raise ValueError(f"Error parsing restaurant data: {e}")
    
    def load_district_config(self, config_path: str = "config/districts") -> Dict[str, Any]:
        """
        Load district configuration from local files.
        
        Args:
            config_path: Path to district configuration directory
            
        Returns:
            Dictionary containing district configuration
            
        Raises:
            FileNotFoundError: If config files are missing
            ValueError: If JSON is malformed
        """
        if self._district_config is not None:
            return self._district_config
            
        config_dir = Path(config_path)
        
        try:
            # Load master config
            master_config_path = config_dir / "master-config.json"
            if not master_config_path.exists():
                raise FileNotFoundError(f"Master config not found: {master_config_path}")
                
            with open(master_config_path, 'r', encoding='utf-8') as f:
                master_config = json.load(f)
            
            # Load regional configs
            regional_configs = {}
            region_files = [
                "hong-kong-island.json",
                "kowloon.json", 
                "new-territories.json",
                "islands.json"
            ]
            
            for region_file in region_files:
                region_path = config_dir / region_file
                if region_path.exists():
                    with open(region_path, 'r', encoding='utf-8') as f:
                        region_name = region_file.replace('.json', '')
                        regional_configs[region_name] = json.load(f)
                        logger.info(f"Loaded config for region: {region_name}")
                else:
                    logger.warning(f"Regional config not found: {region_path}")
            
            self._district_config = {
                'master': master_config,
                'regions': regional_configs
            }
            
            logger.info(f"Successfully loaded district configuration for {len(regional_configs)} regions")
            return self._district_config
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in district config: {e}")
            raise ValueError(f"Malformed JSON in district configuration: {e}")
        except Exception as e:
            logger.error(f"Error loading district configuration: {e}")
            raise
    
    def test_s3_connection(self) -> bool:
        """
        Test S3 connection and bucket access.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Test bucket access by listing objects with limit
            response = self.s3_client.list_objects_v2(
                Bucket=self.s3_bucket,
                Prefix=self.s3_prefix,
                MaxKeys=1
            )
            
            logger.info(f"S3 connection test successful for bucket: {self.s3_bucket}")
            return True
            
        except ClientError as e:
            logger.error(f"S3 connection test failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error testing S3 connection: {e}")
            return False
    
    def get_available_districts_from_s3(self) -> Dict[str, List[str]]:
        """
        Get available districts by listing S3 objects.
        
        Returns:
            Dictionary mapping regions to lists of available districts
        """
        try:
            districts_by_region = {}
            
            # List all objects in the restaurants prefix
            paginator = self.s3_client.get_paginator('list_objects_v2')
            pages = paginator.paginate(Bucket=self.s3_bucket, Prefix=f"{self.s3_prefix}/")
            
            for page in pages:
                if 'Contents' in page:
                    for obj in page['Contents']:
                        key = obj['Key']
                        # Parse key format: restaurants/region/district.json
                        if key.endswith('.json'):
                            parts = key.split('/')
                            if len(parts) >= 3:
                                region = parts[1]
                                district = parts[2].replace('.json', '')
                                
                                if region not in districts_by_region:
                                    districts_by_region[region] = []
                                districts_by_region[region].append(district)
            
            logger.info(f"Found districts in S3: {districts_by_region}")
            return districts_by_region
            
        except Exception as e:
            logger.error(f"Error listing districts from S3: {e}")
            return {}