import asyncio
import aiohttp
import random
from honeygrabber.config.fetcher_config import FetcherConfig
from .utils.authentication import Authentication
from .utils.session_manager import SessionManager
from .utils.rate_limiter import RateLimiter
from playwright.async_api import async_playwright
from .logger import getLogger

logger = getLogger(__name__)


class Fetcher:
    def __init__(self, fetcher_config: FetcherConfig):
        """Initialize the Fetcher with a configuration object.
        
        Args:
            fetcher_config: Configuration object containing all fetcher settings
        """
        self.proxies = fetcher_config.proxies or []
        self.user_agents = fetcher_config.user_agents or [self.default_user_agent()]
        self.rate_limit = fetcher_config.rate_limit
        self.cache = fetcher_config.cache
        self.authentication = fetcher_config.authentication
        self.session_manager = fetcher_config.session_manager or SessionManager()
        
        self.rate_limiter = RateLimiter(self.rate_limit)
        self._headers = {'User-Agent': random.choice(self.user_agents)}
        self._proxy = None if not self.proxies else random.choice(self.proxies)

    @property
    def headers(self):
        if not hasattr(self, '_headers') or self._headers is None:
            self._headers = {'User-Agent': random.choice(self.user_agents)}
        return self._headers

    @headers.setter
    def headers(self, value):
        self._headers = value

    @property
    def proxy(self):
        if not hasattr(self, '_proxy') or self._proxy is None and self.proxies:
            self._proxy = random.choice(self.proxies)
        return self._proxy

    @proxy.setter
    def proxy(self, value):
        self._proxy = value

    async def fetch(self, url: str, retries=3, timeout=10):
        cache = await self._pre_flight(url)
        if cache:
            return cache

        async with self.session_manager as session:
            attempt = 0
            while attempt <= retries:
                try:
                    async with session.get(
                        url,
                        headers=self.headers,
                        proxy=self.proxy,
                        timeout=timeout
                    ) as response:
                        response.raise_for_status()
                        content_type = response.headers.get('Content-Type', '')
                        content = await response.text()

                        if self.cache is not None:
                            await self.cache.set(url, (content, content_type))

                        return content, content_type
                except Exception as e:
                    logger.error(f"HTTP error for URL {url}: {e}")
                    if attempt < retries:
                        await asyncio.sleep(2 ** attempt)
                        attempt += 1
                        continue
                    else:
                        raise e

    async def fetch_multiple(self, urls: list, retries=3, timeout=10):
        async with self.session_manager as session:
            tasks = []
            for url in urls:
                tasks.append(self._fetch_single(url, session, retries, timeout))
            results = await asyncio.gather(*tasks, return_exceptions=True)
        return results

    async def _fetch_single(self, url, session:aiohttp.ClientSession, retries, timeout):
        cache = await self._pre_flight(url)
        if cache:
            return cache
        attempt = 0
        while attempt <= retries:
            try:
                async with session.get(
                    url,
                    headers=self.headers,
                    proxy=self.proxy,
                    timeout=timeout
                ) as response:
                    response.raise_for_status()
                    content_type = response.headers.get('Content-Type', '')
                    content = await response.text()

                    if self.cache:
                        await self.cache.set(url, (content, content_type))
                        
                    return content, content_type
            except Exception as e:
                    logger.error(f"HTTP error for URL {url}: {e}")
                    if attempt < retries:
                        await asyncio.sleep(2 ** attempt)
                        attempt += 1
                        continue
                    else:
                        raise e

    # async def fetch_multiple(self, urls: list, retries=3, timeout=10):
    #     results = []
    #     async with self.session_manager as session:
    #         for url in urls:
    #             cache = await self._pre_flight(url)
    #             if cache:
    #                 results.append(cache)
    #                 continue

    #             attempt = 0
    #             while attempt <= retries:
    #                 try:
    #                     async with session.get(
    #                         url,
    #                         headers=self.headers,
    #                         proxy=self.proxy,
    #                         timeout=timeout
    #                     ) as response:
    #                         response.raise_for_status()
    #                         content_type = response.headers.get(
    #                             'Content-Type', '')
    #                         content = await response.text()

    #                         if self.cache:
    #                             await self.cache.set(url, (content, content_type))

    #                         results.append((content, content_type))
    #                         break
    #                 except Exception as e:
    #                     logger.error(f"HTTP error for URL {url}: {e}")
    #                     if attempt < retries:
    #                         await asyncio.sleep(2 ** attempt)
    #                         attempt += 1
    #                         continue
    #                     else:
    #                         raise e
    #     return results

    async def fetch_with_playwright(self, url, retries=3, timeout=10):
        cache = await self._pre_flight(url)
        if cache:
            return cache

        attempt = 0
        proxy_settings = None
        
        while attempt <= retries:
            try:
                async with async_playwright() as p:
                    
                    if self.proxy and self.proxy is not None:
                        proxy_settings = {
                            'server': self.proxy,
                        }

                    browser = await p.chromium.launch(proxy=proxy_settings)
                    if browser is None:
                        raise ValueError("Failed to launch browser")
                        
                    context = await browser.new_context(extra_http_headers=self.headers if hasattr(self, 'headers') and self.headers else {})
                    if context is None:
                        await browser.close()
                        raise ValueError("Failed to create browser context")
                        
                    page = await context.new_page()
                    if page is None:
                        await context.close()
                        await browser.close()
                        raise ValueError("Failed to create page")

                    response = await page.goto(url, timeout=timeout * 1000)
                    if response is None:
                        await page.close()
                        await context.close()
                        await browser.close()
                        raise ValueError(f"Failed to navigate to {url}")
                        
                    content = await page.content()

                    await browser.close()

                    if self.cache:
                        await self.cache.set(url, (content, 'text/html'))

                    return content, 'text/html'
            except Exception as e:
                logger.error(f"Error fetching URL with Playwright {url}: {e}")
                if attempt < retries:
                    await asyncio.sleep(2 ** attempt)
                    attempt += 1
                    continue
                else:
                    raise e

    async def fetch_with_playwright_multiple(self, urls: list, retries=3, timeout=10):
        
        _ = await self._pre_flight(None)
        
        try:
            async with async_playwright() as p:
                proxy_settings = None
                if self.proxy and self.proxy is not None:
                    proxy_settings = {'server': self.proxy}

                browser = await p.chromium.launch(proxy=proxy_settings)
                if browser is None:
                    raise ValueError("Failed to launch browser")
                
                context = await browser.new_context(extra_http_headers=self.headers if hasattr(self, 'headers') and self.headers else {})
                if context is None:
                    await browser.close()
                    raise ValueError("Failed to create browser context")

                tasks = [self._fetch_page_with_playwright(url, context, retries, timeout) for url in urls]
                
                results = await asyncio.gather(*tasks, return_exceptions=True)

                await context.close()
                await browser.close()
            return results
        except Exception as e:
            logger.error(f"Error in fetch_with_playwright_multiple: {e}")
            raise e

    async def _fetch_page_with_playwright(self, url, context, retries, timeout):
        attempt = 0
        
        cache = await self._pre_flight(url)
        if cache:
            return cache
        
        while attempt <= retries:
            try:
                page = await context.new_page()
                if page is None:
                    raise ValueError("Failed to create page")
                
                response = await page.goto(url, timeout=timeout * 1000)
                if response is None:
                    await page.close()
                    raise ValueError(f"Failed to navigate to {url}")
                
                content = await page.content()
                await page.close()

                if self.cache:
                    await self.cache.set(url, (content, 'text/html'))
                return content, 'text/html'
            
            except Exception as e:
                    logger.error(f"Error fetching URL with Playwright {url}: {e}")
                    if attempt < retries:
                        await asyncio.sleep(2 ** attempt)
                        attempt += 1
                        continue
                    else:
                        raise e

    # async def fetch_with_playwright_multiple(self, urls: list, retries=3, timeout=10):
    #     results = []
    #     for url in urls:
    #         cache = await self._pre_flight(url)
    #         if cache:
    #             results.append(cache)
    #             continue

    #         attempt = 0
    #         while attempt <= retries:
    #             try:
    #                 async with async_playwright() as p:
    #                     proxy_settings = None
    #                     if self.proxy:
    #                         proxy_settings = {
    #                             'server': self.proxy,
    #                         }

    #                     browser = await p.chromium.launch(proxy=proxy_settings)
    #                     context = await browser.new_context(extra_http_headers=self.headers)
    #                     page = await context.new_page()

    #                     await page.goto(url, timeout=timeout * 1000)
    #                     content = await page.content()

    #                     await browser.close()

    #                     if self.cache:
    #                         await self.cache.set(url, (content, 'text/html'))

    #                     results.append((content, 'text/html'))
    #                     break
    #             except Exception as e:
    #                 logger.error(f"Error fetching URL with Playwright {url}: {e}")
    #                 if attempt < retries:
    #                     await asyncio.sleep(2 ** attempt)
    #                     attempt += 1
    #                     continue
    #                 else:
    #                     raise e
    #     return results

    async def _pre_flight(self, url) -> str | None:
        if url is None:
            # Initialize headers and proxy for a new session but don't try to cache
            self.headers = {'User-Agent': random.choice(self.user_agents)}
            # Apply authentication headers for new session if available
            if self.authentication:
                if hasattr(self.authentication, 'get_auth'):
                    auth = self.authentication.get_auth()
                    if auth:
                        if isinstance(auth, aiohttp.BasicAuth):
                            auth_header = auth.encode()
                            self.headers.update({'Authorization': auth_header})
                        elif isinstance(auth, dict):
                            self.headers.update(auth)
                elif hasattr(self.authentication, 'get_headers'):
                    headers = self.authentication.get_headers()
                    if headers:
                        self.headers.update(headers)
                elif hasattr(self.authentication, 'get_auth_for_aiohttp'):
                    auth = self.authentication.get_auth_for_aiohttp()
                    if auth:
                        auth_header = auth.encode()
                        self.headers.update({'Authorization': auth_header})
            self.proxy = random.choice(self.proxies) if self.proxies else None
            return None
            
        if self.cache and self.cache.contains(url):
            logger.info(f"Cache hit for URL: {url}")
            return await self.cache.get(url)

        await self.rate_limiter.wait(url)

        self.headers = {'User-Agent': random.choice(self.user_agents)}

        if self.authentication:
            if hasattr(self.authentication, 'get_auth'):
                auth = self.authentication.get_auth()
                if auth:
                    if isinstance(auth, aiohttp.BasicAuth):
                        auth_header = auth.encode()
                        self.headers.update({'Authorization': auth_header})
                    elif isinstance(auth, dict):
                        self.headers.update(auth)
            elif hasattr(self.authentication, 'get_headers'):
                headers = self.authentication.get_headers()
                if headers:
                    self.headers.update(headers)
            elif hasattr(self.authentication, 'get_auth_for_aiohttp'):
                auth = self.authentication.get_auth_for_aiohttp()
                if auth:
                    auth_header = auth.encode()
                    self.headers.update({'Authorization': auth_header})

        self.proxy = random.choice(self.proxies) if self.proxies else None

        return None

    async def __aenter__(self):
        await self.session_manager.open()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session_manager.close()

    @staticmethod
    def default_user_agent():
        return "Mozilla/5.0 (compatible; Retry/1.0; +https://example.com/bot)"
