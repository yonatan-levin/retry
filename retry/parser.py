from lxml import html
from .logger import logger

class HTMLParser:
    def __init__(self, content):
        try:
            self.tree = html.fromstring(content)
        except Exception as e:
            logger.error(f"Error parsing HTML content: {e}")
            self.tree = None

    def select(self, selector, selector_type='css'):
        if not self.tree:
            return []
        try:
            if selector_type == 'css':
                return self.tree.cssselect(selector)
            elif selector_type == 'xpath':
                return self.tree.xpath(selector)
            else:
                logger.error(f"Unknown selector type: {selector_type}")
                return []
        except Exception as e:
            logger.error(f"Error selecting elements: {e}")
            return []
