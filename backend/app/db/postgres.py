import asyncpg
from app.config import settings

_pool: asyncpg.Pool | None = None


async def get_pg_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(dsn=settings.postgres_dsn, min_size=2, max_size=10)
    return _pool


async def close_pg_pool():
    global _pool
    if _pool:
        await _pool.close()
        _pool = None
