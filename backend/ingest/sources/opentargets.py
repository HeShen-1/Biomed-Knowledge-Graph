from datetime import datetime, timezone
from typing import AsyncIterator
from ingest.base import BaseIngester
from ingest.models import NormalizedRecord, NormalizedNode, NormalizedEdge


class OpenTargetsIngester(BaseIngester):
    source_name = "opentargets"
    batch_size = 500

    async def fetch(self, since: datetime) -> AsyncIterator[dict]:
        import httpx
        base_url = "https://api.platform.opentargets.org/api/v4/graphql"
        query = """
        query TargetDiseaseAssociations($cursor: String) {
          diseases {
            associatedTargets(page: { size: 500, cursor: $cursor }) {
              rows {
                target { id approvedSymbol }
                disease { id name }
                score
                datasourceScores { componentId score }
              }
              cursor
            }
          }
        }
        """
        async with httpx.AsyncClient(timeout=30) as client:
            cursor = None
            while True:
                response = await client.post(base_url, json={"query": query, "variables": {"cursor": cursor}})
                data = response.json()
                assoc = data.get("data", {}).get("diseases", {}).get("associatedTargets", {})
                rows = assoc.get("rows", [])
                if not rows:
                    break
                for row in rows:
                    yield row
                cursor = assoc.get("cursor")
                if not cursor:
                    break

    def normalize(self, record: dict) -> NormalizedRecord | None:
        target = record.get("target", {})
        disease = record.get("disease", {})
        gene_id = target.get("id", "")
        gene_symbol = target.get("approvedSymbol", "")
        disease_id = disease.get("id", "")
        disease_name = disease.get("name", "")
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

        evidence_sources = [
            ds.get("componentId", "") for ds in record.get("datasourceScores", [])
        ]

        edges: list[NormalizedEdge] = [
            NormalizedEdge(
                from_id=f"gene:{gene_symbol}", to_id=f"disease:{disease_id}",
                relation="TARGETS",
                properties={"score": score, "evidence_sources": evidence_sources, "source": "opentargets"},
            ),
        ]

        return NormalizedRecord(
            nodes=nodes, edges=edges,
            source=self.source_name, fetched_at=datetime.now(timezone.utc),
        )

