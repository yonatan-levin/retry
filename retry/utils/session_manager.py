"""
Session management utilities for the retry package.

This module provides session management functionality for the retry package,
including proxy rotation, connection pooling, and automatic retries.
"""

import time
import random
import logging
from typing import Dict, List, Optional, Any, Union, Callable, Tuple, Awaitable
import asyncio
import aiohttp
from aiohttp import ClientSession, TCPConnector, ClientTimeout
import requests

from retry.utils.logger import get_logger
from retry.utils.exceptions import NetworkError

logger = get_logger(__name__)


class SessionManager:
    """
    Manages HTTP sessions with features like proxy rotation and connection pooling.
    
    This class provides both synchronous and asynchronous HTTP session management
    with support for proxy rotation, connection pooling, and automatic retries.
    """
    
    def __init__(self,
                 proxies: Optional[List[str]] = None,
                 max_connections: int = 10,
                 timeout: int = 30,
                 retry_attempts: int = 3,
                 retry_delay: int = 1,
                 user_agents: Optional[List[str]] = None):
        """
        Initialize a SessionManager.
        
        Args:
            proxies: List of proxy URLs to use (format: 'http://user:pass@host:port')
            max_connections: Maximum number of connections per host
            timeout: Default timeout for requests in seconds
            retry_attempts: Number of retry attempts for failed requests
            retry_delay: Delay between retry attempts in seconds
            user_agents: List of user agent strings to rotate
        """
        self.proxies = proxies or []
        self.max_connections = max_connections
        self.timeout = timeout
        self.retry_attempts = retry_attempts
        self.retry_delay = retry_delay
        
        # Default user agents if none provided
        self.user_agents = user_agents or [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        ]
        
        # Current client session
        self._session: Optional[ClientSession] = None
        
        # Synchronous session
        self._sync_session: Optional[requests.Session] = None
        
        # Last used proxy index
        self._proxy_index = -1
        
        # Last used user agent index
        self._user_agent_index = -1
        
        # Default headers
        self.default_headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": self._get_next_user_agent(),
        }
        
        logger.debug(f"Initialized SessionManager with {len(self.proxies)} proxies and {len(self.user_agents)} user agents")
    
    def _get_next_proxy(self) -> Optional[str]:
        """
        Get the next proxy from the rotation.
        
        Returns:
            Next proxy URL or None if no proxies are configured
        """
        if not self.proxies:
            return None
        
        self._proxy_index = (self._proxy_index + 1) % len(self.proxies)
        return self.proxies[self._proxy_index]
    
    def _get_next_user_agent(self) -> str:
        """
        Get the next user agent from the rotation.
        
        Returns:
            Next user agent string
        """
        self._user_agent_index = (self._user_agent_index + 1) % len(self.user_agents)
        return self.user_agents[self._user_agent_index]
    
    def _update_user_agent(self, headers: Dict[str, str]) -> Dict[str, str]:
        """
        Update headers with a rotated user agent.
        
        Args:
            headers: Headers dictionary to update
            
        Returns:
            Updated headers dictionary
        """
        headers = headers.copy()
        headers["User-Agent"] = self._get_next_user_agent()
        return headers
    
    async def get_session(self) -> ClientSession:
        """
        Get an async client session.
        
        Returns:
            Configured aiohttp.ClientSession
        """
        if self._session is None or self._session.closed:
            # Configure proxy
            proxy = self._get_next_proxy()
            
            # Create connector with connection pooling
            connector = TCPConnector(
                limit=self.max_connections,
                enable_cleanup_closed=True,
                ssl=False,
            )
            
            # Create session
            self._session = ClientSession(
                connector=connector,
                timeout=ClientTimeout(total=self.timeout),
                headers=self.default_headers,
            )
            
            logger.debug(f"Created new async session with proxy: {proxy}")
        
        return self._session
    
    def get_sync_session(self) -> requests.Session:
        """
        Get a synchronous requests session.
        
        Returns:
            Configured requests.Session
        """
        if self._sync_session is None:
            # Create session
            self._sync_session = requests.Session()
            
            # Configure default headers
            self._sync_session.headers.update(self.default_headers)
            
            # Configure default timeout
            self._sync_session.request = lambda method, url, **kwargs: super(requests.Session, self._sync_session).request(
                method=method,
                url=url,
                timeout=kwargs.pop('timeout', self.timeout),
                **kwargs
            )
            
            logger.debug("Created new synchronous session")
        
        return self._sync_session
    
    async def fetch(self, 
                   url: str, 
                   method: str = "GET", 
                   headers: Optional[Dict[str, str]] = None, 
                   data: Any = None, 
                   params: Optional[Dict[str, str]] = None,
                   proxy: Optional[str] = None) -> aiohttp.ClientResponse:
        """
        Fetch a URL with retry logic.
        
        Args:
            url: URL to fetch
            method: HTTP method (GET, POST, etc.)
            headers: Additional headers
            data: Request body data
            params: URL parameters
            proxy: Specific proxy to use (if None, rotate from list)
            
        Returns:
            aiohttp.ClientResponse object
            
        Raises:
            NetworkError: If all retry attempts fail
        """
        session = await self.get_session()
        
        # Combine default headers with provided headers
        request_headers = self.default_headers.copy()
        if headers:
            request_headers.update(headers)
        
        # Update User-Agent
        request_headers = self._update_user_agent(request_headers)
        
        # Get proxy
        request_proxy = proxy or self._get_next_proxy()
        
        # Retry logic
        for attempt in range(self.retry_attempts):
            try:
                response = await session.request(
                    method=method,
                    url=url,
                    headers=request_headers,
                    data=data,
                    params=params,
                    proxy=request_proxy,
                    ssl=False,
                )
                
                # Check for successful response
                if response.status < 400:
                    return response
                
                # For certain status codes, don't retry
                if response.status in (401, 403, 404):
                    error_msg = f"Error {response.status} fetching {url}"
                    logger.error(error_msg)
                    raise NetworkError(error_msg, url=url, status_code=response.status)
                
                # For server errors or rate limiting, wait and retry
                if response.status in (429, 500, 502, 503, 504):
                    error_msg = f"Error {response.status} fetching {url} (attempt {attempt+1}/{self.retry_attempts})"
                    logger.warning(error_msg)
                    
                    # Rate limiting: check for Retry-After header
                    retry_after = response.headers.get('Retry-After')
                    if retry_after and retry_after.isdigit():
                        wait_time = int(retry_after)
                    else:
                        # Exponential backoff
                        wait_time = self.retry_delay * (2 ** attempt)
                    
                    # Rotate proxy and user agent for next attempt
                    request_proxy = self._get_next_proxy()
                    request_headers = self._update_user_agent(request_headers)
                    
                    await asyncio.sleep(wait_time)
                    continue
                
                # For other errors, return the response
                return response
                
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                error_msg = f"Error fetching {url}: {str(e)} (attempt {attempt+1}/{self.retry_attempts})"
                logger.warning(error_msg)
                
                if attempt < self.retry_attempts - 1:
                    # Rotate proxy and user agent for next attempt
                    request_proxy = self._get_next_proxy()
                    request_headers = self._update_user_agent(request_headers)
                    
                    # Exponential backoff
                    wait_time = self.retry_delay * (2 ** attempt)
                    await asyncio.sleep(wait_time)
                else:
                    raise NetworkError(
                        f"Failed to fetch {url} after {self.retry_attempts} attempts", 
                        url=url
                    ) from e
        
        # This should not be reached, but just in case
        raise NetworkError(f"Failed to fetch {url} after {self.retry_attempts} attempts", url=url)
    
    def fetch_sync(self, 
                  url: str, 
                  method: str = "GET", 
                  headers: Optional[Dict[str, str]] = None, 
                  data: Any = None, 
                  params: Optional[Dict[str, str]] = None,
                  proxy: Optional[str] = None) -> requests.Response:
        """
        Fetch a URL synchronously with retry logic.
        
        Args:
            url: URL to fetch
            method: HTTP method (GET, POST, etc.)
            headers: Additional headers
            data: Request body data
            params: URL parameters
            proxy: Specific proxy to use (if None, rotate from list)
            
        Returns:
            requests.Response object
            
        Raises:
            NetworkError: If all retry attempts fail
        """
        session = self.get_sync_session()
        
        # Combine default headers with provided headers
        request_headers = self.default_headers.copy()
        if headers:
            request_headers.update(headers)
        
        # Update User-Agent
        request_headers = self._update_user_agent(request_headers)
        
        # Get proxy
        request_proxy = proxy or self._get_next_proxy()
        proxies = {"http": request_proxy, "https": request_proxy} if request_proxy else None
        
        # Retry logic
        for attempt in range(self.retry_attempts):
            try:
                response = session.request(
                    method=method,
                    url=url,
                    headers=request_headers,
                    data=data,
                    params=params,
                    proxies=proxies,
                    verify=False,
                )
                
                # Check for successful response
                if response.status_code < 400:
                    return response
                
                # For certain status codes, don't retry
                if response.status_code in (401, 403, 404):
                    error_msg = f"Error {response.status_code} fetching {url}"
                    logger.error(error_msg)
                    raise NetworkError(error_msg, url=url, status_code=response.status_code)
                
                # For server errors or rate limiting, wait and retry
                if response.status_code in (429, 500, 502, 503, 504):
                    error_msg = f"Error {response.status_code} fetching {url} (attempt {attempt+1}/{self.retry_attempts})"
                    logger.warning(error_msg)
                    
                    # Rate limiting: check for Retry-After header
                    retry_after = response.headers.get('Retry-After')
                    if retry_after and retry_after.isdigit():
                        wait_time = int(retry_after)
                    else:
                        # Exponential backoff
                        wait_time = self.retry_delay * (2 ** attempt)
                    
                    # Rotate proxy and user agent for next attempt
                    request_proxy = self._get_next_proxy()
                    proxies = {"http": request_proxy, "https": request_proxy} if request_proxy else None
                    request_headers = self._update_user_agent(request_headers)
                    
                    time.sleep(wait_time)
                    continue
                
                # For other errors, return the response
                return response
                
            except (requests.RequestException, requests.Timeout) as e:
                error_msg = f"Error fetching {url}: {str(e)} (attempt {attempt+1}/{self.retry_attempts})"
                logger.warning(error_msg)
                
                if attempt < self.retry_attempts - 1:
                    # Rotate proxy and user agent for next attempt
                    request_proxy = self._get_next_proxy()
                    proxies = {"http": request_proxy, "https": request_proxy} if request_proxy else None
                    request_headers = self._update_user_agent(request_headers)
                    
                    # Exponential backoff
                    wait_time = self.retry_delay * (2 ** attempt)
                    time.sleep(wait_time)
                else:
                    raise NetworkError(
                        f"Failed to fetch {url} after {self.retry_attempts} attempts", 
                        url=url
                    ) from e
        
        # This should not be reached, but just in case
        raise NetworkError(f"Failed to fetch {url} after {self.retry_attempts} attempts", url=url)
    
    async def close(self) -> None:
        """
        Close the session.
        """
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None
            logger.debug("Closed async session")
        
        if self._sync_session:
            self._sync_session.close()
            self._sync_session = None
            logger.debug("Closed synchronous session")
    
    def add_proxy(self, proxy: str) -> None:
        """
        Add a proxy to the rotation.
        
        Args:
            proxy: Proxy URL to add
        """
        if proxy not in self.proxies:
            self.proxies.append(proxy)
            logger.debug(f"Added proxy: {proxy}")
    
    def remove_proxy(self, proxy: str) -> None:
        """
        Remove a proxy from the rotation.
        
        Args:
            proxy: Proxy URL to remove
        """
        if proxy in self.proxies:
            self.proxies.remove(proxy)
            logger.debug(f"Removed proxy: {proxy}")
    
    def add_user_agent(self, user_agent: str) -> None:
        """
        Add a user agent to the rotation.
        
        Args:
            user_agent: User agent string to add
        """
        if user_agent not in self.user_agents:
            self.user_agents.append(user_agent)
            logger.debug(f"Added user agent: {user_agent}")
    
    def clear_proxies(self) -> None:
        """
        Clear all proxies from the rotation.
        """
        self.proxies = []
        self._proxy_index = -1
        logger.debug("Cleared all proxies")
    
    def set_proxies(self, proxies: List[str]) -> None:
        """
        Set the proxy list.
        
        Args:
            proxies: List of proxy URLs
        """
        self.proxies = proxies
        self._proxy_index = -1
        logger.debug(f"Set {len(proxies)} proxies")
    
    def set_user_agents(self, user_agents: List[str]) -> None:
        """
        Set the user agent list.
        
        Args:
            user_agents: List of user agent strings
        """
        self.user_agents = user_agents
        self._user_agent_index = -1
        logger.debug(f"Set {len(user_agents)} user agents")
    
    def __enter__(self) -> 'SessionManager':
        """
        Enter context manager.
        
        Returns:
            SessionManager instance
        """
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """
        Exit the sync context manager.
        
        Args:
            exc_type: Exception type (if any)
            exc_val: Exception value (if any)
            exc_tb: Exception traceback (if any)
        """
        # Close sessions and perform cleanup
        for session in self._sessions.values():
            session.close()
        self._sessions = {}
        
    async def __aenter__(self) -> ClientSession:
        """
        Enter the async context manager.
        
        Returns:
            An aiohttp ClientSession instance
        """
        return await self.get_session()
        
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """
        Exit the async context manager.
        
        Args:
            exc_type: Exception type (if any)
            exc_val: Exception value (if any)
            exc_tb: Exception traceback (if any)
        """
        # Close sessions and perform cleanup
        await self.close()  # Use the existing close method for async cleanup
    
