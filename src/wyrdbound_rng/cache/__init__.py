"""
Cache module for storing and retrieving computed probabilities.
"""

from .cache_adapter import CacheAdapter
from .json_cache_adapter import JsonCacheAdapter

__all__ = ['CacheAdapter', 'JsonCacheAdapter']
