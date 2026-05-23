const LAYOUTS: { key: 'cose' | 'breadthfirst' | 'concentric' | 'grid'; label: string }[] = [
  { key: 'cose', label: 'Force' },
  { key: 'breadthfirst', label: 'Tree' },
  { key: 'concentric', label: 'Radial' },
  { key: 'grid', label: 'Grid' },
];

interface Props {
  layout: string;
  onLayoutChange: (layout: 'cose' | 'breadthfirst' | 'concentric' | 'grid') => void;
}

export function LayoutControls({ layout, onLayoutChange }: Props) {
  return (
    <div style={{ display: 'flex', gap: 2, background: 'var(--color-surface-2)', borderRadius: 'var(--radius-sm)', padding: 2 }}>
      {LAYOUTS.map((l) => (
        <button
          key={l.key}
          className={layout === l.key ? 'primary' : 'ghost'}
          onClick={() => onLayoutChange(l.key)}
          style={{ fontSize: 11, padding: '3px 10px', borderRadius: 'var(--radius-sm)', border: 'none' }}
        >
          {l.label}
        </button>
      ))}
    </div>
  );
}
