"""Nova Pro Knowledge Base Client for MBTI Travel Assistant.

This module implements the NovaProKnowledgeBaseClient class that uses Amazon Nova Pro
foundation model to query the OpenSearch knowledge base for personality-matched tourist spots.
Provides optimized MBTI-specific query prompts and efficient knowledge base query strategies.

Requirements: 5.1, 5.2, 5.3
"""

import asyncio
import json
import time
import random
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass
from enum import Enum
import boto3
from botocore.exceptions import ClientError, BotoCoreError, EndpointConnectionError, NoCredentialsError
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
    
    class TouristSpotOperatingHours:
        pass


logger = structlog.get_logger(__name__)


class QueryStrategy(Enum):
    """Query strategies for knowledge base searches."""
    BROAD_PERSONALITY = "broad_personality"
    SPECIFIC_TRAITS = "specific_traits"
    LOCATION_FOCUSED = "location_focused"
    CATEGORY_BASED = "category_based"


class KnowledgeBaseErrorType(Enum):
    """Knowledge base error types for classification."""
    CONNECTION_ERROR = "connection_error"
    AUTHENTICATION_ERROR = "authentication_error"
    AUTHORIZATION_ERROR = "authorization_error"
    THROTTLING_ERROR = "throttling_error"
    VALIDATION_ERROR = "validation_error"
    PARSING_ERROR = "parsing_error"
    TIMEOUT_ERROR = "timeout_error"
    SERVICE_UNAVAILABLE = "service_unavailable"
    UNKNOWN_ERROR = "unknown_error"


@dataclass
class RetryConfig:
    """Configuration for retry logic with exponential backoff."""
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True


@dataclass
class FallbackConfig:
    """Configuration for fallback strategies."""
    enable_cache_fallback: bool = True
    enable_simplified_queries: bool = True
    enable_partial_results: bool = True
    min_results_threshold: int = 5


@dataclass
class MBTITraits:
    """MBTI personality traits for query optimization."""
    energy_source: str  # Extraversion vs Introversion
    information_processing: str  # Sensing vs Intuition
    decision_making: str  # Thinking vs Feeling
    lifestyle: str  # Judging vs Perceiving
    description: str
    preferences: List[str]
    suitable_activities: List[str]
    environment_preferences: List[str]


@dataclass
class QueryResult:
    """Result from a knowledge base query."""
    tourist_spot: TouristSpot
    relevance_score: float
    s3_uri: str
    query_used: str
    strategy: QueryStrategy


