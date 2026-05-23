import asyncio
import httpx

CACHE: dict[str, dict] = {}
BASE_URL = "https://www.ebi.ac.uk/chembl/api/data/molecule"
TIMEOUT = 15.0
_client: httpx.AsyncClient | None = None


def _get_client() -> httpx.AsyncClient:
    global _client
    if _client is None:
        _client = httpx.AsyncClient(timeout=httpx.Timeout(TIMEOUT))
    return _client


async def _fetch_one(chembl_id: str) -> dict:
    try:
        client = _get_client()
        response = await client.get(f"{BASE_URL}/{chembl_id}.json")
        response.raise_for_status()
        data = response.json()
    except (httpx.HTTPError, httpx.TimeoutException):
        return {"molecule_chembl_id": chembl_id}

    return {
        "molecule_chembl_id": data.get("molecule_chembl_id", chembl_id),
        "pref_name": data.get("pref_name"),
        "canonical_smiles": (data.get("molecule_structures") or {}).get("canonical_smiles"),
        "full_mwt": (data.get("molecule_properties") or {}).get("full_mwt"),
        "alogp": (data.get("molecule_properties") or {}).get("alogp"),
    }


async def resolve_compound_id(chembl_id: str) -> dict:
    key = chembl_id.strip().upper()
    if key in CACHE:
        return CACHE[key]
    data = await _fetch_one(key)
    CACHE[key] = data
    return data


async def resolve_compound_ids(chembl_ids: list[str]) -> dict[str, dict]:
    results: dict[str, dict] = {}
    missing: list[str] = []
    for raw in chembl_ids:
        key = raw.strip().upper()
        if key in CACHE:
            results[key] = CACHE[key]
        else:
            missing.append(key)

    if missing:
        fetched = await asyncio.gather(*(_fetch_one(k) for k in missing))
        for i, key in enumerate(missing):
            CACHE[key] = fetched[i]
            results[key] = fetched[i]

    return results
