import pytest
from ingest.sources.pubmed import PubMedIngester

SAMPLE = {
    "uid": "12345678",
    "title": "BRCA1 mutations in breast cancer",
    "pubdate": "20240101",
    "source": "Nature",
    "abstract": "This study investigates BRCA1 mutations in breast cancer patients.",
    "authors": [{"name": "Smith J"}, {"name": "Doe K"}],
}


@pytest.mark.asyncio
async def test_pubmed_normalize_snapshot():
    ingester = PubMedIngester()
    result = await ingester.normalize(SAMPLE)
    assert result is not None
    assert len(result.nodes) == 1
    assert result.nodes[0].type == "article"
    assert result.nodes[0].id == "pmid:12345678"
    assert result.nodes[0].properties["title"] == "BRCA1 mutations in breast cancer"


@pytest.mark.asyncio
async def test_pubmed_normalize_empty_record_returns_none():
    ingester = PubMedIngester()
    result = await ingester.normalize({})
    assert result is None


@pytest.mark.asyncio
async def test_pubmed_build_queries():
    ingester = PubMedIngester()
    result = await ingester.normalize(SAMPLE)
    statements = ingester.build_queries([result])
    assert len(statements) > 0
    assert isinstance(statements[0], tuple)
    assert "MERGE" in statements[0][0]
    assert isinstance(statements[0][1], dict)
