"""
Tool Registration Helper

This module provides utilities for registering existing MCP tools with the orchestration engine,
including automatic discovery from MCP server OpenAPI schemas and integration with existing tools.

Features:
- Automatic tool discovery from MCP servers
- Integration with existing restaurant search and reasoning tools
- OpenAPI schema parsing for tool metadata extraction
- Health check endpoint configuration
- Performance characteristics estimation
"""

import logging
import json
import asyncio
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
import requests
import yaml

from .tool_registry import (
    ToolRegistry, ToolMetadata, ToolCapability, ToolType, ToolHealthStatus,
    PerformanceCharacteristics, ResourceRequirements,
    create_restaurant_search_tool_metadata, create_restaurant_reasoning_tool_metadata
)
from .tool_orchestration_engine import ToolOrchestrationEngine


class ToolRegistrationHelper:
    """
    Helper class for registering tools with the orchestration engine.
    
    Provides utilities for:
    - Registering existing MCP tools
    - Discovering tools from OpenAPI schemas
    - Configuring tool metadata and capabilities
    - Setting up health checks and performance monitoring
    """
    
    def __init__(self, orchestration_engine: ToolOrchestrationEngine):
        """
        Initialize the tool registration helper.
        
        Args:
            orchestration_engine: The orchestration engine to register tools with
        """
        self.orchestration_engine = orchestration_engine
        self.tool_registry = orchestration_engine.tool_registry
        self.logger = logging.getLogger(f"mbti_travel_planner.tool_registration")
    
    def register_existing_tools(self, 
                               restaurant_search_tool: Any = None,
                               restaurant_reasoning_tool: Any = None) -> None:
        """
        Register existing restaurant tools with the orchestration engine.
        
        Args:
            restaurant_search_tool: Instance of RestaurantSearchTool
            restaurant_reasoning_tool: Instance of RestaurantReasoningTool
        """
        self.logger.info("Registering existing tools with orchestration engine")
        
        # Register restaurant search tool
        if restaurant_search_tool:
            search_metadata = create_restaurant_search_tool_metadata()
            self.tool_registry.register_tool(search_metadata, restaurant_search_tool)
            self.logger.info(f"Registered restaurant search tool: {search_metadata.id}")
        
        # Register restaurant reasoning tool
        if restaurant_reasoning_tool:
            reasoning_metadata = create_restaurant_reasoning_tool_metadata()
            self.tool_registry.register_tool(reasoning_metadata, restaurant_reasoning_tool)
            self.logger.info(f"Registered restaurant reasoning tool: {reasoning_metadata.id}")
        
        self.logger.info("Existing tools registration completed")
    
    async def discover_and_register_mcp_tools(self, 
                                             mcp_servers: List[Dict[str, str]]) -> List[str]:
        """
        Discover and register tools from MCP servers using OpenAPI schemas.
        
        Args:
            mcp_servers: List of MCP server configurations with 'name' and 'url' keys
            
        Returns:
            List of registered tool IDs
        """
        registered_tool_ids = []
        
        for server_config in mcp_servers:
            try:
                server_name = server_config.get('name', 'unknown')
                server_url = server_config.get('url')
                
                if not server_url:
                    self.logger.warning(f"No URL provided for MCP server: {server_name}")
                    continue
                
                self.logger.info(f"Discovering tools from MCP server: {server_name} ({server_url})")
                
                # Discover tools from server
                discovered_tools = await self._discover_tools_from_server(server_url, server_name)
                
                # Register discovered tools
                for tool_metadata in discovered_tools:
                    self.tool_registry.register_tool(tool_metadata)
                    registered_tool_ids.append(tool_metadata.id)
                    self.logger.info(f"Registered MCP tool: {tool_metadata.name} ({tool_metadata.id})")
                
            except Exception as e:
                self.logger.error(f"Failed to discover tools from server {server_config}: {e}")
        
        self.logger.info(f"MCP tool discovery completed. Registered {len(registered_tool_ids)} tools.")
        return registered_tool_ids
    
    async def _discover_tools_from_server(self, 
                                         server_url: str, 
                                         server_name: str) -> List[ToolMetadata]:
        """
        Discover tools from a single MCP server.
        
        Args:
            server_url: URL of the MCP server
            server_name: Name of the MCP server
            
        Returns:
            List of discovered tool metadata
        """
        discovered_tools = []
        
        try:
            # Try to get OpenAPI schema
            openapi_url = f"{server_url.rstrip('/')}/openapi.json"
            
            response = requests.get(openapi_url, timeout=10)
            if response.status_code == 200:
                openapi_schema = response.json()
                discovered_tools = self._parse_openapi_schema(openapi_schema, server_url, server_name)
            else:
                self.logger.warning(f"Could not fetch OpenAPI schema from {openapi_url}: {response.status_code}")
                
                # Try alternative discovery methods
                discovered_tools = await self._alternative_tool_discovery(server_url, server_name)
        
        except Exception as e:
            self.logger.error(f"Error discovering tools from {server_url}: {e}")
        
        return discovered_tools
    
    def _parse_openapi_schema(self, 
                             openapi_schema: Dict[str, Any], 
                             server_url: str, 
                             server_name: str) -> List[ToolMetadata]:
        """
        Parse OpenAPI schema to extract tool metadata.
        
        Args:
            openapi_schema: OpenAPI schema dictionary
            server_url: URL of the MCP server
            server_name: Name of the MCP server
            
        Returns:
            List of tool metadata extracted from schema
        """
        tools = []
        
        try:
            paths = openapi_schema.get('paths', {})
            
            for path, path_info in paths.items():
                for method, operation in path_info.items():
                    if method.lower() not in ['get', 'post']:
                        continue
                    
                    # Extract tool information from operation
                    operation_id = operation.get('operationId', f"{method}_{path.replace('/', '_')}")
                    summary = operation.get('summary', '')
                    description = operation.get('description', summary)
                    
                    # Skip health check and other non-tool endpoints
                    if any(keyword in path.lower() for keyword in ['health', 'status', 'ping', 'docs']):
                        continue
                    
                    # Create tool metadata
                    tool_id = f"{server_name}_{operation_id}".lower().replace(' ', '_')
                    
                    # Determine tool type based on path and operation
                    tool_type = self._determine_tool_type(path, operation)
                    
                    # Extract capabilities
                    capabilities = self._extract_capabilities_from_operation(operation, path)
                    
                    # Extract schemas
                    input_schema = self._extract_input_schema(operation)
                    output_schema = self._extract_output_schema(operation)
                    
                    # Create performance characteristics
                    performance_chars = PerformanceCharacteristics(
                        average_response_time_ms=2000.0,  # Default estimate
                        success_rate=0.95,  # Default estimate
                        throughput_requests_per_minute=60  # Default estimate
                    )
                    
                    tool_metadata = ToolMetadata(
                        id=tool_id,
                        name=summary or operation_id,
                        description=description,
                        tool_type=tool_type,
                        capabilities=capabilities,
                        mcp_server_url=server_url,
                        mcp_tool_name=operation_id,
                        input_schema=input_schema,
                        output_schema=output_schema,
                        performance_characteristics=performance_chars,
                        health_check_endpoint=f"{server_url}/health",
                        category="mcp_discovered",
                        tags={server_name, "mcp", "auto_discovered"}
                    )
                    
                    tools.append(tool_metadata)
        
        except Exception as e:
            self.logger.error(f"Error parsing OpenAPI schema: {e}")
        
        return tools
    
    def _determine_tool_type(self, path: str, operation: Dict[str, Any]) -> ToolType:
        """Determine tool type based on path and operation details."""
        path_lower = path.lower()
        operation_id = operation.get('operationId', '').lower()
        summary = operation.get('summary', '').lower()
        
        # Check for restaurant-related tools
        if any(keyword in path_lower for keyword in ['restaurant', 'search']):
            if any(keyword in path_lower + operation_id + summary for keyword in ['recommend', 'reason', 'sentiment']):
                return ToolType.RESTAURANT_REASONING
            else:
                return ToolType.RESTAURANT_SEARCH
        
        # Check for sentiment analysis
        if any(keyword in path_lower + operation_id + summary for keyword in ['sentiment', 'analyze']):
            return ToolType.SENTIMENT_ANALYSIS
        
        return ToolType.GENERIC_MCP
    
    def _extract_capabilities_from_operation(self, 
                                           operation: Dict[str, Any], 
                                           path: str) -> List[ToolCapability]:
        """Extract capabilities from OpenAPI operation."""
        capabilities = []
        
        operation_id = operation.get('operationId', '')
        summary = operation.get('summary', '')
        description = operation.get('description', '')
        
        # Extract parameters
        parameters = operation.get('parameters', [])
        request_body = operation.get('requestBody', {})
        
        required_params = []
        optional_params = []
        
        # Process parameters
        for param in parameters:
            param_name = param.get('name', '')
            is_required = param.get('required', False)
            
            if is_required:
                required_params.append(param_name)
            else:
                optional_params.append(param_name)
        
        # Process request body schema
        if request_body:
            content = request_body.get('content', {})
            for content_type, content_info in content.items():
                schema = content_info.get('schema', {})
                properties = schema.get('properties', {})
                required = schema.get('required', [])
                
                for prop_name in properties.keys():
                    if prop_name in required:
                        required_params.append(prop_name)
                    else:
                        optional_params.append(prop_name)
        
        # Create capability
        capability_name = operation_id or path.strip('/').replace('/', '_')
        
        capability = ToolCapability(
            name=capability_name,
            description=description or summary or f"Capability for {capability_name}",
            required_parameters=required_params,
            optional_parameters=optional_params,
            output_format="json",
            use_cases=[summary] if summary else []
        )
        
        capabilities.append(capability)
        return capabilities
    
    def _extract_input_schema(self, operation: Dict[str, Any]) -> Dict[str, Any]:
        """Extract input schema from OpenAPI operation."""
        input_schema = {}
        
        # Extract from parameters
        parameters = operation.get('parameters', [])
        if parameters:
            input_schema['parameters'] = parameters
        
        # Extract from request body
        request_body = operation.get('requestBody', {})
        if request_body:
            input_schema['requestBody'] = request_body
        
        return input_schema
    
    def _extract_output_schema(self, operation: Dict[str, Any]) -> Dict[str, Any]:
        """Extract output schema from OpenAPI operation."""
        responses = operation.get('responses', {})
        
        # Look for successful response schemas
        for status_code in ['200', '201', '202']:
            if status_code in responses:
                response_info = responses[status_code]
                content = response_info.get('content', {})
                
                for content_type, content_info in content.items():
                    schema = content_info.get('schema', {})
                    if schema:
                        return {
                            'status_code': status_code,
                            'content_type': content_type,
                            'schema': schema
                        }
        
        return {}
    
    async def _alternative_tool_discovery(self, 
                                        server_url: str, 
                                        server_name: str) -> List[ToolMetadata]:
        """
        Alternative tool discovery when OpenAPI schema is not available.
        
        Args:
            server_url: URL of the MCP server
            server_name: Name of the MCP server
            
        Returns:
            List of discovered tool metadata
        """
        tools = []
        
        try:
            # Try common MCP endpoints
            common_endpoints = [
                '/tools',
                '/capabilities',
                '/mcp/tools'
            ]
            
            for endpoint in common_endpoints:
                try:
                    response = requests.get(f"{server_url.rstrip('/')}{endpoint}", timeout=5)
                    if response.status_code == 200:
                        data = response.json()
                        
                        # Parse tool information from response
                        if isinstance(data, list):
                            for tool_info in data:
                                tool_metadata = self._create_tool_from_info(tool_info, server_url, server_name)
                                if tool_metadata:
                                    tools.append(tool_metadata)
                        elif isinstance(data, dict) and 'tools' in data:
                            for tool_info in data['tools']:
                                tool_metadata = self._create_tool_from_info(tool_info, server_url, server_name)
                                if tool_metadata:
                                    tools.append(tool_metadata)
                        
                        break  # Found tools, stop trying other endpoints
                
                except Exception as e:
                    self.logger.debug(f"Failed to fetch from {endpoint}: {e}")
                    continue
        
        except Exception as e:
            self.logger.error(f"Alternative discovery failed for {server_url}: {e}")
        
        return tools
    
    def _create_tool_from_info(self, 
                              tool_info: Dict[str, Any], 
                              server_url: str, 
                              server_name: str) -> Optional[ToolMetadata]:
        """Create tool metadata from tool information dictionary."""
        try:
            tool_name = tool_info.get('name', 'unknown_tool')
            tool_id = f"{server_name}_{tool_name}".lower().replace(' ', '_')
            
            description = tool_info.get('description', f"Tool from {server_name}")
            
            # Create basic capability
            capabilities = [
                ToolCapability(
                    name=tool_name,
                    description=description,
                    required_parameters=tool_info.get('required_parameters', []),
                    optional_parameters=tool_info.get('optional_parameters', [])
                )
            ]
            
            return ToolMetadata(
                id=tool_id,
                name=tool_name,
                description=description,
                tool_type=ToolType.GENERIC_MCP,
                capabilities=capabilities,
                mcp_server_url=server_url,
                mcp_tool_name=tool_name,
                category="mcp_discovered",
                tags={server_name, "mcp", "auto_discovered"}
            )
        
        except Exception as e:
            self.logger.error(f"Failed to create tool metadata from info: {e}")
            return None
    
    def register_tool_from_config(self, config: Dict[str, Any]) -> Optional[str]:
        """
        Register a tool from configuration dictionary.
        
        Args:
            config: Tool configuration dictionary
            
        Returns:
            Tool ID if successful, None otherwise
        """
        try:
            # Extract basic information
            tool_id = config['id']
            name = config['name']
            description = config.get('description', '')
            tool_type_str = config.get('type', 'generic_mcp')
            
            # Convert tool type
            try:
                tool_type = ToolType(tool_type_str)
            except ValueError:
                tool_type = ToolType.GENERIC_MCP
            
            # Extract capabilities
            capabilities = []
            capabilities_config = config.get('capabilities', [])
            
            for cap_config in capabilities_config:
                capability = ToolCapability(
                    name=cap_config['name'],
                    description=cap_config.get('description', ''),
                    required_parameters=cap_config.get('required_parameters', []),
                    optional_parameters=cap_config.get('optional_parameters', []),
                    output_format=cap_config.get('output_format', 'json'),
                    use_cases=cap_config.get('use_cases', [])
                )
                capabilities.append(capability)
            
            # Extract performance characteristics
            perf_config = config.get('performance', {})
            performance_chars = PerformanceCharacteristics(
                average_response_time_ms=perf_config.get('average_response_time_ms', 2000.0),
                success_rate=perf_config.get('success_rate', 0.95),
                throughput_requests_per_minute=perf_config.get('throughput_requests_per_minute', 60)
            )
            
            # Create tool metadata
            tool_metadata = ToolMetadata(
                id=tool_id,
                name=name,
                description=description,
                tool_type=tool_type,
                capabilities=capabilities,
                version=config.get('version', '1.0.0'),
                mcp_server_url=config.get('mcp_server_url'),
                mcp_tool_name=config.get('mcp_tool_name'),
                input_schema=config.get('input_schema', {}),
                output_schema=config.get('output_schema', {}),
                performance_characteristics=performance_chars,
                health_check_endpoint=config.get('health_check_endpoint'),
                health_check_interval_seconds=config.get('health_check_interval_seconds', 60),
                category=config.get('category', 'configured'),
                tags=set(config.get('tags', []))
            )
            
            # Register tool
            self.tool_registry.register_tool(tool_metadata)
            
            self.logger.info(f"Registered tool from config: {name} ({tool_id})")
            return tool_id
        
        except Exception as e:
            self.logger.error(f"Failed to register tool from config: {e}")
            return None
    
    def register_tools_from_config_file(self, config_file_path: str) -> List[str]:
        """
        Register tools from a configuration file.
        
        Args:
            config_file_path: Path to configuration file (YAML or JSON)
            
        Returns:
            List of registered tool IDs
        """
        registered_tool_ids = []
        
        try:
            with open(config_file_path, 'r') as f:
                if config_file_path.endswith('.yaml') or config_file_path.endswith('.yml'):
                    config = yaml.safe_load(f)
                else:
                    config = json.load(f)
            
            tools_config = config.get('tools', [])
            
            for tool_config in tools_config:
                tool_id = self.register_tool_from_config(tool_config)
                if tool_id:
                    registered_tool_ids.append(tool_id)
            
            self.logger.info(f"Registered {len(registered_tool_ids)} tools from config file: {config_file_path}")
        
        except Exception as e:
            self.logger.error(f"Failed to register tools from config file {config_file_path}: {e}")
        
        return registered_tool_ids
    
    async def perform_initial_health_checks(self) -> Dict[str, ToolHealthStatus]:
        """
        Perform initial health checks on all registered tools.
        
        Returns:
            Dictionary of tool_id -> health status
        """
        self.logger.info("Performing initial health checks on registered tools")
        
        health_results = await self.tool_registry.perform_health_checks()
        
        status_summary = {}
        for tool_id, health_record in health_results.items():
            status_summary[tool_id] = health_record.status
        
        self.logger.info(f"Initial health checks completed. Results: {status_summary}")
        return status_summary
    
    def get_registration_summary(self) -> Dict[str, Any]:
        """Get summary of tool registration status."""
        registry_stats = self.tool_registry.get_registry_statistics()
        
        return {
            'total_registered_tools': registry_stats['total_tools'],
            'tools_with_instances': registry_stats['tools_with_instances'],
            'tools_by_type': registry_stats['tools_by_type'],
            'tools_by_health_status': registry_stats['tools_by_health_status'],
            'capabilities_available': registry_stats['total_capabilities'],
            'registration_timestamp': datetime.utcnow().isoformat()
        }