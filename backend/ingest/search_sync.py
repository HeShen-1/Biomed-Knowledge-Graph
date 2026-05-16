from app.db.postgres import get_pg_pool
from ingest.models import NormalizedRecord, NormalizedNode


async def sync_search_index(batch: list[NormalizedRecord]):
    """Write node labels and descriptions to PostgreSQL entities_search for full-text indexing."""
    pool = await get_pg_pool()
    rows = []
    for record in batch:
        for node in record.nodes:
            label = _make_label(node)
            description = _make_description(node)
            rows.append((node.id, node.type, label, description))
    async with pool.acquire() as conn:
        await conn.executemany(
            """
            INSERT INTO entities_search (id, type, label, description, search_vector)
            VALUES ($1, $2, $3, $4, to_tsvector('english', $3 || ' ' || COALESCE($4, '')))
            ON CONFLICT (id) DO UPDATE SET
                label = EXCLUDED.label,
                description = EXCLUDED.description,
                search_vector = EXCLUDED.search_vector,
                search_count = entities_search.search_count + 1
            """,
            rows,
        )


def _make_label(node: NormalizedNode) -> str:
    props = node.properties
    return (
        props.get("name")
        or props.get("symbol")
        or props.get("title")
        or node.id
    )


def _make_description(node: NormalizedNode) -> str | None:
    props = node.properties
    if node.type == "protein":
        return f"Protein: length={props.get('length', '?')}"
    if node.type == "gene":
        return f"Gene symbol: {props.get('symbol', '?')}"
    if node.type == "compound":
        parts = []
        if props.get("mw"):
            parts.append(f"MW={props['mw']}")
        if props.get("smiles"):
            parts.append(props["smiles"][:100])
        return "Compound: " + ", ".join(parts) if parts else None
    if node.type == "disease":
        return f"Disease: {props.get('name', '')}"
    if node.type == "article":
        journal = props.get("journal", "")
        year = props.get("year", "")
        return f"Article: {journal} ({year})"
    return None
