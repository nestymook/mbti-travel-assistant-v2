"""
Comprehensive Validation and Load Testing

This module provides comprehensive validation tests for session assignment logic validation,
load testing for concurrent MBTI requests, and regression testing for itinerary generation accuracy.
"""

import pytest
import asyncio
import time
import statistics
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed, ProcessPoolExecutor
from unittest.mock import Mock, patch, AsyncMock
from typing import List, Dict, Any, Tuple
import json
import random
import uuid
from datetime import datetime, timedelta

from ..services.assignment_validator import AssignmentValidator, ValidationSeverity, ValidationCategory
from ..services.session_assignment_logic import SessionAssignmentLogic
from ..services.itinerary_generator import ItineraryGenerator
from ..models.tourist_spot_models import TouristSpot, TouristSpotOperatingHours, SessionType
from ..models.restaurant_models import Restaurant
from ..models.itinerary_models import MainItinerary, DayItinerary, SessionAssignment, MealAssignment


class TestSessionAssignmentValidation:
    """Comprehensive tests for session assignment logic validation."""

    def setup_method(self):
        """Set up validation test fixtures."""
        self.validator = AssignmentValidator()
        self.session_logic = SessionAssignmentLogic()
        self.validation_scenarios = self._create_validation_scenarios()

    def _create_validation_scenarios(self) -> List[Dict[str, Any]]:
        """Create comprehensive validation test scenarios."""
        scenarios = []
        
        # Scenario 1: Perfect valid itinerary
        scenarios.append({
            "name": "perfect_valid_itinerary",
            "description": "Itinerary with all valid assignments",
            "spots": self._create_valid_spots(),
            "restaurants": self._create_valid_restaurants(),
            "expected_errors": 0,
            "expected_warnings": 0
        })
        
        # Scenario 2: Operating hours violations
        scenarios.append({
            "name": "operating_hours_violations",
            "description": "Itinerary with operating hours violations",
            "spots": self._create_invalid_hours_spots(),
            "restaurants": self._create_valid_restaurants(),
            "expected_errors": 3,  # One per session type
            "expected_warnings": 0
        })
        
        # Scenario 3: District matching issues
        scenarios.append({
            "name": "district_matching_issues",
            "description": "Itinerary with district matching problems",
            "spots": self._create_district_mismatch_spots(),
            "restaurants": self._create_valid_restaurants(),
            "expected_errors": 0,
            "expected_warnings": 2  # Afternoon and night sessions
        })
        
        # Scenario 4: Uniqueness violations
        scenarios.append({
            "name": "uniqueness_violations",
            "description": "Itinerary with duplicate assignments",
            "spots": self._create_duplicate_spots(),
            "restaurants": self._create_duplicate_restaurants(),
            "expected_errors": 2,  # Spot and restaurant duplicates
            "expected_warnings": 0
        })
        
        # Scenario 5: Incomplete assignments
        scenarios.append({
            "name": "incomplete_assignments",
            "description": "Itinerary with missing assignments",
            "spots": [],  # No spots available
            "restaurants": [],  # No restaurants available
            "expected_errors": 9,  # 9 missing assignments (3 days × 3 sessions)
            "expected_warnings": 0
        })
        
        return scenarios

    def _create_valid_spots(self) -> List[TouristSpot]:
        """Create valid tourist spots for testing."""
        spots = []
        districts = ["Central", "Admiralty", "Wan Chai"]
        
        for i, district in enumerate(districts):
            for j in range(3):  # 3 spots per district
                operating_hours = TouristSpotOperatingHours(
                    monday="09:00-22:00", tuesday="09:00-22:00", wednesday="09:00-22:00",
                    thursday="09:00-22:00", friday="09:00-22:00", saturday="10:00-21:00", sunday="10:00-21:00"
                )
                
                spot = TouristSpot(
                    id=f"valid_spot_{i}_{j}",
                    name=f"Valid Spot {i}-{j}",
                    address=f"{100 + i + j} Valid Street, {district}, Hong Kong",
                    district=district,
                    area="Hong Kong Island",
                    location_category="Museum",
                    description=f"Valid spot {i}-{j} for testing",
                    operating_hours=operating_hours,
                    operating_days=["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"],
                    mbti_personality_types=["INFJ"],
                    keywords=["valid", "test"],
                    mbti_match=True
                )
                spots.append(spot)
        
        return spots

    def _create_invalid_hours_spots(self) -> List[TouristSpot]:
        """Create spots with invalid operating hours."""
        spots = []
        
        # Morning-only spot (invalid for afternoon/night)
        spots.append(TouristSpot(
            id="morning_only_spot",
            name="Morning Only Spot",
            address="Morning Street, Central, Hong Kong",
            district="Central",
            area="Hong Kong Island",
            location_category="Park",
            description="Morning only spot",
            operating_hours=TouristSpotOperatingHours(
                monday="07:00-11:00", tuesday="07:00-11:00"
            ),
            operating_days=["monday", "tuesday"],
            mbti_personality_types=["INFJ"],
            mbti_match=True
        ))
        
        # Afternoon-only spot (invalid for morning/night)
        spots.append(TouristSpot(
            id="afternoon_only_spot",
            name="Afternoon Only Spot",
            address="Afternoon Street, Central, Hong Kong",
            district="Central",
            area="Hong Kong Island",
            location_category="Gallery",
            description="Afternoon only spot",
            operating_hours=TouristSpotOperatingHours(
                monday="13:00-17:00", tuesday="13:00-17:00"
            ),
            operating_days=["monday", "tuesday"],
            mbti_personality_types=["INFJ"],
            mbti_match=True
        ))
        
        # Night-only spot (invalid for morning/afternoon)
        spots.append(TouristSpot(
            id="night_only_spot",
            name="Night Only Spot",
            address="Night Street, Central, Hong Kong",
            district="Central",
            area="Hong Kong Island",
            location_category="Market",
            description="Night only spot",
            operating_hours=TouristSpotOperatingHours(
                monday="19:00-23:00", tuesday="19:00-23:00"
            ),
            operating_days=["monday", "tuesday"],
            mbti_personality_types=["INFJ"],
            mbti_match=True
        ))
        
        return spots

    def _create_district_mismatch_spots(self) -> List[TouristSpot]:
        """Create spots with district mismatches."""
        spots = []
        
        # Morning spot in Central
        spots.append(TouristSpot(
            id="central_morning_spot",
            name="Central Morning Spot",
            address="Central Street, Central, Hong Kong",
            district="Central",
            area="Hong Kong Island",
            location_category="Museum",
            description="Central morning spot",
            operating_hours=TouristSpotOperatingHours(
                monday="09:00-22:00", tuesday="09:00-22:00"
            ),
            operating_days=["monday", "tuesday"],
            mbti_personality_types=["INFJ"],
            mbti_match=True
        ))
        
        # Afternoon spot in Tsim Sha Tsui (different district)
        spots.append(TouristSpot(
            id="tst_afternoon_spot",
            name="TST Afternoon Spot",
            address="TST Street, Tsim Sha Tsui, Kowloon",
            district="Tsim Sha Tsui",
            area="Kowloon",
            location_category="Gallery",
            description="TST afternoon spot",
            operating_hours=TouristSpotOperatingHours(
                monday="09:00-22:00", tuesday="09:00-22:00"
            ),
            operating_days=["monday", "tuesday"],
            mbti_personality_types=["INFJ"],
            mbti_match=True
        ))
        
        # Night spot in Mong Kok (different district and area)
        spots.append(TouristSpot(
            id="mk_night_spot",
            name="MK Night Spot",
            address="MK Street, Mong Kok, Kowloon",
            district="Mong Kok",
            area="Kowloon",
            location_category="Market",
            description="MK night spot",
            operating_hours=TouristSpotOperatingHours(
                monday="09:00-22:00", tuesday="09:00-22:00"
            ),
            operating_days=["monday", "tuesday"],
            mbti_personality_types=["INFJ"],
            mbti_match=True
        ))
        
        return spots

    def _create_duplicate_spots(self) -> List[TouristSpot]:
        """Create spots that will cause uniqueness violations."""
        # Return same spot multiple times to force duplicates
        spot = TouristSpot(
            id="duplicate_spot",
            name="Duplicate Spot",
            address="Duplicate Street, Central, Hong Kong",
            district="Central",
            area="Hong Kong Island",
            location_category="Museum",
            description="Duplicate spot for testing",
            operating_hours=TouristSpotOperatingHours(
                monday="09:00-22:00", tuesday="09:00-22:00"
            ),
            operating_days=["monday", "tuesday"],
            mbti_personality_types=["INFJ"],
            mbti_match=True
        )
        
        return [spot] * 3  # Same spot repeated

    def _create_valid_restaurants(self) -> List[Restaurant]:
        """Create valid restaurants for testing."""
        restaurants = []
        districts = ["Central", "Admiralty", "Wan Chai"]
        meal_configs = [
            ("breakfast", "07:00-11:00"),
            ("lunch", "11:30-15:00"),
            ("dinner", "18:00-22:00")
        ]
        
        for district in districts:
            for meal_type, hours in meal_configs:
                for i in range(3):  # 3 restaurants per meal per district
                    restaurant = Restaurant(
                        id=f"valid_{meal_type}_{district.lower()}_{i}",
                        name=f"Valid {district} {meal_type.title()} {i}",
                        address=f"{200 + i} Valid {meal_type.title()} Street, {district}, Hong Kong",
                        district=district,
                        operating_hours=hours,
                        cuisine_type="Test Cuisine",
                        rating=4.0 + (i * 0.1)
                    )
                    restaurants.append(restaurant)
        
        return restaurants

    def _create_duplicate_restaurants(self) -> List[Restaurant]:
        """Create restaurants that will cause uniqueness violations."""
        # Return same restaurant multiple times to force duplicates
        restaurant = Restaurant(
            id="duplicate_restaurant",
            name="Duplicate Restaurant",
            address="Duplicate Restaurant Street, Central, Hong Kong",
            district="Central",
            operating_hours="09:00-22:00",
            cuisine_type="Test Cuisine",
            rating=4.0
        )
        
        return [restaurant] * 3  # Same restaurant repeated

    def test_validation_scenario_perfect_valid_itinerary(self):
        """Test validation with perfect valid itinerary."""
        scenario = self.validation_scenarios[0]  # Perfect valid itinerary
        
        # Create itinerary with valid assignments
        itinerary = self._create_test_itinerary(scenario["spots"], scenario["restaurants"])
        
        # Validate
        report = self.validator.validate_complete_itinerary(itinerary)
        
        # Should have minimal issues
        assert report.error_count <= scenario["expected_errors"]
        assert report.warning_count <= scenario["expected_warnings"]
        
        if report.error_count == 0 and report.warning_count == 0:
            assert report.is_valid is True

    def test_validation_scenario_operating_hours_violations(self):
        """Test validation with operating hours violations."""
        scenario = self.validation_scenarios[1]  # Operating hours violations
        
        # Create itinerary with invalid hour assignments
        itinerary = self._create_invalid_hours_itinerary(scenario["spots"])
        
        # Validate
        report = self.validator.validate_complete_itinerary(itinerary)
        
        # Should detect operating hours errors
        operating_hours_errors = [
            issue for issue in report.issues
            if issue.category == ValidationCategory.OPERATING_HOURS
        ]
        
        assert len(operating_hours_errors) >= 1
        assert report.error_count >= 1

    def test_validation_scenario_district_matching_issues(self):
        """Test validation with district matching issues."""
        scenario = self.validation_scenarios[2]  # District matching issues
        
        # Create itinerary with district mismatches
        itinerary = self._create_district_mismatch_itinerary(scenario["spots"])
        
        # Validate
        report = self.validator.validate_complete_itinerary(itinerary)
        
        # Should detect district matching warnings
        district_warnings = [
            issue for issue in report.issues
            if issue.category == ValidationCategory.DISTRICT_MATCHING
        ]
        
        assert len(district_warnings) >= 1

    def test_validation_scenario_uniqueness_violations(self):
        """Test validation with uniqueness violations."""
        scenario = self.validation_scenarios[3]  # Uniqueness violations
        
        # Create itinerary with duplicate assignments
        itinerary = self._create_duplicate_itinerary(scenario["spots"], scenario["restaurants"])
        
        # Validate
        report = self.validator.validate_complete_itinerary(itinerary)
        
        # Should detect uniqueness errors
        uniqueness_errors = [
            issue for issue in report.issues
            if issue.category == ValidationCategory.UNIQUENESS
        ]
        
        assert len(uniqueness_errors) >= 1
        assert report.error_count >= 1

    def test_validation_scenario_incomplete_assignments(self):
        """Test validation with incomplete assignments."""
        scenario = self.validation_scenarios[4]  # Incomplete assignments
        
        # Create itinerary with missing assignments
        itinerary = MainItinerary(
            mbti_personality="INFJ",
            day_1=DayItinerary(day_number=1),  # Empty day
            day_2=DayItinerary(day_number=2),  # Empty day
            day_3=DayItinerary(day_number=3)   # Empty day
        )
        
        # Validate
        report = self.validator.validate_complete_itinerary(itinerary)
        
        # Should detect missing assignments
        assert report.error_count >= 1
        assert not report.is_valid

    def test_session_assignment_validation_comprehensive(self):
        """Test comprehensive session assignment validation."""
        # Test all session types with various operating hours
        test_cases = [
            # (session_type, operating_hours, should_be_valid)
            (SessionType.MORNING, "09:00-18:00", True),
            (SessionType.MORNING, "13:00-18:00", False),  # Afternoon hours for morning
            (SessionType.AFTERNOON, "12:00-17:00", True),
            (SessionType.AFTERNOON, "19:00-23:00", False),  # Night hours for afternoon
            (SessionType.NIGHT, "18:00-23:00", True),
            (SessionType.NIGHT, "09:00-12:00", False),  # Morning hours for night
        ]
        
        for session_type, hours, should_be_valid in test_cases:
            spot = TouristSpot(
                id=f"test_spot_{session_type.value}",
                name=f"Test Spot {session_type.value}",
                address="Test Address",
                district="Central",
                area="Hong Kong Island",
                location_category="Test",
                description="Test spot",
                operating_hours=TouristSpotOperatingHours(
                    monday=hours, tuesday=hours
                ),
                operating_days=["monday", "tuesday"],
                mbti_personality_types=["INFJ"]
            )
            
            issues = self.validator.validate_session_operating_hours(
                spot, session_type, f"test_location_{session_type.value}"
            )
            
            if should_be_valid:
                assert len(issues) == 0, f"Valid {session_type.value} assignment should have no issues"
            else:
                assert len(issues) > 0, f"Invalid {session_type.value} assignment should have issues"

    def test_validation_performance_under_load(self):
        """Test validation performance under load."""
        # Create large itinerary for performance testing
        large_itinerary = self._create_large_itinerary()
        
        # Measure validation time
        start_time = time.time()
        report = self.validator.validate_complete_itinerary(large_itinerary)
        end_time = time.time()
        
        validation_time = (end_time - start_time) * 1000  # Convert to milliseconds
        
        # Validation should complete quickly (< 1 second)
        assert validation_time < 1000, f"Validation time {validation_time}ms too slow"
        
        # Should still produce valid report
        assert isinstance(report.issues, list)
        assert report.total_issues >= 0

    def _create_test_itinerary(self, spots: List[TouristSpot], restaurants: List[Restaurant]) -> MainItinerary:
        """Create test itinerary from spots and restaurants."""
        if not spots or not restaurants:
            return MainItinerary(
                mbti_personality="INFJ",
                day_1=DayItinerary(day_number=1),
                day_2=DayItinerary(day_number=2),
                day_3=DayItinerary(day_number=3)
            )
        
        # Create day 1 with valid assignments
        day_1 = DayItinerary(
            day_number=1,
            morning_session=SessionAssignment("morning", spots[0] if len(spots) > 0 else None),
            afternoon_session=SessionAssignment("afternoon", spots[1] if len(spots) > 1 else None),
            night_session=SessionAssignment("night", spots[2] if len(spots) > 2 else None),
            breakfast=MealAssignment("breakfast", restaurants[0] if len(restaurants) > 0 else None),
            lunch=MealAssignment("lunch", restaurants[1] if len(restaurants) > 1 else None),
            dinner=MealAssignment("dinner", restaurants[2] if len(restaurants) > 2 else None)
        )
        
        return MainItinerary(
            mbti_personality="INFJ",
            day_1=day_1,
            day_2=DayItinerary(day_number=2),
            day_3=DayItinerary(day_number=3)
        )

    def _create_invalid_hours_itinerary(self, spots: List[TouristSpot]) -> MainItinerary:
        """Create itinerary with invalid operating hours assignments."""
        # Assign morning-only spot to afternoon session (invalid)
        # Assign afternoon-only spot to night session (invalid)
        # Assign night-only spot to morning session (invalid)
        
        day_1 = DayItinerary(
            day_number=1,
            morning_session=SessionAssignment("morning", spots[2] if len(spots) > 2 else None),  # Night-only spot
            afternoon_session=SessionAssignment("afternoon", spots[0] if len(spots) > 0 else None),  # Morning-only spot
            night_session=SessionAssignment("night", spots[1] if len(spots) > 1 else None)  # Afternoon-only spot
        )
        
        return MainItinerary(
            mbti_personality="INFJ",
            day_1=day_1,
            day_2=DayItinerary(day_number=2),
            day_3=DayItinerary(day_number=3)
        )

    def _create_district_mismatch_itinerary(self, spots: List[TouristSpot]) -> MainItinerary:
        """Create itinerary with district mismatches."""
        day_1 = DayItinerary(
            day_number=1,
            morning_session=SessionAssignment("morning", spots[0] if len(spots) > 0 else None),  # Central
            afternoon_session=SessionAssignment("afternoon", spots[1] if len(spots) > 1 else None),  # TST
            night_session=SessionAssignment("night", spots[2] if len(spots) > 2 else None)  # Mong Kok
        )
        
        return MainItinerary(
            mbti_personality="INFJ",
            day_1=day_1,
            day_2=DayItinerary(day_number=2),
            day_3=DayItinerary(day_number=3)
        )

    def _create_duplicate_itinerary(self, spots: List[TouristSpot], restaurants: List[Restaurant]) -> MainItinerary:
        """Create itinerary with duplicate assignments."""
        if not spots or not restaurants:
            return MainItinerary(mbti_personality="INFJ")
        
        # Use same spot for multiple sessions
        duplicate_spot = spots[0]
        duplicate_restaurant = restaurants[0]
        
        day_1 = DayItinerary(
            day_number=1,
            morning_session=SessionAssignment("morning", duplicate_spot),
            afternoon_session=SessionAssignment("afternoon", duplicate_spot),  # Duplicate
            night_session=SessionAssignment("night", spots[1] if len(spots) > 1 else None),
            breakfast=MealAssignment("breakfast", duplicate_restaurant),
            lunch=MealAssignment("lunch", duplicate_restaurant),  # Duplicate
            dinner=MealAssignment("dinner", restaurants[1] if len(restaurants) > 1 else None)
        )
        
        return MainItinerary(
            mbti_personality="INFJ",
            day_1=day_1,
            day_2=DayItinerary(day_number=2),
            day_3=DayItinerary(day_number=3)
        )

    def _create_large_itinerary(self) -> MainItinerary:
        """Create large itinerary for performance testing."""
        # Create itinerary with many assignments
        spots = self._create_valid_spots()
        restaurants = self._create_valid_restaurants()
        
        days = []
        for day_num in range(1, 31):  # 30 days
            day = DayItinerary(
                day_number=day_num,
                morning_session=SessionAssignment("morning", spots[day_num % len(spots)]),
                afternoon_session=SessionAssignment("afternoon", spots[(day_num + 1) % len(spots)]),
                night_session=SessionAssignment("night", spots[(day_num + 2) % len(spots)]),
                breakfast=MealAssignment("breakfast", restaurants[day_num % len(restaurants)]),
                lunch=MealAssignment("lunch", restaurants[(day_num + 1) % len(restaurants)]),
                dinner=MealAssignment("dinner", restaurants[(day_num + 2) % len(restaurants)])
            )
            days.append(day)
        
        # Create itinerary with first 3 days
        itinerary = MainItinerary(
            mbti_personality="INFJ",
            day_1=days[0],
            day_2=days[1],
            day_3=days[2]
        )
        
        return itinerary


