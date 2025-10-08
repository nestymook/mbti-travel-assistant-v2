"""
Advanced Tool Selector

This module extends the basic tool selector with advanced selection criteria including:
- User context consideration in tool selection
- Health status and availability checking before selection
- Fallback tool identification and ranking logic
- Dynamic selection criteria adjustment
- Learning from user feedback and tool performance

Features:
- Context-aware tool selection based on user history and preferences
- Real-time health monitoring and availability checking
- Intelligent fallback selection with ranking
- Adaptive selection weights based on performance feedback
- User behavior learning and personalization
"""

import logging
import time
import statistics
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple, Set, Callable
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
import asyncio
import json

from .tool_selector import ToolSelector, SelectionWeights, ToolRanking, PerformanceMetrics
from .orchestration_types import Intent, UserContext, SelectedTool
from .tool_registry import ToolRegistry, ToolMetadata, ToolHealthStatus, ToolCapability


class ContextType(Enum):
    """Types of user context for selection."""
    MBTI_PERSONALITY = "mbti_personality"
    LOCATION_PREFERENCE = "location_preference"
    TIME_OF_DAY = "time_of_day"
    CONVERSATION_HISTORY = "conversation_history"
    USER_FEEDBACK = "user_feedback"
    USAGE_PATTERNS = "usage_patterns"


class HealthCheckStrategy(Enum):
    """Strategies for health checking."""
    IMMEDIATE = "immediate"  # Check health before each selection
    CACHED = "cached"       # Use cached health status
    PERIODIC = "periodic"   # Check periodically in background
    ADAPTIVE = "adaptive"   # Adjust frequency based on tool reliability


@dataclass
class UserPreferenceProfile:
    """User preference profile for personalized tool selection."""
    user_id: str
    preferred_tools: Set[str] = field(default_factory=set)
    avoided_tools: Set[str] = field(default_factory=set)
    tool_ratings: Dict[str, float] = field(default_factory=dict)  # 0.0 to 1.0
    usage_frequency: Dict[str, int] = field(default_factory=dict)
    success_rate_by_tool: Dict[str, float] = field(default_factory=dict)
    context_preferences: Dict[str, Any] = field(default_factory=dict)
    last_updated: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            'user_id': self.user_id,
            'preferred_tools': list(self.preferred_tools),
            'avoided_tools': list(self.avoided_tools),
            'tool_ratings': self.tool_ratings,
            'usage_frequency': self.usage_frequency,
            'success_rate_by_tool': self.success_rate_by_tool,
            'context_preferences': self.context_preferences,
            'last_updated': self.last_updated.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserPreferenceProfile':
        """Create from dictionary."""
        return cls(
            user_id=data['user_id'],
            preferred_tools=set(data.get('preferred_tools', [])),
            avoided_tools=set(data.get('avoided_tools', [])),
            tool_ratings=data.get('tool_ratings', {}),
            usage_frequency=data.get('usage_frequency', {}),
            success_rate_by_tool=data.get('success_rate_by_tool', {}),
            context_preferences=data.get('context_preferences', {}),
            last_updated=datetime.fromisoformat(data.get('last_updated', datetime.utcnow().isoformat()))
        )


@dataclass
class FallbackStrategy:
    """Strategy for fallback tool selection."""
    primary_tool_id: str
    fallback_tools: List[Tuple[str, float]] = field(default_factory=list)  # (tool_id, confidence)
    fallback_conditions: Dict[str, Any] = field(default_factory=dict)
    max_fallback_attempts: int = 3
    fallback_timeout_seconds: int = 30
    
    def get_next_fallback(self, attempted_tools: Set[str]) -> Optional[Tuple[str, float]]:
        """Get next fallback tool that hasn't been attempted."""
        for tool_id, confidence in self.fallback_tools:
            if tool_id not in attempted_tools:
                return (tool_id, confidence)
        return None


@dataclass
class HealthCheckResult:
    """Result of a health check operation."""
    tool_id: str
    is_healthy: bool
    health_score: float
    response_time_ms: float
    error_message: Optional[str] = None
    check_timestamp: datetime = field(default_factory=datetime.utcnow)
    additional_metrics: Dict[str, Any] = field(default_factory=dict)


