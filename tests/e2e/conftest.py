"""
Shared fixtures for end-to-end tests.

This module provides fixtures for testing complete workflows
with minimal mocking.
"""

import pytest
from pathlib import Path
from typing import List, Dict, Any


@pytest.fixture
def integration_logger(tmp_path: Path):
    """
    Provide a logger configured for e2e testing.

    Args:
        tmp_path: pytest temporary directory fixture

    Returns:
        Logger instance configured with file and console output
    """
    from src.utils.logging import setup_logging

    log_file = tmp_path / "e2e_test.log"
    logger = setup_logging(
        log_level='DEBUG',
        log_file=str(log_file),
        test_mode=True
    )
    return logger


@pytest.fixture
def e2e_env_file(tmp_path: Path) -> Path:
    """
    Create a complete .env file for E2E testing.

    Args:
        tmp_path: pytest temporary directory fixture

    Returns:
        Path to .env file configured for E2E testing
    """
    # TODO: Create .env with test mode enabled and all required fields
    # Reference: AC-FEAT-000-019
    pass


@pytest.fixture
def sample_batch_data() -> List[Dict[str, Any]]:
    """
    Provide sample batch data with duplicate Place IDs for testing.

    Returns:
        List of place data dicts with ~20% duplicates
    """
    # TODO: Generate realistic batch data with duplicates for cache testing
    # Reference: AC-FEAT-000-021
    pass


@pytest.fixture
def e2e_test_mode_config():
    """
    Provide configuration for test mode operation.

    Returns:
        Configuration dict with test mode enabled
    """
    # TODO: Return config with test mode, dry-run, debug logging enabled
    # Reference: AC-FEAT-000-019
    pass
