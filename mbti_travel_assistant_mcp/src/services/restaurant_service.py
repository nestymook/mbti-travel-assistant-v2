"""Restaurant service for business logic and search operations.

This module provides the RestaurantService class that implements core restaurant
search functionality by district and meal type. It integrates with the district
service, time service, and data access client to provide comprehensive search
capabilities for the MCP server.
"""

import logging
from typing import List, Dict, Optional, Tuple, Any

from src.models.restaurant_models import Restaurant, RestaurantDataFile
from src.services.district_service import DistrictService, DistrictConfigurationError
from src.services.time_service import TimeService
from src.services.data_access import DataAccessClient


logger = logging.getLogger(__name__)


class RestaurantSearchError(Exception):
    """Exception raised for restaurant search errors."""
    pass


class RestaurantService:
    """Service for restaurant search operations.
    
    Provides methods for searching restaurants by district, meal type, and
    combined criteria. Integrates with district configuration, time analysis,
    and S3 data access.
    """
    
    def __init__(self, config_base_path: str = "config"):
        """Initialize the restaurant service.
        
        Args:
            config_base_path: Base path to configuration directory
        """
        self.district_service = DistrictService(config_base_path)
        self.time_service = TimeService()
        self.data_access_client = DataAccessClient()
        self._initialized = False
    
    def _ensure_initialized(self) -> None:
        """Ensure services are initialized before operations.
        
        Raises:
            RestaurantSearchError: If initialization fails
        """
        if not self._initialized:
            try:
                self.district_service.load_district_config()
                self._initialized = True
                logger.info("Restaurant service initialized successfully")
            except DistrictConfigurationError as e:
                raise RestaurantSearchError(f"Failed to initialize district service: {e}")
    
    def search_by_districts(self, districts: List[str]) -> List[Restaurant]:
        """Search for restaurants in specific districts.
        
        Args:
            districts: List of district names to search
            
        Returns:
            List of Restaurant objects from all specified districts
            
        Raises:
            RestaurantSearchError: If search fails or districts are invalid
        """
        self._ensure_initialized()
        
        if not districts:
            raise RestaurantSearchError("Districts list cannot be empty")
        
        # Validate districts
        valid_districts, invalid_districts = self.district_service.validate_districts(districts)
        
        if invalid_districts:
            available_districts = self.district_service.get_all_district_names()
            raise RestaurantSearchError(
                f"Invalid districts: {invalid_districts}. "
                f"Available districts: {available_districts}"
            )
        
        logger.info(f"Searching restaurants in districts: {valid_districts}")
        
        # Get region-district pairs for data retrieval
        region_district_pairs = []
        for district in valid_districts:
            region = self.district_service.get_region_for_district(district)
            if region:
                # Convert to S3 key format (lowercase with hyphens)
                region_key = region.lower().replace(' ', '-')
                
                district_key = district.lower().replace(' ', '-')
                region_district_pairs.append((region_key, district_key))
            else:
                logger.warning(f"No region found for district: {district}")
        
        if not region_district_pairs:
            logger.warning("No valid region-district pairs found")
            return []
        
        # Retrieve restaurant data from S3
        try:
            restaurant_data_files = self.data_access_client.get_multiple_restaurant_data(
                region_district_pairs
            )
            
            # Combine all restaurants from all districts
            all_restaurants = []
            for district_key, data_file in restaurant_data_files.items():
                all_restaurants.extend(data_file.restaurants)
                logger.info(f"Retrieved {len(data_file.restaurants)} restaurants from {district_key}")
            
            logger.info(f"Total restaurants found: {len(all_restaurants)}")
            return all_restaurants
            
        except Exception as e:
            logger.error(f"Error retrieving restaurant data: {e}")
            raise RestaurantSearchError(f"Failed to retrieve restaurant data: {e}")
    
    def search_by_meal_types(self, meal_types: List[str]) -> List[Restaurant]:
        """Search for restaurants by meal type based on operating hours.
        
        Args:
            meal_types: List of meal types ("breakfast", "lunch", "dinner")
            
        Returns:
            List of Restaurant objects that serve the specified meal types
            
        Raises:
            RestaurantSearchError: If search fails or meal types are invalid
        """
        self._ensure_initialized()
        
        if not meal_types:
            raise RestaurantSearchError("Meal types list cannot be empty")
        
        # Validate meal types
        valid_meal_types = []
        invalid_meal_types = []
        
        for meal_type in meal_types:
            if self.time_service.validate_meal_type(meal_type):
                valid_meal_types.append(meal_type.lower())
            else:
                invalid_meal_types.append(meal_type)
        
        if invalid_meal_types:
            raise RestaurantSearchError(
                f"Invalid meal types: {invalid_meal_types}. "
                f"Valid meal types: {list(self.time_service.VALID_MEAL_TYPES)}"
            )
        
        logger.info(f"Searching restaurants for meal types: {valid_meal_types}")
        
        # Get all districts to search across all available data
        all_districts = self.district_service.get_all_district_names()
        
        # Get all restaurant data
        try:
            all_restaurants = self.search_by_districts(all_districts)
            
            # Filter restaurants by meal type
            matching_restaurants = []
            for restaurant in all_restaurants:
                # Check if restaurant serves any of the requested meal types
                serves_meal = False
                for meal_type in valid_meal_types:
                    if self.time_service.is_open_for_meal(restaurant.operating_hours, meal_type):
                        serves_meal = True
                        break
                
                if serves_meal:
                    matching_restaurants.append(restaurant)
            
            logger.info(f"Found {len(matching_restaurants)} restaurants serving meal types: {valid_meal_types}")
            return matching_restaurants
            
        except Exception as e:
            logger.error(f"Error searching by meal types: {e}")
            raise RestaurantSearchError(f"Failed to search by meal types: {e}")
    
    def search_combined(self, districts: Optional[List[str]] = None, 
                       meal_types: Optional[List[str]] = None) -> List[Restaurant]:
        """Search for restaurants by both district and meal type criteria.
        
        Args:
            districts: Optional list of district names to search
            meal_types: Optional list of meal types to filter by
            
        Returns:
            List of Restaurant objects matching both criteria
            
        Raises:
            RestaurantSearchError: If search fails or parameters are invalid
        """
        self._ensure_initialized()
        
        if not districts and not meal_types:
            raise RestaurantSearchError("At least one of districts or meal_types must be provided")
        
        logger.info(f"Combined search - districts: {districts}, meal_types: {meal_types}")
        
        # Start with district-based search if districts are specified
        if districts:
            restaurants = self.search_by_districts(districts)
        else:
            # If no districts specified, get all restaurants
            all_districts = self.district_service.get_all_district_names()
            restaurants = self.search_by_districts(all_districts)
        
        # Filter by meal types if specified
        if meal_types:
            # Validate meal types
            valid_meal_types = []
            invalid_meal_types = []
            
            for meal_type in meal_types:
                if self.time_service.validate_meal_type(meal_type):
                    valid_meal_types.append(meal_type.lower())
                else:
                    invalid_meal_types.append(meal_type)
            
            if invalid_meal_types:
                raise RestaurantSearchError(
                    f"Invalid meal types: {invalid_meal_types}. "
                    f"Valid meal types: {list(self.time_service.VALID_MEAL_TYPES)}"
                )
            
            # Filter restaurants by meal type
            filtered_restaurants = []
            for restaurant in restaurants:
                # Check if restaurant serves any of the requested meal types
                serves_meal = False
                for meal_type in valid_meal_types:
                    if self.time_service.is_open_for_meal(restaurant.operating_hours, meal_type):
                        serves_meal = True
                        break
                
                if serves_meal:
                    filtered_restaurants.append(restaurant)
            
            restaurants = filtered_restaurants
        
        logger.info(f"Combined search found {len(restaurants)} restaurants")
        return restaurants
    
    def get_available_districts(self) -> Dict[str, List[str]]:
        """Get all available districts organized by region.
        
        Returns:
            Dictionary mapping region names to lists of district names
            
        Raises:
            RestaurantSearchError: If district configuration is not available
        """
        self._ensure_initialized()
        
        try:
            return self.district_service.get_all_districts()
        except DistrictConfigurationError as e:
            raise RestaurantSearchError(f"Failed to get available districts: {e}")
    
    def get_restaurant_count_by_district(self, districts: List[str]) -> Dict[str, int]:
        """Get count of restaurants in each district.
        
        Args:
            districts: List of district names
            
        Returns:
            Dictionary mapping district names to restaurant counts
            
        Raises:
            RestaurantSearchError: If search fails
        """
        self._ensure_initialized()
        
        try:
            # Validate districts first
            valid_districts, invalid_districts = self.district_service.validate_districts(districts)
            
            if invalid_districts:
                raise RestaurantSearchError(f"Invalid districts: {invalid_districts}")
            
            # Get region-district pairs
            region_district_pairs = []
            for district in valid_districts:
                region = self.district_service.get_region_for_district(district)
                if region:
                    region_key = region.lower().replace(' ', '-')
                    
                    district_key = district.lower().replace(' ', '-')
                    region_district_pairs.append((region_key, district_key))
            
            # Get restaurant data
            restaurant_data_files = self.data_access_client.get_multiple_restaurant_data(
                region_district_pairs
            )
            
            # Count restaurants by district
            counts = {}
            for district in valid_districts:
                district_key = district.lower().replace(' ', '-')
                if district_key in restaurant_data_files:
                    counts[district] = len(restaurant_data_files[district_key].restaurants)
                else:
                    counts[district] = 0
            
            return counts
            
        except Exception as e:
            logger.error(f"Error getting restaurant counts: {e}")
            raise RestaurantSearchError(f"Failed to get restaurant counts: {e}")
    
    def get_meal_type_analysis(self, restaurants: List[Restaurant]) -> Dict[str, Any]:
        """Analyze meal type coverage across restaurants.
        
        Args:
            restaurants: List of restaurants to analyze
            
        Returns:
            Dictionary containing meal type analysis
        """
        if not restaurants:
            return {
                'total_restaurants': 0,
                'meal_type_counts': {'breakfast': 0, 'lunch': 0, 'dinner': 0},
                'restaurants_by_meal_type': {'breakfast': [], 'lunch': [], 'dinner': []}
            }
        
        meal_type_counts = {'breakfast': 0, 'lunch': 0, 'dinner': 0}
        restaurants_by_meal_type = {'breakfast': [], 'lunch': [], 'dinner': []}
        
        for restaurant in restaurants:
            for meal_type in self.time_service.VALID_MEAL_TYPES:
                if self.time_service.is_open_for_meal(restaurant.operating_hours, meal_type):
                    meal_type_counts[meal_type] += 1
                    restaurants_by_meal_type[meal_type].append(restaurant.name)
        
        return {
            'total_restaurants': len(restaurants),
            'meal_type_counts': meal_type_counts,
            'restaurants_by_meal_type': restaurants_by_meal_type
        }
    
    def test_services(self) -> Dict[str, bool]:
        """Test all underlying services for connectivity and configuration.
        
        Returns:
            Dictionary with test results for each service
        """
        results = {}
        
        # Test district service
        try:
            self._ensure_initialized()
            districts = self.district_service.get_all_district_names()
            results['district_service'] = len(districts) > 0
        except Exception as e:
            logger.error(f"District service test failed: {e}")
            results['district_service'] = False
        
        # Test S3 connection
        try:
            results['s3_connection'] = self.data_access_client.test_s3_connection()
        except Exception as e:
            logger.error(f"S3 connection test failed: {e}")
            results['s3_connection'] = False
        
        # Test time service
        try:
            # Test basic time service functionality
            test_result = self.time_service.validate_meal_type('breakfast')
            results['time_service'] = test_result
        except Exception as e:
            logger.error(f"Time service test failed: {e}")
            results['time_service'] = False
        
        return results