import { useEffect } from 'react';
import { CytoscapeRenderer } from './CytoscapeRenderer';
import { LayoutControls } from './LayoutControls';
import { useGraphStore } from '@/store/graphStore';
import { useGraphExpand } from '@/hooks/useGraphExpand';

export function GraphCanvas() {
  const selectedNode = useGraphStore((s) => s.selectedNode);
  const setSubgraph = useGraphStore((s) => s.setSubgraph);
  const { data } = useGraphExpand(selectedNode?.type ?? null, selectedNode?.id ?? null);

  useEffect(() => {
    if (data && data.nodes.length > 0) {
      setSubgraph(data.nodes, data.edges || []);
    }
  }, [data, setSubgraph]);

  return (
    <div className="card">
      <h3 style={{ fontWeight: 300, marginBottom: 'var(--space-2)' }}>Graph</h3>
      <CytoscapeRenderer />
      <LayoutControls />
    </div>
  );
}
