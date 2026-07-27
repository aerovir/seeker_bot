"""
Seeker Bot — Abstract base fetcher for content sources.

All fetchers must implement fetch() and return raw bytes.
"""

from abc import ABC, abstractmethod


class BaseFetcher(ABC):
    """Abstract base for content source fetchers."""

    @abstractmethod
    async def fetch(self, source) -> bytes | None:
        """Fetch raw data from a content source.

        Args:
            source: ContentSource DB model instance.

        Returns:
            Raw bytes of the content, or None if the source returned empty data.

        Raises:
            FetchError: If the fetch fails (network, HTTP error, timeout).
        """
        ...
