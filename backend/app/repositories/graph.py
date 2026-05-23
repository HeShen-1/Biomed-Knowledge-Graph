from app.db.neo4j import get_neo4j_driver
from app.models.graph import NodeModel, EdgeModel, NodeDetailResponse, SubgraphModel
from app.errors import EntityNotFoundError, GraphTimeoutError, InvalidParamError
from app.config import settings

NODE_TYPE_MAP = {
    "gene": "Gene",
    "protein": "Protein",
    "compound": "Compound",
    "disease": "Disease",
    "article": "Article",
}


async def get_node_detail(node_type: str, node_id: str, limit: int = 100) -> NodeDetailResponse:
    label = NODE_TYPE_MAP.get(node_type)
    if not label:
        raise EntityNotFoundError(f"Unknown node type: {node_type}")

    full_id = node_id if ":" in node_id else f"{node_type}:{node_id}"
    driver = await get_neo4j_driver()
    cypher = f"""
        MATCH (n:{label} {{id: $full_id}})
        OPTIONAL MATCH (n)-[r]-(neighbor)
        RETURN n, r, neighbor, labels(neighbor) AS neighbor_labels
        LIMIT $limit
    """
    try:
        records = await driver.execute_query(cypher, {"full_id": full_id, "limit": limit})
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
        if rec["r"] is not None:
            neighbor_data = dict(rec["neighbor"])
            neighbor_labels = rec["neighbor_labels"]
            matched_type = next((l.lower() for l in NODE_TYPE_MAP.values() if l in neighbor_labels), "unknown")
            rel_props = {k: v for k, v in dict(rec["r"]).items() if not k.startswith("_")}
            nbr_id = neighbor_data.get("id", "")
            rel = rec["r"]
            src_id = full_id if rel.start_node.get("id", "") == full_id else nbr_id
            tgt_id = nbr_id if src_id == full_id else full_id
            neighbor = NodeModel(id=nbr_id, type=matched_type, properties=neighbor_data)
            neighbors.append(EdgeModel(
                relation=rel.type, direction="out",
                source_id=src_id, target_id=tgt_id,
                node=neighbor, properties=rel_props,
            ))

    return NodeDetailResponse(node=node, neighbors=neighbors, total_edges=len(neighbors))


async def expand_node(node_type: str, node_id: str, depth: int, limit: int) -> SubgraphModel:
    if depth < 1 or depth > settings.graph_max_depth:
        raise InvalidParamError(f"depth must be between 1 and {settings.graph_max_depth}")
    if limit < 1 or limit > settings.graph_max_limit:
        raise InvalidParamError(f"limit must be between 1 and {settings.graph_max_limit}")
    label = NODE_TYPE_MAP.get(node_type)
    full_id = node_id if ":" in node_id else f"{node_type}:{node_id}"
    driver = await get_neo4j_driver()
    cypher = f"""
        MATCH (start:{label} {{id: $full_id}})
        OPTIONAL MATCH (start)-[rels*1..{depth}]-(neighbor)
        WITH DISTINCT start, neighbor, rels
        LIMIT $limit
        RETURN start, neighbor, rels, labels(neighbor) AS neighbor_labels
    """
    try:
        records = await driver.execute_query(cypher, {"full_id": full_id, "limit": limit})
    except Exception as e:
        if "timeout" in str(e).lower():
            raise GraphTimeoutError("Query timed out")
        raise

    nodes_map: dict[str, NodeModel] = {}
    edges: list[EdgeModel] = []
    seen_edges: set[tuple[str, str, str]] = set()

    for rec in records.records:
        if rec["start"] and not nodes_map.get(full_id):
            sdata = dict(rec["start"])
            sdata.pop("id", None)
            nodes_map[full_id] = NodeModel(id=full_id, type=node_type, properties=sdata)

        if rec["neighbor"] is None:
            continue

        neighbor = rec["neighbor"]
        ndata = dict(neighbor)
        nid = ndata.pop("id", "")
        nlabels = rec["neighbor_labels"]
        ntype = next((l.lower() for l in NODE_TYPE_MAP.values() if l in nlabels), "unknown")
        if nid and nid not in nodes_map:
            nodes_map[nid] = NodeModel(id=nid, type=ntype, properties=ndata)

        # Extract edges from path relationships
        rels = rec["rels"]
        if isinstance(rels, list):
            for rel in rels:
                start_id = rel.start_node.get("id", "")
                end_id = rel.end_node.get("id", "")
                rel_type = rel.type
                edge_key = (start_id, end_id, rel_type)
                if edge_key not in seen_edges:
                    seen_edges.add(edge_key)
                    rel_props = {k: v for k, v in dict(rel).items() if not k.startswith("_")}
                    edges.append(EdgeModel(
                        relation=rel_type, direction="out",
                        source_id=start_id, target_id=end_id,
                        node=NodeModel(id=end_id, type=ntype, properties={}),
                        properties=rel_props,
                    ))

    return SubgraphModel(nodes=list(nodes_map.values()), edges=edges, total_edges=len(edges))


