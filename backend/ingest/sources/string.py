from datetime import datetime, timezone
from typing import AsyncIterator
from ingest.base import BaseIngester
from ingest.models import NormalizedRecord, NormalizedNode, NormalizedEdge


class StringIngester(BaseIngester):
    source_name = "string"
    batch_size = 500

    async def fetch(self, since: datetime) -> AsyncIterator[dict]:
        import httpx
        base_url = "https://string-db.org/api/json/network"
        params = {
            "identifiers": "9606.%0A",  # Get all human PPI
            "species": 9606,
            "required_score": 700,  # minimum 0.7 score
            "limit": self.batch_size,
        }
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.get(base_url, params=params)
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

    def build_queries(self, batch: list[NormalizedRecord]) -> list[str]:
        queries: list[str] = []
        for record in batch:
            for node in record.nodes:
                parts = []
                for k, v in node.properties.items():
                    if v is not None:
                        parts.append(f"n.{k} = '{v}'" if isinstance(v, str) else f"n.{k} = {v}")
                props_str = ", ".join(parts)
                queries.append(
                    f"MERGE (n:Protein {{id: '{node.id}'}}) "
                    f"ON CREATE SET {props_str} ON MATCH SET {props_str}"
                )
            for edge in record.edges:
                queries.append(
                    f"MATCH (a {{id: '{edge.from_id}'}}), (b {{id: '{edge.to_id}'}}) "
                    f"MERGE (a)-[:{edge.relation}]->(b)"
                )
        return queries
