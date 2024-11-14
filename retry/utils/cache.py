from abc import ABC, abstractmethod
import time
from typing import Any, Optional

class CacheInterface(ABC):
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        pass

    @abstractmethod
    async def set(self, key: str, value: Any) -> None:
        pass

    @abstractmethod
    def contains(self, key: str) -> bool:
        pass

class SimpleCache(CacheInterface):
    def __init__(self, expiration: float = 300):
        self.expiration = expiration
        self.store = {}

    def contains(self, key: str) -> bool:
        if key in self.store:
            if (time.time() - self.store[key]['time']) < self.expiration:
                return True
            else:
                del self.store[key]
        return False

    async def get(self, key: str) -> Optional[Any]:
        if self.contains(key):
            return self.store[key]['value']
        else:
            return None  # or raise KeyError(f"Key '{key}' not found")

    async def set(self, key: str, value: Any) -> None:
        self.store[key] = {'value': value, 'time': time.time()}
