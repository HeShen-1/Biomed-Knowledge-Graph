import { useGraphStore } from '@/store/graphStore';
import { useNodeDetail } from '@/hooks/useNodeDetail';
import { NodeDetail } from './NodeDetail';
import { RelationTable } from './RelationTable';
import { ExternalLinks } from './ExternalLinks';

export function DetailPanel() {
  const selectedNode = useGraphStore((s) => s.selectedNode);
  const { data, isLoading, isError, error } = useNodeDetail(selectedNode?.type ?? null, selectedNode?.id ?? null);

  return (
    <div className="card">
      <h3 style={{ fontWeight: 300, marginBottom: 'var(--space-3)' }}>Details</h3>
      {!selectedNode && <p style={{ color: 'var(--color-ink-subtle)' }}>Select a node to view details</p>}
      {isLoading && <p style={{ color: 'var(--color-ink-subtle)' }}>Loading...</p>}
      {isError && <p style={{ color: 'var(--color-error)' }}>Error: {(error as Error)?.message || 'Failed to load'}</p>}
      {!isLoading && !isError && selectedNode && (
        <>
          <NodeDetail node={data?.node ?? selectedNode} />
          <RelationTable edges={data?.neighbors ?? []} />
          <ExternalLinks node={selectedNode} />
        </>
      )}
    </div>
  );
}
