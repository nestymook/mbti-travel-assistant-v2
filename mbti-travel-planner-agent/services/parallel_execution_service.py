"""
Parallel Execution Service

This module provides parallel execution capabilities for independent agent calls
to improve performance by running multiple operations concurrently. It includes
dependency management, error handling, and result aggregation.

Features:
- Concurrent execution of independent operations
- Dependency-aware task scheduling
- Error isolation and handling
- Result aggregation and correlation
- Timeout management
- Performance monitoring
"""

import asyncio
import logging
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable, Awaitable, Union, TypeVar, Generic
from enum import Enum
import uuid

logger = logging.getLogger(__name__)

T = TypeVar('T')


class TaskStatus(Enum):
    """Task execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class ExecutionStrategy(Enum):
    """Execution strategies for parallel tasks."""
    ALL_OR_NOTHING = "all_or_nothing"  # All tasks must succeed
    BEST_EFFORT = "best_effort"  # Continue even if some tasks fail
    FAIL_FAST = "fail_fast"  # Stop on first failure
    MAJORITY_SUCCESS = "majority_success"  # Require majority to succeed


@dataclass
class TaskResult(Generic[T]):
    """Result of a parallel task execution."""
    task_id: str
    status: TaskStatus
    result: Optional[T] = None
    error: Optional[Exception] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    execution_time_ms: Optional[int] = None
    
    @property
    def is_successful(self) -> bool:
        """Check if task completed successfully."""
        return self.status == TaskStatus.COMPLETED and self.error is None
    
    @property
    def duration(self) -> Optional[timedelta]:
        """Get task duration."""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return None


@dataclass
class ParallelExecutionResult(Generic[T]):
    """Result of parallel execution."""
    execution_id: str
    strategy: ExecutionStrategy
    total_tasks: int
    successful_tasks: int
    failed_tasks: int
    cancelled_tasks: int
    timeout_tasks: int
    results: Dict[str, TaskResult[T]]
    start_time: datetime
    end_time: datetime
    total_execution_time_ms: int
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.total_tasks == 0:
            return 1.0
        return self.successful_tasks / self.total_tasks
    
    @property
    def is_successful(self) -> bool:
        """Check if execution was successful based on strategy."""
        if self.strategy == ExecutionStrategy.ALL_OR_NOTHING:
            return self.successful_tasks == self.total_tasks
        elif self.strategy == ExecutionStrategy.BEST_EFFORT:
            return self.successful_tasks > 0
        elif self.strategy == ExecutionStrategy.FAIL_FAST:
            return self.failed_tasks == 0
        elif self.strategy == ExecutionStrategy.MAJORITY_SUCCESS:
            return self.successful_tasks > (self.total_tasks / 2)
        return False
    
    def get_successful_results(self) -> Dict[str, T]:
        """Get only successful results."""
        return {
            task_id: result.result
            for task_id, result in self.results.items()
            if result.is_successful and result.result is not None
        }
    
    def get_failed_results(self) -> Dict[str, Exception]:
        """Get failed results with their errors."""
        return {
            task_id: result.error
            for task_id, result in self.results.items()
            if result.error is not None
        }


@dataclass
class TaskDefinition:
    """Definition of a parallel task."""
    task_id: str
    task_func: Callable[[], Awaitable[Any]]
    dependencies: List[str] = field(default_factory=list)
    timeout_seconds: Optional[int] = None
    retry_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate task definition."""
        if not self.task_id:
            raise ValueError("Task ID cannot be empty")
        
        if not callable(self.task_func):
            raise ValueError("Task function must be callable")
        
        if self.retry_count < 0:
            raise ValueError("Retry count cannot be negative")


@dataclass
class ExecutionConfig:
    """Configuration for parallel execution."""
    strategy: ExecutionStrategy = ExecutionStrategy.BEST_EFFORT
    max_concurrent_tasks: int = 10
    default_timeout_seconds: int = 60
    enable_retries: bool = True
    max_retries_per_task: int = 2
    retry_delay_seconds: float = 1.0
    enable_dependency_resolution: bool = True
    fail_on_circular_dependencies: bool = True
    enable_performance_monitoring: bool = True


