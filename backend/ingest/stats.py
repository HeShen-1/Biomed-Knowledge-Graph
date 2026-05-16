from datetime import datetime, timezone
from app.db.postgres import get_pg_pool


async def collect_stats(source: str, stats: dict):
    pool = await get_pg_pool()
    now = datetime.now(timezone.utc)
    await pool.execute("""
        INSERT INTO ingest_status (source, last_sync_at, status, records_added, records_updated, records_failed)
        VALUES ($1, $2, 'idle', $3, $4, $5)
        ON CONFLICT (source) DO UPDATE SET
            last_sync_at = EXCLUDED.last_sync_at,
            status = 'idle',
            records_added = ingest_status.records_added + EXCLUDED.records_added,
            records_updated = ingest_status.records_updated + EXCLUDED.records_updated,
            records_failed = ingest_status.records_failed + EXCLUDED.records_failed
    """, source, now, stats["added"], stats["updated"], stats["failed"])
