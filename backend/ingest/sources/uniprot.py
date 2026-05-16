from datetime import datetime, timezone
from typing import AsyncIterator
from ingest.base import BaseIngester
from ingest.models import NormalizedRecord, NormalizedNode, NormalizedEdge


class UniProtIngester(BaseIngester):
    source_name = "uniprot"
    batch_size = 500

    async def fetch(self, since: datetime) -> AsyncIterator[dict]:
        import httpx
        base_url = "https://rest.uniprot.org/uniprotkb/search"
        params = {
            "query": "reviewed:true AND organism_id:9606",
            "format": "json",
            "size": self.batch_size,
        }
        async with httpx.AsyncClient(timeout=30) as client:
            url = f"{base_url}?{'&'.join(f'{k}={v}' for k, v in params.items())}"
            while url:
                response = await client.get(url)
                data = response.json()
                for entry in data.get("results", []):
                    yield entry
                url = response.headers.get("Link", "")
                if 'rel="next"' in url:
                    url = url.split(";")[0].strip("<>")
                else:
                    break

    def normalize(self, record: dict) -> NormalizedRecord | None:
        accession = record.get("primaryAccession")
        if not accession:
            return None

        protein_id = f"protein:{accession}"
        gene_name = record.get("genes", [{}])[0].get("geneName", {}).get("value", "")
        protein_name = (
            record.get("proteinDescription", {})
            .get("recommendedName", {})
            .get("fullName", {})
            .get("value", "")
        )
        sequence = record.get("sequence", {}).get("value", "")
        length = record.get("sequence", {}).get("length", 0)

        comments = record.get("comments", [])
        diseases: list[str] = []
        for comment in comments:
            if comment.get("commentType") == "DISEASE":
                disease_id = comment.get("disease", {}).get("diseaseId")
                if disease_id:
                    diseases.append(disease_id)

        nodes: list[NormalizedNode] = [
            NormalizedNode(
                id=protein_id, type="protein",
                properties={"name": protein_name, "sequence": sequence[:50], "length": length},
            )
        ]

        edges: list[NormalizedEdge] = []

        if gene_name:
            nodes.append(NormalizedNode(
                id=f"gene:{gene_name}", type="gene",
                properties={"symbol": gene_name},
            ))
            edges.append(NormalizedEdge(
                from_id=f"gene:{gene_name}", to_id=protein_id,
                relation="ENCODES", properties={},
            ))

        for disease_id in diseases:
            edges.append(NormalizedEdge(
                from_id=protein_id, to_id=f"disease:{disease_id}",
                relation="ASSOCIATED_WITH", properties={"confidence": 0.8},
            ))

        return NormalizedRecord(
            nodes=nodes, edges=edges,
            source=self.source_name, fetched_at=datetime.now(timezone.utc),
        )

