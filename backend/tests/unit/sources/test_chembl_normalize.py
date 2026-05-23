import pytest
from unittest.mock import AsyncMock, patch
from ingest.sources.chembl import ChEMBLIngester

MOLECULE_SAMPLE = {
    "_endpoint": "molecule",
    "molecule_chembl_id": "CHEMBL25",
    "pref_name": "Aspirin",
    "molecule_structures": {"canonical_smiles": "CC(=O)Oc1ccccc1C(=O)O"},
    "molecule_properties": {"full_mwt": 180.16, "alogp": 1.43},
}

MECHANISM_SAMPLE = {
    "_endpoint": "mechanism",
    "molecule_chembl_id": "CHEMBL25",
    "target_chembl_id": "CHEMBL209",
    "mechanism_of_action": "COX inhibitor",
}


@pytest.mark.asyncio
async def test_chembl_molecule_normalize():
    ingester = ChEMBLIngester()
    result = await ingester.normalize(MOLECULE_SAMPLE)
    assert result is not None
    assert len(result.nodes) == 1
    assert result.nodes[0].id == "compound:CHEMBL25"
    assert result.nodes[0].properties["name"] == "Aspirin"


@pytest.mark.asyncio
@patch("ingest.sources.chembl._resolve_target_to_uniprot", new_callable=AsyncMock)
async def test_chembl_mechanism_normalize(mock_resolve):
    mock_resolve.return_value = "P12345"

    ingester = ChEMBLIngester()
    result = await ingester.normalize(MECHANISM_SAMPLE)
    assert result is not None
    assert len(result.edges) == 1
    assert result.edges[0].relation == "BINDS_TO"
    assert result.edges[0].from_id == "compound:CHEMBL25"
    assert result.edges[0].from_type == "compound"
    assert result.edges[0].to_type == "protein"
    edge = result.edges[0]
    assert edge.to_id == "protein:P12345"
    node_ids = {n.id for n in result.nodes}
    assert edge.to_id in node_ids
    mock_resolve.assert_called_once_with("CHEMBL209")


@pytest.mark.asyncio
@patch("ingest.sources.chembl._resolve_target_to_uniprot", new_callable=AsyncMock)
async def test_chembl_mechanism_unresolved_target(mock_resolve):
    mock_resolve.return_value = None

    ingester = ChEMBLIngester()
    result = await ingester.normalize(MECHANISM_SAMPLE)
    assert result is not None
    edge = result.edges[0]
    assert edge.to_id == "protein:CHEMBL209"


@pytest.mark.asyncio
async def test_chembl_empty_record_returns_none():
    ingester = ChEMBLIngester()
    result = await ingester.normalize({})
    assert result is None