class TestConcurrentLoadTesting:
    """Comprehensive load testing for concurrent MBTI requests."""

    def setup_method(self):
        """Set up load testing fixtures."""
        self.itinerary_generator = ItineraryGenerator()
        self.load_test_metrics = {
            "concurrent_levels": [],
            "throughput": [],
            "response_times": [],
            "error_rates": [],
            "resource_usage": []
        }

    @pytest.mark.asyncio
    async def test_concurrent_mbti_requests_scalability(self):
        """Test scalability with increasing concurrent MBTI requests."""
        concurrent_levels = [1, 5, 10, 20, 50, 100]
        
        for concurrent_count in concurrent_levels:
            print(f"\nTesting {concurrent_count} concurrent requests...")
            
            # Setup mocks for consistent testing
            with patch.object(self.itinerary_generator, 'nova_client') as mock_nova:
                with patch.object(self.itinerary_generator, 'mcp_client') as mock_mcp:
                    with patch.object(self.itinerary_generator, 'restaurant_agent') as mock_restaurant:
                        
                        # Configure mocks
                        mock_nova.query_mbti_tourist_spots = AsyncMock(
                            return_value=self._create_load_test_spots()
                        )
                        mock_mcp.search_restaurants_by_meal_and_district = AsyncMock(
                            return_value=self._create_load_test_restaurants()
                        )
                        mock_restaurant.get_restaurant_recommendations = AsyncMock(
                            return_value={"recommendation": self._create_load_test_restaurants()[0], "candidates": []}
                        )
                        
                        # Execute concurrent requests
                        start_time = time.time()
                        results = await self._execute_concurrent_requests(concurrent_count)
                        end_time = time.time()
                        
                        # Analyze results
                        total_time = end_time - start_time
                        successful_requests = sum(1 for r in results if r.get("success", False))
                        failed_requests = len(results) - successful_requests
                        
                        throughput = successful_requests / total_time  # Requests per second
                        error_rate = failed_requests / len(results)
                        
                        response_times = [r.get("response_time", 0) for r in results if r.get("success", False)]
                        avg_response_time = statistics.mean(response_times) if response_times else 0
                        
                        # Performance assertions
                        assert error_rate <= 0.05, f"Error rate {error_rate:.2%} too high for {concurrent_count} concurrent requests"
                        assert throughput >= 0.5, f"Throughput {throughput:.2f} req/s too low for {concurrent_count} concurrent requests"
                        
                        if response_times:
                            assert avg_response_time < 20000, f"Average response time {avg_response_time}ms too high under {concurrent_count} concurrent load"
                        
                        # Record metrics
                        self.load_test_metrics["concurrent_levels"].append(concurrent_count)
                        self.load_test_metrics["throughput"].append(throughput)
                        self.load_test_metrics["response_times"].append(avg_response_time)
                        self.load_test_metrics["error_rates"].append(error_rate)
                        
                        print(f"Throughput: {throughput:.2f} req/s, Avg Response: {avg_response_time:.0f}ms, Error Rate: {error_rate:.2%}")

    @pytest.mark.asyncio
    async def test_sustained_load_endurance(self):
        """Test system endurance under sustained load."""
        duration_minutes = 2  # 2-minute endurance test
        requests_per_minute = 30
        
        total_requests = duration_minutes * requests_per_minute
        request_interval = 60.0 / requests_per_minute  # Seconds between requests
        
        results = []
        start_time = time.time()
        
        with patch.object(self.itinerary_generator, 'nova_client') as mock_nova:
            with patch.object(self.itinerary_generator, 'mcp_client') as mock_mcp:
                with patch.object(self.itinerary_generator, 'restaurant_agent') as mock_restaurant:
                    
                    # Configure mocks
                    mock_nova.query_mbti_tourist_spots = AsyncMock(
                        return_value=self._create_load_test_spots()
                    )
                    mock_mcp.search_restaurants_by_meal_and_district = AsyncMock(
                        return_value=self._create_load_test_restaurants()
                    )
                    mock_restaurant.get_restaurant_recommendations = AsyncMock(
                        return_value={"recommendation": self._create_load_test_restaurants()[0], "candidates": []}
                    )
                    
                    # Execute sustained requests
                    for i in range(total_requests):
                        request_start = time.time()
                        
                        try:
                            mbti_type = ["INFJ", "ENFP", "INTJ", "ESTP"][i % 4]
                            result = await self.itinerary_generator.generate_complete_itinerary(mbti_type)
                            
                            request_time = (time.time() - request_start) * 1000
                            results.append({"success": True, "response_time": request_time})
                            
                        except Exception as e:
                            results.append({"success": False, "error": str(e)})
                        
                        # Maintain request rate
                        elapsed = time.time() - start_time
                        expected_time = i * request_interval
                        if elapsed < expected_time:
                            await asyncio.sleep(expected_time - elapsed)
        
        # Analyze endurance results
        successful_requests = sum(1 for r in results if r.get("success", False))
        success_rate = successful_requests / len(results)
        
        response_times = [r.get("response_time", 0) for r in results if r.get("success", False)]
        
        # Performance should remain stable throughout test
        assert success_rate >= 0.95, f"Success rate {success_rate:.2%} degraded during sustained load"
        
        if response_times:
            # Check for performance degradation over time
            first_half = response_times[:len(response_times)//2]
            second_half = response_times[len(response_times)//2:]
            
            if first_half and second_half:
                first_half_avg = statistics.mean(first_half)
                second_half_avg = statistics.mean(second_half)
                
                degradation = (second_half_avg - first_half_avg) / first_half_avg
                assert degradation < 0.5, f"Performance degradation {degradation:.2%} too high during sustained load"

    @pytest.mark.asyncio
    async def test_burst_load_handling(self):
        """Test system handling of burst load scenarios."""
        # Simulate burst scenarios: sudden spike in requests
        burst_scenarios = [
            {"burst_size": 20, "burst_duration": 5},   # 20 requests in 5 seconds
            {"burst_size": 50, "burst_duration": 10},  # 50 requests in 10 seconds
            {"burst_size": 100, "burst_duration": 20}  # 100 requests in 20 seconds
        ]
        
        for scenario in burst_scenarios:
            burst_size = scenario["burst_size"]
            burst_duration = scenario["burst_duration"]
            
            print(f"\nTesting burst: {burst_size} requests in {burst_duration} seconds")
            
            with patch.object(self.itinerary_generator, 'nova_client') as mock_nova:
                with patch.object(self.itinerary_generator, 'mcp_client') as mock_mcp:
                    with patch.object(self.itinerary_generator, 'restaurant_agent') as mock_restaurant:
                        
                        # Configure mocks
                        mock_nova.query_mbti_tourist_spots = AsyncMock(
                            return_value=self._create_load_test_spots()
                        )
                        mock_mcp.search_restaurants_by_meal_and_district = AsyncMock(
                            return_value=self._create_load_test_restaurants()
                        )
                        mock_restaurant.get_restaurant_recommendations = AsyncMock(
                            return_value={"recommendation": self._create_load_test_restaurants()[0], "candidates": []}
                        )
                        
                        # Execute burst requests
                        start_time = time.time()
                        
                        # Create all tasks at once (burst)
                        tasks = []
                        for i in range(burst_size):
                            mbti_type = ["INFJ", "ENFP", "INTJ", "ESTP"][i % 4]
                            task = self.itinerary_generator.generate_complete_itinerary(mbti_type)
                            tasks.append(task)
                        
                        # Execute all tasks concurrently
                        results = await asyncio.gather(*tasks, return_exceptions=True)
                        
                        end_time = time.time()
                        actual_duration = end_time - start_time
                        
                        # Analyze burst results
                        successful_results = [r for r in results if not isinstance(r, Exception)]
                        failed_results = [r for r in results if isinstance(r, Exception)]
                        
                        success_rate = len(successful_results) / len(results)
                        
                        # Burst handling requirements
                        assert success_rate >= 0.90, f"Burst success rate {success_rate:.2%} too low for {burst_size} requests"
                        assert actual_duration <= burst_duration * 2, f"Burst processing time {actual_duration:.1f}s too slow"
                        
                        print(f"Burst completed in {actual_duration:.1f}s with {success_rate:.2%} success rate")

    async def _execute_concurrent_requests(self, concurrent_count: int) -> List[Dict[str, Any]]:
        """Execute concurrent requests and return results."""
        mbti_types = ["INFJ", "ENFP", "INTJ", "ESTP", "ISFJ", "ISFP", "ISTJ", "ISTP"]
        
        async def single_request(request_id: int) -> Dict[str, Any]:
            try:
                start_time = time.time()
                mbti_type = mbti_types[request_id % len(mbti_types)]
                
                result = await self.itinerary_generator.generate_complete_itinerary(mbti_type)
                
                end_time = time.time()
                response_time = (end_time - start_time) * 1000
                
                return {
                    "success": True,
                    "response_time": response_time,
                    "mbti_type": mbti_type,
                    "request_id": request_id
                }
                
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e),
                    "request_id": request_id
                }
        
        # Execute all requests concurrently
        tasks = [single_request(i) for i in range(concurrent_count)]
        results = await asyncio.gather(*tasks)
        
        return results

    def _create_load_test_spots(self) -> List[TouristSpot]:
        """Create tourist spots optimized for load testing."""
        spots = []
        
        for i in range(50):  # Sufficient spots for load testing
            operating_hours = TouristSpotOperatingHours(
                monday="09:00-22:00", tuesday="09:00-22:00", wednesday="09:00-22:00",
                thursday="09:00-22:00", friday="09:00-22:00", saturday="10:00-21:00", sunday="10:00-21:00"
            )
            
            spot = TouristSpot(
                id=f"load_spot_{i}",
                name=f"Load Test Spot {i}",
                address=f"Load Test Address {i}",
                district=["Central", "Admiralty", "Wan Chai", "Tsim Sha Tsui"][i % 4],
                area="Hong Kong Island" if i % 2 == 0 else "Kowloon",
                location_category=["Museum", "Park", "Gallery", "Market"][i % 4],
                description=f"Load test spot {i}",
                operating_hours=operating_hours,
                operating_days=["daily"],
                mbti_personality_types=["INFJ", "ENFP", "INTJ", "ESTP"][i % 4],
                keywords=["load", "test"],
                mbti_match=True
            )
            spots.append(spot)
        
        return spots

    def _create_load_test_restaurants(self) -> List[Restaurant]:
        """Create restaurants optimized for load testing."""
        restaurants = []
        
        districts = ["Central", "Admiralty", "Wan Chai", "Tsim Sha Tsui"]
        meal_configs = [
            ("breakfast", "07:00-11:00"),
            ("lunch", "11:30-15:00"),
            ("dinner", "18:00-22:00")
        ]
        
        for district in districts:
            for meal_type, hours in meal_configs:
                for i in range(5):  # 5 restaurants per meal per district
                    restaurant = Restaurant(
                        id=f"load_{meal_type}_{district.lower()}_{i}",
                        name=f"Load {district} {meal_type.title()} {i}",
                        address=f"Load Test {meal_type.title()} Address {i}",
                        district=district,
                        operating_hours=hours,
                        cuisine_type="Load Test Cuisine",
                        rating=3.5 + (i * 0.1)
                    )
                    restaurants.append(restaurant)
        
        return restaurants

    def teardown_method(self):
        """Generate load test report."""
        if self.load_test_metrics["concurrent_levels"]:
            print(f"\n{'='*60}")
            print("LOAD TEST SUMMARY")
            print(f"{'='*60}")
            
            for i, level in enumerate(self.load_test_metrics["concurrent_levels"]):
                throughput = self.load_test_metrics["throughput"][i]
                response_time = self.load_test_metrics["response_times"][i]
                error_rate = self.load_test_metrics["error_rates"][i]
                
                print(f"Concurrent Level: {level:3d} | "
                      f"Throughput: {throughput:5.2f} req/s | "
                      f"Avg Response: {response_time:6.0f}ms | "
                      f"Error Rate: {error_rate:5.2%}")


