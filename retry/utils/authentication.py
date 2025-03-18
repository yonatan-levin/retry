"""
Authentication utilities for the retry package.

This module provides authentication functionality for the retry package,
including various authentication methods and an authentication manager.
"""

from typing import Dict, Optional, Any, Union, Callable, Tuple
import base64
import json
import re
import time
import asyncio
import logging
from urllib.parse import urlencode

import aiohttp
import requests
from aiohttp import BasicAuth as AioBasicAuth

from retry.utils.logger import get_logger
from retry.utils.exceptions import AuthenticationError

logger = get_logger(__name__)


class BaseAuth:
    """
    Base class for authentication methods.
    
    This class defines the interface for all authentication methods
    and provides some common functionality.
    
    Attributes:
        auth_type: Type of authentication
        credentials: Authentication credentials
    """
    
    def __init__(self, auth_type: str, credentials: Dict[str, Any]):
        """
        Initialize a BaseAuth instance.
        
        Args:
            auth_type: Type of authentication
            credentials: Authentication credentials
        """
        self.auth_type = auth_type
        self.credentials = credentials
        self._is_authenticated = False
        self._token_expires_at: Optional[float] = None
        
        logger.debug(f"Initialized {auth_type} authentication")
    
    def is_authenticated(self) -> bool:
        """
        Check if the authentication is valid.
        
        Returns:
            True if authenticated, False otherwise
        """
        # If we have an expiration time, check if the token has expired
        if self._token_expires_at is not None:
            return self._is_authenticated and time.time() < self._token_expires_at
        
        return self._is_authenticated
    
    def set_authenticated(self, is_authenticated: bool, expires_in: Optional[int] = None) -> None:
        """
        Set the authentication status.
        
        Args:
            is_authenticated: Authentication status
            expires_in: Seconds until the authentication expires
        """
        self._is_authenticated = is_authenticated
        
        if expires_in is not None:
            self._token_expires_at = time.time() + expires_in
    
    def get_auth_for_aiohttp(self) -> Any:
        """
        Get authentication for aiohttp.
        
        Returns:
            Authentication object or headers for aiohttp
            
        Raises:
            AuthenticationError: If authentication is not supported for aiohttp
        """
        raise AuthenticationError(self.auth_type, "Authentication not supported for aiohttp")
    
    def get_auth_for_requests(self) -> Any:
        """
        Get authentication for requests.
        
        Returns:
            Authentication object or headers for requests
            
        Raises:
            AuthenticationError: If authentication is not supported for requests
        """
        raise AuthenticationError(self.auth_type, "Authentication not supported for requests")
    
    def get_headers(self) -> Dict[str, str]:
        """
        Get authentication headers.
        
        Returns:
            Authentication headers
            
        Raises:
            AuthenticationError: If authentication headers are not supported
        """
        raise AuthenticationError(self.auth_type, "Authentication headers not supported")
    
    async def authenticate(self, session: Optional[aiohttp.ClientSession] = None) -> bool:
        """
        Authenticate with the server.
        
        Args:
            session: Optional aiohttp ClientSession
            
        Returns:
            True if authentication was successful, False otherwise
            
        Raises:
            AuthenticationError: If authentication fails
        """
        # No authentication to perform
        self.set_authenticated(True)
        return True
    
    def authenticate_sync(self, session: Optional[requests.Session] = None) -> bool:
        """
        Authenticate with the server synchronously.
        
        Args:
            session: Optional requests Session
            
        Returns:
            True if authentication was successful, False otherwise
            
        Raises:
            AuthenticationError: If authentication fails
        """
        # No authentication to perform
        self.set_authenticated(True)
        return True


