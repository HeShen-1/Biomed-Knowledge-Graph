from abc import ABC, abstractmethod
from collections import defaultdict
from datetime import datetime
from typing import AsyncIterator
from ingest.models import NormalizedRecord, NormalizedNode, NormalizedEdge
from ingest.serializers import safe_label, safe_relation


ID_PREFIX_MAP = {"gene": "gene", "protein": "protein", "compound": "compound",
                 "disease": "disease", "pmid": "article", "article": "article"}


def _derive_type(node_id: str) -> str | None:
    """Extract node type from ID prefix, mapping known prefixes to valid types."""
    prefix = node_id.split(":", 1)[0].lower()
    return ID_PREFIX_MAP.get(prefix)


class BaseIngester(ABC):
    source_name: str
    batch_size: int = 500

    @abstractmethod
    async def fetch(self, since: datetime) -> AsyncIterator[dict]:
        ...

    @abstractmethod
    async def normalize(self, record: dict) -> NormalizedRecord | None:
        ...

    def build_queries(self, batch: list[NormalizedRecord]) -> list[tuple[str, dict]]:
        # Collect all nodes and edges across the batch
        seen_nodes: dict[str, NormalizedNode] = {}
        all_edges: list[NormalizedEdge] = []
        for record in batch:
            for node in record.nodes:
                seen_nodes.setdefault(node.id, node)
            all_edges.extend(record.edges)

        # Group nodes by label, build UNWIND MERGE per group
        nodes_by_label: dict[str, list[dict]] = defaultdict(list)
        for node in seen_nodes.values():
            label = safe_label(node.type)
            props = {k: v for k, v in node.properties.items() if v is not None}
            nodes_by_label[label].append({"id": node.id, "props": props})

        statements: list[tuple[str, dict]] = []
        for label, rows in nodes_by_label.items():
            statements.append((
                f"UNWIND $batch AS row MERGE (n:{label} {{id: row.id}}) SET n += row.props",
                {"batch": rows},
            ))

        # Group edges by (from_type, to_type, relation), build UNWIND MATCH+MERGE per group
        edges_by_pattern: dict[tuple[str | None, str | None, str], list[dict]] = defaultdict(list)
        for edge in all_edges:
            relation = safe_relation(edge.relation)
            from_type = edge.from_type or _derive_type(edge.from_id)
            to_type = edge.to_type or _derive_type(edge.to_id)
            key = (from_type, to_type, relation)
            edges_by_pattern[key].append({
                "from_id": edge.from_id,
                "to_id": edge.to_id,
            })

        for (from_type, to_type, relation), rows in edges_by_pattern.items():
            from_label = safe_label(from_type) if from_type else None
            to_label = safe_label(to_type) if to_type else None
            if from_label and to_label:
                statements.append((
                    f"UNWIND $batch AS row "
                    f"MATCH (a:{from_label} {{id: row.from_id}}), (b:{to_label} {{id: row.to_id}}) "
                    f"MERGE (a)-[:{relation}]->(b)",
                    {"batch": rows},
                ))
            else:
                # Fallback: unlabeled MATCH when types can't be derived
                statements.append((
                    f"UNWIND $batch AS row "
                    f"MATCH (a {{id: row.from_id}}), (b {{id: row.to_id}}) "
                    f"MERGE (a)-[:{relation}]->(b)",
                    {"batch": rows},
                ))
        return statements
