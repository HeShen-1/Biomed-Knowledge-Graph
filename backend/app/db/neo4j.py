import asyncio
from neo4j import AsyncGraphDatabase, AsyncDriver, basic_auth
from app.config import settings

_driver: AsyncDriver | None = None
_lock = asyncio.Lock()


async def get_neo4j_driver() -> AsyncDriver:
    global _driver
    if _driver is None:
        async with _lock:
            if _driver is None:
                _driver = AsyncGraphDatabase.driver(
                    settings.neo4j_uri,
                    auth=basic_auth(settings.neo4j_user, settings.neo4j_password),
                    max_connection_pool_size=20,
                    connection_acquisition_timeout=10.0,
                    max_transaction_retry_time=30.0,
                    max_connection_lifetime=3600,
                    keep_alive=True,
                )
    return _driver


async def close_neo4j_driver():
    global _driver
    if _driver:
        await _driver.close()
        _driver = None


async def verify_indexes():
    """Verify indexes exist on all node types. Logs warnings for missing indexes.
    Timeout-limited to avoid blocking startup when Neo4j is unreachable."""
    import logging
    logger = logging.getLogger(__name__)

    expected_labels = ["Gene", "Protein", "Compound", "Disease", "Article"]
    driver = await get_neo4j_driver()

    try:
        records, _, _ = await asyncio.wait_for(
            driver.execute_query(
                "SHOW INDEXES YIELD labelsOrTypes, properties WHERE labelsOrTypes IS NOT NULL"
            ),
            timeout=5.0,
        )
        existing: set[str] = set()
        for rec in records:
            labels_val = rec.get("labelsOrTypes")
            props_val = rec.get("properties")
            labels = list(labels_val) if labels_val else []
            props = list(props_val) if props_val else []
            if labels and "id" in props:
                existing.add(labels[0])

        for label in expected_labels:
            if label not in existing:
                logger.warning(
                    "Missing Neo4j index on :%s(id). "
                    "Create with: CREATE INDEX FOR (n:%s) ON (n.id)",
                    label, label,
                )

        logger.info(
            "Neo4j index check: %d/%d indexes present", len(existing), len(expected_labels)
        )
    except (asyncio.TimeoutError, Exception) as exc:
        msg = "Neo4j unavailable, skipping index verification" if isinstance(exc, asyncio.TimeoutError) else str(exc)
        logger.warning("Failed to verify Neo4j indexes: %s", msg)
