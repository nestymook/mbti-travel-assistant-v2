"""
AgentCore API Request and Response Models

This module provides data models for AgentCore API requests and responses,
ensuring proper parameter mapping and backward compatibility with existing response formats.
"""

import json
import uuid
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Union
from datetime import datetime


@dataclass
class AgentCoreInvocationRequest:
    """
    Request model for AgentCore agent invocation with correct parameter mapping.
    
    This model ensures proper parameter mapping for AgentCore API compatibility
    while maintaining backward compatibility with existing request formats.
    """
    agent_runtime_arn: str
    input_text: str
    qualifier: str = "DEFAULT"
    session_id: Optional[str] = None
    payload_format: str = "json"
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        """Post-initialization validation and setup."""
        # Ensure session ID is at least 33 characters as required by AgentCore
        if self.session_id is None:
            self.session_id = str(uuid.uuid4())
        
        if len(self.session_id) < 33:
            self.session_id = f"{self.session_id}_{'x' * (33 - len(self.session_id))}"
        
        # Initialize metadata if not provided
        if self.metadata is None:
            self.metadata = {}
    
    def to_api_params(self) -> Dict[str, Any]:
        """
        Convert to AgentCore API parameters.
        
        Returns:
            Dictionary with correct AgentCore API parameter names and format
        """
        # Prepare payload in the correct JSON format expected by AgentCore
        payload = json.dumps({
            "input": {"prompt": self.input_text}
        })
        
        params = {
            'agentRuntimeArn': self.agent_runtime_arn,
            'runtimeSessionId': self.session_id,
            'payload': payload,
            'qualifier': self.qualifier
        }
        
        return params
    
    def to_legacy_params(self) -> Dict[str, Any]:
        """
        Convert to legacy API parameters for backward compatibility.
        
        Returns:
            Dictionary with legacy parameter names
        """
        return {
            'agentId': self.agent_runtime_arn.split('/')[-1] if '/' in self.agent_runtime_arn else self.agent_runtime_arn,
            'agentAliasId': 'TSTALIASID',
            'sessionId': self.session_id,
            'inputText': self.input_text
        }
    
    @classmethod
    def from_legacy_request(
        cls,
        agent_arn: str,
        input_text: str,
        session_id: Optional[str] = None,
        **kwargs
    ) -> 'AgentCoreInvocationRequest':
        """
        Create request from legacy parameters for backward compatibility.
        
        Args:
            agent_arn: Agent ARN (can be legacy format)
            input_text: Input text for the agent
            session_id: Optional session ID
            **kwargs: Additional legacy parameters
            
        Returns:
            AgentCoreInvocationRequest instance
        """
        return cls(
            agent_runtime_arn=agent_arn,
            input_text=input_text,
            session_id=session_id,
            metadata=kwargs
        )
    
    def validate(self) -> bool:
        """
        Validate the request parameters.
        
        Returns:
            True if valid, raises ValueError if invalid
        """
        if not self.agent_runtime_arn:
            raise ValueError("agent_runtime_arn is required")
        
        if not self.input_text:
            raise ValueError("input_text is required")
        
        if len(self.session_id) < 33:
            raise ValueError("session_id must be at least 33 characters")
        
        return True


