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


def test_chembl_molecule_normalize():
    ingester = ChEMBLIngester()
    result = ingester.normalize(MOLECULE_SAMPLE)
    assert result is not None
    assert len(result.nodes) == 1
    assert result.nodes[0].id == "compound:CHEMBL25"
    assert result.nodes[0].properties["name"] == "Aspirin"


def test_chembl_mechanism_normalize():
    ingester = ChEMBLIngester()
    result = ingester.normalize(MECHANISM_SAMPLE)
    assert result is not None
    assert len(result.edges) == 1
    assert result.edges[0].relation == "BINDS_TO"
    assert result.edges[0].from_id == "compound:CHEMBL25"
    assert result.edges[0].to_id == "protein:CHEMBL209"


def test_chembl_empty_record_returns_none():
    ingester = ChEMBLIngester()
    result = ingester.normalize({})
    assert result is None
