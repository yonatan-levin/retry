import pytest
from bs4 import BeautifulSoup
import json
from retry.parser import ContentParser

@pytest.fixture
def sample_json_content():
    return json.dumps({
        "key1": {
            "key2": {
                "key3": "value3"
            },
            "key4": [1, 2, 3]
        }
    })

@pytest.fixture
def sample_html_content():
    return """
    <html>
        <head><title>Test Page</title></head>
        <body>
            <div id="main">
                <h1 class="title">Hello World</h1>
                <p class="content">This is a <strong>test</strong> page.</p>
                <ul>
                    <li><a href="/link1">Link 1</a></li>
                    <li><a href="/link2">Link 2</a></li>
                    <li><a href="/link3">Link 3</a></li>
                </ul>
            </div>
        </body>
    </html>
    """

def test_parse_json_content(sample_json_content):
    parser = ContentParser(sample_json_content, content_type='application/json')
    assert isinstance(parser.parsed_content, dict)
    assert parser.parsed_content['key1']['key2']['key3'] == 'value3'

def test_parse_html_content(sample_html_content):
    parser = ContentParser(sample_html_content, content_type='text/html')
    assert isinstance(parser.parsed_content, BeautifulSoup)
    title = parser.parsed_content.title.string
    assert title == 'Test Page'

def test_select_css_selector(sample_html_content):
    parser = ContentParser(sample_html_content, content_type='text/html')
    elements = parser.select('h1.title')
    assert len(elements) == 1
    assert elements[0].string == 'Hello World'

def test_select_xpath_selector(sample_html_content):
    parser = ContentParser(sample_html_content, content_type='text/html')
    elements = parser.select('//h1[@class="title"]', selector_type='xpath')
    assert len(elements) == 1
    assert elements[0].text == 'Hello World'

def test_select_invalid_selector_type(sample_html_content):
    parser = ContentParser(sample_html_content, content_type='text/html')
    with pytest.raises(ValueError) as exc_info:
        parser.select('h1.title', selector_type='invalid')
    assert 'Unsupported selector type' in str(exc_info.value)

def test_select_from_json(sample_json_content):
    parser = ContentParser(sample_json_content, content_type='application/json')
    result = parser.select('key1.key2.key3')
    assert result == ['value3']

def test_select_nonexistent_json_key(sample_json_content):
    parser = ContentParser(sample_json_content, content_type='application/json')
    result = parser.select('key1.key2.nonexistent')
    assert result == []

def test_unsupported_content_type():
    content = "Plain text content"
    with pytest.raises(ValueError) as exc_info:
        ContentParser(content, content_type='text/plain')
    assert 'Unsupported content type' in str(exc_info.value)

def test_parsed_content_type_not_supported():
    content = "<xml><data>Test</data></xml>"
    with pytest.raises(ValueError) as exc_info:
        parser = ContentParser(content, content_type='application/xml')
        parser.select('data')
    assert 'Unsupported content type: application/xml' in str(exc_info.value)

def test_select_css_multiple_elements(sample_html_content):
    parser = ContentParser(sample_html_content, content_type='text/html')
    links = parser.select('ul li a')
    assert len(links) == 3
    hrefs = [link['href'] for link in links]
    assert hrefs == ['/link1', '/link2', '/link3']

def test_select_xpath_multiple_elements(sample_html_content):
    parser = ContentParser(sample_html_content, content_type='text/html')
    links = parser.select('//ul/li/a', selector_type='xpath')
    assert len(links) == 3
    hrefs = [link.get('href') for link in links]
    assert hrefs == ['/link1', '/link2', '/link3']

def test_select_json_list(sample_json_content):
    parser = ContentParser(sample_json_content, content_type='application/json')
    result = parser.select('key1.key4')
    assert result == [[1, 2, 3]]

def test_select_json_invalid_selector(sample_json_content):
    parser = ContentParser(sample_json_content, content_type='application/json')
    result = parser.select('key1.key5')
    assert result == []

def test_parse_content_invalid_json():
    invalid_json = "{'key': 'value'"  # Missing closing brace
    with pytest.raises(json.JSONDecodeError):
        ContentParser(invalid_json, content_type='application/json')

def test_parse_content_invalid_html():
    invalid_html = "<html><body><h1>Test"  # Missing closing tags
    parser = ContentParser(invalid_html, content_type='text/html')
    assert isinstance(parser.parsed_content, BeautifulSoup)
    h1 = parser.parsed_content.find('h1')
    assert h1.string == 'Test'

def test_select_invalid_selector(sample_html_content):
    parser = ContentParser(sample_html_content, content_type='text/html')
    with pytest.raises(ValueError) as exc_info:
        parser.select('invalid_selector')
    assert 'Unsupported selector type' in str(exc_info.value)