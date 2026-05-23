import asyncio
import httpx

_cached: dict[str, str] = {}
_cache_lock = asyncio.Lock()

_client: httpx.AsyncClient | None = None


def _get_client() -> httpx.AsyncClient:
    global _client
    if _client is None:
        _client = httpx.AsyncClient(timeout=httpx.Timeout(10.0))
    return _client


def _extract_accession(hit: dict) -> str | None:
    uniprot = hit.get("uniprot")
    if not isinstance(uniprot, dict):
        return None
    swissprot = uniprot.get("Swiss-Prot")
    if isinstance(swissprot, list) and swissprot:
        return swissprot[0]
    if isinstance(swissprot, str) and swissprot:
        return swissprot
    return None


def _fallback(symbol: str) -> str:
    key = symbol.strip().upper()
    if not key:
        return "protein:UNKNOWN"
    return f"protein:{key}"


async def resolve_gene_symbol(symbol: str) -> str:
    key = symbol.strip().upper()
    if not key:
        return "protein:UNKNOWN"

    if key in _cached:
        return _cached[key]

    async with _cache_lock:
        if key in _cached:
            return _cached[key]

        try:
            client = _get_client()
            resp = await client.get(
                "https://mygene.info/v3/query",
                params={
                    "q": f"symbol:{symbol}",
                    "species": "human",
                    "fields": "uniprot.Swiss-Prot",
                },
            )
            resp.raise_for_status()
            data = resp.json()
            hits = data if isinstance(data, list) else data.get("hits", [])
            if hits:
                accession = _extract_accession(hits[0])
                if accession:
                    result = f"protein:{accession}"
                    _cached[key] = result
                    return result
            result = _fallback(symbol)
            _cached[key] = result
            return result
        except (httpx.HTTPError, httpx.TimeoutException, ValueError):
            result = _fallback(symbol)
            _cached[key] = result
            return result


async def resolve_gene_symbols(symbols: list[str]) -> dict[str, str]:
    results: dict[str, str] = {}
    uncached: list[str] = []

    for s in symbols:
        key = s.strip().upper()
        if not key:
            results[s] = "protein:UNKNOWN"
        elif key in _cached:
            results[s] = _cached[key]
        else:
            uncached.append(key)

    if not uncached:
        return results

    query_parts = [f"symbol:{s}" for s in uncached]
    q = " OR ".join(query_parts)

    try:
        client = _get_client()
        resp = await client.post(
            "https://mygene.info/v3/query",
            json={
                "q": q,
                "species": "human",
                "fields": ["uniprot.Swiss-Prot"],
                "scopes": "symbol",
            },
        )
        resp.raise_for_status()
        data = resp.json()
        hits = data if isinstance(data, list) else data.get("hits", [])

        found: dict[str, str] = {}
        for hit in hits:
            query = hit.get("query", "")
            if not query or query.startswith("symbol:"):
                symbol_from_query = query.removeprefix("symbol:") if query.startswith("symbol:") else query
                accession = _extract_accession(hit)
                if accession:
                    found[symbol_from_query.upper()] = f"protein:{accession}"
    except (httpx.HTTPError, httpx.TimeoutException, ValueError):
        found = {}

    async with _cache_lock:
        for s in symbols:
            if s in results:
                continue
            key = s.strip().upper()
            if key in _cached:
                results[s] = _cached[key]
                continue
            if key in found:
                results[s] = found[key]
            else:
                results[s] = _fallback(s)
            _cached[key] = results[s]

    return results
