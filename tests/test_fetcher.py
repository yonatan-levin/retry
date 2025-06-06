import aiohttp
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import pytest_asyncio
from yarl import URL
from honeygrabber.config.fetcher_config import FetcherConfig
from honeygrabber.fetcher import Fetcher
from honeygrabber.utils.authentication import BasicAuth, TokenAuth, AuthManager
from aioresponses import CallbackResult, aioresponses
from honeygrabber.utils.cache import SimpleCache

@pytest.fixture()
def sample_url():
    return "https://example.com"

@pytest.fixture()
def sample_content():
    return "<html><body>Hello World</body></html>"

@pytest.fixture()
def mock_cache():
    class MockCache:
        def __init__(self):
            self.store = {}

        async def set(self, key, value):
            self.store[key] = value

        async def get(self, key):
            return self.store.get(key, None)

        def contains(self, key):
            return key in self.store

    return MockCache()

@pytest.fixture()
def mock_authentication():
    class MockAuthentication(BasicAuth):
        def __init__(self):
            super().__init__(username='user', password='pass')
            
        def get_auth(self):
            return {'Authorization': 'Bearer token'}
    
    return MockAuthentication()

@pytest_asyncio.fixture()
async def url_fetcher(mock_cache, mock_authentication):
    fetcher_config = FetcherConfig(
        proxies=['http://proxy1.com'],
        user_agents=['UserAgent1'],
        cache=mock_cache,
        authentication=mock_authentication
    )
    fetcher = Fetcher(fetcher_config=fetcher_config)
    yield fetcher
    await fetcher.session_manager.close()

@pytest.mark.asyncio
async def test_fetch_success(url_fetcher, sample_url, sample_content):
    with aioresponses() as m:
        m.get(sample_url, status=200, body=sample_content, headers={'Content-Type': 'text/html'})

        content, content_type = await url_fetcher.fetch(sample_url)

        assert content == sample_content , f"Expected {sample_content}, but got {content}"
        assert content_type == 'text/html', f"Expected 'text/html', but got {content_type}"
        
        m.assert_called_once_with(
                sample_url,
                headers=url_fetcher.headers,
                proxy=url_fetcher.proxy,
                timeout=10
            )
        
@pytest.mark.asyncio
async def test_fetch_with_retry(url_fetcher, sample_url, sample_content):
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
                body=sample_content,
                headers={'Content-Type': 'text/html'}
            )

    with aioresponses() as m:
        m.get(sample_url, callback=request_callback)

        # Optionally, mock asyncio.sleep to avoid delays during testing
        with patch('asyncio.sleep', return_value=None):
            content, content_type = await url_fetcher.fetch(sample_url)

    # Assertions
    assert content == sample_content, f"Expected {sample_content}, but got {content}"
    assert content_type == 'text/html', f"Expected 'text/html', but got {content_type}"
    assert call_count == 2  # Ensure it retried once
    
@pytest.mark.asyncio
async def test_fetch_http_error(url_fetcher, sample_url):
    
    def request_callback(url, **kwargs):
        
        request_info = aiohttp.RequestInfo(
                url=URL(url),
                method='GET',
                headers=kwargs.get('headers', {}),
                real_url=URL(url)
            )
        
        raise aiohttp.ClientResponseError(
                request_info=request_info,
                history=(),
                status=500,
                message='Mock Client Error',
            )
    
    with aioresponses() as m:
        m.get(sample_url, callback=request_callback)
        try:
            content, content_type = await url_fetcher.fetch(sample_url)
        except aiohttp.ClientError as e:
            assert e.status == 500
            assert e.message == 'Mock Client Error'

@pytest.mark.asyncio
async def test_fetch_cache_hit(url_fetcher,sample_url, sample_content):

    with aioresponses() as m:
        await url_fetcher.cache.set(sample_url, (sample_content, 'text/html'))
        content, content_type = await url_fetcher.fetch(sample_url)
        
        # Verify that the content was retrieved from the cache
        assert url_fetcher.cache.contains(sample_url)
        assert content == sample_content
        assert content_type == 'text/html'
        # Assert that no network requests were made
        assert len(m.requests) == 0

@pytest.mark.asyncio
async def test_fetch_cache_hit_on_second_request(url_fetcher, sample_url, sample_content):
    # Use aioresponses to mock network requests
    with aioresponses() as m:
        # Mock the network response for the sample_url
        m.get(sample_url, status=200, body=sample_content, headers={'Content-Type': 'text/html'})
        
        # First fetch: Should make a network call
        content1, content_type1 = await url_fetcher.fetch(sample_url)
        assert content1 == sample_content
        assert content_type1 == 'text/html'
        
        # Ensure the content is now cached
        assert url_fetcher.cache.contains(sample_url)
        
        # Second fetch: Should retrieve content from cache, no network call
        content2, content_type2 = await url_fetcher.fetch(sample_url)
        assert content2 == sample_content
        assert content_type2 == 'text/html'
        
        # Verify that only one network request was made
        assert len(m.requests) == 1, f"Expected 1 network request, but got {len(m.requests)}"

