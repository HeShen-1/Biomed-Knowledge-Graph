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
    <div style={{ display: 'flex', gap: 4, marginTop: 8, flexWrap: 'wrap' }}>
      {ENTITY_TYPES.map((t) => (
        <button
          key={t.key ?? 'all'}
          className={selectedType === t.key ? 'primary' : ''}
          onClick={() => onChange(t.key)}
          style={{ fontSize: 12, padding: '4px 8px' }}
        >
          {t.label}
        </button>
      ))}
    </div>
  );
}
