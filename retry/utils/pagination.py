"""
Pagination utilities for the retry package.

This module provides pagination functionality for the retry package,
supporting different pagination strategies like URL, page parameter, offset, cursor, 
and advanced methods like link header and JSON path.
"""

import json
import re
from typing import Dict, List, Optional, Any, Union, Callable, Tuple, Generator, AsyncGenerator
import asyncio
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
import logging

from retry.utils.logger import get_logger
from retry.utils.exceptions import PaginationError

logger = get_logger(__name__)


class PaginationHandler:
    """
    Handler for different pagination strategies.
    
    This class provides methods for handling different pagination strategies,
    including URL-based, parameter-based, and more.
    """
    
    def __init__(self, 
                max_pages: Optional[int] = None, 
                start_page: int = 1,
                page_param: str = 'page',
                offset_param: str = 'offset',
                limit_param: str = 'limit',
                items_per_page: int = 10):
        """
        Initialize a PaginationHandler.
        
        Args:
            max_pages: Maximum number of pages to fetch (None for unlimited)
            start_page: Starting page number
            page_param: Name of the page parameter
            offset_param: Name of the offset parameter
            limit_param: Name of the limit parameter
            items_per_page: Default number of items per page
        """
        self.max_pages = max_pages
        self.start_page = start_page
        self.page_param = page_param
        self.offset_param = offset_param
        self.limit_param = limit_param
        self.items_per_page = items_per_page
        self.current_page = start_page
        self.current_offset = 0
        
        logger.debug(f"Initialized PaginationHandler with max_pages: {max_pages}, start_page: {start_page}")
    
    def reset(self) -> None:
        """
        Reset pagination state.
        """
        self.current_page = self.start_page
        self.current_offset = 0
        logger.debug("Reset pagination state")
    
    def add_page_param(self, url: str, page_number: int) -> str:
        """
        Add page parameter to URL.
        
        Args:
            url: Base URL
            page_number: Page number to add
            
        Returns:
            URL with page parameter
        """
        parsed = urlparse(url)
        query = parse_qs(parsed.query)
        
        # Update or add page parameter
        query[self.page_param] = [str(page_number)]
        
        # Rebuild URL
        parsed = parsed._replace(query=urlencode(query, doseq=True))
        return urlunparse(parsed)
    
    def add_offset_param(self, url: str, offset: int, limit: Optional[int] = None) -> str:
        """
        Add offset and limit parameters to URL.
        
        Args:
            url: Base URL
            offset: Offset value
            limit: Limit value (None for default)
            
        Returns:
            URL with offset and limit parameters
        """
        limit = limit or self.items_per_page
        
        parsed = urlparse(url)
        query = parse_qs(parsed.query)
        
        # Update or add offset parameter
        query[self.offset_param] = [str(offset)]
        
        # Update or add limit parameter
        query[self.limit_param] = [str(limit)]
        
        # Rebuild URL
        parsed = parsed._replace(query=urlencode(query, doseq=True))
        return urlunparse(parsed)
    
    def next_page_url(self, url: str) -> str:
        """
        Get URL for the next page using page parameter.
        
        Args:
            url: Current page URL
            
        Returns:
            URL for the next page
        """
        next_page_url = self.add_page_param(url, self.current_page)
        self.current_page += 1
        return next_page_url
    
    def next_offset_url(self, url: str) -> str:
        """
        Get URL for the next page using offset and limit parameters.
        
        Args:
            url: Current page URL
            
        Returns:
            URL for the next page
        """
        next_offset_url = self.add_offset_param(url, self.current_offset)
        self.current_offset += self.items_per_page
        return next_offset_url
    
    def is_last_page(self, data: Any, total_items: Optional[int] = None) -> bool:
        """
        Check if current page is the last page.
        
        Args:
            data: Data from current page
            total_items: Total number of items (if known)
            
        Returns:
            True if current page is the last page, False otherwise
        """
        # Check if max pages reached
        if self.max_pages is not None and self.current_page > self.start_page + self.max_pages - 1:
            logger.debug(f"Max pages ({self.max_pages}) reached")
            return True
        
        # Check if no data (empty array or empty dict)
        if not data or (isinstance(data, list) and len(data) == 0) or (isinstance(data, dict) and len(data) == 0):
            logger.debug("No data in response, assuming last page")
            return True
        
        # Check if fewer items than expected
        if isinstance(data, list) and len(data) < self.items_per_page:
            logger.debug(f"Fewer items ({len(data)}) than expected ({self.items_per_page}), assuming last page")
            return True
        
        # Check if all items fetched
        if total_items is not None:
            items_so_far = (self.current_page - self.start_page) * self.items_per_page
            if items_so_far >= total_items:
                logger.debug(f"All items fetched ({items_so_far} >= {total_items})")
                return True
        
        return False
    
    def extract_next_url_from_json(self, data: Dict[str, Any], json_path: str) -> Optional[str]:
        """
        Extract next URL from JSON response.
        
        Args:
            data: JSON response data
            json_path: JSON path to next URL
            
        Returns:
            Next URL or None if not found
            
        Example:
            For data: {"meta": {"pagination": {"next_url": "https://example.com/page/2"}}}
            Use json_path: "meta.pagination.next_url"
        """
        if not data:
            return None
        
        # Split JSON path by dots
        parts = json_path.split('.')
        
        # Navigate through the JSON structure
        current = data
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None
        
        # Return the final value if it's a string
        if isinstance(current, str):
            return current
        
        return None
    
    def extract_next_url_from_headers(self, headers: Dict[str, str]) -> Optional[str]:
        """
        Extract next URL from response headers.
        
        Args:
            headers: Response headers
            
        Returns:
            Next URL or None if not found
            
        Note:
            This method looks for the 'Link' header with rel="next"
        """
        if not headers:
            return None
        
        # Look for Link header
        link_header = headers.get('Link') or headers.get('link')
        if not link_header:
            return None
        
        # Parse Link header
        links = {}
        for link in link_header.split(','):
            url_match = re.search(r'<([^>]+)>', link)
            rel_match = re.search(r'rel="([^"]+)"', link)
            
            if url_match and rel_match:
                url = url_match.group(1)
                rel = rel_match.group(1)
                links[rel] = url
        
        # Return next URL if found
        return links.get('next')
    
    def extract_total_from_json(self, data: Dict[str, Any], json_path: str) -> Optional[int]:
        """
        Extract total items count from JSON response.
        
        Args:
            data: JSON response data
            json_path: JSON path to total items count
            
        Returns:
            Total items count or None if not found
            
        Example:
            For data: {"meta": {"pagination": {"total": 100}}}
            Use json_path: "meta.pagination.total"
        """
        if not data:
            return None
        
        # Split JSON path by dots
        parts = json_path.split('.')
        
        # Navigate through the JSON structure
        current = data
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None
        
        # Return the final value if it's an integer
        if isinstance(current, int):
            return current
        
        # Try to convert to integer if it's a string
        if isinstance(current, str) and current.isdigit():
            return int(current)
        
        return None
    
    def extract_total_from_headers(self, headers: Dict[str, str], header_name: str = 'X-Total-Count') -> Optional[int]:
        """
        Extract total items count from response headers.
        
        Args:
            headers: Response headers
            header_name: Name of the header containing the total count
            
        Returns:
            Total items count or None if not found
        """
        if not headers:
            return None
        
        # Look for the specified header
        total_header = headers.get(header_name) or headers.get(header_name.lower())
        if not total_header:
            return None
        
        # Try to convert to integer
        if total_header.isdigit():
            return int(total_header)
        
        return None
    
    def get_cursor_url(self, url: str, cursor: str, cursor_param: str = 'cursor') -> str:
        """
        Get URL with cursor parameter.
        
        Args:
            url: Base URL
            cursor: Cursor value
            cursor_param: Name of the cursor parameter
            
        Returns:
            URL with cursor parameter
        """
        parsed = urlparse(url)
        query = parse_qs(parsed.query)
        
        # Update or add cursor parameter
        query[cursor_param] = [cursor]
        
        # Rebuild URL
        parsed = parsed._replace(query=urlencode(query, doseq=True))
        return urlunparse(parsed)
    
    def has_more_pages(self, current_page: int) -> bool:
        """
        Check if there are more pages to fetch based on current page number.
        
        Args:
            current_page: Current page number
            
        Returns:
            True if there are more pages, False otherwise
        """
        if self.max_pages is None:
            return True
        
        return current_page < self.start_page + self.max_pages
    
    def has_more_items(self, items_fetched: int, total_items: Optional[int] = None) -> bool:
        """
        Check if there are more items to fetch.
        
        Args:
            items_fetched: Number of items fetched so far
            total_items: Total number of items (if known)
            
        Returns:
            True if there are more items, False otherwise
        """
        if total_items is None:
            return True
        
        return items_fetched < total_items
    
    async def paginate(self, 
                      fetch_func: Callable[[str], AsyncGenerator[Any, None]],
                      base_url: str,
                      pagination_type: str = 'page',
                      json_path: Optional[str] = None,
                      cursor_param: Optional[str] = None) -> AsyncGenerator[Any, None]:
        """
        Paginate through results.
        
        Args:
            fetch_func: Function to fetch data from URL
            base_url: Base URL to start from
            pagination_type: Type of pagination (page, offset, link, json, cursor)
            json_path: JSON path for extracting next URL (for 'json' pagination type)
            cursor_param: Name of the cursor parameter (for 'cursor' pagination type)
            
        Yields:
            Data from each page
            
        Raises:
            PaginationError: If there is an error paginating
        """
        self.reset()
        current_url = base_url
        page_num = 0
        
        try:
            while True:
                # Fetch current page
                async for data in fetch_func(current_url):
                    page_num += 1
                    logger.debug(f"Fetched page {page_num}: {current_url}")
                    
                    # Yield data
                    yield data
                    
                    # Check if last page
                    if self.is_last_page(data):
                        logger.debug("Last page reached")
                        return
                    
                    # Get next page URL based on pagination type
                    if pagination_type == 'page':
                        current_url = self.next_page_url(base_url)
                    elif pagination_type == 'offset':
                        current_url = self.next_offset_url(base_url)
                    elif pagination_type == 'link':
                        # Extract from response headers (if provided in data)
                        if isinstance(data, dict) and 'headers' in data:
                            next_url = self.extract_next_url_from_headers(data['headers'])
                            if next_url:
                                current_url = next_url
                            else:
                                logger.debug("No next URL found in headers")
                                return
                        else:
                            logger.debug("Headers not found in data")
                            return
                    elif pagination_type == 'json':
                        # Extract from JSON response
                        if json_path:
                            next_url = self.extract_next_url_from_json(data, json_path)
                            if next_url:
                                current_url = next_url
                            else:
                                logger.debug(f"No next URL found at JSON path: {json_path}")
                                return
                        else:
                            logger.debug("JSON path not provided")
                            return
                    elif pagination_type == 'cursor':
                        # Extract cursor from JSON response
                        if json_path and cursor_param:
                            cursor = self.extract_next_url_from_json(data, json_path)
                            if cursor:
                                current_url = self.get_cursor_url(base_url, cursor, cursor_param)
                            else:
                                logger.debug(f"No cursor found at JSON path: {json_path}")
                                return
                        else:
                            logger.debug("JSON path or cursor parameter not provided")
                            return
                    else:
                        raise PaginationError(f"Unsupported pagination type: {pagination_type}")
        
        except Exception as e:
            error_msg = f"Error paginating: {str(e)}"
            logger.error(error_msg)
            raise PaginationError(error_msg, page=page_num, url=current_url) from e 