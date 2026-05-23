const ENTITY_TYPES = [
  { key: null, label: 'All' },
  { key: 'gene', label: 'Genes' },
  { key: 'protein', label: 'Proteins' },
  { key: 'compound', label: 'Compounds' },
  { key: 'disease', label: 'Diseases' },
  { key: 'article', label: 'Articles' },
];

interface Props {
  selectedType: string | null;
  onChange: (type: string | null) => void;
}

export function FilterBar({ selectedType, onChange }: Props) {
  return (
    <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap', marginTop: 'var(--space-2)' }}>
      {ENTITY_TYPES.map((t) => {
        const active = selectedType === t.key;
        return (
          <button
            key={t.key ?? 'all'}
            className={active ? 'primary' : 'ghost'}
            onClick={() => onChange(t.key)}
            style={{
              fontSize: 11, padding: '3px 10px', borderRadius: 'var(--radius-sm)',
              border: active ? undefined : '1px solid transparent',
            }}
          >
            {t.label}
          </button>
        );
      })}
    </div>
  );
}
