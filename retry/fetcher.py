import asyncio
import aiohttp
import random
from retry.config.fetcher_config import FetcherConfig
from .utils.authentication import Authentication
from .utils.session_manager import SessionManager
from .utils.rate_limiter import RateLimiter
from playwright.async_api import async_playwright
from .logger import logger

logger.name = 'fetcher'

class Fetcher:
    def __init__(self, 
                proxies:list[str]=None, 
                user_agents=None, 
                rate_limit=1, 
                cache=None, 
                authentication: Authentication = None, 
                session_manager=None,
                fetcher_config:FetcherConfig=None):
        if fetcher_config:
            self.proxies = fetcher_config.proxies or proxies or []
            self.user_agents = fetcher_config.user_agents or user_agents or [self.default_user_agent()]
            self.rate_limit = fetcher_config.rate_limit or rate_limit
            self.cache = fetcher_config.cache or cache
            self.authentication = fetcher_config.authentication or authentication
            self.session_manager = fetcher_config.session_manager or session_manager or SessionManager()
        else:
            self.proxies = proxies or []
            self.user_agents = user_agents or [self.default_user_agent()]
            self.rate_limit = rate_limit
            self.cache = cache
            self.authentication = authentication
            self.session_manager = session_manager or SessionManager()
        self.rate_limiter = RateLimiter(self.rate_limit)

    async def fetch(self, url, retries=3,timeout=10):
        cache = await self._pre_flight(url)
        if cache:
            return cache

        try:
            async with self.session_manager as session:
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
                       await self.cache.set(url,(content, content_type))

                    return content, content_type
        except Exception as e:
            logger.error(f"HTTP error for URL {url}: {e}")
            if retries > 0:
                await asyncio.sleep(2 ** (3 - retries))
                return await self.fetch(url, retries - 1,timeout)
            else:
                raise e
 
    async def fetch_with_playwright(self, url, retries=3):
        cache = await self._pre_flight(url)
        if cache:
            return cache
        try:

            async with async_playwright() as p:
                proxy_settings = None
                if self.proxy:
                    proxy_settings = {
                        'server': self.proxy,
                        # Add 'username' and 'password' if required ??
                    }

                browser = await p.chromium.launch(proxy=proxy_settings)
                context = await browser.new_context(extra_http_headers=self.headers)
                page = await context.new_page()

                await page.goto(url)
                content = await page.content()

                await browser.close()

                if self.cache:
                   await self.cache.set(url, content)

                return content, 'text/html'
        except Exception as e:
            logger.error(f"Error fetching URL with Playwright {url}: {e}")
            if retries > 0:
                await asyncio.sleep(2 ** (3 - retries))
                return await self.fetch_with_playwright(url, retries - 1)
            else:
                raise e

    async def _pre_flight(self, url) -> str|None:
        if self.cache and self.cache.contains(url):
            logger.info(f"Cache hit for URL: {url}")
            return await self.cache.get(url)

        await self.rate_limiter.wait()

        self.headers = {'User-Agent': random.choice(self.user_agents)}

        if self.authentication:
            auth = self.authentication.get_auth()
            if auth:
                if isinstance(auth, aiohttp.BasicAuth):
                    auth_header = auth.encode()
                    self.headers.update({'Authorization': auth_header})
                elif isinstance(auth, dict):
                    self.headers.update(auth)
                
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
