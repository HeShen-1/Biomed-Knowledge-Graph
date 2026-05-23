from pydantic import BaseModel, Field
from typing import Literal

NodeType = Literal["gene", "protein", "compound", "disease", "article", "unknown"]


class NodeModel(BaseModel):
    id: str
    type: NodeType
    properties: dict = Field(default_factory=dict)


class EdgeModel(BaseModel):
    relation: str
    direction: Literal["in", "out"]
    source_id: str = ""
    target_id: str = ""
    node: NodeModel = Field(default_factory=lambda: NodeModel(id="", type="unknown", properties={}))
    properties: dict = Field(default_factory=dict)


class SubgraphModel(BaseModel):
    nodes: list[NodeModel]
    edges: list[EdgeModel]
    total_edges: int


class NodeDetailResponse(BaseModel):
    node: NodeModel
    neighbors: list[EdgeModel]
    total_edges: int


class ExpandParams(BaseModel):
    depth: int = Field(default=1, ge=1, le=3)
    limit: int = Field(default=50, ge=1, le=200)


class PathParams(BaseModel):
    from_id: str
    to_id: str
    max_length: int = Field(default=4, ge=1, le=6)
