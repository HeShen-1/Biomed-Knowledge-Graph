# serializers.py is the designated DB boundary layer for the ingest module.
# Importing from app.db.neo4j here is intentional — this is where the data hits the graph.
from app.db.neo4j import get_neo4j_driver

VALID_LABELS = {"Gene", "Protein", "Compound", "Disease", "Article"}
VALID_RELATIONS = {"MENTIONS", "ENCODES", "ASSOCIATED_WITH", "BINDS_TO",
                    "INTERACTS_WITH", "TARGETS", "TREATS"}


def safe_label(node_type: str) -> str:
    label = node_type.capitalize()
    if label not in VALID_LABELS:
        raise ValueError(f"Rejected label: {label}")
    return label


def safe_relation(relation: str) -> str:
    if relation not in VALID_RELATIONS:
        raise ValueError(f"Rejected relation: {relation}")
    return relation


async def batch_write(statements: list[tuple[str, dict]]) -> dict:
    driver = await get_neo4j_driver()
    added = 0
    updated = 0
    async with driver.session() as session:
        async with await session.begin_transaction() as tx:
            for cypher, params in statements:
                result = await tx.run(cypher, params)
                summary = await result.consume()
                added += summary.counters.nodes_created
                updated += summary.counters.properties_set
    return {"added": added, "updated": updated}
