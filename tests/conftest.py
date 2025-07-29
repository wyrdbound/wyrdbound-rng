"""
Test configuration and fixtures for the wyrdbound-rng package tests.
"""

from pathlib import Path

import pytest

# Get the test data directory
TEST_DIR = Path(__file__).parent
ROOT_DIR = TEST_DIR.parent
ROOT_DATA_DIR = ROOT_DIR / "data"


@pytest.fixture
def fantasy_names_yaml_path():
    """Path to the fantasy names YAML file."""
    return str(ROOT_DATA_DIR / "generic-fantasy.yaml")


@pytest.fixture
def sengoku_names_yaml_path():
    """Path to the Sengoku names YAML file."""
    return str(ROOT_DATA_DIR / "japanese-sengoku.yaml")
