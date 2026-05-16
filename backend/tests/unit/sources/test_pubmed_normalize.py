from ingest.sources.pubmed import PubMedIngester

SAMPLE = {
    "uid": "12345678",
    "title": "BRCA1 mutations in breast cancer",
    "pubdate": "20240101",
    "source": "Nature",
    "abstract": "This study investigates BRCA1 mutations in breast cancer patients.",
    "authors": [{"name": "Smith J"}, {"name": "Doe K"}],
}


def test_pubmed_normalize_snapshot():
    ingester = PubMedIngester()
    result = ingester.normalize(SAMPLE)
    assert result is not None
    assert len(result.nodes) == 1
    assert result.nodes[0].type == "article"
    assert result.nodes[0].id == "pmid:12345678"
    assert result.nodes[0].properties["title"] == "BRCA1 mutations in breast cancer"


def test_pubmed_normalize_empty_record_returns_none():
    ingester = PubMedIngester()
    result = ingester.normalize({})
    assert result is None


def test_pubmed_build_queries():
    ingester = PubMedIngester()
    result = ingester.normalize(SAMPLE)
    queries = ingester.build_queries([result])
    assert len(queries) > 0
    assert any("MERGE" in q for q in queries)