@dataclass
class AgentCoreInvocationResponse:
    """
    Response model for AgentCore agent invocation with proper response parsing.
    
    This model ensures proper parsing of AgentCore responses while maintaining
    backward compatibility with existing response formats.
    """
    response_text: str
    session_id: str
    status_code: int
    metadata: Dict[str, Any]
    execution_time_ms: Optional[int] = None
    agent_arn: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    @classmethod
    def from_api_response(
        cls,
        response: Dict[str, Any],
        agent_arn: Optional[str] = None,
        execution_time_ms: Optional[int] = None
    ) -> 'AgentCoreInvocationResponse':
        """
        Parse AgentCore API response into structured format.
        
        Args:
            response: Raw response from AgentCore API
            agent_arn: Optional agent ARN for context
            execution_time_ms: Optional execution time
            
        Returns:
            AgentCoreInvocationResponse instance
        """
        # Handle streaming response body
        response_text = ""
        session_id = ""
        
        try:
            if 'response' in response:
                # AgentCore returns a streaming response body
                response_body = response['response'].read()
                if isinstance(response_body, bytes):
                    response_body = response_body.decode('utf-8')
                
                try:
                    response_data = json.loads(response_body)
                    response_text = cls._extract_response_text(response_data)
                except json.JSONDecodeError:
                    # If not JSON, treat as plain text
                    response_text = response_body
            else:
                # Direct response format
                response_text = cls._extract_response_text(response)
            
            # Extract session ID
            session_id = response.get('sessionId', response.get('runtimeSessionId', ''))
            
            # Extract metadata
            metadata = response.get('ResponseMetadata', {})
            status_code = metadata.get('HTTPStatusCode', 200)
            
            return cls(
                response_text=response_text,
                session_id=session_id,
                status_code=status_code,
                metadata=metadata,
                execution_time_ms=execution_time_ms,
                agent_arn=agent_arn
            )
            
        except Exception as e:
            # Create error response for parsing failures
            return cls(
                response_text="",
                session_id=session_id,
                status_code=500,
                metadata={
                    'parse_error': str(e),
                    'raw_response': str(response)
                },
                execution_time_ms=execution_time_ms,
                agent_arn=agent_arn
            )
    
    @staticmethod
    def _extract_response_text(response_data: Union[Dict, str]) -> str:
        """
        Extract response text from various response formats.
        
        Args:
            response_data: Response data in various formats
            
        Returns:
            Extracted response text
        """
        if isinstance(response_data, str):
            return response_data
        
        if isinstance(response_data, dict):
            # Try different possible keys for response text
            for key in ['output', 'result', 'text', 'response', 'completion']:
                if key in response_data:
                    value = response_data[key]
                    if isinstance(value, str):
                        return value
                    elif isinstance(value, dict):
                        # Nested structure, try to extract text
                        return str(value)
            
            # If no specific key found, convert entire dict to string
            return str(response_data)
        
        return str(response_data)
    
    def to_legacy_format(self) -> Dict[str, Any]:
        """
        Convert to legacy response format for backward compatibility.
        
        Returns:
            Dictionary in legacy response format
        """
        return {
            'completion': self.response_text,
            'sessionId': self.session_id,
            'ResponseMetadata': self.metadata
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary format.
        
        Returns:
            Dictionary representation of the response
        """
        return {
            'response_text': self.response_text,
            'session_id': self.session_id,
            'status_code': self.status_code,
            'metadata': self.metadata,
            'execution_time_ms': self.execution_time_ms,
            'agent_arn': self.agent_arn,
            'timestamp': self.timestamp.isoformat()
        }
    
    def is_successful(self) -> bool:
        """
        Check if the response indicates a successful invocation.
        
        Returns:
            True if successful, False otherwise
        """
        return (
            200 <= self.status_code < 300 and
            self.response_text is not None and
            'parse_error' not in self.metadata
        )
    
    def get_error_details(self) -> Optional[Dict[str, Any]]:
        """
        Get error details if the response indicates an error.
        
        Returns:
            Error details dictionary or None if no error
        """
        if self.is_successful():
            return None
        
        return {
            'status_code': self.status_code,
            'error_message': self.metadata.get('parse_error', 'Unknown error'),
            'raw_response': self.metadata.get('raw_response'),
            'agent_arn': self.agent_arn
        }


@dataclass
class AgentCoreStreamingResponse:
    """
    Response model for AgentCore streaming invocations.
    
    This model handles streaming responses from AgentCore agents.
    """
    chunk_text: str
    session_id: str
    is_final: bool
    chunk_index: int = 0
    metadata: Optional[Dict[str, Any]] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    @classmethod
    def from_stream_chunk(
        cls,
        chunk_data: Dict[str, Any],
        session_id: str,
        chunk_index: int = 0
    ) -> 'AgentCoreStreamingResponse':
        """
        Create streaming response from chunk data.
        
        Args:
            chunk_data: Raw chunk data from stream
            session_id: Session ID
            chunk_index: Index of the chunk in the stream
            
        Returns:
            AgentCoreStreamingResponse instance
        """
        chunk_text = ""
        is_final = False
        metadata = {}
        
        try:
            if 'chunk' in chunk_data:
                chunk = chunk_data['chunk']
                if 'bytes' in chunk:
                    chunk_text = chunk['bytes'].decode('utf-8')
                elif 'text' in chunk:
                    chunk_text = chunk['text']
            
            # Check if this is the final chunk
            is_final = chunk_data.get('final', False) or chunk_data.get('is_final', False)
            
            # Extract metadata
            metadata = chunk_data.get('metadata', {})
            
        except Exception as e:
            metadata['parse_error'] = str(e)
        
        return cls(
            chunk_text=chunk_text,
            session_id=session_id,
            is_final=is_final,
            chunk_index=chunk_index,
            metadata=metadata
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary format.
        
        Returns:
            Dictionary representation of the streaming response
        """
        return {
            'chunk_text': self.chunk_text,
            'session_id': self.session_id,
            'is_final': self.is_final,
            'chunk_index': self.chunk_index,
            'metadata': self.metadata,
            'timestamp': self.timestamp.isoformat()
        }


class AgentCoreAPITransformer:
    """
    Utility class for transforming between different API formats.
    
    This class provides methods to transform data between AgentCore API format,
    legacy formats, and internal application formats while maintaining
    backward compatibility.
    """
    
    @staticmethod
    def transform_request_to_agentcore(
        agent_arn: str,
        input_text: str,
        session_id: Optional[str] = None,
        **kwargs
    ) -> AgentCoreInvocationRequest:
        """
        Transform request parameters to AgentCore format.
        
        Args:
            agent_arn: Agent ARN
            input_text: Input text
            session_id: Optional session ID
            **kwargs: Additional parameters
            
        Returns:
            AgentCoreInvocationRequest instance
        """
        return AgentCoreInvocationRequest(
            agent_runtime_arn=agent_arn,
            input_text=input_text,
            session_id=session_id,
            metadata=kwargs
        )
    
    @staticmethod
    def transform_response_from_agentcore(
        response: Dict[str, Any],
        agent_arn: Optional[str] = None,
        execution_time_ms: Optional[int] = None,
        legacy_format: bool = False
    ) -> Union[AgentCoreInvocationResponse, Dict[str, Any]]:
        """
        Transform AgentCore response to internal format.
        
        Args:
            response: Raw AgentCore response
            agent_arn: Optional agent ARN
            execution_time_ms: Optional execution time
            legacy_format: Whether to return legacy format
            
        Returns:
            AgentCoreInvocationResponse or legacy format dict
        """
        agentcore_response = AgentCoreInvocationResponse.from_api_response(
            response, agent_arn, execution_time_ms
        )
        
        if legacy_format:
            return agentcore_response.to_legacy_format()
        
        return agentcore_response
    
    @staticmethod
    def ensure_backward_compatibility(
        response: AgentCoreInvocationResponse
    ) -> Dict[str, Any]:
        """
        Ensure response maintains backward compatibility with existing code.
        
        Args:
            response: AgentCore response
            
        Returns:
            Dictionary with both new and legacy fields
        """
        return {
            # New format fields
            'response_text': response.response_text,
            'session_id': response.session_id,
            'status_code': response.status_code,
            'metadata': response.metadata,
            'execution_time_ms': response.execution_time_ms,
            'agent_arn': response.agent_arn,
            'timestamp': response.timestamp.isoformat(),
            
            # Legacy format fields for backward compatibility
            'completion': response.response_text,
            'sessionId': response.session_id,
            'output': response.response_text,
            'ResponseMetadata': response.metadata,
            
            # Additional compatibility fields
            'success': response.is_successful(),
            'error_details': response.get_error_details()
        }


# Export main classes
__all__ = [
    'AgentCoreInvocationRequest',
    'AgentCoreInvocationResponse', 
    'AgentCoreStreamingResponse',
    'AgentCoreAPITransformer'
]