class BasicAuth(BaseAuth):
    """
    Basic authentication.
    
    This class provides Basic authentication functionality.
    
    Attributes:
        username: Username for authentication
        password: Password for authentication
        use_legacy: Whether to use legacy Basic auth
    """
    
    def __init__(self, username: str, password: str, use_legacy: bool = False):
        """
        Initialize a BasicAuth instance.
        
        Args:
            username: Username for authentication
            password: Password for authentication
            use_legacy: Whether to use legacy Basic auth
        """
        super().__init__("basic", {"username": username, "password": password})
        self.username = username
        self.password = password
        self.use_legacy = use_legacy
        
        # Basic auth is authenticated by default since it's sent with each request
        self.set_authenticated(True)
    
    def get_auth_for_aiohttp(self) -> AioBasicAuth:
        """
        Get authentication for aiohttp.
        
        Returns:
            AioBasicAuth instance
        """
        return AioBasicAuth(self.username, self.password)
    
    def get_auth_for_requests(self) -> Tuple[str, str]:
        """
        Get authentication for requests.
        
        Returns:
            Tuple of username and password
        """
        return (self.username, self.password)
    
    def get_headers(self) -> Dict[str, str]:
        """
        Get authentication headers.
        
        Returns:
            Authentication headers
        """
        if not self.use_legacy:
            return {}
        
        auth_str = f"{self.username}:{self.password}"
        auth_bytes = auth_str.encode('utf-8')
        auth_b64 = base64.b64encode(auth_bytes).decode('utf-8')
        
        return {"Authorization": f"Basic {auth_b64}"}


class TokenAuth(BaseAuth):
    """
    Token authentication.
    
    This class provides token-based authentication functionality.
    
    Attributes:
        token: Authentication token
        prefix: Token prefix (e.g., Bearer)
        expires_in: Seconds until the token expires
    """
    
    def __init__(self, token: str, prefix: str = "Bearer", expires_in: Optional[int] = None):
        """
        Initialize a TokenAuth instance.
        
        Args:
            token: Authentication token
            prefix: Token prefix (e.g., Bearer)
            expires_in: Seconds until the token expires
        """
        super().__init__("token", {"token": token, "prefix": prefix})
        self.token = token
        self.prefix = prefix
        
        # Token auth is authenticated by default since it's sent with each request
        self.set_authenticated(True, expires_in)
    
    def get_auth_for_aiohttp(self) -> Dict[str, str]:
        """
        Get authentication for aiohttp.
        
        Returns:
            Authentication headers
        """
        return self.get_headers()
    
    def get_auth_for_requests(self) -> Dict[str, str]:
        """
        Get authentication for requests.
        
        Returns:
            Authentication headers
        """
        return self.get_headers()
    
    def get_headers(self) -> Dict[str, str]:
        """
        Get authentication headers.
        
        Returns:
            Authentication headers
        """
        return {"Authorization": f"{self.prefix} {self.token}"}


