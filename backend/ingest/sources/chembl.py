from datetime import datetime, timezone
from typing import AsyncIterator
import httpx
from ingest.base import BaseIngester
from ingest.models import NormalizedRecord, NormalizedNode, NormalizedEdge

import re

_CHEMBL_ID_RE = re.compile(r"^CHEMBL\d+$")
_target_client: httpx.AsyncClient | None = None
_target_cache: dict[str, str | None] = {}


def _validate_chembl_id(chembl_id: str) -> bool:
    return bool(_CHEMBL_ID_RE.match(chembl_id))


def _get_target_client() -> httpx.AsyncClient:
    global _target_client
    if _target_client is None:
        _target_client = httpx.AsyncClient(timeout=httpx.Timeout(10.0))
    return _target_client


async def _resolve_target_to_uniprot(target_chembl_id: str) -> str | None:
    if target_chembl_id in _target_cache:
        return _target_cache[target_chembl_id]

    if not _validate_chembl_id(target_chembl_id):
        _target_cache[target_chembl_id] = None
        return None

    try:
        client = _get_target_client()
        resp = await client.get(
            f"https://www.ebi.ac.uk/chembl/api/data/target/{target_chembl_id}.json"
        )
        resp.raise_for_status()
        data = resp.json()
        components = data.get("target_components", [])
        if not isinstance(components, list):
            components = []

        for comp in components:
            if not isinstance(comp, dict):
                continue
            accession = comp.get("accession")
            if accession:
                _target_cache[target_chembl_id] = accession
                return accession
        _target_cache[target_chembl_id] = None
        return None
    except (httpx.HTTPError, httpx.TimeoutException, KeyError):
        _target_cache[target_chembl_id] = None
        return None


class ChEMBLIngester(BaseIngester):
    source_name = "chembl"
    batch_size = 500

    async def fetch(self, since: datetime) -> AsyncIterator[dict]:
        base_url = "https://www.ebi.ac.uk/chembl/api/data"
        endpoints = ["molecule", "mechanism"]
        max_pages = 3

        async with httpx.AsyncClient(timeout=30) as client:
            for ep in endpoints:
                page = 0
                url = f"{base_url}/{ep}?format=json&limit={self.batch_size}"
                while url and page < max_pages:
                    response = await client.get(url)
                    data = response.json()
                    key = ep + "s" if (ep + "s") in data else ep
                    for item in data.get(key, []):
                        item["_endpoint"] = ep
                        yield item
                    url = data.get("page_metadata", {}).get("next")
                    page += 1
                    if not url:
                        break

    async def normalize(self, record: dict) -> NormalizedRecord | None:
        ep = record.get("_endpoint", "")
        nodes: list[NormalizedNode] = []
        edges: list[NormalizedEdge] = []

        if ep == "molecule":
            chembl_id = record.get("molecule_chembl_id")
            if not chembl_id:
                return None
            structures = record.get("molecule_structures") or {}
            properties = record.get("molecule_properties") or {}
            nodes.append(NormalizedNode(
                id=f"compound:{chembl_id}", type="compound",
                properties={
                    "name": record.get("pref_name", "") or chembl_id,
                    "smiles": structures.get("canonical_smiles", ""),
                    "mw": properties.get("full_mwt"),
                    "logp": properties.get("alogp"),
                },
            ))

        elif ep == "mechanism":
            chembl_id = record.get("molecule_chembl_id")
            target_id = record.get("target_chembl_id")
            if not chembl_id or not target_id:
                return None
            accession = await _resolve_target_to_uniprot(target_id)
            protein_id = f"protein:{accession}" if accession else f"protein:{target_id}"
            nodes.append(NormalizedNode(
                id=f"compound:{chembl_id}", type="compound",
                properties={"name": chembl_id},
            ))
            nodes.append(NormalizedNode(
                id=protein_id, type="protein",
                properties={
                    "name": accession or target_id,
                    "source": "chembl_target",
                    "chembl_target_id": target_id,
                },
            ))
            edges.append(NormalizedEdge(
                from_id=f"compound:{chembl_id}", to_id=protein_id,
                relation="BINDS_TO",
                from_type="compound", to_type="protein",
                properties={
                    "mechanism": record.get("mechanism_of_action", ""),
                    "source": "chembl",
                },
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
                accession = await _resolve_target_to_uniprot(target_id)
                protein_id = f"protein:{accession}" if accession else f"protein:{target_id}"
                edges.append(NormalizedEdge(
                    from_id=f"compound:{chembl_id}", to_id=protein_id,
                    relation="BINDS_TO",
                    from_type="compound", to_type="protein",
                    properties={
                        "ic50": ic50,
                        "assay_type": record.get("assay_type", ""),
                        "source": "chembl",
                    },
                ))

        if not nodes:
            return None

        return NormalizedRecord(
            nodes=nodes, edges=edges,
            source=self.source_name, fetched_at=datetime.now(timezone.utc),
        )
