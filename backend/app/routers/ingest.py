from fastapi import APIRouter, Query
from app.models.ingest import SyncStatus, SyncLog
from app.services import ingest as ingest_svc

router = APIRouter(prefix="/api/ingest", tags=["ingest"])


@router.post("/sync/{source}")
async def trigger_sync(source: str):
    return await ingest_svc.trigger_sync(source)


@router.get("/status", response_model=list[SyncStatus])
async def get_status():
    return await ingest_svc.get_all_status()


@router.get("/logs", response_model=list[SyncLog])
async def get_logs(source: str | None = Query(default=None), limit: int = Query(default=20, ge=1, le=100)):
    return await ingest_svc.get_logs(source, limit)
