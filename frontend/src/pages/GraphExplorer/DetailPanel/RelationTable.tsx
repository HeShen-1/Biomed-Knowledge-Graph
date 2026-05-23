import type { EdgeData } from '@/api/graph';

const REL_COLORS: Record<string, string> = {
  ENCODES: '#0f62fe',
  INTERACTS_WITH: '#3fb950',
  BINDS_TO: '#da1e28',
  TARGETS: '#f1c21b',
  ASSOCIATED_WITH: '#8b949e',
  TREATS: '#f78166',
  MENTIONS: '#8b949e',
};

interface Props {
  edges: EdgeData[];
}

export function RelationTable({ edges }: Props) {
  if (edges.length === 0) {
    return (
      <div style={{ marginTop: 'var(--space-4)', paddingTop: 'var(--space-3)', borderTop: '1px solid var(--color-hairline)' }}>
        <h4 style={{ fontSize: 12, fontWeight: 500, color: 'var(--color-ink-muted)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 6 }}>
          Relations
        </h4>
        <p style={{ fontSize: 12, color: 'var(--color-ink-subtle)' }}>No relations found</p>
      </div>
    );
  }

  return (
    <div style={{ marginTop: 'var(--space-4)', paddingTop: 'var(--space-3)', borderTop: '1px solid var(--color-hairline)' }}>
      <h4 style={{
        fontSize: 12, fontWeight: 500, color: 'var(--color-ink-muted)',
        textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 8,
      }}>
        Relations ({edges.length})
      </h4>
      {edges.slice(0, 15).map((edge, i) => {
        const color = REL_COLORS[edge.relation] ?? '#8b949e';
        const tgtId = edge.node?.id ?? '';
        const tgtLabel = String(edge.node?.properties?.label ?? edge.node?.properties?.name ?? tgtId);
        return (
          <div
            key={`${tgtId}-${edge.relation}-${i}`}
            style={{
              display: 'flex', alignItems: 'center', gap: 8,
              padding: '5px 0', borderBottom: '1px solid var(--color-hairline)',
              fontSize: 12,
            }}
          >
            <span style={{
              color, fontWeight: 500, fontSize: 10,
              textTransform: 'uppercase', letterSpacing: '0.04em',
              minWidth: 90, flexShrink: 0,
            }}>
              {edge.relation.replace(/_/g, ' ')}
            </span>
            <span style={{ color: 'var(--color-ink-subtle)', flexShrink: 0 }}>→</span>
            <span style={{
              color: 'var(--color-ink)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
            }}>
              {String(tgtLabel).slice(0, 40)}
            </span>
          </div>
        );
      })}
      {edges.length > 15 && (
        <p style={{ fontSize: 11, color: 'var(--color-ink-subtle)', marginTop: 6 }}>
          +{edges.length - 15} more
        </p>
      )}
    </div>
  );
}
