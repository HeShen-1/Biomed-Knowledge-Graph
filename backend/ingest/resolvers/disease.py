import asyncio
from typing import Any

import httpx

OLS_BASE = "https://www.ebi.ac.uk/ols/api"
REQUEST_TIMEOUT = 10.0

_cache: dict[str, dict] = {}
_cache_lock = asyncio.Lock()


def _parse_doid(term_data: dict) -> str | None:
    annotation = term_data.get("annotation", {}) or {}

    for ref in annotation.get("database_cross_reference", []) or []:
        if isinstance(ref, str) and ref.startswith("DOID:"):
            return ref

    for xref in term_data.get("obo_xref", []) or []:
        if isinstance(xref, dict) and xref.get("database") == "DOID":
            return f"DOID:{xref['id']}"

    for match in annotation.get("has exact match", []) or []:
        if isinstance(match, str) and "DOID_" in match:
            doid_num = match.split("DOID_")[-1].split("/")[0]
            if doid_num.isdigit():
                return f"DOID:{doid_num}"

    return None


def _extract_description(term_data: dict) -> str | None:
    description = term_data.get("description")
    if isinstance(description, list) and description:
        return description[0]
    if isinstance(description, str):
        return description
    return None


async def _fetch_efo_term(client: httpx.AsyncClient, efo_id: str) -> dict | None:
    """Fetch term details from OLS API. EFO IDs use underscore format (EFO_0000305)."""
    obo_id = efo_id.replace(":", "_") if ":" in efo_id else efo_id
    url = f"{OLS_BASE}/ontologies/efo/terms"
    params = {"obo_id": obo_id, "size": "1"}

    try:
        resp = await client.get(url, params=params, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        return None

    embedded = data.get("_embedded", {}) or {}
    terms = embedded.get("terms", []) or []
    if not terms:
        return None

    return terms[0]


async def resolve_disease_id(efo_id: str) -> dict:
    """Map an EFO ID to a standardized disease ontology dict.

    Returns dict with keys: efo_id, label, doid (or None), description.
    """
    if efo_id in _cache:
        return _cache[efo_id]

    async with _cache_lock:
        if efo_id in _cache:
            return _cache[efo_id]

        async with httpx.AsyncClient(follow_redirects=True) as client:
            term = await _fetch_efo_term(client, efo_id)

        if term is None:
            result: dict[str, Any] = {
                "efo_id": efo_id,
                "label": None,
                "doid": None,
                "description": None,
            }
        else:
            result = {
                "efo_id": efo_id,
                "label": term.get("label"),
                "doid": _parse_doid(term),
                "description": _extract_description(term),
            }

        _cache[efo_id] = result
        return result


async def resolve_disease_ids(efo_ids: list[str]) -> dict[str, dict]:
    """Batch resolve multiple EFO IDs. Returns dict mapping efo_id -> result dict."""
    uncached = [eid for eid in efo_ids if eid not in _cache]
    if not uncached:
        return {eid: _cache[eid] for eid in efo_ids}

    async with _cache_lock:
        still_uncached = [eid for eid in uncached if eid not in _cache]
        if still_uncached:
            async with httpx.AsyncClient(follow_redirects=True) as client:
                tasks = [_fetch_efo_term(client, eid) for eid in still_uncached]
                terms = await asyncio.gather(*tasks)

            for eid, term in zip(still_uncached, terms):
                if term is None:
                    _cache[eid] = {
                        "efo_id": eid,
                        "label": None,
                        "doid": None,
                        "description": None,
                    }
                else:
                    _cache[eid] = {
                        "efo_id": eid,
                        "label": term.get("label"),
                        "doid": _parse_doid(term),
                        "description": _extract_description(term),
                    }

    return {eid: _cache[eid] for eid in efo_ids}
