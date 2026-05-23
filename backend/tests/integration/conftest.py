import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient
from app.main import app


def _make_eager_result(records: list):
    """Fake Neo4j EagerResult supporting both .records and tuple unpack."""
    r = MagicMock()
    r.records = records
    r.summary = MagicMock()
    r.keys = MagicMock(return_value=[])
    # Support tuple unpack: records, summary, keys = await execute_query(...)
    r.__iter__ = lambda s: iter([r.records, r.summary, r.keys])
    return r


@pytest.fixture(autouse=True)
def mock_neo4j_driver(mocker):
    """Mock Neo4j driver — all tests run without a real DB."""
    mock_driver = AsyncMock()
    mock_driver.execute_query.return_value = _make_eager_result([])
    mocker.patch("app.db.neo4j.get_neo4j_driver", return_value=mock_driver)
    mocker.patch("app.repositories.graph.get_neo4j_driver", return_value=mock_driver)
    return mock_driver


@pytest.fixture(autouse=True)
def mock_pg_pool(mocker):
    """Mock PostgreSQL pool — all tests run without a real DB."""
    mock_pool = AsyncMock()
    mock_pool.fetch.return_value = []
    mocker.patch("app.db.postgres.get_pg_pool", return_value=mock_pool)
    mocker.patch("app.repositories.search.get_pg_pool", return_value=mock_pool)
    mocker.patch("app.repositories.ingest.get_pg_pool", return_value=mock_pool)
    return mock_pool


@pytest.fixture
def client():
    return TestClient(app)
