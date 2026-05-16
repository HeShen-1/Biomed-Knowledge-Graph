from pydantic import BaseModel
from datetime import datetime


class NormalizedNode(BaseModel):
    id: str
    type: str
    properties: dict


class NormalizedEdge(BaseModel):
    from_id: str
    to_id: str
    relation: str
    properties: dict


class NormalizedRecord(BaseModel):
    nodes: list[NormalizedNode]
    edges: list[NormalizedEdge]
    source: str
    fetched_at: datetime
