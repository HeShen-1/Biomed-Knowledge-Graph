import pytest
from unittest.mock import AsyncMock, patch
from ingest.sources.opentargets import OpenTargetsIngester

SAMPLE = {
    "target": {"id": "ENSG00000141510", "approvedSymbol": "TP53"},
    "disease": {"id": "MONDO_0016575", "name": "breast carcinoma"},
    "score": 0.85,
    "_disease_id": "EFO_0000305",
    "_disease_name": "breast carcinoma",
}

MOCK_RESOLVED = {"efo_id": "EFO_0000305", "label": "breast carcinoma", "doid": "DOID:1612", "description": None}


@pytest.mark.asyncio
@patch("ingest.sources.opentargets.resolve_disease_id", new_callable=AsyncMock)
async def test_opentargets_normalize_snapshot(mock_resolve):
    mock_resolve.return_value = MOCK_RESOLVED
    ingester = OpenTargetsIngester()
    result = await ingester.normalize(SAMPLE)
    assert result is not None
    assert len(result.nodes) == 2  # gene + disease
    gene = [n for n in result.nodes if n.type == "gene"][0]
    assert gene.id == "gene:TP53"
    disease = [n for n in result.nodes if n.type == "disease"][0]
    assert disease.id == "disease:DOID:1612"
    assert disease.properties["doid"] == "DOID:1612"
    assert disease.properties["efo_id"] == "EFO_0000305"
    assert len(result.edges) == 1
    assert result.edges[0].relation == "TARGETS"
    assert result.edges[0].properties["score"] == 0.85
    mock_resolve.assert_called_once_with("EFO_0000305")


@pytest.mark.asyncio
@patch("ingest.sources.opentargets.resolve_disease_id", new_callable=AsyncMock)
async def test_opentargets_disease_without_doid(mock_resolve):
    mock_resolve.return_value = {"efo_id": "EFO_0000305", "label": "breast carcinoma", "doid": None, "description": None}
    ingester = OpenTargetsIngester()
    result = await ingester.normalize(SAMPLE)
    assert result is not None
    disease = [n for n in result.nodes if n.type == "disease"][0]
    assert disease.id == "disease:EFO_0000305"  # fallback to EFO ID


@pytest.mark.asyncio
async def test_opentargets_empty_record_returns_none():
    ingester = OpenTargetsIngester()
    result = await ingester.normalize({"target": {}, "disease": {}})
    assert result is None
