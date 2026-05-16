import type { Suggestion } from '@/api/search';

interface Props {
  items: Suggestion[];
  onSelect: (item: Suggestion) => void;
  visible: boolean;
}

export function SuggestionList({ items, onSelect, visible }: Props) {
  if (!visible || items.length === 0) return null;
  return (
    <div style={{ border: '1px solid var(--color-hairline)', borderRadius: 'var(--radius-md)', maxHeight: 200, overflowY: 'auto', marginTop: 4 }}>
      {items.map((item) => (
        <div
          key={item.id}
          onClick={() => onSelect(item)}
          style={{ padding: '8px 16px', cursor: 'pointer', borderBottom: '1px solid var(--color-hairline)' }}
        >
          <span style={{ fontWeight: 600 }}>{item.label}</span>
          <span style={{ marginLeft: 8, color: 'var(--color-ink-subtle)', fontSize: 12 }}>{item.type}</span>
        </div>
      ))}
    </div>
  );
}
