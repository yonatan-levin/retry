import asyncio
from typing import Any, Dict, Union

from .models.rules import Rules
from .utils import PaginationHandler
from .config import CleanerConfig,FetcherConfig
from .fetcher import Fetcher
from .parser import ContentParser
from .extractor import ContentExtractor
from .cleaner import Cleaner
from .formatter import OutputFormatter

class HoneyGrabber:
    def __init__(self,
                 rules: Union[Dict[str, Any], Rules] = None,
                 fetcher_config=None,
                 extractor_config=None,
                 cleaner_config=None,
                 fetcher=None, 
                 parser_class=ContentParser, 
                 extractor_class=ContentExtractor,
                 cleaner=None, 
                 formatter=None, 
                 plugins=None, 
                 ):
        
        self._rules = None
        self.rules = rules or {}
        
        self.fetcher_config = fetcher_config or FetcherConfig()
        self.extractor_config = extractor_config
        self.cleaner_config = cleaner_config or CleanerConfig()

        self.fetcher = fetcher or Fetcher(fetcher_config=self.fetcher_config)
        self.parser_class = parser_class
        self.extractor_class = extractor_class
        self.cleaner = cleaner or Cleaner(cleaner_config=self.cleaner_config)
        self.formatter = formatter or OutputFormatter()
        self.plugins = plugins or []
        self.pipeline = [
            self._fetch_content,
            self._parse_content,
            self._extract_data,
            self._clean_data,
            self._apply_plugins
        ]


    @property
    def rules(self):
        return self._rules

    @rules.setter
    def rules(self, rules):
        if rules is None:
            self._rules = {}
        elif isinstance(rules, Rules):
            # Unwrap root model
            self._rules = rules.root
        elif isinstance(rules, dict):
            # Validate dict against Rules root model
            validated = Rules.model_validate(rules)
            self._rules = validated.root
        else:
            raise ValueError("Invalid rules format. Must be a dict or Rules object.")

    def register_plugin(self, plugin):
        if hasattr(plugin, 'process') and callable(getattr(plugin, 'process')):
            self.plugins.append(plugin)
        else:
            raise ValueError("Plugin must implement a callable 'process' method.")

    async def scrape_async(self, url, rules, fetch_method='fetch',fetcher_config=None, extractor_config=None, cleaner_config=None,**kwargs):
        
        context = {
            'url': url,
            'rules': rules,
            'fetch_method': fetch_method,
            'fetcher_config': fetcher_config or self.fetcher_config,
            'extractor_config': extractor_config or self.extractor_config,
            'cleaner_config': cleaner_config or self.cleaner_config,
            'kwargs': kwargs
        }
        for step in self.pipeline:
            await step(context)
        return context.get('data')

    async def scrape(self, url, rules, fetch_method='fetch', **kwargs):
        return await self.scrape_async(url, rules, fetch_method, **kwargs)
    
    def scrape_sync(self, url, rules, fetch_method='fetch', **kwargs):
        return asyncio.run(self.scrape_async(url, rules, fetch_method, **kwargs))

    async def scrape_multiple(self, urls, rules, fetch_method='fetch_multiple',fetcher_config=None, extractor_config=None, cleaner_config=None,**kwargs):
            if fetch_method == 'fetch_multiple':
                contents = await self.fetcher.fetch_multiple(urls, **kwargs)
            elif fetch_method == 'fetch_with_playwright_multiple':
                contents = await self.fetcher.fetch_with_playwright_multiple(urls, **kwargs)
            else:
                raise ValueError(f"Unknown fetch_method: {fetch_method}")

            results = []
            for i, (content, content_type) in enumerate(contents):
                context = {
                    'url': urls[i],
                    'content': content,
                    'content_type': content_type,
                    'rules': rules,
                    'fetch_method': fetch_method,
                    'fetcher_config': fetcher_config or self.fetcher_config,
                    'extractor_config': extractor_config or self.extractor_config,
                    'cleaner_config': cleaner_config or self.cleaner_config,
                    'kwargs': kwargs
                }
                # Process the rest of the pipeline
                for step in self.pipeline[1:]:  # Skip the _fetch_content step
                    await step(context)
                results.append(context.get('data'))
            return results

    async def scrape_with_pagination(self, url, rules, pagination_handler: PaginationHandler, **kwargs):
            """
            Scrape data across multiple pages using pagination.

            :param url: The starting URL.
            :param rules: The extraction rules.
            :param pagination_handler: An instance of PaginationHandler.
            :param kwargs: Additional arguments for scraping.
            :return: A list of aggregated data from all pages.
            """
            results = []
            current_url = url
            page_count = 0

            while current_url:
                data = await self.scrape(current_url, rules, **kwargs)
                results.append(data)

                # Create a ContentParser instance to use with PaginationHandler
                parser = self.parser_class(self.fetcher.last_content, self.fetcher.last_content_type)

                # Get the next page URL
                current_url = pagination_handler.get_next_page_url(parser, current_url)
                page_count += 1

                if pagination_handler.limit and page_count >= pagination_handler.limit:
                    break

            return results

    def output(self, data, format_type='json',structure_data=True):
            return self.formatter.format(data, format_type,structure_data)

    async def _fetch_content(self, context):
        fetch_function = getattr(self.fetcher, context['fetch_method'])
        kwargs = {
            'retries': getattr(context['fetcher_config'], 'retries', 3)
        }
        if context['fetch_method'] != 'fetch_with_playwright':
            kwargs['timeout'] = getattr(context['fetcher_config'], 'timeout', 10)
            
        content, content_type = await fetch_function(context['url'], **kwargs)

        context['content'] = content
        context['content_type'] = content_type
        
    async def _parse_content(self, context):
        parser = self.parser_class(context['content'], context['content_type'])
        context['parser'] = parser

    async def _extract_data(self, context):
        
        extractor = self.extractor_class(
            parser=context['parser'],
            rules=context['rules'],
            extractor_config=context['extractor_config']
        )
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
