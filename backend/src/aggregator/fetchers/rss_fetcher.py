"""
Seeker Bot — RSS/Atom feed fetcher.

Fetches RSS/Atom XML content over HTTP using aiohttp.
"""

import asyncio

import aiohttp

from src.aggregator.fetchers.base import BaseFetcher
from src.common.exceptions import FetchError
from src.common.logging import logger


class RSSFetcher(BaseFetcher):
    """Fetches RSS/Atom feed content via HTTP GET."""

    USER_AGENT = "SeekerBot/1.0"

    async def fetch(self, source) -> bytes | None:
        """Fetch RSS/Atom feed XML.

        Args:
            source: ContentSource with feed_url, timeout_seconds.

        Returns:
            Raw feed XML as bytes.

        Raises:
            FetchError: On HTTP error or timeout.
        """
        headers = {"User-Agent": self.USER_AGENT}
        timeout = aiohttp.ClientTimeout(total=source.timeout_seconds or 30)

        try:
            async with aiohttp.ClientSession(headers=headers) as session:
                logger.debug(
                    "rss_fetch_start",
                    url=source.feed_url,
                    source=source.slug,
                )
                async with session.get(
                    source.feed_url,
                    timeout=timeout,
                ) as response:
                    if response.status != 200:
                        raise FetchError(
                            f"HTTP {response.status} for {source.feed_url}"
                        )
                    data = await response.read()
                    logger.debug(
                        "rss_fetch_success",
                        url=source.feed_url,
                        bytes=len(data),
                    )
                    return data

        except asyncio.TimeoutError:
            logger.warning("rss_fetch_timeout", url=source.feed_url)
            raise FetchError(f"Timeout fetching {source.feed_url}")
        except aiohttp.ClientError as e:
            logger.warning("rss_fetch_error", url=source.feed_url, error=str(e))
            raise FetchError(f"Network error fetching {source.feed_url}: {e}")