async def find_path(from_type: str, from_id: str, to_type: str, to_id: str, max_length: int) -> SubgraphModel:
    if max_length < 1 or max_length > settings.graph_max_depth:
        raise InvalidParamError(f"max_length must be between 1 and {settings.graph_max_depth}")
    from_label = NODE_TYPE_MAP.get(from_type)
    to_label = NODE_TYPE_MAP.get(to_type)
    full_from = from_id if ":" in from_id else f"{from_type}:{from_id}"
    full_to = to_id if ":" in to_id else f"{to_type}:{to_id}"
    driver = await get_neo4j_driver()
    cypher = f"""
        CYPHER runtime=slotted
        MATCH path = shortestPath(
          (a:{from_label} {{id: $from_id}})-[*..{max_length}]-(b:{to_label} {{id: $to_id}})
        )
        UNWIND nodes(path) AS n
        UNWIND relationships(path) AS r
        RETURN DISTINCT n, r
    """
    try:
        records = await driver.execute_query(cypher, {"from_id": full_from, "to_id": full_to}, timeout=30.0)
    except Exception as e:
        if "timeout" in str(e).lower():
            raise GraphTimeoutError("Shortest path query timed out")
        raise
    nodes_map: dict[str, NodeModel] = {}
    edges: list[EdgeModel] = []
    for rec in records.records:
        ndata = dict(rec["n"])
        nid = ndata.pop("id", "")
        nlabels = rec["n"].labels
        ntype = next((l.lower() for l in NODE_TYPE_MAP.values() if l in nlabels), "unknown")
        if nid and nid not in nodes_map:
            nodes_map[nid] = NodeModel(id=nid, type=ntype, properties=ndata)
        r = rec["r"]
        rel_props = {k: v for k, v in dict(r).items() if not k.startswith("_")}
        edges.append(EdgeModel(
            relation=r.type,
            direction="out",
            source_id=r.start_node.get("id", ""),
            target_id=r.end_node.get("id", ""),
            properties=rel_props,
        ))
    return SubgraphModel(nodes=list(nodes_map.values()), edges=edges, total_edges=len(edges))


async def protein_network(protein_id: str, min_score: float = 0.7, limit: int = 100) -> SubgraphModel:
    full_id = f"protein:{protein_id}"
    driver = await get_neo4j_driver()
    cypher = """
        MATCH (a:Protein {id: $protein_id})-[r:INTERACTS_WITH]->(b:Protein)
        WHERE r.score >= $min_score
        RETURN a, b, r
        LIMIT $limit
    """
    records = await driver.execute_query(cypher, {"protein_id": full_id, "min_score": min_score, "limit": limit})
    nodes_map: dict[str, NodeModel] = {}
    edges: list[EdgeModel] = []
    for rec in records.records:
        for key in ["a", "b"]:
            ndata = dict(rec[key])
            nid = ndata.pop("id", "")
            if nid not in nodes_map:
                nodes_map[nid] = NodeModel(id=nid, type="protein", properties=ndata)
        rel_data = dict(rec["r"])
        src_id = rec["a"].get("id", "")
        tgt_id = rec["b"].get("id", "")
        edges.append(EdgeModel(
            relation="INTERACTS_WITH", direction="out",
            source_id=src_id, target_id=tgt_id,
            node=NodeModel(id=tgt_id, type="protein", properties={}),
            properties={k: v for k, v in rel_data.items() if not k.startswith("_")},
        ))
    return SubgraphModel(nodes=list(nodes_map.values()), edges=edges, total_edges=len(edges))
