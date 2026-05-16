import type { EdgeData } from '@/api/graph';

interface Props {
  edges: EdgeData[];
}

export function RelationTable({ edges }: Props) {
  if (edges.length === 0) {
    return <p style={{ color: 'var(--color-ink-subtle)', fontSize: 13, marginTop: 16 }}>No relations</p>;
  }
  return (
    <div style={{ marginTop: 16 }}>
      <h4 style={{ fontWeight: 400, marginBottom: 8 }}>Relations ({edges.length})</h4>
      {edges.map((edge, i) => (
        <div key={`${edge.node?.id}-${edge.relation}-${i}`} style={{ padding: '4px 0', borderBottom: '1px solid var(--color-hairline)', fontSize: 13 }}>
          <span style={{ color: 'var(--color-primary)', fontWeight: 600 }}>{edge.relation}</span>
          <span style={{ margin: '0 8px', color: 'var(--color-ink-subtle)' }}>→</span>
          <span>{edge.node?.id ?? 'unknown'}</span>
        </div>
      ))}
    </div>
  );
}
