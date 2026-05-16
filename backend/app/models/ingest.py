from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class SyncStatus(BaseModel):
    source: str
    last_sync_at: Optional[datetime] = None
    status: str
    records_added: int = 0
    records_updated: int = 0
    records_failed: int = 0

class SyncLog(BaseModel):
    id: int
    source: str
    started_at: datetime
    finished_at: Optional[datetime] = None
    status: str
    message: Optional[str] = None