class NovaProKnowledgeBaseClient:
    """Nova Pro client for knowledge base queries with MBTI optimization.
    
    This client uses Amazon Nova Pro foundation model to query the OpenSearch
    knowledge base for personality-matched tourist spots. It implements optimized
    query strategies based on test_single_mbti_type.py patterns but with improved
    performance for faster response times.
    
    Attributes:
        knowledge_base_id: Amazon Bedrock Knowledge Base ID
        region: AWS region for Bedrock services
        bedrock_runtime_client: Bedrock Agent Runtime client
        bedrock_client: Bedrock client for model invocation
        nova_pro_model_id: Nova Pro model identifier
        mbti_traits_map: Mapping of MBTI types to personality traits
    """
    
    def __init__(
        self,
        knowledge_base_id: str = "RCWW86CLM9",
        region: str = "us-east-1",
        nova_pro_model_id: str = "amazon.nova-pro-v1:0",
        retry_config: Optional[RetryConfig] = None,
        fallback_config: Optional[FallbackConfig] = None
    ):
        """Initialize Nova Pro Knowledge Base Client.
        
        Args:
            knowledge_base_id: Bedrock Knowledge Base ID
            region: AWS region
            nova_pro_model_id: Nova Pro model identifier
            retry_config: Configuration for retry logic
            fallback_config: Configuration for fallback strategies
        """
        self.knowledge_base_id = knowledge_base_id
        self.region = region
        self.nova_pro_model_id = nova_pro_model_id
        
        # Error handling and resilience configuration
        self.retry_config = retry_config or RetryConfig()
        self.fallback_config = fallback_config or FallbackConfig()
        
        # Initialize AWS clients with error handling
        try:
            self.bedrock_runtime_client = boto3.client(
                'bedrock-agent-runtime',
                region_name=region
            )
            self.bedrock_client = boto3.client(
                'bedrock-runtime',
                region_name=region
            )
        except NoCredentialsError as e:
            logger.error("AWS credentials not found", error=str(e))
            raise
        except Exception as e:
            logger.error("Failed to initialize AWS clients", error=str(e))
            raise
        
        # Initialize MBTI traits mapping
        self._initialize_mbti_traits_map()
        
        # Query performance tracking and error metrics
        self._query_cache: Dict[str, List[QueryResult]] = {}
        self._performance_metrics: Dict[str, Any] = {}
        self._error_metrics: Dict[str, Any] = {
            'total_errors': 0,
            'error_types': {},
            'retry_attempts': 0,
            'fallback_activations': 0,
            'last_error_time': None
        }
        
        logger.info(
            "Nova Pro Knowledge Base Client initialized",
            knowledge_base_id=knowledge_base_id,
            region=region,
            model_id=nova_pro_model_id,
            retry_config=retry_config,
            fallback_config=fallback_config
        )
    
    def _initialize_mbti_traits_map(self) -> None:
        """Initialize MBTI personality traits mapping for query optimization."""
        self.mbti_traits_map = {
            'INFJ': MBTITraits(
                energy_source='Introversion',
                information_processing='Intuition',
                decision_making='Feeling',
                lifestyle='Judging',
                description='Quiet, meaningful experiences; cultural sites; peaceful environments',
                preferences=[
                    'meaningful cultural experiences',
                    'quiet contemplative spaces',
                    'artistic and creative venues',
                    'historical significance',
                    'peaceful natural settings'
                ],
                suitable_activities=[
                    'museums and galleries',
                    'cultural centers',
                    'quiet gardens',
                    'historical sites',
                    'art exhibitions'
                ],
                environment_preferences=[
                    'serene and peaceful',
                    'culturally rich',
                    'intellectually stimulating',
                    'not overcrowded',
                    'authentic experiences'
                ]
            ),
            'ENFP': MBTITraits(
                energy_source='Extraversion',
                information_processing='Intuition',
                decision_making='Feeling',
                lifestyle='Perceiving',
                description='Vibrant, social experiences; interactive attractions; diverse activities',
                preferences=[
                    'vibrant social experiences',
                    'interactive attractions',
                    'diverse activities',
                    'spontaneous exploration',
                    'people-centered experiences'
                ],
                suitable_activities=[
                    'markets and festivals',
                    'interactive museums',
                    'social venues',
                    'entertainment districts',
                    'cultural performances'
                ],
                environment_preferences=[
                    'lively and energetic',
                    'socially engaging',
                    'variety and options',
                    'flexible scheduling',
                    'inspiring and uplifting'
                ]
            ),
            'INTJ': MBTITraits(
                energy_source='Introversion',
                information_processing='Intuition',
                decision_making='Thinking',
                lifestyle='Judging',
                description='Strategic, educational experiences; museums; architectural sites',
                preferences=[
                    'strategic learning experiences',
                    'architectural marvels',
                    'systematic exploration',
                    'educational content',
                    'efficient planning'
                ],
                suitable_activities=[
                    'science museums',
                    'architectural tours',
                    'technology centers',
                    'strategic viewpoints',
                    'educational institutions'
                ],
                environment_preferences=[
                    'well-organized',
                    'intellectually challenging',
                    'architecturally significant',
                    'efficient access',
                    'comprehensive information'
                ]
            ),
            'ESTP': MBTITraits(
                energy_source='Extraversion',
                information_processing='Sensing',
                decision_making='Thinking',
                lifestyle='Perceiving',
                description='Active, adventurous experiences; outdoor activities; dynamic environments',
                preferences=[
                    'active adventures',
                    'hands-on experiences',
                    'dynamic environments',
                    'immediate gratification',
                    'physical activities'
                ],
                suitable_activities=[
                    'outdoor adventures',
                    'sports venues',
                    'action-packed attractions',
                    'dynamic markets',
                    'entertainment complexes'
                ],
                environment_preferences=[
                    'high energy',
                    'physically engaging',
                    'immediate rewards',
                    'social interaction',
                    'variety and excitement'
                ]
            )
            # Additional MBTI types can be added here following the same pattern
        }
        
        # Add remaining MBTI types with basic traits
        remaining_types = [
            'INTP', 'ENTJ', 'ENTP', 'INFP', 'ENFJ',
            'ISTJ', 'ISFJ', 'ESTJ', 'ESFJ', 'ISTP', 'ISFP', 'ESFP'
        ]
        
        for mbti_type in remaining_types:
            if mbti_type not in self.mbti_traits_map:
                self.mbti_traits_map[mbti_type] = self._generate_basic_traits(mbti_type)
    
    def _generate_basic_traits(self, mbti_type: str) -> MBTITraits:
        """Generate basic traits for MBTI types not explicitly defined.
        
        Args:
            mbti_type: 4-character MBTI code
            
        Returns:
            MBTITraits object with basic characteristics
        """
        # Extract individual preferences
        energy = 'Extraversion' if mbti_type[0] == 'E' else 'Introversion'
        info = 'Intuition' if mbti_type[1] == 'N' else 'Sensing'
        decision = 'Feeling' if mbti_type[2] == 'F' else 'Thinking'
        lifestyle = 'Judging' if mbti_type[3] == 'J' else 'Perceiving'
        
        return MBTITraits(
            energy_source=energy,
            information_processing=info,
            decision_making=decision,
            lifestyle=lifestyle,
            description=f'{mbti_type} personality preferences',
            preferences=[f'{energy.lower()} experiences', f'{info.lower()} activities'],
            suitable_activities=['varied attractions', 'diverse experiences'],
            environment_preferences=['suitable environments', 'appropriate settings']
        )
    
    def validate_mbti_format(self, mbti_personality: str) -> bool:
        """Validate MBTI personality format.
        
        Args:
            mbti_personality: 4-character MBTI code
            
        Returns:
            True if valid format, False otherwise
        """
        if not mbti_personality or not isinstance(mbti_personality, str):
            return False
        
        mbti_clean = mbti_personality.strip().upper()
        
        if len(mbti_clean) != 4:
            return False
        
        valid_types = {
            'INTJ', 'INTP', 'ENTJ', 'ENTP',
            'INFJ', 'INFP', 'ENFJ', 'ENFP',
            'ISTJ', 'ISFJ', 'ESTJ', 'ESFJ',
            'ISTP', 'ISFP', 'ESTP', 'ESFP'
        }
        
        return mbti_clean in valid_types
    
    def _classify_error(self, error: Exception) -> KnowledgeBaseErrorType:
        """Classify error type for appropriate handling.
        
        Args:
            error: Exception to classify
            
        Returns:
            KnowledgeBaseErrorType enum value
        """
        error_str = str(error).lower()
        
        if isinstance(error, NoCredentialsError):
            return KnowledgeBaseErrorType.AUTHENTICATION_ERROR
        elif isinstance(error, EndpointConnectionError):
            return KnowledgeBaseErrorType.CONNECTION_ERROR
        elif isinstance(error, ClientError):
            error_code = error.response.get('Error', {}).get('Code', '').lower()
            
            if error_code in ['accessdenied', 'forbidden']:
                return KnowledgeBaseErrorType.AUTHORIZATION_ERROR
            elif error_code in ['throttling', 'throttlingexception', 'requestlimitexceeded']:
                return KnowledgeBaseErrorType.THROTTLING_ERROR
            elif error_code in ['validationexception', 'invalidparameter']:
                return KnowledgeBaseErrorType.VALIDATION_ERROR
            elif error_code in ['serviceunavailable', 'internalerror']:
                return KnowledgeBaseErrorType.SERVICE_UNAVAILABLE
            elif 'timeout' in error_code:
                return KnowledgeBaseErrorType.TIMEOUT_ERROR
            else:
                return KnowledgeBaseErrorType.UNKNOWN_ERROR
        elif isinstance(error, (ConnectionError, TimeoutError)):
            if 'timeout' in error_str:
                return KnowledgeBaseErrorType.TIMEOUT_ERROR
            else:
                return KnowledgeBaseErrorType.CONNECTION_ERROR
        elif isinstance(error, ValueError):
            return KnowledgeBaseErrorType.VALIDATION_ERROR
        elif 'json' in error_str or 'parse' in error_str:
            return KnowledgeBaseErrorType.PARSING_ERROR
        else:
            return KnowledgeBaseErrorType.UNKNOWN_ERROR
    
    def _should_retry(self, error: Exception, attempt: int) -> bool:
        """Determine if an error should be retried.
        
        Args:
            error: Exception that occurred
            attempt: Current attempt number (0-based)
            
        Returns:
            True if should retry, False otherwise
        """
        if attempt >= self.retry_config.max_retries:
            return False
        
        error_type = self._classify_error(error)
        
        # Retry on transient errors
        retryable_errors = {
            KnowledgeBaseErrorType.CONNECTION_ERROR,
            KnowledgeBaseErrorType.THROTTLING_ERROR,
            KnowledgeBaseErrorType.TIMEOUT_ERROR,
            KnowledgeBaseErrorType.SERVICE_UNAVAILABLE
        }
        
        return error_type in retryable_errors
    
    def _calculate_retry_delay(self, attempt: int) -> float:
        """Calculate delay before retry using exponential backoff.
        
        Args:
            attempt: Current attempt number (0-based)
            
        Returns:
            Delay in seconds
        """
        delay = self.retry_config.base_delay * (
            self.retry_config.exponential_base ** attempt
        )
        delay = min(delay, self.retry_config.max_delay)
        
        # Add jitter to prevent thundering herd
        if self.retry_config.jitter:
            jitter = random.uniform(0, delay * 0.1)
            delay += jitter
        
        return delay
    
    async def _execute_with_retry(
        self,
        operation_name: str,
        operation_func,
        *args,
        **kwargs
    ) -> Any:
        """Execute an operation with retry logic and error handling.
        
        Args:
            operation_name: Name of the operation for logging
            operation_func: Function to execute
            *args: Arguments for the operation function
            **kwargs: Keyword arguments for the operation function
            
        Returns:
            Result of the operation
            
        Raises:
            Exception: If all retry attempts fail
        """
        last_error = None
        
        for attempt in range(self.retry_config.max_retries + 1):
            try:
                if attempt > 0:
                    delay = self._calculate_retry_delay(attempt - 1)
                    logger.info(
                        f"Retrying {operation_name}",
                        attempt=attempt,
                        delay=delay,
                        max_retries=self.retry_config.max_retries
                    )
                    await asyncio.sleep(delay)
                    self._error_metrics['retry_attempts'] += 1
                
                result = await operation_func(*args, **kwargs)
                
                # Log successful retry
                if attempt > 0:
                    logger.info(
                        f"{operation_name} succeeded after retry",
                        attempt=attempt,
                        total_attempts=attempt + 1
                    )
                
                return result
                
            except Exception as error:
                last_error = error
                error_type = self._classify_error(error)
                
                # Update error metrics
                self._error_metrics['total_errors'] += 1
                self._error_metrics['error_types'][error_type.value] = (
                    self._error_metrics['error_types'].get(error_type.value, 0) + 1
                )
                self._error_metrics['last_error_time'] = time.time()
                
                logger.warning(
                    f"{operation_name} failed",
                    attempt=attempt + 1,
                    error_type=error_type.value,
                    error=str(error)
                )
                
                # Check if we should retry
                if not self._should_retry(error, attempt):
                    logger.error(
                        f"{operation_name} failed permanently",
                        total_attempts=attempt + 1,
                        error_type=error_type.value,
                        error=str(error)
                    )
                    break
        
        # All retries exhausted, raise the last error
        raise last_error
    
    def _build_optimized_queries(self, mbti_personality: str) -> List[Dict[str, Any]]:
        """Build optimized query prompts for specific MBTI type.
        
        Args:
            mbti_personality: 4-character MBTI code
            
        Returns:
            List of query dictionaries with strategy and prompt
        """
        mbti_upper = mbti_personality.upper().strip()
        traits = self.mbti_traits_map.get(mbti_upper)
        
        if not traits:
            logger.warning(f"No traits found for MBTI type: {mbti_upper}")
            return self._build_fallback_queries(mbti_upper)
        
        queries = []
        
        # Strategy 1: Broad personality-based queries
        queries.extend([
            {
                'strategy': QueryStrategy.BROAD_PERSONALITY,
                'prompt': f"Find Hong Kong tourist attractions suitable for {mbti_upper} personality type. "
                         f"Focus on {traits.description}. Include attractions that offer "
                         f"{', '.join(traits.preferences[:3])}.",
                'max_results': 25
            },
            {
                'strategy': QueryStrategy.BROAD_PERSONALITY,
                'prompt': f"Hong Kong attractions for {mbti_upper} {traits.energy_source.lower()} "
                         f"{traits.information_processing.lower()} {traits.decision_making.lower()} "
                         f"{traits.lifestyle.lower()} personality. Suitable for visitors who prefer "
                         f"{', '.join(traits.environment_preferences[:2])}.",
                'max_results': 20
            }
        ])
        
        # Strategy 2: Specific trait-based queries
        for preference in traits.preferences[:3]:
            queries.append({
                'strategy': QueryStrategy.SPECIFIC_TRAITS,
                'prompt': f"Hong Kong tourist spots offering {preference} suitable for {mbti_upper} personality",
                'max_results': 15
            })
        
        # Strategy 3: Activity-based queries
        for activity in traits.suitable_activities[:3]:
            queries.append({
                'strategy': QueryStrategy.CATEGORY_BASED,
                'prompt': f"Hong Kong {activity} attractions for {mbti_upper} personality type",
                'max_results': 15
            })
        
        # Strategy 4: Location-focused with personality context
        queries.append({
            'strategy': QueryStrategy.LOCATION_FOCUSED,
            'prompt': f"Hong Kong Central district attractions suitable for {mbti_upper} personality "
                     f"preferring {traits.environment_preferences[0]} environments",
            'max_results': 15
        })
        
        return queries
    
    def _build_fallback_queries(self, mbti_personality: str) -> List[Dict[str, Any]]:
        """Build fallback queries for unknown MBTI types.
        
        Args:
            mbti_personality: 4-character MBTI code
            
        Returns:
            List of basic query dictionaries
        """
        return [
            {
                'strategy': QueryStrategy.BROAD_PERSONALITY,
                'prompt': f"Hong Kong tourist attractions for {mbti_personality} personality type",
                'max_results': 25
            },
            {
                'strategy': QueryStrategy.LOCATION_FOCUSED,
                'prompt': f"Hong Kong attractions suitable for {mbti_personality} visitors",
                'max_results': 20
            }
        ]
    
    async def query_mbti_tourist_spots(
        self,
        mbti_personality: str,
        use_cache: bool = True,
        max_total_results: int = 50
    ) -> List[QueryResult]:
        """Query knowledge base for MBTI-matched tourist spots using Nova Pro.
        
        Args:
            mbti_personality: 4-character MBTI code (e.g., "INFJ", "ENFP")
            use_cache: Whether to use cached results if available
            max_total_results: Maximum number of total results to return
            
        Returns:
            List of QueryResult objects with tourist spots and metadata
            
        Raises:
            ValueError: If MBTI personality format is invalid
            ClientError: If AWS service calls fail
        """
        start_time = time.time()
        
        # Validate MBTI format
        if not self.validate_mbti_format(mbti_personality):
            raise ValueError(
                f"Invalid MBTI personality format: '{mbti_personality}'. "
                "Expected 4-character code like INFJ, ENFP."
            )
        
        mbti_upper = mbti_personality.upper().strip()
        cache_key = f"{mbti_upper}_{max_total_results}"
        
        # Check cache
        if use_cache and cache_key in self._query_cache:
            logger.info(
                "Returning cached results for MBTI query",
                mbti_type=mbti_upper,
                cached_results=len(self._query_cache[cache_key])
            )
            return self._query_cache[cache_key][:max_total_results]
        
        logger.info(
            "Starting Nova Pro knowledge base query",
            mbti_type=mbti_upper,
            max_results=max_total_results
        )
        
        try:
            # Execute main query logic with retry handling
            all_results = await self._execute_with_retry(
                "knowledge_base_query",
                self._execute_main_query_logic,
                mbti_upper,
                max_total_results
            )
            
            # Sort results by relevance score
            all_results.sort(key=lambda x: x.relevance_score, reverse=True)
            
            # Cache results
            if use_cache:
                self._query_cache[cache_key] = all_results
            
            # Update performance metrics
            execution_time = time.time() - start_time
            self._performance_metrics[mbti_upper] = {
                'execution_time': execution_time,
                'results_found': len(all_results),
                'timestamp': time.time(),
                'fallback_used': False
            }
            
            logger.info(
                "Nova Pro knowledge base query completed successfully",
                mbti_type=mbti_upper,
                execution_time=f"{execution_time:.2f}s",
                results_found=len(all_results)
            )
            
            return all_results[:max_total_results]
            
        except Exception as primary_error:
            logger.error(
                "Primary knowledge base query failed, attempting fallback",
                mbti_type=mbti_upper,
                error=str(primary_error),
                error_type=self._classify_error(primary_error).value
            )
            
            # Attempt fallback strategies
            try:
                fallback_results = await self._get_fallback_results(
                    mbti_upper, max_total_results, primary_error
                )
                
                # Update performance metrics for fallback
                execution_time = time.time() - start_time
                self._performance_metrics[mbti_upper] = {
                    'execution_time': execution_time,
                    'results_found': len(fallback_results),
                    'timestamp': time.time(),
                    'fallback_used': True,
                    'primary_error': str(primary_error)
                }
                
                if fallback_results:
                    logger.info(
                        "Fallback strategies successful",
                        mbti_type=mbti_upper,
                        execution_time=f"{execution_time:.2f}s",
                        fallback_results=len(fallback_results)
                    )
                    return fallback_results
                else:
                    logger.error(
                        "All fallback strategies failed",
                        mbti_type=mbti_upper,
                        primary_error=str(primary_error)
                    )
                    # Re-raise the original error
                    raise primary_error
                    
            except Exception as fallback_error:
                logger.error(
                    "Fallback strategies failed",
                    mbti_type=mbti_upper,
                    primary_error=str(primary_error),
                    fallback_error=str(fallback_error)
                )
                # Re-raise the original error
                raise primary_error
    
    async def _execute_main_query_logic(
        self,
        mbti_upper: str,
        max_total_results: int
    ) -> List[QueryResult]:
        """Execute the main query logic with error handling.
        
        Args:
            mbti_upper: MBTI personality type in uppercase
            max_total_results: Maximum number of results to return
            
        Returns:
            List of QueryResult objects
        """
        # Build optimized queries
        query_configs = self._build_optimized_queries(mbti_upper)
        
        all_results = []
        unique_s3_uris: Set[str] = set()
        query_count = 0
        
        for query_config in query_configs:
            if len(all_results) >= max_total_results:
                break
            
            try:
                query_results = await self._execute_single_query(
                    query_config['prompt'],
                    query_config['strategy'],
                    query_config['max_results'],
                    mbti_upper
                )
                
                # Add unique results
                new_results = 0
                for result in query_results:
                    if result.s3_uri not in unique_s3_uris and len(all_results) < max_total_results:
                        unique_s3_uris.add(result.s3_uri)
                        all_results.append(result)
                        new_results += 1
                
                query_count += 1
                logger.debug(
                    "Query executed",
                    query_num=query_count,
                    strategy=query_config['strategy'].value,
                    new_results=new_results,
                    total_results=len(all_results)
                )
                
            except Exception as e:
                logger.warning(
                    "Individual query execution failed",
                    query=query_config['prompt'][:50] + "...",
                    error=str(e)
                )
                # Continue with other queries instead of failing completely
                continue
        
        # Check if we got sufficient results
        if len(all_results) < self.fallback_config.min_results_threshold:
            raise ValueError(
                f"Insufficient results found: {len(all_results)} < {self.fallback_config.min_results_threshold}"
            )
        
        return all_results
        
        return all_results[:max_total_results]
    
    async def _get_fallback_results(
        self,
        mbti_personality: str,
        max_results: int,
        original_error: Exception
    ) -> List[QueryResult]:
        """Get fallback results when primary queries fail.
        
        Args:
            mbti_personality: MBTI personality type
            max_results: Maximum number of results to return
            original_error: The original error that triggered fallback
            
        Returns:
            List of fallback QueryResult objects
        """
        fallback_results = []
        self._error_metrics['fallback_activations'] += 1
        
        logger.info(
            "Activating fallback strategies",
            mbti_type=mbti_personality,
            original_error=str(original_error),
            fallback_config=self.fallback_config
        )
        
        # Strategy 1: Check cache for similar MBTI types
        if self.fallback_config.enable_cache_fallback:
            cache_results = await self._get_cache_fallback_results(
                mbti_personality, max_results
            )
            fallback_results.extend(cache_results)
            
            if len(fallback_results) >= self.fallback_config.min_results_threshold:
                logger.info(
                    "Cache fallback successful",
                    results_found=len(fallback_results)
                )
                return fallback_results[:max_results]
        
        # Strategy 2: Use simplified queries
        if self.fallback_config.enable_simplified_queries:
            simplified_results = await self._get_simplified_query_results(
                mbti_personality, max_results
            )
            fallback_results.extend(simplified_results)
            
            if len(fallback_results) >= self.fallback_config.min_results_threshold:
                logger.info(
                    "Simplified query fallback successful",
                    results_found=len(fallback_results)
                )
                return fallback_results[:max_results]
        
        # Strategy 3: Return partial results if available
        if self.fallback_config.enable_partial_results and fallback_results:
            logger.info(
                "Returning partial fallback results",
                results_found=len(fallback_results)
            )
            return fallback_results[:max_results]
        
        # No fallback results available
        logger.warning(
            "All fallback strategies failed",
            mbti_type=mbti_personality,
            original_error=str(original_error)
        )
        return []
    
    async def _get_cache_fallback_results(
        self,
        mbti_personality: str,
        max_results: int
    ) -> List[QueryResult]:
        """Get fallback results from cache for similar MBTI types.
        
        Args:
            mbti_personality: Target MBTI personality type
            max_results: Maximum number of results
            
        Returns:
            List of cached QueryResult objects
        """
        cache_results = []
        
        # Find similar MBTI types in cache
        similar_types = self._find_similar_mbti_types(mbti_personality)
        
        for similar_type in similar_types:
            cache_key = f"{similar_type}_{max_results}"
            if cache_key in self._query_cache:
                cached_results = self._query_cache[cache_key]
                
                # Mark as fallback results and update MBTI match
                for result in cached_results:
                    fallback_result = QueryResult(
                        tourist_spot=result.tourist_spot,
                        relevance_score=result.relevance_score * 0.8,  # Reduce score for fallback
                        s3_uri=result.s3_uri,
                        query_used=f"FALLBACK: {result.query_used}",
                        strategy=result.strategy
                    )
                    # Mark as non-MBTI match since it's from a different type
                    fallback_result.tourist_spot.mbti_match = False
                    cache_results.append(fallback_result)
                
                if len(cache_results) >= max_results:
                    break
        
        logger.info(
            "Cache fallback results retrieved",
            target_mbti=mbti_personality,
            similar_types=similar_types,
            results_found=len(cache_results)
        )
        
        return cache_results[:max_results]
    
    def _find_similar_mbti_types(self, mbti_personality: str) -> List[str]:
        """Find similar MBTI types for fallback purposes.
        
        Args:
            mbti_personality: Target MBTI personality type
            
        Returns:
            List of similar MBTI types in order of similarity
        """
        if len(mbti_personality) != 4:
            return []
        
        similar_types = []
        
        # Find types that share 3 out of 4 characteristics
        for cached_type in self._query_cache.keys():
            if '_' in cached_type:
                cached_mbti = cached_type.split('_')[0]
                if len(cached_mbti) == 4:
                    matches = sum(
                        1 for i in range(4) 
                        if mbti_personality[i] == cached_mbti[i]
                    )
                    if matches >= 3:
                        similar_types.append(cached_mbti)
        
        # Sort by similarity (more matches first)
        similar_types.sort(
            key=lambda t: sum(
                1 for i in range(4) 
                if mbti_personality[i] == t[i]
            ),
            reverse=True
        )
        
        return similar_types[:3]  # Return top 3 similar types
    
    async def _get_simplified_query_results(
        self,
        mbti_personality: str,
        max_results: int
    ) -> List[QueryResult]:
        """Get results using simplified queries as fallback.
        
        Args:
            mbti_personality: MBTI personality type
            max_results: Maximum number of results
            
        Returns:
            List of QueryResult objects from simplified queries
        """
        simplified_results = []
        
        # Use very basic queries that are less likely to fail
        simple_queries = [
            f"Hong Kong tourist attractions",
            f"Hong Kong sightseeing spots",
            f"Hong Kong travel destinations"
        ]
        
        for query_text in simple_queries:
            try:
                # Use a simpler query execution without complex processing
                response = self.bedrock_runtime_client.retrieve(
                    knowledgeBaseId=self.knowledge_base_id,
                    retrievalQuery={'text': query_text},
                    retrievalConfiguration={
                        'vectorSearchConfiguration': {
                            'numberOfResults': min(max_results, 10)
                        }
                    }
                )
                
                retrieval_results = response.get('retrievalResults', [])
                
                for result in retrieval_results:
                    try:
                        tourist_spot = self._parse_tourist_spot_from_result(
                            result, mbti_personality
                        )
                        
                        if tourist_spot:
                            # Mark as non-MBTI match since it's a simplified query
                            tourist_spot.mbti_match = False
                            
                            query_result = QueryResult(
                                tourist_spot=tourist_spot,
                                relevance_score=result.get('score', 0.0) * 0.6,  # Lower score for simplified
                                s3_uri=result['location']['s3Location']['uri'],
                                query_used=f"SIMPLIFIED: {query_text}",
                                strategy=QueryStrategy.LOCATION_FOCUSED
                            )
                            simplified_results.append(query_result)
                    
                    except Exception as e:
                        logger.debug(
                            "Failed to parse simplified query result",
                            error=str(e)
                        )
                        continue
                
                if len(simplified_results) >= max_results:
                    break
                    
            except Exception as e:
                logger.warning(
                    "Simplified query failed",
                    query=query_text,
                    error=str(e)
                )
                continue
        
        logger.info(
            "Simplified query fallback completed",
            results_found=len(simplified_results)
        )
        
        return simplified_results[:max_results]
    
    async def _execute_single_query(
        self,
        query_prompt: str,
        strategy: QueryStrategy,
        max_results: int,
        mbti_type: str
    ) -> List[QueryResult]:
        """Execute a single knowledge base query with error handling.
        
        Args:
            query_prompt: Query text to search for
            strategy: Query strategy being used
            max_results: Maximum results for this query
            mbti_type: MBTI personality type for filtering
            
        Returns:
            List of QueryResult objects
        """
        return await self._execute_with_retry(
            f"single_query_{strategy.value}",
            self._execute_single_query_impl,
            query_prompt,
            strategy,
            max_results,
            mbti_type
        )
    
    async def _execute_single_query_impl(
        self,
        query_prompt: str,
        strategy: QueryStrategy,
        max_results: int,
        mbti_type: str
    ) -> List[QueryResult]:
        """Implementation of single query execution.
        
        Args:
            query_prompt: Query text to search for
            strategy: Query strategy being used
            max_results: Maximum results for this query
            mbti_type: MBTI personality type for filtering
            
        Returns:
            List of QueryResult objects
        """
        try:
            response = self.bedrock_runtime_client.retrieve(
                knowledgeBaseId=self.knowledge_base_id,
                retrievalQuery={'text': query_prompt},
                retrievalConfiguration={
                    'vectorSearchConfiguration': {
                        'numberOfResults': max_results
                    }
                }
            )
            
            retrieval_results = response.get('retrievalResults', [])
            query_results = []
            
            for result in retrieval_results:
                try:
                    # Extract S3 URI and filename
                    s3_uri = result['location']['s3Location']['uri']
                    filename = s3_uri.split('/')[-1]
                    
                    # Filter for MBTI-specific files
                    if not filename.startswith(f'{mbti_type}_'):
                        continue
                    
                    # Parse tourist spot data
                    tourist_spot = self._parse_tourist_spot_from_result(result, mbti_type)
                    
                    if tourist_spot:
                        query_result = QueryResult(
                            tourist_spot=tourist_spot,
                            relevance_score=result.get('score', 0.0),
                            s3_uri=s3_uri,
                            query_used=query_prompt,
                            strategy=strategy
                        )
                        query_results.append(query_result)
                
                except Exception as e:
                    logger.warning(
                        "Failed to parse query result",
                        s3_uri=result.get('location', {}).get('s3Location', {}).get('uri', 'unknown'),
                        error=str(e)
                    )
                    continue
            
            return query_results
            
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            error_message = e.response.get('Error', {}).get('Message', '')
            
            logger.error(
                "AWS client error during query execution",
                query=query_prompt[:50] + "...",
                error_code=error_code,
                error_message=error_message,
                strategy=strategy.value
            )
            raise
        except Exception as e:
            logger.error(
                "Unexpected error during query execution",
                query=query_prompt[:50] + "...",
                error=str(e),
                strategy=strategy.value
            )
            raise
    
    def _parse_tourist_spot_from_result(
        self,
        result: Dict[str, Any],
        mbti_type: str
    ) -> Optional[TouristSpot]:
        """Parse tourist spot data from knowledge base result.
        
        Args:
            result: Knowledge base retrieval result
            mbti_type: MBTI personality type for matching
            
        Returns:
            TouristSpot object or None if parsing fails
        """
        try:
            content = result['content']['text']
            s3_uri = result['location']['s3Location']['uri']
            filename = s3_uri.split('/')[-1]
            
            # Extract basic information
            spot_data = {
                'id': filename.replace('.md', ''),
                'name': '',
                'address': '',
                'district': '',
                'area': '',
                'location_category': '',
                'description': '',
                'operating_hours': TouristSpotOperatingHours(),
                'operating_days': [],
                'mbti_match': True,  # Since we filtered for MBTI-specific files
                'mbti_personality_types': [mbti_type],
                'keywords': [],
                'metadata': {
                    's3_uri': s3_uri,
                    'relevance_score': result.get('score', 0.0)
                }
            }
            
            # Parse content using simple text extraction
            lines = content.split('\n')
            current_section = None
            
            for line in lines:
                line = line.strip()
                
                if line.startswith('# '):
                    spot_data['name'] = line[2:].strip()
                elif line.startswith('**Address:**'):
                    spot_data['address'] = line.replace('**Address:**', '').strip()
                elif line.startswith('**District:**'):
                    spot_data['district'] = line.replace('**District:**', '').strip()
                elif line.startswith('**Area:**'):
                    spot_data['area'] = line.replace('**Area:**', '').strip()
                elif line.startswith('**Description:**'):
                    spot_data['description'] = line.replace('**Description:**', '').strip()
                elif 'MBTI:' in line:
                    # Extract keywords from MBTI line
                    keywords_part = line.split('MBTI:')[1] if 'MBTI:' in line else line
                    spot_data['keywords'] = [
                        kw.strip() for kw in keywords_part.split(',') if kw.strip()
                    ]
            
            # Set default values for missing fields
            if not spot_data['name']:
                spot_data['name'] = filename.replace('.md', '').replace('_', ' ')
            if not spot_data['location_category']:
                spot_data['location_category'] = 'Tourist Attraction'
            if not spot_data['description']:
                spot_data['description'] = f"Tourist attraction suitable for {mbti_type} personality"
            
            # Create TouristSpot object
            tourist_spot = TouristSpot.from_dict(spot_data)
            
            return tourist_spot
            
        except Exception as e:
            logger.warning(
                "Failed to parse tourist spot from result",
                error=str(e),
                content_preview=content[:100] + "..." if len(content) > 100 else content
            )
            return None
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for knowledge base queries.
        
        Returns:
            Dictionary with performance metrics by MBTI type
        """
        return self._performance_metrics.copy()
    
    def clear_cache(self) -> None:
        """Clear the query result cache."""
        self._query_cache.clear()
        logger.info("Query cache cleared")
    
    async def query_tourist_spots_by_location(
        self,
        districts: Optional[List[str]] = None,
        areas: Optional[List[str]] = None,
        max_results: int = 20
    ) -> List[TouristSpot]:
        """Query tourist spots by specific districts and areas.
        
        Args:
            districts: List of district names to search
            areas: List of area names to search
            max_results: Maximum number of results to return
            
        Returns:
            List of TouristSpot objects
        """
        try:
            # Build location-based query
            location_terms = []
            if districts:
                location_terms.extend([f"district {district}" for district in districts])
            if areas:
                location_terms.extend([f"area {area}" for area in areas])
            
            if not location_terms:
                query_prompt = "Hong Kong tourist attractions and spots"
            else:
                query_prompt = f"Hong Kong tourist attractions in {' or '.join(location_terms)}"
            
            logger.info(
                "Querying tourist spots by location",
                districts=districts,
                areas=areas,
                max_results=max_results
            )
            
            response = self.bedrock_runtime_client.retrieve(
                knowledgeBaseId=self.knowledge_base_id,
                retrievalQuery={'text': query_prompt},
                retrievalConfiguration={
                    'vectorSearchConfiguration': {
                        'numberOfResults': max_results
                    }
                }
            )
            
            retrieval_results = response.get('retrievalResults', [])
            tourist_spots = []
            
            for result in retrieval_results:
                try:
                    # Parse tourist spot without MBTI filtering
                    tourist_spot = self._parse_tourist_spot_from_result(result, "GENERAL")
                    
                    if tourist_spot:
                        # Mark as non-MBTI match since this is a general location query
                        tourist_spot.mbti_match = False
                        tourist_spots.append(tourist_spot)
                
                except Exception as e:
                    logger.warning(
                        "Failed to parse location-based result",
                        error=str(e)
                    )
                    continue
            
            logger.info(
                "Location-based query completed",
                results_found=len(tourist_spots)
            )
            
            return tourist_spots
            
        except Exception as e:
            logger.error(
                "Failed to query tourist spots by location",
                districts=districts,
                areas=areas,
                error=str(e)
            )
            return []

    def get_error_metrics(self) -> Dict[str, Any]:
        """Get error metrics and statistics.
        
        Returns:
            Dictionary with error metrics
        """
        return {
            'total_errors': self._error_metrics['total_errors'],
            'error_types': self._error_metrics['error_types'].copy(),
            'retry_attempts': self._error_metrics['retry_attempts'],
            'fallback_activations': self._error_metrics['fallback_activations'],
            'last_error_time': self._error_metrics['last_error_time'],
            'error_rate': self._calculate_error_rate(),
            'health_status': self._get_health_status()
        }
    
    def _calculate_error_rate(self) -> float:
        """Calculate current error rate.
        
        Returns:
            Error rate as a percentage
        """
        total_operations = sum(
            metrics.get('queries_executed', 0) 
            for metrics in self._performance_metrics.values()
        )
        
        if total_operations == 0:
            return 0.0
        
        return (self._error_metrics['total_errors'] / total_operations) * 100
    
    def _get_health_status(self) -> str:
        """Get current health status based on error metrics.
        
        Returns:
            Health status string
        """
        error_rate = self._calculate_error_rate()
        last_error_time = self._error_metrics['last_error_time']
        
        # Check if there were recent errors
        if last_error_time and (time.time() - last_error_time) < 300:  # 5 minutes
            if error_rate > 50:
                return "unhealthy"
            elif error_rate > 20:
                return "degraded"
        
        if error_rate > 10:
            return "degraded"
        else:
            return "healthy"
    
    def reset_error_metrics(self) -> None:
        """Reset error metrics for monitoring purposes."""
        self._error_metrics = {
            'total_errors': 0,
            'error_types': {},
            'retry_attempts': 0,
            'fallback_activations': 0,
            'last_error_time': None
        }
        logger.info("Error metrics reset")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        total_cached_results = sum(
            len(results) for results in self._query_cache.values()
        )
        
        return {
            'cached_queries': len(self._query_cache),
            'total_cached_results': total_cached_results,
            'cache_hit_rate': self._calculate_cache_hit_rate(),
            'cache_size_mb': self._estimate_cache_size()
        }
    
    def _calculate_cache_hit_rate(self) -> float:
        """Calculate cache hit rate.
        
        Returns:
            Cache hit rate as a percentage
        """
        # This would need to be tracked during actual usage
        # For now, return 0 as placeholder
        return 0.0
    
    def _estimate_cache_size(self) -> float:
        """Estimate cache size in MB.
        
        Returns:
            Estimated cache size in megabytes
        """
        # Rough estimation based on number of cached items
        total_items = sum(len(results) for results in self._query_cache.values())
        estimated_size_mb = total_items * 0.001  # Rough estimate: 1KB per item
        return round(estimated_size_mb, 2)otal_cached_results': sum(len(results) for results in self._query_cache.values()),
            'cache_keys': list(self._query_cache.keys())
        }