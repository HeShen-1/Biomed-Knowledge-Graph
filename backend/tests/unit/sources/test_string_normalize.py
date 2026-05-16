from ingest.sources.string import StringIngester

SAMPLE_HIGH_SCORE = {
    "preferredName_A": "TP53",
    "preferredName_B": "MDM2",
    "score": 998,  # 0.998
    "escore": 850,
}

SAMPLE_LOW_SCORE = {
    "preferredName_A": "TP53",
    "preferredName_B": "XYZ",
    "score": 500,  # 0.5, below threshold
    "escore": 200,
}


def test_string_normalize_snapshot():
    ingester = StringIngester()
    result = ingester.normalize(SAMPLE_HIGH_SCORE)
    assert result is not None
    assert len(result.nodes) == 2
    assert result.nodes[0].id == "protein:TP53" or result.nodes[1].id == "protein:TP53"
    assert len(result.edges) == 1
    assert result.edges[0].relation == "INTERACTS_WITH"
    assert result.edges[0].properties["score"] == 0.998


def test_string_low_score_returns_none():
    ingester = StringIngester()
    result = ingester.normalize(SAMPLE_LOW_SCORE)
    assert result is None


def test_string_empty_record_returns_none():
    ingester = StringIngester()
    result = ingester.normalize({})
    assert result is None
