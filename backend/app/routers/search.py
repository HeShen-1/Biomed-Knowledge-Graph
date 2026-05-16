from fastapi import APIRouter, Query
from app.models.search import SearchResult, Suggestion, SearchParams, TopEntitiesParams
from app.services import search as search_svc

router = APIRouter(prefix="/api/search", tags=["search"])


@router.get("", response_model=list[SearchResult])
async def search(
    q: str = Query(min_length=1),
    type: str | None = Query(default=None),
    min_relevance: float = Query(default=0.01, ge=0.0, le=1.0),
    limit: int = Query(default=20, ge=1, le=100),
):
    params = SearchParams(q=q, type=type, min_relevance=min_relevance, limit=limit)
    return await search_svc.search(params)


@router.get("/suggest", response_model=list[Suggestion])
async def suggest(q: str = Query(min_length=1), limit: int = Query(default=10, ge=1, le=20)):
    return await search_svc.suggest(q, limit)


@router.get("/top", response_model=list[SearchResult])
async def top(type: str = Query(), limit: int = Query(default=20, ge=1, le=100)):
    params = TopEntitiesParams(type=type, limit=limit)
    return await search_svc.top_entities(params)
