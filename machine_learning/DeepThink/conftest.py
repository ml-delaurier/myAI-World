#!/usr/bin/env python3

# Version 1.0.0
# Pytest configuration file for DeepSeekEngineer GUI tests
# Contains shared fixtures and configuration for all test files

import pytest
import os
from pathlib import Path

def pytest_configure(config):
    """
    Custom pytest configuration
    """
    # Register custom markers
    config.addinivalue_line(
        "markers", "gui: mark test as requiring GUI environment"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )

@pytest.fixture(scope="session")
def test_data_dir():
    """
    Fixture to provide a temporary directory for test data
    """
    test_dir = Path(__file__).parent / "test_data"
    test_dir.mkdir(exist_ok=True)
    return test_dir

@pytest.fixture(autouse=True)
def setup_test_env():
    """
    Fixture to set up test environment variables
    """
    os.environ["DEEPSEEK_API_KEY"] = "test_key"
    os.environ["TEST_MODE"] = "true"
    yield
    # Clean up
    os.environ.pop("TEST_MODE", None)
