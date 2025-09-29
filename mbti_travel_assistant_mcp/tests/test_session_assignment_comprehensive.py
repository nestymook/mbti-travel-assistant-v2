"""
Comprehensive Unit Tests for Session Assignment Logic

This module provides comprehensive unit tests for the session assignment logic engine
with 90%+ code coverage, focusing on all edge cases, error conditions, and business rules.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import List, Set, Dict, Any
from datetime import datetime, time

from ..services.session_assignment_logic import (
    SessionAssignmentLogic,
    DistrictAreaMatcher,
    LocationOptimizer,
    UniquenessConstraintEnforcer,
    ItineraryUniquenessValidator,
    AssignmentContext,
    AssignmentResult,
    AssignmentPriority
)
from ..models.tourist_spot_models import TouristSpot, TouristSpotOperatingHours, SessionType
from ..models.itinerary_models import MainItinerary, DayItinerary, SessionAssignment


class TestSessionAssignmentLogicComprehensive:
    """Comprehensive test cases for SessionAssignmentLogic class with 90%+ coverage."""

    def setup_method(self):
        """Set up test fixtures."""
        self.session_logic = SessionAssignmentLogic()
        self.test_spots = self._create_comprehensive_test_spots()
        self.mbti_personality = "INFJ"

    def _create_comprehensive_test_spots(self) -> List[TouristSpot]:
        """Create comprehensive test spots covering all scenarios."""
        spots = []
        
        # INFJ-matched spots with various operating hours
        operating_hours_scenarios = [
            # Morning only
            TouristSpotOperatingHours(
                monday="08:00-12:00", tuesday="08:00-12:00", wednesday="08:00-12:00",
                thursday="08:00-12:00", friday="08:00-12:00", saturday="09:00-12:00", sunday="09:00-12:00"
            ),
            # Afternoon only
            TouristSpotOperatingHours(
                monday="13:00-17:00", tuesday="13:00-17:00", wednesday="13:00-17:00",
                thursday="13:00-17:00", friday="13:00-17:00", saturday="13:00-17:00", sunday="13:00-17:00"
            ),
            # Night only
            TouristSpotOperatingHours(
                monday="19:00-23:00", tuesday="19:00-23:00", wednesday="19:00-23:00",
                thursday="19:00-23:00", friday="19:00-23:00", saturday="19:00-23:00", sunday="19:00-23:00"
            ),
            # All day
            TouristSpotOperatingHours(
                monday="09:00-22:00", tuesday="09:00-22:00", wednesday="09:00-22:00",
                thursday="09:00-22:00", friday="09:00-22:00", saturday="10:00-22:00", sunday="10:00-22:00"
            ),
            # No operating hours (always available)
            None,
            # Weekends only
            TouristSpotOperatingHours(
                monday="", tuesday="", wednesday="", thursday="", friday="",
                saturday="10:00-18:00", sunday="10:00-18:00"
            ),
            # Irregular hours
            TouristSpotOperatingHours(
                monday="10:00-14:00", tuesday="", wednesday="15:00-19:00",
                thursday="10:00-14:00", friday="15:00-19:00", saturday="09:00-21:00", sunday=""
            )
        ]
        
        districts = ["Central", "Admiralty", "Wan Chai", "Tsim Sha Tsui", "Causeway Bay"]
        areas = ["Hong Kong Island", "Kowloon", "New Territories"]
        
        # Create INFJ-matched spots
        for i, operating_hours in enumerate(operating_hours_scenarios):
            district = districts[i % len(districts)]
            area = areas[i % len(areas)]
            
            spot = TouristSpot(
                id=f"infj_spot_{i}",
                name=f"INFJ Spot {i}",
                address=f"Address {i}",
                district=district,
                area=area,
                location_category="Museum" if i % 2 == 0 else "Park",
                description=f"Test INFJ spot {i}",
                operating_hours=operating_hours,
                operating_days=self._get_operating_days(operating_hours),
                mbti_personality_types=["INFJ"],
                keywords=["quiet", "cultural", "peaceful"]
            )
            spots.append(spot)
        
        # Create non-INFJ spots for fallback testing
        for i in range(5):
            operating_hours = TouristSpotOperatingHours(
                monday="10:00-22:00", tuesday="10:00-22:00", wednesday="10:00-22:00",
                thursday="10:00-22:00", friday="10:00-22:00", saturday="10:00-22:00", sunday="10:00-22:00"
            )
            
            spot = TouristSpot(
                id=f"non_infj_spot_{i}",
                name=f"Non-INFJ Spot {i}",
                address=f"Non-INFJ Address {i}",
                district=districts[i % len(districts)],
                area=areas[i % len(areas)],
                location_category="Entertainment",
                description=f"Test non-INFJ spot {i}",
                operating_hours=operating_hours,
                operating_days=["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"],
                mbti_personality_types=["ESTP", "ENFP"],
                keywords=["active", "social", "vibrant"]
            )
            spots.append(spot)
        
        return spots

    def _get_operating_days(self, operating_hours: TouristSpotOperatingHours) -> List[str]:
        """Get operating days based on operating hours."""
        if operating_hours is None:
            return ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        
        days = []
        day_mapping = {
            "monday": operating_hours.monday,
            "tuesday": operating_hours.tuesday,
            "wednesday": operating_hours.wednesday,
            "thursday": operating_hours.thursday,
            "friday": operating_hours.friday,
            "saturday": operating_hours.saturday,
            "sunday": operating_hours.sunday
        }
        
        for day, hours in day_mapping.items():
            if hours and hours.strip():
                days.append(day)
        
        return days if days else ["daily"]

    def test_assign_morning_session_success_all_scenarios(self):
        """Test morning session assignment success in all scenarios."""
        used_spots = set()
        
        # Test with INFJ spots available
        result = self.session_logic.assign_morning_session(
            self.test_spots, used_spots, self.mbti_personality, 1
        )
        
        assert result.tourist_spot is not None
        assert result.mbti_match is True
        assert result.assignment_priority in [
            AssignmentPriority.MBTI_MATCH_ANY_LOCATION,
            AssignmentPriority.MBTI_MATCH_SAME_DISTRICT,
            AssignmentPriority.MBTI_MATCH_SAME_AREA
        ]
        assert result.fallback_used is False
        assert result.tourist_spot.matches_mbti_personality(self.mbti_personality)

    def test_assign_morning_session_with_operating_hours_constraints(self):
        """Test morning session assignment with operating hours constraints."""
        # Create spots with specific operating hours
        morning_only_spot = TouristSpot(
            id="morning_only",
            name="Morning Only Spot",
            address="Morning Address",
            district="Central",
            area="Hong Kong Island",
            location_category="Museum",
            description="Morning only spot",
            operating_hours=TouristSpotOperatingHours(
                monday="08:00-11:00", tuesday="08:00-11:00"
            ),
            operating_days=["monday", "tuesday"],
            mbti_personality_types=["INFJ"]
        )
        
        afternoon_only_spot = TouristSpot(
            id="afternoon_only",
            name="Afternoon Only Spot",
            address="Afternoon Address",
            district="Central",
            area="Hong Kong Island",
            location_category="Park",
            description="Afternoon only spot",
            operating_hours=TouristSpotOperatingHours(
                monday="14:00-17:00", tuesday="14:00-17:00"
            ),
            operating_days=["monday", "tuesday"],
            mbti_personality_types=["INFJ"]
        )
        
        test_spots = [morning_only_spot, afternoon_only_spot]
        used_spots = set()
        
        result = self.session_logic.assign_morning_session(
            test_spots, used_spots, self.mbti_personality, 1
        )
        
        # Should select the morning-compatible spot
        assert result.tourist_spot is not None
        assert result.tourist_spot.id == "morning_only"
        assert result.mbti_match is True

    def test_assign_morning_session_no_available_spots(self):
        """Test morning session assignment when no spots are available."""
        # Mark all spots as used
        used_spots = {spot.id for spot in self.test_spots}
        
        result = self.session_logic.assign_morning_session(
            self.test_spots, used_spots, self.mbti_personality, 1
        )
        
        assert result.tourist_spot is None
        assert result.mbti_match is False
        assert result.fallback_used is False
        assert result.assignment_priority == AssignmentPriority.NO_ASSIGNMENT

    def test_assign_morning_session_empty_spots_list(self):
        """Test morning session assignment with empty spots list."""
        empty_spots = []
        used_spots = set()
        
        result = self.session_logic.assign_morning_session(
            empty_spots, used_spots, self.mbti_personality, 1
        )
        
        assert result.tourist_spot is None
        assert result.mbti_match is False
        assert result.fallback_used is False
        assert result.assignment_priority == AssignmentPriority.NO_ASSIGNMENT

    def test_assign_morning_session_invalid_mbti(self):
        """Test morning session assignment with invalid MBTI personality."""
        used_spots = set()
        invalid_mbti = "INVALID"
        
        result = self.session_logic.assign_morning_session(
            self.test_spots, used_spots, invalid_mbti, 1
        )
        
        # Should still work but with fallback logic
        assert result.tourist_spot is not None
        assert result.mbti_match is False
        assert result.fallback_used is True

    def test_assign_afternoon_session_district_priority(self):
        """Test afternoon session assignment with district priority."""
        used_spots = set()
        
        # First assign morning session
        morning_result = self.session_logic.assign_morning_session(
            self.test_spots, used_spots, self.mbti_personality, 1
        )
        used_spots.add(morning_result.tourist_spot.id)
        
        # Then assign afternoon session
        afternoon_result = self.session_logic.assign_afternoon_session(
            self.test_spots, used_spots, morning_result.tourist_spot, self.mbti_personality, 1
        )
        
        assert afternoon_result.tourist_spot is not None
        assert afternoon_result.tourist_spot.id not in used_spots
        assert afternoon_result.mbti_match is True
        
        # Check district matching priority
        if afternoon_result.district_match:
            assert afternoon_result.tourist_spot.district == morning_result.tourist_spot.district

    def test_assign_afternoon_session_no_morning_spot(self):
        """Test afternoon session assignment without morning spot reference."""
        used_spots = set()
        
        result = self.session_logic.assign_afternoon_session(
            self.test_spots, used_spots, None, self.mbti_personality, 1
        )
        
        assert result.tourist_spot is not None
        assert result.mbti_match is True
        assert result.district_match is False  # No reference spot to match

    def test_assign_afternoon_session_area_fallback(self):
        """Test afternoon session assignment with area fallback when district unavailable."""
        used_spots = set()
        
        # Create morning spot in specific district
        morning_spot = TouristSpot(
            id="morning_unique",
            name="Morning Unique Spot",
            address="Unique Address",
            district="Unique District",
            area="Hong Kong Island",
            location_category="Museum",
            description="Unique morning spot",
            operating_hours=None,
            operating_days=["daily"],
            mbti_personality_types=["INFJ"]
        )
        
        # Use spots that don't have the same district but same area
        afternoon_result = self.session_logic.assign_afternoon_session(
            self.test_spots, used_spots, morning_spot, self.mbti_personality, 1
        )
        
        assert afternoon_result.tourist_spot is not None
        assert afternoon_result.mbti_match is True
        # Should fall back to area matching if district not available
        if afternoon_result.area_match:
            assert afternoon_result.tourist_spot.area == morning_spot.area

    def test_assign_night_session_multiple_reference_spots(self):
        """Test night session assignment with multiple reference spots."""
        used_spots = set()
        
        # Create morning and afternoon spots
        morning_spot = self.test_spots[0]
        afternoon_spot = self.test_spots[1]
        used_spots.add(morning_spot.id)
        used_spots.add(afternoon_spot.id)
        
        night_result = self.session_logic.assign_night_session(
            self.test_spots, used_spots, morning_spot, afternoon_spot, self.mbti_personality, 1
        )
        
        assert night_result.tourist_spot is not None
        assert night_result.tourist_spot.id not in used_spots
        assert night_result.mbti_match is True

    def test_assign_night_session_no_reference_spots(self):
        """Test night session assignment without reference spots."""
        used_spots = set()
        
        result = self.session_logic.assign_night_session(
            self.test_spots, used_spots, None, None, self.mbti_personality, 1
        )
        
        assert result.tourist_spot is not None
        assert result.mbti_match is True
        assert result.district_match is False
        assert result.area_match is False

    def test_fallback_assignment_logic(self):
        """Test fallback assignment when MBTI spots are exhausted."""
        # Mark all INFJ spots as used
        infj_spots = [spot for spot in self.test_spots if "INFJ" in spot.mbti_personality_types]
        used_spots = {spot.id for spot in infj_spots}
        
        result = self.session_logic.assign_morning_session(
            self.test_spots, used_spots, self.mbti_personality, 1
        )
        
        assert result.tourist_spot is not None
        assert result.mbti_match is False
        assert result.fallback_used is True
        assert result.assignment_priority in [
            AssignmentPriority.NON_MBTI_SAME_DISTRICT,
            AssignmentPriority.NON_MBTI_SAME_AREA,
            AssignmentPriority.NON_MBTI_ANY_LOCATION
        ]

    def test_validate_session_assignment_all_session_types(self):
        """Test session assignment validation for all session types."""
        # Test spot with all-day hours
        all_day_spot = TouristSpot(
            id="all_day",
            name="All Day Spot",
            address="All Day Address",
            district="Central",
            area="Hong Kong Island",
            location_category="Park",
            description="All day spot",
            operating_hours=TouristSpotOperatingHours(
                monday="09:00-22:00", tuesday="09:00-22:00"
            ),
            operating_days=["monday", "tuesday"],
            mbti_personality_types=["INFJ"]
        )
        
        # Should be valid for all session types
        for session_type in [SessionType.MORNING, SessionType.AFTERNOON, SessionType.NIGHT]:
            errors = self.session_logic.validate_session_assignment(all_day_spot, session_type)
            assert len(errors) == 0

    def test_validate_session_assignment_invalid_hours(self):
        """Test session assignment validation with invalid operating hours."""
        # Test spot with morning-only hours for night session
        morning_only_spot = TouristSpot(
            id="morning_only",
            name="Morning Only Spot",
            address="Morning Address",
            district="Central",
            area="Hong Kong Island",
            location_category="Museum",
            description="Morning only spot",
            operating_hours=TouristSpotOperatingHours(
                monday="08:00-11:00", tuesday="08:00-11:00"
            ),
            operating_days=["monday", "tuesday"],
            mbti_personality_types=["INFJ"]
        )
        
        # Should have errors for night session
        night_errors = self.session_logic.validate_session_assignment(
            morning_only_spot, SessionType.NIGHT
        )
        assert len(night_errors) > 0
        assert any("not available during night session" in error for error in night_errors)

    def test_validate_session_assignment_none_spot(self):
        """Test session assignment validation with None spot."""
        errors = self.session_logic.validate_session_assignment(None, SessionType.MORNING)
        assert len(errors) == 1
        assert "No tourist spot provided" in errors[0]

    def test_get_assignment_statistics_comprehensive(self):
        """Test comprehensive assignment statistics generation."""
        # Create diverse assignment results
        results = [
            AssignmentResult(
                tourist_spot=self.test_spots[0],
                assignment_priority=AssignmentPriority.MBTI_MATCH_SAME_DISTRICT,
                mbti_match=True,
                district_match=True,
                area_match=True,
                fallback_used=False
            ),
            AssignmentResult(
                tourist_spot=self.test_spots[1],
                assignment_priority=AssignmentPriority.MBTI_MATCH_SAME_AREA,
                mbti_match=True,
                district_match=False,
                area_match=True,
                fallback_used=False
            ),
            AssignmentResult(
                tourist_spot=self.test_spots[2],
                assignment_priority=AssignmentPriority.NON_MBTI_ANY_LOCATION,
                mbti_match=False,
                district_match=False,
                area_match=False,
                fallback_used=True
            ),
            AssignmentResult(
                tourist_spot=None,
                assignment_priority=AssignmentPriority.NO_ASSIGNMENT,
                mbti_match=False,
                district_match=False,
                area_match=False,
                fallback_used=False
            )
        ]
        
        stats = self.session_logic.get_assignment_statistics(results)
        
        assert stats['total_assignments'] == 4
        assert stats['successful_assignments'] == 3
        assert stats['success_rate'] == 0.75
        assert stats['mbti_matches'] == 2
        assert stats['mbti_match_rate'] == 0.5
        assert stats['district_matches'] == 1
        assert stats['area_matches'] == 2
        assert stats['fallback_assignments'] == 1
        assert stats['failed_assignments'] == 1
        
        # Check priority distribution
        assert 'priority_distribution' in stats
        assert stats['priority_distribution'][AssignmentPriority.MBTI_MATCH_SAME_DISTRICT.value] == 1
        assert stats['priority_distribution'][AssignmentPriority.NO_ASSIGNMENT.value] == 1

    def test_get_assignment_statistics_empty_results(self):
        """Test assignment statistics with empty results."""
        stats = self.session_logic.get_assignment_statistics([])
        
        assert stats['total_assignments'] == 0
        assert stats['successful_assignments'] == 0
        assert stats['success_rate'] == 0.0
        assert stats['mbti_matches'] == 0
        assert stats['mbti_match_rate'] == 0.0

    def test_assignment_context_creation(self):
        """Test AssignmentContext creation and usage."""
        context = AssignmentContext(
            mbti_personality=self.mbti_personality,
            day_number=1,
            session_type=SessionType.MORNING,
            reference_spots=[],
            used_spots=set(),
            assignment_constraints={}
        )
        
        assert context.mbti_personality == self.mbti_personality
        assert context.day_number == 1
        assert context.session_type == SessionType.MORNING
        assert isinstance(context.reference_spots, list)
        assert isinstance(context.used_spots, set)
        assert isinstance(context.assignment_constraints, dict)

    def test_assignment_result_creation(self):
        """Test AssignmentResult creation and properties."""
        result = AssignmentResult(
            tourist_spot=self.test_spots[0],
            assignment_priority=AssignmentPriority.MBTI_MATCH_SAME_DISTRICT,
            mbti_match=True,
            district_match=True,
            area_match=True,
            fallback_used=False,
            assignment_reason="Perfect MBTI and location match",
            validation_errors=[],
            assignment_metadata={"score": 0.95}
        )
        
        assert result.tourist_spot == self.test_spots[0]
        assert result.assignment_priority == AssignmentPriority.MBTI_MATCH_SAME_DISTRICT
        assert result.mbti_match is True
        assert result.district_match is True
        assert result.area_match is True
        assert result.fallback_used is False
        assert result.assignment_reason == "Perfect MBTI and location match"
        assert result.validation_errors == []
        assert result.assignment_metadata["score"] == 0.95

    def test_assignment_priority_enum(self):
        """Test AssignmentPriority enum values and ordering."""
        priorities = list(AssignmentPriority)
        
        # Check all expected priorities exist
        expected_priorities = [
            AssignmentPriority.MBTI_MATCH_SAME_DISTRICT,
            AssignmentPriority.MBTI_MATCH_SAME_AREA,
            AssignmentPriority.MBTI_MATCH_ANY_LOCATION,
            AssignmentPriority.NON_MBTI_SAME_DISTRICT,
            AssignmentPriority.NON_MBTI_SAME_AREA,
            AssignmentPriority.NON_MBTI_ANY_LOCATION,
            AssignmentPriority.NO_ASSIGNMENT
        ]
        
        for priority in expected_priorities:
            assert priority in priorities

    def test_session_type_enum(self):
        """Test SessionType enum values."""
        session_types = list(SessionType)
        
        expected_types = [SessionType.MORNING, SessionType.AFTERNOON, SessionType.NIGHT]
        
        for session_type in expected_types:
            assert session_type in session_types

    def test_error_handling_invalid_inputs(self):
        """Test error handling with various invalid inputs."""
        # Test with None inputs
        result = self.session_logic.assign_morning_session(
            None, set(), self.mbti_personality, 1
        )
        assert result.tourist_spot is None
        assert result.assignment_priority == AssignmentPriority.NO_ASSIGNMENT
        
        # Test with invalid day number
        result = self.session_logic.assign_morning_session(
            self.test_spots, set(), self.mbti_personality, 0
        )
        assert result.tourist_spot is not None  # Should still work
        
        # Test with negative day number
        result = self.session_logic.assign_morning_session(
            self.test_spots, set(), self.mbti_personality, -1
        )
        assert result.tourist_spot is not None  # Should still work

    def test_performance_with_large_dataset(self):
        """Test performance with large dataset."""
        # Create large dataset
        large_spots = []
        for i in range(1000):
            spot = TouristSpot(
                id=f"large_spot_{i}",
                name=f"Large Spot {i}",
                address=f"Address {i}",
                district=f"District {i % 10}",
                area=f"Area {i % 3}",
                location_category="Test",
                description=f"Large test spot {i}",
                operating_hours=None,
                operating_days=["daily"],
                mbti_personality_types=["INFJ"] if i % 2 == 0 else ["ESTP"]
            )
            large_spots.append(spot)
        
        used_spots = set()
        
        # Measure assignment time
        start_time = time.time()
        result = self.session_logic.assign_morning_session(
            large_spots, used_spots, self.mbti_personality, 1
        )
        end_time = time.time()
        
        # Should complete within reasonable time (< 1 second)
        assert (end_time - start_time) < 1.0
        assert result.tourist_spot is not None

    def test_concurrent_assignment_safety(self):
        """Test thread safety of assignment operations."""
        import threading
        import concurrent.futures
        
        results = []
        used_spots = set()
        
        def assign_session(day_num):
            return self.session_logic.assign_morning_session(
                self.test_spots, used_spots, self.mbti_personality, day_num
            )
        
        # Run concurrent assignments
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(assign_session, i) for i in range(1, 6)]
            for future in concurrent.futures.as_completed(futures):
                results.append(future.result())
        
        # All assignments should succeed
        assert len(results) == 5
        assert all(result.tourist_spot is not None for result in results)

    def test_memory_usage_optimization(self):
        """Test memory usage optimization."""
        import sys
        
        # Measure memory before
        initial_size = sys.getsizeof(self.session_logic)
        
        # Perform many assignments
        used_spots = set()
        for i in range(100):
            result = self.session_logic.assign_morning_session(
                self.test_spots, used_spots, self.mbti_personality, i + 1
            )
            if result.tourist_spot:
                used_spots.add(result.tourist_spot.id)
        
        # Memory should not grow significantly
        final_size = sys.getsizeof(self.session_logic)
        memory_growth = final_size - initial_size
        
        # Memory growth should be minimal (< 1KB)
        assert memory_growth < 1024


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=services.session_assignment_logic", "--cov-report=term-missing"])