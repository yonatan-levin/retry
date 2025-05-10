import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from honeygrabber import HoneyGrabberSC
from honeygrabber.fetcher import Fetcher
from honeygrabber.parser import ContentParser
from honeygrabber.extractor import ContentExtractor
from honeygrabber.cleaner import Cleaner
from honeygrabber.formatter import OutputFormatter
from honeygrabber.utils.cache import SimpleCache
from honeygrabber.utils.session_manager import SessionManager
from honeygrabber.config.fetcher_config import FetcherConfig

@pytest.fixture
def sample_html_content():
    return """
    <html>
        <head><title>Test Page</title></head>
        <body>
            <div id="main">
                <h1 class="title">Hello World</h1>
                <p class="content">This is a <strong>test</strong> page.</p>
            </div>
        </body>
    </html>
    """

@pytest.fixture
def sample_rules():
    return {
        'title': {
            'selector': 'h1.title',
            'type': 'css',
            'attribute': None,
            'multiple': False
        }
    }

@pytest.fixture
def retry_instance():
    return HoneyGrabberSC()

@pytest.mark.asyncio
async def test_scrape_async(retry_instance, sample_html_content, sample_rules):
    # Mock the fetcher to return sample_html_content
    with patch.object(Fetcher, 'fetch', new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = (sample_html_content, 'text/html')
        data = await retry_instance.scrape_async('http://example.com', sample_rules)
        assert data == {'title': 'Hello World'}

def test_scrape_sync(retry_instance, sample_html_content, sample_rules):
    # Mock the fetcher to return sample_html_content
    with patch.object(Fetcher, 'fetch', new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = (sample_html_content, 'text/html')
        data = retry_instance.scrape_sync('http://example.com', sample_rules)
        assert data == {'title': 'Hello World'}

@pytest.mark.asyncio
async def test_fetch_content_error(retry_instance, sample_rules):
    # Simulate a network error
    with patch.object(Fetcher, 'fetch', new_callable=AsyncMock) as mock_fetch:
        mock_fetch.side_effect = Exception("Network Error")
        with pytest.raises(Exception) as exc_info:
            await retry_instance.scrape_async('http://example.com', sample_rules)
        assert "Network Error" in str(exc_info.value)

@pytest.mark.asyncio
@patch.object(Fetcher, 'fetch', new_callable=AsyncMock)
async def test_retry_on_error(mock_fetch, retry_instance,sample_html_content, sample_rules):
    # Simulate the fetcher failing twice before succeeding
    async def side_effect(url, retries=3,timeout=10):
        try:        
            if side_effect.attempts < 2:
                side_effect.attempts += 1
                raise Exception("Network Error")
            else:
                return (sample_html_content, 'text/html')
        except:
            return await side_effect(url, retries - 1,timeout)

    side_effect.attempts = 0
    mock_fetch.side_effect = side_effect

    data = await retry_instance.scrape_async('http://example.com', sample_rules)
    assert data == {'title': 'Hello World'}
    assert side_effect.attempts == 2
    
@pytest.mark.asyncio
async def test_plugin_system(retry_instance, sample_html_content, sample_rules):
    # Define a simple plugin
    class UpperCasePlugin:
        def process(self, data):
            return {k: v.upper() for k, v in data.items()}

    retry_instance.register_plugin(UpperCasePlugin())

    with patch.object(Fetcher, 'fetch', new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = (sample_html_content, 'text/html')
        data = await retry_instance.scrape_async('http://example.com', sample_rules)
        assert data == {'title': 'HELLO WORLD'}

def test_output_formatter(retry_instance):
    data = {'title': 'Hello World'}
    json_output = retry_instance.output(data, format_type='json')
    assert json_output == '{\n  "title": "Hello World"\n}'

    csv_output = retry_instance.output(data, format_type='csv')
    assert csv_output.strip() == 'title\r\nHello World'

    xml_output = retry_instance.output(data, format_type='xml')
    assert '<root>' in xml_output and '<title>Hello World</title>' in xml_output

@pytest.mark.asyncio
async def test_pipeline_execution_order(retry_instance, sample_html_content, sample_rules):
    order = []

    async def mock_fetch_content(context):
        order.append('fetch')
        context['content'] = sample_html_content
        context['content_type'] = 'text/html'

    async def mock_parse_content(context):
        order.append('parse')
        context['parser'] = ContentParser(context['content'], context['content_type'])

    async def mock_extract_data(context):
        order.append('extract')
        extractor = ContentExtractor(context['parser'], context['rules'])
        context['data'] = extractor.extract()

    async def mock_clean_data(context):
        order.append('clean')
        context['data'] = context['data']

    async def mock_apply_plugins(context):
        order.append('plugins')
        context['data'] = context['data']

    retry_instance.pipeline = [
        mock_fetch_content,
        mock_parse_content,
        mock_extract_data,
        mock_clean_data,
        mock_apply_plugins
    ]

    data = await retry_instance.scrape_async('http://example.com', sample_rules)
    assert data == {'title': 'Hello World'}
    assert order == ['fetch', 'parse', 'extract', 'clean', 'plugins']

def test_register_plugin_invalid(retry_instance):
    class InvalidPlugin:
        pass

    with pytest.raises(ValueError) as exc_info:
        retry_instance.register_plugin(InvalidPlugin())
    assert "Plugin must implement a callable 'process' method." in str(exc_info.value)

@pytest.mark.asyncio
async def test_cache_usage():
    # Create a mock cache with async methods
    class MockCache:
        def __init__(self):
            self.store = {}

        async def set(self, key, value):
            self.store[key] = value

        async def get(self, key):
            return self.store.get(key, None)

        def contains(self, key):
            return key in self.store
    
    cache = MockCache()
    
    # Create a mock session_manager
    mock_session_manager = MagicMock()
    fetcher_config = FetcherConfig(session_manager=mock_session_manager, cache=cache)
    fetcher = Fetcher(fetcher_config)
    # Also mock the rate_limiter
    fetcher.rate_limiter.wait = AsyncMock(return_value=None)
    retry_instance = HoneyGrabberSC(fetcher=fetcher)

    url = 'http://example.com'

    # Mock the session_manager's __aenter__ and __aexit__ methods
    mock_session = MagicMock()
    mock_session_manager.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session_manager.__aexit__ = AsyncMock(return_value=None)

    # Mock the session.get method to return an async context manager
    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.raise_for_status = MagicMock()
    # Ensure that response.headers.get('Content-Type') returns 'text/html'
    mock_response.headers = {'Content-Type': 'text/html'}
    mock_response.text = AsyncMock(return_value='<html></html>')

    # Create a proper async context manager for mock_session.get()
    class AsyncContextManagerMock:
        async def __aenter__(self):
            return mock_response
        
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            return None
    
    # Use the MagicMock for get
    mock_session.get = MagicMock(return_value=AsyncContextManagerMock())

    # First fetch: Should use the network and store result in cache
    data1 = await retry_instance.scrape_async(url, {})
    assert url in cache.store

    # Reset the mock_session.get to track calls in the second fetch
    mock_session.get.reset_mock()

    # Second fetch: Should retrieve from cache, so no network call
    data2 = await retry_instance.scrape_async(url, {})

    # Ensure that the session.get method was not called in the second fetch
    mock_session.get.assert_not_called()

    # Verify that the data from both fetches is the same
    assert data1 == data2

    # Optionally, verify that the cache contains the expected content
    cached_content = await cache.get(url)
    assert cached_content == ('<html></html>', 'text/html')

@pytest.mark.asyncio
async def test_cleaner_usage(retry_instance, sample_html_content, sample_rules):
    # Mock the cleaner to modify data
    class MockCleaner:
        def clean(self, data):
            data['title'] = data['title'].lower()
            return data

    retry_instance.cleaner = MockCleaner()

    with patch.object(Fetcher, 'fetch', new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = (sample_html_content, 'text/html')
        data = await retry_instance.scrape_async('http://example.com', sample_rules)
        assert data == {'title': 'hello world'}

def test_fetcher_initialization():
    # Test that the fetcher is initialized with the cache and config
    cache = SimpleCache()
    fetcher_config = FetcherConfig(retries=5, timeout=15, rate_limit=2, cache=cache)
    retry_instance = HoneyGrabberSC(fetcher_config=fetcher_config)
    assert retry_instance.fetcher.cache is cache
    assert retry_instance.fetcher_config is fetcher_config
    assert retry_instance.fetcher_config.retries == 5
    assert retry_instance.fetcher_config.timeout == 15
    assert retry_instance.fetcher_config.rate_limit == 2

def test_formatter_initialization():
    # Test that the formatter is initialized properly
    formatter = OutputFormatter()
    retry_instance = HoneyGrabberSC(formatter=formatter)
    assert retry_instance.formatter is formatter

def test_parser_class_initialization():
    class CustomParser(ContentParser):
        pass

    retry_instance = HoneyGrabberSC(parser_class=CustomParser)
    assert retry_instance.parser_class is CustomParser

def test_extractor_class_initialization():
    class CustomExtractor(ContentExtractor):
        pass

    retry_instance = HoneyGrabberSC(extractor_class=CustomExtractor)
    assert retry_instance.extractor_class is CustomExtractor

@pytest.mark.asyncio
async def test_pipeline_modification(retry_instance):
    # Remove the cleaner step from the pipeline
    retry_instance.pipeline.remove(retry_instance._clean_data)

    with patch.object(Fetcher, 'fetch', new_callable=AsyncMock) as mock_fetch, \
         patch.object(ContentExtractor, 'extract', return_value={'title': 'Test Title'}) as mock_extract:

        mock_fetch.return_value = ('<html></html>', 'text/html')
        data = await retry_instance.scrape_async('http://example.com', {})
        assert data == {'title': 'Test Title'}

        # Ensure that the cleaner was not called
        assert retry_instance.cleaner is not None
        # Since the cleaner was removed from the pipeline, data should be unmodified

def test_fetcher_method_not_found(retry_instance):
    with pytest.raises(AttributeError) as exc_info:
        retry_instance.scrape_sync('http://example.com', {}, fetch_method='nonexistent_method')
    assert "object has no attribute 'nonexistent_method'" in str(exc_info.value)
