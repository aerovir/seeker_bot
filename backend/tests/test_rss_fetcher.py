"""
Tests for RSS fetcher — RSSFetcher.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.common.exceptions import FetchError


@pytest.fixture
def mock_source():
    """Create a minimal ContentSource-like object for testing."""
    from src.db.models.source import ContentSource
    from src.common.constants import SourceType, SourceStatus

    return ContentSource(
        id=1,
        name="Test RSS",
        slug="test-rss",
        source_type=SourceType.RSS,
        feed_url="https://example.com/rss",
        status=SourceStatus.ACTIVE,
        timeout_seconds=30,
    )


class TestRSSFetcher:
    @pytest.mark.asyncio
    async def test_fetch_success(self, mock_source):
        """RSSFetcher returns bytes on successful HTTP response."""
        from src.aggregator.fetchers.rss_fetcher import RSSFetcher

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.__aenter__.return_value = mock_response
        mock_response.read.return_value = b"<rss><item>test</item></rss>"

        mock_get = MagicMock(return_value=mock_response)

        mock_session = AsyncMock()
        mock_session.__aenter__.return_value.get = mock_get

        fetcher = RSSFetcher()
        with patch("aiohttp.ClientSession", return_value=mock_session):
            result = await fetcher.fetch(mock_source)

        assert result == b"<rss><item>test</item></rss>"

    @pytest.mark.asyncio
    async def test_fetch_http_error(self, mock_source):
        """RSSFetcher raises FetchError on non-200 response."""
        from src.aggregator.fetchers.rss_fetcher import RSSFetcher

        mock_response = AsyncMock()
        mock_response.status = 404
        mock_response.__aenter__.return_value = mock_response

        mock_get = MagicMock(return_value=mock_response)

        mock_session = AsyncMock()
        mock_session.__aenter__.return_value.get = mock_get

        fetcher = RSSFetcher()
        with patch("aiohttp.ClientSession", return_value=mock_session):
            with pytest.raises(FetchError, match="HTTP 404"):
                await fetcher.fetch(mock_source)

    @pytest.mark.asyncio
    async def test_fetch_timeout(self, mock_source):
        """RSSFetcher raises FetchError on timeout."""
        from src.aggregator.fetchers.rss_fetcher import RSSFetcher
        import asyncio

        mock_get = MagicMock(side_effect=asyncio.TimeoutError())

        mock_session = AsyncMock()
        mock_session.__aenter__.return_value.get = mock_get

        fetcher = RSSFetcher()
        with patch("aiohttp.ClientSession", return_value=mock_session):
            with pytest.raises(FetchError):
                await fetcher.fetch(mock_source)
