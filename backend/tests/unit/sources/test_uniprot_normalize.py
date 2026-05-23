import pytest
from ingest.sources.uniprot import UniProtIngester

SAMPLE = {
    "primaryAccession": "P04637",
    "genes": [{"geneName": {"value": "TP53"}}],
    "proteinDescription": {"recommendedName": {"fullName": {"value": "Cellular tumor antigen p53"}}},
    "sequence": {"value": "MEEPQSDPSV...", "length": 393},
    "comments": [{"commentType": "DISEASE", "disease": {"diseaseId": "Li-Fraumeni syndrome", "diseaseAcronym": "LFS1"}}],
}


@pytest.mark.asyncio
async def test_uniprot_normalize_snapshot():
    ingester = UniProtIngester()
    result = await ingester.normalize(SAMPLE)
    assert result is not None
    assert len(result.nodes) == 3  # protein + gene + disease
    protein = [n for n in result.nodes if n.type == "protein"][0]
    assert protein.id == "protein:P04637"
    assert protein.properties["name"] == "Cellular tumor antigen p53"
    gene = [n for n in result.nodes if n.type == "gene"][0]
    assert gene.id == "gene:TP53"
    disease = [n for n in result.nodes if n.type == "disease"][0]
    assert disease.id == "disease:LFS1"
    assert disease.properties["acronym"] == "LFS1"
    assert len(result.edges) == 2  # ENCODES + ASSOCIATED_WITH
    associated = [e for e in result.edges if e.relation == "ASSOCIATED_WITH"][0]
    assert associated.from_type == "protein"
    assert associated.to_type == "disease"


@pytest.mark.asyncio
async def test_uniprot_empty_record_returns_none():
    ingester = UniProtIngester()
    result = await ingester.normalize({})
    assert result is None


@pytest.mark.asyncio
async def test_uniprot_build_queries():
    ingester = UniProtIngester()
    result = await ingester.normalize(SAMPLE)
    statements = ingester.build_queries([result])
    assert len(statements) > 0
    assert isinstance(statements[0], tuple)
    assert "MERGE" in statements[0][0]
    assert isinstance(statements[0][1], dict)