@pytest.mark.asyncio
async def test_fetch_with_authentication_basic(url_fetcher, sample_url, sample_content):
    with aioresponses() as m:
        m.get(sample_url, status=200, body=sample_content, headers={'Content-Type': 'text/html'})
        
        # Setup authentication
        auth = BasicAuth(
            username='user', 
            password='pass'
        )
        url_fetcher.authentication = auth
        content, content_type = await url_fetcher.fetch(sample_url)
        
        assert content == sample_content
        assert content_type == 'text/html'
        
@pytest.mark.asyncio
async def test_fetch_with_authentication_token(url_fetcher,mock_authentication, sample_url, sample_content):
    with aioresponses() as m:
        m.get(sample_url, status=200, body=sample_content, headers={'Content-Type': 'text/html'})
        
        content,content_type = await url_fetcher.fetch(sample_url)

        # Check that the request included the authentication header
        headers = url_fetcher.headers
        assert 'Authorization' in headers
        assert headers['Authorization'] == mock_authentication.get_auth()['Authorization']
        assert content_type == 'text/html'
        assert content == sample_content
    
@pytest.mark.asyncio
async def test_fetch_with_playwright_success(url_fetcher, sample_url, sample_content):
    
    with patch('honeygrabber.fetcher.async_playwright') as mock_async_playwright:
        # Set up the async context manager for async_playwright
        mock_playwright_instance = AsyncMock()
        mock_async_playwright.return_value.__aenter__.return_value = mock_playwright_instance

        # Mock the browser, context, and page
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_page = AsyncMock()

        # Configure the mocks to return the appropriate objects
        mock_playwright_instance.chromium.launch.return_value = mock_browser
        mock_browser.new_context.return_value = mock_context
        mock_context.new_page.return_value = mock_page
        
        # Mock the page interactions
        mock_page.goto.return_value = AsyncMock()
        mock_page.content.return_value = sample_content

        # Mock browser.close()
        mock_browser.close.return_value = AsyncMock()

        # Call the method under test
        content, content_type = await url_fetcher.fetch_with_playwright(sample_url)
        
        # Assertions
        assert content == sample_content
        assert content_type == 'text/html'

        expected_proxy_settings = {'server': 'http://proxy1.com'}

        # Verify that the methods were called with the correct arguments
        mock_playwright_instance.chromium.launch.assert_called_with(proxy=expected_proxy_settings)
        mock_browser.new_context.assert_called_with(extra_http_headers=url_fetcher.headers)
        mock_page.goto.assert_called_with(sample_url, timeout=10000)
        mock_browser.close.assert_called_once()

@pytest.mark.asyncio
async def test_fetch_with_playwright_error(url_fetcher, sample_url):
    # Mock async_playwright to raise an exception
    with patch('honeygrabber.fetcher.async_playwright') as mock_async_playwright:
        mock_async_playwright.return_value.__aenter__.side_effect = Exception("Playwright error")

        # Attempt to call the method and expect it to handle retries and eventually raise the exception
        with pytest.raises(Exception) as exc_info:
            await url_fetcher.fetch_with_playwright(sample_url, retries=0)
        assert "Playwright error" in str(exc_info.value)

