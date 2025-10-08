"""
Tool Orchestration Engine

This module provides intelligent tool orchestration for the MBTI Travel Planner Agent,
enabling smart tool selection, workflow coordination, and performance monitoring.

Features:
- Intelligent tool selection based on request intent and context
- Multi-step workflow coordination
- Performance monitoring and metrics collection
- Error handling and fallback mechanisms
- Integration with existing AgentCore monitoring service
"""

import asyncio
import logging
import time
import uuid
import statistics
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Union, Callable, TYPE_CHECKING
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
import yaml
import json
import threading
from collections import defaultdict, deque

from .agentcore_monitoring_service import AgentCoreMonitoringService, AgentOperationType
from .tool_registry import ToolRegistry, ToolMetadata, ToolCapability
from .intent_analyzer import IntentAnalyzer
from .context_aware_analyzer import ContextAwareAnalyzer
from .advanced_tool_selector import AdvancedToolSelector, HealthCheckStrategy
from config.environment_loader import load_environment_config, GatewayEnvironmentConfig

# Type hints only imports to avoid circular dependency
if TYPE_CHECKING:
    from .restaurant_search_tool import RestaurantSearchTool
    from .restaurant_reasoning_tool import RestaurantReasoningTool


# Import shared types
from .orchestration_types import (
    RequestType, ExecutionStrategy, UserContext, Intent, 
    SelectedTool, OrchestrationResult
)


@dataclass
class OrchestrationConfig:
    """Configuration for tool orchestration engine."""
    # Intent analysis configuration
    intent_confidence_threshold: float = 0.8
    enable_context_analysis: bool = True
    
    # Tool selection configuration
    performance_weight: float = 0.4
    health_weight: float = 0.3
    capability_weight: float = 0.3
    max_fallback_tools: int = 2
    
    # Workflow configuration
    max_concurrent_workflows: int = 50
    step_timeout_seconds: int = 30
    max_retries: int = 3
    retry_backoff_multiplier: float = 2.0
    max_retry_backoff_seconds: int = 60
    
    # Performance monitoring
    enable_metrics_collection: bool = True
    enable_health_checks: bool = True
    health_check_interval_seconds: int = 30
    performance_window_seconds: int = 300
    
    # Error handling
    enable_circuit_breaker: bool = True
    circuit_breaker_failure_threshold: int = 5
    circuit_breaker_recovery_timeout: int = 60
    
    @classmethod
    def from_yaml(cls, config_path: str) -> 'OrchestrationConfig':
        """Load configuration from YAML file."""
        try:
            with open(config_path, 'r') as f:
                config_data = yaml.safe_load(f)
            
            # Extract orchestration section if it exists
            orchestration_config = config_data.get('orchestration', {})
            
            return cls(**orchestration_config)
        except Exception as e:
            logging.getLogger(__name__).warning(
                f"Failed to load orchestration config from {config_path}: {e}. Using defaults."
            )
            return cls()
    
    @classmethod
    def from_environment(cls, env_config: GatewayEnvironmentConfig) -> 'OrchestrationConfig':
        """Create configuration from environment config."""
        return cls(
            step_timeout_seconds=env_config.agent_timeout,
            max_retries=env_config.max_retries,
            # Use other environment-specific settings as needed
        )


