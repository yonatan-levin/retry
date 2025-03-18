"""
Custom exceptions for the retry package.

This module defines various exception classes used throughout the retry package
to provide more specific error information and better error handling.
"""

from typing import Optional, Dict, Any, List, Union


class RetryError(Exception):
    """Base exception class for all retry errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        """
        Initialize a RetryError.
        
        Args:
            message: Error message
            details: Additional error details
        """
        self.message = message
        self.details = details or {}
        super().__init__(message)
    
    def __str__(self) -> str:
        """
        Return string representation of the error.
        
        Returns:
            Error message with details if any
        """
        if self.details:
            return f"{self.message} - Details: {self.details}"
        return self.message


class ConfigurationError(RetryError):
    """Exception raised for errors in the configuration."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        """
        Initialize a ConfigurationError.
        
        Args:
            message: Error message
            details: Additional error details
        """
        super().__init__(f"Configuration error: {message}", details)


class NetworkError(RetryError):
    """Exception raised for network-related errors."""
    
    def __init__(self, message: str, url: Optional[str] = None, status_code: Optional[int] = None, 
                 response_text: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        """
        Initialize a NetworkError.
        
        Args:
            message: Error message
            url: URL that caused the error
            status_code: HTTP status code
            response_text: Response text if any
            details: Additional error details
        """
        error_details = details or {}
        if url:
            error_details["url"] = url
        if status_code:
            error_details["status_code"] = status_code
        if response_text:
            error_details["response_text"] = response_text
        
        super().__init__(f"Network error: {message}", error_details)


class ParsingError(RetryError):
    """Exception raised for errors during content parsing."""
    
    def __init__(self, message: str, content_type: Optional[str] = None, 
                 details: Optional[Dict[str, Any]] = None):
        """
        Initialize a ParsingError.
        
        Args:
            message: Error message
            content_type: Content type that caused the error
            details: Additional error details
        """
        error_details = details or {}
        if content_type:
            error_details["content_type"] = content_type
        
        super().__init__(f"Parsing error: {message}", error_details)


class ExtractionError(RetryError):
    """Exception raised for errors during data extraction."""
    
    def __init__(self, message: str, rule_name: Optional[str] = None, selector: Optional[str] = None, 
                 details: Optional[Dict[str, Any]] = None):
        """
        Initialize an ExtractionError.
        
        Args:
            message: Error message
            rule_name: Name of the rule that caused the error
            selector: Selector that caused the error
            details: Additional error details
        """
        error_details = details or {}
        if rule_name:
            error_details["rule_name"] = rule_name
        if selector:
            error_details["selector"] = selector
        
        super().__init__(f"Extraction error: {message}", error_details)


class ValidationError(RetryError):
    """Exception raised for validation errors."""
    
    def __init__(self, message: str, field: Optional[str] = None, value: Optional[Any] = None, 
                 details: Optional[Dict[str, Any]] = None):
        """
        Initialize a ValidationError.
        
        Args:
            message: Error message
            field: Field that caused the error
            value: Value that caused the error
            details: Additional error details
        """
        error_details = details or {}
        if field:
            error_details["field"] = field
        if value is not None:
            error_details["value"] = value
        
        super().__init__(f"Validation error: {message}", error_details)


class RateLimitError(RetryError):
    """Exception raised when rate limiting is triggered."""
    
    def __init__(self, message: str, limit: Optional[int] = None, retry_after: Optional[int] = None, 
                 details: Optional[Dict[str, Any]] = None):
        """
        Initialize a RateLimitError.
        
        Args:
            message: Error message
            limit: Rate limit that was exceeded
            retry_after: Seconds to wait before retrying
            details: Additional error details
        """
        error_details = details or {}
        if limit:
            error_details["limit"] = limit
        if retry_after:
            error_details["retry_after"] = retry_after
        
        super().__init__(f"Rate limit exceeded: {message}", error_details)


class AuthenticationError(RetryError):
    """Exception raised for authentication errors."""
    
    def __init__(self, message: str, auth_type: Optional[str] = None, 
                 details: Optional[Dict[str, Any]] = None):
        """
        Initialize an AuthenticationError.
        
        Args:
            message: Error message
            auth_type: Authentication type that caused the error
            details: Additional error details
        """
        error_details = details or {}
        if auth_type:
            error_details["auth_type"] = auth_type
        
        super().__init__(f"Authentication error: {message}", error_details)


class CacheError(RetryError):
    """Exception raised for caching errors."""
    
    def __init__(self, message: str, cache_key: Optional[str] = None, 
                 details: Optional[Dict[str, Any]] = None):
        """
        Initialize a CacheError.
        
        Args:
            message: Error message
            cache_key: Cache key that caused the error
            details: Additional error details
        """
        error_details = details or {}
        if cache_key:
            error_details["cache_key"] = cache_key
        
        super().__init__(f"Cache error: {message}", error_details)


class NLPError(RetryError):
    """Exception raised for NLP-related errors."""
    
    def __init__(self, operation: str, message: str, details: Optional[Dict[str, Any]] = None):
        """
        Initialize an NLPError.
        
        Args:
            operation: NLP operation that caused the error
            message: Error message
            details: Additional error details
        """
        error_details = details or {}
        error_details["operation"] = operation
        
        super().__init__(f"NLP error in {operation}: {message}", error_details)


class PaginationError(RetryError):
    """Exception raised for pagination errors."""
    
    def __init__(self, message: str, page: Optional[int] = None, url: Optional[str] = None, 
                 details: Optional[Dict[str, Any]] = None):
        """
        Initialize a PaginationError.
        
        Args:
            message: Error message
            page: Page number that caused the error
            url: URL that caused the error
            details: Additional error details
        """
        error_details = details or {}
        if page is not None:
            error_details["page"] = page
        if url:
            error_details["url"] = url
        
        super().__init__(f"Pagination error: {message}", error_details)


class PluginError(RetryError):
    """Exception raised for plugin errors."""
    
    def __init__(self, plugin_name: str, message: str, details: Optional[Dict[str, Any]] = None):
        """
        Initialize a PluginError.
        
        Args:
            plugin_name: Name of the plugin that caused the error
            message: Error message
            details: Additional error details
        """
        error_details = details or {}
        error_details["plugin_name"] = plugin_name
        
        super().__init__(f"Plugin error in {plugin_name}: {message}", error_details) 