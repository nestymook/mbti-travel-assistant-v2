"""
Test configuration for enhanced MCP status check tests.
"""

import sys
import os

# Add the parent directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
import asyncio


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_aiohttp_session():
    """Create a mock aiohttp session for testing."""
    from unittest.mock import AsyncMock
    return AsyncMock()