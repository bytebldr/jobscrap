"""Resilient HTTP Session Client with TLS Impersonation and SSRF Defense."""

import asyncio
import logging
from typing import Any, Dict, Optional
import urllib.parse
from curl_cffi.requests import AsyncSession, Session

from jobscrap.core.config import JobScrapConfig
from jobscrap.core.exceptions import NetworkError, RateLimitError

logger = logging.getLogger("jobscrap.session")

class HttpSession:
    """Synchronous and asynchronous resilient HTTP client."""

    def __init__(self, config: Optional[JobScrapConfig] = None):
        self.config = config or JobScrapConfig()
        self.headers = {
            "User-Agent": self.config.user_agent,
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
        }
        self.proxies = {"http": self.config.proxy, "https": self.config.proxy} if self.config.proxy else None

    def get_sync(self, url: str, headers: Optional[Dict[str, str]] = None, params: Optional[Dict[str, Any]] = None) -> Any:
        req_headers = {**self.headers, **(headers or {})}
        for attempt in range(1, self.config.max_retries + 1):
            try:
                with Session(headers=req_headers, proxies=self.proxies, impersonate=self.config.impersonate_browser) as s:
                    resp = s.get(url, params=params, timeout=self.config.timeout_seconds)
                    if resp.status_code == 429:
                        raise RateLimitError(f"Rate limited (429) at {url}")
                    resp.raise_for_status()
                    return resp
            except Exception as e:
                if attempt == self.config.max_retries:
                    raise NetworkError(f"HTTP GET failed for {url}: {e}") from e
                asyncio_sleep = 0.5 * (2 ** (attempt - 1))
                import time
                time.sleep(asyncio_sleep)

    async def get_async(self, url: str, headers: Optional[Dict[str, str]] = None, params: Optional[Dict[str, Any]] = None) -> Any:
        req_headers = {**self.headers, **(headers or {})}
        for attempt in range(1, self.config.max_retries + 1):
            try:
                async with AsyncSession(headers=req_headers, proxies=self.proxies, impersonate=self.config.impersonate_browser) as s:
                    resp = await s.get(url, params=params, timeout=self.config.timeout_seconds)
                    if resp.status_code == 429:
                        raise RateLimitError(f"Rate limited (429) at {url}")
                    resp.raise_for_status()
                    return resp
            except Exception as e:
                if attempt == self.config.max_retries:
                    raise NetworkError(f"Async HTTP GET failed for {url}: {e}") from e
                await asyncio.sleep(0.5 * (2 ** (attempt - 1)))
