import os
import pytest
import asyncio
from app.db.neo4j import get_neo4j_driver, close_neo4j_driver


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def neo4j_driver():
    if not os.environ.get("BIOMED_TEST_DB"):
        pytest.skip("Set BIOMED_TEST_DB=1 to run tests that require Neo4j")
    driver = await get_neo4j_driver()
    await driver.execute_query("MATCH (n) DETACH DELETE n")
    yield driver
    await close_neo4j_driver()
