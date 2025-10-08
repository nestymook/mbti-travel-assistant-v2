"""
Tool Selector

This module provides intelligent tool selection capabilities for the MBTI Travel Planner Agent.
It implements sophisticated algorithms for ranking tools based on capability match, performance
metrics, and user context.

Features:
- Capability matching algorithms
- Performance-based ranking using historical metrics
- Tool compatibility validation for workflow planning
- Health status consideration
- User context integration
- Fallback tool identification
"""

import logging
import time
import statistics
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
import asyncio

from .orchestration_types import Intent, UserContext, SelectedTool
from .tool_registry import ToolRegistry, ToolMetadata, ToolHealthStatus, ToolCapability


class SelectionCriteria(Enum):
    """Criteria for tool selection."""
    CAPABILITY_MATCH = "capability_match"
    PERFORMANCE_SCORE = "performance_score"
    HEALTH_STATUS = "health_status"
    USER_CONTEXT = "user_context"
    COMPATIBILITY = "compatibility"


@dataclass
class ToolRanking:
    """Ranking information for a tool."""
    tool_metadata: ToolMetadata
    overall_score: float
    capability_score: float
    performance_score: float
    health_score: float
    context_score: float
    compatibility_score: float
    ranking_details: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging."""
        return {
            'tool_id': self.tool_metadata.id,
            'tool_name': self.tool_metadata.name,
            'overall_score': self.overall_score,
            'capability_score': self.capability_score,
            'performance_score': self.performance_score,
            'health_score': self.health_score,
            'context_score': self.context_score,
            'compatibility_score': self.compatibility_score,
            'ranking_details': self.ranking_details
        }


@dataclass
class SelectionWeights:
    """Weights for different selection criteria."""
    capability_weight: float = 0.35
    performance_weight: float = 0.25
    health_weight: float = 0.20
    context_weight: float = 0.15
    compatibility_weight: float = 0.05
    
    def __post_init__(self):
        """Validate weights sum to 1.0."""
        total = (self.capability_weight + self.performance_weight + 
                self.health_weight + self.context_weight + self.compatibility_weight)
        if abs(total - 1.0) > 0.01:
            raise ValueError(f"Selection weights must sum to 1.0, got {total}")


@dataclass
class PerformanceMetrics:
    """Performance metrics for a tool."""
    success_rate: float = 0.0
    average_response_time_ms: float = 0.0
    throughput_score: float = 0.0
    error_rate: float = 0.0
    availability_score: float = 0.0
    recent_invocations: int = 0
    
    def calculate_overall_score(self) -> float:
        """Calculate overall performance score (0.0 to 1.0)."""
        # Weight different metrics
        score = (
            self.success_rate * 0.4 +
            (1.0 - min(self.average_response_time_ms / 10000, 1.0)) * 0.3 +  # 10s = 0 score
            self.throughput_score * 0.15 +
            (1.0 - self.error_rate) * 0.10 +
            self.availability_score * 0.05
        )
        return max(0.0, min(1.0, score))


class ToolSelector:
    """
    Intelligent tool selector that ranks tools based on multiple criteria.
    
    This class implements sophisticated algorithms for:
    - Capability matching with intent requirements
    - Performance-based ranking using historical metrics
    - Tool compatibility validation for workflow planning
    - Health status and availability checking
    - User context consideration
    - Fallback tool identification and ranking
    """
    
    def __init__(self, 
                 tool_registry: ToolRegistry,
                 selection_weights: Optional[SelectionWeights] = None,
                 performance_window_minutes: int = 60):
        """
        Initialize the tool selector.
        
        Args:
            tool_registry: Tool registry for metadata and health information
            selection_weights: Weights for selection criteria
            performance_window_minutes: Window for performance metrics calculation
        """
        self.tool_registry = tool_registry
        self.selection_weights = selection_weights or SelectionWeights()
        self.performance_window_minutes = performance_window_minutes
        self.logger = logging.getLogger(f"mbti_travel_planner.tool_selector")
        
        # Performance tracking
        self._performance_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self._last_performance_calculation: Dict[str, datetime] = {}
        self._cached_performance_metrics: Dict[str, PerformanceMetrics] = {}
        
        self.logger.info("Tool selector initialized", extra={
            'selection_weights': {
                'capability': self.selection_weights.capability_weight,
                'performance': self.selection_weights.performance_weight,
                'health': self.selection_weights.health_weight,
                'context': self.selection_weights.context_weight,
                'compatibility': self.selection_weights.compatibility_weight
            },
            'performance_window_minutes': performance_window_minutes
        })
    
    async def select_tools(self, 
                          intent: Intent, 
                          user_context: Optional[UserContext] = None,
                          max_tools: int = 5,
                          min_score_threshold: float = 0.3) -> List[SelectedTool]:
        """
        Select and rank tools based on intent and context.
        
        Args:
            intent: Analyzed user intent
            user_context: Optional user context for personalization
            max_tools: Maximum number of tools to return
            min_score_threshold: Minimum score threshold for tool selection
            
        Returns:
            List of selected tools ranked by suitability
        """
        start_time = time.time()
        
        self.logger.debug("Starting tool selection", extra={
            'intent_type': intent.type.value,
            'required_capabilities': intent.required_capabilities,
            'optional_capabilities': intent.optional_capabilities,
            'max_tools': max_tools,
            'min_score_threshold': min_score_threshold
        })
        
        # Step 1: Get candidate tools based on capabilities
        candidate_tools = await self._get_candidate_tools(intent)
        
        if not candidate_tools:
            self.logger.warning("No candidate tools found for intent", extra={
                'intent_type': intent.type.value,
                'required_capabilities': intent.required_capabilities
            })
            return []
        
        self.logger.debug(f"Found {len(candidate_tools)} candidate tools")
        
        # Step 2: Rank tools using multiple criteria
        ranked_tools = await self.rank_tools(candidate_tools, intent, user_context)
        
        # Step 3: Filter by minimum score and limit results
        selected_tools = []
        for ranking in ranked_tools:
            if ranking.overall_score >= min_score_threshold and len(selected_tools) < max_tools:
                # Get fallback tools
                fallback_tools = await self._get_fallback_tools(ranking.tool_metadata, candidate_tools)
                
                selected_tool = SelectedTool(
                    tool_id=ranking.tool_metadata.id,
                    tool_name=ranking.tool_metadata.name,
                    confidence=ranking.overall_score,
                    expected_performance={
                        'capability_score': ranking.capability_score,
                        'performance_score': ranking.performance_score,
                        'health_score': ranking.health_score,
                        'context_score': ranking.context_score,
                        'compatibility_score': ranking.compatibility_score,
                        'overall_score': ranking.overall_score
                    },
                    fallback_tools=[t.id for t in fallback_tools],
                    selection_reason=self._generate_selection_reason(ranking)
                )
                
                selected_tools.append(selected_tool)
        
        selection_time_ms = (time.time() - start_time) * 1000
        
        self.logger.info("Tool selection completed", extra={
            'selected_tools_count': len(selected_tools),
            'candidate_tools_count': len(candidate_tools),
            'selection_time_ms': selection_time_ms,
            'selected_tools': [tool.tool_name for tool in selected_tools]
        })
        
        return selected_tools
    
    async def rank_tools(self, 
                        candidate_tools: List[ToolMetadata],
                        intent: Intent,
                        user_context: Optional[UserContext] = None) -> List[ToolRanking]:
        """
        Rank tools based on multiple criteria.
        
        Args:
            candidate_tools: List of candidate tools to rank
            intent: User intent for capability matching
            user_context: Optional user context
            
        Returns:
            List of tool rankings sorted by overall score (highest first)
        """
        rankings = []
        
        for tool_metadata in candidate_tools:
            # Calculate individual scores
            capability_score = await self._calculate_capability_score(tool_metadata, intent)
            performance_score = await self._calculate_performance_score(tool_metadata)
            health_score = await self._calculate_health_score(tool_metadata)
            context_score = await self._calculate_context_score(tool_metadata, user_context)
            compatibility_score = await self._calculate_compatibility_score(tool_metadata, candidate_tools)
            
            # Calculate weighted overall score
            overall_score = (
                capability_score * self.selection_weights.capability_weight +
                performance_score * self.selection_weights.performance_weight +
                health_score * self.selection_weights.health_weight +
                context_score * self.selection_weights.context_weight +
                compatibility_score * self.selection_weights.compatibility_weight
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
                    'selection_weights': {
                        'capability': self.selection_weights.capability_weight,
                        'performance': self.selection_weights.performance_weight,
                        'health': self.selection_weights.health_weight,
                        'context': self.selection_weights.context_weight,
                        'compatibility': self.selection_weights.compatibility_weight
                    },
                    'calculated_at': datetime.utcnow().isoformat()
                }
            )
            
            rankings.append(ranking)
        
        # Sort by overall score (highest first)
        rankings.sort(key=lambda r: r.overall_score, reverse=True)
        
        self.logger.debug("Tools ranked", extra={
            'rankings': [r.to_dict() for r in rankings[:3]]  # Log top 3
        })
        
        return rankings
    
    async def validate_tool_compatibility(self, 
                                        tools: List[ToolMetadata],
                                        workflow_requirements: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Validate compatibility between tools for workflow planning.
        
        Args:
            tools: List of tools to validate compatibility
            workflow_requirements: Optional workflow-specific requirements
            
        Returns:
            Validation result with compatibility information
        """
        validation_result = {
            'compatible': True,
            'issues': [],
            'recommendations': [],
            'compatibility_matrix': {},
            'workflow_feasible': True
        }
        
        if len(tools) < 2:
            return validation_result
        
        # Check pairwise compatibility
        for i, tool1 in enumerate(tools):
            for j, tool2 in enumerate(tools[i+1:], i+1):
                compatibility = await self._check_tool_pair_compatibility(tool1, tool2)
                validation_result['compatibility_matrix'][f"{tool1.id}_{tool2.id}"] = compatibility
                
                if not compatibility['compatible']:
                    validation_result['compatible'] = False
                    validation_result['issues'].extend(compatibility['issues'])
        
        # Check workflow-specific requirements
        if workflow_requirements:
            workflow_validation = await self._validate_workflow_requirements(tools, workflow_requirements)
            validation_result['workflow_feasible'] = workflow_validation['feasible']
            validation_result['issues'].extend(workflow_validation.get('issues', []))
            validation_result['recommendations'].extend(workflow_validation.get('recommendations', []))
        
        # Generate recommendations for compatibility issues
        if validation_result['issues']:
            recommendations = await self._generate_compatibility_recommendations(tools, validation_result['issues'])
            validation_result['recommendations'].extend(recommendations)
        
        return validation_result
    
    async def _get_candidate_tools(self, intent: Intent) -> List[ToolMetadata]:
        """Get candidate tools based on intent capabilities."""
        if not intent.required_capabilities:
            # If no specific capabilities required, return all tools
            return self.tool_registry.get_all_tools()
        
        # Get tools that have all required capabilities
        candidate_tools = self.tool_registry.get_tools_by_capabilities(intent.required_capabilities)
        
        # Also consider tools that have some optional capabilities
        if intent.optional_capabilities:
            optional_tools = []
            for capability in intent.optional_capabilities:
                tools_with_optional = self.tool_registry.get_tools_by_capabilities([capability])
                optional_tools.extend(tools_with_optional)
            
            # Add unique optional tools that aren't already in candidates
            candidate_ids = {tool.id for tool in candidate_tools}
            for tool in optional_tools:
                if tool.id not in candidate_ids:
                    candidate_tools.append(tool)
        
        return candidate_tools
    
    async def _calculate_capability_score(self, tool_metadata: ToolMetadata, intent: Intent) -> float:
        """Calculate capability match score for a tool."""
        if not intent.required_capabilities and not intent.optional_capabilities:
            return 1.0  # No specific requirements
        
        tool_capabilities = {cap.name for cap in tool_metadata.capabilities}
        
        # Required capabilities score (must have all)
        required_score = 0.0
        if intent.required_capabilities:
            required_matches = sum(1 for cap in intent.required_capabilities if cap in tool_capabilities)
            required_score = required_matches / len(intent.required_capabilities)
        else:
            required_score = 1.0  # No requirements means perfect match
        
        # Optional capabilities score (bonus for having them)
        optional_score = 0.0
        if intent.optional_capabilities:
            optional_matches = sum(1 for cap in intent.optional_capabilities if cap in tool_capabilities)
            optional_score = optional_matches / len(intent.optional_capabilities)
        
        # Weight required capabilities heavily
        final_score = (required_score * 0.8) + (optional_score * 0.2)
        
        # Bonus for having additional relevant capabilities
        additional_capabilities = len(tool_capabilities) - len(intent.required_capabilities or [])
        if additional_capabilities > 0:
            bonus = min(0.1, additional_capabilities * 0.02)  # Max 10% bonus
            final_score += bonus
        
        return min(1.0, final_score)
    
    async def _calculate_performance_score(self, tool_metadata: ToolMetadata) -> float:
        """Calculate performance score based on historical metrics."""
        tool_id = tool_metadata.id
        
        # Check if we have cached metrics that are still valid
        last_calculation = self._last_performance_calculation.get(tool_id)
        if (last_calculation and 
            datetime.utcnow() - last_calculation < timedelta(minutes=5) and
            tool_id in self._cached_performance_metrics):
            return self._cached_performance_metrics[tool_id].calculate_overall_score()
        
        # Get performance metrics from registry
        registry_metrics = self.tool_registry.get_tool_performance_metrics(tool_id)
        
        # Get recent performance history
        performance_history = self._performance_history.get(tool_id, deque())
        
        # Calculate metrics
        metrics = PerformanceMetrics()
        
        if performance_history:
            # Calculate from recent history
            recent_window = datetime.utcnow() - timedelta(minutes=self.performance_window_minutes)
            recent_records = [
                record for record in performance_history 
                if record.get('timestamp', datetime.min) > recent_window
            ]
            
            if recent_records:
                # Success rate
                successful = sum(1 for r in recent_records if r.get('success', False))
                metrics.success_rate = successful / len(recent_records)
                
                # Average response time
                response_times = [r.get('response_time_ms', 0) for r in recent_records if r.get('success', False)]
                if response_times:
                    metrics.average_response_time_ms = statistics.mean(response_times)
                
                # Error rate
                errors = sum(1 for r in recent_records if not r.get('success', True))
                metrics.error_rate = errors / len(recent_records)
                
                # Recent invocations count
                metrics.recent_invocations = len(recent_records)
        
        # Fallback to registry metrics if no recent history
        if metrics.recent_invocations == 0 and registry_metrics:
            metrics.success_rate = registry_metrics.get('success_rate', 0.8)
            metrics.average_response_time_ms = registry_metrics.get('average_response_time_ms', 2000)
            metrics.error_rate = registry_metrics.get('error_rate', 0.1)
        
        # Use tool metadata performance characteristics as baseline
        if metrics.recent_invocations == 0:
            perf_chars = tool_metadata.performance_characteristics
            metrics.success_rate = perf_chars.success_rate
            metrics.average_response_time_ms = perf_chars.average_response_time_ms
            metrics.throughput_score = min(1.0, perf_chars.throughput_requests_per_minute / 100.0)
        
        # Calculate availability score (based on recent activity)
        if metrics.recent_invocations > 0:
            # Higher score for tools that have been used recently
            metrics.availability_score = min(1.0, metrics.recent_invocations / 10.0)
        else:
            metrics.availability_score = 0.5  # Default for unused tools
        
        # Cache the metrics
        self._cached_performance_metrics[tool_id] = metrics
        self._last_performance_calculation[tool_id] = datetime.utcnow()
        
        return metrics.calculate_overall_score()
    
    async def _calculate_health_score(self, tool_metadata: ToolMetadata) -> float:
        """Calculate health score for a tool."""
        health_status = self.tool_registry.get_tool_health_status(tool_metadata.id)
        
        if health_status == ToolHealthStatus.HEALTHY:
            return 1.0
        elif health_status == ToolHealthStatus.DEGRADED:
            return 0.6
        elif health_status == ToolHealthStatus.UNHEALTHY:
            return 0.1
        else:  # UNKNOWN
            return 0.5
    
    async def _calculate_context_score(self, 
                                     tool_metadata: ToolMetadata, 
                                     user_context: Optional[UserContext]) -> float:
        """Calculate context relevance score."""
        if not user_context:
            return 0.5  # Neutral score when no context
        
        score = 0.5  # Base score
        
        # MBTI type relevance
        if user_context.mbti_type and 'mbti_personalization' in [cap.name for cap in tool_metadata.capabilities]:
            score += 0.3  # Bonus for MBTI-aware tools
        
        # Location context relevance
        if (user_context.location_context and 
            any('location' in cap.name.lower() or 'district' in cap.name.lower() 
                for cap in tool_metadata.capabilities)):
            score += 0.2
        
        # Conversation history relevance
        if user_context.conversation_history:
            # Simple keyword matching with tool capabilities
            history_text = ' '.join(user_context.conversation_history).lower()
            capability_keywords = [cap.name.lower() for cap in tool_metadata.capabilities]
            
            matches = sum(1 for keyword in capability_keywords if keyword in history_text)
            if matches > 0:
                score += min(0.2, matches * 0.05)
        
        # User preferences
        if user_context.preferences:
            # Check if tool type matches user preferences
            preferred_tools = user_context.preferences.get('preferred_tools', [])
            if tool_metadata.name in preferred_tools or tool_metadata.id in preferred_tools:
                score += 0.3
            
            # Check for negative preferences
            avoided_tools = user_context.preferences.get('avoided_tools', [])
            if tool_metadata.name in avoided_tools or tool_metadata.id in avoided_tools:
                score -= 0.4
        
        return max(0.0, min(1.0, score))
    
    async def _calculate_compatibility_score(self, 
                                           tool_metadata: ToolMetadata,
                                           candidate_tools: List[ToolMetadata]) -> float:
        """Calculate compatibility score with other candidate tools."""
        if len(candidate_tools) <= 1:
            return 1.0  # Perfect compatibility when alone
        
        compatibility_scores = []
        
        for other_tool in candidate_tools:
            if other_tool.id == tool_metadata.id:
                continue
            
            # Check capability overlap (good for redundancy)
            tool_caps = {cap.name for cap in tool_metadata.capabilities}
            other_caps = {cap.name for cap in other_tool.capabilities}
            
            overlap = len(tool_caps & other_caps)
            total_caps = len(tool_caps | other_caps)
            
            if total_caps > 0:
                overlap_score = overlap / total_caps
                # Moderate overlap is good (0.2-0.6), too much or too little is bad
                if 0.2 <= overlap_score <= 0.6:
                    compatibility_scores.append(0.8)
                elif overlap_score < 0.2:
                    compatibility_scores.append(0.6)  # Complementary tools
                else:
                    compatibility_scores.append(0.4)  # Too much overlap
            else:
                compatibility_scores.append(0.5)
        
        return statistics.mean(compatibility_scores) if compatibility_scores else 1.0
    
    async def _get_fallback_tools(self, 
                                primary_tool: ToolMetadata,
                                candidate_tools: List[ToolMetadata]) -> List[ToolMetadata]:
        """Get fallback tools for a primary tool."""
        fallback_tools = []
        primary_capabilities = {cap.name for cap in primary_tool.capabilities}
        
        for tool in candidate_tools:
            if tool.id == primary_tool.id:
                continue
            
            tool_capabilities = {cap.name for cap in tool.capabilities}
            
            # Check for capability overlap
            overlap = len(primary_capabilities & tool_capabilities)
            if overlap > 0:
                # Calculate fallback suitability
                overlap_ratio = overlap / len(primary_capabilities)
                health_score = await self._calculate_health_score(tool)
                
                # Good fallback should have significant capability overlap and good health
                fallback_score = (overlap_ratio * 0.7) + (health_score * 0.3)
                
                if fallback_score > 0.5:  # Minimum threshold for fallback
                    fallback_tools.append((tool, fallback_score))
        
        # Sort by fallback score and return top candidates
        fallback_tools.sort(key=lambda x: x[1], reverse=True)
        return [tool for tool, score in fallback_tools[:3]]  # Top 3 fallbacks
    
    async def _check_tool_pair_compatibility(self, 
                                           tool1: ToolMetadata,
                                           tool2: ToolMetadata) -> Dict[str, Any]:
        """Check compatibility between two tools."""
        compatibility_result = {
            'compatible': True,
            'issues': [],
            'compatibility_score': 1.0,
            'details': {}
        }
        
        # Check for resource conflicts
        resource1 = tool1.performance_characteristics.resource_requirements
        resource2 = tool2.performance_characteristics.resource_requirements
        
        total_cpu = resource1.cpu_cores + resource2.cpu_cores
        total_memory = resource1.memory_mb + resource2.memory_mb
        
        if total_cpu > 4.0:  # Assume 4 CPU limit
            compatibility_result['issues'].append(f"High CPU usage: {total_cpu} cores")
            compatibility_result['compatibility_score'] *= 0.8
        
        if total_memory > 4096:  # Assume 4GB memory limit
            compatibility_result['issues'].append(f"High memory usage: {total_memory} MB")
            compatibility_result['compatibility_score'] *= 0.8
        
        # Check for capability conflicts (tools that do the same thing)
        caps1 = {cap.name for cap in tool1.capabilities}
        caps2 = {cap.name for cap in tool2.capabilities}
        
        overlap = caps1 & caps2
        if len(overlap) > len(caps1) * 0.8:  # More than 80% overlap
            compatibility_result['issues'].append("High capability overlap - potential redundancy")
            compatibility_result['compatibility_score'] *= 0.9
        
        # Update overall compatibility
        if compatibility_result['compatibility_score'] < 0.7:
            compatibility_result['compatible'] = False
        
        compatibility_result['details'] = {
            'cpu_usage': total_cpu,
            'memory_usage': total_memory,
            'capability_overlap': len(overlap),
            'overlap_percentage': len(overlap) / len(caps1 | caps2) if caps1 | caps2 else 0
        }
        
        return compatibility_result
    
    async def _validate_workflow_requirements(self, 
                                            tools: List[ToolMetadata],
                                            workflow_requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Validate tools against workflow-specific requirements."""
        validation_result = {
            'feasible': True,
            'issues': [],
            'recommendations': []
        }
        
        # Check execution order requirements
        if 'execution_order' in workflow_requirements:
            required_order = workflow_requirements['execution_order']
            tool_names = [tool.name for tool in tools]
            
            for i, required_tool in enumerate(required_order):
                if required_tool not in tool_names:
                    validation_result['feasible'] = False
                    validation_result['issues'].append(f"Required tool not found: {required_tool}")
        
        # Check data flow requirements
        if 'data_flow' in workflow_requirements:
            data_requirements = workflow_requirements['data_flow']
            # Validate that tools can pass data between each other
            # This would require more detailed schema analysis
            pass
        
        # Check performance requirements
        if 'max_execution_time' in workflow_requirements:
            max_time = workflow_requirements['max_execution_time']
            total_estimated_time = sum(
                tool.performance_characteristics.average_response_time_ms 
                for tool in tools
            )
            
            if total_estimated_time > max_time:
                validation_result['feasible'] = False
                validation_result['issues'].append(
                    f"Estimated execution time ({total_estimated_time}ms) exceeds limit ({max_time}ms)"
                )
        
        return validation_result
    
    async def _generate_compatibility_recommendations(self, 
                                                    tools: List[ToolMetadata],
                                                    issues: List[str]) -> List[str]:
        """Generate recommendations to resolve compatibility issues."""
        recommendations = []
        
        for issue in issues:
            if "CPU usage" in issue:
                recommendations.append("Consider using tools sequentially instead of parallel execution")
            elif "memory usage" in issue:
                recommendations.append("Consider splitting workflow into smaller batches")
            elif "capability overlap" in issue:
                recommendations.append("Remove redundant tools or use them as fallbacks")
            elif "Required tool not found" in issue:
                recommendations.append("Add missing tools to the workflow or find alternatives")
        
        return recommendations
    
    def _generate_selection_reason(self, ranking: ToolRanking) -> str:
        """Generate human-readable selection reason."""
        reasons = []
        
        if ranking.capability_score > 0.8:
            reasons.append("excellent capability match")
        elif ranking.capability_score > 0.6:
            reasons.append("good capability match")
        
        if ranking.performance_score > 0.8:
            reasons.append("high performance")
        elif ranking.performance_score < 0.4:
            reasons.append("performance concerns")
        
        if ranking.health_score > 0.8:
            reasons.append("healthy status")
        elif ranking.health_score < 0.5:
            reasons.append("health issues")
        
        if ranking.context_score > 0.7:
            reasons.append("good context fit")
        
        if not reasons:
            reasons.append("meets minimum requirements")
        
        return f"Selected for {', '.join(reasons)} (score: {ranking.overall_score:.2f})"
    
    def record_tool_execution(self, 
                            tool_id: str,
                            success: bool,
                            response_time_ms: float,
                            error_message: Optional[str] = None) -> None:
        """Record tool execution for performance tracking."""
        execution_record = {
            'timestamp': datetime.utcnow(),
            'success': success,
            'response_time_ms': response_time_ms,
            'error_message': error_message
        }
        
        self._performance_history[tool_id].append(execution_record)
        
        # Invalidate cached performance metrics
        if tool_id in self._cached_performance_metrics:
            del self._cached_performance_metrics[tool_id]
        if tool_id in self._last_performance_calculation:
            del self._last_performance_calculation[tool_id]
    
    def get_selection_statistics(self) -> Dict[str, Any]:
        """Get tool selection statistics."""
        stats = {
            'tools_with_performance_history': len(self._performance_history),
            'cached_performance_metrics': len(self._cached_performance_metrics),
            'selection_weights': {
                'capability': self.selection_weights.capability_weight,
                'performance': self.selection_weights.performance_weight,
                'health': self.selection_weights.health_weight,
                'context': self.selection_weights.context_weight,
                'compatibility': self.selection_weights.compatibility_weight
            },
            'performance_window_minutes': self.performance_window_minutes
        }
        
        # Add performance summary
        if self._performance_history:
            total_executions = sum(len(history) for history in self._performance_history.values())
            successful_executions = sum(
                sum(1 for record in history if record.get('success', False))
                for history in self._performance_history.values()
            )
            
            stats['total_executions_tracked'] = total_executions
            stats['overall_success_rate'] = successful_executions / total_executions if total_executions > 0 else 0
        
        return stats