import asyncio
import logging
from datetime import datetime, timezone
from typing import AsyncIterator
from ingest.base import BaseIngester
from ingest.models import NormalizedRecord, NormalizedNode, NormalizedEdge

logger = logging.getLogger(__name__)


DISCOVERY_EFOS = [
    "EFO_0000305",  # breast carcinoma
    "EFO_0000311",  # lung carcinoma
    "EFO_0000220",  # colorectal cancer
    "EFO_0000246",  # Alzheimer's disease
    "EFO_0000729",  # type 2 diabetes mellitus
    "EFO_0000319",  # cardiovascular disease
    "EFO_0000685",  # immune system disease
    "EFO_0000384",  # leukemia
    "EFO_0000612",  # lymphoma
    "EFO_0000700",  # prostate carcinoma
]


class OpenTargetsIngester(BaseIngester):
    source_name = "opentargets"
    batch_size = 200

    async def fetch(self, since: datetime) -> AsyncIterator[dict]:
        import httpx

        query = """
        query TargetDisease($efoId: String!, $index: Int!, $size: Int!) {
          disease(efoId: $efoId) {
            id
            name
            associatedTargets(page: {index: $index, size: $size}) {
              rows {
                target { id approvedSymbol }
                score
              }
              count
            }
          }
        }
        """

        async with httpx.AsyncClient(timeout=30) as client:
            for efo_id in DISCOVERY_EFOS:
                index = 0
                while True:
                    resp = await client.post(
                        "https://api.platform.opentargets.org/api/v4/graphql",
                        json={
                            "query": query,
                            "variables": {"efoId": efo_id, "index": index, "size": self.batch_size},
                        },
                    )
                    data = resp.json()
                    if data.get("errors"):
                        logger.warning("OT error for %s: %s", efo_id, data["errors"][0]["message"][:100])
                        break

                    disease_data = data.get("data", {}).get("disease")
                    if not disease_data:
                        break

                    disease_id = disease_data.get("id", "")
                    disease_name = disease_data.get("name", "")
                    assoc = disease_data.get("associatedTargets", {})
                    rows = assoc.get("rows", [])
                    total = assoc.get("count", 0)

                    if not rows:
                        break

                    for row in rows:
                        row["_disease_id"] = disease_id
                        row["_disease_name"] = disease_name
                        yield row

                    index += 1
                    if index * self.batch_size >= total:
                        break
                    await asyncio.sleep(0.1)

    async def normalize(self, record: dict) -> NormalizedRecord | None:
        target = record.get("target", {})
        gene_symbol = target.get("approvedSymbol", "")
        gene_id = target.get("id", "")
        disease_id = record.get("_disease_id", "")
        disease_name = record.get("_disease_name", "")
        score = record.get("score", 0)

        if not gene_id or not disease_id:
            return None

        nodes: list[NormalizedNode] = [
            NormalizedNode(
                id=f"gene:{gene_symbol}", type="gene",
                properties={"symbol": gene_symbol, "ensembl_id": gene_id},
            ),
            NormalizedNode(
                id=f"disease:{disease_id}", type="disease",
                properties={"name": disease_name},
            ),
        ]

        edges: list[NormalizedEdge] = [
            NormalizedEdge(
                from_id=f"gene:{gene_symbol}",
                to_id=f"disease:{disease_id}",
                relation="TARGETS",
                from_type="gene", to_type="disease",
                properties={
                    "score": round(score, 4),
                    "source": "opentargets",
                },
            ),
        ]

        return NormalizedRecord(
            nodes=nodes,
            edges=edges,
            source=self.source_name,
            fetched_at=datetime.now(timezone.utc),
        )
