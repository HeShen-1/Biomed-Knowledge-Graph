from app.db.postgres import get_pg_pool
from app.models.ingest import SyncStatus, SyncLog


async def get_all_status() -> list[SyncStatus]:
    pool = await get_pg_pool()
    rows = await pool.fetch("""
        SELECT source, last_sync_at, status, records_added, records_updated, records_failed
        FROM ingest_status ORDER BY source
    """)
    return [SyncStatus(**dict(r)) for r in rows]


async def get_logs(source: str | None = None, limit: int = 20) -> list[SyncLog]:
    pool = await get_pg_pool()
    if source:
        rows = await pool.fetch(
            "SELECT id, source, started_at, finished_at, status, message FROM ingest_log WHERE source=$1 ORDER BY id DESC LIMIT $2",
            source, limit)
    else:
        rows = await pool.fetch(
            "SELECT id, source, started_at, finished_at, status, message FROM ingest_log ORDER BY id DESC LIMIT $1",
            limit)
    return [SyncLog(**dict(r)) for r in rows]
