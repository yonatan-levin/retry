from bs4 import BeautifulSoup
import json
import lxml.etree

class ContentParser:
    def __init__(self, content, content_type):
        self.content_type = content_type
        self.parsed_content = self.parse_content(content)

    def parse_content(self, content):
        if 'application/json' in self.content_type:
            return json.loads(content)
        elif 'text/html' in self.content_type:
            return BeautifulSoup(content, 'lxml')
        else:
            raise ValueError(f"Unsupported content type: {self.content_type}")

    def select(self, selector, selector_type='css'):
        if isinstance(self.parsed_content, BeautifulSoup):
            if selector_type == 'css':
                return self.parsed_content.select(selector)
            elif selector_type == 'xpath':
                # Convert BeautifulSoup object to string and parse with lxml
                html_str = str(self.parsed_content)
                tree = lxml.etree.HTML(html_str)
                return tree.xpath(selector)
            else:
                raise ValueError(f"Unsupported selector type: {selector_type}")
        elif isinstance(self.parsed_content, dict):
            # For JSON content, we can implement a simple JSONPath selector
            return self.select_json(selector)
        else:
            raise ValueError("Parsed content type not supported for selection")

    def select_json(self, selector):
        # Simple implementation of JSONPath-like selector
        # For example, selector = 'key1.key2'
        keys = selector.split('.')
        data = self.parsed_content
        for key in keys:
            if isinstance(data, dict):
                data = data.get(key, {})
            else:
                data = {}
        return [data] if data else []
