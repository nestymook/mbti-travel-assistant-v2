"""
Tool Registry System

This module provides a comprehensive tool registry for managing MCP tool metadata,
capabilities, health status, and performance characteristics.

Features:
- Tool metadata management and storage
- Capability-based tool discovery
- Health status tracking and updates
- Performance characteristics monitoring
- Tool instance management
- Integration with MCP server discovery
"""

import logging
import time
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Set, Union, TYPE_CHECKING
from dataclasses import dataclass, field, asdict
from enum import Enum
from collections import defaultdict
import threading
import asyncio

# Type hints only imports to avoid circular dependency
if TYPE_CHECKING:
    from .restaurant_search_tool import RestaurantSearchTool
    from .restaurant_reasoning_tool import RestaurantReasoningTool


class ToolHealthStatus(Enum):
    """Health status of a tool."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class ToolType(Enum):
    """Types of tools in the registry."""
    RESTAURANT_SEARCH = "restaurant_search"
    RESTAURANT_REASONING = "restaurant_reasoning"
    SENTIMENT_ANALYSIS = "sentiment_analysis"
    GENERIC_MCP = "generic_mcp"


@dataclass
class ToolCapability:
    """Represents a capability that a tool provides."""
    name: str
    description: str
    required_parameters: List[str] = field(default_factory=list)
    optional_parameters: List[str] = field(default_factory=list)
    output_format: str = "json"
    use_cases: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ToolCapability':
        """Create from dictionary."""
        return cls(**data)


@dataclass
class ResourceRequirements:
    """Resource requirements for a tool."""
    cpu_cores: float = 1.0
    memory_mb: int = 512
    network_bandwidth_mbps: float = 10.0
    storage_mb: int = 100
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)


@dataclass
class PerformanceCharacteristics:
    """Performance characteristics of a tool."""
    average_response_time_ms: float = 1000.0
    success_rate: float = 0.95
    throughput_requests_per_minute: int = 60
    resource_requirements: ResourceRequirements = field(default_factory=ResourceRequirements)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        data['resource_requirements'] = self.resource_requirements.to_dict()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PerformanceCharacteristics':
        """Create from dictionary."""
        resource_data = data.pop('resource_requirements', {})
        resource_requirements = ResourceRequirements(**resource_data)
        return cls(resource_requirements=resource_requirements, **data)


@dataclass
class ToolMetadata:
    """Comprehensive metadata for a registered tool."""
    id: str
    name: str
    description: str
    tool_type: ToolType
    capabilities: List[ToolCapability] = field(default_factory=list)
    version: str = "1.0.0"
    
    # MCP-specific metadata
    mcp_server_url: Optional[str] = None
    mcp_tool_name: Optional[str] = None
    
    # Schema information
    input_schema: Dict[str, Any] = field(default_factory=dict)
    output_schema: Dict[str, Any] = field(default_factory=dict)
    
    # Performance and health
    performance_characteristics: PerformanceCharacteristics = field(default_factory=PerformanceCharacteristics)
    health_check_endpoint: Optional[str] = None
    health_check_interval_seconds: int = 60
    
    # Registration metadata
    registered_at: datetime = field(default_factory=datetime.utcnow)
    last_updated: datetime = field(default_factory=datetime.utcnow)
    
    # Tags and categorization
    tags: Set[str] = field(default_factory=set)
    category: str = "general"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        data['tool_type'] = self.tool_type.value
        data['capabilities'] = [cap.to_dict() for cap in self.capabilities]
        data['performance_characteristics'] = self.performance_characteristics.to_dict()
        data['registered_at'] = self.registered_at.isoformat()
        data['last_updated'] = self.last_updated.isoformat()
        data['tags'] = list(self.tags)
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ToolMetadata':
        """Create from dictionary."""
        # Convert tool_type
        tool_type = ToolType(data.pop('tool_type'))
        
        # Convert capabilities
        capabilities_data = data.pop('capabilities', [])
        capabilities = [ToolCapability.from_dict(cap) for cap in capabilities_data]
        
        # Convert performance characteristics
        perf_data = data.pop('performance_characteristics', {})
        performance_characteristics = PerformanceCharacteristics.from_dict(perf_data)
        
        # Convert datetime fields
        registered_at = datetime.fromisoformat(data.pop('registered_at', datetime.utcnow().isoformat()))
        last_updated = datetime.fromisoformat(data.pop('last_updated', datetime.utcnow().isoformat()))
        
        # Convert tags
        tags = set(data.pop('tags', []))
        
        return cls(
            tool_type=tool_type,
            capabilities=capabilities,
            performance_characteristics=performance_characteristics,
            registered_at=registered_at,
            last_updated=last_updated,
            tags=tags,
            **data
        )


@dataclass
class ToolHealthRecord:
    """Health check record for a tool."""
    tool_id: str
    status: ToolHealthStatus
    timestamp: datetime
    response_time_ms: float = 0.0
    error_message: Optional[str] = None
    additional_data: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        data['status'] = self.status.value
        data['timestamp'] = self.timestamp.isoformat()
        return data


class ToolRegistry:
    """
    Comprehensive registry for managing tool metadata, capabilities, and health status.
    
    Features:
    - Tool registration and metadata management
    - Capability-based tool discovery
    - Health status tracking
    - Performance monitoring integration
    - MCP server integration
    """
    
    def __init__(self):
        """Initialize the tool registry."""
        self.logger = logging.getLogger(f"mbti_travel_planner.tool_registry")
        
        # Tool storage
        self._tools: Dict[str, ToolMetadata] = {}
        self._tool_instances: Dict[str, Any] = {}
        
        # Capability indexing
        self._capability_index: Dict[str, Set[str]] = defaultdict(set)
        self._tag_index: Dict[str, Set[str]] = defaultdict(set)
        self._type_index: Dict[ToolType, Set[str]] = defaultdict(set)
        
        # Health tracking
        self._health_status: Dict[str, ToolHealthStatus] = {}
        self._health_history: Dict[str, List[ToolHealthRecord]] = defaultdict(list)
        self._last_health_check: Dict[str, datetime] = {}
        
        # Performance tracking
        self._performance_metrics: Dict[str, Dict[str, Any]] = defaultdict(dict)
        
        # Thread safety
        self._lock = threading.RLock()
        
        self.logger.info("Tool registry initialized")
    
    def register_tool(self, tool_metadata: ToolMetadata, tool_instance: Any = None) -> None:
        """
        Register a tool with the registry.
        
        Args:
            tool_metadata: Tool metadata
            tool_instance: Optional tool instance for direct invocation
        """
        with self._lock:
            tool_id = tool_metadata.id
            
            # Store tool metadata
            self._tools[tool_id] = tool_metadata
            
            # Store tool instance if provided
            if tool_instance is not None:
                self._tool_instances[tool_id] = tool_instance
            
            # Update indexes
            self._update_indexes(tool_metadata)
            
            # Initialize health status
            self._health_status[tool_id] = ToolHealthStatus.UNKNOWN
            
            self.logger.info(f"Tool registered: {tool_metadata.name} ({tool_id})", extra={
                'tool_id': tool_id,
                'tool_name': tool_metadata.name,
                'tool_type': tool_metadata.tool_type.value,
                'capabilities': [cap.name for cap in tool_metadata.capabilities]
            })
    
    def unregister_tool(self, tool_id: str) -> bool:
        """
        Unregister a tool from the registry.
        
        Args:
            tool_id: Tool identifier
            
        Returns:
            True if tool was unregistered, False if not found
        """
        with self._lock:
            if tool_id not in self._tools:
                return False
            
            tool_metadata = self._tools[tool_id]
            
            # Remove from storage
            del self._tools[tool_id]
            self._tool_instances.pop(tool_id, None)
            
            # Remove from indexes
            self._remove_from_indexes(tool_metadata)
            
            # Remove health data
            self._health_status.pop(tool_id, None)
            self._health_history.pop(tool_id, None)
            self._last_health_check.pop(tool_id, None)
            self._performance_metrics.pop(tool_id, None)
            
            self.logger.info(f"Tool unregistered: {tool_metadata.name} ({tool_id})")
            return True
    
    def get_tool_metadata(self, tool_id: str) -> Optional[ToolMetadata]:
        """Get tool metadata by ID."""
        with self._lock:
            return self._tools.get(tool_id)
    
    def get_tool_instance(self, tool_id: str) -> Optional[Any]:
        """Get tool instance by ID."""
        with self._lock:
            return self._tool_instances.get(tool_id)
    
    def get_all_tools(self) -> List[ToolMetadata]:
        """Get all registered tools."""
        with self._lock:
            return list(self._tools.values())
    
    def get_tools_by_type(self, tool_type: ToolType) -> List[ToolMetadata]:
        """Get tools by type."""
        with self._lock:
            tool_ids = self._type_index.get(tool_type, set())
            return [self._tools[tool_id] for tool_id in tool_ids if tool_id in self._tools]
    
    def get_tools_by_capabilities(self, capabilities: List[str]) -> List[ToolMetadata]:
        """
        Get tools that have all specified capabilities.
        
        Args:
            capabilities: List of required capability names
            
        Returns:
            List of tools that have all specified capabilities
        """
        with self._lock:
            if not capabilities:
                return list(self._tools.values())
            
            # Find tools that have all required capabilities
            matching_tool_ids = None
            
            for capability in capabilities:
                tool_ids_with_capability = self._capability_index.get(capability, set())
                
                if matching_tool_ids is None:
                    matching_tool_ids = tool_ids_with_capability.copy()
                else:
                    matching_tool_ids &= tool_ids_with_capability
            
            if matching_tool_ids is None:
                return []
            
            return [self._tools[tool_id] for tool_id in matching_tool_ids if tool_id in self._tools]
    
    def get_tools_by_tags(self, tags: List[str]) -> List[ToolMetadata]:
        """Get tools that have any of the specified tags."""
        with self._lock:
            matching_tool_ids = set()
            
            for tag in tags:
                matching_tool_ids.update(self._tag_index.get(tag, set()))
            
            return [self._tools[tool_id] for tool_id in matching_tool_ids if tool_id in self._tools]
    
    def search_tools(self, 
                    query: str = None,
                    tool_type: ToolType = None,
                    capabilities: List[str] = None,
                    tags: List[str] = None,
                    health_status: ToolHealthStatus = None) -> List[ToolMetadata]:
        """
        Search tools with multiple criteria.
        
        Args:
            query: Text query to search in name and description
            tool_type: Filter by tool type
            capabilities: Filter by required capabilities
            tags: Filter by tags
            health_status: Filter by health status
            
        Returns:
            List of matching tools
        """
        with self._lock:
            results = list(self._tools.values())
            
            # Filter by tool type
            if tool_type is not None:
                results = [tool for tool in results if tool.tool_type == tool_type]
            
            # Filter by capabilities
            if capabilities:
                tools_with_capabilities = self.get_tools_by_capabilities(capabilities)
                capability_ids = {tool.id for tool in tools_with_capabilities}
                results = [tool for tool in results if tool.id in capability_ids]
            
            # Filter by tags
            if tags:
                results = [tool for tool in results if any(tag in tool.tags for tag in tags)]
            
            # Filter by health status
            if health_status is not None:
                results = [tool for tool in results 
                          if self._health_status.get(tool.id) == health_status]
            
            # Filter by text query
            if query:
                query_lower = query.lower()
                results = [tool for tool in results 
                          if (query_lower in tool.name.lower() or 
                              query_lower in tool.description.lower())]
            
            return results
    
    def update_tool_health_status(self, 
                                 tool_id: str, 
                                 status: ToolHealthStatus,
                                 response_time_ms: float = 0.0,
                                 error_message: Optional[str] = None,
                                 additional_data: Dict[str, Any] = None) -> None:
        """
        Update tool health status.
        
        Args:
            tool_id: Tool identifier
            status: New health status
            response_time_ms: Response time for health check
            error_message: Error message if unhealthy
            additional_data: Additional health check data
        """
        with self._lock:
            if tool_id not in self._tools:
                self.logger.warning(f"Attempted to update health for unknown tool: {tool_id}")
                return
            
            # Update current status
            old_status = self._health_status.get(tool_id, ToolHealthStatus.UNKNOWN)
            self._health_status[tool_id] = status
            self._last_health_check[tool_id] = datetime.utcnow()
            
            # Create health record
            health_record = ToolHealthRecord(
                tool_id=tool_id,
                status=status,
                timestamp=datetime.utcnow(),
                response_time_ms=response_time_ms,
                error_message=error_message,
                additional_data=additional_data or {}
            )
            
            # Store in history (keep last 100 records)
            self._health_history[tool_id].append(health_record)
            if len(self._health_history[tool_id]) > 100:
                self._health_history[tool_id] = self._health_history[tool_id][-100:]
            
            # Log status changes
            if old_status != status:
                self.logger.info(f"Tool health status changed: {self._tools[tool_id].name}", extra={
                    'tool_id': tool_id,
                    'old_status': old_status.value,
                    'new_status': status.value,
                    'response_time_ms': response_time_ms,
                    'error_message': error_message
                })
    
    def get_tool_health_status(self, tool_id: str) -> Optional[ToolHealthStatus]:
        """Get current health status of a tool."""
        with self._lock:
            return self._health_status.get(tool_id)
    
    def get_tool_health_history(self, 
                               tool_id: str, 
                               limit: int = 50) -> List[ToolHealthRecord]:
        """Get health history for a tool."""
        with self._lock:
            history = self._health_history.get(tool_id, [])
            return history[-limit:] if limit > 0 else history
    
    def get_healthy_tools(self) -> List[ToolMetadata]:
        """Get all tools with healthy status."""
        with self._lock:
            healthy_tool_ids = [
                tool_id for tool_id, status in self._health_status.items()
                if status == ToolHealthStatus.HEALTHY
            ]
            return [self._tools[tool_id] for tool_id in healthy_tool_ids if tool_id in self._tools]
    
    def update_tool_performance_metrics(self, 
                                       tool_id: str, 
                                       metrics: Dict[str, Any]) -> None:
        """
        Update performance metrics for a tool.
        
        Args:
            tool_id: Tool identifier
            metrics: Performance metrics dictionary
        """
        with self._lock:
            if tool_id not in self._tools:
                return
            
            self._performance_metrics[tool_id].update(metrics)
            self._performance_metrics[tool_id]['last_updated'] = datetime.utcnow().isoformat()
    
    def get_tool_performance_metrics(self, tool_id: str) -> Dict[str, Any]:
        """Get performance metrics for a tool."""
        with self._lock:
            return self._performance_metrics.get(tool_id, {}).copy()
    
    def get_registry_statistics(self) -> Dict[str, Any]:
        """Get registry statistics."""
        with self._lock:
            # Count tools by type
            type_counts = defaultdict(int)
            for tool in self._tools.values():
                type_counts[tool.tool_type.value] += 1
            
            # Count tools by health status
            health_counts = defaultdict(int)
            for status in self._health_status.values():
                health_counts[status.value] += 1
            
            # Count capabilities
            capability_counts = {
                capability: len(tool_ids) 
                for capability, tool_ids in self._capability_index.items()
            }
            
            return {
                'total_tools': len(self._tools),
                'tools_with_instances': len(self._tool_instances),
                'tools_by_type': dict(type_counts),
                'tools_by_health_status': dict(health_counts),
                'total_capabilities': len(self._capability_index),
                'capability_distribution': capability_counts,
                'last_updated': datetime.utcnow().isoformat()
            }
    
    def export_registry(self) -> Dict[str, Any]:
        """Export registry data for backup or migration."""
        with self._lock:
            return {
                'tools': {tool_id: tool.to_dict() for tool_id, tool in self._tools.items()},
                'health_status': {
                    tool_id: status.value 
                    for tool_id, status in self._health_status.items()
                },
                'health_history': {
                    tool_id: [record.to_dict() for record in records]
                    for tool_id, records in self._health_history.items()
                },
                'performance_metrics': dict(self._performance_metrics),
                'exported_at': datetime.utcnow().isoformat()
            }
    
    def import_registry(self, data: Dict[str, Any]) -> None:
        """Import registry data from backup."""
        with self._lock:
            # Clear existing data
            self._tools.clear()
            self._tool_instances.clear()
            self._capability_index.clear()
            self._tag_index.clear()
            self._type_index.clear()
            self._health_status.clear()
            self._health_history.clear()
            self._performance_metrics.clear()
            
            # Import tools
            tools_data = data.get('tools', {})
            for tool_id, tool_data in tools_data.items():
                tool_metadata = ToolMetadata.from_dict(tool_data)
                self._tools[tool_id] = tool_metadata
                self._update_indexes(tool_metadata)
            
            # Import health status
            health_status_data = data.get('health_status', {})
            for tool_id, status_value in health_status_data.items():
                self._health_status[tool_id] = ToolHealthStatus(status_value)
            
            # Import health history
            health_history_data = data.get('health_history', {})
            for tool_id, records_data in health_history_data.items():
                records = []
                for record_data in records_data:
                    record = ToolHealthRecord(
                        tool_id=record_data['tool_id'],
                        status=ToolHealthStatus(record_data['status']),
                        timestamp=datetime.fromisoformat(record_data['timestamp']),
                        response_time_ms=record_data.get('response_time_ms', 0.0),
                        error_message=record_data.get('error_message'),
                        additional_data=record_data.get('additional_data', {})
                    )
                    records.append(record)
                self._health_history[tool_id] = records
            
            # Import performance metrics
            performance_data = data.get('performance_metrics', {})
            self._performance_metrics.update(performance_data)
            
            self.logger.info(f"Registry imported: {len(self._tools)} tools loaded")
    
    def _update_indexes(self, tool_metadata: ToolMetadata) -> None:
        """Update internal indexes for a tool."""
        tool_id = tool_metadata.id
        
        # Update capability index
        for capability in tool_metadata.capabilities:
            self._capability_index[capability.name].add(tool_id)
        
        # Update tag index
        for tag in tool_metadata.tags:
            self._tag_index[tag].add(tool_id)
        
        # Update type index
        self._type_index[tool_metadata.tool_type].add(tool_id)
    
    def _remove_from_indexes(self, tool_metadata: ToolMetadata) -> None:
        """Remove tool from internal indexes."""
        tool_id = tool_metadata.id
        
        # Remove from capability index
        for capability in tool_metadata.capabilities:
            self._capability_index[capability.name].discard(tool_id)
            if not self._capability_index[capability.name]:
                del self._capability_index[capability.name]
        
        # Remove from tag index
        for tag in tool_metadata.tags:
            self._tag_index[tag].discard(tool_id)
            if not self._tag_index[tag]:
                del self._tag_index[tag]
        
        # Remove from type index
        self._type_index[tool_metadata.tool_type].discard(tool_id)
        if not self._type_index[tool_metadata.tool_type]:
            del self._type_index[tool_metadata.tool_type]
    
    async def perform_health_checks(self) -> Dict[str, ToolHealthRecord]:
        """
        Perform health checks on all registered tools.
        
        Returns:
            Dictionary of tool_id -> health check results
        """
        results = {}
        
        with self._lock:
            tools_to_check = list(self._tools.items())
        
        for tool_id, tool_metadata in tools_to_check:
            try:
                # Check if health check is needed
                last_check = self._last_health_check.get(tool_id)
                if (last_check and 
                    datetime.utcnow() - last_check < timedelta(seconds=tool_metadata.health_check_interval_seconds)):
                    continue
                
                # Perform health check
                health_result = await self._perform_tool_health_check(tool_id, tool_metadata)
                results[tool_id] = health_result
                
                # Update health status
                self.update_tool_health_status(
                    tool_id=tool_id,
                    status=health_result.status,
                    response_time_ms=health_result.response_time_ms,
                    error_message=health_result.error_message,
                    additional_data=health_result.additional_data
                )
                
            except Exception as e:
                self.logger.error(f"Health check failed for tool {tool_id}: {e}")
                
                # Mark as unhealthy
                error_result = ToolHealthRecord(
                    tool_id=tool_id,
                    status=ToolHealthStatus.UNHEALTHY,
                    timestamp=datetime.utcnow(),
                    error_message=str(e)
                )
                results[tool_id] = error_result
                
                self.update_tool_health_status(
                    tool_id=tool_id,
                    status=ToolHealthStatus.UNHEALTHY,
                    error_message=str(e)
                )
        
        return results
    
    async def _perform_tool_health_check(self, 
                                        tool_id: str, 
                                        tool_metadata: ToolMetadata) -> ToolHealthRecord:
        """Perform health check on a specific tool."""
        start_time = time.time()
        
        try:
            # Get tool instance
            tool_instance = self._tool_instances.get(tool_id)
            
            if not tool_instance:
                return ToolHealthRecord(
                    tool_id=tool_id,
                    status=ToolHealthStatus.UNKNOWN,
                    timestamp=datetime.utcnow(),
                    error_message="Tool instance not available"
                )
            
            # Perform basic health check
            if hasattr(tool_instance, 'health_check'):
                # Tool has custom health check method
                health_result = await tool_instance.health_check()
                status = ToolHealthStatus.HEALTHY if health_result.get('healthy', False) else ToolHealthStatus.UNHEALTHY
                error_message = health_result.get('error')
                additional_data = health_result
            else:
                # Basic availability check
                status = ToolHealthStatus.HEALTHY
                error_message = None
                additional_data = {'check_type': 'basic_availability'}
            
            response_time_ms = (time.time() - start_time) * 1000
            
            return ToolHealthRecord(
                tool_id=tool_id,
                status=status,
                timestamp=datetime.utcnow(),
                response_time_ms=response_time_ms,
                error_message=error_message,
                additional_data=additional_data
            )
            
        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            
            return ToolHealthRecord(
                tool_id=tool_id,
                status=ToolHealthStatus.UNHEALTHY,
                timestamp=datetime.utcnow(),
                response_time_ms=response_time_ms,
                error_message=str(e)
            )
    
    async def discover_mcp_tools(self, mcp_server_url: str, openapi_schema_path: str = None) -> List[ToolMetadata]:
        """
        Discover tools from an MCP server using OpenAPI schema.
        
        Args:
            mcp_server_url: URL of the MCP server
            openapi_schema_path: Optional path to OpenAPI schema file (if not provided, will try to fetch from server)
            
        Returns:
            List of discovered tool metadata
        """
        discovered_tools = []
        
        try:
            # Load OpenAPI schema
            if openapi_schema_path:
                # Load from local file
                import yaml
                with open(openapi_schema_path, 'r') as f:
                    schema = yaml.safe_load(f)
            else:
                # Try to fetch from server
                import requests
                response = requests.get(f"{mcp_server_url}/openapi.yaml")
                response.raise_for_status()
                import yaml
                schema = yaml.safe_load(response.text)
            
            # Extract tool information from OpenAPI schema
            paths = schema.get('paths', {})
            
            for path, path_info in paths.items():
                if '/mcp/tools/' in path:
                    # This is an MCP tool endpoint
                    tool_metadata = self._extract_tool_metadata_from_openapi(
                        path, path_info, schema, mcp_server_url
                    )
                    if tool_metadata:
                        discovered_tools.append(tool_metadata)
            
            self.logger.info(f"Discovered {len(discovered_tools)} tools from MCP server: {mcp_server_url}")
            
        except Exception as e:
            self.logger.error(f"Failed to discover tools from MCP server {mcp_server_url}: {e}")
        
        return discovered_tools
    
    def _extract_tool_metadata_from_openapi(self, 
                                           path: str, 
                                           path_info: Dict[str, Any], 
                                           schema: Dict[str, Any],
                                           mcp_server_url: str) -> Optional[ToolMetadata]:
        """Extract tool metadata from OpenAPI path definition."""
        try:
            # Get POST operation (MCP tools use POST)
            post_op = path_info.get('post', {})
            if not post_op:
                return None
            
            # Extract tool name from path
            tool_name = path.split('/')[-1]  # e.g., /mcp/tools/search_restaurants -> search_restaurants
            
            # Determine tool type based on path/operation
            if 'search' in tool_name.lower():
                tool_type = ToolType.RESTAURANT_SEARCH
            elif 'recommend' in tool_name.lower() or 'reason' in tool_name.lower() or 'analyz' in tool_name.lower():
                tool_type = ToolType.RESTAURANT_REASONING
            else:
                tool_type = ToolType.GENERIC_MCP
            
            # Extract capabilities from operation
            capabilities = self._extract_capabilities_from_operation(post_op, tool_name)
            
            # Extract schemas
            request_body = post_op.get('requestBody', {})
            input_schema = {}
            if request_body:
                content = request_body.get('content', {})
                json_content = content.get('application/json', {})
                input_schema = json_content.get('schema', {})
            
            # Extract response schema
            responses = post_op.get('responses', {})
            success_response = responses.get('200', {})
            output_schema = {}
            if success_response:
                content = success_response.get('content', {})
                json_content = content.get('application/json', {})
                output_schema = json_content.get('schema', {})
            
            # Create performance characteristics based on tool type
            if tool_type == ToolType.RESTAURANT_SEARCH:
                perf_chars = PerformanceCharacteristics(
                    average_response_time_ms=2000.0,
                    success_rate=0.95,
                    throughput_requests_per_minute=30
                )
            elif tool_type == ToolType.RESTAURANT_REASONING:
                perf_chars = PerformanceCharacteristics(
                    average_response_time_ms=3000.0,
                    success_rate=0.92,
                    throughput_requests_per_minute=20
                )
            else:
                perf_chars = PerformanceCharacteristics()
            
            # Create tool metadata
            tool_metadata = ToolMetadata(
                id=f"mcp_{tool_name}",
                name=post_op.get('summary', tool_name.replace('_', ' ').title()),
                description=post_op.get('description', f"MCP tool: {tool_name}"),
                tool_type=tool_type,
                capabilities=capabilities,
                version="1.0.0",
                mcp_server_url=mcp_server_url,
                mcp_tool_name=tool_name,
                input_schema=input_schema,
                output_schema=output_schema,
                performance_characteristics=perf_chars,
                health_check_endpoint=f"{mcp_server_url}/health",
                health_check_interval_seconds=120,
                tags={"mcp", "discovered", tool_type.value},
                category="mcp_tools"
            )
            
            return tool_metadata
            
        except Exception as e:
            self.logger.error(f"Failed to extract tool metadata from path {path}: {e}")
            return None
    
    def _extract_capabilities_from_operation(self, operation: Dict[str, Any], tool_name: str) -> List[ToolCapability]:
        """Extract capabilities from OpenAPI operation definition."""
        capabilities = []
        
        try:
            # Get request body schema to understand parameters
            request_body = operation.get('requestBody', {})
            content = request_body.get('content', {})
            json_content = content.get('application/json', {})
            schema = json_content.get('schema', {})
            
            properties = schema.get('properties', {})
            required = schema.get('required', [])
            
            # Extract parameters
            required_params = []
            optional_params = []
            
            for param_name, param_info in properties.items():
                if param_name in required:
                    required_params.append(param_name)
                else:
                    optional_params.append(param_name)
            
            # Determine use cases based on tool name and parameters
            use_cases = []
            if 'search' in tool_name.lower():
                if 'district' in str(properties).lower():
                    use_cases.append("location-based search")
                if 'meal' in str(properties).lower():
                    use_cases.append("meal-type filtering")
                use_cases.append("restaurant discovery")
            elif 'recommend' in tool_name.lower():
                use_cases.extend(["intelligent recommendations", "sentiment analysis"])
            elif 'analyz' in tool_name.lower():
                use_cases.extend(["data analysis", "sentiment analysis"])
            
            # Create main capability
            capability = ToolCapability(
                name=tool_name,
                description=operation.get('summary', f"MCP tool capability: {tool_name}"),
                required_parameters=required_params,
                optional_parameters=optional_params,
                output_format="json",
                use_cases=use_cases
            )
            
            capabilities.append(capability)
            
        except Exception as e:
            self.logger.error(f"Failed to extract capabilities for tool {tool_name}: {e}")
        
        return capabilities
    
    async def register_mcp_server_tools(self, mcp_server_url: str, openapi_schema_path: str = None) -> int:
        """
        Discover and register all tools from an MCP server.
        
        Args:
            mcp_server_url: URL of the MCP server
            openapi_schema_path: Optional path to OpenAPI schema file
            
        Returns:
            Number of tools registered
        """
        discovered_tools = await self.discover_mcp_tools(mcp_server_url, openapi_schema_path)
        
        registered_count = 0
        for tool_metadata in discovered_tools:
            try:
                # Create MCP tool wrapper instance
                mcp_tool_instance = MCPToolWrapper(
                    tool_metadata.mcp_tool_name,
                    mcp_server_url,
                    tool_metadata.input_schema,
                    tool_metadata.output_schema
                )
                
                # Register with the registry
                self.register_tool(tool_metadata, mcp_tool_instance)
                registered_count += 1
                
            except Exception as e:
                self.logger.error(f"Failed to register MCP tool {tool_metadata.id}: {e}")
        
        self.logger.info(f"Registered {registered_count} MCP tools from server: {mcp_server_url}")
        return registered_count


class MCPToolWrapper:
    """Wrapper for MCP tools to provide consistent interface."""
    
    def __init__(self, tool_name: str, server_url: str, input_schema: Dict, output_schema: Dict):
        """Initialize MCP tool wrapper."""
        self.tool_name = tool_name
        self.server_url = server_url
        self.input_schema = input_schema
        self.output_schema = output_schema
        self.logger = logging.getLogger(f"mcp_tool.{tool_name}")
    
    async def invoke(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Invoke the MCP tool with given parameters."""
        try:
            import requests
            
            # Construct endpoint URL
            endpoint = f"{self.server_url}/mcp/tools/{self.tool_name}"
            
            # Make request to MCP server
            response = requests.post(
                endpoint,
                json=parameters,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            self.logger.error(f"Failed to invoke MCP tool {self.tool_name}: {e}")
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on the MCP tool."""
        try:
            import requests
            
            # Check server health endpoint
            health_url = f"{self.server_url}/health"
            response = requests.get(health_url, timeout=10)
            response.raise_for_status()
            
            health_data = response.json()
            
            return {
                "healthy": health_data.get("status") == "healthy",
                "server_status": health_data.get("status"),
                "response_time_ms": response.elapsed.total_seconds() * 1000,
                "tool_name": self.tool_name,
                "server_url": self.server_url
            }
            
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e),
                "tool_name": self.tool_name,
                "server_url": self.server_url
            }


# Convenience functions for creating common tool metadata

def create_restaurant_search_tool_metadata(tool_id: str = "restaurant_search_tool") -> ToolMetadata:
    """Create metadata for restaurant search tool."""
    capabilities = [
        ToolCapability(
            name="search_by_district",
            description="Search restaurants by district/location",
            required_parameters=["districts"],
            optional_parameters=["meal_types"],
            use_cases=["location-based restaurant discovery"]
        ),
        ToolCapability(
            name="search_by_meal_type",
            description="Search restaurants by meal type",
            required_parameters=["meal_types"],
            optional_parameters=["districts"],
            use_cases=["meal-specific restaurant search"]
        ),
        ToolCapability(
            name="combined_search",
            description="Search restaurants using combined filters",
            required_parameters=[],
            optional_parameters=["districts", "meal_types"],
            use_cases=["multi-criteria search", "flexible filtering"]
        )
    ]
    
    performance_chars = PerformanceCharacteristics(
        average_response_time_ms=2000.0,
        success_rate=0.95,
        throughput_requests_per_minute=30
    )
    
    return ToolMetadata(
        id=tool_id,
        name="Restaurant Search Tool",
        description="Search restaurants by district and meal type",
        tool_type=ToolType.RESTAURANT_SEARCH,
        capabilities=capabilities,
        performance_characteristics=performance_chars,
        tags={"restaurant", "search", "location", "meal_type"},
        category="restaurant_services"
    )


def create_restaurant_reasoning_tool_metadata(tool_id: str = "restaurant_reasoning_tool") -> ToolMetadata:
    """Create metadata for restaurant reasoning tool."""
    capabilities = [
        ToolCapability(
            name="recommend_restaurants",
            description="Generate intelligent restaurant recommendations",
            required_parameters=["restaurants"],
            optional_parameters=["ranking_method"],
            use_cases=["restaurant recommendations", "sentiment analysis"]
        ),
        ToolCapability(
            name="mbti_recommendations",
            description="Generate MBTI-based recommendations",
            required_parameters=["restaurants", "mbti_type", "preferences"],
            optional_parameters=["ranking_method"],
            use_cases=["personality-based recommendations", "MBTI analysis"]
        ),
        ToolCapability(
            name="sentiment_analysis",
            description="Analyze restaurant sentiment data",
            required_parameters=["restaurants"],
            optional_parameters=["ranking_method"],
            use_cases=["sentiment analysis", "data analysis"]
        )
    ]
    
    performance_chars = PerformanceCharacteristics(
        average_response_time_ms=3000.0,
        success_rate=0.92,
        throughput_requests_per_minute=20
    )
    
    return ToolMetadata(
        id=tool_id,
        name="Restaurant Reasoning Tool",
        description="Advanced restaurant reasoning with MBTI analysis",
        tool_type=ToolType.RESTAURANT_REASONING,
        capabilities=capabilities,
        performance_characteristics=performance_chars,
        tags={"restaurant", "reasoning", "mbti", "sentiment"},
        category="restaurant_services"
    )


async def register_known_mcp_servers(registry: ToolRegistry) -> Dict[str, int]:
    """
    Register tools from known MCP servers.
    
    Args:
        registry: Tool registry instance
        
    Returns:
        Dictionary mapping server URLs to number of registered tools
    """
    results = {}
    
    # Known MCP servers with their OpenAPI schema paths
    known_servers = [
        {
            "url": "http://localhost:8080",  # Restaurant Search MCP
            "schema_path": "restaurant-search-mcp/openapi.yaml",
            "name": "Restaurant Search MCP"
        },
        {
            "url": "http://localhost:8081",  # Restaurant Reasoning MCP  
            "schema_path": "restaurant-search-result-reasoning-mcp/openapi.yaml",
            "name": "Restaurant Reasoning MCP"
        }
    ]
    
    for server_info in known_servers:
        try:
            count = await registry.register_mcp_server_tools(
                server_info["url"],
                server_info["schema_path"]
            )
            results[server_info["name"]] = count
            
        except Exception as e:
            registry.logger.error(f"Failed to register tools from {server_info['name']}: {e}")
            results[server_info["name"]] = 0
    
    return results
    
    return ToolMetadata(
        id=tool_id,
        name="Restaurant Search Tool",
        description="MCP tool for searching restaurants by location and meal type",
        tool_type=ToolType.RESTAURANT_SEARCH,
        capabilities=capabilities,
        mcp_server_url="https://restaurant-search-mcp.bedrock-agentcore.us-east-1.amazonaws.com",
        category="restaurant",
        tags={"search", "restaurant", "location", "meal"},
        performance_characteristics=PerformanceCharacteristics(
            average_response_time_ms=2000.0,
            success_rate=0.98,
            throughput_requests_per_minute=120
        )
    )


def create_restaurant_reasoning_tool_metadata(tool_id: str = "restaurant_reasoning_tool") -> ToolMetadata:
    """Create metadata for restaurant reasoning tool."""
    capabilities = [
        ToolCapability(
            name="recommend_restaurants",
            description="Provide intelligent restaurant recommendations",
            required_parameters=["restaurants"],
            optional_parameters=["ranking_method", "user_preferences"],
            use_cases=["personalized restaurant recommendations"]
        ),
        ToolCapability(
            name="analyze_sentiment",
            description="Analyze restaurant sentiment data",
            required_parameters=["restaurants"],
            optional_parameters=[],
            use_cases=["sentiment analysis", "review analysis"]
        ),
        ToolCapability(
            name="mbti_personalization",
            description="MBTI-based restaurant personalization",
            required_parameters=["restaurants", "mbti_type"],
            optional_parameters=["preferences"],
            use_cases=["personality-based recommendations"]
        )
    ]
    
    return ToolMetadata(
        id=tool_id,
        name="Restaurant Reasoning Tool",
        description="MCP tool for restaurant recommendations and sentiment analysis",
        tool_type=ToolType.RESTAURANT_REASONING,
        capabilities=capabilities,
        mcp_server_url="https://restaurant-reasoning-mcp.bedrock-agentcore.us-east-1.amazonaws.com",
        category="restaurant",
        tags={"recommendation", "reasoning", "sentiment", "mbti"},
        performance_characteristics=PerformanceCharacteristics(
            average_response_time_ms=3000.0,
            success_rate=0.96,
            throughput_requests_per_minute=80
        )
    )