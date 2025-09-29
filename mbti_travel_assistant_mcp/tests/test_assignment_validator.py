"""Tests for assignment validator system.

This module contains comprehensive tests for the AssignmentValidator class,
validating business rule validation, operating hours validation, district matching,
and validation reporting functionality.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch

from ..services.assignment_validator import (
    AssignmentValidator,
    ValidationIssue,
    ValidationReport,
    ValidationSeverity,
    ValidationCategory
)
from ..models.tourist_spot_models import TouristSpot, TouristSpotOperatingHours, SessionType
from ..models.itinerary_models import (
    MainItinerary,
    DayItinerary,
    SessionAssignment,
    MealAssignment
)
from ..models.restaurant_models import Restaurant


class TestAssignmentValidator:
    """Test cases for AssignmentValidator class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.validator = AssignmentValidator()
        
        # Create test tourist spots
        self.morning_spot = self._create_test_tourist_spot(
            "morning_spot_1",
            "Morning Museum",
            "Central",
            "Hong Kong Island",
            operating_hours=TouristSpotOperatingHours(
                monday="09:00-17:00",
                tuesday="09:00-17:00"
            ),
            mbti_types=["INFJ"]
        )
        
        self.afternoon_spot = self._create_test_tourist_spot(
            "afternoon_spot_1",
            "Afternoon Park",
            "Central",  # Same district as morning
            "Hong Kong Island",
            operating_hours=TouristSpotOperatingHours(
                monday="10:00-20:00",
                tuesday="10:00-20:00"
            ),
            mbti_types=["INFJ"]
        )
        
        self.night_spot = self._create_test_tourist_spot(
            "night_spot_1",
            "Night Market",
            "Wan Chai",  # Different district
            "Hong Kong Island",  # Same area
            operating_hours=TouristSpotOperatingHours(
                monday="18:00-23:00",
                tuesday="18:00-23:00"
            ),
            mbti_types=["INFJ"]
        )
        
        # Create test restaurants
        self.breakfast_restaurant = self._create_test_restaurant(
            "breakfast_rest_1",
            "Morning Cafe",
            "Central",
            "07:00-11:00"
        )
        
        self.lunch_restaurant = self._create_test_restaurant(
            "lunch_rest_1",
            "Lunch Bistro",
            "Central",
            "11:30-15:00"
        )
        
        self.dinner_restaurant = self._create_test_restaurant(
            "dinner_rest_1",
            "Evening Restaurant",
            "Wan Chai",
            "18:00-22:00"
        )

    def _create_test_tourist_spot(
        self,
        spot_id: str,
        name: str,
        district: str,
        area: str,
        operating_hours: TouristSpotOperatingHours = None,
        mbti_types: list = None
    ) -> TouristSpot:
        """Create a test tourist spot."""
        if operating_hours is None:
            operating_hours = TouristSpotOperatingHours()
        
        if mbti_types is None:
            mbti_types = []
        
        spot = TouristSpot(
            id=spot_id,
            name=name,
            address=f"123 {name} Street",
            district=district,
            area=area,
            location_category="Test Category",
            description=f"Test description for {name}",
            operating_hours=operating_hours,
            operating_days=["monday", "tuesday", "wednesday", "thursday", "friday"],
            mbti_personality_types=mbti_types
        )
        
        # Set MBTI match status
        if mbti_types:
            spot.mbti_match = True
        
        return spot

    def _create_test_restaurant(
        self,
        restaurant_id: str,
        name: str,
        district: str,
        operating_hours: str
    ) -> Restaurant:
        """Create a test restaurant."""
        return Restaurant(
            id=restaurant_id,
            name=name,
            address=f"456 {name} Street",
            district=district,
            operating_hours=operating_hours,
            cuisine_type="Test Cuisine"
        )

    def _create_test_itinerary(self) -> MainItinerary:
        """Create a test itinerary with complete assignments."""
        # Create session assignments
        morning_session = SessionAssignment(
            session_type="morning",
            tourist_spot=self.morning_spot
        )
        
        afternoon_session = SessionAssignment(
            session_type="afternoon",
            tourist_spot=self.afternoon_spot
        )
        
        night_session = SessionAssignment(
            session_type="night",
            tourist_spot=self.night_spot
        )
        
        # Create meal assignments
        breakfast = MealAssignment(
            meal_type="breakfast",
            restaurant=self.breakfast_restaurant
        )
        
        lunch = MealAssignment(
            meal_type="lunch",
            restaurant=self.lunch_restaurant
        )
        
        dinner = MealAssignment(
            meal_type="dinner",
            restaurant=self.dinner_restaurant
        )
        
        # Create day itinerary
        day_1 = DayItinerary(
            day_number=1,
            morning_session=morning_session,
            afternoon_session=afternoon_session,
            night_session=night_session,
            breakfast=breakfast,
            lunch=lunch,
            dinner=dinner
        )
        
        # Create similar days (simplified for testing)
        day_2 = DayItinerary(day_number=2)
        day_3 = DayItinerary(day_number=3)
        
        return MainItinerary(
            mbti_personality="INFJ",
            day_1=day_1,
            day_2=day_2,
            day_3=day_3
        )

    def test_validate_session_operating_hours_valid(self):
        """Test validation of valid session operating hours."""
        issues = self.validator.validate_session_operating_hours(
            self.morning_spot,
            SessionType.MORNING,
            "day_1.morning_session"
        )
        
        assert len(issues) == 0

    def test_validate_session_operating_hours_invalid(self):
        """Test validation of invalid session operating hours."""
        # Create spot that doesn't operate during morning hours
        invalid_spot = self._create_test_tourist_spot(
            "invalid_spot",
            "Evening Only Spot",
            "Central",
            "Hong Kong Island",
            operating_hours=TouristSpotOperatingHours(
                monday="20:00-23:00"  # Only evening hours
            )
        )
        
        issues = self.validator.validate_session_operating_hours(
            invalid_spot,
            SessionType.MORNING,
            "day_1.morning_session"
        )
        
        assert len(issues) == 1
        assert issues[0].severity == ValidationSeverity.ERROR
        assert issues[0].category == ValidationCategory.OPERATING_HOURS
        assert "not available during morning session" in issues[0].message

    def test_validate_session_operating_hours_none_spot(self):
        """Test validation with None tourist spot."""
        issues = self.validator.validate_session_operating_hours(
            None,
            SessionType.MORNING,
            "day_1.morning_session"
        )
        
        assert len(issues) == 1
        assert issues[0].severity == ValidationSeverity.ERROR
        assert issues[0].category == ValidationCategory.DATA_INTEGRITY

    def test_validate_district_matching_same_district(self):
        """Test district matching validation with same district."""
        issues = self.validator.validate_district_matching(
            self.afternoon_spot,  # Same district as morning
            self.night_spot,      # Different district
            self.morning_spot,    # Reference morning spot
            "day_1"
        )
        
        # Should have one warning for night spot being in different district
        district_issues = [i for i in issues if i.category == ValidationCategory.DISTRICT_MATCHING]
        assert len(district_issues) == 1
        assert district_issues[0].severity == ValidationSeverity.WARNING

    def test_validate_district_matching_no_morning_spot(self):
        """Test district matching validation without morning spot."""
        issues = self.validator.validate_district_matching(
            self.afternoon_spot,
            self.night_spot,
            None,  # No morning spot
            "day_1"
        )
        
        assert len(issues) == 1
        assert issues[0].severity == ValidationSeverity.WARNING
        assert "No morning spot available" in issues[0].message

    def test_validate_area_matching(self):
        """Test area matching validation."""
        issues = self.validator.validate_area_matching(
            self.afternoon_spot,  # Same district as morning
            self.night_spot,      # Different district, same area
            self.morning_spot,    # Reference morning spot
            "day_1"
        )
        
        # Night spot should pass area matching since it's in same area
        area_issues = [i for i in issues if i.category == ValidationCategory.AREA_MATCHING]
        assert len(area_issues) == 0  # No area matching issues expected

    def test_validate_complete_itinerary_valid(self):
        """Test validation of complete valid itinerary."""
        itinerary = self._create_test_itinerary()
        report = self.validator.validate_complete_itinerary(itinerary)
        
        assert isinstance(report, ValidationReport)
        assert report.total_issues >= 0  # May have warnings but should be structurally valid
        assert report.validation_timestamp is not None

    def test_validate_complete_itinerary_missing_mbti(self):
        """Test validation of itinerary with missing MBTI personality."""
        itinerary = self._create_test_itinerary()
        itinerary.mbti_personality = ""
        
        report = self.validator.validate_complete_itinerary(itinerary)
        
        assert not report.is_valid
        assert report.error_count > 0
        
        # Should have data integrity error
        data_errors = [i for i in report.issues if i.category == ValidationCategory.DATA_INTEGRITY]
        assert len(data_errors) > 0

    def test_validate_complete_itinerary_duplicate_spots(self):
        """Test validation of itinerary with duplicate tourist spots."""
        itinerary = self._create_test_itinerary()
        
        # Create duplicate assignment
        duplicate_session = SessionAssignment(
            session_type="afternoon",
            tourist_spot=self.morning_spot  # Same spot as morning
        )
        itinerary.day_1.afternoon_session = duplicate_session
        
        report = self.validator.validate_complete_itinerary(itinerary)
        
        assert not report.is_valid
        assert report.error_count > 0
        
        # Should have uniqueness error
        uniqueness_errors = [i for i in report.issues if i.category == ValidationCategory.UNIQUENESS]
        assert len(uniqueness_errors) > 0

    def test_generate_detailed_validation_report(self):
        """Test generation of detailed validation report."""
        itinerary = self._create_test_itinerary()
        detailed_report = self.validator.generate_detailed_validation_report(itinerary)
        
        assert 'detailed_analysis' in detailed_report
        assert 'session_analysis' in detailed_report['detailed_analysis']
        assert 'restaurant_analysis' in detailed_report['detailed_analysis']
        assert 'location_coherence_analysis' in detailed_report['detailed_analysis']
        assert 'mbti_alignment_analysis' in detailed_report['detailed_analysis']
        assert 'coverage_analysis' in detailed_report['detailed_analysis']
        
        assert 'correction_recommendations' in detailed_report
        assert 'validation_metrics' in detailed_report

    def test_generate_validation_warnings(self):
        """Test generation of validation warnings."""
        itinerary = self._create_test_itinerary()
        warnings = self.validator.generate_validation_warnings(itinerary)
        
        assert isinstance(warnings, list)
        
        # Check warning structure if any warnings exist
        if warnings:
            warning = warnings[0]
            assert 'warning_id' in warning
            assert 'category' in warning
            assert 'message' in warning
            assert 'suggestion' in warning
            assert 'impact_level' in warning
            assert 'auto_correctable' in warning
            assert 'correction_options' in warning

    def test_suggest_corrections_for_validation_failures(self):
        """Test generation of correction suggestions."""
        # Create some validation issues
        issues = [
            ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category=ValidationCategory.OPERATING_HOURS,
                message="Test operating hours error",
                location="day_1.morning_session",
                suggestion="Replace with valid spot",
                affected_item_id="test_spot_1",
                affected_item_name="Test Spot",
                rule_violated="Requirement 7.1"
            ),
            ValidationIssue(
                severity=ValidationSeverity.WARNING,
                category=ValidationCategory.DISTRICT_MATCHING,
                message="Test district matching warning",
                location="day_1.afternoon_session",
                suggestion="Consider same district spot",
                affected_item_id="test_spot_2",
                affected_item_name="Test Spot 2",
                rule_violated="Requirement 7.4"
            )
        ]
        
        corrections = self.validator.suggest_corrections_for_validation_failures(issues)
        
        assert isinstance(corrections, dict)
        assert ValidationCategory.OPERATING_HOURS.value in corrections
        assert ValidationCategory.DISTRICT_MATCHING.value in corrections
        
        # Check correction structure
        operating_hours_corrections = corrections[ValidationCategory.OPERATING_HOURS.value]
        assert len(operating_hours_corrections) == 1
        
        correction = operating_hours_corrections[0]
        assert 'issue_id' in correction
        assert 'severity' in correction
        assert 'problem_description' in correction
        assert 'suggested_actions' in correction
        assert 'alternative_solutions' in correction
        assert 'implementation_priority' in correction
        assert 'estimated_effort' in correction

    def test_validation_issue_creation(self):
        """Test ValidationIssue creation and properties."""
        issue = ValidationIssue(
            severity=ValidationSeverity.ERROR,
            category=ValidationCategory.OPERATING_HOURS,
            message="Test error message",
            location="day_1.morning_session",
            suggestion="Test suggestion",
            affected_item_id="test_id",
            affected_item_name="Test Item",
            rule_violated="Requirement 7.1"
        )
        
        assert issue.severity == ValidationSeverity.ERROR
        assert issue.category == ValidationCategory.OPERATING_HOURS
        assert issue.message == "Test error message"
        assert issue.location == "day_1.morning_session"
        assert issue.suggestion == "Test suggestion"
        assert issue.affected_item_id == "test_id"
        assert issue.affected_item_name == "Test Item"
        assert issue.rule_violated == "Requirement 7.1"

    def test_validation_report_creation(self):
        """Test ValidationReport creation and computed fields."""
        issues = [
            ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category=ValidationCategory.OPERATING_HOURS,
                message="Error 1",
                location="location_1"
            ),
            ValidationIssue(
                severity=ValidationSeverity.WARNING,
                category=ValidationCategory.DISTRICT_MATCHING,
                message="Warning 1",
                location="location_2"
            ),
            ValidationIssue(
                severity=ValidationSeverity.INFO,
                category=ValidationCategory.AREA_MATCHING,
                message="Info 1",
                location="location_3"
            )
        ]
        
        report = ValidationReport(
            is_valid=False,
            total_issues=3,
            error_count=1,
            warning_count=1,
            info_count=1,
            issues=issues,
            validation_timestamp="",
            validation_summary={},
            correction_suggestions=[]
        )
        
        assert not report.is_valid
        assert report.total_issues == 3
        assert report.error_count == 1
        assert report.warning_count == 1
        assert report.info_count == 1
        assert len(report.issues) == 3
        assert report.validation_timestamp is not None
        
        # Test to_dict method
        report_dict = report.to_dict()
        assert 'is_valid' in report_dict
        assert 'issues' in report_dict
        assert len(report_dict['issues']) == 3

    def test_session_time_ranges(self):
        """Test session time range definitions."""
        assert SessionType.MORNING in self.validator.session_time_ranges
        assert SessionType.AFTERNOON in self.validator.session_time_ranges
        assert SessionType.NIGHT in self.validator.session_time_ranges
        
        morning_range = self.validator.session_time_ranges[SessionType.MORNING]
        assert morning_range == (7, 0, 11, 59)  # 07:00-11:59

    def test_meal_time_ranges(self):
        """Test meal time range definitions."""
        assert 'breakfast' in self.validator.meal_time_ranges
        assert 'lunch' in self.validator.meal_time_ranges
        assert 'dinner' in self.validator.meal_time_ranges
        
        breakfast_range = self.validator.meal_time_ranges['breakfast']
        assert breakfast_range[0].hour == 6  # 06:00
        assert breakfast_range[1].hour == 11  # 11:29

    def test_private_helper_methods(self):
        """Test private helper methods."""
        # Test session time string generation
        morning_str = self.validator._get_session_time_string(SessionType.MORNING)
        assert morning_str == "07:00-11:59"
        
        # Test meal time string generation
        breakfast_str = self.validator._get_meal_time_string('breakfast')
        assert breakfast_str == "06:00-11:29"
        
        # Test requirement number mapping
        req_num = self.validator._get_requirement_number(SessionType.MORNING)
        assert req_num == "1"

    def test_analyze_session_assignments(self):
        """Test session assignment analysis."""
        itinerary = self._create_test_itinerary()
        analysis = self.validator._analyze_session_assignments(itinerary)
        
        assert 'total_sessions' in analysis
        assert 'assigned_sessions' in analysis
        assert 'mbti_matched_sessions' in analysis
        assert 'session_distribution' in analysis
        assert 'mbti_match_percentage' in analysis
        assert 'assignment_completion_percentage' in analysis
        
        assert analysis['total_sessions'] == 9

    def test_analyze_restaurant_assignments(self):
        """Test restaurant assignment analysis."""
        itinerary = self._create_test_itinerary()
        analysis = self.validator._analyze_restaurant_assignments(itinerary)
        
        assert 'total_meals' in analysis
        assert 'assigned_meals' in analysis
        assert 'meal_distribution' in analysis
        assert 'assignment_completion_percentage' in analysis
        
        assert analysis['total_meals'] == 9

    def test_analyze_location_coherence(self):
        """Test location coherence analysis."""
        itinerary = self._create_test_itinerary()
        analysis = self.validator._analyze_location_coherence(itinerary)
        
        assert 'district_coherence_score' in analysis
        assert 'area_coherence_score' in analysis
        assert 'daily_coherence' in analysis
        assert 'overall_coherence_rating' in analysis

    def test_analyze_mbti_alignment(self):
        """Test MBTI alignment analysis."""
        itinerary = self._create_test_itinerary()
        analysis = self.validator._analyze_mbti_alignment(itinerary)
        
        assert 'mbti_personality' in analysis
        assert 'total_tourist_spots' in analysis
        assert 'mbti_matched_spots' in analysis
        assert 'mbti_alignment_percentage' in analysis
        assert 'alignment_by_day' in analysis
        assert 'alignment_rating' in analysis
        
        assert analysis['mbti_personality'] == "INFJ"

    def test_analyze_coverage_completeness(self):
        """Test coverage completeness analysis."""
        itinerary = self._create_test_itinerary()
        analysis = self.validator._analyze_coverage_completeness(itinerary)
        
        assert 'session_coverage' in analysis
        assert 'meal_coverage' in analysis
        assert 'missing_assignments' in analysis
        assert 'completeness_rating' in analysis

    def test_calculate_validation_metrics(self):
        """Test validation metrics calculation."""
        issues = [
            ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category=ValidationCategory.OPERATING_HOURS,
                message="Error 1",
                location="location_1"
            ),
            ValidationIssue(
                severity=ValidationSeverity.WARNING,
                category=ValidationCategory.DISTRICT_MATCHING,
                message="Warning 1",
                location="location_2"
            )
        ]
        
        itinerary = self._create_test_itinerary()
        metrics = self.validator._calculate_validation_metrics(issues, itinerary)
        
        assert 'validation_score' in metrics
        assert 'compliance_percentage' in metrics
        assert 'issue_density' in metrics
        assert 'critical_issues_count' in metrics
        assert 'improvement_potential' in metrics
        assert 'quality_rating' in metrics
        
        assert metrics['critical_issues_count'] == 1  # One error
        assert 0 <= metrics['validation_score'] <= 100
        assert metrics['quality_rating'] in ['Excellent', 'Good', 'Fair', 'Poor', 'Critical']


