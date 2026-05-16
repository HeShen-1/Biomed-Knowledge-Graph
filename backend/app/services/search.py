from app.models.search import SearchResult, Suggestion, SearchParams, TopEntitiesParams
from app.repositories import search as search_repo


async def search(params: SearchParams) -> list[SearchResult]:
    return await search_repo.search_entities(params.q, params.type, params.min_relevance, params.limit)


async def suggest(query: str, limit: int = 10) -> list[Suggestion]:
    return await search_repo.get_suggestions(query, limit)


async def top_entities(params: TopEntitiesParams) -> list[SearchResult]:
    return await search_repo.get_top_entities(params.type, params.limit)
