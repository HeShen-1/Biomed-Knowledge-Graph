import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch
from ingest.base import BaseIngester
from ingest.models import NormalizedRecord, NormalizedNode
from ingest.pipeline import Pipeline


class FakeIngester(BaseIngester):
    source_name = "test"
    batch_size = 2

    async def fetch(self, since: datetime):
        for i in range(3):
            yield {"id": str(i), "name": f"item_{i}"}

    async def normalize(self, record: dict) -> NormalizedRecord | None:
        return NormalizedRecord(
            nodes=[NormalizedNode(id=f"gene:TEST{record['id']}", type="gene", properties=record)],
            edges=[],
            source=self.source_name,
            fetched_at=datetime.now(timezone.utc),
        )


@pytest.mark.asyncio
async def test_pipeline_runs_all_records():
    ingester = FakeIngester()
    pipeline = Pipeline(ingester, rate_limit=100.0)

    with patch("ingest.pipeline.batch_write", new_callable=AsyncMock) as mock_write, \
         patch("ingest.pipeline.sync_search_index", new_callable=AsyncMock) as mock_search, \
         patch("ingest.pipeline.collect_stats", new_callable=AsyncMock) as mock_stats:
        mock_write.return_value = {"added": 1, "updated": 0}
        result = await pipeline.run()
        assert mock_write.call_count == 2
        statements = mock_write.call_args[0][0]
        assert isinstance(statements, list)
        assert isinstance(statements[0], tuple)
        assert mock_search.call_count == 2
        assert mock_stats.call_count == 1
        assert result["source"] == "test"


@pytest.mark.asyncio
async def test_pipeline_handles_normalize_failure():
    ingester = FakeIngester()

    async def bad_normalize(record):
        if record["id"] == "1":
            raise ValueError("bad")
        return await FakeIngester.normalize(ingester, record)

    ingester.normalize = bad_normalize
    pipeline = Pipeline(ingester, rate_limit=100.0)

    with patch("ingest.pipeline.batch_write", new_callable=AsyncMock) as mock_write, \
         patch("ingest.pipeline.sync_search_index", new_callable=AsyncMock), \
         patch("ingest.pipeline.collect_stats", new_callable=AsyncMock) as mock_stats:
        mock_write.return_value = {"added": 1, "updated": 0}
        result = await pipeline.run()
        assert result["failed"] == 1


@pytest.mark.asyncio
async def test_pipeline_handles_none_normalize():
    ingester = FakeIngester()
    async def none_normalize(record):
        return None

    ingester.normalize = none_normalize
    pipeline = Pipeline(ingester, rate_limit=100.0)

    with patch("ingest.pipeline.batch_write", new_callable=AsyncMock) as mock_write, \
         patch("ingest.pipeline.sync_search_index", new_callable=AsyncMock), \
         patch("ingest.pipeline.collect_stats", new_callable=AsyncMock) as mock_stats:
        mock_write.return_value = {"added": 0, "updated": 0}
        result = await pipeline.run()
        assert mock_write.call_count == 0


@pytest.mark.asyncio
async def test_pipeline_passes_since_to_fetch():
    ingester = FakeIngester()
    fetched_since = []

    async def tracking_fetch(since):
        fetched_since.append(since)
        async for r in FakeIngester.fetch(ingester, since):
            yield r

    ingester.fetch = tracking_fetch
    pipeline = Pipeline(ingester, rate_limit=100.0)

    ref_date = datetime(2024, 1, 1, tzinfo=timezone.utc)
    with patch("ingest.pipeline.batch_write", new_callable=AsyncMock) as mock_write, \
         patch("ingest.pipeline.sync_search_index", new_callable=AsyncMock), \
         patch("ingest.pipeline.collect_stats", new_callable=AsyncMock):
        mock_write.return_value = {"added": 1, "updated": 0}
        await pipeline.run(since=ref_date)
    assert fetched_since[0] == ref_date
