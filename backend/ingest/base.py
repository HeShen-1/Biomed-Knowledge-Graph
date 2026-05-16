from abc import ABC, abstractmethod
from datetime import datetime
from typing import AsyncIterator
from ingest.models import NormalizedRecord
from ingest.serializers import safe_label, safe_relation


class BaseIngester(ABC):
    source_name: str
    batch_size: int = 500

    @abstractmethod
    async def fetch(self, since: datetime) -> AsyncIterator[dict]:
        ...

    @abstractmethod
    def normalize(self, record: dict) -> NormalizedRecord | None:
        ...

    def build_queries(self, batch: list[NormalizedRecord]) -> list[tuple[str, dict]]:
        statements: list[tuple[str, dict]] = []
        for i, record in enumerate(batch):
            for j, node in enumerate(record.nodes):
                label = safe_label(node.type)
                props = {k: v for k, v in node.properties.items() if v is not None}
                statements.append((
                    f"MERGE (n:{label} {{id: $id_{i}_{j}}}) SET n += $props_{i}_{j}",
                    {f"id_{i}_{j}": node.id, f"props_{i}_{j}": props},
                ))
            for k, edge in enumerate(record.edges):
                safe_relation(edge.relation)
                statements.append((
                    f"MATCH (a {{id: $from_{i}_{k}}}), (b {{id: $to_{i}_{k}}}) "
                    f"MERGE (a)-[:{edge.relation}]->(b)",
                    {f"from_{i}_{k}": edge.from_id, f"to_{i}_{k}": edge.to_id},
                ))
        return statements
