"""
Seeker Bot — Abstract base parser for content sources.

All parsers must implement parse() and return list[RawEvent].
"""

from abc import ABC, abstractmethod


class BaseParser(ABC):
    """Abstract base for content source parsers."""

    @abstractmethod
    async def parse(self, raw_data: bytes, source) -> list:
        """Parse raw data into a list of RawEvent objects.

        Args:
            raw_data: Raw bytes from the fetcher.
            source: ContentSource DB model instance.

        Returns:
            List of RawEvent objects.

        Raises:
            ParseError: If parsing fails.
        """
        ...
