import pytest
from unittest.mock import AsyncMock, MagicMock
import httpx

from ingest.resolvers.gene import (
    resolve_gene_symbol,
    resolve_gene_symbols,
    _extract_accession,
    _fallback,
)


@pytest.fixture(autouse=True)
def clear_gene_state():
    import ingest.resolvers.gene as gene_mod

    gene_mod._cached.clear()
    gene_mod._client = None
    yield
    gene_mod._cached.clear()
    gene_mod._client = None


def _mock_client_get_with_hits(accession: str):
    mock_client = AsyncMock()
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "hits": [{"uniprot": {"Swiss-Prot": [accession]}}],
    }
    mock_response.raise_for_status = MagicMock()
    mock_client.get.return_value = mock_response
    return mock_client


@pytest.mark.asyncio
async def test_resolve_gene_symbol_returns_accession():
    import ingest.resolvers.gene as gene_mod

    gene_mod._client = _mock_client_get_with_hits("P04637")
    result = await resolve_gene_symbol("TP53")
    assert result == "protein:P04637"


@pytest.mark.asyncio
async def test_resolve_gene_symbol_cache_hit():
    import ingest.resolvers.gene as gene_mod

    gene_mod._cached["TP53"] = "protein:P04637"
    gene_mod._client = AsyncMock()

    result = await resolve_gene_symbol("TP53")
    assert result == "protein:P04637"
    gene_mod._client.get.assert_not_called()


@pytest.mark.asyncio
async def test_resolve_gene_symbol_fallback_on_http_error():
    import ingest.resolvers.gene as gene_mod

    mock_client = AsyncMock()
    mock_client.get.side_effect = httpx.HTTPError("Down")
    gene_mod._client = mock_client

    result = await resolve_gene_symbol("BRCA1")
    assert result == "protein:BRCA1"
    assert gene_mod._cached["BRCA1"] == "protein:BRCA1"


@pytest.mark.asyncio
async def test_resolve_gene_symbol_fallback_on_timeout():
    import ingest.resolvers.gene as gene_mod

    mock_client = AsyncMock()
    mock_client.get.side_effect = httpx.TimeoutException("Timeout")
    gene_mod._client = mock_client

    result = await resolve_gene_symbol("EGFR")
    assert result == "protein:EGFR"


@pytest.mark.asyncio
async def test_resolve_gene_symbol_fallback_no_hits():
    import ingest.resolvers.gene as gene_mod

    mock_client = AsyncMock()
    mock_response = MagicMock()
    mock_response.json.return_value = {"hits": []}
    mock_response.raise_for_status = MagicMock()
    mock_client.get.return_value = mock_response
    gene_mod._client = mock_client

    result = await resolve_gene_symbol("KRAS")
    assert result == "protein:KRAS"


@pytest.mark.asyncio
async def test_resolve_gene_symbol_fallback_hit_without_accession():
    import ingest.resolvers.gene as gene_mod

    mock_client = AsyncMock()
    mock_response = MagicMock()
    mock_response.json.return_value = {"hits": [{"uniprot": {}}]}
    mock_response.raise_for_status = MagicMock()
    mock_client.get.return_value = mock_response
    gene_mod._client = mock_client

    result = await resolve_gene_symbol("MYC")
    assert result == "protein:MYC"


@pytest.mark.asyncio
async def test_resolve_gene_symbol_empty_input():
    result = await resolve_gene_symbol("")
    assert result == "protein:UNKNOWN"


@pytest.mark.asyncio
async def test_resolve_gene_symbol_strips_whitespace():
    import ingest.resolvers.gene as gene_mod

    mock_client = AsyncMock()
    mock_client.get.side_effect = httpx.TimeoutException("timeout")
    gene_mod._client = mock_client

    result = await resolve_gene_symbol("  tp53  ")
    assert result == "protein:TP53"


@pytest.mark.asyncio
async def test_resolve_gene_symbols_batch_all_resolved():
    import ingest.resolvers.gene as gene_mod

    mock_client = AsyncMock()
    mock_response = MagicMock()
    mock_response.json.return_value = [
        {"query": "symbol:TP53", "uniprot": {"Swiss-Prot": ["P04637"]}},
        {"query": "symbol:MDM2", "uniprot": {"Swiss-Prot": ["Q00987"]}},
    ]
    mock_response.raise_for_status = MagicMock()
    mock_client.post.return_value = mock_response
    gene_mod._client = mock_client

    results = await resolve_gene_symbols(["TP53", "MDM2"])
    assert results == {"TP53": "protein:P04637", "MDM2": "protein:Q00987"}


@pytest.mark.asyncio
async def test_resolve_gene_symbols_batch_with_cache():
    import ingest.resolvers.gene as gene_mod

    gene_mod._cached["TP53"] = "protein:P04637"

    mock_client = AsyncMock()
    mock_response = MagicMock()
    mock_response.json.return_value = [
        {"query": "symbol:MDM2", "uniprot": {"Swiss-Prot": ["Q00987"]}},
    ]
    mock_response.raise_for_status = MagicMock()
    mock_client.post.return_value = mock_response
    gene_mod._client = mock_client

    results = await resolve_gene_symbols(["TP53", "MDM2"])
    assert results == {"TP53": "protein:P04637", "MDM2": "protein:Q00987"}
    # Only MDM2 should be requested via POST
    called_json = mock_client.post.call_args[1]["json"]
    assert "symbol:MDM2" in called_json["q"]
    assert "symbol:TP53" not in called_json["q"]


@pytest.mark.asyncio
async def test_resolve_gene_symbols_batch_api_error_fallback():
    import ingest.resolvers.gene as gene_mod

    mock_client = AsyncMock()
    mock_client.post.side_effect = httpx.HTTPError("Down")
    gene_mod._client = mock_client

    results = await resolve_gene_symbols(["BRCA1", "EGFR"])
    assert results == {"BRCA1": "protein:BRCA1", "EGFR": "protein:EGFR"}


@pytest.mark.asyncio
async def test_resolve_gene_symbols_batch_partial_results():
    import ingest.resolvers.gene as gene_mod

    mock_client = AsyncMock()
    mock_response = MagicMock()
    # Only TP53 resolved, MDM2 missing from hits
    mock_response.json.return_value = [
        {"query": "symbol:TP53", "uniprot": {"Swiss-Prot": ["P04637"]}},
    ]
    mock_response.raise_for_status = MagicMock()
    mock_client.post.return_value = mock_response
    gene_mod._client = mock_client

    results = await resolve_gene_symbols(["TP53", "MDM2"])
    assert results["TP53"] == "protein:P04637"
    assert results["MDM2"] == "protein:MDM2"


def test_extract_accession_from_list():
    hit = {"uniprot": {"Swiss-Prot": ["P04637"]}}
    assert _extract_accession(hit) == "P04637"


def test_extract_accession_from_string():
    hit = {"uniprot": {"Swiss-Prot": "Q00987"}}
    assert _extract_accession(hit) == "Q00987"


def test_extract_accession_no_uniprot():
    assert _extract_accession({}) is None


def test_extract_accession_uniprot_not_dict():
    assert _extract_accession({"uniprot": "bad"}) is None


def test_fallback_uppercases():
    assert _fallback("tp53") == "protein:TP53"
    assert _fallback("  mdm2 ") == "protein:MDM2"
