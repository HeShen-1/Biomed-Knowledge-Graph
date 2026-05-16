import { useGraphStore } from '@/store/graphStore';

const LAYOUTS: { key: 'cose' | 'breadthfirst' | 'concentric' | 'grid'; label: string }[] = [
  { key: 'cose', label: 'Force' },
  { key: 'breadthfirst', label: 'Tree' },
  { key: 'concentric', label: 'Radial' },
  { key: 'grid', label: 'Grid' },
];

export function LayoutControls() {
  const layout = useGraphStore((s) => s.layout);
  const setLayout = useGraphStore((s) => s.setLayout);

  return (
    <div style={{ display: 'flex', gap: 4, marginTop: 8 }}>
      {LAYOUTS.map((l) => (
        <button key={l.key} className={layout === l.key ? 'primary' : ''} onClick={() => setLayout(l.key)} style={{ fontSize: 12, padding: '4px 8px' }}>
          {l.label}
        </button>
      ))}
    </div>
  );
}
