"""
Shared fixtures for unit tests.

This module provides common fixtures used across unit tests for the shared infrastructure.
"""

import pytest
from pathlib import Path
from typing import Dict, Any


@pytest.fixture
def sample_env_vars() -> Dict[str, str]:
    """
    Provide sample environment variables for configuration testing.

    Returns:
        Dictionary of environment variable names and values
    """
    # TODO: Implement fixture to return sample configuration dict
    # Reference: AC-FEAT-000-001
    pass


@pytest.fixture
def temp_env_file(tmp_path: Path) -> Path:
    """
    Create a temporary .env file for testing.

    Args:
        tmp_path: pytest temporary directory fixture

    Returns:
        Path to temporary .env file
    """
    # TODO: Create and return path to temporary .env file with test data
    # Reference: AC-FEAT-000-001
    pass


@pytest.fixture
def mock_logger():
    """
    Provide a mock logger for testing logging functionality.

    Returns:
        Mock logger instance
    """
    # TODO: Create and return mock logger with capture capabilities
    # Reference: AC-FEAT-000-005
    pass


@pytest.fixture
def sample_places_api_response() -> Dict[str, Any]:
    """
    Provide sample Google Places API response for testing.

    Returns:
        Dictionary representing Places API response
    """
    # TODO: Return realistic Places API response dict
    # Reference: AC-FEAT-000-016
    pass


@pytest.fixture
def sample_notion_schema() -> Dict[str, Any]:
    """
    Provide sample Notion database schema for testing.

    Returns:
        Dictionary representing Notion database schema
    """
    # TODO: Return realistic Notion schema dict
    # Reference: AC-FEAT-000-015
    pass
