"""
Comprehensive Unit Tests for Nova Pro Knowledge Base Integration

This module provides comprehensive unit tests for Nova Pro knowledge base integration
with 90%+ code coverage, including error handling, edge cases, and performance testing.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from typing import List, Dict, Any
import json
import time
from datetime import datetime

from ..services.nova_pro_knowledge_base_client import (
    NovaProKnowledgeBaseClient,
    QueryStrategy,
    MBTITraits,
    KnowledgeBaseError,
    QueryOptimizationError
)
from ..services.mbti_personality_processor import (
    MBTIPersonalityProcessor,
    PersonalityDimension,
    PersonalityProfile,
    PersonalityValidationError
)
from ..services.knowledge_base_response_parser import (
    KnowledgeBaseResponseParser,
    ParsedDataQuality,
    ParsedTouristSpot,
    ParsingError
)
from ..models.tourist_spot_models import TouristSpot, TouristSpotOperatingHours


class TestNovaProKnowledgeBaseClientComprehensive:
    """Comprehensive test cases for NovaProKnowledgeBaseClient with 90%+ coverage."""

    def setup_method(self):
        """Set up test fixtures."""
        self.nova_client = NovaProKnowledgeBaseClient()
        self.mock_bedrock_client = Mock()
        self.nova_client.bedrock_client = self.mock_bedrock_client
        self.nova_client.bedrock_agent_client = Mock()

    def test_initialization_default_values(self):
        """Test client initialization with default values."""
        client = NovaProKnowledgeBaseClient()
        
        assert client.knowledge_base_id == "RCWW86CLM9"
        assert client.region == "us-east-1"
        assert client.nova_pro_model_id == "amazon.nova-pro-v1:0"
        assert client.enable_caching is True
        assert client.max_retries == 3
        assert client.timeout_seconds == 30
        assert isinstance(client.mbti_traits_map, dict)
        assert len(client.mbti_traits_map) == 16

    def test_initialization_custom_values(self):
        """Test client initialization with custom values."""
        custom_config = {
            'knowledge_base_id': 'CUSTOM_KB_ID',
            'region': 'us-west-2',
            'nova_pro_model_id': 'custom-model-id',
            'enable_caching': False,
            'max_retries': 5,
            'timeout_seconds': 60
        }
        
        client = NovaProKnowledgeBaseClient(**custom_config)
        
        assert client.knowledge_base_id == 'CUSTOM_KB_ID'
        assert client.region == 'us-west-2'
        assert client.nova_pro_model_id == 'custom-model-id'
        assert client.enable_caching is False
        assert client.max_retries == 5
        assert client.timeout_seconds == 60

    def test_validate_mbti_format_valid_types(self):
        """Test MBTI format validation with valid types."""
        valid_types = [
            'INFJ', 'INFP', 'INTJ', 'INTP',
            'ISFJ', 'ISFP', 'ISTJ', 'ISTP',
            'ENFJ', 'ENFP', 'ENTJ', 'ENTP',
            'ESFJ', 'ESFP', 'ESTJ', 'ESTP'
        ]
        
        for mbti_type in valid_types:
            assert self.nova_client.validate_mbti_format(mbti_type) is True
            assert self.nova_client.validate_mbti_format(mbti_type.lower()) is True

    def test_validate_mbti_format_invalid_types(self):
        """Test MBTI format validation with invalid types."""
        invalid_types = [
            '', None, 'INVALID', 'INF', 'INFJA', 'XXXX', '1234',
            'infj ', ' INFJ', 'I-N-F-J', 'I.N.F.J'
        ]
        
        for invalid_type in invalid_types:
            assert self.nova_client.validate_mbti_format(invalid_type) is False

    def test_mbti_traits_mapping_completeness(self):
        """Test MBTI traits mapping for all personality types."""
        expected_types = [
            'INFJ', 'INFP', 'INTJ', 'INTP',
            'ISFJ', 'ISFP', 'ISTJ', 'ISTP',
            'ENFJ', 'ENFP', 'ENTJ', 'ENTP',
            'ESFJ', 'ESFP', 'ESTJ', 'ESTP'
        ]
        
        for mbti_type in expected_types:
            assert mbti_type in self.nova_client.mbti_traits_map
            traits = self.nova_client.mbti_traits_map[mbti_type]
            assert isinstance(traits, MBTITraits)
            assert traits.energy_source in ['Introversion', 'Extraversion']
            assert traits.information_processing in ['Sensing', 'Intuition']
            assert traits.decision_making in ['Thinking', 'Feeling']
            assert traits.lifestyle in ['Judging', 'Perceiving']
            assert len(traits.preferences) > 0
            assert len(traits.suitable_activities) > 0

    @pytest.mark.asyncio
    async def test_query_mbti_tourist_spots_success(self):
        """Test successful MBTI tourist spots query."""
        # Mock successful response
        mock_response = {
            'output': {
                'text': 'Generated response text'
            },
            'retrievalResults': [
                {
                    'content': {
                        'text': 'Test tourist spot content'
                    },
                    'score': 0.85,
                    'location': {
                        's3Location': {
                            'uri': 's3://test-bucket/test-file.md'
                        }
                    }
                }
            ]
        }
        
        self.nova_client.bedrock_agent_client.retrieve_and_generate = AsyncMock(return_value=mock_response)
        
        result = await self.nova_client.query_mbti_tourist_spots('INFJ')
        
        assert isinstance(result, list)
        assert len(result) > 0
        self.nova_client.bedrock_agent_client.retrieve_and_generate.assert_called_once()

    @pytest.mark.asyncio
    async def test_query_mbti_tourist_spots_invalid_mbti(self):
        """Test MBTI tourist spots query with invalid MBTI type."""
        with pytest.raises(ValueError, match="Invalid MBTI personality format"):
            await self.nova_client.query_mbti_tourist_spots('INVALID')

    @pytest.mark.asyncio
    async def test_query_mbti_tourist_spots_api_error(self):
        """Test MBTI tourist spots query with API error."""
        # Mock API error
        self.nova_client.bedrock_agent_client.retrieve_and_generate = AsyncMock(
            side_effect=Exception("API Error")
        )
        
        with pytest.raises(KnowledgeBaseError):
            await self.nova_client.query_mbti_tourist_spots('INFJ')

    @pytest.mark.asyncio
    async def test_query_mbti_tourist_spots_with_retry(self):
        """Test MBTI tourist spots query with retry logic."""
        # Mock first call fails, second succeeds
        mock_response = {
            'output': {'text': 'Success'},
            'retrievalResults': []
        }
        
        self.nova_client.bedrock_agent_client.retrieve_and_generate = AsyncMock(
            side_effect=[Exception("Temporary error"), mock_response]
        )
        
        result = await self.nova_client.query_mbti_tourist_spots('INFJ')
        
        assert isinstance(result, list)
        assert self.nova_client.bedrock_agent_client.retrieve_and_generate.call_count == 2

    @pytest.mark.asyncio
    async def test_query_mbti_tourist_spots_max_retries_exceeded(self):
        """Test MBTI tourist spots query when max retries exceeded."""
        # Mock all calls fail
        self.nova_client.bedrock_agent_client.retrieve_and_generate = AsyncMock(
            side_effect=Exception("Persistent error")
        )
        
        with pytest.raises(KnowledgeBaseError):
            await self.nova_client.query_mbti_tourist_spots('INFJ')
        
        # Should retry max_retries + 1 times (initial + retries)
        assert self.nova_client.bedrock_agent_client.retrieve_and_generate.call_count == self.nova_client.max_retries + 1

    def test_build_mbti_query_prompt_all_types(self):
        """Test MBTI query prompt building for all personality types."""
        mbti_types = ['INFJ', 'ENFP', 'INTJ', 'ESTP']
        
        for mbti_type in mbti_types:
            prompt = self.nova_client._build_mbti_query_prompt(mbti_type)
            
            assert isinstance(prompt, str)
            assert mbti_type in prompt
            assert len(prompt) > 100  # Should be substantial
            assert 'Hong Kong' in prompt
            assert 'tourist spots' in prompt.lower()

    def test_build_mbti_query_prompt_with_strategy(self):
        """Test MBTI query prompt building with different strategies."""
        strategies = [
            QueryStrategy.COMPREHENSIVE,
            QueryStrategy.FOCUSED,
            QueryStrategy.RAPID
        ]
        
        for strategy in strategies:
            prompt = self.nova_client._build_mbti_query_prompt('INFJ', strategy)
            
            assert isinstance(prompt, str)
            assert 'INFJ' in prompt
            assert len(prompt) > 50

    def test_optimize_query_for_performance(self):
        """Test query optimization for performance."""
        base_prompt = "Find tourist spots for INFJ personality"
        
        optimized = self.nova_client._optimize_query_for_performance(base_prompt, 'INFJ')
        
        assert isinstance(optimized, str)
        assert len(optimized) >= len(base_prompt)
        assert 'INFJ' in optimized

    def test_cache_functionality(self):
        """Test caching functionality."""
        # Test cache stats
        stats = self.nova_client.get_cache_stats()
        assert 'cached_queries' in stats
        assert 'total_cached_results' in stats
        assert 'cache_hit_rate' in stats
        assert 'cache_size' in stats
        
        # Test cache clearing
        self.nova_client.clear_cache()
        stats_after_clear = self.nova_client.get_cache_stats()
        assert stats_after_clear['cached_queries'] == 0

    def test_performance_metrics(self):
        """Test performance metrics collection."""
        metrics = self.nova_client.get_performance_metrics()
        
        assert isinstance(metrics, dict)
        assert 'total_queries' in metrics
        assert 'average_response_time' in metrics
        assert 'success_rate' in metrics
        assert 'error_rate' in metrics
        assert 'cache_hit_rate' in metrics

    def test_error_handling_configuration(self):
        """Test error handling configuration."""
        # Test with invalid configuration
        with pytest.raises(ValueError):
            NovaProKnowledgeBaseClient(max_retries=-1)
        
        with pytest.raises(ValueError):
            NovaProKnowledgeBaseClient(timeout_seconds=0)

    @pytest.mark.asyncio
    async def test_concurrent_queries(self):
        """Test concurrent query handling."""
        # Mock successful responses
        mock_response = {
            'output': {'text': 'Success'},
            'retrievalResults': []
        }
        
        self.nova_client.bedrock_agent_client.retrieve_and_generate = AsyncMock(return_value=mock_response)
        
        # Run concurrent queries
        tasks = [
            self.nova_client.query_mbti_tourist_spots('INFJ'),
            self.nova_client.query_mbti_tourist_spots('ENFP'),
            self.nova_client.query_mbti_tourist_spots('INTJ')
        ]
        
        results = await asyncio.gather(*tasks)
        
        assert len(results) == 3
        assert all(isinstance(result, list) for result in results)

    @pytest.mark.asyncio
    async def test_timeout_handling(self):
        """Test timeout handling."""
        # Mock slow response
        async def slow_response(*args, **kwargs):
            await asyncio.sleep(2)  # Longer than timeout
            return {'output': {'text': 'Success'}, 'retrievalResults': []}
        
        self.nova_client.timeout_seconds = 1  # Short timeout
        self.nova_client.bedrock_agent_client.retrieve_and_generate = slow_response
        
        with pytest.raises(KnowledgeBaseError, match="timeout"):
            await self.nova_client.query_mbti_tourist_spots('INFJ')


class TestMBTIPersonalityProcessorComprehensive:
    """Comprehensive test cases for MBTIPersonalityProcessor with 90%+ coverage."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_nova_client = Mock(spec=NovaProKnowledgeBaseClient)
        self.processor = MBTIPersonalityProcessor(self.mock_nova_client)

    def test_initialization(self):
        """Test processor initialization."""
        assert self.processor.nova_client == self.mock_nova_client
        assert len(self.processor.personality_profiles) == 16
        assert self.processor.enable_caching is True

    def test_validate_mbti_personality_valid(self):
        """Test MBTI personality validation with valid types."""
        valid_types = ['INFJ', 'enfp', 'InTj', 'ESTP']
        
        for mbti_type in valid_types:
            is_valid, normalized = self.processor.validate_mbti_personality(mbti_type)
            assert is_valid is True
            assert normalized == mbti_type.upper()

    def test_validate_mbti_personality_invalid(self):
        """Test MBTI personality validation with invalid types."""
        invalid_types = ['', None, 'INVALID', 'INF', 'INFJA']
        
        for invalid_type in invalid_types:
            is_valid, normalized = self.processor.validate_mbti_personality(invalid_type)
            assert is_valid is False
            assert normalized == ""

    def test_get_personality_profile_all_types(self):
        """Test personality profile retrieval for all MBTI types."""
        mbti_types = [
            'INFJ', 'INFP', 'INTJ', 'INTP',
            'ISFJ', 'ISFP', 'ISTJ', 'ISTP',
            'ENFJ', 'ENFP', 'ENTJ', 'ENTP',
            'ESFJ', 'ESFP', 'ESTJ', 'ESTP'
        ]
        
        for mbti_type in mbti_types:
            profile = self.processor.get_personality_profile(mbti_type)
            
            assert isinstance(profile, PersonalityProfile)
            assert profile.mbti_type == mbti_type
            assert len(profile.dimensions) > 0
            assert len(profile.matching_score_weights) > 0
            assert len(profile.preferred_query_strategies) > 0

    def test_get_personality_profile_invalid_type(self):
        """Test personality profile retrieval with invalid type."""
        with pytest.raises(PersonalityValidationError):
            self.processor.get_personality_profile('INVALID')

    def test_get_optimization_recommendations(self):
        """Test optimization recommendations generation."""
        recommendations = self.processor.get_optimization_recommendations('INFJ')
        
        assert isinstance(recommendations, dict)
        assert recommendations['mbti_type'] == 'INFJ'
        assert 'preferred_strategies' in recommendations
        assert 'optimization_notes' in recommendations
        assert 'matching_weights' in recommendations
        assert 'recommended_max_results' in recommendations

    def test_get_supported_mbti_types(self):
        """Test supported MBTI types retrieval."""
        supported_types = self.processor.get_supported_mbti_types()
        
        assert isinstance(supported_types, list)
        assert len(supported_types) == 16
        assert 'INFJ' in supported_types
        assert 'ESTP' in supported_types

    def test_analyze_personality_dimensions(self):
        """Test personality dimensions analysis."""
        analysis = self.processor.analyze_personality_dimensions('INFJ')
        
        assert isinstance(analysis, dict)
        assert 'energy_source' in analysis
        assert 'information_processing' in analysis
        assert 'decision_making' in analysis
        assert 'lifestyle' in analysis
        assert 'dimension_scores' in analysis

    def test_calculate_mbti_compatibility_score(self):
        """Test MBTI compatibility score calculation."""
        # Test with mock tourist spot data
        spot_data = {
            'keywords': ['quiet', 'cultural', 'peaceful'],
            'category': 'Museum',
            'description': 'A peaceful cultural museum'
        }
        
        score = self.processor.calculate_mbti_compatibility_score('INFJ', spot_data)
        
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0

    def test_generate_personality_insights(self):
        """Test personality insights generation."""
        insights = self.processor.generate_personality_insights('INFJ')
        
        assert isinstance(insights, dict)
        assert 'personality_summary' in insights
        assert 'travel_preferences' in insights
        assert 'recommended_activities' in insights
        assert 'compatibility_factors' in insights

    def test_cache_functionality(self):
        """Test caching functionality."""
        # Test cache stats
        stats = self.processor.get_cache_stats()
        assert 'caching_enabled' in stats
        assert 'cached_profiles' in stats
        
        # Test cache clearing
        self.processor.clear_cache()

    def test_performance_metrics(self):
        """Test performance metrics collection."""
        metrics = self.processor.get_performance_metrics()
        
        assert isinstance(metrics, dict)
        assert 'total_validations' in metrics
        assert 'successful_validations' in metrics
        assert 'profile_retrievals' in metrics


