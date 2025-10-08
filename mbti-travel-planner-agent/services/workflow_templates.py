"""
Workflow Templates

This module provides pre-defined workflow templates for common patterns in the MBTI Travel Planner,
including search-then-recommend workflows, multi-criteria search with result merging,
and iterative refinement workflows for complex requests.

Features:
- Search-then-recommend workflow template
- Multi-criteria search with result merging template
- Iterative refinement workflow for complex requests
- Template customization and parameterization
- Dynamic workflow generation based on intent patterns
"""

import uuid
import time
from typing import Dict, Any, Optional, List, Union, Callable
from dataclasses import dataclass, field
from enum import Enum

from .workflow_engine import (
    Workflow, WorkflowStep, DataMapping, ExecutionStrategy,
    WorkflowStatus, StepStatus
)
from .orchestration_types import (
    RequestType, UserContext, Intent, SelectedTool
)


class TemplateType(Enum):
    """Types of workflow templates."""
    SEARCH_THEN_RECOMMEND = "search_then_recommend"
    MULTI_CRITERIA_SEARCH = "multi_criteria_search"
    ITERATIVE_REFINEMENT = "iterative_refinement"
    PARALLEL_SEARCH_MERGE = "parallel_search_merge"
    CONDITIONAL_RECOMMENDATION = "conditional_recommendation"
    SENTIMENT_ANALYSIS_WORKFLOW = "sentiment_analysis_workflow"
    COMPREHENSIVE_PLANNING = "comprehensive_planning"


@dataclass
class TemplateConfig:
    """Configuration for workflow templates."""
    template_type: TemplateType
    parameters: Dict[str, Any] = field(default_factory=dict)
    customizations: Dict[str, Any] = field(default_factory=dict)
    
    # Common template parameters
    enable_parallel_execution: bool = False
    max_search_results: int = 50
    min_recommendation_score: float = 0.5
    enable_mbti_personalization: bool = True
    enable_fallback_strategies: bool = True
    step_timeout_seconds: int = 30
    
    def get_parameter(self, key: str, default: Any = None) -> Any:
        """Get template parameter with fallback to default."""
        return self.parameters.get(key, default)


