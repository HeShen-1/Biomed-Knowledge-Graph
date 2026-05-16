from fastapi import APIRouter, Query
from app.models.graph import NodeDetailResponse, SubgraphModel, ExpandParams, PathParams
from app.services import graph as graph_svc
from app.errors import InvalidParamError

router = APIRouter(prefix="/api/graph", tags=["graph"])

VALID_TYPES = {"gene", "protein", "compound", "disease", "article"}


@router.get("/node/{type}/{id}", response_model=NodeDetailResponse)
async def get_node_detail(type: str, id: str):
    if type not in VALID_TYPES:
        raise InvalidParamError(f"Invalid node type: {type}")
    return await graph_svc.get_node(type, id)


@router.get("/expand/{type}/{id}", response_model=SubgraphModel)
async def expand_node(
    type: str, id: str,
    depth: int = Query(default=1, ge=1, le=3),
    limit: int = Query(default=50, ge=1, le=200),
):
    if type not in VALID_TYPES:
        raise InvalidParamError(f"Invalid node type: {type}")
    params = ExpandParams(depth=depth, limit=limit)
    return await graph_svc.expand(type, id, params)


@router.get("/path", response_model=SubgraphModel)
async def shortest_path(
    from_: str = Query(alias="from"),
    to: str = Query(),
    max_length: int = Query(default=4, ge=1, le=6),
):
    params = PathParams(from_id=from_, to_id=to, max_length=max_length)
    return await graph_svc.path(params)


@router.get("/network/{protein_id}", response_model=SubgraphModel)
async def protein_network(
    protein_id: str,
    min_score: float = Query(default=0.7, ge=0.0, le=1.0),
    limit: int = Query(default=100, ge=1, le=500),
):
    return await graph_svc.protein_network(protein_id, min_score, limit)
