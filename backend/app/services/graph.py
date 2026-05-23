from app.models.graph import NodeDetailResponse, SubgraphModel, ExpandParams, PathParams
from app.repositories import graph as graph_repo
from app.errors import InvalidParamError


async def get_node(type_: str, id_: str, limit: int = 100) -> NodeDetailResponse:
    return await graph_repo.get_node_detail(type_, id_, limit)


async def expand(type_: str, id_: str, params: ExpandParams) -> SubgraphModel:
    return await graph_repo.expand_node(type_, id_, params.depth, params.limit)


async def path(params: PathParams) -> SubgraphModel:
    if ":" not in params.from_id:
        raise InvalidParamError(f"from_id must be in format 'type:id', got: {params.from_id}")
    if ":" not in params.to_id:
        raise InvalidParamError(f"to_id must be in format 'type:id', got: {params.to_id}")
    from_type, from_id = params.from_id.split(":", 1)
    to_type, to_id = params.to_id.split(":", 1)
    return await graph_repo.find_path(from_type, from_id, to_type, to_id, params.max_length)


async def protein_network(protein_id: str, min_score: float = 0.7, limit: int = 100) -> SubgraphModel:
    return await graph_repo.protein_network(protein_id, min_score, limit)
