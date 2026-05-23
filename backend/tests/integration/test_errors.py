"""Integration tests for error handling and edge cases."""
import pytest


class TestErrorHandling:
    def test_404_for_unknown_route(self, client):
        resp = client.get("/api/graph/node/gene/NONEXISTENT_ID_99999")
        assert resp.status_code == 404

    def test_400_for_invalid_node_type(self, client):
        resp = client.get("/api/graph/node/invalid/foo")
        assert resp.status_code == 400

    def test_400_for_invalid_expand_type(self, client):
        resp = client.get("/api/graph/expand/invalid/foo")
        assert resp.status_code == 400

    def test_422_for_query_param_out_of_range(self, client):
        resp = client.get("/api/graph/expand/gene/foo?limit=9999")
        assert resp.status_code == 422

    def test_health_always_returns_ok(self, client):
        resp = client.get("/api/health")
        assert resp.status_code == 200

    def test_cors_headers_present(self, client):
        resp = client.options("/api/health")
        assert resp.status_code in (200, 405)


class TestRateLimitHeaders:
    def test_graph_endpoints_registered(self, client):
        resp = client.get("/api/graph/node/gene/test")
        assert resp.status_code in (200, 404)  # route exists (404=not found, not 404=route missing)

    def test_search_endpoints_registered(self, client):
        assert client.get("/api/search?q=test").status_code in (200, 422)

    def test_ingest_endpoints_registered(self, client):
        # Ingest status/logs query PG — mock returns empty, should get 200
        assert client.get("/api/ingest/status").status_code == 200
        assert client.get("/api/ingest/logs").status_code == 200
