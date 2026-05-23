"""Integration tests for /api/graph endpoints with mocked Neo4j."""
import pytest
from unittest.mock import MagicMock
from .conftest import _make_eager_result


def _mk(data: dict):
    r = MagicMock()
    r.__getitem__ = lambda _, k: data.get(k)
    r.get = lambda _, k, default=None: data.get(k, default)
    return r


@pytest.fixture
def mock_graph(mock_neo4j_driver):
    """Set up mock Neo4j data for graph endpoints."""
    def _setup(records):
        mock_neo4j_driver.execute_query.return_value = _make_eager_result(records)
        return mock_neo4j_driver
    return _setup


class TestNodeDetail:
    def test_returns_node_with_neighbors(self, client, mock_graph):
        rec = _mk({
            "n": {"id": "gene:TP53", "symbol": "TP53", "name": "Tumor Protein p53"},
            "r": None,
            "neighbor": None,
            "neighbor_labels": None,
        })
        mock_graph([rec])

        resp = client.get("/api/graph/node/gene/gene:TP53")
        assert resp.status_code == 200
        data = resp.json()
        assert data["node"]["id"] == "gene:TP53"
        assert data["node"]["type"] == "gene"
        assert data["node"]["properties"]["symbol"] == "TP53"

    def test_unknown_type_returns_400(self, client):
        resp = client.get("/api/graph/node/cell/foo")
        assert resp.status_code == 400

    def test_empty_result_returns_404(self, client, mock_graph):
        mock_graph([])
        resp = client.get("/api/graph/node/gene/nonexistent")
        assert resp.status_code == 404


class TestExpand:
    def test_expand_with_depth_1(self, client, mock_graph):
        rec = _mk({
            "start": {"id": "gene:BRCA1", "name": "BRCA1"},
            "neighbor": {"id": "protein:P38398", "name": "BRCA1 protein"},
            "rels": [],
            "neighbor_labels": ["Protein"],
        })
        mock_graph([rec])

        resp = client.get("/api/graph/expand/gene/gene:BRCA1?depth=1&limit=10")
        assert resp.status_code == 200
        data = resp.json()
        assert "nodes" in data
        assert "edges" in data

    def test_expand_invalid_type_returns_400(self, client):
        resp = client.get("/api/graph/expand/cell/foo")
        assert resp.status_code == 400

    def test_expand_depth_exceeds_limit_returns_422(self, client):
        resp = client.get("/api/graph/expand/gene/foo?depth=10")
        assert resp.status_code == 422


class TestPath:
    def test_path_invalid_format_returns_400(self, client):
        resp = client.get("/api/graph/path?from=invalid&to=gene:TP53")
        assert resp.status_code == 400


class TestProteinNetwork:
    def test_network_returns_neighbors(self, client, mock_graph):
        rec = _mk({
            "a": {"id": "protein:P04637", "name": "TP53"},
            "b": {"id": "protein:P38398", "name": "BRCA1"},
            "r": {"score": 0.95},
        })
        mock_graph([rec])

        resp = client.get("/api/graph/network/P04637")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["nodes"]) >= 1


class TestHealth:
    def test_health_returns_ok(self, client):
        resp = client.get("/api/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"
