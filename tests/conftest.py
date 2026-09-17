"""
Test configuration and fixtures for the wyrdbound-rng package tests.
"""

from pathlib import Path

import pytest

from wyrdbound_rng.name_list_resolver import get_data_directory

# The packaged data directory is the only source of built-in name lists.
DATA_DIR = Path(get_data_directory())


@pytest.fixture
def fantasy_names_yaml_path():
    """Path to the fantasy names YAML file."""
    return str(DATA_DIR / "generic-fantasy.yaml")


@pytest.fixture
def sengoku_names_yaml_path():
    """Path to the Sengoku names YAML file."""
    return str(DATA_DIR / "japanese-sengoku.yaml")
