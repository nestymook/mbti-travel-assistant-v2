"""Unit tests for TimeService class.

Tests time parsing, validation, meal type calculations, and edge cases
including midnight crossover and multiple time ranges.
Follows PEP8 style guidelines and comprehensive test coverage.
"""

import unittest
from datetime import time
from services.time_service import TimeService
from models.restaurant_models import OperatingHours


class TestTimeService(unittest.TestCase):
    """Test cases for TimeService functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.time_service = TimeService()
    
    def test_parse_time_range_valid_formats(self):
        """Test parsing of valid time range formats."""
        test_cases = [
            ("11:30 - 15:30", (time(11, 30), time(15, 30))),
            ("07:00-11:29", (time(7, 0), time(11, 29))),
            ("18:00 - 22:30", (time(18, 0), time(22, 30))),
            ("09:15 - 10:45", (time(9, 15), time(10, 45))),
            ("00:00 - 23:59", (time(0, 0), time(23, 59))),
            ("12:00-12:30", (time(12, 0), time(12, 30))),
        ]
        
        for time_range_str, expected in test_cases:
            with self.subTest(time_range=time_range_str):
                result = self.time_service.parse_time_range(time_range_str)
                self.assertEqual(result, expected)
    
    def test_parse_time_range_invalid_formats(self):
        """Test parsing of invalid time range formats."""
        invalid_cases = [
            "",
            None,
            "invalid",
            "25:00 - 15:30",  # Invalid hour
            "11:60 - 15:30",  # Invalid minute
            "11:30 - 25:30",  # Invalid end hour
            "11:30 - 15:60",  # Invalid end minute
            "11:30",          # Missing end time
            "11:30 -",        # Missing end time
            "- 15:30",        # Missing start time
            "11:30 15:30",    # Missing separator
            "11.30 - 15.30",  # Wrong separator
        ]
        
        for invalid_range in invalid_cases:
            with self.subTest(time_range=invalid_range):
                result = self.time_service.parse_time_range(invalid_range)
                self.assertIsNone(result)
    
    def test_check_time_overlap_normal_ranges(self):
        """Test time overlap detection for normal ranges (no midnight crossover)."""
        # Overlapping ranges
        overlapping_cases = [
            ((time(11, 0), time(15, 0)), (time(14, 0), time(18, 0))),  # Partial overlap
            ((time(11, 0), time(15, 0)), (time(11, 0), time(15, 0))),  # Exact match
            ((time(11, 0), time(15, 0)), (time(12, 0), time(14, 0))),  # Contained
            ((time(12, 0), time(14, 0)), (time(11, 0), time(15, 0))),  # Contains
            ((time(11, 0), time(15, 0)), (time(15, 0), time(18, 0))),  # Adjacent (touching)
        ]
        
        for range1, range2 in overlapping_cases:
            with self.subTest(range1=range1, range2=range2):
                self.assertTrue(self.time_service.check_time_overlap(range1, range2))
                # Test symmetry
                self.assertTrue(self.time_service.check_time_overlap(range2, range1))
        
        # Non-overlapping ranges
        non_overlapping_cases = [
            ((time(11, 0), time(14, 0)), (time(15, 0), time(18, 0))),  # Gap between
            ((time(7, 0), time(11, 0)), (time(12, 0), time(15, 0))),   # Morning vs afternoon
        ]
        
        for range1, range2 in non_overlapping_cases:
            with self.subTest(range1=range1, range2=range2):
                self.assertFalse(self.time_service.check_time_overlap(range1, range2))
                # Test symmetry
                self.assertFalse(self.time_service.check_time_overlap(range2, range1))
    
    def test_check_time_overlap_midnight_crossover(self):
        """Test time overlap detection with midnight crossover scenarios."""
        # Range crossing midnight
        midnight_range = (time(22, 0), time(2, 0))  # 22:00 - 02:00
        
        # Overlapping with midnight crossover
        overlapping_cases = [
            (midnight_range, (time(23, 0), time(23, 30))),  # Late night overlap
            (midnight_range, (time(1, 0), time(3, 0))),     # Early morning overlap
            (midnight_range, (time(21, 0), time(23, 0))),   # Before midnight overlap
            (midnight_range, (time(0, 0), time(4, 0))),     # After midnight overlap
            (midnight_range, (time(21, 0), time(3, 0))),    # Spans entire range
        ]
        
        for range1, range2 in overlapping_cases:
            with self.subTest(range1=range1, range2=range2):
                self.assertTrue(self.time_service.check_time_overlap(range1, range2))
                # Test symmetry
                self.assertTrue(self.time_service.check_time_overlap(range2, range1))
        
        # Non-overlapping with midnight crossover
        non_overlapping_cases = [
            (midnight_range, (time(3, 0), time(5, 0))),     # After range ends
            (midnight_range, (time(19, 0), time(21, 0))),   # Before range starts
        ]
        
        for range1, range2 in non_overlapping_cases:
            with self.subTest(range1=range1, range2=range2):
                self.assertFalse(self.time_service.check_time_overlap(range1, range2))
                # Test symmetry
                self.assertFalse(self.time_service.check_time_overlap(range2, range1))
    
    def test_validate_meal_type(self):
        """Test meal type validation."""
        # Valid meal types
        valid_types = ['breakfast', 'lunch', 'dinner', 'BREAKFAST', 'Lunch', 'DINNER']
        for meal_type in valid_types:
            with self.subTest(meal_type=meal_type):
                self.assertTrue(self.time_service.validate_meal_type(meal_type))
        
        # Invalid meal types
        invalid_types = ['', None, 'brunch', 'snack', 'tea', 123, []]
        for meal_type in invalid_types:
            with self.subTest(meal_type=meal_type):
                self.assertFalse(self.time_service.validate_meal_type(meal_type))
    
    def test_is_open_for_meal_breakfast(self):
        """Test breakfast meal period detection (07:00-11:29)."""
        # Operating hours that serve breakfast
        breakfast_hours = OperatingHours(
            mon_fri=["07:00 - 11:30"],
            sat_sun=["08:00 - 12:00"],
            public_holiday=["09:00 - 11:00"]
        )
        
        self.assertTrue(self.time_service.is_open_for_meal(breakfast_hours, 'breakfast'))
        
        # Operating hours that don't serve breakfast
        no_breakfast_hours = OperatingHours(
            mon_fri=["12:00 - 15:00"],
            sat_sun=["18:00 - 22:00"],
            public_holiday=["19:00 - 23:00"]
        )
        
        self.assertFalse(self.time_service.is_open_for_meal(no_breakfast_hours, 'breakfast'))
    
    def test_is_open_for_meal_lunch(self):
        """Test lunch meal period detection (11:30-17:29)."""
        # Operating hours that serve lunch
        lunch_hours = OperatingHours(
            mon_fri=["11:30 - 15:30"],
            sat_sun=["12:00 - 16:00"],
            public_holiday=["13:00 - 17:00"]
        )
        
        self.assertTrue(self.time_service.is_open_for_meal(lunch_hours, 'lunch'))
        
        # Operating hours that don't serve lunch
        no_lunch_hours = OperatingHours(
            mon_fri=["07:00 - 11:00"],
            sat_sun=["18:00 - 22:00"],
            public_holiday=["19:00 - 23:00"]
        )
        
        self.assertFalse(self.time_service.is_open_for_meal(no_lunch_hours, 'lunch'))
    
    def test_is_open_for_meal_dinner(self):
        """Test dinner meal period detection (17:30-22:30)."""
        # Operating hours that serve dinner
        dinner_hours = OperatingHours(
            mon_fri=["18:00 - 22:00"],
            sat_sun=["17:30 - 23:00"],
            public_holiday=["19:00 - 22:30"]
        )
        
        self.assertTrue(self.time_service.is_open_for_meal(dinner_hours, 'dinner'))
        
        # Operating hours that don't serve dinner
        no_dinner_hours = OperatingHours(
            mon_fri=["07:00 - 11:00"],
            sat_sun=["12:00 - 16:00"],
            public_holiday=["13:00 - 17:00"]
        )
        
        self.assertFalse(self.time_service.is_open_for_meal(no_dinner_hours, 'dinner'))
    
    def test_is_open_for_meal_multiple_time_ranges(self):
        """Test meal detection with multiple time ranges per day."""
        # Restaurant with split hours (breakfast and dinner, no lunch)
        split_hours = OperatingHours(
            mon_fri=["07:00 - 11:00", "18:00 - 22:00"],
            sat_sun=["08:00 - 10:30", "19:00 - 23:00"],
            public_holiday=["09:00 - 11:29", "17:30 - 21:00"]
        )
        
        self.assertTrue(self.time_service.is_open_for_meal(split_hours, 'breakfast'))
        self.assertFalse(self.time_service.is_open_for_meal(split_hours, 'lunch'))
        self.assertTrue(self.time_service.is_open_for_meal(split_hours, 'dinner'))
    
    def test_is_open_for_meal_edge_cases(self):
        """Test meal detection edge cases."""
        # Exactly at meal boundary
        boundary_hours = OperatingHours(
            mon_fri=["11:29 - 11:31"],  # Spans breakfast-lunch boundary
            sat_sun=["17:29 - 17:31"],  # Spans lunch-dinner boundary
            public_holiday=["22:30 - 23:00"]  # Ends exactly at dinner boundary
        )
        
        # Should detect both meals for boundary-spanning hours
        self.assertTrue(self.time_service.is_open_for_meal(boundary_hours, 'breakfast'))
        self.assertTrue(self.time_service.is_open_for_meal(boundary_hours, 'lunch'))
        self.assertTrue(self.time_service.is_open_for_meal(boundary_hours, 'dinner'))
    
    def test_is_open_for_meal_invalid_meal_type(self):
        """Test meal detection with invalid meal types."""
        hours = OperatingHours(
            mon_fri=["11:30 - 15:30"],
            sat_sun=["12:00 - 16:00"],
            public_holiday=["13:00 - 17:00"]
        )
        
        invalid_types = ['brunch', 'snack', '', None, 123]
        for invalid_type in invalid_types:
            with self.subTest(meal_type=invalid_type):
                self.assertFalse(self.time_service.is_open_for_meal(hours, invalid_type))
    
    def test_get_meal_types_for_hours(self):
        """Test getting all meal types for operating hours."""
        # All-day restaurant
        all_day_hours = OperatingHours(
            mon_fri=["07:00 - 23:00"],
            sat_sun=["08:00 - 22:30"],
            public_holiday=["09:00 - 21:00"]
        )
        
        meal_types = self.time_service.get_meal_types_for_hours(all_day_hours)
        self.assertEqual(set(meal_types), {'breakfast', 'lunch', 'dinner'})
        
        # Breakfast only
        breakfast_only_hours = OperatingHours(
            mon_fri=["07:00 - 11:00"],
            sat_sun=["08:00 - 10:30"],
            public_holiday=["09:00 - 11:29"]
        )
        
        meal_types = self.time_service.get_meal_types_for_hours(breakfast_only_hours)
        self.assertEqual(meal_types, ['breakfast'])
        
        # No meals (closed during all meal periods)
        no_meal_hours = OperatingHours(
            mon_fri=["02:00 - 06:00"],
            sat_sun=["03:00 - 05:00"],
            public_holiday=["01:00 - 04:00"]
        )
        
        meal_types = self.time_service.get_meal_types_for_hours(no_meal_hours)
        self.assertEqual(meal_types, [])
    
    def test_parse_multiple_time_ranges(self):
        """Test parsing multiple time ranges."""
        time_ranges = [
            "07:00 - 11:00",
            "18:00 - 22:00",
            "invalid_range",
            "12:00 - 15:00"
        ]
        
        parsed_ranges = self.time_service.parse_multiple_time_ranges(time_ranges)
        
        expected = [
            (time(7, 0), time(11, 0)),
            (time(18, 0), time(22, 0)),
            (time(12, 0), time(15, 0))
        ]
        
        self.assertEqual(parsed_ranges, expected)
    
    def test_has_meal_overlap_any_day(self):
        """Test meal overlap detection for specific day types."""
        # Different hours for different day types
        mixed_hours = OperatingHours(
            mon_fri=["07:00 - 11:00"],      # Breakfast only
            sat_sun=["12:00 - 16:00"],      # Lunch only
            public_holiday=["18:00 - 22:00"] # Dinner only
        )
        
        # Test breakfast
        breakfast_overlap = self.time_service.has_meal_overlap_any_day(mixed_hours, 'breakfast')
        expected_breakfast = {'mon_fri': True, 'sat_sun': False, 'public_holiday': False}
        self.assertEqual(breakfast_overlap, expected_breakfast)
        
        # Test lunch
        lunch_overlap = self.time_service.has_meal_overlap_any_day(mixed_hours, 'lunch')
        expected_lunch = {'mon_fri': False, 'sat_sun': True, 'public_holiday': False}
        self.assertEqual(lunch_overlap, expected_lunch)
        
        # Test dinner
        dinner_overlap = self.time_service.has_meal_overlap_any_day(mixed_hours, 'dinner')
        expected_dinner = {'mon_fri': False, 'sat_sun': False, 'public_holiday': True}
        self.assertEqual(dinner_overlap, expected_dinner)
    
    def test_meal_periods_constants(self):
        """Test that meal period constants are correctly defined."""
        self.assertEqual(self.time_service.MEAL_PERIODS['breakfast'], 
                        (time(7, 0), time(11, 29, 59)))
        self.assertEqual(self.time_service.MEAL_PERIODS['lunch'], 
                        (time(11, 30), time(17, 29, 59)))
        self.assertEqual(self.time_service.MEAL_PERIODS['dinner'], 
                        (time(17, 30), time(22, 30, 59)))
        
        self.assertEqual(self.time_service.VALID_MEAL_TYPES, 
                        {'breakfast', 'lunch', 'dinner'})


if __name__ == '__main__':
    unittest.main()