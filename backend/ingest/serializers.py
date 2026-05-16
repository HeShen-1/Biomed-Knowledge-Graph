from app.db.neo4j import get_neo4j_driver


async def batch_write(queries: list[str]) -> dict:
    driver = await get_neo4j_driver()
    added = 0
    updated = 0
    async with driver.session() as session:
        for query in queries:
            result = await session.run(query)
            summary = await result.consume()
            added += summary.counters.nodes_created
            updated += summary.counters.properties_set
    return {"added": added, "updated": updated}