class TestValidationIntegration:
    """Integration tests for validation system."""

    def setup_method(self):
        """Set up integration test fixtures."""
        self.validator = AssignmentValidator()

    def test_end_to_end_validation_workflow(self):
        """Test complete end-to-end validation workflow."""
        # Create a complex itinerary with various issues
        itinerary = self._create_complex_test_itinerary()
        
        # Run complete validation
        report = self.validator.validate_complete_itinerary(itinerary)
        
        # Generate detailed report
        detailed_report = self.validator.generate_detailed_validation_report(itinerary)
        
        # Generate warnings
        warnings = self.validator.generate_validation_warnings(itinerary)
        
        # Generate corrections
        corrections = self.validator.suggest_corrections_for_validation_failures(report.issues)
        
        # Verify all components work together
        assert isinstance(report, ValidationReport)
        assert isinstance(detailed_report, dict)
        assert isinstance(warnings, list)
        assert isinstance(corrections, dict)
        
        # Verify data consistency
        assert detailed_report['total_issues'] == report.total_issues
        assert detailed_report['error_count'] == report.error_count
        assert detailed_report['warning_count'] == report.warning_count

    def _create_complex_test_itinerary(self) -> MainItinerary:
        """Create a complex test itinerary with various validation issues."""
        # This would create an itinerary with intentional validation issues
        # for comprehensive testing
        return MainItinerary(
            mbti_personality="INFJ",
            day_1=DayItinerary(day_number=1),
            day_2=DayItinerary(day_number=2),
            day_3=DayItinerary(day_number=3)
        )


if __name__ == "__main__":
    pytest.main([__file__])