"""
Abstract base class for cache adapters.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class CacheAdapter(ABC):
    """
    Abstract base class for cache storage adapters.

    This allows for different storage backends (JSON, Redis, Database, etc.)
    while maintaining a consistent interface.
    """

    @abstractmethod
    def get(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached data by key.

        Args:
            cache_key (str): The cache key to look up

        Returns:
            Optional[Dict[str, Any]]: The cached data or None if not found
        """
        pass

    @abstractmethod
    def set(self, cache_key: str, data: Dict[str, Any]) -> None:
        """
        Store data in the cache.

        Args:
            cache_key (str): The cache key to store under
            data (Dict[str, Any]): The data to cache
        """
        pass

    @abstractmethod
    def exists(self, cache_key: str) -> bool:
        """
        Check if a cache key exists.

        Args:
            cache_key (str): The cache key to check

        Returns:
            bool: True if the key exists, False otherwise
        """
        pass

    @abstractmethod
    def clear(self, cache_key: str) -> None:
        """
        Remove a specific cache entry.

        Args:
            cache_key (str): The cache key to remove
        """
        pass
