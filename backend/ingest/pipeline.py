import asyncio
import logging
from datetime import datetime, timezone
from typing import AsyncIterator
from ingest.base import BaseIngester
from ingest.models import NormalizedRecord
from ingest.serializers import batch_write
from ingest.stats import collect_stats

logger = logging.getLogger(__name__)


class Pipeline:
    def __init__(self, ingester: BaseIngester, rate_limit: float = 3.0, max_retries: int = 3):
        self.ingester = ingester
        self.rate_limit = rate_limit
        self.max_retries = max_retries

    async def run(self, since: datetime | None = None) -> dict:
        since = since or datetime.min.replace(tzinfo=timezone.utc)
        stats = {"added": 0, "updated": 0, "failed": 0, "source": self.ingester.source_name}
        batch: list[NormalizedRecord] = []

        async for raw in self._fetch_with_retry(since):
            try:
                record = self.ingester.normalize(raw)
            except Exception:
                logger.warning("normalize failed for record in %s", self.ingester.source_name)
                stats["failed"] += 1
                continue

            if record is None:
                continue

            batch.append(record)
            if len(batch) >= self.ingester.batch_size:
                await self._flush_batch(batch, stats)
                batch = []

        if batch:
            await self._flush_batch(batch, stats)

        await collect_stats(self.ingester.source_name, stats)
        return stats

    async def _fetch_with_retry(self, since: datetime) -> AsyncIterator[dict]:
        for attempt in range(self.max_retries):
            try:
                async for record in self.ingester.fetch(since):
                    yield record
                    await asyncio.sleep(1.0 / self.rate_limit)
                return
            except Exception:
                logger.error("fetch attempt %d failed for %s", attempt + 1, self.ingester.source_name)
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
        logger.error("all fetch attempts failed for %s", self.ingester.source_name)

    async def _flush_batch(self, batch: list[NormalizedRecord], stats: dict):
        queries = self.ingester.build_queries(batch)
        try:
            result = await batch_write(queries)
            stats["added"] += result["added"]
            stats["updated"] += result["updated"]
        except Exception:
            stats["failed"] += len(batch)
            logger.exception("batch write failed for %s", self.ingester.source_name)