class ToolOrchestrationEngine:
    """
    Central orchestration engine for intelligent tool selection and workflow coordination.
    
    This engine provides:
    - Intelligent tool selection based on request analysis
    - Multi-step workflow coordination
    - Performance monitoring and optimization
    - Error handling and fallback mechanisms
    - Integration with AgentCore monitoring
    """
    
    def __init__(self, 
                 config: Optional[OrchestrationConfig] = None,
                 environment: str = "production",
                 config_path: Optional[str] = None):
        """
        Initialize the tool orchestration engine.
        
        Args:
            config: Orchestration configuration
            environment: Environment name for configuration
            config_path: Path to YAML configuration file
        """
        self.environment = environment
        self.logger = logging.getLogger(f"mbti_travel_planner.orchestration")
        
        # Load configuration
        if config:
            self.config = config
        elif config_path:
            self.config = OrchestrationConfig.from_yaml(config_path)
        else:
            # Load from environment
            try:
                env_config = load_environment_config(environment)
                self.config = OrchestrationConfig.from_environment(env_config)
            except Exception as e:
                self.logger.warning(f"Failed to load environment config: {e}. Using defaults.")
                self.config = OrchestrationConfig()
        
        # Initialize core components
        self.tool_registry = ToolRegistry()
        self.monitoring_service = AgentCoreMonitoringService(
            environment=environment,
            enable_detailed_logging=self.config.enable_metrics_collection,
            enable_performance_tracking=self.config.enable_metrics_collection,
            enable_health_checks=self.config.enable_health_checks
        )
        
        # Initialize intent analysis components
        self.intent_analyzer = IntentAnalyzer(
            enable_context_analysis=self.config.enable_context_analysis
        )
        self.context_aware_analyzer = ContextAwareAnalyzer(self.intent_analyzer)
        
        # Initialize advanced tool selector
        self.tool_selector = AdvancedToolSelector(
            tool_registry=self.tool_registry,
            performance_window_minutes=self.config.performance_window_seconds // 60,
            health_check_strategy=HealthCheckStrategy.CACHED,
            enable_user_learning=True
        )
        
        # Workflow management
        self._active_workflows = {}
        self._workflow_lock = threading.Lock()
        
        # Performance tracking
        self._performance_metrics = defaultdict(lambda: deque(maxlen=1000))
        self._metrics_lock = threading.Lock()
        
        # Circuit breaker state
        self._circuit_breaker_state = defaultdict(lambda: {
            'failure_count': 0,
            'last_failure_time': None,
            'state': 'closed'  # closed, open, half_open
        })
        
        self.logger.info(f"Tool orchestration engine initialized for {environment} environment")
    
    async def orchestrate_request(self, 
                                 request_text: str,
                                 user_context: Optional[UserContext] = None,
                                 correlation_id: Optional[str] = None) -> OrchestrationResult:
        """
        Orchestrate a user request by analyzing intent and coordinating appropriate tools.
        
        Args:
            request_text: User's request text
            user_context: Optional user context for personalization
            correlation_id: Optional correlation ID for tracking
            
        Returns:
            OrchestrationResult with execution results
        """
        start_time = time.time()
        
        if not correlation_id:
            correlation_id = f"orch_{int(time.time() * 1000)}_{uuid.uuid4().hex[:8]}"
        
        self.logger.info(f"Starting request orchestration", extra={
            'correlation_id': correlation_id,
            'request_length': len(request_text),
            'has_user_context': user_context is not None
        })
        
        try:
            # Step 1: Analyze intent using the new intent analysis system
            if user_context and self.config.enable_context_analysis:
                intent = await self.context_aware_analyzer.analyze_intent_with_context(
                    request_text, user_context
                )
            else:
                intent = await self.intent_analyzer.analyze_intent(request_text, user_context)
            
            self.logger.debug(f"Intent analyzed", extra={
                'correlation_id': correlation_id,
                'intent_type': intent.type.value,
                'confidence': intent.confidence,
                'parameters': intent.parameters
            })
            
            # Step 2: Select appropriate tools using advanced selector
            selected_tools = await self.tool_selector.select_tools_with_context(
                intent=intent,
                user_context=user_context,
                max_tools=5,
                min_score_threshold=0.3,
                require_health_check=True
            )
            
            self.logger.debug(f"Tools selected", extra={
                'correlation_id': correlation_id,
                'tool_count': len(selected_tools),
                'tools': [tool.tool_name for tool in selected_tools]
            })
            
            # Step 3: Execute workflow
            results = await self._execute_workflow(
                intent, selected_tools, user_context, correlation_id
            )
            
            execution_time_ms = (time.time() - start_time) * 1000
            
            # Create result
            orchestration_result = OrchestrationResult(
                correlation_id=correlation_id,
                success=True,
                results=results,
                execution_time_ms=execution_time_ms,
                tools_used=[tool.tool_name for tool in selected_tools]
            )
            
            # Log successful orchestration
            self.monitoring_service.log_agent_invocation_result(
                correlation_id=correlation_id,
                agent_arn="tool_orchestration_engine",
                operation_type=AgentOperationType.CENTRAL_DISTRICT_WORKFLOW,
                response=None,  # We'll create a mock response object if needed
                error=None
            )
            
            self.logger.info(f"Request orchestration completed successfully", extra={
                'correlation_id': correlation_id,
                'execution_time_ms': execution_time_ms,
                'tools_used': len(selected_tools),
                'results_count': len(results)
            })
            
            return orchestration_result
            
        except Exception as e:
            execution_time_ms = (time.time() - start_time) * 1000
            
            self.logger.error(f"Request orchestration failed", extra={
                'correlation_id': correlation_id,
                'error': str(e),
                'execution_time_ms': execution_time_ms
            })
            
            # Log failed orchestration
            self.monitoring_service.log_agent_invocation_result(
                correlation_id=correlation_id,
                agent_arn="tool_orchestration_engine",
                operation_type=AgentOperationType.CENTRAL_DISTRICT_WORKFLOW,
                response=None,
                error=e
            )
            
            return OrchestrationResult(
                correlation_id=correlation_id,
                success=False,
                execution_time_ms=execution_time_ms,
                error_message=str(e)
            )
    
    async def _analyze_intent(self, 
                             request_text: str, 
                             user_context: Optional[UserContext] = None) -> Intent:
        """
        Analyze user request to determine intent and extract parameters.
        
        Args:
            request_text: User's request text
            user_context: Optional user context
            
        Returns:
            Intent object with analysis results
        """
        request_lower = request_text.lower()
        parameters = {}
        required_capabilities = []
        optional_capabilities = []
        
        # Simple pattern matching for intent classification
        # In a production system, this would use more sophisticated NLP
        
        if any(keyword in request_lower for keyword in ['search', 'find', 'restaurants', 'places']):
            if any(keyword in request_lower for keyword in ['district', 'area', 'location', 'central', 'admiralty']):
                intent_type = RequestType.RESTAURANT_SEARCH_BY_LOCATION
                required_capabilities = ['search_by_district']
                
                # Extract district names
                districts = self._extract_districts(request_text)
                if districts:
                    parameters['districts'] = districts
                    
            elif any(keyword in request_lower for keyword in ['breakfast', 'lunch', 'dinner', 'meal']):
                intent_type = RequestType.RESTAURANT_SEARCH_BY_MEAL
                required_capabilities = ['search_by_meal_type']
                
                # Extract meal types
                meal_types = self._extract_meal_types(request_text)
                if meal_types:
                    parameters['meal_types'] = meal_types
                    
            else:
                intent_type = RequestType.COMBINED_SEARCH_AND_RECOMMENDATION
                required_capabilities = ['search_restaurants', 'recommend_restaurants']
                
        elif any(keyword in request_lower for keyword in ['recommend', 'suggestion', 'best', 'top']):
            intent_type = RequestType.RESTAURANT_RECOMMENDATION
            required_capabilities = ['recommend_restaurants']
            
        elif any(keyword in request_lower for keyword in ['analyze', 'sentiment', 'review']):
            intent_type = RequestType.SENTIMENT_ANALYSIS
            required_capabilities = ['analyze_sentiment']
            
        else:
            intent_type = RequestType.UNKNOWN
        
        # Calculate confidence based on keyword matches and context
        confidence = self._calculate_intent_confidence(request_text, intent_type, user_context)
        
        # Add context-based parameters
        if user_context:
            if user_context.mbti_type:
                parameters['mbti_type'] = user_context.mbti_type
                optional_capabilities.append('mbti_personalization')
            
            if user_context.location_context:
                parameters['location_context'] = user_context.location_context
        
        return Intent(
            type=intent_type,
            confidence=confidence,
            parameters=parameters,
            required_capabilities=required_capabilities,
            optional_capabilities=optional_capabilities
        )
    
    def _extract_districts(self, text: str) -> List[str]:
        """Extract district names from text."""
        # Common Hong Kong districts
        districts = [
            'Central', 'Admiralty', 'Wan Chai', 'Causeway Bay', 'Tsim Sha Tsui',
            'Mong Kok', 'Yau Ma Tei', 'Jordan', 'Sheung Wan', 'Mid-Levels'
        ]
        
        found_districts = []
        text_lower = text.lower()
        
        for district in districts:
            if district.lower() in text_lower:
                found_districts.append(district)
        
        return found_districts
    
    def _extract_meal_types(self, text: str) -> List[str]:
        """Extract meal types from text."""
        meal_types = []
        text_lower = text.lower()
        
        if any(keyword in text_lower for keyword in ['breakfast', 'morning', 'brunch']):
            meal_types.append('breakfast')
        
        if any(keyword in text_lower for keyword in ['lunch', 'afternoon', 'midday']):
            meal_types.append('lunch')
        
        if any(keyword in text_lower for keyword in ['dinner', 'evening', 'night']):
            meal_types.append('dinner')
        
        return meal_types
    
    def _calculate_intent_confidence(self, 
                                   request_text: str, 
                                   intent_type: RequestType,
                                   user_context: Optional[UserContext] = None) -> float:
        """Calculate confidence score for intent classification."""
        base_confidence = 0.5
        
        # Keyword-based confidence boost
        keyword_matches = 0
        total_keywords = 0
        
        request_lower = request_text.lower()
        
        if intent_type == RequestType.RESTAURANT_SEARCH_BY_LOCATION:
            keywords = ['search', 'find', 'restaurants', 'district', 'area', 'location']
            keyword_matches = sum(1 for keyword in keywords if keyword in request_lower)
            total_keywords = len(keywords)
            
        elif intent_type == RequestType.RESTAURANT_SEARCH_BY_MEAL:
            keywords = ['search', 'find', 'restaurants', 'breakfast', 'lunch', 'dinner', 'meal']
            keyword_matches = sum(1 for keyword in keywords if keyword in request_lower)
            total_keywords = len(keywords)
            
        elif intent_type == RequestType.RESTAURANT_RECOMMENDATION:
            keywords = ['recommend', 'suggestion', 'best', 'top', 'good']
            keyword_matches = sum(1 for keyword in keywords if keyword in request_lower)
            total_keywords = len(keywords)
        
        if total_keywords > 0:
            keyword_confidence = keyword_matches / total_keywords
            base_confidence += keyword_confidence * 0.4
        
        # Context-based confidence boost
        if user_context and user_context.conversation_history:
            # Boost confidence if similar requests in history
            base_confidence += 0.1
        
        # Ensure confidence is within valid range
        return min(max(base_confidence, 0.0), 1.0)
    
    async def _select_tools(self, 
                           intent: Intent, 
                           user_context: Optional[UserContext] = None) -> List[SelectedTool]:
        """
        Select appropriate tools based on intent and context.
        
        Args:
            intent: Analyzed user intent
            user_context: Optional user context
            
        Returns:
            List of selected tools with metadata
        """
        # Get available tools from registry
        available_tools = self.tool_registry.get_tools_by_capabilities(intent.required_capabilities)
        
        if not available_tools:
            self.logger.warning(f"No tools found for required capabilities: {intent.required_capabilities}")
            return []
        
        selected_tools = []
        
        for tool_metadata in available_tools:
            # Check tool health and performance
            health_score = await self._get_tool_health_score(tool_metadata.id)
            performance_score = await self._get_tool_performance_score(tool_metadata.id)
            capability_score = self._calculate_capability_match_score(tool_metadata, intent)
            
            # Calculate overall selection score
            overall_score = (
                health_score * self.config.health_weight +
                performance_score * self.config.performance_weight +
                capability_score * self.config.capability_weight
            )
            
            # Get fallback tools
            fallback_tools = self._get_fallback_tools(tool_metadata, available_tools)
            
            selected_tool = SelectedTool(
                tool_id=tool_metadata.id,
                tool_name=tool_metadata.name,
                confidence=overall_score,
                expected_performance={
                    'health_score': health_score,
                    'performance_score': performance_score,
                    'capability_score': capability_score,
                    'overall_score': overall_score
                },
                fallback_tools=[t.id for t in fallback_tools[:self.config.max_fallback_tools]],
                selection_reason=f"Health: {health_score:.2f}, Performance: {performance_score:.2f}, Capability: {capability_score:.2f}"
            )
            
            selected_tools.append(selected_tool)
        
        # Sort by confidence/score
        selected_tools.sort(key=lambda t: t.confidence, reverse=True)
        
        return selected_tools
    
    async def _get_tool_health_score(self, tool_id: str) -> float:
        """Get health score for a tool (0.0 to 1.0)."""
        # Check circuit breaker state
        cb_state = self._circuit_breaker_state[tool_id]
        if cb_state['state'] == 'open':
            return 0.0
        elif cb_state['state'] == 'half_open':
            return 0.5
        
        # Get health status from registry
        health_status = self.tool_registry.get_tool_health_status(tool_id)
        
        if health_status == 'healthy':
            return 1.0
        elif health_status == 'degraded':
            return 0.7
        elif health_status == 'unhealthy':
            return 0.3
        else:
            return 0.5  # unknown status
    
    async def _get_tool_performance_score(self, tool_id: str) -> float:
        """Get performance score for a tool based on recent metrics."""
        with self._metrics_lock:
            metrics = self._performance_metrics.get(tool_id, deque())
            
            if not metrics:
                return 0.8  # Default score for tools without metrics
            
            # Calculate success rate from recent metrics
            recent_metrics = list(metrics)[-100:]  # Last 100 invocations
            if not recent_metrics:
                return 0.8
            
            success_count = sum(1 for m in recent_metrics if m.get('success', False))
            success_rate = success_count / len(recent_metrics)
            
            # Calculate average response time
            response_times = [m.get('response_time_ms', 0) for m in recent_metrics if m.get('success', False)]
            if response_times:
                avg_response_time = sum(response_times) / len(response_times)
                # Normalize response time score (lower is better)
                time_score = max(0.0, 1.0 - (avg_response_time / 10000))  # 10 seconds = 0 score
            else:
                time_score = 0.5
            
            # Combine success rate and response time
            return (success_rate * 0.7) + (time_score * 0.3)
    
    def _calculate_capability_match_score(self, tool_metadata: ToolMetadata, intent: Intent) -> float:
        """Calculate how well a tool's capabilities match the intent."""
        required_match = 0.0
        optional_match = 0.0
        
        tool_capabilities = {cap.name for cap in tool_metadata.capabilities}
        
        # Check required capabilities
        if intent.required_capabilities:
            required_matches = sum(1 for cap in intent.required_capabilities if cap in tool_capabilities)
            required_match = required_matches / len(intent.required_capabilities)
        else:
            required_match = 1.0  # No requirements means perfect match
        
        # Check optional capabilities
        if intent.optional_capabilities:
            optional_matches = sum(1 for cap in intent.optional_capabilities if cap in tool_capabilities)
            optional_match = optional_matches / len(intent.optional_capabilities)
        
        # Weight required capabilities more heavily
        return (required_match * 0.8) + (optional_match * 0.2)
    
    def _get_fallback_tools(self, primary_tool: ToolMetadata, available_tools: List[ToolMetadata]) -> List[ToolMetadata]:
        """Get fallback tools for a primary tool."""
        fallback_tools = []
        
        for tool in available_tools:
            if tool.id != primary_tool.id:
                # Check if tool has overlapping capabilities
                primary_caps = {cap.name for cap in primary_tool.capabilities}
                tool_caps = {cap.name for cap in tool.capabilities}
                
                if primary_caps & tool_caps:  # Has overlapping capabilities
                    fallback_tools.append(tool)
        
        return fallback_tools
    
    async def _execute_workflow(self, 
                               intent: Intent,
                               selected_tools: List[SelectedTool],
                               user_context: Optional[UserContext],
                               correlation_id: str) -> List[Dict[str, Any]]:
        """
        Execute workflow using selected tools.
        
        Args:
            intent: User intent
            selected_tools: Selected tools for execution
            user_context: User context
            correlation_id: Correlation ID for tracking
            
        Returns:
            List of execution results
        """
        if not selected_tools:
            raise ValueError("No tools selected for execution")
        
        results = []
        
        # For now, implement simple sequential execution
        # In the future, this can be enhanced with parallel execution and complex workflows
        
        for tool in selected_tools:
            try:
                # Check circuit breaker
                if not self._check_circuit_breaker(tool.tool_id):
                    self.logger.warning(f"Circuit breaker open for tool {tool.tool_name}")
                    continue
                
                # Execute tool
                result = await self._execute_tool(tool, intent, user_context, correlation_id)
                results.append(result)
                
                # Record successful execution
                self._record_tool_execution(tool.tool_id, True, result.get('execution_time_ms', 0))
                
                # Reset circuit breaker failure count on success
                self._circuit_breaker_state[tool.tool_id]['failure_count'] = 0
                
            except Exception as e:
                self.logger.error(f"Tool execution failed: {tool.tool_name}", extra={
                    'correlation_id': correlation_id,
                    'tool_id': tool.tool_id,
                    'error': str(e)
                })
                
                # Record failed execution
                self._record_tool_execution(tool.tool_id, False, 0)
                
                # Update circuit breaker
                self._update_circuit_breaker(tool.tool_id)
                
                # Try fallback tools if available
                fallback_result = await self._try_fallback_tools(tool, intent, user_context, correlation_id)
                if fallback_result:
                    results.append(fallback_result)
        
        return results
    
    async def _execute_tool(self, 
                           tool: SelectedTool,
                           intent: Intent,
                           user_context: Optional[UserContext],
                           correlation_id: str) -> Dict[str, Any]:
        """Execute a specific tool."""
        start_time = time.time()
        
        # Get tool instance from registry
        tool_instance = self.tool_registry.get_tool_instance(tool.tool_id)
        
        if not tool_instance:
            raise ValueError(f"Tool instance not found: {tool.tool_id}")
        
        # Prepare execution parameters
        execution_params = intent.parameters.copy()
        
        if user_context:
            execution_params.update({
                'user_id': user_context.user_id,
                'session_id': user_context.session_id,
                'mbti_type': user_context.mbti_type
            })
        
        # Execute tool based on its type
        if hasattr(tool_instance, 'search_restaurants'):
            # Restaurant search tool
            result = await tool_instance.search_restaurants(**execution_params)
        elif hasattr(tool_instance, 'recommend_restaurants'):
            # Restaurant reasoning tool
            result = await tool_instance.recommend_restaurants(**execution_params)
        elif hasattr(tool_instance, 'analyze_sentiment'):
            # Sentiment analysis tool
            result = await tool_instance.analyze_sentiment(**execution_params)
        else:
            # Generic tool execution
            result = await tool_instance.execute(**execution_params)
        
        execution_time_ms = (time.time() - start_time) * 1000
        
        # Add execution metadata
        result_with_metadata = {
            'tool_id': tool.tool_id,
            'tool_name': tool.tool_name,
            'execution_time_ms': execution_time_ms,
            'correlation_id': correlation_id,
            'result': result
        }
        
        self.logger.debug(f"Tool executed successfully", extra={
            'correlation_id': correlation_id,
            'tool_id': tool.tool_id,
            'execution_time_ms': execution_time_ms
        })
        
        return result_with_metadata
    
    def _check_circuit_breaker(self, tool_id: str) -> bool:
        """Check if circuit breaker allows execution for a tool."""
        cb_state = self._circuit_breaker_state[tool_id]
        
        if cb_state['state'] == 'closed':
            return True
        elif cb_state['state'] == 'open':
            # Check if recovery timeout has passed
            if cb_state['last_failure_time']:
                time_since_failure = time.time() - cb_state['last_failure_time']
                if time_since_failure > self.config.circuit_breaker_recovery_timeout:
                    cb_state['state'] = 'half_open'
                    return True
            return False
        elif cb_state['state'] == 'half_open':
            return True
        
        return False
    
    def _update_circuit_breaker(self, tool_id: str):
        """Update circuit breaker state after a failure."""
        cb_state = self._circuit_breaker_state[tool_id]
        cb_state['failure_count'] += 1
        cb_state['last_failure_time'] = time.time()
        
        if cb_state['failure_count'] >= self.config.circuit_breaker_failure_threshold:
            cb_state['state'] = 'open'
            self.logger.warning(f"Circuit breaker opened for tool {tool_id}")
    
    def _record_tool_execution(self, tool_id: str, success: bool, response_time_ms: float):
        """Record tool execution metrics."""
        with self._metrics_lock:
            metrics = self._performance_metrics[tool_id]
            metrics.append({
                'timestamp': time.time(),
                'success': success,
                'response_time_ms': response_time_ms
            })
    
    async def _try_fallback_tools(self, 
                                 failed_tool: SelectedTool,
                                 intent: Intent,
                                 user_context: Optional[UserContext],
                                 correlation_id: str) -> Optional[Dict[str, Any]]:
        """Try fallback tools when primary tool fails."""
        if not failed_tool.fallback_tools:
            return None
        
        for fallback_tool_id in failed_tool.fallback_tools:
            try:
                # Get fallback tool metadata
                fallback_metadata = self.tool_registry.get_tool_metadata(fallback_tool_id)
                if not fallback_metadata:
                    continue
                
                # Create fallback tool selection
                fallback_tool = SelectedTool(
                    tool_id=fallback_tool_id,
                    tool_name=fallback_metadata.name,
                    confidence=0.5,  # Lower confidence for fallback
                    expected_performance={},
                    selection_reason="Fallback tool"
                )
                
                # Execute fallback tool
                result = await self._execute_tool(fallback_tool, intent, user_context, correlation_id)
                
                self.logger.info(f"Fallback tool executed successfully", extra={
                    'correlation_id': correlation_id,
                    'primary_tool': failed_tool.tool_name,
                    'fallback_tool': fallback_tool.tool_name
                })
                
                # Mark result as fallback
                result['fallback_used'] = True
                result['primary_tool_failed'] = failed_tool.tool_name
                
                return result
                
            except Exception as e:
                self.logger.warning(f"Fallback tool also failed", extra={
                    'correlation_id': correlation_id,
                    'fallback_tool_id': fallback_tool_id,
                    'error': str(e)
                })
                continue
        
        return None
    
    def register_tool(self, tool_metadata: ToolMetadata, tool_instance: Any = None):
        """
        Register a tool with the orchestration engine.
        
        Args:
            tool_metadata: Tool metadata
            tool_instance: Optional tool instance for execution
        """
        self.tool_registry.register_tool(tool_metadata, tool_instance)
        self.logger.info(f"Tool registered with orchestration engine: {tool_metadata.name}")
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get performance metrics for all tools.
        
        Returns:
            Dictionary containing performance metrics
        """
        metrics = {}
        
        with self._metrics_lock:
            for tool_id, tool_metrics in self._performance_metrics.items():
                if not tool_metrics:
                    continue
                
                recent_metrics = list(tool_metrics)[-100:]  # Last 100 invocations
                
                success_count = sum(1 for m in recent_metrics if m.get('success', False))
                success_rate = success_count / len(recent_metrics) if recent_metrics else 0.0
                
                response_times = [m.get('response_time_ms', 0) for m in recent_metrics if m.get('success', False)]
                avg_response_time = statistics.mean(response_times) if response_times else 0.0
                
                metrics[tool_id] = {
                    'total_invocations': len(recent_metrics),
                    'success_rate': success_rate,
                    'average_response_time_ms': avg_response_time,
                    'circuit_breaker_state': self._circuit_breaker_state[tool_id]['state']
                }
        
        return metrics
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check of the orchestration engine and registered tools.
        
        Returns:
            Health check results
        """
        health_results = {
            'orchestration_engine': {
                'status': 'healthy',
                'active_workflows': len(self._active_workflows),
                'registered_tools': len(self.tool_registry._tools)
            },
            'tools': {}
        }
        
        # Check health of registered tools
        for tool_id in self.tool_registry._tools:
            try:
                health_score = await self._get_tool_health_score(tool_id)
                cb_state = self._circuit_breaker_state[tool_id]['state']
                
                if health_score >= 0.8 and cb_state == 'closed':
                    status = 'healthy'
                elif health_score >= 0.5 or cb_state == 'half_open':
                    status = 'degraded'
                else:
                    status = 'unhealthy'
                
                health_results['tools'][tool_id] = {
                    'status': status,
                    'health_score': health_score,
                    'circuit_breaker_state': cb_state
                }
                
            except Exception as e:
                health_results['tools'][tool_id] = {
                    'status': 'error',
                    'error': str(e)
                }
        
        return health_results
    
    def shutdown(self):
        """Shutdown the orchestration engine gracefully."""
        self.logger.info("Shutting down tool orchestration engine")
        
        # Cancel active workflows
        with self._workflow_lock:
            for workflow_id in list(self._active_workflows.keys()):
                try:
                    workflow = self._active_workflows[workflow_id]
                    if hasattr(workflow, 'cancel'):
                        workflow.cancel()
                except Exception as e:
                    self.logger.error(f"Error canceling workflow {workflow_id}: {e}")
            
            self._active_workflows.clear()
        
        self.logger.info("Tool orchestration engine shutdown complete")
    
    def _check_circuit_breaker(self, tool_id: str) -> bool:
        """Check if circuit breaker allows execution."""
        cb_state = self._circuit_breaker_state[tool_id]
        
        if cb_state['state'] == 'closed':
            return True
        elif cb_state['state'] == 'open':
            # Check if recovery timeout has passed
            if (cb_state['last_failure_time'] and 
                time.time() - cb_state['last_failure_time'] > self.config.circuit_breaker_recovery_timeout):
                cb_state['state'] = 'half_open'
                return True
            return False
        elif cb_state['state'] == 'half_open':
            return True
        
        return False
    
    def _update_circuit_breaker(self, tool_id: str) -> None:
        """Update circuit breaker state after failure."""
        cb_state = self._circuit_breaker_state[tool_id]
        cb_state['failure_count'] += 1
        cb_state['last_failure_time'] = time.time()
        
        if cb_state['failure_count'] >= self.config.circuit_breaker_failure_threshold:
            cb_state['state'] = 'open'
            self.logger.warning(f"Circuit breaker opened for tool {tool_id}")
    
    def _record_tool_execution(self, tool_id: str, success: bool, response_time_ms: float) -> None:
        """Record tool execution metrics."""
        with self._metrics_lock:
            self._performance_metrics[tool_id].append({
                'timestamp': time.time(),
                'success': success,
                'response_time_ms': response_time_ms
            })
    
    async def _try_fallback_tools(self, 
                                 failed_tool: SelectedTool,
                                 intent: Intent,
                                 user_context: Optional[UserContext],
                                 correlation_id: str) -> Optional[Dict[str, Any]]:
        """Try fallback tools when primary tool fails."""
        for fallback_tool_id in failed_tool.fallback_tools:
            try:
                fallback_metadata = self.tool_registry.get_tool_metadata(fallback_tool_id)
                if not fallback_metadata:
                    continue
                
                fallback_tool = SelectedTool(
                    tool_id=fallback_tool_id,
                    tool_name=fallback_metadata.name,
                    confidence=0.5,  # Lower confidence for fallback
                    expected_performance={},
                    selection_reason="Fallback tool"
                )
                
                result = await self._execute_tool(fallback_tool, intent, user_context, correlation_id)
                result['fallback_used'] = True
                
                self.logger.info(f"Fallback tool succeeded: {fallback_metadata.name}", extra={
                    'correlation_id': correlation_id,
                    'original_tool': failed_tool.tool_name,
                    'fallback_tool': fallback_metadata.name
                })
                
                return result
                
            except Exception as e:
                self.logger.warning(f"Fallback tool also failed: {fallback_tool_id}", extra={
                    'correlation_id': correlation_id,
                    'error': str(e)
                })
                continue
        
        return None
    
    def register_tool(self, tool_metadata: ToolMetadata, tool_instance: Any) -> None:
        """Register a tool with the orchestration engine."""
        self.tool_registry.register_tool(tool_metadata, tool_instance)
        self.logger.info(f"Tool registered: {tool_metadata.name} ({tool_metadata.id})")
    
    def get_performance_metrics(self, window_minutes: int = 60) -> Dict[str, Any]:
        """Get performance metrics for the orchestration engine."""
        with self._metrics_lock:
            metrics = {}
            
            for tool_id, tool_metrics in self._performance_metrics.items():
                cutoff_time = time.time() - (window_minutes * 60)
                recent_metrics = [m for m in tool_metrics if m['timestamp'] > cutoff_time]
                
                if recent_metrics:
                    success_count = sum(1 for m in recent_metrics if m['success'])
                    total_count = len(recent_metrics)
                    avg_response_time = sum(m['response_time_ms'] for m in recent_metrics) / total_count
                    
                    metrics[tool_id] = {
                        'total_executions': total_count,
                        'success_rate': success_count / total_count,
                        'average_response_time_ms': avg_response_time,
                        'circuit_breaker_state': self._circuit_breaker_state[tool_id]['state']
                    }
            
            return metrics
    
    def get_orchestration_status(self) -> Dict[str, Any]:
        """Get current orchestration engine status."""
        return {
            'environment': self.environment,
            'registered_tools': len(self.tool_registry.get_all_tools()),
            'active_workflows': len(self._active_workflows),
            'circuit_breaker_states': {
                tool_id: state['state'] 
                for tool_id, state in self._circuit_breaker_state.items()
            },
            'config': {
                'max_concurrent_workflows': self.config.max_concurrent_workflows,
                'step_timeout_seconds': self.config.step_timeout_seconds,
                'max_retries': self.config.max_retries,
                'enable_circuit_breaker': self.config.enable_circuit_breaker
            }
        }