class AdvancedToolSelector(ToolSelector):
    """
    Advanced tool selector with enhanced selection criteria.
    
    Extends the basic ToolSelector with:
    - User context consideration and personalization
    - Real-time health status checking
    - Intelligent fallback identification and ranking
    - Adaptive selection weights
    - Learning from user feedback
    """
    
    def __init__(self, 
                 tool_registry: ToolRegistry,
                 selection_weights: Optional[SelectionWeights] = None,
                 performance_window_minutes: int = 60,
                 health_check_strategy: HealthCheckStrategy = HealthCheckStrategy.CACHED,
                 enable_user_learning: bool = True):
        """
        Initialize the advanced tool selector.
        
        Args:
            tool_registry: Tool registry for metadata and health information
            selection_weights: Initial weights for selection criteria
            performance_window_minutes: Window for performance metrics calculation
            health_check_strategy: Strategy for health checking
            enable_user_learning: Whether to learn from user feedback
        """
        super().__init__(tool_registry, selection_weights, performance_window_minutes)
        
        self.health_check_strategy = health_check_strategy
        self.enable_user_learning = enable_user_learning
        self.logger = logging.getLogger(f"mbti_travel_planner.advanced_tool_selector")
        
        # User preference management
        self._user_profiles: Dict[str, UserPreferenceProfile] = {}
        self._profile_lock = asyncio.Lock()
        
        # Health checking
        self._health_check_cache: Dict[str, HealthCheckResult] = {}
        self._health_check_lock = asyncio.Lock()
        self._health_check_tasks: Dict[str, asyncio.Task] = {}
        
        # Fallback management
        self._fallback_strategies: Dict[str, FallbackStrategy] = {}
        self._fallback_performance: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        
        # Adaptive weights
        self._adaptive_weights: Dict[str, SelectionWeights] = {}  # Per user or context
        self._weight_adjustment_history: List[Dict[str, Any]] = []
        
        # Context analysis
        self._context_analyzers: Dict[ContextType, Callable] = {
            ContextType.MBTI_PERSONALITY: self._analyze_mbti_context,
            ContextType.LOCATION_PREFERENCE: self._analyze_location_context,
            ContextType.TIME_OF_DAY: self._analyze_time_context,
            ContextType.CONVERSATION_HISTORY: self._analyze_conversation_context,
            ContextType.USER_FEEDBACK: self._analyze_feedback_context,
            ContextType.USAGE_PATTERNS: self._analyze_usage_patterns
        }
        
        self.logger.info("Advanced tool selector initialized", extra={
            'health_check_strategy': health_check_strategy.value,
            'enable_user_learning': enable_user_learning,
            'context_analyzers': list(self._context_analyzers.keys())
        })
    
    async def select_tools_with_context(self, 
                                      intent: Intent, 
                                      user_context: Optional[UserContext] = None,
                                      max_tools: int = 5,
                                      min_score_threshold: float = 0.3,
                                      require_health_check: bool = True) -> List[SelectedTool]:
        """
        Select tools with advanced context consideration and health checking.
        
        Args:
            intent: Analyzed user intent
            user_context: User context for personalization
            max_tools: Maximum number of tools to return
            min_score_threshold: Minimum score threshold
            require_health_check: Whether to perform health checks
            
        Returns:
            List of selected tools with enhanced metadata
        """
        start_time = time.time()
        
        self.logger.debug("Starting advanced tool selection", extra={
            'intent_type': intent.type.value,
            'user_id': user_context.user_id if user_context else None,
            'require_health_check': require_health_check
        })
        
        # Step 1: Get user preference profile
        user_profile = None
        if user_context and user_context.user_id and self.enable_user_learning:
            user_profile = await self._get_user_profile(user_context.user_id)
        
        # Step 2: Get adaptive selection weights
        selection_weights = await self._get_adaptive_weights(user_context, user_profile)
        
        # Step 3: Get candidate tools with context filtering
        candidate_tools = await self._get_context_aware_candidates(intent, user_context, user_profile)
        
        if not candidate_tools:
            self.logger.warning("No candidate tools found after context filtering")
            return []
        
        # Step 4: Perform health checks if required
        if require_health_check:
            healthy_tools = await self._filter_healthy_tools(candidate_tools)
            if not healthy_tools:
                self.logger.warning("No healthy tools available, using all candidates")
                healthy_tools = candidate_tools
            candidate_tools = healthy_tools
        
        # Step 5: Rank tools with enhanced criteria
        ranked_tools = await self._rank_tools_advanced(
            candidate_tools, intent, user_context, user_profile, selection_weights
        )
        
        # Step 6: Select tools and generate fallback strategies
        selected_tools = []
        for ranking in ranked_tools:
            if ranking.overall_score >= min_score_threshold and len(selected_tools) < max_tools:
                # Generate fallback strategy
                fallback_strategy = await self._create_fallback_strategy(
                    ranking.tool_metadata, candidate_tools, user_profile
                )
                
                selected_tool = SelectedTool(
                    tool_id=ranking.tool_metadata.id,
                    tool_name=ranking.tool_metadata.name,
                    confidence=ranking.overall_score,
                    expected_performance=ranking.ranking_details.get('performance_breakdown', {}),
                    fallback_tools=[tool_id for tool_id, _ in fallback_strategy.fallback_tools],
                    selection_reason=self._generate_advanced_selection_reason(ranking, user_profile)
                )
                
                selected_tools.append(selected_tool)
                self._fallback_strategies[ranking.tool_metadata.id] = fallback_strategy
        
        selection_time_ms = (time.time() - start_time) * 1000
        
        # Step 7: Update user profile if learning is enabled
        if user_profile and self.enable_user_learning:
            await self._update_user_profile_selection(user_profile, selected_tools, intent)
        
        self.logger.info("Advanced tool selection completed", extra={
            'selected_tools_count': len(selected_tools),
            'selection_time_ms': selection_time_ms,
            'health_checks_performed': require_health_check,
            'user_learning_enabled': self.enable_user_learning and user_profile is not None
        })
        
        return selected_tools
    
    async def check_tool_availability(self, 
                                    tool_id: str,
                                    force_check: bool = False) -> HealthCheckResult:
        """
        Check tool availability and health status.
        
        Args:
            tool_id: Tool identifier
            force_check: Force immediate health check
            
        Returns:
            Health check result
        """
        async with self._health_check_lock:
            # Check cache first unless forced
            if not force_check and tool_id in self._health_check_cache:
                cached_result = self._health_check_cache[tool_id]
                cache_age = datetime.utcnow() - cached_result.check_timestamp
                
                # Use cached result if it's fresh enough
                if cache_age < timedelta(minutes=5):
                    return cached_result
            
            # Perform health check
            health_result = await self._perform_health_check(tool_id)
            
            # Cache the result
            self._health_check_cache[tool_id] = health_result
            
            # Update tool registry health status
            health_status = ToolHealthStatus.HEALTHY if health_result.is_healthy else ToolHealthStatus.UNHEALTHY
            self.tool_registry.update_tool_health_status(
                tool_id=tool_id,
                status=health_status,
                response_time_ms=health_result.response_time_ms,
                error_message=health_result.error_message,
                additional_data=health_result.additional_metrics
            )
            
            return health_result
    
    async def get_fallback_tools(self, 
                               primary_tool_id: str,
                               attempted_tools: Optional[Set[str]] = None) -> List[Tuple[str, float]]:
        """
        Get fallback tools for a primary tool.
        
        Args:
            primary_tool_id: Primary tool that failed
            attempted_tools: Tools that have already been attempted
            
        Returns:
            List of (tool_id, confidence) tuples for fallback tools
        """
        attempted_tools = attempted_tools or set()
        
        # Get fallback strategy
        fallback_strategy = self._fallback_strategies.get(primary_tool_id)
        if not fallback_strategy:
            # Generate fallback strategy on demand
            primary_tool = self.tool_registry.get_tool_metadata(primary_tool_id)
            if primary_tool:
                candidate_tools = self.tool_registry.get_all_tools()
                fallback_strategy = await self._create_fallback_strategy(primary_tool, candidate_tools)
                self._fallback_strategies[primary_tool_id] = fallback_strategy
        
        if not fallback_strategy:
            return []
        
        # Get available fallback tools
        fallback_tools = []
        for tool_id, confidence in fallback_strategy.fallback_tools:
            if tool_id not in attempted_tools:
                # Check if tool is healthy
                health_result = await self.check_tool_availability(tool_id)
                if health_result.is_healthy:
                    # Adjust confidence based on health score
                    adjusted_confidence = confidence * health_result.health_score
                    fallback_tools.append((tool_id, adjusted_confidence))
        
        # Sort by confidence
        fallback_tools.sort(key=lambda x: x[1], reverse=True)
        
        return fallback_tools[:fallback_strategy.max_fallback_attempts]
    
    async def record_tool_feedback(self, 
                                 tool_id: str,
                                 user_id: Optional[str],
                                 success: bool,
                                 user_rating: Optional[float] = None,
                                 feedback_text: Optional[str] = None) -> None:
        """
        Record user feedback for tool performance learning.
        
        Args:
            tool_id: Tool identifier
            user_id: User identifier
            success: Whether the tool execution was successful
            user_rating: User rating (0.0 to 1.0)
            feedback_text: Optional feedback text
        """
        if not self.enable_user_learning or not user_id:
            return
        
        # Update user profile
        user_profile = await self._get_user_profile(user_id)
        
        # Update tool rating
        if user_rating is not None:
            current_rating = user_profile.tool_ratings.get(tool_id, 0.5)
            # Weighted average with more weight on recent feedback
            new_rating = (current_rating * 0.7) + (user_rating * 0.3)
            user_profile.tool_ratings[tool_id] = new_rating
        
        # Update success rate
        current_success_rate = user_profile.success_rate_by_tool.get(tool_id, 0.5)
        usage_count = user_profile.usage_frequency.get(tool_id, 0)
        
        # Calculate new success rate
        total_successes = current_success_rate * usage_count
        if success:
            total_successes += 1
        new_usage_count = usage_count + 1
        new_success_rate = total_successes / new_usage_count
        
        user_profile.success_rate_by_tool[tool_id] = new_success_rate
        user_profile.usage_frequency[tool_id] = new_usage_count
        
        # Update preferences based on feedback
        if user_rating is not None:
            if user_rating > 0.7:
                user_profile.preferred_tools.add(tool_id)
                user_profile.avoided_tools.discard(tool_id)
            elif user_rating < 0.3:
                user_profile.avoided_tools.add(tool_id)
                user_profile.preferred_tools.discard(tool_id)
        
        user_profile.last_updated = datetime.utcnow()
        
        # Store updated profile
        async with self._profile_lock:
            self._user_profiles[user_id] = user_profile
        
        self.logger.debug("Tool feedback recorded", extra={
            'tool_id': tool_id,
            'user_id': user_id,
            'success': success,
            'user_rating': user_rating,
            'new_success_rate': new_success_rate
        })
    
    async def _get_user_profile(self, user_id: str) -> UserPreferenceProfile:
        """Get or create user preference profile."""
        async with self._profile_lock:
            if user_id not in self._user_profiles:
                self._user_profiles[user_id] = UserPreferenceProfile(user_id=user_id)
            return self._user_profiles[user_id]
    
    async def _get_adaptive_weights(self, 
                                  user_context: Optional[UserContext],
                                  user_profile: Optional[UserPreferenceProfile]) -> SelectionWeights:
        """Get adaptive selection weights based on context and user profile."""
        # Start with default weights
        weights = SelectionWeights(
            capability_weight=self.selection_weights.capability_weight,
            performance_weight=self.selection_weights.performance_weight,
            health_weight=self.selection_weights.health_weight,
            context_weight=self.selection_weights.context_weight,
            compatibility_weight=self.selection_weights.compatibility_weight
        )
        
        # Adjust based on user profile
        if user_profile:
            # Users with more experience can rely more on performance
            total_usage = sum(user_profile.usage_frequency.values())
            if total_usage > 50:  # Experienced user
                weights.performance_weight += 0.05
                weights.capability_weight -= 0.05
            
            # Users with strong preferences should weight context more
            if len(user_profile.preferred_tools) > 3:
                weights.context_weight += 0.05
                weights.compatibility_weight -= 0.05
        
        # Adjust based on current context
        if user_context:
            # If user has MBTI type, weight context more heavily
            if user_context.mbti_type:
                weights.context_weight += 0.05
                weights.capability_weight -= 0.05
            
            # If user has location context, weight context more
            if user_context.location_context:
                weights.context_weight += 0.03
                weights.performance_weight -= 0.03
        
        # Ensure weights still sum to 1.0
        total = (weights.capability_weight + weights.performance_weight + 
                weights.health_weight + weights.context_weight + weights.compatibility_weight)
        
        if abs(total - 1.0) > 0.01:
            # Normalize weights
            weights.capability_weight /= total
            weights.performance_weight /= total
            weights.health_weight /= total
            weights.context_weight /= total
            weights.compatibility_weight /= total
        
        return weights
    
    async def _get_context_aware_candidates(self, 
                                          intent: Intent,
                                          user_context: Optional[UserContext],
                                          user_profile: Optional[UserPreferenceProfile]) -> List[ToolMetadata]:
        """Get candidate tools with context-aware filtering."""
        # Start with capability-based candidates
        candidate_tools = await self._get_candidate_tools(intent)
        
        # Apply user preference filtering
        if user_profile:
            # Remove avoided tools
            candidate_tools = [
                tool for tool in candidate_tools 
                if tool.id not in user_profile.avoided_tools
            ]
            
            # Boost preferred tools by ensuring they're included
            preferred_tool_ids = user_profile.preferred_tools
            for tool_id in preferred_tool_ids:
                tool_metadata = self.tool_registry.get_tool_metadata(tool_id)
                if tool_metadata and tool_metadata not in candidate_tools:
                    # Check if preferred tool has any relevant capabilities
                    tool_caps = {cap.name for cap in tool_metadata.capabilities}
                    required_caps = set(intent.required_capabilities or [])
                    optional_caps = set(intent.optional_capabilities or [])
                    
                    if tool_caps & (required_caps | optional_caps):
                        candidate_tools.append(tool_metadata)
        
        # Apply context-based filtering
        if user_context:
            filtered_tools = []
            for tool in candidate_tools:
                context_score = await self._calculate_advanced_context_score(tool, user_context, user_profile)
                # Only include tools with reasonable context fit
                if context_score > 0.2:
                    filtered_tools.append(tool)
            
            if filtered_tools:
                candidate_tools = filtered_tools
        
        return candidate_tools
    
    async def _filter_healthy_tools(self, candidate_tools: List[ToolMetadata]) -> List[ToolMetadata]:
        """Filter tools based on health status."""
        healthy_tools = []
        
        # Check health for all candidate tools
        health_check_tasks = []
        for tool in candidate_tools:
            task = asyncio.create_task(self.check_tool_availability(tool.id))
            health_check_tasks.append((tool, task))
        
        # Wait for all health checks
        for tool, task in health_check_tasks:
            try:
                health_result = await task
                if health_result.is_healthy or health_result.health_score > 0.5:
                    healthy_tools.append(tool)
            except Exception as e:
                self.logger.warning(f"Health check failed for tool {tool.id}: {e}")
                # Include tool anyway if health check fails
                healthy_tools.append(tool)
        
        return healthy_tools
    
    async def _rank_tools_advanced(self, 
                                 candidate_tools: List[ToolMetadata],
                                 intent: Intent,
                                 user_context: Optional[UserContext],
                                 user_profile: Optional[UserPreferenceProfile],
                                 selection_weights: SelectionWeights) -> List[ToolRanking]:
        """Rank tools with advanced criteria."""
        rankings = []
        
        for tool_metadata in candidate_tools:
            # Calculate enhanced scores
            capability_score = await self._calculate_capability_score(tool_metadata, intent)
            performance_score = await self._calculate_enhanced_performance_score(tool_metadata, user_profile)
            health_score = await self._calculate_enhanced_health_score(tool_metadata)
            context_score = await self._calculate_advanced_context_score(tool_metadata, user_context, user_profile)
            compatibility_score = await self._calculate_compatibility_score(tool_metadata, candidate_tools)
            
            # Calculate weighted overall score with adaptive weights
            overall_score = (
                capability_score * selection_weights.capability_weight +
                performance_score * selection_weights.performance_weight +
                health_score * selection_weights.health_weight +
                context_score * selection_weights.context_weight +
                compatibility_score * selection_weights.compatibility_weight
            )
            
            ranking = ToolRanking(
                tool_metadata=tool_metadata,
                overall_score=overall_score,
                capability_score=capability_score,
                performance_score=performance_score,
                health_score=health_score,
                context_score=context_score,
                compatibility_score=compatibility_score,
                ranking_details={
                    'adaptive_weights': {
                        'capability': selection_weights.capability_weight,
                        'performance': selection_weights.performance_weight,
                        'health': selection_weights.health_weight,
                        'context': selection_weights.context_weight,
                        'compatibility': selection_weights.compatibility_weight
                    },
                    'performance_breakdown': {
                        'capability_score': capability_score,
                        'performance_score': performance_score,
                        'health_score': health_score,
                        'context_score': context_score,
                        'compatibility_score': compatibility_score
                    },
                    'user_profile_applied': user_profile is not None,
                    'calculated_at': datetime.utcnow().isoformat()
                }
            )
            
            rankings.append(ranking)
        
        # Sort by overall score
        rankings.sort(key=lambda r: r.overall_score, reverse=True)
        
        return rankings
    
    async def _calculate_enhanced_performance_score(self, 
                                                  tool_metadata: ToolMetadata,
                                                  user_profile: Optional[UserPreferenceProfile]) -> float:
        """Calculate enhanced performance score including user-specific metrics."""
        # Get base performance score
        base_score = await self._calculate_performance_score(tool_metadata)
        
        # Enhance with user-specific data
        if user_profile:
            tool_id = tool_metadata.id
            
            # User-specific success rate
            user_success_rate = user_profile.success_rate_by_tool.get(tool_id)
            if user_success_rate is not None:
                # Weight user-specific success rate more heavily
                base_score = (base_score * 0.6) + (user_success_rate * 0.4)
            
            # Usage frequency bonus (tools used more often are likely better for this user)
            usage_count = user_profile.usage_frequency.get(tool_id, 0)
            if usage_count > 0:
                usage_bonus = min(0.1, usage_count / 100.0)  # Max 10% bonus
                base_score += usage_bonus
        
        return min(1.0, base_score)
    
    async def _calculate_enhanced_health_score(self, tool_metadata: ToolMetadata) -> float:
        """Calculate enhanced health score with real-time checking."""
        # Get cached health result
        health_result = self._health_check_cache.get(tool_metadata.id)
        
        if health_result:
            # Use cached result with age penalty
            cache_age = datetime.utcnow() - health_result.check_timestamp
            age_penalty = min(0.2, cache_age.total_seconds() / 3600)  # Max 20% penalty after 1 hour
            
            base_score = health_result.health_score
            return max(0.0, base_score - age_penalty)
        else:
            # Fall back to registry health status
            return await self._calculate_health_score(tool_metadata)
    
    async def _calculate_advanced_context_score(self, 
                                              tool_metadata: ToolMetadata,
                                              user_context: Optional[UserContext],
                                              user_profile: Optional[UserPreferenceProfile]) -> float:
        """Calculate advanced context score with multiple context types."""
        if not user_context and not user_profile:
            return 0.5  # Neutral score
        
        context_scores = []
        
        # Analyze different context types
        for context_type, analyzer in self._context_analyzers.items():
            try:
                score = await analyzer(tool_metadata, user_context, user_profile)
                if score is not None:
                    context_scores.append(score)
            except Exception as e:
                self.logger.warning(f"Context analysis failed for {context_type}: {e}")
        
        # Calculate weighted average of context scores
        if context_scores:
            return statistics.mean(context_scores)
        else:
            return 0.5
    
    async def _create_fallback_strategy(self, 
                                      primary_tool: ToolMetadata,
                                      candidate_tools: List[ToolMetadata],
                                      user_profile: Optional[UserPreferenceProfile] = None) -> FallbackStrategy:
        """Create fallback strategy for a primary tool."""
        fallback_tools = []
        primary_capabilities = {cap.name for cap in primary_tool.capabilities}
        
        for tool in candidate_tools:
            if tool.id == primary_tool.id:
                continue
            
            tool_capabilities = {cap.name for cap in tool.capabilities}
            
            # Calculate capability overlap
            overlap = len(primary_capabilities & tool_capabilities)
            if overlap > 0:
                overlap_ratio = overlap / len(primary_capabilities)
                
                # Calculate fallback confidence
                health_score = await self._calculate_enhanced_health_score(tool)
                performance_score = await self._calculate_enhanced_performance_score(tool, user_profile)
                
                # User preference bonus
                preference_bonus = 0.0
                if user_profile:
                    if tool.id in user_profile.preferred_tools:
                        preference_bonus = 0.2
                    elif tool.id in user_profile.avoided_tools:
                        preference_bonus = -0.3
                
                fallback_confidence = (
                    overlap_ratio * 0.4 +
                    health_score * 0.3 +
                    performance_score * 0.3 +
                    preference_bonus
                )
                
                if fallback_confidence > 0.3:  # Minimum threshold
                    fallback_tools.append((tool.id, fallback_confidence))
        
        # Sort by confidence and take top candidates
        fallback_tools.sort(key=lambda x: x[1], reverse=True)
        
        return FallbackStrategy(
            primary_tool_id=primary_tool.id,
            fallback_tools=fallback_tools[:5],  # Top 5 fallbacks
            fallback_conditions={
                'min_overlap_ratio': 0.3,
                'min_health_score': 0.5,
                'created_at': datetime.utcnow().isoformat()
            }
        )
    
    async def _perform_health_check(self, tool_id: str) -> HealthCheckResult:
        """Perform health check on a tool."""
        start_time = time.time()
        
        try:
            # Get tool instance
            tool_instance = self.tool_registry.get_tool_instance(tool_id)
            tool_metadata = self.tool_registry.get_tool_metadata(tool_id)
            
            if not tool_instance or not tool_metadata:
                return HealthCheckResult(
                    tool_id=tool_id,
                    is_healthy=False,
                    health_score=0.0,
                    response_time_ms=0.0,
                    error_message="Tool instance or metadata not found"
                )
            
            # Perform health check
            if hasattr(tool_instance, 'health_check'):
                health_result = await tool_instance.health_check()
                is_healthy = health_result.get('healthy', False)
                error_message = health_result.get('error')
                additional_metrics = health_result
            else:
                # Basic availability check
                is_healthy = True
                error_message = None
                additional_metrics = {'check_type': 'basic_availability'}
            
            response_time_ms = (time.time() - start_time) * 1000
            
            # Calculate health score based on multiple factors
            health_score = 1.0 if is_healthy else 0.0
            
            # Adjust based on response time
            if response_time_ms > 5000:  # 5 seconds
                health_score *= 0.5
            elif response_time_ms > 2000:  # 2 seconds
                health_score *= 0.8
            
            return HealthCheckResult(
                tool_id=tool_id,
                is_healthy=is_healthy,
                health_score=health_score,
                response_time_ms=response_time_ms,
                error_message=error_message,
                additional_metrics=additional_metrics
            )
            
        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            
            return HealthCheckResult(
                tool_id=tool_id,
                is_healthy=False,
                health_score=0.0,
                response_time_ms=response_time_ms,
                error_message=str(e)
            )
    
    async def _update_user_profile_selection(self, 
                                           user_profile: UserPreferenceProfile,
                                           selected_tools: List[SelectedTool],
                                           intent: Intent) -> None:
        """Update user profile based on tool selection."""
        for tool in selected_tools:
            # Update usage frequency
            current_usage = user_profile.usage_frequency.get(tool.tool_id, 0)
            user_profile.usage_frequency[tool.tool_id] = current_usage + 1
            
            # Update context preferences based on intent
            intent_type = intent.type.value
            if intent_type not in user_profile.context_preferences:
                user_profile.context_preferences[intent_type] = {}
            
            context_prefs = user_profile.context_preferences[intent_type]
            if 'selected_tools' not in context_prefs:
                context_prefs['selected_tools'] = defaultdict(int)
            
            context_prefs['selected_tools'][tool.tool_id] += 1
        
        user_profile.last_updated = datetime.utcnow()
    
    def _generate_advanced_selection_reason(self, 
                                          ranking: ToolRanking,
                                          user_profile: Optional[UserPreferenceProfile]) -> str:
        """Generate advanced selection reason with user context."""
        reasons = []
        
        # Capability reasons
        if ranking.capability_score > 0.8:
            reasons.append("excellent capability match")
        elif ranking.capability_score > 0.6:
            reasons.append("good capability match")
        
        # Performance reasons
        if ranking.performance_score > 0.8:
            reasons.append("high performance")
        elif ranking.performance_score < 0.4:
            reasons.append("performance concerns")
        
        # Health reasons
        if ranking.health_score > 0.8:
            reasons.append("healthy status")
        elif ranking.health_score < 0.5:
            reasons.append("health issues")
        
        # Context reasons
        if ranking.context_score > 0.7:
            reasons.append("excellent context fit")
        elif ranking.context_score > 0.5:
            reasons.append("good context fit")
        
        # User preference reasons
        if user_profile:
            tool_id = ranking.tool_metadata.id
            if tool_id in user_profile.preferred_tools:
                reasons.append("user preferred")
            
            user_rating = user_profile.tool_ratings.get(tool_id)
            if user_rating and user_rating > 0.7:
                reasons.append("highly rated by user")
            
            usage_count = user_profile.usage_frequency.get(tool_id, 0)
            if usage_count > 10:
                reasons.append("frequently used")
        
        if not reasons:
            reasons.append("meets minimum requirements")
        
        return f"Selected for {', '.join(reasons)} (score: {ranking.overall_score:.2f})"
    
    # Context analyzer methods
    async def _analyze_mbti_context(self, 
                                  tool_metadata: ToolMetadata,
                                  user_context: Optional[UserContext],
                                  user_profile: Optional[UserPreferenceProfile]) -> Optional[float]:
        """Analyze MBTI personality context."""
        if not user_context or not user_context.mbti_type:
            return None
        
        # Check if tool supports MBTI personalization
        tool_capabilities = {cap.name for cap in tool_metadata.capabilities}
        if 'mbti_personalization' in tool_capabilities:
            return 0.8  # High score for MBTI-aware tools
        
        # Check tool type compatibility with MBTI
        mbti_type = user_context.mbti_type.upper()
        
        # Simple MBTI-tool compatibility rules
        if 'restaurant_reasoning' in tool_metadata.name.lower():
            # Thinking types might prefer reasoning tools
            if 'T' in mbti_type:
                return 0.7
            else:
                return 0.6
        
        if 'search' in tool_metadata.name.lower():
            # Sensing types might prefer concrete search tools
            if 'S' in mbti_type:
                return 0.7
            else:
                return 0.6
        
        return 0.5  # Neutral score
    
    async def _analyze_location_context(self, 
                                      tool_metadata: ToolMetadata,
                                      user_context: Optional[UserContext],
                                      user_profile: Optional[UserPreferenceProfile]) -> Optional[float]:
        """Analyze location preference context."""
        if not user_context or not user_context.location_context:
            return None
        
        # Check if tool supports location-based operations
        tool_capabilities = {cap.name for cap in tool_metadata.capabilities}
        location_capabilities = [
            'search_by_district', 'location_search', 'district_search'
        ]
        
        if any(cap in tool_capabilities for cap in location_capabilities):
            return 0.8
        
        return 0.4  # Lower score for non-location tools
    
    async def _analyze_time_context(self, 
                                  tool_metadata: ToolMetadata,
                                  user_context: Optional[UserContext],
                                  user_profile: Optional[UserPreferenceProfile]) -> Optional[float]:
        """Analyze time of day context."""
        current_hour = datetime.now().hour
        
        # Check if tool supports meal-time operations
        tool_capabilities = {cap.name for cap in tool_metadata.capabilities}
        
        if 'search_by_meal_type' in tool_capabilities:
            # Higher score during meal times
            if 7 <= current_hour <= 10:  # Breakfast
                return 0.8
            elif 11 <= current_hour <= 14:  # Lunch
                return 0.8
            elif 17 <= current_hour <= 21:  # Dinner
                return 0.8
            else:
                return 0.6
        
        return 0.5  # Neutral score
    
    async def _analyze_conversation_context(self, 
                                          tool_metadata: ToolMetadata,
                                          user_context: Optional[UserContext],
                                          user_profile: Optional[UserPreferenceProfile]) -> Optional[float]:
        """Analyze conversation history context."""
        if not user_context or not user_context.conversation_history:
            return None
        
        # Analyze recent conversation for tool relevance
        recent_conversation = ' '.join(user_context.conversation_history[-5:]).lower()
        tool_name_lower = tool_metadata.name.lower()
        
        # Simple keyword matching
        if tool_name_lower in recent_conversation:
            return 0.9  # High score if tool was mentioned
        
        # Check capability keywords
        capability_keywords = [cap.name.lower() for cap in tool_metadata.capabilities]
        matches = sum(1 for keyword in capability_keywords if keyword in recent_conversation)
        
        if matches > 0:
            return 0.6 + (matches * 0.1)  # Bonus for keyword matches
        
        return 0.5  # Neutral score
    
    async def _analyze_feedback_context(self, 
                                      tool_metadata: ToolMetadata,
                                      user_context: Optional[UserContext],
                                      user_profile: Optional[UserPreferenceProfile]) -> Optional[float]:
        """Analyze user feedback context."""
        if not user_profile:
            return None
        
        tool_id = tool_metadata.id
        
        # Check user rating
        user_rating = user_profile.tool_ratings.get(tool_id)
        if user_rating is not None:
            return user_rating
        
        # Check if tool is in preferences
        if tool_id in user_profile.preferred_tools:
            return 0.8
        elif tool_id in user_profile.avoided_tools:
            return 0.2
        
        return 0.5  # Neutral score for unrated tools
    
    async def _analyze_usage_patterns(self, 
                                    tool_metadata: ToolMetadata,
                                    user_context: Optional[UserContext],
                                    user_profile: Optional[UserPreferenceProfile]) -> Optional[float]:
        """Analyze usage pattern context."""
        if not user_profile:
            return None
        
        tool_id = tool_metadata.id
        usage_count = user_profile.usage_frequency.get(tool_id, 0)
        
        if usage_count == 0:
            return 0.4  # Lower score for unused tools
        
        # Calculate usage score based on frequency
        max_usage = max(user_profile.usage_frequency.values()) if user_profile.usage_frequency else 1
        usage_ratio = usage_count / max_usage
        
        # Convert to score (0.4 to 0.9 range)
        return 0.4 + (usage_ratio * 0.5)