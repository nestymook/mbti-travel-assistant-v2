"""Knowledge Base Response Parser for MBTI Travel Assistant.

This module implements tourist spot data extraction from Nova Pro responses,
data structure validation, error handling, and caching for frequently requested
MBTI personalities. Provides robust parsing of knowledge base retrieval results.

Requirements: 5.6, 5.9
"""

import asyncio
import json
import re
import time
from typing import Dict, List, Any, Optional, Tuple, Set, Union
from dataclasses import dataclass, asdict
from enum import Enum
try:
    import structlog
    logger = structlog.get_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

try:
    from ..models.tourist_spot_models import TouristSpot, TouristSpotOperatingHours
except ImportError:
    # For testing purposes, create minimal classes
    class TouristSpot:
        @classmethod
        def from_dict(cls, data):
            return cls()
        
        def validate(self):
            return []
    
    class TouristSpotOperatingHours:
        pass


class ParsedDataQuality(Enum):
    """Quality levels for parsed data."""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    INVALID = "invalid"


@dataclass
class ParsedTouristSpot:
    """Parsed tourist spot with quality metrics."""
    tourist_spot: TouristSpot
    quality_score: float
    parsing_confidence: float
    missing_fields: List[str]
    validation_errors: List[str]
    source_metadata: Dict[str, Any]


@dataclass
class ParsingResult:
    """Result of knowledge base response parsing."""
    parsed_spots: List[ParsedTouristSpot]
    total_results_processed: int
    successful_parses: int
    failed_parses: int
    parsing_time: float
    quality_distribution: Dict[ParsedDataQuality, int]
    errors: List[str]


