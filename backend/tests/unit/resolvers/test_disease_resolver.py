import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from ingest.resolvers.disease import (
    resolve_disease_id,
    resolve_disease_ids,
    _parse_doid,
    _fetch_efo_term,
)


@pytest.fixture(autouse=True)
def clear_disease_state():
    import ingest.resolvers.disease as disease_mod

    disease_mod._cache.clear()
    # Reset lock to avoid any stale state
    disease_mod._cache_lock = asyncio.Lock()
    yield
    disease_mod._cache.clear()
    disease_mod._cache_lock = asyncio.Lock()


def _ols_term_with_crossref(doid: str = "DOID:1612"):
    return {
        "label": "breast cancer",
        "annotation": {
            "database_cross_reference": [doid, "OMIM:114480", "SNOMEDCT:254837009"],
        },
        "description": ["A cancer that arises from the breast."],
    }


def _ols_term_with_obo_xref(doid_id: str = "1612"):
    return {
        "label": "breast cancer",
        "obo_xref": [{"database": "DOID", "id": doid_id}],
        "description": ["A cancer of the breast."],
    }


def _ols_term_with_exact_match(doid_num: str = "1612"):
    return {
        "label": "breast cancer",
        "annotation": {
            "has exact match": [
                f"http://purl.obolibrary.org/obo/DOID_{doid_num}",
            ],
        },
        "description": ["Breast carcinoma."],
    }


def _ols_term_minimal():
    return {
        "label": "some disease",
        "description": ["A disease."],
    }


def _mock_ols_embedded(term: dict):
    return {
        "_embedded": {
            "terms": [term],
        },
    }


@pytest.mark.asyncio
async def test_resolve_disease_id_with_crossref_doid():
    term = _ols_term_with_crossref("DOID:1612")
    with patch(
        "ingest.resolvers.disease._fetch_efo_term",
        AsyncMock(return_value=term),
    ):
        result = await resolve_disease_id("EFO:0000305")
        assert result["efo_id"] == "EFO:0000305"
        assert result["label"] == "breast cancer"
        assert result["doid"] == "DOID:1612"
        assert result["description"] == "A cancer that arises from the breast."


@pytest.mark.asyncio
async def test_resolve_disease_id_with_obo_xref_doid():
    term = _ols_term_with_obo_xref("9982")
    with patch(
        "ingest.resolvers.disease._fetch_efo_term",
        AsyncMock(return_value=term),
    ):
        result = await resolve_disease_id("EFO:0000400")
        assert result["doid"] == "DOID:9982"


@pytest.mark.asyncio
async def test_resolve_disease_id_with_exact_match_doid():
    term = _ols_term_with_exact_match("1612")
    with patch(
        "ingest.resolvers.disease._fetch_efo_term",
        AsyncMock(return_value=term),
    ):
        result = await resolve_disease_id("EFO:0000305")
        assert result["doid"] == "DOID:1612"


@pytest.mark.asyncio
async def test_resolve_disease_id_no_doid():
    term = _ols_term_minimal()
    with patch(
        "ingest.resolvers.disease._fetch_efo_term",
        AsyncMock(return_value=term),
    ):
        result = await resolve_disease_id("EFO:0000305")
        assert result["doid"] is None
        assert result["label"] == "some disease"


@pytest.mark.asyncio
async def test_resolve_disease_id_cache_hit():
    import ingest.resolvers.disease as disease_mod

    disease_mod._cache["EFO:0000305"] = {
        "efo_id": "EFO:0000305",
        "label": "cached",
        "doid": "DOID:9999",
        "description": "from cache",
    }

    mock_fetch = AsyncMock()
    with patch("ingest.resolvers.disease._fetch_efo_term", mock_fetch):
        result = await resolve_disease_id("EFO:0000305")
        assert result["label"] == "cached"
        mock_fetch.assert_not_called()


@pytest.mark.asyncio
async def test_resolve_disease_id_api_error():
    with patch(
        "ingest.resolvers.disease._fetch_efo_term",
        AsyncMock(return_value=None),
    ):
        result = await resolve_disease_id("EFO:0000305")
        assert result["efo_id"] == "EFO:0000305"
        assert result["label"] is None
        assert result["doid"] is None
        assert result["description"] is None


@pytest.mark.asyncio
async def test_resolve_disease_ids_batch_all_resolved():
    terms = {
        "EFO:0000305": _ols_term_with_crossref("DOID:1612"),
        "EFO:0000400": _ols_term_with_obo_xref("9982"),
    }

    async def mock_fetch(client, efo_id):
        return terms.get(efo_id)

    with patch(
        "ingest.resolvers.disease._fetch_efo_term",
        AsyncMock(side_effect=mock_fetch),
    ):
        results = await resolve_disease_ids(["EFO:0000305", "EFO:0000400"])
        assert results["EFO:0000305"]["doid"] == "DOID:1612"
        assert results["EFO:0000400"]["doid"] == "DOID:9982"


@pytest.mark.asyncio
async def test_resolve_disease_ids_mixed_cache():
    import ingest.resolvers.disease as disease_mod

    disease_mod._cache["EFO:0000305"] = {
        "efo_id": "EFO:0000305",
        "label": "cached breast",
        "doid": "DOID:1612",
        "description": "from cache",
    }

    mock_fetch = AsyncMock(return_value=_ols_term_with_obo_xref("9982"))
    with patch("ingest.resolvers.disease._fetch_efo_term", mock_fetch):
        results = await resolve_disease_ids(["EFO:0000305", "EFO:0000400"])
        assert results["EFO:0000305"]["label"] == "cached breast"
        assert results["EFO:0000400"]["doid"] == "DOID:9982"
        # Only the uncached one should be fetched
        assert mock_fetch.call_count == 1


def test_parse_doid_crossref(mocker):
    term = _ols_term_with_crossref("DOID:1612")
    assert _parse_doid(term) == "DOID:1612"


def test_parse_doid_crossref_no_doid():
    term = {
        "annotation": {
            "database_cross_reference": ["OMIM:114480"],
        },
    }
    assert _parse_doid(term) is None


def test_parse_doid_obo_xref():
    term = _ols_term_with_obo_xref("1612")
    assert _parse_doid(term) == "DOID:1612"


def test_parse_doid_exact_match():
    term = _ols_term_with_exact_match("1612")
    assert _parse_doid(term) == "DOID:1612"


def test_parse_doid_exact_match_non_numeric():
    # Non-numeric suffix after DOID_ should not parse
    term = {
        "annotation": {
            "has exact match": ["http://purl.obolibrary.org/obo/DOID_abc"],
        },
    }
    assert _parse_doid(term) is None


def test_parse_doid_empty_term():
    assert _parse_doid({}) is None
