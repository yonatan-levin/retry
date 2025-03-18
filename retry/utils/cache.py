"""
Caching utilities for the retry package.

This module provides caching functionality for the retry package,
including in-memory, file-based, and Redis-based caching.
"""

import os
import time
import json
import pickle
import hashlib
import inspect
from typing import Any, Dict, Optional, Callable, Tuple, Union, List, TypeVar, cast
from abc import ABC, abstractmethod
import threading
from functools import wraps
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

from retry.utils.logger import get_logger

logger = get_logger(__name__)

# Type variable for return type
T = TypeVar('T')


class BaseCache(ABC):
    """
    Abstract base class for cache implementations.
    """
    
    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """
        Get a value from the cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found
        """
        pass
    
    @abstractmethod
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Set a value in the cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (None for no expiration)
        """
        pass
    
    @abstractmethod
    def delete(self, key: str) -> None:
        """
        Delete a value from the cache.
        
        Args:
            key: Cache key
        """
        pass
    
    @abstractmethod
    def clear(self) -> None:
        """
        Clear the cache.
        """
        pass
    
    @abstractmethod
    def get_size(self) -> int:
        """
        Get the size of the cache.
        
        Returns:
            Number of items in the cache
        """
        pass
    
    def contains(self, key: str) -> bool:
        """
        Check if a key exists in the cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if the key exists, False otherwise
        """
        return self.get(key) is not None


class MemoryCache(BaseCache):
    """
    In-memory cache implementation.
    """
    
    def __init__(self, max_size: Optional[int] = None):
        """
        Initialize a MemoryCache.
        
        Args:
            max_size: Maximum number of items to store (None for unlimited)
        """
        self.cache: Dict[str, Tuple[Any, Optional[float]]] = {}
        self.max_size = max_size
        self.lock = threading.RLock()
        logger.debug(f"Initialized MemoryCache with max_size: {max_size}")
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get a value from the cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found or expired
        """
        with self.lock:
            if key not in self.cache:
                return None
            
            value, expiration = self.cache[key]
            
            # Check if expired
            if expiration is not None and time.time() > expiration:
                self.delete(key)
                return None
            
            return value
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Set a value in the cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (None for no expiration)
        """
        with self.lock:
            # Check if we need to evict an item
            if self.max_size is not None and len(self.cache) >= self.max_size and key not in self.cache:
                self._evict_one()
            
            # Calculate expiration time
            expiration = time.time() + ttl if ttl is not None else None
            
            # Store in cache
            self.cache[key] = (value, expiration)
    
    def delete(self, key: str) -> None:
        """
        Delete a value from the cache.
        
        Args:
            key: Cache key
        """
        with self.lock:
            if key in self.cache:
                del self.cache[key]
    
    def clear(self) -> None:
        """
        Clear the cache.
        """
        with self.lock:
            self.cache.clear()
    
    def get_size(self) -> int:
        """
        Get the size of the cache.
        
        Returns:
            Number of items in the cache
        """
        with self.lock:
            return len(self.cache)
    
    def _evict_one(self) -> None:
        """
        Evict one item from the cache.
        """
        # Find the oldest item
        oldest_key = None
        oldest_time = float('inf')
        
        for key, (_, expiration) in self.cache.items():
            if expiration is None:
                # Items with no expiration are considered oldest
                oldest_key = key
                break
            
            if expiration < oldest_time:
                oldest_key = key
                oldest_time = expiration
        
        # Evict the oldest item
        if oldest_key:
            self.delete(oldest_key)


class FileCache(BaseCache):
    """
    File-based cache implementation.
    """
    
    def __init__(self, cache_dir: str):
        """
        Initialize a FileCache.
        
        Args:
            cache_dir: Directory to store cache files
        """
        self.cache_dir = cache_dir
        
        # Create cache directory if it doesn't exist
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
        
        logger.debug(f"Initialized FileCache with cache_dir: {cache_dir}")
    
    def _get_cache_path(self, key: str) -> str:
        """
        Get the path to a cache file.
        
        Args:
            key: Cache key
            
        Returns:
            Path to the cache file
        """
        # Hash the key to get a valid filename
        hashed_key = hashlib.md5(key.encode()).hexdigest()
        return os.path.join(self.cache_dir, f"{hashed_key}.cache")
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get a value from the cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found or expired
        """
        cache_path = self._get_cache_path(key)
        
        if not os.path.exists(cache_path):
            return None
        
        try:
            with open(cache_path, 'rb') as f:
                data = pickle.load(f)
            
            # Check if expired
            if 'expiration' in data and data['expiration'] is not None and time.time() > data['expiration']:
                self.delete(key)
                return None
            
            return data['value']
            
        except (pickle.PickleError, IOError) as e:
            logger.error(f"Error reading cache file: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Set a value in the cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (None for no expiration)
        """
        cache_path = self._get_cache_path(key)
        
        # Calculate expiration time
        expiration = time.time() + ttl if ttl is not None else None
        
        # Store data
        data = {
            'key': key,
            'value': value,
            'expiration': expiration,
        }
        
        try:
            with open(cache_path, 'wb') as f:
                pickle.dump(data, f)
        except (pickle.PickleError, IOError) as e:
            logger.error(f"Error writing cache file: {e}")
    
    def delete(self, key: str) -> None:
        """
        Delete a value from the cache.
        
        Args:
            key: Cache key
        """
        cache_path = self._get_cache_path(key)
        
        if os.path.exists(cache_path):
            try:
                os.remove(cache_path)
            except IOError as e:
                logger.error(f"Error deleting cache file: {e}")
    
    def clear(self) -> None:
        """
        Clear the cache.
        """
        for filename in os.listdir(self.cache_dir):
            if filename.endswith('.cache'):
                try:
                    os.remove(os.path.join(self.cache_dir, filename))
                except IOError as e:
                    logger.error(f"Error deleting cache file: {e}")
    
    def get_size(self) -> int:
        """
        Get the size of the cache.
        
        Returns:
            Number of items in the cache
        """
        return len([f for f in os.listdir(self.cache_dir) if f.endswith('.cache')])


class RedisCache(BaseCache):
    """
    Redis-based cache implementation.
    
    Note:
        Requires the Redis package to be installed.
    """
    
    def __init__(self, 
                host: str = 'localhost', 
                port: int = 6379, 
                db: int = 0, 
                password: Optional[str] = None,
                prefix: str = 'retry:cache:'):
        """
        Initialize a RedisCache.
        
        Args:
            host: Redis host
            port: Redis port
            db: Redis database number
            password: Redis password
            prefix: Key prefix for Redis keys
        
        Raises:
            ImportError: If the Redis package is not installed
        """
        if not REDIS_AVAILABLE:
            raise ImportError("Redis package is required for RedisCache")
        
        self.prefix = prefix
        self.redis_client = redis.Redis(host=host, port=port, db=db, password=password)
        
        logger.debug(f"Initialized RedisCache with host: {host}, port: {port}, db: {db}")
    
    def _get_prefixed_key(self, key: str) -> str:
        """
        Get a key with the prefix.
        
        Args:
            key: Cache key
            
        Returns:
            Prefixed key
        """
        return f"{self.prefix}{key}"
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get a value from the cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found
        """
        prefixed_key = self._get_prefixed_key(key)
        
        try:
            value = self.redis_client.get(prefixed_key)
            
            if value is None:
                return None
            
            return pickle.loads(value)
            
        except (redis.RedisError, pickle.PickleError) as e:
            logger.error(f"Error getting value from Redis: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Set a value in the cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (None for no expiration)
        """
        prefixed_key = self._get_prefixed_key(key)
        
        try:
            # Serialize value
            serialized_value = pickle.dumps(value)
            
            # Store in Redis
            if ttl is not None:
                self.redis_client.setex(prefixed_key, ttl, serialized_value)
            else:
                self.redis_client.set(prefixed_key, serialized_value)
            
        except (redis.RedisError, pickle.PickleError) as e:
            logger.error(f"Error setting value in Redis: {e}")
    
    def delete(self, key: str) -> None:
        """
        Delete a value from the cache.
        
        Args:
            key: Cache key
        """
        prefixed_key = self._get_prefixed_key(key)
        
        try:
            self.redis_client.delete(prefixed_key)
        except redis.RedisError as e:
            logger.error(f"Error deleting value from Redis: {e}")
    
    def clear(self) -> None:
        """
        Clear the cache.
        """
        try:
            # Find all keys with the prefix
            keys = self.redis_client.keys(f"{self.prefix}*")
            
            if keys:
                self.redis_client.delete(*keys)
                
        except redis.RedisError as e:
            logger.error(f"Error clearing Redis cache: {e}")
    
    def get_size(self) -> int:
        """
        Get the size of the cache.
        
        Returns:
            Number of items in the cache
        """
        try:
            keys = self.redis_client.keys(f"{self.prefix}*")
            return len(keys)
        except redis.RedisError as e:
            logger.error(f"Error getting cache size from Redis: {e}")
            return 0


class SimpleCache(MemoryCache):
    """
    Simple in-memory cache for backward compatibility.
    """
    pass


def cached(cache: BaseCache, ttl: Optional[int] = None, key_fn: Optional[Callable[..., str]] = None) -> Callable:
    """
    Decorator for caching function results.
    
    Args:
        cache: Cache instance to use
        ttl: Time to live in seconds (None for no expiration)
        key_fn: Function to generate cache key from arguments
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            # Generate cache key
            if key_fn:
                key = key_fn(*args, **kwargs)
            else:
                # Default key generation based on function name and arguments
                key_parts = [func.__module__, func.__name__]
                
                # Add positional arguments
                for arg in args:
                    key_parts.append(str(arg))
                
                # Add keyword arguments
                for k, v in sorted(kwargs.items()):
                    key_parts.append(f"{k}={v}")
                
                key = ":".join(key_parts)
            
            # Check cache
            cached_value = cache.get(key)
            if cached_value is not None:
                logger.debug(f"Cache hit for {func.__name__} with key {key}")
                return cast(T, cached_value)
            
            # Call function
            logger.debug(f"Cache miss for {func.__name__} with key {key}")
            result = func(*args, **kwargs)
            
            # Store in cache
            cache.set(key, result, ttl)
            
            return result
        
        return wrapper
    
    return decorator
