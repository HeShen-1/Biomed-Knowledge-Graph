from ingest.sources.opentargets import OpenTargetsIngester

SAMPLE = {
    "target": {"id": "ENSG00000141510", "approvedSymbol": "TP53"},
    "disease": {"id": "MONDO_0016575", "name": "breast carcinoma"},
    "score": 0.85,
    "datasourceScores": [
        {"componentId": "genetic_association", "score": 0.9},
        {"componentId": "rna_expression", "score": 0.7},
    ],
}


def test_opentargets_normalize_snapshot():
    ingester = OpenTargetsIngester()
    result = ingester.normalize(SAMPLE)
    assert result is not None
    assert len(result.nodes) == 2  # gene + disease
    gene = [n for n in result.nodes if n.type == "gene"][0]
    assert gene.id == "gene:TP53"
    disease = [n for n in result.nodes if n.type == "disease"][0]
    assert disease.id == "disease:MONDO_0016575"
    assert len(result.edges) == 1
    assert result.edges[0].relation == "TARGETS"
    assert result.edges[0].properties["score"] == 0.85


def test_opentargets_empty_record_returns_none():
    ingester = OpenTargetsIngester()
    result = ingester.normalize({"target": {}, "disease": {}})
    assert result is None
