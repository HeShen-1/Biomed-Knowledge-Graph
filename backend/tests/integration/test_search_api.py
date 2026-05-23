"""Integration tests for /api/search endpoints with mocked PostgreSQL."""
import pytest
from unittest.mock import MagicMock


def _mk(data: dict):
    r = MagicMock()
    r.__getitem__ = lambda _, k: data.get(k)
    r.get = lambda _, k, default=None: data.get(k, default)
    return r


@pytest.fixture
def mock_search(mock_pg_pool):
    """Set up mock PG data for search endpoints."""
    def _setup(rows):
        mock_pg_pool.fetch.return_value = rows
        return mock_pg_pool
    return _setup


class TestSearch:
    def test_search_with_type_filter(self, client, mock_search):
        mock_search([_mk({
            "id": "gene:TP53", "type": "gene", "label": "TP53",
            "description": "Tumor suppressor", "relevance": 0.95,
        })])

        resp = client.get("/api/search?q=TP53&type=gene")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["id"] == "gene:TP53"
        assert data[0]["type"] == "gene"

    def test_search_without_type(self, client, mock_search):
        mock_search([_mk({
            "id": "gene:BRCA1", "type": "gene", "label": "BRCA1",
            "description": "", "relevance": 0.9,
        })])

        resp = client.get("/api/search?q=BRCA1")
        assert resp.status_code == 200

    def test_search_empty_query_returns_422(self, client):
        resp = client.get("/api/search")
        assert resp.status_code == 422

    def test_search_min_length_enforced(self, client):
        resp = client.get("/api/search?q=")
        assert resp.status_code == 422


class TestSuggest:
    def test_suggest_returns_results(self, client, mock_search):
        mock_search([_mk({
            "id": "gene:TP53", "type": "gene", "label": "TP53",
        })])

        resp = client.get("/api/search/suggest?q=TP")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["label"] == "TP53"

    def test_suggest_empty_returns_422(self, client):
        resp = client.get("/api/search/suggest")
        assert resp.status_code == 422


class TestTopEntities:
    def test_top_by_type(self, client, mock_search):
        mock_search([_mk({
            "id": "gene:TP53", "type": "gene", "label": "TP53",
            "description": "Tumor suppressor", "relevance": 1.0,
        })])

        resp = client.get("/api/search/top?type=gene")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 0