@pytest.mark.asyncio
async def test_fetch_with_playwright_retry(url_fetcher, sample_url, sample_content):
    initial_retries = 2
    call_count = 0

    async def mock_async_playwright_enter(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count <= initial_retries:
            raise Exception("Playwright error")
        else:
            # On the final attempt, return a successful mock object
            mock_playwright_instance = AsyncMock()
            mock_browser = AsyncMock()
            mock_context = AsyncMock()
            mock_page = AsyncMock()

            # Configure the mocks to return the appropriate objects
            mock_playwright_instance.chromium.launch.return_value = mock_browser
            mock_browser.new_context.return_value = mock_context
            mock_context.new_page.return_value = mock_page

            # Mock the page interactions
            mock_page.goto.return_value = AsyncMock()
            mock_page.content.return_value = sample_content

            # Mock browser.close()
            mock_browser.close.return_value = AsyncMock()
            return mock_playwright_instance

    with patch('honeygrabber.fetcher.async_playwright') as mock_async_playwright:
            mock_async_playwright.return_value.__aenter__.side_effect = mock_async_playwright_enter
            
            
            content, content_type = await url_fetcher.fetch_with_playwright(sample_url, retries=initial_retries)

            # Assertions as before
            assert content == sample_content
            assert content_type == 'text/html'
            expected_calls = initial_retries + 1
            assert call_count == expected_calls, f"Expected {expected_calls} attempts, but got {call_count}"

@pytest.mark.asyncio
async def test_fetch_success_with_fetcher_config(sample_url, sample_content, mock_cache):
    # Create a FetcherConfig instance
    fetcher_config = FetcherConfig(
        proxies=['http://proxy1.com'],
        user_agents=['UserAgent1', 'UserAgent2'],
        rate_limit=1,
        cache=mock_cache  # Use mock_cache instead of SimpleCache
    )

    # Create a Fetcher instance with the FetcherConfig
    fetcher = Fetcher(fetcher_config=fetcher_config)
    # Mock the rate_limiter
    fetcher.rate_limiter.wait = AsyncMock(return_value=None)

    # Use aioresponses to mock the network response
    with aioresponses() as m:
        m.get(sample_url, status=200, body=sample_content, headers={'Content-Type': 'text/html'})

        # Fetch the content
        content, content_type = await fetcher.fetch(sample_url)

        # Assert that the content was fetched successfully
        assert content == sample_content
        assert content_type == 'text/html'
       
@pytest.mark.asyncio
async def test_fetch_multiple_success(url_fetcher, sample_url, sample_content):
    urls = [f"{sample_url}/page{i}" for i in range(1, 4)]
    with aioresponses() as m:
        for url in urls:
            m.get(url, status=200, body=sample_content, headers={'Content-Type': 'text/html'})
        
        results = await url_fetcher.fetch_multiple(urls)
        
        # Verify that the results are as expected
        for content, content_type in results:
            assert content == sample_content
            assert content_type == 'text/html'
        
        # Verify that the requests were made for each URL
        assert len(m.requests) == len(urls)
        
@pytest.mark.asyncio
async def test_fetch_multiple_with_retry(url_fetcher, sample_url, sample_content):
    urls = [f"{sample_url}/page{i}" for i in range(1, 4)]
    call_counts = {}

    async def request_callback(url, **kwargs):
        
        nonlocal call_counts
        if url not in call_counts:
            call_counts[url] = 0
        call_counts[url] += 1

        request_info = aiohttp.RequestInfo(
                url=URL(url),
                method='GET',
                headers=kwargs.get('headers', {}),
                real_url=URL(url)
            )
        if call_counts[url] == 1:
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
                body=sample_content,
                headers={'Content-Type': 'text/html'}
            )

    with aioresponses() as m:
        for url in urls:
            m.get(url, callback=request_callback)

        # Optionally, mock asyncio.sleep to avoid delays during testing
        with patch('asyncio.sleep', return_value=None):
            results = await url_fetcher.fetch_multiple(urls)

    # Assertions
    for content, content_type in results:
        assert content == sample_content
        assert content_type == 'text/html'
    total_call_count = sum(call_counts.values())
    assert total_call_count == 2 * len(urls)
    
@pytest.mark.asyncio
async def test_fetch_with_playwright_multiple_success(url_fetcher, sample_url, sample_content):
    urls = [f"{sample_url}/page{i}" for i in range(1, 4)]

    with patch('honeygrabber.fetcher.async_playwright') as mock_async_playwright:
            # Set up the async context manager for async_playwright
            mock_playwright_instance = AsyncMock()
            mock_async_playwright.return_value.__aenter__.return_value = mock_playwright_instance


            # Mock the browser and context
            mock_browser = AsyncMock()
            mock_context = AsyncMock()

            # Configure the mocks to return the appropriate objects
            mock_playwright_instance.chromium.launch.return_value = mock_browser
            mock_browser.new_context.return_value = mock_context

            # Mock the page interactions for each URL
            mock_pages = []
            for _ in urls:
                mock_page = AsyncMock()
                mock_page.goto.return_value = AsyncMock()
                mock_page.content.return_value = sample_content
                mock_page.close.return_value = AsyncMock()
                mock_pages.append(mock_page)
            mock_context.new_page.side_effect = mock_pages

            # Call the method under test
            results = await url_fetcher.fetch_with_playwright_multiple(urls)

            # Assertions
            for content, content_type in results:
                assert content == sample_content
                assert content_type == 'text/html'
            # Get the proxy from the url_fetcher that was configured in the fixture
            expected_proxy_settings = {'server': url_fetcher.proxy}

            # Verify that the methods were called with the correct arguments
            mock_playwright_instance.chromium.launch.assert_called_with(proxy=expected_proxy_settings)
            mock_browser.new_context.assert_called_with(extra_http_headers=url_fetcher.headers)
            assert mock_context.new_page.call_count == len(urls)
            for mock_page in mock_pages:
                mock_page.goto.assert_called()
                mock_page.content.assert_called()
                mock_page.close.assert_called()
            mock_browser.close.assert_called_once()