class FormAuth(BaseAuth):
    """
    Form authentication.
    
    This class provides form-based authentication functionality.
    
    Attributes:
        login_url: URL to submit login form
        username_field: Name of the username field
        password_field: Name of the password field
        username: Username for authentication
        password: Password for authentication
        extra_fields: Extra fields to submit with the form
        success_url: URL to redirect to after successful login
        success_text: Text to look for in the response to confirm success
        token_extractor: Function to extract token from response
        error_text: Text to look for in the response to confirm failure
        auth_cookie: Name of the authentication cookie
    """
    
    def __init__(self,
                 login_url: str,
                 username_field: str,
                 password_field: str,
                 username: str,
                 password: str,
                 extra_fields: Optional[Dict[str, Any]] = None,
                 success_url: Optional[str] = None,
                 success_text: Optional[str] = None,
                 token_extractor: Optional[Callable[[Any], str]] = None,
                 error_text: Optional[str] = None,
                 auth_cookie: Optional[str] = None):
        """
        Initialize a FormAuth instance.
        
        Args:
            login_url: URL to submit login form
            username_field: Name of the username field
            password_field: Name of the password field
            username: Username for authentication
            password: Password for authentication
            extra_fields: Extra fields to submit with the form
            success_url: URL to redirect to after successful login
            success_text: Text to look for in the response to confirm success
            token_extractor: Function to extract token from response
            error_text: Text to look for in the response to confirm failure
            auth_cookie: Name of the authentication cookie
        """
        credentials = {
            "username": username,
            "password": password,
            "login_url": login_url,
            "username_field": username_field,
            "password_field": password_field,
        }
        
        super().__init__("form", credentials)
        
        self.login_url = login_url
        self.username_field = username_field
        self.password_field = password_field
        self.username = username
        self.password = password
        self.extra_fields = extra_fields or {}
        self.success_url = success_url
        self.success_text = success_text
        self.token_extractor = token_extractor
        self.error_text = error_text
        self.auth_cookie = auth_cookie
        
        # Token extracted from response
        self.extracted_token: Optional[str] = None
    
    def get_auth_for_aiohttp(self) -> Dict[str, str]:
        """
        Get authentication for aiohttp.
        
        Returns:
            Authentication headers if token is extracted, empty dict otherwise
        """
        if self.extracted_token:
            return {"Authorization": f"Bearer {self.extracted_token}"}
        return {}
    
    def get_auth_for_requests(self) -> Dict[str, str]:
        """
        Get authentication for requests.
        
        Returns:
            Authentication headers if token is extracted, empty dict otherwise
        """
        if self.extracted_token:
            return {"Authorization": f"Bearer {self.extracted_token}"}
        return {}
    
    def get_headers(self) -> Dict[str, str]:
        """
        Get authentication headers.
        
        Returns:
            Authentication headers if token is extracted, empty dict otherwise
        """
        if self.extracted_token:
            return {"Authorization": f"Bearer {self.extracted_token}"}
        return {}
    
    async def authenticate(self, session: Optional[aiohttp.ClientSession] = None) -> bool:
        """
        Authenticate with the server.
        
        Args:
            session: Optional aiohttp ClientSession
            
        Returns:
            True if authentication was successful, False otherwise
            
        Raises:
            AuthenticationError: If authentication fails
        """
        if self.is_authenticated():
            return True
        
        # Create session if not provided
        should_close_session = False
        if session is None:
            session = aiohttp.ClientSession()
            should_close_session = True
        
        try:
            # Prepare form data
            form_data = {
                self.username_field: self.username,
                self.password_field: self.password,
            }
            
            # Add extra fields
            form_data.update(self.extra_fields)
            
            # Submit login form
            async with session.post(self.login_url, data=form_data, allow_redirects=True) as response:
                # Check if response is successful
                if response.status != 200:
                    error_msg = f"Authentication failed: HTTP {response.status}"
                    logger.error(error_msg)
                    raise AuthenticationError(self.auth_type, error_msg)
                
                # Check if response contains success text
                text = await response.text()
                
                if self.error_text and self.error_text in text:
                    error_msg = f"Authentication failed: Error text found in response"
                    logger.error(error_msg)
                    raise AuthenticationError(self.auth_type, error_msg)
                
                if self.success_text and self.success_text not in text:
                    error_msg = f"Authentication failed: Success text not found in response"
                    logger.error(error_msg)
                    raise AuthenticationError(self.auth_type, error_msg)
                
                # Check if response URL matches success URL
                if self.success_url and str(response.url) != self.success_url:
                    error_msg = f"Authentication failed: Response URL does not match success URL"
                    logger.error(error_msg)
                    raise AuthenticationError(self.auth_type, error_msg)
                
                # Check if auth cookie is present
                if self.auth_cookie:
                    cookies = response.cookies
                    if self.auth_cookie not in cookies:
                        error_msg = f"Authentication failed: Auth cookie not found in response"
                        logger.error(error_msg)
                        raise AuthenticationError(self.auth_type, error_msg)
                
                # Extract token if token extractor is provided
                if self.token_extractor:
                    try:
                        # Try to parse JSON response
                        try:
                            data = await response.json()
                        except:
                            data = text
                        
                        # Extract token
                        self.extracted_token = self.token_extractor(data)
                        
                        if not self.extracted_token:
                            error_msg = f"Authentication failed: Could not extract token from response"
                            logger.error(error_msg)
                            raise AuthenticationError(self.auth_type, error_msg)
                    except Exception as e:
                        error_msg = f"Authentication failed: Error extracting token - {str(e)}"
                        logger.error(error_msg)
                        raise AuthenticationError(self.auth_type, error_msg) from e
                
                # Authentication successful
                self.set_authenticated(True)
                logger.debug("Authentication successful")
                return True
        
        finally:
            # Close session if we created it
            if should_close_session:
                await session.close()
    
    def authenticate_sync(self, session: Optional[requests.Session] = None) -> bool:
        """
        Authenticate with the server synchronously.
        
        Args:
            session: Optional requests Session
            
        Returns:
            True if authentication was successful, False otherwise
            
        Raises:
            AuthenticationError: If authentication fails
        """
        if self.is_authenticated():
            return True
        
        # Create session if not provided
        should_close_session = False
        if session is None:
            session = requests.Session()
            should_close_session = True
        
        try:
            # Prepare form data
            form_data = {
                self.username_field: self.username,
                self.password_field: self.password,
            }
            
            # Add extra fields
            form_data.update(self.extra_fields)
            
            # Submit login form
            response = session.post(self.login_url, data=form_data, allow_redirects=True)
            
            # Check if response is successful
            if response.status_code != 200:
                error_msg = f"Authentication failed: HTTP {response.status_code}"
                logger.error(error_msg)
                raise AuthenticationError(self.auth_type, error_msg)
            
            # Check if response contains success text
            text = response.text
            
            if self.error_text and self.error_text in text:
                error_msg = f"Authentication failed: Error text found in response"
                logger.error(error_msg)
                raise AuthenticationError(self.auth_type, error_msg)
            
            if self.success_text and self.success_text not in text:
                error_msg = f"Authentication failed: Success text not found in response"
                logger.error(error_msg)
                raise AuthenticationError(self.auth_type, error_msg)
            
            # Check if response URL matches success URL
            if self.success_url and response.url != self.success_url:
                error_msg = f"Authentication failed: Response URL does not match success URL"
                logger.error(error_msg)
                raise AuthenticationError(self.auth_type, error_msg)
            
            # Check if auth cookie is present
            if self.auth_cookie:
                cookies = response.cookies
                if self.auth_cookie not in cookies:
                    error_msg = f"Authentication failed: Auth cookie not found in response"
                    logger.error(error_msg)
                    raise AuthenticationError(self.auth_type, error_msg)
            
            # Extract token if token extractor is provided
            if self.token_extractor:
                try:
                    # Try to parse JSON response
                    try:
                        data = response.json()
                    except:
                        data = text
                    
                    # Extract token
                    self.extracted_token = self.token_extractor(data)
                    
                    if not self.extracted_token:
                        error_msg = f"Authentication failed: Could not extract token from response"
                        logger.error(error_msg)
                        raise AuthenticationError(self.auth_type, error_msg)
                except Exception as e:
                    error_msg = f"Authentication failed: Error extracting token - {str(e)}"
                    logger.error(error_msg)
                    raise AuthenticationError(self.auth_type, error_msg) from e
            
            # Authentication successful
            self.set_authenticated(True)
            logger.debug("Authentication successful")
            return True
        
        finally:
            # Close session if we created it
            if should_close_session:
                session.close()


