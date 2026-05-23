import { useGraphStore } from '@/store/graphStore';
import { useNodeDetail } from '@/hooks/useNodeDetail';
import { NodeDetail } from './NodeDetail';
import { RelationTable } from './RelationTable';
import { ExternalLinks } from './ExternalLinks';
import { HistoryPanel } from './HistoryPanel';

export function DetailPanel() {
  const selectedNode = useGraphStore((s) => s.selectedNode);
  const clearGraph = useGraphStore((s) => s.clearGraph);
  const { data, isLoading, isError, error } = useNodeDetail(
    selectedNode?.type ?? null,
    selectedNode?.id ?? null,
  );

  return (
    <div className="card" style={{ padding: 'var(--space-3)', height: '100%', overflowY: 'auto' }}>
      <div className="panel-header" style={{ marginBottom: 0, paddingBottom: 'var(--space-2)' }}>
        <h3>Details</h3>
        {selectedNode && (
          <button
            className="ghost"
            onClick={clearGraph}
            style={{ fontSize: 11, padding: '2px 8px' }}
          >
            Clear
          </button>
        )}
      </div>

      {isLoading && (
        <div style={{ textAlign: 'center', padding: 'var(--space-5) 0', color: 'var(--color-ink-subtle)' }}>
          <span style={{ fontSize: 13 }}>Loading…</span>
        </div>
      )}

      {isError && (
        <div style={{
          marginTop: 'var(--space-3)', padding: 'var(--space-3)',
          background: 'rgba(218, 30, 40, 0.08)', borderRadius: 'var(--radius-md)',
          border: '1px solid rgba(218, 30, 40, 0.2)',
          fontSize: 12, color: 'var(--color-error)',
        }}>
          {(error as Error)?.message || 'Failed to load'}
        </div>
      )}

      {!isLoading && !isError && !selectedNode && (
        <NodeDetail node={null} />
      )}

      {!isLoading && !isError && selectedNode && (
        <>
          <NodeDetail node={data?.node ?? selectedNode} />
          <RelationTable edges={data?.neighbors ?? []} />
          <ExternalLinks node={data?.node ?? selectedNode} />
        </>
      )}

      <div style={{ marginTop: 'var(--space-3)' }}>
        <HistoryPanel />
      </div>
    </div>
  );
}
