import pytest
from unittest.mock import patch, AsyncMock
from ingest.sources.string import StringIngester

SAMPLE_HIGH_SCORE = {
    "preferredName_A": "TP53",
    "preferredName_B": "MDM2",
    "score": 998,
    "escore": 850,
}

SAMPLE_LOW_SCORE = {
    "preferredName_A": "TP53",
    "preferredName_B": "XYZ",
    "score": 500,
    "escore": 200,
}


@pytest.mark.asyncio
@patch("ingest.sources.string.resolve_gene_symbols")
async def test_string_normalize_snapshot(mock_resolve):
    mock_resolve.return_value = {
        "TP53": "protein:P04637",
        "MDM2": "protein:Q00987",
    }

    ingester = StringIngester()
    result = await ingester.normalize(SAMPLE_HIGH_SCORE)
    assert result is not None
    assert len(result.nodes) == 2
    node_ids = {n.id for n in result.nodes}
    assert node_ids == {"protein:P04637", "protein:Q00987"}
    assert len(result.edges) == 1
    assert result.edges[0].relation == "INTERACTS_WITH"
    assert result.edges[0].properties["score"] == 0.998
    assert result.edges[0].from_id == "protein:P04637"
    assert result.edges[0].to_id == "protein:Q00987"
    assert result.edges[0].from_type == "protein"
    assert result.edges[0].to_type == "protein"


@pytest.mark.asyncio
@patch("ingest.sources.string.resolve_gene_symbols")
async def test_string_low_score_returns_none(mock_resolve):
    mock_resolve.return_value = {"TP53": "protein:P04637", "XYZ": "protein:XYZ"}

    ingester = StringIngester()
    result = await ingester.normalize(SAMPLE_LOW_SCORE)
    assert result is None
    # Resolver should not be called when score is filtered
    mock_resolve.assert_not_called()


@pytest.mark.asyncio
@patch("ingest.sources.string.resolve_gene_symbols")
async def test_string_empty_record_returns_none(mock_resolve):
    mock_resolve.return_value = {}

    ingester = StringIngester()
    result = await ingester.normalize({})
    assert result is None
    mock_resolve.assert_not_called()
