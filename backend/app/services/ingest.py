from app.models.ingest import SyncStatus, SyncLog
from app.repositories import ingest as ingest_repo

SOURCES = ["pubmed", "uniprot", "chembl", "opentargets", "string"]


async def trigger_sync(source: str) -> dict:
    if source not in SOURCES:
        from app.errors import InvalidParamError
        raise InvalidParamError(f"Unknown source: {source}")
    # Lazy import to avoid service-layer coupling with Celery task definitions
    from tasks.celery_app import celery_app
    celery_app.send_task("sync_source", args=[source])
    return {"status": "triggered", "source": source}


async def get_all_status() -> list[SyncStatus]:
    return await ingest_repo.get_all_status()


async def get_logs(source: str | None = None, limit: int = 20) -> list[SyncLog]:
    return await ingest_repo.get_logs(source, limit)