class WorkflowTemplateManager:
    """
    Manager for workflow templates and dynamic workflow generation.
    
    This manager provides:
    - Pre-defined workflow templates for common patterns
    - Template customization and parameterization
    - Dynamic workflow generation based on intent analysis
    - Template validation and optimization
    """
    
    def __init__(self):
        """Initialize the workflow template manager."""
        self._templates: Dict[TemplateType, Callable] = {}
        self._register_templates()
    
    def create_workflow_from_template(self,
                                    template_type: TemplateType,
                                    intent: Intent,
                                    selected_tools: List[SelectedTool],
                                    config: Optional[TemplateConfig] = None,
                                    user_context: Optional[UserContext] = None) -> Workflow:
        """
        Create a workflow from a template.
        
        Args:
            template_type: Type of template to use
            intent: User intent
            selected_tools: Selected tools for execution
            config: Template configuration
            user_context: User context for personalization
            
        Returns:
            Configured workflow
        """
        if template_type not in self._templates:
            raise ValueError(f"Unknown template type: {template_type}")
        
        # Use default config if none provided
        if config is None:
            config = TemplateConfig(template_type=template_type)
        
        # Generate workflow using template
        template_func = self._templates[template_type]
        workflow = template_func(intent, selected_tools, config, user_context)
        
        return workflow
    
    def get_recommended_template(self,
                               intent: Intent,
                               selected_tools: List[SelectedTool],
                               user_context: Optional[UserContext] = None) -> TemplateType:
        """
        Get recommended template type based on intent and available tools.
        
        Args:
            intent: User intent
            selected_tools: Available tools
            user_context: User context
            
        Returns:
            Recommended template type
        """
        # Analyze intent type and tool capabilities
        tool_names = [tool.tool_name.lower() for tool in selected_tools]
        has_search_tools = any('search' in name for name in tool_names)
        has_recommend_tools = any('recommend' in name for name in tool_names)
        has_sentiment_tools = any('sentiment' in name or 'analyze' in name for name in tool_names)
        
        # Determine template based on intent and available tools
        if intent.type == RequestType.COMBINED_SEARCH_AND_RECOMMENDATION:
            if has_search_tools and has_recommend_tools:
                return TemplateType.SEARCH_THEN_RECOMMEND
            else:
                return TemplateType.MULTI_CRITERIA_SEARCH
        
        elif intent.type in [RequestType.RESTAURANT_SEARCH_BY_LOCATION, RequestType.RESTAURANT_SEARCH_BY_MEAL]:
            if len(selected_tools) > 1:
                return TemplateType.PARALLEL_SEARCH_MERGE
            else:
                return TemplateType.MULTI_CRITERIA_SEARCH
        
        elif intent.type == RequestType.RESTAURANT_RECOMMENDATION:
            if user_context and user_context.mbti_type:
                return TemplateType.CONDITIONAL_RECOMMENDATION
            else:
                return TemplateType.SEARCH_THEN_RECOMMEND
        
        elif intent.type == RequestType.SENTIMENT_ANALYSIS:
            return TemplateType.SENTIMENT_ANALYSIS_WORKFLOW
        
        else:
            # For complex or unknown intents, use comprehensive planning
            return TemplateType.COMPREHENSIVE_PLANNING
    
    def _register_templates(self):
        """Register all available workflow templates."""
        self._templates = {
            TemplateType.SEARCH_THEN_RECOMMEND: self._create_search_then_recommend_template,
            TemplateType.MULTI_CRITERIA_SEARCH: self._create_multi_criteria_search_template,
            TemplateType.ITERATIVE_REFINEMENT: self._create_iterative_refinement_template,
            TemplateType.PARALLEL_SEARCH_MERGE: self._create_parallel_search_merge_template,
            TemplateType.CONDITIONAL_RECOMMENDATION: self._create_conditional_recommendation_template,
            TemplateType.SENTIMENT_ANALYSIS_WORKFLOW: self._create_sentiment_analysis_template,
            TemplateType.COMPREHENSIVE_PLANNING: self._create_comprehensive_planning_template
        }
    
    def _create_search_then_recommend_template(self,
                                             intent: Intent,
                                             selected_tools: List[SelectedTool],
                                             config: TemplateConfig,
                                             user_context: Optional[UserContext]) -> Workflow:
        """Create search-then-recommend workflow template."""
        workflow_id = f"search_recommend_{int(time.time() * 1000)}_{uuid.uuid4().hex[:8]}"
        
        # Separate search and recommendation tools
        search_tools = [t for t in selected_tools if 'search' in t.tool_name.lower()]
        recommend_tools = [t for t in selected_tools if 'recommend' in t.tool_name.lower()]
        
        steps = []
        
        # Step 1: Search for restaurants
        if search_tools:
            search_tool = search_tools[0]  # Use primary search tool
            
            search_step = WorkflowStep(
                id="restaurant_search",
                tool_id=search_tool.tool_id,
                tool_name=search_tool.tool_name,
                input_mapping=[
                    DataMapping(
                        source_field="intent.parameters.districts",
                        target_field="districts",
                        required=False,
                        default_value=[]
                    ),
                    DataMapping(
                        source_field="intent.parameters.meal_types",
                        target_field="meal_types",
                        required=False,
                        default_value=[]
                    ),
                    DataMapping(
                        source_field="context.mbti_type",
                        target_field="mbti_type",
                        required=False
                    )
                ],
                output_mapping=[
                    DataMapping(source_field="restaurants", target_field="found_restaurants"),
                    DataMapping(source_field="total_count", target_field="restaurant_count"),
                    DataMapping(source_field="search_metadata", target_field="search_info")
                ],
                timeout_seconds=config.step_timeout_seconds
            )
            steps.append(search_step)
        
        # Step 2: Get recommendations based on search results
        if recommend_tools and search_tools:
            recommend_tool = recommend_tools[0]  # Use primary recommendation tool
            
            recommend_step = WorkflowStep(
                id="restaurant_recommendation",
                tool_id=recommend_tool.tool_id,
                tool_name=recommend_tool.tool_name,
                depends_on=["restaurant_search"],
                condition="restaurant_search.restaurant_count > 0",
                input_mapping=[
                    DataMapping(
                        source_field="restaurant_search.found_restaurants",
                        target_field="restaurants",
                        transformation="to_list"
                    ),
                    DataMapping(
                        source_field="context.mbti_type",
                        target_field="mbti_type",
                        required=False
                    ),
                    DataMapping(
                        source_field="intent.parameters.preferences",
                        target_field="user_preferences",
                        required=False,
                        default_value={}
                    )
                ],
                output_mapping=[
                    DataMapping(source_field="recommendations", target_field="final_recommendations"),
                    DataMapping(source_field="recommendation_metadata", target_field="recommendation_info")
                ],
                timeout_seconds=config.step_timeout_seconds
            )
            steps.append(recommend_step)
        
        # Step 3: Optional sentiment analysis if tools available
        sentiment_tools = [t for t in selected_tools if 'sentiment' in t.tool_name.lower() or 'analyze' in t.tool_name.lower()]
        if sentiment_tools and config.get_parameter('enable_sentiment_analysis', False):
            sentiment_tool = sentiment_tools[0]
            
            sentiment_step = WorkflowStep(
                id="sentiment_analysis",
                tool_id=sentiment_tool.tool_id,
                tool_name=sentiment_tool.tool_name,
                depends_on=["restaurant_search"],
                condition="restaurant_search.restaurant_count > 0",
                input_mapping=[
                    DataMapping(
                        source_field="restaurant_search.found_restaurants",
                        target_field="restaurants",
                        transformation="to_list"
                    )
                ],
                output_mapping=[
                    DataMapping(source_field="sentiment_analysis", target_field="restaurant_sentiments")
                ],
                timeout_seconds=config.step_timeout_seconds
            )
            steps.append(sentiment_step)
        
        return Workflow(
            id=workflow_id,
            name="Search Then Recommend",
            description="Search for restaurants then provide personalized recommendations",
            steps=steps,
            execution_strategy=ExecutionStrategy.SEQUENTIAL,
            context_data={
                'template_type': TemplateType.SEARCH_THEN_RECOMMEND.value,
                'intent_type': intent.type.value,
                'user_mbti_type': user_context.mbti_type if user_context else None,
                'enable_mbti_personalization': config.enable_mbti_personalization
            }
        )
    
    def _create_multi_criteria_search_template(self,
                                             intent: Intent,
                                             selected_tools: List[SelectedTool],
                                             config: TemplateConfig,
                                             user_context: Optional[UserContext]) -> Workflow:
        """Create multi-criteria search with result merging template."""
        workflow_id = f"multi_search_{int(time.time() * 1000)}_{uuid.uuid4().hex[:8]}"
        
        steps = []
        search_tools = [t for t in selected_tools if 'search' in t.tool_name.lower()]
        
        # Create search steps for different criteria
        for i, tool in enumerate(search_tools):
            step_id = f"search_step_{i}"
            
            search_step = WorkflowStep(
                id=step_id,
                tool_id=tool.tool_id,
                tool_name=tool.tool_name,
                input_mapping=[
                    DataMapping(
                        source_field="intent.parameters.districts",
                        target_field="districts",
                        required=False
                    ),
                    DataMapping(
                        source_field="intent.parameters.meal_types",
                        target_field="meal_types",
                        required=False
                    ),
                    DataMapping(
                        source_field="intent.parameters.cuisine_types",
                        target_field="cuisine_types",
                        required=False
                    )
                ],
                output_mapping=[
                    DataMapping(source_field="restaurants", target_field=f"restaurants_{i}"),
                    DataMapping(source_field="search_metadata", target_field=f"metadata_{i}")
                ],
                timeout_seconds=config.step_timeout_seconds
            )
            steps.append(search_step)
        
        # Add result merging step if multiple search tools
        if len(search_tools) > 1:
            merge_dependencies = [f"search_step_{i}" for i in range(len(search_tools))]
            
            merge_step = WorkflowStep(
                id="merge_results",
                tool_id="result_merger",  # This would be a built-in merging tool
                tool_name="Result Merger",
                depends_on=merge_dependencies,
                input_mapping=[
                    DataMapping(
                        source_field=f"search_step_{i}.restaurants_{i}",
                        target_field=f"input_restaurants_{i}",
                        required=False
                    ) for i in range(len(search_tools))
                ],
                output_mapping=[
                    DataMapping(source_field="merged_restaurants", target_field="final_restaurants"),
                    DataMapping(source_field="merge_statistics", target_field="merge_info")
                ],
                timeout_seconds=config.step_timeout_seconds
            )
            steps.append(merge_step)
        
        execution_strategy = ExecutionStrategy.PARALLEL if config.enable_parallel_execution else ExecutionStrategy.SEQUENTIAL
        
        return Workflow(
            id=workflow_id,
            name="Multi-Criteria Search",
            description="Search using multiple criteria and merge results",
            steps=steps,
            execution_strategy=execution_strategy,
            context_data={
                'template_type': TemplateType.MULTI_CRITERIA_SEARCH.value,
                'search_tools_count': len(search_tools),
                'parallel_execution': config.enable_parallel_execution
            }
        )
    
    def _create_iterative_refinement_template(self,
                                            intent: Intent,
                                            selected_tools: List[SelectedTool],
                                            config: TemplateConfig,
                                            user_context: Optional[UserContext]) -> Workflow:
        """Create iterative refinement workflow for complex requests."""
        workflow_id = f"iterative_{int(time.time() * 1000)}_{uuid.uuid4().hex[:8]}"
        
        steps = []
        max_iterations = config.get_parameter('max_iterations', 3)
        
        # Initial search step
        search_tools = [t for t in selected_tools if 'search' in t.tool_name.lower()]
        if search_tools:
            initial_search = WorkflowStep(
                id="initial_search",
                tool_id=search_tools[0].tool_id,
                tool_name=search_tools[0].tool_name,
                input_mapping=[
                    DataMapping(source_field="intent.parameters", target_field="search_params")
                ],
                output_mapping=[
                    DataMapping(source_field="restaurants", target_field="initial_results"),
                    DataMapping(source_field="total_count", target_field="result_count")
                ],
                timeout_seconds=config.step_timeout_seconds
            )
            steps.append(initial_search)
        
        # Iterative refinement steps
        for iteration in range(max_iterations):
            iteration_id = f"refinement_{iteration}"
            
            # Analysis step to determine if refinement is needed
            analysis_step = WorkflowStep(
                id=f"analysis_{iteration}",
                tool_id="result_analyzer",  # Built-in analysis tool
                tool_name="Result Analyzer",
                depends_on=["initial_search"] if iteration == 0 else [f"refinement_{iteration-1}"],
                condition=f"{'initial_search' if iteration == 0 else f'refinement_{iteration-1}'}.result_count < {config.max_search_results}",
                input_mapping=[
                    DataMapping(
                        source_field=f"{'initial_search' if iteration == 0 else f'refinement_{iteration-1}'}.initial_results",
                        target_field="current_results"
                    ),
                    DataMapping(source_field="intent.parameters", target_field="original_intent")
                ],
                output_mapping=[
                    DataMapping(source_field="refinement_needed", target_field="needs_refinement"),
                    DataMapping(source_field="suggested_parameters", target_field="new_params")
                ],
                timeout_seconds=config.step_timeout_seconds
            )
            steps.append(analysis_step)
            
            # Refinement search step
            if search_tools:
                refinement_step = WorkflowStep(
                    id=iteration_id,
                    tool_id=search_tools[0].tool_id,
                    tool_name=search_tools[0].tool_name,
                    depends_on=[f"analysis_{iteration}"],
                    condition=f"analysis_{iteration}.needs_refinement == true",
                    input_mapping=[
                        DataMapping(
                            source_field=f"analysis_{iteration}.new_params",
                            target_field="search_params"
                        )
                    ],
                    output_mapping=[
                        DataMapping(source_field="restaurants", target_field="refined_results"),
                        DataMapping(source_field="total_count", target_field="result_count")
                    ],
                    timeout_seconds=config.step_timeout_seconds
                )
                steps.append(refinement_step)
        
        return Workflow(
            id=workflow_id,
            name="Iterative Refinement",
            description="Iteratively refine search results for complex requests",
            steps=steps,
            execution_strategy=ExecutionStrategy.CONDITIONAL,
            context_data={
                'template_type': TemplateType.ITERATIVE_REFINEMENT.value,
                'max_iterations': max_iterations,
                'refinement_strategy': 'progressive_narrowing'
            }
        )
    
    def _create_parallel_search_merge_template(self,
                                             intent: Intent,
                                             selected_tools: List[SelectedTool],
                                             config: TemplateConfig,
                                             user_context: Optional[UserContext]) -> Workflow:
        """Create parallel search with intelligent result merging."""
        workflow_id = f"parallel_merge_{int(time.time() * 1000)}_{uuid.uuid4().hex[:8]}"
        
        steps = []
        search_tools = [t for t in selected_tools if 'search' in t.tool_name.lower()]
        
        # Create parallel search steps
        search_step_ids = []
        for i, tool in enumerate(search_tools):
            step_id = f"parallel_search_{i}"
            search_step_ids.append(step_id)
            
            search_step = WorkflowStep(
                id=step_id,
                tool_id=tool.tool_id,
                tool_name=tool.tool_name,
                input_mapping=[
                    DataMapping(source_field="intent.parameters", target_field="search_params")
                ],
                output_mapping=[
                    DataMapping(source_field="restaurants", target_field=f"results_{i}"),
                    DataMapping(source_field="search_metadata", target_field=f"metadata_{i}")
                ],
                timeout_seconds=config.step_timeout_seconds
            )
            steps.append(search_step)
        
        # Intelligent merging step
        if len(search_tools) > 1:
            merge_step = WorkflowStep(
                id="intelligent_merge",
                tool_id="intelligent_merger",
                tool_name="Intelligent Result Merger",
                depends_on=search_step_ids,
                input_mapping=[
                    DataMapping(
                        source_field=f"parallel_search_{i}.results_{i}",
                        target_field=f"source_{i}_results"
                    ) for i in range(len(search_tools))
                ] + [
                    DataMapping(source_field="context.mbti_type", target_field="user_mbti_type", required=False),
                    DataMapping(source_field="intent.parameters.preferences", target_field="user_preferences", required=False)
                ],
                output_mapping=[
                    DataMapping(source_field="merged_restaurants", target_field="final_results"),
                    DataMapping(source_field="merge_strategy", target_field="merge_info"),
                    DataMapping(source_field="confidence_scores", target_field="result_confidence")
                ],
                timeout_seconds=config.step_timeout_seconds
            )
            steps.append(merge_step)
        
        return Workflow(
            id=workflow_id,
            name="Parallel Search and Merge",
            description="Execute parallel searches and intelligently merge results",
            steps=steps,
            execution_strategy=ExecutionStrategy.PARALLEL,
            context_data={
                'template_type': TemplateType.PARALLEL_SEARCH_MERGE.value,
                'parallel_tools': len(search_tools),
                'merge_strategy': 'intelligent_deduplication'
            }
        )
    
    def _create_conditional_recommendation_template(self,
                                                  intent: Intent,
                                                  selected_tools: List[SelectedTool],
                                                  config: TemplateConfig,
                                                  user_context: Optional[UserContext]) -> Workflow:
        """Create conditional recommendation workflow based on user context."""
        workflow_id = f"conditional_rec_{int(time.time() * 1000)}_{uuid.uuid4().hex[:8]}"
        
        steps = []
        recommend_tools = [t for t in selected_tools if 'recommend' in t.tool_name.lower()]
        
        if recommend_tools:
            # Context analysis step
            context_step = WorkflowStep(
                id="context_analysis",
                tool_id="context_analyzer",
                tool_name="Context Analyzer",
                input_mapping=[
                    DataMapping(source_field="context.mbti_type", target_field="mbti_type"),
                    DataMapping(source_field="context.preferences", target_field="user_preferences", required=False),
                    DataMapping(source_field="context.conversation_history", target_field="history", required=False)
                ],
                output_mapping=[
                    DataMapping(source_field="recommendation_strategy", target_field="strategy"),
                    DataMapping(source_field="personalization_level", target_field="personalization")
                ],
                timeout_seconds=config.step_timeout_seconds
            )
            steps.append(context_step)
            
            # Conditional recommendation steps based on MBTI type
            mbti_strategies = {
                'E': 'social_focused',  # Extroverted
                'I': 'intimate_focused',  # Introverted
                'S': 'practical_focused',  # Sensing
                'N': 'experience_focused',  # Intuitive
                'T': 'logical_focused',  # Thinking
                'F': 'feeling_focused',  # Feeling
                'J': 'structured_focused',  # Judging
                'P': 'flexible_focused'  # Perceiving
            }
            
            for mbti_trait, strategy in mbti_strategies.items():
                rec_step = WorkflowStep(
                    id=f"recommendation_{mbti_trait.lower()}",
                    tool_id=recommend_tools[0].tool_id,
                    tool_name=recommend_tools[0].tool_name,
                    depends_on=["context_analysis"],
                    condition=f"context.mbti_type contains '{mbti_trait}'",
                    input_mapping=[
                        DataMapping(source_field="intent.parameters.restaurants", target_field="restaurants"),
                        DataMapping(source_field="context.mbti_type", target_field="mbti_type"),
                        DataMapping(source_field=f"'{strategy}'", target_field="recommendation_strategy")
                    ],
                    output_mapping=[
                        DataMapping(source_field="recommendations", target_field=f"{strategy}_recommendations")
                    ],
                    timeout_seconds=config.step_timeout_seconds
                )
                steps.append(rec_step)
        
        return Workflow(
            id=workflow_id,
            name="Conditional Recommendation",
            description="Provide recommendations based on user context and MBTI type",
            steps=steps,
            execution_strategy=ExecutionStrategy.CONDITIONAL,
            context_data={
                'template_type': TemplateType.CONDITIONAL_RECOMMENDATION.value,
                'mbti_personalization': True,
                'context_aware': True
            }
        )
    
    def _create_sentiment_analysis_template(self,
                                          intent: Intent,
                                          selected_tools: List[SelectedTool],
                                          config: TemplateConfig,
                                          user_context: Optional[UserContext]) -> Workflow:
        """Create sentiment analysis workflow."""
        workflow_id = f"sentiment_{int(time.time() * 1000)}_{uuid.uuid4().hex[:8]}"
        
        steps = []
        sentiment_tools = [t for t in selected_tools if 'sentiment' in t.tool_name.lower() or 'analyze' in t.tool_name.lower()]
        
        if sentiment_tools:
            # Data preparation step
            prep_step = WorkflowStep(
                id="data_preparation",
                tool_id="data_preprocessor",
                tool_name="Data Preprocessor",
                input_mapping=[
                    DataMapping(source_field="intent.parameters.restaurants", target_field="raw_data")
                ],
                output_mapping=[
                    DataMapping(source_field="processed_restaurants", target_field="clean_data"),
                    DataMapping(source_field="data_quality", target_field="quality_metrics")
                ],
                timeout_seconds=config.step_timeout_seconds
            )
            steps.append(prep_step)
            
            # Sentiment analysis step
            sentiment_step = WorkflowStep(
                id="sentiment_analysis",
                tool_id=sentiment_tools[0].tool_id,
                tool_name=sentiment_tools[0].tool_name,
                depends_on=["data_preparation"],
                input_mapping=[
                    DataMapping(source_field="data_preparation.clean_data", target_field="restaurants")
                ],
                output_mapping=[
                    DataMapping(source_field="sentiment_scores", target_field="analysis_results"),
                    DataMapping(source_field="sentiment_summary", target_field="summary")
                ],
                timeout_seconds=config.step_timeout_seconds
            )
            steps.append(sentiment_step)
            
            # Results interpretation step
            interpretation_step = WorkflowStep(
                id="result_interpretation",
                tool_id="result_interpreter",
                tool_name="Result Interpreter",
                depends_on=["sentiment_analysis"],
                input_mapping=[
                    DataMapping(source_field="sentiment_analysis.analysis_results", target_field="raw_results"),
                    DataMapping(source_field="context.mbti_type", target_field="user_type", required=False)
                ],
                output_mapping=[
                    DataMapping(source_field="interpreted_results", target_field="final_analysis"),
                    DataMapping(source_field="recommendations", target_field="action_items")
                ],
                timeout_seconds=config.step_timeout_seconds
            )
            steps.append(interpretation_step)
        
        return Workflow(
            id=workflow_id,
            name="Sentiment Analysis Workflow",
            description="Comprehensive sentiment analysis with interpretation",
            steps=steps,
            execution_strategy=ExecutionStrategy.SEQUENTIAL,
            context_data={
                'template_type': TemplateType.SENTIMENT_ANALYSIS_WORKFLOW.value,
                'analysis_depth': 'comprehensive',
                'include_interpretation': True
            }
        )
    
    def _create_comprehensive_planning_template(self,
                                              intent: Intent,
                                              selected_tools: List[SelectedTool],
                                              config: TemplateConfig,
                                              user_context: Optional[UserContext]) -> Workflow:
        """Create comprehensive planning workflow for complex requests."""
        workflow_id = f"comprehensive_{int(time.time() * 1000)}_{uuid.uuid4().hex[:8]}"
        
        steps = []
        
        # Phase 1: Discovery and Analysis
        discovery_step = WorkflowStep(
            id="discovery_phase",
            tool_id="discovery_analyzer",
            tool_name="Discovery Analyzer",
            input_mapping=[
                DataMapping(source_field="intent.parameters", target_field="user_request"),
                DataMapping(source_field="context", target_field="user_context")
            ],
            output_mapping=[
                DataMapping(source_field="analysis_results", target_field="discovery_insights"),
                DataMapping(source_field="recommended_approach", target_field="planning_strategy")
            ],
            timeout_seconds=config.step_timeout_seconds
        )
        steps.append(discovery_step)
        
        # Phase 2: Multi-tool execution based on discovery
        search_tools = [t for t in selected_tools if 'search' in t.tool_name.lower()]
        recommend_tools = [t for t in selected_tools if 'recommend' in t.tool_name.lower()]
        
        if search_tools:
            search_step = WorkflowStep(
                id="comprehensive_search",
                tool_id=search_tools[0].tool_id,
                tool_name=search_tools[0].tool_name,
                depends_on=["discovery_phase"],
                input_mapping=[
                    DataMapping(source_field="discovery_phase.planning_strategy", target_field="search_strategy"),
                    DataMapping(source_field="intent.parameters", target_field="base_params")
                ],
                output_mapping=[
                    DataMapping(source_field="restaurants", target_field="comprehensive_results")
                ],
                timeout_seconds=config.step_timeout_seconds
            )
            steps.append(search_step)
        
        if recommend_tools:
            recommendation_step = WorkflowStep(
                id="comprehensive_recommendation",
                tool_id=recommend_tools[0].tool_id,
                tool_name=recommend_tools[0].tool_name,
                depends_on=["comprehensive_search"] if search_tools else ["discovery_phase"],
                input_mapping=[
                    DataMapping(
                        source_field="comprehensive_search.comprehensive_results" if search_tools else "intent.parameters.restaurants",
                        target_field="restaurants"
                    ),
                    DataMapping(source_field="context.mbti_type", target_field="mbti_type", required=False)
                ],
                output_mapping=[
                    DataMapping(source_field="recommendations", target_field="comprehensive_recommendations")
                ],
                timeout_seconds=config.step_timeout_seconds
            )
            steps.append(recommendation_step)
        
        # Phase 3: Results synthesis and planning
        synthesis_step = WorkflowStep(
            id="results_synthesis",
            tool_id="results_synthesizer",
            tool_name="Results Synthesizer",
            depends_on=[step.id for step in steps if step.id != "discovery_phase"],
            input_mapping=[
                DataMapping(source_field="comprehensive_search.comprehensive_results", target_field="search_results", required=False),
                DataMapping(source_field="comprehensive_recommendation.comprehensive_recommendations", target_field="recommendations", required=False),
                DataMapping(source_field="discovery_phase.discovery_insights", target_field="insights")
            ],
            output_mapping=[
                DataMapping(source_field="synthesized_plan", target_field="final_plan"),
                DataMapping(source_field="execution_summary", target_field="summary")
            ],
            timeout_seconds=config.step_timeout_seconds
        )
        steps.append(synthesis_step)
        
        return Workflow(
            id=workflow_id,
            name="Comprehensive Planning",
            description="Comprehensive workflow for complex travel planning requests",
            steps=steps,
            execution_strategy=ExecutionStrategy.SEQUENTIAL,
            context_data={
                'template_type': TemplateType.COMPREHENSIVE_PLANNING.value,
                'complexity_level': 'high',
                'multi_phase_execution': True,
                'includes_synthesis': True
            }
        )
    
    def get_available_templates(self) -> List[Dict[str, Any]]:
        """Get list of available workflow templates."""
        return [
            {
                'type': template_type.value,
                'name': template_type.value.replace('_', ' ').title(),
                'description': self._get_template_description(template_type)
            }
            for template_type in self._templates.keys()
        ]
    
    def _get_template_description(self, template_type: TemplateType) -> str:
        """Get description for a template type."""
        descriptions = {
            TemplateType.SEARCH_THEN_RECOMMEND: "Search for restaurants then provide personalized recommendations",
            TemplateType.MULTI_CRITERIA_SEARCH: "Search using multiple criteria and merge results",
            TemplateType.ITERATIVE_REFINEMENT: "Iteratively refine search results for complex requests",
            TemplateType.PARALLEL_SEARCH_MERGE: "Execute parallel searches and intelligently merge results",
            TemplateType.CONDITIONAL_RECOMMENDATION: "Provide recommendations based on user context and MBTI type",
            TemplateType.SENTIMENT_ANALYSIS_WORKFLOW: "Comprehensive sentiment analysis with interpretation",
            TemplateType.COMPREHENSIVE_PLANNING: "Comprehensive workflow for complex travel planning requests"
        }
        
        return descriptions.get(template_type, "Custom workflow template")
    
    def validate_template_config(self, config: TemplateConfig) -> List[str]:
        """Validate template configuration and return any issues."""
        issues = []
        
        # Check required parameters based on template type
        if config.template_type == TemplateType.ITERATIVE_REFINEMENT:
            max_iterations = config.get_parameter('max_iterations')
            if max_iterations is None or max_iterations < 1:
                issues.append("Iterative refinement requires max_iterations >= 1")
        
        # Check timeout values
        if config.step_timeout_seconds <= 0:
            issues.append("Step timeout must be positive")
        
        # Check recommendation score threshold
        if not (0.0 <= config.min_recommendation_score <= 1.0):
            issues.append("Minimum recommendation score must be between 0.0 and 1.0")
        
        return issues