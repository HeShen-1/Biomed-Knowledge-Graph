from app.db.postgres import get_pg_pool
from app.models.search import SearchResult, Suggestion


async def search_entities(query: str, entity_type: str | None, min_relevance: float, limit: int) -> list[SearchResult]:
    pool = await get_pg_pool()
    rows = await pool.fetch("""
        WITH q AS (SELECT websearch_to_tsquery('english', $1) AS tq)
        SELECT id, type, label, description,
               ts_rank(search_vector, q.tq) AS relevance
        FROM entities_search, q
        WHERE ($2::text IS NULL OR type = $2)
          AND search_vector @@ q.tq
          AND ts_rank(search_vector, q.tq) >= $3
        ORDER BY relevance DESC
        LIMIT $4
    """, query, entity_type, min_relevance, limit)
    return [
        SearchResult(id=r["id"], type=r["type"], label=r["label"],
                     description=r["description"], relevance=r["relevance"])
        for r in rows
    ]


async def get_suggestions(query: str, limit: int = 10) -> list[Suggestion]:
    pool = await get_pg_pool()
    rows = await pool.fetch("""
        SELECT id, type, label FROM entities_search
        WHERE label ILIKE $1
        ORDER BY label LIMIT $2
    """, f"{query}%", limit)
    return [Suggestion(id=r["id"], type=r["type"], label=r["label"]) for r in rows]


async def get_top_entities(entity_type: str, limit: int = 20) -> list[SearchResult]:
    pool = await get_pg_pool()
    rows = await pool.fetch("""
        SELECT id, type, label, description FROM entities_search
        WHERE type = $1
        ORDER BY search_count DESC
        LIMIT $2
    """, entity_type, limit)
    return [
        SearchResult(id=r["id"], type=r["type"], label=r["label"],
                     description=r["description"], relevance=1.0)
        for r in rows
    ]
