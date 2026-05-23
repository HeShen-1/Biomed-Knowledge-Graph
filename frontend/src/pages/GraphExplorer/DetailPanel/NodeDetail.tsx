import { useEffect, useRef } from 'react';
import { animate, stagger } from 'animejs';
import type { NodeData } from '@/api/graph';

const BADGE_CLASS: Record<string, string> = {
  gene: 'badge badge-gene',
  protein: 'badge badge-protein',
  compound: 'badge badge-compound',
  disease: 'badge badge-disease',
  article: 'badge badge-article',
};

interface Props {
  node: NodeData | null;
}

export function NodeDetail({ node }: Props) {
  const tableRef = useRef<HTMLTableElement>(null);

  useEffect(() => {
    if (node && tableRef.current) {
      const rows = tableRef.current.querySelectorAll('tr');
      animate(Array.from(rows), {
        translateX: [6, 0],
        opacity: [0, 1],
        delay: stagger(25),
        duration: 280,
        easing: 'easeOutCubic',
      });
    }
  }, [node]);

  if (!node) {
    return (
      <div style={{ textAlign: 'center', padding: 'var(--space-5) 0', color: 'var(--color-ink-subtle)' }}>
        <span style={{ fontSize: 36, display: 'block', marginBottom: 10, opacity: 0.3 }}>◉</span>
        <span style={{ fontSize: 13 }}>Select a node to view details</span>
      </div>
    );
  }

  const label = String(node.properties?.label ?? node.properties?.name ?? node.properties?.symbol ?? node.id);
  const rawId = node.id;
  const displayId = rawId.includes(':') ? rawId.split(':').slice(1).join(':') : rawId;

  const skipKeys = new Set(['label', 'id', 'source']);
  const entries = Object.entries(node.properties).filter(([k]) => !skipKeys.has(k));
  const shown = entries.slice(0, 8);

  return (
    <div className="fade-in">
      {/* Header */}
      <div style={{ marginBottom: 'var(--space-3)' }}>
        <span className={BADGE_CLASS[node.type] ?? 'badge'} style={{ marginBottom: 6 }}>
          {node.type}
        </span>
        <h4 style={{
          fontSize: 16, fontWeight: 500, color: 'var(--color-ink)',
          marginTop: 6, wordBreak: 'break-word', letterSpacing: '-0.01em',
        }}>
          {String(label).slice(0, 120)}
        </h4>
        <p style={{
          fontSize: 11, color: 'var(--color-ink-subtle)',
          fontFamily: 'var(--font-mono)',
          marginTop: 4, wordBreak: 'break-all',
        }}>
          {displayId}
        </p>
      </div>

      {/* Properties */}
      {shown.length > 0 && (
        <table className="kv-table" ref={tableRef}>
          <tbody>
            {shown.map(([key, value]) => (
              <tr key={key}>
                <td className="kv-key">{key}</td>
                <td className="kv-val">{String(value).slice(0, 200)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {entries.length > 8 && (
        <p style={{ fontSize: 11, color: 'var(--color-ink-subtle)', marginTop: 6 }}>
          +{entries.length - 8} more properties
        </p>
      )}
    </div>
  );
}