class KnowledgeBaseResponseParser:
    """Parser for knowledge base responses with advanced data extraction.
    
    This service extracts tourist spot data from Nova Pro knowledge base responses,
    validates data structures, handles parsing errors gracefully, and provides
    caching for frequently requested MBTI personalities.
    
    Attributes:
        parsing_cache: Cache for parsed responses
        parsing_patterns: Regex patterns for data extraction
        validation_rules: Rules for data validation
        performance_metrics: Performance tracking
    """
    
    def __init__(self, enable_caching: bool = True):
        """Initialize Knowledge Base Response Parser.
        
        Args:
            enable_caching: Whether to enable response caching
        """
        self.enable_caching = enable_caching
        self.parsing_cache: Dict[str, ParsingResult] = {}
        self.performance_metrics: Dict[str, Any] = {}
        
        # Initialize parsing patterns
        self._initialize_parsing_patterns()
        
        # Initialize validation rules
        self._initialize_validation_rules()
        
        logger.info(
            "Knowledge Base Response Parser initialized",
            caching_enabled=enable_caching
        )
    
    def _initialize_parsing_patterns(self) -> None:
        """Initialize regex patterns for data extraction."""
        self.parsing_patterns = {
            # Basic structure patterns
            'title': re.compile(r'^#\s*(.+)$', re.MULTILINE),
            'section_header': re.compile(r'^##\s*(.+)$', re.MULTILINE),
            
            # MBTI information patterns
            'mbti_type': re.compile(r'\*\*Type:\*\*\s*([A-Z]{4})', re.IGNORECASE),
            'mbti_description': re.compile(r'\*\*Description:\*\*\s*(.+?)(?=\n\*\*|\n##|\n$)', re.DOTALL),
            
            # Location information patterns
            'address': re.compile(r'\*\*Address:\*\*\s*(.+?)(?=\n\*\*|\n##|\n$)', re.DOTALL),
            'district': re.compile(r'\*\*District:\*\*\s*(.+?)(?=\n\*\*|\n##|\n$)', re.DOTALL),
            'area': re.compile(r'\*\*Area:\*\*\s*(.+?)(?=\n\*\*|\n##|\n$)', re.DOTALL),
            
            # Operating hours patterns
            'weekday_hours': re.compile(r'\*\*Weekdays?\s*(?:\(Mon-Fri\))?\s*:\*\*\s*(.+?)(?=\n\*\*|\n##|\n$)', re.DOTALL | re.IGNORECASE),
            'weekend_hours': re.compile(r'\*\*Weekends?\s*(?:\(Sat-Sun\))?\s*:\*\*\s*(.+?)(?=\n\*\*|\n##|\n$)', re.DOTALL | re.IGNORECASE),
            'holiday_hours': re.compile(r'\*\*(?:Public\s*)?Holidays?\s*:\*\*\s*(.+?)(?=\n\*\*|\n##|\n$)', re.DOTALL | re.IGNORECASE),
            'operating_hours': re.compile(r'\*\*Operating\s*Hours?\s*:\*\*\s*(.+?)(?=\n\*\*|\n##|\n$)', re.DOTALL | re.IGNORECASE),
            
            # Additional information patterns
            'contact_remarks': re.compile(r'\*\*Contact(?:/Remarks)?:\*\*\s*(.+?)(?=\n\*\*|\n##|\n$)', re.DOTALL | re.IGNORECASE),
            'phone': re.compile(r'\*\*Phone:\*\*\s*(.+?)(?=\n\*\*|\n##|\n$)', re.DOTALL),
            'website': re.compile(r'\*\*Website:\*\*\s*(.+?)(?=\n\*\*|\n##|\n$)', re.DOTALL),
            'entrance_fee': re.compile(r'\*\*(?:Entrance\s*)?Fee:\*\*\s*(.+?)(?=\n\*\*|\n##|\n$)', re.DOTALL | re.IGNORECASE),
            
            # Keywords and metadata patterns
            'keywords': re.compile(r'(?:Keywords?|MBTI):\s*(.+?)(?=\n|$)', re.IGNORECASE),
            'category': re.compile(r'\*\*Category:\*\*\s*(.+?)(?=\n\*\*|\n##|\n$)', re.DOTALL | re.IGNORECASE),
            
            # Time format patterns
            'time_range': re.compile(r'(\d{1,2}):(\d{2})\s*[-–]\s*(\d{1,2}):(\d{2})'),
            'time_single': re.compile(r'(\d{1,2}):(\d{2})'),
            
            # Special values
            'closed': re.compile(r'\b(?:closed|休息|休館)\b', re.IGNORECASE),
            'always_open': re.compile(r'\b(?:24\s*hours?|always\s*open|全天開放)\b', re.IGNORECASE),
            'by_appointment': re.compile(r'\b(?:by\s*appointment|預約|appointment\s*only)\b', re.IGNORECASE)
        }
    
    def _initialize_validation_rules(self) -> None:
        """Initialize validation rules for parsed data."""
        self.validation_rules = {
            'required_fields': ['name', 'address', 'district'],
            'optional_fields': ['area', 'description', 'contact_info', 'website', 'entrance_fee'],
            'mbti_types': {
                'INTJ', 'INTP', 'ENTJ', 'ENTP',
                'INFJ', 'INFP', 'ENFJ', 'ENFP',
                'ISTJ', 'ISFJ', 'ESTJ', 'ESFJ',
                'ISTP', 'ISFP', 'ESTP', 'ESFP'
            },
            'min_name_length': 2,
            'max_name_length': 200,
            'min_address_length': 10,
            'max_description_length': 2000,
            'valid_districts': {
                'Central', 'Admiralty', 'Wan Chai', 'Causeway Bay', 'North Point',
                'Quarry Bay', 'Tai Koo', 'Shau Kei Wan', 'Chai Wan', 'Sheung Wan',
                'Mid-Levels', 'The Peak', 'Aberdeen', 'Wong Chuk Hang', 'Stanley',
                'Repulse Bay', 'Tsim Sha Tsui', 'Jordan', 'Yau Ma Tei', 'Mong Kok',
                'Prince Edward', 'Sham Shui Po', 'Cheung Sha Wan', 'Lai Chi Kok',
                'Mei Foo', 'Kowloon Tong', 'Kowloon City', 'To Kwa Wan', 'Ma Tau Wai',
                'Hung Hom', 'Whampoa', 'Ho Man Tin', 'Yau Yat Chuen', 'Diamond Hill',
                'Wong Tai Sin', 'Lok Fu', 'Kowloon Bay', 'Ngau Tau Kok', 'Kwun Tong',
                'Lam Tin', 'Yau Tong', 'Lei Yue Mun', 'Tseung Kwan O', 'Sha Tin',
                'Tai Po', 'Fanling', 'Sheung Shui', 'Yuen Long', 'Tuen Mun',
                'Tsuen Wan', 'Kwai Chung', 'Tsing Yi', 'Ma On Shan', 'Tai Wai'
            }
        }
    
    async def parse_knowledge_base_responses(
        self,
        query_results: List[Dict[str, Any]],
        mbti_type: str,
        use_cache: bool = True
    ) -> ParsingResult:
        """Parse knowledge base query results into structured tourist spot data.
        
        Args:
            query_results: List of knowledge base retrieval results
            mbti_type: MBTI personality type for context
            use_cache: Whether to use cached parsing results
            
        Returns:
            ParsingResult with parsed tourist spots and metadata
        """
        start_time = time.time()
        
        # Generate cache key
        cache_key = self._generate_cache_key(query_results, mbti_type)
        
        # Check cache
        if use_cache and self.enable_caching and cache_key in self.parsing_cache:
            logger.info(
                "Returning cached parsing results",
                mbti_type=mbti_type,
                results_count=len(query_results)
            )
            return self.parsing_cache[cache_key]
        
        logger.info(
            "Starting knowledge base response parsing",
            mbti_type=mbti_type,
            results_count=len(query_results)
        )
        
        parsed_spots = []
        failed_parses = 0
        errors = []
        quality_distribution = {quality: 0 for quality in ParsedDataQuality}
        
        for i, result in enumerate(query_results):
            try:
                parsed_spot = await self._parse_single_result(result, mbti_type, i)
                
                if parsed_spot:
                    parsed_spots.append(parsed_spot)
                    
                    # Update quality distribution
                    quality = self._assess_data_quality(parsed_spot)
                    quality_distribution[quality] += 1
                else:
                    failed_parses += 1
                    
            except Exception as e:
                failed_parses += 1
                error_msg = f"Failed to parse result {i}: {str(e)}"
                errors.append(error_msg)
                logger.warning(
                    "Failed to parse knowledge base result",
                    result_index=i,
                    error=str(e)
                )
        
        # Create parsing result
        parsing_time = time.time() - start_time
        result = ParsingResult(
            parsed_spots=parsed_spots,
            total_results_processed=len(query_results),
            successful_parses=len(parsed_spots),
            failed_parses=failed_parses,
            parsing_time=parsing_time,
            quality_distribution=quality_distribution,
            errors=errors
        )
        
        # Cache result
        if use_cache and self.enable_caching:
            self.parsing_cache[cache_key] = result
        
        # Update performance metrics
        self.performance_metrics[mbti_type] = {
            'parsing_time': parsing_time,
            'success_rate': len(parsed_spots) / len(query_results) if query_results else 0,
            'quality_distribution': dict(quality_distribution),
            'timestamp': time.time()
        }
        
        logger.info(
            "Knowledge base response parsing completed",
            mbti_type=mbti_type,
            parsing_time=f"{parsing_time:.2f}s",
            successful_parses=len(parsed_spots),
            failed_parses=failed_parses,
            success_rate=f"{(len(parsed_spots) / len(query_results) * 100):.1f}%" if query_results else "0%"
        )
        
        return result
    
    async def _parse_single_result(
        self,
        result: Dict[str, Any],
        mbti_type: str,
        result_index: int
    ) -> Optional[ParsedTouristSpot]:
        """Parse a single knowledge base result into a tourist spot.
        
        Args:
            result: Single knowledge base retrieval result
            mbti_type: MBTI personality type for context
            result_index: Index of result for tracking
            
        Returns:
            ParsedTouristSpot object or None if parsing fails
        """
        try:
            # Extract basic information from result
            content = result.get('content', {}).get('text', '')
            score = result.get('score', 0.0)
            location = result.get('location', {})
            s3_uri = location.get('s3Location', {}).get('uri', '')
            
            if not content:
                logger.warning(f"Empty content in result {result_index}")
                return None
            
            # Extract source metadata
            source_metadata = {
                's3_uri': s3_uri,
                'relevance_score': score,
                'result_index': result_index,
                'content_length': len(content)
            }
            
            # Parse tourist spot data
            spot_data = self._extract_tourist_spot_data(content, s3_uri, mbti_type)
            
            if not spot_data:
                return None
            
            # Create TouristSpot object
            tourist_spot = TouristSpot.from_dict(spot_data)
            
            # Validate parsed data
            validation_errors = tourist_spot.validate()
            missing_fields = self._identify_missing_fields(spot_data)
            
            # Calculate quality metrics
            quality_score = self._calculate_quality_score(spot_data, validation_errors, missing_fields)
            parsing_confidence = self._calculate_parsing_confidence(content, spot_data)
            
            return ParsedTouristSpot(
                tourist_spot=tourist_spot,
                quality_score=quality_score,
                parsing_confidence=parsing_confidence,
                missing_fields=missing_fields,
                validation_errors=validation_errors,
                source_metadata=source_metadata
            )
            
        except Exception as e:
            logger.error(
                "Error parsing single result",
                result_index=result_index,
                error=str(e)
            )
            return None
    
    def _extract_tourist_spot_data(
        self,
        content: str,
        s3_uri: str,
        mbti_type: str
    ) -> Optional[Dict[str, Any]]:
        """Extract tourist spot data from content text.
        
        Args:
            content: Text content from knowledge base
            s3_uri: S3 URI of the source document
            mbti_type: MBTI personality type for context
            
        Returns:
            Dictionary with extracted tourist spot data
        """
        try:
            # Initialize data structure
            spot_data = {
                'id': self._generate_spot_id(s3_uri),
                'name': '',
                'address': '',
                'district': '',
                'area': '',
                'location_category': 'Tourist Attraction',
                'description': '',
                'operating_hours': {},
                'operating_days': [],
                'mbti_match': True,
                'mbti_personality_types': [mbti_type],
                'keywords': [],
                'metadata': {
                    's3_uri': s3_uri,
                    'source_content_length': len(content)
                }
            }
            
            # Extract name from title
            title_match = self.parsing_patterns['title'].search(content)
            if title_match:
                spot_data['name'] = title_match.group(1).strip()
            else:
                # Fallback: extract from filename
                filename = s3_uri.split('/')[-1] if s3_uri else 'unknown'
                spot_data['name'] = filename.replace('.md', '').replace('_', ' ')
            
            # Extract MBTI information
            mbti_match = self.parsing_patterns['mbti_type'].search(content)
            if mbti_match:
                extracted_mbti = mbti_match.group(1).upper()
                if extracted_mbti in self.validation_rules['mbti_types']:
                    spot_data['mbti_personality_types'] = [extracted_mbti]
            
            desc_match = self.parsing_patterns['mbti_description'].search(content)
            if desc_match:
                spot_data['description'] = desc_match.group(1).strip()
            
            # Extract location information
            address_match = self.parsing_patterns['address'].search(content)
            if address_match:
                spot_data['address'] = address_match.group(1).strip()
            
            district_match = self.parsing_patterns['district'].search(content)
            if district_match:
                spot_data['district'] = district_match.group(1).strip()
            
            area_match = self.parsing_patterns['area'].search(content)
            if area_match:
                spot_data['area'] = area_match.group(1).strip()
            
            # Extract operating hours
            operating_hours = self._extract_operating_hours(content)
            spot_data['operating_hours'] = operating_hours
            
            # Extract additional information
            contact_match = self.parsing_patterns['contact_remarks'].search(content)
            if contact_match:
                spot_data['contact_info'] = contact_match.group(1).strip()
            
            website_match = self.parsing_patterns['website'].search(content)
            if website_match:
                spot_data['website'] = website_match.group(1).strip()
            
            fee_match = self.parsing_patterns['entrance_fee'].search(content)
            if fee_match:
                spot_data['entrance_fee'] = fee_match.group(1).strip()
            
            # Extract keywords
            keywords_match = self.parsing_patterns['keywords'].search(content)
            if keywords_match:
                keywords_text = keywords_match.group(1)
                keywords = [kw.strip() for kw in keywords_text.split(',') if kw.strip()]
                spot_data['keywords'] = keywords
            
            # Set default values for missing critical fields
            if not spot_data['name']:
                spot_data['name'] = f"Tourist Attraction {mbti_type}"
            
            if not spot_data['description']:
                spot_data['description'] = f"Tourist attraction suitable for {mbti_type} personality"
            
            if not spot_data['district'] and spot_data['area']:
                spot_data['district'] = spot_data['area']
            
            return spot_data
            
        except Exception as e:
            logger.error(
                "Error extracting tourist spot data",
                error=str(e),
                content_preview=content[:100] + "..." if len(content) > 100 else content
            )
            return None
    
    def _extract_operating_hours(self, content: str) -> Dict[str, Any]:
        """Extract operating hours from content text.
        
        Args:
            content: Text content to parse
            
        Returns:
            Dictionary with operating hours data
        """
        operating_hours = {}
        
        # Extract weekday hours
        weekday_match = self.parsing_patterns['weekday_hours'].search(content)
        if weekday_match:
            weekday_hours = weekday_match.group(1).strip()
            operating_hours.update({
                'monday': weekday_hours,
                'tuesday': weekday_hours,
                'wednesday': weekday_hours,
                'thursday': weekday_hours,
                'friday': weekday_hours
            })
        
        # Extract weekend hours
        weekend_match = self.parsing_patterns['weekend_hours'].search(content)
        if weekend_match:
            weekend_hours = weekend_match.group(1).strip()
            operating_hours.update({
                'saturday': weekend_hours,
                'sunday': weekend_hours
            })
        
        # Extract holiday hours
        holiday_match = self.parsing_patterns['holiday_hours'].search(content)
        if holiday_match:
            operating_hours['public_holiday'] = holiday_match.group(1).strip()
        
        # Extract general operating hours if specific ones not found
        if not operating_hours:
            general_match = self.parsing_patterns['operating_hours'].search(content)
            if general_match:
                general_hours = general_match.group(1).strip()
                # Apply to all days
                for day in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']:
                    operating_hours[day] = general_hours
        
        return operating_hours
    
    def _generate_spot_id(self, s3_uri: str) -> str:
        """Generate unique spot ID from S3 URI.
        
        Args:
            s3_uri: S3 URI of the source document
            
        Returns:
            Unique spot identifier
        """
        if s3_uri:
            filename = s3_uri.split('/')[-1]
            return filename.replace('.md', '').replace('.txt', '')
        else:
            return f"spot_{int(time.time())}"
    
    def _identify_missing_fields(self, spot_data: Dict[str, Any]) -> List[str]:
        """Identify missing required and optional fields.
        
        Args:
            spot_data: Extracted spot data dictionary
            
        Returns:
            List of missing field names
        """
        missing_fields = []
        
        # Check required fields
        for field in self.validation_rules['required_fields']:
            if not spot_data.get(field) or (isinstance(spot_data[field], str) and not spot_data[field].strip()):
                missing_fields.append(field)
        
        # Check important optional fields
        for field in self.validation_rules['optional_fields']:
            if not spot_data.get(field) or (isinstance(spot_data[field], str) and not spot_data[field].strip()):
                missing_fields.append(field)
        
        return missing_fields
    
    def _calculate_quality_score(
        self,
        spot_data: Dict[str, Any],
        validation_errors: List[str],
        missing_fields: List[str]
    ) -> float:
        """Calculate quality score for parsed data.
        
        Args:
            spot_data: Extracted spot data
            validation_errors: List of validation errors
            missing_fields: List of missing fields
            
        Returns:
            Quality score between 0.0 and 1.0
        """
        base_score = 1.0
        
        # Deduct for validation errors
        error_penalty = len(validation_errors) * 0.1
        base_score -= min(error_penalty, 0.5)
        
        # Deduct for missing required fields
        required_missing = [f for f in missing_fields if f in self.validation_rules['required_fields']]
        required_penalty = len(required_missing) * 0.2
        base_score -= min(required_penalty, 0.6)
        
        # Deduct for missing optional fields
        optional_missing = [f for f in missing_fields if f in self.validation_rules['optional_fields']]
        optional_penalty = len(optional_missing) * 0.05
        base_score -= min(optional_penalty, 0.3)
        
        # Bonus for rich data
        if spot_data.get('operating_hours') and isinstance(spot_data['operating_hours'], dict):
            if len(spot_data['operating_hours']) >= 3:
                base_score += 0.1
        
        if spot_data.get('keywords') and len(spot_data['keywords']) >= 3:
            base_score += 0.05
        
        if spot_data.get('description') and len(spot_data['description']) >= 50:
            base_score += 0.05
        
        return max(0.0, min(1.0, base_score))
    
    def _calculate_parsing_confidence(
        self,
        content: str,
        spot_data: Dict[str, Any]
    ) -> float:
        """Calculate confidence in parsing accuracy.
        
        Args:
            content: Original content text
            spot_data: Extracted spot data
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        confidence = 0.5  # Base confidence
        
        # Increase confidence for structured content
        if '**' in content and '##' in content:
            confidence += 0.2
        
        # Increase confidence for clear patterns
        if self.parsing_patterns['title'].search(content):
            confidence += 0.1
        
        if self.parsing_patterns['address'].search(content):
            confidence += 0.1
        
        if self.parsing_patterns['mbti_type'].search(content):
            confidence += 0.1
        
        # Decrease confidence for very short content
        if len(content) < 200:
            confidence -= 0.2
        
        # Decrease confidence for missing critical data
        if not spot_data.get('name') or not spot_data.get('address'):
            confidence -= 0.3
        
        return max(0.0, min(1.0, confidence))
    
    def _assess_data_quality(self, parsed_spot: ParsedTouristSpot) -> ParsedDataQuality:
        """Assess overall data quality for parsed spot.
        
        Args:
            parsed_spot: Parsed tourist spot with metrics
            
        Returns:
            ParsedDataQuality enum value
        """
        quality_score = parsed_spot.quality_score
        confidence = parsed_spot.parsing_confidence
        error_count = len(parsed_spot.validation_errors)
        missing_count = len(parsed_spot.missing_fields)
        
        # Determine quality based on multiple factors
        if quality_score >= 0.9 and confidence >= 0.8 and error_count == 0:
            return ParsedDataQuality.EXCELLENT
        elif quality_score >= 0.7 and confidence >= 0.6 and error_count <= 1:
            return ParsedDataQuality.GOOD
        elif quality_score >= 0.5 and confidence >= 0.4 and error_count <= 3:
            return ParsedDataQuality.FAIR
        elif quality_score >= 0.3 and confidence >= 0.2:
            return ParsedDataQuality.POOR
        else:
            return ParsedDataQuality.INVALID
    
    def _generate_cache_key(
        self,
        query_results: List[Dict[str, Any]],
        mbti_type: str
    ) -> str:
        """Generate cache key for parsing results.
        
        Args:
            query_results: List of query results
            mbti_type: MBTI personality type
            
        Returns:
            Cache key string
        """
        # Create hash of result URIs and scores
        result_signature = []
        for result in query_results:
            uri = result.get('location', {}).get('s3Location', {}).get('uri', '')
            score = result.get('score', 0.0)
            result_signature.append(f"{uri}:{score:.3f}")
        
        signature_str = "|".join(sorted(result_signature))
        signature_hash = hash(signature_str)
        
        return f"{mbti_type}_{len(query_results)}_{signature_hash}"
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for response parsing.
        
        Returns:
            Dictionary with performance metrics by MBTI type
        """
        return self.performance_metrics.copy()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics for parsing results.
        
        Returns:
            Dictionary with cache statistics
        """
        if not self.enable_caching:
            return {'caching_enabled': False}
        
        total_parsed_spots = sum(
            len(result.parsed_spots) for result in self.parsing_cache.values()
        )
        
        return {
            'caching_enabled': True,
            'cached_parsing_results': len(self.parsing_cache),
            'total_cached_spots': total_parsed_spots,
            'cache_keys': list(self.parsing_cache.keys())
        }
    
    def clear_cache(self) -> None:
        """Clear the parsing result cache."""
        self.parsing_cache.clear()
        logger.info("Parsing cache cleared")
    
    def validate_parsed_data(
        self,
        parsed_spots: List[ParsedTouristSpot],
        quality_threshold: float = 0.5
    ) -> Tuple[List[ParsedTouristSpot], List[ParsedTouristSpot]]:
        """Validate parsed data and separate valid from invalid spots.
        
        Args:
            parsed_spots: List of parsed tourist spots
            quality_threshold: Minimum quality score threshold
            
        Returns:
            Tuple of (valid_spots, invalid_spots)
        """
        valid_spots = []
        invalid_spots = []
        
        for spot in parsed_spots:
            if (spot.quality_score >= quality_threshold and 
                spot.parsing_confidence >= 0.3 and
                len(spot.validation_errors) <= 2):
                valid_spots.append(spot)
            else:
                invalid_spots.append(spot)
        
        logger.info(
            "Data validation completed",
            total_spots=len(parsed_spots),
            valid_spots=len(valid_spots),
            invalid_spots=len(invalid_spots),
            quality_threshold=quality_threshold
        )
        
        return valid_spots, invalid_spots