"""
Authentication examples for the retry package.

This script demonstrates how to use the various authentication methods
provided by the retry package.
"""

import os
import sys
import asyncio

# Add parent directory to path to import retry
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from retry.utils.authentication import (
    BasicAuth, TokenAuth, FormAuth, OAuth2Auth, AuthManager
)


def basic_auth_example():
    """Example of using Basic authentication."""
    print("\n=== Basic Authentication ===")
    
    # Create a BasicAuth instance
    auth = BasicAuth(username="user123", password="pass456")
    
    # Get authentication headers
    headers = auth.get_headers()
    print(f"Headers (default): {headers}")
    
    # With legacy mode
    auth_legacy = BasicAuth(username="user123", password="pass456", use_legacy=True)
    headers_legacy = auth_legacy.get_headers()
    print(f"Headers (legacy): {headers_legacy}")
    
    # For use with aiohttp
    aiohttp_auth = auth.get_auth_for_aiohttp()
    print(f"Aiohttp auth: {aiohttp_auth}")
    
    # For use with requests
    requests_auth = auth.get_auth_for_requests()
    print(f"Requests auth: {requests_auth}")


def token_auth_example():
    """Example of using Token authentication."""
    print("\n=== Token Authentication ===")
    
    # Create a TokenAuth instance
    auth = TokenAuth(token="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...")
    
    # Get authentication headers
    headers = auth.get_headers()
    print(f"Headers (default): {headers}")
    
    # With custom prefix
    auth_custom = TokenAuth(token="access_token_value", prefix="Token")
    headers_custom = auth_custom.get_headers()
    print(f"Headers (custom prefix): {headers_custom}")


async def form_auth_example():
    """Example of using Form authentication."""
    print("\n=== Form Authentication ===")
    
    # Create a FormAuth instance
    auth = FormAuth(
        login_url="https://example.com/login",
        username_field="username",
        password_field="password",
        username="user123",
        password="pass456",
        extra_fields={"remember": True},
        success_text="Welcome"
    )
    
    # In a real application, you would authenticate with the server
    # await auth.authenticate()
    
    print("FormAuth instance created with the following details:")
    print(f"  Login URL: {auth.login_url}")
    print(f"  Username field: {auth.username_field}")
    print(f"  Password field: {auth.password_field}")
    print(f"  Extra fields: {auth.extra_fields}")
    
    # Example with token extraction
    def extract_token(response):
        """Extract token from response."""
        if isinstance(response, dict):
            return response.get("token")
        return None
    
    auth_with_token = FormAuth(
        login_url="https://example.com/api/login",
        username_field="email",
        password_field="pass",
        username="user@example.com",
        password="secret",
        token_extractor=extract_token
    )
    
    # Simulate token extraction
    auth_with_token.extracted_token = "extracted_token_123"
    
    # Get authentication headers
    headers = auth_with_token.get_headers()
    print(f"Headers after token extraction: {headers}")


async def oauth2_auth_example():
    """Example of using OAuth 2.0 authentication."""
    print("\n=== OAuth 2.0 Authentication ===")
    
    # Create an OAuth2Auth instance
    auth = OAuth2Auth(
        client_id="client_id_123",
        client_secret="client_secret_456",
        token_url="https://example.com/oauth/token",
        scope="read write"
    )
    
    # In a real application, you would authenticate with the server
    # await auth.authenticate()
    
    print("OAuth2Auth instance created with the following details:")
    print(f"  Client ID: {auth.client_id}")
    print(f"  Token URL: {auth.token_url}")
    print(f"  Scope: {auth.scope}")
    
    # Simulate successful authentication
    auth.access_token = "oauth_access_token_789"
    auth.refresh_token = "oauth_refresh_token_123"
    auth.set_authenticated(True, 3600)
    
    # Get authentication headers
    headers = auth.get_headers()
    print(f"Headers after authentication: {headers}")
    print(f"Is authenticated: {auth.is_authenticated()}")


def auth_manager_example():
    """Example of using the AuthManager."""
    print("\n=== Authentication Manager ===")
    
    # Create an AuthManager instance
    manager = AuthManager()
    
    # Create authentication methods
    basic_auth = BasicAuth(username="user123", password="pass456")
    token_auth = TokenAuth(token="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...")
    
    # Add authentication methods to the manager
    manager.add_auth_method("basic", basic_auth)
    manager.add_auth_method("token", token_auth, default=True)
    
    # Get authentication headers for specific method
    basic_headers = manager.get_headers("basic")
    print(f"Basic auth headers: {basic_headers}")
    
    # Get authentication headers for default method
    default_headers = manager.get_headers()
    print(f"Default auth headers: {default_headers}")
    
    # Get authentication method
    token_method = manager.get_auth_method("token")
    print(f"Token auth method: {token_method}")
    
    # Change default method
    manager.set_default_method("basic")
    print(f"New default method: {manager.default_method}")


async def main():
    """Run all examples."""
    basic_auth_example()
    token_auth_example()
    await form_auth_example()
    await oauth2_auth_example()
    auth_manager_example()


if __name__ == "__main__":
    asyncio.run(main()) 