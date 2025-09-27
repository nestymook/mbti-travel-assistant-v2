#!/usr/bin/env python3
"""
End-to-End Authentication Tests for Restaurant Search MCP

This module provides comprehensive end-to-end authentication tests that validate
the complete authentication flow from Cognito login to MCP tool execution,
including JWT token propagation through AgentCore Runtime to MCP server.

Requirements: 16.1, 16.2, 16.4, 17.1, 18.1
"""

import asyncio
import json
import os
import sys
import time
import pytest
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List, Tuple
from unittest.mock import Mock, patch, AsyncMock
import requests
import subprocess

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.auth_service import (
    CognitoAuthenticator,
    TokenValidator,
    AuthenticationError,
    AuthenticationTokens,
    JWTClaims,
    UserContext
)
from services.auth_middleware import (
    AuthenticationMiddleware,
    AuthenticationConfig,
    AuthenticationHelper
)

try:
    from mcp import ClientSession
    from mcp.client.streamable_http import streamablehttp_client
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    ClientSession = None
    streamablehttp_client = None

try:
    from bedrock_agentcore_starter_toolkit import Runtime
    AGENTCORE_AVAILABLE = True
except ImportError:
    AGENTCORE_AVAILABLE = False
    Runtime = None


class E2EAuthenticationTestSuite:
    """Comprehensive end-to-end authentication test suite."""
    
    def __init__(self, config_file: str = "cognito_config.json"):
        """Initialize test suite with configuration.
        
        Args:
            config_file: Path to Cognito configuration file.
        """
        self.config_file = config_file
        self.cognito_config = self._load_cognito_config()
        self.test_results = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'test_suite': 'E2E Authentication Tests',
            'tests': {},
            'summary': {}
        }
        
        # Initialize authentication components
        self.authenticator = CognitoAuthenticator(
            user_pool_id=self.cognito_config['user_pool']['user_pool_id'],
            client_id=self.cognito_config['app_client']['client_id'],
            region=self.cognito_config['region']
        )
        
        self.token_validator = TokenValidator({
            'user_pool_id': self.cognito_config['user_pool']['user_pool_id'],
            'client_id': self.cognito_config['app_client']['client_id'],
            'region': self.cognito_config['region'],
            'discovery_url': self.cognito_config['discovery_url']
        })
        
        # Test user credentials
        self.test_username = self.cognito_config.get('test_user', {}).get('email', 'test@example.com')
        self.test_password = "TempPass123!"  # Default from setup_cognito.py
        
        # AgentCore configuration
        self.agent_arn = None
        self.agentcore_runtime = None
        
    def _load_cognito_config(self) -> Dict[str, Any]:
        """Load Cognito configuration from file.
        
        Returns:
            Cognito configuration dictionary.
            
        Raises:
            FileNotFoundError: If config file doesn't exist.
            ValueError: If config is invalid.
        """
        try:
            if not os.path.exists(self.config_file):
                raise FileNotFoundError(
                    f"Cognito configuration file not found: {self.config_file}. "
 