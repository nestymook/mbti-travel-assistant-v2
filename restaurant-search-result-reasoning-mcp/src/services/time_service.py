"""Time service for meal type calculations and operating hours analysis.

This module provides utilities for parsing time ranges, validating meal types,
and determining if restaurants are open during specific meal periods.
Follows PEP8 style guidelines and handles various time format edge cases.
"""

import re
from datetime import time
from typing import List, Tuple, Optional
from src.models.restaurant_models import OperatingHours


class TimeService:
    """Service for time parsing and meal type calculations.
    
    Handles time range parsing, meal period validation, and operating hours
    analysis for restaurant search functionality.
    """
    
    # Meal type time ranges (24-hour format)
    # Note: Using 59 seconds to make boundaries exclusive
    MEAL_PERIODS = {
        'breakfast': (time(7, 0), time(11, 29, 59)),
        'lunch': (time(11, 30), time(17, 29, 59)),
        'dinner': (time(17, 30), time(22, 30, 59))
    }
    
    # Valid meal types
    VALID_MEAL_TYPES = {'breakfast', 'lunch', 'dinner'}
    
    def __init__(self):
        """Initialize the TimeService."""
        # Regex pattern for time range parsing
        # Matches formats like "11:30 - 15:30", "07:00-11:29", "18:00 - 22:30"
        self._time_range_pattern = re.compile(
            r'(\d{1,2}):(\d{2})\s*-\s*(\d{1,2}):(\d{2})'
        )
    
    def parse_time_range(self, time_range: str) -> Optional[Tuple[time, time]]:
        """Parse a time range string into start and end time objects.
        
        Args:
            time_range: Time range string (e.g., "11:30 - 15:30")
            
        Returns:
            Tuple of (start_time, end_time) or None if parsing fails
            
        Examples:
            >>> service = TimeService()
            >>> service.parse_time_range("11:30 - 15:30")
            (datetime.time(11, 30), datetime.time(15, 30))
        """
        if not time_range or not isinstance(time_range, str):
            return None
            
        match = self._time_range_pattern.match(time_range.strip())
        if not match:
            return None
            
        try:
            start_hour, start_min, end_hour, end_min = map(int, match.groups())
            
            # Validate time components
            if not (0 <= start_hour <= 23 and 0 <= start_min <= 59):
                return None
            if not (0 <= end_hour <= 23 and 0 <= end_min <= 59):
                return None
                
            start_time = time(start_hour, start_min)
            end_time = time(end_hour, end_min)
            
            return (start_time, end_time)
            
        except (ValueError, TypeError):
            return None
    
    def check_time_overlap(self, range1: Tuple[time, time], 
                          range2: Tuple[time, time]) -> bool:
        """Check if two time ranges overlap.
        
        Args:
            range1: First time range (start_time, end_time)
            range2: Second time range (start_time, end_time)
            
        Returns:
            True if ranges overlap, False otherwise
            
        Note:
            Handles midnight crossover by treating times as continuous.
            For example, 22:00-02:00 overlaps with 01:00-03:00.
        """
        start1, end1 = range1
        start2, end2 = range2
        
        # Check if range1 crosses midnight
        range1_crosses_midnight = end1 < start1
        # Check if range2 crosses midnight
        range2_crosses_midnight = end2 < start2
        
        if range1_crosses_midnight and range2_crosses_midnight:
            # Both ranges cross midnight - they always overlap
            return True
        elif range1_crosses_midnight:
            # Only range1 crosses midnight (e.g., 22:00 - 02:00)
            # Range1 covers: [start1, 23:59:59] and [00:00:00, end1]
            # Check if range2 overlaps with either part
            # Part 1: [start1, 23:59:59] - check if range2 overlaps
            part1_overlap = start2 >= start1 or end2 >= start1
            # Part 2: [00:00:00, end1] - check if range2 overlaps  
            part2_overlap = start2 <= end1 or end2 <= end1
            return part1_overlap or part2_overlap
        elif range2_crosses_midnight:
            # Only range2 crosses midnight
            # Range2 covers: [start2, 23:59:59] and [00:00:00, end2]
            # Check if range1 overlaps with either part
            # Part 1: [start2, 23:59:59] - check if range1 overlaps
            part1_overlap = start1 >= start2 or end1 >= start2
            # Part 2: [00:00:00, end2] - check if range1 overlaps
            part2_overlap = start1 <= end2 or end1 <= end2
            return part1_overlap or part2_overlap
        else:
            # Neither range crosses midnight - normal overlap check
            return start1 <= end2 and start2 <= end1
    
    def validate_meal_type(self, meal_type: str) -> bool:
        """Validate if a meal type is supported.
        
        Args:
            meal_type: Meal type string to validate
            
        Returns:
            True if meal type is valid, False otherwise
        """
        if not meal_type or not isinstance(meal_type, str):
            return False
        return meal_type.lower() in self.VALID_MEAL_TYPES
    
    def is_open_for_meal(self, operating_hours: OperatingHours, 
                        meal_type: str) -> bool:
        """Check if restaurant is open during a specific meal period.
        
        Args:
            operating_hours: Restaurant operating hours
            meal_type: Meal type to check ("breakfast", "lunch", "dinner")
            
        Returns:
            True if restaurant is open during meal period, False otherwise
            
        Note:
            Checks all day types (Mon-Fri, Sat-Sun, Public Holiday) and
            returns True if ANY of them overlap with the meal period.
        """
        if not self.validate_meal_type(meal_type):
            return False
            
        meal_period = self.MEAL_PERIODS[meal_type.lower()]
        
        # Check all day types for overlap
        all_time_ranges = []
        all_time_ranges.extend(operating_hours.mon_fri)
        all_time_ranges.extend(operating_hours.sat_sun)
        all_time_ranges.extend(operating_hours.public_holiday)
        
        for time_range_str in all_time_ranges:
            parsed_range = self.parse_time_range(time_range_str)
            if parsed_range and self.check_time_overlap(parsed_range, meal_period):
                return True
                
        return False
    
    def get_meal_types_for_hours(self, operating_hours: OperatingHours) -> List[str]:
        """Get all meal types that a restaurant serves based on operating hours.
        
        Args:
            operating_hours: Restaurant operating hours
            
        Returns:
            List of meal types the restaurant serves
        """
        meal_types = []
        
        for meal_type in self.VALID_MEAL_TYPES:
            if self.is_open_for_meal(operating_hours, meal_type):
                meal_types.append(meal_type)
                
        return sorted(meal_types)
    
    def parse_multiple_time_ranges(self, time_ranges: List[str]) -> List[Tuple[time, time]]:
        """Parse multiple time range strings.
        
        Args:
            time_ranges: List of time range strings
            
        Returns:
            List of parsed time range tuples (excludes invalid ranges)
        """
        parsed_ranges = []
        
        for time_range_str in time_ranges:
            parsed_range = self.parse_time_range(time_range_str)
            if parsed_range:
                parsed_ranges.append(parsed_range)
                
        return parsed_ranges
    
    def has_meal_overlap_any_day(self, operating_hours: OperatingHours, 
                                meal_type: str) -> dict:
        """Check meal overlap for each day type separately.
        
        Args:
            operating_hours: Restaurant operating hours
            meal_type: Meal type to check
            
        Returns:
            Dictionary with day types as keys and boolean overlap as values
        """
        if not self.validate_meal_type(meal_type):
            return {'mon_fri': False, 'sat_sun': False, 'public_holiday': False}
            
        meal_period = self.MEAL_PERIODS[meal_type.lower()]
        
        result = {}
        day_types = {
            'mon_fri': operating_hours.mon_fri,
            'sat_sun': operating_hours.sat_sun,
            'public_holiday': operating_hours.public_holiday
        }
        
        for day_type, time_ranges in day_types.items():
            has_overlap = False
            for time_range_str in time_ranges:
                parsed_range = self.parse_time_range(time_range_str)
                if parsed_range and self.check_time_overlap(parsed_range, meal_period):
                    has_overlap = True
                    break
            result[day_type] = has_overlap
            
        return result