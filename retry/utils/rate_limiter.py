"""
Rate limiting utilities for the retry package.

This module provides rate limiting functionality for the retry package,
including global and per-domain rate limiting.
"""

import time
import asyncio
from typing import Dict, Optional, Any, List, Set, Union
import re
from urllib.parse import urlparse

from retry.utils.logger import get_logger
from retry.utils.exceptions import RateLimitError

logger = get_logger(__name__)


class RateLimiter:
    """
    Rate limiter for controlling request frequency.
    
    This class provides rate limiting functionality with support for
    global rate limiting and per-domain rate limiting.
    """
    
    def __init__(self, 
                 requests_per_second: float = 1.0,
                 domain_rules: Optional[Dict[str, float]] = None,
                 max_domains: int = 100):
        """
        Initialize a RateLimiter.
        
        Args:
            requests_per_second: Default requests per second (global limit)
            domain_rules: Domain-specific rules (domain -> requests per second)
            max_domains: Maximum number of domains to track
        """
        self.global_limit = requests_per_second
        self.domain_rules = domain_rules or {}
        self.max_domains = max_domains
        
        # Last request timestamp (global)
        self.last_request_time: float = 0.0
        
        # Last request timestamp per domain
        self.domain_timestamps: Dict[str, float] = {}
        
        # List of recently accessed domains (for LRU caching)
        self.recent_domains: List[str] = []
        
        logger.debug(f"Initialized RateLimiter with global limit: {requests_per_second} rps")
    
    def extract_domain(self, url: str) -> str:
        """
        Extract domain from URL.
        
        Args:
            url: URL to extract domain from
            
        Returns:
            Domain name
        """
        try:
            parsed = urlparse(url)
            domain = parsed.netloc or parsed.path
            
            # Remove port number if present
            domain = domain.split(':')[0]
            
            # Normalize domain
            domain = domain.lower()
            
            return domain
        except Exception as e:
            logger.warning(f"Error extracting domain from URL {url}: {e}")
            # Return the URL as-is if parsing fails
            return url
    
    def get_domain_limit(self, domain: str) -> float:
        """
        Get rate limit for a domain.
        
        Args:
            domain: Domain name
            
        Returns:
            Requests per second limit for the domain
        """
        # Check for exact domain match
        if domain in self.domain_rules:
            return self.domain_rules[domain]
        
        # Check for wildcard matches
        for pattern, limit in self.domain_rules.items():
            if pattern.startswith('*.') and domain.endswith(pattern[1:]):
                return limit
            elif pattern.startswith('*') and pattern.endswith('*') and pattern[1:-1] in domain:
                return limit
            elif pattern.startswith('*') and domain.endswith(pattern[1:]):
                return limit
            elif pattern.endswith('*') and domain.startswith(pattern[:-1]):
                return limit
        
        # Default to global limit
        return self.global_limit
    
    def update_domain_tracking(self, domain: str) -> None:
        """
        Update domain tracking for LRU caching.
        
        Args:
            domain: Domain name to track
        """
        # Remove domain from list if already present
        if domain in self.recent_domains:
            self.recent_domains.remove(domain)
        
        # Add domain to front of list
        self.recent_domains.insert(0, domain)
        
        # Remove oldest domain if list is too long
        if len(self.recent_domains) > self.max_domains:
            old_domain = self.recent_domains.pop()
            if old_domain in self.domain_timestamps:
                del self.domain_timestamps[old_domain]
    
    def add_domain_rule(self, domain: str, requests_per_second: float) -> None:
        """
        Add or update a domain rule.
        
        Args:
            domain: Domain pattern (can include wildcards)
            requests_per_second: Requests per second limit
        """
        self.domain_rules[domain] = requests_per_second
        logger.debug(f"Added domain rule: {domain} -> {requests_per_second} rps")
    
    def remove_domain_rule(self, domain: str) -> bool:
        """
        Remove a domain rule.
        
        Args:
            domain: Domain pattern to remove
            
        Returns:
            True if the rule was removed, False if not found
        """
        if domain in self.domain_rules:
            del self.domain_rules[domain]
            logger.debug(f"Removed domain rule: {domain}")
            return True
        return False
    
    def clear_domain_rules(self) -> None:
        """
        Clear all domain rules.
        """
        self.domain_rules = {}
        logger.debug("Cleared all domain rules")
    
    def set_global_limit(self, requests_per_second: float) -> None:
        """
        Set global rate limit.
        
        Args:
            requests_per_second: Requests per second limit
        """
        self.global_limit = requests_per_second
        logger.debug(f"Set global rate limit: {requests_per_second} rps")
    
    def get_wait_time(self, url: str) -> float:
        """
        Get wait time for a URL.
        
        Args:
            url: URL to check
            
        Returns:
            Time to wait in seconds
        """
        now = time.time()
        domain = self.extract_domain(url)
        
        # Get domain limit
        domain_limit = self.get_domain_limit(domain)
        
        # Calculate delay based on domain limit
        domain_delay = 0.0
        if domain in self.domain_timestamps:
            elapsed = now - self.domain_timestamps[domain]
            expected_interval = 1.0 / domain_limit
            domain_delay = max(0.0, expected_interval - elapsed)
        
        # Calculate delay based on global limit
        global_delay = 0.0
        if self.last_request_time > 0:
            elapsed = now - self.last_request_time
            expected_interval = 1.0 / self.global_limit
            global_delay = max(0.0, expected_interval - elapsed)
        
        # Return the larger of the two delays
        return max(domain_delay, global_delay)
    
    def update_timestamps(self, url: str) -> None:
        """
        Update timestamps after a request.
        
        Args:
            url: URL that was requested
        """
        now = time.time()
        domain = self.extract_domain(url)
        
        # Update global timestamp
        self.last_request_time = now
        
        # Update domain timestamp
        self.domain_timestamps[domain] = now
        
        # Update domain tracking
        self.update_domain_tracking(domain)
    
    async def wait(self, url: str) -> None:
        """
        Wait for rate limit.
        
        Args:
            url: URL to wait for
        """
        wait_time = self.get_wait_time(url)
        
        if wait_time > 0:
            logger.debug(f"Rate limiting: waiting {wait_time:.2f}s for {url}")
            await asyncio.sleep(wait_time)
        
        # Update timestamps after waiting
        self.update_timestamps(url)
    
    def wait_sync(self, url: str) -> None:
        """
        Wait for rate limit synchronously.
        
        Args:
            url: URL to wait for
        """
        wait_time = self.get_wait_time(url)
        
        if wait_time > 0:
            logger.debug(f"Rate limiting: waiting {wait_time:.2f}s for {url}")
            time.sleep(wait_time)
        
        # Update timestamps after waiting
        self.update_timestamps(url)
    
    async def with_rate_limit(self, url: str, func, *args, **kwargs):
        """
        Execute a function with rate limiting.
        
        Args:
            url: URL to rate limit
            func: Async function to execute
            *args: Arguments to pass to the function
            **kwargs: Keyword arguments to pass to the function
            
        Returns:
            Result of the function
            
        Raises:
            RateLimitError: If rate limit is exceeded and retries are exhausted
        """
        # Wait for rate limit
        await self.wait(url)
        
        try:
            # Execute function
            return await func(*args, **kwargs)
        except Exception as e:
            # Check if it's a rate limit error (usually HTTP 429)
            if getattr(e, 'status', 0) == 429 or '429' in str(e):
                retry_after = None
                
                # Try to extract Retry-After header
                if hasattr(e, 'headers') and e.headers:
                    retry_after = e.headers.get('Retry-After')
                    if retry_after and retry_after.isdigit():
                        retry_after = int(retry_after)
                
                # Add temporary rate limit rule
                if retry_after and retry_after > 0:
                    previous_limit = self.get_domain_limit(self.extract_domain(url))
                    new_limit = 1.0 / (retry_after * 2)  # More conservative than the server requested
                    
                    if new_limit < previous_limit:
                        self.add_domain_rule(self.extract_domain(url), new_limit)
                        logger.warning(f"Temporarily reducing rate limit for {self.extract_domain(url)} to {new_limit} rps")
                
                # Raise rate limit error
                raise RateLimitError(
                    f"Rate limit exceeded for {url}",
                    retry_after=retry_after
                ) from e
            
            # Re-raise other exceptions
            raise
    
    def with_rate_limit_sync(self, url: str, func, *args, **kwargs):
        """
        Execute a function with rate limiting synchronously.
        
        Args:
            url: URL to rate limit
            func: Function to execute
            *args: Arguments to pass to the function
            **kwargs: Keyword arguments to pass to the function
            
        Returns:
            Result of the function
            
        Raises:
            RateLimitError: If rate limit is exceeded and retries are exhausted
        """
        # Wait for rate limit
        self.wait_sync(url)
        
        try:
            # Execute function
            return func(*args, **kwargs)
        except Exception as e:
            # Check if it's a rate limit error (usually HTTP 429)
            if getattr(e, 'status_code', 0) == 429 or '429' in str(e):
                retry_after = None
                
                # Try to extract Retry-After header
                if hasattr(e, 'headers') and e.headers:
                    retry_after = e.headers.get('Retry-After')
                    if retry_after and retry_after.isdigit():
                        retry_after = int(retry_after)
                
                # Add temporary rate limit rule
                if retry_after and retry_after > 0:
                    previous_limit = self.get_domain_limit(self.extract_domain(url))
                    new_limit = 1.0 / (retry_after * 2)  # More conservative than the server requested
                    
                    if new_limit < previous_limit:
                        self.add_domain_rule(self.extract_domain(url), new_limit)
                        logger.warning(f"Temporarily reducing rate limit for {self.extract_domain(url)} to {new_limit} rps")
                
                # Raise rate limit error
                raise RateLimitError(
                    f"Rate limit exceeded for {url}",
                    retry_after=retry_after
                ) from e
            
            # Re-raise other exceptions
            raise
