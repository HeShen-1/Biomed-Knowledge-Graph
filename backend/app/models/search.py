from pydantic import BaseModel
from typing import Optional

class SearchResult(BaseModel):
    id: str
    type: str
    label: str
    description: Optional[str] = None
    relevance: float

class Suggestion(BaseModel):
    id: str
    type: str
    label: str

class SearchParams(BaseModel):
    q: str
    type: Optional[str] = None
    min_relevance: float = 0.3
    limit: int = 20

class TopEntitiesParams(BaseModel):
    type: str
    limit: int = 20
