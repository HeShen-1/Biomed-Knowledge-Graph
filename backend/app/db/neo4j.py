import asyncio
from neo4j import AsyncGraphDatabase, AsyncDriver
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
                    auth=(settings.neo4j_user, settings.neo4j_password),
                    max_connection_pool_size=20,
                    connection_acquisition_timeout=10.0,
                    max_transaction_retry_time=30.0,
                )
    return _driver


async def close_neo4j_driver():
    global _driver
    if _driver:
        await _driver.close()
        _driver = None