class ParallelExecutionService:
    """
    Service for executing multiple tasks in parallel with dependency management.
    
    This service allows for efficient parallel execution of independent operations
    while handling dependencies, errors, and timeouts appropriately.
    """
    
    def __init__(self, config: Optional[ExecutionConfig] = None):
        """
        Initialize parallel execution service.
        
        Args:
            config: Execution configuration
        """
        self.config = config or ExecutionConfig()
        
        # Execution tracking
        self._active_executions: Dict[str, asyncio.Task] = {}
        self._execution_stats = {
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "total_tasks_executed": 0,
            "total_execution_time_ms": 0
        }
        
        logger.info("Parallel execution service initialized")
    
    async def execute_parallel(
        self,
        tasks: List[TaskDefinition],
        execution_id: Optional[str] = None,
        config_override: Optional[ExecutionConfig] = None
    ) -> ParallelExecutionResult:
        """
        Execute tasks in parallel with dependency management.
        
        Args:
            tasks: List of task definitions
            execution_id: Optional execution identifier
            config_override: Optional configuration override
            
        Returns:
            ParallelExecutionResult with execution details
        """
        if not tasks:
            raise ValueError("Tasks list cannot be empty")
        
        # Use provided execution ID or generate one
        exec_id = execution_id or str(uuid.uuid4())
        
        # Use config override if provided
        config = config_override or self.config
        
        start_time = datetime.utcnow()
        
        logger.info(f"Starting parallel execution {exec_id} with {len(tasks)} tasks")
        
        try:
            # Validate and prepare tasks
            task_map = {task.task_id: task for task in tasks}
            
            # Check for duplicate task IDs
            if len(task_map) != len(tasks):
                raise ValueError("Duplicate task IDs found")
            
            # Resolve dependencies if enabled
            if config.enable_dependency_resolution:
                execution_order = self._resolve_dependencies(tasks)
            else:
                execution_order = [tasks]  # Single batch with all tasks
            
            # Execute tasks in dependency order
            all_results = {}
            
            for batch in execution_order:
                batch_results = await self._execute_batch(
                    batch, exec_id, config, all_results
                )
                all_results.update(batch_results)
                
                # Check if we should continue based on strategy
                if not self._should_continue_execution(batch_results, config.strategy):
                    # Cancel remaining tasks
                    remaining_tasks = []
                    for remaining_batch in execution_order[execution_order.index(batch) + 1:]:
                        remaining_tasks.extend(remaining_batch)
                    
                    for task in remaining_tasks:
                        all_results[task.task_id] = TaskResult(
                            task_id=task.task_id,
                            status=TaskStatus.CANCELLED
                        )
                    break
            
            end_time = datetime.utcnow()
            total_time_ms = int((end_time - start_time).total_seconds() * 1000)
            
            # Calculate statistics
            successful_count = sum(1 for r in all_results.values() if r.is_successful)
            failed_count = sum(1 for r in all_results.values() if r.status == TaskStatus.FAILED)
            cancelled_count = sum(1 for r in all_results.values() if r.status == TaskStatus.CANCELLED)
            timeout_count = sum(1 for r in all_results.values() if r.status == TaskStatus.TIMEOUT)
            
            # Create result
            result = ParallelExecutionResult(
                execution_id=exec_id,
                strategy=config.strategy,
                total_tasks=len(tasks),
                successful_tasks=successful_count,
                failed_tasks=failed_count,
                cancelled_tasks=cancelled_count,
                timeout_tasks=timeout_count,
                results=all_results,
                start_time=start_time,
                end_time=end_time,
                total_execution_time_ms=total_time_ms
            )
            
            # Update statistics
            self._update_execution_stats(result)
            
            logger.info(
                f"Parallel execution {exec_id} completed: "
                f"{successful_count}/{len(tasks)} successful in {total_time_ms}ms"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Parallel execution {exec_id} failed: {e}")
            
            # Create failed result
            end_time = datetime.utcnow()
            total_time_ms = int((end_time - start_time).total_seconds() * 1000)
            
            failed_results = {
                task.task_id: TaskResult(
                    task_id=task.task_id,
                    status=TaskStatus.FAILED,
                    error=e
                )
                for task in tasks
            }
            
            result = ParallelExecutionResult(
                execution_id=exec_id,
                strategy=config.strategy,
                total_tasks=len(tasks),
                successful_tasks=0,
                failed_tasks=len(tasks),
                cancelled_tasks=0,
                timeout_tasks=0,
                results=failed_results,
                start_time=start_time,
                end_time=end_time,
                total_execution_time_ms=total_time_ms
            )
            
            self._update_execution_stats(result)
            raise
    
    def _resolve_dependencies(self, tasks: List[TaskDefinition]) -> List[List[TaskDefinition]]:
        """
        Resolve task dependencies and return execution order.
        
        Args:
            tasks: List of task definitions
            
        Returns:
            List of task batches in execution order
        """
        task_map = {task.task_id: task for task in tasks}
        
        # Check for circular dependencies
        if self.config.fail_on_circular_dependencies:
            self._check_circular_dependencies(tasks)
        
        # Build dependency graph
        in_degree = defaultdict(int)
        dependencies = defaultdict(list)
        
        for task in tasks:
            in_degree[task.task_id] = len(task.dependencies)
            for dep in task.dependencies:
                if dep not in task_map:
                    raise ValueError(f"Task {task.task_id} depends on unknown task {dep}")
                dependencies[dep].append(task.task_id)
        
        # Topological sort to determine execution order
        execution_batches = []
        remaining_tasks = set(task.task_id for task in tasks)
        
        while remaining_tasks:
            # Find tasks with no dependencies
            ready_tasks = [
                task_id for task_id in remaining_tasks
                if in_degree[task_id] == 0
            ]
            
            if not ready_tasks:
                raise ValueError("Circular dependency detected or unresolvable dependencies")
            
            # Create batch of ready tasks
            batch = [task_map[task_id] for task_id in ready_tasks]
            execution_batches.append(batch)
            
            # Remove ready tasks and update dependencies
            for task_id in ready_tasks:
                remaining_tasks.remove(task_id)
                for dependent in dependencies[task_id]:
                    in_degree[dependent] -= 1
        
        logger.debug(f"Resolved dependencies into {len(execution_batches)} execution batches")
        return execution_batches
    
    def _check_circular_dependencies(self, tasks: List[TaskDefinition]):
        """Check for circular dependencies using DFS."""
        task_map = {task.task_id: task for task in tasks}
        visited = set()
        rec_stack = set()
        
        def has_cycle(task_id: str) -> bool:
            if task_id in rec_stack:
                return True
            if task_id in visited:
                return False
            
            visited.add(task_id)
            rec_stack.add(task_id)
            
            if task_id in task_map:
                for dep in task_map[task_id].dependencies:
                    if has_cycle(dep):
                        return True
            
            rec_stack.remove(task_id)
            return False
        
        for task in tasks:
            if task.task_id not in visited:
                if has_cycle(task.task_id):
                    raise ValueError(f"Circular dependency detected involving task {task.task_id}")
    
    async def _execute_batch(
        self,
        batch: List[TaskDefinition],
        execution_id: str,
        config: ExecutionConfig,
        previous_results: Dict[str, TaskResult]
    ) -> Dict[str, TaskResult]:
        """
        Execute a batch of tasks concurrently.
        
        Args:
            batch: List of tasks to execute
            execution_id: Execution identifier
            config: Execution configuration
            previous_results: Results from previous batches
            
        Returns:
            Dictionary of task results
        """
        if not batch:
            return {}
        
        logger.debug(f"Executing batch of {len(batch)} tasks for execution {execution_id}")
        
        # Create semaphore to limit concurrent tasks
        semaphore = asyncio.Semaphore(config.max_concurrent_tasks)
        
        # Create tasks
        async_tasks = []
        for task_def in batch:
            async_task = asyncio.create_task(
                self._execute_single_task(task_def, config, semaphore, previous_results)
            )
            async_tasks.append(async_task)
        
        # Wait for all tasks to complete
        results = await asyncio.gather(*async_tasks, return_exceptions=True)
        
        # Process results
        batch_results = {}
        for i, result in enumerate(results):
            task_def = batch[i]
            
            if isinstance(result, Exception):
                batch_results[task_def.task_id] = TaskResult(
                    task_id=task_def.task_id,
                    status=TaskStatus.FAILED,
                    error=result
                )
            else:
                batch_results[task_def.task_id] = result
        
        return batch_results
    
    async def _execute_single_task(
        self,
        task_def: TaskDefinition,
        config: ExecutionConfig,
        semaphore: asyncio.Semaphore,
        previous_results: Dict[str, TaskResult]
    ) -> TaskResult:
        """
        Execute a single task with retry logic and timeout.
        
        Args:
            task_def: Task definition
            config: Execution configuration
            semaphore: Concurrency semaphore
            previous_results: Results from previous batches
            
        Returns:
            TaskResult
        """
        async with semaphore:
            start_time = datetime.utcnow()
            
            # Check if dependencies are satisfied
            for dep_id in task_def.dependencies:
                if dep_id not in previous_results or not previous_results[dep_id].is_successful:
                    return TaskResult(
                        task_id=task_def.task_id,
                        status=TaskStatus.FAILED,
                        error=ValueError(f"Dependency {dep_id} not satisfied"),
                        start_time=start_time,
                        end_time=datetime.utcnow()
                    )
            
            # Determine timeout
            timeout = task_def.timeout_seconds or config.default_timeout_seconds
            
            # Execute with retries
            max_attempts = (task_def.retry_count if config.enable_retries else 0) + 1
            last_error = None
            
            for attempt in range(max_attempts):
                try:
                    # Execute task with timeout
                    result = await asyncio.wait_for(
                        task_def.task_func(),
                        timeout=timeout
                    )
                    
                    end_time = datetime.utcnow()
                    execution_time_ms = int((end_time - start_time).total_seconds() * 1000)
                    
                    return TaskResult(
                        task_id=task_def.task_id,
                        status=TaskStatus.COMPLETED,
                        result=result,
                        start_time=start_time,
                        end_time=end_time,
                        execution_time_ms=execution_time_ms
                    )
                    
                except asyncio.TimeoutError as e:
                    last_error = e
                    if attempt == max_attempts - 1:  # Last attempt
                        end_time = datetime.utcnow()
                        return TaskResult(
                            task_id=task_def.task_id,
                            status=TaskStatus.TIMEOUT,
                            error=e,
                            start_time=start_time,
                            end_time=end_time
                        )
                    
                except Exception as e:
                    last_error = e
                    if attempt == max_attempts - 1:  # Last attempt
                        end_time = datetime.utcnow()
                        return TaskResult(
                            task_id=task_def.task_id,
                            status=TaskStatus.FAILED,
                            error=e,
                            start_time=start_time,
                            end_time=end_time
                        )
                
                # Wait before retry
                if attempt < max_attempts - 1:
                    await asyncio.sleep(config.retry_delay_seconds)
            
            # Should not reach here, but handle just in case
            end_time = datetime.utcnow()
            return TaskResult(
                task_id=task_def.task_id,
                status=TaskStatus.FAILED,
                error=last_error or Exception("Unknown error"),
                start_time=start_time,
                end_time=end_time
            )
    
    def _should_continue_execution(
        self, 
        batch_results: Dict[str, TaskResult], 
        strategy: ExecutionStrategy
    ) -> bool:
        """
        Determine if execution should continue based on strategy and results.
        
        Args:
            batch_results: Results from current batch
            strategy: Execution strategy
            
        Returns:
            True if execution should continue
        """
        if strategy == ExecutionStrategy.FAIL_FAST:
            return all(result.is_successful for result in batch_results.values())
        
        # For other strategies, continue execution
        return True
    
    def _update_execution_stats(self, result: ParallelExecutionResult):
        """Update execution statistics."""
        self._execution_stats["total_executions"] += 1
        self._execution_stats["total_tasks_executed"] += result.total_tasks
        self._execution_stats["total_execution_time_ms"] += result.total_execution_time_ms
        
        if result.is_successful:
            self._execution_stats["successful_executions"] += 1
        else:
            self._execution_stats["failed_executions"] += 1
    
    def get_execution_statistics(self) -> Dict[str, Any]:
        """Get execution statistics."""
        stats = self._execution_stats.copy()
        
        if stats["total_executions"] > 0:
            stats["average_execution_time_ms"] = (
                stats["total_execution_time_ms"] / stats["total_executions"]
            )
            stats["success_rate"] = (
                stats["successful_executions"] / stats["total_executions"]
            )
        else:
            stats["average_execution_time_ms"] = 0
            stats["success_rate"] = 1.0
        
        if stats["total_tasks_executed"] > 0:
            stats["average_tasks_per_execution"] = (
                stats["total_tasks_executed"] / stats["total_executions"]
            )
        else:
            stats["average_tasks_per_execution"] = 0
        
        return stats
    
    async def execute_restaurant_workflow(
        self,
        search_func: Callable[[], Awaitable[Any]],
        reasoning_func: Callable[[Any], Awaitable[Any]],
        enable_parallel_search: bool = True
    ) -> Dict[str, Any]:
        """
        Execute restaurant search and reasoning workflow with optimized parallelization.
        
        Args:
            search_func: Function to search restaurants
            reasoning_func: Function to get recommendations
            enable_parallel_search: Whether to enable parallel search optimization
            
        Returns:
            Combined workflow results
        """
        if enable_parallel_search:
            # Execute search first, then reasoning (sequential dependency)
            tasks = [
                TaskDefinition(
                    task_id="restaurant_search",
                    task_func=search_func,
                    timeout_seconds=30
                ),
                TaskDefinition(
                    task_id="restaurant_reasoning",
                    task_func=lambda: reasoning_func(None),  # Will be updated with search results
                    dependencies=["restaurant_search"],
                    timeout_seconds=45
                )
            ]
            
            # Execute with dependency resolution
            result = await self.execute_parallel(
                tasks,
                config_override=ExecutionConfig(
                    strategy=ExecutionStrategy.ALL_OR_NOTHING,
                    max_concurrent_tasks=2
                )
            )
            
            if result.is_successful:
                successful_results = result.get_successful_results()
                return {
                    "search_result": successful_results.get("restaurant_search"),
                    "reasoning_result": successful_results.get("restaurant_reasoning"),
                    "execution_time_ms": result.total_execution_time_ms,
                    "parallel_execution": True
                }
            else:
                failed_results = result.get_failed_results()
                raise Exception(f"Workflow failed: {failed_results}")
        
        else:
            # Sequential execution
            start_time = time.time()
            
            search_result = await search_func()
            reasoning_result = await reasoning_func(search_result)
            
            execution_time_ms = int((time.time() - start_time) * 1000)
            
            return {
                "search_result": search_result,
                "reasoning_result": reasoning_result,
                "execution_time_ms": execution_time_ms,
                "parallel_execution": False
            }


# Global parallel execution service
_global_execution_service: Optional[ParallelExecutionService] = None


def get_parallel_execution_service(config: Optional[ExecutionConfig] = None) -> ParallelExecutionService:
    """
    Get global parallel execution service instance.
    
    Args:
        config: Optional execution configuration
        
    Returns:
        ParallelExecutionService instance
    """
    global _global_execution_service
    
    if _global_execution_service is None:
        _global_execution_service = ParallelExecutionService(config)
    
    return _global_execution_service


# Export main classes and functions
__all__ = [
    'ParallelExecutionService',
    'TaskDefinition',
    'TaskResult',
    'ParallelExecutionResult',
    'ExecutionConfig',
    'ExecutionStrategy',
    'TaskStatus',
    'get_parallel_execution_service'
]