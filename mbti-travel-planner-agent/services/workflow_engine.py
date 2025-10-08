"""
Workflow Engine

This module provides workflow coordination capabilities for multi-step tool execution,
data mapping and transformation between workflow steps, and result aggregation.

Features:
- Step-by-step workflow execution
- Data mapping and transformation between steps
- Result aggregation and response formatting
- Support for sequential, parallel, and conditional execution strategies
- Integration with tool orchestration engine
"""

import asyncio
import logging
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Union, Callable, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
import json
from collections import defaultdict

from .orchestration_types import (
    RequestType, ExecutionStrategy, UserContext, Intent, 
    SelectedTool, OrchestrationResult
)


class WorkflowStatus(Enum):
    """Workflow execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StepStatus(Enum):
    """Workflow step execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class DataMapping:
    """Data mapping configuration for workflow steps."""
    source_field: str
    target_field: str
    transformation: Optional[str] = None  # JSON path or transformation function name
    required: bool = True
    default_value: Any = None


@dataclass
class WorkflowStep:
    """Individual step in a workflow."""
    id: str
    tool_id: str
    tool_name: str
    input_mapping: List[DataMapping] = field(default_factory=list)
    output_mapping: List[DataMapping] = field(default_factory=list)
    depends_on: List[str] = field(default_factory=list)  # Step IDs this step depends on
    condition: Optional[str] = None  # Condition for conditional execution
    timeout_seconds: int = 30
    retry_count: int = 0
    max_retries: int = 3
    status: StepStatus = StepStatus.PENDING
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    execution_time_ms: float = 0.0
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging."""
        return {
            'id': self.id,
            'tool_id': self.tool_id,
            'tool_name': self.tool_name,
            'status': self.status.value,
            'execution_time_ms': self.execution_time_ms,
            'retry_count': self.retry_count,
            'error': self.error
        }


@dataclass
class Workflow:
    """Workflow definition with steps and execution strategy."""
    id: str
    name: str
    description: str
    steps: List[WorkflowStep] = field(default_factory=list)
    execution_strategy: ExecutionStrategy = ExecutionStrategy.SEQUENTIAL
    status: WorkflowStatus = WorkflowStatus.PENDING
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    execution_time_ms: float = 0.0
    context_data: Dict[str, Any] = field(default_factory=dict)
    results: List[Dict[str, Any]] = field(default_factory=list)
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'execution_strategy': self.execution_strategy.value,
            'status': self.status.value,
            'execution_time_ms': self.execution_time_ms,
            'steps_count': len(self.steps),
            'completed_steps': len([s for s in self.steps if s.status == StepStatus.COMPLETED]),
            'failed_steps': len([s for s in self.steps if s.status == StepStatus.FAILED]),
            'error': self.error
        }


@dataclass
class WorkflowResult:
    """Result of workflow execution."""
    workflow_id: str
    correlation_id: str
    success: bool
    results: List[Dict[str, Any]] = field(default_factory=list)
    aggregated_result: Optional[Dict[str, Any]] = None
    execution_time_ms: float = 0.0
    steps_executed: int = 0
    steps_failed: int = 0
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging."""
        return asdict(self)


