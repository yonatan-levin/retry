from dataclasses import dataclass
from ..utils.authentication import Authentication
from ..utils.cache import BaseCache
from ..utils.session_manager import SessionManager


@dataclass
class FetcherConfig:
    fetch_method: str = 'fetch'
    retries: int = 3
    rate_limit: int = 1
    timeout: int = 10
    user_agents: str = None
    proxies: list[str] = None
    cache: BaseCache = None
    authentication: Authentication = None
    session_manager: SessionManager = None
    

    def __post_init__(self):
        if self.fetch_method not in ['fetch', 'fetch_once', 'fetch_with_playwright']:
            raise ValueError(f"Invalid fetch method: {self.fetch_method}")

        if self.retries < 0:
            raise ValueError("retries must be a non-negative integer")

        if self.timeout < 0:
            raise ValueError("timeout must be a non-negative integer")
        
        if self.rate_limit < 0:
            raise ValueError("rate_limit must be a non-negative integer")
