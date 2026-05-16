import re
from datetime import datetime, timezone
from typing import AsyncIterator
from ingest.base import BaseIngester
from ingest.models import NormalizedRecord, NormalizedNode, NormalizedEdge

GENE_SYMBOL_PATTERN = re.compile(r'\b[A-Z]{2,}[0-9]*\b')
DISEASE_PATTERN = re.compile(r'\b(?:cancer|carcinoma|syndrome|disease|disorder|deficiency)\b', re.IGNORECASE)


class PubMedIngester(BaseIngester):
    source_name = "pubmed"
    batch_size = 500

    async def fetch(self, since: datetime) -> AsyncIterator[dict]:
        import httpx
        import os
        api_key = os.environ.get("NCBI_API_KEY", "")
        base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
        params = {
            "db": "pubmed",
            "term": f'("{since.date().isoformat()}"[PDAT] : "3000"[PDAT])',
            "retmax": self.batch_size,
            "retmode": "json",
            "sort": "pub_date",
            "api_key": api_key,
        }
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(f"{base_url}/esearch.fcgi", params=params)
            data = response.json()
            id_list = data.get("esearchresult", {}).get("idlist", [])
            if not id_list:
                return

            fetch_params = {
                "db": "pubmed",
                "id": ",".join(id_list),
                "retmode": "json",
                "api_key": api_key,
            }
            fetch_response = await client.get(f"{base_url}/esummary.fcgi", params=fetch_params)
            result = fetch_response.json().get("result", {})
            for uid in id_list:
                record = result.get(uid)
                if record and record.get("title"):
                    yield record

    def normalize(self, record: dict) -> NormalizedRecord | None:
        title = record.get("title", "")
        abstract = record.get("abstract", "")

        if not title:
            return None

        pmid = f"pmid:{record.get('uid', '')}"
        nodes: list[NormalizedNode] = [
            NormalizedNode(
                id=pmid, type="article",
                properties={
                    "title": title, "abstract": abstract,
                    "year": int(record.get("pubdate", "0000")[:4]) if record.get("pubdate") else None,
                    "journal": record.get("source", ""),
                },
            )
        ]

        edges: list[NormalizedEdge] = []
        all_text = f"{title} {abstract}"
        genes = set(GENE_SYMBOL_PATTERN.findall(all_text))
        diseases = set(DISEASE_PATTERN.findall(all_text))

        for gene in genes:
            if len(gene) > 2:
                edges.append(NormalizedEdge(
                    from_id=pmid, to_id=f"gene:{gene}",
                    relation="MENTIONS", properties={"mention_type": "gene"},
                ))

        for disease in diseases:
            edges.append(NormalizedEdge(
                from_id=pmid, to_id=f"disease:{disease}",
                relation="MENTIONS", properties={"mention_type": "disease"},
            ))

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
                        if isinstance(v, str):
                            parts.append(f"n.{k} = '{v}'")
                        else:
                            parts.append(f"n.{k} = {v}")
                props_str = ", ".join(parts)
                queries.append(
                    f"MERGE (n:{node.type.capitalize()} {{id: '{node.id}'}}) "
                    f"ON CREATE SET {props_str} ON MATCH SET {props_str}"
                )
            for edge in record.edges:
                queries.append(
                    f"MATCH (a {{id: '{edge.from_id}'}}), (b {{id: '{edge.to_id}'}}) "
                    f"MERGE (a)-[:{edge.relation}]->(b)"
                )
        return queries