class OAuth2Auth(BaseAuth):
    """
    OAuth 2.0 authentication.
    
    This class provides OAuth 2.0 authentication functionality.
    
    Attributes:
        client_id: OAuth 2.0 client ID
        client_secret: OAuth 2.0 client secret
        token_url: URL to get access token
        refresh_url: URL to refresh access token
        scope: OAuth 2.0 scope
        access_token: Current access token
        refresh_token: Current refresh token
        token_type: Type of token
        expires_in: Seconds until the token expires
    """
    
    def __init__(self,
                 client_id: str,
                 client_secret: str,
                 token_url: str,
                 refresh_url: Optional[str] = None,
                 scope: Optional[str] = None,
                 access_token: Optional[str] = None,
                 refresh_token: Optional[str] = None,
                 token_type: str = "Bearer",
                 expires_in: Optional[int] = None):
        """
        Initialize an OAuth2Auth instance.
        
        Args:
            client_id: OAuth 2.0 client ID
            client_secret: OAuth 2.0 client secret
            token_url: URL to get access token
            refresh_url: URL to refresh access token
            scope: OAuth 2.0 scope
            access_token: Current access token
            refresh_token: Current refresh token
            token_type: Type of token
            expires_in: Seconds until the token expires
        """
        credentials = {
            "client_id": client_id,
            "client_secret": client_secret,
            "token_url": token_url,
        }
        
        super().__init__("oauth2", credentials)
        
        self.client_id = client_id
        self.client_secret = client_secret
        self.token_url = token_url
        self.refresh_url = refresh_url or token_url
        self.scope = scope
        
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.token_type = token_type
        
        # Set authenticated if we have an access token
        if access_token:
            self.set_authenticated(True, expires_in)
    
    def get_auth_for_aiohttp(self) -> Dict[str, str]:
        """
        Get authentication for aiohttp.
        
        Returns:
            Authentication headers
        """
        return self.get_headers()
    
    def get_auth_for_requests(self) -> Dict[str, str]:
        """
        Get authentication for requests.
        
        Returns:
            Authentication headers
        """
        return self.get_headers()
    
    def get_headers(self) -> Dict[str, str]:
        """
        Get authentication headers.
        
        Returns:
            Authentication headers
        """
        if not self.access_token:
            return {}
        
        return {"Authorization": f"{self.token_type} {self.access_token}"}
    
    async def authenticate(self, session: Optional[aiohttp.ClientSession] = None) -> bool:
        """
        Authenticate with the server.
        
        Args:
            session: Optional aiohttp ClientSession
            
        Returns:
            True if authentication was successful, False otherwise
            
        Raises:
            AuthenticationError: If authentication fails
        """
        if self.is_authenticated():
            return True
        
        # Try to refresh token if we have a refresh token
        if self.refresh_token:
            try:
                await self._refresh_token(session)
                return True
            except AuthenticationError:
                logger.warning("Failed to refresh token, trying to get a new token")
        
        # Create session if not provided
        should_close_session = False
        if session is None:
            session = aiohttp.ClientSession()
            should_close_session = True
        
        try:
            # Prepare token request data
            data = {
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            }
            
            if self.scope:
                data["scope"] = self.scope
            
            # Send token request
            async with session.post(self.token_url, data=data) as response:
                # Check if response is successful
                if response.status != 200:
                    error_msg = f"Authentication failed: HTTP {response.status}"
                    logger.error(error_msg)
                    raise AuthenticationError(self.auth_type, error_msg)
                
                # Parse response
                try:
                    token_data = await response.json()
                except Exception as e:
                    error_msg = f"Authentication failed: Error parsing token response - {str(e)}"
                    logger.error(error_msg)
                    raise AuthenticationError(self.auth_type, error_msg) from e
                
                # Extract token information
                self.access_token = token_data.get("access_token")
                self.refresh_token = token_data.get("refresh_token")
                self.token_type = token_data.get("token_type", "Bearer")
                expires_in = token_data.get("expires_in")
                
                if not self.access_token:
                    error_msg = f"Authentication failed: No access token in response"
                    logger.error(error_msg)
                    raise AuthenticationError(self.auth_type, error_msg)
                
                # Authentication successful
                self.set_authenticated(True, expires_in)
                logger.debug("Authentication successful")
                return True
        
        finally:
            # Close session if we created it
            if should_close_session:
                await session.close()
    
    async def _refresh_token(self, session: Optional[aiohttp.ClientSession] = None) -> bool:
        """
        Refresh the access token.
        
        Args:
            session: Optional aiohttp ClientSession
            
        Returns:
            True if refresh was successful, False otherwise
            
        Raises:
            AuthenticationError: If refresh fails
        """
        if not self.refresh_token:
            return False
        
        # Create session if not provided
        should_close_session = False
        if session is None:
            session = aiohttp.ClientSession()
            should_close_session = True
        
        try:
            # Prepare refresh request data
            data = {
                "grant_type": "refresh_token",
                "refresh_token": self.refresh_token,
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            }
            
            # Send refresh request
            async with session.post(self.refresh_url, data=data) as response:
                # Check if response is successful
                if response.status != 200:
                    error_msg = f"Token refresh failed: HTTP {response.status}"
                    logger.error(error_msg)
                    raise AuthenticationError(self.auth_type, error_msg)
                
                # Parse response
                try:
                    token_data = await response.json()
                except Exception as e:
                    error_msg = f"Token refresh failed: Error parsing token response - {str(e)}"
                    logger.error(error_msg)
                    raise AuthenticationError(self.auth_type, error_msg) from e
                
                # Extract token information
                self.access_token = token_data.get("access_token")
                self.refresh_token = token_data.get("refresh_token", self.refresh_token)
                self.token_type = token_data.get("token_type", self.token_type)
                expires_in = token_data.get("expires_in")
                
                if not self.access_token:
                    error_msg = f"Token refresh failed: No access token in response"
                    logger.error(error_msg)
                    raise AuthenticationError(self.auth_type, error_msg)
                
                # Refresh successful
                self.set_authenticated(True, expires_in)
                logger.debug("Token refresh successful")
                return True
        
        finally:
            # Close session if we created it
            if should_close_session:
                await session.close()
    
    def authenticate_sync(self, session: Optional[requests.Session] = None) -> bool:
        """
        Authenticate with the server synchronously.
        
        Args:
            session: Optional requests Session
            
        Returns:
            True if authentication was successful, False otherwise
            
        Raises:
            AuthenticationError: If authentication fails
        """
        if self.is_authenticated():
            return True
        
        # Try to refresh token if we have a refresh token
        if self.refresh_token:
            try:
                self._refresh_token_sync(session)
                return True
            except AuthenticationError:
                logger.warning("Failed to refresh token, trying to get a new token")
        
        # Create session if not provided
        should_close_session = False
        if session is None:
            session = requests.Session()
            should_close_session = True
        
        try:
            # Prepare token request data
            data = {
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            }
            
            if self.scope:
                data["scope"] = self.scope
            
            # Send token request
            response = session.post(self.token_url, data=data)
            
            # Check if response is successful
            if response.status_code != 200:
                error_msg = f"Authentication failed: HTTP {response.status_code}"
                logger.error(error_msg)
                raise AuthenticationError(self.auth_type, error_msg)
            
            # Parse response
            try:
                token_data = response.json()
            except Exception as e:
                error_msg = f"Authentication failed: Error parsing token response - {str(e)}"
                logger.error(error_msg)
                raise AuthenticationError(self.auth_type, error_msg) from e
            
            # Extract token information
            self.access_token = token_data.get("access_token")
            self.refresh_token = token_data.get("refresh_token")
            self.token_type = token_data.get("token_type", "Bearer")
            expires_in = token_data.get("expires_in")
            
            if not self.access_token:
                error_msg = f"Authentication failed: No access token in response"
                logger.error(error_msg)
                raise AuthenticationError(self.auth_type, error_msg)
            
            # Authentication successful
            self.set_authenticated(True, expires_in)
            logger.debug("Authentication successful")
            return True
        
        finally:
            # Close session if we created it
            if should_close_session:
                session.close()
    
    def _refresh_token_sync(self, session: Optional[requests.Session] = None) -> bool:
        """
        Refresh the access token synchronously.
        
        Args:
            session: Optional requests Session
            
        Returns:
            True if refresh was successful, False otherwise
            
        Raises:
            AuthenticationError: If refresh fails
        """
        if not self.refresh_token:
            return False
        
        # Create session if not provided
        should_close_session = False
        if session is None:
            session = requests.Session()
            should_close_session = True
        
        try:
            # Prepare refresh request data
            data = {
                "grant_type": "refresh_token",
                "refresh_token": self.refresh_token,
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            }
            
            # Send refresh request
            response = session.post(self.refresh_url, data=data)
            
            # Check if response is successful
            if response.status_code != 200:
                error_msg = f"Token refresh failed: HTTP {response.status_code}"
                logger.error(error_msg)
                raise AuthenticationError(self.auth_type, error_msg)
            
            # Parse response
            try:
                token_data = response.json()
            except Exception as e:
                error_msg = f"Token refresh failed: Error parsing token response - {str(e)}"
                logger.error(error_msg)
                raise AuthenticationError(self.auth_type, error_msg) from e
            
            # Extract token information
            self.access_token = token_data.get("access_token")
            self.refresh_token = token_data.get("refresh_token", self.refresh_token)
            self.token_type = token_data.get("token_type", self.token_type)
            expires_in = token_data.get("expires_in")
            
            if not self.access_token:
                error_msg = f"Token refresh failed: No access token in response"
                logger.error(error_msg)
                raise AuthenticationError(self.auth_type, error_msg)
            
            # Refresh successful
            self.set_authenticated(True, expires_in)
            logger.debug("Token refresh successful")
            return True
        
        finally:
            # Close session if we created it
            if should_close_session:
                session.close()


