from datetime import datetime, timezone
from typing import AsyncIterator
from ingest.base import BaseIngester
from ingest.models import NormalizedRecord, NormalizedNode, NormalizedEdge
from ingest.resolvers.gene import resolve_gene_symbols


class StringIngester(BaseIngester):
    source_name = "string"
    batch_size = 500

    async def fetch(self, since: datetime) -> AsyncIterator[dict]:
        import httpx

        # Well-known cancer-related genes for STRING query
        KEY_GENES = [
            "TP53", "BRCA1", "BRCA2", "EGFR", "KRAS", "PTEN", "MYC",
            "VEGFA", "AKT1", "MTOR", "ALK", "ERBB2", "BRAF", "PIK3CA",
            "RB1", "NF1", "KIT", "PDGFRA", "RET", "MET", "CTNNB1",
            "NOTCH1", "CDKN2A", "MLH1", "MSH2", "APC", "SMAD4",
            "ABL1", "JAK2", "FLT3", "NPM1", "IDH1", "IDH2", "FGFR3",
            "GNAQ", "GNA11", "HRAS", "NRAS", "MAP2K1", "MAP2K2",
        ]

        identifier_str = "%0A".join(KEY_GENES)
        url = (
            "https://string-db.org/api/json/network"
            f"?identifiers={identifier_str}"
            f"&species=9606"
            f"&required_score=700"
            f"&limit=1000"
        )
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.get(url)
            data = response.json()
            for row in data:
                if isinstance(row, dict) and "preferredName_A" in row:
                    yield row

    async def normalize(self, record: dict) -> NormalizedRecord | None:
        protein_a = record.get("preferredName_A") or record.get("stringId_A", "")
        protein_b = record.get("preferredName_B") or record.get("stringId_B", "")
        score = record.get("score", 0) / 1000.0

        if not protein_a or not protein_b or score < 0.7:
            return None

        resolved = await resolve_gene_symbols([protein_a, protein_b])
        protein_a_id = resolved.get(protein_a, f"protein:{protein_a}")
        protein_b_id = resolved.get(protein_b, f"protein:{protein_b}")

        nodes: list[NormalizedNode] = [
            NormalizedNode(id=protein_a_id, type="protein", properties={"name": protein_a}),
            NormalizedNode(id=protein_b_id, type="protein", properties={"name": protein_b}),
        ]

        edges: list[NormalizedEdge] = [
            NormalizedEdge(
                from_id=protein_a_id, to_id=protein_b_id,
                relation="INTERACTS_WITH",
                from_type="protein", to_type="protein",
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
