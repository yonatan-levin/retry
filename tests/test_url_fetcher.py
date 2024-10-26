import aiohttp
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import pytest_asyncio
from yarl import URL
from retry.fetcher import URLFetcher
from aioresponses import CallbackResult, aioresponses

    
@pytest_asyncio.fixture
async def url_fetcher():
    fetcher = URLFetcher()
    yield fetcher
    await fetcher.session_manager.close()

@pytest.mark.asyncio
async def test_fetch_success(url_fetcher):
    with aioresponses() as m:
        m.get('http://example.com', status=200, body='Mock Content')

        content = await url_fetcher.fetch('http://example.com')

        assert content == 'Mock Content'
        m.assert_called_once_with(
                'http://example.com',
                headers=url_fetcher.headers,
                proxy=url_fetcher.proxy,
                timeout=10
            )
        
@pytest.mark.asyncio
async def test_fetch_with_retry(url_fetcher):
    call_count = 0

    async def request_callback(url, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            request_info = aiohttp.RequestInfo(
                url=URL(url),
                method='GET',
                headers=kwargs.get('headers', {}),
                real_url=URL(url)
            )

            # First response: Raise a 404 ClientResponseError
            raise aiohttp.ClientResponseError(
                request_info=request_info,
                history=(),
                status=404,
                message='Not Found',
            )
        else:
            # Second response: Return 200 OK with desired content
            return CallbackResult(
                status=200,
                body='Mock Content After Retry'
            )

    with aioresponses() as m:
        m.get('http://example.com', callback=request_callback)

        # Optionally, mock asyncio.sleep to avoid delays during testing
        with patch('asyncio.sleep', return_value=None):
            content = await url_fetcher.fetch('http://example.com')

    # Assertions
    assert content == 'Mock Content After Retry'
    assert call_count == 2  # Ensure it retried once
    
@pytest.mark.asyncio
async def test_fetch_with_playwright_success(url_fetcher):
    # Mock the Playwright context managers and methods
    mock_playwright = MagicMock()
    mock_playwright.__aenter__.return_value = mock_playwright
    mock_playwright.__aexit__.return_value = None
    
    mock_browser = AsyncMock()
    mock_context = AsyncMock()
    mock_page = AsyncMock()
    
    # Set up the mocks to return the appropriate mock objects
    mock_playwright.chromium.launch.return_value = mock_browser
    mock_browser.new_context.return_value = mock_context
    mock_context.new_page.return_value = mock_page
    mock_page.content.return_value = 'Mock Content'
    
    # Patch 'async_playwright' to return the mock_playwright
    async def mock_async_playwright():
        return mock_playwright
    
    with patch('fetcher.async_api.async_playwright', new=mock_async_playwright):
        content = await url_fetcher.fetch_with_playwright('http://example.com')
    
    # Assertions
    assert content == 'Mock Content'
    
    # Verify that the methods were called correctly
    mock_playwright.chromium.launch.assert_called_once_with(proxy=None)
    mock_browser.new_context.assert_called_once_with(extra_http_headers=url_fetcher.headers)
    mock_context.new_page.assert_called_once()
    mock_page.goto.assert_called_once_with('http://example.com')
    mock_page.content.assert_called_once()
    mock_browser.close.assert_called_once()

@pytest.mark.asyncio
async def test_fetch_with_playwright_retry(url_fetcher):
    # Counter to keep track of attempts
    attempt = 0
    
    # Mock the Playwright context managers and methods
    mock_playwright = MagicMock()
    mock_playwright.__aenter__.return_value = mock_playwright
    mock_playwright.__aexit__.return_value = None
    
    mock_browser = AsyncMock()
    mock_context = AsyncMock()
    mock_page = AsyncMock()
    
    # Function to simulate exception on first attempt and success on second
    async def mock_page_content():
        nonlocal attempt
        attempt += 1
        if attempt == 1:
            raise Exception("Simulated Playwright exception")
        else:
            return 'Mock Content After Retry'
    
    mock_page.content.side_effect = mock_page_content
    
    # Set up the mocks to return the appropriate mock objects
    mock_playwright.chromium.launch.return_value = mock_browser
    mock_browser.new_context.return_value = mock_context
    mock_context.new_page.return_value = mock_page
    
    # Patch 'async_playwright' and 'asyncio.sleep'
    async def mock_async_playwright():
        return mock_playwright
    
    with patch('playwright.async_api.async_playwright', new=mock_async_playwright):
        with patch('asyncio.sleep', return_value=None):
            content = await url_fetcher.fetch_with_playwright('http://example.com')
    
    # Assertions
    assert content == 'Mock Content After Retry'
    assert attempt == 2  # Ensure it retried once
    
    # Verify that the methods were called correctly
    assert mock_playwright.chromium.launch.call_count == 2
    assert mock_browser.new_context.call_count == 2
    assert mock_context.new_page.call_count == 2
    assert mock_page.goto.call_count == 2
    assert mock_page.content.call_count == 2
    assert mock_browser.close.call_count == 2


if __name__ == "__main__":
    pytest.main()
