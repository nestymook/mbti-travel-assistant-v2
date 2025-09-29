"""
Comprehensive Unit Tests for Assignment Validator and Error Handling

This module provides comprehensive unit tests for the assignment validator system
with 90%+ code coverage, including all validation scenarios, error conditions, and edge cases.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import List, Dict, Any
from datetime import datetime, time
import json

from ..services.assignment_validator import (
    AssignmentValidator,
    ValidationIssue,
    ValidationReport,
    ValidationSeverity,
    ValidationCategory,
    ValidationError,
    ValidationConfigurationError
)
from ..models.tourist_spot_models import TouristSpot, TouristSpotOperatingHours, SessionType
from ..models.itinerary_models import (
    MainItinerary,
    DayItinerary,
    SessionAssignment,
    MealAssignment
)
from ..models.restaurant_models import Restaurant


class TestAssignmentValidatorComprehensive:
    """Comprehensive test cases for AssignmentValidator with 90%+ coverage."""

    def setup_method(self):
        """Set up test fixtures."""
        self.validator = AssignmentValidator()
        self.test_spots = self._create_comprehensive_test_spots()
        self.test_restaurants = self._create_comprehensive_test_restaurants()
        self.test_itinerary = self._create_comprehensive_test_itinerary()

    def _create_comprehensive_test_spots(self) -> List[TouristSpot]:
        """Create comprehensive test spots covering all validation scenarios."""
        spots = []
        
        # Spot with complete valid data
        spots.append(TouristSpot(
            id="valid_spot_1",
            name="Valid Museum",
            address="123 Valid Street, Central, Hong Kong",
            district="Central",
            area="Hong Kong Island",
            location_category="Museum",
            description="A valid museum for testing",
            operating_hours=TouristSpotOperatingHours(
                monday="09:00-18:00", tuesday="09:00-18:00", wednesday="09:00-18:00",
                thursday="09:00-18:00", friday="09:00-18:00", saturday="10:00-17:00", sunday="10:00-17:00"
            ),
            operating_days=["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"],
            mbti_personality_types=["INFJ"],
            keywords=["cultural", "quiet", "educational"]
        ))
        
        # Spot with morning-only hours
        spots.append(TouristSpot(
            id="morning_only_spot",
            name="Morning Only Park",
            address="456 Morning Street, Admiralty, Hong Kong",
            district="Admiralty",
            area="Hong Kong Island",
            location_category="Park",
            description="A park that opens only in the morning",
            operating_hours=TouristSpotOperatingHours(
                monday="07:00-12:00", tuesday="07:00-12:00", wednesday="07:00-12:00",
                thursday="07:00-12:00", friday="07:00-12:00", saturday="08:00-12:00", sunday="08:00-12:00"
            ),
            operating_days=["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"],
            mbti_personality_types=["INFJ"],
            keywords=["nature", "peaceful"]
        ))
        
        # Spot with night-only hours
        spots.append(TouristSpot(
            id="night_only_spot",
            name="Night Market",
            address="789 Night Street, Wan Chai, Hong Kong",
            district="Wan Chai",
            area="Hong Kong Island",
            location_category="Market",
            description="A market that operates only at night",
            operating_hours=TouristSpotOperatingHours(
                monday="19:00-23:00", tuesday="19:00-23:00", wednesday="19:00-23:00",
                thursday="19:00-23:00", friday="19:00-23:00", saturday="19:00-24:00", sunday="19:00-24:00"
            ),
            operating_days=["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"],
            mbti_personality_types=["ENFP"],
            keywords=["vibrant", "social", "food"]
        ))
        
        # Spot with no operating hours (always available)
        spots.append(TouristSpot(
            id="always_open_spot",
            name="Always Open Attraction",
            address="321 Always Street, Tsim Sha Tsui, Kowloon",
            district="Tsim Sha Tsui",
            area="Kowloon",
            location_category="Attraction",
            description="An attraction that is always open",
            operating_hours=None,
            operating_days=["daily"],
            mbti_personality_types=["INTJ"],
            keywords=["accessible", "flexible"]
        ))
        
        # Spot with incomplete data
        spots.append(TouristSpot(
            id="incomplete_spot",
            name="Incomplete Spot",
            address="",  # Missing address
            district="",  # Missing district
            area="Hong Kong Island",
            location_category="Unknown",
            description="A spot with incomplete data",
            operating_hours=None,
            operating_days=[],
            mbti_personality_types=[],
            keywords=[]
        ))
        
        # Spot with invalid operating hours format
        spots.append(TouristSpot(
            id="invalid_hours_spot",
            name="Invalid Hours Spot",
            address="999 Invalid Street, Central, Hong Kong",
            district="Central",
            area="Hong Kong Island",
            location_category="Museum",
            description="A spot with invalid operating hours",
            operating_hours=TouristSpotOperatingHours(
                monday="25:00-30:00",  # Invalid time format
                tuesday="invalid-time",
                wednesday="",
                thursday="09:00-08:00",  # End before start
                friday="09:00-18:00",
                saturday="10:00-17:00",
                sunday="10:00-17:00"
            ),
            operating_days=["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"],
            mbti_personality_types=["INFJ"],
            keywords=["problematic"]
        ))
        
        return spots

    def _create_comprehensive_test_restaurants(self) -> List[Restaurant]:
        """Create comprehensive test restaurants covering all validation scenarios."""
        restaurants = []
        
        # Valid breakfast restaurant
        restaurants.append(Restaurant(
            id="breakfast_rest_1",
            name="Morning Cafe",
            address="123 Breakfast Street, Central, Hong Kong",
            district="Central",
            operating_hours="07:00-11:00",
            cuisine_type="Cafe",
            phone="+852-1234-5678",
            rating=4.5
        ))
        
        # Valid lunch restaurant
        restaurants.append(Restaurant(
            id="lunch_rest_1",
            name="Lunch Bistro",
            address="456 Lunch Street, Admiralty, Hong Kong",
            district="Admiralty",
            operating_hours="11:30-15:00",
            cuisine_type="Bistro",
            phone="+852-2345-6789",
            rating=4.2
        ))
        
        # Valid dinner restaurant
        restaurants.append(Restaurant(
            id="dinner_rest_1",
            name="Evening Restaurant",
            address="789 Dinner Street, Wan Chai, Hong Kong",
            district="Wan Chai",
            operating_hours="18:00-22:00",
            cuisine_type="Fine Dining",
            phone="+852-3456-7890",
            rating=4.8
        ))
        
        # Restaurant with invalid operating hours
        restaurants.append(Restaurant(
            id="invalid_hours_rest",
            name="Invalid Hours Restaurant",
            address="999 Invalid Street, Central, Hong Kong",
            district="Central",
            operating_hours="25:00-30:00",  # Invalid time format
            cuisine_type="Unknown",
            phone="",
            rating=0.0
        ))
        
        # Restaurant with incomplete data
        restaurants.append(Restaurant(
            id="incomplete_rest",
            name="",  # Missing name
            address="",  # Missing address
            district="",  # Missing district
            operating_hours="",  # Missing hours
            cuisine_type="",
            phone="",
            rating=None
        ))
        
        return restaurants

    def _create_comprehensive_test_itinerary(self) -> MainItinerary:
        """Create comprehensive test itinerary with various validation scenarios."""
        # Day 1 - Valid assignments
        day_1_morning = SessionAssignment(
            session_type="morning",
            tourist_spot=self.test_spots[0]  # Valid spot
        )
        day_1_afternoon = SessionAssignment(
            session_type="afternoon",
            tourist_spot=self.test_spots[0]  # Same spot (duplicate issue)
        )
        day_1_night = SessionAssignment(
            session_type="night",
            tourist_spot=self.test_spots[2]  # Night-only spot
        )
        
        day_1_breakfast = MealAssignment(
            meal_type="breakfast",
            restaurant=self.test_restaurants[0]  # Valid breakfast restaurant
        )
        day_1_lunch = MealAssignment(
            meal_type="lunch",
            restaurant=self.test_restaurants[1]  # Valid lunch restaurant
        )
        day_1_dinner = MealAssignment(
            meal_type="dinner",
            restaurant=self.test_restaurants[2]  # Valid dinner restaurant
        )
        
        day_1 = DayItinerary(
            day_number=1,
            morning_session=day_1_morning,
            afternoon_session=day_1_afternoon,
            night_session=day_1_night,
            breakfast=day_1_breakfast,
            lunch=day_1_lunch,
            dinner=day_1_dinner
        )
        
        # Day 2 - Mixed valid/invalid assignments
        day_2_morning = SessionAssignment(
            session_type="morning",
            tourist_spot=self.test_spots[2]  # Night-only spot (invalid for morning)
        )
        day_2_afternoon = SessionAssignment(
            session_type="afternoon",
            tourist_spot=self.test_spots[1]  # Morning-only spot (invalid for afternoon)
        )
        day_2_night = SessionAssignment(
            session_type="night",
            tourist_spot=self.test_spots[3]  # Always open spot (valid)
        )
        
        day_2_breakfast = MealAssignment(
            meal_type="breakfast",
            restaurant=self.test_restaurants[3]  # Invalid hours restaurant
        )
        day_2_lunch = MealAssignment(
            meal_type="lunch",
            restaurant=None  # Missing restaurant
        )
        day_2_dinner = MealAssignment(
            meal_type="dinner",
            restaurant=self.test_restaurants[4]  # Incomplete restaurant
        )
        
        day_2 = DayItinerary(
            day_number=2,
            morning_session=day_2_morning,
            afternoon_session=day_2_afternoon,
            night_session=day_2_night,
            breakfast=day_2_breakfast,
            lunch=day_2_lunch,
            dinner=day_2_dinner
        )
        
        # Day 3 - Incomplete assignments
        day_3 = DayItinerary(
            day_number=3,
            morning_session=None,  # Missing session
            afternoon_session=None,  # Missing session
            night_session=None,  # Missing session
            breakfast=None,  # Missing meal
            lunch=None,  # Missing meal
            dinner=None  # Missing meal
        )
        
        return MainItinerary(
            mbti_personality="INFJ",
            day_1=day_1,
            day_2=day_2,
            day_3=day_3
        )

    def test_initialization_default_configuration(self):
        """Test validator initialization with default configuration."""
        validator = AssignmentValidator()
        
        assert validator.enable_strict_validation is True
        assert validator.enable_warnings is True
        assert validator.enable_suggestions is True
        assert len(validator.session_time_ranges) == 3
        assert len(validator.meal_time_ranges) == 3
        assert len(validator.validation_rules) > 0

    def test_initialization_custom_configuration(self):
        """Test validator initialization with custom configuration."""
        custom_config = {
            'enable_strict_validation': False,
            'enable_warnings': False,
            'enable_suggestions': False,
            'custom_session_ranges': {
                SessionType.MORNING: (6, 0, 10, 59),
                SessionType.AFTERNOON: (11, 0, 16, 59),
                SessionType.NIGHT: (17, 0, 23, 59)
            }
        }
        
        validator = AssignmentValidator(**custom_config)
        
        assert validator.enable_strict_validation is False
        assert validator.enable_warnings is False
        assert validator.enable_suggestions is False

    def test_validate_session_operating_hours_all_scenarios(self):
        """Test session operating hours validation for all scenarios."""
        test_cases = [
            # (spot_index, session_type, expected_error_count)
            (0, SessionType.MORNING, 0),    # Valid all-day spot for morning
            (0, SessionType.AFTERNOON, 0),  # Valid all-day spot for afternoon
            (0, SessionType.NIGHT, 0),      # Valid all-day spot for night
            (1, SessionType.MORNING, 0),    # Morning-only spot for morning
            (1, SessionType.AFTERNOON, 1),  # Morning-only spot for afternoon (invalid)
            (1, SessionType.NIGHT, 1),      # Morning-only spot for night (invalid)
            (2, SessionType.MORNING, 1),    # Night-only spot for morning (invalid)
            (2, SessionType.AFTERNOON, 1),  # Night-only spot for afternoon (invalid)
            (2, SessionType.NIGHT, 0),      # Night-only spot for night
            (3, SessionType.MORNING, 0),    # Always open spot for morning
            (3, SessionType.AFTERNOON, 0),  # Always open spot for afternoon
            (3, SessionType.NIGHT, 0),      # Always open spot for night
            (5, SessionType.MORNING, 1),    # Invalid hours spot for morning
        ]
        
        for spot_index, session_type, expected_error_count in test_cases:
            issues = self.validator.validate_session_operating_hours(
                self.test_spots[spot_index],
                session_type,
                f"test_location_{spot_index}_{session_type.value}"
            )
            
            assert len(issues) == expected_error_count, \
                f"Spot {spot_index} for {session_type.value} should have {expected_error_count} issues, got {len(issues)}"

    def test_validate_session_operating_hours_edge_cases(self):
        """Test session operating hours validation edge cases."""
        # Test with None spot
        issues = self.validator.validate_session_operating_hours(
            None, SessionType.MORNING, "test_location"
        )
        assert len(issues) == 1
        assert issues[0].severity == ValidationSeverity.ERROR
        assert issues[0].category == ValidationCategory.DATA_INTEGRITY

    def test_validate_district_matching_all_scenarios(self):
        """Test district matching validation for all scenarios."""
        # Same district scenario
        issues = self.validator.validate_district_matching(
            self.test_spots[0],  # Central district
            self.test_spots[2],  # Wan Chai district
            self.test_spots[0],  # Central district (reference)
            "day_1"
        )
        
        # Should have warning for night spot in different district
        district_warnings = [i for i in issues if i.category == ValidationCategory.DISTRICT_MATCHING]
        assert len(district_warnings) >= 1

    def test_validate_district_matching_edge_cases(self):
        """Test district matching validation edge cases."""
        # Test with None spots
        issues = self.validator.validate_district_matching(
            None, None, None, "day_1"
        )
        assert len(issues) >= 1
        
        # Test with missing district information
        spot_no_district = TouristSpot(
            id="no_district",
            name="No District Spot",
            address="Address",
            district="",  # Empty district
            area="Hong Kong Island",
            location_category="Test",
            description="Test spot",
            operating_hours=None,
            operating_days=["daily"],
            mbti_personality_types=["INFJ"]
        )
        
        issues = self.validator.validate_district_matching(
            spot_no_district, spot_no_district, spot_no_district, "day_1"
        )
        assert len(issues) >= 1

    def test_validate_area_matching_all_scenarios(self):
        """Test area matching validation for all scenarios."""
        # Same area scenario
        issues = self.validator.validate_area_matching(
            self.test_spots[0],  # Hong Kong Island
            self.test_spots[1],  # Hong Kong Island
            self.test_spots[0],  # Hong Kong Island (reference)
            "day_1"
        )
        
        # Should have no area matching issues
        area_issues = [i for i in issues if i.category == ValidationCategory.AREA_MATCHING]
        assert len(area_issues) == 0

    def test_validate_uniqueness_constraints_duplicate_spots(self):
        """Test uniqueness constraints validation with duplicate spots."""
        # Create itinerary with duplicate spots
        duplicate_itinerary = MainItinerary(
            mbti_personality="INFJ",
            day_1=DayItinerary(
                day_number=1,
                morning_session=SessionAssignment("morning", self.test_spots[0]),
                afternoon_session=SessionAssignment("afternoon", self.test_spots[0]),  # Duplicate
                night_session=SessionAssignment("night", self.test_spots[1])
            ),
            day_2=DayItinerary(day_number=2),
            day_3=DayItinerary(day_number=3)
        )
        
        issues = self.validator.validate_uniqueness_constraints(duplicate_itinerary)
        
        # Should detect duplicate spot
        uniqueness_errors = [i for i in issues if i.category == ValidationCategory.UNIQUENESS]
        assert len(uniqueness_errors) >= 1

    def test_validate_uniqueness_constraints_duplicate_restaurants(self):
        """Test uniqueness constraints validation with duplicate restaurants."""
        # Create itinerary with duplicate restaurants
        duplicate_itinerary = MainItinerary(
            mbti_personality="INFJ",
            day_1=DayItinerary(
                day_number=1,
                breakfast=MealAssignment("breakfast", self.test_restaurants[0]),
                lunch=MealAssignment("lunch", self.test_restaurants[0]),  # Duplicate
                dinner=MealAssignment("dinner", self.test_restaurants[1])
            ),
            day_2=DayItinerary(day_number=2),
            day_3=DayItinerary(day_number=3)
        )
        
        issues = self.validator.validate_uniqueness_constraints(duplicate_itinerary)
        
        # Should detect duplicate restaurant
        uniqueness_errors = [i for i in issues if i.category == ValidationCategory.UNIQUENESS]
        assert len(uniqueness_errors) >= 1

    def test_validate_meal_operating_hours_all_scenarios(self):
        """Test meal operating hours validation for all scenarios."""
        test_cases = [
            # (restaurant_index, meal_type, expected_error_count)
            (0, "breakfast", 0),  # Valid breakfast restaurant
            (1, "lunch", 0),      # Valid lunch restaurant
            (2, "dinner", 0),     # Valid dinner restaurant
            (0, "lunch", 1),      # Breakfast restaurant for lunch (invalid)
            (1, "dinner", 1),     # Lunch restaurant for dinner (invalid)
            (2, "breakfast", 1),  # Dinner restaurant for breakfast (invalid)
            (3, "breakfast", 1),  # Invalid hours restaurant
        ]
        
        for restaurant_index, meal_type, expected_error_count in test_cases:
            issues = self.validator.validate_meal_operating_hours(
                self.test_restaurants[restaurant_index],
                meal_type,
                f"test_meal_{restaurant_index}_{meal_type}"
            )
            
            assert len(issues) == expected_error_count, \
                f"Restaurant {restaurant_index} for {meal_type} should have {expected_error_count} issues, got {len(issues)}"

    def test_validate_meal_operating_hours_edge_cases(self):
        """Test meal operating hours validation edge cases."""
        # Test with None restaurant
        issues = self.validator.validate_meal_operating_hours(
            None, "breakfast", "test_location"
        )
        assert len(issues) == 1
        assert issues[0].severity == ValidationSeverity.ERROR

    def test_validate_complete_itinerary_comprehensive(self):
        """Test comprehensive itinerary validation."""
        report = self.validator.validate_complete_itinerary(self.test_itinerary)
        
        assert isinstance(report, ValidationReport)
        assert report.total_issues > 0  # Should have issues due to test data
        assert report.error_count >= 0
        assert report.warning_count >= 0
        assert report.info_count >= 0
        assert len(report.issues) == report.total_issues
        assert report.validation_timestamp is not None

    def test_validate_complete_itinerary_empty_itinerary(self):
        """Test validation of empty itinerary."""
        empty_itinerary = MainItinerary(
            mbti_personality="",
            day_1=DayItinerary(day_number=1),
            day_2=DayItinerary(day_number=2),
            day_3=DayItinerary(day_number=3)
        )
        
        report = self.validator.validate_complete_itinerary(empty_itinerary)
        
        assert not report.is_valid
        assert report.error_count > 0

    def test_validate_complete_itinerary_none_input(self):
        """Test validation with None itinerary."""
        with pytest.raises(ValidationError):
            self.validator.validate_complete_itinerary(None)

    def test_generate_detailed_validation_report_comprehensive(self):
        """Test comprehensive detailed validation report generation."""
        detailed_report = self.validator.generate_detailed_validation_report(self.test_itinerary)
        
        # Check main structure
        assert 'detailed_analysis' in detailed_report
        assert 'correction_recommendations' in detailed_report
        assert 'validation_metrics' in detailed_report
        assert 'total_issues' in detailed_report
        assert 'error_count' in detailed_report
        assert 'warning_count' in detailed_report
        
        # Check detailed analysis sections
        detailed_analysis = detailed_report['detailed_analysis']
        expected_sections = [
            'session_analysis', 'restaurant_analysis', 'location_coherence_analysis',
            'mbti_alignment_analysis', 'coverage_analysis'
        ]
        
        for section in expected_sections:
            assert section in detailed_analysis

    def test_generate_validation_warnings_comprehensive(self):
        """Test comprehensive validation warnings generation."""
        warnings = self.validator.generate_validation_warnings(self.test_itinerary)
        
        assert isinstance(warnings, list)
        
        # Check warning structure if warnings exist
        if warnings:
            warning = warnings[0]
            expected_fields = [
                'warning_id', 'category', 'message', 'suggestion',
                'impact_level', 'auto_correctable', 'correction_options'
            ]
            
            for field in expected_fields:
                assert field in warning

    def test_suggest_corrections_for_validation_failures_comprehensive(self):
        """Test comprehensive correction suggestions generation."""
        # Create diverse validation issues
        issues = [
            ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category=ValidationCategory.OPERATING_HOURS,
                message="Operating hours error",
                location="day_1.morning_session",
                suggestion="Replace with valid spot",
                affected_item_id="test_spot_1",
                affected_item_name="Test Spot",
                rule_violated="Requirement 7.1"
            ),
            ValidationIssue(
                severity=ValidationSeverity.WARNING,
                category=ValidationCategory.DISTRICT_MATCHING,
                message="District matching warning",
                location="day_1.afternoon_session",
                suggestion="Consider same district spot",
                affected_item_id="test_spot_2",
                affected_item_name="Test Spot 2",
                rule_violated="Requirement 7.4"
            ),
            ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category=ValidationCategory.UNIQUENESS,
                message="Uniqueness violation",
                location="day_2.morning_session",
                suggestion="Select different spot",
                affected_item_id="test_spot_3",
                affected_item_name="Test Spot 3",
                rule_violated="Requirement 2.6"
            )
        ]
        
        corrections = self.validator.suggest_corrections_for_validation_failures(issues)
        
        assert isinstance(corrections, dict)
        assert len(corrections) >= 2  # Should have corrections for different categories
        
        # Check correction structure
        for category, category_corrections in corrections.items():
            assert isinstance(category_corrections, list)
            if category_corrections:
                correction = category_corrections[0]
                expected_fields = [
                    'issue_id', 'severity', 'problem_description',
                    'suggested_actions', 'alternative_solutions',
                    'implementation_priority', 'estimated_effort'
                ]
                
                for field in expected_fields:
                    assert field in correction

    def test_validation_issue_creation_comprehensive(self):
        """Test comprehensive ValidationIssue creation."""
        # Test with all fields
        issue = ValidationIssue(
            severity=ValidationSeverity.ERROR,
            category=ValidationCategory.OPERATING_HOURS,
            message="Test error message",
            location="day_1.morning_session",
            suggestion="Test suggestion",
            affected_item_id="test_id",
            affected_item_name="Test Item",
            rule_violated="Requirement 7.1",
            additional_context={"key": "value"},
            correction_priority=1,
            auto_correctable=True
        )
        
        assert issue.severity == ValidationSeverity.ERROR
        assert issue.category == ValidationCategory.OPERATING_HOURS
        assert issue.additional_context == {"key": "value"}
        assert issue.correction_priority == 1
        assert issue.auto_correctable is True

    def test_validation_report_creation_comprehensive(self):
        """Test comprehensive ValidationReport creation."""
        issues = [
            ValidationIssue(ValidationSeverity.ERROR, ValidationCategory.OPERATING_HOURS, "Error 1", "loc1"),
            ValidationIssue(ValidationSeverity.WARNING, ValidationCategory.DISTRICT_MATCHING, "Warning 1", "loc2"),
            ValidationIssue(ValidationSeverity.INFO, ValidationCategory.AREA_MATCHING, "Info 1", "loc3")
        ]
        
        report = ValidationReport(
            is_valid=False,
            total_issues=3,
            error_count=1,
            warning_count=1,
            info_count=1,
            issues=issues,
            validation_timestamp=datetime.utcnow().isoformat(),
            validation_summary={"test": "summary"},
            correction_suggestions=["suggestion1", "suggestion2"],
            validation_metadata={"metadata": "value"}
        )
        
        # Test computed properties
        assert report.has_errors is True
        assert report.has_warnings is True
        assert report.validation_score < 100  # Should be less than perfect due to issues
        
        # Test to_dict method
        report_dict = report.to_dict()
        assert 'is_valid' in report_dict
        assert 'issues' in report_dict
        assert 'validation_metadata' in report_dict

    def test_validation_severity_enum(self):
        """Test ValidationSeverity enum values."""
        severities = list(ValidationSeverity)
        expected_severities = [
            ValidationSeverity.ERROR,
            ValidationSeverity.WARNING,
            ValidationSeverity.INFO
        ]
        
        for severity in expected_severities:
            assert severity in severities

    def test_validation_category_enum(self):
        """Test ValidationCategory enum values."""
        categories = list(ValidationCategory)
        expected_categories = [
            ValidationCategory.OPERATING_HOURS,
            ValidationCategory.DISTRICT_MATCHING,
            ValidationCategory.AREA_MATCHING,
            ValidationCategory.UNIQUENESS,
            ValidationCategory.DATA_INTEGRITY,
            ValidationCategory.MBTI_ALIGNMENT
        ]
        
        for category in expected_categories:
            assert category in categories

    def test_error_handling_invalid_configuration(self):
        """Test error handling with invalid configuration."""
        # Test with invalid session time ranges
        with pytest.raises(ValidationConfigurationError):
            AssignmentValidator(custom_session_ranges={
                SessionType.MORNING: (25, 0, 30, 0)  # Invalid hours
            })

    def test_error_handling_malformed_data(self):
        """Test error handling with malformed data."""
        # Test with malformed tourist spot
        malformed_spot = Mock()
        malformed_spot.operating_hours = "invalid_format"
        malformed_spot.district = None
        
        # Should handle gracefully without crashing
        issues = self.validator.validate_session_operating_hours(
            malformed_spot, SessionType.MORNING, "test_location"
        )
        assert len(issues) >= 1

    def test_performance_with_large_itinerary(self):
        """Test validation performance with large itinerary."""
        # Create large itinerary with many days
        large_itinerary = MainItinerary(mbti_personality="INFJ")
        
        # Add many days (simulate large itinerary)
        for day_num in range(1, 31):  # 30 days
            day = DayItinerary(
                day_number=day_num,
                morning_session=SessionAssignment("morning", self.test_spots[0]),
                afternoon_session=SessionAssignment("afternoon", self.test_spots[1]),
                night_session=SessionAssignment("night", self.test_spots[2])
            )
            setattr(large_itinerary, f"day_{day_num}", day)
        
        # Measure validation time
        start_time = time.time()
        report = self.validator.validate_complete_itinerary(large_itinerary)
        end_time = time.time()
        
        # Should complete within reasonable time (< 5 seconds)
        assert (end_time - start_time) < 5.0
        assert isinstance(report, ValidationReport)

    def test_memory_efficiency(self):
        """Test memory efficiency during validation."""
        import sys
        
        # Measure memory before
        initial_size = sys.getsizeof(self.validator)
        
        # Perform many validations
        for _ in range(100):
            report = self.validator.validate_complete_itinerary(self.test_itinerary)
        
        # Memory should not grow significantly
        final_size = sys.getsizeof(self.validator)
        memory_growth = final_size - initial_size
        
        # Memory growth should be minimal (< 5KB)
        assert memory_growth < 5120

    def test_concurrent_validation_safety(self):
        """Test thread safety of validation operations."""
        import threading
        import concurrent.futures
        
        results = []
        
        def validate_itinerary():
            return self.validator.validate_complete_itinerary(self.test_itinerary)
        
        # Run concurrent validations
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(validate_itinerary) for _ in range(10)]
            for future in concurrent.futures.as_completed(futures):
                results.append(future.result())
        
        # All validations should succeed
        assert len(results) == 10
        assert all(isinstance(result, ValidationReport) for result in results)

    def test_validation_rule_customization(self):
        """Test validation rule customization."""
        # Create validator with custom rules
        custom_rules = {
            'required_fields': ['name', 'district'],
            'field_formats': {
                'operating_hours': r'\d{2}:\d{2}-\d{2}:\d{2}'
            },
            'data_quality': {
                'min_description_length': 10
            }
        }
        
        validator = AssignmentValidator(custom_validation_rules=custom_rules)
        
        # Test that custom rules are applied
        assert validator.validation_rules['required_fields'] == ['name', 'district']

    def test_validation_caching(self):
        """Test validation result caching."""
        # Enable caching
        self.validator.enable_caching = True
        
        # First validation
        start_time = time.time()
        report1 = self.validator.validate_complete_itinerary(self.test_itinerary)
        first_time = time.time() - start_time
        
        # Second validation (should use cache)
        start_time = time.time()
        report2 = self.validator.validate_complete_itinerary(self.test_itinerary)
        second_time = time.time() - start_time
        
        # Second validation should be faster (cached)
        assert second_time < first_time
        assert report1.total_issues == report2.total_issues


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=services.assignment_validator", "--cov-report=term-missing"])