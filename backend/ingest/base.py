from abc import ABC, abstractmethod
from datetime import datetime
from typing import AsyncIterator
from ingest.models import NormalizedRecord


class BaseIngester(ABC):
    source_name: str
    batch_size: int = 500

    @abstractmethod
    async def fetch(self, since: datetime) -> AsyncIterator[dict]:
        ...

    @abstractmethod
    def normalize(self, record: dict) -> NormalizedRecord | None:
        ...

    @abstractmethod
    def build_queries(self, batch: list[NormalizedRecord]) -> list[str]:
        ...
