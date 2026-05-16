from datetime import datetime, timezone
from typing import AsyncIterator
from ingest.base import BaseIngester
from ingest.models import NormalizedRecord, NormalizedNode, NormalizedEdge


class StringIngester(BaseIngester):
    source_name = "string"
    batch_size = 500

    async def fetch(self, since: datetime) -> AsyncIterator[dict]:
        import httpx
        url = (
            "https://string-db.org/api/json/network"
            "?identifiers=9606.%0A"
            f"&species=9606"
            f"&required_score=700"
            f"&limit={self.batch_size}"
        )
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.get(url)
            data = response.json()
            for row in data:
                yield row

    def normalize(self, record: dict) -> NormalizedRecord | None:
        protein_a = record.get("preferredName_A") or record.get("stringId_A", "")
        protein_b = record.get("preferredName_B") or record.get("stringId_B", "")
        score = record.get("score", 0) / 1000.0  # STRING score is 0-1000, normalize to 0-1

        if not protein_a or not protein_b or score < 0.7:
            return None

        nodes: list[NormalizedNode] = [
            NormalizedNode(id=f"protein:{protein_a}", type="protein", properties={"name": protein_a}),
            NormalizedNode(id=f"protein:{protein_b}", type="protein", properties={"name": protein_b}),
        ]

        edges: list[NormalizedEdge] = [
            NormalizedEdge(
                from_id=f"protein:{protein_a}", to_id=f"protein:{protein_b}",
                relation="INTERACTS_WITH",
                properties={
                    "score": round(score, 4),
                    "evidence": record.get("escore", 0),
                    "source": "string",
                },
            ),
        ]

        return NormalizedRecord(
            nodes=nodes, edges=edges,
            source=self.source_name, fetched_at=datetime.now(timezone.utc),
        )

