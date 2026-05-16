import { client } from './client';

export interface NodeData {
  id: string;
  type: string;
  properties: Record<string, unknown>;
}

export interface EdgeData {
  relation: string;
  direction: 'in' | 'out';
  node: NodeData;
  properties: Record<string, unknown>;
}

export interface NodeDetailResponse {
  node: NodeData;
  neighbors: EdgeData[];
  total_edges: number;
}

export interface SubgraphData {
  nodes: NodeData[];
  edges: EdgeData[];
  total_edges: number;
}

export async function getNodeDetail(type: string, id: string): Promise<NodeDetailResponse> {
  const { data } = await client.get(`/graph/node/${type}/${id}`);
  return data;
}

export async function expandNode(
  type: string, id: string, depth = 1, limit = 50,
): Promise<SubgraphData> {
  const { data } = await client.get(`/graph/expand/${type}/${id}`, { params: { depth, limit } });
  return data;
}

export async function findPath(from: string, to: string): Promise<SubgraphData> {
  const { data } = await client.get('/graph/path', { params: { from, to } });
  return data;
}

export async function getProteinNetwork(
  proteinId: string, minScore = 0.7, limit = 100,
): Promise<SubgraphData> {
  const { data } = await client.get(`/graph/network/${proteinId}`, { params: { min_score: minScore, limit } });
  return data;
}
