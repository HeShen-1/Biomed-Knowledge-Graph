from ingest.sources.uniprot import UniProtIngester

SAMPLE = {
    "primaryAccession": "P04637",
    "genes": [{"geneName": {"value": "TP53"}}],
    "proteinDescription": {"recommendedName": {"fullName": {"value": "Cellular tumor antigen p53"}}},
    "sequence": {"value": "MEEPQSDPSV...", "length": 393},
    "comments": [{"commentType": "DISEASE", "disease": {"diseaseId": "Li-Fraumeni syndrome"}}],
}


def test_uniprot_normalize_snapshot():
    ingester = UniProtIngester()
    result = ingester.normalize(SAMPLE)
    assert result is not None
    assert len(result.nodes) == 2  # protein + gene
    protein = [n for n in result.nodes if n.type == "protein"][0]
    assert protein.id == "protein:P04637"
    assert protein.properties["name"] == "Cellular tumor antigen p53"
    gene = [n for n in result.nodes if n.type == "gene"][0]
    assert gene.id == "gene:TP53"
    assert len(result.edges) == 2  # ENCODES + ASSOCIATED_WITH


def test_uniprot_empty_record_returns_none():
    ingester = UniProtIngester()
    result = ingester.normalize({})
    assert result is None


def test_uniprot_build_queries():
    ingester = UniProtIngester()
    result = ingester.normalize(SAMPLE)
    queries = ingester.build_queries([result])
    assert len(queries) > 0
    assert any("MERGE" in q for q in queries)
