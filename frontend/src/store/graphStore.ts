import { create } from 'zustand';
import type { NodeData, EdgeData } from '@/api/graph';

interface GraphState {
  nodes: NodeData[];
  edges: EdgeData[];
  selectedNode: NodeData | null;
  layout: 'cose' | 'breadthfirst' | 'concentric' | 'grid';
  setNodes: (nodes: NodeData[]) => void;
  setEdges: (edges: EdgeData[]) => void;
  setSubgraph: (nodes: NodeData[], edges: EdgeData[]) => void;
  setSelectedNode: (node: NodeData | null) => void;
  setLayout: (layout: GraphState['layout']) => void;
  clearGraph: () => void;
}

export const useGraphStore = create<GraphState>((set) => ({
  nodes: [],
  edges: [],
  selectedNode: null,
  layout: 'cose',
  setNodes: (nodes) => set({ nodes }),
  setEdges: (edges) => set({ edges }),
  setSubgraph: (nodes, edges) => set({ nodes, edges }),
  setSelectedNode: (selectedNode) => set({ selectedNode }),
  setLayout: (layout) => set({ layout }),
  clearGraph: () => set({ nodes: [], edges: [], selectedNode: null }),
}));
