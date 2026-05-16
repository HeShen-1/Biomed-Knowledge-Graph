import type { NodeData } from '@/api/graph';

interface Props {
  node: NodeData | null;
}

export function NodeDetail({ node }: Props) {
  if (!node) {
    return <p style={{ color: 'var(--color-ink-subtle)' }}>Select a node to view details</p>;
  }

  return (
    <div>
      <h4 style={{ fontWeight: 400, marginBottom: 8 }}>
        {String(node.properties?.label ?? node.properties?.name ?? node.id)}
      </h4>
      <p style={{ fontSize: 12, color: 'var(--color-ink-muted)', marginBottom: 16 }}>
        Type: <strong>{node.type}</strong> · ID: {node.id}
      </p>
      <table style={{ width: '100%', fontSize: 13, borderCollapse: 'collapse' }}>
        <tbody>
          {Object.entries(node.properties).map(([key, value]) => (
            <tr key={key} style={{ borderBottom: '1px solid var(--color-hairline)' }}>
              <td style={{ padding: '4px 8px', fontWeight: 600, color: 'var(--color-ink-muted)', width: '40%' }}>{key}</td>
              <td style={{ padding: '4px 8px' }}>{String(value).slice(0, 200)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