class TestRegressionTesting:
    """Regression testing for itinerary generation accuracy."""

    def setup_method(self):
        """Set up regression testing fixtures."""
        self.itinerary_generator = ItineraryGenerator()
        self.baseline_results = self._load_baseline_results()

    def _load_baseline_results(self) -> Dict[str, Any]:
        """Load baseline results for regression testing."""
        # In a real implementation, this would load from a file
        # For testing, we'll create expected baseline results
        return {
            "INFJ": {
                "expected_spot_categories": ["Museum", "Temple", "Garden", "Gallery"],
                "expected_districts": ["Central", "Admiralty", "Wan Chai"],
                "expected_mbti_match_rate": 0.8,
                "expected_response_time_ms": 5000
            },
            "ENFP": {
                "expected_spot_categories": ["Market", "Festival", "Entertainment", "Park"],
                "expected_districts": ["Tsim Sha Tsui", "Mong Kok", "Causeway Bay"],
                "expected_mbti_match_rate": 0.75,
                "expected_response_time_ms": 5000
            }
        }

    @pytest.mark.asyncio
    async def test_infj_itinerary_accuracy_regression(self):
        """Test INFJ itinerary generation accuracy against baseline."""
        baseline = self.baseline_results["INFJ"]
        
        with patch.object(self.itinerary_generator, 'nova_client') as mock_nova:
            with patch.object(self.itinerary_generator, 'mcp_client') as mock_mcp:
                with patch.object(self.itinerary_generator, 'restaurant_agent') as mock_restaurant:
                    
                    # Setup consistent mocks for regression testing
                    infj_spots = self._create_infj_baseline_spots()
                    mock_nova.query_mbti_tourist_spots = AsyncMock(return_value=infj_spots)
                    mock_mcp.search_restaurants_by_meal_and_district = AsyncMock(
                        return_value=self._create_baseline_restaurants()
                    )
                    mock_restaurant.get_restaurant_recommendations = AsyncMock(
                        return_value={"recommendation": self._create_baseline_restaurants()[0], "candidates": []}
                    )
                    
                    # Generate itinerary
                    start_time = time.time()
                    result = await self.itinerary_generator.generate_complete_itinerary("INFJ")
                    end_time = time.time()
                    
                    response_time = (end_time - start_time) * 1000
                    
                    # Regression checks
                    self._validate_regression_results(result, baseline, response_time)

    @pytest.mark.asyncio
    async def test_enfp_itinerary_accuracy_regression(self):
        """Test ENFP itinerary generation accuracy against baseline."""
        baseline = self.baseline_results["ENFP"]
        
        with patch.object(self.itinerary_generator, 'nova_client') as mock_nova:
            with patch.object(self.itinerary_generator, 'mcp_client') as mock_mcp:
                with patch.object(self.itinerary_generator, 'restaurant_agent') as mock_restaurant:
                    
                    # Setup consistent mocks for regression testing
                    enfp_spots = self._create_enfp_baseline_spots()
                    mock_nova.query_mbti_tourist_spots = AsyncMock(return_value=enfp_spots)
                    mock_mcp.search_restaurants_by_meal_and_district = AsyncMock(
                        return_value=self._create_baseline_restaurants()
                    )
                    mock_restaurant.get_restaurant_recommendations = AsyncMock(
                        return_value={"recommendation": self._create_baseline_restaurants()[0], "candidates": []}
                    )
                    
                    # Generate itinerary
                    start_time = time.time()
                    result = await self.itinerary_generator.generate_complete_itinerary("ENFP")
                    end_time = time.time()
                    
                    response_time = (end_time - start_time) * 1000
                    
                    # Regression checks
                    self._validate_regression_results(result, baseline, response_time)

    def _validate_regression_results(self, result: Dict[str, Any], baseline: Dict[str, Any], response_time: float):
        """Validate results against baseline for regression testing."""
        # Check response time regression
        assert response_time <= baseline["expected_response_time_ms"] * 1.2, \
            f"Response time {response_time}ms exceeds baseline {baseline['expected_response_time_ms']}ms by >20%"
        
        # Check structure completeness
        assert "main_itinerary" in result
        assert "candidate_tourist_spots" in result
        assert "candidate_restaurants" in result
        assert "metadata" in result
        
        # Check MBTI match rate
        main_itinerary = result["main_itinerary"]
        total_spots = 0
        mbti_matched_spots = 0
        
        for day_key in ["day_1", "day_2", "day_3"]:
            if day_key in main_itinerary:
                day = main_itinerary[day_key]
                for session_key in ["morning_session", "afternoon_session", "night_session"]:
                    if session_key in day and day[session_key] and day[session_key].get("tourist_spot"):
                        total_spots += 1
                        spot = day[session_key]["tourist_spot"]
                        if spot.get("mbti_match", False):
                            mbti_matched_spots += 1
        
        if total_spots > 0:
            actual_mbti_match_rate = mbti_matched_spots / total_spots
            expected_rate = baseline["expected_mbti_match_rate"]
            
            # Allow 10% variance from baseline
            assert actual_mbti_match_rate >= expected_rate * 0.9, \
                f"MBTI match rate {actual_mbti_match_rate:.2%} below baseline {expected_rate:.2%}"

    def _create_infj_baseline_spots(self) -> List[TouristSpot]:
        """Create INFJ baseline spots for regression testing."""
        spots = []
        categories = ["Museum", "Temple", "Garden", "Gallery"]
        districts = ["Central", "Admiralty", "Wan Chai"]
        
        for i in range(15):
            spot = TouristSpot(
                id=f"infj_baseline_{i}",
                name=f"INFJ Baseline Spot {i}",
                address=f"Baseline Address {i}",
                district=districts[i % len(districts)],
                area="Hong Kong Island",
                location_category=categories[i % len(categories)],
                description=f"INFJ baseline spot {i}",
                operating_hours=TouristSpotOperatingHours(
                    monday="09:00-18:00", tuesday="09:00-18:00"
                ),
                operating_days=["daily"],
                mbti_personality_types=["INFJ"],
                keywords=["quiet", "cultural", "peaceful"],
                mbti_match=True
            )
            spots.append(spot)
        
        return spots

    def _create_enfp_baseline_spots(self) -> List[TouristSpot]:
        """Create ENFP baseline spots for regression testing."""
        spots = []
        categories = ["Market", "Festival", "Entertainment", "Park"]
        districts = ["Tsim Sha Tsui", "Mong Kok", "Causeway Bay"]
        
        for i in range(15):
            spot = TouristSpot(
                id=f"enfp_baseline_{i}",
                name=f"ENFP Baseline Spot {i}",
                address=f"Baseline Address {i}",
                district=districts[i % len(districts)],
                area="Kowloon" if i % 2 == 0 else "Hong Kong Island",
                location_category=categories[i % len(categories)],
                description=f"ENFP baseline spot {i}",
                operating_hours=TouristSpotOperatingHours(
                    monday="10:00-22:00", tuesday="10:00-22:00"
                ),
                operating_days=["daily"],
                mbti_personality_types=["ENFP"],
                keywords=["vibrant", "social", "interactive"],
                mbti_match=True
            )
            spots.append(spot)
        
        return spots

    def _create_baseline_restaurants(self) -> List[Restaurant]:
        """Create baseline restaurants for regression testing."""
        restaurants = []
        
        for i in range(10):
            restaurant = Restaurant(
                id=f"baseline_restaurant_{i}",
                name=f"Baseline Restaurant {i}",
                address=f"Baseline Restaurant Address {i}",
                district="Central",
                operating_hours="09:00-22:00",
                cuisine_type="Baseline Cuisine",
                rating=4.0
            )
            restaurants.append(restaurant)
        
        return restaurants


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "--tb=short"])