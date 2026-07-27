"""
Tests for AggregationPipeline — full content pipeline orchestration.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestAggregationPipeline:
    @pytest.mark.asyncio
    async def test_pipeline_execute_full(self):
        """Pipeline runs fetch → parse → classify → dedup → enrich → store."""
        from src.aggregator.pipeline import AggregationPipeline
        from src.db.models.source import ContentSource
        from src.common.constants import SourceType, SourceStatus

        source = ContentSource(
            id=1, name="Test", slug="test", source_type=SourceType.RSS,
            feed_url="https://example.com/rss", status=SourceStatus.ACTIVE,
            timeout_seconds=30,
        )

        mock_session = AsyncMock()
        mock_session.get = AsyncMock(return_value=source)

        pipeline = AggregationPipeline(mock_session, source)

        from src.aggregator.models import RawEvent

        with patch("src.aggregator.pipeline.RSSFetcher") as mock_fetcher_cls, \
             patch("src.aggregator.pipeline.RSSParser") as mock_parser_cls, \
             patch("src.aggregator.pipeline.CategoryClassifier") as mock_cc_cls, \
             patch("src.aggregator.pipeline.CityClassifier") as mock_ci_cls, \
             patch("src.aggregator.pipeline.Deduplicator") as mock_dedup_cls, \
             patch("src.aggregator.pipeline.Enricher") as mock_enr_cls, \
             patch("src.aggregator.pipeline.EventService") as mock_es_cls:

            # 1. Fetch
            mock_fetcher = MagicMock()
            mock_fetcher.fetch = AsyncMock(return_value=b"<rss/>")
            mock_fetcher_cls.return_value = mock_fetcher

            # 2. Parse
            mock_parser = MagicMock()
            mock_parser.parse = AsyncMock(return_value=[
                RawEvent(title="Event 1", content_source_id=1, source_slug="test", source_item_guid="guid-1"),
                RawEvent(title="Event 2", content_source_id=1, source_slug="test", source_item_guid="guid-2"),
            ])
            mock_parser_cls.return_value = mock_parser

            # 3. Classifiers
            mock_cc = MagicMock()
            mock_cc.load_categories = AsyncMock()
            mock_cc.classify.return_value = [(1, 0.9, "keyword")]
            mock_cc_cls.return_value = mock_cc

            mock_ci = MagicMock()
            mock_ci.build_index = AsyncMock()
            mock_ci.extract.return_value = [(1, 1.0, "gazetteer")]
            mock_ci_cls.return_value = mock_ci

            # 4. Dedup
            mock_dedup = MagicMock()
            mock_dedup.build_index = AsyncMock()
            mock_dedup.filter_new = AsyncMock(return_value=[
                RawEvent(title="Event 1", content_source_id=1, source_slug="test", source_item_guid="guid-1"),
            ])
            mock_dedup_cls.return_value = mock_dedup

            # 5. Enrich
            mock_enr = MagicMock()
            mock_enr.enrich_all.return_value = [MagicMock(title="Event 1")]
            mock_enr_cls.return_value = mock_enr

            # 6. Store
            mock_es = MagicMock()
            mock_es.create_from_raw = AsyncMock(return_value=MagicMock(id=1))
            mock_es_cls.return_value = mock_es

            result = await pipeline.execute()

        assert result is not None
        assert len(result.created) == 1
        assert result.created[0].id == 1

    @pytest.mark.asyncio
    async def test_pipeline_skip_empty_fetch(self):
        """Pipeline skips if fetch returns no data."""
        from src.aggregator.pipeline import AggregationPipeline
        from src.db.models.source import ContentSource
        from src.common.constants import SourceType, SourceStatus

        source = ContentSource(
            id=1, name="Test", slug="test", source_type=SourceType.RSS,
            feed_url="https://example.com/rss", status=SourceStatus.ACTIVE,
            timeout_seconds=30,
        )

        mock_session = AsyncMock()

        pipeline = AggregationPipeline(mock_session, source)

        with patch("src.aggregator.pipeline.RSSFetcher") as mock_fetcher_cls:
            mock_fetcher = MagicMock()
            mock_fetcher.fetch = AsyncMock(return_value=None)
            mock_fetcher_cls.return_value = mock_fetcher

            result = await pipeline.execute()

        assert result.skipped is True
        assert result.reason == "empty_fetch"
