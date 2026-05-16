from datetime import datetime, timezone
from typing import AsyncIterator
from ingest.base import BaseIngester
from ingest.models import NormalizedRecord, NormalizedNode, NormalizedEdge


class ChEMBLIngester(BaseIngester):
    source_name = "chembl"
    batch_size = 500

    async def fetch(self, since: datetime) -> AsyncIterator[dict]:
        import httpx
        base_url = "https://www.ebi.ac.uk/chembl/api/data"
        endpoints = ["molecule", "mechanism", "activity"]
        async with httpx.AsyncClient(timeout=30) as client:
            for ep in endpoints:
                url = f"{base_url}/{ep}?format=json&limit={self.batch_size}"
                while url:
                    response = await client.get(url)
                    data = response.json()
                    for item in data.get(ep.rstrip("s"), []):
                        item["_endpoint"] = ep
                        yield item
                    url = data.get("page_metadata", {}).get("next")
                    if not url:
                        break

    def normalize(self, record: dict) -> NormalizedRecord | None:
        ep = record.get("_endpoint", "")
        nodes: list[NormalizedNode] = []
        edges: list[NormalizedEdge] = []

        if ep == "molecule":
            chembl_id = record.get("molecule_chembl_id")
            if not chembl_id:
                return None
            nodes.append(NormalizedNode(
                id=f"compound:{chembl_id}", type="compound",
                properties={
                    "name": record.get("pref_name", "") or chembl_id,
                    "smiles": record.get("molecule_structures", {}).get("canonical_smiles", ""),
                    "mw": record.get("molecule_properties", {}).get("full_mwt"),
                    "logp": record.get("molecule_properties", {}).get("alogp"),
                },
            ))

        elif ep == "mechanism":
            chembl_id = record.get("molecule_chembl_id")
            target_id = record.get("target_chembl_id")
            if not chembl_id or not target_id:
                return None
            nodes.append(NormalizedNode(
                id=f"compound:{chembl_id}", type="compound",
                properties={"name": chembl_id},
            ))
            edges.append(NormalizedEdge(
                from_id=f"compound:{chembl_id}", to_id=f"protein:{target_id}",
                relation="BINDS_TO",
                properties={"mechanism": record.get("mechanism_of_action", ""), "source": "chembl"},
            ))

        elif ep == "activity":
            chembl_id = record.get("molecule_chembl_id")
            target_id = record.get("target_chembl_id")
            if not chembl_id:
                return None
            ic50 = record.get("standard_value") if record.get("standard_type") == "IC50" else None
            nodes.append(NormalizedNode(
                id=f"compound:{chembl_id}", type="compound",
                properties={"name": chembl_id},
            ))
            if target_id:
                edges.append(NormalizedEdge(
                    from_id=f"compound:{chembl_id}", to_id=f"protein:{target_id}",
                    relation="BINDS_TO",
                    properties={"ic50": ic50, "assay_type": record.get("assay_type", ""), "source": "chembl"},
                ))

        if not nodes:
            return None

        return NormalizedRecord(
            nodes=nodes, edges=edges,
            source=self.source_name, fetched_at=datetime.now(timezone.utc),
        )

