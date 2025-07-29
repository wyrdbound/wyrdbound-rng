"""
Utility for resolving name list identifiers to file paths.
"""

import os
from pathlib import Path
from typing import List, Optional


def get_available_name_lists() -> List[str]:
    """
    Get a list of available built-in name lists.
    
    Returns:
        List of name list identifiers (without .yaml extension)
    """
    data_dir = get_data_directory()
    if not data_dir or not os.path.exists(data_dir):
        return []
    
    yaml_files = []
    for file in os.listdir(data_dir):
        if file.endswith('.yaml') or file.endswith('.yml'):
            # Remove extension to get identifier
            identifier = file.rsplit('.', 1)[0]
            yaml_files.append(identifier)
    
    return sorted(yaml_files)


def get_data_directory() -> Optional[str]:
    """
    Get the path to the data directory containing built-in name lists.
    
    Returns:
        Path to data directory, or None if not found
    """
    # First try relative to the package (development mode)
    package_dir = Path(__file__).parent
    root_dir = package_dir.parent.parent  # Go up two levels from src/wyrdbound_rng/
    data_dir = root_dir / "data"
    
    if data_dir.exists():
        return str(data_dir)
    
    # For installed packages, try relative to the package location
    # This would need to be adjusted based on how the package is distributed
    # For now, just return None as fallback
    return None


def resolve_name_list(identifier: str) -> Optional[str]:
    """
    Resolve a name list identifier to a file path.
    
    This function supports:
    1. Built-in name list identifiers (e.g., "generic-fantasy")
    2. Relative file paths (e.g., "./my-names.yaml")
    3. Absolute file paths (e.g., "/path/to/names.yaml")
    
    Args:
        identifier: Name list identifier or file path
        
    Returns:
        Full path to the YAML file, or None if not found
    """
    # Check if it's already a file path that exists
    if os.path.exists(identifier):
        return os.path.abspath(identifier)
    
    # Check if it's a relative path that exists
    if "/" in identifier or "\\" in identifier:
        if os.path.exists(identifier):
            return os.path.abspath(identifier)
        return None
    
    # Try to resolve as built-in name list
    data_dir = get_data_directory()
    if data_dir:
        # Try with .yaml extension first
        yaml_path = os.path.join(data_dir, f"{identifier}.yaml")
        if os.path.exists(yaml_path):
            return yaml_path
        
        # Try with .yml extension
        yml_path = os.path.join(data_dir, f"{identifier}.yml")
        if os.path.exists(yml_path):
            return yml_path
    
    return None


def format_available_lists() -> str:
    """
    Format the available name lists for display in help text.
    
    Returns:
        Formatted string listing available name lists
    """
    lists = get_available_name_lists()
    if not lists:
        return "No built-in name lists found."
    
    return "Available built-in name lists:\n  " + "\n  ".join(lists)