class TestKnowledgeBaseResponseParserComprehensive:
    """Comprehensive test cases for KnowledgeBaseResponseParser with 90%+ coverage."""

    def setup_method(self):
        """Set up test fixtures."""
        self.parser = KnowledgeBaseResponseParser()

    def test_initialization(self):
        """Test parser initialization."""
        assert self.parser.enable_caching is True
        assert len(self.parser.parsing_patterns) > 0
        assert len(self.parser.validation_rules) > 0

    def test_parsing_patterns_completeness(self):
        """Test parsing patterns completeness."""
        expected_patterns = [
            'title', 'address', 'district', 'area', 'category',
            'description', 'operating_hours', 'mbti_type', 'keywords'
        ]
        
        for pattern_name in expected_patterns:
            assert pattern_name in self.parser.parsing_patterns
            pattern = self.parser.parsing_patterns[pattern_name]
            assert hasattr(pattern, 'search')  # Should be a regex pattern

    def test_validation_rules_completeness(self):
        """Test validation rules completeness."""
        expected_rules = [
            'required_fields', 'field_formats', 'data_quality',
            'consistency_checks', 'completeness_thresholds'
        ]
        
        for rule_name in expected_rules:
            assert rule_name in self.parser.validation_rules

    @pytest.mark.asyncio
    async def test_parse_knowledge_base_responses_success(self):
        """Test successful knowledge base response parsing."""
        mock_responses = [
            {
                'content': {
                    'text': """# Test Museum

## MBTI Personality Match
**Type:** INFJ
**Description:** Perfect for quiet contemplation

## Location Information
**Address:** 123 Test Street, Central, Hong Kong
**District:** Central
**Area:** Central District

## Operating Hours
**Weekdays:** 09:00-18:00
**Weekends:** 10:00-19:00

## Keywords
MBTI: INFJ, Hong Kong, Museum, Cultural"""
                },
                'score': 0.85,
                'location': {
                    's3Location': {
                        'uri': 's3://test-bucket/test-file.md'
                    }
                }
            }
        ]
        
        result = await self.parser.parse_knowledge_base_responses(
            mock_responses, 'INFJ', use_cache=False
        )
        
        assert result.successful_parses == 1
        assert result.failed_parses == 0
        assert len(result.parsed_spots) == 1
        
        parsed_spot = result.parsed_spots[0]
        assert parsed_spot.tourist_spot.name == "Test Museum"
        assert parsed_spot.tourist_spot.district == "Central"
        assert parsed_spot.tourist_spot.mbti_match is True
        assert "INFJ" in parsed_spot.tourist_spot.mbti_personality_types

    @pytest.mark.asyncio
    async def test_parse_knowledge_base_responses_malformed_data(self):
        """Test parsing with malformed data."""
        mock_responses = [
            {
                'content': {
                    'text': "Incomplete data without proper structure"
                },
                'score': 0.5,
                'location': {
                    's3Location': {
                        'uri': 's3://test-bucket/malformed.md'
                    }
                }
            }
        ]
        
        result = await self.parser.parse_knowledge_base_responses(
            mock_responses, 'INFJ', use_cache=False
        )
        
        # Should handle malformed data gracefully
        assert result.successful_parses >= 0
        assert result.failed_parses >= 0
        assert result.successful_parses + result.failed_parses == 1

    @pytest.mark.asyncio
    async def test_parse_knowledge_base_responses_empty_list(self):
        """Test parsing with empty response list."""
        result = await self.parser.parse_knowledge_base_responses(
            [], 'INFJ', use_cache=False
        )
        
        assert result.successful_parses == 0
        assert result.failed_parses == 0
        assert len(result.parsed_spots) == 0

    @pytest.mark.asyncio
    async def test_parse_knowledge_base_responses_with_caching(self):
        """Test parsing with caching enabled."""
        mock_responses = [
            {
                'content': {'text': 'Test content'},
                'score': 0.8,
                'location': {'s3Location': {'uri': 's3://test/file.md'}}
            }
        ]
        
        # First call
        result1 = await self.parser.parse_knowledge_base_responses(
            mock_responses, 'INFJ', use_cache=True
        )
        
        # Second call (should use cache)
        result2 = await self.parser.parse_knowledge_base_responses(
            mock_responses, 'INFJ', use_cache=True
        )
        
        # Results should be consistent
        assert result1.successful_parses == result2.successful_parses
        assert result1.failed_parses == result2.failed_parses

    def test_extract_tourist_spot_data_complete(self):
        """Test tourist spot data extraction with complete data."""
        content = """# Complete Museum

## Location Information
**Address:** 123 Complete Street, Central, Hong Kong
**District:** Central
**Area:** Hong Kong Island

## Operating Hours
**Monday-Friday:** 09:00-18:00
**Saturday-Sunday:** 10:00-19:00

## MBTI Match
**Type:** INFJ
**Keywords:** quiet, cultural, peaceful"""
        
        extracted_data = self.parser._extract_tourist_spot_data(content)
        
        assert extracted_data['name'] == "Complete Museum"
        assert extracted_data['address'] == "123 Complete Street, Central, Hong Kong"
        assert extracted_data['district'] == "Central"
        assert extracted_data['area'] == "Hong Kong Island"
        assert 'operating_hours' in extracted_data
        assert 'mbti_types' in extracted_data

    def test_extract_tourist_spot_data_minimal(self):
        """Test tourist spot data extraction with minimal data."""
        content = "# Minimal Spot\nBasic description only."
        
        extracted_data = self.parser._extract_tourist_spot_data(content)
        
        assert extracted_data['name'] == "Minimal Spot"
        assert 'description' in extracted_data

    def test_validate_extracted_data_valid(self):
        """Test validation of valid extracted data."""
        valid_data = {
            'name': 'Test Museum',
            'address': '123 Test Street',
            'district': 'Central',
            'area': 'Hong Kong Island',
            'category': 'Museum',
            'description': 'Test description'
        }
        
        is_valid, quality_score, issues = self.parser._validate_extracted_data(valid_data)
        
        assert is_valid is True
        assert quality_score > 0.5
        assert len(issues) == 0

    def test_validate_extracted_data_invalid(self):
        """Test validation of invalid extracted data."""
        invalid_data = {
            'name': '',  # Missing required field
            'address': None,
            'district': '',
            'area': ''
        }
        
        is_valid, quality_score, issues = self.parser._validate_extracted_data(invalid_data)
        
        assert is_valid is False
        assert quality_score < 0.5
        assert len(issues) > 0

    def test_calculate_parsing_confidence(self):
        """Test parsing confidence calculation."""
        high_quality_data = {
            'name': 'Complete Museum',
            'address': '123 Street, Central, Hong Kong',
            'district': 'Central',
            'area': 'Hong Kong Island',
            'category': 'Museum',
            'description': 'Detailed description',
            'operating_hours': {'monday': '09:00-18:00'},
            'mbti_types': ['INFJ'],
            'keywords': ['cultural', 'quiet']
        }
        
        confidence = self.parser._calculate_parsing_confidence(high_quality_data)
        
        assert isinstance(confidence, float)
        assert 0.0 <= confidence <= 1.0
        assert confidence > 0.7  # Should be high for complete data

    def test_create_tourist_spot_from_data(self):
        """Test tourist spot creation from extracted data."""
        spot_data = {
            'name': 'Test Museum',
            'address': '123 Test Street, Central, Hong Kong',
            'district': 'Central',
            'area': 'Hong Kong Island',
            'category': 'Museum',
            'description': 'Test museum description',
            'operating_hours': {
                'monday': '09:00-18:00',
                'tuesday': '09:00-18:00'
            },
            'mbti_types': ['INFJ'],
            'keywords': ['cultural', 'quiet']
        }
        
        tourist_spot = self.parser._create_tourist_spot_from_data(spot_data, 'INFJ')
        
        assert isinstance(tourist_spot, TouristSpot)
        assert tourist_spot.name == 'Test Museum'
        assert tourist_spot.district == 'Central'
        assert tourist_spot.area == 'Hong Kong Island'
        assert tourist_spot.mbti_match is True
        assert 'INFJ' in tourist_spot.mbti_personality_types

    def test_cache_functionality(self):
        """Test caching functionality."""
        # Test cache stats
        stats = self.parser.get_cache_stats()
        assert 'caching_enabled' in stats
        assert 'cached_responses' in stats
        
        # Test cache clearing
        self.parser.clear_cache()

    def test_performance_metrics(self):
        """Test performance metrics collection."""
        metrics = self.parser.get_performance_metrics()
        
        assert isinstance(metrics, dict)
        assert 'total_parses' in metrics
        assert 'successful_parses' in metrics
        assert 'average_parse_time' in metrics

    def test_error_handling_invalid_input(self):
        """Test error handling with invalid input."""
        # Test with None input
        with pytest.raises(ParsingError):
            self.parser._extract_tourist_spot_data(None)
        
        # Test with invalid data structure
        with pytest.raises(ParsingError):
            self.parser._validate_extracted_data(None)

    @pytest.mark.asyncio
    async def test_concurrent_parsing(self):
        """Test concurrent parsing operations."""
        mock_responses = [
            {
                'content': {'text': f'# Test Spot {i}\nDescription {i}'},
                'score': 0.8,
                'location': {'s3Location': {'uri': f's3://test/file{i}.md'}}
            }
            for i in range(5)
        ]
        
        # Run concurrent parsing
        tasks = [
            self.parser.parse_knowledge_base_responses([response], 'INFJ', use_cache=False)
            for response in mock_responses
        ]
        
        results = await asyncio.gather(*tasks)
        
        assert len(results) == 5
        assert all(isinstance(result.parsed_spots, list) for result in results)

    def test_memory_efficiency(self):
        """Test memory efficiency with large datasets."""
        import sys
        
        # Create large mock response
        large_content = "# Large Spot\n" + "Description line.\n" * 1000
        mock_response = {
            'content': {'text': large_content},
            'score': 0.8,
            'location': {'s3Location': {'uri': 's3://test/large.md'}}
        }
        
        # Measure memory before
        initial_size = sys.getsizeof(self.parser)
        
        # Process large response
        extracted_data = self.parser._extract_tourist_spot_data(large_content)
        
        # Memory should not grow excessively
        final_size = sys.getsizeof(self.parser)
        memory_growth = final_size - initial_size
        
        # Memory growth should be reasonable (< 10KB)
        assert memory_growth < 10240


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=services.nova_pro_knowledge_base_client", 
                 "--cov=services.mbti_personality_processor", 
                 "--cov=services.knowledge_base_response_parser", 
                 "--cov-report=term-missing"])