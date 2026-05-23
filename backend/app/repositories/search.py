from app.db.postgres import get_pg_pool
from app.models.search import SearchResult, Suggestion


async def search_entities(query: str, entity_type: str | None, min_relevance: float, limit: int) -> list[SearchResult]:
    pool = await get_pg_pool()
    # Full-text search with per-type limit when no filter (ensures diversity)
    if entity_type is None:
        per_type = max(3, limit // 5 + 1)
        rows = await pool.fetch("""
            WITH q AS (SELECT websearch_to_tsquery('english', $1) AS tq)
            SELECT id, type, label, description, relevance FROM (
                SELECT id, type, label, description,
                       ts_rank(search_vector, q.tq) AS relevance,
                       ROW_NUMBER() OVER (PARTITION BY type ORDER BY ts_rank(search_vector, q.tq) DESC) AS rn
                FROM entities_search, q
                WHERE search_vector @@ q.tq
                  AND ts_rank(search_vector, q.tq) >= $2
            ) ranked
            WHERE rn <= $3
            ORDER BY relevance DESC
            LIMIT $4
        """, query, min_relevance, per_type, limit)
    else:
        rows = await pool.fetch("""
            WITH q AS (SELECT websearch_to_tsquery('english', $1) AS tq)
            SELECT id, type, label, description,
                   ts_rank(search_vector, q.tq) AS relevance
            FROM entities_search, q
            WHERE type = $2
              AND search_vector @@ q.tq
              AND ts_rank(search_vector, q.tq) >= $3
            ORDER BY relevance DESC
            LIMIT $4
        """, query, entity_type, min_relevance, limit)

    # Fallback to ILIKE if full-text returned nothing
    if not rows:
        if entity_type is None:
            rows = await pool.fetch("""
                SELECT id, type, label, description, 0.5 AS relevance FROM (
                    SELECT id, type, label, description,
                        ROW_NUMBER() OVER (PARTITION BY type ORDER BY label) AS rn
                    FROM entities_search
                    WHERE label ILIKE $1
                ) ranked
                WHERE rn <= $2
                ORDER BY label
                LIMIT $3
            """, f"%{query}%", max(3, limit // 5 + 1), limit)
        else:
            rows = await pool.fetch("""
                SELECT id, type, label, description, 0.5 AS relevance
                FROM entities_search
                WHERE type = $1 AND label ILIKE $2
                ORDER BY label
                LIMIT $3
            """, entity_type, f"%{query}%", limit)

    return [
        SearchResult(id=r["id"], type=r["type"], label=r["label"],
                     description=r["description"], relevance=r["relevance"])
        for r in rows
    ]


async def get_suggestions(query: str, limit: int = 10) -> list[Suggestion]:
    pool = await get_pg_pool()
    # Use ROW_NUMBER to take up to N per type, ensuring diversity
    per_type = max(3, limit // 5 + 1)
    rows = await pool.fetch("""
        SELECT id, type, label FROM (
            SELECT id, type, label,
                ROW_NUMBER() OVER (
                    PARTITION BY type
                    ORDER BY
                        CASE WHEN label ILIKE $2 THEN 0 ELSE 1 END,
                        position(lower($3) in lower(label)),
                        label
                ) AS rn
            FROM entities_search
            WHERE label ILIKE $1
        ) ranked
        WHERE rn <= $4
        ORDER BY
            CASE WHEN label ILIKE $2 THEN 0 ELSE 1 END,
            position(lower($3) in lower(label)),
            label
        LIMIT $5
    """, f"%{query}%", f"{query}%", query, per_type, limit)
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
