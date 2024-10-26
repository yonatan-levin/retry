import asyncio
import time

class RateLimiter:
    def __init__(self, rate_limit):
        """
        Initialize the RateLimiter.

        :param rate_limit: The minimum number of seconds to wait between requests.
        """
        self.rate_limit = rate_limit
        self._lock = asyncio.Lock()
        self._last_request_time = None

    async def wait(self):
        """
        Waits for the appropriate amount of time to respect the rate limit.
        """
        async with self._lock:
            if self._last_request_time is not None:
                elapsed = time.time() - self._last_request_time
                wait_time = self.rate_limit - elapsed
                if wait_time > 0:
                    await asyncio.sleep(wait_time)
            self._last_request_time = time.time()
