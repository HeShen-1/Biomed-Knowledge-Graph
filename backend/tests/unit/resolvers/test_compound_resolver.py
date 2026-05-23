import httpx
import pytest
from unittest.mock import AsyncMock, MagicMock

from ingest.resolvers.compound import resolve_compound_id, resolve_compound_ids


FULL_MOLECULE_RESPONSE = {
    "molecule_chembl_id": "CHEMBL25",
    "pref_name": "Aspirin",
    "molecule_structures": {"canonical_smiles": "CC(=O)Oc1ccccc1C(=O)O"},
    "molecule_properties": {"full_mwt": 180.16, "alogp": 1.43},
}


@pytest.fixture(autouse=True)
def clear_compound_state():
    import ingest.resolvers.compound as compound_mod

    compound_mod.CACHE.clear()
    compound_mod._client = None
    yield
    compound_mod.CACHE.clear()
    compound_mod._client = None


def _set_mock_client_with_response(response_data: dict):
    import ingest.resolvers.compound as compound_mod

    mock_client = AsyncMock()
    mock_response = MagicMock()
    mock_response.json.return_value = response_data
    mock_response.raise_for_status = MagicMock()
    mock_client.get.return_value = mock_response
    compound_mod._client = mock_client


@pytest.mark.asyncio
async def test_resolve_compound_id_returns_normalized_data():
    _set_mock_client_with_response(FULL_MOLECULE_RESPONSE)

    result = await resolve_compound_id("CHEMBL25")
    assert result["molecule_chembl_id"] == "CHEMBL25"
    assert result["pref_name"] == "Aspirin"
    assert result["canonical_smiles"] == "CC(=O)Oc1ccccc1C(=O)O"
    assert result["full_mwt"] == 180.16
    assert result["alogp"] == 1.43


@pytest.mark.asyncio
async def test_resolve_compound_id_cache_hit():
    import ingest.resolvers.compound as compound_mod

    compound_mod.CACHE["CHEMBL25"] = {
        "molecule_chembl_id": "CHEMBL25",
        "pref_name": "Aspirin",
        "canonical_smiles": "CC(=O)Oc1ccccc1C(=O)O",
        "full_mwt": 180.16,
        "alogp": 1.43,
    }
    compound_mod._client = AsyncMock()

    result = await resolve_compound_id("CHEMBL25")
    assert result["pref_name"] == "Aspirin"
    compound_mod._client.get.assert_not_called()


@pytest.mark.asyncio
async def test_resolve_compound_id_api_error_fallback():
    import ingest.resolvers.compound as compound_mod

    mock_client = AsyncMock()
    mock_client.get.side_effect = httpx.TimeoutException("Timeout")
    compound_mod._client = mock_client

    result = await resolve_compound_id("CHEMBL25")
    assert result == {"molecule_chembl_id": "CHEMBL25"}


@pytest.mark.asyncio
async def test_resolve_compound_id_case_insensitive_cache():
    import ingest.resolvers.compound as compound_mod

    compound_mod.CACHE["CHEMBL25"] = {"molecule_chembl_id": "CHEMBL25", "pref_name": "cached"}
    compound_mod._client = AsyncMock()

    result = await resolve_compound_id("chembl25")
    assert result["pref_name"] == "cached"


@pytest.mark.asyncio
async def test_resolve_compound_ids_batch_all_fetched():
    import ingest.resolvers.compound as compound_mod

    responses = {
        "CHEMBL25": FULL_MOLECULE_RESPONSE,
        "CHEMBL100": {
            "molecule_chembl_id": "CHEMBL100",
            "pref_name": "Ibuprofen",
            "molecule_structures": {"canonical_smiles": "CC(C)Cc1ccc(C(C)C(=O)O)cc1"},
            "molecule_properties": {"full_mwt": 206.28, "alogp": 3.97},
        },
    }

    async def mock_get(url):
        mock_resp = MagicMock()
        chembl_id = url.split("/")[-1].replace(".json", "").upper()
        mock_resp.json.return_value = responses.get(chembl_id, {"molecule_chembl_id": chembl_id})
        mock_resp.raise_for_status = MagicMock()
        return mock_resp

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(side_effect=mock_get)
    compound_mod._client = mock_client

    results = await resolve_compound_ids(["CHEMBL25", "CHEMBL100"])
    assert results["CHEMBL25"]["pref_name"] == "Aspirin"
    assert results["CHEMBL100"]["pref_name"] == "Ibuprofen"


@pytest.mark.asyncio
async def test_resolve_compound_ids_mixed_cache():
    import ingest.resolvers.compound as compound_mod

    compound_mod.CACHE["CHEMBL25"] = {"molecule_chembl_id": "CHEMBL25", "pref_name": "cached"}

    mock_response = MagicMock()
    mock_response.json.return_value = {"molecule_chembl_id": "CHEMBL100", "pref_name": "new"}
    mock_response.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.get.return_value = mock_response
    compound_mod._client = mock_client

    results = await resolve_compound_ids(["CHEMBL25", "CHEMBL100"])
    assert results["CHEMBL25"]["pref_name"] == "cached"
    assert results["CHEMBL100"]["pref_name"] == "new"
    # Only CHEMBL100 should trigger an API call
    assert mock_client.get.call_count == 1


@pytest.mark.asyncio
async def test_resolve_compound_id_nulls_in_response():
    response = {
        "molecule_chembl_id": "CHEMBL25",
        "pref_name": None,
        "molecule_structures": None,
        "molecule_properties": None,
    }
    _set_mock_client_with_response(response)

    result = await resolve_compound_id("CHEMBL25")
    assert result["pref_name"] is None
    assert result["canonical_smiles"] is None
    assert result["full_mwt"] is None
    assert result["alogp"] is None
