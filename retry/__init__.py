import asyncio

import aiohttp
from .fetcher import URLFetcher
from .parser import HTMLParser
from .extractor import ContentExtractor
from .cleaner import DataCleaner
from .formatter import OutputFormatter
from .utils.cache import SimpleCache
from .logger import logger

class Retry:
    def __init__(self, **kwargs):
        self.cache = kwargs.get('cache', SimpleCache())
        self.fetcher = URLFetcher(**kwargs)
        self.cleaner = DataCleaner()
        self.formatter = OutputFormatter()
        self.plugins = []

    def register_plugin(self, plugin):
        if hasattr(plugin, 'process') and callable(getattr(plugin, 'process')):
            self.plugins.append(plugin)
        else:
            raise ValueError("Plugin must implement a callable 'process' method.")

    async def scrape_async(self, url, rules, **kwargs):
                content = await self.fetcher.fetch(url,retries=kwargs.get('retries', 3))
                parser = HTMLParser(content)
                extractor = ContentExtractor(parser, rules)
                data = extractor.extract()
                data = self.cleaner.clean(data)
                for plugin in self.plugins:
                    data = plugin.process(data)
                return data

    async def scrape(self, url, rules, **kwargs):
        return await self.scrape_async(url, rules, **kwargs)

    def scrape_sync(self, url, rules, **kwargs):
        return asyncio.run(self.scrape_async(url, rules, **kwargs))

    def output(self, data, format_type='json'):
            return self.formatter.format(data, format_type)
