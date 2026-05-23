import { lazy, Suspense, useState } from 'react';
import type { Core } from 'cytoscape';
import { LayoutControls } from './LayoutControls';
import { CompoundNode } from './CompoundNode';
import { useGraphStore } from '@/store/graphStore';
import { useGraphExpand } from '@/hooks/useGraphExpand';

const CytoscapeRenderer = lazy(() =>
  import('./CytoscapeRenderer').then((m) => ({ default: m.CytoscapeRenderer }))
);

const LEGEND = [
  { type: 'gene', label: 'Gene', color: '#0f62fe' },
  { type: 'protein', label: 'Protein', color: '#24a148' },
  { type: 'compound', label: 'Compound', color: '#da1e28' },
  { type: 'disease', label: 'Disease', color: '#f1c21b' },
  { type: 'article', label: 'Article', color: '#8b949e' },
];

export function GraphCanvas() {
  const selectedNode = useGraphStore((s) => s.selectedNode);
  const nodes = useGraphStore((s) => s.nodes);
  const edges = useGraphStore((s) => s.edges);
  const layout = useGraphStore((s) => s.layout);
  const setLayout = useGraphStore((s) => s.setLayout);
  const [cy, setCy] = useState<Core | null>(null);

  const { isError: expandError } = useGraphExpand(selectedNode?.type ?? null, selectedNode?.id ?? null);

  return (
    <div className="card" style={{ display: 'flex', flexDirection: 'column', height: '100%', padding: 'var(--space-3)' }}>
      <div className="panel-header" style={{ marginBottom: 'var(--space-2)', paddingBottom: 'var(--space-2)' }}>
        <h3>Graph</h3>
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
          <span style={{ fontSize: 11, color: 'var(--color-ink-subtle)' }}>
            {nodes.length} nodes · {edges.length} edges
          </span>
          <LayoutControls layout={layout} onLayoutChange={setLayout} />
        </div>
      </div>

      <div style={{ display: 'flex', gap: 12, marginBottom: 'var(--space-2)', padding: '6px 10px', background: 'var(--color-surface-2)', borderRadius: 'var(--radius-sm)' }}>
        {LEGEND.map(item => (
          <div key={item.type} style={{ display: 'flex', alignItems: 'center', gap: 5, fontSize: 11, color: 'var(--color-ink-muted)' }}>
            <span style={{ width: 10, height: 10, borderRadius: '50%', background: item.color, flexShrink: 0 }} />
            {item.label}
          </div>
        ))}
      </div>

      <div style={{ flex: 1, minHeight: 420, position: 'relative' }}>
        {nodes.length === 0 && (
          <div style={{
            position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column',
            alignItems: 'center', justifyContent: 'center',
            color: 'var(--color-ink-subtle)', pointerEvents: 'none', zIndex: 1,
          }}>
            <span style={{ fontSize: 40, marginBottom: 12, opacity: 0.3 }}>◉</span>
            <span style={{ fontSize: 14, fontWeight: 300 }}>Search and select a node to explore the graph</span>
          </div>
        )}
        {expandError && (
          <div style={{
            position: 'absolute', top: 8, left: 8, right: 8, zIndex: 10,
            padding: '8px 12px', borderRadius: 'var(--radius-sm)',
            background: 'var(--color-error-muted)', color: 'var(--color-error)',
            fontSize: 12, display: 'flex', alignItems: 'center', gap: 6,
          }}>
            <span>⚠</span> Failed to load graph data
          </div>
        )}
        <Suspense fallback={
          <div style={{
            position: 'absolute', inset: 0, display: 'flex',
            alignItems: 'center', justifyContent: 'center',
            color: 'var(--color-ink-subtle)',
          }}>
            <span style={{ fontSize: 14, fontWeight: 300 }}>Loading graph renderer...</span>
          </div>
        }>
          <CytoscapeRenderer onReady={setCy} />
        </Suspense>
        <CompoundNode cy={cy} />
      </div>
    </div>
  );
}