class AuthManager:
    """
    Authentication manager.
    
    This class manages authentication methods and provides a unified interface
    for authentication.
    
    Attributes:
        auth_methods: Dictionary of authentication methods
        default_method: Default authentication method
    """
    
    def __init__(self):
        """
        Initialize an AuthManager instance.
        """
        self.auth_methods: Dict[str, BaseAuth] = {}
        self.default_method: Optional[str] = None
        
        logger.debug("Initialized AuthManager")
    
    def add_auth_method(self, name: str, auth_method: BaseAuth, default: bool = False) -> None:
        """
        Add an authentication method.
        
        Args:
            name: Name of the authentication method
            auth_method: Authentication method
            default: Whether this is the default method
        """
        self.auth_methods[name] = auth_method
        
        if default or self.default_method is None:
            self.default_method = name
        
        logger.debug(f"Added auth method: {name}, default: {default}")
    
    def remove_auth_method(self, name: str) -> bool:
        """
        Remove an authentication method.
        
        Args:
            name: Name of the authentication method
            
        Returns:
            True if the method was removed, False otherwise
        """
        if name in self.auth_methods:
            self.auth_methods.pop(name)
            
            # Update default method if necessary
            if self.default_method == name:
                self.default_method = next(iter(self.auth_methods.keys())) if self.auth_methods else None
            
            logger.debug(f"Removed auth method: {name}")
            return True
        
        return False
    
    def get_auth_method(self, name: Optional[str] = None) -> Optional[BaseAuth]:
        """
        Get an authentication method.
        
        Args:
            name: Name of the authentication method (None for default)
            
        Returns:
            Authentication method or None if not found
        """
        if name is not None:
            return self.auth_methods.get(name)
        
        if self.default_method is not None:
            return self.auth_methods.get(self.default_method)
        
        return None
    
    def set_default_method(self, name: str) -> bool:
        """
        Set the default authentication method.
        
        Args:
            name: Name of the authentication method
            
        Returns:
            True if the default method was set, False otherwise
        """
        if name in self.auth_methods:
            self.default_method = name
            logger.debug(f"Set default auth method: {name}")
            return True
        
        return False
    
    async def authenticate(self, 
                          name: Optional[str] = None, 
                          session: Optional[aiohttp.ClientSession] = None) -> bool:
        """
        Authenticate with the server.
        
        Args:
            name: Name of the authentication method (None for default)
            session: Optional aiohttp ClientSession
            
        Returns:
            True if authentication was successful, False otherwise
            
        Raises:
            AuthenticationError: If authentication fails
        """
        auth_method = self.get_auth_method(name)
        
        if auth_method is None:
            error_msg = f"Authentication method not found: {name or 'default'}"
            logger.error(error_msg)
            raise AuthenticationError("unknown", error_msg)
        
        return await auth_method.authenticate(session)
    
    def authenticate_sync(self, 
                         name: Optional[str] = None, 
                         session: Optional[requests.Session] = None) -> bool:
        """
        Authenticate with the server synchronously.
        
        Args:
            name: Name of the authentication method (None for default)
            session: Optional requests Session
            
        Returns:
            True if authentication was successful, False otherwise
            
        Raises:
            AuthenticationError: If authentication fails
        """
        auth_method = self.get_auth_method(name)
        
        if auth_method is None:
            error_msg = f"Authentication method not found: {name or 'default'}"
            logger.error(error_msg)
            raise AuthenticationError("unknown", error_msg)
        
        return auth_method.authenticate_sync(session)
    
    def get_headers(self, name: Optional[str] = None) -> Dict[str, str]:
        """
        Get authentication headers.
        
        Args:
            name: Name of the authentication method (None for default)
            
        Returns:
            Authentication headers
            
        Raises:
            AuthenticationError: If authentication headers are not available
        """
        auth_method = self.get_auth_method(name)
        
        if auth_method is None:
            error_msg = f"Authentication method not found: {name or 'default'}"
            logger.error(error_msg)
            raise AuthenticationError("unknown", error_msg)
        
        return auth_method.get_headers()
    
    def get_auth_for_aiohttp(self, name: Optional[str] = None) -> Any:
        """
        Get authentication for aiohttp.
        
        Args:
            name: Name of the authentication method (None for default)
            
        Returns:
            Authentication object or headers for aiohttp
            
        Raises:
            AuthenticationError: If authentication is not available for aiohttp
        """
        auth_method = self.get_auth_method(name)
        
        if auth_method is None:
            error_msg = f"Authentication method not found: {name or 'default'}"
            logger.error(error_msg)
            raise AuthenticationError("unknown", error_msg)
        
        return auth_method.get_auth_for_aiohttp()
    
    def get_auth_for_requests(self, name: Optional[str] = None) -> Any:
        """
        Get authentication for requests.
        
        Args:
            name: Name of the authentication method (None for default)
            
        Returns:
            Authentication object or headers for requests
            
        Raises:
            AuthenticationError: If authentication is not available for requests
        """
        auth_method = self.get_auth_method(name)
        
        if auth_method is None:
            error_msg = f"Authentication method not found: {name or 'default'}"
            logger.error(error_msg)
            raise AuthenticationError("unknown", error_msg)
        
        return auth_method.get_auth_for_requests()

# For backward compatibility
Authentication = AuthManager
