from app.db.neo4j import get_neo4j_driver
from app.models.graph import NodeModel, EdgeModel, NodeDetailResponse, SubgraphModel
from app.errors import EntityNotFoundError, GraphTimeoutError
from typing import Optional

NODE_TYPE_MAP = {
    "gene": "Gene",
    "protein": "Protein",
    "compound": "Compound",
    "disease": "Disease",
    "article": "Article",
}


async def get_node_detail(node_type: str, node_id: str) -> NodeDetailResponse:
    label = NODE_TYPE_MAP.get(node_type)
    if not label:
        raise EntityNotFoundError(f"Unknown node type: {node_type}")

    driver = await get_neo4j_driver()
    cypher = f"""
        MATCH (n:{label} {{id: $node_id}})
        OPTIONAL MATCH (n)-[r]-(neighbor)
        RETURN n, r, neighbor, labels(neighbor) AS neighbor_labels
        LIMIT 100
    """
    try:
        records = await driver.execute_query(cypher, {"node_id": node_id}, routing_="r")
    except Exception as e:
        if "timeout" in str(e).lower():
            raise GraphTimeoutError("Query timed out")
        raise

    if not records.records:
        raise EntityNotFoundError(f"{node_type} not found: {node_id}")

    node_data = dict(records.records[0]["n"])
    node = NodeModel(id=node_data.pop("id"), type=node_type, properties=node_data)

    neighbors: list[EdgeModel] = []
    for rec in records.records:
        if rec["r"]:
            neighbor_data = dict(rec["neighbor"])
            neighbor_labels = rec["neighbor_labels"]
            matched_type = next((l.lower() for l in NODE_TYPE_MAP.values() if l in neighbor_labels), "unknown")
            rel_props = {k: v for k, v in dict(rec["r"]).items() if not k.startswith("_")}
            neighbor = NodeModel(id=neighbor_data.pop("id", ""), type=matched_type, properties=neighbor_data)
            neighbors.append(EdgeModel(
                relation=rec["r"].type, direction="out",
                node=neighbor, properties=rel_props,
            ))

    return NodeDetailResponse(node=node, neighbors=neighbors, total_edges=len(neighbors))


async def expand_node(node_type: str, node_id: str, depth: int, limit: int) -> SubgraphModel:
    label = NODE_TYPE_MAP.get(node_type)
    driver = await get_neo4j_driver()
    cypher = f"""
        MATCH (start:{label} {{id: $node_id}})-[r*1..{depth}]-(neighbor)
        WITH DISTINCT neighbor
        RETURN neighbor
        LIMIT $limit
    """
    try:
        records = await driver.execute_query(cypher, {"node_id": node_id, "limit": limit})
    except Exception as e:
        if "timeout" in str(e).lower():
            raise GraphTimeoutError("Query timed out")
        raise

    nodes_map: dict[str, NodeModel] = {}
    start_cypher = f"MATCH (n:{label} {{id: $node_id}}) RETURN n"
    start_rec = await driver.execute_query(start_cypher, {"node_id": node_id})
    if start_rec.records:
        sdata = dict(start_rec.records[0]["n"])
        nodes_map[node_id] = NodeModel(id=sdata.pop("id"), type=node_type, properties=sdata)

    for rec in records.records:
        ndata = dict(rec["neighbor"])
        nid = ndata.pop("id", "")
        nlabels = rec["neighbor"].labels
        ntype = next((l.lower() for l in NODE_TYPE_MAP.values() if l in nlabels), "unknown")
        if nid not in nodes_map:
            nodes_map[nid] = NodeModel(id=nid, type=ntype, properties=ndata)

    return SubgraphModel(nodes=list(nodes_map.values()), edges=[], total_edges=len(nodes_map))


async def find_path(from_type: str, from_id: str, to_type: str, to_id: str, max_length: int) -> SubgraphModel:
    from_label = NODE_TYPE_MAP.get(from_type)
    to_label = NODE_TYPE_MAP.get(to_type)
    driver = await get_neo4j_driver()
    cypher = f"""
        MATCH path = shortestPath(
          (a:{from_label} {{id: $from_id}})-[*..{max_length}]-(b:{to_label} {{id: $to_id}})
        )
        UNWIND nodes(path) AS n
        RETURN DISTINCT n
    """
    records = await driver.execute_query(cypher, {"from_id": from_id, "to_id": to_id})
    nodes = [
        NodeModel(id=dict(r["n"])["id"], type=dict(r["n"]).get("type", "unknown"), properties=dict(r["n"]))
        for r in records.records
    ]
    return SubgraphModel(nodes=nodes, edges=[], total_edges=0)


async def protein_network(protein_id: str, min_score: float = 0.7, limit: int = 100) -> SubgraphModel:
    driver = await get_neo4j_driver()
    cypher = """
        MATCH (a:Protein {id: $protein_id})-[r:INTERACTS_WITH]-(b:Protein)
        WHERE r.score >= $min_score
        RETURN a, b, r
        LIMIT $limit
    """
    records = await driver.execute_query(cypher, {"protein_id": protein_id, "min_score": min_score, "limit": limit})
    nodes_map: dict[str, NodeModel] = {}
    for rec in records.records:
        for key in ["a", "b"]:
            ndata = dict(rec[key])
            nid = ndata.pop("id", "")
            if nid not in nodes_map:
                nodes_map[nid] = NodeModel(id=nid, type="protein", properties=ndata)
    return SubgraphModel(nodes=list(nodes_map.values()), edges=[], total_edges=len(nodes_map))