@dataclass
class ExecutionContext:
    """Context for workflow execution."""
    correlation_id: str
    user_context: Optional[UserContext] = None
    intent: Optional[Intent] = None
    workflow_data: Dict[str, Any] = field(default_factory=dict)
    step_results: Dict[str, Any] = field(default_factory=dict)  # Results from completed steps
    
    def get_step_result(self, step_id: str) -> Optional[Dict[str, Any]]:
        """Get result from a completed step."""
        return self.step_results.get(step_id)
    
    def set_step_result(self, step_id: str, result: Dict[str, Any]) -> None:
        """Set result for a completed step."""
        self.step_results[step_id] = result
    
    def get_mapped_data(self, mappings: List[DataMapping]) -> Dict[str, Any]:
        """Get data based on input mappings."""
        mapped_data = {}
        
        for mapping in mappings:
            try:
                # Get source data
                source_value = self._get_nested_value(mapping.source_field)
                
                if source_value is not None:
                    # Apply transformation if specified
                    if mapping.transformation:
                        source_value = self._apply_transformation(source_value, mapping.transformation)
                    
                    mapped_data[mapping.target_field] = source_value
                elif mapping.required and mapping.default_value is not None:
                    mapped_data[mapping.target_field] = mapping.default_value
                elif mapping.required:
                    raise ValueError(f"Required field {mapping.source_field} not found and no default value provided")
                    
            except Exception as e:
                if mapping.required:
                    raise ValueError(f"Failed to map field {mapping.source_field}: {e}")
        
        return mapped_data
    
    def _get_nested_value(self, field_path: str) -> Any:
        """Get nested value using dot notation (e.g., 'step1.result.data')."""
        parts = field_path.split('.')
        
        # Check different data sources
        if parts[0] == 'context':
            # User context data
            if self.user_context:
                return self._traverse_dict(self.user_context.__dict__, parts[1:])
        elif parts[0] == 'intent':
            # Intent data
            if self.intent:
                return self._traverse_dict(self.intent.__dict__, parts[1:])
        elif parts[0] == 'workflow':
            # Workflow data
            return self._traverse_dict(self.workflow_data, parts[1:])
        elif parts[0] in self.step_results:
            # Step result data
            return self._traverse_dict(self.step_results[parts[0]], parts[1:])
        else:
            # Try workflow data as fallback
            return self._traverse_dict(self.workflow_data, parts)
        
        return None
    
    def _traverse_dict(self, data: Dict[str, Any], path: List[str]) -> Any:
        """Traverse nested dictionary using path."""
        current = data
        
        for part in path:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None
        
        return current
    
    def _apply_transformation(self, value: Any, transformation: str) -> Any:
        """Apply transformation to value."""
        # Simple transformations - can be extended
        if transformation == 'to_string':
            return str(value)
        elif transformation == 'to_list':
            if isinstance(value, list):
                return value
            return [value]
        elif transformation == 'flatten':
            if isinstance(value, list):
                flattened = []
                for item in value:
                    if isinstance(item, list):
                        flattened.extend(item)
                    else:
                        flattened.append(item)
                return flattened
        elif transformation == 'extract_ids':
            if isinstance(value, list):
                return [item.get('id') for item in value if isinstance(item, dict) and 'id' in item]
        
        return value


