"""
JSON-based cache adapter for storing probability data.
"""

import json
import os
from typing import Any, Dict, Optional

from .cache_adapter import CacheAdapter


class JsonCacheAdapter(CacheAdapter):
    """
    JSON file-based cache adapter.

    Stores cache data as JSON files in a specified directory.
    """

    def __init__(self, cache_dir: str = ".rng_cache"):
        """
        Initialize the JSON cache adapter.

        Args:
            cache_dir (str): Directory to store cache files in
        """
        self.cache_dir = cache_dir

        # Create cache directory if it doesn't exist
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)

    def _get_cache_file_path(self, cache_key: str) -> str:
        """
        Get the file path for a cache key.

        Args:
            cache_key (str): The cache key

        Returns:
            str: The file path for the cache entry
        """
        # Sanitize the cache key for filename use
        safe_key = cache_key.replace("/", "_").replace("\\", "_")
        return os.path.join(self.cache_dir, f"{safe_key}.json")

    def get(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached data by key.

        Args:
            cache_key (str): The cache key to look up

        Returns:
            Optional[Dict[str, Any]]: The cached data or None if not found
        """
        cache_file = self._get_cache_file_path(cache_key)

        if not os.path.exists(cache_file):
            return None

        try:
            with open(cache_file, encoding="utf-8") as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError):
            # If file is corrupted or unreadable, treat as cache miss
            return None

    def set(self, cache_key: str, data: Dict[str, Any]) -> None:
        """
        Store data in the cache.

        Args:
            cache_key (str): The cache key to store under
            data (Dict[str, Any]): The data to cache
        """
        cache_file = self._get_cache_file_path(cache_key)

        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except OSError as e:
            # Log the error but don't crash - caching is optional
            print(f"Warning: Failed to write cache file {cache_file}: {e}")

    def exists(self, cache_key: str) -> bool:
        """
        Check if a cache key exists.

        Args:
            cache_key (str): The cache key to check

        Returns:
            bool: True if the key exists, False otherwise
        """
        cache_file = self._get_cache_file_path(cache_key)
        return os.path.exists(cache_file)

    def clear(self, cache_key: str) -> None:
        """
        Remove a specific cache entry.

        Args:
            cache_key (str): The cache key to remove
        """
        cache_file = self._get_cache_file_path(cache_key)

        if os.path.exists(cache_file):
            try:
                os.remove(cache_file)
            except OSError as e:
                print(f"Warning: Failed to remove cache file {cache_file}: {e}")
