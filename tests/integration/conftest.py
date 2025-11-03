"""
Shared fixtures for integration tests.

This module provides fixtures for testing component interactions
and cross-cutting concerns.
"""

import pytest
import json
from pathlib import Path
from typing import Dict, Any


@pytest.fixture
def integration_env_file(tmp_path: Path) -> Path:
    """
    Create a complete .env file for integration testing.

    Args:
        tmp_path: pytest temporary directory fixture

    Returns:
        Path to temporary .env file with all required configuration
    """
    # TODO: Create complete .env file with all required fields
    # Reference: AC-FEAT-000-001
    pass


@pytest.fixture
def integration_logger(tmp_path: Path):
    """
    Provide a logger configured for integration testing.

    Args:
        tmp_path: pytest temporary directory fixture

    Returns:
        Logger instance configured with file and console output
    """
    from src.utils.logging import setup_logging

    log_file = tmp_path / "integration_test.log"
    logger = setup_logging(
        log_level='DEBUG',
        log_file=str(log_file),
        test_mode=True
    )
    return logger


@pytest.fixture
def mock_places_api():
    """
    Provide a mock Google Places API for integration testing.

    Returns:
        Mock API instance with realistic response behavior
    """
    # TODO: Create mock API that simulates success, failures, retries
    # Reference: AC-FEAT-000-010
    pass


@pytest.fixture
def sample_notion_schema() -> Dict[str, Any]:
    """
    Provide sample Notion database schema for testing.

    Returns:
        Dict containing Notion database schema structure
    """
    schema_path = Path(__file__).parent.parent / "fixtures" / "sample_notion_schema.json"
    with open(schema_path, 'r') as f:
        return json.load(f)


@pytest.fixture
def mock_notion_api():
    """
    Provide a mock Notion API for integration testing.

    Returns:
        Mock Notion API instance with schema validation
    """
    # TODO: Create mock Notion API with schema validation
    # Reference: AC-FEAT-000-015
    pass