class WorkflowEngine:
    """
    Workflow engine for coordinating multi-step tool execution.
    
    This engine provides:
    - Step-by-step workflow execution
    - Data mapping and transformation between steps
    - Result aggregation and response formatting
    - Support for different execution strategies
    """
    
    def __init__(self, 
                 max_concurrent_workflows: int = 50,
                 default_step_timeout: int = 30,
                 enable_detailed_logging: bool = True):
        """
        Initialize the workflow engine.
        
        Args:
            max_concurrent_workflows: Maximum number of concurrent workflows
            default_step_timeout: Default timeout for workflow steps in seconds
            enable_detailed_logging: Enable detailed logging
        """
        self.max_concurrent_workflows = max_concurrent_workflows
        self.default_step_timeout = default_step_timeout
        self.enable_detailed_logging = enable_detailed_logging
        
        self.logger = logging.getLogger(f"mbti_travel_planner.workflow_engine")
        
        # Active workflows tracking
        self._active_workflows: Dict[str, Workflow] = {}
        self._workflow_semaphore = asyncio.Semaphore(max_concurrent_workflows)
        
        # Workflow templates
        self._workflow_templates: Dict[str, Callable] = {}
        self._register_default_templates()
        
        self.logger.info(f"Workflow engine initialized with max concurrent workflows: {max_concurrent_workflows}")
    
    async def execute_workflow(self, 
                              workflow: Workflow,
                              context: ExecutionContext) -> WorkflowResult:
        """
        Execute a workflow with the given context.
        
        Args:
            workflow: Workflow to execute
            context: Execution context
            
        Returns:
            WorkflowResult with execution results
        """
        start_time = time.time()
        
        # Acquire semaphore to limit concurrent workflows
        async with self._workflow_semaphore:
            self.logger.info(f"Starting workflow execution", extra={
                'workflow_id': workflow.id,
                'correlation_id': context.correlation_id,
                'steps_count': len(workflow.steps),
                'execution_strategy': workflow.execution_strategy.value
            })
            
            # Track active workflow
            self._active_workflows[workflow.id] = workflow
            
            try:
                workflow.status = WorkflowStatus.RUNNING
                workflow.start_time = datetime.now()
                
                # Execute workflow based on strategy
                if workflow.execution_strategy == ExecutionStrategy.SEQUENTIAL:
                    results = await self._execute_sequential(workflow, context)
                elif workflow.execution_strategy == ExecutionStrategy.PARALLEL:
                    results = await self._execute_parallel(workflow, context)
                elif workflow.execution_strategy == ExecutionStrategy.CONDITIONAL:
                    results = await self._execute_conditional(workflow, context)
                else:
                    raise ValueError(f"Unsupported execution strategy: {workflow.execution_strategy}")
                
                # Aggregate results
                aggregated_result = self._aggregate_results(results, workflow, context)
                
                workflow.status = WorkflowStatus.COMPLETED
                workflow.end_time = datetime.now()
                workflow.execution_time_ms = (time.time() - start_time) * 1000
                workflow.results = results
                
                # Count execution statistics
                steps_executed = len([s for s in workflow.steps if s.status == StepStatus.COMPLETED])
                steps_failed = len([s for s in workflow.steps if s.status == StepStatus.FAILED])
                
                self.logger.info(f"Workflow execution completed successfully", extra={
                    'workflow_id': workflow.id,
                    'correlation_id': context.correlation_id,
                    'execution_time_ms': workflow.execution_time_ms,
                    'steps_executed': steps_executed,
                    'steps_failed': steps_failed
                })
                
                return WorkflowResult(
                    workflow_id=workflow.id,
                    correlation_id=context.correlation_id,
                    success=True,
                    results=results,
                    aggregated_result=aggregated_result,
                    execution_time_ms=workflow.execution_time_ms,
                    steps_executed=steps_executed,
                    steps_failed=steps_failed
                )
                
            except Exception as e:
                workflow.status = WorkflowStatus.FAILED
                workflow.end_time = datetime.now()
                workflow.execution_time_ms = (time.time() - start_time) * 1000
                workflow.error = str(e)
                
                steps_executed = len([s for s in workflow.steps if s.status == StepStatus.COMPLETED])
                steps_failed = len([s for s in workflow.steps if s.status == StepStatus.FAILED])
                
                self.logger.error(f"Workflow execution failed", extra={
                    'workflow_id': workflow.id,
                    'correlation_id': context.correlation_id,
                    'error': str(e),
                    'execution_time_ms': workflow.execution_time_ms,
                    'steps_executed': steps_executed,
                    'steps_failed': steps_failed
                })
                
                return WorkflowResult(
                    workflow_id=workflow.id,
                    correlation_id=context.correlation_id,
                    success=False,
                    execution_time_ms=workflow.execution_time_ms,
                    steps_executed=steps_executed,
                    steps_failed=steps_failed,
                    error_message=str(e)
                )
                
            finally:
                # Remove from active workflows
                self._active_workflows.pop(workflow.id, None)
    
    async def execute_step(self, 
                          step: WorkflowStep,
                          context: ExecutionContext) -> Dict[str, Any]:
        """
        Execute a single workflow step.
        
        Args:
            step: Workflow step to execute
            context: Execution context
            
        Returns:
            Step execution result
        """
        start_time = time.time()
        
        self.logger.debug(f"Executing workflow step", extra={
            'step_id': step.id,
            'tool_name': step.tool_name,
            'correlation_id': context.correlation_id
        })
        
        try:
            step.status = StepStatus.RUNNING
            step.start_time = datetime.now()
            
            # Get input data based on mappings
            input_data = context.get_mapped_data(step.input_mapping)
            
            # Add context data
            if context.user_context:
                input_data.update({
                    'user_id': context.user_context.user_id,
                    'session_id': context.user_context.session_id,
                    'mbti_type': context.user_context.mbti_type
                })
            
            # Execute step with timeout
            result = await asyncio.wait_for(
                self._execute_step_tool(step, input_data, context),
                timeout=step.timeout_seconds
            )
            
            step.status = StepStatus.COMPLETED
            step.end_time = datetime.now()
            step.execution_time_ms = (time.time() - start_time) * 1000
            step.result = result
            
            # Apply output mappings and store in context
            if step.output_mapping:
                mapped_output = self._apply_output_mappings(result, step.output_mapping)
                context.set_step_result(step.id, mapped_output)
            else:
                context.set_step_result(step.id, result)
            
            self.logger.debug(f"Workflow step completed successfully", extra={
                'step_id': step.id,
                'tool_name': step.tool_name,
                'correlation_id': context.correlation_id,
                'execution_time_ms': step.execution_time_ms
            })
            
            return result
            
        except asyncio.TimeoutError:
            step.status = StepStatus.FAILED
            step.end_time = datetime.now()
            step.execution_time_ms = (time.time() - start_time) * 1000
            step.error = f"Step timed out after {step.timeout_seconds} seconds"
            
            self.logger.error(f"Workflow step timed out", extra={
                'step_id': step.id,
                'tool_name': step.tool_name,
                'correlation_id': context.correlation_id,
                'timeout_seconds': step.timeout_seconds
            })
            
            raise Exception(step.error)
            
        except Exception as e:
            step.status = StepStatus.FAILED
            step.end_time = datetime.now()
            step.execution_time_ms = (time.time() - start_time) * 1000
            step.error = str(e)
            
            self.logger.error(f"Workflow step failed", extra={
                'step_id': step.id,
                'tool_name': step.tool_name,
                'correlation_id': context.correlation_id,
                'error': str(e),
                'execution_time_ms': step.execution_time_ms
            })
            
            raise
    
    async def _execute_step_tool(self, 
                                step: WorkflowStep,
                                input_data: Dict[str, Any],
                                context: ExecutionContext) -> Dict[str, Any]:
        """Execute the actual tool for a workflow step."""
        # This is a placeholder - in a real implementation, this would
        # integrate with the tool orchestration engine to execute the actual tool
        
        # For now, simulate tool execution based on tool type
        if 'search' in step.tool_name.lower():
            # Simulate restaurant search
            return {
                'restaurants': [
                    {'id': '1', 'name': 'Restaurant A', 'district': 'Central'},
                    {'id': '2', 'name': 'Restaurant B', 'district': 'Admiralty'}
                ],
                'total_count': 2,
                'search_parameters': input_data
            }
        elif 'recommend' in step.tool_name.lower():
            # Simulate restaurant recommendation
            return {
                'recommendations': [
                    {'restaurant_id': '1', 'score': 0.95, 'reason': 'Perfect MBTI match'},
                    {'restaurant_id': '2', 'score': 0.87, 'reason': 'Good location match'}
                ],
                'recommendation_parameters': input_data
            }
        else:
            # Generic tool execution
            return {
                'result': 'Tool executed successfully',
                'input_parameters': input_data,
                'tool_name': step.tool_name
            }
    
    def _apply_output_mappings(self, 
                              result: Dict[str, Any],
                              mappings: List[DataMapping]) -> Dict[str, Any]:
        """Apply output mappings to step result."""
        mapped_result = {}
        
        for mapping in mappings:
            try:
                # Get source value from result
                source_value = self._get_nested_dict_value(result, mapping.source_field)
                
                if source_value is not None:
                    # Apply transformation if specified
                    if mapping.transformation:
                        source_value = self._apply_simple_transformation(source_value, mapping.transformation)
                    
                    mapped_result[mapping.target_field] = source_value
                elif mapping.default_value is not None:
                    mapped_result[mapping.target_field] = mapping.default_value
                    
            except Exception as e:
                self.logger.warning(f"Failed to apply output mapping {mapping.source_field}: {e}")
        
        return mapped_result
    
    def _get_nested_dict_value(self, data: Dict[str, Any], path: str) -> Any:
        """Get nested dictionary value using dot notation."""
        parts = path.split('.')
        current = data
        
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None
        
        return current
    
    def _apply_simple_transformation(self, value: Any, transformation: str) -> Any:
        """Apply simple transformation to value."""
        if transformation == 'to_string':
            return str(value)
        elif transformation == 'to_list':
            return [value] if not isinstance(value, list) else value
        elif transformation == 'count':
            return len(value) if hasattr(value, '__len__') else 0
        
        return value
    
    async def _execute_sequential(self, 
                                 workflow: Workflow,
                                 context: ExecutionContext) -> List[Dict[str, Any]]:
        """Execute workflow steps sequentially."""
        results = []
        
        for step in workflow.steps:
            # Check dependencies
            if not self._check_step_dependencies(step, workflow):
                step.status = StepStatus.SKIPPED
                self.logger.info(f"Skipping step due to unmet dependencies", extra={
                    'step_id': step.id,
                    'dependencies': step.depends_on
                })
                continue
            
            # Check condition
            if step.condition and not self._evaluate_condition(step.condition, context):
                step.status = StepStatus.SKIPPED
                self.logger.info(f"Skipping step due to condition", extra={
                    'step_id': step.id,
                    'condition': step.condition
                })
                continue
            
            try:
                result = await self.execute_step(step, context)
                results.append({
                    'step_id': step.id,
                    'step_name': step.tool_name,
                    'result': result,
                    'execution_time_ms': step.execution_time_ms
                })
            except Exception as e:
                # Handle step failure
                self.logger.error(f"Step failed in sequential execution", extra={
                    'step_id': step.id,
                    'error': str(e)
                })
                
                # For sequential execution, we might want to stop on failure
                # or continue based on configuration
                results.append({
                    'step_id': step.id,
                    'step_name': step.tool_name,
                    'error': str(e),
                    'execution_time_ms': step.execution_time_ms
                })
        
        return results
    
    async def _execute_parallel(self, 
                               workflow: Workflow,
                               context: ExecutionContext) -> List[Dict[str, Any]]:
        """Execute workflow steps in parallel where possible."""
        # Group steps by dependency levels
        dependency_levels = self._group_steps_by_dependencies(workflow.steps)
        results = []
        
        for level_steps in dependency_levels:
            # Execute steps at this level in parallel
            tasks = []
            
            for step in level_steps:
                # Check condition
                if step.condition and not self._evaluate_condition(step.condition, context):
                    step.status = StepStatus.SKIPPED
                    continue
                
                tasks.append(self.execute_step(step, context))
            
            if tasks:
                # Wait for all tasks at this level to complete
                level_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for i, result in enumerate(level_results):
                    step = level_steps[i]
                    if isinstance(result, Exception):
                        results.append({
                            'step_id': step.id,
                            'step_name': step.tool_name,
                            'error': str(result),
                            'execution_time_ms': step.execution_time_ms
                        })
                    else:
                        results.append({
                            'step_id': step.id,
                            'step_name': step.tool_name,
                            'result': result,
                            'execution_time_ms': step.execution_time_ms
                        })
        
        return results
    
    async def _execute_conditional(self, 
                                  workflow: Workflow,
                                  context: ExecutionContext) -> List[Dict[str, Any]]:
        """Execute workflow steps with conditional logic."""
        # For conditional execution, we evaluate each step's condition
        # and dependencies dynamically
        results = []
        remaining_steps = workflow.steps.copy()
        
        while remaining_steps:
            executed_in_round = False
            
            for step in remaining_steps.copy():
                # Check dependencies
                if not self._check_step_dependencies(step, workflow):
                    continue
                
                # Check condition
                if step.condition and not self._evaluate_condition(step.condition, context):
                    step.status = StepStatus.SKIPPED
                    remaining_steps.remove(step)
                    executed_in_round = True
                    continue
                
                try:
                    result = await self.execute_step(step, context)
                    results.append({
                        'step_id': step.id,
                        'step_name': step.tool_name,
                        'result': result,
                        'execution_time_ms': step.execution_time_ms
                    })
                    remaining_steps.remove(step)
                    executed_in_round = True
                except Exception as e:
                    results.append({
                        'step_id': step.id,
                        'step_name': step.tool_name,
                        'error': str(e),
                        'execution_time_ms': step.execution_time_ms
                    })
                    remaining_steps.remove(step)
                    executed_in_round = True
            
            # If no steps were executed in this round, we might have circular dependencies
            if not executed_in_round:
                self.logger.warning("No steps executed in conditional round - possible circular dependencies")
                break
        
        return results
    
    def _check_step_dependencies(self, step: WorkflowStep, workflow: Workflow) -> bool:
        """Check if step dependencies are satisfied."""
        if not step.depends_on:
            return True
        
        for dep_step_id in step.depends_on:
            dep_step = next((s for s in workflow.steps if s.id == dep_step_id), None)
            if not dep_step or dep_step.status != StepStatus.COMPLETED:
                return False
        
        return True
    
    def _evaluate_condition(self, condition: str, context: ExecutionContext) -> bool:
        """Evaluate a step condition."""
        # Simple condition evaluation - can be extended with more complex logic
        try:
            # For now, support simple conditions like:
            # - "step1.result.count > 0"
            # - "context.mbti_type == 'ENFP'"
            
            # This is a simplified implementation
            # In production, you'd want a more robust expression evaluator
            
            if '>' in condition:
                left, right = condition.split('>')
                left_val = context._get_nested_value(left.strip())
                right_val = float(right.strip())
                return left_val is not None and float(left_val) > right_val
            elif '==' in condition:
                left, right = condition.split('==')
                left_val = context._get_nested_value(left.strip())
                right_val = right.strip().strip("'\"")
                return left_val == right_val
            elif 'exists' in condition:
                field = condition.replace('exists', '').strip()
                return context._get_nested_value(field) is not None
            
            return True  # Default to true for unknown conditions
            
        except Exception as e:
            self.logger.warning(f"Failed to evaluate condition '{condition}': {e}")
            return True  # Default to true on evaluation error
    
    def _group_steps_by_dependencies(self, steps: List[WorkflowStep]) -> List[List[WorkflowStep]]:
        """Group steps by dependency levels for parallel execution."""
        levels = []
        remaining_steps = steps.copy()
        completed_steps = set()
        
        while remaining_steps:
            current_level = []
            
            for step in remaining_steps.copy():
                # Check if all dependencies are satisfied
                if all(dep in completed_steps for dep in step.depends_on):
                    current_level.append(step)
                    remaining_steps.remove(step)
            
            if not current_level:
                # No steps can be executed - possible circular dependency
                self.logger.warning("Circular dependency detected in workflow steps")
                break
            
            levels.append(current_level)
            completed_steps.update(step.id for step in current_level)
        
        return levels
    
    def _aggregate_results(self, 
                          results: List[Dict[str, Any]],
                          workflow: Workflow,
                          context: ExecutionContext) -> Dict[str, Any]:
        """Aggregate workflow results into a single response."""
        aggregated = {
            'workflow_id': workflow.id,
            'workflow_name': workflow.name,
            'execution_strategy': workflow.execution_strategy.value,
            'total_steps': len(workflow.steps),
            'successful_steps': len([r for r in results if 'error' not in r]),
            'failed_steps': len([r for r in results if 'error' in r]),
            'total_execution_time_ms': sum(r.get('execution_time_ms', 0) for r in results),
            'step_results': results
        }
        
        # Extract specific result types for easier access
        search_results = []
        recommendations = []
        
        for result in results:
            if 'result' in result:
                step_result = result['result']
                
                if 'restaurants' in step_result:
                    search_results.extend(step_result['restaurants'])
                elif 'recommendations' in step_result:
                    recommendations.extend(step_result['recommendations'])
        
        if search_results:
            aggregated['restaurants'] = search_results
        
        if recommendations:
            aggregated['recommendations'] = recommendations
        
        return aggregated
    
    def create_workflow_from_intent(self, 
                                   intent: Intent,
                                   selected_tools: List[SelectedTool]) -> Workflow:
        """
        Create a workflow from intent and selected tools.
        
        Args:
            intent: User intent
            selected_tools: Selected tools for execution
            
        Returns:
            Workflow configured for the intent
        """
        workflow_id = f"workflow_{int(time.time() * 1000)}_{uuid.uuid4().hex[:8]}"
        
        # Determine workflow type based on intent
        if intent.type == RequestType.COMBINED_SEARCH_AND_RECOMMENDATION:
            return self._create_search_then_recommend_workflow(workflow_id, intent, selected_tools)
        elif intent.type in [RequestType.RESTAURANT_SEARCH_BY_LOCATION, RequestType.RESTAURANT_SEARCH_BY_MEAL]:
            return self._create_simple_search_workflow(workflow_id, intent, selected_tools)
        elif intent.type == RequestType.RESTAURANT_RECOMMENDATION:
            return self._create_simple_recommendation_workflow(workflow_id, intent, selected_tools)
        else:
            return self._create_generic_workflow(workflow_id, intent, selected_tools)
    
    def _create_search_then_recommend_workflow(self, 
                                             workflow_id: str,
                                             intent: Intent,
                                             selected_tools: List[SelectedTool]) -> Workflow:
        """Create a search-then-recommend workflow."""
        steps = []
        
        # Find search and recommendation tools
        search_tools = [t for t in selected_tools if 'search' in t.tool_name.lower()]
        recommend_tools = [t for t in selected_tools if 'recommend' in t.tool_name.lower()]
        
        # Step 1: Search for restaurants
        if search_tools:
            search_tool = search_tools[0]
            search_step = WorkflowStep(
                id="search_step",
                tool_id=search_tool.tool_id,
                tool_name=search_tool.tool_name,
                input_mapping=[
                    DataMapping(source_field="intent.parameters.districts", target_field="districts", required=False),
                    DataMapping(source_field="intent.parameters.meal_types", target_field="meal_types", required=False),
                    DataMapping(source_field="context.mbti_type", target_field="mbti_type", required=False)
                ],
                output_mapping=[
                    DataMapping(source_field="restaurants", target_field="restaurants"),
                    DataMapping(source_field="total_count", target_field="restaurant_count")
                ]
            )
            steps.append(search_step)
        
        # Step 2: Get recommendations based on search results
        if recommend_tools and search_tools:
            recommend_tool = recommend_tools[0]
            recommend_step = WorkflowStep(
                id="recommend_step",
                tool_id=recommend_tool.tool_id,
                tool_name=recommend_tool.tool_name,
                depends_on=["search_step"],
                condition="search_step.restaurant_count > 0",
                input_mapping=[
                    DataMapping(source_field="search_step.restaurants", target_field="restaurants"),
                    DataMapping(source_field="context.mbti_type", target_field="mbti_type", required=False)
                ],
                output_mapping=[
                    DataMapping(source_field="recommendations", target_field="recommendations")
                ]
            )
            steps.append(recommend_step)
        
        return Workflow(
            id=workflow_id,
            name="Search Then Recommend",
            description="Search for restaurants then provide personalized recommendations",
            steps=steps,
            execution_strategy=ExecutionStrategy.SEQUENTIAL
        )
    
    def _create_simple_search_workflow(self, 
                                     workflow_id: str,
                                     intent: Intent,
                                     selected_tools: List[SelectedTool]) -> Workflow:
        """Create a simple search workflow."""
        steps = []
        
        for i, tool in enumerate(selected_tools):
            step = WorkflowStep(
                id=f"search_step_{i}",
                tool_id=tool.tool_id,
                tool_name=tool.tool_name,
                input_mapping=[
                    DataMapping(source_field="intent.parameters.districts", target_field="districts", required=False),
                    DataMapping(source_field="intent.parameters.meal_types", target_field="meal_types", required=False)
                ]
            )
            steps.append(step)
        
        return Workflow(
            id=workflow_id,
            name="Restaurant Search",
            description="Search for restaurants based on criteria",
            steps=steps,
            execution_strategy=ExecutionStrategy.PARALLEL if len(steps) > 1 else ExecutionStrategy.SEQUENTIAL
        )
    
    def _create_simple_recommendation_workflow(self, 
                                             workflow_id: str,
                                             intent: Intent,
                                             selected_tools: List[SelectedTool]) -> Workflow:
        """Create a simple recommendation workflow."""
        steps = []
        
        for i, tool in enumerate(selected_tools):
            step = WorkflowStep(
                id=f"recommend_step_{i}",
                tool_id=tool.tool_id,
                tool_name=tool.tool_name,
                input_mapping=[
                    DataMapping(source_field="intent.parameters.restaurants", target_field="restaurants", required=False),
                    DataMapping(source_field="context.mbti_type", target_field="mbti_type", required=False)
                ]
            )
            steps.append(step)
        
        return Workflow(
            id=workflow_id,
            name="Restaurant Recommendation",
            description="Provide personalized restaurant recommendations",
            steps=steps,
            execution_strategy=ExecutionStrategy.SEQUENTIAL
        )
    
    def _create_generic_workflow(self, 
                               workflow_id: str,
                               intent: Intent,
                               selected_tools: List[SelectedTool]) -> Workflow:
        """Create a generic workflow for unknown intent types."""
        steps = []
        
        for i, tool in enumerate(selected_tools):
            step = WorkflowStep(
                id=f"step_{i}",
                tool_id=tool.tool_id,
                tool_name=tool.tool_name,
                input_mapping=[
                    DataMapping(source_field="intent.parameters", target_field="parameters", required=False)
                ]
            )
            steps.append(step)
        
        return Workflow(
            id=workflow_id,
            name="Generic Workflow",
            description="Generic workflow for tool execution",
            steps=steps,
            execution_strategy=ExecutionStrategy.SEQUENTIAL
        )
    
    def _register_default_templates(self):
        """Register default workflow templates."""
        self._workflow_templates.update({
            'search_then_recommend': self._create_search_then_recommend_workflow,
            'simple_search': self._create_simple_search_workflow,
            'simple_recommendation': self._create_simple_recommendation_workflow,
            'generic': self._create_generic_workflow
        })
    
    def get_active_workflows(self) -> Dict[str, Dict[str, Any]]:
        """Get information about currently active workflows."""
        return {
            workflow_id: workflow.to_dict()
            for workflow_id, workflow in self._active_workflows.items()
        }
    
    def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific workflow."""
        workflow = self._active_workflows.get(workflow_id)
        return workflow.to_dict() if workflow else None