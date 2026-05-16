import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from ingest.base import BaseIngester
from ingest.models import NormalizedRecord, NormalizedNode
from ingest.pipeline import Pipeline


class FakeIngester(BaseIngester):
    source_name = "test"
    batch_size = 2

    async def fetch(self, since: datetime):
        for i in range(3):
            yield {"id": str(i), "name": f"item_{i}"}

    def normalize(self, record: dict) -> NormalizedRecord | None:
        return NormalizedRecord(
            nodes=[NormalizedNode(id=f"test:{record['id']}", type="test", properties=record)],
            edges=[],
            source=self.source_name,
            fetched_at=datetime.now(timezone.utc),
        )

    def build_queries(self, batch: list[NormalizedRecord]) -> list[str]:
        return [f"CREATE (n:Test {{id: '{r.nodes[0].id}'}})" for r in batch]


@pytest.mark.asyncio
async def test_pipeline_runs_all_records():
    ingester = FakeIngester()
    pipeline = Pipeline(ingester, rate_limit=100.0)

    with patch("ingest.pipeline.batch_write", new_callable=AsyncMock) as mock_write, \
         patch("ingest.pipeline.collect_stats", new_callable=AsyncMock) as mock_stats:
        mock_write.return_value = {"added": 1, "updated": 0}
        result = await pipeline.run()
        assert mock_write.call_count == 2  # batch_size=2, 3 items = 2 batches
        assert mock_stats.call_count == 1
        assert result["source"] == "test"


@pytest.mark.asyncio
async def test_pipeline_handles_normalize_failure():
    ingester = FakeIngester()

    def bad_normalize(record):
        if record["id"] == "1":
            raise ValueError("bad")
        return FakeIngester.normalize(ingester, record)

    ingester.normalize = bad_normalize
    pipeline = Pipeline(ingester, rate_limit=100.0)

    with patch("ingest.pipeline.batch_write", new_callable=AsyncMock) as mock_write, \
         patch("ingest.pipeline.collect_stats", new_callable=AsyncMock) as mock_stats:
        mock_write.return_value = {"added": 1, "updated": 0}
        result = await pipeline.run()
        assert result["failed"] == 1


@pytest.mark.asyncio
async def test_pipeline_handles_none_normalize():
    ingester = FakeIngester()
    ingester.normalize = lambda r: None
    pipeline = Pipeline(ingester, rate_limit=100.0)

    with patch("ingest.pipeline.batch_write", new_callable=AsyncMock) as mock_write, \
         patch("ingest.pipeline.collect_stats", new_callable=AsyncMock) as mock_stats:
        mock_write.return_value = {"added": 0, "updated": 0}
        result = await pipeline.run()
        assert mock_write.call_count == 0  # no records generated
