import asyncio
from .fetcher import Fetcher
from .parser import ContentParser
from .extractor import ContentExtractor
from .cleaner import Cleaner
from .formatter import OutputFormatter
from .utils.cache import SimpleCache



#Write here a global 


class Retry:
    def __init__(self, fetcher=None, parser_class=ContentParser, extractor_class=ContentExtractor,
                 cleaner=None, formatter=None, cache=None, plugins=None, **kwargs):
        self.cache = cache or SimpleCache()
        self.fetcher = fetcher or Fetcher(**kwargs, cache=self.cache)
        self.parser_class = parser_class
        self.extractor_class = extractor_class
        self.cleaner = cleaner or Cleaner()
        self.formatter = formatter or OutputFormatter()
        self.plugins = plugins or []
        self.pipeline = [
            self._fetch_content,
            self._parse_content,
            self._extract_data,
            self._clean_data,
            self._apply_plugins
        ]


    def register_plugin(self, plugin):
        if hasattr(plugin, 'process') and callable(getattr(plugin, 'process')):
            self.plugins.append(plugin)
        else:
            raise ValueError("Plugin must implement a callable 'process' method.")

    async def scrape_async(self, url, rules, fetch_method='fetch', **kwargs):
        context = {
            'url': url,
            'rules': rules,
            'fetch_method': fetch_method,
            'kwargs': kwargs
        }
        for step in self.pipeline:
            await step(context)
        return context.get('data')

    async def scrape(self, url, rules, fetch_method='fetch', **kwargs):
        return await self.scrape_async(url, rules, fetch_method, **kwargs)
    
    def scrape_sync(self, url, rules, fetch_method='fetch', **kwargs):
        return asyncio.run(self.scrape_async(url, rules, fetch_method, **kwargs))

    def output(self, data, format_type='json'):
            return self.formatter.format(data, format_type)

    async def _fetch_content(self, context):
        fetch_function = getattr(self.fetcher, context['fetch_method'])
        content,content_type = await fetch_function(context['url'], retries=context['kwargs'].get('retries', 3))

        context['content'] = content
        context['content_type'] = content_type
        
    async def _parse_content(self, context):
        parser = self.parser_class(context['content'], context['content_type'])
        context['parser'] = parser

    async def _extract_data(self, context):
        extractor = self.extractor_class(context['parser'], context['rules'])
        data = extractor.extract()
        context['data'] = data

    async def _clean_data(self, context):
        data = self.cleaner.clean(context['data'])
        context['data'] = data

    async def _apply_plugins(self, context):
        data = context['data']
        for plugin in self.plugins:
            data = plugin.process(data)
        context['data'] = data
